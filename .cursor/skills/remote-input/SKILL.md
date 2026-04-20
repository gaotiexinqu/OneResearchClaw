---
name: remote-input
description: Download remote content (arxiv papers, YouTube videos, Bilibili videos) to local storage and route to downstream grounding pipeline. Use when user provides a URL instead of a local file path.
---

# Remote Input

Download remote content (arxiv papers, YouTube videos, Bilibili videos) to local storage and seamlessly integrate into the downstream pipeline.

## What This Skill Does

This skill acts as a **pre-processing layer** for the pipeline:

1. Detects URL type (arxiv, YouTube, or Bilibili)
2. Downloads content to `data/raw_inputs/remote/`
3. Returns the local file path
4. Triggers the next pipeline stage

## Supported URL Types

| URL Type | Download Target | Local Extension | Downstream Routing |
|----------|-----------------|-----------------|-------------------|
| `https://arxiv.org/abs/...` | PDF | `.pdf` | `document-grounding` |
| `https://arxiv.org/pdf/...` | PDF | `.pdf` | `document-grounding` |
| `https://www.youtube.com/watch?v=...` | Video | `.mp4`/`.mkv` | `meeting-video-grounding` |
| `https://youtu.be/...` | Video | `.mp4`/`.mkv` | `meeting-video-grounding` |
| `https://www.youtube.com/shorts/...` | Video | `.mp4`/`.mkv` | `meeting-video-grounding` |
| `https://bilibili.com/video/BV...` | Video | `.mp4`/`.mkv` | `meeting-video-grounding` |
| `https://www.bilibili.com/video/av...` | Video | `.mp4`/`.mkv` | `meeting-video-grounding` |
| `https://b23.tv/...` | Video | `.mp4`/`.mkv` | `meeting-video-grounding` |

> **Note on merge failure**: When video download produces separate video and audio files (merge failure), the downloader returns `merge_failed: true` with `audio_path` pointing to the audio file. The downstream routing switches to `meeting-audio-grounding` instead of `meeting-video-grounding`.

## Directory Structure

```
data/raw_inputs/remote/
├── arxiv/
│   └── <paper_id>.pdf          # e.g., 2301.07041.pdf
├── youtube/
│   └── <video_title>.mp4       # e.g., "Introduction to Transformers.mp4"
├── bilibili/
│   └── <video_title>.mp4       # e.g., "教程视频.mp4"
└── metadata/
    └── <ground_id>.json        # Download metadata
```

## Workflow

### Step 1. Parse Input URL

Detect the URL type:

```
If URL contains "arxiv.org":
    → Use arxiv downloader
    → Ground ID = arxiv paper ID (e.g., "2301.07041")

If URL contains "youtube.com" or "youtu.be":
    → Use YouTube downloader
    → Ground ID = sanitized video title or video ID

If URL contains "bilibili.com" or "b23.tv":
    → Use Bilibili downloader
    → Ground ID = BV ID (e.g., "BV1xx411c7JZ")
```

### Step 2. Download Content

#### For arXiv Papers

```bash
python .cursor/skills/remote-input/scripts/download_arxiv.py download "<url_or_id>" \
    --dir data/raw_inputs/remote/arxiv
```

Output:
```json
{
  "success": true,
  "path": "data/raw_inputs/remote/arxiv/2301.07041.pdf",
  "paper_id": "2301.07041",
  "title": "Attention Is All You Need",
  "authors": ["Ashish Vaswani", ...],
  "abstract": "The dominant sequence transduction models...",
  "size_kb": 1024
}
```

#### For YouTube Videos

```bash
python .cursor/skills/remote-input/scripts/download_video.py "<url>" \
    -o data/raw_inputs/remote/youtube \
    -q 720p
```

Output (normal - video with audio):
```json
{
  "success": true,
  "path": "data/raw_inputs/remote/youtube/Video Title.mp4",
  "title": "Video Title",
  "video_id": "dQw4w9WgXcQ",
  "source": "youtube",
  "duration": 213,
  "uploader": "Rick Astley",
  "audio_path": null,
  "merge_failed": false
}
```

Output (merge failure - separate audio file):
```json
{
  "success": true,
  "path": "data/raw_inputs/remote/youtube/Video Title.f136.mp4",
  "title": "Video Title",
  "video_id": "dQw4w9WgXcQ",
  "source": "youtube",
  "duration": 213,
  "uploader": "Rick Astley",
  "audio_path": "data/raw_inputs/remote/youtube/Video Title.f251.webm",
  "merge_failed": true
}
```

#### For Bilibili Videos

```bash
python .cursor/skills/remote-input/scripts/download_video.py "<url>" \
    -o data/raw_inputs/remote/bilibili \
    -q 720p \
    -s  # 可选：下载字幕
```

Output (normal - video with audio):
```json
{
  "success": true,
  "path": "data/raw_inputs/remote/bilibili/视频标题.mp4",
  "title": "视频标题",
  "video_id": "BV1xx411c7JZ",
  "source": "bilibili",
  "duration": 600,
  "uploader": "UP主名称",
  "audio_path": null,
  "merge_failed": false
}
```

Output (merge failure - separate audio file):
```json
{
  "success": true,
  "path": "data/raw_inputs/remote/bilibili/视频标题.f136.mp4",
  "title": "视频标题",
  "video_id": "BV1xx411c7JZ",
  "source": "bilibili",
  "duration": 600,
  "uploader": "UP主名称",
  "audio_path": "data/raw_inputs/remote/bilibili/视频标题.f251.webm",
  "merge_failed": true
}
```

> **Note**: Bilibili 视频需要登录 Cookie 才能下载高画质 (1080p+)。使用默认设置可下载 1080p 及以下画质。如需下载更高画质，请配置 `--cookies-from-browser chrome` 或提供 cookie 文件。

### Step 3. Write Metadata

Save download metadata to:
```
data/raw_inputs/remote/metadata/<ground_id>.json
```

Example:
```json
{
  "ground_id": "arxiv_2301.07041",
  "source_type": "arxiv",
  "source_url": "https://arxiv.org/abs/2301.07041",
  "downloaded_path": "data/raw_inputs/remote/arxiv/2301.07041.pdf",
  "downloaded_at": "2024-01-15T10:30:00Z",
  "metadata": {
    "title": "Attention Is All You Need",
    "authors": ["Ashish Vaswani", ...]
  }
}
```

Example (Bilibili):
```json
{
  "ground_id": "bilibili_BV1xx411c7JZ",
  "source_type": "bilibili",
  "source_url": "https://bilibili.com/video/BV1xx411c7JZ",
  "downloaded_path": "data/raw_inputs/remote/bilibili/视频标题.mp4",
  "downloaded_at": "2024-01-15T10:30:00Z",
  "metadata": {
    "title": "视频标题",
    "uploader": "UP主名称"
  }
}
```

### Step 4. Return Local Path

Return the local file path for downstream pipeline integration:
- For `one-report`: Pass the local path as `input_path`
- For `input-router`: The router will detect `.pdf` or `.mp4` extension

## Usage Examples

### Example 1: arXiv Paper

```text
Input: https://arxiv.org/abs/2301.07041

Workflow:
1. Download PDF to: data/raw_inputs/remote/arxiv/2301.07041.pdf
2. Write metadata: data/raw_inputs/remote/metadata/arxiv_2301.07041.json
3. Return: data/raw_inputs/remote/arxiv/2301.07041.pdf

Next: Pass to input-router → document-grounding → ...
```

### Example 2: YouTube Video

```text
Input: https://www.youtube.com/watch?v=dQw4w9WgXcQ

Workflow:
1. Download video to: data/raw_inputs/remote/youtube/Rick Astley - Never Gonna Give You Up.mp4
2. Write metadata: data/raw_inputs/remote/metadata/youtube_dQw4w9WgXcQ.json
3. Return: data/raw_inputs/remote/youtube/Rick Astley - Never Gonna Give You Up.mp4

Next: Pass to input-router → meeting-video-grounding → ...
```

### Example 2b: Bilibili Video

```text
Input: https://bilibili.com/video/BV1xx411c7JZ

Workflow:
1. Download video to: data/raw_inputs/remote/bilibili/视频标题.mp4
2. Write metadata: data/raw_inputs/remote/metadata/bilibili_BV1xx411c7JZ.json
3. Return: data/raw_inputs/remote/bilibili/视频标题.mp4

Next: Pass to input-router → meeting-video-grounding → ...
```

Supported Bilibili URL formats:
- `https://bilibili.com/video/BV1xx411c7JZ` (BV号)
- `https://www.bilibili.com/video/av12345678` (AV号)
- `https://b23.tv/abc123` (短链接)

### Example 3: Via one-report Skill

```text
Use the one-report skill with a remote URL:

Input:
- input_path: https://arxiv.org/abs/2301.07041
- output_formats: md,pdf

The one-report skill will:
1. Detect URL input (not local file)
2. Invoke remote-input to download
3. Continue pipeline with local file path
```

## Integration Points

### Integration with one-report

When `input_path` is a URL:
1. Detect URL pattern
2. Invoke `remote-input` skill
3. Use returned local path for downstream pipeline

### Integration with input-router

Update routing table to support URLs:

| Input | Route To |
|-------|----------|
| URL matching `arxiv.org` | `remote-input` → `document-grounding` |
| URL matching `youtube.com`, `youtu.be` | `remote-input` → `meeting-video-grounding` |
| URL matching `bilibili.com`, `b23.tv` | `remote-input` → `meeting-video-grounding` |

## Error Handling

| Error | Handling |
|-------|----------|
| Invalid URL format | Report unsupported URL pattern |
| arXiv ID not found | Report "Paper not found on arXiv" |
| YouTube video unavailable | Report "Video unavailable" |
| Bilibili video unavailable | Report "Video unavailable or requires login" |
| Download timeout | Retry once, then fail with error |
| Network error | Report network connectivity issue |

## Merge Failure Handling

When video download produces separate video and audio files (merge failure):

### Detection
The downloader uses `ffprobe` to check if the main video file contains an audio track:
- If no audio track detected → triggers merge attempt
- If merge fails → marks as `merge_failed: true`

### Auto-Recovery Flow
```
1. Download produces: video.mp4 (no audio) + audio.webm
2. Detect: video.mp4 lacks audio
3. Attempt: ffmpeg merge video.mp4 + audio.webm → video.mp4
4. If merge succeeds → use video.mp4 (merge_failed: false)
5. If merge fails → use audio.webm directly (merge_failed: true)
```

### Downstream Impact
When `merge_failed: true`, the downloader returns:
```json
{
  "success": true,
  "path": "video.mp4",
  "audio_path": "audio.webm",
  "merge_failed": true
}
```

The pipeline should:
1. Use `audio_path` for transcription instead of video
2. Skip video-only processing
3. Continue with `meeting-audio-grounding` using the audio file

### Supported Audio Formats for Transcription
WhisperX (used by `audio_structuring`) supports:
- `.mp3`, `.wav`, `.m4a`, `.aac`, `.ogg`
- `.webm` (also supported via ffmpeg backend)

The audio file at `audio_path` can be directly passed to `meeting-audio-grounding`.

## Ground ID Generation

| Source | Ground ID Format | Example |
|--------|-----------------|---------|
| arXiv | `arxiv_<paper_id>` | `arxiv_2301.07041` |
| YouTube | `youtube_<video_id>` | `youtube_dQw4w9WgXcQ` |
| Bilibili | `bilibili_<video_id>` | `bilibili_BV1xx411c7JZ` |

## Quality Settings

> **Note**: For Bilibili, default settings download up to 1080p from domestic servers. Higher quality (4K/8K) requires login cookies configuration.

### For YouTube

| Quality | Description | Use Case |
|---------|-------------|----------|
| `best` | Highest available | High quality presentations |
| `1080p` | Full HD | Standard videos |
| `720p` | HD | Balanced quality/size |
| `480p` | SD | Limited bandwidth |
| `360p` | Low | Slow connections |
| `worst` | Lowest available | Testing only |

Default quality: `720p` (recommended for most use cases)

### For Bilibili

| Quality | Description | Notes |
|---------|-------------|-------|
| Default | Up to 1080p | Works without login |
| 4K/8K | Highest available | Requires login cookies |
| Audio only | MP3 extraction | Works without login |

### Bilibili Login Configuration (Optional)

For higher quality downloads:
```bash
# Use browser cookies
--cookies-from-browser chrome

# Or provide cookie file
--cookies /path/to/cookies.txt
```

## Audio-Only Option

For YouTube videos that are primarily audio (podcasts, lectures):
```bash
python scripts/download_video.py "<url>" -a
```
Downloads audio as MP3 to the youtube directory.
