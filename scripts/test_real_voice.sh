#!/bin/bash
set -e

echo "🎯 Starting Real Voice Test with Browser TTS"
echo "============================================="

# Check if services are running
echo "🔧 Checking services..."
if ! curl -s http://localhost:8080/health > /dev/null; then
    echo "❌ Media Gateway not running. Starting services..."
    docker compose up -d
    sleep 10
fi

echo "✅ Services are running"

# Open the voice client
echo ""
echo "🌐 Opening Real Voice Test Client..."

if command -v xdg-open > /dev/null; then
    xdg-open "file://$(pwd)/voice_test_client.html"
elif command -v open > /dev/null; then
    open "file://$(pwd)/voice_test_client.html"
else
    echo "Please open this file in your browser:"
    echo "file://$(pwd)/voice_test_client.html"
fi

echo ""
echo "🎯 Real Voice Test Ready!"
echo "========================"
echo ""
echo "📋 Instructions:"
echo "1. Select a clinic (1001, 1002, or 1003)"
echo "2. Allow microphone access when prompted"
echo "3. Click 'Start Talking' and speak your request"
echo "4. 🔊 The AI will respond with REAL VOICE using browser TTS!"
echo ""
echo "🎤 Voice Flow:"
echo "   Your Voice → WebSocket → Media Gateway → AI Processing → Browser TTS → Your Speakers"
echo ""
echo "💡 Try saying:"
echo "   - 'I need an appointment tomorrow morning'"
echo "   - 'What times are available?'"
echo "   - 'Book me for 9:30 AM'"
echo ""
echo "🔊 Voice Features:"
echo "   - Different voices for each clinic"
echo "   - Real-time speech synthesis"
echo "   - Barge-in protection (stops AI when you speak)"
echo ""