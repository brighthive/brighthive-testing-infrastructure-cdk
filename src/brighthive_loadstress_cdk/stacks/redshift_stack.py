"""Redshift Stack for BrightAgent Load/Stress Infrastructure.

Creates Redshift cluster with WLM and query monitoring for production-scale load/stress.
"""
import os
import json
import aws_cdk as cdk
from aws_cdk import Stack, CfnOutput
from aws_cdk import aws_redshift as redshift
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class RedshiftStack(Stack):
    """Simple Redshift cluster for scenario loadstress."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.IVpc,
        config: dict,
        **kwargs,
    ) -> None:
        """Initialize Redshift Stack.

        Args:
            scope: CDK app or parent stack
            construct_id: Unique identifier for this stack
            vpc: VPC to deploy Redshift into
            config: Environment configuration dict from config.yaml
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        redshift_config = config["redshift"]
        environment = config["tags"]["Environment"]

        # Load password from environment variable (never hardcode credentials)
        master_password = os.environ.get("REDSHIFT_MASTER_PASSWORD")
        if not master_password:
            raise ValueError(
                "REDSHIFT_MASTER_PASSWORD environment variable not set. "
                "Please set it before deploying: export REDSHIFT_MASTER_PASSWORD='YourSecurePassword123!' "
                "Or source your environment: source .env.loadstress"
            )

        # Explicit security group naming - Readability counts
        self.security_group = ec2.SecurityGroup(
            self,
            "RedshiftSecurityGroup",
            vpc=vpc,
            security_group_name="brightagent-loadstress-redshift-sg",
            description="Redshift cluster security group",
            allow_all_outbound=True,
        )

        # Allow Redshift access from within VPC
        self.security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(5439),
            description="VPC access to Redshift",
        )

        # Explicit subnet group naming
        subnet_group = redshift.CfnClusterSubnetGroup(
            self,
            "SubnetGroup",
            description="Redshift subnet group",
            subnet_ids=[subnet.subnet_id for subnet in vpc.private_subnets],
            tags=[cdk.CfnTag(key="Name", value="brightagent-loadstress-redshift-subnets")],
        )

        # WLM Configuration for production-scale query management
        # 3-queue setup: ETL (high memory), Analytics (medium), Short queries (low latency)
        wlm_config = [
            {
                "name": "etl_queue",
                "query_concurrency": 3,
                "memory_percent_to_use": 50,
                "query_group": ["etl"],
                "query_group_wild_card": 0,
            },
            {
                "name": "analytics_queue",
                "query_concurrency": 5,
                "memory_percent_to_use": 35,
                "query_group": ["analytics"],
                "query_group_wild_card": 0,
            },
            {
                "name": "short_query_queue",
                "query_concurrency": 10,
                "memory_percent_to_use": 15,
                "query_group": ["short"],
                "query_group_wild_card": 0,
                "max_execution_time": 60000,  # 60 seconds
            },
        ]

        # Query Monitoring Rules (QMR) to detect problematic queries
        query_monitoring_rules = [
            {
                "name": "abort_long_queries",
                "predicate": [{"metric_name": "query_execution_time", "operator": "gt", "value": 300000}],  # 5 min
                "action": "abort",
            },
            {
                "name": "log_high_cpu_queries",
                "predicate": [{"metric_name": "query_cpu_time", "operator": "gt", "value": 100000}],  # 100 sec
                "action": "log",
            },
            {
                "name": "log_disk_spill",
                "predicate": [{"metric_name": "query_temp_blocks_to_disk", "operator": "gt", "value": 100000}],
                "action": "log",
            },
        ]

        # Create parameter group with WLM configuration
        parameter_group = redshift.CfnClusterParameterGroup(
            self,
            "ParameterGroup",
            description="Redshift WLM configuration for load/stress testing",
            parameter_group_family="redshift-1.0",
            parameters=[
                {
                    "parameterName": "wlm_json_configuration",
                    "parameterValue": json.dumps(wlm_config),
                },
                {
                    "parameterName": "enable_user_activity_logging",
                    "parameterValue": "true",
                },
                {
                    "parameterName": "max_concurrency_scaling_clusters",
                    "parameterValue": "1",
                },
            ],
            tags=[cdk.CfnTag(key="Name", value="brightagent-loadstress-redshift-params")],
        )

        # Determine cluster type based on number of nodes
        # Redshift requires: single-node for 1 node, multi-node for 2+ nodes
        num_nodes = redshift_config["number_of_nodes"]
        cluster_type = "single-node" if num_nodes == 1 else "multi-node"

        # Explicit cluster identifier - There should be one obvious way to do it
        self.cluster = redshift.CfnCluster(
            self,
            "Cluster",
            cluster_identifier="brightagent-loadstress-redshift",
            cluster_type=cluster_type,
            node_type=redshift_config["node_type"],
            number_of_nodes=num_nodes,
            db_name=redshift_config["database_name"],
            master_username=redshift_config["master_username"],
            master_user_password=master_password,
            cluster_subnet_group_name=subnet_group.ref,
            vpc_security_group_ids=[self.security_group.security_group_id],
            cluster_parameter_group_name=parameter_group.ref,
            publicly_accessible=False,
            automated_snapshot_retention_period=1,
        )

        self.cluster.add_dependency(subnet_group)
        self.cluster.add_dependency(parameter_group)

        # CDK Outputs for scenario integration
        CfnOutput(
            self,
            "RedshiftClusterEndpoint",
            value=self.cluster.attr_endpoint_address,
            description="Redshift cluster endpoint address",
            export_name=f"{environment}-redshift-endpoint",
        )

        CfnOutput(
            self,
            "RedshiftClusterPort",
            value=str(self.cluster.attr_endpoint_port),
            description="Redshift cluster port",
            export_name=f"{environment}-redshift-port",
        )

        CfnOutput(
            self,
            "RedshiftClusterIdentifier",
            value=self.cluster.cluster_identifier,
            description="Redshift cluster identifier",
            export_name=f"{environment}-redshift-cluster-id",
        )

        CfnOutput(
            self,
            "RedshiftDatabaseName",
            value=redshift_config["database_name"],
            description="Redshift database name",
            export_name=f"{environment}-redshift-database-name",
        )

        CfnOutput(
            self,
            "RedshiftMasterUsername",
            value=redshift_config["master_username"],
            description="Redshift master username",
            export_name=f"{environment}-redshift-username",
        )

        CfnOutput(
            self,
            "RedshiftParameterGroup",
            value=parameter_group.ref,
            description="Redshift parameter group with WLM configuration",
            export_name=f"{environment}-redshift-param-group",
        )
