#!/usr/bin/env python3
"""Prepare V4 legacy/llama files and re-score with registry Llama-3.3-70B (budget cap)."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from glob import glob
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "notes/v4_llama_rescore_packs.json"
VERIFIER = "v4_ragas_nli"
WANT_MODEL = "meta-llama/llama-3.3-70b-instruct"


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else "")
    )


def is_llama_row(row: dict) -> bool:
    m = (row.get("api_model") or row.get("model") or "").lower()
    return WANT_MODEL.split("/")[-1] in m or WANT_MODEL in m


def sum_cost(path: Path) -> float:
    total = 0.0
    for row in read_jsonl(path):
        c = row.get("api_cost_usd")
        if c is not None:
            total += float(c)
    return total


def prepare_pack(pack: dict) -> dict:
    score_dir = ROOT / pack["score_dir"]
    live = score_dir / f"{VERIFIER}.jsonl"
    legacy = score_dir / f"{VERIFIER}.legacy.jsonl"
    llama = score_dir / f"{VERIFIER}.llama.jsonl"
    out = {"id": pack["id"], "legacy": str(legacy.relative_to(ROOT)), "llama": str(llama.relative_to(ROOT))}

    if pack.get("reuse_llama_from_live") and live.is_file() and not llama.is_file():
        rows = read_jsonl(live)
        llama_rows = [r for r in rows if is_llama_row(r)]
        if llama_rows:
            write_jsonl(llama, llama_rows)
            out["seeded_llama"] = len(llama_rows)

    if not legacy.is_file():
        if live.is_file():
            rows = read_jsonl(live)
            if pack.get("reuse_llama_from_live") and all(is_llama_row(r) for r in rows):
                for pattern in pack.get("legacy_backup_globs") or []:
                    for cand in sorted(glob(str(ROOT / pattern)), key=lambda p: -Path(p).stat().st_mtime):
                        backup_rows = read_jsonl(Path(cand))
                        if backup_rows:
                            write_jsonl(legacy, backup_rows)
                            out["legacy_from_backup"] = cand
                            break
                if not legacy.is_file():
                    write_jsonl(legacy, [])
                    out["legacy_empty"] = True
            else:
                shutil.copy2(live, legacy)
                out["legacy_from_live"] = True
            if live.is_file() and legacy.is_file():
                live.unlink()
                out["removed_live"] = True
        else:
            for pattern in pack.get("legacy_backup_globs") or []:
                for cand in sorted(glob(str(ROOT / pattern)), key=lambda p: -Path(p).stat().st_mtime):
                    backup_rows = read_jsonl(Path(cand))
                    if backup_rows:
                        write_jsonl(legacy, backup_rows)
                        out["legacy_from_backup"] = cand
                        break
    elif live.is_file() and llama.is_file():
        live.unlink()

    out["legacy_n"] = len(read_jsonl(legacy))
    out["llama_n"] = len(read_jsonl(llama))
    return out


def run_score(pack: dict, budget_usd: float, spent: float) -> tuple[float, dict]:
    inst = ROOT / pack["instances"]
    score_dir = ROOT / pack["score_dir"]
    llama = score_dir / f"{VERIFIER}.llama.jsonl"
    if not inst.is_file():
        return spent, {"skipped": "missing_instances", "instances": str(inst)}
    if spent >= budget_usd:
        return spent, {"skipped": "budget_exhausted"}
    cmd = [
        sys.executable,
        str(ROOT / "src/score_jsonl.py"),
        "--verifier",
        VERIFIER,
        "--instances",
        str(inst),
        "--out",
        str(llama),
    ]
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "MEDVERIF_USE_OPENROUTER": "1", "MEDVERIF_M1": "0"}
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/openrouter_budget.py")],
        cwd=ROOT,
        env=env,
        check=False,
    )
    proc = subprocess.run(cmd, cwd=ROOT, env=env)
    spent = sum_cost(llama) + sum(
        sum_cost(ROOT / p["score_dir"] / f"{VERIFIER}.llama.jsonl")
        for p in json.loads(MANIFEST.read_text())["packs"]
    )
    return spent, {"exit_code": proc.returncode, "llama_n": len(read_jsonl(llama))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--pack", default="", help="Single pack id")
    parser.add_argument("--budget-usd", type=float, default=0)
    args = parser.parse_args()
    data = json.loads(MANIFEST.read_text())
    budget = args.budget_usd or float(data.get("budget_usd", 3.0))
    packs = [p for p in data["packs"] if not args.pack or p["id"] == args.pack]
    prep = [prepare_pack(p) for p in packs]
    log = ROOT / "notes/v4_llama_rescore_prepare.json"
    log.write_text(json.dumps({"prepare": prep}, indent=2) + "\n")
    print(json.dumps({"prepared": len(prep)}, indent=2))
    if args.prepare_only:
        return
    spent = sum(
        sum_cost(ROOT / p["score_dir"] / f"{VERIFIER}.llama.jsonl") for p in data["packs"]
    )
    results = []
    for pack in packs:
        spent, rep = run_score(pack, budget, spent)
        rep["pack"] = pack["id"]
        rep["spent_usd_est"] = round(spent, 4)
        results.append(rep)
        if spent >= budget:
            break
    out = ROOT / "notes/v4_llama_rescore_run.json"
    out.write_text(json.dumps({"results": results, "spent_usd_est": spent}, indent=2) + "\n")


if __name__ == "__main__":
    main()
