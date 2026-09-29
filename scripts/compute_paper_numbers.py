#!/usr/bin/env python3
"""Canonical paper numbers: scores from results/raw only (+ data/qc), with exclusions."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import (  # noqa: E402
    N_BOOT,
    SEED,
    _c0_pass_bases,
    _groups,
    _parsed,
    bootstrap_rate,
    read_jsonl,
)
from non_dose_targets import invalidate_non_dose_row  # noqa: E402
from review_filters import (  # noqa: E402
    analysis_keep_row,
    effective_unit_natural_y,
    inv_mechanism,
)
from text_utils import rule_natural_unit_conversion_label  # noqa: E402
from t14_t3_filter_report import inv_span_before  # noqa: E402
from verifier_labels import CANONICAL_VERIFIERS, DISPLAY_NAME  # noqa: E402

OUT_JSON = ROOT / "qvc/paper_numbers.json"
OUT_CARD = ROOT / "results/tables/card_main.md"
OUT_M1 = ROOT / "results/tables/m1_before_after.md"

# Hard denylist: never load these score files (Qwen V4 local / drift / legacy sidecars).
SCORE_DENY_BASENAMES = frozenset(
    {
        "v4_ragas_nli.jsonl",
    }
)
SCORE_DENY_GLOBS = (
    "**/_quarantine/**",
    "**/*.legacy.jsonl",
    "**/*.quarantined.jsonl",
)

V4_LLAMA_ONLY = "v4_ragas_nli.llama.jsonl"

OPENROUTER_VERIFIERS = frozenset(
    {"v1_medscore", "v1b_medscore", "v1c_medscore", "v4_ragas_nli", "v5_ragas_nli"}
    | {v for v in CANONICAL_VERIFIERS if v.startswith("v6_")}
)


def _score_file_allowed(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    for pat in SCORE_DENY_GLOBS:
        if fnmatch(rel, pat):
            return False
    if path.name in SCORE_DENY_BASENAMES:
        return False
    if path.name.startswith("v4_ragas_nli") and path.name != V4_LLAMA_ONLY:
        return False
    return True


def quarantined_instance_ids() -> set[str]:
    out: set[str] = set()
    qroot = ROOT / "results/raw/_quarantine"
    if not qroot.is_dir():
        return out
    for path in qroot.rglob("*.quarantined.jsonl"):
        for line in path.open():
            if line.strip():
                out.add(json.loads(line)["instance_id"])
    return out


def load_score_jsonl(path: Path, quarantine_ids: set[str]) -> dict[str, dict]:
    if not _score_file_allowed(path):
        return {}
    out: dict[str, dict] = {}
    with path.open() as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            iid = row.get("instance_id")
            if not iid or iid in quarantine_ids:
                continue
            if row.get("verifier") in OPENROUTER_VERIFIERS or path.name.startswith(
                ("v1", "v4", "v5", "v6")
            ):
                if not row.get("api_model"):
                    continue
            out[iid] = row
    return out


def score_paths_for_pack(pack_id: str, verifier: str) -> list[Path]:
    dirs: list[Path] = []
    if pack_id in ("main_dose", "pol", "cpu_early"):
        dirs.append(ROOT / "results/raw")
    if pack_id == "m1_before":
        dirs.append(ROOT / "results/raw")
    if pack_id == "m1_after":
        dirs.append(ROOT / "results/raw_m1")
    if pack_id == "t7":
        dirs.append(ROOT / "results/raw/t7")
    if pack_id == "t14":
        dirs.append(ROOT / "results/raw/t14")
    if pack_id == "t17":
        dirs.append(ROOT / "results/raw/t17")
    if pack_id == "t3":
        for sub in ("t3", "t3_t2", "t3_t6b"):
            d = ROOT / "results/raw" / sub
            if d.is_dir():
                dirs.append(d)
    if pack_id == "e2":
        dirs.append(ROOT / "results/raw/e2_main")
    paths: list[Path] = []
    for d in dirs:
        if not d.is_dir():
            continue
        if verifier == "v4_ragas_nli":
            cand = d / V4_LLAMA_ONLY
            if cand.is_file():
                paths.append(cand)
            continue
        for name in (f"{verifier}.llama.jsonl", f"{verifier}.jsonl"):
            cand = d / name
            if cand.is_file() and _score_file_allowed(cand):
                paths.append(cand)
                break
    return paths


def merged_scores(pack_id: str, verifier: str, quarantine_ids: set[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in score_paths_for_pack(pack_id, verifier):
        out.update(load_score_jsonl(path, quarantine_ids))
    return out


def load_pack_instances(rel_path: str) -> list[dict]:
    rows = read_jsonl(ROOT / rel_path)
    out = []
    for r in rows:
        r = dict(r)
        invalidate_non_dose_row(r)
        if not r.get("valid", True):
            continue
        if not analysis_keep_row(r):
            continue
        out.append(r)
    return out


PACKS: list[dict] = [
    {
        "id": "main_dose",
        "label": "Main DOSE",
        "instances": "data/v3/instances_main.jsonl",
        "filter": lambda r: r.get("type") == "DOSE" and r.get("subset") == "main",
    },
    {
        "id": "pol",
        "label": "POL flip",
        "instances": "data/v3/instances_main.jsonl",
        "filter": lambda r: r.get("type") == "POLARITY",
    },
    {
        "id": "cpu_early",
        "label": "CPU early (M1 cohort)",
        "instances": "data/v3/instances_cpu_early.jsonl",
        "filter": lambda r: True,
    },
    {
        "id": "t7",
        "label": "T7 E1-unit",
        "instances": "data/t7/instances_e1_unit.jsonl",
        "filter": lambda r: True,
    },
    {
        "id": "t14",
        "label": "T14 repr families",
        "instances": "data/t14/instances_t14.jsonl",
        "filter": lambda r: True,
    },
    {
        "id": "t17",
        "label": "T17 down-dose",
        "instances": "data/v3/t17_downdose.jsonl",
        "filter": lambda r: True,
    },
    {
        "id": "t3",
        "label": "T3 INV families",
        "instances": "data/t3/instances_inv_families.jsonl",
        "filter": lambda r: True,
    },
    {
        "id": "e2",
        "label": "E2 main",
        "instances": "data/v3/instances_main.jsonl",
        "filter": lambda r: r.get("type") == "DOSE" and r.get("subset") == "main",
    },
]


def join_pack(pack: dict, verifier: str, scores: dict[str, dict]) -> list[dict]:
    filt = pack["filter"]
    joined = []
    for inst in load_pack_instances(pack["instances"]):
        if not filt(inst):
            continue
        sc = scores.get(inst["instance_id"])
        if not sc:
            continue
        row = dict(inst)
        row["verifier"] = verifier
        row["verdict"] = sc.get("verdict")
        row["score"] = sc.get("score")
        row["api_model"] = sc.get("api_model")
        row["api_provider"] = sc.get("api_provider")
        row["_score_source"] = sc.get("_source_path")
        joined.append(row)
    return joined


def _attach_source(rows: list[dict], path: Path) -> None:
    rel = path.relative_to(ROOT).as_posix()
    for r in rows:
        r["_source_path"] = rel


def metric_entry(
    *,
    metric: str,
    verifier: str,
    pack: dict,
    subset: str,
    conditioning: str,
    stat: dict,
    source_files: list[str],
    extra: dict | None = None,
) -> dict:
    model = DISPLAY_NAME.get(verifier, verifier)
    if extra and extra.get("api_model"):
        model = f"{model} ({extra['api_model']})"
    ent = {
        "metric": metric,
        "verifier_slug": verifier,
        "verifier_model": model,
        "pack": pack["id"],
        "pack_label": pack["label"],
        "subset": subset,
        "conditioning": conditioning,
        "n": stat.get("den", 0),
        "n_bases": stat.get("n_bases", 0),
        "num": stat.get("num", 0),
        "rate": stat.get("rate"),
        "ci95_lo": stat.get("lo"),
        "ci95_hi": stat.get("hi"),
        "bootstrap_n": N_BOOT,
        "bootstrap_seed": SEED,
        "source_instances": pack["instances"],
        "source_scores": sorted(set(source_files)),
        "exclusions": [
            "non_dose_target bases",
            "valid=false",
            "analysis_keep_row (PI_ok INV / POL E1 flip gate)",
            "score denylist (Qwen v4_ragas_nli.jsonl, legacy, quarantine sidecars)",
            "OpenRouter rows without api_model",
            "quarantined instance_ids",
        ],
    }
    if extra:
        ent.update(extra)
    return ent


def compute_metrics(pack: dict, verifier: str, joined: list[dict], sources: list[str]) -> list[dict]:
    if not joined:
        return []
    block = joined
    cond = _c0_pass_bases(block)
    entries: list[dict] = []

    c0_stat = bootstrap_rate(_groups(block, lambda r: r["condition"] == "C0"))
    entries.append(
        metric_entry(
            metric="C0",
            verifier=verifier,
            pack=pack,
            subset="C0 all",
            conditioning="unconditional on C0",
            stat=c0_stat,
            source_files=sources,
        )
    )

    qi_all = bootstrap_rate(
        _groups(
            block,
            lambda r: r["base_id"] in cond
            and r["condition"] == "INV-claim"
            and _parsed(r),
        )
    )
    entries.append(
        metric_entry(
            metric="QI",
            verifier=verifier,
            pack=pack,
            subset="INV-claim all magnitudes",
            conditioning="| C0 PASS",
            stat=qi_all,
            source_files=sources,
            extra={"n_c0_bases": len(cond)},
        )
    )

    def _natural_inv(r: dict) -> bool:
        if r.get("condition") != "INV-claim" or r.get("magnitude") != "unit_conversion":
            return False
        orig = inv_span_before(r)
        return effective_unit_natural_y(
            r["base_id"], bool(rule_natural_unit_conversion_label(orig))
        )

    qi_nat = bootstrap_rate(
        _groups(
            block,
            lambda r: r["base_id"] in cond and _natural_inv(r) and _parsed(r),
        )
    )
    entries.append(
        metric_entry(
            metric="QI",
            verifier=verifier,
            pack=pack,
            subset="INV-unit natural",
            conditioning="| C0 PASS",
            stat=qi_nat,
            source_files=sources,
            extra={"n_c0_bases": len(cond)},
        )
    )

    ns_groups = []
    by: dict[str, list[dict]] = defaultdict(list)
    for r in block:
        if r["base_id"] not in cond or r["condition"] != "E1-evid" or not _parsed(r):
            continue
        by[r["base_id"]].append(r)
    for _, g in by.items():
        ns_groups.append((sum(1 for r in g if r["verdict"] == "FAIL"), len(g)))
    ns_stat = bootstrap_rate(ns_groups)
    entries.append(
        metric_entry(
            metric="NS",
            verifier=verifier,
            pack=pack,
            subset="E1-evid (value perturb evidence)",
            conditioning="| C0 PASS; rate = FAIL",
            stat=ns_stat,
            source_files=sources,
            extra={"n_c0_bases": len(cond)},
        )
    )

    us_groups = []
    by2: dict[str, list[dict]] = defaultdict(list)
    for r in block:
        if r["base_id"] not in cond:
            continue
        if r.get("condition") not in ("E1-unit-claim", "E1-unit-evid", "E1-unit"):
            continue
        if not _parsed(r):
            continue
        by2[r["base_id"]].append(r)
    for _, g in by2.items():
        us_groups.append((sum(1 for r in g if r["verdict"] == "FAIL"), len(g)))
    us_stat = bootstrap_rate(us_groups)
    entries.append(
        metric_entry(
            metric="US",
            verifier=verifier,
            pack=pack,
            subset="E1-unit claim/evid",
            conditioning="| C0 PASS; rate = FAIL",
            stat=us_stat,
            source_files=sources,
            extra={"n_c0_bases": len(cond)},
        )
    )
    return entries


def fmt_stat(stat: dict | None) -> str:
    if not stat or stat.get("rate") is None:
        return "NA"
    num = stat.get("num", 0)
    den = stat.get("n") or stat.get("den") or 0
    if stat.get("ci95_lo") is None and stat.get("lo") is None:
        return f"{stat['rate']:.3f} ({num}/{den})"
    lo = stat.get("ci95_lo", stat.get("lo"))
    hi = stat.get("ci95_hi", stat.get("hi"))
    return f"{stat['rate']:.3f} [{lo:.3f},{hi:.3f}] ({num}/{den})"


def _entry_as_stat(e: dict | None) -> dict | None:
    if not e:
        return None
    return {
        "rate": e.get("rate"),
        "lo": e.get("ci95_lo"),
        "hi": e.get("ci95_hi"),
        "num": e.get("num"),
        "n": e.get("n"),
    }


def write_m1_table(all_entries: list[dict]) -> None:
    lines = [
        "# M1 before / after",
        "",
        "_Generated by `scripts/compute_paper_numbers.py` (canonical). "
        "V4 uses **Llama-3.3-70B** scores only (`v4_ragas_nli.llama.jsonl`)._",
        "",
        "| Verifier | C0 (support) | QI INV pass (|C0) | NS E1-evid FAIL (|C0) | cohort |",
        "| --- | --- | --- | --- | --- |",
    ]
    verifiers = ("v2a_minicheck", "v3_alignscore", "v1_medscore", "v4_ragas_nli")
    labels = {"v2a_minicheck": "V2a", "v3_alignscore": "V3", "v1_medscore": "V1", "v4_ragas_nli": "V4"}
    for cohort, pack_id in (("raw", "m1_before"), ("M1", "m1_after")):
        for v in verifiers:
            pick = {
                e["metric"]: e
                for e in all_entries
                if e["pack"] == pack_id
                and e["verifier_slug"] == v
                and e["subset"] == "INV-claim all magnitudes"
                or (
                    e["pack"] == pack_id
                    and e["verifier_slug"] == v
                    and e["metric"] in ("C0", "NS")
                )
            }
            # rebuild cleanly
            c0 = next(
                (
                    e
                    for e in all_entries
                    if e["pack"] == pack_id
                    and e["verifier_slug"] == v
                    and e["metric"] == "C0"
                ),
                None,
            )
            qi = next(
                (
                    e
                    for e in all_entries
                    if e["pack"] == pack_id
                    and e["verifier_slug"] == v
                    and e["metric"] == "QI"
                    and e["subset"] == "INV-claim all magnitudes"
                ),
                None,
            )
            ns = next(
                (
                    e
                    for e in all_entries
                    if e["pack"] == pack_id
                    and e["verifier_slug"] == v
                    and e["metric"] == "NS"
                ),
                None,
            )
            if not c0 and not qi:
                continue
            lines.append(
                f"| {labels[v]} {cohort} | "
                f"{fmt_stat(_entry_as_stat(c0))} | "
                f"{fmt_stat(_entry_as_stat(qi))} | "
                f"{fmt_stat(_entry_as_stat(ns))} | {cohort} |"
            )
    lines.append("")
    OUT_M1.parent.mkdir(parents=True, exist_ok=True)
    OUT_M1.write_text("\n".join(lines) + "\n")


def write_card(entries: list[dict]) -> None:
    main = [e for e in entries if e["pack"] == "main_dose"]
    lines = [
        "# Quantity Validity Card (main DOSE)",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Canonical pipeline: `scripts/compute_paper_numbers.py`. "
        "Cluster-bootstrap by `base_id`, seed 42, 1000 resamples.",
        "",
        "| Metric | Verifier | Subset | Conditioning | Rate [95% CI] | n | Sources |",
        "| --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for e in sorted(main, key=lambda x: (x["verifier_slug"], x["metric"], x["subset"])):
        rate = e["rate"]
        if rate is None:
            cell = "NA"
        elif e["ci95_lo"] is None:
            cell = f"{rate:.3f}"
        else:
            cell = f"{rate:.3f} [{e['ci95_lo']:.3f}, {e['ci95_hi']:.3f}]"
        src = ", ".join(f"`{s}`" for s in e["source_scores"][:2])
        lines.append(
            f"| **{e['metric']}** | {e['verifier_model']} | {e['subset']} | {e['conditioning']} | "
            f"{cell} | {e['n']} | {src} |"
        )
    lines.append("")
    OUT_CARD.parent.mkdir(parents=True, exist_ok=True)
    OUT_CARD.write_text("\n".join(lines) + "\n")


def mark_legacy_tables() -> None:
    banner = (
        "<!-- LEGACY — not for paper. Use results/tables/card_main.md and "
        "qvc/paper_numbers.json from scripts/compute_paper_numbers.py. -->\n\n"
    )
    for rel in (
        "results/tables/t13_pairwise_preference.md",
        "results/tables/t14_c0_conditional_pass.md",
        "results/tables/t7_m1_mcnemar.md",
        "results/tables/full_v1v4.md",
        "results/tables/prelim_v2v3.md",
    ):
        path = ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text()
        if "LEGACY — not for paper" in text:
            continue
        path.write_text(banner + text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-legacy-mark", action="store_true")
    args = parser.parse_args()

    quarantine_ids = quarantined_instance_ids()
    all_entries: list[dict] = []

    pack_defs = list(PACKS) + [
        {
            "id": "m1_before",
            "label": "M1 before (cpu_early scores)",
            "instances": "data/v3/instances_cpu_early.jsonl",
            "filter": lambda r: True,
        },
        {
            "id": "m1_after",
            "label": "M1 after (raw_m1)",
            "instances": "data/v3/instances_cpu_early.jsonl",
            "filter": lambda r: True,
        },
    ]

    verifiers = [v for v in CANONICAL_VERIFIERS if v in DISPLAY_NAME]

    for pack in pack_defs:
        inst_path = ROOT / pack["instances"]
        if not inst_path.is_file():
            continue
        for verifier in verifiers:
            paths = score_paths_for_pack(pack["id"], verifier)
            if not paths:
                continue
            scores = merged_scores(pack["id"], verifier, quarantine_ids)
            if not scores:
                continue
            joined = join_pack(pack, verifier, scores)
            sources = [p.relative_to(ROOT).as_posix() for p in paths]
            all_entries.extend(compute_metrics(pack, verifier, joined, sources))

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pipeline": "scripts/compute_paper_numbers.py",
        "score_denylist_basenames": sorted(SCORE_DENY_BASENAMES),
        "score_denylist_globs": list(SCORE_DENY_GLOBS),
        "v4_scores_only": V4_LLAMA_ONLY,
        "n_entries": len(all_entries),
        "entries": all_entries,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    write_card(all_entries)
    write_m1_table(all_entries)
    if not args.skip_legacy_mark:
        mark_legacy_tables()
    print(json.dumps({"json": str(OUT_JSON), "card": str(OUT_CARD), "m1": str(OUT_M1), "n": len(all_entries)}))


if __name__ == "__main__":
    main()
