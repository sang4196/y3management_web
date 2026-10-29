# WORKFORCE-002 Trainer 업무 상태 제한 구현 계약

2026-10-30 제한 구현·독립 분할 검증·설계자 인수 완료. 기준 parent `d55db2ef1e60d9ad8efa92b656545b348d8ab61a`, branch `codex/workforce-trainer-state`. 아래 QA 초안은 제한 계약으로 승격했고 실제 구현·검증 및 인수를 완료했다. Product/OPEN/ADR와 전역 PROPOSED 상태는 변경하지 않는다.

현재 판정과 실제 실행은 [인수 결과](workforce-002-trainer-state-results.md) 및
[최소 근거](workforce-002-trainer-state-review.json)가 우선한다. fast131, 서버 PG206 보존+fresh109의 분할315,
fresh native225를 확인했으며 최종 단일315/전체576을 실행한 것은 아니다. 이하의 QA/PROPOSED/미실행 표현은
설계 작성 당시 이력이다. Product·ADR·전역 모듈 승인 범위를 추가하지 않는다.

상태 조합 승인 일관성:

- **no_account**: W0 Trainer registration is independent from login account issuance; state command creates no account
- **pending_setup**: I1-Q1 explicitly allows original still-valid setup source after reactivation; business reactivation must not require setup first
- **withdrawn_grant**: I2 regrant requires active Trainer, so business reactivation cannot require regrant first; reactivation never changes grant
- **disabled_account**: B2/A8 separate business state from account-wide block; state change cannot clear DISABLED or other independent blockers
- **home_inactive**: G1/G4/I1 distinguish existing Home from new assignment; no new Home assignment occurs

---

# W1 Trainer 업무 상태 계약 초안

QA 검토용 PROPOSED. Product 승인·구현 진입·검증 통과를 뜻하지 않는다. IAM-012 독립 전체 검증, 설계자 인수, 전담 커밋 완료 후 오케스트레이터의 명시적 기술 검토를 거쳐 저장소 명세로 승격한다. 이번 작성은 QA 파일 두 개에 한정하며 소스·테스트·migration·설정·lock·Git·trust 변경 및 runtime 검사는 수행하지 않았다.

## 근거와 범위

PR-005/021/026/029/030, BR-OPS-012/014/019, Product 결정 B1/B2 및 G1, I1-Q1을 따른다. BR-OPS-014 중간의 과거 재활성화 Actor 미정 문구보다 끝의 B1/B2 후속 승인이 우선한다. ARCH-001/002와 MB-001/008의 후속 관계·역사 사실 게이트를 일괄 종료하지 않는다.

Master는 자기 Organization, Branch Admin은 처리 시점 실제 Trainer Home 범위에서 기존 Trainer.active를 비활성화하거나 재활성화한다. 최소 상태 조회·화면·작업 결과 대사·typed 상태 이력과 감사까지 한 증분이다. 현재 Home 지점 자체가 inactive여도 기존 소속의 업무 상태 변경은 새 배정이 아니므로 허용한다. G1/I1과 일치하며 새 등록·배정의 active Branch 요건으로 확대하지 않는다.

계정 상태, grant, 독립 관리자 역할/Scope, Home, 비밀번호, Passkey, 보상, 담당 Pass, 과거 업무 사실은 바꾸지 않는다. 새 필수 사유·승인 단계·자동 재배정·기본급 0 또는 비례 계산은 없다. 좁힌 범위에 필요한 새 Product 질문은 없다. 기술 선택은 설계자 검토 사항이다.

## 상태 조합과 인증 효과

| 대상 | inactive 변경 | active 복귀 |
|---|---|---|
| 미연결 Trainer | 업무 상태만 변경, 계정 생성 없음 | 동일 |
| PENDING_SETUP | 설정 진행 보류, 원래 source 보존 | 원래 유효한 source로만 설정 가능 |
| ACTIVE + Trainer grant | Trainer 권한 중단 | 다른 인증 요건을 충족한 새 로그인 가능 |
| DISABLED | DISABLED 유지 | 계정 복구 없음 |
| I2 grant 회수 | grant false 유지 | grant 자동 재부여 없음 |
| 독립 관리자 겸임 | 유효한 관리자 권한·Scope·세션 유지 | Trainer 자격만 현재 사실에 따라 재평가 |

실제 true→false 전이 때, 현재 지원하는 독립 로그인 역할이 없는 연결 계정의 기존 AuthSession을 철회하는 기술안을 권고한다. 현재 독립 역할은 구현된 Master/Branch Admin이며 미래 Operator를 가정하지 않는다. 역할 독립성과 계정 로그인 가능 상태를 혼동하지 않는다. DISABLED 관리자 계정이라고 해서 관리자 역할을 제거하거나 세션을 되살리지 않는다. 현재 grant가 없더라도 독립 역할 없는 연결 계정의 잔존 세션은 실제 비활성화 때 철회 대상이다.

판정과 세션 변경은 IAM 공개 port를 통해 Service가 조정한다. Workforce가 IAM private SQL을 읽거나 변경하지 않는다. I2의 역할 변경 효과를 복사하지 않는다. account.row_version, security version, role_epoch는 증가시키지 않으며 Trainer 설정 source/기타 credential을 소비·교체하지 않는다. 관리자는 요청마다 현재 역할·Trainer 사실을 확인하므로 inactive Trainer 권한을 행사할 수 없지만 독립 관리자 인증은 유효하다.

재활성화는 철회 세션을 복구하거나 자동 로그인하지 않는다. 새 상태 변경도 없는 noop/동일 operation replay는 새 세션을 철회하지 않는다. 상태 version은 실제 전이 때만 정확히 +1이다.

## 진행 중 인증과 I1-Q1

원래 30분 source의 내용·계정 버전·만료를 비활성화/재활성화 동안 보존한다. inactive 상태의 최종 설정 검사는 실패하며 source를 소비하지 않는다. 재활성화 뒤에도 미소비·미만료 source만 사용할 수 있고 만료 연장이나 자동 재발급은 없다.

로그인은 최종 잠금 아래 현재 active 및 기존 계정/grant/credential 조건으로 선형화한다. 로그인 커밋이 비활성화보다 먼저면 생성 세션은 이어지는 비활성화 철회 대상이다. 비활성 상태 동안 최종 검사하면 새 세션을 만들지 않는다. 비활성화와 재활성화가 모두 커밋된 뒤 최종 검사한다면 여전히 유효한 진행 중 비밀번호 증명은 현재 조건을 모두 만족할 때 새 세션을 만들 수 있다. 이는 옛 쿠키 복원이 아니다. 이 불변식에 별도 상태 epoch는 필요하지 않다. I1 설정 증명도 source 원래 조건과 최종 active를 확인하며 일시 비활성 이력만으로 source를 무효화하지 않는다.

## UoW와 잠금

사전 읽기 UoW에서 현재 Scope와 IAM 공개 binding hint를 얻고 닫는다. 본 UoW의 순서는 installation → 정렬된 actor/target IAM accounts → 정렬된 해당 AuthSessions → 필요할 때 credentials → 현재 Branch SHARE → Trainer UPDATE다. W1은 credential 변경이 없어 credential 잠금을 생략한다. 다른 경로와의 교차 잠금 순서를 바꾸지 않는다.

본 UoW의 installation/account 잠금 뒤 binding을 재검증한다. 미연결 hint 뒤 연결이 생겼거나 대상이 달라졌으면 충돌로 종료하여 새 요청으로 재조회한다. Branch/Trainer 잠금을 잡은 뒤 대상 account 잠금을 늦게 획득하지 않는다. 미연결 대상은 actor 계정/세션만 잠그며 IAM 계정을 만들지 않는다. actor==target은 유효한 관리자여야 하므로 독립 역할 보존 경로이며 자신의 관리 세션을 철회하지 않는다.

W0는 installation/actor 인증 → Branch → Trainer 생성/확인, I1/I2는 installation/정렬된 계정·세션 → credentials → Branch → Trainer, currentprincipal/C3 및 설정 완료는 IAM 잠금 → Trainer SHARE 순서를 유지한다. W1의 Trainer UPDATE와 기존 SHARE가 인증의 현재 상태 검사를 직렬화한다. 실제 구현 전 이 교차 그래프와 I2 binding 생성 경합을 코드 수준으로 재검토한다.

현재 관리 인증/MFA·CSRF, Org/Home, Trainer version을 검증한다. 상태 변경·대상 세션 철회·operation receipt·상태 이력·typed audit는 같은 UoW다. 마지막에는 모든 현재 사실과 감사 작업을 마친 뒤 DB clock으로 actor의 원래 idle/absolute 기한과 현재 유효성을 검사한다. 먼저 last_activity를 갱신하여 만료를 숨기지 않는다. 기존 authenticate 내부의 이른 clock만으로 충분하다고 가정하지 않는다. 기존 TrainerRolesPort.snapshot(authentication)과 confirm_actor(snapshot, self_change=False)를 재사용한다. 새 일반 인증 계층은 만들지 않는다. 어느 감사/최종 확인 실패든 전체 rollback이다. inactive 전이 자체가 겸임 actor의 관리자 Scope를 무효화하지 않는다.

## 최소 API와 화면 제안

제안 경로는 POST /admin/trainers/{trainer_id}/state, 입력은 desired_active, expected_trainer_version, operation_id다. 아래 snake_case 공개 DTO 계약을 따른다. account 상태/role/Home 입력은 받지 않는다. 기존 Trainer 상세에 active/version과 현재 허용 동작을 노출하고 GET /admin/trainer-state-operations/{operation_id}로 ACK 유실을 대사한다. 작업 조회는 현재 실제 대상 Scope를 다시 확인한다.

canonical receipt는 org/operation/target/요청 payload/원래 결과 version·changed를 저장한다. 같은 operation과 같은 payload는 현재 인가 후 원래 결과를 반환하고 변이를 반복하지 않는다. 같은 operation의 다른 payload는 409다. 새 operation의 stale expected version은 desired 값이 현재와 같아도 409다. 동일 version의 동일 상태는 changed=false receipt만 남기며 상태 이력/세션 철회를 만들지 않는다. 현재 상태는 원래 receipt와 별도 조회하여 오래된 결과를 현재 사실로 오인하지 않게 한다.

인증 실패 401, 지원 역할 불가 403, 현재 Scope 밖/없는 대상 404, version/operation 충돌 409, 입력 오류는 기존 422 계약을 따른다. 오류에 타 Org·계정 credential·source를 노출하지 않는다. 역할 변경과 업무 상태 버튼은 구분하고 대사 전 operation_id를 버리지 않는다. 비활성화 중 유효 I1 링크는 소비된 링크처럼 지우지 않고 원래 만료와 일시 사용 불가를 표시한다. 재활성화 후에도 만료면 명시적 I1 재발급 경로를 사용한다.

## 이력과 migration 제안

다음 forward migration 번호는 현재 0012 다음을 기준으로 실제 진입 시 확인한다. 기존 Web W0 Trainer는 migration 시점의 observed_active/observed_version/observed_at을 legacy_observation으로 기록한다. 이는 C# 운영 데이터 이관이 아니다. 과거 활성 시작일이나 생성일이 아니며 과거 actor/상태 전이를 만들어내지 않는다. 원래 생성일을 알아도 과거 상태를 역산하지 않는다.

신규 W0 등록은 실제 등록 시점 active 초기 사실을 registered 유형으로 기존 등록/보상/감사 UoW에 함께 기록한다. 이후 실제 변경은 before/after active와 version, operation, 현재 actor 역할/Home, 대상 Trainer/nullable 연결 account, DB 기록 시각을 typed transition 및 audit에 남긴다. 감사에는 인증 비밀을 기록하지 않는다. 기록 시각은 transaction 내 관찰 시각이며 정확한 commit timestamp로 주장하지 않는다. 전이 순서는 version을 사용한다. 미래 Home 변경 등도 공유 row_version을 올릴 수 있으므로 상태 이벤트 간 version이 항상 연속이라고 가정하지 않는다.

operation은 Org 내 고유하며 실제 대상과 Org 일치를 제약한다. 전이 이력은 operation당 한 건이며 noop은 전이 이력이 없다. 기존 데이터와 credential/session/version을 보존한다. migration의 잠금은 installation을 먼저 획득하고 필요한 Trainer/history 테이블을 일관된 순서로 보호하며 live writer와 교차 그래프를 검증한다. IAM 데이터를 migration 편의상 갱신하지 않는다.

downgrade는 순수 legacy 관찰만 존재하고 현재 상태/version도 해당 관찰과 일치할 때만 관찰 구조 제거를 허용하는 안이다. 새 registration 초기 사실, operation 또는 실제 transition이 하나라도 있거나 현재 사실과 baseline이 달라졌다면 DDL 전에 거부한다. 손실을 숨기기 위해 이력을 삭제하거나 과거 상태로 되돌리지 않는다. 향후 PT의 과거 특정 시점 상태가 필요하면 legacy 관찰 이전은 unknown이며 별도 역사 사실 게이트를 유지한다.

## 인수 검증 계획 — 실행하지 않음

기존 pytest/fixture, 소유권 확인된 전용 DB, 실제 native 브라우저 흐름을 사용한다. 별도 실행 관리 도구를 만들지 않는다.

- 실제 관리 API로 미연결/PENDING/ACTIVE/DISABLED/회수 grant 조합을 전이하고 IAM·Home·보상 불변을 비교한다. Master/Home BA 허용, 외부 Scope 404, inactive Home 허용을 검증한다.
- Trainer-only 두 기존 쿠키의 영구 거부와 재활성화 후 새 로그인, 겸임 관리자 및 actor==target의 관리자 세션 유지를 검증한다.
- I1 source 원본/version/만료를 전후 비교하고 inactive 설정 실패, 원래 만료 내 재활성화 성공, 만료 후 실패를 검증한다.
- 독립 연결의 causal barrier로 로그인 완료 전후 및 두 전이 이후 최종 검사, I1 설정, I2 역할/binding, C3/currentprincipal과의 양방향 잠금 순서를 검증한다. 시간 sleep만으로 경합 성공을 추정하지 않는다.
- stale version, 동일 operation replay, noop 이후 생성된 세션 미철회, ACK 유실 대사, current Scope 변경 뒤 조회 거부를 검증한다.
- audit 실패와 마지막 idle/absolute 만료를 barrier로 유발해 state/history/receipt/session 모두 rollback됨을 증명한다.
- 실제 0012 데이터에서 forward 적용 후 legacy 관찰과 인증 데이터 보존, 신규 등록 초기 사실, downgrade 무손실 허용/손실 거부를 검증한다.
- native 화면에서 실제 actor의 상태 변경·겸임 관리 유지·일시 보류 source·ACK 대사를 검증한다. HTTP TestClient를 native 보안 검사로 보고하지 않는다.

IAM-012 기존 전체 검증과 W1 향후 검증은 별도다. 이 초안은 검사 수나 성공을 주장하지 않으며, S1 로그인 보호 AST 등 동결 경계 변경은 현재 허용하지 않는다.

## 최종 검토용 공개 계약 상세

다음 신규 이름은 구현 제안이며 현재 코드에 이미 존재한다고 주장하지 않는다. existing 표시는 실제 공개 port를 읽어 확인했다. Service가 모듈 간 UoW를 조정하고 다른 모듈의 adapter나 SQL을 호출하지 않는다.

### DTO와 공개 port

HTTP JSON의 필드는 snake_case다. `TrainerStateRequest(operation_id: UUID, desired_active: bool, expected_trainer_version: int)`는 추가 필드를 거부하고 bool/int 강제 변환을 허용하지 않는다. version은 양수다. Trainer와 Org는 경로와 인증에서 얻으며 요청 body로 인가를 결정하지 않는다.

`TrainerStateResult(operation_id: UUID, trainer_id: UUID, changed: bool, committed_active: bool, committed_trainer_version: int, current_state: TrainerIdentityFact)`는 원래 커밋 결과와 현재 사실을 구분한다. current_state는 기존 `trainer_id, organization_id, home_branch_id, active, version`이다. 조회에 연결 account의 인증 비밀이나 전체 감사 이력을 포함하지 않는다. 응답의 changed는 원래 operation의 결과이며 replay에서도 변하지 않는다. 최초 적용 여부는 내부 반환 change의 존재로 판단한다.

| 소유 port | 입력 → 결과 | 책임 |
|---|---|---|
| existing IAMPort.trainer_binding | org, trainer → TrainerBinding 또는 None | 사전 hint 및 본 UoW binding 재확인 |
| existing IAMPort.authenticate | token, management=True, target=account_id 또는 None, touch=False → Authentication | 기존 정렬된 account/session 잠금 및 관리자 인증 |
| existing IAMPort.account_roles | account_id → AccountRoles | IAM이 제공하는 admin/binding/grant 현재 사실; Workforce private 조회 없음 |
| existing TrainerRolesPort.snapshot | Authentication → RoleActorSnapshot | 원래 actor 계정·세션·키 사실 및 idle/absolute 기한 저장 |
| existing TrainerRolesPort.confirm_actor | snapshot, self_change=False → None 또는 401 | 마지막 모든 읽기 뒤 DB clock으로 원래 actor의 불변성과 기한 확인 |
| proposed IAMPort.revoke_trainer_only_sessions | binding: TrainerBinding → int | 이미 account/session 잠금을 확보한 상태에서 binding 동일성·AccountRoles.admin 재확인. admin이면 0, 아니면 아직 미철회인 target 세션만 철회하고 개수 반환 |
| existing WorkforcePort.lock_identity | organization_id, ident, exclusive=True → TrainerIdentityFact | 실제 현재 Home/state/version 잠금 |
| proposed WorkforcePort.state_operation | caller: Caller, operation_id: UUID → TrainerStateResult 또는 None | 저장된 target의 현재 Org/Home Scope에서 최소 receipt 조회 |
| proposed WorkforcePort.change_state | caller: Caller, branch: ScopedBranchFact, trainer: TrainerIdentityFact, request: TrainerStateRequest → tuple[TrainerStateResult, TrainerStateChange 또는 None] | current Scope/version·canonical replay 확인, 실제 변경 및 이력/receipt 쓰기 |
| proposed WorkforcePort.confirm_state | caller: Caller, result: TrainerStateResult → None | 같은 잠금 아래 current fact 및 receipt 불변 확인; 다른 모듈 호출 없음 |
| proposed AuditPort.append_trainer_state | event: TrainerStateEvent → None | typed allowlist 감사 쓰기; 실패는 전체 UoW rollback |

`TrainerStateChange(organization_id, operation_id, trainer_id, before_active, after_active, before_version, after_version, recorded_at)`를 내부 immutable DTO로 제안한다. replay/noop은 change=None이므로 세션 철회와 audit를 호출하지 않는다. 실제 false 전이에서만 Service가 IAM 철회 port를 호출한다. 이 port 자체는 상태 전이 권한을 발급하지 않으며 Service의 실제 change가 선행조건이다. int 결과는 내부 검증용이며 외부 API에 필요 없이 노출하지 않는다.

`TrainerStateEvent`는 `organization_id, operation_id, trainer_id, account_id: UUID | None, actor_id, actor_role, actor_branch: UUID | None, target_home, before_active, after_active, before_version, after_version, recorded_at`만 받는다. actor_role은 MASTER/BRANCH_ADMIN이다. 신규 등록 초기 사실은 WorkforcePort.register 내부에서 기존 등록 operation과 함께 저장하고 기존 AuditPort.append_trainer_registered를 유지한다. 상태 전이 감사 API에 가짜 등록 전이를 만들지 않는다.

W1의 actor snapshot은 관리 인증/MFA·CSRF 이후, 변이 이전에 획득한다. 최종 Branch/Trainer/receipt 확인과 audit를 모두 완료한 후 `confirm_actor(snapshot, self_change=False)`를 마지막 검증으로 호출한다. actor==target이어도 항상 False다. I2의 self_change=True에만 허용된 revoked=True/epoch+1 예외를 W1에서 사용하지 않는다. actor IAM account/role/key/세션 사실 변경을 허용하지 않는다. 별도 target Trainer-only 세션 철회만 앞의 명시적 효과로 수행한다. 마지막 확인 전 activity touch는 금지한다. 새 epoch/범용 인증 추상화는 추가하지 않는다.

전체 상태 감사·이력 열람 endpoint는 추가하지 않는다. 승인 범위는 현재 Scope에서 현재 상태와 특정 operation receipt를 읽는 데 한정된다.

### schema 구체안과 보존 목록

새 구조 이름 역시 제안이다. 모든 FK는 기본적으로 삭제 연쇄 없이 보존한다. Org 복합 FK로 타 Org 참조를 막는다. 불변 history를 일반 관리 명령으로 UPDATE/DELETE하지 않는다.

- `workforce_trainer_state_origins`: trainer_id PK, organization_id, origin, active, trainer_version, recorded_at, registration_operation_id nullable. `(organization_id,trainer_id)` → workforce_trainers. `(organization_id,registration_operation_id,trainer_id)` → workforce_registration_operations. `origin IN ('legacy_observation','registered')`, `trainer_version>0`, registered일 때 registration_operation_id NOT NULL/active=true/trainer_version=1, legacy일 때 registration_operation_id IS NULL CHECK. Trainer당 origin 한 건. legacy 시간은 migration 관찰, registered 시간은 실제 등록 기록이다.
- `workforce_trainer_state_operations`: `(organization_id,operation_id)` PK, trainer_id, actor_id, target_home, canonical_version, fingerprint, desired_active, expected_trainer_version, before_active, before_version, committed_active, committed_trainer_version, changed, recorded_at. `(organization_id,operation_id,trainer_id)` UNIQUE. Trainer/actor/Home은 각각 같은 Org의 workforce_trainers/iam_accounts/organization_branches로 FK. `canonical_version=1`, fingerprint 길이 32, expected/before/committed version 양수, expected=before, desired=committed CHECK. changed이면 before_active<>committed_active 및 committed_version=before_version+1, 아니면 active/version 동일 CHECK. canonical fingerprint는 target trainer_id와 입력 DTO·canonical_version을 포함하며 caller 신원은 포함하지 않는다. 다른 현재 인가 actor가 같은 요청을 대사할 수 있지만 최초 actor는 보존한다.
- `workforce_trainer_state_transitions`: `(organization_id,operation_id)` PK, trainer_id, before_active, after_active, before_version, after_version, recorded_at. `(organization_id,trainer_id,after_version)` UNIQUE. operation의 Org/operation/Trainer FK 및 before/committed active/version/changed=true를 일치시키는 복합 FK를 둔다. 이를 위해 operation에 대응 복합 UNIQUE와 transition의 `changed boolean NOT NULL CHECK(changed)`를 둔다. `before_active<>after_active`, `before_version>0`, `after_version=before_version+1` CHECK. noop operation에 transition을 연결할 수 없다.
- `audit_trainer_state_events`: id PK, `(organization_id,operation_id)` UNIQUE, 위 TrainerStateEvent의 필드. transition의 Org/operation/Trainer/before·after 상태/version과 복합 FK로 동일 사실을 강제한다(transition에 대응 UNIQUE). actor의 Org/account FK, actor_branch와 target_home의 Org/Branch FK. nullable account_id는 `(organization_id,account_id,trainer_id)` → iam_trainer_bindings FK로 실제 연결을 제한한다. MASTER이면 actor_branch IS NULL, BRANCH_ADMIN이면 actor_branch=target_home AND actor_branch IS NOT NULL CHECK. active flip/+1 CHECK도 유지한다. NULL account는 당시 미연결일 때 Service가 기록한다.

FK는 잘못 연결된 감사/전이를 막지만 모든 operation에 감사가 존재한다는 역방향 보장을 단독 제공하지 않는다. 실제 변경에 transition+audit를 빠짐없이 쓰는 Service UoW, `confirm_state`, 실패 주입 검증으로 보장한다. 기록 시각은 한 명령의 DB 시각을 공유하되 commit 시각으로 주장하지 않는다.

기존 `workforce_trainers`는 실제 명령의 active/row_version 외 필드를 보존한다. `workforce_initial_snapshots`, `workforce_registration_operations`, `audit_workforce_initial_events`의 기존 데이터는 그대로 둔다. `iam_accounts`, `iam_trainer_bindings`, `iam_trainer_role_grants`, I1/I2 operations, `iam_trainer_setup_credentials`, `iam_security_states`, Passkey·암호/reset/recovery 자료는 변경하지 않는다. `iam_sessions`는 명령 시 위 한정 철회만 허용하고 migration에서는 전혀 바꾸지 않는다. 기존 identity/role audit 역시 보존한다.

forward는 하나의 transaction에서 설치 잠금 획득 → workforce_trainers를 writer와 충돌하는 테이블 잠금으로 고정 → origins/operations → transitions → audit 순서로 제약을 포함해 생성 → 기존 Web Trainer 전체를 legacy_observation으로 삽입 → 건수·Org/현재 active/version 대응 확인 후 commit한다. W0 등록과 모든 관리 writer가 installation 우선 순서를 공유하는지 확인한 뒤 실행한다. 신규 등록 코드는 migration 적용 후에만 새 origin을 쓴다. C# 데이터 추출·변환·수입 작업은 없다.

downgrade는 같은 installation/Trainer 잠금과 새 테이블 쓰기 차단 잠금을 획득한 뒤 새 registered origin/operation/transition/audit 존재 또는 legacy baseline의 누락·여분·현재 active/version 불일치를 확인한다. 하나라도 있으면 어떤 DROP보다 먼저 실패한다. 모두 순수 관찰임을 확인한 경우 audit → transitions → operations → origins 역순 DROP 후 commit한다. 기존 IAM/W0 데이터와 제약을 제거·재작성하지 않는다. 예상 실패는 데이터 보존 결과를 실제 DB에서 검증한다.

공유 Trainer row_version은 미래 profile/Home 변경도 증가시킬 수 있다. 각 단일 전이는 +1이지만 서로 다른 상태 전이 사이의 version 간격은 허용한다. legacy 관찰 이전은 unknown이며 origin을 최초 활성일로 보여주지 않는다.

### 카드·패널 갱신과 링크 생명주기

상태 명령 응답 또는 operation 대사 완료 후 현재 Trainer 상세를 읽어 기존 카드의 `t.active`, `t.version`을 갱신한다. 열린 계정 패널은 기존 account state, 역할 패널은 기존 role state를 함께 새로 읽고 각 expected version/허용 버튼을 최신 사실로 교체한다. 원래 committed 값으로 더 최신 current 값을 덮어쓰지 않는다. 조회 실패나 불일치 시 조작을 잠시 막고 재조회하며 이전 version으로 후속 명령을 전송하지 않는다.

클라이언트가 보유한 I1 링크는 Trainer/account 동일성, account_version, 현재 PENDING_SETUP/source 상태와 원래 initial_setup_expires_at이 모두 일치하고 아직 미만료일 때만 유지한다. W1 inactive만 달라졌으면 원래 만료 그대로 보존하고 일시 보류로 표시한다. 계정 version/source 만료·소비·재발급·역할 변경으로 유효 조건이 달라지면 기존 링크를 폐기한다. raw source를 조회 API가 다시 반환하거나 receipt에 저장하지 않는다. I2 역할 변경으로 링크가 폐기되는 기존 UI 계약은 유지한다. 재활성화가 폐기한 링크를 복원하지 않는다.

### 기존 회귀 node 재사용 범위

아래는 읽어서 존재를 확인한 회귀 범위이며 실행 결과가 아니다. 새 검증은 앞 절의 실제 W1 관리 흐름/현재 상태 선형화/출처 보존/이력 제약에 집중하고 전체 조합의 단순 곱으로 늘리지 않는다. 기존 SQL fixture active 변경 검사는 보존하되 W1 API 인수의 대체물로 쓰지 않는다.

- W0 등록·초기 사실/원자성: `backend/tests/test_workforce.py::test_exact_registration_inactive_g1_and_replay`, `::test_audit_failure_rolls_everything_back`; `backend/tests/test_workforce_guards.py::test_each_persisted_step_failure`; `backend/tests/test_workforce_integrity.py::test_commit_ack_loss_replay`, `::test_migration_roundtrip_and_information_guard`. 새 등록 origin 실패도 기존 전체 rollback 경로에 통합한다.
- 현재 Scope·기한: `backend/tests/test_workforce_guards.py::test_actual_home_reauthorization`, `::test_late_absolute_only`; `backend/tests/test_workforce_integrity.py::test_late_idle_check_not_rescued_by_touch`; `backend/tests/test_iam_trainer_roles.py::test_final_actor_snapshot_read_crosses_original_deadline`. W1 snapshot final clock이 같은 실패를 놓치지 않는 새 causal 사례를 추가한다.
- I1 보존: `backend/tests/test_iam_trainer.py::test_active_at_all_three_phases`, `::test_inactive_home_allows_all_initial_phases_and_login`, `::test_inactive_cookie_is_rejected_on_every_self_path`, `::test_actual_w0_setup_login_self_change_logout`. source 원본 비교와 비활성→재활성 후 원래 만료 내 설정은 W1 API로 새 검증한다.
- I2 효과 분리: `backend/tests/test_iam_trainer_roles.py::test_first_link_self_requires_new_uv_and_preserves_admin`, `::test_pending_withdraw_regrant_explicit_new_source`; `backend/tests/test_iam_trainer_roles_races.py::test_role_commit_ack_replay_preserves_later_login`, `::test_prepared_password_login_cannot_cross_role_epoch`; `backend/tests/test_iam_trainer_roles_causal.py::test_prepared_initial_hash_cannot_cross_committed_role_cycle`, `::test_initial_reissue_and_role_share_observed_lock_chain`. I2 역할 epoch 차단은 유지하면서 W1의 일시 inactive 이력만으로 증명을 무효화하지 않는 차이를 새 사례로 증명한다.
- native 재사용: `backend/tests/test_workforce_browser.py::test_workforce_native`, `backend/tests/test_iam_trainer_browser.py::test_trainer_native`, `backend/tests/test_iam_trainer_roles_browser.py::test_trainer_roles_native`. 기존 fixture/manifest 흐름에 W1의 카드·계정·역할 동시 갱신, 유효 링크 보류/무효 링크 폐기, ACK 대사를 추가한다. 검사 수·성공 여부는 실제 구현·실행 이후에만 기록한다.


## 구현 반영 및 검증 기록 경계 (2026-10-30)

구현은 기존 `WorkforcePort`/`IAMPort`/`AuditPort`와 `Service`/공유 UoW를 사용한다.
새 revision은 `0013_workforce_trainer_state`이며 기존 migration 파일은 수정하지 않았다.
`TrainerRolesPort.snapshot`/`confirm_actor(self_change=False)`를 재사용하고 신규 일반 인증 계층은 없다.
현재 상태/operation API와 화면만 제공하며 상태 감사 전체 조회 권한을 추가하지 않는다.

기존 하위 migration guard 회귀는 실제 parent `d55db2ef1e60d9ad8efa92b656545b348d8ab61a`의
HTTP 등록 경로로 만든 W0 자료를 관찰 baseline으로 올린 뒤 실행한다. 현재 앱과 parent 앱 lifespan은
순차 실행하며 ProcessGuard를 완화하지 않는다. 기존 Alembic env의 오류 비노출도 유지한다.
CLI nonzero/보존 단언과 별도로 실제 revision 함수를 같은 DB에서 순서대로 실행하여 정확한 DB guard를
관찰하고 트랜잭션 전체를 rollback한다. 새 상위 guard의 거절을 하위 guard 통과 증거로 쓰지 않는다.

만료·소비된 초기 source는 기존 credential GC가 정리할 수 있다. W1이 원래 source/version/만료를
변경하지 않는 사실은 GC 이전에 대조하며, 만료된 source가 재활성화로 다시 사용되지 않음을 확인한다.
유효 source 보존을 만료 후 영구 보존 정책으로 확대하지 않는다.

개발 대상 실행과 독립 인수는 분리한다. 실제 node·실패 원인·정리 receipt·native 항목 및 최종 동결은
해당 QA 결과와 후속 검증 결과 문서에 기록하며, 이 계약만으로 실행 성공을 주장하지 않는다.


## 인수 후 UI 정합성 보완

실제 발급 전 GET 응답이 발급 후 도착하면 새 링크를 지우는 동작을 이전 앱에서 재현했다. 현재 화면은
패널별 최신 조회만 반영하고 쓰기 시 이전 조회를 무효화한다. 완료 호출자는 최신 조회 완료까지 기다리며,
Trainer 버전이 낮은 상세 응답으로 현재 활성 상태를 되돌리지 않는다. 계정·역할·상태 패널의 허용 버튼과
링크 보류/재사용은 현재 사실을 사용한다. 실제 source 소비·계정 버전·만료 불일치일 때의 링크 폐기는 유지한다.
서버 업무 Python/SQL은 이 UI 보완 전후 동일하다. 원래49개 native 조건을 그대로 두고 실제 발급 전/비활성화 전
응답의 지연 전달을 추가 검증했다. 최초 독립 실패의 정확한 통신 순서를 새 재현으로 확정한 것은 아니다.
