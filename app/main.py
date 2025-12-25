"""
OCR API Service - Main Application

A REST API service for Tesseract OCR with:
- API key authentication
- Rate limiting
- Multiple output formats
- Image preprocessing
- Batch processing
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .config import get_settings
from .ocr_engine import get_tesseract_version, get_available_languages
from .routes.ocr import router as ocr_router
from .routes.admin import router as admin_router


settings = get_settings()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="🔍 OCR API Service",
    description="""
## Tesseract OCR as a Service

A powerful REST API for extracting text from images using Tesseract OCR.

### Features
- 🖼️ **Multiple Image Formats** - PNG, JPEG, TIFF, BMP, and more
- 🌍 **100+ Languages** - Support for over 100 languages
- 🔐 **API Key Authentication** - Secure access with rate limiting
- ⚡ **Image Preprocessing** - Automatic enhancement for better accuracy
- 📦 **Batch Processing** - Process multiple images in one request
- 📊 **Multiple Output Formats** - Plain text, JSON with word data, hOCR

### Getting Started
1. Get your API key from the admin
2. Include `X-API-Key: your-key` header in all requests
3. Upload images to the `/ocr/extract` endpoint

### Authentication
All OCR endpoints require an API key. Include it in the request header:
```
X-API-Key: ocr_your_api_key_here
```
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ocr_router)
app.include_router(admin_router)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Homepage with API information."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR API</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --bg: #0a0a0a;
            --surface: #111111;
            --border: #1a1a1a;
            --text: #fafafa;
            --text-muted: #666666;
            --accent: #ffffff;
        }
        
        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: var(--bg);
            min-height: 100vh;
            color: var(--text);
            line-height: 1.6;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 80px 24px;
        }
        
        /* Header */
        .header {
            margin-bottom: 80px;
        }
        
        .logo {
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 0.1em;
            color: var(--text-muted);
            text-transform: uppercase;
            margin-bottom: 24px;
        }
        
        h1 {
            font-size: 48px;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin-bottom: 16px;
        }
        
        .subtitle {
            font-size: 18px;
            color: var(--text-muted);
            max-width: 500px;
        }
        
        /* Buttons */
        .actions {
            display: flex;
            gap: 12px;
            margin-top: 40px;
        }
        
        .btn {
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 500;
            text-decoration: none;
            border-radius: 6px;
            transition: all 0.15s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: var(--text);
            color: var(--bg);
        }
        
        .btn-primary:hover {
            opacity: 0.9;
            transform: translateY(-1px);
        }
        
        .btn-secondary {
            background: transparent;
            color: var(--text);
            border: 1px solid var(--border);
        }
        
        .btn-secondary:hover {
            border-color: #333;
            background: var(--surface);
        }
        
        /* Features */
        .features {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1px;
            background: var(--border);
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 60px;
        }
        
        .feature {
            background: var(--surface);
            padding: 32px;
        }
        
        .feature-icon {
            font-size: 24px;
            margin-bottom: 16px;
        }
        
        .feature h3 {
            font-size: 15px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .feature p {
            font-size: 14px;
            color: var(--text-muted);
            line-height: 1.5;
        }
        
        /* Code */
        .code-section {
            margin-bottom: 60px;
        }
        
        .code-label {
            font-size: 12px;
            font-weight: 500;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 12px;
        }
        
        .code-block {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            overflow-x: auto;
        }
        
        .code-block pre {
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            line-height: 1.7;
            color: #888;
        }
        
        .code-block .cmd { color: var(--text); }
        .code-block .flag { color: #666; }
        .code-block .str { color: #999; }
        
        /* Endpoints */
        .endpoints {
            margin-bottom: 60px;
        }
        
        .endpoint {
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 16px 0;
            border-bottom: 1px solid var(--border);
        }
        
        .endpoint:last-child {
            border-bottom: none;
        }
        
        .method {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 600;
            padding: 4px 8px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 4px;
            min-width: 50px;
            text-align: center;
        }
        
        .method.post { color: #4ade80; border-color: #14532d; }
        .method.get { color: #60a5fa; border-color: #1e3a5f; }
        
        .path {
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            color: var(--text);
        }
        
        .desc {
            font-size: 13px;
            color: var(--text-muted);
            margin-left: auto;
        }
        
        /* Footer */
        footer {
            padding-top: 40px;
            border-top: 1px solid var(--border);
            font-size: 13px;
            color: var(--text-muted);
            display: flex;
            justify-content: space-between;
        }
        
        footer a {
            color: var(--text-muted);
            text-decoration: none;
        }
        
        footer a:hover {
            color: var(--text);
        }
        
        @media (max-width: 640px) {
            h1 { font-size: 32px; }
            .features { grid-template-columns: 1fr; }
            .endpoint { flex-wrap: wrap; }
            .desc { margin-left: 66px; margin-top: 4px; }
            footer { flex-direction: column; gap: 8px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="logo">OCR API</div>
            <h1>Extract text from images</h1>
            <p class="subtitle">A fast, reliable OCR API powered by Tesseract. Process images and get back structured text data.</p>
            <div class="actions">
                <a href="/docs" class="btn btn-primary">Documentation</a>
                <a href="/redoc" class="btn btn-secondary">API Reference</a>
            </div>
        </header>
        
        <div class="features">
            <div class="feature">
                <div class="feature-icon">📄</div>
                <h3>Multiple Formats</h3>
                <p>PNG, JPEG, TIFF, BMP, WebP and more.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">🌍</div>
                <h3>100+ Languages</h3>
                <p>English, Chinese, Japanese, Arabic, and more.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">⚡</div>
                <h3>Fast Processing</h3>
                <p>Optimized preprocessing for accuracy.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">🔑</div>
                <h3>API Keys</h3>
                <p>Secure access with rate limiting.</p>
            </div>
        </div>
        
        <div class="code-section">
            <div class="code-label">Quick Start</div>
            <div class="code-block">
                <pre><span class="cmd">curl</span> <span class="flag">-X POST</span> <span class="str">"https://ocr.muazaoski.online/ocr/extract"</span> <span class="flag">\\</span>
  <span class="flag">-H</span> <span class="str">"X-API-Key: your_api_key"</span> <span class="flag">\\</span>
  <span class="flag">-F</span> <span class="str">"file=@image.png"</span></pre>
            </div>
        </div>
        
        <div class="endpoints">
            <div class="code-label">Endpoints</div>
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="path">/ocr/extract</span>
                <span class="desc">Extract text from image</span>
            </div>
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="path">/ocr/extract/detailed</span>
                <span class="desc">Get word positions</span>
            </div>
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="path">/ocr/batch</span>
                <span class="desc">Process multiple images</span>
            </div>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/ocr/languages</span>
                <span class="desc">List available languages</span>
            </div>
        </div>
        
        <footer>
            <span>OCR API v1.0.0</span>
            <a href="/health">Status</a>
        </footer>
    </div>
</body>
</html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        version = get_tesseract_version()
        languages = get_available_languages()
        
        return {
            "status": "healthy",
            "version": "1.0.0",
            "tesseract_version": version,
            "available_languages": languages
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.get("/info")
async def api_info():
    """Get API information."""
    return {
        "name": "OCR API Service",
        "version": "1.0.0",
        "description": "Tesseract OCR as a REST API",
        "tesseract_version": get_tesseract_version(),
        "endpoints": {
            "ocr": {
                "extract": "POST /ocr/extract - Extract text from image",
                "detailed": "POST /ocr/extract/detailed - Get word-level data",
                "hocr": "POST /ocr/extract/hocr - Get hOCR XML output",
                "batch": "POST /ocr/batch - Batch process images",
                "languages": "GET /ocr/languages - List available languages"
            },
            "admin": {
                "login": "POST /admin/login - Admin authentication",
                "keys": "GET/POST /admin/keys - Manage API keys",
                "stats": "GET /admin/stats - Usage statistics"
            }
        },
        "authentication": "Include X-API-Key header with all OCR requests"
    }
