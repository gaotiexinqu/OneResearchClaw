---
name: table-grounding
description: Convert an xlsx or csv table into a structured table-grounding bundle for downstream research and summary.


---

# Table Grounding

Convert a table file into a structured **table-grounding bundle**.

This skill is for **table grounding**, not a polished final report.
It should produce a stable intermediate bundle that is easy for downstream skills and agents to use.

## When to Use

Use this skill when:

- the input is a `.xlsx` or `.csv` file
- the file mainly contains tabular data
- you need a structured grounding note before downstream follow-up work
- you want schema, preview rows, summary statistics, and simple charts before writing conclusions

Do not use this skill when:

- the input is a PDF, DOCX, Markdown, or plain text document
- the goal is a polished final report
- the input is not primarily tabular

## Input

A single table file:

- `.xlsx`
- `.csv`

For `.xlsx`, the default behavior is to use the first sheet.
If a specific sheet is provided, use that sheet instead.
Do not silently merge multiple sheets in the first version.

The table may contain:

- numeric columns
- categorical columns
- date/time columns
- missing values
- duplicated rows
- messy column names
- mixed types
- derived or computed columns

## Output Bundle

Write outputs under:

`data/grounded_notes/<type>-<table_id>/`

If a specific xlsx sheet is selected, the bundle directory may include a sheet suffix.

Examples:

- `data/grounded_notes/xlsx-sales_q1/`
- `data/grounded_notes/xlsx-sales_q1-sheet-Summary/`
- `data/grounded_notes/csv-benchmark_results/`

The bundle should contain:

```text
<bundle_dir>/
├─ extracted.md
├─ extracted_meta.json
├─ schema.json
├─ summary_stats.json
├─ asset_index.json
└─ assets/
   ├─ previews/
   │  ├─ head.csv
   │  ├─ sampled_rows.csv
   │  └─ column_summary.md
   └─ charts/
      ├─ chart_001.png
      ├─ chart_002.png
      └─ ...
```

Important:

- The script stage must **not** generate a placeholder `grounded.md`.
- The agent must read the bundle and then write a real `grounded.md`.

## Required Workflow

When using this skill, you must follow this workflow:

1. First run the existing script entrypoint:

   ```bash
   bash .cursor/skills/table-grounding/scripts/run.sh <input_path> <output_root> [sheet_selector]
   ```

2. Do **not** manually reimplement schema extraction, summary statistics, preview generation, or chart generation if the existing script can already do it.

3. After the bundle is generated, read:

   - `extracted.md`
   - `extracted_meta.json`
   - `schema.json`
   - `summary_stats.json`
   - `asset_index.json`
   - `assets/previews/*`
   - `assets/charts/*`

4. Then write a real `grounded.md` into the same bundle directory.

5. The task is **not complete** if only the bundle files exist but `grounded.md` has not been written.

6. The task is also **not complete** if `grounded.md` is written without first generating and using the bundle evidence.

## Grounded Output

After the bundle is generated, write `grounded.md` in the same bundle directory.

Return markdown with **exactly** these sections:

```markdown
# Table Grounding

## 1. Main Topic / Purpose
[2–4 sentence statement of what this table or dataset appears to describe.]

## 2. Main Fields
- [One bullet per major field or field group]

## 3. Key Signals
- [Important trends, contrasts, distributions, or clusters strongly supported by the table]

## 4. Anomalies / Outliers
- [Only clearly unusual values, missing patterns, inconsistent rows, sharp jumps, duplicates, or suspicious records]

## 5. Possible Supported Conclusions
- [Only cautious conclusions supported by the data]
- [Do not turn correlation into causality]

## 6. Risks / Data Quality Issues
- [Missing values, sparse columns, duplicated rows, unclear schema, inconsistent units, tiny sample size, etc.]

## 7. Suggested Next Checks
- [Concrete next-step analyses or validation directions grounded in the table]

## 8. Search Keywords

### Problem Keywords
- ...

### Method / Solution Keywords
- ...

### Domain / Constraint Keywords
- ...
```

## Instructions

- Do **not** write a polished final report.
- Do **not** invent business context, causal claims, owners, deadlines, or metadata not supported by the table.
- Do **not** turn weak correlations into strong conclusions.
- Do **not** ignore missing values, duplicates, or unclear schema.
- You must reuse the existing `scripts/run.sh` and `scripts/ground_table.py` workflow directly.
- Do not replace the existing extraction / statistics / chart pipeline with ad hoc analysis unless a minimal necessary fix is required.
- The script stage is the required evidence-building stage.
- `grounded.md` must be based on the generated bundle rather than on direct free-form inspection alone.
- Use the generated bundle as evidence:
  - `extracted.md`
  - `extracted_meta.json`
  - `schema.json`
  - `summary_stats.json`
  - `asset_index.json`
  - `assets/previews/*`
  - `assets/charts/*`
- If `AssetRef` blocks appear in `extracted.md`, inspect those referenced assets before writing `grounded.md`.
- Keep the output concise and structured.

## Special Rules

### Key Signals

Only include signals strongly supported by the data or auto-generated previews / charts.
Do not overstate weak patterns.

### Anomalies / Outliers

Only include anomalies that are clearly visible in the table, statistics, or charts.

### Possible Supported Conclusions

Use cautious wording.
Prefer:

- suggests
- is consistent with
- may indicate
- appears associated with

Avoid:

- proves
- establishes causality
- confirms

unless the evidence is unusually strong.

### Risks / Data Quality Issues

Only include issues that belong to the **table or dataset itself**, such as:

- missing values
- sparse columns
- duplicated rows
- unclear schema
- inconsistent units
- tiny sample size
- unusually wide or fragmented schema
- strong evidence of data incompleteness

Do **not** put routine pipeline or execution notes here by default.

Examples that should **not** automatically appear under `Risks / Data Quality Issues`:

- no charts were generated
- numeric/date parsing was imperfect
- a column type may have been misclassified by the current pipeline
- a preview or chart was not especially informative

Only mention a pipeline / execution issue in `grounded.md` if it **materially limits interpretation** of a specific conclusion.
If needed, mention it briefly under `Suggested Next Checks` rather than treating it as a data-quality defect.

### Suggested Next Checks

Only include follow-up checks grounded in the current table, such as:

- validate missing data
- inspect a suspicious subgroup
- compare another sheet or source
- verify units or schema
- run a more specific downstream search
- re-check a conclusion if current parsing or chart generation materially limited interpretation

### Search Keywords

Use specific noun phrases that are useful for later search.
Avoid generic terms such as:

- table
- spreadsheet
- data
- results
- analysis
- issue

## Example Invocation

`/.cursor/skills/table-grounding`