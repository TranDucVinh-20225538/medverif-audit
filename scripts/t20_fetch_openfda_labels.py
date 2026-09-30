#!/usr/bin/env python3
"""T20 step 2: cache openFDA label JSON for drugs in data/t20/drug_list.jsonl."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRUG_LIST = ROOT / "data/t20/drug_list.jsonl"
LABEL_DIR = ROOT / "data/t20/labels"
MANIFEST = ROOT / "notes/t20_openfda_fetch.json"
API = "https://api.fda.gov/drug/label.json"


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return s[:80] or "unknown"


def fetch_drug(drug: str) -> tuple[dict | None, str | None]:
    q = urllib.parse.urlencode(
        {
            "search": f'openfda.generic_name:"{drug}" OR openfda.brand_name:"{drug}"',
            "limit": 1,
        }
    )
    url = f"{API}?{q}"
    req = urllib.request.Request(url, headers={"User-Agent": "medverif-audit-t20/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None, "not_found"
        return None, f"http_{exc.code}"
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)[:120]
    results = payload.get("results") or []
    if not results:
        return None, "empty"
    return results[0], None


def main() -> None:
    if not DRUG_LIST.is_file():
        raise SystemExit(f"missing {DRUG_LIST} — run t20_build_drug_list.py first")
    LABEL_DIR.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(line) for line in DRUG_LIST.open() if line.strip()]
    stats = {"requested": len(rows), "hits": 0, "misses": []}
    for row in rows:
        drug = row["drug"]
        path = LABEL_DIR / f"{slug(drug)}.json"
        if path.is_file() and path.stat().st_size > 50:
            stats["hits"] += 1
            continue
        doc, err = fetch_drug(drug)
        if doc:
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
            stats["hits"] += 1
        else:
            stats["misses"].append({"drug": drug, "error": err})
        time.sleep(0.25)
    MANIFEST.write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
