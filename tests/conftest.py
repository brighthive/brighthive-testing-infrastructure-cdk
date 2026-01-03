"""Shared pytest fixtures for BrightHive Testing Infrastructure CDK."""

import pytest
from typing import AsyncGenerator
from pathlib import Path


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for test files."""
    return tmp_path


@pytest.fixture
async def async_client() -> AsyncGenerator:
    """Provide an async client for testing."""
    # TODO: Replace with your actual async client setup
    yield None


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch) -> None:
    """Reset environment variables and settings cache for each test."""
    # Clear settings cache to prevent test pollution
    from brighthive_testing_cdk.settings import get_settings
    get_settings.cache_clear()
    # Add any environment variables that should be reset between tests
    monkeypatch.setenv("TESTING", "true")


@pytest.fixture
def sample_data() -> dict:
    """Provide sample data for testing."""
    return {
        "name": "test",
        "value": 123,
        "items": ["a", "b", "c"],
    }
