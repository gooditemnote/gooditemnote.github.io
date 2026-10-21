#!/usr/bin/env python3
"""Good Object Note: register one *verified* product card without a build step.

This is the final data-write step after ChatGPT/browser has verified the
Coupang item. It does NOT scrape Coupang, invent reviews, or generate affiliate
tracking links. It preserves previous cards and checks identifiers/URLs.
Supplied partner HTML is inspected without rewriting its source text.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = ROOT / 'products.js'
PREFIX = '// 좋은물건노트 상품 데이터: 화면 공개용 내용만 기록합니다.\nwindow.GOODNOTE_PRODUCTS = '


class PartnerIframeParser(HTMLParser):
    """Inspect the supplied markup; never rebuild it from parsed attributes."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.started = False
        self.finished = False

    def handle_starttag(self, tag, attrs):
        if tag != 'iframe' or self.started:
            raise ValueError('partnerHtml에는 단일 iframe만 넣어 주세요.')
        self.started = True
        names = [name for name, _ in attrs]
        allowed = {'src', 'width', 'height', 'frameborder', 'scrolling',
                   'referrerpolicy', 'title', 'loading', 'allowfullscreen'}
        if len(names) != len(set(names)):
            raise ValueError('partnerHtml에 중복 속성이 있습니다. 원문을 다시 확인하세요.')
        if any(name.startswith('on') or name == 'srcdoc' for name in names):
            raise ValueError('partnerHtml에는 이벤트 속성이나 srcdoc을 넣을 수 없습니다.')
        if any(name not in allowed for name in names):
            raise ValueError('partnerHtml에 화면에서 지원하지 않는 속성이 있습니다. 원문을 바꾸지 않고 등록을 중단합니다.')
        src = dict(attrs).get('src')
        if not isinstance(src, str) or not src or re.search(r'[\x00-\x20\x7f]', src):
            raise ValueError('partnerHtml에 정상적인 쿠팡 파트너스 src가 필요합니다.')
        parsed = urlsplit(src)
        if (parsed.scheme != 'https'
                or parsed.hostname not in ('coupa.ng', 'link.coupang.com')
                or parsed.username or parsed.password
                or parsed.port not in (None, 443) or not parsed.path.strip('/')):
            raise ValueError('iframe src는 HTTPS 쿠팡 파트너스 주소여야 합니다.')

    def handle_endtag(self, tag):
        if tag != 'iframe' or not self.started or self.finished:
            raise ValueError('partnerHtml의 iframe 닫는 태그를 확인하세요.')
        self.finished = True

    def handle_data(self, data):
        if data and not data.isspace():
            raise ValueError('partnerHtml에는 iframe 이외의 내용을 넣을 수 없습니다.')

    def reject_extra(self, *args):
        raise ValueError('partnerHtml에는 추가 태그·주석·선언·텍스트를 넣을 수 없습니다.')

    handle_startendtag = reject_extra
    handle_comment = reject_extra
    handle_decl = reject_extra
    unknown_decl = reject_extra
    handle_pi = reject_extra
    handle_entityref = reject_extra
    handle_charref = reject_extra


def approved_partner_html(raw):
    if not isinstance(raw, str) or not raw:
        raise ValueError('partnerHtml에 해당 상품의 쿠팡 공식 HTML 원문이 필요합니다.')
    if len(raw) > 20000:
        raise ValueError('partnerHtml이 너무 깁니다. 단일 상품의 원문을 확인하세요.')
    # HTMLParser is forgiving about malformed HTML. Require a complete, quoted
    # or unquoted attribute grammar as well, rather than silently repairing it.
    space = r'[\t\n\f\r ]'
    attribute = r'''[A-Za-z_:][A-Za-z0-9_:.-]*(?:[\t\n\f\r ]*=[\t\n\f\r ]*(?:"[^"]*"|'[^']*'|[^\s"'=<>`]+))?'''
    shape = rf'{space}*<iframe(?:{space}+{attribute})*{space}*>{space}*</iframe{space}*>{space}*'
    if not re.fullmatch(shape, raw, flags=re.IGNORECASE):
        raise ValueError('partnerHtml은 완전히 닫힌 iframe 원문이어야 합니다. 자동 보정하지 않습니다.')
    parser = PartnerIframeParser()
    parser.feed(raw)
    parser.close()
    if not parser.started or not parser.finished or parser.rawdata:
        raise ValueError('partnerHtml의 iframe 원문이 완전하지 않습니다.')
    return raw


def read_products():
    text = PRODUCTS.read_text(encoding='utf-8').strip()
    if not text.startswith(PREFIX.strip()) or not text.endswith(';'):
        raise ValueError('products.js 형식이 예상과 다릅니다. 임의로 덮어쓰지 않습니다.')
    contents = text[len(PREFIX.strip()):-1].strip()
    values = json.loads(contents)
    if not isinstance(values, list):
        raise ValueError('상품 배열 형식이 아닙니다.')
    return values


def approved_affiliate(url):
    if not url:
        return ''
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in ('link.coupang.com', 'coupa.ng'):
        raise ValueError('affiliateUrl은 검증된 쿠팡 파트너스 제휴 주소만 사용해야 합니다.')
    if parsed.username or parsed.password or not parsed.path.strip('/'):
        raise ValueError('affiliateUrl 형식이 올바르지 않습니다.')
    return url


def normal_image(path):
    if not path:
        return ''
    if not re.fullmatch(r'\./assets/[a-zA-Z0-9_./-]+\.(?:png|jpg|jpeg|webp|avif)',path,re.IGNORECASE) or '..' in path:
        raise ValueError('imageUrl은 권한이 확인된 ./assets/ 파일만 등록하세요.')
    if not (ROOT / path).resolve().is_file():
        raise ValueError('실제 이미지 파일이 assets 폴더에 없습니다.')
    return path


def normal_video(url):
    if not url:
        return ''
    parsed=urlsplit(url)
    if parsed.scheme!='https' or parsed.hostname not in ('youtube.com','www.youtube.com','m.youtube.com','youtu.be'):
        raise ValueError('videoUrl은 정상적인 HTTPS 유튜브 주소만 사용하세요.')
    return url


def source_ids(url):
    if not url:
        return '',''
    parsed=urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in ('coupang.com','www.coupang.com'):
        raise ValueError('sourceUrl은 쿠팡의 일반 상품 페이지 주소여야 합니다.')
    m=re.fullmatch(r'/vp/products/(\d+)(?:/)?',parsed.path)
    if not m:
        raise ValueError('sourceUrl에서 쿠팡 상품 번호를 찾지 못했습니다.')
    from urllib.parse import parse_qs
    v=parse_qs(parsed.query)
    item=v.get('itemId',[''])[0]
    if item and not item.isdecimal():
        raise ValueError('itemId는 숫자여야 합니다.')
    return m.group(1),item


def trimmed(obj,key,required=False,cap=180):
    value=obj.get(key,'')
    if not isinstance(value,str):
        raise ValueError(f'{key}는 문자열이어야 합니다.')
    value=value.strip()
    if required and not value:
        raise ValueError(f'{key}가 필요합니다. 상품 페이지에서 확인한 정보만 사용하세요.')
    if len(value)>cap:
        raise ValueError(f'{key}가 너무 깁니다.')
    return value


def validate(item,existing):
    if not isinstance(item,dict):
        raise ValueError('입력 파일은 JSON 객체여야 합니다.')
    partner_html = approved_partner_html(item.get('partnerHtml'))
    existing_ids=[int(str(p['id'])) for p in existing]
    expected=max(existing_ids,default=0)+1
    requested=item.get('id')
    number=expected if requested in (None,'') else int(str(requested))
    if number!=expected:
        raise ValueError(f'다음 등록 번호는 {expected:03d}입니다. 기존 번호를 건너뛰거나 덮어쓰지 않습니다.')
    if number<1 or number>9999:
        raise ValueError('번호는 001부터 9999까지 지원합니다.')
    category=trimmed(item,'category',True,40)
    title=trimmed(item,'name',True,70)
    summary=trimmed(item,'summary',True,240)
    feature=trimmed(item,'feature',False,150)
    note=trimmed(item,'note',False,240)
    if '<' in title or '>' in title or '<' in summary or '>' in summary:
        raise ValueError('HTML 마크업은 상품 공개 정보에 허용하지 않습니다.')
    brand_terms=item.get('brandTokens',[])
    if not isinstance(brand_terms,list) or any(not isinstance(t,str) for t in brand_terms):
        raise ValueError('brandTokens는 검수할 브랜드명 목록이어야 합니다.')
    combined=' '.join([title,summary,feature,note,category]).casefold()
    for term in brand_terms:
        if term.strip() and term.strip().casefold() in combined:
            raise ValueError('브랜드명 노출 금지: 공개 문구에서 브랜드 이름이 발견되었습니다.')
    source_id, source_item_id=source_ids(trimmed(item,'sourceUrl',True,2000))
    if any(str(x.get('sourceProductId',''))==source_id and (
            not source_item_id or not x.get('sourceItemId') or str(x.get('sourceItemId'))==source_item_id
    ) for x in existing):
        raise ValueError('동일한 쿠팡 상품 및 옵션이 이미 등록되어 있습니다.')
    if any(str(x.get('id'))==str(number).zfill(3) for x in existing):
        raise ValueError('이미 사용 중인 상품번호입니다.')
    affiliate=approved_affiliate(trimmed(item,'affiliateUrl',False,2000))
    image=normal_image(trimmed(item,'imageUrl',False,260))
    video=normal_video(trimmed(item,'videoUrl',False,2000))
    published=trimmed(item,'publishedAt') or dt.date.today().isoformat()
    try:
        dt.date.fromisoformat(published)
    except ValueError as exc:
        raise ValueError('publishedAt은 YYYY-MM-DD 형식이어야 합니다.') from exc
    return {
        'id': f'{number:03d}', 'name':title, 'category':category,
        'summary':summary,'feature':feature,'note':note,
        'affiliateUrl':affiliate,'imageUrl':image,'videoUrl':video,
        'partnerHtml':partner_html,
        'publishedAt':published,'sourceProductId':source_id,'sourceItemId':source_item_id
    }


def main():
    parser=argparse.ArgumentParser(description='검증 완료된 상품 1개를 좋은물건노트 상품 목록에 등록')
    parser.add_argument('--input',required=True,help='상품 검증 정보 JSON 파일 경로')
    parser.add_argument('--partner-html-file',help='쿠팡 공식 HTML 원문 UTF-8 파일 경로 (줄바꿈 포함 그대로 보관)')
    parser.add_argument('--dry-run',action='store_true',help='실제 파일을 변경하지 않고 검사만 수행')
    args=parser.parse_args()
    item=json.loads(Path(args.input).read_text(encoding='utf-8-sig'))
    if not isinstance(item, dict):
        raise ValueError('입력 파일은 JSON 객체여야 합니다.')
    if args.partner_html_file:
        raw = Path(args.partner_html_file).read_bytes().decode('utf-8')
        supplied = item.get('partnerHtml', '')
        if supplied != '' and supplied != raw:
            raise ValueError('JSON의 partnerHtml과 HTML 파일 원문이 다릅니다. 원문 하나로 맞춰 주세요.')
        item['partnerHtml'] = raw
    original=read_products()
    card=validate(item,original)
    updated=original+[card]
    serialized=json.dumps(updated,ensure_ascii=False,indent=2)
    restored=json.loads(serialized)
    if any(saved.get('partnerHtml') != before.get('partnerHtml')
           for before, saved in zip(updated, restored)):
        raise ValueError('HTML 원문 보존 검사에 실패하여 저장하지 않습니다.')
    if not args.dry_run:
        result=PREFIX+serialized+';\n'
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',newline='',
                                             dir=PRODUCTS.parent,delete=False) as output:
                temporary = Path(output.name)
                output.write(result)
            temporary.replace(PRODUCTS)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    print(f"{'검증만 완료' if args.dry_run else '등록 완료'}: #{card['id']} {card['name']}")
    print('쿠팡 공식 HTML: 원문 보존 검사 완료 (상품번호·배치·테두리는 바깥에서 표시)')
    print(f"기존 제휴 URL: {'보관됨' if card['affiliateUrl'] else '별도 URL 없음'}")


if __name__=='__main__':
    try:main()
    except (ValueError, OSError, KeyError) as e:
        print(f'등록 중단: {e}',file=sys.stderr);sys.exit(1)
