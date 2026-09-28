"""Split instances_cpu_early.jsonl into main and threshold JSONL files."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/data2/hpcshared/medverif-audit")
SRC = ROOT / "data" / "v3" / "instances_cpu_early.jsonl"


def write(path: Path, rows: list[dict]) -> None:
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    rows = []
    with SRC.open() as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    main_rows = [r for r in rows if r.get("subset") == "main" and r.get("valid", True)]
    thr_rows = [r for r in rows if r.get("subset") == "threshold" and r.get("valid", True)]
    out_main = ROOT / "data" / "v3" / "instances_cpu_main.jsonl"
    out_thr = ROOT / "data" / "v3" / "instances_cpu_threshold.jsonl"
    write(out_main, main_rows)
    write(out_thr, thr_rows)
    print(json.dumps({"main": len(main_rows), "threshold": len(thr_rows)}))


if __name__ == "__main__":
    main()
