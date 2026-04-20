---
name: meeting-video-grounding
description: Convert a meeting video into an audio-first transcript bundle, then use meeting-grounding to produce structured meeting grounding outputs.


---

# Meeting Video Grounding

Convert a meeting video into structured meeting grounding outputs by:

1. extracting audio from the video
2. reusing the existing `audio_structuring` skill to produce `meeting_transcript.txt`
3. reusing the existing `meeting-grounding` skill to turn that transcript into meeting grounding outputs

This skill is for **meeting videos** where the primary information comes from speech.
It is intentionally **audio-first**.
It does **not** attempt full visual understanding of the video.

## When to Use

Use this skill when:

- the input is a meeting video or discussion video
- the main information is expected to come from spoken content
- you want to reuse the existing audio transcription and meeting grounding workflow

Do not use this skill when:

- the task requires visual analysis of slides, demos, whiteboards, or screen content as first-class evidence
- the video has little or no speech
- the task is to write a polished final report directly from the raw video

## Input

A single meeting video file.

Typical examples:

- `.mp4`
- `.mkv`
- `.mov`
- `.webm`

Optional input:

- `transcription_language`: language code such as `en` or `zh`

## Output Bundle

For each input video, create one bundle directory:

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
│  └─ meeting_audio.wav
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
  - extracting audio from the input video
  - calling the existing `audio_structuring` skill
  - creating the bundle files:
    - `audio/meeting_audio.wav`
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
   - `audio/meeting_audio.wav`
   - `transcript/meeting_transcript.txt`
3. Read `transcript/meeting_transcript.txt` as the primary grounding evidence.
4. Reuse the existing `meeting-grounding` skill on that transcript.
5. Always save the meeting-level structured note to `grounded.md` inside the same bundle directory.
6. If the transcript clearly contains multiple independent topics, also save:
   - `topic_manifest.json`
   - `child_outputs/topic_xx/grounded.md`
7. Do not stop after confirming that the transcript bundle exists.

## Important scope rule

This skill currently treats meeting videos as **audio-first inputs**.

That means:

- the extracted transcript is the primary evidence for grounding
- absence of visual analysis is not, by itself, a failure
- do not invent slide content, visual details, or screen evidence that were not captured in the transcript

## Output Format

The final `grounded.md` must follow the existing `meeting-grounding` schema exactly.

If topic children are created, each child grounded note must also follow the same `meeting-grounding` schema.

Do not invent a new schema here.

## Instructions

- Do **not** implement a new ASR pipeline.
- Do **not** implement a new meeting summarizer.
- Do **not** directly summarize the raw video without first running the existing workflow.
- Reuse the existing `audio_structuring` skill for transcription.
- Reuse the existing `meeting-grounding` skill for transcript grounding.
- Treat the transcript as the primary evidence.
- Keep the workflow simple and stable.

## Failure Handling

- If the input video file does not exist, fail clearly.
- If the video has no audio stream, fail clearly.
- If audio extraction fails, fail clearly.
- If `meeting_transcript.txt` is not produced, fail clearly.
- Do not pretend the task succeeded if only part of the workflow completed.

## Example Invocation

`/meeting-video-grounding`