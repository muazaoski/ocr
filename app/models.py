"""
Pydantic models for request/response schemas.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ============================================================================
# API Key Models
# ============================================================================

class APIKeyCreate(BaseModel):
    """Request model for creating a new API key."""
    name: str = Field(..., min_length=1, max_length=100, description="Name/description for this API key")
    rate_limit_per_minute: int = Field(60, ge=1, le=1000, description="Requests allowed per minute")
    rate_limit_per_day: int = Field(1000, ge=1, le=100000, description="Requests allowed per day")
    is_active: bool = Field(True, description="Whether the key is active")


class APIKeyResponse(BaseModel):
    """Response model for API key information."""
    id: str
    name: str
    key: str
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool
    rate_limit_per_minute: int
    rate_limit_per_day: int
    total_requests: int = 0


class APIKeyStats(BaseModel):
    """Statistics for an API key."""
    id: str
    name: str
    total_requests: int
    requests_today: int
    requests_this_hour: int
    last_used: Optional[datetime] = None


# ============================================================================
# OCR Models
# ============================================================================

class OCRRequest(BaseModel):
    """Configuration options for OCR request."""
    language: str = Field("eng", description="Language code (e.g., eng, fra, deu)")
    psm: int = Field(3, ge=0, le=13, description="Page segmentation mode (0-13)")
    oem: int = Field(3, ge=0, le=3, description="OCR engine mode (0-3)")
    preprocess: bool = Field(True, description="Apply image preprocessing")
    output_format: str = Field("text", description="Output format: text, json, hocr")


class OCRTextResult(BaseModel):
    """OCR result in plain text format."""
    text: str
    confidence: float
    processing_time_ms: float
    language: str


class OCRWordData(BaseModel):
    """Individual word data from OCR."""
    text: str
    confidence: float
    left: int
    top: int
    width: int
    height: int


class OCRDetailedResult(BaseModel):
    """Detailed OCR result with word-level data."""
    text: str
    confidence: float
    processing_time_ms: float
    language: str
    words: list[OCRWordData]
    line_count: int
    word_count: int


class OCRBatchItem(BaseModel):
    """Individual item result in batch processing."""
    filename: str
    success: bool
    text: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None


class OCRBatchResult(BaseModel):
    """Result from batch OCR processing."""
    total_files: int
    successful: int
    failed: int
    processing_time_ms: float
    results: list[OCRBatchItem]


# ============================================================================
# Authentication Models
# ============================================================================

class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class AdminLogin(BaseModel):
    """Admin login credentials."""
    username: str
    password: str


# ============================================================================
# Health & Info Models
# ============================================================================

class HealthCheck(BaseModel):
    """Health check response."""
    status: str
    version: str
    tesseract_version: str
    available_languages: list[str]


class UsageStats(BaseModel):
    """API usage statistics."""
    total_api_keys: int
    active_api_keys: int
    total_requests_today: int
    total_requests_all_time: int
