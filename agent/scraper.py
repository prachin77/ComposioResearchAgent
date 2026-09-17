"""
URL content extraction — fetch web pages and extract clean text.
"""
import logging
import hashlib
from pathlib import Path
import httpx
import trafilatura
from tenacity import retry, stop_after_attempt, wait_fixed
import config

logger = logging.getLogger(__name__)


def _cache_path(url: str) -> Path:
    """Get the cache file path for a URL."""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return config.CACHE_DIR / f"{url_hash}.txt"


def _read_cache(url: str) -> str | None:
    """Read cached content for a URL."""
    path = _cache_path(url)
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    return None


def _write_cache(url: str, content: str):
    """Cache content for a URL."""
    path = _cache_path(url)
    path.write_text(content, encoding="utf-8")


@retry(stop=stop_after_attempt(2), wait=wait_fixed(2))
def fetch_url(url: str) -> str | None:
    """
    Fetch a URL and extract clean text content.
    Uses trafilatura for intelligent content extraction.
    
    Args:
        url: The URL to fetch
    
    Returns:
        Extracted text content, or None if failed
    """
    # Check cache first
    cached = _read_cache(url)
    if cached is not None:
        logger.debug(f"Cache hit: {url}")
        return cached

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0; academic research)"
        }
        with httpx.Client(timeout=config.URL_FETCH_TIMEOUT, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            html = response.text

        # Extract clean text using trafilatura
        text = trafilatura.extract(
            html,
            include_links=False,
            include_tables=True,
            favor_recall=True,
        )

        if not text:
            # Fallback: basic HTML text extraction
            from html.parser import HTMLParser
            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text_parts = []
                    self._skip = False
                def handle_starttag(self, tag, attrs):
                    if tag in ('script', 'style', 'nav', 'footer', 'header'):
                        self._skip = True
                def handle_endtag(self, tag):
                    if tag in ('script', 'style', 'nav', 'footer', 'header'):
                        self._skip = False
                def handle_data(self, data):
                    if not self._skip:
                        stripped = data.strip()
                        if stripped:
                            self.text_parts.append(stripped)
            extractor = TextExtractor()
            extractor.feed(html)
            text = "\n".join(extractor.text_parts)

        if text:
            # Truncate to max chars
            text = text[:config.MAX_DOC_CHARS]
            _write_cache(url, text)
            logger.debug(f"Fetched {url}: {len(text)} chars")
            return text
        else:
            logger.warning(f"No content extracted from {url}")
            return None

    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def fetch_multiple(urls: list[str], max_urls: int = None) -> dict[str, str]:
    """
    Fetch multiple URLs and return a dict of url -> content.
    
    Args:
        urls: List of URLs to fetch
        max_urls: Maximum number of URLs to fetch (default: config.MAX_URLS_PER_APP)
    
    Returns:
        Dict mapping URL to extracted text content
    """
    if max_urls is None:
        max_urls = config.MAX_URLS_PER_APP

    results = {}
    for url in urls[:max_urls]:
        content = fetch_url(url)
        if content:
            results[url] = content

    logger.info(f"Fetched {len(results)}/{len(urls[:max_urls])} URLs successfully")
    return results
