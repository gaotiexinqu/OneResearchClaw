#!/usr/bin/env python3
"""
External API backend adapter for grounded-research-lit.

What this version closes:
- keeps the original query -> search -> open flow intact
- preserves readable source material under opened_sources/
- automatically builds structured paper notes from opened content
- supports sidecar/concurrent download so download does not block analysis
- writes a download manifest when download is enabled
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import requests

import prepare_opened_paper_notes as notes_prep
import download_opened_literature as downloader

SEARCH_URL = 'https://search-svip.bigmodel.cn/api/paas/v4/search'
READER_URL = 'https://search-svip.bigmodel.cn/api/paas/v4/reader'
_USER_AGENT = 'Mozilla/5.0 (compatible; grounded-research-lit/3.0)'
_TIMEOUT = 45
_MAX_OPENED_CONTENT_CHARS = 40_000
_DEFAULT_MAX_OPEN_ATTEMPTS = 8
_DEFAULT_DOWNLOAD_WORKERS = 4

_STRONG_ACADEMIC_DOMAINS = (
    'arxiv.org', 'openreview.net', 'aclanthology.org', 'proceedings.mlr.press',
    'proceedings.neurips.cc', 'papers.nips.cc', 'neurips.cc',
    'openaccess.thecvf.com', 'thecvf.com', 'cvf.com', 'ieeexplore.ieee.org',
    'dl.acm.org', 'link.springer.com', 'springer.com', 'sciencedirect.com',
    'nature.com', 'science.org', 'jmlr.org', 'aaai.org', 'ijcai.org', 'usenix.org', 'doi.org',
)
_WEAK_ACADEMIC_SUFFIXES = ('.edu', '.edu.cn', '.ac.uk', '.ac.cn', '.ac.jp')
_RESEARCH_KEYWORDS = (
    'paper', 'abstract', 'dataset', 'benchmark', 'method', 'experiment', 'results',
    'appendix', 'conference', 'journal', 'workshop', 'proceedings', 'doi', 'arxiv',
    'openreview', 'preprint', 'accepted',
)
_NEGATIVE_KEYWORDS = ('tutorial', 'course', 'blog', 'news', 'docs', 'documentation', 'marketing', 'product')
_GENERIC_NONPAPER_PATTERNS = [
    re.compile(r'^https?://(?:www\.)?github\.com/', re.I),
    re.compile(r'^https?://(?:www\.)?(?:medium|substack|dev\.to|stackoverflow|reddit)', re.I),
    re.compile(r'^https?://(?:www\.)?(?:twitter|x\.com|facebook|linkedin)', re.I),
]


@dataclass
class ReadResult:
    success: bool
    method: str
    content: str
    error: Optional[str] = None


def _bool_env(name: str, default: bool = False) -> bool:
    val = os.getenv(name, '').strip().lower()
    if val in {'true', '1', 'yes'}:
        return True
    if val in {'false', '0', 'no'}:
        return False
    return default


def _int_env(name: str, default: int) -> int:
    val = os.getenv(name, '').strip()
    try:
        return int(val)
    except Exception:
        return default


def _auth_key() -> str:
    key = os.getenv('BIGMODEL_SEARCH_API_KEY', '').strip()
    if not key:
        raise ValueError('BIGMODEL_SEARCH_API_KEY is not set')
    return key


def _load_constants() -> Dict[str, Any]:
    return {
        'SEARCH_BACKEND': os.getenv('SEARCH_BACKEND', 'auto'),
        'REQUIRE_OPEN_LINK': _bool_env('REQUIRE_OPEN_LINK', True),
        'DOWNLOAD_OPENED_LITERATURE': _bool_env('DOWNLOAD_OPENED_LITERATURE', True),
        'DOWNLOAD_DIR': os.getenv('DOWNLOAD_DIR', 'data/lit_downloads'),
        'OPEN_TOP_K': _int_env('OPEN_TOP_K', 2),
    }


def _write_json(data: Dict[str, Any], output: Optional[str]) -> None:
    if output:
        p = Path(output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))


def _http_get(url: str, timeout: int = _TIMEOUT) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': _USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _fetch_html(url: str, timeout: int = _TIMEOUT) -> Optional[str]:
    try:
        raw = _http_get(url, timeout=timeout)
    except Exception:
        return None
    text = raw.decode('utf-8', errors='ignore')
    if '<html' in text[:1000].lower() or '</html>' in text.lower():
        return text
    return None


def _strip_html(html: str) -> str:
    text = re.sub(r'<script[\s\S]*?</script>', ' ', html, flags=re.I)
    text = re.sub(r'<style[\s\S]*?</style>', ' ', text, flags=re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _search_api(query: str, api_key: str, *, count: int) -> Dict[str, Any]:
    headers = {
        'Authorization': api_key,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    payload = {
        'q': query,
        'search_engine': 'search_std',
        'query_rewrite': False,
        'count': count,
        'location': 'cn',
        'page': 1,
        'search_recency_filter': 'noLimit',
        'content_size': 'medium',
    }
    resp = requests.post(SEARCH_URL, headers=headers, json=payload, timeout=_TIMEOUT)
    if not resp.ok:
        body = resp.text.strip()
        raise RuntimeError(f'Search API {resp.status_code} for query={query!r}: {body or '<empty body>'}')
    return resp.json()


def _reader_api(url: str, api_key: str) -> Dict[str, Any]:
    headers = {
        'Authorization': api_key,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Return-Format': 'markdown',
        'X-Timeout': '10',
        'X-No-Cache': 'true',
    }
    resp = requests.post(READER_URL, headers=headers, json={'url': url}, timeout=_TIMEOUT)
    if not resp.ok:
        body = resp.text.strip()
        raise RuntimeError(f'Reader API {resp.status_code} for url={url!r}: {body or '<empty body>'}')
    return resp.json()


def _extract_search_items(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = result.get('search_result')
    if items is None:
        items = result.get('data')
    if items is None and isinstance(result.get('result'), dict):
        nested = result['result']
        items = nested.get('search_result') or nested.get('data')
    return items or []


def _normalize_item(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'title': raw.get('title') or '',
        'url': raw.get('link') or raw.get('url') or '',
        'snippet': raw.get('content') or raw.get('description') or '',
        'publish_date': raw.get('publish_date') or raw.get('date'),
        'media': raw.get('media'),
        'raw': raw,
    }


def _coerce_query_text(query: Any) -> str:
    if isinstance(query, str):
        return query.strip()
    if isinstance(query, dict):
        value = query.get('query')
        if value is None:
            return ''
        return str(value).strip()
    if query is None:
        return ''
    return str(query).strip()


def _query_label(query: Any) -> Any:
    if isinstance(query, dict):
        return query
    return _coerce_query_text(query)


def _keyword_score(*texts: Optional[str]) -> int:
    text = ' '.join([t or '' for t in texts]).lower()
    pos = sum(1 for kw in _RESEARCH_KEYWORDS if kw in text)
    neg = sum(1 for kw in _NEGATIVE_KEYWORDS if kw in text)
    return pos - neg


def _host(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.lower()


def _is_research_literature(url: str, title: str = '', snippet: str = '', page_summary: str = '') -> bool:
    if not url:
        return False
    lower = url.lower()
    host = _host(url)
    if lower.endswith('.pdf') or '/pdf/' in lower:
        return True
    if any(domain in lower for domain in _STRONG_ACADEMIC_DOMAINS):
        return True
    if any(host.endswith(sfx) for sfx in _WEAK_ACADEMIC_SUFFIXES) and _keyword_score(title, snippet, page_summary) >= 1:
        return True
    if any(p.search(lower) for p in _GENERIC_NONPAPER_PATTERNS):
        return _keyword_score(title, snippet, page_summary) >= 4
    return _keyword_score(title, snippet, page_summary) >= 3


def _research_score(url: str, title: str, snippet: str) -> int:
    score = _keyword_score(title, snippet)
    lower = (url or '').lower()
    if lower.endswith('.pdf') or '/pdf/' in lower:
        score += 8
    if any(domain in lower for domain in _STRONG_ACADEMIC_DOMAINS):
        score += 6
    if 'arxiv.org' in lower:
        score += 4
    if 'openreview.net' in lower or 'aclanthology.org' in lower:
        score += 4
    if any(p.search(lower) for p in _GENERIC_NONPAPER_PATTERNS):
        score -= 4
    return score


def _safe_slug(text: str, fallback: str) -> str:
    base = re.sub(r'[^A-Za-z0-9._-]+', '_', (text or '').strip())
    base = re.sub(r'_+', '_', base).strip('_')
    return (base[:120] or fallback)


def _extract_reader_content(reader_json: Dict[str, Any]) -> str:
    data = reader_json.get('content')
    if isinstance(data, str) and data.strip():
        return data
    nested = reader_json.get('data')
    if isinstance(nested, dict):
        for key in ('content', 'markdown', 'text'):
            val = nested.get(key)
            if isinstance(val, str) and val.strip():
                return val
    return ''


def _read_one_url(url: str, api_key: str) -> ReadResult:
    try:
        reader = _reader_api(url, api_key)
        content = _extract_reader_content(reader)
        if content.strip():
            return ReadResult(True, 'reader_api', content[:_MAX_OPENED_CONTENT_CHARS])
    except Exception as exc:
        reader_err = str(exc)
    else:
        reader_err = None

    html = _fetch_html(url)
    if html:
        stripped = _strip_html(html)
        if stripped:
            return ReadResult(True, 'html_fallback', stripped[:_MAX_OPENED_CONTENT_CHARS], error=reader_err)

    return ReadResult(False, 'none', '', error=reader_err or 'Unable to read page')


def _infer_task_id(query_file: str) -> str:
    p = Path(query_file)
    try:
        payload = json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        payload = {}
    return payload.get('ground_id') or payload.get('task_id') or payload.get('meeting_id') or p.parent.name


def _opened_sources_dir(query_file: str, explicit: Optional[str]) -> Path:
    if explicit:
        return Path(explicit)
    return Path(query_file).parent / 'opened_sources'


def _notes_output_paths(query_file: str, explicit_jsonl: Optional[str], explicit_dir: Optional[str]) -> Tuple[Path, Path]:
    base = Path(query_file).parent
    return (
        Path(explicit_jsonl) if explicit_jsonl else base / 'opened_paper_notes.jsonl',
        Path(explicit_dir) if explicit_dir else base / 'opened_paper_notes',
    )


def _save_opened_source(opened_dir: Path, task_id: str, group: str, query: str, rank: int, title: str, url: str, content: str) -> str:
    opened_dir.mkdir(parents=True, exist_ok=True)
    slug = _safe_slug(title or Path(urllib.parse.urlparse(url).path).stem, f'item_{rank:03d}')
    path = opened_dir / f'{rank:03d}_{slug}.md'
    body = (
        f'# {title or "Untitled"}\n\n'
        f'- task_id: {task_id}\n'
        f'- group: {group}\n'
        f'- query: {query}\n'
        f'- url: {url}\n\n'
        f'## Readable Content\n\n{content}\n'
    )
    path.write_text(body, encoding='utf-8')
    return str(path)


def _candidate_indices(items: Sequence[Dict[str, Any]], open_top_k: int, max_open_attempts: int) -> List[int]:
    if not items:
        return []
    first = list(range(min(open_top_k, len(items))))
    rest = list(range(len(items)))[len(first):]
    rest.sort(key=lambda i: _research_score(items[i].get('url', ''), items[i].get('title', ''), items[i].get('snippet', '')), reverse=True)
    ordered = first + [i for i in rest if i not in first]
    return ordered[:max_open_attempts]


def _process_one_query(
    query_text: str,
    query_meta: Any,
    group_name: str,
    api_key: str,
    *,
    count: int,
    open_top_k: int,
    max_open_attempts: int,
    require_open_link: bool,
    opened_dir: Path,
    task_id: str,
    download_opened: bool,
    download_dir: Path,
    download_mode: str,
    download_executor: Optional[ThreadPoolExecutor],
    download_futures: List[Tuple[Future, Dict[str, Any]]],
) -> Dict[str, Any]:
    search_result = _search_api(query_text, api_key, count=count)
    raw_items = _extract_search_items(search_result)
    normalized = [_normalize_item(x) for x in raw_items]
    open_indices = set(_candidate_indices(normalized, open_top_k, max_open_attempts)) if require_open_link else set()
    items: List[Dict[str, Any]] = []
    opened_research_count = 0

    for idx, item in enumerate(normalized, start=1):
        url = item.get('url') or ''
        title = item.get('title') or ''
        snippet = item.get('snippet') or ''
        entry: Dict[str, Any] = {
            'rank': idx,
            'group': group_name,
            'query': _query_label(query_meta),
            'title': title,
            'url': url,
            'snippet': snippet,
            'publish_date': item.get('publish_date'),
            'media': item.get('media'),
            'opened': False,
            'open_status': 'skipped',
            'page_summary': None,
            'content_excerpt': None,
            'content_char_count': 0,
            'opened_source_path': None,
            'reader_method': None,
            'is_research_literature': _is_research_literature(url, title, snippet, ''),
            'downloadable': True,
            'download_attempted': False,
            'downloaded': False,
            'download_path': None,
            'download_error': None,
            'download_mode': download_mode if download_opened else 'off',
            'backend': 'external_api',
        }

        if not url:
            entry['open_status'] = 'failed'
            entry['page_summary'] = 'Missing URL'
            items.append(entry)
            continue

        if (idx - 1) in open_indices:
            rr = _read_one_url(url, api_key)
            if rr.success:
                entry['opened'] = True
                entry['open_status'] = 'success'
                entry['reader_method'] = rr.method
                clean = rr.content.strip()
                entry['page_summary'] = clean[:4000]
                entry['content_excerpt'] = clean[:8000]
                entry['content_char_count'] = len(clean)
                entry['is_research_literature'] = _is_research_literature(url, title, snippet, clean[:4000])
                entry['opened_source_path'] = _save_opened_source(opened_dir, task_id, group_name, query_text, idx, title, url, clean)
                if entry['is_research_literature']:
                    opened_research_count += 1
                    if download_opened:
                        if download_mode == 'sidecar' and download_executor is not None:
                            entry['download_attempted'] = True
                            fut = download_executor.submit(downloader.download_item, entry, download_dir / task_id, len(download_futures) + 1)
                            download_futures.append((fut, entry))
                        elif download_mode == 'inline':
                            entry['download_attempted'] = True
                            dl = downloader.download_item(entry, download_dir / task_id, len(items) + 1)
                            if dl.get('download_path'):
                                entry['download_path'] = dl['download_path']
                            entry['downloaded'] = dl.get('downloaded', False)
                            entry['download_error'] = dl.get('download_error')
            else:
                entry['open_status'] = 'failed'
                entry['page_summary'] = rr.error or 'Reader failed'
                entry['reader_method'] = rr.method
        items.append(entry)

    return {
        'group': group_name,
        'query': _query_label(query_meta),
        'opened_count': sum(1 for x in items if x.get('opened')),
        'opened_research_count': opened_research_count,
        'items': items,
    }



def _count_download_eligible(query_blocks: Sequence[Dict[str, Any]]) -> int:
    count = 0
    for block in query_blocks:
        for item in block.get('items', []) or []:
            if item.get('opened') and item.get('open_status') in (None, 'success') and item.get('is_research_literature'):
                count += 1
    return count


def _write_queued_manifest(manifest_dir: Path, task_id: str, eligible_item_count: int) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / 'manifest.json'
    manifest = {
        'task_id': task_id,
        'status': ('no_eligible_items' if eligible_item_count == 0 else 'queued'),
        'download_attempted': True,
        'background': True,
        'eligible_item_count': eligible_item_count,
        'downloaded_count': 0,
        'items': [],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return manifest_path


def _launch_background_download(search_results_path: Path, download_dir: Path, task_id: str, *, max_workers: int) -> Dict[str, Any]:
    script_path = Path(__file__).with_name('download_opened_literature.py')
    manifest_path = download_dir / task_id / 'manifest.json'
    eligible_count = 0
    try:
        search_data = json.loads(search_results_path.read_text(encoding='utf-8'))
        eligible_count = _count_download_eligible(search_data.get('queries', []) or [])
    except Exception:
        eligible_count = 0
    queued_path = _write_queued_manifest(download_dir / task_id, task_id, eligible_count)
    log_path = download_dir / task_id / 'background_download.log'
    cmd = [
        sys.executable, str(script_path),
        '--search-results', str(search_results_path),
        '--output-dir', str(download_dir / task_id),
        '--ground-id', task_id,
        '--only-opened', 'true',
        '--max-workers', str(max_workers),
        '--manifest-path', str(manifest_path),
    ]
    with log_path.open('ab') as log_f:
        proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT, start_new_session=True)
    return {
        'manifest_path': str(queued_path),
        'background_log_path': str(log_path),
        'background_pid': proc.pid,
        'eligible_item_count': eligible_count,
    }

def _gather_downloads(download_futures: List[Tuple[Future, Dict[str, Any]]], manifest_dir: Path, task_id: str) -> Dict[str, Any]:
    manifest_items: List[Dict[str, Any]] = []
    for idx, (future, entry) in enumerate(download_futures, start=1):
        try:
            dl = future.result()
        except Exception as exc:
            dl = {
                'title': entry.get('title'),
                'url': entry.get('url'),
                'resolved_url': None,
                'download_attempted': True,
                'downloaded': False,
                'download_path': None,
                'download_error': str(exc),
            }
        if dl.get('download_path'):
            entry['download_path'] = dl['download_path']
        entry['downloaded'] = dl.get('downloaded', False)
        entry['download_error'] = dl.get('download_error')
        manifest_items.append(dl)
    manifest = {
        'task_id': task_id,
        'download_attempted': True,
        'eligible_item_count': len(download_futures),
        'downloaded_count': sum(1 for x in manifest_items if x.get('downloaded')),
        'items': manifest_items,
    }
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'manifest': manifest, 'manifest_path': str(manifest_path)}


def batch_search_read(
    query_file: str,
    api_key: str,
    *,
    count: int = 6,
    open_top_k: int = 2,
    max_open_attempts: int = _DEFAULT_MAX_OPEN_ATTEMPTS,
    require_open_link: bool = True,
    download_opened: bool = False,
    download_mode: str = 'background',
    download_dir: str = 'data/lit_downloads',
    opened_content_dir: Optional[str] = None,
    paper_notes_output: Optional[str] = None,
    paper_notes_dir: Optional[str] = None,
    max_download_workers: int = _DEFAULT_DOWNLOAD_WORKERS,
    sleep_sec: float = 0.0,
) -> Dict[str, Any]:
    payload = json.loads(Path(query_file).read_text(encoding='utf-8'))
    task_id = _infer_task_id(query_file)
    opened_dir = _opened_sources_dir(query_file, opened_content_dir)
    notes_output, notes_dir = _notes_output_paths(query_file, paper_notes_output, paper_notes_dir)
    problem_queries = payload.get('problem_queries') or []
    method_queries = payload.get('method_queries') or []
    constraint_queries = payload.get('constraint_queries') or []
    groups = [
        ('problem_queries', problem_queries),
        ('method_queries', method_queries),
        ('constraint_queries', constraint_queries),
    ]

    query_blocks: List[Dict[str, Any]] = []
    total_opened = 0
    total_opened_research = 0
    errors: List[str] = []
    download_futures: List[Tuple[Future, Dict[str, Any]]] = []
    download_executor: Optional[ThreadPoolExecutor] = None
    if download_opened and download_mode == 'sidecar':
        download_executor = ThreadPoolExecutor(max_workers=max(1, max_download_workers))

    try:
        for group_name, queries in groups:
            for query in queries:
                query_text = _coerce_query_text(query)
                query_label = _query_label(query)
                if not query_text:
                    errors.append(f'{group_name} / {query_label}: empty query text')
                    query_blocks.append({
                        'group': group_name,
                        'query': query_label,
                        'opened_count': 0,
                        'opened_research_count': 0,
                        'items': [{
                            'rank': 1,
                            'group': group_name,
                            'query': query_label,
                            'title': None,
                            'url': None,
                            'snippet': None,
                            'opened': False,
                            'open_status': 'failed',
                            'page_summary': 'Search error: empty query text',
                            'content_excerpt': None,
                            'content_char_count': 0,
                            'opened_source_path': None,
                            'reader_method': None,
                            'is_research_literature': False,
                            'downloadable': False,
                            'download_attempted': False,
                            'downloaded': False,
                            'download_path': None,
                            'download_error': None,
                            'download_mode': download_mode if download_opened else 'off',
                            'backend': 'external_api',
                        }],
                    })
                    if sleep_sec > 0:
                        time.sleep(sleep_sec)
                    continue
                try:
                    block = _process_one_query(
                        query_text,
                        query,
                        group_name,
                        api_key,
                        count=count,
                        open_top_k=open_top_k,
                        max_open_attempts=max_open_attempts,
                        require_open_link=require_open_link,
                        opened_dir=opened_dir,
                        task_id=task_id,
                        download_opened=download_opened,
                        download_dir=Path(download_dir),
                        download_mode=download_mode,
                        download_executor=download_executor,
                        download_futures=download_futures,
                    )
                    query_blocks.append(block)
                    total_opened += block['opened_count']
                    total_opened_research += block['opened_research_count']
                except Exception as exc:
                    errors.append(f'{group_name} / {query_label}: {exc}')
                    query_blocks.append({
                        'group': group_name,
                        'query': query_label,
                        'opened_count': 0,
                        'opened_research_count': 0,
                        'items': [{
                            'rank': 1,
                            'group': group_name,
                            'query': query_label,
                            'title': None,
                            'url': None,
                            'snippet': None,
                            'opened': False,
                            'open_status': 'failed',
                            'page_summary': f'Search error: {exc}',
                            'content_excerpt': None,
                            'content_char_count': 0,
                            'opened_source_path': None,
                            'reader_method': None,
                            'is_research_literature': False,
                            'downloadable': False,
                            'download_attempted': False,
                            'downloaded': False,
                            'download_path': None,
                            'download_error': None,
                            'download_mode': download_mode if download_opened else 'off',
                            'backend': 'external_api',
                        }],
                    })
                if sleep_sec > 0:
                    time.sleep(sleep_sec)
    finally:
        if download_executor is not None:
            download_executor.shutdown(wait=False)

    output: Dict[str, Any] = {
        'task_id': task_id,
        'backend': 'external_api',
        'constants': {
            'SEARCH_BACKEND': os.getenv('SEARCH_BACKEND', 'auto'),
            'REQUIRE_OPEN_LINK': require_open_link,
            'DOWNLOAD_OPENED_LITERATURE': download_opened,
            'DOWNLOAD_DIR': download_dir,
            'OPEN_TOP_K': open_top_k,
            'DOWNLOAD_MODE': download_mode if download_opened else 'off',
        },
        'opened_sources_dir': str(opened_dir),
        'opened_paper_notes_file': str(notes_output),
        'opened_paper_notes_dir': str(notes_dir),
        'stats': {
            'query_count': sum(len(qs) for _, qs in groups),
            'opened_count': total_opened,
            'opened_research_count': total_opened_research,
        },
        'queries': query_blocks,
    }
    if errors:
        output['errors'] = errors

    # Generate paper notes before waiting for download sidecar to finish.
    notes_summary = notes_prep.generate_notes_from_data(output, output_path=notes_output, notes_dir=notes_dir)
    output['paper_notes_summary'] = notes_summary

    if download_opened and download_mode == 'sidecar':
        dl_summary = _gather_downloads(download_futures, Path(download_dir) / task_id, task_id)
        output['download_manifest'] = dl_summary['manifest']
        output['download_manifest_path'] = dl_summary['manifest_path']

    return output


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='External API search + reader adapter for grounded-research-lit.')
    subparsers = parser.add_subparsers(dest='command', required=True)
    p = subparsers.add_parser('batch-search-read', help='Run queries from JSON, open links, generate notes, optionally download')
    p.add_argument('--query-file', required=True)
    p.add_argument('--count', type=int, default=6)
    p.add_argument('--open-top-k', type=int, default=None, dest='open_top_k')
    p.add_argument('--max-open-attempts', type=int, default=_DEFAULT_MAX_OPEN_ATTEMPTS)
    p.add_argument('--require-open-link', type=lambda x: x.lower() in ('true', '1', 'yes'), default=None, dest='require_open_link')
    p.add_argument('--download-opened-literature', type=lambda x: x.lower() in ('true', '1', 'yes'), default=None, dest='download_opened_literature')
    p.add_argument('--download-mode', choices=('off', 'background', 'sidecar', 'inline'), default=None)
    p.add_argument('--download-dir', default=None)
    p.add_argument('--opened-content-dir', default=None)
    p.add_argument('--paper-notes-output', default=None)
    p.add_argument('--paper-notes-dir', default=None)
    p.add_argument('--max-download-workers', type=int, default=_DEFAULT_DOWNLOAD_WORKERS)
    p.add_argument('--sleep-sec', type=float, default=0.0)
    p.add_argument('--output', default=None)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    constants = _load_constants()
    require_open_link = constants['REQUIRE_OPEN_LINK'] if args.require_open_link is None else args.require_open_link
    open_top_k = constants['OPEN_TOP_K'] if args.open_top_k is None else args.open_top_k
    download_opened = constants['DOWNLOAD_OPENED_LITERATURE'] if args.download_opened_literature is None else args.download_opened_literature
    download_dir = constants['DOWNLOAD_DIR'] if args.download_dir is None else args.download_dir
    download_mode = 'off' if not download_opened else (args.download_mode or 'background')

    if args.command == 'batch-search-read':
        data = batch_search_read(
            query_file=args.query_file,
            api_key=_auth_key(),
            count=args.count,
            open_top_k=open_top_k,
            max_open_attempts=args.max_open_attempts,
            require_open_link=require_open_link,
            download_opened=download_opened,
            download_mode=download_mode,
            download_dir=download_dir,
            opened_content_dir=args.opened_content_dir,
            paper_notes_output=args.paper_notes_output,
            paper_notes_dir=args.paper_notes_dir,
            max_download_workers=args.max_download_workers,
            sleep_sec=args.sleep_sec,
        )
        _write_json(data, args.output)
        if download_opened and download_mode == 'background' and args.output:
            bg = _launch_background_download(Path(args.output), Path(download_dir), data.get('task_id') or _infer_task_id(args.query_file), max_workers=args.max_download_workers)
            data['download_manifest_path'] = bg['manifest_path']
            data['background_download_log'] = bg['background_log_path']
            data['background_download_pid'] = bg['background_pid']
            data['download_manifest'] = {
                'task_id': data.get('task_id') or _infer_task_id(args.query_file),
                'status': ('no_eligible_items' if bg['eligible_item_count'] == 0 else 'queued'),
                'download_attempted': True,
                'background': True,
                'eligible_item_count': bg['eligible_item_count'],
                'downloaded_count': 0,
                'items': [],
            }
            _write_json(data, args.output)
        return 0
    raise RuntimeError(f'Unknown command: {args.command}')


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        raise
