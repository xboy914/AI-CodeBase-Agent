from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .models import AskRequest, AskResult, IndexRequest, IndexResult
from .service import CodebaseAgent

settings = get_settings()
app = FastAPI(
    title="AI Codebase Agent",
    version="1.0.0",
    description="Retrieval-augmented analysis for React and TypeScript repositories.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def get_agent() -> CodebaseAgent:
    return CodebaseAgent(settings)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": app.version}


@app.post("/index", response_model=IndexResult)
def index_codebase(request: IndexRequest) -> IndexResult:
    try:
        return get_agent().index(request.path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/map")
def map_codebase(request: IndexRequest) -> dict:
    try:
        return get_agent().repository_map(request.path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/ask", response_model=AskResult)
def ask_codebase(request: AskRequest) -> AskResult:
    return get_agent().ask(request.question, request.limit)
