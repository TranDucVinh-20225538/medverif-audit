#!/usr/bin/env python3
"""T15 step 3: score base + fine-tuned MiniCheck; draft notes/t15_report.md."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "analysis"))

from analyze import read_jsonl  # noqa: E402
from verifiers.io_utils import append_jsonl, done_ids  # noqa: E402

def _row_id(row: dict) -> str:
    if row.get("instance_id"):
        return str(row["instance_id"])
    cid = row.get("contamination_identifier") or row.get("id")
    if cid:
        return str(cid)
    raise KeyError(f"row missing instance_id: keys={list(row.keys())[:12]}")


PACKS = (
    ("main_dose", ROOT / "data/v3/instances_main.jsonl"),
    ("t14", ROOT / "data/t14/instances_t14.jsonl"),
    ("t18", ROOT / "data/t18/instances_t18.jsonl"),
    ("t18_medical_expand", ROOT / "data/t18_medical_expand/instances_t18.jsonl"),
)


def _normalize_rows(rows: list[dict]) -> list[dict]:
    out: list[dict] = []
    for row in rows:
        nr = dict(row)
        nr.setdefault("instance_id", _row_id(row))
        if not (nr.get("evidence") or "").strip() and (nr.get("doc") or "").strip():
            nr["evidence"] = nr["doc"]
        out.append(nr)
    return out


def _log_progress(tag: str, n_done: int, total: int) -> None:
    print(json.dumps({"t15": tag, "progress": n_done, "total": total}), flush=True)


def _score_pack(rows: list[dict], out: Path, *, use_t15: bool, progress_tag: str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = _normalize_rows(rows)
    already = done_ids(out)
    todo = [r for r in rows if r.get("valid", True) and r["instance_id"] not in already]
    todo = [r for r in todo if (r.get("claim") or "").strip() and (r.get("evidence") or "").strip()]
    total_target = len(already) + len(todo)
    if not todo:
        _log_progress(progress_tag, len(already), total_target)
        return
    _log_progress(progress_tag, len(already), total_target)
    if use_t15:
        from verifiers import t15_minicheck_roberta as t15

        bundle, _ = t15.load()
        step = 8
        for off in range(0, len(todo), step):
            append_jsonl(out, t15.score_batch(bundle, todo[off : off + step]))
            n = len(already) + min(off + step, len(todo))
            if off == 0 or (off // step) % 25 == 0 or off + step >= len(todo):
                _log_progress(progress_tag, n, total_target)
    else:
        from verifiers import t6a_minicheck as mc

        model, _ = mc.load("t6a_minicheck_roberta")
        step = 4
        for off in range(0, len(todo), step):
            append_jsonl(out, mc.score_batch(model, todo[off : off + step], "t6a_minicheck_roberta"))
            n = len(already) + min(off + step, len(todo))
            if off == 0 or (off // step) % 50 == 0 or off + step >= len(todo):
                _log_progress(progress_tag, n, total_target)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=ROOT / "notes/t15_report.md")
    parser.add_argument(
        "--packs",
        default="all",
        help="comma-separated pack names or 'all' (default)",
    )
    parser.add_argument(
        "--aggrefact-only",
        action="store_true",
        help="score LLM-AggreFact test split only (resume-friendly)",
    )
    args = parser.parse_args()

    raw_root = ROOT / "results/raw/t15"
    status_lines = ["# T15 evaluation (auto draft)", ""]

    want = {p.strip() for p in args.packs.split(",")} if args.packs != "all" else None
    if args.aggrefact_only:
        want = set()

    for name, path in PACKS:
        if want is not None and name not in want:
            continue
        if not path.is_file():
            status_lines.append(f"- **{name}:** skipped (missing `{path.relative_to(ROOT)}`)")
            continue
        rows = read_jsonl(path)
        base_out = raw_root / f"base_{name}.jsonl"
        ft_out = raw_root / f"ft_{name}.jsonl"
        _score_pack(rows, base_out, use_t15=False, progress_tag=f"base_{name}")
        _score_pack(rows, ft_out, use_t15=True, progress_tag=f"ft_{name}")
        status_lines.append(
            f"- **{name}:** base `{base_out.relative_to(ROOT)}` ({len(done_ids(base_out))} rows), "
            f"ft `{ft_out.relative_to(ROOT)}` ({len(done_ids(ft_out))} rows)"
        )

    # LLM-AggreFact test regression (balanced acc) when test split exists
    agg_test = ROOT / "data/t8/aggrefact/test.jsonl"
    run_agg = agg_test.is_file() and (args.aggrefact_only or args.packs == "all")
    if run_agg:
        rows = read_jsonl(agg_test)
        for tag, use_t15 in (("base", False), ("ft", True)):
            out = raw_root / f"{tag}_aggrefact_test.jsonl"
            _score_pack(rows, out, use_t15=use_t15, progress_tag=f"{tag}_aggrefact_test")
        status_lines.append("- **AggreFact test:** scored under `results/raw/t15/*_aggrefact_test.jsonl`")
    elif args.aggrefact_only:
        status_lines.append("- **AggreFact:** missing `data/t8/aggrefact/test.jsonl`")
    elif not agg_test.is_file() and args.packs == "all":
        status_lines.append("- **AggreFact:** skipped (run `scripts/t8_download_aggrefact.py` first)")

    status_lines += [
        "",
        "Full QVC table (QI/NS/US, McNemar, CIs): extend with `qvc/evaluate/card.py` on joined rows.",
        "",
    ]
    import subprocess

    try:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts/t15_aggrefact_report.py")],
            capture_output=True,
            text=True,
            check=False,
            cwd=str(ROOT),
        )
        if proc.stdout.strip():
            status_lines.extend(["", proc.stdout.strip()])
        elif proc.returncode:
            status_lines.append(f"- **AggreFact report:** failed ({proc.stderr[:200]})")
    except Exception as exc:
        status_lines.append(f"- **AggreFact report:** skipped ({exc})")

    args.report.write_text("\n".join(status_lines) + "\n")
    print(json.dumps({"report": str(args.report)}, indent=2))


if __name__ == "__main__":
    main()
