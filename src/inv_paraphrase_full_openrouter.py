"""G — full INV paraphrase run (OpenRouter Qwen72B + Gemini flash validator)."""

from __future__ import annotations

import json
import os
import re
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from generate_v3 import OUT, read_jsonl, append_jsonl
from inv_paraphrase_openrouter import GEN_OR, generate_one, valid_main_bases
from inv_paraphrase_rules import rule_failure_v2
from inv_manual_review_csv import write_manual_review_csv
from inv_paraphrase_validator import pick_validator_model, validate_pair
from openrouter_runtime import load_tokenizer

ROOT = Path("/data2/hpcshared/medverif-audit")
QC_V3B = ROOT / "qc" / "qc_samples_inv_v3b.md"
ATTEMPTS = OUT / "para_attempts_g.jsonl"
INSTANCES = OUT / "instances_g_inv_paraphrase.jsonl"
MANUAL_CSV = ROOT / "qc" / "inv_manual_review.csv"
REPORT = ROOT / "notes" / "g_full_run_report.md"
LOG_MODEL = ROOT / "notes" / "g_inv_validator_model.json"
G_ACTIVE = ROOT / ".cache" / "g_full.active"

SANITY_MUST_REJECT = ("D0004", "D0005", "D0007", "P0087")
SANITY_MUST_PASS = (
    "D0001",
    "D0008",
    "D0009",
    "D0011",
    "D0013",
    "P0019",
    "P0021",
    "P0004",
    "P0046",
    "P0085",
    "P0097",
)

_append_lock = threading.Lock()
_results_lock = threading.Lock()


def parse_v3b_rewrites(path: Path) -> dict[str, tuple[str, str, str]]:
    text = path.read_text()
    blocks = re.split(r"\n## ", text)[1:]
    out: dict[str, tuple[str, str, str]] = {}
    for block in blocks:
        head = block.split("\n", 1)[0]
        m = re.match(r"(\w+)\s+\((\w+)", head)
        if not m:
            continue
        bid, typ = m.group(1), m.group(2)
        orig = re.search(r"\*\*Original\*\*\n```\n(.*?)```", block, re.S)
        rew = re.search(r"\*\*Rewrite\*\*\n```\n(.*?)```", block, re.S)
        if orig and rew:
            out[bid] = (typ, orig.group(1).strip(), rew.group(1).strip())
    return out


def claim_map(todo: list[dict]) -> dict[str, dict]:
    return {r["base_id"]: r for r in todo}


def load_by_base(path: Path) -> dict[str, list[dict]]:
    by: dict[str, list[dict]] = {}
    for row in read_jsonl(path):
        by.setdefault(row["base_id"], []).append(row)
    return by


def real_attempts(rows: list[dict]) -> list[dict]:
    return [r for r in rows if not r.get("gen_error")]


def base_finished(rows: list[dict], max_attempts: int = 3) -> bool:
    if any(r.get("passed") for r in rows):
        return True
    return len(real_attempts(rows)) >= max_attempts


def result_from_attempts(row: dict, attempts: list[dict]) -> dict:
    passed = any(a.get("passed") for a in attempts)
    chosen = next((a for a in attempts if a.get("passed")), attempts[-1] if attempts else None)
    return {
        "row": row,
        "chosen": chosen,
        "attempts": attempts,
        "passed": passed,
    }


def pipeline_pass(row: dict, rewrite: str, val_model: str, val_tok, val_provider: str | None) -> tuple[bool, str | None, dict]:
    rule = rule_failure_v2(row["claim"], rewrite, row["span"])
    if rule:
        return False, rule, {"rule": rule}
    ok, vmeta = validate_pair(row["claim"], rewrite, model=val_model, tok=val_tok, provider=val_provider)
    if not ok:
        tag = vmeta.get("hard_reject") or f"validator:{vmeta.get('fluent')}/{vmeta.get('same_meaning')}"
        return False, tag, vmeta
    return True, None, vmeta


def run_sanity(
    todo_by_id: dict[str, dict],
    v3b: dict[str, tuple[str, str, str]],
    val_model: str,
    val_tok,
    val_provider: str | None,
) -> None:
    failures: list[str] = []
    for bid in SANITY_MUST_REJECT:
        row = todo_by_id.get(bid)
        if not row or bid not in v3b:
            failures.append(f"{bid}: missing todo or v3b rewrite")
            continue
        _, _, rewrite = v3b[bid]
        passed, reason, vmeta = pipeline_pass(row, rewrite, val_model, val_tok, val_provider)
        if passed:
            failures.append(f"{bid}: expected reject, got pass (validator {vmeta})")
        else:
            print(json.dumps({"sanity_reject_ok": bid, "reason": reason}), flush=True)
    for bid in SANITY_MUST_PASS:
        row = todo_by_id.get(bid)
        if not row or bid not in v3b:
            failures.append(f"{bid}: missing todo or v3b rewrite")
            continue
        _, _, rewrite = v3b[bid]
        passed, reason, vmeta = pipeline_pass(row, rewrite, val_model, val_tok, val_provider)
        if not passed:
            failures.append(f"{bid}: expected pass, got {reason} ({vmeta.get('reason')})")
        else:
            print(json.dumps({"sanity_pass_ok": bid}), flush=True)
    if failures:
        raise SystemExit("sanity check failed:\n" + "\n".join(failures))


def load_c0_main() -> dict[str, dict]:
    path = OUT / "instances_cpu_main.jsonl"
    if not path.exists():
        path = OUT / "instances_main.jsonl"
    c0 = {}
    for row in read_jsonl(path):
        if row.get("condition") == "C0" and row.get("subset") == "main" and row.get("valid"):
            c0[row["base_id"]] = row
    return c0


def write_instances_and_csv(results: list[dict], c0: dict[str, dict]) -> int:
    accepted: list[dict] = []
    csv_rows: list[dict] = []
    for res in results:
        if not res.get("passed") or not res.get("chosen"):
            continue
        row = res["row"]
        src = c0.get(row["base_id"])
        if not src:
            continue
        rewrite = res["chosen"]["text"]
        item = dict(src)
        item["instance_id"] = f"{row['base_id']}__INV-claim__paraphrase_v3"
        item["condition"] = "INV-claim"
        item["magnitude"] = "paraphrase"
        item["claim"] = rewrite
        item["evidence"] = src.get("evidence_c0") or src["evidence"]
        item["expected_verdict"] = "PASS"
        item["valid"] = True
        item["invalid_reason"] = None
        item["diff"] = {"where": "paraphrase_v3", "attempt": res["chosen"]["attempt"]}
        accepted.append(item)
        csv_rows.append(
            {
                "base_id": row["base_id"],
                "type": row["type"],
                "original": row["claim"],
                "rewrite": rewrite,
            }
        )
    from apply_v3 import write_jsonl

    write_jsonl(INSTANCES, accepted)
    write_manual_review_csv(MANUAL_CSV, csv_rows)
    return len(accepted)


def process_base_full(
    row: dict,
    gen_tok,
    val_model: str,
    val_tok,
    gen_provider: str | None,
    val_provider: str | None,
    prior: list[dict],
    max_attempts: int = 3,
) -> dict:
    attempts_log = list(prior)
    chosen: dict | None = next((a for a in prior if a.get("passed")), None)
    if chosen:
        return result_from_attempts(row, attempts_log)

    start_attempt = len(real_attempts(prior)) + 1
    for attempt in range(start_attempt, max_attempts + 1):
        try:
            rewrite, gmeta = generate_one(row, attempt, gen_tok, gen_provider)
        except Exception as exc:  # noqa: BLE001 — log and defer base
            entry = {
                "base_id": row["base_id"],
                "attempt": attempt,
                "text": "",
                "rule": "gen_error",
                "gen_error": True,
                "error": str(exc),
                "passed": False,
                "validator": {},
                "gen": {},
            }
            with _append_lock:
                append_jsonl(ATTEMPTS, [entry])
            attempts_log.append(entry)
            print(json.dumps({"gen_error": row["base_id"], "attempt": attempt, "err": str(exc)[:200]}), flush=True)
            break

        rule = rule_failure_v2(row["claim"], rewrite, row["span"])
        passed = False
        vmeta: dict = {}
        if rule is None:
            passed, vmeta = validate_pair(
                row["claim"], rewrite, model=val_model, tok=val_tok, provider=val_provider
            )
        entry = {
            "base_id": row["base_id"],
            "attempt": attempt,
            "text": rewrite,
            "rule": rule,
            "passed": passed and rule is None,
            "validator": vmeta,
            "gen": gmeta,
        }
        with _append_lock:
            append_jsonl(ATTEMPTS, [entry])
        attempts_log.append(entry)
        if entry["passed"]:
            chosen = entry
            break
        time.sleep(0.05)

    if chosen is None and attempts_log:
        chosen = attempts_log[-1]
    return result_from_attempts(row, attempts_log)


def write_final_report(results: list[dict], n_acc: int, val_model: str) -> None:
    by_type = Counter(r["row"]["type"] for r in results if r["passed"])
    denom = Counter(r["row"]["type"] for r in results)
    lines = [
        "# G full run — INV paraphrase (OpenRouter)",
        "",
        f"- Generator: `{GEN_OR}`",
        f"- Validator: `{val_model}` (see `notes/g_inv_validator_model.json`)",
        f"- Bases: {len(results)} valid main (DOSE + POLARITY, rule B filter)",
        f"- Accepted: **{n_acc}/{len(results)}** ({n_acc / max(len(results), 1):.1%})",
        "",
        "## Pass rate by type",
        "",
        "| type | passed | total | rate |",
        "|------|--------|-------|------|",
    ]
    for typ in sorted(denom):
        p = by_type.get(typ, 0)
        d = denom[typ]
        lines.append(f"| {typ} | {p} | {d} | {p / d:.1%} |")
    lines += [
        "",
        f"- Attempts log: `{ATTEMPTS.relative_to(ROOT)}`",
        f"- Instances: `{INSTANCES.relative_to(ROOT)}`",
        f"- Manual review: `{MANUAL_CSV.relative_to(ROOT)}`",
        "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n")


def main() -> None:
    resume = os.environ.get("MEDVERIF_G_RESUME", "1").lower() in ("1", "true", "yes")
    if not resume and ATTEMPTS.exists():
        ATTEMPTS.unlink()

    G_ACTIVE.parent.mkdir(parents=True, exist_ok=True)
    G_ACTIVE.write_text(f"started={time.strftime('%Y-%m-%dT%H:%M:%S')}\n")

    todo_all = read_jsonl(OUT / "paraphrase_todo.jsonl")
    todo = valid_main_bases(todo_all)
    todo_by_id = claim_map(todo)
    v3b = parse_v3b_rewrites(QC_V3B)
    by_base = load_by_base(ATTEMPTS) if ATTEMPTS.exists() else {}

    gen_provider = os.environ.get("MEDVERIF_PARA_GEN_PROVIDER")
    val_provider = os.environ.get("MEDVERIF_PARA_VAL_PROVIDER")
    val_model, val_tok_id = pick_validator_model(val_provider)
    LOG_MODEL.write_text(json.dumps({"validator_model": val_model, "gen": GEN_OR}, indent=2) + "\n")

    gen_tok = load_tokenizer(
        os.environ.get("MEDVERIF_PARA_GEN_TOKENIZER", "Qwen/Qwen2.5-72B-Instruct"),
        os.environ.get("MEDVERIF_PARA_GEN_REV"),
    )
    val_tok = load_tokenizer(val_tok_id, None)

    skip_sanity = resume and by_base and os.environ.get("MEDVERIF_G_SKIP_SANITY", "1").lower() in (
        "1",
        "true",
        "yes",
    )
    if not skip_sanity:
        run_sanity(todo_by_id, v3b, val_model, val_tok, val_provider)
    else:
        print(json.dumps({"sanity": "skipped_resume"}), flush=True)

    c0 = load_c0_main()
    results: dict[str, dict] = {}
    for row in todo:
        bid = row["base_id"]
        prior = by_base.get(bid, [])
        if prior:
            results[bid] = result_from_attempts(row, prior)
    if results:
        n0 = write_instances_and_csv(list(results.values()), c0)
        print(json.dumps({"resume_flush": True, "accepted": n0, "bases": len(results)}), flush=True)

    pending = [row for row in todo if not base_finished(by_base.get(row["base_id"], []))]

    print(
        json.dumps(
            {
                "full_run_start": len(todo),
                "pending": len(pending),
                "resume_results": len(results),
                "validator": val_model,
            }
        ),
        flush=True,
    )

    workers = min(3, int(os.environ.get("MEDVERIF_G_WORKERS", "1")))
    completed_since_flush = 0

    def run_one(row: dict) -> tuple[str, dict]:
        prior = by_base.get(row["base_id"], [])
        if base_finished(prior):
            return row["base_id"], result_from_attempts(row, prior)
        res = process_base_full(
            row, gen_tok, val_model, val_tok, gen_provider, val_provider, prior
        )
        by_base[row["base_id"]] = res["attempts"]
        return row["base_id"], res

    def flush_if_needed(force: bool = False) -> None:
        nonlocal completed_since_flush
        if not force and completed_since_flush < 10:
            return
        with _results_lock:
            n_acc = write_instances_and_csv(list(results.values()), c0)
        print(json.dumps({"incremental_flush": True, "accepted": n_acc, "bases": len(results)}), flush=True)
        completed_since_flush = 0

    if workers <= 1:
        for i, row in enumerate(pending, 1):
            if i % 10 == 1:
                print(json.dumps({"progress": i, "of": len(pending)}), flush=True)
            bid, res = run_one(row)
            results[bid] = res
            completed_since_flush += 1
            flush_if_needed()
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(run_one, row): row for row in pending}
            for i, fut in enumerate(as_completed(futs), 1):
                bid, res = fut.result()
                with _results_lock:
                    results[bid] = res
                    completed_since_flush += 1
                if i % 10 == 0:
                    print(json.dumps({"progress": i, "of": len(pending)}), flush=True)
                flush_if_needed()

    flush_if_needed(force=True)
    ordered = [results[r["base_id"]] for r in todo if r["base_id"] in results]
    n_acc = write_instances_and_csv(ordered, c0)
    write_final_report(ordered, n_acc, val_model)
    G_ACTIVE.unlink(missing_ok=True)
    print(json.dumps({"report": str(REPORT), "accepted": n_acc, "n": len(ordered)}))


if __name__ == "__main__":
    main()
