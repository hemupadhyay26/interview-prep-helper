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

`POST /resume` (multipart, field `file`, **PDF only**, ≤5MB) loads the
resume with LangChain's
[`PyPDFLoader`](https://python.langchain.com/docs/integrations/document_loaders/pypdfloader/),
runs the extracted text through `resume_agent` into a full structured
`ResumeProfile` (`app/schemas/resume.py`) — name, headline, contact,
summary, skills, per-role experience with bullet highlights, projects,
education, certifications, awards, languages — then splits the pages with
`RecursiveCharacterTextSplitter` and embeds the chunks into a local Chroma
store at `data/chroma/` via `langchain-chroma` + `OpenAIEmbeddings`
(`EMBEDDING_MODEL_NAME` in `.env`, default `text-embedding-3-small`).

Link handling: `resume_parser.extract_hyperlinks` reads the PDF's `/Annots`
link targets so a link shown as "linkedin.com" is stored as the real
`linkedin.com/in/<handle>` URL; `_merge_links` reconciles those with the
model's text guesses and forces an `https://` scheme.

`interview_agent` gets the whole snapshot (name, links, experience,
education, certs) injected every turn and can call the `search_resume`
tool for the full bullet-level detail. `GET`/`DELETE /resume` fetch/remove
it. Re-uploading replaces the previous one. `GET` upgrades older
flat-schema rows on the fly, but re-upload is needed to fill the new
fields.

Note: DOCX is no longer supported — `PyPDFLoader` is PDF-only. Scanned
(image-only) PDFs also won't work without OCR; the upload 422s with a
"could not extract any text" message in that case.
