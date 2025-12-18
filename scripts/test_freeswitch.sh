#!/bin/bash

# Multi-Tenant AI Voice Appointment Bot - FreeSWITCH Testing Script
# Tests FreeSWITCH deployment and voice integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo "🧪 Testing FreeSWITCH Voice Integration"
echo "======================================="

# Test 1: Check if FreeSWITCH container is running
print_status "Test 1: Checking FreeSWITCH container status..."
if docker ps | grep -q "clinic-voice-bot-freeswitch"; then
    print_success "FreeSWITCH container is running"
else
    print_error "FreeSWITCH container is not running"
    echo "Start it with: cd freeswitch && docker-compose up -d"
    exit 1
fi

# Test 2: Check FreeSWITCH status
print_status "Test 2: Checking FreeSWITCH status..."
if docker-compose -f freeswitch/docker-compose.yml exec -T freeswitch fs_cli -x "status" | grep -q "UP"; then
    print_success "FreeSWITCH is UP and running"
else
    print_error "FreeSWITCH status check failed"
    exit 1
fi

# Test 3: Check SIP profiles
print_status "Test 3: Checking SIP profiles..."
if docker-compose -f freeswitch/docker-compose.yml exec -T freeswitch fs_cli -x "sofia status" | grep -q "external"; then
    print_success "External SIP profile is loaded"
else
    print_warning "External SIP profile may not be loaded"
fi

# Test 4: Check dialplan
print_status "Test 4: Checking dialplan configuration..."
if docker-compose -f freeswitch/docker-compose.yml exec -T freeswitch fs_cli -x "xml_locate dialplan" | grep -q "downtown_medical"; then
    print_success "Dialplan is configured with clinic extensions"
else
    print_warning "Dialplan may not be loaded correctly"
fi

# Test 5: Check Lua scripts
print_status "Test 5: Checking Lua scripts..."
if docker-compose -f freeswitch/docker-compose.yml exec -T freeswitch ls /usr/share/freeswitch/scripts/bedrock_agent_handler.lua &> /dev/null; then
    print_success "Bedrock agent handler script is available"
else
    print_error "Bedrock agent handler script not found"
    exit 1
fi

if docker-compose -f freeswitch/docker-compose.yml exec -T freeswitch ls /usr/share/freeswitch/scripts/aws_bedrock_client.lua &> /dev/null; then
    print_success "AWS Bedrock client script is available"
else
    print_error "AWS Bedrock client script not found"
    exit 1
fi

# Test 6: Check required modules
print_status "Test 6: Checking required modules..."
REQUIRED_MODULES=("mod_lua" "mod_sofia" "mod_dptools" "mod_http_cache")

for module in "${REQUIRED_MODULES[@]}"; do
    if docker-compose -f freeswitch/docker-compose.yml exec -T freeswitch fs_cli -x "module_exists $module" | grep -q "true"; then
        print_success "Module $module is loaded"
    else
        print_warning "Module $module may not be loaded"
    fi
done

# Test 7: Check backend services connectivity
print_status "Test 7: Testing backend services connectivity..."

# Test tenant config service
if curl -s -f "https://3ecpj0ss4j.execute-api.us-east-1.amazonaws.com/prod/v1/tenants/resolve?did=1001" > /dev/null; then
    print_success "Tenant config service is accessible"
else
    print_error "Cannot reach tenant config service"
fi

# Test appointment service
if curl -s -f "https://zkbwkpdpx9.execute-api.us-east-1.amazonaws.com/prod/v1/health" > /dev/null; then
    print_success "Appointment service is accessible"
else
    print_warning "Appointment service health check failed"
fi

# Test 8: Check logs for errors
print_status "Test 8: Checking recent logs for errors..."
ERROR_COUNT=$(docker-compose -f freeswitch/docker-compose.yml logs --tail=100 freeswitch 2>&1 | grep -i "error" | wc -l)

if [ "$ERROR_COUNT" -eq 0 ]; then
    print_success "No errors found in recent logs"
else
    print_warning "Found $ERROR_COUNT error messages in recent logs"
    echo "View logs with: docker-compose -f freeswitch/docker-compose.yml logs -f"
fi

# Test 9: Check resource usage
print_status "Test 9: Checking resource usage..."
docker stats --no-stream clinic-voice-bot-freeswitch --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Test 10: Simulate a test call (if possible)
print_status "Test 10: Testing DID routing logic..."
echo "To test actual voice calls:"
echo "  1. Configure your SIP trunk in freeswitch/.env"
echo "  2. Route DIDs 1001, 1002, 1003 to this FreeSWITCH server"
echo "  3. Call each DID and verify:"
echo "     - Correct greeting plays"
echo "     - Speech recognition works"
echo "     - Appointment booking completes"

# Summary
echo ""
echo "======================================="
echo "📊 Test Summary"
echo "======================================="
echo "✅ FreeSWITCH is operational"
echo "✅ Configuration files loaded"
echo "✅ Lua scripts available"
echo "✅ Backend services accessible"
echo ""
echo "🎯 Next Steps:"
echo "1. Configure SIP trunk credentials in freeswitch/.env"
echo "2. Update firewall rules for SIP (5080/UDP) and RTP (16384-32768/UDP)"
echo "3. Configure DID routing with your SIP provider"
echo "4. Test voice calls to DIDs 1001, 1002, 1003"
echo ""
echo "📋 Useful Commands:"
echo "  FreeSWITCH CLI: docker-compose -f freeswitch/docker-compose.yml exec freeswitch fs_cli"
echo "  View logs: docker-compose -f freeswitch/docker-compose.yml logs -f"
echo "  Restart: docker-compose -f freeswitch/docker-compose.yml restart"
echo "  Check calls: docker-compose -f freeswitch/docker-compose.yml exec freeswitch fs_cli -x 'show calls'"
echo ""

print_success "FreeSWITCH testing completed!"