#!/usr/bin/env python3
"""RD2 exploratory: dose-focused frontier judges (NOT HTML RAGAS).

Prompt id: dose_focused_v1@2026-10-26
Outputs ONLY under results/journal5/rd2/frontier_judges_dose_focused/
Does not modify results/journal5/rd2/frontier_judges/ or label_v3.csv.

Usage:
  python scripts/journal5/rd2_frontier_dose_focused.py --smoke --max-usd 2
  python scripts/journal5/rd2_frontier_dose_focused.py --full --max-usd 50
  python scripts/journal5/rd2_frontier_dose_focused.py --report-only
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import re
import sys
import time
from collections import Counter, OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "journal"))
sys.path.insert(0, str(ROOT / "src"))

RD2 = ROOT / "results" / "journal5" / "rd2"
OUT = RD2 / "frontier_judges_dose_focused"
RAGAS_DIR = RD2 / "frontier_judges"
LABEL_V3 = RD2 / "analysis" / "label_v3.csv"
INST = RD2 / "real_dose" / "instances.jsonl"
QUESTIONS = RD2 / "real_dose" / "questions.jsonl"
ANSWERS = RD2 / "real_dose" / "answers.jsonl"
FR_SAMPLE = RAGAS_DIR / "false_reject_sample.csv"

PROMPT_ID = "dose_focused_v1@2026-10-26"
SEED = 20261026
MAX_TOKENS = 128
UNIT_TYPE = ("unit_error", "basis_error")

SYSTEM = (
    "You are a clinical dosing checker. Decide whether the ANSWER states a dose "
    "(amount, unit, and dosing basis such as /kg or /m², and frequency/duration if the answer "
    "states them) that is consistent with the LABEL EXCERPT for the population/indication "
    "named in the question.\n\n"
    "Pass (verdict=1) if the dose content is supported or is a correct narrowing of a labelled "
    "range (e.g. answering 0.5 mg/kg when the label says 0.3–0.5 mg/kg), or uses an equivalent "
    "unit (500 mg = 0.5 g).\n\n"
    "Fail (verdict=0) if the dose amount, unit, or basis is wrong or missing when the label "
    "requires it (especially dropped /kg or /m²), or the answer gives a dose for the wrong "
    "population/indication.\n\n"
    "Ignore extra true details that do not change the dose (brand name, infusion tip, "
    "supportive care) unless they contradict the label dose.\n\n"
    "Return ONLY JSON:\n"
    '{"verdict": 0 or 1, "reason": "one short sentence"}'
)

MODELS = OrderedDict([
    ("claude_sonnet", {"model": "anthropic/claude-sonnet-4.6", "provider": "Anthropic", "allow_fallbacks": False}),
    ("gpt4o", {"model": "openai/gpt-4o", "provider": "OpenAI", "allow_fallbacks": False}),
    ("deepseek_chat", {"model": "deepseek/deepseek-chat", "provider": "", "allow_fallbacks": True}),
])

RAGAS_FILES = OrderedDict([
    ("claude_sonnet", "v6_ragas_html_claude.jsonl"),
    ("gpt4o", "v6_ragas_html_gpt4o.jsonl"),
    ("deepseek_chat", "v6_ragas_html_deepseek.jsonl"),
])


def log(**kw):
    kw = dict({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")}, **kw)
    print(json.dumps(kw, ensure_ascii=False, default=str), flush=True)


def force_load_key() -> None:
    envf = Path.home() / "kkk" / "openrouter.env"
    if not envf.is_file():
        raise SystemExit("STOP: missing %s" % envf)
    for line in envf.read_text().splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("export "):
            s = s[len("export "):]
        if "=" not in s:
            continue
        k, v = s.split("=", 1)
        if k.strip() == "OPENROUTER_API_KEY":
            os.environ["OPENROUTER_API_KEY"] = v.strip().strip('"').strip("'")
            break
    if not (os.environ.get("OPENROUTER_API_KEY") or "").strip():
        raise SystemExit("STOP: OPENROUTER_API_KEY empty")
    log(stage="key", loaded=True, key_len=len(os.environ["OPENROUTER_API_KEY"]))


def read_jsonl(path: Path):
    if not path.is_file():
        return []
    return [json.loads(l) for l in path.open(encoding="utf-8") if l.strip()]


def append_jsonl(path: Path, rows: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def done_ids(path: Path) -> set:
    return {r["instance_id"] for r in read_jsonl(path) if r.get("instance_id") and r.get("verdict") in ("PASS", "FAIL", "PARSE_FAIL")}


def spent_paths(paths) -> float:
    s = 0.0
    for p in paths:
        for r in read_jsonl(p):
            c = r.get("api_cost_usd")
            if isinstance(c, (int, float)):
                s += float(c)
    return s


def wilson(k, n, z=1.959963984540054):
    if not n:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def pct(k, n):
    return 100.0 * k / n if n else float("nan")


def fmt_rate(k, n):
    if not n:
        return "— (0)"
    lo, hi = wilson(k, n)
    return "%.1f (%d/%d; %.1f–%.1f)" % (pct(k, n), k, n, 100 * lo, 100 * hi)


_JSON = re.compile(r"\{[^{}]*\"verdict\"[^{}]*\}", re.S)


def parse_dose_json(raw: str) -> tuple[str, str]:
    """-> (PASS|FAIL|PARSE_FAIL, reason)."""
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
    m = _JSON.search(text)
    if not m:
        # try whole text
        try:
            obj = json.loads(text)
        except Exception:
            return "PARSE_FAIL", ""
    else:
        try:
            obj = json.loads(m.group(0))
        except Exception:
            return "PARSE_FAIL", ""
    if not isinstance(obj, dict) or "verdict" not in obj:
        return "PARSE_FAIL", ""
    v = obj.get("verdict")
    reason = str(obj.get("reason") or "").strip()
    if v in (1, "1", True, "pass", "PASS"):
        return "PASS", reason
    if v in (0, "0", False, "fail", "FAIL"):
        return "FAIL", reason
    return "PARSE_FAIL", reason


def user_prompt(question: str, evidence: str, answer: str) -> str:
    return (
        "QUESTION:\n%s\n\n"
        "LABEL EXCERPT:\n%s\n\n"
        "ANSWER:\n%s\n"
    ) % (question, evidence, answer)


def load_pack():
    questions = {q["qid"]: q for q in read_jsonl(QUESTIONS)}
    instances = {r["instance_id"]: r for r in read_jsonl(INST)}
    answers = {}
    for r in read_jsonl(ANSWERS):
        answers[(r["qid"], r["generator"], r["condition"])] = r.get("answer") or ""
    v3 = {r["instance_id"]: r for r in csv.DictReader(LABEL_V3.open(encoding="utf-8"))}
    ragas = {}
    for slug, fn in RAGAS_FILES.items():
        ragas[slug] = {r["instance_id"]: r.get("verdict") for r in read_jsonl(RAGAS_DIR / fn)}
    return questions, instances, answers, v3, ragas


def item_texts(iid, instances, questions, answers, v3row):
    it = instances[iid]
    qid = v3row["qid"]
    q = questions.get(qid, {})
    ans = answers.get((qid, v3row["generator"], v3row["condition"]), "") or (it.get("claim") or "")
    return q.get("question") or "", it.get("evidence") or "", ans


def build_smoke_ids(v3, ragas, seed=SEED) -> list[str]:
    rng = random.Random(seed)
    # 10 v3-correct closed that RAGAS false-rejected (prefer FR sample)
    fr_sample_ids = []
    if FR_SAMPLE.is_file():
        for r in csv.DictReader(FR_SAMPLE.open(encoding="utf-8")):
            iid = r["instance_id"]
            row = v3.get(iid)
            if not row:
                continue
            if row.get("ref_v3") == "nonerror" and row.get("condition") == "closed":
                # any RAGAS FAIL
                if any(ragas[s].get(iid) == "FAIL" for s in ragas):
                    fr_sample_ids.append(iid)
    fr_sample_ids = list(dict.fromkeys(fr_sample_ids))
    rng.shuffle(fr_sample_ids)

    # expand from full claude FR if needed
    fr_pool = list(fr_sample_ids)
    extra = [iid for iid, r in v3.items()
             if r.get("ref_v3") == "nonerror" and r.get("condition") == "closed"
             and ragas["claude_sonnet"].get(iid) == "FAIL" and iid not in fr_pool]
    rng.shuffle(extra)
    fr_pool.extend(extra)
    correct_fr = fr_pool[:10]

    err = [iid for iid, r in v3.items()
           if r.get("ref_v3") == "error" and r.get("condition") == "closed"]
    rng.shuffle(err)
    errors = err[:10]

    other = [iid for iid, r in v3.items()
             if r.get("excluded_non_dose") != "1"
             and r.get("condition") == "closed"
             and r.get("ref_v3") == ""
             and r.get("class_v3") not in ("correct_suspect",)
             and iid not in correct_fr and iid not in errors]
    rng.shuffle(other)
    others = other[:10]

    ids = correct_fr + errors + others
    if len(ids) < 30:
        raise SystemExit("smoke pool short: correct_fr=%d err=%d other=%d" % (
            len(correct_fr), len(errors), len(others)))
    meta = {
        "correct_fr_ragas": correct_fr,
        "errors": errors,
        "other": others,
        "n": len(ids),
    }
    (OUT / "smoke_ids.json").write_text(json.dumps(meta, indent=2) + "\n")
    return ids


def call_one(slug: str, iid: str, question: str, evidence: str, answer: str) -> dict:
    os.environ["MEDVERIF_USE_OPENROUTER"] = "1"
    os.environ["MEDVERIF_API_LEDGER"] = "0"
    from llm_client import chat  # noqa: E402

    spec = MODELS[slug]
    msgs = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_prompt(question, evidence, answer)},
    ]
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        kw = dict(model=spec["model"], messages=msgs, temperature=0.0,
                  max_tokens=MAX_TOKENS, seed=42, allow_fallbacks=spec["allow_fallbacks"])
        if spec["provider"]:
            kw["provider"] = spec["provider"]
        resp = chat(**kw)
        if spec["provider"] and resp.provider and resp.provider.lower() != spec["provider"].lower():
            raise RuntimeError("provider drift: asked %s served %s" % (spec["provider"], resp.provider))
        raw = (resp.text or "").strip()
        verdict, reason = parse_dose_json(raw)
        return {
            "instance_id": iid,
            "verdict": verdict,
            "reason": reason,
            "raw": raw,
            "prompt_id": PROMPT_ID,
            "model": spec["model"],
            "api_model": resp.model or spec["model"],
            "api_provider": resp.provider or spec["provider"] or "",
            "api_request_id": resp.request_id,
            "api_prompt_tokens": resp.prompt_tokens,
            "api_completion_tokens": resp.completion_tokens,
            "api_total_tokens": resp.total_tokens,
            "api_cost_usd": resp.cost_usd,
            "ts": ts,
            "slug": slug,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "instance_id": iid,
            "verdict": "PARSE_FAIL",
            "reason": "",
            "raw": "",
            "error": str(exc)[:400],
            "prompt_id": PROMPT_ID,
            "model": spec["model"],
            "api_cost_usd": 0.0,
            "ts": ts,
            "slug": slug,
        }


def run_batch(slugs, ids, questions, instances, answers, v3, max_usd, workers, tag) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    force_load_key()
    summary = {"tag": tag, "per_model": {}}
    for slug in slugs:
        out = OUT / ("%s.jsonl" % slug)
        have = done_ids(out)
        todo = [iid for iid in ids if iid not in have]
        paths = [OUT / ("%s.jsonl" % s) for s in MODELS]
        spent0 = spent_paths(paths)
        log(stage="run", slug=slug, todo=len(todo), have=len(have), spent0=round(spent0, 4), max_usd=max_usd)
        if not todo:
            summary["per_model"][slug] = {"todo": 0, "done": len(have)}
            continue

        def work(iid, slug=slug):
            q, e, a = item_texts(iid, instances, questions, answers, v3[iid])
            return call_one(slug, iid, q, e, a)

        ok = err = pf = 0
        batch_n = 0
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(work, iid): iid for iid in todo}
            buf = []
            for fut in as_completed(futs):
                rec = fut.result()
                buf.append(rec)
                batch_n += 1
                if rec.get("verdict") == "PASS":
                    ok += 1
                elif rec.get("verdict") == "FAIL":
                    err += 1
                else:
                    pf += 1
                if len(buf) >= 10:
                    append_jsonl(out, buf)
                    buf = []
                    spent = spent_paths(paths)
                    log(stage="progress", slug=slug, done=batch_n, total=len(todo),
                        spent=round(spent, 4), ok=ok, fail=err, parse_fail=pf)
                    if spent > max_usd:
                        if buf:
                            append_jsonl(out, buf)
                        raise SystemExit("BUDGET STOP: spent $%.4f > max_usd $%.2f" % (spent, max_usd))
            if buf:
                append_jsonl(out, buf)
        spent = spent_paths(paths)
        n_rows = len(read_jsonl(out))
        pf_rate = pf / max(batch_n, 1)
        summary["per_model"][slug] = {
            "new_rows": batch_n, "total_rows": n_rows, "pass": ok, "fail": err,
            "parse_fail": pf, "parse_fail_rate": pf_rate, "spent_usd": round(spent, 4),
        }
        log(stage="slug_done", slug=slug, **summary["per_model"][slug])
    summary["spent_usd"] = round(spent_paths([OUT / ("%s.jsonl" % s) for s in MODELS]), 4)
    return summary


def verdict_map_dose(slug: str) -> dict:
    return {r["instance_id"]: r.get("verdict") for r in read_jsonl(OUT / ("%s.jsonl" % slug))}


def rate_on(ids, vm):
    usable = [i for i in ids if vm.get(i) in ("PASS", "FAIL")]
    pf = sum(1 for i in ids if vm.get(i) == "PARSE_FAIL")
    k_pass = sum(1 for i in usable if vm[i] == "PASS")
    k_fail = sum(1 for i in usable if vm[i] == "FAIL")
    n = len(usable)
    return {
        "n_ref": len(ids), "n": n, "parse_fail": pf,
        "k_pass": k_pass, "k_fail": k_fail,
        "pass_rate": k_pass / n if n else float("nan"),
        "fail_rate": k_fail / n if n else float("nan"),
    }


def go_nogo(v3, ragas, smoke_meta) -> dict:
    """GO if parse OK and ≥1 model lowers FR on the 10 correct smoke rows vs RAGAS, without missing all 10 errors."""
    correct = smoke_meta["correct_fr_ragas"]
    errors = smoke_meta["errors"]
    decision = {"go": False, "reasons": [], "per_model": {}}
    any_better_fr = False
    for slug in MODELS:
        vm = verdict_map_dose(slug)
        rows = [r for r in read_jsonl(OUT / ("%s.jsonl" % slug)) if r["instance_id"] in set(correct + errors + smoke_meta["other"])]
        pf = sum(1 for r in rows if r.get("verdict") == "PARSE_FAIL")
        pf_rate = pf / max(len(rows), 1)
        # FR on 10 correct
        fr_dose = sum(1 for i in correct if vm.get(i) == "FAIL")
        fr_ragas = sum(1 for i in correct if ragas[slug].get(i) == "FAIL")
        # miss on errors = PASS on error
        miss_dose = sum(1 for i in errors if vm.get(i) == "PASS")
        miss_all = miss_dose == len(errors) and all(vm.get(i) in ("PASS", "FAIL") for i in errors)
        better = fr_dose < fr_ragas
        if better and not miss_all:
            any_better_fr = True
        decision["per_model"][slug] = {
            "n_smoke_rows": len(rows),
            "parse_fail": pf,
            "parse_fail_rate": round(pf_rate, 4),
            "fr_on_10_correct_dose": fr_dose,
            "fr_on_10_correct_ragas": fr_ragas,
            "miss_on_10_errors_dose": miss_dose,
            "better_fr": better,
            "missed_all_errors": miss_all,
        }
        if pf_rate >= 0.05:
            decision["reasons"].append("%s parse_fail_rate=%.1f%% >= 5%%" % (slug, 100 * pf_rate))
    if decision["reasons"]:
        decision["go"] = False
        decision["reasons"].insert(0, "NO-GO: parse-fail gate")
    elif any_better_fr:
        decision["go"] = True
        decision["reasons"].append("GO: ≥1 model lowered FR on 10 correct smoke rows vs RAGAS without missing all 10 errors")
    else:
        decision["go"] = False
        decision["reasons"].append("NO-GO: no model improved FR on the 10 correct smoke rows (or all missed all errors)")
    return decision


def write_smoke_md(summary, decision, smoke_meta, v3, ragas):
    lines = [
        "# Dose-focused frontier judges — SMOKE",
        "",
        "Prompt: `%s`. Date: 2026-10-26." % PROMPT_ID,
        "",
        "## Smoke composition (n=30)",
        "",
        "- 10 v3-correct closed that RAGAS false-rejected",
        "- 10 v3 unit/basis errors closed",
        "- 10 other closed (not error/correct/correct_suspect)",
        "",
        "## Per-model smoke",
        "",
        "| model | new | PASS | FAIL | PARSE_FAIL | PF%% | spent$ |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for slug, m in summary.get("per_model", {}).items():
        lines.append("| `%s` | %s | %s | %s | %s | %.1f | %.4f |" % (
            MODELS[slug]["model"], m.get("new_rows"), m.get("pass"), m.get("fail"),
            m.get("parse_fail"), 100 * m.get("parse_fail_rate", 0), m.get("spent_usd", 0)))
    lines += ["", "## GO/NO-GO", "", "**Decision: %s**" % ("GO" if decision["go"] else "NO-GO"), ""]
    for r in decision["reasons"]:
        lines.append("- %s" % r)
    lines += ["", "| model | FR dose/10 | FR RAGAS/10 | miss dose/10 | better FR |",
              "|---|---:|---:|---:|:---:|"]
    for slug, m in decision["per_model"].items():
        lines.append("| `%s` | %d | %d | %d | %s |" % (
            MODELS[slug]["model"], m["fr_on_10_correct_dose"], m["fr_on_10_correct_ragas"],
            m["miss_on_10_errors_dose"], "Y" if m["better_fr"] else "N"))
    lines += ["", "Spent total smoke: **$%.4f**" % summary.get("spent_usd", 0), ""]
    (OUT / "SMOKE.md").write_text("\n".join(lines), encoding="utf-8")
    (OUT / "smoke_decision.json").write_text(json.dumps(decision, indent=2) + "\n")


def write_report(v3, ragas):
    """Full report: dose-focused metrics + side-by-side vs RAGAS on v3 in-scope and full 5688."""
    # scopes
    def ids(kind, cond, scope):
        out = []
        for iid, r in v3.items():
            if cond != "all" and r.get("condition") != cond:
                continue
            if scope == "v3":
                if r.get("excluded_non_dose") == "1":
                    continue
                if kind == "error" and r.get("ref_v3") != "error":
                    continue
                if kind == "nonerror" and r.get("ref_v3") != "nonerror":
                    continue
            else:  # full5688 — use class_v2 via class_v3 mapping: error=unit/basis v2, correct=v2 correct incl suspect?
                # "full 5,688 for continuity" — use class_v2 from label row
                # label_v3 still has class_v2
                if kind == "error" and r.get("class_v2") not in UNIT_TYPE:
                    continue
                if kind == "nonerror" and r.get("class_v2") != "correct":
                    continue
            out.append(iid)
        return out

    # costs
    costs = {}
    for slug in MODELS:
        rows = read_jsonl(OUT / ("%s.jsonl" % slug))
        costs[slug] = {
            "n": len(rows),
            "cost_usd": round(sum(float(r["api_cost_usd"]) for r in rows if isinstance(r.get("api_cost_usd"), (int, float))), 4),
            "verdicts": dict(Counter(r.get("verdict") for r in rows)),
            "api_model": Counter(r.get("api_model") for r in rows).most_common(1)[0][0] if rows else MODELS[slug]["model"],
        }

    rate_rows = []
    for scope in ("v3", "full5688"):
        for slug in MODELS:
            vm_d = verdict_map_dose(slug)
            vm_r = ragas[slug]
            for cond in ("closed", "grounded", "all"):
                for kind, metric_pass, metric_fail in (
                    ("error", "pass_on_error_miss", None),
                    ("nonerror", None, "fail_on_correct_false_reject"),
                ):
                    idlist = ids(kind, cond, scope)
                    for family, vm in (("dose_focused", vm_d), ("ragas_html", vm_r)):
                        st = rate_on(idlist, vm)
                        if kind == "error":
                            k, n = st["k_pass"], st["n"]
                            metric = "pass_on_error_miss"
                        else:
                            k, n = st["k_fail"], st["n"]
                            metric = "fail_on_correct_false_reject"
                        lo, hi = wilson(k, n)
                        rate_rows.append(OrderedDict([
                            ("scope", scope), ("family", family), ("system", slug),
                            ("model", MODELS[slug]["model"]), ("condition", cond),
                            ("reference", kind), ("metric", metric),
                            ("k", k), ("n", n), ("parse_fail", st["parse_fail"]),
                            ("rate_pct", pct(k, n) if n else float("nan")),
                            ("wilson_lo", 100 * lo if n else float("nan")),
                            ("wilson_hi", 100 * hi if n else float("nan")),
                        ]))

    # write CSV
    with (OUT / "rates_dose_focused.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rate_rows[0].keys()))
        w.writeheader()
        w.writerows(rate_rows)

    def cell(scope, family, slug, cond, metric):
        r = next(x for x in rate_rows if x["scope"] == scope and x["family"] == family
                 and x["system"] == slug and x["condition"] == cond and x["metric"] == metric)
        return fmt_rate(r["k"], r["n"]), r

    lines = [
        "# RD2 dose-focused frontier judges — report",
        "",
        "**Exploratory.** Prompt `%s`. Not HTML RAGAS (RAGAS artefacts untouched)." % PROMPT_ID,
        "",
        "## Models & cost",
        "",
        "| slug | api_model | n | verdicts | cost USD |",
        "|---|---|---:|---|---:|",
    ]
    for slug, c in costs.items():
        lines.append("| `%s` | `%s` | %d | %s | **%.2f** |" % (
            slug, c["api_model"], c["n"], c["verdicts"], c["cost_usd"]))
    lines.append("| **total** | | | | **%.2f** |" % sum(c["cost_usd"] for c in costs.values()))
    lines += [
        "",
        "## v3 in-scope (exclude non-dose; hold out correct_suspect) — closed / grounded / all",
        "",
        "Miss = PASS on unit+basis errors; false-reject = FAIL on v3 correct.",
        "",
    ]
    for cond in ("closed", "grounded", "all"):
        lines.append("### Condition: `%s`" % cond)
        lines.append("")
        lines.append("| model | miss dose-focused | miss RAGAS | FR dose-focused | FR RAGAS |")
        lines.append("|---|---|---|---|---|")
        for slug in MODELS:
            md, _ = cell("v3", "dose_focused", slug, cond, "pass_on_error_miss")
            mr, _ = cell("v3", "ragas_html", slug, cond, "pass_on_error_miss")
            fd, _ = cell("v3", "dose_focused", slug, cond, "fail_on_correct_false_reject")
            fr, _ = cell("v3", "ragas_html", slug, cond, "fail_on_correct_false_reject")
            lines.append("| `%s` | %s | %s | %s | %s |" % (MODELS[slug]["model"], md, mr, fd, fr))
        lines.append("")

    lines += [
        "## Full 5,688 continuity (class_v2 error / correct; includes non-dose & correct_suspect-as-correct)",
        "",
    ]
    for cond in ("closed", "grounded", "all"):
        lines.append("### Condition: `%s` (full5688)" % cond)
        lines.append("")
        lines.append("| model | miss dose | miss RAGAS | FR dose | FR RAGAS |")
        lines.append("|---|---|---|---|---|")
        for slug in MODELS:
            md, _ = cell("full5688", "dose_focused", slug, cond, "pass_on_error_miss")
            mr, _ = cell("full5688", "ragas_html", slug, cond, "pass_on_error_miss")
            fd, _ = cell("full5688", "dose_focused", slug, cond, "fail_on_correct_false_reject")
            fr, _ = cell("full5688", "ragas_html", slug, cond, "fail_on_correct_false_reject")
            lines.append("| `%s` | %s | %s | %s | %s |" % (MODELS[slug]["model"], md, mr, fd, fr))
        lines.append("")

    # headline closed v3 comparison
    lines += ["## Headline (v3 closed)", ""]
    for slug in MODELS:
        _, rd = cell("v3", "dose_focused", slug, "closed", "fail_on_correct_false_reject")
        _, rr = cell("v3", "ragas_html", slug, "closed", "fail_on_correct_false_reject")
        _, md = cell("v3", "dose_focused", slug, "closed", "pass_on_error_miss")
        _, mr = cell("v3", "ragas_html", slug, "closed", "pass_on_error_miss")
        dfr = rd["rate_pct"] - rr["rate_pct"] if rd["n"] and rr["n"] else float("nan")
        lines.append("- `%s`: FR %.1f%% → %.1f%% (Δ %+.1f pp); miss %.1f%% → %.1f%%" % (
            MODELS[slug]["model"], rr["rate_pct"], rd["rate_pct"], dfr, mr["rate_pct"], md["rate_pct"]))
    lines += [
        "",
        "## Files",
        "",
        "- `claude_sonnet.jsonl`, `gpt4o.jsonl`, `deepseek_chat.jsonl`",
        "- `rates_dose_focused.csv`, `report_dose_focused.json`",
        "- `SMOKE.md`, `smoke_decision.json`",
        "",
        "RAGAS paths under `frontier_judges/` were not modified.",
        "",
    ]
    (OUT / "report_dose_focused.md").write_text("\n".join(lines), encoding="utf-8")
    payload = {
        "prompt_id": PROMPT_ID,
        "costs": costs,
        "rates": rate_rows,
        "spent_usd_total": sum(c["cost_usd"] for c in costs.values()),
    }
    (OUT / "report_dose_focused.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    log(stage="report_written", spent=payload["spent_usd_total"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--max-usd", type=float, default=2.0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--slugs", default="claude_sonnet,gpt4o,deepseek_chat")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    questions, instances, answers, v3, ragas = load_pack()
    slugs = [s.strip() for s in args.slugs.split(",") if s.strip()]

    if args.report_only:
        write_report(v3, ragas)
        return

    if args.smoke:
        ids = build_smoke_ids(v3, ragas)
        log(stage="smoke_ids", n=len(ids))
        summary = run_batch(slugs, ids, questions, instances, answers, v3,
                            max_usd=args.max_usd, workers=args.workers, tag="smoke")
        smoke_meta = json.loads((OUT / "smoke_ids.json").read_text())
        decision = go_nogo(v3, ragas, smoke_meta)
        write_smoke_md(summary, decision, smoke_meta, v3, ragas)
        log(stage="smoke_decision", go=decision["go"], reasons=decision["reasons"])
        if not decision["go"]:
            raise SystemExit("NO-GO after smoke — full run not started")
        return

    if args.full:
        # require smoke decision GO if present
        dec_path = OUT / "smoke_decision.json"
        if dec_path.is_file():
            dec = json.loads(dec_path.read_text())
            if not dec.get("go"):
                raise SystemExit("Refusing --full: smoke_decision.json says NO-GO")
        ids = sorted(instances.keys())
        summary = run_batch(slugs, ids, questions, instances, answers, v3,
                            max_usd=args.max_usd, workers=args.workers, tag="full")
        write_report(v3, ragas)
        log(stage="full_done", **{k: summary.get(k) for k in ("spent_usd",)})
        return

    raise SystemExit("Specify --smoke, --full, or --report-only")


if __name__ == "__main__":
    main()
