#!/usr/bin/env python3
"""(RD2-4b) Chain-3 local scorers on RD2, through the UNCHANGED chain-3 code paths.  Python >= 3.8.

  --what judge  scripts/journal3/j3_judge_score.py (local open LLM judges, vLLM, RAGAS-NLI paper prompt, strict parser)
                on pack rd2 (results/journal5/rd2/real_dose/instances.jsonl) -> results/journal5/rd2/judges/<slug>__rd2.jsonl
  --what ft     scripts/journal3/j3_ft_score.py (chain-1 fine-tuned MiniCheck-Flan-T5 / AlignScore-large + same-path bases)
                on packs rd2_raw + rd2unf_{raw,unf,unf_v2} (results/journal5/rd2/real_dose/unf/rd_pack.jsonl, built by
                rd2_unf_pack.py) -> results/journal5/rd2/ft/<name>__<pack>_<variant>.jsonl
The wrapper only registers the two RD2 packs in j3_common.PACK_FILES / VARIANTS and points the chain-3 markers to
results/journal5/rd2/markers_j3 (so the existing J3_* markers of the RD runs do not skip RD2); all other arguments are
passed through (e.g. --array-index 8 --backend vllm).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rd2_common import INSTANCES, RD2, RD2_DIR, ROOT  # noqa: E402

os.environ.setdefault("MEDVERIF_J3_MARKERS", str(RD2_DIR / "markers_j3"))
sys.path.insert(0, str(ROOT / "scripts" / "journal3"))
import j3_common  # noqa: E402

j3_common.PACK_FILES["rd2"] = INSTANCES
j3_common.PACK_FILES["rd2unf"] = RD2 / "unf" / "rd_pack.jsonl"
j3_common.VARIANTS[("rd2", "raw")] = ("claim", "evidence")
j3_common.VARIANTS[("rd2unf", "raw")] = ("claim_orig", "evidence_orig")
j3_common.VARIANTS[("rd2unf", "unf")] = ("claim_unf", "evidence_unf")
j3_common.VARIANTS[("rd2unf", "unf_v2")] = ("claim_unf_v2", "evidence_unf_v2")


def main() -> None:
    argv = sys.argv[1:]
    if "--what" not in argv:
        raise SystemExit("usage: rd2_j3_score.py --what judge|ft [chain-3 args...]")
    i = argv.index("--what")
    what = argv[i + 1]
    rest = argv[:i] + argv[i + 2:]
    if not INSTANCES.is_file():
        raise SystemExit("no RD2 instances (%s); run rd2_extract.py first" % INSTANCES)
    if what == "judge":
        import j3_judge_score as M
        defaults = ["--packs", "rd2", "--out-dir", str(RD2_DIR / "judges")]
    elif what == "ft":
        import j3_ft_score as M
        defaults = ["--packs", "rd2_raw,rd2unf_raw,rd2unf_unf,rd2unf_unf_v2", "--out-dir", str(RD2_DIR / "ft")]
    else:
        raise SystemExit("--what must be judge or ft")
    flags = {a for a in rest if a.startswith("--")}
    extra = []
    for k in range(0, len(defaults), 2):
        if defaults[k] not in flags:
            extra += defaults[k:k + 2]
    sys.argv = [M.__file__] + rest + extra
    M.main()


if __name__ == "__main__":
    main()
