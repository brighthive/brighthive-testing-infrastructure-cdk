"""Configuration management using Pydantic.

This module provides type-safe configuration with validation.
Settings are automatically loaded from .env file without needing load_dotenv().
"""

from enum import Enum
from pathlib import Path
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    SecretStr,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

# Find .env file in project root (parent of src/)
_PACKAGE_DIR = Path(__file__).parent
_PROJECT_ROOT = _PACKAGE_DIR.parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Environment(str, Enum):
    """Application environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class CacheConfig(BaseModel):
    """Cache configuration."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    ttl_seconds: Annotated[int, Field(ge=0)] = 300
    max_size: Annotated[int, Field(ge=0)] = 1000





class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Settings are loaded from:
    1. Environment variables (highest priority)
    2. .env file in project root (if it exists)
    3. Default values (lowest priority)

    The .env file is located at: <project_root>/.env
    """

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    # Basic settings
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    log_level: LogLevel = LogLevel.INFO

    # Application metadata
    app_name: str = "BrightHive Testing Infrastructure CDK"
    app_version: str = "0.1.0"

    # Security
    secret_key: SecretStr = Field(default=SecretStr("change-me-in-production"))
    allowed_hosts: list[str] = Field(default_factory=lambda: ["*"])

    # Cache
    cache: CacheConfig = Field(default_factory=CacheConfig)

    

    @field_validator("environment", mode="before")
    @classmethod
    def validate_environment(cls, v: Any) -> Environment:
        """Validate and convert environment string."""
        if isinstance(v, str):
            return Environment(v.lower())
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        """Check if running in test mode."""
        return self.environment == Environment.TESTING

    def model_dump_safe(self) -> dict[str, Any]:
        """Dump model without exposing secrets."""
        data = self.model_dump()
        # Mask sensitive fields
        if "secret_key" in data:
            data["secret_key"] = "***REDACTED***"
        return data

