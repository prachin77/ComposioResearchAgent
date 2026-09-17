"""
Pattern analysis — extract insights from the 100-app research dataset.
"""
import json
import logging
from collections import Counter, defaultdict
from models import AppResearch, AnalysisResults

logger = logging.getLogger(__name__)


def analyze_patterns(results: list[AppResearch]) -> AnalysisResults:
    """
    Analyze patterns across all research results.
    
    Args:
        results: List of all app research results
    
    Returns:
        AnalysisResults with computed statistics
    """
    analysis = AnalysisResults()

    # --- Auth Distribution ---
    all_auth = []
    primary_auths = []
    for r in results:
        all_auth.extend(r.auth_methods)
        if r.primary_auth and r.primary_auth != "unknown":
            primary_auths.append(r.primary_auth)

    analysis.auth_distribution = dict(Counter(all_auth).most_common())
    analysis.primary_auth_distribution = dict(Counter(primary_auths).most_common())

    # --- Access Model Distribution ---
    access_models = [r.access_model for r in results if r.access_model != "unknown"]
    analysis.access_distribution = dict(Counter(access_models).most_common())

    # Access by category
    cat_access = defaultdict(lambda: Counter())
    for r in results:
        if r.access_model != "unknown":
            cat_access[r.category][r.access_model] += 1
    analysis.access_by_category = {cat: dict(counts) for cat, counts in cat_access.items()}

    # --- API Distribution ---
    all_api_types = []
    for r in results:
        all_api_types.extend(r.api_types)
    analysis.api_type_distribution = dict(Counter(all_api_types).most_common())

    breadths = [r.api_breadth for r in results if r.api_breadth != "unknown"]
    analysis.api_breadth_distribution = dict(Counter(breadths).most_common())

    # --- MCP Stats ---
    mcp_counts = {
        "official_mcp": sum(1 for r in results if r.has_official_mcp),
        "community_mcp": sum(1 for r in results if r.has_community_mcp),
        "any_mcp": sum(1 for r in results if r.has_official_mcp or r.has_community_mcp),
        "no_mcp": sum(1 for r in results if not r.has_official_mcp and not r.has_community_mcp),
    }
    analysis.mcp_stats = mcp_counts

    # --- Buildability ---
    buildabilities = [r.buildability for r in results if r.buildability != "unknown"]
    analysis.buildability_distribution = dict(Counter(buildabilities).most_common())

    blockers = [r.blocker_type for r in results if r.blocker_type and r.blocker_type != "none"]
    analysis.blocker_distribution = dict(Counter(blockers).most_common())

    # Buildability by category
    cat_build = defaultdict(lambda: Counter())
    for r in results:
        if r.buildability != "unknown":
            cat_build[r.category][r.buildability] += 1
    analysis.buildability_by_category = {cat: dict(counts) for cat, counts in cat_build.items()}

    # --- Confidence ---
    confs = [r.confidence for r in results]
    analysis.confidence_distribution = dict(Counter(confs).most_common())

    # --- Segmentation ---
    # Easy wins: self-serve + broad API + buildable
    analysis.easy_wins = [
        r.name for r in results
        if r.self_serve_signup
        and r.api_breadth in ("broad", "very_broad")
        and r.buildability in ("ready", "buildable")
    ]

    # Needs outreach: has API but gated
    analysis.needs_outreach = [
        r.name for r in results
        if r.has_public_api
        and r.access_model in ("partner_gated", "contact_sales", "admin_approval")
    ]

    # Blocked: no usable API
    analysis.blocked_apps = [
        r.name for r in results
        if not r.has_public_api
        or r.buildability == "blocked"
    ]

    logger.info(f"Analysis complete: {len(analysis.easy_wins)} easy wins, "
                f"{len(analysis.needs_outreach)} need outreach, "
                f"{len(analysis.blocked_apps)} blocked")

    return analysis
