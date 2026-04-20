#!/usr/bin/env python3
"""
Reject Patch Proposal Script

Archives a proposal as rejected with an explicit reason.
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

SKILL_ROOT = Path(__file__).parent.parent
WORKSPACE_ROOT = SKILL_ROOT.parent.parent.parent
DATA_ROOT = WORKSPACE_ROOT / ".skill-evolve-data"
PROPOSED_DIR = DATA_ROOT / "patch_proposals" / "proposed"
REJECTED_DIR = DATA_ROOT / "patch_proposals" / "rejected"


def reject_proposal(proposal_id: str, reason: str):
    path = PROPOSED_DIR / f"{proposal_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Proposal not found: {proposal_id}")
    with open(path, "r", encoding="utf-8") as f:
        proposal = json.load(f)
    proposal["status"] = "rejected"
    proposal["rejected_at"] = datetime.now().isoformat()
    proposal["rejection_reason"] = reason
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)
    dest = REJECTED_DIR / f"{proposal_id}.json"
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(proposal, f, indent=2, ensure_ascii=False)
    path.unlink()
    return dest


def main():
    parser = argparse.ArgumentParser(description="Archive a patch proposal as rejected")
    parser.add_argument("--proposal-id", "-p", required=True)
    parser.add_argument("--reason", "-r", required=True)
    args = parser.parse_args()
    try:
        dest = reject_proposal(args.proposal_id, args.reason)
        print(f"Proposal rejected and archived: {dest}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
