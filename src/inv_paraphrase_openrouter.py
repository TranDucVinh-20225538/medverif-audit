"""G — INV paraphrase pilot via OpenRouter (generator ≠ validator ≠ V1/V4)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from generate_v3 import FLUENCY_SYSTEM, HINTS, MEANING_SYSTEM, OUT, PARA_SYSTEM, read_jsonl, rule_failure
from inv_paraphrase_rules import rule_failure_v2
from llm_client import chat
from openrouter_runtime import load_tokenizer
from qc_v3 import polarity_flip_allowed
from stage12_llm import render

ROOT = Path("/data2/hpcshared/medverif-audit")
PILOT_VERSION = os.environ.get("MEDVERIF_G_PILOT_VERSION", "v2")
QC = ROOT / "qc" / (
    "qc_samples_inv_v3b.md" if PILOT_VERSION == "v2" else "qc_samples_inv_v3.md"
)

GEN_OR = os.environ.get("MEDVERIF_PARA_GEN_MODEL", "qwen/qwen-2.5-72b-instruct")
VAL_OR = os.environ.get("MEDVERIF_PARA_VAL_MODEL", "microsoft/phi-4")
GEN_TOK = os.environ.get("MEDVERIF_PARA_GEN_TOKENIZER", "Qwen/Qwen2.5-72B-Instruct")
GEN_REV = os.environ.get("MEDVERIF_PARA_GEN_REV") or None
VAL_TOK = os.environ.get("MEDVERIF_PARA_VAL_TOKENIZER", "microsoft/phi-4")
VAL_REV = os.environ.get("MEDVERIF_PARA_VAL_REV", "2db69c1c3e91a05d2c64a3185acfbaf36f744e25")

PARA_SYSTEM_V2 = (
    "You rewrite one medical sentence. Return one sentence only, with no preamble. "
    "It must be grammatical, start with a capital letter, and end with a period. "
    "A real paraphrase restructures the clause: use active↔passive voice, reorder clauses, "
    "and synonyms for words OUTSIDE the target span. "
    "Do NOT merely move an adverbial or prepositional phrase to the start of the sentence. "
    "Copy the target span exactly once, character for character. "
    "Keep every qualifier and hedge; add nothing; remove nothing."
)

HINTS_V2 = (
    "Restructure with active↔passive or clause reordering; do not front a trailing phrase.",
    "Previous attempt rejected. Change structure and wording; keep the target span verbatim; no fronting.",
    "Write one formal clinical sentence with a different structure than the original; keep all qualifiers.",
)


def valid_main_bases(todo: list[dict]) -> list[dict]:
    out: list[dict] = []
    for row in todo:
        if row.get("subset") != "main":
            continue
        if row.get("type") == "POLARITY":
            block = polarity_flip_allowed(row["claim"], row["span"], row.get("base_id", ""))
            if block:
                continue
        out.append(row)
    out.sort(key=lambda r: r["base_id"])
    return out


def pilot_bases(todo: list[dict]) -> list[dict]:
    if PILOT_VERSION == "v2":
        valid = valid_main_bases(todo)
        dose = [r for r in valid if r.get("type") == "DOSE"][:10]
        pol = [r for r in valid if r.get("type") == "POLARITY"][:10]
        return dose + pol
    dose = [r for r in todo if r.get("type") == "DOSE"]
    pol = [r for r in todo if r.get("type") == "POLARITY"]
    return dose[:5] + pol[:5]


def check_rules(original: str, rewrite: str, span: str) -> str | None:
    if PILOT_VERSION == "v2":
        return rule_failure_v2(original, rewrite, span)
    return rule_failure(original, rewrite, span)


def para_system() -> str:
    return PARA_SYSTEM_V2 if PILOT_VERSION == "v2" else PARA_SYSTEM


def hints_for(attempt: int) -> str:
    hints = HINTS_V2 if PILOT_VERSION == "v2" else HINTS
    return hints[min(attempt - 1, len(hints) - 1)]


def one_word(system: str, user: str, *, model: str, tok, provider: str | None) -> tuple[str, dict]:
    prompt = render(tok, system, user)
    resp = chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=16,
        provider=provider,
        allow_fallbacks=False,
    )
    text = resp.text or ""
    word = text.strip().split()[0].upper() if text.strip() else "?"
    if word not in {"YES", "NO"}:
        word = "YES" if word.startswith("Y") else "NO" if word.startswith("N") else word
    return word, {
        "provider": resp.provider,
        "request_id": resp.request_id,
        "model": resp.model,
        "tokens": resp.total_tokens,
        "cost_usd": resp.cost_usd,
    }


def generate_one(
    row: dict,
    attempt: int,
    gen_tok,
    gen_provider: str | None,
) -> tuple[str, dict]:
    seed = 42 + attempt - 1
    temperature = 0.0 if attempt == 1 else 0.7
    user = (
        f"Target span (copy verbatim, once): {row['span']}\n"
        f"Original sentence:\n{row['claim']}\n"
        f"Instruction: {hints_for(attempt)}"
    )
    prompt = render(gen_tok, para_system(), user)
    gen_fb = os.environ.get("MEDVERIF_PARA_GEN_ALLOW_FALLBACKS", "").lower() in (
        "1",
        "true",
        "yes",
    )
    resp = chat(
        model=GEN_OR,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=160,
        temperature=temperature,
        seed=seed,
        provider=gen_provider,
        allow_fallbacks=gen_fb,
        max_retries=int(os.environ.get("MEDVERIF_OR_MAX_RETRIES", "12")),
    )
    rewrite = (resp.text or "").strip().split("\n")[0].strip().strip('"')
    return rewrite, {
        "provider": resp.provider,
        "request_id": resp.request_id,
        "model": resp.model,
        "generator": GEN_OR,
        "attempt": attempt,
        "seed": seed,
        "temperature": temperature,
    }


def process_base(
    row: dict,
    gen_tok,
    val_tok,
    gen_provider: str | None,
    val_provider: str | None,
    max_attempts: int,
) -> dict:
    attempts_log: list[dict] = []
    chosen: dict | None = None
    for attempt in range(1, max_attempts + 1):
        rewrite, gmeta = generate_one(row, attempt, gen_tok, gen_provider)
        rule = check_rules(row["claim"], rewrite, row["span"])
        flu, fmeta = one_word(
            FLUENCY_SYSTEM,
            f"Sentence:\n{rewrite}\nGrammatical and fluent?",
            model=VAL_OR,
            tok=val_tok,
            provider=val_provider,
        )
        mean, mmeta = one_word(
            MEANING_SYSTEM,
            "Original:\n" + row["claim"] + "\n\nRewrite:\n" + rewrite + "\n\nSame meaning, nothing added?",
            model=VAL_OR,
            tok=val_tok,
            provider=val_provider,
        )
        passed = rule is None and flu == "YES" and mean == "YES"
        entry = {
            "attempt": attempt,
            "rewrite": rewrite,
            "rule": rule,
            "fluency": flu,
            "meaning": mean,
            "passed": passed,
            "gen": gmeta,
            "fluency_meta": fmeta,
            "meaning_meta": mmeta,
        }
        attempts_log.append(entry)
        if passed:
            chosen = entry
            break
    if chosen is None:
        chosen = attempts_log[-1]
    return {
        "row": row,
        "chosen": chosen,
        "attempts": attempts_log,
        "passed": chosen.get("passed", False),
    }


def main() -> None:
    todo = pilot_bases(read_jsonl(OUT / "paraphrase_todo.jsonl"))
    need = 20 if PILOT_VERSION == "v2" else 10
    if len(todo) < need:
        raise SystemExit(f"need {need} pilot bases, got {len(todo)}")
    gen_tok = load_tokenizer(GEN_TOK, GEN_REV)
    val_tok = load_tokenizer(VAL_TOK, VAL_REV)
    gen_provider = os.environ.get("MEDVERIF_PARA_GEN_PROVIDER")
    val_provider = os.environ.get("MEDVERIF_PARA_VAL_PROVIDER", "DeepInfra")
    max_attempts = 3 if PILOT_VERSION == "v2" else 1

    n_dose = sum(1 for r in todo if r.get("type") == "DOSE")
    n_pol = sum(1 for r in todo if r.get("type") == "POLARITY")
    results = [
        process_base(row, gen_tok, val_tok, gen_provider, val_provider, max_attempts)
        for row in todo
    ]
    n_pass = sum(1 for r in results if r["passed"])
    pass_rate = n_pass / max(len(results), 1)

    lines = [
        f"# QC samples — INV paraphrase pilot {PILOT_VERSION} (OpenRouter)",
        "",
        "**WAIT for PI OK** before full paraphrase run.",
        "",
        f"- Generator: `{GEN_OR}` (≠ V1 Mistral, ≠ V4 Qwen3-14B)",
        f"- Validator: `{VAL_OR}` (Phi-4)",
        f"- Pilot: **{n_dose} DOSE + {n_pol} POLARITY** (main subset, QC rule B–valid POLARITY only)",
        f"- Pass rate: **{n_pass}/{len(results)}** ({pass_rate:.1%})",
        "",
    ]
    if PILOT_VERSION == "v2":
        lines += [
            "- Bases: `valid=true` main C0; excludes POLARITY with flip rule B block (e.g. P0009, P0017).",
            "- Rules: qualifier-set match, no fronting, Jaccard ≥ 0.5, not pure permutation, then Phi-4.",
            "",
        ]

    for res in results:
        row = res["row"]
        ch = res["chosen"]
        rejections = [
            f"a{ e['attempt']}: rule={e['rule'] or 'ok'} flu={e['fluency']} mean={e['meaning']}"
            for e in res["attempts"]
            if not e["passed"]
        ]
        lines += [
            f"## {row['base_id']} ({row['type']}, {row.get('subset', '?')})",
            "",
            f"**Pass:** {res['passed']} (attempt {ch['attempt']}/{len(res['attempts'])})",
            f"**Rule:** {ch['rule'] or 'ok'} | **Fluency:** {ch['fluency']} | **Meaning:** {ch['meaning']}",
            "",
        ]
        if rejections:
            lines += ["**Rejections:**", *[f"- {r}" for r in rejections], ""]
        lines += [
            "**Original**",
            "```",
            row["claim"],
            "```",
            "",
            "**Rewrite**",
            "```",
            ch["rewrite"],
            "```",
            "",
            f"_Gen:_ `{json.dumps(ch['gen'])}`",
            f"_Val fluency:_ `{json.dumps(ch['fluency_meta'])}`",
            f"_Val meaning:_ `{json.dumps(ch['meaning_meta'])}`",
            "",
        ]

    QC.parent.mkdir(parents=True, exist_ok=True)
    QC.write_text("\n".join(lines) + "\n")
    print(json.dumps({"qc": str(QC), "n": len(todo), "pass_rate": pass_rate, "version": PILOT_VERSION}))


if __name__ == "__main__":
    main()
