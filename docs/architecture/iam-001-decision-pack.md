# IAM-001 첫 증분 계약과 최소 결정안

2026-10-16 O03 부분 승인: [MFA M1/M2](../product/product-decisions.md#review-20261016-mfa-m-batch)로 관리자 복수 Passkey 등록/로그인 시 하나 사용과, 같은 Organization의 다른 정상 Master에 의한 관리자 본인 확인·기존 Passkey/모든 로그인 폐기·일회용 링크 재등록을 확정했다. Branch Admin 위임/타 조직·암호 reset/차단 해제·역할 복원은 포함하지 않으며 AB4/AB5를 유지한다. 추가 등록/삭제·마지막 인증수단 보호·등록/복구의 API·상태·링크 수명/소비·원자성/경합·운영 확인·실제 검증은 후속이며 아래 O03의 등록/분실/복구 미결정 중 승인된 M1/M2만 대체한다.

2026-10-13 최신 인수: **§4/§9/§10의 IAM S1a/S1b 개발 인수 PASS**. [S1 결과](iam-001-s1-results.md) 및 [설계자 판정](iam-001-s1-review.json)에 구현·독립 실행·보완 검토 근거를 기록한다. 아래 별도 구현 지시/사전검증/인수 대기 기록은 이전 단계의 이력이다. 첫 증분의 인수로 Product OPEN, 전체 모듈의 PROPOSED, S2 및 운영 게이트를 닫지 않는다.

2026-10-13 최신 지시: 사용자가 **사전검증 통과 후 첫 IAM 구현**, 별도 `테스트노예` 세션의 검사와 설계자의 결과 검토·문제 재지시를 승인했다. §4/§9/§10의 좁은 S1 범위와 TX01–TX06은 이번 증분의 구현 작업 기준이다. 전체 모듈 경계/후속 기능의 일괄 ACCEPTED, Product OPEN 변경, 운영 개시는 승인하지 않았다. 아래 이전 구현 승인 대기/미전달 문구는 이 지시 전 이력이다. PREP-IAM-001의 미해결은 먼저 증거로 해소해야 하며, 담당자 보고와 독립 검토 전 통과·완료로 표시하지 않는다.

최신 범위/정책: [2026-10-13 AB 승인](../product/product-decisions.md#review-20261013-ab-batch)으로 후속 reset30분·운영 관리자 비밀번호+사용자검증 Passkey·업무책임자 승인/별도 운영담당자 비상 복구와 지원 브라우저 목표가 확정됐다. K3/X1 첫 IAM S1 범위/개발 순서·구체 계약 PROPOSED·별도 구현 지시를 유지한다. AB 정책 승인으로 아래 기술계약 전체를 채택하지 않는다.

2026-10-12 승인 근거 갱신: [2026-10-12 일괄 승인](../product/product-decisions.md#review-20261012-batch)의 B1–B7/A1–A10만 확정한다. A4/A5는 2번(최초 설정 링크 30분/전 역할 idle 30분·absolute 8시간), 나머지는 1번이며 v1 PG AuthSession+opaque Cookie는 ADR-0004 ACCEPTED다. JWT는 후속 버전의 재검토 후보다. D02/D03/D07의 첫 범위·Bootstrap·복구 제외 운영 한계와 중요 관리 재인증 5분·D10 제한 수치·D11 세부/실제 D12 수집·접근·보존은 이번 답변으로 일괄 승인하지 않는다. 라이브러리/차단목록/정규화·구체 계약/UoW·잠금/검증은 별도 기술 검토이며 구현 지시는 아직 없다.

Status: **S1a/S1b 개발 인수 PASS — 2026-10-13. K3/X1·§4/§9/§10의 제한된 구현·검증 완료; 전체 설계의 PROPOSED/후속·운영 게이트 유지**. [PREP 판정](prep-iam-001-review.json) 및 [S1 판정](iam-001-s1-review.json)을 따른다.
검토일: 2026-09-18. 기준: `main`, `b83defe3fc564b56d0f77cb075ddb5436759d191`.

첫 증분 범위·계약/인수 조건은 이 문서를 읽되, 현재 승인 정책은 [2026-10-12 일괄 승인](../product/product-decisions.md#review-20261012-batch)을 우선한다. ADR-0004는 v1 인증 방식 ACCEPTED다. 아래 D/F/O 번호는 상세 검토 항목이며 B/A 답변이 각 행 전체/부수 수치·전이·구체 계약의 승인은 아니다.

2026-10-12 승인 갱신: 일회용 링크 본인 설정에 더해 최초 설정 링크 30분/단일 사용/재발급 시 이전 폐기(A4)가 확정됐다. 전달 채널/수신자 확인·활성 계정 reset 및 다른 D/F/O의 잔여는 구분한다. 기술 계약과 S1/S2 범위는 계속 제안이다.

같은 날 추가 사용자 결정: Master Admin 또는 Branch Admin이 Trainer를 겸하며 **한 계정으로 관리 업무와 본인의 PT 진행 기록을 수행**한다([ARCH-001의 부분 해결](../product/open-questions.md#arch-001)). 계정 신원과 역할/Scope 부여를 분리하는 기술안을 재검토한다. 관리 Branch 단일 제한과 실제 Trainer/Home Branch의 Workforce 소유권은 유지한다. 후속 최종 정정으로 보상 설정은 보유한 관리 범위 안이면 본인도 조회·변경 가능하다. Master는 본인 포함 전체, Branch Admin은 본인 Trainer의 Home Branch가 관리 Branch일 때 허용하며 관리자 권한 없는 Trainer의 설정 접근 금지는 유지한다. 이 결정은 S1에서 Trainer 기능을 선행 구현하거나 D02의 전체 계약을 승인한다는 뜻이 아니다.

## 1. 추천 단위와 완료 경계

**S1은 영속 PostgreSQL 기반 서비스의 첫 기능 증분이다. K3으로 실제 계정 준비 → 관리자 비밀번호 로그인 → 지점 접근 제어 → 인증 철회의 첫 개발 검증 범위를 선택했으며, 첫 인수는 가상 데이터의 격리 환경에서 수행한다.** S1 완료는 운영 개시 허용이나 전체 IAM 완료가 아니다. 가상 데이터·24시간 실행·소유 영역 폐기는 별도 실험/인수 하네스의 실행 관리 후보이며 **제품 계정·데이터 수명이나 삭제 기본값으로 넣지 않는다.** 기존 A~D에서 복구·재설정·추가 Master·Master 권한 전이를 분리한다. DB schema만 먼저 만드는 작업을 Vertical Slice 완료로 부르지 않는다.

| 검토 출발 흐름 | S1의 최소 포함 기능 / 필요한 이유·의존성 |
| --- | --- |
| 1–2. Bootstrap, Organization·최초 Master | 일회성 로컬 CLI. 계정 준비를 fixture/수동 SQL로 대체하지 않기 위해 필요. 빈 소유권 확인 DB, migration, IAM/Organization/Audit 원자성에 의존 |
| 3–4. 로그인, 현재 사용자·Scope | 실제 해시 검증, AuthSession, CSRF, `/auth/me`. 서버가 검증한 신원에서 인가까지 이어지는 출발점 |
| 5. 지점 A/B 생성 | Master 전용 생성. 허용/금지 지점을 실제 제품 경로로 준비. Organization 계약과 감사 필요 |
| 6. Branch Admin 발급·본인 암호 설정 | Master 발급 → PENDING_SETUP → 본인 설정 → ACTIVE. X1 승인: 발급 응답을 잃어 ID를 못 받으면 Master Org의 정확한 Login ID 조회 후 설정 대기 링크 재발급. A4 30분 단일 사용/이전 링크 폐기·현재 인가/상태/version 재검사. 활성 계정 암호 재설정과 구별 |
| 7–9. 목록·상세·다른 지점 ID 차단 | Master 자기 조직 전체, Branch Admin 단일 지점. 목록 pagination/count와 상세 모두 서버 제한. 클라이언트 권한 필드는 근거로 사용하지 않음 |
| 10. 로그아웃 | 현재 AuthSession 서버 폐기+쿠키 삭제. 복사해 둔 쿠키가 다음 요청에서 실패해야 함 |
| 11. 차단·Scope 변경 | Master가 ACTIVE Branch Admin을 DISABLED로 차단하거나 같은 조직 A→B로 관리 지점 변경. 모든 기존 인증 철회와 재로그인 후 새 Scope를 검증. Master 자체 변경/승격/강등 제외 |
| 12. 중요 변경과 감사 | Bootstrap·지점 생성·발급/재발급·활성화·차단·Scope 변경과 감사가 한 commit 또는 전부 rollback. 보안 버전과 토큰 철회도 같은 경계 |

**S1 완료:** 새 전용 테스트 영역에서 CLI와 실제 API로 조직·Master·지점 A/B·각 Branch Admin을 준비하고, 허용/금지 조회·여러 인증의 철회·아래 U1/P1/C1/B1 수준의 필수 검사를 모두 통과해야 한다. 빠진 수준은 미검증으로 표기하며 S1 완료로 올리지 않는다. HTTPS 브라우저 하네스는 검증용이며 운영 UI/Responsive v1 완료가 아니다.

더 작은 작업이 필요하면 **S1a(준비·로그인·Scope 조회·로그아웃)**와 **S1b(Branch Admin 차단·Scope 변경·독립 worker 경합)**로 순차 나눌 수 있다. S1a도 CLI→실제 발급→로그인과 감사·HTTPS 검사를 가진 독립적인 개발 중간 인수 단위다. 그러나 흐름 11이 빠지므로 S1/IAM-001 완료 또는 운영 사용으로 보고할 수 없다. 추천은 정책 승인을 S1 단위로 받고 구현 전달만 두 작업으로 나누는 것이다.

**S2(계정 수명 후속):** DISABLED 복구, 활성 계정 암호 재설정/본인 변경, 추가 Master 발급, Master 차단/강등과 마지막 Master 보호, Login ID 변경, 비상 복구. 각 기능 승인·인수 이후에만 제공한다. 기존 IAM-001의 전체 관리자 흐름은 S1+S2 완료로 판단하며, 운영 허용은 MFA·전달·보존·백업 복구 등의 별도 운영 게이트까지 필요하다. **Trainer 실제 로그인/연결은 후속 Workforce v1 증분**이다. 가짜 Trainer 모델이나 관리자 로그인만 가능한 인증기를 만들지 않는다. Operator 단일 Branch·신규 Operator/Trainer 발급과 E5 기존 역할 추가/회수의 Actor/Scope는 승인됐고, 대상 상태/연결·역할 조합/재부여·공개 계약은 MB-004/ARCH-001 후속이다. Member 로그인·예약·Mobile App은 Future다.

2026-10-12 G1–G5 승인과 S1 범위: Branch 비활성만으로 유효 계정/역할의 로그인/기존 조회를 거부하는 정책은 채택하지 않는다. 현재 계정/역할·행위별 Scope와 실제 지점 사실을 구분한다. 과거 수업 처리/타 활성 지점 이용·이동은 해당 후속 모듈의 업무이며 S1에 지점 상태 변경/Trainer·PT·정산·이동 기능을 자동 포함하지 않는다. 현재 제안 S1/S2 범위·최소 상태/조회 계약·검증 경계는 계속 기술 검토와 별도 구현 지시 대상이다. [2026-10-12 G 일괄 승인](../product/product-decisions.md#review-20261012-g-batch).

2026-10-12 K3 승인 경계: 위 S1 기능 범위/개발 순서와 복구/추가 Master/Trainer 연결의 후속 분리는 선택됐다. 표의 구체 준비·발급/상태명·API/계약·공유 UoW/잠금/감사 배치·인수 수준/하네스의 전체 일괄 채택이나 구현 지시는 아니다. 구체 설계는 PROPOSED로 검토하고 실제 검증 전 S1 완료·전체 IAM 완료·운영 허용을 보고하지 않는다. [2026-10-12 K 일괄 승인](../product/product-decisions.md#review-20261012-k-batch).

## 2. 승인 질문 — 첫 구현 전에 필요한 것

D01~D12는 첫 구현의 의존성을 검토하기 위한 묶음이며 모두를 사용자 정책 질문으로 일괄 처리하지 않는다. 계정 식별·암호·전달·상태/수명·철회·실제 기록 수집/접근 등 제품·운영 정책은 관련 기능 구현 전에 사용자 결정이 필요하다. 인증 후보·모듈/UoW·브라우저 방식은 기술 검토와 그에 따른 제품 영향의 확인 대상으로 구분한다. 패키지 호환성·해시 비용 측정·임시 인증서/프로필·작업 소유 실험 영역과 실행시간 관리 같은 구현/하네스 상세는 허용된 작업 안에서 담당자가 검증·제안하며 별도 사용자 정책 승인을 요구하지 않는다. D01/D02의 위임 제안이나 이번 사전검증을 기술 채택·정책 승인으로 간주하지 않는다.

| 항목 / 사용자에게 묻는 질문 | 추천안 | 이유 | 다른 선택의 사용자 경험·구현·검증 영향 | 기존 게이트 |
| --- | --- | --- | --- | --- |
| **D01 인증 — A1 승인/기술 검토 분리** | v1 PG 서버 AuthSession+opaque Cookie 채택(ADR-0004 ACCEPTED). pwdlib/Argon2id·버전/비용은 후보로 검토 | 차단/Scope 변경을 서버 상태로 관리하는 선택은 승인됐다 | JWT는 후속 버전의 별도 재검토/ADR. 라이브러리·저장/계약·잠금은 일괄 승인 아님 | T-05/T-02, ARCH-002, A1 |
| **D02 범위·책임 — K3 기능 범위/순서 승인; 구체 책임/계약 후속** | 관리자 인증/지점 접근 제어의 S1 개발 검증부터, 복구/추가 Master/Trainer 연결은 후속. §4 책임/공유 UoW·§5 잠금 순서는 상세 검토 제안 | 전체 모듈 승인 없이 첫 관리자 흐름을 구체 검토하고 후속 v1/운영 의무 유지 | 구체 모듈 소유권/Caller·DB/API/상태 enum/UoW/잠금·인수 방식/위임은 K3으로 일괄 채택되지 않음. 코드 작성은 별도 지시 | T-01/T-09, ARCH-001/002; K3; [2026-10-12 K 일괄 승인](../product/product-decisions.md#review-20261012-k-batch) |
| **D03 Bootstrap — E1 방식 승인/보호 상세** | 설치 담당자의 제한된 설치 명령 최초1회 실행/최초 Master 본인 암호 설정. S1은 격리된 로컬 가상 환경 후보이며 숨김 TTY/opt-in·대상 소유권·원자 생성/중복 방어를 상세 검토 | 초기 웹 화면/고정 관리자 암호를 추가하지 않음. 명령은 아직 미구현 | 실제 설치 담당 지정/권한 지급·회수·본인 확인/보호 입력·원격/운영 절차/실패·감사·경합 검증은 후속. 첫 로컬 검증과 운영 허용 구분 | ARCH-002, OPS-001, T-07, E1 |
| **D04 Login ID — A2/C6/E3/E4 승인** | 별도 영문·숫자 중심 3–64자/대소문자 미구별. Master ID 변경·계정/연결/이력 보존·전 로그인 종료. 이전 ID 원래 계정 예약/다른 계정 재할당 금지·현재 ID만 로그인 | TrainerA/trainera 동일, 발급/변경/예약에도 같은 비교. 원래 계정 재사용도 Master 변경 절차 | 구분자/공백·정규화/표시·예약/유일성·감사/경합 및 구현 증분은 후속 | ARCH-002, LEGAL-001, A2/C6/E3/E4 |
| **D05 비밀번호 — A3 정책 승인/공급 검토** | 15–128자, 조합 강제/주기 변경 강제 없음, 흔한 암호 차단. Unicode/정규화·로컬 차단목록의 출처/적합성/무결성·해시 비용은 상세 검토 | 길이·UX·차단 의무는 확정, 공급 구현 가능성만으로 품질 충족 아님 | 유출목록 공급 선정/외부 조회·누락 대응의 기존 후보는 A3 전체 승인이 아님. 빈 목록/소형 실험 목록으로 방어 완료 주장 불가 | ARCH-002, T-05/T-07, A3 |
| **D06 최초 설정·전달 — A4/E2 승인** | 30분 단일 사용·재발급 시 이전 최초 링크 폐기. 허용된 관리자가 본인 확인 후 대면/확인된 1:1 업무 연락으로 최초 설정·reset 링크 전달. 시스템 이메일 자동 발송 미채택 | 실제 대상자 본인 암호 설정/발급·reset Actor 경계 유지 | AB3로 활성 계정 reset TTL30분 확정. 확인/전달 운영 절차·URL/노출/소비/준비 CSRF 상세 및 검증은 후속 | ARCH-002, LEGAL-001, T-07, A4/E2 |
| **D07 계정 전이·Master — K3 첫 기능/후속 분리 승인** | 첫 기능의 관리자 로그인/지점 접근·차단/Scope 변경 반영 개발 검증을 먼저 진행. 복구/추가 Master/Trainer 연결은 후속이며 §4의 Branch Admin 발급/차단/A→B 상태·진입점은 구체 제안 | 첫 흐름의 인증 철회를 검증하는 순서를 선택하며 전체 IAM/운영 완료와 구분 | 유일 Master 분실/침해 시 개발 사용 중단·bootstrap/DB 초기화로 복구 대체 없음. 상시 사용/실운영 전 MFA·비상 복구 등 필수 후속 검증. 상태 전이/API/잠금 상세는 PROPOSED | ARCH-002, ARCH-001, MB-004; K3; [2026-10-12 K 일괄 승인](../product/product-decisions.md#review-20261012-k-batch) |
| **D08 수명/관리 확인 — A5/C1 승인** | 모든 역할 idle 30분/absolute 8시간. 유효 로그인/기존 Scope 안의 계정 관리는 추가 비밀번호 재확인 없이 허용 | 5분 이내 비밀번호 확인·이를 위한 S1 새 로그인/S2 재인증 후보 미채택 | 실제 만료/현재 인가·CSRF/운영 MFA 유지. 본인 암호 변경의 현재 암호 확인(C3)은 별개. 활동/polling·갱신·경합은 상세 검토 | ARCH-002, T-05, A5/C1/C3 |
| **D09 기기·보안 변경 — A6/A7/C3/C4/C6 승인** | 복수 독립 AuthSession/일반 logout 현재만. 관리 역할/Branch 변경·본인 암호 변경 성공·Master reset 확정·Login ID 변경은 기존 로그인 전부 종료 | 본인 암호 변경에는 현재 암호 확인, reset 확정부터 이전 암호도 무효. Trainer 업무 비활성과 구별 | 보안 버전/잠금·처리 중 응답/설정 토큰 처리의 구체 순서·원자성 검토. 시스템 철회와 사용자 전체 로그아웃 기능은 별개 | ARCH-002, T-09, A6/A7/C3/C4/C6 |
| **D10 반복 시도 — C2 계정 정책 승인/IP 상세 후보** | 계정당 15분 내 5회 실패 시 15분 대기 후 재시도. 영구 잠금/관리자 수동 해제 없음 | 계정 비노출의 일반 오류와 현재 차단 정책을 유지하며 원자적 카운터/창·초기화·동시 시도를 상세 설계 | IP당 15분 100회/준비 상태·토큰 목적별 예산은 미승인 기술 후보. 공유 NAT/프록시 신뢰·해시 자원 보호/보관은 별도 검토 | ARCH-002/004, T-09/T-07, C2 |
| **D11 브라우저:** same-origin HTTPS를 인수 기준으로 하고 loopback HTTP는 명시적인 개발 예외만 허용할까요? | Secure/HttpOnly/host-only/SameSite=Lax/Path=/ 및 CSRF. HTTP는 development/test+opt-in+정확한 loopback origin과 별도 쿠키명, 제한된 가상 데이터만. 로컬 HTTPS 실제 브라우저 인수는 필수 | 운영 호스팅/프레임워크 선정 없이 브라우저 보안 검증 가능 | HTTP만 검사하면 S1 완료 불가. cross-origin 프론트면 CORS·Origin·프록시 신뢰 계약 추가. 상세 하네스 도구는 구현자 위임 | T-05/06/07, ARCH-004 |
| **D12 기록·접근 — C7/C8 부분 승인** | 로그인 감사는 계정·시각·행위·성공/실패 최소 기록/원문 IP·브라우저 제외. 인증/계정 관리 감사의 앱 열람은 자기 Organization Master만. 계정 관리 필수 변경/Actor 감사 유지 | 반복 시도 방어의 일시적 IP 처리와 로그인 사건을 구분. 비밀번호/토큰/링크 등 비밀 금지. 하네스 가상 데이터/24시간/정리는 실행 관리 후보 | 미확인 계정 사건 표현·조회 계약/운영 접근·보존/백업/삭제는 LEGAL-001/O02 후속. 하네스 정리를 제품 기록 정책으로 대체하지 않음 | LEGAL-001, ARCH-001/002/004, OPS-001, C7/C8 |

D10의 원자적 집계 후보는 해시 전 슬롯 예약과 실패/성공 결과 처리, 여러 worker 공유 저장을 검토한다. 진행 중 예약의 실패 한도 산입·성공 시 초기화/예약 해제·기존 cooldown 처리·중단 요청/창 경계는 아직 기술 상세이며 C2 숫자 정책 승인만으로 이 알고리즘까지 채택하지 않는다. IP 예산/준비·토큰 제출의 제한도 별도 후보다. 존재하지 않는 ID도 계정 존재를 노출하지 않는 제한/일반 오류가 필요하고 임의 forwarding header 우회를 허용하지 않는다. 실제 단위·경합/NAT 검증은 미수행이다.

### 후속·운영 결정을 지금부터 구현 가능으로 처리하지 않는 기준

| 항목 / 구체 질문 | 추천안과 이유 | 대안 영향 | 기존 게이트 | 결정 시점 |
| --- | --- | --- | --- | --- |
| **F01 복구·재설정/본인 변경 — A8/C1/C3/C4/E6 승인** | 계정 전체 차단/복구·관리자 reset은 같은 Organization Master만. 일반 차단 해제 시 유효 기존 암호 재로그인/매번 강제 reset 없음. ACTIVE reset 확정 즉시 옛 암호/전 로그인 무효, 본인 현재 암호 확인 변경 후 전 로그인 종료. 추가 관리 재인증 없음 | AB3 reset TTL30분 확정. 전달 운영·본인 확인/정확한 전이는 후속. 옛 AuthSession/무효 암호·회수한 역할/MFA·Trainer 상태 복원 없음. 침해 의심 복구/Trainer 재활성화 B1 별도 | ARCH-002, T-05/T-09, A8/C1/C3/C4/E6 | S2/해당 기능 전 상세 필요, 현재 정책 재질문 없음 |
| **F02 추가·마지막 Master — A9/C5 승인** | 복수 Master 허용/마지막 사용 가능 Master 차단·권한 제거·일반 관리자 reset 금지. 현재 암호를 확인하는 본인 변경(C3)은 허용 | 사용 가능 판정/발급·동시 변경/조직 잠금은 기술 상세. 미활성/차단/reset 대기를 정상 대체자로 세어 보호를 우회하지 않음. 별도 비상 복구는 아직 필요 | ARCH-002, T-09, A9/C3/C5 | S2/해당 기능 전 상세 필요, 복구 완료 아님 |
| **F03 유일 Master 암호 분실·침해:** 정상 Master가 없을 때 어떤 별도 복구를 허용할까요? | bootstrap 재사용 금지. 유일 Master의 일반 재설정을 막는 것만으로는 복구되지 않으므로 설치 통제권+사용자 확인·감사·전체 인증 철회의 별도 복구 절차를 설계한 후 제공. AB5로 조직 업무책임자 확인/승인+별도 시스템 운영담당자 실행을 선택. 실제 확인 증거/자격·대상/범위/실패 경로는 후속 | 마지막 Master 재설정 예외를 허용하면 복구 완료 전 관리 중단과 실패 복구 인수 필요. 우회 SQL은 제품 복구 경로가 아님 | ARCH-002, OPS-001, T-07/T-09 | 해당 후속 기능 구현 전에 필요; 실제 운영 개시 전 완료 필수 |
| **F04 사용자 전체 로그아웃의 남은 범위** | C1에 따라 계정 관리의 별도 비밀번호 재인증 API/5분 강제 재로그인 후보는 미채택. C3 본인 암호 변경의 현재 암호 확인은 별개. 시스템 전 로그인 철회는 유지 | 사용자 임의 전체 로그아웃/기기 목록·개별 원격 철회는 별도 기능/공개 계약 후보이며 이번에 승인하지 않음 | ARCH-002, T-05/T-09, C1/C3 | 해당 후속 기능 전 상세 검토 |
| **O01 설치·전달의 남은 운영 상세 — E1/E2 방식 승인** | 제한된 최초1회 설치 명령/본인 암호 설정, 허용 관리자의 수신자 확인 후 대면/확인된 1:1 직접 링크 전달. 이메일/SMS 자동화 서비스는 도입하지 않음 | 실제 설치 책임자/통제 자격 지급·회수·원격 최초 본인 확인/보호 입력, 확인된 연락 경로/오전달·실패 대응/운영 검증은 후속. 개발 하네스로 운영 허용을 대신하지 않음 | ARCH-002, OPS-001, T-07, E1/E2 | 실제 운영/원격 전달 기능 구현 전 해당 상세 필요 |
| **O02 보존·운영 접근·삭제의 남은 범위** | 앱 사용자의 인증/계정 관리 감사 읽기는 C7의 Master 자기 Organization, 로그인 최소 필드는 C8로 해결. 사건/보안 상태/제한 digest/백업별 보존·운영 접근/정리 실패·복원 후 인증 처리와 삭제 검증은 후속 | 기존 24시간/90일 표는 비교 후보. 짧은/장기 보존의 운영 영향과 실제 삭제 수단을 검토하며 하네스 정리로 대체하지 않음 | LEGAL-001, ARCH-001/004, T-07/T-09, C7/C8 | 실제 운영 전, 상시 수집/검색/정리 기능 도입 전 해당 상세 필요 |
| **O03 운영 MFA — A10 시점 승인/수단·품질 후속** | Master/Branch Admin MFA는 실제 운영 전 필수. 로컬 개발/첫 기능 검증은 먼저 가능. AB4 비밀번호 뒤 사용자검증 Passkey를 추가 수단으로 선택, 구현 완료/운영 허용 아님 | AB4 수단 선택 완료. 등록/분실/복구와 실제 TLS/도메인·AB6 브라우저 OS/기기 매트릭스/부하/NAT·차단목록 운영은 후속 | ARCH-002/004, PD-021, OPS-001, T-05/06/07, A10 | 실제 운영 전 구현/검증 필수 |

## 3. 개발 검증 절차와 기록 범위

### 일회용 비밀번호 설정 링크의 개발 인수 후보

1. 검증 실행자가 전용 로컬 DB/schema 소유권과 run ID를 확인한다. 실사용자 이름·연락처는 넣지 않고 Master·Branch Admin 역할의 가상 ID를 사용한다. 별도 브라우저 프로필 또는 격리 context로 기기를 구별한다.
2. 검증용 same-origin HTTPS 화면에서 Master가 로그인 후 Branch Admin을 발급하고 일회용 비밀번호 설정 링크를 확인한다. 응답 body는 no-store, 링크 표시 영역은 외부 스크립트/분석 도구/서비스워커/LocalStorage/다운로드 없음. 접근 로그·body trace·스크린샷·영상·HAR 수집을 끈다. CLI에 토큰 인자를 넣거나 curl 응답을 셸 출력으로 복사하지 않는다. API의 setup_token으로 화면에서 링크를 구성할지 setup_link를 반환할지와 URL 내 토큰 표현은 기술 상세 검토 대상이다.
3. 받는 역할의 사람이 별도 브라우저 context에서 전달받은 설정 링크를 열어 본인 비밀번호를 입력한다. 가상 역할을 한 검증자가 교대로 수행할 수 있지만 Master 인증 쿠키는 넘기지 않는다. 긴 토큰의 수동 입력은 요구하지 않는다. 링크 열람만으로 토큰을 소비하지 않는 후보와 주소/Referer/로그의 노출 방지를 실제 브라우저에서 검증한다. 인수 하네스의 격리된 링크 전달은 실제 운영 전달 채널의 선정과 구분한다.
4. 설정 완료는 인증 쿠키를 발급하지 않는다. 토큰 재제출 거부, 새 비밀번호 로그인 성공, Master에게 암호 비노출을 확인한다. 만료/표시 유실이면 계정 ID로 현재 version을 조회한 뒤 **PENDING_SETUP에 한하여** 재발급한다. ACTIVE는 재발급 endpoint로 재설정할 수 없다.
5. 자동 인수는 HTTP 응답에서 받은 token을 테스트 프로세스 메모리로 다음 POST에 전달한다. 실패 assertion/trace에도 값이 출력되지 않도록 검증한다. 이 자동 경로는 수동 전달 UX 검증을 대체하지 않는다. HTTP 예외로 서버 연동을 점검해도 HTTPS 전달 인수는 별도로 수행한다.

하네스·CLI는 모두 향후 구현 항목이며 현재 제공하지 않는다. 검증 화면은 배포 UI 선정과 분리하고 development/test 전용 진입점으로 제한한다. 미활성 계정의 token 재발급은 최초 전달 실패를 처리하는 최소 기능이며 활성 계정 복구를 우회하지 않는다.

### 수집·접근·정리의 첫 범위

- **필수 감사:** Bootstrap, 지점 생성, 계정 발급/활성화 재발급/활성화, 차단, Scope 변경. 사건 ID·run/request ID·서버 UTC 시각·검증된 actor ID와 당시 역할/Scope·대상 ID·허용 필드 전후(계정 상태/관리 Branch/version, 지점 code/name)만 기록한다. Bootstrap은 인증 전 설치 실행자 유형+run ID이며 가짜 로그인 Actor가 아니다.
- **인증 사건(C8 승인):** 로그인 감사는 계정·시각·행위·성공/실패 결과의 최소 정보다. 알려진 계정은 내부 ID로 표현하고 미확인 계정의 안전한 사건 표현은 상세 검토한다. 원문 입력 ID/IP·브라우저 정보·비밀번호/해시·쿠키/설정/CSRF 토큰·링크·본문·연락처·보상정보를 로그인 감사에 남기지 않는다. 실패 제한/로그아웃 등 사건의 구체 유형·저장 계약/보존은 후속이며 모든 필드를 일괄 승인하지 않는다.
- **보안 상태:** AuthSession/준비/활성화 digest와 수명, 제한용 keyed ID/IP digest·창·카운터. digest도 무조건 익명정보라 간주하지 않는다. 로컬 외부 비밀 설정의 동일 키를 worker가 공유하며 문서/로그에 출력하지 않는다. 요청 IP는 direct peer를 사용하고 임의 forwarding header를 신뢰하지 않는다.
- **접근(C7 승인/인수 경로 구분):** 인증/계정 관리 감사의 앱 사용자 열람은 자기 Organization Master만 허용한다. Branch Admin/Operator/Trainer 단독은 거부한다. S1의 앱 감사 조회/export API는 아직 포함하지 않는 증분 후보이며 제품 열람 권한이 없다는 의미는 아니다. 가상 인수 run의 제한된 실행자 조회는 별도 하네스 권한이고 운영 사용자 권한을 대신하지 않는다. Backend/프록시/하네스의 일반 로그도 비밀/개인정보 allowlist를 적용한다.
- **정리:** 최대 24시간 또는 실행 종료 시의 폐기는 별도로 생성한 실험/인수 run 관리 후보다. 적용한다면 검증 실행자가 소유 확인한 해당 영역만 폐기·확인한다. 기존 개발/테스트 DB·다른 run·Compose 볼륨은 대상이 아니다. 제품 계정·감사 데이터의 수명/삭제 기본값으로 넣지 않으며 영속 서비스에 자동 reset/전체 영역 폐기를 구현하지 않는다. 실제 서비스의 C7/C8 수집·앱 열람 원칙 외 보존/삭제·미확인 사건/보안 상태/운영 접근은 D12/LEGAL-001/O02 후속이고, 하네스 정리로 그 결정을 대체하지 않는다. 인증 만료는 행 삭제와 무관하게 적용한다.

Master 암호 분실 시 S1은 **관리 불능을 인정하고 중단**한다. 가상 테스트 영역의 정상 종료/새 실행은 개발 검증 준비일 뿐 계정 복구 인수가 아니다. 기존 DB를 초기화하거나 bootstrap 완료 표시를 지워 복구하지 않는다. 상시 사용·실데이터 도입에는 F03이 필수다.

## 4. 구현 전달 계약 — 필요한 진입점과 소유권

아래 이름은 아직 존재하지 않는 제안이다. `/api/v1` 접두사 후보를 생략했다. 원본 설계의 더 넓은 API 표를 S1 구현 목록으로 사용하지 않는다.

| CLI/API | S1 계약 |
| --- | --- |
| `bootstrap-initial-master` | development/test 한정 명령, 비밀 숨김 입력. InstallationControl 잠금→미설치/빈 조직·계정 재확인→조직+ACTIVE Master+감사+완료표시 원자 생성. 중복/불일치/감사 실패 non-zero, force·재설정 없음 |
| `GET /auth/csrf` | custom header와 출처 검사 후 현재 인증 또는 짧은 준비 상태에 결합된 nonce 제공, no-store. 단독 인증 근거가 아님 |
| `POST /auth/login` | `{login_id,password}` + 준비 쿠키/CSRF. 실제 검증 후 준비 상태 소비+새 AuthSession 원자 발급. 204+HttpOnly 쿠키, JSON에 인증 token 없음 |
| `GET /auth/me` | 현재 계정/조직/부여된 역할과 각 Scope·이번 기능 capabilities만 반환하는 후보. 단일 role 응답의 겸임 제한을 피함. 인증과 관리자 인가 분리, idle 갱신 없음 |
| `POST /auth/logout` | 유효 CSRF로 현재 세션 서버 폐기 후 204+쿠키 삭제. 무효/폐기 상태 재요청은 준비 CSRF로 정리 가능. DB 결과 불명확이면 성공 응답 금지 |
| `POST /admin/branches` | Master만 `{code,name}`, 조직은 Caller에서 결정. 201 비밀 없는 ID/code/name. 정보 수정/비활성화 없음 |
| `GET /branches`, `GET /branches/{id}` | Master는 자기 Organization, Branch Admin은 자신의 단일 Branch. DTO는 ID/code/name만. 서버 Scope 적용 후 pagination/count. 부가 권한·scope query 거부 |
| `POST /admin/accounts` | 유효 로그인/현재 권한의 Master만 `{login_id,branch_id}`. **Branch Admin만** 발급, organization/role/admin_scope 임의 입력 거부. 201 `{account_id,state,version,setup_link,expires_at}`. 신뢰한 서버 origin의 일회용 링크를 한 번 반환. 같은 조직 지점 검증 |
| `GET /admin/accounts/{id}` | Master만 같은 조직 관리자 계정의 ID/login_id/state/Scope/version. token/해시 없음. 알려진 ID 조회는 유지하며 일반 목록/부분 검색 없음 |
| `POST /admin/accounts/lookup` | X1 승인 기능의 계약 후보. 유효 로그인/현재 Master+CSRF, `{login_id}` 정확한 대소문자 미구별 비교. 자기 Organization S1 Branch Admin만 `account_id,login_id,state,admin_scope,version` 반환. 원래 token/해시·일반 목록/부분 검색 없음. 조회는 대상 상태/설정 token을 변경하지 않음 |
| `POST /admin/accounts/{id}/activation` | 유효 로그인/현재 권한의 Master, `{expected_version}`. PENDING_SETUP만 활성화 token 재발급, 이전 token 폐기+version 증가+감사. ACTIVE/DISABLED/Master는 409. 201 `{setup_link,expires_at}` 한 번 제공 |
| `POST /auth/credentials/complete` | 준비 CSRF+`{setup_token,new_password}`, PENDING_SETUP·activation 목적·version·만료/미소비 재검사. 해시+ACTIVE+version 증가+token 소비/나머지 폐기+감사 원자 반영. 204, 자동 로그인 없음 |
| `PATCH /admin/accounts/{id}/access` | 유효 로그인/현재 권한의 Master, `{branch_id,expected_version}`. ACTIVE Branch Admin의 같은 조직 관리 지점만 변경. role·조직·Master 전이 불가. 200 비밀 없는 새 Scope/version |
| `PATCH /admin/accounts/{id}/status` | 유효 로그인/현재 권한의 Master, `{status:DISABLED,expected_version}`. ACTIVE Branch Admin만 차단. 200 새 상태/version, 복구·PENDING 차단·Master 차단 불포함 |

같은 값을 다시 지정하는 access 명령은 현재 version 일치 시 무변경 결과를 반환하고 불필요한 철회/변경 감사를 만들지 않는다. 상태 변경 재시도는 현재 version/상태를 재조회하도록 409로 수렴한다. 로그인된 상태로 다른 계정 로그인은 409, 로그아웃 후 새 로그인한다. 계정/지점 생성의 통신 결과가 불명확할 때 자동 재시도하지 않는다. X1 승인으로 계정 발급 응답을 잃어 ID도 모르면 Master가 자기 Organization Branch Admin을 정확한 Login ID로 조회해 현재 ID/상태·Scope/version을 확인하고, PENDING_SETUP에서 기존 activation 계약으로 새 링크를 명시적으로 재발급한다. 새 링크는 30분 단일 사용/이전 최초 링크 폐기·감사 원자성을 유지한다. 조회 결과는 직전 발급 성공 증명/재발급 권한 snapshot이 아니며 재발급 요청에서 현재 Caller/상태/version을 재검사한다. ACTIVE/DISABLED/Master reset·원래 token 조회·자동 중복 생성/반복 재발급은 제공하지 않는다. 404로 미완료 commit 부재를 단정하지 않으며 결과 불명확 시 상태 재확인을 우선한다. 일반 생성 멱등성/다른 결과 확인·운영 복구 계약은 별도 후속이다.

| 상태·명령 | 허용 결과 | 제한 |
| --- | --- | --- |
| Bootstrap | 최초 Master ACTIVE | 단 한 번, 이후 Master 쓰기 API 없음 |
| Branch Admin 발급 | PENDING_SETUP, 해시 없음 | 로그인 불가 |
| 활성화 / 활성화 재발급 | PENDING_SETUP→ACTIVE / PENDING_SETUP 유지 | 같은 최신 version의 유효 activation token만 사용; 재발급은 옛 token 무효 |
| 차단 | ACTIVE→DISABLED | 모든 AuthSession/설정 요청 폐기, S1 역전이 없음 |
| Scope 변경 | ACTIVE 유지, A→B | ADMIN+BRANCH 유지, 같은 조직·정확히 한 지점, 이전 인증 전체 폐기 |
| 복구/암호 재설정/추가 Master/승강격 | S2 | 숨은 generic PATCH 또는 CLI로 우회 제공하지 않음 |

IAM은 Account·역할/관리 Scope 부여·AuthSession·LoginPreparation·activation 전용 CredentialSetup·AttemptBudget·InstallationControl의 유일 쓰기 소유자다. S1에는 reset 목적/credential_setup_required 등 후속 재설정 전용 필드를 미리 구현하지 않는다. Organization은 조직·지점 사실의 소유자이며 `CreateInitialOrganization/CreateBranch/GetBranchFacts/ListVisibleBranches/GetVisibleBranch`만 제공한다. Audit은 allowlist 사건의 쓰기 소유자다. Application은 `Authenticate/ResolveCaller/Logout/IssueBranchAdmin/ReissueActivation/CompleteActivation/DisableBranchAdmin/ChangeManagedBranch`와 Organization·Audit 계약을 조정하고 한 UoW를 commit한다. 모듈별 독립 commit·다른 모듈 ORM/Repository 접근은 없다.

`DBSession`(SQLAlchemy 자원), `AuthSession`(인증), `PTSession`(수업)은 별개다. VerifiedCaller는 서버가 만든 불변 ID/역할 부여와 각 Scope/security_version/인증시각 값이며 JSON·헤더에서 역직렬화하지 않는다. Router는 Origin/입력 확인과 HTTP 변환, Application은 인증→Caller→행위 인가→대상 Scope→소유 Use Case의 순서를 조정한다. Organization Use Case도 인가 범위를 확인하며 내부 직접 호출도 검사한다. 클라이언트의 role/organization_id/branch_id는 권한 근거가 아니고 관리 명령의 branch_id는 검증할 대상 값이다.

핵심 DB 불변식 제안(T-01/T-09): 대소문자를 구별하지 않는 현재/예약 login_id의 계정 소유 정합성 및 각 token digest 유일, 계정의 조직 FK, 지점 `(organization_id,id)` 후보키와 관리 Scope 부여의 복합 FK, ADMIN+ORGANIZATION이면 관리 branch 없음/ADMIN+BRANCH이면 관리 branch 하나, 계정의 역할 겸임 가능, PENDING_SETUP 해시 없음/ACTIVE 해시 있음, 양수 row_version/security_version(구별은 §9), AuthSession/activation의 account FK, 수명 순서 CHECK. 역할 부여의 구체 저장/잠금은 재검토하며 아래 기존 잠금 표를 새 모델의 검증 완료로 간주하지 않는다. 활성화 미소비 요청은 계정당 하나만 유효하게 갱신한다. 설치는 하나의 조직만 참조하고 최초 실행을 직렬화한다. 개인정보 이력을 cascade 삭제하는 규칙은 두지 않는다. 이 물리 FK는 추출 비용이 있는 **제안**이지 cross-module 직접 읽기 허가가 아니다. Trainer를 위한 가짜 업무 테이블·보상 필드·Pass 상태는 없다.

E5의 역할 추가/회수는 v1 제품 정책으로 승인됐지만 위 S1은 K3으로 관리자 인증/지점 접근 제어부터 개발 검증하는 범위를 선택했다. Branch Admin 최초 발급/관리의 구체 상태 전이/API·계약은 계속 제안이다. Operator/Trainer 역할 관리와 Workforce 실제 연결·대상 최소 조회/인가/감사·Caller/철회/진행 중 요청·역할 조합/재부여의 구현은 해당 후속 증분에서 설계한다. 이를 generic 계정 PATCH/SQL이나 가짜 Trainer로 S1에 선행 제공하지 않는다. E3/E4 ID 대소문자 유일성/예약은 처음 발급부터 불변식에 포함할 상세 기술 계약이 필요하다. [2026-10-12 E 일괄 승인](../product/product-decisions.md#review-20261012-e-batch)

## 5. transaction·잠금·철회와 오류 계약

**추천 관찰 결과:** 계정 보안 변경 commit 이후 권한을 확정하는 요청은 옛 AuthSession으로 성공하지 않는다. 변경보다 먼저 잠금을 얻어 인가·DTO 구성을 끝낸 응답은 변경 후 네트워크에 도착할 수 있다. 복수 기기/관리 변경 전체 재로그인은 A6/A7로 승인됐지만 이 선후/잠금 계약 자체는 기술 검토·실제 경합 검증이 필요하다.

구체안은 READ COMMITTED와 명시적 행 잠금이다. 모든 경로에서 필요한 잠금을 **InstallationControl(관리/설치만) → Account(ID 정렬) → AuthSession(ID 정렬) → LoginPreparation → CredentialSetup → Branch 사실 → Audit append** 순으로 획득한다. 일부 단계가 없으면 건너뛰되 뒤에서 앞 순서로 돌아가지 않는다. 먼저 digest로 account ID를 찾는 읽기는 탐색일 뿐 권한 증명이 아니며 잠금 후 다시 검증한다. 모듈 어댑터가 동일 DBSession/트랜잭션에 참여하되 공개 계약에는 ORM/DBSession을 전달하지 않는다.

| 경로 | 잠금·검증·commit 계약 |
| --- | --- |
| 지점 읽기·`/me` | Account `FOR SHARE` → 해당 AuthSession `FOR UPDATE`; 잠금 대기 후 현재 시각으로 만료/상태/version 재검사→VerifiedCaller→scoped query→DTO 구성. 활동 갱신은 유효 상태만, `/me` 제외. commit 후 전송 |
| 로그인·로그아웃 | 로그인 해시 검증은 잠금 밖; 발급에서는 Account SHARE→새 세션/준비 행 순서 아래 해시·상태/version 재검사. 기존 로그인 여부도 확인. 준비 상태 소비와 새 세션 발급 한 commit. 로그아웃은 Account SHARE→해당 AuthSession UPDATE→폐기+인증 사건 한 commit |
| Master의 차단/Scope 변경 | InstallationControl UPDATE→actor/target Account ID 순 UPDATE→관련 AuthSession ID 순 UPDATE→설정 행→Branch 사실. actor 현재 인증/행위 인가·target 상태/row_version 재검사. target 변경+row/security_version 증가+target 인증/설정 token 철회+감사 한 commit. 실행자 인증은 이 명령 때문에 철회하지 않음 |
| Master의 지점/계정 발급·설정 링크 재발급 | 같은 관리 잠금 계획을 처음부터 사용하고 현재 actor/대상·지점 Scope 재검사. 지점/계정 생성은 실행자 row/security_version·기존 로그인을 변경하지 않음. PENDING_SETUP 재발급은 target row_version 증가/이전 설정 token 폐기·감사 한 commit이며 실행자 로그인 유지 |
| 활성화 | 해시 생성은 잠금 밖. Account UPDATE→관련 인증→준비 상태→설정 token 순으로 잠금, 상태·purpose·version·만료를 다시 검증. 두 token 소비 요청 중 하나만 성공; 재발급 경합도 동일 계정 잠금으로 직렬화 |
| 실패 제한 | ID/IP bucket은 정렬된 key 순서로 별도 짧은 보안 상태 transaction에서 예약/결과 기록. 이 잠금을 업무 UoW와 동시에 유지하지 않는다. 실패 rollback으로 공격 횟수가 사라지지 않음. DB 장애는 503, 메모리 무제한 fallback 없음 |

Account SHARE는 변경 경로 UPDATE와 충돌해야 하므로 KEY SHARE로 약화하지 않는다. 세션 철회 중 actor 세션만 먼저 잠그고 나머지를 뒤에서 거꾸로 획득하지 않는다. ORM identity cache의 과거 Account를 그대로 사용하지 않고 잠금 읽기로 갱신한다. DB의 transaction 시작 시각을 만료 검사 시각으로 고정하면 대기 중 만료를 놓칠 수 있으므로 잠금 획득 **후** 서버 시각을 사용한다. long polling/streaming/background 작업으로 Caller를 넘기지 않는다. deadlock/잠금 timeout은 전체 rollback 후 안전한 503, S1은 숨은 자동 재시도를 하지 않는다. lock timeout 세부는 기존 DB timeout과 맞춰 구현자가 검증하되 수명·인가 의미 변경은 재검토한다.

감사 저장 실패 시 중요 변경·version·인증 철회·token 소비 모두 rollback한다. Bootstrap 중 감사 실패면 조직/계정/완료표시도 없다. 성공 로그인·로그아웃 사건 실패도 해당 AuthSession 변경과 함께 실패시킨다. 실패 로그인 기록/제한은 별도 transaction으로 유지하며 기록 저장 실패면 503으로 닫는다. **commit 응답 유실은 rollback 증거가 아니다.** 변경 결과 확인 전 성공·실패 단정/맹목 재발급을 피하고 known account ID의 상태/version으로 대조하고, 발급 응답 유실로 ID도 없으면 X1의 Master 자기 조직 Branch Admin 정확한 Login ID 조회를 사용한다. token 원문은 사후 조회하지 않는다.

오류는 `401 invalid_credentials`(없는 ID/틀린 암호/차단/미설정 동일), 보호 요청 401(무효 인증), 403(행위 인가 또는 CSRF 불충족), scoped 404(미존재/다른 조직·지점 동일), 409(version/상태/중복), 422(안전한 입력 오류), 429(일반 Retry-After), 503(DB/제한/잠금/commit 불명확)로 제한한다. token은 무효/만료/소비/폐기 모두 같은 400. Account 존재 정보는 발급 권한 있는 Master의 자기 조직 관리 응답 외 노출하지 않는다. 타 조직 branch 지정은 존재 사유를 분리하지 않는 오류로 처리한다. 원본 예외·validation 입력값·비밀을 응답/로그에 반사하지 않는다.

CSRF는 [기존 설계 7절](iam-001-design.md)의 synchronizer token+정확한 Origin/Referer·Fetch Metadata 방어를 유지한다. 준비 token으로 다른 유효 AuthSession의 변경 요청을 승인하지 않는다. 로그인/활성화/로그아웃/모든 관리 쓰기에 적용, SameSite만으로 대체하지 않는다. 로그인 성공은 새 AuthSession/CSRF로 교체하고 서버 저장 cookie digest·폐기·만료·security_version을 매 보호 요청 확인한다. C1에 따라 별도 중요 관리 재인증 API/5분 검사는 제외하며 C3 본인 암호 변경 검증은 후속 해당 기능에서 다룬다.

## 6. migration과 인수 계획 — 모두 미실행

현재 `backend/src/y3management/`는 main/application/database/config 기반이며 로그인 경로가 없다. `Database.session()`은 수명만 관리하고 자동 commit하지 않는다. Alembic `target_metadata=None`, 업무 revision 없음, pyproject에 pwdlib 없음. 기존 Import Linter의 네 계층 exhaustive 계약은 새 경계에 맞게 확장해야 하며 제거로 통과시키지 않는다. backend/·dependency·lockfile은 이번에 수정하지 않는다.

Migration은 위 S1 소유 객체/제약/인덱스와 비밀 없는 InstallationControl 초기 행만 포함한다. 고정 Master/암호·조직·Branch seed는 CLI를 대신하지 않는다. schema 등록·autogenerate 후보 수동 검토 후 별도 적용, app startup create_all/자동 upgrade/stamp 금지. 현 기준은 base→첫 revision이며 존재하지 않는 이전 업무 revision을 시험했다고 주장하지 않는다. 새 빈 전용 영역 upgrade→현재 head 확인→제약 위반 SQL 검사→실제 CLI/API 인수→소유 영역에서 downgrade/base 및 재-upgrade를 확인한다. 실패 migration rollback/고아 객체와 데이터 보존 범위를 대조한다. 향후 실제 이전 revision이 있으면 이전→새 revision 데이터 보존 검사를 추가한다. 운영 downgrade는 데이터 손실 가능성이 있어 별도 백업/forward 복구 검토 대상이다.

| 수준 / S1 필수 사례 | 관찰해야 할 결과 | 기존 기반과의 차이 |
| --- | --- | --- |
| **U1 DB 없는 정책·계약** | Login ID/암호 정규화·차단목록 누락·상태표·Role/Scope, idle/absolute 만료·추가 관리 비밀번호 확인 없음(C1), CSRF/HTTP 예외·오류 비노출, 최소 DTO/모듈 의존성. 가짜 Caller는 이 수준만 | 기존 fast는 기반 Ruff/mypy/36 pytest/Import Linter 2개였음. IAM 사례는 신규 |
| **P1 실제 PostgreSQL 전체 흐름** | 소유 영역에 migration→CLI Master→로그인→A/B 생성→실제 Branch Admin 발급/설정/로그인→목록·상세·타 지점 404. forged role/org/branch 거부. logout 복사 쿠키 401, 두 기기에서 Scope 변경 후 모두 401→새 로그인은 B만, 차단 후 암호 로그인도 401 | Foundation DB 3개는 연결·세션/health/current만 확인. fixture/수동 SQL로 인수 준비를 대체하지 않음 |
| **P2 원자성·제약·실패** | 모든 중요 변경 단계/감사 실패 주입 시 상태·version·인증·감사 대조, token 해시만 저장/중복 소비·만료/재발급 거부, migration CHECK/UNIQUE/FK 실제 위반 거부, DB 장애 503·비밀 비노출, 발급 응답 유실 후 Master 정확한 Login ID 조회/설정 대기 링크 재발급→옛 링크 거부/새 설정·실제 로그인, 중복 생성 없음/원래 token 비노출 및 남은 중단 한계 | SQLite/단위 mock만으로 성공 처리 불가. 잘못된 제약을 만드는 음성 fixture는 보조 검사로만 허용 |
| **C1 독립 연결·worker 경합** | 읽기 먼저 잠금→차단 대기→읽기 commit→차단 commit; 반대 순서는 401. Scope 변경/로그아웃과 읽기, 차단과 로그인 발급, 활성화와 재발급/동시 소비, X1 조회 후 활성화/차단/Scope 변경·재발급 응답 유실/version 재검사, 동시 bootstrap 중 1회 성공, 로그인 만료 경계/C1 추가 관리 비밀번호 확인 없음, 제한 bucket 동시 예약·NAT 공유·재시작·두 worker 일관 | barrier와 독립 connection/프로세스로 순서를 관찰; sleep 타이밍 추측·한 연결의 순차 실행은 경합 증거 아님. 타 조직 fixture는 격리 음성 검사이며 SaaS bootstrap 아님 |
| **B1 실제 HTTPS 브라우저** | 로컬 신뢰 인증서로 격리 Chromium context 두 개와 공격 origin에서 로그인/활성화/읽기/logout 수행. Secure/HttpOnly/host-only/Path/SameSite, JS cookie 비노출, 전송·삭제, CSRF 누락/위조·sibling origin·cross-site 차단, 새 로그인 후 옛 CSRF 거부, no-store/비기록 토큰 전달. 실제 브라우저/버전·origin을 결과에 기록 | TestClient는 서버 계약 검사만. HTTPS 검사에서 인증서 오류 무시 옵션 금지. Chromium은 개발 인수 대상 제안이며 v1 전체 지원 브라우저 승인 아님 |
| **B2 개발 경계·종료** | HTTP 예외는 정확한 opt-in/loopback에서만, production 비보안 설정 거부. 비밀 비기록·로컬 조회 제한·run 종료/24시간 상한과 소유 영역 폐기 확인 | 삭제 job/법적 보존 완료·운영 배포 완료가 아님 |

S1에는 Master 변경 경로가 없으므로 마지막 Master 두 명의 동시 차단/강등/재설정 시험은 **S2 필수**다. S1에서 Master 대상 status/access/activation 명령 거부를 실제 로그인으로 검사한다. Trainer/Operator 비관리자 인가는 U1 계약으로 검사하되 실제 Trainer 로그인 완료는 Workforce 후속에서만 보고한다.

승인 후 기존 `bash check.sh fast`·`bash check.sh db`에 해당 수준의 검사를 추가하고 전용 Y3_TEST_DATABASE_URL·Compose 소유권 검증·missing/skip/xfail/미수집 실패 원칙을 유지한다. 브라우저 경로는 별도 추가 구성이다. 이번 작업에서는 세 명령 경로 모두 재실행하지 않았으며 기반 36 passed/DB 3 passed/경고 2개는 [이전 WSL 기록](wsl-migration.md)이다.

## 7. 승인 이후 전달·남은 공백

구현 담당자에게는 D01~D12 중 필요한 제품·운영 정책의 항목별 승인 근거, 기술 검토/위임 결과, 범위(S1 또는 S1a→S1b), ADR-0004 선택 근거를 구분해 전달한다. 코드·검사·migration·하네스 작성 권한은 **별도 구현 지시**가 필요하다. 다음 작업의 범위는 위 API/CLI, 최소 IAM/Organization/Audit/UoW, S1 migration, U1/P1/P2/C1/B1/B2와 실행 안내다. 숨은 reset/복구/Master 관리/Trainer 모델/업무 schema는 추가하지 않는다.

Product의 확정 경계와 S1 기능 사이의 충돌은 발견하지 않았으며 A1–A10/B1–B7/C1–C13/E1–E6의 승인 정책과 남은 D/F/O 기술/정책은 분리한다. 모든 D01~D12가 미승인인 상태는 아니다. 가상 데이터·실행시간·정리는 별도 하네스 관리 후보로 구분하며 이를 영속 서비스 정책으로 바꾸지 않는다. Product 수정이 필요하면 ARCH-002에 첫 계정 수명 부분의 승인 근거와 F01~F03 잔여를 구분하고, LEGAL-001의 C7/C8 수집/앱 열람 승인 외 운영 보존/삭제 등 잔여를 구체화해야 한다. 이번에는 Product OPEN을 닫지 않는다. PT·정산 OPEN은 독립 IAM 검증을 막지 않으며 지점 조회를 보상 설정·정산 권한으로 확대하지 않는다. Pass의 ACTIVE/COMPLETED/CANCELLED는 승인 상태명으로 채택하거나 schema에 넣지 않는다.

남은 구현 전 기술 확인은 차단목록의 실제 공급 artifact, 라이브러리 지원/보안·해시 비용 측정, 실제 패키지/Import Linter 경계, 로컬 TLS·브라우저 실행 하네스다. 위임 후에도 확인 실패를 기본값/생략으로 처리할 수 없다. X1 범위의 Branch Admin 발급 응답 유실/ID 미확보는 S1 정확한 조회/설정 대기 링크 재발급으로 보완한다. 일반 생성 멱등성·다른 결과 확인/유일 Master 분실·DISABLED 복구 등 남은 한계를 운영 기능으로 숨기지 않는다. 최종 호스팅·운영 담당 실명·법적 보존기간은 개발 착수 조건으로 요구하지 않지만 해당 기능/운영을 앞당기면 관련 결정을 선행한다.

### 이번 기술 자료 확인 범위

공식 자료를 다시 확인했다. 아래는 선택 근거이며 설치·성능·보안 시험 결과가 아니다. 기존 초안의 release 버전 관찰은 이 작업에서 최신 버전으로 재확인하거나 lock에 반영하지 않았다.

- [FastAPI 보안 안내](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/): pwdlib/Argon2 해시 예시를 후보 근거로 사용. 예시 JWT 방식까지 채택하지 않음.
- [NIST 비밀번호 지침](https://pages.nist.gov/800-63-4/sp800-63b.html): 길이·차단목록·정규화 검토 참고. 이 서비스의 정책 승인/준수 인증 아님.
- [PostgreSQL 17 명시적 잠금](https://www.postgresql.org/docs/17/explicit-locking.html): SHARE와 UPDATE 충돌·일관된 잠금 순서 검토. 위 애플리케이션 경합 계약의 실행 증명 아님.
- [OWASP CSRF](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html): 서버 결합 token과 출처 검증 참고. 실제 브라우저 동작은 B1에서 증명.

### 이번 문서 검증 결과

2026-09-18 재검토에서 시작 상태(main/기준 HEAD, README unstaged 및 설계·ADR untracked, staged 없음)를 재확인했다. 시작 시 저장소 tracked/untracked 68개 파일 해시와 기존 세 문서 원문을 별도 임시 위치에 보관해 비교했다. 변경은 허용된 기존 세 문서뿐이며 신규 문서는 이 결정안 하나다. backend/전체·Product·AGENTS.md·ACCEPTED ADR-0001~0003·Foundation/WSL 과거 기록·dependency/lockfile은 그대로다. 기존 미커밋 변경 위의 증분 diff로 의미를 검토했으며 reset/checkout/clean/revert/commit/push는 하지 않았다.

네 문서의 로컬 링크/앵커 61개, 명시적 Product/기술 참조 ID 31개의 존재와 Markdown 표 열 수를 검사했고 오류가 없었다. tracked diff의 `git diff --check` 및 untracked 포함 공백 검사를 수행했다. 12개 흐름의 S1 포함 사유, D 질문의 기존 게이트/시점, S2/운영 경계, 준비·인가·철회·감사·migration/브라우저 검사 연결을 문서로 대조했다. 새 파일은 일반 git diff 통계에 나오지 않으므로 파일 해시·원문 비교를 병행했다. 앱·테스트·migration·패키지 설치·fast/db·브라우저 검사는 실행하지 않았다. 이 문서 검증은 인증 보안/운영 검증의 통과가 아니다.

2026-10-12 K3 반영: 첫 관리자 기능/개발 검증과 후속 복구/추가 Master/Trainer 연결의 순서 선택은 완료됐다. D02/D07의 구체 소유권/공유 UoW/잠금·상태/진입점은 후속 기술 검토이며 해당 문서 PROPOSED를 일괄 ACCEPTED로 바꾸지 않는다. 별도 코드 작성 지시·기존 실제 기록/보존/해당 운영 게이트를 유지한다. 이번 변경은 문서 반영이며 새 해시/브라우저/DB 실험·업무 검사·migration 실행은 없다. [2026-10-12 K 일괄 승인](../product/product-decisions.md#review-20261012-k-batch).

AB3–AB6 후속 경계: reset30분·운영 관리자 비밀번호+Passkey/업무책임자 승인·별도 시스템 운영담당자 비상 복구·Chrome/Edge/Safari 최신2개 안정 주버전은 선택됐다. 현재 S1에 reset/MFA/비상명령·전브라우저 운영 인수를 선행 구현하지 않는다. 실제 등록/분실/복구·자격/감사/본인확인·보존/운영·매트릭스/실제 검증은 남는다. [AB 승인](../product/product-decisions.md#review-20261013-ab-batch); V-134–137 미구성·미실행.

<a id="review-20261013-x1-proposal"></a>
## 8. 2026-10-13 재검토 — 발급 응답 유실의 복구 후보 X1

상태: **X1=1 기능 보완 승인 / 구체 계약 PROPOSED**. 아래 비교표는 승인 전 제안 이력이며 W1/W2가 아닌 후속 사용자 답변 “1”로 X1을 선택했다. Master 자기 Organization Branch Admin의 정확한 Login ID 발급 결과 조회/설정 대기 링크 재발급을 S1에 포함한다. API/필드·모듈/UoW/잠금 상세 일괄 채택이나 코드/migration 지시는 아니다. [승인 근거](../product/product-decisions.md#review-20261013-x-batch).

승인 전 확인한 공백: 당시 §4 초안은 발급 응답으로 받은 account ID를 통해서만 조회하도록 제안했다. DB에서 Branch Admin 계정 발급이 commit됐어도 클라이언트가 응답을 잃으면 account ID와 최초 설정 링크를 모두 받지 못할 수 있다. 이때 기존 §4/§7 초안은 해당 개발 run 중단/S2 보완을 제안했다. 같은 Login ID로 다시 발급하면 중복으로 거부될 수 있고, 응답 유실을 DB 실패로 간주하거나 원래 토큰을 조회하는 방법은 해결책이 아니다. 최초 Master 암호 분실/복구 문제와는 별개다.

| 선택 항목 | 1번 추천안 | 2번 기존 초안 유지 | 이유/영향 |
| --- | --- | --- | --- |
| X1 — Branch Admin 발급 응답 유실 복구 | S1에 Master의 자기 조직 Branch Admin 정확한 Login ID 조회를 추가해 ID/현재 상태를 확인하고, 설정 대기 상태이면 기존 절차로 새 설정 링크 발급 | S1은 ID를 못 받으면 개발 검증을 중단하고 결과 재조회 보완을 후속으로 미룸 | 1번은 일반적인 응답 유실에서 검증 흐름을 복구할 수 있으나 최소 조회 계약/인가/실패·경합 검사가 늘어난다. 2번은 최초 구현 범위가 더 작지만 발급 결과 확인 경로 부재를 인수·사용 한계로 유지한다 |

### X1=1 기능 보완에 대응하는 구체 계약 후보

API 이름/필드는 기술 제안이다. 기존 계정 관리 역할을 Branch Admin에게 위임하거나 계정 목록/부분 검색·추가 Master/Operator/Trainer 계정 관리·암호 재설정을 추가하지 않는다.

| 단계 | 계약 후보 | 경계 |
| --- | --- | --- |
| 정확한 발급 결과 조회 | `POST /admin/accounts/lookup`에 `{login_id}`와 유효 AuthSession/CSRF. 현재 Master가 자기 Organization의 S1 Branch Admin 계정만 정확한 ID 비교로 조회. 응답은 `account_id,login_id,state,admin_scope,version` | Login ID의 승인된 대소문자 미구별을 적용하며 부분 검색/목록/다른 조직 응답은 없음. 조직은 Caller에서 결정. 원래 설정 token/암호 hash·다른 역할/개인정보는 반환하지 않음. raw 입력을 URL/일반 로그·오류에 남기지 않음 |
| 조회 결과 대조 | Master가 의도한 Login ID/관리 Branch·현재 상태를 확인. 조회 자체는 계정/Scope·인증 상태/설정 링크를 변경하지 않음 | 같은 Login ID 결과가 있다는 사실만으로 직전 발급 시도의 성공을 증명했다고 단정하지 않음. 과거 조회/발급 권한으로 현재 요청을 승인하지 않음 |
| 설정 대기 링크 재발급 | 확인된 account ID와 최신 version으로 기존 `POST /admin/accounts/{id}/activation` 실행. 새 30분 단일 사용 링크, 이전 설정 token 폐기·version 증가·감사 원자 반영 | 현재 Master/자기 조직/대상 PENDING_SETUP을 다시 검사. ACTIVE/DISABLED·Master·version 충돌은 기존 오류로 거부하고 암호 reset/강제 상태 변경으로 우회하지 않음. 새 token은 성공 응답에서 한 번만 전달, 원문 사후 조회 없음 |
| 다시 응답을 잃은 경우 | 정확한 조회로 현재 상태/version 재확인 후 허용 상태에서만 명시적 재발급 | 숨은 자동 반복 발급·성공/rollback 단정 없음. 재발급 실패/감사 실패 시 이전 상태와 기존 유효 token을 유지. commit 결과 불명확은 결과 재확인 전 실패 확정으로 처리하지 않음 |

조회 인가 후보: 보호 요청 공통 401, 현재 Master가 아닌 역할은 403, 자기 Organization의 대상 Branch Admin이 없거나 범위 밖이면 같은 scoped 404, DB 장애는 안전한 503. HTTP 경로/요청 모델의 매칭과 최소 응답은 구현 전 기술 검토 대상이다. 조회가 404라고 진행 중 commit의 부재/rollback을 증명한 것은 아니므로 미확인 발급을 자동 재시도하지 않는다. 기존 Login ID 유일성·현재/예약 ID 정책과 생성 중복 방어는 유지한다. 이미 account ID가 있는 경우 기존 ID 조회 경로도 유지한다.

모듈/트랜잭션 후보: 조회는 IAM 소유의 계정/Scope 공개 읽기 계약으로 제공한다. 같은 UoW에서 Account/AuthSession 현재 상태·Role/Scope를 확인하고 scoped 조회/DTO를 구성하며, 관리 쓰기는 기존 InstallationControl → 정렬된 Account → AuthSession → 설정 행 순서를 처음부터 따른다. 일반 읽기 인증 잠금을 먼저 획득한 뒤 관리 쓰기 경로로 승격하지 않는다. 링크 재발급/동시 활성화·차단/Scope 변경은 기존 상태/version 재검사와 감사 원자성을 유지한다. 다른 모듈 Repository/ORM/DB 직접 읽기 예외를 추가하지 않는다. 구체 소유권/공개 계약·UoW/잠금은 PROPOSED다.

인수 추가 후보(모두 미구성·미실행): 실제 PostgreSQL에서 정상 발급 commit 이후 응답만 버림 → 동일 Master가 정확한 Login ID로 ID/상태 대조 → 새 링크 재발급 → 이전 링크 거부/새 링크 최초 설정 → Branch Admin 실제 로그인/허용 지점 조회. 중복 계정 없음, 다른 조직/비Master/부분 검색·원문 token 조회 거부, 조회와 활성화/차단/관리 Scope 변경 경합·오래된 version·감사 실패 rollback·재발급 응답 유실도 검사한다. 이 경로는 Bootstrap 재실행/DB 초기화/고정 fixture 계정으로 대체하지 않는다.

선택 반영: X1=1로 §4의 정확한 조회/설정 대기 재발급·§6 P2/C1 인수·§7 잔여 설명과 원본 IAM 설계를 맞췄다. 2번의 발급 ID 미확보만으로 S1 중단/S2 재조회 보완은 선택하지 않았다. 기능 보완/인가 범위 승인과 위 API/필드·소유권/공개 계약/UoW/잠금 PROPOSED를 구별한다. V-126은 미구성·미실행이며 K3 첫 흐름/후속 분리·ADR-0004/나머지 Product OPEN/기존 정책과 별도 구현 지시 경계를 유지한다. 실제 계정·개인정보/비밀·운영 DB는 사용하지 않았다.


<a id="review-20261013-s1-contracts"></a>
## 9. S1 기술계약 재검토 — 2026-10-13

상태: **PROPOSED — 설계자가 구체화한 S1 검토/구현 인계안; AB 정책 승인과 코드 구현 승인 아님**. K3/X1 관리자 인증/지점 접근 제어에 한정한다. 모듈 경계 전체/후속 Workforce·PT·Settlement/운영 MFA·복구를 일괄 채택하지 않는다. §4/§5의 현재 후보도 이 구체화에 맞췄고 아래 TX01–TX06을 한 묶음으로 검토한다.

| 계약 | 구체안 | 인수에서 확인할 것 |
| --- | --- | --- |
| TX01 소유권/공개 경계 | IAM은 계정·역할/관리Scope·인증/설정/제한 상태, Organization은 조직/지점, Audit은 허용된 감사사건의 쓰기 소유자. Application Use Case가 공개 계약만 조정 | 타 모듈 Repository/ORM/DB 직접 읽기 예외0건. 공개 DTO에 FastAPI Request/SQLAlchemy DBSession·ORM/비밀번호 hash 없음. 업무 모듈이 Cookie를 읽지 않음 |
| TX02 하나의 업무 트랜잭션 | Use Case 내부에서 DBSession/UoW를 시작하고 같은 DBSession으로 module-private adapter를 구성. 공개 계약에는 DBSession을 전달하지 않음. 필수 상태/철회/감사는 Application이 한 번 commit, 오류 시 전부 rollback | 기존 `Database.session()`은 수명만 제공하므로 자동commit으로 오해하지 않음. 요청 공통 dependency는 factory만 제공하고 DB 인증/잠금을 선행하지 않음 |
| TX03 두 버전의 의미 분리 | `row_version`은 target 변경 충돌 검사/API `version`·`expected_version`; `security_version`은 AuthSession에 결합한 인증 철회 epoch. 인증 활동 갱신/일반 logout은 Account 버전을 바꾸지 않음 | 단순 로그인이 관리자 화면의 target version을 바꾸지 않음. status/access는 target 버전 두 개 증가/전 인증 철회. no-op·실행자 버전/인증은 유지 |
| TX04 경로별 잠금 순서 | READ COMMITTED. 관리 경로는 InstallationControl→Account ID 순→AuthSession ID 순→준비/설정→Branch 사실→Audit. 읽기는 Account SHARE→AuthSession UPDATE. 모든 인가/현재 Scope는 잠금 후 재검사 | 읽기 인증 잠금을 먼저 잡은 뒤 관리 잠금으로 승격하지 않음. 늦게 도착한 응답과 변경 후 새 인가를 구별. 독립 PostgreSQL 연결/worker barrier로 선후를 증명 |
| TX05 설정 링크/CSRF/실패 비노출 | 발급 응답은 `setup_link`를 한 번 제공. 서버가 신뢰한 origin으로 링크를 만들고 token은 fragment에 둠. GET으로 소비하지 않고 페이지가 fragment를 지운 뒤 준비 CSRF와 설정 POST. 원래 링크/token 재조회 없음 | `setup_token`은 설정 완료 POST 내부 입력에만 사용. 비밀 로그/Referer/분석/캐시 금지. X1 재조회에는 링크 없음. 기존 없는ID/차단/설정대기/오입력 일반오류·제한 비노출 유지 |
| TX06 패키지/검증 경계 | 기존 main/application/config/database 유지, 필요한 iam/organization/audit 및 use_cases·UoW 구성만 추가하는 패키지 후보. HTTP 조립과 Application Use Case 이름/책임을 구별 | 기존 exhaustive import 검사를 제거하지 않고 새 경계로 확장. domain/public은 HTTP/ORM 비의존, 다른 모듈 내부 import 금지. U1/P1/P2/C1/B1/B2·fast/db 완료를 실제 증거로 구별 |

버전 상세: S1의 외부 `version`은 Account `row_version`이다. 발급 초기 두 버전은 양수로 시작한다. PENDING_SETUP 링크 재발급은 row_version을 올리고 이전 요청을 폐기하며 새 설정 요청을 해당 row_version에 결합한다. 설정 완료는 동일 최신 요청/상태를 재검사하고 암호·ACTIVE·row/security_version·token 소비/감사를 함께 반영한다. ACTIVE 차단/관리 Branch 변경은 target의 두 버전을 올리고 대상 기존 인증/설정 요청을 폐기한다. AuthSession의 생성/last activity/현재 logout은 Account row/security_version을 올리지 않는다. 무변경 access는 expected_version 일치 확인 후 무변경으로 수렴한다. 미래 Operator/Trainer 역할 변경에 자동 전체 logout을 일반화하지 않으며 그 증분의 승인 정책/별도 계약을 따른다.

실행자/대상: 지점 생성·Branch Admin 발급/설정 링크 재발급을 수행했다는 이유로 Master 자신의 로그인/권한 버전을 바꾸지 않는다. actor 인증은 현재 상태/Scope/CSRF 검증 대상이고, 명령의 인증 철회 효과는 명시된 target에만 적용한다. S1에는 Master 자체 차단/Scope 변경이 없으므로 actor=금지 target인 요청은 기존 상태/권한 계약으로 거부한다. 감사 실패 시 지점/계정/링크/대상 version·철회를 함께 rollback한다.

자원/인가 시점: 동기 Use Case 전체를 한 worker 실행 안에서 호출하고 그 안에서 DBSession을 열고 닫는다. sync DB 작업을 async handler에 직접 넣거나 열린 DBSession/Caller를 다른 thread/background 작업에 넘기지 않는다. 로그인 비밀번호 검증은 쓰기 잠금 밖에서 수행하며 IAM 내부 검증 snapshot/결과를 공개 Caller/응답/로그에 hash로 노출하지 않는다. 이후 발급 UoW에서 최신 상태/security_version·검증한 자격이 여전히 유효한지 재검사한다. 잠금 없는 식별자 탐색은 UoW 내부의 힌트일 뿐 인가가 아니며 ORM cache를 최신 사실처럼 재사용하지 않는다. scoped DTO를 구성한 뒤 commit/close하고 외부 응답 전송까지 DB 잠금을 붙잡지 않는다.

제한/오류 비노출: C2의 계정5회/15분 실패·15분 대기는 정규화된 제출 Login ID의 keyed digest를 기준으로 존재 여부와 관계없이 같은 경로에 적용하는 후보로 구체화한다. 없는 ID만401을 계속 내고 실제 계정만429로 바꾸는 누출을 만들지 않는다. HTTP 상태/본문/Retry-After의 존재 여부 차이를 검증하며 더미 해시는 시간 차이를 줄이는 수단이지 완전한 시간 동일성 보장이 아니다. 실패 예산/사건은 별도 짧은 보안 transaction으로 유지하고 업무 UoW와 bucket 잠금을 동시에 유지하지 않는다. 원자적 예약/실패 창·진행중/장애 처리·IP/NAT/해시 자원 상한은 T-05 사전검증에서 구체화하며 임의 실패 초기화/무제한 fallback을 넣지 않는다.

링크/브라우저: `setup_link`는 설정된 canonical HTTPS origin으로 조립하며 임의 Host/forwarded 헤더/클라이언트 origin을 신뢰하지 않는다. 형식 후보는 `https://<configured-origin>/activate#token=<one-time-token>`이고 실제 주소/값은 예시로 수집하지 않는다. 서버 응답은 no-store이며 링크 페이지는 외부 script/분석 없이 fragment를 메모리로 옮기고 주소에서 제거한 후 준비 CSRF·동일 출처 설정 POST를 수행한다. 최초 링크30분/단일사용·재발급 폐기·자동로그인 없음·X1 복구는 유지한다. AuthSession 식별자는 기존 `__Host-y3-auth` HttpOnly Cookie만 사용하고 CSRF nonce/설정 token과 구별한다. S1 브라우저 인수는 같은 origin HTTPS로 고정한다. D11의 plain HTTP opt-in은 아직 비교 후보이며 이번 S1 구현 지시안에 포함하지 않는다. 운영 도메인/프록시/TLS·후속 reset/Passkey·전 지원 브라우저 인수는 관련 운영 게이트를 따른다.

패키지/어댑터: `application.py`의 기존 create_app/health 조립 계약을 유지하고 업무 조정은 별도 use_cases 후보로 둔다. 각 모듈의 public은 불변 값/명령·결과·검증된 Caller 계약, application은 모듈 업무, domain은 순수 규칙, infrastructure는 ORM/Repository 구현으로 구분한다. UoW 구성 지점만 같은 DBSession으로 각 private adapter를 조립하며 다른 모듈은 public 계약에만 의존한다. 전체 모듈의 빈 패키지를 미리 만들지 않고 import 검사에 명시적인 경계/불허 의존성을 추가한다. 실제 패키지/Import Linter 설정의 적합성은 구현 검증 대상이며 지금 구성됐다고 주장하지 않는다.

확인 근거: 현재 source의 `Database.session()`은 자동commit하지 않고, Import Linter는 main/application/database/config 네 계층 exhaustive, Alembic target_metadata는 None이고 업무 revision은 없다. [SQLAlchemy2.0 Session](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)은 DBSession의 동시 사용/수명을 확인하는 근거, [PostgreSQL17 잠금](https://www.postgresql.org/docs/17/explicit-locking.html)은 잠금 충돌/일관된 순서의 근거다. [OWASP Authentication](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)은 본문뿐 아니라 HTTP 상태 차이도 계정 구별을 만들 수 있음을 뒷받침한다. 두 버전/공개 계약·제한 key/링크 형식은 승인 정책을 만족시키기 위해 설계자가 제안한 구체안이며 출처 문서가 이 애플리케이션의 실행 정확성을 보증하지 않는다.

남은 사전검증: 해시 후보/비용·차단목록의 긴/Unicode·한국어 및 서비스 문맥 적합성/출처·배포/무결성, 실패 제한 원자성/자원 상한, 실제 HTTPS 전달/CSRF, 새 import/공유UoW/행 잠금·schema 제약은 아직 증명하지 않았다. 기존 preflight100k 목록의 긴 암호72개만으로 공급 적합성을 완료 처리하지 않는다. Foundation36/PG3/이전 임시probe는 새 S1 인수가 아니다. 단위·실제PostgreSQL·독립worker·실브라우저 검증 전 완료/운영 허용을 보고하지 않는다. V-138은 미구성·미실행 계획이다. 정책/관측 결과·운영 기능 범위를 바꿔야 할 때는 새 근거/영향을 묶어 사용자 확인하며 기술 세부마다 질문하지 않는다.

<a id="s1-implementation-handoff-20261013"></a>
## 10. 개발 담당자 전달안 — 2026-10-13 조건부 착수 승인

상태: **AUTHORIZED / PREP-IAM-001 통과 후 S1a→S1b 구현**. 2026-10-13 사용자가 이 전달 범위의 착수를 명시 승인했다. 사전검증 미해결 우회·승인 정책 임의 변경은 위임하지 않았다. 실제 전달·선행 검토·구현·독립 검사 결과는 별도 보고 근거로 확인한다.

1. Git/AGENTS·Product/ADR/현재 S1 문서를 확인하고 기존 dirty 문서/HEAD/index·운영 데이터/비밀을 보존한다. 기준 HEAD만 checkout해 최신 미커밋 정책 문서를 잃지 않는다. 앱 코드 변경은 이 작업지시의 착수 승인 후에만 시작한다.
2. **PREP-IAM-001 선행:** 기존 고정 버전/원본 .venv/lockfile을 바꾸지 않는 작업 소유 영역에서 T-05 미해결 공급/호환성·부하/제한·브라우저 기술 근거를 검증한다. 실제 corpus/라이선스/고정 출처·checksum/분포/알려진 약암호·정규화/오탐/서비스 문맥/갱신 근거를 제시한다. 작은 실험 목록·임의 문자열만으로 완료 처리하지 않는다. 자원/품질을 만족시키지 못하면 미해결 상태와 구체 대안을 보고하며 게이트를 우회해 앱 인증을 구현하지 않는다.
3. 선행 근거 검토/게이트 충족 뒤 **IAM-S1a → IAM-S1b**로 §4 CLI/API와 §9 TX01–TX06을 구현한다. 최초 계정 준비→실제 로그인/현재 Scope→Master 지점/Branch Admin 준비·링크 설정/유실 복구→허용 조회/타 지점 직접ID 차단→logout, 이어 차단/Scope 변경·철회/경합을 검증한다. S1a는 중간 인수이며 S1 완료가 아니다.
4. 필요한 IAM/Organization/Audit/UoW 및 첫 업무 migration·의미 있는 U1/P1/P2/C1/B1/B2 검사/안내만 추가한다. repo별 commit·request 선행 DB 인증 잠금·소유 모듈 우회·원래 token 조회·App startup create_all/자동migration은 금지한다. Dependency 추가/정확한 잠금은 선행 후보 검증을 근거로 하며 기존 의존성의 자동upgrade는 하지 않는다.
5. 소유권 확인한 전용 Compose/PostgreSQL에서 migration/제약·rollback/감사·독립 연결/worker 경합·실제 HTTPS 브라우저를 검사하고 `bash check.sh fast`/`bash check.sh db`를 실행한다. 필수DB의 설정누락/skip/xfail/미수집을 성공 처리하지 않는다. 기반 검사를 새 IAM/전체 v1 완료로 확대하지 않는다.
6. 보고에는 시작/종료 Git 상태·정확한 변경 범위/계약·검사 명령/결과·실패/경고·미검증/남은 게이트와 비밀 없는 증거를 포함한다. 설계자가 결과/diff/검증을 검토해 이상이 있으면 재지시한다. commit/push·Product OPEN 임의CLOSED/ADR 임의ACCEPTED·기존 변경 삭제/회원/PT/정산/후속reset/MFA·비상복구 구현은 이번 S1 작업 범위가 아니다.

검토 순서: 승인된 정책 반영과 구체 기술계약의 제안 상태를 구별한 뒤 이 전달 범위의 구현 착수 여부를 확인한다. 전달안 승인만으로 사전검증 미해결을 성공 처리하거나 운영 허용을 선언하지 않는다. 실제 전달/구현·추가 패키지 설치/DB·브라우저 실행은 이번 문서 검토에서 하지 않았다.
