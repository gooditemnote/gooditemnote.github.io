# 좋은물건노트 — R010 UI 수정 및 보호 규칙

**2026-10-22 / R009 기준 사이트 소스에서 제한 수정 / 배포하지 않음**

## 수정 사항
1. 600px 이하 모바일에서 상단 브랜드(좋은물건노트), 히어로 제목/설명 중앙 정렬. 601px 이상은 기존 정렬.
2. 상품 정렬 라벨은 시각적으로 제거. `select#sort`에 `aria-label="상품 정렬"` 부여.
3. 정렬 옵션 `최신 순`(기본값) / `오래된 순`만 유지. 날짜 `publishedAt` 기준. 값이 같으면 번호 tie-break.
4. 기존 300x250 제휴 이미지와 제휴 링크 배너를 삭제. 아래 사용자가 제공한 쿠팡 캐러셀 스크립트를 하단 제휴광고 영역에 원문 그대로 삽입:

```html
<script src="https://ads-partners.coupang.com/g.js"></script>
<script>
	new PartnersCoupang.G({"id":1041957,"template":"carousel","trackingCode":"AF4347646","width":"400","height":"400","tsource":""});
</script>
```

5. 400x400 광고 코드는 고정. 400px보다 좁은 화면은 **외부 래퍼만 스케일**해서 잘림 방지. 네트워크 오류나 광고 차단 환경에서는 실제 광고 노출 검증에 제한이 있음.

## 불변 조건
- 상품 등록 규칙은 `PRODUCT_REGISTRATION_RULES_R009.md` 유지.
- `products.js`와 `partner-html/001.html`, `partner-html/002.html`은 R009 대비 바이트 단위 동일.
- 상품번호 검색·001/002 상품 카드·2열/4열·번호 배지·더보기·제휴 안내문·링크 보호 유지.
- R010에서 원본 쿠팡 광고 HTML 코드는 어떠한 속성도 변경하지 않음.

## 범위
- 변경: `index.html`, `card-preview.html`, `README.md`.
- 추가: `R010_UI_IMPLEMENTATION.md`, `R010_TEST_RESULTS.md`.
- 원격 GitHub Pages 배포: **하지 않음**.
