"""Claim generation (Qwen2.5-32B-Instruct) and QC (Phi-4).

Neither model is the V1 verifier (Mistral-Small-24B) or the V4 judge (Qwen3-14B).
Temperature 0. Thinking mode does not apply to these checkpoints.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
from collections import Counter
from pathlib import Path

from perturb import perturb_one
from text_utils import first_word

GEN_MODEL = "Qwen/Qwen2.5-32B-Instruct"
GEN_REV = "5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd"
VAL_MODEL = "microsoft/phi-4"
VAL_REV = "2db69c1c3e91a05d2c64a3185acfbaf36f744e25"

GEN_SYSTEM = (
    "You write one patient-facing sentence that restates a medical fact from the evidence. "
    "The sentence must be fully supported by the evidence. Do not add facts, numbers, or advice. "
    "Copy the target span exactly, character for character. "
    "Return one sentence only, with no preamble."
)
VAL_SYSTEM = (
    "You check whether the evidence fully supports the claim. "
    "Reply with one word: YES or NO. "
    "YES only if every factual part of the claim, including numbers, units, and recommendation "
    "direction, is stated by the evidence. "
    "If the claim adds, changes, or contradicts any fact, reply NO."
)
INV_SYSTEM = (
    "You check whether two sentences mean the same thing. "
    "Reply with one word: YES or NO. "
    "YES only if the edited span is the same dose or the same recommendation as the original span. "
    "A correct unit conversion that names the same amount is YES. "
    "A different number, or a stronger or weaker recommendation, is NO."
)


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def render(tokenizer, system: str, user: str) -> str:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


def gen_user(row: dict) -> str:
    return (
        f"Evidence:\n{row['evidence']}\n\n"
        f"Target sentence:\n{row['target_sentence']}\n\n"
        f"Target span to copy exactly:\n{row['target_span']}\n\n"
        "Patient-facing sentence:"
    )


def val_user(evidence: str, claim: str) -> str:
    return f"Evidence:\n{evidence}\n\nClaim:\n{claim}"


def inv_user(original: str, edited: str, span_a: str, span_b: str) -> str:
    return (
        f"Original sentence:\n{original}\n\n"
        f"Edited sentence:\n{edited}\n\n"
        f"Original span: {span_a}\n"
        f"Edited span: {span_b}"
    )


def clean_claim(text: str) -> str:
    text = (text or "").strip()
    for prefix in ("Patient-facing sentence:", "Sentence:"):
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        text = text[1:-1].strip()
    return text


def load_llm(model: str, revision: str):
    from vllm import LLM

    return LLM(
        model=model,
        revision=revision,
        dtype="bfloat16",
        seed=42,
        trust_remote_code=True,
        max_model_len=4096,
        gpu_memory_utilization=0.90,
        download_dir=os.environ.get("HUGGINGFACE_HUB_CACHE"),
    )


def unload(llm) -> None:
    import torch

    del llm
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def generate(rows: list[dict], raw_path: Path, template_path: Path) -> list[dict]:
    from vllm import SamplingParams

    llm = load_llm(GEN_MODEL, GEN_REV)
    tokenizer = llm.get_tokenizer()
    prompts = [render(tokenizer, GEN_SYSTEM, gen_user(row)) for row in rows]
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text(
        "# Exact chat-template strings\n\n"
        f"Generator: `{GEN_MODEL}` revision `{GEN_REV}`\n\n"
        "Call: `tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)` "
        "with a system message and a user message. Temperature 0, seed 42, max_tokens 256. "
        "Thinking mode is not a parameter of this checkpoint.\n\n"
        "```\n" + prompts[0] + "\n```\n"
    )
    params = SamplingParams(temperature=0.0, max_tokens=256, seed=42)
    outputs = llm.generate(prompts, params)
    records = []
    for row, prompt, out in zip(rows, prompts, outputs):
        choice = out.outputs[0]
        records.append({
            "cand_id": row["cand_id"],
            "model": GEN_MODEL,
            "revision": GEN_REV,
            "prompt": prompt,
            "raw_output": choice.text,
            "finish_reason": choice.finish_reason,
        })
    write_jsonl(raw_path, records)
    unload(llm)
    return records


def classify_claim(row: dict, raw: dict) -> tuple[dict | None, str | None]:
    if raw["finish_reason"] == "length":
        return None, "generator_truncated"
    claim = clean_claim(raw["raw_output"])
    if not claim:
        return None, "generator_empty"
    span = row["target_span"]
    count = claim.count(span)
    if count == 0:
        return None, "span_missing_in_claim"
    if count != 1:
        return None, "span_not_unique_in_claim"
    start = claim.find(span)
    end = start + len(span)
    built = {
        "id": row["cand_id"],
        "type": row["type"],
        "evidence": row["evidence"],
        "claim": claim,
        "target_span_evidence": span,
        "target_span_claim": claim[start:end],
        "source_passage_id": row["source_passage_id"],
        "evidence_span_start": row["evidence_span_start"],
        "evidence_span_end": row["evidence_span_end"],
        "claim_span_start": start,
        "claim_span_end": end,
        "target_sentence": row["target_sentence"],
        "book": row["book"],
        "dose_number": row["dose_number"],
        "dose_unit": row["dose_unit"],
        "polarity_cue": row["polarity_cue"],
        "generator_model": GEN_MODEL,
        "generator_revision": GEN_REV,
        "generator_raw": raw["raw_output"],
    }
    return built, None


def yes_no(llm, tokenizer, system: str, users: list[str], max_tokens: int) -> list[dict]:
    from vllm import SamplingParams

    prompts = [render(tokenizer, system, user) for user in users]
    params = SamplingParams(temperature=0.0, max_tokens=max_tokens, seed=42)
    outputs = llm.generate(prompts, params)
    records = []
    for prompt, out in zip(prompts, outputs):
        choice = out.outputs[0]
        word = first_word(choice.text)
        if word not in {"yes", "no"}:
            label = "UNPARSEABLE"
        else:
            label = "YES" if word == "yes" else "NO"
        records.append({
            "prompt": prompt,
            "raw_output": choice.text,
            "finish_reason": choice.finish_reason,
            "label": label,
        })
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--limit-per-type", type=int, default=0)
    parser.add_argument("--template-note", type=Path, required=True)
    args = parser.parse_args()
    rows = read_jsonl(args.candidates)
    if args.limit_per_type:
        kept = []
        counts = Counter()
        for row in rows:
            if counts[row["type"]] >= args.limit_per_type:
                continue
            counts[row["type"]] += 1
            kept.append(row)
        rows = kept
    args.outdir.mkdir(parents=True, exist_ok=True)
    drops = Counter()
    gen_records = generate(rows, args.outdir / "generator_raw.jsonl", args.template_note)
    by_id = {rec["cand_id"]: rec for rec in gen_records}
    ruled = []
    for row in rows:
        built, reason = classify_claim(row, by_id[row["cand_id"]])
        if reason:
            drops[reason] += 1
            continue
        ruled.append(built)

    llm = load_llm(VAL_MODEL, VAL_REV)
    tokenizer = llm.get_tokenizer()
    val_users = [val_user(row["evidence"], row["claim"]) for row in ruled]
    val_out = yes_no(llm, tokenizer, VAL_SYSTEM, val_users, 16) if ruled else []
    # Append the validator template onto the generator note.
    if val_users:
        with args.template_note.open("a") as handle:
            handle.write(
                f"\nValidator and INV checker: `{VAL_MODEL}` revision `{VAL_REV}`\n\n"
                "Same call shape. Temperature 0, seed 42, max_tokens 16. "
                "Thinking mode is not a parameter of this checkpoint.\n\n"
                "```\n" + render(tokenizer, VAL_SYSTEM, val_users[0]) + "\n```\n"
            )
    supported = []
    val_raw = []
    for row, rec in zip(ruled, val_out):
        saved = {
            "id": row["id"],
            "model": VAL_MODEL,
            "revision": VAL_REV,
            "raw_output": rec["raw_output"],
            "label": rec["label"],
            "finish_reason": rec["finish_reason"],
        }
        val_raw.append(saved)
        if rec["label"] == "UNPARSEABLE":
            drops["validator_unparseable"] += 1
            continue
        if rec["label"] == "NO":
            drops["validator_no"] += 1
            continue
        row = dict(row)
        row["validator_model"] = VAL_MODEL
        row["validator_revision"] = VAL_REV
        row["validator_raw"] = rec["raw_output"]
        supported.append(row)
    write_jsonl(args.outdir / "validator_raw.jsonl", val_raw)

    pending = []
    perturb_fail = []
    for base in supported:
        got, failed = perturb_one(base)
        if failed:
            perturb_fail.extend(failed)
            drops["perturb_" + failed[0]["reason"]] += 1
            continue
        pending.extend(got)

    inv_rows = [row for row in pending if row["condition"] == "INV-claim"]
    inv_users = [
        inv_user(row["claim_c0"], row["claim"], row["diff"]["claim"]["span_before"], row["claim_span"])
        for row in inv_rows
    ]
    inv_out = yes_no(llm, tokenizer, INV_SYSTEM, inv_users, 16) if inv_users else []
    unload(llm)
    inv_raw = []
    inv_ok = set()
    for row, rec in zip(inv_rows, inv_out):
        inv_raw.append({
            "instance_id": row["instance_id"],
            "base_id": row["base_id"],
            "model": VAL_MODEL,
            "revision": VAL_REV,
            "raw_output": rec["raw_output"],
            "label": rec["label"],
        })
        if rec["label"] == "YES":
            inv_ok.add(row["base_id"])
        elif rec["label"] == "UNPARSEABLE":
            drops["inv_unparseable"] += 1
        else:
            drops["inv_meaning_rejected"] += 1
    write_jsonl(args.outdir / "inv_raw.jsonl", inv_raw)

    final = [row for row in pending if row["base_id"] in inv_ok]
    kept_ids = {row["base_id"] for row in final}
    bases = [row for row in supported if row["id"] in kept_ids]
    write_jsonl(args.outdir / "base_pairs.jsonl", bases)
    write_jsonl(args.outdir / "instances.jsonl", final)
    type_counts = Counter(row["type"] for row in bases)
    cond_counts = Counter((row["type"], row["condition"], row["magnitude"]) for row in final)
    stats = {
        "generator_model": GEN_MODEL,
        "generator_revision": GEN_REV,
        "validator_model": VAL_MODEL,
        "validator_revision": VAL_REV,
        "candidates_attempted": len(rows),
        "attempted_by_type": dict(Counter(row["type"] for row in rows)),
        "rule_passed": len(ruled),
        "validator_yes": len(supported),
        "bases_kept": len(bases),
        "bases_kept_by_type": dict(type_counts),
        "instances": len(final),
        "instances_by_type_condition_magnitude": {
            f"{a}|{b}|{c}": n for (a, b, c), n in sorted(cond_counts.items())
        },
        "drops": dict(drops),
        "perturb_failures": perturb_fail,
        "roles": {
            "claim_generator": GEN_MODEL,
            "support_validator": VAL_MODEL,
            "inv_meaning_checker": VAL_MODEL,
            "not_used": [
                "mistralai/Mistral-Small-24B-Instruct-2501",
                "Qwen/Qwen3-14B",
                "gpt-4o",
            ],
        },
    }
    (args.outdir / "llm_stats.json").write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
