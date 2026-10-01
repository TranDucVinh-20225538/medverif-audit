#!/usr/bin/env python3
"""E2 (faithful-but-wrong control) PASS rates for all 9 LLM-judge configs on the main DOSE card cohort.

Cohort: the 220 E2 rows (110 bases x {x2, x10}) of `t15_card_report.load_main_dose_instances()`, the same
instances the main card uses. Rate = PASS / (PASS+FAIL) over E2 rows whose base is C0-PASS for that judge
(C0 verdicts from the card loader `paper_numbers_final.card_verdicts`); the unconditional rate is reported too.

E2 verdict sources per judge (first hit per instance wins):
  1. card loader (`paper_numbers_final.card_verdicts`, i.e. t13 merged score dirs + lane_b)  -> v1_medscore, v4_ragas_nli
  2. results/raw/t23/<slug>.jsonl (T23 OpenRouter run; covers v1c + the four v6 judges)
  3. results/raw/e2_remaining/<slug>.jsonl (written by this script)
Judges with E2 rows missing from all sources are scored here (on HPC; OpenRouter) with the repo's own verifier
modules and the pins resolved/validated by `rerun_agreement.resolve_spec` (registry -> notes/t6_models.json ->
stored rows; must agree with the judge's stored main-card rows), temperature 0, seed 42, no provider fallbacks.

  python3 scripts/e2_remaining_judges.py --dry-run     # coverage, spec check, cost estimate; no API calls
  python3 scripts/e2_remaining_judges.py               # score missing rows (cap --budget-usd, default 3), write note
  python3 scripts/e2_remaining_judges.py --report-only # just rewrite notes/e2_all_judges.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "scripts", ROOT / "analysis"):
    sys.path.insert(0, str(p))

import rerun_agreement as ra  # noqa: E402

T23 = ROOT / "results/raw/t23"
OUT_DIR = ROOT / "results/raw/e2_remaining"
NOTE = ROOT / "notes/e2_all_judges.md"
BATCH = 10


def read_jsonl(path: Path) -> list:
    out = []
    if path.is_file():
        for line in path.open(encoding="utf-8"):
            if line.strip():
                out.append(json.loads(line))
    return out


def cohort():
    from t15_card_report import load_main_dose_instances

    inst = load_main_dose_instances()
    e2 = {r["instance_id"]: r for r in inst if r["condition"] == "E2"}
    return inst, e2


def e2_verdicts(slug: str, e2: dict, card: dict) -> dict:
    """instance_id -> (verdict, source, api_model, api_provider)."""
    out = {}
    stored = ra.stored_rows(slug)
    for iid in e2:
        if iid in card:
            r = stored.get(iid) or {}
            out[iid] = (card[iid], "card_loader", r.get("api_model"), r.get("api_provider"))
    for src, path in (("t23", T23 / f"{slug}.jsonl"), ("e2_remaining", OUT_DIR / f"{slug}.jsonl")):
        for r in read_jsonl(path):
            iid = r.get("instance_id")
            if iid in e2 and iid not in out and r.get("verdict"):
                out[iid] = (r["verdict"], src, r.get("api_model"), r.get("api_provider"))
    return out


def rates(inst: list, e2: dict, card: dict, ev: dict) -> dict:
    c0p = {r["base_id"] for r in inst if r["condition"] == "C0" and card.get(r["instance_id"]) == "PASS"}
    scored = {i: v for i, v in ev.items() if v[0] in ("PASS", "FAIL")}
    cond = {i: v for i, v in scored.items() if e2[i]["base_id"] in c0p}
    return {"c0_pass_bases": len(c0p), "cond_pass": sum(v[0] == "PASS" for v in cond.values()), "cond_n": len(cond),
            "all_pass": sum(v[0] == "PASS" for v in scored.values()), "all_n": len(scored),
            "parse_fail": sum(v[0] == "PARSE_FAIL" for v in ev.values()), "covered": len(ev),
            "sources": sorted({v[1] for v in ev.values()}),
            "models": sorted({f"{v[2]}@{v[3]}" for v in ev.values()})}


def write_note(table: dict, spent: float, aborted) -> None:
    from verifier_labels import verifier_display_name

    lines = ["# E2 (faithful-but-wrong) PASS, all 9 LLM judges, main DOSE card cohort", "",
             f"Generated {datetime.now(timezone.utc).isoformat()} by `scripts/e2_remaining_judges.py`. Cohort: 220 E2 "
             "rows (110 bases x {x2, x10}) from `load_main_dose_instances()`; PASS rate over PASS/FAIL rows, "
             "conditional on the base's C0 verdict = PASS for that judge (card loader). Higher = worse "
             "(the evidence was edited consistently, so PASS is 'faithful but wrong').", "",
             "| Judge | E2 PASS given C0 PASS | % | E2 PASS (all) | PARSE_FAIL | coverage | source(s) | api model@provider |",
             "|---|---:|---:|---:|---:|---:|---|---|"]
    for slug, t in table.items():
        pct = f"{100 * t['cond_pass'] / t['cond_n']:.1f}%" if t["cond_n"] else "NA"
        lines.append(f"| {verifier_display_name(slug)} | {t['cond_pass']}/{t['cond_n']} | {pct} | "
                     f"{t['all_pass']}/{t['all_n']} | {t['parse_fail']} | {t['covered']}/220 | "
                     f"{', '.join(t['sources'])} | {', '.join(t['models'])} |")
    lines += ["", f"Spend this run: {spent:.4f} USD."]
    if aborted:
        lines += ["", f"**Run aborted:** {aborted}. Re-run the same command to resume."]
    NOTE.write_text("\n".join(lines) + "\n")
    print(f"wrote {NOTE}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--budget-usd", type=float, default=3.0)
    ap.add_argument("--judges", default=",".join(ra.JUDGES))
    ap.add_argument("--fill-gaps", action="store_true",
                    help="also score the few E2 rows missing for judges that already have E2 data "
                         "(default: only judges with no E2 data at all are scored, so existing cells stay as reported)")
    args = ap.parse_args()
    judges = [j.strip() for j in args.judges.split(",") if j.strip()]
    unknown = [j for j in judges if j not in ra.JUDGES]
    if unknown:
        sys.exit(f"unknown judges: {unknown}")
    import paper_numbers_final as pnf

    inst, e2 = cohort()
    card = {j: pnf.card_verdicts(j) for j in judges}
    ev = {j: e2_verdicts(j, e2, card[j]) for j in judges}
    missing = {j: sorted(i for i in e2 if i not in ev[j]) for j in judges}
    gaps = {j: v for j, v in missing.items() if v and ev[j] and not args.fill_gaps}
    missing = {j: ([] if j in gaps else v) for j, v in missing.items()}

    # spec check for every judge (pins vs the judge's stored main-card rows), before any API call
    rows = ra.candidate_rows()
    stored = {j: ra.stored_rows(j) for j in judges}
    sample = ra.build_sample(rows, stored)
    specs = {j: ra.resolve_spec(j, stored[j], sample[j]) for j in judges}
    plan = []
    for j in judges:
        sp = specs[j]
        # E2 rows already present must come from the same model/provider
        for iid, v in ev[j].items():
            if v[2] and sp["openrouter_model"] and sp["openrouter_model"].lower() not in str(v[2]).lower():
                sp["problems"].append(f"existing E2 row {iid} model {v[2]!r} != pin")
                break
        est = ra.est_cost(j, stored[j], missing[j]) if missing[j] else 0.0
        t = rates(inst, e2, card[j], ev[j])
        plan.append({"judge": j, "model": sp["openrouter_model"], "provider": sp["provider"], "pin_source": sp["source"],
                     "e2_covered": len(ev[j]), "to_score": len(missing[j]), "gap_not_scored": len(gaps.get(j, [])), "sources": t["sources"],
                     "current": f"{t['cond_pass']}/{t['cond_n']} (all {t['all_pass']}/{t['all_n']})",
                     "est_cost_usd": round(est, 4), "problems": sp["problems"]})
    for p in plan:
        print(json.dumps(p))
    total = sum(p["est_cost_usd"] for p in plan)
    print(json.dumps({"est_total_usd": round(total, 4), "budget_usd": args.budget_usd}))
    bad = {p["judge"]: p["problems"] for p in plan if p["problems"]}
    if bad:
        sys.exit(f"SPEC CHECK FAILED (no API call made): {json.dumps(bad)}")
    if args.dry_run:
        if total > args.budget_usd:
            print(f"WARNING: estimate {total:.2f} USD exceeds cap {args.budget_usd:.2f}; the run would stop at the cap.")
        return

    spent, aborted = 0.0, None
    if not args.report_only and any(missing[j] for j in judges):
        ra.load_env()
        if not os.environ.get("OPENROUTER_API_KEY", "").strip():
            sys.exit("OPENROUTER_API_KEY not set (env, ./.env, ~/kkk/openrouter.env)")
        import importlib

        from verifiers.io_utils import append_jsonl

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        for j in judges:
            todo = [i for i in missing[j] if i not in {r["instance_id"] for r in read_jsonl(OUT_DIR / f"{j}.jsonl")}]
            if not todo:
                continue
            ra.set_judge_env(j, specs[j])
            mod_name = ra.JUDGES[j][0]
            sys.modules.pop(f"verifiers.{mod_name}", None)
            module = importlib.import_module(f"verifiers.{mod_name}")
            llm, tok, params, _ = module.load()
            per_call = ra.est_cost(j, stored[j], [None])
            for off in range(0, len(todo), BATCH):
                ids = todo[off: off + BATCH]
                if spent + per_call * len(ids) > args.budget_usd:
                    aborted = f"budget: spent {spent:.4f} + next batch est {per_call * len(ids):.4f} > cap {args.budget_usd}"
                    break
                scored = module.score_batch(llm, tok, params, [e2[i] for i in ids])
                stamp = datetime.now(timezone.utc).isoformat()
                for r in scored:
                    c = r.get("api_cost_usd")
                    spent += float(c) if isinstance(c, (int, float)) else per_call
                    r.update({"judge": j, "pinned_model": specs[j]["openrouter_model"],
                              "pinned_provider": specs[j]["provider"], "scored_at_utc": stamp})
                append_jsonl(OUT_DIR / f"{j}.jsonl", scored)
                print(json.dumps({"judge": j, "done": off + len(ids), "of": len(todo), "spent_usd": round(spent, 4)}),
                      flush=True)
                if spent > args.budget_usd:
                    aborted = f"budget exceeded after batch: {spent:.4f} > {args.budget_usd}"
                    break
            if aborted:
                break
        ev = {j: e2_verdicts(j, e2, card[j]) for j in judges}
    table = {j: rates(inst, e2, card[j], ev[j]) for j in judges}
    write_note(table, spent, aborted)
    if aborted:
        print("ABORTED:", aborted, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
