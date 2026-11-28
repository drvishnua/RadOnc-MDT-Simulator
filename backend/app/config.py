"""Validated environment-based configuration for RadOnc MDT Simulator."""

from __future__ import annotations

import os
from typing import ClassVar

from pydantic import BaseModel, Field, field_validator


_DEFAULT_CORS_ORIGINS: tuple[str, ...] = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
)


class AppSettings(BaseModel):
    """Fail-fast Pydantic settings loaded from environment variables."""

    _DEFAULT_ORIGINS: ClassVar[tuple[str, ...]] = _DEFAULT_CORS_ORIGINS

    app_name: str = Field(default="RadOnc MDT Simulator", min_length=1, max_length=120)
    app_version: str = Field(default="0.1.0", min_length=1, max_length=40)
    ollama_base_url: str = Field(default="http://127.0.0.1:11434", min_length=1)
    ollama_model: str = Field(default="qwen3.5:4b", min_length=1, max_length=120)
    agent_concurrency: int = Field(default=1, ge=1, le=2)
    cors_origins: list[str] = Field(default_factory=lambda: list(_DEFAULT_CORS_ORIGINS), min_length=1)
    circuit_breaker_threshold: int = Field(default=5, ge=1, le=49)
    data_dir: str | None = Field(default=None)
    legacy_db_path: str | None = Field(default=None)
    library_path: str | None = Field(default=None)

    @field_validator("ollama_base_url")
    @classmethod
    def validate_ollama_base_url(cls, value: str) -> str:
        cleaned = value.strip().rstrip("/")
        if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
            raise ValueError("OLLAMA_BASE_URL must start with 'http://' or 'https://'.")
        return cleaned

    @field_validator("ollama_model")
    @classmethod
    def validate_ollama_model(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("OLLAMA_MODEL must not be blank.")
        return cleaned

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, values: list[str]) -> list[str]:
        cleaned = [item.strip().rstrip("/") for item in values if item.strip()]
        if not cleaned:
            raise ValueError("RADONC_CORS_ORIGINS must include at least one origin.")
        if any(item == "*" for item in cleaned):
            raise ValueError("Wildcard '*' CORS origin is forbidden; specify explicit origins.")
        return cleaned

    @classmethod
    def from_env(cls) -> "AppSettings":
        raw_concurrency = os.getenv("RADONC_AGENT_CONCURRENCY", "1").strip()
        raw_threshold = os.getenv("RADONC_CIRCUIT_BREAKER_THRESHOLD", "5").strip()
        raw_cors = os.getenv("RADONC_CORS_ORIGINS")
        cors_list = (
            [origin.strip() for origin in raw_cors.split(",") if origin.strip()]
            if raw_cors is not None
            else list(cls._DEFAULT_ORIGINS)
        )
        return cls(
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "qwen3.5:4b"),
            agent_concurrency=int(raw_concurrency),
            cors_origins=cors_list,
            circuit_breaker_threshold=int(raw_threshold),
            data_dir=os.getenv("RADONC_DATA_DIR") or None,
            legacy_db_path=os.getenv("RADONC_LEGACY_DB_PATH") or None,
            library_path=os.getenv("RADONC_LIBRARY_PATH") or None,
        )


settings = AppSettings.from_env()

APP_NAME = settings.app_name
APP_VERSION = settings.app_version
OLLAMA_BASE_URL = settings.ollama_base_url
OLLAMA_MODEL = settings.ollama_model
# Keep the default at one until the local Ollama parallel benchmark demonstrates
# a reliable throughput improvement on the target GPU.
RADONC_AGENT_CONCURRENCY = settings.agent_concurrency
CORS_ORIGINS = settings.cors_origins
CIRCUIT_BREAKER_THRESHOLD = settings.circuit_breaker_threshold
RADONC_DATA_DIR = settings.data_dir
RADONC_LEGACY_DB_PATH = settings.legacy_db_path
RADONC_LIBRARY_PATH = settings.library_path
