"""Centralized configuration management for the antenna digital twin system."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    APP_NAME: str = "Antenna Digital Twin"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8080", "http://127.0.0.1:3000", "http://127.0.0.1:5173", "http://127.0.0.1:8080"]
    
    # Database - PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "antenna_twin"
    POSTGRES_PASSWORD: str = "antenna_twin"
    POSTGRES_DB: str = "antenna_twin"
    DATABASE_URL: Optional[str] = None
    
    # Database - InfluxDB (Time-series)
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = ""
    INFLUXDB_ORG: str = "antenna_twin"
    INFLUXDB_BUCKET: str = "measurements"
    
    # Object Storage - MinIO/S3
    S3_ENDPOINT: str = "localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_EM_RESULTS: str = "em-results"
    S3_BUCKET_MEASUREMENTS: str = "measurements"
    S3_USE_SSL: bool = False
    
    # ML Models (resolved relative to backend package so path is consistent)
    _backend_root: Path = Path(__file__).resolve().parent.parent
    ML_MODEL_DIR: Path = _backend_root / "models"
    ML_CACHE_DIR: Path = _backend_root / "cache"
    ML_DEVICE: str = "cpu"  # "cpu" or "cuda"
    # When predicted surrogate MAE (e.g. dB) exceeds this, recommend running full EM
    EM_ACCURACY_THRESHOLD_MAE: float = 1.0  # dB for s11_min
    # Nearest-neighbor blend: pull model output toward OpenEMS training data when design is close
    NN_BLEND_ENABLED: bool = True
    NN_BLEND_DISTANCE_THRESHOLD: float = 2.0  # in scaled space; blend when nearest dist < this
    NN_BLEND_WEIGHT_MAX: float = 0.5  # max weight (0–1) given to nearest training row

    # EM Solver
    EM_SOLVER_TIMEOUT: int = 3600  # seconds
    EM_SOLVER_MAX_WORKERS: int = 4
    EM_SOLVER_RESULTS_DIR: Path = Path("data/em_results")
    
    # Celery (Task Queue)
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Unity Integration
    UNITY_WEBSOCKET_PORT: int = 8765
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[Path] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-generate DATABASE_URL if not provided
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        
        # Create directories
        self.ML_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        self.ML_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.EM_SOLVER_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        if self.LOG_FILE:
            self.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()



















