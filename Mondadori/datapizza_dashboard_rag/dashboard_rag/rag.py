from __future__ import annotations

import json
import re
import socket
import unicodedata
from contextlib import nullcontext
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import List

import pandas as pd

from .config import Settings
from .ingestion import DatasetArtifacts
from .local_qdrant import LocalQdrantVectorstore


@dataclass(frozen=True)
class AnswerReference:
    source_path: str
    raw_table: str
    analysis_table: str
    source_label: str
    matched_column: str | None = None
    matched_value: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class AnswerPayload:
    text: str
    references: list[AnswerReference]
    conversation_focus: str | None = None
    memory: object | None = None


@dataclass(frozen=True)
class EntityMatch:
    column: str
    value: str
    score: float


def _network_error_message(exc: Exception, phase: str) -> str:
    text = str(exc).strip() or exc.__class__.__name__
    return (
        f"Errore di rete durante l'esecuzione RAG nella fase `{phase}`. "
        "Il processo non riesce a risolvere l'host remoto (DNS). "
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


def _normalize_lookup(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    return re.sub(r"\s+", " ", text)


def _preferred_entity_columns(frame: pd.DataFrame) -> list[str]:
    preferred = ["testata", "source", "target"]
    available = []
    for column in frame.columns:
        normalized = _normalize_lookup(column)
        if normalized in preferred:
            available.append(column)
    return available or [
        column
        for column in frame.columns
        if pd.api.types.is_string_dtype(frame[column]) or frame[column].dtype == "object"
    ]


def _iter_entity_matches(query: str, frame: pd.DataFrame) -> list[EntityMatch]:
    query_norm = _normalize_lookup(query)
    if not query_norm:
        return []

    query_tokens = set(query_norm.split())
    matches: dict[tuple[str, str], EntityMatch] = {}
    preferred_columns = set(_preferred_entity_columns(frame))

    for column in _preferred_entity_columns(frame):
        values = frame[column].dropna().astype(str).str.strip()
        for value in values.unique():
            value_norm = _normalize_lookup(value)
            if not value_norm:
                continue

            ratio = SequenceMatcher(None, query_norm, value_norm).ratio()
            score = ratio

            if value_norm == query_norm:
                score = 1.0
            elif value_norm in query_norm:
                score = max(score, 0.97)
            elif query_norm in value_norm:
                score = max(score, 0.93)
            elif set(value_norm.split()).issubset(query_tokens):
                score = max(score, 0.91)

            if column in preferred_columns:
                score += 0.03

            key = (column, value)
            previous = matches.get(key)
            if previous is None or score > previous.score:
                matches[key] = EntityMatch(column=column, value=value, score=score)

    return sorted(matches.values(), key=lambda item: item.score, reverse=True)


def _best_entity_match(query: str, frame: pd.DataFrame) -> EntityMatch | None:
    matches = _iter_entity_matches(query, frame)
    if not matches:
        return None
    best = matches[0]
    if best.score < 0.65:
        return None
    return best


def _match_rows(frame: pd.DataFrame, column: str, value: str) -> pd.DataFrame:
    target = _normalize_lookup(value)
    return frame.loc[frame[column].astype(str).map(_normalize_lookup) == target].copy()


def _latest_entity_row(rows: pd.DataFrame) -> pd.Series:
    sort_columns = [column for column in ("mese_dt", "period_order", "mese", "trimestre") if column in rows.columns]
    if sort_columns:
        return rows.sort_values(sort_columns).iloc[-1]
    return rows.iloc[-1]


def _dataset_reference(
    artifacts: DatasetArtifacts,
    *,
    matched_column: str | None = None,
    matched_value: str | None = None,
    note: str | None = None,
) -> AnswerReference:
    return AnswerReference(
        source_path=artifacts.source_path,
        raw_table=artifacts.raw_table,
        analysis_table=artifacts.analysis_table,
        source_label=artifacts.dataset_name,
        matched_column=matched_column,
        matched_value=matched_value,
        note=note,
    )


def _entity_summary_json(match: EntityMatch, analysis_df: pd.DataFrame, artifacts: DatasetArtifacts) -> str:
    rows = _match_rows(analysis_df, match.column, match.value)
    if rows.empty:
        return json.dumps(
            {
                "matched": False,
                "query": match.value,
                "source_path": artifacts.source_path,
            },
            ensure_ascii=False,
            indent=2,
        )

    payload: dict[str, object] = {
        "matched": True,
        "matched_value": match.value,
        "matched_column": match.column,
        "row_count": int(len(rows)),
        "source_path": artifacts.source_path,
        "raw_table": artifacts.raw_table,
        "analysis_table": artifacts.analysis_table,
    }

    if "revenue_cumulativa_eur" in rows.columns:
        latest = _latest_entity_row(rows)
        payload["business_rule"] = (
            "Per i dataset con colonne cumulative, la revenue totale della testata coincide "
            "con l'ultimo valore cumulativo disponibile e non con la somma delle righe."
        )
        payload["metric_name"] = "latest_cumulative_revenue_eur"
        payload["metric_value"] = float(latest["revenue_cumulativa_eur"])
        if "mese" in latest.index:
            payload["latest_period"] = str(latest["mese"])
        if "revenue_eur" in latest.index:
            payload["latest_incremental_revenue_eur"] = float(latest["revenue_eur"])
    elif "revenue_eur" in rows.columns:
        payload["metric_name"] = "total_revenue_eur"
        payload["metric_value"] = float(rows["revenue_eur"].sum())
        if "mese" in rows.columns:
            payload["periods"] = sorted(rows["mese"].astype(str).unique().tolist())
    elif "value" in rows.columns:
        payload["metric_name"] = "total_value"
        payload["metric_value"] = float(rows["value"].sum())
    else:
        payload["available_columns"] = rows.columns.tolist()

    preview_columns = [column for column in ("mese", "trimestre", "revenue_eur", "revenue_cumulativa_eur", "value") if column in rows.columns]
    if preview_columns:
        payload["preview"] = rows[preview_columns].head(6).to_dict(orient="records")

    return json.dumps(payload, ensure_ascii=False, indent=2)


def answer_question(
    question: str,
    settings: Settings,
    artifacts: DatasetArtifacts,
    analysis_df: pd.DataFrame,
    memory=None,
    conversation_focus: str | None = None,
) -> AnswerPayload:
    if not settings.openai_api_key:
        raise RuntimeError("Chiave OpenAI assente. Inserisci `Openai` nel file .env.")
    if not artifacts.collection_name:
        raise RuntimeError("Il dataset non è stato indicizzato per il retrieval.")

    try:
        from datapizza.agents import Agent
        from datapizza.clients.openai import OpenAIClient
        from datapizza.embedders.openai import OpenAIEmbedder
        from datapizza.tools import tool
        from datapizza.tools.SQLDatabase import SQLDatabase
        from datapizza.tracing import ContextTracing
    except ImportError as exc:
        raise RuntimeError(
            "Dipendenze Datapizza non installate. Usa Python 3.10+ e installa requirements.txt."
        ) from exc

    client = OpenAIClient(api_key=settings.openai_api_key, model=settings.chat_model)
    embedder = OpenAIEmbedder(api_key=settings.openai_api_key)
    vectorstore = LocalQdrantVectorstore(path=str(settings.qdrant_dir / "local_qdrant"))
    sql_tool = SQLDatabase(db_uri=f"sqlite:///{settings.sqlite_path}")
    profile_text = Path(artifacts.profile_path).read_text(encoding="utf-8")
    reference_state = {
        "references": [],
        "conversation_focus": conversation_focus,
    }

    def _add_reference(reference: AnswerReference) -> None:
        if reference not in reference_state["references"]:
            reference_state["references"].append(reference)

    @tool
    def get_active_dataset_metadata() -> str:
        """Restituisce i metadati del dataset attivo nella dashboard."""
        _add_reference(_dataset_reference(artifacts, note="Metadati del dataset attivo"))
        return json.dumps(
            {
                "dataset_id": artifacts.dataset_id,
                "dataset_name": artifacts.dataset_name,
                "dataset_kind": artifacts.dataset_kind,
                "source_path": artifacts.source_path,
                "raw_table": artifacts.raw_table,
                "analysis_table": artifacts.analysis_table,
                "row_count": artifacts.row_count,
                "analysis_row_count": artifacts.analysis_row_count,
            },
            ensure_ascii=False,
            indent=2,
        )

    @tool
    def resolve_entity_reference(entity_query: str) -> str:
        """Trova la migliore corrispondenza flessibile per una testata o altro valore testuale nel dataset attivo."""
        matches = _iter_entity_matches(entity_query, analysis_df)
        top_matches = matches[:5]
        if not top_matches:
            return json.dumps(
                {
                    "matched": False,
                    "query": entity_query,
                    "source_path": artifacts.source_path,
                },
                ensure_ascii=False,
                indent=2,
            )

        best = top_matches[0]
        reference_state["conversation_focus"] = best.value
        _add_reference(
            _dataset_reference(
                artifacts,
                matched_column=best.column,
                matched_value=best.value,
                note="Corrispondenza flessibile dell'entità nel dataset attivo",
            )
        )
        return json.dumps(
            {
                "matched": True,
                "query": entity_query,
                "best_match": {
                    "value": best.value,
                    "column": best.column,
                    "score": round(best.score, 3),
                },
                "candidates": [
                    {
                        "value": match.value,
                        "column": match.column,
                        "score": round(match.score, 3),
                    }
                    for match in top_matches
                ],
                "source_path": artifacts.source_path,
            },
            ensure_ascii=False,
            indent=2,
        )

    @tool
    def get_entity_business_summary(entity_query: str) -> str:
        """Restituisce un riepilogo deterministico per una testata o entità nominale, gestendo correttamente le colonne cumulative."""
        match = _best_entity_match(entity_query, analysis_df)
        if match is None:
            return json.dumps(
                {
                    "matched": False,
                    "query": entity_query,
                    "source_path": artifacts.source_path,
                },
                ensure_ascii=False,
                indent=2,
            )

        reference_state["conversation_focus"] = match.value
        _add_reference(
            _dataset_reference(
                artifacts,
                matched_column=match.column,
                matched_value=match.value,
                note="Riepilogo deterministico su entità con gestione dei cumulativi",
            )
        )
        return _entity_summary_json(match, analysis_df, artifacts)

    @tool
    def retrieve_dataset_context(query: str) -> str:
        """Recupera il contesto semantico del dataset attivo dal vector store locale."""
        try:
            query_vector = embedder.embed(query, model_name=settings.embedding_model)
        except Exception as exc:
            if not _is_network_error(exc):
                raise
            raise RuntimeError(_network_error_message(exc, "openai_embed_query")) from exc
        try:
            chunks = vectorstore.search(
                collection_name=artifacts.collection_name,
                query_vector=query_vector,
                k=4,
            )
        except Exception as exc:
            if not _is_network_error(exc):
                raise
            raise RuntimeError(_network_error_message(exc, "qdrant_search")) from exc

        _add_reference(_dataset_reference(artifacts, note="Contesto semantico recuperato da Qdrant locale"))
        if not chunks:
            return profile_text

        parts: List[str] = []
        for index, chunk in enumerate(chunks, start=1):
            parts.append(f"[chunk {index}] {chunk.text}")
        return "\n\n".join(parts)

    system_prompt_parts = [
        "Sei un data analyst specializzato sui dataset mostrati in dashboard.",
        "Usa sempre i tool disponibili per basarti sui dati reali.",
        "Per contesto e definizioni usa retrieve_dataset_context.",
        "Per domande su testate, giornali, brand o entità nominali usa prima resolve_entity_reference o get_entity_business_summary.",
        "Le corrispondenze sulle testate devono essere flessibili: mai limitarsi a match case-sensitive o esatti se esiste un match plausibile nel dataset.",
        "Se il dataset contiene colonne cumulative come revenue_cumulativa_eur, la revenue totale di una testata coincide con l'ultimo valore cumulativo disponibile e non con la somma delle righe.",
        "Usa SQL sulle tabelle del dataset attivo per ranking, aggregazioni e confronti multi-entità quando serve.",
        "Usa la memoria conversazionale: se l'utente fa follow-up ellittici come 'solo per Focus' o 'e per lei?', mantieni il focus della conversazione salvo chiaro cambio di soggetto.",
        "Non inventare colonne o periodi. Se il dato non c'è, dillo esplicitamente.",
        "Nella risposta finale cita in modo naturale il dataset attivo e il criterio usato.",
    ]
    if conversation_focus:
        system_prompt_parts.append(
            f"Focus conversazionale corrente: `{conversation_focus}`. Usalo solo se il nuovo messaggio è un follow-up ambiguo o ellittico."
        )

    agent = Agent(
        name="mondadori_dashboard_analyst",
        client=client,
        max_steps=6,
        stateless=False,
        memory=memory,
        system_prompt=" ".join(system_prompt_parts),
        tools=[
            get_active_dataset_metadata,
            resolve_entity_reference,
            get_entity_business_summary,
            retrieve_dataset_context,
            sql_tool.list_tables,
            sql_tool.get_table_schema,
            sql_tool.run_sql_query,
        ],
    )

    task_input = question
    if conversation_focus:
        task_input = (
            f"Follow-up context: il focus conversazionale corrente e` `{conversation_focus}`. "
            f"Usalo solo se utile.\n\nRichiesta utente: {question}"
        )

    trace_context = nullcontext()
    try:
        trace_context = ContextTracing().trace(f"rag_{artifacts.dataset_id}")
    except Exception:
        trace_context = nullcontext()

    try:
        with trace_context:
            response = agent.run(task_input)
    except Exception as exc:
        if not _is_network_error(exc):
            raise
        raise RuntimeError(_network_error_message(exc, "agent_run")) from exc

    references = list(reference_state["references"]) or [_dataset_reference(artifacts)]
    return AnswerPayload(
        text=response.text.strip(),
        references=references,
        conversation_focus=reference_state["conversation_focus"],
        memory=getattr(agent, "_memory", None),
    )
