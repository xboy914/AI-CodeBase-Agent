from fastapi.testclient import TestClient

from codebase_agent.api import app, get_agent
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


def client() -> TestClient:
    app.dependency_overrides[get_agent] = FakeAgent
    return TestClient(app)


def test_health_and_core_workflow_contracts():
    api = client()
    assert api.get("/health").json() == {"status": "ok", "version": "1.0.0"}
    assert api.post("/index", json={"path": "."}).status_code == 200
    assert api.post("/map", json={"path": "."}).json()["internal_dependencies"] == 1
    answer = api.post("/ask", json={"question": "Where is auth?"})
    assert answer.status_code == 200
    assert answer.json()["citations"][0]["path"] == "src/auth.ts"
