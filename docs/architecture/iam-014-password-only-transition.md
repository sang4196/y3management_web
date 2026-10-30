# IAM-014 — password-only 전환 상세 계약

2026-10-31. [현재 인증 정책](../product/product-decisions.md#review-20261031-password-only)과
[전체 설계](iam-014-password-only-design.md)의 직접 영향 전환 명세다. 기준 구현은7855786이다.
독립 제한 설계 검토를 마쳤다. 실제 DDL/코드·원본 DB 상태 집계/전환·테스트는 미구현·미실행이며 구현 전 기술 게이트를 유지한다.
이 명세의 필드/제약/검증 계획은 실행 결과가 아니다. 원본13 migration/감사·검증 결과와 현재Backend는 유지한다.

## A. 실제 의존성과 폐기/보존 대상

| 실제 원본 | 제약/GC 영향 | P0 처리 |
| --- | --- | --- |
| 0001 iam_installation(id=1), iam_security_control(id=1) | 설치/관리 잠금과 짧은 보안 transaction 직렬화의 원본 | 설치 row에 auth_policy_version과 policy_transition_id 추가. 원래 조직/설치 사실 유지 |
| iam_sessions(id,expires_at) → iam_security_states(id,expires_at), iam_session_slot | 이 FK는 cascade가 아니므로 session을 남기고 parent만 삭제할 수 없음 | 기존 양 assurance 전부 revoked=true. assurance 값 위조/기한수정 없이 session/slot 보존. 새 session만 password/policy2 |
| iam_preparations/iam_credentials/iam_trainer_setup_credentials/iam_reset_credentials | id→security_states ON DELETE CASCADE; 각각 consumed/expiry 및 계정버전·역할/source 목적 검사 | 모든 구 row consumed=true. 기존 expiry/hash/목적·generation 사실 유지. 새 policy2 원본만 현재 API 소비 |
| iam_recovery_credentials / iam_mfa_contexts | recovery/source/session/attempt/emergency FK, 여러 ON DELETE CASCADE; MFA context의 purpose별 임시hash 제약 | recovery consumed=true, context consumed=true와 password_hash=NULL을 같은 UPDATE. 새로운 MFA/recovery row 생성 없음. key/원본감사 보존과 임시 파생 비밀 종료를 구별 |
| iam_passkeys | credential_id PK, key_id UNIQUE, account FK; audit key_id는 역사값 | live row의 revoked_at만 전환시각으로 기록, 기존 revoked_at 유지. public_key/credential/key history 물리삭제 안 함 |
| iam_emergency_cases | UNIQUE(id,account_id,factors), emergency_identity(id,org,account,factors), supersedes 단일child, parent/origin 복합FK factors 동일 | 원래 facts/승인/완료/부모/factors 유지. both→password를 이 기존 FK에 억지로 넣거나 factors 덮어쓰기 금지 |
| iam_emergency_credentials | case_id UNIQUE, (case_id,account_id,factors) 복합FK; security_states cascade | 구source consumed=true, 새 password lineage는 별도 명시 구조 사용 |
| audit_events | emergency case/origin/previous FK, action/issuer variant check, key/reset before-after 필드 | 원래 이벤트/enum/FK 보존. 전환 이력은 별도 typed audit, 기존 passkey 성공을 password 성공으로 변환하지 않음 |
| iam_attempts/iam_budgets | attempts→states cascade 및 budget key FK; outcome/lease/window/cooldown | C2 outcome/finished_at/lease/cooldown/key 불변. 기존 waiting/verifying를 success/failure로 덮어쓰지 않음 |
| 0012 role grant→account(role_epoch) DEFERRABLE FK, 0011 binding 및 typed audit | 계정 security_version와 role_epoch는 서로 다른 경계 | role_epoch/grant/binding/Home/Trainer state 불변. 정책 전환은 역할변경 audit가 아님 |

실제 `Security._guard:27`은 context→source 순서로 SKIP LOCKED 후 **fresh snapshot child 부재 재확인**을 거쳐 부모 security_states를 삭제한다. `_guard:67`은 성공/만료 attempt를, `:73`은 자식 attempt 없는 만료 budget을 정리한다. `release:137`은 현재 여러 자식의 부재를 확인한다. 이 코드에서 MFA 테이블 이름만 빼면 부모 삭제가 숨은 cascade로 역사/자식을 지울 수 있다. `TrainerRoles.lock` 및 IAM.revoke_management_sources의 테이블 목록도 함께 바꿔야 한다.

### 전환은 소비·철회, 정리는 기존 bounded GC

설계자 판정에 따라 모든 옛 transient를 영구 고정하는 안과 관련 capacity 필터 변경은 철회한다. 보존용 새 필드/별도 보존체계를 추가하지 않는다. 신규 policy_version은 소비·인증 경계이며 GC 면제나 capacity 제외 근거가 아니다.

**실제 FK 확인 범위:** 기존0001–0013의 REFERENCES/FOREIGN KEY 및 MFA context 변경 DDL을 확인했다. `iam_mfa_contexts`를 부모로 참조하는 durable audit/case FK는 없다. 반대로 context가 source/session/attempt/emergency를 참조한다. audit_events는 emergency case/origin/previous case를 참조하고 transient credential/context를 참조하지 않는다. emergency credential→case FK를 이유로 credential을 지워도 case가 삭제되는 것은 아니다. FK의 삭제 방향은 부모→자식이다.

| 부모 삭제 대상 | 실제 자식/삭제 의미 | 안전한 정리 조건 |
| --- | --- | --- |
| context 자체의 iam_security_states | iam_mfa_contexts.id ON DELETE CASCADE | consumed 또는 expired context를 id정렬 FOR UPDATE SKIP LOCKED로 잡은 뒤 그 id의 parent만 삭제. durable 참조 없음. 잠긴 context는 건너뜀 |
| setup/recovery/emergency source의 security parent | source가 cascade 삭제되고 그 source를 참조하는 context도 cascade 가능. emergency에는 별도 복합FK도 있음 | context 먼저 정리. source 후보는 context reference 없음 조건, 정렬 UPDATE lock 후 새 statement snapshot으로 같은 부재 재확인. 건너뛴 context가 있으면 source 유지·다음 GC에서 재시도. 복합FK 제거/우회 없음 |
| preparation/trainer_setup/reset source의 security parent | 각 transient row cascade. 기존DDL에 그 row를 참조하는 MFA context 없음 | 기존 consumed/expiry·정렬 lock 조건 유지. 신규 password emergency source도 같은 parent/단회 원본 규칙으로만 추가 |
| iam_sessions 행 | iam_mfa_contexts.session_id ON DELETE CASCADE | IAM.gc_sessions의 기존 revoked/absolute/idle 조건·정렬 account SHARE/session UPDATE lock 유지. legacy도 같은 대상. 전환 직후 context는 이미 consumed·임시hash 없음. 자식 lock 충돌은 기존 DB lock/timeout·transaction rollback 의미를 지키며 권한 있는 새 자료로 간주하지 않음 |
| session_slot security parent | iam_sessions(id,expires_at) non-cascade FK | session 존재 동안 삭제 금지. session 정리 후 기존 expiry/무자식 orphan lease 조건으로 parent 정리. parent 만료를 억지로 앞당기거나 FK를 없애지 않음 |
| attempt security parent | iam_attempts cascade, 그 attempt를 참조하는 context도 cascade 가능 | 기존 success 또는 security parent expiry 조건 유지. 실패/진행 outcome·lease를 전환이 바꾸지 않음. 앞선 context 정리와 기존 DB 잠금/timeout 계약 유지. orphan 방지를 위해 parent 삭제를 무조건 강제하지 않음 |
| budget security parent | iam_budgets cascade, attempts→budget key는 non-cascade | 기존 expiry 경과와 child attempt 없음 확인 필수. 살아있는 cooldown/attempt를 capacity 확보 목적으로 버리지 않음 |

전환 transaction에서 source/context consumed=true, session revoked=true, key revoked_at, 정책marker·전환audit만 기록한다. context의 임시 password_hash는 소비와 함께 NULL로 종료하되 원본 Account hash는 보존한다. **migration 안에서 위 parent/child를 물리 DELETE하거나 전체 GC를 호출하지 않는다.** 이후 기존 security control 직렬화·bounded 자원/timeout·정렬 lock·source의 fresh-snapshot 재검증으로 정상 정리한다. 새 인증 기능은 MFA 발급/WebAuthn/키검증을 수행하지 않는다. 무효화된 legacy transient를 정리하는 호환 SQL의 제한적 조회는 허용한다.

`Security._guard/release`의 legacy context/source 존재 검사는 자료가 남는 동안 유지한다. orphan lease의 NOT EXISTS 목록도 그냥 삭제하지 않는다. 새 password emergency source를 추가하면 그 참조만 이 목록과 consumed/expiry 처리에 추가한다. 기존 expired/success attempt·budget·session_slot 정리 및 capacity count 의미는 그대로다. policy1 자료를 capacity에서 일괄 제외하지 않으며, C2 stable key/failure window/cooldown/lease/query bound를 바꾸지 않는다.

영구 보존 대상은 Account/역할·불변binding/원래 durable hash, emergency case/승인·handoff lineage, 기존 audit 및 revoked key 역사다. 이들은 legacy GC의 DELETE 대상이 아니다. 정리된 ephemeral의 원문을 별도 영구 복제하지 않는다. 현재 확인된 durable FK 때문에 모든 옛 session/source/attempt/budget를 영구 보존해야 할 예외는 없다. 특정 lock이나 살아있는 child로 **일시 보류**되는 경우만 기존 GC가 다음 실행에서 재검사한다. F의 ACK 실패 직후 committed-child 보존과 이후 정상 bounded GC는 서로 다른 관찰 시점이다.

## B. 정확한 marker / 새로운 자격 경계

제안 정책 숫자: legacy=1, password-only=2. 이는 인증 정책 schema 값이며 사용자 수치 정책이 아니다.

- `iam_policy_transitions`: id UUID PK, from_version=1, to_version=2, transition_at(DB clock), target_schema_revision, immutable summary 및 UNIQUE(to_version). installation.policy_transition_id FK, auth_policy_version CHECK IN(1,2). 초기 빈DB에도 같은 marker가 생긴다.
- 새 `iam_sessions.policy_version`과 위 현재 단회 테이블들의 `policy_version`은 NOT NULL CHECK IN(1,2). security_states에 UNIQUE(id,policy_version), 각 자식의 (id,policy_version) 복합FK를 추가한다. session의 기존 (id,expires_at) FK는 그대로 유지한다. `CHECK(policy_version<>2 OR assurance='password')`, `CHECK(policy_version<>1 OR revoked)`로 legacy session 재활성화를 막는다. 구 source는 `CHECK(policy_version<>1 OR consumed)`로 일괄 폐기 결과를 강제한다.
- 이 FK가 현재 installation policy와 같음을 자동 증명하는 것은 아니다. runtime은 policy marker=2를 부팅/CLI 진입 및 각 새 security/business UoW에서 확인하고, 모든 token lookup은 source/session.policy_version=2 조건을 가진다. legacy row 조회 후 조건 누락에 기대지 않는다. 새 INSERT는 policy2를 명시하고 legacy DEFAULT를 남겨 구 INSERT를 묵시 승격시키지 않는다.
- `LoginProof`, setup/reset/비상 proof, `Reservation`, `RoleActorSnapshot`에 policy_version 및 transition_id를 포함한다. client가 준 값은 사용하지 않고 서버가 현재 marker에서 만든다. password hash 준비 전후와 최종 잠금 안 marker 일치 검사. 기존 account/security/role/source generation/expiry/nonce 검사를 대체하지 않는다.
- 새 token 포맷을 바꾸는 것만으로 안전을 주장하지 않는다. 무작위 원문/digest는 유지할 수 있으며 목적별 table·정책·계정·원래기한을 검사한다. 구token이 policy2 endpoint로 넘어와도 거부한다.
- fresh admission과 legacy C2 이력을 분리한다. 기존 waiting/verifying proof/lease는 새 policy2 credential/session을 만들 수 없다. 대기 행 자체는 원래 lease가 끝날 때까지 보수적으로 admission을 점유하며 실패 수로 조작하지 않는다.

제안 transition UPDATE 대상(아래는 문서 명세이며 실행 SQL이 아님):
1. `iam_accounts`: 모든 row security_version=security_version+1, row_version=row_version+1; hash/state/reset_generation/password_reset_pending/role_epoch는 유지. recovery_pending 제거는 D의 분류 결과에만 따름.
2. `iam_sessions`: revoked=true (기존 assurance/기한/감사는 유지).
3. `iam_preparations`, `iam_credentials`, `iam_trainer_setup_credentials`, `iam_reset_credentials`, `iam_recovery_credentials`, `iam_emergency_credentials`: consumed=true, expiry·원래 version/factors 불변.
4. `iam_mfa_contexts`: consumed=true,password_hash=NULL; 허가를 폐기하되 첫 비밀번호로 승격하지 않음.
5. `iam_passkeys`: revoked_at=COALESCE(revoked_at,transition_at).
6. policy metadata, typed 전환 이력 및 installation marker를 같은 transaction으로 기록. pending의 출처가 불명확하면 앞선 UPDATE 이전 또는 transaction rollback으로 전부 취소.

기존 정상 hash가 없는 ACTIVE/DISABLED는 0007 account CHECK상 reset_pending+generation>0이어야 한다. 이 관계가 깨진 row는 정상 복구 후보가 아니라 전환 오류다. constraints를 disable해서 통과시키지 않는다.

## C. 유지보수·잠금·실패 경계

`runtime.py::ProcessGuard`는 POSIX flock, 고정 `/tmp/y3management-runtime`, UID/0700 dir·0600 file·NOFOLLOW, port/database/schema identity, worker_count=1을 사용한다. 이미 기존 앱/CLI가 잡은 동일 락과 전환 실행의 배타성을 재사용한다. 별도 lock경로나 framework를 만들지 않는다. 동일 호스트 범위를 넘는 자동 탐지 기능은 없다.

전환 실행은 운영자가 구 앱/CLI/GC 중지를 확인한 뒤 guard 획득→DB transaction→기존 보안 control/설치/참조 table들의 DDL용 ACCESS EXCLUSIVE lock을 **고정 순서**로 획득한다. 제안 순서: security_control → installation → accounts → sessions → security_states → preparations/credentials/trainer_setup/reset/recovery/emergency credentials → MFA contexts/passkeys → cases → budgets/attempts → 해당 audit/신규 전환 tables. 다중 lock 획득 중 timeout/deadlock이면 전체 rollback하며 살아있는 구프로세스를 자동 종료하지 않는다. 온라인 운영을 지원하는 잠금 순서라고 주장하지 않는다.

각 account row는 UUID 정렬, affected session은 id 정렬, source는 목적별 고정 순서·id 정렬 FOR UPDATE로 조회하여 전환 판정과 실제 행 변경 경계를 검증한다. 배타 table lock과 row lock은 purpose가 다르다: 전자는 유지보수/DDL 충돌 차단, 후자는 코드/테스트에서 명시적인 데이터 판정 순서다. 기존 workflow의 installation→sorted Accounts→affected Sessions→sources 순서 및 독립 Security UoW를 역전시키지 않는다. 전환 중 독립 nested Security transaction을 열지 않는다.

입력 상태와 기존 FK 의존 대조→typed audit→원본 폐기→marker/schema 변경이 한 transaction이다. 마지막 marker 기록 전 오류·감사 실패·검증실패는 전체 rollback. commit ACK 모호하면 원래 transition id/unique to_version/marker/row counts digest로 **읽기 대사**하며 UPDATE 재실행으로 version 재증가하지 않는다. 새 policy 이후 downgrade는 데이터 있는 경우 DDL 전 거부한다. 설계자 확정에 따라 **전역 완전 빈 DB만 lossless0014→0013 왕복을 허용**한다. 아래 K절의 전체 표·전환 zero-summary·singleton 조건을 DDL 전에 검사하며, 데이터가 하나라도 있으면 거부하고 forward repair한다.

marker는 구 worker를 중지시키지 않는다. guard를 무시하는 직접 DB 클라이언트까지 차단했다고 주장하지 않는다. 실제 구프로세스 부재·접근권한·backup 검증은 운영 인수 자료다. 새 앱/CLI는 marker/revision 불일치면 거부하지만 production 거부도 계속 유지한다.

## D. key 은퇴 판정과 최소 전환 이력

새 `iam_policy_account_transitions` (transition_id,organization_id,account_id) PK, account 복합FK, before/after state·row/security version, before recovery_pending/password_reset_pending/password_ready, classification, retirement_kind를 저장한다. 분류 enum은 `unchanged_password`, `pending_setup`, `disabled`, `password_pending`, `key_only_retired`; 필요 case id를 별도 nullable FK로 묶는다. 토큰·hash·public key·Login ID·승인 원문을 audit에 복사하지 않는다. row count/enum 집계는 transition header와 대조한다. 사용자·역할 변경 행위 audit로 위장하지 않는다.

분류는 다음 **primary 우선순위**를 위에서부터 단 한 번 적용한다. 계정당 `(transition_id,organization_id,account_id)` 정확히1행이며, 대상 계정 수와 전환 이력 수·ID 집합을 같은 transaction에서 대조한다.

1. 상태/hash/pending/세대/FK/사건 의미의 invariant 불일치 또는 분류 불명 → 전체 전환 abort. 아래 분류로 덮지 않는다.
2. DISABLED → `disabled` (password pending과 key retirement는 auxiliary facts).
3. PENDING_SETUP → `pending_setup` (임시hash 존재는 auxiliary, durable hash 승격 없음).
4. ACTIVE이고 password_reset_pending → `password_pending` (null durable hash 및 양수 reset_generation 필수).
5. ACTIVE이고 durable hash·!password_reset_pending이며 검증된 순수 key 대기 → `key_only_retired`.
6. 나머지 적격 ACTIVE durable hash·!password_reset_pending·남은 미분류 key 대기 없음 → `unchanged_password`.

auxiliary facts는 before/after password_ready/password_reset_pending, before/after key pending·retirement_kind, 원래 사건/factors·적격 password continuation을 저장한다. 따라서 DISABLED+password pending+key 대기는 primary disabled **한 행** 안에 모두 보존하며 여러 primary 행을 만들지 않는다. legacy key flag 분리도 account state/암호 복구 완료로 표현하지 않는다.

- PENDING_SETUP/nullhash/!reset_pending: 유지. staged hash 존재는 완료 증거가 아니다. source 폐기 후 인가된 새 최초 설정을 기다린다.
- DISABLED: 유지. durable hash 또는 기존 reset_pending 사실을 보존하고, key요인 관련 flag는 전환 이력으로 분리한다. 이 분리는 account restore가 아니며 해제 후에도 남은 password/role/업무 조건이 필요하다.
- ACTIVE durable hash + !password_reset_pending: 정상 password 기반 사실. recovery_pending=false면 그대로; true면 실제 latest 유효 recovery/비상 사건 및 감사와 generation/대상 일치, password 범위 미완료가 없다는 증거를 확인해 `key_only_retired`로 남긴다. 단순 key 존재/부재로 판정하지 않는다.
- ACTIVE/DISABLED reset_pending+nullhash+generation>0: password_pending 유지. key요인 제거는 그 암호 복구 완료를 의미하지 않는다. 역할0/inactive/Home는 원상 보존.
- both 사건: 현행 `Emergency.complete`는 두 요인을 원자 완료하므로 **임시 context hash만 존재하는 것은 password 완료가 아니다**. completed_at/audit/account facts로 실제 완료를 증명해야 한다. 미완료 both는 password 범위가 여전히 미완료인 경우로 처리하고 원래 승인 subset만 인계한다.
- GC로 source가 사라져도 durable 사건/감사와 계정 generation으로 출처를 입증할 수 있으면 검토 가능하다. 출처·세대·완료 여부 모순/불명, PENDING+durable hash, reset_pending+durable hash, foreign org나 factor scope 불일치는 전환 abort. 입력에서 실제로 일어나지 않는 상태를 임의 정상화하지 않는다.

## E. legacy both → password lineage의 최소 DDL 제안

원래 `iam_emergency_cases`/그 source/인계 복합FK를 수정하지 않는 것이 목적이다. `both`를 password로 바꿔 기존 parent FK를 통과시키면 승인 원본을 훼손한다. 신규 **암호 사건 table + 그 단회 source table**을 제안한다(별도 bridge table은 필요 없음).

`iam_password_emergency_cases` 필수값:
- id(operation UUID) PK, organization_id/account_id 복합FK, policy_version=2, purpose='password', kind IN('operating','legacy_handoff','handoff'), UNIQUE(id,organization_id,account_id).
- legacy_origin_id/legacy_parent_id와 각각 legacy_origin_factors/legacy_parent_factors nullable. legacy_handoff는 모두 NOT NULL, factors IN('password','both'), 각각 `(id,org,account,factors)`를 기존 `emergency_identity`로 FK. 같은 target/org를 묶고 passkey-only를 CHECK에서 거부한다. origin은 운영승인 원본, parent는 마지막 유효 옛 사건이며 동일해도 된다.
- parent_id는 신규 table의 `(id,org,account)` 복합FK. handoff는 필수이고 자기참조 금지. `UNIQUE(parent_id) WHERE parent_id IS NOT NULL`, `UNIQUE(legacy_parent_id) WHERE legacy_parent_id IS NOT NULL`로 각 부모당 새 자식 하나. 동일 operation id는 canonical payload fingerprint가 같으면 기존 결과, 다르면409.
- kind별 CHECK: operating은 기존 manual 승인 필드/검증시각/승인유효기한·별도 실행자 필수, parent/legacy refs NULL. legacy_handoff는 current Master actor 필수·actor!=target, 운영승인 필드 NULL(새 승인을 위조하지 않음), legacy refs 필수. handoff는 current Master actor와 신규 parent 필수; inherited origin은 parent lineage를 따라 읽고 검증하며 중복 복사하지 않음.
- issued_at/expires_at/completed_at; expiry>issued_at AND expiry<=issued_at+30min. current account row/security/reset generation snapshot, issuer, fingerprint. 원래 legacy case의 expires_at이나 approval_valid_until을 변경하지 않는다.
- FK는 legacy origin이 실제 operating인지, parent가 그 origin의 후손인지, 현재 미완료 password가 있는지까지 증명하지 않는다. 그 부분은 installation/account/parent 잠금 아래 durable chain을 검사하고 typed case audit와 commit한다. 반대 SQL seed를 이용한 DB 구조 제약 검사와 service 의미 검사를 구별한다.

### E-0. 신규 case의 상호 배타 variant와 source 결합

아래 `N`은 반드시 NOT NULL, `—`는 반드시 NULL이다. CHECK는 SQL의 UNKNOWN을 통과시키지 않도록 각 variant의 IS NULL/IS NOT NULL을 전부 명시한다. 단순 `kind IN` 검사만으로 대체하지 않는다.

| field/group | operating | legacy_handoff | handoff |
| --- | --- | --- | --- |
| issuer_account_id | — | N, target와 다름 | N, target와 다름 |
| approval_ref/owner_ref/executor_ref/executor_uid/checked_at/approval_valid_until | 모두 N | 모두 — | 모두 — |
| approval_mode | manual | current_master | current_master |
| parent_id (신규 case) | — | — | N, 자기 id와 다름 |
| legacy_origin_id/legacy_parent_id/두 factors | 모두 — | 모두 N, 양 factors 동일·password 또는 both | 모두 — |
| policy_transition_id/continuation_eligible | 모두 — | N/true | 모두 — |

공통 id/org/account/policy_version=2/purpose='password'/fingerprint/issued_at/expires_at/발급후 snapshot은 NOT NULL이다. 모든 handoff의 actor는 같은 org account 복합FK이고 현재 Master 여부는 서비스가 잠금 안 확인한다. operating은 executor_uid>=0, owner_ref!=executor_ref, checked_at<=issued_at 및 approval_valid_until>issued_at 등 기존 승인 조건을 따른다. `approval_valid_until`은 실제 기존 운영 승인 필드이며 발급시 유효성을 검사한다. 30분 링크 TTL과 같다고 추정하거나 R4 인계에 새 승인 TTL을 만들지 않는다.

일반 handoff의 원래 승인 origin은 신규 parent chain을 따라 operating 또는 legacy_handoff의 고정 origin까지 찾는다. 직접 legacy refs를 복사하지 않는다. parent chain cycle/누락/foreign target·origin 불일치는 거부한다. 이 ancestry 의미는 단순 self-FK가 증명하지 않으므로 서비스 검증과 별도 인수 대상이다. legacy_handoff의 전환 복합FK는 E-1을 따른다.

**새 password emergency source / case / allocator 계약:**

- security_states의 기존 kind=`emergency`를 재사용하고 새 kind/capacity 정책을 만들지 않는다. 제안 UNIQUE(id,policy_version,kind,expires_at)를 추가한다. source에는 allocator_kind='emergency' CHECK, policy_version=2, purpose='emergency_password'를 둔다. `(id,policy_version,allocator_kind,expires_at)`가 allocator의 위 UNIQUE tuple을 참조한다. allocator의 id는 source id이고 case id와 별개다.
- case에 `source_purpose='emergency_password'` CHECK 및 UNIQUE(id,organization_id,account_id,policy_version,source_purpose,expires_at)를 둔다. source의 `(case_id,organization_id,account_id,policy_version,purpose,expires_at)`는 그 tuple에 복합FK로 연결한다. source.case_id UNIQUE는 case당 source 하나를 보장한다. 재발급은 새 case+새 source+새 allocation이며 옛 case 만료를 바꾸지 않는다.
- 이 구조에서 **세 expires_at은 동일**해야 한다. source/case는 원래 allocator30분 기한을 그대로 사용하며 이후 이동시키지 않는다. case.issued_at은 실제 case 발급 DB clock, expires_at>issued_at 및 <=issued_at+30분을 검사한다. allocation 후의 짧은 준비 시간이 남은 수명을 줄일 수 있으며 기한을 보상 연장하지 않는다. 명시 재발급에는 새 allocation의 새30분을 적용한다.
- 각 policy_version/purpose/kind의 상수 CHECK와 복합FK는 row 간 정책·목적·기한 혼용을 막는다. 현재 installation marker와 같은지, account/case snapshot·미완료 범위·원래 승인 lineage가 유효한지는 IAM 서비스가 최종 잠금 안 검증한다. FK가 현재 인증/사람 승인 진위를 대신한다고 주장하지 않는다.
- 새 allocation → case/source 생성 → 감사가 실패하면 같은 business UoW를 rollback하고, 별도 security release는 source 자식이 없을 때만 정리한다. commit ACK 모호 시 부모 release로 확정 자식을 cascade 삭제하지 않는다. 신규 복합FK를 이유로 기존 session_slot/다른 source 기한을 일괄 수정하지 않는다.

### E-1. 전환 전 유효성의 증명과 제한된 snapshot 연결

기존 `Handoff.validate`는 사건의 **발급 후** row/security/key_set/reset/recovery generation과 현재 계정을 비교한다. `expected_*`는 발급 전 사실이므로 비교 대상을 혼동하지 않는다. 전환의 +1 때문에 이 비교를 무조건 생략하거나 부모를 최신 epoch로 rebasing하면 안 된다.

전환 account 이력(D)에 다음 불변 fact를 추가한다. 원문 hash/key 대신 readiness boolean만 쓴다.

- before와 after 각각: state, row_version, security_version, key_set_version, reset_generation, recovery_generation, password_reset_pending, recovery_pending, password_ready, key_ready, trainer_role_epoch, 현재 admin scope/branch 사실.
- `legacy_parent_id`, `legacy_origin_id`, `legacy_factors`, `legacy_password_continuation_eligible`를 추가한다. 적격성은 cutover 잠금 안에서 계산한다. 명백한 stale 사례는 eligible=false와 이유(enum)로 남기고 연결을 거부한다. 모순/분류불능을 정상 stale로 덮어쓰지 않으며 전환 abort 판정은 유지한다.
- UNIQUE(transition_id,organization_id,account_id,legacy_parent_id,legacy_origin_id,legacy_factors,legacy_password_continuation_eligible). eligible=true이면 parent/origin/factors NOT NULL, factors IN('password','both'), before/after state='ACTIVE', before/after password_reset_pending=true, before/after password_ready=false가 CHECK 필수다.
- before/after row와 security는 각각 after=before+1, reset/recovery generation·key_set_version·role_epoch·admin grant는 같아야 한다. after key_ready=false는 key 철회의 결과이며 before key_ready를 변경하지 않는다. key recovery flag의 은퇴 전후는 별도 retirement 판정과 맞춰 기록한다. account hash·역할·상태를 고치는 효과는 없다.
- 이 이력의 legacy parent/origin은 기존 `(id,organization_id,account_id,factors)` 복합FK를 따른다. null tuple로 FK 검사를 빠져나가지 않도록 eligible=true의 NOT NULL 조건을 명시한다.

신규 `iam_password_emergency_cases`의 legacy_handoff에 `policy_transition_id`, `continuation_eligible=true`를 필수 추가한다. `(policy_transition_id,organization_id,account_id,legacy_parent_id,legacy_origin_id,legacy_parent_factors,continuation_eligible)`는 위 전환 이력 UNIQUE tuple을 참조한다. legacy origin factors=parent factors CHECK를 둔다. operating/일반 신규 handoff에는 이 직접 전환 참조를 NULL로 두고 신규 부모 chain을 따른다. 이 FK는 다른 계정/전환/부모의 적격 판정을 빌릴 수 없게 한다. 기존 factors 복합FK와 원본 사건은 그대로다.

검증식을 명시한다. `P`=옛 부모의 발급 후 snapshot, `B`=cutover 직전 snapshot, `A`=cutover 직후 snapshot, `C`=새 명시 인계 직전 현재 snapshot이다.

1. **P→B**: `(row_version,security_version,key_set_version,reset_generation,recovery_generation)`가 정확히 같아야 한다. B는 ACTIVE/current Master이고 P는 completed_at=NULL·latest unsuperseded case여야 한다. P.factors=password이면 B.reset_pending=true/password_ready=false/recovery_pending=false/key_ready=true, both이면 B.reset_pending=true/password_ready=false/recovery_pending=true/key_ready=false로 기존 `Handoff.validate`의 의미를 유지한다. 이 단계에서 key 상태는 전환 잠금 아래 실제 DB 사실로 확인하며 key의 암호학적 인증 완료를 새로 주장하지 않는다.
2. 원래 operating origin과 parent chain의 조직/대상/factors, issuer variant, supersedes/origin 일치·버전 단조 증가를 검증한다. 현재 다른 Master라는 사실만으로 이 과거 chain을 만들 수 없다. 발급 전 expected tuple도 원본대로 보존하고 원래 사건의 증거를 새 값으로 재작성하지 않는다.
3. **B→A**: 위 전환 전용 +1 및 허용 key 은퇴 차이만 허용한다. 변경 없는 password 미완료 범위와 원래 case를 전환 이력이 뒷받침한다. 전환 외 account mutation을 함께 감추지 않는다.
4. **A→C**: 현재 policy marker/transition id가 일치하고 row/security/reset generation, password pending/readiness, state, 현재 admin grant가 A와 같아야 한다. 보존된 key_set/recovery generation scalar도 바뀌지 않았음을 확인한다. current consumer가 live Passkey를 조회할 필요는 없다. C에서 다시 같은 조직 ACTIVE Master·password 미완료 범위를 확인한다. **대상의 독립 Trainer grant/role_epoch는 원본 유효성의 A와의 필수 동등 조건에서 제외한다.** I2의 Trainer 역할 cycle만으로 장기 원본/기존 password 승인 범위를 폐기하지 않는다. 계정 row/security·암호/세대·Master grant가 바뀌었다면 그 독립 근거로 stale 거부하며, 이를 최신값으로 rebasing해 통과시키지 않는다.
5. 새 명시 인계 Actor는 같은 조직의 **현재 인증된 다른 Master**이고 noSelf/CSRF·원래 idle/absolute·현재 scope를 별도로 검사한다. Actor 자신의 epoch/currentSession은 항상 같은 요청에서 새 snapshot으로 읽고 최종 재검증하며, target 원본의 epoch 예외를 Actor에 적용하지 않는다. 원래 R4의 operating 링크 만료 조건은 명시 인계 시점에 그대로 검사한다. 만료 전 cutover에서도 P→B 적격성을 기록할 수 있지만, 이를 근거로 만료 전 인계를 허용하지 않는다. 새 source는 이 적격 인계에서 새30분이고 ACK 재조회는 연장하지 않는다.
6. 성공 시 새 case는 C에서 정상 인계로 증가한 account row/security/reset generation과 source를 소유한다. 새 source 발급/암호 hash proof 준비는 현재 target epoch를 관찰해 만들고, 준비된 proof는 최종 잠금에서 그 epoch와 현재 epoch의 동일성을 검증한다. proof 준비 뒤 Trainer 역할 변경은 옛 prepared proof를 거부하지만, 독립 credential/권한 조건이 유효한 원본에서 현재 epoch로 새 proof를 준비하는 것은 허용한다. source에 발급 당시 epoch를 기록하더라도 이를 영구 원본 만료 조건으로 사용하지 않는다. 전환 참조는 그 **첫 legacy_handoff**의 선행 증거다. 다음 신규 handoff는 새 부모의 발급 후 snapshot과 현재 facts를 비교하며 A로 반복 되돌아가지 않는다. 같은 parent 한 child/operation idempotency는 기존 제안을 유지한다.

P→B의 full tuple·미완료 범위와 A→C의 현재 사실 검사는 IAM 소유 installation→정렬 actor/target accounts·sessions→case/source 잠금 안에서 수행한다. 전환 기록의 before/after 값이 정말 DB에서 관찰된 값인지 FK만으로 증명되지 않는다. 이 부분은 전환 transaction의 read/update/audit 원자성과 독립 DB 검증으로 보장한다. 새 FK는 연결 구조와 필수 facts를 보장하며 SQL만으로 모든 의미 검증을 했다고 과장하지 않는다.

stale parent는 `409 stale_snapshot` 등 기존 범주의 거부다. 현재 Master가 A8 정상 reset을 따로 하거나 필요하면 새로운 AB5 승인 절차로 처리할 수 있으나, 실패한 과거 인계를 성공으로 재분류하지 않는다. 과거 사건/승인·stale 이유는 보존한다.

추가 최소 인수: (a) P=B인 legacy both/password→cutover→동일 C에서 인계 성공, (b) cutover 직전 이미 row/security/key/reset/recovery 중 하나라도 stale이면 +1 후에도 거부, (c) 전환 이후 A→C의 credential/권한 stale 변동 거부와 독립 Trainer epoch-only cycle 뒤 새 준비 허용·옛 prepared proof 거부, (d) foreign transition/parent/origin 및 NULL eligibility tuple FK/CHECK 거부, (e) passkey-only/완료/후속 child 존재 거부, (f) 전환과 신규 인계 감사 실패 각각 rollback, (g) 같은operation ACK 대사 무연장. 실제 수집/실행은 하지 않았다.

`iam_password_emergency_credentials`: id→security_states(id,policy_version) 복합FK, case_id UNIQUE, (case_id,org,account)→신규 case FK, policy_version=2, digest UNIQUE/32bytes, account/security/reset generation, expires_at, consumed, purpose='emergency_password'. source에 factors 선택값은 없다. 신규 case를 현재 consumer의 원본으로 쓰며 legacy source를 새 consumer에서 재사용하지 않는다.

새 `EmergencyPasswordProof`는 source id/case id/정책version·transition id/account org/id·row/security/reset generation/**현재 trainer_role_epoch**/원래 source expiry/새 hash를 가진 서버 내부 immutable proof다. trainer_role_epoch는 해시 준비 전에 읽고 최종 잠금 뒤 현재 값과 반드시 일치해야 한다. case/source에 발급시 epoch를 기록하더라도 long-lived 원본을 폐기하는 고정 유효성 조건으로 사용하지 않는다. 신규 hash는 응답·감사에 포함하지 않는다. hash 준비 후 잠금 안 동일 snapshot·source 미소비·현재 ACTIVE Master·policy·DB clock 재검증 후 소비/암호 완료/감사 한 UoW. source 수명은 발급시 새30분이며 hash 준비가 연장하지 않는다.

새 `audit_password_emergency_events`는 신규 case FK, legacy origin/parent 참조(필요한 legacy_handoff에만), actor/역할/행위·generation·버전 전후·정책version을 typed 저장한다. legacy case의 audit_events를 고치거나 기존 emergency_factors='both'를 password로 수정하지 않는다. 기존 역사 조회와 현재 사건 조회는 응답에서 출처를 구별한다. 새 감사 원본에 승인 원문·token/hash는 넣지 않는다.

R4 인계는 만료된 원본 링크 뒤에도 현재 정상 Master 권한으로 새 password source를 발급한다. 신규 운영 CLI 실행의 approval_valid_until 검사와 혼동하지 않는다. 같은 operation ACK 조회는 같은 case/expiry를 돌려주며 **원문 링크 복구 또는 새 TTL 생성은 하지 않는다**. 사용자는 별도 명시 reissue로 새 operation을 시작한다. passkey-only 사건에서 새 password 권한이 필요하면 기존 A8 또는 새로운 AB5 password 승인이 필요하다.

## F. S1 committed child와 미전달 session 철회

직접 영향 노드: `tests/test_iam.py::test_commit_ack_loss_preserves_committed_children`. 기존 S1의 로그인 후 `NOT revoked=1`은 새 모드의 정책과 다르므로 그 단언만 설계자 승인 변경으로 명시한다. 대체는 **확정 session/slot 및 그 실행에서 실제 남아 있던 attempt child·성공 login audit 보존, session.revoked=true, cookie 없음, 그 token 재사용401**이다. 정상 Security GC가 이미 정리한 success attempt를 새로 재생성하지 않으며, 실패 처리 때문에 기존 child가 cascade로 없어지지 않았음을 fault 지점별로 대조한다.

새 권고 절차: admission reserve→hash/proof→session+audit business commit→별도 finish(success)→응답 전달. business/finish ACK 손실 시 우리 attempt와 sid의 연계/계정/proof가 확인되는 committed session만 별도 UoW로 UPDATE revoked=true. 다른 기존 session은 보존한다. 이후 `release(sid,collect=False)`는 자식 존재 때문에 부모를 삭제하지 않아야 한다. committed child가 있는 경우 cancel/reservation 삭제를 호출하지 않는다. `_guard`가 즉시 revoked session을 지워 이 검증을 우회하지 않게 cleanup과 정상 다음GC를 구분한다.

단순 sid(UUID) 소유 추적과 durable 원본 일치를 명시할 최소안: 신규 session에 login_attempt_id 및 policy/계정 연계를 보존하되 ephemeral attempt FK는 만들지 않아 정상 success-attempt GC를 방해하지 않는다. proof/reservation의 서버 내부 id와 session의 이 필드를 비교한다. 원문 cookie는 응답 전 일시 메모리에만 있고 로그/QA에 쓰지 않는다. session 없으면 미commit으로 안전한 no-op; 상태 확인 실패면 cookie를 반환하지 않고 제한된 deferred cleanup/원래 bounded expiry로 대사한다. DB 오류를 wrong-password401로 바꾸거나 C2 failure/성공을 재기록하지 않는다.

이것은 **응답 전 발생한 관찰 가능한 실패** 처리 계약이다. 서버가 성공 응답을 넘긴 뒤 네트워크에서 유실된 cookie의 실제 수신 여부를 일반 HTTP만으로 자동 알 수 있다고 주장하지 않는다. receipt protocol을 새로 도입하지 않는다. reset/발급 ACK는 session과 달리 확정 계정/source를 되돌리지 않고 safeGET·명시재발급한다.

## G. 직접 영향 테스트의 구체 매핑

아래 새 이름은 제안 def이며 아직 파일/collection/실행이 없다. 전체614 복사·AST 전량 문서화가 아니다.

| 기존 파일::def | 폐기/보존과 새 제안 |
| --- | --- |
| test_iam_mfa.py::test_crypto_rejection; test_iam_mfa_security.py::test_synced_zero_counter_and_backup_state / test_nonadvancing_counter_and_duplicate_key_rejected | WebAuthn crypto/key counter 기능 폐기. 새 `test_removed_factor_routes_and_imports`로 API404/패키지 미의존·새 설정거부 검증; crypto 성공 건수로 환산하지 않음 |
| test_iam_mfa.py::test_actual_cli_setup_two_keys_and_branch | two keys만 폐기. `test_cli_password_master_then_actual_admin_setup_and_scope`: 실제 getpass/CLI·브랜치·본인설정·정상 password login/타지점차단 유지 |
| test_iam_mfa_install.py::test_cli_failed_or_unknown_commit | enrollment 파일 의미는 폐기. `test_password_bootstrap_commit_failure_or_unknown`: 단회 조직/account/hash/audit, 보호 입력, rollback/ACK 대사·재bootstrap금지 유지 |
| test_iam_mfa_security.py::test_c2_shared_budget_success_does_not_clear / test_actual_budget_key_binding / test_failed_login_audit_principal_and_unknown | password-only 실제 login으로 재작성. success로 기존failure/cooldown 지우지 않음·계정 비노출/현재ID/rename admission 결합 유지 |
| test_iam_mfa_security.py::test_waiting_is_bounded_and_counts_toward_admission | 신규 MFA waiting은 폐기. `test_legacy_waiting_lease_preserves_c2_and_admission`으로 전환 입력의 대기 행이 성공/실패로 바뀌지 않고 원래lease 적용됨을 검증 |
| test_iam_mfa_security.py::test_failed_final_delivery_never_returns_cookie + test_iam.py::test_commit_ack_loss_preserves_committed_children | F의 단일 password모드 fault matrix로 통합. audit rollback/commitACK/finishACK/cleanup 실패 각각 child·cookie·기존session·C2를 별도 대조 |
| test_iam_mfa_security.py::test_onboarding_reissue_revokes_staged_password / test_setup_key_and_audits_roll_back_together | `test_password_setup_reissue_and_atomic_completion`: staged hash 승격 없음, 원래source 재발급/소비/암호·ACTIVE·감사 동시rollback, auto login 없음 |
| test_iam_mfa_races.py::test_single_enrollment_consumption_race / test_registration_or_login_orders_security_changes | 암호 setup 단회경합 및 실제 password proof 준비 뒤 disable/rename/reissue의 독립worker 선후로 재작성; 도달장벽/실제commit 확인 유지 |
| test_iam_mfa_management.py::test_delete_revokes_every_session_and_preserves_last_key; races::test_concurrent_key_deletion | 키삭제 기능 폐기. 계정 마지막 Master 보호는 별도 reset/관리 경합에서 계속 검증; 마지막key 단언을 마지막Master 통과로 계산하지 않음 |
| test_iam_mfa_management.py::test_actual_additional_master_and_legacy_scope / test_mfa_current_password_change_preserves_key_and_revokes_all_sessions | 추가Master/noSelf/기존scoped_account 제한·C3 현재암호/전세션철회 유지, 키보존 단언만 기능제거로 제외 |
| test_iam_mfa_management_authorization.py::test_final_recovery_actor_rechecked | key recovery 기능은 폐기하지만 idle/absolute/revoked actor 재검증은 reset·AB5 handoff의 password actor final-clock 사례로 이동. 원래세션기한·감사후확인 유지 |
| test_iam_mfa_management_gc.py::test_gc_skips_source_with_locked_child_then_cleans | 신규 MFA 발급 기능만 폐기. `test_retired_transient_gc_skips_locked_child_then_cleans`로 legacy consumed context를 잠근 독립 연결 때문에 source를 건너뛰고, 해제 후 정상 정리하되 durable case/audit/key를 보존하는 기존 의미를 검증 |
| test_iam_mfa_install.py::test_mfa_downgrade_preserves_each_fact; test_iam_mfa_management_migration.py::test_each_management_downgrade_guard | 원본revision검사 근거 보존. 새 `test_password_transition_forward_only_loss_guard`로 데이터/역사 있는0014 하향DDL전거부, 구13원문보존 확인 |
| test_iam_emergency_handoff_integrity.py::test_variants_nulls_parent_factors_and_history_downgrade | 새 legacy origin/parent typedFK, both→password 허용 subset·passkey-only 거부·foreign/null/잘못된parent·역사보존 검증으로 재작성 |
| test_iam_emergency_handoff.py::test_expired_source_gc_then_live_explicit_reissue; races::test_concurrent_same_parent_only_one_child | 원본만료 후 새30분·한부모한자식·현재Master/명시operation/ACK 무연장으로 유지 |
| test_iam_emergency_integrity.py::test_real_uv_then_reissue_rejects_old_completion; handoff_races::test_real_uv_proof_loses_to_reissue | 실제 password hash proof 준비→재발급 commit→옛proof 거부로 대체. UV 없이도 늦은proof의 source/generation 경계 유지 |
| test_iam_emergency_integrity.py::test_both_completion_failure_preserves_two_pending | 새both발급 기능은 폐기. legacy both migration 입력에서 password미완료 보존·key은퇴 구별 및 전환실패rollback으로 재작성 |

최소 신규 전환 검증 명단(계획): empty0013→0014, populated 모든 D분류, stagedhash 비승격, source/session/preauth 구token 전부거부, budget/failure/lease 불변, legacy FK 정리순서/locked-child skip·fresh snapshot/기존 capacity·C2 불변, keyonly retired/사건감사원문불변, unknown분류 전체rollback, audit실패rollback, 전환commitACK idempotent대사, schema/policy mismatch 시작거부, ProcessGuard 배타·DB 실제 대기/timeoutrollback, legacy both/password lineage의 explicit handoff 성공/passkey-only 실패, 전역 완전빈0014 왕복 positive와 일부라도 자료가 있는 downgrade pre-DDL 거부 negative.

기존 password reset 및 IAM013 clock/causal/privacy, I1/I2/W1/Workforce browser는 기존 실제 업무 흐름·권한·동시성 단언을 유지하고 fixture/로그인만 password-only로 재구성한다. native WebAuthn 기기 조작은 삭제하지만 trusted HTTPS/cookie/CSRF/fragment/명시 전달/ACK safeGET/자기철회·현재scope는 계속 실제브라우저로 검사한다. 신규 수집 수·최종 PG수는 **미실행·미확정**이며 과거614나179/243을 목표로 삼지 않는다. skip/xfail/timeout 완화로 대응하지 않는다.

## H. 채택한 기술 방향과 구현 전 조건

설계자 선택은 기존 bounded legacy-transient GC 유지, 새 password emergency case/source로 옛 factors FK 보존, policy2 marker/proof/parent 복합FK, 전역 완전 빈 DB에만 허용하는0014 하향이다. 새 사용자 정책 질문은 없다. 실제 DDL·구현·DB 실행과 최종 인수는 아래 진입 조건을 충족한 뒤 수행한다.

## I. AB5 운영 사실과 DB 준비 상태의 구별

‘모든 Master가 실제로 로그인할 수 없음’은 업무책임자의 승인과 별도 운영담당자가 보호된 절차로 확인할 사실이다. `password_hash IS NOT NULL`인 ACTIVE Master 수가0이어야 한다는 DB 조건으로 대체하지 않는다. 저장 hash가 있는 유일 Master도 암호를 잊었으면 AB5 대상일 수 있다. hash 존재는 암호를 알고 있음/현재 로그인 가능/본인 확인 완료의 증명이 아니다.

DB는 승인 범위·대상 ACTIVE Master·조직·snapshot/세대·원래 사건·단회성·실행자 분리와 기록을 검증한다. 보호된 사람 확인의 진위를 암호학적으로 증명한다고 보고하지 않는다. 실제 로그인은 항상 입력 암호 검증과 C2·상태/현재 역할 검사를 통과해야 한다. 전환 표의 durable hash는 저장 준비 사실만 뜻한다.

C5/A9의 정상 관리 경로는 실제로 현재 인증된 다른 Master/noSelf와 transaction 경계의 현재 권한을 근거로 보호한다. AB5의 운영 확인을 이 정상 관리 조건으로 막지 않는다. C2 일시 cooldown/일부 잠금만으로 AB5를 자동 시작하거나 예산·상태를 해제하지 않는다. 기존 비밀번호를 아는 마지막 Master의 C3는 별개다.

E-1 보완 경계: B→A에서는 role_epoch가 그대로여야 한다(전환 자체가 역할을 변경하지 않음). A→C의 target epoch는 장기 원본 보존과 별개이며 I2 의미를 유지한다. Actor의 요청별 epoch/session 검증과 target prepared proof의 최종 epoch 검증은 완화하지 않는다.

## J. 설계 마감 범위와 후속 진입 게이트

현재 마감은 정책·사용자 흐름·전환 방향 및 직접 영향 P0 상세 **제안**이다. G절은 직접 영향 테스트군 대응이며 기존614개 전수 node/모든 assertion 분류 완료가 아니다. 현재 collection·실행 수는 미확정이다.

미분류 테스트군이나 기능을 실제 삭제·대체하기 전에는 담당자가 그 영향과 보존할 보안 의미를 제출하고 root 검토를 받아야 한다. 기존 테스트 수를 맞추거나 broad skip/xfail로 처리하지 않는다. 이 증분 게이트를 거쳐 상세DDL/FK/GC 인수 및 실제 구현 범위를 확정한다. 이 문서 공표는 SQL 실행·migration 적용·전수 기능 구현 착수 또는 실제 원본 DB 전환 승인이 아니다. 현재 변경은 문서뿐이며 앱/테스트/DB/runtime은 변경·실행하지 않았다.

## K. 확정된0014 하향 loss guard: 전역 완전 빈 상태만

이 절이 기존 ‘일괄 downgrade 비지원’ 제안을 대체한다. 데이터가 있는0014는 DDL 이전 거부/forward repair, 완전히 빈 DB는0013으로 무손실 왕복을 허용한다. 빈 DB를 만들려고 행을 삭제·GC 강제·cascade purge하거나 summary를 zero로 덮어쓰지 않는다.

기존0001–0013의 CREATE TABLE을 읽어 확인한 **모두0행이어야 하는 실제 표**:

- `organization_organizations`
- `organization_branches`
- `iam_accounts`
- `iam_login_ids`
- `iam_admin_grants`
- `iam_sessions`
- `iam_security_states`
- `iam_budgets`
- `iam_attempts`
- `iam_preparations`
- `iam_credentials`
- `audit_events`
- `iam_passkeys`
- `iam_mfa_contexts`
- `iam_recovery_credentials`
- `iam_reset_credentials`
- `iam_emergency_cases`
- `iam_emergency_credentials`
- `workforce_trainers`
- `workforce_initial_snapshots`
- `workforce_registration_operations`
- `audit_workforce_initial_events`
- `iam_trainer_bindings`
- `iam_trainer_account_operations`
- `iam_trainer_setup_credentials`
- `audit_trainer_identity_events`
- `iam_trainer_role_grants`
- `iam_trainer_role_operations`
- `audit_trainer_role_events`
- `workforce_trainer_state_origins`
- `workforce_trainer_state_operations`
- `workforce_trainer_state_transitions`
- `audit_trainer_state_events`

추가0014 제안 표 중 `iam_policy_account_transitions`, `iam_password_emergency_cases`, `iam_password_emergency_credentials`, `audit_password_emergency_events` 역시0행이어야 한다. 후속 상세DDL에서 표가 추가되면 그 표도 정확히 포함해야 하며, 미분류 업무/auth/audit 표가 있으면 빈 상태 판정을 통과시키지 않는다. `audit_events`는 actor/target가 NULL인 실패 감사 한 행도 빈 조건을 깨뜨린다. revoked key, consumed/expired source, pending/success/failure attempt도 행이 남아 있으면 빈 조건을 깨뜨린다.

허용되는 데이터는 schema version metadata 및 다음 **정확한 singleton/zero-summary**뿐이다.

- `iam_installation`: id=1 정확히1행, organization_id=NULL, 새 policy marker/transition 참조가 예상0014 전환을 가리킴. 누락·추가행·다른 marker는 거부.
- `iam_security_control`: id=1 정확히1행. 별도 budget/attempt 행이 허용되는 뜻이 아님.
- `iam_policy_transitions`: 빈0013에서 새로 넘어온 전환 header 정확히1행, from1/to2·실제revision 일치, 영향을 받은 account/session/source/key/case/audit 등 명시 집계 전부0, 계정별 전환 행0. 비영(非零) 전환이력이 있으면 나중에 현재 테이블이 비어도 거부한다. 비영 이력을 지워 조건을 만들지 않는다.
- `alembic_version`: 대상 revision metadata만 존재. 이 metadata와 전환marker 제거는 완전빈 positive의 구조적 하향 절차이며 업무 기록 삭제가 아니다.

하향 절차는 현재 ProcessGuard 유지보수 조건 및 관련 모든 표의 일관된 DB lock을 확보하고 **전체 빈조건/FK 참조/zero-summary/marker를 먼저 검사**한다. guard가 모두 통과한 경우에만 신규 child FK/표→policy 추가 제약/컬럼→marker/header를 참조 역순으로 제거하고0013 schema를 복원한다. 새로운 schema/제약을 일부 지운 후 데이터 존재를 발견하는 순서는 금지한다. 원래13 revision raw는 수정하지 않는다. guard/DDL 실패는 transaction rollback이며 account/case/audit 자료 삭제로 우회하지 않는다.

### 기존 모듈 empty와 새 전역 empty의 테스트 구별

- `test_iam_password_reset_storage.py::test_reset_empty_roundtrip`는 MFA Master가 있는 fixture를 사용한다. reset 표가 비었다는 이유만으로0014→0013 positive로 전용하지 않는다. 원래0007 revision의 모듈 loss guard 의미는 해당 revision 경계에서 검증하고, 같은 자료로0014 하향을 시도하면 **negative**다.
- `test_iam_trainer_storage.py::test_blank_identity_tables_roundtrip`, `test_iam_trainer_roles_storage.py::test_actual_0011_backfill_roundtrip_preserves_live_auth_and_source`, `test_iam_mfa_management_migration.py::test_management_empty_roundtrip`도 각 원래 revision의 계약과 새0014 전역 정책을 구별한다. 모듈empty지만 admin/org/auth자료가 있는0014 하향은 거부한다.
- 기존0001–0013의 각각 loss guard 검사는 원래 revision까지 준비한 명시 migration fixture에서 검사한다. head0014를 거친 데이터 있는 상태를 억지로 낮추거나 구guard 통과를 위해 자료를 지우지 않는다.
- 신규 `test_password_transition_globally_empty_roundtrip`(제안): 업무/auth/audit행 없이 schema singleton만 존재하는0013→0014→0013→0014를 실제 테스트 DB에서 수행하고 표/제약/marker/zero-summary를 대조한다. 아직 실행하지 않았다.
- 신규 `test_password_transition_nonempty_rejected_before_ddl`(제안): 실제 FK를 만족시키는 최소자료를 종류별로 준비하고 위 각 표의 자료/비영transition summary/잘못된singleton 중 하나라도 있으면 거부하는 parameterized negative다. 실패 전후 revision·schema·row fingerprint를 대조한다. 지원하는 실제 제약을 무효화해 불가능한 orphan fixture를 만들지 않는다.
- 실제 실행 중 insert/발급과 하향 lock 대기를 독립 연결로 관찰하여, lock 후 fresh 검사가 커밋된 자료를 보고 거부하는지 검증한다. 강제SQL seed는 migration 입력 검증 용도로만 사용하며 일반 사용자 E2E를 대신하지 않는다.

위 명단은 소스에서 확인한 기존 표와 제안0014 표의 **설계 목록**이다. 실제 신규DDL 확정 시 FK/제약 이름과 모든 표를 다시 대조한 뒤 검증한다. 현재 SQL/DB/runtime/collection 실행은 없다.
