# AI Codebase Agent

A full-stack retrieval-augmented assistant that indexes React and TypeScript repositories, retrieves relevant code, and answers architecture and implementation questions with file-and-line citations.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-Web-000000?logo=nextdotjs&logoColor=white)
![Tree-sitter](https://img.shields.io/badge/Tree--sitter-AST-6A4C93)
![OpenAI](https://img.shields.io/badge/OpenAI-Embeddings%20%2B%20Responses-412991?logo=openai&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-Hybrid%20Retrieval-DC244C)
![CI](https://github.com/xboy914/AI-CodeBase-Agent/actions/workflows/ci.yml/badge.svg)

## What it demonstrates

- AST-aware TypeScript, TSX, JavaScript, and JSX chunking with Tree-sitter
- Content-hash incremental indexing that skips unchanged files
- Vector replacement for modified files and cleanup for deleted files
- Hybrid semantic and lexical retrieval with Reciprocal Rank Fusion
- Exact matching for file paths, symbols, declaration kinds, and code tokens
- Grounded answers with explicit citations and uncertainty rules
- FastAPI, CLI, and a responsive Next.js workspace
- Independent backend and web quality gates in GitHub Actions

## Retrieval pipeline

```text
Repository -> AST chunks -> incremental embeddings -> Qdrant
Question ----+-> semantic candidates -----------+
             +-> lexical path/symbol/code scan --+-> RRF -> grounded answer
```

Each stored chunk carries its source path, file hash, symbol, declaration kind, and line range. Re-indexing skips unchanged files, replaces modified vectors, and removes deleted sources. At query time, Reciprocal Rank Fusion combines semantic ranking with deterministic lexical ranking, so conceptual questions and exact identifiers both retrieve useful context.

The lexical pass scans stored payloads and is intentionally simple for a portfolio-sized repository. A production deployment can replace it with a Qdrant sparse index without changing the fusion boundary.

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

Open `http://localhost:3000` to index a permitted repository, ask a codebase question, and inspect retrieved citations.

### CLI

```bash
codebase-agent index .
codebase-agent ask "Where is authentication state managed?"
```

The index command reports total files, embedded chunks, indexed files, unchanged files, and deleted files.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | API status and version |
| POST | `/index` | Incrementally parse, embed, replace, and clean repository vectors |
| POST | `/ask` | Hybrid retrieval and grounded answer with citations |

Interactive API documentation is available at `http://localhost:8000/docs`.

## Safety and boundaries

- Indexing is restricted to `CODEBASE_ROOT`.
- Common generated and dependency directories are ignored.
- Retrieved code is sent to the configured model provider; do not index secrets or proprietary code without authorization.
- The agent is read-only and never edits the target repository.

## Roadmap

- Batch-limited embeddings for very large repositories
- Native sparse-vector lexical retrieval for large collections
- Repository map and dependency graph
- Pluggable local and hosted model providers
- Streaming answers and saved analysis sessions

## License

MIT
