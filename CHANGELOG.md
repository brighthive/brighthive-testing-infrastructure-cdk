# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Realistic Data Generation**: Realistic mock data generators using Faker with weighted distributions, correlations, and seasonality patterns
  - `seed_data/emr_jobs/generate_warehouse_realistic.py` - Star schema warehouse data with business-realistic patterns
  - `seed_data/emr_jobs/generate_multi_source_realistic.py` - Multi-source conflict data for data quality testing
  - `DATA_GENERATION_APPROACH.md` - Documentation of 10 key realistic data generation patterns
- **Redshift WLM Configuration**: 3-queue workload management setup (ETL 50%, Analytics 35%, Short Query 15%)
  - Query monitoring rules: Abort queries >5min, log high CPU queries, log disk spills
  - Parameter group with user activity logging enabled
  - Concurrency scaling support
- **Optimized Redshift Schemas**: Production-ready table definitions with DISTKEY/SORTKEY
  - `seed_data/redshift_schemas/optimized_warehouse_schema.sql` - Star schema with performance optimizations
  - `seed_data/redshift_schemas/deploy_schemas.sh` - Automated schema deployment script
  - `seed_data/redshift_schemas/README.md` - Complete optimization guide with performance benchmarks
  - Expected performance: 4-9x faster queries, 4-5x storage compression
- **Enhanced CloudWatch Alarms**:
  - Redshift slow query alarm (>30s threshold)
  - EMR job failure alarm (critical for data generation)
  - SNS email subscription auto-configured to kuri@brighthive.io
- **S3 Cost Optimization**: Intelligent-Tiering lifecycle rule (~40% storage cost savings)
- **Dynamic EMR Scaling**: Deployment-mode-specific worker sizing
  - SUBSET: 2 workers × 16vCPU × 64GB = 128GB total
  - FULL: 20 workers × 32vCPU × 128GB = 2.5TB total
  - Maximum capacity increased to 800vCPU / 3200GB

### Changed
- **EMR Resources (FULL mode)**: Doubled from 10 to 20 workers with larger instance sizes
  - Worker CPU: 16vCPU → 32vCPU
  - Worker memory: 64GB → 128GB
  - **Impact**: 1B record generation time reduced from 10+ hours to 2-3 hours
- **Cost Estimates Updated**:
  - SUBSET mode: $35/day → $37/day
  - FULL mode: $1,400/day → $1,580/day (+$180/day for EMR capacity)
- **Monitoring Stack**: Added SNS subscriptions and additional alarms
- **README.md**: Updated with latest infrastructure changes, cost estimates, and optimization guides
- **OBSERVABILITY_GUIDE.md**: Added WLM configuration section, new alarms documentation

### Removed
- Empty/unused files: `src/brighthive_loadstress_cdk/health.py`, `src/brighthive_loadstress_cdk/metrics.py`

### Fixed
- SNS topic now has email subscriber (kuri@brighthive.io) - alarms will be delivered
- EMR failure detection - added CloudWatch alarm for failed jobs
- Slow query detection - added alarm for queries exceeding 30 seconds

## [0.1.0] - 2026-01-03

### Added
- Initial CDK infrastructure deployment for LOADSTRESS environment
- 5 core stacks: VPC, DataLake, Redshift, EMR, Monitoring
- CloudWatch logging for all services (7-day retention)
- CloudWatch dashboard with Redshift, S3, and VPC metrics
- Basic CloudWatch alarms (CPU, connections, disk space)
- Deployment modes: SUBSET (1M records) and FULL (1B records)
- Project structure with modern Python tooling (uv, ruff, mypy)
- Comprehensive documentation (README, OBSERVABILITY_GUIDE, SCENARIO_IMPLEMENTATION_PLAN)

[Unreleased]
[0.1.0] - 2026-01-03
