import asyncio
import logging

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.core.config import settings

logger = logging.getLogger(__name__)

# The resume is global (one per app), so every chunk is tagged with this
# fixed scope - used to clear the previous resume's chunks on re-upload.
_RESUME_SCOPE = "global"

_embeddings = OpenAIEmbeddings(
    model=settings.embedding_model_name,
    api_key=settings.openai_api_key,
)

# Same on-disk location and collection name as before; LangChain's Chroma
# wrapper opens it with a chromadb.PersistentClient under the hood.
_store = Chroma(
    collection_name="resumes",
    embedding_function=_embeddings,
    persist_directory=settings.chroma_persist_dir,
)


def _clean_metadata(metadata: dict) -> dict:
    """Chroma only accepts str/int/float/bool metadata values - PyPDFLoader
    can emit None / other types for PDF header fields, so drop those."""
    return {
        key: value
        for key, value in metadata.items()
        if isinstance(value, (str, int, float, bool))
    }


async def upsert_resume_chunks(chunks: list[Document]) -> None:
    """Replace all stored resume chunks with `chunks`."""

    await delete_resume_chunks()

    if not chunks:
        return

    for chunk in chunks:
        chunk.metadata = {
            **_clean_metadata(chunk.metadata),
            "scope": _RESUME_SCOPE,
        }

    ids = [f"{_RESUME_SCOPE}:{i}" for i in range(len(chunks))]

    await asyncio.to_thread(_store.add_documents, chunks, ids=ids)

    logger.info("Stored %d resume chunks", len(chunks))


async def search_resume_chunks(query: str, k: int = 4) -> list[str]:
    """Return up to `k` resume chunk texts most relevant to `query`.
    Empty list if no resume has been uploaded."""

    results = await asyncio.to_thread(
        _store.similarity_search,
        query,
        k=k,
        filter={"scope": _RESUME_SCOPE},
    )

    return [doc.page_content for doc in results]


async def delete_resume_chunks() -> None:
    """Remove every chunk from the `resumes` collection.

    The resume is global (one per app), so the collection only ever holds
    the current resume - clearing it wholesale (rather than filtering on
    `scope`) guarantees no stale or older-format chunks survive a delete
    or a re-upload and leak into a later `search_resume`.
    """

    def _clear() -> None:
        existing = _store._collection.get(include=[])
        ids = existing.get("ids") or []
        if ids:
            _store._collection.delete(ids=ids)

    await asyncio.to_thread(_clear)
