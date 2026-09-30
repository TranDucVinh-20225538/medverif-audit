#!/usr/bin/env python3
"""Build cpuverif rescoring chunks for every MiniCheck score file cited in qvc/paper_numbers.json
whose env is unrecorded (raw_node30, results/raw top level, e2_main, t7, raw_m1)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from build_m1_pending_node30 import m1_enrich  # noqa: E402

OUT = ROOT / "data/minicheck_cpuverif_chunks"
CHUNK = 100

CHECKER_FILES = {
    "t6a_minicheck_roberta": "t6_minicheck_roberta.jsonl",
    "t6a_minicheck_deberta": "t6_minicheck_deberta.jsonl",
    "v2a_minicheck": "v2a_minicheck.jsonl",
}
GROUP_DIRS = {
    "main": ("results/raw_node30", "results/raw", "results/raw/e2_main"),
    "t7": ("results/raw/t7", "results/raw_node30/t7"),
    "m1": ("results/raw_m1",),
    "t3": ("results/raw/t3", "results/raw_node30/t3"),
    "t4_eco": ("results/raw/t4_eco", "results/raw_node30/t4_eco"),
    "t4c_eco": ("results/raw/t4c_eco", "results/raw_node30/t4c_eco"),
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def ids_in(paths: list[Path]) -> set[str]:
    out: set[str] = set()
    for p in paths:
        if p.is_file():
            out.update(r["instance_id"] for r in read_jsonl(p))
    return out


PROBE_CHECKERS = {
    "t6a_alignscore_base": ("t6_alignscore_base.jsonl", "cpuverif"),
    "v3_alignscore": ("v3_alignscore.jsonl", "cpuverif"),
    "t6a_hhem": ("t6_hhem.jsonl", "cpuverif"),
    "t6a_granite_guardian": ("t6_granite_guardian.jsonl", "cpuverif"),
    "t6a_summac_zs": ("t6_summac_zs.jsonl", "cpuverif_legacy"),
    "t6a_summac_conv": ("t6_summac_conv.jsonl", "cpuverif_legacy"),
}
N_PROBE = 30
SEED = 42


def build_probe(pool: dict, t7: dict, cpu: dict) -> None:
    """30-row sampled agreement probe per (non-MiniCheck local checker, score-file group)."""
    import random

    tasks: list[str] = []
    for cid, (fname, env) in PROBE_CHECKERS.items():
        for group, dirs in GROUP_DIRS.items():
            ids = ids_in([ROOT / d / fname for d in dirs])
            src = {"main": pool, "t7": t7, "m1": cpu}[group]
            cand = sorted(i for i in ids if i in src)
            if not cand:
                continue
            pick = random.Random(SEED).sample(cand, min(N_PROBE, len(cand)))
            rows = [m1_enrich(src[i]) if group == "m1" else src[i] for i in pick]
            name = f"probe__{cid}__{group}"
            with (OUT / f"{name}.jsonl").open("w") as fh:
                for r in rows:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            tasks.append(f"{cid} {name} {env}")
    (OUT / "tasks_probe.txt").write_text("\n".join(tasks) + "\n")
    print(json.dumps({"n_probe_tasks": len(tasks)}))


def main() -> None:
    pool = {r["instance_id"]: r for r in read_jsonl(ROOT / "data/v3/instances_cpu_early.jsonl")}
    pool.update({r["instance_id"]: r for r in read_jsonl(ROOT / "data/v3/instances_main.jsonl")})
    t7 = {r["instance_id"]: r for r in read_jsonl(ROOT / "data/t7/instances_e1_unit.jsonl")}
    cpu = {r["instance_id"]: r for r in read_jsonl(ROOT / "data/v3/instances_cpu_early.jsonl")}
    OUT.mkdir(parents=True, exist_ok=True)
    if "--probe" in sys.argv:
        build_probe(pool, t7, cpu)
        return
    tasks: list[str] = []
    summary: dict[str, dict[str, int]] = {}
    for cid, fname in CHECKER_FILES.items():
        for group, dirs in GROUP_DIRS.items():
            ids = ids_in([ROOT / d / fname for d in dirs])
            if group == "main":
                rows = [pool[i] for i in sorted(ids) if i in pool]
            elif group == "t7":
                rows = [t7[i] for i in sorted(ids) if i in t7]
            else:
                rows = [m1_enrich(cpu[i]) for i in sorted(ids) if i in cpu]
            if not rows:
                continue
            summary.setdefault(cid, {})[group] = len(rows)
            for k in range(0, len(rows), CHUNK):
                name = f"{cid}__{group}__{k // CHUNK:03d}"
                with (OUT / f"{name}.jsonl").open("w") as fh:
                    for r in rows[k : k + CHUNK]:
                        fh.write(json.dumps(r, ensure_ascii=False) + "\n")
                tasks.append(f"{cid} {name}")
    (OUT / "tasks.txt").write_text("\n".join(tasks) + "\n")
    print(json.dumps({"n_tasks": len(tasks), "rows": summary}, indent=1))


if __name__ == "__main__":
    main()
