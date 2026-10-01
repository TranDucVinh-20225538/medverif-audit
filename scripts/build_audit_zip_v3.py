#!/usr/bin/env python3
"""Audit snapshot v3: results (all packs), data, qc, scripts/src/analysis, notes, paper_numbers_final.md.

No keys, no .env, no usernames: IAA answer keys excluded, secrets scanned (build fails on a hit),
absolute paths and the account name scrubbed in every text file copied into the zip.
Usage: build_audit_zip_v3.py [--dry-run]
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_ZIP = ROOT / "release/audit_snapshot_v3.zip"
OUT_MANIFEST = ROOT / "release/audit_snapshot_v3_manifest.json"

INCLUDE_DIRS = ["results/raw", "results/raw_m1", "results/raw_node30", "results/tables", "results/figures",
                "data", "qc", "scripts", "src", "analysis", "notes", "configs", "config", "tests"]
INCLUDE_FILES = ["paper_numbers_final.md", "README.md", "pyproject.toml", "results/cache/m1_strong_gate_indep.json",
                 "release/canonical_sources.tsv"]
INCLUDE_GLOBS = ["jobs/*.sbatch", "jobs/*.sh"]

EXCLUDE_PREFIXES = ("data/t15_cpuverif_chunks/", "data/minicheck_cpuverif_chunks/", "data/smoke/")
EXCLUDE_FILES = {"qc/iaa_key_DO_NOT_SHARE.csv", "qc/iaa_answer_key.jsonl"}
EXCLUDE_NAME_RE = re.compile(
    r"(^\.env$|\.env$|\.bak(\.|$)|\.quarantined\.|\.pyc$|\.tar\.gz$|\.zip$|\.safetensors$|\.bin$|\.pt$|\.ckpt$"
    r"|secret|credential|token|password|api_?key|iaa_key|answer_key)",
    re.I,
)
EXCLUDE_PART = {"__pycache__", "_quarantine", ".cache", ".git", "wandb", "hf_home", "models", "checkpoints"}
TEXT_SUFFIX = {".jsonl", ".json", ".md", ".csv", ".tsv", ".txt", ".py", ".sh", ".sbatch", ".toml", ".yaml", ".yml",
               ".cfg", ".ini", ".co", ".tex", ".log", ""}

SCRUB = [
    ("/data2/cmdir/home/toandq", "$HOME"),
    ("/data2/hpcshared/medverif-audit", "<repo>"),
    ("/data2/hpcshared", "<shared>"),
    ("/data2/shared", "<shared_apps>"),
    ("/data2/cmdir/home", "<home_root>"),
    ("toandq", "<user>"),
]
SECRET_RE = re.compile(
    r"(sk-or-v1-[0-9a-f]{32,}|sk-ant-[A-Za-z0-9_\-]{20,}|sk-proj-[A-Za-z0-9_\-]{20,}|\bsk-[A-Za-z0-9]{40,}"
    r"|\bhf_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}"
    r"|(?:OPENROUTER|OPENAI|ANTHROPIC|HF|HUGGINGFACE)[A-Z_]*(?:KEY|TOKEN)\s*=\s*['\"]?[A-Za-z0-9_\-]{20,})"
)


def git_head() -> str:
    try:
        return subprocess.check_output(["/usr/bin/git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def excluded(rel: str) -> bool:
    if rel in EXCLUDE_FILES or rel.startswith(EXCLUDE_PREFIXES):
        return True
    parts = rel.split("/")
    if any(p in EXCLUDE_PART for p in parts[:-1]):
        return True
    return bool(EXCLUDE_NAME_RE.search(parts[-1]))


def collect() -> list[Path]:
    out: set[Path] = set()
    for d in INCLUDE_DIRS:
        base = ROOT / d
        if base.is_dir():
            out.update(p for p in base.rglob("*") if p.is_file() and not p.is_symlink())
    for f in INCLUDE_FILES:
        if (ROOT / f).is_file():
            out.add(ROOT / f)
    for g in INCLUDE_GLOBS:
        out.update(p for p in ROOT.glob(g) if p.is_file())
    return sorted(p for p in out if not excluded(p.relative_to(ROOT).as_posix()))


def scrub(text: str) -> tuple[str, int]:
    n = 0
    for old, new in SCRUB:
        c = text.count(old)
        if c:
            n += c
            text = text.replace(old, new)
    return text, n


def main() -> None:
    dry = "--dry-run" in sys.argv
    files = collect()
    head = git_head()
    manifest = {"built_at": datetime.now(timezone.utc).isoformat(), "git_head": head, "files": {}, "scrubbed_files": 0,
                "scrub_replacements": 0, "excluded_by_policy": sorted(EXCLUDE_FILES) + [p.rstrip("/") for p in EXCLUDE_PREFIXES]}
    hits: list[str] = []
    zf = None if dry else zipfile.ZipFile(OUT_ZIP.with_suffix(".zip.tmp"), "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6)
    total = 0
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        raw = p.read_bytes()
        total += len(raw)
        data = raw
        if p.suffix.lower() in TEXT_SUFFIX:
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = None
            if text is not None:
                for m in SECRET_RE.finditer(text):
                    hits.append(f"{rel}: {m.group(0)[:12]}…")
                text, n = scrub(text)
                if n:
                    manifest["scrubbed_files"] += 1
                    manifest["scrub_replacements"] += n
                data = text.encode("utf-8")
        elif b"toandq" in raw:
            hits.append(f"{rel}: binary file contains account name")
        manifest["files"][rel] = hashlib.sha256(data).hexdigest()
        if zf:
            zf.writestr(rel, data)
    if hits:
        if zf:
            zf.close()
            OUT_ZIP.with_suffix(".zip.tmp").unlink()
        print("SECRET/USERNAME SCAN FAILED:\n" + "\n".join(hits[:50]), file=sys.stderr)
        sys.exit(2)
    readme = "\n".join([
        "# Audit snapshot v3",
        "",
        f"Built {manifest['built_at']} from commit `{head}`.",
        "",
        "Contents: `results/raw`, `results/raw_m1`, `results/raw_node30` (all packs incl. m1_strong_final amendment 5, T13, T14, "
        "T15 incl. AggreFact, T17, T19, T24b), `results/tables`, `results/figures`, `data/` (rescoring chunk dirs excluded), "
        "`qc/` (IAA answer keys excluded), `scripts/`, `src/`, `analysis/`, `notes/`, `jobs/*.sbatch|*.sh`, `paper_numbers_final.md`.",
        "",
        "Paper numbers: `paper_numbers_final.md` (env, agreement, source, script and commit per number). "
        "Regenerate with `python scripts/paper_numbers_final.py`.",
        "",
        "Not included by policy: API keys and `.env` files, IAA answer keys, `*.bak*` and `*.quarantined.*` backups, "
        "`_quarantine/`, model weights and caches. Absolute paths are replaced by `<repo>`, `<shared>`, `$HOME`; "
        "the account name by `<user>`.",
        "",
        "`release/audit_snapshot_v3_manifest.json`: sha256 of every file as stored in the zip.",
        "",
    ])
    if zf:
        zf.writestr("AUDIT_SNAPSHOT_V3_README.md", readme)
        zf.writestr("release/audit_snapshot_v3_manifest.json", json.dumps(manifest, indent=1) + "\n")
        zf.close()
        OUT_ZIP.with_suffix(".zip.tmp").replace(OUT_ZIP)
        with zipfile.ZipFile(OUT_ZIP) as z:
            bad = [n for n in z.namelist() if n in EXCLUDE_FILES or "toandq" in z.read(n).decode("utf-8", "ignore")]
        if bad:
            print("POST-CHECK FAILED: " + ", ".join(bad[:20]), file=sys.stderr)
            sys.exit(3)
        manifest["zip_sha256"] = hashlib.sha256(OUT_ZIP.read_bytes()).hexdigest()
        manifest["zip_bytes"] = OUT_ZIP.stat().st_size
    OUT_MANIFEST.write_text(json.dumps({**{k: v for k, v in manifest.items() if k != "files"}, "n_files": len(files)}, indent=1) + "\n")
    print(json.dumps({"dry_run": dry, "n_files": len(files), "input_mb": round(total / 2**20, 1),
                      "zip_mb": round(manifest.get("zip_bytes", 0) / 2**20, 1), "scrubbed_files": manifest["scrubbed_files"],
                      "scrub_replacements": manifest["scrub_replacements"]}))


if __name__ == "__main__":
    main()
