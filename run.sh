#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONIOENCODING="utf-8"

exec python3 "${SCRIPT_DIR}/main.py" "$@"

