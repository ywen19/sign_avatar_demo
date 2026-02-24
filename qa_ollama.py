#!/usr/bin/env python3
"""
qa_ollama_single.py
-------------------
Hardware validation workload:
- Start `ollama serve` as a CHILD process (so proc-tree monitor includes it)
- Start monitor_process.py (your existing proc-tree monitor) against THIS script PID
- Send ONE prompt, block until full response returned (non-streaming)
- Optional warmup/after idle windows to capture stable VRAM baseline and post-gen steady state
- Exit (monitor stops when parent process ends)

Assumptions:
- `ollama` is installed and on PATH
- monitor_process.py is located at: ./pc_test/monitor_process.py (relative to this file)
- For clean runs, pre-pull the model to avoid download noise:
    ollama pull phi3:mini
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from typing import Any, Dict, Optional

import requests


# --------- Fixed config (keep deterministic for hardware validation) ---------
MODEL = "phi3:mini"

# One prompt only (edit freely)
PROMPT = (
    "You are a helpful assistant. Answer in English.\n"
    "Explain in 4 sentences what causes frame drops in real-time rendering pipelines."
)

TEMPERATURE = 0.2
NUM_PREDICT = 200        # Max tokens to generate
HTTP_TIMEOUT_S = 300

# Monitoring / timing windows
MONITOR_OUT = "resource_log.csv"
MONITOR_INTERVAL_S = 1.0
WARMUP_SECONDS = 5.0     # idle after ollama ready (weights/VRAM settle)
AFTER_SECONDS = 5.0      # idle after response (capture post-gen steady state)

# Child process output
QUIET_CHILDREN = True    # set False if you want to see ollama/monitor logs

# Whether to print model response (printing can add noise)
PRINT_RESPONSE = False
# ---------------------------------------------------------------------------


def pick_free_port(preferred: int = 11434) -> int:
    """Pick a free localhost port. Prefer 11434 if available."""
    def is_free(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return True
            except OSError:
                return False

    if is_free(preferred):
        return preferred

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def wait_for_ollama_ready(base_url: str, timeout_s: float = 12.0) -> bool:
    """Wait until Ollama responds (poll /api/tags)."""
    deadline = time.time() + timeout_s
    url = base_url.rstrip("/") + "/api/tags"
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=1.0)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.2)
    return False


def terminate_proc(p: Optional[subprocess.Popen]) -> None:
    if p is None:
        return
    try:
        if p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                p.kill()
    except Exception:
        pass


def ask_once(base_url: str, model: str, prompt: str) -> str:
    """Single non-streaming call to Ollama /api/generate (blocks until done)."""
    url = base_url.rstrip("/") + "/api/generate"
    payload: Dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": TEMPERATURE,
            "num_predict": NUM_PREDICT,
        },
    }
    r = requests.post(url, json=payload, timeout=HTTP_TIMEOUT_S)
    r.raise_for_status()
    data = r.json()
    return (data.get("response") or "").strip()


def main() -> int:
    # 1) Start ollama serve as CHILD
    port = pick_free_port(11434)
    base_url = f"http://127.0.0.1:{port}"

    env = os.environ.copy()
    env["OLLAMA_HOST"] = f"127.0.0.1:{port}"

    stdout = subprocess.DEVNULL if QUIET_CHILDREN else None
    stderr = subprocess.DEVNULL if QUIET_CHILDREN else None

    ollama_proc: Optional[subprocess.Popen] = None
    monitor_proc: Optional[subprocess.Popen] = None

    try:
        ollama_proc = subprocess.Popen(
            ["ollama", "serve"],
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
        )

        if not wait_for_ollama_ready(base_url, timeout_s=12.0):
            print("[error] Ollama server did not become ready in time.")
            return 2

        # 2) Start monitor for THIS script PID (includes children: ollama serve)
        root_pid = os.getpid()
        print(f"PID: {root_pid}  (monitoring this process tree incl. child ollama)")
        print(f"[ollama] base_url={base_url}  model={MODEL}")
        print(f"[monitor] out={MONITOR_OUT} interval={MONITOR_INTERVAL_S}s")

        script_dir = os.path.dirname(os.path.abspath(__file__))
        monitor_path = os.path.join(script_dir, "pc_test", "monitor_process.py")

        monitor_proc = subprocess.Popen(
            [sys.executable, monitor_path, str(root_pid), MONITOR_OUT, str(MONITOR_INTERVAL_S)],
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
        )

        # 3) Warmup idle window (capture VRAM baseline after weights load)
        if WARMUP_SECONDS > 0:
            print(f"[phase] warmup idle {WARMUP_SECONDS}s")
            time.sleep(WARMUP_SECONDS)

        # 4) One blocking generation (this is the window you care about)
        print("[phase] generate start")
        response = ask_once(base_url=base_url, model=MODEL, prompt=PROMPT)
        print("[phase] generate done")

        if PRINT_RESPONSE:
            print("\n--- response ---\n")
            print(response)
            print("\n--- end ---\n")

        # 5) After idle window (capture post-gen steady state)
        if AFTER_SECONDS > 0:
            print(f"[phase] after idle {AFTER_SECONDS}s")
            time.sleep(AFTER_SECONDS)

        print("[done] exiting")
        return 0

    except requests.exceptions.ConnectionError:
        print("[error] Cannot connect to Ollama server at", base_url)
        return 3
    except requests.HTTPError as e:
        print("[error] HTTP error:", e)
        return 4
    except KeyboardInterrupt:
        print("\n[stopped] by user")
        return 130
    finally:
        terminate_proc(monitor_proc)
        terminate_proc(ollama_proc)


if __name__ == "__main__":
    """
    PROMPTS = [
    "What should I cook for dinner tonight?",
    "I have been feeling tired after work lately and I don't have much time to cook. "
    "What are some simple and healthy meal ideas that I can prepare quickly during weekdays?"]
    """
    raise SystemExit(main())
