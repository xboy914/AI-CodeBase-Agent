from pathlib import Path

from codebase_agent.repository_map import analyze_repository, extract_imports


def put(root: Path, name: str, content: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_extracts_static_and_dynamic_imports():
    source = 'import React from "react"; export {x} from "./x"; import("./lazy")'
    assert extract_imports(source) == {"react", "./x", "./lazy"}


def test_builds_dependency_map_hotspots_and_cycles(tmp_path):
    put(tmp_path, "src/a.ts", 'import React from "react"; import "./feature";')
    put(tmp_path, "src/feature/index.ts", 'import "../a";')
    result = analyze_repository(tmp_path)
    assert result["total_files"] == 2
    assert result["internal_dependencies"] == 2
    assert result["external_dependencies"] == ["react"]
    assert result["cycles"] == [["src/a.ts", "src/feature/index.ts"]]
    assert result["hotspots"] == ["src/a.ts", "src/feature/index.ts"]
