"""RSS feed fetcher — pull signals from RSS/Atom feeds.

Supports any standard RSS or Atom feed.  Optionally requires
the ``feedparser`` package (``pip install pm-signals[rss]``).
Falls back to a minimal built-in XML parser if feedparser is
not installed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from pm_signals.fetchers.base import BaseFetcher
from pm_signals.models import Signal

try:
    import feedparser  # type: ignore[import-untyped]

    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False


class RSSFetcher(BaseFetcher):
    """Fetch signals from RSS/Atom feeds."""

    name = "rss"

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        super().__init__(settings)
        self._feeds: list[str] = self.settings.get("feeds", [])

    def fetch(self) -> list[Signal]:
        """Fetch entries from all configured RSS feeds."""
        signals: list[Signal] = []
        for feed_url in self._feeds:
            signals.extend(self._fetch_feed(feed_url))
        return signals

    def _fetch_feed(self, url: str) -> list[Signal]:
        """Fetch a single RSS feed."""
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
        except requests.RequestException:
            return []

        if HAS_FEEDPARSER:
            return self._parse_with_feedparser(url, resp.text)
        return self._parse_minimal(url, resp.text)

    def _parse_with_feedparser(self, url: str, content: str) -> list[Signal]:
        """Parse using the feedparser library."""
        feed = feedparser.parse(content)
        signals: list[Signal] = []

        for i, entry in enumerate(feed.entries[:30]):
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            if published:
                ts = datetime(*published[:6], tzinfo=timezone.utc)
            else:
                ts = datetime.now(tz=timezone.utc)

            signals.append(
                Signal(
                    id=f"rss-{hash(url)}-{i}",
                    source="rss",
                    title=entry.get("title", "RSS Entry"),
                    body=entry.get("summary", ""),
                    url=entry.get("link", url),
                    author=entry.get("author", ""),
                    timestamp=ts,
                    metadata={
                        "feed_url": url,
                        "feed_title": feed.feed.get("title", ""),
                    },
                )
            )
        return signals

    def _parse_minimal(self, url: str, content: str) -> list[Signal]:
        """Minimal XML parsing fallback (no feedparser)."""
        import re

        signals: list[Signal] = []
        # Extract <item> or <entry> blocks
        items = re.findall(r"<(?:item|entry)>(.*?)</(?:item|entry)>", content, re.DOTALL)

        for i, item in enumerate(items[:30]):
            title = _extract_tag(item, "title")
            desc = _extract_tag(item, "description") or _extract_tag(item, "summary")
            link = _extract_tag(item, "link")

            signals.append(
                Signal(
                    id=f"rss-{hash(url)}-{i}",
                    source="rss",
                    title=title or "RSS Entry",
                    body=desc or "",
                    url=link or url,
                    timestamp=datetime.now(tz=timezone.utc),
                    metadata={"feed_url": url},
                )
            )
        return signals


def _extract_tag(xml: str, tag: str) -> str:
    """Extract text content from an XML tag."""
    import re

    match = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", xml, re.DOTALL)
    if match:
        text = match.group(1).strip()
        # Strip CDATA
        text = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", text, flags=re.DOTALL)
        # Strip HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        return text.strip()
    return ""
