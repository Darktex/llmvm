#!/bin/bash
# SGLang Deployment Script for DGX Spark
# Optimized for sparse models (GPT-OSS, Qwen) with HomeAssistant integration

set -e

echo "🚀 SGLang Deployment for DGX Spark"
echo "=================================="

# Configuration
MODEL=${MODEL:-"Qwen/Qwen2.5-72B-Instruct"}  # Change to openai/gpt-oss-120b if desired
PORT=${PORT:-8000}
TP_SIZE=${TP_SIZE:-8}  # Tensor parallelism - adjust for your GPU count
API_KEY=${API_KEY:-$(openssl rand -hex 16)}  # Generate random API key if not provided
FP8=${FP8:-true}
NO_RADIX_CACHE=${NO_RADIX_CACHE:-true}  # Disable for diverse HA queries

echo "Configuration:"
echo "  Model: $MODEL"
echo "  Port: $PORT"
echo "  Tensor Parallelism: $TP_SIZE GPUs"
echo "  FP8 Quantization: $FP8"
echo "  API Key: $API_KEY"
echo ""

# Check if SGLang is installed
if ! python -c "import sglang" 2>/dev/null; then
    echo "📦 Installing SGLang..."
    pip install "sglang[all]" --upgrade
else
    echo "✅ SGLang already installed"
fi

# Check GPU availability
GPU_COUNT=$(nvidia-smi --list-gpus | wc -l)
echo "🎮 Detected $GPU_COUNT GPUs"

if [ $GPU_COUNT -lt $TP_SIZE ]; then
    echo "⚠️  Warning: Requested TP_SIZE=$TP_SIZE but only $GPU_COUNT GPUs available"
    echo "   Adjusting TP_SIZE to $GPU_COUNT"
    TP_SIZE=$GPU_COUNT
fi

# Build command
CMD="python -m sglang.launch_server"
CMD="$CMD --model-path $MODEL"
CMD="$CMD --host 0.0.0.0"
CMD="$CMD --port $PORT"
CMD="$CMD --tp $TP_SIZE"
CMD="$CMD --mem-fraction-static 0.9"
CMD="$CMD --context-length 32768"
CMD="$CMD --api-key $API_KEY"

# Add FP8 quantization if enabled
if [ "$FP8" = "true" ]; then
    CMD="$CMD --enable-fp8-weight"
    echo "✅ FP8 quantization enabled"
fi

# Disable radix cache for diverse queries (better for HA)
if [ "$NO_RADIX_CACHE" = "true" ]; then
    CMD="$CMD --disable-radix-cache"
    echo "✅ Radix cache disabled (better for diverse HA queries)"
fi

# Add model-specific optimizations
if [[ $MODEL == *"gpt-oss"* ]]; then
    echo "🤖 GPT-OSS detected - applying thinking reduction"
    SYSTEM_PROMPT="You are a helpful assistant for smart home control. CRITICAL: Do not show reasoning or thinking steps. Provide only direct, concise answers. Reasoning: disabled."
    CMD="$CMD --system-prompt \"$SYSTEM_PROMPT\""
    CMD="$CMD --served-model-name gpt-oss-120b"
elif [[ $MODEL == *"Qwen"* ]]; then
    echo "🤖 Qwen detected - optimized for instruction following"
    CMD="$CMD --served-model-name qwen-72b"
fi

# Create systemd service file
cat > /tmp/sglang.service << EOF
[Unit]
Description=SGLang Inference Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME
Environment="PATH=$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
Environment="CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7"
Environment="SGLANG_API_KEY=$API_KEY"
ExecStart=$CMD
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=sglang

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "📄 Systemd service file created at /tmp/sglang.service"
echo "   To install: sudo cp /tmp/sglang.service /etc/systemd/system/"
echo "   Then: sudo systemctl enable sglang && sudo systemctl start sglang"
echo ""

# Save LLMVM config snippet
cat > /tmp/llmvm-sglang-config.yaml << EOF
# Add this to ~/.config/llmvm/config.yaml
executor: 'openai'
openai_api_base: 'http://localhost:$PORT/v1'
default_openai_model: '$(basename $MODEL)'

# Optional: Set API key if using authentication
# environment:
#   OPENAI_API_KEY: '$API_KEY'
EOF

echo "📄 LLMVM config snippet saved to /tmp/llmvm-sglang-config.yaml"
echo ""

# Ask user how to proceed
echo "How would you like to proceed?"
echo "  1) Run SGLang now (foreground)"
echo "  2) Run SGLang in background (nohup)"
echo "  3) Install as systemd service (requires sudo)"
echo "  4) Show command and exit"
read -p "Choice [1-4]: " choice

case $choice in
    1)
        echo ""
        echo "🚀 Starting SGLang in foreground..."
        echo "Press Ctrl+C to stop"
        echo ""
        eval $CMD
        ;;
    2)
        echo ""
        echo "🚀 Starting SGLang in background..."
        nohup $CMD > sglang.log 2>&1 &
        PID=$!
        echo "✅ SGLang started with PID: $PID"
        echo "   Logs: tail -f sglang.log"
        echo "   Stop: kill $PID"
        echo ""
        sleep 5
        echo "📊 Checking server health..."
        curl -s http://localhost:$PORT/health || echo "⚠️  Server not responding yet (may still be loading model)"
        ;;
    3)
        echo ""
        echo "🔧 Installing systemd service..."
        sudo cp /tmp/sglang.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable sglang
        sudo systemctl start sglang
        echo "✅ Service installed and started"
        echo "   Status: sudo systemctl status sglang"
        echo "   Logs: sudo journalctl -u sglang -f"
        ;;
    4)
        echo ""
        echo "Command to run SGLang:"
        echo ""
        echo "$CMD"
        echo ""
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "📚 Next Steps:"
echo "  1. Update LLMVM config: cat /tmp/llmvm-sglang-config.yaml >> ~/.config/llmvm/config.yaml"
echo "  2. Test the API: curl http://localhost:$PORT/v1/models"
echo "  3. Restart LLMVM server if already running"
echo ""
echo "🔑 API Key: $API_KEY"
echo "   (Save this - you'll need it for LLMVM config)"
echo ""
echo "✅ Deployment complete!"
