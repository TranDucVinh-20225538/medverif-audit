#!/usr/bin/env python3
"""One-shot C0 claim regen for expand DOSE bases (Qwen-72B + Phi-4, budget cap)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "expand"))

from c0_claim_audit import (  # noqa: E402
    C0_NO_DRUG_IN_EVIDENCE_OK,
    c0_regen_reasons,
    needs_c0_regen,
)
from llm_client import chat  # noqa: E402
from openrouter_runtime import load_tokenizer  # noqa: E402
from stage12_openrouter import GEN_OR, VAL_OR, classify_claim  # noqa: E402
from stage12_llm import (  # noqa: E402
    GEN_SYSTEM,
    VAL_SYSTEM,
    first_word,
    gen_user,
    read_jsonl,
    render,
    val_user,
    write_jsonl,
)

CAP_USD = 2.0
LEDGER = ROOT / "data" / "expand" / "c0_regen" / "api_spend.jsonl"
OUT_STATS = ROOT / "notes" / "expand_c0_regen.json"

GEN_EXTRA = (
    "Name the specific drug or drugs when the evidence names them; do not use pronouns, "
    "'the medication', or 'the drug' as the subject unless the evidence also uses only those terms. "
    "Keep every route, population, and indication qualifier from the target sentence "
    "(e.g. oral/intravenous, pediatric/adult, together with)."
)


class BudgetStop(RuntimeError):
    pass


def spent_usd() -> float:
    if not LEDGER.is_file():
        return 0.0
    total = 0.0
    for line in LEDGER.read_text().splitlines():
        if line.strip():
            total += float(json.loads(line).get("cost_usd") or 0)
    return total


def record_cost(cost: float | None, *, base_id: str, phase: str) -> None:
    if cost is None:
        return
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a") as handle:
        handle.write(json.dumps({"base_id": base_id, "phase": phase, "cost_usd": float(cost)}) + "\n")
    if spent_usd() >= CAP_USD:
        raise BudgetStop(f"C0 regen spend >= ${CAP_USD:.2f}")


def assert_budget() -> None:
    if spent_usd() >= CAP_USD:
        raise BudgetStop(f"C0 regen spend >= ${CAP_USD:.2f}")


def gen_user_regen(base: dict, reasons: list[str]) -> str:
    hint = GEN_EXTRA
    if "c0_missing_drug" in reasons:
        hint += " You must include the drug name(s) from the evidence."
    if "c0_dropped_qualifier" in reasons:
        hint += " Preserve route and population wording from the target sentence."
    row = dict(base)
    row["target_span"] = base.get("target_span_claim") or base.get("target_span_evidence") or ""
    return f"{gen_user(row)}\n\nAdditional instruction:\n{hint}\n\nPatient-facing sentence:"


def generate_one(base: dict, reasons: list[str], gen_tok, provider: str | None) -> dict:
    assert_budget()
    prompt = render(gen_tok, GEN_SYSTEM, gen_user_regen(base, reasons))
    resp = chat(
        model=GEN_OR,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=256,
        temperature=0.0,
        seed=42,
        provider=provider,
        allow_fallbacks=False,
    )
    record_cost(resp.cost_usd, base_id=base["id"], phase="generator")
    finish = "length" if resp.completion_tokens >= 256 else "stop"
    return {"raw_output": resp.text, "finish_reason": finish}


def validate_one(base_id: str, evidence: str, claim: str, val_tok, provider: str | None) -> str:
    assert_budget()
    prompt = render(val_tok, VAL_SYSTEM, val_user(evidence, claim))
    resp = chat(
        model=VAL_OR,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=16,
        temperature=0.0,
        provider=provider,
        allow_fallbacks=False,
    )
    record_cost(resp.cost_usd, base_id=base_id, phase="validator")
    word = first_word(resp.text or "")
    if word not in {"yes", "no"}:
        return "UNPARSEABLE"
    return "YES" if word == "yes" else "NO"


def row_for_classify(base: dict) -> dict:
    span = base.get("target_span_claim") or base.get("target_span_evidence") or ""
    return {
        "cand_id": base["id"],
        "type": base["type"],
        "evidence": base["evidence"],
        "target_sentence": base.get("target_sentence") or "",
        "target_span": span,
        "source_passage_id": base.get("source_passage_id"),
        "evidence_span_start": base.get("evidence_span_start"),
        "evidence_span_end": base.get("evidence_span_end"),
        "book": base.get("book"),
        "dose_number": base.get("dose_number"),
        "dose_unit": base.get("dose_unit"),
        "polarity_cue": base.get("polarity_cue"),
    }


def apply_claim_to_base(base: dict, built: dict) -> dict:
    out = dict(base)
    out["claim"] = built["claim"]
    out["target_span_claim"] = built["target_span_claim"]
    out["claim_span_start"] = built["claim_span_start"]
    out["claim_span_end"] = built["claim_span_end"]
    out.pop("c0_qc_fail", None)
    out["c0_regen"] = True
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bases", type=Path, default=ROOT / "data" / "expand" / "bases_main.jsonl")
    parser.add_argument("--pairs", type=Path, default=ROOT / "data" / "expand" / "base_pairs.jsonl")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    bases = read_jsonl(args.bases)
    by_id = {b["id"]: b for b in bases}
    todo = [
        b
        for b in bases
        if b.get("type") == "DOSE" and b["id"] not in C0_NO_DRUG_IN_EVIDENCE_OK and needs_c0_regen(b)
    ]
    todo.sort(key=lambda r: r["id"])

    stats: Counter = Counter()
    stats["candidates"] = len(todo)

    if args.dry_run:
        print(json.dumps({"candidates": len(todo), "ids": [b["id"] for b in todo]}, indent=2))
        return

    gen_provider = os.environ.get("MEDVERIF_EXPAND_GEN_PROVIDER") or os.environ.get(
        "MEDVERIF_V1_PROVIDER", "DeepInfra"
    )
    val_provider = os.environ.get("MEDVERIF_EXPAND_VAL_PROVIDER") or None
    gen_tok = load_tokenizer(os.environ.get("MEDVERIF_EXPAND_GEN_TOKENIZER", "Qwen/Qwen2.5-72B-Instruct"))
    val_tok = load_tokenizer(
        os.environ.get("MEDVERIF_EXPAND_VAL_TOKENIZER", "microsoft/phi-4"),
        revision=os.environ.get(
            "MEDVERIF_EXPAND_VAL_REV", "2db69c1c3e91a05d2c64a3185acfbaf36f744e25"
        ),
    )

    regen_log: list[dict] = []
    for base in todo:
        bid = base["id"]
        reasons = c0_regen_reasons(base)
        stats["regenerated"] += 1
        try:
            raw = generate_one(base, reasons, gen_tok, gen_provider)
            built, fail = classify_claim(row_for_classify(base), raw)
            if fail or not built:
                stats["dropped"] += 1
                by_id[bid]["c0_qc_fail"] = reasons[0]
                regen_log.append({"base_id": bid, "status": "drop_gen", "reason": fail})
                continue
            label = validate_one(bid, built["evidence"], built["claim"], val_tok, val_provider)
            trial = apply_claim_to_base(base, built)
            still = c0_regen_reasons(trial)
            if label != "YES" or still:
                reason = still[0] if still else ("validator_unparseable" if label == "UNPARSEABLE" else "validator_no")
                by_id[bid]["c0_qc_fail"] = reason if reason.startswith("c0_") else reasons[0]
                stats["dropped"] += 1
                regen_log.append({"base_id": bid, "status": "drop_post", "reason": reason, "label": label})
                continue
            by_id[bid] = trial
            stats["fixed"] += 1
            regen_log.append({"base_id": bid, "status": "fixed", "reasons": reasons})
        except BudgetStop as exc:
            stats["budget_stop"] = str(exc)
            break

    updated = [by_id[b["id"]] for b in bases]
    write_jsonl(args.bases, updated)
    if args.pairs.is_file():
        pairs = read_jsonl(args.pairs)
        pair_by = {p["id"]: p for p in pairs}
        for bid, b in by_id.items():
            if bid not in pair_by:
                continue
            for key in (
                "claim",
                "target_span_claim",
                "claim_span_start",
                "claim_span_end",
                "c0_regen",
            ):
                if key in b:
                    pair_by[bid][key] = b[key]
            if b.get("c0_qc_fail"):
                pair_by[bid]["c0_qc_fail"] = b["c0_qc_fail"]
            else:
                pair_by[bid].pop("c0_qc_fail", None)
        write_jsonl(args.pairs, pairs)

    report = {
        "cap_usd": CAP_USD,
        "spent_usd": spent_usd(),
        "counts": dict(stats),
    }
    OUT_STATS.parent.mkdir(parents=True, exist_ok=True)
    OUT_STATS.write_text(json.dumps(report, indent=2) + "\n")
    log_path = ROOT / "data" / "expand" / "c0_regen" / "regen_log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in regen_log) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
