"""Apply study_verdict post-hoc to V1 raw outputs. Keeps released_parser_score unchanged."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from v1_parser import released_verdict, study_verdict


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def reparse_file(path: Path, in_place: bool) -> dict:
    rows = read_jsonl(path)
    n = 0
    disagree = 0
    for row in rows:
        raw = row.get("raw_output")
        if raw is None:
            continue
        released = row.get("released_parser_score")
        if released is None:
            released = row.get("score")
        rel_v = released_verdict(raw)
        study = study_verdict(raw)
        row["released_verdict"] = rel_v
        row["study_verdict"] = study
        row["verdict"] = study
        row["score"] = (
            None
            if study == "PARSE_FAIL"
            else 1.0
            if study == "PASS"
            else 0.0
        )
        if rel_v != study:
            disagree += 1
        n += 1
    out = path
    if not in_place:
        out = path.with_name(path.stem + "_study" + path.suffix)
    write_jsonl(out, rows)
    rate = disagree / n if n else 0.0
    return {"path": str(out), "n": n, "disagree": disagree, "disagree_rate": rate}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path, help="results/raw/*.jsonl files")
    parser.add_argument("--in-place", action="store_true")
    args = parser.parse_args()
    summary = []
    for path in args.paths:
        summary.append(reparse_file(path, args.in_place))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
