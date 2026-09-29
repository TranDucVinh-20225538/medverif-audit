"""Lane B (cpuverif login) package pins and per-row score stamps."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_JSON = ROOT / "notes" / "lane_b_env.json"


def _pkg_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _alignscore_note() -> dict:
    src = ROOT / ".cache/src/AlignScore"
    rev = None
    if (src / ".git").is_dir():
        try:
            rev = (
                subprocess.check_output(["git", "-C", str(src), "rev-parse", "HEAD"], text=True)
                .strip()
            )
        except subprocess.CalledProcessError:
            rev = None
    return {
        "pip": _pkg_version("alignscore"),
        "git_rev": rev,
        "clone_path": str(src) if src.is_dir() else None,
    }


def _minicheck_note() -> dict:
    src = ROOT / ".cache/src/MiniCheck"
    rev = None
    if (src / ".git").is_dir():
        try:
            rev = (
                subprocess.check_output(["git", "-C", str(src), "rev-parse", "HEAD"], text=True)
                .strip()
            )
        except subprocess.CalledProcessError:
            rev = None
    return {"pip": _pkg_version("minicheck"), "git_rev": rev}


def capture_packages() -> dict:
    pkgs = {
        "transformers": _pkg_version("transformers"),
        "torch": _pkg_version("torch"),
        "summac": _pkg_version("summac"),
        "huggingface_hub": _pkg_version("huggingface-hub"),
        "pytorch_lightning": _pkg_version("pytorch-lightning"),
    }
    pkgs["minicheck"] = _minicheck_note()
    pkgs["alignscore"] = _alignscore_note()
    return pkgs


def env_fingerprint(packages: dict) -> str:
    blob = json.dumps(packages, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def load_env_doc() -> dict | None:
    if not ENV_JSON.is_file():
        return None
    try:
        return json.loads(ENV_JSON.read_text())
    except json.JSONDecodeError:
        return None


def record_lane_b_env(*, reason: str = "manual") -> dict:
    packages = capture_packages()
    doc = {
        "conda_env": os.environ.get("CONDA_DEFAULT_ENV", "cpuverif"),
        "python": sys.version.split()[0],
        "host_role": "hpc_login",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "packages": packages,
        "env_id": env_fingerprint(packages),
    }
    ENV_JSON.parent.mkdir(parents=True, exist_ok=True)
    ENV_JSON.write_text(json.dumps(doc, indent=2) + "\n")
    return doc


def stamp_score_row(row: dict) -> dict:
    doc = load_env_doc()
    if not doc:
        doc = record_lane_b_env(reason="auto_stamp")
    out = dict(row)
    out["env"] = "hpc"
    out["lane_b_env_id"] = doc["env_id"]
    out["package_versions"] = doc["packages"]
    return out


def append_stamped(path: Path, rows) -> None:
    from verifiers.io_utils import append_jsonl

    append_jsonl(path, [stamp_score_row(r) for r in rows])
