#!/usr/bin/env python3
"""T12 pilot/full framework eval → QVC cards (RAGAS / DeepEval / TruLens)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

OUT = ROOT / "notes/t12_qvc_cards.json"
RAW = ROOT / "results/raw/t12"
DATA = ROOT / "data/t12"
BUDGET_USD = 12.0
FRAMEWORKS = (
    "t12_ragas_faithfulness",
    "t12_deepeval_faithfulness",
    "t12_trulens_groundedness",
)


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def sum_cost(path: Path) -> float:
    total = 0.0
    for row in read_jsonl(path):
        c = row.get("api_cost_usd")
        if c is not None:
            total += float(c)
    return total


def build_instances(mode: str) -> Path:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/t12_build_instances.py"), "--mode", mode],
        cwd=ROOT,
        check=True,
    )
    return DATA / f"instances_{mode}.jsonl"


def score_framework(verifier: str, instances: Path, out: Path) -> None:
    env = {
        **os.environ,
        "PYTHONPATH": str(ROOT / "src"),
        "MEDVERIF_USE_OPENROUTER": "1",
        "MEDVERIF_OR_MIN_CREDIT": "2",
    }
    subprocess.run([sys.executable, str(ROOT / "scripts/openrouter_budget.py")], cwd=ROOT, env=env, check=False)
    cmd = [
        sys.executable,
        str(ROOT / "src/score_jsonl.py"),
        "--verifier",
        verifier,
        "--instances",
        str(instances),
        "--out",
        str(out),
    ]
    subprocess.run(cmd, cwd=ROOT, env=env, check=False)


def qvc_card(verifier: str, instances: list[dict], scores: dict[str, str]) -> dict:
    from qvc.evaluate.card import evaluate

    items = []
    for row in instances:
        iid = row["instance_id"]
        if iid not in scores:
            continue
        items.append(
            {
                "id": iid,
                "base_id": row["base_id"],
                "condition": row.get("condition") or "",
                "family": row.get("inv_family") or row.get("magnitude") or "",
                "claim": row.get("claim") or "",
                "evidence": row.get("evidence") or "",
            }
        )

    by_id = {it["id"]: scores[it["id"]] for it in items}

    def verifier_fn(claim: str, evidence: str) -> str:
        for it in items:
            if it["claim"] == claim and it["evidence"] == evidence:
                return by_id[it["id"]]
        return "PARSE_FAIL"

    card = evaluate(items, verifier_fn)
    card["json"]["verifier"] = verifier
    card["json"]["n_scored"] = len(by_id)
    return card["json"]


def main() -> None:
    mode = "pilot" if "--pilot" in sys.argv else "full"
    if "--full" in sys.argv:
        mode = "full"
    inst_path = build_instances(mode)
    instances = read_jsonl(inst_path)
    RAW.mkdir(parents=True, exist_ok=True)
    spent = sum(sum_cost(p) for p in RAW.glob("*.jsonl"))
    cards = {"mode": mode, "budget_usd": BUDGET_USD, "spent_usd_est": round(spent, 4), "frameworks": {}}
    for fw in FRAMEWORKS:
        if spent >= BUDGET_USD:
            cards["frameworks"][fw] = {"status": "budget_exhausted", "QI": None, "NS": None, "US": None}
            continue
        out = RAW / f"{fw}.jsonl"
        score_framework(fw, inst_path, out)
        spent = sum(sum_cost(p) for p in RAW.glob("*.jsonl"))
        scores = {r["instance_id"]: r["verdict"] for r in read_jsonl(out) if r.get("verdict") != "PARSE_FAIL"}
        if scores:
            qvc = qvc_card(fw, instances, scores)
            cards["frameworks"][fw] = {
                "status": "ok",
                "n_scored": qvc.get("n_scored"),
                "QI": qvc.get("QI"),
                "NS": qvc.get("NS"),
                "US": qvc.get("US"),
                "QI_ci": qvc.get("QI_ci"),
                "NS_ci": qvc.get("NS_ci"),
                "n_inv": qvc.get("n_inv"),
                "n_e1": qvc.get("n_e1"),
            }
        else:
            cards["frameworks"][fw] = {"status": "no_scores", "QI": None, "NS": None, "US": None}
        cards["spent_usd_est"] = round(spent, 4)
    subprocess.run([sys.executable, str(ROOT / "scripts/openrouter_budget.py")], cwd=ROOT, check=False)
    OUT.write_text(json.dumps(cards, indent=2) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
