"""Tests for the retry_with_backoff decorator (exponential backoff)."""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.retry import retry_with_backoff


class TestRetryWithBackoff:
    """Verify retry decorator behaviour without real API calls."""

    def test_succeeds_on_first_try(self):
        """When the function succeeds immediately, no retry happens."""
        mock_fn = MagicMock(return_value="ok")

        @retry_with_backoff(max_retries=3)
        def call():
            return mock_fn()

        result = call()
        assert result == "ok"
        assert mock_fn.call_count == 1

    @patch("services.retry.time.sleep", return_value=None)
    def test_succeeds_after_transient_failure(self, mock_sleep):
        """Retries on a transient error, then succeeds."""
        mock_fn = MagicMock(side_effect=[ConnectionError("down"), "recovered"])

        @retry_with_backoff(
            max_retries=3,
            base_delay=1.0,
            retryable_exceptions=[ConnectionError],
        )
        def call():
            return mock_fn()

        result = call()
        assert result == "recovered"
        assert mock_fn.call_count == 2
        mock_sleep.assert_called_once()

    @patch("services.retry.time.sleep", return_value=None)
    def test_exhausts_max_retries(self, mock_sleep):
        """After max_retries failures, the last exception is raised."""
        mock_fn = MagicMock(side_effect=ConnectionError("persistent failure"))

        @retry_with_backoff(
            max_retries=2,
            base_delay=1.0,
            retryable_exceptions=[ConnectionError],
        )
        def call():
            return mock_fn()

        with pytest.raises(ConnectionError, match="persistent failure"):
            call()

        # 1 initial + 2 retries = 3 total calls
        assert mock_fn.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("services.retry.time.sleep", return_value=None)
    def test_backoff_timing(self, mock_sleep):
        """Verify exponential delay pattern: base * factor^attempt."""
        mock_fn = MagicMock(
            side_effect=[
                ConnectionError("1"),
                ConnectionError("2"),
                ConnectionError("3"),
                "done",
            ]
        )

        @retry_with_backoff(
            max_retries=3,
            base_delay=2.0,
            backoff_factor=2.0,
            retryable_exceptions=[ConnectionError],
        )
        def call():
            return mock_fn()

        result = call()
        assert result == "done"

        # Delays: 2*2^0=2, 2*2^1=4, 2*2^2=8
        delays = [c.args[0] for c in mock_sleep.call_args_list]
        assert delays == [2.0, 4.0, 8.0]
