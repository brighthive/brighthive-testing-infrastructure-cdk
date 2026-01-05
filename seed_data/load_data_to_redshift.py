#!/usr/bin/env python3
"""Load data from S3 to Redshift using COPY command."""
import os
import sys
import time
import boto3

REDSHIFT_CLUSTER = os.environ.get("REDSHIFT_CLUSTER_ID", "brightagent-loadstress-redshift")
REDSHIFT_DATABASE = os.environ.get("REDSHIFT_DATABASE", "brightagent_loadstress")
REDSHIFT_USER = os.environ.get("REDSHIFT_USER", "admin")
AWS_REGION = os.environ.get("AWS_REGION", "us-west-2")

S3_BUCKET = "brightagent-loadstress-data-824267124830"
IAM_ROLE = "arn:aws:iam::824267124830:role/brightagent-loadstress-redshift-s3-role"

def execute_sql(client, sql: str, description: str) -> None:
    """Execute SQL statement using Redshift Data API."""
    print(f"\n{description}...")

    response = client.execute_statement(
        ClusterIdentifier=REDSHIFT_CLUSTER,
        Database=REDSHIFT_DATABASE,
        DbUser=REDSHIFT_USER,
        Sql=sql
    )

    statement_id = response["Id"]

    # Wait for statement to complete
    while True:
        status_response = client.describe_statement(Id=statement_id)
        status = status_response["Status"]

        if status == "FINISHED":
            result_rows = status_response.get("ResultRows", 0)
            print(f"  ✓ {description} completed (Rows affected: {result_rows})")
            return
        elif status == "FAILED":
            error = status_response.get("Error", "Unknown error")
            print(f"  ✗ {description} failed: {error}")
            sys.exit(1)
        elif status == "ABORTED":
            print(f"  ✗ {description} was aborted")
            sys.exit(1)
        else:
            time.sleep(2)


def main():
    print(f"Loading data from S3 to Redshift...")
    print(f"Cluster: {REDSHIFT_CLUSTER}")
    print(f"Database: {REDSHIFT_DATABASE}")
    print(f"Region: {AWS_REGION}")

    client = boto3.client("redshift-data", region_name=AWS_REGION)

    # 1. Load customers (SKIP - already loaded with 100K rows)
    print("\n" + "="*60)
    print("CUSTOMERS - ALREADY LOADED (100,000 rows)")
    print("="*60)

    # 2. Load products
    print("\n" + "="*60)
    print("LOADING PRODUCTS")
    print("="*60)
    # Let Redshift auto-map columns by name from Parquet
    execute_sql(
        client,
        f"""
        COPY products
        FROM 's3://{S3_BUCKET}/warehouse/products/'
        IAM_ROLE '{IAM_ROLE}'
        FORMAT AS PARQUET;
        """,
        "Loading products from S3"
    )

    # 3. Load orders (with partitioning)
    print("\n" + "="*60)
    print("LOADING ORDERS")
    print("="*60)
    print("NOTE: Orders table is partitioned by order_date")
    print("      We need to add the partition column during COPY")

    # For partitioned data, we need to use a different approach
    # Option 1: Load all partitions at once (Redshift will read partition values from path)
    execute_sql(
        client,
        f"""
        COPY orders
        FROM 's3://{S3_BUCKET}/warehouse/orders/'
        IAM_ROLE '{IAM_ROLE}'
        FORMAT AS PARQUET;
        """,
        "Loading orders from S3 (all partitions)"
    )

    # 4. Load multi-source entities (with partitioning)
    print("\n" + "="*60)
    print("LOADING MULTI-SOURCE ENTITIES")
    print("="*60)
    print("NOTE: Multi-source table is partitioned by source")
    print("      We need to add the partition column during COPY")

    execute_sql(
        client,
        f"""
        COPY multi_source_entities
        FROM 's3://{S3_BUCKET}/multi_source_data/'
        IAM_ROLE '{IAM_ROLE}'
        FORMAT AS PARQUET;
        """,
        "Loading multi-source entities from S3 (all partitions)"
    )

    # 5. Verify row counts
    print("\n" + "="*60)
    print("VERIFYING ROW COUNTS")
    print("="*60)

    for table in ["customers", "products", "orders", "multi_source_entities"]:
        response = client.execute_statement(
            ClusterIdentifier=REDSHIFT_CLUSTER,
            Database=REDSHIFT_DATABASE,
            DbUser=REDSHIFT_USER,
            Sql=f"SELECT COUNT(*) as count FROM {table}"
        )

        statement_id = response["Id"]

        # Wait for completion
        while True:
            status_response = client.describe_statement(Id=statement_id)
            if status_response["Status"] == "FINISHED":
                result_response = client.get_statement_result(Id=statement_id)
                count = result_response["Records"][0][0]["longValue"]
                print(f"  {table}: {count:,} rows")
                break
            elif status_response["Status"] in ["FAILED", "ABORTED"]:
                print(f"  {table}: Failed to get count")
                break
            time.sleep(1)

    print("\n✅ Data loading complete!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Data loading failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
