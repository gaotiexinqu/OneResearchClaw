#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: bash scripts/run.sh <input_path> <output_root>"
  exit 1
fi

INPUT_PATH="$1"
OUTPUT_ROOT="$2"

if [ ! -f "$INPUT_PATH" ]; then
  echo "[ERROR] Input file not found: $INPUT_PATH"
  exit 1
fi

EXT="${INPUT_PATH##*.}"
EXT="${EXT,,}"

SUPPORTED="pdf docx md txt"
if [[ ! " $SUPPORTED " =~ " $EXT " ]]; then
  echo "[ERROR] Unsupported file format: .$EXT"
  echo "Supported formats: $SUPPORTED"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${SKILL_DIR}/../../.." && pwd)"

# Compute DOC_ID (without timestamp)
DOC_ID="$(basename "$INPUT_PATH")"
DOC_ID="${DOC_ID%.*}"
DOC_ID="$(printf '%s' "$DOC_ID" | tr '[:space:]' '-' | sed 's/[^A-Za-z0-9._-]/_/g')"

# Generate timestamp (Beijing time)
TIMESTAMP="$(python - "$PROJECT_ROOT" <<'PY'
from datetime import datetime, timezone, timedelta
# Beijing time UTC+8
tz_beijing = timezone(timedelta(hours=8))
now = datetime.now(tz_beijing)
print(now.strftime("%Y%m%d%H%M%S"))
PY
)"

# Generate GROUND_ID: type-doc_id_timestamp
TYPE_PREFIX="$EXT"
GROUND_ID="${TYPE_PREFIX}-${DOC_ID}_${TIMESTAMP}"
BUNDLE_DIR="${OUTPUT_ROOT}/${GROUND_ID}"

mkdir -p "$BUNDLE_DIR"

# Write GROUND_ID to ground_id.txt for downstream stages to reuse
echo "$GROUND_ID" > "${BUNDLE_DIR}/ground_id.txt"

# Prefer explicitly provided path.
if [ -z "${DOCLING_ARTIFACTS_PATH:-}" ]; then
  if [ -d "${PROJECT_ROOT}/models/docling" ]; then
    export DOCLING_ARTIFACTS_PATH="${PROJECT_ROOT}/models/docling"
  elif [ -d "${PROJECT_ROOT}/models/docling-project/docling-models" ]; then
    export DOCLING_ARTIFACTS_PATH="${PROJECT_ROOT}/models/docling-project/docling-models"
  elif [ -d "/root/.cache/docling/models" ]; then
    export DOCLING_ARTIFACTS_PATH="/root/.cache/docling/models"
  fi
fi

python "${SCRIPT_DIR}/ground_document.py" "$INPUT_PATH" "$BUNDLE_DIR"

echo "[OK] Bundle written to: $BUNDLE_DIR"
echo "[OK] Ground ID: $GROUND_ID"
echo "[OK] Files:"
find "$BUNDLE_DIR" -maxdepth 3 -type f | sort
