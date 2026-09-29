#!/usr/bin/env python3
"""Audit V1/V4/V1b/V5 raw jsonl by api_model; optional quarantine of mismatches."""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAR = ROOT / "results/raw/_quarantine"
REG = json.loads((ROOT / "notes/openrouter_verifiers.json").read_text())

AUDIT_VERIFIERS = {
    "v1_medscore.jsonl": "v1_medscore",
    "v4_ragas_nli.jsonl": "v4_ragas_nli",
    "v1b_medscore.jsonl": "v1b_medscore",
    "v5_ragas_nli.jsonl": "v5_ragas_nli",
}

PROVEN_LLAMA = set(REG.get("file_provenance_llama_v4", []))
FORCE_QUAR_FILES = set(REG.get("file_provenance_quarantine_v4", []))


def iter_score_files() -> list[Path]:
    out = []
    for pattern in ("v1_medscore.jsonl", "v4_ragas_nli.jsonl", "v1b_medscore.jsonl", "v5_ragas_nli.jsonl"):
        for path in ROOT.glob(f"results/**/{pattern}"):
            if "_quarantine" in path.parts:
                continue
            out.append(path)
    return sorted(set(out))


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def expected_model(verifier_key: str) -> str:
    return REG["verifiers"][verifier_key]["openrouter_model"].lower()


def quarantine_sidecar(rel_path: str) -> Path:
    return Path(str(QUAR / rel_path) + ".quarantined.jsonl")


def count_quarantined(rel_path: str) -> int:
    suffix = f"{rel_path}.quarantined.jsonl"
    ids: set[str] = set()
    for side in QUAR.rglob("*.quarantined.jsonl"):
        if not (str(side).endswith(suffix) or side == quarantine_sidecar(rel_path)):
            continue
        for line in side.open():
            if line.strip():
                ids.add(json.loads(line)["instance_id"])
    return len(ids)


def audit_file(path: Path, verifier_key: str) -> dict:
    rel_path = rel(path)
    want = expected_model(verifier_key)
    by_model: Counter = Counter()
    total = 0
    registry_ok = 0
    wrong_model = 0
    unlogged = 0
    bad_ids: list[str] = []
    force = rel_path in FORCE_QUAR_FILES
    proven_llama = rel_path in PROVEN_LLAMA
    with path.open() as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            total += 1
            model = (row.get("api_model") or row.get("model") or "").strip()
            prov = row.get("api_provider") or row.get("provider") or ""
            if model:
                by_model[(model, prov or "-")] += 1
                if want in model.lower():
                    registry_ok += 1
                else:
                    wrong_model += 1
                    bad_ids.append(row["instance_id"])
            else:
                unlogged += 1
                by_model[("(no api_model)", prov or "-")] += 1
                if force or (verifier_key == "v4_ragas_nli" and not proven_llama):
                    bad_ids.append(row["instance_id"])
    breakdown = [
        {"model": m, "provider": p, "rows": c}
        for (m, p), c in sorted(by_model.items(), key=lambda x: (-x[1], x[0][0]))
    ]
    return {
        "path": rel_path,
        "verifier": verifier_key,
        "expected_model": REG["verifiers"][verifier_key]["openrouter_model"],
        "expected_provider": REG["verifiers"][verifier_key].get("provider", ""),
        "total": total,
        "registry_ok": registry_ok,
        "wrong_model": wrong_model,
        "unlogged": unlogged,
        "by_model": breakdown,
        "bad_ids": bad_ids,
        "quarantined_cumulative": count_quarantined(rel_path),
        "proven_llama_file": proven_llama,
        "force_quarantine_file": force,
    }


def quarantine_file(path: Path, bad_ids: set[str]) -> tuple[int, int]:
    if not bad_ids:
        return 0, 0
    keep: list[dict] = []
    quar: list[dict] = []
    with path.open() as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row["instance_id"] in bad_ids:
                quar.append(row)
            else:
                keep.append(row)
    backup = QUAR / rel(path)
    backup.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and not backup.is_file():
        shutil.copy2(path, backup)
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in keep) + ("\n" if keep else ""))
    quar_path = quarantine_sidecar(rel(path))
    quar_path.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict] = []
    if quar_path.is_file():
        existing = [json.loads(line) for line in quar_path.open() if line.strip()]
    merged = {r["instance_id"]: r for r in existing}
    for r in quar:
        merged[r["instance_id"]] = r
    quar_path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in merged.values()) + ("\n" if merged else "")
    )
    return len(keep), len(quar)


def format_breakdown(rep: dict) -> str:
    parts = []
    for item in rep["by_model"]:
        parts.append(f"{item['model']} @ {item['provider']}: {item['rows']}")
    return "; ".join(parts) if parts else "—"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--quarantine",
        action="store_true",
        help="Remove bad rows from live files (default: report only)",
    )
    args = parser.parse_args()

    reports = []
    quarantine_this_run: list[dict] = []
    for path in iter_score_files():
        name = path.name
        if name not in AUDIT_VERIFIERS:
            continue
        vkey = AUDIT_VERIFIERS[name]
        if vkey not in REG["verifiers"]:
            continue
        rep = audit_file(path, vkey)
        reports.append(rep)
        if args.quarantine and rep["bad_ids"]:
            kept, nq = quarantine_file(path, set(rep["bad_ids"]))
            rep["quarantined_cumulative"] = count_quarantined(rep["path"])
            quarantine_this_run.append(
                {"path": rep["path"], "quarantined_now": nq, "kept": kept}
            )

    reg_pins = ", ".join(
        f"**{k}** → `{v['openrouter_model']}` @ {v.get('provider') or '—'}"
        for k, v in REG["verifiers"].items()
    )
    lines = [
        "# OpenRouter model audit (V1 / V4 / V1b / V5)",
        "",
        f"Registry: `notes/openrouter_verifiers.json`. Pins: {reg_pins}.",
        f"Quarantine dir: `{QUAR.relative_to(ROOT)}`.",
        "",
        "**#re-scored** = rows with `api_model` matching registry (post-assert scoring). "
        "**#quarantined** = cumulative rows in `.quarantined.jsonl` sidecars (removed from live file).",
        "",
        "**T6-B / T12:** not in this registry yet — audit extension pending.",
        "",
        "| File | Verifier | Rows | Model @ provider (counts) | #re-scored | #wrong | #unlogged | #quarantined |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for rep in reports:
        lines.append(
            f"| `{rep['path']}` | {rep['verifier']} | {rep['total']} | "
            f"{format_breakdown(rep)} | {rep['registry_ok']} | {rep['wrong_model']} | "
            f"{rep['unlogged']} | {rep['quarantined_cumulative']} |"
        )

    if quarantine_this_run:
        lines += ["", "## Quarantine actions (this run)", ""]
        for q in quarantine_this_run:
            lines.append(f"- `{q['path']}`: **{q['quarantined_now']}** rows removed ({q['kept']} kept)")

    out_md = ROOT / "notes/openrouter_model_audit.md"
    out_json = ROOT / "notes/openrouter_model_audit.json"
    out_md.write_text("\n".join(lines) + "\n")
    out_json.write_text(
        json.dumps({"reports": reports, "quarantine_this_run": quarantine_this_run}, indent=2) + "\n"
    )
    print(out_md)
    print(json.dumps({"files": len(reports)}, indent=2))


if __name__ == "__main__":
    main()
