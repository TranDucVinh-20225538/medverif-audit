#!/usr/bin/env python3
"""EXPLORATORY (not preregistered): does the original numeral survive as a token inside the rescaled numeral?

US_up after-M1 pairs: flag = some token (checker's own tokenizer) covering the numeral that M1 introduced
(e.g. 500000) has surface exactly equal to the original numeral (e.g. 500). Control: NS_x10 (e.g. 500 -> 5000),
same test on the ×10 numeral vs the C0 numeral. Rows come from `notes/m1_strong_final_rows.json`
(`m1_strong_run.py --final --dump-rows`), i.e. exactly the pairs/rows behind m1_strong_final.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import N_BOOT, SEED, bootstrap_rate, read_jsonl  # noqa: E402
from verifier_labels import verifier_display_name  # noqa: E402

ROWS = ROOT / "notes/m1_strong_final_rows.json"
AFTER = ROOT / "data/lane_b/m1_t7_e1_unit.jsonl"
RAW_T7 = ROOT / "data/t7/instances_e1_unit.jsonl"
MAIN = ROOT / "data/v3/instances_main.jsonl"
OUT = ROOT / "notes/m1_token_overlap_exploratory.md"
OUT_JSON = ROOT / "notes/m1_token_overlap_exploratory.json"
HF = ROOT / ".cache/huggingface"

TOKENIZERS = {
    "t6a_minicheck_roberta": "lytang/MiniCheck-RoBERTa-Large",
    "t6a_minicheck_deberta": "lytang/MiniCheck-DeBERTa-v3-Large",
    "v2a_minicheck": "lytang/MiniCheck-Flan-T5-Large",
    "t6a_alignscore_base": "roberta-base",
    "v3_alignscore": "roberta-large",
    "t6a_summac_zs": "tals/albert-xlarge-vitaminc-mnli",
    "t6a_granite_guardian": "ibm-granite/granite-guardian-3.0-2b",
    "v2b_bespoke": "bespokelabs/Bespoke-MiniCheck-7B",
    "v1_medscore": "mistralai/Mistral-Small-24B-Instruct-2501",
    # Llama-3.3-70B was scored via API; Llama 3.1/3.3 share the same 128k tokenizer.
    "v4_ragas_nli": "meta-llama/Llama-3.1-8B-Instruct",
}
TOKENIZER_NOTES = {"v4_ragas_nli": "proxy: Llama-3.1-8B-Instruct tokenizer (same Llama-3 vocabulary as 3.3-70B)"}

NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")


def load_tokenizer(name: str):
    from transformers import AutoTokenizer

    for cache in (HF / "hub", HF):
        try:
            return AutoTokenizer.from_pretrained(
                name, cache_dir=str(cache), local_files_only=True, use_fast=True, trust_remote_code=True
            )
        except Exception:  # noqa: BLE001
            continue
    raise RuntimeError(f"tokenizer not cached: {name}")


def token_offsets(tok, text: str) -> list[tuple[int, int]]:
    if getattr(tok, "is_fast", False):
        return tok(text, return_offsets_mapping=True, add_special_tokens=False)["offset_mapping"]
    # Slow tokenizers: align each token's surface string left-to-right in the text.
    offsets, cur = [], 0
    for t in tok.tokenize(text):
        piece = tok.convert_tokens_to_string([t]).strip()
        if not piece:
            offsets.append((cur, cur))
            continue
        pos = text.find(piece, cur)
        if pos < 0:
            offsets.append((cur, cur))
            continue
        offsets.append((pos, pos + len(piece)))
        cur = pos + len(piece)
    return offsets


def lead_num(span: str) -> str | None:
    m = NUM_RE.search(span or "")
    return m.group(0) if m else None


def new_numeral_spans(after: str, raw: str) -> list[tuple[int, int]]:
    """Char spans in `after` of numerals whose count exceeds their count in `raw`."""
    raw_count = Counter(m.group(0) for m in NUM_RE.finditer(raw))
    seen: Counter = Counter()
    spans = []
    for m in NUM_RE.finditer(after):
        seen[m.group(0)] += 1
        if seen[m.group(0)] > raw_count[m.group(0)]:
            spans.append(m.span())
    return spans


def flag(tok, text: str, spans: list[tuple[int, int]], original: str) -> bool:
    for s, e in token_offsets(tok, text):
        if e <= s:
            continue
        if any(s < b and e > a for a, b in spans) and text[s:e].strip(" ▁Ġ") == original:
            return True
    return False


def m1_noop_ids() -> set[str]:
    """US_up rows whose after-M1 text equals the raw text (checker-side M1 regex lacks e.g. g/kg, L)."""
    raw = {r["instance_id"]: r for r in read_jsonl(RAW_T7)}
    return {
        r["instance_id"]
        for r in read_jsonl(AFTER)
        if r["instance_id"] in raw
        and (r["claim"], r["evidence"]) == (raw[r["instance_id"]]["claim"], raw[r["instance_id"]]["evidence"])
    }


def after_rate(rows: list[dict]) -> dict:
    by: dict[str, list[int]] = defaultdict(list)
    for r in rows:
        by[r["base_id"]].append(int(r["after"] == "FAIL"))
    return bootstrap_rate([(sum(v), len(v)) for v in by.values()])


def us_up_items() -> dict[str, dict]:
    after = {r["instance_id"]: r for r in read_jsonl(AFTER)}
    raw = {r["instance_id"]: r for r in read_jsonl(RAW_T7)}
    items = {}
    for iid, a in after.items():
        r = raw.get(iid)
        if not r:
            continue
        original = lead_num(r["claim_span"])
        per_side = []
        for key in ("claim", "evidence"):
            spans = new_numeral_spans(a[key], r[key])
            if spans:
                per_side.append((a[key], spans))
        items[iid] = {"original": original, "sides": per_side}
    return items


def ns_items() -> dict[str, dict]:
    items = {}
    for r in read_jsonl(MAIN):
        if r.get("magnitude") != "x10" or r.get("condition") not in ("E1-claim", "E1-evid"):
            continue
        key = "claim" if r["condition"] == "E1-claim" else "evidence"
        d = (r.get("diff") or {}).get(key) or {}
        original, new = lead_num(d.get("span_before", "")), lead_num(d.get("span_after", ""))
        text = r[key]
        span_after = d.get("span_after", "")
        pos = text.find(span_after) if span_after else -1
        sides = []
        if pos >= 0 and new:
            m = NUM_RE.search(text, pos)
            if m:
                sides.append((text, [m.span()]))
        items[r["instance_id"]] = {"original": original, "sides": sides}
    return items


def split(rows: list[dict], items: dict[str, dict], tok, value_key: str, noop: set[str] = frozenset()) -> dict:
    groups: dict[str, dict[str, list[int]]] = {"yes": defaultdict(list), "no": defaultdict(list)}
    unresolved = n_noop = 0
    for row in rows:
        if row["instance_id"] in noop:
            n_noop += 1
            continue
        it = items.get(row["instance_id"])
        if not it or not it["original"] or not it["sides"]:
            unresolved += 1
            continue
        hit = any(flag(tok, text, spans, it["original"]) for text, spans in it["sides"])
        groups["yes" if hit else "no"][row["base_id"]].append(int(row[value_key] == "FAIL"))
    out = {"unresolved": unresolved, "m1_noop": n_noop}
    for k, by in groups.items():
        out[k] = bootstrap_rate([(sum(v), len(v)) for v in by.values()])
    return out


def fmt(st: dict) -> str:
    if st.get("rate") is None:
        return f"NA (n={st.get('den', 0)})"
    ci = f" [{100*st['lo']:.1f}, {100*st['hi']:.1f}]" if st.get("lo") is not None else ""
    return f"{100*st['rate']:.1f}%{ci} (n={st['den']})"


def main() -> None:
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    dump = json.loads(ROWS.read_text())
    us_items, ns, noop = us_up_items(), ns_items(), m1_noop_ids()
    result = {}
    lines = [
        "# EXPLORATORY — numeral-token survival after M1 (not preregistered)",
        "",
        "**Exploratory analysis; not part of the preregistered M1-strong criterion.** Rows = exactly the "
        "pairs/rows behind `results/tables/m1_strong_final.md` (C0-PASS bases, parsed scores).",
        "",
        "- **Flag (US_up after-M1):** tokenize the after-M1 text with the checker's own tokenizer; flag = yes if a "
        "token overlapping the numeral M1 introduced (e.g. `500000`) has surface exactly equal to the original "
        "numeral (e.g. `500`). Cell = US_up **after** FAIL rate.",
        "- **Control (NS_x10):** same test on the ×10 numeral (e.g. `5000`) vs the C0 numeral (`500`). Cell = NS_x10 FAIL rate.",
        f"- Bootstrap {N_BOOT} × base_id, seed {SEED}. `no-op` = US_up pairs where M1 left the text unchanged "
        "(no rescaled numeral exists; excluded from the split). `unres.` = other rows where no introduced numeral was found.",
        "",
        "| Model | Side | US_up after, flag=yes | US_up after, flag=no | no-op | unres. | NS_x10, flag=yes | NS_x10, flag=no | unres. |",
        "| --- | --- | --- | --- | ---: | ---: | --- | --- | ---: |",
    ]
    for slug, tname in TOKENIZERS.items():
        if slug not in dump:
            continue
        tok = load_tokenizer(tname)
        result[slug] = {"tokenizer": tname}
        for s in ("claim", "evid"):
            us = split(dump[slug]["us_up_after_pairs"][s], us_items, tok, "after", noop)
            nsr = split(dump[slug]["ns_x10"][s], ns, tok, "verdict")
            result[slug][s] = {"us_up_after": us, "ns_x10": nsr}
            lines.append(
                f"| {verifier_display_name(slug)} | {s.upper()} | {fmt(us['yes'])} | {fmt(us['no'])} | {us['m1_noop']} | {us['unresolved']} | "
                f"{fmt(nsr['yes'])} | {fmt(nsr['no'])} | {nsr['unresolved']} |"
            )
    lines += ["", "Tokenizers: " + "; ".join(f"{verifier_display_name(k)} = `{v}`" for k, v in TOKENIZERS.items()) + "."]
    lines += [f"- {verifier_display_name(k)}: {v}" for k, v in TOKENIZER_NOTES.items()]
    lines += [
        "",
        "## Caveat found here — M1 no-op rows inside the US_up after pairs (sensitivity, not a revision)",
        "",
        f"Checker-side M1 (`src/quantity_norm.py` DOSE_RE) has no `g/kg` or `L`, so **{len(noop)}/214** US_up ×1000 rows "
        "(mg/kg→g/kg, mL→L) are unchanged by M1; the gate still passes them because M1-lib and M1 agree (both unchanged). "
        "In `m1_strong_final` these count as after-M1 pairs although the checker saw the before input. "
        "US_down after (150/150 changed) and NS (no M1) are unaffected. The accepted table is **not** changed.",
        "",
        "| Model | Side | US_up after (as reported) | US_up after, M1-changed rows only | US_up after, no-op rows only | NS_x10 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    final = json.loads((ROOT / "notes/m1_strong_final.json").read_text())["checkers"]
    for slug in TOKENIZERS:
        if slug not in dump:
            continue
        for s in ("claim", "evid"):
            rows = dump[slug]["us_up_after_pairs"][s]
            if not rows:
                continue
            keep = [r for r in rows if r["instance_id"] not in noop]
            only = [r for r in rows if r["instance_id"] in noop]
            result[slug][s]["sensitivity"] = {"all": after_rate(rows), "m1_changed": after_rate(keep), "noop": after_rate(only)}
            lines.append(
                f"| {verifier_display_name(slug)} | {s.upper()} | {fmt(after_rate(rows))} | {fmt(after_rate(keep))} | "
                f"{fmt(after_rate(only))} | {fmt(final[slug]['metrics'][f'NS_x10_{s}'])} |"
            )
    OUT.write_text("\n".join(lines) + "\n")
    OUT_JSON.write_text(json.dumps(result, indent=2) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
