"""
Verification system — three layers of accuracy checking.
Layer 1: Automated cross-validation (new search vs agent claims)
Layer 2: Consistency checks (logical contradictions)
Layer 3: Human verification protocol (manual spot-check)
"""
import json
import logging
from models import AppResearch, VerificationResult, VerificationSummary
from agent.search import search
from agent.llm import call_gemini_json
import config

logger = logging.getLogger(__name__)

# 20 apps for manual verification: 2 per category, mix of major + niche
VERIFICATION_SAMPLE_IDS = [
    1,   # Salesforce (CRM, major)
    4,   # Attio (CRM, niche)
    11,  # Zendesk (Support, major)
    15,  # Pylon (Support, niche)
    21,  # Slack (Comms, major)
    25,  # Pumble (Comms, niche)
    31,  # Google Ads (Marketing, gated)
    37,  # systeme.io (Marketing, unclear)
    41,  # Shopify (Ecomm, major)
    50,  # fanbasis (Ecomm, obscure)
    53,  # Ahrefs (Data, paid)
    58,  # Sherlock (Data, OSS tool)
    61,  # GitHub (Dev, major)
    66,  # Neo4j (Dev, database)
    71,  # Notion (Prod, major)
    80,  # Harvest (Prod, niche)
    81,  # Stripe (Finance, major)
    90,  # PitchBook (Finance, gated)
    91,  # NotebookLM (AI, new)
    98,  # Mermaid CLI (AI, CLI tool)
]


def run_consistency_checks(result: AppResearch) -> list[VerificationResult]:
    """
    Layer 2: Check for logical contradictions in the research output.
    
    Returns list of verification results for flagged issues.
    """
    issues = []

    # Rule 1: If oauth2_available, "oauth2" should be in auth_methods
    if result.oauth2_available and "oauth2" not in result.auth_methods:
        issues.append(VerificationResult(
            app_id=result.id, app_name=result.name,
            field_name="oauth2_consistency",
            agent_value=f"oauth2_available=True but auth_methods={result.auth_methods}",
            verified_value="inconsistent",
            is_correct=False,
            notes="oauth2_available is True but oauth2 not in auth_methods",
        ))

    # Rule 2: If access_model is self_serve, self_serve_signup should be True
    if result.access_model == "self_serve" and not result.self_serve_signup:
        issues.append(VerificationResult(
            app_id=result.id, app_name=result.name,
            field_name="access_consistency",
            agent_value=f"access_model=self_serve but self_serve_signup=False",
            verified_value="inconsistent",
            is_correct=False,
            notes="access_model is self_serve but self_serve_signup is False",
        ))

    # Rule 3: If has_public_api is False, api_breadth should be none
    if not result.has_public_api and result.api_breadth not in ("none", "unknown"):
        issues.append(VerificationResult(
            app_id=result.id, app_name=result.name,
            field_name="api_consistency",
            agent_value=f"has_public_api=False but api_breadth={result.api_breadth}",
            verified_value="inconsistent",
            is_correct=False,
            notes="No public API but api_breadth is not none",
        ))

    # Rule 4: If buildability is ready/buildable, there shouldn't be a major blocker
    if result.buildability in ("ready", "buildable") and result.blocker_type not in ("none", ""):
        issues.append(VerificationResult(
            app_id=result.id, app_name=result.name,
            field_name="buildability_consistency",
            agent_value=f"buildability={result.buildability} but blocker_type={result.blocker_type}",
            verified_value="inconsistent",
            is_correct=False,
            notes="Marked as buildable but has a blocker",
        ))

    # Rule 5: Evidence should not be empty
    if not result.evidence:
        issues.append(VerificationResult(
            app_id=result.id, app_name=result.name,
            field_name="evidence_present",
            agent_value="no evidence",
            verified_value="missing",
            is_correct=False,
            notes="No evidence URLs provided",
        ))

    return issues


def run_cross_validation(result: AppResearch) -> list[VerificationResult]:
    """
    Layer 1: Automated cross-validation.
    Run a NEW search and compare key claims against fresh results.
    """
    verifications = []
    key_fields = ["primary_auth", "access_model", "has_public_api"]

    # Search for verification
    query = f"{result.name} API authentication developer documentation"
    search_results = search(query, max_results=3)
    search_context = "\n".join([
        f"- {r.get('title', '')}: {r.get('body', '')}" for r in search_results
    ])

    if not search_context.strip():
        return verifications

    # Ask LLM to verify
    prompt = f"""I have the following research claims about {result.name}:

1. Primary authentication: {result.primary_auth}
2. Access model: {result.access_model}
3. Has public API: {result.has_public_api}
4. API breadth: {result.api_breadth}

Here are fresh search results about this app:
{search_context}

For each claim, respond with a JSON object:
{{
  "verifications": [
    {{
      "field": "primary_auth",
      "agent_claim": "{result.primary_auth}",
      "search_says": "what the search results indicate",
      "is_consistent": true/false,
      "notes": "explanation"
    }},
    ... (for each of the 4 fields)
  ]
}}

Be strict. Only mark is_consistent=true if the search results clearly support the claim."""

    try:
        raw = call_gemini_json(prompt)
        for v in raw.get("verifications", []):
            verifications.append(VerificationResult(
                app_id=result.id,
                app_name=result.name,
                field_name=v.get("field", ""),
                agent_value=v.get("agent_claim", ""),
                verified_value=v.get("search_says", ""),
                is_correct=v.get("is_consistent", False),
                notes=v.get("notes", ""),
            ))
    except Exception as e:
        logger.warning(f"Cross-validation failed for {result.name}: {e}")

    return verifications


def run_verification(results: list[AppResearch], sample_ids: list[int] = None) -> VerificationSummary:
    """
    Run the full verification pipeline on a sample of apps.
    
    Args:
        results: All research results
        sample_ids: App IDs to verify (default: VERIFICATION_SAMPLE_IDS)
    
    Returns:
        VerificationSummary with accuracy metrics
    """
    if sample_ids is None:
        sample_ids = VERIFICATION_SAMPLE_IDS

    sample_results = [r for r in results if r.id in sample_ids]
    all_verifications = []

    logger.info(f"Running verification on {len(sample_results)} apps...")

    for result in sample_results:
        # Layer 1: Cross-validation
        cross_val = run_cross_validation(result)
        all_verifications.extend(cross_val)

        # Layer 2: Consistency checks
        consistency = run_consistency_checks(result)
        all_verifications.extend(consistency)

    # Calculate metrics
    total_fields = len(all_verifications)
    correct_fields = sum(1 for v in all_verifications if v.is_correct)
    field_accuracy = correct_fields / total_fields if total_fields > 0 else 0.0

    # Row accuracy: an app is "correct" if all its verified fields are correct
    app_results = {}
    for v in all_verifications:
        if v.app_id not in app_results:
            app_results[v.app_id] = True
        if not v.is_correct:
            app_results[v.app_id] = False
    
    correct_rows = sum(1 for is_correct in app_results.values() if is_correct)
    row_accuracy = correct_rows / len(app_results) if app_results else 0.0

    # Identify error patterns
    error_patterns = []
    error_fields = [v.field_name for v in all_verifications if not v.is_correct]
    from collections import Counter
    for field, count in Counter(error_fields).most_common(5):
        error_patterns.append(f"{field}: {count} errors")

    summary = VerificationSummary(
        sample_size=len(sample_results),
        total_fields_checked=total_fields,
        correct_fields=correct_fields,
        field_accuracy=round(field_accuracy, 4),
        row_accuracy=round(row_accuracy, 4),
        pass_number=1,
        results=all_verifications,
        error_patterns=error_patterns,
    )

    logger.info(f"Verification complete: field_accuracy={summary.field_accuracy:.1%}, row_accuracy={summary.row_accuracy:.1%}")
    return summary
