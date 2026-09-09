# AI Codebase Agent

A full-stack retrieval-augmented assistant that indexes React and TypeScript repositories, retrieves relevant code, and answers architecture and implementation questions with file-and-line citations.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-Web-000000?logo=nextdotjs&logoColor=white)
![Tree-sitter](https://img.shields.io/badge/Tree--sitter-AST-6A4C93)
![Providers](https://img.shields.io/badge/AI-OpenAI%20%7C%20Ollama-412991)
![Qdrant](https://img.shields.io/badge/Qdrant-Hybrid%20Retrieval-DC244C)
![CI](https://github.com/xboy914/AI-CodeBase-Agent/actions/workflows/ci.yml/badge.svg)

## What it demonstrates

- AST-aware TypeScript, TSX, JavaScript, and JSX chunking with Tree-sitter
- Content-hash incremental indexing that skips unchanged files
- Vector replacement for modified files and cleanup for deleted files
- Hybrid semantic and lexical retrieval with Reciprocal Rank Fusion
- Exact matching for file paths, symbols, declaration kinds, and code tokens
- Pluggable OpenAI-compatible providers for hosted OpenAI, local Ollama, and custom endpoints
- Repository maps with imports, packages, dependency cycles, and hotspots
- Grounded answers with explicit citations and uncertainty rules
- FastAPI, CLI, and a responsive Next.js workspace
- Docker Compose deployment and API workflow smoke tests\n- Independent backend and web quality gates in GitHub Actions

## Retrieval pipeline

```text
Repository -> AST chunks -> incremental embeddings -> Qdrant
Question ----+-> semantic candidates -----------+
             +-> lexical path/symbol/code scan --+-> RRF -> grounded answer
```

Each stored chunk carries its source path, file hash, symbol, declaration kind, and line range. Re-indexing skips unchanged files, replaces modified vectors, and removes deleted sources. At query time, Reciprocal Rank Fusion combines semantic ranking with deterministic lexical ranking, so conceptual questions and exact identifiers both retrieve useful context.

The lexical pass scans stored payloads and is intentionally simple for a portfolio-sized repository. A production deployment can replace it with a Qdrant sparse index without changing the fusion boundary.

## One-command demo

```bash
cp .env.example .env
# Add OPENAI_API_KEY, or configure Ollama as documented below.
docker compose up --build
```

Open the workspace at `http://localhost:3000`, API docs at `http://localhost:8000/docs`, and Qdrant at `http://localhost:6333/dashboard`. The repository is mounted read-only, so use `AI-CodeBase-Agent` as the demo index path.

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

Set `CODEBASE_ROOT` to the parent directory containing repositories you are authorized to analyze. The default provider is OpenAI.

### Run fully locally with Ollama

```bash
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text
```

Then configure `.env`:

```env
AI_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
CHAT_MODEL=qwen2.5-coder:7b
```

Ollama uses `http://localhost:11434/v1` by default. Set `PROVIDER_BASE_URL` and `PROVIDER_API_KEY` to connect to another OpenAI-compatible service such as vLLM.

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
codebase-agent map .
codebase-agent ask "Where is authentication state managed?"
```

The index command reports total files, embedded chunks, indexed files, unchanged files, and deleted files.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | API status and version |
| POST | `/index` | Incrementally parse, embed, replace, and clean repository vectors |
| POST | `/map` | Build dependency graph, cycle report, and hotspot list |
| POST | `/ask` | Hybrid retrieval and grounded answer with citations |

Interactive API documentation is available at `http://localhost:8000/docs`.

## Safety and boundaries

- Indexing is restricted to `CODEBASE_ROOT`.
- Common generated and dependency directories are ignored.
- Retrieved code is sent only to the configured provider. With Ollama, generation and embeddings remain on the local machine.
- Do not index secrets or proprietary code without authorization.
- The agent is read-only and never edits the target repository.

## Production roadmap

- Batch-limited embeddings and native sparse vectors for very large repositories
- Streaming answers, authentication, and saved analysis sessions

## License

MIT
