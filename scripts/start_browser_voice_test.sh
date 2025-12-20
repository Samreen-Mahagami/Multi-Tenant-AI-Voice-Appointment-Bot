#!/bin/bash
set -e

echo "🚀 Starting Browser Voice Test Environment"
echo "=========================================="

# Load environment variables
if [ -f .env ]; then
    source .env
    echo "✅ Environment variables loaded"
else
    echo "⚠️  No .env file found - using demo mode"
fi

# Start services
echo ""
echo "🔧 Starting backend services..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 15

# Check service health
echo ""
echo "🏥 Checking service health..."

echo "1. Tenant Config Service:"
if curl -s http://localhost:7001/v1/health > /dev/null; then
    echo "   ✅ Healthy"
else
    echo "   ❌ Not responding"
fi

echo "2. Appointment Service:"
if curl -s http://localhost:7002/v1/health > /dev/null; then
    echo "   ✅ Healthy"
else
    echo "   ❌ Not responding"
fi

echo "3. Media Gateway:"
if curl -s http://localhost:8080/health > /dev/null; then
    echo "   ✅ Healthy"
else
    echo "   ❌ Not responding"
fi

echo ""
echo "🌐 Opening Browser Voice Client..."

# Check if we're in a desktop environment
if command -v xdg-open > /dev/null; then
    xdg-open "file://$(pwd)/browser_voice_client.html"
elif command -v open > /dev/null; then
    open "file://$(pwd)/browser_voice_client.html"
else
    echo "Please open this file in your browser:"
    echo "file://$(pwd)/browser_voice_client.html"
fi

echo ""
echo "🎯 Browser Voice Test Ready!"
echo "============================"
echo ""
echo "📋 Instructions:"
echo "1. Open the browser client (should open automatically)"
echo "2. Select a clinic (1001, 1002, or 1003)"
echo "3. Allow microphone access when prompted"
echo "4. Click 'Start Talking' and speak your request"
echo "5. The AI will respond with voice!"
echo ""
echo "🎤 Voice Flow:"
echo "   Browser → WebSocket → Media Gateway → AWS Transcribe (sim) → Bedrock Agent (sim) → Polly (sim) → Browser"
echo ""
echo "💡 Tips:"
echo "   - Use Chrome or Firefox for best WebRTC support"
echo "   - Speak clearly and wait for the AI response"
echo "   - Try: 'I need an appointment tomorrow morning'"
echo ""
echo "🔧 Troubleshooting:"
echo "   - If microphone doesn't work, check browser permissions"
echo "   - If connection fails, ensure services are running: docker compose ps"
echo "   - Check logs: docker compose logs media-gateway-go"
echo ""