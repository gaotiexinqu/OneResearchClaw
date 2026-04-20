#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: bash .cursor/skills/report-export/scripts/run.sh <input_report_path> <output_root> <format_or_comma_separated_formats> [output_lang]" >&2
  exit 1
fi

INPUT_REPORT_PATH="$1"
OUTPUT_ROOT="$2"
FORMATS="$3"
OUTPUT_LANG="${4:-en}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$SCRIPT_DIR/export_report.py" "$INPUT_REPORT_PATH" "$OUTPUT_ROOT" "$FORMATS" "$OUTPUT_LANG"
