# R009 로컬 검증 결과

- 기준 파일: R008 수정본을 복제한 R009. 실제 GitHub Pages 원격 배포 없음.
- 현재 **001 = cqkhQb / 002 = cqkhNh** 그대로 유지, HTML 파일과 JS 내 원문 바이트 일치.
- `tools/register_product.py`는 `--number`, `--partner-html-file`만 요구. JSON 다중 필드 입력 폐지.
- 신규 `003` 등록, 기존 `002` 교체 및 원본 백업, 동일 내용 중복 등록 방지, dry-run 파일 무변경 PASS (격리된 임시 디렉터리에서 검증).
- 쿠팡 외 도메인 iframe, 잘못된 HTML, 틀린 상품번호 형식, HTML 보관 파일 불일치 검출 및 중단 PASS.
- 브라우저 `index.html`·`card-preview.html` 각 320px / 390px / 1024px: 모바일 2열·PC 4열, 001·002 iframe, 번호 전용 검색, 정렬, 공백/숫자 검색 통과.
- `index.html`과 `card-preview.html`의 JS 구문검사 PASS.
- `002 / cqkigJ`는 교체 동작을 **복제본 테스트**로만 확인. 실제 R009의 002 데이터에는 **적용하지 않음**.
- 외부 쿠팡 페이지의 최종 상품 및 수익 집계는 본 검증에서 확인하지 않음. 배포 후 실접속 필요.
