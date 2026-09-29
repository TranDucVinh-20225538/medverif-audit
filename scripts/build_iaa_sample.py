#!/usr/bin/env python3
"""IAA: 120 stratified items, blind labels, shuffled presentation order."""

from __future__ import annotations

import csv
import hashlib
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from verifiers.io_utils import read_jsonl  # noqa: E402

MAIN = ROOT / "data/v3/instances_main.jsonl"
OUT = ROOT / "qc/iaa_sample.csv"
KEY = ROOT / "qc/iaa_key_DO_NOT_SHARE.csv"
GUIDE = ROOT / "qc/iaa_guidelines.md"
MANIFEST = ROOT / "notes/iaa_sample_manifest.json"

STRATA = {
    "conversion_naturalness": 30,
    "polarity_flips": 30,
    "rephrases": 20,
    "frequency_route": 25,
    "dose_value": 15,
}

ROUTE_FREQ_RE = re.compile(
    r"\b(?:daily|twice|three times|every \d+|q\d+h|q\d+d|once|weekly|hourly|"
    r"oral|intravenous|intramuscular|subcutaneous|topical|inhaled|route)\b",
    re.I,
)


def stratum(row: dict) -> str | None:
    cond = row.get("condition")
    mag = row.get("magnitude") or ""
    typ = row.get("type")
    if cond == "INV-claim" and mag == "unit_conversion" and typ == "DOSE":
        return "conversion_naturalness"
    if typ == "POLARITY" and cond in ("E1-evid", "E1-claim", "E2") and mag == "flip":
        return "polarity_flips"
    if cond == "INV-claim" and mag in ("rephrase", "paraphrase", "paraphrase_v3"):
        return "rephrases"
    if typ == "DOSE" and cond == "C0" and ROUTE_FREQ_RE.search(row.get("claim") or ""):
        return "frequency_route"
    if typ == "DOSE" and cond in ("E1-evid", "E1-claim") and mag in ("x2", "x10"):
        return "dose_value"
    return None


def blind_id(instance_id: str, idx: int) -> str:
    digest = hashlib.sha256(f"iaa2026:{instance_id}".encode()).hexdigest()[:10]
    return f"IAA{idx:03d}_{digest}"


def main() -> None:
    pool = [
        r
        for r in read_jsonl(MAIN)
        if r.get("valid", True) and r.get("subset") == "main" and stratum(r) is not None
    ]
    by_stratum: dict[str, list[dict]] = {k: [] for k in STRATA}
    for row in pool:
        by_stratum[stratum(row)].append(row)
    rng = random.Random(20260929)
    picked: list[dict] = []
    for name, need in STRATA.items():
        rows = list(by_stratum[name])
        rng.shuffle(rows)
        if len(rows) < need:
            raise RuntimeError(f"IAA stratum {name}: need {need}, have {len(rows)}")
        picked.extend(rows[:need])
    rng.shuffle(picked)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as handle:
        w = csv.writer(handle)
        w.writerow(["blind_id", "claim", "evidence", "reviewer_a", "reviewer_b"])
        key_rows = []
        for i, r in enumerate(picked, start=1):
            bid = blind_id(r["instance_id"], i)
            w.writerow([bid, r.get("claim", ""), r.get("evidence", ""), "", ""])
            key_rows.append(
                {
                    "blind_id": bid,
                    "instance_id": r["instance_id"],
                    "base_id": r["base_id"],
                    "condition": r.get("condition"),
                    "magnitude": r.get("magnitude"),
                    "type": r.get("type"),
                    "stratum": stratum(r),
                    "expected_verdict": r.get("expected_verdict"),
                }
            )
    with KEY.open("w", newline="") as handle:
        kw = csv.DictWriter(
            handle,
            fieldnames=[
                "blind_id",
                "instance_id",
                "base_id",
                "stratum",
                "condition",
                "magnitude",
                "type",
                "expected_verdict",
            ],
        )
        kw.writeheader()
        kw.writerows(key_rows)
    GUIDE.write_text(
        "# IAA guidelines\n\n"
        "Reviewers mark PASS or FAIL in `reviewer_a` / `reviewer_b` for whether the claim "
        "is supported by the evidence.\n\n"
        "The review CSV contains only `blind_id`, claim, and evidence — no condition, stratum, "
        "or expected labels.\n\n"
        "Adjudication metadata lives locally in `qc/iaa_key_DO_NOT_SHARE.csv` (do not share with reviewers).\n\n"
        f"Design strata (n={sum(STRATA.values())}): {json.dumps(STRATA)}\n"
    )
    MANIFEST.write_text(
        json.dumps(
            {
                "n": len(picked),
                "strata": STRATA,
                "csv": str(OUT.relative_to(ROOT)),
                "answer_key_local": str(KEY.relative_to(ROOT)),
                "answer_key_in_git": False,
                "blind": True,
                "shuffled": True,
                "public_csv_columns": ["blind_id", "claim", "evidence", "reviewer_a", "reviewer_b"],
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps({"n": len(picked), "strata": STRATA}, indent=2))


if __name__ == "__main__":
    main()
