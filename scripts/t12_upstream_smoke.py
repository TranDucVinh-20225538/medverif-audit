#!/usr/bin/env python3
"""Smoke 5 T12 instances per upstream framework (or record failure)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

DATA = ROOT / "data/t12/instances_pilot.jsonl"
OUT = ROOT / "notes/t12_upstream_smoke.json"
N = 5


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def smoke_ragas(rows: list[dict], model: str) -> dict:
    from datasets import Dataset
    from langchain_openai import ChatOpenAI
    from ragas import evaluate
    from ragas.metrics import faithfulness

    llm = ChatOpenAI(model=model, temperature=0)
    sample = rows[:N]
    ds = Dataset.from_dict(
        {
            "question": [""] * len(sample),
            "answer": [r["claim"] for r in sample],
            "contexts": [[r["evidence"]] for r in sample],
        }
    )
    result = evaluate(ds, metrics=[faithfulness], llm=llm)
    return {"framework": "ragas", "pipeline": "upstream_default", "model": model, "result": str(result)}


def smoke_deepeval(rows: list[dict], model: str) -> dict:
    from deepeval.metrics import FaithfulnessMetric
    from deepeval.test_case import LLMTestCase

    metric = FaithfulnessMetric(threshold=0.5, model=model)
    scores = []
    for r in rows[:N]:
        tc = LLMTestCase(
            input="",
            actual_output=r["claim"],
            retrieval_context=[r["evidence"]],
        )
        metric.measure(tc)
        scores.append(metric.score)
    return {"framework": "deepeval", "pipeline": "upstream_default", "model": model, "scores": scores}


def smoke_trulens(rows: list[dict], model: str) -> dict:
    from trulens.feedback import Groundedness
    from trulens.providers.openai import OpenAI

    provider = OpenAI(model_engine=model)
    grounded = Groundedness(groundedness_provider=provider)
    out = []
    for r in rows[:N]:
        s = grounded.groundedness_measure_with_llm(r["claim"], r["evidence"])
        out.append(float(s) if s is not None else None)
    return {"framework": "trulens", "pipeline": "upstream_default", "model": model, "scores": out}


def main() -> None:
    from t12_openrouter_env import apply_openrouter_openai_env, log_package_versions

    apply_openrouter_openai_env()
    versions = log_package_versions()
    rows = read_jsonl(DATA)[:N]
    reg = json.loads((ROOT / "notes/openrouter_verifiers.json").read_text())["verifiers"]
    tests = [
        ("ragas", smoke_ragas, reg["t12_ragas_faithfulness"]["openrouter_model"]),
        ("deepeval", smoke_deepeval, reg["t12_deepeval_faithfulness"]["openrouter_model"]),
        ("trulens", smoke_trulens, reg["t12_trulens_groundedness"]["openrouter_model"]),
    ]
    report = {"package_versions": versions, "smokes": []}
    for name, fn, model in tests:
        try:
            report["smokes"].append(fn(rows, model))
        except Exception as exc:
            report["smokes"].append(
                {"framework": name, "pipeline": f"{name}-style prompt fallback needed", "error": str(exc)}
            )
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
