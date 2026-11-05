# IAM-015 — 계정 상태·Login ID 관리 제한 계약

Status: **IMPLEMENTED / DESIGNER LOCAL ACCEPTANCE PASS — APPROVED SPLIT VERIFICATION** (2026-11-05).
독립 진입검토·구현·실행과 설계자 인수를 마쳤다. [실제 결과](iam-015-account-lifecycle-results.md)와
[최소 근거](iam-015-account-lifecycle-review.json)의 범위/원래 실패/한계를 따른다. 운영 전환 승인은 별도다.
기준 parent `af9de549a5511eae28e66ba092c84cd98d2c8ef5`, branch `codex/iam-account-lifecycle`.
[LC-1/LC-2](../product/product-decisions.md#review-20261105-account-lifecycle)와 기존 A8/C6/E6/I1/I2를
구현하는 증분이다. ADR-0001–0005의 실제 상태와 전역 모듈 PROPOSED를 변경하지 않는다.
본 계약의 기술 선택은 설계자 제한 결정이며 전체 Architecture 승인이나 운영 전환 승인이 아니다.

## 범위와 인가

같은 조직의 현재 정상 Master만 다른 지원 계정의 전체 차단·복구·ID 변경을 수행한다.
지원 대상은 현재 구현된 Master, Branch Admin, 실제 Trainer 연결 계정, 겸임 및 동일 연결의 role0이다.
Master 본인 관리 우회 금지·마지막 사용 가능 Master 보호를 모든 별칭 경로에 동일 적용한다.
Branch Admin/Trainer/role0 행위자에게 전체 계정 관리 권한을 주지 않는다. 다른 조직/누락/지원하지 않는
orphan/본인 대상은 기존 비노출404를 따른다. Operator/Member·새 역할·계정 합치기·일반 디렉터리는 제외한다.

`scoped_account`는 기존 Branch Admin 전용 조회·Scope 변경·관리자 최초 설정에도 사용되므로 넓히지 않는다.
별도 lifecycle 대상 공개 계약으로 실제 현재 역할·불변 Trainer binding을 확인한다. Workforce의 비공개
테이블을 IAM에서 직접 읽지 않는다. 역할 유효성은 로그인/설정 자격과 구분한다. role0 복구는 로그인/권한을
만들지 않으며 Trainer 비활성/Home 변경·회수 grant·과거 업무/보상에 영향을 주지 않는다.

## 상태와 저장 사실

새 forward revision `0015_account_lifecycle`로 `iam_accounts.restore_state` nullable text를 추가한다.
이는 복구 목적지이며 과거 상태를 재구성했다는 역사 주장이 아니다. 클라이언트 입력으로 받지 않는다.

| 현재 상태 | 명령 | 결과 | restore_state |
| --- | --- | --- | --- |
| PENDING_SETUP | 차단 | DISABLED | PENDING_SETUP |
| ACTIVE | 차단 | DISABLED | ACTIVE |
| DISABLED | 복구 | 저장된 목적지 | NULL로 지움 |
| 세 상태 모두 | 다른 정규화 ID로 변경 | 상태 그대로 | 그대로 |
| 세 상태 모두 | 같은 정규화 ID | no-op | 그대로 |

실제 변경은 row/security version을 각각1 증가시키고 이전 인증을 철회하며 단일 UoW로 감사와 함께 확정한다.
이미 차단된 계정 재차 차단/비차단 계정 복구는409이며 목적지를 덮어쓰지 않는다.
no-op도 현재 expected_version/인가를 검사한다. stale은409; 정상 no-op은 version/감사/원본/세션/C2/
행위자 활동을 포함해 변경하지 않는다.

CHECK는 SQL NULL/UNKNOWN 통과를 막도록 명시한다. DISABLED는 restore_state NOT NULL 및 두 값 중 하나,
나머지는 NULL이다. PENDING_SETUP 및 pending 목적지 DISABLED는 hash NULL/reset_pending=false이다.
ACTIVE 및 ACTIVE 목적지 DISABLED는 기존0014의 정상 hash 또는 reset_pending/hash NULL/유효 generation
규칙을 유지한다. hash 존재 여부로 목적지를 추측하지 않는다. reset 대기 ACTIVE의 복구도 ACTIVE/reset 대기다.
기존 암호·reset generation·role epoch·grant/binding/Trainer 사실·C2 key/횟수/예약/이력은 보존한다.

## Migration과 이전 runtime

원래0001–0014 bytes는 불변이다. 기존0014 DISABLED에는 이전 실행 계약의 무조건 ACTIVE 복구를 보존하기
위해 목적지 ACTIVE를 부여한다. 비밀번호나 누락된 감사로 과거 상태를 추정한 결과가 아니다.
새 revision은 기존 schema/정책/readiness 무결성을 잠금하에 검사하고 모순 시 DDL 전에 거부한다.
명백한 반증은 기존 `audit_events`에서 `success=true`인 `account_disable` PENDING_SETUP→DISABLED 또는
`account_restore` DISABLED→PENDING_SETUP이다. 존재하면 자동 보정하지 않는다. 다른 최신 감사의 순서를
동일 시각만으로 추정하거나 감사 부재/보존 공백을 오류로 만들지 않는다. 다른 외부 변경 provenance는
별도 원본 데이터 검토 한계이며 이 증분에서 운영 데이터 전환을 실행하지 않는다.

새 감사 column은 추가하지 않는다. 기존 typed event의 실제 before/after state/ID/version/Actor Scope를 기록한다.
새 pending 차단/복구 사건은 그 자체로 실제 전이를 나타내고 과거 감사를 backfill하지 않는다.
0015→0014 downgrade는 모든 사전 검증 후에만 실행한다. pending 복구 목적지, 새 pending 차단/복구
감사, 잘못된 destination/readiness 등 기존0014 의미로 손실 없이 표현할 수 없는 사실이 있으면 거부한다.
기존 DISABLED/ACTIVE 목적지만 존재하고 기존 제약을 만족하는 경우는 backfill만을 이유로 거부하지 않는다.
거부 시 데이터/revision/DDL 불변과 rollback을 검사한다. 0014→0013의 기존 global-empty guard는 완화하지 않는다.
한 downgrade 요청이0014를 지나 더 내려가다 거부되면 트랜잭션 전체가 원래 상태를 유지해야 한다.

정책은2 그대로다. 기존 policy_transition의 역사 target0014를0015로 바꾸지 않는다.
현재 runtime/readiness/CLI/UoW는 **정확한0015 schema + 원래 유효 policy2 transition**을 요구하고,
이전 runtime은0015를 거부하며 새 runtime은 미전환0014를 거부한다. `>=revision`이나 자동 migration은 금지한다.
ProcessGuard/기존 명시 migration 진입을 사용한다. 원본 DB 변경·배포·dependency/lock 변경은 범위 밖이다.

## Source·ID·트랜잭션

실제 차단/복구/rename은 target AuthSession, 관리자/Trainer 최초 설정, reset/비상 복구와 남은 legacy
인증 source/context를 기존 정렬 잠금 순서로 폐기한다. 새 링크를 할당하거나 수명을 연장하지 않는다.
보존된 사건/원본 역사 행·기존 bounded GC/할당 정책을 지키며, 준비된 login/KDF/setup/reset 증명은
원래 account/security/purpose/policy/binding/epoch/source version·기한을 최종 잠금 후 재검사한다.
같은 ID 복귀/차단→복구 뒤에도 옛 증명이 다시 유효해지지 않는다.

새 ID 예약과 이전 ID의 원계정 영구 예약, 최초 고정 login_budget_key, 현재 ID만 로그인 원칙을 유지한다.
기존 hash를 ID 변경에 맞춰 다시 계산하거나 reset하지 않는다. Login ID 변경은 state/destination을 유지한다.
설치→정렬 account→영향 session→기존 canonical source/role→필요한 공개 업무 사실의 잠금 체계를 검토한다.
동기 SQLAlchemy UoW 하나로 처리하며 Repository별 commit/업무 잠금 중 외부 호출은 추가하지 않는다.

행위자 초기 authenticate는 touch 없이 원래 idle/absolute를 보존한다. 필수 감사와 최종 사실 조회 뒤
마지막 DB clock으로 원래 기한을 검증하고 성공한 변경만 같은 시각으로 한 번 touch한다.
감사 대기 뒤 만료/역할·상태 변경은 대상/감사/원본/활동 전체 rollback이다. 기존 RoleActorSnapshot의
self-change 예외를 넓히거나 deadline을 재설정해 실패 검증을 통과시키지 않는다.

## API와 최소 UI

목적을 구분한 새 읽기 계약:

- `POST /api/v1/admin/account-lifecycle/lookup`: 같은 조직 Master의 현재 정규화 Login ID 완전 일치 조회.
- `GET /api/v1/admin/account-lifecycle/{account_id}`: 같은 UUID의 최신 상태/version을 안전하게 읽음.

기존 일반 status/restore/login-id 및 Master 전용 mutation은 하나의 lifecycle 핵심으로 연결하고
일반 경로로 Master noSelf/보호를 우회하지 못하게 한다. `/access`, 원래 X1 `/accounts/lookup`,
최초 설정 `/activation`은 각각 기존의 좁은 계약을 유지한다. 새 읽기는 UUID/현재 ID/state/restore_state/
version/현재 지원 대상 종류·역할/설정 재발급 경로를 최소 DTO로 반환하며 Trainer에 가짜 BranchScope를 붙이지 않는다.
변경 응답도 같은 실제 사실을 사용한다. 기존 `account_json`의 nonMaster→BRANCH fallback을 Trainer-only/
role0에 적용하지 않는다. 관리 grant가 없으면 admin_scope는 NULL이고 실제 Master/Branch Admin Scope만 표시한다.
클라이언트의 role/org/목적지/자격 주장은 입력 금지다. 기존 strict JSON·CSRF/Origin·크기/ID 정규화를 유지한다.

Master에게만 최소 계정 관리 화면/section을 제공한다. 완전 일치 조회 후 명시 차단/복구/ID 변경을 수행한다.
복구 목적지를 명확히 보여주고 pending 복구/rename 뒤 링크를 자동 발급하지 않는다. 필요한 경우 기존 별도
명시 재발급으로 안내한다: Master/Branch Admin은 기존 관리자 최초 설정 경로, Trainer-only는 현재 실제
Trainer/유효 grant/Home 권한/I1을 다시 검증하는 Trainer 최초 설정 경로다. role0/비활성 Trainer는 자동 설정 불가다.
Branch Admin의 기존 Trainer 발급 권한은 유지하며 lifecycle 버튼/일반 계정 조회 권한을 부여하지 않는다.

일회용 링크는 state/ID/version 변경 또는 조회 실패에 맞춰 폐기하고 늦은 응답이 다시 표시하지 못하게 한다.
조회 세대/대상 UUID/version과 쓰기 대기 상태를 묶어 중복 클릭·낡은 덮어쓰기를 막는다.
409는 새 상태 조회 후 명시 재시도이며 자동 POST/복구 뒤 자동 발급은 없다. 503/transport/COMMIT ACK 불명은
UUID 안전 조회로 현재 상태만 대사한다. 타인의 version 증가를 자기 명령 성공 영수증으로 오해하거나
보상 rollback/옛 secret 재조회/자동 재발급하지 않는다. 정상 token 전달 유실은 기존 명시 재발급 원칙이다.

## 개발·독립 검증 진입

개발 담당자는 본 계약의 독립 진입검토와 설계자 승인 후에만 backend/src, 관련 tests, 새0015,
필요한 기존 QA/개발 안내를 수정한다. Product/ADR/원래 revision/의존성은 수정하지 않는다.
설계자는 Product/Architecture 현재 포인터·인수 문서를 관리한다. 테스트 담당자는 먼저 독립 정적 검토,
구현 동결 후 자기 실행의 fixture/수집·현재 schema/DB 소유권을 확인하고 승인된 검증을 실행한다.
browser 검증 작성자와 실행자를 구분하고 전원이 동시 source writer가 되지 않는다.

최소 검증은 다음의 양성/음성 대조와 관련 기존 회귀다.

- pending 차단→복구→별도 재발급→최초 설정, ACTIVE/정상 암호 및 reset 대기 복구, disabled rename/반복 cycle.
- 지원 대상/동일 조직 Master와 비Master/다른 조직/본인·역할0·Trainer 비활성/회수 grant, 기존 Scope 변경 격리.
- 상태/암호/역할/binding/업무/C2/옛 ID 예약 불변, 실제 rename 전 인증 폐기와 no-op/stale 차이.
- 준비된 증명 ABA, 설정 완료/rename/차단 경합, 감사 실패/행 대기 뒤 원래 Actor 기한, rollback과 ACK 유실.
- CHECK NULL 경계, 기존0014 호환 backfill/명백한 모순 거부, 안전 downgrade/전체 rollback, 정확 schema/정책 양방향 거부.
- 실제 화면의 최신 상태/명시 재발급/일회용 링크 폐기·늦은 응답/중복 클릭/불명 ACK. 기존 native 검증 틀을 재사용한다.

전체 실제 fixture setup-plan/collection을 먼저 확인한다. 역사 검증은 정확한 옛 revision에서 준비하며
0014 자체 guard에 현재0015 shape를 잘못 넘겨 실패시키지 않는다. 이전 head 호출의 의도를 개별 점검한다.
원래0001–0014 guard를 수정하거나 옛 MFA 요구를 현재 정책에 다시 적용하지 않는다.
새 fast와 선정 PG/native를 실제 exit·정확 node·skip/xfail/미실행·작성자/실행자·불변 source와 연결한다.
선정 실행을 전체PG PASS로 보고하지 않으며 이전 IAM-014 성적을 새 증분에 합산하지 않는다.

실행은 ignored `.local/qa/` 고유 폴더/전용 소유 schema·프로세스를 사용한다. 새 관리 시스템 없이 기존
pytest/fixture를 재사용한다. 최소 인수 요약과 미해결 근거만 보존하고 자기 자원 정리 결과를 보고한다.
완료는 개발→독립 테스트→설계자 검토→전담 한글 상세 커밋·일반 feature push다. main merge/원본 DB/배포는 없다.
