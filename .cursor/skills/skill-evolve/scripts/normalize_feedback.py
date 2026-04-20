#!/usr/bin/env python3
"""
Normalize Feedback Script

Converts raw feedback into structured normalized feedback according to the
feedback schema. Maps user feedback to the failure taxonomy when possible.

Usage:
    python normalize_feedback.py --feedback-id FB-123456
    python normalize_feedback.py --feedback-id FB-123456 --stage grounding --skill document-grounding
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

SKILL_ROOT = Path(__file__).parent.parent
WORKSPACE_ROOT = SKILL_ROOT.parent.parent.parent
DATA_ROOT = WORKSPACE_ROOT / ".skill-evolve-data"
RAW_FEEDBACK_DIR = DATA_ROOT / "feedback" / "raw"
NORMALIZED_FEEDBACK_DIR = DATA_ROOT / "feedback" / "normalized"
SCHEMA_PATH = SKILL_ROOT / "schemas" / "feedback.schema.json"


# Failure taxonomy mapping
FAILURE_TAXONOMY = {
    "grounding": [
        "canonical_path_missing",
        "wrong_router_choice",
        "multi_topic_not_split",
        "transcript_segmentation_fault",
        "evidence_bundle_incomplete",
        "source_metadata_missing",
        "grounding_output_missing_key_evidence",
        "grounding_wrong_file_type_handled"
    ],
    "research": [
        "opened_count_insufficient",
        "downloaded_count_insufficient",
        "exact_opened_count_not_verified",
        "downloaded_pdf_not_covered",
        "weak_literature_depth",
        "irrelevant_papers_included",
        "search_query_too_broad",
        "search_query_too_narrow",
        "citation_context_missing",
        "research_redundant_sources",
        "research_weak_query_quality"
    ],
    "summary": [
        "literature_body_shrunk",
        "paper_count_mismatch",
        "4_1_not_literal_copy",
        "report_overcompressed",
        "report_style_preference",
        "report_paragraph_length_inconsistent",
        "report_abstract_too_brief",
        "report_conclusion_lacks_action_items",
        "report_language_too_informal",
        "report_language_too_academic",
        "report_structure_missing_section",
        "report_hedging_inappropriate",
        "report_citation_format_inconsistent",
        "report_fluent_summary_mismatch",
        "summary_source_evidence_gap",
        "summary_methodology_unclear"
    ],
    "review": [
        "score_formula_incorrect",
        "pass_threshold_wrong",
        "weak_repair_loop",
        "reviewer_writer_not_separated",
        "review_criteria_unclear",
        "review_feedback_not_actionable",
        "review_inconsistent_scoring",
        "review_missing_dimension"
    ],
    "export": [
        "markdown_inline_not_rendered",
        "numbering_broken",
        "wrong_input_source_used",
        "export_format_mismatch",
        "file_naming_inconsistent",
        "export_missing_metadata",
        "export_layout_broken",
        "export_image_reference_broken"
    ]
}

# Keywords for automatic taxonomy mapping
TAXONOMY_KEYWORDS = {
    "grounding": {
        "canonical_path_missing": ["canonical path", "expected path", "should be at"],
        "wrong_router_choice": ["wrong skill", "should use", "router selected"],
        "multi_topic_not_split": ["multi-topic", "split failed", "fan-out"],
        "transcript_segmentation_fault": ["segment", "transcript", "speaker", "timestamp", "paragraph split"],
        "evidence_bundle_incomplete": ["missing evidence", "incomplete bundle", "evidence gap"],
        "source_metadata_missing": ["metadata", "source missing", "author", "date", "title missing"],
        "grounding_output_missing_key_evidence": ["key evidence", "missing key", "critical evidence"],
        "grounding_wrong_file_type_handled": ["wrong file type", "file type", "unsupported format"]
    },
    "research": {
        "opened_count_insufficient": ["opened papers", "not enough", "insufficient literature"],
        "downloaded_count_insufficient": ["downloaded", "download count", "need more"],
        "exact_opened_count_not_verified": ["count not verified", "exact count", "verification"],
        "downloaded_pdf_not_covered": ["pdf not covered", "downloaded pdf", "missing pdf"],
        "weak_literature_depth": ["shallow", "weak depth", "not deep enough"],
        "irrelevant_papers_included": ["irrelevant", "off-topic", "not related", "wrong papers"],
        "search_query_too_broad": ["query too broad", "too many results", "search broad"],
        "search_query_too_narrow": ["query too narrow", "too few results", "search narrow"],
        "citation_context_missing": ["citation context", "citation missing", "reference unclear"],
        "research_redundant_sources": ["redundant", "duplicate", "overlap"],
        "research_weak_query_quality": ["bad query", "weak query", "poor search", "query quality"]
    },
    "summary": {
        "literature_body_shrunk": ["shrunk", "compressed", "lost content"],
        "paper_count_mismatch": ["paper count", "mismatch", "count wrong"],
        "4_1_not_literal_copy": ["section 4.1", "literal copy", "not copied"],
        "report_overcompressed": ["overcompressed", "too short", "missing detail"],
        "report_style_preference": ["report style", "format preference", "模板", "output template", "报告风格"],
        "report_paragraph_length_inconsistent": ["paragraph too short", "段落太短", "paragraph length", "段落长度"],
        "report_abstract_too_brief": ["abstract too brief", "摘要太短", "summary too brief", "executive summary"],
        "report_conclusion_lacks_action_items": ["conclusion no action", "结论缺少", "缺少行动", "结论建议"],
        "report_language_too_informal": ["too informal", "口语化", "language informal", "colloquial"],
        "report_language_too_academic": ["too academic", "太学术", "language academic", "formal tone"],
        "report_structure_missing_section": ["missing section", "缺少章节", "section missing", "报告结构"],
        "report_hedging_inappropriate": ["hedging", "语气太弱", "过度模糊", "uncertain tone"],
        "report_citation_format_inconsistent": ["citation format", "引用格式", "reference style"],
        "report_fluent_summary_mismatch": ["summary mismatch", "摘要不一致", "摘要偏差", "executive summary wrong"],
        "summary_source_evidence_gap": ["evidence gap", "evidence missing", "缺少引用", "missing citation"],
        "summary_methodology_unclear": ["methodology", "方法论", "method unclear", "方法不清楚"]
    },
    "review": {
        "score_formula_incorrect": ["score formula", "calculation wrong", "scoring"],
        "pass_threshold_wrong": ["threshold", "pass criteria", "gate wrong"],
        "weak_repair_loop": ["repair loop", "not repaired", "loop weak"],
        "reviewer_writer_not_separated": ["not separated", "same context", "combined"],
        "review_criteria_unclear": ["review criteria", "评分标准", "criteria unclear", "标准不清楚"],
        "review_feedback_not_actionable": ["feedback not actionable", "反馈无用", "suggestion vague"],
        "review_inconsistent_scoring": ["inconsistent scoring", "评分不一致", "scoring varies"],
        "review_missing_dimension": ["missing dimension", "缺少维度", "评分维度", "dimension missing"]
    },
    "export": {
        "markdown_inline_not_rendered": ["markdown", "render", "inline code"],
        "numbering_broken": ["numbering", "ordering", "sequence broken"],
        "wrong_input_source_used": ["wrong source", "used wrong", "input error"],
        "export_format_mismatch": ["format mismatch", "格式不符", "export format", "wrong format"],
        "file_naming_inconsistent": ["file naming", "命名不一致", "naming convention"],
        "export_missing_metadata": ["export metadata", "元数据", "missing metadata", "metadata lost"],
        "export_layout_broken": ["layout broken", "布局错乱", "format broken"],
        "export_image_reference_broken": ["image broken", "图片", "image missing", "figure reference"]
    }
}


def load_raw_feedback(feedback_id: str) -> Dict:
    """Load raw feedback from file."""
    raw_path = RAW_FEEDBACK_DIR / f"{feedback_id}.json"
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw feedback not found: {feedback_id}")
    
    with open(raw_path, "r", encoding="utf-8") as f:
        return json.load(f)


def map_to_taxonomy(text: str) -> tuple[Optional[str], Optional[str]]:
    """
    Attempt to map feedback text to the failure taxonomy.
    
    Returns:
        Tuple of (pipeline_stage, failure_type) or (None, None) if no match
    """
    text_lower = text.lower()
    
    for stage, failures in TAXONOMY_KEYWORDS.items():
        for failure_type, keywords in failures.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return stage, failure_type
    
    return None, None


def infer_severity(text: str) -> str:
    """Infer severity from feedback text."""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["critical", "fails completely", "broken", "error"]):
        return "critical"
    elif any(word in text_lower for word in ["major", "wrong", "incorrect", "poor"]):
        return "major"
    elif any(word in text_lower for word in ["minor", "small", "slight", "could improve"]):
        return "minor"
    
    return "cosmetic"


def normalize_feedback(
    feedback_id: str,
    pipeline_stage: Optional[str] = None,
    suspected_skill: Optional[str] = None,
    failure_type: Optional[str] = None,
    case_id: Optional[str] = None
) -> Dict:
    """
    Normalize a raw feedback entry.
    
    Args:
        feedback_id: ID of the raw feedback to normalize
        pipeline_stage: Optional explicit pipeline stage
        suspected_skill: Optional explicit skill name
        failure_type: Optional explicit failure type
        case_id: Optional case identifier
    
    Returns:
        Normalized feedback dictionary
    """
    raw = load_raw_feedback(feedback_id)
    raw_content = raw.get("raw_content", "")
    
    # Map to taxonomy if not explicitly provided
    inferred_stage, inferred_type = map_to_taxonomy(raw_content)
    
    stage = pipeline_stage or inferred_stage or "unknown"
    detected_type = failure_type or inferred_type or "unknown"
    severity = infer_severity(raw_content)
    
    normalized = {
        "feedback_id": feedback_id,  # Keep original ID as-is
        "case_id": case_id or raw.get("case_id", "unknown"),
        "pipeline_stage": stage,
        "suspected_skill": suspected_skill or "unknown",
        "failure_type": detected_type,
        "severity": severity,
        "user_feedback": raw_content,
        "observed_artifacts": [],
        "expected_behavior": "",
        "actual_behavior": "",
        "current_skill_version": "unknown",
        "reproduce_steps": [],
        "preferred_fix_scope": "unknown",
        "status": "normalized",
        "tags": [],
        "created_at": raw.get("collected_at", datetime.now().isoformat()),
        "updated_at": datetime.now().isoformat(),
        "notes": ""
    }
    
    return normalized


def save_normalized_feedback(normalized: Dict) -> Path:
    """Save normalized feedback to file."""
    NORMALIZED_FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    
    output_path = NORMALIZED_FEEDBACK_DIR / f"{normalized['feedback_id']}_normalized.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2, ensure_ascii=False)
    
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Normalize raw feedback into structured format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python normalize_feedback.py --feedback-id FB-123456
    python normalize_feedback.py --feedback-id FB-123456 --stage research --skill grounded-research-lit
        """
    )
    
    parser.add_argument(
        "--feedback-id", "-f",
        required=True,
        help="Raw feedback ID to normalize"
    )
    parser.add_argument(
        "--stage", "-s",
        choices=["grounding", "research", "summary", "review", "export", "unknown"],
        help="Explicit pipeline stage"
    )
    parser.add_argument(
        "--skill",
        help="Suspected skill name"
    )
    parser.add_argument(
        "--failure-type",
        help="Specific failure type from taxonomy"
    )
    parser.add_argument(
        "--case-id",
        help="Case identifier for this feedback"
    )
    
    args = parser.parse_args()
    
    try:
        normalized = normalize_feedback(
            feedback_id=args.feedback_id,
            pipeline_stage=args.stage,
            suspected_skill=args.skill,
            failure_type=args.failure_type,
            case_id=args.case_id
        )
        
        output_path = save_normalized_feedback(normalized)
        
        print(f"Feedback normalized successfully!")
        print(f"Feedback ID: {normalized['feedback_id']}")
        print(f"Pipeline Stage: {normalized['pipeline_stage']}")
        print(f"Failure Type: {normalized['failure_type']}")
        print(f"Severity: {normalized['severity']}")
        print(f"Saved to: {output_path}")
        
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())