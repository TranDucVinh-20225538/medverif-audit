"""Forbidden keys for T15 training (disjoint from evaluation packs)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

from text_utils import normalize_ws

ROOT = Path(__file__).resolve().parents[1]


def sentence_hash(text: str) -> str:
    norm = normalize_ws(text or "").casefold()
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def _iter_jsonl(path: Path) -> Iterable[dict]:
    if not path.is_file():
        return
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def _add_base(row: dict, bases: set[str]) -> None:
    for key in ("id", "base_id"):
        val = row.get(key)
        if val:
            bases.add(str(val))


def _add_passage(row: dict, passages: set[str]) -> None:
    val = row.get("source_passage_id")
    if val:
        passages.add(str(val))


def _add_sentence(row: dict, sentences: set[str]) -> None:
    for key in ("target_sentence", "generator_raw", "claim_c0"):
        val = row.get(key)
        if val:
            sentences.add(sentence_hash(str(val)))
            break


def collect_forbidden(root: Path | None = None) -> dict:
    root = root or ROOT
    bases: set[str] = set()
    passages: set[str] = set()
    sentences: set[str] = set()

    base_globs = [
        root / "data/expand/bases_main.jsonl",
        root / "data/expand/bases_threshold.jsonl",
        root / "data/v2/bases_dose.jsonl",
        root / "data/v2/bases_polarity.jsonl",
    ]
    for path in base_globs:
        for row in _iter_jsonl(path):
            _add_base(row, bases)
            _add_passage(row, passages)
            _add_sentence(row, sentences)

    instance_globs = [
        root / "data/expand/instances_main.jsonl",
        root / "data/v3/instances_main.jsonl",
        root / "data/v3/instances_inv_families.jsonl",
        root / "data/t3/instances_inv_families.jsonl",
        root / "data/t7/instances_e1_unit.jsonl",
        root / "data/t14/instances_t14.jsonl",
        root / "data/t9/instances_all.jsonl",
        root / "data/v3/instances_pol_flip_pending_node30.jsonl",
    ]
    for path in instance_globs:
        for row in _iter_jsonl(path):
            _add_base(row, bases)
            _add_passage(row, passages)
            _add_sentence(row, sentences)

    extra_dirs = [
        root / "data/t17",
        root / "data/t18",
        root / "data/t13",
    ]
    for d in extra_dirs:
        if not d.is_dir():
            continue
        for path in d.glob("*.jsonl"):
            for row in _iter_jsonl(path):
                _add_base(row, bases)
                _add_passage(row, passages)
                _add_sentence(row, sentences)

    return {
        "base_ids": bases,
        "source_passage_ids": passages,
        "sentence_hashes": sentences,
    }


def row_blocked(row: dict, forbidden: dict) -> str | None:
    bid = str(row.get("base_id") or row.get("id") or "")
    if bid and bid in forbidden["base_ids"]:
        return "base_id"
    pid = str(row.get("source_passage_id") or "")
    if pid and pid in forbidden["source_passage_ids"]:
        return "source_passage_id"
    sent = row.get("target_sentence") or ""
    if sent and sentence_hash(sent) in forbidden["sentence_hashes"]:
        return "sentence_hash"
    return None
