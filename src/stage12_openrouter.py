"""Expansion Stage-1: Qwen2.5-72B claims + Phi-4 validator via OpenRouter (Stage-1 v2 rules)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "expand"))

from expand_budget import ExpandBudgetStop, assert_ok, record_cost  # noqa: E402
from llm_client import chat, map_concurrent  # noqa: E402
from openrouter_runtime import load_tokenizer  # noqa: E402
from perturb import perturb_one  # noqa: E402
from stage12_llm import (  # noqa: E402
    GEN_SYSTEM,
    INV_SYSTEM,
    VAL_SYSTEM,
    clean_claim,
    gen_user,
    inv_user,
    read_jsonl,
    render,
    val_user,
    write_jsonl,
)
from text_utils import first_word  # noqa: E402

GEN_OR = os.environ.get("MEDVERIF_EXPAND_GEN_MODEL", "qwen/qwen-2.5-72b-instruct")
VAL_OR = os.environ.get("MEDVERIF_EXPAND_VAL_MODEL", "microsoft/phi-4")
GEN_TOK = os.environ.get("MEDVERIF_EXPAND_GEN_TOKENIZER", "Qwen/Qwen2.5-72B-Instruct")
VAL_TOK = os.environ.get("MEDVERIF_EXPAND_VAL_TOKENIZER", "microsoft/phi-4")
VAL_REV = os.environ.get("MEDVERIF_EXPAND_VAL_REV", "2db69c1c3e91a05d2c64a3185acfbaf36f744e25")
PAUSE = ROOT / "notes" / "pause_expand_openrouter"


def wait_if_paused() -> None:
    while PAUSE.is_file():
        print(json.dumps({"expand": "paused", "file": str(PAUSE)}), flush=True)
        time.sleep(90)


def classify_claim(row: dict, raw: dict) -> tuple[dict | None, str | None]:
    if raw.get("finish_reason") == "length":
        return None, "generator_truncated"
    claim = clean_claim(raw.get("raw_output") or "")
    if not claim:
        return None, "generator_empty"
    span = row["target_span"]
    count = claim.count(span)
    if count == 0:
        return None, "span_missing_in_claim"
    if count != 1:
        return None, "span_not_unique_in_claim"
    start = claim.find(span)
    end = start + len(span)
    return (
        {
            "id": row["cand_id"],
            "type": row["type"],
            "evidence": row["evidence"],
            "claim": claim,
            "target_span_evidence": span,
            "target_span_claim": claim[start:end],
            "source_passage_id": row["source_passage_id"],
            "evidence_span_start": row["evidence_span_start"],
            "evidence_span_end": row["evidence_span_end"],
            "claim_span_start": start,
            "claim_span_end": end,
            "target_sentence": row["target_sentence"],
            "book": row["book"],
            "dose_number": row["dose_number"],
            "dose_unit": row["dose_unit"],
            "polarity_cue": row["polarity_cue"],
            "generator_model": GEN_OR,
            "generator_revision": "openrouter",
            "generator_raw": raw.get("raw_output"),
        },
        None,
    )


def or_yes_no(
    system: str,
    users: list[str],
    *,
    tok,
    provider: str | None,
    cand_id: str,
    phase: str,
) -> list[dict]:
    out = []
    for user in users:
        wait_if_paused()
        assert_ok()
        prompt = render(tok, system, user)
        resp = chat(
            model=VAL_OR,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=16,
            temperature=0.0,
            provider=provider,
            allow_fallbacks=False,
        )
        record_cost(resp.cost_usd, cand_id=cand_id, phase=phase)
        word = first_word(resp.text or "")
        if word not in {"yes", "no"}:
            label = "UNPARSEABLE"
        else:
            label = "YES" if word == "yes" else "NO"
        out.append(
            {
                "raw_output": resp.text,
                "label": label,
                "finish_reason": "stop",
            }
        )
    return out


def generate_one(row: dict, gen_tok, gen_provider: str | None) -> dict:
    wait_if_paused()
    assert_ok()
    prompt = render(gen_tok, GEN_SYSTEM, gen_user(row))
    resp = chat(
        model=GEN_OR,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=256,
        temperature=0.0,
        seed=42,
        provider=gen_provider,
        allow_fallbacks=False,
    )
    record_cost(resp.cost_usd, cand_id=row["cand_id"], phase="generator")
    finish = "length" if resp.completion_tokens >= 256 else "stop"
    return {
        "cand_id": row["cand_id"],
        "model": GEN_OR,
        "revision": "openrouter",
        "prompt": prompt,
        "raw_output": resp.text,
        "finish_reason": finish,
        "provider": resp.provider,
        "request_id": resp.request_id,
    }


def load_gen_done(path: Path) -> dict[str, dict]:
    done: dict[str, dict] = {}
    if path.is_file():
        for row in read_jsonl(path):
            done[row["cand_id"]] = row
    return done


def load_finished_ids(outdir: Path) -> set[str]:
    finished: set[str] = set()
    drops = outdir / "drops.jsonl"
    if drops.is_file():
        for row in read_jsonl(drops):
            finished.add(row["cand_id"])
    bases = outdir / "base_pairs.jsonl"
    if bases.is_file():
        for row in read_jsonl(bases):
            finished.add(row["id"])
    return finished


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def sort_candidates(rows: list[dict]) -> list[dict]:
    def key(row: dict) -> tuple[int, str]:
        return (0 if row["type"] == "POLARITY" else 1, row["cand_id"])

    return sorted(rows, key=key)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--candidates",
        type=Path,
        default=ROOT / "data" / "expand" / "candidates_selected.jsonl",
    )
    parser.add_argument("--outdir", type=Path, default=ROOT / "data" / "expand" / "stage1")
    parser.add_argument(
        "--template-note",
        type=Path,
        default=ROOT / "notes" / "expand_chat_template.md",
    )
    args = parser.parse_args()
    rows = sort_candidates(read_jsonl(args.candidates))
    args.outdir.mkdir(parents=True, exist_ok=True)
    gen_path = args.outdir / "generator_raw.jsonl"
    gen_done = load_gen_done(gen_path)
    finished = load_finished_ids(args.outdir)

    gen_provider = os.environ.get("MEDVERIF_EXPAND_GEN_PROVIDER") or os.environ.get(
        "MEDVERIF_V1_PROVIDER", "DeepInfra"
    )
    val_provider = os.environ.get("MEDVERIF_EXPAND_VAL_PROVIDER") or os.environ.get(
        "MEDVERIF_OPENROUTER_PROVIDER", ""
    ).strip() or None

    gen_tok = load_tokenizer(GEN_TOK)
    val_tok = load_tokenizer(VAL_TOK, revision=VAL_REV)

    pending_gen = [r for r in rows if r["cand_id"] not in gen_done and r["cand_id"] not in finished]
    workers = max(1, int(os.environ.get("MEDVERIF_OR_MAX_INFLIGHT", "2")))

    def _gen(row: dict) -> tuple[str, dict]:
        rec = generate_one(row, gen_tok, gen_provider)
        return row["cand_id"], rec

    if pending_gen:
        for chunk_start in range(0, len(pending_gen), workers * 4):
            chunk = pending_gen[chunk_start : chunk_start + workers * 4]
            for cid, rec in map_concurrent(_gen, chunk, max_workers=workers):
                append_jsonl(gen_path, rec)
                gen_done[cid] = rec

    if not args.template_note.is_file() and gen_done:
        sample = next(iter(gen_done.values()))
        args.template_note.parent.mkdir(parents=True, exist_ok=True)
        args.template_note.write_text(
            "# Expansion Stage-1 OpenRouter templates\n\n"
            f"Generator: `{GEN_OR}` tokenizer `{GEN_TOK}`\n\n"
            f"Validator: `{VAL_OR}` tokenizer `{VAL_TOK}` rev `{VAL_REV}`\n\n"
            "```\n" + (sample.get("prompt") or "")[:4000] + "\n```\n"
        )

    drops = Counter()
    kept_bases = 0
    kept_instances = 0

    for row in rows:
        cid = row["cand_id"]
        if cid in finished:
            continue
        raw = gen_done.get(cid)
        if not raw:
            continue
        built, reason = classify_claim(row, raw)
        if reason:
            drops[reason] += 1
            append_jsonl(args.outdir / "drops.jsonl", {"cand_id": cid, "reason": reason})
            finished.add(cid)
            continue
        val_out = or_yes_no(
            VAL_SYSTEM,
            [val_user(built["evidence"], built["claim"])],
            tok=val_tok,
            provider=val_provider,
            cand_id=cid,
            phase="validator",
        )[0]
        append_jsonl(
            args.outdir / "validator_raw.jsonl",
            {"id": cid, "label": val_out["label"], "raw_output": val_out["raw_output"]},
        )
        if val_out["label"] != "YES":
            reason = (
                "validator_unparseable"
                if val_out["label"] == "UNPARSEABLE"
                else "validator_no"
            )
            drops[reason] += 1
            append_jsonl(args.outdir / "drops.jsonl", {"cand_id": cid, "reason": reason})
            finished.add(cid)
            continue
        base = dict(built)
        base["validator_model"] = VAL_OR
        base["validator_revision"] = VAL_REV
        base["validator_raw"] = val_out["raw_output"]
        pending_inst, failed = perturb_one(base)
        if failed:
            drops["perturb_" + failed[0]["reason"]] += 1
            append_jsonl(
                args.outdir / "drops.jsonl",
                {"cand_id": cid, "reason": "perturb_" + failed[0]["reason"]},
            )
            finished.add(cid)
            continue
        inv_rows = [r for r in pending_inst if r["condition"] == "INV-claim"]
        inv_users = [
            inv_user(
                r["claim_c0"],
                r["claim"],
                r["diff"]["claim"]["span_before"],
                r["claim_span"],
            )
            for r in inv_rows
        ]
        inv_out = (
            or_yes_no(
                INV_SYSTEM,
                inv_users,
                tok=val_tok,
                provider=val_provider,
                cand_id=cid,
                phase="inv",
            )
            if inv_users
            else []
        )
        inv_ok = True
        for inv_row, rec in zip(inv_rows, inv_out):
            append_jsonl(
                args.outdir / "inv_raw.jsonl",
                {
                    "instance_id": inv_row["instance_id"],
                    "base_id": inv_row["base_id"],
                    "label": rec["label"],
                    "raw_output": rec["raw_output"],
                },
            )
            if rec["label"] != "YES":
                inv_ok = False
                drops[
                    "inv_unparseable"
                    if rec["label"] == "UNPARSEABLE"
                    else "inv_meaning_rejected"
                ] += 1
        if not inv_ok:
            append_jsonl(args.outdir / "drops.jsonl", {"cand_id": cid, "reason": "inv_rejected"})
            finished.add(cid)
            continue
        append_jsonl(args.outdir / "base_pairs.jsonl", base)
        for inst in pending_inst:
            append_jsonl(args.outdir / "instances.jsonl", inst)
        kept_bases += 1
        kept_instances += len(pending_inst)
        finished.add(cid)
        print(
            json.dumps(
                {
                    "kept_base": cid,
                    "type": row["type"],
                    "bases_total": kept_bases,
                    "instances_total": kept_instances,
                }
            ),
            flush=True,
        )

    bases = read_jsonl(args.outdir / "base_pairs.jsonl")
    instances = read_jsonl(args.outdir / "instances.jsonl")
    type_counts = Counter(row["type"] for row in bases)
    stats = {
        "generator_model": GEN_OR,
        "validator_model": VAL_OR,
        "candidates_attempted": len(rows),
        "attempted_by_type": dict(Counter(row["type"] for row in rows)),
        "bases_kept": len(bases),
        "bases_kept_by_type": dict(type_counts),
        "instances": len(instances),
        "drops": dict(drops),
        "expand_spend_usd": assert_ok().get("spent_usd"),
    }
    (args.outdir / "llm_stats.json").write_text(json.dumps(stats, indent=2) + "\n")
    # Symlink-style copies for downstream rebuild
    write_jsonl(ROOT / "data" / "expand" / "base_pairs.jsonl", bases)
    write_jsonl(ROOT / "data" / "expand" / "instances_pre_rebuild.jsonl", instances)
    print(json.dumps(stats, indent=2))
    unfinished = [r["cand_id"] for r in rows if r["cand_id"] not in finished]
    if unfinished:
        print(
            json.dumps({"status": "incomplete", "unfinished": len(unfinished)}),
            flush=True,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except ExpandBudgetStop as exc:
        print(json.dumps({"error": str(exc)}), flush=True)
        raise SystemExit(2) from exc
