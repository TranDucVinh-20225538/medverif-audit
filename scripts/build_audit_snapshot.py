#!/usr/bin/env python3
"""Build release/audit_snapshot.zip for independent recomputation (no secrets)."""

from __future__ import annotations

import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_ZIP = ROOT / "release/audit_snapshot.zip"
README = ROOT / "release/AUDIT_SNAPSHOT_README.md"

INSTANCE_FILES = [
    "data/v3/instances_main.jsonl",
    "data/v3/instances_cpu_early.jsonl",
    "data/v3/instances_inv_families.jsonl",
    "data/v3/t17_downdose.jsonl",
    "data/t7/instances_e1_unit.jsonl",
    "data/t14/instances_t14.jsonl",
    "data/t3/instances_inv_families.jsonl",
]

QC_FILES = [
    "qc/e1_pol_review.csv",
    "qc/inv_manual_review.csv",
    "qc/unit_naturalness.csv",
    "qc/dose3_labels.csv",
    "qc/t7_PI_ok_labels.csv",
    "qc/t14_PI_ok_labels.csv",
]

EXCLUSION_FILES = [
    "notes/allow_data_shrink.json",
    "notes/openrouter_verifiers.json",
    "src/non_dose_targets.py",
    "scripts/compute_paper_numbers.py",
]

SCORE_GLOBS = [
    "results/raw/v2a_minicheck.jsonl",
    "results/raw/v3_alignscore.jsonl",
    "results/raw/v1_medscore.jsonl",
    "results/raw/v4_ragas_nli.llama.jsonl",
    "results/raw/v5_ragas_nli.jsonl",
    "results/raw/v1b_medscore.jsonl",
    "results/raw/e2_main/*.jsonl",
    "results/raw/t7/*.jsonl",
    "results/raw/t14/*.jsonl",
    "results/raw/t17/*.jsonl",
    "results/raw/t3/*.jsonl",
    "results/raw/t3_t2/*.jsonl",
    "results/raw/t3_t6b/*.jsonl",
    "results/raw_m1/v1_medscore.jsonl",
    "results/raw_m1/v4_ragas_nli.llama.jsonl",
    "results/raw_m1/v2a_minicheck.jsonl",
    "results/raw_m1/v3_alignscore.jsonl",
]

NODE30_SCORE_GLOB = "results/raw_node30/**/*.jsonl"
NODE30_META = [
    "results/raw_node30/README.md",
    "results/raw_node30/node30_source.json",
]

COLUMN_DOC = {
    "instances_*.jsonl": "instance_id, base_id, type, condition, magnitude, claim, evidence, valid, invalid_reason, subset, …",
    "qc/*.csv": "Human labels: PI_ok, natural, dose audit fields (per file header row).",
    "results/raw/**/*.jsonl": "instance_id, verdict, score, verifier, api_model, api_provider (OpenRouter rows), latency_s, …",
    "scripts/compute_paper_numbers.py": "Canonical metric definitions and score denylist.",
}


def _git_head() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=ROOT,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            .strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _load_node30_source() -> dict:
    path = ROOT / "results/raw_node30/node30_source.json"
    if path.is_file():
        return json.loads(path.read_text())
    return {"branch": "node30-results", "commit": "unknown", "env": "node30"}


def _collect_score_paths() -> list[Path]:
    out: list[Path] = []
    for pat in SCORE_GLOBS:
        if "*" in pat:
            out.extend(sorted(ROOT.glob(pat)))
        else:
            p = ROOT / pat
            if p.is_file():
                out.append(p)
    # dedupe; skip denylisted v4 plain under results/raw (HPC)
    seen: set[str] = set()
    final: list[Path] = []
    for p in out:
        if p.name == "v4_ragas_nli.jsonl":
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel not in seen:
            seen.add(rel)
            final.append(p)
    return final


def _collect_node30_score_paths() -> list[Path]:
    return sorted(p for p in ROOT.glob(NODE30_SCORE_GLOB) if p.is_file())


def _jsonl_row_count(path: Path) -> int:
    n = 0
    with path.open("rb") as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def _jsonl_verifier(path: Path) -> str:
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                break
            v = row.get("verifier")
            if v:
                return str(v)
            break
    return path.stem


def _score_pack(path: Path) -> str:
    rel = path.relative_to(ROOT)
    parts = rel.parts
    if parts[0] == "results" and parts[1] in ("raw", "raw_node30", "raw_m1"):
        rest = parts[2:]
        if len(rest) <= 1:
            return "main"
        return rest[0]
    return rel.parent.as_posix()


def _score_source(path: Path, master_commit: str, node30: dict) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel.startswith("results/raw_node30/"):
        return f"{node30.get('branch', 'node30-results')}@{node30.get('commit', 'unknown')}"
    return f"master@{master_commit}"


def _build_manifest_tsv(
    score_paths: list[Path], master_commit: str, node30: dict
) -> str:
    lines = ["verifier\tpack\trows\tsource\tpath"]
    for path in score_paths:
        rel = path.relative_to(ROOT).as_posix()
        lines.append(
            "\t".join(
                [
                    _jsonl_verifier(path),
                    _score_pack(path),
                    str(_jsonl_row_count(path)),
                    _score_source(path, master_commit, node30),
                    rel,
                ]
            )
        )
    return "\n".join(lines) + "\n"


def write_readme(score_paths: list[Path], node30_paths: list[Path]) -> None:
    lines = [
        "# Audit snapshot",
        "",
        f"Built: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Recompute paper numbers:",
        "",
        "```bash",
        "python scripts/compute_paper_numbers.py",
        "```",
        "",
        "## Instance packs",
        "",
    ]
    for rel in INSTANCE_FILES:
        lines.append(f"- `{rel}` — columns: {COLUMN_DOC['instances_*.jsonl']}")
    lines += ["", "## QC / exclusions", ""]
    for rel in QC_FILES + EXCLUSION_FILES:
        lines.append(f"- `{rel}`")
    lines += ["", "## Score files included (HPC / master `results/raw/`)", ""]
    for p in score_paths:
        if p.relative_to(ROOT).as_posix().startswith("results/raw_node30/"):
            continue
        lines.append(f"- `{p.relative_to(ROOT).as_posix()}`")
    node30 = _load_node30_source()
    lines += [
        "",
        f"## Node30 CPU scores (`env={node30.get('env', 'node30')}`)",
        "",
        f"Under `results/raw_node30/` — sourced from `{node30.get('branch', 'node30-results')}` "
        f"at `{node30.get('commit', 'unknown')}` (MiniCheck, AlignScore, SummaC, HHEM, Granite, "
        "Bespoke, V2/V3, T9 NeMo). Not merged into `results/raw/` on master.",
        "",
    ]
    for p in node30_paths:
        lines.append(f"- `{p.relative_to(ROOT).as_posix()}`")
    lines += [
        "",
        "## Manifest",
        "",
        "- `release/score_manifest.tsv` — one row per score file: verifier, pack, row count, source branch/commit.",
        "",
        "## Excluded by policy",
        "",
        "- `results/raw/**/v4_ragas_nli.jsonl` (non-Llama / Qwen local on HPC tree only)",
        "- `**/_quarantine/**`, secrets, `.env`",
        "",
    ]
    README.parent.mkdir(parents=True, exist_ok=True)
    README.write_text("\n".join(lines) + "\n")


def main() -> None:
    master_commit = _git_head()
    node30 = _load_node30_source()
    score_paths = _collect_score_paths()
    node30_paths = _collect_node30_score_paths()
    all_score_paths = sorted(
        score_paths + node30_paths,
        key=lambda p: p.relative_to(ROOT).as_posix(),
    )
    write_readme(score_paths, node30_paths)
    manifest_tsv = _build_manifest_tsv(all_score_paths, master_commit, node30)
    OUT_ZIP.parent.mkdir(parents=True, exist_ok=True)
    manifest = {"files": [], "built_at": datetime.now(timezone.utc).isoformat()}
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in INSTANCE_FILES + QC_FILES + EXCLUSION_FILES:
            path = ROOT / rel
            if path.is_file():
                arc = rel
                zf.write(path, arcname=arc)
                manifest["files"].append(arc)
        for rel in NODE30_META:
            path = ROOT / rel
            if path.is_file():
                zf.write(path, arcname=rel)
                manifest["files"].append(rel)
        for path in all_score_paths:
            arc = path.relative_to(ROOT).as_posix()
            zf.write(path, arcname=arc)
            manifest["files"].append(arc)
        zf.writestr("release/AUDIT_SNAPSHOT_README.md", README.read_text())
        manifest["files"].append("release/AUDIT_SNAPSHOT_README.md")
        zf.writestr("release/score_manifest.tsv", manifest_tsv)
        manifest["files"].append("release/score_manifest.tsv")
        zf.writestr("release/manifest.json", json.dumps(manifest, indent=2) + "\n")
    size_mb = OUT_ZIP.stat().st_size / (1024 * 1024)
    print(json.dumps({"zip": str(OUT_ZIP), "size_bytes": OUT_ZIP.stat().st_size, "size_mb": round(size_mb, 2)}))


if __name__ == "__main__":
    main()
