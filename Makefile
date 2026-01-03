.PHONY: help install dev-install test test-quick check format clean lint type-check pre-commit

help:
	@echo "BrightHive Testing Infrastructure CDK - Available commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make dev-install   - Install development dependencies"
	@echo "  make test          - Run tests with coverage"
	@echo "  make test-quick    - Run tests without coverage"
	@echo "  make check         - Run all code quality checks"
	@echo "  make format        - Format code with ruff"
	@echo "  make lint          - Lint code with ruff"
	@echo "  make type-check    - Run type checking with mypy"
	@echo "  make pre-commit    - Run pre-commit on all files"
	@echo "  make clean         - Remove build artifacts and caches"

install:
	uv pip install -e .

dev-install:
	uv pip install -e ".[dev]"
	pre-commit install
	pre-commit install --hook-type pre-push

test:
	@bash scripts/test.sh

test-quick:
	@bash scripts/test.sh --no-cov

check:
	@bash scripts/check_code.sh

format:
	ruff format src tests
	ruff check --fix src tests

lint:
	ruff check src tests

type-check:
	mypy src

pre-commit:
	pre-commit run --all-files

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
