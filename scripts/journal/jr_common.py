"""Shared helpers for the journal (JHIR) chain: paths, markers, budget ledger, spec checks.

Python >= 3.8, stdlib only.  Every stage is resumable: outputs are appended by id and a
stage marker (results/journal/markers/<stage>.done) lets the chain skip finished stages.

Budget: ONE cap for all API work in the chain (default $5, env MEDVERIF_JR_CAP_USD).
Spend = sum of `api_cost_usd` over every row written by the chain under results/journal/
(question writer, generators, judges).  This is robust across processes, unlike
results/api_cost.json, which llm_client rewrites per process.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT / "src", ROOT / "scripts", ROOT / "analysis", ROOT / "scripts" / "journal"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

JR = ROOT / "results" / "journal"
MARKERS = JR / "markers"
RAG_DIR = JR / "rag"
FT_DIR = JR / "ft"
NOTES = ROOT / "notes"
CAP_USD = float(os.environ.get("MEDVERIF_JR_CAP_USD", "5"))

# API models used by the chain.  Judges come from notes/openrouter_verifiers.json (registry);
# generators / question writer are pinned here.  The spec check refuses to run if a model or
# provider drifts from these values.
QUESTION_WRITER = {"model": "mistralai/mistral-small-3.2-24b-instruct", "provider": "DeepInfra"}
GENERATORS = {
    "gpt4o_mini": {"model": "openai/gpt-4o-mini", "provider": "OpenAI"},
    "gemma3_27b": {"model": "google/gemma-3-27b-it", "provider": "DeepInfra"},
}
JUDGES = ("v4_ragas_nli", "v1_medscore")  # same API pair as T24b (Llama-3.3-70B RAGAS, Mistral-24B MedScore)
# $ per token (prompt, completion) -- used only for dry-run estimates / pre-batch projections
PRICES = {
    "mistralai/mistral-small-3.2-24b-instruct": (0.09375e-6, 0.25e-6),
    "openai/gpt-4o-mini": (0.15e-6, 0.60e-6),
    "google/gemma-3-27b-it": (0.08e-6, 0.45e-6),
    "meta-llama/llama-3.3-70b-instruct": (0.10e-6, 0.32e-6),
    "mistralai/mistral-small-24b-instruct-2501": (0.05e-6, 0.08e-6),
}


def log(stage: str, **kw) -> None:
    kw = dict({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "stage": stage}, **kw)
    print(json.dumps(kw, ensure_ascii=False, default=str), flush=True)


def read_jsonl(path: Path) -> List[dict]:
    if not Path(path).is_file():
        return []
    with Path(path).open(encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def append_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(path)


def done_ids(path: Path, key: str = "instance_id") -> set:
    return {r.get(key) for r in read_jsonl(path)}


def marker(stage: str) -> Path:
    return MARKERS / (stage + ".done")


def is_done(stage: str) -> bool:
    return marker(stage).is_file() and os.environ.get("MEDVERIF_JR_FORCE", "") not in ("1", stage)


def mark_done(stage: str, **info) -> None:
    MARKERS.mkdir(parents=True, exist_ok=True)
    info = dict({"stage": stage, "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                 "slurm_job": os.environ.get("SLURM_JOB_ID", "local")}, **info)
    marker(stage).write_text(json.dumps(info, indent=2, default=str) + "\n")


# ------------------------------------------------------------------ budget
def spent_usd() -> float:
    total = 0.0
    if not JR.is_dir():
        return 0.0
    for p in JR.rglob("*.jsonl"):
        if "markers" in p.parts:
            continue
        for r in read_jsonl(p):
            c = r.get("api_cost_usd")
            if isinstance(c, (int, float)):
                total += float(c)
            elif r.get("api_prompt_tokens"):  # provider returned no cost -> estimate from tokens
                total += est_cost(r.get("api_model") or "", r.get("api_prompt_tokens") or 0,
                                  r.get("api_completion_tokens") or 0)
    return total


def est_cost(model: str, prompt_tokens: float, completion_tokens: float) -> float:
    pin, pout = PRICES.get(model, (1.0e-6, 2.0e-6))  # unknown model -> pessimistic
    return prompt_tokens * pin + completion_tokens * pout


def assert_budget(next_batch_usd: float = 0.0, what: str = "") -> Dict[str, float]:
    s = spent_usd()
    if s + next_batch_usd > CAP_USD:
        raise SystemExit("BUDGET STOP%s: spent $%.4f + next batch est $%.4f > cap $%.2f" % (
            (" (" + what + ")") if what else "", s, next_batch_usd, CAP_USD))
    return {"spent_usd": s, "cap_usd": CAP_USD, "remaining_usd": CAP_USD - s}


def tokens(text: str) -> int:
    return max(1, len(text or "") // 4)


# ------------------------------------------------------------------ env + spec check
def load_env() -> None:
    """KEY=VALUE lines from ./.env (HPC checkout) or ~/kkk/openrouter.env; existing env wins."""
    for path in (ROOT / ".env", Path.home() / "kkk/openrouter.env"):
        if not path.is_file():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        break


def spec_check(judges: Iterable[str] = JUDGES, need_key: bool = True) -> List[str]:
    """Validate every API spec BEFORE any call. Returns a list of problems (empty = OK)."""
    problems = []
    reg = json.loads((NOTES / "openrouter_verifiers.json").read_text())["verifiers"]
    for j in judges:
        spec = reg.get(j)
        if not spec:
            problems.append("judge %s missing from notes/openrouter_verifiers.json" % j)
            continue
        if not spec.get("openrouter_model") or not spec.get("provider"):
            problems.append("judge %s has no pinned model/provider in registry" % j)
    for name, spec in list(GENERATORS.items()) + [("question_writer", QUESTION_WRITER)]:
        if not spec.get("model") or not spec.get("provider"):
            problems.append("%s has no pinned model/provider" % name)
        if spec.get("model") not in PRICES:
            problems.append("%s model %s has no price entry (cost estimate impossible)" % (name, spec.get("model")))
    if need_key:
        load_env()
        if not os.environ.get("OPENROUTER_API_KEY", "").strip():
            problems.append("OPENROUTER_API_KEY not set (env, ./.env, ~/kkk/openrouter.env)")
    return problems


def judge_spec(j: str) -> dict:
    return json.loads((NOTES / "openrouter_verifiers.json").read_text())["verifiers"][j]


def chat_pinned(spec: dict, prompt: str, max_tokens: int = 256, seed: int = 42) -> dict:
    """One temperature-0 call with pinned provider (no fallbacks). Returns a row-ready dict."""
    os.environ["MEDVERIF_USE_OPENROUTER"] = "1"
    from llm_client import chat  # noqa: E402

    resp = chat(model=spec["model"], messages=[{"role": "user", "content": prompt}], temperature=0.0,
                max_tokens=max_tokens, seed=seed, provider=spec["provider"], allow_fallbacks=False)
    served = (resp.provider or "")
    if served and served.lower() != spec["provider"].lower():
        raise RuntimeError("provider drift: asked %s, served %s" % (spec["provider"], served))
    return {"text": (resp.text or "").strip(), "api_model": resp.model or spec["model"], "api_provider": served or spec["provider"],
            "api_request_id": resp.request_id, "api_prompt_tokens": resp.prompt_tokens,
            "api_completion_tokens": resp.completion_tokens,
            "api_cost_usd": resp.cost_usd if resp.cost_usd is not None
            else est_cost(spec["model"], resp.prompt_tokens or 0, resp.completion_tokens or 0)}
