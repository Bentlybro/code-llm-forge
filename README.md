# 🔨 Code LLM Forge

**Build, fine-tune, and rigorously benchmark your own coding LLM that excels at code generation, tool calling, AND reasoning.**

> This project provides everything you need to go from a base model to a production-ready coding assistant that you can run locally with llama.cpp.

---

## 🎯 Project Goals

1. **Fine-tune a coding LLM** that genuinely excels at:
   - ✅ Code generation across multiple languages
   - ✅ Tool/function calling with structured JSON output
   - ✅ Chain-of-thought reasoning for complex problems
2. **Benchmark it honestly** — no reward hacking, no contaminated test sets
3. **Run it locally** via llama.cpp / Ollama on consumer hardware

---

## 🧠 Base Model Decision: Qwen2.5-Coder-7B-Instruct

After extensive research comparing 8 candidate models, we chose **Qwen2.5-Coder-7B-Instruct** as our base. Here's why:

### Why Qwen2.5-Coder-7B-Instruct Wins

| Criteria | Qwen2.5-Coder-7B | Yi-Coder-9B | DeepSeek-V2-Lite | Qwen3-8B | Llama-3.1-8B |
|----------|-------------------|-------------|-------------------|----------|--------------|
| **HumanEval** | 62% | 65% | 85% (MoE) | ~55% | ~49% |
| **Code-specific training** | 5.5T code tokens | ✅ Strong | ✅ Strong | General + code | General |
| **Native tool calling** | ✅ Built into chat template | ⚠️ Needs work | ⚠️ Needs work | ✅ Yes | ✅ Yes |
| **128K context** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **LoRA/QLoRA stability** | ✅ Excellent | ✅ Good | ⚠️ MoE complexity | ✅ Good | ✅ Excellent |
| **Fine-tuning community** | 🏆 Largest | Medium | Small | Growing | 🏆 Largest |
| **License** | Apache 2.0 | Apache 2.0 | MIT | Apache 2.0 | Llama 3.1 |
| **GGUF ecosystem** | 🏆 Best | Good | Limited | Good | 🏆 Best |

### Key Reasoning:

1. **Starting from Instruct, not Base**: Research shows that for teams with <10K curated examples, instruction-tuned models converge faster, are more stable, and resist catastrophic forgetting better. Since we're adding capabilities (tool calling + reasoning) on top of existing code skills, Instruct is the right starting point.

2. **Why not DeepSeek-V2-Lite?** Despite incredible benchmarks (85% HumanEval), MoE architectures are significantly harder to fine-tune. Expert imbalance, routing instability, and the need for specialized LoRA strategies make it risky for this project.

3. **Why not Yi-Coder-9B?** Strong model, but less community fine-tuning experience and no native tool-calling chat template. Would require more custom work.

4. **Why not Qwen3-8B?** Newer with better reasoning, but less code-specific training and smaller fine-tuning community as of April 2026.

---

## 📊 Training Strategy: Multi-Stage Pipeline

Based on research into multi-task learning, we use a **3-stage training pipeline**:

```
Stage 1: Code + Reasoning Foundation (SFT)
├── CodeFeedback-Filtered-Instruction (156K, complexity-filtered)
├── Magicoder-OSS-Instruct-75K (real OSS code)
├── Magicoder-Evol-Instruct-110K (evolved complexity)
├── open-r1/Mixture-of-Thoughts (reasoning traces)
└── Mix ratio: ~55% code, ~20% reasoning, ~25% general

Stage 2: Tool Calling Specialization (SFT)
├── NousResearch/hermes-function-calling-v1 (multi-turn)
├── glaiveai/glaive-function-calling-v2 (113K examples)
├── Gorilla OpenFunctions V2 (multi-language APIs)
└── Mix ratio: ~60% Hermes, ~25% Glaive, ~15% Gorilla

Stage 3: Preference Optimization (DPO)
├── Pairs: correct vs incorrect tool calls
├── Pairs: good vs bad reasoning chains
└── Pairs: clean vs buggy code
```

### Why Multi-Stage?

Research shows that **hard transitions between data distributions cause catastrophic forgetting**. By training code+reasoning first (related capabilities), then layering tool calling on top, we:
- Build strong code foundations before specializing
- Reduce distribution shift between stages
- Allow the model to develop shared code+reasoning representations

### Dataset Sizes & Training Time Estimates

| Stage | Dataset Size | Method | Time (A100 80GB) | Time (H100 80GB) |
|-------|-------------|--------|-------------------|-------------------|
| Stage 1 | ~340K samples | QLoRA r=32 | ~8-12 hours | ~5-8 hours |
| Stage 2 | ~180K samples | QLoRA r=16 | ~4-6 hours | ~2-4 hours |
| Stage 3 | ~20K pairs | DPO | ~2-3 hours | ~1-2 hours |
| **Total** | **~540K samples** | | **~14-21 hours** | **~8-14 hours** |

---

## 📁 Repository Structure

```
code-llm-forge/
├── README.md                          # This file
├── notebooks/
│   ├── 01_data_preparation.ipynb      # Download & combine datasets
│   ├── 02_stage1_code_reasoning.ipynb # Stage 1: Code + reasoning SFT
│   ├── 03_stage2_tool_calling.ipynb   # Stage 2: Tool calling SFT
│   ├── 04_stage3_dpo.ipynb            # Stage 3: DPO preference optimization
│   ├── 05_benchmarking_suite.ipynb    # Comprehensive benchmarking
│   └── 06_export_gguf.ipynb           # Convert to GGUF for local use
├── benchmarks/
│   ├── private_v1/                    # Private contamination-free benchmark
│   │   ├── problems/                  # Custom problems (see benchmark guide)
│   │   ├── metadata/                  # Creation dates, contamination scans
│   │   └── evaluation/               # Sealed results
│   ├── tool_calling_bench.json        # Custom tool-calling evaluation
│   └── reasoning_bench.json           # Custom reasoning evaluation
├── configs/
│   ├── stage1_config.yaml             # Stage 1 training config
│   ├── stage2_config.yaml             # Stage 2 training config
│   ├── stage3_dpo_config.yaml         # Stage 3 DPO config
│   └── benchmark_config.yaml          # Benchmark settings
├── scripts/
│   ├── prepare_datasets.py            # Dataset download & mixing
│   ├── merge_adapter.py               # Merge LoRA weights
│   └── convert_to_gguf.py            # GGUF conversion helper
└── datasets/
    └── .gitkeep                       # Datasets downloaded at runtime
```

---

## 🧪 Benchmarking Philosophy: No Reward Hacking

### The Problem with Standard Benchmarks
- **HumanEval**: Only 164 problems, public since 2021, widely contaminated
- **MBPP**: 427 problems, same contamination issues
- Models can memorize test cases and appear capable without genuine understanding

### Our Benchmarking Approach

We use a **3-tier evaluation system**:

#### Tier 1: Zero-Contamination (Primary)
| Benchmark | What It Tests | Why It's Reliable |
|-----------|--------------|-------------------|
| **LiveCodeBench** | Coding ability | Fresh problems from live competitions, post-training-cutoff |
| **Private Benchmark** | All capabilities | Custom problems we create, never published |
| **BFCL-style Tool Eval** | Function calling | Custom tool-calling scenarios with novel APIs |

#### Tier 2: Low-Contamination (Secondary)
| Benchmark | What It Tests | Why It's Useful |
|-----------|--------------|-----------------|
| **SWE-bench Lite** | Real-world engineering | Actual GitHub issues, hard to memorize |
| **BigCodeBench** | Practical coding | 1,140 diverse problems with library usage |
| **CRUXEval** | Compositional reasoning | Multi-step decomposition required |

#### Tier 3: Reference Only (For Comparison)
| Benchmark | What It Tests | Caveat |
|-----------|--------------|--------|
| **HumanEval+** | Basic coding | Assume contaminated, use only for comparison |
| **MBPP+** | Basic coding | Same caveat — reference only |

### Statistical Rigor
- **Temperature**: 0.0 for pass@1, 0.8 for pass@10
- **Samples**: Minimum 200 per benchmark tier
- **Confidence intervals**: Wilson score intervals reported
- **Contamination detection**: N-gram overlap checks against training data
- **Multiple runs**: 3 runs minimum, report mean ± std

---

## 🚀 Quick Start

### Option 1: Google Colab (Recommended)
1. Open `notebooks/01_data_preparation.ipynb` in Colab
2. Follow notebooks 02 → 03 → 04 sequentially
3. Run `05_benchmarking_suite.ipynb` to evaluate
4. Export with `06_export_gguf.ipynb`

### Option 2: Local Setup
```bash
git clone https://github.com/YOUR_USERNAME/code-llm-forge.git
cd code-llm-forge
pip install -r requirements.txt
python scripts/prepare_datasets.py
# Then open notebooks in Jupyter
```

### Running Your Fine-Tuned Model Locally
```bash
# After export, run with llama.cpp
llama-cli -m ./output/code-llm-forge-v1-Q8_0.gguf \
  -co -cnv \
  -p "You are a helpful coding assistant with tool-calling capabilities." \
  -fa -ngl 99 -c 8192
```

---

## 📚 Research Sources

- [Qwen2.5-Coder Technical Report](https://arxiv.org/abs/2409.12186)
- [PiKE: Adaptive Data Mixing for Multi-Task Learning](https://arxiv.org/html/2502.06244v1)
- [Multi-task Code LLMs: Data Mix or Model Merge?](https://arxiv.org/html/2601.21115v1)
- [LiveCodeBench](https://livecodebench.github.io/)
- [BigCodeBench](https://bigcode-bench.github.io/)
- [EvalPlus](https://evalplus.github.io/)
- [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html)
- [The 1 Billion Token Challenge: Finding the Perfect Pre-training Mix](https://huggingface.co/blog/codelion/optimal-dataset-mixing)

---

## 📜 License

This project is released under the **MIT License**. Note that fine-tuned models inherit the base model's license (Apache 2.0 for Qwen2.5-Coder).

---

*Built with 🔥 by the Code LLM Forge community*
