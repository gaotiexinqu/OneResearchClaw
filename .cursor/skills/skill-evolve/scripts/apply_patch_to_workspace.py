#!/usr/bin/env python3
"""
Apply Patch to Workspace Script

Applies a candidate patch to an isolated workspace for testing.
Does NOT overwrite stable skills by default.

Usage:
    python apply_patch_to_workspace.py --proposal-id PP-123456
    python apply_patch_to_workspace.py --proposal-id PP-123456 --workspace-path /tmp/test_workspace
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

SKILL_ROOT = Path(__file__).parent.parent
WORKSPACE_ROOT = SKILL_ROOT.parent.parent.parent
DATA_ROOT = WORKSPACE_ROOT / ".skill-evolve-data"
PROPOSED_DIR = DATA_ROOT / "patch_proposals" / "proposed"
CANDIDATE_DIR = DATA_ROOT / "versions"


def load_proposal(proposal_id: str) -> Dict:
    """Load patch proposal from file."""
    proposal_path = PROPOSED_DIR / f"{proposal_id}.json"
    if not proposal_path.exists():
        raise FileNotFoundError(f"Proposal not found: {proposal_id}")
    
    with open(proposal_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_candidate_version(proposal_id: str) -> Path:
    """
    Create a new candidate version directory.
    
    Returns:
        Path to the candidate version directory
    """
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    # Find next candidate version number
    versions_dir = CANDIDATE_DIR
    existing = list(versions_dir.glob("candidate_*"))
    
    if existing:
        nums = [int(d.name.split("_")[1]) for d in existing]
        next_num = max(nums) + 1
    else:
        next_num = 1
    
    candidate_dir = versions_dir / f"candidate_{next_num:03d}"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    
    return candidate_dir


def copy_skill_files(target_files: List[str], candidate_dir: Path) -> List[str]:
    """
    Copy target skill files to candidate workspace.

    Args:
        target_files: List of file paths relative to WORKSPACE_ROOT
        candidate_dir: Destination candidate directory

    Returns:
        List of copied file paths
    """
    workspace = candidate_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    copied = []
    for target in target_files:
        # Always resolve source relative to WORKSPACE_ROOT (project root),
        # regardless of where the file lives (.cursor/skills/, .cursor/agents/, etc.)
        source = WORKSPACE_ROOT / target

        if not source.exists():
            print(f"Warning: Source file not found: {source}")
            continue

        # Preserve the path as-is under workspace root
        relative_target = target
        dest = workspace / relative_target
        dest.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source, dest)
        copied.append(relative_target)

    return copied


def apply_changes_to_workspace(
    proposal: Dict,
    candidate_dir: Path,
    changes: Optional[List[Dict]] = None
) -> List[Path]:
    """
    Apply planned changes to the candidate workspace.
    
    Args:
        proposal: The patch proposal
        candidate_dir: Candidate version directory
        changes: Optional list of changes to apply (defaults to proposal's planned_changes)
    
    Returns:
        List of modified file paths
    """
    workspace = candidate_dir / "workspace"
    changes = changes or proposal.get("planned_changes", [])
    
    modified = []
    for change in changes:
        file_path = change.get("file", "")
        change_type = change.get("change_type", "modify")
        
        if not file_path:
            continue
        
        # Resolve file path relative to WORKSPACE_ROOT, preserving directory structure
        full_path = workspace / file_path
        
        if not full_path.exists():
            print(f"Warning: File not found in workspace: {full_path}")
            continue
        
        if change_type == "modify":
            # Read current content
            content = full_path.read_text(encoding="utf-8")
            
            before = change.get("before", "")
            after = change.get("after", "")
            
            if not before or not after:
                raise ValueError(f"Unsafe modify change for {file_path}: both `before` and `after` must be provided")
            if before not in content:
                raise ValueError(f"Unsafe modify change for {file_path}: `before` pattern not found")
            content = content.replace(before, after)
            full_path.write_text(content, encoding="utf-8")
            modified.append(full_path)
        
        elif change_type == "replace":
            before = change.get("before", "")
            after = change.get("after", "")
            if not before or not after:
                raise ValueError(f"Unsafe replace change for {file_path}: both `before` and `after` must be provided")
            content = full_path.read_text(encoding="utf-8")
            if before not in content:
                raise ValueError(f"Unsafe replace change for {file_path}: `before` pattern not found")
            content = content.replace(before, after)
            full_path.write_text(content, encoding="utf-8")
            modified.append(full_path)

        elif change_type == "add":
            content = full_path.read_text(encoding="utf-8")
            after = change.get("after", "")
            if not after.strip():
                raise ValueError(f"Unsafe add change for {file_path}: `after` must be non-empty")
            content += f"\n\n# PATCH: {proposal['proposal_id']}\n{after}\n"
            full_path.write_text(content, encoding="utf-8")
            modified.append(full_path)

        elif change_type == "remove":
            before = change.get("before", "")
            if not before:
                raise ValueError(f"Unsafe remove change for {file_path}: `before` must be provided")
            content = full_path.read_text(encoding="utf-8")
            if before not in content:
                raise ValueError(f"Unsafe remove change for {file_path}: `before` pattern not found")
            content = content.replace(before, "")
            full_path.write_text(content, encoding="utf-8")
            modified.append(full_path)
    
    return modified


def create_workspace_manifest(
    proposal: Dict,
    candidate_dir: Path,
    copied_files: List[str],
    modified_files: List[Path]
) -> Path:
    """Create a manifest for the candidate workspace."""
    manifest = {
        "proposal_id": proposal["proposal_id"],
        "candidate_dir": str(candidate_dir),
        "workspace_path": str(candidate_dir / "workspace"),
        "target_files": copied_files,
        "modified_files": [str(f) for f in modified_files],
        "created_at": datetime.now().isoformat(),
        "proposal_snapshot": proposal
    }
    
    manifest_path = candidate_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    return manifest_path


def apply_patch_to_workspace(
    proposal_id: str,
    workspace_path: Optional[str] = None,
    apply_changes: bool = False
) -> Path:
    """
    Apply a patch proposal to an isolated workspace.
    
    Args:
        proposal_id: The proposal ID to apply
        workspace_path: Optional custom workspace path (if None, creates candidate version dir)
        apply_changes: Whether to actually apply the planned changes
    
    Returns:
        Path to the workspace directory
    """
    proposal = load_proposal(proposal_id)
    target_files = proposal.get("target_files", [])
    
    if not target_files:
        raise ValueError("No target files specified in proposal")
    
    # Determine workspace location
    if workspace_path:
        workspace = Path(workspace_path)
        workspace.mkdir(parents=True, exist_ok=True)
        candidate_dir = workspace.parent
    else:
        candidate_dir = create_candidate_version(proposal_id)
        workspace = candidate_dir / "workspace"
    
    # Copy original skill files
    copied = copy_skill_files(target_files, candidate_dir)
    
    if not copied:
        raise RuntimeError("No files were copied to workspace")
    
    # Apply changes if requested
    modified = []
    if apply_changes:
        modified = apply_changes_to_workspace(proposal, candidate_dir)
    
    # Create manifest
    manifest_path = create_workspace_manifest(
        proposal, candidate_dir, copied,
        modified if apply_changes else []
    )
    
    # Update proposal status
    proposal["status"] = "candidate"
    proposal["candidate_dir"] = str(candidate_dir)
    proposal["updated_at"] = datetime.now().isoformat()
    
    proposal_out = PROPOSED_DIR / f"{proposal_id}.json"
    with open(proposal_out, "w", encoding="utf-8") as f:
        json.dump(proposal, f, indent=2, ensure_ascii=False)
    
    return candidate_dir


def main():
    parser = argparse.ArgumentParser(
        description="Apply patch proposal to isolated workspace for testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python apply_patch_to_workspace.py --proposal-id PP-123456
    python apply_patch_to_workspace.py --proposal-id PP-123456 --workspace-path /tmp/test
    python apply_patch_to_workspace.py --proposal-id PP-123456 --apply-changes
        """
    )
    
    parser.add_argument(
        "--proposal-id", "-p",
        required=True,
        help="Patch proposal ID to apply"
    )
    parser.add_argument(
        "--workspace-path", "-w",
        help="Custom workspace path (default: create candidate_* directory)"
    )
    parser.add_argument(
        "--apply-changes",
        action="store_true",
        help="Actually apply the planned changes (default: copy only)"
    )
    
    args = parser.parse_args()
    
    try:
        workspace_path = apply_patch_to_workspace(
            proposal_id=args.proposal_id,
            workspace_path=args.workspace_path,
            apply_changes=args.apply_changes
        )
        
        print(f"Patch applied to workspace successfully!")
        print(f"Proposal ID: {args.proposal_id}")
        print(f"Workspace: {workspace_path}")
        print(f"Changes applied: {args.apply_changes}")
        
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())