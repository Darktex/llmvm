# Ollama Integration for LLMVM

LLMVM now supports [Ollama](https://ollama.ai), allowing you to run local language models with full tool calling capabilities using LLMVM's `<helpers>` block pattern.

## What is Ollama?

Ollama is a tool for running large language models locally. It provides:
- Easy installation and model management
- OpenAI-compatible API
- Support for many popular models (Llama, Mistral, Qwen, Gemma, etc.)
- Low-latency local inference
- No API costs or rate limits

## Installation

### 1. Install Ollama

Download and install Ollama from [https://ollama.ai/download](https://ollama.ai/download)

Or use package managers:

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download the installer from [https://ollama.ai/download](https://ollama.ai/download)

### 2. Start Ollama Server

```bash
ollama serve
```

The server will start on `http://localhost:11434`

### 3. Pull a Model

For tool calling and code generation, we recommend models that support function calling:

```bash
# Llama 3.1 (8B) - Good balance of speed and quality
ollama pull llama3.1

# Qwen 2.5 (7B) - Excellent for code generation
ollama pull qwen2.5

# Mistral (7B) - Fast and capable
ollama pull mistral

# Check available models
ollama list
```

## Configuration

### Environment Variables

Set the executor to use Ollama:

```bash
export LLMVM_EXECUTOR='ollama'
export LLMVM_MODEL='llama3.1'
```

Optional configuration:

```bash
# If Ollama is running on a different host/port
export OLLAMA_API_BASE='http://192.168.1.100:11434/v1'

# Override token limits
export LLMVM_OVERRIDE_MAX_INPUT_TOKENS=128000
export LLMVM_OVERRIDE_MAX_OUTPUT_TOKENS=4096
```

### Config File

Alternatively, edit `~/.config/llmvm/config.yaml`:

```yaml
executor: 'ollama'
default_ollama_model: 'llama3.1'
ollama_api_base: 'http://localhost:11434/v1'
```

## Usage

### Basic Conversation

```bash
# Start LLMVM client with Ollama
LLMVM_EXECUTOR="ollama" LLMVM_MODEL="llama3.1" python -m llmvm.client

query>> Hello! What can you help me with?
```

### With Server (for Tool Support)

Start the LLMVM server:

```bash
LLMVM_EXECUTOR="ollama" LLMVM_MODEL="llama3.1" python -m llmvm.server
```

In another terminal, start the client:

```bash
LLMVM_EXECUTOR="ollama" LLMVM_MODEL="llama3.1" python -m llmvm.client
```

### Tool Calling Example

The key feature of Ollama integration is support for LLMVM's `<helpers>` blocks:

```bash
query>> I have 5 MSFT stocks and 10 NVDA stocks, what is my net worth in grams of gold?
```

The model will generate code like:

```python
<helpers>
msft_price = get_stock_price("MSFT")
nvda_price = get_stock_price("NVDA")

total_value = (5 * msft_price) + (10 * nvda_price)

gold_price_per_gram = get_gold_silver_price_in_usd()["gold"]["price"] / 31.1035

net_worth_in_gold = total_value / gold_price_per_gram

result(f"Your portfolio is worth {net_worth_in_gold:.2f} grams of gold")
</helpers>
```

The LLMVM server executes this code and returns results in `<helpers_result>` blocks.

### Shell Alias

Create convenient aliases in your `.bashrc` or `.zshrc`:

```bash
alias ollama-llama="LLMVM_EXECUTOR=ollama LLMVM_MODEL=llama3.1 python -m llmvm.client"
alias ollama-qwen="LLMVM_EXECUTOR=ollama LLMVM_MODEL=qwen2.5 python -m llmvm.client"
alias ollama-mistral="LLMVM_EXECUTOR=ollama LLMVM_MODEL=mistral python -m llmvm.client"
```

Then use:

```bash
cat code.py | ollama-qwen "explain this code and suggest improvements"
```

## Model Recommendations

Different Ollama models have different strengths:

| Model | Size | Context Window | Best For | Tool Calling |
|-------|------|----------------|----------|--------------|
| llama3.1 | 8B | 128k | General purpose, balanced | ✅ Excellent |
| qwen2.5 | 7B | 128k | Code generation, math | ✅ Excellent |
| mistral | 7B | 32k | Fast inference, general | ✅ Good |
| gemma2 | 9B | 8k | Efficient, good quality | ⚠️ Limited |
| llama2 | 7B | 4k | Legacy support | ❌ Poor |

For LLMVM tool calling, **llama3.1** or **qwen2.5** are recommended.

## Testing

Run the comprehensive test suite:

```bash
# Test both conversation and tool calling
python scripts/test_ollama.py

# Test specific model
python scripts/test_ollama.py --model qwen2.5

# Test only conversation mode
python scripts/test_ollama.py --conversation

# Test only tool calling
python scripts/test_ollama.py --tools
```

## Performance Tips

### 1. GPU Acceleration

Ollama automatically uses GPU if available (CUDA or Metal). Check GPU usage:

```bash
# During inference, check GPU utilization
nvidia-smi  # NVIDIA GPUs
```

### 2. Model Quantization

Ollama models are typically quantized (4-bit or 8-bit). For better quality at the cost of memory:

```bash
# Pull larger quantization
ollama pull llama3.1:70b  # 70B parameter version
ollama pull qwen2.5:32b   # 32B parameter version
```

### 3. Concurrent Requests

Ollama supports concurrent requests. You can run multiple LLMVM clients against the same Ollama server.

### 4. Context Length

Large context windows consume more memory. For long documents:

```bash
# Use models with larger context windows
ollama pull llama3.1  # 128k context
```

## Troubleshooting

### Connection Issues

**Problem:** `Cannot connect to Ollama`

**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it
ollama serve
```

### Model Not Found

**Problem:** `Model 'llama3.1' not found`

**Solution:**
```bash
# Pull the model
ollama pull llama3.1

# List available models
ollama list
```

### Poor Tool Calling

**Problem:** Model doesn't generate `<helpers>` blocks

**Solution:**
- Try llama3.1 or qwen2.5 (best for code generation)
- Ensure you're using the LLMVM server (not direct client)
- Check the system prompt is being applied
- Lower temperature (0.3-0.5) for more deterministic output

### Out of Memory

**Problem:** Ollama crashes or runs very slowly

**Solution:**
```bash
# Use smaller models
ollama pull llama3.1:8b    # Instead of :70b

# Or quantized versions
ollama pull qwen2.5:4bit   # Smaller memory footprint
```

### Slow Inference

**Problem:** Responses are very slow

**Solution:**
- Check GPU is being used: `nvidia-smi` or Activity Monitor
- Use smaller models or quantized versions
- Reduce max_output_tokens in config
- Close other GPU-intensive applications

## Advanced Configuration

### Custom Ollama Endpoint

If running Ollama on a different machine:

```bash
OLLAMA_API_BASE='http://192.168.1.100:11434/v1' \
LLMVM_EXECUTOR='ollama' \
LLMVM_MODEL='llama3.1' \
python -m llmvm.client
```

### Token Limits

Override default token limits:

```yaml
# ~/.config/llmvm/config.yaml
executor: 'ollama'
default_ollama_model: 'llama3.1'
override_max_input_tokens: 128000
override_max_output_tokens: 8192
```

### Multiple Ollama Instances

Run different models on different ports:

```bash
# Terminal 1: Llama for general queries
OLLAMA_HOST=0.0.0.0:11434 ollama serve

# Terminal 2: Qwen for code generation
OLLAMA_HOST=0.0.0.0:11435 ollama serve
```

Then configure LLMVM to use specific endpoints.

## Comparison with Cloud Models

| Feature | Ollama | OpenAI/Anthropic |
|---------|--------|------------------|
| Cost | Free (hardware only) | Pay per token |
| Privacy | Fully local | Data sent to cloud |
| Latency | Low (local) | Higher (network) |
| Model Quality | Good (8B-70B models) | Excellent (175B+ models) |
| Setup | Requires local GPU | Just API key |
| Rate Limits | None | Yes |
| Context Window | Up to 128k | Up to 200k+ |

Ollama is ideal for:
- Privacy-sensitive applications
- Development and testing
- High-volume usage
- Offline environments
- Cost-sensitive projects

Cloud models are better for:
- Maximum quality
- No local hardware
- Very long contexts
- Specialized tasks

## Examples

### Code Analysis

```bash
query>> -p src/**/*.py "analyze this codebase and find potential bugs"
```

### Document Processing

```bash
query>> -p document.pdf "summarize this document and extract key points"
```

### Data Analysis

```bash
query>> I have sales data: Q1=$100k, Q2=$150k, Q3=$120k, Q4=$180k. Calculate growth rate and create a visualization.
```

### Web Scraping

```bash
query>> Go to https://news.ycombinator.com and get the top 10 stories
```

## Contributing

To improve Ollama support:

1. Test with different models and report compatibility
2. Submit issues for model-specific quirks
3. Contribute prompt improvements for better tool calling
4. Share performance optimizations

## Resources

- [Ollama Official Docs](https://github.com/ollama/ollama)
- [Ollama Model Library](https://ollama.ai/library)
- [LLMVM GitHub](https://github.com/9600dev/llmvm)
- [OpenAI Compatibility](https://ollama.com/blog/openai-compatibility)

## License

This integration follows the same license as LLMVM.
