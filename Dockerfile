# Multi-stage Dockerfile for BrightHive Testing Infrastructure CDK
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install uv
RUN pip install uv

# Development stage
FROM base as development

# Copy dependency files
COPY pyproject.toml ./
COPY README.md ./

# Install dependencies
RUN uv pip install --system -e ".[dev]"

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/

# Production stage
FROM base as production

# Copy dependency files
COPY pyproject.toml ./
COPY README.md ./

# Install production dependencies only
RUN uv pip install --system .

# Copy source code
COPY src/ ./src/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"


# Default command
CMD ["python", "-m", "brighthive_testing_cdk.main"]

