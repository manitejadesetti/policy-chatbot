from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app_backend.config import get_env


@dataclass(frozen=True)
class QdrantCollectionHandle:
    """Small collection facade to keep call sites compatible with previous DB API."""

    repository: "QdrantRepository"
    name: str

    def count(self) -> int:
        return self.repository.count(self.name)


class QdrantRepository:
    def __init__(self) -> None:
        self.url = get_env("QDRANT_URL", "http://localhost:6333")
        self.api_key = get_env("QDRANT_API_KEY")
        self.vector_size = int(get_env("EMBEDDING_DIM", "384"))

        # Use URL mode by default; this supports both local and cloud Qdrant.
        if self.api_key:
            self.client = QdrantClient(url=self.url, api_key=self.api_key)
        else:
            self.client = QdrantClient(url=self.url)

    def get_or_create_collection(self, collection_name: str) -> QdrantCollectionHandle:
        existing = {
            collection.name for collection in self.client.get_collections().collections
        }
        if collection_name not in existing:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )
        return QdrantCollectionHandle(repository=self, name=collection_name)

    def add(
        self,
        collection_name: str,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
    ) -> None:
        points = [
            PointStruct(id=point_id, vector=vector, payload={"document": doc})
            for point_id, doc, vector in zip(ids, documents, embeddings, strict=False)
        ]
        self.client.upsert(collection_name=collection_name, points=points)

    def query(
        self,
        collection_name: str,
        query_embeddings: list[list[float]],
        n_results: int,
    ) -> dict[str, Any]:
        if not query_embeddings:
            return {"documents": [[]]}

        hits = self.client.search(
            collection_name=collection_name,
            query_vector=query_embeddings[0],
            limit=n_results,
            with_payload=True,
        )
        documents = [
            (hit.payload or {}).get("document", "")
            for hit in hits
            if (hit.payload or {}).get("document")
        ]
        return {"documents": [documents]}

    def count(self, collection_name: str) -> int:
        result = self.client.count(collection_name=collection_name, exact=True)
        return int(result.count)
