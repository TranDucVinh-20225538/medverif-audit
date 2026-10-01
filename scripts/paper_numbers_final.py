#!/usr/bin/env python3
"""paper_numbers_final.md: every paper number with the env of the score rows behind it.

env is derived per score row, following each table's loader (same directories, same order, last file wins):
  API             row carries api_model / openrouter_model / api_provider
  cpuverif        lane_b_env_profile=cpuverif, or results/raw/{t15_cpuverif,minicheck_cpuverif}
  cpuverif_legacy lane_b_env_profile=legacy
  vllm            results/raw/t15 (GPU env), Bespoke-MiniCheck-7B (GPU bf16; reference env by design)
  nemo            T9 NeMo Guardrails AlignScore rails (reference env by design)
  node30          results/raw_node30 rows without env metadata (covered by agreement checks; HHEM and
                  SummaC-Conv are node30-only main-card numbers, agreement NA, decision M)
  unrecorded      local score file without env metadata
Reference env: cpuverif (SummaC: cpuverif_legacy); API for hosted LLM judges.
Any other env needs an agreement check against the reference env (notes/*agreement*.json).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

import m1_strong_run as m1s  # noqa: E402
import t13_best_of_n_report as t13  # noqa: E402
from canonical_scores import (  # noqa: E402
    _score_file_allowed,
    minicheck_cpuverif_path,
    minicheck_cpuverif_rows,
    score_filename,
)
from t15_card_report import T7, join_extra, join_rows, load_main_dose_instances, metrics_block  # noqa: E402
from verifier_labels import CANONICAL_VERIFIERS, verifier_display_name  # noqa: E402

OUT = ROOT / "paper_numbers_final.md"
OUT_JSON = ROOT / "notes/paper_numbers_final.json"
REFERENCE = {"cpuverif", "API"}
LEGACY_OK = {"t6a_summac_zs", "t6a_summac_conv", "t6_summac_zs", "t6_summac_conv"}
NODE30_ONLY = {"t6a_hhem", "t6a_summac_conv"}
# Author decisions (Oct 1): the supported backend is the reference env for these checkers.
REF_BY_DESIGN = {
    "v2b_bespoke": ("vllm", "reference env = vllm (by design)"),
    "t9": ("nemo", "reference env = nemo (by design)"),
}
SCRIPT = "scripts/paper_numbers_final.py"


def git(*args: str) -> str:
    try:
        return subprocess.check_output(["/usr/bin/git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


HEAD = git("rev-parse", "--short", "HEAD")


@lru_cache(maxsize=None)
def commit_of(rel: str) -> str:
    return git("log", "-1", "--format=%h", "--", rel) or "uncommitted"


# ---------- row env ----------

# Untagged score files whose env is fixed by the job script that wrote them (interpreter path in the sbatch).
JOB_ENV = {
    "results/raw/lane_b/m1_t7_e1_unit_amend5/v2a_minicheck.jsonl": ("cpuverif", "jobs/run_m1_amend5_rescore.sbatch"),
    "results/raw/lane_b/m1_t7_e1_unit_amend5/v3_alignscore.jsonl": ("cpuverif", "jobs/run_m1_amend5_rescore.sbatch"),
    "results/raw/lane_b/m1_t17_unit_down/v2a_minicheck.jsonl": ("cpuverif", "jobs/run_m1_t17_unit_down_after.sbatch"),
    "results/raw/lane_b/m1_t17_unit_down/v3_alignscore.jsonl": ("cpuverif", "jobs/run_m1_t17_unit_down_after.sbatch"),
    "results/raw/t24b/v2a_minicheck.jsonl": ("vllm", "jobs/run_t24b.sbatch"),
    "results/raw/t24b/v3_alignscore.jsonl": ("vllm", "jobs/run_t24b.sbatch"),
    "results/raw/t14/v2a_minicheck.jsonl": ("vllm", "jobs/run_t14_small_checkers.sbatch"),
    "results/raw/t14/v3_alignscore.jsonl": ("vllm", "jobs/run_t14_small_checkers.sbatch"),
}

def row_env(path: Path, row: dict) -> str:
    if row.get("api_model") or row.get("openrouter_model") or row.get("api_provider"):
        return "API"
    prof = row.get("lane_b_env_profile")
    if prof == "cpuverif":
        return "cpuverif"
    if prof in ("legacy", "cpuverif_legacy"):
        return "cpuverif_legacy"
    rel = str(path.relative_to(ROOT))
    if rel in JOB_ENV:
        return JOB_ENV[rel][0]
    if rel.startswith(("results/raw/t15_cpuverif/", "results/raw/minicheck_cpuverif/")):
        return "cpuverif"
    if rel.startswith("results/raw/t15/"):
        return "vllm"
    if "bespoke" in path.name or "bespoke" in str(row.get("model", "")).lower():
        return "vllm"
    if rel.startswith("results/raw/t9/"):
        return "nemo"
    if rel.startswith("results/raw_node30/"):
        return "node30"
    return "unrecorded"


@lru_cache(maxsize=None)
def file_rows(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.open():
        if line.strip():
            row = json.loads(line)
            iid = row.get("instance_id")
            if iid:
                out[iid] = row_env(path, row)
    return out


def winners(paths: list[Path], deny: bool = False) -> dict[str, tuple[Path, str]]:
    """deny=True mirrors loaders that apply canonical_scores._score_file_allowed (m1_strong_run.merge_verdicts)."""
    out: dict[str, tuple[Path, str]] = {}
    for p in paths:
        if deny and not _score_file_allowed(p):
            continue
        for iid, env in file_rows(p).items():
            out[iid] = (p, env)
        cpu_path = minicheck_cpuverif_path(p)
        if cpu_path:
            cpu = minicheck_cpuverif_rows(p)
            for iid in file_rows(p):
                if iid in cpu:
                    out[iid] = (cpu_path, "cpuverif")
    return out


def cond_of(iid: str) -> str:
    parts = iid.split("__")
    return parts[1] if len(parts) > 1 else ""


# ---------- agreement evidence ----------

def load_agreement() -> dict[str, str]:
    """relpath → short agreement text vs reference env."""
    ev: dict[str, str] = {}
    p = ROOT / "notes/minicheck_cpuverif_agreement.json"
    if p.is_file():
        for rel, r in json.loads(p.read_text())["files"].items():
            tag = "full rescore" if r["mode"] == "full" else "30-row probe"
            ev[rel] = f"{tag} {r['verdict_agree']}/{r['n_compared']}"
    p = ROOT / "notes/t15_card_cpuverif_agreement.json"
    if p.is_file():
        for key, r in json.loads(p.read_text()).items():
            ev[f"results/raw/t15/{key}.jsonl"] = f"full rescore {r['verdict_agree']}/{r['n_common']} (superseded by cpuverif)"
    p = ROOT / "notes/m1_granite_cpuverif_agreement.json"
    if p.is_file():
        g = json.loads(p.read_text())
        if g.get("pass"):
            txt = " + ".join(f"{k} {round(g[k]['verdict_agreement'] * g[k]['n_compared'])}/{g[k]['n_compared']}"
                             for k in ("c0_probe", "e1_probe") if k in g)
            ev.setdefault(g["reference_scores"], f"cpuverif probe {txt}")
    p = ROOT / "notes/env_probe_cpuverif.json"
    if p.is_file():
        for rel, r in json.loads(p.read_text()).items():
            if r.get("pass"):
                ev[rel] = f"{r['reference_env']} 30-row probe {r['verdict_agree']}/{r['n_compared']}"
    p = ROOT / "notes/t14_env_agreement.json"
    if p.is_file():
        t6 = {c["id"]: c["jsonl"] for c in json.loads((ROOT / "notes/t6a_eco_checkers.json").read_text())["checkers"]}
        for r in json.loads(p.read_text())["checkers"]:
            fname = t6.get(r["checker"], f"{r['checker']}.jsonl")
            ev.setdefault(f"results/raw/t14/{fname}",
                          f"T14 vllm-env 30-row probe vs main scores {round(r['verdict_agreement'] * r['n_compared'])}/{r['n_compared']}")
    return ev


AGREE = load_agreement()


def env_cell(win: dict[str, tuple[Path, str]], ids: set[str], slug: str, source: str = "") -> dict:
    envs: Counter = Counter()
    files: Counter = Counter()
    for iid in ids:
        if iid in win:
            p, e = win[iid]
            envs[e] += 1
            files[str(p.relative_to(ROOT))] += 1
    ok_envs = REFERENCE | ({"cpuverif_legacy"} if slug in LEGACY_OK else set())
    by_design = REF_BY_DESIGN.get(slug)
    if by_design:
        ok_envs = ok_envs | {by_design[0]}
    checks = []
    unchecked = []
    for f in files:
        f_envs = {win[i][1] for i in ids if i in win and str(win[i][0].relative_to(ROOT)) == f}
        if f_envs <= ok_envs:
            continue
        if f in AGREE:
            checks.append(f"`{f}`: {AGREE[f]}")
        else:
            unchecked.append(f)
    if not envs:
        label = "—"
    elif len(envs) == 1:
        label = next(iter(envs))
    else:
        label = " + ".join(f"{e} {n}" for e, n in envs.most_common())
    status = "reference" if set(envs) <= ok_envs else ("checked" if not unchecked else "UNCHECKED")
    if by_design and by_design[0] in envs:
        checks = [by_design[1]] + checks
    if slug in NODE30_ONLY:
        label, checks, unchecked, status = "node30", ["NA (node30-only main-card number, decision M)"], [], "node30-only"
    return {
        "env": label,
        "env_rows": dict(envs),
        "files": dict(files),
        "agreement": checks,
        "unchecked_non_reference_files": unchecked,
        "status": status,
        "source": source,
        "commit": commit_of(source) if source else HEAD,
    }


# ---------- instance id universes ----------

def ids_of(path: str) -> set[str]:
    return {json.loads(l)["instance_id"] for l in (ROOT / path).open() if l.strip()}


MAIN_IDS = ids_of("data/v3/instances_main.jsonl") | ids_of("data/v3/instances_cpu_early.jsonl")
T7_IDS = ids_of("data/t7/instances_e1_unit.jsonl")
T17_IDS = ids_of("data/v3/t17_downdose.jsonl")
T14_IDS = ids_of("data/t14/instances_t14.jsonl")


def by_cond(ids: set[str], *conds: str) -> set[str]:
    return {i for i in ids if cond_of(i) in conds}


def fmt(rate, lo=None, hi=None) -> str:
    if rate is None or rate != rate:
        return "—"
    s = f"{100 * rate:.1f}%"
    if lo is not None and hi is not None:
        s += f" [{100 * lo:.1f}, {100 * hi:.1f}]"
    return s


rows: list[dict] = []


def add(table: str, checker: str, metric: str, value: str, n, cell: dict) -> None:
    rows.append({"table": table, "checker": checker, "metric": metric, "value": value, "n": n, **cell})


# ---------- A. main card (main DOSE, | C0 PASS; same computation as Figure 1) ----------

CARD_SRC = "scripts/t15_card_report.py (metrics_block) via scripts/figures/fig1_qi_vs_us.py loader"
CARD_KEYS = ("c0_pass_rate", "qi_all", "qi_nat", "ns", "us_claim_up", "us_evid_up")
CARD_CELL: dict[str, dict] = {}


def card_verdicts(slug: str) -> dict[str, str]:
    out = {}
    for iid, r in t13.merged_score_rows(slug).items():
        v = r.get("verdict")
        if v in ("PASS", "FAIL", "PARSE_FAIL"):
            out[iid] = v
        elif r.get("score") is not None:
            out[iid] = "PASS" if float(r["score"]) >= 0.5 else "FAIL"
    for iid, v in m1s.merge_verdicts(slug, (ROOT / "results/raw/lane_b/main_e1_evid",)).items():
        out.setdefault(iid, v)
    return out


def section_card() -> None:
    inst = load_main_dose_instances()
    for slug in CANONICAL_VERIFIERS:
        v = card_verdicts(slug)
        block = join_rows(inst, v) + join_extra(inst, v, T7)
        m = metrics_block(block, set())
        if m["qi_all"].get("rate") is None:
            continue
        e1_evid = [p for p in m1_paths(slug, (ROOT / "results/raw/lane_b/main_e1_evid",)) if _score_file_allowed(p)]
        win = winners(e1_evid + t13_paths(slug))
        ids = {r["instance_id"] for r in block} & set(win)
        cell = env_cell(win, ids, slug)
        cell["source"] = "computed in this script (score files per number in notes/paper_numbers_final.json)"
        cell["script"] = CARD_SRC
        CARD_CELL[slug] = cell
        for key in CARD_KEYS:
            st = m.get(key) or {}
            if st.get("rate") is None:
                continue
            add("Main card (main DOSE)", verifier_display_name(slug), key, fmt(st["rate"], st.get("lo"), st.get("hi")), st.get("den"), cell)


# ---------- B. M1-strong final, amendment 5 ----------

def m1_names(slug: str) -> tuple[str, ...]:
    fname = score_filename(slug)
    if slug == "v2b_bespoke" and fname == "t6_bespoke_minicheck.jsonl":
        return (fname, "v2b_bespoke.jsonl", f"{slug}.jsonl")
    return (fname, f"{slug}.jsonl")


def m1_paths(slug: str, dirs) -> list[Path]:
    return [d / n for d in dirs for n in m1_names(slug)]


API_SLUGS = ("v1_medscore", "v4_ragas_nli", "v5_ragas_nli")


def us_after_dirs(slug: str) -> tuple[Path, ...]:
    if slug in API_SLUGS:
        return m1s.US_AFTER_DIRS + (ROOT / "results/raw_m1/t7_amend5",)
    return (ROOT / "results/raw/lane_b/m1_t7_e1_unit", ROOT / "results/raw/lane_b/m1_t7_e1_unit_amend5")


def m1_groups(slug: str) -> dict:
    ns_dirs = m1s.MAIN_NS_DIRS + ((ROOT / "results/raw/t2_full",) if slug in API_SLUGS else ())
    ns_ids = MAIN_IDS | ids_of("data/lane_b/m1_strong_ns.jsonl")
    return {
        "NS_x10": (ns_dirs, ns_ids, ("E1-claim", "E1-evid")),
        "NS_div10": ((ROOT / "results/raw/lane_b/m1_strong_ns",) + m1s.T17_DIRS, T17_IDS | ids_of("data/lane_b/m1_strong_ns.jsonl"), ("E1-down10",)),
        "US_up_before": (m1s.T7_BEFORE_DIRS, T7_IDS, ("E1-unit-claim", "E1-unit-evid")),
        "US_up_after": (us_after_dirs(slug), T7_IDS, ("E1-unit-claim", "E1-unit-evid")),
        "US_down_before": (m1s.T17_DIRS, T17_IDS, ("E1-unit-down",)),
        "US_down_after": (m1s.DOWN_AFTER_DIRS, T17_IDS, ("E1-unit-down",)),
    }


M1_SRC = "notes/m1_strong_final_amend5.json"


def section_m1() -> None:
    d = json.loads((ROOT / M1_SRC).read_text())
    for slug, blk in d["checkers"].items():
        if slug in NODE30_ONLY:
            continue
        groups = m1_groups(slug)

        def cell_for(grp: str) -> dict:
            dirs, uni, conds = groups[grp]
            win = winners(m1_paths(slug, dirs), deny=True)
            c = env_cell(win, by_cond(uni & set(win), *conds), slug, M1_SRC)
            c["script"] = "scripts/m1_strong_run.py --final --amend5"
            return c

        name = blk["display_name"]
        for side in ("claim", "evid"):
            for metric in (f"NS_x10_{side}", f"NS_div10_{side}"):
                m = blk["metrics"].get(metric)
                if m:
                    add("M1-strong final (amendment 5)", name, metric, fmt(m["rate"], m["lo"], m["hi"]), m["den"], cell_for(metric.rsplit("_", 1)[0]))
            for direction in ("up", "down"):
                pr = blk["paired"].get(f"{direction}_{side}") or {}
                for when in ("before", "after"):
                    m = pr.get(when) or {}
                    label = f"US_{direction}_{when}_{side} (paired; b/c {pr.get('b_pass_to_fail')}/{pr.get('c_fail_to_pass')})" if when == "after" else f"US_{direction}_{when}_{side} (paired)"
                    add("M1-strong final (amendment 5)", name, label, fmt(m.get("rate"), m.get("lo"), m.get("hi")), pr.get("n_pairs"), cell_for(f"US_{direction}_{when}"))
            b = blk["bind"][side]
            add("M1-strong final (amendment 5)", name, f"Bind {side} (up, down → side)", f"{b['up']}, {b['down']} → {b['side']}", None,
                cell_for("US_up_after"))
        add("M1-strong final (amendment 5)", name, "Bind overall", str(blk["binding_overall"]), None, cell_for("US_up_after"))


# ---------- C. T13 ----------

T13_PAIR_COND = {
    "x1000_vs_inv": ("E1-unit-claim", "INV-claim"),
    "x1000_vs_inv_all": ("E1-unit-claim", "INV-claim"),
    "x1000_vs_c0": ("E1-unit-claim", "C0"),
    "evid_x1000_vs_c0": ("E1-unit-evid", "C0"),
    "e1x2_vs_inv": ("E1-claim", "INV-claim"),
}


def t13_paths(slug: str) -> list[Path]:
    paths: list[Path] = []
    t6a = {c["id"]: c["jsonl"] for c in json.loads(t13.T6A.read_text()).get("checkers", [])}
    if slug in t6a:
        paths += [d / t6a[slug] for d in t13.SCORE_DIRS]
    if slug == "v2b_bespoke":
        paths += [d / n for n in ("t6_bespoke_minicheck.jsonl", "v2b_bespoke.jsonl") for d in t13.SCORE_DIRS]
    for d in t13.SCORE_DIRS:
        llama, plain = d / f"{slug}.llama.jsonl", d / f"{slug}.jsonl"
        paths.append(llama if llama.is_file() else plain)
    seen, out = set(), []
    for p in paths:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def section_t13() -> None:
    src = "notes/t13_pairwise_preference.json"
    d = json.loads((ROOT / src).read_text())
    for slug, blk in d["by_verifier"].items():
        if slug.startswith("t6_") or slug == "v6_ragas_nli" or slug in NODE30_ONLY:
            continue
        win = winners(t13_paths(slug))
        for key, p in blk["pairs"].items():
            ids = by_cond((MAIN_IDS | T7_IDS) & set(win), *T13_PAIR_COND[key])
            lo, hi = p["ci95"]
            c = env_cell(win, ids, slug, src)
            c["script"] = "scripts/t13_best_of_n_report.py"
            add("T13 pairwise preference", blk["display_name"], f"P(wrong≥correct) {key}", fmt(p["p_wrong_prefers"], lo, hi), p["n_pairs"], c)


# ---------- D. T14 ----------

def section_t14() -> None:
    src = "notes/t14_c0_conditional_pass.json"
    d = json.loads((ROOT / src).read_text())
    for slug, blk in d["by_verifier"].items():
        if slug in NODE30_ONLY:
            continue
        paths = t13_paths(slug)
        t14_names = [f"{slug}.jsonl", f"{slug}.llama.jsonl"] + ([f"t6_{slug[4:]}.jsonl"] if slug.startswith("t6a_") else [])
        t14_paths = [ROOT / "results/raw/t14" / n for n in t14_names]
        win = winners(paths + t14_paths)

        def cell(ids: set[str]) -> dict:
            c = env_cell(win, ids, slug, src)
            c["script"] = "scripts/t14_c0_conditional_report.py"
            return c

        add("T14", blk["display_name"], "C0 pass rate", fmt(blk["c0_pass_rate"]), blk["n_c0_scored"], cell(by_cond(MAIN_IDS & set(win), "C0")))
        add("T14", blk["display_name"], "QI (INV nat | C0)", fmt(blk["qi_inv_natural_given_c0"]), blk["n_qi_given_c0"], cell(by_cond(MAIN_IDS & set(win), "INV-claim", "C0")))
        for fam, f in blk["families"].items():
            if not f.get("n_given_c0"):
                continue
            add("T14", blk["display_name"], f"P(PASS | C0) {fam}", fmt(f["p_pass_given_c0"]), f["n_given_c0"], cell(T14_IDS & set(win)))


# ---------- E. T15 card, AggreFact, T15-OOD, T24b ----------

def aggrefact_agreement() -> dict[str, str]:
    out = {}
    for leg in ("base", "ft"):
        a = {}
        for env, d in (("vllm", "results/raw/t15"), ("cpuverif", "results/raw/t15_cpuverif")):
            f = ROOT / d / f"{leg}_aggrefact_test.jsonl"
            if f.is_file():
                a[env] = {json.loads(l)["instance_id"]: json.loads(l)["verdict"] for l in f.open() if l.strip()}
        if len(a) == 2:
            common = set(a["vllm"]) & set(a["cpuverif"])
            agree = sum(a["vllm"][i] == a["cpuverif"][i] for i in common)
            out[leg] = f"cpuverif vs vllm {agree}/{len(common)}"
    return out


def aggrefact_bacc() -> tuple[dict[str, dict[str, str]], list[tuple[str, int, str, str]]]:
    """Overall (macro BAcc over the 11 datasets, micro BAcc, accuracy, n) per leg + per-dataset BAcc rows."""
    overall: dict[str, dict[str, str]] = {}
    per_ds: list[tuple[str, int, str, str]] = []
    for line in (ROOT / "notes/t15_report.md").read_text().splitlines():
        m = re.match(
            r"- \*\*(base|ft)\*\* LLM-AggreFact BAcc \(macro over datasets\)=([\d.]+) · micro BAcc=([\d.]+)"
            r" · accuracy=([\d.]+) \(n=(\d+)",
            line,
        )
        if m:
            overall[m.group(1)] = {"macro": m.group(2), "micro": m.group(3), "acc": m.group(4), "n": m.group(5)}
            continue
        m = re.match(r"\| ([A-Za-z][\w.-]*) \| (\d+) \| ([\d.]+) \| ([\d.]+) \| [+-][\d.]+ \|$", line)
        if m:
            per_ds.append((m.group(1), int(m.group(2)), m.group(3), m.group(4)))
    return overall, per_ds


def section_t15() -> None:
    src = "notes/t15_card.json"
    d = json.loads((ROOT / src).read_text())
    raw = ROOT / "results/raw/t15_cpuverif"
    for leg, m in d["main_dose"].items():
        paths = [raw / f"{leg}_{p}.jsonl" for p in ("main_dose", "t7", "t17")]
        win = winners(paths)
        cell = env_cell(win, set(win), "t15", src)
        cell["script"] = "scripts/t15_card_report.py"
        if leg == "ft":
            CARD_CELL["t15_ft"] = cell
        for key in ("c0_pass_rate", "qi_all", "qi_nat", "ns", "us_claim_up", "us_evid_up", "us_claim_down", "us_evid_down"):
            s_ = m[key]
            add("T15 card (main DOSE)", f"MiniCheck-RoBERTa {leg}", key, fmt(s_["rate"], s_["lo"], s_["hi"]), s_["den"], cell)
    agree = aggrefact_agreement()
    bacc, per_ds = aggrefact_bacc()
    for leg in ("base", "ft"):
        win = winners([raw / f"{leg}_aggrefact_test.jsonl"])
        cell = env_cell(win, set(win), "t15", "notes/t15_report.md")
        cell["script"] = "scripts/t15_aggrefact_finish_report.sh"
        if leg in agree:
            cell["agreement"] = cell["agreement"] + [agree[leg]]
        b = bacc.get(leg, {})
        n = int(b.get("n", len(win)))
        add("T15 card (AggreFact test)", f"MiniCheck-RoBERTa {leg}",
            "LLM-AggreFact BAcc (macro mean over 11 datasets)", b.get("macro", "—"), n, cell)
        add("T15 card (AggreFact test)", f"MiniCheck-RoBERTa {leg}", "micro BAcc (all rows pooled)", b.get("micro", "—"), n, cell)
        add("T15 card (AggreFact test)", f"MiniCheck-RoBERTa {leg}", "accuracy (reference only)", b.get("acc", "—"), n, cell)
        for ds, ds_n, base_v, ft_v in per_ds:
            add("T15 card (AggreFact test, per dataset)", f"MiniCheck-RoBERTa {leg}", f"BAcc {ds}",
                base_v if leg == "base" else ft_v, ds_n, cell)

    src = "notes/t15_ood_card.json"
    d = json.loads((ROOT / src).read_text())
    for pack, legs in d.items():
        if not isinstance(legs, dict) or "base" not in legs:
            continue
        for leg, m in legs.items():
            win = winners([raw / f"{leg}_{'t24b' if pack == 't24b' else 't18_ood'}.jsonl"])
            cell = env_cell(win, set(win), "t15", src)
            cell["script"] = "scripts/t15_ood_report.py"
            for key, s_ in m.items():
                add(f"T15-OOD ({pack})", f"MiniCheck-RoBERTa {leg}", key, fmt(s_["rate"], s_["lo"], s_["hi"]), s_["den"], cell)


T24B_FILES = {
    "MiniCheck-RoBERTa": "t6_minicheck_roberta.jsonl", "MiniCheck-DeBERTa": "t6_minicheck_deberta.jsonl",
    "AlignScore-base": "t6_alignscore_base.jsonl", "MiniCheck-Flan-T5-Large": "v2a_minicheck.jsonl",
    "AlignScore-large": "v3_alignscore.jsonl", "Bespoke-MiniCheck-7B": "v2b_bespoke.jsonl",
    "Llama-3.3-70B (RAGAS NLI)": "v4_ragas_nli.jsonl", "Mistral-Small-24B (MedScore)": "v1_medscore.jsonl",
}


def section_t24b() -> None:
    src = "notes/t24b_report.md"
    lines = (ROOT / src).read_text().splitlines()
    hdr = next(i for i, l in enumerate(lines) if l.startswith("| Checker |"))
    cols = [c.strip() for c in lines[hdr].strip("|").split("|")]
    for line in lines[hdr + 2:]:
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip("|").split("|")]
        name = cells[0]
        fname = T24B_FILES[name]
        slug = fname.removesuffix(".jsonl").replace("t6_", "t6a_", 1) if fname.startswith("t6_") else fname.removesuffix(".jsonl")
        win = winners([ROOT / "results/raw/t24b" / fname])
        cell = env_cell(win, set(win), slug, src)
        cell["script"] = "scripts/t24b_report.py"
        for col, val in zip(cols[1:], cells[1:]):
            n = re.search(r"n=(\d+)", val)
            add("T24b", name, col, val.split(" (n=")[0], int(n.group(1)) if n else None, cell)


# ---------- F. T17 NS ÷2 / ÷10 ----------

def section_t17() -> None:
    src = "notes/t17_ns.json"
    d = json.loads((ROOT / src).read_text())
    for slug, blk in d.items():
        if not isinstance(blk, dict) or "cells" not in blk or slug in NODE30_ONLY:
            continue
        win = winners(t13_paths(slug) + [p for p in m1_paths(slug, m1s.T17_DIRS) if _score_file_allowed(p)])
        for key, m in blk["cells"].items():
            cond = "E1-down10" if "div10" in key else "E1-down2"
            c = env_cell(win, by_cond(T17_IDS & set(win), cond, "E1-unit-down") | by_cond(MAIN_IDS & set(win), "C0"), slug, src)
            c["script"] = "scripts/t17_ns_report.py"
            add("T17 NS (÷2, ÷10)", blk["display_name"], f"FAIL {key} | C0 PASS", fmt(m.get("rate"), m.get("lo"), m.get("hi")), m.get("den"), c)


# ---------- G. T9 NeMo Guardrails ----------

def section_t9() -> None:
    src = "notes/t9_nondose.json"
    for r in json.loads((ROOT / src).read_text()):
        win = winners([ROOT / r["source"]])
        c = env_cell(win, set(win), "t9", src)
        c["script"] = "scripts/t9_nondose_report.py"
        add("T9 NeMo Guardrails (non-dose excluded)", r["rail"], f"blocked · {r['cell']}", f"{fmt(r['rate'], r['lo'], r['hi'])} ({r['blocked']}/{r['total']})", r["total"], c)


# ---------- H. Repair (M1 E1-unit evid explanations) ----------

def section_repair() -> None:
    import m1_e1_unit_repair_report as rep

    src = "notes/m1_e1_unit_repair_report.json"
    d = json.loads((ROOT / src).read_text())
    specs = {"t7_e1_unit_evid_x1000": rep.LLM_VERIFIERS, "t17_e1_unit_down_evid": rep.T17_LLMS}
    for key, cohort in d.items():
        dirs = {slug: (b, a) for slug, _l, b, a in specs[key]}
        uni = T7_IDS if key.startswith("t7") else T17_IDS
        for v in cohort["verifiers"]:
            slug = v["verifier"]
            b, a = dirs[slug]
            after = [a] + ([rep.AFTER_M1_T7_AMEND5] if a == rep.AFTER_M1_T7 else [])
            files = [rep.score_file(x, slug) for x in [b] + after]
            win_b = winners([f for f in files[:1] if f])
            win_a = winners([f for f in files[1:] if f])
            win = {**{f"b:{k}": x for k, x in win_b.items()}, **{f"a:{k}": x for k, x in win_a.items()}}
            ids = {f"b:{i}" for i in uni & set(win_b)} | {f"a:{i}" for i in uni & set(win_a)}
            c = env_cell(win, ids, slug, src)
            c["script"] = "scripts/m1_e1_unit_repair_report.py"
            n = v["n_paired"]
            add("Repair (E1-unit evid, before → after M1)", f"{verifier_display_name(slug)} · {cohort['cohort']}", "PASS before → after",
                f"{v['pass_before']}/{n} → {v['pass_after']}/{n}", n, c)


# ---------- I. QC ----------

def section_qc() -> None:
    qc_cell = {"env": "human", "env_rows": {}, "files": {}, "agreement": [], "unchecked_non_reference_files": [], "status": "n/a (human labels)"}
    src = "notes/qc_gemini_vs_author.json"
    d = json.loads((ROOT / src).read_text())
    for k, v in d.items():
        if not isinstance(v, dict):
            continue
        add("QC (author vs Gemini validator)", k, "approved_labelled / author_rejected / text_mismatch / no_gemini_pass",
            f"{v.get('approved_labelled')} / {v.get('author_rejected')} / {v.get('text_mismatch')} / {v.get('no_gemini_pass')}", None,
            {**qc_cell, "source": src, "commit": commit_of(src), "script": "scripts/qc_gemini_vs_author.py"})
    src = "notes/iaa_kappa.json"
    d = json.loads((ROOT / src).read_text())
    for q in ("q1_vs_expected_verdict", "q2_vs_author_labels"):
        o = d[q]["overall"]
        val = f"κ={o['kappa']:.3f} ({100 * o['pct_agree']:.1f}% agree)" if o.get("kappa") is not None else "not filled (0 pairs)"
        add("QC (IAA)", q, "Cohen's κ overall", val, o.get("n_pairs"),
            {**qc_cell, "source": src, "commit": commit_of(src), "script": "scripts/iaa_kappa.py"})


# ---------- J. Figure 1 ----------

def section_fig1() -> None:
    src = "results/figures/fig1_qi_vs_us.json"
    for p in json.loads((ROOT / src).read_text()):
        cell = dict(CARD_CELL.get(p["slug"]) or {"env": "—", "env_rows": {}, "files": {}, "agreement": [], "unchecked_non_reference_files": [], "status": "—"})
        cell.update(source=src, commit=commit_of(src), script="scripts/figures/fig1_qi_vs_us.py")
        for key in ("qi_all", "us_claim_up", "ns"):
            st = p.get(key) or {}
            if st.get("rate") is None:
                continue
            add("Figure 1 (QI_all vs US_up claim; NS inset)", p["label"], key, fmt(st["rate"], st.get("lo"), st.get("hi")), st.get("den"), cell)


# ---------- K. agreement evidence ----------

def agreement_lines() -> list[str]:
    lines = ["## Agreement checks vs reference env", "",
             "| check | result | source |", "|---|---|---|"]
    for rel, txt in sorted(AGREE.items()):
        lines.append(f"| `{rel}` | {txt} | agreement JSONs (see source column of each number) |")
    for leg, txt in aggrefact_agreement().items():
        lines.append(f"| AggreFact test {leg} (`results/raw/t15` vs `results/raw/t15_cpuverif`) | {txt} | computed by `{SCRIPT}` |")
    lines.append("")
    return lines


# ---------- render ----------

def main() -> None:
    section_card()
    section_m1()
    section_t13()
    section_t14()
    section_t15()
    section_t24b()
    section_t17()
    section_t9()
    section_repair()
    section_qc()
    section_fig1()
    status = Counter(r["status"] for r in rows)
    envs = Counter(r["env"] if "+" not in r["env"] else "mixed" for r in rows)
    lines = [
        "# Paper numbers — final, with score env",
        "",
        f"Generated by `{SCRIPT}` at commit `{HEAD}`. This file is the only source of paper numbers "
        "(`qvc/paper_numbers.json` and `results/tables/card_main.md` are archived). M1-strong numbers are the amendment-5 table "
        "(`notes/m1_prereg_amendment5.md`). HHEM and SummaC-Conv appear only in the main card (env node30, agreement NA) and are "
        "excluded from every other analysis (decision M).",
        "",
        "`env` is read from each score row the number uses, following the table's own loader (same directories and order; last file wins):",
        "",
        "- **cpuverif** — reference env for local checkers (torch cpu, transformers 5.x).",
        "- **cpuverif_legacy** — reference env for SummaC-ZS.",
        "- **API** — hosted LLM judges via OpenRouter (row has `api_model`/`api_provider`).",
        "- **vllm** — GPU env (`results/raw/t15`; Bespoke-MiniCheck-7B bf16, where vllm is the reference env by design).",
        "- **nemo** — NeMo Guardrails' own env for the T9 AlignScore rails (reference env by design).",
        "- **node30** — `results/raw_node30` rows; each file needs an agreement check vs cpuverif (listed), except HHEM/SummaC-Conv (NA by decision).",
        "- **unrecorded** — local score file with no env metadata.",
        "",
        "`status`: **reference** = every row from a reference env; **checked** = non-reference rows, each such file has a verdict-agreement "
        "check vs the reference env (listed); **UNCHECKED** = at least one non-reference file has no check; **node30-only** = HHEM/SummaC-Conv main card.",
        "",
        "Columns: value = rate [95% cluster-bootstrap CI by base]; n = denominator; source = artifact the number is read from; "
        "script = generator of that artifact; commit = last commit of the source artifact.",
        "",
        f"- Numbers: **{len(rows)}** · status: " + ", ".join(f"{k} **{v}**" for k, v in status.most_common()),
        "- env: " + ", ".join(f"{k} **{v}**" for k, v in envs.most_common()),
        "",
    ]
    unchecked = Counter(f for r in rows for f in r["unchecked_non_reference_files"])
    if unchecked:
        lines += ["## Non-reference files without an agreement check", "", "| file | numbers using it |", "|---|---:|"]
        lines += [f"| `{f}` | {n} |" for f, n in unchecked.most_common()]
        lines.append("")
    lines += agreement_lines()
    for table in dict.fromkeys(r["table"] for r in rows):
        lines += [f"## {table}", "",
                  "| checker | metric | value [95% CI] | n | env | status | agreement | source | script | commit |",
                  "|---|---|---|---:|---|---|---|---|---|---|"]
        for r in (x for x in rows if x["table"] == table):
            chk = "<br>".join(r["agreement"]) if r["agreement"] else ""
            if r["unchecked_non_reference_files"]:
                chk += ("<br>" if chk else "") + "no check: " + ", ".join(f"`{f}`" for f in r["unchecked_non_reference_files"])
            lines.append(f"| {r['checker']} | {r['metric']} | {r['value']} | {r['n'] if r['n'] is not None else ''} | {r['env']} | "
                         f"{r['status']} | {chk} | `{r.get('source', '')}` | `{r.get('script', '')}` | `{r.get('commit', '')}` |")
        lines.append("")
    OUT.write_text("\n".join(lines) + "\n")
    OUT_JSON.write_text(json.dumps(rows, indent=1) + "\n")
    print(json.dumps({"n": len(rows), "status": status, "env": envs, "unchecked_files": len(unchecked)}, indent=1))


if __name__ == "__main__":
    main()
