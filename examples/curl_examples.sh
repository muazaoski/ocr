#!/bin/bash
# Example: Using the OCR API with cURL

API_URL="http://localhost:8000"
API_KEY="ocr_your_api_key_here"

# ============================================================================
# Admin Operations
# ============================================================================

# Login as admin (get access token)
echo "🔐 Admin Login..."
TOKEN=$(curl -s -X POST "$API_URL/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}' \
  | jq -r '.access_token')
echo "   Token: ${TOKEN:0:20}..."

# Create a new API key
echo -e "\n🔑 Creating API Key..."
curl -s -X POST "$API_URL/admin/keys" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Application",
    "rate_limit_per_minute": 60,
    "rate_limit_per_day": 1000
  }' | jq

# List all API keys
echo -e "\n📋 List API Keys..."
curl -s -X GET "$API_URL/admin/keys" \
  -H "Authorization: Bearer $TOKEN" | jq

# Get usage statistics
echo -e "\n📊 Usage Stats..."
curl -s -X GET "$API_URL/admin/stats" \
  -H "Authorization: Bearer $TOKEN" | jq

# ============================================================================
# OCR Operations (requires API Key)
# ============================================================================

# Health check (no auth required)
echo -e "\n🏥 Health Check..."
curl -s "$API_URL/health" | jq

# Extract text from image
echo -e "\n📝 Extract Text..."
curl -s -X POST "$API_URL/ocr/extract" \
  -H "X-API-Key: $API_KEY" \
  -F "file=@image.png" | jq

# Extract with options
echo -e "\n📝 Extract (French, no preprocessing)..."
curl -s -X POST "$API_URL/ocr/extract?language=fra&preprocess=false" \
  -H "X-API-Key: $API_KEY" \
  -F "file=@french_doc.png" | jq

# Get detailed results with word positions
echo -e "\n📊 Detailed Extraction..."
curl -s -X POST "$API_URL/ocr/extract/detailed" \
  -H "X-API-Key: $API_KEY" \
  -F "file=@image.png" | jq

# Get hOCR output
echo -e "\n📄 hOCR Output..."
curl -s -X POST "$API_URL/ocr/extract/hocr" \
  -H "X-API-Key: $API_KEY" \
  -F "file=@image.png" > output.hocr
echo "   Saved to output.hocr"

# Batch processing
echo -e "\n📦 Batch Processing..."
curl -s -X POST "$API_URL/ocr/batch" \
  -H "X-API-Key: $API_KEY" \
  -F "files=@image1.png" \
  -F "files=@image2.png" \
  -F "files=@image3.png" | jq

# Get available languages
echo -e "\n🌍 Available Languages..."
curl -s -X GET "$API_URL/ocr/languages" \
  -H "X-API-Key: $API_KEY" | jq
