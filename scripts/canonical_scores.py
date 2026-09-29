"""Pick canonical score JSONL paths (HPC vs node30) for paper metrics."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from verifier_labels import CANONICAL_VERIFIERS, DISPLAY_NAME  # noqa: E402

CANONICAL_TSV = ROOT / "release/canonical_sources.tsv"
V4_LLAMA_ONLY = "v4_ragas_nli.llama.jsonl"

OPENROUTER_VERIFIERS = frozenset(
    {"v1_medscore", "v1b_medscore", "v1c_medscore", "v4_ragas_nli", "v5_ragas_nli"}
    | {v for v in CANONICAL_VERIFIERS if v.startswith("v6_")}
)

LOCAL_CPU_VERIFIERS = frozenset(
    {"v2a_minicheck", "v3_alignscore", "v2b_bespoke"}
    | {v for v in CANONICAL_VERIFIERS if v.startswith("t6a_")}
)

SCORE_DENY_BASENAMES = frozenset({"v4_ragas_nli.jsonl"})
SCORE_DENY_GLOBS = ("**/_quarantine/**", "**/*.legacy.jsonl", "**/*.quarantined.jsonl")

# pack_id -> list of directory suffixes under each score root ("" = root jsonls)
PACK_SCORE_DIRS: dict[str, list[str]] = {
    "main_dose": [""],
    "pol": [""],
    "cpu_early": [""],
    "m1_before": [""],
    "m1_after": [""],  # HPC raw_m1 only
    "t7": ["t7"],
    "t14": ["t14"],
    "t17": ["t17"],
    "t3": ["t3", "t3_t2", "t3_t6b"],
    "e2": ["e2_main"],
}

PACK_INSTANCES: dict[str, tuple[str, str]] = {
    "main_dose": ("data/v3/instances_main.jsonl", "main_dose"),
    "pol": ("data/v3/instances_main.jsonl", "pol"),
    "cpu_early": ("data/v3/instances_cpu_early.jsonl", "cpu_early"),
    "m1_before": ("data/v3/instances_cpu_early.jsonl", "cpu_early"),
    "m1_after": ("data/v3/instances_cpu_early.jsonl", "cpu_early"),
    "t7": ("data/t7/instances_e1_unit.jsonl", "t7"),
    "t14": ("data/t14/instances_t14.jsonl", "t14"),
    "t17": ("data/v3/t17_downdose.jsonl", "t17"),
    "t3": ("data/t3/instances_inv_families.jsonl", "t3"),
    "e2": ("data/v3/instances_main.jsonl", "main_dose"),
}

SCORE_ROOTS: dict[str, Path] = {
    "hpc_raw": ROOT / "results/raw",
    "hpc_m1": ROOT / "results/raw_m1",
    "node30": ROOT / "results/raw_node30",
}


def score_basename(verifier: str) -> str:
    if verifier == "v2b_bespoke":
        return "t6_bespoke_minicheck"
    if verifier.startswith("t6a_"):
        return verifier.replace("t6a_", "t6_", 1)
    return verifier


def score_filename(verifier: str) -> str:
    if verifier == "v4_ragas_nli":
        return V4_LLAMA_ONLY
    return f"{score_basename(verifier)}.jsonl"


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


def candidate_path(root_key: str, dir_suffix: str, verifier: str) -> Path | None:
    if root_key == "hpc_m1":
        base = SCORE_ROOTS["hpc_m1"]
        rel_dir = Path(dir_suffix) if dir_suffix else Path(".")
    elif root_key == "node30":
        base = SCORE_ROOTS["node30"]
        rel_dir = Path(dir_suffix) if dir_suffix else Path(".")
    else:
        base = SCORE_ROOTS["hpc_raw"]
        rel_dir = Path(dir_suffix) if dir_suffix else Path(".")
    path = base / rel_dir / score_filename(verifier)
    if path.is_file() and _score_file_allowed(path):
        return path
    return None


def _load_jsonl_verdicts(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    with path.open() as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            iid = row.get("instance_id")
            if iid:
                out[iid] = row.get("verdict")
    return out


def _required_instance_ids(pack_id: str) -> set[str]:
    """Instance ids used by compute_paper_numbers join (approx: valid rows in pack file)."""
    inst_rel, filter_key = PACK_INSTANCES[pack_id]
    path = ROOT / inst_rel
    if not path.is_file():
        return set()
    sys.path.insert(0, str(ROOT / "analysis"))
    sys.path.insert(0, str(ROOT / "src"))
    from analyze import read_jsonl  # noqa: E402
    from non_dose_targets import invalidate_non_dose_row  # noqa: E402
    from review_filters import analysis_keep_row  # noqa: E402

    filters = {
        "main_dose": lambda r: r.get("type") == "DOSE" and r.get("subset") == "main",
        "pol": lambda r: r.get("type") == "POLARITY",
        "cpu_early": lambda r: True,
        "t7": lambda r: True,
        "t14": lambda r: True,
        "t17": lambda r: True,
        "t3": lambda r: True,
    }
    filt = filters.get(filter_key, lambda r: True)
    out: set[str] = set()
    for r in read_jsonl(path):
        r = dict(r)
        invalidate_non_dose_row(r)
        if not r.get("valid", True):
            continue
        if not analysis_keep_row(r):
            continue
        if filt(r):
            out.add(r["instance_id"])
    return out


def _overlap_agreement(a: dict[str, str], b: dict[str, str]) -> tuple[int, float | None]:
    common = set(a) & set(b)
    if not common:
        return 0, None
    agree = sum(1 for i in common if a[i] == b[i])
    return len(common), agree / len(common)


def pick_canonical_path(pack_id: str, verifier: str, dir_suffix: str) -> tuple[Path | None, str]:
    hpc_key = "hpc_m1" if pack_id == "m1_after" else "hpc_raw"
    hpc = candidate_path(hpc_key, dir_suffix, verifier)
    n30 = None if pack_id == "m1_after" else candidate_path("node30", dir_suffix, verifier)

    if verifier in OPENROUTER_VERIFIERS:
        if hpc:
            return hpc, "API/OpenRouter verifier: HPC results/raw (authoritative)."
        return None, "missing HPC API scores"

    if verifier not in LOCAL_CPU_VERIFIERS:
        if hpc:
            return hpc, "default HPC"
        return n30, "node30 fallback" if n30 else "missing"

    required = _required_instance_ids(pack_id) if dir_suffix == "" else set()
    # Subdir packs: coverage = rows present for any instance in file vs pack file is global;
    # use row count heuristic when required set is for whole pack (t7/t14 use subdir only).
    if dir_suffix:
        required = set()

    if pack_id == "pol" and dir_suffix == "":
        if n30:
            return n30, (
                "POL flip-ok pending rows (42) merged into node30 root encoders at "
                "node30-results@c48093b; no separate pol* score files on branch."
            )
        return hpc, "node30 POL encoder missing; HPC fallback (incomplete POL)"

    if hpc and n30 and verifier in ("v2a_minicheck", "v3_alignscore"):
        hv = _load_jsonl_verdicts(hpc)
        nv = _load_jsonl_verdicts(n30)
        if required:
            h_cov = len(required & set(hv))
            n_cov = len(required & set(nv))
        else:
            h_cov, n_cov = len(hv), len(nv)
        overlap_n, agr = _overlap_agreement(hv, nv)
        agr_s = f"{agr:.4f}" if agr is not None else "n/a"
        if n_cov > h_cov:
            return (
                n30,
                f"node30 encoder has fuller pack coverage ({n_cov} vs HPC={h_cov} required ids); "
                f"overlap verdict agreement={agr_s} on n={overlap_n}.",
            )
        if h_cov > n_cov and hpc:
            return (
                hpc,
                f"HPC fuller pack coverage ({h_cov} vs node30={n_cov}); "
                f"overlap verdict agreement={agr_s} on n={overlap_n}.",
            )
        if hpc:
            return (
                hpc,
                f"equal/full coverage on HPC ({h_cov} required ids); "
                f"overlap verdict agreement={agr_s} on n={overlap_n}.",
            )

    if hpc and not n30:
        return hpc, "HPC-only pack path"
    if n30 and not hpc:
        return n30, "node30-only local verifier scores"
    if hpc:
        return hpc, "prefer HPC when both exist"
    return n30, "node30 fallback"


def build_canonical_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    verifiers = [v for v in CANONICAL_VERIFIERS if v in DISPLAY_NAME]
    for pack_id, dir_suffixes in PACK_SCORE_DIRS.items():
        inst_rel, _ = PACK_INSTANCES.get(pack_id, ("", ""))
        if inst_rel and not (ROOT / inst_rel).is_file():
            continue
        for verifier in verifiers:
            for suffix in dir_suffixes:
                path, reason = pick_canonical_path(pack_id, verifier, suffix)
                if not path:
                    continue
                overlap_n = ""
                overlap_agr = ""
                if verifier in ("v2a_minicheck", "v3_alignscore"):
                    hpc_key = "hpc_m1" if pack_id == "m1_after" else "hpc_raw"
                    hpc = candidate_path(hpc_key, suffix, verifier)
                    n30 = candidate_path("node30", suffix, verifier)
                    if hpc and n30 and hpc != n30:
                        n, agr = _overlap_agreement(
                            _load_jsonl_verdicts(hpc), _load_jsonl_verdicts(n30)
                        )
                        overlap_n = str(n)
                        overlap_agr = f"{agr:.6f}" if agr is not None else ""
                rows.append(
                    {
                        "verifier": verifier,
                        "pack_id": pack_id,
                        "score_path": path.relative_to(ROOT).as_posix(),
                        "reason": reason,
                        "overlap_n": overlap_n,
                        "overlap_agreement": overlap_agr,
                    }
                )
    return rows


def write_canonical_tsv(path: Path | None = None) -> Path:
    out = path or CANONICAL_TSV
    rows = build_canonical_rows()
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "verifier",
        "pack_id",
        "score_path",
        "reason",
        "overlap_n",
        "overlap_agreement",
    ]
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return out


def load_canonical_paths() -> dict[tuple[str, str], list[Path]]:
    """Map (pack_id, verifier) -> ordered list of score files (from canonical_sources.tsv only)."""
    tsv = CANONICAL_TSV
    if not tsv.is_file():
        write_canonical_tsv(tsv)
    grouped: dict[tuple[str, str], list[Path]] = defaultdict(list)
    with tsv.open() as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            key = (row["pack_id"], row["verifier"])
            path = ROOT / row["score_path"]
            if path.is_file():
                grouped[key].append(path)
    return grouped


if __name__ == "__main__":
    p = write_canonical_tsv()
    print(json.dumps({"canonical_tsv": str(p), "rows": sum(1 for _ in p.open()) - 1}))
