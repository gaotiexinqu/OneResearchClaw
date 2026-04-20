from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Callable, Dict, Iterable, List

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from export_audio import export_audio
from export_docx import export_docx
from export_md import export_md
from export_pdf import export_pdf
from export_pptx import export_pptx

SUPPORTED_FORMATS: Dict[str, Callable[[Path, Path, str], Path]] = {
    "md": export_md,
    "docx": export_docx,
    "pdf": export_pdf,
    "pptx": export_pptx,
    "audio": export_audio,
}

# Filter patterns for report-production metadata that should not appear in exports
_HR_RE = re.compile(r"^\s*[-*_]{3,}\s*$")
_PIPELINE_FOOTER_RE = re.compile(
    r"^\s*\*?\s*(本报告通过|报告产出：|Report produced|Manuscript prepared)",
    re.IGNORECASE,
)


def _filter_meta_lines(lines: List[str]) -> List[str]:
    """Drop horizontal rules, pipeline production footnotes, and consecutive blank lines."""
    out: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip standalone horizontal rules (---, ***, ___)
        if _HR_RE.match(line):
            # Check if the next non-blank line is a pipeline footer — if so, skip the whole block
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and _PIPELINE_FOOTER_RE.search(lines[j]):
                # Skip the HR, all following blank lines, the footer line itself, and any trailing blanks
                k = j + 1
                while k < len(lines) and not lines[k].strip():
                    k += 1
                i = k
                continue
            # Otherwise skip only the HR line itself
            i += 1
            continue

        # Skip pipeline production metadata footnotes (standalone or inline)
        if _PIPELINE_FOOTER_RE.search(line):
            i += 1
            continue

        out.append(line)
        i += 1
    return out


def _strip_pipeline_metadata(text: str) -> str:
    """Remove pipeline production metadata (HR separators + production footnotes)."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    filtered = _filter_meta_lines(lines)
    return "\n".join(filtered) + "\n"


def _parse_formats(raw: str) -> List[str]:
    formats = [item.strip().lower() for item in raw.split(",") if item.strip()]
    if not formats:
        raise ValueError("No export format specified.")
    unsupported = [f for f in formats if f not in SUPPORTED_FORMATS]
    if unsupported:
        raise ValueError(
            "Unsupported format(s): " + ", ".join(unsupported) + ". Supported formats: " + ", ".join(SUPPORTED_FORMATS)
        )
    # preserve order while deduplicating
    seen = set()
    out = []
    for f in formats:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def _infer_ground_id(input_report: Path) -> str:
    if input_report.parent.name:
        return input_report.parent.name
    return input_report.stem


def _ensure_input(input_report: Path) -> None:
    if not input_report.exists():
        raise FileNotFoundError(f"Input report not found: {input_report}")
    if input_report.is_dir():
        raise IsADirectoryError(f"Input report path is a directory, expected a markdown file: {input_report}")


def export_report(input_report: Path, output_root: Path, formats: Iterable[str], output_lang: str = "en") -> Dict[str, str]:
    _ensure_input(input_report)
    ground_id = _infer_ground_id(input_report)
    base_dir = output_root / ground_id
    written: Dict[str, str] = {}

    # Strip pipeline metadata once, reuse for pptx and audio
    raw_text = input_report.read_text(encoding="utf-8")
    cleaned_text = _strip_pipeline_metadata(raw_text)

    # For output_lang=zh, check for pre-translated content
    translated_text: str | None = None
    zh_md_path = base_dir / output_lang / "report.md"
    if output_lang == "zh" and zh_md_path.exists():
        # Use existing translation
        translated_text = _strip_pipeline_metadata(zh_md_path.read_text(encoding="utf-8"))
        print(f"[report-export] Using existing translation: {zh_md_path}")
    elif output_lang == "zh":
        print(f"[report-export] WARNING: No translation found at {zh_md_path}")
        print(f"[report-export] For proper Chinese output, please translate the report first:")
        print(f"[report-export]   1. Create the translated markdown file")
        print(f"[report-export]   2. Re-run export with the same parameters")
        print(f"[report-export] Falling back to original text with Chinese font settings.")

    # Formats that need their own cleaned file on disk
    needs_clean_file = {"pptx", "audio"}
    # Formats that handle filtering internally
    handles_own_filter = {"md", "docx", "pdf"}

    # Write shared cleaned temp file for pptx/audio
    clean_path: Path | None = None
    if needs_clean_file & set(formats):
        # Use translated text if available, otherwise use original
        content_to_write = translated_text if translated_text else cleaned_text
        with tempfile.NamedTemporaryFile(
            suffix=".md", prefix="report_export_clean_", mode="w", encoding="utf-8", delete=False
        ) as f:
            f.write(content_to_write)
            clean_path = Path(f.name)

    # For md format with translation, write translated content
    md_translated_path: Path | None = None
    if "md" in formats and translated_text is not None:
        md_dir = base_dir / "md" / output_lang
        md_dir.mkdir(parents=True, exist_ok=True)
        md_translated_path = md_dir / "report.md"
        md_translated_path.write_text(translated_text, encoding="utf-8")

    try:
        for fmt in formats:
            exporter = SUPPORTED_FORMATS[fmt]
            output_dir = base_dir / fmt
            if fmt in needs_clean_file and clean_path is not None:
                # Use the cleaned temp file for formats that don't handle filtering
                path = exporter(clean_path, output_dir, output_lang)
            elif fmt == "md" and md_translated_path is not None:
                # Use translated markdown for md format
                path = md_translated_path
                written[fmt] = str(path)
                continue
            else:
                # md/docx/pdf handle filtering internally
                # pdf will check for translated md in parent zh/ dir
                path = exporter(input_report, output_dir, output_lang)
            written[fmt] = str(path)
    finally:
        if clean_path is not None:
            clean_path.unlink(missing_ok=True)

    return written


def main(argv: List[str]) -> int:
    if len(argv) < 4:
        print(
            "Usage: python export_report.py <input_report_path> <output_root> <format_or_comma_separated_formats> [output_lang]",
            file=sys.stderr,
        )
        return 2

    input_report = Path(argv[1]).expanduser().resolve()
    output_root = Path(argv[2]).expanduser().resolve()
    formats = _parse_formats(argv[3])
    output_lang = argv[4] if len(argv) > 4 else "en"
    written = export_report(input_report, output_root, formats, output_lang)
    print(json.dumps({"written": written, "output_lang": output_lang}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
