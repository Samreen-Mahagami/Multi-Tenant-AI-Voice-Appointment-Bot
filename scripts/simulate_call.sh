#!/bin/bash

echo "🎯 Simulating FreeSWITCH Calls (No Softphone Needed)"
echo "=================================================="

# Test 1: Simulate call to extension 1001
echo ""
echo "📞 Test 1: Calling Downtown Medical Center (1001)..."
echo "Expected: Should route to Media Gateway and show greeting"

# Use FreeSWITCH originate command to simulate call
docker exec freeswitch fs_cli -x "originate {origination_caller_id_number=1000}loopback/1001/public &echo()"

echo ""
echo "📞 Test 2: Calling Westside Family Practice (1002)..."
docker exec freeswitch fs_cli -x "originate {origination_caller_id_number=1000}loopback/1002/public &echo()"

echo ""
echo "📞 Test 3: Calling Pediatric Care Clinic (1003)..."
docker exec freeswitch fs_cli -x "originate {origination_caller_id_number=1000}loopback/1003/public &echo()"

echo ""
echo "✅ Call simulation completed!"
echo "Check the Media Gateway logs to see if calls were processed:"
echo "   docker logs media-gateway-go --tail 20"