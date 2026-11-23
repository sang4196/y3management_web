# WORKFORCE-005 실행 결과 — 미래 일반 기본급 일정

2026-11-24 **설계자 로컬 인수 PASS — 재동결본의 새 독립 선정 검사**.
Parent `34ac47eb4324e57175b3663dc2457d6d122392d6`, branch `codex/workforce-base-schedule`.
[WF5-1](../product/product-decisions.md#review-20261123-future-base-cancellation)와 [제한 계약](workforce-005-base-schedule-design.md)을 구현했다.
개별 판정·소스 SHA·브라우저 원시 조건/실행 출처·초기 교정은 [최소 근거](workforce-005-base-schedule-review.json)에 있다.

## 구현·설계자 검토

현재 Master는 자기 Organization, Branch Admin은 현재 Trainer Home 범위에서 독립 관리자 본인 포함 미래 일반 기본급 일정을 등록·금액 수정·취소한다.
초기 필수 anchor는 불변이며, 그 이전 시작월 생성은 최소 범위에서 거부하고 같은월 overlay는 허용한다. 같은 금액의 새 시작월도 일정 경계로 남긴다.
같은 logical change의 동일 금액 수정만 no-op다. 취소는 전체 logical change를 무효화하고 옛 수정 금액을 부활시키지 않는다.
빈 시작월에 명시적 새 등록은 새 UUID다. 이전 유효 설정은 다음 남은 변경까지 계속하며0원은 미설정과 다르다.

기준월 조회는 현재 계획에 따른 일반 설정값이다. anchor 전은 없음으로 표시하고 실제 수동 지정/확정 정산 적용액이나 당시 고용·소속을 추정하지 않는다.
별도 Base ledger/revision을 사용해 Trainer/Home/state·Rate/Fixed compensation version·원래 Base/초기 snapshot·IAM/원본 링크를 유지한다.
목록·이력은 ledger/server business month와 해당 기준월 token으로 페이지 혼합을 막는다. 이력은 원래 초기 감사와 새 typed Base 감사로 분리 조회한다.
과거 작성자/Home는 현재 권한을 유지하지 않으며 Operator/Trainer 단독과 타 조직·옛 지점은 값/이력/receipt/변경 접근이 차단된다.

감사 뒤 원래 Actor 검증이 실제 사용한 DB clock을 public 반환한다. 기존 인증/기한/401/touch 동작은 그대로다.
Base는 같은 clock으로 한국 월의 미래 자격을 판단하고 월이 지났으면409로 전체 rollback한다. 성공 receipt는 동일 validated_at으로 봉인한다.
성공 활동 시각과 validated_at이 같고, 실패하면 그 활동 갱신도 되돌아감을 확인했다. clock을 물리 PostgreSQL commit timestamp로 부르지 않는다.
정확 replay는 월이 바뀌어도 현재 권한/원래 기한으로 원래 결과만 대사하며 새 취소를 다시 실행하지 않는다.

새0021은 정상20의 RF 변경/version>1·Home/state/기존 행을 보존하며 초기 Base 관계만 검증한다. 0020의 currentRF==initial 조건을 복제하지 않았다.
업무 없는 초기1 중복 metadata만 제거할 수 있고 모든 Base receipt(no-op 포함)/일정/감사·ledger 누락/모순은 파괴 downgrade 전 거부한다.
불변 change 시작월을 receipt FK에 결속했다. valid edit의 before 금액만 변조해 CHECK/core FK가 유효한 상태에서도
별도 deferred before FK가 SET CONSTRAINTS 및 실제 commit에서23503/정확한 제약명으로 거부하고 전체 행을 복원함을 검증했다.
감사 없는 no-op의 시작월만 변조한 경우에도 source FK 자체가 거부한다. 실제21→20→19/18 guard 준비를 사용하고 원래 이력을 지워 우회하지 않았다.

화면은 lazy panel과 고정 선택 snapshot/Actor·generation을 사용한다. 취소 확인은 시작월/예정금액을 함께 제시한다.
계정 전환 뒤 금융 입력 초안이 남던 경로를 지웠고 이전 결과도 중앙 정리한다. 기존 catch가 결과 문구를 이미 대체하므로 과거 결과 유출이 입증됐다고 확대하지 않는다.
실제 늦은 초기 응답보다 새 UI를 먼저 게시하고, 늦은 응답의 최종 owner 조회 완료 뒤에도 최신 표시가 유지됨을 확인했다.
POST commit 응답 유실→같은 UUID 대사/중복 없음, 원래 receipt→실제 추가 저장→fresh 현재 표시를 별도 검증했다.

## 새 독립 실행

| 검사 | 실제 결과 |
| --- | --- |
| `bash check.sh fast` | 비PG211 PASS, Ruff/format/mypy PASS, Import Linter8 kept |
| 선정 PostgreSQL | 새 단일 실행62 PASS, `--require-postgres -x`, 462.02초 |
| 기존 workforce native | 위62에 포함, manifest54 모두 literal true |
| Base 기본 native | 위62에 포함, 별도 manifest15 모두 literal true |
| Base 경합 native | 위62에 포함, 별도 manifest8 모두 literal true |
| 실패/error/skip/xfail/xpass·선정 누락 | 모두0 |
| Collection | 전체1020=비PG211+PG809. 나머지PG747은 미실행 |

fast `auto-036333dac2034d29bdf9046c728dc766`, PG/세 native `auto-0ab12d5dbf3d47e1b29fee420d84cc9d`.
실제 설치 Chromium151.0.7922.34와 각 manifest exact keyset/동일 run-id를 설계자가 직접 대조했다. 조건 수는 별도 사례 수이며 중복을 합산한 단일 manifest 성적이 아니다.
기존 native fixture는 profile/manifest/evidence selector만 한정 확장했고 원래 TLS/NSS/bubblewrap/소유권/90초 cap/정리 body는 보존했다.
collection-only exit1·fixture 보고 process0/QA summary1은 실행0의 메타데이터다. 개발/이전 성공을 독립 성적에 차용하거나 합산하지 않았다.
기존 Starlette/httpx·AnyIO 경고2개는 유지했다.

## 시간·실패·정리의 검증 경계

2090 반환값만 바꾼 초기 검사는 Base proof 출력 fault injection일 뿐이다. 추가 검사는 소유 fixture의 원래 Actor 기한을 경계 주위에 맞추고
원본 confirm_actor 내부 IAM.now 포트에 같은 시각을 주입해 한국월 전/정각/후의200/409·동일 검증 clock/전체 rollback을 확인했다.
실제 PostgreSQL 고정 timestamptz의 Asia/Seoul 변환, 실제 Audit 대기 중 idle/absolute401, 서로 다른 PID의 global gate/CAS는 별개로 실행했다.
실제 시스템 시계 변경이나 실제 월말 경과를 시험했다고 주장하지 않는다.

새 테스트의400↔422/감사 예외 기대값, 단일2.2초 대기가 원래 statement timeout을 넘긴 준비 오류, original20 runtime 모드 누락을 바로잡았다.
인라인JS regex 줄 분리의 실제 문법 결함을 수정했다. 기존18 기대값3개/actual18 준비2개의 호환성 검사도 현재21 기대와 실제 inverse caller로 교정했다.
원래 migrations/guards/common helpers·timeout을 약화하지 않았다. 첫 실패를 성공으로 바꾸지 않고 최소 근거에 원인과 fresh 재검사를 남겼다.
추가로 두 노드만 한정 재실행해 before/source FK와 늦은 owner 응답 인과 대기를 보완한 뒤 최종 동결했다.

독립 전후 전체316/Backend201 raw SHA·보호35·HEAD/index/refs47·신뢰/hosts/resolver/NSS가 동일했다.
설계자는 각62 판정·세 native 원시 조건과 소유 process/schema/auto 폴더 부재를 대조했다. 인수 후 변경은 Architecture 문서뿐이며 Backend bytes는 불변이다.
공유 Compose/원본 데이터·현재 도구는 보존하며, 완료된 집계 QA 로그는 커밋 검토 후 최소 결론만 유지한다.
현재/과거 일반 기본급 편집·월별 수동/확정 정정·실제 정산·PT/역사 resolver·다른 플랫폼·원본 DB/운영 배포는 인수 범위 밖이다.
다른 Product OPEN/전역 PROPOSED를 유지한다. 다음 상품 입력/최초 판매 상태 질문은 별도 미결정으로 이번 구현/커밋과 분리한다.
