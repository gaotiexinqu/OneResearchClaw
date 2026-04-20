from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


SUMMARY_TITLES = (
    "executive summary",
    "summary",
    "highlights",
    "key findings",
    "key takeaways",
    "overview",
    # Chinese variants
    "执行摘要",
    "摘要",
    "概要",
    "核心发现",
    "核心要点",
    "概述",
)
CLOSING_TITLES = (
    "conclusion",
    "conclusions",
    "next steps",
    "recommendations",
    "final remarks",
    # Chinese variants
    "结论",
    "建议",
    "后续步骤",
    "建议下一步",
    "最终评论",
)


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_title(lines: List[str], fallback: str) -> str:
    for line in lines:
        m = re.match(r"^#\s+(.*)$", line.strip())
        if m:
            return _normalize_text(m.group(1))
    return fallback


def _infer_ground_id(input_report: Path) -> str:
    return input_report.parent.name if input_report.parent.name else input_report.stem


def _is_table_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2


def _is_table_separator(line: str) -> bool:
    stripped = line.strip().strip("|").strip()
    if not stripped:
        return False
    cells = [c.strip() for c in stripped.split("|")]
    return all(re.fullmatch(r":?-{3,}:?", c) for c in cells)


def _clean_inline_markdown(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = text.replace("**", "").replace("__", "")
    text = text.replace("*", "").replace("_", "")
    return _normalize_text(text)


def _split_long_text(text: str, max_len: int = 210) -> List[str]:
    text = _clean_inline_markdown(text)
    if len(text) <= max_len:
        return [text] if text else []

    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) <= 1:
        words = text.split()
        chunks: List[str] = []
        cur: List[str] = []
        cur_len = 0
        for word in words:
            extra = len(word) + (1 if cur else 0)
            if cur and cur_len + extra > max_len:
                chunks.append(" ".join(cur))
                cur = [word]
                cur_len = len(word)
            else:
                cur.append(word)
                cur_len += extra
        if cur:
            chunks.append(" ".join(cur))
        return chunks

    chunks: List[str] = []
    cur = ""
    for sent in sentences:
        candidate = sent if not cur else f"{cur} {sent}"
        if cur and len(candidate) > max_len:
            chunks.append(cur)
            cur = sent
        else:
            cur = candidate
    if cur:
        chunks.append(cur)
    return chunks


def _parse_table(lines: List[str]) -> Tuple[List[str], List[List[str]]]:
    rows: List[List[str]] = []
    for line in lines:
        stripped = line.strip().strip("|")
        cells = [_clean_inline_markdown(c.strip()) for c in stripped.split("|")]
        rows.append(cells)
    if len(rows) >= 2 and _is_table_separator(lines[1]):
        header = rows[0]
        body = rows[2:]
    else:
        header = rows[0] if rows else []
        body = rows[1:] if len(rows) > 1 else []
    width = len(header)
    normalized = []
    for row in body:
        if len(row) < width:
            row = row + [""] * (width - len(row))
        elif len(row) > width:
            row = row[:width]
        normalized.append(row)
    return header, normalized


def parse_markdown(input_report: Path) -> Dict:
    raw = input_report.read_text(encoding="utf-8")
    lines = raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    title = _extract_title(lines, fallback=input_report.stem)

    sections: List[Dict] = []
    current: Optional[Dict] = {"title": "Overview", "blocks": []}
    sections.append(current)

    def ensure_section(name: Optional[str] = None) -> Dict:
        nonlocal current
        if current is None:
            current = {"title": name or "Overview", "blocks": []}
            sections.append(current)
        return current

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        if not stripped:
            i += 1
            continue

        h1 = re.match(r"^#\s+(.*)$", stripped)
        if h1:
            i += 1
            continue

        h2 = re.match(r"^##\s+(.*)$", stripped)
        if h2:
            current = {"title": _clean_inline_markdown(h2.group(1)), "blocks": []}
            sections.append(current)
            i += 1
            continue

        h3 = re.match(r"^###\s+(.*)$", stripped)
        if h3:
            ensure_section("Overview")["blocks"].append(
                {"type": "subhead", "text": _clean_inline_markdown(h3.group(1))}
            )
            i += 1
            continue

        img = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)", stripped)
        if img:
            ensure_section("Overview")["blocks"].append(
                {"type": "image", "alt": _clean_inline_markdown(img.group(1)), "path": img.group(2).strip()}
            )
            i += 1
            continue

        if _is_table_line(stripped):
            table_lines = [stripped]
            i += 1
            while i < len(lines) and _is_table_line(lines[i].strip()):
                table_lines.append(lines[i].strip())
                i += 1
            headers, rows = _parse_table(table_lines)
            if headers:
                ensure_section("Overview")["blocks"].append({"type": "table", "headers": headers, "rows": rows})
            continue

        bullet = re.match(r"^[-*+]\s+(.*)$", stripped) or re.match(r"^\d+[.)]\s+(.*)$", stripped)
        if bullet:
            items = [_clean_inline_markdown(bullet.group(1))]
            i += 1
            while i < len(lines):
                nxt = lines[i].strip()
                m = re.match(r"^[-*+]\s+(.*)$", nxt) or re.match(r"^\d+[.)]\s+(.*)$", nxt)
                if not m:
                    break
                items.append(_clean_inline_markdown(m.group(1)))
                i += 1
            ensure_section("Overview")["blocks"].append({"type": "bullet_list", "items": items})
            continue

        para_lines = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt:
                break
            if re.match(r"^#{1,3}\s+", nxt):
                break
            if re.match(r"^!\[[^\]]*\]\(([^)]+)\)", nxt):
                break
            if _is_table_line(nxt):
                break
            if re.match(r"^[-*+]\s+", nxt) or re.match(r"^\d+[.)]\s+", nxt):
                break
            para_lines.append(nxt)
            i += 1
        paragraph = _clean_inline_markdown(" ".join(para_lines))
        if paragraph:
            ensure_section("Overview")["blocks"].append({"type": "paragraph", "text": paragraph})

    cleaned_sections = [s for s in sections if s.get("blocks")]
    return {"title": title, "sections": cleaned_sections or sections}


def _section_kind(title: str) -> str:
    t = title.lower().strip()
    if any(key in t for key in SUMMARY_TITLES):
        return "summary"
    if any(key in t for key in CLOSING_TITLES):
        return "closing"
    return "section"


def _resolve_image_path(raw_path: str, source_report: Path) -> str:
    p = Path(raw_path)
    if p.is_absolute():
        return str(p)
    return str((source_report.parent / p).resolve())


def _plain_section_title(title: str) -> str:
    return _normalize_text(re.sub(r"^\d+[.)]?\s*", "", title).strip()) or title


def _extract_section_number(title: str, fallback: int) -> int:
    m = re.match(r"^(\d+)[.)]?\s+", title.strip())
    return int(m.group(1)) if m else fallback


def _section_theme(title: str, kind: str) -> str:
    t = title.lower()
    if kind == "summary":
        return "blue"
    if kind == "closing":
        return "purple"
    if "problem" in t or "setting" in t:
        return "blue"
    if "understanding" in t or "analysis" in t or "findings" in t:
        return "teal"
    if "literature" in t or "support" in t or "background" in t:
        return "indigo"
    if "action" in t or "recommend" in t or "plan" in t:
        return "green"
    if "risk" in t or "caveat" in t or "limitation" in t or "warning" in t:
        return "red"
    if "question" in t or "open" in t:
        return "amber"
    return "slate"


def _normalize_text_blocks(blocks: List[Dict]) -> Tuple[Optional[str], List[str]]:
    lead: Optional[str] = None
    bullets: List[str] = []
    pending_subhead: Optional[str] = None

    for block in blocks:
        btype = block["type"]
        if btype == "subhead":
            pending_subhead = block["text"]
            continue

        if btype == "bullet_list":
            items = block.get("items", [])
            for idx, item in enumerate(items):
                text = item
                if idx == 0 and pending_subhead:
                    text = f"{pending_subhead}: {text}"
                    pending_subhead = None
                bullets.extend(_split_long_text(text))
            continue

        if btype == "paragraph":
            pieces = _split_long_text(block.get("text", ""))
            if not pieces:
                continue
            if lead is None and len(pieces[0]) <= 220 and len(blocks) > 1:
                lead = pieces[0]
                pieces = pieces[1:]
            if pending_subhead and pieces:
                pieces[0] = f"{pending_subhead}: {pieces[0]}"
                pending_subhead = None
            bullets.extend(pieces)
            continue

    if pending_subhead:
        bullets.append(pending_subhead)
    bullets = [_normalize_text(b) for b in bullets if _normalize_text(b)]
    return lead, bullets


def _chunk(items: List[str], size: int) -> List[List[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)] or [[]]


def _compact_adjacent_items(items: List[str], max_len: int = 220) -> List[str]:
    if len(items) <= 1:
        return items
    merged: List[str] = []
    cur = items[0]
    for nxt in items[1:]:
        if (
            len(cur) <= 120
            and len(nxt) <= 120
            and len(cur) + 1 + len(nxt) <= max_len
            and not cur.endswith(":")
        ):
            cur = f"{cur} {nxt}"
        else:
            merged.append(cur)
            cur = nxt
    merged.append(cur)
    return merged


def _is_dense_section(title: str) -> bool:
    t = title.lower()
    dense_keys = (
        "literature", "support", "risk", "caveat", "limitation",
        "question", "open", "action", "recommend", "plan",
    )
    return any(k in t for k in dense_keys)


def build_slide_plan(parsed: Dict, source_report: Path) -> Dict:
    title = parsed["title"]
    ground_id = _infer_ground_id(source_report)
    sections = parsed["sections"]

    slides: List[Dict] = [{
        "type": "title",
        "title": title,
        "subtitle": f"Grounded item: {ground_id}",
    }]

    for fallback_idx, section in enumerate(sections, start=1):
        section_title = section.get("title") or "Overview"
        kind = _section_kind(section_title)
        section_number = _extract_section_number(section_title, fallback_idx)
        plain_title = _plain_section_title(section_title)
        theme = _section_theme(section_title, kind)
        text_buffer: List[Dict] = []

        def flush_text_buffer() -> None:
            nonlocal text_buffer
            if not text_buffer:
                return
            lead, bullets = _normalize_text_blocks(text_buffer)
            if not bullets and lead:
                bullets = [lead]
                lead = None
            if not bullets:
                text_buffer = []
                return

            if len(bullets) > 8:
                bullets = _compact_adjacent_items(bullets)

            if kind in {"summary", "closing"}:
                chunks = _chunk(bullets, 4)
                for idx, chunk in enumerate(chunks):
                    page_title = section_title if idx == 0 else f"{section_title} (cont.)"
                    slides.append({
                        "type": kind,
                        "title": page_title,
                        "lead": lead if idx == 0 else None,
                        "bullets": chunk,
                        "source_section": section_title,
                        "section_number": section_number,
                        "section_plain_title": plain_title,
                        "theme": theme,
                    })
                text_buffer = []
                return

            dense_section = _is_dense_section(section_title)
            continuation_capacity = 6 if dense_section else 5
            first_support_capacity = 4

            if lead:
                takeaway = lead
                first_support = bullets[:first_support_capacity]
                remaining = bullets[first_support_capacity:]
            else:
                takeaway = bullets[0] if bullets else ""
                first_support = bullets[1:1 + first_support_capacity]
                remaining = bullets[1 + first_support_capacity:]
                if not first_support and takeaway:
                    first_support = [takeaway]

            slides.append({
                "type": "insight",
                "title": section_title,
                "lead": lead,
                "takeaway": takeaway,
                "bullets": first_support[:3],
                "source_section": section_title,
                "section_number": section_number,
                "section_plain_title": plain_title,
                "theme": theme,
            })

            for idx, chunk in enumerate(_chunk(remaining, continuation_capacity), start=1):
                if not chunk:
                    continue
                page_title = f"{section_title} (cont.)"
                slides.append({
                    "type": "bullets",
                    "title": page_title,
                    "bullets": chunk,
                    "source_section": section_title,
                    "section_number": section_number,
                    "section_plain_title": plain_title,
                    "theme": theme,
                    "dense_layout": dense_section,
                })
            text_buffer = []

        for block in section["blocks"]:
            if block["type"] in {"paragraph", "bullet_list", "subhead"}:
                text_buffer.append(block)
                continue

            flush_text_buffer()

            if block["type"] == "table":
                slides.append({
                    "type": "table",
                    "title": section_title,
                    "headers": block.get("headers", []),
                    "rows": block.get("rows", []),
                    "source_section": section_title,
                    "section_number": section_number,
                    "section_plain_title": plain_title,
                    "theme": theme,
                })
            elif block["type"] == "image":
                slides.append({
                    "type": "figure",
                    "title": section_title,
                    "image_path": _resolve_image_path(block.get("path", ""), source_report),
                    "caption": block.get("alt") or "Figure",
                    "source_section": section_title,
                    "section_number": section_number,
                    "section_plain_title": plain_title,
                    "theme": theme,
                })

        flush_text_buffer()

    plan = {
        "meta": {
            "report_title": title,
            "ground_id": ground_id,
            "source_report": str(source_report),
            "plan_version": "v3-condensed",
            "section_count": len(sections),
        },
        "slides": slides,
    }
    return plan


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        print("Usage: python plan_slides.py <input_report_path> <output_slide_plan_json>", file=sys.stderr)
        return 2

    input_report = Path(argv[1]).expanduser().resolve()
    output_path = Path(argv[2]).expanduser().resolve()

    if not input_report.exists():
        raise FileNotFoundError(f"Input report not found: {input_report}")
    if input_report.is_dir():
        raise IsADirectoryError(f"Expected a markdown report file, got directory: {input_report}")

    parsed = parse_markdown(input_report)
    plan = build_slide_plan(parsed, input_report)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"written": str(output_path), "slides": len(plan.get("slides", []))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
