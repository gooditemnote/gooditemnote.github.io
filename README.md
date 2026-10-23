# 좋은물건노트 — R010 사이트 UI 수정 / R009 간편 상품등록

**2026-10-24 / R010 + 003 상품 포함 배포용 확인본 / GitHub Pages에 아직 배포하지 않음**

## 현재 유효한 상품등록 규칙

**`PRODUCT_REGISTRATION_RULES_R009.md`가 상품등록의 단일 기준입니다.**

> `003 상품등록 해줘` + 해당 상품 쿠팡 공식 `<iframe ...></iframe>` 원문 → 그 번호로 카드 등록.

- 요청에 필요한 것은 **상품번호와 쿠팡 공식 iframe HTML 원문**뿐입니다.
- 예전 상품명·설명·카테고리·썸네일·제품 페이지·별도 제휴 URL 입력, JSON 다중 필드 입력은 더 이상 필수가 아닙니다.
- 새 번호는 추가, 기존 번호+새 HTML은 기존 번호 교체(백업), 같은 번호+같은 HTML은 변경 없음.
- 쿠팡 HTML 원문의 글자·속성·추적 URL을 손대지 않습니다.
- `tools/register_product.py`가 번호와 iframe 파일만으로 등록·교체합니다. 백업은 사이트 폴더 외부로 저장합니다.
- 예시 `002 / cqkigJ`는 **정책 샘플**이며, 이번 R009 파일에서 실제 002 상품 링크는 변경하지 않았습니다.

## 현재 등록 상품

| 번호 | 실제 iframe URL | 원문 보관 경로 |
|---|---|---|
| 001 | `https://coupa.ng/cqkhQb` | `partner-html/001.html` |
| 002 | `https://coupa.ng/cqkhNh` | `partner-html/002.html` |
| 003 | `https://coupa.ng/cqnN6I` | `partner-html/003.html` |

R010 UI는 모바일 2열 / PC 4열, 번호 배지·테두리·쿠팡 iframe 카드, 상품번호 전용 검색, **최신 순 / 오래된 순 2개 정렬**, 12개씩 더보기를 유지합니다.

### R010 화면 개선 (2026-10-22)

- 모바일 상단 브랜드명, 제목, 설명을 중앙 정렬 (PC는 기존 정렬 유지).
- 정렬 라벨은 화면에서 제거하되 스크린리더용 `aria-label="상품 정렬"` 유지.
- 목록 정렬은 `최신 순`(기본값), `오래된 순` 2개만 제공. 기준은 등록일 `publishedAt`, 날짜가 같으면 고정 상품번호로 구분.
- 하단 **기존 300x250 쿠팡 광고 이미지/링크 제거**. 제공받은 공식 `PartnersCoupang.G` 캐러셀(광고 ID 1041957, trackingCode AF4347646, 400x400) 코드로 교체.
- 외부 광고 스크립트와 설정 문자열은 **원문 그대로 사용**, 400px 미만 화면에서는 광고 바깥쪽 래퍼만 축소. iframe 내부나 광고 설정은 수정하지 않음.
- 하단 광고 표시 여부 및 실제 클릭 추적/수익 귀속은 네트워크와 쿠팡 측 동작에 따라 달라질 수 있어 배포 후 확인 필요.
- `card-preview.html`에는 정렬·모바일 중앙 정렬을 동일 반영했지만 실제 제휴 광고 스크립트는 포함하지 않음.

## 작업 시 참고

- `index.html`: 실제 상품 목록 화면.
- `products.js`: 상품번호·공식 iframe을 읽어 화면에 표시합니다.
- `partner-html/NNN.html`: 각 상품의 공식 쿠팡 HTML **원본**입니다.
- `tools/register_product.py`: `--number` + `--partner-html-file` 등록/교체 도구.
- `PRODUCT_REGISTRATION_RULES_R009.md`: **유효한 등록 규칙**.
- `R004_POLICY.md`, `R005_POLICY.md`, `R006_REVIEW.md`, `R007_001_002_APPLY.md`, `R008_NUMBER_ONLY_SEARCH.md`: 과거 정책/구현 기록입니다. **R009와 충돌하는 상품등록 문구는 더 이상 적용하지 않습니다.**

### 자동 등록 명령 예시

```sh
python tools/register_product.py --number 003 --partner-html-file /path/to/new-official-iframe.html --dry-run
python tools/register_product.py --number 003 --partner-html-file /path/to/new-official-iframe.html
```

실제 GitHub Pages 업로드는 사용자 요청 및 별도 배포 단계입니다.
