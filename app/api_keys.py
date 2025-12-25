"""
API Key management - storage and validation.
Uses JSON file for persistence (can be upgraded to database later).
"""
import json
import secrets
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from .config import get_settings


settings = get_settings()
API_KEYS_FILE = settings.data_dir / "api_keys.json"


def _load_keys() -> dict:
    """Load API keys from file."""
    if not API_KEYS_FILE.exists():
        return {}
    with open(API_KEYS_FILE, "r") as f:
        return json.load(f)


def _save_keys(keys: dict) -> None:
    """Save API keys to file."""
    with open(API_KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=2, default=str)


def _hash_key(key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a new API key."""
    return f"ocr_{secrets.token_urlsafe(32)}"


def create_api_key(
    name: str,
    rate_limit_per_minute: int = 60,
    rate_limit_per_day: int = 1000,
    is_active: bool = True
) -> dict:
    """Create a new API key and store it."""
    keys = _load_keys()
    
    # Generate unique ID and key
    key_id = secrets.token_hex(8)
    raw_key = generate_api_key()
    key_hash = _hash_key(raw_key)
    
    key_data = {
        "id": key_id,
        "name": name,
        "key_hash": key_hash,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_used": None,
        "is_active": is_active,
        "rate_limit_per_minute": rate_limit_per_minute,
        "rate_limit_per_day": rate_limit_per_day,
        "total_requests": 0,
        "requests_log": []  # Stores timestamps for rate limiting
    }
    
    keys[key_id] = key_data
    _save_keys(keys)
    
    # Return the raw key (only shown once!)
    return {
        "id": key_id,
        "name": name,
        "key": raw_key,  # Only returned during creation
        "created_at": key_data["created_at"],
        "is_active": is_active,
        "rate_limit_per_minute": rate_limit_per_minute,
        "rate_limit_per_day": rate_limit_per_day,
        "total_requests": 0
    }


def validate_api_key(raw_key: str) -> Optional[dict]:
    """Validate an API key and return its data if valid."""
    if not raw_key or not raw_key.startswith("ocr_"):
        return None
    
    key_hash = _hash_key(raw_key)
    keys = _load_keys()
    
    for key_id, key_data in keys.items():
        if key_data["key_hash"] == key_hash:
            if not key_data.get("is_active", True):
                return None
            return key_data
    
    return None


def update_key_usage(key_id: str) -> None:
    """Update usage statistics for an API key."""
    keys = _load_keys()
    
    if key_id not in keys:
        return
    
    now = datetime.now(timezone.utc)
    keys[key_id]["last_used"] = now.isoformat()
    keys[key_id]["total_requests"] = keys[key_id].get("total_requests", 0) + 1
    
    # Add to requests log for rate limiting
    requests_log = keys[key_id].get("requests_log", [])
    requests_log.append(now.isoformat())
    
    # Keep only last 24 hours of requests
    cutoff = (now.timestamp() - 86400)  # 24 hours ago
    requests_log = [
        ts for ts in requests_log 
        if datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp() > cutoff
    ]
    keys[key_id]["requests_log"] = requests_log
    
    _save_keys(keys)


def check_rate_limit(key_data: dict) -> tuple[bool, str]:
    """Check if API key is within rate limits."""
    now = datetime.now(timezone.utc)
    requests_log = key_data.get("requests_log", [])
    
    # Count requests in last minute
    minute_ago = now.timestamp() - 60
    requests_last_minute = sum(
        1 for ts in requests_log
        if datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp() > minute_ago
    )
    
    if requests_last_minute >= key_data.get("rate_limit_per_minute", 60):
        return False, "Rate limit exceeded: too many requests per minute"
    
    # Count requests today
    day_ago = now.timestamp() - 86400
    requests_today = sum(
        1 for ts in requests_log
        if datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp() > day_ago
    )
    
    if requests_today >= key_data.get("rate_limit_per_day", 1000):
        return False, "Rate limit exceeded: daily limit reached"
    
    return True, ""


def list_api_keys() -> list[dict]:
    """List all API keys (without the actual keys)."""
    keys = _load_keys()
    result = []
    
    for key_id, key_data in keys.items():
        result.append({
            "id": key_id,
            "name": key_data["name"],
            "created_at": key_data["created_at"],
            "last_used": key_data.get("last_used"),
            "is_active": key_data.get("is_active", True),
            "rate_limit_per_minute": key_data.get("rate_limit_per_minute", 60),
            "rate_limit_per_day": key_data.get("rate_limit_per_day", 1000),
            "total_requests": key_data.get("total_requests", 0)
        })
    
    return result


def get_api_key_stats(key_id: str) -> Optional[dict]:
    """Get statistics for a specific API key."""
    keys = _load_keys()
    
    if key_id not in keys:
        return None
    
    key_data = keys[key_id]
    now = datetime.now(timezone.utc)
    requests_log = key_data.get("requests_log", [])
    
    # Calculate stats
    hour_ago = now.timestamp() - 3600
    day_ago = now.timestamp() - 86400
    
    requests_this_hour = sum(
        1 for ts in requests_log
        if datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp() > hour_ago
    )
    requests_today = sum(
        1 for ts in requests_log
        if datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp() > day_ago
    )
    
    return {
        "id": key_id,
        "name": key_data["name"],
        "total_requests": key_data.get("total_requests", 0),
        "requests_today": requests_today,
        "requests_this_hour": requests_this_hour,
        "last_used": key_data.get("last_used")
    }


def delete_api_key(key_id: str) -> bool:
    """Delete an API key."""
    keys = _load_keys()
    
    if key_id not in keys:
        return False
    
    del keys[key_id]
    _save_keys(keys)
    return True


def toggle_api_key(key_id: str, is_active: bool) -> bool:
    """Enable or disable an API key."""
    keys = _load_keys()
    
    if key_id not in keys:
        return False
    
    keys[key_id]["is_active"] = is_active
    _save_keys(keys)
    return True


def get_usage_stats() -> dict:
    """Get overall usage statistics."""
    keys = _load_keys()
    now = datetime.now(timezone.utc)
    day_ago = now.timestamp() - 86400
    
    total_requests_today = 0
    total_requests_all_time = 0
    active_keys = 0
    
    for key_data in keys.values():
        total_requests_all_time += key_data.get("total_requests", 0)
        
        if key_data.get("is_active", True):
            active_keys += 1
        
        requests_log = key_data.get("requests_log", [])
        total_requests_today += sum(
            1 for ts in requests_log
            if datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp() > day_ago
        )
    
    return {
        "total_api_keys": len(keys),
        "active_api_keys": active_keys,
        "total_requests_today": total_requests_today,
        "total_requests_all_time": total_requests_all_time
    }
