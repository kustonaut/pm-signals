"""Triage engine — combines routing, sentiment, and urgency into decisions.

The triage pipeline takes a list of signals and produces a
:class:`TriageResult` for each one by running three classifiers:

1. **Router** — keyword-based project area classification
2. **Sentiment** — frustrated/negative/neutral/constructive/positive
3. **Urgency** — critical/high/medium/low with weighted scoring

Additionally determines the recommended **action** based on
the combination of urgency and signal type.
"""

from __future__ import annotations

import re
from typing import Any

from pm_signals.models import Signal, TriageResult
from pm_signals.router import Router
from pm_signals.sentiment import SentimentAnalyzer
from pm_signals.urgency import UrgencyScorer


# Action classification patterns
_ACTION_PATTERNS: dict[str, list[str]] = {
    "investigate": [
        r"\b(incident|outage|failed|error|crash|timeout)\b",
    ],
    "respond": [
        r"\b(question|ask|how to|help|guidance)\b",
    ],
    "route": [
        r"\b(transfer|wrong team|not our|escalate)\b",
    ],
    "track": [
        r"\b(tracking|monitoring|watch|known issue|by design)\b",
    ],
    "fix": [
        r"\b(bug|regression|broken|patch|hotfix)\b",
    ],
}


class TriageEngine:
    """Full triage pipeline: route → sentiment → urgency → action.

    Args:
        project_keywords: ``{project_name: [keywords]}`` for routing.
            If ``None``, all signals route to ``"unclassified"``.

    Example::

        engine = TriageEngine({
            "Frontend": ["react", "css", "UI"],
            "Backend": ["api", "server", "database"],
        })
        results = engine.triage(signals)
        for result in results:
            print(result.project, result.urgency, result.sentiment)
    """

    def __init__(self, project_keywords: dict[str, list[str]] | None = None) -> None:
        self._router = Router(project_keywords or {})
        self._sentiment = SentimentAnalyzer()
        self._urgency = UrgencyScorer()

    def triage(self, signals: list[Signal]) -> list[TriageResult]:
        """Triage a list of signals.

        Returns one :class:`TriageResult` per signal.
        """
        return [self.triage_one(signal) for signal in signals]

    def triage_one(self, signal: Signal) -> TriageResult:
        """Triage a single signal through the full pipeline."""
        text = signal.text()

        # 1. Route to project area
        route = self._router.route(signal)

        # 2. Sentiment analysis
        sentiment = self._sentiment.analyze(text)

        # 3. Urgency scoring
        urgency = self._urgency.score(text)

        # 4. Action classification
        action = self._classify_action(text, urgency.level)

        # 5. Build tags
        tags = self._build_tags(signal, route.project, urgency.level)

        return TriageResult(
            signal_id=signal.id,
            project=route.project,
            project_confidence=route.confidence,
            sentiment=sentiment.label,
            sentiment_score=sentiment.score,
            urgency=urgency.level,
            urgency_score=urgency.score,
            action=action,
            tags=tags,
        )

    def _classify_action(self, text: str, urgency: str) -> str:
        """Determine recommended action from text patterns + urgency."""
        text_lower = text.lower()

        # Urgency overrides
        if urgency == "critical":
            return "investigate"

        # Pattern matching
        for action, patterns in _ACTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return action

        return "track"

    def _build_tags(self, signal: Signal, project: str, urgency: str) -> list[str]:
        """Build classification tags for the signal."""
        tags: list[str] = []

        if signal.source:
            tags.append(f"source:{signal.source}")
        if project != "unclassified":
            tags.append(f"project:{project}")
        tags.append(f"urgency:{urgency}")

        # Check metadata for extra tags
        labels = signal.metadata.get("labels", [])
        if isinstance(labels, list):
            for label in labels[:5]:
                tags.append(f"label:{label}")

        return tags
