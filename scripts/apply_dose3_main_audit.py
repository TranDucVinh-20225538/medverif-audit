#!/usr/bin/env python3
"""Apply qc/dose3_labels.csv: non-dose drops, E1 PI invalidations, c0_underspecified tags."""

from __future__ import annotations

import csv
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dose_weak_contrast import flag_weak_e1_contrast  # noqa: E402
from non_dose_targets import invalidate_non_dose_row  # noqa: E402

V3 = ROOT / "data/v3"
AUDIT = V3 / "instances_audit.jsonl"
LABELS = ROOT / "qc/dose3_labels.csv"
ATTACH = Path(
    "/data2/cmdir/home/toandq/.cursor/projects/data2-hpcshared-Vinh/attachments/"
    "c8490c3c-8029-48bf-90f8-080969f892d1/dose3_labels.csv"
)
MANIFEST = ROOT / "notes/dose3_main_audit_apply.json"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")


def load_labels() -> list[dict]:
    src = ATTACH if ATTACH.is_file() else LABELS
    if not src.is_file():
        raise SystemExit(f"missing {LABELS}")
    shutil.copy2(src, LABELS)
    return list(csv.DictReader(LABELS.open(encoding="utf-8-sig")))


def e1_instance_ids(base_id: str, mag: str) -> list[str]:
    return [
        f"{base_id}__E1-claim__{mag}",
        f"{base_id}__E1-evid__{mag}",
    ]


def refresh_outputs(audit: list[dict]) -> None:
    main_rows = [r for r in audit if r.get("valid") and r.get("subset") == "main"]
    thr_rows = [r for r in audit if r.get("valid") and r.get("subset") == "threshold"]
    range_rows = [r for r in audit if r.get("valid") and r.get("subset") == "range"]
    write_jsonl(V3 / "instances_main.jsonl", main_rows)
    write_jsonl(V3 / "instances_threshold.jsonl", thr_rows)
    write_jsonl(V3 / "instances_range.jsonl", range_rows)
    cpu_early = [r for r in main_rows + thr_rows if r.get("magnitude") != "paraphrase"]
    write_jsonl(V3 / "instances_cpu_early.jsonl", cpu_early)
    write_jsonl(V3 / "instances_cpu_main.jsonl", [r for r in main_rows if r.get("magnitude") != "paraphrase"])


def main() -> None:
    labels = load_labels()
    by_base = {r["base_id"]: r for r in labels}
    non_dose = {bid for bid, r in by_base.items() if (r.get("C0_ok") or "").strip().upper() == "LOẠI"}
    underspec = {
        bid
        for bid, r in by_base.items()
        if (r.get("C0_ok") or "").strip().upper() == "N"
    }
    e1_invalid: set[str] = set()
    for bid, r in by_base.items():
        if (r.get("E1x2_ok") or "").strip().upper() == "N":
            e1_invalid.update(e1_instance_ids(bid, "x2"))
        if (r.get("E1x10_ok") or "").strip().upper() == "N":
            e1_invalid.update(e1_instance_ids(bid, "x10"))

    audit = read_jsonl(AUDIT)
    stats = Counter()
    flagged_bases: set[str] = set()
    out = []
    for row in audit:
        r = dict(row)
        bid = r.get("base_id") or ""
        invalidate_non_dose_row(r)
        if bid in non_dose:
            r["valid"] = False
            r["invalid_reason"] = "non_dose_target"
            stats["non_dose_instances"] += 1
        if bid in underspec:
            r["c0_underspecified"] = True
            stats["c0_underspecified_instances"] += 1
        iid = r.get("instance_id") or ""
        if iid in e1_invalid:
            r["valid"] = False
            r["invalid_reason"] = r.get("invalid_reason") or "dose3_e1_pi_n"
            stats["e1_pi_invalidated"] += 1
        if r.get("type") == "DOSE" and r.get("subset") == "main" and r.get("valid", True):
            r = flag_weak_e1_contrast(r)
            if r.get("weak_e1_contrast"):
                flagged_bases.add(bid)
                stats["weak_e1_contrast_instances"] += 1
        out.append(r)

    write_jsonl(AUDIT, out)
    refresh_outputs(out)

    dose_main_bases = {
        r["base_id"]
        for r in out
        if r.get("type") == "DOSE"
        and r.get("subset") == "main"
        and r.get("condition") == "C0"
        and r.get("valid", True)
    }
    manifest = {
        "labels_file": str(LABELS.relative_to(ROOT)),
        "sample_bases": len(labels),
        "non_dose_bases": sorted(non_dose),
        "c0_underspecified_bases": sorted(underspec),
        "e1_invalid_instance_ids": sorted(e1_invalid),
        "weak_e1_contrast_main_bases": sorted(flagged_bases),
        "n_weak_e1_contrast_main_bases": len(flagged_bases),
        "n_dose_main_c0_valid_bases": len(dose_main_bases),
        "counts": dict(stats),
        "e1_validity_on_sample": {
            "denominator_excl_non_dose": len(labels) - len(non_dose),
            "x2_ok": sum(1 for r in labels if r["base_id"] not in non_dose and (r.get("E1x2_ok") or "").upper() == "Y"),
            "x10_ok": sum(1 for r in labels if r["base_id"] not in non_dose and (r.get("E1x10_ok") or "").upper() == "Y"),
            "c0_ok": sum(1 for r in labels if r["base_id"] not in non_dose and (r.get("C0_ok") or "").upper() == "Y"),
        },
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
