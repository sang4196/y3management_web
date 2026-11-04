# IAM-014 비밀번호 전용 인증 로컬 인수 결과

2026-11-05 **설계자 로컬 인수 PASS**. [승인 PW-1–PW-6](../product/product-decisions.md#review-20261031-password-only),
[ADR-0005](../decisions/0005-password-only-authentication.md), [설계](iam-014-password-only-design.md),
[전환 계약](iam-014-password-only-transition.md)을 구현했다.
정확한 소스·노드별 실행 출처·브라우저 개별 판정은 [최소 인수 근거](iam-014-password-only-review.json)에 남긴다.
구현 parent는 `774661b33086334fe4ddf30b92de27432814defd`다.

## 구현한 동작

- 현재 지원하는 Master·Branch Admin·Trainer·겸임 계정은 ID와 비밀번호로 로그인한다. `Y3_IAM_MODE=password`를 명시하며 과거 `mfa`/`s1_password` 설정은 거부한다. PostgreSQL AuthSession과 무작위 식별자 Cookie를 유지한다.
- Passkey 등록·추가/삭제·로그인·분실 재등록 화면/API/CLI 옵션과 현행 WebAuthn 의존성을 제거했다. 최초 Master TTY 준비, 관리자·Trainer 발급과 수신자의 직접 암호 설정, 본인 변경, 정상 Master 재설정, 승인된 비상 암호 복구와 인계를 비밀번호 흐름으로 연결했다. 설정·복구 완료 후 명시적으로 로그인한다.
- 현재 Role/Organization/Branch/Trainer 사실, 민감 보상 설정의 Home Scope, noSelf·마지막 Master, 비밀번호·C2 실패 제한, CSRF·Cookie·철회·감사 정책을 유지했다. 미지원 역할·업무를 새로 구현하지 않았다.
- 새 `0014_password_only`는 policy2 marker와 전환 사실, 신규 암호 복구 사건·원본·typed 감사를 저장한다. 기존 계정/암호/역할/소속/업무/C2·원래 감사/사건/키 이력을 보존하면서 구 인증 권한을 폐기한다. 분류 불능은 전환을 중단하고 임시 MFA hash를 계정 암호로 승격하지 않는다.
- 전환은 유지보수·단일 호스트 ProcessGuard 및 명시 migration 절차를 사용한다. 앱/UoW의 정책 검사, 원래 기한/단회성·정확한 FK/lineage, 원자 rollback/COMMIT 불명 대사와 기존 bounded GC를 검증했다. 실제 원본 DB에는 적용하지 않았다.
- 데이터가 있는 0014의 하향은 DDL 전에 거부한다. 모든 관련 업무/auth/audit 자료와 전환 집계가 비고 singleton이 정확한 상태만 빈 왕복을 허용한다. 원본 0001–0013은 byte 그대로다.

`webauthn`, `cbor2`, `cryptography`, `pyasn1`, `pyasn1-modules`, `pyopenssl`을 현재 lock에서 제거했다.
추가 패키지와 공통 패키지 버전 변경은 0이다. 현재 앱/CLI/수집은 WebAuthn 없이 동작한다.

## 실제 독립 검증

최종 동결은 소스 **268개/Backend174개**,
SHA256 `01d623f235e7e52ddbbf6dee7e2e29caaef19d66930f2c7f684e1e618a068e53`다.
개발자와 분리된 담당자가 실행했고, 브라우저 검사 일부의 작성 관계와 별도 정적 검토를 근거 JSON에 명시했다.

| 검사 | 실제 결과 |
| --- | --- |
| 최종 R6 fast | pytest197 passed, Ruff/format137·mypy119·Import8 통과, 다섯 명령 각각 exit0 |
| PostgreSQL 승인 분할 | R3 261 + R4 storage15 + R5 94 + R6 256 = 고유626 passed |
| 분할의 정확성 | 전체 node 합집합626, 교집합/누락/중복/최종 skip·xfail·xpass·미실행0 |
| 같은 R3의 실제 HTTPS | native7사례/물리 보고7개/10manifest의283조건 전부 literal true |

**PostgreSQL626은 단일 전체 실행 PASS가 아니다.** R3/R4/R5의 원래 실행은 각각
261/1setupERROR/364미실행, 21/1failure/343미실행, 98/1failure/251미실행으로 exit1이었다.
그 실행의 소스가 같은 실제 통과분만 명시 승인한 분할로 보존했다. 바뀐 모듈의 기존 통과 사례도
보수적으로 재선정해 한 번만 집계했다. 현재 앱/CLI/UI/공통 fixture/helper/migration/lock은 R3부터 그대로이며,
후속 변경은 지정 테스트 배선·역사 준비·폐기 factor 단언뿐이다. raw 차이와 비대상 함수/fixture/전역 AST의
불변을 구분했다. 모든 동적 외부 의존의 동등성을 형식 증명했다고 주장하지 않는다.

fast는 기존 `check.sh fast` 구성의 다섯 locked 명령을 개별 실행했고 pytest 계측 인수는 상위 CLI에만 전달했다.
DB 실행도 기존 `--require-postgres`와 소유권 확인된 전용 Compose DB/고유 schema를 사용했다.
전체823 수집과 `--setup-plan`의 fixture lookup0은 준비 근거다. 실제 본문이 실행되지 않은 이 명령들의
필수 PG guard exit1은 유지했으며 실행 PASS로 계산하지 않았다.

브라우저는 Chromium `151.0.7922.34`, 실제 신뢰 HTTPS·sandbox·격리 NSS/프로필로 실행했다.
283조건은 PostgreSQL 사례 안의 판정이므로 테스트 수에 더하지 않는다. R6에서 새 native를 실행한 것으로
보고하지 않는다. 시스템 CA/사용자 NSS의 원래4파일, source 전체/HEAD/branch/index/main을 전후 대조했다.

## 검토에서 보완한 경계

기존 관리자 C3와 일부 관리 쓰기에 필수 감사 뒤 원래 Actor 기한 검사가 빠진 것을 발견했다.
실제 DB에서 기한을 넘긴 C3가204로 성공하는 반례를 재현했다. 일반 관리 명령은 감사·현재 사실 읽기 뒤
마지막 DB clock으로 원래 idle/absolute를 검사하고 같은 시각으로 성공 활동만 갱신한다.
C3는 별도 `PasswordChangeActor`가 예상 hash·version 증가/자기 전 세션 철회/설정 자격 소비만 허용하는
후상태 HMAC을 검사한다. 감사 후 원래 기한을 넘으면 전체 rollback하고 C3 활동은 갱신하지 않는다.
기존 Trainer 역할 자기 철회 특례는 그대로다. 55사례에는 별도 연결이 실제 audit INSERT를 막는
`pg_blocking_pids` 증거와 기한 경과·해제 후401/원자 rollback4개가 포함된다.

비상 암호 복구 성공 후 이미 철회된 AUTH cookie가 남던 것을 정상 reset과 같이 AUTH/PREAUTH 삭제로 보완했다.
원래 실패의 복합 판정은 자동 로그인이나 소비된 자격 재사용의 발생 증거가 아니다.
정상 로그인 중 수신자 복구 요청은 기존409로 거부하고 그 세션을 보존한다. 별도 익명 context에서
같은 소비 원본은401이다. 기존15 native 조건을 유지하고 로그인 중409 조건1개를 추가했다.

그 외 fixture 누락/옛 `mfa` 인자와 역사 migration 시작점 오류를 테스트에서 바로잡았다.
S2/S2b/S2c의6개 원래 revision 계약은 고정 원본 pin/원래 lock/실제 CLI·API·fixture·test로 실행한다.
원래 ownership 코드가 현재와 같은지 확인하고 모듈 위치 metadata만 실제 Compose 경로로 연결한다.
원래 배포 재현이나 현재 앱의 MFA 실행을 뜻하지 않는다. 현재 populated0014의 보호를 약화하거나
자료를 지워 왕복 조건을 만들지 않는다. 원래 child exit255가 어떤 선행 guard에 도달했는지는 추가 관측하지 않았다.

audience의 옛 `weak`/`key` 무효-factor 단언은 은퇴했다. 현재 policy2 password·키0의 명시적 positive control은
관리 권한이 없는 유효 인증의403/계정 audience401을 정확히 검사한다. 만료·철회·epoch·차단·암호 reset 등
무효 상태의401과 catch-inside-UoW의 no-touch/full snapshot 검사는 유지한다. 모순된 legacy pending flag도
fail-closed401로 유지한다. 키0 검사를 역사 키 보존/UV 검증으로 설명하지 않는다.

초기 실행 옵션·테스트 래퍼 접근·타입 오류와 모든 원래 실패/중단 수치는 최소 근거에 구분했다.
개발 분할 PASS와 이전 IAM 인수 수치를 최종 성적에 합산하지 않는다. 기존 Starlette HTTPX fallback/
AnyIO BlockingPortal alias 경고2개는 숨기지 않았다.

## 정리·한계·다음 단계

자동 실행은 기존 fixture의 소유권 guard로 자기 schema/process/코드 추출본/가상환경/로그·프로필 폴더를
정리했다. 마지막 R6에서 관찰한253 schema·203 OS identity·897 PG identity의 부재와 baseline DB schema/table
복원을 대조했다. 이는 관찰 목록과 fixture 정리를 보충하며 모든 외부 자원의 목록이라는 주장은 아니다.
설계자도 채택 분할의 실행 폴더 부재와 신뢰4파일/소스/Git 불변을 확인했다.
최소 근거를 저장한 뒤 완료된 원본 로그·중복 보고·검토용 사본은 정리하고 현재 도구/원본 데이터는 유지한다.

원본/운영 DB 전환, 보호 backup/restore, 배포/production 허용, 실물 기기·다른 브라우저·모바일 전체는 별도다.
Operator 미구현 업무·Member 인증/PT·Pass·지급·Settlement를 이번 인수로 검증하지 않는다.
Product OPEN22/CLOSED8·PD OPEN1/CLOSED26 및 다른 ADR/전역 모듈 PROPOSED는 그대로다.

후속은 전담 한글 상세 커밋·일반 feature push다. 기존 미답변인 **설정 전 계정 차단/복구**와
**Login ID 변경 대상 상태 확장**은 구현하지 않았고 다음 사용자 결정으로 남긴다.
현재 실행 안내는 [Backend IAM-014](../../backend/README.md#iam-014-비밀번호-전용-개발-실행)를 따른다.
