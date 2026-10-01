#!/usr/bin/env python3
"""API re-run agreement for the 9 LLM-judge configs (run on the HPC login node; CPU only, OpenRouter).

For each judge: re-score a fixed stratified sample of 60 main-DOSE rows (20 C0, 20 INV-claim unit_conversion,
20 E1-unit-claim x1000 from data/t7/instances_e1_unit.jsonl) with the repo's own verifier modules
(src/verifiers/*: same prompt, parser, OpenRouter model + provider pin from notes/openrouter_verifiers.json,
temperature 0, seed 42, allow_fallbacks=False) and compare to the stored verdicts that the main card uses
(t13_best_of_n_report.merged_score_rows). The same 60 instance_ids are used for every judge when possible.

Outputs: results/rerun_agreement/<slug>.jsonl (one row per re-scored instance, with stored + new verdict),
         results/rerun_agreement/sample.json, notes/rerun_agreement.md (k/60 identical verdicts per judge, spend).
Budget: hard cap --budget-usd (default 3.0). Before each batch the projected spend (spent + estimated batch cost)
is checked; the run aborts (exit 2) before exceeding the cap. Resumable: rows already in the output are skipped.

Usage:
  python3 scripts/rerun_agreement.py --dry-run            # counts + estimated cost, no API calls, no .env needed
  python3 scripts/rerun_agreement.py                      # real run (needs OPENROUTER_API_KEY; loads ./.env)
  python3 scripts/rerun_agreement.py --judges v1_medscore,v4_ragas_nli --budget-usd 1
"""
from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "scripts", ROOT / "analysis"):
    sys.path.insert(0, str(p))

OUT_DIR = ROOT / "results/rerun_agreement"
NOTE = ROOT / "notes/rerun_agreement.md"
T7 = ROOT / "data/t7/instances_e1_unit.jsonl"
SEED = 20261001
PER_STRATUM = 20
BATCH = 10

# slug -> (verifier module, env var for model, env var for provider)
JUDGES = {
    "v1_medscore": ("v1_medscore", "MEDVERIF_V1_OPENROUTER_MODEL", "MEDVERIF_V1_PROVIDER"),
    "v1c_medscore": ("v1c_medscore", "MEDVERIF_V1C_OPENROUTER_MODEL", "MEDVERIF_V1C_PROVIDER"),
    "v1b_medscore": ("v1b_medscore", "MEDVERIF_V1B_OPENROUTER_MODEL", "MEDVERIF_V1B_PROVIDER"),
    "v6_ragas_llama31_8b": ("v6_ragas_nli", "MEDVERIF_V6_OPENROUTER_MODEL", "MEDVERIF_V6_PROVIDER"),
    "v4_ragas_nli": ("v4_ragas_nli", "MEDVERIF_V4_OPENROUTER_MODEL", "MEDVERIF_V4_PROVIDER"),
    "v6_ragas_mistral_small32": ("v6_ragas_nli", "MEDVERIF_V6_OPENROUTER_MODEL", "MEDVERIF_V6_PROVIDER"),
    "v6_ragas_gpt4o_mini": ("v6_ragas_nli", "MEDVERIF_V6_OPENROUTER_MODEL", "MEDVERIF_V6_PROVIDER"),
    "v6_ragas_haiku45": ("v6_ragas_nli", "MEDVERIF_V6_OPENROUTER_MODEL", "MEDVERIF_V6_PROVIDER"),
    "v5_ragas_nli": ("v5_ragas_nli", "MEDVERIF_V5_OPENROUTER_MODEL", "MEDVERIF_V5_PROVIDER"),
}
STRATA = ("C0", "INV-unit", "E1-unit-claim-x1000")
# fallback per-call cost guess (USD) when no stored api_cost_usd exists for a judge
FALLBACK_COST = {"v1b_medscore": 0.004, "v5_ragas_nli": 0.008, "v6_ragas_haiku45": 0.003}


def load_env() -> None:
    """Same convention as jobs/*.sh (`set -a; source <file>`): KEY=VALUE lines; existing env wins."""
    for path in (ROOT / ".env", Path.home() / "kkk/openrouter.env"):
        if not path.is_file():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        break


def stratum(row: dict) -> str | None:
    c, m = row.get("condition"), row.get("magnitude")
    if c == "C0":
        return "C0"
    if c == "INV-claim" and m == "unit_conversion":
        return "INV-unit"
    if c == "E1-unit-claim" and m == "x1000":
        return "E1-unit-claim-x1000"
    return None


def candidate_rows() -> dict[str, dict]:
    from analyze import read_jsonl
    from t15_card_report import analysis_keep_row, load_main_dose_instances

    inst = load_main_dose_instances()
    bases = {r["base_id"] for r in inst}
    rows = {r["instance_id"]: r for r in inst if stratum(r)}
    for r in read_jsonl(T7):
        if r.get("valid", True) and analysis_keep_row(r) and r["base_id"] in bases and stratum(r):
            rows[r["instance_id"]] = r
    return rows


def stored_rows(slug: str) -> dict[str, dict]:
    import t13_best_of_n_report as t13

    return t13.merged_score_rows(slug)


def build_sample(rows: dict[str, dict], stored: dict[str, dict[str, dict]]) -> dict[str, list[str]]:
    """Common sample: ids with a stored PASS/FAIL verdict for all judges; per-judge top-up if a stratum is short."""
    rng = random.Random(SEED)
    ok = lambda slug, iid: (stored[slug].get(iid) or {}).get("verdict") in ("PASS", "FAIL")  # noqa: E731
    common: list[str] = []
    for s in STRATA:
        ids = sorted(i for i, r in rows.items() if stratum(r) == s and all(ok(j, i) for j in stored))
        rng.shuffle(ids)
        common += ids[:PER_STRATUM]
    sample = {}
    for slug in stored:
        ids = list(common)
        for s in STRATA:
            have = sum(1 for i in ids if stratum(rows[i]) == s)
            if have < PER_STRATUM:
                extra = sorted(i for i, r in rows.items() if stratum(r) == s and ok(slug, i) and i not in ids)
                random.Random(f"{SEED}:{slug}:{s}").shuffle(extra)
                ids += extra[: PER_STRATUM - have]
        sample[slug] = ids
    return sample


def est_cost(slug: str, stored: dict[str, dict], ids: list[str]) -> float:
    costs = [float(r["api_cost_usd"]) for r in stored.values() if isinstance(r.get("api_cost_usd"), (int, float))]
    per = statistics.mean(costs) if costs else FALLBACK_COST.get(slug, 0.002)
    return per * len(ids) * 1.25  # 25% safety margin


T6_MODELS = ROOT / "notes/t6_models.json"


def _stored_pin(stored: dict[str, dict], ids: list[str]) -> tuple[str | None, str | None, int]:
    """Majority (api_model, api_provider) over the stored rows of the sampled ids."""
    from collections import Counter

    c: Counter = Counter()
    for i in ids:
        r = stored.get(i) or {}
        m = (r.get("api_model") or r.get("openrouter_model") or r.get("model") or "").strip() or None
        pr = (r.get("api_provider") or r.get("provider") or "").strip() or None
        c[(m, pr)] += 1
    if not c:
        return None, None, 0
    (m, pr), n = c.most_common(1)[0]
    return m, pr, n


def resolve_spec(slug: str, stored: dict[str, dict], ids: list[str]) -> dict:
    """Model/provider pin for one judge.

    Order: notes/openrouter_verifiers.json (registry) -> notes/t6_models.json (T6-B zoo, e.g. v1c_medscore) ->
    majority api_model/api_provider of the stored verdict rows being compared. The result must agree with the
    stored rows (else the rerun would not test the same config)."""
    from verifier_registry import expected_openrouter

    spec, source = None, None
    reg = expected_openrouter(slug)
    if reg and reg.get("openrouter_model"):
        spec, source = {"openrouter_model": reg["openrouter_model"], "provider": reg.get("provider")}, "registry"
    if spec is None and T6_MODELS.is_file():
        for m in json.loads(T6_MODELS.read_text()).get("t6b_openrouter", []):
            if m.get("slug") == slug and m.get("openrouter_model"):
                spec, source = {"openrouter_model": m["openrouter_model"], "provider": m.get("provider")}, "t6_models"
                break
    sm, sp, sn = _stored_pin(stored, ids)
    if spec is None and sm:
        spec, source = {"openrouter_model": sm, "provider": sp}, "stored_rows"
    problems = []
    if spec is None:
        problems.append("no model pin found (registry, t6_models.json, stored rows)")
    else:
        if not spec.get("provider"):
            if sp:
                spec["provider"] = sp
            else:
                problems.append("no provider pin")
        if not sm:
            problems.append("stored rows carry no api_model")
        elif spec["openrouter_model"].lower() not in sm.lower():
            problems.append(f"model pin {spec['openrouter_model']!r} != stored rows {sm!r}")
        if sp and spec.get("provider") and spec["provider"].lower() != sp.lower():
            problems.append(f"provider pin {spec['provider']!r} != stored rows {sp!r}")
        if sn < len(ids):
            problems.append(f"only {sn}/{len(ids)} stored rows carry the majority model/provider")
    return {"judge": slug, "module": JUDGES[slug][0], "openrouter_model": (spec or {}).get("openrouter_model"),
            "provider": (spec or {}).get("provider"), "source": source, "stored_model": sm, "stored_provider": sp,
            "stored_rows_matching": sn, "problems": problems}


def set_judge_env(slug: str, spec: dict) -> None:
    module, mkey, pkey = JUDGES[slug]
    for k in list(os.environ):
        if k.startswith("MEDVERIF_V6_") or k in ("MEDVERIF_M1",):
            del os.environ[k]
    os.environ["MEDVERIF_USE_OPENROUTER"] = "1"
    os.environ[mkey] = spec["openrouter_model"]
    os.environ[pkey] = spec["provider"]
    if module == "v6_ragas_nli":
        os.environ["MEDVERIF_V6_VERIFIER_SLUG"] = slug


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--budget-usd", type=float, default=3.0)
    ap.add_argument("--judges", default=",".join(JUDGES))
    args = ap.parse_args()
    judges = [j.strip() for j in args.judges.split(",") if j.strip()]
    unknown = [j for j in judges if j not in JUDGES]
    if unknown:
        sys.exit(f"unknown judges: {unknown}")

    rows = candidate_rows()
    stored = {j: stored_rows(j) for j in judges}
    sample = build_sample(rows, stored)
    specs = {j: resolve_spec(j, stored[j], sample[j]) for j in judges}
    for j in judges:
        sp = specs[j]
        print(json.dumps({k: sp[k] for k in ("judge", "openrouter_model", "provider", "source", "stored_model",
                                              "stored_provider", "stored_rows_matching", "problems")}))
    bad = {j: specs[j]["problems"] for j in judges if specs[j]["problems"]}
    if bad:
        sys.exit(f"SPEC CHECK FAILED (no API call made): {json.dumps(bad)}")
    plan = []
    for j in judges:
        ids = sample[j]
        by = {s: sum(1 for i in ids if stratum(rows[i]) == s) for s in STRATA}
        out = OUT_DIR / f"{j}.jsonl"
        done = set()
        if out.is_file():
            done = {json.loads(l)["instance_id"] for l in out.open() if l.strip()}
        todo = [i for i in ids if i not in done]
        plan.append({"judge": j, "n": len(ids), "by_stratum": by, "already_done": len(ids) - len(todo),
                     "todo": len(todo), "est_cost_usd": round(est_cost(j, stored[j], todo), 4)})
    total_est = sum(p["est_cost_usd"] for p in plan)
    print(json.dumps({"seed": SEED, "budget_usd": args.budget_usd, "est_total_usd": round(total_est, 4),
                      "candidates": {s: sum(1 for r in rows.values() if stratum(r) == s) for s in STRATA},
                      "common_ids": len(set.intersection(*(set(v) for v in sample.values()))) if sample else 0},
                     indent=1))
    for p in plan:
        print(json.dumps(p))
    if args.dry_run:
        if total_est > args.budget_usd:
            print(f"WARNING: estimated {total_est:.2f} USD exceeds the {args.budget_usd:.2f} USD cap; "
                  "the real run would stop when the next batch would cross the cap.")
        return

    load_env()
    if not os.environ.get("OPENROUTER_API_KEY", "").strip():
        sys.exit("OPENROUTER_API_KEY not set (looked in env, ./.env, ~/kkk/openrouter.env)")
    import importlib

    from verifiers.io_utils import append_jsonl

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "sample.json").write_text(json.dumps({"seed": SEED, "sample": sample}, indent=1) + "\n")
    spent = 0.0
    aborted = None
    for p in plan:
        j = p["judge"]
        out = OUT_DIR / f"{j}.jsonl"
        done = {json.loads(l)["instance_id"] for l in out.open() if l.strip()} if out.is_file() else set()
        todo = [i for i in sample[j] if i not in done]
        if not todo:
            continue
        set_judge_env(j, specs[j])
        module_name = JUDGES[j][0]
        sys.modules.pop(f"verifiers.{module_name}", None)
        module = importlib.import_module(f"verifiers.{module_name}")
        llm, tok, params, _ = module.load()
        per_call = est_cost(j, stored[j], [None]) / 1.0
        for off in range(0, len(todo), BATCH):
            chunk_ids = todo[off: off + BATCH]
            if spent + per_call * len(chunk_ids) > args.budget_usd:
                aborted = f"budget: spent {spent:.4f} + next batch est {per_call * len(chunk_ids):.4f} > cap {args.budget_usd}"
                break
            chunk = [rows[i] for i in chunk_ids]
            scored = module.score_batch(llm, tok, params, chunk)
            stamp = datetime.now(timezone.utc).isoformat()
            for r in scored:
                st = stored[j].get(r["instance_id"]) or {}
                c = r.get("api_cost_usd")
                spent += float(c) if isinstance(c, (int, float)) else per_call
                r.update({"judge": j, "pinned_model": specs[j]["openrouter_model"],
                          "pinned_provider": specs[j]["provider"], "stratum": stratum(rows[r["instance_id"]]), "stored_verdict": st.get("verdict"),
                          "stored_api_model": st.get("api_model"), "stored_api_provider": st.get("api_provider"),
                          "identical": r.get("verdict") == st.get("verdict"), "rerun_at_utc": stamp})
            append_jsonl(out, scored)
            print(json.dumps({"judge": j, "done": off + len(chunk_ids), "of": len(todo), "spent_usd": round(spent, 4)}),
                  flush=True)
            if spent > args.budget_usd:
                aborted = f"budget exceeded after batch: {spent:.4f} > {args.budget_usd}"
                break
        if aborted:
            break
    write_note(judges, sample, spent, aborted, args.budget_usd)
    if aborted:
        print("ABORTED:", aborted, file=sys.stderr)
        sys.exit(2)


def write_note(judges, sample, spent, aborted, cap) -> None:
    from verifier_labels import verifier_display_name

    lines = ["# API re-run agreement (LLM judges)", "",
             f"Generated {datetime.now(timezone.utc).isoformat()} by `scripts/rerun_agreement.py` (seed {SEED}). "
             f"Sample per judge: {PER_STRATUM} C0 + {PER_STRATUM} INV-claim unit_conversion + {PER_STRATUM} "
             "E1-unit-claim x1000 (main DOSE bases), same prompt/parser/model pin/provider, temperature 0. "
             "Stored verdicts = the main-card loader (`t13_best_of_n_report.merged_score_rows`).", "",
             "| Judge | identical verdicts | C0 | INV-unit | E1-unit-claim x1000 | PARSE_FAIL (new) | api models seen | spend (USD) |",
             "|---|---:|---:|---:|---:|---:|---|---:|"]
    total = 0.0
    for j in judges:
        out = OUT_DIR / f"{j}.jsonl"
        rs = [json.loads(l) for l in out.open() if l.strip()] if out.is_file() else []
        rs = [r for r in rs if r["instance_id"] in set(sample[j])]
        k = sum(r["identical"] for r in rs)
        cost = sum(float(r["api_cost_usd"]) for r in rs if isinstance(r.get("api_cost_usd"), (int, float)))
        total += cost
        cell = lambda s: f"{sum(r['identical'] for r in rs if r['stratum'] == s)}/{sum(1 for r in rs if r['stratum'] == s)}"  # noqa: E731
        models = sorted({f"{r.get('api_model')}@{r.get('api_provider')}" for r in rs})
        lines.append(f"| {verifier_display_name(j)} | {k}/{len(rs)} (of {len(sample[j])}) | {cell('C0')} | "
                     f"{cell('INV-unit')} | {cell('E1-unit-claim-x1000')} | "
                     f"{sum(r.get('verdict') == 'PARSE_FAIL' for r in rs)} | {', '.join(models)} | {cost:.4f} |")
    lines += ["", f"Total spend (sum of api_cost_usd in outputs): **{total:.4f} USD**; this run: {spent:.4f} USD; "
              f"cap {cap:.2f} USD.", ""]
    if aborted:
        lines += [f"**Run aborted:** {aborted}. Re-run the same command to resume (done rows are skipped).", ""]
    NOTE.write_text("\n".join(lines) + "\n")
    print(f"wrote {NOTE}")


if __name__ == "__main__":
    main()
