"""Compare real local Ollama throughput for one vs two simultaneous requests.

Uses the currently running Ollama service; it does not change server settings or restart
Ollama. A result is a measurement of the current OLLAMA_NUM_PARALLEL configuration.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import statistics
import subprocess
import time
import urllib.error
import urllib.request

BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")
TRIALS = 2


def gpu_snapshot() -> str:
    try:
        return subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=memory.used,memory.total,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=5,
        ).strip()
    except Exception:
        return "nvidia-smi unavailable"


def post_json(path: str, body: dict, timeout: int = 240) -> dict:
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        BASE_URL + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def make_body(sequence: int) -> dict:
    return {
        "model": MODEL,
        "system": "You are a concise test generator. Return one valid JSON object only.",
        "prompt": (
            "Return JSON with one field named summary. In 70 to 90 words, explain "
            "why a synthetic clinical case must distinguish supplied facts from assumptions. "
            f"Include test marker {sequence}."
        ),
        "format": "json",
        "stream": False,
        "think": False,
        "keep_alive": "30m",
        "options": {
            "temperature": 0,
            "seed": 73,
            "num_ctx": 2048,
            "num_predict": 180,
        },
    }


def timed_request(sequence: int) -> tuple[float, dict]:
    started = time.perf_counter()
    payload = post_json("/api/generate", make_body(sequence))
    elapsed = time.perf_counter() - started
    if not isinstance(payload.get("response"), str) or not payload["response"].strip():
        raise RuntimeError(f"Model returned an empty response for test {sequence}.")
    return elapsed, payload


def run_sequential(start_sequence: int) -> dict:
    started = time.perf_counter()
    results = [timed_request(start_sequence), timed_request(start_sequence + 1)]
    wall = time.perf_counter() - started
    return summarize("sequential", wall, results)


def run_parallel(start_sequence: int) -> dict:
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(timed_request, start_sequence),
            pool.submit(timed_request, start_sequence + 1),
        ]
        results = [future.result() for future in futures]
    wall = time.perf_counter() - started
    return summarize("parallel_2", wall, results)


def summarize(mode: str, wall: float, results: list[tuple[float, dict]]) -> dict:
    tokens = sum(int(payload.get("eval_count", 0)) for _, payload in results)
    generation_ns = sum(int(payload.get("eval_duration", 0)) for _, payload in results)
    return {
        "mode": mode,
        "wall_seconds": round(wall, 2),
        "individual_seconds": [round(seconds, 2) for seconds, _ in results],
        "output_tokens": tokens,
        "aggregate_generation_tokens_per_second": round(tokens / (generation_ns / 1e9), 2)
        if generation_ns
        else None,
        "load_seconds": [
            round(int(payload.get("load_duration", 0)) / 1e9, 2)
            for _, payload in results
        ],
    }


def main() -> int:
    print("RADONC_OLLAMA_CONCURRENCY_BENCHMARK")
    print(f"Endpoint: {BASE_URL}")
    print(f"Model: {MODEL}")
    try:
        with urllib.request.urlopen(BASE_URL + "/api/version", timeout=4) as response:
            version = json.loads(response.read().decode("utf-8")).get("version")
    except Exception as exc:
        print(f"SKIP: Ollama is not reachable ({type(exc).__name__}).")
        return 0

    print(f"Ollama version: {version}")
    print(f"GPU before: {gpu_snapshot()}")

    try:
        # One warm-up call prevents model-loading time from skewing the comparison.
        timed_request(9000)
        sequential = [run_sequential(9100 + index * 2) for index in range(TRIALS)]
        parallel = [run_parallel(9200 + index * 2) for index in range(TRIALS)]
    except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
        print(f"BENCHMARK_ERROR: {type(exc).__name__}: {exc}")
        return 1

    seq_median = statistics.median(item["wall_seconds"] for item in sequential)
    par_median = statistics.median(item["wall_seconds"] for item in parallel)
    speedup = seq_median / par_median if par_median else 0.0
    recommendation = 2 if speedup >= 1.12 else 1

    print("Sequential trials:")
    for item in sequential:
        print(json.dumps(item, sort_keys=True))
    print("Two-request parallel trials:")
    for item in parallel:
        print(json.dumps(item, sort_keys=True))
    print(f"Sequential median pair time: {seq_median:.2f}s")
    print(f"Parallel median pair time: {par_median:.2f}s")
    print(f"Measured speedup: {speedup:.2f}x")
    print(f"Recommended RADONC_AGENT_CONCURRENCY: {recommendation}")
    print(f"GPU after: {gpu_snapshot()}")
    print("Note: this test measures the currently running Ollama server settings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
