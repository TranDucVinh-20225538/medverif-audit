#!/usr/bin/env python3
"""(UNF-ADV-2) Score the adversarial unit-spelling set and the RD-UNF pack with the 5 small checkers (CPU, resumable).

  --set adv     data/journal2/unf_adversarial.jsonl
                packs: orig (claim/evidence), unf (UNF v1 = the pre-specified fix: claim_unf/evidence_unf),
                       unf_v2 (POST-HOC v2 normalizer: claim_unf_v2/evidence_unf_v2)
                -> results/journal2/unf_adv/scores/<pack>/<checker>.jsonl
  --set rd_unf  results/journal2/impact/rd_unf_pack.jsonl (real-dose pairs whose text UNF v1 changes;
                written by scripts/journal2/impact_estimate.py)
                packs: orig (claim_orig/evidence_orig, same-run "before"), unf (claim_unf/evidence_unf)
                -> results/journal2/impact/rd_unf_scores/<pack>/<checker>.jsonl
Resumable by instance_id.  A row whose (claim, evidence) text is identical to a row already scored by the same
checker in another pack of the same set reuses that score (identical input; `reused_from` records the pack).
Checkers = scripts/journal2/small_checkers.py loaders (paper wrappers, thresholds, CPU patches):
  t6a_minicheck_roberta t6a_minicheck_deberta t6a_alignscore_base v2a_minicheck v3_alignscore
--mock: deterministic stub scorer (numeral+unit token overlap) for pipeline smoke tests without models; it writes
only under --outdir (default /tmp/unf_adv_mock) and tags rows env=MOCK.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ["MEDVERIF_M1"] = "0"  # never stack M1 on top of UNF

SETS = {
    "adv": {"data": ROOT / "data/journal2/unf_adversarial.jsonl", "out": ROOT / "results/journal2/unf_adv/scores",
            "packs": {"orig": ("claim", "evidence"), "unf": ("claim_unf", "evidence_unf"),
                      "unf_v2": ("claim_unf_v2", "evidence_unf_v2")}},
    "rd_unf": {"data": ROOT / "results/journal2/impact/rd_unf_pack.jsonl", "out": ROOT / "results/journal2/impact/rd_unf_scores",
               "packs": {"orig": ("claim_orig", "evidence_orig"), "unf": ("claim_unf", "evidence_unf")}},
}
CHECKERS = ("t6a_minicheck_roberta", "t6a_minicheck_deberta", "t6a_alignscore_base", "v2a_minicheck", "v3_alignscore")


def read_jsonl(p: Path) -> list:
    if not Path(p).is_file():
        return []
    return [json.loads(l) for l in Path(p).open(encoding="utf-8") if l.strip()]


_TOK = re.compile(r"\d+(?:[.,]\d+)?\s*[A-Za-zµμ/]+")


def mock_scorer():
    def fn(rows):
        out = []
        for r in rows:
            ct = {t.replace(" ", "").lower() for t in _TOK.findall(r["claim"])}
            et = {t.replace(" ", "").lower() for t in _TOK.findall(r["evidence"])}
            sc = (len(ct & et) / len(ct)) if ct else 0.0
            out.append({"instance_id": r["instance_id"], "score": sc, "verdict": "PASS" if sc > 0.5 else "FAIL"})
        return out
    return fn


def score_pack(rows: list, checker: str, out: Path, other_outs: dict, texts: dict, batch: int, limit: int, extra: dict,
               mock: bool) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {r["instance_id"] for r in read_jsonl(out)}
    todo = [r for r in rows if r["instance_id"] not in done]
    # reuse identical inputs already scored by this checker in another pack
    reuse = {}
    for pack, p in other_outs.items():
        for s in read_jsonl(p):
            key = texts[pack].get(s["instance_id"])
            if key is not None and s.get("verdict") in ("PASS", "FAIL"):
                reuse.setdefault(key, (pack, s))
    fresh, n_reused = [], 0
    with out.open("a", encoding="utf-8") as fh:
        for r in todo:
            hit = reuse.get((r["claim"], r["evidence"]))
            if hit:
                pack, s = hit
                fh.write(json.dumps({"instance_id": r["instance_id"], "score": s["score"], "verdict": s["verdict"],
                                     "verifier": checker, "reused_from": pack, **extra}) + "\n")
                n_reused += 1
            else:
                fresh.append(r)
    if limit:
        fresh = fresh[:limit]
    print(json.dumps({"score": checker, "out": str(out), "todo": len(todo), "reused": n_reused, "fresh": len(fresh)}), flush=True)
    if not fresh:
        return 0
    if mock:
        fn = mock_scorer()
        with out.open("a", encoding="utf-8") as fh:
            for r in fn(fresh):
                fh.write(json.dumps({**r, "verifier": checker, **extra}) + "\n")
        return len(fresh)
    import small_checkers as SC  # noqa: E402  (torch only needed for real scoring)

    return SC.score_rows(fresh, checker, out, batch=batch, extra=extra, label=out.parent.name)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", required=True, choices=list(SETS))
    ap.add_argument("--pack", default="all", help="pack name or 'all'")
    ap.add_argument("--checker", required=True, help="one id or 'all'")
    ap.add_argument("--limit", type=int, default=0, help="max FRESH rows per pack (smoke tests)")
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--ids", default="", help="comma-separated instance_ids to restrict to (smoke tests)")
    ap.add_argument("--outdir", default="")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()
    S = SETS[args.set]
    data = [r for r in read_jsonl(S["data"]) if r.get("valid", True)]
    if not data:
        raise SystemExit("no rows in %s (build it first)" % S["data"])
    if args.ids:
        keep = set(args.ids.split(","))
        data = [r for r in data if r["instance_id"] in keep]
    outroot = Path(args.outdir) if args.outdir else (Path("/tmp/unf_adv_mock") / args.set if args.mock else S["out"])
    packs = list(S["packs"]) if args.pack == "all" else [args.pack]
    texts = {p: {r["instance_id"]: (r[c], r[e]) for r in data} for p, (c, e) in S["packs"].items()}
    checkers = CHECKERS if args.checker == "all" else [args.checker]
    if args.mock:
        tag = {"env": "MOCK"}
    else:
        import small_checkers as SC

        try:
            import cpu_early as ce

            ce.ensure_nltk()
        except Exception as exc:  # noqa: BLE001
            print("nltk check:", exc)
        tag = SC.env_tag(os.environ.get("MEDVERIF_UNF_ENV", os.environ.get("MEDVERIF_SCORE_ENV_TAG", "box_cpu")))
    for ck in checkers:
        for pack in packs:
            c, e = S["packs"][pack]
            rows = [{"instance_id": r["instance_id"], "claim": r[c], "evidence": r[e], "base_id": r.get("base_id")} for r in data]
            others = {p: outroot / p / (ck + ".jsonl") for p in S["packs"] if p != pack}
            score_pack(rows, ck, outroot / pack / (ck + ".jsonl"), others, texts, args.batch, args.limit,
                       dict(pack=pack, set=args.set, **tag), args.mock)


if __name__ == "__main__":
    main()
