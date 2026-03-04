"""Sample data fetcher — built-in signals for demo and testing.

Generates realistic signals from fictional projects so the full
pipeline can be demonstrated with zero configuration and no
external dependencies.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from pm_signals.fetchers.base import BaseFetcher
from pm_signals.models import Signal

# Realistic sample signals — generic, no PII
_SAMPLE_SIGNALS: list[dict[str, Any]] = [
    {
        "source": "github",
        "title": "Dashboard charts fail to render on mobile viewports",
        "body": "The analytics dashboard charts overflow on screens < 768px. "
        "CSS grid layout breaks and bar charts overlap the sidebar. "
        "This is blocking our mobile launch. Users are frustrated.",
        "author": "dev-sarah",
        "metadata": {"type": "issue", "repo": "acme/web-app", "labels": ["bug", "frontend"]},
    },
    {
        "source": "github",
        "title": "API rate limiting returns 500 instead of 429",
        "body": "When users exceed the rate limit, the server returns HTTP 500 "
        "instead of 429 Too Many Requests. This causes client retry storms "
        "that make the problem worse. Critical fix needed.",
        "author": "dev-marco",
        "metadata": {"type": "issue", "repo": "acme/api-server", "labels": ["bug", "backend", "critical"]},
    },
    {
        "source": "github",
        "title": "Feature request: export dashboard data as CSV",
        "body": "Multiple users have asked for CSV export from the analytics dashboard. "
        "Would be great to have a one-click download button. This would help "
        "our enterprise customers who need data for compliance reports.",
        "author": "pm-alex",
        "metadata": {"type": "issue", "repo": "acme/web-app", "labels": ["enhancement", "frontend"]},
    },
    {
        "source": "github",
        "title": "Database connection pool exhaustion under load",
        "body": "During peak hours (9-11 AM), we're seeing connection pool exhaustion. "
        "PostgreSQL max_connections=100 is not enough. Queries start timing out "
        "after 30s. Need to implement connection pooling with PgBouncer or similar.",
        "author": "dev-priya",
        "metadata": {"type": "issue", "repo": "acme/api-server", "labels": ["bug", "infrastructure", "performance"]},
    },
    {
        "source": "rss",
        "title": "New React 20 features for server components",
        "body": "React 20 introduces improved server component streaming and partial "
        "hydration. This could significantly improve our page load times. "
        "Worth investigating for the frontend rewrite planned next quarter.",
        "author": "",
        "metadata": {"feed_url": "https://reactblog.example.com/feed"},
    },
    {
        "source": "github",
        "title": "CI/CD pipeline fails intermittently on ARM64 runners",
        "body": "About 15% of our GitHub Actions runs fail on arm64 runners with "
        "segfaults in the test suite. Works fine on x86. Might be a "
        "race condition in our concurrent test setup.",
        "author": "dev-chen",
        "metadata": {"type": "issue", "repo": "acme/infra", "labels": ["bug", "ci-cd"]},
    },
    {
        "source": "file",
        "title": "Q1 Customer Feedback Summary",
        "body": "Top 3 themes from Q1 feedback: (1) Dashboard performance — 34% of "
        "complaints mention slow load times. (2) Missing CSV export — 22% of "
        "enterprise customers need this for compliance. (3) Mobile experience — "
        "18% report broken layouts on tablets and phones.",
        "author": "pm-alex",
        "metadata": {"filename": "q1_feedback_summary.md"},
    },
    {
        "source": "github",
        "title": "Kubernetes pod autoscaling not triggering on memory pressure",
        "body": "HPA is configured for CPU but not memory. During data processing "
        "jobs, pods hit OOM kills before scaling kicks in. Need to add "
        "memory-based autoscaling to the HPA configuration.",
        "author": "ops-taylor",
        "metadata": {"type": "issue", "repo": "acme/infra", "labels": ["infrastructure", "kubernetes"]},
    },
    {
        "source": "rss",
        "title": "PostgreSQL 17 improves JSON query performance by 3x",
        "body": "PostgreSQL 17 brings massive improvements to JSONB query performance "
        "with new index types. Our JSON-heavy analytics queries could benefit. "
        "Upgrade path looks straightforward from PG 15.",
        "author": "",
        "metadata": {"feed_url": "https://pgblog.example.com/feed"},
    },
    {
        "source": "github",
        "title": "Data pipeline silently drops records with null timestamps",
        "body": "The ETL pipeline discards any record where `created_at` is null "
        "instead of using a fallback. This has been silently losing about 3% "
        "of our event data for the past month. We need a fix ASAP.",
        "author": "data-jamie",
        "metadata": {"type": "issue", "repo": "acme/data-pipeline", "labels": ["bug", "data", "critical"]},
    },
    {
        "source": "github",
        "title": "Add Terraform state locking with DynamoDB",
        "body": "We had a near-miss where two engineers ran terraform apply "
        "simultaneously and corrupted the state file. Need to add "
        "DynamoDB-based state locking before this causes an outage.",
        "author": "ops-taylor",
        "metadata": {"type": "issue", "repo": "acme/infra", "labels": ["infrastructure", "terraform"]},
    },
    {
        "source": "github",
        "title": "Search API returns stale results after index rebuild",
        "body": "After reindexing, search results are stale for 5-10 minutes. "
        "The cache invalidation logic doesn't account for full rebuilds. "
        "Users are complaining about searching for items that don't exist.",
        "author": "dev-marco",
        "metadata": {"type": "issue", "repo": "acme/api-server", "labels": ["bug", "backend", "cache"]},
    },
    {
        "source": "file",
        "title": "Partner Integration Requirements - DataFlow Inc",
        "body": "DataFlow Inc needs: (1) Webhook delivery guarantees with retry. "
        "(2) OAuth 2.0 client credentials flow. (3) Rate limit of 10k req/min. "
        "(4) CSV bulk import API. Timeline: needs to be ready by end of Q2.",
        "author": "pm-alex",
        "metadata": {"filename": "dataflow_integration_requirements.md"},
    },
    {
        "source": "github",
        "title": "Accessibility: screen reader can't navigate data tables",
        "body": "Our data tables lack proper ARIA attributes. Screen readers "
        "can't navigate columns or understand sorting. This blocks sale "
        "to government agencies that require WCAG 2.1 AA compliance.",
        "author": "dev-sarah",
        "metadata": {"type": "issue", "repo": "acme/web-app", "labels": ["accessibility", "frontend", "compliance"]},
    },
    {
        "source": "github",
        "title": "Grafana dashboards showing gaps in metrics collection",
        "body": "Intermittent 2-3 minute gaps in the Grafana time series. "
        "Likely caused by the Prometheus scrape target going down during "
        "rolling deployments. Need to add scrape continuity during deploys.",
        "author": "ops-taylor",
        "metadata": {"type": "issue", "repo": "acme/infra", "labels": ["monitoring", "infrastructure"]},
    },
    {
        "source": "rss",
        "title": "OWASP Top 10 2026: API security risks update",
        "body": "OWASP released their 2026 Top 10 for API security. New entries "
        "include AI-assisted injection attacks and LLM-based SSRF. Worth "
        "reviewing our API security posture against the updated list.",
        "author": "",
        "metadata": {"feed_url": "https://security.example.com/feed"},
    },
    {
        "source": "github",
        "title": "Feature: real-time collaboration on dashboards",
        "body": "Multiple users should be able to edit dashboard layouts "
        "simultaneously. Similar to Google Docs but for dashboard config. "
        "This is the #1 feature request from enterprise customers.",
        "author": "pm-alex",
        "metadata": {"type": "issue", "repo": "acme/web-app", "labels": ["enhancement", "frontend"]},
    },
    {
        "source": "github",
        "title": "GraphQL N+1 query problem in user profile endpoint",
        "body": "The /api/users/:id endpoint makes 47 separate database queries "
        "for a single profile page load. DataLoader is not configured for "
        "the nested resolvers. Response time is 2.3s, should be <200ms.",
        "author": "dev-priya",
        "metadata": {"type": "issue", "repo": "acme/api-server", "labels": ["performance", "backend", "graphql"]},
    },
    {
        "source": "file",
        "title": "Sprint Retrospective Notes",
        "body": "Start: better PR review turnaround, automated regression tests. "
        "Stop: deploying on Fridays, skipping staging env. "
        "Continue: daily standups, pair programming on complex features. "
        "Top concern: deployment velocity is slowing — need CI optimization.",
        "author": "team-lead",
        "metadata": {"filename": "sprint_retro_notes.md"},
    },
    {
        "source": "github",
        "title": "ETL job OOM crash processing large customer dataset",
        "body": "Customer 'BigCorp' has 50M records. Our ETL job tries to load "
        "everything into memory at once. Need to implement streaming/chunked "
        "processing. This has crashed 3 times this week.",
        "author": "data-jamie",
        "metadata": {"type": "issue", "repo": "acme/data-pipeline", "labels": ["bug", "data", "performance"]},
    },
]


class SampleFetcher(BaseFetcher):
    """Generate sample signals for demo and testing purposes.

    This fetcher requires no configuration — it produces realistic
    signals from fictional projects so the full pipeline works
    out of the box.
    """

    name = "sample"

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        super().__init__(settings)
        self._count = min(self.settings.get("count", 20), len(_SAMPLE_SIGNALS))

    def fetch(self) -> list[Signal]:
        """Return built-in sample signals."""
        now = datetime.now(tz=timezone.utc)
        signals: list[Signal] = []

        for i, data in enumerate(_SAMPLE_SIGNALS[: self._count]):
            signals.append(
                Signal(
                    id=f"sample-{i + 1:03d}",
                    source=data["source"],
                    title=data["title"],
                    body=data["body"],
                    author=data.get("author", ""),
                    # Spread signals across last 24 hours
                    timestamp=now - timedelta(hours=24 - i),
                    metadata=data.get("metadata", {}),
                )
            )

        return signals
