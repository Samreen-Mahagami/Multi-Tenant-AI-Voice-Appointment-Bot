#!/bin/bash
set -e

echo "🧪 Testing Lambda Functions with Local Go Services"
echo "=================================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if Go services are running
echo "📋 Checking if Go services are running..."
if ! curl -s http://localhost:7001/v1/health > /dev/null; then
    echo -e "${RED}❌ Tenant Config Service not running${NC}"
    echo "Please start services with: docker compose up -d"
    exit 1
fi

if ! curl -s http://localhost:7002/v1/health > /dev/null; then
    echo -e "${RED}❌ Appointment Service not running${NC}"
    echo "Please start services with: docker compose up -d"
    exit 1
fi

echo -e "${GREEN}✅ Both Go services are running${NC}"
echo ""

# Test search-slots Lambda locally
echo "🔍 Testing search-slots Lambda function..."
echo "==========================================="

# Create test event for search-slots
cat > /tmp/search-slots-event.json <<EOF
{
  "actionGroup": "AppointmentActions",
  "apiPath": "/searchSlots",
  "httpMethod": "POST",
  "requestBody": {
    "content": {
      "application/json": {
        "properties": [
          {"name": "tenant_id", "value": "downtown_medical"},
          {"name": "date", "value": "tomorrow"},
          {"name": "time_preference", "value": "morning"}
        ]
      }
    }
  },
  "sessionAttributes": {},
  "promptSessionAttributes": {}
}
EOF

# Run Lambda function locally using Python
cd lambda/search-slots
export APPOINTMENT_SERVICE_URL="http://localhost:7002"

echo "Running search-slots handler..."
python3 -c "
import json
import index

with open('/tmp/search-slots-event.json', 'r') as f:
    event = json.load(f)

result = index.handler(event, None)
print(json.dumps(result, indent=2))

# Validate response
response = result.get('response', {})
status_code = response.get('httpStatusCode', 0)
if status_code == 200:
    print('\n✅ search-slots Lambda test PASSED')
else:
    print(f'\n❌ search-slots Lambda test FAILED (status: {status_code})')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ search-slots Lambda works with Go services${NC}"
else
    echo -e "${RED}❌ search-slots Lambda test failed${NC}"
    exit 1
fi

cd ../..
echo ""

# Test confirm-appointment Lambda locally
echo "📝 Testing confirm-appointment Lambda function..."
echo "================================================="

# First, get a real slot ID
SLOT_ID=$(curl -s -X POST http://localhost:7002/v1/slots/search \
  -H "Content-Type: application/json" \
  -d '{"tenantId":"downtown_medical","date":"tomorrow","timePreference":"morning"}' | \
  jq -r '.slots[0].slot_id')

echo "Using slot ID: $SLOT_ID"

# Create test event for confirm-appointment
cat > /tmp/confirm-appointment-event.json <<EOF
{
  "actionGroup": "AppointmentActions",
  "apiPath": "/confirmAppointment",
  "httpMethod": "POST",
  "requestBody": {
    "content": {
      "application/json": {
        "properties": [
          {"name": "tenant_id", "value": "downtown_medical"},
          {"name": "slot_id", "value": "$SLOT_ID"},
          {"name": "patient_name", "value": "Test Patient"},
          {"name": "patient_email", "value": "test@example.com"}
        ]
      }
    }
  },
  "sessionAttributes": {},
  "promptSessionAttributes": {}
}
EOF

# Run Lambda function locally
cd lambda/confirm-appointment
export APPOINTMENT_SERVICE_URL="http://localhost:7002"

echo "Running confirm-appointment handler..."
python3 -c "
import json
import index

with open('/tmp/confirm-appointment-event.json', 'r') as f:
    event = json.load(f)

result = index.handler(event, None)
print(json.dumps(result, indent=2))

# Validate response
response = result.get('response', {})
status_code = response.get('httpStatusCode', 0)
body_str = response.get('responseBody', {}).get('application/json', {}).get('body', '{}')
body = json.loads(body_str)

if status_code == 200 and body.get('status') == 'BOOKED':
    print(f'\n✅ confirm-appointment Lambda test PASSED')
    print(f'   Confirmation: {body.get(\"confirmation_ref\")}')
else:
    print(f'\n❌ confirm-appointment Lambda test FAILED')
    print(f'   Status: {body.get(\"status\")}, Error: {body.get(\"error\")}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ confirm-appointment Lambda works with Go services${NC}"
else
    echo -e "${RED}❌ confirm-appointment Lambda test failed${NC}"
    exit 1
fi

cd ../..
echo ""

# Summary
echo "📊 Test Summary"
echo "==============="
echo -e "${GREEN}✅ All Lambda functions work correctly with Go backend services${NC}"
echo ""
echo "🎯 Phase 3 Status:"
echo "   ✅ Lambda functions can call Go services"
echo "   ✅ Real appointment data is being used"
echo "   ✅ End-to-end integration validated locally"
echo ""
echo "Next steps:"
echo "   1. Deploy Go services to AWS (ECS, Lambda, or EC2)"
echo "   2. Update Lambda environment variables with deployed URLs"
echo "   3. Test with Bedrock Agent in AWS"

# Cleanup
rm -f /tmp/search-slots-event.json /tmp/confirm-appointment-event.json