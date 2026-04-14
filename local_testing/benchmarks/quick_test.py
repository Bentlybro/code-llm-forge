"""
Quick custom benchmark suite — runs in ~10 minutes per model.
Tests function calling, code generation (with execution), and reasoning.
Uses the OpenAI-compatible API directly, so works with any llama.cpp server.
"""

import json
import re
import subprocess
import sys
import tempfile
import textwrap
import time
from dataclasses import dataclass
from openai import OpenAI

from .tests_function_calling import FUNCTION_CALLING_TESTS
from .tests_coding import CODING_TESTS
from .tests_reasoning import REASONING_TESTS


@dataclass
class TestResult:
    name: str
    category: str
    passed: bool
    score: float        # 0.0 – 1.0
    detail: str = ""
    latency: float = 0.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def chat(client: OpenAI, model: str, messages: list, tools: list | None = None, **gen_kwargs):
    """Single chat completion, returns the assistant message object."""
    kwargs = dict(model=model, messages=messages, **gen_kwargs)
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message


def extract_tool_calls(message) -> list[dict]:
    """Pull tool_calls out of a chat completion message."""
    if not message.tool_calls:
        return []
    calls = []
    for tc in message.tool_calls:
        try:
            args = json.loads(tc.function.arguments)
        except json.JSONDecodeError:
            args = {}
        calls.append({"name": tc.function.name, "args": args})
    return calls


def run_python(code: str, timeout: int = 10) -> tuple[bool, str]:
    """Execute Python code in a subprocess. Returns (success, output)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(textwrap.dedent(code))
        fname = f.name
    try:
        result = subprocess.run(
            [sys.executable, fname],
            capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, (result.stdout + result.stderr).strip()
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except Exception as e:
        return False, str(e)


def extract_code(response_text: str) -> str:
    """Pull the first Python code block from a response."""
    text = response_text.strip()

    # Try explicit ```python ... ``` (with or without newline after opening tag)
    m = re.search(r"```python[^\n]*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()

    # Try any fenced block
    m = re.search(r"```[^\n]*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()

    # Response IS the fenced block (starts directly with ```)
    if text.startswith("```"):
        lines = text.splitlines()
        # Find closing fence
        end = len(lines)
        for i in range(len(lines) - 1, 0, -1):
            if lines[i].strip() == "```":
                end = i
                break
        return "\n".join(lines[1:end]).strip()

    return text


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_quick_benchmark(model_cfg: dict, gen_cfg: dict) -> dict:
    client = OpenAI(base_url=model_cfg["base_url"], api_key=model_cfg["api_key"])
    model  = model_cfg["model"]
    results: list[TestResult] = []

    # ── Function Calling ─────────────────────────────────────────────────────
    print("\n  [Function Calling]")
    for t in FUNCTION_CALLING_TESTS:
        t0 = time.time()
        try:
            msg = chat(client, model, t["messages"], tools=t["tools"],
                       temperature=gen_cfg["temperature"], max_tokens=2048)
            calls = extract_tool_calls(msg)
            passed = t["check"](calls)
            detail = f"{len(calls)} call(s): {[c['name'] for c in calls]}"
        except Exception as e:
            passed, detail = False, f"ERROR: {e}"
        latency = time.time() - t0
        results.append(TestResult(t["id"], "function_calling", passed, float(passed), detail, latency))
        print(f"    {'✓' if passed else '✗'} {t['id']:<30} {detail}")

    # ── Code Generation ──────────────────────────────────────────────────────
    print("\n  [Code Generation]")
    for t in CODING_TESTS:
        t0 = time.time()
        try:
            msg = chat(client, model,
                       [{"role": "user", "content": t["prompt"]}],
                       temperature=gen_cfg["temperature"],
                       max_tokens=gen_cfg["max_tokens"])
            code = extract_code(msg.content or "")
            test_src = code + "\n" + t["test_code"]
            ok, out = run_python(test_src)
            passed = ok and "PASS" in out
            detail = out[:120] if not passed else "PASS"
        except Exception as e:
            passed, detail = False, f"ERROR: {e}"
        latency = time.time() - t0
        results.append(TestResult(t["id"], "coding", passed, float(passed), detail, latency))
        print(f"    {'✓' if passed else '✗'} {t['id']:<30} {detail[:60]}")

    # ── Reasoning ────────────────────────────────────────────────────────────
    # Use 1024 tokens — Gemma 4 E4B is a thinking model and burns tokens on
    # internal reasoning before outputting the answer. 256 leaves no budget.
    print("\n  [Reasoning]")
    for t in REASONING_TESTS:
        t0 = time.time()
        try:
            msg = chat(client, model,
                       [{"role": "user", "content": t["prompt"]}],
                       temperature=gen_cfg["temperature"],
                       max_tokens=1024)
            answer = (msg.content or "").strip()
            # Fallback: some llama.cpp builds put content in a different field
            if not answer:
                raw = getattr(msg, "model_dump", lambda: {})()
                answer = str(raw.get("content") or raw.get("text") or "").strip()
            passed = t["check"](answer)
            detail = answer[:200]
        except Exception as e:
            passed, detail = False, f"ERROR: {e}"
        latency = time.time() - t0
        results.append(TestResult(t["id"], "reasoning", passed, float(passed), detail, latency))
        print(f"    {'✓' if passed else '✗'} {t['id']:<30} {detail[:80]}")

    # ── Aggregate ────────────────────────────────────────────────────────────
    def cat_stats(cat):
        subset = [r for r in results if r.category == cat]
        passed = sum(r.passed for r in subset)
        return {"passed": passed, "total": len(subset), "pct": passed / len(subset) if subset else 0}

    categories = ["function_calling", "coding", "reasoning"]
    summary = {cat: cat_stats(cat) for cat in categories}
    total_p = sum(r.passed for r in results)
    total_t = len(results)
    summary["overall"] = {"passed": total_p, "total": total_t, "pct": total_p / total_t if total_t else 0}

    return {
        "model":   model_cfg["label"],
        "summary": summary,
        "results": [
            {"id": r.name, "category": r.category, "passed": r.passed,
             "score": r.score, "detail": r.detail, "latency": round(r.latency, 2)}
            for r in results
        ]
    }
