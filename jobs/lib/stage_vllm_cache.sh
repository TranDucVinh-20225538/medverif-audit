# Copy a Hugging Face hub snapshot to node-local storage before vLLM load (avoid NFS mmap stalls).
# Usage: stage_hf_snapshot REPO_ID REVISION
# Sets HUGGINGFACE_HUB_CACHE (and HF_HOME) to the local tree.

stage_hf_snapshot() {
  local repo="$1"
  local rev="$2"
  local root="${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}"
  local slug="models--${repo//\//--}"
  local src="${root}/.cache/huggingface/hub/${slug}/snapshots/${rev}"
  if [[ ! -d "${src}" ]]; then
    echo "stage_hf_snapshot: missing ${src}" >&2
    return 1
  fi
  local base="${TMPDIR:-/tmp}/medverif_${SLURM_JOB_ID:-local}"
  local dest="${base}/hub/${slug}/snapshots/${rev}"
  if [[ ! -f "${dest}/config.json" ]] && [[ ! -f "${dest}/model.safetensors.index.json" ]]; then
    echo "staging ${repo}@${rev} -> ${dest} ($(date -Is))" >&2
    mkdir -p "$(dirname "${dest}")"
    rsync -a --info=stats2 "${src}/" "${dest}/"
  else
    echo "using cached local snapshot ${dest}" >&2
  fi
  export HF_HOME="${base}"
  export HUGGINGFACE_HUB_CACHE="${base}/hub"
  export MEDVERIF_HF_LOCAL="${dest}"
}
