#!/bin/bash
# =============================================================================
# Qwen3-VL-2B-Thinking Installation Script for VPS
# =============================================================================
# This script sets up the Qwen3-VL vision-language model on your VPS
# Run as root: sudo bash install_qwen_vl.sh
# =============================================================================

set -e  # Exit on error

echo "=========================================="
echo "🧠 Qwen3-VL-2B-Thinking Setup"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root: sudo bash $0"
    exit 1
fi

# Check available RAM
TOTAL_RAM=$(free -m | awk '/^Mem:/{print $2}')
echo "📊 Total RAM: ${TOTAL_RAM}MB"

if [ "$TOTAL_RAM" -lt 3500 ]; then
    echo "⚠️  Warning: Less than 4GB RAM detected. Model may not load properly."
    echo "   Consider using IQ2_XXS quantization or upgrading VPS."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Install build dependencies
echo ""
echo "📦 Step 1/5: Installing build dependencies..."
apt-get update
apt-get install -y build-essential cmake git curl wget

# Step 2: Build llama.cpp
echo ""
echo "🔧 Step 2/5: Building llama.cpp..."
if [ -d "/opt/llama.cpp" ]; then
    echo "   llama.cpp directory exists, updating..."
    cd /opt/llama.cpp
    git pull
else
    cd /opt
    git clone https://github.com/ggml-org/llama.cpp
    cd llama.cpp
fi

# Build with optimizations
make clean 2>/dev/null || true
make -j$(nproc) LLAMA_FAST=1

echo "   ✅ llama.cpp built successfully"

# Step 3: Download model files
echo ""
echo "📥 Step 3/5: Downloading Qwen3-VL-2B-Thinking model..."
mkdir -p /opt/models/qwen3-vl
cd /opt/models/qwen3-vl

# Model file (~1.5GB)
if [ ! -f "Qwen3-VL-2B-Thinking-Q4_K_M.gguf" ]; then
    echo "   Downloading model (Q4_K_M ~1.5GB)..."
    wget -c "https://huggingface.co/unsloth/Qwen3-VL-2B-Thinking-GGUF/resolve/main/Qwen3-VL-2B-Thinking-Q4_K_M.gguf"
else
    echo "   Model already downloaded"
fi

# Vision encoder (~500MB)
if [ ! -f "mmproj-Qwen3-VL-2B-Thinking-f16.gguf" ]; then
    echo "   Downloading vision encoder..."
    wget -c "https://huggingface.co/unsloth/Qwen3-VL-2B-Thinking-GGUF/resolve/main/mmproj-Qwen3-VL-2B-Thinking-f16.gguf"
else
    echo "   Vision encoder already downloaded"
fi

echo "   ✅ Model files downloaded"

# Step 4: Create systemd service
echo ""
echo "⚙️  Step 4/5: Creating systemd service..."
cat > /etc/systemd/system/qwen-vl.service << 'EOF'
[Unit]
Description=Qwen3-VL Vision Language Model Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/llama.cpp
ExecStart=/opt/llama.cpp/llama-server \
    -m /opt/models/qwen3-vl/Qwen3-VL-2B-Thinking-Q4_K_M.gguf \
    --mmproj /opt/models/qwen3-vl/mmproj-Qwen3-VL-2B-Thinking-f16.gguf \
    --host 127.0.0.1 \
    --port 8081 \
    -c 4096 \
    -ngl 0 \
    --threads 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "   ✅ Systemd service created"

# Step 5: Start the service
echo ""
echo "🚀 Step 5/5: Starting Qwen-VL service..."
systemctl enable qwen-vl
systemctl start qwen-vl

# Wait for startup
echo "   Waiting for service to start (this may take 30-60 seconds)..."
sleep 10

# Check status
if systemctl is-active --quiet qwen-vl; then
    echo "   ✅ Qwen-VL service is running!"
    
    # Test the API
    echo ""
    echo "🧪 Testing API..."
    sleep 5
    if curl -s http://localhost:8081/health > /dev/null 2>&1; then
        echo "   ✅ API is responding at http://localhost:8081"
    else
        echo "   ⚠️  API not responding yet. It may take a minute to fully load."
        echo "   Run: curl http://localhost:8081/health"
    fi
else
    echo "   ❌ Service failed to start. Check logs with:"
    echo "   journalctl -u qwen-vl -n 50"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "📋 Service Commands:"
echo "   Start:   systemctl start qwen-vl"
echo "   Stop:    systemctl stop qwen-vl"
echo "   Status:  systemctl status qwen-vl"
echo "   Logs:    journalctl -u qwen-vl -f"
echo ""
echo "🌐 API Endpoint:"
echo "   http://localhost:8081/v1/chat/completions"
echo ""
echo "🔧 Next Steps:"
echo "   1. Update your OCR API with the new code"
echo "   2. Rebuild: docker compose build --no-cache"
echo "   3. Restart: docker compose up -d"
echo "   4. Test: curl https://ocr.muazaoski.online/ocr/understand/status"
echo ""
