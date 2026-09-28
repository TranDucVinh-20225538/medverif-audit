"""Verify V1 score_batch stores full raw_output (mock LLM, same code path as GPU run)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reparse_v1_study import reparse_file
from v1_parser import study_verdict
from verifiers import v1_medscore


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def mock_llm(texts: list[str]):
    class Out:
        def __init__(self, text: str):
            self.outputs = [SimpleNamespace(text=text)]

    class LLM:
        def generate(self, prompts, params):
            return [Out(t) for t in texts[: len(prompts)]]

    class Tok:
        def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
            return messages[0]["content"]

    return LLM(), Tok(), None, 0.0


def main() -> None:
    smoke = read_jsonl(ROOT / "tests" / "smoke_pairs.jsonl")
    extra = read_jsonl(ROOT / "tests" / "v1_study_smoke.jsonl")
    texts = ["True"] * len(smoke) + [r["raw_output"] for r in extra]
    pairs = smoke + [
        {
            "instance_id": r["instance_id"],
            "claim": "mock",
            "evidence": "mock",
        }
        for r in extra
    ]
    llm, tok, params, _ = mock_llm(texts)
    scored = v1_medscore.score_batch(llm, tok, params, pairs)
    for row, want in zip(scored, texts):
        if row.get("raw_output") != want:
            raise SystemExit(f"missing raw for {row['instance_id']}: {row.get('raw_output')!r}")
        if not isinstance(row["raw_output"], str):
            raise SystemExit("raw_output not str")
    out = ROOT / "tests" / "smoke_results" / "_verify_v1_raw.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as handle:
        for row in scored:
            handle.write(json.dumps(row) + "\n")
    rep = reparse_file(out, in_place=True)
    if rep["n"] != len(scored):
        raise SystemExit("reparse count mismatch")
    neg = [r for r in scored if "not true" in r["raw_output"].lower()]
    if not neg:
        raise SystemExit("no negated case")
    reparsed = read_jsonl(out)
    by_id = {r["instance_id"]: r for r in reparsed}
    for r in extra:
        expect = study_verdict(r["raw_output"])
        if by_id[r["instance_id"]]["study_verdict"] != expect:
            raise SystemExit(f"study {expect} expected for {r['instance_id']}")
    print(json.dumps({"ok": True, "n": len(scored), "reparse_disagree_rate": rep["disagree_rate"]}))


if __name__ == "__main__":
    main()
