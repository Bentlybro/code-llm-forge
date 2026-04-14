"""
BFCL (Berkeley Function Calling Leaderboard) wrapper.

BFCL is the gold standard for function calling evaluation.
Categories: simple, multiple, parallel, parallel_multiple, relevance, live_*

Install: pip install bfcl-eval

BFCL talks to a local server via environment variables. We set them before
calling the CLI so no manual .env setup is needed.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def run_bfcl(model_cfg: dict, categories: list[str], output_dir: str) -> dict:
    """
    Run BFCL benchmark against a local llama.cpp server.
    Returns dict with scores per category.
    """
    os.makedirs(output_dir, exist_ok=True)

    # BFCL reads endpoint config from env vars
    env = os.environ.copy()

    # Parse host and port from base_url (e.g. "http://localhost:8080/v1")
    url = model_cfg["base_url"].rstrip("/v1").rstrip("/")
    env["REMOTE_OPENAI_BASE_URL"] = model_cfg["base_url"]
    env["REMOTE_OPENAI_API_KEY"]  = model_cfg["api_key"]

    categories_str = ",".join(categories)
    results = {}

    print(f"\n  Running BFCL [{categories_str}] against {model_cfg['label']}...")

    # Step 1: Generate responses
    gen_cmd = [
        sys.executable, "-m", "bfcl", "generate",
        "--model",         model_cfg["model"],
        "--test-category", categories_str,
        "--skip-server-setup",
        "--result-dir",    output_dir,
    ]

    try:
        proc = subprocess.run(gen_cmd, capture_output=True, text=True, env=env, timeout=3600)
        if proc.returncode != 0:
            print(f"  ✗ BFCL generate failed:\n{proc.stderr[-500:]}")
            return {"model": model_cfg["label"], "bfcl": {"error": proc.stderr[-200:]}}
    except subprocess.TimeoutExpired:
        return {"model": model_cfg["label"], "bfcl": {"error": "TIMEOUT during generate"}}

    # Step 2: Evaluate results
    eval_cmd = [
        sys.executable, "-m", "bfcl", "evaluate",
        "--model",         model_cfg["model"],
        "--test-category", categories_str,
        "--result-dir",    output_dir,
    ]

    try:
        proc = subprocess.run(eval_cmd, capture_output=True, text=True, env=env, timeout=600)

        # Try to parse JSON output
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    data = json.loads(line)
                    results = data
                    break
                except json.JSONDecodeError:
                    pass

        if not results:
            # Fallback: print raw output for the user to read
            results = {"raw_output": proc.stdout[-1000:]}

        print(f"  ✓ BFCL complete. Results: {output_dir}")

    except subprocess.TimeoutExpired:
        results = {"error": "TIMEOUT during evaluate"}
    except Exception as e:
        results = {"error": str(e)}

    return {"model": model_cfg["label"], "bfcl": results}
