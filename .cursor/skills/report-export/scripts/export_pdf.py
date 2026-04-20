from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from export_docx import markdown_to_docx, _resolve_font


class PDFExportError(RuntimeError):
    pass


def _find_office_binary() -> str:
    for candidate in ("libreoffice", "soffice"):
        path = shutil.which(candidate)
        if path:
            return path
    raise PDFExportError("Could not find libreoffice/soffice in PATH for PDF export.")


def _check_cjk_fonts() -> bool:
    """Return True if any CJK font is available via fc-list."""
    if not shutil.which("fc-list"):
        return False
    result = subprocess.run(
        ["fc-list", ":lang=zh"],
        capture_output=True, text=True, timeout=10,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def _install_cjk_fonts() -> None:
    """Attempt to install CJK font package if none is found."""
    if _check_cjk_fonts():
        return
    packages = ["fonts-noto-cjk", "fonts-wqy-zenhei"]
    for pkg in packages:
        result = subprocess.run(
            ["sudo", "apt-get", "install", "-y", pkg],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            subprocess.run(["sudo", "fc-cache", "-fv"], capture_output=True, timeout=30)
            if _check_cjk_fonts():
                return
    raise PDFExportError(
        "No CJK font detected and could not install fonts-noto-cjk automatically. "
        "Please run: sudo apt-get install -y fonts-noto-cjk"
    )


def _ensure_cjk_fonts_for_lang(lang: str) -> None:
    """If the output language requires CJK fonts, ensure at least one is available."""
    if lang != "zh":
        return
    if _check_cjk_fonts():
        return
    _install_cjk_fonts()


def export_pdf(input_report: Path, output_dir: Path, output_lang: str = "en") -> Path:
    # output_dir is base_dir/format when called from export_report.py
    # -> strip /format, add /output_lang to get base_dir/lang
    final_dir = output_dir.parent / output_lang
    final_dir.mkdir(parents=True, exist_ok=True)
    output_path = final_dir / "report.pdf"

    # Ensure CJK fonts are available before LibreOffice runs
    _ensure_cjk_fonts_for_lang(output_lang)

    office = _find_office_binary()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        docx_path = tmpdir_path / "report.docx"
        
        # Check if a pre-translated markdown file exists (e.g., from export_md translation)
        # If output_lang is zh and source is en, look for translated version first
        translated_md: Path | None = None
        if output_lang == "zh":
            # Look for zh translated version: output_dir/parent/zh/report.md
            zh_md_candidate = (output_dir.parent / output_lang / "report.md")
            if zh_md_candidate.exists():
                translated_md = zh_md_candidate
        
        # Use translated markdown if available, otherwise use original
        source_md = translated_md if translated_md else input_report
        markdown_to_docx(source_md, docx_path, output_lang)

        cmd = [
            office,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(tmpdir_path),
            str(docx_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise PDFExportError(
                f"LibreOffice PDF export failed with code {proc.returncode}.\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
            )

        produced = tmpdir_path / "report.pdf"
        if not produced.exists() or produced.stat().st_size == 0:
            raise PDFExportError("LibreOffice did not produce a non-empty PDF file.")

        shutil.copy2(produced, output_path)

    return output_path
