#!/usr/bin/env python3
"""One scoring-valid instance per T3-queue OpenRouter verifier (smoke before auto-start)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INST = ROOT / "data/v3/instances_inv_families.jsonl"
OUT_DIR = ROOT / "results/raw/t3_smoke"


def scoring_rows() -> list[dict]:
    rows = []
    for line in INST.open():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("valid") and row.get("pi_ok") == "Y":
            rows.append(row)
    if not rows:
        raise SystemExit(f"no scoring-valid rows in {INST}")
    return rows


def write_one_row(path: Path, row: dict) -> None:
    path.write_text(json.dumps(row, ensure_ascii=False) + "\n")


def run_score(verifier: str, inst: Path, out: Path, extra_env: dict[str, str]) -> None:
    env = os.environ.copy()
    env.update(extra_env)
    env["PYTHONPATH"] = str(ROOT / "src")
    env["MEDVERIF_USE_OPENROUTER"] = "1"
    cmd = [
        sys.executable,
        str(ROOT / "src/score_jsonl.py"),
        "--verifier",
        verifier,
        "--instances",
        str(inst),
        "--out",
        str(out),
        "--limit",
        "1",
    ]
    subprocess.run(cmd, env=env, check=True, cwd=str(ROOT))


def main() -> None:
    row = scoring_rows()[0]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        one = Path(tmp) / "one.jsonl"
        write_one_row(one, row)
        print(json.dumps({"smoke_instance_id": row["instance_id"]}), flush=True)

        t2_env = {
            "MEDVERIF_V1B_OPENROUTER_MODEL": os.environ.get(
                "MEDVERIF_V1B_OPENROUTER_MODEL", "openai/gpt-4o"
            ),
            "MEDVERIF_V1B_PROVIDER": os.environ.get("MEDVERIF_V1B_PROVIDER", "OpenAI"),
            "MEDVERIF_V5_OPENROUTER_MODEL": os.environ.get(
                "MEDVERIF_V5_OPENROUTER_MODEL", "anthropic/claude-sonnet-4.6"
            ),
            "MEDVERIF_V5_PROVIDER": os.environ.get("MEDVERIF_V5_PROVIDER", "Anthropic"),
            "MEDVERIF_V5_TOKENIZER_MODEL": os.environ.get(
                "MEDVERIF_V5_TOKENIZER_MODEL", "HuggingFaceH4/zephyr-7b-beta"
            ),
        }
        for v in ("v1b_medscore", "v5_ragas_nli"):
            out = OUT_DIR / f"{v}.jsonl"
            if out.is_file():
                out.unlink()
            print(json.dumps({"verifier": v, "status": "start"}), flush=True)
            run_score(v, one, out, t2_env)
            print(json.dumps({"verifier": v, "status": "ok", "out": str(out)}), flush=True)

        models = json.loads((ROOT / "notes/t6_models.json").read_text())["t6b_openrouter"]
        for m in models:
            slug = m["slug"]
            module = m["verifier_module"]
            out = OUT_DIR / f"{slug}.jsonl"
            if out.is_file():
                out.unlink()
            extra = {
                "MEDVERIF_V6_VERIFIER_SLUG": slug,
                "MEDVERIF_V6_OPENROUTER_MODEL": m["openrouter_model"],
                "MEDVERIF_V6_PROVIDER": m["provider"],
                "MEDVERIF_V1C_OPENROUTER_MODEL": m["openrouter_model"],
                "MEDVERIF_V1C_PROVIDER": m["provider"],
            }
            print(
                json.dumps(
                    {
                        "verifier": module,
                        "slug": slug,
                        "model": m["openrouter_model"],
                        "provider": m["provider"],
                        "status": "start",
                    }
                ),
                flush=True,
            )
            run_score(module, one, out, extra)
            print(json.dumps({"slug": slug, "status": "ok"}), flush=True)

    print(json.dumps({"smoke": "all_pass"}))


if __name__ == "__main__":
    main()
