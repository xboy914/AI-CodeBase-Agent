from hashlib import sha256
from typing import Iterable
from uuid import UUID

from openai import OpenAI
from qdrant_client import QdrantClient, models

from .chunker import CodeChunk
from .config import Settings


class CodeStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.openai = OpenAI(api_key=settings.openai_api_key)
        self.client = (
            QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
            if settings.qdrant_url
            else QdrantClient(path=".qdrant")
        )

    def _embed(self, texts: list[str]) -> list[list[float]]:
        response = self.openai.embeddings.create(
            model=self.settings.embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def replace(self, chunks: Iterable[CodeChunk]) -> int:
        items = list(chunks)
        if not items:
            return 0

        vectors = self._embed([item.content for item in items])
        size = len(vectors[0])
        collection = self.settings.qdrant_collection

        if self.client.collection_exists(collection):
            self.client.delete_collection(collection)

        self.client.create_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(size=size, distance=models.Distance.COSINE),
        )

        points = []
        for item, vector in zip(items, vectors, strict=True):
            digest = sha256(
                f"{item.path}:{item.start_line}:{item.end_line}".encode()
            ).digest()[:16]
            points.append(
                models.PointStruct(
                    id=str(UUID(bytes=digest)),
                    vector=vector,
                    payload={
                        "path": item.path,
                        "start_line": item.start_line,
                        "end_line": item.end_line,
                        "content": item.content,
                    },
                )
            )

        self.client.upsert(collection_name=collection, points=points, wait=True)
        return len(points)

    def search(self, query: str, limit: int) -> list[dict]:
        vector = self._embed([query])[0]
        result = self.client.query_points(
            collection_name=self.settings.qdrant_collection,
            query=vector,
            limit=limit,
            with_payload=True,
        )
        return [point.payload or {} for point in result.points]
