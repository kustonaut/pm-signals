"""Tests for the sentiment analyzer."""

from pm_signals.sentiment import SentimentAnalyzer


class TestSentimentAnalyzer:
    """Classify text sentiment without external APIs."""

    def setup_method(self):
        self.analyzer = SentimentAnalyzer()

    def test_frustrated_text(self):
        result = self.analyzer.analyze("This is absolutely frustrating! Broken again, unacceptable!!")
        assert result.label == "frustrated"
        assert result.score < -0.5

    def test_negative_text(self):
        result = self.analyzer.analyze("There's a bug causing errors when the page loads")
        assert result.label == "negative"
        assert result.score < 0

    def test_positive_text(self):
        result = self.analyzer.analyze("Great work! This is awesome and very helpful, thank you!")
        assert result.label == "positive"
        assert result.score > 0.3

    def test_constructive_text(self):
        result = self.analyzer.analyze("Suggestion: we could add a config option for this")
        assert result.label == "constructive"
        assert result.score > 0

    def test_neutral_text(self):
        result = self.analyzer.analyze("Updated the configuration file with new settings")
        assert result.label == "neutral"
        assert -0.2 <= result.score <= 0.15

    def test_score_clamped(self):
        # Even with many negative signals, score should stay >= -1
        result = self.analyzer.analyze(
            "Frustrated, broken, unacceptable, terrible, horrible, awful, "
            "still broken, wasting time, ignored, no response!!!!!"
        )
        assert result.score >= -1.0

    def test_emoji_property(self):
        result = self.analyzer.analyze("This is great!")
        assert result.emoji in ["😤", "😟", "😐", "💡", "😊"]
