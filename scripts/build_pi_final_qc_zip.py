#!/usr/bin/env python3
"""Zip FINAL PI review CSVs only (generation-complete packs)."""

from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "release/pi_final_review_packs.zip"
MANIFEST = ROOT / "qc/REVIEW_PACKS_FINAL.manifest"

# Marked FINAL 2026-09-30 — instance generation complete; PI review pending return.
FINAL_CSVS = [
    ("qc/main_ext_review.csv", "main_ext whitelist INV (60 rows)"),
    ("qc/t18_sample.csv", "T18 Wikipedia pack QC sample"),
    ("qc/t17_sample.csv", "T17 downdose QC sample"),
]


def main() -> None:
    lines = [
        "# FINAL review packs (2026-09-30)",
        "",
        "Generation complete for these cohorts. Return labeled CSV to unfreeze scoring.",
        "",
    ]
    manifest_files: list[str] = []
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel, desc in FINAL_CSVS:
            path = ROOT / rel
            lines.append(f"- **{rel}** — {desc}")
            if not path.is_file():
                lines.append(f"  - MISSING on disk")
                continue
            zf.write(path, arcname=rel)
            manifest_files.append(rel)
            n = sum(1 for _ in path.open() if _.strip()) - 1
            lines.append(f"  - rows (excl header): {n}")
        readme = "\n".join(lines) + "\n"
        zf.writestr("README_FINAL.txt", readme)
        manifest_files.append("README_FINAL.txt")
    MANIFEST.write_text(readme)
    print(
        json.dumps(
            {
                "zip": str(OUT),
                "files": manifest_files,
                "built_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
