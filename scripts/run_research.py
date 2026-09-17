"""
Main entry point — runs the full research pipeline.
Usage: python run_research.py [--force]
"""
import sys
import json
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add parent dir to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.orchestrator import run_pipeline, load_all_results
from agent.verifier import run_verification
from analysis.patterns import analyze_patterns
import config


def main():
    force = "--force" in sys.argv

    print("=" * 60)
    print("  COMPOSIO 100-APP RESEARCH PIPELINE")
    print("=" * 60)

    # Step 1: Research all apps
    print("\n📋 Step 1: Researching 100 apps...")
    results = run_pipeline(force_rerun=force)

    # Step 2: Run verification
    print("\n🔍 Step 2: Running verification...")
    verification = run_verification(results)

    # Save verification results
    verif_path = config.DATA_DIR / "verification_results.json"
    with open(verif_path, "w", encoding="utf-8") as f:
        json.dump(verification.model_dump(), f, indent=2, default=str)
    print(f"  Verification saved to {verif_path}")
    print(f"  Field accuracy: {verification.field_accuracy:.1%}")
    print(f"  Row accuracy: {verification.row_accuracy:.1%}")

    # Step 3: Pattern analysis
    print("\n📊 Step 3: Analyzing patterns...")
    analysis = analyze_patterns(results)

    # Save analysis results
    analysis_path = config.DATA_DIR / "analysis_results.json"
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(analysis.model_dump(), f, indent=2, default=str)
    print(f"  Analysis saved to {analysis_path}")
    print(f"  Easy wins: {len(analysis.easy_wins)} apps")
    print(f"  Needs outreach: {len(analysis.needs_outreach)} apps")
    print(f"  Blocked: {len(analysis.blocked_apps)} apps")

    # Step 4: Save combined dataset for HTML generation
    print("\n[*] Step 4: Saving combined dataset...")
    dataset = {
        "results": [r.model_dump() for r in results],
        "analysis": analysis.model_dump(),
        "verification": verification.model_dump(),
    }
    dataset_path = config.OUTPUT_DIR / "data.json"
    with open(dataset_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, default=str)
    print(f"  Dataset saved to {dataset_path}")

    # Step 5: Generate self-contained interactive HTML deliverable
    print("\n[*] Step 5: Generating interactive HTML dashboard...")
    try:
        from scripts.generate_html import generate_html as gen_html
        html = gen_html(dataset)
        html_path = config.OUTPUT_DIR / "index.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  HTML report generated at: {html_path}")
    except Exception as e:
        print(f"  Warning: Failed to generate HTML automatically: {e}")
        print("  You can generate it manually with: py scripts/generate_html.py")

    print("\n" + "=" * 60)
    print("  [SUCCESS] PIPELINE COMPLETE!")
    print(f"  View your report by opening: {config.OUTPUT_DIR / 'index.html'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
