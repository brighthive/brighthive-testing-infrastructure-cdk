#!/usr/bin/env python3
"""
BrightAgent Load/Stress Loadstress Infrastructure CDK Application

LOADSTRESS environment - dedicated for stress/load loadstress production scenarios.
Creates AWS infrastructure with REAL production-scale data to loadstress BrightAgent.

Supports three deployment modes:
- DRYRUN: Preview changes without deploying
- SUBSET: Small-scale for loadstress (1M records, 1 node)
- FULL: Production-scale deployment (1B records, 2 nodes)

Purpose: Isolated stress/load loadstress environment across AWS accounts/regions.
Related Jira Ticket: BH-107
"""
import sys
import aws_cdk as cdk
import yaml
from pathlib import Path
from typing import Any

# Import stacks
from src.brighthive_loadstress_cdk.stacks.vpc_stack import VPCStack
from src.brighthive_loadstress_cdk.stacks.data_lake_stack import DataLakeStack
from src.brighthive_loadstress_cdk.stacks.redshift_stack import RedshiftStack
from src.brighthive_loadstress_cdk.stacks.emr_stack import EMRStack
from src.brighthive_loadstress_cdk.stacks.monitoring_stack import MonitoringStack
from src.brighthive_loadstress_cdk.project_settings import DeploymentMode, SCALE_CONFIG


def load_config(config_path: Path) -> dict[str, Any]:
    """Load and validate configuration from YAML file.

    Args:
        config_path: Path to config.yaml

    Returns:
        Loaded configuration dictionary

    Raises:
        FileNotFoundError: If config.yaml doesn't exist
        ValueError: If config is invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Please create config.yaml in the project root."
        )

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in config file: {e}")

    if not config:
        raise ValueError(f"Configuration file is empty: {config_path}")

    return config


def validate_environment_config(config: dict[str, Any], environment: str) -> None:
    """Validate that required environment configuration exists.

    Args:
        config: Full configuration dictionary
        environment: Environment name (e.g., 'LOADSTRESS')

    Raises:
        ValueError: If environment config is missing or invalid
    """
    if environment not in config:
        available = [k for k in config.keys() if k.isupper()]
        raise ValueError(
            f"Environment '{environment}' not found in config.yaml\n"
            f"Available environments: {', '.join(available)}"
        )

    env_config = config[environment]
    required_keys = ['account', 'region', 'vpc', 'data_lake', 'redshift', 'emr', 'tags']

    missing_keys = [key for key in required_keys if key not in env_config]
    if missing_keys:
        raise ValueError(
            f"Missing required configuration keys for {environment}:\n"
            f"  Missing: {', '.join(missing_keys)}\n"
            f"  Required: {', '.join(required_keys)}"
        )


def validate_deployment_mode(mode_str: str) -> DeploymentMode:
    """Validate and convert deployment mode string to enum.

    Args:
        mode_str: Deployment mode string from config

    Returns:
        DeploymentMode enum value

    Raises:
        ValueError: If deployment mode is invalid
    """
    valid_modes = [mode.value for mode in DeploymentMode]

    if not mode_str:
        raise ValueError(
            f"deployment_mode not specified in config.yaml\n"
            f"Valid modes: {', '.join(valid_modes)}\n"
            f"Add to config.yaml: deployment_mode: 'subset'"
        )

    try:
        return DeploymentMode(mode_str)
    except ValueError:
        raise ValueError(
            f"Invalid deployment_mode: '{mode_str}'\n"
            f"Valid modes: {', '.join(valid_modes)}\n"
            f"Update config.yaml to use one of the valid modes."
        )

app = cdk.App()

# LOADSTRESS - dedicated stress/load loadstress environment
environment = "LOADSTRESS"

try:
    # Load configuration with validation
    config_path = Path(__file__).parent / "config.yaml"
    config = load_config(config_path)

    # Validate environment configuration exists
    validate_environment_config(config, environment)

    # Get and validate deployment mode
    deployment_mode_str = config.get("deployment_mode", "subset")
    deployment_mode = validate_deployment_mode(deployment_mode_str)

    # Get scale configuration based on mode
    scale = SCALE_CONFIG[deployment_mode]

    env_config = config[environment]
except (FileNotFoundError, ValueError) as e:
    print(f"\n❌ Configuration Error: {e}\n", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Unexpected Error: {type(e).__name__}: {e}\n", file=sys.stderr)
    sys.exit(1)

# Inject scale configuration into env_config
env_config["redshift"]["number_of_nodes"] = scale["redshift_nodes"]
env_config["emr"]["instance_count"] = scale["emr_workers"]
env_config["emr"]["worker_cpu"] = scale["emr_worker_cpu"]
env_config["emr"]["worker_memory"] = scale["emr_worker_memory"]
env_config["data_records"] = scale["data_records"]
env_config["deployment_mode"] = deployment_mode.value

# Create CDK environment
env = cdk.Environment(
    account=env_config["account"],
    region=env_config["region"]
)

# Stack naming convention: BrightAgent-{Environment}-{StackName}
stack_prefix = f"BrightAgent-{environment}"

# Create VPC Stack
vpc_stack = VPCStack(
    app,
    f"{stack_prefix}-VPC",
    env=env,
    config=env_config,
)

# Create Data Lake Stack
data_lake_stack = DataLakeStack(
    app,
    f"{stack_prefix}-DataLake",
    env=env,
    config=env_config,
)

# Create Redshift Stack
redshift_stack = RedshiftStack(
    app,
    f"{stack_prefix}-Redshift",
    vpc=vpc_stack.vpc,
    env=env,
    config=env_config,
)

# Create EMR Stack for data generation
emr_stack = EMRStack(
    app,
    f"{stack_prefix}-EMR",
    data_bucket=data_lake_stack.data_bucket,
    env=env,
    config=env_config,
)

# Create Monitoring Stack for observability
monitoring_stack = MonitoringStack(
    app,
    f"{stack_prefix}-Monitoring",
    vpc=vpc_stack.vpc,
    env=env,
    config=env_config,
)

# Apply tags to all stacks
for key, value in env_config["tags"].items():
    cdk.Tags.of(app).add(key, value)

app.synth()
