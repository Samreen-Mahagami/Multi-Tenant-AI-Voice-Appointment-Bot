#!/bin/bash
set -e

echo "🚀 Deploying Multi-Tenant AI Voice Appointment Bot Infrastructure..."

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI first."
    exit 1
fi

# Check CDK
if ! command -v cdk &> /dev/null; then
    echo "❌ AWS CDK not found. Installing..."
    npm install -g aws-cdk
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Check Bedrock model access
echo "🔍 Checking Bedrock model access..."
if aws bedrock list-foundation-models --query "modelSummaries[?modelId=='anthropic.claude-3-haiku-20240307-v1:0']" --output text | grep -q "anthropic.claude-3-haiku"; then
    echo "✅ Claude 3 Haiku model access confirmed"
else
    echo "⚠️  Claude 3 Haiku model access not found. Please enable it in AWS Console:"
    echo "   1. Go to Amazon Bedrock → Model access"
    echo "   2. Request access to Anthropic Claude 3 Haiku"
    echo "   3. Wait for approval (usually instant)"
    read -p "Press Enter after enabling model access..."
fi

# Install CDK dependencies
echo "📦 Installing CDK dependencies..."
cd infrastructure
npm install

# Build TypeScript
echo "🔨 Building CDK project..."
npm run build

# Bootstrap CDK (if needed)
echo "🏗️  Checking CDK bootstrap..."
if ! aws cloudformation describe-stacks --stack-name CDKToolkit &> /dev/null; then
    echo "🚀 Bootstrapping CDK..."
    cdk bootstrap
else
    echo "✅ CDK already bootstrapped"
fi

# Deploy infrastructure
echo "🚀 Deploying infrastructure..."
cdk deploy --all --require-approval never

# Get outputs
echo "📋 Getting deployment outputs..."
AGENT_ID=$(aws cloudformation describe-stacks \
  --stack-name IvrBedrockAgentStack \
  --query "Stacks[0].Outputs[?OutputKey=='AgentId'].OutputValue" \
  --output text)

ALIAS_ID=$(aws cloudformation describe-stacks \
  --stack-name IvrBedrockAgentStack \
  --query "Stacks[0].Outputs[?OutputKey=='AgentAliasId'].OutputValue" \
  --output text)

echo "✅ Deployment completed!"
echo ""
echo "📋 Deployment Information:"
echo "   Agent ID: $AGENT_ID"
echo "   Alias ID: $ALIAS_ID"

# Prepare the agent
echo "🔧 Preparing Bedrock Agent..."
aws bedrock-agent prepare-agent --agent-id $AGENT_ID

# Wait for agent to be ready
echo "⏳ Waiting for agent to be prepared..."
while true; do
    STATUS=$(aws bedrock-agent get-agent --agent-id $AGENT_ID --query "agent.agentStatus" --output text)
    if [ "$STATUS" = "PREPARED" ]; then
        echo "✅ Agent is ready!"
        break
    elif [ "$STATUS" = "FAILED" ]; then
        echo "❌ Agent preparation failed!"
        exit 1
    else
        echo "   Status: $STATUS (waiting...)"
        sleep 10
    fi
done

# Update .env file
cd ..
echo "📝 Updating .env file..."
if [ ! -f .env ]; then
    cp .env.example .env
fi

# Update or add the agent IDs
if grep -q "BEDROCK_AGENT_ID=" .env; then
    sed -i "s/BEDROCK_AGENT_ID=.*/BEDROCK_AGENT_ID=$AGENT_ID/" .env
else
    echo "BEDROCK_AGENT_ID=$AGENT_ID" >> .env
fi

if grep -q "BEDROCK_AGENT_ALIAS_ID=" .env; then
    sed -i "s/BEDROCK_AGENT_ALIAS_ID=.*/BEDROCK_AGENT_ALIAS_ID=$ALIAS_ID/" .env
else
    echo "BEDROCK_AGENT_ALIAS_ID=$ALIAS_ID" >> .env
fi

echo ""
echo "🎉 Deployment successful!"
echo ""
echo "📋 Next steps:"
echo "   1. Test the agent: ./scripts/test_agent.sh"
echo "   2. View agent in AWS Console: https://console.aws.amazon.com/bedrock/home#/agents"
echo "   3. Continue with local services setup"
echo ""