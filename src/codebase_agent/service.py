from hashlib import sha256
from pathlib import Path

from .chunker import chunk_file, iter_source_files
from .config import Settings
from .models import AskResult, Citation, IndexResult
from .providers import AIProvider, build_provider
from .repository_map import analyze_repository
from .store import CodeStore

SYSTEM_PROMPT = """You are a senior React and TypeScript codebase analyst.
Answer only from the supplied repository context. Be precise, call out uncertainty,
and cite source ranges as [path:start-end]. Never invent files, symbols, or behavior.
When suggesting a change, separate observed behavior from your recommendation."""


class CodebaseAgent:
    def __init__(self, settings: Settings, provider: AIProvider | None = None):
        self.settings = settings
        self.provider = provider or build_provider(settings)
        self.store = CodeStore(settings, self.provider)

    def _resolve_path(self, relative_path: str) -> Path:
        base = self.settings.codebase_root.resolve()
        target = (base / relative_path).resolve()
        if target != base and base not in target.parents:
            raise ValueError("Path must stay inside CODEBASE_ROOT")
        if not target.is_dir():
            raise ValueError("Index path must be an existing directory")
        return target

    def index(self, relative_path: str = ".") -> IndexResult:
        target = self._resolve_path(relative_path)
        files = list(iter_source_files(target))
        chunks_by_path = {
            path.relative_to(target).as_posix(): list(chunk_file(path, target))
            for path in files
        }
        file_hashes = {
            path.relative_to(target).as_posix(): sha256(path.read_bytes()).hexdigest()
            for path in files
        }
        result = self.store.sync(chunks_by_path, file_hashes)
        return IndexResult(
            files=len(files),
            chunks=result.chunks,
            indexed_files=result.indexed_files,
            unchanged_files=result.unchanged_files,
            deleted_files=result.deleted_files,
        )

    def repository_map(self, relative_path: str = ".") -> dict:
        return analyze_repository(self._resolve_path(relative_path))

    def ask(self, question: str, limit: int = 8) -> AskResult:
        context = self.store.search(question, limit)
        if not context:
            return AskResult(answer="No indexed context was found.", citations=[])

        blocks = [
            f"[{item['path']}:{item['start_line']}-{item['end_line']}]\n{item['content']}"
            for item in context
        ]
        answer = self.provider.answer(
            SYSTEM_PROMPT,
            f"Question:\n{question}\n\nRepository context:\n" + "\n\n".join(blocks),
        )
        citations = [
            Citation(
                path=str(item["path"]),
                start_line=int(item["start_line"]),
                end_line=int(item["end_line"]),
            )
            for item in context
        ]
        return AskResult(answer=answer, citations=citations)
