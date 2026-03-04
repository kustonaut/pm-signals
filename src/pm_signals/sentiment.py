"""Sentiment analyzer — detect user sentiment from signal text.

Uses weighted keyword matching to classify text into five
categories: frustrated, negative, neutral, constructive, positive.
No external dependencies or LLM calls required.

Ported and generalized from a production triage pipeline
processing 176+ signals/month.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SentimentResult:
    """Sentiment analysis result."""

    label: str  # frustrated | negative | neutral | constructive | positive
    score: float  # -1.0 to 1.0

    @property
    def emoji(self) -> str:
        """Emoji representation of the sentiment."""
        return {
            "frustrated": "😤",
            "negative": "😟",
            "neutral": "😐",
            "constructive": "💡",
            "positive": "😊",
        }.get(self.label, "❓")


class SentimentAnalyzer:
    """Weighted keyword-based sentiment analyzer.

    Detects sentiment without external APIs — uses pattern matching
    with weighted signals for each sentiment category.

    Example::

        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("This bug is really frustrating!")
        print(result.label)   # "frustrated"
        print(result.score)   # -0.8
    """

    _FRUSTRATED_SIGNALS: list[tuple[str, float]] = [
        (r"\b(frustrated|frustrating)\b", 0.8),
        (r"\b(broken|still broken|keeps breaking)\b", 0.7),
        (r"\b(unacceptable|ridiculous)\b", 0.9),
        (r"\b(wast(?:e|ed|ing) time)\b", 0.7),
        (r"\b(no response|ignored|no update)\b", 0.6),
        (r"\b(blocker|blocking us|blocked)\b", 0.6),
        (r"!!+", 0.5),
        (r"\b(terrible|horrible|awful)\b", 0.8),
    ]

    _NEGATIVE_SIGNALS: list[tuple[str, float]] = [
        (r"\b(bug|issue|problem|fail(?:ed)?|error)\b", 0.3),
        (r"\b(slow|poor|bad|wrong)\b", 0.4),
        (r"\b(cannot|can't|doesn't work|not working)\b", 0.5),
        (r"\b(crash(?:es|ed|ing)?)\b", 0.5),
        (r"\b(timeout|timed? out)\b", 0.4),
        (r"\b(missing|broken)\b", 0.3),
    ]

    _POSITIVE_SIGNALS: list[tuple[str, float]] = [
        (r"\b(thanks|thank you|great|awesome)\b", 0.4),
        (r"\b(works|working|resolved|fixed)\b", 0.3),
        (r"\b(love|excellent|perfect)\b", 0.5),
        (r"\b(helpful|useful|appreciate)\b", 0.4),
        (r"\b(well done|nice work|good job)\b", 0.5),
    ]

    _CONSTRUCTIVE_SIGNALS: list[tuple[str, float]] = [
        (r"\b(suggest(?:ion)?|proposal|idea)\b", 0.4),
        (r"\b(would be nice|feature request|enhancement)\b", 0.3),
        (r"\b(workaround|alternative)\b", 0.3),
        (r"\b(could we|what if|how about)\b", 0.3),
        (r"\b(improvement|improve)\b", 0.3),
    ]

    def analyze(self, text: str) -> SentimentResult:
        """Analyze text and return sentiment label + score.

        Args:
            text: The text to analyze.

        Returns:
            SentimentResult with label and score (-1.0 to 1.0).
        """
        text_lower = text.lower()
        score = 0.0

        for pattern, weight in self._FRUSTRATED_SIGNALS:
            if re.search(pattern, text_lower):
                score -= weight

        for pattern, weight in self._NEGATIVE_SIGNALS:
            if re.search(pattern, text_lower):
                score -= weight

        for pattern, weight in self._POSITIVE_SIGNALS:
            if re.search(pattern, text_lower):
                score += weight

        for pattern, weight in self._CONSTRUCTIVE_SIGNALS:
            if re.search(pattern, text_lower):
                score += weight * 0.5  # Constructive leans slightly positive

        # Clamp to [-1, 1]
        score = max(-1.0, min(1.0, score))

        # Classify
        if score <= -0.6:
            label = "frustrated"
        elif score <= -0.2:
            label = "negative"
        elif score >= 0.4:
            label = "positive"
        elif score >= 0.15:
            label = "constructive"
        else:
            label = "neutral"

        return SentimentResult(label=label, score=round(score, 3))
