#!/usr/bin/env python3
"""Gate Lane B bespoke packs: cal-200 vs node30 t6_bespoke_minicheck (≥97% agreement)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from verifiers.io_utils import read_jsonl  # noqa: E402

CAL = ROOT / "data/lane_b/calibration_200.jsonl"
HPC = ROOT / "results/raw/lane_b/calibration_200/v2b_bespoke.jsonl"
REF = ROOT / "results/raw_node30/t6_bespoke_minicheck.jsonl"
OUT_JSON = ROOT / "notes/lane_b_bespoke_calibration.json"
OUT_MD = ROOT / "notes/lane_b_bespoke_calibration.md"
THRESH = 0.97


def by_id(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    return {r["instance_id"]: r for r in read_jsonl(path)}


def compare(ref: dict[str, dict], hpc: dict[str, dict], ids: set[str]) -> dict:
    n = agree = 0
    diffs: list[float] = []
    bad_precision: list[str] = []
    for iid in ids:
        a, b = ref.get(iid), hpc.get(iid)
        if not b:
            continue
        prec = (b.get("precision") or "").lower()
        quant = b.get("quantized")
        if prec and prec != "bf16":
            bad_precision.append(iid)
        if quant is True:
            bad_precision.append(iid)
        if not a:
            continue
        va, vb = a.get("verdict"), b.get("verdict")
        if va not in ("PASS", "FAIL") or vb not in ("PASS", "FAIL"):
            continue
        n += 1
        agree += int(va == vb)
        sa, sb = a.get("score"), b.get("score")
        if sa is not None and sb is not None:
            diffs.append(abs(float(sa) - float(sb)))
    rate = agree / n if n else None
    return {
        "n": n,
        "agreement": rate,
        "mean_abs_score_diff": (sum(diffs) / len(diffs)) if diffs else None,
        "hpc_rows": len(hpc),
        "bad_precision_rows": sorted(set(bad_precision)),
        "sample_hpc_meta": next(iter(hpc.values()), {}),
    }


def main() -> int:
    cal_ids = {r["instance_id"] for r in read_jsonl(CAL)}
    ref = by_id(REF)
    hpc = by_id(HPC)
    stat = compare(ref, hpc, cal_ids)
    ok_agree = stat["agreement"] is not None and stat["agreement"] >= THRESH
    ok_prec = not stat["bad_precision_rows"] and stat["hpc_rows"] > 0
    sample = stat.get("sample_hpc_meta") or {}
    ok_meta = (sample.get("precision") == "bf16" and sample.get("quantized") is False)
    proceed = ok_agree and ok_prec and ok_meta and stat["n"] >= 50

    doc = {
        "threshold_agreement": THRESH,
        "node30_ref": str(REF.relative_to(ROOT)),
        "hpc_file": str(HPC.relative_to(ROOT)),
        "calibration_ids": len(cal_ids),
        "proceed_lane_b_packs": proceed,
        **stat,
    }
    OUT_JSON.write_text(json.dumps(doc, indent=2) + "\n")
    ag = stat["agreement"]
    ag_s = f"{100 * ag:.1f}%" if ag is not None else "NA"
    lines = [
        "# Bespoke-MiniCheck-7B calibration vs node30",
        "",
        f"- **n (overlap):** {stat['n']}",
        f"- **verdict agreement:** {ag_s}",
        f"- **mean |Δscore|:** {stat['mean_abs_score_diff']:.4f}" if stat["mean_abs_score_diff"] is not None else "- **mean |Δscore|:** NA",
        f"- **HPC rows scored:** {stat['hpc_rows']}",
        f"- **precision (sample row):** {sample.get('precision')} quantized={sample.get('quantized')}",
        f"- **Proceed packs:** {'YES' if proceed else 'NO'}",
        "",
    ]
    if not proceed:
        lines.append("Hold Lane B bespoke packs; use node30 `t6_bespoke_minicheck` for main-card.")
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps(doc, indent=2))
    return 0 if proceed else 1


if __name__ == "__main__":
    raise SystemExit(main())
