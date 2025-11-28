import os
from typing import Any, Awaitable, Callable, Optional, cast

from llmvm.common.container import Container
from llmvm.common.helpers import Helpers
from llmvm.common.logging_helpers import setup_logging
from llmvm.common.object_transformers import ObjectTransformers
from llmvm.common.objects import (
    Assistant,
    AstNode,
    BrowserContent,
    Content,
    FileContent,
    HTMLContent,
    ImageContent,
    MarkdownContent,
    Message,
    PdfContent,
    System,
    TextContent,
    User,
    awaitable_none,
)
from llmvm.common.openai_executor import OpenAIExecutor
from llmvm.common.perf import TokenStreamManager

logging = setup_logging()


class OllamaExecutor(OpenAIExecutor):
    """
    Ollama executor that uses Ollama's OpenAI-compatible API.

    Ollama provides a local inference server with OpenAI-compatible endpoints,
    allowing us to inherit from OpenAIExecutor and override specific behaviors.
    """

    def __init__(
        self,
        api_key: str = 'ollama',  # Ollama doesn't validate API keys locally
        default_model: str = 'llama3.1',
        api_endpoint: str = 'http://localhost:11434/v1',
        default_max_input_len: int = 128000,
        default_max_output_len: int = 4096,
        max_images: int = 10,
    ):
        """
        Initialize the Ollama executor.

        Args:
            api_key: API key (unused by Ollama, but required by OpenAI client)
            default_model: Default model to use (e.g., 'llama3.1', 'mistral', 'qwen2.5')
            api_endpoint: Ollama server endpoint
            default_max_input_len: Maximum input tokens
            default_max_output_len: Maximum output tokens
            max_images: Maximum number of images to include in requests
        """
        super().__init__(
            api_key=api_key,
            default_model=default_model,
            api_endpoint=api_endpoint,
            default_max_input_len=default_max_input_len,
            default_max_output_len=default_max_output_len,
            max_images=max_images,
        )

    def user_token(self) -> str:
        return 'User'

    def assistant_token(self) -> str:
        return 'Assistant'

    def append_token(self) -> str:
        return ''

    def scratchpad_token(self) -> str:
        return 'scratchpad'

    def name(self) -> str:
        return 'ollama'

    def max_input_tokens(
        self,
        model: Optional[str] = None,
    ) -> int:
        """
        Return maximum input tokens for the model.

        Different Ollama models have different context windows.
        This can be overridden via config or environment variables.
        """
        # Common context windows for popular Ollama models:
        # - llama3.1: 128k
        # - qwen2.5: 128k
        # - mistral: 32k
        # - gemma2: 8k
        # - llama2: 4k
        return self.default_max_input_len

    def max_output_tokens(
        self,
        model: Optional[str] = None,
    ) -> int:
        """
        Return maximum output tokens for the model.
        """
        return self.default_max_output_len

    def responses(self, model: Optional[str]) -> bool:
        """
        Ollama does not support the 'responses' API format.
        Always return False to use the standard chat completions API.
        """
        return False

    def does_not_stop(self, model: Optional[str]) -> bool:
        """
        Some Ollama models may not respect stop tokens properly.
        Override this if needed for specific models.
        """
        # Most Ollama models handle stop tokens correctly
        return False

    async def count_tokens(
        self,
        messages: list[Message],
    ) -> int:
        """
        Count tokens in messages.

        Ollama doesn't provide a tokenization API, so we use tiktoken
        as an approximation (inherited from OpenAIExecutor).
        This may not be perfectly accurate for all models but is good enough.
        """
        messages_list = self.unpack_and_wrap_messages(messages, self.default_model)
        return await self.count_tokens_dict(messages_list)

    async def count_tokens_dict(
        self,
        messages: list[dict[str, Any]],
    ) -> int:
        """
        Count tokens in dictionary-formatted messages.

        Uses the parent class's tiktoken-based counting as an approximation.
        """
        return await super().count_tokens_dict(messages)

    async def aexecute_direct(
        self,
        messages: list[dict[str, str]],
        functions: list[dict[str, str]] = [],
        model: Optional[str] = None,
        max_output_tokens: int = 4096,
        temperature: float = 1.0,
        stop_tokens: list[str] = [],
        thinking: int = 0,
    ) -> TokenStreamManager:
        """
        Execute a request directly using Ollama's OpenAI-compatible API.

        Ollama supports:
        - Standard chat completions
        - Streaming responses
        - Stop tokens
        - Temperature control

        IMPORTANT: Ollama's OpenAI-compatible API does NOT support passing num_ctx
        via the API. You must create model variants with the desired context size:

        docker exec open-webui sh -c 'echo -e "FROM modelname\\nPARAMETER num_ctx 262144" > /root/.ollama/ctx.Modelfile && ollama create modelname-ctx -f /root/.ollama/ctx.Modelfile'

        Then use 'modelname-ctx' instead of 'modelname' to get the full context.
        """
        # Ollama doesn't support reasoning/thinking modes like o1/o3
        if thinking > 0:
            logging.debug(f'Ollama does not support reasoning modes. Ignoring thinking={thinking}')
            thinking = 0

        # Log warning for large prompts that might get truncated
        message_tokens = await self.count_tokens_dict(messages)
        if message_tokens > 4096 and '-ctx' not in (model or self.default_model):
            logging.warning(
                f"Ollama: Prompt has {message_tokens} tokens but model '{model or self.default_model}' "
                f"may use default 2048 context. Create a -ctx variant with: "
                f"docker exec open-webui sh -c 'echo -e \"FROM {model or self.default_model}\\nPARAMETER num_ctx 262144\" "
                f"> /root/.ollama/ctx.Modelfile && ollama create {model or self.default_model}-ctx -f /root/.ollama/ctx.Modelfile'"
            )

        return await super().aexecute_direct(
            messages=messages,
            functions=functions,
            model=model,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            stop_tokens=stop_tokens,
            thinking=thinking,
        )

    async def aexecute(
        self,
        messages: list[Message],
        max_output_tokens: int = 4096,
        temperature: float = 1.0,
        stop_tokens: list[str] = [],
        model: Optional[str] = None,
        thinking: int = 0,
        stream_handler: Callable[[AstNode], Awaitable[None]] = awaitable_none,
    ) -> Assistant:
        """
        Execute a request asynchronously with Ollama.

        This is the main entry point for making requests to Ollama models.
        It handles streaming, token counting, and response parsing.
        """
        return await super().aexecute(
            messages=messages,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            stop_tokens=stop_tokens,
            model=model,
            thinking=thinking,
            stream_handler=stream_handler,
        )
