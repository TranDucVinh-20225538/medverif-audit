#!/usr/bin/env python3
"""(J3-DL) Login-node step: check Hugging Face access for the chain-3 judge models and download missing weights.

Compute nodes have no reliable Hub egress (notes/t19_llama_hf_gate.md), so this runs on the LOGIN node from
jobs/run_journal_chain3.sh before anything is submitted.  --check-only (used by --dry-run): access + size + cache
check, no download.  Gated repos (meta-llama/*, google/medgemma-4b-it) are probed with a HEAD request on config.json:
no access -> status 'skipped' with a clear reason (the judge array task then marks itself skipped and exits 0).

Writes results/journal3/models.json: slug -> {hf_id, revision (pinned commit sha), status, size_gb, cached, reason}.
The scoring jobs load exactly that revision, offline.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import shutil
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from j3_common import J3, MOCK, ROOT, log  # noqa: E402
from j3_models import JUDGES  # noqa: E402

OUT = J3 / "models.json"
PATTERNS = ["*.json", "*.safetensors", "*.model", "*.txt", "*.jinja", "tokenizer*", "*.tiktoken"]


def hub_cache() -> Path:
    """The hub cache the scoring jobs read (jr3_env.sh: HF_HOME defaults to <ROOT>/.cache/huggingface, not ~)."""
    env = os.environ.get("HUGGINGFACE_HUB_CACHE") or os.environ.get("HF_HUB_CACHE")
    if env:
        return Path(env).expanduser()
    return Path(os.environ.get("HF_HOME") or ROOT / ".cache" / "huggingface").expanduser() / "hub"


def extra_caches() -> list:
    home = Path("~/.cache/huggingface/hub").expanduser()
    return [home] if home.is_dir() and home.resolve() != hub_cache().resolve() else []


def safetensors_ok(p: Path) -> bool:
    """Header parses and the file is exactly 8 + header + tensor data bytes (catches truncated downloads)."""
    try:
        size = p.stat().st_size
        with open(p, "rb") as f:
            n = struct.unpack("<Q", f.read(8))[0]
            hdr = json.loads(f.read(n))
        end = max((v["data_offsets"][1] for k, v in hdr.items() if k != "__metadata__"), default=0)
        return size == 8 + n + end
    except Exception:  # noqa: BLE001
        return False


def snapshot_complete(s: Path) -> bool:
    if not (s / "config.json").is_file():
        return False
    idx = s / "model.safetensors.index.json"
    if idx.is_file():
        shards = set(json.loads(idx.read_text())["weight_map"].values())
    elif (s / "model.safetensors").exists():
        shards = {"model.safetensors"}
    else:
        return False
    return bool(shards) and all(safetensors_ok(s / x) for x in shards)


def cached_snapshot(hf_id: str, revision: str | None = None, cache: Path | None = None):
    """Return (revision, dir) of a complete cached snapshot (every shard present with an intact safetensors file)."""
    d = (cache or hub_cache()) / ("models--" + hf_id.replace("/", "--"))
    snaps = d / "snapshots"
    if not snaps.is_dir():
        return None, None
    cands = [snaps / revision] if revision else []
    ref = d / "refs" / "main"
    if ref.is_file():
        cands.append(snaps / ref.read_text().strip())
    cands += sorted(snaps.iterdir())
    for s in cands:
        if s.is_dir() and snapshot_complete(s):
            return s.name, s
    return None, None


def link_into_hub_cache(hf_id: str, src_snap: Path) -> Path:
    """Symlink a complete model dir from another cache into the job cache (an existing partial dir is moved aside)."""
    name = "models--" + hf_id.replace("/", "--")
    dst = hub_cache() / name
    if dst.is_symlink() or dst.exists():
        aside = dst.with_name("%s.partial-%s" % (name, time.strftime("%Y%m%d%H%M%S")))
        dst.rename(aside)
        log("J3_DL", model=hf_id, moved_aside=str(aside))
    dst.symlink_to(src_snap.parent.parent)
    return dst / "snapshots" / src_snap.name


def ensure_refs_main(hf_id: str, sha: str) -> None:
    """vLLM 0.8.x builds the multimodal processor's tokenizer without the pinned revision (tokenizer_revision is dropped),
    so offline loads of e.g. MedGemma resolve 'main' and need refs/main.  sha must be the Hub's current main."""
    ref = hub_cache() / ("models--" + hf_id.replace("/", "--")) / "refs" / "main"
    if not ref.is_file():
        ref.parent.mkdir(parents=True, exist_ok=True)
        ref.write_text(sha)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="0-6", help="array spec over j3_models.JUDGES, e.g. 0-6 or 0-7 or 0,2")
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--out", default=str(OUT), help="models.json path (override only for smoke tests)")
    args = ap.parse_args()
    out_path = Path(args.out)
    idx = set()
    for part in args.models.split(","):
        a, _, b = part.partition("-")
        idx.update(range(int(a), int(b or a) + 1))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lock_dir = hub_cache() / ".locks"  # outside results/journal3, which jr3_final.sbatch commits
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock = open(lock_dir / "j3_models_json.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit("%s is being written by another j3_download.py; wait for it to finish" % out_path)
    prev = json.loads(out_path.read_text()) if out_path.is_file() else {}
    res = dict(prev)
    free_gb = shutil.disk_usage(hub_cache() if hub_cache().exists() else Path.cwd()).free / 1e9
    need_gb = 0.0
    token = os.environ.get("HF_TOKEN") or None
    for i in sorted(idx):
        slug, hf_id, params_b, size_gb, family, gated = JUDGES[i]
        rec = {"hf_id": hf_id, "params_b": params_b, "family": family, "gated": gated, "array_index": i}
        if MOCK:
            res[slug] = dict(rec, status="ok", revision="MOCKREV", cached=True, size_gb=size_gb)
            continue
        want_rev = (prev.get(slug) or {}).get("revision")
        rev, snap = cached_snapshot(hf_id, want_rev)
        if not rev:
            for other in extra_caches():
                rev, src = cached_snapshot(hf_id, want_rev, other)
                if rev:
                    snap = src if args.check_only else link_into_hub_cache(hf_id, src)
                    log("J3_DL", model=slug, found_in=str(other), linked=not args.check_only)
                    break
        if rev:
            refs_main = (snap.parent.parent / "refs" / "main").is_file()
            res[slug] = dict(rec, status="ok", revision=rev, cached=True, size_gb=round(sum(
                f.stat().st_size for f in snap.iterdir() if f.suffix == ".safetensors") / 1e9, 2), local_path=str(snap),
                refs_main=refs_main)
            log("J3_DL", model=slug, cached=True, revision=rev)
            if not refs_main and family == "gemma3":
                log("J3_DL", model=slug, warning="refs/main missing: offline vLLM multimodal load will fail; run "
                    "snapshot_download(%r, revision='main') online if main == %s" % (hf_id, rev))
            continue
        try:
            from huggingface_hub import HfApi, get_hf_file_metadata, hf_hub_url

            info = HfApi().model_info(hf_id, files_metadata=True, token=token)
            sha = info.sha
            size = sum((s.size or 0) for s in info.siblings if s.rfilename.endswith(".safetensors")) / 1e9
            get_hf_file_metadata(hf_hub_url(hf_id, "config.json", revision=sha), token=token)  # gated -> raises
        except Exception as exc:  # noqa: BLE001
            name = type(exc).__name__
            if isinstance(exc, ImportError):
                hint = "huggingface_hub missing in this python (use MEDVERIF_PYTHON = vllm env)"
            elif "OfflineMode" in name:
                hint = "HF_HUB_OFFLINE is set in this shell; unset HF_HUB_OFFLINE TRANSFORMERS_OFFLINE and rerun"
            elif "Gated" in name or "401" in str(exc) or "403" in str(exc):
                hint = ("gated repo: accept the license on https://huggingface.co/%s with the account of HF_TOKEN "
                        "(or ~/.cache/huggingface/token), then rerun" % hf_id)
            else:
                hint = "no Hub access from this node? run on the login node"
            res[slug] = dict(rec, status="skipped", cached=False, revision=None, reason="%s: %s -- %s" % (name, str(exc)[:200], hint))
            log("J3_DL", model=slug, skipped=res[slug]["reason"])
            continue
        res[slug] = dict(rec, status="pending_download", revision=sha, cached=False, size_gb=round(size, 2))
        need_gb += size
        if args.check_only:
            log("J3_DL", model=slug, would_download_gb=round(size, 1), revision=sha)
            continue
        from huggingface_hub import snapshot_download

        free_now = shutil.disk_usage(hub_cache() if hub_cache().exists() else Path.cwd()).free / 1e9
        if free_now < size * 1.05 + 5:
            res[slug].update(status="skipped", reason="insufficient disk: %.1f GB needed, %.1f GB free in %s" % (size, free_now, hub_cache()))
            log("J3_DL", model=slug, skipped=res[slug]["reason"])
            continue
        log("J3_DL", model=slug, downloading_gb=round(size, 1), revision=sha)
        try:
            path = snapshot_download(hf_id, revision=sha, allow_patterns=PATTERNS, cache_dir=str(hub_cache()), token=token)
        except Exception as exc:  # noqa: BLE001  (network / disk); rerun resumes the partial download
            res[slug].update(status="download_failed", reason="%s: %s" % (type(exc).__name__, str(exc)[:300]))
            log("J3_DL", model=slug, download_failed=res[slug]["reason"])
            continue
        if not snapshot_complete(Path(path)):
            res[slug].update(status="download_failed", reason="snapshot incomplete/truncated after download: %s" % path)
            log("J3_DL", model=slug, download_failed=res[slug]["reason"])
            continue
        ensure_refs_main(hf_id, sha)
        res[slug].update(status="ok", cached=True, local_path=path, refs_main=True)
    out = {"_meta": {"hub_cache": str(hub_cache()), "free_gb": round(free_gb, 1), "need_gb_new": round(need_gb, 1),
                     "check_only": args.check_only}}
    out.update({k: v for k, v in res.items() if not k.startswith("_")})
    tmp = out_path.with_name(out_path.name + ".tmp")
    tmp.write_text(json.dumps(out, indent=1) + "\n")
    tmp.replace(out_path)
    print(json.dumps({"models_json": str(out_path), "free_gb": round(free_gb, 1), "need_gb_new": round(need_gb, 1),
                      "status": {k: v.get("status") for k, v in out.items() if not k.startswith("_")}}, indent=1))
    if need_gb > free_gb * 0.9:
        print("WARNING: not enough free disk for the downloads (%.1f GB needed, %.1f GB free)" % (need_gb, free_gb), file=sys.stderr)


if __name__ == "__main__":
    main()
