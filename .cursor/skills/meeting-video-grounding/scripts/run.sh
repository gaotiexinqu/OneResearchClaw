#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: bash scripts/run.sh <video_path> <output_root> [transcription_language]"
  exit 1
fi

VIDEO_PATH="$1"
OUTPUT_ROOT="$2"
TRANSCRIPTION_LANGUAGE="${3:-en}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

AUDIO_STRUCTURING_RUN="${REPO_ROOT}/.cursor/skills/audio_structuring/scripts/run.sh"
PREPARE_BUNDLE_PY="${SCRIPT_DIR}/prepare_bundle.py"

if [ ! -f "$VIDEO_PATH" ]; then
  echo "[ERROR] Video file not found: $VIDEO_PATH"
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "[ERROR] ffmpeg not found in PATH"
  exit 1
fi

if ! command -v ffprobe >/dev/null 2>&1; then
  echo "[ERROR] ffprobe not found in PATH"
  exit 1
fi

if [ ! -f "$AUDIO_STRUCTURING_RUN" ]; then
  echo "[ERROR] audio_structuring run.sh not found: $AUDIO_STRUCTURING_RUN"
  exit 1
fi

VIDEO_BASENAME="$(basename "$VIDEO_PATH")"
VIDEO_STEM="${VIDEO_BASENAME%.*}"
SAFE_STEM="$(printf '%s' "$VIDEO_STEM" | tr ' ' '_' | tr -cd '[:alnum:]_.-')"

# Generate timestamp (Beijing time)
TIMESTAMP="$(python - <<'PY'
from datetime import datetime, timezone, timedelta
tz_beijing = timezone(timedelta(hours=8))
now = datetime.now(tz_beijing)
print(now.strftime("%Y%m%d%H%M%S"))
PY
)"

# Generate GROUND_ID: video-safe_stem_timestamp
GROUND_ID="video-${SAFE_STEM}_${TIMESTAMP}"
BUNDLE_DIR="${OUTPUT_ROOT}/${GROUND_ID}"
AUDIO_DIR="${BUNDLE_DIR}/audio"
TRANSCRIPT_DIR="${BUNDLE_DIR}/transcript"
EXTRACTED_AUDIO="${AUDIO_DIR}/meeting_audio.wav"
TRANSCRIPT_PATH="${TRANSCRIPT_DIR}/meeting_transcript.txt"

mkdir -p "$AUDIO_DIR" "$TRANSCRIPT_DIR"

# Write ground_id.txt for downstream stages to reuse
echo "$GROUND_ID" > "${BUNDLE_DIR}/ground_id.txt"

HAS_AUDIO="$(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$VIDEO_PATH" | head -n 1 || true)"
if [ -z "$HAS_AUDIO" ]; then
  echo "[ERROR] No audio stream detected in input video: $VIDEO_PATH"
  exit 1
fi

echo "[INFO] Extracting audio from video..."
ffmpeg -y -i "$VIDEO_PATH" -map 0:a:0 -vn -acodec pcm_s16le -ar 16000 -ac 1 "$EXTRACTED_AUDIO" >/dev/null 2>&1

if [ ! -f "$EXTRACTED_AUDIO" ]; then
  echo "[ERROR] Failed to extract audio: $EXTRACTED_AUDIO"
  exit 1
fi

echo "[INFO] Running audio_structuring on extracted audio..."
bash "$AUDIO_STRUCTURING_RUN" "$EXTRACTED_AUDIO" "$TRANSCRIPT_DIR" "$TRANSCRIPTION_LANGUAGE"

if [ ! -f "$TRANSCRIPT_PATH" ]; then
  echo "[ERROR] meeting_transcript.txt not found after audio_structuring: $TRANSCRIPT_PATH"
  exit 1
fi

python "$PREPARE_BUNDLE_PY" \
  --video_path "$VIDEO_PATH" \
  --bundle_dir "$BUNDLE_DIR" \
  --audio_path "$EXTRACTED_AUDIO" \
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

echo "[OK] Meeting video bundle saved to: $BUNDLE_DIR"
echo "[OK] Ground ID: $GROUND_ID"
