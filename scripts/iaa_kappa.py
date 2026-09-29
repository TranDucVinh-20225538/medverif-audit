#!/usr/bin/env python3
"""IAA agreement: q1 vs expected verdict; q2 vs author nat3/PI_ok labels."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "qc/iaa_sample.csv"
KEY = ROOT / "qc/iaa_key_DO_NOT_SHARE.csv"
OUT = ROOT / "notes/iaa_kappa.json"


def norm_yn(raw: str) -> str | None:
    v = (raw or "").strip().upper()
    if v in ("Y", "YES", "TRUE", "1"):
        return "Y"
    if v in ("N", "NO", "FALSE", "0"):
        return "N"
    return None


def kappa_binary(a: list[str], b: list[str]) -> float | None:
    pairs = [(x, y) for x, y in zip(a, b) if x in ("Y", "N") and y in ("Y", "N")]
    if len(pairs) < 2:
        return None
    n = len(pairs)
    agree = sum(int(x == y) for x, y in pairs) / n
    pa = sum(1 for x, _ in pairs if x == "Y") / n
    pb = sum(1 for _, y in pairs if y == "Y") / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    if pe == 1:
        return 1.0
    return (agree - pe) / (1 - pe)


def load_key() -> dict[str, dict]:
    out: dict[str, dict] = {}
    with KEY.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            out[row["blind_id"]] = row
    return out


def score_block(
    rows: list[tuple[str, str, str | None, str | None]],
) -> dict:
    """rows: (blind_id, rater, ref, stratum)"""
    rater = [r for _, r, ref, _ in rows if r and ref]
    ref = [ref for _, r, ref, _ in rows if r and ref]
    return {
        "n_pairs": len(rater),
        "kappa": kappa_binary(rater, ref),
        "pct_agree": (sum(int(a == b) for a, b in zip(rater, ref)) / len(rater)) if rater else None,
    }


def main() -> None:
    key = load_key()
    q1_rows: list[tuple[str, str, str | None, str]] = []
    q2_rows: list[tuple[str, str, str | None, str]] = []
    with CSV.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            bid = row["blind_id"]
            meta = key.get(bid, {})
            st = meta.get("stratum") or "unknown"
            q1 = norm_yn(row.get("q1_supported") or "")
            q2 = norm_yn(row.get("q2_natural") or "")
            ref1 = norm_yn(meta.get("expected_q1") or "")
            if not ref1:
                ev = (meta.get("expected_verdict") or "").upper()
                ref1 = "Y" if ev == "PASS" else "N" if ev == "FAIL" else None
            ref2 = norm_yn(meta.get("author_q2") or "")
            if q1 and ref1:
                q1_rows.append((bid, q1, ref1, st))
            if q2 and ref2:
                q2_rows.append((bid, q2, ref2, st))

    by_stratum_q1: dict[str, list] = defaultdict(list)
    by_stratum_q2: dict[str, list] = defaultdict(list)
    for t in q1_rows:
        by_stratum_q1[t[3]].append(t)
    for t in q2_rows:
        by_stratum_q2[t[3]].append(t)

    stat = {
        "n_csv_rows": sum(1 for _ in open(CSV)) - 1,
        "q1_vs_expected_verdict": {
            "overall": score_block(q1_rows),
            "by_stratum": {s: score_block(v) for s, v in sorted(by_stratum_q1.items())},
        },
        "q2_vs_author_labels": {
            "overall": score_block(q2_rows),
            "by_stratum": {s: score_block(v) for s, v in sorted(by_stratum_q2.items())},
            "note": "Author refs: nat3 (unit INV), inv PI_ok, flip PI_ok, dose3 C0/E1 ok",
        },
        "filled_q1": len(q1_rows),
        "filled_q2_with_author_ref": len(q2_rows),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(stat, indent=2) + "\n")
    print(json.dumps(stat, indent=2))


if __name__ == "__main__":
    main()
