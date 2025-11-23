#!/bin/bash
# Startup script for LLMVM + HomeAssistant MCP Server
# This is useful for development or manual startup

set -e

echo "🚀 Starting LLMVM + HomeAssistant Integration"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
LLMVM_PORT=8011
MCP_PORT=8765
HA_MCP_DIR="$HOME/homeassistant-mcp"

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${GREEN}✓${NC} Port $1 is in use"
        return 0
    else
        echo -e "${RED}✗${NC} Port $1 is not in use"
        return 1
    fi
}

# Step 1: Check if HomeAssistant is running
echo -e "\n${YELLOW}1. Checking HomeAssistant...${NC}"
if curl -sf http://localhost:8123 > /dev/null; then
    echo -e "${GREEN}✓${NC} HomeAssistant is running"
else
    echo -e "${RED}✗${NC} HomeAssistant is not running!"
    echo "   Please start HomeAssistant first"
    exit 1
fi

# Step 2: Start HomeAssistant MCP Server
echo -e "\n${YELLOW}2. Starting HomeAssistant MCP Server...${NC}"
if [ ! -d "$HA_MCP_DIR" ]; then
    echo -e "${RED}✗${NC} HomeAssistant MCP directory not found: $HA_MCP_DIR"
    echo "   Please clone it first:"
    echo "   git clone https://github.com/cronus42/homeassistant-mcp.git $HA_MCP_DIR"
    exit 1
fi

cd "$HA_MCP_DIR"

if [ ! -f ".env" ]; then
    echo -e "${RED}✗${NC} .env file not found in $HA_MCP_DIR"
    echo "   Please create it with your HomeAssistant URL and token"
    exit 1
fi

# Kill existing MCP server if running
pkill -f "homeassistant_mcp.server" || true
sleep 2

# Start MCP server in background
nohup python -m homeassistant_mcp.server --port $MCP_PORT > mcp_server.log 2>&1 &
MCP_PID=$!
echo -e "${GREEN}✓${NC} Started MCP server (PID: $MCP_PID)"

# Wait for MCP server to start
echo "   Waiting for MCP server to be ready..."
for i in {1..10}; do
    if check_port $MCP_PORT > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} MCP server is ready"
        break
    fi
    sleep 1
done

# Step 3: Start LLMVM Server
echo -e "\n${YELLOW}3. Starting LLMVM Server...${NC}"

# Check if llmvm-server is in PATH
if ! command -v llmvm-server &> /dev/null; then
    echo -e "${RED}✗${NC} llmvm-server not found in PATH"
    echo "   Please install LLMVM first"
    exit 1
fi

# Kill existing LLMVM server if running
pkill -f "llmvm.server" || true
sleep 2

# Start LLMVM server in background
cd "$HOME"
nohup llmvm-server > ~/.local/share/llmvm/logs/server.log 2>&1 &
LLMVM_PID=$!
echo -e "${GREEN}✓${NC} Started LLMVM server (PID: $LLMVM_PID)"

# Wait for LLMVM server to start
echo "   Waiting for LLMVM server to be ready..."
for i in {1..30}; do
    if curl -sf http://localhost:$LLMVM_PORT/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} LLMVM server is ready"
        break
    fi
    sleep 1
done

# Step 4: Verify MCP discovery
echo -e "\n${YELLOW}4. Verifying MCP server discovery...${NC}"
sleep 5  # Give LLMVM time to discover the MCP server

echo "   Checking LLMVM logs for MCP discovery..."
if tail -n 50 ~/.local/share/llmvm/logs/server.log | grep -q "Connected to MCP server"; then
    echo -e "${GREEN}✓${NC} LLMVM discovered the MCP server!"
else
    echo -e "${YELLOW}⚠${NC}  MCP server not yet discovered. This may take a few seconds."
    echo "   Check logs: tail -f ~/.local/share/llmvm/logs/server.log"
fi

# Summary
echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ All services started successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Service Status:"
echo "  • HomeAssistant:  http://localhost:8123"
echo "  • MCP Server:     http://localhost:$MCP_PORT (PID: $MCP_PID)"
echo "  • LLMVM Server:   http://localhost:$LLMVM_PORT (PID: $LLMVM_PID)"
echo ""
echo "Logs:"
echo "  • LLMVM:     tail -f ~/.local/share/llmvm/logs/server.log"
echo "  • MCP:       tail -f $HA_MCP_DIR/mcp_server.log"
echo ""
echo "To stop services:"
echo "  kill $LLMVM_PID $MCP_PID"
echo ""
echo -e "${YELLOW}Next step:${NC} Configure the LLMVM Conversation Agent in HomeAssistant"
echo "  Settings → Devices & Services → Add Integration → LLMVM Conversation Agent"
