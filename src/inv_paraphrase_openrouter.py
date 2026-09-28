"""G — INV paraphrase pilot via OpenRouter (generator ≠ validator ≠ V1/V4)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from generate_v3 import FLUENCY_SYSTEM, HINTS, MEANING_SYSTEM, OUT, PARA_SYSTEM, read_jsonl, rule_failure
from llm_client import chat
from openrouter_runtime import load_tokenizer
from stage12_llm import render

ROOT = Path("/data2/hpcshared/medverif-audit")
QC = ROOT / "qc" / "qc_samples_inv_v3.md"

GEN_OR = os.environ.get("MEDVERIF_PARA_GEN_MODEL", "qwen/qwen-2.5-72b-instruct")
VAL_OR = os.environ.get("MEDVERIF_PARA_VAL_MODEL", "microsoft/phi-4")
GEN_TOK = os.environ.get("MEDVERIF_PARA_GEN_TOKENIZER", "Qwen/Qwen2.5-72B-Instruct")
GEN_REV = os.environ.get("MEDVERIF_PARA_GEN_REV") or None
VAL_TOK = os.environ.get("MEDVERIF_PARA_VAL_TOKENIZER", "microsoft/phi-4")
VAL_REV = os.environ.get("MEDVERIF_PARA_VAL_REV", "2db69c1c3e91a05d2c64a3185acfbaf36f744e25")


def pilot_bases(todo: list[dict]) -> list[dict]:
    dose = [r for r in todo if r.get("type") == "DOSE"]
    pol = [r for r in todo if r.get("type") == "POLARITY"]
    return dose[:5] + pol[:5]


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


def generate_one(row: dict, attempt: int, gen_tok, gen_provider: str | None) -> tuple[str, dict]:
    user = (
        f"Target span (copy verbatim, once): {row['span']}\n"
        f"Original sentence:\n{row['claim']}\n"
        f"Instruction: {HINTS[attempt - 1]}"
    )
    prompt = render(gen_tok, PARA_SYSTEM, user)
    resp = chat(
        model=GEN_OR,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=160,
        provider=gen_provider,
        allow_fallbacks=False,
    )
    rewrite = (resp.text or "").strip().split("\n")[0].strip().strip('"')
    return rewrite, {
        "provider": resp.provider,
        "request_id": resp.request_id,
        "model": resp.model,
        "generator": GEN_OR,
    }


def main() -> None:
    todo = pilot_bases(read_jsonl(OUT / "paraphrase_todo.jsonl"))
    if len(todo) < 10:
        raise SystemExit(f"need 10 pilot bases, got {len(todo)}")
    gen_tok = load_tokenizer(GEN_TOK, GEN_REV)
    val_tok = load_tokenizer(VAL_TOK, VAL_REV)
    gen_provider = os.environ.get("MEDVERIF_PARA_GEN_PROVIDER")
    val_provider = os.environ.get("MEDVERIF_PARA_VAL_PROVIDER", "DeepInfra")

    lines = [
        "# QC samples — INV paraphrase pilot (OpenRouter)",
        "",
        "**WAIT for PI OK** before full paraphrase run.",
        "",
        f"- Generator: `{GEN_OR}` (≠ V1 Mistral, ≠ V4 Qwen3-14B)",
        f"- Validator: `{VAL_OR}` (Phi-4)",
        f"- Pilot: **5 DOSE + 5 POLARITY** bases",
        "",
    ]

    for row in todo:
        rewrite, gmeta = generate_one(row, 1, gen_tok, gen_provider)
        rule = rule_failure(row["claim"], rewrite, row["span"])
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
        lines += [
            f"## {row['base_id']} ({row['type']}, {row.get('subset', '?')})",
            "",
            f"**Rule:** {rule or 'ok'} | **Fluency:** {flu} | **Meaning:** {mean} | **Pass:** {passed}",
            "",
            "**Original**",
            "```",
            row["claim"],
            "```",
            "",
            "**Rewrite**",
            "```",
            rewrite,
            "```",
            "",
            f"_Gen:_ `{json.dumps(gmeta)}`",
            f"_Val fluency:_ `{json.dumps(fmeta)}`",
            f"_Val meaning:_ `{json.dumps(mmeta)}`",
            "",
        ]

    QC.parent.mkdir(parents=True, exist_ok=True)
    QC.write_text("\n".join(lines) + "\n")
    print(json.dumps({"qc": str(QC), "n": len(todo)}))


if __name__ == "__main__":
    main()
