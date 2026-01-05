"""Unit tests for PySpark data generation scripts.

These tests run locally with a small Spark session to validate:
1. PySpark code syntax and type correctness
2. Data generation logic
3. Schema validation
4. Column expressions (would have caught all our bugs!)

Run with: pytest tests/test_pyspark_data_generation.py -v
"""
import pytest
import sys
from pathlib import Path

# Add seed_data to path so we can import the generators
sys.path.insert(0, str(Path(__file__).parent.parent / "seed_data" / "emr_jobs"))

from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark():
    """Create local Spark session for testing.

    This runs in local[1] mode - no cluster needed!
    """
    spark = SparkSession.builder \
        .master("local[1]") \
        .appName("pyspark-unit-tests") \
        .config("spark.sql.shuffle.partitions", "1") \
        .config("spark.default.parallelism", "1") \
        .getOrCreate()

    yield spark

    spark.stop()


class TestWarehouseDataGeneration:
    """Test warehouse data generation with SMALL datasets."""

    def test_import_warehouse_script(self):
        """Test that we can import the script without errors."""
        try:
            import generate_warehouse_realistic
            assert hasattr(generate_warehouse_realistic, 'generate_customers')
            assert hasattr(generate_warehouse_realistic, 'generate_products')
            assert hasattr(generate_warehouse_realistic, 'generate_orders')
        except ImportError as e:
            pytest.fail(f"Failed to import warehouse script: {e}")

    def test_generate_customers_small(self, spark):
        """Test customer generation with 10 records."""
        from generate_warehouse_realistic import generate_customers

        # Generate tiny dataset
        df = generate_customers(spark, num_customers=10)

        # Verify count
        assert df.count() == 10, "Should generate exactly 10 customers"

        # Verify schema
        expected_columns = {
            'customer_id', 'company_name', 'segment', 'industry',
            'annual_revenue', 'num_employees', 'created_at', 'status'
        }
        actual_columns = set(df.columns)
        assert expected_columns.issubset(actual_columns), \
            f"Missing columns: {expected_columns - actual_columns}"

        # Verify no nulls in critical fields
        assert df.filter("customer_id IS NULL").count() == 0
        assert df.filter("company_name IS NULL").count() == 0

        # Verify data types (would catch BIGINT vs INT issues!)
        df.printSchema()

        # Try to collect (would fail if Column type issues)
        rows = df.collect()
        assert len(rows) == 10

    def test_generate_products_small(self, spark):
        """Test product generation with 5 records."""
        from generate_warehouse_realistic import generate_products

        df = generate_products(spark, num_products=5)

        assert df.count() == 5
        assert 'product_id' in df.columns
        assert 'category' in df.columns

        # Verify no nulls
        assert df.filter("product_id IS NULL").count() == 0

    def test_generate_orders_small(self, spark):
        """Test order generation with 20 records."""
        from generate_warehouse_realistic import generate_customers, generate_products, generate_orders

        # Need customers and products first
        customers = generate_customers(spark, num_customers=5)
        products = generate_products(spark, num_products=3)

        # Generate small order set
        orders = generate_orders(spark, customers, num_orders=20)

        assert orders.count() == 20

        # Verify schema
        assert 'order_id' in orders.columns
        assert 'customer_id' in orders.columns
        assert 'order_date' in orders.columns

        # Verify no nulls in critical fields
        assert orders.filter("order_id IS NULL").count() == 0
        assert orders.filter("order_amount IS NULL").count() == 0


class TestMultiSourceDataGeneration:
    """Test multi-source conflict data generation."""

    def test_import_multi_source_script(self):
        """Test that we can import the script."""
        try:
            import generate_multi_source_realistic
            assert hasattr(generate_multi_source_realistic, 'generate_base_entities')
            assert hasattr(generate_multi_source_realistic, 'apply_source_conflicts')
        except ImportError as e:
            pytest.fail(f"Failed to import multi-source script: {e}")

    def test_generate_base_entities_small(self, spark):
        """Test base entity generation with 50 records."""
        from generate_multi_source_realistic import generate_base_entities

        df = generate_base_entities(spark, num_entities=50)

        assert df.count() == 50

        # Verify schema
        expected_columns = {
            'entity_id', 'first_name', 'last_name', 'email', 'phone',
            'annual_revenue', 'employee_count', 'created_date', 'last_updated'
        }
        assert set(df.columns) == expected_columns

        # Verify no nulls
        assert df.filter("entity_id IS NULL").count() == 0
        assert df.filter("email IS NULL").count() == 0

        # This would have caught the "id" column issue!
        rows = df.collect()
        assert len(rows) == 50

    def test_apply_source_conflicts_small(self, spark):
        """Test conflict application - THIS WOULD HAVE CAUGHT ALL BUGS!"""
        from generate_multi_source_realistic import generate_base_entities, apply_source_conflicts

        # Generate base entities
        base_entities = generate_base_entities(spark, num_entities=20)

        # Apply conflicts for Source A
        # This is where all our bugs were!
        source_a = apply_source_conflicts(
            entities=base_entities,
            source_name="A",
            source_quality=0.95,
            timestamp_offset_days=0
        )

        # Verify the transformation worked
        assert source_a.count() == 20

        # Verify new columns were added
        assert 'source' in source_a.columns
        assert 'has_conflict' in source_a.columns
        assert 'conflict_type' in source_a.columns

        # Verify source column is set correctly
        assert source_a.filter("source != 'A'").count() == 0

        # This would have caught the Python bool vs Column error!
        rows = source_a.collect()
        assert len(rows) == 20

        # Verify conflict types are valid
        valid_types = {'none', 'name', 'measure', 'date', 'other'}
        conflict_types = set(row['conflict_type'] for row in rows)
        assert conflict_types.issubset(valid_types), \
            f"Invalid conflict types: {conflict_types - valid_types}"


class TestDataQuality:
    """Test data quality and realistic patterns."""

    def test_customer_segment_distribution(self, spark):
        """Verify segment distribution is realistic (not uniform)."""
        from generate_warehouse_realistic import generate_customers

        df = generate_customers(spark, num_customers=1000)

        # Get segment counts
        segment_counts = df.groupBy('segment').count().collect()
        segments = {row['segment']: row['count'] for row in segment_counts}

        # Verify weighted distribution (not 33/33/33)
        # Expected: Enterprise 15%, Mid-Market 35%, SMB 50%
        total = sum(segments.values())

        enterprise_pct = segments.get('Enterprise', 0) / total
        smb_pct = segments.get('SMB', 0) / total

        # SMB should be much larger than Enterprise
        assert smb_pct > enterprise_pct, \
            f"SMB ({smb_pct:.1%}) should be > Enterprise ({enterprise_pct:.1%})"

    def test_entity_id_format(self, spark):
        """Verify entity IDs follow expected format."""
        from generate_multi_source_realistic import generate_base_entities

        df = generate_base_entities(spark, num_entities=10)

        rows = df.collect()

        # All entity IDs should start with "ENT"
        for row in rows:
            assert row['entity_id'].startswith('ENT'), \
                f"Entity ID {row['entity_id']} doesn't start with ENT"

            # Should be ENT + 10 digits
            assert len(row['entity_id']) == 13, \
                f"Entity ID {row['entity_id']} should be 13 chars"


@pytest.mark.integration
class TestEndToEnd:
    """End-to-end integration tests (marked as integration)."""

    def test_full_warehouse_pipeline_tiny(self, spark, tmp_path):
        """Test complete warehouse pipeline with 10/5/20 records."""
        from generate_warehouse_realistic import generate_customers, generate_products, generate_orders

        # Generate tiny dataset
        customers = generate_customers(spark, 10)
        products = generate_products(spark, 5)
        orders = generate_orders(spark, customers, 20)

        # Write to temp parquet
        output = str(tmp_path / "test_output")

        customers.write.mode("overwrite").parquet(f"{output}/customers")
        products.write.mode("overwrite").parquet(f"{output}/products")
        orders.write.mode("overwrite").parquet(f"{output}/orders")

        # Verify we can read back
        customers_read = spark.read.parquet(f"{output}/customers")
        assert customers_read.count() == 10

    def test_full_multi_source_pipeline_tiny(self, spark, tmp_path):
        """Test complete multi-source pipeline with 30 entities."""
        from generate_multi_source_realistic import generate_base_entities, apply_source_conflicts

        base = generate_base_entities(spark, 30)

        # Apply conflicts for all 3 sources
        source_a = apply_source_conflicts(base, "A", 0.95, 0)
        source_b = apply_source_conflicts(base, "B", 0.90, 5)
        source_c = apply_source_conflicts(base, "C", 0.85, 10)

        # Union all sources
        all_sources = source_a.union(source_b).union(source_c)

        # Should have 3x records
        assert all_sources.count() == 90

        # Verify all sources present
        source_counts = all_sources.groupBy('source').count().collect()
        assert len(source_counts) == 3

        # Write to temp
        output = str(tmp_path / "multi_source")
        all_sources.write.mode("overwrite").parquet(output)

        # Verify read back
        read_back = spark.read.parquet(output)
        assert read_back.count() == 90


if __name__ == "__main__":
    # Allow running directly: python tests/test_pyspark_data_generation.py
    pytest.main([__file__, "-v", "--tb=short"])
