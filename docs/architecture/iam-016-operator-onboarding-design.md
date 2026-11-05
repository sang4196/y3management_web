# IAM-016 — Operator 발급·최초 설정·로그인 제한 계약

Status: **PRODUCT APPROVED / LOCAL ACCEPTANCE PASS — AUTHORIZED SPLIT VERIFICATION** (2026-11-05).
Parent `f54b89fd5991eee52969f7fd6e07fa916f6af9e4`, branch `codex/iam-operator-onboarding`.
[OP-2/OP-3](../product/product-decisions.md#review-20261105-operator-onboarding), BR-OPS-011,
A4/A8/C2/C3/C6/E2/E5/E6/G1/I1/I2/LC-1/LC-2와 비밀번호 전용 인증 기준을 따른다.
전역 모듈/UoW 설계 PROPOSED·다른 OPEN/운영 게이트를 승인하거나 닫는 문서가 아니다.
독립 기술 진입 검토와 개발자 ACK는 계약 `fa66ed76cb41aca5479d4b3755f615f028d25cca3d10a5bce12bf6043bde661c`를
대조해 차단 사항 없음으로 판정했다. 구현과 독립 실행/설계자 인수를 마쳤다.
[실행 결과](iam-016-operator-onboarding-results.md)와 [최소 인수 근거](iam-016-operator-onboarding-review.json)를 따른다.
최종 Backend178개에서 새 fast197·승인된 PG299 분할(118+181)·실제 native33조건을 확인했다.
원래 실패와 재사용 한계를 보존하며 원본 DB/운영 승인은 포함하지 않는다.

## 첫 증분과 제외 경계

허용된 현재 관리자의 새 Operator 발급 → PENDING_SETUP 조회/명시 재발급 → 본인 최초 비밀번호 설정 →
로그인/현재 역할·독립 업무 지점/자기 지점 기본정보 → 본인 암호 변경·로그아웃을 연결한다.
새 Actor가 기존 Master 전용 차단/복구·ID 변경·정상 reset과 GC/감사·Trainer 연결을 우회하지 않게 한다.
기존 Operator 계정을 기존 I2의 준비된 계정 대상으로 연결해 Operator·Trainer 겸임을 실제로 검증한다.
기존 계정에 Operator 역할 추가/회수, Operator 업무 지점 이동, Member/Pass/PT/보상 쓰기는 이번 증분에서 구현하지 않는다.
기존 E5/G5 승인을 취소하거나 그 기능을 영구 금지하는 뜻이 아니다. 관리자+Operator 조합의 신규 생성도 범위 밖이다.

## 역할·저장·인증

IAM이 별도 `OperatorGrant`/업무 Scope 사실을 소유한다. `Caller.branch_id`와 `Account.branch_id`는
**Branch Admin 관리 지점** 의미를 유지한다. Operator 지점을 이 필드에 대입하거나 비관리자를 Branch Admin으로
분류하지 않는다. 검증된 Caller/Authentication/현재 역할 값에 별도 typed Operator Scope를 추가한다.
Operator 업무 지점, 관리자 관리 지점, Trainer Home Branch는 독립이며 요청 role/org/branch 값은 권한 근거가 아니다.

신규 `0016_operator_onboarding`에서 account당 최대1개의 Operator grant(계정/조직/업무 지점·granted·양의 단조 version),
Operator 최초 설정 원본과 typed onboarding 감사 저장을 추가한다. 실제 계정/조직·조직/지점 관계를 복합 FK로 검증한다.
기존 계정에서 Operator를 추론/backfill하지 않는다. 이 증분의 grant는 신규 발급에서만 생성한다.
미래 회수 시 이력 row를 지워 version1로 재생성하는 ABA를 허용하는 기반으로 만들지 않는다.

준비된 로그인 증명과 발급 AuthSession은 계정 security_version/Trainer epoch와 별도로 Operator grant version에
결속한다. 기존 계정/세션의 Operator version은0이며 없는 grant를 세션의 유효 Operator 주장으로 승격하지 않는다.
현재 grant/조직·지점·상태/비밀번호 marker/정책·original lease를 KDF 준비와 최종 잠금/감사 뒤에 다시 대조한다.
grant가 없거나 무효라면 해당 역할을 쓰지 않는다. 유효 역할0이면 로그인/기존 인증 접근을 허용하지 않는다.
로그인 잠금에서는 준비 당시 암호 marker를 확인하고, 감사 뒤에는 같은 UoW의 정상 rehash를 반영한
기대 marker를 확인한다. 적법한 rehash를 다른 암호 변경과 혼동하지 않으며 다른 변경/ABA는 거부한다.

Operator-only와 유효 Operator·Trainer는 account audience로 로그인한다. 비활성 Trainer/grant 회수만으로
독립 Operator 권한을 제거하지 않는다. 일반 관리자 audience는 그대로 관리자 전용이다. 유효 Operator가
관리자 API를 직접 호출해도403이며, 기존 Trainer-only의 기존 거부 계약은 보존한다.
현재 계정 상태·암호 reset 대기·서버 세션 철회/idle30분·absolute8시간·C2·CSRF/Origin을 유지한다.
현재 ID만 로그인하고 옛 ID 영구 예약·고정 budget key/계정 실패 제한·원래 로그인 attempt 정체성을 보존한다.

## 발급·재발급·소비

신규 발급 Actor는 같은 Organization Master 또는 자기 관리 Branch Admin이다. 실제 활성 Branch에
고유 새 ID/계정·단일 Operator grant·초기 원본·필수 감사를 한 UoW에서 생성한다. 다른 지점/조직·기존 ID/
옛 예약 ID의 다른 계정 재사용·기존 계정 덮어쓰기·자동 동일인 연결·Operator/Trainer 단독 발급은 거부한다.
발급 후 Master 승인을 기다리는 상태를 추가하지 않는다.

재발급은 현재 PENDING_SETUP+유효 Operator grant에 대해 Master Organization 또는 **현재 업무 Branch**
Admin만 허용한다. 현재 expected_version이 맞아야 하며 실제 재발급은 row version을 전진시키고 이전 원본을 폐기한다.
ACTIVE/reset 대기/DISABLED의 초기 설정 우회는 불가다. 과거 발급자/이전 지점 관리자 권한은 남기지 않는다.
다른 관리자 역할의 최초 설정 인가를 Operator 재발급 경로로 우회하지 않는다.

신규 배정에는 Organization 공개 계약의 활성/assignable 조건을 사용한다. 기발급 계정의 명시 재발급과
기존 원본 소비에는 Branch.active/version 변화만을 자격 상실로 사용하지 않는다(OP-3). 실제 조직·현재
업무 지점/Operator grant·계정 상태/row/security·정책·purpose·단회·원래 기한은 계속 확인한다.
지점 비활성·GET·재시도만으로 원래 링크 기한을 연장하거나 폐기 원본을 살리지 않는다.

Operator source는 `purpose=operator_initial`, policy2, 계정/Operator grant version·업무 지점과 결속된
별도 원본이다. 기존 관리자·Trainer 초기 설정/reset/비상 source와 교차 소비할 수 없다. 무작위 원본의
digest만 저장하고30분 단회/재발급 시 이전 원본 폐기를 유지한다. KDF는 업무 잠금 밖에서 준비한다.
완료는 서버가 검증한 source의 현재 사실을 사용하며 클라이언트의 역할·조직·Scope를 받지 않는다.
필수 감사 뒤 원래 source/preauth 기한까지 확인하고 원자 소비/암호 저장/상태 전진·인증 철회를 확정한다.
최초 설정은 자동 로그인이나 Trainer 활성/role 복원이 아니다.

기존 bounded `credential` slot(최초 설정용) 할당/해제·consumed/expired SKIP LOCKED GC를 재사용한다.
새 원본을 GC sweep, orphan 배제, release 참조 검사 **양쪽**에 포함한다. 보존 grant/감사는 transient GC로 지우지 않는다.

## 기존 수명·겸임과 공통 변경

Master의 lifecycle 지원 대상 판정에 Operator를 추가하고 기존 noSelf/마지막 Master/동일 조직·세 상태
ID 변경/복구 목적지·C2 불변을 유지한다. 실제 차단/복구/rename/reset/C3/I2의 필요한 인증 폐기에
Operator source와 이미 준비된 증명을 포함한다. lifecycle 읽기의 admin_scope는 실제 관리 grant가 없으면NULL이다.
Operator 전용 최초 설정 권한이 기존 `/accounts/lookup`, `/access`, 관리자 `/activation`을 넓히지 않는다.

정상 reset은 같은 조직 다른 Master·기존 ACTIVE 대상과 원래 generation/source/기한 정책이다.
Operator+Trainer의 비활성 Trainer만으로 독립 Operator 계정의 reset을 막지 않는다. 본인 C3는 현재 암호를
확인하며 성공 시 모든 기존 로그인을 종료한다. 준비 digest/최종 사실에는 Operator grant/source를 포함한다.
로그아웃은 현재 세션만 종료한다. 비상 복구는 계속 기존 Master 전용 사건이다.

I2 첫 연결의 준비 조건을 기존 관리자 또는 유효 Operator인 ACTIVE/login-ready 계정으로 확장한다.
행위자는 계속 Master 또는 실제 Trainer 현재 Home Branch Admin이고 활성 Trainer·일대일 동일인 확인을 유지한다.
현재 Operator 업무 지점만으로 Trainer Home 관리 권한이 생기지 않는다. 같은 binding 재부여 ACTIVE/PENDING,
DISABLED 제외·상태 무관 회수·실제 역할 변경의 모든 로그인 철회/epoch 전진·no-op/replay 규칙을 그대로 적용한다.
W1 Trainer 비활성화의 Trainer-only 세션 철회가 유효 독립 Operator 세션을 철회하지 않게 한다.
Trainer 접근은 현재 활성/grant 조건을 따르고 Operator 접근은 자기 업무 Scope를 따른다.

## UoW·감사·API·UI

기존 설치→정렬 actor/target 계정→영향 세션→canonical source/grant/binding→필요한 Organization/Workforce
공개 사실 잠금 순서에 새 원본/grant를 일관되게 넣는다. 타 모듈 private Repository/DB 직접 읽기를 추가하지 않는다.
최초 Actor authenticate는 touch 없이 원래 idle/absolute를 보존한다. 필수 감사·최종 현재 사실 읽기 뒤
마지막 DB clock으로 원래 기한을 확인하고 성공 활동만 같은 시각으로 갱신한다. 기존 self-change 예외를 넓히지 않는다.
필수 변경·감사·소비/계정/Scope는 모두 함께 commit/rollback한다. Repository별 commit은 없다.

발급/재발급/설정 완료는 typed `OperatorAccountEvent`와 Audit 소유 저장으로 대상 Operator 역할·업무 Branch,
계정/버전 전후·Actor/실제 Role·Branch Context·시점을 남긴다. login/logout/C3는 실제 Operator 맥락을 기록하고
nonMaster→BRANCH_ADMIN 또는 nonAdmin→Trainer-only fallback을 사용하지 않는다. 비밀·원문 IP·브라우저는 기록하지 않는다.

| 목적 | 제한 계약 |
| --- | --- |
| 발급 | `POST /api/v1/admin/operator-accounts`, body login_id/branch_id |
| 현재 결과 대사 | `POST /api/v1/admin/operator-accounts/lookup` 완전 일치 ID, `GET /api/v1/admin/operator-accounts/{id}` |
| 명시 재발급 | `POST /api/v1/admin/operator-accounts/{id}/initial-setup`, expected_version |
| 본인 설정 | `POST /api/v1/auth/operator-credentials/complete`, 기존 preauth/CSRF/비밀번호 입력 계약 |
| 자기 Branch | `GET /api/v1/operator/branches/{branch_id}`, 실제 현재 Operator Scope를 Organization 공개 읽기 계약에 전달 |

관리 조회는 Master Organization/Branch Admin 현재 Operator 업무 Branch의 최소 계정 상태/version/Operator Scope만 반환한다.
일반 디렉터리/다른 역할·Trainer 전체 프로필·보상·로그인 이력 조회를 만들지 않는다. Operator 자기 Branch 응답은
기존 id/code/name 기본 DTO이며 다른 Branch ID/조직은404다. 기존 관리자 Branch 목록/조회 helper를 Operator에게 열지 않는다.
`/auth/me`는 실제 OPERATOR와 업무 Branch를 독립 역할로 반환하며 admin capability를 부여하지 않는다.

기존 HTML/CSS/JS와 검증 runner를 확장해 관리자 `/operator-accounts`, 수신자 `/operator-activate#token=...`,
내 계정의 Operator/겸임·업무 Branch/C3/logout을 연결한다. 새 프레임워크/의존성은 도입하지 않는다.
fragment는 요청 전에 제거하고 GET은 비소비, no-JS 비밀 제출 금지·자동 로그인 없음·현재 링크 폐기를 유지한다.
읽기 세대/선택 계정/version/쓰기 상태를 결속해 늦은 응답·중복 클릭·옛 링크 재표시를 막는다.
409/ACK 불명은 권한 있는 exact ID/UUID로 현재 상태만 확인한다. version 증가를 자기 성공 영수증으로
오해하거나 POST 자동 재전송/보상 rollback/옛 secret 재조회하지 않는다. 미전달 링크는 OP-2 명시 재발급으로 처리한다.

## Migration·진입·검증

원래0001–0015와 ADR/의존성/lock은 불변이다. 원래 policy2 transition.target0014를 변경하지 않고
새 runtime/CLI/UoW는 정확한 단일0016 schema를 요구한다. 구15 runtime은16을, 신runtime은15를 거부한다.
새 값/보존 이력이 있으면0016 downgrade는 DDL 전에 거부하고, 빈 신규 사실은15로 의미 손실 없이 왕복한다.
여러 revision을 지나 옛 손실 guard가 거부할 때 전체 원상 rollback을 검증한다. runtime 자동 migration/원본 DB 전환은 없다.
연속 downgrade 중 새 정리 UoW와의 잠금 역전을 막기 위해0016 downgrade는 installation 관계의 배타 잠금을
다른 preflight/자식 잠금보다 먼저 얻는다. upgrade/공통 preflight·원래 DDL/guard와 runtime은 이 교정으로 바꾸지 않았다.

역사 검사는 원래14/15 revision에서 해당 SQL/guard를 검증하고, **현재 UoW/앱 실행 직전에는 실제 current head**로 준비한다.
0015 lifecycle 왕복과 current 앱 기동 양성은 별도 단계/fixture로 구분한다. legacy_helpers의 guard 준비는
실제16→15→14 DDL/marker를 rollback-only에서 수행한다. 원래 guard를 고치거나 marker만 바꿔 우회하지 않는다.
전체 collection/setup-plan으로 fixture·literal revision·current 소비자를 먼저 확인하고 미실행 gate exit1은 PASS가 아니다.

독립 기술 진입검토 후 개발자만 관련 backend/src/tests·신규0016·필요 개발 안내를 수정한다.
Root는 Product/Architecture를 관리하며 테스트 담당자는 read-only 검토 후 동결본의 별도 실제 실행을 맡는다.
다음의 양성/음성 대조와 영향받은 기존 회귀·실제 HTTPS/native를 선정해 정확 node/exit/미실행/한계를 남긴다.

- Master/자기 Branch Admin 발급·현재 Scope 재발급, 다른 지점/조직/Operator/Trainer 거부, ACTIVE/DISABLED 우회 거부.
- 신규 inactive 배정 거부와 기발급 후 inactive 설정/재발급 성공, 옛 원본/다른 purpose/만료/preauth 실패.
- Operator-only·Operator/Trainer의 서로 다른 두 지점, admin 승격 방지, 자기 Branch 한정, Trainer 비활성/회수 독립성·역할0 거부.
- 일반 login/C2·prepare proof·C3·reset·lifecycle·I2·원래 기한·필수 audit 실패/DB 대기·ACK·원자 rollback.
- slot/GC/release 양방향·source version/준비 증명 ABA, DB cardinal/FK/CHECK 및 schema15/16 양방향/손실 guard/역사 시작점.
- 실제 발급→설정→로그인→자기 Branch→C3/logout·관리자 거부와 UI 원본 폐기/409/불명 응답/늦은 읽기.

실행 자료는 ignored `.local/qa/` 고유 폴더와 기존 pytest/fixture를 사용한다. 새 수명주기 관리 도구는 없다.
자기 프로세스/schema/폴더를 정리하고 최소 인수 근거·미해결 자료만 보존한다. 완료는 독립 테스트→설계자 검토→
전담 한글 상세 커밋·일반 feature push다. 새 main merge/운영 배포/미결정 기능은 범위 밖이다.
