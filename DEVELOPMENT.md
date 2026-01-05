# Development Guide

## Package Management Strategy

This project uses **uv** for fast, reliable package management with clear separation between production and development dependencies.

---

## Installation Options

### 1. **Production Only** (CDK Deployment)
Install only what's needed to deploy infrastructure:

```bash
uv pip install -e .
```

**Installs:**
- AWS CDK (`aws-cdk-lib`, `constructs`)
- AWS SDK (`boto3`)
- Configuration (`pyyaml`, `pydantic`)
- Logging (`structlog`)

**Use when:** Deploying to AWS, running CDK commands

---

### 2. **Development Environment** (Recommended)
Install everything for local development:

```bash
# Option A: UV sync (installs dev-dependencies automatically)
uv sync

# Option B: Explicit dev dependencies
uv pip install -e ".[dev]"
```

**Installs production + dev tools:**
- Testing: `pytest`, `pytest-cov`, `pytest-asyncio`
- Code quality: `ruff`, `mypy`, `pre-commit`
- Interactive: `ipython`, `ipdb`

**Use when:** Local development, running tests, linting code

---

### 3. **PySpark Testing** (Unit test EMR scripts locally)
Test data generation scripts WITHOUT deploying to EMR:

```bash
uv pip install -e ".[pyspark-testing]"
```

**Installs:**
- `pyspark>=3.5.0` - Run Spark locally
- `faker>=22.0.0` - Generate realistic test data
- `pytest` - Test framework

**Use when:**
- Testing EMR scripts before deployment
- Catching PySpark bugs locally (in seconds vs minutes)
- Developing new data generation logic

**Run tests:**
```bash
pytest tests/test_pyspark_data_generation.py -v
```

---

### 4. **Everything** (Full development setup)
Install ALL optional dependencies:

```bash
uv pip install -e ".[all-dev]"
```

**Includes:**
- All dev tools
- PySpark testing
- Performance profiling (`memory-profiler`, `line-profiler`)
- Security scanning (`safety`, `pip-audit`, `bandit`)
- Observability (`opentelemetry`)

**Use when:** You want maximum tooling (takes longer to install)

---

## Common Workflows

### New Developer Setup

```bash
# Clone repo
cd brighthive_testing_infrastructure_cdk

# Create virtual environment
uv venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dev dependencies
uv sync

# Install pre-commit hooks
pre-commit install

# Verify setup
pytest tests/ -v
```

### Test EMR Scripts Locally (BEFORE deploying)

```bash
# Install PySpark
uv pip install -e ".[pyspark-testing]"

# Run PySpark unit tests (catches bugs in 10 seconds!)
pytest tests/test_pyspark_data_generation.py -v

# Test specific function
pytest tests/test_pyspark_data_generation.py::test_apply_source_conflicts_small -vv

# If tests pass ✅ → Safe to deploy to EMR
# If tests fail ❌ → Fix bugs locally, no EMR cost
```

### Deploy Infrastructure

```bash
# Load environment
source .env.loadstress

# Bootstrap CDK (first time only)
cdk bootstrap aws://824267124830/us-west-2

# Deploy all stacks
./deploy.sh subset   # or: ./deploy.sh full
```

### Run Code Quality Checks

```bash
# Format code
ruff format .

# Lint code
ruff check . --fix

# Type check
mypy src/

# Run all checks (pre-commit)
pre-commit run --all-files
```

---

## Dependency Groups Reference

| Group | Install Command | Use Case |
|-------|----------------|----------|
| **Production** | `uv pip install -e .` | CDK deployment only |
| **dev** | `uv pip install -e ".[dev]"` | Local development, testing, linting |
| **pyspark-testing** | `uv pip install -e ".[pyspark-testing]"` | Test EMR scripts locally |
| **loadstress-advanced** | `uv pip install -e ".[loadstress-advanced]"` | Performance profiling |
| **security** | `uv pip install -e ".[security]"` | Security scanning |
| **observability** | `uv pip install -e ".[observability]"` | OpenTelemetry tracing |
| **all-dev** | `uv pip install -e ".[all-dev]"` | Everything |

---

## Why This Matters

### ✅ Benefits

1. **Faster CI/CD** - Production installs are minimal (no test dependencies)
2. **Isolated testing** - PySpark tests don't require EMR cluster
3. **Clear separation** - Know exactly what's needed for each task
4. **Cost savings** - Catch bugs locally before expensive EMR runs

### ❌ Anti-Patterns to Avoid

```bash
# DON'T: Install everything for production
pip install pyspark faker pytest  # Production doesn't need these!

# DON'T: Test EMR scripts by deploying
# (Wastes time and money - 8 failed attempts = $$$)

# DO: Test locally first
pytest tests/test_pyspark_data_generation.py  # Free, instant feedback
```

---

## Troubleshooting

### "Module 'pyspark' not found"

```bash
# PySpark is NOT in production dependencies (by design)
# Install it for testing:
uv pip install -e ".[pyspark-testing]"
```

### "Slow package installation"

```bash
# Use uv instead of pip (10-100x faster)
uv pip install -e ".[all-dev]"
```

### "Pre-commit hooks failing"

```bash
# Reinstall hooks
pre-commit clean
pre-commit install
pre-commit run --all-files
```

---

## Related Documentation

- **CDK Infrastructure:** See [README.md](README.md)
- **Observability:** See [OBSERVABILITY_GUIDE.md](OBSERVABILITY_GUIDE.md)
- **Data Generation:** See [DATA_GENERATION_APPROACH.md](DATA_GENERATION_APPROACH.md)
- **Changelog:** See [CHANGELOG.md](CHANGELOG.md)
