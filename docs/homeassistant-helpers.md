# HomeAssistant Helpers for LLMVM

This document describes the HomeAssistant helpers available in LLMVM, which provide direct integration with your HomeAssistant instance using the Python `homeassistant_api` library.

## Overview

The HomeAssistant helpers allow the LLM to directly interact with your HomeAssistant instance without requiring an MCP server. This approach is simpler and more lightweight than the MCP-based integration.

## Architecture

```
LLMVM Server                          HomeAssistant
┌──────────────────────────┐         ┌─────────────────┐
│                          │         │                 │
│  Agent Loop              │         │                 │
│  ┌────────────────────┐  │         │                 │
│  │ 1. Call Local LLM  │  │         │                 │
│  │ 2. Generate code   │  │         │                 │
│  │ 3. Execute helpers │  │         │                 │
│  └─────────┬──────────┘  │         │                 │
│            │             │         │                 │
│  ┌─────────▼──────────┐  │  REST   │                 │
│  │ HomeAssistant      │──┼────────>│  REST API       │
│  │ Helpers            │  │  API    │  (Port 8123)    │
│  │ - get_state()      │  │         │                 │
│  │ - turn_on()        │  │         │                 │
│  │ - get_sensors()    │  │         │                 │
│  │ - ...              │  │         │                 │
│  └────────────────────┘  │         │                 │
└──────────────────────────┘         └─────────────────┘
```

## Setup

### Prerequisites

1. HomeAssistant instance running and accessible
2. Long-lived access token from HomeAssistant
3. Python `homeassistant_api` library installed (already in conda base env)

### Configuration

1. **Set environment variables** (already configured in `~/.bashrc`):
   ```bash
   export HA_URL="http://192.168.0.201:8123/api"
   export HA_TOKEN="your_long_lived_access_token_here"
   ```

2. **Helpers are registered** in `~/.config/llmvm/config.yaml`:
   ```yaml
   helper_functions:
     # ... other helpers ...

     # HomeAssistant - Smart Home Control
     - llmvm.server.tools.homeassistant.HomeAssistantHelpers.get_state
     - llmvm.server.tools.homeassistant.HomeAssistantHelpers.turn_on
     - llmvm.server.tools.homeassistant.HomeAssistantHelpers.turn_off
     # ... etc
   ```

3. **Restart the LLMVM server** for changes to take effect.

## Available Helpers

### State Query Helpers

#### `get_state(entity_id: str) -> str`
Get the current state of a specific entity.

```python
<helpers>
state = HomeAssistantHelpers.get_state('light.living_room')
result(f'Living room light is: {state}')
</helpers>
```

#### `get_entity_attributes(entity_id: str) -> Dict[str, Any]`
Get all attributes of a specific entity.

```python
<helpers>
attrs = HomeAssistantHelpers.get_entity_attributes('light.living_room')
brightness = attrs.get('brightness')
result(f'Brightness: {brightness}')
</helpers>
```

#### `get_entities_by_domain(domain: str) -> List[Tuple[str, str]]`
Get all entities for a specific domain (light, switch, sensor, etc.).

```python
<helpers>
lights = HomeAssistantHelpers.get_entities_by_domain('light')
for entity_id, state in lights:
    result(f'{entity_id}: {state}')
</helpers>
```

### Control Helpers

#### `turn_on(entity_id: str, **kwargs) -> bool`
Turn on an entity with optional parameters.

```python
<helpers>
# Simple turn on
HomeAssistantHelpers.turn_on('light.living_room')

# Turn on with brightness (0-255)
HomeAssistantHelpers.turn_on('light.living_room', brightness=128)

# Turn on with RGB color
HomeAssistantHelpers.turn_on('light.living_room', rgb_color=[255, 0, 0])
</helpers>
```

#### `turn_off(entity_id: str, **kwargs) -> bool`
Turn off an entity.

```python
<helpers>
HomeAssistantHelpers.turn_off('light.living_room')
</helpers>
```

#### `toggle(entity_id: str) -> bool`
Toggle an entity's state.

```python
<helpers>
HomeAssistantHelpers.toggle('light.living_room')
</helpers>
```

### Specialized Helpers

#### `set_light_brightness(entity_id: str, brightness: int) -> bool`
Set the brightness of a light (0-255).

```python
<helpers>
# Set to 50% brightness
HomeAssistantHelpers.set_light_brightness('light.living_room', 128)
</helpers>
```

#### `set_light_color(entity_id: str, rgb: Tuple[int, int, int]) -> bool`
Set the color of a light.

```python
<helpers>
# Set to red
HomeAssistantHelpers.set_light_color('light.living_room', (255, 0, 0))
</helpers>
```

#### `set_climate_temperature(entity_id: str, temperature: float) -> bool`
Set the target temperature for a climate entity.

```python
<helpers>
HomeAssistantHelpers.set_climate_temperature('climate.living_room', 22.5)
</helpers>
```

### Discovery Helpers

#### `get_all_lights() -> List[Tuple[str, str, Dict[str, Any]]]`
Get all lights with their states and attributes.

```python
<helpers>
lights = HomeAssistantHelpers.get_all_lights()
for entity_id, state, attrs in lights:
    friendly_name = attrs.get('friendly_name', entity_id)
    result(f'{friendly_name}: {state}')
</helpers>
```

#### `get_sensors() -> List[Tuple[str, str, Dict[str, Any]]]`
Get all sensors with their states and attributes.

```python
<helpers>
sensors = HomeAssistantHelpers.get_sensors()
for entity_id, state, attrs in sensors:
    unit = attrs.get('unit_of_measurement', '')
    result(f'{entity_id}: {state} {unit}')
</helpers>
```

#### `get_switches() -> List[Tuple[str, str, Dict[str, Any]]]`
Get all switches with their states and attributes.

```python
<helpers>
switches = HomeAssistantHelpers.get_switches()
for entity_id, state, attrs in switches:
    result(f'{entity_id}: {state}')
</helpers>
```

#### `search_entities(search_term: str) -> List[Tuple[str, str, Dict[str, Any]]]`
Search for entities by name or entity_id.

```python
<helpers>
# Find all living room entities
results = HomeAssistantHelpers.search_entities('living_room')
for entity_id, state, attrs in results:
    result(f'{entity_id}: {state}')
</helpers>
```

### Advanced Helpers

#### `call_service(domain: str, service: str, **kwargs) -> bool`
Call any HomeAssistant service.

```python
<helpers>
# Call a notification service
HomeAssistantHelpers.call_service('notify', 'notify',
                                  message='Hello from LLMVM!')
</helpers>
```

#### `activate_scene(scene_id: str) -> bool`
Activate a scene.

```python
<helpers>
HomeAssistantHelpers.activate_scene('scene.movie_time')
</helpers>
```

#### `get_config() -> Dict[str, Any]`
Get HomeAssistant configuration.

```python
<helpers>
config = HomeAssistantHelpers.get_config()
location = (config.get('latitude'), config.get('longitude'))
result(f'Home location: {location}')
</helpers>
```

## Example Usage Scenarios

### 1. Turn on all lights in a room

**User Query**: "Turn on all living room lights"

```python
<helpers>
# Search for living room lights
lights = HomeAssistantHelpers.search_entities('living room')

# Filter to only lights and turn them on
for entity_id, state, attrs in lights:
    if entity_id.startswith('light.'):
        HomeAssistantHelpers.turn_on(entity_id)
        result(f'Turned on {entity_id}')
</helpers>
```

### 2. Get temperature readings

**User Query**: "What are the current temperatures in the house?"

```python
<helpers>
# Get all sensors
sensors = HomeAssistantHelpers.get_sensors()

# Filter to temperature sensors
temps = []
for entity_id, state, attrs in sensors:
    unit = attrs.get('unit_of_measurement', '')
    device_class = attrs.get('device_class', '')
    if unit in ['°C', '°F'] or device_class == 'temperature':
        friendly_name = attrs.get('friendly_name', entity_id)
        temps.append(f'{friendly_name}: {state}{unit}')

result('\n'.join(temps))
</helpers>
```

### 3. Create a movie scene

**User Query**: "Set up the living room for a movie"

```python
<helpers>
# Dim the lights
lights = HomeAssistantHelpers.search_entities('living room')
for entity_id, state, attrs in lights:
    if entity_id.startswith('light.'):
        HomeAssistantHelpers.set_light_brightness(entity_id, 20)

# Or activate a predefined scene
HomeAssistantHelpers.activate_scene('scene.movie_time')

result('Living room is ready for a movie!')
</helpers>
```

### 4. Climate control based on outside temperature

**User Query**: "If it's cold outside, turn on the heater"

```python
<helpers>
# Get outdoor temperature
outdoor_temp = float(HomeAssistantHelpers.get_state('sensor.outdoor_temperature'))

if outdoor_temp < 15:
    # Turn on climate system and set to 22°C
    HomeAssistantHelpers.set_climate_temperature('climate.living_room', 22.0)
    result(f'It\'s {outdoor_temp}°C outside. Heater turned on to 22°C.')
else:
    result(f'It\'s {outdoor_temp}°C outside. No heating needed.')
</helpers>
```

## Comparison with MCP Integration

| Feature | Python Helpers | MCP Integration |
|---------|---------------|-----------------|
| Setup complexity | Simple | More complex |
| Dependencies | homeassistant_api only | MCP server + dependencies |
| Latency | Low | Slightly higher (extra IPC) |
| Flexibility | Direct API access | Limited to MCP tools |
| Maintenance | Single codebase | Two codebases (LLMVM + MCP server) |

## Troubleshooting

### "HomeAssistant token not found" error

Make sure the `HA_TOKEN` environment variable is set:
```bash
export HA_TOKEN="your_token_here"
```

### Connection refused errors

1. Check that HomeAssistant is accessible:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" http://192.168.0.201:8123/api/
   ```

2. Verify the `HA_URL` is correct (should end with `/api`):
   ```bash
   export HA_URL="http://192.168.0.201:8123/api"
   ```

### Helpers not loading

1. Check that helpers are registered in `~/.config/llmvm/config.yaml`
2. Restart the LLMVM server
3. Check server logs for import errors:
   ```bash
   tail -f ~/.local/share/llmvm/logs/server.log | grep -i homeassistant
   ```

## Security Considerations

1. **Protect your token**: The long-lived access token has full access to your HomeAssistant instance. Keep it secure.

2. **Network security**: If running LLMVM on a different machine than HomeAssistant, ensure the network connection is secure.

3. **Token rotation**: Periodically rotate your long-lived access token in HomeAssistant.

## Future Enhancements

Potential improvements for the HomeAssistant helpers:

1. **Caching**: Cache entity states to reduce API calls
2. **WebSocket support**: Use WebSocket API for real-time state updates
3. **Error handling**: More robust error handling and retry logic
4. **Automation creation**: Helpers to create/modify automations
5. **History queries**: Better support for querying entity history

## Contributing

To add new HomeAssistant helpers:

1. Add methods to `/home/texx0/llmvm/llmvm/server/tools/homeassistant.py`
2. Register new methods in `~/.config/llmvm/config.yaml`
3. Test thoroughly
4. Update this documentation

## See Also

- [HomeAssistant API Documentation](https://homeassistantapi.readthedocs.io/)
- [HomeAssistant REST API](https://developers.home-assistant.io/docs/api/rest)
- [LLMVM README](../README.md)
