"""Tests for settings and configuration."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest
from pydantic import ValidationError

from brighthive_loadstress_cdk.config import (
    CacheConfig,
    Environment,
    LogLevel,
    Settings,
)
from brighthive_loadstress_cdk.settings import get_settings


class TestSettings:
    """Test suite for Settings class."""

    def test_settings_defaults(self) -> None:
        """Test that settings have correct defaults."""
        settings = Settings()
        assert settings.environment == Environment.DEVELOPMENT
        assert settings.debug is False
        assert settings.log_level == LogLevel.INFO
        assert settings.app_name == "BrightHive Loadstress Infrastructure CDK"
        assert settings.app_version == "0.1.0"

    def test_settings_from_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that settings can be loaded from environment variables."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("SECRET_KEY", "super-secret-key")

        settings = Settings()

        assert settings.environment == Environment.PRODUCTION
        assert settings.debug is True
        assert settings.log_level == LogLevel.DEBUG
        assert settings.secret_key.get_secret_value() == "super-secret-key"

    def test_settings_from_env_file(self) -> None:
        """Test that settings can be loaded from .env file."""
        with TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                "ENVIRONMENT=staging\n"
                "DEBUG=true\n"
                "LOG_LEVEL=WARNING\n"
                "SECRET_KEY=from-env-file\n"
            )

            settings = Settings(_env_file=str(env_file))

            assert settings.environment == Environment.STAGING
            assert settings.debug is True
            assert settings.log_level == LogLevel.WARNING
            assert settings.secret_key.get_secret_value() == "from-env-file"

    def test_settings_without_env_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that settings work without .env file (using defaults and env vars)."""
        # Point to a non-existent .env file
        with TemporaryDirectory() as tmpdir:
            non_existent_env = Path(tmpdir) / ".env"
            # Ensure file doesn't exist
            assert not non_existent_env.exists()

            # Override with environment variable
            monkeypatch.setenv("ENVIRONMENT", "staging")

            settings = Settings(_env_file=str(non_existent_env))

            # Should use env var
            assert settings.environment == Environment.STAGING
            # Should use defaults for missing vars
            assert settings.debug is False
            assert settings.log_level == LogLevel.INFO

    def test_settings_env_vars_override_env_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that environment variables override .env file values."""
        with TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("ENVIRONMENT=staging\n")

            # Override with env var
            monkeypatch.setenv("ENVIRONMENT", "production")

            settings = Settings(_env_file=str(env_file))

            assert settings.environment == Environment.PRODUCTION

    def test_settings_case_insensitive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that settings are case-insensitive."""
        monkeypatch.setenv("environment", "PRODUCTION")
        monkeypatch.setenv("DEBUG", "TRUE")

        settings = Settings()

        assert settings.environment == Environment.PRODUCTION
        assert settings.debug is True

    def test_settings_nested_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test nested configuration with double underscore delimiter."""
        monkeypatch.setenv("CACHE__ENABLED", "false")
        monkeypatch.setenv("CACHE__TTL_SECONDS", "600")
        monkeypatch.setenv("CACHE__MAX_SIZE", "2000")

        settings = Settings()

        assert settings.cache.enabled is False
        assert settings.cache.ttl_seconds == 600
        assert settings.cache.max_size == 2000

    def test_settings_validation_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that invalid settings raise validation errors."""
        monkeypatch.setenv("CACHE__TTL_SECONDS", "-1")

        with pytest.raises(ValidationError):
            Settings()

    def test_settings_extra_fields_ignored(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that extra fields are ignored."""
        monkeypatch.setenv("UNKNOWN_FIELD", "some_value")

        # Should not raise an error
        settings = Settings()
        assert not hasattr(settings, "unknown_field")

    def test_is_production_property(self) -> None:
        """Test is_production property."""
        settings = Settings(environment=Environment.PRODUCTION)
        assert settings.is_production is True
        assert settings.is_development is False
        assert settings.is_loadstress is False

    def test_is_development_property(self) -> None:
        """Test is_development property."""
        settings = Settings(environment=Environment.DEVELOPMENT)
        assert settings.is_production is False
        assert settings.is_development is True
        assert settings.is_loadstress is False

    def test_is_loadstress_property(self) -> None:
        """Test is_loadstress property."""
        settings = Settings(environment=Environment.LOADSTRESS)
        assert settings.is_production is False
        assert settings.is_development is False
        assert settings.is_loadstress is True

    def test_model_dump_safe_redacts_secrets(self) -> None:
        """Test that model_dump_safe redacts sensitive information."""
        settings = Settings(secret_key="super-secret")

        safe_dump = settings.model_dump_safe()

        assert safe_dump["secret_key"] == "***REDACTED***"
        assert safe_dump["environment"] == Environment.DEVELOPMENT


class TestGetSettings:
    """Test suite for get_settings function."""

    def test_get_settings_returns_settings_instance(self) -> None:
        """Test that get_settings returns a Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_caching(self) -> None:
        """Test that get_settings caches the instance."""
        settings1 = get_settings()
        settings2 = get_settings()

        # Should be the same instance due to lru_cache
        assert settings1 is settings2

    def test_get_settings_with_env_changes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that settings reflect environment at cache time."""
        # Clear the cache first
        get_settings.cache_clear()

        monkeypatch.setenv("ENVIRONMENT", "production")

        settings = get_settings()

        assert settings.environment == Environment.PRODUCTION


class TestCacheConfig:
    """Test suite for CacheConfig."""

    def test_cache_config_defaults(self) -> None:
        """Test CacheConfig default values."""
        cache = CacheConfig()

        assert cache.enabled is True
        assert cache.ttl_seconds == 300
        assert cache.max_size == 1000

    def test_cache_config_custom_values(self) -> None:
        """Test CacheConfig with custom values."""
        cache = CacheConfig(
            enabled=False,
            ttl_seconds=600,
            max_size=2000
        )

        assert cache.enabled is False
        assert cache.ttl_seconds == 600
        assert cache.max_size == 2000

    def test_cache_config_validation(self) -> None:
        """Test CacheConfig validation."""
        with pytest.raises(ValidationError):
            CacheConfig(ttl_seconds=-1)

        with pytest.raises(ValidationError):
            CacheConfig(max_size=-1)

    def test_cache_config_frozen(self) -> None:
        """Test that CacheConfig is frozen (immutable)."""
        cache = CacheConfig()

        with pytest.raises(ValidationError):
            cache.enabled = False





class TestEnvironmentEnum:
    """Test suite for Environment enum."""

    def test_environment_values(self) -> None:
        """Test Environment enum values."""
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.STAGING.value == "staging"
        assert Environment.PRODUCTION.value == "production"
        assert Environment.LOADSTRESS.value == "loadstress"


class TestLogLevelEnum:
    """Test suite for LogLevel enum."""

    def test_log_level_values(self) -> None:
        """Test LogLevel enum values."""
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.ERROR.value == "ERROR"
        assert LogLevel.CRITICAL.value == "CRITICAL"

