from pydantic import BaseModel, Field


class IndexRequest(BaseModel):
    path: str = Field(default=".", description="Path relative to CODEBASE_ROOT")


class IndexResult(BaseModel):
    files: int
    chunks: int
    indexed_files: int = 0
    unchanged_files: int = 0
    deleted_files: int = 0


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2_000)
    limit: int = Field(default=8, ge=1, le=20)


class Citation(BaseModel):
    path: str
    start_line: int
    end_line: int


class AskResult(BaseModel):
    answer: str
    citations: list[Citation]
