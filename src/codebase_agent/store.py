from collections.abc import Iterable
from dataclasses import dataclass
from hashlib import sha256
from uuid import UUID

from openai import OpenAI
from qdrant_client import QdrantClient, models

from .chunker import CodeChunk
from .config import Settings


@dataclass(frozen=True)
class IndexPlan:
    changed: set[str]
    unchanged: set[str]
    deleted: set[str]


@dataclass(frozen=True)
class SyncResult:
    chunks: int
    indexed_files: int
    unchanged_files: int
    deleted_files: int


def build_index_plan(current: dict[str, str], stored: dict[str, str]) -> IndexPlan:
    current_paths = set(current)
    stored_paths = set(stored)
    unchanged = {path for path in current_paths & stored_paths if current[path] == stored[path]}
    return IndexPlan(
        changed=current_paths - unchanged,
        unchanged=unchanged,
        deleted=stored_paths - current_paths,
    )


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

    def _stored_hashes(self) -> dict[str, str]:
        collection = self.settings.qdrant_collection
        if not self.client.collection_exists(collection):
            return {}

        stored: dict[str, str] = {}
        offset = None
        while True:
            points, offset = self.client.scroll(
                collection_name=collection,
                limit=256,
                offset=offset,
                with_payload=["path", "file_hash"],
                with_vectors=False,
            )
            for point in points:
                payload = point.payload or {}
                path = payload.get("path")
                file_hash = payload.get("file_hash")
                if isinstance(path, str) and isinstance(file_hash, str):
                    stored[path] = file_hash
            if offset is None:
                break
        return stored

    def _delete_paths(self, paths: Iterable[str]) -> None:
        collection = self.settings.qdrant_collection
        for path in paths:
            self.client.delete(
                collection_name=collection,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="path",
                                match=models.MatchValue(value=path),
                            )
                        ]
                    )
                ),
                wait=True,
            )

    def sync(
        self,
        chunks_by_path: dict[str, list[CodeChunk]],
        file_hashes: dict[str, str],
    ) -> SyncResult:
        collection = self.settings.qdrant_collection
        collection_exists = self.client.collection_exists(collection)
        plan = build_index_plan(file_hashes, self._stored_hashes())

        if collection_exists:
            self._delete_paths(plan.changed | plan.deleted)

        changed_chunks = [
            chunk
            for path in sorted(plan.changed)
            for chunk in chunks_by_path.get(path, [])
        ]
        if not changed_chunks:
            return SyncResult(
                chunks=0,
                indexed_files=len(plan.changed),
                unchanged_files=len(plan.unchanged),
                deleted_files=len(plan.deleted),
            )

        vectors = self._embed([item.content for item in changed_chunks])
        if not collection_exists:
            self.client.create_collection(
                collection_name=collection,
                vectors_config=models.VectorParams(
                    size=len(vectors[0]),
                    distance=models.Distance.COSINE,
                ),
            )

        points = []
        for item, vector in zip(changed_chunks, vectors, strict=True):
            file_hash = file_hashes[item.path]
            digest = sha256(
                f"{item.path}:{item.start_line}:{item.end_line}:{item.kind}".encode()
            ).digest()[:16]
            points.append(
                models.PointStruct(
                    id=str(UUID(bytes=digest)),
                    vector=vector,
                    payload={
                        "path": item.path,
                        "file_hash": file_hash,
                        "start_line": item.start_line,
                        "end_line": item.end_line,
                        "content": item.content,
                        "kind": item.kind,
                        "symbol": item.symbol,
                    },
                )
            )
        self.client.upsert(collection_name=collection, points=points, wait=True)
        return SyncResult(
            chunks=len(points),
            indexed_files=len(plan.changed),
            unchanged_files=len(plan.unchanged),
            deleted_files=len(plan.deleted),
        )

    def search(self, query: str, limit: int) -> list[dict]:
        vector = self._embed([query])[0]
        result = self.client.query_points(
            collection_name=self.settings.qdrant_collection,
            query=vector,
            limit=limit,
            with_payload=True,
        )
        return [point.payload or {} for point in result.points]
