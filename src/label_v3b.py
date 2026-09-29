"""Phi-4 only: validate paraphrase attempts, side labels, apply_v3. One GPU load."""

from __future__ import annotations

import json
import os
from pathlib import Path

from generate_v3 import (
    FLUENCY_SYSTEM,
    KIND_SYSTEM,
    DOMAIN_SYSTEM,
    MEANING_SYSTEM,
    OUT,
    claim_of,
    phi_labels,
    read_jsonl,
    append_jsonl,
    log,
)
from qc_v3 import sentence_rule_failure
from stage12_llm import VAL_MODEL, VAL_REV, first_word, load_llm, render, unload

MAX_PARAPHRASE_ATTEMPT = 2
PHI_BATCH = 64


def write_jsonl(path: Path, rows: list[dict]) -> None:
    from safe_jsonl import write_jsonl_atomic

    write_jsonl_atomic(path, rows)


def load_attempts() -> list[dict]:
    rows = []
    for row in read_jsonl(OUT / "para_attempts.jsonl"):
        if row.get("attempt", 99) <= MAX_PARAPHRASE_ATTEMPT:
            rows.append(row)
    return rows


def save_attempts(rows: list[dict]) -> None:
    write_jsonl(OUT / "para_attempts.jsonl", rows)


def validate_paraphrases(llm, tokenizer, attempts: list[dict], todo: list[dict]) -> None:
    need = [row for row in attempts if row.get("rule") is None and row.get("fluency") is None]
    log(f"phi paraphrase validate n={len(need)}")
    for start in range(0, len(need), PHI_BATCH):
        chunk = need[start : start + PHI_BATCH]
        flu = phi_labels(llm, tokenizer, FLUENCY_SYSTEM, [
            f"Sentence:\n{row['text']}\nGrammatical and fluent?" for row in chunk
        ])
        mean = phi_labels(llm, tokenizer, MEANING_SYSTEM, [
            "Original:\n" + claim_of(todo, row["base_id"]) + "\n\nRewrite:\n" + row["text"]
            + "\n\nSame meaning, nothing added?"
            for row in chunk
        ])
        for row, f, m in zip(chunk, flu, mean):
            row["fluency"] = f
            row["meaning"] = m
            row["passed"] = f == "YES" and m == "YES"
        save_attempts(attempts)
        log(f"phi paraphrase batch {start // PHI_BATCH + 1} saved")


def label_flips_session(llm, tokenizer, flips: list[dict]) -> None:
    path = OUT / "flip_fluency.jsonl"
    done = {row["base_id"] for row in read_jsonl(path)}
    records = []
    need = []
    for row in flips:
        if row["base_id"] in done:
            continue
        reason = sentence_rule_failure(row["claim"])
        if reason:
            records.append({"base_id": row["base_id"], "fluency": "NO", "rule": reason})
        else:
            need.append(row)
    for start in range(0, len(need), PHI_BATCH):
        chunk = need[start : start + PHI_BATCH]
        labels = phi_labels(llm, tokenizer, FLUENCY_SYSTEM, [
            f"Sentence:\n{row['claim']}\nGrammatical and fluent?" for row in chunk
        ])
        for row, label in zip(chunk, labels):
            records.append({"base_id": row["base_id"], "fluency": label, "rule": None})
        if records:
            append_jsonl(path, records)
            records = []
    if records:
        append_jsonl(path, records)


def label_kinds_session(llm, tokenizer, todo: list[dict]) -> None:
    from vllm import SamplingParams

    params = SamplingParams(temperature=0.0, max_tokens=8, seed=42)
    dose_path = OUT / "dose_kind_phi.jsonl"
    done_dose = {row["base_id"] for row in read_jsonl(dose_path)}
    dose_rows = [row for row in todo if row.get("need_dose_kind") and row["base_id"] not in done_dose]
    if dose_rows:
        prompts = [render(tokenizer, KIND_SYSTEM, "Statement:\n" + row["claim"] + "\nLabel:") for row in dose_rows]
        written = []
        for row, out in zip(dose_rows, llm.generate(prompts, params)):
            word = first_word(out.outputs[0].text).lower()
            if word not in {"prescriptive", "descriptive", "measurement"}:
                word = "unclear"
            written.append({"base_id": row["base_id"], "dose_kind": word, "raw_output": out.outputs[0].text})
        append_jsonl(dose_path, written)
    domain_path = OUT / "domain_phi.jsonl"
    done_dom = {row["base_id"] for row in read_jsonl(domain_path)}
    dom_rows = [row for row in todo if row.get("need_domain") and row["base_id"] not in done_dom]
    if dom_rows:
        prompts = [render(tokenizer, DOMAIN_SYSTEM, "Statement:\n" + row["claim"] + "\nLabel:") for row in dom_rows]
        written = []
        for row, out in zip(dom_rows, llm.generate(prompts, params)):
            word = first_word(out.outputs[0].text).lower()
            if word not in {"treatment", "diagnostic_procedure", "other"}:
                word = "unclear"
            written.append({"base_id": row["base_id"], "domain_kind": word, "raw_output": out.outputs[0].text})
        append_jsonl(domain_path, written)


def log_skip_attempt3(todo: list[dict], attempts: list[dict]) -> None:
    by_base: dict[str, list[dict]] = {}
    for row in attempts:
        by_base.setdefault(row["base_id"], []).append(row)

    def passed(base_id: str) -> bool:
        return any(r.get("passed") for r in by_base.get(base_id, []))

    no_inv = [row["base_id"] for row in todo if not passed(row["base_id"])]
    stats = {
        "max_attempt": MAX_PARAPHRASE_ATTEMPT,
        "paraphrase_todo": len(todo),
        "no_inv_paraphrase_bases": len(no_inv),
        "no_inv_paraphrase_base_ids": no_inv,
        "note": "Attempt 3 not run; bases without a passed attempt 1–2 get no INV-paraphrase.",
    }
    (OUT / "label_v3b_skip.json").write_text(json.dumps(stats, indent=2) + "\n")
    log(json.dumps({k: stats[k] for k in stats if k != "no_inv_paraphrase_base_ids"}))


def main() -> None:
    log(f"label_v3b start host={os.uname().nodename} pid={os.getpid()}")
    todo = read_jsonl(OUT / "paraphrase_todo.jsonl")
    flips = read_jsonl(OUT / "flip_fluency_todo.jsonl")
    attempts = load_attempts()
    log(f"attempts={len(attempts)} todo={len(todo)} flips={len(flips)}")
    llm = load_llm(VAL_MODEL, VAL_REV, enforce_eager=True)
    log("phi loaded")
    tokenizer = llm.get_tokenizer()
    validate_paraphrases(llm, tokenizer, attempts, todo)
    label_flips_session(llm, tokenizer, flips)
    label_kinds_session(llm, tokenizer, todo)
    log_skip_attempt3(todo, attempts)
    unload(llm)
    log("phi unloaded")
    from apply_v3 import main as apply_main
    apply_main()
    from write_qc_v3 import main as qc_main
    qc_main()
    log("label_v3b done")


if __name__ == "__main__":
    main()
