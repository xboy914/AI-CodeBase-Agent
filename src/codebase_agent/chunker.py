from dataclasses import dataclass
from pathlib import Path

SUPPORTED_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".css", ".scss"}
IGNORED_PARTS = {"node_modules", ".git", ".next", "dist", "build", "coverage"}


@dataclass(frozen=True)
class CodeChunk:
    path: str
    start_line: int
    end_line: int
    content: str


def iter_source_files(root: Path):
    for path in root.rglob("*"):
        if (
            path.is_file()
            and path.suffix.lower() in SUPPORTED_SUFFIXES
            and not any(part in IGNORED_PARTS for part in path.parts)
        ):
            yield path


def chunk_file(path: Path, root: Path, lines_per_chunk: int = 120, overlap: int = 20):
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    step = max(1, lines_per_chunk - overlap)
    relative = path.relative_to(root).as_posix()

    for start in range(0, len(lines), step):
        selected = lines[start : start + lines_per_chunk]
        if not selected:
            continue
        yield CodeChunk(
            path=relative,
            start_line=start + 1,
            end_line=start + len(selected),
            content="\n".join(selected),
        )
        if start + lines_per_chunk >= len(lines):
            break
