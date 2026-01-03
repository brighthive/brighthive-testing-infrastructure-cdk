"""VPC Stack for BrightBot Testing Infrastructure.

Creates isolated VPC for scenario testing with public/private subnets,
NAT gateway, and VPC endpoints for cost optimization.
"""
from aws_cdk import Stack, Tags
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


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

        # Create VPC with public and private subnets
        self.vpc = ec2.Vpc(
            self,
            "VPC",
            ip_addresses=ec2.IpAddresses.cidr(vpc_config["cidr"]),
            max_azs=vpc_config["max_azs"],
            nat_gateways=vpc_config["nat_gateways"],
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=28,  # Small public subnet
                ),
            ],
        )

        # VPC Endpoints for cost savings (no NAT traffic for AWS services)
        self.vpc.add_gateway_endpoint(
            "S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3,
        )

        self.vpc.add_interface_endpoint(
            "SecretsManagerEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
        )

        self.vpc.add_interface_endpoint(
            "CloudWatchLogsEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
        )

        # Tag VPC resources
        Tags.of(self.vpc).add("Name", f"{construct_id}-VPC")
