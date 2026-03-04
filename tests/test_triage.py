"""Tests for the full triage engine."""

from pm_signals.models import Signal
from pm_signals.triage import TriageEngine


def _make_signal(title: str, body: str = "", source: str = "test") -> Signal:
    return Signal(id="test-1", source=source, title=title, body=body)


KEYWORDS = {
    "Frontend": ["react", "css", "UI", "component"],
    "Backend": ["api", "server", "database"],
}


class TestTriageEngine:
    """Full triage pipeline: route + sentiment + urgency + action."""

    def test_triage_one_returns_result(self):
        engine = TriageEngine(KEYWORDS)
        sig = _make_signal("React component crashing on load", "The UI component crashes")
        result = engine.triage_one(sig)
        assert result.signal_id == "test-1"
        assert result.project == "Frontend"
        assert result.sentiment in ["frustrated", "negative", "neutral", "constructive", "positive"]
        assert result.urgency in ["critical", "high", "medium", "low"]
        assert result.action in ["investigate", "respond", "route", "track", "fix"]

    def test_triage_list(self):
        engine = TriageEngine(KEYWORDS)
        signals = [
            _make_signal("API server error 500"),
            _make_signal("React dashboard broken"),
        ]
        results = engine.triage(signals)
        assert len(results) == 2

    def test_critical_urgency_forces_investigate(self):
        engine = TriageEngine(KEYWORDS)
        sig = _make_signal("Security vulnerability in API server")
        result = engine.triage_one(sig)
        assert result.action == "investigate"

    def test_question_gets_respond_action(self):
        engine = TriageEngine(KEYWORDS)
        sig = _make_signal("Question: how to use the API?")
        result = engine.triage_one(sig)
        assert result.action == "respond"

    def test_bug_gets_fix_action(self):
        engine = TriageEngine(KEYWORDS)
        sig = _make_signal("Bug: regression in database queries")
        result = engine.triage_one(sig)
        assert result.action == "fix"

    def test_tags_include_source(self):
        engine = TriageEngine(KEYWORDS)
        sig = _make_signal("Some issue", source="github")
        result = engine.triage_one(sig)
        assert "source:github" in result.tags

    def test_no_keywords_still_works(self):
        engine = TriageEngine()
        sig = _make_signal("Random signal with no keywords")
        result = engine.triage_one(sig)
        assert result.project == "unclassified"
