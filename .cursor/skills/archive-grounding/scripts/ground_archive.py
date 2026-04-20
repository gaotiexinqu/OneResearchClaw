#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SUPPORTED_ROUTE_MAP: Dict[str, Tuple[str, str]] = {
    ".pdf": ("document", "document-grounding"),
    ".docx": ("document", "document-grounding"),
    ".md": ("document", "document-grounding"),
    ".txt": ("document", "document-grounding"),
    ".xlsx": ("table", "table-grounding"),
    ".csv": ("table", "table-grounding"),
    ".pptx": ("slides", "pptx-grounding"),
    ".mp3": ("audio", "meeting-audio-grounding"),
    ".wav": ("audio", "meeting-audio-grounding"),
    ".m4a": ("audio", "meeting-audio-grounding"),
    ".mp4": ("video", "meeting-video-grounding"),
    ".mov": ("video", "meeting-video-grounding"),
    ".mkv": ("video", "meeting-video-grounding"),
}

SKIP_FILE_PATTERNS = [
    re.compile(r"^__MACOSX/"),
    re.compile(r"(^|/)\.DS_Store$"),
    re.compile(r"(^|/)Thumbs\.db$", re.IGNORECASE),
]

MAX_FILES = 500
MAX_TOTAL_UNCOMPRESSED_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB


@dataclass
class ManifestItem:
    relative_path: str
    file_name: str
    extension: str
    size_bytes: int
    detected_type: Optional[str]
    supported: bool
    recommended_skill: Optional[str]
    skip_reason: Optional[str] = None


@dataclass
class RoutedItem:
    relative_path: str
    detected_type: Optional[str]
    recommended_skill: Optional[str]
    downstream_status: str
    child_output_path: Optional[str]
    notes: Optional[str] = None


class ArchiveGroundingError(RuntimeError):
    pass


def safe_stem(name: str) -> str:
    stem = re.sub(r"\.[^.]+$", "", name)
    stem = re.sub(r"\s+", "_", stem.strip())
    stem = re.sub(r"[^A-Za-z0-9_.-]", "", stem)
    return stem or "archive"


def safe_rel_component(value: str) -> str:
    value = value.strip()
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"[^A-Za-z0-9_.-]", "", value)
    return value or "item"


def make_child_bundle_name(skill_name: str, file_name: str) -> str:
    skill_prefix_map = {
        "document-grounding": "doc",
        "table-grounding": "table",
        "pptx-grounding": "pptx",
        "meeting-audio-grounding": "audio",
        "meeting-video-grounding": "video",
    }
    prefix = skill_prefix_map.get(skill_name, "child")
    return f"{prefix}-{safe_stem(file_name)}"


def is_skipped_path(rel_path: str) -> Optional[str]:
    for pattern in SKIP_FILE_PATTERNS:
        if pattern.search(rel_path):
            return "hidden_or_system_file"
    return None


def ensure_safe_member(member: zipfile.ZipInfo) -> None:
    path = member.filename
    if os.path.isabs(path):
        raise ArchiveGroundingError(f"Unsafe absolute member path: {path}")
    normalized = os.path.normpath(path)
    if normalized.startswith(".."):
        raise ArchiveGroundingError(f"Unsafe archive member path traversal: {path}")


def inspect_zip(input_zip: Path) -> List[zipfile.ZipInfo]:
    with zipfile.ZipFile(input_zip, "r") as zf:
        members = zf.infolist()
        if len(members) > MAX_FILES:
            raise ArchiveGroundingError(
                f"Archive contains too many members ({len(members)} > {MAX_FILES})"
            )
        total_size = 0
        for member in members:
            ensure_safe_member(member)
            total_size += int(member.file_size)
        if total_size > MAX_TOTAL_UNCOMPRESSED_BYTES:
            raise ArchiveGroundingError(
                f"Archive uncompressed size too large ({total_size} bytes)"
            )
        return members


def unpack_zip(input_zip: Path, unpack_dir: Path) -> None:
    if unpack_dir.exists():
        shutil.rmtree(unpack_dir)
    unpack_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(input_zip, "r") as zf:
        for member in zf.infolist():
            ensure_safe_member(member)
        zf.extractall(unpack_dir)


def detect_file_type(path: Path) -> Tuple[Optional[str], Optional[str]]:
    ext = path.suffix.lower()
    if ext in SUPPORTED_ROUTE_MAP:
        return SUPPORTED_ROUTE_MAP[ext]
    return None, None


def build_manifest(unpack_dir: Path, child_outputs_dir: Path) -> Tuple[List[ManifestItem], List[RoutedItem]]:
    manifest: List[ManifestItem] = []
    routed: List[RoutedItem] = []

    all_files = [p for p in unpack_dir.rglob("*") if p.is_file()]
    all_files.sort(key=lambda p: str(p.relative_to(unpack_dir)).lower())

    for file_path in all_files:
        rel_path = str(file_path.relative_to(unpack_dir))
        skip_reason = is_skipped_path(rel_path)
        size_bytes = file_path.stat().st_size
        ext = file_path.suffix.lower()

        if skip_reason:
            manifest_item = ManifestItem(
                relative_path=rel_path,
                file_name=file_path.name,
                extension=ext,
                size_bytes=size_bytes,
                detected_type=None,
                supported=False,
                recommended_skill=None,
                skip_reason=skip_reason,
            )
            routed_item = RoutedItem(
                relative_path=rel_path,
                detected_type=None,
                recommended_skill=None,
                downstream_status="skipped",
                child_output_path=None,
                notes=skip_reason,
            )
        else:
            detected_type, recommended_skill = detect_file_type(file_path)
            supported = recommended_skill is not None
            child_output_path = None
            if supported and recommended_skill:
                child_bundle_name = make_child_bundle_name(recommended_skill, file_path.name)
                child_output_path = str((Path("child_outputs") / child_bundle_name).as_posix())
            manifest_item = ManifestItem(
                relative_path=rel_path,
                file_name=file_path.name,
                extension=ext,
                size_bytes=size_bytes,
                detected_type=detected_type,
                supported=supported,
                recommended_skill=recommended_skill,
                skip_reason=None if supported else "unsupported_extension",
            )
            routed_item = RoutedItem(
                relative_path=rel_path,
                detected_type=detected_type,
                recommended_skill=recommended_skill,
                downstream_status="pending_child_grounding" if supported else "unsupported",
                child_output_path=child_output_path,
                notes=None if supported else "unsupported_extension",
            )

        manifest.append(manifest_item)
        routed.append(routed_item)

    return manifest, routed


def build_extracted_meta(input_zip: Path, ground_id: str, manifest: List[ManifestItem]) -> Dict:
    total_files = len(manifest)
    supported_count = sum(1 for item in manifest if item.supported)
    skipped_count = sum(1 for item in manifest if item.skip_reason == "hidden_or_system_file")
    unsupported_count = sum(1 for item in manifest if item.skip_reason == "unsupported_extension")

    by_skill: Dict[str, int] = {}
    for item in manifest:
        if item.recommended_skill:
            by_skill[item.recommended_skill] = by_skill.get(item.recommended_skill, 0) + 1

    return {
        "source_file": str(input_zip),
        "source_type": "zip",
        "ground_id": ground_id,
        "total_files": total_files,
        "supported_files": supported_count,
        "skipped_files": skipped_count,
        "unsupported_files": unsupported_count,
        "recommended_skill_counts": by_skill,
        "child_outputs_dir": "child_outputs",
        "unpacked_dir": "unpacked",
        "child_output_policy": "all downstream child grounding outputs for supported files should be written under this archive bundle's child_outputs directory",
    }


def build_extracted_md(input_zip: Path, ground_id: str, manifest: List[ManifestItem], routed: List[RoutedItem]) -> str:
    lines: List[str] = []
    lines.append("# Archive Extraction Bundle")
    lines.append("")
    lines.append("## Archive Overview")
    lines.append(f"- Source archive: {input_zip}")
    lines.append(f"- Ground ID: {ground_id}")
    lines.append(f"- Total files discovered: {len(manifest)}")
    lines.append(f"- Supported files: {sum(1 for item in manifest if item.supported)}")
    lines.append(f"- Unsupported files: {sum(1 for item in manifest if item.skip_reason == 'unsupported_extension')}")
    lines.append(f"- Skipped hidden/system files: {sum(1 for item in manifest if item.skip_reason == 'hidden_or_system_file')}")
    lines.append("- Child grounding outputs for supported files should be written under `child_outputs/` inside this archive bundle.")
    lines.append("")

    lines.append("## File Inventory")
    for item in manifest:
        detail = f"type={item.detected_type or 'unknown'} | supported={str(item.supported).lower()}"
        if item.recommended_skill:
            detail += f" | recommended_skill={item.recommended_skill}"
        if item.skip_reason:
            detail += f" | reason={item.skip_reason}"
        lines.append(f"- `{item.relative_path}` | {detail}")
    lines.append("")

    lines.append("## Supported Items and Recommended Child Output Paths")
    supported = [item for item in routed if item.recommended_skill]
    if supported:
        for item in supported:
            lines.append(
                f"- `{item.relative_path}` -> {item.recommended_skill} | status={item.downstream_status} | child_output_path={item.child_output_path}"
            )
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Skipped / Unsupported Items")
    rejected = [item for item in routed if not item.recommended_skill]
    if rejected:
        for item in rejected:
            reason = item.notes or item.downstream_status
            lines.append(f"- `{item.relative_path}` | {reason}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Next Step for the Agent")
    lines.append("- Read `routed_items.json` and run the recommended existing child skill for each supported file.")
    lines.append("- Write each child grounding output under the current archive bundle's `child_outputs/` directory, not the global grounding root.")
    lines.append("- Only after child bundles are produced should you write a real archive-level `grounded.md`.")
    return "\n".join(lines) + "\n"


def write_json(path: Path, payload: Dict | List) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def get_beijing_timestamp() -> str:
    """Get a Beijing-time timestamp string in format YYYYMMDDHHMMSS."""
    from datetime import datetime, timezone, timedelta
    tz_beijing = timezone(timedelta(hours=8))
    now = datetime.now(tz_beijing)
    return now.strftime("%Y%m%d%H%M%S")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ground a ZIP archive into an archive-level bundle.")
    parser.add_argument("--input_zip", required=True)
    parser.add_argument("--output_root", required=True)
    args = parser.parse_args()

    input_zip = Path(args.input_zip).expanduser().resolve()
    output_root = Path(args.output_root).expanduser().resolve()

    if not input_zip.exists():
        raise ArchiveGroundingError(f"Input zip not found: {input_zip}")
    if input_zip.suffix.lower() != ".zip":
        raise ArchiveGroundingError("Only .zip archives are supported in this skill.")

    inspect_zip(input_zip)

    # Generate GROUND_ID: archive-safe_stem_timestamp
    timestamp = get_beijing_timestamp()
    archive_id = safe_stem(input_zip.name)
    ground_id = f"archive-{archive_id}_{timestamp}"
    bundle_dir = output_root / ground_id
    unpack_dir = bundle_dir / "unpacked"
    child_outputs_dir = bundle_dir / "child_outputs"

    bundle_dir.mkdir(parents=True, exist_ok=True)
    child_outputs_dir.mkdir(parents=True, exist_ok=True)

    unpack_zip(input_zip, unpack_dir)
    manifest, routed = build_manifest(unpack_dir, child_outputs_dir)
    extracted_meta = build_extracted_meta(input_zip, ground_id, manifest)
    extracted_md = build_extracted_md(input_zip, ground_id, manifest, routed)

    (bundle_dir / "extracted.md").write_text(extracted_md, encoding="utf-8")
    write_json(bundle_dir / "extracted_meta.json", extracted_meta)
    write_json(bundle_dir / "manifest.json", [asdict(item) for item in manifest])
    write_json(bundle_dir / "routed_items.json", [asdict(item) for item in routed])

    # Write ground_id.txt for downstream stages to reuse
    (bundle_dir / "ground_id.txt").write_text(ground_id + "\n", encoding="utf-8")

    print(f"[archive-grounding] ground_id={ground_id}")
    print(f"[archive-grounding] bundle_dir={bundle_dir}")
    print(f"[archive-grounding] extracted_md={bundle_dir / 'extracted.md'}")
    print(f"[archive-grounding] manifest_json={bundle_dir / 'manifest.json'}")
    print(f"[archive-grounding] routed_items_json={bundle_dir / 'routed_items.json'}")
    print(f"[archive-grounding] child_outputs_dir={child_outputs_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ArchiveGroundingError as exc:
        print(f"[archive-grounding] ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
