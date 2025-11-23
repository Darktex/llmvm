# LLMVM Conversation Agent for HomeAssistant

A HomeAssistant custom component that integrates the LLMVM agent framework as a conversation agent, enabling AI-powered control of your smart home with access to web browsing, market data, and other tools.

## Features

- 🤖 **Full Agent Capabilities**: Uses LLMVM's agent mode with tool execution
- 🔧 **60+ HomeAssistant Tools**: Auto-discovers MCP server tools for HA control
- 🌐 **Web Access**: Can browse the web, search, check stocks, weather, etc.
- 🏠 **Smart Home Control**: Natural language control of all HA entities
- 💬 **Context Awareness**: Maintains conversation history across messages
- 🔒 **Privacy First**: Works with local LLMs (no cloud required)
- ⚡ **Fast**: Direct HTTP communication, no middleware

## Installation

### Prerequisites

1. HomeAssistant 2024.1 or later
2. LLMVM server running and accessible
3. HomeAssistant MCP server running (see main documentation)

### Install via HACS (coming soon)

This integration will be submitted to HACS for easy installation.

### Manual Installation

1. Copy the `llmvm_conversation` folder to your `custom_components` directory:
   ```bash
   cp -r custom_components/llmvm_conversation /config/custom_components/
   ```

2. Restart HomeAssistant

3. Add the integration:
   - Go to Settings → Devices & Services
   - Click "+ Add Integration"
   - Search for "LLMVM Conversation Agent"
   - Configure with your LLMVM server URL

## Configuration

The integration is configured via the HomeAssistant UI.

### Configuration Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| LLMVM Server URL | Yes | `http://localhost:8011` | URL of your LLMVM server |
| LLM Executor | No | `openai` | Which LLM provider to use (openai, anthropic, gemini, etc.) |
| Model Name | No | (executor default) | Specific model to use |
| Temperature | No | `0.7` | Controls randomness (0-2) |
| Max Tokens | No | `4000` | Maximum response length |

## Usage

Once configured and set as your default conversation agent:

### Simple Commands
- "Turn on the living room lights"
- "Set bedroom temperature to 72 degrees"
- "What's the status of the front door?"

### Complex Queries
- "What time is sunset and turn on porch lights 30 minutes before"
- "If it's going to rain tomorrow, remind me to close the windows"
- "Show me the current price of Tesla stock"

### Multi-Tool Queries
- "Search for the best Italian restaurant nearby and add it to my shopping list notes"
- "What's the weather forecast and should I water the garden?"
- "Browse the news for tech headlines and summarize the top 3"

## How It Works

1. User asks a question via HomeAssistant Assist
2. Custom component sends query to LLMVM server's `/v1/tools/completions` endpoint
3. LLMVM's local LLM generates Python code to accomplish the task
4. Code executes using available tools:
   - MCP tools (60+ HomeAssistant control functions)
   - Built-in tools (weather, stocks, browser, search, etc.)
5. Results are returned to HomeAssistant
6. User sees the response

## Architecture

```
┌──────────────────────────────────────────────────┐
│ HomeAssistant                                    │
│                                                  │
│  User ──> LLMVM Conv Agent ──> LLMVM Server      │
│              (Custom Component)        │         │
│                                        │         │
└────────────────────────────────────────┼─────────┘
                                         │ HTTP
                      ┌──────────────────▼──────────────────┐
                      │ LLMVM Server                        │
                      │  - Receives query                   │
                      │  - Calls local LLM                  │
                      │  - Executes Python code with tools  │
                      │  - Returns response                 │
                      └──────────────────┬──────────────────┘
                                         │
                      ┌──────────────────▼──────────────────┐
                      │ MCP Tools (Auto-discovered)         │
                      │  - HomeAssistant control (60 tools) │
                      │  - Weather, stocks, browser, etc.   │
                      └─────────────────────────────────────┘
```

## Troubleshooting

### Cannot connect to LLMVM server

**Check**:
- Is LLMVM server running? `curl http://localhost:8011/health`
- Is the URL in configuration correct?
- Are there firewall rules blocking the connection?

### Responses are slow

**Causes**:
- Local LLM might be processing slowly
- Complex tool execution (especially browser automation)
- Network latency to LLMVM server

**Solutions**:
- Use a faster model
- Reduce `max_tokens` in configuration
- Ensure LLMVM server has adequate resources

### HomeAssistant tools don't work

**Check**:
- Is the HomeAssistant MCP server running?
- Has LLMVM discovered the MCP server? Check LLMVM logs
- Is the MCP server's HA token valid?

See the main [HomeAssistant Integration Guide](../../docs/homeassistant-integration.md) for detailed troubleshooting.

## Development

### File Structure

```
llmvm_conversation/
├── __init__.py          # Component setup
├── manifest.json        # Component metadata
├── const.py            # Constants
├── config_flow.py      # UI configuration flow
├── conversation.py     # Main conversation agent implementation
├── strings.json        # UI strings
└── translations/
    └── en.json         # English translations
```

### Testing Locally

1. Set up a development HomeAssistant instance
2. Copy the component to `config/custom_components/`
3. Enable debug logging in `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.llmvm_conversation: debug
   ```
4. Restart and check logs: `config/home-assistant.log`

## License

This component is part of the LLMVM project. See the main LICENSE file.

## Support

- Documentation: [HomeAssistant Integration Guide](../../docs/homeassistant-integration.md)
- Issues: [GitHub Issues](https://github.com/9600dev/llmvm/issues)
- LLMVM Main Repo: [https://github.com/9600dev/llmvm](https://github.com/9600dev/llmvm)
