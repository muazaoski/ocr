"""
Vision Language Model Engine using Qwen3-VL-2B-Thinking.
Provides document understanding capabilities via local llama.cpp server.
"""
import base64
import time
import httpx
from typing import Optional
import os

from .config import get_settings

settings = get_settings()

# VLM Server configuration
VLM_SERVER_URL = os.getenv("VLM_SERVER_URL", "http://127.0.0.1:8081")
VLM_TIMEOUT = int(os.getenv("VLM_TIMEOUT", "120"))  # 2 minutes for CPU inference


def get_vlm_status() -> dict:
    """Check if the VLM server is running and healthy."""
    try:
        response = httpx.get(f"{VLM_SERVER_URL}/health", timeout=5.0)
        if response.status_code == 200:
            return {"status": "healthy", "server": VLM_SERVER_URL}
        return {"status": "unhealthy", "error": f"Status code: {response.status_code}"}
    except Exception as e:
        return {"status": "offline", "error": str(e)}


def image_to_base64(image_bytes: bytes) -> str:
    """Convert image bytes to base64 data URL."""
    base64_data = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/png;base64,{base64_data}"


async def understand_image(
    image_bytes: bytes,
    prompt: str = "Extract all text and data from this image. Return as structured JSON.",
    temperature: float = 0.7,
    max_tokens: int = 2048
) -> dict:
    """
    Send an image to Qwen3-VL for understanding.
    
    Args:
        image_bytes: Raw image bytes
        prompt: Custom prompt for the model
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens to generate
    
    Returns:
        dict with result and metadata
    """
    start_time = time.time()
    
    # Check server health first
    status = get_vlm_status()
    if status["status"] != "healthy":
        raise ConnectionError(f"VLM server not available: {status.get('error', 'Unknown error')}")
    
    # Convert image to base64
    image_url = image_to_base64(image_bytes)
    
    # Build the request payload (OpenAI-compatible format)
    payload = {
        "model": "qwen3-vl",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=VLM_TIMEOUT) as client:
            response = await client.post(
                f"{VLM_SERVER_URL}/v1/chat/completions",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException:
        raise TimeoutError(f"VLM request timed out after {VLM_TIMEOUT} seconds")
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"VLM server error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        raise RuntimeError(f"VLM request failed: {str(e)}")
    
    processing_time = (time.time() - start_time) * 1000
    
    # Extract the response content
    content = ""
    if "choices" in data and len(data["choices"]) > 0:
        message = data["choices"][0].get("message", {})
        content = message.get("content", "")
    
    return {
        "result": content,
        "processing_time_ms": processing_time,
        "model": "qwen3-vl-2b-thinking",
        "tokens_used": data.get("usage", {})
    }


# Preset prompts for common use cases
PROMPT_PRESETS = {
    "size_chart": """Analyze this size chart image and extract all data as JSON.
Return format:
{
    "sizes": ["S", "M", "L", ...],
    "measurements": {
        "measurement_name": {"size": value, ...}
    },
    "notes": "any additional notes"
}""",
    
    "invoice": """Extract all data from this invoice as JSON.
Return format:
{
    "vendor": "company name",
    "date": "YYYY-MM-DD",
    "invoice_number": "...",
    "items": [{"description": "...", "quantity": N, "price": N}],
    "subtotal": N,
    "tax": N,
    "total": N
}""",
    
    "receipt": """Extract all data from this receipt as JSON.
Return format:
{
    "store": "store name",
    "date": "YYYY-MM-DD",
    "items": [{"name": "...", "price": N}],
    "subtotal": N,
    "tax": N,
    "total": N,
    "payment_method": "..."
}""",
    
    "business_card": """Extract contact information from this business card as JSON.
Return format:
{
    "name": "...",
    "title": "...",
    "company": "...",
    "email": "...",
    "phone": "...",
    "address": "...",
    "website": "..."
}""",
    
    "table": """Extract all tabular data from this image as JSON.
Return format:
{
    "headers": ["col1", "col2", ...],
    "rows": [["val1", "val2", ...], ...]
}""",
    
    "general": "Extract all text and data from this image. Describe what you see and provide any structured data you can identify."
}


def get_preset_prompt(preset: str) -> str:
    """Get a preset prompt by name."""
    return PROMPT_PRESETS.get(preset, PROMPT_PRESETS["general"])
