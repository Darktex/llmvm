import os
from typing import Any, Dict, List, Optional, Tuple
from homeassistant_api import Client
from homeassistant_api.models.entity import Entity
from homeassistant_api.models.states import State


class HomeAssistantHelpers():
    """
    Helper class for interacting with HomeAssistant.
    Provides methods to control and query HomeAssistant entities.

    Configuration:
    Set these environment variables or they will use defaults:
    - HA_URL: HomeAssistant URL (default: http://192.168.0.201:8123/api)
    - HA_TOKEN: HomeAssistant long-lived access token (required)
    """

    _client: Optional[Client] = None
    _url: Optional[str] = None
    _token: Optional[str] = None

    @classmethod
    def _get_client(cls) -> Client:
        """Get or create the HomeAssistant client instance."""
        if cls._client is None:
            # Try to get from environment variables
            url = os.getenv('HA_URL', 'http://192.168.0.201:8123/api')
            token = os.getenv('HA_TOKEN')

            if not token:
                raise ValueError(
                    "HomeAssistant token not found. Please set HA_TOKEN environment variable. "
                    "You can get a long-lived token from HomeAssistant: "
                    "Profile → Long-lived access tokens → Create Token"
                )

            cls._url = url
            cls._token = token
            cls._client = Client(url, token)

        return cls._client

    @staticmethod
    def get_state(entity_id: str) -> str:
        """
        Get the current state of a specific entity.

        Example:
        state = HomeAssistantHelpers.get_state('light.living_room')

        :param entity_id: The entity ID (e.g., 'light.living_room', 'sensor.temperature')
        :return: The current state of the entity (e.g., 'on', 'off', '23.5')
        """
        client = HomeAssistantHelpers._get_client()
        state_obj = client.get_state(entity_id=entity_id)
        return state_obj.state

    @staticmethod
    def get_entity_attributes(entity_id: str) -> Dict[str, Any]:
        """
        Get all attributes of a specific entity.

        Example:
        attrs = HomeAssistantHelpers.get_entity_attributes('light.living_room')
        brightness = attrs.get('brightness')

        :param entity_id: The entity ID
        :return: Dictionary of entity attributes
        """
        client = HomeAssistantHelpers._get_client()
        state_obj = client.get_state(entity_id=entity_id)
        return state_obj.attributes

    @staticmethod
    def get_entities_by_domain(domain: str) -> List[Tuple[str, str]]:
        """
        Get all entities for a specific domain.

        Example:
        lights = HomeAssistantHelpers.get_entities_by_domain('light')
        for entity_id, state in lights:
            print(f'{entity_id}: {state}')

        :param domain: The domain (e.g., 'light', 'switch', 'sensor', 'climate')
        :return: List of tuples (entity_id, state)
        """
        client = HomeAssistantHelpers._get_client()
        states = client.get_states()

        domain_entities = []
        for state in states:
            if state.entity_id.startswith(f'{domain}.'):
                domain_entities.append((state.entity_id, state.state))

        return domain_entities

    @staticmethod
    def turn_on(entity_id: str, **kwargs) -> bool:
        """
        Turn on an entity (light, switch, etc.).

        Example:
        # Simple turn on
        HomeAssistantHelpers.turn_on('light.living_room')

        # Turn on with brightness
        HomeAssistantHelpers.turn_on('light.living_room', brightness=128)

        # Turn on with color
        HomeAssistantHelpers.turn_on('light.living_room', rgb_color=[255, 0, 0])

        :param entity_id: The entity ID
        :param kwargs: Additional service data (brightness, rgb_color, etc.)
        :return: True if successful
        """
        client = HomeAssistantHelpers._get_client()
        domain = entity_id.split('.')[0]

        service_data = {'entity_id': entity_id}
        service_data.update(kwargs)

        client.trigger_service(domain, 'turn_on', **service_data)
        return True

    @staticmethod
    def turn_off(entity_id: str, **kwargs) -> bool:
        """
        Turn off an entity (light, switch, etc.).

        Example:
        HomeAssistantHelpers.turn_off('light.living_room')

        :param entity_id: The entity ID
        :param kwargs: Additional service data
        :return: True if successful
        """
        client = HomeAssistantHelpers._get_client()
        domain = entity_id.split('.')[0]

        service_data = {'entity_id': entity_id}
        service_data.update(kwargs)

        client.trigger_service(domain, 'turn_off', **service_data)
        return True

    @staticmethod
    def toggle(entity_id: str) -> bool:
        """
        Toggle an entity's state.

        Example:
        HomeAssistantHelpers.toggle('light.living_room')

        :param entity_id: The entity ID
        :return: True if successful
        """
        client = HomeAssistantHelpers._get_client()
        domain = entity_id.split('.')[0]

        client.trigger_service(domain, 'toggle', entity_id=entity_id)
        return True

    @staticmethod
    def set_light_brightness(entity_id: str, brightness: int) -> bool:
        """
        Set the brightness of a light.

        Example:
        # Set to 50% brightness
        HomeAssistantHelpers.set_light_brightness('light.living_room', 128)

        :param entity_id: The light entity ID
        :param brightness: Brightness value (0-255)
        :return: True if successful
        """
        return HomeAssistantHelpers.turn_on(entity_id, brightness=brightness)

    @staticmethod
    def set_light_color(entity_id: str, rgb: Tuple[int, int, int]) -> bool:
        """
        Set the color of a light.

        Example:
        # Set to red
        HomeAssistantHelpers.set_light_color('light.living_room', (255, 0, 0))

        :param entity_id: The light entity ID
        :param rgb: RGB color tuple (0-255 for each channel)
        :return: True if successful
        """
        return HomeAssistantHelpers.turn_on(entity_id, rgb_color=list(rgb))

    @staticmethod
    def set_climate_temperature(entity_id: str, temperature: float) -> bool:
        """
        Set the target temperature for a climate entity.

        Example:
        HomeAssistantHelpers.set_climate_temperature('climate.living_room', 22.5)

        :param entity_id: The climate entity ID
        :param temperature: Target temperature
        :return: True if successful
        """
        client = HomeAssistantHelpers._get_client()
        client.trigger_service('climate', 'set_temperature',
                             entity_id=entity_id,
                             temperature=temperature)
        return True

    @staticmethod
    def call_service(domain: str, service: str, **kwargs) -> bool:
        """
        Call any HomeAssistant service.

        Example:
        # Call a custom service
        HomeAssistantHelpers.call_service('notify', 'notify',
                                          message='Hello from LLMVM!')

        :param domain: The service domain
        :param service: The service name
        :param kwargs: Service data
        :return: True if successful
        """
        client = HomeAssistantHelpers._get_client()
        client.trigger_service(domain, service, **kwargs)
        return True

    @staticmethod
    def get_all_lights() -> List[Tuple[str, str, Dict[str, Any]]]:
        """
        Get all lights with their states and attributes.

        Example:
        lights = HomeAssistantHelpers.get_all_lights()
        for entity_id, state, attrs in lights:
            if state == 'on':
                print(f'{entity_id} is on with brightness {attrs.get("brightness", "N/A")}')

        :return: List of tuples (entity_id, state, attributes)
        """
        client = HomeAssistantHelpers._get_client()
        states = client.get_states()

        lights = []
        for state in states:
            if state.entity_id.startswith('light.'):
                lights.append((state.entity_id, state.state, state.attributes))

        return lights

    @staticmethod
    def get_sensors() -> List[Tuple[str, str, Dict[str, Any]]]:
        """
        Get all sensors with their states and attributes.

        Example:
        sensors = HomeAssistantHelpers.get_sensors()
        for entity_id, state, attrs in sensors:
            unit = attrs.get('unit_of_measurement', '')
            print(f'{entity_id}: {state} {unit}')

        :return: List of tuples (entity_id, state, attributes)
        """
        client = HomeAssistantHelpers._get_client()
        states = client.get_states()

        sensors = []
        for state in states:
            if state.entity_id.startswith('sensor.'):
                sensors.append((state.entity_id, state.state, state.attributes))

        return sensors

    @staticmethod
    def get_switches() -> List[Tuple[str, str, Dict[str, Any]]]:
        """
        Get all switches with their states and attributes.

        Example:
        switches = HomeAssistantHelpers.get_switches()
        for entity_id, state, attrs in switches:
            print(f'{entity_id}: {state}')

        :return: List of tuples (entity_id, state, attributes)
        """
        client = HomeAssistantHelpers._get_client()
        states = client.get_states()

        switches = []
        for state in states:
            if state.entity_id.startswith('switch.'):
                switches.append((state.entity_id, state.state, state.attributes))

        return switches

    @staticmethod
    def search_entities(search_term: str) -> List[Tuple[str, str, Dict[str, Any]]]:
        """
        Search for entities by name or entity_id.

        Example:
        # Find all living room entities
        results = HomeAssistantHelpers.search_entities('living_room')
        for entity_id, state, attrs in results:
            print(f'{entity_id}: {state}')

        :param search_term: Search term to match against entity_id or friendly_name
        :return: List of tuples (entity_id, state, attributes)
        """
        client = HomeAssistantHelpers._get_client()
        states = client.get_states()

        results = []
        search_lower = search_term.lower()

        for state in states:
            entity_id_match = search_lower in state.entity_id.lower()
            friendly_name = state.attributes.get('friendly_name', '')
            name_match = search_lower in friendly_name.lower()

            if entity_id_match or name_match:
                results.append((state.entity_id, state.state, state.attributes))

        return results

    @staticmethod
    def get_entity_history(entity_id: str, hours: int = 24) -> str:
        """
        Get the history of an entity.

        Example:
        history = HomeAssistantHelpers.get_entity_history('sensor.temperature', hours=12)

        :param entity_id: The entity ID
        :param hours: Number of hours of history to retrieve
        :return: String representation of the entity's history
        """
        import datetime
        client = HomeAssistantHelpers._get_client()

        end_time = datetime.datetime.now()
        start_time = end_time - datetime.timedelta(hours=hours)

        history = client.get_history(entity_ids=[entity_id],
                                     start_time=start_time,
                                     end_time=end_time)

        return str(history)

    @staticmethod
    def activate_scene(scene_id: str) -> bool:
        """
        Activate a scene.

        Example:
        HomeAssistantHelpers.activate_scene('scene.movie_time')

        :param scene_id: The scene entity ID
        :return: True if successful
        """
        client = HomeAssistantHelpers._get_client()
        client.trigger_service('scene', 'turn_on', entity_id=scene_id)
        return True

    @staticmethod
    def get_config() -> Dict[str, Any]:
        """
        Get HomeAssistant configuration.

        Example:
        config = HomeAssistantHelpers.get_config()
        print(f"Location: {config.get('latitude')}, {config.get('longitude')}")

        :return: Configuration dictionary
        """
        client = HomeAssistantHelpers._get_client()
        config = client.get_config()
        return config
