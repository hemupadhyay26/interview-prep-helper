import logging
from io import BytesIO
from pathlib import Path

from docling.datamodel.base_models import DocumentStream
from docling.document_converter import DocumentConverter

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

# Building the converter loads Docling's layout/table models - do this once
# per process, not per request.
_converter = DocumentConverter()

# Resume section headings, normalized to a canonical key. Matched against
# the lowercased heading text with substring matching.
_SECTION_KEYWORDS: list[tuple[str, str]] = [
    ("experience", "experience"),
    ("employment", "experience"),
    ("work history", "experience"),
    ("skill", "skills"),
    ("technolog", "skills"),
    ("project", "projects"),
    ("education", "education"),
    ("certification", "education"),
    ("summary", "summary"),
    ("objective", "summary"),
    ("profile", "summary"),
]


def parse_to_markdown(filename: str, content: bytes) -> str:
    """
    Parse a resume file (PDF or DOCX) into markdown text via Docling,
    preserving the document's detected heading structure so it can later
    be split by section rather than by page.
    """
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{extension}'. "
            f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    source = DocumentStream(name=filename, stream=BytesIO(content))

    try:
        result = _converter.convert(source)
    except Exception as exc:
        logger.exception("Docling failed to parse resume: %s", filename)
        raise ValueError(f"Could not parse '{filename}': {exc}") from exc

    return result.document.export_to_markdown()


def _normalize_heading(heading: str) -> str:
    lowered = heading.strip().lower()

    for keyword, key in _SECTION_KEYWORDS:
        if keyword in lowered:
            return key

    return "other"


def split_into_sections(markdown: str) -> list[dict]:
    """
    Split markdown into sections by heading line, e.g.:

        # John Doe
        ## Experience
        ...
        ## Projects
        ...

    Content before the first heading (typically just a name/contact line)
    is dropped. Returns one {"key", "title", "text"} dict per heading,
    where `key` is normalized to experience/skills/projects/education/
    summary/other. Falls back to a single "other" section covering the
    whole document if no headings were detected at all.
    """
    sections: list[dict] = []
    current_title: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        if current_title is None:
            return

        text = "\n".join(current_lines).strip()

        if text:
            sections.append(
                {
                    "key": _normalize_heading(current_title),
                    "title": current_title,
                    "text": text,
                }
            )

    for line in markdown.splitlines():
        stripped = line.strip()

        if stripped.startswith("#"):
            flush()
            current_title = stripped.lstrip("#").strip()
            current_lines = []
        else:
            current_lines.append(line)

    flush()

    if not sections:
        text = markdown.strip()
        if text:
            sections.append({"key": "other", "title": "Resume", "text": text})

    return sections
