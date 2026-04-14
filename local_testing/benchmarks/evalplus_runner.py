"""
EvalPlus wrapper — HumanEval+ and MBPP+ via llama.cpp OpenAI-compatible API.

EvalPlus adds 80x more test cases than original HumanEval/MBPP.
Runs as a subprocess so it inherits the correct Python env.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def run_evalplus(model_cfg: dict, datasets: list[str], output_dir: str) -> dict:
    """
    Run EvalPlus benchmarks against a local llama.cpp server.
    Returns dict of {dataset: {pass@1, details_path}}.
    """
    os.makedirs(output_dir, exist_ok=True)
    results = {}

    for dataset in datasets:
        print(f"\n  Running EvalPlus [{dataset}] against {model_cfg['label']}...")
        out_path = Path(output_dir) / f"evalplus_{dataset}"

        cmd = [
            sys.executable, "-m", "evalplus.evaluate",
            "--model",    model_cfg["model"],
            "--dataset",  dataset,
            "--backend",  "openai",
            "--base-url", model_cfg["base_url"],
            "--output",   str(out_path),
            "--greedy",                 # deterministic (temp=0)
            "--parallel", "4",          # concurrent requests to llama.cpp
        ]

        env = os.environ.copy()
        env["OPENAI_API_KEY"] = model_cfg["api_key"]

        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True,
                env=env, timeout=3600
            )

            # Parse pass@1 from stdout
            pass_at_1 = None
            for line in proc.stdout.splitlines():
                if "pass@1" in line.lower():
                    # EvalPlus prints something like: "pass@1: 0.542"
                    parts = line.split(":")
                    if len(parts) >= 2:
                        try:
                            pass_at_1 = float(parts[-1].strip())
                        except ValueError:
                            pass

            if proc.returncode != 0:
                print(f"  ✗ EvalPlus [{dataset}] failed:")
                print(proc.stderr[-500:])
                results[dataset] = {"error": proc.stderr[-200:]}
            else:
                results[dataset] = {
                    "pass@1":       pass_at_1,
                    "details_path": str(out_path),
                    "stdout_tail":  proc.stdout[-300:],
                }
                print(f"  ✓ {dataset} pass@1: {pass_at_1}")

        except subprocess.TimeoutExpired:
            results[dataset] = {"error": "TIMEOUT"}
            print(f"  ✗ EvalPlus [{dataset}] timed out")
        except Exception as e:
            results[dataset] = {"error": str(e)}
            print(f"  ✗ EvalPlus [{dataset}] error: {e}")

    return {"model": model_cfg["label"], "evalplus": results}
