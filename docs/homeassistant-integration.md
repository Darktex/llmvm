# HomeAssistant Integration Guide

This guide explains how to integrate LLMVM with HomeAssistant to create a powerful local AI conversation agent with full tool access.

## 🎯 Overview

The integration consists of three main components:

1. **LLMVM Server** - The agent server with tool execution capabilities
2. **HomeAssistant MCP Server** - Provides HomeAssistant control tools via Model Context Protocol
3. **LLMVM Conversation Agent** - HomeAssistant custom component that connects to LLMVM

## 🏗️ Architecture

```
HomeAssistant                          LLMVM Server
┌─────────────────────┐               ┌──────────────────────────┐
│                     │               │                          │
│ User: "Turn on      │───HTTP───────>│  Agent Loop              │
│  living room lights"│               │  ┌────────────────────┐  │
│                     │               │  │ 1. Call Local LLM  │  │
│ ┌─────────────────┐ │               │  │ 2. Generate code   │  │
│ │ LLMVM Conv Agent│ │<──Response────┤  │ 3. Execute tools   │  │
│ │ (Custom         │ │               │  └─────────┬──────────┘  │
│ │  Component)     │ │               │            │             │
│ └─────────────────┘ │               │  ┌─────────▼──────────┐  │
│                     │               │  │ MCP Tools:         │  │
└─────────────────────┘               │  │ - turn_on()        │  │
         │                            │  │ - get_state()      │  │
         │ REST API                   │  │ - call_service()   │  │
         │                            │  │ ... (60 tools)     │  │
         │                            │  └─────────┬──────────┘  │
         │                            └────────────┼─────────────┘
         │                                         │ MCP Protocol
         │                            ┌────────────▼────────────┐
         └────────────────────────────│ HA MCP Server           │
                                      │ (cronus42/ha-mcp)       │
                                      └─────────────────────────┘
```

## 📋 Prerequisites

- Python 3.11 or later
- HomeAssistant 2024.1 or later
- LLMVM server running (see main README)
- Local LLM with OpenAI-compatible API (optional, can use cloud models)

## 🚀 Installation

### Step 1: Install and Configure HomeAssistant MCP Server

We recommend using `cronus42/homeassistant-mcp` as it provides 60 comprehensive tools.

#### 1.1 Clone and install the MCP server:

```bash
cd ~/
git clone https://github.com/cronus42/homeassistant-mcp.git
cd homeassistant-mcp
./setup.sh
```

#### 1.2 Create a Long-Lived Access Token in HomeAssistant:

1. Open HomeAssistant web interface
2. Click on your profile (bottom left)
3. Scroll down to "Long-lived access tokens"
4. Click "Create Token"
5. Give it a name like "LLMVM MCP Server"
6. Copy the token (you won't see it again!)

#### 1.3 Configure the MCP server:

Create a `.env` file in the `homeassistant-mcp` directory:

```bash
cat > .env << EOF
HOME_ASSISTANT_URL=http://localhost:8123
HOME_ASSISTANT_TOKEN=your_long_lived_access_token_here
EOF
```

Replace `http://localhost:8123` with your HomeAssistant URL if different.

#### 1.4 Test the connection:

```bash
python tests/test_connection.py
```

You should see a successful connection message.

#### 1.5 Start the MCP server:

```bash
# Start in SSE mode (recommended for LLMVM auto-discovery)
python -m homeassistant_mcp.server --port 8765
```

Or run in the background:

```bash
nohup python -m homeassistant_mcp.server --port 8765 > mcp_server.log 2>&1 &
```

**Note**: LLMVM will automatically discover this MCP server when it's running!

### Step 2: Install LLMVM Conversation Agent in HomeAssistant

#### 2.1 Copy the custom component:

```bash
# From the LLMVM repository root
cp -r custom_components/llmvm_conversation /path/to/homeassistant/config/custom_components/
```

For example, if using Home Assistant OS:
```bash
cp -r custom_components/llmvm_conversation /usr/share/hassio/homeassistant/custom_components/
```

For Home Assistant Container:
```bash
cp -r custom_components/llmvm_conversation /config/custom_components/
```

#### 2.2 Restart HomeAssistant:

In HomeAssistant:
- Settings → System → Restart
- Wait for HomeAssistant to come back online

### Step 3: Configure the LLMVM Conversation Agent

#### 3.1 Add the integration:

1. In HomeAssistant, go to **Settings → Devices & Services**
2. Click **"+ Add Integration"**
3. Search for **"LLMVM Conversation Agent"**
4. Click to add it

#### 3.2 Configure the integration:

Fill in the configuration form:
- **LLMVM Server URL**: `http://localhost:8011` (or your LLMVM server address)
- **LLM Executor**: `openai` (or `anthropic`, `gemini`, etc.)
- **Model Name**: Leave empty to use executor default, or specify like `gpt-4`
- **Temperature**: `0.7` (0 = deterministic, 2 = very creative)
- **Max Tokens**: `4000` (maximum response length)

Click **Submit**. The integration will test the connection to your LLMVM server.

#### 3.3 Set as default conversation agent:

1. Go to **Settings → Voice Assistants**
2. Click on your assistant (or create one)
3. Under **Conversation agent**, select **"LLMVM Conversation Agent"**
4. Click **Save**

### Step 4: Verify Everything is Working

#### 4.1 Check LLMVM has discovered the MCP server:

In your LLMVM server logs, you should see:
```
INFO - Detected SSE MCP server on port 8765 (PID: xxxxx)
INFO - Connected to MCP server (sse) with 60 tools
INFO - Updated helpers with 60 MCP tools
```

#### 4.2 Test the conversation agent:

In HomeAssistant:
1. Go to **Settings → Voice Assistants → Assist**
2. Type: "What lights are in the living room?"
3. The agent should respond with information about your lights

Try more complex queries:
- "Turn on all living room lights to 50% brightness"
- "What's the temperature in the bedroom?"
- "Set the thermostat to 72 degrees"
- "What time is sunset today?" (uses LLMVM's weather tools!)
- "What's the current price of TSLA stock?" (uses LLMVM's market tools!)

## 🔧 Configuration

### LLMVM Server Configuration

Edit your `~/.config/llmvm/config.yaml`:

```yaml
# If using local LLM via OpenAI-compatible API
executor: 'openai'
openai_api_base: 'http://your-dgx-spark:8000/v1'  # Your local LLM endpoint
default_openai_model: 'your-model-name'

# Server settings
server_host: '0.0.0.0'
server_port: 8011

# Enable all the helpful tools
helper_functions:
  - llmvm.server.bcl.BCL.datetime
  - llmvm.server.bcl.BCL.get_weather
  - llmvm.server.tools.browser.Browser
  - llmvm.server.tools.search_tool.Search.google_search
  # ... etc (see config.yaml for full list)
```

### MCP Server Auto-Discovery Configuration

LLMVM automatically discovers MCP servers. To customize discovery, you can modify patterns in the server code, but the defaults should work for most cases.

The MCP monitor looks for:
- Processes with `fastmcp` in the command line
- Processes with `mcp_server.py` or `mcp-server.py`
- Processes with SSE endpoints (ports are auto-detected)

## 🎯 Use Cases

### Example 1: Smart Home Control

**User**: "Turn on the living room lights and set them to warm white at 60% brightness"

**What happens**:
1. HomeAssistant sends query to LLMVM
2. LLMVM's local LLM generates Python code
3. Code uses MCP tools: `turn_on_light(entity_id="light.living_room", brightness=153, color_temp=...)`
4. MCP server calls HomeAssistant REST API
5. Lights turn on as requested
6. Response sent back to user

### Example 2: Context-Aware Information

**User**: "What time is sunset today and turn on the porch light 30 minutes before that"

**What happens**:
1. LLMVM uses `BCL.get_weather()` to get sunset time
2. Calculates sunset - 30 minutes
3. Uses HomeAssistant MCP tools to create an automation
4. Responds with confirmation

### Example 3: Multi-Tool Query

**User**: "Check if TSLA stock is up today and if so, flash the office lights green"

**What happens**:
1. LLMVM uses `MarketHelpers.get_stock_price_history()` to check TSLA
2. Compares to previous day
3. If up, uses MCP tools to flash office lights with green color
4. Responds with stock info and action taken

## 🐛 Troubleshooting

### LLMVM can't discover the MCP server

**Check**:
1. Is the MCP server running? `ps aux | grep homeassistant_mcp`
2. Is it listening on a port? `lsof -i :8765`
3. Check LLMVM logs: `tail -f ~/.local/share/llmvm/logs/server.log`

**Solution**: Start the MCP server in SSE mode with explicit port:
```bash
python -m homeassistant_mcp.server --port 8765
```

### HomeAssistant can't connect to LLMVM

**Check**:
1. Is LLMVM server running? `curl http://localhost:8011/health`
2. Is the URL correct in the integration config?
3. Check network/firewall rules if on different machines

### Conversation agent responses are slow

**Causes**:
- Local LLM might be slow (check GPU utilization)
- MCP server might be slow to respond to HomeAssistant API calls
- Tool execution might be complex (browser automation, etc.)

**Solutions**:
- Use a faster local model
- Reduce `max_tokens` in configuration
- Increase timeout in `conversation.py` if needed

### MCP tools not working

**Check**:
1. Is the HomeAssistant token valid?
2. Can the MCP server reach HomeAssistant? `curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8123/api/`
3. Check MCP server logs: `tail -f ~/homeassistant-mcp/mcp_server.log`

## 🔒 Security Considerations

1. **Long-Lived Access Tokens**: Keep your HA token secure. Don't commit `.env` files to git.
2. **Network Exposure**: If exposing LLMVM server to network, use authentication/TLS.
3. **Local LLM**: Using a local LLM keeps all data on your infrastructure - no cloud calls.
4. **Rate Limiting**: Consider adding rate limiting if exposing to multiple users.

## 📚 Additional Resources

- [LLMVM Documentation](../README.md)
- [HomeAssistant MCP Server (cronus42)](https://github.com/cronus42/homeassistant-mcp)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [HomeAssistant Conversation API](https://www.home-assistant.io/integrations/conversation/)

## 🤝 Contributing

Found an issue or want to improve the integration? Please submit issues or PRs to the LLMVM repository!
