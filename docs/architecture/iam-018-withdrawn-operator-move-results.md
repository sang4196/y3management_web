# IAM-018 실행 결과 — 회수된 Operator의 업무 지점 변경

2026-11-12 **설계자 로컬 인수 PASS — 최종 동결본의 새 독립 선정 검사**.
Parent `7b64f5731ed993f5f8473a1476f27fb6c4931513`, branch `codex/iam-withdrawn-operator-move`.
[OP-7](../product/product-decisions.md#review-20261112-withdrawn-operator-move)와 [제한 계약](iam-018-withdrawn-operator-move-design.md)을 구현했다.
정확한 node/개별 판정·소스 map·같은 실행의 브라우저 boolean·초기 실패 보완은 [최소 근거](iam-018-withdrawn-operator-move-review.json)에 있다.

## 구현과 검토

같은 조직 Master는 보존 grant가 있는 Operator를 유효/회수 및 계정 상태와 관계없이 활성 지점으로 이동할 수 있다.
회수 상태·차단/reset/복구 목적·독립 관리자/Trainer 역할·Home/업무 상태·보상 설정·C2/과거 이력은 유지한다.
새 역할/계정/링크를 자동 생성하지 않는다. 새 현재 지점의 허용 관리자가 별도로 재부여/명시 재발급하며
DISABLED 재부여와 역할0 로그인은 계속 거부한다. 기존 grant가 없는 이동·BA 이동·타 조직/비활성 목적지는 거부한다.

기존 현재 Caller/expected Actor·CSRF·account/Operator CAS·잠금·typed self/최종 기한·단일 UoW를 재사용했다.
실제 이동은 grant epoch를 한 번 전진시키고 옛 로그인/원본 링크를 철회하며 감사와 receipt를 함께 저장한다.
no-op/replay는 새 로그인/원본을 다시 철회하거나 활동 시각을 늘리지 않는다. 원래 receipt와 현재 상태,
원래 Actor identity와 현재 Branch 인가를 구별하며 이전 지점 관리자는 이동 뒤 권한을 유지하지 않는다.

새 `0018_withdrawn_operator_move`는 원래17 전이 CHECK를 실제 catalog의 식/열로 정확히 식별한다.
move의 전후 granted 동일만 확장하며 나머지 CHECK/FK/Actor/Branch/version 조건과 원래 행을 유지한다.
설치 관계 AEX 선취 뒤 revision/policy를 검증하며 회수 이동 감사 또는 move/false receipt가 있으면
같은 지점 no-op도 포함해 downgrade DDL 전 거부한다. 일반 회수 이력은 표현 가능한17 왕복을 막지 않는다.
원래0001–0017·정책2/target14와 parent17/current18의 실제 runtime 경계·원래17 receipt의18 replay를 검증했다.

## 최종 독립 실행

| 검사 | 실제 결과 |
| --- | --- |
| `bash check.sh fast` | Ruff/format/mypy PASS, 비PG197 PASS, Import Linter8 kept |
| 선정 PostgreSQL | `--require-postgres -x`, 단일 새 pytest 실행104 PASS, 718.018초 |
| 실제 HTTPS/native | 위104에 포함된1사례, Chromium151.0.7922.34, 정확한 manifest54항목 모두 literal true |
| 실패/error/skip/xfail/xpass·선정 누락 | 모두0 |
| 수집/fixture 계획 | 전체925=비PG197+PG728, 선정104 일치. 실행0/필수PG gate exit1 세 건은 메타데이터 |

fast run은 `auto-5b7c2eabfc3742b2a04289f1d23b6340`, 선정PG/native는 같은
`auto-e6b7b130a86f434cab4833db830b5848`이다. 개발자 점수나 과거 통과를 재사용/합산하지 않았다.
전체PG728 중624개는 수집/계획만 했으며 실행하지 않았다. 실제 설치 브라우저 한 종류의 로컬 검사다.
원래 실행 환경을 사용했고 추가 DNS/hosts 우회는 없었다. 시스템/개인 신뢰·hosts/resolver도 전후 동일하다.
Starlette TestClient HTTPX 및 AnyIO BlockingPortal 의존 경고2개는 그대로 관찰했으며 숨기거나 의존성을 변경하지 않았다.

## 초기 개발 검사 보완

개발 중 초기 실패6회를 최종 성공으로 바꾸지 않고 최소 근거에 원인/교정을 기록했다.
기존404/500 응답·positive version HTTP DTO의422를 새 테스트가 다르게 기대한 경우는 기존 계약에 맞췄다.
grant flag만 변조하면 원래 단조 version DB guard에서503으로 거부되므로 version도 전진시켜 최종 typed proof의409/전체 rollback까지 검증했다.
활성 앱의 ProcessGuard로 CLI/구 runtime 검사에 잘못 실패·통과할 수 있었던 fixture는 앱 lifespan을 정상 종료한 뒤 검사하도록 수정했다.
초기 설정 재발급의 회수 grant404도 유지하고 새 지점 BA 재부여→dual-version 명시 재발급→옛 링크 거부/새 링크 완료를 검증했다.

개발 선정103 통과 뒤 Home/초기 보상 snapshot/C2 보존 단언을 보강하고 관련2개를 최종 소스로 재검증했다.
두 node는 선정103과 중복이며105개로 합산하지 않는다. 최종 인수 성적은 이후의 새 독립197/104뿐이다.
개발자·독립 tester·설계자·전담 커밋 담당자의 정적 검토에서 남은 구체 결함/추가 Product 결정은 없었다.

## 소스와 자원 경계

독립 동결 전체289개/Backend183개가 전후 동일했고 원래 보호31개·HEAD/index/branch/main refs 불변을 대조했다.
Backend raw map SHA-256은 `5b18cd6d14e61e059041d640e46d56dbb916af017434e3a2f9cca50b18b38e8d`다.
설계자는 개별104 판정·원래 선정 목록·실제 JUnit104·native54 exact keyset/literal true/동일 run-id를 직접 대조했다.
인수 후 설계자 변경은 Architecture README/게이트/설계 상태 및 새 결과/최소 근거 문서5개뿐이며 Backend bytes는 유지한다.

완료된 개발13개와 독립5개 실행은 기존 소유권/pytest fixture로 자기 프로세스/schema/자동 폴더를 정리했고 실제 경로 부재를 대조했다.
검토용 QA 원본 로그/중복 결과는 인수·커밋 검토 종료 후 정리하며 최소 판정만 유지한다. 공유 Compose/corpus·원본 환경은 보존한다.
추가 QA 관리 도구·framework/dependency 도입, 원본 DB 적용·운영 배포·전체PG/다른 브라우저·모바일·PT/정산 인수는 없다.
다른 Product OPEN/전역 PROPOSED와 후속 Trainer Home 이동의 대상 상태 결정을 이번 승인으로 대체하지 않는다.
