#!/usr/bin/env python3
"""CLI helper for downloading papers from various sources.

Used by the ``remote-input`` skill (skills/remote-input/SKILL.md).

Commands
--------
download  Download a paper PDF by URL or paper ID.

Examples
--------
python3 download_arxiv.py download "2301.07041"
python3 download_arxiv.py download "https://arxiv.org/abs/2301.07041"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

_USER_AGENT = "research-bot/1.0"
_TIMEOUT = 120
_MIN_PDF_BYTES = 10_240

_NEW_STYLE_ID_RE = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")
_OLD_STYLE_ID_RE = re.compile(r"^[A-Za-z.-]+/\d{7}(v\d+)?$")
_ARXIV_URL_RE = re.compile(
    r'(?:https?://)?(?:www\.)?arxiv\.org/(?:abs|pdf)/(\d+\.\d+(?:v\d+)?)'
)


def is_arxiv_url(value: str) -> bool:
    """Return True when the input is an arXiv URL."""
    return bool(_ARXIV_URL_RE.search(value.strip()))


def extract_arxiv_id_from_url(url: str) -> str | None:
    """Extract arXiv ID from various URL formats."""
    match = _ARXIV_URL_RE.search(url.strip())
    if match:
        return _normalize_id(match.group(1))
    return None


def _normalize_id(paper_id: str) -> str:
    """Strip URL/version noise and return a clean paper ID."""
    value = paper_id.strip()
    if "/abs/" in value:
        value = value.split("/abs/", 1)[1]
    if value.startswith("id:"):
        value = value[3:]
    if "v" in value.split(".")[-1]:
        value = value.rsplit("v", 1)[0]
    return value


def _looks_like_arxiv_id(value: str) -> bool:
    """Return True when the input resembles an arXiv paper ID."""
    value = value.strip()
    return bool(_NEW_STYLE_ID_RE.match(value) or _OLD_STYLE_ID_RE.match(value))


def _is_url(value: str) -> bool:
    """Check if the input is a URL."""
    return value.strip().startswith(("http://", "https://"))


def download(paper_id_or_url: str, output_dir: str = "papers") -> dict:
    """Download a paper PDF and return metadata about the saved file.
    
    Args:
        paper_id_or_url: Paper ID (e.g. 2301.07041) or URL (e.g. https://arxiv.org/abs/2301.07041)
        output_dir: Output directory
    
    Returns:
        dict with keys: success, path, size_kb, paper_id, skipped, error
    """
    input_value = paper_id_or_url.strip()
    
    # Extract paper ID from URL if needed
    if _is_url(input_value):
        if is_arxiv_url(input_value):
            extracted_id = extract_arxiv_id_from_url(input_value)
            if extracted_id:
                paper_id = extracted_id
            else:
                return {
                    "success": False,
                    "path": None,
                    "paper_id": None,
                    "error": f"Could not extract paper ID from URL: {input_value}"
                }
        else:
            return {
                "success": False,
                "path": None,
                "paper_id": None,
                "error": f"Unsupported URL format: {input_value}"
            }
    else:
        # Treat as paper ID
        if not _looks_like_arxiv_id(input_value):
            return {
                "success": False,
                "path": None,
                "paper_id": None,
                "error": f"Invalid paper ID format: {input_value}"
            }
        paper_id = _normalize_id(input_value)
    
    safe_id = paper_id.replace("/", "_")

    dest_dir = Path(output_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{safe_id}.pdf"

    if dest.exists():
        return {
            "success": True,
            "path": str(dest),
            "size_kb": dest.stat().st_size // 1024,
            "paper_id": paper_id,
            "skipped": True,
        }

    pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"
    req = urllib.request.Request(pdf_url, headers={"User-Agent": _USER_AGENT})

    for attempt in (1, 2, 3):
        try:
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                data = resp.read()
            break
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            if attempt < 3:
                time.sleep(3)
                continue
            return {
                "success": False,
                "path": None,
                "paper_id": paper_id,
                "error": f"Failed to download after 3 attempts: {exc}"
            }

    if len(data) < _MIN_PDF_BYTES:
        return {
            "success": False,
            "path": None,
            "paper_id": paper_id,
            "error": f"Downloaded file is only {len(data)} bytes - likely an error page"
        }

    dest.write_bytes(data)

    return {
        "success": True,
        "path": str(dest),
        "size_kb": len(data) // 1024,
        "paper_id": paper_id,
        "skipped": False,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download papers from various sources.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    download_parser = subparsers.add_parser("download", help="Download a paper PDF")
    download_parser.add_argument(
        "id",
        help="Paper ID or full URL",
    )
    download_parser.add_argument(
        "--dir",
        default="papers",
        metavar="DIR",
        help="Output directory (default: papers).",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.command == "download":
        result = download(args.id, output_dir=args.dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("success") else 1

    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    sys.exit(main())