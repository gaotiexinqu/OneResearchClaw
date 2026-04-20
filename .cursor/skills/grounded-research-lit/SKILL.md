---
name: grounded-research-lit
description: Run focused literature and web research from a grounded note. Use when a grounded note already exists and you want targeted research results, opened-link evidence, deeper per-paper analysis materials, optional downloaded literature, and a two-stage literature output (`lit_initial.md` then refined `lit.md`).


---

# Grounded Research Literature

Use a structured grounded note to perform **targeted literature / web research**.

This skill is **not** a generic survey skill.
It is a **grounding-conditioned research stage**.

Its responsibilities are:

1. read a grounded note
2. adapt to the grounded note's schema
3. generate focused search queries
4. save them to a JSON file
5. run research using either:
   - external API backend, or
   - Cursor-native search / browse fallback
6. enforce link opening when required
7. preserve readable source material for opened literature items
8. build structured paper-level notes from opened source material
9. write an initial literature report (`lit_initial.md`) from opened-source evidence
10. optionally download opened research literature as an auxiliary artifact
11. refine paper notes from successfully downloaded PDFs
12. write the final refined literature report (`lit.md`) for downstream stages

---

## Pipeline Constants

Load constants from:

- `config/research_pipeline.env`

Use:

```bash
source config/research_pipeline.env
```

### Constants

| Variable                     | Values                         | Meaning                                                 |
| ---------------------------- | ------------------------------ | ------------------------------------------------------- |
| `SEARCH_BACKEND`             | `auto` / `external` / `cursor` | Select research backend                                 |
| `REQUIRE_OPEN_LINK`          | `true` / `false`               | Whether links must be opened and read                   |
| `DOWNLOAD_OPENED_LITERATURE` | `true` / `false`               | Whether opened research literature should be downloaded |
| `DOWNLOAD_DIR`               | path                           | Download root directory                                 |
| `OPEN_TOP_K`                 | integer ≥ 1                    | Minimum number of results to open per query             |
| `MIN_OPENED_PAPERS`       | integer ≥ 1                    | **(Cursor-native only)** Minimum number of opened papers required before writing `lit_initial.md`; value is controlled by `research_mode` via `config/research_pipeline.env` |
| `MIN_RECENT_PAPERS`          | integer ≥ 1                    | **(Cursor-native only)** Minimum number of recently-published opened papers required (within the last 2 years) |

### Backend selection rule

```text
if SEARCH_BACKEND == "external":
    use external API backend only
elif SEARCH_BACKEND == "cursor":
    use Cursor-native research only
else:  # auto
    if BIGMODEL_SEARCH_API_KEY exists:
        use external API backend
    else:
        use Cursor-native research
```

Important:

- **Cursor-native fallback is orchestration logic in this skill**
- **Do not try to call Cursor-native search through Python**
- `web_search_reader.py` is only for the external backend
- `prepare_opened_paper_notes.py` is used for both backends
- `download_opened_literature.py` is a local downloader / backfill helper
- `refine_notes_from_downloaded_pdfs.py` is the PDF refinement helper used after downloads complete

---

## When to Use

Use this skill when:

- a grounded note already exists
- you want focused literature / web follow-up
- you want search results with evidence quality
- you want a structured literature result rather than raw URLs

Do **not** use this skill when:

- the input is a raw transcript or raw document
- the upstream grounding stage has not yet been completed
- the goal is a final polished memo (use `grounded-summary` after this)
- the goal is a broad field survey unrelated to the grounded input

---

## Input

### How to get `ground_id`

Read `ground_id.txt` from the grounding bundle to get the stable pipeline identifier:

```
data/grounded_notes/<ground_id>/ground_id.txt
```

**Do NOT generate a new `ground_id`.** All downstream directories reuse the same `ground_id`.

### Grounded note input

Usually:

- `data/grounded_notes/<ground_id>/grounded.md`

### Optional input

- `queries_confirmed_path`: path to a user-confirmed queries JSON file (e.g., `data/lit_inputs/<ground_id>/queries_confirmed.json`). When provided, use the queries from this file directly instead of generating new ones.

This skill should adapt to the grounded note's actual schema rather than forcing one universal section layout.

### Primary query seed

When `queries_confirmed_path` is provided, use the queries from that file as the authoritative source — do not re-generate.

When `queries_confirmed_path` is NOT provided, fall back to:
- When `Search Keywords` is present in the grounded note, use it as the **primary query seed**.
- However, do **not** rely on keywords alone. Always interpret them together with the grounded note's topic, current findings, unresolved issues, risks, and suggested next steps.

### Schema-aware reading rules

Map the grounded note into research-relevant semantic slots.

#### Archive Grounding

- topic ← `Archive Overview`
- materials ← `Included Materials`
- processed_items ← `Successfully Processed Child Items`
- cross_material_signals ← `Key Signals Across Materials`
- failures ← `Skipped / Unsupported / Failed Items`
- next_steps ← `Suggested Next Steps`
- keywords ← `Search Keywords`

#### Document Grounding

- topic ← `Main Topic / Purpose`
- known_points ← `Main Points`
- conclusions ← `Key Findings / Claims`
- risks ← `Constraints / Risks`
- evidence ← `Important Non-Textual Elements`
- open_questions ← `Unresolved Issues`
- next_steps ← `Suggested Next Steps`
- keywords ← `Search Keywords`

#### Meeting Grounding

- topic ← `Meeting Topic`
- known_points ← `Main Discussion Points`
- conclusions ← `Key Conclusions`
- risks ← `Constraints / Risks`
- open_questions ← `Disagreements or Unresolved Issues`
- next_steps ← `Suggested Next Steps`
- keywords ← `Search Keywords`

#### PPTX Grounding

- topic ← `Main Topic / Purpose`
- structure ← `Deck Structure / Narrative Flow`
- known_points ← `Main Points`
- evidence ← `Important Evidence and Assets`
- notes_signals ← `Speaker Notes Signals`
- risks ← `Gaps / Risks / Ambiguities`
- next_steps ← `Suggested Next Steps`
- keywords ← `Search Keywords`

#### Table Grounding

- topic ← `Main Topic / Purpose`
- schema_signals ← `Main Fields`
- known_points ← `Key Signals`
- anomalies ← `Anomalies / Outliers`
- cautious_conclusions ← `Possible Supported Conclusions`
- risks ← `Risks / Data Quality Issues`
- next_checks ← `Suggested Next Checks`
- keywords ← `Search Keywords`

### Query-generation emphasis

Generate query groups with grounding-type-aware emphasis.

#### Problem / background queries

Use for:

- task/background understanding
- domain context
- benchmark/dataset context
- problem framing

#### Method / solution queries

Use for:

- methods
- baselines
- solution directions
- implementation ideas

#### Domain / constraint queries

Use for:

- risks
- constraints
- ambiguities
- unresolved issues
- failure modes
- data quality concerns

---

#### Required `queries.json` format

`queries.json` must use **plain string arrays** for each query group.

Preferred structure:

```json
{
  "ground_id": "<ground_id>",
  "problem_queries": [
    "query string 1",
    "query string 2"
  ],
  "method_queries": [
    "query string 1",
    "query string 2"
  ],
  "constraint_queries": [
    "query string 1",
    "query string 2"
  ]
}
```

Rules:

- keep `problem_queries`, `method_queries`, and `constraint_queries` as arrays of **strings only**
- do **not** wrap each query as an object
- do **not** include per-query fields such as `query`, `emphasis`, `keywords`, or `rationale`
- concise, directly searchable query strings are preferred over verbose natural-language instructions
- top-level metadata such as `ground_id` is allowed, but query entries themselves must remain plain strings

---

## Output Files

### Intermediate files

Under:

- `data/lit_inputs/<ground_id>/`

Write:

- `data/lit_inputs/<ground_id>/queries.json`
- `data/lit_inputs/<ground_id>/search_results.json`

### Opened source artifacts

If any literature item is successfully opened and readable, preserve source material under:

- `data/lit_inputs/<ground_id>/opened_sources/`

### Structured paper notes

After search/open, generate structured paper-note artifacts under:

- `data/lit_inputs/<ground_id>/opened_paper_notes.jsonl`
- `data/lit_inputs/<ground_id>/opened_paper_notes/`

These artifacts are **internal to this skill** and do not change downstream contracts.
They exist to make the literature report deeper, less snippet-driven, and more evidence-backed.

### Initial literature output (internal)

Under:

- `data/lit_inputs/<ground_id>/lit_initial.md`

This is an **internal research-stage intermediate artifact**.
It may be used to checkpoint the first pass based on opened-page evidence, but it must **not** be treated as the final output for downstream stages.

### Final literature output

Under:

- `data/lit_results/<ground_id>/lit.md`

This is the **final research-stage output** that downstream stages should consume.
It must be written only **after the PDF refinement pass completes or no eligible downloaded PDFs are available**.

### Optional downloads

If `DOWNLOAD_OPENED_LITERATURE=true`:

- downloaded files go to:
  - `data/lit_downloads/<ground_id>/`
- manifest file:
  - `data/lit_downloads/<ground_id>/manifest.json`

### Skill-local scripts

- `.cursor/skills/grounded-research-lit/scripts/web_search_reader.py`
- `.cursor/skills/grounded-research-lit/scripts/prepare_opened_paper_notes.py`
- `.cursor/skills/grounded-research-lit/scripts/download_opened_literature.py`
- `.cursor/skills/grounded-research-lit/scripts/refine_notes_from_downloaded_pdfs.py`

---

## Required behavior

When invoked, this skill must:

1. infer `ground_id` from the grounded note path if possible
2. read the grounded note
3. detect or infer the grounding type from the note structure
4. load constants from `config/research_pipeline.env`
5. load confirmed queries if `queries_confirmed_path` is provided; otherwise extract and generate:
   - main topic
   - open questions / unresolved issues
   - constraints / risks / ambiguities
   - likely method directions
   - search keywords
6. **if `queries_confirmed_path` is provided**: read queries from that file and copy them as `queries.json` — do NOT regenerate or ask the user again
7. **if `queries_confirmed_path` is NOT provided**: use `Search Keywords` as the primary query seed, generate query groups:
   - problem/background queries
   - method/solution queries
   - domain/constraint queries
   - write `queries.json` using plain string arrays for each query group; do not use per-query objects with fields such as `query`, `emphasis`, `keywords`, or `rationale`
8. run research:
   - external backend → use `web_search_reader.py`
   - Cursor-native backend → use Cursor-native research / browse
9. preserve opened readable sources under `opened_sources/`
10. generate `opened_paper_notes.jsonl` and per-paper note markdown files using `prepare_opened_paper_notes.py`
11. for backend=`cursor`, explicitly verify the opened-paper count using the exact opened-count verification rule before writing `data/lit_inputs/<ground_id>/lit_initial.md`
11.5. **Paper Opened Confirmation (Agent Inline Check)** — this step must be completed before writing `data/lit_inputs/<ground_id>/lit_initial.md`:

    - Iterate through each paper in `opened_paper_notes.jsonl` and verify, for each one:
      - whether a corresponding opened source file exists under `opened_sources/`
      - whether that source file contains sufficient readable content (≥ 500 chars of readable body = sufficient; < 100 chars = severely insufficient)
      - whether the paper note's analysis is substantive (not hollow, no obvious hallucination risk)
    - If a paper is found to be missing a source file or to have severely insufficient source content:
      - must re-search using the paper title
      - attempt to open a new readable page and save it to `opened_sources/`
      - regenerate the corresponding paper note
    - If a paper still cannot obtain sufficient source content after re-searching, it should be removed from the candidate list (not referenced in lit_initial.md)
    - **This confirmation is performed by the agent inline, without relying on external scripts**
    - after confirmation is complete, proceed to write `lit_initial.md`
12. write `data/lit_inputs/<ground_id>/lit_initial.md` from opened-page evidence and paper notes
13. if `DOWNLOAD_OPENED_LITERATURE=true`:

   - external backend: launch background/auxiliary download when possible
   - Cursor-native backend: run `download_opened_literature.py` after the opened-source artifacts and initial note artifacts exist
   - in both cases, treat download as an auxiliary stage **between** `data/lit_inputs/<ground_id>/lit_initial.md` and final `lit.md`

14. wait until the download manifest reaches a terminal state (`completed` or `no_eligible_items`) before finalizing the research stage
15. run `refine_notes_from_downloaded_pdfs.py` to enrich notes from successfully downloaded PDFs
16. write the final `lit.md` from the refined notes

### Backend-specific sufficiency rule

#### External API backend

- preserve the existing broader external search/open flow
- analyze as many successfully opened relevant literature items as the run actually obtains
- if downloads are enabled, download as many opened relevant literature items as are actually available
- do **not** impose a fixed minimum successful-download count on the external backend

#### Cursor-native backend

- before writing `data/lit_inputs/<ground_id>/lit_initial.md`, you must search and open **at least `MIN_OPENED_PAPERS` unique relevant literature items**
- `at least $MIN_OPENED_PAPERS opened items` is a **hard requirement**, not a best-effort suggestion
- do not treat snippet-only candidates as opened papers for this count
- the minimum-`$MIN_OPENED_PAPERS` rule must be enforced using the exact opened-count verification rule, not by rough browsing impressions alone
- if fewer than `$MIN_OPENED_PAPERS` unique relevant literature items satisfy the exact opened-count verification rule, the Cursor-native research stage is **not complete** and must continue searching / opening more items
- if `DOWNLOAD_OPENED_LITERATURE=true`, the Cursor-native backend must also successfully download **at least `MIN_OPENED_PAPERS` unique relevant literature items** before the research stage can be treated as complete, unless the run explicitly reports why this target could not be reached after continued search/open/download attempts
- the opened count is an **entry sufficiency** rule for writing, while the download count is a **completion sufficiency** rule when download is enabled
- recent-paper enforcement runs after the opened-count check: the agent must ensure at least `MIN_RECENT_PAPERS` papers published in the last 2 years have been opened before writing `lit_initial.md`; if insufficient, supplement searches with year-filtered queries must be performed

---

## Critical workflow rule: `data/lit_inputs/<ground_id>/lit_initial.md` first, `lit.md` last

The research stage must follow this post-search order:

1. obtain search results
2. open readable literature items
3. preserve opened readable source content
4. build structured paper notes from opened readable content
5. write `data/lit_inputs/<ground_id>/lit_initial.md` based primarily on those paper notes
6. run or complete literature download as an auxiliary stage
7. refine notes using downloaded PDFs when available
8. write the final `lit.md`

The goal is:

- **fast first-pass analysis** from opened readable sources
- **deeper final analysis** from downloaded PDFs when available
- **stable file-flow semantics** for downstream stages

`data/lit_inputs/<ground_id>/lit_initial.md` is internal to this research stage.
Downstream stages should consume only the final `lit.md`.

---

## Paper Opened Confirmation: Inline Check Before Writing `lit_initial.md`

Before writing `data/lit_inputs/<ground_id>/lit_initial.md`, the following confirmation process must be completed for all candidate papers. This step is executed by the agent inline, without relying on external scripts.

### Subject

Each paper in `opened_paper_notes.jsonl`.

### Verification Rules

For each paper, verify:

| Check | Logic | If Problem Found |
|-------|-------|-----------------|
| Source file exists | Corresponding file found under `opened_sources/` | Missing → re-search and open |
| Content sufficient | Readable body content ≥ 500 chars | Insufficient → re-search and open |
| Analysis substantive | Paper note is not hollow and has real content | Too thin → attempt to expand; if not possible, remove |
| Source-analysis alignment | Content referenced in the analysis can be traced back to the source file | Suspicious → re-search to confirm |

### Handling Flow

1. Read `opened_paper_notes.jsonl` to get the paper list
2. Check that each paper's `opened_source_path` exists under `opened_sources/`
3. Read each corresponding source file and measure readable body length
4. For any paper with issues:
   - Re-search using the paper title
   - Open a new readable page and save it to `opened_sources/`
   - Re-run `prepare_opened_paper_notes.py`
   - If still no sufficient source after re-searching, remove the paper from the candidate list
5. After all confirmations are complete, write `lit_initial.md`

### Judgment Standards

- **Sufficient**: readable body ≥ 500 chars, analysis ≥ 20 lines → ready to write
- **Thin**: readable content 100–500 chars, analysis < 20 lines → attempt to expand, or keep with noted limitations
- **Severely insufficient**: readable content < 100 chars, or no source file at all → must re-search; if irrecoverable, remove
- **Suspicious**: analysis content clearly misaligned with the source file → must re-search to confirm

> The purpose of this step is to eliminate hallucination risk before writing, not to fix it after writing.

---

## Cursor-native artifact production rule

When backend=`cursor`, do **not** treat browsing alone as research completion.
The Cursor-native branch must produce explicit local artifacts before the writing stage.

The required sequence is:

1. search and identify candidate literature items
2. continue opening and reading literature items until at least `$MIN_OPENED_PAPERS` unique relevant items satisfy the exact opened-count verification rule
3. for each successfully opened and readable literature item:
   - save one readable source file under `data/lit_inputs/<ground_id>/opened_sources/`
   - record the opened status in `search_results.json`
4. after opened-source preservation, run `prepare_opened_paper_notes.py`
5. confirm that:
   - `opened_paper_notes.jsonl` exists
   - `opened_paper_notes/` contains generated per-paper note files
6. explicitly verify that the opened-paper count is at least `$MIN_OPENED_PAPERS` using the exact opened-count verification rule

6.5 (Cursor-native only) recent papers enforcement:

    Load constant from `config/research_pipeline.env`:
      MIN_RECENT_PAPERS (value depends on `research_mode`)

    This check is always active for the Cursor-native backend.
    a. From all opened papers in `search_results.json` where:
           - opened == true
           - open_status == "success"
           - is_research_literature == true
         extract the publication year from:
           - the `publish_date` field, or
           - the opened source file content (look for a year in the visible
             metadata or near the title/abstract)
      b. Count papers with year >= (current_year - 1). In 2026, the cutoff is 2025.
      c. If count < MIN_RECENT_PAPERS:
           i.   Extract Search Keywords from the grounded note.
           ii.  Generate supplementary queries by appending year filters for
                the last 2 years to keywords:
                  e.g. "[keyword] 2025..2026"
                       "[keyword] 2025 site:arxiv.org"
                       "[keyword] 2026 site:arxiv.org"
           iii. Run WebSearch with these supplementary queries.
           iv.  Use WebFetch to open newly found papers.
           v.   Save each newly opened source under `opened_sources/`.
           vi.  Update `search_results.json` with new opened items
                (append to the existing queries array).
           vii. Re-run `prepare_opened_paper_notes.py`.
           viii.Re-verify: opened count >= `$MIN_OPENED_PAPERS` AND recent count >= MIN_RECENT_PAPERS.
                If still insufficient after supplement, apply the fallback
                policy below only after exhausting the escalation steps in
                section d.

      d. (Escalation — must be attempted before any fallback is taken)
         If supplement search in step c still leaves recent count < MIN_RECENT_PAPERS,
         the agent must escalate before falling back:

           - Broaden the keyword strategy: try shorter core terms, remove
             modifiers, try synonyms (e.g. from "long-context transformer"
             to "transformer", from "RAG" to "retrieval augmented generation")
           - Search arxiv's cs.* categories directly with year filters
           - Search Google Scholar with year filters if available
           - Try searching for "state of the art [keyword] 2025" and
             "latest research on [keyword]" as standalone queries
           - Try the arxiv cs.CV / cs.CL / cs.AI new submission pages
           - Record every escalation attempt in the run report:
               what was tried, how many results were found, how many
               were opened, why each attempt fell short

         After completing all escalation steps, re-count recent papers.
         Only if recent count is still < MIN_RECENT_PAPERS AND the agent can
         document a concrete reason why recent papers do not exist for this topic
         (e.g. the research area literally did not exist until this year),
         then the fallback in section e may be taken.

      e. (Strict fallback — only as last resort, requires explicit justification)
         Fallback means: the minimum is reduced to 1 recent paper if at least
         1 can be found; if even 1 cannot be found after all escalation steps,
         the research stage reports the complete absence of recent literature
         as a finding in the run report and proceeds.

         ⚠️ ANTI-GAMING RULE: The fallback is NOT a permission to skip the
         recent-paper requirement. It exists only for genuinely novel topics
         where research from the last 2 years is physically absent.
         The agent must NOT use fallback as a convenience escape hatch.
         Any fallback taken without documented escalation attempts in section d
         constitutes a skill violation.

         Before taking fallback, the agent must explicitly state in the run
         report:
           - Which escalation steps in section d were attempted
           - How many results each yielded
           - The concrete reason recent papers could not be found
           - Whether the fallback to 1 recent paper or zero-recent finding
             was taken, and why

7. only then write `data/lit_inputs/<ground_id>/lit_initial.md`
8. if downloads are enabled, run `download_opened_literature.py`
9. wait for the manifest terminal state
10. run `refine_notes_from_downloaded_pdfs.py`
11. only then finalize `lit.md`

### ⚠️ REQUIRED TOOLS FOR CURSOR-NATIVE BACKEND — READ CAREFULLY

When backend=`cursor`, you MUST use these tools for search and open:

#### ✅ USE THESE TOOLS:
- **`WebSearch`** — Use this tool to search for literature. Provide a targeted `search_term` and an `explanation` of what you're looking for.
- **`WebFetch`** — Use this tool to fetch and read individual paper/abstract pages from URLs returned by WebSearch.

#### ❌ DO NOT USE:
- **MCP browser tools** (`ListMcpResources`, `FetchMcpResource`, `browser_*` tools) — these are for different purposes, NOT for literature research
- **Python search scripts** (`web_search_reader.py`) — these are for the external API backend only, not Cursor-native
- **`CallMcpTool`** for browser/IDE-related operations during research

#### Required workflow with WebSearch + WebFetch:
1. For each query in `queries.json`, call **`WebSearch`** with the query string
2. From the search results, identify relevant papers (arxiv, conference papers, etc.)
3. For each promising result, call **`WebFetch`** to read the paper page
4. Save the fetched content as markdown files under `data/lit_inputs/<ground_id>/opened_sources/`
5. Create `data/lit_inputs/<ground_id>/search_results.json` recording each item's opened status
6. After all opens, run `prepare_opened_paper_notes.py`

#### ⚠️ CRITICAL REMINDER:
The skill file says "Cursor-native fallback is orchestration logic in this skill" and "Do not try to call Cursor-native search through Python". This means you must use the WebSearch and WebFetch tools directly — there is NO Python script that does the searching for you in Cursor-native mode.

---

### Exact opened-count verification rule for Cursor-native backend

For backend=`cursor`, the minimum opened-paper requirement must be verified explicitly from local artifacts before `data/lit_inputs/<ground_id>/lit_initial.md` is written.

A literature item counts toward the required opened count only if all of the following are true:

- `is_research_literature == true`
- `opened == true`
- `open_status == "success"`
- `opened_source_path` is present in `search_results.json`
- the file referenced by `opened_source_path` actually exists on disk under `data/lit_inputs/<ground_id>/opened_sources/`

The following do **not** count as opened papers for the minimum-`$MIN_OPENED_PAPERS` rule:

- snippet-only candidates
- items with `opened=false`
- items whose `open_status` is not `success`
- items missing `opened_source_path`
- items whose `opened_source_path` is recorded but the file does not actually exist on disk

For backend=`cursor`, `data/lit_inputs/<ground_id>/lit_initial.md` must **not** be written until the explicitly verified opened count is at least `$MIN_OPENED_PAPERS`.

### Required opened-source preservation details for Cursor-native backend

For each successfully opened and readable literature item in the Cursor-native backend, save one markdown file under:

- `data/lit_inputs/<ground_id>/opened_sources/`

Each saved opened-source file should include, when available:

- title
- source URL
- access date
- venue / year / author metadata visible on the page
- readable abstract / summary text
- readable body text or the most informative page-level content actually available

The corresponding item in `search_results.json` should record, when available:

- `title`
- `url`
- `opened`
- `open_status`
- `opened_source_path`
- `is_research_literature`

### Required local script execution for Cursor-native backend

After `search_results.json` and `opened_sources/` are populated, run:

```bash
python .cursor/skills/grounded-research-lit/scripts/prepare_opened_paper_notes.py \
  --search-results data/lit_inputs/<ground_id>/search_results.json \
  --output data/lit_inputs/<ground_id>/opened_paper_notes.jsonl \
  --notes-dir data/lit_inputs/<ground_id>/opened_paper_notes
```

If `DOWNLOAD_OPENED_LITERATURE=true`, then run:

```bash
python .cursor/skills/grounded-research-lit/scripts/download_opened_literature.py \
  --search-results data/lit_inputs/<ground_id>/search_results.json \
  --output-dir data/lit_downloads/<ground_id> \
  --ground-id <ground_id> \
  --manifest-path data/lit_downloads/<ground_id>/manifest.json \
  --wait \
  --wait-timeout-sec 1800
```

> ⚠️ `--ground-id` is **required**. `--manifest-path` is optional (defaults to `{output-dir}/manifest.json`) but **must** be provided when also using `--wait` so that the wait loop checks the correct file. `--wait` makes the script poll for a terminal-valid manifest state: `status=completed` OR `status=no_eligible_items` with `downloaded_count>0`. A manifest with `status=no_eligible_items` and `downloaded_count=0` means the download failed before producing results (e.g. `_iter_items` returned 0 items) — the script will keep polling and timeout rather than treat the broken state as terminal.

After the download stage reaches a terminal manifest state, run:

```bash
python .cursor/skills/grounded-research-lit/scripts/refine_notes_from_downloaded_pdfs.py \
  --search-results data/lit_inputs/<ground_id>/search_results.json \
  --notes-path data/lit_inputs/<ground_id>/opened_paper_notes.jsonl \
  --notes-dir data/lit_inputs/<ground_id>/opened_paper_notes \
  --manifest-path data/lit_downloads/<ground_id>/manifest.json \
  --wait \
  --wait-timeout-sec 1800
```

> ⚠️ Argument names differ from the old `--notes-jsonl / --downloads-dir / --output-jsonl` names. Use `--notes-path`, `--notes-dir`, `--manifest-path` exactly as shown. `--wait` makes refine poll the manifest until it reaches a terminal-valid state before reading it, avoiding the case where refine runs before download has finished. The poll loop also correctly ignores `no_eligible_items` manifests with `downloaded_count=0` — it keeps waiting for the next download attempt.

Failure to produce these artifacts means the Cursor-native research stage is incomplete.

---

## Critical writing rule: `lit.md` must be paper-note-driven

Neither `data/lit_inputs/<ground_id>/lit_initial.md` nor `lit.md` may be driven mainly by snippets.

They must use, in order of priority:

1. `opened_paper_notes.jsonl`
2. files under `opened_paper_notes/`
3. files under `opened_sources/`
4. only then search snippets for candidates that could not be opened

After PDF refinement, the final `lit.md` should prefer:

1. refined note fields derived from downloaded PDFs
2. original opened-page note fields for papers without downloaded PDFs
3. snippet-only candidates as a separate last section

### Required `data/lit_inputs/<ground_id>/lit_initial.md` structure

```md
# Literature Research Results (Initial)

## Research Focus

## Overall Literature Synthesis

## Detailed Analysis of Opened Papers

## Snippet-Level / Not-Fully-Opened Candidates

## Initial Takeaways for the Current Grounded Topic
```

### Required final `lit.md` structure

```md
# Literature Research Results

## Research Focus

## Overall Literature Synthesis

## Detailed Analysis of Opened Papers

## Newly Strengthened / Newly Added Papers from Downloaded PDFs

## Snippet-Level / Not-Fully-Opened Candidates

## Takeaways for the Current Grounded Topic
```

If no downloaded PDFs were successfully refined, the final `lit.md` may omit the dedicated “Newly Strengthened / Newly Added Papers from Downloaded PDFs” heading, but it must still reflect the completed refinement pass.

### Rules for "Detailed Analysis of Opened Papers"

For each opened paper, do **not** stop at a short abstract-like summary.
Core papers should be written as compact literature mini-reviews, not QA-style checklists.

For the main opened-paper body, prefer:

#### Problem and Task Setting

#### Methodology and Why It Works

#### Main Evidence and What the Results Actually Support

#### Relevance to the Current Grounded Topic, Borrowable Ideas, and Limits

For core papers, methodology is not optional background. It should be one of the main bodies of the analysis.
Do not reduce the method section to a one-sentence idea summary. When the source is rich enough, explain the main pipeline/stages, key modules, training signal or loss, inference flow, and why the design should help.

At minimum, the opened-paper analysis should, when the source is rich enough, include:

- a concrete task setting / benchmark / dataset description
- a concrete description of the method pipeline or key mechanism
- concrete training / optimization details when available
- one to three concrete empirical findings or numbers
- one explicit comparison against a baseline or prior work when available
- one explicit limitation or unproven point
- one explicit statement of what is borrowable for the current grounded topic
- one explicit statement of what is not directly transferable or not directly proven
- at least **two concrete evidence snippets / details** drawn from the opened or refined source material when available

Avoid generic claims such as `strong`, `effective`, `promising`, `important`, `significant`, or `useful` unless they are immediately grounded in setup details, method details, quantitative evidence, or explicit comparisons.
If the source does not expose enough information to support these fields, say so explicitly instead of fabricating details.

### Section depth and topicality requirements

Neither `data/lit_inputs/<ground_id>/lit_initial.md` nor the final `lit.md` may collapse into a thin recap.
Every major section must be substantial, topic-aware, and evidence-backed.

#### `## Research Focus`

This section must clearly state:

- the current grounded topic
- the concrete research questions being investigated
- the scope boundaries of the current search
- what kinds of evidence were prioritized

Do not leave this as one vague sentence.

#### `## Overall Literature Synthesis`

This section must be a real synthesis, not a list of disconnected paper names.
It should explain:

- what the literature broadly agrees on
- where the main solution families differ
- which ideas look most relevant to the grounded topic
- where evidence is weak, mixed, or still missing

Prefer multiple substantial paragraphs over a few bullets when enough material exists.

#### `## Detailed Analysis of Opened Papers`

This is the core body of the literature report and must be the longest section when enough opened material exists.
Do not compress it into brief abstract-like summaries.
For each core opened paper, provide a deep standalone formal paper analysis grounded in the actual opened or refined evidence.
Do not rely on generic filler prose or reuse the same abstract template across many papers. Each subsection should reflect the paper's actual task setting, method design, evidence pattern, and limits.

#### `## Newly Strengthened / Newly Added Papers from Downloaded PDFs`

When downloaded PDFs added real value, explain exactly what became clearer after PDF access, such as:

- method details that were missing from the opened page
- experiment details or numbers that became available
- stronger evidence for or against transfer to the current topic
- important caveats discovered only after reading the PDF

Do not make this section a placeholder heading with one generic sentence.

This section must also provide explicit coverage for successfully downloaded and parsable PDFs that are not already fully covered in `## Detailed Analysis of Opened Papers`.
Each such paper must appear as its own standalone subsection. Do **not** merge multiple downloaded papers into one mixed paragraph, one grouped bullet list, or one shallow recap block.

For each such paper, write a medium-to-deep formal paper analysis that includes:

- Problem and Task Setting
- Methodology
- Main Evidence with at least 2 concrete details or quantitative findings when available
- Relevance to the current grounded topic
- at least one limitation, caveat, or transfer boundary when the PDF exposes enough evidence

Coverage is mandatory, but coverage must not be satisfied with generic placeholder language such as "the paper addresses...", "methods exist for...", or "the work improves..." unless concrete extracted details immediately follow.
The goal is not a short note. The goal is a real standalone paper analysis, even when it is somewhat shorter than the analysis for the most central papers.

#### `## Snippet-Level / Not-Fully-Opened Candidates`

This section should stay clearly separated from the opened-paper body.
Still, it must be useful: explain why each candidate matters, what can and cannot be inferred from the snippet alone, and what uncertainty remains.

#### `## Initial Takeaways for the Current Grounded Topic` / `## Takeaways for the Current Grounded Topic`

These takeaways must connect the literature back to the grounded topic in a concrete way.
They should state:

- what appears most borrowable
- what still needs validation
- what looks risky or unsupported
- what decisions the current research stage can already support
- what remains blocked by evidence gaps

Do not end with generic statements such as “more work is needed” without specifying what kind of work and why.


### Rules for refinement from downloaded PDFs

The refinement pass should:

- **strengthen** papers already analyzed in `data/lit_inputs/<ground_id>/lit_initial.md` when their PDFs were downloaded successfully
- **add** papers that were downloaded successfully but were not sufficiently represented in the initial literature report
- preserve earlier opened-page evidence when no PDF was available or parsable

Do **not** discard usable opened-page analyses just because some PDFs were unavailable.
The refinement stage is additive and corrective, not destructive.

After PDF extraction completes, you must enumerate every paper in `data/lit_downloads/<ground_id>/manifest.json` with `downloaded=true`. For each successfully downloaded and parsable PDF, the final `lit.md` must contain an explicit corresponding analysis entry, either by:

- strengthening an already-covered paper inside `## Detailed Analysis of Opened Papers`, or
- adding a new standalone paper analysis inside `## Newly Strengthened / Newly Added Papers from Downloaded PDFs`

A downloaded PDF may be excluded from explicit final-report coverage only when the PDF text could not be parsed into usable content. In that case, the failure should be reported explicitly rather than silently dropping the paper.

Do not satisfy this coverage rule with short memo-style notes, grouped summaries, or shallow filler prose. Every covered downloaded PDF should read like a real paper analysis with concrete task, method, evidence, relevance, and limits.

When available, use `data/lit_inputs/<ground_id>/refine_coverage.json` from `refine_notes_from_downloaded_pdfs.py` as the checklist of downloaded papers that still require explicit final `lit.md` coverage.

### Rules for snippet-only candidates

Candidates that were not fully opened must be placed under:

- `## Snippet-Level / Not-Fully-Opened Candidates`

Do **not** mix snippet-only candidates into the main opened-paper analysis section.

---

## Backend-specific requirements

### External API backend

- preserve the existing query → search → open logic
- if a relevant literature item can be opened and read, analyze it even if download is still pending
- when `DOWNLOAD_OPENED_LITERATURE=true`, prefer background/auxiliary download rather than blocking the first-pass writing path
- analyze as many successfully opened relevant literature items as the run actually obtains
- download as many opened relevant literature items as are actually available and downloadable
- after download completion, run the PDF refinement pass before finalizing `lit.md`
- do **not** impose a fixed minimum successful-download count on the external backend

### Cursor-native backend

- preserve existing Cursor-native search/browse logic, but make it artifact-producing rather than browse-only
- before writing `data/lit_inputs/<ground_id>/lit_initial.md`, you must search, open, and read **at least `MIN_OPENED_PAPERS` unique relevant literature items**
- `at least $MIN_OPENED_PAPERS opened items` is a **hard requirement**, not a best-effort suggestion
- do not treat snippet-only candidates as opened papers for this count
- if fewer than `$MIN_OPENED_PAPERS` unique relevant literature items have been opened, the Cursor-native research stage is **not complete** and must continue searching / opening more items
- for every successfully opened and readable literature item, save a local opened-source file under `opened_sources/` and record the corresponding metadata/path in `search_results.json`
- after opened-source preservation, run `prepare_opened_paper_notes.py` so the writing stage uses structured paper notes rather than snippets alone
- if `DOWNLOAD_OPENED_LITERATURE=true`, run `download_opened_literature.py` after the opened-source artifacts and initial note artifacts exist
- if `DOWNLOAD_OPENED_LITERATURE=true`, the Cursor-native backend must successfully download **at least `MIN_OPENED_PAPERS` unique relevant literature items** before the run can be treated as complete, unless it explicitly reports why this target could not be reached after continued search/open/download attempts
- do not finalize `lit.md` until the refinement pass is complete

---

## Completion checklist

A run is not complete unless all of the following are true:

- `queries.json` exists
- `search_results.json` exists
- `opened_sources/` exists and contains saved opened-source files when readable pages were opened
- `opened_paper_notes.jsonl` exists when readable pages were opened
- `opened_paper_notes/` exists and contains generated per-paper note files when readable pages were opened
- for the Cursor-native backend, **at least `MIN_OPENED_PAPERS` unique relevant literature items were actually searched/opened/read** before `data/lit_inputs/<ground_id>/lit_initial.md` was written
- for the Cursor-native backend, `prepare_opened_paper_notes.py` actually ran after opened-source preservation
- for the Cursor-native backend, the exact opened-count verification rule was explicitly applied before `data/lit_inputs/<ground_id>/lit_initial.md` was written
- for the Cursor-native backend, the explicitly verified opened count was at least `$MIN_OPENED_PAPERS` before `data/lit_inputs/<ground_id>/lit_initial.md` was written
- for the Cursor-native backend, the recent-paper count was verified before writing `lit_initial.md`; if the minimum was not met after supplement, the agent completed all escalation steps in section d before any fallback was taken, and the fallback decision is documented in the run report with explicit justification
- `data/lit_inputs/<ground_id>/lit_initial.md` exists
- Paper opened confirmation was completed via the inline check; no problematic papers remained before `lit_initial.md` was written
- if `DOWNLOAD_OPENED_LITERATURE=true`, `manifest.json` exists and is in a terminal state (`completed` or `no_eligible_items`)
- if backend=`cursor` and `DOWNLOAD_OPENED_LITERATURE=true`, **at least `MIN_OPENED_PAPERS` unique relevant literature items were successfully downloaded**, or the run explicitly reports why this target could not be reached after continued search/open/download attempts
- the PDF refinement pass has run
- if `DOWNLOAD_OPENED_LITERATURE=true`, every successfully downloaded and parsable PDF from `manifest.json` has a corresponding explicit strengthened or newly added analysis entry in final `lit.md`
- final `lit.md` exists
- final `lit.md` contains:
  - a paper-note-driven opened-paper analysis section
  - a `## Newly Strengthened / Newly Added Papers from Downloaded PDFs` section that covers all successfully downloaded and parsable PDFs not already fully covered in the opened-paper section
  - a separate snippet-only candidate section
  - substantial, topic-aware, evidence-backed analysis rather than a thin recap

---

## Reporting expectations

At the end of a run, report concisely but concretely:

1. which backend was actually used
2. whether opened-link reading was enforced
3. how many literature items were searched
4. how many unique relevant literature items were actually opened and read
5. whether opened readable sources were preserved
6. whether structured paper notes were generated
7. whether literature download was triggered
8. for backend=`cursor` with downloads enabled, whether the successful-download target of `MIN_OPENED_PAPERS` was satisfied; if not, explain why not
9. for backend=`cursor`, how many recent papers were found (within the last 2 years), whether supplement and escalation searches were triggered, whether the MIN_RECENT_PAPERS target was reached; if not, which escalation steps from section d were attempted, how many results each yielded, and whether a fallback was taken with explicit documented justification
10. whether PDF refinement was completed
11. which files were written
12. the weakest point of the current research-stage output