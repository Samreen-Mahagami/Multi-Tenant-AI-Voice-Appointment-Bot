#!/bin/bash

echo "🎯 Installing Alternative SIP Clients for Voice Testing"
echo "======================================================"

echo ""
echo "📞 Installing multiple SIP client options..."

# Install Twinkle (Qt-based SIP client)
echo "1. Installing Twinkle..."
sudo apt update
sudo apt install -y twinkle

# Install Ekiga (GNOME SIP client)
echo ""
echo "2. Installing Ekiga..."
sudo apt install -y ekiga

# Install Jami (modern SIP client)
echo ""
echo "3. Installing Jami..."
sudo apt install -y jami

# Install command line SIP tools
echo ""
echo "4. Installing SIP command line tools..."
sudo apt install -y sip-tester sipgrep

echo ""
echo "✅ Alternative SIP clients installed!"

echo ""
echo "🎯 Available Voice Testing Options:"
echo ""
echo "1. Twinkle (Recommended for Ubuntu):"
echo "   Command: twinkle"
echo "   - Modern Qt interface"
echo "   - Good audio quality"
echo ""
echo "2. Ekiga:"
echo "   Command: ekiga"
echo "   - GNOME integration"
echo "   - Video calling support"
echo ""
echo "3. Jami:"
echo "   Command: jami"
echo "   - Modern interface"
echo "   - Secure communications"
echo ""
echo "4. Linphone:"
echo "   Command: linphone"
echo "   - Cross-platform"
echo "   - Professional features"

echo ""
echo "🔧 SIP Account Configuration (same for all):"
echo "   Username: 1000"
echo "   Password: 1234"
echo "   Server/Domain: localhost"
echo "   Port: 5060"
echo "   Transport: UDP"

echo ""
echo "📞 Test Extensions:"
echo "   1001 → Downtown Medical Center"
echo "   1002 → Westside Family Practice"
echo "   1003 → Pediatric Care Clinic"

echo ""
echo "🚀 Choose your preferred client:"
echo "   twinkle    (recommended)"
echo "   ekiga"
echo "   jami"
echo "   linphone"