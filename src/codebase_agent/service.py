from pathlib import Path

from openai import OpenAI

from .chunker import chunk_file, iter_source_files
from .config import Settings
from .models import AskResult, Citation, IndexResult
from .store import CodeStore

SYSTEM_PROMPT = """You are a senior React and TypeScript codebase analyst.
Answer only from the supplied repository context. Be precise, call out uncertainty,
and cite source ranges as [path:start-end]. Never invent files, symbols, or behavior.
When suggesting a change, separate observed behavior from your recommendation."""


class CodebaseAgent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.store = CodeStore(settings)
        self.openai = OpenAI(api_key=settings.openai_api_key)

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
        chunks = [chunk for file in files for chunk in chunk_file(file, target)]
        return IndexResult(files=len(files), chunks=self.store.replace(chunks))

    def ask(self, question: str, limit: int = 8) -> AskResult:
        context = self.store.search(question, limit)
        if not context:
            return AskResult(answer="No indexed context was found.", citations=[])

        blocks = [
            f"[{item['path']}:{item['start_line']}-{item['end_line']}]\n{item['content']}"
            for item in context
        ]
        response = self.openai.responses.create(
            model=self.settings.chat_model,
            instructions=SYSTEM_PROMPT,
            input=f"Question:\n{question}\n\nRepository context:\n" + "\n\n".join(blocks),
        )
        citations = [
            Citation(
                path=str(item["path"]),
                start_line=int(item["start_line"]),
                end_line=int(item["end_line"]),
            )
            for item in context
        ]
        return AskResult(answer=response.output_text, citations=citations)
