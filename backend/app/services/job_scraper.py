import logging

logger = logging.getLogger(__name__)

# Job-posting pages are wrapped in a lot of chrome (nav bars, footers,
# "apply" widgets, cookie banners). Drop the obvious non-content tags before
# markdown generation so the extraction agent sees mostly the role text.
_EXCLUDED_TAGS = ["nav", "footer", "aside", "header", "form"]

# Below this, we almost certainly hit a login wall / bot check / JS shell
# rather than a real posting.
_MIN_USEFUL_CHARS = 200

_PAGE_TIMEOUT_MS = 60_000


class JobScrapeError(Exception):
    """Raised when a job posting URL could not be turned into usable text."""


class BrowserSetupError(JobScrapeError):
    """The headless browser itself failed to launch (missing system libs,
    browser not installed) - a server setup problem, not a bad URL."""


# Substrings that mean "the browser can't run here", not "this page is bad".
_BROWSER_SETUP_MARKERS = (
    "shared libraries",
    "install-deps",
    "playwright install",
    "executable doesn't exist",
    "browserType.launch",
    "Host system is missing dependencies",
)


async def scrape_job_posting(url: str) -> str:
    """
    Fetch `url` with a headless browser (Crawl4AI) and return the page as
    markdown, with navigation/footer chrome stripped.

    Raises `JobScrapeError` if the page could not be loaded or produced too
    little text to be a real posting (login wall, bot check, JS-only shell).
    The caller is expected to fall back to asking the user to paste the job
    description text.
    """

    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
        from crawl4ai.async_configs import CacheMode
    except ImportError as exc:  # pragma: no cover - depends on install
        raise JobScrapeError(
            "Web scraping support is not installed on the server."
        ) from exc

    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig(
        page_timeout=_PAGE_TIMEOUT_MS,
        excluded_tags=_EXCLUDED_TAGS,
        remove_overlay_elements=True,
        remove_forms=True,
        exclude_external_links=True,
        cache_mode=CacheMode.BYPASS,
    )

    def _is_browser_setup(message: str) -> bool:
        lowered = message.lower()
        return any(m.lower() in lowered for m in _BROWSER_SETUP_MARKERS)

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_config)
    except Exception as exc:
        logger.exception("Crawl4AI failed to fetch job posting: %s", url)
        if _is_browser_setup(str(exc)):
            raise BrowserSetupError(
                "The scraping browser isn't set up on the server "
                "(run `crawl4ai-setup`). Paste the job description text "
                "instead."
            ) from exc
        raise JobScrapeError(f"Could not load '{url}': {exc}") from exc

    if not result.success:
        message = result.error_message or "unknown error"
        if _is_browser_setup(message):
            raise BrowserSetupError(
                "The scraping browser isn't set up on the server "
                "(run `crawl4ai-setup`). Paste the job description text "
                "instead."
            )
        raise JobScrapeError(f"Could not load '{url}': {message}")

    markdown = (getattr(result, "markdown", None) or "").strip()

    if len(markdown) < _MIN_USEFUL_CHARS:
        raise JobScrapeError(
            f"'{url}' did not return a readable job description "
            "(it may require a login or block automated access)."
        )

    logger.info(
        "Scraped job posting | url=%s | chars=%d",
        url,
        len(markdown),
    )

    return markdown
