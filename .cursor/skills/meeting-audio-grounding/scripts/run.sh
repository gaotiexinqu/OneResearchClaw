#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: bash scripts/run.sh <audio_path> <output_root> [transcription_language] [bundle_dir_override]"
  exit 1
fi

AUDIO_PATH="$1"
OUTPUT_ROOT="$2"
TRANSCRIPTION_LANGUAGE="${3:-en}"
BUNDLE_DIR_OVERRIDE="${4:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

AUDIO_STRUCTURING_RUN="${REPO_ROOT}/.cursor/skills/audio_structuring/scripts/run.sh"
PREPARE_BUNDLE_PY="${SCRIPT_DIR}/prepare_bundle.py"

if [ ! -f "$AUDIO_PATH" ]; then
  echo "[ERROR] Audio file not found: $AUDIO_PATH"
  exit 1
fi

if [ ! -f "$AUDIO_STRUCTURING_RUN" ]; then
  echo "[ERROR] audio_structuring run.sh not found: $AUDIO_STRUCTURING_RUN"
  exit 1
fi

AUDIO_BASENAME="$(basename "$AUDIO_PATH")"
AUDIO_STEM="${AUDIO_BASENAME%.*}"
AUDIO_EXT="${AUDIO_BASENAME##*.}"
SAFE_STEM="$(printf '%s' "$AUDIO_STEM" | tr ' ' '_' | tr -cd '[:alnum:]_.-')"

# Generate timestamp (Beijing time)
TIMESTAMP="$(python - <<'PY'
from datetime import datetime, timezone, timedelta
tz_beijing = timezone(timedelta(hours=8))
now = datetime.now(tz_beijing)
print(now.strftime("%Y%m%d%H%M%S"))
PY
)"

# Generate GROUND_ID: audio-safe_stem_timestamp
GROUND_ID="audio-${SAFE_STEM}_${TIMESTAMP}"

if [ -n "$BUNDLE_DIR_OVERRIDE" ]; then
  BUNDLE_DIR="$BUNDLE_DIR_OVERRIDE"
else
  BUNDLE_DIR="${OUTPUT_ROOT}/${GROUND_ID}"
fi

AUDIO_DIR="${BUNDLE_DIR}/audio"
TRANSCRIPT_DIR="${BUNDLE_DIR}/transcript"
BUNDLE_AUDIO_PATH="${AUDIO_DIR}/meeting_audio.${AUDIO_EXT}"
TRANSCRIPT_PATH="${TRANSCRIPT_DIR}/meeting_transcript.txt"

mkdir -p "$AUDIO_DIR" "$TRANSCRIPT_DIR"

# Write ground_id.txt for downstream stages to reuse
echo "$GROUND_ID" > "${BUNDLE_DIR}/ground_id.txt"

SOURCE_REAL="$(python - <<'PY' "$AUDIO_PATH"
from pathlib import Path
import sys
print(Path(sys.argv[1]).resolve())
PY
)"
TARGET_REAL="$(python - <<'PY' "$BUNDLE_AUDIO_PATH"
from pathlib import Path
import sys
print(Path(sys.argv[1]).resolve())
PY
)"

if [ "$SOURCE_REAL" != "$TARGET_REAL" ]; then
  cp "$AUDIO_PATH" "$BUNDLE_AUDIO_PATH"
fi

if [ ! -f "$BUNDLE_AUDIO_PATH" ]; then
  echo "[ERROR] Failed to place audio into bundle: $BUNDLE_AUDIO_PATH"
  exit 1
fi

echo "[INFO] Running audio_structuring on meeting audio..."
bash "$AUDIO_STRUCTURING_RUN" "$BUNDLE_AUDIO_PATH" "$TRANSCRIPT_DIR" "$TRANSCRIPTION_LANGUAGE"

if [ ! -f "$TRANSCRIPT_PATH" ]; then
  echo "[ERROR] meeting_transcript.txt not found after audio_structuring: $TRANSCRIPT_PATH"
  exit 1
fi

python "$PREPARE_BUNDLE_PY" \
  --audio_path "$AUDIO_PATH" \
  --bundle_dir "$BUNDLE_DIR" \
  --bundle_audio_path "$BUNDLE_AUDIO_PATH" \
  --transcript_path "$TRANSCRIPT_PATH" \
  --transcription_language "$TRANSCRIPTION_LANGUAGE"

if [ ! -f "${BUNDLE_DIR}/extracted.md" ]; then
  echo "[ERROR] extracted.md was not generated"
  exit 1
fi

if [ ! -f "${BUNDLE_DIR}/extracted_meta.json" ]; then
  echo "[ERROR] extracted_meta.json was not generated"
  exit 1
fi

echo "[OK] Meeting audio bundle saved to: $BUNDLE_DIR"
echo "[OK] Ground ID: $GROUND_ID"
