"""Urgency scorer — weighted 4-tier urgency classification.

Scores signals as critical, high, medium, or low urgency using
layered keyword patterns with weighted signals.  No external
dependencies required.

Ported and generalized from a production triage pipeline
processing 6,000+ GitHub issues.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class UrgencyResult:
    """Urgency scoring result."""

    level: str  # critical | high | medium | low
    score: float  # 0.0 to 1.0
    matched_signals: list[str]

    @property
    def emoji(self) -> str:
        """Emoji representation of urgency level."""
        return {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
        }.get(self.level, "⚪")


class UrgencyScorer:
    """Weighted urgency scoring with 4-tier signal architecture.

    Scans text for urgency indicators at four severity levels,
    computing a composite score that determines the final
    urgency classification.

    Example::

        scorer = UrgencyScorer()
        result = scorer.score("Production database is down! Data loss reported.")
        print(result.level)  # "critical"
        print(result.score)  # 0.95
    """

    _CRITICAL_SIGNALS: list[tuple[str, float]] = [
        (r"\b(security|vulnerability|CVE-\d+)\b", 1.0),
        (r"\b(data loss|data corruption)\b", 0.95),
        (r"\b(production down|service down)\b", 0.9),
        (r"\b(outage|site down)\b", 0.85),
        (r"\b(P0|Sev[- ]?0|Sev[- ]?1)\b", 0.9),
        (r"\b(incident|emergency)\b", 0.8),
    ]

    _HIGH_SIGNALS: list[tuple[str, float]] = [
        (r"\b(P1|Sev[- ]?2)\b", 0.7),
        (r"\b(escalation|escalated)\b", 0.65),
        (r"\b(urgent|urgently)\b", 0.7),
        (r"\b(regression|regressed)\b", 0.65),
        (r"\b(blocking|blocker)\b", 0.6),
        (r"\b(ASAP|immediately)\b", 0.65),
        (r"\b(customer[- ]impact)\b", 0.7),
        (r"\b(OOM|out of memory)\b", 0.6),
    ]

    _MEDIUM_SIGNALS: list[tuple[str, float]] = [
        (r"\b(P2|Sev[- ]?3)\b", 0.4),
        (r"\b(bug|defect)\b", 0.3),
        (r"\b(performance|slow|latency)\b", 0.35),
        (r"\b(feature request|enhancement)\b", 0.25),
        (r"\b(compliance|audit)\b", 0.4),
        (r"\b(workaround available)\b", 0.2),
    ]

    _LOW_SIGNALS: list[tuple[str, float]] = [
        (r"\b(P3|Sev[- ]?4)\b", 0.15),
        (r"\b(question|documentation)\b", 0.1),
        (r"\b(minor|cosmetic|typo)\b", 0.1),
        (r"\b(nice to have|low priority)\b", 0.1),
        (r"\b(suggestion|idea)\b", 0.1),
    ]

    def score(self, text: str) -> UrgencyResult:
        """Score the urgency of a text signal.

        Args:
            text: The text to analyze for urgency signals.

        Returns:
            UrgencyResult with level, score, and matched signals.
        """
        text_lower = text.lower()
        max_score = 0.0
        matched: list[str] = []

        for pattern, weight in self._CRITICAL_SIGNALS:
            if re.search(pattern, text_lower):
                max_score = max(max_score, weight)
                matched.append(f"critical:{pattern}")

        for pattern, weight in self._HIGH_SIGNALS:
            if re.search(pattern, text_lower):
                max_score = max(max_score, weight)
                matched.append(f"high:{pattern}")

        for pattern, weight in self._MEDIUM_SIGNALS:
            if re.search(pattern, text_lower):
                max_score = max(max_score, 0.3 + weight * 0.3)
                matched.append(f"medium:{pattern}")

        for pattern, weight in self._LOW_SIGNALS:
            if re.search(pattern, text_lower):
                if max_score == 0.0:
                    max_score = weight
                matched.append(f"low:{pattern}")

        # Classify based on score
        if max_score >= 0.8:
            level = "critical"
        elif max_score >= 0.55:
            level = "high"
        elif max_score >= 0.25:
            level = "medium"
        else:
            level = "low"

        return UrgencyResult(
            level=level,
            score=round(max_score, 3),
            matched_signals=matched,
        )
