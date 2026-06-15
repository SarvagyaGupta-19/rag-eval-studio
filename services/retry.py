"""Retry with exponential backoff for transient API failures."""
from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Callable, Sequence, Type

logger = logging.getLogger(__name__)

# Default transient exceptions that warrant a retry.
_DEFAULT_RETRYABLE: tuple[Type[Exception], ...] = (
    ConnectionError,
    TimeoutError,
    OSError,
)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 2.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: Sequence[Type[Exception]] | None = None,
) -> Callable:
    """Decorator that retries a function on transient failures.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds before the first retry.
        backoff_factor: Multiplier applied to delay after each retry.
        retryable_exceptions: Exception types that trigger a retry.
            Defaults to ConnectionError, TimeoutError, OSError.

    Returns:
        The return value of the wrapped function on success.

    Raises:
        The last caught exception if all retry attempts are exhausted.
    """
    exceptions = tuple(retryable_exceptions) if retryable_exceptions else _DEFAULT_RETRYABLE

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last_exception: Exception | None = None
            for attempt in range(max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc
                    if attempt < max_retries:
                        delay = base_delay * (backoff_factor ** attempt)
                        logger.warning(
                            "Attempt %d/%d for %s failed: %s. Retrying in %.1fs...",
                            attempt + 1,
                            max_retries + 1,
                            fn.__name__,
                            exc,
                            delay,
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            "All %d attempts for %s exhausted. Last error: %s",
                            max_retries + 1,
                            fn.__name__,
                            exc,
                        )
            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator
