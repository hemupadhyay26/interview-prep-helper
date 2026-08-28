# prep-helper-agent

An AI interview-preparation assistant. Chat with an agent that pulls in a
target job posting from a URL, reads your uploaded resume, and generates
grounded practice questions for that specific role.

The repo is a two-part monorepo:

| Path        | Stack                                                        |
| ----------- | ----------------------------------------------------------- |
| `backend/`  | FastAPI + [pydantic-ai](https://ai.pydantic.dev), SQLite, Alembic, ChromaDB |
| `frontend/` | React 19 + Vite + TypeScript + Tailwind CSS v4             |

## Features

- **Conversational agent** — a main `interview_agent` runs the chat and
  delegates to specialized agents/tools.
- **Job posting ingestion** — paste a URL in chat; the agent scrapes the
  page ([crawl4ai](https://github.com/unclecode/crawl4ai)) and extracts a
  structured `JobDetails` record (`job_agent`).
- **Resume grounding** — upload a PDF/DOCX (≤5 MB). It is parsed with
  [Docling](https://docling-project.github.io/docling/), split by section,
  structured by `resume_agent`, and embedded into a local Chroma store.
  The interview agent then asks about your actual projects and roles via a
  `search_resume` tool.
- **Question generation** — `question_generator` produces role-specific
  technical / behavioral / situational questions.
- **Auto chat titles** — `title_agent` names a conversation once it has
  enough context.
- **Streaming** — chat responses stream to the client as Server-Sent
  Events.
- **Observability** — optional [Langfuse](https://langfuse.com) tracing of
  every agent run.

## Architecture

```
frontend (Vite dev server, :3000)
   │  REST + SSE
   ▼
backend (FastAPI, :8000)
   ├─ api/routes/       health, sessions, resume, job
   ├─ agents/           interview, job, question_generator, title, resume
   ├─ services/         chat_stream, job_scraper, resume_parser,
   │                    vector_store, memory
   └─ db/               SQLAlchemy async + SQLite   ← Alembic migrations
                        data/chroma/                ← embeddings
```

## Prerequisites

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Node.js 20+ and npm
- An OpenAI API key

## Backend setup

```bash
cd backend

# 1. Create .env (see app/core/config.py for all settings)
cat > .env <<'EOF'
OPENAI_API_KEY=sk-...
LLM_MODEL_NAME=gpt-5.2
EMBEDDING_MODEL_NAME=text-embedding-3-small
HOST=0.0.0.0
PORT=8000
LANGFUSE_ENABLED=false
EOF

# 2. Install deps + apply migrations
uv sync
uv run alembic upgrade head

# 3. Run (reads HOST/PORT from .env)
uv run python main.py
```

`uv run uvicorn main:app --reload` also works, but `--host`/`--port` flags
there override `.env`. See [backend/README.md](backend/README.md) for
migrations, resume-upload internals, and the `docling` dependency note.

The API is then at `http://localhost:8000` (`GET /health` to check).

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The dev server runs on **port 3000** (strict) — the backend's CORS config
only allows `http://localhost:3000`. It talks to the backend at
`http://localhost:8000` by default; override with `VITE_API_URL` in a
`frontend/.env` file.

Other scripts: `npm run build`, `npm run typecheck`, `npm run lint`,
`npm run preview`.

## How it works

- Each conversation is a **session**. Create one, then chat with the
  agent; replies stream back token by token.
- Drop a job posting URL into the chat and the agent fetches and
  structures the role for you.
- Upload a resume to a session and questions become grounded in your
  actual experience.
- One resume and one job posting per session — re-adding either replaces
  the previous one.

Interactive API docs are available at `http://localhost:8000/docs` while
the backend is running.

## Data & storage

- `backend/data/prephelper.db` — SQLite (sessions, resumes, job postings)
- `backend/data/chroma/` — Chroma vector store (resume embeddings)

Both live under `backend/data/` and are safe to delete to reset state
(re-run `alembic upgrade head` afterwards).
