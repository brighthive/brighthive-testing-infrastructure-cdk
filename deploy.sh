#!/usr/bin/env bash
set -euo pipefail

# BrightAgent LOADSTRESS Infrastructure Deployment
# Deploy to us-west-2 (Oregon)

echo "🚀 BrightAgent LOADSTRESS Infrastructure Deployment"
echo "   Region: us-west-2 (Oregon)"
echo "   Account: 824267124830"
echo ""

# Load environment variables
if [ ! -f ".env.loadstress" ]; then
    echo "❌ Error: .env.loadstress not found"
    exit 1
fi

source .env.loadstress

# Verify credentials
echo "✓ Verifying AWS credentials..."
aws sts get-caller-identity --query 'Account' --output text > /dev/null || {
    echo "❌ AWS credentials not valid"
    exit 1
}

echo "✓ Credentials valid for account: $(aws sts get-caller-identity --query 'Account' --output text)"
echo "✓ Region: $AWS_REGION"
echo ""

# Check if REDSHIFT_MASTER_PASSWORD is set
if [ -z "${REDSHIFT_MASTER_PASSWORD:-}" ]; then
    echo "❌ Error: REDSHIFT_MASTER_PASSWORD not set"
    echo "   This password is required for Redshift cluster creation"
    exit 1
fi

echo "✓ Redshift password configured"
echo ""

# Deployment mode
DEPLOYMENT_MODE="${1:-subset}"
echo "📦 Deployment Mode: $DEPLOYMENT_MODE"
case $DEPLOYMENT_MODE in
    subset)
        echo "   - Redshift: 1 node (ra3.xlplus)"
        echo "   - EMR: 2 workers (16vCPU × 64GB)"
        echo "   - Data: 1M records (~100MB)"
        echo "   - Cost: ~\$37/day"
        ;;
    full)
        echo "   - Redshift: 2 nodes (ra3.xlplus)"
        echo "   - EMR: 20 workers (32vCPU × 128GB)"
        echo "   - Data: 1B records (~100GB)"
        echo "   - Cost: ~\$1,580/day"
        ;;
    *)
        echo "❌ Invalid deployment mode: $DEPLOYMENT_MODE"
        echo "   Usage: ./deploy.sh [subset|full]"
        exit 1
        ;;
esac
echo ""

# Confirm deployment
read -p "Deploy to us-west-2? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""
echo "🔨 Deploying 5 stacks..."
echo "   1. VPC (networking)"
echo "   2. Data Lake (S3 storage)"
echo "   3. Redshift (data warehouse)"
echo "   4. EMR (data generation)"
echo "   5. Monitoring (CloudWatch logs, dashboards, alarms)"
echo ""

# Deploy all stacks
cdk deploy --all --require-approval never

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Stack Outputs:"
echo "   View outputs: aws cloudformation describe-stacks --region us-west-2"
echo ""
echo "📈 Monitoring & Observability:"
echo "   Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#dashboards:name=BrightAgent-LOADSTRESS"
echo "   Log Groups:"
echo "     - VPC Flow: /aws/vpc/brightagent-loadstress"
echo "     - Redshift: /aws/redshift/brightagent-loadstress"
echo "     - EMR: /aws/emr-serverless/brightagent-loadstress"
echo "     - ECS: /aws/ecs/brightagent-loadstress"
echo "   Full guide: OBSERVABILITY_GUIDE.md"
echo ""
echo "🎯 Next Steps:"
echo "   1. Confirm alarm subscription (sent to kuri@brighthive.io)"
echo "      Check email and click confirmation link"
echo ""
echo "   2. Generate baseline data (see README.md for full commands):"
echo "      export EMR_APP_ID=\$(aws cloudformation describe-stacks --stack-name BrightAgent-LOADSTRESS-EMR --query 'Stacks[0].Outputs[?OutputKey==\`EMRApplicationId\`].OutputValue' --output text --region us-west-2)"
echo "      aws emr-serverless start-job-run --application-id \$EMR_APP_ID ..."
echo ""
echo "   3. Deploy Redshift schemas:"
echo "      cd seed_data/redshift_schemas && ./deploy_schemas.sh"
echo ""
echo "   4. Run scenarios:"
echo "      See SCENARIO_IMPLEMENTATION_PLAN.md"
echo ""
