"""
Main benchmark runner — sequential single-server mode.

Workflow:
    1. llama-server -m base_model.gguf --port 8080 --n-gpu-layers 99
       python run_all.py --model base --quick-only

    2. Ctrl+C server, swap model:
       llama-server -m finetuned.gguf --port 8080 --n-gpu-layers 99
       python run_all.py --model finetuned --quick-only

    3. Compare saved results:
       python run_all.py --compare

Other flags:
    --model base|finetuned   run only one model (default: whichever server is up)
    --quick-only             skip EvalPlus/BFCL/lm-eval (~10 min vs ~90 min)
    --compare                diff the two most recent saved results, no server needed
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table

import config
from benchmarks.quick_test import run_quick_benchmark
from benchmarks.evalplus_runner import run_evalplus
from benchmarks.bfcl_runner import run_bfcl
from benchmarks.lmeval_runner import run_lm_eval

console = Console()


def check_server(model_cfg: dict) -> bool:
    """Ping the llama.cpp server to make sure it's up."""
    import urllib.request
    try:
        url = model_cfg["base_url"].rstrip("/") + "/models"
        urllib.request.urlopen(url, timeout=5)
        return True
    except Exception:
        return False


def run_for_model(model_key: str, model_cfg: dict, args) -> dict:
    label = model_cfg["label"]
    console.rule(f"[bold cyan]{label}")

    if not check_server(model_cfg):
        console.print(f"[red]✗ Server not reachable at {model_cfg['base_url']} — skipping {label}[/red]")
        console.print(f"  Start it with: llama-server -m your_model.gguf --port {model_cfg['base_url'].split(':')[-1].split('/')[0]} --n-gpu-layers 99")
        return {"model": label, "skipped": True}

    run_dir = Path(config.RESULTS_DIR) / model_key / datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)

    all_results = {"model": label, "timestamp": datetime.now().isoformat()}

    # ── Quick custom suite ──────────────────────────────────────────────────
    if config.RUN_QUICK or args.quick_only:
        console.print("\n[bold]Running quick custom suite...[/bold]")
        quick = run_quick_benchmark(model_cfg, config.GENERATION)
        all_results["quick"] = quick
        _save(run_dir / "quick.json", quick)

    if args.quick_only:
        return all_results

    # ── EvalPlus (coding) ───────────────────────────────────────────────────
    if config.RUN_EVALPLUS:
        console.print("\n[bold]Running EvalPlus (HumanEval+ / MBPP+)...[/bold]")
        ep = run_evalplus(model_cfg, config.EVALPLUS_DATASETS, str(run_dir / "evalplus"))
        all_results["evalplus"] = ep
        _save(run_dir / "evalplus.json", ep)

    # ── BFCL (function calling) ─────────────────────────────────────────────
    if config.RUN_BFCL:
        console.print("\n[bold]Running BFCL (function calling leaderboard)...[/bold]")
        bfcl = run_bfcl(model_cfg, config.BFCL_CATEGORIES, str(run_dir / "bfcl"))
        all_results["bfcl"] = bfcl
        _save(run_dir / "bfcl.json", bfcl)

    # ── lm-eval (reasoning) ─────────────────────────────────────────────────
    if config.RUN_LM_EVAL:
        console.print("\n[bold]Running lm-eval (GSM8K reasoning)...[/bold]")
        lme = run_lm_eval(model_cfg, config.LM_EVAL_TASKS, str(run_dir / "lm_eval"))
        all_results["lm_eval"] = lme
        _save(run_dir / "lm_eval.json", lme)

    _save(run_dir / "full_results.json", all_results)
    console.print(f"\n[green]Results saved to {run_dir}[/green]")
    return all_results


def print_comparison(results: dict[str, dict]):
    """Print a side-by-side comparison table."""
    console.rule("[bold yellow]COMPARISON SUMMARY")

    model_keys = list(results.keys())
    if len(model_keys) < 2:
        console.print("[yellow]Only one model ran — nothing to compare.[/yellow]")
        return

    a_key, b_key = model_keys[0], model_keys[1]
    a, b = results[a_key], results[b_key]

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Category",   style="bold", width=28)
    table.add_column(a.get("model", a_key), justify="center", width=18)
    table.add_column(b.get("model", b_key), justify="center", width=18)
    table.add_column("Delta",      justify="center", width=10)

    def fmt_pct(val):
        if val is None:
            return "N/A"
        return f"{val:.0%}"

    def quick_row(label, cat, results_a, results_b):
        def get_pct(r):
            try:
                s = r["quick"]["summary"][cat]
                return s["pct"]
            except (KeyError, TypeError):
                return None
        va, vb = get_pct(results_a), get_pct(results_b)
        if va is not None and vb is not None:
            delta = vb - va
            d_str = f"[green]+{delta:.0%}[/green]" if delta > 0 else (f"[red]{delta:.0%}[/red]" if delta < 0 else "0%")
        else:
            d_str = "N/A"
        table.add_row(label, fmt_pct(va), fmt_pct(vb), d_str)

    quick_row("Quick: Function Calling", "function_calling", a, b)
    quick_row("Quick: Coding",           "coding",           a, b)
    quick_row("Quick: Reasoning",        "reasoning",        a, b)
    quick_row("Quick: Overall",          "overall",          a, b)

    # EvalPlus
    for dataset in config.EVALPLUS_DATASETS:
        def get_ep(r):
            try:
                return r["evalplus"]["evalplus"][dataset]["pass@1"]
            except (KeyError, TypeError):
                return None
        va, vb = get_ep(a), get_ep(b)
        if va is not None and vb is not None:
            delta = vb - va
            d_str = f"[green]+{delta:.1%}[/green]" if delta > 0 else (f"[red]{delta:.1%}[/red]" if delta < 0 else "0%")
        else:
            d_str = "N/A"
        table.add_row(f"EvalPlus: {dataset}", fmt_pct(va), fmt_pct(vb), d_str)

    console.print(table)


def _save(path: Path, data: dict):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_latest_result(model_key: str) -> dict | None:
    """Load the most recently saved full_results.json for a model."""
    base = Path(config.RESULTS_DIR) / model_key
    if not base.exists():
        return None
    runs = sorted(base.iterdir(), reverse=True)
    for run in runs:
        result_file = run / "full_results.json"
        if result_file.exists():
            with open(result_file) as f:
                return json.load(f)
    return None


def main():
    parser = argparse.ArgumentParser(description="LLM benchmark runner for local llama.cpp models")
    parser.add_argument("--model",      choices=list(config.MODELS.keys()), default=None,
                        help="Which model to benchmark")
    parser.add_argument("--quick-only", action="store_true",
                        help="Only run the fast custom suite, skip EvalPlus/BFCL/lm-eval")
    parser.add_argument("--compare",    action="store_true",
                        help="Compare the most recent saved results for both models (no server needed)")
    args = parser.parse_args()

    os.makedirs(config.RESULTS_DIR, exist_ok=True)

    # Compare-only mode — load saved results and print table
    if args.compare:
        console.rule("[bold yellow]Loading saved results for comparison")
        saved = {}
        for key in config.MODELS:
            r = load_latest_result(key)
            if r:
                saved[key] = r
                console.print(f"  [green]✓[/green] {key}: {r.get('timestamp', 'unknown time')}")
            else:
                console.print(f"  [red]✗[/red] {key}: no saved results found in {config.RESULTS_DIR}/{key}/")
        if len(saved) >= 2:
            print_comparison(saved)
        else:
            console.print("[red]Need results for both models to compare. Run each model first.[/red]")
        return

    # Normal run mode
    if args.model is None:
        console.print("[yellow]No --model specified. Detecting which server is up...[/yellow]")
        for key, cfg in config.MODELS.items():
            if check_server(cfg):
                args.model = key
                console.print(f"  Server found at {cfg['base_url']} — running as [bold]{key}[/bold]")
                break
        if args.model is None:
            console.print("[red]No server reachable. Start llama-server first.[/red]")
            return

    model_cfg = config.MODELS[args.model]
    result = run_for_model(args.model, model_cfg, args)

    # Check if we have results for the other model and auto-compare
    other_key = [k for k in config.MODELS if k != args.model]
    if other_key:
        other_result = load_latest_result(other_key[0])
        if other_result:
            console.print(f"\n[cyan]Found saved results for '{other_key[0]}' — showing comparison:[/cyan]")
            print_comparison({args.model: result, other_key[0]: other_result})


if __name__ == "__main__":
    main()
