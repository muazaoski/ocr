from fastapi import APIRouter, HTTPException, Depends, Request
from ..auth import get_admin_user, authenticate_admin
from ..api_keys import (
    create_api_key, list_api_keys, get_api_key_stats,
    delete_api_key, toggle_api_key, get_usage_stats
)
from ..models import APIKeyCreate, APIKeyResponse, APIKeyStats, Token, AdminLogin, UsageStats
from ..config import get_settings
from ..limiter import limiter


settings = get_settings()
router = APIRouter(prefix=f"/{settings.admin_path}", tags=["Admin"])


@router.post(
    "/login",
    response_model=Token,
    summary="Admin login",
    description="Authenticate as admin to manage API keys."
)
@limiter.limit("5/minute")
async def admin_login(request: Request, credentials: AdminLogin):
    """Authenticate admin and get access token."""
    token = authenticate_admin(credentials.username, credentials.password)
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
    
    return Token(access_token=token)


@router.get(
    "/keys",
    response_model=list[APIKeyResponse],
    summary="List API keys",
    description="Get all API keys (without the actual key values)."
)
async def list_keys(admin: dict = Depends(get_admin_user)):
    """List all API keys."""
    keys = list_api_keys()
    
    # Add placeholder for key field (actual key not stored)
    for key in keys:
        key["key"] = "••••••••"
    
    return keys


@router.post(
    "/keys",
    response_model=APIKeyResponse,
    summary="Create API key",
    description="Create a new API key. The key is only shown once!"
)
async def create_key(
    key_data: APIKeyCreate,
    admin: dict = Depends(get_admin_user)
):
    """
    Create a new API key.
    
    ⚠️ **Important:** The API key is only returned once during creation.
    Store it securely as it cannot be retrieved later.
    """
    key = create_api_key(
        name=key_data.name,
        rate_limit_per_minute=key_data.rate_limit_per_minute,
        rate_limit_per_day=key_data.rate_limit_per_day,
        is_active=key_data.is_active
    )
    return APIKeyResponse(**key)


@router.get(
    "/keys/{key_id}",
    response_model=APIKeyStats,
    summary="Get API key stats",
    description="Get usage statistics for a specific API key."
)
async def get_key_stats(
    key_id: str,
    admin: dict = Depends(get_admin_user)
):
    """Get detailed statistics for an API key."""
    stats = get_api_key_stats(key_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return APIKeyStats(**stats)


@router.delete(
    "/keys/{key_id}",
    summary="Delete API key",
    description="Permanently delete an API key."
)
async def remove_key(
    key_id: str,
    admin: dict = Depends(get_admin_user)
):
    """Delete an API key."""
    if not delete_api_key(key_id):
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {"message": "API key deleted successfully"}


@router.patch(
    "/keys/{key_id}/toggle",
    summary="Enable/disable API key",
    description="Toggle an API key's active status."
)
async def toggle_key(
    key_id: str,
    is_active: bool,
    admin: dict = Depends(get_admin_user)
):
    """Enable or disable an API key."""
    if not toggle_api_key(key_id, is_active):
        raise HTTPException(status_code=404, detail="API key not found")
    
    status = "enabled" if is_active else "disabled"
    return {"message": f"API key {status} successfully"}


@router.get(
    "/stats",
    response_model=UsageStats,
    summary="Get usage statistics",
    description="Get overall API usage statistics."
)
async def usage_stats(admin: dict = Depends(get_admin_user)):
    """Get overall usage statistics."""
    return UsageStats(**get_usage_stats())
