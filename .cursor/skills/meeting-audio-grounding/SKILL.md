---
name: meeting-audio-grounding
description: Convert a meeting audio file into a transcript bundle, then use meeting-grounding to produce structured meeting grounding outputs.

---

# Meeting Audio Grounding

Convert a meeting audio file into structured meeting grounding outputs by:

1. reusing the existing `audio_structuring` skill to produce `meeting_transcript.txt`
2. reusing the existing `meeting-grounding` skill to turn that transcript into meeting grounding outputs

This skill is for **meeting audio inputs** where the primary information comes from speech.
It is intentionally **transcript-first**.

## When to Use

Use this skill when:

- the input is a meeting recording or discussion audio file
- the main information is expected to come from spoken content
- you want to reuse the existing audio transcription and meeting grounding workflow

Do not use this skill when:

- the task is only to produce a transcript without meeting grounding
- the task is to write a polished final report directly from raw audio
- the input is not a meeting/discussion recording

## Input

A single meeting audio file.

Typical examples:

- `.mp3`
- `.wav`
- `.m4a`
- `.webm`
- `.aac`
- `.ogg`

All these formats are supported via WhisperX's ffmpeg backend.

Optional input:

- `transcription_language`: language code such as `en` or `zh`

## Output Bundle

For each input audio file, create one bundle directory:

```text
data/grounded_notes/<ground_id>/
```

Inside that bundle, the expected outputs are always:

```text
<bundle_dir>/
├─ extracted.md
├─ extracted_meta.json
├─ grounded.md
├─ audio/
│  └─ meeting_audio<original_ext>
└─ transcript/
   └─ meeting_transcript.txt
```

If the meeting contains multiple independent topics that should be researched separately downstream, the bundle may also contain:

```text
<bundle_dir>/
├─ topic_manifest.json
└─ child_outputs/
   ├─ topic_01/
   │  └─ grounded.md
   ├─ topic_02/
   │  └─ grounded.md
   └─ ...
```

## Important separation of responsibilities

- `scripts/run.sh` is responsible for:
  - preparing the bundle directory
  - ensuring the input audio is present under `audio/`
  - calling the existing `audio_structuring` skill
  - creating the bundle files:
    - `audio/meeting_audio<original_ext>`
    - `transcript/meeting_transcript.txt`
    - `extracted.md`
    - `extracted_meta.json`
- The **agent** is responsible for:
  - reading the transcript bundle
  - applying the existing `meeting-grounding` skill
  - always writing the meeting-level:
    - `grounded.md`
  - and, when appropriate, also writing:
    - `topic_manifest.json`
    - `child_outputs/topic_xx/grounded.md`

`grounded.md` must be a real grounding note.
It must **not** remain a placeholder scaffold.

## Required Agent Workflow

1. Run the existing `scripts/run.sh` entrypoint for this skill.
2. Confirm that the bundle exists and that these files are present:
   - `extracted.md`
   - `extracted_meta.json`
   - `audio/`
   - `transcript/meeting_transcript.txt`
3. Read `transcript/meeting_transcript.txt` as the primary grounding evidence.
4. Reuse the existing `meeting-grounding` skill on that transcript.
5. Always save the meeting-level structured note to `grounded.md` inside the same bundle directory.
6. If the transcript clearly contains multiple independent topics, also save:
   - `topic_manifest.json`
   - `child_outputs/topic_xx/grounded.md`
7. Do not stop after confirming that the transcript bundle exists.

## Output Format

The final `grounded.md` must follow the existing `meeting-grounding` schema exactly.

If topic children are created, each child grounded note must also follow the same `meeting-grounding` schema.

Do not invent a new schema here.

## Instructions

- Do **not** implement a new ASR pipeline.
- Do **not** implement a new meeting summarizer.
- Do **not** directly summarize the raw audio without first running the existing workflow.
- Reuse the existing `audio_structuring` skill for transcription.
- Reuse the existing `meeting-grounding` skill for transcript grounding.
- Treat the transcript as the primary evidence.
- Keep the workflow simple and stable.

## Failure Handling

- If the input audio file does not exist, fail clearly.
- If `meeting_transcript.txt` is not produced, fail clearly.
- Do not pretend the task succeeded if only part of the workflow completed.

## Example Invocation

`/meeting-audio-grounding`