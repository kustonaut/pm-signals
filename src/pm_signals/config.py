"""Configuration loader for PM Signals.

Reads a YAML config file with project areas, routing keywords,
fetcher settings, and pipeline options. Falls back to sensible
defaults for everything.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG: dict[str, Any] = {
    "version": 1,
    "output_dir": "./signals_output",
    "projects": {
        "Frontend": {
            "keywords": [
                "react",
                "vue",
                "angular",
                "css",
                "html",
                "UI",
                "UX",
                "component",
                "layout",
                "responsive",
                "accessibility",
                "a11y",
            ],
            "color": "#61DAFB",
        },
        "Backend": {
            "keywords": [
                "api",
                "server",
                "database",
                "endpoint",
                "REST",
                "GraphQL",
                "authentication",
                "middleware",
                "cache",
                "queue",
                "worker",
            ],
            "color": "#68D391",
        },
        "Infrastructure": {
            "keywords": [
                "deploy",
                "CI/CD",
                "docker",
                "kubernetes",
                "terraform",
                "monitoring",
                "alert",
                "scaling",
                "load balancer",
                "DNS",
            ],
            "color": "#F6AD55",
        },
        "Data": {
            "keywords": [
                "pipeline",
                "ETL",
                "analytics",
                "dashboard",
                "metrics",
                "telemetry",
                "warehouse",
                "BigQuery",
                "Snowflake",
                "dbt",
            ],
            "color": "#B794F4",
        },
    },
    "fetchers": {
        "github": {
            "enabled": False,
            "repos": [],
            "token_env": "GITHUB_TOKEN",
        },
        "rss": {
            "enabled": False,
            "feeds": [],
        },
        "file_watcher": {
            "enabled": False,
            "watch_dirs": [],
            "extensions": [".md", ".txt", ".json"],
        },
        "sample": {
            "enabled": True,
            "count": 20,
        },
    },
    "pipeline": {
        "schedule": "08:30",
        "retention_days": 14,
        "brief_format": "markdown",
    },
    "llm": {
        "enabled": False,
        "provider": "openai",
        "model": "gpt-4o-mini",
        "temperature": 0.3,
    },
}


@dataclass
class Config:
    """Parsed configuration for PM Signals."""

    version: int = 1
    output_dir: str = "./signals_output"
    projects: dict[str, dict[str, Any]] = field(default_factory=dict)
    fetchers: dict[str, dict[str, Any]] = field(default_factory=dict)
    pipeline: dict[str, Any] = field(default_factory=dict)
    llm: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Config":
        """Load config from a YAML file, falling back to defaults."""
        data = dict(DEFAULT_CONFIG)

        if path is not None:
            p = Path(path)
            if p.exists():
                with open(p) as f:
                    user_data = yaml.safe_load(f) or {}
                # Deep merge: user overrides defaults
                data = _deep_merge(data, user_data)

        return cls(
            version=data.get("version", 1),
            output_dir=data.get("output_dir", "./signals_output"),
            projects=data.get("projects", {}),
            fetchers=data.get("fetchers", {}),
            pipeline=data.get("pipeline", {}),
            llm=data.get("llm", {}),
            raw=data,
        )

    def get_project_keywords(self) -> dict[str, list[str]]:
        """Return {project_name: [keywords]} mapping."""
        return {
            name: info.get("keywords", []) for name, info in self.projects.items()
        }

    def get_enabled_fetchers(self) -> list[str]:
        """Return names of enabled fetchers."""
        return [
            name
            for name, settings in self.fetchers.items()
            if settings.get("enabled", False)
        ]


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
