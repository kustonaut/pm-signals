# pm-signals

**Multi-source signal intelligence for product managers.**

[![PyPI](https://img.shields.io/pypi/v/pm-signals)](https://pypi.org/project/pm-signals/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)

Fetch signals from GitHub, RSS feeds, file drops, and more — then classify, score urgency, analyze sentiment, and generate a daily intelligence brief.  All from the command line, zero external APIs required.

> **Try the [Interactive Demo](https://kustonaut.github.io/pm-signals/)** — runs entirely in your browser.

---

## Why pm-signals?

Product managers drown in noise — GitHub notifications, RSS feeds, Slack threads, file drops.  `pm-signals` aggregates these into one pipeline:

```
📡 Fetch → 🗂️ Route → 💬 Sentiment → 🚨 Urgency → 📋 Brief
```

**What you get:**
- **Unified signal feed** from any source (GitHub, RSS, files, custom)
- **Automatic project routing** with configurable keyword matching
- **Sentiment analysis** (frustrated → positive, no LLM needed)
- **4-tier urgency scoring** (critical/high/medium/low)
- **Daily intelligence brief** in Markdown — ready for your team
- **Pluggable architecture** — add your own fetchers in minutes

---

## Quick Start

```bash
# Install
pip install pm-signals

# Run with built-in sample data (zero config)
pm-signals demo

# Run the full pipeline with your config
pm-signals pipeline -c config.yaml
```

### 30-Second Example

```python
from pm_signals.fetchers.sample import SampleFetcher
from pm_signals.triage import TriageEngine
from pm_signals.brief import BriefGenerator

# 1. Fetch sample signals
signals = SampleFetcher().fetch()

# 2. Triage all signals
engine = TriageEngine({
    "Frontend": ["react", "css", "UI", "dashboard"],
    "Backend": ["api", "server", "database", "endpoint"],
    "Infrastructure": ["deploy", "CI/CD", "docker", "kubernetes"],
    "Data": ["pipeline", "ETL", "analytics", "warehouse"],
})
results = engine.triage(signals)

# 3. Generate a daily brief
brief = BriefGenerator().generate(signals, results)
print(brief.to_markdown())
```

---

## Installation

```bash
# Core (no extra dependencies)
pip install pm-signals

# With RSS feed support
pip install pm-signals[rss]

# With optional LLM-powered summaries
pip install pm-signals[llm]

# Development
pip install pm-signals[dev]
```

**Requirements:** Python 3.10+

---

## Configuration

Create a `config.yaml` (or copy [`config.sample.yaml`](config.sample.yaml)):

```yaml
projects:
  Frontend:
    keywords: [react, vue, css, UI, component, dashboard]
  Backend:
    keywords: [api, server, database, endpoint, auth]
  Infrastructure:
    keywords: [deploy, CI/CD, docker, kubernetes, terraform]
  Data:
    keywords: [pipeline, ETL, analytics, warehouse]

fetchers:
  github:
    enabled: true
    repos: ["your-org/your-repo"]
  rss:
    enabled: true
    feeds:
      - https://blog.example.com/feed.xml
  sample:
    enabled: false
```

Set `GITHUB_TOKEN` for GitHub fetching:

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `pm-signals pipeline` | Full pipeline: fetch → triage → brief |
| `pm-signals demo` | Run with built-in sample data |
| `pm-signals fetch` | Fetch signals from configured sources |
| `pm-signals cleanup` | Archive old output files |
| `pm-signals stats` | Show statistics from latest run |

**Global options:**
- `-c, --config PATH` — Config YAML file
- `-o, --output DIR` — Output directory (default: `signals_output/`)
- `-v, --verbose` — Debug logging

---

## Architecture

```
┌─────────────┐     ┌──────────┐     ┌──────────────┐     ┌────────────┐     ┌──────────┐
│  Fetchers   │────▶│  Router  │────▶│  Sentiment   │────▶│  Urgency   │────▶│  Brief   │
│             │     │          │     │  Analyzer    │     │  Scorer    │     │Generator │
│ • GitHub    │     │ keyword  │     │              │     │            │     │          │
│ • RSS       │     │ matching │     │ frustrated   │     │ critical   │     │ Markdown │
│ • Files     │     │ per      │     │ negative     │     │ high       │     │ JSON     │
│ • Sample    │     │ project  │     │ neutral      │     │ medium     │     │ JSONL    │
│ • Custom    │     │ area     │     │ constructive │     │ low        │     │          │
│             │     │          │     │ positive     │     │            │     │          │
└─────────────┘     └──────────┘     └──────────────┘     └────────────┘     └──────────┘
```

### Pluggable Fetchers

Every fetcher extends `BaseFetcher`:

```python
from pm_signals.fetchers.base import BaseFetcher
from pm_signals.models import Signal

class SlackFetcher(BaseFetcher):
    def fetch(self) -> list[Signal]:
        # Your logic here
        return [Signal(id="...", source="slack", title="...", body="...")]
```

### Sentiment Analysis

Weighted keyword matching across five categories — no API calls needed:

| Category | Examples | Score Range |
|----------|----------|-------------|
| Frustrated | "broken", "unacceptable", "wasting time" | -0.6 to -1.0 |
| Negative | "bug", "error", "not working" | -0.2 to -0.6 |
| Neutral | (no strong signals) | -0.2 to 0.15 |
| Constructive | "suggestion", "feature request", "improvement" | 0.15 to 0.4 |
| Positive | "great", "love", "excellent" | 0.4 to 1.0 |

### Urgency Scoring

Four-tier classification with weighted signal patterns:

| Level | Triggers | Score |
|-------|----------|-------|
| 🔴 Critical | security, data loss, outage, P0/Sev0 | 0.8 – 1.0 |
| 🟠 High | blocking, regression, urgent, P1 | 0.55 – 0.8 |
| 🟡 Medium | bug, performance, P2, feature request | 0.25 – 0.55 |
| 🟢 Low | question, minor, documentation | 0 – 0.25 |

---

## Output

The pipeline writes three files per run:

- `signals_output/brief_YYYY-MM-DD.md` — Markdown intelligence brief
- `signals_output/signals_YYYY-MM-DD.json` — Full signal + triage data
- `signals_output/triage_YYYY-MM-DD.jsonl` — One JSON object per triaged signal

---

## Portfolio

`pm-signals` is part of the [PM Intelligence](https://github.com/kustonaut) open-source toolkit:

| Repo | What It Does |
|------|-------------|
| [issue-sentinel](https://github.com/kustonaut/issue-sentinel) | Zero-config GitHub issue classification |
| [github-issue-analytics](https://github.com/kustonaut/github-issue-analytics) | Visual analytics for GitHub issue data |
| **pm-signals** | Multi-source signal aggregation & triage |

---

## Development

```bash
git clone https://github.com/kustonaut/pm-signals.git
cd pm-signals
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/

# Type check
mypy src/
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT — see [LICENSE](LICENSE).

Built by [@kustonaut](https://github.com/kustonaut).
