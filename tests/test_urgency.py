"""Tests for the urgency scorer."""

from pm_signals.urgency import UrgencyScorer


class TestUrgencyScorer:
    """4-tier urgency classification."""

    def setup_method(self):
        self.scorer = UrgencyScorer()

    def test_critical_security(self):
        result = self.scorer.score("Security vulnerability CVE-2025-1234 found in XML parser")
        assert result.level == "critical"
        assert result.score >= 0.8

    def test_critical_data_loss(self):
        result = self.scorer.score("Data loss detected in production database")
        assert result.level == "critical"

    def test_critical_outage(self):
        result = self.scorer.score("Production down — service outage affecting all users")
        assert result.level == "critical"

    def test_high_regression(self):
        result = self.scorer.score("Regression in the login flow after latest deploy, blocking users")
        assert result.level == "high"
        assert result.score >= 0.55

    def test_high_urgent(self):
        result = self.scorer.score("Urgent: customer-impact escalation needed ASAP")
        assert result.level == "high"

    def test_medium_bug(self):
        result = self.scorer.score("Bug: slow performance on the search page")
        assert result.level == "medium"
        assert result.score >= 0.25

    def test_medium_feature_request(self):
        result = self.scorer.score("Feature request: add export to PDF")
        assert result.level == "medium"

    def test_low_question(self):
        result = self.scorer.score("Question about documentation formatting")
        assert result.level == "low"
        assert result.score < 0.25

    def test_low_minor(self):
        result = self.scorer.score("Minor typo in the settings page")
        assert result.level == "low"

    def test_no_signals_is_low(self):
        result = self.scorer.score("Regular weekly sync meeting notes")
        assert result.level == "low"
        assert result.score == 0.0

    def test_emoji_property(self):
        result = self.scorer.score("Security incident")
        assert result.emoji == "🔴"

    def test_matched_signals_populated(self):
        result = self.scorer.score("Urgent blocker — regression in production")
        assert len(result.matched_signals) > 0
