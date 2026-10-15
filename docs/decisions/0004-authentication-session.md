# ADR-0004 — v1 PostgreSQL 로그인 상태와 브라우저 쿠키 인증

Status: **ACCEPTED**

작성일: 2026-09-18. 채택일: 2026-10-12. Approval source: 사용자 일괄 답변 “A4,5번은 2번. 나머지 전부 1번. A1은 v1에서 1번으로 진행하되 추후 버전에서 jwt사용을 고려.” A1의 v1 PG 서버 AuthSession+opaque Cookie 방식 채택에 한정한다. JWT는 후속 버전의 재검토 후보이며 의무 전환/도입 시점 승인이 아니다.

Scope: v1 브라우저 인증의 PG 서버 저장 AuthSession+opaque Cookie 방식만 채택한다. 라이브러리/해시·쿠키/CSRF·모듈/계약/UoW/잠금·배포의 상세 후보는 이 ACCEPTED 범위에 포함하지 않는다. 전체 비교·정책 후보는 [IAM-001 설계](../architecture/iam-001-design.md), 첫 증분의 승인 질문·정확한 범위·인수 조건은 [IAM-001 결정안](../architecture/iam-001-decision-pack.md)이다. [ADR-0001](0001-backend-stack.md)~[ADR-0003](0003-foundation-tooling.md)의 승인 기술을 대체하지 않으며, 6개 모듈·운영 배포·계정 정책을 일괄 승인하지 않는다.

## Context

Master Admin은 자기 Organization 전체 지점, Branch Admin은 자신의 단일 지점에 접근해야 한다. Trainer 로그인도 v1에 포함된다. 서버는 클라이언트가 지정한 역할/지점을 권한으로 믿지 않아야 하며, 로그아웃·계정 차단·권한 축소 이후 이전 로그인 상태의 이용을 제한해야 한다. 제품 근거는 PR-001/020/021/026/029/030, NFR-001과 PD-019다. 계정 수명·세부 Permission은 ARCH-001/002 OPEN이다.

현재 WSL Ubuntu의 기반은 검증됐지만 인증 코드·업무 schema는 없다. PostgreSQL을 공유하는 단일 백엔드이므로 초기부터 독립 인증 서버·브로커·캐시를 전제할 필요가 없다. 운영 HTTPS/프록시/프론트엔드는 T-06/07 후속이다.

## Decision

v1 브라우저 인증은 **PostgreSQL에 저장하는 AuthSession과 무작위 opaque 식별자 쿠키**를 채택한다. token digest, 계정·수명·폐기·보안 버전을 서버에서 확인하고 매 요청의 현재 역할/Scope로 검증된 호출자 정보를 만든다. 프로세스 메모리를 인증 원본으로 사용하지 않는다. 쿠키 삭제와 서버 상태 폐기를 함께 처리한다.

업무 모듈에 Cookie/JWT 해석을 퍼뜨리지 않고 서버가 검증한 Caller로 신원과 대상 지점 행위 권한을 분리하는 기존 원칙을 유지한다. VerifiedCaller의 구체 계약·역할/데이터 소유권/UoW는 PROPOSED다. [2026-10-12 일괄 승인](../product/product-decisions.md#review-20261012-batch)의 전 역할 idle 30분/absolute 8시간, 복수 로그인/현재 로그인 logout, 관리 역할/관리 Branch 변경 전체 재로그인, Master 전용 계정 차단/복구·관리자 reset, 복수 Master/마지막 Master 보호·운영 전 MFA는 승인 정책이다. 후속 [2026-10-12 C 일괄 승인](../product/product-decisions.md#review-20261012-c-batch)에서 추가 관리 비밀번호 재확인 없음(C1), 계정 실패 제한/자격·ID 변경 철회/마지막 Master reset 보호·인증 감사(C2–C8)를 확정했다. 처리 중 요청의 선후·나머지 계정 전이/복구·저장 계약은 후속이다.

라이브러리/구체 구현 후보는 기존 FastAPI/Starlette 요청·응답/쿠키 기능, Python `secrets`/`hashlib`, 신규 후보 `pwdlib[argon2]`와 `argon2-cffi`다. 이번 인증 방식 채택으로 새 라이브러리/버전·해시 비용까지 채택하지 않는다. 비밀번호용 Argon2id는 라이브러리로 수행하고 자체 암호 알고리즘을 작성하지 않는다. 해시 파라미터와 패키지 버전은 실제 지원·보안·부하 검토 후 별도 고정한다. 세션/CSRF 수명 조정은 프로젝트가 검증해야 할 구현 책임이다.

동일 origin 프론트엔드/API, HTTPS와 Secure/HttpOnly/host-only 쿠키, 서버 저장 CSRF token을 우선 후보로 둔다. 로그인 전 CSRF 준비 상태도 필요하며 로그인 성공 후 새 인증 상태로 교체한다. 배포 구성이 확정되었다는 의미는 아니다.

## 첫 증분의 제한과 결정 시점

S1은 영속 PostgreSQL 기반 서비스의 첫 기능 증분이며, 첫 인수는 가상 데이터의 격리된 로컬 환경에서 수행한다. 가상 데이터·24시간·영역 폐기는 별도 실험/인수 하네스 실행 관리 후보이며 제품 수명/삭제 기본값으로 넣지 않는다. 실제 Bootstrap→Master/Branch Admin 로그인→서버 지점 Scope→logout/차단/Scope 변경 철회와 감사 원자성까지 검증한다. Branch Admin 발급·활성화·미활성 token 재발급은 포함하고, 활성 계정 reset/복구·추가 Master·Master 전이는 S2로 분리한다. C1에 따라 중요 계정 관리의 5분 이내 비밀번호 확인/강제 재로그인·별도 재인증 후보는 미채택이다. 유효 인증/현재 인가·CSRF/만료·운영 전 MFA와 C3 본인 암호 변경의 현재 암호 검증은 유지한다.

구현 전 의존성은 결정안 D01~D12에 모았으며 제품·운영 정책의 사용자 결정, 기술 검토, 담당자 구현/하네스 상세를 구분한다. 불필요한 하네스 정책 승인을 요구하지 않으며 기술 실험 성공은 선택 승인과 다르다. Argon2 비용·라이브러리 잠금 버전·인덱스·하네스 세부는 제한적으로 위임할 후보이며 사용자에게 모든 구현 선택을 요구하지 않는다. Product OPEN·T-01/T-05/T-09와 구체 UoW/FK/잠금은 승인 전 PROPOSED다. 공유 IP 제한 수치는 기존 초안의 30회에서 D10의 개발 후보 100회로 조정했으며 어느 값도 승인되지 않았다.

유일 Master의 재설정 거부만으로 복구 가능하다고 주장하지 않는다. S1에서 분실 시 사용 중단이라는 한계는 D07에서 승인 대상이고, 운영 전에는 별도 복구 절차가 필수다. 실험/인수 하네스의 작업 소유 영역 폐기로 영속 서비스의 기록 정책을 대신하지 않는다. 실제 제품의 C7/C8 로그인 최소 수집/앱 감사 열람 원칙 외 보존/삭제·보안 상태/운영 접근은 D12/LEGAL-001/O02의 게이트를 유지하며, 기존 개발/테스트 DB·볼륨은 실험 정리 대상이 아니다. MFA 없는 개발 검증은 무MFA 운영 승인과 다르다. 운영 담당 실명·최종 호스팅은 첫 로컬 구현의 선행조건이 아니다.

## Alternatives and trade-offs

| 대안 | 장점 | 현재 선택 시 비용/한계 |
| --- | --- | --- |
| access JWT + 회전하는 refresh token | 서비스별 서명 로컬 검증, 향후 표준 인증 연계에 활용 가능 | access 만료 전 차단을 보장하려면 철회/현재 계정 버전 조회 필요. refresh 회전·재사용 탐지·키 교체가 추가됨 |
| Starlette SessionMiddleware의 서명 쿠키 | 프레임워크 제공 기능으로 서명/쿠키 처리를 줄일 수 있음 | 읽을 수 있는 클라이언트 저장 상태이며 이 ADR의 DB AuthSession 구현체가 아님. 개별 서버 철회·현재 권한 검증 문제를 별도로 풀어야 함 |
| FastAPI Users Cookie + Database strategy | 계정/로그인·인증 transport/strategy를 제공하는 검토 가능한 라이브러리 | 공식 maintenance mode, 기본 SQLAlchemy async 통합. 동기 기반과 관리자 발급·Scope·감사 정책에 대한 조정/검증 필요 |
| 메모리만 사용하는 서버 세션 | 단일 프로세스 실험이 쉬움 | 재시작·여러 worker에서 인증/철회 불일치. 기본안으로 부적합 |

쿠키와 JWT는 각각 전달 수단과 토큰 형식으로 서로 다른 분류다. JWT를 쿠키로 운반하면 CSRF 문제도 그대로 검토해야 한다. Authorization 헤더로 운반하면 브라우저 토큰 저장과 XSS 위험을 검토한다. FastAPI/MSA가 JWT를 의무화하지 않는다. 세부 비교는 IAM-001 3절에 모았다.

## Costs, constraints and review triggers

서버 세션은 요청마다 DB 조회/활동 갱신과 정리 작업을 요구하고 DB 장애에 인증이 영향을 받는다. 인증 DB 실패 시 무검증 접근을 허용하지 않는다. 여러 worker의 rate limit, 계정/세션 폐기 경쟁, 감사 원자성까지 실제 PostgreSQL로 시험해야 한다. 라이브러리 채택이 인가·CSRF·계정 복구의 완성을 보장하지 않는다.

브라우저 쿠키/CSRF 동작은 서버 단위 테스트만으로 검증할 수 없다. 관리자 MFA는 A10 승인으로 실제 운영 시작 전에 필수다. 수단/등록·분실/비상복구와 실제 브라우저/HTTPS 검증은 후속이며 로컬 개발/첫 기능 검증 허용이 무MFA 운영 허용은 아니다. 지점 접근 설계를 지급정보 열람 권한으로 확대하지 않는다.

사용자 A1 단서에 따라 JWT 사용을 후속 버전에서 재검토한다. 별도 앱/외부 인증 제공자, 독립 서비스가 인증 정보를 소비하는 요구, DB 조회 병목의 실측, 라이브러리 유지관리/보안 상태 변화 등을 근거로 별도 ADR을 작성하고 채택 여부를 다시 결정한다. 후속 버전이라는 이유만으로 JWT 자동 전환이나 별도 인증 서비스를 선행하지 않는다. 전환에는 활성 세션 처리, 인증·인가 계약, 키/철회·복구, 사용자 재로그인 비용을 포함한다. 이번에 MSA나 OAuth/OIDC 서버를 만들지 않는다.

## Evidence and validation limits

아래는 초기 초안의 공식 자료 확인 기록(2026-09-18)이다. 이번 범위 재검토에서 다시 확인한 자료는 결정안 말미에 구분했다. 초기 release 버전/설치 소스 관찰을 이번에 재실행한 것으로 보고하지 않는다. 유지관리 관찰은 장기 지원 보장이나 이 프로젝트와의 설치 호환 시험이 아니다.

- [FastAPI 보안 안내](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/): pwdlib/Argon2와 JWT 선택 시 PyJWT 사용 예시.
- [Starlette middleware 문서](https://raw.githubusercontent.com/Kludex/starlette/main/docs/middleware.md): SessionMiddleware의 서명 쿠키 특성. 설치된 Starlette 1.6.0 소스와 함께 확인.
- [pwdlib release 기록](https://github.com/frankie567/pwdlib/releases), [argon2-cffi parameter 문서](https://argon2-cffi.readthedocs.io/en/stable/parameters.html): 유지보수 변경 및 해시 파라미터 측정 기능 확인.
- [FastAPI Users 저장소](https://github.com/fastapi-users/fastapi-users), [DB strategy 문서](https://fastapi-users.github.io/fastapi-users/latest/configuration/authentication/strategies/database/): transport/strategy와 maintenance mode 확인.
- [PyJWT changelog](https://pyjwt.readthedocs.io/en/stable/changelog.html): 대안 라이브러리의 검증/보안 변경 기록 확인.
- [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html): 세션 갱신/철회 및 로그인 CSRF 설계 참고.

구현 진입에는 이번 A1 채택과 [2026-10-12 일괄 승인](../product/product-decisions.md#review-20261012-batch)을 반영한 나머지 정책/기술 검토·범위 인계와 별도 구현 지시가 필요하다. 본 ADR의 v1 인증 방식만 ACCEPTED이며 다른 기술 초안·S1/S2 범위는 일괄 승인하지 않는다. 코드·의존성·migration·실행 검사 변경은 없다.
