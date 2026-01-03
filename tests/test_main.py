"""Tests for main module."""

import pytest

from brighthive_testing_cdk.main import main


@pytest.mark.asyncio
async def test_main_runs() -> None:
    """Test that main function runs without errors."""
    await main()
    assert True


class TestAsync:
    """Test suite for async functionality."""

    @pytest.mark.asyncio
    async def test_example_async(self) -> None:
        """Example async test."""
        result = await self._async_helper()
        assert result == "test"

    async def _async_helper(self) -> str:
        """Helper async function."""
        return "test"


@pytest.mark.unit
def test_example_with_fixture(sample_data: dict) -> None:
    """Test using a fixture from conftest.py."""
    assert sample_data["name"] == "test"
    assert sample_data["value"] == 123
    assert len(sample_data["items"]) == 3
