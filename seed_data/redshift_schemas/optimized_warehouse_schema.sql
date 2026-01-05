-- Optimized Redshift Schema for BrightAgent Load/Stress Testing
-- Star schema with proper DISTKEY/SORTKEY for 1B record scale
--
-- Performance optimizations:
-- 1. Small dimensions (customers, products) use DISTSTYLE ALL (replicated)
-- 2. Large fact table (orders) uses DISTKEY on customer_id for co-located joins
-- 3. SORTKEY on order_date for time-series query performance
-- 4. ENCODE AUTO for column compression
-- 5. ANALYZE after loading for accurate query planning

-- ========================================
-- Customers Dimension (small, ~1M records)
-- ========================================
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_id VARCHAR(20) NOT NULL PRIMARY KEY,
    company_name VARCHAR(200) NOT NULL,
    segment VARCHAR(20) NOT NULL,
    industry VARCHAR(50),
    num_employees BIGINT,
    annual_revenue BIGINT,
    lifetime_value DECIMAL(38,6),
    region VARCHAR(50),
    state VARCHAR(50),
    status VARCHAR(20),
    created_at DATE
)
DISTSTYLE ALL  -- Replicate small dimension across all nodes
SORTKEY (customer_id);  -- Sort by primary key for efficient lookups

COMMENT ON TABLE customers IS 'Customer dimension - replicated on all nodes for fast joins';

-- ========================================
-- Products Dimension (small, ~10K records)
-- ========================================
DROP TABLE IF EXISTS products CASCADE;

CREATE TABLE products (
    product_id VARCHAR(20) NOT NULL PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    unit_price BIGINT,
    inventory_quantity INTEGER
)
DISTSTYLE ALL  -- Replicate small dimension across all nodes
SORTKEY (category, product_id);  -- Compound sort for category queries

COMMENT ON TABLE products IS 'Product dimension - replicated on all nodes for fast joins';

-- ========================================
-- Orders Fact Table (large, 1B records)
-- ========================================
DROP TABLE IF EXISTS orders CASCADE;

CREATE TABLE orders (
    order_id VARCHAR(30) NOT NULL PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    order_timestamp TIMESTAMP NOT NULL,
    order_amount DECIMAL(24,2) NOT NULL,
    status VARCHAR(20),
    days_to_fulfill BIGINT,

    -- Foreign keys (not enforced in Redshift, for documentation only)
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
)
DISTKEY (customer_id)  -- Distribute by customer_id for co-located joins with customers table
SORTKEY (order_timestamp, customer_id);  -- Compound sort: time-series queries first, then customer lookups

COMMENT ON TABLE orders IS 'Orders fact table - distributed by customer_id, sorted by order_date for time-series queries';

-- ========================================
-- Multi-Source Conflict Data (Scenario S02)
-- ========================================
DROP TABLE IF EXISTS multi_source_entities CASCADE;

CREATE TABLE multi_source_entities (
    record_id VARCHAR(50) NOT NULL,
    source VARCHAR(10) NOT NULL,
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
    conflict_type VARCHAR(20),

    PRIMARY KEY (record_id, source)
)
DISTKEY (entity_id)  -- Distribute by entity_id for conflict resolution queries
SORTKEY (entity_id, source, last_updated);  -- Sort for entity-based conflict resolution

COMMENT ON TABLE multi_source_entities IS 'Multi-source data with realistic conflicts for resolution testing';

-- ========================================
-- Load Optimization Recommendations
-- ========================================

-- After loading data:
-- 1. Run ANALYZE to update statistics
--    ANALYZE customers;
--    ANALYZE products;
--    ANALYZE orders;
--    ANALYZE multi_source_entities;
--
-- 2. Run VACUUM to reclaim space and sort data
--    VACUUM SORT ONLY orders;
--    VACUUM SORT ONLY multi_source_entities;
--
-- 3. Check table statistics
--    SELECT "table", size, tbl_rows, skew_rows
--    FROM SVV_TABLE_INFO
--    WHERE schema = 'public'
--    ORDER BY size DESC;
--
-- 4. Monitor query performance
--    SELECT query, elapsed, rows, query_text
--    FROM STL_QUERY
--    WHERE userid > 1
--    ORDER BY starttime DESC
--    LIMIT 100;

-- ========================================
-- Common Query Patterns (for testing)
-- ========================================

-- Time-series aggregation (uses SORTKEY on order_date)
-- SELECT order_date, COUNT(*), SUM(order_amount)
-- FROM orders
-- WHERE order_date BETWEEN '2020-01-01' AND '2023-12-31'
-- GROUP BY order_date
-- ORDER BY order_date;

-- Customer revenue analysis (uses DISTKEY on customer_id)
-- SELECT c.company_name, c.segment, COUNT(o.order_id), SUM(o.order_amount)
-- FROM customers c
-- JOIN orders o ON c.customer_id = o.customer_id
-- WHERE o.order_date >= '2023-01-01'
-- GROUP BY c.company_name, c.segment
-- ORDER BY SUM(o.order_amount) DESC
-- LIMIT 100;

-- Product category performance (dimension replicated for fast joins)
-- SELECT p.category, COUNT(o.order_id), SUM(o.order_amount)
-- FROM products p
-- JOIN orders o ON p.product_id = o.product_id
-- WHERE o.order_date BETWEEN '2023-01-01' AND '2023-12-31'
-- GROUP BY p.category
-- ORDER BY SUM(o.order_amount) DESC;

-- Multi-source conflict resolution (uses SORTKEY on entity_id, source, last_updated)
-- SELECT entity_id, source, first_name, last_name, last_updated
-- FROM multi_source_entities
-- WHERE entity_id = 'ENT0000000001'
-- ORDER BY last_updated DESC;
