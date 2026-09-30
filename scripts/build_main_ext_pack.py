#!/usr/bin/env python3
"""main_ext: MedRAG Textbooks + Qwen72B/Phi-4 stage1 + author_whitelist perturb."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from text_utils import author_whitelist_unit_conversion  # noqa: E402
from verifiers.io_utils import read_jsonl  # noqa: E402

OUT_BASES = ROOT / "data/main_ext/bases_main_ext.jsonl"
OUT_INST = ROOT / "data/main_ext/instances_main_ext.jsonl"
QC = ROOT / "qc/main_ext_review.csv"
MANIFEST = ROOT / "notes/main_ext_manifest.json"
STAGE1 = ROOT / "data/main_ext/stage1"
CAND = ROOT / "data/main_ext/candidates_selected.jsonl"


def run(cmd: list[str], env: dict | None = None) -> None:
    merged = {**os.environ, **(env or {})}
    subprocess.run(cmd, check=True, cwd=str(ROOT), env=merged)


def base_from_stage1(row: dict) -> dict:
    return {
        "id": row["id"],
        "type": row["type"],
        "claim": row["claim"],
        "evidence": row["evidence"],
        "claim_span_start": row["claim_span_start"],
        "claim_span_end": row["claim_span_end"],
        "evidence_span_start": row["evidence_span_start"],
        "evidence_span_end": row["evidence_span_end"],
        "target_span_claim": row["target_span_claim"],
        "target_span_evidence": row["target_span_evidence"],
        "subset": "main_ext",
        "book": row.get("book"),
        "source_passage_id": row.get("source_passage_id"),
        "target_sentence": row.get("target_sentence"),
        "generator_model": row.get("generator_model"),
        "validator_model": row.get("validator_model"),
    }


def run_stage1(max_candidates: int, smoke: bool) -> None:
    run([sys.executable, str(ROOT / "scripts/main_ext_select_candidates.py"), "--max-candidates", str(max_candidates)])
    STAGE1.mkdir(parents=True, exist_ok=True)
    env = {
        "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / 'scripts/expand'}",
        "MEDVERIF_EXPAND_LEDGER": str(STAGE1 / "api_spend.jsonl"),
        "MEDVERIF_EXPAND_BUDGET_USD": os.environ.get("MEDVERIF_LANE_A_CAP_USD", "3"),
        "MEDVERIF_LANE_A_SYNC": "1",
    }
    if os.environ.get("MEDVERIF_USE_OPENROUTER") != "1":
        raise RuntimeError("main_ext requires MEDVERIF_USE_OPENROUTER=1 (Qwen72B + Phi-4)")
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "src/stage12_openrouter.py"),
            "--candidates",
            str(CAND),
            "--outdir",
            str(STAGE1),
            "--template-note",
            str(ROOT / "notes/main_ext_chat_template.md"),
        ],
        cwd=str(ROOT),
        env={**os.environ, **env},
        check=False,
    )
    if proc.returncode not in (0, 2) and not (STAGE1 / "base_pairs.jsonl").is_file():
        raise subprocess.CalledProcessError(proc.returncode, proc.args)


def run_perturb(bases: list[dict], out_inst: Path, failures: Path) -> list[dict]:
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as tmp:
        for b in bases:
            tmp.write(json.dumps(b, ensure_ascii=False) + "\n")
        base_path = Path(tmp.name)
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "src/perturb.py"),
            "--base",
            str(base_path),
            "--out",
            str(out_inst),
            "--failures",
            str(failures),
            "--unit-inv-policy",
            "author_whitelist",
        ],
        check=True,
        cwd=str(ROOT),
        env=env,
    )
    return list(read_jsonl(out_inst))


def write_qc_all_inv(instances: list[dict]) -> None:
    inv = [r for r in instances if r.get("condition") == "INV-claim"]
    QC.parent.mkdir(parents=True, exist_ok=True)
    with QC.open("w", newline="") as handle:
        w = csv.writer(handle)
        w.writerow(["instance_id", "base_id", "condition", "magnitude", "unit_inv_source", "PI_ok", "notes"])
        for row in inv:
            w.writerow(
                [
                    row["instance_id"],
                    row["base_id"],
                    row["condition"],
                    row.get("magnitude"),
                    row.get("unit_inv_source") or "",
                    "",
                    "",
                ]
            )


def bases_with_whitelist_inv(instances: list[dict], bases: list[dict]) -> set[str]:
    ok: set[str] = set()
    base_by_id = {b["id"]: b for b in bases}
    for row in instances:
        if row.get("condition") != "INV-claim" or row.get("magnitude") != "unit_conversion":
            continue
        bid = row["base_id"]
        base = base_by_id.get(bid)
        if not base:
            continue
        span = base["target_span_claim"]
        sent = base.get("claim") or ""
        if author_whitelist_unit_conversion(span, sent):
            ok.add(bid)
    return ok


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--target-bases", type=int, default=80)
    p.add_argument("--smoke-bases", type=int, default=0)
    p.add_argument("--max-stage1", type=int, default=250)
    args = p.parse_args()
    target = args.smoke_bases if args.smoke_bases > 0 else args.target_bases
    # ~40% stage1 keep → need ≥200 candidates for ~80 kept bases (no filter loosening).
    stage1_n = args.max_stage1 if args.smoke_bases == 0 else min(args.max_stage1, target + 5)
    run_stage1(stage1_n, smoke=args.smoke_bases > 0)
    pairs_path = STAGE1 / "base_pairs.jsonl"
    if not pairs_path.is_file():
        raise FileNotFoundError(f"missing {pairs_path} — stage1 produced no bases")
    all_bases = [base_from_stage1(r) for r in read_jsonl(pairs_path)]
    fail_path = ROOT / "notes/main_ext_perturb_failures.json"
    instances = run_perturb(all_bases, OUT_INST, fail_path)
    wl = bases_with_whitelist_inv(instances, all_bases)
    kept_bases = [b for b in all_bases if b["id"] in wl][:target]
    if len(kept_bases) < target and args.smoke_bases == 0:
        print(json.dumps({"warn": "whitelist_inv_bases", "have": len(kept_bases), "want": target}), flush=True)
    kept_ids = {b["id"] for b in kept_bases}
    instances = [r for r in instances if r["base_id"] in kept_ids]
    OUT_BASES.parent.mkdir(parents=True, exist_ok=True)
    with OUT_BASES.open("w") as handle:
        for b in kept_bases:
            handle.write(json.dumps(b, ensure_ascii=False) + "\n")
    with OUT_INST.open("w") as handle:
        for row in instances:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    write_qc_all_inv(instances)
    run([sys.executable, str(ROOT / "scripts/main_ext_disjointness.py"), "--bases", str(OUT_BASES)])
    cand_n = sum(1 for _ in read_jsonl(CAND)) if CAND.is_file() else None
    manifest = {
        "source": "MedRAG_Textbooks_only",
        "pipeline": "stage12_openrouter (Qwen2.5-72B + Phi-4) + perturb author_whitelist",
        "not_used": "data/expand/candidates_pool.jsonl (StatPearls/expand QC fail ~63%)",
        "stage1_candidates": cand_n,
        "stage1_bases_out": len(all_bases),
        "stage1_keep_rate": (len(all_bases) / cand_n) if cand_n else None,
        "bases_kept": len(kept_bases),
        "bases_target": target,
        "bases_whitelist_inv": len(wl),
        "instances": len(instances),
        "bases_path": str(OUT_BASES.relative_to(ROOT)),
        "instances_path": str(OUT_INST.relative_to(ROOT)),
        "qc_inv_rows": sum(1 for r in instances if r.get("condition") == "INV-claim"),
        "qc_path": str(QC.relative_to(ROOT)),
        "disjointness": "data/main_ext/disjointness_check.json",
        "stage1_dir": str(STAGE1.relative_to(ROOT)),
        "smoke": args.smoke_bases > 0,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
