#!/bin/bash

# Simple test using AWS CLI directly
echo "🧪 Testing Bedrock Agent with AWS CLI..."

source .env

echo "Agent ID: $BEDROCK_AGENT_ID"
echo "Alias ID: $BEDROCK_AGENT_ALIAS_ID"

# Test if we can at least get agent info
echo "📋 Getting agent information..."
aws bedrock-agent get-agent --agent-id $BEDROCK_AGENT_ID

echo ""
echo "📋 Getting agent alias information..."
aws bedrock-agent get-agent-alias --agent-id $BEDROCK_AGENT_ID --agent-alias-id $BEDROCK_AGENT_ALIAS_ID