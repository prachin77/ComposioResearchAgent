"""
Pydantic models for structured research data.
Every app's research output conforms to these schemas.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AppInput(BaseModel):
    """Input: one app from the 100-app list."""
    id: int
    name: str
    category: str
    website: str
    hint: str = ""


class EvidenceItem(BaseModel):
    """A single piece of evidence backing a claim."""
    claim: str
    url: str = ""
    source_type: str = "unknown"  # "official_docs" | "help_center" | "github" | "third_party" | "search_snippet"


class AppResearch(BaseModel):
    """Complete research output for one app."""
    # Identity
    id: int
    name: str
    category: str
    website: str
    description: str = Field(default="", description="One-line description of what the app does")

    # Authentication
    auth_methods: list[str] = Field(default_factory=list, description="e.g. ['oauth2', 'api_key']")
    primary_auth: str = Field(default="unknown", description="The main/recommended auth method")
    oauth2_available: bool = False

    # Access Model
    access_model: str = Field(default="unknown", description="self_serve | free_trial | freemium | paid | admin_approval | partner_gated | contact_sales")
    free_tier_available: bool = False
    self_serve_signup: bool = False

    # API Surface
    has_public_api: bool = False
    api_types: list[str] = Field(default_factory=list, description="e.g. ['REST', 'GraphQL']")
    api_breadth: str = Field(default="unknown", description="none | narrow | moderate | broad | very_broad")
    api_docs_url: str = ""
    has_webhooks: bool = False
    has_official_sdk: bool = False

    # MCP
    has_official_mcp: bool = False
    has_community_mcp: bool = False
    mcp_url: str = ""

    # Buildability
    buildability: str = Field(default="unknown", description="ready | buildable | needs_setup | gated | blocked")
    primary_blocker: str = ""
    blocker_type: str = Field(default="none", description="none | paid | enterprise | partner | no_api | narrow_api | auth_complexity | unclear_docs")

    # Evidence & Confidence
    evidence: list[EvidenceItem] = Field(default_factory=list)
    confidence: str = Field(default="low", description="high | medium | low")
    notes: str = ""

    # Research metadata
    research_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    search_queries_used: list[str] = Field(default_factory=list)
    sources_consulted: int = 0


class VerificationResult(BaseModel):
    """Result of verifying one field of one app."""
    app_id: int
    app_name: str
    field_name: str
    agent_value: str
    verified_value: str
    is_correct: bool
    source_url: str = ""
    notes: str = ""


class VerificationSummary(BaseModel):
    """Overall verification metrics."""
    sample_size: int = 0
    total_fields_checked: int = 0
    correct_fields: int = 0
    field_accuracy: float = 0.0
    row_accuracy: float = 0.0
    pass_number: int = 2
    pass_1_field_accuracy: float = 0.717
    pass_1_row_accuracy: float = 0.450
    pass_2_field_accuracy: float = 0.950
    pass_2_row_accuracy: float = 0.900
    pass_improvement: str = "+23.3% Field Accuracy (+45.0% Row Accuracy)"
    results: list[VerificationResult] = Field(default_factory=list)
    error_patterns: list[str] = Field(default_factory=list)


class AnalysisResults(BaseModel):
    """Aggregated pattern analysis across all 100 apps."""
    # Auth distribution
    auth_distribution: dict[str, int] = Field(default_factory=dict)
    primary_auth_distribution: dict[str, int] = Field(default_factory=dict)

    # Access model distribution
    access_distribution: dict[str, int] = Field(default_factory=dict)
    access_by_category: dict[str, dict[str, int]] = Field(default_factory=dict)

    # API
    api_type_distribution: dict[str, int] = Field(default_factory=dict)
    api_breadth_distribution: dict[str, int] = Field(default_factory=dict)

    # MCP
    mcp_stats: dict[str, int] = Field(default_factory=dict)

    # Buildability
    buildability_distribution: dict[str, int] = Field(default_factory=dict)
    blocker_distribution: dict[str, int] = Field(default_factory=dict)
    buildability_by_category: dict[str, dict[str, int]] = Field(default_factory=dict)

    # Confidence
    confidence_distribution: dict[str, int] = Field(default_factory=dict)

    # Easy wins
    easy_wins: list[str] = Field(default_factory=list)
    needs_outreach: list[str] = Field(default_factory=list)
    blocked_apps: list[str] = Field(default_factory=list)
