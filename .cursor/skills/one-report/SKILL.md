---
name: one-report
description: Run the full One-Report pipeline from one input file through grounding, research, evidence-rich report drafting, final review quality-gating, and export, while reusing existing skills, preserving current contracts, and enforcing strict downstream skill fidelity for every grounded unit.
---

# One-Report

Use this skill as the **single top-level entry skill** for the full One-Report pipeline.

This skill is a **thin orchestration layer**.
It does **not** replace existing input, grounding, research, summary, review, or export skills.
It must **reuse** them.

The purpose of this skill is to let a user provide:

- one input file path
- a small set of research requirements
- requested export format(s)

and then complete the full pipeline:

input
-> grounding
-> research
-> report drafting
-> review quality gate
-> output export

without requiring the user to manually run each stage.

---

## What This Skill Does

This skill must:

1. read the user-provided pipeline inputs
2. route the input into the correct existing grounding workflow
3. continue until grounding is actually completed
4. identify the grounded unit(s) that should continue downstream
5. **for multi-topic grounding: use `Task` tool to create independent subagent branches for each topic child (see Subagent Rule below)**
6. run research for each grounded unit
7. run the main report-drafting stage for each grounded unit
8. run the final review/refinement stage for each grounded unit
9. run output export for each final reviewed report
10. enforce strict downstream skill fidelity for every grounded unit, whether single-topic or multi-topic
11. report the final output paths clearly

---

## What This Skill Does Not Do

This skill must **not**:

- implement its own grounding logic
- implement its own literature search logic
- implement its own report-writing logic
- implement its own review logic
- implement its own export logic
- rewrite existing lower-level skill contracts
- skip `grounded-review` and treat the draft report as the final deliverable
- ask downstream stages to compress rich literature analysis into a shallow memo
- satisfy a downstream stage with a visibly abbreviated or weakened version of that stage's own skill contract
- let single-topic execution become lax just because no fan-out occurred
- **attempt downstream work in the parent context when multi-topic grounding exists** (must use subagent branches)

This skill is an **orchestrator**, not a replacement for the lower-level skills.

---

## 🚨 PARENT AGENT SUBAGENT ISOLATION RULES

**This section is MANDATORY. Violations will break the pipeline.**

### The Core Problem

When subagents are launched, the parent agent may be tempted to:
- Generate the same files ("lit.md", "summary.md") directly to "ensure completion"
- Override or overwrite subagent outputs
- Skip waiting and generate files prematurely

**This is forbidden and breaks the pipeline.**

### Absolute Prohibitions

During subagent execution, the parent agent must **NOT**:

| Forbidden Action | Why It Breaks Things |
|----------------|---------------------|
| Generate `lit.md` directly | Overwrites/wastes subagent's research work |
| Generate `summary.md` directly | Overwrites/wastes subagent's summary work |
| Override subagent output files | Destroys evidence of subagent completion |
| "Help by generating" while subagent runs | Creates duplicate work, confuses pipeline state |
| Skip waiting to move to next stage | Violates artifact-based completion rule |
| Use transcript line count as progress metric | Misleading — subagent may write files without updating transcript |

### Subagent Completion Signal Protocol

Every subagent that produces a pipeline artifact must end its final response with a structured **completion signal block**. This signal is the authoritative declaration of whether the subagent believes its work is done.

**Required format — subagent must include at the end of its final response:**

```json
{
  "subagent_claims_complete": true,
  "artifact_written": "<canonical path>",
  "lines_written": <number>,
  "round": <N>,
  "completion_verified_by_subagent": true
}
```

If `subagent_claims_complete` is `false`, the subagent is still working or has encountered a problem. The parent must not act as if the stage is complete.

**Subagent prompt instruction**: Every subagent prompt launched via `Task` tool must end with:

```
After completing your work and writing the output file, your final response MUST end with this block:

{
  "subagent_claims_complete": true,
  "artifact_written": "<canonical output path>",
  "lines_written": <actual line count>,
  "round": <N or 0>,
  "completion_verified_by_subagent": true
}

Do NOT end your response without this block. The parent agent will not act on your work without it.
```

**Parent agent rule**: The parent agent must wait for this signal before treating a subagent as complete. The presence of this signal in the subagent's response is necessary (but not sufficient) for the parent to mark the task as complete.

### The Only Permitted Actions During Subagent Execution

The parent agent may only:

1. **Monitor** - Check if expected output files exist (using Glob/Read tools)
2. **Resume** - Use `Task` tool with `resume` parameter to prompt stuck subagents
3. **Report** - Log progress without generating pipeline artifacts
4. **Retry** - If subagent definitively fails, launch a replacement subagent

### Todo Structure as Enforcement

When launching subagents, immediately create this todo structure:

```
todo_write with:
[
  {"id": "research_<topic_id>", "status": "in_progress:awaiting_file", "expected_file": "data/lit_results/<ground_id>/lit.md"},
  {"id": "summary_<topic_id>", "status": "blocked", "depends_on": ["research_<topic_id>"]},
  {"id": "review_<topic_id>", "status": "blocked", "depends_on": ["summary_<topic_id>"]}
]
```

**Rule**: `blocked` todos must never be processed by the parent agent directly.

### Completion Gate: File Existence Only

A subagent task is complete **ONLY** when its expected file exists at the canonical path:

| Subagent Type | Expected File | Minimum Size |
|--------------|---------------|--------------|
| Research | `data/lit_results/<ground_id>/lit.md` | ~200 lines |
| Summary | `data/report_inputs/<ground_id>/summary.md` | ~300 lines |

**Parent agent must verify file existence before marking todo as `completed`.**

### Artifact-Based Polling Strategy (Replace Transcript-Line-Count Polling)

The parent agent must NOT use transcript line count as a progress or completion metric. Subagents may write files without updating their transcript, especially when:
- The subagent writes a large output file (lit.md, summary.md) that takes many tool calls
- The subagent runs a blocking script (e.g., `download_opened_literature.py --wait`)
- The subagent completes work in a single large Write tool call that doesn't surface intermediate progress

**Correct polling protocol:**

```
1. Launch subagent with run_in_background=true
2. Set todo status to "in_progress:awaiting_file"
3. Poll using Glob — check if the canonical output file exists AND has non-trivial size:
   - Research: data/lit_results/<ground_id>/lit.md (min ~200 lines)
   - Summary: data/report_inputs/<ground_id>/summary.md (min ~300 lines)
   - Review round: data/review_outputs/<ground_id>/round_<N>/review_state.json
   - Research report: data/reports/<ground_id>/research_report.md (min ~150 lines)
4. If file exists with valid size:
   - Check transcript for the subagent's completion signal block
   - If signal present: mark todo completed, proceed
   - If signal absent: wait one more poll cycle (60s), then check again
5. If file does NOT exist after 2+ consecutive polls (60s each) AND transcript shows no new messages:
   - Consider the subagent stalled
   - Resume via Task tool resume parameter with explicit continuation instructions
   - Do NOT generate the file yourself
6. If file does NOT exist after resume + 2 more poll cycles: treat as definitive failure, launch replacement subagent
```

**Critical**: A subagent transcript that stops growing does NOT mean the subagent has stopped working. It means the transcript has stopped updating. Always verify artifact existence before drawing any conclusions about subagent state.

**What to check instead of transcript lines:**

| Instead of this | Check this |
|---|---|
| Transcript line count | `Glob` for canonical output file existence |
| "Subagent seems quiet" | `ls` to verify file size > minimum threshold |
| "No new transcript messages" | `wc -l` on the output file to confirm content |
| Subagent declared "I'm writing..." | Actual file on disk at canonical path |

### If a Subagent Seems Stuck

Before acting:

1. **Read the subagent transcript** - Check `agent-transcripts/<uuid>/subagents/<subagent_id>.jsonl` for the completion signal block
2. **Check artifact state** - Use Glob/Read to see if the canonical output file exists and has content
3. **If the artifact exists with valid content but subagent transcript stopped**: The subagent is likely complete — mark done, do NOT regenerate the file
4. **If the artifact exists but is empty or too small**: The subagent may have crashed mid-write — resume with explicit continuation
5. **If the artifact does NOT exist and subagent has not declared completion**: Resume via `Task` tool with `resume` parameter
6. **If subagent definitively fails** (error state, no progress after resume): Launch a replacement subagent
7. **Do NOT**: generate the file yourself, overwrite subagent output, or proceed without the artifact

### Correct Workflow Pattern

```text
1. Launch subagent with run_in_background=true
2. Set todo status to "in_progress:awaiting_file"
3. Poll using Glob for canonical output file existence:
   - Research: data/lit_results/<ground_id>/lit.md
   - Summary: data/report_inputs/<ground_id>/summary.md
   - Research report: data/reports/<ground_id>/research_report.md
4. Check wc -l on output file — verify size > minimum threshold
5. When canonical file exists with valid size AND subagent transcript shows completion signal:
   - Mark todo as "completed"
   - Mark dependent todo as "in_progress"
6. If file exists but completion signal absent: wait one more 60s poll before marking done
7. If file absent: wait for resume signal, do not generate the file yourself
8. Never: generate the file yourself while subagent runs, or treat a silent transcript as failure
```

### Violation = Pipeline Failure

If the parent agent generates a file that a subagent was supposed to produce:
- That stage is marked as **failed** (not completed by subagent)
- The generated file must be deleted
- A new subagent must be launched to redo the work

---

## Required User Inputs

The user should provide the following information at the beginning.

### Required

- `input_path`
- `output_formats`
- `research_mode`

### Optional

- `research_requirements`
- `search_backend`
- `external_api_key`
- `require_open_link`
- `download_opened_literature`
- `transcription_language`
- `output_lang`

### Meaning of the inputs

#### `input_path`

Path to exactly one supported input file.

#### `output_formats`

One format or comma-separated formats supported by `report-export`, for example:

- `md`
- `md,pdf`
- `md,docx,pdf,pptx`

#### `research_mode`

Controls how many literature items the research stage will search for and open. This is the **primary token-cost lever** for the pipeline.

Expected values:

- `simple` — few papers. For focused, well-scoped topics where a small number of highly relevant papers are sufficient.
- `medium` — moderate papers. For topics that require broader coverage or moderate exploration. This is the default.
- `complex` — many papers. For topics that span multiple sub-areas, involve cross-domain context, or require comprehensive literature mapping.

> The exact paper count range for each mode is defined in `config/research_pipeline.env` as the `RESEARCH_MODE_*_MIN_OPENED` / `RESEARCH_MODE_*_MAX_OPENED` variables. Edit those variables to customize the default ranges.

**This is a required parameter.** The pipeline will not proceed without it.

The mode is translated into runtime config values (`MIN_OPENED_PAPERS`, `OPEN_TOP_K`, `MIN_RECENT_PAPERS`) and written to `config/research_pipeline.env` before the research stage begins.

#### `research_requirements`

Optional extra research instructions that should shape the downstream research stage.
Examples:

- focus on technical contribution and limitations
- emphasize engineering deployment concerns
- keep uncertainty explicit
- prioritize benchmark and evaluation evidence
- preserve literature depth in the final report body

#### `search_backend`

Optional override for the research backend.
Expected values:

- `auto`
- `external`
- `cursor`

If omitted, downstream research should use its normal default behavior.

#### `external_api_key`

Optional external search API key, only relevant when an external backend is requested or available.

#### `require_open_link`

Optional boolean-like setting for the research stage.
Expected values:

- `true`
- `false`

#### `download_opened_literature`

Optional boolean-like setting for the research stage.
Expected values:

- `true`
- `false`

#### `transcription_language`

The language of the audio/video source content, used to guide Whisper transcription.

This parameter is only relevant when the input is an audio or video file. It tells the speech recognition system what language to expect, which directly affects transcription accuracy.

Expected values:
- `en` — English
- `zh` — Chinese (Simplified)
- `zh-TW` — Chinese (Traditional)
- `ja` — Japanese
- `ko` — Korean
- etc. (any language code supported by Whisper)

If omitted, the downstream audio/video grounding skill defaults to `en`.

#### `output_lang`

The language for the **final export products** (PDF, DOCX, PPTX, etc.).

This parameter controls the language of the exported report only. It has **no effect** on intermediate pipeline artifacts (`grounded.md`, `lit.md`, `summary.md`, `research_report.md`, `review_report.md`), which are always written in English.

Expected values:
- `en` — English (default)
- `zh` — Chinese (Simplified)

If omitted, defaults to `en`.

---

## Input Routing Rule

### URL Detection (NEW)

If the user provides a **URL** instead of a local file path:

1. **Invoke `remote-input` skill first** to download the remote content
2. Use the returned local path as `input_path` for the rest of the pipeline
3. **Check for merge failure**: If the download returns `merge_failed: true`, use `audio_path` instead of `path`
4. Continue with routing based on the actual file type (audio file → `meeting-audio-grounding`, video file → `meeting-video-grounding`)

#### Supported URL Patterns

| URL Type | Download Target | Local Extension |
|----------|-----------------|-----------------|
| `https://arxiv.org/abs/...` | PDF | `.pdf` |
| `https://arxiv.org/pdf/...` | PDF | `.pdf` |
| `https://www.youtube.com/watch?v=...` | Video | `.mp4`/`.mkv` |
| `https://youtu.be/...` | Video | `.mp4`/`.mkv` |

#### Workflow for URL Input

```
User provides: https://arxiv.org/abs/2301.07041
                        ↓
            ┌───────────────────────┐
            │   remote-input skill   │
            │   (downloads PDF to    │
            │   data/raw_inputs/     │
            │   remote/arxiv/)      │
            └───────────────────────┘
                        ↓
Returns: data/raw_inputs/remote/arxiv/2301.07041.pdf
                        ↓
         Continue with normal pipeline
         (input-router → document-grounding → ...)
```

#### Workflow for Video URL with Merge Failure

```
User provides: https://youtube.com/watch?v=xxx
                        ↓
            ┌───────────────────────┐
            │   remote-input skill   │
            │   (downloads video,    │
            │   merge may fail)      │
            └───────────────────────┘
                        ↓
Returns: {
  "path": "video.mp4",           // video without audio
  "audio_path": "audio.webm",    // separate audio file
  "merge_failed": true
}
                        ↓
Since merge_failed=true, use audio_path
                        ↓
         Route to meeting-audio-grounding
         (not meeting-video-grounding)
```

### Default rule

By default, this skill must reuse the existing `input-router` skill and therefore follow the current extension-based routing behavior.

That means the input should normally be routed strictly by extension through:

- `input-router`

which will dispatch to the correct existing grounding skill.

### Special exception for transcript-like `.txt`

There is only one allowed exception.

If the user explicitly states that a `.txt` file is an **already-transcribed meeting transcript**, then this skill may bypass the normal `.txt -> document-grounding` route and instead apply:

- `meeting-grounding`

This exception should be used **only when the user explicitly says so**.

Do **not** infer meeting-transcript status from filename patterns or directory names alone.

### Language Parameter Routing

When the input is an audio or video file, the `transcription_language` parameter must be passed to the downstream audio/video grounding skill to guide Whisper transcription.

The `transcription_language` parameter is **only relevant for audio/video inputs**. It has **no effect** on document, PPTX, or table inputs.

---

## 🚨 CRITICAL DECISION POINT

**Immediately after grounding completes**, check for multi-topic structure before ANY downstream work:

### Single Topic?
→ Continue downstream execution in the current context.

### Multi-Topic?
→ **STOP. You MUST use the `Task` tool NOW to create independent subagent branches for each topic child.**

Do **not** attempt to run research or downstream stages in the parent/main context when multi-topic structure exists.
See the **Subagent Rule for Multi-Topic Meetings** section below for the required `Task` tool invocation pattern.

---

## Required Top-Level Workflow

This skill must follow this workflow.

### Step 1. Read user inputs

Collect:

- `input_path`
- `output_formats`
- `research_mode` (required; one of `simple` / `medium` / `complex`)
- `transcription_language` (if provided by user; defaults to `en`)
- `output_lang` (if provided by user; defaults to `en`)
- any other optional settings provided by the user

### Step 2. Run the correct grounding entry workflow

Normally:

- invoke `input-router`
- continue until the selected downstream grounding workflow is completed

Special case:

- if the user explicitly says the `.txt` file is an already-transcribed meeting transcript, directly apply `meeting-grounding`

The task is **not complete** after naming the selected skill.
Grounding must actually finish.
Do not stop after planning the pipeline, identifying the correct skills, or describing what should be done next.

When invoking `input-router` for audio or video input, always pass `transcription_language` (from user settings, default `en`) so that the downstream audio/video grounding skill can guide Whisper transcription accurately.

### Step 3. Identify downstream grounded unit(s)

After grounding is complete, determine what should continue into research.

### Step 3A. Enforce canonical grounded-output paths and ground_id acquisition

#### Ground ID Acquisition

Every downstream stage in the pipeline must reuse the **same `ground_id`** that was generated at the grounding stage. This ensures all artifacts for the same input belong to the same pipeline run.

**How to get the ground_id:**

Read `ground_id.txt` from the grounding bundle:

```
data/grounded_notes/<ground_id>/ground_id.txt
```

The file contains exactly one line: the `ground_id` string (e.g. `pdf-paper_name_20260410153022`).

**Do NOT generate a new ground_id in downstream stages.** All downstream directories reuse the same `ground_id`:

```
data/lit_inputs/<ground_id>/
data/lit_downloads/<ground_id>/
data/lit_results/<ground_id>/
data/report_inputs/<ground_id>/
data/review_outputs/<ground_id>/
data/reports/<ground_id>/
data/final_outputs/<ground_id>/
```

#### Single-grounded-unit canonical path

For a standard single-unit grounding result, grounding counts as complete only if the grounded note exists at:

- `data/grounded_notes/<ground_id>/grounded.md`

Do **not** treat an alternative temporary path, scratch path, or non-canonical location as sufficient completion if the canonical grounded note has not been written.

#### Multi-topic meeting canonical paths

For a multi-topic meeting grounding result, grounding counts as complete only if all of the following canonical artifacts exist under the same parent grounded unit root:

- `data/grounded_notes/<ground_id>/grounded.md`
- `data/grounded_notes/<ground_id>/topic_manifest.json`
- `data/grounded_notes/<ground_id>/child_outputs/topic_xx/grounded.md` for each topic child that is expected to continue downstream

Do **not** treat the meeting as properly grounded if only non-canonical child files exist somewhere else.

#### General fan-out canonical-path rule

If grounding produces multiple child grounded items for separate downstream work, each child grounded note must also exist at its canonical downstream path under the parent grounded root before downstream research begins.

Grounding is not complete merely because a grounding skill was invoked or because some grounded-like file exists somewhere on disk. The canonical downstream grounded artifacts must actually be written.

#### Standard case

If the grounding output corresponds to one grounded unit, continue with that single grounded unit.

#### Multi-topic meeting case

If the meeting grounding output includes:

- `topic_manifest.json`
- `child_outputs/topic_xx/grounded.md`

then treat each child topic grounded note as an independent downstream grounded unit.

In this case, do **not** collapse the meeting back into one mixed downstream report.

#### General fan-out rule

If grounding clearly produces multiple child grounded items that are intended for separate downstream work, then continue downstream **per child grounded unit**, not only at the parent level.

### Step 3B. Research Query Keyword Confirmation

> ⚠️ **This is a human-in-the-loop checkpoint. It must be executed before any research begins.**

After all grounded unit(s) are identified, and before launching any research subagent (multi-topic) or running research directly (single-topic), you must:

#### Step 3B.1 — Extract query candidates for all grounded units

For **each grounded unit** (single or multi-topic), read its `grounded.md` and extract:

- the main topic / purpose
- `Search Keywords` if present
- open questions / unresolved issues
- suggested next steps

Then generate **three query groups** per grounded unit:

- **problem_queries**: background, domain context, benchmark, problem framing
- **method_queries**: methods, baselines, solution directions
- **constraint_queries**: risks, constraints, ambiguities, failure modes

#### Step 3B.2 — Present all queries to the user at once

Display the query candidates in a structured, readable format. Group by grounded unit (especially for multi-topic). Explain what each query group is for.

**Example single-topic display:**

```
Based on your input, I have generated the following search keywords for literature research:

【Problem / Background Direction (problem_queries)】
  1. "xxx"
  2. "yyy"

【Method / Solution Direction (method_queries)】
  1. "zzz"
  2. "www"

【Constraint / Risk Direction (constraint_queries)】
  1. "vvv"

Please confirm:
- Press Enter to continue with the above keywords
- Or tell me what you want to add, remove, or adjust
```

**Example multi-topic display:**

```
The following topics were found. Preparing for literature research:

[Topic 1: xxx]
  problem_queries: ["aaa", "bbb"]
  method_queries: ["ccc"]
  constraint_queries: ["ddd"]

[Topic 2: yyy]
  problem_queries: ["eee", "fff"]
  method_queries: ["ggg"]
  constraint_queries: ["hhh"]

Please confirm each topic, or tell me in one message which topic(s) you want to modify and what changes you would like.
```

#### Step 3B.3 — Wait for user input

Stop execution and wait for the user's response.

Interpret the user's response as follows:

| User response | Action |
|---|---|
| "continue" / "ok" / "looks good" | Use all query groups as-is |
| Specific additions | Append the new queries to the indicated group(s) |
| Specific deletions | Remove the indicated queries |
| Specific replacements | Substitute the indicated queries |
| Mixed feedback | Apply all changes, then continue |

#### Step 3B.4 — Store confirmed queries per grounded unit

After the user confirms (with or without modifications), store the confirmed queries:

- For **multi-topic**: write each topic's confirmed queries to:
  `data/lit_inputs/<topic_ground_id>/queries_confirmed.json`
- For **single-topic**: write to:
  `data/lit_inputs/<ground_id>/queries_confirmed.json`

Format:

```json
{
  "ground_id": "<ground_id>",
  "problem_queries": ["query string 1", "query string 2"],
  "method_queries": ["query string 1"],
  "constraint_queries": ["query string 1"]
}
```

#### Step 3B.5 — Sync research_mode to runtime config

> ⚠️ **Before any research begins**, write the mode-specific runtime values to `config/research_pipeline.env`.

Read the current `RESEARCH_MODE_*` preset values from `config/research_pipeline.env`, then write the runtime variables based on `research_mode`:

```bash
# Example for research_mode=medium:
RESEARCH_MODE=medium
MIN_OPENED_PAPERS=6
OPEN_TOP_K=3
MIN_RECENT_PAPERS=4
```

This ensures `grounded-research-lit` reads the correct thresholds when it runs `source config/research_pipeline.env`.

#### Step 3B.6 — Proceed to research

- **Multi-topic**: launch research subagents (see below), passing the path to `queries_confirmed.json`
- **Single-topic**: run `grounded-research-lit` directly, passing the path to `queries_confirmed.json`

---

## Strict Downstream Execution Fidelity Rule

For **every grounded unit** selected in Step 3 — whether there is only **one** grounded unit or **multiple** topic child units — this skill must require the downstream stages to be executed **strictly according to the downstream skill contracts**, not in a shortened, approximate, or weakly summarized form.

This rule applies equally to:

- single-topic runs
- multi-topic meeting fan-out runs
- any other grounded fan-out case

### Required behavior

For each grounded unit, this top-level orchestration must ensure that:

- `grounded-research-lit` is actually executed with its full artifact, opening, note-building, and literature-writing requirements
- `grounded-summary` is actually executed as the main evidence-rich report-drafting stage rather than a short recap
- `grounded-review` is actually executed as the final review / refinement / quality-gating stage — **with dedicated reviewer and writer subagents via `Task` tool, bounded repair rounds (initial + up to 5 rounds), explicit rubric scoring, hard-gate enforcement, and `reviewer_independence` recorded in `review_state.json`** — rather than a superficial cleanup pass, a monolithic parent-context review, or a repair step that was diagnosed but never executed
- `report-export` is actually executed from the final reviewed report rather than from an earlier intermediate draft

### Strong rule

Do **not** allow a grounded unit to pass downstream merely because some artifact file exists if the produced content is visibly much thinner, more abbreviated, or more weakly structured than the downstream skill contract requires.

Examples of unacceptable weak execution include:

- a literature result that looks like a snippet recap instead of a paper-note-driven literature report
- a summary output that collapses rich analysis into a short memo or a shallow bullet digest
- a review output that behaves like a light edit rather than a quality gate with real reviewer/writer subagent separation, bounded repair rounds, explicit verdict scoring, and `used_reviewer_role === true` / `used_writer_role === true` recorded in `review_state.json`; examples include:
  - review was run monolithically in the parent context (no `Task` tool call for reviewer)
  - `verdict === "repair"` was diagnosed but the writer subagent was never launched (no `Task` tool call for writer)
  - `research_report.md` was finalized with a pending repair verdict
  - `reviewer_independence === "unknown"` indicating no dedicated reviewer was used
- an export path that uses an intermediate draft instead of the final reviewed report

If the output of a downstream stage is clearly inconsistent with the intended depth or structure required by that stage's own skill, treat that stage as **not properly completed**.

---

## Subagent Rule for Multi-Topic Meetings

> ⚠️ **IMPORTANT**: This section works in conjunction with the **PARENT AGENT SUBAGENT ISOLATION RULES** section at the top of this document. **Read both sections together.**

If a meeting grounding result contains multiple topic child grounded notes, this skill must require topic-isolated downstream execution for **research and summary stages**.

### Required behavior

For each topic child grounded note:

- **must** create an independent subagent / branch for the **research stage**
- **must** create an independent subagent / branch for the **summary stage** (using the Two-Phase Execution Model)
- **must not** let subagent handle review or export stages
- After both subagent stages complete, **continue in parent context** for review and export

### Subagent scopes

Each topic requires **two sequential subagent branches**:

#### Branch 1 — Research (topic-isolated)

Perform:

1. `grounded-research-lit`
   - Search and open relevant literature
   - Build opened paper notes
   - Produce `data/lit_results/<ground_id>/lit.md`

After the subagent completes research and writes `lit.md`, **do NOT** have the subagent proceed to summary/review/export. The research subagent's task ends after `lit.md` is written.

#### Branch 2 — Summary (topic-isolated)

Perform:

1. `grounded-summary`
   - Read `grounded.md` and `lit.md` produced by Branch 1
   - Execute **Phase 1 (Literal Copy)**: copy `lit.md` paper analysis bodies verbatim into Section 4.1, complete the verification checklist before proceeding
   - Execute **Phase 2 (Thematic Synthesis)**: write all remaining sections
   - Produce `data/report_inputs/<ground_id>/summary.md`

The summary subagent is **fully responsible** for Two-Phase execution fidelity. The parent cannot enforce this if the subagent skips Phase 1 verification — so the subagent must be explicitly instructed to do it.

After the subagent completes summary and writes `summary.md`, **do NOT** have the subagent proceed to review/export. The summary subagent's task ends after `summary.md` is written.

### Parent context scope (AFTER RESEARCH AND SUMMARY)

After both research and summary subagents complete for all topic children, the parent agent should:

1. For each topic child (in parallel if supported):
   a. Verify that `lit.md` and `summary.md` both exist at their canonical paths
   b. Execute `grounded-review` **using reviewer/writer subagents via `Task` tool** with the bounded repair loop (initial review + up to 5 repair rounds). The reviewer subagent is loaded via `.cursor/agents/reviewer.md`, which provides a **different model** than the writer subagent (loaded via `.cursor/agents/writer.md`) to maximize reviewer independence.
   c. **Verify review contract compliance** (see below) before proceeding to export
   d. Execute `report-export` for requested formats

### Why this separation matters

Separating research and summary into dedicated subagents ensures:

- **Topic isolation** during literature search and summary writing
- **Two-Phase execution** for summary is enforced by the subagent itself, not by parent supervision
- Better parent-level control over **review repair loops**
- Proper enforcement of `review_state.json` verdict logic
- No subagent skipping of the review repair stage
- Parent retains cross-topic visibility for review and export, enabling horizontal consistency checks across topic branches

### Required Task Tool Invocation Pattern

For each topic child, you **MUST** use the `Task` tool with `subagent_type="generalPurpose"` for both branches.

#### Research subagent invocation (Branch 1):

```
Use the `.cursor/skills/grounded-research-lit` skill to run literature research.

Input:
- grounded_note_path: data/grounded_notes/<parent_ground_id>/child_outputs/<topic_id>/grounded.md
- ground_id: <topic_ground_id> (e.g., "meeting_001_topic01")
- queries_confirmed_path: data/lit_inputs/<topic_ground_id>/queries_confirmed.json
- transcription_language: [from user settings, default en — only relevant for audio/video source; passed downstream for grounding accuracy]

Research requirements:
- [copy from user's research requirements]

Search settings:
- search_backend: [from user settings]
- require_open_link: [from user settings]
- download_opened_literature: [from user settings]
- research_mode: [from user settings — simple / medium / complex; determines MIN_OPENED_PAPERS, OPEN_TOP_K, MIN_RECENT_PAPERS via config]

Confirmed queries: The user has reviewed and confirmed the search queries. Use the queries from data/lit_inputs/<topic_ground_id>/queries_confirmed.json directly — do NOT regenerate queries or ask the user again. Write queries.json from the confirmed file, then proceed to execute research.

Language requirement: ALL output content MUST be in English only (this applies to all intermediate artifacts; `transcription_language` above only affects upstream audio/video transcription accuracy, not this stage's output language).

IMPORTANT — Tools to use:
- When search_backend is "cursor", you MUST use the WebSearch and WebFetch tools directly
- DO NOT use MCP browser tools (ListMcpResources, browser_* tools) — these are not for literature research
- DO NOT try to call Python search scripts — those are for external API backend only
- web_search_reader.py is only for external backend

IMPORTANT: After completing research and writing the lit.md file, your task is complete. Do NOT proceed to summary, review, or export stages. The parent agent will handle those stages.

IMPORTANT: Your final response MUST end with this block (do not omit it):

{
  "subagent_claims_complete": true,
  "artifact_written": "data/lit_results/<ground_id>/lit.md",
  "lines_written": <actual line count of lit.md>,
  "round": 0,
  "completion_verified_by_subagent": true
}
```

#### Summary subagent invocation (Branch 2):

```
Use the `.cursor/skills/grounded-summary` skill to produce the report draft.

Input:
- grounded_note_path: data/grounded_notes/<parent_ground_id>/child_outputs/<topic_id>/grounded.md
- lit_result_path: data/lit_results/<topic_ground_id>/lit.md
- ground_id: <topic_ground_id> (e.g., "meeting_001_topic01")
- transcription_language: [from user settings, default en — only relevant for audio/video source; passed downstream for grounding accuracy]

IMPORTANT — Language rule:
ALL output content MUST be in English only. The `transcription_language` parameter above only affects upstream audio/video transcription accuracy — this stage always outputs English.

IMPORTANT — Two-Phase Execution:
You must follow the Two-Phase Execution Model in grounded-summary/SKILL.md strictly:

Phase 1 — Literal Copy (Section 4.1):
1. Read lit.md
2. Locate "## Detailed Analysis of Opened Papers" and "## Newly Strengthened / Newly Added Papers from Downloaded PDFs"
3. Copy both sections verbatim into Section 4.1 of summary.md
4. Do NOT paraphrase, condense, or rewrite during Phase 1
5. Run the Phase 1 Verification Checklist:
   - All opened papers present in Section 4.1? (count match vs lit.md)
   - All PDF-refined papers present? (count match vs lit.md)
   - Paper body word count >= 90% of lit.md per paper?
   - Subsection structure (Problem/Method/Evidence/Relevance/Limits) preserved?
   - Wording identical to lit.md, not paraphrased?
6. If any check fails, go back and fix Section 4.1 before proceeding

Phase 2 — Thematic Synthesis (all other sections):
7. Write Sections 1, 2, 3, 4.2, 5, 6, 7, 8
8. Phase 2 references Phase 1 but does not modify it

Output:
- data/report_inputs/<ground_id>/summary.md

IMPORTANT: After completing summary and writing the summary.md file, your task is complete. Do NOT proceed to review or export stages. The parent agent will handle those stages.

IMPORTANT: Your final response MUST end with this block (do not omit it):

{
  "subagent_claims_complete": true,
  "artifact_written": "data/report_inputs/<ground_id>/summary.md",
  "lines_written": <actual line count of summary.md>,
  "round": 0,
  "completion_verified_by_subagent": true
}
```

**Important:**
- Launch **all research subagents in parallel** when multiple topics exist
- Wait for all research subagents to complete
- Then launch **all summary subagents in parallel** (can overlap with research if lit.md is ready per topic)
- Wait for all summary subagents to complete
- After all subagent stages complete, continue in parent context for review/export per topic
- For each topic, run the full grounded-review (with repair loop) → report-export pipeline in the parent context
- **After each grounded-review run, verify contract compliance** (see below) before proceeding to export

### Review Contract Compliance Verification

**After each grounded-review execution, before proceeding to report-export, the parent agent must verify `review_state.json` against this checklist. If any check fails, the review is incomplete — re-execute the review properly before exporting.**

| Check | Required value | If fails |
|-------|---------------|----------|
| `used_reviewer_role` | `true` | Re-launch reviewer subagent via `Task` tool |
| `reviewer_agent_path` | not `null` | Ensure reviewer reads `.cursor/agents/reviewer.md` |
| `reviewer_independence` | `high` or `limited` (not `unknown`) | Re-execute reviewer via `Task` tool |
| `reviewer_model_hint` | not `inherit` or `unknown` | The reviewer subagent must be launched with the agent role declaration block — this triggers Cursor's auto-matching to load `.cursor/agents/reviewer.md` and its configured model |
| `verdict` | `pass` or `repair` | Review incomplete |
| If `verdict == "repair"` and `round < 2` | `used_writer_role === true` | Re-launch writer subagent via `Task` tool, then re-review |
| All 6 rubric scores present | `scores` object has all 6 dimensions | Re-execute reviewer |
| `weighted_total` | consistent with score formula | Re-execute reviewer |
| `round_<N>/` directory exists for each completed round | Each round's files in its own `round_<N>/` | Review incomplete — reorganize files into `round_<N>/` |
| `review_history.json` exists and covers all rounds | History matches each `round_<N>/review_state.json` | Review incomplete — rebuild `review_history.json` |
| Historical `round_<N>/` directories were never overwritten | Only new `round_<N+1>/` created; existing rounds unchanged | Review incomplete — restore from backup |

The presence of `review_report.md` and `research_report.md` on disk does **not** mean the review was properly executed. Only the metadata fields in `review_state.json` are authoritative for contract compliance.

**If `verdict == "repair"` and `used_writer_role == false`, do NOT proceed to export. Re-launch the writer subagent and complete the bounded repair loop first.**

### Branch-creation verification rule

For multi-topic downstream execution, it is **not enough** to merely claim that topics were handled separately.

The run must be able to state:
- whether a dedicated subagent / branch was **actually created** for each topic child's research stage
- whether a dedicated subagent / branch was **actually created** for each topic child's summary stage
- whether the summary subagent reported completing the **Phase 1 verification checklist**

If dedicated branch creation did not occur, or if the summary subagent skipped Phase 1 verification, the corresponding multi-topic workflow stage should be treated as failed or incomplete.

## Runtime Research Config Sync Rule

Some research-stage controls are implemented as global runtime configuration values rather than prompt-only instructions.

For any user-provided setting that affects the research stage global behavior, this skill must ensure that the effective runtime configuration is updated **before** invoking `grounded-research-lit`.

This includes, when provided by the user:

- `research_mode`
- `search_backend`
- `external_api_key`
- `require_open_link`
- `download_opened_literature`

### Required behavior

If the downstream research workflow reads these values from a shared config file such as:

- `config/research_pipeline.env`

then this skill must:

1. update that config file so the current run reflects the user's requested settings
2. do so before starting the research stage
3. ensure the research stage is executed against the updated config, not only against prompt text

#### How to sync `research_mode` to config

For `research_mode`, look up the corresponding values from the mode preset table in `config/research_pipeline.env` and write them to the runtime variables **before** any research subagent is launched:

| mode      | write `RESEARCH_MODE=<mode>` | then set runtime vars to |
|-----------|------------------------------|--------------------------|
| `simple`  | `RESEARCH_MODE=simple`       | `_SIMPLE_` preset values |
| `medium`  | `RESEARCH_MODE=medium`      | `_MEDIUM_` preset values |
| `complex` | `RESEARCH_MODE=complex`      | `_COMPLEX_` preset values |

Specifically, write these lines to `config/research_pipeline.env` (in addition to preserving existing non-mode variables):

```bash
RESEARCH_MODE=<mode>
MIN_OPENED_PAPERS=<preset_MIN_OPENED>
OPEN_TOP_K=<preset_OPEN_TOP_K>
MIN_RECENT_PAPERS=<preset_MIN_RECENT>
```

Example for `research_mode=medium`:
```bash
RESEARCH_MODE=medium
MIN_OPENED_PAPERS=6
OPEN_TOP_K=3
MIN_RECENT_PAPERS=4
```

This must happen **before** `grounded-research-lit` is invoked, so that the skill's `source config/research_pipeline.env` call reads the correct values.

Prompt-level instructions alone are **not sufficient** when a downstream stage depends on runtime config.

### Strong rule

Do **not** merely mention, forward, or restate user research settings in natural language if the actual downstream execution depends on a config file or environment-backed control.
The settings must be made effective in the runtime configuration used by the current run.

### Completion rule for config-backed settings

A research setting counts as applied only if both are true:

- the relevant runtime config has been updated for the current run
- the downstream research stage has actually executed using that updated config

If a requested config-backed setting cannot be applied, fail clearly or report that the setting was not honored.

---

## Backend-Specific Research Sufficiency Rule

This top-level orchestration skill must respect the backend-specific completion rules of `grounded-research-lit`.

### External backend rule

If the actual research backend is `external`:

- do **not** impose a fixed minimum successful-download count
- allow the research stage to analyze as many opened relevant literature items as the run actually obtains
- if downloads are enabled, ensure the auxiliary download/refinement flow is completed before treating research as finished

### Cursor-native backend rule

If the actual research backend is `cursor`:

- do **not** treat browsing alone as research completion
- before downstream report drafting begins, the research stage must have searched/opened/read **at least `MIN_OPENED_PAPERS` unique relevant literature items**
- the Cursor-native branch must preserve opened-source artifacts under `opened_sources/`
- the Cursor-native branch must run `prepare_opened_paper_notes.py` and produce:
  - `opened_paper_notes.jsonl`
  - files under `opened_paper_notes/`
- if `DOWNLOAD_OPENED_LITERATURE=true`, the Cursor-native branch must also successfully download **at least `MIN_OPENED_PAPERS` unique relevant literature items**, or explicitly report why this target could not be reached after continued search/open/download attempts
- before moving to `grounded-summary`, the parent/main agent must explicitly verify the opened-paper count from `search_results.json` and `opened_sources/` rather than relying only on stage self-report
- an item counts toward the top-level opened threshold only if all of the following are true:
  - `is_research_literature == true`
  - `opened == true`
  - `open_status == "success"`
  - `opened_source_path` is present in `search_results.json`
  - the file referenced by `opened_source_path` actually exists on disk under `data/lit_inputs/<ground_id>/opened_sources/`
- snippet-only candidates, failed opens, or missing opened-source files do **not** count toward the minimum-`$MIN_OPENED_PAPERS` rule
- if the explicitly verified opened count is below `MIN_OPENED_PAPERS`, do **not** move to `grounded-summary`; the research stage must continue or fail clearly
- do not move to `grounded-summary` until these research-stage artifact and sufficiency conditions have been satisfied

---

## Report Richness Preservation Rule

This orchestration skill must preserve the intended depth of the pipeline.

That means:

- `grounded-research-lit` is expected to produce a substantial literature analysis rather than a thin search recap
- `grounded-summary` is expected to produce the **main evidence-rich report draft** for the grounded unit
- `grounded-review` is expected to perform **final review, refinement, evidence alignment, overclaim control, and detail restoration when needed**
- `report-export` is expected to export the reviewed report without materially compressing it

### Strong rule

Do **not** frame `grounded-summary` as a short memo stage when invoking it from this top-level workflow.
Do **not** frame `grounded-review` as a second summarization pass. It is a **reviewer/writer subagent loop with bounded repair rounds and explicit verdict scoring**.
Do **not** instruct downstream stages to shrink detailed literature analysis into a minimal bullet recap.

### Required preservation behavior

For each grounded unit, the downstream flow must preserve and integrate:

- the grounded source findings
- the literature-based deep analysis
- evidence strength and limitations
- unresolved questions and decision-critical gaps
- concrete implications for the current project

The final report should be a substantial, well-organized report, not a compressed note.

### Execution-quality interpretation rule

If a downstream artifact exists but the content is conspicuously too brief, too generic, or too weakly structured relative to the downstream skill's expected behavior, do **not** treat that stage as successfully executed just because a file was written.

In particular:

- a very brief or generic literature result suggests `grounded-research-lit` was not followed strictly enough
- a very brief or generic report draft suggests `grounded-summary` was not followed strictly enough (also check: did the Phase 1 literal copy of `lit.md` paper analysis bodies into Section 4.1 complete with the required verification? Was Section 4.1 word count approximately preserved vs `lit.md`? Were all papers from `lit.md` included?)
- a very brief or weakly corrective final report suggests `grounded-review` was not followed strictly enough (also check: did it use reviewer/writer subagents via `Task` tool? did it go through the bounded repair loop? did `review_state.json` record `used_reviewer_role: true`?)

The top-level orchestration must prefer **faithful stage execution** over merely obtaining minimal placeholder artifacts.

---

## Downstream Stage Reuse

For each grounded unit selected in Step 3, reuse the existing downstream skills in order.

### Research stage

Apply:

- `grounded-research-lit`

using the grounded unit as input and the user-confirmed queries from `queries_confirmed.json`.

Pass along:

- User-confirmed queries: the path to `data/lit_inputs/<ground_id>/queries_confirmed.json` — the `grounded-research-lit` skill should read queries from this file instead of generating its own
- User-provided research settings when relevant, including:
  - `research_requirements`
  - `search_backend`
  - `external_api_key`
  - `require_open_link`
  - `download_opened_literature`

> ⚠️ **Single-topic**: After Step 3B completes, the confirmed queries file already exists. Pass `queries_confirmed_path` to `grounded-research-lit` so it uses the confirmed queries directly without re-generating or re-asking.

The top-level workflow must also enforce the backend-specific research sufficiency rule:

- if backend=`external`, do not require a fixed minimum download count
- if backend=`cursor`, do not allow research to finish unless at least `MIN_OPENED_PAPERS` unique relevant literature items were searched/opened/read and the expected opened-source / paper-note artifacts were produced
- if backend=`cursor`, the parent/main agent must explicitly verify the minimum-`$MIN_OPENED_PAPERS` opened count from local artifacts before allowing the pipeline to proceed to `grounded-summary`
- if backend=`cursor` and `DOWNLOAD_OPENED_LITERATURE=true`, do not allow research to finish unless at least `MIN_OPENED_PAPERS` unique relevant literature items were successfully downloaded, or the run explicitly reports why this target could not be reached after continued search/open/download attempts

### Summary stage

Apply:

- `grounded-summary`

using the grounded note and the literature result from the current grounded unit.

`grounded-summary` is the **main report-drafting stage**.
It should produce the primary evidence-rich report draft for the grounded unit.
It must preserve relevant literature depth and integrate it into the report body rather than compressing it into a shallow memo.
It must be executed according to the full `grounded-summary` skill expectations even when the current run is only a single-topic case.

### Review stage

Apply:

- `grounded-review`

using the current grounded unit's:

- grounded note
- literature result
- report draft

`grounded-review` is the **final refinement, verification, and quality-gating stage**.

**CRITICAL: This stage must be executed using reviewer and writer subagents via `Task` tool, not as a single monolithic pass in the parent context.**

The required execution pattern is:

1. Launch **reviewer subagent** via `Task` tool to score, diagnose, and produce repair actions. The reviewer prompt **must start with the agent role declaration block** to trigger Cursor's agent auto-matching:

   ```
   ---
   You are operating as the **REVIEWER AGENT** (grounded-review-reviewer).
   Read and follow .cursor/agents/reviewer.md now to load your reviewer configuration and model.
   ---
   ```

   This loads `.cursor/agents/reviewer.md`, which provides the dedicated reviewer model (configured in the agent file frontmatter) and the full reviewer role definition.
2. **Parent agent** creates `round_<N>/` directory and persists `review_report.md` and `review_state.json` to `data/review_outputs/<ground_id>/round_<N>/`
3. **Parent agent** waits for reviewer's completion signal block in transcript before proceeding

   The reviewer subagent's final response must include:
   ```
   {
     "subagent_claims_complete": true,
     "artifact_written": "data/review_outputs/<ground_id>/round_<N>/review_state.json",
     "lines_written": <N>,
     "round": <current round>,
     "completion_verified_by_subagent": true
   }
   ```

4. If verdict is `repair` and round < 2: launch **writer subagent** via `Task` tool to apply repairs. The writer prompt **must start with the agent role declaration block**:

   ```
   ---
   You are operating as the **WRITER AGENT** (grounded-review-writer).
   Read and follow .cursor/agents/writer.md now to load your writer configuration.
   ---
   ```

   This loads `.cursor/agents/writer.md`, which provides the writer role definition.
5. **Parent agent** waits for writer's completion signal block in transcript before proceeding

   The writer subagent's final response must include:
   ```
   {
     "subagent_claims_complete": true,
     "artifact_written": "data/reports/<ground_id>/research_report.md",
     "lines_written": <N>,
     "round": <current round>,
     "completion_verified_by_subagent": true
   }
   ```

6. **Parent agent** archives the current round: if round > 0, ensure `round_<N>/` is intact (immutable)
7. Launch **reviewer subagent** again to re-check the revised draft (round + 1). Use the same reviewer prompt template with the agent role declaration block.

8. **Parent agent** creates `round_<N+1>/` directory and persists the new `review_report.md` and `review_state.json`
9. Repeat steps 3–8 for at most **5 repair rounds**
10. Only after reviewer passes (or loop is exhausted): update `review_history.json`, update root-level `review_report.md` and `review_state.json` (symlinks/copies), and finalize `research_report.md`

The review stage must produce the final reviewed report. `review_state.json` must record `used_reviewer_role: true` and `used_writer_role: true` if the subagent loop was properly executed.

**Agent model separation summary:**
- **Reviewer subagent**: loaded via `.cursor/agents/reviewer.md` → model is whatever `model` field is in reviewer.md frontmatter (dedicated, different from writer)
- **Writer subagent**: loaded via `.cursor/agents/writer.md` → model is whatever `model` field is in writer.md frontmatter (typically `inherit`)

### Export stage

Apply:

- `report-export`

using the final reviewed report from the current grounded unit, the user-requested `output_formats`, and the `output_lang` parameter.

When `data/reports/<ground_id>/research_report.md` exists, export must use that final reviewed report rather than an earlier draft such as `summary.md`.

When `output_lang` is not `en`, the Agent must translate the English report into the target language before exporting. Perform the translation by reading the report content and writing a translated markdown version, then use that translated file for all format exports. All markdown structure (headings, tables, code fences, links, formatting) must be preserved during translation.

---

## Content Truth Rule

The final content truth source for each grounded unit remains:

- `data/reports/<ground_id>/research_report.md`

This skill must not redefine the truth source.

Export should happen **after** review, not before.

---

## Language Consistency Rule

### Intermediate Pipeline Outputs: English Only

All intermediate artifacts produced by the pipeline **must be written in English only**, regardless of the `output_lang` setting:

- `grounded.md`
- `lit.md`
- `summary.md`
- `research_report.md`
- `review_report.md`

When invoking any downstream skill or subagent for grounding, research, summary, or review, always include this instruction:

```
Language requirement: ALL output content MUST be in English only.
- Write all headings in English
- Write all body text in English
- Do not mix languages within the same document
- If the source material is in another language, translate/summarize the key content into English
```

### Final Export Outputs: Controlled by `output_lang`

The `output_lang` parameter controls the language of the **final export products** only (e.g., PDF, DOCX, PPTX).

It has **no effect** on any intermediate pipeline artifacts.

The default export language is **English (`en`)**.

### Parameter Summary

| Parameter | Scope | Purpose |
|-----------|-------|---------|
| `transcription_language` | Audio/video grounding | Guides Whisper transcription |
| `output_lang` | Export stage only | Controls final export language |

These two parameters are independent and serve different purposes.

### Audio Export Language Rule

The `audio` export format is **always narrated in English**, regardless of the `output_lang` setting. This is because audio narration synthesizes the report content directly, and the `audio` backend is configured for English speech synthesis. Do not apply `output_lang` translation to the `audio` format.

---

## Output Reporting Requirements

At the end, this skill must clearly report:

1. which grounding workflow was used
2. whether grounding produced:
   - one grounded unit, or
   - multiple grounded units
3. for each grounded unit:
   - grounded note path
   - whether the grounded note path is the canonical downstream path required by this skill
   - literature result path
   - report-draft path
   - reviewed report path
   - final export path(s)
   - whether the backend-specific research sufficiency rule was satisfied, not applicable, or only partially satisfied with an explicit reason
   - for backend=`cursor`, the explicitly verified opened-paper count used by the parent/main agent
   - if applicable, whether the required topic-isolated subagent / branch was actually created for that grounded unit (both research and summary branches for multi-topic cases)
   - for the summary stage: whether the summary subagent completed the Phase 1 verification checklist and whether Section 4.1 word count is approximately preserved vs lit.md
   - whether each downstream stage appears to have been executed in full according to its own skill contract, or whether any stage output looked materially abbreviated
4. any stage that failed, if relevant

For multi-topic meetings, the final report must make clear that multiple topic branches were processed separately.

---

## Supported Scope for Version 1

This version is intended for:

- exactly one input file at the top level
- automatic grounding via existing skills
- per-grounded-unit downstream reuse
- multi-topic meeting fan-out when produced by grounding
- final export in one or more requested formats

This version is **not** intended to implement:

- multi-input merging
- cross-input joint synthesis before grounding
- manual user-specified topic counts
- replacement of lower-level skills

---

## Artifact-Based Completion Rule

A stage counts as complete only if its expected output artifact has actually been written to the correct path.

Examples:

- grounding -> canonical grounded note output exists at the required downstream path
- research -> expected literature result output exists
- summary -> expected report-draft output exists
- review -> expected `research_report.md` exists
- export -> expected requested export files exist

Stating that a stage was invoked, planned, or requested is not enough.

For this top-level skill, artifact existence is a necessary condition but not always a sufficient quality condition. If the produced artifact is materially inconsistent with the required depth or structure of the downstream skill that produced it, the stage should be treated as not properly completed.

For grounding specifically, artifact existence means the **canonical** downstream grounded artifacts exist at the required locations, not merely that some grounded-like file was written somewhere else.

---

## Failure Handling

- If `input_path` is missing, fail clearly.
- If the input extension is unsupported by the current router behavior, fail clearly.
- If grounding does not complete, do not pretend the full pipeline succeeded.
- If grounding writes only non-canonical grounded files and fails to write the required canonical grounded-note path(s), treat grounding as failed or incomplete.
- If multi-topic downstream execution does not create a dedicated subagent / branch for each required topic child, treat the multi-topic run as failed or incomplete rather than silently continuing in one shared context.
- If downstream processing fails for one branch in a multi-topic meeting, report which branch failed.
- If a downstream artifact exists but is clearly too abbreviated to satisfy the downstream skill contract, treat that stage as failed or incomplete rather than claiming success.
- Do not claim success until grounding, research, summary, review, and export have actually completed for the intended grounded unit(s).

---

## External Reviewer API Configuration

When `reviewer_api_config` is provided in the one-report invocation, the review stage uses the external LLM API as the reviewer for **all rounds** of the bounded loop — not just the first round. The external API replaces the local Cursor reviewer subagent for every round (Round 0, Round 1, ..., Round N) until the report passes or the loop is exhausted.

This is useful when you want to:
- Use a specific external model for reviewer (e.g., a cheaper or more capable model)
- Integrate with existing API infrastructure
- Have more control over the reviewer's model and parameters

### Parameter Schema

```yaml
reviewer_api_config:
  provider:          # Required. External LLM provider type
    type: string
    enum: [openai, gemini]
    description: |
      "openai" - OpenAI-compatible API (supports official OpenAI, vLLM, third-party proxies)
      "gemini" - Gemini API (supports JD Cloud Gemini, Google Gemini API)
  
  model:              # Required. Model identifier
    type: string
    description: "Specific model ID (e.g., gpt-4o, gpt-4o-mini, Gemini-3-Flash-Preview)"
  
  api_key:            # Optional. Direct API key
    type: string
    description: "API key for authentication. Takes precedence over api_key_env."
  
  api_key_env:        # Optional. Environment variable name
    type: string
    description: "Environment variable containing the API key (alternative to api_key)"
  
  base_url:           # Optional. Custom API endpoint
    type: string
    description: "Override the default API endpoint. Useful for proxies or custom deployments."
  
  temperature:         # Optional. Default: 0.3
    type: number
    description: "Temperature for review generation (recommend 0.1-0.3)"
  
  max_tokens:         # Optional. Default: 4096
    type: integer
    description: "Maximum tokens in response"

  fallback_to_local:   # Optional. Default: true
    type: boolean
    description: "If external API call fails on Round N, fall back to local Cursor reviewer for that round only. Subsequent rounds continue using external API unless all retries are exhausted."
```

**At least one of `api_key` or `api_key_env` must be provided.**

### Provider Details

| Provider | Default Endpoint | Notes |
|----------|-----------------|-------|
| openai | https://api.openai.com/v1/chat/completions | OpenAI-compatible APIs |
| gemini | https://generativelanguage.googleapis.com/v1beta/models | JD Cloud / Google Gemini |

### Execution Behavior

**When `reviewer_api_config` is provided, the external API is the reviewer for every round of the bounded loop:**

1. **Review stage** detects the external config
2. **Round 0**: constructs prompts from `grounded.md` + `lit.md` + `summary.md`
3. **Round N (N >= 1)**: constructs prompts from current `research_report.md` + previous `round_<N-1>/review_report.md` + repair actions context
4. **Calls `call_ext_api.py`** via Shell tool with system prompt (from `.cursor/agents/reviewer.md`) + user prompt
5. **Parses JSON response** into rubric scores, verdict, repair actions
6. **Persists outputs** to `round_<N>/` directories
7. **Sets** `reviewer_independence: "high"` and `reviewer_agent_path: null` (external mode)
8. **If verdict = repair and round < 5**: launches writer subagent via `Task` tool, then loops back to step 2 with updated `research_report.md`
9. **If verdict = pass**: launches writer for light repair, then finalizes

**When `reviewer_api_config` is NOT provided:**
- Uses local Cursor reviewer subagent via `Task` tool for all rounds
- Behavior is unchanged from current implementation

### API Provider Examples

#### OpenAI Official API:

```yaml
reviewer_api_config:
  provider: openai
  model: gpt-4o
  api_key_env: OPENAI_API_KEY
  temperature: 0.2
```

#### OpenAI Third-Party Proxy:

```yaml
reviewer_api_config:
  provider: openai
  model: gpt-4o-mini
  api_key: "sk-xxxxx"
  base_url: "https://api.gptplus5.com/v1"
  temperature: 0.2
```

#### JD Cloud Gemini:

```yaml
reviewer_api_config:
  provider: gemini
  model: Gemini-3-Flash-Preview
  api_key_env: GEMINI_API_KEY
  base_url: "https://modelservice.jdcloud.com/v1"
  temperature: 0.2
```

#### Google Gemini:

```yaml
reviewer_api_config:
  provider: gemini
  model: gemini-2.5-pro-preview-03-12
  api_key_env: GOOGLE_API_KEY
  temperature: 0.2
```

---

## Example Invocation

### Local File Input

```text
Use the existing `.cursor/skills/one-report/` skill to generate a full report.

Input:
- input_path: data/raw_inputs/docs/example.pdf
- research_mode: medium

Research requirements:
- focus on technical contribution, evidence strength, limitations, and concrete next steps
- require opened-link reading
- preserve literature depth in the report body

Search settings:
- search_backend: auto
- download_opened_literature: false

Output:
- output_formats: md,pdf,pptx

Language requirement: ALL output content MUST be in English only.
```

### URL Input: arXiv Paper

```text
Use the existing `.cursor/skills/one-report/` skill to generate a full report.

Input:
- input_path: https://arxiv.org/abs/2301.07041
- output_formats: md,pdf
- research_mode: medium

Research requirements:
- focus on technical contribution, evidence strength, limitations

The skill will:
1. Download the arXiv paper PDF via remote-input skill
2. Continue with document-grounding pipeline
```

### URL Input: YouTube Video

```text
Use the existing `.cursor/skills/one-report/` skill to generate a full report.

Input:
- input_path: https://www.youtube.com/watch?v=dQw4w9WgXcQ
- output_formats: md,pdf
- research_mode: medium

Research requirements:
- focus on key insights and technical details

The skill will:
1. Download the YouTube video via remote-input skill
2. Continue with meeting-video-grounding pipeline
```

### Example with External Reviewer (OpenAI):

```text
Use the existing `.cursor/skills/one-report/` skill to generate a full report.

Input:
- input_path: data/raw_inputs/docs/example.pdf
- research_mode: medium

Research requirements:
- focus on technical contribution, evidence strength, limitations, and concrete next steps

Output:
- output_formats: md,pdf

Reviewer:
- provider: openai
- model: gpt-4o
- api_key_env: OPENAI_API_KEY
- temperature: 0.2
```

### Example with External Reviewer (JD Cloud Gemini):

```text
Use the existing `.cursor/skills/one-report/` skill to generate a full report.

Input:
- input_path: data/raw_inputs/meeting.pdf
- research_mode: medium

Output:
- output_formats: md

Reviewer:
- provider: gemini
- model: Gemini-3-Flash-Preview
- api_key_env: GEMINI_API_KEY
- base_url: "https://modelservice.jdcloud.com/v1"
- temperature: 0.2
```

### Example with External Reviewer (Third-party Proxy):

```text
Use the existing `.cursor/skills/one-report/` skill to generate a full report.

Input:
- input_path: data/raw_inputs/meeting.pdf
- research_mode: medium

Output:
- output_formats: md

Reviewer:
- provider: openai
- model: gpt-4o-mini
- api_key: "sk-xxxxx"
- base_url: "https://api.custom-proxy.com/v1"
- temperature: 0.2
```

### Example transcript exception

```text
Use the existing `.cursor/skills/one-report/` skill to generate a full report.

Input:
- input_path: data/raw_inputs/transcripts/example.txt
- research_mode: simple

This txt file is an already-transcribed meeting transcript. Treat it as meeting input rather than a general document.

Output:
- output_formats: md,pdf
```