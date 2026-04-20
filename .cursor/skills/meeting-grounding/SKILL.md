---
name: meeting-grounding
description: Convert a raw multi-speaker meeting transcript into structured meeting notes for downstream follow-up, with optional topic-level fan-out when the meeting contains multiple independent discussion blocks.


---

# Meeting Grounding

Convert a raw meeting transcript into a structured meeting grounding output.

This skill is for **meeting grounding**, not a narrative recap.
It should produce a stable intermediate note that is easy to read and easy for downstream skills to use.

This skill supports both:

- **single-topic meetings**
- **multi-topic meetings** where the transcript contains multiple discussion blocks that should be researched separately downstream

## When to Use

Use this skill when:

- the input is a raw meeting transcript
- the transcript is noisy, repetitive, or multi-speaker
- you need structured meeting notes before follow-up work

Do not use this skill when:

- the input is already a structured memo or action-item list
- the task is to write a polished final report
- the input is not a meeting/discussion transcript

## Input

A plain text meeting transcript.

The transcript may contain:

- speaker labels
- timestamps
- interruptions
- repeated phrases
- incomplete sentences
- filler language
- partial or ambiguous decisions

## Output

This skill always produces a **meeting-level** grounding note.

### Required output

Always produce:

```markdown
grounded.md
```

This file must follow the meeting grounding schema below.

### Optional multi-topic outputs

If the meeting clearly contains multiple **independent topic blocks** that should be researched separately downstream, also produce:

```text
topic_manifest.json
child_outputs/topic_01/grounded.md
child_outputs/topic_02/grounded.md
...
```

Do **not** create topic children unless there is strong evidence that the meeting contains multiple discussion blocks that should remain separate for downstream research, summary, review, and reporting.

## Meeting-level grounded.md schema

Return markdown with **exactly** these sections.
If a section has no reliable evidence, write `None identified`.

```markdown
# Meeting Grounding

## 1. Meeting Topic
[2–4 sentence statement of the meeting’s main topic and purpose.
If the meeting genuinely contains multiple distinct topics, summarize the overall meeting scope at a higher level.]

## 2. Main Discussion Points
- [One bullet per major discussion block or major sub-topic]

## 3. Key Conclusions
- [Only items explicitly agreed, decided, confirmed, ruled out, or clearly deferred]
- [If none: None identified]

## 4. Constraints / Risks
- [Only constraints or risks explicitly stated, or strongly supported by repeated evidence]
- [If none: None identified]

## 5. Disagreements or Unresolved Issues
- [Preserve disagreements, uncertainty, and open questions]
- [If none: None identified]

## 6. Suggested Next Steps
- [Concrete follow-up actions or suggested follow-ups grounded in the transcript]
- [Do not invent owners, deadlines, or commitments]
- [If none: None identified]

## 7. Search Keywords

### Problem Keywords
- ...

### Method / Solution Keywords
- ...

### Domain / Constraint Keywords
- ...
```

## Topic-level child grounded.md schema

If topic children are created, each child grounded note must also follow the **same meeting-grounding schema** exactly.

Do **not** invent a new topic schema.

Each child grounded note should cover only its own topic block, not the entire meeting.

## Topic segmentation rule

Before writing outputs, first read the transcript **holistically** and decide whether the meeting is:

- a **single-topic meeting**, or
- a **multi-topic meeting** with multiple independent discussion blocks

A new topic block should be created **only** when the discussion has shifted to a different topic that would reasonably require separate downstream research.

This is a semantic judgment, not a simple surface-rule split.

## Topic segmentation hard constraints (MUST follow)

### Constraint 1: Same person, different work → Must split

When one speaker transitions from one work item to a completely different work item, create a new topic regardless of discussion duration or depth.

Indicators of different work (create new topic):
- Switching from Project A to Project B
- Switching from Experiment X to Experiment Y
- Switching from Tool development to Paper writing
- Any transition between distinct tasks with no direct dependency

### Constraint 2: Different work → Never merge

Multiple work items discussed by the same or different speakers must NOT be merged into one topic, even if:
- They are discussed consecutively
- They share similar technical domain
- They belong to the same team member
- They are briefly mentioned together

### Constraint 3: Topic identity rule

Each topic has exactly ONE identity:
- One distinct work item
- One primary contributor
- One set of follow-up actions

If a discussion covers multiple work items, it is MULTIPLE topics.

## Strong rule: do not split on weak signals alone

Do **not** split topics merely because of:

- speaker changes
- interruptions
- Q&A turns
- short digressions
- brief examples
- clarification exchanges
- repeated restatements
- agenda phrases without a real shift in discussion target

These are at most weak supporting signals.

## What counts as a real topic shift

Only create a new topic block when there is strong evidence that the meeting has shifted to a different discussion unit, such as:

- a different project, paper, system, workstream, or case
- a different primary problem or decision target
- a different set of follow-up research needs
- a sustained new discussion block rather than a brief aside

## Topic segmentation workflow

1. Read the full transcript first.
2. Identify major discussion blocks.
3. Decide whether they should remain together or be split for downstream research.
4. Always write the meeting-level `grounded.md`.
5. Only if multi-topic structure is strong and useful, also write:
   - `topic_manifest.json`
   - `child_outputs/topic_xx/grounded.md`

## topic_manifest.json requirements

If multi-topic outputs are created, write a `topic_manifest.json` file that records:

- source meeting identifier if available
- segmentation mode
- topic count
- for each topic:
  - `topic_id`
  - `topic_ground_id`
  - `title`
  - `start_turn`
  - `end_turn`
  - `start_time` if recoverable
  - `end_time` if recoverable
  - `confidence`
  - `boundary_reason`
  - `topic_summary`
  - `search_keywords`
  - `child_grounded_path`

## Instructions

- Do **not** write a chronological recap of the meeting.
- Do **not** invent facts, conclusions, owners, deadlines, or commitments.
- Do **not** turn suggestions or strong opinions into final conclusions.
- Do **not** add external knowledge, acronym expansions, years, or metadata not explicitly stated.
- Remove greetings, filler, repeated acknowledgements, and low-signal chatter.
- Keep disagreement and uncertainty if they matter.
- Group related discussion into high-level sub-topics instead of speaker-by-speaker bullets.
- Keep the output concise and structured.
- In multi-topic meetings, preserve separation between independent discussion blocks.

## Special Rules

### Key Conclusions

Only include something here if it was clearly settled in the meeting.
If it was only proposed, discussed, or favored, do not treat it as a conclusion.

### Constraints / Risks

Only include constraints or risks that were explicitly stated or strongly evidenced.
Do not infer hidden constraints from weak hints.

### Suggested Next Steps

Only include follow-up actions that were explicitly discussed or strongly implied.
Do not invent action owners, deadlines, or firm commitments.

### Search Keywords

Use specific noun phrases that are useful for later search.
Avoid generic terms such as:

- project
- meeting
- update
- issue
- optimization
- system

For multi-topic meetings, topic-specific search keywords should be attached to each topic in `topic_manifest.json` and reflected in each child grounded note.

## Handling Difficult Cases

- If the transcript is repetitive, summarize repeated points once.
- If the transcript is incomplete, paraphrase only when meaning is clear.
- If statements conflict, keep the conflict under unresolved issues.
- If the meeting contains multiple independent discussion blocks, do not force them into one topic-specific note.
- If the topic structure is genuinely unclear, prefer a single meeting-level grounding note and avoid over-segmentation.
- For long transcripts, identify major semantic blocks first, then synthesize.

## Example Invocation

`/meeting-grounding`