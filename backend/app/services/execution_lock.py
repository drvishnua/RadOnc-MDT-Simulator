"""Shared in-process lock for local model generation."""

import asyncio

MODEL_EXECUTION_LOCK = asyncio.Lock()
