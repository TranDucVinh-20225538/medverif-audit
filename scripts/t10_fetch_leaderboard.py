#!/usr/bin/env python3
"""Fetch public HHEM / Vectara hallucination leaderboard sources (no scoring)."""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "t10"
META = ROOT / "notes" / "t10_sources.json"

HF_README = "https://huggingface.co/vectara/hallucination_evaluation_model/raw/main/README.md"
HF_LEADERBOARD = "https://huggingface.co/datasets/vectara/hallucination_leaderboard/raw/main/README.md"


def fetch(url: str) -> tuple[str, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": "medverif-audit/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        text = resp.read().decode("utf-8", errors="replace")
        commit = resp.headers.get("x-linked-version") or resp.headers.get("etag")
    return text, commit


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sources = {}
    for name, url in (("hhem_model_readme", HF_README), ("leaderboard_readme", HF_LEADERBOARD)):
        try:
            text, commit = fetch(url)
            path = OUT_DIR / f"{name}.md"
            path.write_text(text)
            sources[name] = {"url": url, "path": str(path.relative_to(ROOT)), "bytes": len(text), "commit_hint": commit}
        except Exception as exc:  # noqa: BLE001
            sources[name] = {"url": url, "error": str(exc)}

    # GitHub raw fallback for leaderboard eval script if linked in README
    lb = sources.get("leaderboard_readme", {})
    if lb.get("path"):
        text = (ROOT / lb["path"]).read_text(errors="replace")
        m = re.search(r"https://github.com/[^)\s]+", text)
        if m:
            sources["github_link_from_readme"] = m.group(0)

    META.parent.mkdir(parents=True, exist_ok=True)
    META.write_text(json.dumps(sources, indent=2) + "\n")
    print(json.dumps(sources, indent=2))


if __name__ == "__main__":
    main()
