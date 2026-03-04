"""Quickstart example for pm-signals.

Run:  python examples/quickstart.py
"""

from pm_signals.fetchers.sample import SampleFetcher
from pm_signals.triage import TriageEngine
from pm_signals.brief import BriefGenerator


def main():
    # 1. Fetch sample signals (built-in, zero config)
    fetcher = SampleFetcher()
    signals = fetcher.fetch()
    print(f"Fetched {len(signals)} signals\n")

    # 2. Define project areas with keywords
    project_keywords = {
        "Frontend": ["react", "css", "UI", "component", "dashboard", "mobile", "accessibility"],
        "Backend": ["api", "server", "database", "endpoint", "rate limit", "cache", "GraphQL"],
        "Infrastructure": ["deploy", "CI/CD", "docker", "kubernetes", "terraform", "monitoring"],
        "Data": ["pipeline", "ETL", "analytics", "warehouse", "data quality"],
    }

    # 3. Triage all signals
    engine = TriageEngine(project_keywords)
    results = engine.triage(signals)

    # 4. Print triage results
    urgency_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
    for sig, result in zip(signals, results):
        emoji = urgency_emoji.get(result.urgency, "⚪")
        print(
            f"  {emoji} [{result.project:<16s}] "
            f"{result.sentiment:<13s} "
            f"→ {result.action:<12s} "
            f"{sig.title[:55]}"
        )

    # 5. Generate a daily brief
    gen = BriefGenerator()
    brief = gen.generate(signals, results)
    print(f"\n{'='*60}\n")
    print(brief.to_markdown())


if __name__ == "__main__":
    main()
