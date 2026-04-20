---
name: pptx-grounding
description: Extract a structured evidence bundle from a .pptx deck, then write a real grounded.md from the bundle.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob

---

# PPTX Grounding

This skill handles **PowerPoint (`.pptx`)** inputs in the any-input -> grounding -> downstream research / summary / report pipeline.

Its job is **not** to write a polished final report. Its job is to produce a stable, structured, reusable **evidence bundle** for a deck. After that, the agent must read the bundle and write a real `grounded.md`.

## When to use this skill

Use this skill for common PowerPoint decks such as:

- project updates
- proposal decks
- experiment / result review decks
- internal presentations
- lecture / meeting decks
- any `.pptx` where the main evidence lives in slide titles, bullets, text boxes, images, tables, charts, and speaker notes

Use this skill when **slide order, per-slide structure, and per-slide assets matter**.

## Relationship to other grounding skills

This skill is **not** the same as document-grounding:

- document-grounding is primarily linear-document oriented
- pptx-grounding is slide-oriented
- slide order, slide-level structure, and per-slide assets matter here

This skill is also **not** table-grounding:

- it may export tables and charts found inside a deck
- but it treats them as **deck evidence assets**, not as standalone spreadsheet analysis tasks

---

## Supported extraction targets

This skill should extract and organize the following when present:

- deck-level metadata
- slide-by-slide structure
- slide title extraction
- bullet / paragraph extraction
- other text-box extraction
- speaker notes extraction
- embedded image export
- native PowerPoint table export
- native PowerPoint chart export (lightweight best-effort extraction)
- `AssetRef` insertion into `extracted.md`
- bundle generation for downstream agent grounding

### Out of scope

This skill does **not** aim to handle the following:

- video / audio extraction
- animation / transition analysis
- OCR on images
- SmartArt semantic reconstruction
- precise visual rendering / slide preview generation
- embedded file deep extraction
- comment / revision workflows
- automatic polished final report generation

---

## Required Workflow

When using this skill, you **must** follow this workflow:

1. First run the existing script entrypoint:

   ```bash
   bash .cursor/skills/pptx-grounding/scripts/run.sh <input_pptx> <output_root>
   ```

2. The script generates an **evidence bundle only**.
   It does **not** generate `grounded.md`.

3. After the bundle is generated, read:

   - `extracted.md`
   - `extracted_meta.json`
   - `slide_index.json`
   - `asset_index.json`

4. If `AssetRef` blocks are present in `extracted.md`, inspect the referenced assets before writing `grounded.md`.
   This includes, when present:

   - `assets/images/*`
   - `assets/tables/*`
   - `assets/charts/*`

5. Then write a **real** `grounded.md` into the same bundle directory.

6. Do **not** create a placeholder `grounded.md`.
   If `grounded.md` exists, it must be a real grounding note written after inspecting the generated bundle.

7. The task is **not complete** if only the extraction bundle exists.

8. The task is also **not complete** if `grounded.md` is written without first generating and using the bundle evidence.

---

## Input

```bash
bash .cursor/skills/pptx-grounding/scripts/run.sh <input_pptx> <output_root>
```

### Arguments

- `input_pptx`: path to a `.pptx` file
- `output_root`: parent directory under which the bundle should be created

Example:

```bash
bash .cursor/skills/pptx-grounding/scripts/run.sh \
  /path/to/deck.pptx \
  data/grounded_notes
```

This will create something like:

```text
<data/grounded_notes>/<ground_id>/
```

---

## Output bundle contract

The script should create:

```text
<pptx_bundle>/
├─ extracted.md
├─ extracted_meta.json
├─ slide_index.json
├─ asset_index.json
├─ assets/
│  ├─ images/
│  ├─ tables/
│  └─ charts/
└─ grounded.md   # written later by the agent, not by the script
```

### File roles

#### `extracted.md`

Human-readable entrypoint for the agent.

It should include:

- deck overview
- slide-by-slide extraction
- title
- bullet blocks
- other text blocks
- notes text
- `AssetRef` blocks for images / tables / charts

#### `extracted_meta.json`

Global deck metadata, such as:

- source file
- source type
- deck id
- slide count
- parser name
- note / image / table / chart counts
- extraction timestamp
- extraction scope notes

#### `slide_index.json`

Machine-readable slide-level index.

Each slide record should include:

- slide number
- slide id
- layout name (if available)
- title
- bullet blocks
- text blocks
- notes text
- assets
- shape statistics

#### `asset_index.json`

Global asset registry for all exported assets.

Each asset record should include:

- asset id
- asset type
- slide number
- source shape id / name
- relative path
- lightweight metadata
- extraction status

---

## Extraction targets

### 1. Slide title

Extract separately when possible.

### 2. Bullet / paragraph text

Preserve paragraph order and indentation level where possible.

### 3. Other text boxes

Extract non-title text separately from bullet blocks.

### 4. Speaker notes

Extract notes text when present.

### 5. Images

Export embedded images into `assets/images/` and register them in `asset_index.json`.

### 6. Tables

For native PowerPoint tables:

- export markdown view
- export csv view
- register as table assets

### 7. Charts

For native PowerPoint charts, do lightweight best-effort export:

- chart metadata JSON
- flattened CSV if possible
- register as chart assets

If chart extraction is partial, record that clearly in metadata rather than pretending extraction succeeded fully.

---

## grounded.md schema (recommended)

After reading the bundle, the agent should write a stable grounding note such as:

```markdown
# PPTX Grounding

## 1. Main Topic / Purpose

## 2. Deck Structure / Narrative Flow

## 3. Main Points

## 4. Important Evidence and Assets

## 5. Speaker Notes Signals (only if present and materially useful)

## 6. Gaps / Risks / Ambiguities

## 7. Suggested Next Steps

## 8. Search Keywords
```

### Writing guidance

`grounded.md` should be a **stable intermediate grounding note**, not a polished final report.

It should:

- summarize what the deck is mainly about
- preserve the deck's narrative flow at a useful level
- call out the most important slides and extracted evidence that materially affects interpretation
- mention notes, tables, charts, or other asset types only when they are actually present and useful
- record real ambiguity, evidence gaps, or extraction issues that matter for downstream use
- support downstream research / summary / report steps

It should **not**:

- pretend the bundle was fully interpreted without inspecting assets
- invent conclusions unsupported by the deck
- treat the simple absence of an asset type as a risk or extraction failure
- add a "Missing Assets" section just because a deck has no charts, no tables, or no speaker notes
- replace the downstream final report stage

### Important rule on absent asset types

Do **not** write that charts / tables / images / speaker notes are "missing" unless there is positive evidence that the deck contains them and extraction failed.

If an asset type is simply **not present** in the PPTX, do one of the following:

- omit it entirely from `grounded.md`, or
- mention it neutrally only if necessary for clarity

Examples of acceptable neutral wording:

- `No speaker notes were detected in this deck.`
- `No native PowerPoint charts were detected in this deck.`

Do **not** present these as risks, failures, or missing assets by default.

---

## Failure handling

If extraction is partial or some assets fail to export:

- still write the bundle files that were successfully produced
- record failures explicitly in `asset_index.json` or metadata
- do **not** fabricate successful extraction
- do **not** skip bundle generation silently

If a deck is too complex for full extraction, produce the best available bundle and make the limitations explicit.