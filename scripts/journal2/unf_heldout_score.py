#!/usr/bin/env python3
"""(UNF-HO-3) Score the held-out UNF set and the RD pairs changed by UNF v1/v2 with the 5 small checkers (CPU, resumable).

  --set ho  data/journal2/unf_heldout.jsonl (S / U / anchor rows; parse-only rows are not scored)
            packs: orig (claim/evidence), unf (v1: claim_unf/evidence_unf), unf_v2 (FROZEN post-hoc v2)
            -> results/journal2/unf_heldout/scores/<pack>/<checker>.jsonl
  --set rd  results/journal2/unf_heldout/rd_pack.jsonl (RD pairs whose text v1 or v2 changes)
            packs: orig / unf / unf_v2 -> results/journal2/unf_heldout/rd_scores/<pack>/<checker>.jsonl
Resumable by instance_id.  Before any model call, a row reuses an existing score for the IDENTICAL (claim, evidence)
text from (1) another pack of the same set, (2) READ-ONLY caches of the UNF-ADV job (jr2_UNFADV.sbatch, e.g. HPC job
62104): results/journal2/unf_adv/scores/{orig,unf,unf_v2}/ and results/journal2/impact/rd_unf_scores/{orig,unf}/
(texts from data/journal2/unf_adversarial.jsonl and results/journal2/impact/rd_unf_pack.jsonl).  Those caches are only
read (a partially written last line is skipped), never written, so a still-running UNFADV job is not affected.
`reused_from` records the source.  --mock: deterministic stub scorer for smoke tests (writes under --outdir only).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ["MEDVERIF_M1"] = "0"
from unf_adv_score import CHECKERS, mock_scorer  # noqa: E402

PACKS3 = {"orig": ("claim", "evidence"), "unf": ("claim_unf", "evidence_unf"), "unf_v2": ("claim_unf_v2", "evidence_unf_v2")}
SETS = {
    "ho": {"data": ROOT / "data/journal2/unf_heldout.jsonl", "out": ROOT / "results/journal2/unf_heldout/scores",
           "packs": PACKS3, "keep": lambda r: r.get("family") in ("S", "U", "anchor")},
    "rd": {"data": ROOT / "results/journal2/unf_heldout/rd_pack.jsonl", "out": ROOT / "results/journal2/unf_heldout/rd_scores",
           "packs": {"orig": ("claim_orig", "evidence_orig"), "unf": ("claim_unf", "evidence_unf"),
                     "unf_v2": ("claim_unf_v2", "evidence_unf_v2")}, "keep": lambda r: True},
}
EXTERNAL = [  # (label, data file, pack -> (claim col, evidence col), score root)  -- UNF-ADV caches, read-only
    ("unfadv_adv", ROOT / "data/journal2/unf_adversarial.jsonl", PACKS3, ROOT / "results/journal2/unf_adv/scores"),
    ("unfadv_rd_unf", ROOT / "results/journal2/impact/rd_unf_pack.jsonl",
     {"orig": ("claim_orig", "evidence_orig"), "unf": ("claim_unf", "evidence_unf")}, ROOT / "results/journal2/impact/rd_unf_scores"),
]


def read_jsonl(p: Path) -> list:
    out = []
    if not Path(p).is_file():
        return out
    with Path(p).open(encoding="utf-8") as fh:
        for l in fh:
            if l.strip():
                try:
                    out.append(json.loads(l))
                except json.JSONDecodeError:  # concurrent writer: incomplete last line
                    continue
    return out


def reuse_map(checker: str, sets: list) -> dict:
    """(claim, evidence) -> (source, score row) from the given [(label, data rows, packs, score root)]."""
    out = {}
    for label, rows, packs, sroot in sets:
        for pack, (c, e) in packs.items():
            txt = {r["instance_id"]: (r.get(c), r.get(e)) for r in rows}
            for s in read_jsonl(Path(sroot) / pack / (checker + ".jsonl")):
                key = txt.get(s["instance_id"])
                if key and key[0] is not None and s.get("verdict") in ("PASS", "FAIL") and s.get("score") is not None:
                    out.setdefault(key, ("%s/%s" % (label, pack), s))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", required=True, choices=list(SETS))
    ap.add_argument("--checker", required=True, help="one id or 'all'")
    ap.add_argument("--pack", default="all")
    ap.add_argument("--limit", type=int, default=0, help="max FRESH rows per pack (smoke tests)")
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--outdir", default="")
    ap.add_argument("--no-external", action="store_true", help="do not reuse UNF-ADV caches")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()
    S = SETS[args.set]
    data = [r for r in read_jsonl(S["data"]) if r.get("valid", True) and S["keep"](r)]
    if not data:
        raise SystemExit("no rows in %s (build it first)" % S["data"])
    outroot = Path(args.outdir) if args.outdir else (Path("/tmp/unf_ho_mock") / args.set if args.mock else S["out"])
    packs = list(S["packs"]) if args.pack == "all" else [args.pack]
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
    ext = [] if args.no_external else [(l, read_jsonl(d), p, s) for l, d, p, s in EXTERNAL]
    for ck in checkers:
        for pack in packs:
            c, e = S["packs"][pack]
            out = outroot / pack / (ck + ".jsonl")
            out.parent.mkdir(parents=True, exist_ok=True)
            done = {r["instance_id"] for r in read_jsonl(out)}
            rows = [{"instance_id": r["instance_id"], "claim": r[c], "evidence": r[e], "base_id": r.get("base_id")}
                    for r in data if r["instance_id"] not in done]
            own = [("this/%s" % p, data, {p: S["packs"][p]}, outroot) for p in S["packs"] if p != pack]
            rmap = reuse_map(ck, own + ext)
            fresh, n_reused = [], 0
            with out.open("a", encoding="utf-8") as fh:
                for r in rows:
                    hit = rmap.get((r["claim"], r["evidence"]))
                    if hit:
                        src, s = hit
                        fh.write(json.dumps({"instance_id": r["instance_id"], "score": s["score"], "verdict": s["verdict"],
                                             "verifier": ck, "reused_from": src, "pack": pack, "set": "unfho_" + args.set,
                                             **tag}) + "\n")
                        n_reused += 1
                    else:
                        fresh.append(r)
            # identical texts inside the fresh list: score once, copy afterwards
            uniq, dup = {}, []
            for r in fresh:
                k = (r["claim"], r["evidence"])
                if k in uniq:
                    dup.append((r, uniq[k]))
                else:
                    uniq[k] = r
            todo = list(uniq.values())
            if args.limit:
                todo = todo[:args.limit]
            print(json.dumps({"set": args.set, "checker": ck, "pack": pack, "rows": len(data), "already": len(done),
                              "reused": n_reused, "fresh_unique": len(uniq), "scoring_now": len(todo)}), flush=True)
            extra = dict(pack=pack, set="unfho_" + args.set, **tag)
            if todo:
                if args.mock:
                    with out.open("a", encoding="utf-8") as fh:
                        for s in mock_scorer()(todo):
                            fh.write(json.dumps({**s, "verifier": ck, **extra}) + "\n")
                else:
                    import small_checkers as SC  # noqa: E402

                    SC.score_rows(todo, ck, out, batch=args.batch, extra=extra, label="unfho_%s/%s" % (args.set, pack))
            if dup:
                got = {s["instance_id"]: s for s in read_jsonl(out)}
                with out.open("a", encoding="utf-8") as fh:
                    for r, first in dup:
                        s = got.get(first["instance_id"])
                        if s and r["instance_id"] not in got:
                            fh.write(json.dumps({"instance_id": r["instance_id"], "score": s["score"], "verdict": s["verdict"],
                                                 "verifier": ck, "reused_from": "this/%s(dup)" % pack, **extra}) + "\n")


if __name__ == "__main__":
    main()
