"""Structured logging configuration using structlog.

This provides JSON-formatted logs suitable for production environments
and pretty console output for development.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application context to log entries.

    Args:
        logger: Logger instance
        method_name: Method being called
        event_dict: Event dictionary

    Returns:
        EventDict: Updated event dictionary with app context
    """
    
    from .settings import get_settings

    settings = get_settings()
    event_dict["app_name"] = settings.app_name
    event_dict["app_version"] = settings.app_version
    event_dict["environment"] = settings.environment.value
    
    return event_dict


def configure_logging(
    log_level: str = "INFO",
    json_logs: bool = True,
    include_context: bool = True,
) -> None:
    """Configure structured logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: If True, output JSON logs; otherwise use console format
        include_context: If True, add application context to all logs

    Example:
        >>> configure_logging(log_level="DEBUG", json_logs=False)
        >>> import structlog
        >>> logger = structlog.get_logger()
        >>> logger.info("application_started")
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Build processor chain
    processors: list[Processor] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if include_context:
        processors.append(add_app_context)

    # Add format processor
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            )
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


# Initialize logging on module import

from .settings import get_settings

settings = get_settings()
configure_logging(
    log_level=settings.log_level.value,
    json_logs=settings.is_production,
    include_context=True,
)


