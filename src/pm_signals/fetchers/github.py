"""GitHub fetcher — pull signals from GitHub notifications and issues.

Requires a ``GITHUB_TOKEN`` environment variable (or configure
``token_env`` in settings).  Uses the GitHub REST API to fetch
notifications and recent issues from configured repositories.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import requests

from pm_signals.fetchers.base import BaseFetcher
from pm_signals.models import Signal


class GitHubFetcher(BaseFetcher):
    """Fetch GitHub notifications and recent issues as signals."""

    name = "github"

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        super().__init__(settings)
        token_env = self.settings.get("token_env", "GITHUB_TOKEN")
        self._token = os.environ.get(token_env, "")
        self._repos: list[str] = self.settings.get("repos", [])
        self._headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            self._headers["Authorization"] = f"Bearer {self._token}"

    def fetch(self) -> list[Signal]:
        """Fetch notifications + recent issues from configured repos."""
        signals: list[Signal] = []

        # Fetch notifications
        signals.extend(self._fetch_notifications())

        # Fetch recent issues from each repo
        for repo in self._repos:
            signals.extend(self._fetch_issues(repo))

        return signals

    def _fetch_notifications(self) -> list[Signal]:
        """Fetch unread GitHub notifications."""
        if not self._token:
            return []

        try:
            resp = requests.get(
                "https://api.github.com/notifications",
                headers=self._headers,
                params={"participating": "true", "per_page": 50},
                timeout=30,
            )
            resp.raise_for_status()
        except requests.RequestException:
            return []

        signals: list[Signal] = []
        for notif in resp.json():
            subject = notif.get("subject", {})
            signals.append(
                Signal(
                    id=f"gh-notif-{notif['id']}",
                    source="github",
                    title=subject.get("title", "GitHub Notification"),
                    body=f"[{notif.get('reason', 'unknown')}] {subject.get('type', '')}",
                    url=subject.get("url", ""),
                    author=notif.get("repository", {}).get("full_name", ""),
                    timestamp=_parse_gh_time(notif.get("updated_at", "")),
                    metadata={
                        "type": "notification",
                        "reason": notif.get("reason"),
                        "repo": notif.get("repository", {}).get("full_name"),
                    },
                )
            )
        return signals

    def _fetch_issues(self, repo: str) -> list[Signal]:
        """Fetch recently updated issues from a repository."""
        try:
            resp = requests.get(
                f"https://api.github.com/repos/{repo}/issues",
                headers=self._headers,
                params={"state": "open", "sort": "updated", "per_page": 30},
                timeout=30,
            )
            resp.raise_for_status()
        except requests.RequestException:
            return []

        signals: list[Signal] = []
        for issue in resp.json():
            if issue.get("pull_request"):
                continue  # Skip PRs
            labels = [l.get("name", "") for l in issue.get("labels", [])]
            signals.append(
                Signal(
                    id=f"gh-issue-{repo}-{issue['number']}",
                    source="github",
                    title=issue.get("title", ""),
                    body=issue.get("body", "") or "",
                    url=issue.get("html_url", ""),
                    author=issue.get("user", {}).get("login", ""),
                    timestamp=_parse_gh_time(issue.get("updated_at", "")),
                    metadata={
                        "type": "issue",
                        "repo": repo,
                        "number": issue["number"],
                        "labels": labels,
                        "state": issue.get("state"),
                        "comments": issue.get("comments", 0),
                    },
                )
            )
        return signals


def _parse_gh_time(ts: str) -> datetime:
    """Parse a GitHub API timestamp."""
    if not ts:
        return datetime.now(tz=timezone.utc)
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(tz=timezone.utc)
