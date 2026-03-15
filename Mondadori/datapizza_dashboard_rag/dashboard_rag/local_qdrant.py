from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from datapizza.core.vectorstore import VectorConfig
from datapizza.type import Chunk, DenseEmbedding, EmbeddingFormat, SparseEmbedding
from qdrant_client import QdrantClient, models


@dataclass(frozen=True)
class SearchChunk:
    text: str


class LocalQdrantVectorstore:
    _clients: ClassVar[dict[str, QdrantClient]] = {}

    def __init__(self, path: str):
        self.path = path
        if path not in self._clients:
            self._clients[path] = QdrantClient(path=path)
        self.client = self._clients[path]

    def get_collections(self):
        return self.client.get_collections().collections

    def create_collection(self, collection_name: str, vector_config: list[VectorConfig], **kwargs) -> None:
        if self.client.collection_exists(collection_name):
            return

        dense_config = {
            v.name: models.VectorParams(
                size=v.dimensions,
                distance=v.distance.value,
            )
            for v in vector_config
            if v.format == EmbeddingFormat.DENSE
        }
        sparse_config = {
            v.name: models.SparseVectorParams()
            for v in vector_config
            if v.format == EmbeddingFormat.SPARSE
        }

        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=dense_config or None,
            sparse_vectors_config=sparse_config or None,
            **kwargs,
        )

    def add(self, chunks: Chunk | list[Chunk], collection_name: str) -> None:
        items = [chunks] if isinstance(chunks, Chunk) else chunks
        points = [self._process_chunk(chunk) for chunk in items]
        self.client.upsert(collection_name=collection_name, points=points, wait=True)

    def search(
        self,
        collection_name: str,
        query_vector: list[float] | SparseEmbedding | dict,
        k: int = 10,
        vector_name: str | None = None,
    ) -> list[SearchChunk]:
        using = None

        if isinstance(query_vector, list) and all(isinstance(v, float) for v in query_vector):
            if not vector_name:
                collection = self.client.get_collection(collection_name)
                vectors = collection.config.params.vectors
                if isinstance(vectors, dict):
                    names = list(vectors.keys())
                    if len(names) > 1:
                        raise ValueError(
                            "Vector name not specified and multiple dense vectors are configured."
                        )
                    if names:
                        vector_name = names[0]
            using = vector_name
            qry = query_vector
        elif isinstance(query_vector, dict):
            qry = models.SparseVector(
                indices=query_vector.get("indices", []),
                values=query_vector.get("values", []),
            )
            using = vector_name or "default"
        elif isinstance(query_vector, SparseEmbedding):
            qry = models.SparseVector(indices=query_vector.indices, values=query_vector.values)
            using = query_vector.name
        else:
            raise ValueError(f"Unsupported query vector type: {type(query_vector)}")

        hits = self.client.query_points(
            collection_name=collection_name,
            query=qry,
            using=using,
            limit=k,
            with_payload=True,
        )
        return [SearchChunk(text=point.payload["text"]) for point in hits.points if point.payload and "text" in point.payload]

    def _process_chunk(self, chunk: Chunk) -> models.PointStruct:
        if not chunk.embeddings:
            raise ValueError("Chunk must have an embedding")

        if len(chunk.embeddings) == 1 and isinstance(chunk.embeddings[0], DenseEmbedding):
            embedding = chunk.embeddings[0]
            vector: dict[str, list[float] | models.SparseVector] | list[float]
            if embedding.name is None:
                vector = embedding.vector
            else:
                vector = {embedding.name: embedding.vector}
        else:
            vector = {}
            for embedding in chunk.embeddings:
                if isinstance(embedding, DenseEmbedding):
                    if embedding.name is None:
                        raise ValueError("Unnamed vector found in chunk with multiple embeddings")
                    vector[embedding.name] = embedding.vector
                elif isinstance(embedding, SparseEmbedding):
                    vector[embedding.name] = models.SparseVector(
                        values=embedding.values,
                        indices=embedding.indices,
                    )
                else:
                    raise ValueError(f"Unsupported embedding type: {type(embedding)}")

        return models.PointStruct(
            id=str(chunk.id),
            payload={"text": chunk.text, **chunk.metadata},
            vector=vector,
        )
