#!/usr/bin/env python3
"""Load partitioned data using Spectrum external tables."""
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
    """Execute SQL and wait."""
    print(f"\n{description}...")

    response = client.execute_statement(
        ClusterIdentifier=REDSHIFT_CLUSTER,
        Database=REDSHIFT_DATABASE,
        DbUser=REDSHIFT_USER,
        Sql=sql
    )

    while True:
        status = client.describe_statement(Id=response["Id"])
        if status["Status"] == "FINISHED":
            print(f"  ✓ {description} completed")
            return
        elif status["Status"] == "FAILED":
            print(f"  ✗ {description} failed: {status.get('Error', 'Unknown')}")
            return
        time.sleep(1)

def main():
    client = boto3.client("redshift-data", region_name=AWS_REGION)

    # Create external schema (skip Glue database creation)
    execute_sql(
        client,
        f"CREATE EXTERNAL SCHEMA IF NOT EXISTS spectrum FROM DATA CATALOG DATABASE 'default' IAM_ROLE '{IAM_ROLE}';",
        "Creating Spectrum schema"
    )

    # Create external table for orders (with partitions)
    execute_sql(
        client,
        f"""
        DROP TABLE IF EXISTS spectrum.orders_ext;

        CREATE EXTERNAL TABLE spectrum.orders_ext (
            customer_id VARCHAR(20),
            days_to_fulfill BIGINT,
            order_amount DECIMAL(24,2),
            order_id VARCHAR(30),
            order_timestamp TIMESTAMP,
            status VARCHAR(20)
        )
        PARTITIONED BY (order_date DATE)
        STORED AS PARQUET
        LOCATION 's3://{S3_BUCKET}/warehouse/orders/';
        """,
        "Creating external table for orders"
    )

    # Add partitions (let Redshift discover them)
    execute_sql(
        client,
        "ALTER TABLE spectrum.orders_ext ADD IF NOT EXISTS PARTITIONS;",
        "Adding partitions to orders"
    )

    # Load into main table using INSERT SELECT
    execute_sql(
        client,
        """
        INSERT INTO orders (order_id, customer_id, order_date, order_timestamp,  order_amount, status, days_to_fulfill)
        SELECT order_id, customer_id, order_date, order_timestamp, order_amount, status, days_to_fulfill
        FROM spectrum.orders_ext;
        """,
        "Loading orders from external table"
    )

    # Create external table for multi-source (with partitions)
    execute_sql(
        client,
        f"""
        DROP TABLE IF EXISTS spectrum.multi_source_ext;

        CREATE EXTERNAL TABLE spectrum.multi_source_ext (
            record_id VARCHAR(50),
            source_system_id VARCHAR(50),
            entity_id VARCHAR(20),
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            email VARCHAR(200),
            phone VARCHAR(30),
            annual_revenue DECIMAL(24,2),
            employee_count BIGINT,
            created_date DATE,
            created_date_str VARCHAR(20),
            last_updated DATE,
            has_conflict BOOLEAN,
            conflict_type VARCHAR(20)
        )
        PARTITIONED BY (source VARCHAR(10))
        STORED AS PARQUET
        LOCATION 's3://{S3_BUCKET}/multi_source_data/';
        """,
        "Creating external table for multi-source"
    )

    # Add partitions
    execute_sql(
        client,
        "ALTER TABLE spectrum.multi_source_ext ADD IF NOT EXISTS PARTITIONS;",
        "Adding partitions to multi-source"
    )

    # Load into main table
    execute_sql(
        client,
        """
        INSERT INTO multi_source_entities
        SELECT record_id, source, source_system_id, entity_id, first_name, last_name,
               email, phone, annual_revenue, employee_count, created_date, created_date_str,
               last_updated, has_conflict, conflict_type
        FROM spectrum.multi_source_ext;
        """,
        "Loading multi-source from external table"
    )

    print("\n✅ Partitioned data loaded successfully!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
