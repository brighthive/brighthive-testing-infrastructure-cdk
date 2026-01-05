"""Data Lake Stack for BrightAgent Load/Stress Infrastructure.

Creates simple S3 bucket for load/stress scenario data.
"""
from aws_cdk import Stack, RemovalPolicy, Duration, CfnOutput
from aws_cdk import aws_s3 as s3
from constructs import Construct


class DataLakeStack(Stack):
    """Simple S3 bucket for test data."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: dict,
        **kwargs,
    ) -> None:
        """Initialize Data Lake Stack.

        Args:
            scope: CDK app or parent stack
            construct_id: Unique identifier for this stack
            config: Environment configuration dict from config.yaml
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        data_lake_config = config["data_lake"]
        environment = config["tags"]["Environment"]

        # Explicit S3 bucket naming - Simple is better than complex
        # Deterministic names for idempotent deployments
        self.data_bucket = s3.Bucket(
            self,
            "DataBucket",
            bucket_name="brightagent-loadstress-data-824267124830",
            versioned=False,
            lifecycle_rules=[
                # Intelligent-Tiering for cost optimization (~40% savings)
                s3.LifecycleRule(
                    id="intelligent-tiering",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INTELLIGENT_TIERING,
                            transition_after=Duration.days(1),
                        )
                    ],
                ),
                # Auto-delete old data after retention period
                s3.LifecycleRule(
                    id="auto-delete-old-data",
                    expiration=Duration.days(data_lake_config["retention_days"]),
                ),
            ],
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # CDK Outputs for scenario integration
        CfnOutput(
            self,
            "DataBucketName",
            value=self.data_bucket.bucket_name,
            description="S3 bucket name for load/stress scenario data",
            export_name=f"{environment}-data-bucket-name",
        )

        CfnOutput(
            self,
            "DataBucketArn",
            value=self.data_bucket.bucket_arn,
            description="S3 bucket ARN for load/stress scenario data",
            export_name=f"{environment}-data-bucket-arn",
        )
