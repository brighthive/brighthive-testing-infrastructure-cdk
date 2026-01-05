"""Project-wide settings and constants.

Following Zen of Python:
- There should be one obvious way to do it
- Explicit is better than implicit
- Constants in CAPS for clarity
"""
from enum import Enum


class DeploymentMode(Enum):
    """Deployment modes for cost control and loadstress."""

    DRYRUN = "dryrun"  # Preview only, no actual deployment
    SUBSET = "subset"  # Small-scale for loadstress (MB/GB scale)
    FULL = "full"  # Full production scale (TB/PB scale)


# Project naming - single source of truth
PROJECT_NAME = "brightagent"
ACCOUNT_ID = "824267124830"

# Scale configurations by deployment mode
SCALE_CONFIG = {
    DeploymentMode.SUBSET: {
        "redshift_nodes": 1,  # Single node for loadstress
        "emr_workers": 2,  # Minimal EMR capacity
        "emr_worker_cpu": "16vCPU",  # Small workers for loadstress
        "emr_worker_memory": "64GB",  # 128GB total capacity
        "data_records": 1_000_000,  # 1M records (~100MB)
        "description": "Small subset for loadstress",
    },
    DeploymentMode.FULL: {
        "redshift_nodes": 2,  # Multi-node cluster
        "emr_workers": 20,  # Doubled from 10 for 1B record generation
        "emr_worker_cpu": "32vCPU",  # Doubled from 16vCPU
        "emr_worker_memory": "128GB",  # Doubled from 64GB (2.5TB total)
        "data_records": 1_000_000_000,  # 1B records (~100GB)
        "description": "Full production scale (reduces generation time from 10+ hrs to 2-3 hrs)",
    },
}

# Stack naming pattern
def stack_name(environment: str, component: str) -> str:
    """Generate deterministic stack name.

    Args:
        environment: Environment name (e.g., 'loadstress')
        component: Component name (e.g., 'vpc', 'redshift')

    Returns:
        Formatted stack name
    """
    return f"{PROJECT_NAME}-{environment}-{component}"


def resource_name(environment: str, resource_type: str, suffix: str = "") -> str:
    """Generate deterministic resource name.

    Args:
        environment: Environment name
        resource_type: Type of resource (e.g., 'vpc', 'sg', 'bucket')
        suffix: Optional suffix for additional specificity

    Returns:
        Formatted resource name
    """
    base = f"{PROJECT_NAME}-{environment}-{resource_type}"
    return f"{base}-{suffix}" if suffix else base
