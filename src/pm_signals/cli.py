"""pm-signals CLI — multi-source signal intelligence pipeline.

Commands::

    pm-signals pipeline    Run the full pipeline (fetch → triage → brief)
    pm-signals demo        Run with built-in sample data (zero config)
    pm-signals fetch       Fetch signals from configured sources
    pm-signals triage      Triage previously fetched signals
    pm-signals brief       Generate a brief from triaged data
    pm-signals cleanup     Archive old output files
    pm-signals stats       Show signal statistics
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click

from pm_signals.config import Config


def _setup_logging(verbose: bool) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
    )


@click.group()
@click.version_option(package_name="pm-signals")
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging.")
@click.option(
    "-c",
    "--config",
    "config_path",
    default=None,
    type=click.Path(exists=True),
    help="Path to config YAML file.",
)
@click.option(
    "-o",
    "--output",
    "output_dir",
    default="signals_output",
    help="Output directory for briefs and data.",
)
@click.pass_context
def main(ctx: click.Context, verbose: bool, config_path: str | None, output_dir: str) -> None:
    """pm-signals — multi-source signal intelligence for PMs."""
    _setup_logging(verbose)
    ctx.ensure_object(dict)

    if config_path:
        ctx.obj["config"] = Config.load(config_path)
    else:
        ctx.obj["config"] = Config.load()  # Uses DEFAULT_CONFIG

    ctx.obj["output_dir"] = output_dir


@main.command()
@click.option("--dry-run", is_flag=True, help="Process but don't write files.")
@click.pass_context
def pipeline(ctx: click.Context, dry_run: bool) -> None:
    """Run the full pipeline: fetch → triage → brief."""
    from pm_signals.pipeline import Pipeline

    config = ctx.obj["config"]
    output_dir = ctx.obj["output_dir"]

    p = Pipeline(config, output_dir=output_dir)
    brief = p.run(dry_run=dry_run)

    click.echo(f"\n{brief.summary}")
    click.echo(f"\nStats: {json.dumps(brief.stats, indent=2)}")

    if not dry_run:
        click.echo(f"\nOutputs → {output_dir}/")


@main.command()
@click.option("--count", default=20, help="Number of sample signals.")
@click.pass_context
def demo(ctx: click.Context, count: int) -> None:
    """Run a demo with built-in sample data — zero configuration needed."""
    from pm_signals.fetchers.sample import SampleFetcher
    from pm_signals.triage import TriageEngine
    from pm_signals.brief import BriefGenerator

    click.echo("🚀 pm-signals demo\n")

    # Use default config for project keywords
    config = ctx.obj["config"]

    # Fetch sample signals
    fetcher = SampleFetcher(settings={"count": count})
    signals = fetcher.fetch()
    click.echo(f"📡 Fetched {len(signals)} sample signals\n")

    # Show signals
    for i, sig in enumerate(signals, 1):
        click.echo(f"  {i:2d}. [{sig.source}] {sig.title}")

    click.echo()

    # Triage
    project_keywords = config.get_project_keywords()
    engine = TriageEngine(project_keywords)
    results = engine.triage(signals)

    click.echo("🔍 Triage Results:\n")
    urgency_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
    for result in results:
        sig = next((s for s in signals if s.id == result.signal_id), None)
        if not sig:
            continue
        emoji = urgency_emoji.get(result.urgency, "⚪")
        click.echo(
            f"  {emoji} [{result.project:<16s}] "
            f"{result.sentiment:<13s} "
            f"→ {result.action:<12s} "
            f"{sig.title[:50]}"
        )

    # Brief
    gen = BriefGenerator()
    brief = gen.generate(signals, results)

    click.echo(f"\n{'='*60}")
    click.echo(brief.to_markdown()[:2000])  # First 2000 chars

    click.echo(f"\n✅ Demo complete — {len(signals)} signals triaged")
    click.echo("   Install with: pip install pm-signals")
    click.echo("   Then run:     pm-signals pipeline")


@main.command()
@click.pass_context
def fetch(ctx: click.Context) -> None:
    """Fetch signals from all configured sources."""
    from pm_signals.pipeline import Pipeline

    config = ctx.obj["config"]
    p = Pipeline(config, output_dir=ctx.obj["output_dir"])
    signals = p._fetch()

    click.echo(f"Fetched {len(signals)} signals")
    for sig in signals:
        click.echo(f"  [{sig.source}] {sig.title}")


@main.command()
@click.option("--archive-days", default=14, help="Archive files older than N days.")
@click.option("--delete-days", default=60, help="Delete archived files older than N days.")
@click.option("--dry-run", is_flag=True, help="Show what would happen.")
@click.pass_context
def cleanup(ctx: click.Context, archive_days: int, delete_days: int, dry_run: bool) -> None:
    """Archive and clean old output files."""
    from pm_signals.cleanup import cleanup as do_cleanup

    output_dir = ctx.obj["output_dir"]
    counts = do_cleanup(output_dir, archive_days, delete_days, dry_run)

    mode = " [dry-run]" if dry_run else ""
    click.echo(f"Cleanup{mode}: {counts['archived']} archived, {counts['deleted']} deleted, {counts['skipped']} skipped")


@main.command()
@click.pass_context
def stats(ctx: click.Context) -> None:
    """Show signal statistics from the latest run."""
    output_dir = Path(ctx.obj["output_dir"])

    if not output_dir.exists():
        click.echo("No output directory found. Run 'pm-signals pipeline' first.")
        return

    # Find latest signals JSON
    json_files = sorted(output_dir.glob("signals_*.json"), reverse=True)
    if not json_files:
        click.echo("No signal data found. Run 'pm-signals pipeline' first.")
        return

    latest = json_files[0]
    data = json.loads(latest.read_text(encoding="utf-8"))

    stats_data = data.get("stats", {})
    click.echo(f"📊 Signal Statistics ({latest.name})\n")
    click.echo(f"  Total signals: {stats_data.get('total', 0)}")
    click.echo(f"  Sources:       {', '.join(stats_data.get('sources', []))}")

    click.echo("\n  Urgency breakdown:")
    for level, count in stats_data.get("urgency", {}).items():
        emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(level, "⚪")
        click.echo(f"    {emoji} {level}: {count}")

    click.echo("\n  Sentiment breakdown:")
    for label, count in stats_data.get("sentiment", {}).items():
        click.echo(f"    {label}: {count}")

    click.echo("\n  Project breakdown:")
    for project, count in stats_data.get("projects", {}).items():
        click.echo(f"    {project}: {count}")


if __name__ == "__main__":
    main()
