"""Settings and configuration access.

This module provides a clean interface for accessing application settings.
Settings are automatically loaded from .env file via pydantic-settings.
No load_dotenv() needed!

Usage:
    Basic usage:
        >>> from brighthive_loadstress_cdk.settings import get_settings
        >>> settings = get_settings()
        >>> print(settings.app_name)
        BrightHive Loadstress Infrastructure CDK

    Check environment:
        >>> settings = get_settings()
        >>> if settings.is_production:
        ...     # Production-specific code
        ...     pass

    Access nested config:
        >>> settings = get_settings()
        >>> print(settings.cache.ttl_seconds)
        300

    Testing with custom settings:
        >>> import pytest
        >>> def test_example(monkeypatch):
        ...     monkeypatch.setenv("DEBUG", "true")
        ...     get_settings.cache_clear()  # Clear cache
        ...     settings = get_settings()
        ...     assert settings.debug is True
"""

from functools import lru_cache

from .config import Settings


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Settings are automatically loaded from .env file in project root.
    Using lru_cache ensures we only load settings once (singleton pattern).
    This is the recommended way to access settings throughout your application.

    Priority order (highest to lowest):
        1. Environment variables
        2. .env file in project root
        3. Default values from config.py

    Returns:
        Settings: Cached settings instance with validated configuration

    Example:
        >>> from brighthive_loadstress_cdk.settings import get_settings
        >>> settings = get_settings()
        >>> print(f"Running in {settings.environment.value} mode")
        Running in development mode

    Note:
        In tests, call get_settings.cache_clear() after changing environment
        variables to force reload of settings.
    """
    return Settings()


# Convenience exports
__all__ = ["Settings", "get_settings"]

