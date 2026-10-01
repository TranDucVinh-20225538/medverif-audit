"""Shared helpers for journal chain 3 (FT-on-RD, FT+UNF, small local LLM judges).  Python >= 3.8.

SELF-CONTAINED on purpose: the HPC checkout has ~30 locally modified files (e.g. scripts/t15_card_report.py is an older
local version), so chain 3 never imports from scripts/*.py, analysis/ or scripts/journal{,2}/.  The few helpers it
needs are vendored here from the committed versions:
  * bootstrap_rate / card metrics  <- analysis/analyze.py + scripts/t15_card_report.metrics_block (git 6d0b7d8)
  * drug-cluster bootstrap (Boot/ratio), verdict rule <- scripts/journal2/impact_estimate.py
  * RAG cells (cell/boot)          <- scripts/journal/jr_rag_report.py
  * held-out UNF metrics (residual, auc) <- scripts/journal2/unf_heldout_report.py
Nothing from src/ is imported either (UNF v1/v2 texts are pre-computed in the committed packs); the sha256 of
src/unit_norm_fix_v2.py is still checked against results/journal2/unf_v2_freeze.json.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import subprocess
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
J3 = ROOT / "results" / "journal3"
MARKERS = Path(os.environ.get("MEDVERIF_J3_MARKERS") or (J3 / "markers"))  # override only for smoke tests
PACKS_DIR = J3 / "packs"
FT_SCORES = J3 / "ft" / "scores"
JUDGE_SCORES = J3 / "judges" / "scores"
NOTES = ROOT / "notes"
FREEZE = ROOT / "results/journal2/unf_v2_freeze.json"
MOCK = os.environ.get("MEDVERIF_J3_MOCK", "").lower() in ("1", "true", "yes")

# ---------------------------------------------------------------- packs (all committed; chain 3 never rebuilds them)
PACK_FILES = {
    "card": PACKS_DIR / "card.jsonl",                                   # frozen by j3_build_card.py (958 rows)
    "rag": ROOT / "data/journal/instances_rag.jsonl",                   # chain-1 real-RAG pack (1622)
    "rd": ROOT / "results/journal2/real_dose/instances.jsonl",          # real-dose answers (1451)
    "ho": ROOT / "data/journal2/unf_heldout.jsonl",                     # held-out UNF set (S/U/anchor = 450 scored)
    "rdunf": ROOT / "results/journal2/unf_heldout/rd_pack.jsonl",       # RD pairs changed by UNF v1/v2 (705)
}
# (pack, variant) -> (claim column, evidence column)
VARIANTS = {
    ("card", "raw"): ("claim", "evidence"), ("rag", "raw"): ("claim", "evidence"), ("rd", "raw"): ("claim", "evidence"),
    ("ho", "raw"): ("claim", "evidence"), ("ho", "unf"): ("claim_unf", "evidence_unf"),
    ("ho", "unf_v2"): ("claim_unf_v2", "evidence_unf_v2"),
    ("rdunf", "raw"): ("claim_orig", "evidence_orig"), ("rdunf", "unf"): ("claim_unf", "evidence_unf"),
    ("rdunf", "unf_v2"): ("claim_unf_v2", "evidence_unf_v2"),
}


def log(stage: str, **kw) -> None:
    print(json.dumps(dict({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "stage": stage}, **kw), ensure_ascii=False, default=str),
          flush=True)


def read_jsonl(path) -> List[dict]:
    out = []
    p = Path(path)
    if not p.is_file():
        return out
    with p.open(encoding="utf-8") as fh:
        for l in fh:
            if l.strip():
                try:
                    out.append(json.loads(l))
                except json.JSONDecodeError:  # partially written last line of a running job
                    continue
    return out


def append_jsonl(path, rows: Iterable[dict]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def done_ids(path) -> set:
    return {r["instance_id"] for r in read_jsonl(path) if r.get("instance_id")}


def marker(stage: str) -> Path:
    return MARKERS / ("%s.done" % stage)


def is_done(stage: str) -> bool:
    return marker(stage).is_file() and not os.environ.get("MEDVERIF_J3_FORCE", "") in (stage, "all")


def mark_done(stage: str, **info) -> None:
    MARKERS.mkdir(parents=True, exist_ok=True)
    info = dict({"stage": stage, "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                 "slurm_job": "%s%s" % (os.environ.get("SLURM_ARRAY_JOB_ID") or os.environ.get("SLURM_JOB_ID", "local"),
                                        ("_" + os.environ["SLURM_ARRAY_TASK_ID"]) if os.environ.get("SLURM_ARRAY_TASK_ID") else "")}, **info)
    marker(stage).write_text(json.dumps(info, indent=1, default=str) + "\n")


def sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def v2_freeze_ok() -> Tuple[bool, str, str]:
    frz = json.loads(FREEZE.read_text())
    cur = sha256(ROOT / "src/unit_norm_fix_v2.py")
    return cur == frz["sha256"], cur, frz["sha256"]


def git_dirty(paths: List[str]) -> List[str]:
    try:
        out = subprocess.run(["git", "status", "--porcelain", "--"] + paths, cwd=ROOT, capture_output=True, text=True, timeout=60).stdout
    except Exception:  # noqa: BLE001
        return []
    return [l for l in out.splitlines() if l.strip()]


def pack_rows(pack: str, variant: str = "raw") -> List[dict]:
    """[{instance_id, claim, evidence, cluster}] for one pack/variant (only rows the chain scores)."""
    c, e = VARIANTS[(pack, variant)]
    out = []
    for r in read_jsonl(PACK_FILES[pack]):
        if not r.get("valid", True):
            continue
        if pack == "ho" and r.get("family") not in ("S", "U", "anchor"):
            continue
        cl, ev = (r.get(c) or "").strip(), (r.get(e) or "").strip()
        if cl and ev:
            out.append({"instance_id": r["instance_id"], "claim": cl, "evidence": ev,
                        "cluster": r.get("drug") or r.get("base_id") or r.get("question_id")})
    return out


def text_key(claim: str, evidence: str) -> str:
    return hashlib.sha1((claim + "\x00" + evidence).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- verdict rules
def verdict_map(path, threshold_rule: str = "gt") -> Dict[str, str]:
    """Stored verdict wins; else score > 0.5 (rd_report / impact_estimate rule).  Last row per id wins."""
    out = {}
    for r in read_jsonl(path):
        v = r.get("verdict")
        if v in ("PASS", "FAIL", "PARSE_FAIL"):
            out[r["instance_id"]] = v
        elif r.get("score") is not None:
            out[r["instance_id"]] = "PASS" if float(r["score"]) > 0.5 else "FAIL"
    return out


def score_map(paths, key: str = "score") -> Dict[str, float]:
    """Continuous score per id (judges: p_yes if present, else score)."""
    out = {}
    for p in paths if isinstance(paths, (list, tuple)) else [paths]:
        for r in read_jsonl(p):
            s = r.get("p_yes") if r.get("p_yes") is not None else r.get(key)
            if s is not None:
                out[r["instance_id"]] = float(s)
    return out


# ---------------------------------------------------------------- base-clustered bootstrap (analysis/analyze.py)
N_BOOT, SEED = 1000, 42


def _percentile(xs: List[float], q: float) -> float:
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * q
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def bootstrap_rate(groups: List[Tuple[int, int]], seed: int = SEED, n_boot: int = N_BOOT) -> dict:
    usable = [(n, d) for n, d in groups if d > 0]
    num = sum(n for n, _ in usable)
    den = sum(d for _, d in usable)
    if den == 0:
        return {"rate": None, "lo": None, "hi": None, "num": 0, "den": 0, "n_bases": 0}
    point = num / den
    if len(usable) < 2:
        return {"rate": point, "lo": None, "hi": None, "num": num, "den": den, "n_bases": len(usable)}
    rng = random.Random(seed)
    stats = []
    m = len(usable)
    for _ in range(n_boot):
        n_sum = d_sum = 0
        for _j in range(m):
            n, d = usable[rng.randrange(m)]
            n_sum += n
            d_sum += d
        if d_sum:
            stats.append(n_sum / d_sum)
    stats.sort()
    return {"rate": point, "lo": _percentile(stats, 0.025), "hi": _percentile(stats, 0.975), "num": num, "den": den,
            "n_bases": m}


def _groups(block, pred, want):
    by = defaultdict(list)
    for r in block:
        if r["verdict"] in ("PASS", "FAIL") and pred(r):
            by[r["base_id"]].append(r)
    return [(sum(1 for x in g if x["verdict"] == want), len(g)) for g in by.values()]


def card_metrics(card: List[dict], verd: Dict[str, str]) -> dict:
    """Paper card cells (t15_card_report.metrics_block, C0-conditional) on the frozen card cohort."""
    block = [dict(r, verdict=verd[r["instance_id"]]) for r in card if r["instance_id"] in verd]
    c0 = {r["base_id"] for r in block if r["condition"] == "C0" and r["verdict"] == "PASS"}
    inc0 = lambda r: r["base_id"] in c0  # noqa: E731
    cells = {
        "c0_pass_rate": _groups(block, lambda r: r["condition"] == "C0", "PASS"),
        "qi_all": _groups(block, lambda r: inc0(r) and r["condition"] == "INV-claim", "PASS"),
        "qi_nat": _groups(block, lambda r: inc0(r) and r["condition"] == "INV-claim" and r.get("natural_inv"), "PASS"),
        "ns": _groups(block, lambda r: inc0(r) and r["condition"] == "E1-evid", "FAIL"),
        "ns_claim": _groups(block, lambda r: inc0(r) and r["condition"] == "E1-claim", "FAIL"),
        "us_claim_up": _groups(block, lambda r: inc0(r) and r["condition"] == "E1-unit-claim" and r.get("magnitude") == "x1000", "FAIL"),
        "us_evid_up": _groups(block, lambda r: inc0(r) and r["condition"] == "E1-unit-evid" and r.get("magnitude") == "x1000", "FAIL"),
        "us_claim_down": _groups(block, lambda r: inc0(r) and r["condition"] == "E1-unit-down" and "__claim__" in r["instance_id"], "FAIL"),
        "us_evid_down": _groups(block, lambda r: inc0(r) and r["condition"] == "E1-unit-down" and "__evid__" in r["instance_id"], "FAIL"),
    }
    out = {k: bootstrap_rate(v) for k, v in cells.items()}
    out["n_scored"] = len(block)
    out["n_parse_fail"] = sum(1 for r in block if r["verdict"] == "PARSE_FAIL")
    out["n_c0_pass_bases"] = len(c0)
    return out


def inversion_floor(card: List[dict], scores: Dict[str, float]) -> dict:
    """jr_threshold_robustness.inversion_floor: share of bases whose correct conversion scores <= the wrong x1000 swap."""
    conv = {r["base_id"]: scores[r["instance_id"]] for r in card
            if r["condition"] == "INV-claim" and r.get("magnitude") == "unit_conversion" and r["instance_id"] in scores}
    out = {}
    for side, cond in (("claim", "E1-unit-claim"), ("evid", "E1-unit-evid")):
        swap = {r["base_id"]: scores[r["instance_id"]] for r in card
                if r["condition"] == cond and r.get("magnitude") == "x1000" and r["instance_id"] in scores}
        common = sorted(set(conv) & set(swap))
        inv = [b for b in common if conv[b] <= swap[b]]
        out[side] = {"floor": (len(inv) / len(common)) if common else None, "n_bases_paired": len(common),
                     "auc_conv_vs_swap": auc(list(conv.values()), list(swap.values()))}
    return out


def auc(pos: List[float], neg: List[float]) -> Optional[float]:
    if not pos or not neg:
        return None
    gt = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return gt / (len(pos) * len(neg))


# ---------------------------------------------------------------- RAG cells (jr_rag_report.cell / boot)
RAG_CELLS = [("C0 PASS", "RAG-C0", "PASS", False), ("conv PASS|C0", "RAG-conv", "PASS", True),
             ("value×2 FAIL|C0", "RAG-value-x2", "FAIL", True), ("value×10 FAIL|C0", "RAG-value-x10", "FAIL", True),
             ("unit-up FAIL|C0", "RAG-unit-up", "FAIL", True), ("unit-down FAIL|C0", "RAG-unit-down", "FAIL", True)]


def rag_cell(inst, verd, cond, want, conditional, c0_cond="RAG-C0"):
    c0ok = {r["base_id"] for r in inst if r["condition"] == c0_cond and verd.get(r["instance_id"]) == "PASS"}
    groups = defaultdict(lambda: [0, 0])
    for r in inst:
        if r["condition"] != cond or verd.get(r["instance_id"]) not in ("PASS", "FAIL"):
            continue
        if conditional and r["base_id"] not in c0ok:
            continue
        g = groups[r["question_id"]]
        g[1] += 1
        g[0] += int(verd[r["instance_id"]] == want)
    return list(groups.values())


def qboot(groups, B=2000, seed=42) -> dict:
    den = sum(d for _, d in groups)
    if not den:
        return {"rate": None, "lo": None, "hi": None, "den": 0, "n_q": 0}
    point = sum(n for n, _ in groups) / den
    if len(groups) < 2:
        return {"rate": point, "lo": None, "hi": None, "den": den, "n_q": len(groups)}
    rng = random.Random(seed)
    st = []
    for _ in range(B):
        s = [groups[rng.randrange(len(groups))] for _ in groups]
        d = sum(x[1] for x in s)
        if d:
            st.append(sum(x[0] for x in s) / d)
    st.sort()
    return {"rate": point, "lo": st[int(0.025 * (len(st) - 1))], "hi": st[int(0.975 * (len(st) - 1))], "den": den, "n_q": len(groups)}


# ---------------------------------------------------------------- drug-cluster bootstrap on counts (impact_estimate.Boot)
class Boot:
    def __init__(self, clusters: list, n_boot: int, seed: int = 20261001):
        import numpy as np

        self.np = np
        self.ids = sorted(set(clusters))
        self.idx = {c: i for i, c in enumerate(self.ids)}
        self.row_c = np.array([self.idx[c] for c in clusters])
        m = len(self.ids)
        rng = np.random.default_rng(seed)
        self.W = rng.multinomial(m, np.full(m, 1.0 / m), size=n_boot).astype(np.float64)

    def sums(self, mask):
        per_c = self.np.bincount(self.row_c, weights=mask.astype(self.np.float64), minlength=len(self.ids))
        return float(per_c.sum()), self.W @ per_c


def ratio(bt: Boot, num, den, scale: float = 1000.0) -> dict:
    np = bt.np
    k, kb = bt.sums(num)
    n, nb = bt.sums(den)
    with np.errstate(divide="ignore", invalid="ignore"):
        rb = np.where(nb > 0, kb / nb, np.nan) * scale
    rb = rb[~np.isnan(rb)]
    ci = [float(np.percentile(rb, 2.5)), float(np.percentile(rb, 97.5))] if len(rb) and n else [None, None]
    return {"k": int(round(k)), "n": int(round(n)), "per": (scale * k / n) if n else None, "ci": ci}


def residual(r: dict) -> bool:
    """unf_heldout_report.residual: U claim still contains a correct copy of the same dose elsewhere."""
    rest = re.sub(r"\s+", "", r["claim"][:r["surface_start"]] + " | " + r["claim"][r["surface_end"]:]).lower()
    return any(re.sub(r"\s+", "", x).lower() in rest for x in (r.get("mention") or "", r.get("evidence_span") or "") if x)


def fmt_rate(st: Optional[dict], pct: bool = True) -> str:
    if not st or st.get("rate") is None:
        return "NA"
    m = 100.0 if pct else 1.0
    n = st.get("den", st.get("n"))
    if st.get("lo") is None:
        return "%.1f (n=%s)" % (m * st["rate"], n)
    return "%.1f [%.1f, %.1f] (n=%s)" % (m * st["rate"], m * st["lo"], m * st["hi"], n)


def fmt_per(s: dict, nd: int = 1) -> str:
    if not s or s.get("per") is None:
        return "NA"
    lo, hi = s["ci"]
    return ("%.*f [%.*f, %.*f]" % (nd, s["per"], nd, lo, nd, hi)) if lo is not None else "%.*f" % (nd, s["per"])
