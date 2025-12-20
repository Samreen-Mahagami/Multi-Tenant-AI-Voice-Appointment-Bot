#!/bin/bash

echo "🎯 Direct FreeSWITCH Testing"
echo "============================"

# Test FreeSWITCH CLI commands
echo "1. FreeSWITCH Status:"
docker exec freeswitch fs_cli -x "status"

echo ""
echo "2. Show Dialplan:"
docker exec freeswitch fs_cli -x "show dialplan"

echo ""
echo "3. Show Channels:"
docker exec freeswitch fs_cli -x "show channels"

echo ""
echo "4. Show Calls:"
docker exec freeswitch fs_cli -x "show calls"

echo ""
echo "5. Test Extension 1001 Routing:"
docker exec freeswitch fs_cli -x "xml_locate dialplan context public destination_number 1001"

echo ""
echo "6. SIP Profile Status:"
docker exec freeswitch fs_cli -x "sofia status"

echo ""
echo "7. Module Status:"
docker exec freeswitch fs_cli -x "show modules"

echo ""
echo "🎯 To simulate a call from FreeSWITCH CLI:"
echo "   docker exec -it freeswitch fs_cli"
echo "   Then run: originate user/1000 1001"