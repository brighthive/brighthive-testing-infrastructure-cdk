"""Unit tests for Data Lake Stack."""
import aws_cdk as cdk
from aws_cdk.assertions import Template, Match
import pytest

from src.brighthive_loadstress_cdk.stacks.data_lake_stack import DataLakeStack


@pytest.fixture
def test_config():
    """Test configuration for Data Lake stack."""
    return {
        "data_lake": {
            "bucket_prefix": "brightagent-loadstress",
            "retention_days": 30,
        },
        "tags": {
            "Environment": "loadstress",
            "Project": "brightagent-loadstress",
        },
    }


@pytest.fixture
def data_lake_stack(test_config):
    """Create Data Lake stack for loadstress."""
    app = cdk.App()
    stack = DataLakeStack(
        app,
        "TestDataLakeStack",
        config=test_config,
        env=cdk.Environment(account="824267124830", region="us-east-1"),
    )
    return stack


class TestDataLakeStack:
    """Test suite for Data Lake Stack."""

    def test_s3_bucket_created(self, data_lake_stack):
        """Test that S3 bucket is created."""
        template = Template.from_stack(data_lake_stack)

        template.resource_count_is("AWS::S3::Bucket", 1)

    def test_s3_bucket_has_deterministic_name(self, data_lake_stack):
        """Test that S3 bucket has deterministic name."""
        template = Template.from_stack(data_lake_stack)

        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "BucketName": "brightagent-loadstress-data-824267124830",
            },
        )

    def test_lifecycle_policy_configured(self, data_lake_stack):
        """Test that lifecycle policy is configured."""
        template = Template.from_stack(data_lake_stack)

        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "LifecycleConfiguration": {
                    "Rules": Match.array_with([
                        Match.object_like({
                            "ExpirationInDays": 30,
                            "Status": "Enabled",
                        })
                    ]),
                },
            },
        )

    def test_bucket_removal_policy(self, data_lake_stack):
        """Test that bucket has delete policy for loadstress."""
        template = Template.from_stack(data_lake_stack)

        # Auto delete should be enabled via custom resource
        template.has_resource_properties(
            "Custom::S3AutoDeleteObjects",
            {
                "ServiceToken": Match.any_value(),
            },
        )

    def test_outputs_exist(self, data_lake_stack):
        """Test that CDK outputs are created."""
        template = Template.from_stack(data_lake_stack)

        outputs = template.find_outputs("*")
        assert "DataBucketName" in outputs
        assert "DataBucketArn" in outputs

    def test_output_exports(self, data_lake_stack):
        """Test that outputs have correct export names."""
        template = Template.from_stack(data_lake_stack)

        outputs = template.find_outputs("*")

        assert outputs["DataBucketName"]["Export"]["Name"] == "loadstress-data-bucket-name"
        assert outputs["DataBucketArn"]["Export"]["Name"] == "loadstress-data-bucket-arn"
