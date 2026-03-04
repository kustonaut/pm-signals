"""File watcher fetcher — scan directories for new signal files.

Watches configured directories for new or modified ``.md``,
``.txt``, and ``.json`` files, turning each into a signal.
Useful as a landing zone — drop files and they get triaged.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pm_signals.fetchers.base import BaseFetcher
from pm_signals.models import Signal


class FileWatcherFetcher(BaseFetcher):
    """Fetch signals from files appearing in watched directories."""

    name = "file_watcher"

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        super().__init__(settings)
        self._watch_dirs: list[str] = self.settings.get("watch_dirs", [])
        self._extensions: list[str] = self.settings.get(
            "extensions", [".md", ".txt", ".json"]
        )

    def fetch(self) -> list[Signal]:
        """Scan watch directories and return file-based signals."""
        signals: list[Signal] = []

        for dir_path in self._watch_dirs:
            p = Path(dir_path)
            if not p.is_dir():
                continue

            for ext in self._extensions:
                for filepath in p.glob(f"*{ext}"):
                    if filepath.is_file():
                        signals.append(self._file_to_signal(filepath))

        return signals

    def _file_to_signal(self, filepath: Path) -> Signal:
        """Convert a single file into a Signal."""
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            content = ""

        stat = filepath.stat()
        modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)

        return Signal(
            id=f"file-{filepath.name}-{int(stat.st_mtime)}",
            source="file",
            title=filepath.stem.replace("_", " ").replace("-", " ").title(),
            body=content[:5000],  # Cap at 5KB
            url=str(filepath),
            timestamp=modified,
            metadata={
                "filename": filepath.name,
                "extension": filepath.suffix,
                "size_bytes": stat.st_size,
                "dir": str(filepath.parent),
            },
        )
