from __future__ import annotations

import re
from pathlib import Path
from typing import List

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

        # Skip standalone horizontal rules (---, ***, ___)
        if _HR_RE.match(line):
            # Check if the next non-blank line is a pipeline footer — if so, skip the whole block
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and _PIPELINE_FOOTER_RE.search(lines[j]):
                i = j + 1
                continue
            i += 1
            continue

        # Skip pipeline production metadata footnotes (standalone or inline)
        if _PIPELINE_FOOTER_RE.search(line):
            i += 1
            continue

        out.append(line)
        i += 1
    return out


def export_md(input_report: Path, output_dir: Path, output_lang: str = "en") -> Path:
    # output_dir is base_dir/format when called from export_report.py
    # -> strip /format, add /output_lang to get base_dir/lang
    final_dir = output_dir.parent / output_lang
    final_dir.mkdir(parents=True, exist_ok=True)
    output_path = final_dir / "report.md"
    text = input_report.read_text(encoding="utf-8")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = _filter_meta_lines(text.split("\n"))
    text = "\n".join(lines)
    if not text.endswith("\n"):
        text += "\n"
    output_path.write_text(text, encoding="utf-8")
    return output_path
