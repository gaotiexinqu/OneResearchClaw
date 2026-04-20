---
name: grounded-summary
description: Create a rich, evidence-preserving research report draft from a grounded note and its follow-up literature result. This is the main report-writing stage of the middle pipeline, not a compression memo.




---

# Grounded Summary

This skill produces a **substantial, evidence-rich research report draft** from:

1. a grounded note, and
2. a follow-up literature result.

It is **not** limited to meeting notes. It applies to any upstream grounded note produced by the grounding family, including:

- meeting-grounding
- document-grounding
- pptx-grounding
- table-grounding
- archive-grounding

The output of this skill is the **main report draft** for the current grounded item.

Write the result to:

- `data/report_inputs/<ground_id>/summary.md`

This file is called `summary.md` for pipeline compatibility, but it should **not** behave like a short summary memo. It should behave like a **full internal research report draft** that preserves the important depth of both the grounded note and `lit.md`.

---

## When to Use

Use this skill when:

- a grounded note already exists
- a literature result already exists
- you want to turn those materials into a substantial report draft
- you want the literature analysis to be integrated into the report body rather than reduced to a few bullets

Do **not** use this skill when:

- the grounded note has not been written yet
- the literature result has not been written yet
- you only want the raw literature result without report writing
- you only want final rendering/export to pdf/docx/slides/audio

---

## Inputs

### How to get `ground_id`

Read `ground_id.txt` from the grounding bundle to get the stable pipeline identifier:

```
data/grounded_notes/<ground_id>/ground_id.txt
```

**Do NOT generate a new `ground_id`.** All downstream directories reuse the same `ground_id`.

This skill assumes the following inputs already exist:

1. `data/grounded_notes/<ground_id>/grounded.md`
2. `data/lit_results/<ground_id>/lit.md`

Optional supporting input:

3. `data/lit_inputs/<ground_id>/search_results.json`

### Pipeline Language Strategy

This skill is a **mid-pipeline** stage. Its output (`summary.md`) is always written in **English only**, regardless of the `output_lang` parameter.

The `output_lang` parameter is handled exclusively by the export layer (`report-export`) and has **no effect on this skill**. When `output_lang` is set to `zh`, the English `summary.md` is translated into Chinese only at the final export step.

Do not apply language translation within this skill. If the source grounded note or literature result contains content in another language, summarize that content into English as part of the report draft.

### Important input rule

The grounded note may come from different grounding skills and may use different section names.

Read the actual grounded note schema as written.

Do **not** force all grounded notes into one fake unified schema.

Instead, interpret the grounded note through its own sections and extract the following semantic slots where possible:

- the main topic / purpose
- the main points or discussion points
- key findings / claims / conclusions
- risks / constraints / ambiguities
- unresolved issues / disagreements / open questions
- suggested next steps
- search keywords

### Schema-aware reading guidance

Typical mappings include:

#### Meeting Grounding

- topic -> `Meeting Topic`
- main points -> `Main Discussion Points`
- conclusions -> `Key Conclusions`
- risks -> `Constraints / Risks`
- open issues -> `Disagreements or Unresolved Issues`
- next steps -> `Suggested Next Steps`
- keywords -> `Search Keywords`

#### Document Grounding

- topic -> `Main Topic / Purpose`
- main points -> `Main Points`
- findings -> `Key Findings / Claims`
- risks -> `Constraints / Risks`
- evidence -> `Important Non-Textual Elements`
- open issues -> `Unresolved Issues`
- next steps -> `Suggested Next Steps`
- keywords -> `Search Keywords`

#### PPTX Grounding

- topic -> `Main Topic / Purpose`
- structure -> `Deck Structure / Narrative Flow`
- main points -> `Main Points`
- evidence -> `Important Evidence and Assets`
- notes -> `Speaker Notes Signals`
- risks -> `Gaps / Risks / Ambiguities`
- next steps -> `Suggested Next Steps`
- keywords -> `Search Keywords`

#### Table Grounding

- topic -> `Main Topic / Purpose`
- fields -> `Main Fields`
- signals -> `Key Signals`
- anomalies -> `Anomalies / Outliers`
- conclusions -> `Possible Supported Conclusions`
- risks -> `Risks / Data Quality Issues`
- next checks -> `Suggested Next Checks`
- keywords -> `Search Keywords`

#### Archive Grounding

- topic -> `Archive Overview`
- materials -> `Included Materials`
- processed items -> `Successfully Processed Child Items`
- cross-material signals -> `Key Signals Across Materials`
- failures -> `Skipped / Unsupported / Failed Items`
- next steps -> `Suggested Next Steps`
- keywords -> `Search Keywords`

---

## Output

Write exactly one file:

- `data/report_inputs/<ground_id>/summary.md`

### Output role

Although the filename is `summary.md`, this file is the **primary report draft** for the current grounded item.

It should be:

- rich enough that a reader can understand the project without opening `lit.md`
- detailed enough that important literature analysis is still present in the report body
- structured enough that `grounded-review` only needs to refine and verify it, not rewrite it from scratch

It should **not** be:

- a thin memo
- a bullet-only recap
- a compressed executive abstract
- a search log
- a placeholder draft waiting for the “real” report to be written later

---

## Two-Phase Execution Model

Section 4.1 and Section 4.2 must be produced in **two strictly ordered phases**, not in a single interleaved pass. Skipping or collapsing this order is the primary cause of literature depth loss in the summary stage.

### Phase 1 — Literal Copy (Section 4.1)

**This phase must complete before any writing for Section 4.2 begins.**

1. Read `data/lit_results/<ground_id>/lit.md`
2. Locate the `## Detailed Analysis of Opened Papers` section
3. Locate the `## Newly Strengthened / Newly Added Papers from Downloaded PDFs` section (if present)
4. **Copy the full body of each section verbatim into Section 4.1** under the corresponding sub-headings
5. Do not paraphrase, condense, merge, or rewrite during this phase

Section 4.1 is a **literal carry-over zone, not a writing zone**. The only allowed action is copying.

### Phase 1 Verification Step — MANDATORY

After copying, **verify** that the following conditions are all true before proceeding:

| Check | How to verify |
|-------|---------------|
| All opened papers are present | Count paper entries in `lit.md` `## Detailed Analysis of Opened Papers` vs Section 4.1. They must match. |
| PDF-refined papers are present | Count entries in `lit.md` `## Newly Strengthened / Newly Added Papers from Downloaded PDFs` vs Section 4.1. They must match. |
| Paper body was not compressed | For each paper, compare the word count of the `lit.md` paper body vs the Section 4.1 paper body. Section 4.1 should be >= 90% of `lit.md` word count per paper. |
| Subsection structure preserved | Check that each paper retains its `Problem and Task Setting`, `Methodology`, `Main Evidence`, `Relevance`, `Limits` (or equivalent) structure. |
| Wording preserved | The paper body content should be identical to `lit.md`, not paraphrased. |

If any check fails, **go back and fix Section 4.1 before proceeding to Phase 2**.

### Phase 2 — Thematic Synthesis (Sections 1, 2, 3, 4.2, 5, 6, 7, 8)

After Phase 1 verification passes, write all remaining sections. This is where analysis, synthesis, and judgment happen. Phase 2 should reference the Phase 1 material but should not modify it.

---

## Writing Goal

Write a **substantial research report draft** that organizes and preserves the depth of both inputs.

The goal is **not** to compress the grounded note and `lit.md` into a small number of bullets.

The goal is to produce a report that lets a reader answer:

- What is the real problem or task setting?
- What is already established from the grounded input?
- What deep analysis does the literature provide for the most relevant questions?
- Which parts of the literature directly support the current project, and which parts only partially or directionally support it?
- What remains unresolved after combining grounded evidence and literature evidence?
- What should be done next, and why?

---

## Critical Writing Rules

### 1. Do not treat this as a compression step

This skill is **not** a “compress everything into a short memo” stage.

If `lit.md` contains meaningful deep analysis, that depth must be carried into the report draft.

Do **not** replace multi-paragraph analysis with one-line bullets just because it is called `summary.md`.

### 2. The literature belongs in the report body

The most relevant literature analysis must appear in the **main body** of the report.

Do **not** push the literature into:

- a tiny “search supports” section
- a trailing appendix-like note
- a few generic bullets with no mechanism or limitation detail

The report body should contain **substantive literature-grounded discussion**.

### 3. Organize primarily by questions, themes, or design issues — but preserve explicit paper-level deep analysis when it matters

The report as a whole should **not** collapse into a paper-by-paper list such as:

- Paper A says ...
- Paper B says ...
- Paper C says ...

Instead, the report should primarily be organized around:

- research questions
- method components
- design choices
- engineering tensions
- evaluation concerns
- evidence gaps

However, this rule does **not** mean that important paper-level deep analysis should be flattened away.

If `lit.md` already contains substantial paper-level analyses that materially support the project, the report must preserve them explicitly inside Section **4.1 Preserved Detailed Paper Analyses** rather than reducing them to theme-only synthesis.

Use thematic organization for the report-level logic, but keep explicit paper-level deep analysis where that is the best way to preserve mechanism, evidence, and limitation detail.

### 4. Preserve mechanism, evidence, and limitation — not just conclusions

When a literature item matters, preserve the parts that make it useful, such as:

- the core mechanism or method idea
- the relevant setting or experimental condition
- the main finding
- the support boundary
- the limitation or mismatch to the current project
- the concrete implication for the current project

Do **not** keep only the paper’s headline conclusion.

### 5. Preserve evidence-strength distinctions

Use wording such as:

- strongly supported
- directly supported in a similar setting
- partially supported
- directionally supported
- conceptually relevant but not directly validated here
- limited evidence
- unresolved by current evidence

Do **not** upgrade:

- analogous precedent
- conceptual support
- partial similarity
- general intuition

into direct proof.

### 6. Preserve real uncertainty and disagreement

If the grounded note or `lit.md` reveals disagreement, ambiguity, missing evidence, or unresolved design trade-offs, preserve them clearly.

Do **not** make the report sound more settled than the evidence supports.

### 7. Do not summarize the search process itself

Do **not** report search execution statistics in the main report body, such as:

- number of queries
- number of hits
- number of opened links
- number of downloaded papers
- coverage diagnostics
- manifest-style file inventories

These belong to research QA or logs, not to the report body.

### 8. Prefer paragraphs for substantive analysis

Use bullets only where bullets are naturally better, such as:

- concise findings inventories
- action items
- risk lists

For the main analysis sections, prefer **full paragraphs and thematic subsections**.

### 9. Do not optimize for shortness

There is **no reward for making the report shorter**.

If the inputs are rich, the report should also be rich.

Avoid arbitrary brevity targets.

### 10. Preserve high-value specifics

If the grounded note or `lit.md` includes any of the following, keep them when they materially affect understanding:

- important quantitative facts
- concrete failure modes
- architecture splits
- competing design branches
- data or evaluation caveats
- specific mechanism-level insights
- explicit trade-offs
- conflicts between literature and current assumptions

### 11. Section 4.1 copy is a mandatory execution phase, not a writing preference

The Phase 1 literal copy of `lit.md` paper analysis bodies into Section 4.1 is a **mandatory execution step**, not a writing guideline. See the **Two-Phase Execution Model** section above for the required procedure and the mandatory verification step. Rule #1 through #10 above do not apply to Phase 1 content — they apply only to Sections 1, 2, 3, 4.2, 5, 6, 7, and 8.

---

## Required Output Structure

Write the report draft with the following structure.

# Research Report Draft

## 1. Executive Overview

Write **2–4 substantial paragraphs**.

This section should include:

- the core problem or task setting
- the current state of understanding
- the most important grounded findings
- the most important literature-backed insights
- the main unresolved bottleneck or decision point
- why the issue matters for the current project

### Requirement

This section should be concise relative to the full report, but still specific.

Do not reduce it to a tiny abstract.

---

## 2. Problem Setting and Source Context

Write **2–5 substantial paragraphs**.

This section should explain:

- what the grounded source material is about
- what project, task, or problem is currently being discussed
- what constraints, goals, stakes, or context are already known from the grounded note
- what the current system state or decision context is

When useful, include:

- relevant source-specific structure
- major discussion branches
- setup assumptions
- important non-textual evidence from the grounded note

### Requirement

This section should make the report understandable even to a reader who has not opened `grounded.md`.

---

## 3. Grounded Findings from the Source Material

Write **3–8 focused subsections or paragraphs**, depending on the material.

This section should preserve the most important information coming directly from `grounded.md`, such as:

- concrete observations
- current hypotheses
- design branches
- current conclusions
- constraints and risks
- anomalies or disagreements
- implementation or evaluation concerns

### Requirement

This section should preserve the source-side substance rather than restating the topic in generic terms.

Do not flatten grounded findings into vague project summaries.

---

## 4. Literature-Based Deep Analysis

This is the **main body** of the report.

It should contain **two complementary layers**:

### 4.1 Preserved Detailed Paper Analyses

**See the Two-Phase Execution Model section above for the mandatory Phase 1 copy procedure and verification step.**

This subsection is where the Phase 1 literal copy result is placed. The full bodies of `## Detailed Analysis of Opened Papers` and `## Newly Strengthened / Newly Added Papers from Downloaded PDFs` from `lit.md` must appear here verbatim — not paraphrased, not condensed, not selectively trimmed.

### 4.2 Integrated Thematic Assessment

Phase 2 synthesis. Write **3–6 substantial thematic subsections** that organize the literature around a **question, mechanism, design issue, or evidence theme**. This synthesis should reference and build upon the Phase 1 paper analyses — it should not modify or compress them.

Examples of valid subsection styles:

- support for a proposed supervision strategy
- evidence for a decomposition or stage design
- evidence for a specific architecture split
- lessons about reward design, data curation, retrieval, or evaluation
- where related methods succeed or fail
- transfer limits from similar but non-identical settings

For each thematic subsection, include most of the following when applicable:

1. **Why this theme matters** for the current project
2. **What the literature says**, with enough detail to preserve mechanism and evidence
3. **How strong the support is** for the current project
4. **What does not transfer cleanly** or remains mismatched
5. **What the practical implication is** for the current project

### Requirement

Do **not** collapse Section 4 into generic bullets or a thin thematic recap.

Section 4.1 must preserve the **full standalone paper-analysis body** from `lit.md` with aligned paper-level coverage and approximately aligned paper count.
Section 4.2 must synthesize that preserved literature body into project-level thematic judgment.

If `lit.md` contains rich downloaded-PDF refinements or explicit paper-level analyses, the corresponding value must still be visible in this section rather than being flattened into generic conclusions.

---

## 5. Integrated Assessment for the Current Project

Write **2–5 substantial paragraphs**.

This section should combine the grounded findings and literature analysis to answer questions like:

- which directions currently look most justified
- which assumptions are only weakly supported
- which branches deserve further testing
- which claims should be treated cautiously
- what the current evidence does and does not allow you to conclude

### Requirement

This section should not merely repeat Sections 3 and 4.

It should synthesize them into a project-level judgment.

---

## 6. Unresolved Questions and Decision-Critical Gaps

Write **4–8 items**, each as a substantial bullet or short paragraph.

Each item should state:

- the unresolved question or gap
- why it matters
- what evidence is currently missing or inconclusive
- what kind of experiment, analysis, or check would reduce the uncertainty

### Requirement

Do not write generic “future work” bullets.

These should be real decision-critical uncertainties.

---

## 7. Recommended Next Steps

Write **4–7 concrete actions**.

Each action should:

- follow directly from the report body
- be specific enough to execute
- reflect real leverage for the project
- avoid invented owners, deadlines, or commitments

Good action types include:

- targeted ablations
- controlled comparisons
- direct replications of a literature mechanism
- evaluation redesigns
- deeper reads of a narrow high-value literature cluster
- data checks or error analysis

### Requirement

Explain **why** each action matters, not just what to do.

---

## 8. Key Risks, Caveats, and Evidence Boundaries

Write **4–8 items**.

This section should include risks such as:

- methodological risks
- evidence-transfer risks
- evaluation risks
- data-quality risks
- overfitting or generalization risks
- mismatch between literature settings and the current project setting
- hidden assumptions in the current plan

### Requirement

Phrase weak support as an evidence risk about the method or plan, not as a complaint about search execution.

---

## Writing Strength Requirement

The report draft should read like:

- a serious internal research report
- a report that can already stand on its own
- a draft that preserves real analysis depth
- a document strong enough that review should mainly refine it rather than rewrite it

It should **not** read like:

- a raw search log
- a manifest of downloaded papers
- a chat reply
- a short memo pretending to be a report
- a bullet-only recap of a much richer literature result

---

## Completion Criteria

This task is complete only if:

1. the grounded note was actually read
2. the literature result was actually read
3. a substantial report draft was written to:
   - `data/report_inputs/<ground_id>/summary.md`
4. the report follows the required section structure above
5. the report preserves relevant deep literature analysis in the main body
6. the report does not drift into search-process recap or manifest listing
7. the report is clearly richer and more informative than a compressed memo