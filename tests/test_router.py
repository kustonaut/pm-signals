"""Tests for the signal router."""

from pm_signals.models import Signal
from pm_signals.router import Router


def _make_signal(title: str, body: str = "") -> Signal:
    return Signal(id="test-1", source="test", title=title, body=body)


class TestRouter:
    """Route signals to project areas by keyword matching."""

    KEYWORDS = {
        "Frontend": ["react", "css", "UI", "component", "dashboard"],
        "Backend": ["api", "server", "database", "endpoint"],
        "Infrastructure": ["deploy", "CI/CD", "docker", "kubernetes"],
        "Data": ["pipeline", "ETL", "analytics", "warehouse"],
    }

    def test_routes_to_frontend(self):
        router = Router(self.KEYWORDS)
        sig = _make_signal("Dashboard react component broken")
        result = router.route(sig)
        assert result.project == "Frontend"
        assert result.confidence > 0

    def test_routes_to_backend(self):
        router = Router(self.KEYWORDS)
        sig = _make_signal("API endpoint returning 500 errors from database")
        result = router.route(sig)
        assert result.project == "Backend"

    def test_routes_to_infrastructure(self):
        router = Router(self.KEYWORDS)
        sig = _make_signal("Docker build failing in CI/CD pipeline")
        result = router.route(sig)
        assert result.project == "Infrastructure"

    def test_routes_to_data(self):
        router = Router(self.KEYWORDS)
        sig = _make_signal("ETL pipeline failing, analytics warehouse stale")
        result = router.route(sig)
        assert result.project == "Data"

    def test_unclassified_when_no_match(self):
        router = Router(self.KEYWORDS)
        sig = _make_signal("Meeting notes from Monday standup")
        result = router.route(sig)
        assert result.project == "unclassified"
        assert result.confidence == 0.0

    def test_higher_confidence_with_more_keywords(self):
        router = Router(self.KEYWORDS)
        sig_one = _make_signal("react issue")
        sig_many = _make_signal("react css UI component dashboard")
        r1 = router.route(sig_one)
        r2 = router.route(sig_many)
        assert r2.confidence >= r1.confidence

    def test_route_all_returns_multiple_matches(self):
        router = Router(self.KEYWORDS)
        sig = _make_signal("API server deploy CI/CD")  # Backend + Infra
        results = router.route_all(sig)
        projects = [r.project for r in results]
        assert "Backend" in projects
        assert "Infrastructure" in projects

    def test_empty_keywords(self):
        router = Router({})
        sig = _make_signal("Anything at all")
        result = router.route(sig)
        assert result.project == "unclassified"
