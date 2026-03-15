from __future__ import annotations

from pathlib import Path

import plotly.express as px
import streamlit as st

from dashboard_rag.catalog import DatasetEntry, discover_datasets
from dashboard_rag.charting import build_charts, build_insights, build_kpis
from dashboard_rag.config import has_openai_key, load_settings
from dashboard_rag.ingestion import DatasetArtifacts, build_dataset_frames, ensure_dataset_assets
from dashboard_rag.monitoring import MonitoringStore, monitored_operation
from dashboard_rag.rag import answer_question


def _dataset_lookup(entries: list[DatasetEntry]) -> dict[str, DatasetEntry]:
    return {entry.dataset_id: entry for entry in entries}


def _save_uploaded_file(target_dir: Path, uploaded_file) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / uploaded_file.name
    output_path.write_bytes(uploaded_file.getbuffer())
    return output_path


def _render_kpis(kpis: list[tuple[str, str]]) -> None:
    columns = st.columns(len(kpis))
    for column, (label, value) in zip(columns, kpis):
        column.metric(label, value)


def _render_monitoring(store: MonitoringStore, selected_dataset: DatasetEntry) -> None:
    events = store.load_events()
    if events.empty:
        st.info("Nessun evento registrato ancora.")
        return

    dataset_events = events.loc[(events["dataset_id"].isna()) | (events["dataset_id"] == selected_dataset.dataset_id)].copy()
    if dataset_events.empty:
        st.info("Nessun evento per il dataset selezionato.")
        return

    latency = dataset_events["duration_ms"].dropna()
    failures = dataset_events.loc[dataset_events["status"] == "error"]
    monitoring_kpis = [
        ("Eventi", str(len(dataset_events))),
        ("Errori", str(len(failures))),
        ("Latenza media", f"{latency.mean():.1f} ms" if not latency.empty else "n/d"),
    ]
    _render_kpis(monitoring_kpis)

    counts = dataset_events.groupby("event_type", as_index=False).size()
    counts_chart = px.bar(counts, x="event_type", y="size", color="event_type")
    counts_chart.update_layout(showlegend=False, xaxis_title="Evento", yaxis_title="Conteggio")
    st.plotly_chart(counts_chart, use_container_width=True)

    timed = dataset_events.dropna(subset=["duration_ms"]).sort_values("timestamp")
    if not timed.empty:
        duration_chart = px.line(timed, x="timestamp", y="duration_ms", color="event_type", markers=True)
        duration_chart.update_layout(xaxis_title="Timestamp", yaxis_title="Durata (ms)")
        st.plotly_chart(duration_chart, use_container_width=True)

    st.dataframe(dataset_events[["timestamp", "event_type", "status", "dataset_id", "duration_ms", "metadata"]], use_container_width=True)


def _ensure_assets(
    selected_dataset: DatasetEntry,
    settings,
    store: MonitoringStore,
) -> DatasetArtifacts:
    cache_key = f"assets::{selected_dataset.dataset_id}"
    cached = st.session_state.get(cache_key)
    if cached is not None:
        return cached

    with monitored_operation(
        store,
        "dataset_index",
        dataset_id=selected_dataset.dataset_id,
        metadata={"dataset_kind": selected_dataset.kind},
    ):
        assets = ensure_dataset_assets(selected_dataset, settings)

    st.session_state[cache_key] = assets
    return assets


def main() -> None:
    settings = load_settings()
    store = MonitoringStore(settings.monitoring_path)

    st.set_page_config(page_title="Mondadori Datapizza Dashboard", layout="wide")
    st.title("Mondadori Datapizza Dashboard")
    st.caption("Dashboard CSV + RAG + monitoring con Datapizza AI e OpenAI.")

    datasets = discover_datasets(settings)
    if not datasets:
        st.error("Nessun CSV trovato. Aggiungi file nella root della repo o in datapizza_dashboard_rag/datasets.")
        return

    dataset_by_id = _dataset_lookup(datasets)

    st.sidebar.header("Dataset")
    selected_dataset_id = st.sidebar.selectbox(
        "Scegli il file CSV da considerare",
        options=[entry.dataset_id for entry in datasets],
        format_func=lambda item: dataset_by_id[item].label,
    )
    selected_dataset = dataset_by_id[selected_dataset_id]

    uploaded = st.sidebar.file_uploader("Aggiungi un nuovo CSV", type=["csv"])
    if uploaded and st.sidebar.button("Salva CSV nella cartella datasets"):
        saved_path = _save_uploaded_file(settings.datasets_dir, uploaded)
        st.sidebar.success(f"CSV salvato in {saved_path.name}. Riavvia o aggiorna la pagina.")

    st.sidebar.markdown(f"**File attivo:** `{selected_dataset.path.name}`")
    st.sidebar.markdown(f"**Tipo riconosciuto:** `{selected_dataset.kind}`")
    st.sidebar.markdown(f"**OpenAI configurato:** `{'sì' if has_openai_key(settings) else 'no'}`")
    st.sidebar.markdown("**Nota runtime:** `datapizza-ai` richiede Python 3.10+.")

    raw_df, analysis_df = build_dataset_frames(selected_dataset)

    dashboard_tab, rag_tab, monitoring_tab = st.tabs(["Dashboard", "RAG", "Monitoring"])

    with dashboard_tab:
        with monitored_operation(
            store,
            "dashboard_render",
            dataset_id=selected_dataset.dataset_id,
            metadata={"dataset_kind": selected_dataset.kind},
        ):
            st.subheader(selected_dataset.name)
            st.write(selected_dataset.description)
            _render_kpis(build_kpis(selected_dataset, analysis_df))

            for insight in build_insights(selected_dataset, analysis_df):
                st.markdown(f"- {insight}")

            for chart in build_charts(selected_dataset, analysis_df):
                st.markdown(f"### {chart.title}")
                st.caption(chart.caption)
                st.plotly_chart(chart.figure, use_container_width=True)

            with st.expander("Anteprima dati"):
                st.markdown("**Raw**")
                st.dataframe(raw_df, use_container_width=True)
                st.markdown("**Analysis**")
                st.dataframe(analysis_df, use_container_width=True)

    with rag_tab:
        st.subheader("Interroga il dataset attivo")
        st.write(
            "La chat indicizza il CSV selezionato in SQLite e Qdrant locale, poi usa un agente Datapizza con retrieval semantico e query SQL."
        )

        if not has_openai_key(settings):
            st.warning("Chiave OpenAI non trovata nel `.env`. Imposta `Openai=...` per abilitare il RAG.")
        else:
            st.caption(f"Dataset attivo per la chat: `{selected_dataset.name}`")

            history_key = f"chat::{selected_dataset.dataset_id}"
            history = st.session_state.setdefault(history_key, [])
            for item in history:
                with st.chat_message(item["role"]):
                    st.markdown(item["content"])

            user_question = st.chat_input("Fai una domanda sul dataset attivo")
            if user_question:
                history.append({"role": "user", "content": user_question})
                with st.chat_message("user"):
                    st.markdown(user_question)

                with st.chat_message("assistant"):
                    try:
                        assets = _ensure_assets(selected_dataset, settings, store)
                        with monitored_operation(
                            store,
                            "rag_query",
                            dataset_id=selected_dataset.dataset_id,
                            metadata={"question": user_question[:120]},
                        ):
                            answer = answer_question(user_question, settings, assets)
                    except Exception as exc:
                        answer = f"Errore durante l'esecuzione RAG: {exc}"
                    st.markdown(answer)

                history.append({"role": "assistant", "content": answer})

            if st.button("Indicizza ora il dataset attivo"):
                try:
                    assets = _ensure_assets(selected_dataset, settings, store)
                except Exception as exc:
                    st.error(str(exc))
                else:
                    st.success(
                        f"Indicizzazione completata. Tabelle: `{assets.raw_table}`, `{assets.analysis_table}`. Collection: `{assets.collection_name or 'non creata'}`."
                    )

    with monitoring_tab:
        st.subheader("Monitoring locale")
        _render_monitoring(store, selected_dataset)


if __name__ == "__main__":
    main()
