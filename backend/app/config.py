"""Configuration management for the Pantry Inventory API."""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration."""

    # API Configuration
    API_TITLE: str = "Pantry Inventory API"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite:///./pantry.db"
    )

    # Vision Provider Configuration
    # Default is "hermes" (agent-driven analysis). Other supported providers:
    # openai, nvidia, ollama, mock. OpenClaw is NOT used/tested/supported.
    VISION_PROVIDER: str = os.getenv("VISION_PROVIDER", "hermes")

    # Hermes Vision (agent-driven analysis via OpenAI-compatible endpoint)
    HERMES_VISION_URL: str = os.getenv("HERMES_VISION_URL", "")
    HERMES_API_KEY: Optional[str] = os.getenv("HERMES_API_KEY")
    HERMES_MODEL: str = os.getenv("HERMES_MODEL", "gpt-4-vision-preview")
    HERMES_TIMEOUT: int = int(os.getenv("HERMES_TIMEOUT", "120"))

    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-5")
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TIMEOUT: int = 30
    
    # NVIDIA NIM Configuration
    NVIDIA_NIM_API_KEY: Optional[str] = os.getenv("NVIDIA_NIM_API_KEY")
    NVIDIA_MODEL: str = os.getenv("NVIDIA_MODEL", "moonshotai/kimi-k2.5")
    # Redis Configuration (for job queue and caching)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds

    # Shared API token (Bearer) required on all write routes.
    # Set PANTRY_API_TOKEN in the environment/.env. If not set, writes are
    # allowed (dev mode) so existing setups don't break; production should set it.
    PANTRY_API_TOKEN: Optional[str] = os.getenv("PANTRY_API_TOKEN")

    # Allowed CORS origins (comma-separated in env). Localhost defaults are safe
    # for local dev; set CORS_ORIGINS to your deployed web origin in production.
    CORS_ORIGINS: list = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if o.strip()
    ]

    # Job Queue Configuration
    CELERY_BROKER_URL: str = os.getenv(
        "CELERY_BROKER_URL", "redis://localhost:6379/0"
    )
    CELERY_RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    )
    JOB_TIMEOUT: int = 300  # 5 minutes
    MAX_RETRIES: int = 3

    # Image Processing Configuration
    MAX_IMAGE_SIZE: int = 20 * 1024 * 1024  # 20 MB
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/webp"]
    
    # Storage Configuration
    STORAGE_PATH: str = os.getenv("STORAGE_PATH", "./storage")
    IMAGE_RETENTION_DAYS: int = int(os.getenv("IMAGE_RETENTION_DAYS", "30"))
    MAX_STORAGE_MB: int = int(os.getenv("MAX_STORAGE_MB", "5000"))

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "WARNING")
    # Legacy .env compatibility (ignored but accepted)
    IMAGES_DIR: Optional[str] = None
    HOST: Optional[str] = None
    PORT: Optional[str] = None


    # Vision Confidence Tuning
    VISION_MIN_CONFIDENCE: float = float(os.getenv("VISION_MIN_CONFIDENCE", "0.7"))
    VISION_MIN_SCENE_CONFIDENCE: float = float(os.getenv("VISION_MIN_SCENE_CONFIDENCE", "0.3"))
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()

