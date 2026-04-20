#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def safe_rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except Exception:
        return str(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio_path", required=True)
    parser.add_argument("--bundle_dir", required=True)
    parser.add_argument("--bundle_audio_path", required=True)
    parser.add_argument("--transcript_path", required=True)
    parser.add_argument("--transcription_language", default="en")
    args = parser.parse_args()

    audio_path = Path(args.audio_path).resolve()
    bundle_dir = Path(args.bundle_dir).resolve()
    bundle_audio_path = Path(args.bundle_audio_path).resolve()
    transcript_path = Path(args.transcript_path).resolve()

    bundle_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "source_type": "meeting_audio",
        "grounding_strategy": "transcript_first",
        "source_file": str(audio_path),
        "bundle_dir": str(bundle_dir),
        "audio_filename": audio_path.name,
        "transcription_language": args.transcription_language,
        "audio_output": safe_rel(bundle_audio_path, bundle_dir),
        "transcript_output": safe_rel(transcript_path, bundle_dir),
        "grounded_output": "grounded.md",
        "status": {
            "audio_prepared": bundle_audio_path.is_file(),
            "transcript_generated": transcript_path.is_file(),
            "grounded_generated": (bundle_dir / "grounded.md").is_file(),
        },
    }

    extracted_md = f"""# Meeting Audio Extraction Bundle

## Source Overview
- Source type: meeting_audio
- Grounding strategy: transcript_first
- Source file: {audio_path}
- Transcription Language: {args.transcription_language}
- Audio output: {safe_rel(bundle_audio_path, bundle_dir)}
- Transcript output: {safe_rel(transcript_path, bundle_dir)}

## Workflow Summary
This bundle treats the meeting audio as a transcript-first input.
The audio has already been prepared and transcribed.
The primary evidence for grounding is the transcript file below.

## Primary Evidence
- Transcript: `{safe_rel(transcript_path, bundle_dir)}`

## Required Downstream Step
Read `transcript/meeting_transcript.txt`, then apply the existing `meeting-grounding` skill.

Always save the meeting-level structured grounding note as `grounded.md` in this same bundle directory.

If the transcript clearly contains multiple independent topics that should be researched separately downstream, also save:
- `topic_manifest.json`
- `child_outputs/topic_xx/grounded.md`
"""

    (bundle_dir / "extracted_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (bundle_dir / "extracted.md").write_text(extracted_md, encoding="utf-8")


if __name__ == "__main__":
    main()
