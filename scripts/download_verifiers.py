"""Download verifier weights after Phi-4 is complete.

Verifier repos use 4 HTTP streams. Each finished file is kept only when its
size matches the Hugging Face metadata. A mismatch is deleted and fetched
again on one stream. Qwen2.5 for Stage 1–2 is not downloaded here.


Does not start a download while microsoft/phi-4 still has fewer than 6
safetensor shards or any *.incomplete blob. Writes notes/weight_integrity.json
from the Hugging Face file metadata. Does not touch data/, qc/, or SLURM jobs.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import huggingface_hub.file_download as hf_file_download

hf_file_download.is_xet_available = lambda: False

from huggingface_hub import HfApi, hf_hub_download, snapshot_download

ROOT = Path("/data2/hpcshared/medverif-audit")
CACHE = ROOT / ".cache" / "huggingface"
HUB = CACHE / "hub"
PHI = HUB / "models--microsoft--phi-4"
NOTES = ROOT / "notes" / "weight_integrity.json"
WORKERS = 4

MODELS = [
    {
        "name": "v1_medscore",
        "repo": "mistralai/Mistral-Small-24B-Instruct-2501",
        "revision": "9527884be6e5616bdd54de542f9ae13384489724",
        "allow_patterns": [
            "model-*.safetensors",
            "model.safetensors.index.json",
            "config.json",
            "generation_config.json",
            "params.json",
            "tokenizer.model",
            "tokenizer.json",
            "tokenizer_config.json",
            "special_tokens_map.json",
            "*.py",
            ".gitattributes",
            "README.md",
        ],
    },
    {
        "name": "v2a_minicheck",
        "repo": "lytang/MiniCheck-Flan-T5-Large",
        "revision": "96eafd01cee2d16cf81aaa2fb226b14f422a37b3",
    },
    {
        "name": "v2b_bespoke",
        "repo": "bespokelabs/Bespoke-MiniCheck-7B",
        "revision": "1ed7786bcda3fa1dc35f7c4ed9e3f36b785d33b8",
    },
    {
        "name": "v3_alignscore_ckpt",
        "repo": "yzha/AlignScore",
        "revision": "8509e78d25bb914939fc585c626500c9b2944249",
        "allow_patterns": ["AlignScore-large.ckpt"],
    },
    {
        "name": "v3_roberta_large",
        "repo": "FacebookAI/roberta-large",
        "revision": "722cf37b1afa9454edce342e7895e588b6ff1d59",
        "ignore_patterns": ["pytorch_model.bin"],
    },
    {
        "name": "v4_ragas_nli",
        "repo": "Qwen/Qwen3-14B",
        "revision": "40c069824f4251a91eefaf281ebe4c544efd3e18",
    },
]


def phi_ready() -> bool:
    shards = list(PHI.glob("**/model-*.safetensors"))
    incomplete = list(PHI.glob("**/*.incomplete"))
    print(f"phi shards={len(shards)} incomplete={len(incomplete)}", flush=True)
    return len(shards) >= 6 and not incomplete


def wait_for_phi() -> None:
    while not phi_ready():
        time.sleep(60)


def local_snapshot(repo: str, revision: str) -> Path | None:
    folder = HUB / ("models--" + repo.replace("/", "--"))
    snap = folder / "snapshots" / revision
    if snap.is_dir():
        return snap
    snaps = list((folder / "snapshots").glob("*")) if (folder / "snapshots").is_dir() else []
    return snaps[0] if len(snaps) == 1 else None


def check_one(api: HfApi, spec: dict) -> dict:
    info = api.model_info(spec["repo"], revision=spec["revision"], files_metadata=True)
    remote = {sib.rfilename: sib.size for sib in info.siblings}
    snap = local_snapshot(spec["repo"], spec["revision"])
    allow = set(spec.get("allow_patterns") or [])
    ignore = set(spec.get("ignore_patterns") or [])
    index_report = []
    if snap is not None:
        for index_path in snap.glob("*.safetensors.index.json"):
            payload = json.loads(index_path.read_text())
            weight_map = payload.get("weight_map") or {}
            missing = []
            size_mismatch = []
            for filename in sorted(set(weight_map.values())):
                local = snap / filename
                expected = remote.get(filename)
                if not local.is_file():
                    missing.append(filename)
                    continue
                actual = local.stat().st_size
                if expected is not None and actual != expected:
                    size_mismatch.append({"file": filename, "local": actual, "remote": expected})
            index_report.append({
                "index": index_path.name,
                "n_files": len(set(weight_map.values())),
                "missing": missing,
                "size_mismatch": size_mismatch,
            })
    files = []
    names = allow or set(remote)
    for filename, expected in sorted(remote.items()):
        if filename in ignore or (allow and filename not in allow):
            continue
        if not allow and not (
            filename.endswith(".safetensors")
            or filename.endswith(".safetensors.index.json")
            or filename.endswith(".ckpt")
            or filename.endswith(".bin")
            or filename.endswith(".json")
        ):
            continue
        local_size = None
        if snap is not None and (snap / filename).is_file():
            local_size = (snap / filename).stat().st_size
        files.append({
            "file": filename,
            "remote": expected,
            "local": local_size,
            "match": local_size is not None and (expected is None or local_size == expected),
        })
    ok = all(item["match"] for item in files) and all(not item["missing"] and not item["size_mismatch"] for item in index_report)
    if spec["name"] != "v3_alignscore_ckpt" and not index_report and any(name.endswith(".safetensors.index.json") for name in remote):
        ok = False
    return {
        "name": spec["name"],
        "repo": spec["repo"],
        "revision": info.sha,
        "requested_revision": spec["revision"],
        "snapshot": str(snap) if snap else None,
        "ok": ok,
        "indexes": index_report,
        "files_checked": files,
    }


def _bad_files(report: dict) -> list[str]:
    names = [row["file"] for row in report["files_checked"] if not row["match"]]
    for index in report["indexes"]:
        names.extend(index["missing"])
        names.extend(row["file"] for row in index["size_mismatch"])
    return sorted(set(names))


def repair(api: HfApi, spec: dict, report: dict) -> dict:
    bad = _bad_files(report)
    if not bad:
        return report
    print(f"REPAIR {spec['name']} {bad}", flush=True)
    snap = local_snapshot(spec["repo"], spec["revision"])
    for filename in bad:
        if snap is not None and (snap / filename).is_file():
            (snap / filename).unlink()
        hf_hub_download(
            repo_id=spec["repo"],
            filename=filename,
            revision=spec["revision"],
            cache_dir=str(HUB),
            force_download=True,
        )
    return check_one(api, spec)


def _bytes_ok(report: dict) -> int:
    return sum(row["remote"] or 0 for row in report["files_checked"] if row["match"] and row["remote"])


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    print("waiting for phi-4", flush=True)
    wait_for_phi()
    print(f"phi-4 complete; downloading verifiers max_workers={WORKERS}", flush=True)
    for spec in MODELS:
        print(f"START {spec['name']}", flush=True)
        started = time.perf_counter()
        if spec["name"] == "v3_alignscore_ckpt":
            hf_hub_download(
                repo_id=spec["repo"],
                filename="AlignScore-large.ckpt",
                revision=spec["revision"],
                cache_dir=str(HUB),
            )
        else:
            kwargs = {
                "repo_id": spec["repo"],
                "revision": spec["revision"],
                "cache_dir": str(HUB),
                "max_workers": WORKERS,
            }
            if spec.get("allow_patterns"):
                kwargs["allow_patterns"] = spec["allow_patterns"]
            if spec.get("ignore_patterns"):
                kwargs["ignore_patterns"] = spec["ignore_patterns"]
            snapshot_download(**kwargs)
        elapsed = time.perf_counter() - started
        print(f"DONE {spec['name']} sec={elapsed:.1f}", flush=True)
    api = HfApi()
    report = []
    for spec in MODELS:
        checked = repair(api, spec, check_one(api, spec))
        checked["max_workers"] = WORKERS
        report.append(checked)
        print(
            f"RATE {spec['name']} ok={checked['ok']} bytes={_bytes_ok(checked)}",
            flush=True,
        )
    NOTES.parent.mkdir(parents=True, exist_ok=True)
    NOTES.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({row["name"]: row["ok"] for row in report}), flush=True)


if __name__ == "__main__":
    main()
