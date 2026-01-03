# Contributing to BrightHive Testing Infrastructure CDK

Thank you for considering contributing to BrightHive Testing Infrastructure CDK!

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/brighthive_testing_infrastructure_cdk.git
   cd brighthive_testing_infrastructure_cdk
   ```

3. Run the setup script:
   ```bash
   bash scripts/setup_dev.sh
   ```

4. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Your Changes

- Write clear, concise code
- Follow the existing code style
- Add type hints to all functions
- Write docstrings for public functions

### 3. Write Tests

All new features must include tests:

```python
def test_your_feature():
    """Test description."""
    result = your_function()
    assert result == expected_value
```

### 4. Run Quality Checks

Before committing, ensure all checks pass:

```bash
# Run all checks
make check

# Or run individually
make test        # Run tests
make lint        # Check code style
make type-check  # Check types
```

### 5. Commit Your Changes

Pre-commit hooks will run automatically:

```bash
git add .
git commit -m "feat: add new feature"
```

### Commit Message Format

Follow conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test changes
- `refactor:` Code refactoring
- `chore:` Build/tooling changes

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Style

### Python Style

- Line length: 100 characters
- Use type hints
- Follow PEP 8 (enforced by Ruff)
- Use descriptive variable names

### Example

```python
def calculate_total(items: list[dict[str, float]]) -> float:
    """Calculate the total price of items.

    Args:
        items: List of items with 'price' key

    Returns:
        Total price of all items

    Raises:
        ValueError: If items list is empty
    """
    if not items:
        raise ValueError("Items list cannot be empty")

    return sum(item["price"] for item in items)
```

## Testing Guidelines

### Test Structure

```python
def test_function_name_when_condition_then_expected_result():
    """Test description."""
    # Arrange
    input_data = setup_test_data()

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected_value
```

### Test Coverage

- Aim for 90%+ coverage
- Test edge cases
- Test error conditions
- Use fixtures for common setup

### Running Tests

```bash
# All tests with coverage
make test

# Specific test file
pytest tests/test_module.py

# Specific test function
pytest tests/test_module.py::test_function

# With verbose output
pytest -v

# Stop on first failure
pytest -x
```

## Documentation

### Docstrings

Use Google-style docstrings:

```python
def function(arg1: str, arg2: int) -> bool:
    """Short description.

    Longer description if needed.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Raises:
        ValueError: When something goes wrong
    """
```

## Questions?

Feel free to open an issue for:
- Bug reports
- Feature requests
- Questions about the codebase

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
