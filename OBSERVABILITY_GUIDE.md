# BrightAgent LOADSTRESS - Observability & Monitoring Guide

**Complete CloudWatch logging, monitoring, and alerting for all infrastructure components**

---

## 📊 CloudWatch Log Groups

All services are configured to send logs to dedicated CloudWatch Log Groups with 7-day retention:

### 1. VPC Flow Logs
**Log Group:** `/aws/vpc/brightagent-loadstress`
- **Purpose**: Network traffic analysis, security monitoring
- **Contains**: All VPC traffic (ACCEPT/REJECT), source/dest IPs, bytes transferred
- **Use Cases**:
  - Identify top talkers (bandwidth usage)
  - Detect rejected traffic (security)
  - Network troubleshooting

**Example Query** (CloudWatch Insights):
```
fields @timestamp, srcAddr, dstAddr, bytes, action
| filter action = "REJECT"
| stats count() by srcAddr
| sort count desc
| limit 10
```

---

### 2. Redshift Cluster Logs
**Log Group:** `/aws/redshift/brightagent-loadstress`
- **Purpose**: Query performance, audit logging
- **Contains**: Connection logs, user activity, query execution
- **Use Cases**:
  - Slow query analysis
  - User activity auditing
  - Query optimization

**Example Query**:
```
fields @timestamp, query, duration, database
| filter duration > 5000
| sort duration desc
| limit 20
```

---

### 3. EMR Serverless Logs
**Log Group:** `/aws/emr-serverless/brightagent-loadstress`
- **Purpose**: Data generation job monitoring
- **Contains**: Spark job logs, task execution, errors
- **Use Cases**:
  - Job failure debugging
  - Performance tuning
  - Progress tracking

**Example Query**:
```
fields @timestamp, @message
| filter @message like /ERROR/
| stats count() as errors by bin(5m)
```

**Submitting jobs with CloudWatch logging**:
```bash
# Set variables from stack outputs (see Data Generation section in README.md)
export EMR_APP_ID=$(aws cloudformation describe-stacks \
  --stack-name BrightAgent-LOADSTRESS-EMR \
  --query 'Stacks[0].Outputs[?OutputKey==`EMRApplicationId`].OutputValue' \
  --output text --region us-west-2)

export EMR_JOB_ROLE=$(aws cloudformation describe-stacks \
  --stack-name BrightAgent-LOADSTRESS-EMR \
  --query 'Stacks[0].Outputs[?OutputKey==`EMRJobRoleArn`].OutputValue' \
  --output text --region us-west-2)

# Submit job
aws emr-serverless start-job-run \
  --application-id $EMR_APP_ID \
  --execution-role-arn $EMR_JOB_ROLE \
  --job-driver '{
    "sparkSubmit": {
      "entryPoint": "s3://brightagent-loadstress-data-824267124830/scripts/job.py"
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

---

### 4. ECS/Fargate Agent Logs
**Log Group:** `/aws/ecs/brightagent-loadstress`
- **Purpose**: BrightAgent container logs (future use)
- **Contains**: Agent execution logs, scenario results, errors
- **Use Cases**:
  - Agent debugging
  - Scenario execution tracking
  - Error analysis

---

### 5. Application Logs
**Log Group:** `/aws/application/brightagent-loadstress`
- **Purpose**: General application and orchestration logs
- **Contains**: Scenario orchestrator, test runner, utilities
- **Use Cases**:
  - End-to-end test execution tracking
  - Orchestration debugging

---

## 📈 CloudWatch Dashboard

**Dashboard Name:** `BrightAgent-LOADSTRESS`
**URL**: https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#dashboards:name=BrightAgent-LOADSTRESS

### Widgets Included:

#### **Row 1: Overview**
- Environment summary text (LOADSTRESS, us-west-2, account ID)

#### **Row 2: Redshift Performance**
1. **CPU Utilization** (5-minute average)
   - Metric: `AWS/Redshift/CPUUtilization`
   - Alarm Threshold: 80%

2. **Database Connections** (5-minute sum)
   - Metric: `AWS/Redshift/DatabaseConnections`
   - Alarm Threshold: 450 (90% of max 500)

3. **Query Duration** (5-minute average)
   - Metric: `AWS/Redshift/QueryDuration`
   - Track slow queries

#### **Row 3: S3 Storage**
1. **Bucket Size** (hourly average)
   - Metric: `AWS/S3/BucketSizeBytes`
   - Track data growth (baseline: ~100GB for 1B records)

2. **Number of Objects** (hourly average)
   - Metric: `AWS/S3/NumberOfObjects`

3. **Request Latency** (5-minute average)
   - Metric: `AWS/S3/FirstByteLatency`
   - Monitor S3 performance

#### **Row 4: VPC Network Analysis**
1. **Top Talkers** (Log Insights query)
   - Shows top 10 source IPs by bytes transferred

2. **Rejected Traffic** (Log Insights query)
   - Shows security group denials

---

## 🚨 CloudWatch Alarms

All alarms send notifications to SNS topic: `brightagent-loadstress-alarms` → **kuri@brighthive.io** (auto-subscribed)

### 1. Redshift High CPU
**Alarm Name:** `brightagent-loadstress-redshift-high-cpu`
- **Threshold**: CPU > 80% for 10 minutes (2 × 5min periods)
- **Action**: SNS notification to kuri@brighthive.io
- **Resolution**:
  - Check running queries via WLM console
  - Review slow queries in CloudWatch Logs
  - Consider scaling to more nodes
  - Optimize queries using EXPLAIN

### 2. Redshift High Connections
**Alarm Name:** `brightagent-loadstress-redshift-high-connections`
- **Threshold**: Connections > 450 (90% of max)
- **Action**: SNS notification to kuri@brighthive.io
- **Resolution**:
  - Check WLM queues for queued queries
  - Identify connection leaks
  - Implement connection pooling
  - Scale cluster if needed

### 3. Redshift Low Disk Space
**Alarm Name:** `brightagent-loadstress-redshift-low-disk`
- **Threshold**: Disk usage > 85%
- **Action**: SNS notification to kuri@brighthive.io
- **Resolution**:
  - Run VACUUM to reclaim space
  - Delete old data
  - Add more nodes
  - Check table compression (ANALYZE)

### 4. Redshift Slow Queries (NEW)
**Alarm Name:** `brightagent-loadstress-redshift-slow-queries`
- **Threshold**: Query duration > 30 seconds
- **Action**: SNS notification to kuri@brighthive.io
- **Resolution**:
  - Review query in CloudWatch Logs
  - Check if SORTKEY/DISTKEY are optimal
  - Run EXPLAIN to identify bottlenecks
  - Consider WLM queue adjustments
  - Check for disk spill (temp blocks to disk)

### 5. EMR Job Failure (NEW)
**Alarm Name:** `brightagent-loadstress-emr-job-failed`
- **Threshold**: Any EMR Serverless job fails
- **Action**: SNS notification to kuri@brighthive.io
- **Resolution**:
  - Check EMR job logs in CloudWatch
  - Review Spark executor failures
  - Verify S3 permissions and paths
  - Check data format compatibility
  - Consider increasing EMR resources

---

## ⚙️ Redshift Workload Management (WLM)

The Redshift cluster uses a 3-queue WLM configuration for optimal query performance and resource management.

### WLM Queue Configuration

| Queue | Memory % | Concurrency | Timeout | Use Case |
|-------|----------|-------------|---------|----------|
| **ETL** | 50% | 3 queries | None | Data loading, large transformations |
| **Analytics** | 35% | 5 queries | None | Complex analytical queries, aggregations |
| **Short Query** | 15% | 10 queries | 60 seconds | Quick lookups, metadata queries |

### Query Monitoring Rules (QMR)

1. **Abort Long Queries**
   - **Condition**: Query execution time > 5 minutes (300,000 ms)
   - **Action**: Abort query automatically
   - **Purpose**: Prevent runaway queries from consuming resources

2. **Log High CPU Queries**
   - **Condition**: Query CPU time > 100 seconds (100,000 ms)
   - **Action**: Log to CloudWatch
   - **Purpose**: Identify CPU-intensive queries for optimization

3. **Log Disk Spill**
   - **Condition**: Temp blocks to disk > 100,000
   - **Action**: Log to CloudWatch
   - **Purpose**: Identify queries exceeding memory allocation

### Using WLM Queues

Assign queries to specific queues using query groups:

```sql
-- ETL queue (50% memory, 3 concurrent)
SET query_group TO 'etl';
COPY customers FROM 's3://bucket/data/'
IAM_ROLE 'role-arn' FORMAT AS PARQUET;

-- Analytics queue (35% memory, 5 concurrent)
SET query_group TO 'analytics';
SELECT customer_segment, SUM(order_amount)
FROM orders
WHERE order_date >= '2023-01-01'
GROUP BY customer_segment;

-- Short query queue (15% memory, 10 concurrent, 60s timeout)
SET query_group TO 'short';
SELECT COUNT(*) FROM customers;

-- Reset to default queue
RESET query_group;
```

### Monitoring WLM Performance

```sql
-- Check current queue utilization
SELECT service_class AS queue_id,
       num_executed_queries,
       num_queued_queries,
       num_executing_queries
FROM stv_wlm_service_class_state
ORDER BY queue_id;

-- View recent query queue assignments
SELECT query, queue_start_time, queue_end_time,
       exec_start_time, exec_end_time,
       (exec_end_time - exec_start_time)/1000000 AS exec_seconds
FROM stl_wlm_query
WHERE userid > 1
ORDER BY queue_start_time DESC
LIMIT 20;
```

### WLM Best Practices

1. **Route queries appropriately**:
   - ETL: Use for COPY, UNLOAD, large DELETE/UPDATE
   - Analytics: Use for SELECT with aggregations, JOINs
   - Short: Use for metadata queries, quick lookups

2. **Monitor queue wait times**:
   - If queries wait in queue frequently, increase concurrency
   - If queries are slow, reduce concurrency to increase memory per query

3. **Adjust based on workload**:
   - Development/testing: Favor short query queue
   - Production ETL: Favor ETL queue
   - Ad-hoc analysis: Favor analytics queue

---

## 🔍 Pre-Defined CloudWatch Insights Queries

### 1. Top 10 Slowest Queries
```
fields @timestamp, query, duration
| filter @message like /Query/
| sort duration desc
| limit 10
```

### 2. Error Rate by Hour
```
fields @timestamp, @message
| filter @message like /ERROR/
| stats count() as errors by bin(5m)
```

### 3. Agent Execution Timeline
```
fields @timestamp, agent_id, scenario, status
| filter scenario like /S/
| sort @timestamp desc
```

### 4. Data Generation Progress
```
fields @timestamp, records_processed, total_records
| filter job_type = "data_generation"
| stats max(records_processed) as progress by bin(1m)
```

---

## 📧 Alarm Notifications

### Primary Email (Auto-Configured)

Email notifications are **automatically configured** to send to **kuri@brighthive.io**.

After deployment, confirm the SNS subscription by clicking the confirmation link in the email.

### Adding Additional Email Subscribers

```bash
# Subscribe additional email to alarm topic
aws sns subscribe \
  --topic-arn arn:aws:sns:us-west-2:824267124830:brightagent-loadstress-alarms \
  --protocol email \
  --notification-endpoint additional-email@brighthive.io \
  --region us-west-2

# Confirm subscription via email link
```

### Option 2: Slack Notifications

```bash
# Create AWS Chatbot for Slack integration
# 1. Go to AWS Chatbot console
# 2. Configure Slack workspace
# 3. Subscribe channel to SNS topic: brightagent-loadstress-alarms
```

### Option 3: PagerDuty

```bash
# Get PagerDuty integration endpoint
PAGERDUTY_ENDPOINT="https://events.pagerduty.com/integration/xxx/enqueue"

# Subscribe PagerDuty to SNS topic
aws sns subscribe \
  --topic-arn arn:aws:sns:us-west-2:824267124830:brightagent-loadstress-alarms \
  --protocol https \
  --notification-endpoint $PAGERDUTY_ENDPOINT \
  --region us-west-2
```

---

## 📝 Accessing Logs

### Via AWS Console

1. **CloudWatch Logs**: https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#logsV2:log-groups
2. **CloudWatch Dashboard**: https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#dashboards:name=BrightAgent-LOADSTRESS
3. **CloudWatch Alarms**: https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#alarmsV2:

### Via AWS CLI

```bash
# Tail VPC Flow Logs
aws logs tail /aws/vpc/brightagent-loadstress \
  --follow \
  --region us-west-2

# Tail Redshift Logs
aws logs tail /aws/redshift/brightagent-loadstress \
  --follow \
  --region us-west-2

# Tail EMR Logs
aws logs tail /aws/emr-serverless/brightagent-loadstress \
  --follow \
  --region us-west-2

# Query logs with CloudWatch Insights
aws logs start-query \
  --log-group-name /aws/vpc/brightagent-loadstress \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /REJECT/ | limit 20' \
  --region us-west-2
```

---

## 🎯 Common Monitoring Scenarios

### Scenario 1: Debugging Failed EMR Job

```bash
# Set EMR_APP_ID if not already set (see EMR Serverless section above)
export EMR_APP_ID=$(aws cloudformation describe-stacks \
  --stack-name BrightAgent-LOADSTRESS-EMR \
  --query 'Stacks[0].Outputs[?OutputKey==`EMRApplicationId`].OutputValue' \
  --output text --region us-west-2)

# 1. Get recent EMR job runs
aws emr-serverless list-job-runs \
  --application-id $EMR_APP_ID \
  --region us-west-2

# 2. Check logs for specific job
aws logs filter-log-events \
  --log-group-name /aws/emr-serverless/brightagent-loadstress \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '1 hour ago' +%s000) \
  --region us-west-2
```

### Scenario 2: Identifying Slow Redshift Queries

```bash
# CloudWatch Insights query
aws logs start-query \
  --log-group-name /aws/redshift/brightagent-loadstress \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string 'fields @timestamp, query, duration | filter duration > 5000 | sort duration desc | limit 10' \
  --region us-west-2
```

### Scenario 3: Network Traffic Analysis

```bash
# Top bandwidth consumers
aws logs start-query \
  --log-group-name /aws/vpc/brightagent-loadstress \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string 'stats sum(bytes) as totalBytes by srcAddr | sort totalBytes desc | limit 10' \
  --region us-west-2
```

---

## 💰 Cost Monitoring

### CloudWatch Costs

**Log Ingestion**: $0.50 per GB ingested
**Log Storage**: $0.03 per GB per month
**Dashboards**: First 3 dashboards free, $3/month each after
**Alarms**: First 10 free, $0.10/month each after
**Insights Queries**: $0.005 per GB scanned

**Estimated Monthly Cost** (SUBSET mode):
- Log Ingestion: ~5GB/day × 30 × $0.50 = $75
- Log Storage: ~150GB × $0.03 = $4.50
- Dashboard: Free (1 dashboard)
- Alarms: Free (3 alarms)
- **Total**: ~$80/month

**Retention Strategy**:
- Keep logs for 7 days (configurable)
- Export important logs to S3 for long-term storage
- Use S3 Glacier for compliance archives

---

## 🔧 Troubleshooting

### Issue: Logs not appearing in CloudWatch

**Cause**: IAM permissions or misconfiguration

**Solution**:
```bash
# Set variables if not already set
export EMR_APP_ID=$(aws cloudformation describe-stacks \
  --stack-name BrightAgent-LOADSTRESS-EMR \
  --query 'Stacks[0].Outputs[?OutputKey==`EMRApplicationId`].OutputValue' \
  --output text --region us-west-2)

export JOB_RUN_ID="00ffnqv30gqvpe09"  # From your job submission output

# Check EMR job run configuration
aws emr-serverless get-job-run \
  --application-id $EMR_APP_ID \
  --job-run-id $JOB_RUN_ID \
  --region us-west-2

# Verify IAM role has CloudWatch permissions
aws iam get-role-policy \
  --role-name brightagent-loadstress-emr-job-role \
  --policy-name EMRJobRoleDefaultPolicy \
  --region us-west-2
```

### Issue: Dashboard not showing metrics

**Cause**: Metrics have no data or wrong time range

**Solution**:
- Wait 5-15 minutes for metrics to populate
- Check time range (default is last 3 hours)
- Verify resources are running and generating metrics

---

## 📚 Additional Resources

- **AWS CloudWatch Documentation**: https://docs.aws.amazon.com/cloudwatch/
- **CloudWatch Insights Syntax**: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html
- **Redshift Logging**: https://docs.aws.amazon.com/redshift/latest/mgmt/db-auditing.html
- **EMR Serverless Monitoring**: https://docs.aws.amazon.com/emr/latest/EMR-Serverless-UserGuide/logging.html

---

**All monitoring configured!** 🎉 Ready for full observability from day one.
