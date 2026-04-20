#!/usr/bin/env bash
set -euo pipefail

# Install opencc if not available
if ! python -c "import opencc" 2>/dev/null; then
  echo "[INFO] Installing opencc for Traditional to Simplified Chinese conversion..."
  pip install opencc-python-reimplemented -q
fi

if [ $# -lt 2 ]; then
  echo "Usage: bash scripts/run.sh <audio_path> <output_dir> [language]"
  exit 1
fi

AUDIO_PATH="$1"
OUTPUT_DIR="$2"
LANGUAGE="${3:-en}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

MODEL_ROOT="${REPO_ROOT}/models"
ASR_MODEL_PATH="${MODEL_ROOT}/faster-whisper-large-v2"
DIARIZE_MODEL_PATH="${MODEL_ROOT}/speaker-diarization-community-1"

mkdir -p "$OUTPUT_DIR"

if [ ! -f "$AUDIO_PATH" ]; then
  echo "[ERROR] Audio file not found: $AUDIO_PATH"
  exit 1
fi

if [ ! -d "$ASR_MODEL_PATH" ]; then
  echo "[ERROR] ASR model dir not found: $ASR_MODEL_PATH"
  exit 1
fi

if [ ! -d "$DIARIZE_MODEL_PATH" ]; then
  echo "[ERROR] Diarization model dir not found: $DIARIZE_MODEL_PATH"
  exit 1
fi

AUDIO_BASENAME="$(basename "$AUDIO_PATH")"
AUDIO_STEM="${AUDIO_BASENAME%.*}"

ARGS=(
  "$AUDIO_PATH"
  --model "$ASR_MODEL_PATH"
  --output_dir "$OUTPUT_DIR"
  --output_format txt
  --language "$LANGUAGE"
  --diarize
  --diarize_model "$DIARIZE_MODEL_PATH"
  --no_align
)

if command -v nvidia-smi >/dev/null 2>&1; then
  ARGS+=(--device cuda --compute_type float16 --batch_size 8)
else
  ARGS+=(--device cpu --compute_type int8 --batch_size 2)
fi

HF_HUB_OFFLINE=1 python -m whisperx "${ARGS[@]}"

RAW_TXT="$OUTPUT_DIR/${AUDIO_STEM}.txt"
FINAL_TXT="$OUTPUT_DIR/meeting_transcript.txt"

if [ ! -f "$RAW_TXT" ]; then
  echo "[ERROR] WhisperX did not produce expected txt file: $RAW_TXT"
  exit 1
fi

mv "$RAW_TXT" "$FINAL_TXT"

# Convert Traditional Chinese to Simplified Chinese for Chinese language
if [[ "$LANGUAGE" == "zh" || "$LANGUAGE" == "zh-CN" || "$LANGUAGE" == "zh-TW" ]]; then
  python -c "
import opencc
converter = opencc.OpenCC('t2s')
with open('$FINAL_TXT', 'r', encoding='utf-8') as f:
    content = f.read()
simplified = converter.convert(content)
with open('$FINAL_TXT', 'w', encoding='utf-8') as f:
    f.write(simplified)
"
  echo "[INFO] Converted Traditional Chinese to Simplified Chinese"
fi

echo "[OK] Transcript saved to: $FINAL_TXT"