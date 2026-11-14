"""Regression tests for bounded structured Ollama generation timeouts."""

from __future__ import annotations

import asyncio
import json

from pydantic import BaseModel

from app.services import mdt_generation


class _StructuredResult(BaseModel):
    value: str


class _FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"response": json.dumps({"value": "ok"})}


def test_generate_structured_uses_extended_bounded_read_timeout(monkeypatch):
    captured = {}

    class _FakeAsyncClient:
        def __init__(self, *, base_url: str, timeout):
            captured["base_url"] = base_url
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def post(self, path: str, json: dict):
            captured["path"] = path
            captured["request"] = json
            return _FakeResponse()

    monkeypatch.setattr(mdt_generation.httpx, "AsyncClient", _FakeAsyncClient)

    result = asyncio.run(
        mdt_generation._generate_structured("bounded test prompt", _StructuredResult, 32)
    )

    assert result.value == "ok"
    assert captured["path"] == "/api/generate"
    assert captured["timeout"].read == mdt_generation.GENERATION_REQUEST_TIMEOUT_SECONDS
    assert captured["timeout"].connect == 5.0
    assert mdt_generation.GENERATION_REQUEST_TIMEOUT_SECONDS == 600.0
