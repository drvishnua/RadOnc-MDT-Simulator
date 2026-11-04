"""Read-only status client for a local Ollama server."""

from __future__ import annotations

import httpx

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL


async def get_ollama_status() -> dict[str, object]:
    """Return runtime reachability and installed model names without generating text."""
    try:
        async with httpx.AsyncClient(base_url=OLLAMA_BASE_URL, timeout=5.0) as client:
            version_response = await client.get("/api/version")
            version_response.raise_for_status()
            version_data = version_response.json()

            tags_response = await client.get("/api/tags")
            tags_response.raise_for_status()
            tags_data = tags_response.json()

        models = [
            str(model.get("name", ""))
            for model in tags_data.get("models", [])
            if model.get("name")
        ]
        return {
            "reachable": True,
            "version": version_data.get("version"),
            "configured_model": OLLAMA_MODEL,
            "configured_model_installed": OLLAMA_MODEL in models,
            "models": models,
        }
    except (httpx.HTTPError, ValueError) as exc:
        return {
            "reachable": False,
            "version": None,
            "configured_model": OLLAMA_MODEL,
            "configured_model_installed": False,
            "models": [],
            "error": type(exc).__name__,
        }
