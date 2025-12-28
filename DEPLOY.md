# 🔍 OCR API - VPS Deployment Guide

## VPS Details
- **IP:** 51.79.161.63
- **User:** debian
- **OS:** Debian 12 + Docker
- **Domain:** ocr.muazaoski.online
- **App Directory:** /opt/apps/ocr

---

## 🚀 First Time Deployment

### Step 1: Configure DNS (Cloudflare)

Add this DNS record:

| Type | Name | Content | Proxy Status |
|------|------|---------|--------------|
| A | ocr | 51.79.161.63 | **DNS only** (gray cloud) |

### Step 2: Connect to VPS

```bash
ssh debian@51.79.161.63
sudo -i
```

### Step 3: Clone Repository

```bash
mkdir -p /opt/apps
cd /opt/apps
git clone https://github.com/muazaoski/ocr.git
cd ocr
```

### Step 4: Configure Environment

```bash
# Create production .env
cat > .env << 'EOF'
SECRET_KEY=your-super-secret-random-string-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password-here
EOF
```

### Step 5: Build and Run

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f
```

### Step 6: Update Main Caddyfile
Add this to your main Caddyfile at `/opt/apps/caddy/Caddyfile` (or wherever your main Caddy config is):

```caddy
ocr.muazaoski.online {
    reverse_proxy localhost:8000
}
```

Then restart Caddy:
```bash
docker exec -it caddy caddy reload
```

---

## 📋 Quick Deploy (After Code Changes)

### On Your Local Machine (Windows):

```powershell
git add .
git commit -m "Update OCR API"
git push
```

### On Your VPS:

```bash
ssh debian@51.79.161.63
sudo -i
cd /opt/apps/ocr

# Pull and rebuild
git fetch origin
git reset --hard origin/main
docker compose down
docker compose build --no-cache
docker compose up -d

# Check logs
docker compose logs -f
```

---

## 🔑 Creating API Keys

Once deployed, create API keys:

```bash
# From VPS or any machine with curl

# 1. Login as admin
TOKEN=$(curl -s -X POST "https://ocr.muazaoski.online/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}' | jq -r '.access_token')

# 2. Create API key
curl -X POST "https://ocr.muazaoski.online/admin/keys" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "User1", "rate_limit_per_minute": 60, "rate_limit_per_day": 1000}'
```

---

## 📊 Testing OCR

```bash
# Test with an image
curl -X POST "https://ocr.muazaoski.online/ocr/extract" \
  -H "X-API-Key: ocr_your_api_key_here" \
  -F "file=@test.png"
```

---

## 🛠 Common Commands

```bash
# View running containers
docker compose ps

# View OCR API logs (real-time)
docker compose logs -f ocr-api

# View last 50 lines
docker compose logs --tail=50 ocr-api

# Restart
docker compose restart

# Stop
docker compose down

# Rebuild
docker compose build --no-cache
docker compose up -d

# Nuclear option
docker compose down
docker system prune -af
docker compose up -d --build
```

---

## 🧠 AI Understanding (Qwen3-VL)

The OCR API includes AI-powered document understanding using **Qwen3VL-2B-Instruct**.

### Qwen-VL Service Commands

```bash
# Check status
systemctl status qwen-vl

# View logs (real-time)
journalctl -u qwen-vl -f

# View last 100 lines
journalctl -u qwen-vl -n 100

# Restart Qwen-VL
systemctl restart qwen-vl

# Stop Qwen-VL
systemctl stop qwen-vl

# Start Qwen-VL
systemctl start qwen-vl
```

### Test AI Understanding

```bash
# Check VLM status
curl -H "X-API-Key: ocr_demo_key_public_feel_free_to_use" \
  https://ocr.muazaoski.online/ocr/understand/status

# Test with an image
curl -X POST "https://ocr.muazaoski.online/ocr/understand" \
  -H "X-API-Key: ocr_demo_key_public_feel_free_to_use" \
  -F "file=@receipt.png" \
  -F "prompt=Extract all data from this receipt"
```

### Qwen-VL File Locations

| Path | Purpose |
|------|---------|
| `/opt/llama.cpp/build/bin/llama-server` | VLM Server binary |
| `/opt/models/qwen3-vl/` | Model files |
| `/etc/systemd/system/qwen-vl.service` | Systemd service |

---

## 📊 View All Logs (Both Services)

```bash
# Terminal 1: OCR API logs
docker compose logs -f ocr-api

# Terminal 2: Qwen-VL logs
journalctl -u qwen-vl -f
```

---

## 🌐 URLs

- **Website:** https://ocr.muazaoski.online
- **API Docs:** https://ocr.muazaoski.online/docs
- **Health:** https://ocr.muazaoski.online/health
- **VLM Status:** https://ocr.muazaoski.online/ocr/understand/status

---

## 📁 File Locations

| Path | Purpose |
|------|---------|
| `/opt/apps/ocr/` | Main app directory |
| `/opt/apps/ocr/.env` | Environment (secrets) |
| `/opt/apps/ocr/data/` | API keys (persistent) |
| `/opt/models/qwen3-vl/` | AI model files |

---

## Architecture

```
Traffic Flow:

Basic OCR:
User → Caddy (HTTPS:443) → OCR-API (Python:8000) → Tesseract

AI Understanding:
User → Caddy (HTTPS:443) → OCR-API (Python:8000) → Qwen-VL (llama.cpp:8081)
```

### Components

| Service | Port | Purpose |
|---------|------|---------|
| **Caddy** | 443 | Reverse proxy with auto HTTPS |
| **OCR-API** | 8000 | FastAPI application |
| **Tesseract** | - | OCR engine (in Docker) |
| **Qwen-VL** | 8081 | Vision-language AI model |

