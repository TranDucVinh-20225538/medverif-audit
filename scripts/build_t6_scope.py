#!/usr/bin/env python3
"""Build deduped T6 evaluation scope (T2 + T3 INV families when present)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from t2_build_instances import (  # noqa: E402
    EXPAND,
    MAIN,
    build_full,
    read_jsonl,
    write_jsonl,
)

OUT = ROOT / "data" / "v3" / "instances_t6_scope.jsonl"
MANIFEST = ROOT / "data" / "v3" / "manifest_t6_scope.json"
T3 = ROOT / "data" / "v3" / "instances_inv_families.jsonl"


def content_sha1(row: dict) -> str:
    claim = row.get("claim") or ""
    evidence = row.get("evidence") or ""
    return hashlib.sha1(f"{claim}\n{evidence}".encode("utf-8")).hexdigest()


def main() -> None:
    rows, meta = build_full(read_jsonl(MAIN), read_jsonl(EXPAND))
    t3 = read_jsonl(T3)
    by_id: dict[str, dict] = {}
    for row in rows + t3:
        if not row.get("valid", True):
            continue
        iid = row["instance_id"]
        enriched = dict(row)
        enriched["content_sha1"] = content_sha1(row)
        by_id[iid] = enriched

    final = sorted(by_id.values(), key=lambda r: r["instance_id"])
    write_jsonl(OUT, final)
    manifest = {
        **meta,
        "path": str(OUT.relative_to(ROOT)),
        "n_instances": len(final),
        "n_t3_inv_families": sum(1 for r in final if str(r.get("magnitude", "")).startswith("inv_")),
        "dedupe_key": "instance_id",
        "content_sha1": "sha1(claim + newline + evidence)",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
