#!/usr/bin/env python3
"""
Propose Skill Patch Script

Generates a structured patch proposal from normalized feedback.
Proposals are minimal by design - touching only 1-3 files.

Key Features:
- Change Unit: Main file + dependency references
- Dependency Reference Scanning: Auto-identify all skills/agent configs referencing the main file
- Auto-generated Assertions: Infer regression gate assertions from planned_changes

Usage:
    python propose_skill_patch.py --feedback-id FB-123456
    python propose_skill_patch.py --feedback-id FB-123456,FB-234567
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Set

SKILL_ROOT = Path(__file__).parent.parent
WORKSPACE_ROOT = SKILL_ROOT.parent.parent.parent
DATA_ROOT = WORKSPACE_ROOT / ".skill-evolve-data"
NORMALIZED_FEEDBACK_DIR = DATA_ROOT / "feedback" / "normalized"
PROPOSED_DIR = DATA_ROOT / "patch_proposals" / "proposed"
STABLE_DIR = DATA_ROOT / "stable"
STABLE_POINTER = STABLE_DIR / "current_version.json"


def generate_proposal_id() -> str:
    """Generate a unique proposal ID in format PP-XXXXXX."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"PP-{timestamp[-6:]}"


def load_normalized_feedback(feedback_id: str) -> Dict:
    """Load normalized feedback from file."""
    feedback_path = NORMALIZED_FEEDBACK_DIR / f"{feedback_id}_normalized.json"
    if not feedback_path.exists():
        raise FileNotFoundError(f"Normalized feedback not found: {feedback_id}")
    
    with open(feedback_path, "r", encoding="utf-8") as f:
        return json.load(f)




def load_current_stable_version() -> Optional[str]:
    """Load current stable version if available."""
    if not STABLE_POINTER.exists():
        return None
    with open(STABLE_POINTER, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("version")

def infer_target_files(feedback_list: List[Dict]) -> List[str]:
    """
    Infer target skill files from feedback.
    
    Maps skill names to their SKILL.md files.
    """
    skill_to_file = {
        "grounded-research-lit": ".cursor/skills/grounded-research-lit/SKILL.md",
        "grounded-summary": ".cursor/skills/grounded-summary/SKILL.md",
        "grounded-review": ".cursor/skills/grounded-review/SKILL.md",
        "report-export": ".cursor/skills/report-export/SKILL.md",
        "document-grounding": ".cursor/skills/document-grounding/SKILL.md",
        "meeting-grounding": ".cursor/skills/meeting-grounding/SKILL.md",
        "input-router": ".cursor/skills/input-router/SKILL.md",
        "one-report": ".cursor/skills/one-report/SKILL.md",
        "remote-input": ".cursor/skills/remote-input/SKILL.md"
    }
    
    targets = set()
    for feedback in feedback_list:
        skill = feedback.get("suspected_skill", "")
        if skill in skill_to_file:
            targets.add(skill_to_file[skill])
        elif skill != "unknown":
            # Try generic mapping
            targets.add(f".cursor/skills/{skill}/SKILL.md")
    
    return list(targets)[:3]  # Max 3 files


def infer_change_scope(feedback_list: List[Dict]) -> str:
    """Infer the change scope from feedback."""
    failure_types = [f.get("failure_type", "") for f in feedback_list]
    
    if any("missing" in ft or "not_found" in ft for ft in failure_types):
        return "contract_hardening"
    elif any("documentation" in ft or "doc" in ft for ft in failure_types):
        return "documentation"
    elif any("not_" in ft or "wrong" in ft or "incorrect" in ft for ft in failure_types):
        return "local"
    
    return "minimal_feature"


def analyze_root_cause(feedback_list: List[Dict]) -> str:
    """Generate a root cause analysis from feedback."""
    stages = set(f.get("pipeline_stage", "unknown") for f in feedback_list)
    failures = set(f.get("failure_type", "unknown") for f in feedback_list)
    severities = [f.get("severity", "minor") for f in feedback_list]
    
    primary_severity = max(severities, key=lambda s: 
        {"critical": 4, "major": 3, "minor": 2, "cosmetic": 1}.get(s, 0))
    
    root_cause = f"Issue in {', '.join(stages)} stage(s): {', '.join(failures)}. "
    root_cause += f"Primary severity: {primary_severity}."
    
    return root_cause


def generate_planned_changes(feedback_list: List[Dict], target_files: List[str]) -> List[Dict]:
    """
    Generate minimal planned changes from feedback.
    
    This is a template-based generator. For actual patch proposals,
    a human should review and refine these.
    """
    changes = []
    
    for feedback in feedback_list:
        skill = feedback.get("suspected_skill", "unknown")
        failure_type = feedback.get("failure_type", "unknown")
        user_feedback = feedback.get("user_feedback", "")[:200]
        
        for target in target_files:
            if skill in target or skill == "unknown":
                change = {
                    "file": target,
                    "change_type": "modify",
                    "description": f"Address {failure_type}: {user_feedback}...",
                    "before": "",
                    "after": "",
                    "line_range": None
                }
                changes.append(change)
                break
    
    return changes[:5]  # Limit to 5 change items


def assess_risk(feedback_list: List[Dict]) -> str:
    """Assess risk level based on feedback characteristics."""
    severities = [f.get("severity", "minor") for f in feedback_list]
    
    if "critical" in severities:
        return "high"
    elif "major" in severities:
        return "medium"
    
    return "low"


# =============================================================================
# Dependency Reference Scanning
# =============================================================================

# Skill to file path mapping
SKILL_TO_FILE = {
    "grounded-research-lit": ".cursor/skills/grounded-research-lit/SKILL.md",
    "grounded-summary": ".cursor/skills/grounded-summary/SKILL.md",
    "grounded-review": ".cursor/skills/grounded-review/SKILL.md",
    "report-export": ".cursor/skills/report-export/SKILL.md",
    "document-grounding": ".cursor/skills/document-grounding/SKILL.md",
    "meeting-grounding": ".cursor/skills/meeting-grounding/SKILL.md",
    "input-router": ".cursor/skills/input-router/SKILL.md",
    "one-report": ".cursor/skills/one-report/SKILL.md",
    "audio-structuring": ".cursor/skills/audio_structuring/SKILL.md",
    "pptx-grounding": ".cursor/skills/pptx-grounding/SKILL.md",
    "table-grounding": ".cursor/skills/table-grounding/SKILL.md",
    "archive-grounding": ".cursor/skills/archive-grounding/SKILL.md",
    "meeting-audio-grounding": ".cursor/skills/meeting-audio-grounding/SKILL.md",
    "meeting-video-grounding": ".cursor/skills/meeting-video-grounding/SKILL.md",
    "remote-input": ".cursor/skills/remote-input/SKILL.md"
}

# Agent config paths
AGENT_FILES = [
    ".cursor/agents/reviewer.md",
    ".cursor/agents/router.md",
    ".cursor/agents/researcher.md",
]


def scan_dependency_references(main_skill: str, workspace_root: Path) -> List[Dict]:
    """
    Scan all dependency reference points.
    
    Find all other skills/agent configs that reference the main skill.
    
    Args:
        main_skill: Name of the skill being modified
        workspace_root: Workspace root directory
    
    Returns:
        List of dependency reference points
    """
    references = []
    main_file = SKILL_TO_FILE.get(main_skill, f".cursor/skills/{main_skill}/SKILL.md")
    
    # 1. Scan other skill files
    skills_dir = workspace_root / ".cursor" / "skills"
    if skills_dir.exists():
        for skill_file in skills_dir.rglob("SKILL.md"):
            if skill_file.name != main_file.split("/")[-1]:
                # Skip main file itself
                if str(skill_file) == str(workspace_root / main_file):
                    continue
                    
                # Check if this file references the main skill
                if _skill_references_target(skill_file, main_skill, main_file):
                    references.append({
                        "file": str(skill_file.relative_to(workspace_root)),
                        "type": "skill_reference",
                        "skill_name": main_skill,
                        "update_needed": "description_sync"
                    })
    
    # 2. Scan agent configs
    agents_dir = workspace_root / ".cursor" / "agents"
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            if _agent_references_skill(agent_file, main_skill):
                references.append({
                    "file": str(agent_file.relative_to(workspace_root)),
                    "type": "agent_config",
                    "skill_name": main_skill,
                    "update_needed": "behavior_description"
                })
    
    return references


def _skill_references_target(skill_file: Path, main_skill: str, main_file: str) -> bool:
    """Check if a skill file references the target skill."""
    try:
        content = skill_file.read_text(encoding="utf-8")
        
        # Check for skill name reference
        if main_skill in content:
            return True
        
        # Check for file path reference
        if main_file in content:
            return True
        
        # Check common reference patterns
        patterns = [
            rf'use.*\b{main_skill}\b',
            rf'\b{main_skill}\b.*skill',
            rf'\bskills?/{main_skill}/',
        ]
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
                
        return False
    except Exception:
        return False


def _agent_references_skill(agent_file: Path, main_skill: str) -> bool:
    """Check if an agent config references the target skill."""
    try:
        content = agent_file.read_text(encoding="utf-8")
        
        # Check for skill name reference
        if main_skill in content:
            return True
        
        # Check for skill-related reference patterns
        patterns = [
            rf'\b{main_skill}\b',
            rf'use.*{main_skill}',
        ]
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
                
        return False
    except Exception:
        return False


# =============================================================================
# Auto-generated Assertions
# =============================================================================

def generate_assertions_from_changes(planned_changes: List[Dict], dependency_refs: List[Dict]) -> List[Dict]:
    """
    Auto-generate assertions from planned_changes.
    
    Analyze each change:
    - If before exists → generate not_contains assertion
    - If after exists → generate contains assertion
    - Numeric changes (90→95) → generate regex_match assertion
    - Dependency references should have corresponding assertions
    
    Args:
        planned_changes: List of planned changes
        dependency_refs: List of dependency reference points
    
    Returns:
        List of assertions
    """
    assertions = []
    
    # 1. Generate assertions for main file changes
    for change in planned_changes:
        file_path = change.get("file", "")
        before = change.get("before", "")
        after = change.get("after", "")
        change_type = change.get("change_type", "")
        
        # Extract filename (without path)
        file_name = file_path.split("/")[-1]
        
        if change_type == "delete":
            # Delete change: verify original content no longer exists
            if before:
                assertions.append({
                    "name": f"old_content_removed_from_{file_name}",
                    "type": "not_contains",
                    "file": file_path,
                    "pattern": before
                })
        
        elif change_type == "add":
            # Add change: verify new content exists
            if after:
                assertions.append({
                    "name": f"new_content_added_to_{file_name}",
                    "type": "contains",
                    "file": file_path,
                    "pattern": after
                })
        
        elif change_type == "modify":
            # Modify change: verify new content exists
            if after:
                assertions.append({
                    "name": f"new_content_in_{file_name}",
                    "type": "contains",
                    "file": file_path,
                    "pattern": after
                })
        
        # 2. Detect numeric changes (90→95)
        numeric_change = _detect_numeric_change(before, after)
        if numeric_change:
            assertions.append({
                "name": f"numeric_value_updated_in_{file_name}",
                "type": "regex_match",
                "file": file_path,
                "pattern": numeric_change["new_pattern"]
            })
    
    # 3. Generate assertions for dependency references
    for ref in dependency_refs:
        ref_file = ref.get("file", "")
        ref_type = ref.get("type", "")
        skill_name = ref.get("skill_name", "")
        
        if ref_type == "skill_reference":
            # Skill reference: verify description sync
            assertions.append({
                "name": f"skill_reference_sync_{ref_file.split('/')[-1]}",
                "type": "contains",
                "file": ref_file,
                "pattern": skill_name
            })
        elif ref_type == "agent_config":
            # Agent config: verify skill reference exists
            assertions.append({
                "name": f"agent_config_sync_{ref_file.split('/')[-1]}",
                "type": "contains",
                "file": ref_file,
                "pattern": skill_name
            })
    
    # 4. Ensure not empty
    if not assertions:
        raise ValueError("Cannot auto-generate assertions: no changes with before/after content")
    
    return assertions


def _detect_numeric_change(before: str, after: str) -> Optional[Dict]:
    """
    Detect numeric changes (90→95).
    
    Returns:
        Dict with old/new patterns, or None
    """
    if not before or not after:
        return None
    
    # Extract numbers
    before_nums = re.findall(r'\d+(?:\.\d+)?', before)
    after_nums = re.findall(r'\d+(?:\.\d+)?', after)
    
    # If both have numbers and they differ
    if before_nums and after_nums and before_nums != after_nums:
        # Build new value regex pattern
        new_value = after_nums[0]
        # Preserve before/after context
        context_before = before[:20]
        context_after = after[:20]
        
        return {
            "old_value": before_nums[0],
            "new_value": new_value,
            "new_pattern": re.escape(context_after).replace(re.escape(new_value), r'\d+(?:\.\d+)?')
        }
    
    return None


def create_proposal(feedback_ids: List[str], proposal_type: str = "core_skill_patch") -> Dict:
    """
    Create a patch proposal from feedback IDs.
    
    Args:
        feedback_ids: List of normalized feedback IDs
    
    Returns:
        Patch proposal dictionary with change unit and auto-generated assertions
    """
    # Load all feedback
    feedback_list = []
    for fb_id in feedback_ids:
        fb = load_normalized_feedback(fb_id)
        fb["feedback_id"] = fb_id  # Ensure ID matches
        feedback_list.append(fb)
    
    # Generate proposal components
    proposal_id = generate_proposal_id()
    target_files = infer_target_files(feedback_list)
    change_scope = infer_change_scope(feedback_list)
    root_cause = analyze_root_cause(feedback_list)
    planned_changes = generate_planned_changes(feedback_list, target_files)
    risk_level = assess_risk(feedback_list)
    
    # Identify main skill (for dependency scanning)
    main_skill = None
    for fb in feedback_list:
        skill = fb.get("suspected_skill", "")
        if skill and skill != "unknown" and skill in SKILL_TO_FILE:
            main_skill = skill
            break
    
    # Scan dependency references (part of change unit)
    dependency_references = []
    if main_skill:
        dependency_references = scan_dependency_references(main_skill, WORKSPACE_ROOT)
    
    # Determine required_regression_cases (based on affected skills)
    required_cases = []
    for fb in feedback_list:
        stage = fb.get("pipeline_stage", "")
        if stage:
            required_cases.append(f"case_{stage}_basic")
    # Also include dependency reference-related cases
    for ref in dependency_references:
        ref_type = ref.get("type", "")
        if ref_type == "skill_reference":
            required_cases.append("case_skill_integration")
        elif ref_type == "agent_config":
            required_cases.append("case_agent_integration")
    
    # Auto-generate assertions (for regression gate)
    try:
        auto_assertions = generate_assertions_from_changes(planned_changes, dependency_references)
    except ValueError as e:
        # If auto-generation fails, use empty assertions
        auto_assertions = []
        print(f"Warning: {e}. Manual assertion creation required.")
    
    proposal = {
        "proposal_id": proposal_id,
        "proposal_type": proposal_type,
        "based_on_version": load_current_stable_version(),
        "feedback_ids": feedback_ids,
        "target_files": target_files,
        "change_scope": change_scope,
        "suspected_root_cause": root_cause,
        "planned_changes": planned_changes,
        "risk_level": risk_level,
        "required_regression_cases": list(set(required_cases)),
        
        # 改动单元（Change Unit）
        "change_unit": {
            "main_file": SKILL_TO_FILE.get(main_skill, target_files[0] if target_files else ""),
            "main_skill": main_skill,
            "dependency_references": dependency_references,
            "description": "A change unit includes the main skill file and all dependent references that must stay in sync."
        },
        
        # 自动生成的断言
        "auto_generated_assertions": auto_assertions,
        
        "rollback_plan": {
            "enabled": True,
            "method": "version_manifest",
            "steps": [
                "Revert files to previous version manifest state",
                "Restore from git if available",
                "Mark proposal as rejected"
            ]
        },
        "manual_review_required": True,
        "ready_to_apply": False,
        "status": "proposed",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "created_by": "automated_proposer",
        "notes": "Auto-generated proposal with 改动单元 and assertions. Review and refine before acceptance."
    }
    
    return proposal


def save_proposal(proposal: Dict) -> Path:
    """Save proposal to file."""
    PROPOSED_DIR.mkdir(parents=True, exist_ok=True)
    
    output_path = PROPOSED_DIR / f"{proposal['proposal_id']}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(proposal, f, indent=2, ensure_ascii=False)
    
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate patch proposal from normalized feedback",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python propose_skill_patch.py --feedback-id FB-123456
    python propose_skill_patch.py --feedback-id FB-123456,FB-234567
        """
    )
    
    parser.add_argument(
        "--feedback-id", "-f",
        required=True,
        help="Normalized feedback ID(s), comma-separated"
    )
    parser.add_argument(
        "--proposal-type",
        choices=["core_skill_patch", "sidecar_feature_patch", "documentation_patch"],
        default="core_skill_patch",
        help="Proposal type classification"
    )
    
    args = parser.parse_args()
    
    try:
        feedback_ids = [fb.strip() for fb in args.feedback_id.split(",")]
        
        if len(feedback_ids) > 5:
            print("Warning: Large number of feedback items. Consider splitting into multiple proposals.")
        
        proposal = create_proposal(feedback_ids, proposal_type=args.proposal_type)
        output_path = save_proposal(proposal)
        
        print(f"Patch proposal created successfully!")
        print(f"Proposal ID: {proposal['proposal_id']}")
        print(f"Target Files: {', '.join(proposal['target_files'])}")
        print(f"Change Scope: {proposal['change_scope']}")
        print(f"Risk Level: {proposal['risk_level']}")
        print(f"Required Cases: {', '.join(proposal['required_regression_cases'])}")
        
        # Change unit info
        change_unit = proposal.get("change_unit", {})
        main_skill = change_unit.get("main_skill", "unknown")
        dep_refs = change_unit.get("dependency_references", [])
        
        print(f"\n=== Change Unit ===")
        print(f"Main Skill: {main_skill}")
        print(f"Main File: {change_unit.get('main_file', 'N/A')}")
        print(f"Dependency References: {len(dep_refs)}")
        for ref in dep_refs:
            print(f"  - {ref.get('file', 'unknown')}: {ref.get('type', 'unknown')} ({ref.get('update_needed', 'N/A')})")
        
        # Auto-generated assertions
        auto_assertions = proposal.get("auto_generated_assertions", [])
        print(f"\n=== Auto-generated Assertions ===")
        print(f"Total Assertions: {len(auto_assertions)}")
        for assertion in auto_assertions:
            print(f"  - {assertion.get('name', 'unnamed')}: {assertion.get('type', 'unknown')} on {assertion.get('file', 'unknown')}")
        
        print(f"\nSaved to: {output_path}")
        print(f"\nNOTE: Review and refine planned_changes before promoting to candidate.")
        
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())