#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

_MAX_SECTION_CHARS = 3000
_MAX_EXCERPTS = 12
_EXCERPT_KEYWORDS = (
    'we propose', 'we present', 'we introduce', 'method', 'approach', 'framework',
    'benchmark', 'dataset', 'experiment', 'result', 'improv', 'outperform',
    'achiev', 'limitation', 'however', 'we find', 'we show', 'evaluation',
    'loss', 'objective', 'training', 'optimization', 'module', 'pipeline',
)
_METHOD_EXCERPT_KEYWORDS = (
    'we propose', 'framework', 'architecture', 'pipeline', 'module', 'stage',
    'training', 'optimization', 'loss', 'objective', 'reward', 'inference',
    'method', 'approach', 'algorithm', 'design', 'implemented',
)
_RESULT_EXCERPT_KEYWORDS = (
    'result', 'results', 'outperform', 'improve', 'improvement', 'achieve', 'achieved',
    'accuracy', 'auc', 'c-index', 'f1', 'recall', 'precision', 'ablation', 'baseline',
    'compared', 'vs.', 'significant', 'score',
)
_CANONICAL_SECTIONS = {
    'abstract': ('abstract',),
    'introduction': ('introduction', '1 introduction', 'background'),
    'method': (
        'method', 'methods', 'approach', 'framework', 'model', 'algorithm',
        'architecture', 'pipeline', 'training', 'optimization', 'loss', 'objective',
        'implementation', 'design'
    ),
    'experiment': ('experiment', 'experiments', 'evaluation', 'experimental setup'),
    'results': ('result', 'results', 'analysis', 'ablation'),
    'conclusion': ('conclusion', 'discussion', 'limitations', 'future work'),
}


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def _is_paper_item(d: Dict[str, Any]) -> bool:
    """Detect whether a dict is a bare paper item (has url+title but no container keys)."""
    return all(d.get(k) is not None for k in ('url', 'title'))


def _iter_items(obj: Any, _parent_was_container: bool = False) -> Iterable[Dict[str, Any]]:
    if isinstance(obj, dict):
        # 1. Standard nested containers (items / results / queries)
        for key in ('items', 'results', 'queries'):
            if isinstance(obj.get(key), list):
                for item in obj[key]:
                    if isinstance(item, dict):
                        yield item
        # 2. Bare paper item dict: has url+title but no container children
        if _is_paper_item(obj):
            yield obj
        # 3. Recurse into nested values (but do NOT treat plain dict children as paper items
        #    unless they pass _is_paper_item; this avoids yielding every nested sub-dict)
        for value in obj.values():
            yield from _iter_items(value, _parent_was_container=False)
    elif isinstance(obj, list):
        for value in obj:
            yield from _iter_items(value, _parent_was_container=True)


def _safe_slug(text: str, fallback: str) -> str:
    base = re.sub(r'[^A-Za-z0-9._-]+', '_', (text or '').strip())
    base = re.sub(r'_+', '_', base).strip('_')
    return (base[:120] or fallback)


def _extract_readable_content(text: str) -> str:
    marker = '## Readable Content'
    if marker in text:
        return text.split(marker, 1)[1].strip()
    return text.strip()


def _split_lines(content: str) -> List[str]:
    return [ln.rstrip() for ln in content.splitlines()]


def _is_heading(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if s.startswith('#'):
        return True
    if len(s) < 120 and re.match(r'^(\d+(?:\.\d+)*)?\s*[A-Z][A-Za-z0-9 /:&()\-]{2,}$', s):
        return True
    return False


def _canonical_heading(line: str) -> Optional[str]:
    s = re.sub(r'^#+\s*', '', line.strip()).lower()
    s = re.sub(r'\s+', ' ', s)
    for canonical, options in _CANONICAL_SECTIONS.items():
        for opt in options:
            if opt in s:
                return canonical
    return None


def _extract_sections(content: str) -> Dict[str, str]:
    lines = _split_lines(content)
    sections: Dict[str, List[str]] = {}
    current: Optional[str] = None
    buf: List[str] = []

    def flush() -> None:
        nonlocal buf, current
        if current and buf:
            text = '\n'.join(buf).strip()
            if text:
                sections.setdefault(current, []).append(text)
        buf = []

    for line in lines:
        if _is_heading(line):
            heading = _canonical_heading(line)
            if heading:
                flush()
                current = heading
                continue
        if current:
            buf.append(line)
    flush()

    out: Dict[str, str] = {}
    for key, chunks in sections.items():
        joined = '\n'.join(chunks).strip()
        if joined:
            out[key] = joined[:_MAX_SECTION_CHARS]

    if not out:
        flat = re.sub(r'\s+', ' ', content).strip()
        if flat:
            out['summary_like'] = flat[:_MAX_SECTION_CHARS]
    return out


def _paragraphs(content: str) -> List[str]:
    paras = [re.sub(r'\s+', ' ', p).strip() for p in re.split(r'\n\s*\n+', content) if p.strip()]
    if len(paras) <= 1:
        paras = [re.sub(r'\s+', ' ', p).strip() for p in re.split(r'(?<=[.!?])\s+', content) if p.strip()]
    return paras


def _score_paragraphs(paras: List[str], keywords: Tuple[str, ...]) -> List[Tuple[int, str]]:
    scored: List[Tuple[int, str]] = []
    for para in paras:
        lower = para.lower()
        score = sum(1 for kw in keywords if kw in lower)
        if len(para) < 60:
            score -= 1
        if len(para) > 900:
            score -= 1
        scored.append((score, para))
    scored.sort(key=lambda x: (x[0], len(x[1])), reverse=True)
    return scored


def _pick_excerpts(paras: List[str], keywords: Tuple[str, ...], cap: int = _MAX_EXCERPTS) -> List[str]:
    scored = _score_paragraphs(paras, keywords)
    picked: List[str] = []
    seen = set()
    for score, para in scored:
        if score <= 0 and picked:
            break
        norm = para[:200]
        if norm in seen:
            continue
        seen.add(norm)
        picked.append(para[:700])
        if len(picked) >= cap:
            break
    if not picked:
        picked = [p[:700] for p in paras[:3]]
    return picked


def _extract_excerpts(content: str) -> List[str]:
    return _pick_excerpts(_paragraphs(content), _EXCERPT_KEYWORDS)


def _merge_ranked_excerpts(primary: List[str], secondary: List[str], *, cap: int) -> List[str]:
    picked: List[str] = []
    seen = set()
    for para in (primary or []) + (secondary or []):
        norm = para[:200]
        if not para or norm in seen:
            continue
        seen.add(norm)
        picked.append(para[:700])
        if len(picked) >= cap:
            break
    return picked


def _extract_method_excerpts(content: str, sections: Optional[Dict[str, str]] = None) -> List[str]:
    sections = sections or {}
    section_text = "\n\n".join([sections.get('method', ''), sections.get('experiment', '')]).strip()
    primary = _pick_excerpts(_paragraphs(section_text), _METHOD_EXCERPT_KEYWORDS, cap=8) if section_text else []
    secondary = _pick_excerpts(_paragraphs(content), _METHOD_EXCERPT_KEYWORDS, cap=8)
    return _merge_ranked_excerpts(primary, secondary, cap=8)


def _extract_result_excerpts(content: str, sections: Optional[Dict[str, str]] = None) -> List[str]:
    sections = sections or {}
    section_text = "\n\n".join([sections.get('results', ''), sections.get('experiment', ''), sections.get('conclusion', '')]).strip()
    primary = _pick_excerpts(_paragraphs(section_text), _RESULT_EXCERPT_KEYWORDS, cap=8) if section_text else []
    secondary = _pick_excerpts(_paragraphs(content), _RESULT_EXCERPT_KEYWORDS, cap=8)
    return _merge_ranked_excerpts(primary, secondary, cap=8)


def _build_fallback_note(item: Dict[str, Any], paper_id: str, notes_dir: Path) -> Tuple[List[str], Dict[str, Any]]:
    """Build a minimal paper note from search_results.json metadata when source file is missing."""
    title = item.get('title') or 'Untitled'
    url = item.get('url') or ''
    key_findings = item.get('key_findings', [])
    relevance = item.get('relevance', '')
    abstract = item.get('abstract', '')

    # Compose a summary-like body from available metadata fields
    body_parts = []
    if key_findings:
        body_parts.append('## Key Findings\n')
        for kf in key_findings[:8]:
            body_parts.append(f'- {kf}')
        body_parts.append('')
    if relevance:
        body_parts.append(f'## Relevance\n{relevance}\n')
    if abstract:
        body_parts.append(f'## Abstract\n{abstract}\n')
    if not body_parts:
        body_parts.append(relevance or 'No content available from search metadata.')

    body = '\n'.join(body_parts)
    slug = _safe_slug(title, paper_id)
    note_path = notes_dir / f"{paper_id}_{slug}.md"
    note_md = [
        f"# {paper_id}: {title}",
        '',
        f"- URL: {url}",
        f"- Query group: {item.get('group') or item.get('query_group')}",
        f"- Query: {item.get('query')}",
        f"- Publish date: {item.get('publish_date')}",
        f"- Source path: {item.get('opened_source_path') or 'N/A'}",
        f"- Analysis source: metadata_fallback (source file not found on disk)",
        '',
        body,
    ]
    record = {
        'paper_id': paper_id,
        'title': title,
        'url': url,
        'publish_date': item.get('publish_date'),
        'group': item.get('group') or item.get('query_group'),
        'query': item.get('query'),
        'reader_method': 'metadata_fallback',
        'is_research_literature': item.get('is_research_literature'),
        'opened_source_path': item.get('opened_source_path', ''),
        'note_markdown_path': str(note_path),
        'content_char_count': len(body),
        'analysis_source': 'metadata_fallback',
        'refined_from_pdf': False,
        'pdf_refinement_status': 'skipped_missing_source',
        'sections': {'summary_like': body},
        'key_excerpts': key_findings,
        'method_excerpts': [],
        'result_excerpts': [],
        'evidence_density': 'low',
        'recommended_write_mode': 'formal_paper_analysis_from_metadata',
    }
    return note_md, record


def generate_notes_from_data(search_data: Dict[str, Any], output_path: Path, notes_dir: Optional[Path] = None) -> Dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if notes_dir is None:
        notes_dir = output_path.parent / 'opened_paper_notes'
    notes_dir.mkdir(parents=True, exist_ok=True)

    records: List[Dict[str, Any]] = []
    seen = set()
    skipped_missing = []   # items where source file was missing
    skipped_not_opened = []  # items that were not opened

    for item in _iter_items(search_data):
        if not item.get('opened'):
            skipped_not_opened.append(item.get('title') or item.get('url', '?'))
            continue
        if item.get('open_status') not in (None, 'success'):
            skipped_not_opened.append(item.get('title') or item.get('url', '?'))
            continue
        source_path = item.get('opened_source_path')
        title = item.get('title') or 'Untitled'
        url = item.get('url') or ''
        key = (title, url)
        if key in seen:
            continue
        seen.add(key)
        paper_id = f"P{len(records)+1:03d}"

        src = Path(source_path) if source_path else None
        if src is None or not src.exists() or src.is_dir():
            # Fallback: build note from search_results.json metadata
            skipped_missing.append(f"{title} ({source_path or 'no path'})")
            try:
                note_md, record = _build_fallback_note(item, paper_id, notes_dir)
                note_path = Path(record['note_markdown_path'])
                note_path.write_text('\n'.join(note_md), encoding='utf-8')
                records.append(record)
            except Exception as exc:
                print(f"WARNING: Failed to build fallback note for '{title}': {exc}", file=__import__('sys').stderr)
            continue
        raw = src.read_text(encoding='utf-8', errors='ignore')
        content = _extract_readable_content(raw)
        sections = _extract_sections(content)
        excerpts = _extract_excerpts(content)
        method_excerpts = _extract_method_excerpts(content, sections)
        result_excerpts = _extract_result_excerpts(content, sections)
        evidence_density = 'high' if (len(method_excerpts) >= 3 and len(result_excerpts) >= 3 and any(k in sections for k in ('method', 'results', 'experiment'))) else ('medium' if (len(method_excerpts) >= 2 or len(result_excerpts) >= 2 or any(k in sections for k in ('method', 'results', 'experiment'))) else 'low')
        slug = _safe_slug(title, paper_id)
        note_path = notes_dir / f"{paper_id}_{slug}.md"
        note_md = [
            f"# {paper_id}: {title}",
            '',
            f"- URL: {url}",
            f"- Query group: {item.get('group') or item.get('query_group')}",
            f"- Query: {item.get('query')}",
            f"- Publish date: {item.get('publish_date')}",
            f"- Reader method: {item.get('reader_method')}",
            f"- Source path: {source_path}",
            f"- Content chars: {item.get('content_char_count')}",
            f"- Analysis source: opened_page",
            '',
            '## Extracted Sections',
            '',
        ]
        for key_name, text in sections.items():
            note_md.extend([f"### {key_name}", '', text, ''])
        note_md.extend(['## Key Evidence Excerpts', ''])
        for ex in excerpts:
            note_md.extend([f"- {ex}", ''])
        note_md.extend(['## Method-Oriented Excerpts', ''])
        for ex in method_excerpts:
            note_md.extend([f"- {ex}", ''])
        note_md.extend(['## Result-Oriented Excerpts', ''])
        for ex in result_excerpts:
            note_md.extend([f"- {ex}", ''])
        note_md.extend([
            '## Narrative Writing Guide', '',
            'Each paper must remain a standalone subsection in the final literature report. Do not merge multiple downloaded papers into one mixed paragraph, grouped bullet list, or shallow recap block.', '',
            'Use the following structure for the final write-up:', '',
            '### Problem and Task Setting', '',
            'Explain what problem the paper studies, what concrete task it solves, and what benchmark / dataset / evaluation setting it uses.', '',
            '### Methodology', '',
            'Explain the actual method rather than restating the title. When available, describe the overall pipeline or stages, the key modules or architectural components, the training objective / loss / reward / optimization signal, the inference or prediction flow, and why this design should help.', '',
            '### Main Evidence', '',
            'Explain the most relevant empirical evidence, key comparisons, and concrete numbers when available. Do not just say the method is strong or effective; show what the evidence actually supports.', '',
            '### Relevance to the Current Grounded Topic', '',
            'Explain why the paper matters for the grounded topic, what can be borrowed, and what remains uncertain.', '',
            '### Limits / Caveats', '',
            'State at least one limitation, caveat, or transfer boundary when the opened source or PDF provides enough evidence.', '',
            'Do not satisfy coverage with placeholder language such as "the paper addresses...", "methods exist for...", or "the work improves..." unless concrete extracted details immediately follow.', '',
            '## Minimum Content Requirements for Final Write-up', '',
            'The final paper analysis should not be considered complete unless it includes, when available:', '',
            '- one concrete description of the task setting, benchmark, or dataset',
            '- one concrete description of the method pipeline or key module',
            '- one concrete training signal / loss / optimization detail',
            '- at least two concrete evidence points or quantitative findings when available',
            '- one explicit comparison against a baseline or prior work when available',
            '- one explicit limitation, caveat, or unproven point',
            '- one explicit statement of relevance to the current grounded topic', '',
            'Do not write the main body as a sequence of one-line answers. Use bullets only sparingly for compact metadata or a very small number of key metrics.',
            'If a detail is unavailable, explicitly say that the opened source did not provide enough information instead of fabricating content.',
            f'Evidence density hint for this paper: {evidence_density}. Low density is not permission to write a short note; it means you should rely carefully on the extracted sections and excerpts and keep the prose concrete rather than generic.', '',
        ])
        note_path.write_text('\n'.join(note_md), encoding='utf-8')
        record = {
            'paper_id': paper_id,
            'title': title,
            'url': url,
            'publish_date': item.get('publish_date'),
            'group': item.get('group') or item.get('query_group'),
            'query': item.get('query'),
            'reader_method': item.get('reader_method'),
            'is_research_literature': item.get('is_research_literature'),
            'opened_source_path': source_path,
            'note_markdown_path': str(note_path),
            'content_char_count': item.get('content_char_count', 0),
            'analysis_source': 'opened_page',
            'refined_from_pdf': False,
            'pdf_path': item.get('download_path'),
            'pdf_refinement_status': 'not_attempted',
            'sections': sections,
            'key_excerpts': excerpts,
            'method_excerpts': method_excerpts,
            'result_excerpts': result_excerpts,
            'evidence_density': evidence_density,
            'recommended_write_mode': 'deep_formal_paper_analysis',
        }
        records.append(record)

    with output_path.open('w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    return {
        'paper_note_count': len(records),
        'output_path': str(output_path),
        'notes_dir': str(notes_dir),
        'skipped_missing_source_count': len(skipped_missing),
        'skipped_not_opened_count': len(skipped_not_opened),
        'skipped_missing_sources': skipped_missing,
        'skipped_not_opened': skipped_not_opened,
    }


def run(search_results_path: Path, output_path: Optional[Path] = None, notes_dir: Optional[Path] = None) -> Dict[str, Any]:
    search_data = _read_json(search_results_path)
    if output_path is None:
        output_path = search_results_path.parent / 'opened_paper_notes.jsonl'
    return generate_notes_from_data(search_data, output_path=output_path, notes_dir=notes_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description='Build structured paper notes from search_results + opened_sources')
    parser.add_argument('--search-results', required=True)
    parser.add_argument('--output', default=None)
    parser.add_argument('--notes-dir', default=None)
    args = parser.parse_args()
    summary = run(
        Path(args.search_results),
        output_path=Path(args.output) if args.output else None,
        notes_dir=Path(args.notes_dir) if args.notes_dir else None,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
