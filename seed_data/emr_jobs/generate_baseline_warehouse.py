"""Generate baseline warehouse data for BrightAgent load/stress scenarios.

IDEMPOTENT & DETERMINISTIC data generation:
- Uses fixed random seeds for reproducibility
- Checks if data already exists
- Can safely re-run without duplicates

Creates configurable records (1M-1B) as baseline.
Schema includes:
- record_id (deterministic UUID based on id)
- entity_id (1M unique entities)
- timestamp
- field_001 to field_400 (400 fields)
- metadata
"""
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import expr, col, md5, concat_ws, lit
from pyspark.sql.utils import AnalysisException
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_data_exists(spark: SparkSession, path: str) -> bool:
    """Check if data already exists at path.

    Args:
        spark: Spark session
        path: S3 path to check

    Returns:
        True if data exists, False otherwise

    Raises:
        Exception: If unexpected error occurs (network issues, permissions, etc.)
    """
    try:
        spark.read.parquet(path)
        logger.info(f"Data exists at path: {path}")
        return True
    except AnalysisException as e:
        # Expected: path doesn't exist or is not a valid parquet location
        if "Path does not exist" in str(e) or "is not a Parquet file" in str(e):
            logger.info(f"No data found at path: {path}")
            return False
        # Unexpected AnalysisException - re-raise
        logger.error(f"Analysis error checking path {path}: {type(e).__name__}: {e}")
        raise
    except Exception as e:
        # Unexpected error (network, permissions, etc.) - log and re-raise
        logger.error(f"Unexpected error checking path {path}: {type(e).__name__}: {e}")
        raise


def generate_baseline_warehouse(
    output_path: str, num_records: int = 1_000_000_000, force: bool = False
):
    """Generate baseline warehouse data IDEMPOTENTLY.

    Args:
        output_path: S3 path for output data
        num_records: Number of records to generate (default 1B)
        force: Force regeneration even if data exists
    """
    spark = (
        SparkSession.builder.appName("GenerateBaselineWarehouse")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .getOrCreate()
    )

    # Idempotency check
    if not force and check_data_exists(spark, output_path):
        logger.info(f"Data already exists at {output_path} - skipping generation")
        logger.info("Use --force flag to regenerate data")
        return

    logger.info(f"Generating {num_records:,} records with DETERMINISTIC seeds...")

    # Generate base records with partitioning for parallelism
    df = spark.range(0, num_records, numPartitions=1000)

    # Add core fields with DETERMINISTIC values
    # record_id: MD5 hash of id for deterministic UUID-like values
    df = (
        df.withColumn(
            "record_id",
            md5(concat_ws("-", lit("brightagent"), col("id").cast("string"))),
        )
        .withColumn("entity_id", expr("concat('entity_', cast(id % 1000000 as string))"))
        .withColumn(
            "timestamp",
            expr("timestamp('2024-01-01') + INTERVAL (id % 31536000) SECOND"),
        )
    )

    # Add 400 fields with DETERMINISTIC random values
    # Using (id + field_number) as seed ensures reproducibility
    logger.info("Adding 400 fields with deterministic seeds...")
    for i in range(1, 401):
        field_name = f"field_{i:03d}"
        # Use id-based seeding for deterministic "random" values
        if i % 3 == 0:
            # String field - deterministic based on id
            df = df.withColumn(
                field_name,
                expr(f"concat('value_', cast((id + {i}) % 1000 as string))"),
            )
        elif i % 3 == 1:
            # Numeric field - deterministic calculation
            df = df.withColumn(field_name, expr(f"((id * {i}) % 10000) / 10.0"))
        else:
            # Boolean field - deterministic based on id
            df = df.withColumn(field_name, expr(f"((id + {i}) % 2) = 0"))

    # Add metadata
    df = df.withColumn("metadata", expr("map('source', 'synthetic', 'version', '1.0')"))

    logger.info(f"Writing data to {output_path}...")

    try:
        # Write as Parquet (columnar, compressed)
        # Partition by date for efficient querying
        df.write.mode("overwrite").partitionBy("timestamp").parquet(output_path)

        record_count = df.count()
        logger.info(f"Data generation complete! Total records: {record_count:,}")
    except Exception as e:
        logger.error(f"Failed to write data to {output_path}: {type(e).__name__}: {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Missing required argument: output_path")
        logger.info("Usage: spark-submit generate_baseline_warehouse.py <output_path> [num_records] [--force]")
        logger.info("  --force: Regenerate data even if it exists")
        sys.exit(1)

    output_path = sys.argv[1]
    num_records = 1_000_000_000  # Default to 1B
    force = False

    # Parse arguments
    for arg in sys.argv[2:]:
        if arg == "--force":
            force = True
        elif arg.isdigit():
            num_records = int(arg)

    logger.info("Configuration:")
    logger.info(f"  Output: {output_path}")
    logger.info(f"  Records: {num_records:,}")
    logger.info(f"  Force: {force}")

    try:
        generate_baseline_warehouse(output_path, num_records, force)
    except Exception as e:
        logger.exception(f"Data generation failed: {e}")
        sys.exit(1)
