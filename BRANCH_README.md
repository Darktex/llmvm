# Recovery Branch: ollama-qwen3-working

## Overview
This branch represents the last known working state of LLMVM with Home Assistant Assist integration.

## Details
- **Commit**: fc48b6d ("Works!")
- **Date**: December 30, 2025
- **Created By**: Recovery operation after TensorRT migration issues

## Why This Branch Exists
The TensorRT migration work broke the Home Assistant Assist integration. While attempting to migrate from Ollama to TensorRT-LLM for better performance with Nemotron-3-Nano, the integration started returning boilerplate "Yes, I am ready" responses to all queries instead of properly processing them.

This branch preserves the working state before those changes were made.

## What Works in This Branch
- **Inference Server**: Ollama
- **Model**: qwen3-coder:30b-ctx (Qwen3-Coder with custom 256k context)
- **Home Assistant Integration**: Fully functional Assist conversation agent
- **LLMVM Server**: Properly processes requests from HA Assist
- **Tools/Helpers**: Python-based helpers with HomeAssistant API integration
- **Latency**: ~5-6 seconds when called directly from LLMVM client

## TensorRT Migration Work
The work done for TensorRT migration has been preserved in a stash.
This stash can be reviewed and cherry-picked once the integration issues are understood and resolved.

## Environment Configuration
When running this branch, use these environment variables:
```bash
HA_URL="http://192.168.0.201:8123/api"
HA_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI4YmIzNTdkOGJkYTY0M2VkYmMzZWRiMzg0ZDhiOWJmNSIsImlhdCI6MTc2Mzk0MTk1MiwiZXhwIjoyMDc5MzAxOTUyfQ.np4ye5JHZiYwEk0DlqYqUYPvYmqDnpLyf-4YEd7_ztk"
LLMVM_EXECUTOR="ollama"
LLMVM_MODEL="qwen3-coder:30b-ctx"
LLMVM_PROFILING="true"
LLMVM_EXECUTOR_TRACE="~/tmp/llmvm_executor.trace"
```

Or use the alias:
```bash
start_llmvm_server
```

## Next Steps
1. Verify this branch works with Home Assistant Assist
2. Identify what specific changes in the TensorRT migration broke the integration
3. Apply fixes incrementally while testing HA Assist functionality
4. Once stable, migrate the working fixes to a new branch

## Notes
- Ollama container should be running on port 11434 (default)
- Ensure the qwen3-coder:30b-ctx model is available in Ollama
- The Home Assistant custom component should match this version
