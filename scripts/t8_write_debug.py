#!/usr/bin/env python3
"""15-row T8 debug dump for conversion / truncation review."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from general_quantity import explain_format_quantity_mismatch  # noqa: E402
from verifiers.v1b_medscore import TOK_MODEL, TOK_REV, format_input, render  # noqa: E402

INV = ROOT / "data/t8/instances_aggrefact_inv.jsonl"
SCORES = ROOT / "results/raw/t8/v1b_medscore.jsonl"
SCORES_C0 = ROOT / "results/raw/t8/v1b_medscore_c0.jsonl"
OUT = ROOT / "notes/t8_debug.md"
SEED = 2026
N = 15


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def score_map() -> dict[str, dict]:
    m = {}
    for path in (SCORES, SCORES_C0):
        if path.is_file():
            for row in read_jsonl(path):
                m[row["instance_id"]] = row
    return m


def doc_tokens(tokenizer, evidence: str, claim: str) -> dict:
    user = format_input(evidence, claim)
    prompt = render(tokenizer, evidence, claim)
    ev_ids = tokenizer.encode(evidence, add_special_tokens=False)
    user_ids = tokenizer.encode(user, add_special_tokens=False)
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=False)
    return {
        "evidence_chars": len(evidence),
        "evidence_tokens": len(ev_ids),
        "user_message_tokens": len(user_ids),
        "full_prompt_tokens": len(prompt_ids),
    }


def conversion_note(row: dict) -> str:
    c0 = row.get("claim_c0") or ""
    if row.get("condition") == "T8-aggrefact-inv":
        edited = row.get("claim") or ""
        ex = explain_format_quantity_mismatch(edited, row.get("evidence") or "")
    else:
        edited = row.get("evidence") or ""
        ex = explain_format_quantity_mismatch(c0, edited)
    if ex:
        return f"{ex['mismatch_label']}: `{ex['claim_span']}` vs `{ex['doc_span']}`"
    return f"unit_pair={row.get('unit_pair')} edit_kind={row.get('edit_kind')}"


def main() -> None:
    inv = read_jsonl(INV)
    by_base: dict[str, dict] = {}
    for row in inv:
        by_base.setdefault(row["base_id"], {})[row["condition"]] = row

    rng = random.Random(SEED)
    bases = list(by_base.keys())
    rng.shuffle(bases)
    pick = bases[:N]

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(TOK_MODEL, revision=TOK_REV)
    scores = score_map()

    lines = [
        "# T8 unit-sample debug (15 bases)",
        "",
        "Checklist: exact conversion on measured quantity (not year/id/page #); MedScore uses **full** evidence string in prompt (see token counts).",
        "",
    ]

    for i, bid in enumerate(pick, 1):
        parts = by_base[bid]
        inv_row = parts.get("T8-aggrefact-inv")
        e1_row = parts.get("T8-aggrefact-e1-unit")
        row = inv_row or e1_row or next(iter(parts.values()))
        c0_claim = row.get("claim_c0") or ""
        doc = row.get("evidence_c0") or ""
        tok = doc_tokens(tokenizer, doc, c0_claim)
        inv_claim = (inv_row or {}).get("claim") or "— (no INV row for base)"
        e1_claim = (e1_row or {}).get("claim") or c0_claim
        e1_ev = (e1_row or {}).get("evidence") or doc

        lines += [
            f"## {i}. `{bid}` ({row.get('source_dataset')}) label={row.get('aggrefact_label')}",
            "",
            f"- Evidence tokens (raw doc): **{tok['evidence_tokens']}** (chars {tok['evidence_chars']})",
            f"- User message tokens (doc+claim C0): **{tok['user_message_tokens']}**; chat prompt tokens: **{tok['full_prompt_tokens']}**",
            f"- Conversion note: {conversion_note(inv_row or row)}",
            "",
            "### Original claim (C0)",
            "```",
            c0_claim[:2000],
            "```",
            "",
            "### INV claim",
            "```",
            inv_claim[:2000] if inv_claim != "— (no INV row for base)" else inv_claim,
            "```",
            "",
            "### E1-unit (claim unchanged; edited evidence excerpt)",
            "```",
            f"claim: {e1_claim[:800]}",
            "---",
            f"evidence: {e1_ev[:1200]}",
            "```",
            "",
        ]
        c0_id = f"{bid}__{row.get('source_dataset')}__c0"
        sc0 = scores.get(c0_id, {})
        lines += [
            f"### V1b C0 → {sc0.get('verdict', 'not scored')}",
            "```",
            (sc0.get("raw_output") or "(missing)")[:1500],
            "```",
            "",
        ]
        for cond, r in parts.items():
            sc = scores.get(r["instance_id"], {})
            lines += [
                f"### V1b `{cond}` → {sc.get('verdict', 'not scored')}",
                "```",
                (sc.get("raw_output") or "(missing)")[:1500],
                "```",
                "",
            ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
