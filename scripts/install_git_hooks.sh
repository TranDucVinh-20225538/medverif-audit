#!/usr/bin/env bash
# Install data-integrity hooks (also run after clone).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOKDIR="$(git -C "$ROOT" rev-parse --git-dir)/hooks"
install -m 0755 /dev/stdin "$HOOKDIR/pre-commit" <<'EOF'
#!/bin/sh
exec python3 "$(git rev-parse --show-toplevel)/scripts/check_data_linecounts.py" pre-commit
EOF
install -m 0755 /dev/stdin "$HOOKDIR/pre-push" <<'EOF'
#!/bin/sh
exec python3 "$(git rev-parse --show-toplevel)/scripts/check_data_linecounts.py" pre-push
EOF
echo "installed pre-commit and pre-push in $HOOKDIR"
