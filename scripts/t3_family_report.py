#!/usr/bin/env python3
"""T3 INV frequency/route (PI_ok=Y): pass rates per family and verifier."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.append(str(ROOT / "scripts"))
from canonical_scores import reference_env_rows  # noqa: E402

from analyze import _c0_pass_bases, _parsed  # noqa: E402

T3_PATHS = (
    ROOT / "data/v3/instances_inv_families.jsonl",
    ROOT / "data/t3/instances_inv_families.jsonl",
)
CPU = ROOT / "data/v3/instances_cpu_early.jsonl"
LABELS = ROOT / "qc/inv_claim_PI_ok_labels.csv"
OUT = ROOT / "results/tables/t3_family_pass.md"
OUT_JSON = ROOT / "notes/t3_family_pass.json"
T6A = ROOT / "notes/t6a_eco_checkers.json"

# Pack-specific score roots (first hit wins within each root, later roots override).
VERIFIER_DIRS: dict[str, list[Path]] = {
    "v2a_minicheck": [ROOT / "results/raw/t3", ROOT / "results/raw"],
    "v3_alignscore": [ROOT / "results/raw/t3", ROOT / "results/raw"],
    "v1b_medscore": [ROOT / "results/raw/t3_t2"],
    "v5_ragas_nli": [ROOT / "results/raw/t3_t2"],
    "v1_medscore": [
        ROOT / "results/raw/t3",
        ROOT / "results/raw/t3_t2",
        ROOT / "results/raw/e2_main",
        ROOT / "results/raw",
    ],
    "v4_ragas_nli": [
        ROOT / "results/raw/t3",
        ROOT / "results/raw/e2_main",
        ROOT / "results/raw/t4_eco",
        ROOT / "results/raw/t4c_eco",
        ROOT / "results/raw",
    ],
    "v1c_medscore": [
        ROOT / "results/raw/t3_t6b",
        ROOT / "results/raw/t6b/full",
        ROOT / "results/raw/e2_main",
        ROOT / "results/raw/t4_eco",
    ],
    "v6_ragas_gpt4o_mini": [
        ROOT / "results/raw/t3_t6b",
        ROOT / "results/raw/t6b/full",
        ROOT / "results/raw/e2_main",
    ],
    "v6_ragas_haiku45": [
        ROOT / "results/raw/t3_t6b",
        ROOT / "results/raw/t6b/full",
        ROOT / "results/raw/e2_main",
    ],
    "v6_ragas_llama31_8b": [
        ROOT / "results/raw/t3_t6b",
        ROOT / "results/raw/t6b/full",
        ROOT / "results/raw/e2_main",
    ],
    "v6_ragas_mistral_small32": [
        ROOT / "results/raw/t3_t6b",
        ROOT / "results/raw/t6b/full",
        ROOT / "results/raw/e2_main",
    ],
    "v6_ragas_nli": [
        ROOT / "results/raw/t3_t6b",
        ROOT / "results/raw/t6b/full",
        ROOT / "results/raw/t4_eco",
        ROOT / "results/raw/t4c_eco",
    ],
    "v2b_bespoke": [ROOT / "results/raw/t3", ROOT / "results/raw"],
}
DEFAULT_DIRS = [
    ROOT / "results/raw/t3",
    ROOT / "results/raw/e2_main",
    ROOT / "results/raw/t6b/full",
    ROOT / "results/raw/t2_full",
    ROOT / "results/raw/t7",
    ROOT / "results/raw",
]


def _score_paths(slug: str, root: Path) -> list[Path]:
    out: list[Path] = []
    if slug == "v2b_bespoke":
        for name in ("t6_bespoke_minicheck.jsonl", "v2b_bespoke.jsonl"):
            p = root / name
            if p.is_file():
                out.append(p)
    if T6A.is_file():
        t6a = {c["id"]: c["jsonl"] for c in json.loads(T6A.read_text()).get("checkers", [])}
        fname = t6a.get(slug)
        if fname and (root / fname).is_file():
            out.append(root / fname)
    for name in (f"{slug}.llama.jsonl", f"{slug}.jsonl"):
        p = root / name
        if p.is_file():
            out.append(p)
    return out


def load_scores(slug: str) -> tuple[dict[str, str], str]:
    """Merge DEFAULT_DIRS (C0 / legacy) then pack-specific dirs (override on overlap)."""
    primary = VERIFIER_DIRS.get(slug)
    if primary:
        dirs = list(DEFAULT_DIRS) + list(primary)
    else:
        dirs = list(DEFAULT_DIRS)
    m: dict[str, str] = {}
    used: list[str] = []
    for d in dirs:
        for path in _score_paths(slug, d):
            rel = str(path.relative_to(ROOT))
            if rel not in used:
                used.append(rel)
            for rec in reference_env_rows(path):
                m[rec["instance_id"]] = rec.get("verdict") or ""
    pack_used: list[str] = []
    if primary:
        for d in primary:
            for path in _score_paths(slug, d):
                if not path.is_file():
                    continue
                rel = str(path.relative_to(ROOT))
                if rel not in pack_used:
                    pack_used.append(rel)
    src = ", ".join(pack_used) if pack_used else ", ".join(used) if used else "(none)"
    return m, src


def pi_ok_rows() -> tuple[dict[str, str], list[dict]]:
    fam: dict[str, str] = {}
    for row in csv.DictReader(LABELS.open()):
        if (row.get("PI_ok") or "").strip().upper() != "Y":
            continue
        if (row.get("family") or "").strip() not in ("inv_frequency", "inv_route"):
            continue
        fam[row["instance_id"].strip()] = row["family"].strip()
    by_id: dict[str, dict] = {}
    for path in T3_PATHS:
        if not path.is_file():
            continue
        for line in path.open():
            if not line.strip():
                continue
            row = json.loads(line)
            if row["instance_id"] not in fam:
                continue
            by_id.setdefault(row["instance_id"], row)
    inst = []
    for iid, family in sorted(fam.items()):
        row = by_id.get(iid)
        if not row or not row.get("valid", True):
            continue
        row = dict(row)
        row["family"] = family
        inst.append(row)
    return fam, inst


VERIFIERS = tuple(VERIFIER_DIRS.keys()) + tuple(
    c["id"]
    for c in (json.loads(T6A.read_text()).get("checkers", []) if T6A.is_file() else [])
    if c["id"] not in VERIFIER_DIRS
)


def main() -> None:
    label_ids, inst = pi_ok_rows()
    lines = [
        "# T3 encoder families (PI_ok=Y, valid)",
        "",
        f"- Label ids (freq/route): **{len(label_ids)}**; instances in pack: **{len(inst)}**",
        "- Scores resolved per verifier from pack-specific paths (see JSON `score_paths`).",
        "",
        "| Verifier | Family | PASS | n |",
        "|---|---|---:|---:|",
    ]
    payload: dict = {
        "pi_ok_label_ids": len(label_ids),
        "instances_scored": len(inst),
        "score_paths": {},
        "by_verifier": {},
    }

    bases = {r["base_id"] for r in inst}
    c0_rows = []
    for line in CPU.open():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("valid", True) and row.get("condition") == "C0" and row["base_id"] in bases:
            c0_rows.append(row)

    seen_v: set[str] = set()
    for v in VERIFIERS:
        if v in seen_v:
            continue
        seen_v.add(v)
        sc, src = load_scores(v)
        payload["score_paths"][v] = src
        joined = []
        for row in c0_rows + inst:
            verdict = sc.get(row["instance_id"])
            if not verdict:
                continue
            j = dict(row)
            j["verifier"] = v
            j["verdict"] = verdict
            joined.append(j)
        c0_pass = _c0_pass_bases(joined)
        vdata: dict[str, dict] = {}
        for fam in ("inv_frequency", "inv_route"):
            parsed = [
                r
                for r in joined
                if r.get("family") == fam
                and r["base_id"] in c0_pass
                and _parsed(r)
            ]
            n = len(parsed)
            p = sum(r["verdict"] == "PASS" for r in parsed)
            vdata[fam] = {"pass": p, "n": n}
            lines.append(f"| {v} | {fam} | {p} | {n} |")
        payload["by_verifier"][v] = vdata

    lines.extend(["", "## Score path hints", ""])
    for v, src in sorted(payload["score_paths"].items()):
        lines.append(f"- **{v}**: `{src}`")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
