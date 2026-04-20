---
name: input-router
description: Use the input path to select the correct downstream grounding pipeline and continue execution until the selected grounding workflow is completed.

---

# Input Router

Use this skill as the **unified input entry layer** for the system.

This skill is a **system-level dispatcher**. It does **not** implement document parsing, transcription, table extraction, PPT grounding, archive unpacking, or meeting summarization logic by itself.

However, it does **not** stop at routing analysis.
After identifying the correct input type, it must **immediately invoke the correct downstream skill and continue the task until that downstream grounding workflow is completed**.

## What This Skill Does

This skill must:

1. inspect the input path,
2. determine the file type **strictly by extension**,
3. select the correct downstream grounding pipeline,
4. invoke the corresponding existing skill,
5. and continue until the selected downstream skill's workflow has completed.

## What This Skill Does Not Do

This skill must **not** directly implement the grounding logic that belongs to downstream skills.
It must not:

- transcribe audio by itself
- extract content from documents by itself
- parse tables by itself
- ground PPTX files by itself
- unpack archives by itself
- write `grounded.md` by bypassing the downstream skill

Those tasks belong to the selected downstream skill.

## Routing Principle

Route inputs **strictly by file extension or URL pattern**.

### URL Detection (Priority 1)

If the input is a URL instead of a local file:

| URL Pattern | Route To | Output Type |
|------------|----------|------------|
| `arxiv.org/abs/` or `arxiv.org/pdf/` | `remote-input` | `.pdf` |
| `youtube.com/watch`, `youtu.be`, `youtube.com/shorts` | `remote-input` | `.mp4`/`.mkv` |
| `bilibili.com/video`, `b23.tv` | `remote-input` | `.mp4`/`.mkv` |

**URL routing workflow:**
1. Detect URL pattern
2. Invoke `remote-input` skill to download
3. Use returned local path for downstream routing
   - If `merge_failed: true`, use `audio_path` instead of `path`
4. Continue with extension-based routing

> **Note on merge failure**: When `remote-input` returns `merge_failed: true`, the actual file for downstream routing is the audio file (`.webm` etc.), which routes to `meeting-audio-grounding` instead of `meeting-video-grounding`.

### File Extension Detection (Priority 2)

For local files, route strictly by file extension:

| Extension | Route To |
|-----------|----------|
| `.mp3`, `.wav`, `.m4a`, `.webm`, `.aac`, `.ogg` | `meeting-audio-grounding` |
| `.mp4`, `.mov`, `.mkv` | `meeting-video-grounding` |
| `.pdf`, `.docx`, `.md`, `.txt` | `document-grounding` |
| `.xlsx`, `.csv` | `table-grounding` |
| `.pptx` | `pptx-grounding` |
| `.zip` | `archive-grounding` |

Do not use filename semantics, directory names, or inferred task intent to override the extension-based mapping.

## Supported Routing Table

### URL Patterns (Remote Inputs)

| URL Pattern | Route To | Local Output |
|------------|----------|-------------|
| `arxiv.org/abs/` or `arxiv.org/pdf/` | `remote-input` | PDF in `remote/arxiv/` |
| `youtube.com/watch`, `youtu.be`, `youtube.com/shorts` | `remote-input` | Video in `remote/youtube/` |
| `bilibili.com/video`, `b23.tv` | `remote-input` | Video in `remote/bilibili/` |

### File Extensions (Local Inputs)

| Extension | Route To |
|----------|----------|
| `.mp3`, `.wav`, `.m4a`, `.webm`, `.aac`, `.ogg` | `meeting-audio-grounding` |
| `.mp4`, `.mov`, `.mkv` | `meeting-video-grounding` |
| `.pdf`, `.docx`, `.md`, `.txt` | `document-grounding` |
| `.xlsx`, `.csv` | `table-grounding` |
| `.pptx` | `pptx-grounding` |
| `.zip` | `archive-grounding` |

## Required Workflow

When using this skill, you must follow this workflow:

1. **Detect input type**:
   - If input contains URL patterns (arxiv.org, youtube.com, youtu.be, bilibili.com, b23.tv): goto URL handling
   - Otherwise: goto file handling

2. **URL handling**:
   1. Match URL pattern to `remote-input`
   2. Invoke `remote-input` skill
   3. Receive returned local file path
   4. Use the local path for downstream routing

3. **File handling**:
   1. Inspect the input path
   2. Determine the file extension
   3. Match the extension to the routing table
   4. Select the corresponding downstream skill

4. **Continue**:
   1. Immediately invoke the selected downstream skill
   2. Follow the downstream skill's own workflow strictly
   3. Do **not** stop after only reporting the routing decision

## URL Detection Patterns

### arXiv URLs
- Pattern: `https?://(?:www\.)?arxiv\.org/(abs|pdf)/`
- Examples:
  - `https://arxiv.org/abs/2301.07041`
  - `https://arxiv.org/pdf/2301.07041.pdf`
  - `http://arxiv.org/abs/2301.07041`

### YouTube URLs
- Pattern: `https?://(?:www\.)?youtube\.com/(watch|shorts)/` or `https?://youtu\.be/`
- Examples:
  - `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
  - `https://youtu.be/dQw4w9WgXcQ`
  - `https://www.youtube.com/shorts/abc123`

### Bilibili URLs
- Pattern: `https?://(?:www\.)?bilibili\.com/video/` or `https?://b23\.tv/`
- Examples:
  - `https://bilibili.com/video/BV1xx411c7JZ`
  - `https://www.bilibili.com/video/av12345678`
  - `https://b23.tv/abc123`

## Merge Failure Handling

When downloading video from URL (YouTube or Bilibili), the downloader may produce separate video and audio files instead of a merged video file (merge failure). This happens when:

- The video has separate video and audio streams that couldn't be merged
- Common pattern: `.mp4` file without audio + `.webm` audio file

### Detection and Recovery

After `remote-input` downloads video content:

1. **Check return values** for `merge_failed` field:
   - `merge_failed: false` → Use `path` as normal (video with audio)
   - `merge_failed: true` → Use `audio_path` instead of `path`

2. **Reroute based on actual file type**:
   - If `audio_path` is used → route to `meeting-audio-grounding`
   - If `path` is used → route based on extension (video → `meeting-video-grounding`)

### Routing After Merge Failure

When `merge_failed: true`, the local file is typically a pure audio file (`.webm`, `.mp3`, etc.):

| Returned File Type | Route To |
|-------------------|----------|
| `.mp3`, `.wav`, `.m4a`, `.webm`, `.aac`, `.ogg` | `meeting-audio-grounding` |
| `.mp4`, `.mov`, `.mkv` (with audio) | `meeting-video-grounding` |

### Workflow Example

```
User: https://youtube.com/watch?v=xxx
           ↓
remote-input downloads video
           ↓
Returns: {
  "path": "video.mp4",           // video without audio
  "audio_path": "audio.webm",    // separate audio file
  "merge_failed": true
}
           ↓
Since merge_failed=true, use audio_path
           ↓
audio.webm extension → .webm
           ↓
Route to: meeting-audio-grounding
```

## Completion Rule

The task is **not complete** after:

- identifying the URL pattern or extension,
- naming the downstream skill,
- or reporting the selected pipeline.

The task is complete **only after**:

- for URL inputs: `remote-input` has successfully downloaded the content
- the selected downstream skill has been invoked,
- its required workflow has been followed,
- and the expected grounding result for that input type has been produced.

## Unsupported Inputs

If the input is neither a supported URL nor a supported file extension:

- report that the input is unsupported by the current router,
- do not guess a pipeline,
- do not force the file through an unrelated skill.

## Dispatch Behavior

The router is an **entry skill**, not a stopping point.

For URL inputs:
- do **not** stop after saying `remote-input`; run it
- use the returned local path to continue routing

For audio inputs, do **not** stop after saying `meeting-audio-grounding`; run it
For video inputs, do **not** stop after saying `meeting-video-grounding`; run it
For document inputs, do **not** stop after saying `document-grounding`; run it
For table inputs, do **not** stop after saying `table-grounding`; run it
For PPT inputs, do **not** stop after saying `pptx-grounding`; run it
For ZIP inputs, do **not** stop after saying `archive-grounding`; run it

## Practical Meaning

From the user's perspective, this skill should behave like a unified input layer:

**For URL inputs:**
- the user provides a URL (arxiv paper or YouTube video),
- this skill downloads the content to `data/raw_inputs/remote/`,
- the task continues through the appropriate grounding pipeline.

**For local file inputs:**
- the user provides one input file,
- this skill selects the correct downstream grounding pipeline,
- and the task continues through that pipeline until grounding is actually completed.

The user should **not** need to manually re-enter another instruction just because the router has already identified the correct skill.