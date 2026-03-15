from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .config import Settings
from .ingestion import DatasetArtifacts


def answer_question(question: str, settings: Settings, artifacts: DatasetArtifacts) -> str:
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
        from datapizza.vectorstores.qdrant import QdrantVectorstore
    except ImportError as exc:
        raise RuntimeError(
            "Dipendenze Datapizza non installate. Usa Python 3.10+ e installa requirements.txt."
        ) from exc

    client = OpenAIClient(api_key=settings.openai_api_key, model=settings.chat_model)
    embedder = OpenAIEmbedder(api_key=settings.openai_api_key)
    vectorstore = QdrantVectorstore(location=str(settings.qdrant_dir / "local_qdrant"))
    sql_tool = SQLDatabase(db_uri=f"sqlite:///{settings.sqlite_path}")
    profile_text = Path(artifacts.profile_path).read_text(encoding="utf-8")

    @tool
    def get_active_dataset_metadata() -> str:
        """Restituisce i metadati del dataset attivo nella dashboard."""
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
    def retrieve_dataset_context(query: str) -> str:
        """Recupera il contesto semantico del dataset attivo dal vector store locale."""
        query_vector = embedder.embed(query, model_name=settings.embedding_model)
        chunks = vectorstore.search(
            collection_name=artifacts.collection_name,
            query_vector=query_vector,
            k=4,
        )

        if not chunks:
            return profile_text

        parts: List[str] = []
        for index, chunk in enumerate(chunks, start=1):
            parts.append(f"[chunk {index}] {chunk.text}")
        return "\n\n".join(parts)

    agent = Agent(
        name="mondadori_dashboard_analyst",
        client=client,
        max_steps=6,
        system_prompt=(
            "Sei un data analyst specializzato sui dataset mostrati in dashboard. "
            "Usa sempre i tool disponibili per basarti sui dati reali. "
            "Per contesto e definizioni usa retrieve_dataset_context. "
            "Per numeri, confronti, ranking e aggregazioni usa SQL sulle tabelle del dataset attivo. "
            "Non inventare colonne o periodi. Se il dato non c'è, dillo esplicitamente. "
            "Nella risposta finale cita il dataset attivo e, quando utile, la query o il criterio usato."
        ),
        tools=[
            get_active_dataset_metadata,
            retrieve_dataset_context,
            sql_tool.list_tables,
            sql_tool.get_table_schema,
            sql_tool.run_sql_query,
        ],
    )

    with ContextTracing().trace(f"rag_{artifacts.dataset_id}"):
        response = agent.run(question)

    return response.text.strip()

