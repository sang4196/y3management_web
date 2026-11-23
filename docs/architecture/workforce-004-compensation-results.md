# WORKFORCE-004 실행 결과 — 보상 설정 조회·Rate/Fixed 변경

2026-11-24 **설계자 로컬 인수 PASS — 최종 동결본의 새 독립 선정 검사**.
Parent `7d9e5d05f8bccd27b0038a407ddab962b25da847`, branch `codex/workforce-compensation`.
[제한 계약](workforce-004-compensation-design.md), BR-PAY-010/011/023과 기존 입력 규칙을 구현했다.
개별 판정·소스 SHA·실제 브라우저 조건·초기 실패/교정은 [최소 근거](workforce-004-compensation-review.json)에 있다.

## 구현·검토

현재 Master는 자기 Organization, Branch Admin은 현재 Trainer Home 범위에서 별도 보상 설정·이력을 조회하고
Rate/Fixed를 직접 변경한다. 관리자·Trainer 겸임자의 범위 안 본인도 허용하며 Operator/Trainer 단독은 거부한다.
Home 이동 뒤 옛 지점 관리자는 값·이력·변경·receipt 접근을 유지하지 않는다. 일반 Trainer/계정 응답에 보상을 추가하지 않았다.
Rate0~100 정수와 기존 정확한 정수원 문자열/명시0을 지원하며 누락·소수·음수를 자동 보정하지 않는다.
독립 compensation version만 실제 변경 시 +1하며 Trainer/Home/state version·계정/역할·로그인·원본 링크·초기 snapshot을 보존한다.

초기 기본급과 시작 월은 ‘최초 일반 기본급 설정’으로만 표시하며 편집하지 않는다. Rate/Fixed와 초기 포함 이력은
Audit의 제한된 공개 read/append 계약으로 조정한다. 실제 당시 Actor/Role/Branch Context·전후값·시각을 보존하고
현재 Home으로 인가한다. 초기 before 없음과 명시0을 구분한다. 새 일반 감사 전체 조회나 개인정보 공개를 추가하지 않았다.

두 version CAS·Actor 결속 fingerprint/receipt·CSRF·현재 Scope와 최종 원래 idle/absolute 기한을 검증한다.
설정/receipt/typed Audit는 한 UoW이고 감사 실패·최종 기한 만료 시 rollback한다. no-op/replay는 version/감사/활동 시각을 바꾸지 않는다.
대사 후 새 조회보다 오래된 receipt 값을 ‘현재’라고 표시하던 문제를 고쳤다. 성공 게시 여부와 선택 snapshot을 확인하고,
실제 receipt 응답과 후속 조회 사이에 다른 저장을 실행해 작업 당시/최신 조회값을 검증했다. Home 대사는 조회 당시 문맥으로 명시했다.

새0020은 원래 등록/snapshot/initial_compensation 감사의 Org·UUID·Creator·Role/Branch·초기값/시작월을 DDL 전 검증한다.
Trainer/snapshot 등록 시각과 별도로 샘플링된 원래 감사 시각을 구분한다. 현재 Home/state version이 초기와 같을 것을 요구하지 않는다.
nullable Branch를 복합 FK에 넣어 Master NULL로 결속을 우회시키지 않고, nonnullable identity와 양쪽 Context CHECK를 사용한다.
새 receipt는 no-op도 파괴 downgrade를 차단한다. 실제20→19→하위 guard 준비에서 요청 target을 지나치던 새 test adapter를
교정했고 원래0019 Home 정보/guard와 기존0001–0019·공통 harness·의존성을 유지했다.

## 최종 독립 실행

| 검사 | 실제 결과 |
| --- | --- |
| `bash check.sh fast` | 비PG197 PASS, Ruff/format/mypy PASS, Import Linter8 kept |
| 선정 PostgreSQL | 새 단일 실행39 PASS, `--require-postgres -x`, 342.47초 |
| 실제 HTTPS/native | 위39에 포함된1사례, Chromium151.0.7922.34, 정확한 manifest54항목 모두 literal true |
| 실패/error/skip/xfail/xpass·선정 누락 | 모두0 |
| Collection | 전체981=비PG197+PG784. PG745는 미실행 |

fast `auto-f04107e94187426891140187c2f5ceac`, PG/native `auto-0d35ece739954d608d5957de5918725e`.
개발/이전 점수를 재사용하거나 중복 합산하지 않았다. collection-only process exit1과 fixtures-per-test process0/QA summary1은
실행0의 메타데이터이며 제품 테스트 성공/실패로 바꾸지 않았다. 독립 실행은 모두 성공했다.
기존 Starlette/httpx와 AnyIO 경고2개는 그대로 유지했다.

## 개발 중 실패·정리·한계

fixture import 누락의 준비 실패, 기존 Trainer admin audience401 기대값, 새 guard adapter의 target20/19 조기 반환을 바로잡았다.
브라우저 첫 진입은 async panel 부재를 먼저 기다리도록 교정했다. 지연 응답 실패의 정확한 초기 원인은 끝내 확정하지 못했으며
추정하지 않는다. 대문자 stage 진단 누락과 held 응답 미해제로 종료가 막히던 경로를 보완한 뒤 원래90초 browser cap 안에서 통과했다.
단언 삭제·임의 sleep/timeout 증가·기존 보안 동작 완화는 없다. 최소 근거는 초기 실패를 최종 성공으로 덮지 않는다.

Backend191/기존 tracked298 raw SHA·보호32개·HEAD/index/refs45개·신뢰/hosts/resolver/NSS가 독립 실행 전후 동일했다.
설계자는 신규 Backend4개와 승인 설계 hash를 합친303개 소스 map, 정확한39 판정, 같은 실행의 native54 keyset/true를 대조했다.
인수 후 변경은 Architecture 문서뿐이며 Backend bytes는 그대로다. 자기 process/schema/auto 환경 부재를 대조했다.
공유 Compose PostgreSQL/원본 환경/재사용 도구를 보존하며 완료된 집계 QA 로그는 커밋 검토 뒤 최소 결론만 남긴다.

전체PG784·다른 브라우저/실물 모바일·원본 DB 적용·운영 배포·PT/Member/Settlement/역사 resolver 인수는 아니다.
일반 기본급 일정 편집/월별 수동 지정·확정 정정도 후속이다. 새로 승인된 미래 기본급 변경 취소는 다음 증분에 별도로 기록·설계한다.
다른 Product OPEN/전역 PROPOSED·운영 게이트를 유지한다.
