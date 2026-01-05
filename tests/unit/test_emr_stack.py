"""Unit tests for EMR Stack."""
import aws_cdk as cdk
from aws_cdk.assertions import Template, Match
import pytest

from src.brighthive_loadstress_cdk.stacks.data_lake_stack import DataLakeStack
from src.brighthive_loadstress_cdk.stacks.emr_stack import EMRStack


@pytest.fixture
def test_config():
    """Test configuration for EMR stack."""
    return {
        "data_lake": {
            "bucket_prefix": "brightagent-loadstress",
            "retention_days": 30,
        },
        "emr": {
            "release_label": "emr-7.0.0",
            "instance_type": "c6i.4xlarge",
            "instance_count": 10,
        },
        "tags": {
            "Environment": "loadstress",
            "Project": "brightagent-loadstress",
        },
    }


@pytest.fixture
def emr_stack(test_config):
    """Create EMR stack for loadstress."""
    app = cdk.App()

    # Create Data Lake stack first (dependency)
    data_lake_stack = DataLakeStack(
        app,
        "TestDataLakeStack",
        config=test_config,
        env=cdk.Environment(account="824267124830", region="us-east-1"),
    )

    # Create EMR stack
    stack = EMRStack(
        app,
        "TestEMRStack",
        data_bucket=data_lake_stack.data_bucket,
        config=test_config,
        env=cdk.Environment(account="824267124830", region="us-east-1"),
    )
    return stack


class TestEMRStack:
    """Test suite for EMR Stack."""

    def test_emr_application_created(self, emr_stack):
        """Test that EMR Serverless application is created."""
        template = Template.from_stack(emr_stack)

        template.resource_count_is("AWS::EMRServerless::Application", 1)

    def test_application_configuration(self, emr_stack):
        """Test that application has correct configuration."""
        template = Template.from_stack(emr_stack)

        template.has_resource_properties(
            "AWS::EMRServerless::Application",
            {
                "Name": "brightagent-datagen-loadstress",
                "ReleaseLabel": "emr-7.0.0",
                "Type": "SPARK",
            },
        )

    def test_application_capacity_configuration(self, emr_stack):
        """Test that application has correct capacity configuration."""
        template = Template.from_stack(emr_stack)

        template.has_resource_properties(
            "AWS::EMRServerless::Application",
            {
                "InitialCapacity": Match.array_with([
                    Match.object_like({
                        "Key": "Driver",
                        "Value": {
                            "WorkerCount": 1,
                            "WorkerConfiguration": {
                                "Cpu": "4vCPU",
                                "Memory": "16GB",
                            },
                        },
                    }),
                    Match.object_like({
                        "Key": "Executor",
                        "Value": {
                            "WorkerCount": 10,
                            "WorkerConfiguration": {
                                "Cpu": "16vCPU",
                                "Memory": "64GB",
                            },
                        },
                    }),
                ]),
            },
        )

    def test_auto_stop_configuration(self, emr_stack):
        """Test that auto-stop is configured."""
        template = Template.from_stack(emr_stack)

        template.has_resource_properties(
            "AWS::EMRServerless::Application",
            {
                "AutoStopConfiguration": {
                    "Enabled": True,
                    "IdleTimeoutMinutes": 15,
                },
            },
        )

    def test_auto_start_disabled(self, emr_stack):
        """Test that auto-start is disabled for cost control."""
        template = Template.from_stack(emr_stack)

        template.has_resource_properties(
            "AWS::EMRServerless::Application",
            {
                "AutoStartConfiguration": {
                    "Enabled": False,
                },
            },
        )

    def test_iam_role_created(self, emr_stack):
        """Test that IAM execution role is created."""
        template = Template.from_stack(emr_stack)

        template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "RoleName": "brightagent-loadstress-emr-job-role",
                "Description": "Execution role for EMR Serverless data generation jobs",
            },
        )

    def test_iam_role_has_s3_permissions(self, emr_stack):
        """Test that IAM role has S3 permissions."""
        template = Template.from_stack(emr_stack)

        # Check that role has policy for S3 bucket access
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": Match.array_with([
                        Match.object_like({
                            "Action": Match.array_with([
                                Match.string_like_regexp("s3:.*"),
                            ]),
                            "Effect": "Allow",
                        })
                    ]),
                },
            },
        )

    def test_iam_role_has_glue_permissions(self, emr_stack):
        """Test that IAM role has Glue catalog permissions."""
        template = Template.from_stack(emr_stack)

        # Check for Glue permissions policy
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": Match.array_with([
                        Match.object_like({
                            "Action": Match.array_with([
                                "glue:GetDatabase",
                                "glue:GetTable",
                                "glue:GetPartitions",
                                "glue:CreateTable",
                                "glue:UpdateTable",
                                "glue:BatchCreatePartition",
                            ]),
                            "Effect": "Allow",
                        })
                    ]),
                },
            },
        )

    def test_outputs_exist(self, emr_stack):
        """Test that CDK outputs are created."""
        template = Template.from_stack(emr_stack)

        outputs = template.find_outputs("*")
        assert "EMRApplicationId" in outputs
        assert "EMRApplicationArn" in outputs
        assert "EMRJobRoleArn" in outputs

    def test_output_exports(self, emr_stack):
        """Test that outputs have correct export names."""
        template = Template.from_stack(emr_stack)

        outputs = template.find_outputs("*")

        assert outputs["EMRApplicationId"]["Export"]["Name"] == "loadstress-emr-app-id"
        assert outputs["EMRApplicationArn"]["Export"]["Name"] == "loadstress-emr-app-arn"
        assert outputs["EMRJobRoleArn"]["Export"]["Name"] == "loadstress-emr-job-role-arn"
