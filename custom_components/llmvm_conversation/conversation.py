"""LLMVM conversation agent for Home Assistant."""
from __future__ import annotations

import logging
from typing import Literal

import httpx

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import intent
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import ulid

from .const import (
    CONF_LLMVM_EXECUTOR,
    CONF_LLMVM_MODEL,
    CONF_LLMVM_URL,
    CONF_MAX_TOKENS,
    CONF_TEMPERATURE,
    DEFAULT_EXECUTOR,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up conversation entities."""
    agent = LLMVMConversationEntity(config_entry)
    async_add_entities([agent])


class LLMVMConversationEntity(conversation.ConversationEntity):
    """LLMVM conversation agent."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.entry = config_entry
        self._attr_unique_id = config_entry.entry_id
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "LLMVM Conversation Agent",
            "manufacturer": "LLMVM",
            "model": "Agent",
        }

        # Thread storage for conversation context
        self._threads: dict[str, list[dict]] = {}

    @property
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""
        return ["en"]

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a sentence."""
        llmvm_url = self.entry.data.get(CONF_LLMVM_URL, "http://localhost:8011").rstrip("/")
        executor = self.entry.data.get(CONF_LLMVM_EXECUTOR, DEFAULT_EXECUTOR)
        model = self.entry.data.get(CONF_LLMVM_MODEL, DEFAULT_MODEL)
        temperature = self.entry.data.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE)
        max_tokens = self.entry.data.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS)

        # Use conversation_id to maintain context
        conversation_id = user_input.conversation_id or ulid.ulid()

        # Get or create thread messages
        if conversation_id not in self._threads:
            self._threads[conversation_id] = []

        messages = self._threads[conversation_id]

        # Add user message
        messages.append({
            "role": "user",
            "content": user_input.text
        })

        # Prepare request to LLMVM
        request_data = {
            "executor": executor,
            "messages": messages,
            "mode": "tool",  # Use tool mode to enable agent capabilities
            "stream": False,
        }

        if model:
            request_data["model"] = model
        if temperature is not None:
            request_data["temperature"] = temperature
        if max_tokens is not None:
            request_data["max_tokens"] = max_tokens

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{llmvm_url}/v1/tools/completions",
                    json=request_data,
                )
                response.raise_for_status()
                result = response.json()

            # Extract assistant's response
            if "messages" in result and len(result["messages"]) > 0:
                # Get the last assistant message
                for msg in reversed(result["messages"]):
                    if msg.get("role") == "assistant":
                        response_text = msg.get("content", "I apologize, but I couldn't process that request.")
                        break
                else:
                    response_text = "I apologize, but I couldn't process that request."

                # Update thread with full message history
                self._threads[conversation_id] = result["messages"]
            else:
                response_text = "I apologize, but I couldn't process that request."
                # Still add assistant message to maintain conversation flow
                messages.append({
                    "role": "assistant",
                    "content": response_text
                })

            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_speech(response_text)

            return conversation.ConversationResult(
                conversation_id=conversation_id,
                response=intent_response,
            )

        except httpx.TimeoutException as err:
            _LOGGER.error("Timeout communicating with LLMVM server: %s", err)
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                "Request to LLMVM server timed out. The operation may still be processing.",
            )
            return conversation.ConversationResult(
                conversation_id=conversation_id,
                response=intent_response,
            )

        except httpx.HTTPError as err:
            _LOGGER.error("Error communicating with LLMVM server: %s", err)
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"Failed to communicate with LLMVM server: {err}",
            )
            return conversation.ConversationResult(
                conversation_id=conversation_id,
                response=intent_response,
            )

        except Exception as err:
            _LOGGER.exception("Unexpected error processing conversation: %s", err)
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"Unexpected error: {err}",
            )
            return conversation.ConversationResult(
                conversation_id=conversation_id,
                response=intent_response,
            )
