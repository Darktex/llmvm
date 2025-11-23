# 🏠 HomeAssistant + LLMVM Quick Start Guide

Turn your HomeAssistant into an AI-powered smart home with full tool access!

## 🎯 What You Get

- 🤖 **Natural language control** of all HomeAssistant devices
- 🌐 **Web browsing** - Ask about weather, stocks, news
- 🔧 **60+ HomeAssistant tools** - Control entities, scenes, automations
- 💡 **Smart context** - "Turn on lights if stock is up" type queries
- 🔒 **Privacy first** - Works with local LLMs (optional)

## ⚡ Quick Start (3 Steps)

### 1️⃣ Install HomeAssistant MCP Server

```bash
# Clone the MCP server
cd ~/
git clone https://github.com/cronus42/homeassistant-mcp.git
cd homeassistant-mcp
./setup.sh

# Configure with your HA credentials
cat > .env << EOF
HOME_ASSISTANT_URL=http://localhost:8123
HOME_ASSISTANT_TOKEN=your_long_lived_token_here
EOF

# Test connection
python tests/test_connection.py

# Start the server
python -m homeassistant_mcp.server --port 8765
```

**Get your HA token**: Profile → Long-lived access tokens → Create Token

### 2️⃣ Install LLMVM Conversation Agent

```bash
# Copy custom component to HomeAssistant
cp -r custom_components/llmvm_conversation /path/to/homeassistant/config/custom_components/

# Restart HomeAssistant
# In HA: Settings → System → Restart
```

### 3️⃣ Configure in HomeAssistant

1. **Add Integration**:
   - Settings → Devices & Services → Add Integration
   - Search "LLMVM Conversation Agent"
   - Enter LLMVM server URL: `http://localhost:8011`

2. **Set as Default**:
   - Settings → Voice Assistants → Your Assistant
   - Conversation Agent → "LLMVM Conversation Agent"
   - Save

## 🧪 Test It!

Try these in HomeAssistant Assist:

### Simple Commands
```
"Turn on the living room lights"
"What's the temperature in the bedroom?"
"Set thermostat to 72 degrees"
```

### Smart Queries (using LLMVM tools!)
```
"What time is sunset and turn on porch lights 30 minutes before"
"Is TSLA stock up today?"
"Search for the best Italian restaurants nearby"
"What's the weather forecast for tomorrow?"
```

### Complex Multi-Tool Queries
```
"If it's going to rain tomorrow, close the garage door"
"Check Bitcoin price and if over 100k, flash the office lights green"
"Browse the news for tech headlines and summarize the top 3"
```

## 🎛️ Using a Local LLM

Update `~/.config/llmvm/config.yaml`:

```yaml
executor: 'openai'
openai_api_base: 'http://your-dgx-spark:8000/v1'  # Your local LLM
default_openai_model: 'your-model-name'
```

Compatible with: vLLM, TGI, Ollama, LocalAI, LM Studio

## 📚 Full Documentation

- [Complete Integration Guide](docs/homeassistant-integration.md) - Detailed setup
- [Custom Component README](custom_components/llmvm_conversation/README.md) - Component details
- [Example Configs](examples/homeassistant/) - Configuration files
- [Main LLMVM README](README.md) - Core documentation

## 🐛 Troubleshooting

**LLMVM not discovering MCP server?**
```bash
# Check MCP server is running
lsof -i :8765

# Check LLMVM logs
tail -f ~/.local/share/llmvm/logs/server.log | grep MCP
```

**Conversation agent not responding?**
```bash
# Check LLMVM server health
curl http://localhost:8011/health

# Check HA logs
tail -f /config/home-assistant.log | grep llmvm
```

## 🚀 Advanced Setup

### Production Deployment
See [examples/homeassistant/systemd-*.service](examples/homeassistant/)

### Docker Deployment
See [examples/homeassistant/docker-compose.yml](examples/homeassistant/docker-compose.yml)

### Automated Startup
See [examples/homeassistant/startup-script.sh](examples/homeassistant/startup-script.sh)

## 💬 Support

- Issues: [GitHub Issues](https://github.com/9600dev/llmvm/issues)
- Docs: [docs/homeassistant-integration.md](docs/homeassistant-integration.md)

---

**Built with**:
- [LLMVM](https://github.com/9600dev/llmvm) - LLM agent framework
- [HomeAssistant MCP Server](https://github.com/cronus42/homeassistant-mcp) - 60 HA tools
- [Model Context Protocol](https://modelcontextprotocol.io/) - Tool integration standard
