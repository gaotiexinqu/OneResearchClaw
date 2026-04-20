#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pypdf import PdfReader

import prepare_opened_paper_notes as prep

_TERMINAL_STATUSES = {'completed', 'no_eligible_items'}
_MAX_PDF_TEXT_CHARS = 80000


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    if not path.exists():
        return records
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    return records


def _write_jsonl(path: Path, records: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')


def _infer_manifest_path(search_results: Path, explicit: Optional[Path]) -> Path:
    if explicit is not None:
        return explicit
    ground_id = search_results.parent.name
    return Path('data/lit_downloads') / ground_id / 'manifest.json'


def _wait_for_manifest(manifest_path: Path, *, poll_sec: float, timeout_sec: float) -> Dict[str, Any]:
    """Poll manifest_path until it reaches a terminal+valid state.

    A manifest is considered terminal-valid when:
      - status == 'completed'   (download ran successfully)
      - OR status == 'no_eligible_items' AND downloaded_count > 0
        (previous run re-used already-downloaded files without re-attempting)
    A manifest is considered NOT terminal-valid when:
      - status == 'no_eligible_items' AND downloaded_count == 0
        (download failed before producing any results — keep polling)
      - manifest does not exist yet
      - manifest exists but 'status' field is missing
    """
    start = time.time()
    manifest = None
    while True:
        if manifest_path.exists():
            try:
                manifest = _read_json(manifest_path)
            except Exception:
                manifest = None
            else:
                status = manifest.get('status')
                downloaded_count = manifest.get('downloaded_count', 0)
                if status == 'completed':
                    return manifest
                if status == 'no_eligible_items' and downloaded_count > 0:
                    return manifest
                # no_eligible_items with 0 downloads — keep polling
        if timeout_sec > 0 and time.time() - start > timeout_sec:
            raise TimeoutError(
                f'Manifest did not reach a terminal+valid state within '
                f'{timeout_sec}s (path={manifest_path}). '
                f'Current: status={manifest.get("status") if manifest else "missing"}, '
                f'downloaded_count={manifest.get("downloaded_count", 0) if manifest else 0}'
            )
        time.sleep(poll_sec)


def _extract_pdf_text(pdf_path: Path) -> str:
    try:
        reader = PdfReader(str(pdf_path))
    except Exception:
        return ''
    chunks: List[str] = []
    for page in reader.pages:
        try:
            txt = page.extract_text() or ''
        except Exception:
            txt = ''
        if txt:
            chunks.append(txt)
        if sum(len(c) for c in chunks) >= _MAX_PDF_TEXT_CHARS:
            break
    text = '\n\n'.join(chunks)
    return text[:_MAX_PDF_TEXT_CHARS]


def _iter_search_items(obj: Any):
    if isinstance(obj, dict):
        if 'queries' in obj and isinstance(obj['queries'], list):
            for block in obj['queries']:
                if isinstance(block, dict):
                    for item in block.get('items', []) or []:
                        if isinstance(item, dict):
                            yield item
        for key in ('items', 'results'):
            if isinstance(obj.get(key), list):
                for item in obj[key]:
                    if isinstance(item, dict):
                        yield item
        for v in obj.values():
            yield from _iter_search_items(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _iter_search_items(v)


def _match_record(records: List[Dict[str, Any]], title: str, url: str) -> Optional[Dict[str, Any]]:
    for rec in records:
        if rec.get('url') == url and url:
            return rec
    for rec in records:
        if rec.get('title') == title and title:
            return rec
    return None


def _merge_dict(primary: Optional[Dict[str, Any]], fallback: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = dict(fallback or {})
    for k, v in (primary or {}).items():
        if v:
            out[k] = v
    return out


def _merge_list(primary: Optional[List[Any]], fallback: Optional[List[Any]]) -> List[Any]:
    out: List[Any] = []
    seen = set()
    for item in (primary or []) + (fallback or []):
        if item in (None, ''):
            continue
        key = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, (dict, list)) else str(item)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _search_item_for(url: str, title: str, search_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for item in _iter_search_items(search_data):
        if url and item.get('url') == url:
            return item
    for item in _iter_search_items(search_data):
        if title and item.get('title') == title:
            return item
    return None


def _build_note_markdown(record: Dict[str, Any], note_path: Path) -> None:
    note_md: List[str] = [
        f"# {record.get('paper_id')}: {record.get('title')}",
        '',
        f"- URL: {record.get('url')}",
        f"- Query group: {record.get('group')}",
        f"- Query: {record.get('query')}",
        f"- Publish date: {record.get('publish_date')}",
        f"- Reader method: {record.get('reader_method')}",
        f"- Source path: {record.get('opened_source_path')}",
        f"- Analysis source: {record.get('analysis_source')}",
        f"- Refined from PDF: {record.get('refined_from_pdf')}",
        f"- PDF path: {record.get('pdf_path')}",
        f"- PDF refinement status: {record.get('pdf_refinement_status')}",
        '',
        '## Extracted Sections',
        '',
    ]
    for key_name, text in (record.get('sections') or {}).items():
        note_md.extend([f"### {key_name}", '', text, ''])
    if record.get('pdf_sections'):
        note_md.extend(['## PDF Refinement Sections', ''])
        for key_name, text in (record.get('pdf_sections') or {}).items():
            note_md.extend([f"### {key_name}", '', text, ''])
    note_md.extend(['## Key Evidence Excerpts', ''])
    for ex in record.get('key_excerpts') or []:
        note_md.extend([f"- {ex}", ''])
    if record.get('pdf_key_excerpts'):
        note_md.extend(['## PDF Evidence Excerpts', ''])
        for ex in record.get('pdf_key_excerpts') or []:
            note_md.extend([f"- {ex}", ''])
    note_md.extend(['## Method-Oriented Excerpts', ''])
    for ex in record.get('method_excerpts') or []:
        note_md.extend([f"- {ex}", ''])
    if record.get('pdf_method_excerpts'):
        note_md.extend(['## PDF Method-Oriented Excerpts', ''])
        for ex in record.get('pdf_method_excerpts') or []:
            note_md.extend([f"- {ex}", ''])
    note_md.extend(['## Result-Oriented Excerpts', ''])
    for ex in record.get('result_excerpts') or []:
        note_md.extend([f"- {ex}", ''])
    if record.get('pdf_result_excerpts'):
        note_md.extend(['## PDF Result-Oriented Excerpts', ''])
        for ex in record.get('pdf_result_excerpts') or []:
            note_md.extend([f"- {ex}", ''])
    note_md.extend([
        '## Narrative Writing Guide', '',
        'For the final literature report, prefer PDF-refined evidence when available. Strengthen already-recorded papers with method details, setup details, quantitative results, and explicit limitations extracted from the downloaded PDF.', '',
        'If a paper was not previously prominent in the initial literature report but now has a downloaded PDF and strong relevance, it may be added into the final `lit.md`.', '',
    ])
    note_path.write_text('\n'.join(note_md), encoding='utf-8')


def run(search_results: Path, notes_path: Path, *, notes_dir: Optional[Path] = None, manifest_path: Optional[Path] = None, wait: bool = False, poll_sec: float = 2.0, timeout_sec: float = 1800.0) -> Dict[str, Any]:
    search_data = _read_json(search_results)
    manifest_path = _infer_manifest_path(search_results, manifest_path)
    manifest = _wait_for_manifest(manifest_path, poll_sec=poll_sec, timeout_sec=timeout_sec) if wait else (_read_json(manifest_path) if manifest_path.exists() else {'status': 'missing'})

    records = _read_jsonl(notes_path)
    rec_by_key = {(r.get('title'), r.get('url')): r for r in records}
    if notes_dir is None:
        notes_dir = notes_path.parent / 'opened_paper_notes'
    notes_dir.mkdir(parents=True, exist_ok=True)

    refined_count = 0
    added_count = 0
    skipped_count = 0
    downloaded_count = 0
    parsable_pdf_count = 0
    failed_pdf_items: List[Dict[str, Any]] = []
    coverage_items: List[Dict[str, Any]] = []

    for item in manifest.get('items', []) or []:
        if not item.get('downloaded'):
            skipped_count += 1
            continue
        downloaded_count += 1
        pdf_path = Path(item.get('download_path')) if item.get('download_path') else None
        if not pdf_path or not pdf_path.exists():
            failed_pdf_items.append({
                'title': item.get('title') or 'Untitled',
                'url': item.get('url') or '',
                'reason': 'missing_pdf_path',
            })
            skipped_count += 1
            continue
        title = item.get('title') or 'Untitled'
        url = item.get('url') or ''
        rec = _match_record(records, title, url)
        was_existing = rec is not None
        if rec is None:
            search_item = _search_item_for(url, title, search_data) or {}
            paper_id = f"P{len(records)+1:03d}"
            slug = prep._safe_slug(title, paper_id)
            note_path = notes_dir / f"{paper_id}_{slug}.md"
            rec = {
                'paper_id': paper_id,
                'title': title,
                'url': url,
                'publish_date': search_item.get('publish_date'),
                'group': search_item.get('group') or search_item.get('query_group'),
                'query': search_item.get('query'),
                'reader_method': search_item.get('reader_method'),
                'is_research_literature': True,
                'opened_source_path': search_item.get('opened_source_path'),
                'note_markdown_path': str(note_path),
                'content_char_count': search_item.get('content_char_count', 0),
                'analysis_source': 'opened_page',
                'refined_from_pdf': False,
                'pdf_path': str(pdf_path),
                'pdf_refinement_status': 'pending',
                'sections': {},
                'key_excerpts': [],
                'method_excerpts': [],
                'result_excerpts': [],
            }
            records.append(rec)
            added_count += 1
        text = _extract_pdf_text(pdf_path)
        if not text.strip():
            rec['pdf_refinement_status'] = 'failed_empty_pdf_text'
            failed_pdf_items.append({
                'title': title,
                'url': url,
                'reason': 'failed_empty_pdf_text',
            })
            skipped_count += 1
            continue
        parsable_pdf_count += 1
        rec['pdf_path'] = str(pdf_path)
        rec['pdf_text_char_count'] = len(text)
        rec['pdf_sections'] = prep._extract_sections(text)
        rec['pdf_key_excerpts'] = prep._extract_excerpts(text)
        rec['pdf_method_excerpts'] = prep._extract_method_excerpts(text)
        rec['pdf_result_excerpts'] = prep._extract_result_excerpts(text)
        rec['analysis_source_before'] = rec.get('analysis_source')
        rec['analysis_source'] = 'downloaded_pdf_refined'
        rec['refined_from_pdf'] = True
        rec['pdf_refinement_status'] = 'completed'
        rec['pdf_refined_at'] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        rec['refinement_kind'] = 'strengthen' if was_existing else 'add'
        rec['sections'] = _merge_dict(rec.get('pdf_sections'), rec.get('sections'))
        rec['key_excerpts'] = _merge_list(rec.get('pdf_key_excerpts'), rec.get('key_excerpts'))
        rec['method_excerpts'] = _merge_list(rec.get('pdf_method_excerpts'), rec.get('method_excerpts'))
        rec['result_excerpts'] = _merge_list(rec.get('pdf_result_excerpts'), rec.get('result_excerpts'))
        note_path = Path(rec['note_markdown_path'])
        _build_note_markdown(rec, note_path)
        coverage_items.append({
            'title': title,
            'url': url,
            'paper_id': rec.get('paper_id'),
            'note_markdown_path': rec.get('note_markdown_path'),
            'refinement_kind': rec.get('refinement_kind'),
            'must_appear_in_final_lit': True,
        })
        refined_count += 1

    _write_jsonl(notes_path, records)
    coverage_output = notes_path.parent / 'refine_coverage.json'
    coverage_payload = {
        'manifest_path': str(manifest_path),
        'downloaded_manifest_count': downloaded_count,
        'parsable_pdf_count': parsable_pdf_count,
        'failed_pdf_items': failed_pdf_items,
        'papers_requiring_explicit_final_lit_coverage': coverage_items,
    }
    coverage_output.write_text(json.dumps(coverage_payload, ensure_ascii=False, indent=2), encoding='utf-8')
    summary = {
        'search_results': str(search_results),
        'notes_path': str(notes_path),
        'notes_dir': str(notes_dir),
        'manifest_path': str(manifest_path),
        'manifest_status': manifest.get('status'),
        'refined_count': refined_count,
        'added_count': added_count,
        'skipped_count': skipped_count,
        'total_note_count': len(records),
        'downloaded_manifest_count': downloaded_count,
        'parsable_pdf_count': parsable_pdf_count,
        'failed_pdf_count': len(failed_pdf_items),
        'coverage_output': str(coverage_output),
        'papers_requiring_explicit_final_lit_coverage': coverage_items,
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description='Refine opened paper notes using downloaded PDFs')
    parser.add_argument('--search-results', required=True)
    parser.add_argument('--notes-path', required=True)
    parser.add_argument('--notes-dir', default=None)
    parser.add_argument('--manifest-path', default=None)
    parser.add_argument('--wait', type=lambda x: x.lower() in {'true', '1', 'yes'}, default=False)
    parser.add_argument('--poll-sec', type=float, default=2.0)
    parser.add_argument('--timeout-sec', type=float, default=1800.0)
    args = parser.parse_args()
    summary = run(
        Path(args.search_results),
        Path(args.notes_path),
        notes_dir=Path(args.notes_dir) if args.notes_dir else None,
        manifest_path=Path(args.manifest_path) if args.manifest_path else None,
        wait=args.wait,
        poll_sec=args.poll_sec,
        timeout_sec=args.timeout_sec,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
