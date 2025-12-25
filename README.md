# 🔍 OCR API Service

A powerful, self-hosted REST API for Tesseract OCR with API key authentication, rate limiting, and multiple output formats.

## ✨ Features

- 🖼️ **Multiple Image Formats** - PNG, JPEG, TIFF, BMP, GIF, WebP
- 🌍 **100+ Languages** - English, French, German, Chinese, Japanese, Arabic, and more
- 🔐 **API Key Authentication** - Secure access with usage tracking
- ⏱️ **Rate Limiting** - Per-minute and daily request limits
- ⚡ **Image Preprocessing** - Automatic enhancement for better accuracy
- 📦 **Batch Processing** - Process up to 10 images in one request
- 📊 **Multiple Output Formats** - Plain text, JSON with word positions, hOCR XML
- 🐳 **Docker Ready** - Easy deployment on any VPS

## 🚀 Quick Start

### Option 1: Docker (Recommended for VPS)

```bash
# Clone the repository
git clone <your-repo-url>
cd OCR

# Configure environment
cp .env.example .env
# Edit .env and set your SECRET_KEY and ADMIN_PASSWORD

# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

### Option 2: Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install Tesseract OCR
# Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-eng
# macOS: brew install tesseract
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

# Configure environment
cp .env.example .env

# Run the server
python run.py
```

The API will be available at `http://localhost:8000`

## 📖 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔑 API Key Management

### 1. Admin Login

```bash
curl -X POST "http://localhost:8000/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-admin-password"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### 2. Create API Key

```bash
curl -X POST "http://localhost:8000/admin/keys" \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My App",
    "rate_limit_per_minute": 60,
    "rate_limit_per_day": 1000
  }'
```

Response:
```json
{
  "id": "abc123",
  "name": "My App",
  "key": "ocr_aBcDeFgHiJkLmNoPqRsTuVwXyZ...",  // SAVE THIS! Only shown once!
  "created_at": "2024-12-25T00:00:00Z",
  "is_active": true,
  "rate_limit_per_minute": 60,
  "rate_limit_per_day": 1000,
  "total_requests": 0
}
```

⚠️ **Important**: The API key is only returned during creation. Store it securely!

## 🖼️ OCR Endpoints

### Extract Text

```bash
curl -X POST "http://localhost:8000/ocr/extract" \
  -H "X-API-Key: ocr_your_api_key_here" \
  -F "file=@image.png"
```

Response:
```json
{
  "text": "Hello, World! This is extracted text.",
  "confidence": 95.5,
  "processing_time_ms": 234.5,
  "language": "eng"
}
```

### Extract with Options

```bash
curl -X POST "http://localhost:8000/ocr/extract?language=fra&psm=6&preprocess=true" \
  -H "X-API-Key: ocr_your_api_key_here" \
  -F "file=@french_document.png"
```

### Get Detailed Results (Word Positions)

```bash
curl -X POST "http://localhost:8000/ocr/extract/detailed" \
  -H "X-API-Key: ocr_your_api_key_here" \
  -F "file=@image.png"
```

Response:
```json
{
  "text": "Hello World",
  "confidence": 95.0,
  "processing_time_ms": 250.0,
  "language": "eng",
  "words": [
    {
      "text": "Hello",
      "confidence": 96.0,
      "left": 10,
      "top": 20,
      "width": 50,
      "height": 18
    },
    {
      "text": "World",
      "confidence": 94.0,
      "left": 70,
      "top": 20,
      "width": 48,
      "height": 18
    }
  ],
  "line_count": 1,
  "word_count": 2
}
```

### Batch Processing

```bash
curl -X POST "http://localhost:8000/ocr/batch" \
  -H "X-API-Key: ocr_your_api_key_here" \
  -F "files=@image1.png" \
  -F "files=@image2.jpg" \
  -F "files=@image3.jpeg"
```

## 🔧 Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `DEBUG` | `false` | Enable debug mode |
| `SECRET_KEY` | (required) | JWT signing key |
| `ADMIN_USERNAME` | `admin` | Admin username |
| `ADMIN_PASSWORD` | (required) | Admin password |
| `RATE_LIMIT_PER_MINUTE` | `60` | Default rate limit |
| `RATE_LIMIT_PER_DAY` | `1000` | Default daily limit |
| `MAX_FILE_SIZE_MB` | `10` | Max upload size |

## 📊 Page Segmentation Modes (PSM)

| Mode | Description |
|------|-------------|
| 0 | Orientation and script detection only |
| 1 | Automatic page segmentation with OSD |
| 3 | Fully automatic page segmentation (default) |
| 4 | Assume single column of text |
| 6 | Assume single uniform block of text |
| 7 | Treat image as single text line |
| 8 | Treat image as single word |
| 11 | Sparse text - find as much text as possible |
| 13 | Raw line - treat as single text line |

## 🌍 Supported Languages

The Docker image includes:
- `eng` - English
- `fra` - French
- `deu` - German
- `spa` - Spanish
- `ita` - Italian
- `por` - Portuguese
- `nld` - Dutch
- `pol` - Polish
- `rus` - Russian
- `jpn` - Japanese
- `chi_sim` - Chinese Simplified
- `chi_tra` - Chinese Traditional
- `kor` - Korean
- `ara` - Arabic

## 🔒 Security Considerations

1. **Change default credentials** - Update `SECRET_KEY` and `ADMIN_PASSWORD` in `.env`
2. **Use HTTPS** - Deploy behind a reverse proxy (nginx, Caddy, Traefik) with SSL
3. **Restrict CORS** - Update `allow_origins` in `app/main.py` for production
4. **Monitor usage** - Use `/admin/stats` to track API usage

## 📁 Project Structure

```
OCR/
├── app/
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── main.py             # FastAPI application
│   ├── models.py           # Pydantic schemas
│   ├── api_keys.py         # API key management
│   ├── auth.py             # Authentication utilities
│   ├── ocr_engine.py       # Tesseract wrapper
│   └── routes/
│       ├── __init__.py
│       ├── ocr.py          # OCR endpoints
│       └── admin.py        # Admin endpoints
├── data/                   # Persistent data (API keys)
├── .env.example           # Environment template
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker image
├── docker-compose.yml    # Docker Compose config
└── run.py               # Server entry point
```

## 📝 License

MIT License - feel free to use and modify!
