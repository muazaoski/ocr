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
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from .config import get_settings
from .limiter import limiter
from .ocr_engine import get_tesseract_version, get_available_languages
from .routes.ocr import router as ocr_router
from .routes.admin import router as admin_router
from .routes.understand import router as understand_router


settings = get_settings()

# Rate limiter is now in .limiter module

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
app.include_router(understand_router)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Homepage with interactive OCR playground."""
    from .api_keys import get_or_create_demo_key
    demo_key = get_or_create_demo_key()
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR API | Premium Extraction</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        :root {{
            --bg: #000000;
            --surface: #111111;
            --surface-hover: #161616;
            --border: #222222;
            --text: #fafafa;
            --text-muted: #888888;
            --accent: #4ade80; /* Neon Green */
            --accent-soft: rgba(74, 222, 128, 0.1);
        }}
        
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background: var(--bg);
            min-height: 100vh;
            color: var(--text);
            line-height: 1.6;
            overflow-x: hidden;
        }}

        /* Subtle background glow */
        body::before {{
            content: '';
            position: fixed;
            top: -10%;
            left: -10%;
            width: 40%;
            height: 40%;
            background: radial-gradient(circle, rgba(74, 222, 128, 0.05) 0%, transparent 70%);
            z-index: -1;
            pointer-events: none;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            padding: 80px 24px;
        }}
        
        /* Header */
        .header {{
            text-align: center;
            margin-bottom: 80px;
        }}
        
        .badge {{
            display: inline-block;
            padding: 6px 12px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--accent);
            margin-bottom: 24px;
        }}
        
        h1 {{
            font-size: clamp(40px, 8vw, 64px);
            font-weight: 800;
            letter-spacing: -0.04em;
            margin-bottom: 20px;
            background: linear-gradient(to bottom, #fff 0%, #888 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .subtitle {{
            font-size: 18px;
            color: var(--text-muted);
            max-width: 600px;
            margin: 0 auto 40px;
        }}
        
        /* Playground Section */
        .playground {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 32px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
            margin-bottom: 80px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 32px;
        }}

        @media (max-width: 850px) {{
            .playground {{ grid-template-columns: 1fr; }}
        }}
        
        .dropzone {{
            border: 2px dashed var(--border);
            border-radius: 16px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 300px;
            background: rgba(255,255,255,0.02);
            position: relative;
            overflow: hidden;
        }}
        
        .dropzone:hover, .dropzone.dragover {{
            border-color: var(--accent);
            background: var(--accent-soft);
        }}

        .dropzone img {{
            max-width: 100%;
            max-height: 250px;
            border-radius: 8px;
            display: none;
            margin-bottom: 16px;
        }}
        
        .dropzone-icon {{
            font-size: 32px;
            margin-bottom: 16px;
            opacity: 0.5;
        }}

        /* Result Panel */
        .result-panel {{
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        .panel-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .panel-title {{
            font-size: 14px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .result-box {{
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            flex-grow: 1;
            min-height: 250px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            color: #ccc;
            white-space: pre-wrap;
            overflow-y: auto;
            position: relative;
        }}

        .result-box:empty::before {{
            content: 'Extracted text will appear here...';
            color: var(--text-muted);
            opacity: 0.5;
        }}

        /* Buttons */
        .btn {{
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
            text-decoration: none;
            border-radius: 8px;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            border: none;
            font-family: inherit;
        }}
        
        .btn-primary {{
            background: var(--accent);
            color: #000;
            width: 100%;
            justify-content: center;
        }}
        
        .btn-primary:hover {{
            box-shadow: 0 0 20px rgba(74, 222, 128, 0.3);
            transform: translateY(-1px);
        }}

        .btn-primary:disabled {{
            background: var(--border);
            color: var(--text-muted);
            cursor: not-allowed;
            box-shadow: none;
            transform: none;
        }}

        .copy-btn {{
            background: var(--surface-hover);
            color: var(--text);
            padding: 4px 8px;
            font-size: 11px;
            border: 1px solid var(--border);
            border-radius: 4px;
        }}
        
        /* Features Grid */
        .features {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 24px;
            margin-bottom: 80px;
        }}
        
        .feature-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            padding: 24px;
            border-radius: 16px;
            transition: all 0.2s ease;
        }}
        
        .feature-card:hover {{
            background: var(--surface-hover);
            border-color: #333;
            transform: translateY(-4px);
        }}
        
        .f-icon {{ font-size: 24px; margin-bottom: 16px; display: block; }}
        .f-title {{ font-size: 15px; font-weight: 600; margin-bottom: 8px; }}
        .f-desc {{ font-size: 13px; color: var(--text-muted); }}
        
        /* Loading Overlay */
        .loader {{
            display: none;
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.7);
            backdrop-filter: blur(4px);
            z-index: 10;
            align-items: center;
            justify-content: center;
            border-radius: 16px;
        }}

        .spinner {{
            width: 40px; height: 40px;
            border: 3px solid rgba(255,255,255,0.1);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }}

        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}

        /* Footer */
        footer {{
            padding-top: 40px;
            border-top: 1px solid var(--border);
            font-size: 13px;
            color: var(--text-muted);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .status-dot {{
            display: inline-block;
            width: 8px; height: 8px;
            background: var(--accent);
            border-radius: 50%;
            margin-right: 6px;
            box-shadow: 0 0 5px var(--accent);
        }}
        
        a {{ color: inherit; text-decoration: none; }}
        a:hover {{ color: var(--text); }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <span class="badge">v1.0.0 is live</span>
            <h1>OCR API Service</h1>
            <p class="subtitle">A powerful, developer-first REST API for high-accuracy text extraction. No setup, no overhead, just speed.</p>
            <div style="display: flex; gap: 12px; justify-content: center;">
                <a href="/docs" class="btn btn-secondary" style="background:var(--surface); border:1px solid var(--border)">Documentation</a>
                <a href="#playground" class="btn btn-secondary" style="background:var(--surface); border:1px solid var(--border)">API Explorer</a>
            </div>
        </header>

        <section id="playground" class="playground">
            <div style="position: relative;">
                <div id="loader" class="loader"><div class="spinner"></div></div>
                <div id="dropzone" class="dropzone">
                    <img id="preview" src="" alt="Preview">
                    <div id="dz-content">
                        <div class="dropzone-icon">📥</div>
                        <div class="f-title">Drop your image here</div>
                        <div class="f-desc">PNG, JPG, WebP (Max 10MB)</div>
                    </div>
                </div>
                <input type="file" id="fileInput" hidden accept="image/*">
                <div style="margin-top: 20px; display: flex; gap: 12px;">
                    <select id="langSelect" style="flex: 1; background: var(--surface); border: 1px solid var(--border); color: #ccc; border-radius: 8px; padding: 10px; font-family: inherit;">
                        <option value="eng">English (eng)</option>
                        <option value="ind">Indonesian (ind)</option>
                        <option value="fra">French (fra)</option>
                        <option value="deu">German (deu)</option>
                        <option value="spa">Spanish (spa)</option>
                        <option value="chi_sim">Chinese Simp (chi_sim)</option>
                        <option value="ara">Arabic (ara)</option>
                    </select>
                    <select id="psmSelect" style="flex: 1; background: var(--surface); border: 1px solid var(--border); color: #ccc; border-radius: 8px; padding: 10px; font-family: inherit;">
                        <option value="3">Auto (Default)</option>
                        <option value="6">Uniform Block (Table)</option>
                        <option value="4">Columns (Table)</option>
                        <option value="11">Sparse Text</option>
                        <option value="7">Single Line</option>
                    </select>
                </div>
                <div style="margin-top: 12px;">
                    <button id="extractBtn" class="btn btn-primary" disabled>Extract Text</button>
                </div>
            </div>

            <div class="result-panel">
                <div class="panel-header">
                    <span class="panel-title">Output</span>
                    <button id="copyBtn" class="copy-btn" style="display:none">Copy</button>
                </div>
                <div id="resultBox" class="result-box"></div>
            </div>
        </section>
        
        <div class="features">
            <div class="feature-card">
                <span class="f-icon">⚡</span>
                <span class="f-title">Real-time Speed</span>
                <span class="f-desc">Optimized C++ backend with Tesseract 5 for industry-leading speed.</span>
            </div>
            <div class="feature-card">
                <span class="f-icon">🧠</span>
                <span class="f-title">AI Preprocessing</span>
                <span class="f-desc">Automatic contrast scaling and sharpening before processing.</span>
            </div>
            <div class="feature-card">
                <span class="f-icon">🌐</span>
                <span class="f-title">100+ Languages</span>
                <span class="f-desc">Universal support for UTF-8 characters and multi-language scripts.</span>
            </div>
            <div class="feature-card">
                <span class="f-icon">🛡️</span>
                <span class="f-title">Secure & Private</span>
                <span class="f-desc">No images are permanently stored. Processed and purged instantly.</span>
            </div>
        </div>
        
        <footer>
            <div style="display:flex; align-items:center;">
                <span class="status-dot"></span>
                <span>System Operational</span>
            </div>
            <div>
                <a href="/docs" style="margin-right: 20px;">API Keys</a>
                <a href="/health">Health Status</a>
            </div>
        </footer>
    </div>

    <script>
        const dropzone = document.getElementById('dropzone');
        const fileInput = document.getElementById('fileInput');
        const preview = document.getElementById('preview');
        const dzContent = document.getElementById('dz-content');
        const extractBtn = document.getElementById('extractBtn');
        const resultBox = document.getElementById('resultBox');
        const loader = document.getElementById('loader');
        const copyBtn = document.getElementById('copyBtn');
        const langSelect = document.getElementById('langSelect');
        const psmSelect = document.getElementById('psmSelect');
        
        let selectedFile = null;

        // Interaction
        dropzone.addEventListener('click', () => fileInput.click());
        
        dropzone.addEventListener('dragover', (e) => {{
            e.preventDefault();
            dropzone.classList.add('dragover');
        }});
        
        dropzone.addEventListener('dragleave', () => {{
            dropzone.classList.remove('dragover');
        }});
        
        dropzone.addEventListener('drop', (e) => {{
            e.preventDefault();
            dropzone.classList.remove('dragover');
            if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
        }});
        
        fileInput.addEventListener('change', (e) => {{
            if (e.target.files.length) handleFile(e.target.files[0]);
        }});

        function handleFile(file) {{
            if (!file.type.startsWith('image/')) return alert('Please upload an image.');
            
            selectedFile = file;
            const reader = new FileReader();
            reader.onload = (e) => {{
                preview.src = e.target.result;
                preview.style.display = 'block';
                dzContent.style.display = 'none';
                extractBtn.disabled = false;
            }};
            reader.readAsDataURL(file);
        }}

        extractBtn.addEventListener('click', async () => {{
            if (!selectedFile) return;
            
            loader.style.display = 'flex';
            extractBtn.disabled = true;
            resultBox.textContent = '';
            copyBtn.style.display = 'none';

            const formData = new FormData();
            formData.append('file', selectedFile);
            
            try {{
                const psm = psmSelect.value;
                const response = await fetch(`/ocr/extract?language=${{langSelect.value}}&psm=${{psm}}`, {{
                    method: 'POST',
                    headers: {{ 'X-API-Key': '{demo_key}' }},
                    body: formData
                }});
                
                const data = await response.json();
                
                if (response.ok) {{
                    resultBox.textContent = data.text || 'No text found in image.';
                    copyBtn.style.display = 'block';
                }} else {{
                    resultBox.style.color = '#ff4444';
                    resultBox.textContent = data.detail || 'Error processing image.';
                }}
            }} catch (err) {{
                resultBox.style.color = '#ff4444';
                resultBox.textContent = 'Network error or server unavailable.';
            }} finally {{
                loader.style.display = 'none';
                extractBtn.disabled = false;
            }}
        }});

        copyBtn.addEventListener('click', () => {{
            navigator.clipboard.writeText(resultBox.textContent);
            copyBtn.textContent = 'Copied!';
            setTimeout(() => {{ copyBtn.textContent = 'Copy'; }}, 2000);
        }});
    </script>
</body>
</html>
    """



@app.get(f"/{settings.admin_path}", response_class=HTMLResponse)
async def admin_dashboard():
    """Admin dashboard for managing API keys."""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR Admin | Control Center</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{
            --bg: #000;
            --surface: #111;
            --border: #222;
            --text: #fff;
            --text-muted: #888;
            --accent: #4ade80;
            --danger: #f87171;
        }}
        body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }}
        .container {{ max-width: 1000px; margin: 0 auto; padding: 40px 24px; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px; }}
        h1 {{ font-size: 24px; font-weight: 700; letter-spacing: -0.02em; }}
        
        /* Stats Grid */
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 40px; }}
        .stat-card {{ background: var(--surface); border: 1px solid var(--border); padding: 20px; border-radius: 12px; }}
        .stat-label {{ font-size: 12px; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px; }}
        .stat-value {{ font-size: 24px; font-weight: 700; }}

        /* Login Overlay */
        #loginOverlay {{ position: fixed; inset: 0; background: #000; z-index: 100; display: flex; align-items: center; justify-content: center; }}
        .login-box {{ background: var(--surface); border: 1px solid var(--border); padding: 32px; border-radius: 16px; width: 340px; }}
        input {{ width: 100%; background: #000; border: 1px solid var(--border); padding: 12px; border-radius: 8px; color: #fff; margin-bottom: 12px; font-family: inherit; }}
        button {{ width: 100%; padding: 12px; border-radius: 8px; font-weight: 600; cursor: pointer; border: none; font-family: inherit; transition: 0.2s; }}
        .btn-primary {{ background: #fff; color: #000; }}
        .btn-primary:hover {{ opacity: 0.9; }}
        .btn-danger {{ background: transparent; border: 1px solid #442222; color: var(--danger); }}
        .btn-danger:hover {{ background: #442222; }}

        /* Table */
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px; }}
        th {{ text-align: left; color: var(--text-muted); padding: 12px; border-bottom: 1px solid var(--border); font-weight: 500; }}
        td {{ padding: 16px 12px; border-bottom: 1px solid var(--border); }}
        .key-row:hover {{ background: rgba(255,255,255,0.02); }}
        .tag {{ font-family: 'JetBrains Mono'; font-size: 12px; background: #222; padding: 2px 6px; border-radius: 4px; }}

        /* Create Modal */
        #createModal {{ position: fixed; inset: 0; background: rgba(0,0,0,0.8); z-index: 50; display: none; align-items: center; justify-content: center; }}
        .modal-content {{ background: var(--surface); border: 1px solid var(--border); padding: 32px; border-radius: 16px; width: 400px; }}
    </style>
</head>
<body>
    <div id="loginOverlay">
        <div class="login-box">
            <h2 style="margin-bottom: 24px; text-align: center">Admin Login</h2>
            <input type="text" id="adminUser" placeholder="Username">
            <input type="password" id="adminPass" placeholder="Password">
            <button onclick="login()" class="btn-primary">Login</button>
            <p id="loginError" style="color: var(--danger); font-size: 12px; margin-top: 12px; text-align: center"></p>
        </div>
    </div>

    <div class="container">
        <header class="header">
            <div>
                <h1>Admin Dashboard</h1>
                <p style="color: var(--text-muted); font-size: 14px">Manage API access and usage</p>
            </div>
            <button onclick="showCreateModal()" class="btn-primary" style="width: auto">Create New Key</button>
        </header>

        <div class="stats" id="statsGrid">
            <div class="stat-card"><div class="stat-label">Total Keys</div><div class="stat-value" id="stat-keys">-</div></div>
            <div class="stat-card"><div class="stat-label">Active Keys</div><div class="stat-value" id="stat-active">-</div></div>
            <div class="stat-card"><div class="stat-label">Requests (24h)</div><div class="stat-value" id="stat-today">-</div></div>
        </div>

        <div id="keyListContent">
            <table id="keyTable">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Key Identifier</th>
                        <th>Created</th>
                        <th>Usage</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody id="keyBody"></tbody>
            </table>
        </div>
    </div>

    <div id="createModal">
        <div class="modal-content">
            <h2 style="margin-bottom: 20px">New API Key</h2>
            <input type="text" id="newKeyName" placeholder="Key Name (e.g. My Website)">
            <input type="number" id="newKeyMinute" placeholder="Limit per min (default 60)" value="60">
            <input type="number" id="newKeyDay" placeholder="Limit per day (default 1000)" value="1000">
            <div style="display:flex; gap: 12px; margin-top: 20px">
                <button onclick="closeCreateModal()" class="btn-primary" style="background:#222; color:#fff">Cancel</button>
                <button onclick="createKey()" class="btn-primary" style="background:var(--accent); color:#000">Create</button>
            </div>
        </div>
    </div>

    <script>
        let adminToken = '';
        const apiPath = '/{settings.admin_path}';

        async function login() {{
            const username = document.getElementById('adminUser').value;
            const password = document.getElementById('adminPass').value;
            try {{
                const res = await fetch(`${{apiPath}}/login`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ username, password }})
                }});
                const data = await res.json();
                if (res.ok) {{
                    adminToken = data.access_token;
                    document.getElementById('loginOverlay').style.display = 'none';
                    loadData();
                }} else {{
                    document.getElementById('loginError').textContent = data.detail;
                }}
            }} catch (e) {{ console.error(e); }}
        }}

        async function loadData() {{
            try {{
                const [statsRes, keysRes] = await Promise.all([
                    fetch(`${{apiPath}}/stats`, {{ headers: {{ 'Authorization': `Bearer ${{adminToken}}` }} }}),
                    fetch(`${{apiPath}}/keys`, {{ headers: {{ 'Authorization': `Bearer ${{adminToken}}` }} }})
                ]);
                const stats = await statsRes.json();
                const keys = await keysRes.json();

                document.getElementById('stat-keys').textContent = stats.total_api_keys;
                document.getElementById('stat-active').textContent = stats.active_api_keys;
                document.getElementById('stat-today').textContent = stats.total_requests_today;

                const body = document.getElementById('keyBody');
                body.innerHTML = '';
                keys.forEach(k => {{
                    const row = document.createElement('tr');
                    row.className = 'key-row';
                    row.innerHTML = `
                        <td>${{k.name}}</td>
                        <td class="tag">${{k.id}}</td>
                        <td style="color:var(--text-muted)">${{new Date(k.created_at).toLocaleDateString()}}</td>
                        <td>${{k.total_requests}} reqs</td>
                        <td>
                            <button onclick="deleteKey('${{k.id}}')" class="btn-danger" style="padding: 4px 10px; font-size: 11px; width:auto">Delete</button>
                        </td>
                    `;
                    body.appendChild(row);
                }});
            }} catch (e) {{ console.error(e); }}
        }}

        function showCreateModal() {{ document.getElementById('createModal').style.display = 'flex'; }}
        function closeCreateModal() {{ document.getElementById('createModal').style.display = 'none'; }}

        async function createKey() {{
            const name = document.getElementById('newKeyName').value;
            const res = await fetch(`${{apiPath}}/keys`, {{
                method: 'POST',
                headers: {{ 
                    'Authorization': `Bearer ${{adminToken}}`,
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify({{
                    name,
                    rate_limit_per_minute: parseInt(document.getElementById('newKeyMinute').value),
                    rate_limit_per_day: parseInt(document.getElementById('newKeyDay').value)
                }})
            }});
            const data = await res.json();
            if (res.ok) {{
                alert('Key created! COPY THIS NOW:\\n' + data.key);
                closeCreateModal();
                loadData();
            }}
        }}

        async function deleteKey(id) {{
            if (!confirm('Permanently delete this key?')) return;
            await fetch(`${{apiPath}}/keys/${{id}}`, {{
                method: 'DELETE',
                headers: {{ 'Authorization': `Bearer ${{adminToken}}` }}
            }});
            loadData();
        }}
    </script>
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
