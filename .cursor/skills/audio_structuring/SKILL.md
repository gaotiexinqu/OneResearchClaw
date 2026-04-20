# Audio Structuring Skill

## Purpose
Convert a meeting audio file into a dialogue-style transcript txt file for downstream skills.

## Input
- `audio_path`: path to a single audio file
- `output_dir`: directory to save the transcript
- optional `transcription_language`: language code such as `en` or `zh`

## Output
- `meeting_transcript.txt`

## Behavior
- Reuse WhisperX as the transcription backend.
- Reuse local offline model directories instead of downloading models from Hugging Face at runtime.
- Enable diarization so the txt contains speaker labels whenever available.
- Automatically convert Traditional Chinese output to Simplified Chinese when language is set to `zh`, `zh-CN`, or `zh-TW`.
- Do not implement custom ASR, alignment, or diarization logic.
- Do not generate summary, action items, reports, or any extra files.
- This skill only produces transcript txt for downstream skills.

## Local model requirements
The repository is expected to provide these local model directories under `models/`:

- `models/faster-whisper-large-v2`
- `models/speaker-diarization-community-1`

## Run
```bash
bash scripts/run.sh <audio_path> <output_dir> [language]