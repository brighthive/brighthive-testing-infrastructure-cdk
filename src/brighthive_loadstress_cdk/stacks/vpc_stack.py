"""VPC Stack for BrightAgent Load/Stress Infrastructure.

Creates isolated VPC for load/stress scenarios with public/private subnets and NAT gateway.
"""
from aws_cdk import Stack, Tags, CfnOutput
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

from ..project_settings import resource_name


class VPCStack(Stack):
    """VPC Stack with public/private subnets and VPC endpoints."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: dict,
        **kwargs,
    ) -> None:
        """Initialize VPC Stack.

        Args:
            scope: CDK app or parent stack
            construct_id: Unique identifier for this stack
            config: Environment configuration dict from config.yaml
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        vpc_config = config["vpc"]
        environment = config["tags"]["Environment"]

        # Create VPC with explicit, deterministic naming
        # Explicit is better than implicit - Zen of Python
        self.vpc = ec2.Vpc(
            self,
            "VPC",
            vpc_name=resource_name(environment, "vpc"),
            ip_addresses=ec2.IpAddresses.cidr(vpc_config["cidr"]),
            max_azs=vpc_config["max_azs"],
            nat_gateways=vpc_config["nat_gateways"],
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name=f"{environment}-private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name=f"{environment}-public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=28,
                ),
            ],
        )

        # CDK Outputs for scenario integration
        CfnOutput(
            self,
            "VpcId",
            value=self.vpc.vpc_id,
            description="VPC ID for BrightAgent load/stress scenarios",
            export_name=f"{environment}-vpc-id",
        )

        CfnOutput(
            self,
            "PrivateSubnetIds",
            value=",".join([subnet.subnet_id for subnet in self.vpc.private_subnets]),
            description="Comma-separated list of private subnet IDs",
            export_name=f"{environment}-private-subnet-ids",
        )

        CfnOutput(
            self,
            "PublicSubnetIds",
            value=",".join([subnet.subnet_id for subnet in self.vpc.public_subnets]),
            description="Comma-separated list of public subnet IDs",
            export_name=f"{environment}-public-subnet-ids",
        )
