#!/bin/bash
set -e

echo "🚀 Testing FreeSWITCH Integration"
echo "=================================="

# Load environment variables
if [ -f .env ]; then
    source .env
fi

# Check required environment variables
if [ -z "$BEDROCK_AGENT_ID" ] || [ -z "$BEDROCK_AGENT_ALIAS_ID" ]; then
    echo "❌ Missing required environment variables:"
    echo "   BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS_ID must be set"
    echo ""
    echo "Run this first:"
    echo "   source .env"
    exit 1
fi

echo "✅ Environment variables loaded"
echo "   BEDROCK_AGENT_ID: $BEDROCK_AGENT_ID"
echo "   BEDROCK_AGENT_ALIAS_ID: $BEDROCK_AGENT_ALIAS_ID"
echo ""

# Start services
echo "🔧 Starting all services..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Test service health
echo ""
echo "🏥 Testing service health..."

echo "1. Tenant Config Service:"
curl -s http://localhost:7001/v1/health | jq . || echo "❌ Failed"

echo ""
echo "2. Appointment Service:"
curl -s http://localhost:7002/v1/health | jq . || echo "❌ Failed"

echo ""
echo "3. Media Gateway:"
curl -s http://localhost:8080/health | jq . || echo "❌ Failed"

echo ""
echo "4. FreeSWITCH Status:"
docker exec freeswitch fs_cli -x "status" | head -5 || echo "❌ FreeSWITCH not ready"

echo ""
echo "📞 FreeSWITCH Integration Ready!"
echo "================================"
echo ""
echo "To test with softphone:"
echo "1. Download Zoiper or X-Lite"
echo "2. Configure:"
echo "   Server: localhost:5060"
echo "   Username: 1000"
echo "   Password: 1234"
echo "   Transport: UDP"
echo ""
echo "3. Call extensions:"
echo "   1001 → Downtown Medical Center"
echo "   1002 → Westside Family Practice"
echo "   1003 → Pediatric Care Clinic"
echo ""
echo "🎯 Expected Flow:"
echo "   Call → FreeSWITCH → Media Gateway → Transcribe → Bedrock Agent → Polly → Response"
echo ""