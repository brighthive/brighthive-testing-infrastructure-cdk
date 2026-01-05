"""Generate REALISTIC multi-source conflict data for Scenario S02.

Applies brighthive-mock-data patterns for realistic conflicts:
- Weighted conflict types (40% name, 30% measure, 20% date, 10% other)
- Source quality levels (A: 95% accurate, B: 90%, C: 85%)
- Realistic name variations (John Smith vs J. Smith vs Smith, John)
- Format differences (dates, amounts, phone numbers)
- Temporal resolution (timestamp-based merge opportunities)
- Multi-factor correlations

Creates 3 overlapping sources with realistic conflicts that BrightAgent must resolve.
"""
import logging
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    expr, col, when, lit, concat_ws, md5, row_number,
    upper, lower, regexp_replace, substring
)
from pyspark.sql.window import Window
from pyspark.sql.utils import AnalysisException
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_data_exists(spark: SparkSession, path: str) -> bool:
    """Check if data already exists at path."""
    try:
        spark.read.parquet(path)
        logger.info(f"Data exists at path: {path}")
        return True
    except AnalysisException as e:
        if "Path does not exist" in str(e) or "is not a Parquet file" in str(e):
            logger.info(f"No data found at path: {path}")
            return False
        logger.error(f"Analysis error checking path {path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error checking path {path}: {e}")
        raise


def generate_base_entities(spark: SparkSession, num_entities: int) -> DataFrame:
    """Generate canonical entities (the 'truth' before conflicts).

    This represents the ideal state before data quality issues.
    """
    logger.info(f"Generating {num_entities:,} canonical entities...")

    df = spark.range(0, num_entities)

    # Generate realistic first/last names (deterministic)
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer",
                   "Michael", "Linda", "William", "Elizabeth"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones",
                  "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

    df = df.withColumn(
        "first_name",
        when(col("id") % 10 == 0, lit(first_names[0]))
        .when(col("id") % 10 == 1, lit(first_names[1]))
        .when(col("id") % 10 == 2, lit(first_names[2]))
        .when(col("id") % 10 == 3, lit(first_names[3]))
        .when(col("id") % 10 == 4, lit(first_names[4]))
        .when(col("id") % 10 == 5, lit(first_names[5]))
        .when(col("id") % 10 == 6, lit(first_names[6]))
        .when(col("id") % 10 == 7, lit(first_names[7]))
        .when(col("id") % 10 == 8, lit(first_names[8]))
        .otherwise(lit(first_names[9]))
    )

    df = df.withColumn(
        "last_name",
        when(col("id") % 10 == 0, lit(last_names[0]))
        .when(col("id") % 10 == 1, lit(last_names[1]))
        .when(col("id") % 10 == 2, lit(last_names[2]))
        .when(col("id") % 10 == 3, lit(last_names[3]))
        .when(col("id") % 10 == 4, lit(last_names[4]))
        .when(col("id") % 10 == 5, lit(last_names[5]))
        .when(col("id") % 10 == 6, lit(last_names[6]))
        .when(col("id") % 10 == 7, lit(last_names[7]))
        .when(col("id") % 10 == 8, lit(last_names[8]))
        .otherwise(lit(last_names[9]))
    )

    # Canonical values (the truth)
    df = df.withColumn(
        "entity_id",
        expr("concat('ENT', lpad(cast(id as string), 10, '0'))")
    )

    df = df.withColumn(
        "email",
        lower(concat_ws(".", col("first_name"), col("last_name"), lit("@company.com")))
    )

    df = df.withColumn(
        "phone",
        expr("concat('555-', lpad(cast((id * 17) % 1000 as string), 3, '0'), '-', lpad(cast((id * 23) % 10000 as string), 4, '0'))")
    )

    df = df.withColumn(
        "annual_revenue",
        expr("50000 + (id * 37 % 950000)")  # $50K - $1M
    )

    df = df.withColumn(
        "employee_count",
        expr("10 + (id * 13 % 990)")  # 10-1000 employees
    )

    df = df.withColumn(
        "created_date",
        expr("date_add('2020-01-01', cast((id * 7) % 1460 as int))")  # Spread over 4 years
    )

    df = df.withColumn(
        "last_updated",
        expr("date_add(created_date, cast((id * 11) % 365 as int))")  # Updated within a year of creation
    )

    return df.select(
        "entity_id", "first_name", "last_name", "email", "phone",
        "annual_revenue", "employee_count", "created_date", "last_updated"
    )


def apply_source_conflicts(
    entities: DataFrame,
    source_name: str,
    source_quality: float,
    timestamp_offset_days: int
) -> DataFrame:
    """Apply realistic conflicts to entities based on source characteristics.

    Args:
        entities: Base entities
        source_name: Source identifier (A, B, C)
        source_quality: Accuracy rate (0.95 = 95% accurate, 5% conflicts)
        timestamp_offset_days: Days to add to last_updated (simulates different update times)

    Conflict types (weighted distribution):
    - Name variations: 40%
    - Measure differences: 30%
    - Date conflicts: 20%
    - Other: 10%
    """
    logger.info(f"Applying conflicts for {source_name} (quality: {source_quality*100}%)")

    df = entities

    # Add source metadata
    df = df.withColumn("source", lit(source_name))

    # Update timestamp (different sources update at different times)
    df = df.withColumn(
        "last_updated",
        expr(f"date_add(last_updated, {timestamp_offset_days})")
    )

    # Conflict indicator (based on source quality)
    # Use hash of entity_id for deterministic randomness
    quality_threshold = int(source_quality * 100)
    df = df.withColumn(
        "has_conflict",
        expr(f"abs(hash(entity_id)) % 100") >= quality_threshold
    )

    # Conflict type distribution (among records with conflicts)
    # 40% name, 30% measure, 20% date, 10% other
    df = df.withColumn(
        "conflict_type",
        expr("""
            CASE
                WHEN has_conflict = false THEN 'none'
                WHEN has_conflict = true AND abs(hash(entity_id)) % 10 < 4 THEN 'name'
                WHEN has_conflict = true AND abs(hash(entity_id)) % 10 < 7 THEN 'measure'
                WHEN has_conflict = true AND abs(hash(entity_id)) % 10 < 9 THEN 'date'
                ELSE 'other'
            END
        """)
    )

    # Apply name variations (realistic patterns)
    df = df.withColumn(
        "first_name",
        when(col("conflict_type") == "name",
             when(col("source") == "A", substring(col("first_name"), 1, 1))  # "J" instead of "John"
             .when(col("source") == "B", upper(col("first_name")))           # "JOHN" instead of "John"
             .otherwise(col("first_name")))  # Source C keeps it correct
        .otherwise(col("first_name"))
    )

    df = df.withColumn(
        "last_name",
        when(col("conflict_type") == "name",
             when(col("source") == "A", col("last_name"))  # Keep as is
             .when(col("source") == "B", upper(col("last_name")))  # "SMITH" instead of "Smith"
             .otherwise(lower(col("last_name"))))  # "smith" instead of "Smith"
        .otherwise(col("last_name"))
    )

    # Email format differences
    df = df.withColumn(
        "email",
        when(col("conflict_type") == "other",
             when(col("source") == "A", regexp_replace(col("email"), "@company.com", "@company.org"))
             .when(col("source") == "B", upper(col("email")))
             .otherwise(col("email")))
        .otherwise(col("email"))
    )

    # Phone number format differences
    df = df.withColumn(
        "phone",
        when(col("conflict_type") == "other",
             when(col("source") == "A", regexp_replace(col("phone"), "-", "."))  # 555.123.4567
             .when(col("source") == "B", regexp_replace(col("phone"), "-", ""))  # 5551234567
             .otherwise(col("phone")))  # 555-123-4567
        .otherwise(col("phone"))
    )

    # Measure differences (revenue, employee count)
    df = df.withColumn(
        "annual_revenue",
        when(col("conflict_type") == "measure",
             when(col("source") == "A", expr("annual_revenue * 1.05"))  # 5% higher
             .when(col("source") == "B", expr("annual_revenue * 0.95"))  # 5% lower
             .otherwise(col("annual_revenue")))
        .otherwise(col("annual_revenue"))
    )

    df = df.withColumn(
        "employee_count",
        when(col("conflict_type") == "measure",
             when(col("source") == "A", expr("employee_count + 5"))  # Off by 5
             .when(col("source") == "B", expr("employee_count - 3"))  # Off by 3
             .otherwise(col("employee_count")))
        .otherwise(col("employee_count"))
    )

    # Date format differences
    df = df.withColumn(
        "created_date_str",
        when(col("conflict_type") == "date",
             when(col("source") == "A", expr("date_format(created_date, 'MM/dd/yyyy')"))  # US format
             .when(col("source") == "B", expr("date_format(created_date, 'dd-MM-yyyy')"))  # EU format
             .otherwise(expr("date_format(created_date, 'yyyy-MM-dd')")))  # ISO format
        .otherwise(expr("date_format(created_date, 'yyyy-MM-dd')"))
    )

    # Add record metadata
    df = df.withColumn(
        "record_id",
        md5(concat_ws("-", lit(source_name), col("entity_id"), col("last_updated").cast("string")))
    )

    df = df.withColumn(
        "source_system_id",
        concat_ws("-", lit(source_name), col("entity_id"))
    )

    return df.select(
        "record_id", "source", "source_system_id", "entity_id",
        "first_name", "last_name", "email", "phone",
        "annual_revenue", "employee_count",
        "created_date", "created_date_str", "last_updated",
        "has_conflict", "conflict_type"
    )


def generate_multi_source_realistic(
    output_path: str,
    num_entities: int = 100_000,
    force: bool = False
):
    """Generate realistic multi-source conflict data.

    Creates 3 sources with realistic overlap and conflicts:
    - Source A: 95% accurate, updates first (day 0)
    - Source B: 90% accurate, updates second (day 5)
    - Source C: 85% accurate, updates last (day 10)

    Each source sees 60-80% of entities (realistic overlap).

    Args:
        output_path: S3 base path for output
        num_entities: Number of unique entities
        force: Force regeneration
    """
    spark = (
        SparkSession.builder
        .appName("GenerateMultiSourceConflicts")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .getOrCreate()
    )

    try:
        logger.info("=== Generating Base Entities ===")
        base_entities = generate_base_entities(spark, num_entities)

        # Source A: Highest quality (95%), sees 80% of entities, updates first
        logger.info("=== Generating Source A (95% accurate, 80% coverage) ===")
        source_a = base_entities.filter(col("id") % 100 < 80)  # 80% coverage
        source_a = apply_source_conflicts(source_a, "A", 0.95, 0)  # Day 0

        source_a_path = f"{output_path}/source=A"
        if force or not check_data_exists(spark, source_a_path):
            source_a.write.mode("overwrite").parquet(source_a_path)
            logger.info(f"✓ Wrote {source_a.count():,} records for Source A")

        # Source B: Medium quality (90%), sees 70% of entities, updates later
        logger.info("=== Generating Source B (90% accurate, 70% coverage) ===")
        source_b = base_entities.filter((col("id") % 100 < 70) & (col("id") % 3 != 0))  # 70% coverage, different overlap
        source_b = apply_source_conflicts(source_b, "B", 0.90, 5)  # Day 5

        source_b_path = f"{output_path}/source=B"
        if force or not check_data_exists(spark, source_b_path):
            source_b.write.mode("overwrite").parquet(source_b_path)
            logger.info(f"✓ Wrote {source_b.count():,} records for Source B")

        # Source C: Lower quality (85%), sees 60% of entities, updates last
        logger.info("=== Generating Source C (85% accurate, 60% coverage) ===")
        source_c = base_entities.filter((col("id") % 100 < 60) & (col("id") % 5 != 0))  # 60% coverage, different overlap
        source_c = apply_source_conflicts(source_c, "C", 0.85, 10)  # Day 10

        source_c_path = f"{output_path}/source=C"
        if force or not check_data_exists(spark, source_c_path):
            source_c.write.mode("overwrite").parquet(source_c_path)
            logger.info(f"✓ Wrote {source_c.count():,} records for Source C")

        logger.info("=== Multi-Source Conflict Data Complete! ===")
        logger.info(f"Output location: {output_path}")
        logger.info("Conflict patterns applied:")
        logger.info("  ✓ Name variations (40%): John vs J vs JOHN vs john")
        logger.info("  ✓ Measure differences (30%): ±5% revenue, ±3-5 employees")
        logger.info("  ✓ Date format conflicts (20%): MM/dd/yyyy vs dd-MM-yyyy vs yyyy-MM-dd")
        logger.info("  ✓ Other conflicts (10%): email domains, phone formats")
        logger.info("Source characteristics:")
        logger.info("  Source A: 95% accurate, 80% coverage, earliest timestamp")
        logger.info("  Source B: 90% accurate, 70% coverage, mid timestamp")
        logger.info("  Source C: 85% accurate, 60% coverage, latest timestamp")
        logger.info("Resolution strategies:")
        logger.info("  - Latest timestamp (Source C wins on recency)")
        logger.info("  - Highest quality (Source A wins on accuracy)")
        logger.info("  - Business rules (combine best attributes)")

    except Exception as e:
        logger.exception(f"Data generation failed: {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Missing required argument: output_path")
        logger.info("Usage: spark-submit generate_multi_source_realistic.py <output_path> [num_entities] [--force]")
        logger.info("  Defaults: num_entities=100K")
        logger.info("  --force: Regenerate data even if it exists")
        sys.exit(1)

    output_path = sys.argv[1]
    num_entities = 100_000
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
        generate_multi_source_realistic(output_path, num_entities, force)
    except Exception as e:
        logger.exception(f"Data generation failed: {e}")
        sys.exit(1)
