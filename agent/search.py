"""
Web search — uses Composio SDK (Tavily) as primary, DuckDuckGo as fallback.
Demonstrates Composio product familiarity while ensuring the pipeline always works.
"""
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
import config

logger = logging.getLogger(__name__)

# --- Composio Integration ---
_composio_client = None


def _get_composio():
    """Lazily initialize Composio client."""
    global _composio_client
    if _composio_client is None and config.USE_COMPOSIO:
        try:
            from composio import Composio
            _composio_client = Composio(api_key=config.COMPOSIO_API_KEY)
            logger.info("Composio SDK initialized successfully")
        except Exception as e:
            logger.warning(f"Composio SDK init failed: {e}. Falling back to DuckDuckGo.")
            _composio_client = False  # Mark as failed so we don't retry
    return _composio_client if _composio_client else None


def _composio_search(query: str, max_results: int = 5) -> list[dict]:
    """Search using Composio's Tavily integration."""
    client = _get_composio()
    if not client:
        return []
    try:
        result = client.tools.execute(
            tool_slug="TAVILY_SEARCH",
            arguments={"query": query, "max_results": max_results},
            user_id="composio-research-agent",
        )
        # Parse Composio/Tavily response into our standard format
        results = []
        if isinstance(result, dict):
            # Handle different response formats
            items = result.get("results", result.get("data", []))
            if isinstance(items, list):
                for item in items[:max_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "href": item.get("url", item.get("href", "")),
                        "body": item.get("content", item.get("snippet", "")),
                    })
        return results
    except Exception as e:
        logger.warning(f"Composio search failed for '{query}': {e}")
        return []


# --- DuckDuckGo Fallback ---
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=15),
)
def _ddg_search(query: str, max_results: int = 5) -> list[dict]:
    """Fallback search using DuckDuckGo (free, no API key)."""
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return results
    except Exception as e:
        logger.warning(f"DuckDuckGo search failed for '{query}': {e}")
        return []


def search(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the web. Uses Composio/Tavily if available, DuckDuckGo as fallback.
    
    Returns:
        List of dicts with keys: title, href, body
    """
    # Try Composio first
    if config.USE_COMPOSIO:
        results = _composio_search(query, max_results)
        if results:
            logger.debug(f"Composio search '{query}': {len(results)} results")
            return results

    # Fallback to DuckDuckGo
    results = _ddg_search(query, max_results)
    logger.debug(f"DDG search '{query}': {len(results)} results")
    return results


def search_app_docs(app_name: str, website: str) -> list[dict]:
    """
    Run multiple targeted searches for an app's developer documentation.
    Returns deduplicated list of search results.
    """
    queries = [
        f"{app_name} API documentation developer",
        f"{app_name} authentication OAuth API key developer docs",
        f"site:{website} API",
    ]

    all_results = []
    seen_urls = set()

    for query in queries:
        results = search(query, max_results=5)
        for r in results:
            url = r.get("href", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_results.append(r)

    logger.info(f"Search for '{app_name}': {len(all_results)} unique results from {len(queries)} queries")
    return all_results


def search_mcp(app_name: str) -> list[dict]:
    """
    Search specifically for MCP (Model Context Protocol) servers for an app.
    """
    queries = [
        f"{app_name} MCP server model context protocol",
        f"{app_name} MCP github",
    ]

    all_results = []
    seen_urls = set()

    for query in queries:
        results = search(query, max_results=3)
        for r in results:
            url = r.get("href", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_results.append(r)

    return all_results
