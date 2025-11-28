#!/usr/bin/env python3
"""
Quick test script for HomeAssistant helpers.
Run this to verify the HomeAssistant integration is working.
"""

import os
import sys

# Add llmvm to path
sys.path.insert(0, '/home/texx0/llmvm')

# Set environment variables if not already set
if 'HA_URL' not in os.environ:
    os.environ['HA_URL'] = 'http://192.168.0.201:8123/api'
if 'HA_TOKEN' not in os.environ:
    os.environ['HA_TOKEN'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI4YmIzNTdkOGJkYTY0M2VkYmMzZWRiMzg0ZDhiOWJmNSIsImlhdCI6MTc2Mzk0MTk1MiwiZXhwIjoyMDc5MzAxOTUyfQ.np4ye5JHZiYwEk0DlqYqUYPvYmqDnpLyf-4YEd7_ztk'

from llmvm.server.tools.homeassistant import HomeAssistantHelpers

def main():
    print("🧪 Testing HomeAssistant Helpers Integration\n")
    print(f"HA_URL: {os.environ.get('HA_URL')}")
    print(f"HA_TOKEN: {'*' * 20}... (hidden)\n")

    try:
        # Test 1: Get all lights
        print("✓ Test 1: Getting all lights...")
        lights = HomeAssistantHelpers.get_all_lights()
        print(f"  Found {len(lights)} lights")
        for entity_id, state, attrs in lights[:3]:
            friendly_name = attrs.get('friendly_name', entity_id)
            print(f"    - {friendly_name}: {state}")
        print()

        # Test 2: Get sensors
        print("✓ Test 2: Getting sensors...")
        sensors = HomeAssistantHelpers.get_sensors()
        print(f"  Found {len(sensors)} sensors")

        # Find temperature sensors
        temp_sensors = []
        for entity_id, state, attrs in sensors:
            unit = attrs.get('unit_of_measurement', '')
            device_class = attrs.get('device_class', '')
            if unit in ['°C', '°F'] or device_class == 'temperature':
                temp_sensors.append((entity_id, state, attrs))

        if temp_sensors:
            print(f"  Found {len(temp_sensors)} temperature sensors:")
            for entity_id, state, attrs in temp_sensors[:3]:
                friendly_name = attrs.get('friendly_name', entity_id)
                unit = attrs.get('unit_of_measurement', '')
                print(f"    - {friendly_name}: {state}{unit}")
        print()

        # Test 3: Search entities
        print("✓ Test 3: Searching for entities...")
        results = HomeAssistantHelpers.search_entities('living')
        print(f"  Found {len(results)} entities with 'living' in name")
        for entity_id, state, attrs in results[:5]:
            print(f"    - {entity_id}: {state}")
        print()

        # Test 4: Get switches
        print("✓ Test 4: Getting switches...")
        switches = HomeAssistantHelpers.get_switches()
        print(f"  Found {len(switches)} switches")
        for entity_id, state, attrs in switches[:3]:
            friendly_name = attrs.get('friendly_name', entity_id)
            print(f"    - {friendly_name}: {state}")
        print()

        # Test 5: Get a specific state
        if lights:
            print("✓ Test 5: Getting specific entity state...")
            first_light = lights[0][0]
            state = HomeAssistantHelpers.get_state(first_light)
            print(f"  {first_light}: {state}")
            print()

        print("✅ All tests passed! HomeAssistant helpers are working correctly.\n")
        print("Now you can start the LLMVM server with:")
        print("  start_llmvm_server")
        print("\nAnd then use the client to query HomeAssistant:")
        print("  llmvm")
        print("  query>> what temperature is the house?")
        print("  query>> turn on the living room lights")
        print("  query>> list all my lights")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure:")
        print("1. HomeAssistant is running at http://192.168.0.201:8123")
        print("2. The HA_TOKEN is valid")
        print("3. The homeassistant_api library is installed")
        sys.exit(1)

if __name__ == '__main__':
    main()
