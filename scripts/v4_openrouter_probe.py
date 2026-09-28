#!/usr/bin/env python3
"""Probe V4 OpenRouter configs (20 items each). Non-thinking gates only."""

from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from llm_client import assert_no_thinking_leak, chat
from openrouter_runtime import load_tokenizer
from verifiers.v4_ragas_nli import MODEL, REVISION, _tokenizer_spec, parse_verdict, render

N = 20
MAX_CT = 150


def load_sample() -> list[dict]:
    from verifiers.io_utils import read_jsonl

    rows = [r for r in read_jsonl(ROOT / "data" / "v3" / "instances_cpu_main.jsonl") if r.get("valid", True)]
    random.seed(42)
    return random.sample(rows, min(N, len(rows)))


def eval_config(name: str, rows: list[dict], tok, *, provider: str, extra: dict, suffix: str) -> dict:
    results = []
    for row in rows:
        prompt = render(tok, row["evidence"], row["claim"]) + (suffix or "")
        body_extra = {"chat_template_kwargs": {"enable_thinking": False}, **extra}
        try:
            resp = chat(
                model=os.environ.get("MEDVERIF_V4_OPENROUTER_MODEL", "qwen/qwen3-14b"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                provider=provider,
                allow_fallbacks=False,
                extra_body=body_extra,
                refuse_reasoning_only=False,
            )
            raw = resp.text or ""
            if resp.reasoning:
                verdict = "REJECT_REASONING"
            elif resp.completion_tokens > MAX_CT:
                verdict = "REJECT_TOKENS"
            else:
                try:
                    assert_no_thinking_leak(raw)
                except RuntimeError:
                    verdict = "REJECT_THINK_TAG"
                else:
                    verdict, _ = parse_verdict(raw)
            results.append({
                "instance_id": row["instance_id"],
                "verdict": verdict,
                "completion_tokens": resp.completion_tokens,
                "has_reasoning": bool(resp.reasoning),
                "raw_preview": raw[:400],
            })
        except Exception as exc:
            results.append({
                "instance_id": row["instance_id"],
                "verdict": "ERROR",
                "error": str(exc)[:200],
            })
    parsed_ok = sum(1 for r in results if r.get("verdict") not in {
        "PARSE_FAIL", "ERROR", "REJECT_REASONING", "REJECT_TOKENS", "REJECT_THINK_TAG"
    })
    parse_rate = parsed_ok / max(len(results), 1)
    passed = (
        parse_rate >= 0.95
        and all(not r.get("has_reasoning") for r in results if "has_reasoning" in r)
        and all(r.get("completion_tokens", 999) <= MAX_CT for r in results if "completion_tokens" in r)
    )
    return {
        "config": name,
        "provider": provider,
        "extra": extra,
        "suffix": suffix,
        "n": len(results),
        "parse_rate": parse_rate,
        "passed": passed,
        "examples": [r for r in results if r.get("raw_preview")][:3],
        "results": results,
    }


def _write_report(out_path: Path, report: list, winner: dict | None) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"configs": report, "winner": winner}, indent=2) + "\n")


def main() -> None:
    rows = load_sample()
    tok_model, tok_rev = _tokenizer_spec()
    tok = load_tokenizer(tok_model, tok_rev)
    out_path = ROOT / "notes" / "v4_openrouter_probe.json"
    configs = [
        ("reasoning_enabled_false_deepinfra", "DeepInfra", {"reasoning": {"enabled": False}, "chat_template_kwargs": {"enable_thinking": False}}, ""),
        ("reasoning_effort_none_deepinfra", "DeepInfra", {"reasoning": {"effort": "none"}, "chat_template_kwargs": {"enable_thinking": False}}, ""),
        ("reasoning_enabled_false_alibaba", "Alibaba", {"reasoning": {"enabled": False}, "chat_template_kwargs": {"enable_thinking": False}}, ""),
        ("no_think_suffix_deepinfra", "DeepInfra", {"reasoning": {"enabled": False}, "chat_template_kwargs": {"enable_thinking": False}}, " /no_think"),
    ]
    report = []
    winner = None
    for name, prov, extra, suffix in configs:
        print(json.dumps({"probing": name}), flush=True)
        rep = eval_config(name, rows, tok, provider=prov, extra=extra, suffix=suffix)
        report.append(rep)
        if rep["passed"] and winner is None:
            winner = rep
        _write_report(out_path, report, winner)
    print(json.dumps({"winner": winner["config"] if winner else None, "report": str(out_path)}))


if __name__ == "__main__":
    main()
