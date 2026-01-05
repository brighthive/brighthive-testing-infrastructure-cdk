"""Generate multi-source conflict data for Scenario 02.

IDEMPOTENT & DETERMINISTIC data generation:
- Fixed seeds for reproducible conflicts
- Checks if data exists before generating
- Can safely re-run

Creates overlapping data from multiple sources with conflicts in:
- Field values
- Timestamps
- Entity relationships
"""
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import expr, col, when, md5, concat_ws, lit
from pyspark.sql.utils import AnalysisException
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_data_exists(spark: SparkSession, path: str) -> bool:
    """Check if data already exists.

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


def generate_multi_source_data(
    output_path: str, num_entities: int = 100_000, force: bool = False
):
    """Generate multi-source conflict scenario data IDEMPOTENTLY.

    Args:
        output_path: S3 path for output data
        num_entities: Number of unique entities
        force: Force regeneration even if data exists
    """
    spark = (
        SparkSession.builder.appName("GenerateMultiSourceConflicts")
        .config("spark.sql.adaptive.enabled", "true")
        .getOrCreate()
    )

    # Idempotency check
    if not force and check_data_exists(spark, output_path):
        logger.info(f"Data already exists at {output_path} - skipping generation")
        logger.info("Use --force flag to regenerate data")
        return

    logger.info(f"Generating DETERMINISTIC multi-source conflicts for {num_entities:,} entities...")

    # Generate 3 overlapping sources with conflicts
    sources = ["source_a", "source_b", "source_c"]

    for source in sources:
        logger.info(f"Generating data for {source}...")

        # Each source has overlapping entity IDs but different values
        df = spark.range(0, num_entities * 2, numPartitions=100)

        # Deterministic record generation
        df = (
            df.withColumn("entity_id", expr(f"concat('entity_', cast(id % {num_entities} as string))"))
            .withColumn("source", lit(source))
            .withColumn(
                "record_id",
                md5(concat_ws("-", lit("brightagent"), lit(source), col("id").cast("string"))),
            )
            .withColumn(
                "timestamp",
                expr(f"timestamp('2024-01-01') + INTERVAL (id % 86400) SECOND"),
            )
            # Different sources have conflicting values
            .withColumn(
                "email",
                when(
                    col("source") == "source_a",
                    expr("concat(entity_id, '@sourceA.com')"),
                )
                .when(
                    col("source") == "source_b",
                    expr("concat(entity_id, '@sourceB.com')"),
                )
                .otherwise(expr("concat(entity_id, '@sourceC.com')")),
            )
            .withColumn(
                "age",
                when(col("source") == "source_a", expr("30 + (id % 40)"))
                .when(col("source") == "source_b", expr("35 + (id % 40)"))
                .otherwise(expr("40 + (id % 40)")),
            )
            .withColumn(
                "status",
                when(col("source") == "source_a", expr("'active'"))
                .when(col("source") == "source_b", expr("'inactive'"))
                .otherwise(expr("'pending'")),
            )
        )

        # Write each source to separate partition
        output = f"{output_path}/source={source}"

        try:
            df.write.mode("overwrite").parquet(output)
            record_count = df.count()
            logger.info(f"Wrote {record_count:,} records for {source}")
        except Exception as e:
            logger.error(f"Failed to write data for {source} to {output}: {type(e).__name__}: {e}")
            raise

    logger.info("Multi-source conflict data generation complete!")
    spark.stop()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Missing required argument: output_path")
        logger.info("Usage: spark-submit generate_multi_source.py <output_path> [num_entities] [--force]")
        logger.info("  --force: Regenerate data even if it exists")
        sys.exit(1)

    output_path = sys.argv[1]
    num_entities = 100_000  # Default
    force = False

    # Parse arguments
    for arg in sys.argv[2:]:
        if arg == "--force":
            force = True
        elif arg.isdigit():
            num_entities = int(arg)

    logger.info("Configuration:")
    logger.info(f"  Output: {output_path}")
    logger.info(f"  Entities: {num_entities:,}")
    logger.info(f"  Force: {force}")

    try:
        generate_multi_source_data(output_path, num_entities, force)
    except Exception as e:
        logger.exception(f"Data generation failed: {e}")
        sys.exit(1)
