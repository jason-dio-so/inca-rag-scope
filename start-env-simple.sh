#!/bin/bash

# STEP NEXT-UI-02: Simple Environment Start Script
# Starts API and Web UI in background

echo "🚀 Starting Insurance Comparison UI Environment"
echo ""

# Start API Server
echo "Starting API Server..."
cd /Users/cheollee/inca-rag-scope
uvicorn apps.api.server:app --host 0.0.0.0 --port 8000 > /tmp/api-server.log 2>&1 &
echo "  → API Server PID: $!"
sleep 2

# Start Web UI
echo "Starting Web UI..."
cd /Users/cheollee/inca-rag-scope/apps/web
npm run dev > /tmp/web-ui.log 2>&1 &
echo "  → Web UI PID: $!"
sleep 3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Environment Started!"
echo ""
echo "📍 API Server:  http://localhost:8000"
echo "   API Docs:    http://localhost:8000/docs"
echo ""
echo "📍 Web UI:      http://localhost:3000"
echo ""
echo "📚 Documentation: docs/STEP_NEXT_UI_02_LOCAL.md"
echo ""
echo "To view logs:"
echo "  tail -f /tmp/api-server.log"
echo "  tail -f /tmp/web-ui.log"
echo ""
echo "To stop:"
echo "  ./stop-env.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
