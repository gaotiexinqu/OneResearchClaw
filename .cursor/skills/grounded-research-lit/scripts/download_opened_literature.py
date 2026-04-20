#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

_USER_AGENT = 'Mozilla/5.0 (compatible; grounded-research-lit-downloader/2.0)'
_TIMEOUT = 100
_MIN_PDF_BYTES = 10_240
_DEFAULT_MAX_WORKERS = 4
_TERMINAL_STATUSES = {'completed', 'no_eligible_items'}
_WAIT_POLL_SEC = 2.0
_WAIT_TIMEOUT_SEC = 1800.0


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def _safe_slug(text: str, fallback: str) -> str:
    base = re.sub(r'[^A-Za-z0-9._-]+', '_', (text or '').strip())
    base = re.sub(r'_+', '_', base).strip('_')
    return (base[:120] or fallback)


def _wait_for_manifest(manifest_path: Path, *, poll_sec: float = _WAIT_POLL_SEC, timeout_sec: float = _WAIT_TIMEOUT_SEC) -> Dict[str, Any]:
    """Poll manifest_path until it reaches a terminal + valid state.

    A manifest is considered terminal-valid when:
      - status == 'completed'   (download ran successfully and wrote results)
      - OR status == 'no_eligible_items' AND downloaded_count > 0
        (this can happen when previous run had items that were re-used)
    A manifest is considered NOT terminal-valid when:
      - status == 'no_eligible_items' AND downloaded_count == 0
        (download was called but _iter_items returned 0 items — likely a bug;
         this is not a terminal state, keep polling)
      - manifest does not exist yet
      - manifest exists but 'status' field is missing (still being written)
    """
    start = time.time()
    manifest: Optional[Dict[str, Any]] = None
    while True:
        if manifest_path.exists():
            try:
                manifest = _read_json(manifest_path)
            except Exception:
                manifest = None
            else:
                status = manifest.get('status')
                downloaded_count = manifest.get('downloaded_count', 0)
                # Terminal-valid: completed OR no_eligible_items with real downloads
                if status == 'completed':
                    return manifest
                if status == 'no_eligible_items' and downloaded_count > 0:
                    return manifest
                # NOT terminal-valid: no_eligible_items with zero downloads
                # means _iter_items failed — keep polling so a re-run can succeed
                # (keep manifest as-is for the timeout error message below)
        if timeout_sec > 0 and time.time() - start > timeout_sec:
            current_status = manifest.get('status') if manifest else 'missing'
            current_count = manifest.get('downloaded_count', 0) if manifest else 0
            raise TimeoutError(
                f'Manifest did not reach a terminal+valid state within '
                f'{timeout_sec}s (path={manifest_path}). '
                f'Current: status={current_status}, downloaded_count={current_count}'
            )
        time.sleep(poll_sec)


def _is_bare_paper_item(obj: Dict[str, Any]) -> bool:
    return 'url' in obj and 'title' in obj


def _iter_items(obj: Any, _seen_lists: Optional[List[List[Any]]] = None, _seen_dicts: Optional[List[Dict[str, Any]]] = None) -> Iterable[Dict[str, Any]]:
    """Yield each paper-item dict exactly once, regardless of nesting structure.

    Supported layouts:
      - Flat list:        [{title, url}, {title, url}]
      - Wrapped dict:     {items: [{title, url}], results: [...]}
      - Queries nested:   {queries: [{items: [{title, url}]}]}
      - Mixed:            {queries: [...], items: [...], results: [...]}

    Tracks seen lists AND seen dicts to avoid double-yielding.
    """
    if _seen_lists is None:
        _seen_lists = []
    if _seen_dicts is None:
        _seen_dicts = []

    if isinstance(obj, dict):
        if id(obj) in _seen_dicts:
            return
        # Yield bare paper items (but NOT if already yielded from 'items'/'results' above)
        if _is_bare_paper_item(obj) and obj not in _seen_dicts:
            _seen_dicts.append(obj)
            yield obj
        # Yield from 'items'/'results' arrays (these are "primary yield" paths)
        for key in ('items', 'results'):
            arr = obj.get(key)
            if isinstance(arr, list) and arr not in _seen_lists:
                _seen_lists.append(arr)
                for item in arr:
                    if isinstance(item, dict):
                        yield from _iter_items(item, _seen_lists, _seen_dicts)
        # Recurse into other nested containers
        for key, value in obj.items():
            if key in ('items', 'results'):
                continue
            if isinstance(value, dict):
                if id(value) not in _seen_dicts:
                    yield from _iter_items(value, _seen_lists, _seen_dicts)
            elif isinstance(value, list):
                if value not in _seen_lists:
                    _seen_lists.append(value)
                    for item in value:
                        if isinstance(item, dict):
                            yield from _iter_items(item, _seen_lists, _seen_dicts)
                        elif isinstance(item, list) and item not in _seen_lists:
                            _seen_lists.append(item)
                            yield from _iter_items(item, _seen_lists, _seen_dicts)

    elif isinstance(obj, list):
        if obj in _seen_lists:
            return
        _seen_lists.append(obj)
        for item in obj:
            if isinstance(item, dict):
                yield from _iter_items(item, _seen_lists, _seen_dicts)
            elif isinstance(item, list) and item not in _seen_lists:
                _seen_lists.append(item)
                yield from _iter_items(item, _seen_lists, _seen_dicts)


def _fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': _USER_AGENT})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return resp.read()


def _fetch_html(url: str) -> Optional[str]:
    try:
        data = _fetch_bytes(url)
    except Exception:
        return None
    try:
        return data.decode('utf-8', errors='ignore')
    except Exception:
        return None


def resolve_download_url(url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    lower = (url or '').lower()
    parsed = urllib.parse.urlparse(url)
    if not url:
        return None, None, 'Missing URL'
    if lower.endswith('.pdf') or '/pdf/' in lower:
        return url, '.pdf', None

    m = re.search(r'arxiv\.org/abs/([^?#/]+)', lower)
    if m:
        return f'https://arxiv.org/pdf/{m.group(1)}.pdf', '.pdf', None
    m = re.search(r'arxiv\.org/html/([^?#/]+)', lower)
    if m:
        return f'https://arxiv.org/pdf/{m.group(1)}.pdf', '.pdf', None

    if 'openreview.net' in lower:
        qs = urllib.parse.parse_qs(parsed.query)
        paper_id = qs.get('id', [None])[0]
        if paper_id:
            return f'https://openreview.net/pdf?id={paper_id}', '.pdf', None

    if 'aclanthology.org' in lower and not lower.endswith('.pdf') and parsed.path:
        return urllib.parse.urlunparse(parsed._replace(path=f"{parsed.path.rstrip('/')}.pdf", query='')), '.pdf', None

    html = _fetch_html(url)
    if html:
        m = re.search(r"<meta[^>]+name=['\"]citation_pdf_url['\"][^>]+content=['\"]([^'\"]+)['\"]", html, re.I)
        if m:
            return urllib.parse.urljoin(url, m.group(1)), '.pdf', None
        m = re.search(r"href=['\"]([^'\"]+\.pdf(?:\?[^'\"]*)?)['\"]", html, re.I)
        if m:
            return urllib.parse.urljoin(url, m.group(1)), '.pdf', None
    return None, None, 'No downloadable PDF found'


def _looks_like_research_literature(item: Dict[str, Any]) -> bool:
    flag = item.get('is_research_literature')
    if flag is not None:
        return bool(flag)
    url = str(item.get('url') or '').lower()
    source = str(item.get('source') or '').lower()
    domains = (
        'arxiv.org', 'openreview.net', 'aclanthology.org', 'proceedings.neurips.cc',
        'openaccess.thecvf.com', 'thecvf.com', 'ieeexplore.ieee.org', 'dl.acm.org',
        'springer.com', 'sciencedirect.com', 'aaai.org', 'ijcai.org', 'doi.org',
    )
    if any(d in url for d in domains):
        return True
    return source in {'arxiv', 'openreview', 'aclan', 'official', 'project_page', 'paper'}


def download_item(item: Dict[str, Any], output_dir: Path, index: int) -> Dict[str, Any]:
    title = item.get('title') or 'untitled'
    url = item.get('url') or ''
    existing = item.get('download_path')
    result = {
        'title': title,
        'url': url,
        'source': item.get('source'),
        'resolved_url': None,
        'download_attempted': True,
        'downloaded': False,
        'download_path': None,
        'download_error': None,
    }
    if existing and Path(existing).exists():
        result['downloaded'] = True
        result['download_path'] = existing
        result['download_attempted'] = False
        return result

    resolved_url, ext, err = resolve_download_url(url)
    result['resolved_url'] = resolved_url
    if err or not resolved_url or not ext:
        result['download_error'] = err or 'Unable to resolve download URL'
        return result

    slug = _safe_slug(title, f'paper_{index:03d}')
    dest = output_dir / f'{index:03d}_{slug}{ext}'
    if dest.exists():
        result['downloaded'] = True
        result['download_path'] = str(dest)
        result['download_attempted'] = False
        return result

    try:
        data = _fetch_bytes(resolved_url)
        if ext == '.pdf' and len(data) < _MIN_PDF_BYTES:
            result['download_error'] = f'Downloaded file is only {len(data)} bytes; likely not a valid PDF'
            return result
        output_dir.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        result['downloaded'] = True
        result['download_path'] = str(dest)
        return result
    except urllib.error.HTTPError as exc:
        result['download_error'] = f'HTTP {exc.code}: {exc.reason}'
    except Exception as exc:
        result['download_error'] = str(exc)
    return result


def _collect_items(data: Dict[str, Any], only_opened: bool = True) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    seen = set()
    for item in _iter_items(data):
        url = item.get('url')
        title = item.get('title')
        key = (url, title)
        if key in seen:
            continue
        seen.add(key)
        if only_opened and not item.get('opened'):
            continue
        if only_opened and item.get('open_status') not in (None, 'success'):
            continue
        if not _looks_like_research_literature(item):
            continue
        items.append(item)
    return items


def run(search_results: Path, output_dir: Path, ground_id: str, *, only_opened: bool = True, max_workers: int = _DEFAULT_MAX_WORKERS, manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    data = _read_json(search_results)
    output_dir.mkdir(parents=True, exist_ok=True)
    items = _collect_items(data, only_opened=only_opened)
    indexed_items = list(enumerate(items, start=1))
    results: List[Optional[Dict[str, Any]]] = [None] * len(indexed_items)

    with ThreadPoolExecutor(max_workers=max(1, max_workers)) as ex:
        future_map = {ex.submit(download_item, item, output_dir, idx): idx - 1 for idx, item in indexed_items}
        for fut in as_completed(future_map):
            pos = future_map[fut]
            try:
                results[pos] = fut.result()
            except Exception as exc:
                item = indexed_items[pos][1]
                results[pos] = {
                    'title': item.get('title'),
                    'url': item.get('url'),
                    'resolved_url': None,
                    'download_attempted': True,
                    'downloaded': False,
                    'download_path': None,
                    'download_error': str(exc),
                }

    final_results = [r for r in results if r is not None]
    manifest = {
        'ground_id': ground_id,
        'search_results': str(search_results),
        'download_attempted': True,
        'only_opened': only_opened,
        'eligible_item_count': len(items),
        'status': ('no_eligible_items' if len(items) == 0 else 'completed'),
        'downloaded_count': sum(1 for x in final_results if x.get('downloaded')),
        'items': final_results,
    }
    if manifest_path is None:
        manifest_path = output_dir / 'manifest.json'
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description='Download opened literature items from grounded-research-lit search_results.json')
    parser.add_argument('--search-results', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--ground-id', required=True)
    parser.add_argument('--only-opened', type=lambda x: x.lower() in {'true', '1', 'yes'}, default=True)
    parser.add_argument('--max-workers', type=int, default=_DEFAULT_MAX_WORKERS)
    parser.add_argument('--manifest-path', default=None)
    parser.add_argument(
        '--wait', '--no-wait',
        dest='wait',
        action='store_true',
        default=False,
        help='Wait for the manifest to reach a terminal+valid state before returning. '
             'Useful when this script is called multiple times and the first call may have '
             'failed due to _iter_items returning 0 items.'
    )
    parser.add_argument('--wait-poll-sec', type=float, default=_WAIT_POLL_SEC)
    parser.add_argument('--wait-timeout-sec', type=float, default=_WAIT_TIMEOUT_SEC)
    args = parser.parse_args()

    if args.wait:
        manifest_path = Path(args.manifest_path) if args.manifest_path else (
            Path(args.output_dir) / 'manifest.json'
        )
        if not manifest_path.exists():
            manifest = run(
                Path(args.search_results),
                Path(args.output_dir),
                args.ground_id,
                only_opened=args.only_opened,
                max_workers=args.max_workers,
                manifest_path=manifest_path,
            )
            print(json.dumps(manifest, ensure_ascii=False, indent=2))
        manifest = _wait_for_manifest(
            manifest_path,
            poll_sec=args.wait_poll_sec,
            timeout_sec=args.wait_timeout_sec,
        )
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0

    manifest = run(
        Path(args.search_results),
        Path(args.output_dir),
        args.ground_id,
        only_opened=args.only_opened,
        max_workers=args.max_workers,
        manifest_path=Path(args.manifest_path) if args.manifest_path else None,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
