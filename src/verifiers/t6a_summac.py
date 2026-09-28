"""T6-A SummaC-ZS and SummaC-Conv."""

from __future__ import annotations

import time

from verifiers.preprocess import verifier_inputs


def load(verifier_id: str):
    from summac.model_summac import SummaCConv, SummaCZS

    started = time.perf_counter()
    if verifier_id == "t6a_summac_zs":
        model = SummaCZS(granularity="sentence", model_name="vitc", device="cpu")
    else:
        model = SummaCConv(
            models=["vitc"], bins="percentile", granularity="sentence", device="cpu"
        )
    return model, time.perf_counter() - started


def score_batch(model, rows: list[dict], verifier_id: str) -> list[dict]:
    started = time.perf_counter()
    out = []
    for row in rows:
        claim, evidence = verifier_inputs(row)
        result = model.score([evidence], [claim])
        score_obj = result["scores"][0]
        value = float(score_obj)
        out.append(
            {
                "instance_id": row["instance_id"],
                "raw_output": str(value),
                "score": value,
                "verdict": "PASS" if value > 0.5 else "FAIL",
                "latency_s": None,
                "verifier": verifier_id,
            }
        )
    per = (time.perf_counter() - started) / max(len(rows), 1)
    for row in out:
        row["latency_s"] = per
    return out
