"""
tests/test_cv.py — Unit tests for cv/grading_model.py
"""

import pytest


class TestGradingModel:
    """Tests for the computer vision produce grading model."""

    def setup_method(self):
        from cv.grading_model import GradingModel
        self.grader = GradingModel()

    def test_model_initialises(self):
        assert self.grader is not None
        assert self.grader.classes == ["Grade A", "Grade B", "Grade C"]

    def test_predict_returns_dict(self):
        result = self.grader.predict("dummy_image.jpg")
        assert isinstance(result, dict)

    def test_predict_has_grade_key(self):
        result = self.grader.predict("dummy.jpg")
        assert "grade" in result

    def test_predict_has_confidence_key(self):
        result = self.grader.predict("dummy.jpg")
        assert "confidence" in result

    def test_predict_has_details_key(self):
        result = self.grader.predict("dummy.jpg")
        assert "details" in result

    def test_grade_is_valid(self):
        result = self.grader.predict("dummy.jpg")
        assert result["grade"] in ["Grade A", "Grade B", "Grade C"]

    def test_confidence_in_range(self):
        result = self.grader.predict("dummy.jpg")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_predict_multiple_calls_consistent_structure(self):
        """Multiple calls should always return same dict structure."""
        for _ in range(5):
            result = self.grader.predict("dummy.jpg")
            assert "grade" in result
            assert "confidence" in result
            assert "details" in result

    def test_classes_list_unchanged(self):
        """classes attribute must not be mutated by predict()."""
        original = list(self.grader.classes)
        self.grader.predict("dummy.jpg")
        assert self.grader.classes == original
