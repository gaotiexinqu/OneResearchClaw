---
name: report-export
description: Export a final reviewed research report into one or more requested output formats. This skill is the unified output-layer renderer for the pipeline.


---

# Report Export

This skill is the **unified output-layer export skill**.

It reads a final reviewed research report and renders it into one or more requested output formats.

This skill is the output-layer renderer for the pipeline:

grounding
-> grounded-research-lit
-> grounded-summary
-> grounded-review
-> report-export

---

## Purpose

Use this skill to export a final reviewed report from:

- `data/reports/<ground_id>/research_report.md`

into one or more requested formats, currently:

- `md`
- `docx`
- `pdf`
- `pptx`
- `audio`

The output should be written under:

- `data/final_outputs/<ground_id>/...`

---

## What this skill does

This skill:

1. reads the final reviewed report
2. infers `<ground_id>` from the input path
3. exports the report into the requested format(s)
4. writes outputs into a dedicated `<ground_id>` output folder

---

## What this skill does not do

This skill must **not**:

- run new research
- revise the research conclusions
- add new evidence
- rewrite the report as a different argument
- act as a substitute for grounded-review

It may perform only the minimum transformation needed for the requested output format, such as:

- markdown normalization
- document formatting
- PDF rendering via the DOCX export path
- light speech-oriented normalization for audio rendering

---

## Inputs

### How to get `ground_id`

Infer `ground_id` from the parent directory of the input report:

```
data/reports/<ground_id>/research_report.md
```

The `<ground_id>` is embedded in the input path — no need to read `ground_id.txt`.

The main input is:

- `data/reports/<ground_id>/research_report.md`

The skill assumes this file is already the final reviewed report.

Do **not** go back to:

- `grounded.md`
- `lit.md`
- `summary.md`

unless the user explicitly asks for a re-review or re-synthesis task.

### `output_lang`

The language for the exported report. Controls the language of all output format files (DOCX, PDF, PPTX, etc.).

Expected values:
- `en` — English (default)
- `zh` — Chinese (Simplified)

If omitted, defaults to `en`.

When `output_lang` is `zh`, the Agent performing the export task must first translate the English report into Chinese, then export the translated content into the requested format(s). The translation is done by the Agent directly — no API call or translation script is required. Preserve all markdown structure (headings, tables, code fences, links, formatting) during translation.

The `audio` format is always narrated in English regardless of `output_lang`.

---

## Outputs

Write outputs under:

- `data/final_outputs/<ground_id>/`

### Supported format outputs

#### Markdown

- `data/final_outputs/<ground_id>/md/report.md`

#### DOCX

- `data/final_outputs/<ground_id>/docx/report.docx`

#### PDF

- `data/final_outputs/<ground_id>/pdf/report.pdf`

#### PPTX

- `data/final_outputs/<ground_id>/pptx/report.pptx`

#### Audio

- `data/final_outputs/<ground_id>/audio/report.wav`

---

## Supported formats (current version)

This skill currently supports:

- `md`
- `docx`
- `pdf`
- `pptx`
- `audio`

If the user requests an unsupported format, report it clearly instead of guessing.

Examples of unsupported formats for the current version include:

- `html`
- `json`
- `chartpack`

---

## Invocation pattern

Use the existing script entrypoint:

```bash
bash .cursor/skills/report-export/scripts/run.sh <input_report_path> <output_root> <format_or_comma_separated_formats> [output_lang]
```

**⚠️ Important path rules:**
- `<output_root>` should be the parent directory, **NOT** including `ground_id`
- The script automatically infers `ground_id` from the input report's parent directory
- Output is always written to `<output_root>/<ground_id>/<output_lang>/...` where `<output_lang>` is the 4th argument (default: `en`)
- **Do NOT** pass `<output_root>/<ground_id>` or `<output_root>/<ground_id>/<lang>` as the output_root

Examples:

```bash
# Correct: output_root is data/final_outputs (no ground_id, no lang)
bash .cursor/skills/report-export/scripts/run.sh \
  data/reports/video-20260309195735/research_report.md \
  data/final_outputs \
  md
# Output: data/final_outputs/video-20260309195735/en/report.md

# Export Chinese version (output_lang=zh)
bash .cursor/skills/report-export/scripts/run.sh \
  data/reports/video-20260309195735/research_report.md \
  data/final_outputs \
  docx,pdf \
  zh
# Output: data/final_outputs/video-20260309195735/zh/report.docx, report.pdf

# Export multiple formats with English (default)
bash .cursor/skills/report-export/scripts/run.sh \
  data/reports/video-20260309195735/research_report.md \
  data/final_outputs \
  md,docx,pdf,pptx,audio
# Output: data/final_outputs/video-20260309195735/en/{report.md,report.docx,report.pdf,...}
```

---

## Required Workflow

1. **Font check (CJK languages):** Before exporting with `output_lang=zh`, verify that CJK fonts are available by running `fc-list :lang=zh`. If no CJK fonts are found, install them first:
   ```bash
   sudo apt-get update && sudo apt-get install -y fonts-noto-cjk fonts-wqy-zenhei
   sudo fc-cache -fv
   ```
   The export scripts will also attempt auto-install, but checking upfront avoids mid-export failures.
2. Read the final report input path.
3. Infer `<ground_id>` from the parent directory of the input report.
4. Determine the requested export format(s).
5. Run the export script.
6. Write outputs into `data/final_outputs/<ground_id>/<lang>/...` where `<lang>` is the `output_lang` parameter (default: `en`).
7. Verify that the requested file(s) were actually written.
8. Do not stop at analysis; complete the export.
9. **Metadata stripping:** Ensure pipeline production metadata (`---` horizontal-rule separators and `*本报告通过...*` footnotes) is stripped from all exported formats. This is handled automatically by `export_docx.py`, `export_pdf.py`, and the updated `export_md.py`.

---

## Important content rule

All exported formats must preserve the underlying research content.

That means:

- `md`, `docx`, `pdf`, and `pptx` should remain substantively aligned
- `audio` may apply light speech-oriented rendering normalization
- formatting may change
- layout may change
- the report content must not be materially rewritten

Do **not**:

- add or remove major claims
- introduce new risks or conclusions
- omit core evidence-bearing sections
- compress the report into a shorter abstract unless the user explicitly asks for that

For `audio`, acceptable normalization includes:

- stripping markdown syntax that reads poorly aloud
- flattening bullet markers into spoken sentences
- simplifying markdown tables into readable line text
- splitting long sections into smaller speech chunks for stable TTS synthesis

For `audio`, unacceptable behavior includes:

- summarizing the report into a shorter spoken version
- changing the argument structure
- replacing uncertainty wording with stronger claims
- dropping core evidence-bearing sections for brevity

---

## Format-specific guidance

### Markdown export

Markdown export should:

- preserve headings
- preserve bullet lists
- preserve tables when possible
- normalize line endings and spacing lightly

### DOCX export

DOCX export should:

- preserve heading hierarchy
- preserve bullet structure
- preserve readable paragraph spacing
- preserve basic tables when present
- produce a clean, editable document

### PDF export

PDF export should:

- be generated from the report content without altering meaning
- prioritize stable readability
- preserve section structure
- be written as a real PDF file, not a placeholder
- **automatically detect and install missing CJK fonts** (e.g. `fonts-noto-cjk`) when `output_lang=zh` is requested
- **strip pipeline production metadata** (e.g. footnotes like `*本报告通过接地评审...` and horizontal rule separators `---`) from the output file — do not include them in the exported document

### PPTX export

PPTX export should:

- render the reviewed report into a presentation file
- preserve the report's major structure and meaning
- prioritize slide readability over literal markdown structure
- avoid introducing new claims or evidence

### Audio export

Audio export should:

- read only the final reviewed report
- render a spoken version from the same report content
- output a real audio file at `audio/report.wav`
- preserve meaning while allowing light speech-oriented normalization
- use chunked synthesis rather than one giant end-to-end call for long reports

The current recommended backend is Kokoro TTS.

**Font dependencies are automatically handled.** The export scripts (`export_pdf.py`) will automatically check for CJK fonts and attempt to install them if missing. However, for reliable operation in new environments, ensure these packages are pre-installed:

```bash
# Required for PDF/DOCX export with CJK (Chinese/Japanese/Korean) text
sudo apt-get update
sudo apt-get install -y fonts-noto-cjk fonts-wqy-zenhei

pip install "python-docx>=1.0.0"
```

If fonts are missing and auto-install fails, the export will raise an error with instructions. Run the install command above and retry.

Common environment variables for audio export:

- `REPORT_EXPORT_AUDIO_LANG_CODE` (default: `a`)
- `REPORT_EXPORT_AUDIO_VOICE` (default: `af_heart`)
- `REPORT_EXPORT_AUDIO_SPEED` (default: `1.0`)
- `REPORT_EXPORT_AUDIO_MAX_CHARS` (default: `1200`)

The default values are aligned with a basic English narration path. Non-English use should provide a compatible language code, optional language-specific dependency, and a compatible voice name.

---

## Completion Criteria

This task is complete only if:

1. the input report was actually read
2. the requested export format(s) were actually processed
3. the output file(s) were written under `data/final_outputs/<ground_id>/...`
4. the output file(s) exist on disk
5. the exported content remains aligned with the final reviewed report