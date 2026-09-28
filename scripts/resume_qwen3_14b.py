"""Resume Qwen3-14B shards 5–7 (xet off), then safetensors header check."""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import huggingface_hub.file_download as hf_file_download

hf_file_download.is_xet_available = lambda: False

from huggingface_hub import snapshot_download

ROOT = Path("/data2/hpcshared/medverif-audit")
HUB = ROOT / ".cache" / "huggingface" / "hub"
REPO = "Qwen/Qwen3-14B"
REVISION = "40c069824f4251a91eefaf281ebe4c544efd3e18"
MISSING = [
    "model-00005-of-00008.safetensors",
    "model-00006-of-00008.safetensors",
    "model-00007-of-00008.safetensors",
]
ALLOW = [
    "model.safetensors.index.json",
    "config.json",
    "generation_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "merges.txt",
    "vocab.json",
    *MISSING,
]


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
    folder = HUB / "models--Qwen--Qwen3-14B"
    for blob in folder.glob("**/*.incomplete"):
        print(f"remove incomplete {blob}", flush=True)
        blob.unlink(missing_ok=True)

    print(f"download allow_patterns n={len(ALLOW)}", flush=True)
    snapshot_download(
        repo_id=REPO,
        revision=REVISION,
        cache_dir=str(HUB),
        allow_patterns=ALLOW,
        max_workers=4,
    )

    snap = HUB / "models--Qwen--Qwen3-14B" / "snapshots" / REVISION
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
    out = ROOT / "notes" / "qwen3_14b_shard_headers.json"
    payload = {"revision": REVISION, "n_shards": len(shards), "bad": bad, "shards": report}
    out.write_text(json.dumps(payload, indent=2) + "\n")
    status = ROOT / "notes" / "qwen3_14b_download.json"
    status.write_text(
        json.dumps(
            {
                "repo": REPO,
                "revision": REVISION,
                "ready": bad == 0,
                "missing_shards": [r["shard"] for r in report if not r["ok"]],
                "incomplete_blobs": len(list(folder.glob("**/*.incomplete"))),
                "header_check": str(out),
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps({"bad": bad, "n": len(shards), "out": str(out)}))
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
