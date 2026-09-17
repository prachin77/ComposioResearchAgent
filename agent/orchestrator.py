"""
Orchestrator — runs the research pipeline across all 100 apps.
Resume-safe: saves each result to disk immediately, skips already-completed apps.
"""
import json
import logging
import time
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.logging import RichHandler

from models import AppInput, AppResearch
from agent.researcher import research_app
import config

import warnings

warnings.filterwarnings("ignore")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google").setLevel(logging.WARNING)
logging.getLogger("google.genai").setLevel(logging.WARNING)

console = Console(safe_box=True)
logger = logging.getLogger(__name__)


def load_apps() -> list[AppInput]:
    """Load the 100 apps from data/apps.json."""
    apps_file = config.DATA_DIR / "apps.json"
    with open(apps_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [AppInput(**app) for app in data]


def load_result(app_id: int) -> AppResearch | None:
    """Load a previously saved result for an app. Ignores failed attempts so they get retried."""
    result_file = config.RESULTS_DIR / f"{app_id}.json"
    if result_file.exists():
        try:
            with open(result_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not data.get("description", "").startswith("Research failed"):
                return AppResearch(**data)
        except Exception:
            return None
    return None


def save_result(result: AppResearch):
    """Save a research result to disk."""
    result_file = config.RESULTS_DIR / f"{result.id}.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2, default=str)


def load_all_results() -> list[AppResearch]:
    """Load all saved results."""
    results = []
    for f in sorted(config.RESULTS_DIR.glob("*.json")):
        with open(f, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        results.append(AppResearch(**data))
    return sorted(results, key=lambda r: r.id)


def run_pipeline(force_rerun: bool = False):
    """
    Run the full research pipeline.
    
    Args:
        force_rerun: If True, re-research apps even if results exist
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )

    apps = load_apps()
    console.print(f"\n[bold cyan][*] Composio 100-App Research Pipeline[/bold cyan]")
    console.print(f"[dim]Apps to research: {len(apps)}[/dim]\n")

    completed = 0
    skipped = 0
    failed = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Researching apps...", total=len(apps))

        for app in apps:
            # Check if already done
            if not force_rerun:
                existing = load_result(app.id)
                if existing:
                    skipped += 1
                    progress.update(task, advance=1, description=f"[dim]Skipped: {app.name}[/dim]")
                    continue

            # Research this app
            progress.update(task, description=f"[cyan]{app.name}[/cyan]")
            try:
                result = research_app(app)
                save_result(result)
                completed += 1
            except Exception as e:
                logger.error(f"Failed to research {app.name}: {e}")
                # Save a failure result
                result = AppResearch(
                    id=app.id,
                    name=app.name,
                    category=app.category,
                    website=app.website,
                    description=f"Research failed: {e}",
                    confidence="low",
                )
                save_result(result)
                failed += 1

            progress.update(task, advance=1)

    # Summary
    console.print(f"\n[bold green][OK] Pipeline complete![/bold green]")
    console.print(f"  Completed: {completed}")
    console.print(f"  Skipped (cached): {skipped}")
    console.print(f"  Failed: {failed}")

    # Load and return all results
    all_results = load_all_results()
    console.print(f"  Total results: {len(all_results)}")

    return all_results


if __name__ == "__main__":
    run_pipeline()
