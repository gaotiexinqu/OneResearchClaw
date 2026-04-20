#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: bash .cursor/skills/table-grounding/scripts/run.sh <input_path> <output_root> [sheet_selector]" >&2
  exit 1
fi

INPUT_PATH="$1"
OUTPUT_ROOT="$2"
SHEET_SELECTOR="${3-}"

if [[ ! -f "$INPUT_PATH" ]]; then
  echo "Input file not found: $INPUT_PATH" >&2
  exit 1
fi

EXT="$(basename "$INPUT_PATH")"
EXT="${EXT##*.}"
EXT="$(echo "$EXT" | tr '[:upper:]' '[:lower:]')"

case "$EXT" in
  xlsx|csv) ;;
  *)
    echo "Unsupported table type: .$EXT (only .xlsx and .csv are supported)" >&2
    exit 1
    ;;
esac

BASE_NAME="$(basename "$INPUT_PATH")"
TABLE_ID="${BASE_NAME%.*}"
TABLE_ID="$(python - "$TABLE_ID" <<'PY'
import re, sys
name = sys.argv[1]
name = re.sub(r'\s+', '-', name.strip())
name = re.sub(r'[^A-Za-z0-9._-]', '_', name)
name = re.sub(r'_+', '_', name).strip('_-')
print(name or "table")
PY
)"

SHEET_SUFFIX=""
if [[ "$EXT" == "xlsx" && -n "${SHEET_SELECTOR}" ]]; then
  SHEET_SLUG="$(python - "$SHEET_SELECTOR" <<'PY'
import re, sys
name = sys.argv[1]
name = re.sub(r'\s+', '-', name.strip())
name = re.sub(r'[^A-Za-z0-9._-]', '_', name)
name = re.sub(r'_+', '_', name).strip('_-')
print(name or "sheet")
PY
)"
  SHEET_SUFFIX="-sheet-${SHEET_SLUG}"
fi

BUNDLE_DIR="${OUTPUT_ROOT}/${EXT}-${TABLE_ID}${SHEET_SUFFIX}"

# Generate timestamp (Beijing time)
TIMESTAMP="$(python - <<'PY'
from datetime import datetime, timezone, timedelta
tz_beijing = timezone(timedelta(hours=8))
now = datetime.now(tz_beijing)
print(now.strftime("%Y%m%d%H%M%S"))
PY
)"

# Generate GROUND_ID: ext-table_id[_sheet-selector]_timestamp
if [[ "$EXT" == "xlsx" && -n "${SHEET_SELECTOR}" ]]; then
  GROUND_ID="${EXT}-${TABLE_ID}${SHEET_SUFFIX}_${TIMESTAMP}"
else
  GROUND_ID="${EXT}-${TABLE_ID}_${TIMESTAMP}"
fi

BUNDLE_DIR="${OUTPUT_ROOT}/${GROUND_ID}"
mkdir -p "$BUNDLE_DIR"

# Write ground_id.txt for downstream stages to reuse
echo "$GROUND_ID" > "${BUNDLE_DIR}/ground_id.txt"

CMD=(python ".cursor/skills/table-grounding/scripts/ground_table.py" "$INPUT_PATH" "$BUNDLE_DIR")

if [[ "$EXT" == "xlsx" && -n "${SHEET_SELECTOR}" ]]; then
  CMD+=("--sheet" "${SHEET_SELECTOR}")
fi

"${CMD[@]}"

echo "Table-grounding bundle created at: $BUNDLE_DIR"
echo "Ground ID: $GROUND_ID"
echo "Expected next step: agent reads the bundle and writes grounded.md"
