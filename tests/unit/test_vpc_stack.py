"""Unit tests for VPC Stack."""
import aws_cdk as cdk
from aws_cdk.assertions import Template, Match
import pytest

from src.brighthive_loadstress_cdk.stacks.vpc_stack import VPCStack


@pytest.fixture
def test_config():
    """Test configuration for VPC stack."""
    return {
        "vpc": {
            "cidr": "10.51.0.0/16",
            "max_azs": 3,
            "nat_gateways": 2,
        },
        "tags": {
            "Environment": "loadstress",
            "Project": "brightagent-loadstress",
        },
    }


@pytest.fixture
def vpc_stack(test_config):
    """Create VPC stack for loadstress."""
    app = cdk.App()
    stack = VPCStack(
        app,
        "TestVPCStack",
        config=test_config,
        env=cdk.Environment(account="824267124830", region="us-east-1"),
    )
    return stack


class TestVPCStack:
    """Test suite for VPC Stack."""

    def test_vpc_created(self, vpc_stack):
        """Test that VPC is created with correct CIDR."""
        template = Template.from_stack(vpc_stack)

        template.has_resource_properties(
            "AWS::EC2::VPC",
            {
                "CidrBlock": "10.51.0.0/16",
                "EnableDnsHostnames": True,
                "EnableDnsSupport": True,
            },
        )

    def test_vpc_has_correct_name(self, vpc_stack):
        """Test that VPC has deterministic name."""
        template = Template.from_stack(vpc_stack)

        template.has_resource_properties(
            "AWS::EC2::VPC",
            {
                "Tags": Match.array_with([
                    {"Key": "Name", "Value": "brightagent-loadstress-vpc"}
                ]),
            },
        )

    def test_private_subnets_created(self, vpc_stack):
        """Test that private subnets are created."""
        template = Template.from_stack(vpc_stack)

        # Should have private subnets (3 AZs)
        template.resource_count_is("AWS::EC2::Subnet", 6)  # 3 private + 3 public

    def test_nat_gateways_created(self, vpc_stack):
        """Test that NAT gateways are created."""
        template = Template.from_stack(vpc_stack)

        # Should have 2 NAT gateways as configured
        template.resource_count_is("AWS::EC2::NatGateway", 2)

    def test_outputs_exist(self, vpc_stack):
        """Test that CDK outputs are created."""
        template = Template.from_stack(vpc_stack)

        # Check that outputs are present
        outputs = template.find_outputs("*")
        assert "VpcId" in outputs
        assert "PrivateSubnetIds" in outputs
        assert "PublicSubnetIds" in outputs

    def test_output_exports(self, vpc_stack):
        """Test that outputs have correct export names."""
        template = Template.from_stack(vpc_stack)

        outputs = template.find_outputs("*")

        assert outputs["VpcId"]["Export"]["Name"] == "loadstress-vpc-id"
        assert outputs["PrivateSubnetIds"]["Export"]["Name"] == "loadstress-private-subnet-ids"
        assert outputs["PublicSubnetIds"]["Export"]["Name"] == "loadstress-public-subnet-ids"
