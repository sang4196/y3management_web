# WORKFORCE-003 실행 결과 — Trainer 소속 지점 변경

2026-11-23 **설계자 로컬 인수 PASS — 최종 동결본의 새 독립 선정 검사**.
Parent `e66a4a1291207f85dd6407427945ad16090bdc0a`, branch `codex/workforce-trainer-home`.
[WF3-1](../product/product-decisions.md#review-20261122-trainer-home-states)과 [제한 계약](workforce-003-trainer-home-design.md)을 구현했다.
개별 판정·테스트 소스 SHA·최소 수정 근거는 [인수 근거](workforce-003-trainer-home-review.json)에 있다.

## 구현·검토

같은 조직의 Master는 모든 Trainer/계정/grant 상태와 계정 미발급 상태에서 Home을 활성 지점으로 즉시 변경한다.
업무/계정/회수 상태·독립 관리자/Operator Scope·보상·기존 설정/reset/recovery 링크·과거 사실을 보존한다.
Home만 이동해 로그인 전체를 철회하거나 역할을 부여하지 않는다. 이전 지점 관리자는 이후 현재 Home 인가에서 제외된다.
현재 Home과 W1 공유 version·변경 이력·Actor 결속 receipt·typed Audit를 한 UoW로 저장하며 실패 시 함께 rollback한다.
no-op/replay는 새 이력·감사·version·Actor 활동 갱신을 만들지 않는다. 원래 결과와 현재 상태를 구분한다.

기존 관리 화면에 지점 이름 선택·명시 변경·작업 번호 대사를 연결했다. 오래된 Home 조회 응답이 최신 공유 version과
섞여 잘못 저장될 수 있던 경로를 독립 Home/version 선택 snapshot으로 수정하고 실제 지연 응답으로 검증했다.
계정 연결의 사전 조회와 본 처리 사이 경합은 충돌 후 재조회하게 한다. 기존 installation 전역 잠금이 본 UoW를 이미
직렬화하므로 본 UoW 내부의 동시 발급 취약점이 입증됐다고 주장하지 않는다. 잠금 후/최종 binding 확인은 방어 보강이다.

새0019는 기존18의 현재 Home을 migration 시점 legacy_observation으로 보존하며 과거 연속 소속을 꾸며내지 않는다.
새 등록만 실제 registered origin을 갖는다. 원래 등록 snapshot/operation/audit의 identity를 DDL 전 검증한다.
Home receipt는 no-op도 downgrade를 막으며, registered origin은 원래 불변 사실과 정확히 같은 중복 metadata만 제거한다.
실제18↔19 및 이전 runtime 거부·하위 lossguard를 검증했고 원래0001–0018/의존성/공통 harness를 보존했다.

## 독립 실행

| 검사 | 실제 결과 |
| --- | --- |
| `bash check.sh fast` | 비PG197 PASS, Ruff/format/mypy PASS, Import Linter8 kept |
| 선정 PostgreSQL | `--require-postgres -x`, 새 단일 실행64 PASS, 453.8초 |
| 실제 HTTPS/native | 위64에 포함된1사례, Chromium151.0.7922.34, manifest40항목 모두 literal true |
| 실패/error/skip/xfail/선정 누락 | 모두0 |
| Collection | 전체956=비PG197+PG759. 미실행 PG695는 통과 주장 없음 |

fast `auto-6bdb1bae34804897bf9062d7ad51ef8a`, PG/native `auto-a7bd29463e304e43aa4a49ab94d23a85`.
Collection-only exit1은 필수PG runner가 실행0을 거부한 메타데이터이며 실행 실패나 성공으로 바꾸지 않았다.
개발 중 fixture/기존 계약 기대값·실제 global lock barrier·하위 revision 준비·native 동기화 실패와 교정을 최소 근거에 남겼다.
독립 점수에 개발/과거 점수를 합산하지 않았다. 기존 Starlette/httpx·AnyIO 경고2개는 그대로 유지했다.

## 보존·정리·한계

독립 실행 전후 Backend187개 raw SHA·보호25개·HEAD/index·refs43개·신뢰/hosts가 동일했다.
설계자는 정확한64개 개별 판정과 native40 keyset/boolean/동일 run-id, 소유 auto 폴더 부재를 직접 확인했다.
인수 후 Root는 새0019 SQL 문자열의 후행 공백4개만 제거했다. 정규화 AST/SQL token 동등성과 전후 SHA를
별도로 기록했으며 런타임 성적은 공백 제거 전 동결 bytes 기준이다. 이 의미 없는 포맷 변경으로 전체 검사를 반복하지 않았다.
그 외 인수 변경은 Architecture 문서뿐이다. 전담 커밋 검토에서 신규 미추적 파일까지 staged diff-check한다.

개발·독립 실행은 기존 fixture/정리 도구로 자기 프로세스/schema/자동 폴더를 종료·정리했다.
공유 Compose PostgreSQL/원본 환경·기존 도구는 보존한다. 완료된 집계 QA 원본 로그는 커밋 검토 후 최소 결론만 유지한다.
원본 DB 적용·운영 배포·전체PG/다른 브라우저·실물 모바일·Member/PT/정산/과거 Home 정정 인수는 아니다.
다른 Product OPEN/전역 모듈 PROPOSED·운영 게이트를 유지한다.
