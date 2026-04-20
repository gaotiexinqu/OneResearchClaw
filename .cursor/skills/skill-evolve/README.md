# Skill Evolve (Optional Sidecar)

Skill Evolve is an **optional, feedback-driven patch workflow** for improving the skill framework in a controlled way.

It is **not** part of the default report-generation pipeline.
It runs only when the user explicitly requests it.

## Core Principles

1. **Opt-in only**: ordinary report generation must not trigger Skill Evolve.
2. **Candidate-first**: proposed changes are tested in an isolated candidate workspace before any version promotion.
3. **Manual review first**: generated patch proposals are drafts and must be reviewed/refined before real patch application.
4. **Regression gate required**: promotion requires a passed gate result.
5. **No overwrite of `.cursor/skills/`**: promotion creates versioned skill directories such as `.cursor/skills-v002/`.
6. **Rollback-ready**: every promoted version records its base version and rollback target.

## High-Level Loop

```text
raw feedback
-> normalized feedback
-> patch proposal
-> candidate workspace
-> regression gate
-> promote or reject/archive
```

## Important Limitation

Promotion updates the **Skill Evolve stable pointer**, but it does **not** silently change the repository's default `.cursor/skills/` behavior.

To use a promoted version, the user must explicitly:
- point a future prompt at `.cursor/skills-vXXX/...`, or
- manually merge the approved changes into the main `.cursor/skills/` tree using their own workflow.

This is intentional: Skill Evolve is a sidecar framework, not an online self-editing runtime.

## Runtime Data Layout

Skill code lives in:
- `.cursor/skills/skill-evolve/`

Runtime data lives in:
- `{WORKSPACE}/.skill-evolve-data/`

```text
.skill-evolve-data/
  stable/
    current_version.json
  versions/
    v001/
      version_manifest.json
    candidate_001/
      workspace/
      manifest.json
  feedback/
    raw/
    normalized/
  patch_proposals/
    proposed/
    accepted/
    rejected/
  evaluations/
    cases/
    results/
```

## Scripts

- `collect_feedback.py`: store raw feedback
- `normalize_feedback.py`: structure feedback into normalized JSON
- `propose_skill_patch.py`: create a minimal patch proposal draft
- `apply_patch_to_workspace.py`: copy target files into isolated candidate workspace and optionally apply reviewed edits
- `run_regression_gate.py`: execute evaluation assertions against candidate workspace
- `promote_skill_version.py`: promote passed candidate to a new versioned skills directory
- `reject_patch_proposal.py`: archive a proposal as rejected with a reason

## Practical Usage Modes

### Mode A — Analyze only
Generate normalized feedback and a patch proposal, but do not apply changes.

### Mode B — Candidate testing
After manually refining `planned_changes`, apply them to a candidate workspace and run the gate.

### Mode C — Promotion
If the gate passes, create `.cursor/skills-vXXX/` and update the stable pointer used by the evolve subsystem.

## Why Manual Review Is Required

`propose_skill_patch.py` generates **proposal drafts**, not authoritative code edits. The patch proposal must usually be reviewed and refined before `--apply-changes` is used, otherwise the candidate patch may be ambiguous or unsafe.

## Suggested Future Prompt to Use a Promoted Version

```text
Read and follow:
.cursor/skills-v002/one-report/SKILL.md
```

or manually merge selected approved changes back into `.cursor/skills/`.
