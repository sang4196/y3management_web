# IAM S2b — 본인 비밀번호 변경 결과

작성일: 2026-10-15 (Asia/Seoul). 상태: **IAM S2b 제한된 로컬 개발 인수 PASS**. 개발 결과·독립 실행·설계자 재검토를 대조했다.

## 근거와 범위

[Product C3/C5](../product/product-decisions.md), PR-021/026/027 및
[기존 S2a 결과](iam-002-restore-results.md)를 입력으로 본인 비밀번호 변경만 추가했다.
시작 체크포인트는 `c2b01076298e3b1fee9d75ea71acf0184edbd859`,
작업 branch는 `codex/iam-s2b-password-change`다. 시작 Git 상태는 clean이었다.
기존 완료분 push와 이번 증분을 구분하며 개발·검증 단계에서는 commit/push/배포하지 않았다.
사용자 후속 지시에 따라 이 완료 증분의 변경 검토·한글 상세 커밋·푸시는 전담 커밋 담당자가 처리한다.
배포와 미승인 정책 변경은 포함하지 않는다.

관리자 reset, Login ID/역할 변경, 추가 Master, MFA/비상 복구, Workforce·회원·PT·정산은
추가하지 않는다. 마지막 Master라도 현재 암호를 아는 본인 변경은 허용한다.
현재 Master/Branch Admin을 실제 경로로 검증하되 구현 계약은 현재 인증된 본인 기준이며
관리 권한이나 가짜 Trainer 모델을 본인 변경의 조건으로 만들지 않는다.

## 구현 계약

`POST /api/v1/auth/password`는 `current_password`, `new_password`만 받는다.
대상은 현재 AUTH cookie에서 결정하며 추가 account/role/branch/organization 입력을 거부한다.
기존 HTTPS/Origin/JSON/CSRF/body limit 및 비밀 없는 오류 응답을 유지한다.
성공은 빈 204와 AUTH/PREAUTH 삭제이며 자동 로그인·새 Cookie·Account DTO를 반환하지 않는다.

초기 현재 인증/CSRF 확인의 UoW를 먼저 닫는다. 다음 UoW에서 잠금 없는 자격 snapshot으로
현재 암호를 검증하고 기존 정책으로 새 hash를 준비한다. Argon2 작업 동안 업무 행 잠금을
유지하지 않는다. hash는 IAM private adapter에만 보관하며 공개 proof에는 account ID,
security_version, HMAC credential marker만 포함한다.

최종 적용은 Installation→Account→정렬된 모든 자기 AuthSession→credential 순서로 잠근 뒤
현재 인증/CSRF·ACTIVE·만료·동일 자격 marker/security_version을 다시 확인한다.
새 hash와 두 version 전진, 자기 전 AuthSession 철회, 기존 credential 소비 상태 유지,
`password_change` 감사는 한 업무 트랜잭션이다. 초기·최종 인증은 활동 시각을 불필요하게
변경하지 않으며 실패 시 기존 자격/상태/인증/감사/budget을 보존한다.

계정 ID/Organization/역할/관리 Branch와 타 계정 자격·인증을 유지한다.
기존 모든 로그인 실패 budget/cooldown을 초기화하거나 본인 변경 실패를 로그인 실패로
임의 가산하지 않는다. 새 숫자 제한·암호 이력/재사용 금지·새 라이브러리를 도입하지 않았다.
동일 NFC/길이/고정 SHA-256 차단목록·유한 보조 규칙 및 공통 hash 동시 2개를 유지한다.

## Migration과 변경 소유권

신규 `0003_iam_password`는 Audit action CHECK에 `password_change`만 추가한다.
기존 0001/0002와 데이터는 보존한다. 해당 감사가 존재하는 downgrade는 전체 rollback으로
거부하며 감사를 삭제해 성공시키지 않는다. 과거 restore 감사의 downgrade 거부도 유지한다.

변경은 IAM public/infrastructure, use_cases.py, http.py, 신규 0003,
신규 test_iam_s2b.py, 기존 browser/s1.cjs·required-checks.json의 확장 및 이 문서다.
설계자가 추가 허용한 기존 S2a migration 검사의 단일 고정 revision 단언은
Alembic ScriptDirectory의 실제 current head 비교로 변경했다. 데이터·감사 보존 검사는 유지했다.
공통 pytest/QA/browser Python/check 도구, 의존성/lockfile, Product/ADR/기존 결과,
원문을 제거한 `blocked-sha256.txt`는 변경하지 않았다.

## 검증 근거

최신 판정·개발/독립 실행 수치와 9개 구현 파일의 SHA-256은
[설계자 인수 요약](iam-003-password-change-review.json)에 남겼다.
기존 pytest가 자기 프로세스/schema/실행 폴더를 정리했으며 완료된 private 검토 폴더와 원본 로그도
최소 판정 보존·미사용 확인 후 정리했다. 과거 /tmp 실행 자료를 재사용하지 않았다.

- 실제 CLI로 최초 Master를 준비하고 API로 Branch Admin을 설정·로그인한다.
  두 계정 각각 독립 인증 2개가 유효함을 먼저 증명한 뒤 변경·옛 Cookie401·옛 암호 거부·
  새 암호 로그인·같은 Scope·다른 계정 보존을 검사한다.
- anonymous/철회/만료/차단·현재 암호 오류·새 정책 오류·CSRF/Origin/비JSON/extra field·
  hash 용량 거부와 실패 시 데이터/budget/쿠키 보존을 검사한다.
- 감사 실패 rollback과 commit ACK 유실503 후 새 자격 로그인 복구를 검사한다.
- 해시가 멈춘 동안 별도 관리 변경이 커밋할 수 있고, 오래된 proof가 거부됨을 검사한다.
  비밀번호 변경 선행 시 별도 PG 연결의 로그인/차단/Scope 요청이 실제
  `pg_blocking_pids`로 대기함을 확인한다. 로그인 snapshot 선행 및 동시 본인 변경도 검사한다.
- 실제 cooldown이 남은 상태의 비밀번호 변경은 이를 지우지 않으며 새 로그인은 기존429를 유지한다.
- 0002→0003 왕복 데이터 보존과 새 감사 존재 시 downgrade rollback을 검사한다.
- 기존 HTTPS 31개를 유지하고 17개를 추가한 필수 48개 검사로 두 장치·복사 쿠키 철회,
  현재 암호 확인·쿠키 삭제·새 암호/같은 Scope·마지막 Master·다른 계정 보존을 검증한다.
  TLS 인증서 검증과 브라우저 sandbox를 우회하지 않는다.

Privacy 검토에서는 pytest 중첩 assert가 원문 header/body/Row를 설명에 포함할 수 있고,
SyntheticSecret repr만으로 문자열 diff가 가려지지 않는 점을 확인했다.
민감한 비교는 assert 전에 boolean/숫자·HMAC 지문으로 계산하며 안전한 변수만 단언한다.
쿠키/본문/nonce/가상 계정 hash를 넣은 의도적 실패 canary 6건을 `--showlocals`로 실행해
예상 exit1을 유지하면서 원문 비노출을 확인했다. 원문 canary 출력은 보존하지 않는다.

초기 실패는 비JSON 요청의 테스트 기대값415였다. 기존 FastAPI body 검증은 handler 이전에
422를 반환하므로 앱 공통 동작을 바꾸지 않고 테스트를 수정했다. 그 외 초기 정적 검사에서
테스트 반환 타입과 줄 길이를 수정했다. 수행하지 않은 검사를 통과로 기록하지 않는다.

## 제한

S2b 개발 기능 인수는 전체 IAM/실운영 준비 완료가 아니다. 단일 WSL 호스트/ASGI worker,
기존 제한된 개발 실행과 SHA-256 차단목록 공급 범위를 유지한다. 운영 MFA/복구·배포·성능,
지원 브라우저 전체 행렬, 관리자 reset 및 다른 계정 수명 기능은 후속이다.
최종 전체 실행 수치와 설계자/독립 판정은 아래와 인수 요약에서 구분한다.

## 최종 개발 실행 결과

| 명령 (backend/) | 실제 결과 |
| --- | --- |
| `bash check.sh fast` | exit0, Ruff/format 통과, mypy41 source files 통과, pytest **69 passed / 49 deselected**, Import Linter **7 kept / 0 broken**, 33.56초 |
| `bash check.sh db` | exit0, 실제 PostgreSQL **49 passed / 69 deselected**, 316.00초 |
| 별도 실제 HTTPS browser 대상 검사 | 1 passed. 최종 DB 전체 실행에도 포함. 정확한 필수 **48 checks** 모두 true |
| 의도적 실패 privacy probe `--showlocals` | 예상 exit1 및 6 failed 유지. 원문 auth/body/nonce/hash 비노출 PASS |
| `git diff --check` 및 소유 범위/원본 checksum 비교 | 통과 |

총 수집 118개를 fast69/PG49로 나눠 실행했다. PG49는 S1 14개, 실제 브라우저1개,
S2a 7개, 새 S2b 24개, 기반3개다. skip/xfail은 없으며 두 전체 pytest 실행 모두
기존 HTTPX TestClient 및 AnyIO BlockingPortal 경고 2개를 유지한다.
브라우저 내부48개, privacy의 의도적 실패6개를 pytest 통과 건수에 더하지 않는다.

초기 PG 실행의 21 passed/1 failed와 후속 대상13 passed는 이력이며 최종49 통과와 구분한다.
최종 source-manifest는 9개 구현/검사 파일을 고정한다. README 안내 추가는 설계자 소유의
병행 변경으로 보존했고 해당 구현 manifest에는 영향을 주지 않는다. 원래0001/0002,
Product/ADR·의존성/lock·blocked-sha256 공급과 HEAD/staging 상태를 보존했다.
자동 실행들의 자기 schema·프로세스·실행 폴더는 pytest 정리 결과에서 제거 완료를 확인했다.
수동 검토 증거 폴더는 인수 검토까지만 유지하고 미사용 확인 후 정리한다.

## 독립 실행 및 설계자 최종 판정

독립 `bash check.sh fast`는 **69 passed / 49 deselected**, Ruff 검사/서식·mypy41·
Import Linter7 통과다. 독립 `bash check.sh db`는 **49 passed / 69 deselected**로
한 번의 전체 실행에서 통과했다. 이 안의 실제 신뢰 HTTPS 브라우저도 기존31+새17,
**48개 필수 항목**이 모두 참이었다. 두 정규 pytest 실행의 기존 경고2개는 숨기지 않았다.

정규24개 S2b 사례에 없는 동일한 현재/새 비밀번호 입력도 별도 실제 PG 검사로 확인했다.
입력 정책을 만족하는 같은 값에 임의 재사용 금지를 추가하지 않으며, 자격/version 변경과
전 로그인 철회·감사 후 같은 값으로 새 로그인할 수 있다. 추가 검사의 초기 실패는
임시 검사 쿼리가 실제로 없는 grant.role 컬럼을 가정한 문제였다. 실제 scope 컬럼으로
고친 해당 검사만 재실행해 **1 passed**를 확인했다. 이 단발 실행의 경고6개는 기존2개와
외부 검사 marker 등록 관련4개이며 요구된 실제 PG 수집/연결/정리 검사는 유효했다.
단발 검사1개나 privacy 의도적 실패6개를 정규69/49 통과 수치에 합산하지 않는다.

설계자는 현재 인증·CSRF, 해시 단계의 행 잠금 부재와 최종 자격 재확인,
전 로그인 철회·감사 원자성, 실패/응답 유실 복구, 마지막 Master 본인 변경 및
기존 Scope·실패 예산 보존을 검토했다. 테스트의 비밀 출력 위험을 재지시해 보완했고
그 외 확인된 구현 결함은 없다. 기존0001/0002·Product/ADR·의존성/lock·공통 QA 도구와
원문을 제거한 차단 사전은 체크포인트와 동일하다. 전체 모듈 설계/OPEN 상태를 변경하지 않았다.

독립 검사는 자기 schema·프로세스·포트·실행 폴더와 TLS 키/프로필 정리,
전역 신뢰 저장소246개 파일·원본 환경 보존을 확인했다. 최종 판정은 단일 WSL 호스트/worker1의
개발 범위다. 관리자 reset·ID 변경·추가 Master·MFA/비상 복구·Workforce 및 운영 허용은 후속이다.

설계자 최종 대조 후 개발·독립 검증·설계 검토용 private 폴더3개(81,707바이트)를 제거했다.
삭제 전 미리보기와 실제 대상이 같았고 미정리 항목은 없다. 필요한 고정 사전 입력 한 벌,
최신 안전한 자동/브라우저 요약, 현재 개발 환경과 원본 데이터는 유지했다.
