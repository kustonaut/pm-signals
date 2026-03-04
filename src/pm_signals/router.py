"""Signal router — classify signals into project areas by keyword matching.

Uses configurable keyword lists per project area with weighted
scoring.  Supports multi-match (a signal can match multiple areas)
with confidence ranking.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from pm_signals.models import Signal


@dataclass
class RouteMatch:
    """A single routing match result."""

    project: str
    confidence: float
    matched_keywords: list[str]


class Router:
    """Keyword-based signal router.

    Args:
        project_keywords: Mapping of ``{project_name: [keywords]}``.

    Example::

        router = Router({
            "Frontend": ["react", "css", "UI", "component"],
            "Backend": ["api", "server", "database", "endpoint"],
        })
        match = router.route(signal)
        print(match.project, match.confidence)
    """

    def __init__(self, project_keywords: dict[str, list[str]]) -> None:
        self._projects = project_keywords
        # Pre-compile patterns for performance
        self._compiled: dict[str, list[re.Pattern[str]]] = {}
        for project, keywords in project_keywords.items():
            self._compiled[project] = [
                re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE) for kw in keywords
            ]

    def route(self, signal: Signal) -> RouteMatch:
        """Route a signal to the best-matching project area.

        Returns the highest-confidence match, or ``"unclassified"``
        if no keywords match.
        """
        matches = self.route_all(signal)
        if matches:
            return matches[0]
        return RouteMatch(project="unclassified", confidence=0.0, matched_keywords=[])

    def route_all(self, signal: Signal) -> list[RouteMatch]:
        """Return all matching project areas, ranked by confidence."""
        text = signal.text()
        results: list[RouteMatch] = []

        # Also check labels in metadata
        labels = signal.metadata.get("labels", [])
        label_text = " ".join(labels) if isinstance(labels, list) else ""
        full_text = f"{text} {label_text}"

        for project, patterns in self._compiled.items():
            matched: list[str] = []
            for i, pattern in enumerate(patterns):
                if pattern.search(full_text):
                    matched.append(self._projects[project][i])

            if matched:
                # Confidence: ratio of matched keywords to total, scaled
                raw = len(matched) / len(patterns)
                confidence = min(1.0, raw * 2.0)  # Boost: 50% match = 100% confidence
                results.append(
                    RouteMatch(
                        project=project,
                        confidence=round(confidence, 3),
                        matched_keywords=matched,
                    )
                )

        # Sort by confidence descending
        results.sort(key=lambda m: m.confidence, reverse=True)
        return results
