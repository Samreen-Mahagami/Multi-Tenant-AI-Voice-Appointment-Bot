#!/bin/bash

echo "🎯 Setting Up Real Voice Testing on Ubuntu"
echo "=========================================="

echo ""
echo "📞 Installing SIP clients for voice testing..."

# Update package list
sudo apt update

echo ""
echo "1. Installing Linphone (GUI SIP client)..."
sudo apt install -y linphone

echo ""
echo "2. Installing SIP command line tools..."
sudo apt install -y sipgrep sip-tester

echo ""
echo "3. Installing audio tools..."
sudo apt install -y pulseaudio pavucontrol alsa-utils

echo ""
echo "4. Installing Twinkle (alternative SIP client)..."
sudo apt install -y twinkle

echo ""
echo "✅ SIP clients installed successfully!"

echo ""
echo "🔧 Available SIP Clients:"
echo "   1. Linphone (GUI) - Run: linphone"
echo "   2. Twinkle (GUI) - Run: twinkle"

echo ""
echo "📞 SIP Account Configuration:"
echo "   Username: 1000"
echo "   Password: 1234"
echo "   Domain: localhost"
echo "   Proxy: sip:localhost:5060"
echo "   Transport: UDP"

echo ""
echo "🎯 Test Extensions:"
echo "   1001 → Downtown Medical Center (Joanna voice)"
echo "   1002 → Westside Family Practice (Matthew voice)"
echo "   1003 → Pediatric Care Clinic (Salli voice)"

echo ""
echo "🚀 Starting Linphone for you..."
linphone &

echo ""
echo "✅ Voice testing setup complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Configure Linphone with the SIP account above"
echo "2. Call extension 1001, 1002, or 1003"
echo "3. You'll hear the AI greeting and can speak back"
echo "4. The system will process your voice and respond"