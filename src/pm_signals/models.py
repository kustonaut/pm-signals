"""Data models for PM Signals.

All signal, brief, and triage result structures live here as
plain dataclasses — no external dependencies required.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Signal:
    """A single signal from any source.

    Attributes:
        id: Unique identifier (source-specific).
        source: Where the signal came from (github, rss, file, etc.).
        title: Short headline.
        body: Full text content.
        url: Link to the original source (optional).
        author: Who created/sent the signal (optional).
        timestamp: When the signal was created.
        metadata: Arbitrary key-value pairs from the fetcher.
    """

    id: str
    source: str
    title: str
    body: str
    url: str = ""
    author: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-friendly dict."""
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Signal":
        """Deserialize from a dict."""
        data = dict(data)
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)

    def text(self) -> str:
        """Combined searchable text (title + body)."""
        return f"{self.title} {self.body}"


@dataclass
class TriageResult:
    """Result of triaging a single signal.

    Attributes:
        signal_id: Reference back to the signal.
        project: Which project area this routes to.
        project_confidence: 0.0-1.0 routing confidence.
        sentiment: frustrated | negative | neutral | constructive | positive.
        sentiment_score: -1.0 to 1.0 sentiment magnitude.
        urgency: critical | high | medium | low.
        urgency_score: 0.0-1.0 urgency magnitude.
        action: investigate | respond | route | track | fix.
        tags: Additional classification tags.
    """

    signal_id: str
    project: str = "unclassified"
    project_confidence: float = 0.0
    sentiment: str = "neutral"
    sentiment_score: float = 0.0
    urgency: str = "low"
    urgency_score: float = 0.0
    action: str = "track"
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-friendly dict."""
        return asdict(self)


@dataclass
class DailyBrief:
    """A generated daily intelligence brief.

    Attributes:
        date: Brief date.
        signals: All signals included.
        triage_results: All triage decisions.
        summary: Generated summary text.
        sections: Brief organized by project area.
        stats: Aggregate statistics.
    """

    date: str
    signals: list[Signal] = field(default_factory=list)
    triage_results: list[TriageResult] = field(default_factory=list)
    summary: str = ""
    sections: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    stats: dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        """Render the brief as Markdown."""
        lines: list[str] = []
        lines.append(f"# Daily Brief — {self.date}")
        lines.append("")

        if self.summary:
            lines.append("## Summary")
            lines.append(self.summary)
            lines.append("")

        # Stats bar
        if self.stats:
            lines.append("## Overview")
            lines.append(f"- **Total signals:** {self.stats.get('total', 0)}")
            lines.append(f"- **Sources:** {', '.join(self.stats.get('sources', []))}")

            urgency = self.stats.get("urgency", {})
            if urgency:
                parts = [f"{k}: {v}" for k, v in urgency.items() if v > 0]
                lines.append(f"- **Urgency:** {', '.join(parts)}")

            sentiment = self.stats.get("sentiment", {})
            if sentiment:
                parts = [f"{k}: {v}" for k, v in sentiment.items() if v > 0]
                lines.append(f"- **Sentiment:** {', '.join(parts)}")
            lines.append("")

        # Sections by project
        for project, items in self.sections.items():
            lines.append(f"## {project}")
            for item in items:
                urgency_badge = item.get("urgency", "low")
                emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(
                    urgency_badge, "⚪"
                )
                lines.append(f"- {emoji} **{item.get('title', 'Untitled')}**")
                if item.get("source"):
                    lines.append(f"  - Source: {item['source']}")
                if item.get("action"):
                    lines.append(f"  - Action: {item['action']}")
                if item.get("sentiment") and item["sentiment"] != "neutral":
                    lines.append(f"  - Sentiment: {item['sentiment']}")
            lines.append("")

        return "\n".join(lines)

    def to_json(self) -> str:
        """Serialize the full brief to JSON."""
        data = {
            "date": self.date,
            "summary": self.summary,
            "sections": self.sections,
            "stats": self.stats,
            "signals": [s.to_dict() for s in self.signals],
            "triage_results": [t.to_dict() for t in self.triage_results],
        }
        return json.dumps(data, indent=2)
