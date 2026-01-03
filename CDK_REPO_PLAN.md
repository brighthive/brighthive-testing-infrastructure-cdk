# BrightHive Testing Infrastructure CDK - Setup Plan

## Repository Overview

**Name**: `brighthive-testing-infrastructure-cdk`
**Location**: `/Users/bado/iccha/brighthive/brighthive-testing-infrastructure-cdk/`
**Purpose**: Deploy AWS infrastructure for production-scale scenario testing
**Pattern**: Mirrors existing `brighthive-data-organization-cdk` and `brighthive-data-workspace-cdk`

---

## 1. Initial Repository Setup

### Commands
```bash
cd /Users/bado/iccha/brighthive/
mkdir brighthive-testing-infrastructure-cdk
cd brighthive-testing-infrastructure-cdk
git init
git checkout -b main
```

### Initial Files to Create
1. **README.md** - Deployment documentation
2. **.gitignore** - CDK standard gitignore
3. **pyproject.toml** - Poetry configuration
4. **cdk.json** - CDK app configuration
5. **config.yaml** - Environment-specific settings
6. **.pre-commit-config.yaml** - Code quality hooks
7. **app.py** - CDK entry point
8. **requirements.txt** - Generated from Poetry

---

## 2. Directory Structure

```
brighthive-testing-infrastructure-cdk/
├── README.md
├── .gitignore
├── .pre-commit-config.yaml
├── pyproject.toml
├── requirements.txt
├── cdk.json
├── config.yaml
├── app.py
├── brighthive_testing_cdk/           # Main CDK package
│   ├── __init__.py
│   ├── vpc_stack.py                  # Test VPC (10.50.0.0/16)
│   ├── data_lake_stack.py            # S3, Glue Catalog
│   ├── redshift_stack.py             # Redshift Serverless
│   ├── ecs_cluster_stack.py          # Fargate cluster (1,000 agents)
│   ├── emr_stack.py                  # EMR Serverless for data gen
│   ├── cost_tracker_stack.py         # Lambda + EventBridge
│   └── monitoring_stack.py           # CloudWatch dashboards
├── lambda/
│   ├── cost_reporter/
│   │   ├── main.py
│   │   └── requirements.txt
│   └── checkpoint_manager/
│       ├── main.py
│       └── requirements.txt
├── seed_data/
│   └── emr_jobs/
│       ├── generate_baseline_warehouse.py      # 1B records
│       ├── generate_multi_source.py            # S02 conflicts
│       └── generate_trillion_records.py        # S12 data
├── connectors/
│   ├── s3_connector.py
│   ├── cost_explorer_connector.py
│   └── slack_connector.py
└── tests/
    └── unit/
        ├── __init__.py
        └── test_stacks.py
```

---

## 3. Key Files Content

### 3.1 pyproject.toml

```toml
[tool.poetry]
name = "brighthive-testing-infrastructure-cdk"
version = "0.1.0"
description = "AWS CDK infrastructure for BrightBot testing scenarios"
authors = ["BrightHive Team"]

[tool.poetry.dependencies]
python = ">=3.11,<3.14"
aws-cdk-lib = "2.139.1"
constructs = "^10.0.0"
boto3 = "^1.34.96"
PyYAML = "^6.0"
pydantic = "^2.0.0"

[tool.poetry.group.dev.dependencies]
pre-commit = "^3.7.0"
black = "^24.0.0"
bandit = "^1.7.0"
pytest = "^8.0.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### 3.2 cdk.json

```json
{
  "app": "python app.py",
  "watch": {
    "include": [
      "**"
    ],
    "exclude": [
      "README.md",
      "cdk*.json",
      "requirements*.txt",
      "source.bat",
      "**/__init__.py",
      "**/__pycache__",
      "tests"
    ]
  },
  "context": {
    "@aws-cdk/aws-lambda:recognizeLayerVersion": true,
    "@aws-cdk/core:checkSecretUsage": true,
    "@aws-cdk/core:target-partitions": [
      "aws",
      "aws-cn"
    ],
    "@aws-cdk-containers/ecs-service-extensions:enableDefaultLogDriver": true,
    "@aws-cdk/aws-ec2:uniqueImdsv2TemplateName": true,
    "@aws-cdk/aws-ecs:arnFormatIncludesClusterName": true,
    "@aws-cdk/aws-iam:minimizePolicies": true,
    "@aws-cdk/core:validateSnapshotRemovalPolicy": true,
    "@aws-cdk/aws-codepipeline:crossAccountKeyAliasStackSafeResourceName": true,
    "@aws-cdk/aws-s3:createDefaultLoggingPolicy": true,
    "@aws-cdk/aws-sns-subscriptions:restrictSqsDescryption": true,
    "@aws-cdk/aws-apigateway:disableCloudWatchRole": true,
    "@aws-cdk/core:enablePartitionLiterals": true,
    "@aws-cdk/aws-events:eventsTargetQueueSameAccount": true,
    "@aws-cdk/aws-iam:standardizedServicePrincipals": true,
    "@aws-cdk/aws-ecs:disableExplicitDeploymentControllerForCircuitBreaker": true,
    "@aws-cdk/aws-iam:importedRoleStackSafeDefaultPolicyName": true,
    "@aws-cdk/aws-s3:serverAccessLogsUseBucketPolicy": true,
    "@aws-cdk/aws-route53-patters:useCertificate": true,
    "@aws-cdk/customresources:installLatestAwsSdkDefault": false,
    "@aws-cdk/aws-rds:databaseProxyUniqueResourceName": true,
    "@aws-cdk/aws-codedeploy:removeAlarmsFromDeploymentGroup": true,
    "@aws-cdk/aws-apigateway:authorizerChangeDeploymentLogicalId": true,
    "@aws-cdk/aws-ec2:launchTemplateDefaultUserData": true,
    "@aws-cdk/aws-secretsmanager:useAttachedSecretResourcePolicyForSecretTargetAttachments": true,
    "@aws-cdk/aws-redshift:columnId": true,
    "@aws-cdk/aws-stepfunctions-tasks:enableEmrServicePolicyV2": true,
    "@aws-cdk/aws-ec2:restrictDefaultSecurityGroup": true,
    "@aws-cdk/aws-apigateway:requestValidatorUniqueId": true,
    "@aws-cdk/aws-kms:aliasNameRef": true,
    "@aws-cdk/aws-autoscaling:generateLaunchTemplateInsteadOfLaunchConfig": true,
    "@aws-cdk/core:includePrefixInUniqueNameGeneration": true,
    "@aws-cdk/aws-efs:denyAnonymousAccess": true,
    "@aws-cdk/aws-opensearchservice:enableOpensearchMultiAzWithStandby": true,
    "@aws-cdk/aws-lambda-nodejs:useLatestRuntimeVersion": true,
    "@aws-cdk/aws-efs:mountTargetOrderInsensitiveLogicalId": true,
    "@aws-cdk/aws-rds:auroraClusterChangeScopeOfInstanceParameterGroupWithEachParameters": true,
    "@aws-cdk/aws-appsync:useArnForSourceApiAssociationIdentifier": true,
    "@aws-cdk/aws-rds:preventRenderingDeprecatedCredentials": true,
    "@aws-cdk/aws-codepipeline-actions:useNewDefaultBranchForCodeCommitSource": true,
    "@aws-cdk/aws-cloudwatch-actions:changeLambdaPermissionLogicalIdForLambdaAction": true,
    "@aws-cdk/aws-codepipeline:crossAccountKeysDefaultValueToFalse": true,
    "@aws-cdk/aws-codepipeline:defaultPipelineTypeToV2": true,
    "@aws-cdk/aws-kms:reduceCrossAccountRegionPolicyScope": true,
    "@aws-cdk/aws-eks:nodegroupNameAttribute": true,
    "@aws-cdk/aws-ec2:ebsDefaultGp3Volume": true,
    "@aws-cdk/aws-ecs:reduceEc2FargateCloudWatchPermissions": true,
    "@aws-cdk/aws-dynamodb:resourcePolicyPerReplica": true
  }
}
```

### 3.3 config.yaml

```yaml
# Environment-specific configuration
DEV:
  AWS:
    ACCOUNT_ID: "YOUR-DEV-ACCOUNT-ID"
    REGION: "us-east-1"
  VPC:
    CIDR: "10.50.0.0/16"
    MAX_AZS: 3
  S3:
    DATA_BUCKET: "brighthive-testing-data"
    ARTIFACTS_BUCKET: "brighthive-testing-artifacts"
    RESULTS_BUCKET: "brighthive-testing-results"
  REDSHIFT:
    NAMESPACE: "brighthive-testing-namespace"
    WORKGROUP: "brighthive-testing-workgroup"
    DATABASE: "testing_warehouse"
  SLACK:
    COST_REPORT_CHANNEL: "C12345"  # Replace with actual channel ID
  TAGS:
    Project: "brightbot-testing"
    Environment: "dev"
    ManagedBy: "cdk"
    Lifecycle: "persistent"

STAGE:
  AWS:
    ACCOUNT_ID: "YOUR-STAGE-ACCOUNT-ID"
    REGION: "us-east-1"
  # ... similar structure

PROD:
  AWS:
    ACCOUNT_ID: "YOUR-PROD-ACCOUNT-ID"
    REGION: "us-east-1"
  # ... similar structure
```

### 3.4 app.py (Entry Point)

```python
#!/usr/bin/env python3
import os
import yaml
import aws_cdk as cdk
from aws_cdk import Tags

from brighthive_testing_cdk.vpc_stack import VPCStack
from brighthive_testing_cdk.data_lake_stack import DataLakeStack
from brighthive_testing_cdk.redshift_stack import RedshiftStack
from brighthive_testing_cdk.ecs_cluster_stack import ECSClusterStack
from brighthive_testing_cdk.emr_stack import EMRStack
from brighthive_testing_cdk.cost_tracker_stack import CostTrackerStack

app = cdk.App()

# Get environment from context (default to DEV)
environment = app.node.try_get_context("environment") or "DEV"

# Load configuration
with open("config.yaml") as f:
    config = yaml.safe_load(f)

env_config = config[environment]
aws_config = env_config["AWS"]

# CDK environment
cdk_env = cdk.Environment(
    account=aws_config["ACCOUNT_ID"],
    region=aws_config["REGION"]
)

# Base VPC Stack
vpc_stack = VPCStack(
    app,
    f"BrightHiveTesting-VPCStack-{environment}",
    environment=environment,
    config=env_config,
    env=cdk_env
)

# Data Lake Stack (S3, Glue)
data_lake_stack = DataLakeStack(
    app,
    f"BrightHiveTesting-DataLakeStack-{environment}",
    vpc=vpc_stack.vpc,
    environment=environment,
    config=env_config,
    env=cdk_env
)

# Redshift Stack
redshift_stack = RedshiftStack(
    app,
    f"BrightHiveTesting-RedshiftStack-{environment}",
    vpc=vpc_stack.vpc,
    environment=environment,
    config=env_config,
    env=cdk_env
)

# ECS Cluster Stack (for test runners)
ecs_stack = ECSClusterStack(
    app,
    f"BrightHiveTesting-ECSStack-{environment}",
    vpc=vpc_stack.vpc,
    environment=environment,
    config=env_config,
    env=cdk_env
)

# EMR Stack (for data generation)
emr_stack = EMRStack(
    app,
    f"BrightHiveTesting-EMRStack-{environment}",
    data_bucket=data_lake_stack.data_bucket,
    environment=environment,
    config=env_config,
    env=cdk_env
)

# Cost Tracker Stack (Lambda + EventBridge)
cost_tracker_stack = CostTrackerStack(
    app,
    f"BrightHiveTesting-CostTrackerStack-{environment}",
    environment=environment,
    config=env_config,
    env=cdk_env
)

# Apply tags to all stacks
for stack in [vpc_stack, data_lake_stack, redshift_stack, ecs_stack, emr_stack, cost_tracker_stack]:
    Tags.of(stack).add("Project", env_config["TAGS"]["Project"])
    Tags.of(stack).add("Environment", env_config["TAGS"]["Environment"])
    Tags.of(stack).add("ManagedBy", env_config["TAGS"]["ManagedBy"])
    Tags.of(stack).add("Lifecycle", env_config["TAGS"]["Lifecycle"])

app.synth()
```

---

## 4. Stack Implementation Patterns

### 4.1 VPCStack Template

```python
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_logs as logs,
)
from constructs import Construct

class VPCStack(Stack):
    def __init__(self, scope: Construct, id: str, environment: str, config: dict, **kwargs):
        super().__init__(scope, id, **kwargs)

        vpc_config = config["VPC"]

        # Create VPC
        self.vpc = ec2.Vpc(
            self,
            "TestingVPC",
            ip_addresses=ec2.IpAddresses.cidr(vpc_config["CIDR"]),
            max_azs=vpc_config["MAX_AZS"],
            nat_gateways=1,  # Cost optimization
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                ),
            ],
        )

        # VPC Endpoints for cost savings
        self.vpc.add_gateway_endpoint(
            "S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3
        )

        self.vpc.add_interface_endpoint(
            "SecretsManagerEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER
        )

        # VPC Flow Logs
        log_group = logs.LogGroup(
            self,
            "VPCFlowLogGroup",
            retention=logs.RetentionDays.ONE_WEEK
        )

        ec2.FlowLog(
            self,
            "VPCFlowLog",
            resource_type=ec2.FlowLogResourceType.from_vpc(self.vpc),
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(log_group)
        )
```

### 4.2 DataLakeStack Template

```python
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_glue as glue,
    RemovalPolicy,
    Duration,
)
from constructs import Construct

class DataLakeStack(Stack):
    def __init__(self, scope: Construct, id: str, vpc, environment: str, config: dict, **kwargs):
        super().__init__(scope, id, **kwargs)

        s3_config = config["S3"]

        # Data bucket
        self.data_bucket = s3.Bucket(
            self,
            "DataBucket",
            bucket_name=f"{s3_config['DATA_BUCKET']}-{environment.lower()}",
            versioned=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="expire-old-data",
                    expiration=Duration.days(90)
                )
            ],
            removal_policy=RemovalPolicy.RETAIN,  # Keep data on stack delete
        )

        # Artifacts bucket
        self.artifacts_bucket = s3.Bucket(
            self,
            "ArtifactsBucket",
            bucket_name=f"{s3_config['ARTIFACTS_BUCKET']}-{environment.lower()}",
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Results bucket
        self.results_bucket = s3.Bucket(
            self,
            "ResultsBucket",
            bucket_name=f"{s3_config['RESULTS_BUCKET']}-{environment.lower()}",
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Glue Database
        self.glue_database = glue.CfnDatabase(
            self,
            "GlueDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name=f"testing_catalog_{environment.lower()}",
                description="Glue catalog for testing scenarios"
            )
        )
```

---

## 5. Deployment Instructions

### 5.1 Prerequisites

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install AWS CLI v2
# (Assume already installed)

# Install CDK CLI
npm install -g aws-cdk

# Configure AWS credentials
aws configure --profile testing-profile
```

### 5.2 Initial Setup

```bash
cd brighthive-testing-infrastructure-cdk

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Bootstrap CDK (one-time per account/region)
cdk bootstrap \
  --context environment=DEV \
  --profile testing-profile
```

### 5.3 Deploy Stacks

```bash
# Synthesize CloudFormation templates
cdk synth --context environment=DEV

# Deploy all stacks
cdk deploy --all \
  --context environment=DEV \
  --require-approval never \
  --profile testing-profile \
  --outputs-file ./cdk-outputs.json

# Deploy specific stack
cdk deploy BrightHiveTesting-VPCStack-DEV \
  --context environment=DEV \
  --profile testing-profile
```

### 5.4 Destroy Stacks

```bash
# Destroy all stacks (WARNING: Will delete resources)
cdk destroy --all \
  --context environment=DEV \
  --profile testing-profile
```

---

## 6. Cost Tracker Lambda Implementation

### lambda/cost_reporter/main.py

```python
import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, List
import os

def handler(event, context):
    """
    Daily cost report Lambda handler.
    Queries AWS Cost Explorer and posts to Slack.
    """
    ce = boto3.client('ce')

    # Get yesterday's costs
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=1)

    # Query costs by scenario tag
    response = ce.get_cost_and_usage(
        TimePeriod={
            'Start': start_date.isoformat(),
            'End': end_date.isoformat()
        },
        Granularity='DAILY',
        Metrics=['UnblendedCost'],
        GroupBy=[
            {'Type': 'TAG', 'Key': 'Scenario'},
        ]
    )

    # Format report
    report = format_cost_report(response, start_date)

    # Save to S3
    save_to_s3(report, start_date)

    # Send to Slack
    send_to_slack(report)

    return {'statusCode': 200, 'body': 'Cost report generated'}

def format_cost_report(response: dict, date: datetime) -> str:
    """Format cost data as markdown."""
    lines = [
        f"# Daily Cost Report - {date.strftime('%Y-%m-%d')}",
        "",
        "| Scenario | Cost (USD) |",
        "|----------|------------|"
    ]

    total = 0.0
    for result in response['ResultsByTime'][0]['Groups']:
        scenario = result['Keys'][0] or 'Untagged'
        cost = float(result['Metrics']['UnblendedCost']['Amount'])
        total += cost
        lines.append(f"| {scenario} | ${cost:.2f} |")

    lines.append(f"| **TOTAL** | **${total:.2f}** |")

    return "\n".join(lines)

def save_to_s3(report: str, date: datetime):
    """Save report to S3."""
    s3 = boto3.client('s3')
    bucket = os.environ['RESULTS_BUCKET']
    key = f"cost-reports/{date.isoformat()}.md"

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=report.encode('utf-8'),
        ContentType='text/markdown'
    )

def send_to_slack(report: str):
    """Send report to Slack channel."""
    # Import slack_connector utility
    from slack_connector import send_message

    channel_id = os.environ['SLACK_CHANNEL_ID']
    send_message(channel_id, report)
```

---

## 7. EMR Data Generation Jobs

### seed_data/emr_jobs/generate_baseline_warehouse.py

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import sys

def generate_baseline_warehouse(output_path: str, num_records: int = 1_000_000_000):
    """
    Generate 1B records (100GB) as baseline for S01-S15.

    Schema:
    - record_id (UUID)
    - entity_id (1M unique entities)
    - timestamp
    - field_001 to field_400 (400 fields per table)
    - metadata
    """
    spark = SparkSession.builder \
        .appName("GenerateBaselineWarehouse") \
        .config("spark.sql.adaptive.enabled", "true") \
        .getOrCreate()

    # Generate 1B records with 400 fields
    df = spark.range(0, num_records, numPartitions=1000)

    # Add core fields
    df = df \
        .withColumn("record_id", expr("uuid()")) \
        .withColumn("entity_id", expr("concat('entity_', cast(id % 1000000 as string))")) \
        .withColumn("timestamp", expr("timestamp('2024-01-01') + INTERVAL (id % 31536000) SECOND"))

    # Add 400 fields (simulating 1,000 tables × 400 fields)
    for i in range(1, 401):
        field_name = f"field_{i:03d}"
        df = df.withColumn(field_name, expr(f"rand({i}) * 1000"))

    # Add metadata
    df = df.withColumn(
        "metadata",
        expr("map('source', 'synthetic', 'version', '1.0')")
    )

    # Write as Parquet (columnar, compressed)
    df.write \
        .mode("overwrite") \
        .partitionBy("timestamp") \
        .parquet(output_path)

    spark.stop()

if __name__ == "__main__":
    output_path = sys.argv[1] if len(sys.argv) > 1 else "s3://bucket/baseline/"
    generate_baseline_warehouse(output_path)
```

---

## 8. Pre-commit Hooks

### .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: detect-aws-credentials
        args: ['--allow-missing-credentials']
      - id: detect-private-key

  - repo: https://github.com/psf/black
    rev: 24.1.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: ['-c', 'pyproject.toml']

  - repo: https://github.com/asottile/pyupgrade
    rev: v3.15.0
    hooks:
      - id: pyupgrade
        args: [--py311-plus]
```

---

## 9. Testing

### tests/unit/test_stacks.py

```python
import aws_cdk as cdk
from aws_cdk.assertions import Template
import pytest
import yaml

from brighthive_testing_cdk.vpc_stack import VPCStack

@pytest.fixture
def config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)["DEV"]

def test_vpc_stack_creates_vpc(config):
    app = cdk.App()
    stack = VPCStack(
        app,
        "TestVPCStack",
        environment="DEV",
        config=config
    )
    template = Template.from_stack(stack)

    # Assert VPC created
    template.resource_count_is("AWS::EC2::VPC", 1)

    # Assert NAT Gateway count
    template.resource_count_is("AWS::EC2::NatGateway", 1)

    # Assert VPC endpoint created
    template.resource_count_is("AWS::EC2::VPCEndpoint", 2)  # S3 + Secrets Manager
```

---

## 10. Next Steps After CDK Repo Setup

1. **Initial Commit**
   ```bash
   git add .
   git commit -m "feat: initial CDK infrastructure setup"
   git remote add origin <repo-url>
   git push -u origin main
   ```

2. **Deploy Baseline Infrastructure** (Week 1)
   ```bash
   cdk deploy --all --context environment=DEV
   ```

3. **Generate Baseline Data**
   ```bash
   # Submit EMR job
   aws emr-serverless start-job-run \
     --application-id <app-id> \
     --execution-role-arn <role-arn> \
     --job-driver '{
       "sparkSubmit": {
         "entryPoint": "s3://artifacts/generate_baseline_warehouse.py",
         "entryPointArguments": ["s3://data/baseline/"]
       }
     }'
   ```

4. **Integrate with BrightBot Tests**
   - Tests in brightbot repo will reference CDK outputs (S3 buckets, Redshift endpoint, etc.)
   - Use `cdk-outputs.json` for cross-repo integration

---

## Summary

This CDK repo provides:
- ✅ Isolated testing infrastructure (separate from production)
- ✅ Reusable stack patterns from existing CDK repos
- ✅ Cost tracking and daily Slack reports
- ✅ EMR Serverless for massive data generation
- ✅ ECS Fargate cluster for test execution
- ✅ Glue Catalog for metadata management
- ✅ Redshift Serverless for data warehouse testing

**Estimated Setup Time**: 2-3 hours (excluding data generation)
**Estimated Deployment Time**: 20-30 minutes (VPC + all stacks)
