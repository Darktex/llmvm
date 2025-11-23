"""Config flow for LLMVM Conversation integration."""
from __future__ import annotations

import logging
from typing import Any

import httpx
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_LLMVM_EXECUTOR,
    CONF_LLMVM_MODEL,
    CONF_LLMVM_URL,
    CONF_MAX_TOKENS,
    CONF_TEMPERATURE,
    DEFAULT_EXECUTOR,
    DEFAULT_LLMVM_URL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_LLMVM_URL, default=DEFAULT_LLMVM_URL): str,
        vol.Optional(CONF_LLMVM_EXECUTOR, default=DEFAULT_EXECUTOR): str,
        vol.Optional(CONF_LLMVM_MODEL, default=DEFAULT_MODEL): str,
        vol.Optional(CONF_TEMPERATURE, default=DEFAULT_TEMPERATURE): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=2)
        ),
        vol.Optional(CONF_MAX_TOKENS, default=DEFAULT_MAX_TOKENS): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=128000)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    llmvm_url = data[CONF_LLMVM_URL].rstrip("/")

    # Test connection to LLMVM server
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{llmvm_url}/health")
            response.raise_for_status()
    except httpx.HTTPError as err:
        _LOGGER.error("Failed to connect to LLMVM server: %s", err)
        raise CannotConnect from err
    except Exception as err:
        _LOGGER.error("Unexpected error connecting to LLMVM server: %s", err)
        raise CannotConnect from err

    return {"title": f"LLMVM ({llmvm_url})"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LLMVM Conversation."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
