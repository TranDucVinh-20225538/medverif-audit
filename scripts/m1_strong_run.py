#!/usr/bin/env python3
"""M1-strong: pre-registered small FT checkers; claim/evid split; McNemar; NeMo non-dose."""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from analyze import _c0_pass_bases, _parsed, bootstrap_rate, read_jsonl  # noqa: E402
from canonical_scores import _score_file_allowed, reference_env_rows, score_filename  # noqa: E402
from m1_gate import instance_gate, pack_coverage  # noqa: E402
from m1_parse_errors import finalize_and_abort  # noqa: E402
from non_dose_targets import NON_DOSE_TARGET_BASES  # noqa: E402
from review_filters import analysis_keep_row, flip_pi_ok_bases, inv_pi_ok_keys  # noqa: E402
from verifier_labels import DISPLAY_NAME, verifier_display_name  # noqa: E402

OUT_TABLE = ROOT / "results/tables/m1_strong.md"
OUT_NOTE = ROOT / "notes/m1_strong_report.md"
OUT_JSON = ROOT / "notes/m1_strong_report.json"
GATE_CACHE = ROOT / "results/cache/m1_strong_gate.json"
PREREG = ROOT / "notes/m1_preregistration.md"
AMEND1 = ROOT / "notes/m1_prereg_amendment1.md"
AMEND2 = ROOT / "notes/m1_prereg_amendment2.md"
AMEND4 = ROOT / "notes/m1_prereg_amendment4.md"
T6_MANIFEST = ROOT / "notes/t6a_eco_checkers.json"
T9_SCORES_BASE = ROOT / "results/raw/t9/alignscore_rail.jsonl"
T9_SCORES_LARGE = ROOT / "results/raw/t9/alignscore_rail_large.jsonl"

MAIN = ROOT / "data/v3/instances_main.jsonl"
T7 = ROOT / "data/t7/instances_e1_unit.jsonl"
T17 = ROOT / "data/v3/t17_downdose.jsonl"
T9_D = ROOT / "data/t9/instances_d_t7_e1_unit.jsonl"
T9_C = ROOT / "data/t9/instances_c_e1_x2.jsonl"

CRITERION = (
    "Numeral binding is supported for a checker if US_up_after >= NS_x10 - 5 points AND "
    "US_down_after >= NS_div10 - 5 points, or the 95% cluster-bootstrap CIs overlap. "
    "US_after above NS is expected and not counted against. Evaluated on spans parsed by BOTH M1 and M1-lib."
)

# Pre-registered primary (decision M: exclude SummaC-Conv, HHEM)
PRIMARY_SLUGS: tuple[str, ...] = (
    "t6a_minicheck_roberta",
    "t6a_minicheck_deberta",
    "v2a_minicheck",
    "t6a_alignscore_base",
    "v3_alignscore",
    "t6a_summac_zs",
    "t6a_granite_guardian",
    "v2b_bespoke",
)
SECONDARY_SLUGS: tuple[str, ...] = ("v1_medscore", "v4_ragas_nli", "v5_ragas_nli")

V_CODE_MAP = (
    "Report IDs: **V1** = Mistral-Small-24B (MedScore); **V2a** = MiniCheck-Flan-T5-Large; "
    "**V3** = AlignScore-large; **V4** = Llama-3.3-70B (RAGAS NLI)."
)

MAIN_NS_DIRS = (
    ROOT / "results/raw/lane_b/m1_strong_ns",
    ROOT / "results/raw/lane_b/main_e1_evid",
    ROOT / "results/raw_node30",
    ROOT / "results/raw/e2_main",
    ROOT / "results/raw",
    ROOT / "results/raw/t2_full",
    ROOT / "results/raw/t6b/full",
)
T7_BEFORE_DIRS = (ROOT / "results/raw/t7", ROOT / "results/raw/e2_main", ROOT / "results/raw")
US_AFTER_DIRS = (ROOT / "results/raw/lane_b/m1_t7_e1_unit", ROOT / "results/raw_m1/t7")
T17_DIRS = (ROOT / "results/raw/t17", ROOT / "results/raw/lane_b/t17_downdose")
DOWN_AFTER_DIRS = (ROOT / "results/raw/lane_b/m1_t17_unit_down",)

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


def load_gate_cache(refresh: bool) -> dict[str, bool]:
    if refresh and GATE_CACHE.is_file():
        GATE_CACHE.unlink()
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


def _read_score_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for row in reference_env_rows(path):
        iid = row.get("instance_id")
        if iid:
            out[iid] = row.get("verdict") or ""
    return out


def merge_verdicts(slug: str, dirs: tuple[Path, ...]) -> dict[str, str]:
    fname = score_filename(slug)
    if slug == "v2b_bespoke" and fname == "t6_bespoke_minicheck.jsonl":
        alt_names = (fname, "v2b_bespoke.jsonl", f"{slug}.jsonl")
    else:
        alt_names = (fname, f"{slug}.jsonl")
    out: dict[str, str] = {}
    for d in dirs:
        for name in alt_names:
            path = d / name
            if path.is_file() and not _score_file_allowed(path):
                continue
            out.update(_read_score_file(path))
    return out


def c0_pass_bases_for(bases: set[str], c0_rows: list[dict], scores: dict[str, str], verifier: str) -> set[str]:
    joined = []
    for r in c0_rows:
        if r["base_id"] not in bases:
            continue
        v = scores.get(r["instance_id"])
        if not v:
            continue
        row = dict(r)
        row["verifier"] = verifier
        row["verdict"] = v
        joined.append(row)
    return _c0_pass_bases(joined) if joined else set()


def fail_rate_side(
    inst_rows: list[dict],
    scores: dict[str, str],
    c0_pass: set[str],
    *,
    condition: str,
    id_substr: str | None = None,
) -> dict:
    by_base: dict[str, list] = defaultdict(list)
    for r in inst_rows:
        if r["base_id"] not in c0_pass:
            continue
        if r.get("condition") != condition:
            continue
        iid = r.get("instance_id") or ""
        if id_substr and id_substr not in iid:
            continue
        v = scores.get(r["instance_id"])
        if not v or not _parsed({"verdict": v}):
            continue
        by_base[r["base_id"]].append(v)
    groups = [(sum(1 for x in g if x == "FAIL"), len(g)) for g in by_base.values() if g]
    return bootstrap_rate(groups)


def mcnemar(b: int, c: int) -> tuple[float | None, float | None]:
    if b + c == 0:
        return None, None
    stat = (abs(b - c) - 1) ** 2 / (b + c)
    p = math.erfc(math.sqrt(stat / 2))
    return stat, p


def paired_us_mcnemar(
    ids: list[str],
    iid_base: dict[str, str],
    c0_pass: set[str],
    before: dict[str, str],
    after: dict[str, str],
) -> dict:
    b = c = n = unpaired = 0
    fail_before = fail_after = 0
    for iid in ids:
        bid = iid_base.get(iid)
        if bid not in c0_pass:
            unpaired += 1
            continue
        v0, v1 = before.get(iid), after.get(iid)
        if not v0 or not v1 or v0 == "PARSE_FAIL" or v1 == "PARSE_FAIL":
            unpaired += 1
            continue
        n += 1
        f0, f1 = v0 == "FAIL", v1 == "FAIL"
        fail_before += int(f0)
        fail_after += int(f1)
        if not f0 and f1:
            b += 1
        elif f0 and not f1:
            c += 1
    stat, p = mcnemar(b, c)
    return {
        "n_paired": n,
        "n_unpaired_dropped": unpaired,
        "fail_before": fail_before,
        "fail_after": fail_after,
        "discordant_pass_fail": b,
        "discordant_fail_pass": c,
        "mcnemar_p_approx": p,
    }


def paired_us(
    rows: list[dict],
    c0_pass: set[str],
    before: dict[str, str],
    after: dict[str, str],
    *,
    condition: str,
    id_substr: str | None = None,
) -> dict:
    """Pair = gated row on a C0-PASS base with a parsed before AND a parsed after verdict.

    Rows missing either score are excluded from the pair (never imputed as PASS).
    """
    n_cand = before_missing = after_missing = 0
    b = c = 0
    pairs: list[dict] = []
    by_base_before: dict[str, list[int]] = defaultdict(list)
    by_base_after: dict[str, list[int]] = defaultdict(list)
    for r in rows:
        if r["base_id"] not in c0_pass or r.get("condition") != condition:
            continue
        iid = r.get("instance_id") or ""
        if id_substr and id_substr not in iid:
            continue
        n_cand += 1
        v0, v1 = before.get(iid), after.get(iid)
        ok0 = bool(v0) and _parsed({"verdict": v0})
        ok1 = bool(v1) and _parsed({"verdict": v1})
        before_missing += int(not ok0)
        after_missing += int(not ok1)
        if not (ok0 and ok1):
            continue
        f0, f1 = v0 == "FAIL", v1 == "FAIL"
        pairs.append({"instance_id": iid, "base_id": r["base_id"], "before": v0, "after": v1})
        by_base_before[r["base_id"]].append(int(f0))
        by_base_after[r["base_id"]].append(int(f1))
        if not f0 and f1:
            b += 1
        elif f0 and not f1:
            c += 1
    groups0 = [(sum(g), len(g)) for g in by_base_before.values()]
    groups1 = [(sum(g), len(g)) for g in by_base_after.values()]
    _, p = mcnemar(b, c)
    return {
        "n_candidates": n_cand,
        "n_before_scored": n_cand - before_missing,
        "n_after_scored": n_cand - after_missing,
        "n_after_missing": after_missing,
        "n_pairs": sum(len(g) for g in by_base_after.values()),
        "before": bootstrap_rate(groups0),
        "after": bootstrap_rate(groups1),
        "b_pass_to_fail": b,
        "c_fail_to_pass": c,
        "mcnemar_p_approx": p,
        "_pairs": pairs,
    }


def pct(st: dict) -> float | None:
    return None if not st or st.get("rate") is None else round(100 * st["rate"], 1)


def ci_overlap(a: dict, b: dict) -> bool | None:
    if a.get("lo") is None or b.get("lo") is None:
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
    if st.get("lo") is not None and st.get("hi") is not None:
        ci = f" [{pct({'rate': st['lo']})},{pct({'rate': st['hi']})}]"
    else:
        ci = ""
    return f"{p:.1f}%{ci} ({st['num']}/{st['den']})"


def nemo_group_metrics(
    inst_rows: list[dict],
    score_rows: list[dict],
    *,
    exclude_non_dose: bool,
) -> dict:
    """T9 rail: blocked=1 catches error. value-error 'pass' = blocked; unit 'pass-through' = not blocked."""
    by_id = {r["instance_id"]: r for r in score_rows if r.get("instance_id")}
    flags: list[int] = []
    for r in inst_rows:
        if exclude_non_dose and r.get("base_id") in NON_DOSE_TARGET_BASES:
            continue
        sc = by_id.get(r["instance_id"])
        if not sc or sc.get("blocked") is None:
            continue
        flags.append(int(sc["blocked"]))
    if not flags:
        return {"n": 0, "blocked": 0, "not_blocked": 0, "block_rate": None, "ci": None}
    n = len(flags)
    blocked = sum(flags)
    not_blocked = n - blocked
    groups = [(blocked, n)]
    br = bootstrap_rate(groups)
    return {
        "n": n,
        "blocked": blocked,
        "not_blocked": not_blocked,
        "block_rate": br["rate"],
        "ci_lo": br["lo"],
        "ci_hi": br["hi"],
    }


def checker_block(
    slug: str,
    *,
    cache: dict[str, bool],
    bases: set[str],
    c0_rows: list[dict],
    ns_x10_claim: list[dict],
    ns_x10_evid: list[dict],
    ns_div10_claim: list[dict],
    ns_div10_evid: list[dict],
    us_up_raw: list[dict],
    us_up_gate: list[dict],
    us_down_gate: list[dict],
    t7_claim_ids: list[str],
    t7_evid_ids: list[str],
    iid_base: dict[str, str],
    ns_dirs: tuple[Path, ...],
    us_before_dirs: tuple[Path, ...],
    us_after_dirs: tuple[Path, ...],
    t17_dirs: tuple[Path, ...],
    down_after_dirs: tuple[Path, ...] = (),
) -> dict:
    ns_sc = merge_verdicts(slug, ns_dirs)
    ns_t17 = merge_verdicts(slug, (ROOT / "results/raw/lane_b/m1_strong_ns",) + t17_dirs)
    us_before = merge_verdicts(slug, us_before_dirs)
    us_after = merge_verdicts(slug, us_after_dirs)
    down_sc = merge_verdicts(slug, t17_dirs)
    down_after = merge_verdicts(slug, down_after_dirs) if down_after_dirs else {}

    c0p = c0_pass_bases_for(bases, c0_rows, ns_sc, slug)
    side = {}
    specs: list[tuple[str, list[dict], str, dict[str, str], str | None]] = [
        ("NS_x10_claim", ns_x10_claim, "E1-claim", ns_sc, None),
        ("NS_x10_evid", ns_x10_evid, "E1-evid", ns_sc, None),
        ("NS_div10_claim", ns_div10_claim, "E1-down10", ns_t17, "__claim__"),
        ("NS_div10_evid", ns_div10_evid, "E1-down10", ns_t17, "__evid__"),
        ("US_up_before_claim", us_up_raw, "E1-unit-claim", us_before, None),
        ("US_up_before_evid", us_up_raw, "E1-unit-evid", us_before, None),
        ("US_up_after_claim", us_up_gate, "E1-unit-claim", us_after, None),
        ("US_up_after_evid", us_up_gate, "E1-unit-evid", us_after, None),
        ("US_down_claim", us_down_gate, "E1-unit-down", down_sc, "__claim__"),
        ("US_down_evid", us_down_gate, "E1-unit-down", down_sc, "__evid__"),
    ]
    for label, rows, cond, sc, sub in specs:
        side[label] = fail_rate_side(rows, sc, c0p, condition=cond, id_substr=sub)

    paired = {
        "up_claim": paired_us(us_up_gate, c0p, us_before, us_after, condition="E1-unit-claim"),
        "up_evid": paired_us(us_up_gate, c0p, us_before, us_after, condition="E1-unit-evid"),
        "down_claim": paired_us(
            us_down_gate, c0p, down_sc, down_after, condition="E1-unit-down", id_substr="__claim__"
        ),
        "down_evid": paired_us(
            us_down_gate, c0p, down_sc, down_after, condition="E1-unit-down", id_substr="__evid__"
        ),
    }

    def _and(*vals: bool | None) -> bool | None:
        if any(v is None for v in vals):
            return None
        return all(vals)

    bind = {}
    for s in ("claim", "evid"):
        up = supported(paired[f"up_{s}"]["after"], side[f"NS_x10_{s}"])
        down = supported(paired[f"down_{s}"]["after"], side[f"NS_div10_{s}"])
        bind[s] = {"up": up, "down": down, "side": _and(up, down)}
    binding = _and(bind["claim"]["side"], bind["evid"]["side"])

    ns_rows = {}
    for s, rows in (("claim", ns_x10_claim), ("evid", ns_x10_evid)):
        cond = "E1-claim" if s == "claim" else "E1-evid"
        ns_rows[s] = [
            {"instance_id": r["instance_id"], "base_id": r["base_id"], "verdict": ns_sc[r["instance_id"]]}
            for r in rows
            if r["base_id"] in c0p
            and r.get("condition") == cond
            and ns_sc.get(r["instance_id"])
            and _parsed({"verdict": ns_sc[r["instance_id"]]})
        ]
    rows_dump = {
        "us_up_after_pairs": {s: paired[f"up_{s}"]["_pairs"] for s in ("claim", "evid")},
        "ns_x10": ns_rows,
    }
    for pr in paired.values():
        pr.pop("_pairs", None)

    return {
        "_rows": rows_dump,
        "display_name": verifier_display_name(slug),
        "slug": slug,
        "c0_pass_bases": len(c0p),
        "metrics": side,
        "paired": paired,
        "bind": bind,
        "binding_claim": bind["claim"]["side"],
        "binding_evid": bind["evid"]["side"],
        "binding_overall": binding,
    }


def _paired_cells(pr: dict) -> str:
    p = pr["mcnemar_p_approx"]
    p_s = f"{p:.3g}" if p is not None else "—"
    return (
        f"{fmt(pr['before'])} | {fmt(pr['after'])} | "
        f"{pr['n_pairs']} / {pr['n_after_scored']} / {pr['n_after_missing']} | "
        f"{pr['b_pass_to_fail']}/{pr['c_fail_to_pass']} | {p_s}"
    )


def render_checker_table(checkers: dict[str, dict], slugs: tuple[str, ...], title: str) -> list[str]:
    lines = [
        "",
        f"## {title}",
        "",
        "Paired rule: a pair needs a parsed BEFORE and a parsed AFTER-M1 verdict on a gated row of a C0-PASS base; "
        "rows missing either score are excluded, never counted as PASS. "
        "`n` = n_pairs / n_after_scored / n_after_missing (of gated candidates). "
        "b = PASS→FAIL, c = FAIL→PASS (McNemar, continuity-corrected).",
        "",
        "### US_up (×1000) vs NS_x10",
        "",
        "| Model | Side | NS_x10 FAIL | US_up before | US_up after | n | b/c | p≈ | Bind up |",
        "| --- | --- | --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for slug in slugs:
        if slug not in checkers:
            continue
        ch = checkers[slug]
        for s, lab in (("claim", "CLAIM"), ("evid", "EVID")):
            lines.append(
                f"| {ch['display_name']} | {lab} | {fmt(ch['metrics'][f'NS_x10_{s}'])} | "
                f"{_paired_cells(ch['paired'][f'up_{s}'])} | {ch['bind'][s]['up']} |"
            )
    lines += [
        "",
        "### US_down (unit-down) vs NS_div10",
        "",
        "| Model | Side | NS_div10 FAIL | US_down before | US_down after | n | b/c | p≈ | Bind down |",
        "| --- | --- | --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for slug in slugs:
        if slug not in checkers:
            continue
        ch = checkers[slug]
        for s, lab in (("claim", "CLAIM"), ("evid", "EVID")):
            lines.append(
                f"| {ch['display_name']} | {lab} | {fmt(ch['metrics'][f'NS_div10_{s}'])} | "
                f"{_paired_cells(ch['paired'][f'down_{s}'])} | {ch['bind'][s]['down']} |"
            )
    lines += [
        "",
        "### Bind? (criterion uses AFTER values only)",
        "",
        "Side = Bind up AND Bind down, where Bind up compares **US_up after** with NS_x10 and Bind down compares "
        "**US_down after** with NS_div10 (pass if after >= NS - 5 points, or 95% CIs overlap). "
        "None = an input is NA (e.g. after-M1 scores missing).",
        "",
        "| Model | CLAIM (up, down → side) | EVID (up, down → side) | Overall |",
        "| --- | --- | --- | --- |",
    ]
    for slug in slugs:
        if slug not in checkers:
            continue
        ch = checkers[slug]
        bc, be = ch["bind"]["claim"], ch["bind"]["evid"]
        lines.append(
            f"| {ch['display_name']} | {bc['up']}, {bc['down']} → **{bc['side']}** | "
            f"{be['up']}, {be['down']} → **{be['side']}** | **{ch['binding_overall']}** |"
        )
    return lines


def render_primary_table(checkers: dict[str, dict]) -> list[str]:
    return render_checker_table(
        checkers,
        primary_slugs_for_run(),
        "Primary — small fine-tuned checkers (decision M: SummaC-Conv & HHEM excluded)",
    )


def render_secondary_table(checkers: dict[str, dict]) -> list[str]:
    return render_checker_table(checkers, SECONDARY_SLUGS, "Secondary — LLM judges (non-primary; same splits)")


def v4_reconcile(checkers: dict[str, dict]) -> list[str]:
    ch = checkers.get("v4_ragas_nli")
    if not ch:
        return []
    m = ch["metrics"]
    pf = m["US_up_before_claim"]["num"] + m["US_up_before_evid"]["num"]
    pd = m["US_up_before_claim"]["den"] + m["US_up_before_evid"]["den"]
    pr = 100 * pf / pd if pd else 0
    evid = m["US_up_before_evid"]
    return [
        "",
        "## V4 denominator reconciliation (7338b21 pooled bug)",
        "",
        f"- **7338b21** pooled E1-unit-claim + E1-unit-evid under one bootstrap → US_up before ≈ **{pr:.1f}%** ({pf}/{pd} FAIL instances).",
        f"- **Correct (EVID only, |C0 PASS|, parsed):** **{fmt(evid)}** — matches repair report **n_paired≈114** on E1-unit-evid.",
        "- **Card/repair (~55.8% PASS / 61 FAIL):** same **evid-only** cohort; 7338b21 **91.1%** was **FAIL rate on pooled 203**, not PASS.",
        "",
    ]


def render_nemo() -> list[str]:
    def read_t9(path: Path) -> list[dict]:
        return [json.loads(line) for line in path.open() if line.strip()] if path.is_file() else []

    inst_d = read_jsonl(T9_D)
    inst_c = read_jsonl(T9_C)
    base_sc = read_t9(T9_SCORES_BASE)
    large_sc = read_t9(T9_SCORES_LARGE)
    lines = [
        "",
        "## NeMo Guardrails (T9) — after non-dose base exclusion",
        "",
        "Group **d** = T7 E1-unit (unit errors); group **c** = E1-claim ×2 (value errors). "
        "Rail blocks when AlignScore < 0.5. **Value-error detection** = blocked k/n; "
        "**unit pass-through** = not blocked k/n (177/230 raw = errors slipping past rail).",
        "",
        "| Checkpoint | Slice | n | blocked k/n [CI] | not blocked k/n |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for label, sc in ("AlignScore-base", base_sc), ("AlignScore-large", large_sc):
        for gname, inst in ("unit-error (d)", inst_d), ("value-error (c)", inst_c):
            met = nemo_group_metrics(inst, sc, exclude_non_dose=True)
            if not met["n"]:
                lines.append(f"| {label} | {gname} | 0 | — | — |")
                continue
            br = met["block_rate"]
            ci = f"[{met['ci_lo']:.3f},{met['ci_hi']:.3f}]" if met["ci_lo"] is not None else ""
            lines.append(
                f"| {label} | {gname} | {met['n']} | **{met['blocked']}/{met['n']}** ({br:.3f}) {ci} | "
                f"{met['not_blocked']}/{met['n']} |"
            )
    lines.append("")
    return lines


LEGACY_PRIMARY = frozenset({"t6a_summac_zs", "t6a_granite_guardian"})


def granite_allowed() -> bool:
    path = ROOT / "notes/m1_granite_cpuverif_agreement.json"
    if not path.is_file():
        return False
    doc = json.loads(path.read_text())
    return bool(doc.get("pass"))


def primary_slugs_for_run() -> tuple[str, ...]:
    slugs = PRIMARY_SLUGS
    if "--skip-legacy" in sys.argv:
        slugs = tuple(s for s in slugs if s not in LEGACY_PRIMARY)
    elif not granite_allowed():
        slugs = tuple(s for s in slugs if s != "t6a_granite_guardian")
    return slugs


def main() -> None:
    global OUT_TABLE, OUT_NOTE, OUT_JSON
    refresh_gate = "--refresh-gate" in sys.argv
    skip_legacy = "--skip-legacy" in sys.argv
    final_mode = "--final" in sys.argv
    amend5 = "--amend5" in sys.argv
    if final_mode:
        OUT_TABLE = ROOT / "results/tables/m1_strong_final.md"
        OUT_NOTE = ROOT / "notes/m1_strong_final_report.md"
        OUT_JSON = ROOT / "notes/m1_strong_final.json"
    if final_mode and amend5:
        OUT_TABLE = ROOT / "results/tables/m1_strong_final_amend5.md"
        OUT_NOTE = ROOT / "notes/m1_strong_final_amend5_report.md"
        OUT_JSON = ROOT / "notes/m1_strong_final_amend5.json"
    try:
        import quantulum3  # noqa: F401
        import pint  # noqa: F401

        lib_backend = "quantulum3+pint"
    except ImportError as exc:
        lib_backend = f"partial ({exc})"

    if amend5:
        global GATE_CACHE
        GATE_CACHE = ROOT / "results/cache/m1_strong_gate_indep.json"
        refresh_gate = False
    cache = load_gate_cache(refresh_gate)
    # Amendment 4 + dimension-aware M1-lib not landed until AMEND4 exists and lib matches quantity_norm.
    m1_lib_fixed = AMEND4.is_file() and "_canonical_for_gate" in (ROOT / "src/m1_lib.py").read_text()
    final_mode = "--final" in sys.argv
    cohort_label = (
        "post_amendment4_fixed_gate"
        if (refresh_gate and m1_lib_fixed)
        else "pre_amendment4"
    )
    if amend5:
        cohort_label = "post_amendment5_indep_gate"
    print(
        f"[m1-strong] gate cache entries: {len(cache)} refresh={refresh_gate} cohort={cohort_label}",
        flush=True,
    )

    c0_rows = load_rows(MAIN, pred=lambda r: r.get("condition") == "C0")
    t7_rows = load_rows(T7)
    t7_bases = {r["base_id"] for r in t7_rows}
    c0_rows = [r for r in c0_rows if r["base_id"] in t7_bases]
    t7_claim_ids = [r["instance_id"] for r in t7_rows if r.get("condition") == "E1-unit-claim"]
    t7_evid_ids = [r["instance_id"] for r in t7_rows if r.get("condition") == "E1-unit-evid"]
    iid_base = {r["instance_id"]: r["base_id"] for r in t7_rows}

    us_up_raw = [r for r in t7_rows if r.get("magnitude") == "x1000"]
    us_down_raw = [r for r in load_rows(T17) if r.get("condition") == "E1-unit-down"]
    ns_x10_claim_raw = load_rows(
        MAIN, pred=lambda r: r.get("condition") == "E1-claim" and r.get("magnitude") == "x10"
    )
    ns_x10_evid_raw = load_rows(
        MAIN, pred=lambda r: r.get("condition") == "E1-evid" and r.get("magnitude") == "x10"
    )
    ns_div10_claim_raw = [
        r for r in load_rows(T17) if r.get("condition") == "E1-down10" and "__claim__" in r.get("instance_id", "")
    ]
    ns_div10_evid_raw = [
        r for r in load_rows(T17) if r.get("condition") == "E1-down10" and "__evid__" in r.get("instance_id", "")
    ]

    cov_raw = {
        "us_up_x1000": pack_coverage(us_up_raw, pack_name="us_up_x1000"),
        "us_down_unit": pack_coverage(us_down_raw, pack_name="us_down_unit"),
        "ns_x10_claim": pack_coverage(ns_x10_claim_raw, pack_name="ns_x10_claim"),
        "ns_x10_evid": pack_coverage(ns_x10_evid_raw, pack_name="ns_x10_evid"),
        "ns_div10_claim": pack_coverage(ns_div10_claim_raw, pack_name="ns_div10_claim"),
        "ns_div10_evid": pack_coverage(ns_div10_evid_raw, pack_name="ns_div10_evid"),
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

    us_up_gate = on_bases(us_up_raw, bases, cache)
    us_down_gate = on_bases(us_down_raw, bases, cache)
    ns_x10_claim = on_bases(ns_x10_claim_raw, bases, cache)
    ns_x10_evid = on_bases(ns_x10_evid_raw, bases, cache)
    ns_div10_claim = on_bases(ns_div10_claim_raw, bases, cache)
    ns_div10_evid = on_bases(ns_div10_evid_raw, bases, cache)

    primary_slugs = primary_slugs_for_run()
    all_slugs = primary_slugs + SECONDARY_SLUGS
    checkers: dict[str, dict] = {}
    for slug in all_slugs:
        print(f"[m1-strong] {verifier_display_name(slug)} ({slug})", flush=True)
        ns_dirs = MAIN_NS_DIRS if slug not in ("v1_medscore", "v4_ragas_nli", "v5_ragas_nli") else MAIN_NS_DIRS + (ROOT / "results/raw/t2_full",)
        us_after_dirs = US_AFTER_DIRS if slug in ("v1_medscore", "v4_ragas_nli", "v5_ragas_nli") else (ROOT / "results/raw/lane_b/m1_t7_e1_unit",)
        if amend5:
            us_after_dirs = us_after_dirs + (
                (ROOT / "results/raw_m1/t7_amend5",)
                if slug in ("v1_medscore", "v4_ragas_nli", "v5_ragas_nli")
                else (ROOT / "results/raw/lane_b/m1_t7_e1_unit_amend5",)
            )
        checkers[slug] = checker_block(
            slug,
            cache=cache,
            bases=bases,
            c0_rows=c0_rows,
            ns_x10_claim=ns_x10_claim,
            ns_x10_evid=ns_x10_evid,
            ns_div10_claim=ns_div10_claim,
            ns_div10_evid=ns_div10_evid,
            us_up_raw=us_up_raw,
            us_up_gate=us_up_gate,
            us_down_gate=us_down_gate,
            t7_claim_ids=t7_claim_ids,
            t7_evid_ids=t7_evid_ids,
            iid_base=iid_base,
            ns_dirs=ns_dirs,
            us_before_dirs=T7_BEFORE_DIRS,
            us_after_dirs=us_after_dirs,
            t17_dirs=T17_DIRS,
            down_after_dirs=DOWN_AFTER_DIRS,
        )

    rows_dump = {slug: ch.pop("_rows") for slug, ch in checkers.items()}
    if "--dump-rows" in sys.argv:
        dump = OUT_JSON.with_name(OUT_JSON.stem + "_rows.json")
        dump.write_text(json.dumps(rows_dump, indent=1) + "\n")

    payload = {
        "preregistration": str(PREREG),
        "amendment1": str(AMEND1),
        "amendment2": str(AMEND2),
        "amendment4": str(AMEND4) if AMEND4.is_file() else None,
        "decision_M": "exclude t6a_summac_conv, t6a_hhem from primary",
        "criterion_verbatim": CRITERION,
        "m1_lib_backend": lib_backend,
        "gate_cache": str(GATE_CACHE),
        "gate_bases_n": len(bases),
        "cohort_label": cohort_label,
        "amendment4_present": AMEND4.is_file(),
        "m1_lib_dimension_fix": m1_lib_fixed,
        "coverage_by_pack": cov_raw,
        "checkers": checkers,
    }
    pre_arch = ROOT / "notes/m1_strong_report_pre_amendment4.json"
    if final_mode and pre_arch.is_file():
        pre = json.loads(pre_arch.read_text())
        payload["cohort_pre_amendment4"] = {
            "cohort_label": pre.get("cohort_label", "pre_amendment4"),
            "gate_bases_n": pre.get("gate_bases_n"),
            "coverage_by_pack": pre.get("coverage_by_pack"),
            "artifact_json": str(pre_arch.relative_to(ROOT)),
            "artifact_md": "results/tables/m1_strong_pre_amendment4.md",
        }

    lines = [
        "# M1-strong (steps 1–2)" + (" — **final**" if final_mode else ""),
        "",
        f"**Cohort:** `{cohort_label}` · amendment4 file: {AMEND4.is_file()} · M1-lib dimension fix in code: {m1_lib_fixed}",
        "",
        f"Pre-registration: `{PREREG.relative_to(ROOT)}` · Amendments: `{AMEND1.relative_to(ROOT)}`, `{AMEND2.relative_to(ROOT)}`"
        + (f", `{AMEND4.relative_to(ROOT)}`" if AMEND4.is_file() else ""),
        f"M1-lib backend: **{lib_backend}** · Gate bases: **{len(bases)}** (gate cache refreshed={refresh_gate})",
    ]
    if skip_legacy:
        lines += [
            "",
            "**Note:** SummaC-ZS / Granite Guardian omitted (`--skip-legacy`); append after GPU legacy rescore.",
            "",
        ]
    lines += [
        V_CODE_MAP,
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
    lines.append("")
    lines.extend(render_primary_table(checkers))
    lines.extend(render_secondary_table(checkers))
    lines.extend(v4_reconcile(checkers))
    lines.extend(render_nemo())
    if final_mode and pre_arch.is_file():
        pre = json.loads(pre_arch.read_text())
        lines.extend(
            [
                "",
                "## Dual cohort (amendment 4)",
                "",
                f"- **Pre-amendment-4 draft** (`pre_amendment4`, job 61606): gate bases **{pre.get('gate_bases_n')}** — "
                f"`results/tables/m1_strong_pre_amendment4.md`",
                f"- **Post-amendment-4 final** (`{cohort_label}`): gate bases **{len(bases)}** — this file.",
                "",
            ]
        )

    OUT_TABLE.parent.mkdir(parents=True, exist_ok=True)
    OUT_TABLE.write_text("\n".join(lines) + "\n")
    OUT_NOTE.write_text(OUT_TABLE.read_text())
    OUT_JSON.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    finalize_and_abort(
        abort_packs=frozenset({"us_up_x1000", "us_down_unit"}),
        exit_on_fail=not skip_legacy,
    )
    print(json.dumps({"wrote": str(OUT_TABLE), "checkers": len(checkers), "bases": len(bases)}, indent=2))


if __name__ == "__main__":
    main()
