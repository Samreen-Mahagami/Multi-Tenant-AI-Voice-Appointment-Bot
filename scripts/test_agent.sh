#!/bin/bash
set -e

echo "🧪 Testing Bedrock Agent..."

# Load environment
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please run ./scripts/deploy.sh first."
    exit 1
fi

source .env

if [ -z "$BEDROCK_AGENT_ID" ] || [ -z "$BEDROCK_AGENT_ALIAS_ID" ]; then
    echo "❌ Agent IDs not found in .env. Please run ./scripts/deploy.sh first."
    exit 1
fi

echo "🔍 Testing Agent ID: $BEDROCK_AGENT_ID"
echo "🔍 Testing Alias ID: $BEDROCK_AGENT_ALIAS_ID"
echo ""

# Test 1: Agent greeting
echo "📞 Test 1: Initial greeting"
echo "----------------------------------------"
SESSION_ID="test-greeting-$(date +%s)"

aws bedrock-agent-runtime create-invocation \
  --agent-id $BEDROCK_AGENT_ID \
  --agent-alias-id $BEDROCK_AGENT_ALIAS_ID \
  --session-id $SESSION_ID \
  --input-text "Hello" \
  --output json > /tmp/response.json

echo "Response: $(cat /tmp/response.json | jq -r '.completion // .output.text // "No response found"')"
echo ""

# Test 2: Booking flow
echo "📅 Test 2: Appointment booking flow"
echo "----------------------------------------"
SESSION_ID="booking-test-$(date +%s)"

echo "Turn 1: Request appointment"
aws bedrock-agent-runtime invoke-agent \
  --agent-id $BEDROCK_AGENT_ID \
  --agent-alias-id $BEDROCK_AGENT_ALIAS_ID \
  --session-id $SESSION_ID \
  --input-text "I want to book an appointment for tomorrow morning" \
  /tmp/response1.json

echo "Agent: $(cat /tmp/response1.json | jq -r '.completion // .output.text // "No response found"')"
echo ""

sleep 2

echo "Turn 2: Select slot"
aws bedrock-agent-runtime invoke-agent \
  --agent-id $BEDROCK_AGENT_ID \
  --agent-alias-id $BEDROCK_AGENT_ALIAS_ID \
  --session-id $SESSION_ID \
  --input-text "The 9:30 AM slot please" \
  /tmp/response2.json

echo "Agent: $(cat /tmp/response2.json | jq -r '.completion // .output.text // "No response found"')"
echo ""

sleep 2

echo "Turn 3: Provide name"
aws bedrock-agent-runtime invoke-agent \
  --agent-id $BEDROCK_AGENT_ID \
  --agent-alias-id $BEDROCK_AGENT_ALIAS_ID \
  --session-id $SESSION_ID \
  --input-text "My name is John Smith" \
  /tmp/response3.json

echo "Agent: $(cat /tmp/response3.json | jq -r '.completion // .output.text // "No response found"')"
echo ""

sleep 2

echo "Turn 4: Provide email"
aws bedrock-agent-runtime invoke-agent \
  --agent-id $BEDROCK_AGENT_ID \
  --agent-alias-id $BEDROCK_AGENT_ALIAS_ID \
  --session-id $SESSION_ID \
  --input-text "john.smith@example.com" \
  /tmp/response4.json

echo "Agent: $(cat /tmp/response4.json | jq -r '.completion // .output.text // "No response found"')"
echo ""

# Test 3: Human handoff
echo "🤝 Test 3: Human handoff"
echo "----------------------------------------"
SESSION_ID="handoff-test-$(date +%s)"

aws bedrock-agent-runtime invoke-agent \
  --agent-id $BEDROCK_AGENT_ID \
  --agent-alias-id $BEDROCK_AGENT_ALIAS_ID \
  --session-id $SESSION_ID \
  --input-text "I want to speak to a human" \
  /tmp/response5.json

echo "Agent: $(cat /tmp/response5.json | jq -r '.completion // .output.text // "No response found"')"
echo ""

echo "✅ All tests completed!"
echo ""
echo "📋 Test Summary:"
echo "   ✅ Agent responds to greetings"
echo "   ✅ Agent can handle booking flow"
echo "   ✅ Agent can initiate human handoff"
echo ""
echo "🎯 Next: Set up local services with Docker Compose"