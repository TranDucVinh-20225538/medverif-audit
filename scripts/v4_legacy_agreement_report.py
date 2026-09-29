#!/usr/bin/env python3
"""Legacy vs Llama V4 verdict agreement (overall + by condition)."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from analyze import read_jsonl  # noqa: E402

MANIFEST = ROOT / "notes/v4_llama_rescore_packs.json"
OUT_MD = ROOT / "notes/v4_legacy_llama_agreement.md"
OUT_JSON = ROOT / "notes/v4_legacy_llama_agreement.json"
VERIFIER = "v4_ragas_nli"
INST_CACHE: dict[str, dict[str, dict]] = {}


def inst_map(path: Path) -> dict[str, dict]:
    key = str(path)
    if key not in INST_CACHE:
        INST_CACHE[key] = {r["instance_id"]: r for r in read_jsonl(path) if r.get("instance_id")}
    return INST_CACHE[key]


def load_verdicts(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    out = {}
    for row in read_jsonl(path):
        v = row.get("verdict")
        if v and v != "PARSE_FAIL":
            out[row["instance_id"]] = v
    return out


def agreement(legacy: dict[str, str], llama: dict[str, str]) -> dict:
    ids = sorted(set(legacy) & set(llama))
    if not ids:
        return {"n": 0, "agree": 0, "rate": None}
    agree = sum(legacy[i] == llama[i] for i in ids)
    return {"n": len(ids), "agree": agree, "rate": agree / len(ids)}


def main() -> None:
    data = json.loads(MANIFEST.read_text())
    rows = []
    for pack in data["packs"]:
        score_dir = ROOT / pack["score_dir"]
        legacy_p = score_dir / f"{VERIFIER}.legacy.jsonl"
        llama_p = score_dir / f"{VERIFIER}.llama.jsonl"
        inst_p = ROOT / pack["instances"]
        leg = load_verdicts(legacy_p)
        lla = load_verdicts(llama_p)
        overall = agreement(leg, lla)
        by_cond: dict[str, dict] = {}
        im = inst_map(inst_p) if inst_p.is_file() else {}
        cond_legacy: dict[str, dict[str, str]] = defaultdict(dict)
        cond_llama: dict[str, dict[str, str]] = defaultdict(dict)
        for iid, v in leg.items():
            c = (im.get(iid) or {}).get("condition") or "unknown"
            cond_legacy[c][iid] = v
        for iid, v in lla.items():
            c = (im.get(iid) or {}).get("condition") or "unknown"
            cond_llama[c][iid] = v
        for c in sorted(set(cond_legacy) | set(cond_llama)):
            by_cond[c] = agreement(cond_legacy[c], cond_llama[c])
        row = {
            "pack": pack["id"],
            "legacy_path": str(legacy_p.relative_to(ROOT)),
            "llama_path": str(llama_p.relative_to(ROOT)),
            "overall": overall,
            "by_condition": by_cond,
            "legacy_llama_note": overall["rate"] is not None and overall["rate"] >= 0.95,
        }
        rows.append(row)

    lines = [
        "# V4 legacy vs Llama-3.3-70B agreement",
        "",
        "Legacy = `*.legacy.jsonl`; new provenance = `*.llama.jsonl`. "
        "Agreement ≥95% supports treating legacy as same Llama policy (still use `.llama` for analysis).",
        "",
        "| Pack | n | agree | rate | ≥95% legacy≈Llama |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for r in rows:
        o = r["overall"]
        rate = "—" if o["rate"] is None else f"{100 * o['rate']:.1f}%"
        flag = "yes" if r["legacy_llama_note"] else "no" if o["rate"] is not None else "—"
        lines.append(f"| {r['pack']} | {o['n']} | {o['agree']} | {rate} | {flag} |")
    lines.append("")
    for r in rows:
        lines.append(f"## {r['pack']}")
        for c, st in sorted(r["by_condition"].items()):
            if st["n"] == 0:
                continue
            lines.append(
                f"- **{c}**: {st['agree']}/{st['n']} ({100 * st['rate']:.1f}%)"
                if st["rate"] is not None
                else f"- **{c}**: —"
            )
        lines.append("")

    OUT_MD.write_text("\n".join(lines) + "\n")
    OUT_JSON.write_text(json.dumps({"packs": rows}, indent=2) + "\n")
    print(OUT_MD)


if __name__ == "__main__":
    main()
