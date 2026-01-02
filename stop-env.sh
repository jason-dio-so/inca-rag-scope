#!/bin/bash

# STEP NEXT-UI-02: Environment Stop Script
# This script stops both API and Web UI servers

echo "🛑 Stopping Insurance Comparison UI Environment"
echo ""

# Stop API Server
echo "Stopping API Server..."
pkill -f 'apps.api.server' && echo "  ✓ API Server stopped" || echo "  ℹ API Server was not running"

# Stop Web UI
echo "Stopping Web UI..."
pkill -f 'next dev' && echo "  ✓ Web UI stopped" || echo "  ℹ Web UI was not running"

echo ""
echo "✅ Environment stopped"
