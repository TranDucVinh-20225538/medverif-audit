"""Safetensors header check for V1 Mistral shards (read 8 bytes only)."""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

ROOT = Path("/data2/hpcshared/medverif-audit")
HUB = ROOT / ".cache" / "huggingface" / "hub"
REVISION = "9527884be6e5616bdd54de542f9ae13384489724"


def header_ok(path: Path) -> tuple[bool, str]:
    with path.open("rb") as handle:
        raw = handle.read(8)
    if len(raw) != 8:
        return False, "short_read"
    n = struct.unpack("<Q", raw)[0]
    if not (8 < n < 50_000_000):
        return False, f"bad_n={n}"
    if n + 8 > path.stat().st_size:
        return False, "header_longer_than_file"
    return True, "ok"


def main() -> None:
    snap = HUB / "models--mistralai--Mistral-Small-24B-Instruct-2501" / "snapshots" / REVISION
    index_path = snap / "model.safetensors.index.json"
    if not index_path.is_file():
        raise SystemExit(f"missing index {index_path}")
    index = json.loads(index_path.read_text())
    shards = sorted(set(index["weight_map"].values()))
    report = []
    bad = 0
    for name in shards:
        path = snap / name
        if not path.is_file():
            report.append({"shard": name, "ok": False, "reason": "missing"})
            bad += 1
            continue
        ok, reason = header_ok(path)
        report.append({"shard": name, "ok": ok, "reason": reason, "bytes": path.stat().st_size})
        if not ok:
            bad += 1
    out = ROOT / "notes" / "v1_shard_headers.json"
    out.write_text(json.dumps({"revision": REVISION, "n_shards": len(shards), "bad": bad, "shards": report}, indent=2) + "\n")
    print(json.dumps({"bad": bad, "n": len(shards), "out": str(out)}))
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
