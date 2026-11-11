# IAM-017 — 기존 계정 Operator 역할 관리·업무 지점 이동

Status: **IMPLEMENTED / DESIGNER LOCAL ACCEPTANCE PASS — APPROVED SPLIT VERIFICATION** (2026-11-12).
Parent `33c9e20ea36a7ce35833dbc1864b03d0b2c08355`, branch `codex/iam-operator-management`.
[OP-4/OP-5/OP-6](../product/product-decisions.md#review-20261111-operator-management), E5/G5,
BR-OPS-011/019·PR-001/021/026/030·NFR-001/004와 기존 비밀번호 전용 기준을 따른다.
전역 모듈/계약 PROPOSED·다른 Product OPEN/운영 승인을 닫지 않는다.

개발자 ACK와 독립 정적 진입 검토가 동일 계약 `a7f0d80f60e291b3fc1b2980012cd0ca3664eb47b2055432009c1c3cb001f268`에 PASS했다.
이후 F01/F02 보완 계약과 구현·독립 실행을 검토해 제한된 로컬 인수를 마쳤다.
[실행 결과](iam-017-operator-management-results.md)와 [최소 근거](iam-017-operator-management-review.json)의
새 fast197·선정PG380 분할(282+98)·실제 HTTPS2사례/5manifest, 원래 실패·교정·한계를 따른다.
전체695PG/단일 최종380 실행·전역 모듈 승인·원본 DB 전환/운영 배포 인수는 아니다.

## 범위와 상태

기존 계정 exact ID/UUID 조회 → Operator 첫 부여/회수/같은 지점 재부여 → Master의 유효 Operator 지점 이동 →
현재 역할·독립 관리/Operator/Trainer 업무·본인 암호/로그아웃·기존 수명/복구까지 연결한다.
Member/PT/보상/정산, 관리자 역할 추가·승격/Scope 변경, Trainer Home 이동은 범위 밖이다.

| 명령 | 대상 | 현재 인가/지점 |
| --- | --- | --- |
| 처음 부여 | 같은 조직의 Master/BA/Trainer/role0, 관리자 본인 포함. ACTIVE·암호 설정 완료·reset/recovery 대기 아님 | Master Organization 또는 추가할 최초 업무 Branch의 현재 BA. 새 배정 Branch는 활성 |
| 회수 | 보존 grant가 있는 모든 계정 상태 | 현재/보존 Operator 업무 Branch의 BA 또는 같은 조직 Master. 다른 역할 지점은 근거가 아님 |
| 재부여 | 보존된 같은 Branch, ACTIVE/PENDING_SETUP·DISABLED 제외 | 기존 Scope의 현재 관리자. 신규 배정 제한을 유지하고 다른 Branch를 지정해 이동을 우회하지 않음 |
| 이동 | granted=true인 Operator, PENDING_SETUP/DISABLED/reset 대기를 포함한 모든 계정 상태 | 같은 조직 Master만. 활성 목적지, 비활성 출발지 허용 |

회수된 grant의 다른 지점 이동은 OP-6의 유효 Operator 이동 승인에 포함되지 않는다. 이번 API로 허용하지 않는다.
역할0는 로그인할 수 없지만 계정/유효 암호·grant 이력은 보존한다. 상태·restore_state·reset/recovery intent,
독립 관리자/Trainer 역할·Home/업무 상태·C2와 과거 이력을 자동 변경하지 않는다.
다른 역할이 없는 계정의 ACTIVE/암호 준비를 현재 로그인 가능으로 잘못 판단하지 않는다.
재부여에 첫 부여의 암호 준비 조건을 일괄 복제하지 않는다. 관리자의 자기 역할 변경은 승인 범위이며
전체 계정 관리의 기존 noSelf/마지막 Master 보호를 전역 완화하지 않는다.

## IAM 값·저장·현재 인가

현재 `Caller.branch_id`/Account의 Branch는 계속 **Branch Admin 관리 Scope**다. 별도 OperatorScope와
Trainer binding/Home은 독립이다. 최초 grant 없음/version0과 granted=false의 보존 grant/양의 version을 구별한다.
기존 단일 grant/account·동일 조직 FK·삭제 금지·단조 version을 유지한다. 실제 변경은 정확히 다음 grant version을 쓴다.
회수/재부여·A→B→A로 과거 LoginProof/AuthSession/C3/reset/setup 준비 증명이 부활할 수 없다.

새 IAM 소유 Operator 역할 관리 공개 계약/구현을 기존 UoW에 연결한다. Application은 검증된 Caller와
Organization 공개 Branch 사실/잠금을 조합한다. 타 모듈 private Repository/ORM 직접 읽기를 추가하지 않는다.
최소 후보 조회는 새 역할 목적의 exact Login ID/UUID와 요청 최초 Branch 문맥을 사용한다.
대상이 이미 grant를 가졌다면 실제/보존 Branch로 현재 인가하며 요청 Branch로 덮어쓰지 않는다.
기존 Master 전용 일반 계정/lifecycle/감사 조회를 BA에게 열지 않는다. 다른 Organization/Scope는404,
비관리자의 관리 요청은403이며 클라이언트 role/org/다른 역할 Home/과거 issuer를 신뢰하지 않는다.

후보/상태 DTO는 account UUID·현재 ID·상태/암호 준비 여부·account version·raw Operator grant/업무 Branch·
grant version과 허용 명령에 필요한 최소 값만 반환한다. 다른 역할의 상세 관리 지점·Trainer 전체 프로필/전화·
Compensation Setting/정산·일반 계정 디렉터리를 추가하지 않는다.
role0인 former-Operator도 raw grant history를 **관리 대상 식별**에 사용해 기존 Master 수명/정상 reset을 지원한다.
이를 유효 로그인 역할이나 BA의 전역 관리 권한으로 사용하지 않는다. self-reset·마지막 Master·C2 제한은 유지한다.

## 명령·영수증·원자성

strict 입력은 operation UUID, target UUID, expected account version/Operator version, 역할의 desired boolean,
필요한 최초/목적 Branch만 받는다. 별도 move 명령을 두며 역할 요청으로 Branch 이동/다른 역할을 수정하지 않는다.
정규화 command와 실제 actor/account·action/Branch/expected versions의 canonical fingerprint를 저장한다.
조직+operation UUID receipt는 확정 결과와 현재 상태를 분리해 보존한다. 새 metadata 저장 장치를 만들지 않고 DB/UoW를 쓴다.

같은 UUID/다른 payload는409다. 일치 replay도 **현재** 인가를 먼저 검사하며 옛 Actor Scope를 보존하지 않는다.
원래 확정 버전은 현재 버전/권한을 뜻하지 않는다. 허용 receipt 조회는 현재 Scope와 원래 actor identity에 결속하고
secret/과거 다른 Scope의 상세를 노출하지 않는다. expected versions/인가를 만족한 실제 no-op는 grant/account/source/
세션 폐기·감사 변경을 반복하지 않는다. 최초 no-op의 receipt는 기록할 수 있으나 target 사실은 바꾸지 않는다.
no-op/replay 명령은 Actor 활동 시각도 늘리지 않고 원래 기한을 검증한다. 허용된 별도 상태 조회는 정상 읽기 활동 규칙을 쓴다.

설치 admission → 정렬 actor/target account → 영향 AuthSession → canonical credential/source/grant/binding →
공개 Branch 사실 순서로 잠근다. 동일 계정의 Op/I2/lifecycle/C3/reset/지점 상태 경합도 같은 순서를 사용한다.
실제 role mutation은 Op version 전진·기존 세션 철회와 필요한 초기/pending 원본 폐기·typed 감사·receipt를 같은 UoW로 저장한다.
I2와 같이 role mutation 자체로 계정 row/security·암호/reset 상태·독립 관리자 초기/정상 reset intent를 바꾸지 않는다.
새 암호/링크를 자동 발급하지 않으며 원래 reset 원본이 유효하다면 현재 사실로 새 proof를 준비하는 독립 절차를 유지한다.
비상 password proof도 slow hash 전에 raw Operator grant를 캡처하고 canonical 잠금 후/필수 감사 뒤 exact 대조한다.
역할 변경을 가로지른 옛 proof는 거부하되 살아 있는 독립 emergency source는 원래 기한/인가로 새 proof를 준비할 수 있다.
소비/폐기한 Op/Trainer 초기 원본을 되살리지 않는다. no-op/replay는 새 로그인과 원본을 다시 폐기하지 않는다.

실제 move는 **Operator grant version만** 전진시키고 옛 세션·모든 기존 인증/설정/reset/복구 링크를 폐기한다.
account row/security/reset generation은 보존한다. 기존 Handoff/비상 복구가 이 tuple과 원래 승인 lineage를 검증하므로
지점 이동으로 이를 전진/재기준화하지 않는다. 세션의 Op version·준비 증명의 raw grant와 실제 원본 소비/폐기로 옛 인증을 거부한다.
계정/restore_state·암호 준비/reset/recovery intent·C2·다른 역할/binding/Home은 유지한다. 정상/비상 복구의 기존
권한·대상·승인 원본/사건을 보존하며 이후 명시 재발급/인계 절차가 계속 동작해야 한다. 이 조합을 임의로 차단하거나
복구 상태를 지우지 않는다. 구현 전에 기존 복구 연계가 불가능하면 구체 원인/최소 해결을 진입 검토에 보고한다.
비상 case의 원래 snapshot/approval·lineage를 이동 결과에 맞춰 고쳐 쓰거나 새 delta lineage를 도입하지 않는다.
move/no-op·최초/regrant의 활성 Branch 조건은 실제 변경 여부를 구별하고 감사 뒤 공개 사실까지 다시 확인한다.

초기 Actor 인증은 touch 없이 원래 idle/absolute를 보존한다. 필수 감사/최종 현재 사실 뒤 마지막 DB clock으로
원래 기한을 검증하고 다른 대상 실제 성공만 한 번 touch한다. 감사 실패·원래 만료/인가 상실은 변경/receipt까지 rollback한다.
repo별 commit은 없고 새 링크/암호를 만들지 않는 역할 명령은 보안 slot을 선할당하지 않는다.

관리자 본인 실제 변경에는 **별도 typed expected post-state proof**를 사용한다. 허용 grant tuple/version·
정확한 세션/원본 폐기만 계산하고 감사 뒤 실제와 대조한다. account row/security/reset generation·admin Scope/암호/상태·Trainer epoch/
binding/C2의 비예상 변화는 거부한다. Trainer의 epoch+1 self_change나 logout 예외를 넓혀 통과시키지 않는다.
원래 policy/idle/absolute는 예외가 없고 이미 철회된 Actor 세션을 touch하거나 다른 요청에 재사용하지 않는다.
응답은 self 변경의 `reauthentication_required`를 명시하고 별도 재로그인을 요구한다.

## 복합 역할·원래 설정 목적·감사

로그인/C3/logout의 실제 Actor 선택은 MASTER → BRANCH_ADMIN → OPERATOR → 기존 Trainer-only 규칙이다.
Operator가 있다고 관리자 Caller를 false/NULL로 재구성하지 않는다. Operator 인증 감사에는 대상 업무 Branch와
실제 Actor Role/관리 Branch를 각각 기록한다. BA 관리 A/Operator 업무 B/Trainer Home C를 합치지 않는다.
새0017에서 기존 Operator auth kind의 CHECK를 실제 Master/BA Actor 문맥까지 명시 확장하되 원래16/감사 행은 불변이다.
로그인 후 관리자 capability/관리 UI를 유지하고 Operator/Trainer 본인 경로도 제공한다.
Operator 존재만으로 모든 겸임자를 관리자 화면에서 내보내거나 다른 Branch 업무/보상 권한을 부여하지 않는다.

새 typed 관리 감사는 actor/실제 role·관리 Branch, target account·전후 granted/업무 Branch/grant version,
계정 상태/version·operation ID·변경 시점을 남긴다. Audit가 저장을 소유하며 비밀번호/hash/token/IP 등은 기록하지 않는다.
보존 grant/receipt/감사는 transient credential GC로 지우지 않는다. 기존 GC의 고정 행수 bound를 주장하지 않는다.
새 transient family는 만들지 않는 안이며 원본 FK 변경 후에도 sweep·live orphan 배제·release 참조 양쪽과 SKIP LOCKED를 유지한다.

첫 Op 추가가 ACTIVE/PW-ready이고 기존 ACTIVE가 reset으로 PENDING_SETUP으로 내려가지 않으므로 지원 공개 흐름의
PENDING Op는 원래 Operator 신규 발급 목적을 유지한다. 이번에 새 initial-purpose column/backfill을 만들지 않는다.
원래 관리자/Trainer 초기 절차와 OP-2/OP-3 재발급을 보존한다. 예상 밖 pending mixed-role 자료는 목적을 추론/보정하지 않고
안전하게 진단/거부하며 Op 원본으로 관리자 암호를 설정하는 우회를 금지한다.

## API와 화면

| 목적 | 공개 경로 |
| --- | --- |
| 역할 후보/상태 | `POST /api/v1/admin/operator-roles/lookup`, `GET /api/v1/admin/operator-roles/{account_id}` |
| 첫 부여/회수/같은 지점 재부여 | `POST /api/v1/admin/operator-roles/{account_id}/changes` |
| Master 지점 이동 | `POST /api/v1/admin/operator-roles/{account_id}/branch` |
| 현재 인가된 요청 대사 | `GET /api/v1/admin/operator-role-operations/{operation_id}` |

독립 정적 검토 F01 보완: 위 **새 Operator 역할 관리 경로에만** 필수 UUID 헤더
`X-Y3-Expected-Actor`를 사용한다. 서버는 인증된 현재 Caller account와 일치하는지 읽기/쓰기 전에
검사하고 불일치하면409로 종료한다. 이 값은 권한 근거가 아닌 요청 문맥의 동시성 전제이며
실제 Role/Organization/Branch 인가는 계속 검증된 Caller에서만 얻는다. 다른 기존 API의 계약은 넓히지 않는다.
화면은 조회/쓰기/대사 전 현재 로그인 Actor를 확인하고, 달라졌다면 이전 선택·pending 문맥 사용을
중단한다. CSRF 발급과 명령 사이의 계정 변경도 서버의 위 전제로 차단한다. 늦은 응답을 게시할 때도
원래 선택/pending의 Actor·generation을 확인하며 다른 Actor에게 이전 UUID를 연결하지 않는다.
실제 A→B 탭 간 전환 및 확인 이후 전송 사이 전환의 음성을 HTTP/native로 검증한다.

기존 `/operator-accounts`와 관리/본인 UI·기존 HTTPS runner를 확장한다. 새 Framework/dependency는 없다.
후보/선택 계정·account/grant version·현재 Branch·읽기 generation과 쓰기 상태를 결속한다.
기존 Operator 신규 발급/링크 화면의 상태·발급 응답에도 Operator version을 명시하고 링크를 표시하기 전에
account version뿐 아니라 **현재 Branch와 Op version**까지 일치시킨다. row version이 같은 이동/role ABA 뒤의 옛 링크를 표시하지 않는다.
Operator 초기 링크 재발급 요청은 `expected_version`과 `expected_operator_version`을 함께 검증한다.
기존 Operator 화면·Lifecycle의 해당 setup action·실제 HTTP/native 호출도 함께 갱신하며 다른 목적의 재발급 입력을 일괄 변경하지 않는다.
늦은 조회/과거 receipt가 새 현재 상태/링크를 덮거나 중복 클릭이 새 쓰기를 만들지 않게 한다.
409/ACK 불명은 자동 재송신/보상 rollback 없이 같은 UUID/exact ID의 허용된 상태/receipt로 대사한다.
새 version만으로 자기 성공을 추정하지 않는다. self 철회 후에는 재로그인하고 같은 actor의 요청 결과를 확인한다.
재로그인을 넘어 pending operation을 유지할 때는 secret 없는 UUID/actor/account만 보관하고 현재 로그인 actor를 다시 대조한다.
권한 회수/이동으로 더 이상 현재 인가되지 않으면 과거 receipt로 조회를 계속 허용하지 않는다.

## 신규0017과 실제 검증 진입

원래0001–0016·ADR/deps/lock/공통 검증 장치는 불변이다. `0017_operator_management`는 현재 exact16/policy2
전제에서 source의 mutable (org,account,branch) FK를 안정 (org,account) grant FK와 원래 Branch snapshot FK로 분리한다.
필요한 stable unique constraint를 추가하고 기존 source Branch/grant version/기한/소비 상태를 바꾸지 않는다.
typed 관리 감사/receipt와 복합 Actor auth CHECK만 추가/수정하며 기존 role을 추론/backfill하지 않는다.
current runtime/CLI/UoW는 정확한 single17, 원래 policy2 transition target14는 유지한다.
독립 F02 보완: typed 감사의 첫 add만 이전 Branch 없음/version0을 허용한다. revoke/regrant/move에는
이전 Branch `IS NOT NULL`·이전 version 양수를 명시해 PostgreSQL CHECK의 UNKNOWN 통과를 막는다.
receipt와 감사의 대상·원래 Actor는 복합 FK로 결속하며 유효 receipt를 둔 NULL/0 직접 입력을 거부한다.

신규17 downgrade는 다른 policy/version/child/DDL 잠금 전에 installation 관계 AEX를 선취한다.
새 관리 이력/receipt,16 CHECK가 표현하지 못하는 auth Actor 행, 옛 source FK로 복원할 수 없는 snapshot은 DDL 전 거부한다.
원래16 gate/원래 역사와 전체17→16→15→14 rollback을 보존하고 비어 있는 표현 가능한17↔16 왕복을 검증한다.
이전16 runtime(parent33c9)은16 양성/17 음성, 현재17은16 음성/17 양성이다. runtime 자동 migration/원본 적용은 없다.

역사14/15/16 SQL/guard는 원래 shape에서 검증하고 current UoW/app 직전에 실제 head17까지 준비한다.
기존14→15/15→16 archive 대조를 보존하고17 helper는 실제 DDL/stamp를 rollback-only로 걷는다. marker만 바꾸지 않는다.
retained whole-row/multiset은 원래 cutover14 검사를 유지한 뒤 알려진 기본값/새 표만 명시해 전체 원래 행 보존을 확인한다.
직접16 module guard와 exact16 current 앱 소비자를 구분하며 숫자 문자열 전체 치환을 금지한다.

독립 기술 진입 이후 개발자가 관련 backend/src/tests/browser·신규0017·필요 개발 안내만 작성한다.
Root는 Product/Architecture, 독립 담당자는 read-only 검토 후 동결본을 별도 실행한다.
첫 허용 실행은 전체 collection/setup-plan으로 실제 graph/fixture/고정 revision/전체행 비교 영향을 확인한다.
실행0/필수PG gate의 exit1은 PASS가 아니다. 의미 있는 영향 검사를 고정하고 `--require-postgres -x`를 사용한다.

- 모든 대상 유형/first-revoke-regrant-move 상태와 Master/BA 현재 Scope·self·타 조직/지점 거부.
- Admin A/Op B/Trainer C의 실제 로그인·감사·독립 업무/C3/logout와 raw former-Op role0 수명/reset/재부여.
- 실제 grant/move ABA·준비 login/C3/reset/setup 증명·no-op/replay/new login 보존·현재 receipt/ACK와 UI 경합.
- 감사 실패/실제 별도 연결 대기 뒤 원래 Actor/source/preauth 기한 rollback·정확한 self delta/비예상 변경 거부.
- live/consumed/expired/locked source 이동과 old link/session 폐기·원래 목적 명시 재발급·GC/release/DB 제약.
- 실제17 writer/cleanup/migration 두 순서·연속 downgrade/손실 guard·기존16 회귀·previous/current runtime·역사 전체 행.
- 실제 HTTPS/native의 새 화면/본인 철회·409/불명 응답/늦은 읽기/중복 클릭. runner/manifest/실제 run-id·literal true를 대조.

QA는 ignored `.local/qa/` 고유 폴더와 기존 pytest/fixture만 사용한다. 새 수명주기 도구는 없다.
실제 node/exit/실패/미실행/경고·소유 자원 정리를 기록하고 개발→동결→독립 실행→설계자 검토→전담 한글 상세
커밋/일반 feature push로 마친다. 새로운 main merge/원본 DB 전환·배포는 포함하지 않는다.
