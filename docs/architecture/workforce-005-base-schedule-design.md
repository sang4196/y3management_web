# WORKFORCE-005 — 미래 일반 기본급 일정 편집

Status: **LOCAL ARCHITECT ACCEPTANCE PASS — FROZEN SELECTED VERIFICATION** (2026-11-24).
[결과](workforce-005-base-schedule-results.md) / [최소 근거](workforce-005-base-schedule-review.json).
Parent `34ac47eb4324e57175b3663dc2457d6d122392d6`, branch `codex/workforce-base-schedule`.
[WF5-1](../product/product-decisions.md#review-20261123-future-base-cancellation), BR-PAY-010/014/023, AA1/AA2와 W0/W1/WF3/WF4를 따른다.
새 Product 질문 없이 최소 미래 편집부터 기술 진입을 검토한다. 구현은 개발자·독립 tester 사전검토 후 설계자가 허용한다.
전역 모듈/다른 OPEN/운영 게이트는 유지한다.

## 최소 범위·현재 권한

기준월 일반 Base 계획 조회, 아직 미적용인 미래 변경의 등록·금액 수정·취소, 현재 계획 목록과 초기 포함 이력을 구현한다.
현재 Master는 자기 Organization, Branch Admin은 각 요청 시점 Trainer 현재 Home 범위에서 독립 관리자 본인 포함 허용한다.
과거 작성자/Home/수업 지점만으로 권한을 유지하지 않으며 Operator/Trainer 단독은 본인 값도 읽거나 변경하지 못한다.
Trainer/계정 상태·회수/원본 링크·독립 역할/Scope를 변경하지 않는다. 비활성 Home에서도 기존 현재 관리 Scope를 따른다.
일반 설정은 별도 승인/새 필수 사유 없이 저장하며 필수 전후값/Actor/Role/Branch Context/대상 당시 Home/시점 감사를 남긴다.
월별 수동 지정/확정 오류 정정의 사유 필수를 일반 일정 편집에 전파하지 않는다.

‘미래’는 한국 업무 달력월보다 시작 월이 큰 경우다. 최초 필수 anchor 자체를 취소하거나 시작 월을 앞당겨 AA1 이전 월을 메우지 않는다. 이 최소 create는 start_month>=immutable initial anchor start_month를 명시 검사하며, future라도 그보다 이른 시작월은409다. equality overlay는 허용한다.
현재월/미확정 과거월 일반 설정 변경은 이미 승인된 후속 범위이며 이번 미래 편집 제한을 영구 Product 금지로 바꾸지 않는다.
실제 Settlement의 수동/확정 fact가 없는 상태를 미입력0/미확정이라고 추정하지 않는다. 월별 수동/확정 해제·정정·재확정과 실제
정산 적용액/합계/송금·PT 지급/역사 고용·소속 resolver는 이번 범위 밖이다.

금액은 W0/WF4의 정확한0+ 정수원 문자열 codec/1024자리 표현 범위를 재사용한다. 누락/null/소수/음수/임의0 대체·반올림 금지다.
시작/기준월은0001-01~9999-12 codec이며 미래 기간의 업무상 N개월 상한·종료월·유지할 월목록/매월 재등록을 도입하지 않는다.
원래 초기 시작 월이 실제 등록 월보다 이른 값도 원래 사실로 보존한다. 계획 조회는 당시 고용·정산 자격을 증명하지 않는다.

## 일정 의미·기준월 조회

원래 initial snapshot/initial_compensation 감사의 금액·시작월·등록 사실을 취소불가 초기 anchor로 참조한다.
일반 일정의 시작월 이전은 ‘해당 일반 설정 없음’으로 반환하며0원으로 만들지 않는다. AA1의 별도 월 수동 경로 필요를 표시한다.
기준월 projection은 현재 유효 계획에서 시작월<=기준월인 가장 늦은 변경을 택한다. 같은 시작월의 noninitial overlay가 초기 anchor보다 우선한다.
이는 현재 계획을 기준으로 한 일반 설정값이며 과거 당시 알려졌던 값·월별 수동 지정액·확정 정산 적용액이 아니다.
응답은 기준월/서버 업무월/일반값 존재 여부·선택 source 시작월/금액/change UUID/revision/Base ledger version을 구분한다.

noninitial 유효 변경은 Trainer/시작월당 하나다. 같은월 새 create는409이며 기존 change의 명시적 edit/revision CAS를 사용한다.
edit는 같은 logical change의 금액만 바꾸고 원본과 수정 이력을 append한다. 시작월 이동 UI/자동 cancel+create는 포함하지 않는다.
새 시작월 create는 이전과 금액이 같아도 독립 일정 경계/실제 변경이다. 나중에 사이에 일정을 넣어도 그 다음 경계가 유지돼야 한다.
같은 logical change에 같은 금액 edit만 no-op로 처리한다. 새로운 start boundary를 금액 동일 no-op로 제거하지 않는다.

취소는 해당 미래 logical change 전체를 무효화하며 이전 edit 금액을 자동 부활시키지 않는다. 다른 남은 일정은 그대로다.
이전 유효 설정이 다음 남은 변경까지 계속한다. 초기월 overlay 취소는 원래 anchor를 삭제하지 않고 anchor로 복귀한다.
새 UUID로 이미 취소된 대상을 다시 취소하면409, 같은 원래 UUID의 정확 replay는 현재 권한으로 원래 성공 결과만 대사한다.
월이 바뀌었다고 과거 성공 취소를 되돌리거나 replay를 새 취소처럼 다시 판정하지 않는다. 취소로 빈 시작월에 나중에 명시적 새 create를 하면 새 UUID/revision1의 새 사실이다. 취소된 logical change를 편집/부활시키지 않는다.

## 버전·공개 계약·UI

Base ledger 전용 positive monotonic version(초기1)과 logical change revision을 둔다.
Trainer/Home/state version 및 WF004 Rate/Fixed compensation_version과 분리한다. Base 편집은 그것들과 IAM epoch/세션을 바꾸지 않는다.
명령은 operation UUID/expected_base_ledger_version/expected_trainer_version, edit/cancel은 target change revision을 받는다.
create는 시작월/금액, edit는 금액, cancel은 대상만 명시한다. 누락을 유지/0원으로 암묵 처리하지 않는다.
Actor/Trainer/종류/대상/정확 입력/기대 version을 canonical fingerprint에 결속한다. 신규 route는 필수 UUID X-Y3-Expected-Actor와 현재 Caller를 대조한다.
권한 근거는 서버 Caller/현재 Home이며 클라이언트 role/org/branch가 아니다. 쓰기는 CSRF를 요구한다.

후보 route는 /admin/trainers/{id}/base-schedule(기준월/현재 계획), /base-schedule/changes(create),
/base-schedule/changes/{change}(명시 edit/cancel 하위 명령), /base-schedule-history,
/admin/trainer-base-operations/{uuid}(receipt)다. 기존 일반 Trainer/계정 DTO에 값을 섞지 않는다.
목록 offset/limit은 최초 응답의 ledger version/기준월/server_business_month를 snapshot identity로 유지한다. 후속 페이지의 expected_base_ledger_version/expected_server_business_month와 계획 기준월이 달라지면409/재조회한다. 이력 페이지에도 ledger/business month token을 유지하되 기준월 projection은 없다. ledger가 그대로여도 월이 바뀌면 새 전체 조회로 eligibility를 다시 게시한다.
취소로 빠진 항목이나 중간 삽입을 서로 다른 version 페이지로 섞지 않는다. 이력은 ledger version ASC의 immutable 초기1+실제 변경이다.
초기 before 없음과 명시0을 구분한다. Audit 소유 typed read/append를 사용하며 WF004 RF history의 자체 version/total 계약을 바꾸지 않는다.

receipt는 원래 Actor인 현재 허용 관리자/현재 Home로 인가하고 원래 확정 결과와 current 계획을 구분한다.
같은 UUID/다른 Actor·payload는 비노출/충돌이다. 새 stale version은 같은 금액이어도 충돌이며 일치 replay는 현재 CAS 재적용 없이 원래 사실만 반환한다.
no-op edit/replay/조회는 새 audit/이력/ledger version/활동 시각을 만들지 않는다. 새로운 일정/수정/취소만 정상 성공 touch다.
ACK 불명은 원래 UUID로 대사하며 자동 새 명령/보상 rollback은 없다. 과거 결과가 최신 계획을 복구하지 않는다.

기존 Trainer 관리 화면/native runner를 확장한다. 자신의 읽은 Home/Trainer version·ledger version/change revision과 금액/string을
고정 선택 snapshot으로 유지한다. Actor/선택 generation·중복 제출/낡은 응답·다른 패널 변경을 차단한다.
서버 업무월과 미래 eligibility를 표시하며 기기 시간을 인가 근거로 쓰지 않는다. 기준월 계획값/초기값/정산 적용액을 혼동하지 않게 표기한다.
취소는 사용자가 대상 시작월/금액을 확인하는 명시 동작으로 실행한다. 일반 확인 UI이지 추가 관리자 승인/필수 사유 업무가 아니다.
대사 응답과 fresh 조회는 시점이 다르므로 성공 게시된 snapshot을 현재로 쓰거나 ‘조회 당시’로 표시하며 거부된 fresh 뒤 성공 표시를 하지 않는다.
긴 정수원을 JS Number로 바꾸지 않고 기존 responsive wrapping/input 규칙을 유지한다.

## 트랜잭션·월 경계

현재 UoW/공개 ports를 확장한다. installation→Actor 계정/AuthSessions→현재 Branch SHARE→Trainer UPDATE→Base ledger/change 순서를 따른다.
초기/현재 Home와 독립 version을 잠금 후 다시 확인한다. Home/권한 변경·동시 ledger 수정은 실제 global gate/PID 대기와 CAS로 검증한다.
대상 IAM account/credentials를 수정하거나 뒤늦게 추가 잠그지 않는다. 다른 모듈 private Repo/ORM 직접 접근·개별 commit은 추가하지 않는다.
Workforce anchor는 자기 initial snapshot/registration operation을 참조한다. W0 create가 원래 초기 Audit보다 먼저 쓰는 순서를 유지하고 Audit private SQL/즉시 audit-ID FK를 요구하지 않는다. 새 anchor/초기 감사는 같은 UoW에서 완결하고 실패 시 모두 rollback한다.
계획 current head/ledger version·receipt·typed Audit는 하나의 UoW로 성공/rollback한다. Actor 권한 축소/감사 실패/기한 만료 시 전부 rollback한다.

월은 DB 서버 clock과 Asia/Seoul 달력으로 판정한다. 미래 change의 eligibility는 첫 조회가 아니라 감사 뒤 최종 검증에도 확인한다.
월 시작 순간을 넘겨 적용된 change를 새 취소/수정으로 확정하지 않는다. 신규 same-value edit도 최종 미래자격을 확인한다.
기존 public TrainerRolesPort.confirm_actor가 이미 Actor 원래 기한·정책 검증에 사용한 DB now를 반환하도록 datetime 반환 계약만 확장한다.
기존 호출자는 반환을 무시하며 기존 auth/401·deadline/touch 동작은 바꾸지 않는다. IAM에 기본급 업무 월 정책을 넣지 않는다.
Base application은 감사 뒤 이 proof clock으로 Asia/Seoul 업무월/target 미래 자격을 검증하고 월 자격 실패는409 conflict로 rollback한다.
원래 idle/absolute 만료는 기존401이며 touch로 연장해 통과시키지 않는다. 같은 public proof clock을 새 receipt의 validated_at/business_month 근거로 봉인하고
최종 result는 봉인 후 값을 반환한다. operation/Audit의 recorded_at과 검증 clock은 구분하며 Audit private SQL을 다른 모듈에서 수정하지 않는다.
이후 receipt 봉인 SQL까지 잠금/UoW를 유지한다. rollback은 proof에서 이미 수행한 성공 touch도 되돌린다. replay는 과거 validated_at을 보존하고 새 미래 판정을 실행하지 않는다.
기록시각/선형화 clock을 물리PG commit timestamp라고 하지 않는다.
최종 검증 이후 commit 전 짧은 구간의 visibility는 UoW/잠금으로 분리하며 server clock 경계 계약을 실제 테스트로 고정한다.
월이 바뀌어도 이미 완료된 원래 receipt의 정확 replay는 새 취소를 실행하지 않는다.

## 0021·기원·원본 보존

새0021만 추가하고 원래0001–0020/ADR/deps/lock/common harness/WF3·WF4 helper를 보존한다.
원래20 자료는 정상 Rate/Fixed 변경과 compensation_version>1, Home/state 이력이 있을 수 있다.
0020 originals()의 currentRateFixed==initial 조건을 복제해 정상 RF 변경 자료를 거부하지 않는다.
원래 등록 operation/creator·initial snapshot·등록/initial_compensation 감사의 관계와 초기 Base/시작월만 정확히 검증한다.
현재 RF는 원래20이 소유한 사실로 보존하며 원래 초기 Rate/Fixed 감사는 초기 snapshot과만 대조한다.
별도의 sampled audit clock을 snapshot/등록 clock과 강제로 같게 만들지 않고 initial Base 이력은 원래 audit 시각을 사용한다.
기존 Base 열/초기 snapshot을 미래 계획값으로 덮지 않는다. 새 Base ledger와 noninitial change/revision이 계획을 소유한다.

installation AEX 선취 후 정확20↔21 head/policy2/target14·원본 관계를 DDL 전 검증한다.
같은Org/Trainer/Actor/현재 당시Home·종류/target change/시작월/전후금액·positive version/revision/changed flags/시각을 typed CHECK/FK로 결속한다.
nullable Actor Branch는 Master NULL/BA targetHome으로 양쪽에서 도출하고 핵심 composite FK identity를 NULL로 건너뛰지 못하게 한다.
취소된 change의 원래 planned_amount는 명시적 inactive 상태와 함께 보존할 수 있다. 이것을 취소 후 유효 지급액으로 부르지 않으며 projection은 다른 남은 경계를 고른다. create의 before 없음도 가짜0원으로 만들지 않는다. 항상 nonnull인 core/post identity FK와 create시NULL/edit-cancel시필수인 별도 before FK 등
유효한 구조를 사용해 NULL/UNKNOWN 우회를 막는다. per-command typed 구조도 허용한다. 한정된 모델을 불필요한 일반 event system으로 만들지 않는다.

모든 새 Base operation(no-op 포함)/create-edit-cancel 이력·감사/ledger version>1은 파괴 downgrade 전에 정보 손실을 차단한다.
event 없이 남은 noninitial change/revision도 정보 손실 대상으로 거부한다. Trainer↔ledger/anchor의 누락/모순을 FULL-join 등으로 검증한다. 업무가 없는 초기1 중복 metadata만 원래 anchor 사실이 정확히 일치할 때 제거할 수 있다. 원래 RF/Home/state 사실은 양방향 보존한다.
새 WF5-local helper는 실제21 inverse+stamp20 후 기존20 helper에 위임하고 요청 target에 도달하면 즉시 멈춘다.
원래20 RF guard/19 Home guard는 각 실제 head에서 원래 이유로 검증하며 새 이력을 삭제하거나 marker만 바꿔 우회하지 않는다.
parent20 archive로 정상 RF 변경 자료를 만들고21 진입 후 전체 기존 행 보존/역변환 및 current21/parent20 상호head 거부를 검사한다.

## 검증·완료

개발자·독립 tester 사전검토→제한 구현→소스 동결→새 독립 fast/선정PG/native→설계자 인수→전담 한글 상세 커밋/일반 feature push다.
현재Home/겸임 본인/OperatorTrainer 비노출, 최초anchor/초기DTO/원래 RF·IAM·독립역할 보존, 명시0/큰정수/시작월/기준월 없음을 검증한다.
같은월 충돌/edit/noop·같은금액 새경계·취소후앞뒤projection/anchor overlay·원래이력/ActorBoundreceipt/ACK·낡은UI를 선정한다.
실제서버 한국월 경계 전후와 처리중경계통과/원래 Actor idle·absolute/감사 rollback·실제동시CAS를 검증하고 global gate를 우회하지 않는다.
실제20 RF변경 source→21/기원반례/원본행보존/정보손실guard/이전runtime을 검사한다. 전체PG×상태곱은 무조건 재실행하지 않는다.
기존 native fixture/runner의 feature profile을 확장해 Base의 짧은 mode/별도 manifest와 기존 workforce54 회귀를 분리할 수 있다. test_iam_browser.py의 mode/manifest/config 선택만 한정 확장하며 기존 신뢰/소유권/timeout/cleanup 계약·원래모드 동작을 보존한다. 새 lifecycle/tool/framework를 만들지 않는다. 실제clock/값/취소·현재/원래결과/Actor/모바일을 각 case exact keyset/literaltrue/같은run로 기록하며 기존90초 cap을 기능 추가에 대한 막연한 처방으로 늘리지 않는다.
자기 process/schema/auto 폴더는 기존 도구로 정리하고 최소 근거만 유지한다. 새 수명주기 tool/framework/dependency·원본 DB/배포는 없다.
