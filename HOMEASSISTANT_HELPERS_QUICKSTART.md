# 🏠 HomeAssistant Helpers Quick Start

Direct HomeAssistant integration using Python API (simpler than MCP!)

## ✅ What's Done

The HomeAssistant helpers are now fully integrated and ready to use!

- ✅ HomeAssistant helper class created (`llmvm/server/tools/homeassistant.py`)
- ✅ Helpers registered in config (`~/.config/llmvm/config.yaml`)
- ✅ Environment variables configured (`~/.bashrc`)
- ✅ Tested and working with your HomeAssistant at 192.168.0.201

## 🚀 Quick Test

Start the client and try these commands:

```bash
llmvm
```

Then in the LLMVM REPL:

```
query>> list all my lights and their current states
```

```
query>> turn on the living room lights
```

```
query>> what's the temperature in the house?
```

```
query>> turn off all lights
```

## 📋 Available Helper Functions

The LLM has access to these HomeAssistant helper functions:

### 🔍 Query Functions
- `get_state(entity_id)` - Get state of any entity
- `get_entity_attributes(entity_id)` - Get all attributes
- `get_entities_by_domain(domain)` - Get all lights/switches/sensors/etc
- `get_all_lights()` - Get all lights with details
- `get_sensors()` - Get all sensors
- `get_switches()` - Get all switches
- `search_entities(search_term)` - Search by name

### 🎮 Control Functions
- `turn_on(entity_id, **kwargs)` - Turn on with optional brightness/color
- `turn_off(entity_id)` - Turn off
- `toggle(entity_id)` - Toggle state
- `set_light_brightness(entity_id, brightness)` - Set brightness 0-255
- `set_light_color(entity_id, (r, g, b))` - Set RGB color
- `set_climate_temperature(entity_id, temp)` - Set thermostat

### 🔧 Advanced Functions
- `call_service(domain, service, **kwargs)` - Call any HA service
- `activate_scene(scene_id)` - Activate a scene
- `get_config()` - Get HA configuration

## 🎯 Example Queries

**Simple control:**
```
turn on the bedroom light
set the living room light to 50% brightness
turn off all the lights in the kitchen
```

**Complex queries:**
```
if the outdoor temperature is below 18 degrees, turn on the heater
show me all sensors with temperature readings
turn on the living room lights and set them to warm white at 30%
```

**Information queries:**
```
what lights are currently on?
what's the status of all my switches?
show me the temperature sensors in the house
```

## 🔑 Your Configuration

- **HomeAssistant URL**: `http://192.168.0.201:8123/api`
- **Token**: Configured in `~/.bashrc` (HA_TOKEN)
- **Helper file**: `/home/texx0/llmvm/llmvm/server/tools/homeassistant.py`
- **Config file**: `~/.config/llmvm/config.yaml`

## 🔄 Restart Server

If you modified the config or helpers, restart the server:

```bash
# Find and kill the server
pkill -f "python -m llmvm.server"

# Start it again
start_llmvm_server
```

Or restart in the background:
```bash
pkill -f "python -m llmvm.server" && nohup start_llmvm_server > /tmp/llmvm_server.log 2>&1 &
```

## 📊 Your HomeAssistant Stats

When last tested:
- 🔆 **18 lights** configured
- 🔌 **3 switches** found (automation switches)
- 📡 **792 total entities**
- 🏠 **HomeAssistant at**: 192.168.0.201:8123

## 📚 Full Documentation

See [docs/homeassistant-helpers.md](docs/homeassistant-helpers.md) for:
- Complete API reference
- Example code snippets
- Troubleshooting guide
- Advanced usage patterns

## 🆚 MCP vs Python Helpers

You previously tried the MCP approach. Here's why this is better:

| Aspect | MCP Integration | Python Helpers |
|--------|----------------|----------------|
| Setup | Complex (separate server) | ✅ Simple (one file) |
| Dependencies | Many | ✅ Just homeassistant_api |
| Latency | Higher (IPC overhead) | ✅ Lower (direct API) |
| Code location | External repo | ✅ In llmvm codebase |
| Debugging | Two processes | ✅ Single process |

## ✨ What's Next?

Try these advanced scenarios:

1. **Conditional automation:**
   ```
   if it's after sunset, turn on the porch lights
   ```

2. **Multi-step tasks:**
   ```
   set up the living room for a movie: dim the lights to 10%,
   turn on the TV, and close the blinds
   ```

3. **Information aggregation:**
   ```
   give me a summary of all temperature sensors and which lights
   are currently on
   ```

4. **Smart responses:**
   ```
   is it cold in the house? if yes, turn on the heater
   ```

## 🐛 Troubleshooting

**Helpers not loading?**
1. Check server logs: `tail -f ~/.local/share/llmvm/logs/server.log | grep -i homeassistant`
2. Verify config: `grep -A 20 "HomeAssistant" ~/.config/llmvm/config.yaml`
3. Test import: `python -c "from llmvm.server.tools.homeassistant import HomeAssistantHelpers; print('OK')"`

**Can't connect to HomeAssistant?**
1. Test connection: `curl -H "Authorization: Bearer $HA_TOKEN" $HA_URL`
2. Check env vars: `echo $HA_URL && echo $HA_TOKEN`
3. Verify HA is running: `curl http://192.168.0.201:8123/`

**Server won't start?**
1. Check for errors: `python -m llmvm.server 2>&1 | grep -i error`
2. Test helper import: `python -c "import sys; sys.path.insert(0, '/home/texx0/llmvm'); from llmvm.server.tools.homeassistant import HomeAssistantHelpers"`

---

**Built with:**
- [LLMVM](https://github.com/9600dev/llmvm) - LLM agent framework
- [homeassistant_api](https://github.com/GrandMoff100/HomeAssistantAPI) - Python HA client
- Your HomeAssistant instance at 192.168.0.201

Enjoy your AI-powered smart home! 🎉
