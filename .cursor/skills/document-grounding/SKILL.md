---
name: document-grounding
description: Convert a raw document into a structured grounding note for downstream research and summarization.


---

# Document Grounding

Convert a raw document into a structured grounding note.

This skill is for **document grounding**, not a narrative recap.
It should produce a stable intermediate note that is easy to read and easy for downstream skills to use.

## When to Use

Use this skill when:

- the input is a single document file
- the document may be a PDF, DOCX, Markdown, or TXT file
- you need structured document notes before downstream research or summary work
- the document may contain non-textual evidence such as tables, figures, diagrams, formulas, or code blocks

Do not use this skill when:

- the task is to write a polished final report
- the task is to perform external literature search
- the task is to render output into PDF/DOCX
- the input is a meeting transcript and you want meeting-specific grounding

## Input

A single document file.

Supported first-stage formats:

- `.pdf`
- `.docx`
- `.md`
- `.txt`

The document may contain:

- plain text
- section headings
- tables
- figures / diagrams
- formulas
- code blocks
- captions
- layout / reading-order challenges

## Output Bundle

For each input document, create one bundle directory:

```text
data/grounded_notes/<type>-<doc_id>_<timestamp>/
```

where `<type>` is the file extension (e.g. `pdf`, `docx`, `md`, `txt`), `<doc_id>` is the sanitized filename without extension, and `<timestamp>` is the Beijing-time execution timestamp (format: `YYYYMMDDHHMMSS`).

For example:

```text
data/grounded_notes/pdf-paper_name_20260410153022/
data/grounded_notes/docx-notes_001_20260410153100/
data/grounded_notes/md-project_readme_20260410153215/
```

Inside that bundle, the expected outputs are:

```text
<bundle_dir>/
├─ ground_id.txt       # Ground ID for this unit (reused by all downstream stages)
├─ extracted.md
├─ extracted_meta.json
├─ asset_index.json
├─ grounded.md
└─ assets/
   ├─ tables/
   ├─ figures/
   └─ formulas/
```

The `<ground_id>` (e.g. `pdf-paper_name_20260410153022`) is the single stable identifier for the entire pipeline — all downstream directories (`lit_inputs`, `lit_results`, `report_inputs`, `review_outputs`, `reports`, `final_outputs`) reuse this same `<ground_id>`.

### Important separation of responsibilities

- `ground_document.py` is responsible for building the extraction bundle:
  - `extracted.md`
  - `extracted_meta.json`
  - `asset_index.json`
  - `assets/...`
- The **agent** is responsible for reading those outputs and then writing the final:
  - `grounded.md`

`grounded.md` must be a real grounding note.
It must **not** remain a placeholder scaffold.

## Required Agent Workflow

1. Run the extraction script through the existing `run.sh` entrypoint.
2. Read:
   - `extracted.md`
   - `extracted_meta.json`
   - `asset_index.json`
3. If `extracted.md` contains `AssetRef` blocks, inspect the referenced files in `assets/...` before writing `grounded.md`.
4. Write `grounded.md` as a real structured grounding note.
5. Do not stop after merely confirming that the extraction bundle exists.

## AssetRef Rule

`extracted.md` may contain blocks such as:

```markdown
[AssetRef]
type: figure
id: figure_001
path: assets/figures/figure_001.png
instruction: Inspect this asset before writing grounded.md if it is relevant to the document's claims, comparisons, or conclusions.
[/AssetRef]
```

and

```markdown
[AssetRef]
type: table
id: table_001
path_md: assets/tables/table_001.md
path_csv: assets/tables/table_001.csv
instruction: Inspect this table before writing grounded.md if it contains key evidence, comparisons, or numerical results.
[/AssetRef]
```

These are not decorative markers.
They indicate that important evidence may exist outside the plain extracted text.
If an `AssetRef` appears relevant, the agent must inspect the referenced asset before final grounding.

## Output Format

Return markdown with **exactly** these sections.

```markdown
# Document Grounding

## 1. Main Topic / Purpose
[2–4 sentence statement of the document’s main topic and purpose.]

## 2. Main Points
- [One bullet per major sub-topic, contribution, or argument]

## 3. Key Findings / Claims
- [Only items explicitly stated or strongly supported by the document]

## 4. Constraints / Risks
- [Only constraints, limitations, caveats, or risks explicitly stated or strongly supported by the document]

## 4a. Important Non-Textual Elements
- [Key tables, figures, diagrams, formulas, or code blocks that materially affect interpretation]
- [Mention how they affect the reading of the document if relevant]

## 5. Unresolved Issues
- [Preserve uncertainty, unanswered questions, incomplete evidence, or limitations that remain open]

## 6. Suggested Next Steps
- [Concrete follow-up directions grounded in the document]
- [Do not invent owners, deadlines, or commitments]

## 7. Search Keywords

### Problem Keywords
- ...

### Method / Solution Keywords
- ...

### Domain / Constraint Keywords
- ...
```

## Instructions

- Do **not** write a chronological recap of the document.
- Do **not** invent facts, conclusions, owners, deadlines, or commitments.
- Do **not** turn suggestions, hypotheses, or future work into established conclusions.
- Do **not** add external knowledge, acronym expansions, years, benchmark details, or metadata not explicitly stated or strongly evidenced in the document.
- Remove low-signal boilerplate when it does not affect meaning.
- Group related content into high-level sub-topics instead of page-by-page bullets.
- Keep the output concise and structured.
- Treat non-textual evidence as first-class evidence when relevant.

## Special Rules

### Key Findings / Claims

Only include something here if it is explicitly stated or strongly supported by the document.
If it is merely hinted, proposed, or speculative, do not present it as a confirmed finding.

### Constraints / Risks

Only include constraints, limitations, or risks that are explicitly stated or strongly evidenced.
Do not infer hidden constraints from weak hints.

### Important Non-Textual Elements

Only mention tables, figures, formulas, diagrams, or code blocks that materially affect interpretation.
Do not list every asset mechanically.
If an asset was referenced in `extracted.md` through an `AssetRef` block and it appears relevant, inspect it before deciding whether to include it.

### Suggested Next Steps

Only include follow-up actions or directions that are explicitly discussed or strongly implied by the document.
Do not invent action owners, deadlines, or commitments.

### Search Keywords

Use specific noun phrases that are useful for later search.
Avoid generic terms such as:

- project
- document
- update
- issue
- optimization
- system

## Handling Difficult Cases

- If the document is repetitive, summarize repeated points once.
- If the document is incomplete, paraphrase only when meaning is clear.
- If sections conflict, keep the conflict under unresolved issues.
- If the main topic is genuinely unclear, write: `Unclear — multiple loosely related topics appear in the document.`
- For long documents, identify major section shifts first, then synthesize.
- If non-textual assets are present but unclear, mention them cautiously rather than over-claiming their meaning.

## Execution Rule

The task is **not complete** if `grounded.md` is missing, empty, or still contains placeholder scaffold text.
The agent must overwrite or newly create `grounded.md` with a real grounding note based on:

- `extracted.md`
- `extracted_meta.json`
- `asset_index.json`
- any relevant files referenced from `assets/...`

## Example Invocation

`/document-grounding`

## Environment Variables

When running the extraction script, ensure the Docling model path is set:

```bash
export DOCLING_ARTIFACTS_PATH="${PROJECT_ROOT}/models/docling"
```

Supported model path locations (checked in order):
- `${PROJECT_ROOT}/models/docling`
- `${PROJECT_ROOT}/models/docling-project/docling-models`
- `/root/.cache/docling/models`