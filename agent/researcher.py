"""
Per-app research logic — the core intelligence of the pipeline.
Takes one app, searches, reads docs, and produces structured AppResearch.
"""
import json
import logging
from models import AppInput, AppResearch, EvidenceItem
from agent.search import search_app_docs, search_mcp
from agent.scraper import fetch_multiple
from agent.llm import call_gemini_json

logger = logging.getLogger(__name__)

# System prompt for the research extraction LLM call
RESEARCH_SYSTEM_PROMPT = """You are an expert developer-tools analyst researching applications for integration into Composio, a platform that turns apps into tools AI agents can call.

Your job is to analyze documentation excerpts and search results about an application, then produce a structured JSON assessment.

Be precise and evidence-based. If information is not available or unclear, say so honestly rather than guessing.

For auth_methods, use these exact values: "oauth2", "api_key", "basic_auth", "token", "jwt", "other"
For access_model, use: "self_serve", "free_trial", "freemium", "paid", "admin_approval", "partner_gated", "contact_sales"
For api_breadth, use: "none", "narrow", "moderate", "broad", "very_broad"
For buildability, use: "ready", "buildable", "needs_setup", "gated", "blocked"
For blocker_type, use: "none", "paid", "enterprise", "partner", "no_api", "narrow_api", "auth_complexity", "unclear_docs"
For confidence, use: "high", "medium", "low"
"""


def _build_research_prompt(app: AppInput, search_results: list[dict], doc_contents: dict[str, str], mcp_results: list[dict]) -> str:
    """Build the LLM prompt with all gathered context."""

    # Format search results
    search_text = ""
    for i, r in enumerate(search_results[:10], 1):
        search_text += f"\n{i}. [{r.get('title', 'N/A')}]({r.get('href', '')})\n   {r.get('body', '')}\n"

    # Format doc contents
    docs_text = ""
    for url, content in list(doc_contents.items())[:4]:
        truncated = content[:3000]
        docs_text += f"\n--- Document from {url} ---\n{truncated}\n"

    # Format MCP results
    mcp_text = ""
    for r in mcp_results[:5]:
        mcp_text += f"\n- [{r.get('title', '')}]({r.get('href', '')}): {r.get('body', '')}\n"

    prompt = f"""Research the application "{app.name}" (website: {app.website}, category: {app.category}).
{f'Hint: {app.hint}' if app.hint else ''}

## Search Results
{search_text if search_text else "No search results found."}

## Documentation Excerpts
{docs_text if docs_text else "No documentation could be fetched."}

## MCP Server Search Results
{mcp_text if mcp_text else "No MCP server results found."}

Based on the above information, produce a JSON object with these fields:

{{
  "description": "One-line description of what this app does",
  "auth_methods": ["list of auth methods supported, e.g. oauth2, api_key, basic_auth, token"],
  "primary_auth": "the main/recommended auth method",
  "oauth2_available": true/false,
  "access_model": "self_serve | free_trial | freemium | paid | admin_approval | partner_gated | contact_sales",
  "free_tier_available": true/false,
  "self_serve_signup": true/false,
  "has_public_api": true/false,
  "api_types": ["REST", "GraphQL", etc],
  "api_breadth": "none | narrow | moderate | broad | very_broad",
  "api_docs_url": "URL to the main API documentation",
  "has_webhooks": true/false,
  "has_official_sdk": true/false,
  "has_official_mcp": true/false,
  "has_community_mcp": true/false,
  "mcp_url": "URL to MCP server if found, or empty string",
  "buildability": "ready | buildable | needs_setup | gated | blocked",
  "primary_blocker": "main blocker description or empty string",
  "blocker_type": "none | paid | enterprise | partner | no_api | narrow_api | auth_complexity | unclear_docs",
  "confidence": "high | medium | low",
  "notes": "any important caveats or observations",
  "evidence_claims": [
    {{"claim": "what you determined", "url": "source URL", "source_type": "official_docs | help_center | github | third_party | search_snippet"}}
  ]
}}

Be rigorous. Only mark confidence as "high" if you have clear evidence from official sources."""

    return prompt


def research_app(app: AppInput) -> AppResearch:
    """
    Research a single app through the full pipeline:
    1. Web search for API docs & auth info
    2. Fetch and read documentation pages
    3. Search for MCP servers
    4. LLM extraction of structured data
    
    Args:
        app: The app to research
    
    Returns:
        Complete AppResearch object
    """
    logger.info(f"Researching app {app.id}: {app.name}")

    # Stage 1: Web search
    search_results = search_app_docs(app.name, app.website)
    search_queries = [
        f"{app.name} API documentation developer",
        f"{app.name} authentication OAuth API key developer docs",
        f"site:{app.website} API",
    ]

    # Stage 2: Fetch top documentation URLs
    urls = [r["href"] for r in search_results if r.get("href")]
    # Prioritize official docs
    official_urls = [u for u in urls if app.website.replace("www.", "") in u]
    other_urls = [u for u in urls if u not in official_urls]
    ordered_urls = official_urls + other_urls
    doc_contents = fetch_multiple(ordered_urls, max_urls=6)

    # Stage 3: MCP search
    mcp_results = search_mcp(app.name)

    # Stage 4: LLM extraction
    prompt = _build_research_prompt(app, search_results, doc_contents, mcp_results)
    try:
        raw = call_gemini_json(prompt, system_prompt=RESEARCH_SYSTEM_PROMPT)
    except Exception as e:
        logger.error(f"LLM extraction failed for {app.name}: {e}")
        return AppResearch(
            id=app.id,
            name=app.name,
            category=app.category,
            website=app.website,
            description=f"Research failed: {e}",
            confidence="low",
            notes=f"LLM extraction error: {e}",
            search_queries_used=search_queries,
        )

    if isinstance(raw, list):
        raw = raw[0] if raw and isinstance(raw[0], dict) else {}
    elif not isinstance(raw, dict):
        raw = {}

    # Build evidence list
    evidence = []
    for ev in raw.get("evidence_claims", []):
        if isinstance(ev, dict):
            evidence.append(EvidenceItem(
                claim=ev.get("claim", ""),
                url=ev.get("url", ""),
                source_type=ev.get("source_type", "unknown"),
            ))
        elif isinstance(ev, str):
            evidence.append(EvidenceItem(
                claim=ev,
                url="",
                source_type="general",
            ))

    # Construct the AppResearch object
    result = AppResearch(
        id=app.id,
        name=app.name,
        category=app.category,
        website=app.website,
        description=raw.get("description", ""),
        auth_methods=raw.get("auth_methods", []),
        primary_auth=raw.get("primary_auth", "unknown"),
        oauth2_available=raw.get("oauth2_available", False),
        access_model=raw.get("access_model", "unknown"),
        free_tier_available=raw.get("free_tier_available", False),
        self_serve_signup=raw.get("self_serve_signup", False),
        has_public_api=raw.get("has_public_api", False),
        api_types=raw.get("api_types", []),
        api_breadth=raw.get("api_breadth", "unknown"),
        api_docs_url=raw.get("api_docs_url", ""),
        has_webhooks=raw.get("has_webhooks", False),
        has_official_sdk=raw.get("has_official_sdk", False),
        has_official_mcp=raw.get("has_official_mcp", False),
        has_community_mcp=raw.get("has_community_mcp", False),
        mcp_url=raw.get("mcp_url", ""),
        buildability=raw.get("buildability", "unknown"),
        primary_blocker=raw.get("primary_blocker", ""),
        blocker_type=raw.get("blocker_type", "none"),
        confidence=raw.get("confidence", "low"),
        notes=raw.get("notes", ""),
        evidence=evidence,
        search_queries_used=search_queries,
        sources_consulted=len(doc_contents),
    )

    logger.info(f"  [OK] {app.name}: {result.buildability} (confidence: {result.confidence})")
    return result
