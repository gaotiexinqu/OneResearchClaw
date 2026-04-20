---
name: skill-evolve
description: Optional sidecar skill for controlled feedback-driven skill evolution. Not part of the default pipeline. Only activates when explicitly requested.
---

# Skill Evolve (Optional Sidecar)

**This is an OPTIONAL sidecar capability, NOT part of the default pipeline.**

---

## What This Skill Is

Skill Evolve is a **controlled, opt-in framework** for turning real user feedback into skill improvements over time.

It is designed to:
- Collect and normalize user feedback
- Generate minimal patch proposals
- Require manual review/refinement of generated patch proposals before real patch application
- Test reviewed patches in isolated workspaces
- Run regression gates
- Promote verified patches to new stable versions
- Preserve the default `.cursor/skills/` tree unchanged unless a human later chooses to merge approved changes manually

---

## What This Skill Is NOT

This skill must NOT:
- Run automatically during normal report generation
- Modify stable skills without explicit evolve flow
- Replace human judgment with automated decisions
- Make the default pipeline behave differently

---

## When to Use This Skill

Use this skill when:
- User explicitly requests "skill evolution" or "feedback-driven improvement"
- User provides feedback that should be tracked and potentially addressed
- User wants to analyze and improve the skill framework

Do NOT use this skill when:
- Generating reports (use `one-report` instead)
- Running normal pipeline operations
- User has not explicitly requested skill evolution

---

## Controlled Evolve Loop Flow

When explicitly invoked, follow this controlled flow:

### Step 1: Collect Feedback

Use `collect_feedback.py` to ingest raw user feedback:

```bash
python .cursor/skills/skill-evolve/scripts/collect_feedback.py --interactive
# OR
python .cursor/skills/skill-evolve/scripts/collect_feedback.py --text "feedback text"
# OR
python .cursor/skills/skill-evolve/scripts/collect_feedback.py --file /path/to/feedback.txt
```

Raw feedback preserves user language and is saved to:
`{WORKSPACE}/.skill-evolve-data/feedback/raw/`

### Step 2: Normalize Feedback

Convert raw feedback to structured format:

```bash
python .cursor/skills/skill-evolve/scripts/normalize_feedback.py \
    --feedback-id FB-XXXXXX \
    --stage <grounding|research|summary|review|export> \
    --skill <skill-name>
```

Normalized feedback is saved to:
`{WORKSPACE}/.skill-evolve-data/feedback/normalized/`

### Step 3: Propose Minimal Patch

Generate a patch proposal from normalized feedback:

```bash
python .cursor/skills/skill-evolve/scripts/propose_skill_patch.py \
    --feedback-id FB-XXXXXX,FB-YYYYYY
```

Patch proposals are saved to:
`{WORKSPACE}/.skill-evolve-data/patch_proposals/proposed/`

#### Change Unit

A patch proposal is not just a single modified skill file, but a complete **change unit** containing:

1. **Main File**: The skill being modified
2. **Dependency References**: All other skills/agent configs that reference this skill
3. **Auto-generated Assertions**: For regression gate verification

#### Dependency Reference Scanning

When generating a proposal, the agent must:

1. **Identify Main File**: Determine which skill is the modification target
2. **Scan Dependencies**: Search all skills and agent configs to find references to the main file
   - Check other skills' "What This Skill Is" or invocation chain descriptions
   - Check agent configs for skill references
   - Check prompting templates for skill paths
3. **Declare Reference Points**: List all locations requiring sync updates in the proposal
4. **Analyze Impact Scope**: Distinguish between "description update only" and "behavior sync required" references

**Example**:
If the modification target is `grounded-review`:
- Main File: `.cursor/skills/grounded-review/SKILL.md`
- Dependency References:
  - `.cursor/skills/one-report/SKILL.md` (as sub-process reference)
  - `.cursor/agents/reviewer.md` (agent config)

#### Auto-generated Assertions

The proposal script should auto-generate assertions rather than relying on manual creation:

1. **Analyze planned_changes**:
   - If `before` content exists → generate `not_contains` assertion to verify old content removed
   - If `after` content exists → generate `contains` assertion to verify new content added
   - Numeric changes (90→95) → generate `regex_match` assertion

2. **Minimal Assertion Set**:
   - Core semantic changes must be covered by assertions
   - Avoid redundant assertions (one `contains` can verify content without splitting)
   - Empty tests cannot pass vacuously (reject if no changes)

3. **Cross-file Assertions**:
   - If dependency references also need updates, those points should have corresponding assertions
   - Ensure consistency between main file and reference points

**Auto-generated Assertion Example** (threshold 90→95):
```json
{
  "assertions": [
    {
      "name": "threshold_updated_to_95",
      "type": "contains",
      "file": "grounded-review/SKILL.md",
      "pattern": "weighted total >= 95"
    },
    {
      "name": "old_threshold_90_removed",
      "type": "not_contains",
      "file": "grounded-review/SKILL.md",
      "pattern": "weighted total >= 90"
    },
    {
      "name": "one_report_sync",
      "type": "contains",
      "file": "one-report/SKILL.md",
      "pattern": "review threshold"
    }
  ]
}
```

### Step 4: Review and Refine Patch Proposal

Before applying any changes, review and refine the proposed `planned_changes` so they contain concrete, safe edits.

Do **not** treat an auto-generated proposal as ready-to-apply by default.

### Step 5: Apply Patch Candidate

Apply the reviewed patch to an isolated workspace for testing:

```bash
python .cursor/skills/skill-evolve/scripts/apply_patch_to_workspace.py \
    --proposal-id PP-XXXXXX \
    --apply-changes
```

This creates a candidate workspace without modifying stable skills.

### Step 6: Run Regression Gate

Test the patch against evaluation cases:

```bash
python .cursor/skills/skill-evolve/scripts/run_regression_gate.py \
    --proposal-id PP-XXXXXX
```

Results are saved to:
`{WORKSPACE}/.skill-evolve-data/evaluations/results/`

#### Regression Gate for Change Units

Regression gate must verify the complete change unit:

1. **Main File Assertions**: Verify core changes in the main skill file
2. **Dependency Reference Assertions**: Verify sync updates for all dependency reference points
3. **Consistency Checks**: Ensure descriptions/behaviors match between main file and references

#### Assertion File Path Resolution

The `file` field in assertions is resolved relative to workspace root:

- `grounded-review/SKILL.md` → `{workspace}/grounded-review/SKILL.md`
- `one-report/SKILL.md` → `{workspace}/one-report/SKILL.md`
- `.cursor/agents/reviewer.md` → `{workspace}/.cursor/agents/reviewer.md`

#### Failure Handling

If any assertion fails (main file or dependency reference), gate result is `reject`:

```json
{
  "decision": "reject",
  "reason": "Dependency reference out of sync: one-report/SKILL.md missing review threshold update"
}
```

### Step 7: Promote or Reject

If gate passes, promote the candidate:

**Standard promotion** (creates versioned directory only):
```bash
python .cursor/skills/skill-evolve/scripts/promote_skill_version.py \
    --gate-id GR-XXXXXX \
    --notes "Description of changes"
```

**Sync promotion** (also updates stable skills/):
```bash
python .cursor/skills/skill-evolve/scripts/promote_skill_version.py \
    --gate-id GR-XXXXXX \
    --notes "Description of changes" \
    --sync
```

**Result (standard):**
- Original `.cursor/skills/` remains **untouched**
- New `.skill-evolve-data/skills-versions/v002/` created with patches applied

**Result (--sync):**
- Versioned directory created as above
- Additionally: stable `.cursor/skills/` is updated with approved patches
- Consistency checks run to ensure no old patterns remain

**Consistency Check Feature:**
The promote script now runs **full line-by-line checks** on patched files to ensure:
- No remaining old patterns (e.g., `weighted_total >= 90` when it should be `>= 95`)
- Cross-file consistency (all related files updated together)
- Report any missed updates before finalizing

If gate fails, the patch is rejected and stable version remains unchanged.

---

## Version Management

### Stable Version Pointer

Located at: `{WORKSPACE}/.skill-evolve-data/stable/current_version.json`

Contains:
- Current stable version ID
- Path to version manifest
- Last update timestamp

### Version Manifests

Located at: `{WORKSPACE}/.skill-evolve-data/versions/vXXX/version_manifest.json`

Contains:
- Version ID
- Based-on version
- Accepted patch IDs
- Passed gate IDs
- Rollback information

---

## Safety Principles

1. **Opt-in Only**: Nothing runs automatically
2. **Isolation**: Patches are tested in isolated workspaces
3. **Human Approval**: Promotion requires successful gate + explicit promotion call
4. **Rollback Ready**: Every stable version knows its rollback target
5. **No Overwrite**: Stable skills are never modified without explicit promotion

---

## Directory Layout

### Skill Code (in `.cursor/skills/skill-evolve/`)
```
.cursor/
  skills/
    skill-evolve/
      SKILL.md          # This file
      scripts/          # Evolution workflow scripts
      schemas/          # JSON schemas
```

### Data Directory (in `{WORKSPACE}/.skill-evolve-data/`)
```
{WORKSPACE}/
  .skill-evolve-data/
    stable/
      current_version.json
    versions/
      v001/
        version_manifest.json
      vXXX/
    skills-versions/      # Versioned skill+agent snapshots (created on promotion)
      v001/
        agents/           # copy of .cursor/agents/
        skills/           # copy of .cursor/skills/
      v002/
        agents/
        skills/
    feedback/
      raw/              # Original user feedback
      normalized/       # Structured feedback
    patch_proposals/
      proposed/        # Generated proposals
      accepted/        # Successfully promoted
      rejected/        # Failed or rejected
    evaluations/
      cases/           # Evaluation case definitions
      results/         # Gate execution results
```

### Key Design Principle
- **Skill code** stays in `.cursor/skills/skill-evolve/` (git-managed)
- **Versioned snapshots** go to `.skill-evolve-data/skills-versions/` (each version contains both `agents/` and `skills/` sub-dirs)
- **Runtime data** goes to `{WORKSPACE}/.skill-evolve-data/` (local, git-ignored)

---

## Example Invocation

User explicitly requests skill evolution:

```
Use the skill-evolve framework to analyze my feedback and propose improvements.

My feedback: The grounded-research-lit skill sometimes opens fewer papers than the `MIN_OPENED_PAPERS` threshold set by `research_mode`. The cursor backend should ensure the configured minimum number of unique papers are opened before proceeding to summary.

Feedback ID reference: FB-280408 (collected earlier)
```

Agent would then:
1. Normalize the feedback with appropriate stage and skill
2. Propose a minimal patch
3. Apply to candidate workspace
4. Run regression gate
5. Report results for human decision

---

## Summary

| Aspect | Default Pipeline | Skill Evolve |
|--------|-----------------|--------------|
| Activation | Automatic | Explicit request only |
| Purpose | Report generation | Skill improvement |
| Modifications | None | Controlled via gate |
| Automatic changes | Yes | No |
| Human approval | N/A | Required for promotion |


## Important Activation Rule

Promotion updates the Skill Evolve stable pointer and creates a new versioned snapshot such as `.skill-evolve-data/skills-versions/v002/`, which contains **both** `agents/` and `skills/` sub-directories. This ensures every version is self-contained and reproducible.

It does **not** automatically rewrite ordinary prompts or make the default `.cursor/skills/` or `.cursor/agents/` trees behave differently.

If a user wants to use a promoted version in a future chat, they must explicitly point the prompt at that versioned snapshot path or manually merge the approved changes back into `.cursor/skills/` and `.cursor/agents/`.

## Rejection Path

If a proposal is not suitable or fails the regression gate, archive it explicitly using:

```bash
python .cursor/skills/skill-evolve/scripts/reject_patch_proposal.py \
    --proposal-id PP-XXXXXX \
    --reason "Why this proposal is rejected"
```

Do not leave failed proposals ambiguous if you already know they should not be promoted.
