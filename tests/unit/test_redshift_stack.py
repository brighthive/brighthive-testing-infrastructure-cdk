"""Unit tests for Redshift Stack."""
import os
import aws_cdk as cdk
from aws_cdk.assertions import Template, Match
import pytest

from src.brighthive_loadstress_cdk.stacks.vpc_stack import VPCStack
from src.brighthive_loadstress_cdk.stacks.redshift_stack import RedshiftStack


@pytest.fixture
def test_config():
    """Test configuration for Redshift stack."""
    return {
        "vpc": {
            "cidr": "10.51.0.0/16",
            "max_azs": 3,
            "nat_gateways": 2,
        },
        "redshift": {
            "node_type": "ra3.xlplus",
            "number_of_nodes": 2,
            "database_name": "brightagent_loadstress",
            "master_username": "admin",
        },
        "tags": {
            "Environment": "loadstress",
            "Project": "brightagent-loadstress",
        },
    }


@pytest.fixture
def redshift_stack(test_config, monkeypatch):
    """Create Redshift stack for loadstress."""
    # Mock environment variable for password
    monkeypatch.setenv("REDSHIFT_MASTER_PASSWORD", "TestPassword123")

    app = cdk.App()

    # Create VPC stack first (dependency)
    vpc_stack = VPCStack(
        app,
        "TestVPCStack",
        config=test_config,
        env=cdk.Environment(account="824267124830", region="us-east-1"),
    )

    # Create Redshift stack
    stack = RedshiftStack(
        app,
        "TestRedshiftStack",
        vpc=vpc_stack.vpc,
        config=test_config,
        env=cdk.Environment(account="824267124830", region="us-east-1"),
    )
    return stack


class TestRedshiftStack:
    """Test suite for Redshift Stack."""

    def test_redshift_cluster_created(self, redshift_stack):
        """Test that Redshift cluster is created."""
        template = Template.from_stack(redshift_stack)

        template.resource_count_is("AWS::Redshift::Cluster", 1)

    def test_cluster_has_deterministic_identifier(self, redshift_stack):
        """Test that cluster has deterministic identifier."""
        template = Template.from_stack(redshift_stack)

        template.has_resource_properties(
            "AWS::Redshift::Cluster",
            {
                "ClusterIdentifier": "brightagent-loadstress-redshift",
            },
        )

    def test_cluster_configuration(self, redshift_stack):
        """Test that cluster has correct configuration."""
        template = Template.from_stack(redshift_stack)

        template.has_resource_properties(
            "AWS::Redshift::Cluster",
            {
                "ClusterType": "multi-node",
                "NodeType": "ra3.xlplus",
                "NumberOfNodes": 2,
                "DBName": "brightagent_loadstress",
                "MasterUsername": "admin",
                "PubliclyAccessible": False,
            },
        )

    def test_security_group_created(self, redshift_stack):
        """Test that security group is created."""
        template = Template.from_stack(redshift_stack)

        template.has_resource_properties(
            "AWS::EC2::SecurityGroup",
            {
                "GroupName": "brightagent-loadstress-redshift-sg",
                "GroupDescription": "Redshift cluster security group",
            },
        )

    def test_security_group_ingress_rule(self, redshift_stack):
        """Test that security group has VPC ingress rule."""
        template = Template.from_stack(redshift_stack)

        template.has_resource_properties(
            "AWS::EC2::SecurityGroupIngress",
            {
                "IpProtocol": "tcp",
                "FromPort": 5439,
                "ToPort": 5439,
            },
        )

    def test_subnet_group_created(self, redshift_stack):
        """Test that subnet group is created."""
        template = Template.from_stack(redshift_stack)

        template.has_resource_properties(
            "AWS::Redshift::ClusterSubnetGroup",
            {
                "ClusterSubnetGroupName": "brightagent-loadstress-redshift-subnets",
                "Description": "Redshift subnet group",
            },
        )

    def test_outputs_exist(self, redshift_stack):
        """Test that CDK outputs are created."""
        template = Template.from_stack(redshift_stack)

        outputs = template.find_outputs("*")
        assert "RedshiftClusterEndpoint" in outputs
        assert "RedshiftClusterPort" in outputs
        assert "RedshiftClusterIdentifier" in outputs
        assert "RedshiftDatabaseName" in outputs
        assert "RedshiftMasterUsername" in outputs

    def test_output_exports(self, redshift_stack):
        """Test that outputs have correct export names."""
        template = Template.from_stack(redshift_stack)

        outputs = template.find_outputs("*")

        assert outputs["RedshiftClusterEndpoint"]["Export"]["Name"] == "loadstress-redshift-endpoint"
        assert outputs["RedshiftClusterPort"]["Export"]["Name"] == "loadstress-redshift-port"
        assert outputs["RedshiftClusterIdentifier"]["Export"]["Name"] == "loadstress-redshift-cluster-id"

    def test_password_from_environment_variable(self, monkeypatch):
        """Test that password is required from environment variable."""
        # Remove the environment variable
        monkeypatch.delenv("REDSHIFT_MASTER_PASSWORD", raising=False)

        app = cdk.App()
        vpc_stack = VPCStack(
            app,
            "TestVPCStack",
            config={
                "vpc": {"cidr": "10.51.0.0/16", "max_azs": 3, "nat_gateways": 2},
                "tags": {"Environment": "loadstress"},
            },
            env=cdk.Environment(account="824267124830", region="us-east-1"),
        )

        # Should raise ValueError when password env var is missing
        with pytest.raises(ValueError, match="REDSHIFT_MASTER_PASSWORD"):
            RedshiftStack(
                app,
                "TestRedshiftStack",
                vpc=vpc_stack.vpc,
                config={
                    "redshift": {
                        "node_type": "ra3.xlplus",
                        "number_of_nodes": 2,
                        "database_name": "test",
                        "master_username": "admin",
                    },
                    "tags": {"Environment": "loadstress"},
                },
                env=cdk.Environment(account="824267124830", region="us-east-1"),
            )
