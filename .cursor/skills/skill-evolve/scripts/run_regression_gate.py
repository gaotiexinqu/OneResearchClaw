#!/usr/bin/env python3
"""
Run Regression Gate Script

Executes regression tests against evaluation cases stored in the evaluations directory.
Each case contains inputs, expected assertions, and notes.

Usage:
    python run_regression_gate.py --proposal-id PP-123456
    python run_regression_gate.py --proposal-id PP-123456 --case case_research_basic
    python run_regression_gate.py --proposal-id PP-123456 --workspace-path /tmp/candidate_001
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple

SKILL_ROOT = Path(__file__).parent.parent
WORKSPACE_ROOT = SKILL_ROOT.parent.parent.parent
DATA_ROOT = WORKSPACE_ROOT / ".skill-evolve-data"
PROPOSED_DIR = DATA_ROOT / "patch_proposals" / "proposed"
CASES_DIR = DATA_ROOT / "evaluations" / "cases"
RESULTS_DIR = DATA_ROOT / "evaluations" / "results"


def generate_gate_id() -> str:
    """Generate a unique gate ID in format GR-XXXXXX."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"GR-{timestamp[-6:]}"


def load_proposal(proposal_id: str) -> Dict:
    """Load patch proposal from file."""
    proposal_path = PROPOSED_DIR / f"{proposal_id}.json"
    if not proposal_path.exists():
        raise FileNotFoundError(f"Proposal not found: {proposal_id}")
    
    with open(proposal_path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_available_cases() -> List[str]:
    """List all available evaluation cases."""
    if not CASES_DIR.exists():
        return []
    return [d.name for d in CASES_DIR.iterdir() if d.is_dir()]


def load_case(case_id: str) -> Optional[Dict]:
    """Load evaluation case metadata."""
    case_dir = CASES_DIR / case_id
    if not case_dir.exists():
        return None
    
    # Load case metadata
    meta_path = case_dir / "case_metadata.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    return {"case_id": case_id, "notes": "No metadata available"}


def run_file_check(
    check: Dict,
    workspace_path: Path
) -> Tuple[bool, str]:
    """
    Run a file-based assertion check.
    
    Args:
        check: Check definition with type and parameters
        workspace_path: Path to the candidate workspace
    
    Returns:
        Tuple of (passed, details)
    """
    check_type = check.get("type", "")
    
    try:
        if check_type == "file_exists":
            file_path = workspace_path / check.get("file", "")
            passed = file_path.exists()
            return passed, f"File {'exists' if passed else 'not found'}: {file_path}"
        
        elif check_type == "file_not_exists":
            file_path = workspace_path / check.get("file", "")
            passed = not file_path.exists()
            return passed, f"File {'correctly absent' if passed else 'unexpectedly present'}: {file_path}"
        
        elif check_type == "contains":
            file_path = workspace_path / check.get("file", "")
            if not file_path.exists():
                return False, f"File not found: {file_path}"
            content = file_path.read_text(encoding="utf-8")
            pattern = check.get("pattern", "")
            passed = pattern in content
            return passed, f"Pattern {'found' if passed else 'not found'} in {file_path.name}"
        
        elif check_type == "not_contains":
            file_path = workspace_path / check.get("file", "")
            if not file_path.exists():
                return False, f"File not found: {file_path}"
            content = file_path.read_text(encoding="utf-8")
            pattern = check.get("pattern", "")
            passed = pattern not in content
            return passed, f"Pattern {'correctly absent' if passed else 'unexpectedly present'} in {file_path.name}"
        
        elif check_type == "regex_match":
            import re
            file_path = workspace_path / check.get("file", "")
            if not file_path.exists():
                return False, f"File not found: {file_path}"
            content = file_path.read_text(encoding="utf-8")
            pattern = check.get("pattern", "")
            match = re.search(pattern, content, re.MULTILINE)
            passed = match is not None
            return passed, f"Regex {'matched' if passed else 'not matched'} in {file_path.name}"
        
        elif check_type == "line_count":
            file_path = workspace_path / check.get("file", "")
            if not file_path.exists():
                return False, f"File not found: {file_path}"
            lines = len(file_path.read_text(encoding="utf-8").splitlines())
            min_lines = check.get("min_lines", 0)
            max_lines = check.get("max_lines", float('inf'))
            passed = min_lines <= lines <= max_lines
            return passed, f"Line count {lines} is {'within' if passed else 'outside'} range [{min_lines}, {max_lines}]"
        
        else:
            return False, f"Unknown check type: {check_type}"
    
    except Exception as e:
        return False, f"Check failed with error: {str(e)}"


def run_case(
    case_id: str,
    workspace_path: Path,
    proposal: Dict
) -> Dict:
    """
    Run a single evaluation case.
    
    Args:
        case_id: Case identifier
        workspace_path: Path to candidate workspace
        proposal: The proposal being tested
    
    Returns:
        Case result dictionary
    """
    case_dir = CASES_DIR / case_id
    case_data = load_case(case_id)
    
    checks_passed = []
    checks_failed = []
    error_message = None
    
    start_time = time.time()
    
    try:
        # Prefer auto-generated assertions from proposal (change unit)
        assertions = proposal.get("auto_generated_assertions", [])
        
        if not assertions:
            # Fallback: load assertions from case metadata
            assertions = case_data.get("assertions", []) if case_data else []
            
            if not assertions:
                # Check for assertions.json file
                assertions_file = case_dir / "assertions.json"
                if assertions_file.exists():
                    with open(assertions_file, "r", encoding="utf-8") as f:
                        assertions = json.load(f).get("assertions", [])
        
        if not assertions:
            raise ValueError(f"Evaluation case {case_id} has no assertions; empty cases must not pass vacuously")
        
        for assertion in assertions:
            passed, details = run_file_check(assertion, workspace_path)
            result_item = {
                "check_name": assertion.get("name", assertion.get("type", "unnamed")),
                "check_type": assertion.get("type", ""),
                "passed": passed,
                "details": details
            }
            
            if passed:
                checks_passed.append(result_item)
            else:
                checks_failed.append(result_item)
    
    except Exception as e:
        error_message = str(e)
        checks_failed.append({
            "check_name": "execution",
            "passed": False,
            "details": error_message
        })
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    return {
        "case_id": case_id,
        "passed": len(checks_failed) == 0 and error_message is None,
        "checks_passed": checks_passed,
        "checks_failed": checks_failed,
        "duration_ms": duration_ms,
        "error_message": error_message,
        "assertion_source": "auto_generated" if proposal.get("auto_generated_assertions") else "case_file"
    }


def run_regression_gate(
    proposal_id: str,
    case_ids: Optional[List[str]] = None,
    workspace_path: Optional[str] = None
) -> Dict:
    """
    Run regression gate for a proposal.
    
    Args:
        proposal_id: The proposal ID to test
        case_ids: Optional list of specific cases to run (default: all available)
        workspace_path: Optional workspace path (default: from proposal manifest)
    
    Returns:
        Gate result dictionary
    """
    proposal = load_proposal(proposal_id)
    
    # Determine workspace
    if workspace_path:
        workspace = Path(workspace_path)
    elif proposal.get("candidate_dir"):
        workspace = Path(proposal["candidate_dir"]) / "workspace"
    else:
        raise ValueError("No workspace path specified and no candidate_dir in proposal")
    
    if not workspace.exists():
        raise FileNotFoundError(f"Workspace not found: {workspace}")
    
    # Determine cases to run
    required_cases = set(proposal.get("required_regression_cases", []))
    
    if case_ids:
        cases_to_run = case_ids
    else:
        all_cases = list_available_cases()
        # Use required cases if available, otherwise all cases
        cases_to_run = list(required_cases) if required_cases else all_cases
    
    if not cases_to_run:
        raise ValueError("No evaluation cases specified or available")
    
    # Run each case
    case_results = []
    for case_id in cases_to_run:
        result = run_case(case_id, workspace, proposal)
        case_results.append(result)
    
    # Determine overall result
    all_passed = all(r["passed"] for r in case_results)
    
    if all_passed:
        decision = "promote"
        reason = "All regression cases passed."
    else:
        failed_cases = [r["case_id"] for r in case_results if not r["passed"]]
        decision = "reject"
        reason = f"Regression failed for cases: {', '.join(failed_cases)}"
    
    # Build gate result
    gate_result = {
        "gate_id": generate_gate_id(),
        "proposal_id": proposal_id,
        "evaluated_cases": cases_to_run,
        "case_results": case_results,
        "overall_passed": all_passed,
        "decision": decision,
        "reason": reason,
        "executed_at": datetime.now().isoformat(),
        "executed_by": "gate_runner",
        "execution_environment": {
            "workspace_path": str(workspace),
            "candidate_version": proposal.get("candidate_dir", "unknown"),
            "base_version": proposal.get("based_on", "unknown")
        },
        "artifacts": []
    }
    
    # Save gate result
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    result_path = RESULTS_DIR / f"{gate_result['gate_id']}.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(gate_result, f, indent=2, ensure_ascii=False)
    
    return gate_result


def main():
    parser = argparse.ArgumentParser(
        description="Run regression gate on candidate patch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_regression_gate.py --proposal-id PP-123456
    python run_regression_gate.py --proposal-id PP-123456 --case case_research_basic
    python run_regression_gate.py --proposal-id PP-123456 --workspace-path /tmp/candidate_001/workspace
        """
    )
    
    parser.add_argument(
        "--proposal-id", "-p",
        required=True,
        help="Patch proposal ID to test"
    )
    parser.add_argument(
        "--case", "-c",
        action="append",
        dest="cases",
        help="Specific case ID to run (can be specified multiple times)"
    )
    parser.add_argument(
        "--workspace-path", "-w",
        help="Path to candidate workspace (default: from proposal manifest)"
    )
    
    args = parser.parse_args()
    
    try:
        result = run_regression_gate(
            proposal_id=args.proposal_id,
            case_ids=args.cases,
            workspace_path=args.workspace_path
        )
        
        print(f"Regression gate completed!")
        print(f"Gate ID: {result['gate_id']}")
        print(f"Evaluated Cases: {', '.join(result['evaluated_cases'])}")
        print(f"Overall Passed: {result['overall_passed']}")
        print(f"Decision: {result['decision']}")
        print(f"Reason: {result['reason']}")
        print(f"\nCase Results:")
        for case_result in result["case_results"]:
            status = "PASS" if case_result["passed"] else "FAIL"
            print(f"  - {case_result['case_id']}: {status} ({case_result['duration_ms']}ms)")
        
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())