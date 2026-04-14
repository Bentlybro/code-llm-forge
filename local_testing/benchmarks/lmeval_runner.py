"""
lm-evaluation-harness wrapper for reasoning benchmarks.

Runs GSM8K (grade school math) and any other specified tasks against a
local llama.cpp OpenAI-compatible server.

Install: pip install lm-eval[api]
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def run_lm_eval(model_cfg: dict, tasks: str, output_dir: str) -> dict:
    """
    Run lm-evaluation-harness against a local llama.cpp server.

    tasks: comma-separated task names, e.g. "gsm8k_cot_llama"
    Returns dict with per-task scores.
    """
    os.makedirs(output_dir, exist_ok=True)
    out_path = Path(output_dir) / "lm_eval_results.json"

    print(f"\n  Running lm-eval [{tasks}] against {model_cfg['label']}...")

    model_args = ",".join([
        f"base_url={model_cfg['base_url']}",
        "num_concurrent=4",
        "max_retries=3",
        "tokenized_requests=False",
    ])

    cmd = [
        sys.executable, "-m", "lm_eval",
        "--model",              "local-chat-completions",
        "--model_args",         model_args,
        "--tasks",              tasks,
        "--apply_chat_template",
        "--output_path",        str(out_path),
        "--log_samples",
    ]

    env = os.environ.copy()
    env["OPENAI_API_KEY"] = model_cfg["api_key"]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=3600)

        scores = {}

        # Try reading the JSON output file first
        if out_path.exists():
            try:
                with open(out_path) as f:
                    data = json.load(f)
                results_section = data.get("results", {})
                for task_name, metrics in results_section.items():
                    scores[task_name] = {
                        k: v for k, v in metrics.items()
                        if not k.endswith("_stderr") and k != "alias"
                    }
            except Exception:
                pass

        # Fallback: parse stdout table
        if not scores:
            for line in proc.stdout.splitlines():
                if "|" in line and "acc" in line.lower():
                    scores["raw_line"] = line.strip()

        if proc.returncode != 0 and not scores:
            print(f"  ✗ lm-eval failed:\n{proc.stderr[-400:]}")
            return {"model": model_cfg["label"], "lm_eval": {"error": proc.stderr[-200:]}}

        print(f"  ✓ lm-eval complete: {scores}")
        return {"model": model_cfg["label"], "lm_eval": scores}

    except subprocess.TimeoutExpired:
        return {"model": model_cfg["label"], "lm_eval": {"error": "TIMEOUT"}}
    except Exception as e:
        return {"model": model_cfg["label"], "lm_eval": {"error": str(e)}}
