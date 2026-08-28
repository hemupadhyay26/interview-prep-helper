import asyncio
import logging

import chromadb
from openai import AsyncOpenAI

from app.agents.resume_agent import ResumeProfile
from app.core.config import settings

logger = logging.getLogger(__name__)

_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
_collection = _client.get_or_create_collection(name="resumes")

# The resume is global (one per app), so every chunk is tagged with this
# fixed scope - used to clear the previous resume's chunks on re-upload.
_RESUME_SCOPE = "global"

_openai = AsyncOpenAI(api_key=settings.openai_api_key)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    response = await _openai.embeddings.create(
        model=settings.embedding_model_name,
        input=texts,
    )

    return [item.embedding for item in response.data]


def build_chunks(
    sections: list[dict],
    profile: ResumeProfile,
) -> list[tuple[str, dict]]:
    """
    Build (text, metadata) chunks for embedding: one per detected resume
    section (experience/skills/projects/education/...), plus one per
    individually-extracted project - so `search_resume` can return a
    single project's detail rather than the whole projects block.
    """
    chunks: list[tuple[str, dict]] = []

    for section in sections:
        text = f"{section['title']}\n\n{section['text']}"
        chunks.append((text, {"section": section["key"]}))

    for project in profile.projects:
        text = (
            f"Project: {project.name}\n"
            f"{project.description}\n"
            f"Technologies: {', '.join(project.technologies)}"
        )
        chunks.append(
            (text, {"section": "project", "project_name": project.name})
        )

    return chunks


async def upsert_resume_chunks(chunks: list[tuple[str, dict]]) -> None:
    """Replace all stored resume chunks with `chunks`."""

    await delete_resume_chunks()

    if not chunks:
        return

    texts = [text for text, _ in chunks]
    metadatas = [{"scope": _RESUME_SCOPE, **meta} for _, meta in chunks]
    ids = [f"{_RESUME_SCOPE}:{i}" for i in range(len(chunks))]

    embeddings = await embed_texts(texts)

    await asyncio.to_thread(
        _collection.add,
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    logger.info("Stored %d resume chunks", len(chunks))


async def search_resume_chunks(query: str, k: int = 4) -> list[str]:
    """Return up to `k` resume chunk texts most relevant to `query`.
    Empty list if no resume has been uploaded."""

    [query_embedding] = await embed_texts([query])

    result = await asyncio.to_thread(
        _collection.query,
        query_embeddings=[query_embedding],
        n_results=k,
        where={"scope": _RESUME_SCOPE},
    )

    documents = result.get("documents") or [[]]
    return documents[0]


async def delete_resume_chunks() -> None:
    await asyncio.to_thread(
        _collection.delete,
        where={"scope": _RESUME_SCOPE},
    )
