#!/usr/bin/env python3
"""(J4-FJ) Frontier API LLMs as fact-check judges on the REAL drug-dose answers (RD set, 1451 answers vs FDA label excerpts).

Protocol = EXACTLY the paper's RAGAS-NLI judge as used for the API judges (src/verifiers/v4_ragas_nli.py / v5 / v6 OpenRouter
path) and the chain-3 local judges (scripts/journal3/j3_judge_score.py):
  * user turn  = nli_prompt(evidence, [claim])  -- frozen RAGAS prompt, imported from scripts/journal3/j3_ragas_prompt.py
                 (vendored verbatim from src/verifiers/ragas_nli_prompt.py; checked against src at start-up);
                 evidence = FDA label excerpt (instances.jsonl `evidence`), claim = model answer (`claim`); single user message,
                 no system prompt, no prompt suffix.
  * verdict    = STRICT: j3_ragas_prompt.parse_verdict (= v4_ragas_nli.parse_verdict, verbatim): first statement's
                 verdict 1 -> PASS, 0 -> FAIL, anything else -> PARSE_FAIL.  This is the number comparable to every
                 existing judge row.
                 LENIENT (extra, new in journal 4, applied post hoc to raw_output for every judge incl. the existing ones):
                 if strict gives PARSE_FAIL, take the first  "verdict": 0/1  match of LENIENT_RE in the raw text.
  * decoding   = temperature 0 where the provider accepts it (reasoning models that reject it are retried without it;
                 the value actually sent is stored per row), lowest reasoning effort, max output tokens small but with
                 headroom for hidden reasoning tokens (reasoning tokens count against the cap on all three providers).
Providers (plain HTTPS via urllib, no SDK needed): openai (Responses API; --openai-api chat for Chat Completions),
anthropic (Messages API), gemini (generateContent), mock (canned outputs, no network) ; keys from OPENAI_API_KEY /
ANTHROPIC_API_KEY / GEMINI_API_KEY (GOOGLE_API_KEY accepted for gemini).  Keys are never printed or stored.

Packs/subsets:  --pack rd (default): all | adjudicable (correct + auto errors, skips the 249 not-adjudicable rows) |
                flagged47 (auto unit-type = unit_error + basis_error) | true12 (AI-precheck true_unit_error) | smoke (10 rows:
                4 correct, 4 precheck-true, 2 value errors)
                --pack card : the frozen main DOSE card used by chain 3 (958 rows: C0, claim/evidence x2/x10 value edits,
                claim-side / evidence-side unit swaps up and down, conversions); all | smoke (10 rows).
Outputs:  results/journal4/frontier/<model>.jsonl (rd)  or  <model>__card.jsonl  (append-only, resumable by instance_id;
          every row carries tokens + cost, so the jsonl is the cost ledger)
          results/journal4/frontier/report_<pack>_<subset>.{md,json}: same RD metrics as scripts/journal3/j3_report.py
          section 1 (rd_block / RD_GROUPS / drug-clustered bootstrap, imported, not copied) for every frontier model found,
          strict and lenient, with the existing checkers/judges recomputed on the SAME rows, plus the per-case table of the
          12 precheck-true unit errors.
Budget:   pre-run estimate printed; aborts if estimate > --max-usd; hard guard during the run reserves the worst case
          (prompt + max_output_tokens) for every in-flight request, so total spend in the model's jsonl never exceeds
          --max-usd (cumulative over resumes).  Prices: PRICES below (USD / 1M tokens, checked 2026-10-01) or
          --price-in/--price-out.

Python >= 3.8.  pip: pydantic>=2 (prompt rendering), numpy (report).  Nothing else.

Examples:
  python scripts/journal4/frontier_judges_rd.py --provider openai --subset smoke
  python scripts/journal4/frontier_judges_rd.py --provider anthropic --subset all --max-usd 40 --yes
  python scripts/journal4/frontier_judges_rd.py --provider gemini --model gemini-3.1-pro-preview --subset true12 --dry-run
  python scripts/journal4/frontier_judges_rd.py --report-only --subset all
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import datetime as dt
import hashlib
import importlib.util
import json
import os
import random
import re
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
J3_DIR = HERE.parent / "journal3"
sys.path.insert(0, str(J3_DIR))
from j3_common import PACK_FILES, ROOT, append_jsonl, pack_rows, read_jsonl  # noqa: E402
from j3_ragas_prompt import nli_prompt, parse_verdict  # noqa: E402

SCRIPT_VERSION = "j4-frontier-1"
PROMPT_ID_J4 = "ragas_nli@298b682 via j3_ragas_prompt.nli_prompt; raw single user message, no system prompt (API path = v5/v6)"
OUT_DIR = ROOT / "results" / "journal4" / "frontier"
PRECHECK = ROOT / "qc" / "ai_precheck_real_dose_unit_errors.csv"
RD_SCORES = ROOT / "results" / "journal2" / "real_dose" / "scores"
J3_JUDGES = ROOT / "results" / "journal3" / "judges" / "scores"
TZ7 = dt.timezone(dt.timedelta(hours=7))

LENIENT_RE = re.compile(r'"verdict"\s*:\s*"?([01])\b')

# provider -> (default model, env var(s), default effort)
PROVIDERS = OrderedDict([
    ("openai", {"model": "gpt-6-astra", "env": ["OPENAI_API_KEY"], "effort": "low"}),
    ("anthropic", {"model": "claude-opus-5-5", "env": ["ANTHROPIC_API_KEY"], "effort": "low"}),
    ("gemini", {"model": "gemini-3.1-pro-preview", "env": ["GEMINI_API_KEY", "GOOGLE_API_KEY"], "effort": "low"}),
    ("mock", {"model": "mock-judge", "env": [], "effort": "low"}),
])
# USD per 1M tokens (input, output incl. reasoning/thinking tokens); standard tier, prompts < 200k tokens.
# Sources checked 2026-10-01: developers.openai.com/api/docs/models, platform.claude.com/docs/en/about-claude/models,
# ai.google.dev/gemini-api/docs/pricing.  Override with --price-in / --price-out for anything else.
PRICES = {
    "gpt-6-astra": (10.0, 50.0), "gpt-6.1-sol": (2.0, 10.0), "gpt-6-luna": (0.10, 0.50),
    "claude-fable-5-1": (10.0, 50.0), "claude-opus-5-5": (4.0, 20.0), "claude-sonnet-5-5": (2.0, 10.0),
    "claude-opus-5": (5.0, 25.0), "claude-sonnet-5": (2.0, 10.0), "claude-haiku-4-5": (1.0, 5.0),
    "claude-haiku-4-5-20251001": (1.0, 5.0),
    "gemini-3.1-pro-preview": (2.0, 12.0), "gemini-3-flash-preview": (0.50, 3.0),
    "mock-judge": (10.0, 50.0),  # priced like the most expensive default so the guard is exercised in tests
}
# chars per token used for the PRE-RUN estimate only (measured 4.39 chars/token for this prompt with the Llama-3 tokenizer;
# 4.0 is conservative; Claude's tokenizer since Opus 4.7 produces ~35% more tokens for English -> 3.0)
CHARS_PER_TOKEN = {"openai": 4.0, "anthropic": 3.0, "gemini": 4.0, "mock": 4.0}
RETRYABLE = {408, 409, 425, 429, 500, 502, 503, 504, 520, 522, 524, 529}


def now_ts() -> str:
    return dt.datetime.now(TZ7).strftime("%Y-%m-%dT%H:%M:%S%z")


def log(**kw) -> None:
    print(json.dumps(dict({"ts": now_ts()}, **kw), ensure_ascii=False, default=str), flush=True)


def slugify(model: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", model).strip("_")


# ---------------------------------------------------------------- parsing
def parse_strict(raw: str) -> Tuple[str, Optional[float]]:
    """The paper parser (v4_ragas_nli.parse_verdict == j3_ragas_prompt.parse_verdict)."""
    return parse_verdict(raw or "")


def parse_lenient(raw: str) -> Tuple[str, Optional[float]]:
    v, s = parse_strict(raw)
    if v != "PARSE_FAIL":
        return v, s
    m = LENIENT_RE.search(raw or "")
    if not m:
        return "PARSE_FAIL", None
    return ("PASS", 1.0) if m.group(1) == "1" else ("FAIL", 0.0)


def prompt_check() -> Optional[bool]:
    """True if j3_ragas_prompt.nli_prompt == src/verifiers/ragas_nli_prompt.nli_prompt on a probe (None if src missing)."""
    p = ROOT / "src" / "verifiers" / "ragas_nli_prompt.py"
    if not p.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location("_src_ragas_nli_prompt", str(p))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        probe = ("Adults: 1,000 mg every 6 hours.", ["The dose is 1,000 mg every 6 hours."])
        return mod.nli_prompt(*probe) == nli_prompt(*probe)
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------- data
def load_precheck() -> Dict[str, dict]:
    if not PRECHECK.is_file():
        return {}
    with PRECHECK.open(encoding="utf-8") as fh:
        return {r["instance_id"]: r for r in csv.DictReader(l for l in fh if not l.startswith("#"))}


def _spread(rows: List[dict], k: int, salt: str) -> List[dict]:
    """k rows, deterministic, one per drug first (hash order)."""
    rows = sorted(rows, key=lambda r: hashlib.sha1((salt + r["instance_id"]).encode()).hexdigest())
    out, seen = [], set()
    for r in rows:
        d = r.get("drug") or r.get("base_id")
        if d not in seen:
            out.append(r)
            seen.add(d)
        if len(out) == k:
            return out
    for r in rows:
        if r not in out:
            out.append(r)
        if len(out) == k:
            break
    return out


def select_rows(pack: str, subset: str) -> List[dict]:
    """Rows to score: full instance row + `claim`/`evidence` exactly as pack_rows() feeds the chain-3 judges."""
    io = {r["instance_id"]: r for r in pack_rows(pack)}  # valid rows, stripped claim/evidence
    full = [dict(r, claim=io[r["instance_id"]]["claim"], evidence=io[r["instance_id"]]["evidence"])
            for r in read_jsonl(PACK_FILES[pack]) if r.get("instance_id") in io]
    if pack == "card":
        if subset == "all":
            return full
        if subset == "smoke":
            by = lambda c: [r for r in full if r["condition"] == c]  # noqa: E731
            return (_spread(by("C0"), 3, "s") + _spread(by("E1-unit-claim"), 3, "s") + _spread(by("E1-unit-evid"), 2, "s")
                    + _spread(by("INV-claim"), 2, "s"))
        raise SystemExit("--pack card supports --subset all|smoke")
    pre = load_precheck()
    unit = ("unit_error", "basis_error")
    if subset == "all":
        return full
    if subset == "adjudicable":
        return [r for r in full if r["auto_class"] in ("correct", "value_error") + unit]
    if subset == "flagged47":
        return [r for r in full if r["auto_class"] in unit]
    if subset == "true12":
        return [r for r in full if (pre.get(r["instance_id"]) or {}).get("ai_label") == "true_unit_error"]
    if subset == "smoke":
        corr = _spread([r for r in full if r["auto_class"] == "correct"], 4, "smoke")
        true = _spread([r for r in full if (pre.get(r["instance_id"]) or {}).get("ai_label") == "true_unit_error"], 4, "smoke")
        val = _spread([r for r in full if r["auto_class"] == "value_error"], 2, "smoke")
        return corr + true + val
    raise SystemExit("unknown subset %s" % subset)


# ---------------------------------------------------------------- HTTP / providers
class ApiError(Exception):
    def __init__(self, status: int, body: str, retry_after: Optional[float] = None):
        super().__init__("HTTP %s: %s" % (status, body[:600]))
        self.status, self.body, self.retry_after = status, body, retry_after


def http_post(url: str, headers: dict, body: dict, timeout: float) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=dict(headers, **{"Content-Type": "application/json"}), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            txt = e.read().decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            txt = ""
        ra = e.headers.get("retry-after") if e.headers else None
        try:
            ra = float(ra) if ra is not None else None
        except ValueError:
            ra = None
        raise ApiError(e.code, txt, ra)


class Provider:
    name = "base"

    def __init__(self, model: str, effort: Optional[str], temperature: Optional[float], max_out: int, timeout: float, args):
        self.model, self.effort, self.temperature, self.max_out, self.timeout = model, effort, temperature, max_out, timeout
        self.args = args
        self.temp_lock = threading.Lock()
        self.temp_dropped = False

    def key(self) -> str:
        for k in PROVIDERS[self.name]["env"]:
            if os.environ.get(k):
                return os.environ[k]
        raise SystemExit("%s: no API key in env (%s)" % (self.name, " / ".join(PROVIDERS[self.name]["env"])))

    def temp(self) -> Optional[float]:
        with self.temp_lock:
            return None if self.temp_dropped else self.temperature

    def drop_temperature(self, err: ApiError) -> bool:
        """Reasoning models reject temperature: retry without it (once, for the whole run)."""
        if self.temperature is None or err.status != 400 or "temperature" not in err.body.lower():
            return False
        with self.temp_lock:
            if not self.temp_dropped:
                self.temp_dropped = True
                log(warning="provider rejected temperature=%s; continuing WITHOUT temperature (provider default) for this run"
                            % self.temperature, provider=self.name, model=self.model, api_message=err.body[:300])
        return True

    def call(self, prompt: str) -> dict:  # -> {text, prompt_tokens, output_tokens, reasoning_tokens, finish, incomplete, api_model, request_id}
        raise NotImplementedError


class OpenAIProvider(Provider):
    name = "openai"

    def call(self, prompt: str) -> dict:
        base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        hdr = {"Authorization": "Bearer " + self.key()}
        t = self.temp()
        if self.args.openai_api == "chat":
            body = {"model": self.model, "messages": [{"role": "user", "content": prompt}], "max_completion_tokens": self.max_out}
            if self.effort:
                body["reasoning_effort"] = self.effort
            if t is not None:
                body["temperature"] = t
            r = http_post(base + "/chat/completions", hdr, body, self.timeout)
            ch = (r.get("choices") or [{}])[0]
            u = r.get("usage") or {}
            return {"text": (ch.get("message") or {}).get("content") or "", "prompt_tokens": u.get("prompt_tokens"),
                    "output_tokens": u.get("completion_tokens"),
                    "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens"),
                    "finish": ch.get("finish_reason"), "incomplete": ch.get("finish_reason") == "length",
                    "api_model": r.get("model"), "request_id": r.get("id"), "temperature_sent": t}
        body = {"model": self.model, "input": [{"role": "user", "content": prompt}], "max_output_tokens": self.max_out, "store": False}
        if self.effort:
            body["reasoning"] = {"effort": self.effort}
        if t is not None:
            body["temperature"] = t
        r = http_post(base + "/responses", hdr, body, self.timeout)
        texts, refusal = [], False
        for item in r.get("output") or []:
            if item.get("type") == "message":
                for c in item.get("content") or []:
                    if c.get("type") == "output_text":
                        texts.append(c.get("text") or "")
                    elif c.get("type") == "refusal":
                        refusal = True
        u = r.get("usage") or {}
        inc = r.get("status") == "incomplete"
        return {"text": "".join(texts), "prompt_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens"),
                "reasoning_tokens": (u.get("output_tokens_details") or {}).get("reasoning_tokens"),
                "finish": ((r.get("incomplete_details") or {}).get("reason") if inc else r.get("status")) or ("refusal" if refusal else None),
                "incomplete": inc, "api_model": r.get("model"), "request_id": r.get("id"), "temperature_sent": t}


class AnthropicProvider(Provider):
    name = "anthropic"

    def call(self, prompt: str) -> dict:
        base = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
        hdr = {"x-api-key": self.key(), "anthropic-version": "2023-06-01"}
        t = self.temp()
        body = {"model": self.model, "max_tokens": self.max_out, "messages": [{"role": "user", "content": prompt}]}
        if self.effort:
            body["output_config"] = {"effort": self.effort}
        if self.args.anthropic_thinking:
            body["thinking"] = {"type": self.args.anthropic_thinking}
        if t is not None:
            body["temperature"] = t
        r = http_post(base + "/v1/messages", hdr, body, self.timeout)
        text = "".join(b.get("text") or "" for b in r.get("content") or [] if b.get("type") == "text")
        u = r.get("usage") or {}
        return {"text": text, "prompt_tokens": (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0)
                + (u.get("cache_creation_input_tokens") or 0),
                "output_tokens": u.get("output_tokens"), "reasoning_tokens": None,  # thinking is inside output_tokens
                "finish": r.get("stop_reason"), "incomplete": r.get("stop_reason") == "max_tokens",
                "api_model": r.get("model"), "request_id": r.get("id"), "temperature_sent": t}


class GeminiProvider(Provider):
    name = "gemini"

    def call(self, prompt: str) -> dict:
        base = os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        hdr = {"x-goog-api-key": self.key()}
        t = self.temp()
        gc = {"maxOutputTokens": self.max_out}
        if t is not None:
            gc["temperature"] = t
        if self.effort:
            gc["thinkingConfig"] = {"thinkingLevel": self.effort.upper()}
        body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": gc}
        r = http_post("%s/models/%s:generateContent" % (base, self.model), hdr, body, self.timeout)
        cand = (r.get("candidates") or [{}])[0]
        parts = (cand.get("content") or {}).get("parts") or []
        text = "".join(p.get("text") or "" for p in parts if not p.get("thought"))
        u = r.get("usageMetadata") or {}
        out = (u.get("candidatesTokenCount") or 0) + (u.get("thoughtsTokenCount") or 0)
        fin = cand.get("finishReason") or ((r.get("promptFeedback") or {}).get("blockReason"))
        return {"text": text, "prompt_tokens": u.get("promptTokenCount"), "output_tokens": out,
                "reasoning_tokens": u.get("thoughtsTokenCount"), "finish": fin, "incomplete": fin == "MAX_TOKENS",
                "api_model": r.get("modelVersion"), "request_id": r.get("responseId"), "temperature_sent": t}


class MockProvider(Provider):
    """No network.  Canned RAGAS-style outputs exercising both parsers: ~70% clean JSON, 10% fenced JSON (strict ok),
    10% broken JSON with a recoverable "verdict" (lenient only), 10% prose (parse fail).  Verdict = every number of the
    claim occurs in the evidence (same stub rule as j3_judge_score.MockBackend).  ~1 in 7 rows raise one transient 429."""
    name = "mock"
    _seen = set()
    _lock = threading.Lock()

    def call(self, prompt: str) -> dict:
        tail = prompt[prompt.rfind("input: "):]
        try:
            inp = json.loads(tail[len("input: "):tail.rfind("}") + 1])
            ctx, st = inp["context"], inp["statements"][0]
        except Exception:  # noqa: BLE001
            ctx, st = "", ""
        h = int(hashlib.sha1(st.encode("utf-8")).hexdigest(), 16)
        with self._lock:
            first = st not in self._seen
            self._seen.add(st)
        if first and h % 7 == 0:
            raise ApiError(429, '{"error": "mock rate limit"}', 0.05)
        ok = int(all(n in ctx for n in re.findall(r"\d+(?:\.\d+)?", st)))
        js = json.dumps({"statements": [{"statement": st, "reason": "mock", "verdict": ok}]}, indent=4)
        kind = h % 10
        if kind == 0:
            text = "```json\n" + js + "\n```"
        elif kind == 1:
            text = '{\n "statements": [\n  {"statement": %s, "reason": "unterminated, "verdict": %d\n' % (json.dumps(st), ok)
        elif kind == 2:
            text = "The statement appears to be about a dose; I cannot decide."
        else:
            text = js
        time.sleep(0.01)
        return {"text": text, "prompt_tokens": len(prompt) // 4, "output_tokens": len(text) // 4 + 200, "reasoning_tokens": 200,
                "finish": "stop", "incomplete": False, "api_model": "mock-judge", "request_id": "mock-%x" % (h % 10 ** 8),
                "temperature_sent": self.temp()}


PROVIDER_CLS = {"openai": OpenAIProvider, "anthropic": AnthropicProvider, "gemini": GeminiProvider, "mock": MockProvider}


# ---------------------------------------------------------------- cost
class Budget:
    def __init__(self, price_in: float, price_out: float, max_usd: float, spent_prior: float, max_out: int):
        self.pi, self.po, self.max_usd, self.prior, self.max_out = price_in, price_out, max_usd, spent_prior, max_out
        self.spent = 0.0
        self.reserved = 0.0
        self.lock = threading.Lock()
        self.stopped = False

    def cost(self, ptok, otok) -> float:
        return ((ptok or 0) * self.pi + (otok or 0) * self.po) / 1e6

    def worst(self, est_prompt_tokens: int) -> float:
        return self.cost(est_prompt_tokens * 1.25 + 50, self.max_out)

    def reserve(self, est_prompt_tokens: int) -> Optional[float]:
        w = self.worst(est_prompt_tokens)
        with self.lock:
            if self.prior + self.spent + self.reserved + w > self.max_usd:
                self.stopped = True
                return None
            self.reserved += w
            return w

    def settle(self, reserved: float, actual: float) -> None:
        with self.lock:
            self.reserved -= reserved
            self.spent += actual


def estimate(rows: List[dict], provider: str, price: Tuple[float, float], assume_out: int) -> dict:
    cpt = CHARS_PER_TOKEN.get(provider, 4.0)
    ptok = [len(nli_prompt(r["evidence"], [r["claim"]])) / cpt for r in rows]
    tin, tout = sum(ptok), assume_out * len(rows)
    return {"rows": len(rows), "prompt_tokens": int(tin), "output_tokens": int(tout), "mean_prompt_tokens": (tin / len(rows)) if rows else 0,
            "usd": (tin * price[0] + tout * price[1]) / 1e6}


# ---------------------------------------------------------------- scoring
def call_with_retries(prov: Provider, prompt: str, max_retries: int, mock: bool) -> dict:
    attempt = 0
    while True:
        t0 = time.time()
        try:
            res = prov.call(prompt)
            res["latency_s"] = round(time.time() - t0, 3)
            res["attempts"] = attempt + 1
            return res
        except ApiError as e:
            if prov.drop_temperature(e):
                continue  # does not count as a retry
            if e.status not in RETRYABLE or attempt >= max_retries:
                raise
            wait = e.retry_after if e.retry_after is not None else min(60.0, 2.0 * (2 ** attempt))
            log(retry=attempt + 1, http_status=e.status, wait_s=round(wait, 2), msg=e.body[:200])
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, json.JSONDecodeError) as e:
            if attempt >= max_retries:
                raise
            wait = min(60.0, 2.0 * (2 ** attempt))
            log(retry=attempt + 1, error=type(e).__name__, msg=str(e)[:200])
        if mock:
            wait = min(wait, 0.05)
        time.sleep(wait * (1 + 0.25 * random.random()))
        attempt += 1


def run_scoring(args, rows: List[dict], out: Path) -> dict:
    pcfg = PROVIDERS[args.provider]
    price = (args.price_in, args.price_out) if args.price_in is not None and args.price_out is not None else PRICES.get(args.model)
    if price is None:
        raise SystemExit("no price known for model %r: pass --price-in and --price-out (USD per 1M tokens) so the "
                         "--max-usd guard can work" % args.model)
    existing = read_jsonl(out)
    done = {r["instance_id"] for r in existing}
    spent_prior = sum(float(r.get("cost_usd") or 0) for r in existing)
    todo = [r for r in rows if r["instance_id"] not in done]
    est = estimate(todo, args.provider, price, args.assume_output_tokens)
    est_all = estimate(rows, args.provider, price, args.assume_output_tokens)
    obs = [r for r in existing if r.get("output_tokens") is not None]
    obs_note = None
    if obs:
        mo = sum(r["output_tokens"] for r in obs) / len(obs)
        mi = sum(r.get("prompt_tokens") or 0 for r in obs) / len(obs)
        obs_note = {"rows_observed": len(obs), "mean_prompt_tokens": round(mi, 1), "mean_output_tokens": round(mo, 1),
                    "projected_usd_todo_from_observed": round(len(todo) * (mi * price[0] + mo * price[1]) / 1e6, 4)}
    plan = {"provider": args.provider, "model": args.model, "pack": args.pack, "subset": args.subset, "rows_subset": len(rows),
            "already_done": len(rows) - len(todo), "todo": len(todo), "price_usd_per_mtok": price,
            "effort": args.effort, "temperature": args.temperature, "max_output_tokens": args.max_output_tokens,
            "assumed_output_tokens_per_row(visible+reasoning)": args.assume_output_tokens,
            "estimate_todo": {k: (round(v, 4) if isinstance(v, float) else v) for k, v in est.items()},
            "estimate_full_subset_usd": round(est_all["usd"], 4), "spent_prior_usd_in_file": round(spent_prior, 4),
            "max_usd": args.max_usd, "observed_so_far": obs_note, "out": str(out)}
    log(stage="plan", **plan)
    if args.dry_run or not todo:
        return {"plan": plan, "scored": 0}
    proj = max(est["usd"], (obs_note or {}).get("projected_usd_todo_from_observed") or 0)
    if spent_prior + proj > args.max_usd:
        raise SystemExit("ABORT before any call: spent %.4f + estimated %.4f USD > --max-usd %.2f (raise --max-usd or pick a "
                         "smaller --subset)" % (spent_prior, proj, args.max_usd))
    if proj > args.confirm_above_usd and not args.yes:
        if sys.stdin.isatty():
            ans = input("Estimated %.2f USD for %d calls to %s. Proceed? [y/N] " % (proj, len(todo), args.model)).strip().lower()
            if ans not in ("y", "yes"):
                raise SystemExit("aborted by user")
        else:
            raise SystemExit("estimated %.2f USD > --confirm-above-usd %.2f and no --yes (non-interactive)" % (proj, args.confirm_above_usd))
    if args.provider != "mock" and not any(os.environ.get(k) for k in pcfg["env"]):
        raise SystemExit("%s: no API key in env (%s)" % (args.provider, " / ".join(pcfg["env"])))
    temp = None if str(args.temperature).lower() in ("none", "default", "") else float(args.temperature)
    effort = None if str(args.effort).lower() in ("none", "default", "") else args.effort
    prov = PROVIDER_CLS[args.provider](args.model, effort, temp, args.max_output_tokens, args.timeout, args)
    budget = Budget(price[0], price[1], args.max_usd, spent_prior, args.max_output_tokens)
    cpt = CHARS_PER_TOKEN.get(args.provider, 4.0)
    wlock = threading.Lock()
    stats = Counter()
    fatal = []
    t_start = time.time()

    def work(r: dict, reserved: float):
        prompt = nli_prompt(r["evidence"], [r["claim"]])
        try:
            res = call_with_retries(prov, prompt, args.max_retries, args.provider == "mock")
        except Exception as e:  # noqa: BLE001
            budget.settle(reserved, 0.0)
            return r, None, e
        cost = budget.cost(res.get("prompt_tokens"), res.get("output_tokens"))
        budget.settle(reserved, cost)
        vs, ss = parse_strict(res["text"])
        vl, _ = parse_lenient(res["text"])
        rec = {"instance_id": r["instance_id"], "pack": args.pack, "verdict": vs, "score": ss, "verdict_lenient": vl,
               "raw_output": res["text"], "finish": res.get("finish"), "incomplete": bool(res.get("incomplete")),
               "prompt_tokens": res.get("prompt_tokens"), "output_tokens": res.get("output_tokens"),
               "reasoning_tokens": res.get("reasoning_tokens"), "cost_usd": round(cost, 7), "latency_s": res.get("latency_s"),
               "attempts": res.get("attempts"), "provider": args.provider, "model": args.model, "api_model": res.get("api_model"),
               "request_id": res.get("request_id"), "effort": effort, "temperature_sent": res.get("temperature_sent"),
               "max_output_tokens": args.max_output_tokens, "prompt": PROMPT_ID_J4,
               "prompt_sha1": hashlib.sha1(prompt.encode("utf-8")).hexdigest(), "verifier": "j4_" + slugify(args.model),
               "script": SCRIPT_VERSION, "ts": now_ts(), "auto_class": r.get("auto_class") or r.get("condition")}
        with wlock:
            append_jsonl(out, [rec])
        return r, rec, None

    with cf.ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as ex:
        pending = set()
        it = iter(todo)
        exhausted = False
        while True:
            while not exhausted and not fatal and len(pending) < args.concurrency:
                r = next(it, None)
                if r is None:
                    exhausted = True
                    break
                ptok = int(len(nli_prompt(r["evidence"], [r["claim"]])) / cpt)
                res_amt = budget.reserve(ptok)
                if res_amt is None:
                    exhausted = True
                    log(stage="budget_stop", spent_run_usd=round(budget.spent, 4), spent_total_usd=round(budget.prior + budget.spent, 4),
                        max_usd=args.max_usd, msg="next request could exceed --max-usd (worst case reserved); stopping submission")
                    break
                pending.add(ex.submit(work, r, res_amt))
            if not pending:
                break
            fin, pending = cf.wait(pending, return_when=cf.FIRST_COMPLETED)
            for f in fin:
                r, rec, err = f.result()
                if err is not None:
                    stats["error"] += 1
                    msg = str(err)[:600]
                    log(stage="error", instance_id=r["instance_id"], error=type(err).__name__, msg=msg)
                    if isinstance(err, ApiError) and err.status not in RETRYABLE:
                        fatal.append(msg)  # non-retryable (bad request / auth / model id): stop submitting
                    elif stats["error"] >= args.max_errors:
                        fatal.append("too many errors (%d)" % stats["error"])
                    continue
                stats["done"] += 1
                stats[rec["verdict"]] += 1
                stats["lenient_" + rec["verdict_lenient"]] += 1
                stats["incomplete"] += int(rec["incomplete"])
                n = stats["done"]
                if n % args.log_every == 0 or n == len(todo):
                    log(stage="progress", done=n, todo=len(todo), spent_run_usd=round(budget.spent, 4),
                        mean_usd_per_row=round(budget.spent / n, 5), projected_run_usd=round(budget.spent / n * len(todo), 3),
                        pass_=stats["PASS"], fail=stats["FAIL"], parse_fail=stats["PARSE_FAIL"],
                        parse_fail_lenient=stats["lenient_PARSE_FAIL"], incomplete=stats["incomplete"],
                        temperature_dropped=prov.temp_dropped, secs=round(time.time() - t_start))
    summ = {"scored": stats["done"], "errors": stats["error"], "spent_run_usd": round(budget.spent, 5),
            "spent_total_usd": round(budget.prior + budget.spent, 5), "budget_stopped": budget.stopped, "fatal": fatal[:3],
            "temperature_dropped": prov.temp_dropped, "verdicts": {k: stats[k] for k in ("PASS", "FAIL", "PARSE_FAIL")},
            "parse_fail_lenient": stats["lenient_PARSE_FAIL"], "incomplete": stats["incomplete"]}
    log(stage="scoring_done", **summ)
    return {"plan": plan, **summ}


# ---------------------------------------------------------------- report
def frontier_files(out_dir: Path, pack: str) -> List[Path]:
    fs = sorted(out_dir.glob("*.jsonl"))
    if pack == "card":
        return [f for f in fs if f.name.endswith("__card.jsonl")]
    return [f for f in fs if "__" not in f.name]


def vmaps_from_rows(recs: List[dict]) -> Tuple[dict, dict]:
    strict, lenient = {}, {}
    for r in recs:  # recompute from raw_output so strict/lenient are defined identically for every judge
        raw = r.get("raw_output")
        if raw is None:
            v = r.get("verdict")
            if v in ("PASS", "FAIL", "PARSE_FAIL"):
                strict[r["instance_id"]] = lenient[r["instance_id"]] = v
            elif r.get("score") is not None:
                strict[r["instance_id"]] = lenient[r["instance_id"]] = "PASS" if float(r["score"]) > 0.5 else "FAIL"
            continue
        strict[r["instance_id"]] = parse_strict(raw)[0]
        lenient[r["instance_id"]] = parse_lenient(raw)[0]
    return strict, lenient


def write_report(args, rows: List[dict], out_dir: Path) -> dict:
    import numpy as np  # noqa: F401  (j3_report needs it)
    from j3_report import CARD_HDR, CB, RD_GROUPS, RD_HDR, REF_CARD, card_row_md, judge_card, rd_block, rd_rows_md  # noqa: E402
    from j3_common import verdict_map  # noqa: E402

    ids = {r["instance_id"] for r in rows}
    files = frontier_files(out_dir, args.pack)
    gen = dt.datetime.now(TZ7).strftime("%Y-%m-%d %H:%M UTC+7")
    res = {"generated_by": "scripts/journal4/frontier_judges_rd.py", "generated_at": gen, "pack": args.pack, "subset": args.subset,
           "n_rows": len(rows), "prompt": PROMPT_ID_J4, "prompt_matches_src": prompt_check(), "lenient_regex": LENIENT_RE.pattern,
           "frontier": {}, "ref": {}}
    models = OrderedDict()
    for f in files:
        recs = [r for r in read_jsonl(f) if r.get("instance_id") in ids]
        allrecs = read_jsonl(f)
        if not allrecs:
            continue
        name = allrecs[0].get("model") or f.stem
        s, l = vmaps_from_rows(recs)
        n = len(recs)
        tot = lambda k: sum((r.get(k) or 0) for r in recs)  # noqa: E731
        info = {"file": str(f.relative_to(ROOT)) if str(f).startswith(str(ROOT)) else str(f), "provider": allrecs[0].get("provider"),
                "api_model": sorted({str(r.get("api_model")) for r in recs}) if recs else [],
                "effort": allrecs[0].get("effort"), "temperature_sent": sorted({str(r.get("temperature_sent")) for r in recs}),
                "max_output_tokens": allrecs[0].get("max_output_tokens"), "rows_in_subset": n, "rows_in_file": len(allrecs),
                "parse_fail_strict": sum(1 for v in s.values() if v == "PARSE_FAIL"),
                "parse_fail_lenient": sum(1 for v in l.values() if v == "PARSE_FAIL"),
                "incomplete": sum(1 for r in recs if r.get("incomplete")),
                "mean_prompt_tokens": (tot("prompt_tokens") / n) if n else None, "mean_output_tokens": (tot("output_tokens") / n) if n else None,
                "mean_reasoning_tokens": (tot("reasoning_tokens") / n) if n else None,
                "cost_usd_subset": round(sum(float(r.get("cost_usd") or 0) for r in recs), 5),
                "cost_usd_file": round(sum(float(r.get("cost_usd") or 0) for r in allrecs), 5)}
        if n:
            info["cost_per_row_usd"] = info["cost_usd_subset"] / n
        models[name] = (info, s, l)
    pre_full = load_precheck()
    pre = {k: v.get("ai_label") for k, v in pre_full.items()}
    L = ["# Journal 4 — frontier API LLM judges on %s (subset `%s`, %d rows)" % ("real-dose answers" if args.pack == "rd" else "the frozen DOSE card",
                                                                                args.subset, len(rows)), "",
         "Generated %s by `scripts/journal4/frontier_judges_rd.py`. Prompt: %s (identical to `src/verifiers/ragas_nli_prompt.py`: %s). "
         "STRICT verdict = the paper parser (`v4_ragas_nli.parse_verdict`, vendored in `scripts/journal3/j3_ragas_prompt.py`); "
         "LENIENT = strict, else first regex match `%s` in the raw output (recomputed from `raw_output` for every judge, incl. the "
         "existing ones)." % (gen, PROMPT_ID_J4, res["prompt_matches_src"], LENIENT_RE.pattern), ""]
    if args.pack == "rd":
        L += ["RD labels are AUTOMATIC (`rd_extract.py`); precheck-true = AI pre-check `true_unit_error` (n=%d, AI-made, not human). "
              "Metrics = `scripts/journal3/j3_report.py` section 1 (imported `rd_block`): group cells = %% of the group with the wanted "
              "verdict among scored rows (PASS on correct, FAIL on errors), slips/1000 = error answers that PASS per 1000 scored, "
              "drug-clustered bootstrap 95%% CI. Reference rows are recomputed on exactly the same rows." % sum(1 for v in pre.values() if v == "true_unit_error"), ""]
    L += ["## Runs", "", "| model | provider | api model | effort | temperature sent | max out | rows | parse fail strict | parse fail lenient | "
          "truncated | mean in / out (reasoning) tokens | cost subset USD | USD/row |", "|" + "---|" * 13]
    for name, (info, s, l) in models.items():
        res["frontier"][name] = {"info": info}
        L.append("| %s | %s | %s | %s | %s | %s | %d | %d | %d | %d | %s | %.4f | %s |" % (
            name, info["provider"], ",".join(info["api_model"]), info["effort"], ",".join(info["temperature_sent"]), info["max_output_tokens"],
            info["rows_in_subset"], info["parse_fail_strict"], info["parse_fail_lenient"], info["incomplete"],
            ("%.0f / %.0f (%s)" % (info["mean_prompt_tokens"], info["mean_output_tokens"],
                                    "%.0f" % info["mean_reasoning_tokens"] if info["mean_reasoning_tokens"] else "n/a")) if info["rows_in_subset"] else "-",
            info["cost_usd_subset"], ("%.5f" % info["cost_per_row_usd"]) if info.get("cost_per_row_usd") else "-"))
    if not models:
        L.append("| (no frontier results yet in %s) |" % out_dir)

    if args.pack == "rd":
        cb = CB([r["drug"] for r in rows], args.boot)
        refs = OrderedDict()
        for nm, fname in (("Llama-3.3-70B RAGAS (paper)", "v4_ragas_nli.jsonl"), ("Mistral-Small-24B MedScore (paper)", "v1_medscore.jsonl"),
                          ("MiniCheck-DeBERTa (paper)", "t6_minicheck_deberta.jsonl"), ("MiniCheck-Flan-T5-Large (paper)", "v2a_minicheck.jsonl"),
                          ("AlignScore-large (paper)", "v3_alignscore.jsonl")):
            p = RD_SCORES / fname
            if p.is_file():
                recs = read_jsonl(p)
                if fname.startswith("v4"):
                    refs[nm] = vmaps_from_rows(recs)
                else:  # non-generative checkers: stored verdict / score > 0.5 (no parsing involved)
                    vm = verdict_map(p)
                    refs[nm] = (vm, vm)
        for p in sorted(J3_JUDGES.glob("*__rd.jsonl")):
            refs["judge %s (chain 3, vLLM)" % p.name.split("__")[0]] = vmaps_from_rows(read_jsonl(p))
        for mode, idx in (("STRICT (paper parser; comparable to all existing rows)", 1), ("LENIENT (regex fallback)", 2)):
            L += ["", "## RD metrics — %s" % mode, "", "Coverage = scored (PASS/FAIL) / subset rows; PARSE_FAIL and unscored rows are "
                  "excluded from the cells (as in j3_report).", ""] + RD_HDR
            for name, tup in models.items():
                b = rd_block(rows, {k: v for k, v in tup[idx].items()}, pre, cb)
                res["frontier"][name]["rd_" + ("strict" if idx == 1 else "lenient")] = b
                L.append(rd_rows_md("**%s**" % name, b))
            for nm, (s, l) in refs.items():
                b = rd_block(rows, s if idx == 1 else l, pre, cb)
                res["ref"].setdefault(nm, {})["rd_" + ("strict" if idx == 1 else "lenient")] = b
                L.append(rd_rows_md("ref: " + nm, b))
        # per-case table: the 12 AI-precheck true unit errors (whatever the subset, if they were scored)
        true_ids = [k for k, v in pre_full.items() if v.get("ai_label") == "true_unit_error"]
        j3 = OrderedDict((p.name.split("__")[0], vmaps_from_rows(read_jsonl(p))[0]) for p in sorted(J3_JUDGES.glob("*__rd.jsonl")))
        cols = [("pass_minicheck_roberta", "MC-R"), ("pass_minicheck_deberta", "MC-D"), ("pass_alignscore_base", "AS-b"),
                ("pass_minicheck_flant5", "MC-T5"), ("pass_alignscore_large", "AS-L"), ("pass_ragas_llama70b", "L70B"),
                ("pass_medscore_mistral24b", "MedS")]
        L += ["", "## The 12 AI-precheck true unit errors (per case)", "",
              "Wanted verdict = FAIL. Existing columns from `qc/ai_precheck_real_dose_unit_errors.csv` (P = PASS = error slipped through): "
              + ", ".join("%s=%s" % (b, a.replace("pass_", "")) for a, b in cols) + ". Chain-3 local judges: strict verdicts, "
              "P/F/? (? = parse fail) in the order " + ", ".join(j3) + ". Frontier: strict verdict (lenient in brackets if different; "
              "– = not scored).", "",
              "| check | drug | mode/gen | mechanism | label dose | answer dose | " + " | ".join(b for _, b in cols) + " | chain-3 judges | "
              + " | ".join(models) + " |", "|" + "---|" * (6 + len(cols) + 1 + len(models))]
        ab = {"PASS": "P", "FAIL": "F", "PARSE_FAIL": "?"}
        res["true12"] = []
        for iid in sorted(true_ids, key=lambda i: pre_full[i]["check_id"]):
            pr = pre_full[iid]
            fr = OrderedDict()
            for name, (info, s, l) in models.items():
                fr[name] = {"strict": s.get(iid), "lenient": l.get(iid)}
            res["true12"].append({"instance_id": iid, "check_id": pr["check_id"], "drug": pr["drug"], "label_dose": pr["label_dose_auto"],
                                  "answer_dose": pr["answer_dose_auto"], "mechanism": pr["ai_mechanism"],
                                  "existing": {b: pr.get(a) for a, b in cols}, "chain3": {k: v.get(iid) for k, v in j3.items()}, "frontier": fr})
            fcell = []
            for name in models:
                st, le = fr[name]["strict"], fr[name]["lenient"]
                fcell.append("–" if st is None else ("**%s**" % st if st == "PASS" else st) + ("" if le == st else " [%s]" % le))
            L.append("| %s | %s | %s/%s | %s | %s | %s | %s | %s | %s |" % (
                pr["check_id"], pr["drug"], pr["mode"], pr["generator"], pr["ai_mechanism"], pr["label_dose_auto"], pr["answer_dose_auto"],
                " | ".join(ab.get(pr.get(a), pr.get(a) or "") for a, _ in cols), "".join(ab.get(v.get(iid), "–") for v in j3.values()),
                " | ".join(fcell)))
    else:
        card = rows
        L += ["", "## Card — per-condition verdicts (raw counts; wanted: PASS on C0/INV-claim, FAIL on E1-*)", "",
              "| model | parser | " + " | ".join(sorted({r["condition"] for r in card})) + " |", "|" + "---|" * (2 + len({r["condition"] for r in card}))]
        conds = sorted({r["condition"] for r in card})
        for name, (info, s, l) in models.items():
            for lab, vm in (("strict", s), ("lenient", l)):
                cells = []
                for c in conds:
                    vs = [vm.get(r["instance_id"]) for r in card if r["condition"] == c]
                    cells.append("P%d F%d ?%d" % (vs.count("PASS"), vs.count("FAIL"), vs.count("PARSE_FAIL")))
                L.append("| %s | %s | %s |" % (name, lab, " | ".join(cells)))
        full = read_jsonl(PACK_FILES["card"])
        if args.subset == "all":
            L += ["", "## Card — paper cells (C0-conditional; only when all %d rows are scored)" % len(full), ""] + CARD_HDR
            for name, (info, s, l) in models.items():
                m = judge_card(full, s, {}) if len(s) >= len(full) else None
                res["frontier"][name]["card_strict"] = m
                L.append(card_row_md(name + " (strict)", m))
            for p in sorted(J3_JUDGES.glob("*__card.jsonl")):
                vm = vmaps_from_rows(read_jsonl(p))[0]
                L.append(card_row_md("ref: judge %s (chain 3)" % p.name.split("__")[0], judge_card(full, vm, {}) if len(vm) >= len(full) else None))
            for nm, paths in REF_CARD:
                vm = {}
                for p in paths:
                    vm.update(vmaps_from_rows(read_jsonl(p))[0])
                L.append(card_row_md("ref: " + nm, judge_card(full, vm, {}) if vm else None))
    L += ["", "## Caveats", "",
          "- Frontier models are reasoning models: temperature 0 is sent where accepted; if the API rejects it the run continues "
          "with the provider default (column 'temperature sent'). Hidden reasoning/thinking tokens are billed as output and count "
          "against the max-output cap; 'truncated' = cap hit (verdict usually PARSE_FAIL).",
          "- Model IDs are aliases/snapshots as served on the run date (`api model` column); provider-side changes can alter results.",
          "- RD error labels are automatic; the 12 precheck-true cases are AI-checked, not human-verified."]
    out_md = out_dir / ("report_%s_%s.md" % (args.pack, args.subset))
    out_json = out_dir / ("report_%s_%s.json" % (args.pack, args.subset))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(L) + "\n", encoding="utf-8")
    out_json.write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    log(stage="report", wrote=[str(out_md), str(out_json)], models=list(models))
    return res


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--provider", choices=list(PROVIDERS), help="openai | anthropic | gemini | mock")
    ap.add_argument("--model", help="model id (default per provider: %s)" % ", ".join("%s=%s" % (k, v["model"]) for k, v in PROVIDERS.items()))
    ap.add_argument("--pack", choices=["rd", "card"], default="rd")
    ap.add_argument("--subset", default="smoke", help="rd: all|adjudicable|flagged47|true12|smoke ; card: all|smoke (default smoke)")
    ap.add_argument("--effort", default=None, help="reasoning effort / thinking level (openai reasoning.effort, anthropic "
                    "output_config.effort, gemini thinkingLevel); 'none' = do not send. Default: low")
    ap.add_argument("--temperature", default="0", help="sent if the provider accepts it; 'none' = never send (default 0)")
    ap.add_argument("--max-output-tokens", type=int, default=None,
                    help="hard cap on output INCLUDING hidden reasoning tokens (default 2048; visible JSON is ~100-200 tokens; "
                         "mock 512)")
    ap.add_argument("--openai-api", choices=["responses", "chat"], default="responses")
    ap.add_argument("--anthropic-thinking", default=None, help="optional thinking.type, e.g. 'between_tools' on Sonnet 5.5 "
                    "(no up-front thinking); Opus 5.5 rejects 'disabled'")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--max-retries", type=int, default=6)
    ap.add_argument("--max-errors", type=int, default=20, help="stop after this many failed rows (retryable errors exhausted)")
    ap.add_argument("--timeout", type=float, default=180.0)
    ap.add_argument("--max-usd", type=float, default=None,
                    help="hard cap on cumulative spend in this model's output file (default: 1.0 for smoke, else 5.0)")
    ap.add_argument("--confirm-above-usd", type=float, default=5.0, help="ask (or need --yes) if the estimate exceeds this")
    ap.add_argument("--yes", action="store_true", help="no interactive confirmation")
    ap.add_argument("--price-in", type=float, default=None, help="USD per 1M input tokens (overrides PRICES)")
    ap.add_argument("--price-out", type=float, default=None, help="USD per 1M output tokens (overrides PRICES)")
    ap.add_argument("--assume-output-tokens", type=int, default=None,
                    help="pre-run estimate: output tokens per row incl. reasoning (default 450 = ~150 visible + ~300 reasoning)")
    ap.add_argument("--out-dir", default=None, help="default results/journal4/frontier (mock: results/journal4/frontier_mock)")
    ap.add_argument("--dry-run", action="store_true", help="print the plan + cost estimate, make no API call")
    ap.add_argument("--report-only", action="store_true", help="only (re)write the report from existing jsonl files")
    ap.add_argument("--no-report", action="store_true")
    ap.add_argument("--boot", type=int, default=2000, help="bootstrap resamples for the report (j3_report uses 10000)")
    ap.add_argument("--log-every", type=int, default=25)
    args = ap.parse_args()

    if args.max_usd is None:
        args.max_usd = 1.0 if args.subset == "smoke" else 5.0
    if args.max_output_tokens is None:
        args.max_output_tokens = 512 if args.provider == "mock" else 2048
    if args.assume_output_tokens is None:
        args.assume_output_tokens = 450
    if args.effort is None:
        args.effort = PROVIDERS[args.provider]["effort"] if args.provider else "low"
    rows = select_rows(args.pack, args.subset)
    out_dir = Path(args.out_dir) if args.out_dir else (OUT_DIR.parent / "frontier_mock" if args.provider == "mock" else OUT_DIR)
    if args.report_only:
        write_report(args, rows, out_dir)
        return
    if not args.provider:
        raise SystemExit("--provider is required (or --report-only)")
    args.model = args.model or PROVIDERS[args.provider]["model"]
    pc = prompt_check()
    if pc is False:
        raise SystemExit("prompt drift: scripts/journal3/j3_ragas_prompt.nli_prompt != src/verifiers/ragas_nli_prompt.nli_prompt")
    out = out_dir / ("%s%s.jsonl" % (slugify(args.model), "" if args.pack == "rd" else "__" + args.pack))
    log(stage="start", script=SCRIPT_VERSION, python=sys.version.split()[0], provider=args.provider, model=args.model, pack=args.pack,
        subset=args.subset, rows=len(rows), prompt=PROMPT_ID_J4, prompt_matches_src=pc,
        classes=dict(Counter(r.get("auto_class") or r.get("condition") for r in rows)))
    summ = run_scoring(args, rows, out)
    if not args.dry_run and not args.no_report:
        write_report(args, rows, out_dir)
    if summ.get("fatal"):
        sys.exit(3)


if __name__ == "__main__":
    main()
