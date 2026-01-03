# BrightBot Scenario Testing Framework - Setup Plan

## Repository Context

**Repo**: `brightbot` (existing)
**Location**: `/Users/bado/iccha/brighthive/brightbot/`
**New Branch**: `BD-XXX-scenario-testing-framework` (replace XXX with ticket number)
**Base Branch**: `develop`
**Purpose**: Implement integration tests for 9 production scenarios

---

## 1. Branch Creation

### Commands
```bash
cd /Users/bado/iccha/brighthive/brightbot

# Ensure develop is up to date
git checkout develop
git pull origin develop

# Create feature branch (replace XXX with JIRA ticket number)
git checkout -b BD-XXX-scenario-testing-framework

# Verify branch
git branch --show-current
```

---

## 2. Directory Structure to Create

```
brightbot/
├── tests/                           # Existing
│   ├── unit/                        # Existing (keep as-is)
│   ├── e2e/                         # Existing (keep as-is)
│   └── integration/                 # NEW - Scenario tests
│       ├── __init__.py
│       ├── conftest.py              # Pytest config + AWS fixtures
│       ├── pytest.ini               # Pytest configuration
│       ├── scenarios/               # Scenario test implementations
│       │   ├── __init__.py
│       │   ├── base.py              # BaseScenarioTest class
│       │   ├── test_scenario_01_overflow.py
│       │   ├── test_scenario_02_conflicts.py
│       │   ├── test_scenario_03_warehouse.py
│       │   ├── test_scenario_11_evolution.py
│       │   ├── test_scenario_12_search.py
│       │   ├── test_scenario_13_insights.py
│       │   ├── test_scenario_14_query.py
│       │   ├── test_scenario_15_pii.py
│       │   └── test_scenario_16_zombies.py
│       ├── fixtures/                # Test fixtures
│       │   ├── __init__.py
│       │   ├── data_generators.py  # Synthetic data generation
│       │   ├── aws_fixtures.py     # S3, DynamoDB, Redshift clients
│       │   └── agent_fixtures.py   # Mock LangGraph agents
│       ├── metrics/                 # Custom DeepEval metrics
│       │   ├── __init__.py
│       │   ├── compression_metrics.py     # S01, S03
│       │   ├── precision_recall.py        # S12
│       │   ├── statistical_significance.py # S13
│       │   ├── compliance_metrics.py      # S15
│       │   └── cost_metrics.py            # All scenarios
│       └── infrastructure/          # Shared utilities
│           ├── __init__.py
│           ├── checkpoint_manager.py      # S3-based checkpointing
│           ├── cost_tracker.py            # Real-time cost tracking
│           ├── comparison_engine.py       # BEFORE vs AFTER
│           └── parallel_executor.py       # 1,000 agent orchestration
└── scenarios/                       # Existing (keep as-is)
    ├── scenario_01_massive_overflow.md
    └── ... (other scenario docs)
```

---

## 3. Key Files to Create

### 3.1 tests/integration/pytest.ini

```ini
[pytest]
testpaths = tests/integration
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Markers for scenario grouping
markers =
    scenario_01: Token overflow tests
    scenario_02: Multi-source conflict tests
    scenario_03: Warehouse context tests
    scenario_11: Schema evolution tests
    scenario_12: Trillion-record search tests
    scenario_13: Cross-asset insight tests
    scenario_14: Natural language query tests
    scenario_15: PII detection tests
    scenario_16: Zombie table tests
    slow: Long-running tests (>1 hour)
    requires_aws: Tests requiring AWS infrastructure

# Async support
asyncio_mode = auto

# Logging
log_cli = true
log_cli_level = INFO
log_file = tests/integration/test.log
log_file_level = DEBUG

# Coverage
addopts =
    --verbose
    --strict-markers
    --tb=short
    --cov=brightbot
    --cov-report=html
    --cov-report=term-missing
```

### 3.2 tests/integration/conftest.py (Pytest Fixtures)

```python
import pytest
import boto3
import asyncio
from typing import AsyncGenerator, Generator
from brightbot.evals.core.evals import Evals

# AWS Fixtures
@pytest.fixture(scope="session")
def aws_region() -> str:
    """AWS region for testing."""
    return "us-east-1"

@pytest.fixture(scope="session")
def s3_client(aws_region):
    """S3 client for test data."""
    return boto3.client('s3', region_name=aws_region)

@pytest.fixture(scope="session")
def dynamodb_client(aws_region):
    """DynamoDB client for test metadata."""
    return boto3.client('dynamodb', region_name=aws_region)

@pytest.fixture(scope="session")
def cost_explorer_client(aws_region):
    """Cost Explorer client for cost tracking."""
    return boto3.client('ce', region_name=aws_region)

# Redshift Fixtures
@pytest.fixture(scope="session")
def redshift_workgroup_name() -> str:
    """Redshift Serverless workgroup name from CDK."""
    return "brighthive-testing-workgroup"

@pytest.fixture(scope="session")
def redshift_client(aws_region):
    """Redshift Data API client."""
    return boto3.client('redshift-data', region_name=aws_region)

# Test Run Configuration
@pytest.fixture(scope="session")
def run_id() -> str:
    """Unique run ID for this test session."""
    import uuid
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"test-run-{timestamp}-{uuid.uuid4().hex[:8]}"

# Evals Integration
@pytest.fixture(scope="session")
def evals() -> Evals:
    """DeepEval Evals instance for metric measurement."""
    return Evals(agent_name="supervisor", ci_mode=False)

# Results Storage
@pytest.fixture(scope="session")
def results_bucket(s3_client) -> str:
    """S3 bucket for storing test results."""
    return "brighthive-testing-results-dev"

@pytest.fixture(autouse=True)
async def save_test_result(request, run_id, results_bucket, s3_client):
    """
    Auto-save test results to S3 after each test.
    """
    yield  # Test runs here

    # After test completes
    if hasattr(request.node, "result"):
        result = request.node.result
        test_name = request.node.name

        import json
        from datetime import datetime

        result_data = {
            "run_id": run_id,
            "test_name": test_name,
            "timestamp": datetime.utcnow().isoformat(),
            "status": result.get("status"),
            "metrics": result.get("metrics"),
            "error": result.get("error")
        }

        key = f"{run_id}/{test_name}.json"
        s3_client.put_object(
            Bucket=results_bucket,
            Key=key,
            Body=json.dumps(result_data, indent=2)
        )

# Validation Gate Fixtures
@pytest.fixture
def validation_gate():
    """
    Interactive validation gate for 100% approval before next scenario.
    """
    def validate(scenario_id: str, metrics: dict) -> bool:
        print(f"\n{'='*60}")
        print(f"VALIDATION GATE: {scenario_id}")
        print(f"{'='*60}")
        print(f"Metrics:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")
        print(f"{'='*60}")

        approval = input(f"\n{scenario_id} 100% validated? (yes/no): ")
        return approval.lower() == "yes"

    return validate
```

### 3.3 tests/integration/scenarios/base.py (Base Class)

```python
import pytest
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from brightbot.evals.core.evals import Evals
import boto3

class BaseScenarioTest(ABC):
    """
    Base class for all scenario integration tests.
    Extends existing Evals framework with scenario-specific patterns.
    """

    def __init__(
        self,
        scenario_id: str,
        run_id: str,
        aws_region: str = "us-east-1"
    ):
        self.scenario_id = scenario_id
        self.run_id = run_id
        self.aws_region = aws_region
        self.metrics: Dict[str, Any] = {}

        # AWS clients
        self.s3_client = boto3.client('s3', region_name=aws_region)
        self.redshift_client = boto3.client('redshift-data', region_name=aws_region)

        # Reuse existing Evals class
        self.evals = Evals(agent_name="supervisor", ci_mode=False)

    @abstractmethod
    async def setup_fixtures(self):
        """Setup AWS resources, seed data, agent configs."""
        pass

    @abstractmethod
    async def execute_scenario(self) -> Dict[str, Any]:
        """Run the scenario test and return results."""
        pass

    @abstractmethod
    def collect_metrics(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Extract scenario-specific metrics from results."""
        pass

    async def cleanup_fixtures(self):
        """
        Cleanup resources (optional override).
        Default: NO cleanup (reuse infrastructure).
        """
        pass

    async def run(self) -> Dict[str, Any]:
        """Full test lifecycle."""
        try:
            await self.setup_fixtures()
            results = await self.execute_scenario()
            self.metrics = self.collect_metrics(results)

            return {
                "scenario_id": self.scenario_id,
                "run_id": self.run_id,
                "results": results,
                "metrics": self.metrics,
                "status": "success"
            }
        except Exception as e:
            import traceback
            return {
                "scenario_id": self.scenario_id,
                "run_id": self.run_id,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "status": "failure"
            }
        finally:
            await self.cleanup_fixtures()

    def save_baseline(self, phase: str, metrics: dict):
        """
        Save BEFORE or AFTER metrics to S3 for comparison.

        Args:
            phase: "before" or "after"
            metrics: Dict of metric values
        """
        import json
        from datetime import datetime

        data = {
            "scenario_id": self.scenario_id,
            "run_id": self.run_id,
            "phase": phase,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics
        }

        bucket = "brighthive-testing-results-dev"
        key = f"baselines/{self.scenario_id}-{phase}.json"

        self.s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(data, indent=2)
        )
```

### 3.4 tests/integration/scenarios/test_scenario_01_overflow.py

```python
import pytest
from .base import BaseScenarioTest
from ..fixtures.data_generators import WarehouseDataGenerator
from ..metrics.compression_metrics import CompressionRatioMetric

@pytest.mark.scenario_01
@pytest.mark.requires_aws
class TestScenario01TokenOverflow(BaseScenarioTest):
    """
    Test massive context overflow with 10B records → 6K token budget.
    Target: 8.3x compression ratio, 100% budget compliance.
    """

    def __init__(self, run_id: str):
        super().__init__(scenario_id="scenario-01", run_id=run_id)
        self.num_records = 10_000_000_000  # 10B
        self.token_budget = 6000

    async def setup_fixtures(self):
        """
        Use existing 1B baseline warehouse from CDK.
        No new data generation needed.
        """
        self.data_generator = WarehouseDataGenerator(
            s3_client=self.s3_client,
            bucket="brighthive-testing-data-dev",
            prefix="baseline/",
            num_records=self.num_records,
            seed=42  # Deterministic
        )

    async def execute_scenario(self):
        """Test priority-based compilation algorithms."""
        results = {}

        for algorithm in ["greedy", "knapsack", "optimal"]:
            # TODO: Run agent with token budget constraint
            # This will integrate with actual BrightBot agents
            response = await self.run_agent_with_budget(
                input="Query top 100 customers by revenue",
                algorithm=algorithm,
                budget=self.token_budget
            )

            results[algorithm] = {
                "tokens_used": response.token_count,
                "records_included": response.records_included,
                "records_excluded": response.records_excluded,
                "budget_exceeded": response.token_count > self.token_budget
            }

        return results

    def collect_metrics(self, results):
        """Calculate compression ratio, budget compliance."""
        metrics = {}

        for algorithm, result in results.items():
            compression_ratio = (
                self.num_records / result["records_included"]
                if result["records_included"] > 0 else 0
            )

            metrics[f"{algorithm}_compression_ratio"] = compression_ratio
            metrics[f"{algorithm}_budget_compliance"] = (
                1.0 if not result["budget_exceeded"] else 0.0
            )
            metrics[f"{algorithm}_exclusion_rate"] = (
                result["records_excluded"] / self.num_records
            )

        return metrics

    async def run_agent_with_budget(self, input: str, algorithm: str, budget: int):
        """
        Run BrightBot agent with token budget constraint.

        This will integrate with actual agent execution:
        - Use existing supervisor agent
        - Apply token budget to context compilation
        - Return token usage metrics
        """
        # TODO: Implement actual agent execution
        # For now, placeholder
        return {
            "token_count": 5500,
            "records_included": 100,
            "records_excluded": 9_999_999_900
        }

# Pytest test functions
@pytest.mark.asyncio
async def test_scenario_01_before_refactor(run_id, validation_gate):
    """Run S01 BEFORE refactoring."""
    test = TestScenario01TokenOverflow(run_id)
    result = await test.run()

    # Assertions
    assert result["status"] == "success", f"Test failed: {result.get('error')}"
    assert result["metrics"]["optimal_budget_compliance"] == 1.0
    assert result["metrics"]["optimal_compression_ratio"] >= 8.0

    # Save results for comparison
    test.save_baseline("before", result["metrics"])

    # Validation gate
    approved = validation_gate("S01", result["metrics"])
    assert approved, "S01 validation gate not approved"

@pytest.mark.asyncio
async def test_scenario_01_after_refactor(run_id):
    """Run S01 AFTER refactoring."""
    test = TestScenario01TokenOverflow(run_id)
    result = await test.run()

    # Save AFTER results
    test.save_baseline("after", result["metrics"])

    # Compare with BEFORE (done separately by comparison_engine)
    assert result["status"] == "success"
```

---

## 4. Metrics Implementation

### 4.1 tests/integration/metrics/compression_metrics.py

```python
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

class CompressionRatioMetric(BaseMetric):
    """
    Custom DeepEval metric for token compression testing (S01, S03).
    """

    def __init__(self, input_tokens: int, budget_tokens: int):
        self.input_tokens = input_tokens
        self.budget_tokens = budget_tokens
        self.threshold = budget_tokens

    def measure(self, test_case: LLMTestCase):
        """Measure compression ratio."""
        actual_tokens = len(test_case.actual_output.split())  # Simplified

        self.score = self.input_tokens / actual_tokens if actual_tokens > 0 else 0
        self.success = actual_tokens <= self.budget_tokens

        self.reason = (
            f"Compressed {self.input_tokens} → {actual_tokens} tokens "
            f"({self.score:.1f}x compression). "
            f"Budget: {self.budget_tokens}, "
            f"{'✓ PASS' if self.success else '✗ FAIL'}"
        )

    def is_successful(self):
        return self.success

    @property
    def __name__(self):
        return "Compression Ratio"
```

---

## 5. Fixtures Implementation

### 5.1 tests/integration/fixtures/data_generators.py

```python
import boto3
from typing import Iterator

class WarehouseDataGenerator:
    """
    Generator for synthetic warehouse data.
    Uses existing S3 data (no in-memory generation).
    """

    def __init__(self, s3_client, bucket: str, prefix: str, num_records: int, seed: int = 42):
        self.s3_client = s3_client
        self.bucket = bucket
        self.prefix = prefix
        self.num_records = num_records
        self.seed = seed

    def generate_record(self, record_id: int) -> dict:
        """
        Generate single record deterministically.
        O(1) memory - doesn't load all records.
        """
        import hashlib

        # Deterministic: same ID = same record
        seed_str = f"{self.seed}-{record_id}"
        hash_val = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)

        return {
            "record_id": record_id,
            "entity_id": f"entity_{record_id % 1_000_000}",
            "value": (hash_val % 10000) / 100.0,
            "metadata": {"seed": self.seed}
        }

    def list_s3_partitions(self) -> list:
        """
        List S3 partitions for querying.
        Returns paths to Parquet files.
        """
        response = self.s3_client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=self.prefix
        )

        return [obj['Key'] for obj in response.get('Contents', [])]
```

---

## 6. Infrastructure Utilities

### 6.1 tests/integration/infrastructure/comparison_engine.py

```python
import json
from typing import Dict, Any

class ComparisonEngine:
    """
    Compare BEFORE and AFTER refactoring results.
    """

    def __init__(self, s3_client, results_bucket: str, tolerance: float = 0.05):
        self.s3_client = s3_client
        self.results_bucket = results_bucket
        self.tolerance = tolerance

    def load_baseline(self, scenario_id: str, phase: str) -> dict:
        """Load BEFORE or AFTER baseline from S3."""
        key = f"baselines/{scenario_id}-{phase}.json"

        response = self.s3_client.get_object(
            Bucket=self.results_bucket,
            Key=key
        )

        return json.loads(response['Body'].read())

    def compare_scenarios(
        self,
        scenario_id: str
    ) -> Dict[str, Any]:
        """Compare BEFORE and AFTER for a scenario."""
        before = self.load_baseline(scenario_id, "before")
        after = self.load_baseline(scenario_id, "after")

        before_metrics = before["metrics"]
        after_metrics = after["metrics"]

        comparison = {
            "scenario_id": scenario_id,
            "metrics": {},
            "overall": "unchanged"
        }

        improved_count = 0
        degraded_count = 0

        for metric_name, before_value in before_metrics.items():
            after_value = after_metrics.get(metric_name)

            if after_value is None:
                continue

            # Calculate change
            if before_value == 0:
                pct_change = float('inf') if after_value > 0 else 0
            else:
                pct_change = (after_value - before_value) / before_value

            # Determine direction
            if abs(pct_change) < self.tolerance:
                direction = "unchanged"
            elif pct_change > 0:
                direction = "improved"
                improved_count += 1
            else:
                direction = "degraded"
                degraded_count += 1

            comparison["metrics"][metric_name] = {
                "before": before_value,
                "after": after_value,
                "change": pct_change,
                "direction": direction
            }

        # Overall assessment
        if improved_count > degraded_count:
            comparison["overall"] = "improved"
        elif degraded_count > improved_count:
            comparison["overall"] = "degraded"

        return comparison

    def generate_report(self, comparison: Dict[str, Any]) -> str:
        """Generate markdown report."""
        report = [f"# Performance Comparison: {comparison['scenario_id']}\n"]

        report.append(f"**Overall**: {comparison['overall'].upper()}\n")

        report.append("| Metric | Before | After | Change | Direction |")
        report.append("|--------|--------|-------|--------|-----------|")

        for metric_name, metric_data in comparison["metrics"].items():
            before = f"{metric_data['before']:.2f}"
            after = f"{metric_data['after']:.2f}"
            change = f"{metric_data['change']:+.1%}"
            direction = metric_data['direction']

            emoji = {
                "improved": "🟢",
                "degraded": "🔴",
                "unchanged": "⚪"
            }[direction]

            report.append(
                f"| {metric_name} | {before} | {after} | {change} | {emoji} {direction} |"
            )

        return "\n".join(report)
```

---

## 7. Running Tests

### 7.1 Run Single Scenario

```bash
cd /Users/bado/iccha/brighthive/brightbot

# Activate UV environment
source .venv/bin/activate

# Run S01 only
pytest tests/integration/scenarios/test_scenario_01_overflow.py -v

# Run with markers
pytest -m scenario_01 -v
```

### 7.2 Run All Scenarios

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run only AWS-dependent tests
pytest -m requires_aws -v

# Skip slow tests
pytest -m "not slow" -v
```

### 7.3 Run with Coverage

```bash
pytest tests/integration/ \
  --cov=brightbot \
  --cov-report=html \
  --cov-report=term-missing
```

---

## 8. Dependencies to Add

### Update pyproject.toml

```toml
[tool.poetry.dependencies]
# Existing dependencies...
pytest-asyncio = "^0.23.0"  # For async test support
boto3 = "^1.34.96"          # AWS SDK
moto = "^5.0.0"             # AWS mocking (optional)

[tool.poetry.group.dev.dependencies]
# Existing dev dependencies...
pytest-cov = "^4.1.0"       # Coverage reporting
pytest-xdist = "^3.5.0"     # Parallel test execution
```

---

## 9. CI/CD Integration

### .github/workflows/integration-tests.yml (NEW)

```yaml
name: Integration Tests

on:
  pull_request:
    paths:
      - 'tests/integration/**'
      - 'brightbot/**'
  workflow_dispatch:

jobs:
  integration-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_TESTING_ROLE_ARN }}
          aws-region: us-east-1

      - name: Install UV
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: |
          uv venv
          source .venv/bin/activate
          uv pip install -e .

      - name: Run integration tests
        run: |
          source .venv/bin/activate
          pytest tests/integration/ -v \
            --cov=brightbot \
            --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

---

## 10. Next Steps After Test Framework Setup

1. **Initial Commit**
   ```bash
   git add tests/integration/
   git commit -m "feat: add scenario testing framework structure"
   git push -u origin BD-XXX-scenario-testing-framework
   ```

2. **Implement S01 Test** (Week 2)
   - Complete `test_scenario_01_overflow.py`
   - Integrate with actual BrightBot agents
   - Run BEFORE baseline
   - Validate 100% before S02

3. **Incremental Scenario Implementation** (Weeks 3-11)
   - One scenario at a time
   - 100% validation gate before moving forward
   - Reuse shared infrastructure

4. **Comparison Reports** (Week 15)
   - Run comparison engine
   - Generate markdown reports
   - Present findings

---

## Summary

This test framework provides:
- ✅ Integration with existing `brightbot/evals/` framework
- ✅ Pytest-based test discovery and execution
- ✅ Custom DeepEval metrics for scenario-specific validation
- ✅ S3-based result storage for BEFORE/AFTER comparison
- ✅ Validation gates for 100% approval workflow
- ✅ AWS fixture integration (S3, Redshift, DynamoDB)
- ✅ Async test support for long-running scenarios
- ✅ CI/CD integration with GitHub Actions

**Estimated Setup Time**: 1-2 hours
**First Test (S01) Implementation**: 4-6 hours
