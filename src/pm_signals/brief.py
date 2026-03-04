"""Brief generator — synthesize triaged signals into a daily brief.

Generates a structured Markdown brief from triaged signals,
organized by project area with urgency badges, statistics,
and an executive summary.  Optionally uses an LLM for the
summary paragraph (falls back to template-based generation).
"""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any

from pm_signals.models import DailyBrief, Signal, TriageResult


class BriefGenerator:
    """Generate daily intelligence briefs from triaged signals.

    Args:
        use_llm: Whether to attempt LLM-based summary generation.
            Falls back to template-based if LLM is unavailable.

    Example::

        gen = BriefGenerator()
        brief = gen.generate(signals, triage_results)
        print(brief.to_markdown())
    """

    def __init__(self, use_llm: bool = False) -> None:
        self._use_llm = use_llm

    def generate(
        self,
        signals: list[Signal],
        triage_results: list[TriageResult],
        brief_date: str | None = None,
    ) -> DailyBrief:
        """Generate a daily brief from signals and their triage results.

        Args:
            signals: List of fetched signals.
            triage_results: Corresponding triage results.
            brief_date: Override date string (default: today).

        Returns:
            A DailyBrief ready for rendering.
        """
        if brief_date is None:
            brief_date = date.today().isoformat()

        # Build lookup
        signal_map = {s.id: s for s in signals}

        # Organize by project
        sections: dict[str, list[dict[str, Any]]] = {}
        for result in triage_results:
            sig = signal_map.get(result.signal_id)
            if not sig:
                continue

            project = result.project
            if project not in sections:
                sections[project] = []

            sections[project].append({
                "title": sig.title,
                "source": sig.source,
                "author": sig.author,
                "urgency": result.urgency,
                "sentiment": result.sentiment,
                "action": result.action,
                "confidence": result.project_confidence,
                "url": sig.url,
            })

        # Sort each section by urgency priority
        urgency_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        for items in sections.values():
            items.sort(key=lambda x: urgency_order.get(x["urgency"], 4))

        # Compute stats
        stats = self._compute_stats(signals, triage_results)

        # Generate summary
        summary = self._generate_summary(stats, sections)

        return DailyBrief(
            date=brief_date,
            signals=signals,
            triage_results=triage_results,
            summary=summary,
            sections=sections,
            stats=stats,
        )

    def _compute_stats(
        self, signals: list[Signal], results: list[TriageResult]
    ) -> dict[str, Any]:
        """Compute aggregate statistics."""
        source_counts = Counter(s.source for s in signals)
        urgency_counts = Counter(r.urgency for r in results)
        sentiment_counts = Counter(r.sentiment for r in results)
        project_counts = Counter(r.project for r in results)
        action_counts = Counter(r.action for r in results)

        return {
            "total": len(signals),
            "sources": list(source_counts.keys()),
            "source_breakdown": dict(source_counts),
            "urgency": dict(urgency_counts),
            "sentiment": dict(sentiment_counts),
            "projects": dict(project_counts),
            "actions": dict(action_counts),
        }

    def _generate_summary(
        self, stats: dict[str, Any], sections: dict[str, list]
    ) -> str:
        """Generate an executive summary paragraph."""
        total = stats.get("total", 0)
        urgency = stats.get("urgency", {})
        critical = urgency.get("critical", 0)
        high = urgency.get("high", 0)

        parts: list[str] = []
        parts.append(
            f"**{total} signals** collected from "
            f"{len(stats.get('sources', []))} sources."
        )

        if critical > 0:
            parts.append(f"🔴 **{critical} critical** items need immediate attention.")
        if high > 0:
            parts.append(f"🟠 **{high} high-urgency** items flagged.")

        # Top project by signal count
        projects = stats.get("projects", {})
        if projects:
            top_project = max(projects, key=lambda k: projects[k])
            parts.append(
                f"Busiest area: **{top_project}** ({projects[top_project]} signals)."
            )

        # Sentiment summary
        sentiment = stats.get("sentiment", {})
        frustrated = sentiment.get("frustrated", 0)
        if frustrated > 0:
            parts.append(f"⚠️ {frustrated} frustrated signals detected — check these first.")

        return " ".join(parts)
