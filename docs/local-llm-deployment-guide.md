# Local LLM Deployment Guide for DGX Spark (Blackwell)

## Executive Summary

For **DGX Spark with Blackwell GPUs**, use **TensorRT-LLM with NVFP4 quantization** for optimal performance.

**Performance targets:**
- 3-4x faster than previous gen (H200 FP8)
- 2.35x faster than INT4
- <1% accuracy loss
- >30,000 tokens/sec throughput

---

## Why NVFP4 on Blackwell?

### Format Comparison

| Format | Hardware Accelerated? | Speedup vs FP16 | Accuracy Loss | Blackwell Recommendation |
|--------|----------------------|-----------------|---------------|--------------------------|
| **NVFP4** | ✅ **Native (20 PFLOPS)** | **3-4x** | **<1%** | ✅ **Primary choice** |
| FP8 | ✅ Native | 2x | <1% | ⚠️ Fallback if NVFP4 issues |
| MXFP4 | ❌ Software | ~2x | ~10% | ❌ Worse than NVFP4 |
| INT4 | ❌ Needs dequant | ~1.3x | 2-3% | ❌ Slower, less accurate |

### NVFP4 Technical Details

**Format**: E2M1 (1 sign, 2 exponent, 1 mantissa)
**Scaling**: Dual-level (E4M3 micro-blocks + FP32 global)
**Block size**: 16 values (vs 32 for MXFP4)
**Hardware**: Fifth-gen Tensor Cores, 20 PetaFLOPS

**Key advantage**: Unlike INT4, NVFP4 operates directly on 4-bit values without dequantization overhead.

---

## Deployment Options

### Option 1: TensorRT-LLM (Recommended for Blackwell)

**Best for:**
- Maximum performance on Blackwell
- NVFP4 hardware acceleration
- Production deployments
- Sparse models (GPT-OSS, Qwen)

**Pros:**
- Native NVFP4 support
- 3-4x faster than H200 FP8
- Optimized for Blackwell architecture
- OpenAI-compatible API available

**Cons:**
- Complex setup (build step required)
- 10-30 min engine build time
- Less flexible than vLLM/SGLang

**Performance (GPT-OSS-120B on DGX B200 x8):**
- Single user: 150-200 tok/s
- 10 users: 1,200-1,500 tok/s
- Max throughput: >30,000 tok/s
- TTFT: 20-40ms

**Deployment:**
```bash
# Use our automated script
cd /home/user/llmvm/scripts
./deploy-tensorrt-nvfp4.sh

# Or manual deployment (see script for details)
```

---

### Option 2: vLLM with NVFP4 (Easier Alternative)

**Best for:**
- Faster iteration during development
- Easier model swapping
- High concurrency (>32 users)

**Pros:**
- Early NVFP4 support (as of v0.6.0+)
- OpenAI-compatible API built-in
- Easier setup than TensorRT-LLM
- Good prefix caching

**Cons:**
- NVFP4 support not as mature as TensorRT-LLM
- Slightly lower performance than TensorRT-LLM
- May not utilize all Blackwell optimizations

**Performance (estimated):**
- 80-90% of TensorRT-LLM performance
- Still 2-3x faster than H200 FP8

**Deployment:**
```bash
# Install vLLM with NVFP4 support
pip install vllm>=0.6.0

# Launch with NVFP4
python -m vllm.entrypoints.openai.api_server \
    --model openai/gpt-oss-120b \
    --quantization nvfp4 \
    --tensor-parallel-size 8 \
    --gpu-memory-utilization 0.9 \
    --host 0.0.0.0 \
    --port 8000 \
    --api-key your-secret-key
```

---

### Option 3: SGLang (Best for Sparse Models - No NVFP4 Yet)

**Best for:**
- Sparse models without quantization
- DeepSeek-like architectures
- When NVFP4 isn't available

**Pros:**
- Best performance for sparse MoE models (2x faster than vLLM)
- FP8 support
- Good for Qwen, DeepSeek

**Cons:**
- No NVFP4 support yet (coming soon per roadmap)
- Without NVFP4, slower than TensorRT-LLM on Blackwell

**When to use:**
- If you can't get TensorRT-LLM working
- If you need frequent model updates
- If FP8 performance is acceptable

**Deployment:**
```bash
# See scripts/deploy-sglang-dgx.sh
# Or manual:
python -m sglang.launch_server \
    --model-path openai/gpt-oss-120b \
    --tp 8 \
    --enable-fp8-weight \
    --port 8000
```

---

## Decision Matrix

| Scenario | Recommendation | Reason |
|----------|---------------|--------|
| **Production on Blackwell** | TensorRT-LLM + NVFP4 | Maximum performance, hardware-optimized |
| **Quick testing/dev** | vLLM + NVFP4 | Easier setup, good enough performance |
| **Sparse models (no quant)** | SGLang + FP8 | Best for MoE without NVFP4 |
| **High concurrency** | vLLM + NVFP4 | Better batching at >32 users |
| **H100/H200 GPUs** | SGLang + FP8 or vLLM + FP8 | No NVFP4 on non-Blackwell |

---

## Model-Specific Recommendations

### GPT-OSS-120B

**Primary: TensorRT-LLM + NVFP4**
- Expected: 150-200 tok/s single user
- Issue: Thinking mode cannot be fully disabled
- Workaround: System prompts + token limits (see deployment script)

**Alternative: Qwen2.5-72B**
- Native no-think mode support
- Faster than GPT-OSS (sparse architecture)
- Better for HomeAssistant use case

### Qwen 30B-3B Active

**Primary: TensorRT-LLM + NVFP4**
- Sparse model benefits from NVFP4
- Excellent for instruction following

**Alternative: SGLang + FP8**
- If TensorRT build issues
- Still good performance

### DeepSeek-R1 (If Considering)

**Primary: TensorRT-LLM + NVFP4**
- Record-breaking 43,144 tok/s with NVFP4
- 671B model runs at >30,000 tok/s on single DGX B200

---

## GPT-OSS Thinking Mode Mitigation

Since full disable isn't supported, use these strategies:

### 1. System Prompt (Most Effective)

```python
SYSTEM_PROMPT = """You are a smart home assistant.

CRITICAL INSTRUCTIONS:
1. Reasoning: disabled
2. Never show thinking or reasoning steps
3. Provide ONLY final answers
4. Be concise and direct

Example:
User: "Turn on lights"
Correct: [executes function]
Wrong: "Let me think about which lights..."
"""
```

### 2. API Parameters

```python
response = client.chat.completions.create(
    model="gpt-oss-120b",
    messages=[...],
    max_tokens=150,  # Limit prevents extended thinking
    temperature=0.3,  # Lower = less reasoning
    stop=["<|reasoning|>", "\nReasoning:", "\nThinking:"],
    extra_body={"reasoning_effort": "low"}  # If supported
)
```

### 3. Alternative Model

If thinking is still problematic, **use Qwen2.5-72B** instead:
- Native `--no-think` mode
- Faster than GPT-OSS for sparse workloads
- Better instruction following

---

## Performance Benchmarks

### Expected Performance on DGX Spark (8x B200)

#### GPT-OSS-120B + NVFP4

| Configuration | Tokens/Sec | Latency | Memory/GPU |
|---------------|------------|---------|------------|
| TensorRT-LLM | 150-200 (1 user) | 20-40ms | ~30GB |
| TensorRT-LLM | 1,200-1,500 (10 users) | 50-100ms | ~30GB |
| TensorRT-LLM | >30,000 (max) | Variable | ~30GB |
| vLLM + NVFP4 | 120-160 (1 user) | 30-50ms | ~30GB |
| SGLang + FP8 | 80-100 (1 user) | 40-60ms | ~60GB |

#### Qwen2.5-72B + NVFP4

| Configuration | Tokens/Sec | Latency | Memory/GPU |
|---------------|------------|---------|------------|
| TensorRT-LLM | 200-250 (1 user) | 15-30ms | ~20GB |
| TensorRT-LLM | 1,500-2,000 (10 users) | 40-80ms | ~20GB |
| vLLM + NVFP4 | 160-200 (1 user) | 20-40ms | ~20GB |

**Comparison to previous gen:**
- vs H200 FP8: **3-4x faster**
- vs INT4: **2.35x faster**
- Accuracy loss: **<1%** (typically 0.1-0.5%)

---

## Deployment Checklist

### Pre-deployment

- [ ] Verify Blackwell GPUs (B200/B100)
  ```bash
  nvidia-smi --query-gpu=name --format=csv,noheader
  ```

- [ ] Check NVLink connectivity
  ```bash
  nvidia-smi nvlink --status
  ```

- [ ] Ensure sufficient disk space (200GB+ for models)
  ```bash
  df -h
  ```

### Deployment

- [ ] Run TensorRT-LLM deployment script
  ```bash
  cd /home/user/llmvm/scripts
  ./deploy-tensorrt-nvfp4.sh
  ```

- [ ] Verify model quantization (check logs for accuracy metrics)

- [ ] Test server startup
  ```bash
  curl http://localhost:8000/v1/models
  ```

### Integration with LLMVM

- [ ] Update LLMVM config
  ```bash
  cat ./models/trt-nvfp4/llmvm-config.yaml >> ~/.config/llmvm/config.yaml
  ```

- [ ] Add thinking reduction system prompt (for GPT-OSS)

- [ ] Restart LLMVM server
  ```bash
  pkill -f llmvm-server
  llmvm-server &
  ```

- [ ] Test integration
  ```bash
  curl http://localhost:8011/health
  ```

### HomeAssistant Integration

- [ ] Ensure MCP server is running
  ```bash
  lsof -i :8765
  ```

- [ ] Verify LLMVM discovered MCP tools
  ```bash
  curl http://localhost:8011/helpers | grep homeassistant
  ```

- [ ] Test end-to-end
  - Ask in HA: "Turn on the living room lights"
  - Check logs for tool execution

---

## Troubleshooting

### NVFP4 Quantization Fails

**Symptom:** Error during model quantization
**Solutions:**
1. Ensure TensorRT Model Optimizer >= 0.25.0
   ```bash
   pip install --upgrade nvidia-modelopt
   ```

2. Try different calibration data (more diverse examples)

3. Fall back to FP8:
   ```bash
   --quantization fp8
   ```

### Engine Build Fails

**Symptom:** trtllm-build crashes or errors
**Solutions:**
1. Check CUDA version (12.4+ required)
   ```bash
   nvcc --version
   ```

2. Increase build timeout
   ```bash
   export TRTLLM_BUILD_TIMEOUT=7200  # 2 hours
   ```

3. Reduce batch size or sequence length in build config

### Low Performance

**Symptom:** Not achieving expected throughput
**Solutions:**
1. Verify NVFP4 is actually being used:
   ```bash
   nvidia-smi dmon -s u  # Check utilization
   ```

2. Check if Tensor Cores are active:
   ```bash
   nvidia-smi --query-gpu=utilization.memory --format=csv
   ```

3. Ensure NVLink is working:
   ```bash
   nvidia-smi nvlink --status
   ```

4. Try disabling radix cache (for diverse queries):
   ```python
   --disable-radix-cache
   ```

### GPT-OSS Still Showing Thinking

**Solutions:**
1. Use more aggressive system prompt (see examples)
2. Reduce max_tokens to 100-150
3. Add custom stop tokens: `["<|reasoning|>", "\nLet me think"]`
4. Consider switching to Qwen2.5-72B

---

## Performance Tuning

### For Low Latency (Single User)

```bash
trtllm-build \
    ... \
    --max_batch_size 16 \
    --max_num_tokens 2048 \
    --enable_chunked_prefill
```

### For High Throughput (Many Users)

```bash
trtllm-build \
    ... \
    --max_batch_size 512 \
    --max_num_tokens 65536 \
    --enable_chunked_prefill \
    --use_paged_context_fmha enable
```

### For HomeAssistant (Mixed Queries)

```bash
trtllm-build \
    ... \
    --max_batch_size 256 \
    --max_num_tokens 32768 \
    --enable_chunked_prefill \
    --disable_radix_cache  # Diverse queries don't benefit from prefix cache
```

---

## Cost Comparison

### Memory Usage

| Model | FP16 | FP8 | NVFP4 | Reduction |
|-------|------|-----|-------|-----------|
| GPT-OSS-120B | ~240GB | ~120GB | ~68GB | **3.5x** |
| Qwen2.5-72B | ~144GB | ~72GB | ~41GB | **3.5x** |

**Benefit:** Can fit larger models or higher batch sizes

### Power Consumption

NVFP4 on Blackwell:
- ~30% lower power vs FP8 on H200
- ~50% lower power vs FP16

---

## References

- [NVIDIA NVFP4 Technical Blog](https://developer.nvidia.com/blog/introducing-nvfp4-for-efficient-and-accurate-low-precision-inference/)
- [TensorRT-LLM NVFP4 Guide](https://github.com/NVIDIA/TensorRT-LLM)
- [TensorRT Model Optimizer](https://developer.nvidia.com/tensorrt-model-optimizer)
- [Blackwell Performance Benchmarks](https://developer.nvidia.com/blog/nvidia-blackwell-delivers-world-record-deepseek-r1-inference-performance/)

---

## Quick Start Command

For the impatient:

```bash
# Clone repo if needed
cd /home/user/llmvm

# Run automated deployment
./scripts/deploy-tensorrt-nvfp4.sh

# Update LLMVM config
cat ./models/trt-nvfp4/llmvm-config.yaml >> ~/.config/llmvm/config.yaml

# Launch server
./models/trt-nvfp4/launch_server.sh

# Test
curl http://localhost:8000/v1/models
```

Done! You now have hardware-accelerated NVFP4 inference on Blackwell. 🚀
