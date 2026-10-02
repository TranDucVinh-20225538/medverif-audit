#!/usr/bin/env python3
"""(RD2-1c) Write prereg/rd2_freeze.json: sha256 of the pre-registered questions, labels, prompts and the code that
defines RD2 instances (rd2_common.FROZEN_CODE).  Run once, BEFORE any answer is generated; committed together with
prereg/rd2_prereg.md.  rd2_generate.py / rd2_extract.py refuse to run if any of these hashes changes.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rd2_common import FREEZE, FROZEN_CODE, RUNNER_CODE, QUESTIONS, RD2_LABELS, ROOT, SEED, git, read_jsonl, sha256_file, sha256_text  # noqa: E402
from rd_generate import MAX_TOKENS, PROMPTS  # noqa: E402


def main() -> None:
    if (QUESTIONS.parent / "answers.jsonl").exists() or (QUESTIONS.parent / "answers").exists():
        raise SystemExit("answers already exist -- a freeze written now would not be a pre-registration")
    qs = read_jsonl(QUESTIONS)
    frz = {
        "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "parent_commit": git("rev-parse", "HEAD"),
        "seed": SEED,
        "questions_file": str(QUESTIONS.relative_to(ROOT)), "questions_sha256": sha256_file(QUESTIONS), "n_questions": len(qs),
        "labels_file": str(RD2_LABELS.relative_to(ROOT)), "labels_sha256": sha256_file(RD2_LABELS),
        "code_sha256": {rel: sha256_file(ROOT / rel) for rel in FROZEN_CODE},
        "runner_sha256": {rel: sha256_file(ROOT / rel) for rel in RUNNER_CODE},
        "prompts_sha256": {c: sha256_text(PROMPTS[c]) for c in PROMPTS}, "max_tokens": MAX_TOKENS,
        "basis_check_freeze_commit": "fdb95de68b376340946f2e251040d3006c20072e",
        "basis_check_sha256": sha256_file(ROOT / "scripts/journal4/basis_check.py"),
        "unf_v2_sha256": sha256_file(ROOT / "src/unit_norm_fix_v2.py"),
        "generators": {
            "vllm": {"llama31_8b": "meta-llama/Llama-3.1-8B-Instruct@0e9e39f249a16976918f6564b8830bc894c89659",
                     "qwen25_14b": "Qwen/Qwen2.5-14B-Instruct@cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8",
                     "medgemma_27b": "google/medgemma-27b-text-it@5b667cf2ddcf064085bc90952edb35a0edbfb79c",
                     "baichuan_m2_32b": "baichuan-inc/Baichuan-M2-32B@360f684d3cd527a4ef986c54071015eb0e6def58"},
            "openrouter": {"gpt4o_mini": "openai/gpt-4o-mini@OpenAI", "gemma3_27b": "google/gemma-3-27b-it@DeepInfra"},
        },
    }
    FREEZE.parent.mkdir(parents=True, exist_ok=True)
    FREEZE.write_text(json.dumps(frz, indent=1) + "\n")
    print(json.dumps({k: frz[k] for k in ("questions_sha256", "n_questions", "labels_sha256", "parent_commit")}, indent=1))


if __name__ == "__main__":
    main()
