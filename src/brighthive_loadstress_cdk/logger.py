"""Logger utilities and helpers.

Provides convenience functions for logging throughout the application.
"""

from functools import wraps
from time import perf_counter
from typing import Any, Callable, TypeVar

import structlog

F = TypeVar("F", bound=Callable[..., Any])


def get_logger(name: str | None = None) -> Any:
    """Get a structured logger instance.

    Args:
        name: Logger name (defaults to calling module)

    Returns:
        Configured structlog logger

    Example:
        >>> from brighthive_loadstress_cdk.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("event_occurred", user_id=123)
    """
    return structlog.get_logger(name)


def log_function_call(logger: Any | None = None) -> Callable[[F], F]:
    """Decorator to log function calls with arguments and execution time.

    Args:
        logger: Optional logger instance (creates one if not provided)

    Returns:
        Decorated function

    Example:
        >>> @log_function_call()
        ... def process_data(data: dict) -> dict:
        ...     return {"result": "processed"}
    """

    def decorator(func: F) -> F:
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = perf_counter()
            logger.info(
                "function_call_start",
                function=func.__name__,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys()),
            )

            try:
                result = func(*args, **kwargs)
                duration = perf_counter() - start
                logger.info(
                    "function_call_success",
                    function=func.__name__,
                    duration_ms=round(duration * 1000, 2),
                )
                return result
            except Exception as e:
                duration = perf_counter() - start
                logger.error(
                    "function_call_error",
                    function=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__,
                    duration_ms=round(duration * 1000, 2),
                )
                raise

        return wrapper  # type: ignore

    return decorator


class LogContext:
    """Context manager for adding structured context to logs.

    Example:
        >>> from brighthive_loadstress_cdk.logger import get_logger, LogContext
        >>> logger = get_logger(__name__)
        >>> with LogContext(logger, user_id="123", request_id="abc") as ctx_logger:
        ...     ctx_logger.info("processing_request")
    """

    def __init__(self, logger: Any, **context: Any) -> None:
        """Initialize log context.

        Args:
            logger: Logger instance
            **context: Context key-value pairs to add
        """
        self.logger = logger
        self.context = context
        self.bound_logger: Any = None

    def __enter__(self) -> Any:
        """Enter context and bind logger."""
        self.bound_logger = self.logger.bind(**self.context)
        return self.bound_logger

    def __exit__(self, *args: Any) -> None:
        """Exit context."""
        pass


__all__ = ["get_logger", "log_function_call", "LogContext"]

