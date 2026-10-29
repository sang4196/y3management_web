# 현재 WORKFORCE-002 인수 완료 — 분할 검증

2026-10-30 **Trainer 업무 비활성화·재활성화 로컬 설계자 인수 PASS**.
[계약](workforce-002-trainer-state-design.md), [결과](workforce-002-trainer-state-results.md),
[최소 인수 근거](workforce-002-trainer-state-review.json)를 따른다. 현재 Master/실제 Home Branch Admin의
상태 관리, 독립 관리자 인증·원래 초기 source 보존, Trainer-only 기존 로그인 철회, 원자적 상태 이력과
감사를 검증했다. 오래된 실제 조회 응답이 새 링크/현재 상태를 덮는 UI 결함을 인과 재현해 수정했다.

최종 동결248개/Backend162개에서 fresh fast **131개**, PostgreSQL **315개 분할 근거**를 확인했다.
이는 R1의 변경 없는 서버 검사206개와 R2의 새109개이며 최종 단일315/전체576 실행을 뜻하지 않는다.
R2 같은 실행의 native8개 manifest **225항목**이 모두 true였다. 최초 R1 **209 passed/1 failed/105 미실행**은
실패로 보존한다. 동일 증상의 실제 지연 응답을 재현·수정했지만 최초 통신 순서는 미확정이다.
소스/Git/trust 불변과 자동 실행21개 정리·실제 경로 부재를 대조했다. 설계자는 runtime을 추가 실행하지 않았다.

전담 변경 검토·상세 한글 커밋·일반 feature push 뒤, 이미 승인된 A8/C4/AB3/M8에 따른 **IAM-013 Trainer
분실 암호 reset** 제한 계약으로 이어간다. A8 Master 전용 권한을 재질문하지 않는다. 해당 후속은 QA 초안의
기술 검토만 완료했으며 별도 진입 지시 전 미구현이다. 현재 source 인수로 운영·실물/전체 브라우저·전체 모바일,
다른 Product OPEN·전역 PROPOSED 또는 PT/지급/정산 검증을 승인하지 않는다. 아래 서술은 각 증분 당시 이력이다.

# Architecture 및 현재 개발 단계

2026-10-30 최신 인수: **IAM-012 기존 계정 Trainer 역할 로컬 인수 PASS**.
[승인 I2 세 선택](../product/product-decisions.md#review-20261030-i2)을
[제한 계약](iam-012-trainer-roles-design.md), [검증 결과](iam-012-trainer-roles-results.md),
[설계자 최소 판정](iam-012-trainer-roles-review.json)으로 확인했다. 불변 동일인 연결과 현재 grant를
분리하고, 실제 추가/회수/재부여의 대상 전 로그인 철회·무역할 접근 차단·독립 관리자/복구 source 보존,
PENDING_SETUP 복귀·명시 새 링크, 현재 Home 인가와 작업 대사를 검증했다.

동결238개/Backend155개에서 독립 fast **131개**, 새 단일 전체PG **541개**(기존499+신규42),
같은 실행의 실제 HTTPS/native10개 manifest **247항목**이 통과했다. 실패/error/skip/xfail/xpass/
incomplete는0이며, 실제 exit·정확한 node·개별 판정·소스/보호200·HEAD/index/trust·소유 자원 정리를
대조했다. 초기 실패와 원인 미확정 native 응답 읽기 이력은 보존한다. 운영·실물/전체 브라우저·모바일
전 흐름·다른 Product OPEN/전역 PROPOSED는 이번 인수로 승인하지 않는다.

후속은 전담 한글 상세 커밋·일반 feature push 뒤 **Trainer 업무 비활성화/재활성화 W1**의 제한 계약이다.
B1/B2의 Actor/현재 Home Scope는 이미 승인됐으므로 다시 묻지 않는다. IAM 계정/grant와 업무 상태,
독립 관리자 세션과 유효 초기 source를 분리한다. 현재 W1 구현/검증은 미완료다.
아래 각 증분의 미완료/대기 서술은 당시 이력이다. 설계자의 후속 변경은 문서뿐이고 Backend155개를 유지한다.

2026-10-27 최신 인수: **IAM-011 실제 Trainer 계정 발급·로그인 로컬 인수 PASS**.
[계약](iam-011-trainer-login-design.md), [검증 결과](iam-011-trainer-login-results.md),
[설계자 판정](iam-011-trainer-login-review.json)을 따른다. 현재 Master/실제 Home Branch Admin의
일대일 계정 발급·미설정 링크 재발급, 수신자의 직접 암호 설정, Trainer 암호 로그인·최소 본인 조회·
본인 암호 변경/전 로그인 종료·로그아웃을 검증했다. 관리자 UV와 현재 역할/Trainer 상태 검증은 유지한다.

r3 동결225개/Backend145개에서 독립 fast **131개**, 새 단일 PostgreSQL **전체499개**를 통과했다.
기존419개와 신규80개가 같은 실행에 포함되고 실패/error/skip/xfail/xpass/incomplete는0이다.
같은 실행의 실제 HTTPS/native9개 manifest **211항목**은 모두 true이며 브라우저 pytest6건 안의 항목이다.
개별 실제 판정과 소스/보호/HEAD/index/trust 불변, 소유 자동 환경7개의 정리를 대조했다.
두 중단 실행15/2/464와89/1/396 및 원래 실패는 보존한다. S1 호환과 유효 인증403/무효401을
앱에서 복원했고 기존 실패 단언을 바꾸지 않았다. 이전 CLI 준비 오류 한 건의 원인은 여전히 미확정이다.
동일 node의 최종 전체 실행 통과를 원인 규명으로 보고하지 않는다.

설계자의 후속 변경은 결과/단계/판정 문서뿐이며 테스트한 Backend145개 바이트를 유지한다.
전담 변경 검토·한글 상세 커밋·feature branch 일반 push 절차를 따른다. 다음 I2의 기존 계정 Trainer 역할
추가/회수는 대상 상태·무역할 로그인·기존 로그인 처리의 필요한 사용자 결정을 모은 뒤 진행한다.
운영·실물/전체 브라우저·새 Trainer 모바일 인증 인수와 PT/정산·전체 모듈 PROPOSED/잔여 OPEN은 별도다.
아래 각 증분의 대기/미완료 설명은 당시 이력이다.

2026-10-27 r3 개발 이력: **인증·인가 응답 경계 복원 개발 동결, 당시 독립 검증 대기**.
r2 독립 whole은89 passed/1 failed/396 미완료로 중단·정리했다. 유효한 세션의 관리 grant만
회수된 기존 handoff 사례에서 기대403 대신401이 확인됐다. `IAM.authenticate`에서 세션 유효성·
필수 UV/키 검증을 먼저 수행하고, 관리 audience의 유효한 무역할/무binding 계정은 touch/Caller 반환 전
403으로 거절하도록 좁게 복원한다. account audience의 미지원 계정과 Trainer 관리 진입401은 유지한다.
이는 무역할 로그인 허용이나 새 Product 정책이 아니다. r1/r2 동결·실패 이력을 보존한다.
r3 대상41개는 최초39 passed/신규 fixture2 failed 후 해당2개 passed로 확인했다. 기존 assertion은
그대로이며 fast131·mypy95·Import Linter8을 통과했다. 수집630/PG499, native manifest211이며
새 단일 독립 전체 실행과 설계자 인수는 대기 중이다. r3에서는 native 브라우저를 재실행하지 않았다.

2026-10-26 r2 개발 이력: **S1 복원 개발 검증·동결 완료**.
[승인 I1-Q1–Q3](../product/product-decisions.md#review-20261026-i1)와
[제한 구현 계약](iam-011-trainer-login-design.md)에 따라 실제 활성 Trainer의 일대일 계정 발급,
본인 초기 설정·로그인·자기 암호 변경·로그아웃을 구현한다. 비활성 Home도 허용하되 현재 관리 Scope를 강제한다.
[개발 결과](iam-011-trainer-login-results.md): fast131·신규 PG62개 대상 검사·신규 native23개를 확인했다.
첫 독립 whole은15 passed/2 failed/464 미완료로 중단·정리했다. 기존 S1 ACK 보존과 account 대기 순서를
use_cases.py에서 복원하고 기존 assertion 그대로3개, Trainer 관련22개를 통과했다. 기존 기능/native 대상은
16 passed/1 bootstrap setup error 뒤 동일 실패 node 단독 재실행1 passed였다. 최초 오류 원인은 미확정이다.
r2 fast131·native23/23을 확인했고 총617/PG486으로 동결했다. 최초 수집612/PG481과 원래 freeze는
이력으로 보존하며 새 독립 whole PG486/native211이 필요하다.
아래 W0의 세 선택 답변 대기는 이 승인으로 대체된다. 독립 전체 검증·설계자 인수·커밋은 아직 완료되지 않았다.
I2 기존 계정 역할 연결·상태/이동 명령·분실 복구·PT/정산·운영 인수는 포함하지 않는다.

2026-10-21 최신 인수: **WORKFORCE-001 Trainer 최초 등록 로컬 인수 PASS**.
[계약](workforce-001-initial-registration-design.md), [결과](workforce-001-initial-registration-results.md),
[설계자 판정](workforce-001-initial-registration-review.json)을 따른다.
현재 MFA Master/Branch Admin이 실제 Home 관리 범위에서 필수 이름·전화·세 보상값·기본급 시작 월을 입력하면
Trainer/최초 snapshot/operation/두 typed 감사를 한 UoW로 확정한다. G1의 비활성 Home 기존 조회/replay는 유지하고
신규 배정은 활성 Home만 허용한다. 정확한 금액 문자열·명시0·설정 지속·권한·실패 rollback/중복 방지를 검증했다.

최종 동결210개/Backend133개·보호180개 revision4에서 독립 fast **122개**, PostgreSQL **전체419개**를 통과했다.
새 단일 PG 실행에 기존391개와 신규28개가 포함되며 실패/error/skip/xfail/xpass/incomplete는0이다.
같은 실행의 실제 HTTPS/native58/20/15/11/12/23/17/32항목 총188개가 모두 true였다(브라우저 pytest5건 안의 항목).
최초204 passed/1 failed/214 미완료와 재현 실패 두 건은 보존한다. 실제 잠금을 놓친 기존 SQL prefix 관찰을
소유 연결의 PGAPPNAME/pg_blocking_pids로 보완했고 원래 이력·거절·정리 조건은 유지했다.
기존0001–0009/env/의존성과 제품 runtime을 보완 과정에서 바꾸지 않았다. 최종 소스/HEAD/index/trust 일치와
자동 환경4개 정리를 확인했다. 설계자는 runtime을 추가 실행하지 않고 소스와 실행 근거를 검토했다.

다음 I1은 실제 Trainer의 계정 발급·본인 설정·로그인이다. 발급 대상 활성 조건, Trainer당 계정/미설정 재발급,
비활성 Home 신규 발급의 세 운영 선택은 사용자 답변 대기이며 구현하지 않았다. I2 역할/겸임·상태/이동·PT/정산과
production/실물/전체 브라우저·보존은 미인수다. 아래 과거 증분의 현재/미완료 설명은 당시 이력이다.
전체 모듈/데이터 PROPOSED, Product OPEN/ADR 상태와 개발→독립 테스트→설계자 검토→전담 한글 커밋·일반 push를 유지한다.

2026-10-21 최신 인수: **IAM-010 정상 Master의 기존 비상 복구 인계·명시 재발급 로컬 인수 PASS**.
[R4 승인](../product/product-decisions.md#review-20261020-ab5-r4)에 따라 같은 조직의 다른 현재 정상 MFA Master가
최신 미완료 운영 사건의 링크 만료 후 인계한다. 원래 대상·요인·운영 승인 이력을 보존하고 새 발급의 실제 관리자를 기록한다.
[계약](iam-010-emergency-handoff-design.md), [실행 결과](iam-010-emergency-handoff-results.md),
[설계자 판정](iam-010-emergency-handoff-review.json)을 따른다.

동결194개 소스에서 독립 fast **105개**와 PostgreSQL **전체391개(신규27+기존364)**를 새 단일 실행으로 통과했다.
같은 PG 실행의 기존58/20/15/11/12/23 및 새17개 브라우저 항목이 모두 true였다. 새17개는 실제 정상 관리자
인계/재발급과 both 수신자 UV/재로그인이며, 세 요인 전체는 실제 DB/서버 crypto 검사로 검증했다.
최종 DB 시각 lease·활동 선갱신 없는 만료·실제 서로 다른 Master 경합·UV 뒤 재발급·COMMIT 응답 유실을 확인했다.
소스/보호172개·HEAD/index·신뢰 저장소 불변과 자동 환경4개 정리를 대조했다. 기존0001–8/env/의존성을 보존하고
새0009와 승인된 기존 회귀의 retained-head 기대 상수 한 줄만 변경했다. 과거 AS-IS13개 checkout의 CRLF/Git LF 차이는
이전 인수 raw SHA와 같고 논리적 변경이 없음을 확인했으며 파일을 변환하지 않았다.

전담 최종 변경 검토·한글 상세 커밋·일반 push 후, 실제 Trainer 로그인의 선행인 최소 Trainer 등록/필수 최초 보상 설정을
별도 Workforce 계약으로 구체화한다. 그 후속·계정 연결/겸임·PT/정산·실제 운영/보존·실물/전체 브라우저는 아직 인수하지 않았다.
Product OPEN/ADR/전체 모듈 PROPOSED 상태는 유지한다. 아래 각 증분의 현재/미완료 설명은 당시 이력이다.

2026-10-20 최신 인수: **IAM-009 제한된 AB5 비상 인증요인 복구의 로컬 개발 인수 PASS**.
[AB5 R1–R3](../product/product-decisions.md#review-20261020-ab5-r1-r3)에 따라 기존 ACTIVE Master 한 명의
승인된 비밀번호·Passkey·두 요인만 복구한다. 대상의 기존 로그인과 대기 인증만 철회하며 다른 계정·다른 요인·C2를 보존한다.
[구현 계약](iam-009-emergency-recovery-design.md), [독립 검증 결과](iam-009-emergency-recovery-results.md),
[설계자 판정](iam-009-emergency-recovery-review.json)을 따른다.

동결183개 소스로 독립 fast **105개** 및 필수 PostgreSQL **전체364개**를 새로 실행해 모두 통과했다.
신규37개와 기존327개의 단일 PG 실행 안에서 실제 HTTPS/native58·20·15·11·12·23항목이 모두 true였다.
감사 NULL 제약·인과적 재발급 순서·운영 명령 권한·실제 commit 뒤 응답/인터럽트 처리 및 새 downgrade 잠금 문제를
동결 전에 수정하고 이번 전체 회귀로 확인했다. 보호72개·HEAD/index 불변과 자동 실행4개 정리를 대조했다.
기존0001–0007·의존성을 보존하고 새0008만 추가했다. Import Linter의 operating 계층 등록 외 기존 계약은 유지했다.

전담 변경 검토·한글 커밋·일반 push 후, 사용자가 승인한 **R4 정상 Master의 기존 비상 복구 인계**를 별도 계약·증분으로 진행한다.
R4는 이번 소스에 구현되지 않았다. 실제 운영자 provision/OS 분리·승인 진위/별개 인간·보존·배포·실물/전체 지원 브라우저는
이번 로컬 인수로 증명하지 않는다. Product OPEN/ADR/모듈 PROPOSED 상태는 유지하며 아래 각 증분은 당시 이력이다.

2026-10-18 최신 인수: **IAM-008 다른 Master 차단·복구·Login ID 변경의 제한된 로컬 개발 인수 PASS**.
현재 정상 MFA Master가 같은 Organization의 다른 Master를 관리한다. 자기 대상은 이번 증분에서 제외하며,
원래 암호·Passkey·관리 Scope·실패 제한을 보존하고 실제 변경 시 대상의 기존 로그인과 대기 인증 증명을 철회한다.
[계약](iam-008-master-management-design.md), [실행 결과](iam-008-master-management-results.md),
[설계자 판정](iam-008-master-management-review.json)을 따른다.

동결155개 소스로 독립 fast **96개**와 필수 PostgreSQL **전체327개**를 새로 실행해 모두 통과했다.
이번 PG는 신규81개와 기존246개를 포함한 **단일 전체 실행**이며, 이전 증분의 분할 검증을 재사용하지 않았다.
같은 실행의 신뢰 HTTPS58·native MFA20·관리15·reset11·새 Master 관리12항목이 모두 true였다.
검토에서 발견한 비밀 포함 가능 테스트 locals, 철회 cookie 재로그인, 서명 검증 이후 경합의 검증 공백을
소스 동결 전에 보완하고 이번 전체 검사로 확인했다. 소스/보호62개·HEAD/index 일치와 자동 실행4개 정리를 대조했다.
새 migration·의존성 변경 없이 기존0001–0007과 Product/ADR 상태를 유지했다.

전담 변경 검토·한글 커밋·일반 push 절차를 따른다. 다음 AB5 비상 복구의 대상 상태·철회 범위·승인 확인 방식은
사용자 결정 대기이며 구현하지 않았다. 실물/모바일/지원 브라우저 전체·운영 본인 확인/전달/기록·production과
복합 역할/Workforce·PT·정산은 이번 인수 범위가 아니다. 아래 각 증분의 최신/미완료 표현은 당시 이력이다.

2026-10-18 최신 인수: **IAM-006/007 관리자 인증수단 관리·비밀번호 재설정의 제한된 로컬 인수 PASS(분할 검증)**.
본인 Passkey 목록/마지막 키 보호/삭제 시 모든 로그인 종료(M7), 정상 Master의 추가 Master 발급,
다른 정상 Master의 관리자 Passkey 복구와 ACTIVE 관리자 비밀번호 재설정(M8 본인 reset 금지)을 구현했다.
[관리 계약](iam-006-mfa-management-design.md), [재설정 계약](iam-007-password-reset-design.md),
[개발·독립 결과](iam-007-password-reset-results.md), [설계자 인수](iam-007-password-reset-review.json)를 따른다.

최종 fast **91개**와 실제 PostgreSQL **246개 검증 항목의 성공 근거**를 대조했다.
PG는 후보3 전체245 실행의 **244 passed/키 선택 테스트1 failed/exit1**을 보존하고,
앱과 다른105개 파일을 유지한 채 해당 테스트만 고쳐 후보4의 두 UUID 정렬 경우를 독립 통과시킨 분할 검증이다.
최종 수집337=fast91+PG246의 정확한 항목 집합·다른 함수 AST·소스 해시·정리를 확인했다.
**최종 소스로 PG246 전체를 한 번에 실행해 통과했다는 뜻은 아니다.**
동일 앱/브라우저 소스의 실제 신뢰 HTTPS58·native MFA20·관리15·reset11은 모두 true였다.
소스/명령 오류·중단 이력과 원래 실패를 숨기지 않았고, 검증 중/후 실행 자료는 소유권 확인 후 정리했다.
새0006/0007만 추가했으며 기존0001–0005·Product/ADR/의존성은 보존했다.

전담 최종 변경 검토·한글 커밋·일반 push를 거쳐, 이미 승인된 다른 Master 차단/복구와
ACTIVE 다른 Master Login ID 변경을 다음 증분으로 진행한다. 이 후속과 AB5 비상 복구,
운영 본인 확인/전달/기록 정책·실물/모바일/지원 브라우저 전체·production은 아직 인수하지 않았다.
아래 MFA-A 및 이전 날짜의 현재/미완료 표현은 해당 시점의 이력이다.

2026-10-18 최신 인수: **IAM MFA-A 최초/복수 Passkey 등록·비밀번호+UV 로그인의 제한된 로컬 개발 인수 PASS**.
보호 CLI의 최초 Master 준비, Master가 실제 발급한 Branch Admin의 본인 설정, 정상 MFA 본인의 추가 키 등록과
각 키 로그인·Backend 지점 제한을 검증했다. [구현 계약](iam-005-mfa-a-design.md),
[검증 결과](iam-005-mfa-a-results.md), [설계자 인수 근거](iam-005-mfa-a-review.json)를 따른다.
동결79개 소스에 독립 fast **88개**, 필수 PostgreSQL 전체 **144개**가 통과했고,
해당 PG 실행의 신뢰 HTTPS 기존 **58항목**·native MFA **20항목**이 모두 true였다.
R1–R5/PF1 보완·초기 실패/부분 검사·정리 결과를 실제 최종 통과와 구분했다.
webauthn3.0.1과 필요한 전이 의존성만 추가했으며 0001–0004·기존 패키지 버전·Product OPEN/ADR 상태는 유지했다.
`codex/iam-mfa-a`의 전담 최종 변경 검토·한글 커밋·일반 push 뒤, 이미 승인된 본인 키 삭제(M4/M7) →
추가 Master(M6) → 정상 다른 Master의 분실 복구(M2/M5)를 다음 증분으로 진행한다.
그 후속 기능·M8 관리자 reset·AB5 비상 복구·실물/모바일/지원 브라우저 전체와 운영 인수는 아직 미완료다.
production 거부는 유지한다. 아래 각 날짜의 최신/미착수 설명은 해당 시점 이력이다.

2026-10-18 후속 정책: [M7/M8 승인](../product/product-decisions.md#review-20261018-mfa-m7-m8)은 본인 Passkey 삭제 성공 시 전 로그인 종료·Master 본인 관리자 reset 금지다. 현재 MFA-A 등록/로그인 증분과 분리해 다음 삭제/관리자 reset 계약·실제 검증에 적용하며 아직 해당 후속 기능 인수는 아니다.

2026-10-18 MFA-A 진입: [M3–M6 승인](../product/product-decisions.md#review-20261018-mfa-m3-m6)으로 첫 등록 신뢰 경로/본인 추가 등록·마지막 삭제 금지·복구 링크30분·추가 Master 발급 Actor를 확정했다. 현재 다음 개발 단위는 실제 계정 준비/최초 등록 → 비밀번호+UV Passkey 로그인 → 본인 복수 등록/각 credential 로그인이다. 삭제/분실 복구/추가 Master·운영 비상 복구는 별도 증분으로 분리한다. 구현·독립 인수 전이며 아래 최신 구현 PASS는 S2c다. 정책 선택만으로 production 거부/운영 게이트를 해제하지 않는다.

2026-10-16 MFA 후속 정책: [M1/M2 승인](../product/product-decisions.md#review-20261016-mfa-m-batch)으로 관리자 복수 Passkey 등록/로그인 시 하나 사용과, 같은 Organization의 다른 정상 Master에 의한 관리자 본인 확인·기존 Passkey/모든 로그인 폐기·일회용 링크 재등록을 확정했다. 추가 등록/삭제·마지막 인증수단 보호·구체 계약/운영 확인/실제 검증은 후속이다. 아래 Passkey 등록·분실 복구의 미결정 중 M1/M2만 대체한다. MFA 코드·migration·의존성은 변경하지 않았고 최신 구현 인수는 S2c로 유지한다.

2026-10-15 최신 인수: **IAM S2c Login ID 변경의 제한된 로컬 개발 인수 PASS**.
현재 Master가 같은 Organization의 ACTIVE Branch Admin ID를 변경하며 이전 ID는 원계정에 예약한다.
기존 암호/Scope를 보존하고 대상 모든 로그인을 종료하며 실패 제한을 새 ID에도 유지한다.
실제 변경은 현재 Master의 활동만 갱신하고 동일 ID no-op·거부/최종 만료·감사 실패는 원자성을 유지한다.
[구현·검증 결과](iam-004-login-id-results.md), [인수 요약](iam-004-login-id-review.json), [기술 계약](iam-004-login-id-design.md)을 따른다.
최종 독립 검사 fast **81개**, 실제 PostgreSQL 전체 **97개** 및 그 안의 신뢰 HTTPS **58항목**을 확인했다.
초기 테스트 실패·소스 인계 중단·활동 누락 보완/이전 소스 검증은 최종 통과와 구분해 기록했다.
S2b는 `0a947f9bccc615140b4a3ea24809790aa452172e`로 origin/codex/iam-s2b-password-change에 푸시했다.
이번 S2c는 `codex/iam-s2c-login-id`에서 완료했고 전담 커밋 담당자의 최종 검토·한글 커밋·일반 push를 따른다.
Product/ADR/OPEN 상태는 유지한다. Master/다른 상태·역할의 ID 변경, 관리자 reset/추가 Master/Workforce,
운영 MFA/비상 복구/배포·전체 IAM은 후속 범위다. Passkey 등록·분실 복구의 미결정 권한을 임의 구현하지 않는다.
아래 이전 완료/미완료 설명은 해당 시점 이력이다.

2026-10-15 최신 인수: **IAM S2b 본인 비밀번호 변경의 제한된 로컬 개발 인수 PASS**.
현재 비밀번호 확인 후 본인 자격을 바꾸고 현재 장치 포함 모든 기존 로그인을 종료한다.
현재 비밀번호를 아는 마지막 Master도 허용하며 Scope·기존 로그인 실패 대기시간을 유지한다.
[구현·검증 결과](iam-003-password-change-results.md)와 [설계자 인수 요약](iam-003-password-change-review.json)을 따른다.
개발·독립 담당자 모두 fast **69개**, 실제 PostgreSQL 전체 **49개**를 통과했고 그 안의
실제 신뢰 HTTPS 브라우저 필수 **48항목**을 확인했다. 추가 동일 비밀번호 입력 검사1개와
privacy 의도적 실패6개는 정규 통과 건수와 구분한다. 현재 운영/MFA·복구/전체 IAM 완료는 아니다.
기존 완료분은 `c2b01076298e3b1fee9d75ea71acf0184edbd859`로 origin/main에 푸시했다.
이번 S2b는 `codex/iam-s2b-password-change`에서 구현·검증했고 Product/ADR/OPEN 상태는 유지한다.
사용자 후속 지시로 완료 증분은 전담 커밋 담당자의 변경 검토 후 한글 상세 메시지로 커밋·푸시한다.
사용자 결정이 필요한 변경은 승인 전 커밋하지 않으며 승인된 후속 작업은 계속 진행한다.
아래 이전 단계/대기 설명은 해당 시점 이력이다.

2026-10-14 최신 인수: **IAM S2a Branch Admin 일반 차단 해제의 제한된 로컬 개발 인수 PASS**.
같은 Organization의 현재 Master가 DISABLED Branch Admin을 복구하고 기존 암호로 새 로그인한다.
옛 인증은 되살리지 않으며 권한/version·감사·실패 제한을 보존한다.
[구현·검증 결과](iam-002-restore-results.md)와 [설계자 인수 요약](iam-002-restore-review.json)을 따른다.
최종 fast 68개, 실제 PG 24개 및 수정 후 실제 HTTPS 브라우저 1개/31항목을 확인했다.
이는 단일 실행 DB 25개 통과나 S2 전체/운영 완료를 뜻하지 않는다.
기존 pytest QA 정리도 검증했고 [정리 결과](qa-cleanup-results.json)에 삭제·유지 대상을 기록했다.
현재 실행/정리 방법은 [backend 안내](../../backend/README.md#qa-실행-자료와-정리)를 따른다.
아래 2026-10-13까지의 현재 단계/대기 설명은 해당 시점의 이력이며 Product/ADR/OPEN 상태는 변경하지 않았다.

2026-10-13 최신 인수: **첫 IAM S1a/S1b 개발 인수 PASS**. [구현·검증 결과](iam-001-s1-results.md)와 [설계자 판정](iam-001-s1-review.json)을 따른다. 실제 CLI Bootstrap, 로그인/현재 Scope, Master 지점·Branch Admin 발급/설정/X1 복구, Backend 지점 제한, logout, 차단·Scope 변경/철회 및 필수 감사 원자성을 구현했다. 개발자와 독립 담당자 모두 fast **58개**, 실제 PostgreSQL **18개**를 통과했고 별도 실제 HTTPS·경합·장애·migration 왕복 결과를 대조했다. 단일 WSL 호스트/ASGI worker1의 개발 인수이며 운영 배포·MFA/복구·전체 IAM/v1 완료는 아니다. 아래 미착수/인수 대기 및 기반만 완료했다는 기록은 이 인수 이전의 이력이다. Product OPEN/ADR 및 전체 모듈의 PROPOSED 상태는 변경하지 않았다.

2026-10-13 사전검증 판정: [새 PREP 결과](prep-iam-001-results.md)와 [독립 재현·설계자 판정 근거](prep-iam-001-review.json)를 대조해 **제한된 개발용 IAM S1 구현 진입 PASS**로 판정하고 개발 담당자에게 S1a→S1b 구현 진행을 지시했다. 실제 IAM 인수는 아직 완료하지 않았다. 단일 호스트/ASGI worker1·시작 배타 잠금/해시 동시2 및 실제 상태 총량·수명 통합 검증을 적용한다. Product OPEN/전체 모듈의 PROPOSED 상태와 운영 MFA·복구·배포 게이트는 유지한다.

2026-10-13 최신 착수 지시: 사용자가 개발 담당자의 **사전검증 통과 후 첫 IAM 구현(IAM-S1a→S1b)**과 별도 `테스트노예` 세션의 독립 검사, 설계자의 결과 검토·재지시를 승인했다. [S1 전달 범위](iam-001-decision-pack.md#s1-implementation-handoff-20261013) 및 [구체 계약](iam-001-decision-pack.md#review-20261013-s1-contracts)을 이번 증분의 작업 기준으로 사용한다. 미해결 사전검증을 우회하거나 Product OPEN/전체 모듈 설계의 상태를 바꾸는 승인은 아니다. 아래 이전의 별도 구현 지시 대기 기록은 이 지시 전 이력이며, 실제 구현·검사 완료 여부는 담당자 결과와 독립 검토로 갱신한다.

최신 부분 해결: [2026-10-13 AB 승인](../product/product-decisions.md#review-20261013-ab-batch)의 AB1–AB6 모두 1번이다. 월 정산 대상은 적용 기본급/월별 지정·유효 PT/보상대기 지원 PT/추가실적 등으로 자동 선정하며, 한 달 전체 Trainer 비활성·명시 기본급0·무활동·정정 대기 없는 경우 새 정산 확정 의무에서 제외한다. 기존 이력/미완료와 비활성만으로 기본급을 자동0으로 바꾸지 않음은 유지한다. 후속 reset 링크30분·운영 관리자 비밀번호 뒤 Passkey·업무책임자 승인/별도 운영담당자 비상 복구·Chrome/Edge/Safari 최신2개 안정 주버전을 선택했다. K3/X1 첫 IAM/별도 구현 지시·구체 계약 PROPOSED와 22 OPEN/8 CLOSED는 유지한다.

2026-10-12 일괄 승인 반영: B1–B7/A1–A10의 선택은 [2026-10-12 일괄 승인](../product/product-decisions.md#review-20261012-batch)을 따른다. A4/A5만 2번으로 최초 설정 링크 30분 및 전 역할 공통 idle 30분/absolute 8시간이다. 다른 항목은 1번이며 v1 PG AuthSession+opaque Cookie 방식은 ADR-0004 ACCEPTED, JWT는 후속 버전의 재검토 후보다. 새 Pass 활성 담당 필수/상품 횟수 최초 부여·인가 관리자 발급 횟수 초과 추가, Trainer 재활성화/비활성 전용 로그인 제한, 데이터 있는 Branch 비활성화/신규 업무 차단·원본 보존, 공통 한국 시간도 확정됐다. 모듈·저장/계약/UoW·경합의 기술 제안/남은 Product OPEN은 유지하며 코드/migration·의존성·실행 검사는 변경/수행하지 않았다. 앞선 PROPOSED/미결정 기록은 당시 이력이고 이번 승인 범위에 한해 대체한다. 구현 착수는 별도 지시가 필요하며 S1/S2 범위·개발 Bootstrap/실제 기록 정책·중요 관리 재인증/반복 시도 제한은 이번 일괄 답변으로 채택되지 않았다.

2026-10-12 사용자 확정(비활성화 전 누락 수업 대행 등록의 Branch Admin 기준 질문 1번): Master Admin은 자신의 Organization 전체, Branch Admin은 처리 시점 현재 관리 Branch가 실제 수업의 Performed Branch인 경우에만 대행 등록할 수 있다. Trainer 현재 Home Branch가 다른 지점이어도 실제 수업이 자신의 관리 지점에서 진행됐다면 허용한다. Trainer Home Branch·Member Home Branch·Pass Issued Branch 또는 과거 관리자 Scope만으로 대행 권한을 얻지 않는다(BR-OPS-015). 현재 Scope 검증/과거 사실·계약·저장/동시성은 후속이며 Product OPEN 23 OPEN / 7 CLOSED·ADR-0004/Architecture PROPOSED·IAM-001 S1 범위는 유지한다. 코드/migration 변경·업무 검증은 수행하지 않았다.

2026-10-12 사용자 검토 방식 변경: 이후 질문은 관련 미결정 업무 정책을 묶은 목록으로 제시해 한 번에 답할 수 있게 한다. 기존 선택으로 처리할 수 있는 반복 항목은 제외하고, 추천안/대안은 사용자 답변 전 승인된 정책으로 기록하지 않는다.

2026-10-12 사용자 진행 방식 추가: 승인 내용을 문서에 반영하고 검증한 뒤 다음 미결정 항목 검토까지 계속한다. 단순 반영 완료만으로 멈추지 않고 새로운 운영 판단이나 기존 결정 충돌 등 사용자 확인이 필요한 지점에서 질문 묶음을 제시한다. 이미 허용된 문서 정합성 수정·기술 검토는 계속하되 코드/migration 구현이나 미승인 업무 정책 채택으로 작업 범위를 확대하지 않는다.

2026-10-12 공통 PT 상품 생성/수정 권한 반영: Master Admin만 Organization 범위에서 허용하며 Master 권한 없는 Branch Admin·Operator·Trainer는 불가하다. Backend에서 현재 Master 권한/Organization Scope를 검증하고 기존 Pass의 발급 조건·잔여·과거 기록을 보존한다. MB-007은 CLOSED이며 최신 Product OPEN은 23 OPEN / 7 CLOSED다. 아래 이전 날짜의 수치는 당시 기록이다. 권한 계약/저장/UoW·동시성과 모듈 경계·ADR-0004는 계속 PROPOSED이며 이번 반영은 문서 변경이다.

2026-10-11 사용자 검토 진행 지시: 상황이 달라도 기존 사용자 선택과 승인된 Product 정책을 참고해 같은 원칙을 적용하며, 같은 기준을 따르는 항목을 반복해서 질문하지 않는다. 적용 근거와 범위를 기록하고 기존 결정 간 충돌·새 예외·기존 선택으로 해결할 수 없는 금액/권한/상태 전이 차이가 있을 때만 확인한다. 이 지시를 새 기능 범위나 PROPOSED 기술 설계/ADR의 일괄 승인으로 취급하지 않는다. 이번에는 지원 수업 외 실적의 등록 양수 기준을 확정 전 금액 수정에 동일 적용했다.

현재 단계: 최소 백엔드 기반 구성 및 WSL에서 실제 PostgreSQL 기반 검증 완료. [FOUNDATION-001](foundation-001.md)과 [ADR-0003](../decisions/0003-foundation-tooling.md)에 따라 backend/를 구성했으며, 현재 [실행 안내](../../backend/README.md)와 [WSL 이전 검증 기록](wsl-migration.md)을 따른다. 빠른 검사와 실제 PostgreSQL 검사 3개(트랜잭션·세션 정리, health, Alembic 온라인 `current`)가 통과했다. FOUNDATION-001/002의 Windows 당시 미검증·BLOCKED 기록은 이력으로 유지한다. 업무 schema migration·지급 계산 및 업무 동시성·운영 배포 준비 검증은 완료하지 않았고, PT 진행 등록 등 업무 기능도 구현하지 않았다. 6개 업무 모듈 상세는 PROPOSED다.

첫 업무 기능의 설계 초안은 [IAM-001 — 로그인한 관리자의 지점 접근 제어](iam-001-design.md)에 모았다. v1 인증 선택은 [ADR-0004](../decisions/0004-authentication-session.md) **ACCEPTED**다(2026-10-12 A1). 승인된 계정 정책은 [2026-10-12 일괄 승인](../product/product-decisions.md#review-20261012-batch)을 따르며 나머지 정책/구체 계약·인수 계획은 IAM-001에서 구분한다. 설계 작성은 구현 승인이나 인증·업무 migration 검증 완료를 뜻하지 않는다.

첫 구현 단위 재검토는 [IAM-001 최소 결정안](iam-001-decision-pack.md)을 따른다. K3으로 첫 개발 증분의 관리자 인증/지점 접근 제어 개발 검증 범위와 후속 분리를 선택했다. 실제 계정 준비·로그인·지점 Scope·logout/Branch Admin 차단·Scope 변경·감사 원자성까지의 영속 PostgreSQL 기능 흐름을 상세 검토하되 구체 API/상태·공유 UoW/잠금·인수 방식은 제안이다. 첫 인수의 가상 데이터·24시간·영역 폐기는 별도 하네스 실행 관리 후보이며 제품 수명/삭제 기본값으로 넣지 않는다. 복구·재설정/본인 암호·Login ID 변경·추가 Master의 구현은 S2 후보이며 S1 완료와 전체 IAM-001/운영 준비 완료를 구분한다. 다음 진입 조건은 D01~D12의 제품·운영 정책 승인과 기술 검토/위임 결과를 구분한 근거 및 별도 구현 지시다. 하네스 실행 관리만으로 불필요한 사용자 정책 승인을 요구하지 않으며 C7/C8 외 실제 기록/보안 상태·보존/운영 접근 게이트는 유지한다. ADR-0004 v1 인증 방식은 ACCEPTED이며 UoW/FK/잠금 상세는 계속 PROPOSED다. Product 결정의 후속 변경은 아래 2026-10-10 기록과 원본을 따른다. K3 기능 범위/순서 승인과 구체 구현 설계 제안·별도 코드 작성 지시를 구분하며 아래 기반 검사 수치는 이전 검증 기록이다.

2026-10-11 지원 수업 외 추가실적 확정 후 금액 오류의 동일 정정 흐름 반영: 지원 수업 외 실적의 확정 후 금액 오류도 해당 Trainer/월 해제 → 양수 금액 정정 → 같은 월 재확정·이전 확정본/구성/이력 보존(2026-10-11 사용자 일관성 지시 적용). Master Organization/Branch Admin 각 처리 시점 현재 Home Branch·본인 건 포함·별도 승인 없음·해제/정정 모두 사유 필수·감사·기존 재확정 조건/미입력 지원 수업 차단 유지. 발생 월/당시 Home Branch 비용 유지. 금액 외 정보 수정/취소·나머지 기간/금액 제약은 OPEN. 구체 계약/저장/UoW/동시성은 PROPOSED이며 업무 구현·검증 결과가 아니다.

2026-10-11 지원 수업 외 추가실적 수정 금액의 동일 양수 기준 반영: 지원 수업 외 추가실적은 최초 등록과 확정 전 금액 수정 모두 양수만 허용(Product 확정, 2026-10-11 사용자 일관성 지시 적용). 0원·음수·누락 수정 거부/요청 직전 금액·이력·정산 입력 상태 유지; 사유가 있어도 0원 수정 불가. 기존 관리자 Scope/본인 건/승인 생략/사유·이력/감사 유지. 지원 수업 보상 및 월별 수동 기본급의 승인된 사유 필수 0원 예외는 유지. 상한/정밀도·금액 외 정보 수정/취소는 OPEN. 구체 계약/저장/UoW/동시성은 PROPOSED이며 업무 구현·검증 결과가 아니다.

2026-10-11 확정 전 지원 수업 외 추가실적 금액 수정 반영: 월 정산 확정 전 비지원 추가실적 금액 수정은 Master Organization 전체/Branch Admin 각 수정 시점 Trainer 현재 Home Branch 기준으로 허용(Product 확정, 2026-10-11). 관리 범위 안 본인 건 포함·별도 승인 없음·변경 사유 필수·전후 금액/사유/수정자/시점 이력과 감사. 사유 누락 거부/요청 직전 금액 유지. 발생 월/당시 Home Branch 비용 유지. 수정 금액의 나머지 입력 제약, 금액 외 정보 수정/취소는 OPEN. 구체 계약/저장/UoW/동시성은 PROPOSED이며 업무 구현·검증 결과가 아니다.

2026-10-11 관리자 본인 누락 실적 반영: 관리 범위 안 관리자·Trainer 겸임자의 본인 누락 실적 후등록 해제/재확정도 별도 승인 없이 허용(Product 확정, 2026-10-11). Master Organization 범위/Branch Admin 각 처리 시점 본인 현재 Home Branch 일치·해제 사유 필수·본인 감사/이전 확정본 보존·기존 후등록 순서/월/비용 귀속·재확정 조건/미입력 지원 수업 차단 유지. Trainer 단독 권한 없음. 비지원 실적의 금액 외 정보 수정/취소 등은 OPEN. 구체 계약/저장/UoW/동시성은 PROPOSED이며 업무 구현·검증 결과가 아니다.

2026-10-11 비본인 누락 실적 반영의 별도 Master 승인 생략 반영: Branch Admin의 본인이 아닌 소속 Trainer 누락 실적 후등록 해제/재확정은 별도 Master 승인 없음(Product 확정, 2026-10-11). 각 처리 시점 현재 Home Branch 인가·해제 사유 필수·해제 후 등록/동일 월 재확정·이전 확정본/감사·기존 확정 조건/미입력 지원 수업 차단 유지. 관리 범위 안 관리자 본인 건의 해제/재확정 허용·별도 승인 없음도 확정(2026-10-11). 구체 계약/저장/UoW/동시성은 PROPOSED이며 업무 구현·검증 결과가 아니다.

2026-10-11 누락 실적 반영의 확정 해제 사유 반영: 확정 월의 누락된 지원 수업 외 실적 반영을 위한 해제 사유 필수(Product 확정, 2026-10-11). 사유 없는 해제 요청은 거부하고 요청 직전 확정 상태/확정본/기존 실적·정산 구성/금액 유지. 성공 시 대상 Trainer/월·사유·해제자·시점 이력/감사와 이전 확정본 보존. 현재 Home Branch 인가·기존 후등록 순서/월/비용 귀속 유지. 이 흐름의 해제/재확정은 관리 범위 안 본인 건도 별도 승인 없이 허용(2026-10-11). 구체 계약/저장/감사/UoW/동시성은 PROPOSED이며 업무 구현·검증 결과가 아니다.

2026-10-11 지원 수업 외 실적 등록·누락 후등록 인가 반영: 지원 수업 외 실적 등록 및 확정 월 누락분 반영의 해제·재확정은 Master Organization 전체/Branch Admin 각 처리 시점 Trainer 현재 Home Branch 기준으로 인가(Product 확정, 2026-10-11). 단계마다 재검증하며 이전 소속/발생 당시 소속만으로 권한 없음. 발생 월 정산·발생 당시 Home Branch 비용 귀속은 유지. 이 후등록의 해제/재확정 본인 건 허용·별도 승인 없음은 확정(2026-10-11). 기존 실적 정정/취소는 별도 OPEN. 공개 계약/저장/UoW/이동 경합 처리는 PROPOSED이며 구현·검증 결과가 아니다.

2026-10-11 확정 월 누락 추가실적 후등록 흐름 반영: 이미 확정된 발생 월의 누락된 지원 수업 외 Additional Performance는 해당 Trainer·월 정산의 확정 해제 → 누락 실적 등록 → 같은 발생 월 재확정으로 반영한다. 이전 확정본은 보존하고 재확정 결과와 구분한다. 확정 상태에 직접 추가하여 이전 확정본을 덮어쓰거나 등록 월/다른 월로 이월하지 않는다. 기존 등록 권한/금액/감사/비용 귀속과 재확정 조건을 유지한다. 이 흐름의 해제/재확정 본인 건 허용·별도 승인 없음도 확정(2026-10-11). 기존 실적 정정/취소는 BR-009/013 OPEN이다. 단계별 명령/조회 계약·저장/버전·UoW·실패/재시도·동시성은 PROPOSED, 업무 구현/검증 완료가 아니다.

2026-10-11 지원 수업 외 추가실적 정산 월 반영: 회원 유지 등 지원 수업 외 Additional Performance는 실제 실적이 발생한 월의 Trainer 월 정산에 귀속한다. 9월에 발생한 실적을 10월에 등록해도 9월분이며 등록 월이나 금액 입력 월로 이월하거나 관리자가 반영 월을 임의 선택하지 않는다. 같은 실적을 9월·10월에 중복 합산하지 않는다. 기존 금액 필수/양수·관리 Scope/본인 건·승인 생략·감사·발생 당시 Home Branch 비용 귀속은 유지한다. 확정된 발생 월 후등록/해제·재확정·발생 시점 식별/월 경계·소급 기간·나머지 정정/취소는 OPEN이며 확정본 자동 갱신 없음. 계약·저장/조회·UoW·버전/동시성은 PROPOSED, 업무 구현/검증 완료가 아니다.

2026-10-11 지원 수업 외 추가실적 양수 금액 요건 반영: 회원 유지 등 지원 수업 외 Additional Performance의 등록 금액은 0원보다 큰 양수만 허용한다. 0원과 음수 입력은 등록을 거부하며, 사유를 남겨도 0원으로 등록할 수 없다. 기존대로 내용과 금액을 함께 입력해야 등록이 완료되고 누락 금액을 자동으로 채우지 않는다. 기존 권한·본인 등록·승인 생략·감사·발생 당시 Home Branch 비용 귀속과 지원 수업의 사유 필수 0원 허용은 유지한다. 상한액·정밀도/금액 표현·정산 월·비지원 실적의 금액 외 정보 수정/취소의 이동 시 인가·정정/취소 등은 OPEN, 계약·저장/UoW·동시성은 PROPOSED다. 업무 구현/검증 완료가 아니다.

2026-10-11 지원 수업 외 추가실적 등록 완료 요건 반영: 회원 유지 등 지원 수업 외 Additional Performance는 권한 있는 관리자가 실적 내용과 금액을 함께 입력해야 등록이 완료된다. 금액 미입력 요청은 등록을 완료할 수 없으며, 금액 없는 실적을 먼저 등록하고 나중에 금액을 입력하는 흐름은 v1에 두지 않는다. 누락 금액을 자동으로 0원이나 계산식 결과로 대체하지 않는다. 기존 지원 수업 두 단계·관리 Scope/본인 등록·승인 생략·감사·발생 당시 Home Branch 비용 귀속은 유지한다. 0원 허용/입력 제약·정산 월·비지원 실적의 금액 외 정보 수정/취소의 이동 시 인가·정정/취소 등은 OPEN, 계약·저장/UoW·동시성은 PROPOSED다. 업무 구현/검증 완료가 아니다.

2026-10-11 추가실적 등록 흐름 반영: v1 추가실적은 권한 있는 관리자의 직접 등록만 지원하고 Trainer의 시스템 내 별도 신청·승인/반려 흐름은 두지 않는다. Trainer는 실적 내용을 관리자에게 전달하며 기존 Master Admin/Branch Admin이 허용된 관리 범위에서 입력한다. 기존 관리 Scope/본인 등록·승인 생략·감사와 Trainer PT 진행 기록/지원 수업 Pass 차감은 유지한다. v1에 별도 신청 상태·승인/반려 계약을 선행 도입하지 않는다. 남은 금액 확정 시점/입력 제약·비지원 실적의 금액 외 정보 수정/취소의 이동 시 인가·정산 월·정정/취소는 관련 OPEN, 구체 계약·저장/UoW·동시성은 PROPOSED다. 업무 구현/검증 완료가 아니다.

2026-10-11 지원 수업 외 추가실적 금액 산정 반영: 회원 유지 등 지원 수업 외 Additional Performance의 금액도 권한 있는 관리자가 실적 건별로 직접 입력한다. v1에서 유형별 사전 금액·산식으로 자동 계산하는 방식을 채택하지 않으며 일반 RATE/FIXED_AMOUNT 계산 결과로 입력액을 대체하지 않는다. 기존 권한·승인 생략·감사·발생 당시 Home Branch 비용 귀속을 유지한다. 금액 확정 시점/0원/미입력·입력 제약·정산 월·비지원 실적의 금액 외 정보 수정/취소의 이동 시 인가·정정/취소 등 남은 정책은 BR-013/010 및 MB-010 등 OPEN이다. 계약·저장/UoW·연계/버전·동시성은 PROPOSED이며 업무 구현/검증 완료가 아니다.

2026-10-11 지점별 비용 보고서 조회 권한 반영: v1 지점별 비용 보고서는 Master Admin만 Organization 범위에서 조회한다(2026-10-11 사용자 확정). Branch Admin은 자기 지점 비용 합계도 이 보고서로 조회할 수 없으며 Master 권한 없는 Operator·Trainer도 불가하다. Branch Admin의 현재 자기 Home Branch 소속 Trainer 해당 월 정산 전체 금액·구성 내역 조회는 타 지점 지원 보상까지 포함하여 유지한다. 비용 귀속·지급액·기존 등록/정정/확정 권한은 유지하며 보고서 항목·대상 월·집계/완전성·버전 등 남은 상세는 MB-006/010 OPEN이다. 현재 권한/Scope를 검증하는 조회 계약은 후속 설계하며 저장·집계·버전·동시성은 PROPOSED다. 업무 구현/검증 완료가 아니다.

2026-10-11 지원 수업 외 추가실적 비용 귀속 반영: 지원 수업 외 Additional Performance의 비용은 실적 발생 당시 대상 Trainer의 Home Branch에 귀속한다. 등록 시점·금액 확정 시점·대상 월말 또는 조회 시점의 소속으로 대체하지 않는다. 금액·월 합산 횟수·기존 관리 권한은 유지한다. 수업 보상의 실제 수행 지점·이동월 기본급의 월말 소속 귀속과 구분한다. 금액 산정·발생 시점/소속 사실 확인 예외·이동 시 등록/정정 인가 시점·정산 월·남은 정정/취소와 비용 보고 공개/집계 상세는 관련 OPEN, 계약/이력·저장/조회·갱신/버전·동시성은 PROPOSED다. 업무 구현/검증 완료가 아니다.

2026-10-11 일반 PT 수당 비용 귀속 반영: 일반 Session Payment는 해당 PT 진행 기록의 실제 Performed Branch 비용으로 집계한다. 이미 확정된 수업별 지급액을 지점별로 합산하며 대상 월말 Home Branch로 전액을 모으지 않는다. Trainer 월 합계·지급 계산/과거 불변성·지원 수업 일반 지급 중복 합산 금지·이동월 기본급 월말 소속 전액 귀속·기존 권한은 유지한다. 이후 소속 이동만으로 과거 수행 지점에 따른 비용 귀속을 바꾸지 않는다. 일반 지급 정정/취소·다른 추가실적 귀속·기본급 귀속의 남은 예외·비용 보고 공개/집계 상세는 관련 OPEN, 계약·저장/조회·갱신/버전·동시성은 PROPOSED다. 업무 구현/검증 완료가 아니다.

2026-10-11 이동월 기본급 비용 귀속 반영: 월중 Trainer 지점 이동이 있는 달의 해당 월 적용 기본급 비용은 대상 월의 월말 Home Branch 한 곳에 전액 귀속한다. 해당 월 수동 적용액 우선·기본급 한 번 합산·지급액/기존 권한 유지·이후 이동만으로 과거 귀속 변경 없음은 Product 확정이다. 월말 소속 식별 불가 등 예외·다른 보상 귀속·비용 보고 공개/집계 상세는 MB-001/010/006 등 관련 OPEN을 따르며 이력/계약·저장·갱신/버전·동시성 상세는 PROPOSED다. 업무 구현/검증 완료가 아니다.

2026-10-11 지원 수업 보상 비용 집계 반영: 타 지점 지원 수업의 전체 보상으로 확정한 Additional Performance 금액은 해당 수업의 실제 Performed Branch 비용으로 집계한다. Trainer 월 정산 한 번 합산·기존 입력/정정/확정/조회 권한은 유지한다. 소속 이동만으로 과거 지원 수업의 비용 지점을 바꾸지 않는다. 일반 지급·기본급·다른 추가실적 귀속, 비용 보고 공개/집계 상세는 MB-010/006 OPEN이며 계약·저장·정정 연동·갱신/버전·동시성 상세는 PROPOSED다. 지점 간 청구/송금·기본급 자동 배분까지 새로 도입한 결정이나 구현/검증 완료가 아니다.

2026-10-11 월 정산 조회 범위 반영: 현재 자기 Branch 소속 Trainer의 해당 월 정산 전체 금액·구성 내역은 타 지점 지원 수업 보상까지 공개한다(조회 시점 현재 Home Branch 기준, 2026-10-11 사용자 확정). Master Organization 전체 조회를 유지하고 수행 지점만으로 다른 Home Branch Trainer의 전체 정산을 공개하지 않는다. 조회 대상 월·이전 확정본/세부 계산 근거·감사 공개의 남은 상세와 지점 비용 귀속은 MB-006/010 OPEN이다. 조회 계약·저장·동시성 구현은 PROPOSED이며 구현/검증 완료가 아니다.

2026-10-11 최초 월 정산 확정 권한 반영: 월 정산의 최초 확정은 Master Admin에게 Organization 전체 Trainer, Branch Admin에게 확정 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 직접 확정한다. 지원 수업 미입력에 따른 해당 Trainer·월 확정 차단은 유지한다. 상세 공개·비용 귀속·나머지 확정/마감 조건은 BR-009 및 MB-006/010 OPEN이다. Product의 권한 승인과 업무 구현·검증 완료를 구분하며 관련 계약/UoW/동시성 상세는 계속 PROPOSED다.

2026-10-10 사용자 결정 반영: 관리자·Trainer 겸임은 한 계정으로 지원하며 최종 정정에 따라 보유한 관리 범위 안이면 본인 보상 설정도 조회·변경 가능하다(Master는 본인 포함 전체, Branch Admin은 본인 Home Branch가 관리 지점과 일치할 때). 최초 비밀번호는 Master가 전달한 일회용 설정 링크로 대상자가 직접 설정한다. ARCH-001/002의 나머지 질문은 OPEN이다. MB-009는 사용자 정정에 따라 타 지점 수업 보상 전체를 Additional Performance로 처리하도록 CLOSED 반영했다. 동일 수업의 일반 Session Payment를 정산에 별도로 합산하지 않는다. BR-011은 기존 Pass 발급 당시 상품 가격·총횟수·Payment Type 유지, 상품 변경은 새 Pass부터 적용으로 CLOSED 처리했다. Trainer 설정의 등록 시점 적용은 유지한다. [Product OPEN](../product/open-questions.md)은 현재 24 OPEN / 6 CLOSED다. BR-013의 지원 수업 외 인정·금액·신청 승인, 지원 수업 미입력 건의 추적 표현·정정 연동·연계 상세, 기본급 적용 시작 월의 관리자 지정·미확정 과거 월 지정 허용·수동 지정 없는 기존 미확정 정산의 기본급/합계 자동 반영·확정 월 기본급 오류의 해제/정정/동일 월 재확정과 이전 확정본 보존·해당 정정의 Master Organization/Branch Admin 처리 시점 Trainer 현재 Home Branch 기준 권한과 별도 Master 승인 없음·확정 해제/해당 월 기본급 수정 사유 필수·오류 정정의 해당 월 한정 및 현재/미래 설정·다른 월 유지·입퇴사/휴직 월의 관리자 수동 금액 지정·이후 일반 설정 변경에도 수동 지정액 유지·미확정 월 최초 수동 지정/수정 모두 사유 필수·현재 Home Branch 관리자 범위의 직접 수동 지정/수정(본인 포함·별도 Master 승인 없음)까지 확정이며 BR-012의 미리 등록할 수 있는 미래 적용 시작 월의 범위·월별 수동 지정 금액의 입력 제약 등 남은 정책, MB-010/006의 귀속·공개는 OPEN을 유지한다. 이 반영은 문서 변경이며 구현·migration이나 미승인 설계의 승격을 포함하지 않는다.

2026-10-11 기본급 지속 적용 명확화: 일반 Base Salary 설정은 관리자가 지정한 적용 시작 월부터 다음 기본급 변경의 적용 시작 월 전까지 매월 계속 적용한다. 적용 종료 월을 지정하거나 같은 금액을 매월 다시 등록할 필요는 없다. 특정 월 수동 지정은 해당 월에만 적용하는 예외다. 미래 변경을 얼마나 미리 등록할 수 있는 시작 월로 허용할지는 이 명확화와 별도이며 BR-012 OPEN을 유지한다.

2026-10-11 추가 사용자 결정: 해당 월 기본급은 권한 있는 관리자가 사유를 남기면 0원으로 명시적으로 수동 지정할 수 있다. 수동 지정한 0원은 미입력과 구분하며, 미입력이나 누락된 일반 설정을 자동으로 0원으로 대체하지 않는다. 해당 월 기본급에만 적용하고 다른 유효 지급·추가실적은 기존 규칙대로 합산한다. 기존 관리자 Scope·사유/이력/감사·수동 지정액 유지·정산 확정 조건을 따른다. BR-010/012는 미래 적용 월 및 나머지 입력 제약으로 OPEN을 유지한다. 구체 저장 계약과 검증은 후속 설계/구현 대상이다.

같은 날 추가실적 직접 등록은 Master Admin이 Organization 전체 Trainer, Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer에게만 허용하는 것으로 부분 확정했다. 지원받은 지점 관리자는 다른 Home Branch Trainer에게 등록할 수 없다. Branch Admin이 본인이 아닌 자기 지점 소속 Trainer에게 직접 등록할 때는 별도 Master 승인 없음으로 확정했다. 생성·변경 감사는 유지한다. 관리자·Trainer 겸임자도 관리 범위 안이면 본인의 추가실적을 직접 등록할 수 있다. Master는 Organization 범위 안의 본인, Branch Admin은 본인 Trainer Home Branch가 관리 Branch와 같을 때 허용하며 다르면 거부한다. 본인 건도 별도 승인 없이 처리하며 동일한 감사 대상이다. 관리 범위 검증과 Actor/대상 동일인 추적은 유지한다. Trainer 신청과 그 승인·Operator 권한, 지원 수업 외 실적의 금액 외 정보 수정/취소의 소속 이동 시 권한 기준 시점·지원 수업 외 추가실적 금액·금액 미입력 건의 추적 표현·정정 연동·연계 상세·수명 정책은 BR-013 OPEN이다. 타 지점 지원 수업 금액은 권한 있는 관리자가 수업 건별로 직접 입력하는 방식으로 추가 확정했다. 일반 RATE/FIXED_AMOUNT 계산 결과나 지원 전용 고정금액을 자동 지급액으로 사용하지 않는다. 타 지점 지원 수업은 보상 금액 없이도 허용된 PT 진행 기록과 Pass 차감을 먼저 완료한다. 권한 있는 관리자가 나중에 수업 건별 금액을 저장할 때 해당 Additional Performance 보상을 확정한다. 금액 미입력은 확정된 0원과 구분하고 누락 건을 추적할 수 있어야 한다. 해당 Trainer의 해당 월 정산 대상 지원 수업에 금액 미입력 건이 하나라도 있으면 그 Trainer·월 정산을 확정할 수 없다. 타 지점 지원 수업 보상은 권한 있는 관리자가 사유를 기록하면 0원으로 명시적으로 확정할 수 있다. 사유 없는 0원 입력은 보상 확정이 불가하다. 사유를 남기고 확정한 0원은 금액 미입력이 아니므로 그 건으로 월 정산 확정을 차단하지 않는다. 다른 미입력 건이 남으면 기존 차단 조건을 유지한다. 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin에게 Organization 전체, Branch Admin에게 대상 Trainer Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안의 본인 건도 허용하고 변경 이력을 남긴다. 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin·Branch Admin 모두 관리 범위 안에서 본인 건을 포함해 별도 승인 없이 저장 성공 즉시 반영한다. Master나 다른 관리자의 승인 대기를 두지 않으며 권한 검증과 변경 이력을 유지한다. 월 정산 확정 전 지원 수업 보상 금액의 모든 수정에는 변경 사유가 필수다. 양수 간 변경·0원에서 양수로 변경·양수에서 0원으로 변경 모두 적용하며, 사유 없이는 금액을 수정할 수 없다. 변경 전후 금액·변경 사유·수정자·수정 시점을 이력으로 남긴다. 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer의 지원 수업 보상 정정을 위해 월 정산을 확정 해제·재확정할 때는 Master의 별도 승인을 두지 않는다. Master 승인 대기 단계 없이 관리 범위 안에서 직접 처리하며 이전 확정본과 해제·재확정 이력 및 감사를 유지한다. 지원 수업 보상 정정의 월 정산 확정 해제에는 사유가 필수이며, 사유 없이 해제할 수 없다. 사유·해제자·시점을 이력으로 남긴다. 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 남은 정정·취소 절차는 BR-009/013 등 관련 OPEN을 따른다. 2026-10-10 시점 질문의 1번 답변에 따른 업무 단계 분리이며 구체 저장 모델·트랜잭션 구성은 후속 제안이다. 이 승인 생략을 Trainer 신청 승인이나 월 정산 확정으로 확대하지 않는다. 등록 주체와 비용 귀속·정산 공개(MB-010/006)는 별개다. Product 질문 수와 ADR 상태는 유지한다.

[IAM-001 기술 사전검증](iam-001-preflight.md)은 별도 임시 환경의 해시 라이브러리·차단목록 공급·HTTPS 브라우저 원시 동작 결과다. 제품 코드·DB·정책 승인을 포함하지 않으며 실제 IAM 통합/운영 검증과 구별한다.

아래는 **Architecture 1차 설계 당시의 결정·검증 기록**이다. 당시의 구현 금지/도구 미선정/검사 미구성 설명은 그 작업 시점에 한정하며 현재 기반 상태는 위 문서와 ADR-0003이 갱신한다.

작성일: 2026-09-17
상태: **기술/시스템 형태 ADR은 ACCEPTED, 구체 설계는 PROPOSED**.
이 단계는 문서 설계이며 scaffold·애플리케이션·DB schema·API·테스트 코드·migration 환경을 만들지 않는다. 다음 작업을 자동 시작하지 않는다.

## 입력과 문서 상태

현재 승인/검증 상태는 위 현재 단계와 아래 승인 표, 각 ADR 및 Foundation/WSL 기록을 따른다. 아래 두 문단은 2026-09-17 Architecture 최초 작성 당시의 탐색·변경 범위 기록이며 현재 AGENTS.md/ADR/검사 환경의 부재나 이후 Product 문서 수정 금지를 뜻하지 않는다.

[Product Baseline](../product/README.md)의 13개 문서 전체를 읽고 현재 규칙과 이전 결정 이력을 구분했다. [Architecture Handoff](../product/architecture-handoff.md)와 [OPEN](../product/open-questions.md)을 입력으로 사용했다. Product/analysis는 수정하지 않는다. 기존 AGENTS.md 및 Architecture/ADR 문서는 작업 시작 시 발견되지 않아 아래 문서를 새로 구성했다. 기존 docs/ 미커밋·미추적 자료를 보존한다.

이 저장소 파일 목록에 C# 소스는 없으며 C# 구현을 확인했다고 주장하지 않는다. 이번 설계는 승인된 Product로 충분하여 docs/analysis/ 본문을 추가 조사하지 않았다. [Validation Needed](../product/validation-needed.md)의 AS-IS 미검증 상태도 유지한다.

## 승인된 방향과 제안의 경계

| 상태 | 범위 |
| --- | --- |
| ACCEPTED — ADR-0001 | Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL. 타입·의존성·업무/권한/동시성 검사 포함 방향 |
| ACCEPTED — ADR-0002 | 초기 단일 백엔드 배포, Modular Monolith, 모듈 데이터 소유권/계약·업무 트랜잭션 관리, 선택적 서비스 추출 |
| ACCEPTED — ADR-0003 | 기반 도구/잠금 의존성, 동기 SQLAlchemy·psycopg 3, uv·Ruff·mypy·pytest·Import Linter. WSL 기반/실제 PostgreSQL 검증은 별도 기록 참조 |
| ACCEPTED — ADR-0004 | v1 PostgreSQL AuthSession+opaque Cookie 방식. 후속 JWT 재검토 가능; 구체 라이브러리·CSRF/Caller/UoW/잠금·배포까지의 승인이 아님 |
| PROPOSED — 이 Architecture | IAM/Organization/Membership/Workforce/PT Operations/Settlement 6개, Audit 기반, 의존성 DAG, 내부 계약, Application UoW, 추출 후보·검증 상세 |
| OPEN / 후속 기술 검토 | 구체 업무 모듈/계약·인가/UoW/잠금·인증 보안/라이브러리·운영/배포·프론트엔드 상세. 브로커/캐시는 필요 시 검토하며 기반 도구/드라이버·v1 인증 방식은 다시 미결정으로 취급하지 않음 |

ADR의 ACCEPTED는 구체 모듈/트랜잭션 설계를 승인한 것이 아니다. 공식 문서 기능 확인일과 한계는 각 ADR에 기록했다. Product 문서의 초기 “기술 선택 없음”과 아래 날짜별 PROPOSED/검증 미완료 서술은 당시 기록이며, 현재 정책은 각 ADR의 실제 Status와 Product 승인 근거를 따른다. 이 상태 정리는 새로운 제품 규칙이나 기술 채택이 아니다.

## 읽기 순서

1. [루트 AGENTS.md](../../AGENTS.md)와 [Product Handoff](../product/architecture-handoff.md)
2. [ADR-0001 Backend Stack](../decisions/0001-backend-stack.md), [ADR-0002 Modular Monolith](../decisions/0002-modular-monolith.md), [ADR-0003 Foundation Tooling](../decisions/0003-foundation-tooling.md), [ADR-0004 v1 Authentication](../decisions/0004-authentication-session.md)
3. [모듈 경계·소유권·서비스 추출](module-boundaries.md)
4. [데이터 접근·트랜잭션·권한](data-and-transactions.md)
5. [Product/기술 결정 게이트](decision-gates.md)
6. [후속 검증 계획](validation-plan.md)

별도 ADR 형식이 없으므로 순번 파일에 Status/Context/Decision/대안/이유/비용/제약/재검토/근거를 기록한다. 후속 ADR은 기존 번호와 충돌하지 않게 추가하고 기존 결정 변경 시 대체 관계를 명시한다.

## 핵심 제안

PT Operations가 Product·Pass·Session·확정 Payment를 함께 소유한다. 정책이 확정된 일반 Session 등록의 차감·기록·지급 결과·필수 감사를 Application Use Case의 한 PostgreSQL 트랜잭션에서 완료하거나 취소하는 안이다. Repository별 commit은 기본 구조로 사용하지 않는다.

Workforce의 보상 설정 소비, IAM의 현재 권한, Member/Trainer 소속 사실도 이 업무의 일관성에 참여한다. 공개 인터페이스를 둬도 이 결합이 사라지지 않으며 서비스 추출 전에 적용 순서·권한·실패 복구를 다시 설계해야 한다. Audit은 공통 기반으로 제안하고 독립 서비스로 만들지 않는다. 직접 cross-module DB 조회 예외는 승인 0건이다.

설정 조회/변경은 Master Organization 전체 및 Branch Admin의 관리 Branch가 현재 Home Branch인 Trainer에게만 허용한다. 관리 범위 안 관리자·Trainer 겸임자는 본인도 허용하며 관리자 권한 없는 Operator/Trainer는 본인 포함 불가다. 별도 Master 승인 없이 변경하며 감사한다. Performed Branch를 설정 권한 근거로 쓰지 않는다. 계산용 내부 소비와 사용자 조회 권한은 구별한다.

## 주요 Product 결정 게이트

현재 Product OPEN은 22 OPEN / 8 CLOSED이며 PD-021은 OPEN이다. MB-009 타 지점 지원 보상 전체 추가실적/일반 지급 중복 금지와 MB-007 공통 상품 Master 전용 생성·수정은 CLOSED다. BR-013은 관리자 수동 보상/등록·금액 정정 및 H2/H3 비지원 실적 내용 수정/취소·대상/발생 날짜 취소 후 재등록의 승인 범위를 유지하고 나머지 입력·발생/소속 사실·정정 연결/계약 상세가 남는다. BR-012는 적용 시작 월부터 다음 변경까지 지속/월별 수동 지정·확정 월 해제/정정/재확정 등 승인 범위를 유지하고 미래 시작 월 입력 범위·나머지 금액 제약이 남는다. MB-010/MB-006의 비용 귀속·Master 전용 지점 비용 보고서·현재 소속 Trainer 정산 공개는 승인 범위가 있고 남은 역사 사실 예외/보고서 상세만 게이트다. MB-008은 G1–G5 승인 이후 지점 재활성화 상세·역사 사실/다른 상태 조합이 남는다. 해당 기능의 실제 잔여는 [Product OPEN](../product/open-questions.md)과 [게이트 표](decision-gates.md)에서 확인한다.

Product 요약 참조 범위, Operator 정산 화면을 통한 설정 노출, FIFO 동률/설정 경합 순서점의 해석 경계는 같은 문서에 후속 확인으로 남겼다. I3으로 UX-001은 v1 일괄 입력 보류 승인/CLOSED다. I1은 시각 미상 예외 불가, I2는 회원 이름/전화번호/Home Branch 필수·생년월일/성별 제외, I4는 추가 연간 통계 v1 제외이며 기존 월 정산/지점 비용 보고서는 유지한다. Responsive Web은 v1, Member 로그인·일정/예약/취소·Mobile App은 Future를 유지한다. 독립 고객사 SaaS는 추가하지 않는다.

## 다음 결정과 진입 조건

공통 모듈 책임·계약·인가·원자성 검토는 계속 가능하다. 모든 OPEN이 끝나야만 모든 설계를 시작한다는 의미는 아니다.

- 상세 설계 전: 대상 기능을 정하고 T-01 모듈/소유권 제안을 검토한다. 해당 기능의 Product 게이트가 해소됐는지 근거를 확인한다. 미결정 기능의 금액/권한/상태 상세는 보류한다.
- 기반 도구/개발환경: T-02의 현재 잠금 조합·T-03 동기 DB/드라이버·T-04 검사 도구는 ADR-0003 및 WSL 기반에서 이미 선택/검증됐다. 재선정이나 자동 upgrade 없이 현재 backend 안내를 따른다. 다음 인증·UI·배포 작업은 T-05의 남은 구체 보안/계약과 T-06/07 중 해당 범위만 검토한다. 브로커·캐시 T-08은 필요가 생길 때 검토한다.
- 업무 구현 전: 선택한 흐름의 계약·인가·금액·트랜잭션/동시성·보존 설계(T-09)를 검토하고 필요한 테스트 환경/기준을 구성한다. 실제 PostgreSQL 동시성 검증을 단위 테스트로 대체하지 않는다.
- 서비스 추출 전: 별도 필요성/비용 근거와 추출 ADR, 공유 트랜잭션 해소, 계약 호환·이전/대사·실패/되돌림 검증을 마련한다.

AGENTS.md는 다음 구현을 영구 금지하지 않는다. 현재 backend에는 실행 가능한 Ruff/mypy/pytest/Import Linter·Alembic 기반이 있으며 WSL 절차는 [backend/README.md](../../backend/README.md)를 따른다. 빠른 검사 36개 및 실제 PostgreSQL 검사 3개 통과는 [WSL 이전 당시 기록](wsl-migration.md)이며 이번 설계 검토에서 다시 실행한 결과는 아니다. 업무 schema·인가/금액/정산/동시성 검사는 아직 구현되지 않았고 실제 운영 검증도 남는다. 코드/migration 구현은 별도 사용자 지시가 필요하다.

2026-10-12 Product 부분 승인 — 새 Operator 계정 발급/최초 단일 업무 Branch 지정은 Master Organization 전체 또는 Branch Admin 자기 단일 관리 Branch에 허용한다(BR-OPS-011·PD-019·PR-021). 기존 최초 비밀번호 설정 링크/계정 권한 감사 원칙을 재사용하되 기존 계정의 역할/지점 변경·다른 역할 발급/수명 업무 위임은 OPEN이다. 이 승인은 후속 v1 Operator 흐름의 Product 권한 경계이며 보존된 IAM-001 설계/decision-pack의 S1 `POST /admin/accounts`(Master의 Branch Admin 발급)를 Operator/Branch Admin 발급 API로 자동 확장하지 않는다. Operator 흐름의 실제 계약·저장/UoW·보안 검증과 인증 방식/운영 세부 정책은 관련 게이트 후속, ADR-0004 및 모듈/계약은 PROPOSED다. V-61은 예정 검증이며 실행 결과가 아니다.

2026-10-12 Product 부분 승인 — 기존 Operator 업무 Branch 변경은 Master Admin의 Organization 범위 전용이다(BR-OPS-011·PD-019·PR-021). Branch Admin의 자기 지점 신규 발급과 구별하며 기존 저장 후 현재 Scope 반영/실패 보존·감사 원칙을 적용한다. 독립 역할/Trainer Home Branch·과거 업무는 유지하고 대상 상태/절차·기존 계정의 다른 역할/Scope 변경·수명 권한은 OPEN이다. Caller/저장·UoW·캐시/진행 중 요청·동시성 및 AuthSession 철회 방식은 후속이며 IAM-001 S1/ADR-0004 PROPOSED는 유지한다. V-62는 예정 검증이다.

2026-10-12 Product 부분 승인 — 신규 Trainer 로그인 계정 발급은 Master Organization 전체/Branch Admin 대상 Trainer 현재 Home Branch에 허용한다(BR-OPS-012·PD-019·PR-021/029). 기존 최초 비밀번호 설정 링크·계정 권한 감사/실패 일관성을 재사용한다. 보존된 IAM-001 초안의 후속 v1 Master Trainer 발급 서술은 이 최신 Product 승인에 맞춰 Actor 범위를 상세화할 대상이며 S1 `POST /admin/accounts`에서 Master가 Branch Admin 계정을 발급하는 계약을 변경한 것은 아니다. 실제 Trainer 연결은 IAM/Workforce 최소 사실 공개 계약으로 설계하고 기존 계정 역할/연결 변경·Trainer 소속 이동/수명 위임과 발급 상세/저장/UoW·동시성은 게이트를 유지한다. ADR-0004/모듈은 PROPOSED, V-63은 미구성·미실행 예정 검증이다.

2026-10-12 Product 부분 승인 — Trainer Home Branch 변경은 Master Organization 범위 전용이다(BR-OPS-013·PD-004·PR-005). 일반 이동에 기존 저장 후 현재 소속 인가/실패 보존·이력/감사 원칙을 적용하며 독립 IAM 관리자/Operator Scope·Trainer 연결·담당/지원 관계와 수업 당시 소속/기존 지급·정산/설정값은 보존한다. 대상 상태·과거 소속 이력 정정/소급/확인 불가 및 Workforce/IAM/Organization/Audit 계약·저장/UoW·캐시/처리 중 요청/동시성·AuthSession 철회 방식은 후속이다. Trainer 비활성화/계정 수명 정책은 미정이고 S1/ADR-0004 및 모듈 PROPOSED를 유지한다. V-64는 예정 검증이다.

2026-10-12 Product 부분 승인 — Trainer 비활성화는 겸임 계정의 Trainer 권한만 중단하고 독립 관리자 역할/Scope를 유지한다(BR-OPS-014). 계정 전체 차단과 같은 상태 전이/전체 인증 철회를 자동 결합하지 않는다. 후속 인가의 실제 Trainer 상태 확인·실패/이력 보존/감사 원칙을 적용한다. 보존된 IAM-001 초안의 계정 전체 차단/Scope 변경 제안은 이 Trainer 역할 중단의 기술/정책 승인으로 사용할 수 없다. 처리 Actor/재활성화·Trainer 단독 로그인·비활성 상태 예외/관계 처리와 역할/상태·공개 계약·AuthSession 갱신/철회·UoW/동시성은 후속이다. ADR-0004/모듈 설계는 PROPOSED, IAM-001 S1의 Master→Branch Admin 발급/전체 계정 차단 흐름 범위는 그대로이며 Trainer 구현을 선행 추가하지 않는다. V-65는 예정이며 실제 업무 검증은 미완료다.

2026-10-12 Product 추가 승인 — Trainer 비활성화 Actor는 Master Organization 전체/Branch Admin 처리 시점 대상 Trainer 현재 Home Branch 범위다(BR-OPS-014). 소속 이동/권한 축소 이후에도 이전 소속·과거 발급자/지원 지점 사실로 허용하지 않는다. 전체 계정 차단/재활성화 권한과 분리하고 겸임자의 독립 관리자 역할/Scope를 유지한다. 기존 범위 내 직접 처리·현재 사실 반영/실패 보존·감사 원칙 적용이며 재활성화/Trainer 단독 로그인·관계/대상 상태·실제 Caller/계약/저장/UoW·AuthSession/경합은 후속이다. 보존된 IAM-001 초안을 전체 승인하거나 S1에 Trainer 기능을 추가한 것이 아니며 ADR-0004/모듈 설계는 PROPOSED, V-66은 미구성·미실행 계획이다.

2026-10-12 Product 추가 승인 — 잔여가 남은 담당 Pass가 있어도 Trainer 비활성화 가능하며 Assigned Trainer 정보는 유지한다(BR-OPS-008/014). 사전 일괄 교체/자동 담당 해제·교체를 요구하지 않는다. 유지된 담당 관계는 실제 Trainer 활성 상태 검증을 면제하지 않으며 후속 수동 교체는 기존 Member 현재 Home Branch 인가를 따른다. 비활성화 흐름에서 Pass 쓰기/횟수 재처리를 추가하지 않는 경계와 현재 인가/변경 이력·감사 일관성을 검토한다. 개별 지원 관계/재활성화·새 담당 활성 조건/비활성 상태 예외 및 계약/저장/UoW·동시성은 후속이며 보존된 IAM 초안·S1 범위를 전체 승인/확대하지 않는다. ADR-0004/Architecture는 PROPOSED, V-67은 미구성·미실행 계획이다.

2026-10-12 Product 추가 승인 — 새 담당 지정은 실제 활성 Trainer만 허용한다(BR-OPS-008/014). 허용된 최초 지정/교체의 대상 필요조건이며 기존 Actor/같은 Organization 타 지점 허용과 이후 비활성화된 기존 담당 유지/접근 차단은 유지한다. 클라이언트 선택 결과/로그인 유무로 상태 확인을 대체하지 않고 지정/비활성화의 확정 순서·현재 사실 검증·실패 보존을 증명해야 한다. 최초 담당 필수/미지정·다른 계정/Branch/Pass 상태 조합·비활성 전 수업 예외/재활성화·최소 공개 계약/저장/UoW·경합은 후속이며 IAM-001 S1 범위와 ADR-0004/모듈 PROPOSED는 유지한다. V-68은 미구성·미실행 계획이다.

2026-10-12 Product 추가 승인 — 비활성화 전 실제 수행한 누락 PT 수업은 관리자가 대행 등록할 수 있다(BR-OPS-015). Trainer 비활성/계정·현재 담당을 유지하고 실제 수행자/수업일과 입력 관리자/기록 생성 시점을 구분한다. 새 담당 활성 필요조건을 과거 수행자 참조에 잘못 적용하지 않으며 기존 Pass/생성 시점 수행 Trainer 보상/진행 월 정산 조건을 유지한다. 대행 관리자 상세 Role/Branch Scope(Branch Admin 기준 지점)·역사 사실/시점·최소 선택/사유·증빙 및 공개 계약/저장/UoW·경합은 결정/검증 게이트다. 임의 Scope로 구현하지 않는다. 비활성 Trainer 접근 복구·보상 설정/추가실적/정산 권한 확대가 아니며 IAM-001 S1 범위와 ADR-0004/모듈 PROPOSED는 유지한다. V-69는 미구성·미실행 계획이다.

2026-10-12 K3 진입 경계: 첫 기능은 관리자 인증/지점 접근 제어의 개발 검증으로 선택됐으므로 S1과 후속 복구/추가 Master/Trainer 연결의 순서를 다시 질문하지 않는다. 기존 승인 정책을 입력으로 IAM/Organization/Audit의 구체 계약/현재 인가·준비·보안·UoW/잠금·실제 PostgreSQL/브라우저 인수 계획을 설계자가 구체화한다. 정책/권한/관측 결과 변경이나 해당 운영 기능을 앞당길 때만 필요한 결정을 확인한다. 실제 코드 작성은 별도 지시가 필요하고 운영 전 MFA/복구 검증은 유지한다. [2026-10-12 K 일괄 승인](../product/product-decisions.md#review-20261012-k-batch).

2026-10-13 S1 기술계약 구체화: [TX01–TX06](iam-001-decision-pack.md#review-20261013-s1-contracts)에 소유권/공개 계약·공유UoW·row/security_version 분리·경로별 잠금/target 인증 철회·setup_link/CSRF/비노출·import/검증을 묶었다. [개발 전달안](iam-001-decision-pack.md#s1-implementation-handoff-20261013)은 미전달/구현 미착수다. 원래 설계 검토 범위와 별도 구현 착수 승인을 유지하며 보안 공급/관련 사전검증 미해결을 우회하지 않는다. 실제 앱/DB/브라우저 검사는 실행하지 않았다. 구체 계약은 PROPOSED이며 T-01/T-05/T-09·운영 게이트를 자동 닫지 않는다.

## 이번 작업 검증

아래 목록은 2026-09-17 최초 Architecture 문서 작성의 검증 이력이다. 당시 파일 수/OPEN 수·미설치/미실행 범위를 현재 상태로 읽지 않는다. 이후 Foundation/WSL 실행 결과와 현재 승인 범위는 위 현재 단계·ADR 및 각 날짜의 검증 기록을 따른다.

2026-09-17에 다음 문서 검증을 수행했다.

- 링크 검사: 신규 8개 문서의 로컬 링크 81개에 대해 대상 파일 및 지정 앵커 존재를 확인했다. 깨진 참조는 없었다. Product ID 참조의 존재와 실제 26개 OPEN의 게이트 표 포함도 확인했다.
- 설계 정합성 검토: 단일 쓰기 소유권, 의존성 방향, 일반 Session의 차감/기록/지급/감사 원자성, 보상 설정 권한, 과거 확정 결과 보존, 타 지점 보상 등 OPEN의 보류 경계를 원문과 대조했다. 모듈 구성·UoW·추출안은 PROPOSED로 유지했다. 이는 구현 검증이 아니다.
- 변경 범위: 작업 시작 시 기존 28개 파일의 SHA-256과 대조하여 변경/삭제가 없음을 확인했다. 추가 파일은 AGENTS.md, Architecture 5개, ADR 2개뿐이다. 기존 docs/는 미추적 상태이므로 일반 git diff만으로 범위를 판단하지 않고 파일 목록과 해시도 대조했다.
- 공식 문서 확인과 확인일은 각 ADR에 기록했다. 라이브러리 설치·호환성 시험, 애플리케이션 테스트, PostgreSQL 동시성/제약 시험, migration, 자동 타입/의존성 검사, 운영 검증은 수행하지 않았다. [V-01–20](validation-plan.md)은 실행 결과가 아닌 후속 검증 계획이다.


2026-10-13 검토 진행 방식: 사용자가 작은 질문 묶음의 반복/소요 시간을 지적했다. 남은 실제 운영 판단을 한 목록으로 모아 확인하고, 이미 승인된 정책/유사 원칙과 설계자가 정할 기술 세부는 반복 질문하지 않는다. 단순 승인 반영은 핵심 근거/수용 기준/게이트·검증 계획에 간결하게 연결하며 기존 변경/승인 이력을 보존한다. 이 지시는 미승인 금액/권한/상태 정책이나 코드 구현의 포괄 승인은 아니다.
