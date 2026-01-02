#!/bin/bash

# STEP NEXT-UI-02: Environment Setup Script
# This script starts both API and Web UI servers

echo "🚀 STEP NEXT-UI-02: Starting Insurance Comparison UI Environment"
echo ""

# Check if API is already running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ API Server is already running at http://localhost:8000"
else
    echo "Starting API Server..."
    cd /Users/cheollee/inca-rag-scope
    python3 -m apps.api.server > /tmp/api-server.log 2>&1 &
    API_PID=$!
    echo "  → API Server PID: $API_PID"
    echo "  → Logs: /tmp/api-server.log"

    # Wait for API to be ready
    echo "  → Waiting for API to start..."
    for i in {1..10}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "  ✓ API Server is ready!"
            break
        fi
        sleep 1
    done
fi

echo ""

# Check if Web UI is already running
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✓ Web UI is already running at http://localhost:3000"
else
    echo "Starting Web UI..."
    cd /Users/cheollee/inca-rag-scope/apps/web
    npm run dev > /tmp/web-ui.log 2>&1 &
    WEB_PID=$!
    echo "  → Web UI PID: $WEB_PID"
    echo "  → Logs: /tmp/web-ui.log"

    # Wait for Web UI to be ready
    echo "  → Waiting for Web UI to start..."
    for i in {1..20}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo "  ✓ Web UI is ready!"
            break
        fi
        sleep 1
    done
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Environment is ready!"
echo ""
echo "📍 API Server:  http://localhost:8000"
echo "📍 Web UI:      http://localhost:3000"
echo ""
echo "📚 Documentation: docs/STEP_NEXT_UI_02_LOCAL.md"
echo ""
echo "To stop servers:"
echo "  pkill -f 'apps.api.server'"
echo "  pkill -f 'next dev'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
