# IAM-011 — 실제 Trainer의 신규 로그인 계정

2026-10-27. **설계자 제한 계약 검토 완료·r3 인증·인가 경계 복원 개발 동결, 독립 검증 대기 — 전역 ADR/모듈 승인 아님**.
기준 HEAD `4deb779b622f34d3aac17c30259b47faf781f629`, branch `codex/iam-trainer-login`.
[Product I1 승인](../product/product-decisions.md#review-20261026-i1)의 실제 답변 “전부 1”을 입력으로 한다.
정책 승인과 아래 API/저장/잠금 계약 승인은 구분한다. 이 문서는 실행 결과가 아니다.

## 1. 근거와 최소 완료 단위

[Product](../product/README.md), BR-OPS-012/014/016/019, PR-001/021/026/029/030,
A4/B2/G1/C3/AB4/E5 및 [ADR-0004](../decisions/0004-authentication-session.md)를 따른다.
[ADR-0001](../decisions/0001-backend-stack.md)–[0003](../decisions/0003-foundation-tooling.md)의
기술/모놀리스/동기 UoW·검증 기반과 현재 dependency/lockfile을 유지한다.
[모듈 경계](module-boundaries.md)·[데이터/트랜잭션](data-and-transactions.md)의
공개 port 조합 원칙을 따르고 타 모듈 private SQL 예외를 추가하지 않는다.

[W0 결과](workforce-001-initial-registration-results.md)와
[판정](workforce-001-initial-registration-review.json)은 실제 Trainer 등록의 선행 근거다.
과거 W0 fast122/PG419/native188은 기존 기준선이며 IAM-011 검사 결과가 아니다.

완료 흐름: 실제 W0 명령으로 Trainer 등록 → 현재 UV 관리자가 신규 계정 발급 → 다른 수신자
브라우저에서 직접 최초 암호 설정 → Trainer ID/암호 로그인 → 최소 `/auth/me` → C3 본인 암호 변경과
모든 자기 세션 철회 → 새 암호 로그인 → logout 후 옛 쿠키 거부.
계정·Trainer/Caller를 fixture 주입이나 수동 DB 수정으로 대신한 경로를 이 완료 흐름으로 인정하지 않는다.

포함: 신규 계정/명시적 Trainer binding, 초기 링크 발급·재발급·소비, 관리 범위 내 최소 상태/operation 조회,
서버 역할별 인증 강도, 매 요청 현재 Trainer 상태, 본인 암호 변경, typed 감사, 실패·ACK 불명·경합 검증.
제외: I2 기존 계정 역할 추가/회수/재연결·일반 roleless 정책, Operator,
분실 암호 reset/Trainer Passkey 등록·복구, Home 이동/활성 전이 명령,
회원/PT/보상/정산·계정 관리 권한 확대 및 실운영 인수.
E5의 기존 역할 관리 Actor/Scope 승인을 되돌리지 않으며 이번 I1에 구현하지 않을 뿐이다.

## 2. 확정 정책과 상태표

| 행위 | 계정/연결 | Trainer | Home Branch | 추가 조건 |
| --- | --- | --- | --- | --- |
| 신규 발급 | 연결 없음, 사용 가능한 새 Login ID | active | 활성/비활성 모두 | 현재 Master 조직 또는 실제 현재 Home의 Branch Admin, UV |
| 초기 링크 재발급 | 기존 연결의 PENDING_SETUP | active | 활성/비활성 모두 | 같은 현재 관리 Scope, 명시 재발급, expected account version |
| 최초 설정 완료 | PENDING_SETUP, 동일 binding, 미소비·유효 source | active | 활성/비활성 모두 | 수신자의 준비 CSRF와 새 암호 정책 |
| Trainer-only 로그인/기존 인증 사용 | ACTIVE, 유효 binding·epoch/session | active | 활성/비활성 모두 | 암호 증명/세션 보안 조건 |
| 관리자 겸임의 관리 인증 | 독립 현재 admin grant | inactive여도 독립 관리 권한 유지 | 관리 Scope 원본 사용 | mfa 모드에서 password_uv와 유효 key 필수 |
| 상태/과거 operation 조회 | 현재 관리 Scope 내 실제 연결 | 비활성도 조회 가능 | 활성/비활성 모두 | no-touch/no-GC, 비밀 없음 |

한 Trainer에 한 account, 한 account에 한 Trainer다. PENDING_SETUP/ACTIVE/DISABLED 기존 연결을
신규 계정으로 대체하지 않는다. 이름/전화/Login ID 일치로 동일인을 자동 연결하지 않는다.
발급 뒤 비활성화되면 최초 설정 완료를 거부하되 기존 연결과 원래 만료를 유지한다.
재활성화 뒤 원래 링크가 아직 유효하면 사용할 수 있다. 자동 재활성화·만료 연장 없음.

A4 링크30분/단회/재발급 시 전 링크 무효화, 모든 역할 idle30분/absolute8시간,
기존 Login ID 정규화·암호/NFC/차단목록·hash admission·C2 budget을 유지한다.
현재 `iam.infrastructure.login_id`의 승인된 `[A-Za-z0-9][A-Za-z0-9_.-]{2,63}` 및 소문자 정규화를
그대로 사용한다. 영문/숫자라는 요약을 이유로 기존 `_ . -` 허용을 삭제하지 않는다.
관리자 UV 의무를 Trainer-only에 확대하지 않고, 관리 grant가 있으면 서버가 UV를 강제한다.

## 3. 현재 코드의 변경 지점과 공개 계약

모든 아래 항목은 후속 구현 범위 제안이며 지금 코드를 변경하지 않는다.

| 경로·현재 함수 | 구체 변경 계약 |
| --- | --- |
| `backend/src/y3management/iam/public.py` Caller/Authentication/IAMPort | admin Scope와 Trainer binding을 구분한 immutable 값, 인증 audience·잠금·최종 확인 port 추가 |
| `iam/infrastructure.py` `_account`, `authenticate`, `login`, `complete`, `change_password` | 명시적 binding 조회, 역할별 assurance, Trainer 전용 초기 source 및 C3 철회; Workforce SQL 금지 |
| `iam/mfa.py` `begin_login`, `begin_setup`, `register`, `authenticate` | 현재 admin grant 필수 확인. Trainer source/비관리 계정이 기존 ceremony로 진입하는 우회 거부 |
| `iam/security.py` `_guard`, `release` | 신규 Trainer 초기 source의 GC 및 참조 보존 조건 추가. 기존 종류 `credential`/30분 capacity 재사용 |
| `workforce/public.py`, `application.py` | `lock_identity(org, trainer_id, *, exclusive=False)` 공개. 기존 `Repository.identity(..., lock=True)`를 확장해 SHARE/UPDATE 모드를 명시 |
| `workforce/infrastructure.py` `Repository.identity` | 명시 잠금 모드로 자신의 Trainer 행만 읽음. org/id 일치·최소 fact만 반환 |
| `use_cases.py` Service | 공통 self principal 조합, 발급/재발급/status/complete/login 최종 확인; IAM·Workforce·Organization·Audit public port만 사용 |
| `uow.py` Work/UnitOfWork.open | 기존 같은 DBSession 조립 유지. 새 adapter를 별도 만들 필요 없이 IAMPort 확장. commit_observer 사용 |
| `audit/public.py`, `audit/infrastructure.py` | `TrainerIdentityEvent`와 `append_trainer_identity` typed port·전용 저장 추가 |
| `http.py` login/me/csrf/logout/password 및 UI | 기존 admin response 유지, 서버 login 결과로만 분기; Trainer 발급/초기 설정/자기 신원 화면 추가 |

구체 값:

- `TrainerBinding(account_id, organization_id, trainer_id, version)`은 IAM 원본이다. I1 binding.version=1,
  update/delete 명령 없음. admin grant 없음은 binding의 대체 증거가 아니다.
- `AccountRoles(account_id, organization_id, admin_scope, admin_branch_id, trainer_binding)`를
  IAM이 자기 테이블에서 구성한다. `Caller.branch_id`는 기존 관리자 Branch 의미를 유지한다.
- `Authentication`에 실제 `assurance: Literal['password','password_uv']`와 선택 binding fact를
  명시한다. 기존 positional 호출은 보존 가능한 후행 필드로 추가하되, 기본값으로 Trainer를 만들지 않는다.
- 상위 `CurrentPrincipal(authentication, trainer: TrainerIdentityFact | None)`는 검증된 요청용 값이다.
  ORM/Session/암호 hash를 포함하지 않는다. Trainer의 Home는 별도 `trainer.home_branch_id`다.
- `TrainerSetupProof(source_id, account_id, organization_id, trainer_id, account_version,
  security_version, binding_version)`는 공개 proof다. 새 hash는 같은 IAM adapter의 private 임시 저장에만
  유지하고 proof/로그에 넣지 않는다. Trainer version/Home는 암호 해싱 후 잠금 시 현재 원본을 다시 읽는다.
- `IssueTrainerAccount(operation_id, trainer_id, login_id)` 및
  `ReissueTrainerSetup(operation_id, trainer_id, expected_account_version)`은 추가 필드 금지 DTO다.
- `TrainerAccountState(trainer_id, account_id, login_id, state, account_version,
  initial_setup_expires_at)`; 연결 없으면 account 관련 값은 null. 만료/소비 source의 expiry는 null.
- `TrainerAccountOperation(operation_id, kind, trainer_id, account_id, committed_account_version,
  current_state)`는 비밀 없는 확인 결과다. fingerprint·token·전체 링크는 응답에서 제외한다.
- 최초 확정 응답만 `TrainerSetupDelivery(operation, setup: Setup)`를 가지며 repr=False다.

`Workforce.lock_identity`는 호출자 인가를 대신하지 않는 내부 공개 fact 조회다.
상위 Service가 먼저 검증한 IAM 조직/연결·요청 목적을 정하고 fact를 조합한다.
그 fact 자체를 외부에서 받거나 공개 무인증 Trainer 조회 API로 노출하지 않는다.
신규 발급은 그 fact의 실제 Home와 `Organization.lock_scoped_branch`를 이용해 관리 인가한다.
비활성 Home는 허용하므로 `require_assignable`을 호출하지 않는다.

### 신규 port와 상위 함수 이름

| 소유 계약 | 메서드와 결과 | 호출 책임 |
| --- | --- | --- |
| IAMPort | `account_roles(account_id) -> AccountRoles`, `trainer_binding(org, trainer_id) -> Optional[TrainerBinding]` | 잠금 전 hint와 잠금 후 재조회 구분; 인가 대신 사용 금지 |
| IAMPort | `trainer_state(org, trainer_id) -> TrainerAccountState`, `trainer_operation(org, operation_id) -> Optional[TrainerOperation]` | Service가 현재 Home 관리 Scope를 검증한 후 응답으로 사용 |
| IAMPort | `trainer_issue(caller, trainer, home, operation, identifier, expected, slot) -> (TrainerOperation, Setup | None, IdentityTransition | None)` | Service의 같은 UoW에서 잠긴 Workforce/current Scope 확인 뒤 호출. adapter는 IAM 데이터만 변경 |
| IAMPort | `prepare_trainer_setup(token, password) -> TrainerSetupProof`, `lock_trainer_setup(proof, preauth, nonce)`, `complete_trainer_setup(proof, preauth, nonce) -> IdentityTransition` | hash는 private adapter 유지; 잠금은 표 순서대로, write 전에 Service가 active fact 확인 |
| IAMPort | `lock_trainer_credentials(account_id)`, `confirm_trainer_setup(proof)`, `confirm_identity_transition(snapshot, changed, authentication, logout)`, `confirm_login(proof, reservation, sid)` | 잠금/전후 상태와 최종 DB 시각 검증. snapshot은 immutable 값이며 ORM/비밀 없음 |
| IAMPort | `authenticate(..., touch=True)`, `confirm_preparation(preauth, nonce)`, `revoke_undelivered_session(sid)` | 원래 deadline 재검증 후 touch; 미전달 세션만 별도 UoW에서 철회 |
| WorkforcePort | `lock_identity(org, trainer_id, exclusive=False) -> TrainerIdentityFact` | org/id·현재 active/Home/version만, SHARE 또는 UPDATE |
| AuditPort | `append_trainer_identity(event: TrainerIdentityEvent) -> None` | 상위 Service가 세 모듈 fact를 명시 필드로 매핑 |
| Service | `issue_trainer_account`, `trainer_account_state`, `trainer_account_operation`, `complete_trainer_setup`, `login_entry`, `_current_principal` | HTTP는 Service만 호출하고 adapter/DBSession을 직접 사용하지 않음 |

위 write port는 외부에 공개되는 API가 아니며 상위 Service의 직전 인가/잠금 없이 호출하지 않는다.
Service 인수에 raw role/org/Home를 권한 근거로 주입하지 않고, 요청 DTO와 검증된 Caller를 구분한다.
기존 `IAM.login`은 잠금 후 역할 검사에서 admin+mode mfa이면 기존처럼 거부하고,
명시적 Trainer binding일 때만 상위의 잠긴 fact 검증과 함께 password 세션을 허용하도록 확장한다.
이 내부 port를 직접 노출하는 별도 HTTP 경로는 만들지 않는다.

## 4. 인증과 매 요청 상태 확인

`IAM.authenticate`에 `audience: Literal['admin','account']='admin'`을 추가한다.
기존 관리 API 호출은 기본 admin으로 유지한다. admin audience는 실제 admin grant를 요구하고,
mfa 모드에서는 password_uv/유효 key를 확인한다. 기존 제한된 S1 모드의 관리자 암호 경로는 보존한다.
`management=True`는 installation/account/session 잠금 모드일 뿐 인가가 아니다.
`scoped_account`는 Master→Branch Admin 관리 전용이며 Trainer self/신규 발급에 재사용하지 않는다.

account audience는 실제 admin grant 또는 명시적 Trainer binding이 있을 때만 IAM 인증 사실을 반환한다.
admin grant가 있으면 audience와 무관하게 mfa 모드 UV를 강제한다. binding 없는 비관리 계정은
I1이 지원하는 principal이 아니므로 인증 경로에서 거부하며 이를 I2 일반 roleless 정책 승인으로 기록하지 않는다.
기존 관리자 전용 계정에는 binding을 추측 backfill하지 않는다.

상위 `Service._current_principal(w, auth, *, management, target=None, credentials=False)`:

1. `w.iam.authenticate(..., audience='account', touch=False)`로 현재 계정/세션/assurance를 확인한다.
2. C3 최종 호출의 `credentials=True`이면 이 지점에서 기존 credential들과 새 Trainer credential들을
   고정 table 순서(기존 iam_credentials → iam_trainer_setup_credentials), 각 UUID순으로 선취한다.
   다른 self read는 이 잠금을 생략한다. 그 다음 명시적 binding이 있으면 `w.workforce.lock_identity(org, trainer_id)`로 현재 원본을 잠그고
   조직·id 일치를 확인한다. admin grant가 없으면 active 필수. admin grant가 있으면 inactive Trainer의
   Trainer 권한만 제외하고 독립 admin Scope를 유지한다.
3. 최종 DB clock 검사를 마친 뒤에만 반환한다. touch 필요 시 `IAM.authenticate`를 같은 잠금 안에서 다시 호출해 최종 검사 후 touch한다.
   처음부터 활동 시각을 갱신해 대기 중 만료된 세션을 살리지 않는다.

다음 경로는 모두 이 helper를 쓴다: `/auth/me`, 인증된 `/auth/csrf`, `/auth/logout`, `/auth/password`,
로그인 전 기존 쿠키 확인, Trainer 자기 화면. login/me에만 상태 검사를 넣는 구현은 불합격이다.
모든 관리 경로는 기본 admin audience 및 기존 각 업무 Scope를 유지한다.
Passkey 추가/삭제·reset/recovery·emergency/handoff의 관리/수신자 별도 자격 조건도 그대로다.

| 경로 | touch/GC | 비활성 Trainer-only 쿠키 |
| --- | --- | --- |
| me | no-touch/no-GC | 401 |
| csrf | 인증 성공 분기 no-touch/no-GC | 인증 CSRF를 내주지 않음. 기존401 처리처럼 별도 익명 preparation 분기로만 이동 가능 |
| logout | no-touch; 정상 세션 revoke+감사 | 인증 사용자 처리 금지. 기존 익명 preparation CSRF를 통과하면 쿠키 정리204 가능 |
| self password | 초기/최종 no-touch; 성공 전 세션 철회 | 401, 변경 없음 |
| 관리 API | 해당 기존 업무 규칙 | admin grant 없으므로403 또는 기존 비노출401/404, 관리 부작용 없음 |

분리된 preparation 생성은 익명 상태 준비일 뿐 비활성 Trainer 권한 복원이 아니다.
클라이언트 auth cookie가 유효하지 않아도 Origin/CSRF/JSON 검사를 생략하지 않는다.

### 공통 로그인 진입과 한 번의 암호 증명

`Service.login_entry`를 HTTP의 유일한 암호 로그인 진입으로 두고
`LoginOutcome = PasswordSession(token) | PasskeyChallenge(Ceremony)`를 반환한다.
기존 `Service.login`과 `begin_mfa_login`의 사전 쿠키/CSRF·gc_sessions·reserve·verify 부분을
공통 private 절차로 추출한다. 기존 public 호출이 필요하면 각각 공통 절차의 결과 종류를 검증하는
wrapper로 남기며 한 요청에서 두 wrapper를 차례로 호출하지 않는다.
하나의 요청에 reservation 하나, verify_login 한 번(unknown도 기존 dummy 검증), hash admission 한 번이다.
암호 proof 이후 서버 현재 admin grant/binding으로 분기하고 최종 잠금에서 다시 확인한다.
admin이면 기존 mfa_stage→mfa slot→begin_login/Passkey verify 경로, 명시적 Trainer-only면
session slot→현재 Workforce active→password session 경로다. 관리자 오류 뒤 Trainer 경로 재시도는 없다.
S1 관리자 모드에서는 기존 password login 응답을 유지한다. 신규 Trainer 발급 UI/명령은 mfa 관리 진입이다.

r2 복원 경계: `login_entry`는 admission 전에 서버 `iam_mode`를 분기한다. 제한 개발 모드
`s1_password`는 HEAD의 `Service.login` 본문/UoW/account 잠금/ACK 불명 cleanup으로 위임한다.
S1의 preparation과 GC는 별도 UoW이며 installation 선취를 추가하지 않는다. S1은 실제 admin
계정만 허용하여 새 Trainer-only가 Workforce 검사를 우회하지 않게 한다. 불명 COMMIT에서
HTTP503·Cookie 미반환과 이미 커밋된 live child의 기존 보존 계약을 유지한다.

`mfa` 모드에서만 아래의 역할별 공통 admission과 새 Trainer 미전달 세션 철회를 적용한다.
`Service.login`의 MFA 직접 호출은 `login_entry(expected_mfa=False)`로, `begin_mfa_login`은
require_mfa 뒤 `expected_mfa=True`로 진입한다. 이는 내부 타입 제한이며 클라이언트가 고르는
role/assurance가 아니다. entry→login은 S1에서만, login→entry는 MFA에서만 발생해 재귀하지
않으며 reserve/verify를 선행 호출하거나 반복하지 않는다. 승인된 S1 개발 동작을 운영 MFA의
Trainer cleanup 정책으로 일반화하지 않는다.
잘못된 암호·unknown·비활성 Trainer는 같은401 invalid_credentials와 기존 LOGIN_ATTEMPT/C2 처리를 적용한다.
상태/역할을 응답으로 먼저 공개하거나 추가 역할별 admission을 만들지 않는다.

r3 인증·인가 복원 경계: `IAM.authenticate`는 세션/계정 상태·security version·idle/absolute·
철회·pending 조건을 먼저 확인한다. MFA의 관리 audience 또는 현재 관리자 grant가 있는 계정은
현재 grant의 소실 여부와 관계없이 필요한 `password_uv`와 유효 Passkey 검증을 통과해야 한다.
그 뒤 관리 audience에서 현재 admin grant도 Trainer binding도 없으면403 forbidden으로 거절한다.
이 거절은 touch 및 Caller 반환 전이며 관리 업무나 typed audit에 미지원 Caller를 넘기지 않는다.
무효/만료/철회/약한 인증/키 없음은401을 유지한다. account audience의 무역할·무binding 계정401,
Trainer-only 관리 audience401, 기존 self의 현재 Workforce 검사와 겸임 계정 UV 규칙도 유지한다.
S1은 기존 password 계약을 유지한다. 이 구분은 기존 인증/인가 응답 계약 복원이며 roleless 로그인
지원이나 새 역할 정책 승인이 아니다. r2 `Service.login` 복원과 모든 기존 assertion은 유지한다.

## 5. API·화면 계약

모든 API prefix는 `/api/v1`, 기존 8192-byte 제한·extra field 거부·Origin/JSON/CSRF 규칙을 유지한다.

| 메서드/경로 | 입력 | 성공 | 실패/경계 |
| --- | --- | --- | --- |
| POST `/admin/trainers/{trainer_id}/login-account` | operation_id, login_id | 최초201: operation+setup_link+expires_at; 동일 요청 replay200: operation만 | 활성 Trainer/current Home 관리 필수. 기존 연결 또는 예약 Login ID 충돌409 |
| GET `/admin/trainers/{trainer_id}/login-account` | 없음 | 최소 TrainerAccountState | 현재 관리 Scope, 타 조직/타 Home404, no-touch/no-GC |
| POST `/admin/trainers/{trainer_id}/initial-setup` | operation_id, expected_account_version | 최초201 delivery; replay200 operation만 | PENDING_SETUP·활성 Trainer·현재 Scope; old version409 |
| GET `/admin/trainer-account-operations/{operation_id}` | 없음 | 최소 operation + 현재 상태 | operation의 실제 Trainer 현재 Home로 인가, 과거 issuer 권한 사용 금지 |
| POST `/auth/trainer-credentials/complete` | setup_token, new_password | 204, preparation 소비, 자동 로그인 없음 | 잘못된/만료/소비/purpose 불일치400 invalid_setup; CSRF403 |
| POST `/auth/login` | 기존 login_id,password | Trainer-only204+AUTH; 관리자 기존200 ceremony 또는 S1의204 | 서버 현재 역할만 분기. role/kind/org/branch 입력 금지 |
| GET `/auth/me` | 없음 | 관리자 기존 JSON 유지; Trainer 신원 JSON | 아래 최소 DTO, 더 넓은 목록/업무 권한 없음 |
| POST `/auth/password` | 기존 current_password,new_password |204, 모든 자기 세션 철회, AUTH/PREAUTH 삭제 | C3 유지, 추가 대상 ID·관리 Scope 입력 금지 |
| POST `/auth/logout` | 기존 CSRF |204, 해당 세션 철회 및 쿠키 삭제 | 다른 세션까지 자동 철회하지 않음 |

관리자 `/me`의 기존 `roles:[{role:'ADMIN',scope,branch_id}]`와 capabilities를 보존한다.
Trainer-only는 `account_id`, `organization_id`, `roles:[{role:'TRAINER',trainer_id,home_branch_id}]`,
`capabilities:[]`만 반환한다. Trainer Home로 `branches:read`를 부여하지 않는다.
본인 암호 변경은 공통 인증 기능이며 capabilities의 업무 목록과 별개로 노출한다.
전화·보상·전체 Trainer 프로필/다른 Trainer 목록·예전 Login ID를 넣지 않는다.

UI는 기존 관리 Trainer 선택 화면에 발급/상태/재발급을 연결하고 새 입력 role 선택기를 만들지 않는다.
수신 링크는 `/trainer-activate#token=...`; URL fragment를 메모리로 읽은 즉시 history.replaceState로 지운다.
기존 `/activate` 관리자 흐름은 유지한다. Trainer 페이지에서 관리자 token을 입력해도 서버 source 조회가 거부한다.
링크 재표시·storage 저장·콘솔 출력·GET/query 전송 금지. no-JS form은 명시 POST이고
handler 설치 전 submit disabled, CSP/same-origin 스크립트 유지. 설정 완료 후 login 화면으로 이동한다.
현재 `http.py`의 `/mfa.js`는 매번 `.json()`과 publicKey를 가정하므로 `flow==='login'`에서
응답204를 먼저 처리하고 그 경우 WebAuthn 호출 없이 자기 신원 화면으로 이동한다.
응답200 ceremony일 때만 기존 publicKey 변환/UV verify를 수행한다. 다른 enrollment/recovery flow의
응답 처리는 바꾸지 않는다. 로그인 스크립트는 배포의 mfa 설정만으로 분기하지 않는다.
초기 설정 전달/수신자 확인은 기존 승인된 발급자 직접 전달을 사용한다. 로컬 검증은 가상 수신자 별도 브라우저이며
메일/SMS/실운영 전달 서비스를 새로 선택하거나 구현하지 않는다.

## 6. 저장·키·제약

새 forward revision `0011_iam_trainer_login`, down_revision=`0010_workforce_initial`을 제안한다.
기존0001–0010/env를 바꾸지 않는다. 다른 모듈 원본으로의 FK는 무결성 제약이며 IAM private SELECT 허용이 아니다.

| 테이블/소유 | 주요 열·제약 | 수명 |
| --- | --- | --- |
| `iam_trainer_bindings` / IAM | account_id PK, trainer_id UNIQUE, organization_id, binding_version CHECK=1, created_at DB clock; UNIQUE(org,account,trainer), 복합 FK(org,account)→iam_accounts, FK(org,trainer)→workforce_trainers | 영속, I1 update/delete 없음 |
| `iam_trainer_account_operations` / IAM | PK(org,operation_id); kind CHECK issue/reissue; trainer_id,account_id; actor_id; target_home_at_commit; canonical_version=1; fingerprint bytea32; committed_account_version>0; created_at DB clock; FK(org,account,trainer)→binding, actor/target_home 복합 FK | 영속, GC 없음; token/hash 없음 |
| `iam_trainer_setup_credentials` / IAM | id PK/FK iam_security_states ON DELETE CASCADE; purpose CHECK='trainer_initial'; organization_id,account_id,trainer_id; digest UNIQUE bytea32; account_version/security_version/binding_version>0; expires_at; consumed bool; FK(org,account,trainer)→binding | 일시, 미소비 account별 partial UNIQUE; 기존 kind credential/30분 |
| `audit_trainer_identity_events` / Audit | id PK, org/account/trainer FK→binding, kind enum(issue/reissue/setup_complete/login/logout/password_change), actor_id nullable, actor_role enum(MASTER/BRANCH_ADMIN/TRAINER/CREDENTIAL_HOLDER), actor_branch, target_home, operation_id nullable, before/after_state·account_version·security_version, created_at DB clock | 영속 typed 감사, 자동 삭제 없음 |

모든 업무 UUID 참조는 같은 organization의 복합 FK를 적용한다. operation의 target_home는 당시 snapshot이며
후속 인가는 현재 Workforce 원본으로 한다. binding에는 Home/active 복제 원본이 없다.
initial credential의 purpose/계정/binding/epoch는 모두 검증한다. 생성/소비 port는 security state의 kind='credential'과
동일 id/원래 expires_at도 확인한다. operation은 UNIQUE(org,operation_id,account_id,trainer_id)를 두고
issue/reissue audit의 복합 FK가 같은 operation·account·Trainer를 가리키게 한다.
감사 state/version 열은 setup_complete에서 PENDING_SETUP→ACTIVE 및 양 version +1,
password_change에서 ACTIVE→ACTIVE 및 양 version +1, reissue에서 PENDING_SETUP 유지·row version +1·security 유지,
issue에서 이전 version null/새 version1, login/logout에서 ACTIVE 및 version 불변으로 제한한다.
이런 CHECK가 cross-row 원자성을 대신하지는 않으며 UoW와 실패 검증이 함께 필요하다. 신규 테이블을 써서 기존
`iam_credentials` positional INSERT와 admin MFA source 의미를 변경하지 않는다.
새 token은 기존 secrets.token_urlsafe(32), digest SHA256과 `Setup(repr=False)`를 재사용한다.

Audit 제약: issue/reissue는 operation 필수·actor Master 또는 BA, BA는 actor_branch=target_home;
setup_complete는 CREDENTIAL_HOLDER/actor_id null·PENDING_SETUP→ACTIVE;
login/logout/password_change는 TRAINER/actor_id=account_id·admin branch null.
관리자 겸임 경로는 기존 admin 감사와 Scope를 유지한다. 계정·Trainer UUID/current Home만 필요한 새
typed event에 넣고 암호/hash/token/full link, arbitrary JSON, 전화·보상·Login ID는 넣지 않는다.
실패 로그인은 기존 `audit_events`의 LOGIN_ATTEMPT·C2 기록을 유지해 응답/감사로 계정 존재를 더 노출하지 않는다.
신규 typed 감사의 read API/BA 전체 감사 열람은 만들지 않는다.

operation→일시 credential FK를 두지 않는다. credential GC가 영속 operation/감사를 삭제할 수 없어야 한다.
`Security._guard`의 만료/소비 child 수거에 새 credential을 추가하고, orphan sweep와 `release`의
NOT EXISTS에도 추가한다. source child 잠금은 SKIP LOCKED 및 삭제 전 재확인을 유지한다.
참조된 state를 release하면 삭제하지 않으므로 ACK 불명 때도 실제 커밋된 credential을 보존한다.
`collect=False`를 쓰는 신규 발급/reissue 반환 정리와 GET no-GC를 유지한다.
capacity/TTL 종류·수치·전역 GC 정책을 새로 만들지 않는다.

## 7. 멱등성·상태 확인·ACK 불명

canonical v1는 UTF-8 JSON, sort_keys=True/separators=(',',':'), SHA256이다.
issue payload={kind:'issue',trainer_id:소문자 UUID 문자열,login_id:기존 정규화 결과},
reissue payload={kind:'reissue',trainer_id,expected_account_version:정수}다. org+operation_id가 키이며
actor/Home/current version은 요청 fingerprint에 넣지 않는다. 이 사실은 인가 검사를 생략하지 않는다.

같은 키/같은 canonical 요청은 이미 커밋된 operation과 현재 상태만 반환한다. 다른 payload409.
서로 다른 키로 같은 Trainer 발급은 binding 유일성으로 하나만 성공한다. Login ID 예약 충돌은 기존 계정에
연결하지 않고409. 신규 계정 UUID/연결/credential/operation/audit가 한 UoW로 확정된다.
reissue는 같은 계정을 유지하고 account row_version을 전진, 기존 초기 source 모두 소비, 새 source 하나 생성한다.
PENDING_SETUP에서 아직 로그인은 없으며 security_version은 기존 reissue 원칙처럼 유지한다.
설정 완료는 row/security_version 모두 전진한다.

replay/status는 새 발급이 아니므로 비활성 Trainer라도 현재 관리자 Scope 내에서 과거 결과 확인 가능하다.
새 source를 만들지 않으며 Q1의 활성 조건을 우회하지 않는다. replay는 expected version 검사 전에
operation 일치를 판별하되 current Scope 검사는 항상 먼저 한다. 과거 operation 당시 account version과
현재 계정 version/state를 구분한다. 실제 새 reissue만 현재 PENDING_SETUP·active·expected version 필요.

`UnitOfWork.open(commit_observer=...)`의 starting/rejected/confirmed를 이용한다.
확인된 commit 뒤 최초 응답에만 raw link를 전달한다. 응답 실패/CommitUncertain이면503 및 비밀 없는
operation_id 확인 안내를 반환하고 raw link는 폐기한다. 저장된 token을 replay로 복구하지 않는다.
같은 operation 조회로 account 생성 여부를 확인하고, PENDING_SETUP이면 새 operation으로 명시 재발급한다.
commit_ack 불명 뒤 source slot을 무조건 삭제하지 않는다. business UoW를 닫은 다음
`Security.release(slot, collect=False)`의 새 source 참조 검사로 미참조 slot만 정리한다.
replay에서 미리 확보했던 불필요 slot도 동일하게 반환한다. 상태 확인만으로 credential TTL을 연장하지 않는다.

## 8. 잠금 그래프와 최종 확인

격리 수준은 기존 READ COMMITTED, 동일 Work의 DBSession 한 개다. 한 Session을 worker 간 공유하지 않는다.
상위 Service만 transaction 경계를 소유한다. 암호 검증/새 hash는 업무 행 잠금 없는 단계에서 준비한다.
확정 단계에서 원래 marker/epoch와 현재 facts를 다시 확인한다.

신규 Trainer 경로의 공통 순서:

`installation UPDATE(필요한 경로) → account UUID 정렬 → AuthSession UUID 정렬 → preparation →
credential UUID 정렬 → binding → Organization Branch → Workforce Trainer → operation → typed audit → final checks`

이미 잠근 행 재검사는 새 역순 잠금 취득이 아니다. source나 token 조회의 최초 힌트는 비잠금이고 권한이 아니다.
기존 관리/암호 변경 순서에 맞춰 account 이전 installation을 얻는다. 신규 self read/login도
일단 installation을 선취하는 좁은 일관성 계약으로 정한다(throughput 최적화는 후속 측정 없이 도입하지 않음).
기존 관리자 login/MFA 내부의 이미 승인된 순서는 유지하며 Trainer binding 경로와 혼합해 새 역순을 만들지 않는다.

| 경로 | 사전 단계 | 확정 UoW 잠금 및 검사 |
| --- | --- | --- |
| 신규 issue | 현재 admin UV/CSRF·대상 최소 확인; 별도 security credential slot | installation; actor account UPDATE, actor session UPDATE; 대상 Home hint→Organization SHARE→Trainer UPDATE; 같은 Home/org 재확인; operation 확인; 신규 account/binding/source/operation 삽입; typed audit; 최종 actor/Trainer/source 검사; 마지막 touch |
| reissue | binding에서 target account hint, 별도 slot | installation; actor+target account UUID순 UPDATE; 모든 관련 sessions UUID순 UPDATE; target 초기 credentials UPDATE; binding; 현재 Home의 Organization SHARE→Trainer UPDATE; operation; 소비/새 source/감사; 최종 검사·actor touch |
| status/operation | 대상/연결의 비잠금 hint | installation; 현재 actor/필요 target account 정렬; session; binding; Organization SHARE→Trainer SHARE; 현재 Scope 확인; no-touch/no-GC 최종 검사 |
| initial complete | token/source hint, 준비 CSRF 확인 후 UoW 종료; 암호 hash 준비 | installation; target account UPDATE; 자기 sessions 정렬 UPDATE; preparation UPDATE; 해당 초기 credentials 정렬 UPDATE; binding; Trainer SHARE; 실제 active/목적/epoch/만료; 암호 적용/소비/감사; 최종 DB clock; no session 생성 |
| Trainer login | 기존 csrf/gc_sessions/reserve/verify; 해싱 중 업무 잠금 없음; 별도 session slot | installation; account UPDATE(재해시 포함), 기존 관련 session 잠금; preparation; binding; Trainer SHARE; proof/예약/active 재확인; 새 session/password assurance·감사; 최종 DB clock; 별도 security.finish 성공 뒤 cookie |
| me/authenticated csrf | session/account hint | installation; account SHARE; 해당 session UPDATE; binding; Trainer SHARE; 현재 상태·최종 시각; no-touch/no-GC |
| logout | 위 self 인증/CSRF | 같은 순서, 원래 session을 revoke+감사; 최종 검사 후 commit. revoke 전 유효성 snapshot과 현재 account/Trainer/원래 deadline 확인 |
| C3 self password | self 인증/CSRF UoW 종료→현재 암호 검증/새 hash 준비 | installation; 자기 account UPDATE; 모든 자기 sessions 정렬 UPDATE; 기존+Trainer credentials를 정해진 table/UUID순 잠금; binding; Trainer SHARE; proof/CSRF/active; 암호 교체/전 세션 철회/credential 소비/감사; 최종 검사 |

조직 Branch 잠금이 필요한 것은 관리 Scope를 확인하는 발급/status다. 수신자 setup·self 로그인에서는
Workforce의 org/Home FK와 잠긴 fact만 사용하며 Home active를 재인가 조건으로 추가하지 않는다.
관리 명령은 Home 힌트를 읽고 Organization→Trainer 순서로 잠근 뒤 동일 Home인지 확인한다.
바뀌었으면409/rollback 후 새 요청으로 다시 확인한다. Trainer를 잠근 채 다른 Branch 잠금을 뒤늦게 추가하지 않는다.
기존 W0는 installation→account/session→Organization→Workforce/operation 순서와 양립한다.
신규 계정의 account/binding 삽입은 아직 타 transaction에 보이지 않는 행이므로 기존 account 잠금 역순이 아니다.
신규 binding 부재 동시성은 installation 및 Trainer UPDATE로 직렬화하고 DB UNIQUE가 최종 방어다.

`lock_identity(exclusive=False)`의 SHARE를 setup/login/self가 commit까지 보유한다.
향후 W1의 Trainer 비활성/이동 UPDATE는 이 잠금을 기다리고, W1 선행이면 I1은 새 fact로 판단한다.
W1 구현은 여기서 추가하지 않으며 시험에서는 별도 소유 연결의 직접 UPDATE를 경합 harness로만 사용한다.
그것을 실제 W1 업무 인수로 주장하지 않는다. I2는 이후 역할 변화 시 account epoch/잠금 계약까지 함께 검토한다.

Security transaction은 business 잠금 구간과 중첩하여 대기시키지 않는다.
reserve/allocate는 business 잠금 전 종료, finish/release는 business UoW 종료 후 별도 실행한다.
현재 `Service.login`처럼 잠금 없는 hash 단계에서 별도 slot 확보는 가능하나 먼저 account SHARE 등을 잡지 않는다.
GC는 source SKIP LOCKED로 업무 잠금 대기를 피하며 새 source FK가 가리키는 state를 orphan으로 삭제하지 않는다.

최종 확인은 SQL `clock_timestamp()`이며 애플리케이션 시계/transaction 시작 시각을 쓰지 않는다.
감사 지연까지 지난 뒤 다음 항목을 한 번 더 확인하고 불일치면 업무 전체 rollback한다.

- 현재 actor의 ACTIVE/epoch/assurance/key/원래 idle·absolute/CSRF, 동일 actor와 target Scope.
- 잠긴 Trainer 현재 org/Home/active 및 binding account/trainer/version. 상태 조회/replay에는 active 필수 없음.
- 초기 source는 original expires_at, purpose, account/binding/epoch, 준비 CSRF 원래 deadline.
- 신규 session은 slot expiry와 session expires_at, 원래 로그인 예약의 account/key/epoch 및 유효 lease.

이미 같은 transaction에서 source를 consumed 처리하거나 session을 revoked/계정 epoch를 올린 경우
일반 authenticate를 재호출해 자기 변경을 오류로 만들지 않는다. `confirm_trainer_setup` /
`confirm_identity_transition` port가 잠금 전 snapshot과 기대한 변경 후 row를 대조한다.
source의 consumed=true를 예상하고도 원래 deadline/epoch·계정 변경 전후 전이·Trainer 상태를 검증한다.
C3의 기존 `change_password`가 credential 잠금을 내부에서 얻으므로 상위에서 Workforce를 잠그기 전에
`lock_credentials`와 새 Trainer credential 잠금을 선취한다. 이후 재호출은 이미 보유한 잠금이다.

로그인 성공은 `security.finish(reservation, True)` 후에만 쿠키를 보낸다. 이 후처리가 실패/불명하면
`mfa` 모드의 Trainer 경로에서는 쿠키를 보내지 않고 방금 만든 session을 기존 MFA `revoke_undelivered`와 동등한 명시 port로 철회한다.
알려진 인증 실패만 finish False에 반영하고 capacity/HashAdmissionRejected/경합503을 암호 실패로 가산하지 않는다.
현재 C2 예약 alias/account binding·보수적 lease·cancel/release 분류를 유지하며 역할별 새 budget을 만들지 않는다.

## 9. C3·감사·관리 경계

C3는 Trainer도 현재 암호를 알고 유효 self 인증이면 실행할 수 있다.
`scoped_account`, require_master, 관리자 대상 reset을 경유하지 않는다.
새 hash/row_version/security_version, 모든 자기 AuthSession 철회, 초기 credentials 소비와
password_change typed 감사가 한 UoW다. Trainer 연결/Home/active·다른 계정·budget/cooldown은 유지한다.
로그아웃은 현재 세션만 철회한다. 본인 변경 실패를 로그인 실패로 가산하지 않는다.
관리자 C3는 기존 UV/감사·마지막 Master 본인 변경 허용을 유지한다.

관리자 grant가 있는 account가 Trainer 전용 source/endpoint를 통과할 수 없다.
initial source 발급·complete에서 admin grant 부재와 해당 binding을 명시 확인한다.
추후 겸임 연결은 I2이므로 현재 초기 설정 source를 겸임 승격 경로로 쓰지 않는다.
정상 관리자 login/setup/passkey/reset/emergency/handoff는 기존 서버 역할/목적 검증을 보존한다.
기존 코드가 account.master=False와 branch_id=None를 단순 비관리자로 해석하는 부분을 조사하고,
관리 API에서 그 상태가 Trainer 권한이 된다고 추론하지 않도록 기본 audience 방어와 개별 Scope 검사를 함께 둔다.

## 10. Migration·downgrade와 회귀 범위

신규 테이블·인덱스만 추가하고 기존 관리자 계정/grant/session/credential의 의미와 데이터를 보존한다.
새 code가 필요한 source GC 수정은 runtime의 명시 구현 대상이며 기존 migration을 고치지 않는다.
`0011_iam_trainer_login` downgrade는 설치/account/session과 신규 binding/operation/source/audit를
정해진 순서로 ACCESS EXCLUSIVE 잠그고 신규 사실이 하나라도 있으면 거부한다.
생성 이력을 삭제하거나 신규 계정을 roleless로 만든 뒤 내리는 방식은 금지한다.
빈 신규 테이블만 역 FK 순서로 제거하며 기존 W0/관리자 데이터를 보존한다.
동시에 신규 source를 allocate하는 경우 state의 잔존만으로 이력을 가리지 않고 실제 참조/신규 행을 재검사한다.

기존 retained-head 고정 단언은 새 head 때문에 영향을 받을 수 있다.
구현 전 `backend/tests`의 실제 head 단언/스키마 fingerprint/lock 관찰을 목록화해 설계자에게 정확한
함수/상수 변경 범위를 요청한다. 기존 테스트를 일괄 치환·skip하거나 보호 guard를 약화하지 않는다.
직전 W0에서 보완한 MFA/Reset의 PGAPPNAME·실제 blocker 관찰은 그대로 유지한다.
Import Linter 8개 계약을 모두 보존한다. 신규 private adapter 파일을 만들 경우에만 forbidden_modules에
그 경로를 추가하고 기존 경계/계층을 제거하지 않는다. 이번 안은 IAM 기존 adapter 확장으로 충분하다.

현재 직접 검색으로 확인한 head 호환 검토 대상은 다음 세 파일이다. 향후 구현 entry에 정확한 함수/단언
범위를 포함하고 이 문서 작성 단계에서는 수정하지 않는다.

| 파일 | 좁은 호환 검토 |
| --- | --- |
| `tests/test_iam_emergency_integrity.py` | `test_migration_roundtrip_and_durable_history_guard`의 보존 head 비교0010→0011, 기존 거부/이력 assertion 유지 |
| `tests/test_iam_emergency_handoff_integrity.py` | line86의 보존 head 비교0010→0011만, 나머지 CHECK/이력 assertion 유지 |
| `tests/test_workforce_integrity.py` | `test_migration_roundtrip_and_information_guard`의 upgrade head 및 거부 후 head 세 비교0010→0011; downgrade 대상0009와 데이터 보존 assertion 유지 |

`test_iam_s2.py`/`test_iam_s2b.py`는 이미 ScriptDirectory의 current head를 사용하므로 상수 변경 불필요다.
상태 비교는 실제 Alembic transaction rollback 기준을 검증하며 새 head 단언을 약화하는 수단으로 쓰지 않는다.

## 11. 구현 파일별 검증과 인수 계획

새 테스트 파일 후보는 `backend/tests/test_iam_trainer.py`, `test_iam_trainer_races.py`,
`test_iam_trainer_storage.py`, `test_iam_trainer_browser.py` 및 `tests/browser/trainer.cjs`,
`trainer-checks.json`이다. 기존 pytest/fixture/QA runner를 재사용하고 별도 lifecycle 도구를 만들지 않는다.
실제 HTTPS는 `tests/test_iam_browser.py::run_browser`의 기존 W0 선택 방식에 Trainer 선택을 추가해
가상 수신자 격리 browser context와 새 manifest만 연결한다. TLS/CA/NSS/프로세스/schema/cleanup 코드를
복제한 별도 harness를 만들지 않는다. 이 helper의 분기/manifest 선택 변경도 별도 구현 entry에 포함한다.
발급 UI는 기존 `/trainers` 페이지를 확장하며 새로운 관리자 포털을 만들지 않는다.

| 구분 | 필수 사례·증거 |
| --- | --- |
| DB 없는 계약 | 정규화/fingerprint, 상태표, 역할·assurance 분기, extra field 및 비밀 없는 DTO/오류 |
| 실제 PG 수직 흐름 | 실제 W0 생성·현재 Master/BA 발급·수신자 설정·Trainer 로그인/me/C3/logout; 가짜 Caller로 대체 금지 |
| 권한·상태 | 타 org/Home/direct ID/과거 issuer 거부; Home 비활성 허용; Trainer 비활성 3단계 거부 및 기존 쿠키 me/csrf/logout/C3; 독립 admin 유지 |
| 일대일·중복 | 동일 Trainer/다른 op·동일 Login ID·동일 op/다른 payload·replay/status 무토큰; ACTIVE/DISABLED/PENDING_SETUP 연결 덮어쓰기 금지 |
| source/purpose | 관리자 source→Trainer complete 및 역방향 거부, 단회/재발급/원래30분 경계, 비활성 중 소비 금지·재활성화 후 원래 유효기간만 사용 |
| 실제 race | 독립 worker/PID·pg_blocking_pids로 승패 증거: 발급 대 발급/재발급 대 소비/소비 대 소비/C3 대 login/계정차단·Scope 변경/Trainer 상태 UPDATE |
| 최종 시각 | 실제 hash·잠금·감사 callback 도달 뒤 deadline 경과; 처음에는 유효였음을 증명하고 전체 rollback·no premature touch 검증 |
| 원자성/ACK | 계정/연결/source/operation/audit 각 실패 rollback, 실제 commit ACK 유실 후503→status→명시 reissue; source를 release가 지우지 않음 |
| 세션/C2/C3 | 기존 alias/cooldown/lease/용량 유지, inactive는 실패응답으로 계정존재 비노출, C3 모든 자기 session만 철회 및 타 계정 보존, post-commit finish 실패시 미전달 session 철회 |
| 저장/GC | 같은 org FK/유일성/CHECK, source 만료/소비 cleanup, GC 대 소비/재발급 실제 대기·잔존, empty upgrade/downgrade 및 모든 새 이력 보존 거부 |
| 실제 HTTPS/native | 관리자 UV 유지, 다른 recipient 암호 설정, Trainer 암호로그인204/me/C3/logout, 관리 데이터/쓰기 API 차단, Cookie/CSRF/origin/no-JS/fragment 제거/CSP/8192-byte·모바일 |
| 기존 회귀 | S1 관리자 response/암호 모드, 운영 MFA 관리자 login/setup/추가Master/C3/reset/recovery/emergency/handoff, W0 current Home/G1·보상 비노출; 보호된 기존 전체 suite |

운영 TLS/실물 authenticator·전체 지원 브라우저·생산 배포·개인정보/보존 인수는 별도다.
TestClient를 실제 브라우저 검증으로 부르지 않는다. 여러 대상 실행 합계를 단일 전체 실행으로 보고하지 않는다.
현재 fast122/PG419/총541은 기준선; 신규 테스트 추가 후 정확한 수집 수와 native manifest를 다시 산정한다.
개발 대상 검사/최종 fast/수집 → 소스 동결 → 별도 독립 전체 PG/native → 설계자 수용 → 전담 커밋 세션 순서다.

## 12. 현재 문서 작업 결과와 다음 진입

최초 계약 작성 단계에서는 Product 세 선택과 이 계약만 작성했다. 이후 설계자의
`root-implementation-entry.json`에 따라 앱·테스트·새 migration0011을 구현하고 개발 대상 검사를 완료했다. [개발 결과](iam-011-trainer-login-results.md)를 따른다.
계약 단계의 실행 없음 기록은 당시 이력이며 최종 실행 결과와 구별한다.
새 업무 선택 질문은 없다. I2/분실 reset/운영 결정은 I1의 선행조건으로 확대하지 않는다.
기술 계약의 제한 구현 승인은 아래 항목 검토 후 기록되었다. 최종 인수 시 재확인한다:
공통 self helper의 적용 경로·기존 admin default, source/operation/audit 제약, 전체 잠금 그래프,
최종 clock의 자기 전이 처리, C2/GC/ACK 경계, 기존 보호 테스트의 정확한 호환 변경 목록.
[결정 게이트](decision-gates.md)의 과거 I1 답변 대기 문구는 2026-10-26 Product 승인으로 해당 부분만
해결됐으며 이 문서 작업에서 Architecture 단계 문서나 전체 OPEN/ADR 상태를 자동 변경하지 않는다.

문서 검증은 로컬 참조·Product ID·diff/수정 범위·비문서 바이트 보존을 대상으로 한다.
실행 자료는 ignored `.local/qa/iam-trainer-login-07f93e7705ed497d/developer-contract-result.json`에 기록한다.
후속 자동 실행자는 [QA 절차](../../backend/README.md#qa-실행-자료와-정리)에 따라 고유 폴더에 최소 결과를
남긴 뒤 자기 process/schema/folder를 정리하고 실패·미정리를 보고한다. 수동/미해결 자료는 이유와
정리 조건을 기록하며 검수 전 자동 삭제하지 않는다.

정적 페이지 경계: 기존 `/trainers`는 TLS/origin 검사 뒤 개인정보 없는 정적 shell을 반환할 수 있다.
Trainer에게 관리 권한을 주는 것은 아니며 실제 목록·직접 ID·발급/재발급 API는 현재 admin audience와 Scope를 강제한다.
`/account`는 현재 본인 인증이 필요하다. 정적 shell 접근을 관리자 페이지 전체 차단으로 보고하지 않는다.
