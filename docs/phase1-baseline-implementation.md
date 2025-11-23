# Phase 1: Baseline Implementation & Benchmarking

**Goal**: Establish baseline performance with Ollama, measure latency at each stage, identify bottlenecks.

## Overview

Phase 1 focuses on **measurement**, not optimization. We'll instrument the entire pipeline to understand where time is spent:

```
User speaks → ASR → HA Assist → LLMVM Conv Agent → LLMVM Server → LLM → Tool Execution → Response → TTS → Audio
     ↑          ↑         ↑              ↑                  ↑         ↑          ↑            ↑        ↑      ↑
     |          |         |              |                  |         |          |            |        |      |
  Latency  Latency   Latency        Latency            Latency   Latency    Latency      Latency  Latency End
   Point 1    Point 2  Point 3        Point 4            Point 5   Point 6    Point 7      Point 8  Point 9
```

**Latency Points to Measure:**
1. **ASR (Speech-to-Text)**: Voice → Text
2. **HA Routing**: HA Assist → Conversation Agent selection
3. **Agent Overhead**: Conv Agent → LLMVM HTTP call
4. **LLMVM Processing**: HTTP received → LLM request
5. **LLM Inference**: Model generation time (TTFT + generation)
6. **Tool Execution**: MCP tool calls (if any)
7. **LLMVM Response**: LLM done → HTTP response
8. **TTS (Text-to-Speech)**: Text → Audio
9. **Total End-to-End**: User speaks → User hears

---

## Prerequisites

- [x] HomeAssistant running
- [ ] Ollama installed with a model (e.g., `llama3:70b`)
- [ ] LLMVM installed
- [ ] HomeAssistant MCP server (optional for Phase 1, but recommended)

---

## Step-by-Step Implementation

### Step 1: Configure Ollama with OpenAI API

```bash
# On your DGX or local machine

# Install Ollama (if not already)
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model (start with something fast for baseline)
ollama pull llama3:8b  # Fast baseline
# OR
ollama pull qwen2.5:32b  # Better quality

# Ollama automatically exposes OpenAI-compatible API on port 11434
# Test it:
curl http://localhost:11434/v1/models
```

**Ollama automatically runs an OpenAI-compatible server!**
- Base URL: `http://localhost:11434/v1`
- No API key needed (local only)
- Models: whatever you `ollama pull`

---

### Step 2: Configure LLMVM to Use Ollama

Update `~/.config/llmvm/config.yaml`:

```yaml
# Use OpenAI executor pointing to Ollama
executor: 'openai'
openai_api_base: 'http://localhost:11434/v1'
default_openai_model: 'llama3:8b'  # Or whatever you pulled

# Server settings
server_host: '0.0.0.0'
server_port: 8011

# Keep all your existing helper_functions
helper_functions:
  - llmvm.server.bcl.BCL.datetime
  - llmvm.server.bcl.BCL.get_weather
  # ... (keep existing)
```

**Start LLMVM server:**
```bash
llmvm-server
```

**Test it works:**
```bash
curl http://localhost:8011/health
```

---

### Step 3: Install HomeAssistant MCP Server

```bash
# Clone and setup (if not already done)
cd ~
git clone https://github.com/cronus42/homeassistant-mcp.git
cd homeassistant-mcp
./setup.sh

# Configure .env
cat > .env << EOF
HOME_ASSISTANT_URL=http://localhost:8123
HOME_ASSISTANT_TOKEN=your_long_lived_token_here
EOF

# Test connection
python tests/test_connection.py

# Start server
python -m homeassistant_mcp.server --port 8765
```

**Verify LLMVM discovers it:**
```bash
# Check LLMVM logs
tail -f ~/.local/share/llmvm/logs/server.log | grep MCP

# Should see:
# "Detected SSE MCP server on port 8765"
# "Connected to MCP server (sse) with 60 tools"
```

---

### Step 4: Install LLMVM Conversation Agent in HomeAssistant

```bash
# Copy custom component
cp -r /home/user/llmvm/custom_components/llmvm_conversation \
      /path/to/homeassistant/config/custom_components/

# Restart HomeAssistant
# (Settings → System → Restart)
```

**Configure the integration:**
1. Settings → Devices & Services → Add Integration
2. Search "LLMVM Conversation Agent"
3. Configure:
   - LLMVM Server URL: `http://localhost:8011`
   - LLM Executor: `openai`
   - Model Name: `llama3:8b` (or leave empty)
   - Temperature: `0.7`
   - Max Tokens: `2000`

4. Settings → Voice Assistants → Your Assistant
   - Conversation Agent → "LLMVM Conversation Agent"

---

### Step 5: Add Timing Instrumentation

Now we instrument the code to measure latency.

#### 5a: Instrument HA Conversation Agent

Edit `/path/to/homeassistant/config/custom_components/llmvm_conversation/conversation.py`:

```python
"""LLMVM conversation agent for Home Assistant."""
from __future__ import annotations

import logging
import time  # ADD THIS
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
        # === TIMING: Start ===
        t_start = time.perf_counter()

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
            # === TIMING: Before LLMVM call ===
            t_before_llmvm = time.perf_counter()

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{llmvm_url}/v1/tools/completions",
                    json=request_data,
                )
                response.raise_for_status()
                result = response.json()

            # === TIMING: After LLMVM call ===
            t_after_llmvm = time.perf_counter()

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

            # === TIMING: End ===
            t_end = time.perf_counter()

            # === LOG METRICS ===
            agent_overhead = (t_before_llmvm - t_start) * 1000  # ms
            llmvm_latency = (t_after_llmvm - t_before_llmvm) * 1000  # ms
            response_overhead = (t_end - t_after_llmvm) * 1000  # ms
            total_latency = (t_end - t_start) * 1000  # ms

            _LOGGER.info(
                f"LLMVM_METRICS: conversation_id={conversation_id} "
                f"agent_overhead_ms={agent_overhead:.1f} "
                f"llmvm_latency_ms={llmvm_latency:.1f} "
                f"response_overhead_ms={response_overhead:.1f} "
                f"total_ms={total_latency:.1f} "
                f"input_text=\"{user_input.text}\" "
                f"response_len={len(response_text)}"
            )

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
```

**Restart HomeAssistant** after editing.

---

#### 5b: Instrument LLMVM Server

We need to add timing to the LLMVM server's execution controller.

Create a new file `/home/user/llmvm/llmvm/server/metrics.py`:

```python
"""Timing and metrics utilities for LLMVM."""
import time
import logging
from contextlib import contextmanager
from typing import Optional

logging = logging.getLogger(__name__)


class Metrics:
    """Simple metrics collector for request timing."""

    def __init__(self, request_id: str):
        self.request_id = request_id
        self.timings = {}
        self.start_time = time.perf_counter()

    @contextmanager
    def measure(self, stage: str):
        """Context manager to measure a stage."""
        stage_start = time.perf_counter()
        try:
            yield
        finally:
            stage_end = time.perf_counter()
            self.timings[stage] = (stage_end - stage_start) * 1000  # ms

    def log(self, logger: Optional[logging.Logger] = None):
        """Log all metrics."""
        total = (time.perf_counter() - self.start_time) * 1000

        metrics_str = " ".join([
            f"{k}={v:.1f}ms" for k, v in self.timings.items()
        ])

        msg = f"LLMVM_SERVER_METRICS: request_id={self.request_id} {metrics_str} total={total:.1f}ms"

        if logger:
            logger.info(msg)
        else:
            logging.info(msg)
```

Now edit `/home/user/llmvm/llmvm/server/server.py` to add metrics (I'll show you the key changes):

Find the `_tools_completions_generator` function and add timing:

```python
# Around line 470-480 in server.py
from llmvm.server.metrics import Metrics  # ADD THIS at top

# ... in _tools_completions_generator function ...

async def _tools_completions_generator(
    request: ToolCompletionRequest,
    stream_handler: Callable[[StreamNode], Awaitable],
    executor: Executor,
):
    # ADD: Create metrics
    import ulid
    request_id = str(ulid.ULID())
    metrics = Metrics(request_id)

    try:
        # ... existing code ...

        with metrics.measure("message_parsing"):
            messages = Helpers.parse_and_load_messages(
                executor_or_default,
                request.messages
            )

        # ... mode selection ...

        if mode == "direct":
            with metrics.measure("llm_direct"):
                result = await execution_controller.aexecute(...)
        else:
            with metrics.measure("llm_agent_total"):
                result = await execution_controller.aexecute_continuation(...)

        # ... rest of processing ...

    finally:
        # Log metrics at the end
        metrics.log(logging)
```

---

### Step 6: Enable HomeAssistant Detailed Logging

Edit `/path/to/homeassistant/config/configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    # LLMVM conversation agent metrics
    custom_components.llmvm_conversation: debug

    # HomeAssistant Assist pipeline metrics
    homeassistant.components.assist_pipeline: debug
    homeassistant.components.stt: debug
    homeassistant.components.tts: debug
    homeassistant.components.conversation: debug
```

**Restart HomeAssistant**

---

### Step 7: Test End-to-End

1. **Speak to your voice assistant** or use the Assist UI:
   - "Turn on the living room lights"
   - "What's the weather like?"
   - "What time is it?"

2. **Check logs:**

**HomeAssistant logs** (`/config/home-assistant.log`):
```bash
tail -f /config/home-assistant.log | grep "LLMVM_METRICS\|assist_pipeline"
```

You should see:
```
LLMVM_METRICS: conversation_id=abc123 agent_overhead_ms=5.2 llmvm_latency_ms=2450.3 response_overhead_ms=1.1 total_ms=2456.6 input_text="Turn on lights" response_len=45
```

**LLMVM server logs**:
```bash
tail -f ~/.local/share/llmvm/logs/server.log | grep "LLMVM_SERVER_METRICS"
```

You should see:
```
LLMVM_SERVER_METRICS: request_id=xyz789 message_parsing=12.3ms llm_agent_total=2380.5ms total=2395.1ms
```

---

### Step 8: Create Benchmarking Script

Create `/home/user/llmvm/scripts/analyze-metrics.py`:

```python
#!/usr/bin/env python3
"""Analyze LLMVM and HomeAssistant metrics from logs."""

import re
import sys
from collections import defaultdict
from pathlib import Path

def parse_ha_metrics(log_file):
    """Parse HomeAssistant LLMVM_METRICS logs."""
    pattern = r'LLMVM_METRICS:.*?agent_overhead_ms=([\d.]+).*?llmvm_latency_ms=([\d.]+).*?response_overhead_ms=([\d.]+).*?total_ms=([\d.]+)'

    metrics = []
    with open(log_file, 'r') as f:
        for line in f:
            if 'LLMVM_METRICS:' in line:
                match = re.search(pattern, line)
                if match:
                    metrics.append({
                        'agent_overhead': float(match.group(1)),
                        'llmvm_latency': float(match.group(2)),
                        'response_overhead': float(match.group(3)),
                        'total': float(match.group(4))
                    })
    return metrics

def parse_llmvm_metrics(log_file):
    """Parse LLMVM server metrics."""
    pattern = r'LLMVM_SERVER_METRICS:.*?llm_agent_total=([\d.]+)ms.*?total=([\d.]+)ms'

    metrics = []
    with open(log_file, 'r') as f:
        for line in f:
            if 'LLMVM_SERVER_METRICS:' in line:
                match = re.search(pattern, line)
                if match:
                    metrics.append({
                        'llm_agent': float(match.group(1)),
                        'total': float(match.group(2))
                    })
    return metrics

def analyze(metrics, label):
    """Print statistics."""
    if not metrics:
        print(f"\nNo {label} metrics found")
        return

    print(f"\n{label} Statistics ({len(metrics)} requests):")
    print("=" * 60)

    # Calculate stats for each metric
    for key in metrics[0].keys():
        values = [m[key] for m in metrics]
        avg = sum(values) / len(values)
        min_val = min(values)
        max_val = max(values)
        p50 = sorted(values)[len(values) // 2]
        p95 = sorted(values)[int(len(values) * 0.95)] if len(values) > 20 else max_val

        print(f"{key:20s}: avg={avg:7.1f}ms  p50={p50:7.1f}ms  p95={p95:7.1f}ms  min={min_val:7.1f}ms  max={max_val:7.1f}ms")

if __name__ == "__main__":
    ha_log = sys.argv[1] if len(sys.argv) > 1 else "/config/home-assistant.log"
    llmvm_log = sys.argv[2] if len(sys.argv) > 2 else str(Path.home() / ".local/share/llmvm/logs/server.log")

    print(f"Analyzing logs:")
    print(f"  HomeAssistant: {ha_log}")
    print(f"  LLMVM Server:  {llmvm_log}")

    ha_metrics = parse_ha_metrics(ha_log)
    llmvm_metrics = parse_llmvm_metrics(llmvm_log)

    analyze(ha_metrics, "HomeAssistant Agent")
    analyze(llmvm_metrics, "LLMVM Server")

    # Combined analysis
    if ha_metrics:
        print(f"\nBottleneck Analysis:")
        print("=" * 60)
        avg_agent = sum(m['agent_overhead'] for m in ha_metrics) / len(ha_metrics)
        avg_llmvm = sum(m['llmvm_latency'] for m in ha_metrics) / len(ha_metrics)
        avg_response = sum(m['response_overhead'] for m in ha_metrics) / len(ha_metrics)

        print(f"Agent Overhead:     {avg_agent:7.1f}ms  ({avg_agent/avg_llmvm*100:.1f}% of LLMVM time)")
        print(f"LLMVM Processing:   {avg_llmvm:7.1f}ms  (main bottleneck)")
        print(f"Response Overhead:  {avg_response:7.1f}ms  ({avg_response/avg_llmvm*100:.1f}% of LLMVM time)")
```

Make it executable:
```bash
chmod +x /home/user/llmvm/scripts/analyze-metrics.py
```

---

### Step 9: Run Benchmark Tests

Create a test script `/home/user/llmvm/scripts/benchmark-test.sh`:

```bash
#!/bin/bash
# Benchmark test script - sends test queries to HA

set -e

echo "🧪 Running benchmark tests..."
echo "Make sure HomeAssistant Assist is configured with LLMVM agent!"
echo ""

# Test queries (from simple to complex)
TEST_QUERIES=(
    "What time is it?"
    "Turn on the living room lights"
    "What's the weather forecast?"
    "Turn off all lights in the bedroom"
    "What's the temperature in the house?"
    "Set the thermostat to 72 degrees"
    "What's the current price of Tesla stock?"
    "Turn on the lights and check if it's going to rain tomorrow"
)

echo "Running ${#TEST_QUERIES[@]} test queries..."
echo ""

for i in "${!TEST_QUERIES[@]}"; do
    query="${TEST_QUERIES[$i]}"
    echo "[$((i+1))/${#TEST_QUERIES[@]}] Testing: \"$query\""

    # You'll need to trigger these manually via HA UI
    # OR use HA REST API if you set it up

    echo "  → Please say or type this in HA Assist UI"
    echo "  → Press Enter when done..."
    read
done

echo ""
echo "✅ Tests complete!"
echo ""
echo "📊 Analyze results:"
echo "  python3 /home/user/llmvm/scripts/analyze-metrics.py"
```

---

## Expected Output

After running tests, you should see metrics like:

```
HomeAssistant Agent Statistics (10 requests):
============================================================
agent_overhead      : avg=   5.2ms  p50=   4.8ms  p95=   7.1ms  min=   3.2ms  max=   8.9ms
llmvm_latency       : avg=2450.3ms  p50=2380.0ms  p95=3200.5ms  min=1850.2ms  max=4100.8ms
response_overhead   : avg=   1.1ms  p50=   0.9ms  p95=   1.5ms  min=   0.7ms  max=   2.1ms
total               : avg=2456.6ms  p50=2385.7ms  p95=3208.1ms  min=1854.1ms  max=4111.8ms

LLMVM Server Statistics (10 requests):
============================================================
llm_agent           : avg=2380.5ms  p50=2310.0ms  p95=3180.2ms  min=1820.5ms  max=4050.3ms
total               : avg=2395.1ms  p50=2324.6ms  p95=3195.8ms  min=1835.1ms  max=4065.9ms

Bottleneck Analysis:
============================================================
Agent Overhead:        5.2ms  (0.2% of LLMVM time)
LLMVM Processing:   2450.3ms  (main bottleneck)
Response Overhead:     1.1ms  (0.0% of LLMVM time)
```

**Interpretation:**
- **Agent overhead is negligible** (~5ms)
- **LLMVM is the bottleneck** (~2.5 seconds)
- This tells us Phase 2 should focus on LLM optimization

---

## Optimization Targets for Phase 2

Based on typical baselines, you should target:

| Component | Baseline (Phase 1) | Target (Phase 2) | Strategy |
|-----------|-------------------|------------------|----------|
| ASR | 200-500ms | 100-200ms | Optimize STT model |
| Agent Overhead | 5-10ms | <5ms | (already fast) |
| **LLM Inference** | **2000-4000ms** | **500-1000ms** | Faster model, disable thinking, NVFP4 |
| Tool Execution | 100-500ms | 50-200ms | Parallel tool calls |
| TTS | 200-500ms | 100-200ms | Optimize TTS model |
| **Total** | **2500-5500ms** | **750-1600ms** | **3-7x improvement** |

---

## Next Steps

Once you have Phase 1 metrics:

1. **Run analysis**: `python3 scripts/analyze-metrics.py`
2. **Identify bottleneck**: Is it LLM? Tool execution? ASR/TTS?
3. **Plan Phase 2**: Focus optimization where it matters most

Most likely Phase 2 priorities:
1. ✅ Switch from Ollama to TensorRT-LLM + NVFP4 (3-4x faster LLM)
2. ✅ Reduce tool discovery overhead (fewer tools in prompt)
3. ✅ Optimize thinking mode (system prompts)
4. ✅ Consider streaming for perceived latency

---

## Tool Discovery Optimization (Preview)

If tool discovery is slow (many tools in prompt), you can optimize by:

1. **Categorize tools** and only load relevant ones
2. **Use tool embeddings** to select subset
3. **Lazy load** tools on-demand
4. **Cache** tool descriptions

We'll implement this in Phase 2 based on data.

---

## Checklist

- [ ] Ollama installed and running
- [ ] LLMVM configured to use Ollama
- [ ] HomeAssistant MCP server running
- [ ] LLMVM discovers MCP tools
- [ ] HA conversation agent installed
- [ ] Timing instrumentation added to HA agent
- [ ] Metrics module created for LLMVM
- [ ] Logging enabled in HA configuration.yaml
- [ ] Analysis scripts created
- [ ] Run benchmark tests
- [ ] Analyze results
- [ ] Identify bottlenecks
- [ ] Ready for Phase 2!
