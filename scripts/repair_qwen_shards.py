"""Check Qwen and Phi shard sha256 values, then submit Stage 1-2.

A file is kept only when its sha256 matches the Hugging Face LFS oid.
Downloads are one file at a time. The GPU job is submitted only after every
shard matches. Verifier downloads start after that submission.
"""

from __future__ import annotations

import hashlib
import os
import struct
import subprocess
import runpy
from pathlib import Path

import huggingface_hub.file_download as hf_file_download

hf_file_download.is_xet_available = lambda: False

from huggingface_hub import HfApi, hf_hub_download

ROOT = Path("/data2/hpcshared/medverif-audit")
HUB = ROOT / ".cache" / "huggingface" / "hub"
MODELS = [
    ("Qwen/Qwen2.5-32B-Instruct", "5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd"),
    ("microsoft/phi-4", "2db69c1c3e91a05d2c64a3185acfbaf36f744e25"),
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def header_ok(path: Path) -> bool:
    with path.open("rb") as handle:
        raw = handle.read(8)
    if len(raw) != 8:
        return False
    n = struct.unpack("<Q", raw)[0]
    return 8 < n < 50_000_000 and n + 8 < path.stat().st_size


def snapshot(repo: str, revision: str) -> Path:
    return HUB / ("models--" + repo.replace("/", "--")) / "snapshots" / revision


def expected(api: HfApi) -> dict[tuple[str, str], str]:
    out = {}
    for repo, revision in MODELS:
        info = api.model_info(repo, revision=revision, files_metadata=True)
        for sib in info.siblings:
            if not sib.rfilename.endswith(".safetensors"):
                continue
            lfs = sib.lfs
            if lfs is None or not lfs.sha256:
                raise SystemExit(f"no sha256 for {repo} {sib.rfilename}")
            out[(repo, sib.rfilename)] = lfs.sha256
    return out


def unlink_file(path: Path) -> None:
    if not path.is_symlink() and not path.exists():
        return
    blob = Path(os.path.realpath(path))
    path.unlink()
    if blob.exists() and blob != path:
        blob.unlink()
    incomplete = Path(str(blob) + ".incomplete")
    if incomplete.exists():
        incomplete.unlink()


def fetch_one(repo: str, revision: str, filename: str) -> Path:
    pointer = hf_hub_download(
        repo_id=repo,
        filename=filename,
        revision=revision,
        cache_dir=str(HUB),
    )
    return Path(pointer)


def main() -> None:
    api = HfApi()
    wanted = expected(api)
    print(f"checking {len(wanted)} files", flush=True)
    pending = []
    for (repo, filename), digest in sorted(wanted.items()):
        path = snapshot(repo, revision_of(repo)) / filename
        if not path.exists() or not header_ok(path):
            print(f"MISSING {repo} {filename}", flush=True)
            if path.exists():
                unlink_file(path)
            pending.append((repo, filename, digest))
            continue
        got = sha256_file(path)
        if got != digest:
            print(f"MISMATCH {filename} local={got} remote={digest}", flush=True)
            unlink_file(path)
            pending.append((repo, filename, digest))
            continue
        print(f"OK {filename} {got}", flush=True)
    for repo, filename, digest in pending:
        revision = revision_of(repo)
        print(f"GET {filename}", flush=True)
        path = fetch_one(repo, revision, filename)
        got = sha256_file(path)
        if got != digest or not header_ok(path):
            print(f"RETRY {filename} local={got}", flush=True)
            unlink_file(snapshot(repo, revision) / filename)
            path = fetch_one(repo, revision, filename)
            got = sha256_file(path)
        if got != digest or not header_ok(path):
            print(f"FAIL {filename} local={got} remote={digest}", flush=True)
            raise SystemExit(1)
        print(f"OK {filename} {got}", flush=True)
    jid = subprocess.check_output(
        ["sbatch", "--parsable", str(ROOT / "jobs" / "stage12.sbatch")],
        text=True,
    ).strip()
    print("sbatch", jid, flush=True)
    (ROOT / "jobs" / "logs" / "s12.pending").write_text(jid + "\n")
    print("START verifiers", flush=True)
    runpy.run_path(str(ROOT / "scripts" / "download_verifiers.py"), run_name="__main__")


def revision_of(repo: str) -> str:
    for name, revision in MODELS:
        if name == repo:
            return revision
    raise KeyError(repo)


if __name__ == "__main__":
    main()
