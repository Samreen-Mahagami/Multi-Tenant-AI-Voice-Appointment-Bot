#!/bin/bash
set -e

echo "🚀 Deploying Go Services as AWS Lambda Functions"
echo "================================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check prerequisites
echo "🔍 Checking Prerequisites..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found${NC}"
    exit 1
fi

# Check CDK
if ! command -v cdk &> /dev/null; then
    echo -e "${RED}❌ AWS CDK not found${NC}"
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found${NC}"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites met${NC}"

# Get AWS account info
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")

echo -e "${BLUE}📋 Deployment Info:${NC}"
echo "   AWS Account: $AWS_ACCOUNT"
echo "   AWS Region: $AWS_REGION"
echo ""

# Update Go modules
echo "📦 Updating Go Dependencies..."
cd tenant-config-go
go mod tidy
cd ../appointment-service-go
go mod tidy
cd ..

echo -e "${GREEN}✅ Go dependencies updated${NC}"

# Build and deploy with CDK
echo ""
echo "🏗️ Building and Deploying Go Services..."
cd infrastructure

# Install CDK dependencies
echo "Installing CDK dependencies..."
npm install

# Bootstrap CDK if needed
echo "Checking CDK bootstrap..."
if ! aws cloudformation describe-stacks --stack-name CDKToolkit --region $AWS_REGION &> /dev/null; then
    echo "Bootstrapping CDK..."
    cdk bootstrap aws://$AWS_ACCOUNT/$AWS_REGION
fi

# Deploy Go services stack
echo ""
echo -e "${YELLOW}🚀 Deploying Go Services Stack...${NC}"
cdk deploy IvrGoServicesStack --require-approval never

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Go Services deployed successfully!${NC}"
else
    echo -e "${RED}❌ Go Services deployment failed${NC}"
    exit 1
fi

# Get the deployed service URLs
echo ""
echo "📋 Getting Service URLs..."
TENANT_CONFIG_URL=$(aws cloudformation describe-stacks \
    --stack-name IvrGoServicesStack \
    --query 'Stacks[0].Outputs[?OutputKey==`TenantConfigServiceUrl`].OutputValue' \
    --output text \
    --region $AWS_REGION)

APPOINTMENT_SERVICE_URL=$(aws cloudformation describe-stacks \
    --stack-name IvrGoServicesStack \
    --query 'Stacks[0].Outputs[?OutputKey==`AppointmentServiceUrl`].OutputValue' \
    --output text \
    --region $AWS_REGION)

echo -e "${BLUE}🔗 Service URLs:${NC}"
echo "   Tenant Config: $TENANT_CONFIG_URL"
echo "   Appointment Service: $APPOINTMENT_SERVICE_URL"

# Test the deployed services
echo ""
echo "🧪 Testing Deployed Services..."

# Test tenant config service
echo "Testing Tenant Config Service..."
HEALTH_RESPONSE=$(curl -s "${TENANT_CONFIG_URL}v1/health" || echo "ERROR")
if [[ $HEALTH_RESPONSE == *"healthy"* ]]; then
    echo -e "${GREEN}✅ Tenant Config Service is healthy${NC}"
else
    echo -e "${RED}❌ Tenant Config Service health check failed${NC}"
    echo "Response: $HEALTH_RESPONSE"
fi

# Test appointment service
echo "Testing Appointment Service..."
HEALTH_RESPONSE=$(curl -s "${APPOINTMENT_SERVICE_URL}v1/health" || echo "ERROR")
if [[ $HEALTH_RESPONSE == *"healthy"* ]]; then
    echo -e "${GREEN}✅ Appointment Service is healthy${NC}"
else
    echo -e "${RED}❌ Appointment Service health check failed${NC}"
    echo "Response: $HEALTH_RESPONSE"
fi

# Update Lambda functions with new URLs
echo ""
echo "🔄 Updating Lambda Functions..."

# Deploy updated Lambda stack
echo "Deploying updated Lambda functions..."
cdk deploy IvrLambdaStack --require-approval never

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Lambda functions updated successfully!${NC}"
else
    echo -e "${RED}❌ Lambda functions update failed${NC}"
    exit 1
fi

cd ..

# Final summary
echo ""
echo "🎉 Deployment Complete!"
echo "======================="
echo -e "${GREEN}✅ Go Services deployed as Lambda functions${NC}"
echo -e "${GREEN}✅ API Gateway endpoints created${NC}"
echo -e "${GREEN}✅ Lambda functions updated with service URLs${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "   1. Test end-to-end integration with Bedrock Agent"
echo "   2. Run: python3 scripts/test_end_to_end.py"
echo "   3. Validate appointment booking workflow"
echo ""
echo -e "${BLUE}🔗 Service Endpoints:${NC}"
echo "   Tenant Config: $TENANT_CONFIG_URL"
echo "   Appointments: $APPOINTMENT_SERVICE_URL"