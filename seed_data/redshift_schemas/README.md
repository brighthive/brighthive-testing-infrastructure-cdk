# Redshift Optimized Schemas for BrightAgent Load/Stress Testing

## Overview

This directory contains optimized Redshift table schemas designed for 1B record scale testing. The schemas implement best practices for distribution keys (DISTKEY), sort keys (SORTKEY), and compression to maximize query performance.

## Performance Optimizations

### 1. Distribution Strategy

**Small Dimensions (DISTSTYLE ALL)**:
- `customers` table (~1M records): Replicated on all nodes
- `products` table (~10K records): Replicated on all nodes
- **Why**: Small tables are replicated to avoid network transfer during joins

**Large Fact Tables (DISTKEY)**:
- `orders` table (1B records): Distributed by `customer_id`
- `multi_source_entities` table (100K-1M records): Distributed by `entity_id`
- **Why**: Co-locates related data on same nodes for faster joins

### 2. Sort Key Strategy

**Time-Series Queries**:
- `orders` table: `SORTKEY (order_date, customer_id)`
- Optimizes date range queries (common in analytics)

**Lookup Queries**:
- `customers` table: `SORTKEY (customer_id)`
- `products` table: `SORTKEY (category, product_id)`

**Conflict Resolution**:
- `multi_source_entities`: `SORTKEY (entity_id, source, last_updated)`
- Optimizes entity-based conflict resolution queries

### 3. Compression

- All tables use `ENCODE AUTO` (Redshift default)
- Redshift automatically selects best compression per column
- Typical compression: 3-5x for analytics data

## Schema Deployment

### Prerequisites

1. Redshift cluster deployed and accessible
2. Database credentials (master username/password)
3. Network access to Redshift endpoint

### Deploy Schemas

```bash
# Set environment variables (source from .env.loadstress or set manually)
source ../../.env.loadstress

export REDSHIFT_HOST=$(aws cloudformation describe-stacks \
  --stack-name BrightAgent-LOADSTRESS-Redshift \
  --query 'Stacks[0].Outputs[?OutputKey==`RedshiftClusterEndpoint`].OutputValue' \
  --output text --region us-west-2)

export REDSHIFT_PORT=5439
export REDSHIFT_DB="brightagent_loadstress"
export REDSHIFT_USER="admin"
# REDSHIFT_MASTER_PASSWORD already set from .env.loadstress

# Connect and create schemas
psql "postgresql://${REDSHIFT_USER}:${REDSHIFT_MASTER_PASSWORD}@${REDSHIFT_HOST}:${REDSHIFT_PORT}/${REDSHIFT_DB}" \
  -f optimized_warehouse_schema.sql
```

### Alternative: Using AWS CLI

```bash
# Get cluster endpoint from CDK outputs
REDSHIFT_HOST=$(aws cloudformation describe-stacks \
  --stack-name BrightAgent-LOADSTRESS-Redshift \
  --query 'Stacks[0].Outputs[?OutputKey==`RedshiftClusterEndpoint`].OutputValue' \
  --output text)

# Run SQL via Redshift Data API
aws redshift-data execute-statement \
  --cluster-identifier brightagent-loadstress-redshift \
  --database brightagent_loadstress \
  --sql "$(cat optimized_warehouse_schema.sql)"
```

## Post-Deployment Optimization

### 1. Load Data

Use COPY command for bulk loading (10-100x faster than INSERT):

```sql
-- Load customers from S3
COPY customers
FROM 's3://brightagent-loadstress-data-824267124830/warehouse/customers/'
IAM_ROLE 'arn:aws:iam::824267124830:role/RedshiftLoadRole'
FORMAT AS PARQUET;

-- Load products
COPY products
FROM 's3://brightagent-loadstress-data-824267124830/warehouse/products/'
IAM_ROLE 'arn:aws:iam::824267124830:role/RedshiftLoadRole'
FORMAT AS PARQUET;

-- Load orders (1B records)
COPY orders
FROM 's3://brightagent-loadstress-data-824267124830/warehouse/orders/'
IAM_ROLE 'arn:aws:iam::824267124830:role/RedshiftLoadRole'
FORMAT AS PARQUET;
```

### 2. Analyze Tables

Update query planner statistics after loading:

```sql
ANALYZE customers;
ANALYZE products;
ANALYZE orders;
ANALYZE multi_source_entities;
```

### 3. Vacuum Tables

Reclaim space and re-sort data:

```sql
VACUUM SORT ONLY orders;
VACUUM SORT ONLY multi_source_entities;
```

### 4. Verify Optimization

Check table distribution and skew:

```sql
SELECT
    "table",
    size,
    tbl_rows,
    skew_rows,
    skew_sortkey1,
    CASE
        WHEN skew_rows > 1.5 THEN 'HIGH SKEW - Check DISTKEY'
        WHEN skew_rows > 1.2 THEN 'MODERATE SKEW'
        ELSE 'OK'
    END AS skew_status
FROM SVV_TABLE_INFO
WHERE schema = 'public'
ORDER BY size DESC;
```

## Query Performance Testing

### Time-Series Aggregation

```sql
-- Should use SORTKEY on order_date (zone map pruning)
EXPLAIN
SELECT
    order_date,
    COUNT(*) as order_count,
    SUM(total_amount) as revenue
FROM orders
WHERE order_date BETWEEN '2020-01-01' AND '2023-12-31'
GROUP BY order_date
ORDER BY order_date;
```

**Expected**: `XN Seq Scan` with zone map pruning (blocks skipped)

### Customer Revenue Analysis

```sql
-- Should use DISTKEY co-location (no broadcast)
EXPLAIN
SELECT
    c.customer_name,
    c.segment,
    COUNT(o.order_id) as order_count,
    SUM(o.total_amount) as lifetime_value
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_date >= '2023-01-01'
GROUP BY c.customer_name, c.segment
ORDER BY lifetime_value DESC
LIMIT 100;
```

**Expected**: `XN Hash Join DS_DIST_NONE` (no data redistribution)

### Product Category Performance

```sql
-- Should use replicated dimension (no network transfer)
EXPLAIN
SELECT
    p.category,
    COUNT(o.order_id) as order_count,
    SUM(o.total_amount) as category_revenue
FROM products p
JOIN orders o ON p.product_id = o.product_id
WHERE o.order_date BETWEEN '2023-01-01' AND '2023-12-31'
GROUP BY p.category
ORDER BY category_revenue DESC;
```

**Expected**: `XN Hash Join DS_BCAST_INNER` (products broadcasted, already replicated)

## Performance Benchmarks

### Expected Query Performance (1B records)

| Query Type | Expected Time | Notes |
|------------|---------------|-------|
| Time-series aggregation | 5-15s | Uses zone map pruning on SORTKEY |
| Customer revenue (top 100) | 10-30s | Co-located join, no data movement |
| Product category aggregation | 15-45s | Replicated dimension join |
| Full table scan | 2-5 min | Parallel scan across all nodes |

### Optimization Impact

| Metric | Without DISTKEY/SORTKEY | With Optimization | Improvement |
|--------|-------------------------|-------------------|-------------|
| Customer joins | 60-120s | 10-30s | 4-6x faster |
| Date range queries | 45-90s | 5-15s | 6-9x faster |
| Storage size | 100GB raw | 20-25GB compressed | 4-5x reduction |

## Troubleshooting

### High Skew Detected

```sql
-- Check data distribution
SELECT slice, COUNT(*) as row_count
FROM orders
GROUP BY slice
ORDER BY row_count DESC;
```

**Fix**: Choose a different DISTKEY with better cardinality

### Slow Queries Despite SORTKEY

```sql
-- Check if VACUUM is needed
SELECT "table", unsorted
FROM SVV_TABLE_INFO
WHERE schema = 'public';
```

**Fix**: Run `VACUUM SORT ONLY orders;` or `VACUUM SORT ONLY multi_source_entities;` if unsorted > 10%

### Disk-Based Queries

```sql
-- Check for disk spill
SELECT query, step, rows, workmem, is_diskbased
FROM SVL_QUERY_SUMMARY
WHERE is_diskbased = 't'
ORDER BY query DESC
LIMIT 10;
```

**Fix**: Increase WLM queue memory allocation or reduce query concurrency

## References

- [Redshift Best Practices - Distribution Styles](https://docs.aws.amazon.com/redshift/latest/dg/c_best-practices-best-dist-key.html)
- [Redshift Best Practices - Sort Keys](https://docs.aws.amazon.com/redshift/latest/dg/c_best-practices-sort-key.html)
- [Redshift Best Practices - Loading Data](https://docs.aws.amazon.com/redshift/latest/dg/c_best-practices-use-copy.html)
