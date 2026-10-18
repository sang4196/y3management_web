# IAM-005 — 제한된 로컬 MFA-A

상태: 구현·개발 대상 검증 완료, 독립 검증/설계자 인수/운영 허용 전이다.
실행 근거와 한계는 [개발 결과](iam-005-mfa-a-results.md)를 따른다.
기준 HEAD는 `c58cd50668244fcdc0833a40d10e38ff068e803e`이며 작업 브랜치는
`codex/iam-mfa-a`다. 제품 정책의 원본은 [Product 결정](../product/product-decisions.md)의
2026-10-18 M3–M6와 앞선 M1/M2·AB4/AB5다. 이 문서는 해당 정책을 재승인하거나 바꾸지 않는다.

## 범위와 모드

실제 설치 CLI의 최초 Master → 첫 키 등록 → 비밀번호+UV Passkey 로그인,
정상 MFA 본인의 추가 키 등록과 어느 한 키로 로그인, 실제 Branch Admin 발급/본인 설정을 포함한다.
삭제(M4), 분실 복구(M2/M5), 추가 Master(M6), 관리자 password reset, AB5 운영 복구는 후속이다.

`Y3_IAM_ENABLED=true`이면 `Y3_IAM_MODE`를 명시해야 한다. `s1_password`는 과거 제한된
개발 예외, `mfa`는 이번 증분이다. 0개 키·약한 세션·설정 누락에 따른 자동 fallback은 없다.
기존 AuthSession의 assurance는 `password`이며 migration/모드 변경으로 `password_uv`가 되지 않는다.
MFA 모드에서 모든 기존 authenticate 경로가 MFA 수준을 요구한다. production 거부는 유지한다.

## 공개 흐름

기존 `/api/v1` 접두어와 same-origin HTTPS·JSON·CSRF 검사를 유지한다.

| API/CLI | 계약 |
| --- | --- |
| `bootstrap-initial-master --enrollment-file /absolute/private/file` | TTY 비밀번호 입력·기존 설치 잠금·최초 Master 및 30분 설치 허가를 함께 commit |
| `POST /auth/passkeys/enrollment/options` | `setup_token`, 새 관리자일 때 `new_password`. preauth CSRF 필요. 설치/설정 권한으로만 첫 키 준비 |
| `POST /auth/passkeys/enrollment/verify` | `{credential: WebAuthn JSON}`와 ceremony CSRF. 등록 후 자동 로그인 없음 |
| `POST /auth/login` | MFA 모드에서 비밀번호 성공은 request options와 제한 cookie만 반환 |
| `POST /auth/login/passkey/verify` | 최종 두 요소 검증·현재 계정/credential/attempt 결합 확인 후 업무 AuthSession |
| `POST /auth/passkeys/options` | 정상 MFA 본인·CSRF. 추가 비밀번호 확인 없음 |
| `POST /auth/passkeys/verify` | 최초 options를 허가한 동일 계정·동일 MFA 세션의 최종 유효성 확인과 새 키 UV |

Ceremony 응답은 `publicKey`, `csrf_token`, `expires_at`이다.
`__Host-y3-ceremony`는 Secure/HttpOnly/SameSite=Lax/Path=/ cookie이며 업무 인증에 사용할 수 없다.
HTTP는 JSON/크기/cookie 변환만 담당한다. Service는 public port와 immutable proof만 받고,
IAM 내부 MFA adapter가 pinned 검증 라이브러리를 호출한다. 모듈 간 private 접근 금지 검사를 확장했다.
`/enroll`, `/activate`, `/login`, `/passkeys`의 브라우저 화면은 native create/get을 사용한다.
설정 허가 fragment는 즉시 제거하고 URL·로그에 보내지 않는다.

## 설치 파일과 계정 설정

설치 파일은 Linux 절대 경로만 받는다. 경로 각 구성 요소를 descriptor-relative `O_NOFOLLOW`로
열고, 마지막 부모의 현재 사용자 소유권과 정확한 0700을 확인한다. 파일은 O_EXCL/0600으로 만든다.
원본 허가는 stdin/stdout/argv에 출력하지 않는다. 파일과 디렉터리를 fsync한 뒤 business COMMIT한다.
DB 이전 실패/명확 rollback에서는 자기 inode의 파일만 제거한다. COMMIT ACK가 불명확하면 exit 2와
`INSTALLATION_COMMIT_UNKNOWN_RETAIN_PRIVATE_FILE`을 반환하고 파일을 보존한다. 다시 bootstrap하거나
SQL로 복구하지 않는다. 실제 설치 여부와 전달 성공을 확인한 뒤 해당 파일을 정리한다. 허가 만료 뒤
유일 Master 관리 불능은 이 증분의 복구 가능 상태라고 주장하지 않고 후속 복구/검수로 남긴다.

새 관리자는 기존 설정 credential의 account/version/expiry에 묶인 별도 5분 ceremony에 password hash를
임시 보관한다. `PENDING_SETUP`과 계정의 null password hash는 첫 키 검증까지 유지한다.
최종 등록에서 키·password hash·ACTIVE·version 증가·허가 소비·감사를 한 UoW로 commit한다.
설정 재시작은 이전 파생 ceremony를 소비하고 임시 hash를 제거한다. 설정 재발급은 원본 credential과
row_version을 바꿔 모든 이전 파생 권한을 거부한다. 만료/GC는 파생 hash도 제거한다.
설치 허가 30분은 제한된 설치 작업의 기술 상한이며 M5 운영 복구 완료를 의미하지 않는다.

## WebAuthn 검증

`webauthn==3.0.1`의 배포 wheel API를 Python 3.13.15에서 확인했다.
[공식 배포 metadata](https://pypi.org/pypi/webauthn/3.0.1/json)와
[원본 저장소](https://github.com/duo-labs/py_webauthn)를 근거로 선택했다.
기존 직접/무관 패키지 버전은 보존하고 필요한 전이 의존성만 lock했다.

RP ID는 설정된 canonical HTTPS origin의 hostname이다. 요청 Host에서 유도하지 않는다.
user.id는 변경 가능한 login_id가 아닌 Account UUID의 bytes다. 서버가 challenge/purpose/계정/version/
만료를 저장하고, 라이브러리가 type·RP hash·origin·서명·UP·UV·알고리즘·counter·backup flags를 검사한다.
서버는 crossOrigin 거부, credential 소유 계정, 제공된 userHandle의 UUID 일치도 검사한다.
backup eligibility는 등록 때 값과 같아야 하고 backup state는 검증 결과로 갱신한다.
counter 0인 동기화 키의 값을 임의 증가시키지 않는다. 최신 저장 counter와 검증 snapshot을 다시 비교한다.
개인키/생체 원본은 수집하지 않는다. challenge/원본 WebAuthn payload/cookie/password hash는 감사에 넣지 않는다.

## C2와 자원 경계

단일 reservation UUID와 안정적인 login_budget_key를 password → waiting → verifying → 최종 성공/실패에
계속 사용한다. password 단계의 finish(success), MFA용 새 reserve, 성공에 따른 실패/cooldown 초기화는 없다.
시작/최종 발급 시 reservation의 account/security_version/key와 현재 계정·attempt key를 재결합한다.
알려진 실패는 이 결합을 확인한 계정의 조직/대상에 감사로 귀속하며 unknown/불일치는 일반 최소 기록이다.

password worker lease는 30초, 사용자 대기는 별도 최대 5분, assertion worker는 다시 30초다.
전이는 한 번만 허용하며 재요청으로 대기 시간을 연장하지 않는다. 미완료 시도도 기존 5회 admission에 포함한다.
대기/worker 이탈은 해당 deadline의 실패 한 번으로 계산한다. 실패 관찰 창·cooldown 15분을 보존하기 위해
부모 attempt/budget은 대기 전환 시 최대 21분 이상 필요한 시점까지 보존한다. 새 키/로그인 ceremony는
기존 전역 security capacity에 포함된다. 활성 상태를 쫓아내지 않고 가득 차면 503을 반환한다.
30초 지난 미결합 부모는 기존 GC가 회수하며 live ceremony가 있는 부모는 보존한다.

## 잠금·실패·감사

암호/등록 crypto 검증은 계정/세션 행 잠금 밖에서 수행한다. 추가 등록은 초기 세션 확인 후 검증을 수행하고,
효과 저장 직전에 기존 management authenticate를 다시 실행한다. 최종 세션 idle/absolute/철회 실패이면
키/소비/활동/감사를 모두 rollback한다. 최초 등록은 Account → credential/context 순서로 직렬화하며,
기존 관리 작업의 Installation → 정렬 Account → 정렬 AuthSession 순서를 유지한다.
Security guard를 Account 잠금 안에서 호출하지 않는다. Security admission/단계/finish는 짧은 별도 UoW다.

최종 로그인 business transaction의 `login(success)`는 **두 요소 검증과 AuthSession 저장**을 뜻한다.
HTTP 응답이 사용자에게 전달됐다는 사실이 아니다. business COMMIT와 Security.finish는 분리되어 있으며
두 작업을 원자적이라고 주장하지 않는다. finish/ACK가 실패하면 cookie를 반환하지 않고 서버가 만든 해당
미전달 sid만 철회한다. 다른 정상 세션은 철회하지 않는다. 철회 자체 실패는 `mfa_cleanup_deferred`와
고정 로그 코드로 드러내며, sid의 원본 인증 값은 기록하지 않는다. 자원은 기존 세션 만료/GC로 한정된다.
이미 소비된 context나 verifying/success attempt로 중복 로그인할 수 없다.

S2a 복원은 옛 세션·context를 되살리지 않는다. 차단·Scope·비밀번호·ID 변경의 security_version과 설정
재발급의 row_version을 최종 확인하여 진행 중 MFA 권한도 거부한다. 기존 비밀번호/ID/Scope 정책은 바꾸지 않는다.

## Migration과 검증 경계

0001–0004를 보존하고 0005를 추가한다. key/context/assurance/attempt 단계/감사 또는 orphan MFA 부모가
남으면 downgrade를 거부한다. 관련 테이블 쓰기 잠금을 획득한 후 검사하고 원본을 임의 삭제하지 않는다.
새 업무가 없는 빈 상태만 왕복한다. migration은 명시적 유지보수 작업이며 온라인 운영 무중단 인수가 아니다.

새 검사들은 실제 CLI/발급 경로, cryptography·CBOR로 생성한 가상 서명에 대한 실제 verifier 부정 벡터,
독립 PostgreSQL 연결 barrier 경합, rollback/COMMIT ACK, migration 보존, privacy canary를 구분한다.
실제 HTTPS Chromium은 별도 가상 authenticator 두 개와 native WebAuthn으로 복수 키를 검증한다.
가상 서명 검사와 TestClient를 실제 브라우저 검사라고 표시하지 않는다. OS 하드웨어/모바일/지원 브라우저
전체 및 운영 복구 검증은 후속이다. 실행별 성공/실패/정리는 개발 결과 JSON을 근거로 보고한다.
