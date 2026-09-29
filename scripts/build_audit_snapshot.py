#!/usr/bin/env python3
"""Build release/audit_snapshot.zip for independent recomputation (no secrets)."""

from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_ZIP = ROOT / "release/audit_snapshot.zip"
README = ROOT / "release/AUDIT_SNAPSHOT_README.md"

INSTANCE_FILES = [
    "data/v3/instances_main.jsonl",
    "data/v3/instances_cpu_early.jsonl",
    "data/v3/instances_inv_families.jsonl",
    "data/v3/t17_downdose.jsonl",
    "data/t7/instances_e1_unit.jsonl",
    "data/t14/instances_t14.jsonl",
    "data/t3/instances_inv_families.jsonl",
]

QC_FILES = [
    "qc/e1_pol_review.csv",
    "qc/inv_manual_review.csv",
    "qc/unit_naturalness.csv",
    "qc/dose3_labels.csv",
    "qc/t7_PI_ok_labels.csv",
    "qc/t14_PI_ok_labels.csv",
]

EXCLUSION_FILES = [
    "notes/allow_data_shrink.json",
    "notes/openrouter_verifiers.json",
    "src/non_dose_targets.py",
    "scripts/compute_paper_numbers.py",
]

SCORE_GLOBS = [
    "results/raw/v2a_minicheck.jsonl",
    "results/raw/v3_alignscore.jsonl",
    "results/raw/v1_medscore.jsonl",
    "results/raw/v4_ragas_nli.llama.jsonl",
    "results/raw/v5_ragas_nli.jsonl",
    "results/raw/v1b_medscore.jsonl",
    "results/raw/e2_main/*.jsonl",
    "results/raw/t7/*.jsonl",
    "results/raw/t14/*.jsonl",
    "results/raw/t17/*.jsonl",
    "results/raw/t3/*.jsonl",
    "results/raw/t3_t2/*.jsonl",
    "results/raw/t3_t6b/*.jsonl",
    "results/raw_m1/v1_medscore.jsonl",
    "results/raw_m1/v4_ragas_nli.llama.jsonl",
    "results/raw_m1/v2a_minicheck.jsonl",
    "results/raw_m1/v3_alignscore.jsonl",
]

COLUMN_DOC = {
    "instances_*.jsonl": "instance_id, base_id, type, condition, magnitude, claim, evidence, valid, invalid_reason, subset, …",
    "qc/*.csv": "Human labels: PI_ok, natural, dose audit fields (per file header row).",
    "results/raw/**/*.jsonl": "instance_id, verdict, score, verifier, api_model, api_provider (OpenRouter rows), latency_s, …",
    "scripts/compute_paper_numbers.py": "Canonical metric definitions and score denylist.",
}


def _collect_score_paths() -> list[Path]:
    out: list[Path] = []
    for pat in SCORE_GLOBS:
        if "*" in pat:
            out.extend(sorted(ROOT.glob(pat)))
        else:
            p = ROOT / pat
            if p.is_file():
                out.append(p)
    # dedupe; skip denylisted v4 plain
    seen: set[str] = set()
    final: list[Path] = []
    for p in out:
        if p.name == "v4_ragas_nli.jsonl":
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel not in seen:
            seen.add(rel)
            final.append(p)
    return final


def write_readme(score_paths: list[Path]) -> None:
    lines = [
        "# Audit snapshot",
        "",
        f"Built: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Recompute paper numbers:",
        "",
        "```bash",
        "python scripts/compute_paper_numbers.py",
        "```",
        "",
        "## Instance packs",
        "",
    ]
    for rel in INSTANCE_FILES:
        lines.append(f"- `{rel}` — columns: {COLUMN_DOC['instances_*.jsonl']}")
    lines += ["", "## QC / exclusions", ""]
    for rel in QC_FILES + EXCLUSION_FILES:
        lines.append(f"- `{rel}`")
    lines += ["", "## Score files included", ""]
    for p in score_paths:
        lines.append(f"- `{p.relative_to(ROOT).as_posix()}`")
    lines += [
        "",
        "## Excluded by policy",
        "",
        "- `results/raw/**/v4_ragas_nli.jsonl` (non-Llama / Qwen local)",
        "- `**/_quarantine/**`, `*.legacy.jsonl`, secrets, `.env`",
        "",
    ]
    README.parent.mkdir(parents=True, exist_ok=True)
    README.write_text("\n".join(lines) + "\n")


def main() -> None:
    score_paths = _collect_score_paths()
    write_readme(score_paths)
    OUT_ZIP.parent.mkdir(parents=True, exist_ok=True)
    manifest = {"files": [], "built_at": datetime.now(timezone.utc).isoformat()}
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in INSTANCE_FILES + QC_FILES + EXCLUSION_FILES:
            path = ROOT / rel
            if path.is_file():
                arc = rel
                zf.write(path, arcname=arc)
                manifest["files"].append(arc)
        for path in score_paths:
            arc = path.relative_to(ROOT).as_posix()
            zf.write(path, arcname=arc)
            manifest["files"].append(arc)
        zf.writestr("release/AUDIT_SNAPSHOT_README.md", README.read_text())
        manifest["files"].append("release/AUDIT_SNAPSHOT_README.md")
        zf.writestr("release/manifest.json", json.dumps(manifest, indent=2) + "\n")
    size_mb = OUT_ZIP.stat().st_size / (1024 * 1024)
    print(json.dumps({"zip": str(OUT_ZIP), "size_bytes": OUT_ZIP.stat().st_size, "size_mb": round(size_mb, 2)}))


if __name__ == "__main__":
    main()
