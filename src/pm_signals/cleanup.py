"""Cleanup — archive old signals and output files.

Moves files older than a configurable number of days into
an ``archive/`` subdirectory, and optionally deletes files
older than a second threshold.
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


def cleanup(
    output_dir: str | Path,
    archive_days: int = 14,
    delete_days: int = 60,
    dry_run: bool = False,
) -> dict[str, int]:
    """Archive and clean old signal output files.

    Args:
        output_dir: Path to the ``signals_output/`` directory.
        archive_days: Files older than this are moved to ``archive/``.
        delete_days: Archived files older than this are deleted.
        dry_run: If True, log what would happen but don't move/delete.

    Returns:
        Counts: ``{"archived": N, "deleted": M, "skipped": S}``.
    """
    output_path = Path(output_dir)
    archive_path = output_path / "archive"
    now = datetime.now()
    archive_cutoff = now - timedelta(days=archive_days)
    delete_cutoff = now - timedelta(days=delete_days)

    counts = {"archived": 0, "deleted": 0, "skipped": 0}

    if not output_path.exists():
        logger.info(f"Output directory does not exist: {output_path}")
        return counts

    # Phase 1: Archive old files
    for file in output_path.iterdir():
        if file.is_dir() or file.name.startswith("."):
            continue

        mtime = datetime.fromtimestamp(file.stat().st_mtime)
        if mtime < archive_cutoff:
            if dry_run:
                logger.info(f"  [dry-run] Would archive: {file.name}")
                counts["archived"] += 1
            else:
                archive_path.mkdir(exist_ok=True)
                dest = archive_path / file.name
                shutil.move(str(file), str(dest))
                logger.info(f"  Archived: {file.name}")
                counts["archived"] += 1
        else:
            counts["skipped"] += 1

    # Phase 2: Delete very old archived files
    if archive_path.exists():
        for file in archive_path.iterdir():
            if file.is_dir():
                continue

            mtime = datetime.fromtimestamp(file.stat().st_mtime)
            if mtime < delete_cutoff:
                if dry_run:
                    logger.info(f"  [dry-run] Would delete: archive/{file.name}")
                    counts["deleted"] += 1
                else:
                    file.unlink()
                    logger.info(f"  Deleted: archive/{file.name}")
                    counts["deleted"] += 1

    return counts
