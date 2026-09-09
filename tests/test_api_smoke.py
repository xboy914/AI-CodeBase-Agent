from fastapi.testclient import TestClient

import codebase_agent.api as api_module
from codebase_agent.api import app
from codebase_agent.models import AskResult, Citation, IndexResult


class FakeAgent:
    def index(self, path: str) -> IndexResult:
        return IndexResult(files=2, chunks=3, indexed_files=2)

    def repository_map(self, path: str) -> dict:
        return {
            "total_files": 2,
            "internal_dependencies": 1,
            "external_dependencies": ["react"],
            "cycles": [],
            "hotspots": ["src/shared.ts"],
            "files": [],
        }

    def ask(self, question: str, limit: int) -> AskResult:
        return AskResult(
            answer="Authentication lives in the auth module.",
            citations=[Citation(path="src/auth.ts", start_line=1, end_line=12)],
        )


def test_health_and_core_workflow_contracts(monkeypatch):
    monkeypatch.setattr(api_module, "get_agent", lambda: FakeAgent())
    api = TestClient(app)
    assert api.get("/health").json() == {"status": "ok", "version": "1.0.0"}
    assert api.post("/index", json={"path": "."}).status_code == 200
    assert api.post("/map", json={"path": "."}).json()["internal_dependencies"] == 1
    answer = api.post("/ask", json={"question": "Where is auth?"})
    assert answer.status_code == 200
    assert answer.json()["citations"][0]["path"] == "src/auth.ts"
