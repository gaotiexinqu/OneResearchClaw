#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: bash .cursor/skills/pptx-grounding/scripts/run.sh <input_pptx> <output_root>"
  exit 1
fi

INPUT_PPTX="$1"
OUTPUT_ROOT="$2"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="$SCRIPT_DIR/ground_pptx.py"

python3 "$PY_SCRIPT" \
  --input "$INPUT_PPTX" \
  --output-root "$OUTPUT_ROOT"
