from fastapi import FastAPI, HTTPException

from .config import get_settings
from .models import AskRequest, AskResult, IndexRequest, IndexResult
from .service import CodebaseAgent

app = FastAPI(
    title="AI Codebase Agent",
    version="0.1.0",
    description="Retrieval-augmented analysis for React and TypeScript repositories.",
)


def get_agent() -> CodebaseAgent:
    return CodebaseAgent(get_settings())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/index", response_model=IndexResult)
def index_codebase(request: IndexRequest) -> IndexResult:
    try:
        return get_agent().index(request.path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/ask", response_model=AskResult)
def ask_codebase(request: AskRequest) -> AskResult:
    return get_agent().ask(request.question, request.limit)
