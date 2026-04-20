#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path


def ffprobe_json(path: str) -> dict:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration,size,bit_rate",
        "-show_streams",
        "-of",
        "json",
        path,
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return json.loads(result.stdout)
    except Exception:
        return {}


def safe_rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except Exception:
        return str(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video_path", required=True)
    parser.add_argument("--bundle_dir", required=True)
    parser.add_argument("--audio_path", required=True)
    parser.add_argument("--transcript_path", required=True)
    parser.add_argument("--transcription_language", default="en")
    args = parser.parse_args()

    video_path = Path(args.video_path).resolve()
    bundle_dir = Path(args.bundle_dir).resolve()
    audio_path = Path(args.audio_path).resolve()
    transcript_path = Path(args.transcript_path).resolve()

    bundle_dir.mkdir(parents=True, exist_ok=True)

    probe = ffprobe_json(str(video_path))
    fmt = probe.get("format", {}) if isinstance(probe, dict) else {}
    streams = probe.get("streams", []) if isinstance(probe, dict) else []
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    video_streams = [s for s in streams if s.get("codec_type") == "video"]

    meta = {
        "source_type": "meeting_video",
        "grounding_strategy": "audio_first",
        "source_file": str(video_path),
        "bundle_dir": str(bundle_dir),
        "video_filename": video_path.name,
        "transcription_language": args.transcription_language,
        "video_duration_sec": fmt.get("duration"),
        "video_size_bytes": fmt.get("size"),
        "video_bit_rate": fmt.get("bit_rate"),
        "video_stream_count": len(video_streams),
        "audio_stream_count": len(audio_streams),
        "audio_output": safe_rel(audio_path, bundle_dir),
        "transcript_output": safe_rel(transcript_path, bundle_dir),
        "grounded_output": "grounded.md",
        "status": {
            "audio_extracted": audio_path.is_file(),
            "transcript_generated": transcript_path.is_file(),
            "grounded_generated": (bundle_dir / "grounded.md").is_file(),
        },
    }

    extracted_md = f"""# Meeting Video Extraction Bundle

## Source Overview
- Source type: meeting_video
- Grounding strategy: audio_first
- Source file: {video_path}
- Transcription Language: {args.transcription_language}
- Audio output: {safe_rel(audio_path, bundle_dir)}
- Transcript output: {safe_rel(transcript_path, bundle_dir)}

## Workflow Summary
This bundle treats the meeting video as an audio-first input.
The audio track has already been extracted and transcribed.
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
