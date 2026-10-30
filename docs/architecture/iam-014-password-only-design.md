# IAM-014 — 전 역할 아이디·비밀번호 인증 재설계

2026-10-31. Product 방향은 사용자 승인/ADR-0005 ACCEPTED다. 이 문서는 제한 기술 계약이며
독립 방향·상세 설계 검토를 마쳤다. 실제 DDL/미분류 영향군의 구현 전 기술 게이트는 남아 있으며, 코드·migration·runtime 테스트·실제 DB 전환·운영 인수는 미완료다.
기준 parent: `7855786c9f5352748b70e2597397064b853c13b2`.
[현재 Product](../product/product-decisions.md#review-20261031-password-only),
[ADR-0005](../decisions/0005-password-only-authentication.md)를 우선한다.

## 1. 변경과 보존

지원 v1 Master/Branch Admin/Trainer와 겸임은 아이디·비밀번호만 사용한다. Operator도 같은 제품 정책을
따르지만 미구현 업무/모델을 이 증분에 새로 추가하지 않는다. Member는 Future Scope다.
Passkey 등록/복수 관리/삭제/분실 재등록·WebAuthn 인증·비밀번호 뒤 추가 인증을 현행 기능에서 제거한다.
선택 Passkey·Master 예외·OTP/SMS·외부 인증 서비스를 만들지 않는다.

A10/AB4 및 M1–M5/M7의 Passkey 의무만 대체한다. M6 발급 Actor, M8 본인 관리자 reset 금지,
A8/C5/A9/AB5/R4·C1/C2/C3와 기존 역할·지점·업무 상태·민감정보 인가는 유지한다.
기존13 revision과 과거 승인/인수 결과는 원문 보존한다. 예전 PASS를 새 password-only PASS로 옮기지 않는다.
앞서 미답변인 PENDING_SETUP 차단/복구 및 Login ID 대상 상태 확대는 별도 보류다.

## 2. 사용자 흐름

| 업무 | 새 계약 |
| --- | --- |
| 최초 Master | 현재 제한 CLI/확인된 DB target/getpass 두 번/설치 잠금/UoW를 유지한다. Master 본인이 보호된 TTY로 암호를 설정하고 ACTIVE·해시·조직·grant·감사를 commit한다. 첫 key/enrollment 파일 단계만 제거한다. 자동 로그인·기본 암호·Bootstrap 재실행 없음. |
| Branch Admin/추가 Master | 기존 인가된 발급자가 PENDING_SETUP 계정과30분 단회 source를 발급한다. 대상자가 링크에서 직접 암호를 설정하고, 현재 source/계정/원래기한 재검증 뒤 ACTIVE·hash·소비·감사를 원자 commit한다. 완료 뒤 별도 로그인한다. |
| Trainer 최초 설정 | I1 실제 Trainer/동일인 binding/현재 grant·업무 조건·Home 관리 Scope와 목적별 source를 유지한다. 기존 일반 관리자 source를 Trainer source로 혼용하지 않는다. |
| 로그인 | 지원 역할에 하나의 ID/PW 로그인. 성공 시 session 발급, MFA ceremony/키 선택 없음. 현재 계정/role/Trainer fact를 재검증하며 일반 logout은 현재기기만, 기존 C3/C4/C6/I2 철회는 전기기 정책을 유지한다. |
| 본인 암호 변경 | C3의 현재 비밀번호 확인과 전 로그인 종료를 유지한다. C1에 없던 관리 행위 추가 비밀번호 확인은 도입하지 않는다. |
| Master 암호 reset | A8/C4/C5/M8·본인확인·단회30분·명시 재발급·generation·현재 지원 대상과 원자성은 유지하고 관리자 live-key 조건만 제거한다. |
| 정상 계정 관리 | 기존 Actor·현재 조직/지점/대상/버전·noSelf·마지막 Master 보호 유지. Passkey/UV 조건 제거가 범위 확대/관리자 승격은 아니다. |
| 마지막 Master 암호 분실 | AB5 업무책임자 승인·별도 운영담당자 실행·ACTIVE Master 한명·대상만 철회·승인 원본/사건 이력·ACK 대사 유지. Passkey 요인 선택·재등록은 없다. |
| 정상 Master 복귀 후 인계 | R4대로 같은 조직 다른 정상 Master가 기존 사건의 허용된 password 범위만 이어받아 필요한 새 링크를 명시 발급한다. 본인 reset/다른 대상/역할 복원 권한은 얻지 않는다. |

정상 Master는 현재 ACTIVE·Master grant·유효한 저장 암호·password-reset 대기 아님과 유효한 현재
password AuthSession으로 판단한다. key 유무/옛 key set은 근거가 아니다. 일시 C2 제한을 권한 회수나
마지막 Master 수 감소로 재해석하지 않는다. 정상 비밀번호 재설정은 현재 인증된 다른 Master/noSelf·
설치/정렬 Account·affected AuthSession 잠금으로 C5/A9 보호를 유지한다.

AB5의 “모든 Master 로그인 불가”는 기존 업무책임자 승인과 별도 운영담당자의 보호된 수동 확인 사실이다.
DB의 hash 존재 수로 비밀번호 분실 여부/사용자의 실제 로그인 능력을 자동 증명하지 않는다. hash가 남았지만
암호를 잊은 ACTIVE Master도 기존 승인된 비상 암호 복구 대상이 될 수 있다. 유효 저장 hash는 평문 암호를
사전 검증하거나 사용자가 기억한다는 뜻이 아니며 실제 로그인 검증은 별도다. C2 일시 제한이나 마지막 Master
집계를 운영 복구 자동 승인/예산 해제 조건으로 쓰지 않는다.

## 3. 인증과 인가 경계

ADR-0004 PG AuthSession+opaque Cookie는 유지한다. 신규 session은 password 인증 사실과 현재 정책
버전에 묶인다. 계정 ACTIVE/security_version/role_epoch·현재 역할/Scope·로그인 제한·세션 원래 idle30분/
absolute8시간을 검증한다. 클라이언트 role/branch_id/assurance 값은 근거로 쓰지 않는다.

admin audience의 유효 former-admin403, Trainer-only의 admin 진입401 등 현재 오류 경계를 보존한다.
비활성 Trainer-only/role0/차단 계정은 로그인/업무를 허용하지 않고, 독립 관리자 겸임은 해당 관리 Scope로만
판단한다. inactive Home를 신규 전 지점 접근 권한으로 쓰지 않는다. compensation의 Home Scope 제한도 유지한다.

기존 실패 제한·흔한 비밀번호 차단/15~128자·Argon2·hash admission·안정 login_budget_key/이전ID 예약을
유지한다. Session/원본/source-slot의 bounded 용량·정리·timeout, account 비노출, generic auth422·DB503도 유지한다.
새 authentication에는 Passkey나 과거 key metadata를 읽는 조건을 두지 않는다.

로그인 commit ACK가 불명확하거나 응답을 전달하지 못하면 cookie를 발급하지 않는다. 같은 attempt/새 session으로
입증되는 미전달 로그인은 별도 안전한 UoW로 철회하되 이미 commit된 session/slot/attempt 자식과 로그인 감사 자체를
cascade 삭제하거나 실패 성적으로 다시 쓰지 않는다. 원래 S1의 committed-child 보존과 후속 Trainer의 미전달
session 철회를 함께 검증한다. 상태를 입증하지 못하면 보수적으로 보존하고 원래 bounded 만료/정리로 대사한다.
암호 reset·설정 링크의 ACK 유실은 계정 상태/확정 원본을 되돌리지 않고 safeGET+명시 재발급으로 처리한다.

## 4. IAM 공개 계약과 구성

새 `PasswordResetPort`와 IAM 내부 `password_reset.py` adapter로 현재 MFA의 reset 여섯 경로를 이동한다.
현재 public ResetState/ResetProof/ResetChange의 비-key 의미, source 목적/target/조직/불변 binding 지원을
유지한다. reset용 좁은 대상 판정을 일반 계정/관리 Scope 판정에 합쳐서 권한을 넓히지 않는다.

IAMPort가 계정·발급/초기 설정·현재 password 인증을, SecurityPort가 admission/단회 source 수명을 소유한다.
EmergencyPort/HandoffPort는 IAM/암호 reset 계약에 의존하고 MFA 객체를 받지 않는다.
Work 조립에서 MFAPort/MFA/Ceremony/키 proof 및 필요 없는 추가 factor 옵션을 제거한다.
모듈 추가·내부 HTTP·새 auth framework는 없다. 같은 IAM 모듈 내부 저장소 변경을 업무 모듈로 노출하지 않는다.

`TrainerRoles.ready/stable_actor`, `_current_principal`, IAM.authenticate/confirm_login, 추가Master/Workforce의
mode guard도 전수 점검한다. key/UV 조건만 제거하며 현재 account/grant/업무 fact·epoch·소비/감사는 보존한다.
`RoleActorSnapshot`은 같은 요청/UoW에서 새로 만든 원래 세션 사실을 쓴다. 필수 업무·감사·최종 사실 읽기 뒤
마지막 DB clock으로 원래 기한을 검사하고 같은 checked now로 성공 활동만 갱신한다. default touch=False와
자기 역할 철회 특례·no-op Login ID 활동 비갱신을 유지한다. Repository별 commit이나 Router 업무규칙 집중은 금지다.

단일 명시 설정 `Y3_IAM_MODE=password`를 사용하도록 구현한다. `mfa`/`s1_password`는 자동 호환하거나
약한 fallback으로 쓰지 않고 설정 오류로 거부한다. 현재 `require_mfa`를 무조건 성공시키는 stub은 만들지 않는다.
명시 설정 및 전환 schema/policy marker가 일치해야 새 앱을 시작할 수 있다. 현재 production 거부는 유지한다.

## 5. 전환 경계와 원본 보존

신규0014 이후 forward migration으로 설계한다. 기존0001–0013 raw 및 역사 review/감사 값은 고치지 않는다.
[직접 영향 전환 상세](iam-014-password-only-transition.md)에 policy2 marker/복합FK/전환 감사/기존 GC·proof/lineage 명세를 정리했다. 실제 DDL/인덱스·코드와 미분류 영향군 검토는 아래 P0의 구현 전 조건이며 아직 migration이 아니다.
새 빈DB upgrade와 기존0013에 데이터가 있는 upgrade를 모두 지원·검증해야 한다.

전환은 모든 기존 worker/CLI/GC를 정지하는 유지보수 방식이다. 현재 한호스트 worker1 ProcessGuard와
같은 대상 배타 잠금을 운영 절차로 확보하고, 새 앱은 schema/revision와 영속 password 정책 marker를 확인한다.
구버전 재기동·혼합 버전 운용은 지원하지 않는다. migration의 DB lock이나 marker만으로 구 바이너리를 자동
탐지·중단했다고 주장하지 않는다. 실제 운영자/대상·보호 backup/restore와 배포 확인은 운영 게이트다.

전환 transaction은 단회 id/정책 marker를 기록하고 보안 version/필요한 account version 증가·기존 양 assurance
session 전부 철회·setup/trainer_setup/reset/recovery/emergency/preauth 원본과 파생 MFA 권한의 폐기를 함께 수행한다.
실제 권한 없는 이전 proof/토큰이 새 API에서 소비되지 않도록 source/session/proof 정책 버전을 명시 검증한다.
role epoch·grant/binding/Home/업무state·기존 hash·login_budget_key/실패/cooldown은 전환 편의로 바꾸지 않는다.
진행 waiting/verifying attempt를 성공으로 전환하거나 예산을 초기화하지 않는다. 신규 발급과 기존 지문 재사용을 구분한다.

권한 폐기/flag 정리/필수 전환 이력과 marker는 한 transaction이다. 실패는 전체 rollback한다.
실제 commit ACK 유실은 marker/operation/revision·결과 요약으로 대사하며 반복 실행으로 version을 중복 올리거나
링크를 재발급하지 않는다. 전환 뒤 이미 폐기한 자격의 복원은 rollback 전략이 아니다. 데이터 있는 unsafe
하향 migration은 DDL 전 거부하고 forward repair한다. 빈 상태 하향 여부도 P0 loss guard에서 명시한다.

기존 key/요인/audit/사건·승인 원본의 역사 사실은 보존한다. Passkey 개인키는 원래 서버 자료가 아니다.
기존 `password_uv`를 `password`로 고쳐 과거 인증 사실을 위조하지 않는다. MFA 역사 row/FK·enum이 남아도
현행 인증/사용자 기능은 아니다. 새 runtime/기본GC는 key/Ceremony를 발급하거나 인증 근거로 사용하지 않는다.
Readiness의 과거 FK 존재 검증과 Master의 허용된 역사 감사 열람은 활성 factor 의존과 구분한다.

staged MFA hash는 계정 암호로 승격하지 않는다. 폐기된 파생 권한은 현행 단회 자격의 비밀 제거/GC 정책대로
안전 종료하되 원본 Account hash/감사/사건은 삭제하지 않는다. 역사 키·원본 DB를 물리 purge하는 retention 결정은
LEGAL/운영 게이트이며 이 증분의 기본 동작이 아니다. DB 초기화·과거 migration 삭제·무작위 cascade 정리는 금지한다.

## 6. 상태별 기술 판정

아래는 새 사용자 인증수단 선택의 제한 기술 적용이다. 기존 차단 해제/권한 복구 또는 새 password 승인으로
확대하지 않는다. 실제 원본 DB를 조사하지 않았으며 해당 자료가 없다는 가정을 하지 않는다.

| 기존 사실 | 전환 판정 |
| --- | --- |
| ACTIVE + durable hash + password reset 대기 아님 | hash/역할/계정/업무 사실 유지. 옛 권한을 폐기하고 새 policy에서 password 로그인 허용. key 없는 최초 Master도 동일하다. |
| PENDING_SETUP, context 임시 hash만 있음 | PENDING 유지, 임시 hash 승격 없음. 옛 source 폐기 뒤 현재 적격 관리자가 새 최초 설정 링크를 명시 발급한다. 기존 I1 active/grant/동일인 조건 유지. |
| DISABLED | DISABLED 유지. 원래 hash/역할/password pending 사실 보존. 정책 전환을 restore로 쓰지 않는다. |
| password_reset_pending 또는 null durable hash | 기존 password 복구 필요를 보존한다. 현재 정상 Master의 지원 reset/명시 재발급 또는 해당 ACTIVE Master의 AB5가 필요하다. null hash를 채우거나 옛 암호를 복원하지 않는다. |
| ACTIVE + 유효 durable hash + password_reset_pending=false + 실제로 폐지 key요인만 대기 | 현재 사건/원본/계정 사실을 일치 검증한 후 폐지요인 대기를 종료하고 `retired_feature` 이력을 남긴다. key 인증 완료나 account restore로 기록하지 않는다. 현재 역할/Trainer 상태에 따른 로그인 차단은 별개로 유지한다. |
| both 사건에서 password 이미 완료, key만 미완료 | 위 순수 폐지요인 판정을 증명한 경우 남은 key 범위만 retired로 종료한다. 과거 password 완료/승인·사건 원본은 보존한다. |
| both/password 사건에서 password 미완료 | 기존 승인된 password 범위를 보존한다. 옛 토큰은 폐기하고 현재 인가·사건/대상/버전을 검증해 새 password source를 명시 발급/인계한다. 자동 완료·자동 발급 없음. |
| passkey-only 사건 | 그 승인으로 새 password reset 권한을 만들지 않는다. key 범위는 역사/retired로 남긴다. 별도 정상 Master의 A8 행위 또는 필요한 AB5의 password 승인 절차를 사용한다. |
| 모순·출처/대기 의미/승인 범위 분류 불능 | 개인별 원본 자료를 보존한 채 전환을 fail-closed로 중단한다. 임의 hash/ACTIVE/grant·새 승인 TTL을 대입하지 않는다. |

key 관련 legacy flag는 폐지요인의 역사값/전환 결과로 분리한다. DISABLED·PENDING 등에서 legacy flag를
현재 유효 password 대기로 오해하지 않으며, 후속 restore/최초 설정도 새 password 요건과 기존 독립 정책을 따른다.
이는 미답변인 PENDING 차단/복구 상태 확대를 허용하는 계약이 아니다.

**기한 구분:** 기존 source의 expires_at/단회성은 갱신하지 않는다. 현재 권한으로 명시 재발급한 새 source는
기존 정책의 새30분을 가진다. 링크 만료가 업무책임자의 원래 승인 범위를 password로 확대하거나 없던 승인 TTL을
만드는 근거가 아니다. R4의 원본 링크 만료 후 정상 Master 인계는 유지한다. ACK 재조회/동일 operation 재실행으로
추가 링크나 새 기한을 만들지 않는다. AB5 legacy both→password 자식의 연결/승인 원본·subset·복합FK는 P0에서 고정한다.

## 7. 제거와 동등 검증

| 현행 대상 | 변경/동등 검증 |
| --- | --- |
| /auth/passkeys/*, /auth/login/passkey/verify, passkey-recovery·enroll·passkeys 화면, navigator.credentials | 현행 route/JS/schema에서 제거하고 폐기 경로404를 확인한다. 사용자에게 숨기기만 하거나 optional fallback을 남기지 않는다. |
| CLI enrollment 파일/인자·복구 factors passkey/both | 신규 실행에서 제거/거부한다. 설치 getpass·확인된 target·한번설치·보호된 승인 전달·원자성은 유지한다. 원문 암호/토큰을 argv/stdout에 내보내지 않는다. |
| MFA/MFAPort/Ceremony와 WebAuthn imports·직접 의존성 | 기존 암호 업무를 먼저 분리하고 제거한다. 새 앱/CLI/current pytest collection이 WebAuthn에 의존하지 않아야 한다. 공유 전이 dependency는 실제 사용 확인 후 제거하며 관련 없는 upgrade 금지다. |
| 기존 UV/RP/서명·key counter·복수 key/키 분실 검사 | 폐기된 기능군으로 분류하고 이유를 기록한다. pass/skip/xfail로 가장하지 않는다. 역사 Git/결과는 보존한다. |
| MFA 테스트에 섞인 Scope/CSRF/C2/clock/source/동시소비/audit/ACK·GC | 기존 assertion 의미를 유지/재작성하고 새 node에 매핑한다. 새 실제 CLI/HTTP password fixture로 검사하며 가짜 Caller/직접 DB 활성화로 정상 업무 흐름을 대체하지 않는다. |
| reset/추가Master/AB5/handoff 및 I1/I2/W1/Workforce native | 공개 암호 발급·초기 설정·로그인으로 재구성한다. 링크 fragment 비노출/단회/현재권한·typed 감사·미전달 쿠키철회·safeGET·명시재발급·원래기한·자기철회 특례를 보존한다. |
| 전환 state fixture | migration 입력 상태를 만드는 명시적 SQL seed는 일반 사용자 E2E와 구분한다. 실제FK/제약·옛 revision 사실을 검증하고 실제 전환·rollback/ACK를 관찰한다. |

과거 fast131/PG614/선정179/native243은 새 인수 수가 아니다. 실제 수집/명단과 실행·실패·제외/삭제 사유를
분리하고 숫자 맞추기·timeout/guard 완화·원래 실패 숨김을 금지한다. 독립 담당자가 작성한 사례 소유 관계도 명시한다.

## 8. 구현 진입과 검증 단계

- P0 사전 상세: 기존 source/DDL/FK/audit/GC의 전체 의존 목록, 직접 영향 기존 node/assertion의 유지/재작성/기능삭제
  대응표, 새 policy marker·정확 epoch/token/session 계약·필수 전환 audit·AB5 legacy lineage와 상태별 판정식을 제출한다.
  직접 영향군의 전환 상세는 별도 문서에서 검토한다. 아직 미분류인 군은 실제 변경/삭제 전 그 보안 의미와 대응을 제출해 root가 확인한다. 임의 source 삭제/DB 전환을 먼저 하지 않으며 진짜 정책 변경만 사용자에게 묻는다.
- P1 구현: P0를 검토한 동일 범위의 password-only backend/CLI/UI와 신규 forward migration을 하나의 호환 경계로 구현한다.
  0014 이름/DDL 상세와 API signature는 P0의 확인된 계약으로 고정한다. 기존 DB에 실제 migration을 실행하는 지시는 아니다.
- P2 개발 검증: 정적 import/설정/route·패키지 점검, 전 역할 password 로그인/현재Scope/role0/inactive/겸임·발급/reset/C3/
  마지막Master/AB5/R4, 새빈DB/legacy data전환·원래 source/반복실행/불일치/일부실패/실제 commit ACK를 검사한다.
- P3 독립 인수: frozen source의 실제 영향 명단·노드/개별 결과·기한/동시성·native HTTPS·환경/trust 불변과 자기 자원 정리를 확인한다.
  실행하지 않은 운영/실물/지원 브라우저 목표를 통과로 보고하지 않는다. source/migration/legacy history 원문도 대조한다.
- P4 설계자 인수·전담 커밋: 현재 코드/실제 결과와 계약을 대조하고 문제는 재지시한다. 상세 한글 commit/일반feature push 후
  완료된 일회성 QA는 최소 근거를 남겨 정리한다. 사용자 미결정 항목과 원본/공유 DB·미디어·설정·인증정보는 보존한다.

현재 이 문서 단계에서는 앱·테스트·dependency/lockfile·migration을 변경하지 않았고 runtime/DB 검증을 실행하지 않았다.
전체 모듈 PROPOSED와 Product22 OPEN/8 CLOSED·PD1 OPEN/26 CLOSED 및 운영 인수/production 거부는 유지한다.
