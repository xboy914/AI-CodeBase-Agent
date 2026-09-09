# AI Codebase Agent

A full-stack retrieval-augmented assistant that indexes React and TypeScript repositories, retrieves relevant code, and answers architecture and implementation questions with file-and-line citations.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-Web-000000?logo=nextdotjs&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-Embeddings%20%2B%20Responses-412991?logo=openai&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20Search-DC244C)
![CI](https://github.com/xboy914/AI-CodeBase-Agent/actions/workflows/ci.yml/badge.svg)

## What it demonstrates

- Repository ingestion with safe root-path enforcement
- Source filtering and overlapping chunks with file/line metadata
- OpenAI embeddings and Qdrant cosine-similarity retrieval
- Grounded answers through the OpenAI Responses API
- Explicit citations and uncertainty rules
- FastAPI, CLI, and a responsive Next.js workspace
- Independent backend and web quality gates in GitHub Actions

## Architecture

```text
React / Next.js ───────┐
CLI ───────────────────┼─> FastAPI ─> scanner ─> chunks ─> embeddings ─> Qdrant
                       │                                      ↑             │
Question ──────────────┘                                      └─ retrieval ─┘
                                                                      │
                                                          answer + citations
```

## Quick start

### Backend

```bash
git clone https://github.com/xboy914/AI-CodeBase-Agent.git
cd AI-CodeBase-Agent
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn codebase_agent.api:app --reload
```

Add your OpenAI API key to `.env` and set `CODEBASE_ROOT` to the parent directory containing repositories you are authorized to analyze.

### Web workspace

```bash
cd web
cp .env.example .env.local
npm install
npm run dev
```

Open `http://localhost:3000`. The interface checks API health, indexes an allowed relative path, submits codebase questions, and renders retrieved citations.

### CLI

```bash
codebase-agent index .
codebase-agent ask "Where is authentication state managed?"
```

Interactive API documentation is available at `http://localhost:8000/docs`.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | API status and version |
| POST | `/index` | Scan, chunk, embed, and store an allowed repository |
| POST | `/ask` | Retrieve relevant code and answer with citations |

## Safety and boundaries

- Indexing is restricted to `CODEBASE_ROOT`.
- Common generated and dependency directories are ignored.
- Retrieved code is sent to the configured model provider; do not index secrets or proprietary code without authorization.
- The agent is read-only and never edits the target repository.

## Roadmap

- AST-aware chunking with Tree-sitter
- Incremental indexing based on Git diffs
- Hybrid lexical and vector retrieval
- Repository map and dependency graph
- Pluggable model and embedding providers
- Streaming answers and saved analysis sessions

## License

MIT
