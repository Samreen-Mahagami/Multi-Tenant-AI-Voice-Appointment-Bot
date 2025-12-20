#!/bin/bash

echo "🎯 Installing SIP Clients for Voice Testing"
echo "==========================================="

echo ""
echo "Available options:"
echo "1. Linphone (already installed ✅)"
echo "2. Twinkle"
echo "3. Ekiga"
echo "4. Jami"

echo ""
read -p "Which would you like to install? (2-4, or press Enter to use Linphone): " choice

case $choice in
    2)
        echo "Installing Twinkle..."
        sudo apt update && sudo apt install -y twinkle
        echo "✅ Twinkle installed! Run: twinkle"
        ;;
    3)
        echo "Installing Ekiga..."
        sudo apt update && sudo apt install -y ekiga
        echo "✅ Ekiga installed! Run: ekiga"
        ;;
    4)
        echo "Installing Jami..."
        sudo apt update && sudo apt install -y jami
        echo "✅ Jami installed! Run: jami"
        ;;
    *)
        echo "Using Linphone (already installed)"
        ./scripts/setup_linphone.sh
        ;;
esac

echo ""
echo "🔧 SIP Account Configuration for any client:"
echo "   Username: 1000"
echo "   Password: 1234"
echo "   Server/Domain: localhost"
echo "   Port: 5060"
echo "   Transport: UDP"
echo ""
echo "📞 Test by calling: 1001, 1002, or 1003"