# Contributing to pm-signals

Thanks for your interest in contributing!  Here's how to get started.

## Development Setup

```bash
git clone https://github.com/kustonaut/pm-signals.git
cd pm-signals
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest
```

## Code Quality

```bash
ruff check src/
mypy src/
```

## Pull Requests

1. Fork the repo and create a branch from `main`.
2. Add tests for any new functionality.
3. Ensure `pytest`, `ruff check`, and `mypy` pass.
4. Open a PR with a clear description of the change.

## Adding a Fetcher

To add a new signal source:

1. Create `src/pm_signals/fetchers/your_source.py`
2. Extend `BaseFetcher` and implement `fetch() -> list[Signal]`
3. Register it in `pipeline.py` `_create_fetcher()`
4. Add tests in `tests/test_your_source.py`
5. Document in README under "Pluggable Fetchers"

## Reporting Issues

Open an issue on [GitHub](https://github.com/kustonaut/pm-signals/issues) with:
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
