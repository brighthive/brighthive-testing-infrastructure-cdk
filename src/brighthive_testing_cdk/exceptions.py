"""Custom exception hierarchy and error handling patterns.

This module defines application-specific exceptions with context support.
"""

from typing import Any


class BrighthiveTestingCdkError(Exception):
    """Base exception for BrightHive Testing Infrastructure CDK.

    All custom exceptions should inherit from this class.
    Supports additional context via keyword arguments.
    """

    def __init__(self, message: str, **context: Any) -> None:
        """Initialize exception with message and context.

        Args:
            message: Error message
            **context: Additional context as key-value pairs
        """
        super().__init__(message)
        self.message = message
        self.context = context

    def __str__(self) -> str:
        """String representation including context."""
        if self.context:
            ctx_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} ({ctx_str})"
        return self.message


class ValidationError(BrighthiveTestingCdkError):
    """Raised when validation fails."""

    pass


class ConfigurationError(BrighthiveTestingCdkError):
    """Raised when configuration is invalid."""

    pass


class ResourceNotFoundError(BrighthiveTestingCdkError):
    """Raised when a resource is not found."""

    pass


class ExternalServiceError(BrighthiveTestingCdkError):
    """Raised when an external service call fails."""

    pass


class AuthenticationError(BrighthiveTestingCdkError):
    """Raised when authentication fails."""

    pass


class AuthorizationError(BrighthiveTestingCdkError):
    """Raised when authorization fails."""

    pass

