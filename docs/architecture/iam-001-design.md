# IAM-001 — 로그인한 관리자의 지점 접근 제어

2026-10-16 MFA 후속 부분 승인: [M1/M2](../product/product-decisions.md#review-20261016-mfa-m-batch)로 관리자 복수 Passkey 등록/로그인 시 하나 사용과, 같은 Organization의 다른 정상 Master에 의한 본인 확인·관리자 기존 Passkey/모든 AuthSession 폐기·일회용 링크 재등록을 확정했다. AB4 추가 인증/AB5 전체 Master 로그인 불가 비상 복구를 유지하며 비밀번호 reset·차단 해제·역할 복원을 자동 포함하지 않는다. 아래 미결정/PROPOSED 중 이 승인 부분만 대체하며 추가 등록/삭제·마지막 인증수단 보호·구체 API/상태/수명·원자성/경합·실제 검증은 후속이다.

2026-10-13 최신 인수: **IAM S1a/S1b 개발 인수 PASS**. 현재 구현·실행 증거는 [S1 결과](iam-001-s1-results.md), 범위와 한계는 [설계자 판정](iam-001-s1-review.json)을 따른다. 아래 설계 작성 당시의 미구현/미검증·인수 대기 기록은 당시 이력이다. 이번 인수는 K3/X1·§12의 좁은 첫 증분이며 S2·Trainer/Operator 연결·운영 MFA/복구·전체 설계의 일괄 승격을 포함하지 않는다.

2026-10-13 최신 지시: **PREP-IAM-001 통과를 조건으로 IAM-S1a→S1b 구현 착수 승인**. 사용자가 개발 담당자에게 지시하고 별도 `테스트노예` 세션으로 검사한 뒤 설계자가 검토·재지시하도록 요청했다. [전달안](iam-001-decision-pack.md#s1-implementation-handoff-20261013)/TX01–TX06을 이번 S1 작업 기준으로 삼으며 전체 모듈 설계의 ACCEPTED 승격·후속 기능·운영 허용은 포함하지 않는다. 아래 구현 승인 대기 문구는 이 지시 전 상태다. 사전검증과 구현·인수 완료는 아직 보고하지 않는다.

최신 범위/정책: [2026-10-13 AB 승인](../product/product-decisions.md#review-20261013-ab-batch)으로 후속 reset30분·운영 관리자 비밀번호+사용자검증 Passkey·업무책임자 승인/별도 운영담당자 비상 복구와 지원 브라우저 목표가 확정됐다. K3/X1 첫 IAM S1 범위/개발 순서·구체 계약 PROPOSED·별도 구현 지시를 유지한다. AB 정책 승인으로 아래 기술계약 전체를 채택하지 않는다.

2026-10-12 후속 승인 반영: [2026-10-12 일괄 승인](../product/product-decisions.md#review-20261012-batch)을 현재 정책으로 사용한다. 인증 방식은 ADR-0004 ACCEPTED(v1 PG AuthSession+opaque Cookie), JWT는 후속 재검토 후 별도 결정이다. 최초 설정 링크 30분/단일 사용·재발급 이전 폐기, 모든 역할 idle 30분/absolute 8시간, 독립 복수 기기/일반 logout 현재 로그인만 종료, 관리 역할/관리 Branch 변경 전체 재로그인, Master 전용 계정 차단/복구·관리자 reset, 복수 Master/마지막 사용 가능 Master 보호, 운영 전 관리자 MFA는 확정이다. 이전 설계 수치/게이트 중 이 부분만 대체하며 라이브러리·구체 Caller/DB/UoW/잠금·S1/S2 범위·최근 재인증/실패 제한/기록 보존은 일괄 승인하지 않는다. Trainer 업무 비활성화/재활성화와 전체 계정 차단을 구분하고 B1/B2를 따른다. 실제 코드/검사/migration 변경·실행은 없다.

Status: **S1a/S1b 개발 인수 PASS — 2026-10-13**. [현재 S1 계약](iam-001-decision-pack.md), [PREP 판정](prep-iam-001-review.json), [S1 판정](iam-001-s1-review.json)을 따른다. 전체 설계의 PROPOSED/후속·운영 게이트는 유지한다.

작성/근거 확인일: 2026-09-18. 기준 커밋: `b83defe3fc564b56d0f77cb075ddb5436759d191`.

현재 개발환경은 Windows 호스트 위 WSL Ubuntu다. [WSL 검증 기록](wsl-migration.md)의 빠른 검사와 실제 PostgreSQL 기반 검사는 완료됐지만, IAM 기능·업무 schema migration·지급 계산/업무 동시성·운영 배포는 검증하지 않았다. 이 문서는 첫 업무 기능의 제안이며 코드, 의존성 변경, migration 또는 운영 구성을 제공하지 않는다. 아래 API·명령·데이터 이름은 모두 아직 존재하지 않는 초안이다.

## 1. 근거와 승인 경계

[Product 기준](../product/README.md), [역할표](../product/users-and-roles.md), [OPEN](../product/open-questions.md), [결정 게이트](decision-gates.md), [모듈 경계](module-boundaries.md), [트랜잭션 초안](data-and-transactions.md), [검증 계획](validation-plan.md)을 입력으로 사용했다. AS-IS 계정과 C# 구현은 인증 정책의 정답으로 사용하지 않는다.

| 이미 확정된 내용 — 다시 승인받을 대상 아님 | 실제 근거 |
| --- | --- |
| Python/FastAPI/SQLAlchemy/Alembic/PostgreSQL, 단일 백엔드의 모듈 경계 관리, 동기 SQLAlchemy/psycopg 3와 uv 기반 | [ADR-0001](../decisions/0001-backend-stack.md), [ADR-0002](../decisions/0002-modular-monolith.md), [ADR-0003](../decisions/0003-foundation-tooling.md) ACCEPTED |
| 관리자 발급 계정, Master의 Branch Admin 및 계정/권한 관리, 기존 계정·암호 이관 없음 | [PR-001](../product/requirements.md#pr-001), [PR-021](../product/requirements.md#pr-021), [PD-019](../product/product-decisions.md#pd-019) |
| 하나의 Organization, 여러 Branch; Master는 Organization 전체, Branch Admin은 단일 관리 Branch | [PR-020](../product/requirements.md#pr-020), [PR-030](../product/requirements.md#pr-030), 역할표 |
| Trainer 직접 로그인은 v1, 모바일 브라우저 핵심 업무 지원. Member 로그인과 별도 Mobile App은 Future | [PR-029](../product/requirements.md#pr-029), [NFR-001/008](../product/non-functional-requirements.md), [SC-003](../product/user-scenarios.md#sc-003) |
| 계정/권한 및 중요 지점 변경 감사, 서버에서 목록·상세 모두 Scope 제한 | [PR-027](../product/requirements.md#pr-027), PR-030, [NFR-004/005](../product/non-functional-requirements.md) |
| Master 본인 포함 전체 및 Branch Admin 본인 포함 관리 Branch가 Home Branch인 Trainer만 설정 접근 허용. 관리자 권한 없는 Operator/Trainer는 본인 포함 불가 | [BR-PAY-010](../product/business-rules.md#br-pay-010), 역할표. 보상 설정 변경의 별도 Master 승인 불필요는 계정 발급 위임을 뜻하지 않음 |
| 빈 업무 데이터에서 초기 Master·조직·지점·계정을 새로 준비 | [PR-028](../product/requirements.md#pr-028), [SC-001](../product/user-scenarios.md#sc-001) |

초기 계정·재설정·중단·만료·마지막 Master는 **ARCH-002 OPEN**, 역할 기술 표현과 세부 인가는 **ARCH-001 OPEN**, Branch Admin의 계정 위임은 **MB-004 OPEN**이다. 새 Product 질문 ID를 만들거나 기존 상태를 닫지 않는다. 인증 선택은 T-05 및 [ADR-0004 v1 인증 채택](../decisions/0004-authentication-session.md), IAM/Organization 계약은 T-01, 인증 경합은 T-09의 이번 기능 부분만 검토한다. 전체 6개 모듈은 계속 PROPOSED다.

## 2. 첫 증분과 전체 IAM-001의 분리

첫 구현은 [결정안의 S1](iam-001-decision-pack.md)으로 좁힌다. S1은 영속 PostgreSQL 기반 서비스의 첫 기능 증분이며 가상 데이터·24시간·영역 폐기는 별도 실험/인수 하네스 실행 관리 후보다. 제품 수명/삭제 기본값으로 넣지 않는다. **실제 Bootstrap·로그인·Branch Admin 발급/본인 설정·지점 조회·로그아웃·차단/관리 지점 변경·감사 원자성**을 제한된 개발 환경에서 검증한다. 재설정/본인 암호·Login ID 변경·복구·추가 Master·Master 승강격의 구현은 S2 후보로 분리한다. C1의 중요 관리 추가 비밀번호 재인증은 제공하지 않는다. K3으로 관리자 인증/지점 접근 제어의 첫 개발 검증과 후속 분리는 선택됐다. 구체 준비/발급·상태/API/계약/UoW/잠금은 계속 제안이며 구현 착수 승인이 아니다.

| 구분 | 포함 범위 | 완료 보고 경계 |
| --- | --- | --- |
| S1 첫 Vertical Slice | 일회성 로컬 Bootstrap, 실제 로그인/현재 Scope, Master의 지점 생성·Branch Admin 발급, X1 정확한 Login ID 발급 결과 조회·본인 활성화/미활성 token 재발급, 목록/상세 인가, logout·ACTIVE Branch Admin 차단·같은 조직 관리 지점 변경 | 결정안의 실제 PostgreSQL·독립 worker 경합·HTTPS 브라우저 포함 인수 완료 필요. 운영 허용 아님 |
| S1a / S1b 분할 가능 | S1a는 준비→로그인→Scope 조회→logout, S1b는 차단·Scope 변경과 철회 경합 | S1a는 중간 인수이며 S1 완료 아님. 전체 12개 흐름 기준 유지 |
| S2 계정 수명 후속 | 복구·암호 재설정/본인 변경·Login ID 변경, 추가 Master·마지막 Master 보호, Master 전이 | 관련 F 결정과 원래 전체 인수 사례까지 충족해야 관리자 IAM-001 전체 완료 |
| 운영 진입 | 운영 전달·MFA/비상복구·보존/삭제·배포/품질 | S1/S2 구현과 별도 게이트. 실사용·상시 수집은 개발 예외로 허용하지 않음 |

이하 3~9절은 **전체 IAM-001의 상세 후보/비교 자료**를 보존한다. 그 안의 “이번/첫 증분”, 재설정 목적·추가 Master API·수치/보존 제안은 모두 S1 구현 목록을 뜻하지 않는다. 첫 구현의 포함/제외·축소 API·결정 시점은 [결정안](iam-001-decision-pack.md)이 구체화한다. 특히 S1은 Branch Admin만 발급하고 ACTIVE→DISABLED와 ACTIVE의 Branch A→B만 관리한다. C1에 따라 중요 계정 관리에 최근 비밀번호 확인이나 이를 위한 강제 재로그인/별도 재인증을 요구하지 않는다.

**Trainer 구현 순서:** 인증 Use Case는 관리자라는 이유로만 로그인 성공을 허용하는 구조를 만들지 않는다. 계정 인증과 관리자 지점 열람 권한을 분리한다. 이 증분의 발급 API는 관리자 계정부터 제공하고, 후속 v1 증분에서 Master의 Trainer 계정 발급과 Workforce의 실제 Trainer 연결을 추가한다. IAM이 계정 연결을 소유하고 Workforce가 Trainer/Home Branch를 소유한다. 연결 검증은 상위 Application이 두 공개 계약을 조정하며 가짜 Trainer/빈 Workforce 테이블을 만들지 않는다. 그때 실제 Trainer 로그인·본인 조회까지 검증해야 v1 Trainer 인증 완료다. 이번 비관리자 인가 fixture만으로 완료 처리하지 않는다. Operator의 발급/업무 Scope는 MB-004/ARCH-001 해소 후 다룬다.

PTSession 등록, Pass 차감, 지급 계산, 추가실적, 월 정산, 회원 데이터, 예약은 범위 밖이다. 관리 지점 조회 권한을 모든 지점 업무 데이터·정산·보상정보 조회 권한으로 재사용하지 않는다.

2026-10-12 K3 범위/순서 승인: 첫 증분과 후속 복구/추가 Master/Trainer 연결의 분리는 다시 미결정으로 취급하지 않는다. 관리자 인증 성공·현재 Scope·지점 접근/직접 ID 차단·logout/차단·Scope 변경 반영을 개발 검증하는 순서를 선택했으며 구체 상태/API·모듈 소유권/Caller·UoW/잠금·인수 상세는 PROPOSED다. v1 Trainer 직접 로그인/실제 Workforce 연결·운영 전 MFA/비상 복구 검증 의무와 별도 코드 작성 지시는 유지한다. [2026-10-12 K 일괄 승인](../product/product-decisions.md#review-20261012-k-batch).

## 3. 인증 후보 비교와 추천

쿠키는 브라우저의 전달·저장 수단이고 JWT는 토큰 형식이다. JWT도 쿠키로 전달할 수 있고, 서버 저장 상태의 무작위 토큰도 Authorization 헤더로 전달할 수 있다. 비교 대상은 **서버 조회로 유효성을 판단하는 로그인 상태**와 **서명된 access JWT를 주로 로컬 검증하는 상태**다.

| 쟁점 | 추천: PostgreSQL AuthSession + 무작위 쿠키 | 대안: 짧은 access JWT + 갱신/철회 저장소 |
| --- | --- | --- |
| 로그아웃·계정 차단 | DB 폐기/계정 상태를 새 요청에서 확인. 쿠키 삭제와 서버 폐기는 둘 다 필요 | 브라우저 토큰 삭제만으로 복사본을 철회하지 못함. 즉시 철회는 denylist/계정 버전 조회 등이 필요 |
| 권한 변경 | 매 요청 현재 계정/Scope 확인, 기존 상태 전부 무효화 후 재로그인 추천 | claim의 권한은 발급 당시 값. 짧은 만료까지 허용할지 매번 버전을 조회할지 결정 필요 |
| 비용·장애 | 요청마다 PostgreSQL 조회 및 활동 시각 갱신 비용. DB 장애 시 인증 실패로 닫음 | 서명 검증 비용/키 배포. refresh 회전·재사용 탐지·철회 DB까지 넣으면 완전 무상태가 아님 |
| 앱 재시작·다중 worker | 같은 DB와 설정을 사용하므로 sticky session 불필요. 프로세스 메모리는 권한 원본 아님 | 공개키 로컬 검증 가능. 키 회전, refresh/철회 상태 공유가 별도 필요 |
| 모바일 브라우저 | 동일 origin의 HTTPS 쿠키로 PC와 같은 흐름 | 쿠키 운반이면 동일. 헤더 운반이면 JS가 다루는 토큰 저장 위치와 XSS 대응 필요 |
| 향후 별도 앱 | 별도 앱의 안전한 저장·전달/로그인 UX를 추가 설계해야 함 | 표준 OAuth/OIDC 연계에 사용할 수 있으나 자체 JWT가 곧 표준 로그인 프로토콜은 아님 |
| 향후 MSA | 중앙 검증/introspection 또는 신뢰 가능한 gateway 호출자 전달을 새로 설계 | audience별 제한과 서명 검증을 분산 가능. 즉시 차단과 업무 인가는 여전히 별도 문제 |
| CSRF·유출 | 자동 전송 쿠키이므로 CSRF 방어 필요. HttpOnly라도 XSS가 요청을 대신 실행할 수 있음 | JWT 쿠키도 CSRF 필요. 헤더 access token은 JS 유출 위험, 쿠키 refresh는 CSRF 필요. 서명은 payload 기밀성을 주지 않음 |

**v1은 서버 저장 AuthSession+opaque Cookie로 2026-10-12 A1 승인됐다.** JWT는 후속 버전의 별도 재검토 후보이며 자동 전환은 아니다. 현재 단일 백엔드와 PostgreSQL 기반에서 차단·권한 축소의 결과를 명확히 하는 편이 이 기능에 적합하다는 설계 판단이다. FastAPI나 향후 MSA가 JWT를 요구하지 않는다. 세션 조회·활동 갱신 부하를 실측한 뒤 저장소 재검토 여부를 판단하며 Redis를 선행 도입하지 않는다.

JWT 대안을 선택한다면 access 5분·refresh 8시간을 초기 검토값으로 두되 ARCH-002 승인이 필요하다. refresh 원문은 해시로 저장하고 매 사용 시 원자적으로 회전하며 재사용 시 해당 token family를 폐기한다. `iss/aud/sub/exp/iat/nbf/jti`, 고정 algorithm allowlist, 키 수명/회전과 보관 책임을 정한다. 로그아웃·차단을 다음 요청에 반영하려면 access JWT에도 중앙 철회/계정 버전 검사가 필요하다. 이 비용 없이 “즉시 무효화”를 약속하지 않는다. 앱 도입 시 외부 사용자 에이전트 기반 OIDC/PKCE 등은 별도 ADR로 검토하며 이번에 OAuth 제공자를 만들지 않는다.

### 라이브러리 검토

2026-09-18 공식 문서/유지관리 기록을 읽었으며 설치·호환 시험은 수행하지 않았다. 관찰 버전을 채택 버전으로 고정하지 않는다.

| 구성 | 확인 사실과 이번 추천 |
| --- | --- |
| 기존 FastAPI/Starlette | HTTP 어댑터·의존성 주입·응답 쿠키 API를 활용. Starlette SessionMiddleware는 읽을 수 있는 서명 쿠키 방식으로, DB 저장 opaque AuthSession 구현체가 아니다. 설치된 1.6.0 소스도 확인했다. 이를 사용자/권한 저장소로 채택하지 않음. [공식 middleware](https://raw.githubusercontent.com/Kludex/starlette/main/docs/middleware.md), [쿠키 API](https://raw.githubusercontent.com/Kludex/starlette/main/docs/responses.md) |
| `pwdlib[argon2]` + `argon2-cffi` | FastAPI 공식 예제가 pwdlib/Argon2를 안내한다. pwdlib 공식 release 목록에 0.3.1 및 유지보수 변경, argon2-cffi stable 25.1.0 문서에 parameter profile/측정 안내를 확인했다. 권장 해시·검증·재해시 API의 우선 후보. [FastAPI](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/), [pwdlib releases](https://github.com/frankie567/pwdlib/releases), [Argon2 parameters](https://argon2-cffi.readthedocs.io/en/stable/parameters.html) |
| Python 표준 라이브러리 | `secrets`의 CSPRNG/상수시간 비교, `hashlib`의 digest를 사용한다. 자체 난수·암호 알고리즘을 만들지 않는다. [secrets](https://docs.python.org/3.13/library/secrets.html) |
| FastAPI Users | Cookie transport와 Database strategy를 제공하지만 공식 저장소는 maintenance mode(보안·의존성 유지, 신규 기능 없음)를 명시한다. 기본 SQLAlchemy 통합은 async다. 승인된 동기 기반, 관리자 발급·계정 상태·Scope 규칙과의 조정 비용 때문에 기본 채택은 추천하지 않는다. 유지보수 중단으로 단정하지 않음. [저장소](https://github.com/fastapi-users/fastapi-users), [DB strategy](https://fastapi-users.github.io/fastapi-users/latest/configuration/authentication/strategies/database/) |
| PyJWT | JWT 대안 선택 시 후보. stable changelog의 2.14.0 문서와 보안/검증 변경 기록을 확인했다. 서버 세션안에는 불필요. [changelog](https://pyjwt.readthedocs.io/en/stable/changelog.html), [검증 API](https://pyjwt.readthedocs.io/en/stable/api.html) |

작은 IAM 조정 계층은 필요하지만 해시·암호 primitive는 검증된 라이브러리를 사용한다. 세션 저장·철회·CSRF 결합은 프로젝트가 테스트/보안 리뷰할 책임이다. “라이브러리를 썼으므로 인증 전체가 안전하다”고 처리하지 않는다. 구현 전 Python 3.13/현재 FastAPI·Starlette·동기 SQLAlchemy 조합, 패키지 보안 공지·라이선스·잠금 버전을 검토한다. 현재 lockfile에는 위 새 인증 패키지를 추가하지 않았다.

## 4. 용어·소유권·공개 계약

| 용어 | 의미 |
| --- | --- |
| AuthSession | 로그인 성공으로 발급한 서버 인증 상태. 만료·폐기 대상 |
| PTSession | 실제 수행한 PT 수업 1회 완료 기록. 이번에 생성하지 않음 |
| SQLAlchemy Session | DB 연결/트랜잭션 작업 자원. 브라우저 로그인과 무관 |

| 책임 | 최소 소유 개념 | 공개 계약 초안 |
| --- | --- | --- |
| IAM | Account, 비밀번호 해시, 역할/부여된 관리 Scope, AuthSession, 최초 설정 표시, 자격 설정 요청, 로그인 제한 상태 | `Authenticate`, `ResolveCaller`, `Logout`, `IssueAdminAccount`, `ChangeAccountAccess`, `ChangeAccountStatus`, `StartCredentialSetup`, `CompleteCredentialSetup` |
| Organization | Organization, Branch의 식별·이름·조직 관계 | `CreateInitialOrganization`, `CreateBranch`, `GetBranchFacts`, `ListVisibleBranches`, `GetVisibleBranch` |
| Application 조정 | 한 요청의 인가 순서·UoW·결과 조립, 초기 설정 조정 | IAM 검증 결과와 Organization 계약을 같은 작업 경계에서 사용 |
| 최소 Audit 기반 | 변경/보안 사건의 제한된 기록 | `AppendSecurityEvent`, `AppendAdministrativeChange`. 이번에 일반 감사 검색 API를 만들지 않음 |

**2026-10-10 사용자 결정 — 한 계정의 역할 겸임:** Master Admin 또는 Branch Admin이 Trainer를 겸하며 같은 계정으로 관리 업무와 본인의 PT 진행 기록을 수행한다([ARCH-001의 부분 해결](../product/open-questions.md#arch-001)). Account에 단일 role만 저장해 다른 역할을 배제하는 기존 초안을 대체한다. 계정의 신원·자격과 역할/Scope 부여를 분리하는 기술안을 검토하며, 역할 부여의 저장 구조와 결합 시 인가·감사 표현은 계속 PROPOSED다. Branch Admin의 관리 지점은 여전히 하나이며 Trainer Home Branch는 Workforce가 소유한다. 추가 최종 사용자 정정: 관리자·Trainer 겸임자는 보유한 관리 범위 안이면 본인 Rate/Fixed Amount/Base Salary도 조회·변경할 수 있다. Branch Admin의 본인 Home Branch가 관리 Branch와 다르면 불가하며, 관리자 권한 없는 Trainer의 설정 금지는 유지한다. 이 결정을 모든 업무의 무조건적인 역할 합산으로 확대하지 않는다. 첫 관리자 증분에 가짜 Trainer나 미검증 Trainer 권한을 추가하지 않는다.

`VerifiedCaller`는 서버가 이번 요청에서 확인한 `account_id`, `organization_id`, 부여된 역할과 각 Scope, 보안 버전, 인증 시각을 담는 불변 값으로 제안한다. 행위별 인가는 해당 역할의 Scope와 업무 대상 관계를 검증하며, 관리자 역할이 있다는 이유만으로 Trainer 업무를 자동 완성하지 않는다. 원본 쿠키·비밀번호·ORM·SQLAlchemy Session을 포함하지 않는다. 외부 JSON으로 역직렬화하여 생성하는 요청 모델로 사용하지 않는다. 이 값의 출처와 유효 요청 경계는 Application이 보장한다. 미래 서비스 경계에서는 평문 헤더 전달만으로 같은 신뢰를 얻지 못한다.

의존성은 기존 제안의 `Application → IAM/Organization`, `IAM → Organization의 최소 Branch 사실 계약`을 유지한다. Organization이 IAM 내부를 역호출하지 않도록 공통 계약의 검증된 호출자/인가 범위를 받는다. Organization의 목록·상세 Use Case도 행위와 대상 Scope를 검사한다. Router만 검사하고 내부 Use Case는 무조건 허용하는 구조를 피한다. 모듈 간 직접 ORM 조회·Repository 수정·독립 commit은 승인하지 않는다. 공유 DB 어댑터를 UoW가 조립하되 공개 계약에는 DB 자원을 전달하지 않는다.

브라우저가 보내는 `role`, `organization_id`, `branch_id`, `X-User-*`는 권한 근거가 아니다. 관리 API의 대상 `branch_id`도 Master 인가 후 Organization 계약으로 같은 조직의 지점임을 확인하는 입력일 뿐이다. 지점 목록의 범위는 서버가 계산한다. 관리 역할의 부여를 role=ADMIN과 scope=ORGANIZATION/BRANCH로 표현하는 후보를 유지하며 Master/Branch Admin은 이 조합의 제품 명칭이다. 이를 Account의 유일 role로 고정하지 않는다. Operator/Trainer를 ADMIN으로 치환하지 않는다.

E5의 기존 계정 Operator·Trainer 역할 추가/회수는 Master Organization/Branch Admin 해당 대상 역할의 관리 범위로 검증한다(BR-OPS-019). IAM은 계정/부여 역할/Operator Branch, Workforce는 실제 Trainer/Home Branch 사실의 소유 후보이며 공개 계약으로 필요한 현재 사실/연결을 확인한다. 독립 관리자/다른 Scope·Workforce 업무 상태/소속·과거 식별/이력은 보존한다. 역할 회수/재부여로 Master 전용 지점/연결 변경을 우회하지 않는다. 최소 대상 조회/역할 조합·재부여/동일인 연결·AuthSession/처리 중 요청/UoW·잠금은 후속 설계이며 타 모듈 내부 Repository/ORM 직접 접근을 승인하지 않는다. [2026-10-12 E 일괄 승인](../product/product-decisions.md#review-20261012-e-batch)

## 5. 실제 계정과 지점 준비

### 최초 설정 명령 — 설치 권한의 일회성 예외

아래는 전체 설치 후보 절차다. S1은 [D03 및 개발 절차](iam-001-decision-pack.md)의 로컬 실행 역할·가상 데이터·숨김 입력 범위만 대상으로 한다. 운영 담당 실명·자격 지급/회수 상세는 실제 운영 전에 결정하며 로컬 착수의 선행조건으로 삼지 않는다.

명령 후보 이름은 `bootstrap-initial-master`다. **현재 실행할 수 있는 명령이 아니다.** 자동 startup seed나 공개 bootstrap HTTP endpoint는 만들지 않는다.

1. 지정된 설치 책임자가 제한된 서버/배포 실행 권한과 초기 설정용 DB 자격으로 실행한다. 앱의 익명 HTTP 사용자는 실행할 수 없다. WSL 터미널 접근 권한을 운영 실행 권한으로 간주하지 않는다. 책임자 지정과 운영 자격의 지급/회수는 ARCH-002/OPS-001/T-07 결정이다.
2. 비밀 없는 대상 식별/환경과 조직 이름·최초 로그인 ID를 확인하고, 최초 Master 본인이 새 비밀번호를 설정하며 숨김 입력 채널은 상세 기술 후보로 검토한다. 고정 ID/비밀번호·명령행 인자·셸 이력·출력·저장소의 예시값을 사용하지 않는다. 입력을 받지 못하면 중단한다. 무인 자동화는 보호된 입력 채널을 별도 승인하기 전 지원하지 않는다.
3. 명시적 migration 후 존재하는 singleton 설치 제어 행을 잠근다. DB 읽기 오류를 “계정 없음”으로 취급하지 않는다. 완료 표시 또는 기존 조직/계정이 있으면 non-zero로 중단하며 재설정하지 않는다. 불일치 상태도 복구 지침이 필요하다는 오류로 중단한다. `--force`/덮어쓰기/마지막 Master 재생성 우회는 제공하지 않는다.
4. 한 트랜잭션에서 Organization 계약으로 조직 하나, IAM 계약으로 최초 활성 Master 하나, 감사 사건 및 최초 설정 완료 표시를 저장한다. 실패하면 전부 rollback한다. 동시 실행은 한 번만 성공하며 비밀번호 해시 작업은 긴 DB 잠금 밖에서 처리한다.
5. commit 이후 비밀 없는 성공 결과만 알린다. 응답 유실로 재실행해도 기존 상태는 바꾸지 않는다. 최초 설정 자격을 회수한다. 설치 담당자의 식별/승인 참조를 감사에 남기되 아직 없는 로그인 사용자를 가짜 Actor로 넣지 않는다.

OS/DB 관리 권한 자체를 탈취당한 상황까지 이 명령이 방어하지는 못한다. 초기 비밀번호의 전달·최초 사용자 확인을 포함한 운영 절차가 필요하다. 비상 복구는 bootstrap 재사용이 아니라 별도 검토 대상이다.

### 이후 Master 관리 흐름 — 실제 제품 경로

최초 Master가 실제 로그인하고 지점 생성 API로 Branch A/B를 준비한다. 이후 관리자 계정 발급 API로 로그인 ID와 단일 Branch 범위를 지정한다. 계정은 `PENDING_SETUP`이며 암호 없이 로그인할 수 없다. 별도의 활성 Master 추가도 같은 조직 범위로 발급하여 마지막 관리자 사고에 대비하는 안을 S2에서 검토한다. S1에서는 추가 Master 발급을 제공하지 않는다.

**2026-10-10 사용자 결정 — 최초 설정 흐름:** Master가 관리자·Trainer 계정을 발급한 뒤 일회용 비밀번호 설정 링크를 대상자에게 전달하고, 대상자가 링크를 열어 자신의 비밀번호를 직접 설정한다([ARCH-002의 부분 해결](../product/open-questions.md#arch-002)). 긴 토큰을 사람이 직접 입력하는 기존 제안을 대체한다. Trainer 발급의 실제 구현 순서는 2절을 유지한다.

기술 후보는 서버가 256-bit 일회용 자격 설정 토큰을 만들고 digest만 보관하며, 권한 있는 Master 화면에서 HTTPS/no-store로 설정 링크를 제공하는 안이다. 링크의 신뢰할 origin, URL 내 토큰 표현과 주소/Referer/로그의 노출 방지, 단순 링크 열람과 실제 설정 완료의 구분은 후속 상세 설계 대상이다. 비밀번호 저장과 토큰 소비는 설정 완료 POST에서 수행하는 안을 검토한다. 최초 설정 링크의 유효기간 30분/단일 사용·재발급 시 이전 링크 폐기는 A4로 확정됐다. E2로 권한 있는 관리자의 본인 확인 후 대면/확인된 1:1 직접 링크 전달을 확정했다. AB3로 활성 계정 reset TTL30분을 선택했고 확인/전달 운영 절차·URL/노출/소비 상세는 후속이며 C4 즉시 자격/로그인 무효 정책은 유지한다. 링크 정책 승인으로 자동 이메일·SMS 연동을 채택하지 않으며 v1 인증 방식은 A1/ADR-0004에서 별도 채택됐다.

계정 주인이 일회용 토큰과 직접 선택한 비밀번호로 자격 설정을 완료한다. token purpose/account/security version/만료/단일 사용을 검사하고, 비밀번호 해시 저장·토큰 소비·기존 인증 폐기·감사를 원자적으로 처리한다. 자동 로그인하지 않고 새 로그인 과정을 거친다. 전달 실패 시 조회 API로 원문을 재표시하지 않는다. Master가 재발급하면 이전 토큰을 폐기한다.

테스트 fixture는 가상 조직/계정·해시·Scope를 전용 테스트 DB에 준비할 수 있지만 운영 발급 수단이 아니다. 인수 검사에는 위 명령과 관리/활성화 API를 실제 통과하는 시나리오가 별도로 필요하다. 운영에 테스트 fixture나 사용자 강제 주입 경로를 노출하지 않는다.

E1/E2 승인 경계: 제한된 최초1회 설치 명령과 최초 Master 본인 암호 설정, 이후 각 발급/reset 권한 있는 관리자의 본인 확인·대면/확인된 1:1 직접 링크 전달 방식은 확정이다. 설치 담당자 실제 지정/통제 자격의 지급·회수·원격 확인/보호 입력·전달/실패 운영 절차와 기술 후보(명령 이름/인수/잠금)는 후속이다. 초기 웹 설치/자동 발송을 구현하거나 Bootstrap을 마지막 Master 복구로 재사용하지 않는다. [2026-10-12 E 일괄 승인](../product/product-decisions.md#review-20261012-e-batch)

## 6. 계정·로그인 상태 정책 제안

아래는 전체 IAM-001의 초기 수치/전이 후보다. S1 정책 승인 대상은 [D04~D12](iam-001-decision-pack.md)이며, IP 제한 30회는 D10의 개발 후보 100회로 조정하고 보존 24시간/90일은 운영 비교 후보로 남긴다. 추가 Master·재설정·복구 전이는 S2다.

아래 상세 후보 중 A/B/C/E 일괄 승인 부분은 확정이다. E1/E2 설치/전달 방식, E3/E4 ID 대소문자 비교/이전 ID 예약, E5 역할 관리 Actor·Scope와 E6 일반 차단 해제의 유효 암호 허용을 적용한다. AB3 reset30분/AB4 운영 관리자 비밀번호+Passkey/AB5 복구 승인·실행 책임은 확정됐다. 구체 운영 보호/전달·정규화·역할/상태·IP 방어/보존·Passkey 등록/복구·비상 자격/절차 등 남은 상세는 **OPEN/PROPOSED**다. 기술적으로 구현 가능하다는 이유로 남은 값을 기본값으로 넣지 않는다. 최초 설정 링크 30분 승인과 reset 링크/CSRF 수명의 후보를 구분한다. 기존 질문 안의 결정 항목이며 새로운 Product 질문이 아니다.

| 결정 구분 / 기존 게이트 | 추천안 | 이유·남는 비용 |
| --- | --- | --- |
| 제품: 로그인 ID — ARCH-002 | A2 별도 영문·숫자 중심 3–64자, E3 대소문자 미구별/E4 이전 ID 원래 계정 예약·타계정 재할당 금지/현재 ID만 로그인. C6 Master 변경/계정·역할/연결·이력 보존·전 로그인 종료 | ASCII regex/소문자 저장·구분자/공백/표시/예약/유일성은 기술 상세, 원래 계정의 이전 ID 재사용도 Master 변경 절차. S1 기능 일괄 확대 아님 |
| 제품/보안: 비밀번호 — ARCH-002 | A3 15–128자/조합·정기 변경 강제 없음/흔한 암호 차단. C3 본인 현재 암호 확인 후 변경/모든 로그인 종료 승인. Unicode/NFC·공백/길이 처리·차단목록 공급은 기술 상세 후보 | 현재 암호를 아는 마지막 Master도 본인 변경 가능. 차단 계정 복구/MFA 초기화와 구별하며 적합한 차단목록/해시 비용 검증 필요 |
| 기술: 비밀번호 저장 — T-05 | pwdlib/Argon2id, 라이브러리의 salt/검증/재해시 사용. 64 MiB·t=3·p=4를 측정 시작 후보로 삼고 동시 로그인 메모리/지연 측정 후 고정 | OWASP 최소 기준 이상을 목표로 하되 라이브러리 버전/운영 자원 미검증. SHA-256은 비밀번호 저장에 쓰지 않음 |
| 제품: 로그인 수명 — ARCH-002 | A5의 2번 승인: 모든 역할 idle 30분/absolute 8시간. 요청 활동/만료 판정의 상세 후보:  로그인 유지 옵션 없음. 서버 시각 기준, `now >= expiry`는 만료 | 편의와 단말 방치 위험의 절충. 브라우저 종료가 확실한 폐기라는 가정은 하지 않음 |
| 제품: 여러 기기 — ARCH-002 | 독립 AuthSession 허용. 일반 로그아웃은 해당 세션만, 계정 차단·비밀번호 설정/변경·권한 변경은 모든 세션 폐기 | 현장 여러 기기 사용을 막지 않되 계정 전체 위험 변화 후 기존 로그인 철회/재로그인 |
| 제품: 중요 계정 관리 확인 — ARCH-002 | C1의 2번 승인: 유효 로그인/현재 행위·대상 Scope 안에서 추가 비밀번호 재확인 없이 처리. 5분 이내 확인·이를 위한 강제 재로그인/별도 재인증 미채택 | CSRF/HTTPS·A5 만료·A10 운영 전 MFA 유지. 본인 암호 변경의 현재 암호 확인(C3)은 별개 |
| 제품: 설정 토큰 — ARCH-002 | A4의 2번 승인: 최초 설정 30분/단일 사용/재발급 이전 링크 폐기. 재설정 30분·목적 표현·로그인 CSRF 준비 10분은 별도 상세 후보 | 토큰 유출 창을 제한. 만료 시 Master 재발급 필요 |
| 제품: 마지막 Master — ARCH-002 | A9/C5 승인: 마지막 사용 가능 Master 차단·권한 제거·일반 관리자 reset 금지. C3 현재 암호 확인 본인 변경은 허용 | 사용 가능 판정/경합·대기 계정 제외 등 상세와 별도 비상 복구 책임/증거·실패 인수는 후속. 보호만으로 복구 완료 아님 |
| 제품: 추가 Master·자기 변경 — ARCH-002 | A9 복수 Master 허용/마지막 사용 가능 Master 보호, C5 일반 reset 금지. 현재 암호 확인 본인 변경은 C3 승인으로 별도 허용 | 발급/역할 변경 Actor·정확한 상태/조직 잠금·다른 Master가 있는 경우의 관리 전이 상세는 후속 |
| 제품: 계정 상태 — ARCH-002 | E6 승인: Master 일반 차단 해제 시 유효 기존 암호로 새 로그인/매번 강제 reset 없음. PENDING_SETUP/ACTIVE/DISABLED 구체 저장·전이는 제안 | 폐기 로그인/설정 요청·무효 암호·회수한 역할/MFA·Trainer 상태 자동 복원 없음. 침해 복구는 별도, 현재 역할/자격·MFA 등 기존 요건 유지 |
| 제품: 재설정 — ARCH-002 | A8/C4 승인: 같은 Organization Master가 ACTIVE 계정 reset을 명시 확정하면 옛 암호와 모든 기존 로그인 즉시 무효. 새 암호 설정 후 로그인. 마지막 Master 일반 reset은 C5 거부 | 원자적 자격 무효화/credential_setup_required 등의 저장은 후보. reset 링크30분은 미승인, 전달/소비·차단/Trainer 상태 비복원·감사 상세 필요 |
| 제품: 관리자 MFA — ARCH-002, T-05/T-07 | A10 승인: Master/Branch Admin MFA는 실제 운영 시작 전 필수.  첫 제한된 개발 검증은 비밀번호만으로 가능 | 미적용 시 피싱·재사용 암호·단말 탈취 위험이 남음. AB4 비밀번호 뒤 사용자검증 Passkey 선택, 서버 검증·등록/분실/복구/호환성 설계·실검증이 별도 필요. 무MFA 운영 허용으로 해석하지 않음 |
| 제품/운영: 보존 — LEGAL-001, ARCH-004 | 만료/폐기 인증·설정·준비 상태는 만료 후 24시간 이내 정리, 실패 제한 bucket은 24시간, 식별을 최소화한 감사는 90일을 검토 시작값으로 제안 | 기간/열람 책임 미승인. DB 백업의 보존·복원 후 인증 폐기도 함께 결정해야 함 |

비밀번호 길이/차단목록의 참고는 [NIST 비밀번호 지침](https://pages.nist.gov/800-63-4/sp800-63b.html), 해시 선택은 [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)와 위 Argon2 문서다. 이는 참고 근거이며 법적 준수/AAL 인증이나 성능 시험을 주장하지 않는다.

### 로그인 실패와 반복 시도

존재하지 않는 ID·틀린 비밀번호·비활성·자격 설정 대기는 동일한 `401 invalid_credentials`와 본문을 사용한다. 없는 계정도 동일 비용의 더미 해시를 검증해 시간 차이를 줄이되 완전한 시간 동일성을 약속하지 않는다. 입력 형식 실패는 비밀 입력을 반사하지 않는 422다. 계정 존재를 추론하는 세부 사유를 외부에 내보내지 않는다. [OWASP Authentication](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html).

C2 승인: 계정당 15분 내 5회 로그인 실패 시 15분 대기 후 재시도하며 영구 잠금/관리자 수동 해제는 두지 않는다. 없는 ID도 같은 일반 오류로 계정 존재를 노출하지 않는다. 기존 IP당 15분 30회는 D10의 100회 개발 후보로 조정됐으나 어느 IP 수치도 승인되지 않았다. 공유 NAT·프록시 신뢰·해시 자원/준비 상태·토큰 제출 보호와 원자적 카운터/성공 초기화·진행 중 시도/창 경계는 후속 기술 검토다. C1 추가 관리 비밀번호 재인증 경로는 제외한다.

여러 worker가 PostgreSQL bucket의 원자적 갱신/예약을 공유한다. 비싼 해시 전에 시도 예산을 예약해 동시 요청 우회를 막고 트랜잭션 rollback 때문에 실패 횟수가 사라지지 않게 별도 보안 상태 트랜잭션으로 확정한다. ID/IP는 제한용 keyed digest로 보관하고 이 키는 외부 비밀 설정으로 모든 worker에 동일하게 주입한다. IP를 raw 일반 로그에 남기지 않으며 임의 X-Forwarded-For를 믿지 않는다. 프록시 신뢰 범위는 T-07이다. 인증 제한 저장소 장애는 503이며 무제한 로그인으로 fallback하지 않는다. 서버 전체 해시 동시성·요청 크기 제한도 측정하며 worker별 메모리 카운터를 분산 제한의 대체로 쓰지 않는다.

### AuthSession 발급·조회·폐기

로그인 성공 시 CSPRNG 32바이트 식별자를 생성해 쿠키로만 전달한다. DB에는 식별자 SHA-256 digest와 별도 내부 ID를 보관한다. 높은 난수성의 토큰 digest와 비밀번호 해시는 용도가 다르다. 클라이언트 지정 식별자/URL token/role claim을 채택하지 않는다. 비밀번호 확인은 잠금 밖에서 수행하되 발급 트랜잭션에서 계정 활성 상태·보안 버전·검증한 해시가 여전히 같은지 재확인하여 차단/재설정과 경합한 로그인을 막는다.

로그인 전 준비 상태는 성공 시 폐기하고 완전히 새로운 AuthSession을 만든다. 준비 상태 소비와 세션 발급은 한 트랜잭션이며 동시 성공 요청 두 개가 같은 준비 상태를 재사용하지 못하게 한다. C1의 미채택 재인증 API를 인증 경로에 추가하지 않는다. 유효한 로그인 상태에서 다른 계정으로 로그인하려면 먼저 로그아웃하는 흐름을 추천한다. [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html).

매 보호 요청에서 PostgreSQL의 세션 digest·만료·폐기·계정 상태·보안 버전을 확인한 후 현재 Scope로 VerifiedCaller를 만든다. 권한을 프로세스 메모리나 로그인 시점 snapshot만으로 재사용하지 않는다. 인증 확인용 `/me`, `/csrf`의 자동 호출은 idle 수명을 늘리지 않는 안을 추천한다. 활동 갱신은 이전 만료를 먼저 검사하며 absolute 종료를 연장하지 않는다. 서버 재시작으로 만료/폐기 상태가 초기화되지 않는다. 정리 작업이 늦어져도 만료된 행은 인증에 사용할 수 없다.

로그아웃은 서버의 해당 AuthSession을 폐기한 뒤 같은 이름/Path/Domain 조건으로 쿠키를 삭제한다. 모든 상태 변경 commit 성공 후 응답한다. DB 장애/commit 결과 불명확 시 503이며 쿠키만 지우고 서버 로그아웃 성공으로 안내하지 않는다. 재요청은 이미 폐기된 상태를 성공으로 수렴시킬 수 있다. DB 복원은 폐기됐던 상태를 되살릴 수 있으므로 복원 시 기존 세션·설정 토큰 전체 무효화를 운영 복구 절차의 진입 조건으로 제안한다.

### 변경과 처리 중인 요청의 경계

추천 정책은 “보안 변경 commit 이후 인가를 시작한 요청에는 이전 권한을 허용하지 않음”이다. 이미 승인돼 응답을 보내는 요청을 소급 회수한다고 표현하지 않는다. 유효 세션을 먼저 읽었다는 사실만으로 오래된 권한의 나중 쓰기를 허용하지 않도록 다음 짧은 트랜잭션 순서를 제안한다.

- 지점 읽기는 IAM이 계정 행의 공유 잠금과 세션 행 잠금으로 현재 상태를 재확인하고, Organization 계약의 scoped query와 DTO 구성까지 같은 UoW에서 끝낸다. commit 후 외부 전송 지연까지 잠금을 유지하지 않는다. 늦게 도착한 응답의 데이터는 이미 인가된 읽기 시점 기준이다.
- 계정 관리 요청은 설치/조직 제어 행 → actor/target 계정 행(ID 정렬) → 관련 인증/자격 설정 행의 고정 순서로 잠근다. 처음부터 이 순서로 인증/인가를 조정하며 Router에서 계정 잠금을 먼저 잡은 후 제어 행을 뒤늦게 잠그지 않는다. 마지막 Master 검사도 제어 행 아래 직렬화한다.
- 차단/권한 변경/재설정은 보안 버전 증가·세션 폐기·필요한 설정 토큰 폐기·감사와 함께 commit한다. 재활성화 또는 Branch 범위 재부여로 과거 세션을 되살리지 않는다. 권한 상승도 재로그인 대상이다.
- 읽기가 먼저 잠금을 확보했다면 관리 변경은 그 읽기 완료를 기다린다. 변경이 먼저 commit됐다면 다음 읽기는 무효 세션으로 401이다. 나중 재로그인한 Branch Admin은 축소된 범위만 조회한다. 장기 스트리밍·백그라운드 작업에 VerifiedCaller를 재사용하지 않는다.
- 이 절은 IAM/지점 읽기와 최소 관리 명령의 T-09 제안이다. Pass·지급 동시성의 해결책으로 확대하지 않는다. 실제 PostgreSQL 두 연결/worker의 순서 제어 시험, 잠금 대기 제한과 deadlock 처리 검증 후 구현 완료를 판단한다.

2026-10-12 G1 승인: 관리/업무 Branch가 비활성이어도 계정/역할이 유효하면 로그인과 기존 권한 내 조회를 허용한다. 이는 계정 DISABLED·Trainer 자체 비활성·회수 역할/만료·폐기 AuthSession/MFA 등 기존 조건을 해제하지 않는다. Branch 상태와 실제 행위별 Scope는 구분하고 요청마다 현재 사실로 인가한다. G2–G5 과거 수업 처리·타 활성 지점 이용/명시적 이동은 각 후속 업무 계약에서 반영한다. S1에 Branch 상태 변경 API·Trainer/PT/정산/이동 schema를 자동 추가하지 않으며 조회에 필요한 실제 상태/최소 사실 계약과 검증 범위는 후속 기술 검토다. [2026-10-12 G 일괄 승인](../product/product-decisions.md#review-20261012-g-batch).

## 7. 브라우저·CSRF·로그 보안

프론트엔드와 API를 **같은 origin**으로 서비스하는 구성을 우선 후보로 둔다. 운영 도메인·TLS 종료·프록시·배포는 미선정이다. 별도 origin 개발 서버도 프록시로 같은 origin을 만들 수 있으나 이번에는 설정하지 않는다. CORS는 인증/CSRF 방어의 대체가 아니다.

운영 쿠키 후보는 `__Host-y3-auth`, `Secure; HttpOnly; SameSite=Lax; Path=/`, Domain 생략이다. 로그인 전에는 별도 `__Host-y3-preauth`를 쓴다. 브라우저 세션 쿠키를 기본 후보로 하고 실제 만료는 서버가 결정한다. 로그아웃의 만료 쿠키에도 일치하는 속성을 적용한다. HTTPS 요청/응답뿐 아니라 로그인 페이지 전달부터 보호하고, 신뢰한 프록시의 scheme/Host 검증, HSTS 적용 범위와 인증 응답 `Cache-Control: no-store`를 운영 설계에서 확인한다. 쿠키 속성·prefix의 브라우저 조건은 [MDN Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie)를 참고했다.

로컬 HTTP 예외가 필요하면 development/test + 명시적 opt-in + loopback 전용 origin일 때만 `y3-dev-auth` 같은 별도 이름과 Secure 해제를 허용하는 안을 제안한다. production에서는 HTTP origin·비보안 쿠키·개발 이름·wildcard 자격 CORS·누락된 보안 설정이면 기동을 거부한다. 요청의 Host나 OS가 Linux/WSL이라는 이유로 예외를 켜지 않는다. 운영 모드 실브라우저 검증은 HTTPS로 따로 수행한다.

CSRF는 서버 저장 synchronizer token 방식의 제안이다. 인증용 쿠키와 별도로 CSPRNG로 만든 CSRF nonce를 AuthSession 또는 로그인 준비 상태에 보관하고, 같은 origin JS에만 `/auth/csrf`의 no-store 응답으로 전달한다. 이 nonce는 단독 로그인 자격이 아니며 일반 로그/감사에도 남기지 않는다. JS는 메모리에 보관하고 변경 요청의 `X-CSRF-Token`으로 전송한다. 로그인 세션 식별자는 HttpOnly 쿠키 밖으로 노출하지 않는다.

| 요청 | 추천 방어 |
| --- | --- |
| `GET /auth/csrf` | 유효 인증 상태가 있으면 해당 nonce를 반환. 없으면 짧은 준비 상태를 생성/재사용하고 별도 쿠키 발급. 계정/업무 상태는 변경하지 않는 인증 준비 예외. custom `X-Y3-Client` 헤더 요구, cross-origin CORS 불허, Fetch Metadata의 cross-site 차단과 발급 제한 적용 |
| 로그인·계정 활성화/재설정 완료 | 준비 쿠키에 결합한 CSRF token 검사, Origin 정확 일치. 준비 상태를 로그인 세션으로 승격하지 않고 소비/폐기 후 새 상태 발급 |
| 로그아웃·본인 암호 변경·관리 변경 | 유효 AuthSession의 CSRF token을 상수시간 비교. Origin 정확 일치, JSON Content-Type/몸체 크기 제한. GET 변경 금지 |
| Origin이 없는 변경 요청 | 엄격한 Referer origin 확인을 fallback 후보로 하고 둘 다 없거나 `null`/불일치면 403. 허용 origin은 서버 설정에서 읽으며 임의 Host 값으로 산출하지 않음 |

SameSite만으로 로그인 CSRF나 같은 site의 다른 origin을 방어했다고 판단하지 않는다. 만료/미인증 로그아웃은 새 준비 상태의 CSRF로 쿠키만 정리해 204로 수렴할 수 있지만, 준비 토큰으로 유효한 다른 AuthSession을 폐기할 수는 없다. 유효 인증 상태에서는 그 세션에 결합한 nonce가 필요하다. 병렬 탭은 같은 AuthSession nonce를 사용하며 로그인으로 교체되거나 인증 철회된 뒤 이전 nonce는 실패해 다시 조회한다. [OWASP CSRF의 로그인 준비 상태·동기화 토큰 안내](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).

비밀번호/해시, 원본 로그인·자격 설정·CSRF 토큰, 링크, Cookie/Authorization 헤더, 인증 본문, DB URL을 로그/trace/감사에 넣지 않는다. C8 로그인 감사는 계정·시각·행위·성공/실패 최소 정보로 원문 IP/브라우저 정보를 제외한다. 미확인 계정 표현/제한용 digest의 별도 처리·보존은 후속이다. 계정 관리 감사는 기존 검증 actor·역할/Scope/대상·전후 상태/역할·시각 등 필수 변경 기록을 유지하며 암호/해시 전후는 기록하지 않는다. 인증/계정 관리 감사의 앱 열람은 C7의 자기 Organization Master만이다. 중요 변경과 필수 감사는 함께 성공/실패하고 다른 업무의 보상정보 권한을 확대하지 않는다.

XSS는 HttpOnly 이후에도 사용자 권한으로 요청을 보낼 수 있다. 이후 UI의 출력 escape·CSP·외부 스크립트 관리가 필요하다. 지급 설정·기본급·정산 금액은 IAM/지점 DTO에 필드 자체가 없으며 SQL/오류/감사 우회로도 공개하지 않는다.

## 8. 최소 데이터와 API 초안

### 데이터 개념과 제약 후보

아래는 migration 설계 범위이며 SQLAlchemy 모델/DDL이 아니다. 시간은 서버 UTC 기준, ID는 내부 불투명 식별자 후보다.

| 소유자 / 개념 | 필요한 정보·불변 조건 |
| --- | --- |
| Organization / Organization | ID, 이름. 현재 설치는 하나의 조직; SaaS/조직 선택 로그인 추가 없음 |
| Organization / Branch | ID, organization_id, 업무 식별 code·name. `(organization_id, code)` 유일. 이번에는 비활성 상태 전이/삭제 없음 |
| IAM / Account | ID, 정규화 login_id 유일, password_hash(미설정 시 없음), 상태, credential_setup_required, organization_id, security_version, 생성/변경 시각. 단일 role 컬럼으로 겸임을 배제하지 않음 |
| IAM / 역할·관리 Scope 부여 | Account와 분리한 역할/Scope의 표현 후보. ADMIN+ORG는 관리 Branch 없음, ADMIN+BRANCH는 정확히 하나. 같은 계정의 Trainer 역할과 실제 Trainer 연결을 수용하며 Trainer/Home Branch 원본은 Workforce 소유. S1의 실제 부여는 관리자만, Trainer 연결/인가 구현은 후속 v1 증분. 다지점 관리자 배열/임의 권한 JSON 없음 |
| IAM / AuthSession | 내부 ID, 고유 token digest, account_id, 발급 당시 security_version, 발급/idle/absolute 시각, revoked_at, CSRF nonce. role/지점 snapshot을 현재 권한 원본으로 사용하지 않음 |
| IAM / LoginPreparation | preauth digest, CSRF nonce, 만료/소비 시각. 계정 인증 증거 없음, 인증 성공 시 재사용 금지 |
| IAM / CredentialSetup | 고유 digest, account_id, purpose(activation/reset), 대상 security_version, 만료/소비/폐기 시각, 발급 actor. 재설정 token으로 role/지점/상태 활성화를 바꾸지 못함 |
| IAM / InstallationControl | 고정 식별 행, 최초 설정 완료/조직 식별. bootstrap 경쟁과 마지막 Master 변경의 직렬화 기준. migration에는 비밀 없는 미설정 제어 행만 준비 |
| IAM / AttemptBudget | 목적·ID/IP digest key, window/counter/cooldown/expiry. 여러 worker의 원자적 제한 |
| Audit / 최소 사건 | 사건 ID·종류·검증된 actor 또는 설치 실행자·대상·허용 변경값·시각. 비밀 원문·보상정보 없음 |

같은 조직의 관리 지점만 참조하도록 Organization의 `(organization_id, branch_id)` 후보 키와 IAM 관리 Scope 부여의 복합 FK를 검토한다. 이 물리적 cross-module 참조는 삭제 정합성과 추출 비용을 가진 **T-01 제안**이며 직접 내부 테이블 조회/수정 허용이 아니다. Account/역할 부여/AuthSession/설정 요청의 참조와 digest 유일성, 상태 CHECK, 만료 조회 인덱스도 필요하다. 역할 부여의 구체 모델과 잠금 순서는 겸임 요구에 맞춰 상세 재검토하며 기존 단일 역할 초안의 잠금 표를 그대로 승인하지 않는다. 마지막 Master 불변식은 단순 CHECK로 대신하지 않고 관리 트랜잭션으로 검증한다. hard delete/cascade로 감사와 계정 이력을 지우지 않는다.

### API 요청·응답 후보 — 전체 IAM-001

S1의 정확한 API/CLI 목록은 [결정안 4절](iam-001-decision-pack.md)에 있다. 아래 generic 관리자 발급/상태/권한·credential-setup 표를 통째로 S1 구현하지 않는다. activation 전용 재발급은 포함하지만 활성 계정 reset, ACTIVE 복구, 추가 Master는 제외한다.

공통 접두사는 `/api/v1` 후보이며 아래에서는 생략했다. 모든 요청 모델은 허용 필드만 받고 권한 위조 필드는 거부한다. 401/403/404/409/422/429/503 오류에는 안전한 `code`, 일반 메시지, 비밀 없는 request_id만 포함한다. 인증 여부/Scope를 확인하기 전에 타 지점 존재 여부를 응답하지 않는다.

| API | 입력 / 인증·인가 | 성공 결과 | 핵심 실패 |
| --- | --- | --- | --- |
| `GET /auth/csrf` | 인증 또는 준비 쿠키, 준비 요청 custom header | 200 `{csrf_token}` + 필요 시 preauth 쿠키 | 403 출처, 429 제한, 503 저장소 |
| `POST /auth/login` | `{login_id, password}`, 준비 CSRF | 204 + 새 인증 쿠키; 원본 토큰 JSON 없음 | 401 일반 실패, 409 이미 로그인, 422 형식, 429, 503 |
| `GET /auth/me` | 유효 인증 쿠키 | 200 `{account_id, login_id, organization_id, grants:[{role, scope}], capabilities}` 후보. 각 부여의 Scope를 구별하고 단일 role로 겸임을 배제하지 않음 | 401 만료/폐기/차단, 503 DB 장애 |
| `POST /auth/logout` | 인증+CSRF. 무효 세션은 준비 CSRF로 정리 가능 | 204, 서버 폐기 확정 후 쿠키 삭제 | 403 CSRF, 503 폐기 미확인 |
| `GET /branches` | Master/Branch Admin | 200 `{items:[{id, code, name}], next_cursor}`. Master 조직 필터 또는 Branch Admin 단일 지점 필터 | 401, 403 관리자 열람 권한 없음, 422 잘못된 query, 503 |
| `GET /branches/{branch_id}` | 위와 동일 | 200 `{id, code, name}` | 404 미존재 또는 Scope 밖 동일 응답, 401/403/503 |
| `POST /admin/branches` | Master, 인증+CSRF; `{code, name}` | 201 `{id, code, name}`. 조직은 호출자에서 결정 | 403, 409 조직 내 code 중복, 422, 503 |
| `POST /admin/accounts` | 유효 로그인/현재 Master 권한+CSRF; `{login_id, admin_scope:{kind, branch_id}}` | 201 `{account_id, state, version, setup_token, expires_at}`. token 1회 표시 | 403, 409 ID 중복, 422 잘못된/타 조직 Branch, 503 |
| `GET /admin/accounts/{id}` | Master, 같은 Organization의 관리자 계정 | 200 `{account_id, login_id, state, admin_scope, credential_setup_required, version}`. 재설정 token/해시/세션 목록 없음 | 401/403, 404 타 조직/미존재, 503 |
| `PATCH /admin/accounts/{id}/access` | 유효 로그인/현재 Master 권한+CSRF; `{admin_scope, expected_version}` | 200 비밀 없는 account/access/version. 모든 기존 인증 폐기 | 404 타 조직/미존재, 409 경합/마지막 Master, 422 |
| `PATCH /admin/accounts/{id}/status` | 유효 로그인/현재 Master 권한+CSRF; `{status, expected_version}`. ACTIVE/DISABLED만 관리 입력 | 200 비밀 없는 상태/version | 409 마지막 Master/미설정 계정 활성화/경합, 404/422 |
| `POST /admin/accounts/{id}/credential-setup` | 유효 로그인/현재 Master 권한+CSRF; `{expected_version}`. 서버가 상태에 따라 activation/reset 목적 결정 | 201 `{setup_token, expires_at}`, 이전 인증/설정 요청 폐기 | 409 마지막 Master/경합, 404/403/503 |
| `POST /auth/credentials/complete` | `{setup_token, new_password}`, 준비 CSRF | 204, token 소비. 인증 쿠키 발급 없음 | 400 무효/만료/소비된 token 동일 응답, 422 비밀번호 정책, 429, 503 |

이 관리자 발급/변경 API의 **실제 허용 Actor는 승인된 Master**를 기초로 설계한다. Branch Admin에 같은 기능을 주는 안은 MB-004 결정 전 구현하지 않는다. 복수 Master 허용/마지막 사용 가능 Master 차단·권한 제거 금지는 A9 승인이다. self/사용 가능 판정·새 Master 발급/복구의 나머지 상세는 ARCH-002 후속이다. `admin_scope`는 첫 증분 전용 계약이며 이후 Trainer/Operator 발급 기능을 대신하지 않는다. 계정 검색/목록, 본인 비밀번호 변경 UI, 비상 복구 API는 이번 최소 범위에 넣지 않는다. 관리 대상 ID는 발급 응답(본인은 `/me`)으로 확보하고, 최소 상세 조회로 최신 상태/version을 확인한다. 존재하지 않는 계정 검색 API를 가정하지 않는다. `version`은 계정의 security_version이며 `expected_version` 불일치 시 409로 반환해 재조회하도록 한다. 설정 완료/상태/Scope/재설정 변경은 버전을 올리고, 해시 비용 갱신만 하는 rehash는 원래 해시가 그대로인지 확인한 뒤 교체하되 비밀번호 변경으로 취급하지 않는다.

`/me`의 capabilities는 이번 증분에서 허용된 행위만 포함한다(예: `branch.read`, Master의 최소 관리 행위). 전체 v1 Permission 카탈로그 확정이 아니다. 화면 표시용 결과를 다음 요청의 권한 증명으로 되돌려 받지 않는다. 지점 목록은 서버 필터 **후** pagination/count를 계산한다. page size 50/최대 100은 기술 후보이며 cursor는 권한 근거가 아니고 다른 계정의 cursor에도 현재 Scope를 다시 적용한다. 첫 증분에서는 organization/branch 범위를 넓히는 query를 제공하지 않는다.

인가 순서는 출처/입력 검증 → 현재 인증 확인 → 행위 허용 확인 → 대상 Scope 제한이다. 보호 경로의 미인증은 401, 로그인된 비관리자의 관리자 기능은 403, 관리자가 요청한 Scope 밖 Branch 상세는 404다. 비밀번호 같은 입력값을 FastAPI validation error에 되비추지 않도록 기존 안전 오류 처리 경계를 유지한다. 쿠키 기반 로그인에서 무관한 Bearer challenge를 붙이지 않는다. 감사 기록 실패 시 관리 변경도 rollback하며 503 또는 안전한 500으로 실패시킨다.

### migration 범위와 실행 원칙

승인 뒤 위 최소 IAM/Organization/감사 객체와 제약·인덱스만 revision으로 만든다. 현재 `target_metadata`/업무 revision이 없으므로 모델 등록과 metadata 범위도 명시적 리뷰 대상이다. migration은 고정 계정·비밀번호·실제 Branch 데이터를 seed하지 않는다. 비밀 없는 InstallationControl 한 행과 업무 계정의 bootstrap을 구분한다. 앱 시작 create_all/자동 migration은 도입하지 않는다.

빈 전용 DB의 upgrade → 제약 확인 → 가상 데이터/로그인 검사, 직전 revision→새 revision, 실패 rollback, 정해진 downgrade 또는 forward 복구 절차를 실제 PostgreSQL에서 확인해야 한다. 초기 revision의 downgrade는 IAM/계정 데이터를 없앨 수 있으므로 운영에서 자동 실행하지 않는다. 기존 `alembic current` 성공은 이 검증의 대체가 아니다. 운영 데이터 백업·복원·권한·배포 순서는 여전히 T-07/ARCH-004 후속이다.

C3/C6의 본인 암호 변경/Master Login ID 변경 기능은 v1 정책으로 승인됐으나 위 S1 계약/기능 목록에 자동 추가하지 않는다. 구체 API/DTO·현재 암호 검증·ID 유일성/이력·전 로그인 철회·감사/실패 원자성과 경합은 해당 후속 증분에서 설계한다. C1에 따라 위 관리 API는 5분 이내 비밀번호 확인이나 이를 위한 새 로그인 조건을 요구하지 않는다. [2026-10-12 C 일괄 승인](../product/product-decisions.md#review-20261012-c-batch)

E3/E4로 현재/이전 Login ID의 대소문자 미구별 유일성·원래 계정 예약을 처음 발급/변경부터 설계해야 한다. 예약 ID는 로그인 별칭이 아니고 다른 계정으로 이전하지 않는다. 정규화 key/예약 이력·제약/잠금·API/오류/감사 계약은 아직 후보이며 새 테이블/migration을 생성하지 않았다. E5 역할 관리도 위 관리자 전용 S1 API 목록에 자동 추가하지 않고 후속 실제 Workforce/Operator 계약과 함께 설계한다. [2026-10-12 E 일괄 승인](../product/product-decisions.md#review-20261012-e-batch)

## 9. 인수 사례와 검사 경로 제안

아래는 **실행 결과가 아닌 추가할 검사**다. 독립 계정 A/B와 가상 조직/지점만 사용하며 운영 계정·개인정보를 fixture로 복제하지 않는다.

| 사례 | 기대 결과 | 필요한 수준 |
| --- | --- | --- |
| 실제 계정 정상 로그인 / 오입력 / 없는 ID / DISABLED / 설정 대기 | 정상만 새 DB AuthSession 발급, 나머지 일반 401. 토큰/계정 존재 정보 비노출 | 실제 HTTP 로그인+PostgreSQL, 해시 검증 |
| 만료 경계 / 폐기 / 보안 버전 불일치 | cookie가 남아 있어도 401. idle 갱신으로 만료 상태 복원 불가 | 순수 시간 정책 + 실제 DB |
| 로그아웃 후 복사한 기존 쿠키 재접근 / 다른 기기 | 기존 상태 401, 별도 세션은 정책대로 유지. DB 실패 시 로그아웃 성공으로 보고하지 않음 | 실제 로그인·쿠키 jar·DB |
| Master 목록·상세 / 다른 Organization ID | 자기 조직 전 지점 조회, 타 조직 자료 없음/404 | 실제 DB scoped query |
| Branch Admin 목록·상세 / ID·query·cursor 조작 | 자기 지점만 목록/상세, 타 지점과 미존재 상세 동일 404. pagination/count에도 정보 누출 없음 | 정책 단위 + 실제 DB/HTTP |
| role/org/branch 헤더·JSON 위조 / 비관리자 호출 | 서버 권한 불변, 부가 권한 필드 거부, 허용되지 않은 관리 API 403 | 어댑터·Use Case, 이후 실제 Trainer 계정 증분 |
| 차단 / 재활성화 / 지점 범위 축소·이동 / Master 강등 | 모든 과거 상태 폐기. 재로그인 후 새 권한만. 재활성화로 과거 세션 복원 없음 | 두 독립 DB 연결의 순서 제어 |
| 비밀번호 재설정과 로그인/토큰 소비 경합 | 이전 암호/세션 무효, 설정 token 단일 사용. 중복 요청·DISABLED 토큰으로 우회 활성화 없음 | 실제 DB 경쟁/실패 주입 |
| 처리 중 조회와 보안 변경 경합 | 제안된 잠금 순서에 맞는 선후 관계. 변경 후 새 요청은 구권한 사용 불가 | 실제 PostgreSQL, 다른 worker |
| 로그인 fixation / 자격 변경 철회 / 병렬 탭 | 준비 상태와 이전 AuthSession 재사용 불가. 회전 이후 옛 CSRF 거부 | DB 통합 + 브라우저 |
| CSRF 누락·위조 / 로그인·로그아웃·관리 요청 / sibling origin | 변경 없음. 준비 token이 인증된 다른 세션의 token을 대체하지 못함 | 서버 음성 사례 + 실제 브라우저 |
| 쿠키 Secure/HttpOnly/Path/Domain/SameSite·삭제 / 캐시 | HTTPS에서 기대 전송, cross-site/스크립트 접근 제한. 응답 no-store | Windows 브라우저↔WSL 및 HTTPS 브라우저 하네스 |
| 앱 재시작/다중 worker, DB 장애 | 같은 AuthSession 인식/폐기, 제한 bucket 공유. 메모리 fallback 없이 503 | 실제 두 프로세스+PostgreSQL |
| 반복 로그인 / 없는 ID / NAT / 병렬 공격 | 제한 카운터 원자성, 일반 429, 오류 응답의 계정 구별 방지 | 단위 + DB 동시 요청/부하 |
| 최초 명령 중복·동시 실행·오용·DB 오류·감사 실패 | 한 Master/조직만 생성. 기존 조직/계정 덮어쓰기·부분 생성 없음, 잘못된 대상 non-zero | CLI subprocess + 전용 DB |
| 마지막 활성 Master 둘을 동시에 차단/강등/재설정 | 적어도 하나의 사용 가능한 Master 유지. 미활성 초대 계정은 대체로 세지 않음 | 실제 DB 동시성 |
| 실제 지점/계정 준비·활성화 | bootstrap→Master login→Branch 생성→Branch Admin 발급→본인 설정→로그인→허용 지점 조회 성공 | 강제 사용자 주입 없는 end-to-end API/DB |
| 민감 정보·감사 | 응답/로그/오류/감사에 비밀번호·해시·원본 token·지급 설정 없음. 중요 변경+감사 원자성 | capture 검사 + 실제 DB |
| migration | 빈 DB/이전 revision 적용과 제약·기존 데이터 보존, 복구 경로 확인 | 전용 PostgreSQL migration 검사 |

`bash check.sh fast`에는 DB 없는 Scope/계정 정책·시간/오류·해시 adapter·CSRF 판정·설정 실패와 Import Linter 계약 검사를 추가하는 안이다. 테스트에서 VerifiedCaller를 강제 주입하면 **인가 단위 검사**로만 표기하며 실제 인증 완료 증거로 사용하지 않는다. 기존 계층 검사 계약은 실제 IAM/Organization 코드 배치가 승인될 때 확장하고 검사 삭제로 통과시키지 않는다.

`bash check.sh db`에는 위의 실제 로그인→DB→쿠키→인가·철회 흐름, 경쟁·감사 rollback·migration을 `postgres` 필수 검사로 추가한다. 기존 전용 URL/Compose 소유권 검사와 missing/skip/xfail/미수집 실패 정책을 유지한다. 현행 빈 revision 전제의 `alembic current` 검사는 실제 승인된 head 확인으로 변경해야 하며 임의 stamp/create_all로 통과시키지 않는다. migration 검사는 전용 대상 확인 후 별도 소유 DB/schema에 격리하고 개발 DB reset·볼륨 삭제를 사용하지 않는다.

브라우저 검사는 별도 경로로 제안한다. Playwright 같은 실제 브라우저 도구·지원 브라우저·HTTPS 하네스는 T-06/07과 ARCH-004에서 선정한다. 현재 fast/db에 브라우저 실행기가 있다고 가정하지 않는다. TestClient가 Cookie 헤더를 보냈다는 사실은 브라우저의 Secure/SameSite/CSRF 동작 검증이 아니다. 브라우저 검증이 빠졌다면 서버 검사 통과와 분리해 미검증으로 보고한다.

## 10. 구현 전 결정과 종료 조건

첫 구현의 의존성은 [결정안 D01~D12](iam-001-decision-pack.md)에서 제품·운영 정책의 사용자 결정, 기술 선택 검토, 담당자의 구현/하네스 상세로 나눠 확인한다. C7/C8 외 실제 기록/보안 상태·보존/운영 접근 게이트는 유지하며 모든 하네스 선택에 별도 사용자 승인을 요구하지 않는다. 인증·최소 UoW·개발 Bootstrap·ID/암호·활성화 전달·제한 상태 전이·수명/중요 관리·기기/철회 순서·반복 제한·Cookie/CSRF·개발 기록 범위를 구체 질문/추천/대안 영향/기존 게이트와 함께 구분했다. 기존 추천과 이전 상태 복원 보고의 “ㅇㅋ”는 승인 근거가 아니다.

재설정·본인 암호/ID 변경·복구·추가/마지막 Master의 구현은 F01~F04 후속 범위로, 운영 전달·보존/정리·MFA/배포/품질은 O01~O03으로 미룬다. 해당 기능을 앞당기면 필요한 결정을 먼저 받는다. 유일 Master의 재설정을 막기만 해서는 암호 분실을 복구할 수 없다. S1에서는 개발 사용을 중단하고, 실제 운영 전에는 bootstrap 재사용과 구별된 비상 복구를 완성해야 한다.

S1 완료와 전체 IAM-001 완료는 2절 및 결정안의 인수 기준으로 분리한다. 코드·테스트·migration 작성은 이번 범위가 아니며 정책 답변 후에도 별도 구현 지시 없이 시작하지 않는다.

Branch Admin의 신규 Operator/Trainer 발급·E5 기존 역할 관리 Actor/Scope와 Operator 단일 Branch는 승인됐다. 대상 상태/연결·역할 조합·교차 업무/비활성 지점·정산 공개의 잔여는 각각 MB-004, ARCH-001, MB-001/005, MB-008, MB-006 OPEN이다. S1의 축소는 승인된 후속 v1 기능의 영구 금지가 아니며 미결정 권한도 선행 제공하지 않는다. 보상 설정 변경 권한을 계정·역할 변경 권한으로 확대하지 않는다.

이번 설계 완료는 요구사항/OPEN 추적, 준비 경로, 선택 비교, 상태/보안/인가·데이터·API·검증 초안의 문서 검토를 뜻한다. 인증 패키지 설치, 코드/SQLAlchemy 모델/Alembic revision 작성, fast/db 재실행, 브라우저·운영 검증은 이 설계 작업에서 수행하지 않는다. 위 검증표는 모두 후속 계획이며, 본 문서의 추천이나 ADR 초안이 사용자 승인으로 자동 승격되지 않는다. 완료 후 업무 구현을 자동 시작하지 않는다.

초기 초안 작성 당시 문서 검증 기록(2026-09-18, 이번 재검토의 실행 결과 아님): IAM-001·ADR-0004·Architecture README의 로컬 링크/앵커 48개와 IAM-001이 참조한 Product/기술 게이트 ID 24개의 존재를 확인했다. 초기 설정→실제 계정 발급/활성화→로그인→Scope 제한→철회의 연결과 권한 변경/처리 중 요청의 경계를 대조했다. 시작 시 파일 해시와 비교해 기존 수정은 Architecture README의 안내 링크에 한정되고, backend/전체·Product·승인 ADR·FOUNDATION/WSL 기록은 그대로임을 확인했다. 신규 파일은 이 설계와 ADR-0004뿐이다. 인수 사례 19개는 미실행 계획이며 이 문서 점검이 인증 보안 시험을 대신하지 않는다.

이번 범위 축소 검토의 변경·문서 검사 결과는 [결정안](iam-001-decision-pack.md)에 별도로 기록한다. 초기 19개 인수 사례 중 S2 대상은 후속 계획으로 유지하고 S1 실행 결과로 세지 않는다.

2026-10-12 이후 남은 결정/검토: B/A 표로 해결된 정책을 재질문하지 않는다. 개발 Bootstrap의 구체 경로/보호 입력·전달/수신자 확인·중요 관리 재인증·반복 로그인 제한·실제 기록 수집/접근/보존과 비상복구/MFA 수단·S1/S2 범위는 별도 검토 대상이다. 라이브러리/차단목록·정규화·Caller/역할/대상 계약·UoW/FK/잠금/멱등성은 설계자가 구체화하고 실제 검사로 증명할 기술 상세다. 가상 하네스와 영속 서비스 정책은 분리한다. 사용자가 별도 구현을 지시하기 전에는 코드·migration을 작성하지 않는다.

2026-10-12 K3 후속: 첫 개발 기능 범위/순서만 승인됐으며 D02/D07의 구체 계약/상태 전이·인수/모듈/UoW/잠금 상세까지 채택된 것은 아니다. 설계자가 기존 승인 정책으로 기술/하네스 세부를 구체화하고 정책·권한/관측 결과 변경이 필요한 때만 확인한다. 코드·테스트·migration 작성/실행과 실제 운영은 이번 답변으로 시작하지 않는다. [2026-10-12 K 일괄 승인](../product/product-decisions.md#review-20261012-k-batch).

AB3–AB6 갱신: reset30분/운영 관리자 비밀번호+사용자검증 Passkey/비상 업무책임자 승인·별도 운영담당자 실행/Chrome·Edge·Safari 최신2개 안정 주버전 목표는 확정됐다. 실제 계정/등록·분실/복구/자격·운영/보존/호환성·검증은 후속이며 K3/X1 S1·구체 계약 PROPOSED·별도 구현 지시와 구별한다. [AB 승인](../product/product-decisions.md#review-20261013-ab-batch).

<a id="review-20261013-issuance-response-loss"></a>
## 11. 2026-10-13 재검토 — S1 발급 응답 유실

상태: **X1=1 기능 보완 승인 / 구체 계약 PROPOSED**. 사용자 후속 답변 “1”로 [X1 기능 보완](../product/product-decisions.md#review-20261013-x-batch)을 승인했다. W1/W2 답변과 구별하며 [구체 계약 후보/인수 경로](iam-001-decision-pack.md#review-20261013-x1-proposal)는 계속 기술 검토 대상이다.

기존 S1 초안의 Branch Admin 발급 응답 유실/account ID 미확보만으로 개발 run 중단/S2 재조회 보완을 요구하던 한계는 X1의 정확한 조회/설정 대기 링크 재발급으로 대체했다. 이는 최초 Master 분실/복구와 별개이며 계정 생성이 실제로 commit됐는지 확인할 수 없는 통신 결과 문제다. Login ID 중복 생성 재시도/원래 설정 token 사후 조회로 해결하지 않는다.

X1=1 승인 기능은 현재 Master가 자기 Organization의 S1 Branch Admin을 정확한 Login ID로 조회하여 ID/현재 상태·Scope/version을 확인하고, PENDING_SETUP이면 기존 재발급 계약으로 새 30분 일회용 설정 링크를 받는 흐름이다. 비Master/다른 조직·목록/부분 검색·ACTIVE/DISABLED 강제 reset·추가 역할 관리와 원문 token 재조회는 포함하지 않는다. 생성 응답 유실 후 실제 DB 결과 확인·권한/상태 변경 경합·감사 실패/링크 단일 사용을 인수에 추가한다. X1=2의 기존 S1 중단/S2 보완은 선택하지 않았다. 유일 Master 분실/DB 불능 등 다른 중단 조건·계정 수명/운영 복구 후속 의무는 유지한다.

현재 §8 전체 IAM API 후보를 S1에 일괄 추가하지 않는다. 결정안의 좁은 S1 API/인수·응답 유실 설명을 이번 기능 보완 범위에 맞췄으며, 구체 모듈/공개 계약/UoW/잠금 PROPOSED·직접 DB 읽기 예외 0건과 K3 범위/별도 구현 지시 경계를 유지한다. 코드/migration·의존성/lockfile 변경·제품/DB/브라우저 검사는 수행하지 않았다.


<a id="s1-contract-review-20261013"></a>
## 12. S1 기술계약 구체화와 개발 인계안

상태: **PROPOSED / 구현 미착수**. [현재 S1 기술계약 TX01–TX06](iam-001-decision-pack.md#review-20261013-s1-contracts)과 [검토용 개발 전달안](iam-001-decision-pack.md#s1-implementation-handoff-20261013)을 우선 확인한다. AB 정책 승인에 기술계약/코드 작성까지 포함하지 않는다.

구체화한 모호함은 Account 변경 충돌용 row_version과 인증 철회용 security_version 분리, 관리 명령의 target 효과와 실행자 인증 검증 분리, 최초 설정 응답의 setup_link/완료POST setup_token 구별이다. 최신 S1 후보의 발급/재발급은 신뢰한 HTTPS origin의 일회용 링크를 한 번 반환하고 GET/조회로 token을 소비/재노출하지 않는다. 원본 §8의 전체 비교 API 표를 현재 S1 계약으로 일괄 구현하지 않는다.

UoW 내부의 현재 인가/경로별 잠금·같은 DBSession/private adapter 조립·공개 계약/업무 모듈 Cookie·ORM 비의존과 실패/HTTP 상태 차이의 계정 비노출을 연결했다. 기존 Foundation은 자원 수명/기본 import 검사일 뿐 새 계약의 증거가 아니다. 해시/차단목록·제한/자원·실제 HTTPS/DB/worker·migration/import 사전검증과 S1 인수는 남아 있다. 공급 적합성/관련 게이트를 충족한 뒤에만 앱 구현 단계로 진행하는 전달안이며 K3/X1 범위·AB 후속/운영 준비·구체 계약 PROPOSED/직접 DB 읽기 예외0건·별도 구현 지시 경계를 유지한다. V-138은 미구성·미실행이다.
