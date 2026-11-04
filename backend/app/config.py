"""Environment-based configuration for local development."""

from __future__ import annotations

import os


APP_NAME = "RadOnc MDT Simulator"
APP_VERSION = "0.1.0"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")
