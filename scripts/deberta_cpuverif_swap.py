#!/usr/bin/env python3
"""Replace MiniCheck-DeBERTa rows with the cpuverif (reference env) rescores, in place.

Originals are kept as `<name>.pre_cpuverif.quarantined.jsonl` (ignored by score loaders).
Row order and count are unchanged; rows without a cpuverif rescore are left as they are.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGREE = ROOT / "notes/minicheck_cpuverif_agreement.json"
MERGED = ROOT / "results/raw/minicheck_cpuverif"
CID = "t6a_minicheck_deberta"
OUT = ROOT / "notes/deberta_cpuverif_swap.json"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def main() -> None:
    files = json.loads(AGREE.read_text())["files"]
    report = {}
    for rel, info in files.items():
        if info["checker"] != CID or info["mode"] != "full":
            continue
        path = ROOT / rel
        backup = path.with_name(path.stem + ".pre_cpuverif.quarantined.jsonl")
        if not backup.is_file():
            shutil.copy2(path, backup)
        new = {r["instance_id"]: r for r in read_jsonl(MERGED / f"{CID}__{info['group']}.jsonl")}
        rows = read_jsonl(backup)
        replaced = flipped = 0
        out = []
        for r in rows:
            n = new.get(r["instance_id"])
            if n is None:
                out.append(r)
                continue
            replaced += 1
            flipped += int(str(n.get("verdict")) != str(r.get("verdict")))
            out.append({**n, **{k: r[k] for k in ("verifier", "model") if k in r}})
        with path.open("w") as fh:
            for r in out:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        report[rel] = {"rows": len(rows), "replaced": replaced, "verdict_flips": flipped,
                       "backup": str(backup.relative_to(ROOT))}
        print(f"{rel:55s} rows={len(rows)} replaced={replaced} flips={flipped}")
    OUT.write_text(json.dumps(report, indent=1) + "\n")


if __name__ == "__main__":
    main()
