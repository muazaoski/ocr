"""
Vision Language Model Engine using Qwen3VL-2B-Instruct.
Provides document understanding capabilities via local llama.cpp server.
Supports parallel processing with configurable concurrency limits.
"""
import asyncio
import base64
import time
import httpx
import io
from typing import Optional, List
import os
from PIL import Image

from .config import get_settings

settings = get_settings()

# VLM Server configuration
VLM_SERVER_URL = os.getenv("VLM_SERVER_URL", "http://127.0.0.1:8081")
VLM_TIMEOUT = int(os.getenv("VLM_TIMEOUT", "300"))  # 5 minutes for CPU inference
VLM_MAX_CONCURRENT = int(os.getenv("VLM_MAX_CONCURRENT", "2"))  # Max parallel VLM requests

# Maximum image dimension for VLM processing (reduces encoding time)
MAX_IMAGE_SIZE = 512  # Smaller = faster encoding on CPU

# Global semaphore for limiting concurrent VLM requests
_vlm_semaphore: Optional[asyncio.Semaphore] = None

def get_vlm_semaphore() -> asyncio.Semaphore:
    """Get or create the VLM semaphore for concurrency control."""
    global _vlm_semaphore
    if _vlm_semaphore is None:
        _vlm_semaphore = asyncio.Semaphore(VLM_MAX_CONCURRENT)
    return _vlm_semaphore


def resize_image_for_vlm(image_bytes: bytes) -> bytes:
    """
    Resize image to reduce VLM processing time.
    Large images can take 3+ minutes to encode on CPU.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        
        # Get original size
        width, height = img.size
        
        # Skip if already small enough
        if width <= MAX_IMAGE_SIZE and height <= MAX_IMAGE_SIZE:
            return image_bytes
        
        # Calculate new size maintaining aspect ratio
        ratio = min(MAX_IMAGE_SIZE / width, MAX_IMAGE_SIZE / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        # Resize with high quality
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to bytes
        buffer = io.BytesIO()
        # Save as JPEG for smaller size, PNG for quality
        img_resized.save(buffer, format="JPEG", quality=85)
        
        return buffer.getvalue()
    except Exception as e:
        # If resize fails, return original
        print(f"Image resize failed: {e}, using original")
        return image_bytes


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
    return f"data:image/jpeg;base64,{base64_data}"


async def understand_image(
    image_bytes: bytes,
    prompt: str = "Extract all text and data from this image. Return as structured JSON.",
    temperature: float = 0.7,
    max_tokens: int = 1024  # Reduced for faster CPU inference
) -> dict:
    """
    Send an image to Qwen3-VL for understanding.
    Uses semaphore to limit concurrent requests.
    
    Args:
        image_bytes: Raw image bytes
        prompt: Custom prompt for the model
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens to generate
    
    Returns:
        dict with result and metadata
    """
    # Use semaphore to limit concurrent VLM requests
    semaphore = get_vlm_semaphore()
    
    async with semaphore:
        start_time = time.time()
        
        # Check server health first
        status = get_vlm_status()
        if status["status"] != "healthy":
            raise ConnectionError(f"VLM server not available: {status.get('error', 'Unknown error')}")
        
        # Resize large images to speed up processing
        processed_image = resize_image_for_vlm(image_bytes)
        
        # Convert image to base64
        image_url = image_to_base64(processed_image)
        
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
            
            # Thinking model wraps output in <think>...</think> tags
            # The actual response comes AFTER the thinking
            if "</think>" in content:
                # Split and get the part after thinking
                parts = content.split("</think>")
                if len(parts) > 1:
                    # Get the response after thinking, clean it up
                    content = parts[-1].strip()
                else:
                    # No content after thinking, show the thinking itself
                    content = content.replace("<think>", "").replace("</think>", "").strip()
            elif "<think>" in content:
                # Incomplete thinking tag, just show what we have
                content = content.replace("<think>", "").strip()
        
        return {
            "result": content,
            "processing_time_ms": processing_time,
            "model": "qwen3-vl-2b-thinking",
            "tokens_used": data.get("usage", {}),
            "concurrent_limit": VLM_MAX_CONCURRENT,
            "raw_has_think_tag": "</think>" in str(data) if data else False
        }


async def batch_understand_images(
    images: List[tuple],  # List of (filename, image_bytes, prompt) tuples
    temperature: float = 0.7,
    max_tokens: int = 1024
) -> dict:
    """
    Process multiple images in parallel using VLM.
    Uses semaphore to limit concurrent requests.
    
    Args:
        images: List of (filename, image_bytes, prompt) tuples
        temperature: Sampling temperature
        max_tokens: Max tokens per response
    
    Returns:
        Batch result dict with all results
    """
    import time as time_module
    start_time = time_module.time()
    
    async def process_single(item):
        """Process a single image."""
        filename, image_bytes, prompt = item
        try:
            result = await understand_image(
                image_bytes,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return {
                "filename": filename,
                "success": True,
                "result": result["result"],
                "processing_time_ms": result["processing_time_ms"]
            }
        except Exception as e:
            return {
                "filename": filename,
                "success": False,
                "error": str(e)
            }
    
    # Process all images concurrently (semaphore limits actual parallelism)
    tasks = [process_single(item) for item in images]
    results = await asyncio.gather(*tasks)
    
    # Calculate stats
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    total_time = (time_module.time() - start_time) * 1000
    
    return {
        "total_files": len(images),
        "successful": successful,
        "failed": failed,
        "processing_time_ms": total_time,
        "concurrent_limit": VLM_MAX_CONCURRENT,
        "results": results
    }


# Preset prompts for common use cases
PROMPT_PRESETS = {
    "size_chart": """Extract size chart data AND any SKU/article number as JSON.

EXACT FORMAT REQUIRED:
{
    "sizes": ["size1", "size2", ...],
    "measurements": {
        "COLUMN_NAME": {"size1": "value1", "size2": "value2", ...}
    },
    "sku": "extracted SKU or article number if found, otherwise empty string"
}

Rules:
1. "sizes" = array of size labels from first column (e.g., ["36", "37", "38"] or ["S", "M", "L"])
2. "measurements" = object where each key maps to an object of {size: value} pairs
3. Do NOT include the first column (size labels) in measurements
4. Each measurement MUST be an object like {"36": "23 CM", "37": "23.5 CM"}
5. "sku" = Look for any text like "SKU: XXX", "Article: XXX", "Art: XXX", "Model: XXX", "Kode: XXX", or any product code pattern. Extract ONLY the code/number part, NOT the prefix. For example: "SKU 401-02779" -> "401-02779", "Article: ABC-123" -> "ABC-123"

Example input table with SKU:
SKU 207-00635
SIZE | UKURAN
36   | 23 CM
37   | 23.5 CM

Example output:
{
    "sizes": ["36", "37"],
    "measurements": {
        "UKURAN": {"36": "23 CM", "37": "23.5 CM"}
    },
    "sku": "207-00635"
}

Return ONLY valid JSON, no explanations.""",
    
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
