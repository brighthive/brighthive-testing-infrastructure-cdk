"""Monitoring Stack for BrightAgent Load/Stress Infrastructure.

Comprehensive CloudWatch logging, dashboards, and alarms for all services.
"""
from aws_cdk import Stack, Duration, RemovalPolicy, CfnOutput
from aws_cdk import aws_logs as logs
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sns_subscriptions as sns_subscriptions
from aws_cdk import aws_cloudwatch_actions as cw_actions
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from constructs import Construct


class MonitoringStack(Stack):
    """CloudWatch monitoring, logging, and alerting for all infrastructure."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.IVpc,
        config: dict,
        **kwargs,
    ) -> None:
        """Initialize Monitoring Stack.

        Args:
            scope: CDK app or parent stack
            construct_id: Unique identifier for this stack
            vpc: VPC for flow logs
            config: Environment configuration dict from config.yaml
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        environment = config["tags"]["Environment"]

        # ========================================
        # CloudWatch Log Groups
        # ========================================

        # VPC Flow Logs
        self.vpc_flow_log_group = logs.LogGroup(
            self,
            "VPCFlowLogs",
            log_group_name=f"/aws/vpc/brightagent-loadstress",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Enable VPC Flow Logs
        ec2.FlowLog(
            self,
            "VPCFlowLog",
            resource_type=ec2.FlowLogResourceType.from_vpc(vpc),
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(
                self.vpc_flow_log_group
            ),
            traffic_type=ec2.FlowLogTrafficType.ALL,
        )

        # Redshift Query Logs
        self.redshift_log_group = logs.LogGroup(
            self,
            "RedshiftLogs",
            log_group_name="/aws/redshift/brightagent-loadstress",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # EMR Serverless Logs
        self.emr_log_group = logs.LogGroup(
            self,
            "EMRLogs",
            log_group_name="/aws/emr-serverless/brightagent-loadstress",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ECS/Fargate Logs (for future agent execution)
        self.ecs_log_group = logs.LogGroup(
            self,
            "ECSLogs",
            log_group_name="/aws/ecs/brightagent-loadstress",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Application/Agent Logs
        self.application_log_group = logs.LogGroup(
            self,
            "ApplicationLogs",
            log_group_name="/aws/application/brightagent-loadstress",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ========================================
        # CloudWatch Dashboard
        # ========================================

        self.dashboard = cloudwatch.Dashboard(
            self,
            "Dashboard",
            dashboard_name="BrightAgent-LOADSTRESS",
        )

        # Dashboard Layout
        self.dashboard.add_widgets(
            # Row 1: Overview
            cloudwatch.TextWidget(
                markdown="# BrightAgent Load/Stress Loadstress Dashboard\n"
                "**Environment:** LOADSTRESS | **Region:** us-west-2 | "
                "**Account:** 824267124830",
                width=24,
                height=2,
            ),
            # Row 2: Redshift Metrics
            cloudwatch.GraphWidget(
                title="Redshift - CPU Utilization",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/Redshift",
                        metric_name="CPUUtilization",
                        dimensions_map={
                            "ClusterIdentifier": "brightagent-loadstress-redshift"
                        },
                        statistic="Average",
                        period=Duration.minutes(5),
                    )
                ],
                width=8,
                height=6,
            ),
            cloudwatch.GraphWidget(
                title="Redshift - Database Connections",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/Redshift",
                        metric_name="DatabaseConnections",
                        dimensions_map={
                            "ClusterIdentifier": "brightagent-loadstress-redshift"
                        },
                        statistic="Sum",
                        period=Duration.minutes(5),
                    )
                ],
                width=8,
                height=6,
            ),
            cloudwatch.GraphWidget(
                title="Redshift - Query Duration",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/Redshift",
                        metric_name="QueryDuration",
                        dimensions_map={
                            "ClusterIdentifier": "brightagent-loadstress-redshift"
                        },
                        statistic="Average",
                        period=Duration.minutes(5),
                    )
                ],
                width=8,
                height=6,
            ),
            # Row 3: S3 Metrics
            cloudwatch.GraphWidget(
                title="S3 - Bucket Size",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/S3",
                        metric_name="BucketSizeBytes",
                        dimensions_map={
                            "BucketName": "brightagent-loadstress-data-824267124830",
                            "StorageType": "StandardStorage",
                        },
                        statistic="Average",
                        period=Duration.hours(1),
                    )
                ],
                width=8,
                height=6,
            ),
            cloudwatch.GraphWidget(
                title="S3 - Number of Objects",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/S3",
                        metric_name="NumberOfObjects",
                        dimensions_map={
                            "BucketName": "brightagent-loadstress-data-824267124830",
                            "StorageType": "AllStorageTypes",
                        },
                        statistic="Average",
                        period=Duration.hours(1),
                    )
                ],
                width=8,
                height=6,
            ),
            cloudwatch.GraphWidget(
                title="S3 - Request Latency",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/S3",
                        metric_name="FirstByteLatency",
                        dimensions_map={
                            "BucketName": "brightagent-loadstress-data-824267124830"
                        },
                        statistic="Average",
                        period=Duration.minutes(5),
                    )
                ],
                width=8,
                height=6,
            ),
            # Row 4: VPC Flow Logs
            cloudwatch.LogQueryWidget(
                title="VPC Flow Logs - Top Talkers",
                log_group_names=[self.vpc_flow_log_group.log_group_name],
                query_string="""fields @timestamp, srcAddr, dstAddr, bytes
| stats sum(bytes) as totalBytes by srcAddr
| sort totalBytes desc
| limit 10""",
                width=12,
                height=6,
            ),
            cloudwatch.LogQueryWidget(
                title="VPC Flow Logs - Rejected Traffic",
                log_group_names=[self.vpc_flow_log_group.log_group_name],
                query_string="""fields @timestamp, srcAddr, dstAddr, action
| filter action = "REJECT"
| stats count() by srcAddr
| sort count desc
| limit 10""",
                width=12,
                height=6,
            ),
        )

        # ========================================
        # CloudWatch Alarms
        # ========================================

        # SNS Topic for Alarms
        self.alarm_topic = sns.Topic(
            self,
            "AlarmTopic",
            topic_name="brightagent-loadstress-alarms",
            display_name="BrightAgent LOADSTRESS Alarms",
        )

        # Subscribe email to alarm topic
        # Get email from config or use default
        alarm_email = config.get("monitoring", {}).get("alarm_email", "kuri@brighthive.io")
        self.alarm_topic.add_subscription(
            sns_subscriptions.EmailSubscription(alarm_email)
        )

        # Redshift High CPU Alarm
        redshift_cpu_alarm = cloudwatch.Alarm(
            self,
            "RedshiftHighCPU",
            alarm_name="brightagent-loadstress-redshift-high-cpu",
            alarm_description="Redshift CPU > 80% for 10 minutes",
            metric=cloudwatch.Metric(
                namespace="AWS/Redshift",
                metric_name="CPUUtilization",
                dimensions_map={
                    "ClusterIdentifier": "brightagent-loadstress-redshift"
                },
                statistic="Average",
                period=Duration.minutes(5),
            ),
            threshold=80,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        )
        redshift_cpu_alarm.add_alarm_action(cw_actions.SnsAction(self.alarm_topic))

        # Redshift High Connections Alarm
        redshift_connections_alarm = cloudwatch.Alarm(
            self,
            "RedshiftHighConnections",
            alarm_name="brightagent-loadstress-redshift-high-connections",
            alarm_description="Redshift connections > 90% of max",
            metric=cloudwatch.Metric(
                namespace="AWS/Redshift",
                metric_name="DatabaseConnections",
                dimensions_map={
                    "ClusterIdentifier": "brightagent-loadstress-redshift"
                },
                statistic="Maximum",
                period=Duration.minutes(5),
            ),
            threshold=450,  # 90% of 500 max connections
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        )
        redshift_connections_alarm.add_alarm_action(
            cw_actions.SnsAction(self.alarm_topic)
        )

        # Redshift Disk Space Alarm
        redshift_disk_alarm = cloudwatch.Alarm(
            self,
            "RedshiftLowDisk",
            alarm_name="brightagent-loadstress-redshift-low-disk",
            alarm_description="Redshift disk usage > 85%",
            metric=cloudwatch.Metric(
                namespace="AWS/Redshift",
                metric_name="PercentageDiskSpaceUsed",
                dimensions_map={
                    "ClusterIdentifier": "brightagent-loadstress-redshift"
                },
                statistic="Average",
                period=Duration.minutes(5),
            ),
            threshold=85,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        )
        redshift_disk_alarm.add_alarm_action(cw_actions.SnsAction(self.alarm_topic))

        # Redshift Slow Query Alarm
        redshift_slow_query_alarm = cloudwatch.Alarm(
            self,
            "RedshiftSlowQueries",
            alarm_name="brightagent-loadstress-redshift-slow-queries",
            alarm_description="Queries taking >30s - potential bottleneck",
            metric=cloudwatch.Metric(
                namespace="AWS/Redshift",
                metric_name="QueryDuration",
                dimensions_map={
                    "ClusterIdentifier": "brightagent-loadstress-redshift",
                    "latency": "long"
                },
                statistic="Maximum",
                period=Duration.minutes(5),
            ),
            threshold=30000,  # 30 seconds in milliseconds
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        )
        redshift_slow_query_alarm.add_alarm_action(cw_actions.SnsAction(self.alarm_topic))

        # EMR Job Failure Alarm (CRITICAL for data generation)
        # Note: Requires EMR to publish metrics - will alarm if any job fails
        emr_failure_alarm = cloudwatch.Alarm(
            self,
            "EMRJobFailure",
            alarm_name="brightagent-loadstress-emr-job-failed",
            alarm_description="EMR Serverless job failed - data generation blocked",
            metric=cloudwatch.Metric(
                namespace="AWS/EMRServerless",
                metric_name="JobsFailed",
                dimensions_map={
                    "ApplicationName": "brightagent-loadstress-datagen"
                },
                statistic="Sum",
                period=Duration.minutes(5),
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        emr_failure_alarm.add_alarm_action(cw_actions.SnsAction(self.alarm_topic))

        # ========================================
        # CloudWatch Insights Queries
        # ========================================

        # Create Log Group Queries (stored for quick access)
        self.create_log_insights_queries()

        # ========================================
        # CDK Outputs
        # ========================================

        CfnOutput(
            self,
            "DashboardURL",
            value=f"https://console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name=BrightAgent-LOADSTRESS",
            description="CloudWatch Dashboard URL",
            export_name="loadstress-dashboard-url",
        )

        CfnOutput(
            self,
            "VPCFlowLogGroup",
            value=self.vpc_flow_log_group.log_group_name,
            description="VPC Flow Logs log group",
            export_name="loadstress-vpc-flow-log-group",
        )

        CfnOutput(
            self,
            "RedshiftLogGroup",
            value=self.redshift_log_group.log_group_name,
            description="Redshift logs log group",
            export_name="loadstress-redshift-log-group",
        )

        CfnOutput(
            self,
            "EMRLogGroup",
            value=self.emr_log_group.log_group_name,
            description="EMR Serverless logs log group",
            export_name="loadstress-emr-log-group",
        )

        CfnOutput(
            self,
            "ECSLogGroup",
            value=self.ecs_log_group.log_group_name,
            description="ECS/Fargate logs log group",
            export_name="loadstress-ecs-log-group",
        )

        CfnOutput(
            self,
            "ApplicationLogGroup",
            value=self.application_log_group.log_group_name,
            description="Application/Agent logs log group",
            export_name="loadstress-application-log-group",
        )

        CfnOutput(
            self,
            "AlarmTopicArn",
            value=self.alarm_topic.topic_arn,
            description="SNS topic ARN for CloudWatch alarms",
            export_name="loadstress-alarm-topic-arn",
        )

    def create_log_insights_queries(self) -> None:
        """Create pre-defined CloudWatch Insights queries for common analysis."""
        # Note: CDK doesn't have L2 construct for QueryDefinition yet
        # These are documented for manual creation in the console

        queries = {
            "Top 10 Slowest Queries": """fields @timestamp, query, duration
| filter @message like /Query/
| sort duration desc
| limit 10""",
            "Error Rate by Hour": """fields @timestamp, @message
| filter @message like /ERROR/
| stats count() as errors by bin(5m)""",
            "Agent Execution Timeline": """fields @timestamp, agent_id, scenario, status
| filter scenario like /S/
| sort @timestamp desc""",
            "Data Generation Progress": """fields @timestamp, records_processed, total_records
| filter job_type = "data_generation"
| stats max(records_processed) as progress by bin(1m)""",
        }

        # Log the queries for documentation
        print("\n=== CloudWatch Insights Queries ===")
        for name, query in queries.items():
            print(f"\n{name}:")
            print(query)
        print("\n===================================\n")
