"""Environment-based configuration for local development."""

from __future__ import annotations

import os


APP_NAME = "RadOnc MDT Simulator"
APP_VERSION = "0.1.0"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")


# Keep the default at one until the local Ollama parallel benchmark demonstrates
# a reliable throughput improvement on the target GPU.
try:
    RADONC_AGENT_CONCURRENCY = max(1, min(2, int(os.getenv("RADONC_AGENT_CONCURRENCY", "1"))))
except ValueError:
    RADONC_AGENT_CONCURRENCY = 1
