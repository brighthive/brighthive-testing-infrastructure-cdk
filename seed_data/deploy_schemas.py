#!/usr/bin/env python3
"""Deploy Redshift schemas using AWS Redshift Data API.

This script deploys the optimized warehouse schema to the Redshift cluster.
"""
import os
import sys
import time
import boto3
from pathlib import Path

# Get Redshift connection details from environment
REDSHIFT_CLUSTER = os.environ.get("REDSHIFT_CLUSTER_ID", "brightagent-loadstress-redshift")
REDSHIFT_DATABASE = os.environ.get("REDSHIFT_DATABASE", "brightagent_loadstress")
REDSHIFT_USER = os.environ.get("REDSHIFT_USER", "admin")
AWS_REGION = os.environ.get("AWS_REGION", "us-west-2")

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
    print(f"  Statement ID: {statement_id}")

    # Wait for statement to complete
    while True:
        status_response = client.describe_statement(Id=statement_id)
        status = status_response["Status"]

        if status == "FINISHED":
            print(f"  ✓ {description} completed")
            if status_response.get("ResultRows", 0) > 0:
                print(f"    Affected rows: {status_response['ResultRows']}")
            break
        elif status == "FAILED":
            error = status_response.get("Error", "Unknown error")
            print(f"  ✗ {description} failed: {error}")
            sys.exit(1)
        elif status == "ABORTED":
            print(f"  ✗ {description} was aborted")
            sys.exit(1)
        else:
            print(f"  Status: {status}...")
            time.sleep(2)


def deploy_schema():
    """Deploy the Redshift schema."""
    schema_file = Path(__file__).parent / "redshift_schemas" / "optimized_warehouse_schema.sql"

    if not schema_file.exists():
        print(f"Error: Schema file not found: {schema_file}")
        sys.exit(1)

    print(f"Reading schema from: {schema_file}")
    with open(schema_file) as f:
        schema_sql = f.read()

    # Remove comments and split SQL into individual statements
    lines = schema_sql.split("\n")
    clean_lines = []
    for line in lines:
        # Remove single-line comments
        if not line.strip().startswith("--"):
            clean_lines.append(line)

    clean_sql = "\n".join(clean_lines)

    # Split by semicolon
    statements = [s.strip() for s in clean_sql.split(";") if s.strip()]

    print(f"\nConnecting to Redshift cluster: {REDSHIFT_CLUSTER}")
    print(f"Database: {REDSHIFT_DATABASE}")
    print(f"User: {REDSHIFT_USER}")
    print(f"Region: {AWS_REGION}")

    client = boto3.client("redshift-data", region_name=AWS_REGION)

    print(f"\nDeploying {len(statements)} SQL statements...")

    for i, stmt in enumerate(statements, 1):
        # Skip empty statements
        if not stmt:
            continue

        # Determine description from statement
        stmt_upper = stmt.upper()
        if "DROP TABLE" in stmt_upper:
            table_name = stmt.split("IF EXISTS")[1].split()[0] if "IF EXISTS" in stmt_upper else stmt.split("DROP TABLE")[1].split()[0]
            description = f"[{i}/{len(statements)}] Dropping table {table_name}"
        elif "CREATE TABLE" in stmt_upper:
            table_name = stmt.split("CREATE TABLE")[1].split()[0].split("(")[0].strip()
            description = f"[{i}/{len(statements)}] Creating table {table_name}"
        elif "COMMENT ON" in stmt_upper:
            description = f"[{i}/{len(statements)}] Adding table comment"
        else:
            description = f"[{i}/{len(statements)}] Executing statement"

        execute_sql(client, stmt, description)

    print("\n✓ Schema deployment complete!")
    print("\nVerifying tables...")

    # List tables
    execute_sql(
        client,
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename",
        "Listing tables"
    )


if __name__ == "__main__":
    try:
        deploy_schema()
    except Exception as e:
        print(f"\n✗ Schema deployment failed: {e}")
        sys.exit(1)
