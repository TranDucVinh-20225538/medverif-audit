#!/usr/bin/env python3
"""(B3b) Build the real-RAG perturbation pack from generated answers (CPU, no API).

For every answer, the first dose span (DOSE_RE) whose canonical quantity also occurs in the retrieved
passages is the anchor ("answer/evidence dose match"). Instances (claim = full answer, evidence = the
concatenated top-k passages the generator saw):
  RAG-C0          unchanged answer                         expected PASS
  RAG-conv        natural unit conversion of the anchor    expected PASS (same amount)
  RAG-value-x2    anchor number x2                         expected FAIL
  RAG-value-x10   anchor number x10                        expected FAIL
  RAG-unit-up     unit one SI step up, numeral kept (x1000) expected FAIL
  RAG-unit-down   unit one SI step down, numeral kept      expected FAIL
Edits use the same helpers as the main pack (src/text_utils.py).

Outputs: data/journal/instances_rag.jsonl, results/journal/rag/build_manifest.json,
         qc/jr_rag_human_check.csv (stratified sample for a human to verify the dose matching).
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jr_common import RAG_DIR, ROOT, is_done, log, mark_done, read_jsonl, write_jsonl  # noqa: E402

STAGE = "B3b_instances"
ANS = RAG_DIR / "answers.jsonl"
RETR = RAG_DIR / "retrieval.jsonl"
OUT = ROOT / "data/journal/instances_rag.jsonl"
HUMAN = ROOT / "qc/jr_rag_human_check.csv"
SEED = 20261001


def spans(text: str):
    from quantity_norm import canonicalize_dose_span  # noqa: E402
    from text_utils import dose_matches  # noqa: E402

    out = []
    for m in dose_matches(text or ""):
        try:
            canon = canonicalize_dose_span(m.group(1), m.group(2))
        except Exception:
            canon = None
        out.append((m.start(), m.end(), m.group(0), canon))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", default=str(ANS))
    ap.add_argument("--retrieval", default=str(RETR))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--human-n", type=int, default=80)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if is_done(STAGE) and not args.dry_run:
        log(STAGE, skipped="marker present")
        return
    from text_utils import natural_unit_conversion, scale_dose_span, unit_swap_numeral_fixed  # noqa: E402

    retr = {r["qid"]: r for r in read_jsonl(Path(args.retrieval))}
    answers = [a for a in read_jsonl(Path(args.answers)) if a.get("answer")]
    seen = set()
    inst, stats, human_pool = [], Counter(), []
    for a in answers:
        key = (a["qid"], a["generator"])
        if key in seen or a["qid"] not in retr:
            continue
        seen.add(key)
        r = retr[a["qid"]]
        evidence = "\n\n".join(p["text"] for p in r["passages"])
        ans = a["answer"].strip()
        a_sp = spans(ans)
        e_sp = spans(evidence)
        e_canon = {c: s for _, _, s, c in e_sp if c}
        anchor = next(((s, e, surf, c) for s, e, surf, c in a_sp if c and c in e_canon), None)
        status = "no_dose_in_answer" if not a_sp else ("matched" if anchor else "unmatched")
        stats[status] += 1
        base = "%s__%s" % (a["qid"], a["generator"])
        human_pool.append({"status": status, "a": a, "evidence": evidence, "anchor": anchor, "a_sp": a_sp,
                           "e_span": e_canon.get(anchor[3]) if anchor else (e_sp[0][2] if e_sp else "")})
        if not anchor:
            continue
        s, e, surf, _ = anchor
        common = {"base_id": base, "type": "DOSE", "evidence": evidence, "claim_c0": ans, "evidence_span": e_canon[anchor[3]],
                  "generator": a["generator"], "question_id": a["qid"], "question": a["question"], "valid": True,
                  "source": "journal_real_rag", "dense_model": r.get("dense_model")}
        inst.append(dict(common, instance_id=base + "__RAG-C0", condition="RAG-C0", magnitude="none", claim=ans,
                         claim_span=surf, expected_verdict="PASS"))
        edits = [("RAG-conv", "unit_conversion", natural_unit_conversion(surf), "PASS")]
        for f, name in (("2", "x2"), ("10", "x10")):
            try:
                edits.append(("RAG-value-" + name, name, scale_dose_span(surf, Decimal(f)), "FAIL"))
            except ValueError:
                edits.append(("RAG-value-" + name, name, None, "FAIL"))
        for d in ("up", "down"):
            sw = unit_swap_numeral_fixed(surf, d)
            edits.append(("RAG-unit-" + d, "x1000" if d == "up" else "div1000", sw[0] if sw else None, "FAIL"))
        for cond, mag, new, exp in edits:
            if not new:
                stats["skip_" + cond] += 1
                continue
            inst.append(dict(common, instance_id="%s__%s" % (base, cond), condition=cond, magnitude=mag,
                             claim=ans[:s] + new + ans[e:], claim_span=new, span_before=surf, expected_verdict=exp))
            stats[cond] += 1
    out = Path(args.out) if not args.dry_run else Path("/tmp/jr_instances_rag_dryrun.jsonl")
    write_jsonl(out, inst)
    # human-check sample: stratified by generator x match status
    rng = random.Random(SEED)
    strata = {}
    for h in human_pool:
        strata.setdefault((h["a"]["generator"], h["status"]), []).append(h)
    picked = []
    per = max(1, args.human_n // max(1, len(strata)))
    for k in sorted(strata):
        items = sorted(strata[k], key=lambda h: h["a"]["qid"])
        picked += rng.sample(items, min(per, len(items)))
    hpath = HUMAN if not args.dry_run else Path("/tmp/jr_rag_human_check_dryrun.csv")
    hpath.parent.mkdir(parents=True, exist_ok=True)
    with hpath.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["check_id", "question_id", "generator", "question", "answer", "answer_dose_spans", "auto_status",
                    "auto_anchor_span", "auto_evidence_span", "evidence_window", "human_same_quantity_same_context (Y/N)",
                    "human_answer_dose_correct_per_evidence (Y/N)", "note"])
        for i, h in enumerate(picked):
            ev = h["evidence"]
            sp = h["e_span"] or ""
            j = ev.find(sp) if sp else -1
            window = ev[max(0, j - 300): j + len(sp) + 300] if j >= 0 else ev[:600]
            w.writerow(["JRH%03d" % i, h["a"]["qid"], h["a"]["generator"], h["a"]["question"], h["a"]["answer"],
                        "; ".join(x[2] for x in h["a_sp"]), h["status"], h["anchor"][2] if h["anchor"] else "", sp,
                        window, "", "", ""])
    manifest = {"answers": len(seen), "instances": len(inst), "status_counts": dict(stats),
                "human_check_rows": len(picked), "human_check_file": str(hpath.relative_to(ROOT)) if not args.dry_run else str(hpath)}
    if not args.dry_run:
        (RAG_DIR / "build_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        mark_done(STAGE, **manifest)
    log(STAGE, **manifest)


if __name__ == "__main__":
    main()
