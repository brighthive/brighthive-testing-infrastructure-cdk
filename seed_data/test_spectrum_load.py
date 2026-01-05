#!/usr/bin/env python3
"""Test loading data via Spectrum external tables for better error messages."""
import os
import sys
import time
import boto3

REDSHIFT_CLUSTER = "brightagent-loadstress-redshift"
REDSHIFT_DATABASE = "brightagent_loadstress"
REDSHIFT_USER = "admin"
AWS_REGION = "us-west-2"

S3_BUCKET = "brightagent-loadstress-data-824267124830"
IAM_ROLE = "arn:aws:iam::824267124830:role/brightagent-loadstress-redshift-s3-role"

def execute_sql(client, sql: str, description: str):
    """Execute SQL and wait for completion."""
    print(f"\n{description}...")

    response = client.execute_statement(
        ClusterIdentifier=REDSHIFT_CLUSTER,
        Database=REDSHIFT_DATABASE,
        DbUser=REDSHIFT_USER,
        Sql=sql
    )

    statement_id = response["Id"]

    while True:
        status_response = client.describe_statement(Id=statement_id)
        status = status_response["Status"]

        if status == "FINISHED":
            print(f"  ✓ {description} completed")
            return
        elif status == "FAILED":
            error = status_response.get("Error", "Unknown error")
            print(f"  ✗ {description} failed:")
            print(f"    {error}")
            return
        time.sleep(1)

def main():
    client = boto3.client("redshift-data", region_name=AWS_REGION)

    # Create Spectrum external schema
    execute_sql(
        client,
        f"""
        CREATE EXTERNAL SCHEMA IF NOT EXISTS spectrum
        FROM DATA CATALOG
        DATABASE 'loadstress_external'
        IAM_ROLE '{IAM_ROLE}'
        CREATE EXTERNAL DATABASE IF NOT EXISTS;
        """,
        "Creating Spectrum external schema"
    )

    # Create external table for customers
    execute_sql(
        client,
        f"""
        CREATE EXTERNAL TABLE IF NOT EXISTS spectrum.customers_ext (
            annual_revenue BIGINT,
            company_name VARCHAR(200),
            created_at DATE,
            customer_id VARCHAR(20),
            industry VARCHAR(50),
            lifetime_value DECIMAL(38,6),
            num_employees BIGINT,
            region VARCHAR(50),
            segment VARCHAR(20),
            state VARCHAR(50),
            status VARCHAR(20)
        )
        STORED AS PARQUET
        LOCATION 's3://{S3_BUCKET}/warehouse/customers/';
        """,
        "Creating external table for customers"
    )

    # Try to SELECT from external table
    execute_sql(
        client,
        "SELECT * FROM spectrum.customers_ext LIMIT 5;",
        "Testing SELECT from external table"
    )

    print("\n✅ If SELECT worked, we can now INSERT SELECT into the main table")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
