"""Qwen paraphrases and Phi-4 checks for QC v3. One GPU, resumable."""

from __future__ import annotations

import json
from pathlib import Path

from qc_v3 import extra_hedges, sentence_rule_failure, span_once
from stage12_llm import (
    GEN_MODEL,
    GEN_REV,
    VAL_MODEL,
    VAL_REV,
    first_word,
    load_llm,
    render,
    unload,
    yes_no,
)

ROOT = Path("/data2/hpcshared/medverif-audit")
OUT = ROOT / "data" / "v3"
PARA_SYSTEM = (
    "You rewrite one medical sentence. Return one sentence only, with no preamble. "
    "It must be grammatical, start with a capital letter, and end with a period. "
    "Copy the target span exactly once, character for character. "
    "Do not add or remove qualifiers or facts. "
    "Do not introduce these words unless they are already in the original: "
    "exactly, only, up to, at least, approximately, about, always, never, usually, may, in clinical use."
)
FLUENCY_SYSTEM = "You judge whether a sentence is grammatical and fluent. Reply with one word: YES or NO."
MEANING_SYSTEM = (
    "You judge whether a rewrite means the same thing as the original. "
    "Reply with one word: YES or NO. "
    "YES only if nothing was added or removed and the target fact is unchanged."
)
KIND_SYSTEM = (
    "Label the dose statement with one word: prescriptive, descriptive, or measurement. "
    "prescriptive means an administration or recommendation. "
    "descriptive means a study report, dietary intake, or nutrition target. "
    "measurement means a lab value or diagnostic threshold."
)
DOMAIN_SYSTEM = (
    "Label the recommendation with one word: treatment, diagnostic_procedure, or other. "
    "treatment is a drug, vaccine, or therapy. "
    "diagnostic_procedure is a test, image, or diagnostic procedure. "
    "other includes coding rules and specifiers."
)
HINTS = (
    "Use different wording and a different clause order.",
    "The previous attempt was rejected. Write a different single grammatical sentence. Do not add qualifiers.",
    "Write one formal sentence a clinician could read aloud. Change the structure. Do not add quantity or force.",
)


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def rule_failure(original: str, rewrite: str, span: str) -> str | None:
    reason = sentence_rule_failure(rewrite)
    if reason:
        return reason
    if not span_once(rewrite, span):
        return "span_count"
    extra = extra_hedges(rewrite, original)
    if extra:
        return "added_hedge:" + ",".join(extra)
    if rewrite.strip() == original.strip():
        return "unchanged"
    return None


def claim_of(todo: list[dict], base_id: str) -> str:
    for row in todo:
        if row["base_id"] == base_id:
            return row["claim"]
    return ""


def phi_labels(llm, tokenizer, system: str, users: list[str]) -> list[str]:
    if not users:
        return []
    return [row["label"] for row in yes_no(llm, tokenizer, system, users, 8)]


def generate_round(pending: list[dict], attempt: int) -> list[dict]:
    llm = load_llm(GEN_MODEL, GEN_REV)
    tokenizer = llm.get_tokenizer()
    from vllm import SamplingParams

    prompts = []
    for row in pending:
        user = (
            f"Target span (copy verbatim, once): {row['span']}\n"
            f"Original sentence:\n{row['claim']}\n"
            f"Instruction: {HINTS[attempt - 1]}"
        )
        prompts.append(render(tokenizer, PARA_SYSTEM, user))
    outputs = llm.generate(prompts, SamplingParams(temperature=0.0, max_tokens=160, seed=42))
    records = []
    for row, out in zip(pending, outputs):
        text = (out.outputs[0].text or "").strip().split("\n")[0].strip().strip('"')
        records.append({
            "base_id": row["base_id"],
            "attempt": attempt,
            "text": text,
            "rule": rule_failure(row["claim"], text, row["span"]),
            "fluency": None,
            "meaning": None,
            "passed": False,
            "raw_output": out.outputs[0].text,
        })
    unload(llm)
    return records


def run_phi(need: list[dict], todo: list[dict], flips: list[dict], do_side: bool) -> None:
    llm = load_llm(VAL_MODEL, VAL_REV)
    tokenizer = llm.get_tokenizer()
    fluency = phi_labels(llm, tokenizer, FLUENCY_SYSTEM, [
        f"Sentence:\n{row['text']}\nGrammatical and fluent?" for row in need
    ])
    meaning = phi_labels(llm, tokenizer, MEANING_SYSTEM, [
        "Original:\n" + claim_of(todo, row["base_id"]) + "\n\nRewrite:\n" + row["text"] + "\n\nSame meaning, nothing added?"
        for row in need
    ])
    for row, flu, mean in zip(need, fluency, meaning):
        row["fluency"] = flu
        row["meaning"] = mean
        row["passed"] = flu == "YES" and mean == "YES"
    if do_side:
        label_flips(llm, tokenizer, flips)
        label_kinds(llm, tokenizer, todo)
    unload(llm)


def label_flips(llm, tokenizer, flips: list[dict]) -> None:
    path = OUT / "flip_fluency.jsonl"
    if path.exists():
        return
    records = []
    need = []
    for row in flips:
        reason = sentence_rule_failure(row["claim"])
        if reason:
            records.append({"base_id": row["base_id"], "fluency": "NO", "rule": reason})
        else:
            need.append(row)
    labels = phi_labels(llm, tokenizer, FLUENCY_SYSTEM, [
        f"Sentence:\n{row['claim']}\nGrammatical and fluent?" for row in need
    ])
    for row, label in zip(need, labels):
        records.append({"base_id": row["base_id"], "fluency": label, "rule": None})
    append_jsonl(path, records)


def label_kinds(llm, tokenizer, todo: list[dict]) -> None:
    from vllm import SamplingParams

    params = SamplingParams(temperature=0.0, max_tokens=8, seed=42)
    dose_path = OUT / "dose_kind_phi.jsonl"
    if not dose_path.exists():
        rows = [row for row in todo if row.get("need_dose_kind")]
        if rows:
            prompts = [render(tokenizer, KIND_SYSTEM, "Statement:\n" + row["claim"] + "\nLabel:") for row in rows]
            written = []
            for row, out in zip(rows, llm.generate(prompts, params)):
                word = first_word(out.outputs[0].text).lower()
                if word not in {"prescriptive", "descriptive", "measurement"}:
                    word = "unclear"
                written.append({"base_id": row["base_id"], "dose_kind": word, "raw_output": out.outputs[0].text})
            append_jsonl(dose_path, written)
        else:
            dose_path.write_text("")
    domain_path = OUT / "domain_phi.jsonl"
    if not domain_path.exists():
        rows = [row for row in todo if row.get("need_domain")]
        if rows:
            prompts = [render(tokenizer, DOMAIN_SYSTEM, "Statement:\n" + row["claim"] + "\nLabel:") for row in rows]
            written = []
            for row, out in zip(rows, llm.generate(prompts, params)):
                word = first_word(out.outputs[0].text).lower()
                if word not in {"treatment", "diagnostic_procedure", "other"}:
                    word = "unclear"
                written.append({"base_id": row["base_id"], "domain_kind": word, "raw_output": out.outputs[0].text})
            append_jsonl(domain_path, written)
        else:
            domain_path.write_text("")


def main() -> None:
    todo = read_jsonl(OUT / "paraphrase_todo.jsonl")
    flips = read_jsonl(OUT / "flip_fluency_todo.jsonl")
    by_base: dict[str, list[dict]] = {}
    for row in read_jsonl(OUT / "para_attempts.jsonl"):
        by_base.setdefault(row["base_id"], []).append(row)

    def passed(base_id: str) -> bool:
        return any(item.get("passed") for item in by_base.get(base_id, []))

    side_done = False
    for attempt in (1, 2, 3):
        pending = []
        for row in todo:
            prior = by_base.get(row["base_id"], [])
            if passed(row["base_id"]) or any(item.get("attempt") == attempt for item in prior):
                continue
            pending.append(row)
        if not pending and side_done:
            continue
        fresh = generate_round(pending, attempt) if pending else []
        need = [row for row in fresh if row["rule"] is None]
        do_side = not side_done
        if need or do_side:
            run_phi(need, todo, flips, do_side)
            side_done = True
        for row in fresh:
            by_base.setdefault(row["base_id"], []).append(row)
        append_jsonl(OUT / "para_attempts.jsonl", fresh)
    from apply_v3 import main as apply_main
    apply_main()
    from write_qc_v3 import main as qc_main
    qc_main()


if __name__ == "__main__":
    main()
