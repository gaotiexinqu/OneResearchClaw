#!/usr/bin/env python3
"""
Collect Raw Feedback Script

Ingests raw user feedback text or files and saves them as raw feedback artifacts
for later normalization.

Usage:
    python collect_feedback.py --text "feedback text"
    python collect_feedback.py --file /path/to/feedback.txt
    python collect_feedback.py --interactive
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

SKILL_ROOT = Path(__file__).parent.parent
WORKSPACE_ROOT = SKILL_ROOT.parent.parent.parent
DATA_ROOT = WORKSPACE_ROOT / ".skill-evolve-data"
RAW_FEEDBACK_DIR = DATA_ROOT / "feedback" / "raw"


def generate_feedback_id() -> str:
    """Generate a unique feedback ID in format FB-XXXXXX."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"FB-{timestamp[-6:]}"


def save_raw_feedback(feedback_id: str, content: str, source: str = "manual", case_id: str = "unknown") -> Path:
    """
    Save raw feedback to a JSON artifact.
    
    Args:
        feedback_id: Unique identifier for this feedback
        content: The raw feedback content
        source: Source of the feedback (manual, file, etc.)
    
    Returns:
        Path to the saved feedback file
    """
    RAW_FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    
    feedback_data = {
        "feedback_id": feedback_id,
        "raw_content": content,
        "source": source,
        "case_id": case_id,
        "language": "preserved",  # Preserve original language
        "collected_at": datetime.now().isoformat(),
        "status": "raw"
    }
    
    output_path = RAW_FEEDBACK_DIR / f"{feedback_id}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(feedback_data, f, indent=2, ensure_ascii=False)
    
    return output_path


def collect_from_text(text: str, case_id: str = "unknown") -> Path:
    """Collect feedback from direct text input."""
    feedback_id = generate_feedback_id()
    output_path = save_raw_feedback(feedback_id, text, source="manual_text", case_id=case_id)
    return output_path


def collect_from_file(file_path: str, case_id: str = "unknown") -> Path:
    """Collect feedback from a file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Feedback file not found: {file_path}")
    
    content = path.read_text(encoding="utf-8")
    feedback_id = generate_feedback_id()
    output_path = save_raw_feedback(feedback_id, content, source=f"file:{file_path}", case_id=case_id)
    return output_path


def interactive_collection(case_id: str = "unknown") -> Path:
    """Collect feedback via interactive prompt."""
    print("=" * 60)
    print("SKILL EVOLVE - Interactive Feedback Collection")
    print("=" * 60)
    print("\nEnter your feedback (press Ctrl+D or type 'END' on a new line to finish):\n")
    
    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)
        except EOFError:
            break
    
    content = "\n".join(lines)
    if not content.strip():
        print("Error: No feedback content provided.")
        sys.exit(1)
    
    feedback_id = generate_feedback_id()
    output_path = save_raw_feedback(feedback_id, content, source="interactive", case_id=case_id)
    
    print(f"\nFeedback collected successfully!")
    print(f"Feedback ID: {feedback_id}")
    print(f"Saved to: {output_path}")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Collect raw user feedback for skill evolution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python collect_feedback.py --text "The grounding skill failed to route PDF files correctly"
    python collect_feedback.py --file /path/to/feedback.txt
    python collect_feedback.py --interactive
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", "-t", type=str, help="Feedback text directly")
    group.add_argument("--file", "-f", type=str, help="Path to feedback file")
    group.add_argument("--interactive", "-i", action="store_true", help="Interactive feedback collection")
    parser.add_argument("--case-id", help="Optional case/run identifier for this feedback")
    
    args = parser.parse_args()
    
    try:
        if args.interactive:
            output_path = interactive_collection(case_id=args.case_id or "unknown")
        elif args.text:
            output_path = collect_from_text(args.text, case_id=args.case_id or "unknown")
            print(f"Feedback collected successfully!")
            print(f"Feedback ID: {output_path.stem}")
            print(f"Saved to: {output_path}")
        elif args.file:
            output_path = collect_from_file(args.file, case_id=args.case_id or "unknown")
            print(f"Feedback collected successfully!")
            print(f"Feedback ID: {output_path.stem}")
            print(f"Saved to: {output_path}")
        
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
