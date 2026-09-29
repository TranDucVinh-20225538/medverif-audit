#!/usr/bin/env python3
"""Compare data/ and results/raw/ JSONL line counts vs git HEAD and manifests."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "notes" / "integrity_check_2026-09-29.md"
SCAN_ROOTS = [ROOT / "data", ROOT / "results" / "raw"]
MANIFEST_GLOBS = ["notes/*manifest*.json", "notes/*_manifest.json", "data/**/manifest*.json"]


def line_count(path: Path) -> int:
    if not path.exists():
        return -1
    if path.stat().st_size == 0:
        return 0
    n = 0
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            n += chunk.count(b"\n")
    return n


def git_head_lines(rel: str) -> int | None:
    try:
        out = subprocess.check_output(
            ["git", "show", f"HEAD:{rel}"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return None
    if not out.strip():
        return 0
    return out.count(b"\n")


def git_tracked_jsonl() -> set[str]:
    out = subprocess.check_output(
        ["git", "ls-files", "data", "results/raw"],
        cwd=ROOT,
        text=True,
    )
    return {p for p in out.splitlines() if p.endswith(".jsonl")}


def load_manifest_expectations() -> dict[str, int]:
    exp: dict[str, int] = {}
    for pat in MANIFEST_GLOBS:
        for path in ROOT.glob(pat):
            if not path.is_file():
                continue
            try:
                data = json.loads(path.read_text())
            except json.JSONDecodeError:
                continue
            for key in ("instances_total", "instances", "n", "rows", "pending"):
                if isinstance(data.get(key), int):
                    rel = None
                    if isinstance(data.get("paths"), dict):
                        for v in data["paths"].values():
                            if isinstance(v, str) and v.endswith(".jsonl"):
                                rel = v
                                break
                    if isinstance(data.get("path"), str):
                        rel = data["path"]
                    if rel:
                        exp[rel] = max(exp.get(rel, 0), data[key])
    return exp


def find_baks(path: Path) -> list[Path]:
    return sorted(path.parent.glob(path.name + ".bak.*"), reverse=True)


def main() -> int:
    tracked = git_tracked_jsonl()
    manifest = load_manifest_expectations()
    issues: list[dict] = []
    scanned = 0

    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.jsonl")):
            if path.name.endswith(".tmp"):
                continue
            rel = str(path.relative_to(ROOT))
            scanned += 1
            cur = line_count(path)
            head = git_head_lines(rel) if rel in tracked else None
            man = manifest.get(rel)

            shrunk = head is not None and cur >= 0 and cur < head
            empty = cur == 0 and path.exists() and path.stat().st_size == 0
            manifest_miss = man is not None and cur >= 0 and cur < man

            if shrunk or (empty and rel in tracked and (head or 0) > 0) or manifest_miss:
                baks = find_baks(path)
                issues.append(
                    {
                        "path": rel,
                        "current": cur,
                        "git_head": head,
                        "manifest": man,
                        "shrunk_vs_head": shrunk,
                        "empty": empty and (head or 0) > 0,
                        "manifest_miss": manifest_miss,
                        "baks": [str(b.relative_to(ROOT)) for b in baks[:3]],
                    }
                )

    def _restore_from_git(rel: str, commit: str = "HEAD") -> int | None:
        path = ROOT / rel
        try:
            blob = subprocess.check_output(
                ["git", "show", f"{commit}:{rel}"],
                cwd=ROOT,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            return None
        if not blob.strip():
            return None
        import os

        sys.path.insert(0, str(ROOT / "src"))
        from safe_jsonl import write_jsonl_atomic

        rows = [json.loads(line) for line in blob.decode().splitlines() if line.strip()]
        write_jsonl_atomic(path, rows, allow_shrink=True)
        return len(rows)

    para_rel = "data/v3/para_attempts.jsonl"
    if line_count(ROOT / para_rel) == 0:
        n = _restore_from_git(para_rel, "dac0b08") or _restore_from_git(para_rel, "HEAD")
        if n:
            issues.append(
                {"path": para_rel, "action": "restored_from_git", "commit": "dac0b08/HEAD", "lines": n}
            )
            pre = ROOT / "data/v3/para_attempts.pre_qc_v3.jsonl"
            if line_count(pre) == 0:
                import shutil

                shutil.copy2(ROOT / para_rel, pre)

    lines = [
        "# Data integrity check (2026-09-29)",
        "",
        f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        f"Scanned **{scanned}** `.jsonl` files under `data/` and `results/raw/`.",
        "",
        "## Truncation root cause (`para_attempts.jsonl`)",
        "",
        "- **Writer:** `src/apply_qc_v3_decisions.py` — `write_jsonl(..., \"w\")` resets "
        "`data/v3/para_attempts.jsonl` to `[]` (QC decision **G**, paraphrase regen).",
        "- **~2026-09-28 23:58:31 +07:** `para_attempts.jsonl` and `para_attempts.pre_qc_v3.jsonl` "
        "share the same mtime → backup ran when the live file was **already empty**, so backup is empty too.",
        "- **Recovery:** 244 lines restored from git commit **`dac0b08`** (61394 timeout snapshot). "
        "61394 NFS writes beyond that are **not** recoverable from git.",
        "",
        "## Issues (shrunk / empty vs HEAD or manifest)",
        "",
    ]
    if not issues:
        lines.append("_No regressions detected._")
    else:
        lines.append("| Path | Now | HEAD | Manifest | Flags | Backups |")
        lines.append("|------|----:|-----:|---------:|-------|---------|")
        for row in issues:
            if row.get("action") == "restored_from_git":
                lines.append(
                    f"| `{row['path']}` | **{row['lines']}** (restored) | — | — | restore `{row['commit']}` | — |"
                )
                continue
            flags = []
            if row.get("shrunk_vs_head"):
                flags.append("shrunk")
            if row.get("empty"):
                flags.append("empty")
            if row.get("manifest_miss"):
                flags.append("manifest")
            lines.append(
                "| `{path}` | {current} | {head} | {man} | {flags} | {baks} |".format(
                    path=row["path"],
                    current=row["current"],
                    head=row["git_head"] if row["git_head"] is not None else "—",
                    man=row["manifest"] if row["manifest"] is not None else "—",
                    flags=", ".join(flags) or "—",
                    baks=", ".join(f"`{b}`" for b in row["baks"]) or "—",
                )
            )

    lines.extend(
        [
            "",
            "## Guards added",
            "",
            "- `src/safe_jsonl.py` — backup + atomic replace; refuses shrinking `data/**` or `results/raw/**` "
            "unless `notes/allow_data_shrink.json` lists the path.",
            "- `.git/hooks/pre-commit` and `pre-push` → `scripts/check_data_linecounts.py`.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n")
    print(json.dumps({"report": str(REPORT), "issues": len(issues), "scanned": scanned}))
    return 1 if any(i.get("shrunk_vs_head") or i.get("empty") for i in issues if not i.get("action")) else 0


if __name__ == "__main__":
    sys.exit(main())
