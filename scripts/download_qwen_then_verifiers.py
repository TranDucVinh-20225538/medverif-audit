"""Finish Qwen2.5-32B, then the verifier checkpoints. One file at a time."""

from __future__ import annotations

import runpy

import huggingface_hub.file_download as hf_file_download

hf_file_download.is_xet_available = lambda: False

from huggingface_hub import snapshot_download

print("START qwen", flush=True)
path = snapshot_download(
    repo_id="Qwen/Qwen2.5-32B-Instruct",
    revision="5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd",
    cache_dir="/data2/hpcshared/medverif-audit/.cache/huggingface/hub",
    max_workers=1,
)
print("DONE qwen", path, flush=True)
print("START verifiers", flush=True)
runpy.run_path("/data2/hpcshared/medverif-audit/scripts/download_verifiers.py", run_name="__main__")
