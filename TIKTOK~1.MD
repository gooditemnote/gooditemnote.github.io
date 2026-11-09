# 좋은물건노트 | TikTok 이벤트 연결 설정 (2026-10-22)

## 상태
- 사이트 설치본의 Google Tag Manager 웹 컨테이너: `GTM-TBPN8QQW` 유지.
- 사이트는 사용자의 실제 상품번호 검색 및 정확히 일치하는 상품번호의 조회를 `dataLayer`에 기록하도록 준비됨.
- TikTok Pixel ID는 제공되지 않았으므로 **GTM에서 TikTok Pixel 설정 및 이벤트 매핑은 아직 진행되지 않음**.
- 첨부 화면에 보였던 2개의 잘못된 이벤트 이름과 `value: 0`의 원인은 원격 GTM/TikTok 태그 설정에 있을 수 있음. **이 사이트 파일 교체만으로 기존 원격 태그 오류가 자동 수정되지는 않음**.
- 본 파일은 TikTok Ads Manager 또는 Google Tag Manager 설정을 자동으로 변경/게시하지 않음.

## 사이트에서 GTM으로 전송하는 실제 행동

| 행동 | dataLayer `event` | 데이터 | TikTok에 매핑할 표준 이벤트 |
| --- | --- | --- | --- |
| 상품번호 001, 002 등 정확한 숫자 3~4자리 검색 입력 후 650ms 또는 입력 완료 | `goodnote_search` | `search_string`: `001` 또는 `002` | `Search` |
| 해당 번호 상품이 실제 목록에 존재하고 검색으로 표시됨 | `goodnote_view_content` | `content_type`: `product`, `content_ids`: `["001"]` 등 | `ViewContent` |
| `?item=001` 형식의 직접 방문으로 해당 상품이 보임 | `goodnote_view_content` | 위와 동일 | `ViewContent` |

방문 기본 이벤트 `PageView`는 TikTok Pixel 기본 태그/기존 설정에서 처리합니다. 중복 발신 금지.

사용자가 상품번호 `0` 또는 `00`을 입력한 중간 상태, 존재하지 않는 상품번호, iframe 내 클릭, 쿠팡에서 이루어진 결제는 조회 또는 구매로 기록하지 않습니다.

**구매 가공 금지:** `Purchase`, `CompletePayment`, `InitiateCheckout`, `AddToCart`, `value:0`, `currency:'USD'`, 임의 거래번호, 구매자 이메일/전화번호 해시를 삽입하지 않았습니다.

## GTM-TBPN8QQW에서 사용자 또는 관리자 설정

1. https://tagmanager.google.com 에서 컨테이너 `GTM-TBPN8QQW`를 열고, **Preview(미리보기)** 로 오류 이벤트를 보낸 기존 TikTok 태그를 먼저 찾아봅니다. 기존 `event` 이름이 비어 있거나 변수 매핑이 잘못된 태그, 가격도 없는데 `value: 0`을 보내는 태그가 있다면 원인을 고치거나 해당 TikTok 이벤트 태그/트리거만 사용 중지합니다. 정상 GA4 이벤트 및 다른 태그는 임의로 삭제하지 않습니다.
2. TikTok Events Manager의 해당 Pixel ID를 확인합니다. Pixel 기본 태그가 이미 설치돼 있다면 재설치하지 않습니다. Google Tag Manager에 TikTok Pixel 기본 태그가 없다면 TikTok 공식 GTM 통합/템플릿으로 연결합니다. **이 사이트에는 GTM 컨테이너 코드만 설치되어 있으며 Pixel ID는 미포함**입니다.
3. GTM의 **변수 → 사용자 정의 변수 → 데이터 영역 변수(Data Layer Variable)** 에서 아래 3개를 생성합니다.
   - `DLV - search_string`: Data Layer Variable Name `search_string`
   - `DLV - content_ids`: Data Layer Variable Name `content_ids`
   - `DLV - content_type`: Data Layer Variable Name `content_type`
4. GTM의 **트리거 → 새로 만들기 → 맞춤 이벤트(Custom Event)** 를 두 개 생성합니다.
   - `CE - goodnote_search`: 이벤트 이름 `goodnote_search`
   - `CE - goodnote_view_content`: 이벤트 이름 `goodnote_view_content`
5. GTM의 TikTok Pixel 이벤트 태그(공식 템플릿 또는 이미 설치된 TikTok 이벤트 태그 방식)를 2개 구성합니다.
   - `TikTok - Search` / TikTok 표준 이벤트 이름 **`Search`** / 트리거 `CE - goodnote_search` / 파라미터 `search_string` → `{{DLV - search_string}}`
   - `TikTok - ViewContent` / TikTok 표준 이벤트 이름 **`ViewContent`** / 트리거 `CE - goodnote_view_content` / 파라미터 `content_ids` → `{{DLV - content_ids}}`, `content_type` → `{{DLV - content_type}}`
   - `value`와 `currency`는 둘 다 **생략**합니다. 실거래가 없는데 숫자 1 등을 임의로 넣지 않습니다.
6. **GTM Preview** 에서 `?item=001`로 진입하면 `goodnote_view_content`가 1회 발생하는지, 상품번호 `002`를 검색하면 `goodnote_search` 후 `goodnote_view_content`가 발생하는지 확인합니다. TikTok Pixel Helper 및 TikTok 이벤트 관리자 > 테스트 이벤트에서 `Search`, `ViewContent` 수신을 확인합니다. 두 오류 이벤트는 원인 태그를 찾아 끈 후 **새로운 테스트에서 재발하지 않는지** 확인합니다.
7. 검증 후에만 GTM에서 **제출/게시**합니다. 이전에 수신된 과거 오류는 테스트 이력에 계속 표시될 수 있습니다.

## 중요 제한

- 공식 쿠팡 iframe 안의 버튼 클릭/실구매는 타 도메인에서 일어나므로 사이트 JavaScript/GTM으로 확인할 수 없습니다.
- 제품 001·002 공식 `iframe` 및 모든 제휴 URL은 그대로입니다. 외부 구매 버튼·오버레이를 새로 추가하지 않았습니다.
- 검색/조회 전환은 구매 수익을 의미하지 않습니다. 틱톡 광고 목표에 맞게 유효한 표준 이벤트를 선택하세요.
- 쿠팡 파트너스 수익 통계는 쿠팡에서 별도로 확인하세요.
- 실제 원격 TikTok 픽셀 및 GTM 게시 상태는 이 ZIP만으로 확인할 수 없습니다.

## 공식 참고
- TikTok 표준 이벤트: https://ads.tiktok.com/resources/help/article/standard-events-parameters
- GTM 연결: https://ads.tiktok.com/resources/help/article/get-started-google-tag-manager
- Pixel Helper 오류 진단: https://ads.tiktok.com/resources/help/article/tiktok-pixel-helper-2.0
