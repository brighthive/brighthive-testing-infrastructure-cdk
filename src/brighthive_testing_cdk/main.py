"""Main module for BrightHive Testing Infrastructure CDK."""

import asyncio
from .settings import get_settings


async def main() -> None:
    """Main async entry point."""
    # Settings are automatically loaded from .env file via pydantic-settings
    # No need for load_dotenv() - it's handled by the Settings class!
    # The .env file is located at: <project_root>/.env
    settings = get_settings()
    print(f"Hello from {settings.app_name}!")
    print(f"Environment: {settings.environment.value}")
    print(f"Debug mode: {settings.debug}")
    # TODO: Add your async logic here


if __name__ == "__main__":
    asyncio.run(main())

