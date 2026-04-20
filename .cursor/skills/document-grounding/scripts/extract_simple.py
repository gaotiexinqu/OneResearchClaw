#!/usr/bin/env python3
"""
Simple document extraction for PDF using pypdf.
"""

import argparse
import csv
import json
import re
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _slugify(text: str, max_len: int = 80) -> str:
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"[^A-Za-z0-9._-]", "_", text)
    text = re.sub(r"_+", "_", text)
    text = text.strip("_-")
    return (text[:max_len] or "item")


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_text(path: Path, text: str) -> None:
    _ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def _clean_text(text: str) -> str:
    lines = text.splitlines()
    cleaned: List[str] = []
    blank = False
    for line in lines:
        line = line.rstrip()
        stripped = line.strip()
        if re.fullmatch(r"\d+", stripped):
            continue
        line = re.sub(r"[ \t]{2,}", " ", line)
        if stripped == "":
            if not blank:
                cleaned.append("")
            blank = True
        else:
            cleaned.append(line)
            blank = False
    while cleaned and cleaned[-1] == "":
        cleaned.pop()
    return "\n".join(cleaned).strip()


def _guess_title_from_markdown(md: str) -> Optional[str]:
    for line in md.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            return s.lstrip("#").strip()
        return s[:200]
    return None


def _extract_formula_blocks(text: str, formulas_dir: Path) -> List[Dict[str, Any]]:
    _ensure_dir(formulas_dir)
    out: List[Dict[str, Any]] = []
    patterns = [
        re.compile(r"\$\$(.+?)\$\$", re.S),
        re.compile(r"\\begin\{equation\}(.+?)\\end\{equation\}", re.S),
        re.compile(r"\\begin\{align\}(.+?)\\end\{align\}", re.S),
    ]
    seen: List[str] = []
    for pat in patterns:
        for m in pat.findall(text):
            s = m.strip()
            if len(s) < 3:
                continue
            if s in seen:
                continue
            seen.append(s)
    for i, formula in enumerate(seen, start=1):
        fid = f"formula_{i:03d}"
        path = formulas_dir / f"{fid}.txt"
        _write_text(path, formula)
        out.append({"id": fid, "path": str(path)})
    return out


def _extract_pdf_pypdf(pdf_path: str) -> Tuple[str, int]:
    from pypdf import PdfReader
    reader = PdfReader(pdf_path)
    pages = len(reader.pages)
    all_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            all_text.append(text)
    return "\n\n".join(all_text), pages


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract text from PDF using pypdf")
    parser.add_argument("input_path", help="Path to PDF")
    parser.add_argument("bundle_dir", help="Output bundle directory")
    args = parser.parse_args()

    input_path = Path(args.input_path).resolve()
    bundle_dir = Path(args.bundle_dir).resolve()
    _ensure_dir(bundle_dir)

    # Extract text
    print(f"[INFO] Extracting text from: {input_path}")
    try:
        text, num_pages = _extract_pdf_pypdf(str(input_path))
    except Exception as e:
        print(f"[ERROR] Failed to extract PDF: {e}")
        sys.exit(1)

    cleaned_text = _clean_text(text)
    guessed_title = _guess_title_from_markdown(cleaned_text)

    # Extract formulas
    assets_dir = bundle_dir / "assets"
    formulas_dir = assets_dir / "formulas"
    tables_dir = assets_dir / "tables"
    figures_dir = assets_dir / "figures"
    _ensure_dir(tables_dir)
    _ensure_dir(figures_dir)
    _ensure_dir(formulas_dir)

    formulas = _extract_formula_blocks(cleaned_text, formulas_dir)

    asset_index = {
        "source_file": input_path.name,
        "source_type": "pdf",
        "tables": [],
        "figures": [],
        "formulas": formulas,
    }

    _write_text(bundle_dir / "extracted.md", cleaned_text)
    _safe_write_json(bundle_dir / "asset_index.json", asset_index)

    extracted_meta = {
        "source_file": input_path.name,
        "source_type": "pdf",
        "original_path": str(input_path),
        "guessed_title": guessed_title,
        "char_count": len(cleaned_text),
        "line_count": len(cleaned_text.splitlines()),
        "page_count": num_pages,
        "table_count": 0,
        "figure_count": 0,
        "formula_count": len(formulas),
        "extraction_method": "pypdf",
        "grounded_note_generated_by_script": False,
    }
    _safe_write_json(bundle_dir / "extracted_meta.json", extracted_meta)

    print(f"[OK] Extraction complete: {bundle_dir}")
    print(f"[OK] Text length: {len(cleaned_text)} chars, {num_pages} pages")


def _json_safe(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Path):
        return str(obj)
    if callable(obj):
        return None
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_json_safe(x) for x in obj]
    try:
        json.dumps(obj)
        return obj
    except Exception:
        try:
            return str(obj)
        except Exception:
            return None


def _safe_write_json(path: Path, data: Dict[str, Any]) -> None:
    _ensure_dir(path.parent)
    safe = _json_safe(data)
    path.write_text(json.dumps(safe, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()