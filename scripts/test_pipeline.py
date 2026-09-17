"""
Quick test: research just 2 apps to verify the pipeline works end-to-end.
"""
import sys
import os
import json
import logging

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.logging import RichHandler
from rich.console import Console
from models import AppInput
from agent.researcher import research_app
import config

console = Console()
logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[RichHandler(console=console)])

# Test with 2 apps: one well-known (Slack), one niche (Attio)
test_apps = [
    AppInput(id=21, name="Slack", category="Communications and Messaging", website="slack.com"),
    AppInput(id=4, name="Attio", category="CRM and Sales", website="attio.com"),
]

print(f"\n{'='*60}")
print(f"  PIPELINE TEST — {len(test_apps)} apps")
print(f"{'='*60}\n")

for app in test_apps:
    print(f"\n--- Researching: {app.name} ---")
    result = research_app(app)

    # Save result
    result_file = config.RESULTS_DIR / f"{result.id}.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2, default=str)

    # Print summary
    print(f"\n  Description: {result.description}")
    print(f"  Auth: {result.auth_methods} (primary: {result.primary_auth})")
    print(f"  Access: {result.access_model} (self-serve: {result.self_serve_signup})")
    print(f"  API: {result.api_types} breadth={result.api_breadth}")
    print(f"  MCP: official={result.has_official_mcp} community={result.has_community_mcp}")
    print(f"  Buildability: {result.buildability} (blocker: {result.primary_blocker or 'none'})")
    print(f"  Confidence: {result.confidence}")
    print(f"  Evidence: {len(result.evidence)} items")
    print(f"  Saved to: {result_file}")

print(f"\n{'='*60}")
print(f"  ✅ TEST COMPLETE")
print(f"{'='*60}")
