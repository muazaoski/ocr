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

# View logs
docker compose logs -f

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

## 🌐 URLs

- **Website:** https://ocr.muazaoski.online
- **API Docs:** https://ocr.muazaoski.online/docs
- **Health:** https://ocr.muazaoski.online/health

---

## 📁 File Locations

| Path | Purpose |
|------|---------|
| `/opt/apps/ocr/` | Main app directory |
| `/opt/apps/ocr/.env` | Environment (secrets) |
| `/opt/apps/ocr/Caddyfile` | Reverse proxy config |
| `/opt/apps/ocr/data/` | API keys (persistent) |

---

## Architecture

```
Traffic Flow:
User → Caddy (HTTPS:443) → OCR-API (Python:8000) → Tesseract
```

- **Caddy** - Reverse proxy with auto HTTPS
- **OCR-API** - FastAPI application
- **Tesseract** - OCR engine (installed in Docker)
