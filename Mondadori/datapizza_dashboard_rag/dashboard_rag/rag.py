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

JsonObject = dict[str, object]


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


@dataclass(frozen=True)
class PeriodMatch:
    column: str
    value: str
    score: float


@dataclass(frozen=True)
class PeriodMention:
    match: PeriodMatch
    position: int
    alias: str


IT_MONTH_FULL_TO_ABBR = {
    "gennaio": "gen",
    "febbraio": "feb",
    "marzo": "mar",
    "aprile": "apr",
    "maggio": "mag",
    "giugno": "giu",
    "luglio": "lug",
    "agosto": "ago",
    "settembre": "set",
    "ottobre": "ott",
    "novembre": "nov",
    "dicembre": "dic",
}

IT_MONTH_ABBR_TO_FULL = {value: key for key, value in IT_MONTH_FULL_TO_ABBR.items()}
MONTH_LABEL_PATTERN = re.compile(
    r"^(gen|feb|mar|apr|mag|giu|lug|ago|set|ott|nov|dic)-(\d{4})$",
    re.IGNORECASE,
)
QUARTER_LABEL_PATTERN = re.compile(r"^q([1-4])-(\d{4})$", re.IGNORECASE)


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


def _json_response(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


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


def _normalize_period_lookup(value: object) -> str:
    normalized = _normalize_lookup(value)
    tokens = [IT_MONTH_FULL_TO_ABBR.get(token, token) for token in normalized.split()]
    return " ".join(tokens)


def _phrase_position(text: str, phrase: str) -> int:
    if not phrase:
        return -1
    match = re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", text)
    return match.start() if match else -1


def _contains_phrase(text: str, phrase: str) -> bool:
    return _phrase_position(text, phrase) >= 0


def _period_aliases(value: object) -> set[str]:
    text = str(value).strip()
    lower = text.lower()
    aliases = {_normalize_lookup(text), _normalize_period_lookup(text)}

    month_match = MONTH_LABEL_PATTERN.fullmatch(lower)
    if month_match:
        month_txt, year_txt = month_match.groups()
        full_month = IT_MONTH_ABBR_TO_FULL[month_txt]
        aliases.update(
            {
                _normalize_period_lookup(month_txt),
                _normalize_period_lookup(full_month),
                _normalize_period_lookup(f"{month_txt} {year_txt}"),
                _normalize_period_lookup(f"{full_month} {year_txt}"),
            }
        )

    quarter_match = QUARTER_LABEL_PATTERN.fullmatch(lower)
    if quarter_match:
        quarter_txt, year_txt = quarter_match.groups()
        aliases.update(
            {
                _normalize_period_lookup(f"q{quarter_txt}"),
                _normalize_period_lookup(f"q{quarter_txt} {year_txt}"),
                _normalize_period_lookup(f"trimestre {quarter_txt}"),
                _normalize_period_lookup(f"trimestre {quarter_txt} {year_txt}"),
            }
        )

    return {alias for alias in aliases if alias}


def _preferred_period_columns(frame: pd.DataFrame) -> list[str]:
    return [column for column in ("mese", "trimestre") if column in frame.columns]


def _period_order(frame: pd.DataFrame, column: str, value: str) -> int:
    rows = _match_rows(frame, column, value)
    if rows.empty:
        return 0
    if "mese_dt" in rows.columns:
        return int(rows["mese_dt"].max().value)
    if "period_order" in rows.columns:
        return int(rows["period_order"].max())
    return 0


def _iter_period_matches(query: str, frame: pd.DataFrame) -> list[PeriodMatch]:
    query_norm = _normalize_period_lookup(query)
    if not query_norm:
        return []

    query_tokens = set(query_norm.split())
    matches: dict[tuple[str, str], PeriodMatch] = {}
    for column in _preferred_period_columns(frame):
        values = frame[column].dropna().astype(str).str.strip().unique().tolist()
        for value in values:
            aliases = _period_aliases(value)
            if not aliases:
                continue

            score = max(SequenceMatcher(None, query_norm, alias).ratio() for alias in aliases)
            if query_norm in aliases:
                score = 1.0
            elif any(_contains_phrase(query_norm, alias) for alias in aliases):
                score = max(score, 0.97)
            elif any(_contains_phrase(alias, query_norm) for alias in aliases):
                score = max(score, 0.93)
            elif any(set(alias.split()).issubset(query_tokens) for alias in aliases):
                score = max(score, 0.91)

            key = (column, value)
            previous = matches.get(key)
            if previous is None or score > previous.score:
                matches[key] = PeriodMatch(column=column, value=value, score=score)

    return sorted(
        matches.values(),
        key=lambda item: (item.score, _period_order(frame, item.column, item.value)),
        reverse=True,
    )


def _best_period_match(query: str, frame: pd.DataFrame) -> PeriodMatch | None:
    matches = _iter_period_matches(query, frame)
    if not matches:
        return None
    best = matches[0]
    if best.score < 0.72:
        return None
    return best


def _find_period_mentions(query: str, frame: pd.DataFrame) -> list[PeriodMention]:
    query_norm = _normalize_period_lookup(query)
    if not query_norm:
        return []

    mentions: list[PeriodMention] = []
    for match in _iter_period_matches(query, frame):
        best_position: int | None = None
        best_alias = ""
        for alias in sorted(_period_aliases(match.value), key=len, reverse=True):
            position = _phrase_position(query_norm, alias)
            if position >= 0 and (best_position is None or position < best_position):
                best_position = position
                best_alias = alias
        if best_position is not None:
            mentions.append(PeriodMention(match=match, position=best_position, alias=best_alias))

    mentions.sort(key=lambda item: (item.position, -len(item.alias), -item.match.score))
    deduped: list[PeriodMention] = []
    seen: set[tuple[str, str]] = set()
    for mention in mentions:
        key = (mention.match.column, mention.match.value)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(mention)
    return deduped


def _ordered_period_matches(frame: pd.DataFrame, column: str) -> list[PeriodMatch]:
    values = frame[column].dropna().astype(str).str.strip().unique().tolist()
    matches = [PeriodMatch(column=column, value=value, score=1.0) for value in values]
    return sorted(matches, key=lambda item: _period_order(frame, item.column, item.value))


def _previous_period_match(frame: pd.DataFrame, period_match: PeriodMatch) -> PeriodMatch | None:
    ordered = _ordered_period_matches(frame, period_match.column)
    for index, candidate in enumerate(ordered):
        if candidate.value == period_match.value and candidate.column == period_match.column:
            if index == 0:
                return None
            return ordered[index - 1]
    return None


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


def _unmatched_payload(
    artifacts: DatasetArtifacts,
    *,
    query: str | None = None,
    period_query: str | None = None,
    matched_value: str | None = None,
    matched_column: str | None = None,
) -> JsonObject:
    payload: JsonObject = {"matched": False, "source_path": artifacts.source_path}
    if query is not None:
        payload["query"] = query
    if period_query is not None:
        payload["period_query"] = period_query
    if matched_value is not None:
        payload["matched_value"] = matched_value
    if matched_column is not None:
        payload["matched_column"] = matched_column
    return payload


def _entity_summary_payload(match: EntityMatch, analysis_df: pd.DataFrame, artifacts: DatasetArtifacts) -> JsonObject:
    rows = _match_rows(analysis_df, match.column, match.value)
    if rows.empty:
        return _unmatched_payload(artifacts, query=match.value)

    payload: JsonObject = {
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

    return payload


def _entity_period_summary_payload(
    entity_match: EntityMatch,
    period_match: PeriodMatch,
    analysis_df: pd.DataFrame,
    artifacts: DatasetArtifacts,
) -> dict[str, object]:
    entity_rows = _match_rows(analysis_df, entity_match.column, entity_match.value)
    if entity_rows.empty:
        return _unmatched_payload(artifacts, query=entity_match.value)

    period_rows = _match_rows(entity_rows, period_match.column, period_match.value)
    if period_rows.empty:
        return _unmatched_payload(artifacts, query=entity_match.value, period_query=period_match.value)

    payload: JsonObject = {
        "matched": True,
        "matched_value": entity_match.value,
        "matched_column": entity_match.column,
        "period_column": period_match.column,
        "period_value": period_match.value,
        "row_count": int(len(period_rows)),
        "source_path": artifacts.source_path,
        "raw_table": artifacts.raw_table,
        "analysis_table": artifacts.analysis_table,
    }

    if "revenue_cumulativa_eur" in period_rows.columns:
        latest = _latest_entity_row(period_rows)
        payload["business_rule"] = (
            "Per i dataset con colonne cumulative, il valore del periodo richiesto va letto "
            "come snapshot cumulativo di quel mese e non come somma delle righe."
        )
        payload["metric_name"] = "period_cumulative_revenue_eur"
        payload["metric_value"] = float(latest["revenue_cumulativa_eur"])
        if "revenue_eur" in latest.index:
            payload["period_incremental_revenue_eur"] = float(latest["revenue_eur"])
    elif "revenue_eur" in period_rows.columns:
        payload["metric_name"] = "period_revenue_eur"
        payload["metric_value"] = float(period_rows["revenue_eur"].sum())
    elif "value" in period_rows.columns:
        payload["metric_name"] = "period_value"
        payload["metric_value"] = float(period_rows["value"].sum())
    else:
        payload["available_columns"] = period_rows.columns.tolist()

    preview_columns = [
        column
        for column in ("mese", "trimestre", "revenue_eur", "revenue_cumulativa_eur", "value")
        if column in period_rows.columns
    ]
    if preview_columns:
        payload["preview"] = period_rows[preview_columns].head(6).to_dict(orient="records")

    return payload


def _format_number(value: float) -> str:
    rounded = round(value)
    if abs(value - rounded) < 0.005:
        return f"{int(rounded):,}".replace(",", ".")
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _is_incremental_period_request(question: str) -> bool:
    normalized = _normalize_period_lookup(question)
    signals = (
        "sottra",
        "differenz",
        "delta",
        "increment",
        "incrementale",
        "solo ",
        "solo dicembre",
        "nel solo",
        "mese",
        "mese su mese",
    )
    return any(signal in normalized for signal in signals)


def _build_direct_period_answer(payload: dict[str, object], dataset_name: str) -> str:
    entity = str(payload["matched_value"])
    period = str(payload["period_value"])
    metric_name = str(payload.get("metric_name", ""))
    metric_value = float(payload.get("metric_value", 0))
    formatted_value = _format_number(metric_value)

    if metric_name == "period_cumulative_revenue_eur":
        return (
            f"Nel dataset `{dataset_name}`, `{entity}` a `{period}` ha raggiunto "
            f"`{formatted_value} EUR` cumulati."
        )
    if metric_name == "period_revenue_eur":
        return (
            f"Nel dataset `{dataset_name}`, `{entity}` in `{period}` ha registrato "
            f"`{formatted_value} EUR` di revenue."
        )
    if metric_name == "period_value":
        return (
            f"Nel dataset `{dataset_name}`, `{entity}` in `{period}` ha valore "
            f"`{formatted_value}`."
        )
    return (
        f"Nel dataset `{dataset_name}`, `{entity}` in `{period}` ho trovato il dato richiesto "
        "nel periodo specificato."
    )


def _build_incremental_period_answer(
    *,
    dataset_name: str,
    entity: str,
    current_period: str,
    previous_period: str,
    current_value: float,
    previous_value: float,
) -> str:
    delta = current_value - previous_value
    return (
        f"Nel dataset `{dataset_name}`, il valore del solo `{current_period}` per `{entity}` e` "
        f"`{_format_number(delta)} EUR`, calcolato come `{current_period}` (`{_format_number(current_value)}`) "
        f"meno `{previous_period}` (`{_format_number(previous_value)}`)."
    )


def _deterministic_answer(
    *,
    text: str,
    references: list[AnswerReference] | None,
    question: str,
    memory,
    conversation_focus: str | None,
) -> AnswerPayload:
    return AnswerPayload(
        text=text,
        references=references or [],
        conversation_focus=conversation_focus,
        memory=_with_memory_turns(memory, question, text),
    )


def _sanitize_memory(memory):
    if memory is None:
        return None
    if not hasattr(memory, "json_dumps"):
        return memory

    try:
        from datapizza.memory import Memory
    except ImportError:
        return memory

    sanitized = Memory()
    try:
        sanitized.json_loads(memory.json_dumps())
    except Exception:
        return memory
    return sanitized


def _with_memory_turns(memory, user_text: str, assistant_text: str):
    sanitized = _sanitize_memory(memory)
    try:
        from datapizza.memory import Memory
        from datapizza.type import ROLE, TextBlock
    except ImportError:
        return sanitized

    if sanitized is None:
        sanitized = Memory()

    try:
        sanitized.add_turn(TextBlock(content=user_text), role=ROLE.USER)
        sanitized.add_turn(TextBlock(content=assistant_text), role=ROLE.ASSISTANT)
    except Exception:
        return _sanitize_memory(memory)
    return sanitized


def _last_user_message(memory) -> str | None:
    sanitized = _sanitize_memory(memory)
    if sanitized is None:
        return None

    turns = getattr(sanitized, "memory", None)
    if not isinstance(turns, list):
        return None

    for turn in reversed(turns):
        role = getattr(getattr(turn, "role", None), "value", getattr(turn, "role", None))
        if role != "user":
            continue
        for block in getattr(turn, "blocks", []):
            content = getattr(block, "content", None)
            if isinstance(content, str) and content.strip():
                return content.strip()
    return None


def _try_memory_answer(question: str, memory, conversation_focus: str | None) -> AnswerPayload | None:
    normalized = _normalize_lookup(question)
    if not any(phrase in normalized for phrase in ("ti ricordi", "cosa ti ho chiesto", "richiesta prima", "messaggio prima")):
        return None

    previous_user = _last_user_message(memory)
    if previous_user is None:
        text = "Non ho ancora un contesto precedente salvato in questa chat da richiamare."
    else:
        text = f"Sì. Subito prima mi avevi chiesto: `{previous_user}`."

    return _deterministic_answer(
        text=text,
        references=[],
        question=question,
        memory=memory,
        conversation_focus=conversation_focus,
    )


def _try_direct_entity_period_answer(
    question: str,
    artifacts: DatasetArtifacts,
    analysis_df: pd.DataFrame,
    conversation_focus: str | None,
    memory=None,
) -> AnswerPayload | None:
    entity_match = _best_entity_match(question, analysis_df)
    if entity_match is None and conversation_focus:
        entity_match = _best_entity_match(conversation_focus, analysis_df)
    if entity_match is None:
        return None

    entity_rows = _match_rows(analysis_df, entity_match.column, entity_match.value)
    if entity_rows.empty:
        return None

    if "revenue_cumulativa_eur" in entity_rows.columns and _is_incremental_period_request(question):
        mentions = _find_period_mentions(question, entity_rows)
        current_mention = mentions[0] if mentions else None
        if current_mention is None:
            period_match = _best_period_match(question, entity_rows) or _best_period_match(question, analysis_df)
            current_mention = PeriodMention(match=period_match, position=0, alias="") if period_match else None

        if current_mention is not None:
            previous_match = (
                mentions[1].match
                if len(mentions) > 1 and mentions[1].match.column == current_mention.match.column
                else _previous_period_match(entity_rows, current_mention.match)
            )
            if previous_match is not None:
                current_payload = _entity_period_summary_payload(entity_match, current_mention.match, analysis_df, artifacts)
                previous_payload = _entity_period_summary_payload(entity_match, previous_match, analysis_df, artifacts)
                if (
                    current_payload.get("metric_name") == "period_cumulative_revenue_eur"
                    and previous_payload.get("metric_name") == "period_cumulative_revenue_eur"
                ):
                    current_value = float(current_payload["metric_value"])
                    previous_value = float(previous_payload["metric_value"])
                    answer_text = _build_incremental_period_answer(
                        dataset_name=artifacts.dataset_name,
                        entity=entity_match.value,
                        current_period=str(current_payload["period_value"]),
                        previous_period=str(previous_payload["period_value"]),
                        current_value=current_value,
                        previous_value=previous_value,
                    )
                    return _deterministic_answer(
                        text=answer_text,
                        references=[
                            _dataset_reference(
                                artifacts,
                                matched_column=entity_match.column,
                                matched_value=entity_match.value,
                                note="Risposta deterministica su delta tra periodi cumulativi",
                            )
                        ],
                        question=question,
                        memory=memory,
                        conversation_focus=entity_match.value,
                    )

    period_match = _best_period_match(question, entity_rows)
    if period_match is None:
        period_match = _best_period_match(question, analysis_df)
    if period_match is None:
        return None

    payload = _entity_period_summary_payload(entity_match, period_match, analysis_df, artifacts)
    if not payload.get("matched"):
        return None

    answer_text = _build_direct_period_answer(payload, artifacts.dataset_name)
    return _deterministic_answer(
        text=answer_text,
        references=[
            _dataset_reference(
                artifacts,
                matched_column=entity_match.column,
                matched_value=entity_match.value,
                note="Risposta deterministica per entità e periodo specifico",
            )
        ],
        question=question,
        memory=memory,
        conversation_focus=entity_match.value,
    )


def answer_question(
    question: str,
    settings: Settings,
    artifacts: DatasetArtifacts,
    analysis_df: pd.DataFrame,
    memory=None,
    conversation_focus: str | None = None,
) -> AnswerPayload:
    memory_answer = _try_memory_answer(question, memory, conversation_focus)
    if memory_answer is not None:
        return memory_answer

    direct_answer = _try_direct_entity_period_answer(
        question,
        artifacts,
        analysis_df,
        conversation_focus,
        memory=memory,
    )
    if direct_answer is not None:
        return direct_answer

    if not settings.openai_api_key:
        raise RuntimeError("Chiave OpenAI assente. Inserisci `Openai` nel file .env.")
    if not artifacts.collection_name:
        raise RuntimeError("Il dataset non è stato indicizzato per il retrieval.")

    try:
        from datapizza.agents import Agent
        from datapizza.clients.openai import OpenAIClient
        from datapizza.embedders.openai import OpenAIEmbedder
        from datapizza.memory import Memory
        from datapizza.tools import tool
        from datapizza.tools.SQLDatabase import SQLDatabase
        from datapizza.tracing import ContextTracing
    except ImportError as exc:
        raise RuntimeError(
            "Dipendenze Datapizza non installate. Usa Python 3.10+ e installa requirements.txt."
        ) from exc

    safe_memory = _sanitize_memory(memory) or Memory()
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
        return _json_response(
            {
                "dataset_id": artifacts.dataset_id,
                "dataset_name": artifacts.dataset_name,
                "dataset_kind": artifacts.dataset_kind,
                "source_path": artifacts.source_path,
                "raw_table": artifacts.raw_table,
                "analysis_table": artifacts.analysis_table,
                "row_count": artifacts.row_count,
                "analysis_row_count": artifacts.analysis_row_count,
            }
        )

    @tool
    def resolve_entity_reference(entity_query: str) -> str:
        """Trova la migliore corrispondenza flessibile per una testata o altro valore testuale nel dataset attivo."""
        matches = _iter_entity_matches(entity_query, analysis_df)
        top_matches = matches[:5]
        if not top_matches:
            return _json_response(_unmatched_payload(artifacts, query=entity_query))

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
        return _json_response(
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
            }
        )

    @tool
    def get_entity_business_summary(entity_query: str) -> str:
        """Restituisce un riepilogo deterministico per una testata o entità nominale, gestendo correttamente le colonne cumulative."""
        match = _best_entity_match(entity_query, analysis_df)
        if match is None:
            return _json_response(_unmatched_payload(artifacts, query=entity_query))

        reference_state["conversation_focus"] = match.value
        _add_reference(
            _dataset_reference(
                artifacts,
                matched_column=match.column,
                matched_value=match.value,
                note="Riepilogo deterministico su entità con gestione dei cumulativi",
            )
        )
        return _json_response(_entity_summary_payload(match, analysis_df, artifacts))

    @tool
    def get_entity_period_business_summary(entity_query: str, period_query: str) -> str:
        """Restituisce un riepilogo deterministico per una entità in un periodo specifico del dataset attivo."""
        entity_match = _best_entity_match(entity_query, analysis_df)
        if entity_match is None:
            return _json_response(_unmatched_payload(artifacts, query=entity_query, period_query=period_query))

        entity_rows = _match_rows(analysis_df, entity_match.column, entity_match.value)
        period_match = _best_period_match(period_query, entity_rows)
        if period_match is None:
            period_match = _best_period_match(period_query, analysis_df)
        if period_match is None:
            return _json_response(
                _unmatched_payload(
                    artifacts,
                    matched_value=entity_match.value,
                    matched_column=entity_match.column,
                    period_query=period_query,
                )
            )

        reference_state["conversation_focus"] = entity_match.value
        _add_reference(
            _dataset_reference(
                artifacts,
                matched_column=entity_match.column,
                matched_value=entity_match.value,
                note="Riepilogo deterministico su entità e periodo specifico",
            )
        )
        return _json_response(_entity_period_summary_payload(entity_match, period_match, analysis_df, artifacts))

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
        "Per domande su un mese, trimestre o periodo specifico usa prima get_entity_period_business_summary.",
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
        memory=safe_memory,
        system_prompt=" ".join(system_prompt_parts),
        tools=[
            get_active_dataset_metadata,
            resolve_entity_reference,
            get_entity_business_summary,
            get_entity_period_business_summary,
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
        memory=_sanitize_memory(getattr(agent, "_memory", None)),
    )
