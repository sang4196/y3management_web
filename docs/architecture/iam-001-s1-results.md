# IAM-001 S1 구현·개발 검증 결과

2026-10-14 자료 수명 갱신: 사용자 지시로 완료된 실행의 원본 로그·환경·전체 ZIP 보존을 종료한다. 최신 판정/한계와 현재 자동 테스트는 유지하며 미해결 S1 core 결함은 없다. 아래 과거 경로·checksum·실행 수치는 당시 기록이다. 과거 ZIP을 풀어 재실행하는 안내는 종료됐고, 현재 실행/자료 정리는 [Backend QA 안내](../../backend/README.md#qa-실행-자료와-정리)를 따른다. 원문 corpus는 필요한 입력 한 벌만 `.local/qa/corpus-inputs-3a5f62f0e18a/`에 보존했다. 삭제 대상 자료를 다시 복사·압축하지 않았다.

작성일: 2026-10-13 (Asia/Seoul)
상태: **IAM S1a/S1b 개발 인수 PASS — 구현·독립 검사·설계자 검토 완료**. [설계자 판정](iam-001-s1-review.json)을 따른다. 아래 개발자 실행 결과와 독립 검사 결과를 구분한다.

이 문서는 [S1 구현 전달 범위](iam-001-decision-pack.md#s1-implementation-handoff-20261013)의 결과 기록이다.
Product/ADR 승인 상태를 변경하지 않으며 S1 통과를 전체 IAM-001 또는 운영 준비 완료로 확대하지 않는다.
사전검증은 [PREP 결과](prep-iam-001-results.md), 현재 실행법은 [Backend README](../../backend/README.md)를 따른다.

## 독립 검사 및 설계자 검토

독립 담당자가 같은 최종 backend 소스로 `bash check.sh fast` **58 passed** 및 `bash check.sh db` **18 passed**(90.78초)를 재실행했다. skip/xfail 없이 기존 경고 2개를 유지했다. 이 공통 suite의 재실행과 별개로 실제 CLI·신뢰 HTTPS API·PostgreSQL·브라우저 검사도 작성·실행했다. 브라우저 확인 52항목, 별도 원자성/경합/제약/migration 실행 확인 104항목은 준비·정리 확인을 포함하며 고유 pytest 수로 합산하지 않는다.

별도 실행은 최초 Bootstrap 감사 실패 rollback, 실제 두 CLI 프로세스의 준비 경합, 성공 로그인/로그아웃/계정 발급의 필수 감사 실패, 읽기와 관리 변경의 양방향 PostgreSQL blocking, 검증 snapshot 뒤 차단/재발급, 설정 토큰 동시 소비, 실제 worker 종료 뒤 예약/실패 보존, 첫 migration의 downgrade/reupgrade 및 재적용 후 실제 Bootstrap을 확인했다. `pg_blocking_pids`와 backend/OS process/thread 정보를 기록해 sleep만으로 순서를 추정하지 않았다. 자기 schema/listener/임시 TLS 키를 정리했고 기존 신뢰 저장소 246개 파일은 불변이다.

첫 독립 core probe는 125개 확인 뒤 absolute expiry용 직접 SQL fixture에서 `iam_session_slot` FK에 걸렸다. 자식 expiry만 변경한 하네스 문제이며, 별도 원인 재현과 부모/자식 일관 변경 후 실제 API의 401을 확인했다. 제약을 끄거나 앱을 수정하지 않았다. 앞선 CA extension 문제도 임시 인증서를 고쳐 신뢰 검증을 유지했다. 중간 실패 기록과 최종 보완 근거를 구분해 보존한다.

설계자는 실제 코드/계약·diff·실행 증거를 대조하고 12건을 재지시·해소 확인했다. 최신 소스는 개발자 최종 62파일 manifest와 일치하며 Product/ADR 원본과 기존 의존성 버전을 보존했다. 세션 철회, 실패 예산, commit ACK 유실, 감사·공개 계약·실제 앱 시작 배타 잠금 및 안전한 브라우저 집계를 확인했다. 이 판정은 첫 개발 증분에 한정한다.

## 구현 범위

- 보호된 TTY 입력을 사용하는 최초 1회 CLI Bootstrap으로 Organization·Master·관리 권한·감사를 준비한다. 기본 암호, 재설치/reset 우회, 앱 시작 시 자동 migration은 없다.
- 실제 Argon2id 비밀번호 로그인, PostgreSQL AuthSession, 현재 사용자/Scope, 현재 로그아웃을 제공한다. 계정 신원과 관리자 권한을 분리하고 공개 계약에 DBSession·ORM·비밀번호 해시를 내보내지 않는다.
- Master의 지점 생성, Branch Admin 발급/조회/정확한 Login ID lookup, 최초 설정 및 대기 계정의 재발급을 제공한다. 일회용 30분 링크는 HTTPS fragment로 전달하며 GET으로 소비하거나 설정 후 자동 로그인하지 않는다.
- Master Organization / Branch Admin 단일 Branch 범위를 Backend 목록·상세·직접 ID 조회에 적용한다. 차단·관리 지점 변경은 대상의 인증을 철회하고 실행 Master의 인증은 유지한다. 현재 상태/version을 잠금 후 재검사하며 no-op과 stale version을 구별한다.
- 중요 변경과 감사는 동일 UoW에서 커밋/rollback한다. 저장 성공 후 응답 유실 상황에서 이미 커밋된 계정·credential·인증·감사를 보상 삭제하지 않는다.
- 반복 로그인 제한은 별도 PostgreSQL 트랜잭션의 실패/진행 중 예약을 사용한다. 해시 진입 전 용량 거부와 검증 후 저장 실패를 구별하며 후자는 예약을 임의 취소하지 않는다. live 예산을 축출하거나 메모리 fallback하지 않는다.
- 별도 명시적 Alembic revision으로 계정/역할/지점/FK·예약 Login ID·인증/보안 상태·감사를 생성한다. 필터링된 암호 목록과 고정 출처/라이선스/manifest를 패키징하고 시작 시 무결성을 확인한다.
- 신뢰 HTTPS·Secure/HttpOnly/SameSite Cookie·CSRF·Origin 검사를 적용한다. 실제 ASGI lifespan이 같은 DB/schema의 두 번째 OS 프로세스를 거부한다. 해시 작업은 공통 동시 2개 상한이다.

## 최종 실제 실행 결과

아래 명령은 `backend/`에서 현재 소스를 대상으로 실행했다. PostgreSQL 검사는 소유권이 확인된 전용 Compose DB의 무작위 `iam_test_<UUID>` schema를 사용했다.

| 명령 | 결과 |
| --- | --- |
| `bash check.sh fast` | exit 0. Ruff check/format 통과(43 files), mypy 38 source files 통과, pytest **58 passed / 18 deselected**, Import Linter **7 kept / 0 broken** |
| `bash check.sh db` | exit 0. 실제 PostgreSQL pytest **18 passed / 58 deselected**, 92.31초 |
| `uv run --locked --env-file .env.example pytest tests/test_iam.py -k business_commit_precedes -m postgres --require-postgres` | 보완 경합 검사 **2 passed / 12 deselected**. 이후 위 전체 DB 검사에 포함 |
| `uv run --locked python tools/build_password_corpus.py /tmp/y3-prep-iam-001-h90lpnpq/sources --check` | 고정 원문 checksum과 산출물 일치. 길이 15–128의 NFC 항목 **55,169개**, 실제 원문에 포함된 짧은 반복 seed **4개** |
| 별도 소유 schema의 `python -m alembic upgrade head` → `downgrade base` → `upgrade head` | 세 명령 exit 0. 처음/재적용 테이블 15개·제약 58개 및 revision 일치, downgrade 후 revision 없음·버전 테이블만 남음, 자기 schema 삭제 확인 |
| `git diff --check` | 통과 |

전체 수집은 76개이며 fast/DB marker에 따라 58/18로 나뉜다. skip/xfail은 없다. 두 pytest 실행 모두 기존 HTTPX TestClient fallback 및 AnyIO BlockingPortal deprecation 경고 2개를 유지했다. 기존 의존성 변경으로 경고를 숨기지 않았다.

DB 18개는 IAM CLI/API/경합 14개, 실제 HTTPS 브라우저 1개, 기존 Foundation 3개다. 브라우저 1개 안에서 고정된 **25개 check**를 검사한다. TestClient 결과를 브라우저 결과로 계산하지 않는다. Python과 실제 Node의 집계 회귀 7개는 빈 결과·누락·추가·false·정수·잘못된 타입을 실패 처리하며 최종 fast에 포함됐다.

## 경합·실패 근거

- 로그인 검증 snapshot 이후 차단이 먼저 커밋되면 로그인 401이고 새 유효 AuthSession이 없다.
- 반대로 실제 로그인 UoW가 Account 잠금을 가진 채 감사까지 저장한 지점에서 멈추면, 독립 관리 연결이 해당 backend PID에 의해 대기함을 `pg_blocking_pids`로 관찰한다. 로그인 커밋 후 차단이 커밋되고, 방금 발급된 쿠키를 실제 HTTP에 재사용하면 401이다. 실행 Master는 200을 유지한다.
- 최초 설정의 해시 snapshot 이후 재발급이 먼저 커밋되면 구 토큰은 400이며 새 토큰만 설정 가능하다.
- 반대로 활성화 UoW가 먼저 잠금을 가진 경우 재발급 연결의 실제 PostgreSQL 대기를 확인한다. 활성화 커밋 후 재발급은 409이고 ACTIVE/version 2 및 재발급 감사 없음이 확인된다.
- 읽기 인증의 Account SHARE가 유지되는 동안 권한 변경 UPDATE가 기다린다. 별도 검사에서는 인증 트랜잭션 시작 뒤 실제 DB 잠금 대기 중 idle 만료가 지나도록 하고, 잠금 획득 후 `clock_timestamp()` 재검사로 401을 확인했다. 단순 sleep만으로 순서를 추정하지 않는다.
- 독립 연결의 로그인 예약 경쟁, 같은 설정 토큰 동시 소비, 인증 행/slot 회수, 감사 실패의 업무 rollback, commit ACK 유실, 검증 후 실패 예산 보존, SQL 제약 위반을 검사했다.
- 실제 Chromium/신뢰 CA HTTPS에서 CLI로 준비한 Master 로그인부터 지점 생성·계정 발급·fragment 삭제·설정·Branch 범위·CSRF 거부·로그아웃·복사 쿠키 거부까지 확인했다. JavaScript 비활성 시 비밀번호가 전송되지 않는 것도 포함한다. 같은 DB/schema의 다른 포트에서 실제 두 번째 앱 프로세스 기동 거부와 원래 서버 생존을 확인했다.

보완 과정에서는 테스트의 중복 TestClient lifespan이 의도한 단일 앱 guard에 걸렸고, 이를 기존 앱에 복사 쿠키를 보내는 방식으로 수정했다. 추가 테스트의 줄 길이/타입 오류도 최종 전체 검사 전에 수정했다. 앞선 51/14 결과를 최종 수치로 재사용하지 않았다.

## 증거와 변경 보존

설계자가 비밀 없는 개발자·독립 검사·검토 증거를 S1 증거 묶음(완료 자료 정리로 폐기)에 보존했다. ZIP은 46개 entry, 85,646 bytes이며 SHA-256은 `467667a7b3cc4262bed3332d74040fb8be1371b8fa18b3e2cbc79897c70afda2`다. 내부 `manifest.json`에 파일별 checksum이 있다. 개발자 원본 결과 문서는 보고서에 기록된 checksum과 일치하는 인수 전 snapshot으로 별도 보존했으며 현재 문서에는 이후 설계자 인수 결과를 덧붙였다. 원래 61개 계획을 모두 개별 실행했다고 주장하지 않는다. 각 probe의 중간 상태 표시와 설계자의 통합 인수 판정을 구분한다.

작업 소유 증거 디렉터리: `/tmp/y3-iam-s1-oxq4otn6`.

- `final-report.json`: 명령·상태·정확한 결과·제한·증거 checksum을 담은 기계 판독 보고서.
- `final-fast.log`, `final-db.log`, `reverse-races-final.log`, `final-corpus.json`: 최종 실행 증거.
- `final-browser-results.json`, `final-startup-results.json`: 비밀 없는 실제 브라우저/프로세스 결과.
- `final-migration-roundtrip.json`, `migration-roundtrip.py`: schema `iam_test_166cc3b2d6724db2a92c0d38b65f99e1`의 실제 migration 왕복. 빈 schema에서 시작해 최초/재적용 모두 revision `0001_iam_s1`, 15개 테이블·58개 제약의 이름/종류가 일치했다. downgrade 직후는 `alembic_version` 테이블 1개·제약 1개·revision 0개였고 최종 schema 제거까지 확인했다. 앱·테스트 소스 변경 없이 전체 검사 이후 수행한 별도 DDL 검사다.
- `final-source-manifest.json`: backend의 Git tracked/untracked 비무시 파일 62개 SHA-256. manifest 자체 SHA-256은 `639026688d892fdf38110b29bd4813ad2ec794b392ab113036ef958ccf5e6219`다.
- `finalization-preservation-before.json`, `preservation-result.json`: 기존 문서와 HEAD/index 보존 비교. 새 결과 문서만 추가하며 규범 문서를 수정하지 않았다.

수정 범위는 backend의 애플리케이션/설정/DB 조합, IAM·Organization·Audit 공개 계약과 구현, CLI·HTTP·UoW·프로세스 guard, 첫 migration, 테스트·암호 공급 도구/데이터·README·의존성 및 이 새 결과 문서다. 기존 lock 44개 entry의 버전을 유지했고 pwdlib/argon2-cffi/argon2-cffi-bindings/cffi/pycparser 5개만 추가했다.

HEAD `b83defe3fc564b56d0f77cb075ddb5436759d191`과 기존 staging 상태를 유지했다. commit/push/reset/clean을 하지 않았다. 초기 구현 baseline 이후 변경된 외부 파일 `prep-iam-001-review.json`은 공유 작업의 설계자 소유 검토 기록이며 개발 변경으로 귀속하지 않는다. 이번 마무리 시작 시점의 모든 기존 docs 파일은 보존 비교를 통과했다. 다른 담당자의 변경을 되돌리지 않았다.

원문 암호·토큰·쿠키·키·연결 비밀·예외 본문은 결과 문서/JSON에 포함하지 않는다. 브라우저의 입력 파일은 종료 시 삭제하고 서버 종료·로컬 신뢰 저장소 불변을 검사한다. 자기 테스트 schema만 정리하며 공유 Compose 서비스·public·타 담당자 schema/볼륨을 지우지 않는다. `/tmp`는 영구 보관소가 아니므로 안전한 최종 근거는 위 ZIP에 별도 보존했다. 개발자 보존 결과는 개발자 마무리 시점의 snapshot이며 이후 설계자가 갱신한 Architecture 인수 상태와 현재 결과 문서는 개발자 변경으로 귀속하지 않는다. backend 최종 manifest와 Product/ADR은 그 이후에도 불변이다.

## 제한과 남은 판정

- 개발자 최종 검사와 독립 실행·설계자 대조를 마쳤다. 첫 S1 개발 인수 PASS이며 전체 IAM-001/운영 인수는 아니다. 실제 범위와 남은 한계는 [설계자 판정](iam-001-s1-review.json)에 기록한다.
- S1은 단일 WSL 호스트/단일 ASGI worker의 개발 검증이다. 다중 호스트·컨테이너 자원 상한, 운영 SLO/성능/배포·재해복구를 검증하지 않았다. 운영 환경의 IAM 기동은 거부한다.
- 브라우저 검사는 현재 환경의 Chromium 및 외부 설치 Node/Playwright/NSS 도구에 의존한다. 승인된 전체 지원 브라우저 행렬의 완료가 아니다. 미설정/도구 부재는 skip 대신 실패한다.
- 최초 Master 분실/복구, reset·본인 암호/ID 변경, 추가 Master, Operator·Trainer 업무 연결, MFA/Passkey, 감사 열람·보존/삭제의 후속 정책·구현, PT/지급/정산은 이번 완료 범위가 아니다.
- 고정 목록과 유한 약암호 보완은 한국어 유출 대표성이나 모든 변형 탐지를 보장하지 않는다. 향후 목록 갱신은 출처·라이선스·정상 문구 회귀·무결성의 별도 검토 대상이다.
