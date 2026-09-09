from pathlib import Path

from codebase_agent.chunker import chunk_file, iter_source_files


def test_ignores_generated_directories(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.tsx").write_text("export const App = () => null;")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "ignored.ts").write_text("ignore me")

    paths = [path.relative_to(tmp_path).as_posix() for path in iter_source_files(tmp_path)]

    assert paths == ["src/app.tsx"]


def test_chunks_with_line_metadata(tmp_path: Path):
    path = tmp_path / "example.ts"
    path.write_text("\n".join(f"line {number}" for number in range(1, 11)))

    chunks = list(chunk_file(path, tmp_path, lines_per_chunk=5, overlap=1))

    assert [(chunk.start_line, chunk.end_line) for chunk in chunks] == [(1, 5), (5, 9), (9, 10)]
    assert chunks[0].path == "example.ts"
