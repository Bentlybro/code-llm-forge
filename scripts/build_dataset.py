"""
Build the mixed fine-tuning dataset and push to HuggingFace.

Usage:
    pip install datasets huggingface_hub
    huggingface-cli login
    python build_dataset.py
"""

import json
import random
from datasets import load_dataset, Dataset

random.seed(42)


# ── Formatters ───────────────────────────────────────────────────────────────

def fmt_opencodeinstruct(ex):
    q = ex.get("input", "")
    a = ex.get("output", "")
    if not q or not a or len(a) < 20:
        return None
    return [{"role": "user", "content": q}, {"role": "assistant", "content": a}]


def fmt_magicoder(ex):
    q = ex.get("problem", ex.get("instruction", ""))
    a = ex.get("solution", ex.get("response", ""))
    if not q or not a or len(a) < 20:
        return None
    return [{"role": "user", "content": q}, {"role": "assistant", "content": a}]


def fmt_hermes(ex):
    convos = ex.get("conversations", [])
    if not convos or len(convos) < 2:
        return None
    role_map = {"system": "system", "human": "user", "gpt": "assistant", "tool": "user"}
    msgs = []
    for turn in convos:
        role = role_map.get(turn.get("from", ""), None)
        if role is None:
            continue
        value = turn.get("value", "")
        if not value:
            continue
        if turn.get("from") == "tool":
            value = f"[Tool Response]\n{value}"
        msgs.append({"role": role, "content": value})
    return msgs if len(msgs) >= 2 else None


def fmt_fc_sharegpt(ex):
    convos = ex.get("conversations", [])
    if not convos or len(convos) < 2:
        return None
    role_map = {
        "system": "system",
        "human": "user",
        "assistant": "assistant",
        "function_response": "user",
    }
    msgs = []
    for turn in convos:
        role = role_map.get(turn.get("from", ""), None)
        if role is None:
            continue
        value = turn.get("value", "")
        if not value:
            continue
        if turn.get("from") == "function_response":
            value = f"[Tool Response]\n{value}"
        msgs.append({"role": role, "content": value})
    return msgs if len(msgs) >= 2 else None


# ── Download & Filter ────────────────────────────────────────────────────────

print("=" * 60)
print("Building mixed fine-tuning dataset")
print("=" * 60)

# 1. OpenCodeInstruct — filter from 5M streaming
print("\n[1/4] OpenCodeInstruct (streaming + filtering)...")
ds_oci = load_dataset("nvidia/OpenCodeInstruct", split="train", streaming=True)

oci_samples = []
seen = 0
for ex in ds_oci:
    seen += 1
    if seen % 500_000 == 0:
        print(f"  Scanned {seen:,} / ~5M ... kept {len(oci_samples):,}")
    try:
        score = float(ex.get("average_test_score", 0))
        if score < 1.0:
            continue
        output = ex.get("output", "")
        if not output or len(output) < 50:
            continue
    except (ValueError, TypeError):
        continue
    oci_samples.append(ex)
    if len(oci_samples) >= 60_000:
        break

print(f"  Filtered to {len(oci_samples):,} from {seen:,} scanned")

# 2. Magicoder OSS
print("\n[2/4] Magicoder-OSS-Instruct-75K...")
ds_magic_oss = load_dataset("ise-uiuc/Magicoder-OSS-Instruct-75K", split="train")
print(f"  {len(ds_magic_oss):,} samples")

# 3. Function Calling
print("\n[3/4] Function Calling datasets...")
ds_hermes_fc = load_dataset("NousResearch/hermes-function-calling-v1", "func_calling_singleturn", split="train")
ds_hermes_multi = load_dataset("NousResearch/hermes-function-calling-v1", "func_calling", split="train")
ds_fc_sharegpt = load_dataset("hypervariance/function-calling-sharegpt", split="train")
print(f"  Hermes single: {len(ds_hermes_fc):,}")
print(f"  Hermes multi:  {len(ds_hermes_multi):,}")
print(f"  FC-ShareGPT:   {len(ds_fc_sharegpt):,}")

# 4. Magicoder Evol
print("\n[4/4] Magicoder-Evol-Instruct-110K...")
ds_magic_evol = load_dataset("ise-uiuc/Magicoder-Evol-Instruct-110K", split="train")
print(f"  {len(ds_magic_evol):,} samples")


# ── Format & Mix ─────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("Formatting and mixing...")
print("=" * 60)

all_samples = []

# OpenCodeInstruct — 30K
random.shuffle(oci_samples)
count = 0
for ex in oci_samples[:30_000]:
    r = fmt_opencodeinstruct(ex)
    if r:
        all_samples.append({"conversations": r})
        count += 1
print(f"  OpenCodeInstruct: {count:,}")

# Magicoder-OSS — 25K
indices = list(range(len(ds_magic_oss)))
random.shuffle(indices)
count = 0
for i in indices[:25_000]:
    r = fmt_magicoder(ds_magic_oss[i])
    if r:
        all_samples.append({"conversations": r})
        count += 1
print(f"  Magicoder-OSS:    {count:,}")

# Hermes FC — all of it
count = 0
for ex in ds_hermes_fc:
    r = fmt_hermes(ex)
    if r:
        all_samples.append({"conversations": r})
        count += 1
for ex in ds_hermes_multi:
    r = fmt_hermes(ex)
    if r:
        all_samples.append({"conversations": r})
        count += 1
hermes_count = count

# FC-ShareGPT — fill to 20K total tool calling
fc_target = 20_000 - hermes_count
indices = list(range(len(ds_fc_sharegpt)))
random.shuffle(indices)
fc_count = 0
for i in indices[:max(fc_target, 0)]:
    r = fmt_fc_sharegpt(ds_fc_sharegpt[i])
    if r:
        all_samples.append({"conversations": r})
        fc_count += 1
print(f"  Hermes FC:        {hermes_count:,}")
print(f"  FC-ShareGPT:      {fc_count:,}")

# Magicoder-Evol — 5K
indices = list(range(len(ds_magic_evol)))
random.shuffle(indices)
count = 0
for i in indices[:5_000]:
    r = fmt_magicoder(ds_magic_evol[i])
    if r:
        all_samples.append({"conversations": r})
        count += 1
print(f"  Magicoder-Evol:   {count:,}")

random.shuffle(all_samples)
print(f"\n  TOTAL: {len(all_samples):,} samples")


# ── Push to HuggingFace ─────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("Pushing to HuggingFace...")
print("=" * 60)

ds = Dataset.from_list(all_samples)
print(f"  Dataset: {len(ds):,} rows")
print(f"  Columns: {ds.column_names}")
print(f"  Sample: {str(ds[0])[:200]}...")

repo_id = "Bentlybro/gemma4-code-tools-80k"
ds.push_to_hub(repo_id, private=False)
print(f"\n  Pushed to https://huggingface.co/datasets/{repo_id}")
print("  Done!")
