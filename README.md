# AI Codebase Agent

A retrieval-augmented assistant that indexes React and TypeScript repositories, retrieves the most relevant code, and answers architecture and implementation questions with file-and-line citations.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-Embeddings%20%2B%20Responses-412991?logo=openai&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20Search-DC244C)
![CI](https://github.com/xboy914/AI-CodeBase-Agent/actions/workflows/ci.yml/badge.svg)

## What it demonstrates

- Repository ingestion with safe root-path enforcement
- Source filtering for React, TypeScript, JavaScript, styles, Markdown, and JSON
- Overlapping code chunks with file and line metadata
- OpenAI embeddings and Qdrant cosine-similarity retrieval
- Grounded answers through the OpenAI Responses API
- Explicit source citations and uncertainty rules
- FastAPI and CLI interfaces
- Automated linting and tests with GitHub Actions

## Architecture

```text
Repository -> file scanner -> code chunks -> embeddings -> Qdrant
                                                        |
Question -> embedding -> semantic retrieval ------------+
                                                        |
                                      grounded response + citations
```

## Quick start

```bash
git clone https://github.com/xboy914/AI-CodeBase-Agent.git
cd AI-CodeBase-Agent
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Add your OpenAI API key to `.env`, then point `CODEBASE_ROOT` at the parent directory that contains the repository you want to analyze.

### CLI

```bash
codebase-agent index .
codebase-agent ask "Where is authentication state managed?"
```

### API

```bash
uvicorn codebase_agent.api:app --reload
```

```bash
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{"path":"."}'

curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Explain the component and data-flow architecture.","limit":8}'
```

Interactive API documentation is available at `http://localhost:8000/docs`.

## Safety and boundaries

- Indexing is restricted to `CODEBASE_ROOT`.
- Common generated and dependency directories are ignored.
- Retrieved code is sent to the configured model provider; do not index secrets or proprietary code without authorization.
- The agent is read-only: it analyzes code but does not edit the target repository.

## Roadmap

- AST-aware chunking with Tree-sitter
- Incremental indexing based on Git diffs
- Hybrid lexical and vector retrieval
- Repository map and dependency graph
- Pluggable model and embedding providers
- Web interface for browsing answers and citations

## License

MIT
