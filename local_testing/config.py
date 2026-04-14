"""
Local testing config.
Run one model at a time — both point to port 8080.

Workflow:
  1. llama-server -m base_model.gguf     --port 8080 --n-gpu-layers 99
     python run_all.py --model base
  2. Ctrl+C the server, swap the model file
     llama-server -m finetuned.gguf      --port 8080 --n-gpu-layers 99
     python run_all.py --model finetuned
  3. python run_all.py --compare          # compare saved results
"""

MODELS = {
    "base": {
        "label":    "Gemma4-E4B Base",
        "base_url": "http://127.0.0.1:8080/v1",
        "api_key":  "sk-no-key",   # llama.cpp doesn't check this
        "model":    "local-model", # llama.cpp ignores the model field
    },
    "finetuned": {
        "label":    "Gemma4-E4B Finetuned",
        "base_url": "http://127.0.0.1:8080/v1",
        "api_key":  "sk-no-key",
        "model":    "local-model",
    },
}

# Which benchmark suites to run (set False to skip)
RUN_QUICK      = True   # ~10 min/model — custom tests, runs first
RUN_EVALPLUS   = True   # ~30 min/model — HumanEval+ / MBPP+
RUN_BFCL       = True   # ~20 min/model — Berkeley Function Calling Leaderboard
RUN_LM_EVAL    = True   # ~20 min/model — GSM8K reasoning via lm-evaluation-harness

# lm-eval tasks to run (comma-separated)
LM_EVAL_TASKS = "gsm8k_cot_llama"

# EvalPlus datasets
EVALPLUS_DATASETS = ["humaneval", "mbpp"]

# BFCL test categories
BFCL_CATEGORIES = ["simple", "multiple", "parallel", "parallel_multiple", "relevance"]

# Generation settings (used by quick tests)
GENERATION = {
    "temperature": 0.0,   # deterministic
    "max_tokens":  1024,
    "timeout":     60,    # seconds per request
}

RESULTS_DIR = "results"
