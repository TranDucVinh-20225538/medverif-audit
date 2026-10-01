#!/usr/bin/env python3
"""Pre-flight for journal chain 3 (login node; no GPU, no model loading, no API calls).

Blockers (exit 2): UNF v2 sha != freeze record; committed packs missing / wrong size; frozen card sha != manifest;
precheck CSV missing; FT checkpoints missing (FT stage); AlignScore base checkpoint not cached (FT stage).
Warnings: python packages in MEDVERIF_PYTHON (vllm / transformers / minicheck / alignscore / pytorch_lightning), vendored
RAGAS prompt == src prompt (if importable), chain-3 files dirty in git, disk, models.json status, GPU-hour estimate.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from j3_common import J3, PACK_FILES, ROOT, git_dirty, pack_rows, read_jsonl, sha256, v2_freeze_ok  # noqa: E402
from j3_models import AS_FILE, AS_REPO, AS_REV, FT, JUDGES, ft_name  # noqa: E402

EXPECT = {"card": 958, "rag": 1622, "rd": 1451, "ho": 450, "rdunf": 705}
# GPU-minutes per judge on one A100-80GB for ~4031 prompts (~1.3k prompt tok, <=512 gen tok), incl. ~3-6 min load/compile
JG_MIN = {"qwen25_0p5b": 12, "qwen25_1p5b": 15, "qwen25_3b": 20, "medgemma_4b": 30, "qwen25_7b": 35, "llama31_8b": 35,
          "qwen25_14b": 60, "qwen25_32b": 120}
FT_MIN = {"minicheck_ft5": 25, "alignscore_large": 30}  # ~2.8k unique texts per model (GPU); AlignScore on CPU fallback ~3-4 h


def hub() -> Path:
    return Path(os.environ.get("HUGGINGFACE_HUB_CACHE") or Path(os.environ.get("HF_HOME") or ROOT / ".cache/huggingface") / "hub")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="FT,JG")
    ap.add_argument("--judges", default="0-6")
    args = ap.parse_args()
    stages = set(args.stages.split(","))
    jidx = set()
    for part in args.judges.split(","):
        a, _, b = part.partition("-")
        jidx.update(range(int(a), int(b or a) + 1))
    B, W, info = [], [], {}
    ok, cur, frz = v2_freeze_ok()
    (B if not ok else info.setdefault("ok", [])).append("UNF v2 sha256 %s %s freeze %s" % (cur[:12], "==" if ok else "!=", frz[:12]))
    for p, n in EXPECT.items():
        if not PACK_FILES[p].is_file():
            B.append("missing pack %s (%s)" % (p, PACK_FILES[p].relative_to(ROOT)))
            continue
        got = len(pack_rows(p))
        if got != n:
            B.append("pack %s: %d scorable rows, expected %d" % (p, got, n))
    man = J3 / "packs/card_manifest.json"
    if man.is_file() and PACK_FILES["card"].is_file():
        m = json.loads(man.read_text())
        if sha256(PACK_FILES["card"]) != m.get("sha256"):
            B.append("results/journal3/packs/card.jsonl sha256 != card_manifest.json (do not edit the frozen card)")
    else:
        B.append("missing frozen card or its manifest under results/journal3/packs/")
    pre = ROOT / "qc/ai_precheck_real_dose_unit_errors.csv"
    if not pre.is_file():
        B.append("missing qc/ai_precheck_real_dose_unit_errors.csv")
    if "FT" in stages:
        for model, tag in FT:
            if tag == "base":
                continue
            ck = ROOT / ".cache/checkpoints" / ("jr_%s_r%s" % (model, tag[1:])) / ("best.ckpt" if model == "alignscore_large" else "best")
            if not ck.exists():
                skip = ROOT / "results/journal/markers" / ("C2_train_%s_%s.done" % (model, tag))
                if tag == "r2" and skip.is_file() and "skipped" in skip.read_text():
                    W.append("%s: chain-1 training skipped -> FT task will mark itself skipped" % ft_name(model, tag))
                else:
                    B.append("missing FT checkpoint %s" % ck.relative_to(ROOT))
        asd = hub() / ("models--" + AS_REPO.replace("/", "--")) / "snapshots" / AS_REV / AS_FILE
        if not asd.exists():
            B.append("AlignScore-large base ckpt not cached at %s (run once on the login node: python -c \"from huggingface_hub "
                     "import hf_hub_download as d; d('%s','%s',revision='%s')\")" % (asd, AS_REPO, AS_FILE, AS_REV))
        for rel in (".cache/src/MiniCheck", ".cache/src/AlignScore/src"):
            if not (ROOT / rel).is_dir():
                B.append("missing %s (MiniCheck / AlignScore library sources, as in chain 1)" % rel)
    vers = {}
    for mod in ("vllm", "transformers", "torch", "huggingface_hub", "pydantic", "minicheck", "alignscore", "pytorch_lightning", "numpy"):
        try:
            m = importlib.import_module(mod)
            vers[mod] = getattr(m, "__version__", "ok")
        except Exception as exc:  # noqa: BLE001
            vers[mod] = "MISSING (%s)" % type(exc).__name__
    info["python"] = sys.executable
    info["packages"] = vers
    if "JG" in stages and not vers["pydantic"].startswith("2"):
        B.append("pydantic v2 needed for the RAGAS prompt (vendored; found %s) in %s" % (vers["pydantic"], sys.executable))
    if vers["numpy"].startswith("MISSING"):
        B.append("numpy missing in %s (report stage)" % sys.executable)
    if "JG" in stages and vers["vllm"].startswith("MISSING"):
        W.append("vllm not importable in %s -> judge tasks fall back to HF transformers (slower)" % sys.executable)
    if "FT" in stages and (vers["pytorch_lightning"].startswith("MISSING") or vers["alignscore"].startswith("MISSING")):
        W.append("alignscore/pytorch_lightning missing in this env -> AlignScore FT tasks use the cpuverif CPU fallback (as chain 1 C3)")
    try:
        sys.path.insert(0, str(ROOT / "src"))
        from verifiers.ragas_nli_prompt import nli_prompt as src_prompt  # type: ignore

        from j3_ragas_prompt import nli_prompt

        if src_prompt("CTX 5 mg", ["CLAIM 5 mg"]) != nli_prompt("CTX 5 mg", ["CLAIM 5 mg"]):
            W.append("vendored RAGAS prompt differs from src/verifiers/ragas_nli_prompt.py on this checkout (locally modified?); "
                     "chain 3 uses the vendored committed version")
        else:
            info.setdefault("ok", []).append("vendored RAGAS prompt == src/verifiers/ragas_nli_prompt.py")
    except Exception as exc:  # noqa: BLE001
        W.append("could not import src prompt for comparison: %s" % exc)
    finally:
        sys.path.pop(0)
    d = git_dirty(["scripts/journal3", "jobs/journal3", "jobs/run_journal_chain3.sh", "results/journal3/packs"])
    if d:
        W.append("chain-3 files modified locally (git status): %s" % d[:10])
    mj = J3 / "models.json"
    if "JG" in stages:
        if mj.is_file():
            mm = json.loads(mj.read_text())
            info["models"] = {k: v.get("status") for k, v in mm.items() if not k.startswith("_")}
            for i in sorted(jidx):
                s = JUDGES[i][0]
                st = (mm.get(s) or {}).get("status")
                if st == "skipped":
                    W.append("judge %s will be SKIPPED: %s" % (s, mm[s].get("reason", "")[:300]))
                elif st != "ok":
                    W.append("judge %s weights status=%s (download step must finish before the GPU task starts)" % (s, st))
        else:
            W.append("results/journal3/models.json missing (download step not run yet)")
        free = shutil.disk_usage(hub() if hub().exists() else ROOT).free / 1e9
        need = sum(JUDGES[i][3] for i in jidx)
        info["hub_cache"] = "%s (%.0f GB free; selected judges total %.1f GB bf16 if nothing is cached)" % (hub(), free, need)
    gpu = 0.0
    if "FT" in stages:
        gpu += sum(FT_MIN[m] for m, _ in FT) / 60
    if "JG" in stages:
        gpu += sum(JG_MIN[JUDGES[i][0]] for i in jidx) / 60
    info["gpu_hours_estimate"] = round(gpu, 1)
    print(json.dumps({"blockers": B, "warnings": W, "info": info}, indent=1))
    sys.exit(2 if B else 0)


if __name__ == "__main__":
    main()
