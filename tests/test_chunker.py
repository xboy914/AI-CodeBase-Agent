from pathlib import Path

from codebase_agent.chunker import chunk_file, iter_source_files


def test_ignores_generated_directories(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.tsx").write_text("export const App = () => null;")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "ignored.ts").write_text("ignore me")

    paths = [path.relative_to(tmp_path).as_posix() for path in iter_source_files(tmp_path)]

    assert paths == ["src/app.tsx"]


def test_fallback_chunks_with_line_metadata(tmp_path: Path):
    path = tmp_path / "notes.md"
    path.write_text("\n".join(f"line {number}" for number in range(1, 11)))

    chunks = list(chunk_file(path, tmp_path, lines_per_chunk=5, overlap=1))

    assert [(chunk.start_line, chunk.end_line) for chunk in chunks] == [(1, 5), (5, 9), (9, 10)]
    assert chunks[0].path == "notes.md"
    assert chunks[0].kind == "text"


def test_typescript_chunks_preserve_symbols(tmp_path: Path):
    path = tmp_path / "auth.ts"
    path.write_text(
        'import { api } from "./api";\n\n'
        "export interface Session { token: string }\n\n"
        "export async function login(phone: string) {\n"
        "  return api.post('/login', { phone });\n"
        "}\n"
    )

    chunks = list(chunk_file(path, tmp_path))

    assert [(chunk.kind, chunk.symbol) for chunk in chunks] == [
        ("module_context", None),
        ("interface_declaration", "Session"),
        ("function_declaration", "login"),
    ]
    assert chunks[2].start_line == 5
    assert chunks[2].end_line == 7


def test_tsx_component_is_a_named_lexical_declaration(tmp_path: Path):
    path = tmp_path / "Card.tsx"
    path.write_text(
        "export const Card = ({ title }: { title: string }) => (\n"
        "  <article><h2>{title}</h2></article>\n"
        ");\n"
    )

    chunks = list(chunk_file(path, tmp_path))

    assert len(chunks) == 1
    assert chunks[0].kind == "lexical_declaration"
    assert chunks[0].symbol == "Card"
