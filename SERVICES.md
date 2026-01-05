# BrightAgent LOADSTRESS - AWS Service URLs

Quick access links to all deployed AWS services in the LOADSTRESS environment.

**Account:** 824267124830 (brighthive-loadstress)
**Region:** us-west-2 (Oregon)
**Environment:** LOADSTRESS

---

## 🔐 Console Login

**IAM User Sign-In:**
```
https://824267124830.signin.aws.amazon.com/console
```

**Credentials:**
- **Username:** `cdk-deploy`
- **Password:** `[REDACTED - Stored in password manager]`
- **⚠️ First Login:** You'll be forced to change password on first use

**Alternative (Account Alias):**
```
https://brighthive-loadstress.signin.aws.amazon.com/console
```
*(Only works if account alias is configured)*

---

## 📊 CloudWatch (Monitoring & Observability)

### Dashboard
**BrightAgent-LOADSTRESS Dashboard:**
```
https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#dashboards:name=BrightAgent-LOADSTRESS
```

### Log Groups
**All Log Groups:**
```
https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#logsV2:log-groups
```

**VPC Flow Logs:**
```
https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#logsV2:log-groups/log-group/$252Faws$252Fvpc$252Fbrightagent-loadstress
```

**Redshift Logs:**
```
https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#logsV2:log-groups/log-group/$252Faws$252Fredshift$252Fbrightagent-loadstress
```

**EMR Serverless Logs:**
```
https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#logsV2:log-groups/log-group/$252Faws$252Femr-serverless$252Fbrightagent-loadstress
```

**ECS/Fargate Logs:**
```
https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#logsV2:log-groups/log-group/$252Faws$252Fecs$252Fbrightagent-loadstress
```

**Application Logs:**
```
https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#logsV2:log-groups/log-group/$252Faws$252Fapplication$252Fbrightagent-loadstress
```

### Alarms
**All CloudWatch Alarms:**
```
https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#alarmsV2:
```

**Alarm History:**
```
https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#alarmsV2:alarm/history
```

---

## 🗂️ CloudFormation (Infrastructure as Code)

**All Stacks:**
```
https://us-west-2.console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks
```

**VPC Stack:**
```
https://us-west-2.console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/stackinfo?stackId=BrightAgent-LOADSTRESS-VPC
```

**DataLake Stack:**
```
https://us-west-2.console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/stackinfo?stackId=BrightAgent-LOADSTRESS-DataLake
```

**Redshift Stack:**
```
https://us-west-2.console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/stackinfo?stackId=BrightAgent-LOADSTRESS-Redshift
```

**EMR Stack:**
```
https://us-west-2.console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/stackinfo?stackId=BrightAgent-LOADSTRESS-EMR
```

**Monitoring Stack:**
```
https://us-west-2.console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/stackinfo?stackId=BrightAgent-LOADSTRESS-Monitoring
```

---

## 🗄️ Redshift (Data Warehouse)

**Clusters:**
```
https://us-west-2.console.aws.amazon.com/redshiftv2/home?region=us-west-2#clusters
```

**BrightAgent-LOADSTRESS Cluster:**
```
https://us-west-2.console.aws.amazon.com/redshiftv2/home?region=us-west-2#cluster-details?cluster=brightagent-loadstress-redshift
```

**Query Editor v2:**
```
https://us-west-2.console.aws.amazon.com/sqlworkbench/home?region=us-west-2
```

**Workload Management (WLM):**
```
https://us-west-2.console.aws.amazon.com/redshiftv2/home?region=us-west-2#cluster-details?cluster=brightagent-loadstress-redshift&tab=configuration
```

**Query Monitoring:**
```
https://us-west-2.console.aws.amazon.com/redshiftv2/home?region=us-west-2#cluster-details?cluster=brightagent-loadstress-redshift&tab=queries-and-loads
```

**Performance Insights:**
```
https://us-west-2.console.aws.amazon.com/redshiftv2/home?region=us-west-2#cluster-details?cluster=brightagent-loadstress-redshift&tab=monitoring
```

---

## ⚡ EMR Serverless (Data Generation)

**Applications:**
```
https://us-west-2.console.aws.amazon.com/emr/home?region=us-west-2#/serverless
```

**BrightAgent-LOADSTRESS Application:**
```
https://us-west-2.console.aws.amazon.com/emr/home?region=us-west-2#/serverless/applications/brightagent-loadstress-datagen
```

**Job Runs:**
```
https://us-west-2.console.aws.amazon.com/emr/home?region=us-west-2#/serverless/applications/brightagent-loadstress-datagen/job-runs
```

---

## 🪣 S3 (Data Lake)

**All Buckets:**
```
https://s3.console.aws.amazon.com/s3/buckets?region=us-west-2
```

**BrightAgent-LOADSTRESS Data Bucket:**
```
https://s3.console.aws.amazon.com/s3/buckets/brightagent-loadstress-data-824267124830?region=us-west-2&tab=objects
```

**Bucket Properties (Lifecycle Rules):**
```
https://s3.console.aws.amazon.com/s3/buckets/brightagent-loadstress-data-824267124830?region=us-west-2&tab=properties
```

**Bucket Metrics:**
```
https://s3.console.aws.amazon.com/s3/buckets/brightagent-loadstress-data-824267124830?region=us-west-2&tab=metrics
```

---

## 🌐 VPC (Networking)

**VPCs:**
```
https://us-west-2.console.aws.amazon.com/vpc/home?region=us-west-2#vpcs:
```

**Subnets:**
```
https://us-west-2.console.aws.amazon.com/vpc/home?region=us-west-2#subnets:
```

**Route Tables:**
```
https://us-west-2.console.aws.amazon.com/vpc/home?region=us-west-2#RouteTables:
```

**NAT Gateways:**
```
https://us-west-2.console.aws.amazon.com/vpc/home?region=us-west-2#NatGateways:
```

**Security Groups:**
```
https://us-west-2.console.aws.amazon.com/vpc/home?region=us-west-2#SecurityGroups:
```

**Network ACLs:**
```
https://us-west-2.console.aws.amazon.com/vpc/home?region=us-west-2#acls:
```

**VPC Flow Logs:**
```
https://us-west-2.console.aws.amazon.com/vpc/home?region=us-west-2#FlowLogs:
```

---

## 🔔 SNS (Notifications)

**Topics:**
```
https://us-west-2.console.aws.amazon.com/sns/v3/home?region=us-west-2#/topics
```

**BrightAgent-LOADSTRESS Alarms Topic:**
```
https://us-west-2.console.aws.amazon.com/sns/v3/home?region=us-west-2#/topic/arn:aws:sns:us-west-2:824267124830:brightagent-loadstress-alarms
```

**Subscriptions:**
```
https://us-west-2.console.aws.amazon.com/sns/v3/home?region=us-west-2#/subscriptions
```

---

## 🔐 IAM (Identity & Access Management)

**Users:**
```
https://console.aws.amazon.com/iam/home#/users
```

**CDK Deploy User:**
```
https://console.aws.amazon.com/iam/home#/users/cdk-deploy
```

**Roles:**
```
https://console.aws.amazon.com/iam/home#/roles
```

**Policies:**
```
https://console.aws.amazon.com/iam/home#/policies
```

---

## 💰 Billing & Cost Management

**Cost Explorer:**
```
https://console.aws.amazon.com/cost-management/home?region=us-west-2#/cost-explorer
```

**Budgets:**
```
https://console.aws.amazon.com/billing/home?region=us-west-2#/budgets
```

**Bills:**
```
https://console.aws.amazon.com/billing/home?region=us-west-2#/bills
```

**Cost Allocation Tags:**
```
https://console.aws.amazon.com/billing/home?region=us-west-2#/tags
```

---

## 🔍 AWS Systems Manager (Parameter Store)

**Parameter Store:**
```
https://us-west-2.console.aws.amazon.com/systems-manager/parameters?region=us-west-2
```

**Session Manager:**
```
https://us-west-2.console.aws.amazon.com/systems-manager/session-manager?region=us-west-2
```

---

## 📈 Service Health & Status

**AWS Health Dashboard:**
```
https://phd.aws.amazon.com/phd/home?region=us-west-2#/dashboard/open-issues
```

**Service Quotas:**
```
https://us-west-2.console.aws.amazon.com/servicequotas/home?region=us-west-2#!/services
```

---

## 🛠️ Quick Actions

### Start EMR Job
1. Go to [EMR Serverless](https://us-west-2.console.aws.amazon.com/emr/home?region=us-west-2#/serverless/applications/brightagent-loadstress-datagen)
2. Click "Submit job run"
3. Configure job settings
4. Monitor in [Job Runs](https://us-west-2.console.aws.amazon.com/emr/home?region=us-west-2#/serverless/applications/brightagent-loadstress-datagen/job-runs)

### Query Redshift
1. Open [Query Editor v2](https://us-west-2.console.aws.amazon.com/sqlworkbench/home?region=us-west-2)
2. Connect to cluster: `brightagent-loadstress-redshift`
3. Database: `brightagent_loadstress`
4. Run queries with WLM queue groups (ETL, analytics, short)

### View Logs
1. Go to [CloudWatch Logs](https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#logsV2:log-groups)
2. Select log group
3. Use Insights for queries
4. Set time range and filters

### Check Costs
1. Open [Cost Explorer](https://console.aws.amazon.com/cost-management/home?region=us-west-2#/cost-explorer)
2. Filter by tag: `Environment=loadstress`
3. Group by service
4. View daily/monthly trends

---

## 📞 Support

**AWS Support Center:**
```
https://console.aws.amazon.com/support/home
```

**Service Health:**
```
https://status.aws.amazon.com/
```

---

**Last Updated:** 2026-01-04
**Managed By:** CDK (Infrastructure as Code)
**Jira Ticket:** [BH-107](https://brighthiveio.atlassian.net/browse/BH-107)
