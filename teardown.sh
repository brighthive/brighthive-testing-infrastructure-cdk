#!/bin/bash
# Teardown script for BrightAgent Load/Stress Testing Infrastructure
# Safely destroys all AWS resources to stop costs

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "  BrightAgent Infrastructure Teardown"
echo "=============================================="
echo ""

# Check for required environment variables
if [ -f ".env.loadstress" ]; then
    echo -e "${GREEN}✓${NC} Found .env.loadstress"
    source .env.loadstress
else
    echo -e "${RED}✗${NC} .env.loadstress not found!"
    echo "Please create .env.loadstress with AWS credentials"
    exit 1
fi

# Confirm with user
echo -e "${YELLOW}WARNING:${NC} This will destroy ALL infrastructure and data!"
echo "  - VPC, subnets, NAT gateways"
echo "  - Redshift cluster and all data"
echo "  - EMR Serverless application"
echo "  - S3 bucket and all Parquet files"
echo "  - CloudWatch logs and dashboards"
echo ""
read -p "Are you sure you want to proceed? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Teardown cancelled."
    exit 0
fi

echo ""
echo "=============================================="
echo "Step 1: Empty S3 Bucket"
echo "=============================================="

# Find S3 bucket
BUCKET_NAME=$(aws s3 ls | grep brightagent-loadstress-data | awk '{print $3}')

if [ -n "$BUCKET_NAME" ]; then
    echo "Found bucket: $BUCKET_NAME"

    # Count objects
    OBJECT_COUNT=$(aws s3 ls s3://$BUCKET_NAME --recursive --summarize | grep "Total Objects" | awk '{print $3}')

    if [ "$OBJECT_COUNT" -gt 0 ]; then
        echo "Deleting $OBJECT_COUNT objects from S3..."
        aws s3 rm s3://$BUCKET_NAME/ --recursive
        echo -e "${GREEN}✓${NC} S3 bucket emptied"
    else
        echo "S3 bucket already empty"
    fi
else
    echo "No S3 bucket found (may already be deleted)"
fi

echo ""
echo "=============================================="
echo "Step 2: Destroy CDK Stacks"
echo "=============================================="

# Check if stacks exist
STACK_COUNT=$(aws cloudformation list-stacks \
    --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
    --query 'StackSummaries[?contains(StackName, `BrightAgent-LOADSTRESS`)].StackName' \
    --output text \
    --region $AWS_REGION | wc -w)

if [ "$STACK_COUNT" -gt 0 ]; then
    echo "Found $STACK_COUNT stack(s) to destroy"
    echo ""

    # Destroy all stacks (CDK handles dependency order)
    cdk destroy --all --force

    echo ""
    echo -e "${GREEN}✓${NC} All stacks destroyed"
else
    echo "No active stacks found"
fi

echo ""
echo "=============================================="
echo "Step 3: Verify Cleanup"
echo "=============================================="

# Check for remaining resources
echo "Checking for remaining resources..."

# Check CloudFormation stacks
REMAINING_STACKS=$(aws cloudformation list-stacks \
    --query 'StackSummaries[?contains(StackName, `BrightAgent-LOADSTRESS`) && StackStatus != `DELETE_COMPLETE`].{Name:StackName,Status:StackStatus}' \
    --output table \
    --region $AWS_REGION)

if [ -z "$REMAINING_STACKS" ]; then
    echo -e "${GREEN}✓${NC} No remaining CloudFormation stacks"
else
    echo -e "${YELLOW}!${NC} Remaining stacks:"
    echo "$REMAINING_STACKS"
fi

# Check S3 buckets
REMAINING_BUCKETS=$(aws s3 ls | grep brightagent-loadstress)

if [ -z "$REMAINING_BUCKETS" ]; then
    echo -e "${GREEN}✓${NC} No remaining S3 buckets"
else
    echo -e "${YELLOW}!${NC} Remaining S3 buckets:"
    echo "$REMAINING_BUCKETS"
fi

# Check EMR applications
REMAINING_EMR=$(aws emr-serverless list-applications \
    --region $AWS_REGION \
    --query 'applications[?contains(name, `brightagent`)].{Name:name,State:state}' \
    --output table)

if [ -z "$REMAINING_EMR" ]; then
    echo -e "${GREEN}✓${NC} No remaining EMR applications"
else
    echo -e "${YELLOW}!${NC} Remaining EMR applications:"
    echo "$REMAINING_EMR"
fi

echo ""
echo "=============================================="
echo "  Teardown Complete!"
echo "=============================================="
echo ""
echo "Summary:"
echo "  • Infrastructure: DESTROYED"
echo "  • AWS Costs: \$0/hour"
echo "  • Code: Preserved in Git"
echo ""
echo "To redeploy later, run: ./deploy.sh subset"
echo ""
