#!/usr/bin/env python3
"""
BrightHive Testing Infrastructure CDK Application

This CDK app creates AWS infrastructure for testing BrightBot refactoring
by recreating 9 production scenarios with REAL data.

Related Jira Ticket: BH-107
"""
import aws_cdk as cdk
import yaml
from pathlib import Path

# Import stacks
from src.brighthive_testing_cdk.stacks.vpc_stack import VPCStack
from src.brighthive_testing_cdk.stacks.data_lake_stack import DataLakeStack
# from src.brighthive_testing_cdk.stacks.redshift_stack import RedshiftStack  # TODO

app = cdk.App()

# Get environment from context (default to DEV)
environment = app.node.try_get_context("environment") or "DEV"

# Load configuration
config_path = Path(__file__).parent / "config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)

env_config = config[environment]

# Create CDK environment
env = cdk.Environment(
    account=env_config["account"],
    region=env_config["region"]
)

# Stack naming convention: BrightBot-{Environment}-{StackName}
stack_prefix = f"BrightBot-{environment}"

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

# Apply tags to all stacks
for key, value in env_config["tags"].items():
    cdk.Tags.of(app).add(key, value)

app.synth()
