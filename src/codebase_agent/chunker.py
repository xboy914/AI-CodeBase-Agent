from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from tree_sitter import Node
from tree_sitter_language_pack import get_parser

SUPPORTED_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".css", ".scss"}
IGNORED_PARTS = {"node_modules", ".git", ".next", "dist", "build", "coverage"}
PARSER_NAMES = {
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
}
SYMBOL_TYPES = {
    "class_declaration",
    "enum_declaration",
    "function_declaration",
    "interface_declaration",
    "lexical_declaration",
    "type_alias_declaration",
}


@dataclass(frozen=True)
class CodeChunk:
    path: str
    start_line: int
    end_line: int
    content: str
    kind: str = "text"
    symbol: str | None = None


def iter_source_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*"):
        if (
            path.is_file()
            and path.suffix.lower() in SUPPORTED_SUFFIXES
            and not any(part in IGNORED_PARTS for part in path.parts)
        ):
            yield path


def _window_chunks(
    lines: list[str],
    relative: str,
    lines_per_chunk: int,
    overlap: int,
    *,
    offset: int = 0,
    kind: str = "text",
    symbol: str | None = None,
) -> Iterator[CodeChunk]:
    step = max(1, lines_per_chunk - overlap)
    for start in range(0, len(lines), step):
        selected = lines[start : start + lines_per_chunk]
        if not selected:
            continue
        yield CodeChunk(
            path=relative,
            start_line=offset + start + 1,
            end_line=offset + start + len(selected),
            content="\n".join(selected),
            kind=kind,
            symbol=symbol,
        )
        if start + lines_per_chunk >= len(lines):
            break


def _unwrap_export(node: Node) -> Node:
    if node.type != "export_statement":
        return node
    return next(
        (child for child in node.named_children if child.type in SYMBOL_TYPES),
        node,
    )


def _node_symbol(node: Node, source: bytes) -> str | None:
    name = node.child_by_field_name("name")
    if name is None and node.type == "lexical_declaration":
        declarator = next(
            (child for child in node.named_children if child.type == "variable_declarator"),
            None,
        )
        name = declarator.child_by_field_name("name") if declarator else None
    return source[name.start_byte : name.end_byte].decode("utf-8") if name else None


def _ast_chunks(
    source: bytes,
    relative: str,
    suffix: str,
    lines_per_chunk: int,
    overlap: int,
) -> list[CodeChunk]:
    parser = get_parser(PARSER_NAMES[suffix])
    tree = parser.parse(source)
    text_lines = source.decode("utf-8", errors="ignore").splitlines()
    chunks: list[CodeChunk] = []

    imports = [node for node in tree.root_node.named_children if node.type == "import_statement"]
    if imports:
        start = imports[0].start_point.row
        end = imports[-1].end_point.row + 1
        chunks.extend(
            _window_chunks(
                text_lines[start:end],
                relative,
                lines_per_chunk,
                overlap,
                offset=start,
                kind="module_context",
            )
        )

    for top_level in tree.root_node.named_children:
        node = _unwrap_export(top_level)
        if node.type not in SYMBOL_TYPES:
            continue
        start = top_level.start_point.row
        end = top_level.end_point.row + 1
        chunks.extend(
            _window_chunks(
                text_lines[start:end],
                relative,
                lines_per_chunk,
                overlap,
                offset=start,
                kind=node.type,
                symbol=_node_symbol(node, source),
            )
        )

    return chunks


def chunk_file(
    path: Path,
    root: Path,
    lines_per_chunk: int = 120,
    overlap: int = 20,
) -> Iterator[CodeChunk]:
    source = path.read_bytes()
    relative = path.relative_to(root).as_posix()
    suffix = path.suffix.lower()

    if suffix in PARSER_NAMES:
        chunks = _ast_chunks(source, relative, suffix, lines_per_chunk, overlap)
        if chunks:
            yield from chunks
            return

    lines = source.decode("utf-8", errors="ignore").splitlines()
    yield from _window_chunks(lines, relative, lines_per_chunk, overlap)
