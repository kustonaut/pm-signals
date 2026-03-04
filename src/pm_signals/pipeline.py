"""Pipeline orchestrator — fetch → triage → brief → output.

Connects all pipeline stages into a single run:

1. Load configuration from YAML
2. Run configured fetchers to collect signals
3. Triage all signals (route + sentiment + urgency)
4. Generate a daily brief
5. Write outputs (Markdown brief, JSON data, individual signals)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from datetime import date
from typing import Any

from pm_signals.config import Config
from pm_signals.models import Signal, TriageResult, DailyBrief
from pm_signals.triage import TriageEngine
from pm_signals.brief import BriefGenerator
from pm_signals.fetchers.sample import SampleFetcher

logger = logging.getLogger(__name__)


class Pipeline:
    """Main pipeline orchestrator.

    Args:
        config: Loaded Config object.
        output_dir: Directory for pipeline outputs.

    Example::

        config = Config.load("config.yaml")
        pipeline = Pipeline(config)
        brief = pipeline.run()
        print(brief.to_markdown())
    """

    def __init__(self, config: Config, output_dir: str | Path | None = None) -> None:
        self._config = config
        self._output_dir = Path(output_dir) if output_dir else Path("signals_output")

    def run(self, dry_run: bool = False) -> DailyBrief:
        """Execute the full pipeline.

        Args:
            dry_run: If True, process but don't write output files.

        Returns:
            The generated DailyBrief.
        """
        logger.info("Starting pm-signals pipeline")

        # 1. Fetch signals
        signals = self._fetch()
        logger.info(f"Fetched {len(signals)} signals")

        # 2. Triage
        project_keywords = self._config.get_project_keywords()
        engine = TriageEngine(project_keywords)
        results = engine.triage(signals)
        logger.info(f"Triaged {len(results)} signals")

        # 3. Generate brief
        gen = BriefGenerator(
            use_llm=self._config.llm.get("enabled", False),
        )
        brief = gen.generate(signals, results)
        logger.info("Brief generated")

        # 4. Write outputs
        if not dry_run:
            self._write_outputs(brief)
            logger.info(f"Outputs written to {self._output_dir}")

        return brief

    def _fetch(self) -> list[Signal]:
        """Run all configured fetchers and collect signals."""
        all_signals: list[Signal] = []

        for name, fetcher_config in self._config.fetchers.items():
            if not fetcher_config.get("enabled", False):
                continue

            try:
                fetcher = self._create_fetcher(name, fetcher_config)
                if fetcher:
                    signals = fetcher.fetch()
                    all_signals.extend(signals)
                    logger.info(f"  {name}: {len(signals)} signals")
            except Exception as e:
                logger.warning(f"  {name}: failed — {e}")

        return all_signals

    def _create_fetcher(self, name: str, config: dict[str, Any]) -> Any:
        """Create a fetcher instance by name."""
        if name == "sample":
            return SampleFetcher(settings=config)

        if name == "github":
            from pm_signals.fetchers.github import GitHubFetcher
            return GitHubFetcher(settings=config)

        if name == "rss":
            from pm_signals.fetchers.rss import RSSFetcher
            return RSSFetcher(settings=config)

        if name == "file_watcher":
            from pm_signals.fetchers.file_watcher import FileWatcherFetcher
            return FileWatcherFetcher(settings=config)

        logger.warning(f"Unknown fetcher: {name}")
        return None

    def _write_outputs(self, brief: DailyBrief) -> None:
        """Write brief and data outputs to disk."""
        self._output_dir.mkdir(parents=True, exist_ok=True)
        today = date.today().isoformat()

        # Write Markdown brief
        brief_path = self._output_dir / f"brief_{today}.md"
        brief_path.write_text(brief.to_markdown(), encoding="utf-8")

        # Write JSON data
        data_path = self._output_dir / f"signals_{today}.json"
        data_path.write_text(brief.to_json(), encoding="utf-8")

        # Write individual triage results as JSONL
        triage_path = self._output_dir / f"triage_{today}.jsonl"
        with open(triage_path, "w", encoding="utf-8") as f:
            for result in brief.triage_results:
                line = json.dumps({
                    "signal_id": result.signal_id,
                    "project": result.project,
                    "project_confidence": result.project_confidence,
                    "sentiment": result.sentiment,
                    "sentiment_score": result.sentiment_score,
                    "urgency": result.urgency,
                    "urgency_score": result.urgency_score,
                    "action": result.action,
                    "tags": result.tags,
                })
                f.write(line + "\n")
