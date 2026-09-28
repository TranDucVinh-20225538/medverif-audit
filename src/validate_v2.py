"""Phi-4 labels for paraphrase INV and unclear dose_kind. One GPU."""

from __future__ import annotations

import json
from pathlib import Path

from stage12_llm import INV_SYSTEM, first_word, inv_user, load_llm, render, unload, yes_no

ROOT = Path("/data2/hpcshared/medverif-audit")
OUT = ROOT / "data" / "v2"
VAL_MODEL = "microsoft/phi-4"
VAL_REV = "2db69c1c3e91a05d2c64a3185acfbaf36f744e25"
KIND_SYSTEM = (
    "You label a dose statement. Reply with one word: prescriptive or descriptive. "
    "prescriptive means an administration or recommendation. "
    "descriptive means a study report, dietary intake, or nutrition target."
)


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> None:
    pending = read_jsonl(OUT / "paraphrase_pending.jsonl")
    kinds = read_jsonl(OUT / "dose_kind_pending.jsonl")
    llm = load_llm(VAL_MODEL, VAL_REV)
    tokenizer = llm.get_tokenizer()
    users = []
    keys = []
    for row in pending:
        for cand in row["candidates"][:3]:
            users.append(inv_user(row["original"], cand["text"], row["span"], row["span"]))
            keys.append((row["base_id"], cand))
    judged = yes_no(llm, tokenizer, INV_SYSTEM, users, 16) if users else []
    labels = []
    for (base_id, cand), rec in zip(keys, judged):
        labels.append({
            "base_id": base_id,
            "template": cand["template"],
            "text": cand["text"],
            "label": rec["label"],
            "raw_output": rec["raw_output"],
        })
    (OUT / "paraphrase_labels.jsonl").write_text("".join(json.dumps(row) + "\n" for row in labels))
    kind_rows = []
    if kinds:
        from vllm import SamplingParams
        prompts = [
            render(tokenizer, KIND_SYSTEM, "Statement:\n" + row["text"] + "\nLabel:")
            for row in kinds
        ]
        params = SamplingParams(temperature=0.0, max_tokens=8, seed=42)
        outputs = llm.generate(prompts, params)
        for row, out in zip(kinds, outputs):
            word = first_word(out.outputs[0].text).lower()
            kind = word if word in {"prescriptive", "descriptive"} else "unclear"
            kind_rows.append({
                "base_id": row["base_id"],
                "dose_kind": kind,
                "raw_output": out.outputs[0].text,
            })
        (OUT / "dose_kind_labels.jsonl").write_text("".join(json.dumps(row) + "\n" for row in kind_rows))
    unload(llm)
    print(json.dumps({
        "paraphrase_judged": len(labels),
        "paraphrase_yes": sum(row["label"] == "YES" for row in labels),
        "dose_kind": len(kind_rows),
    }))


if __name__ == "__main__":
    main()
