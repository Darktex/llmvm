# HomeAssistant Integration Examples

This directory contains example configuration files for integrating LLMVM with HomeAssistant.

## Files

### Configuration Files

- **`llmvm-config.yaml`** - Example LLMVM configuration with all recommended tools
  - Copy to `~/.config/llmvm/config.yaml`
  - Update with your local LLM endpoint or cloud provider settings

- **`mcp-server-env`** - Environment variables for HomeAssistant MCP Server
  - Copy to your `homeassistant-mcp/.env`
  - Update with your HomeAssistant URL and long-lived access token

### Systemd Service Files

- **`systemd-llmvm.service`** - Systemd service for LLMVM server
  - Install to `/etc/systemd/system/llmvm.service`
  - Update `User`, `Group`, and paths for your system
  - Enable with: `sudo systemctl enable llmvm && sudo systemctl start llmvm`

- **`systemd-mcp-server.service`** - Systemd service for HomeAssistant MCP Server
  - Install to `/etc/systemd/system/ha-mcp-server.service`
  - Update `User`, `Group`, and paths for your system
  - Enable with: `sudo systemctl enable ha-mcp-server && sudo systemctl start ha-mcp-server`

### Docker Deployment

- **`docker-compose.yml`** - Complete Docker Compose setup
  - Includes LLMVM, MCP server, local LLM (vLLM), and HomeAssistant
  - Update model names and paths for your setup
  - Run with: `docker-compose up -d`

### Helper Scripts

- **`startup-script.sh`** - Interactive startup script for development
  - Starts both MCP server and LLMVM server
  - Validates configuration and connectivity
  - Shows logs and status
  - Usage: `./startup-script.sh`

## Quick Start

### Development/Testing

The easiest way to get started for testing:

```bash
# 1. Start the services
./startup-script.sh

# 2. Check logs
tail -f ~/.local/share/llmvm/logs/server.log

# 3. Test LLMVM
curl http://localhost:8011/health
```

### Production Deployment

For production, use systemd services:

```bash
# 1. Install LLMVM service
sudo cp systemd-llmvm.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable llmvm
sudo systemctl start llmvm

# 2. Install MCP server service
sudo cp systemd-mcp-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ha-mcp-server
sudo systemctl start ha-mcp-server

# 3. Check status
sudo systemctl status llmvm
sudo systemctl status ha-mcp-server
```

### Docker Deployment

For containerized deployment:

```bash
# 1. Create .env file with your HA token
echo "HA_TOKEN=your_long_lived_token" > .env

# 2. Update docker-compose.yml with your settings

# 3. Start all services
docker-compose up -d

# 4. Check logs
docker-compose logs -f
```

## Configuration Notes

### Local LLM Setup

If you're using a local LLM on your DGX Spark, update the `openai_api_base` in `llmvm-config.yaml`:

```yaml
executor: 'openai'
openai_api_base: 'http://your-dgx-spark-hostname:8000/v1'
default_openai_model: 'your-model-name'
```

Common local LLM servers that provide OpenAI-compatible APIs:
- **vLLM**: Fast inference with continuous batching
- **Text Generation Inference (TGI)**: Hugging Face's server
- **Ollama**: Easy local deployment
- **LocalAI**: OpenAI-compatible local server
- **LM Studio**: Desktop app with API server

### HomeAssistant MCP Server

The MCP server needs:
1. Your HomeAssistant URL (usually `http://localhost:8123`)
2. A long-lived access token (create in HomeAssistant profile)

The server provides 60 tools for:
- Entity state queries
- Service calls (turn on/off, set values, etc.)
- Area and device management
- Automation and scene management
- Historical data queries
- And much more!

### LLMVM Tools

The example config includes all recommended tools:
- **Weather**: Get weather forecasts
- **Market Data**: Stock prices, options, volatility
- **Web Browsing**: Full browser automation with Playwright
- **Search**: Google, Yelp, HackerNews, Bluesky
- **Financial**: Currency rates, crypto prices, central bank rates
- **Visualization**: Generate graphs and charts
- **File Operations**: Search, replace, code analysis

All of these tools are available to the agent when answering HomeAssistant queries!

## Troubleshooting

See the main [HomeAssistant Integration Guide](../../docs/homeassistant-integration.md) for detailed troubleshooting.

### Quick Checks

```bash
# Check LLMVM is running
curl http://localhost:8011/health

# Check MCP server is running
lsof -i :8765

# Check LLMVM discovered MCP server
tail -n 100 ~/.local/share/llmvm/logs/server.log | grep "MCP"

# Check HomeAssistant is accessible
curl http://localhost:8123

# Test MCP server connection to HA
cd ~/homeassistant-mcp
python tests/test_connection.py
```

## More Information

- [Full Integration Guide](../../docs/homeassistant-integration.md)
- [Custom Component README](../../custom_components/llmvm_conversation/README.md)
- [LLMVM Main Documentation](../../README.md)
