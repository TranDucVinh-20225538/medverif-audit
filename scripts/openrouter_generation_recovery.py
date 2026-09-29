#!/usr/bin/env python3
"""Sample legacy V4 rows: OpenRouter GET /api/v1/generation?id=… for model recovery."""

from __future__ import annotations

import json
import os
import random
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "notes/v4_llama_rescore_packs.json"
OUT = ROOT / "notes/v4_generation_model_recovery.json"
SAMPLE_N = 50
SEED = 42


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()] if path.is_file() else []


def fetch_generation(gen_id: str, api_key: str) -> dict:
    url = f"https://openrouter.ai/api/v1/generation?id={gen_id}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def main() -> None:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        OUT.write_text(json.dumps({"error": "OPENROUTER_API_KEY not set"}, indent=2) + "\n")
        print(OUT)
        return
    data = json.loads(MANIFEST.read_text())
    pool: list[tuple[str, dict]] = []
    for pack in data["packs"]:
        legacy = ROOT / pack["score_dir"] / "v4_ragas_nli.legacy.jsonl"
        for row in read_jsonl(legacy):
            gid = row.get("api_request_id") or row.get("generation_id") or row.get("id")
            if gid:
                pool.append((pack["id"], row))
    random.seed(SEED)
    sample = random.sample(pool, min(SAMPLE_N, len(pool)))
    results = []
    models: Counter = Counter()
    for pack_id, row in sample:
        gid = row.get("api_request_id") or row.get("generation_id") or row.get("id")
        rec = {"pack": pack_id, "instance_id": row["instance_id"], "generation_id": gid}
        try:
            payload = fetch_generation(str(gid), api_key)
            data_block = payload.get("data") or payload
            model = data_block.get("model") or data_block.get("native_model")
            rec["model"] = model
            rec["provider"] = data_block.get("provider")
            if model:
                models[model] += 1
        except urllib.error.HTTPError as exc:
            rec["error"] = f"HTTP {exc.code}"
        except Exception as exc:  # noqa: BLE001
            rec["error"] = str(exc)
        results.append(rec)
    OUT.write_text(
        json.dumps(
            {"sample_n": len(sample), "pool_with_ids": len(pool), "model_counts": dict(models), "rows": results},
            indent=2,
        )
        + "\n"
    )
    print(OUT)


if __name__ == "__main__":
    main()
