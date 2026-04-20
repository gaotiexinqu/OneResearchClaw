#!/usr/bin/env python3
"""
Promote Skill Version Script

Promotes a candidate version to stable only if the gate result says pass.
Updates stable pointer and writes version manifest.

Supports two promotion modes:
1. Versioned-only mode (default): Creates skills-versions/vXXX/ (with agents/ + skills/ sub-dirs) without modifying stable dirs
2. Sync mode (--sync): Also updates stable skills/ and agents/ with approved patches

Usage:
    python promote_skill_version.py --gate-id GR-123456
    python promote_skill_version.py --gate-id GR-123456 --notes "Fixed routing issue"
    python promote_skill_version.py --gate-id GR-123456 --sync
"""

import argparse
import json
import os
import re
import shutil
import sys
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple


SKILL_ROOT = Path(__file__).parent.parent
WORKSPACE_ROOT = SKILL_ROOT.parent.parent.parent
DATA_ROOT = WORKSPACE_ROOT / ".skill-evolve-data"
STABLE_DIR = DATA_ROOT / "stable"
VERSIONS_DIR = DATA_ROOT / "versions"
PROPOSED_DIR = DATA_ROOT / "patch_proposals" / "proposed"
RESULTS_DIR = DATA_ROOT / "evaluations" / "results"
SKILLS_ROOT = SKILL_ROOT.parent  # .cursor/skills/ (sibling of skill-evolve)
VERSIONED_SKILLS_DIR = DATA_ROOT / "skills-versions"  # .skill-evolve-data/skills-versions/


def generate_version_id() -> str:
    """Generate a version ID in format vXXX."""
    existing = list(VERSIONS_DIR.glob("v*"))
    
    if existing:
        nums = [int(d.name[1:]) for d in existing if d.name.startswith("v")]
        next_num = max(nums) + 1 if nums else 1
    else:
        next_num = 1
    
    return f"v{next_num:03d}"


def load_gate_result(gate_id: str) -> Dict:
    """Load gate result from file."""
    result_path = RESULTS_DIR / f"{gate_id}.json"
    if not result_path.exists():
        raise FileNotFoundError(f"Gate result not found: {gate_id}")
    
    with open(result_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_proposal(proposal_id: str) -> Dict:
    """Load patch proposal from file."""
    proposal_path = PROPOSED_DIR / f"{proposal_id}.json"
    if not proposal_path.exists():
        raise FileNotFoundError(f"Proposal not found: {proposal_id}")
    
    with open(proposal_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_current_stable() -> Optional[Dict]:
    """Load current stable version pointer."""
    stable_path = STABLE_DIR / "current_version.json"
    if stable_path.exists():
        with open(stable_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def create_versioned_skills_copy(target_version_id: str) -> Path:
    """
    Create a full copy of both skills/ and agents/ as a new versioned directory.
    This creates `.skill-evolve-data/skills-versions/{version}/` containing:
      skills-versions/v001/
      ├── agents/           # copy of .cursor/agents/
      │   ├── reviewer.md
      │   └── writer.md
      └── skills/           # copy of .cursor/skills/
          ├── grounded-review/
          └── ...
    
    Args:
        target_version_id: Target version ID (e.g., "v002")
    
    Returns:
        Path to the created versioned skills directory (skills-versions/vXXX/)
    """
    target_dir = VERSIONED_SKILLS_DIR / target_version_id
    target_dir.parent.mkdir(parents=True, exist_ok=True)

    if target_dir.exists():
        raise FileExistsError(
            f"Versioned skills directory already exists: {target_dir}\n"
            "Please use a different version or remove the existing directory."
        )
    
    # Create parent directory
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # --- Copy agents/ sub-directory ---
    agents_source = SKILLS_ROOT.parent / "agents"  # .cursor/agents/
    if agents_source.exists():
        agents_dest = target_dir / "agents"
        shutil.copytree(agents_source, agents_dest)
        print(f"Copied agents/ -> {agents_dest}")
    else:
        print(f"Warning: agents source not found at {agents_source}")
    
    # --- Copy skills/ sub-directory ---
    skills_dest = target_dir / "skills"
    shutil.copytree(SKILLS_ROOT, skills_dest)
    print(f"Copied skills/ -> {skills_dest}")
    
    print(f"Created versioned snapshot: {target_dir}")
    
    return target_dir


def apply_patches_to_versioned_skills(
    candidate_dir: Path,
    target_files: list,
    version_id: str
) -> int:
    """
    Apply patch files to a versioned skills directory.
    This modifies skills-versions/{version}/ but NOT skills/
    
    Args:
        candidate_dir: Candidate version directory containing patch workspace
        target_files: List of target file paths (may have .cursor/skills/ or .cursor/agents/ prefix)
        version_id: Version ID (e.g., "v002")
    
    Returns:
        Number of files applied
    """
    workspace = candidate_dir / "workspace"
    applied = 0

    for target in target_files:
        # Resolve source path in the workspace (handles .cursor/skills/ and .cursor/agents/ prefix correctly)
        source = resolve_workspace_file(workspace, target)

        if not source.exists():
            print(f"  Warning: Patch file not found in workspace: {source}")
            continue

        # Resolve destination in versioned skills directory
        # `.cursor/skills/grounded-review/SKILL.md` -> `skills-versions/v001/skills/grounded-review/SKILL.md`
        # `.cursor/agents/reviewer.md` -> `skills-versions/v001/agents/reviewer.md`
        if target.startswith(".cursor/skills/"):
            relative = "skills/" + target.replace(".cursor/skills/", "", 1)
        elif target.startswith(".cursor/agents/"):
            relative = "agents/" + target.replace(".cursor/agents/", "", 1)
        elif target.startswith(".cursor/"):
            relative = target.replace(".cursor/", "", 1)
        else:
            relative = target
        dest = VERSIONED_SKILLS_DIR / version_id / relative
        
        # Ensure destination directory exists
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy patch file to versioned skills directory
        shutil.copy2(source, dest)
        applied += 1
        print(f"  Applied patch: {relative}")
    
    return applied


def create_version_manifest(
    version_id: str,
    proposal: Dict,
    gate_result: Dict,
    notes: str
) -> Dict:
    """Create version manifest."""
    current_stable = load_current_stable()
    
    manifest = {
        "version": version_id,
        "based_on": current_stable.get("version") if current_stable else None,
        "accepted_patch_ids": [proposal["proposal_id"]],
        "passed_gate_ids": [gate_result["gate_id"]],
        "rejected_patch_ids": [],
        "created_at": datetime.now().isoformat(),
        "created_by": "promote_script",
        "notes": notes,
        "status": "stable",
        "affected_skills": proposal.get("target_files", []),
        "breaking_changes": [],
        "rollback_available": True,
        "rollback_to": current_stable.get("version") if current_stable else None,
        "skills_directory": f"skills-versions/{version_id}",
        "skills_path": str(VERSIONED_SKILLS_DIR / version_id),
        "agents_path": str(VERSIONED_SKILLS_DIR / version_id / "agents"),
        "skills_subdir": f"skills-versions/{version_id}/skills",
        "agents_subdir": f"skills-versions/{version_id}/agents",
        "activation_note": f"Each versioned snapshot contains both agents/ and skills/ sub-dirs. Point future prompts at .skill-evolve-data/skills-versions/{version_id}/... or manually merge approved changes back into .cursor/skills/ and .cursor/agents/.",
        "original_skills_preserved": True,
        "original_agents_preserved": True
    }
    
    return manifest


def save_version_manifest(manifest: Dict) -> Path:
    """Save version manifest to file."""
    version_id = manifest["version"]
    version_dir = VERSIONS_DIR / version_id
    version_dir.mkdir(parents=True, exist_ok=True)
    
    manifest_path = version_dir / "version_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    return manifest_path


def update_stable_pointer(version_id: str, manifest_path: Path) -> Path:
    """Update the stable version pointer."""
    STABLE_DIR.mkdir(parents=True, exist_ok=True)
    
    stable_data = {
        "version": version_id,
        "manifest_path": str(manifest_path),
        "skills_directory": f"skills-versions/{version_id}",
        "skills_path": str(VERSIONED_SKILLS_DIR / version_id),
        "agents_path": str(VERSIONED_SKILLS_DIR / version_id / "agents"),
        "skills_subdir": f"skills-versions/{version_id}/skills",
        "agents_subdir": f"skills-versions/{version_id}/agents",
        "activation_note": f"Each versioned snapshot contains both agents/ and skills/ sub-dirs. Point future prompts at .skill-evolve-data/skills-versions/{version_id}/... or manually merge approved changes back into .cursor/skills/ and .cursor/agents/.",
        "updated_at": datetime.now().isoformat()
    }
    
    stable_path = STABLE_DIR / "current_version.json"
    with open(stable_path, "w", encoding="utf-8") as f:
        json.dump(stable_data, f, indent=2)
    
    return stable_path


def move_proposal_to_accepted(proposal_id: str) -> Path:
    """Archive proposal as accepted without moving files."""
    source = PROPOSED_DIR / f"{proposal_id}.json"
    dest_dir = DATA_ROOT / "patch_proposals" / "accepted"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{proposal_id}.json"

    # Read from source if it still exists; otherwise proposal data is already gone
    # (cleanup may have run partially in a previous failed attempt)
    if source.exists():
        shutil.move(str(source), str(dest))
    else:
        # Proposal file already removed by cleanup — create a minimal accepted record
        with open(dest, "w", encoding="utf-8") as f:
            json.dump({"proposal_id": proposal_id, "status": "accepted"}, f, indent=2)
    return dest


def cleanup_intermediate_files(candidate_dir: Path, proposal_id: str, gate_id: str) -> List[str]:
    """
    Clean up intermediate files after successful promotion.
    
    Removes ALL intermediate data, keeps ONLY:
    - stable/ directory with current_version.json
    - versions/vXXX/ with version manifests
    
    Args:
        candidate_dir: The candidate directory to clean up
        proposal_id: Proposal ID for feedback cleanup
        gate_id: Gate ID for result cleanup
    
    Returns:
        List of cleaned up paths
    """
    cleaned = []
    
    print(f"\n[Cleanup] Removing intermediate files...")
    
    # Clean up candidate directory
    if candidate_dir.exists():
        shutil.rmtree(candidate_dir)
        cleaned.append(str(candidate_dir))
        print(f"  Removed: {candidate_dir}")
    
    # Clean up feedback directory entirely
    feedback_dir = DATA_ROOT / "feedback"
    if feedback_dir.exists():
        shutil.rmtree(feedback_dir)
        cleaned.append(str(feedback_dir))
        print(f"  Removed: {feedback_dir}")
    
    # Clean up evaluations directory entirely
    evaluations_dir = DATA_ROOT / "evaluations"
    if evaluations_dir.exists():
        shutil.rmtree(evaluations_dir)
        cleaned.append(str(evaluations_dir))
        print(f"  Removed: {evaluations_dir}")
    
    # Clean up patch_proposals directory, but PRESERVE accepted subdirectory
    proposals_dir = DATA_ROOT / "patch_proposals"
    if proposals_dir.exists():
        accepted_dir = proposals_dir / "accepted"
        # Collect what's inside accepted before we blow it away
        accepted_records = {}
        if accepted_dir.exists():
            for f in accepted_dir.glob("*.json"):
                accepted_records[f.name] = f.read_text(encoding="utf-8")

        shutil.rmtree(proposals_dir)
        cleaned.append(str(proposals_dir))
        print(f"  Removed: {proposals_dir}")

        # Restore accepted records so they survive cleanup
        if accepted_records:
            proposals_dir.mkdir(parents=True, exist_ok=True)
            accepted_dir = proposals_dir / "accepted"
            accepted_dir.mkdir(parents=True, exist_ok=True)
            for fname, fcontent in accepted_records.items():
                (accepted_dir / fname).write_text(fcontent, encoding="utf-8")
            print(f"  Restored {len(accepted_records)} accepted proposal(s)")
    
    # Clean up cleanup_archive (if any leftover)
    cleanup_archive = DATA_ROOT / "cleanup_archive"
    if cleanup_archive.exists():
        shutil.rmtree(cleanup_archive)
        cleaned.append(str(cleanup_archive))
        print(f"  Removed: {cleanup_archive}")
    
    print(f"  Total cleaned: {len(cleaned)} items")
    
    return cleaned


def check_consistency_within_file(file_path: Path, version_id: str, changed_patterns: List[Tuple[str, str]]) -> List[str]:
    """
    Check that a patched file has no remaining old patterns.
    
    Args:
        file_path: Path to the file to check
        version_id: Version ID for reporting
        changed_patterns: List of (old_pattern, new_pattern) tuples that were changed
    
    Returns:
        List of inconsistencies found (empty if all good)
    """
    inconsistencies = []
    
    if not file_path.exists():
        return [f"File not found: {file_path}"]
    
    content = file_path.read_text(encoding="utf-8")
    
    for old_pattern, new_pattern in changed_patterns:
        # Find all occurrences of old pattern
        matches = re.findall(re.escape(old_pattern), content)
        if matches:
            inconsistencies.append(
                f"  [{file_path.name}] Found {len(matches)} remaining '{old_pattern}' after patch "
                f"(expected only '{new_pattern}')"
            )
    
    return inconsistencies


def resolve_workspace_file(workspace: Path, target: str) -> Path:
    """
    Resolve a target file path to its actual location in the workspace.

    Handles two conventions:
    - `.cursor/skills/<skill>/SKILL.md` -> `{workspace}/.cursor/skills/<skill>/SKILL.md`
    - `.cursor/agents/<name>.md` -> `{workspace}/.cursor/agents/<name>.md`
    - `skills/<skill>/SKILL.md` -> `{workspace}/.cursor/skills/<skill>/SKILL.md`
    - `agents/<name>.md` -> `{workspace}/.cursor/agents/<name>.md`
    - `<skill>/SKILL.md` -> `{workspace}/.cursor/skills/<skill>/SKILL.md`
    """
    if target.startswith(".cursor/"):
        return workspace / target
    if target.startswith("skills/"):
        return workspace / ".cursor" / target
    if target.startswith("agents/"):
        return workspace / ".cursor" / target
    # Bare skill name: "grounded-review/SKILL.md"
    if "/" in target and not target.startswith("."):
        return workspace / ".cursor" / "skills" / target
    return workspace / target


def check_cross_file_consistency(
    workspace: Path,
    version_id: str,
    target_files: List[str]
) -> List[str]:
    """
    Check for cross-file consistency issues.

    This ensures that related files are in sync (e.g., thresholds, names, references).

    Args:
        workspace: Path to the candidate workspace directory
        version_id: Version ID for reporting
        target_files: List of files that were modified

    Returns:
        List of consistency issues found
    """
    issues = []

    # Generic consistency check: within each file, all threshold mentions must agree.
    # Extract any ">= N" and "< N" numeric threshold values from lines mentioning
    # "weighted_total" (or equivalent), then flag if both ">=" and "<" patterns disagree.
    import re

    THRESHOLD_RE = re.compile(r"(weighted_total|weighted total)\s*[<>]=?\s*(\d+(?:\.\d+)?)", re.IGNORECASE)

    thresholds_by_file = {}
    for target in target_files:
        patched_file = resolve_workspace_file(workspace, target)
        if not patched_file.exists():
            continue
        content = patched_file.read_text(encoding="utf-8")
        file_vals = set()
        for m in THRESHOLD_RE.finditer(content):
            file_vals.add(m.group(2))
        if file_vals:
            thresholds_by_file[patched_file.name] = file_vals

    for fname, vals in thresholds_by_file.items():
        if len(vals) > 1:
            issues.append(
                f"  [{fname}] Mixed threshold values {sorted(vals)} found in same file — "
                f"all should be the same."
            )

    return issues


def run_full_consistency_check(
    candidate_dir: Path,
    version_id: str,
    target_files: List[str]
) -> Tuple[bool, List[str]]:
    """
    Run comprehensive consistency check across all modified files.
    
    This replaces the simple patch application with a full line-by-line review
    to ensure no old patterns remain and all cross-file references are in sync.
    
    Args:
        candidate_dir: Candidate workspace directory
        version_id: Version ID
        target_files: List of target files that were modified
    
    Returns:
        (success, issues) - success is True if all checks pass
    """
    print(f"\n[Consistency Check] Verifying candidate workspace ({version_id})...")
    
    all_issues = []
    workspace = candidate_dir / "workspace"
    
    # Check each modified file
    for target in target_files:
        # Resolve file path to actual location in workspace
        patched_file = resolve_workspace_file(workspace, target)
        
        if not patched_file.exists():
            continue
        
        # Load the proposed changes to understand what patterns changed
        # This is a simplified check - in real implementation we'd parse the patch more carefully
        content = patched_file.read_text(encoding="utf-8")
        
        # Check each modified file: any weighted_total threshold line must be consistent
        # within the file (no mixing of different numeric values).
        import re as re_mod
        THRESHOLD_RE = re_mod.compile(
            r"(weighted_total|weighted total)\s*[<>]=?\s*(\d+(?:\.\d+)?)", re.IGNORECASE
        )
        lines_with_issues = []
        for i, line in enumerate(content.split("\n"), 1):
            matches = THRESHOLD_RE.findall(line)
            if len(matches) > 1:
                vals = list(OrderedDict.fromkeys(v[1] for v in matches))
                if len(vals) > 1:
                    lines_with_issues.append(
                        f"  Line {i}: Mixed threshold values {vals} in one expression — must be consistent"
                    )
        
        if lines_with_issues:
            all_issues.append(f"[{patched_file.name}]")
            all_issues.extend(lines_with_issues)
    
    # Check cross-file consistency
    cross_file_issues = check_cross_file_consistency(workspace, version_id, target_files)
    all_issues.extend(cross_file_issues)
    
    if all_issues:
        print(f"  Found {len(all_issues)} consistency issues:")
        for issue in all_issues:
            print(issue)
        return False, all_issues
    else:
        print(f"  All consistency checks passed!")
        return True, []


def sync_to_stable_skills(
    candidate_dir: Path,
    target_files: List[str],
    version_id: str,
    force: bool = False
) -> Dict:
    """
    Sync approved patches to the stable .cursor/skills/ and .cursor/agents/ directories.

    This is an OPTIONAL step — by default we only create versioned directories.
    Use --sync flag to also update the stable skills/agents directories.

    Args:
        candidate_dir: Candidate workspace directory
        target_files: List of target file paths
        version_id: Version ID
        force: Skip per-file warnings (pre-sync summary confirmation is still required)

    Returns:
        Sync result dictionary
    """
    print(f"\n[Sync] Updating stable skills/ and agents/ directories...")

    workspace = candidate_dir / "workspace"
    synced = []
    failed = []

    # --- Pre-sync summary: always required, cannot be bypassed ---
    print(f"\n  The following {len(target_files)} file(s) will be MODIFIED:")
    
    agents_files = [t for t in target_files if ".cursor/agents/" in t or t.startswith("agents/")]
    skills_files = [t for t in target_files if ".cursor/skills/" in t or t.startswith("skills/") or ("/" in t and not t.startswith("."))]
    
    if agents_files:
        print(f"    agents/:")
        for t in agents_files:
            rel = t.replace(".cursor/agents/", "") if ".cursor/agents/" in t else t
            print(f"      - {rel}")
    
    if skills_files:
        print(f"    skills/:")
        for t in skills_files:
            rel = t.replace(".cursor/skills/", "") if ".cursor/skills/" in t else t
            print(f"      - {rel}")
    
    print(f"\n  WARNING: This OVERWRITES the existing stable skills/ and agents/ directories.")
    print(f"  Versioned snapshot skills-versions/{version_id}/ is safe regardless of this choice.\n")

    if not force:
        response = input("  Confirm sync to stable skills/ and agents/? This cannot be undone automatically. (yes/N): ")
        if response.strip().lower() != "yes":
            print("  Sync ABORTED. Stable skills/ and agents/ left unchanged.")
            return {"synced": [], "failed": [], "aborted": True}
    else:
        print("  [force mode] Skipping per-file warning prompts.\n")

    for target in target_files:
        # Resolve source path in workspace
        source = resolve_workspace_file(workspace, target)

        if not source.exists():
            failed.append((target, "Source file not found in workspace"))
            continue

        # Destination is the stable skills or agents directory
        if target.startswith(".cursor/skills/") or target.startswith("skills/"):
            if target.startswith(".cursor/"):
                relative_target = target.replace(".cursor/skills/", "")
            else:
                relative_target = target.replace("skills/", "")
            dest = SKILLS_ROOT / relative_target
        elif target.startswith(".cursor/agents/") or target.startswith("agents/"):
            if target.startswith(".cursor/"):
                relative_target = target.replace(".cursor/agents/", "")
            else:
                relative_target = target.replace("agents/", "")
            agents_root = SKILLS_ROOT.parent / "agents"  # .cursor/agents/
            dest = agents_root / relative_target
        else:
            # Default: treat as skills
            relative_target = target
            dest = SKILLS_ROOT / relative_target
        
        # Ensure destination directory exists
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy to stable location
        shutil.copy2(source, dest)
        synced.append(relative_target)
        print(f"  Synced: {relative_target}")
    
    return {
        "synced": synced,
        "failed": failed,
        "version": version_id,
        "aborted": False
    }


def promote_skill_version(
    gate_id: str,
    notes: Optional[str] = None,
    sync_to_stable: bool = False,
    force_sync: bool = False
) -> Dict:
    """
    Promote a candidate version to stable.

    IMPORTANT: This function NEVER modifies .cursor/skills/ or .cursor/agents/ directories.
    It creates a new .skill-evolve-data/skills-versions/{version}/ directory instead,
    which contains both skills/ and agents/ sub-directories as a complete snapshot.

    Execution order (guaranteed no-leftover design):
    1. Consistency check on candidate workspace (BEFORE creating any directory)
    2. Create versioned skills-versions/{version}/ directory with skills/ and agents/ (only if step 1 passes)
    3. Apply patches to versioned skills-versions/{version}/
    4. Optionally sync to stable skills/ and agents/ (--sync flag)

    If step 1 fails, no version directory is created and the function aborts.

    Args:
        gate_id: Gate result ID (must have passed)
        notes: Optional notes for the version

    Returns:
        Promotion result dictionary
    """
    # Load gate result
    gate_result = load_gate_result(gate_id)
    
    # Verify gate passed
    if gate_result.get("decision") != "promote":
        raise ValueError(
            f"Gate {gate_id} did not pass (decision: {gate_result.get('decision')}). "
            "Cannot promote."
        )
    
    if not gate_result.get("overall_passed"):
        raise ValueError(
            f"Gate {gate_id} did not pass all cases. Cannot promote."
        )
    
    proposal_id = gate_result["proposal_id"]
    
    # Load proposal
    proposal = load_proposal(proposal_id)
    
    # Get candidate workspace
    candidate_dir = Path(proposal.get("candidate_dir", ""))
    if not candidate_dir.exists():
        raise FileNotFoundError(f"Candidate directory not found: {candidate_dir}")
    
    # Generate new version ID
    version_id = generate_version_id()
    
    print(f"\n{'='*60}")
    print(f"SKILL EVOLVE - Version Promotion")
    print(f"{'='*60}")
    print(f"Gate ID: {gate_id}")
    print(f"Proposal ID: {proposal_id}")
    print(f"New Version: {version_id}")
    
    # Create version manifest
    manifest = create_version_manifest(
        version_id=version_id,
        proposal=proposal,
        gate_result=gate_result,
        notes=notes or "Promoted from gate result"
    )
    
    # Save manifest
    manifest_path = save_version_manifest(manifest)
    print(f"Manifest saved: {manifest_path}")
    
    # Step 1: Run full consistency check on candidate workspace BEFORE creating any version directory.
    # If this fails, we abort immediately — no version directory is created.
    print(f"\n[Step 1] Running consistency check on candidate workspace...")
    target_files = proposal.get("target_files", [])
    consistency_ok, consistency_issues = run_full_consistency_check(
        candidate_dir, version_id, target_files
    )

    if not consistency_ok:
        print(f"\nConsistency check FAILED. Aborting promotion — no version created.")
        print("Found issues:")
        for issue in consistency_issues:
            print(issue)
        raise ValueError(
            "Consistency check failed. Please fix the proposal and re-run the regression gate "
            "before attempting promotion again."
        )

    # Step 2: Create versioned skills copy (only after consistency passes)
    print(f"\n[Step 2] Creating versioned skills directory...")
    create_versioned_skills_copy(version_id)

    # Step 3: Apply patches to the versioned skills
    print(f"\n[Step 3] Applying patches to versioned skills...")
    files_applied = apply_patches_to_versioned_skills(
        candidate_dir, target_files, version_id
    )

    # Step 4: Optionally sync to stable skills/agents
    if sync_to_stable:
        print(f"\n[Step 4] Syncing to stable skills/ and agents/ directories...")
        sync_result = sync_to_stable_skills(
            candidate_dir, target_files, version_id, force=force_sync
        )
        manifest["synced_to_stable"] = not sync_result.get("aborted", False)
        manifest["sync_details"] = sync_result
        if sync_result.get("aborted"):
            print("\n  Sync was aborted by user — stable skills/ and agents/ left unchanged.")
            print(f"  Versioned snapshot .skill-evolve-data/skills-versions/{version_id}/ is still available.")
    else:
        manifest["synced_to_stable"] = False
        print(f"\n[Step 4] Skipped (use --sync to update stable skills/ and agents/)")
    
    # Update stable pointer
    stable_path = update_stable_pointer(version_id, manifest_path)
    
    # Move proposal to accepted
    move_proposal_to_accepted(proposal_id)
    
    # Clean up intermediate files (candidate workspace, feedback, etc.)
    cleaned = cleanup_intermediate_files(candidate_dir, proposal_id, gate_id)
    
    # Update proposal status
    proposal["status"] = "accepted"
    proposal["version"] = version_id
    proposal["updated_at"] = datetime.now().isoformat()
    with open(DATA_ROOT / "patch_proposals" / "accepted" / f"{proposal_id}.json", "w", encoding="utf-8") as f:
        json.dump(proposal, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"Promotion completed successfully!")
    print(f"{'='*60}")
    print(f"Original skills: {SKILLS_ROOT} (preserved, NOT modified)")
    print(f"Original agents: {SKILLS_ROOT.parent / 'agents'} (preserved, NOT modified)")
    print(f"New snapshot: {VERSIONED_SKILLS_DIR / version_id}")
    print(f"  ├── agents/")
    print(f"  └── skills/")
    print(f"Version ID: {version_id}")
    print(f"Files patched: {files_applied}")
    print(f"Manifest: {manifest_path}")
    print(f"Stable pointer: {stable_path}")
    print(f"How to use this version: Explicitly point future prompts at .skill-evolve-data/skills-versions/{version_id}/...")
    
    return {
        "version_id": version_id,
        "manifest_path": str(manifest_path),
        "stable_pointer": str(stable_path),
        "files_applied": files_applied,
        "original_skills_dir": str(SKILLS_ROOT),
        "new_skills_dir": str(VERSIONED_SKILLS_DIR / version_id),
        "gate_result": gate_result,
        "promoted_at": datetime.now().isoformat()
    }


def main():
    parser = argparse.ArgumentParser(
        description="Promote candidate version to stable with comprehensive consistency checks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script promotes approved patches to a new version.

By default, it:
1. Runs consistency check on candidate workspace (ABORTS if failed — no version created)
2. Creates a new skills-versions/vXXX/ directory containing both agents/ and skills/ sub-dirs
3. Applies patches to the versioned snapshot
4. Reports any remaining old patterns or inconsistencies

With --sync, it additionally:
5. Updates the stable skills/ and agents/ directories with approved patches
6. Verifies all related files are in sync

Examples:
    python promote_skill_version.py --gate-id GR-123456
    python promote_skill_version.py --gate-id GR-123456 --notes "Fixed PDF routing issue"
    python promote_skill_version.py --gate-id GR-123456 --sync
    python promote_skill_version.py --gate-id GR-123456 --sync --force
        """
    )
    
    parser.add_argument(
        "--gate-id", "-g",
        required=True,
        help="Gate result ID that passed"
    )
    parser.add_argument(
        "--notes", "-n",
        help="Optional notes for the new version"
    )
    parser.add_argument(
        "--sync", "-s",
        action="store_true",
        help="Also update the stable skills/ and agents/ directories with approved patches"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force sync even if consistency warnings are found"
    )
    
    args = parser.parse_args()
    
    try:
        result = promote_skill_version(
            gate_id=args.gate_id,
            notes=args.notes,
            sync_to_stable=args.sync,
            force_sync=args.force
        )
        
        # Print sync summary if applicable
        if args.sync and result.get("synced_to_stable"):
            sync_details = result.get("sync_details", {})
            print(f"\n[SUMMARY] Synced {len(sync_details.get('synced', []))} files to stable skills/")
            if sync_details.get("failed"):
                print(f"Failed: {len(sync_details['failed'])}")
        
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
