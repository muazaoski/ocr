"""
API Routes for AI-powered document understanding.
Uses Qwen3-VL-2B-Thinking for vision-language tasks.
"""
from typing import Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form, Query
from pydantic import BaseModel

from ..auth import get_api_key
from ..vlm_engine import understand_image, get_vlm_status, get_preset_prompt, PROMPT_PRESETS
from ..config import get_settings


settings = get_settings()
router = APIRouter(prefix="/ocr", tags=["AI Understanding"])


class UnderstandResult(BaseModel):
    """Response model for document understanding."""
    result: str
    processing_time_ms: float
    model: str
    tokens_used: dict = {}


class VLMStatusResult(BaseModel):
    """Response model for VLM status check."""
    status: str
    server: Optional[str] = None
    error: Optional[str] = None


@router.get(
    "/understand/status",
    response_model=VLMStatusResult,
    summary="Check VLM server status",
    description="Check if the Qwen3-VL vision language model server is running."
)
async def check_vlm_status(api_key: dict = Depends(get_api_key)):
    """Check if the VLM server is healthy and available."""
    status = get_vlm_status()
    return VLMStatusResult(**status)


@router.get(
    "/understand/presets",
    summary="List available prompt presets",
    description="Get list of available prompt presets for common document types."
)
async def list_presets(api_key: dict = Depends(get_api_key)):
    """Get available prompt presets."""
    return {
        "presets": list(PROMPT_PRESETS.keys()),
        "descriptions": {
            "size_chart": "Extract size chart measurements as structured JSON",
            "invoice": "Extract invoice data including items, totals, vendor info",
            "receipt": "Extract receipt data including items and totals",
            "business_card": "Extract contact information from business cards",
            "table": "Extract tabular data with headers and rows",
            "general": "General purpose extraction and description"
        }
    }


@router.post(
    "/understand",
    response_model=UnderstandResult,
    summary="AI-powered document understanding",
    description="""
Upload an image and get AI-powered understanding using Qwen3-VL-2B-Thinking.

Unlike basic OCR, this endpoint:
- Understands context and meaning
- Can extract structured data (JSON)
- Handles complex layouts, tables, charts
- Works with blur, tilt, low-light images
- Supports 32 languages

**Preset Types:**
- `size_chart` - Extract size measurements
- `invoice` - Extract invoice data
- `receipt` - Extract receipt data
- `business_card` - Extract contact info
- `table` - Extract tabular data
- `general` - General understanding

**Custom Prompts:**
Use the `prompt` parameter for specific instructions.
"""
)
async def understand_document(
    file: UploadFile = File(..., description="Image file (PNG, JPEG, WebP, etc.)"),
    preset: Optional[str] = Query(
        None, 
        description="Prompt preset (size_chart, invoice, receipt, business_card, table, general)"
    ),
    prompt: Optional[str] = Form(
        None, 
        description="Custom prompt (overrides preset)"
    ),
    temperature: float = Query(
        0.7, 
        ge=0.0, 
        le=1.0, 
        description="Sampling temperature (lower = more focused)"
    ),
    max_tokens: int = Query(
        2048, 
        ge=256, 
        le=4096, 
        description="Maximum tokens to generate"
    ),
    api_key: dict = Depends(get_api_key)
):
    """
    Analyze an image using AI vision-language model.
    
    This uses Qwen3-VL-2B-Thinking which can:
    - Read and understand text in 32 languages
    - Extract structured data from tables/charts
    - Handle poor quality images (blur, tilt, low light)
    - Provide contextual understanding, not just raw OCR
    
    **Performance Note:** 
    CPU inference takes 10-30 seconds depending on image complexity.
    """
    # Validate file type
    content_type = file.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {content_type}. Please upload an image."
        )
    
    # Read file
    image_bytes = await file.read()
    
    # Check file size
    if len(image_bytes) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.max_file_size_mb}MB."
        )
    
    # Determine prompt to use
    if prompt:
        final_prompt = prompt
    elif preset:
        final_prompt = get_preset_prompt(preset)
    else:
        final_prompt = get_preset_prompt("general")
    
    try:
        result = await understand_image(
            image_bytes,
            prompt=final_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return UnderstandResult(**result)
    
    except ConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail=f"VLM server unavailable: {str(e)}. Please try again later."
        )
    except TimeoutError as e:
        raise HTTPException(
            status_code=504,
            detail=f"Request timed out: {str(e)}. Image may be too complex."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Understanding failed: {str(e)}"
        )


@router.post(
    "/understand/size-chart",
    response_model=UnderstandResult,
    summary="Extract size chart data",
    description="Specialized endpoint for extracting size chart measurements."
)
async def understand_size_chart(
    file: UploadFile = File(..., description="Size chart image"),
    api_key: dict = Depends(get_api_key)
):
    """
    Extract structured data from a size chart image.
    
    Returns JSON with:
    - sizes: List of size labels
    - measurements: Dict of measurement types with values per size
    - notes: Any additional notes found
    """
    content_type = file.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    image_bytes = await file.read()
    
    if len(image_bytes) > settings.max_file_size_bytes:
        raise HTTPException(status_code=400, detail="File too large")
    
    try:
        result = await understand_image(
            image_bytes,
            prompt=get_preset_prompt("size_chart"),
            temperature=0.3,  # Lower temp for more consistent extraction
            max_tokens=2048
        )
        return UnderstandResult(**result)
    
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
