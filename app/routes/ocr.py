"""
API Routes for OCR operations.
"""
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form, Query
from fastapi.responses import Response

from ..auth import get_api_key
from ..ocr_engine import perform_ocr, perform_batch_ocr, get_available_languages
from ..models import OCRTextResult, OCRDetailedResult, OCRBatchResult
from ..config import get_settings


settings = get_settings()
router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.post(
    "/extract",
    response_model=OCRTextResult,
    summary="Extract text from image",
    description="Upload an image and extract text using Tesseract OCR."
)
async def extract_text(
    file: UploadFile = File(..., description="Image file (PNG, JPEG, TIFF, etc.)"),
    language: str = Query("eng", description="Language code (e.g., eng, fra, deu)"),
    psm: int = Query(3, ge=0, le=13, description="Page segmentation mode"),
    oem: int = Query(3, ge=0, le=3, description="OCR engine mode"),
    preprocess: bool = Query(True, description="Apply image preprocessing"),
    api_key: dict = Depends(get_api_key)
):
    """
    Extract text from an uploaded image.
    
    **Page Segmentation Modes (PSM):**
    - 0: Orientation and script detection only
    - 1: Automatic page segmentation with OSD
    - 3: Fully automatic page segmentation (default)
    - 4: Assume single column of text
    - 6: Assume single uniform block of text
    - 7: Treat image as single text line
    - 8: Treat image as single word
    - 11: Sparse text, find as much text as possible
    - 13: Raw line, treat as single text line
    
    **OCR Engine Modes (OEM):**
    - 0: Legacy engine only
    - 1: Neural nets LSTM engine only
    - 2: Legacy + LSTM engines
    - 3: Default, based on what is available
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
    
    try:
        result = perform_ocr(
            image_bytes,
            language=language,
            psm=psm,
            oem=oem,
            preprocess=preprocess,
            output_format="text"
        )
        return OCRTextResult(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


@router.post(
    "/extract/detailed",
    response_model=OCRDetailedResult,
    summary="Extract text with word-level data",
    description="Get detailed OCR results including word positions and confidence."
)
async def extract_detailed(
    file: UploadFile = File(..., description="Image file"),
    language: str = Query("eng", description="Language code"),
    psm: int = Query(3, ge=0, le=13, description="Page segmentation mode"),
    oem: int = Query(3, ge=0, le=3, description="OCR engine mode"),
    preprocess: bool = Query(True, description="Apply preprocessing"),
    api_key: dict = Depends(get_api_key)
):
    """Get detailed OCR results with word positions and individual confidence scores."""
    content_type = file.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    image_bytes = await file.read()
    
    if len(image_bytes) > settings.max_file_size_bytes:
        raise HTTPException(status_code=400, detail="File too large")
    
    try:
        result = perform_ocr(
            image_bytes,
            language=language,
            psm=psm,
            oem=oem,
            preprocess=preprocess,
            output_format="json"
        )
        return OCRDetailedResult(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


@router.post(
    "/extract/hocr",
    summary="Extract text as hOCR",
    description="Get OCR results in hOCR XML format."
)
async def extract_hocr(
    file: UploadFile = File(..., description="Image file"),
    language: str = Query("eng", description="Language code"),
    psm: int = Query(3, ge=0, le=13, description="Page segmentation mode"),
    oem: int = Query(3, ge=0, le=3, description="OCR engine mode"),
    preprocess: bool = Query(True, description="Apply preprocessing"),
    api_key: dict = Depends(get_api_key)
):
    """Get OCR results in hOCR XML format for document analysis."""
    content_type = file.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    image_bytes = await file.read()
    
    if len(image_bytes) > settings.max_file_size_bytes:
        raise HTTPException(status_code=400, detail="File too large")
    
    try:
        result = perform_ocr(
            image_bytes,
            language=language,
            psm=psm,
            oem=oem,
            preprocess=preprocess,
            output_format="hocr"
        )
        return Response(
            content=result["hocr"],
            media_type="application/xml"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


@router.post(
    "/batch",
    response_model=OCRBatchResult,
    summary="Batch process multiple images",
    description="Upload multiple images and process them in batch."
)
async def batch_extract(
    files: List[UploadFile] = File(..., description="Image files (max 10)"),
    language: str = Query("eng", description="Language code"),
    psm: int = Query(3, ge=0, le=13, description="Page segmentation mode"),
    oem: int = Query(3, ge=0, le=3, description="OCR engine mode"),
    preprocess: bool = Query(True, description="Apply preprocessing"),
    api_key: dict = Depends(get_api_key)
):
    """
    Process multiple images in a single request.
    Maximum 10 files per batch request.
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 files per batch request"
        )
    
    images = []
    for file in files:
        content_type = file.content_type or ""
        if not content_type.startswith("image/"):
            continue
        
        image_bytes = await file.read()
        if len(image_bytes) <= settings.max_file_size_bytes:
            images.append((file.filename or "unknown", image_bytes))
    
    if not images:
        raise HTTPException(
            status_code=400,
            detail="No valid image files found"
        )
    
    try:
        result = perform_batch_ocr(
            images,
            language=language,
            psm=psm,
            oem=oem,
            preprocess=preprocess
        )
        return OCRBatchResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")


@router.get(
    "/languages",
    summary="Get available languages",
    description="List all available OCR languages."
)
async def list_languages(api_key: dict = Depends(get_api_key)):
    """Get list of available Tesseract languages."""
    try:
        installed = get_available_languages()
        allowed = settings.languages_list
        available = [lang for lang in installed if lang in allowed]
        
        return {
            "installed": installed,
            "allowed": allowed,
            "available": available
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
