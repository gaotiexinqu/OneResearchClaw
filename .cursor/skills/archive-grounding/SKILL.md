---
name: archive-grounding
description: Unpack a ZIP archive, inventory its files, run the corresponding child grounding skill for each supported child file, and then write a real archive-level grounded.md.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob


---

# Archive Grounding

This skill handles **ZIP archives** as **container inputs** in the any-input -> grounding -> downstream research / summary / report pipeline.

Its job is **not** to directly pretend that the whole archive has already been deeply grounded after unpacking. Its job is to:

1. unpack the archive,
2. build a stable archive bundle,
3. identify supported child files,
4. run the corresponding child skill for each supported child file,
5. collect those child bundles under the current archive bundle's `child_outputs/` directory,
6. and only then write a real archive-level `grounded.md`.

## Position in the pipeline

This skill is for archives that package together multiple materials, such as:

- project material bundles
- meeting material bundles
- report + slides + tables + audio/video attachments
- mixed research input packages

This skill is **not** a replacement for the child grounding skills themselves.

- `document-grounding` still handles document content
- `table-grounding` still handles spreadsheets / CSV tables
- `pptx-grounding` still handles PowerPoint decks
- `meeting-audio-grounding` handles meeting audio inputs
- `meeting-video-grounding` handles meeting videos
- `audio_structuring` remains the atomic audio transcription backend reused by the higher-level audio/video meeting entry skills

This skill acts as an **orchestrator over packaged files**.

---

## Supported child file routing

The first version should route supported child files using a simple extension-based mapping:

- `.pdf`, `.docx`, `.md`, `.txt` -> `document-grounding`
- `.xlsx`, `.csv` -> `table-grounding`
- `.pptx` -> `pptx-grounding`
- `.mp3`, `.wav`, `.m4a` -> `meeting-audio-grounding`
- `.mp4`, `.mov`, `.mkv` -> `meeting-video-grounding`

Unsupported files may be recorded and skipped, but they must not be silently treated as grounded.

---

## Required Workflow

When using this skill, you **must** follow this workflow:

1. First run the existing script entrypoint:

   ```bash
   bash .cursor/skills/archive-grounding/scripts/run.sh <input_zip> <output_root>
   ```

2. The script generates an **archive bundle skeleton** and inventory files such as:

   - `extracted.md`
   - `extracted_meta.json`
   - `manifest.json`
   - `routed_items.json`
   - `unpacked/`
   - `child_outputs/`

3. After the archive bundle is generated, read:

   - `extracted.md`
   - `extracted_meta.json`
   - `manifest.json`
   - `routed_items.json`

4. Then enumerate the supported child files in the archive.

5. For **each supported child file**, you must actually run the corresponding child skill. Do **not** stop after inventory / route planning.

6. For child files inside the archive, all downstream child grounding outputs must be written **inside the current archive bundle's `child_outputs/` directory**, not into the global grounding root.

7. Use the recommended child output path recorded in `routed_items.json` when present.

8. A child file is only considered completed if one of the following is true:

   - its corresponding child bundle was actually generated under `child_outputs/`, or
   - a concrete failure reason is explicitly recorded.

9. Do **not** pretend that a child file was fully grounded merely because it was detected, inventoried, or assigned a route.

10. Only after the supported child files have been processed (or explicit failures have been recorded) may you write the archive-level `grounded.md`.

11. Do **not** create a placeholder `grounded.md`.

12. The task is **not complete** if:

   - only the archive bundle skeleton exists,
   - `manifest.json` / `routed_items.json` exist but no child skills were actually run,
   - child bundles were written to the global grounding root instead of this archive bundle's `child_outputs/`, or
   - archive-level `grounded.md` was written before the child processing step was completed.

---

## Input

```bash
bash .cursor/skills/archive-grounding/scripts/run.sh <input_zip> <output_root>
```

### Arguments

- `input_zip`: path to a `.zip` archive
- `output_root`: parent directory under which the archive bundle should be created

Example:

```bash
bash .cursor/skills/archive-grounding/scripts/run.sh \
  /path/to/materials.zip \
  data/grounded_notes
```

This will create something like:

```text
/data/grounded_notes/archive-materials/
```

---

## Output bundle contract

The script should create:

```text
<archive_bundle>/
├─ extracted.md
├─ extracted_meta.json
├─ manifest.json
├─ routed_items.json
├─ unpacked/
├─ child_outputs/
└─ grounded.md   # written later by the agent, not by the script
```

### File roles

#### `extracted.md`

Human-readable archive overview for the agent.

It should include:

- archive overview
- detected file inventory summary
- supported vs skipped items
- routed child skills
- the rule that child outputs must live under `child_outputs/`

#### `extracted_meta.json`

Global archive metadata, such as:

- source archive path
- archive id
- total file count
- supported file count
- skipped file count
- unpack directory
- generation timestamp

#### `manifest.json`

Machine-readable file inventory for unpacked contents.

Each item should include:

- relative path
- file name
- extension
- size
- detected type
- supported / unsupported
- skip reason if any

#### `routed_items.json`

Machine-readable routing plan for supported child files.

Each routed item should include:

- source relative path
- detected type
- routed skill
- status
- recommended child output path
- notes / failure reason if any

#### `child_outputs/`

Container directory for all downstream child grounding bundles generated from supported child files in this archive.

Child grounding outputs must be stored here rather than in the global grounding root.

---

## grounded.md schema (recommended)

After the child files have been processed and the child bundles exist, the agent should write a stable archive grounding note such as:

```markdown
# Archive Grounding

## 1. Archive Overview

## 2. Included Materials

## 3. Successfully Processed Child Items

## 4. Key Signals Across Materials

## 5. Skipped / Unsupported / Failed Items

## 6. Suggested Next Steps

## 7. Search Keywords
```

This is an **archive-level grounding note**, not a polished final report.

---

## Important rule on absent file types

Do **not** treat the absence of a file type as a risk by default.

Examples:

- if the archive simply does not contain PPTX files, do not mark that as a missing item
- if the archive simply does not contain audio or video files, do not mark that as a missing item
- if the archive simply does not contain tables, do not mark that as a missing item

Only report:

- actual unsupported items,
- actual skipped items,
- actual failed child processing steps,
- or actual inconsistencies between the archive contents and the generated child outputs.

---

## Quality bar

A good result means:

- the archive bundle exists
- the file inventory is correct
- every supported child file was either actually processed by its corresponding child skill or recorded with a concrete failure reason
- child bundles are stored under this archive bundle's `child_outputs/`
- the archive-level `grounded.md` is written only after child processing is complete
- the final archive note is useful as a stable intermediate artifact for downstream research / summary / report

A bad result means:

- the agent only unpacked and inventoried the archive
- the agent wrote archive-level `grounded.md` without running the child skills
- child outputs were scattered into the global grounding root
- unsupported or skipped files were silently treated as processed
- placeholder `grounded.md` was created

---

## Failure handling

If a supported child file cannot be processed successfully, record that explicitly.

Examples:

- child skill missing
- child script failed
- child bundle path not created
- file appears corrupted
- environment dependency missing

Do **not** hide child-processing failures behind a fake “archive success”.