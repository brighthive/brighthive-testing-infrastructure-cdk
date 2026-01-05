"""EMR Stack for BrightAgent Load/Stress Infrastructure.

Creates EMR Serverless application for massive load/stress data generation.
"""
from aws_cdk import Stack, CfnOutput
from aws_cdk import aws_emrserverless as emr
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from constructs import Construct


class EMRStack(Stack):
    """EMR Serverless for data generation jobs."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        data_bucket: s3.IBucket,
        config: dict,
        **kwargs,
    ) -> None:
        """Initialize EMR Stack.

        Args:
            scope: CDK app or parent stack
            construct_id: Unique identifier for this stack
            data_bucket: S3 bucket for input/output data
            config: Environment configuration dict from config.yaml
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        emr_config = config["emr"]
        environment = config["tags"]["Environment"]

        # Explicit IAM role naming - Flat is better than nested
        self.job_role = iam.Role(
            self,
            "EMRJobRole",
            role_name="brightagent-loadstress-emr-job-role",
            assumed_by=iam.ServicePrincipal("emr-serverless.amazonaws.com"),
            description="Execution role for EMR Serverless data generation jobs",
        )

        # Grant S3 permissions for data bucket
        data_bucket.grant_read_write(self.job_role)

        # Grant Glue permissions for catalog access
        self.job_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "glue:GetDatabase",
                    "glue:GetTable",
                    "glue:GetPartitions",
                    "glue:CreateTable",
                    "glue:UpdateTable",
                    "glue:BatchCreatePartition",
                ],
                resources=[
                    f"arn:aws:glue:{self.region}:{self.account}:catalog",
                    f"arn:aws:glue:{self.region}:{self.account}:database/*",
                    f"arn:aws:glue:{self.region}:{self.account}:table/*",
                ],
            )
        )

        # EMR Serverless Application for Spark jobs
        self.application = emr.CfnApplication(
            self,
            "DataGenApplication",
            name="brightagent-loadstress-datagen",
            release_label=emr_config["release_label"],
            type="SPARK",
            initial_capacity=[
                emr.CfnApplication.InitialCapacityConfigKeyValuePairProperty(
                    key="Driver",
                    value=emr.CfnApplication.InitialCapacityConfigProperty(
                        worker_count=1,
                        worker_configuration=emr.CfnApplication.WorkerConfigurationProperty(
                            cpu="4vCPU",
                            memory="16GB",
                        ),
                    ),
                ),
                emr.CfnApplication.InitialCapacityConfigKeyValuePairProperty(
                    key="Executor",
                    value=emr.CfnApplication.InitialCapacityConfigProperty(
                        worker_count=emr_config["instance_count"],
                        worker_configuration=emr.CfnApplication.WorkerConfigurationProperty(
                            cpu=emr_config["worker_cpu"],
                            memory=emr_config["worker_memory"],
                        ),
                    ),
                ),
            ],
            maximum_capacity=emr.CfnApplication.MaximumAllowedResourcesProperty(
                cpu="800vCPU",  # Supports FULL mode: 20 workers × 32vCPU = 640 vCPU
                memory="3200GB",  # Supports FULL mode: 20 workers × 128GB = 2,560 GB
            ),
            auto_start_configuration=emr.CfnApplication.AutoStartConfigurationProperty(
                enabled=False  # Manual start for cost control
            ),
            auto_stop_configuration=emr.CfnApplication.AutoStopConfigurationProperty(
                enabled=True,
                idle_timeout_minutes=15,  # Auto-stop after 15 min idle
            ),
        )

        # CDK Outputs for scenario integration
        CfnOutput(
            self,
            "EMRApplicationId",
            value=self.application.attr_application_id,
            description="EMR Serverless application ID for data generation",
            export_name=f"{environment}-emr-app-id",
        )

        CfnOutput(
            self,
            "EMRApplicationArn",
            value=self.application.attr_arn,
            description="EMR Serverless application ARN",
            export_name=f"{environment}-emr-app-arn",
        )

        CfnOutput(
            self,
            "EMRJobRoleArn",
            value=self.job_role.role_arn,
            description="IAM role ARN for EMR job execution",
            export_name=f"{environment}-emr-job-role-arn",
        )

        CfnOutput(
            self,
            "EMRLogGroup",
            value="/aws/emr-serverless/brightagent-loadstress",
            description="CloudWatch log group for EMR job logs",
            export_name=f"{environment}-emr-log-group-name",
        )
