#!/bin/bash

echo "🎯 Voice Call Testing Script"
echo "============================"

# Check if required tools are installed
if ! command -v linphone &> /dev/null; then
    echo "📦 Installing Linphone..."
    sudo apt update && sudo apt install -y linphone
fi

echo ""
echo "📞 Starting voice call test..."

# Check if FreeSWITCH is running
if ! docker ps | grep -q freeswitch; then
    echo "🚀 Starting FreeSWITCH services..."
    docker compose up -d
    sleep 10
fi

echo ""
echo "✅ Services Status:"
docker compose ps

echo ""
echo "🎤 Voice Testing Options:"
echo ""
echo "Option 1: GUI Linphone"
echo "   1. Run: linphone"
echo "   2. Add SIP account:"
echo "      - Username: 1000"
echo "      - Password: 1234"
echo "      - Domain: localhost"
echo "   3. Call: 1001, 1002, or 1003"

echo ""
echo "Option 2: Command Line (Advanced)"
echo "   Using SIP command line tools..."

# Create a simple SIP test
echo ""
echo "🔧 Testing SIP connectivity..."

# Test if SIP port is open
if nc -z localhost 5060; then
    echo "✅ SIP port 5060 is open"
else
    echo "❌ SIP port 5060 is not accessible"
fi

echo ""
echo "📋 Real Voice Test Instructions:"
echo ""
echo "1. Open Linphone: linphone"
echo "2. Go to Settings → Manage SIP Accounts"
echo "3. Add account with:"
echo "   - Username: 1000"
echo "   - Password: 1234"
echo "   - Domain: localhost"
echo "   - Proxy: sip:localhost:5060"
echo ""
echo "4. Once registered, dial:"
echo "   - 1001 for Downtown Medical (you'll hear Joanna's voice)"
echo "   - 1002 for Westside Family (you'll hear Matthew's voice)"
echo "   - 1003 for Pediatric Care (you'll hear Salli's voice)"
echo ""
echo "5. Speak into your microphone - the AI will respond!"

echo ""
echo "🎯 What You'll Experience:"
echo "   📞 Call connects"
echo "   🔊 You hear clinic greeting"
echo "   🎤 You speak (e.g., 'I want an appointment')"
echo "   🤖 AI processes your speech"
echo "   🔊 AI responds with voice"
echo "   💬 Natural conversation continues"

echo ""
echo "🚀 Starting Linphone now..."
linphone &

echo ""
echo "✅ Voice testing ready! Configure Linphone and start calling!"