# 🧠 Qwen3-VL-2B-Thinking Setup Guide

## Overview

This adds AI-powered document understanding to your OCR API using the Qwen3-VL-2B-Thinking vision-language model.

**New Endpoint:** `POST /ocr/understand`
- Send an image → Get structured understanding (not just text extraction)
- Supports custom prompts for specific use cases
- 32 language OCR with blur/tilt tolerance

---

## Architecture

```
Current:
  Image → Tesseract (OCR) → Raw Text

New (with Qwen3-VL):
  Image → Qwen3-VL → Structured Understanding + Text
```

The system runs two services:
1. **ocr-api** (existing) - FastAPI with Tesseract
2. **qwen-vl** (new) - llama.cpp server with Qwen3-VL model

---

## VPS Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 4GB free | 6GB free |
| Disk | 5GB | 10GB |
| CPU | 2 cores | 4 cores |

---

## Setup Steps

### Step 1: Download Model Files (on VPS)

```bash
# Create models directory
mkdir -p /opt/models/qwen3-vl
cd /opt/models/qwen3-vl

# Download model (Q4_K_M - best balance)
wget https://huggingface.co/unsloth/Qwen3-VL-2B-Thinking-GGUF/resolve/main/Qwen3-VL-2B-Thinking-Q4_K_M.gguf

# Download vision encoder
wget https://huggingface.co/unsloth/Qwen3-VL-2B-Thinking-GGUF/resolve/main/mmproj-Qwen3-VL-2B-Thinking-f16.gguf
```

### Step 2: Install llama.cpp (on VPS)

```bash
# Install build dependencies
apt-get update && apt-get install -y build-essential cmake git

# Clone and build llama.cpp
cd /opt
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
make -j$(nproc)
```

### Step 3: Create Systemd Service

```bash
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
    -ngl 0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
systemctl daemon-reload
systemctl enable qwen-vl
systemctl start qwen-vl

# Check status
systemctl status qwen-vl
```

### Step 4: Verify It's Running

```bash
# Test the API
curl http://localhost:8081/health
```

---

## API Usage

### New Endpoint: POST /ocr/understand

**Request:**
```bash
curl -X POST "https://ocr.muazaoski.online/ocr/understand" \
  -H "X-API-Key: your-api-key" \
  -F "file=@size_chart.png" \
  -F "prompt=Extract all size measurements as JSON"
```

**Response:**
```json
{
  "result": {
    "sizes": ["S", "M", "L", "XL"],
    "measurements": {
      "chest": {"S": 36, "M": 38, "L": 40, "XL": 42},
      "waist": {"S": 28, "M": 30, "L": 32, "XL": 34}
    }
  },
  "processing_time_ms": 1234,
  "model": "qwen3-vl-2b-thinking"
}
```

---

## Troubleshooting

### Model won't load
- Check RAM: `free -h`
- Use smaller quantization: Q4_0 instead of Q4_K_M

### Slow inference
- Normal for CPU-only: ~10-30 seconds per image
- Consider adding GPU support

### Out of memory
- Reduce context: `-c 2048` instead of 4096
- Use IQ2_XXS quantization (~800MB)

---

## Files Added

- `app/routes/understand.py` - New API route
- `app/vlm_engine.py` - Qwen3-VL integration
- `QWEN_VL_SETUP.md` - This file
