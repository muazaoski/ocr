"""
Configuration settings for the OCR API service.
Loads from environment variables with sensible defaults.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Security
    secret_key: str = "change-this-in-production-use-a-strong-random-key"
    admin_username: str = "admin"
    admin_password: str = "admin123"
    algorithm: str = "HS256"
    access_token_expire_days: int = 365
    
    # Tesseract
    tesseract_cmd: str = "tesseract"
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_day: int = 1000
    
    # File Upload
    max_file_size_mb: int = 10
    
    # Allowed Languages
    allowed_languages: str = "eng,fra,deu,spa,ita,por,nld,pol,rus,jpn,chi_sim,chi_tra,kor,ara"
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent
    data_dir: Path = base_dir / "data"
    uploads_dir: Path = data_dir / "uploads"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def languages_list(self) -> list[str]:
        return [lang.strip() for lang in self.allowed_languages.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Ensure directories exist
settings = get_settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.uploads_dir.mkdir(parents=True, exist_ok=True)
