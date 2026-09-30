#!/usr/bin/env python3
"""M1-strong steps 1–2: coverage gate, causal US_up/US_down vs NS_x10/NS_div10."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from analyze import _c0_pass_bases, _parsed, bootstrap_rate, read_jsonl  # noqa: E402
from m1_gate import instance_gate, pack_coverage  # noqa: E402
from review_filters import analysis_keep_row, flip_pi_ok_bases, inv_pi_ok_keys  # noqa: E402

OUT_TABLE = ROOT / "results/tables/m1_strong.md"
OUT_NOTE = ROOT / "notes/m1_strong_report.md"
OUT_JSON = ROOT / "notes/m1_strong_report.json"
GATE_CACHE = ROOT / "results/cache/m1_strong_gate.json"
PREREG = ROOT / "notes/m1_preregistration.md"
AMEND = ROOT / "notes/m1_prereg_amendment1.md"

MAIN = ROOT / "data/v3/instances_main.jsonl"
T7 = ROOT / "data/t7/instances_e1_unit.jsonl"
T17 = ROOT / "data/v3/t17_downdose.jsonl"

CRITERION = (
    "Numeral binding is supported for a checker if US_up_after >= NS_x10 - 5 points AND "
    "US_down_after >= NS_div10 - 5 points, or the 95% cluster-bootstrap CIs overlap. "
    "US_after above NS is expected and not counted against. Evaluated on spans parsed by BOTH M1 and M1-lib."
)

LOCAL_VERIFIERS = (
    ("v2a_minicheck", "V2a"),
    ("v3_alignscore", "V3"),
    ("t6_minicheck_roberta", "MiniCheck-RoBERTa"),
    ("t6_alignscore_base", "AlignScore-base"),
    ("t6_minicheck_deberta", "MiniCheck-DeBERTa"),
    ("v2b_bespoke", "Bespoke"),
)
API_VERIFIERS = (
    ("v1_medscore", "V1-Mistral24B", ROOT / "results/raw", ROOT / "results/raw_m1"),
    ("v4_ragas_nli", "V4-Llama70B", ROOT / "results/raw/t7", ROOT / "results/raw_m1/t7"),
)

T17_OR = ROOT / "results/raw/t17"
T17_CPU = ROOT / "results/raw/lane_b/t17_downdose"
US_M1 = ROOT / "results/raw/lane_b/m1_t7_e1_unit"

_FLIP_Y = flip_pi_ok_bases()
_INV_KEYS = inv_pi_ok_keys()


def load_rows(path: Path, *, pred=None) -> list[dict]:
    out = []
    for r in read_jsonl(path):
        if not r.get("valid", True):
            continue
        if not analysis_keep_row(r, flip_y=_FLIP_Y, inv_keys=_INV_KEYS):
            continue
        if pred and not pred(r):
            continue
        out.append(r)
    return out


def load_gate_cache() -> dict[str, bool]:
    if GATE_CACHE.is_file():
        return json.loads(GATE_CACHE.read_text())
    return {}


def save_gate_cache(cache: dict[str, bool]) -> None:
    GATE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    GATE_CACHE.write_text(json.dumps(cache, indent=2) + "\n")


def gate_pass(row: dict, cache: dict[str, bool]) -> bool:
    iid = row.get("instance_id") or ""
    if iid in cache:
        return cache[iid]
    ok, _ = instance_gate(row)
    cache[iid] = ok
    return ok


def filter_gate(rows: list[dict], cache: dict[str, bool]) -> list[dict]:
    return [r for r in rows if gate_pass(r, cache)]


def gate_bases(*row_lists: list[dict], cache: dict[str, bool]) -> set[str]:
    out: set[str] = set()
    for rows in row_lists:
        for r in rows:
            if gate_pass(r, cache):
                out.add(r["base_id"])
    return out


def on_bases(rows: list[dict], bases: set[str], cache: dict[str, bool]) -> list[dict]:
    return [r for r in rows if r["base_id"] in bases and gate_pass(r, cache)]


def load_scores(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    out: dict[str, dict] = {}
    for line in path.open():
        if line.strip():
            row = json.loads(line)
            if row.get("instance_id"):
                out[row["instance_id"]] = row
    return out


def score_path(base: Path, slug: str) -> Path:
    if slug == "v4_ragas_nli":
        for name in ("v4_ragas_nli.llama.jsonl", "v4_ragas_nli.jsonl"):
            p = base / name
            if p.is_file():
                return p
    return base / f"{slug}.jsonl"


def merge_scores(*paths: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in paths:
        sp = p if p.suffix == ".jsonl" else score_path(p, p.name.replace(".jsonl", ""))
        if sp.is_file():
            out.update(load_scores(sp))
        elif p.is_dir():
            for slug, _ in LOCAL_VERIFIERS:
                out.update(load_scores(score_path(p, slug)))
    return out


def load_checker_scores(slug: str, ns_dir: Path, us_dir: Path, t17_dirs: tuple[Path, ...]) -> tuple[dict, dict]:
    sb = load_scores(score_path(ns_dir, slug))
    for d in t17_dirs:
        sb.update(load_scores(score_path(d, slug)))
    sa = load_scores(score_path(us_dir, slug))
    return sb, sa


def c0_pass_bases_for(bases: set[str], c0_rows: list[dict], scores: dict[str, dict], verifier: str) -> set[str]:
    joined = []
    for r in c0_rows:
        if r["base_id"] not in bases:
            continue
        sc = scores.get(r["instance_id"])
        if not sc:
            continue
        row = dict(r)
        row["verifier"] = verifier
        row["verdict"] = sc.get("verdict")
        joined.append(row)
    return _c0_pass_bases(joined) if joined else set()


def fail_rate(
    inst_rows: list[dict],
    scores: dict[str, dict],
    c0_pass: set[str],
    *,
    condition: str | tuple[str, ...],
) -> dict:
    conds = (condition,) if isinstance(condition, str) else condition
    by_base: dict[str, list] = defaultdict(list)
    for r in inst_rows:
        if r["base_id"] not in c0_pass:
            continue
        if r.get("condition") not in conds:
            continue
        sc = scores.get(r["instance_id"])
        if not sc or not _parsed({"verdict": sc.get("verdict")}):
            continue
        by_base[r["base_id"]].append(sc.get("verdict"))
    groups = [(sum(1 for v in g if v == "FAIL"), len(g)) for g in by_base.values() if g]
    return bootstrap_rate(groups)


def pct(st: dict) -> float | None:
    return None if not st or st.get("rate") is None else round(100 * st["rate"], 1)


def ci_overlap(a: dict, b: dict) -> bool | None:
    if not a.get("lo") or not b.get("lo"):
        return None
    return not (a["hi"] < b["lo"] or b["hi"] < a["lo"])


def supported(us: dict, ns: dict) -> bool | None:
    pu, pn = pct(us), pct(ns)
    if pu is None or pn is None:
        return None
    if ci_overlap(us, ns):
        return True
    return pu >= pn - 5.0


def fmt(st: dict) -> str:
    p = pct(st)
    if p is None:
        return "NA"
    lo, hi = pct({"rate": st["lo"]}), pct({"rate": st["hi"]}) if st.get("lo") else (None, None)
    ci = f" [{lo},{hi}]" if lo is not None else ""
    return f"{p:.1f}%{ci} ({st['num']}/{st['den']})"


def main() -> None:
    try:
        import quantulum3  # noqa: F401
        import pint  # noqa: F401

        lib_backend = "quantulum3+pint"
    except ImportError as exc:
        lib_backend = f"partial ({exc})"

    cache = load_gate_cache()
    print(f"[m1-strong] gate cache entries: {len(cache)}", flush=True)

    c0_rows = load_rows(MAIN, pred=lambda r: r.get("condition") == "C0")
    t7_rows = load_rows(T7)
    t17_rows = load_rows(T17)

    us_up_raw = [r for r in t7_rows if r.get("magnitude") == "x1000"]
    us_down_raw = [r for r in t17_rows if r.get("condition") == "E1-unit-down"]
    ns_x10_claim_raw = load_rows(
        MAIN, pred=lambda r: r.get("condition") == "E1-claim" and r.get("magnitude") == "x10"
    )
    ns_x10_evid_raw = load_rows(
        MAIN, pred=lambda r: r.get("condition") == "E1-evid" and r.get("magnitude") == "x10"
    )
    ns_div10_claim_raw = [
        r for r in t17_rows if r.get("condition") == "E1-down10" and "__claim__" in r.get("instance_id", "")
    ]
    ns_div10_evid_raw = [
        r for r in t17_rows if r.get("condition") == "E1-down10" and "__evid__" in r.get("instance_id", "")
    ]

    cov_raw = {
        "us_up_x1000": pack_coverage(us_up_raw),
        "us_down_unit": pack_coverage(us_down_raw),
        "ns_x10_claim": pack_coverage(ns_x10_claim_raw),
        "ns_x10_evid": pack_coverage(ns_x10_evid_raw),
        "ns_div10_claim": pack_coverage(ns_div10_claim_raw),
        "ns_div10_evid": pack_coverage(ns_div10_evid_raw),
    }

    bases = gate_bases(
        us_up_raw,
        us_down_raw,
        ns_x10_claim_raw,
        ns_x10_evid_raw,
        ns_div10_claim_raw,
        ns_div10_evid_raw,
        cache=cache,
    )
    save_gate_cache(cache)

    us_up_pool = on_bases(us_up_raw, bases, cache)
    us_down_pool = on_bases(us_down_raw, bases, cache)
    ns_x10_claim = on_bases(ns_x10_claim_raw, bases, cache)
    ns_x10_evid = on_bases(ns_x10_evid_raw, bases, cache)
    ns_div10_claim = on_bases(ns_div10_claim_raw, bases, cache)
    ns_div10_evid = on_bases(ns_div10_evid_raw, bases, cache)

    payload: dict = {
        "preregistration": str(PREREG),
        "amendment": str(AMEND),
        "criterion_verbatim": CRITERION,
        "m1_lib_backend": lib_backend,
        "gate_cache": str(GATE_CACHE),
        "gate_bases_n": len(bases),
        "coverage_by_pack": cov_raw,
        "cohorts": {
            "gate_bases": len(bases),
            "us_up_n": len(us_up_pool),
            "us_down_n": len(us_down_pool),
            "ns_x10_claim_n": len(ns_x10_claim),
            "ns_x10_evid_n": len(ns_x10_evid),
            "ns_div10_claim_n": len(ns_div10_claim),
            "ns_div10_evid_n": len(ns_div10_evid),
        },
        "checkers": {},
    }

    lines = [
        "# M1-strong (steps 1–2)",
        "",
        f"Pre-registration: `{PREREG.relative_to(ROOT)}` · Amendment: `{AMEND.relative_to(ROOT)}`",
        f"M1-lib backend: **{lib_backend}** · Gate bases: **{len(bases)}**",
        "",
        "## Criterion (verbatim)",
        "",
        f"> {CRITERION}",
        "",
        "## Coverage by pack (edited target spans; before US/NS metrics)",
        "",
        "| Pack | instances | inst gate pass | target spans | M1 only | M1-lib only | both |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key, c in cov_raw.items():
        lines.append(
            f"| {key} | {c['instances']} | {c['instances_gate_pass']} | {c['edited_target_spans']} | "
            f"{c['spans_m1_only']} | {c['spans_m1_lib_only']} | {c['spans_both']} |"
        )
    lines.extend(
        [
            "",
            f"Cohort intersection: **{len(bases)}** bases with ≥1 gated instance across causal packs.",
            "",
            "| Checker | NS_x10 evid (gate) | US_up before (all ×1000) | US_up after (gate) | NS_div10 evid | US_down | binding? |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    t17_dirs = (T17_OR, T17_CPU)

    def eval_verifier(slug: str, label: str, ns_dir: Path, us_dir: Path) -> None:
        print(f"[m1-strong] checker {label} ({slug})", flush=True)
        sb, sa = load_checker_scores(slug, ns_dir, us_dir, t17_dirs)
        if not sb and not sa:
            return
        c0p = c0_pass_bases_for(bases, c0_rows, sb, slug)
        ns_e = fail_rate(ns_x10_evid, sb, c0p, condition="E1-evid")
        ns_d = fail_rate(ns_div10_evid, sb, c0p, condition="E1-down10") if ns_div10_evid else {"rate": None, "den": 0}
        us_before = fail_rate(us_up_raw, sa, c0p, condition=("E1-unit-claim", "E1-unit-evid"))
        us_after = fail_rate(us_up_pool, sa, c0p, condition=("E1-unit-claim", "E1-unit-evid"))
        us_down = fail_rate(us_down_pool, sa, c0p, condition="E1-unit-down") if us_down_pool else {"rate": None, "den": 0}
        bind = None
        if us_after.get("rate") is not None and ns_e.get("rate") is not None:
            up_ok = supported(us_after, ns_e)
            down_ok = supported(us_down, ns_d) if us_down.get("den") else None
            if up_ok is not None and down_ok is None:
                bind = up_ok
            elif up_ok is not None and down_ok is not None:
                bind = up_ok and down_ok
        payload["checkers"][slug] = {
            "label": label,
            "NS_x10_evid": ns_e,
            "NS_div10_evid": ns_d,
            "US_up_before": us_before,
            "US_up_after": us_after,
            "US_down_after": us_down,
            "numeral_binding_supported": bind,
        }
        lines.append(
            f"| {label} | {fmt(ns_e)} | {fmt(us_before)} | {fmt(us_after)} | "
            f"{fmt(ns_d) if ns_div10_evid else 'pending'} | "
            f"{fmt(us_down) if us_down_pool else 'pending T17 unit-down'} | "
            f"{bind if bind is not None else 'pending'} |"
        )

    seen: set[str] = set()
    for slug, label in LOCAL_VERIFIERS:
        eval_verifier(slug, label, ROOT / "results/raw", US_M1)
        seen.add(slug)
    for slug, label, _raw_d, m1_d in API_VERIFIERS:
        if slug in seen:
            continue
        eval_verifier(slug, label, ROOT / "results/raw", m1_d)

    OUT_TABLE.parent.mkdir(parents=True, exist_ok=True)
    OUT_TABLE.write_text("\n".join(lines) + "\n")
    OUT_NOTE.write_text(OUT_TABLE.read_text())
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"wrote": str(OUT_TABLE), "checkers": len(payload["checkers"]), "bases": len(bases)}, indent=2))


if __name__ == "__main__":
    main()
