# Backend

FastAPI + pydantic-ai interview-prep assistant.

## Structure

```
app/
  main.py           # FastAPI app: middleware, router wiring, startup
  core/              # config, logging, observability setup
  api/routes/        # HTTP endpoints (health, sessions, resume)
  schemas/           # request/response models
  services/          # framework-agnostic helpers (memory, chat streaming,
                      # resume parsing, vector store)
  agents/            # pydantic-ai agents (interview, question, title, resume)
  db/                # SQLAlchemy engine/session + models
alembic/             # migration environment (versions/ holds migration files)
alembic.ini           # alembic config (DB URL is pulled from app settings, not this file)
main.py              # entrypoint: `from app.main import app`, also runnable directly
data/                # sqlite database file + data/chroma/ (vector store)
```

## Run

```bash
uv run alembic upgrade head    # apply any pending migrations
uv run python main.py          # reads HOST/PORT from .env
```

`uv run uvicorn main:app --reload` also works, but `--port`/`--host` flags
on that command take priority over `.env` — use `python main.py` if you
want `HOST`/`PORT` from `.env` to control where it listens.

Requires a `.env` file (see `app/core/config.py` for available settings,
at minimum `OPENAI_API_KEY`).

## Database migrations

Schema is managed with Alembic — `Base.metadata.create_all()` is no longer
run on startup. After changing a model in `app/db/models.py`:

```bash
uv run alembic revision --autogenerate -m "short description"
uv run alembic upgrade head
```

Always review the generated migration in `alembic/versions/` before
committing — autogenerate doesn't catch everything (e.g. column renames
show up as a drop + add).

## Resume upload

The resume is **global** — one per app, not tied to a chat session.
Upload it once; every session's `interview_agent` references it.

`POST /resume` (multipart, field `file`, PDF or DOCX, ≤5MB) parses the
resume with [Docling](https://docling-project.github.io/docling/), splits
it into sections by detected heading (experience/skills/projects/
education), runs it through `resume_agent` for structured extraction, and
embeds section + per-project chunks into a local Chroma store at
`data/chroma/` (via `EMBEDDING_MODEL_NAME` in `.env`, default
`text-embedding-3-small`). `interview_agent` then uses it via a
`search_resume` tool plus a resume summary injected into every turn.
`GET`/`DELETE /resume` fetch/remove it. Re-uploading replaces the
previous one.

Note: `docling` is a heavy dependency (pulls in `torch` + layout/table ML
models) — the first real parse after startup may be slower while those
models load, but a 1-2 page resume converts quickly after that.
