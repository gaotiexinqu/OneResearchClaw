---
name: grounded-review
description: Review a research report draft with a structured scoring rubric, run a bounded repair loop when needed, and produce the final deliverable report.



---

# Grounded Review

This skill performs the **quality-gating and repair stage** of the middle layer.

It reads:

1. the grounded note,
2. the literature result,
3. the report draft,
4. optional supporting research artifacts,

and produces:

- a **review diagnosis and score report**
- a **review state file**
- a **final deliverable research report**

This skill is **not** a broad search skill and **not** an output rendering skill.
It sits between:

- `grounded-summary`
- and the final output-formatting/rendering stage

---

## Position in the pipeline

The intended pipeline is:

grounding
-> grounded-research-lit
-> grounded-summary
-> grounded-review
-> output rendering

This means:

- `grounded-summary` writes the **main report draft**
- `grounded-review` scores, diagnoses, repairs, re-checks, and finalizes that draft
- output skills then present that final report as pdf / docx / md / slides / audio / charts / fancy formats

`grounded-review` should therefore behave like a **quality gate with bounded repair**, not like a second compression stage.

---

## Purpose

The purpose of this skill is to turn a **substantial report draft** into a **final deliverable research report** through:

1. structured evaluation,
2. weakness diagnosis,
3. bounded repair,
4. re-evaluation,
5. finalization.

It should:

- preserve the core structure and substance of the report draft
- improve evidence alignment
- catch overclaiming
- restore missing important technical details if the draft still lost them
- improve section balance and readability
- strengthen explicit linkage between grounded findings and literature evidence
- remove search-process noise from the report body
- make the report suitable for downstream output-format skills
- act as a **quality gate**, not just a surface editor

It should **not**:

- perform an unrestricted new literature search
- invent new claims not grounded in the existing inputs
- radically change the research direction
- rewrite a rich report into a shorter but thinner version
- act as a presentation-formatting skill
- run an unbounded self-improvement loop

---

## When to Use

Use this skill when:

- `grounded.md` already exists
- `lit.md` already exists
- `summary.md` already exists
- you want a final deliverable research report for the current grounded item

Do **not** use this skill when:

- the report draft has not been written yet
- the literature result has not been written yet
- you only want a quick synthesis draft rather than a final report
- you only want formatting or export to pdf/docx/slides/audio

---

## Inputs

### How to get `ground_id`

Read `ground_id.txt` from the grounding bundle to get the stable pipeline identifier:

```
data/grounded_notes/<ground_id>/ground_id.txt
```

**Do NOT generate a new `ground_id`.** All downstream directories reuse the same `ground_id`.

This skill assumes the following files already exist:

1. `data/grounded_notes/<ground_id>/grounded.md`
2. `data/lit_results/<ground_id>/lit.md`
3. `data/report_inputs/<ground_id>/summary.md`

Optional but strongly recommended supporting inputs:

4. `data/lit_inputs/<ground_id>/opened_paper_notes.jsonl`
5. `data/lit_inputs/<ground_id>/search_results.json`
6. `data/lit_downloads/<ground_id>/manifest.json`
7. `data/lit_inputs/<ground_id>/refine_coverage.json`
8. `data/lit_inputs/<ground_id>/lit_initial.md`

### Input reading rule

At minimum, `grounded.md`, `lit.md`, and `summary.md` must be read.

Do **not** review the report draft in isolation.

The grounded note and literature result must be used as the source of truth for:

- evidence support
- scope
- uncertainty
- open questions
- next-step recommendations
- technical detail recovery when the draft is still too thin

When available, use `opened_paper_notes.jsonl`, `manifest.json`, and `refine_coverage.json` to validate:

- downloaded-paper coverage
- paper-level evidence sufficiency
- whether the draft has become thinner than the research-stage output

The report draft should be treated as:

- the main draft to be reviewed
- the default structural base to preserve
- not as unquestionable truth

---

## Outputs

The review stage uses a **round-based archival directory structure** to preserve full review history for later comparison.

### Directory Structure

```
data/review_outputs/<ground_id>/
├── round_0/
│   ├── review_report.md      # Round 0 review diagnosis
│   └── review_state.json     # Round 0 state snapshot
├── round_1/
│   ├── review_report.md       # Round 1 review diagnosis
│   └── review_state.json     # Round 1 state snapshot
├── round_2/                  # (optional, if loop runs to round 2)
│   ├── review_report.md
│   └── review_state.json
├── round_3/                  # (optional, if loop runs to round 3)
│   ├── review_report.md
│   └── review_state.json
├── round_4/                  # (optional, if loop runs to round 4)
│   ├── review_report.md
│   └── review_state.json
├── round_5/                  # (optional, if loop runs to round 5)
│   ├── review_report.md
│   └── review_state.json
├── review_history.json       # Summary of all rounds (canonical reference)
├── review_report.md          # Symlink to latest round (for backward compatibility)
└── review_state.json        # Symlink to latest round (for backward compatibility)

data/reports/<ground_id>/
└── research_report.md       # Current final report (updated after each repair round)
```

### Required Per-Round Outputs

For each review round, write these files to `data/review_outputs/<ground_id>/round_<N>/`:

1. `review_report.md` — human-readable review diagnosis (per-round)
2. `review_state.json` — machine-readable state snapshot (per-round)

### Required Final Outputs

After the loop completes, update these files in `data/review_outputs/<ground_id>/`:

3. `review_history.json` — summary of all rounds (canonical reference for downstream skills)
4. `review_report.md` — symlink/copy of the latest round's report
5. `review_state.json` — symlink/copy of the latest round's state

And finalize the report in:

6. `data/reports/<ground_id>/research_report.md` — the final deliverable report

Optional supporting file if genuinely useful:

- `data/reports/<ground_id>/review_notes.md`

If `review_notes.md` is not necessary, do not create it.

### Output roles

#### `review_report.md`

A human-readable review diagnosis containing:

- rubric scores
- pass/fail judgement
- specific weaknesses
- repair priorities
- what changed across rounds

This file should be **persisted by the parent/main agent**.
If the reviewer subagent is read-only, the reviewer may return a structured diagnosis payload in chat, and the parent agent must write that payload into `review_report.md`.

#### `review_state.json`

A machine-readable state file containing at least:

- `ground_id`
- `round`
- `scores`
- `weighted_total`
- `verdict`
- `needs_repair`
- `repair_actions`
- `passed`
- `used_reviewer_role`
- `used_writer_role`
- `reviewer_agent_path`
- `writer_agent_path`
- `reviewer_model_hint`
- `writer_model_hint`
- `reviewer_independence`
- `final_report_path`

This file should also be **persisted by the parent/main agent**.
A read-only reviewer may populate its contents indirectly by returning structured review results to the parent agent.

#### `research_report.md`

The **final deliverable research report** for the current grounded item.
This is the version that downstream output-format skills should use.

---

## Reviewer Role and Independence

The review stage should be performed by a **dedicated reviewer role / subagent** when available.

Preferred behavior:

- writer role produces the draft
- reviewer role scores and diagnoses the draft
- writer role performs bounded repairs
- reviewer role re-checks the repaired draft

When your environment supports reviewer subagents with their own model configuration, prefer a reviewer model that is **different from the writer model**.

If a separate reviewer model is **not** available, the review stage may still run with the same base model, but it must explicitly record in `review_state.json` that reviewer independence is limited.

Do **not** let the same role simply "declare success" without rubric-based justification.

## Execution Flow

The review stage must execute through a **bounded loop with dedicated reviewer and writer subagents**, not as a single monolithic pass in the parent context.

### Required execution pattern

For every review task, the parent agent must follow this loop. The reviewer is either the external API (if `reviewer_api_config` is present) or the local reviewer subagent (if not present). The writer is **always** the local writer subagent via `Task` tool.

1. **Call reviewer** (Round 0):
   - If `reviewer_api_config` present: call `call_ext_api.py` via Shell → external API
   - If not present: launch reviewer subagent via `Task` tool
2. **Parent agent archives the previous round** (if round > 0: copy current `round_n` → `round_{n-1}/`)
3. **Parent agent persists** `review_report.md` and `review_state.json` to `round_<N>/` directory
4. **If verdict is `repair`** and round < 5: launch writer subagent via `Task` tool to apply repairs, then go to step 6
5. **If verdict is `pass`**: launch writer subagent via `Task` tool to apply reviewer's suggested quality improvements (light repair), then skip to step 9
6. **Call reviewer again** (Round N+1) — same method as step 1:
   - If external mode: call `call_ext_api.py`
   - If local mode: launch reviewer subagent via `Task` tool
7. **Parent agent archives the previous round** → copy current `round_n` → `round_{n-1}/`
8. **Parent agent persists** the new round's `review_report.md` and `review_state.json` to `round_<N>/`
9. **Repeat steps 4–8** for at most **5 repair rounds** (pass verdicts jump from step 5 to finalize)
10. **After reviewer passes** (or loop exhausted): writer applies light repair → update `review_history.json`, symlinks, and finalize `research_report.md`

### External Reviewer Mode

When `reviewer_api_config` is provided in the invocation, the review stage uses the external LLM API as the reviewer for **all rounds** of the bounded loop (Round 0, Round 1, ..., Round N). The external reviewer is **not** a one-shot first-round tool — it is the primary reviewer throughout. The same external API is called at each round after each writer repair, until the report passes or the loop is exhausted.

#### When to Use

Use external reviewer mode when:
- You want to use a specific external model for review (e.g., a cheaper or more capable model)
- You need to integrate with existing API infrastructure
- You want more control over the reviewer's model parameters

#### Execution Pattern

When external reviewer config is available, it is used for **every review round** throughout the bounded loop:

```
┌─────────────────────────────────────────────────────────────────────┐
│               External Reviewer — All Rounds Loop                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Round 0:                                                            │
│  1. Parent Agent receives reviewer_api_config                        │
│  2. Parent Agent reads: grounded.md, lit.md, summary.md             │
│  3. Parent Agent constructs system + user prompts                   │
│  4. Parent Agent calls call_ext_api.py via Shell (Round 0)          │
│  5. Parse JSON → persist round_0/review_report.md + review_state.json│
│  6. If verdict=pass: launch writer for light repair → finalize      │
│  7. If verdict=repair: launch writer for repair → continue           │
│                                                                     │
│  Round N (N >= 1):                                                  │
│  8. Parent Agent reads: revised research_report.md + round_N-1/     │
│  9. Parent Agent constructs prompts with Round N-1 context          │
│  10. Parent Agent calls call_ext_api.py via Shell (Round N)         │
│  11. Parse JSON → persist round_N/review_report.md + review_state.json│
│  12. If verdict=pass: launch writer for light repair → finalize      │
│  13. If verdict=repair and N < 5: launch writer → continue           │
│  14. If verdict=repair and N >= 5: loop exhausted → finalize        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Key invariant:** whenever `reviewer_api_config` is present, the parent agent **must** use `call_ext_api.py` for every review round — not just Round 0. Switching to the local reviewer subagent mid-loop violates the external reviewer contract.

#### External Reviewer API Script

Use the standalone Python script `call_ext_api.py` for direct API calls.

**Script location:** `.cursor/skills/grounded-review/external-reviewer/call_ext_api.py`

**Usage:**

```bash
python .cursor/skills/grounded-review/external-reviewer/call_ext_api.py \
  --provider openai \
  --model gpt-4o-mini \
  --api-key "sk-xxx" \
  --base-url "https://api.example.com/v1" \
  --temperature 0.2 \
  --max-tokens 4096 \
  --system-prompt "Your reviewer role definition..." \
  --user-prompt "Review this report..."
```

**Script output:** JSON with `{ content, usage }` or `{ error, status: "failed" }`

**Invocation method:** Use the `Shell` tool to run the script and parse JSON output.

#### Prompt Construction for External Reviewer

**System prompt** (from `.cursor/agents/reviewer.md`):
- The reviewer role definition
- The scoring rubric (6 dimensions with weights)
- The verdict threshold rules
- The output format requirements

**User prompt — Round 0 (initial review):**

Construct from:
- The full content of `grounded.md`
- The full content of `lit.md`
- The full content of `summary.md` (current draft)
- Instructions to score and return structured JSON

**User prompt — Round N (N >= 1, re-check after writer repair):**

Construct from:
- The full content of `grounded.md`
- The full content of `lit.md`
- The **current** `research_report.md` (post-repair draft)
- `data/review_outputs/<ground_id>/round_<N-1>/review_report.md` (previous round diagnosis)
- Instructions: "This is Round N re-check. Round N-1 verdict was [repair/pass]. The writer applied [list repair actions]. Please score the revised draft and return structured JSON."

#### Response Parsing

The external API response is a JSON string. Parse it to extract:

```json
{
  "content": "<model's response text>",
  "usage": {
    "prompt_tokens": 1000,
    "completion_tokens": 500,
    "total_tokens": 1500
  }
}
```

The `content` should be parsed as a structured review payload with:
- `scores`: 6 dimension scores with raw/weight/subtotal
- `weighted_total`: computed weighted score
- `verdict`: "pass" | "repair"
- `needs_repair`: boolean
- `repair_actions`: array of {action, details}
- `main_weaknesses`: array of weakness descriptions

#### External vs Local Reviewer

| Aspect | External Reviewer (Shell) | Local Reviewer (Task) |
|--------|---------------------------|----------------------|
| Model | Fully customizable | Configured in reviewer.md |
| Invocation | Shell + Python script | Task tool + subagent |
| Independence | Guaranteed (different API) | Depends on model config |
| Latency | Network call required | Faster (in-process) |
| Cost | External API pricing | Cursor subscription |
| Stability | No MCP connection issues | Stable (in-process) |

#### Contract Compliance for External Reviewer

When using external reviewer, the following fields must still be recorded in `review_state.json`:

- `used_reviewer_role`: **must be `true`**
- `used_writer_role`: **must be `true`** (if repair was needed)
- `reviewer_independence`: **must be `"high"`** (external model is fully independent)
- `reviewer_agent_path`: `null` (no local reviewer agent used)
- `reviewer_model_hint`: the external model name from config
- `external_reviewer_config`: the full config used (for audit)

#### Error Handling

If external API call fails:
1. If `fallback_to_local: true`: retry with local Cursor reviewer
2. If `fallback_to_local: false`: report error and stop review

### review_history.json format

After each round, append the round's summary to `data/review_outputs/<ground_id>/review_history.json`:

```json
{
  "ground_id": "<ground_id>",
  "total_rounds": 2,
  "rounds": [
    {
      "round": 0,
      "weighted_total": 76.0,
      "verdict": "repair",
      "needs_repair": true,
      "scores": {
        "topic_alignment": {"raw": 4, "weight": 15, "subtotal": 12.0},
        "coverage_completeness": {"raw": 4, "weight": 20, "subtotal": 16.0},
        "evidence_specificity": {"raw": 4, "weight": 20, "subtotal": 16.0},
        "analytical_depth": {"raw": 3, "weight": 20, "subtotal": 12.0},
        "structure_and_narrative_coherence": {"raw": 4, "weight": 15, "subtotal": 12.0},
        "deliverability": {"raw": 4, "weight": 10, "subtotal": 8.0}
      },
      "repair_actions": [{"action": "...", "details": "..."}],
      "reviewer_agent_path": ".cursor/agents/reviewer.md",
      "writer_agent_path": null,
      "reviewer_model_hint": "<model from reviewer.md frontmatter>",
      "writer_model_hint": "<model from writer.md frontmatter>",
      "reviewer_independence": "high",
      "timestamp": "2026-04-06T14:54:00Z"
    },
    {
      "round": 1,
      "weighted_total": 93.0,
      "verdict": "pass",
      "needs_repair": false,
      "scores": {
        "topic_alignment": {"raw": 4, "weight": 15, "subtotal": 12.0},
        "coverage_completeness": {"raw": 5, "weight": 20, "subtotal": 20.0},
        "evidence_specificity": {"raw": 5, "weight": 20, "subtotal": 20.0},
        "analytical_depth": {"raw": 4, "weight": 20, "subtotal": 16.0},
        "structure_and_narrative_coherence": {"raw": 5, "weight": 15, "subtotal": 15.0},
        "deliverability": {"raw": 5, "weight": 10, "subtotal": 10.0}
      },
      "repair_actions": [],
      "reviewer_agent_path": ".cursor/agents/reviewer.md",
      "writer_agent_path": ".cursor/agents/writer.md",
      "reviewer_model_hint": "<model from reviewer.md frontmatter>",
      "writer_model_hint": "<model from writer.md frontmatter>",
      "reviewer_independence": "high",
      "timestamp": "2026-04-06T15:11:00Z"
    }
  ]
}
```

After the loop completes, also update the symlinks/copies at the root of `review_outputs/<ground_id>/` so existing tooling that reads `review_report.md` and `review_state.json` directly continues to work.

### Choosing Between External and Local Reviewer

| Scenario | Recommended Approach |
|----------|---------------------|
| `reviewer_api_config` provided | **External reviewer for all rounds** via Shell + call_ext_api.py |
| `reviewer_api_config` provided, Round N API call fails + `fallback_to_local: true` | Retry with local reviewer for that round only; resume external for subsequent rounds |
| `reviewer_api_config` provided, Round N API call fails + `fallback_to_local: false` | Report error and stop review |
| `reviewer_api_config` NOT provided | Local reviewer via Task tool (all rounds) |

**Critical rule:** When `reviewer_api_config` is provided, the parent agent **must not** switch to the local reviewer subagent after Round 0. The external API is the designated reviewer for every round. Using the local reviewer mid-loop violates the contract, regardless of whether the local reviewer could produce a valid score.

**CRITICAL:** The reviewer subagent must be created via `Task` tool with `subagent_type="generalPurpose"`. The **prompt must start with an agent role declaration block** to trigger Cursor's agent auto-matching, which will load `.cursor/agents/reviewer.md` and its frontmatter `model` field. The reviewer is **read-only** — it must not write files directly.

Use the `Task` tool with `subagent_type="generalPurpose"`. The prompt must start with:

```
---
You are operating as the **REVIEWER AGENT** (grounded-review-reviewer).
Read and follow .cursor/agents/reviewer.md now to load your reviewer configuration and model.
---
```

Then the prompt must include:

- The exact `ground_id` for the current grounded unit
- Instruction to read `.cursor/agents/reviewer.md` first
- Instruction to read the canonical inputs: `grounded.md`, `lit.md`, `summary.md`, and available supporting artifacts
- Instruction to return a structured review payload

**Example reviewer Task invocation:**

```
---
You are operating as the **REVIEWER AGENT** (grounded-review-reviewer).
Read and follow .cursor/agents/reviewer.md now to load your reviewer configuration and model.
---

Use the grounded-review skill to review the current report draft.

ground_id: <the current grounded unit ID, e.g. "meeting_001_topic01">
round: <current round number, e.g. 0>

Inputs to read:
- data/grounded_notes/<ground_id>/grounded.md
- data/lit_results/<ground_id>/lit.md
- data/report_inputs/<ground_id>/summary.md
- data/reports/<ground_id>/research_report.md (if it already exists — read before scoring)
- data/review_outputs/<ground_id>/round_<N-1>/review_report.md (if round > 0 — for repair progress context)
- data/lit_inputs/<ground_id>/opened_paper_notes.jsonl (if exists)
- data/lit_downloads/<ground_id>/manifest.json (if exists)
- data/lit_inputs/<ground_id>/refine_coverage.json (if exists)

Task: Score the current draft using the rubric in grounded-review/SKILL.md,
check hard gates, diagnose weaknesses, produce minimum repair actions, and return a structured
review payload in your response.

IMPORTANT: Do NOT write files directly. Return a structured diagnosis
payload that the parent agent will persist to disk at data/review_outputs/<ground_id>/round_<N>/.
The payload must include:
  - scores (all 6 dimensions with raw/weight/subtotal)
  - weighted_total
  - verdict (pass / repair)
  - needs_repair (boolean)
  - repair_actions (array of {action, details})
  - passed (boolean)
  - reviewer_independence: "high" (because reviewer agent loaded a dedicated model from reviewer.md)
  - used_reviewer_role: true (explicitly record this)
  - reviewer_agent_path: ".cursor/agents/reviewer.md"
  - reviewer_model_hint: "<model slug from reviewer.md frontmatter>"
  - timestamp: "<ISO 8601 timestamp, e.g. '2026-04-06T14:54:00Z'>"
```

> **Note:** The actual model used by the reviewer subagent is determined entirely by the `model` field in `.cursor/agents/reviewer.md` frontmatter. SKILL.md example prompts use a placeholder — the real value comes from the agent file.

### Task tool invocation for writer

**CRITICAL:** The writer subagent must be created via `Task` tool with `subagent_type="generalPurpose"`. The **prompt must start with an agent role declaration block** to trigger Cursor's agent auto-matching, which will load `.cursor/agents/writer.md` and its frontmatter `model` field. **Do not skip this step even if the repair is simple.**

**Do not let the parent context apply repairs directly.** The bounded repair loop requires a dedicated writer subagent. If `verdict == "repair"` and `round < 2`, the parent agent must launch a writer subagent via `Task` tool — it must not apply repairs in its own context.

Use the `Task` tool with `subagent_type="generalPurpose"`. The prompt must start with:

```
---
You are operating as the **WRITER AGENT** (grounded-review-writer).
Read and follow .cursor/agents/writer.md now to load your writer configuration.
---
```

Then the prompt must include:

- The exact `ground_id` for the current grounded unit
- Instruction to read `.cursor/agents/writer.md` first
- The repair actions approved by the reviewer
- Instruction to preserve the draft's structure and substance

**Example writer Task invocation:**

```
---
You are operating as the **WRITER AGENT** (grounded-review-writer).
Read and follow .cursor/agents/writer.md now to load your writer configuration.
---

Use the grounded-review skill to repair the current report draft.
Do NOT skip reading writer.md.

ground_id: <the current grounded unit ID>

Repair actions approved by the reviewer (apply ONLY these — do NOT improvise additional changes):
- [list the minimum repair actions from the reviewer diagnosis]

Inputs to read:
- data/reports/<ground_id>/research_report.md (current draft — read before revising)
- data/grounded_notes/<ground_id>/grounded.md
- data/lit_results/<ground_id>/lit.md
- data/report_inputs/<ground_id>/summary.md
- data/review_outputs/<ground_id>/round_<N-1>/review_report.md (previous round diagnosis)

Task: Apply ONLY the specified repair actions. Preserve the draft's
structure and substance. Produce the revised report body and write it to
data/reports/<ground_id>/research_report.md.

IMPORTANT: You are the writer role. Only apply the specified repair actions.
Do NOT self-approve or declare the final verdict. Return the revised report body
for the reviewer to re-check.

After the writer completes, record in your response:
  - used_writer_role: true
  - writer_agent_path: ".cursor/agents/writer.md"
  - writer_model_hint: "<model from writer.md frontmatter, e.g. 'inherit'>"
  - repair_actions_applied: [list what was actually applied]
```

### Loop termination

|| Condition | Action |
||-----------|--------|
|| weighted_total >= 90 and no hard-gate failure | **Pass** — launch writer for light repair, then finalize (no re-review needed) |
|| weighted_total < 90 or any hard-gate failure | **Repair** — run writer repair, then re-review via bounded loop (max 5 rounds) |
|| Initial + 5 repair rounds exhausted without pass | Finalize with explicit "loop exhausted" status in `review_state.json` |

### Pass verdict: light repair without re-review

**Pass means the report meets the quality gate.** It does **not** mean the report is perfect or that reviewer diagnoses should be discarded.

When verdict is `pass` but the reviewer identified quality improvement suggestions (even if not hard-gate failures):

1. The parent agent launches a writer subagent via `Task` tool to apply the reviewer's suggested improvements.
2. The writer reads the reviewer diagnosis and applies **only** the suggested improvements.
3. No re-review round is triggered — the report is finalized directly after writer completes.
4. `review_state.json` records `used_writer_role: true` and `repair_actions: [suggested improvements applied]`.

**The distinction from the repair loop:**

- **Repair loop** (verdict = repair): writer repairs → reviewer re-checks → repeat. The reviewer gate determines when to stop.
- **Light repair after pass** (verdict = pass): writer applies suggestions → done. No reviewer re-check because the gate already passed.

This ensures reviewer diagnoses are never discarded, but avoids infinite re-review cycles when the report already meets quality standards.

### Repair Enforcement Rule

**This is a hard rule. Violations must not be silently accepted.**

When a reviewer subagent returns `verdict == "repair"` and `round < 5`:

1. The parent agent **must** launch a writer subagent via `Task` tool.
2. The parent agent **must not** apply repairs in its own context.
3. After the writer completes, the parent agent **must** launch a reviewer subagent again for re-check.

If `used_writer_role == false` when `verdict == "repair"` and `round < 2`, the bounded repair loop was **not executed**. This is a contract violation regardless of whether `research_report.md` was written.

**Remedy:** Re-run the repair loop by launching a writer subagent, then re-review. Do not finalize with a repair verdict still pending.

**In practice:** Before finalizing `research_report.md`, check `review_state.json`. If `verdict == "repair"` and `used_writer_role == false`, re-launch the writer subagent and complete the loop.

## Subagent File Contract

When your Cursor environment supports custom subagents, the review stage should use the following files when present:

- `.cursor/agents/reviewer.md`
- `.cursor/agents/writer.md`

### Expected role split

#### Reviewer subagent

The reviewer subagent is responsible for:

- reading `grounded.md`, `lit.md`, `summary.md`, and available supporting artifacts
- assigning rubric scores
- checking hard gates
- diagnosing concrete weaknesses
- producing the repair plan
- re-checking the revised draft
- deciding `pass` / `repair` / `insufficient`

The reviewer should **not** be the primary author of the final report body except for the diagnosis documents.

If the reviewer subagent is configured as **read-only**, it should not directly modify repository files.
In that case, it should return a structured diagnosis payload to the parent agent, and the parent agent must write:

- `data/review_outputs/<ground_id>/round_<N>/review_report.md`
- `data/review_outputs/<ground_id>/round_<N>/review_state.json`

from the reviewer output.

The reviewer is therefore responsible for the **content** of the review, while the parent agent is responsible for **persisting** that content to disk in the appropriate `round_<N>/` directory when the reviewer cannot write files directly.

#### Writer subagent

The writer subagent is responsible for:

- preserving the draft structure where possible
- performing only the approved repair actions
- revising the report into `research_report.md`
- not inventing new evidence or new citations
- returning the revised report for reviewer re-check

The writer should **not** self-approve the final report without reviewer confirmation.

The writer may write `research_report.md` directly because the writer is the editing role.
However, the writer must not overwrite `review_report.md` or `review_state.json` with its own independent judgement.
Those files must reflect the reviewer-approved diagnosis and verdict.

### Preferred execution order

When reviewer/writer subagents are available, use this order (as detailed in the **Execution Flow** section above):

1. **Parent agent** launches reviewer subagent via `Task` tool to score and diagnose the current draft
2. **Parent agent** creates `round_<N>/` directory and persists `review_report.md` and `review_state.json` from the reviewer output
3. **Parent agent** launches writer subagent via `Task` tool to apply the approved repair actions (if verdict is `repair` and round < 5)
4. **Parent agent** archives the current round: if round > 0, copy `round_<N>/` → `round_<N-1>/`
5. **Parent agent** launches reviewer subagent via `Task` tool to re-check the revised draft
6. **Parent agent** creates a new `round_<N+1>/` directory and persists the new `review_report.md` and `review_state.json`
7. Repeat steps 3–6 for at most 5 repair rounds
8. **Only after reviewer passes**, update `review_history.json`, update symlinks/copies at `review_outputs/<ground_id>/`, and finalize `research_report.md`

The parent agent must not skip the `Task`-tool subagent calls or collapse the reviewer → writer → reviewer cycle into a single pass.

If the subagents are unavailable, the same base model may simulate both roles, but the role separation and `reviewer_independence` record must still be preserved.

### Reviewer return contract

A reviewer subagent may be configured as **read-only**.
If so, it should return a structured review payload in chat rather than trying to write files directly.
That payload must contain enough information for the parent agent to persist both:

- `data/review_outputs/<ground_id>/round_<N>/review_report.md`
- `data/review_outputs/<ground_id>/round_<N>/review_state.json`

The parent agent must not skip file persistence merely because the reviewer role was read-only.

### Parent-agent persistence rule

The parent/main agent is always responsible for ensuring that the required output files exist on disk at the end of the review stage.
Read-only reviewer configuration does **not** relax the output-file requirement.

---

## Core Review Responsibilities

The review stage should check and improve the report draft along these dimensions:

### 1. Topic alignment

Check whether the draft remains tightly aligned with:

- the grounded topic
- the source-derived problem setting
- the actual decision needs of the current project

Downweight or remove weakly related literature that inflates length without improving relevance.

### 2. Coverage completeness

Check whether the report adequately covers:

- the major grounded questions
- the most important themes from `lit.md`
- relevant downloaded and parsable papers when such coverage is expected from the research stage

### 3. Evidence specificity

Check whether major claims are actually supported by:

- the grounded note
- the literature result
- downloaded/opened evidence when available

If not, soften, qualify, or remove them.

### 4. Analytical depth

Check whether the report explains:

- what the method/problem actually is
- why a design matters
- what the evidence really supports
- what remains uncertain

### 5. Structure and narrative coherence

Check whether the report is well structured and readable.

You may reorganize or rewrite for clarity, but **do not remove substance merely to make it shorter or cleaner**.

### 6. Deliverability

Check whether the report is strong enough to be handed to the output layer.

The result should be:

- structurally clear
- technically grounded
- evidence-aware
- readable
- suitable for rendering/export

### 7. Removal of search-process noise

Check whether the report draft contains:

- query counts
- hit counts
- opened-link counts
- download counts
- manifest-like inventories
- retrieval execution commentary

These do not belong in the final report body and should be removed.

---

## Review Authority Boundary

This skill may:

- revise wording
- reorganize material
- restore omitted important details
- improve balance across sections
- soften unsupported claims
- clarify evidence strength
- strengthen section transitions
- improve the final report structure
- trigger one bounded targeted evidence-recovery action when the current inputs are clearly insufficient

This skill must **not**:

- add new external evidence casually or without diagnosis
- run a full new literature survey by default
- fabricate experiments
- invent citations
- move substantive literature analysis out of the report body just to shorten the document
- change the research direction without support from the inputs
- run an unbounded repair loop

---

## Structured Scoring Rubric

Before rewriting the final report, score the current draft across the following dimensions.

Use a **1–5 scale** for each dimension, where:

- `1` = very weak / seriously insufficient
- `2` = weak
- `3` = acceptable but clearly imperfect
- `4` = strong
- `5` = very strong

### Dimensions

1. `topic_alignment`
2. `coverage_completeness`
3. `evidence_specificity`
4. `analytical_depth`
5. `structure_and_narrative_coherence`
6. `deliverability`

### Weights

Use the following weights when computing the weighted total (/100):

- `topic_alignment`: 15
- `coverage_completeness`: 20
- `evidence_specificity`: 20
- `analytical_depth`: 20
- `structure_and_narrative_coherence`: 15
- `deliverability`: 10

### Weighted total formula

Compute the final weighted total as:

`weighted_total =`
- `(topic_alignment / 5) * 15`
- `+ (coverage_completeness / 5) * 20`
- `+ (evidence_specificity / 5) * 20`
- `+ (analytical_depth / 5) * 20`
- `+ (structure_and_narrative_coherence / 5) * 15`
- `+ (deliverability / 5) * 10`

Rules:

- use **exactly** this formula
- do **not** invent any alternative scaling rule
- do **not** rescale weights
- round only at the final reported total if needed
- keep the unrounded internal calculation consistent with the displayed subtotal values

### Required score presentation rule

For each dimension, the review report must explicitly show:

- the raw score (for example `4/5`)
- the weight
- the weighted subtotal computed as `(score / 5) × weight`
- an evidence-backed explanation

For example:

- `topic_alignment: 4/5, weight=15, subtotal=12.0`

The final `weighted_total` must equal the sum of the six displayed subtotals.

If the displayed subtotals and final total are inconsistent, the review is invalid and must be corrected before finalizing `review_report.md` or `review_state.json`.

### Scoring rule

Every score must be **evidence-backed**.

Do not assign a score without explicitly naming:

- what in the current draft supports the score
- what in the current draft weakens the score
- which sections or paper analyses are responsible for the weakness

The review report must not contain empty statements such as “depth is somewhat weak” without concrete explanation.

---


### Dimension-specific scoring constraints

Use the following concrete rules to disambiguate score boundaries. These constraints reduce subjective leniency and make scoring consistent across reviewers.

#### 1. topic_alignment

| Score | Condition |
|-------|-----------|
| 5/5 | All grounded project directions are addressed with dedicated coverage; no drift; source context fully preserved |
| 4/5 | All directions covered, but 1-2 minor tangential sections present OR 1 important nuance from source weakened |
| 3/5 | 1 grounded direction missing or substantially weakened; moderate drift detected |
| 2/5 or below | Multiple directions missing or severely weakened; substantial drift |

**Constraint:** A direction that appears in grounded.md must appear in the report with comparable depth. Downweighting is permitted; silent omission is not. Assigning 4/5 requires naming exactly which section is tangential or which nuance was weakened.

#### 2. coverage_completeness

| Score | Condition |
|-------|-----------|
| 5/5 | All lit.md papers analyzed; all major themes covered; unresolved questions match lit.md's scope |
| 4/5 | All papers present but 1-2 papers receive shallow analysis; OR 1 theme underdeveloped |
| 3/5 | 1-2 papers silently omitted OR 2+ papers shallow; major theme missing or placeholder-level |
| 2/5 or below | Multiple papers omitted; report is clearly thinner than lit.md |

**Constraint:** Each downloaded PDF must be explicitly acknowledged with its refinement contribution. Assigning 4/5 requires naming exactly which paper(s) are shallow and what is missing. Assigning 3/5 or below requires naming the specific paper(s) omitted or shallow.

#### 3. evidence_specificity

| Score | Condition |
|-------|-----------|
| 5/5 | Every major claim cites specific numbers from lit.md; unvalidated claims are explicitly flagged with evidence boundary |
| 4/5 | Most claims supported by numbers, but 1-2 claims lack specific quantification OR 1 unvalidated claim not flagged |
| 3/5 | Several claims lack quantitative support; OR 2+ unvalidated claims presented without flag |
| 2/5 or below | Most claims unsupported; overclaiming pervasive |

**Constraint:** The phrase "unvalidated claim" must appear in the review when a grounded note claim is not matched by published literature. Assigning 4/5 requires naming the specific unsupported claim(s) and where they appear. A report that presents a claim like "within 3 centimeters" without flagging it as unvalidated cannot receive 5/5.

#### 4. analytical_depth

| Score | Condition |
|-------|-----------|
| 5/5 | For every major unresolved question: explains WHY it is unresolved, what evidence bears on it, and what would resolve it |
| 4/5 | Most questions analyzed, but 1-2 questions only restated without explaining the causal gap; OR 1 question lacks actionability |
| 3/5 | Analysis stays on the surface; questions mostly restated rather than analyzed; few causal explanations |
| 2/5 or below | No genuine analysis; report is a summary without synthesis |

**Constraint:** Assigning 4/5 requires naming the specific question(s) that were restated without causal analysis. Simply labeling a question "unresolved" does not count as analysis. The reviewer must identify why existing evidence does not resolve it and what specific evidence would.

#### 5. structure_and_narrative_coherence

| Score | Condition |
|-------|-----------|
| 5/5 | Each piece of evidence appears exactly once at its most relevant depth level; transitions guide the reader logically |
| 4/5 | 1-2 instances of material appearing multiple times at equivalent depth levels, creating minor friction |
| 3/5 | 3+ instances of repetition OR 1 major structural flaw; transitions weak |
| 2/5 or below | Report is disorganized; reader cannot follow the argument |

**Constraint:** When the same paper's methodology appears in both the grounded findings section and the detailed paper analysis section and the thematic synthesis section, each duplicate appearance counts as one repetition instance. Three repeated paper discussions in three locations constitutes 3 repetition instances, which pushes toward 3/5. Assigning 4/5 requires naming the specific repeated content and its locations.

#### 6. deliverability

| Score | Condition |
|-------|-----------|
| 5/5 | Every next-step recommendation is accompanied by sufficient justification; every risk has named source and consequence |
| 4/5 | Most recommendations actionable, but 1-2 are vague; OR 1-2 risks lack named source |
| 3/5 | Multiple vague recommendations; OR report has placeholder sections; OR 2+ risks lack named source |
| 2/5 or below | Recommendations are generic; report is not ready for downstream output rendering |

**Constraint:** A recommendation is vague if it cannot be acted upon without additional research. "Access ShowHowTo's full paper" is specific and actionable; "improve the evaluation" is not. A risk lacks a named source if it references "the literature" without naming specific papers or findings. Assigning 4/5 requires naming the specific vague recommendation(s) or unnamed risk(s).

## Hard Gates

The report must **not** pass directly if any of the following are true:

- `topic_alignment < 3/5`
- `coverage_completeness < 3/5`
- `evidence_specificity < 3/5`
- `analytical_depth < 3/5`

The report must also fail the gate if any of the following are true:

- important downloaded-and-parsable papers that should be covered are silently omitted
- multiple paper analyses are clearly placeholder-like or generic
- the report drifts substantially away from the grounded topic
- the report is clearly thinner than `summary.md` or `lit.md` on core technical substance

---

## Verdict Logic

After scoring, assign one of two verdicts:

- `pass`
- `repair` (no report is discarded)

### Suggested thresholds

- **Pass**: weighted total >= 90 and no hard-gate failure
- **Repair**: weighted total < 90, or any hard-gate weakness (no report is discarded)

The verdict must be justified in `review_report.md`.

---

## Repair Loop

The repair loop must be **bounded**.

### Maximum rounds

The bounded loop consists of:

- **Round 0**: initial review by reviewer subagent
- **Round 1** (optional): writer subagent repair → reviewer subagent re-check
- **Round 2** (optional): writer subagent repair → reviewer subagent re-check
- **Round 3** (optional): writer subagent repair → reviewer subagent re-check
- **Round 4** (optional): writer subagent repair → reviewer subagent re-check
- **Round 5** (optional): writer subagent repair → reviewer subagent re-check

Do **not** loop beyond round 5.

### Repair-first rule

Do not rewrite immediately after a vague negative impression.

First produce:

- scores
- weaknesses
- repair priorities
- minimum repair actions

Then repair.

The diagnosis step must be produced by the reviewer subagent via `Task` tool. The repair step must be performed by the writer subagent via `Task` tool. See the **Execution Flow** section above for the required `Task` invocation patterns.

The parent agent must not skip the reviewer → writer → reviewer cycle even for a simple-seeming repair. Each round must produce a new reviewer verdict before deciding whether to stop.

### Repair categories

Use the minimum repair action that addresses the weakness:

1. `rewrite_existing_sections`
2. `restore_omitted_literature_detail`
3. `deepen_weak_paper_analyses`
4. `remove_or_downweight_weakly_relevant_material`
5. `repair_downloaded_paper_coverage`
6. `targeted_supplementary_research`

### Targeted supplementary research rule

Do **not** re-run the full research stage by default.

Only use `targeted_supplementary_research` if the reviewer explicitly diagnoses that:

- the current inputs are genuinely insufficient to meet the quality gate, and
- the weakness cannot be repaired by better use of `lit.md`, `summary.md`, or the available notes.

If supplementary research is needed, keep it narrow and clearly scoped to the diagnosed gap.

---

## Final Report Writing Rules

### 1. Preserve the report-draft role of `summary.md`

Treat `summary.md` as the **main report draft**, not as a short memo to be heavily rewritten.

The final report should usually remain close to the draft’s major structure unless the draft structure is genuinely weak.

### 2. Never compress rich literature analysis into shallow recap

If the draft already contains strong literature-based analysis, keep it in the final report body.

Do **not** reduce rich thematic analysis into:

- a few generic bullets
- a tiny “literature support” paragraph
- a background-only aside

### 3. Preserve important technical detail

If the underlying materials contain:

- important numeric facts
- concrete failure modes
- architecture branches
- method-specific disagreements
- design alternatives
- evidence-strength distinctions
- important caveats about transfer or evaluation

then keep them when they materially affect understanding.

### 4. Express evidence strength carefully

Use wording such as:

- strongly supported
- directly supported in a similar setting
- partially supported
- directionally supported
- conceptually relevant but not directly validated here
- limited evidence
- unresolved by current evidence

Do not overclaim.

### 5. Prefer body integration over appendix-style dumping

The final report should carry the most relevant literature analysis **inside the main body**, especially in the deep-analysis and integrated-assessment sections.

Do not exile important literature content to the end of the report unless it is truly peripheral.

### 6. Do not include process diagnostics in the report body

Do not include:

- number of search queries
- number of hits
- number of opened links
- number of downloads
- file manifests
- retrieval QA commentary
- review-loop score tables or repair-loop bookkeeping

### 7. Preserve real unresolved questions

The final report should not artificially flatten genuine uncertainty.

If the research question remains unresolved, say so clearly.

### 8. Do not optimize for brevity alone

There is no benefit in making the final report shorter if that shortness destroys understanding.

A final report may be the same length as the draft or even slightly longer if that is necessary to restore omitted substance or improve clarity.

---

## Required Final Report Structure

Write the final report with the following structure.

# Research Report

## 1. Executive Overview

Write **2–4 substantial paragraphs**.

This section should clearly state:

- the problem or task setting
- the current understanding
- the most important grounded findings
- the most important literature-backed insights
- the most important unresolved bottleneck or decision point

## 2. Problem Setting and Source Context

Write **2–5 substantial paragraphs** explaining:

- the grounded source context
- the current project state
- relevant constraints, goals, and stakes
- the setup assumptions needed to understand the report

## 3. Grounded Findings from the Source Material

Preserve the most important source-derived findings, such as:

- concrete observations
- design branches
- current hypotheses and conclusions
- constraints, disagreements, or anomalies
- implementation or evaluation concerns

Prefer **focused paragraphs or short thematic subsections**, not generic bullets.

## 4. Literature-Based Deep Analysis

This should remain a **major body section**, not a thin recap.

Organize it into **3–6 thematic subsections** when the material supports that depth.

For each theme, preserve:

- why the theme matters
- what the literature actually says
- the support strength for the current project
- mismatch, transfer limits, or caveats
- the practical implication for the current project

## 5. Integrated Assessment for the Current Project

Write **2–5 substantial paragraphs** synthesizing grounded evidence and literature evidence into a project-level assessment.

## 6. Unresolved Questions and Decision-Critical Gaps

Write **4–8 substantial items** describing:

- the unresolved issue
- why it matters
- what evidence is missing
- what would reduce the uncertainty

## 7. Recommended Next Steps

Write **4–7 concrete actions**, each with enough explanation to make the action meaningful.

## 8. Key Risks, Caveats, and Evidence Boundaries

Write **4–8 items** preserving:

- methodological risks
- evidence-transfer risks
- evaluation risks
- data or generalization risks
- hidden assumptions and caveats

---

## Required Review Report Structure

Write `review_report.md` with the following structure:

# Review Report

## 1. Current Draft Evaluation

- brief verdict summary
- weighted total score
- whether reviewer independence was high or limited

## 2. Rubric Scores

List each dimension with:

- raw score
- weight
- weighted subtotal computed as `(score / 5) × weight`
- evidence-backed explanation

## 3. Hard-Gate Failures

State clearly whether any hard gate failed and why.

## 4. Main Weaknesses

List the most important weaknesses in priority order.

## 5. Minimum Repair Actions

For each weakness, specify the minimum repair needed.

## 6. Round Outcome

State one of:

- pass
- repair
- insufficient

If pass, say why.
If repair, say what was repaired or still must be repaired.
If insufficient, say what blocks deliverability.

---

## Round Archival

The review stage uses a **per-round archival pattern** to preserve full review history for retrospective comparison across rounds.

### Archival Logic

1. **Round 0**: Create `round_0/` directory. Write `review_report.md` and `review_state.json` to `round_0/`. Initialize `review_history.json` with the Round 0 summary.

2. **Transition from round N to round N+1**: Create a new `round_<N+1>/` directory. Write the new round's files there. Append the round's summary to `review_history.json`.

3. **Loop termination**: Update `review_history.json`, update root-level symlinks/copies for backward compatibility, and finalize `research_report.md`.

### What to Archive

Archive the following per round:
- `review_report.md` — full diagnosis text for that round
- `review_state.json` — full state snapshot for that round

Do **not** archive:
- `research_report.md` — updated in place at `data/reports/<ground_id>/research_report.md`
- `review_notes.md` — if present, not archived

### Why Round Numbers Start at 0

Round 0 = **initial review** before any repair. Round 1 = **first repair round**. Round 2 = **second repair round**. Round 3 = **third repair round**. Round 4 = **fourth repair round**. Round 5 = **fifth repair round**. This makes it easy to `diff round_0/ round_1/` to see exactly what changed.

### No Overwriting Historical Rounds

Once a `round_<N>/` directory is written, it is **immutable for that round**. The parent agent must never overwrite a historical directory — only create new `round_<N+1>/` directories.

---

## Strength Requirement

The final report should be:

- more evidence-aligned than `summary.md`
- at least as informative as `summary.md`
- richer and more deliverable than a compressed memo
- suitable for direct use by downstream output-format skills

It should **not** be:

- shorter but emptier
- a search log
- a lightly edited copy that still loses major literature depth
- a presentation-formatting artifact

---

## Completion Criteria

This task is complete only if ALL of the following are true:

1. `grounded.md` was actually read
2. `lit.md` was actually read
3. `summary.md` was actually read
4. For **each completed round**, a structured `review_report.md` was written to:
   - `data/review_outputs/<ground_id>/round_<N>/review_report.md`
5. For **each completed round**, a machine-readable `review_state.json` was written to:
   - `data/review_outputs/<ground_id>/round_<N>/review_state.json`
6. `review_history.json` was written to:
   - `data/review_outputs/<ground_id>/review_history.json`
7. Root-level symlinks/copies exist for backward compatibility:
   - `data/review_outputs/<ground_id>/review_report.md`
   - `data/review_outputs/<ground_id>/review_state.json`
8. a real final report was written to:
   - `data/reports/<ground_id>/research_report.md`
9. the final report preserves relevant deep literature analysis in the main body
10. the final report is clearly more deliverable than the draft without becoming thinner
11. the final report body does not drift into search-process recap or review-loop bookkeeping
12. the report either:
    - passed the quality gate, or
    - exhausted the bounded repair loop and explicitly recorded the remaining blockers
13. **`used_reviewer_role === true`** in `review_state.json` — reviewer was created via `Task` tool OR via `call_ext_api.py` (external API); if external reviewer was used, `reviewer_agent_path` must be `null` and `external_reviewer_config` must be present
14. **`reviewer_independence !== "unknown"`** in `review_state.json` — independence was verified
15. **`used_writer_role === true`** in `review_state.json` — writer was created via `Task` tool (required for both repair verdicts AND pass verdicts with suggested improvements)
16. **`reviewer_agent_path` is correctly set**: `null` if external reviewer via `call_ext_api.py`; path to `.cursor/agents/reviewer.md` if local reviewer via `Task` tool. When `reviewer_api_config` is present, `reviewer_agent_path` must be `null` and `external_reviewer_config` must be populated.
17. **All historical rounds preserved**: each `round_<N>/` directory is intact and was never overwritten
18. **`review_history.json` is consistent**: its `rounds` array matches the `review_state.json` of each `round_<N>/` directory

**If any of checks 13–18 fail, the review stage is incomplete regardless of whether output files exist. Re-execute the review properly.**

## Subagent Metadata Recording

`review_state.json` must record the following subagent-related fields. These are not optional — they verify that the bounded loop with reviewer/writer subagents was actually executed:

- `used_reviewer_role`: **must be `true`** — if external reviewer via `call_ext_api.py`, still counts as reviewer creation; if `false`, the review was run monolithically in the parent context, which violates this skill's contract.
- `used_writer_role`: **must be `true`** if a writer subagent was launched via `Task` tool. This is required for both repair verdicts AND pass verdicts with reviewer-suggested improvements. If `false` when verdict was pass and the reviewer provided suggestions, the light repair step was skipped, which violates the skill contract.
- `reviewer_agent_path`: `null` if external reviewer via `call_ext_api.py`; path to `.cursor/agents/reviewer.md` if local reviewer via `Task` tool.
- `writer_agent_path`: path to `.cursor/agents/writer.md` or the subagent config used, or `null` if no dedicated writer agent was found.
- `reviewer_model_hint`: explicit model slug from the reviewer agent config if configured, otherwise `inherit` or `unknown`.
- `writer_model_hint`: explicit model slug from the writer agent config if configured, otherwise `inherit` or `unknown`.
- `reviewer_independence`: `high` if reviewer uses a clearly different model from the writer, `limited` if the same inherited model was used, `unknown` if not determinable.
- `repair_rounds_completed`: integer count of repair rounds that were actually executed (0 if no repair was needed; incremented only on repair verdicts).
- `light_repair_after_pass`: boolean. `true` if verdict was pass and the writer was launched to apply reviewer-suggested improvements without re-review. `false` if no light repair was performed after a pass verdict.

If `used_reviewer_role` is `false`, the review must be treated as not properly executed per this skill's contract, regardless of whether `review_report.md` and `research_report.md` were written.

---

## Verification and Self-Check

Before treating the review stage as complete, the executing agent must verify `review_state.json` against the following checklist. If any check fails, the review stage is **incomplete** and must be re-executed properly.

### Checklist

| Check | Condition | If fails |
|-------|-----------|----------|
| `used_reviewer_role === true` | Reviewer subagent via `Task` tool OR external API via `call_ext_api.py` | Review incomplete — re-execute reviewer properly |
| `reviewer_agent_path !== null` OR `external_reviewer_config` present | If local reviewer: path set; if external reviewer: `null` + config present | Review incomplete — ensure reviewer config is recorded |
| `reviewer_independence !== "unknown"` | Independence was explicitly recorded | Review incomplete — re-execute reviewer properly |
| `verdict !== "repair"` OR (`verdict === "repair"` AND `used_writer_role === true` AND `round < 5`) | If verdict is repair and round < 5, writer must be called | Review incomplete — launch writer subagent and complete repair loop |
| `verdict === "repair"` AND `round >= 5` AND `used_writer_role === true` | Loop limit reached, loop exhausted correctly | Finalize with loop_status=exhausted |
| For repair: `writer_agent_path !== null` | Writer read `.cursor/agents/writer.md` | Review incomplete — re-execute writer with proper agent |
| All 6 rubric scores present | `scores` object has all dimensions | Review incomplete — re-execute reviewer |
| `weighted_total` consistent with scores | Sum of (score/5)*weight matches | Review invalid — re-execute reviewer |
| `round_<N>/` directory created for each completed round | Each round's files are in its own directory | Review incomplete — archive files to correct `round_<N>/` |
| `review_history.json` exists and contains all rounds | History records match the `review_state.json` of each round | Review incomplete — rebuild `review_history.json` from round directories |
| No historical round directory was overwritten | Only new `round_<N+1>/` directories are created; existing `round_<N>/` unchanged | Review incomplete — restore from backup if available |

### Self-healing after verification failure

If a `review_state.json` already exists with `used_reviewer_role === false`, the review was not properly executed. The agent must:

1. If external reviewer mode was used: re-call `call_ext_api.py` for the current round with the full reviewer payload, and re-persist `review_state.json` with `used_reviewer_role: true` and `reviewer_agent_path: null`.
2. If local reviewer mode was used: re-launch a reviewer subagent via `Task` tool using the reviewer invocation pattern.
3. If verdict was repair and `used_writer_role === false`, re-launch a writer subagent and complete the repair loop.

The presence of `review_report.md` and `research_report.md` on disk does **not** mean the review was properly executed. The metadata fields in `review_state.json` are the authoritative record of contract compliance.

---

