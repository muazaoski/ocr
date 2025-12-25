"""
OCR processing engine using Tesseract.
Handles image preprocessing and text extraction.
"""
import io
import time
from typing import Optional
import cv2
import numpy as np
import pytesseract
from PIL import Image
from pathlib import Path

from .config import get_settings


settings = get_settings()

# Configure Tesseract path if specified
if settings.tesseract_cmd != "tesseract":
    pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


def get_tesseract_version() -> str:
    """Get Tesseract version string."""
    try:
        return pytesseract.get_tesseract_version().base_version
    except Exception as e:
        return f"Error: {str(e)}"


def get_available_languages() -> list[str]:
    """Get list of available Tesseract languages."""
    try:
        return pytesseract.get_languages()
    except Exception:
        return ["eng"]


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Advanced preprocessing that removes table lines to prevent OCR interference.
    Great for size charts and spreadsheets.
    """
    # 1. Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # 2. Rescale (3x) for better character definition
    gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

    # 3. Thresholding to create a binary image
    # Binary inverse so text/lines are white, background is black
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 4. Remove Table Lines
    # Detect horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    remove_horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    
    # Detect vertical lines
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    remove_vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
    
    # Combine lines to be removed
    lines_mask = remove_horizontal + remove_vertical
    
    # Clean up the original binary image by removing the lines
    clean_binary = cv2.bitwise_and(binary, cv2.bitwise_not(lines_mask))
    
    # 5. Final Inversion (Back to Black text on White background)
    final = cv2.bitwise_not(clean_binary)
    
    # Add a bit of white padding (Tesseract loves padding)
    final = cv2.copyMakeBorder(final, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=[255, 255, 255])
    
    return final


def image_to_cv2(image_bytes: bytes) -> np.ndarray:
    """Convert image bytes to OpenCV format."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        raise ValueError("Could not decode image")
    
    return image


def cv2_to_pil(image: np.ndarray) -> Image.Image:
    """Convert OpenCV image to PIL Image."""
    if len(image.shape) == 3:
        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return Image.fromarray(image)


def perform_ocr(
    image_bytes: bytes,
    language: str = "eng",
    psm: int = 3,
    oem: int = 3,
    preprocess: bool = True,
    output_format: str = "text"
) -> dict:
    """
    Perform OCR on an image.
    
    Args:
        image_bytes: Raw image bytes
        language: Tesseract language code
        psm: Page segmentation mode (0-13)
        oem: OCR engine mode (0-3)
        preprocess: Whether to apply preprocessing
        output_format: 'text', 'json', or 'hocr'
    
    Returns:
        dict with result data
    """
    start_time = time.time()
    
    # Validate language
    if language not in settings.languages_list:
        available = ", ".join(settings.languages_list)
        raise ValueError(f"Language '{language}' not allowed. Available: {available}")
    
    # Convert to OpenCV format
    cv_image = image_to_cv2(image_bytes)
    
    # Preprocess if requested
    if preprocess:
        cv_image = preprocess_image(cv_image)
    
    # Convert to PIL for Tesseract
    pil_image = cv2_to_pil(cv_image)
    
    # Build Tesseract config
    config = f"--oem {oem} --psm {psm}"
    
    if output_format == "hocr":
        # Get hOCR output
        result = pytesseract.image_to_pdf_or_hocr(
            pil_image,
            lang=language,
            config=config,
            extension="hocr"
        )
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "hocr": result.decode("utf-8"),
            "processing_time_ms": processing_time,
            "language": language
        }
    
    elif output_format == "json":
        # Get detailed word-level data
        data = pytesseract.image_to_data(
            pil_image,
            lang=language,
            config=config,
            output_type=pytesseract.Output.DICT
        )
        
        # Extract word data
        words = []
        confidences = []
        n_boxes = len(data["level"])
        
        for i in range(n_boxes):
            text = data["text"][i].strip()
            conf = int(data["conf"][i])
            
            if text and conf > 0:
                words.append({
                    "text": text,
                    "confidence": conf,
                    "left": data["left"][i],
                    "top": data["top"][i],
                    "width": data["width"][i],
                    "height": data["height"][i]
                })
                confidences.append(conf)
        
        # Calculate overall confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        full_text = " ".join([w["text"] for w in words])
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "text": full_text,
            "confidence": avg_confidence,
            "processing_time_ms": processing_time,
            "language": language,
            "words": words,
            "line_count": len(set(data["line_num"])),
            "word_count": len(words)
        }
    
    else:
        # Plain text output
        text = pytesseract.image_to_string(
            pil_image,
            lang=language,
            config=config
        )
        
        # Get confidence
        data = pytesseract.image_to_data(
            pil_image,
            lang=language,
            config=config,
            output_type=pytesseract.Output.DICT
        )
        
        confidences = [int(c) for c in data["conf"] if int(c) > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "text": text.strip(),
            "confidence": avg_confidence,
            "processing_time_ms": processing_time,
            "language": language
        }


def perform_batch_ocr(
    images: list[tuple[str, bytes]],
    language: str = "eng",
    psm: int = 3,
    oem: int = 3,
    preprocess: bool = True
) -> dict:
    """
    Perform OCR on multiple images.
    
    Args:
        images: List of (filename, bytes) tuples
        language: Tesseract language code
        psm: Page segmentation mode
        oem: OCR engine mode
        preprocess: Whether to apply preprocessing
    
    Returns:
        Batch result dict
    """
    start_time = time.time()
    results = []
    successful = 0
    failed = 0
    
    for filename, image_bytes in images:
        try:
            result = perform_ocr(
                image_bytes,
                language=language,
                psm=psm,
                oem=oem,
                preprocess=preprocess,
                output_format="text"
            )
            results.append({
                "filename": filename,
                "success": True,
                "text": result["text"],
                "confidence": result["confidence"]
            })
            successful += 1
        except Exception as e:
            results.append({
                "filename": filename,
                "success": False,
                "error": str(e)
            })
            failed += 1
    
    processing_time = (time.time() - start_time) * 1000
    
    return {
        "total_files": len(images),
        "successful": successful,
        "failed": failed,
        "processing_time_ms": processing_time,
        "results": results
    }
