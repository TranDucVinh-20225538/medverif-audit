"""Shared helpers for journal 5: RD2, the independent pre-registered expansion of the real-dose (RD) set.

Python >= 3.8, stdlib only.  Layout (all NEW files; nothing under data/, qc/ or results/journal2/ is written):

  results/journal5/rd2/labels/labels.jsonl      openFDA labels for NEW drugs (rd2_fetch_labels.py, box, internet)
  results/journal5/rd2/real_dose/questions.jsonl  pre-registered questions (rd2_questions.py)  <- sha256 in prereg
  results/journal5/rd2/real_dose/answers.jsonl    generator answers (rd2_generate.py, HPC vLLM + optional OpenRouter)
  results/journal5/rd2/real_dose/instances.jsonl  same schema as results/journal2/real_dose/instances.jsonl
  results/journal5/rd2/real_dose/scores/          checker scores (scripts/journal2/rd_score.py with MEDVERIF_JR2_DIR)
  results/journal5/rd2/markers/                   stage markers

The directory layout mirrors results/journal2/ on purpose: setting MEDVERIF_JR2_DIR=results/journal5/rd2 makes the
UNCHANGED journal-2 scorer (scripts/journal2/rd_score.py) read RD2 instances and write RD2 scores, with its own
markers and its own API ledger (sum of api_cost_usd over results/journal5/rd2/real_dose/**.jsonl).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (ROOT / "src", ROOT / "scripts" / "journal", ROOT / "scripts" / "journal2", HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

RD2_DIR = Path(os.environ.get("MEDVERIF_RD2_DIR") or (ROOT / "results" / "journal5" / "rd2"))  # override only for tests
RD2 = RD2_DIR / "real_dose"
RD2_LABELS = RD2_DIR / "labels" / "labels.jsonl"
RD2_MARKERS = RD2_DIR / "markers"
QUESTIONS = RD2 / "questions.jsonl"
ANSWERS = RD2 / "answers.jsonl"
INSTANCES = RD2 / "instances.jsonl"
FREEZE = ROOT / "prereg" / "rd2_freeze.json"
PREREG = ROOT / "prereg" / "rd2_prereg.md"

# original RD set (read-only)
RD1 = ROOT / "results" / "journal2" / "real_dose"
RD1_LABELS = ROOT / "data" / "real_labels" / "labels.jsonl"

SEED = 20261002  # RD2 seed (RD used 20261001 for its QC sheet)

# Files whose content defines the RD2 instances; their sha256 is frozen in prereg/rd2_freeze.json and re-checked
# before generation / extraction (the HPC checkout has locally modified files elsewhere).
FROZEN_CODE = (
    "src/unit_norm_fix.py",                 # span extraction + canonical quantities (rd_extract, rd_questions)
    "scripts/journal2/rd_extract.py",       # classify(): auto_class / subtype (reused verbatim)
    "scripts/journal2/rd_questions.py",     # sentences(), dose_kinds_ok() (reused verbatim)
    "scripts/journal2/rd_generate.py",      # PROMPTS + MAX_TOKENS (reused verbatim)
    "scripts/journal5/rd2_common.py",
    "scripts/journal5/rd2_questions.py",
    "scripts/journal5/rd2_extract.py",
)
# Runner / analysis code: sha256 recorded in the freeze; a change is LOGGED (not fatal) and must be documented in
# prereg/rd2_amendments.md with its reason and date.  (basis_check.py and unit_norm_fix_v2.py are hard-checked against
# their own freezes by rd2_basis_check.py / rd2_unf_pack.py.)
RUNNER_CODE = (
    "scripts/journal5/rd2_generate.py",
    "scripts/journal5/rd2_j3_score.py",
    "scripts/journal5/rd2_basis_check.py",
    "scripts/journal5/rd2_unf_pack.py",
    "scripts/journal5/rd2_adjudication_sheet.py",
    "scripts/journal5/rd2_report.py",
    "scripts/journal/jr_common.py",
    "src/llm_client.py",
    "scripts/journal3/j3_judge_score.py",
    "scripts/journal3/j3_ft_score.py",
    "scripts/journal3/j3_common.py",
    "scripts/journal2/rd_score.py",
    "scripts/journal2/small_checkers.py",
)


def log(stage: str, **kw) -> None:
    print(json.dumps(dict({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "stage": stage}, **kw), ensure_ascii=False,
                     default=str), flush=True)


def read_jsonl(path) -> List[dict]:
    p = Path(path)
    if not p.is_file():
        return []
    out = []
    with p.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:  # partially written last line of a running job
                    continue
    return out


def write_jsonl(path, rows: Iterable[dict]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(p)


def append_jsonl(path, rows: Iterable[dict]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def sha256_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git(*args) -> str:
    try:
        return subprocess.run(["git"] + list(args), cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True, timeout=60).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def marker(stage: str) -> Path:
    return RD2_MARKERS / (stage + ".done")


def is_done(stage: str) -> bool:
    return marker(stage).is_file() and os.environ.get("MEDVERIF_RD2_FORCE", "") not in ("1", "all", stage)


def mark_done(stage: str, **info) -> None:
    RD2_MARKERS.mkdir(parents=True, exist_ok=True)
    info = dict({"stage": stage, "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                 "slurm_job": "%s%s" % (os.environ.get("SLURM_ARRAY_JOB_ID") or os.environ.get("SLURM_JOB_ID", "local"),
                                        ("_" + os.environ["SLURM_ARRAY_TASK_ID"]) if os.environ.get("SLURM_ARRAY_TASK_ID") else "")},
                **info)
    marker(stage).write_text(json.dumps(info, indent=1, default=str) + "\n")


# ------------------------------------------------------------------ freeze verification
def freeze_problems(require_questions: bool = True) -> List[str]:
    """Compare the current files with prereg/rd2_freeze.json.  Empty list = OK."""
    if not FREEZE.is_file():
        return ["prereg/rd2_freeze.json missing (pre-registration not committed?)"]
    frz = json.loads(FREEZE.read_text())
    probs = []
    for rel, want in sorted(frz.get("code_sha256", {}).items()):
        p = ROOT / rel
        if not p.is_file():
            probs.append("%s missing" % rel)
        elif sha256_file(p) != want:
            probs.append("%s sha256 differs from the pre-registered version" % rel)
    if require_questions:
        q = ROOT / frz["questions_file"]
        if not q.is_file():
            probs.append("%s missing" % frz["questions_file"])
        elif sha256_file(q) != frz["questions_sha256"]:
            probs.append("%s sha256 differs from the pre-registered file" % frz["questions_file"])
    return probs


def runner_changes() -> List[str]:
    """Runner/analysis files whose sha256 differs from the freeze (informational; document in prereg/rd2_amendments.md)."""
    if not FREEZE.is_file():
        return []
    frz = json.loads(FREEZE.read_text()).get("runner_sha256", {})
    return [rel for rel, want in sorted(frz.items()) if not (ROOT / rel).is_file() or sha256_file(ROOT / rel) != want]


def assert_frozen(require_questions: bool = True) -> None:
    if os.environ.get("MEDVERIF_RD2_SKIP_FREEZE") == "1":  # tests only
        return
    probs = freeze_problems(require_questions)
    if probs:
        raise SystemExit("RD2 FREEZE CHECK FAILED (nothing run): " + "; ".join(probs))
    ch = runner_changes()
    if ch:
        log("RD2_freeze", warning="runner/analysis code changed since the pre-registration; document in "
                                   "prereg/rd2_amendments.md", files=ch)


# ------------------------------------------------------------------ dosing-type tagging (pre-registered strata)
# Applied identically to RD (for the expected-error estimate) and RD2.  Multi-label `dosing_types`; the single
# `stratum` is the first type present in STRATA order (else "fixed").
STRATA = ("bsa", "weight_based", "loading_maintenance", "renal", "pediatric", "divided_daily")
ERROR_PRONE = set(STRATA)
_PED = re.compile(r"\b(pediatric|paediatric|child|children|infants?|neonat\w*|newborns?|adolescents?|premature|preterm|"
                  r"toddlers?|(?:under|younger than|less than|below)\s+(?:1[0-7]|[1-9])\s+years?|"
                  r"(?:1[0-7]|[1-9])\s+(?:months?|years?)\s+(?:of age\s+)?(?:to|through|and)\s+(?:less than\s+)?(?:1[0-7]|[1-9])\s+(?:months?|years?))\b",
                  re.I)
_LOAD = re.compile(r"\b(loading|maintenance|initial\s+(?:intravenous\s+)?bolus|bolus\s+(?:dose|injection)|"
                   r"followed\s+by\s+(?:a\s+)?(?:continuous\s+)?(?:infusion|maintenance))\b", re.I)
_RENAL = re.compile(r"(creatinine\s+clearance|\bCrCl\b|\bCLcr\b|\beGFR\b|\bGFR\b|renal\s+(?:impairment|insufficiency|function|"
                    r"failure|disease|dysfunction)|kidney\s+(?:impairment|disease|function)|(?:hemo|peritoneal\s+)?dialysis|"
                    r"\bESRD\b|\bCRRT\b)", re.I)
_DIVIDED = re.compile(r"\b(divided|in\s+(?:2|3|4|two|three|four)\s+(?:equal\s+|equally\s+)?doses)\b", re.I)
_FREQ = re.compile(r"\b(every\s+\d+(?:\s*(?:to|-)\s*\d+)?\s+hours|twice\s+(?:a\s+)?daily|twice\s+a\s+day|three\s+times|"
                   r"four\s+times|b\.?i\.?d|t\.?i\.?d|q\.?i\.?d|q\d+h)\b", re.I)
_HEAD = re.compile(r"(?:^|\s)(\d{1,2}\.\d{1,2}(?:\.\d{1,2})?)\s+([A-Z][A-Za-z0-9 ,/()'\-]{3,90}?)(?=\s{1,3}[A-Z0-9(]|$)")


def tag_dosing(sentence: str, context_before: str, spans, primary) -> Dict[str, object]:
    """Pre-registered dosing-type tags for one target sentence.
    sentence = target sentence; context_before = up to 250 chars of label text before it (headings such as
    'Pediatric Patients:'); spans = find_spans(sentence); primary = the [DOSE] span."""
    ctx = (context_before or "")[-250:] + " " + sentence
    types = []
    if primary.m2 or any(s.m2 for s in spans):
        types.append("bsa")
    if primary.kg or any(s.kg for s in spans):
        types.append("weight_based")
    if _LOAD.search(sentence):
        types.append("loading_maintenance")
    if _RENAL.search(ctx):
        types.append("renal")
    if _PED.search(ctx):
        types.append("pediatric")
    if _DIVIDED.search(sentence) or (any(s.time == "/day" for s in spans) and _FREQ.search(sentence)):
        types.append("divided_daily")
    stratum = next((t for t in STRATA if t in types), "fixed")
    basis = "/m2" if primary.m2 else ("/kg" if primary.kg else "none")
    mixed = len({("/m2" if s.m2 else ("/kg" if s.kg else "none")) for s in spans if not s.conc}) > 1
    pop = ("renal" if "renal" in types else ("pediatric" if "pediatric" in types else
           ("hepatic" if re.search(r"hepatic\s+impairment|child-pugh", ctx, re.I) else
            ("geriatric" if re.search(r"geriatric|elderly", ctx, re.I) else "adult_or_unspecified"))))
    return {"dosing_types": types, "stratum": stratum, "primary_basis": basis, "mixed_basis_sentence": mixed,
            "population": pop}


def last_heading(text_before: str) -> str:
    """Nearest preceding numbered SPL heading ('2.3 Pediatric Patients') -- documents the indication/section."""
    hs = list(_HEAD.finditer(text_before or ""))
    return ("%s %s" % (hs[-1].group(1), hs[-1].group(2).strip())) if hs else ""


def norm_drug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def rd1_exclusion() -> Dict[str, object]:
    """Everything that identifies an RD (journal 2) drug: lexicon names with >=1 RD question, their label set_ids and
    openFDA generic/brand names.  RD2 excludes every label that shares ANY of these (drug-level exclusion, which
    implies zero overlap of drug/population/indication combinations)."""
    qs = read_jsonl(RD1 / "questions.jsonl")
    drugs = {q["drug"] for q in qs}
    labels = {l["drug"]: l for l in read_jsonl(RD1_LABELS)}
    set_ids = {q.get("set_id") for q in qs if q.get("set_id")}
    names = set()
    for d in drugs:
        names.add(norm_drug(d))
        lab = labels.get(d) or {}
        for n in (lab.get("generic_name") or []) + (lab.get("brand_name") or []):
            names.add(norm_drug(n))
    words = set()
    for n in names:
        for w in n.split():
            if len(w) >= 5 and w not in GENERIC_WORDS:
                words.add(w)
    return {"drugs": drugs, "set_ids": set_ids, "names": names, "words": words,
            "target_sentences": {q["target_sentence"] for q in qs}}


# salt / dosage-form words that must not count as a shared drug name
GENERIC_WORDS = {"sodium", "potassium", "calcium", "magnesium", "hydrochloride", "chloride", "sulfate", "acetate",
                 "phosphate", "citrate", "injection", "tablets", "tablet", "capsules", "extended", "release", "delayed",
                 "solution", "suspension", "dextrose", "water", "hydrobromide", "maleate", "mesylate", "tartrate",
                 "succinate", "fumarate", "bromide", "besylate", "gluconate", "lactate", "carbonate", "bicarbonate",
                 "oral", "topical", "cream", "ointment", "intravenous", "chewable", "disintegrating", "hcl", "and",
                 "with", "free", "base", "monohydrate", "dihydrate", "trihydrate", "anhydrous", "human", "recombinant",
                 "pegylated", "liposomal", "liposome", "lipid", "complex", "kit", "vial", "pharmacy", "bulk", "package",
                 "premix", "premixed", "plastic", "container", "single", "multiple", "dose", "concentrate", "powder",
                 "lyophilized", "film", "coated", "orally", "valerate", "propionate", "dipropionate", "furoate",
                 "pivoxil", "axetil", "trometamol", "tromethamine", "meglumine", "edisylate", "palmitate", "decanoate",
                 "enanthate", "cypionate", "nitrate", "oxide", "hydroxide", "iodide", "fluoride", "acid", "ethyl",
                 "methyl", "alpha", "beta", "insulin", "immune", "globulin", "factor", "toxoid", "vaccine", "inhalation",
                 "aerosol", "spray", "nasal", "ophthalmic", "otic", "patch", "transdermal", "system", "vaginal", "rectal",
                 "suppository", "lotion", "foam", "shampoo", "elixir", "syrup", "drops", "granules", "pellets", "bitartrate",
                 "dinitrate", "mononitrate", "hyclate", "hemihydrate", "sesquihydrate", "disodium", "dipotassium",
                 "magnesium", "zinc", "lysine", "arginine", "conjugated", "pentahydrate"}


def label_overlaps_rd1(lab: dict, excl: Dict[str, object]) -> str:
    """'' if the label shares nothing with RD, else the reason."""
    if lab.get("drug") in excl["drugs"]:
        return "drug_in_rd"
    if lab.get("set_id") and lab["set_id"] in excl["set_ids"]:
        return "set_id_in_rd"
    names = {norm_drug(lab.get("drug"))}
    for n in (lab.get("generic_name") or []) + (lab.get("brand_name") or []):
        names.add(norm_drug(n))
    if names & excl["names"]:
        return "name_in_rd"
    words = {w for n in names for w in n.split() if len(w) >= 5 and w not in GENERIC_WORDS}
    shared = words & excl["words"]
    if shared:
        return "shares_ingredient_word:" + ",".join(sorted(shared))
    return ""
