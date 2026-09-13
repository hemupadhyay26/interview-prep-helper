import logging
import os
import tempfile
from io import BytesIO
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf"}

# One splitter per process. Resume-sized chunks: big enough to keep a
# bullet/role together, small enough that retrieval returns a focused
# passage rather than a whole page.
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def load_pdf_documents(filename: str, content: bytes) -> list[Document]:
    """
    Load a PDF's pages into LangChain `Document`s via `PyPDFLoader`
    (one document per page). `PyPDFLoader` reads from a path, so the
    upload bytes are staged in a temp file for the duration of the load.
    """
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{extension}'. "
            f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        documents = PyPDFLoader(tmp_path).load()
    except Exception as exc:
        logger.exception("PyPDFLoader failed to parse resume: %s", filename)
        raise ValueError(f"Could not parse '{filename}': {exc}") from exc
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    # Replace the temp-file path with the real upload name so it shows up
    # sensibly in chunk metadata / any future citations.
    for document in documents:
        document.metadata["source"] = filename

    text = extract_text(documents)
    if not text:
        raise ValueError(
            f"Could not extract any text from '{filename}'. "
            "If this is a scanned PDF, it needs OCR first."
        )

    return documents


def extract_text(documents: list[Document]) -> str:
    """Concatenate page text, for feeding the whole resume to the LLM."""
    return "\n\n".join(d.page_content for d in documents).strip()


def extract_hyperlinks(content: bytes) -> list[str]:
    """
    Pull real hyperlink targets from a PDF's link annotations.

    Text extraction only yields the visible label - a resume that shows
    "linkedin.com" but hyperlinks it to the full profile URL loses the
    target. The `/Annots` -> `/Link` -> `/URI` entries keep it. Returns
    an order-preserving, de-duplicated list; empty if the PDF has no live
    links (e.g. a print-to-PDF export).
    """
    try:
        reader = PdfReader(BytesIO(content))
    except Exception:
        logger.warning("Could not read PDF for hyperlinks", exc_info=True)
        return []

    urls: list[str] = []
    seen: set[str] = set()

    def _resolve(value):
        return value.get_object() if hasattr(value, "get_object") else value

    for page in reader.pages:
        try:
            annotations = _resolve(page.get("/Annots")) or []
        except Exception:
            continue

        for ref in annotations:
            try:
                annot = _resolve(ref)
                if annot.get("/Subtype") != "/Link":
                    continue

                action = _resolve(annot.get("/A"))
                uri = _resolve(action.get("/URI")) if action else None
            except Exception:
                continue

            if not uri:
                continue

            uri = str(uri).strip()
            key = uri.lower()
            if uri and key not in seen:
                seen.add(key)
                urls.append(uri)

    return urls


def split_documents(documents: list[Document]) -> list[Document]:
    """Split loaded pages into embedding-sized chunks."""
    return _splitter.split_documents(documents)
