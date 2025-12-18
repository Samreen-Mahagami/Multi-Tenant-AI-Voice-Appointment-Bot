#!/bin/bash
set -e

echo "🧪 Testing Backend Services..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test HTTP endpoint
test_endpoint() {
    local url=$1
    local description=$2
    local expected_status=${3:-200}
    
    echo -n "Testing $description... "
    
    response=$(curl -s -w "%{http_code}" -o /tmp/response.json "$url")
    status_code="${response: -3}"
    
    if [ "$status_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $status_code)"
        if [ -f /tmp/response.json ]; then
            echo "   Response: $(cat /tmp/response.json | jq -c . 2>/dev/null || cat /tmp/response.json)"
        fi
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $status_code, expected $expected_status)"
        if [ -f /tmp/response.json ]; then
            echo "   Response: $(cat /tmp/response.json)"
        fi
        return 1
    fi
}

# Function to test POST endpoint
test_post_endpoint() {
    local url=$1
    local data=$2
    local description=$3
    local expected_status=${4:-200}
    
    echo -n "Testing $description... "
    
    response=$(curl -s -w "%{http_code}" -o /tmp/response.json \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$data" \
        "$url")
    status_code="${response: -3}"
    
    if [ "$status_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $status_code)"
        if [ -f /tmp/response.json ]; then
            echo "   Response: $(cat /tmp/response.json | jq -c . 2>/dev/null || cat /tmp/response.json)"
        fi
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $status_code, expected $expected_status)"
        if [ -f /tmp/response.json ]; then
            echo "   Response: $(cat /tmp/response.json)"
        fi
        return 1
    fi
}

echo ""
echo "📋 Testing Tenant Configuration Service"
echo "========================================"

# Test tenant config service health
test_endpoint "http://localhost:7001/v1/health" "Health check"

# Test list tenants
test_endpoint "http://localhost:7001/v1/tenants" "List all tenants"

# Test get specific tenant
test_endpoint "http://localhost:7001/v1/tenants/downtown_medical" "Get Downtown Medical tenant"

# Test DID resolution
test_endpoint "http://localhost:7001/v1/tenants/resolve?did=1001" "Resolve DID 1001"
test_endpoint "http://localhost:7001/v1/tenants/resolve?did=1002" "Resolve DID 1002"
test_endpoint "http://localhost:7001/v1/tenants/resolve?did=1003" "Resolve DID 1003"

# Test invalid DID
test_endpoint "http://localhost:7001/v1/tenants/resolve?did=9999" "Resolve invalid DID" 404

echo ""
echo "📅 Testing Appointment Service"
echo "=============================="

# Test appointment service health
test_endpoint "http://localhost:7002/v1/health" "Health check"

# Test search slots for different tenants
echo ""
echo "🔍 Testing slot searches..."

test_post_endpoint "http://localhost:7002/v1/slots/search" \
    '{"tenantId":"downtown_medical","date":"tomorrow","timePreference":"morning"}' \
    "Search Downtown Medical morning slots"

test_post_endpoint "http://localhost:7002/v1/slots/search" \
    '{"tenantId":"westside_family","date":"tomorrow","timePreference":"afternoon"}' \
    "Search Westside Family afternoon slots"

test_post_endpoint "http://localhost:7002/v1/slots/search" \
    '{"tenantId":"pediatric_care","date":"tomorrow","timePreference":"any"}' \
    "Search Pediatric Care any time slots"

# Test appointment booking
echo ""
echo "📝 Testing appointment booking..."

# First, get a slot to book
echo "Getting available slot for booking test..."
curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"tenantId":"downtown_medical","date":"tomorrow","timePreference":"morning"}' \
    "http://localhost:7002/v1/slots/search" > /tmp/slots.json

# Extract first slot ID
SLOT_ID=$(cat /tmp/slots.json | jq -r '.slots[0].slot_id' 2>/dev/null || echo "")

if [ -n "$SLOT_ID" ] && [ "$SLOT_ID" != "null" ]; then
    echo "Found slot ID: $SLOT_ID"
    
    test_post_endpoint "http://localhost:7002/v1/appointments/confirm" \
        "{\"tenantId\":\"downtown_medical\",\"slotId\":\"$SLOT_ID\",\"patientName\":\"John Smith\",\"patientEmail\":\"john.smith@example.com\"}" \
        "Book appointment for John Smith"
    
    # Try to book the same slot again (should fail)
    test_post_endpoint "http://localhost:7002/v1/appointments/confirm" \
        "{\"tenantId\":\"downtown_medical\",\"slotId\":\"$SLOT_ID\",\"patientName\":\"Jane Doe\",\"patientEmail\":\"jane.doe@example.com\"}" \
        "Try to book same slot again (should fail)" 400
else
    echo -e "${YELLOW}⚠️  No slots available for booking test${NC}"
fi

# Test invalid booking requests
echo ""
echo "🚫 Testing invalid booking requests..."

test_post_endpoint "http://localhost:7002/v1/appointments/confirm" \
    '{"tenantId":"downtown_medical","slotId":"invalid-slot","patientName":"John Smith","patientEmail":"john@example.com"}' \
    "Book invalid slot (should fail)" 400

test_post_endpoint "http://localhost:7002/v1/appointments/confirm" \
    '{"tenantId":"downtown_medical","slotId":"","patientName":"","patientEmail":""}' \
    "Book with missing data (should fail)" 400

echo ""
echo "🎯 Integration Tests"
echo "==================="

# Test cross-service integration
echo "Testing DID resolution + appointment search integration..."

# Get tenant by DID
curl -s "http://localhost:7001/v1/tenants/resolve?did=1002" > /tmp/tenant.json
TENANT_ID=$(cat /tmp/tenant.json | jq -r '.name' 2>/dev/null || echo "")

if [ -n "$TENANT_ID" ] && [ "$TENANT_ID" != "null" ]; then
    echo "Resolved DID 1002 to tenant: $TENANT_ID"
    
    test_post_endpoint "http://localhost:7002/v1/slots/search" \
        "{\"tenantId\":\"$TENANT_ID\",\"date\":\"tomorrow\",\"timePreference\":\"any\"}" \
        "Search slots for resolved tenant"
else
    echo -e "${RED}❌ Failed to resolve tenant from DID${NC}"
fi

echo ""
echo "📊 Test Summary"
echo "==============="

# Check if services are running
TENANT_HEALTH=$(curl -s http://localhost:7001/v1/health | jq -r '.status' 2>/dev/null || echo "error")
APPOINTMENT_HEALTH=$(curl -s http://localhost:7002/v1/health | jq -r '.status' 2>/dev/null || echo "error")

echo "Tenant Config Service: $TENANT_HEALTH"
echo "Appointment Service: $APPOINTMENT_HEALTH"

if [ "$TENANT_HEALTH" = "healthy" ] && [ "$APPOINTMENT_HEALTH" = "healthy" ]; then
    echo -e "${GREEN}✅ All backend services are operational!${NC}"
    echo ""
    echo "🎯 Next steps:"
    echo "   1. Update Lambda functions to call these services"
    echo "   2. Redeploy Lambda functions"
    echo "   3. Test end-to-end with Bedrock Agent"
else
    echo -e "${RED}❌ Some services are not healthy${NC}"
    exit 1
fi

# Cleanup
rm -f /tmp/response.json /tmp/slots.json /tmp/tenant.json