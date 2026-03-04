"""Signal fetchers — pluggable data source adapters."""

from pm_signals.fetchers.base import BaseFetcher
from pm_signals.fetchers.sample import SampleFetcher

__all__ = ["BaseFetcher", "SampleFetcher"]
