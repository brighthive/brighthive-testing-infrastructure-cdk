#!/bin/bash
# Deploy optimized Redshift schemas for BrightAgent Load/Stress Testing
#
# Usage:
#   ./deploy_schemas.sh
#
# Prerequisites:
#   - AWS CLI configured with proper credentials
#   - Redshift cluster deployed via CDK
#   - REDSHIFT_MASTER_PASSWORD environment variable set

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="BrightAgent-LOADSTRESS-Redshift"
CLUSTER_ID="brightagent-loadstress-redshift"
DATABASE_NAME="brightagent_loadstress"
USERNAME="admin"

echo -e "${GREEN}=== Redshift Schema Deployment ===${NC}\n"

# Check prerequisites
if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI not found${NC}"
    echo "Please install AWS CLI: https://aws.amazon.com/cli/"
    exit 1
fi

if [ -z "${REDSHIFT_MASTER_PASSWORD:-}" ]; then
    echo -e "${RED}ERROR: REDSHIFT_MASTER_PASSWORD environment variable not set${NC}"
    echo "Please set it: export REDSHIFT_MASTER_PASSWORD='YourSecurePassword123!'"
    echo "Or source your environment: source .env.loadstress"
    exit 1
fi

# Get cluster endpoint from CDK outputs
echo "Fetching Redshift cluster endpoint..."
REDSHIFT_HOST=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`RedshiftClusterEndpoint`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ -z "$REDSHIFT_HOST" ]; then
    echo -e "${RED}ERROR: Could not retrieve Redshift endpoint${NC}"
    echo "Stack name: $STACK_NAME"
    echo "Make sure the Redshift stack is deployed"
    exit 1
fi

echo -e "${GREEN}✓${NC} Cluster endpoint: $REDSHIFT_HOST"

# Check if cluster is available
echo "Checking cluster status..."
CLUSTER_STATUS=$(aws redshift describe-clusters \
    --cluster-identifier "$CLUSTER_ID" \
    --query 'Clusters[0].ClusterStatus' \
    --output text 2>/dev/null || echo "not-found")

if [ "$CLUSTER_STATUS" != "available" ]; then
    echo -e "${RED}ERROR: Cluster not available (status: $CLUSTER_STATUS)${NC}"
    echo "Wait for cluster to be available before deploying schemas"
    exit 1
fi

echo -e "${GREEN}✓${NC} Cluster status: $CLUSTER_STATUS"

# Deploy schemas using psql if available, otherwise use Redshift Data API
if command -v psql &> /dev/null; then
    echo -e "\n${YELLOW}Deploying schemas using psql...${NC}"

    export PGPASSWORD="$REDSHIFT_MASTER_PASSWORD"
    psql "postgresql://${USERNAME}@${REDSHIFT_HOST}:5439/${DATABASE_NAME}" \
        -f optimized_warehouse_schema.sql \
        --echo-errors \
        --set ON_ERROR_STOP=1

    unset PGPASSWORD

    echo -e "${GREEN}✓${NC} Schemas deployed successfully via psql"
else
    echo -e "\n${YELLOW}psql not found, using Redshift Data API...${NC}"
    echo "Note: This method is async. Check execution status in AWS Console."

    # Execute schema creation via Redshift Data API
    STATEMENT_ID=$(aws redshift-data execute-statement \
        --cluster-identifier "$CLUSTER_ID" \
        --database "$DATABASE_NAME" \
        --db-user "$USERNAME" \
        --sql "$(cat optimized_warehouse_schema.sql)" \
        --query 'Id' \
        --output text)

    echo "Statement ID: $STATEMENT_ID"
    echo "Waiting for execution to complete..."

    # Poll for completion (max 5 minutes)
    MAX_ATTEMPTS=60
    ATTEMPT=0
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        STATUS=$(aws redshift-data describe-statement \
            --id "$STATEMENT_ID" \
            --query 'Status' \
            --output text)

        if [ "$STATUS" = "FINISHED" ]; then
            echo -e "${GREEN}✓${NC} Schemas deployed successfully via Redshift Data API"
            break
        elif [ "$STATUS" = "FAILED" ]; then
            echo -e "${RED}ERROR: Statement execution failed${NC}"
            aws redshift-data describe-statement --id "$STATEMENT_ID"
            exit 1
        fi

        echo -n "."
        sleep 5
        ATTEMPT=$((ATTEMPT + 1))
    done

    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        echo -e "\n${YELLOW}WARNING: Timed out waiting for completion${NC}"
        echo "Check status manually: aws redshift-data describe-statement --id $STATEMENT_ID"
    fi
fi

# Verify tables were created
echo -e "\n${YELLOW}Verifying table creation...${NC}"

VERIFY_SQL="SELECT table_name, size, tbl_rows FROM SVV_TABLE_INFO WHERE schema = 'public' ORDER BY table_name;"

if command -v psql &> /dev/null; then
    export PGPASSWORD="$REDSHIFT_MASTER_PASSWORD"
    psql "postgresql://${USERNAME}@${REDSHIFT_HOST}:5439/${DATABASE_NAME}" \
        -c "$VERIFY_SQL" \
        --tuples-only
    unset PGPASSWORD
else
    VERIFY_ID=$(aws redshift-data execute-statement \
        --cluster-identifier "$CLUSTER_ID" \
        --database "$DATABASE_NAME" \
        --db-user "$USERNAME" \
        --sql "$VERIFY_SQL" \
        --query 'Id' \
        --output text)

    sleep 3
    aws redshift-data get-statement-result --id "$VERIFY_ID" \
        --query 'Records' \
        --output table
fi

echo -e "\n${GREEN}=== Deployment Complete ===${NC}"
echo -e "\nNext steps:"
echo "1. Load data using COPY commands (see README.md)"
echo "2. Run ANALYZE on all tables"
echo "3. Run VACUUM SORT ONLY on large tables"
echo "4. Monitor query performance using SVL_QUERY_SUMMARY"
echo ""
echo "Example COPY command:"
echo "  COPY customers FROM 's3://brightagent-loadstress-data-824267124830/warehouse/customers/'"
echo "  IAM_ROLE 'arn:aws:iam::824267124830:role/brightagent-loadstress-emr-job-role'"
echo "  FORMAT AS PARQUET;"
