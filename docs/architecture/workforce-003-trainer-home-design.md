# WORKFORCE-003 — Trainer 소속 지점 변경

Status: **LOCAL ARCHITECT ACCEPTANCE PASS — SELECTED VERIFICATION** (2026-11-23).
[실행 결과](workforce-003-trainer-home-results.md) / [최소 근거](workforce-003-trainer-home-review.json).
Parent `e66a4a1291207f85dd6407427945ad16090bdc0a`, branch `codex/workforce-trainer-home`.
[WF3-1](../product/product-decisions.md#review-20261122-trainer-home-states), BR-OPS-013/G5와
[W1 계약](workforce-002-trainer-state-design.md), 기존 IAM-018/비밀번호 전용 정책을 따른다.
이 계약의 제한 구현만 허용하며 전역 모듈 PROPOSED/다른 Product OPEN/원본 DB·운영 게이트는 유지한다.

## 범위·인가·보존

같은 조직의 현재 Master만 기존 Trainer의 Home을 활성 Branch로 변경한다. 모든 Trainer/계정/grant 상태와
계정 미발급을 허용하며 비활성 출발지도 허용한다. 새 필수 사유·미래 예약/소급 날짜·계정/grant/보상 입력은 없다.
Trainer.active·계정 상태/restore/reset/recovery·독립 관리 Scope/Operator 업무 Branch·계정 연결과 grant epoch·
보상값/초기 snapshot·등록/상태/IAM 이력은 그대로다. 자동 계정 생성/재활성/차단 해제/재부여/보상 재계산은 없다.
현재 Home과 같은 W1 공유 Trainer row_version만 실제 변경 시 +1한다. 담당/지원/PT/정산 및 과거 Home 정정은 미구현 범위다.

이동 저장 이후 시작하는 기존 Home 기반 목록·직접 조회·계정 발급/재발급·역할/상태 관리 등은 새 현재 Home으로
인가한다. 이전 소속/발급자/receipt의 사실은 권한을 유지하지 않는다. BA의 출발/도착/본인·Operator/Trainer 겸임도
Master 권한 없이 Home 이동을 할 수 없다. 타 조직/잘못된 대상은 기존 비노출 원칙을 따른다.

## 공개 계약·명령 결과

기존 Trainer 관리 화면과 공개 계약을 확장한다. 후보 경로는 `POST /api/v1/admin/trainers/{id}/home`,
`GET /api/v1/admin/trainer-home-operations/{operation_id}`다. 새 Home 경로에는 기존 Operator 관리 방식의
필수 UUID `X-Y3-Expected-Actor` 전제를 적용한다. 인증된 Caller.account_id와 대조하며 이 헤더는 권한 근거가 아니다.
클라이언트는 조회/쓰기/대사 전후 현재 Actor·선택 generation을 확인하고 pending UUID를 원래 Actor/Trainer에 묶는다.
공유 기존 조회 경로의 권한을 넓히거나 일반 API 전부에 새 헤더 의무를 추가하지 않는다.

입력은 operation UUID·destination_home_branch_id·expected_trainer_version이다. 현재 Master·CSRF·원래 정책/기한·
Org/Branch 및 현재 Trainer 사실을 검증한다. canonical fingerprint는 trainer/request/원래 Actor에 결속한다.
같은 operation/다른 payload 또는 Actor는 충돌/비노출 처리하고 receipt도 원래 Actor인 현재 Master/동일 Org로 제한한다.
원래 확정 전후 Home/버전/changed/기록 시각과 current_state를 구분한다. 과거 결과로 현재 Home을 복구하지 않는다.
새 요청의 stale expected version은 같은 목적지여도 충돌이다. 일치 replay는 현재 인가/기한 검증 뒤 원래 결과와 현재 상태만 반환한다.

같은 Home no-op는 버전/이력/감사·원본/세션을 변경하지 않는다. 비활성 현재 Branch의 같은 지점 no-op도 새 배정이 아니다.
필요한 최초 receipt만 기록한다. no-op/replay로 Actor 활동 시각을 늘리지 않으며 실제 성공만 정상 최종 touch 규칙을 적용한다.
ACK 불명은 자동 재시도/보상 rollback 없이 동일 UUID의 현재 인가된 결과로 대사한다. receipt가 새 현재 상태를 덮지 않는다.

W0 등록의 동일 원래 payload replay/결과 조회는 기존 `RegistrationResult.trainer`의 현재 ManagedTrainer 의미를 유지한다.
현재 Home으로 인가하고 원래 fingerprint/등록 snapshot·감사 Home/보상은 보존한다. 원래 등록 명령의 Home을 현재로 바꿔
재송신하면 fingerprint 충돌이다. 이동은 새 등록이 아니며 원래 등록 사실을 새 지점 등록처럼 다시 쓰지 않는다.
W1/IAM receipt도 원래 committed 사실과 현재 인가/상태를 구분한다. 이전 Home 관리자는 이력만으로 접근하지 않는다.

## 인증·원본·트랜잭션

Home은 로그인 역할이나 독립 관리자/Operator Scope가 아니다. 이동만으로 로그인 전체를 철회하거나 account/security/
role epoch·계정 상태·설정/reset/recovery 원본을 소비/재발급/연장하지 않는다. 유효 원본의 수신자는 기존 계정/active/grant/
원래 기한과 새 현재 Trainer 사실을 확인해 완료한다. 오래된 발급 관리자는 새 Home의 관리 권한을 얻지 않는다.
진행 중 로그인/설정도 최종 현재 사실로 판단하며 이전 Home 문맥으로 관리 작업을 확정하지 않는다.
Master/Trainer 본인의 Home 이동도 독립 Master 세션을 보존한다. I2의 role epoch+1/self 철회 예외를 복제하지 않는다.

W1의 두 UoW binding hint를 재사용한다. installation → 정렬된 Actor/대상 계정 → 해당 AuthSessions → 필요한 credentials →
ID순 정렬된 출발/목적 Branch SHARE → Trainer UPDATE 순서로 잠근다. 실제 binding/current Home을 다시 확인하고 hint가
바뀌면 재조회가 필요한 충돌로 종료한다. Trainer/Branch 뒤에 대상 계정 잠금을 추가하지 않는다. 같은 대상 Home/상태·발급/역할/
설정/읽기·Branch 상태 경합을 현재 사실과 CAS로 선형화한다. 관련 모듈은 공개 port를 사용하며 private Repo/ORM 공유를 추가하지 않는다.

현재 Home/버전·Home 이력·receipt·typed Audit는 단일 Application UoW에서 함께 확정/rollback한다. 감사 실패/비예상 상태 변화·
Actor 권한/원래 idle/absolute 만료는 전부 rollback한다. authenticate(touch=False)와 snapshot/final confirm의 원래 기한을 유지한다.
감사 뒤 최종 Trainer/Branch/Actor 사실과 DB clock을 확인한다. 계정 미연결은 계정을 생성하지 않고 Actor 쪽 잠금만 사용한다.

## 소속 이력·0019

원래0001–0018/ADR/deps/lock·공통 검증 장치는 불변이다. 새 `0019_workforce_trainer_home`은 Home origins/operations/
transitions/typed audit를 더한다. 기존 상태 origin/transition/등록·보상/IAM 이력과 현재 row_version을 재기준화하지 않는다.
Home/state가 공유 version을 소비하므로 state-only 이력을 연속 숫자로 가정하지 않는다. 기존 역사13 등의 검사는 원래 shape에서 수행한다.

기존18 자료의 새 Home origin은 **migration 시점의 legacy_observation**이다. 관측 이전 Home 연속 구간을 만들지 않는다.
실제 등록 Home/시각은 원래 immutable initial snapshot에 별도 보존한다. 새19 등록은 실제 등록 시각/초기 Home의 registered origin을
같은 UoW에 만든다. 등록 이전·관측 이전의 불명확한 과거를 현재 Home으로 채우지 않는다. 이 기능은 과거 시점 Home 조회/정정을 구현하지 않는다.
정상 이동은 성공 transaction 안의 서버 기록 시각과 전후 version을 보존한다. 이 시각을 물리적 PostgreSQL commit timestamp라고
부르지 않으며 원자적 가시성은 commit 이후다. 이력 순서는 version으로 구분하고 미래 PT의 시간 경계/불명확성은 기존 게이트를 따른다.

Migration은 installation 관계 AEX 선취·정확한18/19 marker와 기존 policy2/target14를 검증한다. Home 없음/잘못된 Org/FK·
필수 원본 모순 등 관측/신규 구조가 정직하게 표현할 수 없는 데이터는 fail closed한다. 기존 snapshot과 현재 Home을 강제로 같게 바꾸지 않는다.
기존 trainer_registered 감사는 Org/trainer/등록 operation/creator/version1/원래 Home이 immutable snapshot·등록 operation과 일치해야 한다.
누락/모순은 CREATE 전 거부한다. 원래 감사 Home을 현재 Home과 같게 고치지 않는다.
같은 조직 FK·원래 Actor/receipt와 Audit의 복합 identity·정확한 전후 Home/positive version/version+1·Master 문맥을 제약한다.
변경 receipt/transition/audit의 flags·Home/version 결속을 CHECK/FK로 보장하고 PostgreSQL NULL/UNKNOWN 우회를 막는다.

19 downgrade는 설치/child 잠금 아래 파괴 DDL 전에 모든 Home receipt(no-op 포함)/transition/audit와
현재 Home/origin 모순 등 새 정보 손실을 거부한다. 업무 이벤트가 없는 migration-owned legacy observation은 안전하게 제거할 수 있다.
registered origin도 trainer/org/Home/실제 등록 시각/version1/등록 UUID의 모든 사실이 원래 immutable snapshot·등록 operation·
trainer_registered 감사의 Home/version과 정확히 일치하는 경우만 중복 metadata의 lossless inverse로 제거할 수 있다.
원래 사실의 누락/불일치는 fail closed하며 새 Home 업무 이력을 지워 내려가지 않는다. 기존 역사 검사를 준비하려고
origin을 먼저 삭제해 guard를 우회하지 않는다. W1만의 합법적 상태 version 증가를 Home 이동이라고 추론하지 않는다.
실제18↔19/전체 행 보존·lossless registered 역변환 및 각 손실 거부/원래 하위 gate를 검증한다.
current19는18에서, parent18은19에서 거부한다. 실제 archive와 실제 DDL을 사용하고 policy2/transition target14·원본 사건/키는 유지한다.

## 검증·완료

개발/독립 사전검토의 요구를 반영했다. 개발자는 backend/새0019/tests/UI/필요 backend README만 쓰고 Root는 Product/Architecture를 쓴다.
실제 collection/fixture graph에서 새기능·변경된 현재/역사 head·인가/보존·현재역할 경합·원래 기한/감사 rollback·no-op/replay·
old receipt/current Home·migration lossguard/원래 runtime을 선정한다. 모든기능×상태 곱/전체PG를 무조건 반복하지 않는다.
기존 workforce native runner/manifest를 확장해 Master 실제 이동·현재 상태/과거 결과·거부·중복/불명응답/Actor 변경을 확인한다.
새 프레임워크/QA 관리 도구/의존성은 없다. 실제 node/개별 판정·exit/실패/미실행/경고와 동결 SHA를 기록하고 테스트를 완화하지 않는다.
기존 fixture로 자기 process/schema/auto QA를 정리하고 최소 근거만 보존한다. 개발→동결→독립검증→설계자검토→전담 한글상세 커밋/일반 feature push다.
원본 DB 적용/배포·새 과거 정정/미구현 Member/PT/정산 및 다른 OPEN은 포함하지 않는다.
