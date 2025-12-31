"""
Prompt caching module for LLMVM.
Pre-computes and caches system prompts to enable Ollama KV cache reuse.
"""
import logging
from typing import Dict, Tuple, Optional, Callable, List

from llmvm.common.helpers import Helpers
from llmvm.common.objects import System, User, TextContent

# Cache storage
_cached_prompts: Dict[str, Tuple[System, User]] = {}
_cached_helper_descriptions: Optional[str] = None

def get_cached_helper_descriptions(helpers: List[Callable]) -> str:
    """Get cached helper descriptions (computed once)."""
    global _cached_helper_descriptions
    if _cached_helper_descriptions is None:
        _cached_helper_descriptions = "\n".join([
            Helpers.get_function_description_flat(f) for f in helpers
        ])
        logging.info(f"Cached helper descriptions: {len(_cached_helper_descriptions)} chars")
    return _cached_helper_descriptions

def invalidate_cache():
    """Invalidate the prompt cache (e.g., when helpers change)."""
    global _cached_prompts, _cached_helper_descriptions
    _cached_prompts = {}
    _cached_helper_descriptions = None
    logging.info("Prompt cache invalidated")

def get_cached_system_prompt(
    executor,
    model: str,
    thinking: int,
    helpers: List[Callable]
) -> Tuple[System, User]:
    """
    Get cached system prompt for a given executor/model combination.
    Returns copies of the cached messages to avoid mutation issues.
    """
    global _cached_prompts

    cache_key = f"{executor.name()}:{model}:{thinking}"

    if cache_key not in _cached_prompts:
        # Determine which prompt to use
        if thinking > 0:
            prompt_name = "python_continuation_execution_reasoning.prompt"
        else:
            prompt_name = "python_continuation_execution.prompt"

        system_message, tools_message = Helpers.prompts(
            prompt_name=prompt_name,
            template={
                "functions": get_cached_helper_descriptions(helpers),
                "context_window_tokens": str(executor.max_input_tokens()),
                "context_window_words": str(int(executor.max_input_tokens() * 0.75)),
                "context_window_bytes": str(int(executor.max_input_tokens() * 4)),
            },
            user_token=executor.user_token(),
            assistant_token=executor.assistant_token(),
            scratchpad_token=executor.scratchpad_token(),
            append_token=executor.append_token(),
        )

        # Mark as hidden
        system_message.hidden = True
        tools_message.hidden = True

        _cached_prompts[cache_key] = (system_message, tools_message)
        logging.info(f"Cached system prompt for {cache_key}: {len(system_message.get_str())} chars")

    # Return copies to avoid mutation
    cached_sys, cached_tools = _cached_prompts[cache_key]
    return (
        System(cached_sys.get_str()),
        User([TextContent(cached_tools.get_str())])
    )
