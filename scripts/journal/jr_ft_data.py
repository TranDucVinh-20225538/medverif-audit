#!/usr/bin/env python3
"""(C1) Training mixes for the second fine-tune: same dose pairs as the T15 MiniCheck-RoBERTa recipe
(data/t15/train.jsonl, non-ANLI rows) mixed with ANLI at ratio r = n_ANLI / n_dose in {0.5, 1, 2}.

  r = 1   : exactly the original data/t15/train.jsonl (sanity anchor; same rows as the published ft)
  r = 0.5 : dose rows + a seeded half of the original ANLI rows
  r = 2   : dose rows + original ANLI rows + extra ANLI train rows (HF `anli`, same loader/seed as
            scripts/t15_build_training_data.py, excluding every ANLI id already in train/dev)
Dev set = data/t15/dev.jsonl for every ratio (comparable model selection).
Output: .cache/journal/ft/ratio_<r>/{train,dev}.jsonl (not committed) + results/journal/ft/data_manifest.json
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jr_common import FT_DIR, ROOT, is_done, log, mark_done, read_jsonl, write_jsonl  # noqa: E402

STAGE = "C1_ft_data"
OUT = ROOT / ".cache/journal/ft"
RATIOS = ("0.5", "1", "2")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if is_done(STAGE) and not args.dry_run:
        log(STAGE, skipped="marker present")
        return
    train = read_jsonl(ROOT / "data/t15/train.jsonl")
    dev_path = ROOT / "data/t15/dev.jsonl"
    dev = read_jsonl(dev_path)
    if not train or not dev:
        raise SystemExit("data/t15/train.jsonl or dev.jsonl missing")
    dose = [r for r in train if r.get("variant") != "ANLI"]
    anli = [r for r in train if r.get("variant") == "ANLI"]
    used = {r["pair_id"] for r in train + dev if r.get("variant") == "ANLI"}
    n_dose = len(dose)
    man = {"n_dose_train": n_dose, "n_anli_in_t15_train": len(anli), "n_dev": len(dev),
           "dev_label_counts": dict(Counter(r["label"] for r in dev)), "ratios": {}}
    extra = []
    need_extra = max(0, 2 * n_dose - len(anli))
    if not args.dry_run and need_extra:
        try:
            from t15_build_training_data import _load_anli  # noqa: E402

            pool = _load_anli(need_extra + len(used) + 5000, args.seed + 1)
            extra = [r for r in pool if r["pair_id"] not in used][:need_extra]
        except Exception as exc:  # offline / dataset unavailable
            log(STAGE, anli_extra_error=str(exc)[:300])
    rng = random.Random(args.seed)
    for r in RATIOS:
        if r == "1":
            mix = list(train)
            note = "identical to data/t15/train.jsonl"
        elif r == "0.5":
            k = round(0.5 * n_dose)
            mix = dose + rng.sample(sorted(anli, key=lambda x: x["pair_id"]), min(k, len(anli)))
            note = "dose + seeded subset of original ANLI rows"
        else:
            k = 2 * n_dose
            got = anli + extra
            mix = dose + got[:k]
            note = "dose + original ANLI + %d extra ANLI rows" % min(len(extra), max(0, k - len(anli)))
            if len(got) < k:
                note += " (CAPPED: only %d ANLI rows available, ratio %.2f)" % (len(got), len(got) / n_dose)
        rng.shuffle(mix)
        n_anli = sum(1 for x in mix if x.get("variant") == "ANLI")
        man["ratios"][r] = {"n_train": len(mix), "n_anli": n_anli, "effective_ratio": round(n_anli / n_dose, 4),
                            "label_counts": dict(Counter(x["label"] for x in mix)), "note": note}
        if not args.dry_run:
            d = OUT / ("ratio_" + r)
            write_jsonl(d / "train.jsonl", mix)
            shutil.copyfile(dev_path, d / "dev.jsonl")
    log(STAGE, **man)
    if not args.dry_run:
        FT_DIR.mkdir(parents=True, exist_ok=True)
        (FT_DIR / "data_manifest.json").write_text(json.dumps(man, indent=2) + "\n")
        mark_done(STAGE, **{k: v for k, v in man.items() if k != "ratios"})


if __name__ == "__main__":
    main()
