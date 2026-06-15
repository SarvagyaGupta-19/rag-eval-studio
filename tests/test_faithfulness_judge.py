"""Tests for the Gemini faithfulness judge."""
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestFaithfulnessJudge:
    """Test faithfulness scoring logic."""

    def test_score_returns_float_in_range(self):
        if not os.getenv("GEMINI_API_KEY"):
            import pytest
            pytest.skip("GEMINI_API_KEY not set")
        from services.faithfulness_judge import FaithfulnessJudge
        judge = FaithfulnessJudge()
        score = judge.score(
            answer="Apple's revenue was $394 billion.",
            context="Apple reported total revenue of $394 billion in 2024.",
        )
        assert score is not None
        assert 0.0 <= score <= 1.0

    def test_score_handles_failure_gracefully(self):
        if not os.getenv("GEMINI_API_KEY"):
            import pytest
            pytest.skip("GEMINI_API_KEY not set")
        from services.faithfulness_judge import FaithfulnessJudge
        judge = FaithfulnessJudge()
        with patch.object(judge, "client", side_effect=Exception("API down")):
            score = judge.score("test", "test")
            assert score is None or isinstance(score, float)

    def test_missing_key_raises(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
            env_backup = os.environ.pop("GEMINI_API_KEY", None)
            try:
                from importlib import reload
                import services.faithfulness_judge as fj
                reload(fj)
                import pytest
                with pytest.raises(ValueError):
                    fj.FaithfulnessJudge()
            finally:
                if env_backup:
                    os.environ["GEMINI_API_KEY"] = env_backup
