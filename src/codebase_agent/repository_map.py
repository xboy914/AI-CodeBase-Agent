import posixpath
import re
from pathlib import Path
from typing import Any

from .chunker import iter_source_files

PATTERNS = (
    re.compile(r"""(?:import|export)\s+(?:[\s\S]*?\s+from\s+)?["']([^"']+)["']"""),
    re.compile(r"""(?:require|import)\(\s*["']([^"']+)["']\s*\)"""),
)
SUFFIXES = (".ts", ".tsx", ".js", ".jsx", ".json")


def extract_imports(source: str) -> set[str]:
    return {match.group(1) for pattern in PATTERNS for match in pattern.finditer(source)}


def _resolve(source: str, specifier: str, known: set[str]) -> str | None:
    base = posixpath.normpath((Path(source).parent / specifier).as_posix())
    candidates = [base, *(base + suffix for suffix in SUFFIXES)]
    candidates += [f"{base}/index{suffix}" for suffix in SUFFIXES]
    return next((item for item in candidates if item in known), None)


def _cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    found: set[tuple[str, ...]] = set()
    stack: list[str] = []
    active: set[str] = set()
    done: set[str] = set()

    def visit(node: str) -> None:
        if node in active:
            cycle = stack[stack.index(node):]
            pivot = min(range(len(cycle)), key=lambda index: cycle[index])
            found.add(tuple(cycle[pivot:] + cycle[:pivot]))
            return
        if node in done:
            return
        active.add(node)
        stack.append(node)
        for dependency in graph.get(node, []):
            visit(dependency)
        stack.pop()
        active.remove(node)
        done.add(node)

    for node in sorted(graph):
        visit(node)
    return [list(cycle) for cycle in sorted(found)]


def analyze_repository(root: Path) -> dict[str, Any]:
    paths = list(iter_source_files(root))
    known = {path.relative_to(root).as_posix() for path in paths}
    graph: dict[str, list[str]] = {}
    external: set[str] = set()
    for path in paths:
        relative = path.relative_to(root).as_posix()
        internal: set[str] = set()
        source = path.read_text(encoding="utf-8", errors="replace")
        for specifier in extract_imports(source):
            if specifier.startswith("."):
                resolved = _resolve(relative, specifier, known)
                if resolved:
                    internal.add(resolved)
            else:
                parts = specifier.split("/")
                external.add("/".join(parts[:2]) if specifier.startswith("@") else parts[0])
        graph[relative] = sorted(internal)

    incoming = {path: 0 for path in known}
    for dependencies in graph.values():
        for dependency in dependencies:
            incoming[dependency] += 1
    files = [
        {"path": path, "imports": graph[path], "imported_by": incoming[path]}
        for path in sorted(known)
    ]
    hotspots = [
        path
        for path, count in sorted(
            incoming.items(), key=lambda item: (-item[1], item[0])
        )
        if count > 0
    ][:10]
    return {
        "total_files": len(files),
        "internal_dependencies": sum(map(len, graph.values())),
        "external_dependencies": sorted(external),
        "cycles": _cycles(graph),
        "hotspots": hotspots,
        "files": files,
    }
