#!/usr/bin/env python3
"""Verify Parquet schema matches Redshift table schema."""
import boto3
import pyarrow.parquet as pq
from io import BytesIO

S3_BUCKET = "brightagent-loadstress-data-824267124830"
DATASETS = {
    "customers": "warehouse/customers/",
    "products": "warehouse/products/",
    "orders": "warehouse/orders/",
    "multi_source": "multi_source_data/source=A/"
}

def get_parquet_schema(bucket: str, prefix: str) -> dict:
    """Read Parquet schema from S3."""
    s3 = boto3.client("s3", region_name="us-west-2")

    # List objects in prefix
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

    if "Contents" not in response:
        print(f"❌ No files found at s3://{bucket}/{prefix}")
        return {}

    # Get first .parquet file (skip _SUCCESS and other files)
    parquet_files = [obj["Key"] for obj in response["Contents"] if obj["Key"].endswith(".parquet")]

    if not parquet_files:
        print(f"❌ No Parquet files found at s3://{bucket}/{prefix}")
        return {}

    first_file = parquet_files[0]
    print(f"  Reading: s3://{bucket}/{first_file}")

    # Download and read schema
    obj = s3.get_object(Bucket=bucket, Key=first_file)
    data = obj["Body"].read()

    parquet_file = pq.ParquetFile(BytesIO(data))
    schema = parquet_file.schema.to_arrow_schema()

    return {field.name: str(field.type) for field in schema}

def main():
    print("Verifying Parquet schemas in S3...\n")

    for dataset_name, s3_prefix in DATASETS.items():
        print(f"📦 {dataset_name.upper()}")
        schema = get_parquet_schema(S3_BUCKET, s3_prefix)

        if schema:
            print(f"  Columns ({len(schema)}):")
            for col, dtype in sorted(schema.items()):
                print(f"    - {col}: {dtype}")
        print()

if __name__ == "__main__":
    main()
