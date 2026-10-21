#!/usr/bin/env python3
"""좋은물건노트 R009 — 번호 + 쿠팡 공식 iframe 원문으로만 상품 등록/교체.

Do not transform the supplied iframe markup or its affiliate tracking URL.
This script never guesses product details or deploys the website.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS_FILE = ROOT / 'products.js'
PARTNER_DIR = ROOT / 'partner-html'
PREFIX = '// 좋은물건노트 상품 데이터: 화면 공개용 내용만 기록합니다.\nwindow.GOODNOTE_PRODUCTS = '
KST = ZoneInfo('Asia/Seoul')


class StrictIframe(HTMLParser):
    """HTML inspector only: this parser's output is NEVER used for rendering."""

    ALLOWED = {'src', 'width', 'height', 'frameborder', 'scrolling',
               'referrerpolicy', 'title', 'loading', 'allowfullscreen'}

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.opened = False
        self.closed = False

    def handle_starttag(self, tag, attrs):
        if tag != 'iframe' or self.opened:
            raise ValueError('쿠팡 공식 HTML에는 단일 iframe만 사용할 수 있습니다.')
        self.opened = True
        names = [key for key, _ in attrs]
        if len(set(names)) != len(names) or any(key not in self.ALLOWED for key in names):
            raise ValueError('iframe 속성이 검증 조건과 다릅니다. 원문을 수정하지 않고 중단합니다.')
        src = dict(attrs).get('src')
        if not src or re.search(r'[\x00-\x20\x7f]', src):
            raise ValueError('iframe src를 확인해 주세요.')
        try:
            url = urlsplit(src)
            ok = (url.scheme == 'https'
                  and url.hostname in ('coupa.ng', 'link.coupang.com')
                  and not url.username and not url.password and url.port in (None, 443)
                  and bool(url.path.strip('/')))
        except ValueError:
            ok = False
        if not ok:
            raise ValueError('공식 HTTPS 쿠팡 파트너스 iframe 링크만 등록할 수 있습니다.')

    def handle_endtag(self, tag):
        if tag != 'iframe' or not self.opened or self.closed:
            raise ValueError('iframe 닫기 태그가 올바르지 않습니다.')
        self.closed = True

    def handle_data(self, data):
        if data and not data.isspace():
            raise ValueError('iframe 바깥의 텍스트를 포함하지 마세요.')

    def reject(self, *args):
        raise ValueError('iframe 이외의 태그·주석·선언을 포함하지 마세요.')

    handle_startendtag = reject
    handle_comment = reject
    handle_decl = reject
    unknown_decl = reject
    handle_pi = reject
    handle_entityref = reject
    handle_charref = reject


def validate_number(value: str) -> str:
    if not re.fullmatch(r'\d{3,4}', value) or int(value) == 0 or f'{int(value):03d}' != value:
        raise ValueError('상품번호는 001~9999 형식으로 정확히 입력해 주세요.')
    return value


def validate_html(raw: str) -> str:
    if not isinstance(raw, str) or not raw or len(raw) > 20000:
        raise ValueError('쿠팡 공식 iframe HTML 원문을 제공해 주세요.')
    space = r'[\t\n\f\r ]'
    attribute = r'''[A-Za-z_:][A-Za-z0-9_:.-]*(?:[\t\n\f\r ]*=[\t\n\f\r ]*(?:"[^"]*"|'[^']*'|[^\s"'=<>`]+))?'''
    grammar = rf'{space}*<iframe(?:{space}+{attribute})*{space}*>{space}*</iframe{space}*>{space}*'
    if not re.fullmatch(grammar, raw, flags=re.IGNORECASE):
        raise ValueError('완전한 iframe HTML이 아닙니다. 원문은 자동 수정하지 않습니다.')
    parser = StrictIframe()
    parser.feed(raw)
    parser.close()
    if not parser.opened or not parser.closed or parser.rawdata:
        raise ValueError('iframe 원문이 완전하지 않습니다.')
    return raw


def load_products() -> list[dict]:
    original = PRODUCTS_FILE.read_text(encoding='utf-8')
    base = PREFIX.strip()
    stripped = original.strip()
    if not stripped.startswith(base) or not stripped.endswith(';'):
        raise ValueError('products.js 형식을 확인할 수 없어 원본 파일을 보호합니다.')
    data = json.loads(stripped[len(base):-1].strip())
    if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
        raise ValueError('상품 목록 JSON 배열이 올바르지 않습니다.')
    ids = [item.get('id') for item in data]
    if len(ids) != len(set(ids)):
        raise ValueError('기존 목록에 중복 상품번호가 있습니다. 먼저 해결해야 합니다.')
    return data


def write_atomic(path: Path, contents: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
            temp_path = Path(f.name)
            f.write(contents)
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def register(number: str, raw_html: str, dry_run: bool, backup_dir: Path | None):
    number = validate_number(number)
    raw_html = validate_html(raw_html)
    before_js = PRODUCTS_FILE.read_bytes()
    before = load_products()
    path = PARTNER_DIR / f'{number}.html'
    before_html = path.read_bytes() if path.exists() else None
    found = next((i for i, item in enumerate(before) if item.get('id') == number), None)

    # Existing source files MUST agree with registered HTML; never overwrite a
    # conflicting file, even if a new message names the same number.
    if found is not None:
        old_html = before[found].get('partnerHtml')
        if old_html is not None:
            if not isinstance(old_html, str) or before_html is None or before_html != old_html.encode('utf-8'):
                raise ValueError('기존 쿠팡 HTML 보관본과 상품 데이터가 일치하지 않아 중단합니다.')
        elif before_html is not None:
            raise ValueError('해당 번호의 HTML 파일이 있으나 목록에 연결되지 않아 중단합니다.')
    elif before_html is not None:
        raise ValueError('상품번호의 HTML 보관 파일이 이미 있어 중단합니다.')

    if found is not None and before[found].get('partnerHtml') == raw_html:
        print(f'변경 없음: {number}번에 동일한 HTML이 이미 등록되어 있습니다.')
        return

    # For replacements, never carry old item names/IDs/affiliate links forward:
    # the iframe's short URL alone cannot verify that the product is the same.
    entry = {
        'id': number,
        'name': f'상품 {number}',          # neutral internal accessibility label
        'partnerHtml': raw_html,
        'publishedAt': dt.datetime.now(KST).date().isoformat(),
    }
    after = [dict(item) for item in before]
    if found is None:
        after.append(entry)
        action = '새로 등록'
    else:
        after[found] = entry
        action = '기존 번호 HTML 교체'

    # JSON encoding escapes quotation marks for JavaScript syntax. It does NOT
    # change the iframe markup represented by the partnerHtml string.
    encoded_js = (PREFIX + json.dumps(after, ensure_ascii=False, indent=2) + ';\n').encode('utf-8')
    restored = json.loads(encoded_js.decode('utf-8').strip()[len(PREFIX.strip()):-1])
    if any(old.get('partnerHtml') != new.get('partnerHtml') for old, new in zip(before, restored)
           if old.get('id') != number):
        raise ValueError('이전 상품의 HTML이 변경되어 등록을 중단했습니다.')
    if next(item for item in restored if item['id'] == number)['partnerHtml'] != raw_html:
        raise ValueError('등록할 HTML 원문이 변조되어 중단했습니다.')

    sha = hashlib.sha256(raw_html.encode('utf-8')).hexdigest()
    print(f'검증 완료: {number}번 / {action} / HTML SHA-256 {sha}')
    if dry_run:
        print('DRY RUN: 실제 파일과 백업은 변경되지 않았습니다.')
        return

    # Keep snapshots OUTSIDE the public GitHub Pages directory.
    snapshots = backup_dir or ROOT.parent / f'{ROOT.name}_registration_backups'
    snapshots.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(KST).strftime('%Y%m%d_%H%M%S_%f')
    snapshot = snapshots / f'{stamp}_{number}'
    snapshot.mkdir()
    (snapshot / 'products.js').write_bytes(before_js)
    if before_html is not None:
        (snapshot / f'{number}.html').write_bytes(before_html)

    try:
        write_atomic(path, raw_html.encode('utf-8'))
        write_atomic(PRODUCTS_FILE, encoded_js)
        if path.read_bytes() != raw_html.encode('utf-8'):
            raise ValueError('HTML 파일 원문 일치 검증 실패')
        check = load_products()
        if next(item['partnerHtml'] for item in check if item.get('id') == number) != raw_html:
            raise ValueError('상품 목록 HTML 원문 일치 검증 실패')
    except Exception:
        write_atomic(PRODUCTS_FILE, before_js)
        if before_html is None:
            path.unlink(missing_ok=True)
        else:
            write_atomic(path, before_html)
        raise
    print(f'{action} 완료: {number} (기존 파일 백업: {snapshot})')
    print('쿠팡 iframe·제휴 링크·속성 원문은 수정하지 않았습니다.')


def main():
    parser = argparse.ArgumentParser(description='상품번호 + 쿠팡 iframe HTML 원문만으로 등록 또는 교체 (R009)')
    parser.add_argument('--number', required=True, help='고정 상품번호: 예 003')
    parser.add_argument('--partner-html-file', required=True, help='쿠팡에서 복사한 iframe HTML 원문 UTF-8 파일')
    parser.add_argument('--dry-run', action='store_true', help='검증만 수행')
    parser.add_argument('--backup-dir', type=Path, help='백업 저장 경로(사이트 공개 폴더 외부 권장)')
    args = parser.parse_args()
    raw = Path(args.partner_html_file).read_bytes().decode('utf-8')
    register(args.number, raw, args.dry_run, args.backup_dir)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f'등록 중단: {exc}', file=sys.stderr)
        sys.exit(1)
