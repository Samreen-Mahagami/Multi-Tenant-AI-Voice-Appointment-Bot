#!/bin/bash

echo "🎯 Testing SIP Call to FreeSWITCH"
echo "================================="

# Check if FreeSWITCH is running
echo "1. Checking FreeSWITCH status..."
if docker exec freeswitch fs_cli -x "status" > /dev/null 2>&1; then
    echo "✅ FreeSWITCH is running"
else
    echo "❌ FreeSWITCH is not running. Start with: docker compose up -d"
    exit 1
fi

# Show registered users
echo ""
echo "2. Checking registered SIP users..."
docker exec freeswitch fs_cli -x "show registrations"

# Show dialplan
echo ""
echo "3. Available extensions:"
echo "   1001 → Downtown Medical Center"
echo "   1002 → Westside Family Practice"
echo "   1003 → Pediatric Care Clinic"

# Test internal call routing
echo ""
echo "4. Testing dialplan routing..."
docker exec freeswitch fs_cli -x "eval \${destination_number=1001}"

echo ""
echo "🎯 To test with softphone:"
echo "   Server: localhost:5060"
echo "   Username: 1000"
echo "   Password: 1234"
echo "   Then dial: 1001, 1002, or 1003"