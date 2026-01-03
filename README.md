# BrightHive Testing Infrastructure CDK

AWS CDK infrastructure for testing BrightBot refactoring by recreating 9 production scenarios with REAL data.

**Related Jira Ticket:** [BH-107](https://brighthiveio.atlassian.net/browse/BH-107)

## Overview

This repository contains AWS CDK (Cloud Development Kit) infrastructure code to create testing environments for validating BrightBot refactoring. The infrastructure recreates production scenarios at scale to compare BEFORE and AFTER performance using identical test conditions.

### 9 Production Scenarios

1. **S01**: Massive Token Overflow (10B records → 6K tokens)
2. **S02**: Multi-Source Conflict Resolution (3B records)
3. **S03**: Warehouse Context Generation (1,000 tables)
4. **S11**: Schema Evolution Detection (50 sources)
5. **S12**: Distributed Trillion-Record Search (1T records, 50TB)
6. **S13**: Cross-Asset Insight Discovery
7. **S14**: Natural Language Query (<5s latency)
8. **S15**: PII Detection (GDPR compliance)
9. **S16**: Zombie Table Detection (cost optimization)

## CDK Commands

```bash
# Bootstrap CDK (first time only)
make cdk-bootstrap ENV=DEV

# Synthesize CloudFormation templates
make cdk-synth ENV=DEV

# View differences with deployed stacks
make cdk-diff ENV=DEV

# Deploy infrastructure (CAUTION: Creates AWS resources!)
make cdk-deploy ENV=DEV

# Deploy specific stack
make cdk-deploy ENV=DEV STACK=BrightBot-DEV-VPC

# Destroy infrastructure (CAUTION: Deletes all resources!)
make cdk-destroy ENV=DEV
```

### Environment Configuration

Update `config.yaml` with your AWS account ID before deploying:

```yaml
DEV:
  account: "123456789012"  # Replace with your AWS account ID
  region: "us-east-1"
```

## Features

- Modern Python 3.11+ project structure
- Package management with [uv](https://github.com/astral-sh/uv)
- Code quality with [Ruff](https://github.com/astral-sh/ruff)
- Type checking with [MyPy](https://mypy-lang.org/)
- Testing with [Pytest](https://pytest.org/)
- Pre-commit hooks for code quality
- Comprehensive test coverage reporting

- Async/await support
- Docker support

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Quick Start

### 1. Clone and Setup

```bash
cd brighthive_testing_infrastructure_cdk
bash scripts/setup_dev.sh
```

This will:
- Create a virtual environment
- Install all dependencies
- Set up pre-commit hooks
- Create .env file from template

### 2. Activate Virtual Environment

```bash
source .venv/bin/activate
```

### 3. Run Tests

```bash
make test
```

## Development

### Project Structure

```
brighthive_testing_infrastructure_cdk/
├── src/
│   └── brighthive_testing_cdk/
│       ├── __init__.py
│       └── main.py
├── tests/
│   ├── conftest.py
│   ├── __init__.py
│   └── test_main.py
├── scripts/
│   ├── setup_dev.sh
│   ├── check_code.sh
│   └── test.sh
├── .pre-commit-config.yaml
├── pyproject.toml
├── pytest.ini
├── Makefile
└── README.md
```

### Available Commands

```bash
make help          # Show all available commands
make install       # Install production dependencies
make dev-install   # Install development dependencies
make test          # Run tests with coverage
make test-quick    # Run tests without coverage
make check         # Run all code quality checks
make format        # Format code with ruff
make lint          # Lint code with ruff
make type-check    # Run type checking with mypy
make pre-commit    # Run pre-commit on all files
make clean         # Remove build artifacts and caches
```

### Running Tests

```bash
# Run all tests with coverage
make test

# Run tests without coverage (faster)
make test-quick

# Run specific test file
pytest tests/test_main.py

# Run with verbose output
pytest -v

# Run only unit tests
pytest -m unit
```

### Code Quality

```bash
# Run all quality checks
make check

# Format code
make format

# Lint code
make lint

# Type check
make type-check
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`. To run manually:

```bash
make pre-commit
```

## Configuration

### Type-Safe Settings (Pydantic)

This project uses **pydantic-settings** for elegant configuration management. No `load_dotenv()` needed!

**Quick Setup:**

```bash
# 1. Copy the example file
cp .env.example .env

# 2. Edit .env with your settings
# The .env file should be in the project root (same directory as pyproject.toml)
```

**Using Settings in Your Code:**

```python
from brighthive_testing_cdk.settings import get_settings

# Settings are automatically loaded from .env file
# No need for load_dotenv() - it's handled by pydantic-settings!
settings = get_settings()

# Access settings with full type safety and validation
print(f"Environment: {settings.environment}")
print(f"Debug mode: {settings.debug}")
print(f"Log level: {settings.log_level}")

# Check environment
if settings.is_production:
    # Production-specific logic
    pass
```

**How It Works:**

1. **Priority Order** (highest to lowest):
   - Environment variables (e.g., `export DEBUG=true`)
   - `.env` file in project root
   - Default values in `config.py`

2. **Nested Configuration** - Use double underscore `__` for nested settings:
   ```bash
   # .env file
   CACHE__ENABLED=true
   CACHE__TTL_SECONDS=600
   CACHE__MAX_SIZE=2000
   ```

3. **Type Validation** - Invalid values raise validation errors:
   ```bash
   CACHE__TTL_SECONDS=-1  # ❌ Will raise ValidationError (must be >= 0)
   ```

4. **Secret Management** - Sensitive values use `SecretStr`:
   ```python
   # Access secret value
   secret = settings.secret_key.get_secret_value()

   # Safe serialization (secrets are redacted)
   safe_data = settings.model_dump_safe()  # secret_key: "***REDACTED***"
   ```

**Adding New Settings:**

Edit `src/brighthive_testing_cdk/config.py`:

```python
class Settings(BaseSettings):
    # Add your setting with type, default, and validation
    database_url: str = Field(default="sqlite:///./app.db")
    max_connections: Annotated[int, Field(ge=1, le=100)] = 10
```

Then use it:

```python
settings = get_settings()
print(settings.database_url)  # Type-safe access!
```

**Environment-Specific Configuration:**

```bash
# .env.development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# .env.production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=your-production-secret-key
```

**Testing with Different Settings:**

```python
def test_with_custom_settings(monkeypatch):
    # Override environment variables for testing
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    # Clear cache to pick up new settings
    from brighthive_testing_cdk.settings import get_settings
    get_settings.cache_clear()

    settings = get_settings()
    assert settings.debug is True
```



### Code Style

This project uses:
- **Ruff** for linting and formatting
- **MyPy** for type checking
- Line length: 100 characters
- Python 3.11+ type hints required

## Testing

### Writing Tests

Tests are located in the `tests/` directory. Example test:

```python
import pytest

@pytest.mark.asyncio
async def test_example():
    result = await some_async_function()
    assert result == expected_value

```

### Test Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow tests
- `@pytest.mark.e2e` - End-to-end tests

### Coverage

Coverage reports are generated in `htmlcov/index.html` after running tests.

## Contributing

1. Create a new branch for your feature
2. Write tests for your changes
3. Ensure all tests pass: `make test`
4. Ensure code quality checks pass: `make check`
5. Commit your changes (pre-commit hooks will run)
6. Push and create a pull request

## License

MIT

## Authors

- **BrightHive Engineering** - engineering@brighthive.io

## Acknowledgments

Built with:
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- [Ruff](https://github.com/astral-sh/ruff) - Fast Python linter
- [Pytest](https://pytest.org/) - Testing framework
- [MyPy](https://mypy-lang.org/) - Static type checker
