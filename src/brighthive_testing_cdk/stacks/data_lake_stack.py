"""Data Lake Stack for BrightBot Testing Infrastructure.

Creates S3 bucket, Glue Catalog database, and Glue Crawler for
metadata discovery.
"""
from aws_cdk import Stack, RemovalPolicy, Duration
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_glue as glue
from aws_cdk import aws_iam as iam
from constructs import Construct


class DataLakeStack(Stack):
    """Data Lake Stack with S3 and Glue Catalog."""

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

        # S3 bucket for scenario data
        self.data_bucket = s3.Bucket(
            self,
            "DataBucket",
            bucket_name=f"{data_lake_config['bucket_prefix']}-{environment}-{self.account}",
            versioned=False,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="expire-old-data",
                    expiration=Duration.days(data_lake_config["retention_days"]),
                )
            ],
            removal_policy=RemovalPolicy.DESTROY,  # Safe for test env
            auto_delete_objects=True,
        )

        # Glue Catalog Database
        self.catalog_db = glue.CfnDatabase(
            self,
            "CatalogDB",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name=f"brightbot_test_{environment}",
                description=f"Catalog for BrightBot test data ({environment})",
            ),
        )

        # IAM role for Glue Crawler
        crawler_role = iam.Role(
            self,
            "CrawlerRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSGlueServiceRole"
                )
            ],
        )

        # Grant Glue Crawler read access to S3 bucket
        self.data_bucket.grant_read(crawler_role)

        # Glue Crawler for metadata discovery
        self.crawler = glue.CfnCrawler(
            self,
            "Crawler",
            role=crawler_role.role_arn,
            database_name=self.catalog_db.ref,
            targets=glue.CfnCrawler.TargetsProperty(
                s3_targets=[
                    glue.CfnCrawler.S3TargetProperty(
                        path=f"s3://{self.data_bucket.bucket_name}/data/"
                    )
                ]
            ),
            schema_change_policy=glue.CfnCrawler.SchemaChangePolicyProperty(
                update_behavior="UPDATE_IN_DATABASE",
                delete_behavior="LOG",
            ),
        )
