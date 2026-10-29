# IAM-012 — 기존 계정 Trainer 역할 추가·회수·재부여

2026-10-30. **제한 계약 구현·독립 전체 검증·설계자 로컬 인수 완료**.
실행과 한계는 [검증 결과](iam-012-trainer-roles-results.md)·[최소 판정](iam-012-trainer-roles-review.json)을 따른다.
Product [I2-1/2/3 모두1](../product/product-decisions.md#review-20261030-i2)을 입력으로 한 제한 계약안이다.
ADR-0001~0004의 승인 범위를 유지하며 전체 모듈/공유 UoW/운영 설계를 ACCEPTED로 바꾸지 않는다.
기준은 `08f2ef5a26fbe8f91058bf3767efe4b1b382d1a5`와 [I1 영구 인수 근거](iam-011-trainer-login-review.json)다.
이 계약은 이번 IAM-012 증분의 구현 입력이다. 실제 구현·독립 검증·설계자 인수는 별도 결과로 확인한다.

## 1. 승인된 범위와 완료 기준

E5의 현재 Master Organization 또는 실제 Trainer 현재 Home 관리 Branch Admin이 기존 계정에 Trainer
역할을 처음 부여하거나, 같은 불변 연결에서 회수/재부여한다. 관리자+Trainer 겸임은 한 계정으로 처리한다.
Home 비활성만으로 거부하지 않는다. 현재 Actor의 실제 권한과 대상 Trainer Home로 매번 판단한다.

| 요청 | 대상 조건 | 성공 시 |
| --- | --- | --- |
| 첫 연결+부여 | 같은 조직 ACTIVE/login-ready 계정, 활성 Trainer, 양쪽 기존 binding 없음, 명시 동일인 확인 | 불변 binding 생성, grant 부여, 대상 전 인증 철회 |
| 같은 연결 재부여 | ACTIVE 또는 PENDING_SETUP, 활성 Trainer, 기존 불변 쌍 일치 | grant 활성화, 대상 전 인증 철회; 암호/계정 상태 유지 |
| 회수 | 현재 E5 Scope; 계정/Trainer 상태 무관 | grant 비활성, 대상 전 인증 철회; binding/이력/독립 admin 보존 |
| 이미 같은 grant 상태 | 기존 불변 binding/grant 존재, 현재 Scope, 정확한 쌍/요청 버전 확인 | no-op 영수증; epoch/감사 전이/세션 철회 없음 |
| replay/status | 현재 Scope 재검증 | 원래 결과와 최소 현재 상태; 새 철회/링크 발급 없음 |

login-ready는 기존 ACTIVE+유효 암호 보유, recovery/reset pending 아님, 현재 지원 로그인 역할의
인증 준비 충족이다. 현재 관리자는 기존 UV용 유효 Passkey가 있어야 한다. 대상 암호/키를 Actor에게
입력시키거나 자동 복구하지 않는다. 기존 roleless 계정의 같은 binding 재부여는 첫 연결 조건과 구분한다.
DISABLED 추가/재부여 금지, 비활성 Trainer 추가/재부여 금지다. 회수에는 이 두 활성 조건을 적용하지 않는다.
첫 연결로 다른 계정/Trainer의 기존 binding을 교체하거나 다른 조직을 연결할 수 없다.

유효 로그인 역할0이면 신규 로그인/기존 인증 접근 불가다. 마지막 Trainer 역할 회수는 허용하며
자동 DISABLED/삭제/reset을 하지 않는다. 역할을 되돌려도 옛 인증/링크는 되살리지 않는다.
남은 관리자는 기존 password+UV로 로그인하고, Trainer-only는 활성 grant와 실제 활성 Trainer가 필요하다.
관리자+비활성 Trainer는 독립 관리 역할로 로그인 가능하며 Trainer 자격은 유효 역할로 세지 않는다.

완료 수직 흐름: 실제 기존 관리자 계정과 W0 Trainer를 명시 연결→새 UV 로그인으로 겸임 확인→
회수 후 남은 admin 유지→같은 연결 재부여. 별도로 I1 미설정 계정 회수→재부여→명시 새 링크→
수신자 설정→Trainer 로그인, 마지막 역할 회수→로그인 거부→재부여→기존 암호 재로그인을 검증한다.
fixture로 준비·로그인을 대체하지 않는다. 비활성/경합 경계만 소유 테스트 schema의 상태 조작을 허용한다.

Operator 구현, admin 승격/회수, Trainer Home/state 변경, 다른 사람 재연결, 분실 암호 reset,
PT/금융·운영 인수는 제외한다. E5/B2/G1/C3/AB4와 I1 승인값은 재질문하지 않는다.

## 2. 현재 구현과 책임 분리

현재 `AccountRoles.binding` 존재가 Trainer 로그인 자격이며 `binding_version=1`이다.
I1 `identity_transition`은 admin 겸임을 거부하고 기존 typed identity audit은 Trainer 단독 전이용이다.
이를 역할 변경 감사에 억지로 재사용하거나 기존 제약을 완화하지 않는다.

- IAM: 계정/암호/독립 관리자 grant, 불변 Trainer binding, 별도 Trainer grant/epoch, 인증과 작업 영수증.
- Workforce: 현재 Trainer organization/Home/active/version. 기존 `identity`와 `lock_identity` 공개 DTO를 사용한다.
- Organization: `lock_scoped_branch`/`confirm_scoped_branch`의 현재 관리 Scope. Home 활성은 이 작업의 조건이 아니다.
- Application: 위 공개 계약의 잠금 순서, 현재 인가, 한 UoW와 typed Audit 조합.
- Audit: 새 `TrainerRoleEvent`와 저장 제약. IAM이 Workforce 테이블을 직접 조회하지 않는다.

## 3. 불변 연결·grant·epoch와 0012 계획

`iam_trainer_bindings`의 양방향 일대일/동일 조직 FK·binding_version=1을 유지한다. 역할 회수는 이 행을
삭제/수정하지 않는다. 신규 `iam_trainer_role_grants`는 account PK, 같은 organization/account/trainer
복합 binding FK, `granted boolean`, 양수 `role_version`, 변경 시각을 가진다. 회수도 행을 남긴다.
연결 식별 버전과 가변 역할 버전을 혼용하지 않는다.

`iam_accounts.trainer_role_epoch`를 별도로 둔다(미연결0, 최초 연결1, 실제 grant 전이마다+1).
이는 독립 관리자 역할/계정 state/security_version/암호/Passkey를 변경하는 값이 아니다.
grant role_version과 epoch는 이 증분에서 함께 증가하며 동등성은 IAM 원자적 저장/검증과
지연 가능한 복합 FK(account_id,epoch)로 보장하는 안이다. optimistic 기대값은 account row_version,
role_version(첫 연결0), Trainer version이다. **역할 전이는 account row_version/security_version을
증가시키지 않는다.** 기존 recovery/reset/emergency source가 row_version을 확인하므로 이를 올리면
독립 관리자 복구 링크를 의도치 않게 무효화한다. 역할 요청의 stale 판정은 자체 role_version/epoch로
처리하고 기존 계정/암호 변경의 version 규칙은 그대로 둔다.

버전 증분표(실제 role 전이 한 건 기준):

| 값 | 첫 연결+부여 | 회수/같은 연결 재부여 | no-op/replay/status |
| --- | --- | --- | --- |
| account state/password/row_version/security_version | 모두 유지 | 모두 유지 | 유지 |
| trainer_role_epoch | 0→1 | n→n+1 | 유지 |
| grant role_version | 행 생성1 | n→n+1 | 유지 |
| immutable binding_version | 행 생성1 | 1 유지 | 유지 |
| 기존 admin source의 row_version/security_version/generation/expiry | 유지 | 유지 | 유지 |

`expected_account_version`은 다른 계정/암호/수명 변경을 검출하고 `expected_role_version`은 역할
변경을 검출한다. 두 목적을 합치지 않는다. 새 role typed audit의 before/after account version과
security version은 같아야 하며 role version/epoch만 +1이다. 최초 grant는 before role_version=0으로
표현한다. 새로운 epoch를 옛 장기 source/proof에 덮어써 되살리는 migration/명령은 금지한다.
backfill은 새 컬럼만 채우고 기존 source의 버전/소비/기한 값을 그대로 둔다.
기존 I1 신규 발급도 같은 UoW에서 binding+granted=true/version1+epoch1을 처음 만들도록 적응한다.
I1 setup/C3 등 고유 계정 version 전이는 원래 규칙을 유지하며 역할 전이 audit으로 대체하지 않는다.

새 forward revision `0012`만 작성한다. 0011 이전 파일은 불변이다. 같은 transaction/배타 잠금에서
기존 모든 binding에 granted=true/version1, 계정 epoch1을 backfill한다. 기존 상태가 inactive/DISABLED라도
임의 회수/활성화하지 않는다. 현재 binding 수·쌍과 새 grant 집합을 정확히 대조한다. 기존 연결 세션/
대기 로그인 context/Trainer 초기 source에는 해당 epoch1을 backfill해 upgrade 자체가 로그아웃이나
링크 폐기를 일으키지 않게 한다. 미연결 계정/세션은0이다. 감사·operation·기존 history는 변경하지 않는다. grant에 생성 출처(backfill/i1_issue/i2_link)를
고정 저장해 downgrade가 순수 backfill과 이후 새 연결을 식별할 수 있게 한다.

AuthSession, 암호 proof, MFA context/verify proof, Trainer 초기 source/proof 및 준비된 reset/복구 proof에 role epoch를
전달하여 잠금 전 proof가 변경 후 session/source를 확정하지 못하게 한다. 기존 security_version
검증에 이를 추가한다. backfill과 DTO 추가의 모든 소비 경로를 검색해 누락 검사를 작성한다.
`/me` 표시만 바꾸고 실제 인증 검사를 남기는 구현은 불가하다.

DB 제약: grant/binding 쌍과 org 일치, 양방향 유일, 양수 버전, 원래 operation과 typed audit의
동일 대상 FK, epoch/전이 증가 검증. binding이 없는 grant와 다른 사람 쌍 삽입은 거부한다.
역할 operation/audit은 기존 I1 operation/audit과 별도 테이블로 두고 원래 CHECK를 넓히지 않는다.

Downgrade는 installation→관련 계정/세션/credential/grant/binding/operation/audit 테이블 잠금을
고정 순서로 확보한다. I2 operation/audit/새 연결/회수/버전 전이 또는 보존 불가능한 epoch 사실이 있으면
DDL 전 거부한다. backfill만 있고 모든 grant가 원래 binding과 같으며 version1/granted=true이면
기존0011로 정보 손실 없이 돌아갈 수 있는지 검증한 뒤 허용한다. 빈 DB만 통과시킨 결과를 실제 backfill
검증으로 보고하지 않는다. upgrade/downgrade와 실제 issue/role 변경의 잠금 대기도 테스트한다.

## 4. 동일인 선택과 최소 공개

현재 관리 가능한 Trainer를 먼저 연 뒤 **정확한 현재 Login ID**로 계정을 한 건 조회한다.
대소문자 정규화/이전 ID 예약 정책은 유지한다. 부분 검색/조직 전체 계정 목록/이름·전화 자동 병합은 없다.
Trainer 관리 Scope를 확인하기 전에 계정 존재/상태를 응답하지 않는다. 다른 조직 또는 Trainer Scope 밖은404.

후보 응답은 account_id, 현재 login_id, state, account_version, 연결 가능 여부와 기대 role_version만이다.
Passkey 수/식별, 관리자 등급·관리 Branch, 암호/인증 실패/C2·recovery 상세, 전화/보상은 반환하지 않는다.
현재 관리 중인 Trainer의 id/name/Home는 이미 허용된 W0 DTO에서 표시한다. 다른 Trainer와 연결된
계정은 그 Trainer 정보 없이 일반409 또는 선택 불가로 처리한다. account_id로 직접 POST해도 동일 검증한다.
같은 조직의 독립 admin Scope가 BA 범위 밖이어도 Trainer 역할 변경 대상에서 배제할 이유로 사용하지 않되
그 admin Scope를 공개하거나 변경하지 않는다. 이는 별도 관리자 계정 목록 열람 권한이 아니다.

관리자가 기존 E2 본인 확인 절차로 계정 소유자와 실제 Trainer가 같은 사람임을 확인하고 화면에서 두
식별자를 대조해 `identity_confirmed=true`로 명시 제출한다. 서버는 계정·Trainer·org·binding·현재 Scope를
검증한다. boolean은 물리적 동일인 자동 증명이 아니다. 확인 미제출422, 자동 추천/묵시적 병합 금지.
재부여/회수는 이미 고정된 쌍을 사용하며 account_id 변경으로 우회할 수 없다.

## 5. 최소 API와 UI 계약

기존 `/api/v1`, JSON/Origin/CSRF/8192-byte/extra field 거부/입력 원문 비노출을 유지한다.

| API | 계약 |
| --- | --- |
| POST `/admin/trainers/{id}/role-account-lookup` | 정확 Login ID. 현재 Trainer Scope 선검증 후 최소 후보; 조회이며 상태/GC/touch 없음 |
| GET `/admin/trainers/{id}/role` | binding 식별, grant 상태/version, 계정 state/version. 현재 Trainer version은 기존 Trainer 상세 GET으로 조회. token 없음 |
| POST `/admin/trainers/{id}/role` | operation_id, account_id, desired_granted, expected_account_version, expected_role_version, expected_trainer_version, identity_confirmed. 첫 연결/재부여/회수를 서버 현재 상태로 구분 |
| GET `/admin/trainer-role-operations/{operation_id}` | 현재 조직/Trainer Scope로 원래 committed/no-op 결과와 최소 현재 상태. 원래 Actor만의 소유권으로 제한하지 않음 |
| 기존 POST `/admin/trainers/{id}/initial-setup` | 재부여된 PENDING_SETUP+활성 Trainer+현재 grant일 때만 명시 새 링크. role epoch 결합; 역할 명령이 링크를 자동 생성하지 않음 |
| 기존 GET `/auth/me` | 현재 유효 roles와 불변 binding 사실을 분리. 폐기/비활성 Trainer를 현재 Trainer 권한으로 표시하지 않음 |

성공은200, 결과는 operation_id, changed, committed_role_version/epoch, 현재 최소 role 상태,
`reauthentication_required`(actor==target 실제 변경)다. GET/replay는 비밀/새 쿠키/새 링크를 반환하지 않는다.
401 무효 인증,403 유효한 관리자 인증의 행위 인가 실패,404 다른 조직/Scope·없는 대상,
409 상태·버전·불변 쌍/operation 충돌,422 형식/명시 확인 누락을 유지한다.

`/trainers`의 기존 상세 영역에 정확 계정 조회→동일인 확인→부여, 현재 연결의 회수/재부여와 operation
상태 확인을 제공한다. no-op와 실제 변경을 구분하고 실제 변경은 전 로그인 종료를 제출 전에 안내한다.
본인 성공은 응답 후 로그인 화면으로 이동하고 쿠키를 삭제한다. 응답 유실 시 성공을 추정해 자동 반복하지
않고 재로그인 후 같은 operation 상태를 조회한다. 권한이 없어진 Actor는 현재 다른 관리자가 조회할 수 있다.
PENDING 재부여 후에는 별도 초기 링크 재발급 동작을 노출한다. 기존30분/단회/전달/fragment 제거를 유지한다.
JS 비활성 시 제출 차단 및 POST form method로 query 유출을 막고 token/암호를 localStorage·URL query에 두지 않는다.

`/me`: `roles`는 현재 admin 및 활성 grant+활성 Trainer의 유효 역할만, `trainer_binding`은 불변 쌍의
최소 id와 별도 grant 상태를 나타낸다. admin+회수/비활성 Trainer에서 binding은 남아도 TRAINER role은 없다.
roleless는 `/me` 자체401이므로 binding 정보를 공개하지 않는다. 기존 admin 필드와 I1 self 계약은 유지한다.

## 6. 인증·대기 proof·초기 source 처리

실제 grant 전이의 동일 UoW에서 대상 모든 `iam_sessions.revoked=true` 및 epoch 증가를 수행한다.
로그인/UV 확인과 최종 session 생성 모두 현재 role epoch를 다시 검증한다. 대상의 MFA context는 consume하고
임시 password_hash를 제거한다. 이미 발행된 proof도 epoch 불일치로 거부한다. 다른 계정 context/C2는 보존한다.
역할 변경에서 Passkey/암호 hash·관리자 grant·계정 state를 수정하지 않는다.

| 자료 | 실제 전이 시 처리 |
| --- | --- |
| 기존 대상 AuthSession/로그인 proof/MFA context | 전 세션 철회; context consume, proof epoch 재검사; 새/재로그인만 허용 |
| 대상 I1 Trainer 초기 source/proof | 미소비 source consume, 옛 proof epoch 거부. grant 재부여로 다시 살리지 않음 |
| 관리자 setup/recovery/reset/emergency의 장기 source | 역할 추가/회수는 계정 복구가 아니므로 기존 source/state/security epoch 보존. 그 source에서 시작한 MFA context는 위대로 무효화되므로 현재 source 조건으로 ceremony를 새로 시작; 준비된 reset/복구 proof에도 epoch를 확인 |
| Passkey 추가 등 기존 인증에 매인 context | 대상 context consume 및 원래 session 철회로 완료 거부. Passkey 본체는 보존 |
| 다른 계정 자료/C2 예산/immutable binding/업무 history | 변경 없음 |

현 `revoke_management_sources`는 Trainer 초기 source를 포함하지 않고 관리자 장기 source까지
consume하므로 통째로 호출하지 않는다. 전용 role 전이 계약이 Trainer setup source와 전체 MFA context를
명시 처리한다. reset/recovery pending 중 회수도 허용하고 pending flags/암호·키 원본/장기 source의
row_version/security_version/generation은 보존한다. 새 context는 최신 role epoch로 생성한다.
기존 정상 Master의 명시 재발급과 이미 승인된 emergency/handoff 경로는 각자의 현재 인가/대상 조건으로
계속 실행 가능해야 한다. 모든 Master 불가 상태의 정상복구 권한을 이 명령으로 우회하지 않는다.
원래 source가 만료·소비됐다면 기존 명시 재발급/인계만 사용하고 자동 연장/새 링크 발행은 없다.
회수 전 prepare된 proof는 epoch 검사로 차단하고, 회수 후 같은 유효 장기 source에서 새 준비를 시작할 수
있음을 별도 검증한다. 기존 관리자 복구 테스트의 source 인수 조건을 낮추지 않는다.

초기 source 사용·관리 복구 완료로 grant가 복원되는 경로를 만들지 않는다. source 자체가 유효하더라도
완료 시 원래 계정 조건과 최신 역할을 검사한다. 장기 복구 source 보존이 역할0 로그인 허용은 아니다.
PENDING_SETUP 회수는 계정/암호NULL/연결을 그대로 두며 old 초기 source를 폐기한다. 같은 연결 재부여는
계정을 ACTIVE로 만들지 않는다. 현재 관리자의 명시 새 링크 발급 이후에만 기존 I1 방식으로 완료한다.
완료 시 활성 grant/Trainer·epoch·source version/deadline를 다시 확인한다.

I1의 S1 `Service.login` 본문/UoW 분할/ACK 보존/account lock 대기 순서를 재작성하지 않는다.
S1에서 지원되는 현재 admin 로그인만 유지하고 Trainer-only 우회 진입은 계속 금지한다. 필요 epoch 비교는
IAM proof/최종 session 저장 계약에 넣되 서비스의 installation 선취/cleanup 경로를 확대하지 않는다.
기존 유효 세션의 admin grant만 제거한 보호 사례는403이다. I2 실제 역할 회수는 명시 session 철회이므로
그 옛 cookie는401이다. 둘의 전제가 다르며 새 정책을 명목으로 기존403 assertion을 바꾸지 않는다.

## 7. 잠금·자기 세션 철회·최종 시간

신규 역할 명령의 순서: installation → Actor/대상 accounts UUID 정렬 → 영향 AuthSessions UUID 정렬 →
대상 credential/context를 기존 고정 테이블 순서와 각 id 정렬 → Trainer setup credential →
grant/binding → 실제 Home Branch → Trainer. binding 없는 첫 연결도 installation과 유일 제약으로 직렬화한다.
기존 W0/I1은 Branch→Trainer이며 `_trainer_scope`의 hint를 잠금 후 실제 fact/version/Home와 대조한다.
새 경로에서 Trainer 잠금을 먼저 잡은 뒤 Branch로 역행하지 않는다. credentials 종류별 순서도 기존
`revoke_management_sources`의 순서를 따르며 새 role 명령에서 그 helper의 모든 source 소비 동작을 호출하지 않는다.

범위 밖 요청은 사전 현재 인가로 걸러도 업무 UoW에서 전부 재검증한다. 실제 grant 전이는 lockedfact와
canonical 기대 버전/operation을 확정한 뒤 수행한다. 계정·grant·binding·철회·operation·typed audit은
같은 DB transaction이다. 감사/최종 확인 실패는 모두 rollback하며 C2 실패 기록을 지우지 않는다.

actor!=target이면 최종 actor 인증·현재 Scope·Trainer fact를 다시 확인한다. actor==target인 실제 변경은
자기 session을 정상적으로 철회하므로 일반 `authenticate`를 다시 호출해 성공을 rollback하면 안 된다.
철회 전 session_id/account/security/role epoch, assurance/live key, 원래 last_activity/absolute,
Actor 관리 grant/Scope/CSRF와 잠긴 사실을 내부 `RoleActorAuthorizationSnapshot`에 저장한다.
최종 confirm은 동일 잠금 아래 **이 명령이 만든 target revoke/role epoch 증가만** 예상 전이로 허용한다.
다른 계정 변화·admin grant/키 변화·version 불일치·pending/차단은 거절한다. 원래 last_activity를
갱신하지 않고 새 DB `clock_timestamp()`로 idle/absolute를 검사한다. audit가 지연돼 만료되면 rollback한다.
외부에서 snapshot/Caller를 주입할 수 없으며 다른 명령에 재사용하지 않는다. self no-op/replay는 철회가
없으므로 원래 일반 최종 인증을 사용한다. final confirm이 실패한 채 성공/새 쿠키를 반환하지 않는다.

## 8. operation·감사·실패 복구

organization+operation_id 유일. canonical payload에 Trainer/account/desired state/기대 버전/
identity_confirmed와 schema version을 포함하고 원문 Login ID/비밀은 fingerprint에 보관하지 않는다.
같은 id+다른 payload409, 같은 payload replay는 원래 outcome 반환이다. 현재 인가 후 replay를 먼저
판별하므로 원래 기대 버전이 현재와 달라졌다는 이유만으로 정당한 replay를 새 변경으로 실행하지 않는다.
최초 no-op도 durable operation을 기록해 나중 grant가 바뀐 뒤 같은 id가 새 전이로 해석되지 않게 한다.
새 operation의 no-op은 현재 버전 일치를 요구한다. changed=false는 epoch/audit 전이/세션을 바꾸지 않는다.
현재 상태와 committed 상태는 응답 필드를 분리한다. operation 보존은 GC로 취소하지 않는다.

새 typed `TrainerRoleEvent`는 add/revoke/regrant, organization/account/trainer, operation,
검증 Actor id/관리 role/branch, 실제 Home, 전후 granted/version/epoch 및 account version, 시각을 가진다.
최초 binding 여부도 구분한다. 원자적 성공당 한 건, no-op/replay/status에는 전이 감사 없음.
DB CHECK는 role_version/epoch 증가와 grant 전이, account/security version 불변, Actor branch==target Home(BA), 같은 조직 FK,
operation 한 건당 감사 한 건을 검증한다. 암호/token/전화/보상/관리자 키 정보는 감사하지 않는다.
감사 열람 권한은 기존 C7 Master 조직 범위이며 BA의 operation 조회를 감사 전체 열람으로 확장하지 않는다.

COMMIT ACK 유실은503/결과 불명으로 처리하고 role 변경을 별도 보상 transaction으로 되돌리지 않는다.
같은 operation status/replay로 대사한다. 실제 commit이면 모든 대상 인증은 철회된 채 유지되며
재로그인한 새 session은 status/replay로 다시 철회하지 않는다. commit 미확정이면 성공을 추정하지 않는다.
보존 operation/audit/grant/binding은 GC 대상이 아니다. 소비/만료된 ephemeral source/context/slot만
기존 lifecycle을 통해 제거한다. GET/status/no-op에서 암묵 GC로 다른 자료를 바꾸지 않는다.

## 9. 구현 후 검증과 인계 조건

아래는 제한 계약의 검증 기준이다. 실제 수행 범위·실패·미수행 경계는
[개발 결과](iam-012-trainer-roles-results.md)와 QA `coverage-map.json`을 따른다.
기존 I1 fast131/PG499/native211은 과거 기준이며 IAM012 독립 PASS가 아니다.

| 수준 | 필수 사례 |
| --- | --- |
| DB 없는 정책/계약 | ACTIVE/PENDING/DISABLED·Trainer active 조합, grant와 binding 분리, no-op canonical 충돌, typed event 전이, extra field/비노출 |
| 실제 PG 수직 흐름 | 실제 Bootstrap/UV/W0/최초 binding·겸임·회수·재부여, 마지막 역할 회수/기존 암호 재사용, PENDING 왕복/새 링크, Home 비활성 허용, 현재 BA Home·직접ID404 |
| proof와 보존 | admin recovery/reset pending 중 역할 회수와 기존 유효 source 새 ceremony/명시 재발급·비상 인계, 모든 대상 세션/대기 proof 차단, 다른 계정/C2/Passkey/admin/장기 source/이력 보존, 옛 링크/옛 proof 불가, inactive Trainer-only와 admin 겸임 분리 |
| 실패/무변경 | 각 저장·typed audit·final confirm rollback, 본인 변경 성공 및 audit 뒤 idle/absolute 만료 각각 rollback, no-op/replay/status 후 새 세션 보존, 실제 COMMIT ACK 유실 대사 |
| 독립 PG 연결/worker | 부여↔부여(같은/다른 account, 같은/다른 Trainer), 회수↔재부여, 로그인 proof/UV 완료↔회수, 초기 설정↔회수, reissue↔회수, C3/계정 차단/권한 변경↔역할 명령; 실제 PID/pg_blocking_pids와 양방향 순서 확인 |
| migration | 빈/실제0011 데이터 upgrade, grant/session/source epoch backfill·기존 인증 보존, 유일/FK/CHECK, 의미 있는 I2 이력 downgrade 거부, migration↔업무 실제 잠금 대기 |
| trusted HTTPS native | 실제 최소 UI 후보 선택/확인/겸임 UV/본인 성공 로그아웃/다른 대상 철회/미설정 재부여 새 링크/roleless 재로그인 거부, CSRF·fragment·쿠키·no-JS·비밀 비노출 |
| 회귀 | I1 영구 proof의 S1 ACK/대기·유효403/무효401·Trainer 현재 사실/typed audit와 기존 모든 보호 assertion 유지 |

독립 테스트 전 변경 소스/기존 보호 파일 SHA와 정확한 node/PG/native manifest 집합을 새 동결로 남긴다.
개발 대상 검사와 독립 새 단일 전체 PG/native 실행을 구분한다. 실패/error/skip/xfail/미수집·미완료는
성공으로 세지 않는다. 기존 native 항목을 줄이거나 고쳐 새 정책을 숨기지 않는다. 변경된 정책으로 기존
assertion과 실제 충돌하면 먼저 근거/정확한 계약 차이를 설계자에게 제출하고 임의 완화하지 않는다.
검사 자료는 고유 ignored QA 실행 폴더와 기존 fixture를 사용하고 최소 결과/소유 자원 정리 receipt를 남긴다.
개발→독립 테스트→설계자 인수→전담 한글 상세 커밋·일반 feature push 순서다.

## 10. 남은 게이트

이번 세 Product 결정은 해결됐으며 I2 안의 추가 사용자 질문은 현재 없다. 설계자는 계정 row_version과
역할 전용 epoch의 분리, 장기 복구 source와 새 context의 경계, 자기 철회 confirm 및 잠금/이전 proof
검출의 제한 구현 계약을 검토했다. 독립 사전 검토는 병행하며 실제 결함은 최종 소스 동결 전에 보완한다.
이 문서의 구현 진입 허용은 구현·실행 결과 인수나 전역 Architecture 승인이 아니다.
Operator·Home/state 명령·다른 사람 재연결·분실 암호 reset·PT/금융·실운영 및 해당 잔여
ARCH-001/002/MB-004 등은 OPEN이다. 전체22 OPEN/8 CLOSED·PD1 OPEN/26 CLOSED,
전역 PROPOSED와 ACCEPTED ADR 범위는 변경하지 않는다.
