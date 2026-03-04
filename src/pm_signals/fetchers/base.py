"""Abstract base fetcher — all signal sources implement this interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pm_signals.models import Signal


class BaseFetcher(ABC):
    """Base class for all signal fetchers.

    Subclasses must implement ``fetch()`` which returns a list of
    :class:`Signal` objects.  Configuration is passed as a dict
    during construction.

    Example::

        class MyFetcher(BaseFetcher):
            def fetch(self) -> list[Signal]:
                return [Signal(id="1", source="my_source",
                               title="Hello", body="World")]
    """

    name: str = "base"

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        self.settings = settings or {}

    @abstractmethod
    def fetch(self) -> list[Signal]:
        """Fetch signals from this source.

        Returns:
            A list of Signal objects ready for triage.
        """
        ...  # pragma: no cover

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
