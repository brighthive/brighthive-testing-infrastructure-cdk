# BrightHive Testing Infrastructure CDK - Implementation Plan

**Jira Ticket:** BH-107
**Created:** 2026-01-03
**Purpose:** AWS CDK infrastructure for testing BrightBot refactoring with 9 production scenarios

## Executive Summary

Create AWS infrastructure to test BrightBot refactoring by recreating 9 production scenarios with REAL data (not mocks). Compare BEFORE and AFTER performance using identical test conditions.

**Key Decisions:**
- **IaC**: AWS CDK (Python) for tear-up/tear-down automation
- **Scale**: 50TB real data in S3 for trillion-record scenario (S12)
- **Approach**: Start with S01-S03 foundation scenarios, then scale to S12
- **Cost Control**: Daily cost reports with tagging by scenario

## Architecture Overview

### Infrastructure Components

1. **VPC Stack** ✅ IMPLEMENTED
   - CIDR: 10.50.0.0/16 (DEV), 10.51.0.0/16 (STAGING), 10.52.0.0/16 (PROD)
   - 3 Availability Zones
   - Public/Private subnets
   - VPC Endpoints (S3, Secrets Manager, CloudWatch Logs)
   - NAT Gateway (1 for DEV, 2 for STAGING, 3 for PROD)

2. **Data Lake Stack** ✅ IMPLEMENTED
   - S3 bucket with lifecycle policies (30-day retention)
   - Glue Catalog database
   - Glue Crawler for metadata discovery
   - IAM roles for Glue

3. **Redshift Stack** 🔲 TODO
   - Redshift Serverless cluster
   - Auto-pause after 5 minutes inactivity
   - 1,000 tables for S01-S03 scenarios
   - Query editor integration

4. **ECS Cluster Stack** 🔲 TODO
   - Fargate tasks for parallel agent execution
   - Support for 1,000 concurrent agents (S03, S12)
   - CloudWatch logging
   - Task definitions for test runners

5. **EMR Stack** 🔲 TODO
   - EMR Serverless for data generation
   - PySpark jobs for creating 50TB datasets
   - S3 output to Data Lake
   - Cost-optimized Spot instances

6. **Cost Tracker Stack** 🔲 TODO
   - Lambda function for daily cost reports
   - EventBridge schedule (daily 9am UTC)
   - Slack integration via SSM Parameter Store
   - Tag-based cost allocation

## Incremental Testing Strategy

### Scenario Dependency Graph

```
BASE INFRASTRUCTURE (Week 1)
    ↓
┌─────────── GROUP 1: WAREHOUSE ───────────┐
│  S01: Token Overflow (Week 2)            │
│  ↓ Uses: 1B records → Test compression   │
│  S02: Multi-Source Conflicts (Week 3)    │
│  ↓ Extends S01: Add Postgres, DynamoDB   │
│  S03: Warehouse Context (Week 4)         │
│  ✓ ECS cluster validated                 │
└───────────────────────────────────────────┘
    ↓
┌─────────── GROUP 2: METADATA ────────────┐
│  S11: Schema Evolution (Week 5)          │
│  S16: Zombie Tables (Week 6)             │
│  S15: PII Detection (Week 7)             │
└───────────────────────────────────────────┘
    ↓
┌─────────── GROUP 3: INSIGHTS ────────────┐
│  S14: Natural Language Query (Week 8)    │
│  S13: Cross-Asset Insights (Week 9)      │
└───────────────────────────────────────────┘
    ↓
┌─────────── GROUP 4: TRILLION-RECORD ─────┐
│  S12: Distributed Search (Week 10-11)    │
│  NEW DATA: 50TB (1T records)             │
└───────────────────────────────────────────┘
```

### Data Reuse Strategy

| Scenario | Data Source | Reuses From | New Data | Size |
|----------|-------------|-------------|----------|------|
| S01 | Redshift Serverless | Baseline | 1B records, 1,000 tables | 100GB |
| S02 | S01 + Postgres + DynamoDB | S01 | 500M each | +50GB |
| S03 | S01/S02 warehouse | S01, S02 | Metadata | +5GB |
| S11 | S03 warehouse | S01-S03 | Schema versions | +10GB |
| S16 | S11 schemas | S01-S11 | Query logs (90 days) | +20GB |
| S15 | S11/S16 warehouse | S01-S16 | PII samples | +2GB |
| S14 | All warehouse | S01-S15 | Query cache | +1GB |
| S13 | All warehouse | S01-S15 | - | 0GB |
| S12 | **NEW: 1T records** | S03 ECS cluster | 50TB Parquet | **+50TB** |

**Cost Savings**: 89% reduction ($10,350/month → $1,155/month)

## Stack Implementation Details

### 1. VPC Stack (IMPLEMENTED)

```python
# src/brighthive_testing_cdk/stacks/vpc_stack.py
class VPCStack(Stack):
    - VPC with configurable CIDR
    - Public/Private subnets across 3 AZs
    - NAT Gateway (count varies by environment)
    - VPC Endpoints:
      * S3 Gateway Endpoint (no NAT cost)
      * Secrets Manager Interface Endpoint
      * CloudWatch Logs Interface Endpoint
```

### 2. Data Lake Stack (IMPLEMENTED)

```python
# src/brighthive_testing_cdk/stacks/data_lake_stack.py
class DataLakeStack(Stack):
    - S3 bucket: brightbot-test-{env}-{account}
    - Lifecycle policy: 30-day expiration
    - Glue Catalog database
    - Glue Crawler with schema change tracking
    - IAM role for Glue service
```

### 3. Redshift Stack (TODO)

```python
# src/brighthive_testing_cdk/stacks/redshift_stack.py
class RedshiftStack(Stack):
    """Redshift Serverless for S01-S03 scenarios."""

    Components:
    - Redshift Serverless namespace
    - Redshift Serverless workgroup
    - Security group in VPC
    - Secrets Manager for credentials
    - Auto-pause: 5 minutes
    - Base capacity: 32 RPUs (adjustable)

    Scenarios:
    - S01: 10B records (token overflow testing)
    - S02: 3B records (multi-source conflicts)
    - S03: 1,000 tables, 400K fields (warehouse context)
```

### 4. ECS Cluster Stack (TODO)

```python
# src/brighthive_testing_cdk/stacks/ecs_cluster_stack.py
class ECSClusterStack(Stack):
    """ECS Fargate cluster for parallel agent execution."""

    Components:
    - ECS Cluster with Fargate capacity providers
    - Task Definition:
      * 2048 CPU units (2 vCPU)
      * 4096 MB memory
      * CloudWatch log group
    - Service with auto-scaling (0-1000 tasks)
    - IAM execution role

    Usage:
    - S03: 1,000 parallel table agents
    - S12: 1,000 parallel search agents
```

### 5. EMR Stack (TODO)

```python
# src/brighthive_testing_cdk/stacks/emr_stack.py
class EMRStack(Stack):
    """EMR Serverless for data generation jobs."""

    Components:
    - EMR Serverless application
    - S3 bucket for scripts
    - IAM role for EMR execution
    - PySpark jobs:
      * generate_baseline_data.py (1B records, 100GB)
      * generate_trillion_records.py (1T records, 50TB)

    Configuration:
    - Release: emr-7.0.0
    - Instance type: c6i.4xlarge
    - Instance count: 10 (baseline), 100 (trillion-record)
    - Cost: ~$400 for 50TB generation (3 hours)
```

### 6. Cost Tracker Stack (TODO)

```python
# src/brighthive_testing_cdk/stacks/cost_tracker_stack.py
class CostTrackerStack(Stack):
    """Daily cost tracking and Slack notifications."""

    Components:
    - Lambda function (Python 3.12)
    - EventBridge rule (cron: 0 9 * * *)
    - IAM role with Cost Explorer permissions
    - SSM Parameter Store for Slack webhook
    - S3 bucket for cost history

    Features:
    - Tag-based cost allocation
    - Daily Slack reports
    - Cost anomaly detection
    - Scenario-level breakdown
```

## Configuration Management

### config.yaml Structure

```yaml
DEV:
  account: "TBD"  # AWS account ID
  region: "us-east-1"

  vpc:
    cidr: "10.50.0.0/16"
    max_azs: 3
    nat_gateways: 1

  data_lake:
    bucket_prefix: "brightbot-test"
    retention_days: 30

  redshift:
    node_type: "ra3.xlplus"
    number_of_nodes: 2
    database_name: "brightbot_test"
    auto_pause_minutes: 5

  ecs:
    max_task_count: 1000
    cpu: 2048
    memory: 4096

  emr:
    release_label: "emr-7.0.0"
    instance_type: "c6i.4xlarge"
    instance_count: 10

  cost_tracking:
    daily_report_enabled: true
    slack_webhook_ssm_key: "/brightbot/testing/slack-webhook"

  tags:
    Project: "brightbot-testing"
    Environment: "dev"
    ManagedBy: "cdk"
    CostCenter: "engineering"
    JiraTicket: "BH-107"
```

## Deployment Workflow

### 1. Bootstrap (One-Time Setup)

```bash
# Configure AWS credentials
export AWS_PROFILE=brighthive-dev

# Update config.yaml with account ID
vim config.yaml

# Bootstrap CDK
make cdk-bootstrap ENV=DEV
```

### 2. Deploy Infrastructure

```bash
# Deploy all stacks
make cdk-deploy ENV=DEV

# Or deploy incrementally
make cdk-deploy ENV=DEV STACK=BrightBot-DEV-VPC
make cdk-deploy ENV=DEV STACK=BrightBot-DEV-DataLake
make cdk-deploy ENV=DEV STACK=BrightBot-DEV-Redshift
```

### 3. Seed Data (EMR Jobs)

```bash
# Generate baseline 1B records (S01-S03)
aws emr-serverless start-job-run \
  --application-id <app-id> \
  --execution-role-arn <role-arn> \
  --job-driver '{
    "sparkSubmit": {
      "entryPoint": "s3://brightbot-scripts/generate_baseline_data.py"
    }
  }'

# Generate 50TB for S12 (takes ~3 hours)
aws emr-serverless start-job-run \
  --application-id <app-id> \
  --execution-role-arn <role-arn> \
  --job-driver '{
    "sparkSubmit": {
      "entryPoint": "s3://brightbot-scripts/generate_trillion_records.py"
    }
  }'
```

### 4. Run Tests (Brightbot Integration)

Tests are run from the brightbot repository on branch `BH-107-scenario-testing-framework`.

```bash
# From brightbot repo
cd /path/to/brightbot
source .venv/bin/activate

# Run specific scenario
pytest tests/integration/scenarios/test_scenario_01_overflow.py -v

# Run all scenarios
pytest tests/integration/scenarios/ -m scenario
```

### 5. Teardown

```bash
# Destroy all stacks (CAUTION!)
make cdk-destroy ENV=DEV

# Or destroy specific stack
make cdk-destroy ENV=DEV STACK=BrightBot-DEV-Redshift
```

## Cost Estimates

### Monthly Costs (DEV Environment)

| Component | Cost | Notes |
|-----------|------|-------|
| **VPC** | $32/month | NAT Gateway (1 × $32) |
| **S3** | $5/month | 188GB standard storage |
| **Glue Catalog** | $1/month | Metadata storage |
| **Redshift Serverless** | $500/month | Auto-pauses, pay-per-use |
| **ECS Fargate** | $0/month | No tasks when idle |
| **EMR Serverless** | $0/month | Pay per job execution |
| **CloudWatch Logs** | $5/month | VPC Flow Logs, application logs |
| **Total (Idle)** | **~$543/month** | |
| **S12 Storage (50TB)** | **+$1,150/month** | Only when testing S12 |

### Per-Run Costs (BEFORE + AFTER)

| Scenario | Duration | Cost/Run |
|----------|----------|----------|
| S01 | 5 min | $5 |
| S02 | 5 min | $8 |
| S03 | 2-8 hours | $120 |
| S11 | 30 min | $6 |
| S12 | 6.5 hours | $1,092 |
| S13 | 30 min | $7 |
| S14 | 5 sec | $3 |
| S15 | 30 min | $9 |
| S16 | 30 min | $4 |
| **Total** | | **$1,254** |
| **BEFORE + AFTER** | | **$2,508** |

## Security Considerations

### IAM Roles and Policies

- **Least Privilege**: Each service has minimal permissions
- **Service Principals**: Only AWS services can assume roles
- **No Hardcoded Secrets**: All secrets in Secrets Manager/SSM
- **Encryption**: S3 buckets with SSE-S3, Redshift with KMS

### Network Security

- **Private Subnets**: All compute in private subnets
- **Security Groups**: Restrictive ingress rules
- **VPC Endpoints**: Avoid public internet traffic
- **Flow Logs**: VPC Flow Logs to CloudWatch

### Data Protection

- **S3 Versioning**: Disabled for test data (cost optimization)
- **Lifecycle Policies**: Auto-delete after 30 days
- **Backup**: Not required for test environments
- **Destruction**: `RemovalPolicy.DESTROY` for easy cleanup

## Monitoring and Observability

### CloudWatch Dashboards

- **Infrastructure Health**: VPC, ECS, Redshift metrics
- **Cost Tracking**: Daily spend by scenario
- **Test Execution**: ECS task status, Lambda invocations
- **Data Pipeline**: EMR job progress, Glue Crawler runs

### Alarms

- **Cost Anomalies**: Alert if daily cost >$500
- **ECS Task Failures**: Alert on task exit code != 0
- **Redshift Auto-Pause**: Alert if auto-pause fails
- **S3 Bucket Size**: Alert if >60TB (unexpected growth)

## Next Steps

### Immediate (Week 1)

1. ✅ Initialize CDK repository
2. ✅ Implement VPC Stack
3. ✅ Implement Data Lake Stack
4. 🔲 Implement Redshift Stack
5. 🔲 Update AWS account ID in config.yaml
6. 🔲 Deploy to DEV environment
7. 🔲 Generate baseline 1B records

### Short-Term (Weeks 2-4)

1. 🔲 Implement ECS Cluster Stack
2. 🔲 Implement EMR Stack
3. 🔲 Implement Cost Tracker Stack
4. 🔲 Test S01: Token Overflow scenario
5. 🔲 Test S02: Multi-Source Conflicts
6. 🔲 Test S03: Warehouse Context (validate ECS cluster)

### Long-Term (Weeks 5-11)

1. 🔲 Implement remaining scenarios (S11, S13-S16)
2. 🔲 Generate 50TB for S12
3. 🔲 Test S12: Trillion-Record Search
4. 🔲 Collect BEFORE metrics for all scenarios
5. 🔲 Refactor BrightBot multi-agent system
6. 🔲 Re-run all scenarios (AFTER)
7. 🔲 Generate comparison report

## References

- **Jira Ticket**: [BH-107](https://brighthiveio.atlassian.net/browse/BH-107)
- **Brightbot Repo**: `/Users/bado/iccha/brighthive/brightbot`
- **CDK Repository**: `/Users/bado/iccha/brighthive/brighthive_testing_infrastructure_cdk`
- **AWS CDK Docs**: https://docs.aws.amazon.com/cdk/
- **Scenario Files**: `brightbot/scenarios/*.md`

---

**Last Updated**: 2026-01-03
**Status**: In Progress
**Owner**: BrightHive Engineering
