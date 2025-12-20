#!/bin/bash

echo "🎯 Setting up Linphone for FreeSWITCH Testing"
echo "============================================="

echo ""
echo "📞 Linphone is already installed!"
echo ""
echo "🔧 Configuration:"
echo "1. Open Linphone: linphone"
echo "2. Go to Settings/Preferences"
echo "3. Configure SIP Account:"
echo "   - Username: 1000"
echo "   - Password: 1234" 
echo "   - Domain: localhost"
echo "   - Proxy: sip:localhost:5060"
echo "   - Transport: UDP"
echo ""
echo "📞 Test Extensions:"
echo "   - 1001 → Downtown Medical Center"
echo "   - 1002 → Westside Family Practice"
echo "   - 1003 → Pediatric Care Clinic"
echo ""
echo "🚀 Starting Linphone now..."

# Start Linphone
linphone &

echo ""
echo "✅ Linphone started! Configure the account and start calling!"