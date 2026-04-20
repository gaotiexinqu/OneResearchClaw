#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: bash .cursor/skills/archive-grounding/scripts/run.sh <input_zip> <output_root>"
  exit 1
fi

INPUT_ZIP="$1"
OUTPUT_ROOT="$2"

if [[ ! -f "$INPUT_ZIP" ]]; then
  echo "[archive-grounding] ERROR: input zip not found: $INPUT_ZIP"
  exit 1
fi

mkdir -p "$OUTPUT_ROOT"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/ground_archive.py" \
  --input_zip "$INPUT_ZIP" \
  --output_root "$OUTPUT_ROOT"
