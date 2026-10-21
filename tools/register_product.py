#!/usr/bin/env python3
"""Good Object Note: register one *verified* product card without a build step.

This is the final data-write step after ChatGPT/browser has verified the
Coupang item. It does NOT scrape Coupang, invent reviews, or generate affiliate
tracking links. It preserves previous cards and checks identifiers/URLs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = ROOT / 'products.js'
PREFIX = '// 좋은물건노트 상품 데이터: 화면 공개용 내용만 기록합니다.\nwindow.GOODNOTE_PRODUCTS = '


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
        'publishedAt':published,'sourceProductId':source_id,'sourceItemId':source_item_id
    }


def main():
    parser=argparse.ArgumentParser(description='검증 완료된 상품 1개를 좋은물건노트 상품 목록에 등록')
    parser.add_argument('--input',required=True,help='상품 검증 정보 JSON 파일 경로')
    parser.add_argument('--dry-run',action='store_true',help='실제 파일을 변경하지 않고 검사만 수행')
    args=parser.parse_args()
    item=json.loads(Path(args.input).read_text(encoding='utf-8-sig'))
    original=read_products()
    card=validate(item,original)
    if not args.dry_run:
        updated=original+[card]
        result=PREFIX+json.dumps(updated,ensure_ascii=False,indent=2)+';\n'
        PRODUCTS.write_text(result,encoding='utf-8')
    print(f"{'검증만 완료' if args.dry_run else '등록 완료'}: #{card['id']} {card['name']}")
    print(f"구매 버튼: {'활성화' if card['affiliateUrl'] else '제휴 URL 미확인으로 비활성화'}")
    print(f"이미지: {'등록됨' if card['imageUrl'] else '대체 이미지 표시'}")


if __name__=='__main__':
    try:main()
    except (ValueError, OSError, KeyError) as e:
        print(f'등록 중단: {e}',file=sys.stderr);sys.exit(1)
