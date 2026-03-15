from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import socket
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

from .catalog import DatasetEntry
from .config import Settings
from .local_qdrant import LocalQdrantVectorstore


def _network_error_message(exc: Exception, phase: str) -> str:
    text = str(exc).strip() or exc.__class__.__name__
    return (
        f"Errore durante l'indicizzazione del dataset nella fase `{phase}`. "
        "Il processo non riesce a risolvere l'host remoto (DNS) necessario per completare l'operazione. "
        "Verifica connessione internet, VPN/proxy aziendale e che nessuna variabile come "
        "`OPENAI_BASE_URL`, `HTTP_PROXY` o `HTTPS_PROXY` punti a un host non valido. "
        f"Dettaglio originale: {text}"
    )


def _is_network_error(exc: Exception) -> bool:
    current: Exception | None = exc
    while current is not None:
        if isinstance(current, (OSError, socket.gaierror)):
            return True
        if current.__class__.__name__ == "APIConnectionError":
            return True
        current = current.__cause__ if isinstance(current.__cause__, Exception) else None
    return False


IT_MONTH_TO_NUM = {
    "gen": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "mag": 5,
    "giu": 6,
    "lug": 7,
    "ago": 8,
    "set": 9,
    "ott": 10,
    "nov": 11,
    "dic": 12,
}


@dataclass(frozen=True)
class DatasetArtifacts:
    dataset_id: str
    dataset_name: str
    dataset_kind: str
    source_path: str
    fingerprint: str
    raw_table: str
    analysis_table: str
    collection_name: str
    profile_path: str
    manifest_path: str
    row_count: int
    analysis_row_count: int


def load_dataset_frame(entry: DatasetEntry) -> pd.DataFrame:
    return pd.read_csv(entry.path)


def build_dataset_frames(entry: DatasetEntry) -> Tuple[pd.DataFrame, pd.DataFrame]:
    raw_df = load_dataset_frame(entry)
    analysis_df = prepare_analysis_frame(entry, raw_df)
    return raw_df, analysis_df


def _normalize_name(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower()).strip("_")
    return slug or "column"


def _unique_names(columns: Iterable[str]) -> List[str]:
    counts: Dict[str, int] = {}
    normalized = []
    for column in columns:
        base = _normalize_name(column)
        counts[base] = counts.get(base, 0) + 1
        normalized.append(base if counts[base] == 1 else f"{base}_{counts[base]}")
    return normalized


def _convert_object_numbers(frame: pd.DataFrame) -> pd.DataFrame:
    converted = frame.copy()
    for column in converted.columns:
        if pd.api.types.is_numeric_dtype(converted[column]):
            continue
        candidate = (
            converted[column]
            .astype(str)
            .str.strip()
            .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
            .str.replace("%", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        numeric = pd.to_numeric(candidate, errors="coerce")
        if numeric.notna().mean() >= 0.8:
            converted[column] = numeric
    return converted


def _parse_month_label(label: object) -> pd.Timestamp:
    text = str(label).strip()
    lower = text.lower()
    month_txt, year_txt = lower.split("-")
    return pd.Timestamp(year=int(year_txt), month=IT_MONTH_TO_NUM[month_txt], day=1)


def _quarter_order(label: object) -> int:
    text = str(label).strip().lower()
    match = re.fullmatch(r"q([1-4])-(\d{4})", text)
    if not match:
        return 0
    quarter, year = match.groups()
    return int(year) * 10 + int(quarter)


def prepare_analysis_frame(entry: DatasetEntry, raw_df: pd.DataFrame) -> pd.DataFrame:
    if entry.kind == "sankey":
        frame = raw_df.rename(columns=dict(zip(raw_df.columns, _unique_names(raw_df.columns))))
        frame = frame.rename(columns={"source": "source", "target": "target", "value": "value"})
        frame["value"] = pd.to_numeric(frame["value"], errors="coerce").fillna(0)
        frame["edge"] = frame["source"].astype(str) + " -> " + frame["target"].astype(str)
        return frame

    if entry.kind == "scatter":
        frame = raw_df.copy()
        frame.columns = ["testata", "cpm_medio_eur", "fill_rate_pct", "revenue_eur", "mese"]
        frame = _convert_object_numbers(frame)
        frame["mese_dt"] = frame["mese"].apply(_parse_month_label)
        return frame.sort_values(["mese_dt", "testata"]).reset_index(drop=True)

    if entry.kind == "bar_chart_race":
        frame = raw_df.copy()
        month_columns = [column for column in frame.columns if column != "Testata"]
        long_df = frame.melt(id_vars=["Testata"], value_vars=month_columns, var_name="mese", value_name="revenue_cumulativa_eur")
        long_df = long_df.rename(columns={"Testata": "testata"})
        long_df["revenue_cumulativa_eur"] = pd.to_numeric(long_df["revenue_cumulativa_eur"], errors="coerce").fillna(0)
        long_df["mese_dt"] = long_df["mese"].apply(_parse_month_label)
        return long_df.sort_values(["mese_dt", "testata"]).reset_index(drop=True)

    if entry.kind == "slope":
        frame = raw_df.copy()
        period_columns = [column for column in frame.columns if column != "Testata"]
        long_df = frame.melt(id_vars=["Testata"], value_vars=period_columns, var_name="trimestre", value_name="revenue_eur")
        long_df = long_df.rename(columns={"Testata": "testata"})
        long_df["revenue_eur"] = pd.to_numeric(long_df["revenue_eur"], errors="coerce").fillna(0)
        long_df["period_order"] = long_df["trimestre"].apply(_quarter_order)
        long_df = long_df.sort_values(["period_order", "testata"]).reset_index(drop=True)
        long_df["delta_vs_previous"] = long_df.groupby("testata")["revenue_eur"].diff().fillna(0)
        return long_df

    frame = raw_df.rename(columns=dict(zip(raw_df.columns, _unique_names(raw_df.columns))))
    return _convert_object_numbers(frame)


def _fingerprint(entry: DatasetEntry) -> str:
    stat = entry.path.stat()
    return f"{stat.st_size}-{stat.st_mtime_ns}"


def _table_name(prefix: str, dataset_id: str) -> str:
    return f"{prefix}_{dataset_id}"


def _profile_path(settings: Settings, dataset_id: str) -> Path:
    return settings.profiles_dir / f"{dataset_id}.md"


def _manifest_path(settings: Settings, dataset_id: str) -> Path:
    return settings.manifests_dir / f"{dataset_id}.json"


def _numeric_summary(frame: pd.DataFrame) -> str:
    numeric = frame.select_dtypes(include="number")
    if numeric.empty:
        return "- Nessuna colonna numerica disponibile."

    lines = []
    for column in numeric.columns[:6]:
        series = numeric[column].dropna()
        if series.empty:
            continue
        lines.append(
            f"- {column}: min={series.min():,.2f}, max={series.max():,.2f}, media={series.mean():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
    return "\n".join(lines) if lines else "- Nessun riepilogo numerico disponibile."


def _top_rows_summary(entry: DatasetEntry, analysis_df: pd.DataFrame) -> str:
    if entry.kind == "sankey":
        top_edges = analysis_df.nlargest(5, "value")[["source", "target", "value"]]
        return "\n".join(
            f"- {row.source} -> {row.target}: {int(row.value)}" for row in top_edges.itertuples(index=False)
        )

    if entry.kind == "scatter":
        top_revenue = analysis_df.nlargest(5, "revenue_eur")[["testata", "mese", "revenue_eur"]]
        return "\n".join(
            f"- {row.testata} in {row.mese}: {int(row.revenue_eur)} EUR"
            for row in top_revenue.itertuples(index=False)
        )

    if entry.kind == "bar_chart_race":
        latest_period = analysis_df["mese_dt"].max()
        latest = analysis_df.loc[analysis_df["mese_dt"] == latest_period].nlargest(5, "revenue_cumulativa_eur")
        return "\n".join(
            f"- {row.testata} a {row.mese}: {int(row.revenue_cumulativa_eur)} EUR"
            for row in latest.itertuples(index=False)
        )

    if entry.kind == "slope":
        top_delta = analysis_df.nlargest(5, "delta_vs_previous")[["testata", "trimestre", "delta_vs_previous"]]
        return "\n".join(
            f"- {row.testata} in {row.trimestre}: delta {int(row.delta_vs_previous)} EUR"
            for row in top_delta.itertuples(index=False)
        )

    return "\n".join(f"- {row}" for row in analysis_df.head(5).to_dict(orient="records"))


def build_dataset_profile(
    entry: DatasetEntry,
    raw_df: pd.DataFrame,
    analysis_df: pd.DataFrame,
    raw_table: str,
    analysis_table: str,
) -> str:
    columns = "\n".join(f"- {column}" for column in raw_df.columns)

    return "\n".join(
        [
            f"# Dataset {entry.name}",
            "",
            "## Metadata",
            f"- dataset_id: {entry.dataset_id}",
            f"- kind: {entry.kind}",
            f"- source_path: {entry.path}",
            f"- raw_table: {raw_table}",
            f"- analysis_table: {analysis_table}",
            f"- raw_rows: {len(raw_df)}",
            f"- analysis_rows: {len(analysis_df)}",
            "",
            "## Columns",
            columns,
            "",
            "## Numeric summary",
            _numeric_summary(analysis_df),
            "",
            "## Top business facts",
            _top_rows_summary(entry, analysis_df),
            "",
            "## Sample rows",
            analysis_df.head(8).to_json(orient="records", force_ascii=False),
        ]
    )


def _split_text(text: str, chunk_size: int = 1200) -> List[str]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    chunks: List[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 2 <= chunk_size:
            current = f"{current}\n\n{paragraph}".strip()
        else:
            if current:
                chunks.append(current)
            current = paragraph

    if current:
        chunks.append(current)

    return chunks or [text]


def _write_sqlite(raw_df: pd.DataFrame, analysis_df: pd.DataFrame, settings: Settings, raw_table: str, analysis_table: str) -> None:
    connection = sqlite3.connect(settings.sqlite_path)
    try:
        raw_df.to_sql(raw_table, connection, if_exists="replace", index=False)
        analysis_df.to_sql(analysis_table, connection, if_exists="replace", index=False)
    finally:
        connection.close()


def _existing_manifest(settings: Settings, dataset_id: str) -> Optional[DatasetArtifacts]:
    path = _manifest_path(settings, dataset_id)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return DatasetArtifacts(**payload)


def _save_manifest(settings: Settings, artifacts: DatasetArtifacts) -> None:
    path = _manifest_path(settings, artifacts.dataset_id)
    path.write_text(json.dumps(asdict(artifacts), ensure_ascii=False, indent=2), encoding="utf-8")


def _embed_profile(chunks_text: List[str], settings: Settings, collection_name: str, metadata: Dict[str, object]) -> None:
    try:
        from datapizza.core.vectorstore import Distance, VectorConfig
        from datapizza.embedders import ChunkEmbedder
        from datapizza.embedders.openai import OpenAIEmbedder
        from datapizza.type import Chunk, EmbeddingFormat
    except ImportError as exc:
        raise RuntimeError(
            "Dipendenze Datapizza non installate. Usa Python 3.10+ e installa requirements.txt."
        ) from exc

    vectorstore = LocalQdrantVectorstore(path=str(settings.qdrant_dir / "local_qdrant"))
    try:
        collections = vectorstore.get_collections() or []
    except Exception as exc:
        if not _is_network_error(exc):
            raise
        raise RuntimeError(_network_error_message(exc, "qdrant_get_collections")) from exc

    collection_names = set()
    for item in collections:
        if isinstance(item, str):
            collection_names.add(item)
        elif hasattr(item, "name"):
            collection_names.add(getattr(item, "name"))
        elif isinstance(item, dict) and "name" in item:
            collection_names.add(str(item["name"]))

    if collection_name not in collection_names:
        try:
            vectorstore.create_collection(
                collection_name=collection_name,
                vector_config=[
                    VectorConfig(
                        name="text_embeddings",
                        dimensions=settings.embedding_dimensions,
                        format=EmbeddingFormat.DENSE,
                        distance=Distance.COSINE,
                    )
                ],
            )
        except Exception as exc:
            if not _is_network_error(exc):
                raise
            raise RuntimeError(_network_error_message(exc, "qdrant_create_collection")) from exc

    embedder_client = OpenAIEmbedder(api_key=settings.openai_api_key)
    chunk_embedder = ChunkEmbedder(
        client=embedder_client,
        model_name=settings.embedding_model,
        embedding_name="text_embeddings",
    )

    chunks = [
        Chunk(
            id=str(uuid.uuid4()),
            text=chunk_text,
            metadata=dict(metadata, chunk_index=index),
        )
        for index, chunk_text in enumerate(chunks_text, start=1)
    ]

    try:
        embedded_chunks = chunk_embedder.embed(chunks)
    except Exception as exc:
        if not _is_network_error(exc):
            raise
        raise RuntimeError(_network_error_message(exc, "openai_embed_chunks")) from exc

    try:
        vectorstore.add(embedded_chunks, collection_name=collection_name)
    except Exception as exc:
        if not _is_network_error(exc):
            raise
        raise RuntimeError(_network_error_message(exc, "qdrant_add_vectors")) from exc


def ensure_dataset_assets(entry: DatasetEntry, settings: Settings) -> DatasetArtifacts:
    fingerprint = _fingerprint(entry)
    current = _existing_manifest(settings, entry.dataset_id)
    if current and current.fingerprint == fingerprint and Path(current.profile_path).exists():
        return current

    raw_df, analysis_df = build_dataset_frames(entry)
    raw_table = _table_name("raw", entry.dataset_id)
    analysis_table = _table_name("analysis", entry.dataset_id)

    _write_sqlite(raw_df, analysis_df, settings, raw_table, analysis_table)

    profile = build_dataset_profile(entry, raw_df, analysis_df, raw_table, analysis_table)
    profile_path = _profile_path(settings, entry.dataset_id)
    profile_path.write_text(profile, encoding="utf-8")

    collection_suffix = hashlib.md5(fingerprint.encode("utf-8")).hexdigest()[:10]
    collection_name = f"{entry.dataset_id}_{collection_suffix}"
    if settings.openai_api_key:
        _embed_profile(
            _split_text(profile),
            settings=settings,
            collection_name=collection_name,
            metadata={
                "dataset_id": entry.dataset_id,
                "dataset_kind": entry.kind,
                "dataset_name": entry.name,
            },
        )

    artifacts = DatasetArtifacts(
        dataset_id=entry.dataset_id,
        dataset_name=entry.name,
        dataset_kind=entry.kind,
        source_path=str(entry.path),
        fingerprint=fingerprint,
        raw_table=raw_table,
        analysis_table=analysis_table,
        collection_name=collection_name if settings.openai_api_key else "",
        profile_path=str(profile_path),
        manifest_path=str(_manifest_path(settings, entry.dataset_id)),
        row_count=len(raw_df),
        analysis_row_count=len(analysis_df),
    )
    _save_manifest(settings, artifacts)
    return artifacts
