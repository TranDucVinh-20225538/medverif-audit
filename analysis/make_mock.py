"""Random verdicts in the Stage 3 schema. Not pilot data. Not written to results/."""

from __future__ import annotations

import json
import random
from pathlib import Path

VERIFIERS = (
    "v1_medscore",
    "v2a_minicheck",
    "v2b_bespoke",
    "v3_alignscore",
    "v4_ragas_nli",
)
SEED = 42


def _evidence(span: str, position: int, length: int, repeats: int) -> str:
    position = min(position, max(length - len(span), 0))
    body = ["x"] * length
    text = "".join(body)
    # Place the first span, then extra copies further right when they fit.
    placed = text[:position] + span + text[position + len(span):]
    if len(placed) > length:
        placed = placed[:length]
    cursor = position + len(span) + 5
    for _ in range(repeats - 1):
        if cursor + len(span) > len(placed):
            break
        placed = placed[:cursor] + span + placed[cursor + len(span):]
        cursor += len(span) + 5
    return placed


def _instances() -> list[dict]:
    rows = []
    specs = []
    for i in range(12):
        specs.append(("DOSE", f"D{i:02d}", 500, "mg", "x2", "x10", "unit_conversion"))
    for i in range(12):
        specs.append(("POLARITY", f"P{i:02d}", None, None, "flip", None, "rephrase"))
    lengths = [120, 280, 550, 900, 1800, 350]
    positions = [0, 40, 120, 250, 600, 20]
    for index, spec in enumerate(specs):
        fact_type, base, number, unit, mag_a, mag_b, inv_mag = spec
        repeats = 2 if fact_type == "DOSE" and index < 3 else 1
        if fact_type == "DOSE":
            span = f"{number} {unit}"
            span_x2 = f"{number * 2} {unit}"
            span_x10 = f"{number * 10} {unit}"
            inv_span = f"{number / 1000:.1f} g" if unit == "mg" else span
        else:
            span = "indicated"
            span_x2 = "contraindicated"
            span_x10 = None
            inv_span = "recommended for"
        length = lengths[index % len(lengths)]
        position = positions[index % len(positions)]
        evidence0 = _evidence(span, position, length, repeats)
        claim0 = f"The note says {span}."
        conditions = [("C0", "none", claim0, evidence0, span, span)]
        if fact_type == "DOSE":
            for mag, new_span in (("x2", span_x2), ("x10", span_x10)):
                evid = evidence0.replace(span, new_span, 1)
                claim = claim0.replace(span, new_span, 1)
                conditions.append(("E1-evid", mag, claim0, evid, span, new_span))
                conditions.append(("E1-claim", mag, claim, evidence0, new_span, span))
                conditions.append(("E2", mag, claim, evid, new_span, new_span))
        else:
            evid = evidence0.replace(span, span_x2, 1)
            claim = claim0.replace(span, span_x2, 1)
            conditions.append(("E1-evid", "flip", claim0, evid, span, span_x2))
            conditions.append(("E1-claim", "flip", claim, evidence0, span_x2, span))
            conditions.append(("E2", "flip", claim, evid, span_x2, span_x2))
        inv_claim = claim0.replace(span, inv_span, 1)
        conditions.append(("INV-claim", inv_mag, inv_claim, evidence0, inv_span, span))
        for condition, magnitude, claim, evidence, claim_span, evidence_span in conditions:
            diff = {"span_before": span, "span_after": evidence_span if condition != "E1-claim" else claim_span}
            if condition in ("E1-evid", "E2"):
                diff = {"evidence": {"span_before": span, "span_after": evidence_span}, "claim_unchanged": condition == "E1-evid"}
            elif condition == "E1-claim":
                diff = {"claim": {"span_before": span, "span_after": claim_span}, "evidence_unchanged": True}
            rows.append({
                "instance_id": f"{base}__{condition}__{magnitude}",
                "base_id": base,
                "type": fact_type,
                "condition": condition,
                "magnitude": magnitude,
                "claim": claim,
                "evidence": evidence,
                "evidence_c0": evidence0,
                "claim_c0": claim0,
                "claim_span": claim_span,
                "evidence_span": evidence_span,
                "expected_verdict": "FAIL" if condition.startswith("E1") else "PASS",
                "diff": diff,
            })
    return rows


def _verdicts(instances: list[dict]) -> dict[str, list[dict]]:
    rng = random.Random(SEED)
    out = {name: [] for name in VERIFIERS}
    for row in instances:
        for name in VERIFIERS:
            roll = rng.random()
            if roll < 0.05:
                verdict, score = "PARSE_FAIL", None
            elif roll < 0.55:
                verdict, score = "PASS", 0.8
            else:
                verdict, score = "FAIL", 0.2
            out[name].append({
                "instance_id": row["instance_id"],
                "raw_output": "MOCK",
                "score": score,
                "verdict": verdict,
                "latency_s": None,
                "verifier": name,
            })
    return out


def main() -> None:
    root = Path("/data2/hpcshared/medverif-audit/tests/mock_verdicts")
    root.mkdir(parents=True, exist_ok=True)
    instances = _instances()
    (root / "instances.jsonl").write_text("".join(json.dumps(row) + "\n" for row in instances))
    for name, rows in _verdicts(instances).items():
        (root / f"{name}.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    print(json.dumps({"instances": len(instances), "verifiers": len(VERIFIERS)}))


if __name__ == "__main__":
    main()
