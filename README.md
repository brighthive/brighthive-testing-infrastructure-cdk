# BrightAgent LOADSTRESS - Loadstress Infrastructure CDK

AWS CDK infrastructure for BrightAgent load/stress loadstress with 16 production scenarios using REAL data at scale.

**Related Jira Ticket:** [BH-107](https://brighthiveio.atlassian.net/browse/BH-107)

## Overview

This repository contains AWS CDK infrastructure for the **LOADSTRESS** environment - a dedicated AWS environment for load and stress loadstress BrightAgent at production scale. The infrastructure recreates 16 production scenarios with real data volumes (up to 1 billion records) to validate performance, scalability, and reliability.

**Environment:** LOADSTRESS
**Region:** us-west-2 (Oregon)
**Account:** 824267124830

### 16 Production Scenarios

#### Core Scenarios (Ready NOW)
1. **S01**: Massive Token Overflow (10B records → 6K tokens)
2. **S02**: Multi-Source Conflict Resolution (3B records, 3 sources)
3. **S06**: Time Travel Queries (historical snapshots)
4. **S08**: Warehouse-Wide Analytics (aggregations)
5. **S14**: Natural Language Query (<5s latency)

#### Advanced Scenarios (Requires ECS/Fargate)
6. **S09**: Real-Time Streaming Ingestion (10K events/sec)
7. **S12**: Distributed Trillion-Record Search (1T records, 50TB)
8. **S15**: PII Detection at Scale (GDPR compliance)

#### Additional Scenarios
9. **S03**: Warehouse Context Generation (1,000 tables)
10. **S04**: Lineage Graph Traversal (50K nodes)
11. **S05**: Quality Score Computation (1B records/hour)
12. **S07**: Join Path Discovery (complex joins)
13. **S10**: Incremental Materialization (delta processing)
14. **S11**: Schema Evolution Detection (50 sources)
15. **S13**: Cross-Asset Insight Discovery
16. **S16**: Zombie Table Detection (cost optimization)

See **[SCENARIO_IMPLEMENTATION_PLAN.md](SCENARIO_IMPLEMENTATION_PLAN.md)** for complete implementation details.

## Quick Start - Deployment

### Prerequisites

1. **AWS CLI v2** - Install from https://aws.amazon.com/cli/
2. **Node.js 18+** - For AWS CDK installation
3. **AWS CDK** - Install globally:
   ```bash
   npm install -g aws-cdk@latest
   ```
4. **AWS Credentials** - Configured for account 824267124830

### 1. Configure AWS Credentials

Create `.env.loadstress` file:

```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-west-2"
export AWS_REGION="us-west-2"
export AWS_ACCOUNT_ID="824267124830"
export REDSHIFT_MASTER_PASSWORD="YourSecurePassword123!"
```

Source the credentials:

```bash
source .env.loadstress
```

### 2. Bootstrap CDK (First Time Only)

```bash
cdk bootstrap aws://824267124830/us-west-2
```

### 3. Deploy Infrastructure

**SUBSET mode** (1M records, 1 Redshift node, 2 EMR workers - ~$35/day):

```bash
./deploy.sh subset
```

**FULL mode** (1B records, 2 Redshift nodes, 20 EMR workers - ~$1,580/day):

```bash
./deploy.sh full
```

This deploys **5 stacks**:
1. **VPC** - Networking (subnets, NAT, security groups)
2. **Data Lake** - S3 bucket with Intelligent-Tiering for cost optimization
3. **Redshift** - Data warehouse cluster with WLM and query monitoring
4. **EMR** - Serverless Spark for data generation (dynamic scaling)
5. **Monitoring** - CloudWatch logs, dashboards, alarms with email notifications

### 4. Confirm Alarm Subscription

CloudWatch alarms are automatically configured to send notifications to **kuri@brighthive.io**.

After deployment, confirm the SNS subscription via the confirmation email sent to this address.

To add additional email addresses:

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-west-2:824267124830:brightagent-loadstress-alarms \
  --protocol email \
  --notification-endpoint additional-email@brighthive.io \
  --region us-west-2
```

## Infrastructure Components

### Deployed Resources

| Stack | Resources | Purpose |
|-------|-----------|---------|
| **VPC** | VPC, 2 public + 2 private subnets, NAT Gateway, Flow Logs | Network isolation |
| **Data Lake** | S3 bucket with Intelligent-Tiering, lifecycle rules | Cost-optimized data storage (~40% savings) |
| **Redshift** | Cluster (1-2 nodes, ra3.xlplus), WLM parameter group, Security group | Data warehouse with query management |
| **EMR** | Serverless application (2-20 workers, dynamic sizing), IAM role | Scalable data generation |
| **Monitoring** | 5 log groups, dashboard, 5 alarms, SNS topic with email | Complete observability |

### Cost Breakdown

**SUBSET Mode** (~$37/day, ~$1,110/month):
- Redshift: 1 × ra3.xlplus = $21.60/day
- NAT Gateway: $1.08/day (+ data transfer)
- S3: ~100MB data = $0.02/day (after Intelligent-Tiering savings)
- EMR: 2 workers × 16vCPU × 64GB (~$10/day when running)
- CloudWatch: ~$80/month for logs
- **Total**: ~$37/day

**FULL Mode** (~$1,580/day, ~$47,400/month):
- Redshift: 2 × ra3.xlplus = $43.20/day
- NAT Gateway: $1.08/day (+ data transfer)
- S3: ~100GB data = $1.40/day (after Intelligent-Tiering ~40% savings)
- EMR: 20 workers × 32vCPU × 128GB (~$180/day when running)
- CloudWatch: ~$200/month for logs
- **Total**: ~$1,580/day

**Performance Improvement**: FULL mode now generates 1B records in 2-3 hours (down from 10+ hours) due to increased EMR capacity.

## Manual CDK Commands

```bash
# Synthesize CloudFormation templates
cdk synth

# List all stacks
cdk list

# View differences with deployed stacks
cdk diff

# Deploy all stacks manually
cdk deploy --all --require-approval never

# Deploy specific stack
cdk deploy BrightAgent-LOADSTRESS-VPC

# Destroy all infrastructure (CAUTION: Deletes all resources!)
cdk destroy --all
```

## Monitoring & Observability

Complete CloudWatch monitoring is configured for all infrastructure components from day one.

### CloudWatch Log Groups (7-day retention)

1. `/aws/vpc/brightagent-loadstress` - VPC Flow Logs
2. `/aws/redshift/brightagent-loadstress` - Redshift query/audit logs
3. `/aws/emr-serverless/brightagent-loadstress` - EMR job execution logs
4. `/aws/ecs/brightagent-loadstress` - ECS/Fargate agent logs (future)
5. `/aws/application/brightagent-loadstress` - Application logs

### CloudWatch Dashboard

Real-time monitoring dashboard: `BrightAgent-LOADSTRESS`

**Widgets:**
- Redshift: CPU utilization, connections, query duration
- S3: Bucket size, object count, request latency
- VPC: Top talkers, rejected traffic (Log Insights queries)

**Access:** https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#dashboards:name=BrightAgent-LOADSTRESS

### CloudWatch Alarms

| Alarm | Threshold | Action |
|-------|-----------|--------|
| Redshift High CPU | CPU > 80% for 10min | SNS → kuri@brighthive.io |
| Redshift High Connections | Connections > 450 (90% max) | SNS → kuri@brighthive.io |
| Redshift Low Disk | Disk usage > 85% | SNS → kuri@brighthive.io |
| Redshift Slow Queries | Query duration > 30s | SNS → kuri@brighthive.io |
| EMR Job Failure | Any job fails | SNS → kuri@brighthive.io |

**SNS Topic:** `brightagent-loadstress-alarms` (automatically subscribed to kuri@brighthive.io)

### Accessing Logs

**AWS Console:**
```bash
# CloudWatch Logs
https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#logsV2:log-groups

# CloudWatch Dashboard
https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#dashboards:name=BrightAgent-LOADSTRESS
```

**AWS CLI:**
```bash
# Tail VPC Flow Logs
aws logs tail /aws/vpc/brightagent-loadstress --follow --region us-west-2

# Tail Redshift Logs
aws logs tail /aws/redshift/brightagent-loadstress --follow --region us-west-2

# Tail EMR Logs
aws logs tail /aws/emr-serverless/brightagent-loadstress --follow --region us-west-2
```

**CloudWatch Insights Queries:**
```bash
# Top 10 slowest queries
fields @timestamp, query, duration
| filter @message like /Query/
| sort duration desc
| limit 10

# Error rate by hour
fields @timestamp, @message
| filter @message like /ERROR/
| stats count() as errors by bin(5m)
```

See **[OBSERVABILITY_GUIDE.md](OBSERVABILITY_GUIDE.md)** for complete monitoring documentation.

## Redshift Optimization

### Workload Management (WLM)

The Redshift cluster is configured with a 3-queue WLM setup for optimal query performance:

| Queue | Memory | Concurrency | Use Case |
|-------|--------|-------------|----------|
| **ETL** | 50% | 3 queries | Data loading, transformations |
| **Analytics** | 35% | 5 queries | Complex analytical queries |
| **Short Query** | 15% | 10 queries | Quick lookups (<60s timeout) |

**Query Monitoring Rules:**
- Abort queries running > 5 minutes
- Log high CPU queries (> 100s CPU time)
- Log disk spill events (temp blocks to disk)

### Optimized Table Schemas

Production-ready table schemas with **DISTKEY** and **SORTKEY** are available in `seed_data/redshift_schemas/`:

**Performance optimizations:**
- Small dimensions (customers, products): `DISTSTYLE ALL` (replicated)
- Large fact tables (orders): `DISTKEY (customer_id)` for co-located joins
- Sort keys optimized for time-series and lookup queries
- Expected performance: **4-9x faster queries**, **4-5x storage compression**

**Deploy schemas:**
```bash
cd seed_data/redshift_schemas
./deploy_schemas.sh
```

See **[seed_data/redshift_schemas/README.md](seed_data/redshift_schemas/README.md)** for complete schema documentation and performance benchmarks.

## Data Generation

After infrastructure is deployed, generate baseline test data:

### 1. Set Environment Variables from Stack Outputs

```bash
# Get EMR application ID
export EMR_APP_ID=$(aws cloudformation describe-stacks \
  --stack-name BrightAgent-LOADSTRESS-EMR \
  --query 'Stacks[0].Outputs[?OutputKey==`EMRApplicationId`].OutputValue' \
  --output text \
  --region us-west-2)

# Get EMR job execution role ARN
export EMR_JOB_ROLE=$(aws cloudformation describe-stacks \
  --stack-name BrightAgent-LOADSTRESS-EMR \
  --query 'Stacks[0].Outputs[?OutputKey==`EMRJobRoleArn`].OutputValue' \
  --output text \
  --region us-west-2)

# Verify variables are set
echo "EMR Application ID: $EMR_APP_ID"
echo "EMR Job Role: $EMR_JOB_ROLE"
```

### 2. Submit Data Generation Job

```bash
# Upload PySpark script to S3
aws s3 cp scenarios/generate_baseline_warehouse.py \
  s3://brightagent-loadstress-data-824267124830/scripts/

# Start EMR job
aws emr-serverless start-job-run \
  --application-id $EMR_APP_ID \
  --execution-role-arn $EMR_JOB_ROLE \
  --job-driver '{
    "sparkSubmit": {
      "entryPoint": "s3://brightagent-loadstress-data-824267124830/scripts/generate_baseline_warehouse.py",
      "sparkSubmitParameters": "--conf spark.executor.cores=4 --conf spark.executor.memory=16g"
    }
  }' \
  --configuration-overrides '{
    "monitoringConfiguration": {
      "cloudWatchLoggingConfiguration": {
        "enabled": true,
        "logGroupName": "/aws/emr-serverless/brightagent-loadstress"
      }
    }
  }' \
  --region us-west-2
```

### 3. Monitor Job Progress

```bash
# Get job run status (replace JOB_RUN_ID with actual ID from previous command output)
export JOB_RUN_ID="00ffnqv30gqvpe09"  # From start-job-run output

aws emr-serverless get-job-run \
  --application-id $EMR_APP_ID \
  --job-run-id $JOB_RUN_ID \
  --region us-west-2

# Tail logs
aws logs tail /aws/emr-serverless/brightagent-loadstress --follow --region us-west-2
```

### 4. Connect to Redshift

```bash
# Get Redshift endpoint
export REDSHIFT_HOST=$(aws cloudformation describe-stacks \
  --stack-name BrightAgent-LOADSTRESS-Redshift \
  --query 'Stacks[0].Outputs[?OutputKey==`RedshiftClusterEndpoint`].OutputValue' \
  --output text \
  --region us-west-2)

# Connect with psql (password required)
source .env.loadstress
psql -h $REDSHIFT_HOST -U admin -d brightagent_loadstress -p 5439
# Enter password when prompted (from REDSHIFT_MASTER_PASSWORD in .env.loadstress)
```

## CDK Development

### Local Development Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Setup Development Environment

```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt
```

### Project Structure

```
brighthive_loadstress_infrastructure_cdk/
├── app.py                          # CDK app entry point
├── config.yaml                     # Environment configuration
├── deploy.sh                       # Deployment script
├── src/
│   └── brighthive_loadstress_cdk/
│       ├── project_settings.py     # Deployment modes & scale config
│       └── stacks/
│           ├── vpc_stack.py        # VPC networking
│           ├── data_lake_stack.py  # S3 data storage
│           ├── redshift_stack.py   # Redshift cluster
│           ├── emr_stack.py        # EMR Serverless
│           └── monitoring_stack.py # CloudWatch observability
├── scenarios/                      # PySpark data generation scripts
│   ├── generate_baseline_warehouse.py
│   └── generate_multi_source.py
├── seed_data/                      # Test data generation
├── tests/                          # CDK unit tests
├── SCENARIO_IMPLEMENTATION_PLAN.md
├── OBSERVABILITY_GUIDE.md
└── README.md
```

### Loadstress CDK Stacks

```bash
# Run CDK unit tests
pytest tests/

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_stacks.py
```

### Code Quality

```bash
# Format code with ruff
ruff format .

# Lint code with ruff
ruff check .

# Type check with mypy
mypy src/
```

### Modifying Infrastructure

1. Edit stack files in `src/brighthive_loadstress_cdk/stacks/`
2. Update `config.yaml` if adding new configuration
3. Test changes locally: `cdk synth`
4. View differences: `cdk diff`
5. Deploy changes: `./deploy.sh subset`

### Adding New Stacks

1. Create new stack file in `src/brighthive_loadstress_cdk/stacks/`
2. Import and instantiate in `app.py`
3. Add configuration to `config.yaml`
4. Add stack outputs for scenario integration
5. Test deployment in SUBSET mode first

## Configuration Management

Environment configuration is managed via `config.yaml`:

```yaml
LOADSTRESS:
  account: "824267124830"
  region: "us-west-2"

  vpc:
    cidr: "10.0.0.0/16"
    max_azs: 2
    nat_gateways: 1

  redshift:
    node_type: "ra3.xlplus"
    number_of_nodes: 1  # Set by deployment_mode
    database_name: "brightagent_loadstress"
    master_username: "admin"

  emr:
    release_label: "emr-7.0.0"
    instance_count: 2  # Set by deployment_mode

  data_lake:
    lifecycle_days: 90

  tags:
    Environment: "LOADSTRESS"
    Project: "BrightAgent"
    ManagedBy: "CDK"

deployment_mode: "subset"  # or "full"
```

**Deployment Modes** (see `src/brighthive_loadstress_cdk/project_settings.py`):

| Mode | Redshift Nodes | EMR Workers | EMR Resources | Data Records | Generation Time | Cost/Day |
|------|----------------|-------------|---------------|--------------|-----------------|----------|
| `subset` | 1 | 2 | 16vCPU × 64GB | 1M (~100MB) | ~10 min | ~$37 |
| `full` | 2 | 20 | 32vCPU × 128GB | 1B (~100GB) | 2-3 hrs | ~$1,580 |

## Troubleshooting

### CDK Bootstrap Errors

If you see "need to perform AWS calls for account X, but no credentials configured":

```bash
# Source credentials
source .env.loadstress

# Verify credentials
aws sts get-caller-identity
```

### Redshift Connection Issues

If unable to connect to Redshift:

1. Verify you're connecting from within the VPC or have VPN access
2. Check security group allows your IP: `brightagent-loadstress-redshift-sg`
3. Verify credentials match environment variables

### EMR Job Failures

Check CloudWatch logs:

```bash
aws logs tail /aws/emr-serverless/brightagent-loadstress --follow --region us-west-2
```

Common issues:
- Insufficient IAM permissions (check EMR job role)
- Invalid S3 paths
- Spark configuration errors

### Stack Deployment Failures

```bash
# View CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name BrightAgent-LOADSTRESS-<StackName> \
  --region us-west-2 \
  --max-items 20

# Roll back failed deployment
cdk destroy BrightAgent-LOADSTRESS-<StackName>
```

## Security Considerations

- **Credentials**: Never commit `.env.loadstress` to version control
- **Redshift Password**: Store securely, rotate regularly
- **VPC**: Redshift is in private subnets, not publicly accessible
- **IAM Roles**: Follow least-privilege principle
- **S3 Buckets**: Block public access enabled
- **CloudWatch Logs**: 7-day retention to minimize data exposure

## Cost Management

### Daily Monitoring

Check current costs:

```bash
# AWS Cost Explorer
https://console.aws.amazon.com/cost-management/home?region=us-west-2#/cost-explorer

# Set budget alerts
https://console.aws.amazon.com/billing/home?region=us-west-2#/budgets
```

### Cost-Saving Tips

1. **Use SUBSET mode for development** (~$35/day vs $1,400/day)
2. **Destroy infrastructure when not in use**: `cdk destroy --all`
3. **Auto-stop EMR** configured (15min idle timeout)
4. **Redshift snapshots** enabled (1-day retention)
5. **S3 lifecycle rules** delete old data after 90 days

## Documentation

- **[SCENARIO_IMPLEMENTATION_PLAN.md](SCENARIO_IMPLEMENTATION_PLAN.md)** - Complete 6-week implementation plan for all 16 scenarios
- **[OBSERVABILITY_GUIDE.md](OBSERVABILITY_GUIDE.md)** - CloudWatch monitoring, logging, and alerting documentation
- **[DATA_GENERATION_APPROACH.md](DATA_GENERATION_APPROACH.md)** - Realistic data generation patterns and best practices
- **[seed_data/redshift_schemas/README.md](seed_data/redshift_schemas/README.md)** - Redshift optimization guide with DISTKEY/SORTKEY
- **[config.yaml](config.yaml)** - Environment configuration reference

## Support

For issues or questions:
- **Jira Ticket**: [BH-107](https://brighthiveio.atlassian.net/browse/BH-107)
- **Author**: Hikuri Chinca
- **Email**: kuri@brighthive.io

## Built With

- **[AWS CDK](https://aws.amazon.com/cdk/)** - Infrastructure as Code
- **[AWS Redshift](https://aws.amazon.com/redshift/)** - Data warehouse
- **[AWS EMR Serverless](https://aws.amazon.com/emr/serverless/)** - Spark job execution
- **[AWS CloudWatch](https://aws.amazon.com/cloudwatch/)** - Monitoring and observability
- **[Python 3.11+](https://www.python.org/)** - CDK language
- **[uv](https://github.com/astral-sh/uv)** - Fast Python package manager
