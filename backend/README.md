# 백엔드 개발·검증 안내

## QA 실행 자료와 정리

2026-10-14부터 WSL의 기존 pytest runner/fixture가 기본 임시 위치를 프로젝트 루트
`.local/qa/auto-<UUID>/`로 설정한다. 별도 QA 관리 CLI/서비스를 추가하지 않는다.
`run.json`에는 실행 식별자·시각·상태·경로의 device/inode/소유자, 프로세스의 PID와
시작 tick/boot ID, 알려진 포트·전용 테스트 schema를 기록한다. 비밀값은 기록하지 않는다.
일반 `tmp_path`와 HTTPS의 키·입력·로그·NSS/브라우저 프로필도 이 실행 폴더 안에 둔다.

자동 실행은 성공과 실패 모두 최소 결과 `latest-auto.json`을 먼저 기록하고, 자신이 만든
프로세스와 schema를 종료/제거한 뒤 실행 폴더를 정리한다. HTTPS는 허용된 boolean check와
브라우저 버전만 `latest-browser.json`에 유지한다. 원본 로그·캡처·전체 실행 환경을 계속
쌓지 않는다. PID 숫자만으로 종료하지 않고 생성 시 기록한 OS identity와 pidfd를 확인한다.
준비 실패에도 기존 fixture의 ExitStack이 자기 schema 정리를 시도한다. 살아 있는 프로세스,
미정리 schema, 소유권 불일치 또는 정리 오류가 있으면 폴더를 남기고 검사를 실패 처리한다.
강제 중단은 `run.json`의 owner identity로 발견할 수 있으며 자동으로 다른 환경을 지우지 않는다.

수동 검수에는 기존 CLI와 별도 가상 데이터/schema를 사용한다. `tests.conftest.qa_create("manual")`
로 검수 폴더를 만들고 기존 CLI의 환경 파일·인증서·실행 자료를 그 안에 둔다. Python에서
기존 CLI를 Popen으로 시작하면 `qa_register_process(process, run=run, port=port)`로 기록하고
`qa_stop_process(process)`로 동일한 프로세스만 종료한다. 직접 시작한 터미널 서버는 해당
터미널의 Ctrl-C로 종료한다. 검수 폴더는 종료만으로 삭제하지 않으며 원본 DB/설정·미디어를
옮기거나 공유 DB/볼륨을 초기화하지 않는다. 다음 코드는 기존 pytest 지원 함수를 이용한
상태 조회와 **검수 완료 후** 지정 폴더의 정리 예다. 새로운 관리 도구가 아니다.

```python
from pathlib import Path
from tests.conftest import qa_read, qa_finish, qa_cleanup

run = Path("<프로젝트 절대경로>/.local/qa/manual-<UUID>")
print(qa_read(run))  # 상태/OS identity; 인증정보 없음
qa_finish(run, "review-complete")  # 검수 완료·미사용 확인 후에만
plan = qa_cleanup(run)  # dry-run; held면 정리하지 않음
print(plan)
# 확인한 계획 그대로 지정 실행만 정리. 변경·실행 중·소유권 불일치는 거부한다.
if "plan" in plan:
    print(qa_cleanup(run, dry_run=False, expected_plan=plan["plan"]))
```

실패 환경 자체가 재현에 필요할 때만 `qa_finish(run, "retained", "비밀 없는 보존 사유")`로
파일 환경을 보류한다. 수동 DB의 보존/정리는 별도로 소유권을 검증해야 하며 파일 정리 함수가
DB/볼륨을 삭제하지 않는다. 자동 IAM fixture의 정상 종료는 자기 schema를 제거한다.
완료된 테스트의 오래된 링크나 당시 검수 대기 문구는 영구 보존 근거가 아니다.
legacy 경로는 새 표식을 붙여 검증을 우회하지 않고 내용·소유권·사용·공유 여부를 따로 확인한다.

예외: `/tmp/y3management-runtime`은 앱 전체의 고정 배타 잠금 경로다. 실행별로 옮기거나
잠금 파일을 삭제하면 중복 앱 방지가 깨지므로 유지한다. 명시적 pytest `--basetemp`와 복제한
synthetic conftest probe는 호출자 소유이며 상위 실행의 정리 책임 아래 둔다. 코드 복제가
필요하면 현재 dirty 파일까지 반영하되 `.local/qa`, `.git`, 가상환경·캐시를 재귀 복제하지 않는다.

현재 오프라인 corpus 입력 한 벌은 `.local/qa/corpus-inputs-3a5f62f0e18a/`에 있다.
`uv run --locked python tools/build_password_corpus.py ../.local/qa/corpus-inputs-3a5f62f0e18a --check`
로 기존 도구를 실행한다. 고정 source manifest의 7개 입력만 유지하며 중복 실험 환경은 필요 없다.
현재 운영 배포 구성은 없다. 향후 배포에는 `.local/qa/`·테스트 DB/키/프로필/원본 로그를
포함하지 않아야 한다. wheel은 기존 `src/y3management`만 패키징한다. 배포 도구는 추가하지 않는다.

## IAM-S2c 개발 증분 (2026-10-15)

`PATCH /api/v1/admin/accounts/{id}/login-id`는 같은 조직 Master가 ACTIVE Branch Admin의
`login_id`와 `expected_version`을 보내 변경한다. 현재 인증·CSRF를 검증하며 추가 암호 확인은 없다.
대소문자를 무시하고 원계정의 과거 예약 ID 복귀를 허용한다. 다른 계정은 예약 ID를 가져올 수 없다.
현재 ID만 로그인할 수 있다. 변경은 원래 암호/UUID/권한·Scope를 유지하고 대상 모든 세션을 철회한다.
현재 version의 정규화 동일 ID는 세션/version/감사까지 그대로 두는 no-op다.
실제 변경 성공은 현재 Master 세션의 활동 시각만 갱신하고 절대 만료와 다른 세션은 보존한다.
같은 트랜잭션의 최종 재인증에서 만료되면 변경 전체를 rollback한다.

계정의 고정 login budget key로 실패 횟수·cooldown·진행 중 예약을 유지한다. 익명 admission과
변경 후 계정이 엇갈리는 기술 경합은 503으로 종료하고 기존 lease를 보존한다. 새 admission부터
재시도하되 즉시 budget 반환을 보장하지 않는다. commit ACK 유실 때는 account UUID로 결과를 확인한다.
새 `0004_iam_login_id`는 key 또는 신규 감사가 남으면 downgrade를 거부한다.
[기술 설계](../docs/architecture/iam-004-login-id-design.md)와
[개발 검증 결과](../docs/architecture/iam-004-login-id-results.md)를 참고한다.

## IAM-S2b 개발 증분 (2026-10-15)

`POST /api/v1/auth/password`는 현재 인증된 본인의 `current_password`와 `new_password`만 받는다.
현재 암호 확인과 기존 새 암호 정책을 통과하면 자격/version 변경·전 AuthSession 철회·감사를
같은 트랜잭션으로 저장한다. 성공은 본문 없는 204이며 AUTH/PREAUTH cookie를 제거한다.
현재 장치도 새 암호로 다시 로그인해야 한다. 마지막 Master의 본인 변경도 허용한다.
실패하면 기존 자격/인증을 보존하고 로그인 실패 budget/cooldown은 변경하지 않는다.
ACK 유실 등 503이면 저장 결과가 불명확할 수 있으므로 새 로그인으로 확인하며 이전 자격을 보상 복구하지 않는다.
감사 action 추가는 새 `0003_iam_password` revision이고 기존 0001/0002는 유지한다.
현재 구현·검증 결과는 [S2b 결과](../docs/architecture/iam-003-password-change-results.md)를 따른다.
현재 실제 인수 대상은 Master/Branch Admin이다. Trainer 연결/운영 MFA·복구는 후속이다.

## IAM-S2a 개발 증분 (2026-10-14)

같은 Organization의 Master가 정상 차단된 Branch Admin을
`POST /api/v1/admin/accounts/{id}/restore`와 `expected_version`으로 복구한다.
기존 암호로 새 로그인해야 하며 옛 인증·credential·실패 횟수/cooldown은 부활하거나 초기화하지 않는다.
감사는 상태/version 변경과 같은 트랜잭션이고 새 명시적 migration은 `0002_iam_restore`다.
현재 [결과와 제한](../docs/architecture/iam-002-restore-results.md)을 따른다.
본인 암호 변경은 위 S2b 범위다. reset/추가 Master/ID 변경/운영 MFA·비상 복구는 아직 제공하지 않는다.

## IAM-S1 개발 실행 (2026-10-13)

IAM을 명시적으로 켜면 일회성 초기 Master 준비, 실제 암호 로그인, Branch Admin 발급/설정 링크,
조직·지점 범위 조회, 현재 로그아웃, 차단/관리 지점 변경과 전체 인증 철회를 제공한다.
S2a의 일반 Branch Admin 복구와 S2b 본인 암호 변경을 후속 제공하며
reset/추가 Master/Trainer 업무·운영 MFA는 제공하지 않는다. 운영 환경에서는 IAM 기동을 거부한다.
아래 Foundation/Windows 실행 기록은 해당 시점 이력이며 IAM 인수 결과와 구별한다.

1. WSL에서 `uv sync --locked`를 실행한다. 기존 고정 패키지 버전을 유지하고 해시 관련 5개만 추가했다.
2. 소유권이 확인된 `postgres-test` 또는 `postgres-dev`를 사용한다. 독립 검사에는 새 고유 schema를
   직접 준비한다. 기존 `public`/다른 schema·볼륨을 초기화하지 않는다. DB 소유권 검사는
   `tests/conftest.py`와 `y3management.ownership`에 있다.
3. 작업 소유의 0600 환경 파일에 아래 설정을 명시한다. 파일/비밀은 Git에 넣거나 출력하지 않는다.
4. `uv run --locked --env-file <환경파일> alembic upgrade head`로 명시적으로 migration한다.
   앱 기동은 schema를 생성하거나 migration하지 않는다.
5. 서버를 띄우기 전에 아래 Bootstrap 명령을 터미널에서 한 번 실행한다. 암호와 확인값은 숨김 입력한다.
   stdin pipe·기본 암호·force·reset은 지원하지 않는다. 이미 설치된 경우 비정상 종료한다.
6. 같은 origin의 신뢰 HTTPS 인증서/키로 서버를 실행한다. HTTP 예외·임의 forwarded 헤더 신뢰는 없다.

```bash
uv run --locked --env-file <환경파일> python -m y3management.cli bootstrap-initial-master \
  --organization <가상조직명> --login-id <최초ID> --confirm-database y3management_test
uv run --locked --env-file <환경파일> python -m y3management.cli serve \
  --cert <신뢰HTTPS인증서> --key <개인키> --port <포트>
```

필수 IAM 설정은 `Y3_IAM_ENABLED=true`, `Y3_ENVIRONMENT=test`(또는 development),
전용 대상의 `Y3_DATABASE_URL`, `Y3_DATABASE_SCHEMA`, 경로 없는 정확한
`Y3_CANONICAL_ORIGIN=https://localhost:<포트>`, CSPRNG 32바이트 이상에서 만든
`Y3_IAM_KEY`(최소 43문자), `Y3_SECURITY_STATE_CAPACITY`, `Y3_AUTH_SESSION_CAPACITY`다.
키는 실행 간 동일하게 보관하고 요청마다 재생성하지 않는다. 자원 상한은 계정 정책이 아니며
명시적 로컬 용량 설정이다. 자기소유 통합 검사에서는 상태 2048/인증 128을 사용한다.
용량 부족은 503이고 live 예산을 삭제하거나 무제한 fallback하지 않는다.
IAM을 켜지 않은 기존 health-only 구성은 유지한다. `/health/ready`는 DB 연결 검사이며 업무 인수 증거가 아니다.

S1 지원 실행은 단일 WSL 호스트/단일 ASGI worker다. 실제 앱 lifespan이 고정 경로
`/tmp/y3management-runtime/<DB·schema 식별자>.lock`을 획득하므로 같은 DB/schema의
다른 포트/별도 OS 프로세스도 동시에 기동할 수 없다. 실행별 lock 경로 override는 없다.
`Y3_WORKER_COUNT`는 1만 허용한다. 다중 컨테이너/호스트 배포의 자원 상한은 검증 범위 밖이다.
생성/검증/rehash는 공통 동시 2개 gate를 사용하며 무제한 큐를 만들지 않는다.

API 접두사는 `/api/v1`이다. `GET /auth/csrf`에는 `X-Y3-Client`와 정확한 Origin/Referer가 필요하다.
Origin/Referer가 없는 브라우저 same-origin GET은 Fetch Metadata와 custom header를 함께 검사한다.
변경 요청은 JSON과 정확한 Origin(없으면 엄격한 Referer), `X-CSRF-Token`을 요구한다.
인증은 HttpOnly/Secure/SameSite=Lax의 `__Host-y3-auth`, 준비는 `__Host-y3-preauth`를 사용한다.
유효 로그인 중 다시 로그인하면 현재 인증의 CSRF 확인 뒤 409이며 먼저 logout해야 한다.
목록의 허용 query는 offset/limit뿐이며 role/organization/branch를 입력해 범위를 넓힐 수 없다.

발급/재발급의 `setup_link`는 설정된 HTTPS origin의 `/activate#token=...`이고 한 번만 반환한다.
설정 페이지는 fragment를 메모리에 옮기고 URL에서 지운 뒤 POST로 소비한다. GET으로 활성화하지 않으며
설정 후 자동 로그인하지 않는다. 응답 유실 시 Master의 정확한 Login ID lookup으로 대상/version을
확인하고 PENDING_SETUP에 한해 새 링크를 발급한다. 원래 token 조회·맹목 재발급은 없다.
commit 결과 불명확은 503이며 이미 저장된 account/credential/session/audit를 보상 삭제하지 않는다.

암호 공급은 `src/y3management/iam/data`의 고정 manifest/라이선스가 있는 실제 목록에서
NFC 후 길이 15–128자 55,169개를 패키징했다. 저장 artifact는 원문 대신 정렬된 UTF-8 SHA-256
지문 목록 `blocked-sha256.txt`이며 입력을 NFC 처리한 뒤 같은 지문으로 전체 일치를 검사한다.
공개 사전의 토큰 형태 원문을 배포하지 않으면서 같은 항목을 모두 차단한다. 이는 차단 사전의
표현 방식이며 실제 계정 암호 저장은 기존 Argon2를 유지한다. 짧은 반복 seed 4개도 유지한다.
앱은 전체 artifact manifest와 각 파일 checksum을 확인하고 오류 시 기동을 거부한다.
`python tools/build_password_corpus.py <고정 원문 디렉터리> --check`로 원문에서 동등성을 재현한다.
원문 URL/checksum은 source-manifest.json에 있고 요청 중 네트워크 조회/빈 목록 fallback은 없다.
갱신은 새 고정 공급의 분포/유한 약암호·정상문구 회귀와 라이선스를 검토한 후 artifact manifest 및
코드에 고정한 manifest checksum을 함께 변경하는 별도 검토 작업이다. 한국어 유출 대표성/모든 변형 탐지는
보장하지 않으며 일반 단어 부분 포함·hash 입력 trim/casefold는 적용하지 않는다.

```bash
bash check.sh fast
bash check.sh db
# IAM 실제 PG/CLI/API 검사만 (새 자기소유 schema 생성/제거)
uv run --locked --env-file .env.example pytest tests/test_iam.py -m postgres --require-postgres
# 실제 신뢰 HTTPS 브라우저 (추가 의존/리소스는 아래 참조)
uv run --locked --env-file .env.example pytest tests/test_iam_browser.py -m postgres --require-postgres -s
```

브라우저 검사는 WSL의 openssl/bubblewrap/apt/dpkg-deb와 기존
`/home/shlee/.cache/ms-playwright/chromium-1234/chrome-linux64`,
`/home/shlee/Workspace/ai/01.codex/sj_company/node_modules/playwright-core`(1.62.1),
`/home/shlee/.local/share/node/node-v22.23.2-linux-x64/bin/node`를 요구한다.
libnss3-tools는 자기 임시 디렉터리에 다운로드/추출하고 CA 신뢰는 namespace에만 적용한다.
인증서 검증을 끄지 않는다. 미설정/도구 부재를 skip/통과로 바꾸지 않는다.
별도 임시 TLS/프로필/서버와 무작위 schema만 사용하며 종료 시 서버·브라우저·DB schema를 정리한다.
현재 `.local/qa/latest-browser.json`에 비밀 없는 최신 결과만 유지하고 실행의 input/키/프로필/원본 로그는 종료 때 정리한다.
Docker 서비스/기존 schema는 삭제하지 않는다. 지원 브라우저 전체/실운영 성능·배포 검증이 아니다.

## WSL Ubuntu 개발 환경 (2026-09-18 WSL로 이전)

현재 작업 위치는 `/home/shlee/Workspace/ai/01.codex/y3management_web/backend`다. 아래 Windows 절과 FOUNDATION-002의 BLOCKED 기록은 이전 환경의 이력이다. WSL에서는 Python 3.13.15와 uv로 가상환경을 재구성했다.

```bash
uv sync --locked
bash check.sh fast
docker --context wsl-ubuntu compose up -d postgres-dev postgres-test
bash check.sh db
uv run --locked --env-file .env.example uvicorn y3management.main:create_app --factory --host 127.0.0.1 --port 8000 --reload --reload-dir src --no-access-log --log-config logging.json
```

`wsl-ubuntu`는 Ubuntu 내부 Docker Engine 29.8.1의 `unix:///run/docker-wsl.sock`에 연결한다. Docker Desktop의 기본 소켓과 분리했으며 데이터는 D 드라이브의 Ubuntu 가상 디스크에 저장된다. WSL용 Compose/Buildx를 우선 사용한다. 통합 fixture는 Windows에서는 기존 desktop-linux 엔드포인트, Linux에서는 이 명시적 WSL 엔드포인트만 허용하며 기존 Compose 소유권·포트·DB/role 검증을 유지한다. 다른 Linux 환경이 자동 지원된다고 가정하지 않는다.

`check.sh`는 `check.ps1`과 같은 빠른 검사 및 필수 DB 검사 진입점이다. 제품 코드·업무 스키마·의존성 버전은 변경하지 않았다.


현재 WSL 환경에서는 빠른 검사와 실제 PostgreSQL 기반 검사 3개가 통과했다. 실제 연결·commit/rollback·세션 정리·health 및 Alembic 온라인 `current`를 확인했으며, [WSL 이전 검증 기록](../docs/architecture/wsl-migration.md)을 따른다. 필수 DB 검사의 설정 누락·skip/xfail·미수집은 성공으로 처리하지 않는다. [FOUNDATION-002의 Docker BLOCKED 기록](../docs/architecture/foundation-002.md)과 FOUNDATION-001 결과는 당시 Windows 환경의 이력으로 유지한다. 업무 schema migration·지급 계산 및 업무 동시성·운영 배포 준비 검증은 완료하지 않았다.

현재는 개발 기반이며 운영 배포 준비 완료 상태가 아니다. [범위·실행 결과와 배포 후속](../docs/architecture/foundation-001.md), [ADR-0003](../docs/decisions/0003-foundation-tooling.md)을 함께 읽는다. 업무 테이블·로그인·PT 진행 등록은 없다.

## Windows PowerShell 설치

저장소 루트에서 시작한다. uv가 PATH에 있으면 아래 bootstrap 대신 해당 uv를 사용할 수 있다. 이 작업은 uv 0.12.15로 검증했다. bootstrap은 전역 패키지를 변경하지 않고 ignored .tools에 설치한다.

```powershell
python -m pip install --target .tools/uv uv==0.12.15
$uv = (Resolve-Path .tools/uv/bin/uv.exe).Path
Set-Location backend
& $uv python install 3.13.15
& $uv sync --locked
# 기존 .env가 있으면 덮어쓰지 않는다.
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

이후 명령의 작업 위치는 backend/다. 새 PowerShell에서 시작하면 저장소 루트에서 $uv를 다시 지정한다. uv.lock은 커밋 대상이며 .venv/.env/.tools/cache는 제외한다. 예시 비밀번호는 로컬 전용이고 운영에는 허용하지 않는다.

## 전용 로컬 PostgreSQL

먼저 `docker context inspect desktop-linux --format '{{.Endpoints.docker.Host}}'`가 로컬 `npipe:////./pipe/dockerDesktopLinuxEngine`인지 확인한다. 원격 대상이면 진행하지 않는다. 현재 context를 전역 변경하지 않고 명시적으로 지정한다. FOUNDATION-002에서 아래 start는 시간 초과, 이후 status는 stopped였다. config 구문은 검증했지만 서비스 기동은 미수행이다.

```powershell
docker desktop start --timeout 60
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
docker --context desktop-linux version
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
docker --context desktop-linux compose config --quiet
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
docker --context desktop-linux compose up -d postgres-dev postgres-test
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
docker --context desktop-linux compose ps
```

전용 프로젝트 y3management-foundation 아래 개발 DB/role y3management_dev(127.0.0.1:55432)와 테스트 DB/role y3management_test(127.0.0.1:55433), 별도 볼륨을 사용한다. 다른 프로젝트/C# DB를 재사용하지 않는다. 기존 컨테이너/볼륨 자동 삭제·reset 명령은 제공하지 않는다. 초기 환경변수는 이미 초기화된 볼륨을 덮어쓰지 않으므로 연결 실패 시 대상을 확인하고 데이터를 자동 삭제하지 않는다.

## 개발 실행

```powershell
& $uv run --locked --env-file .env uvicorn y3management.main:create_app --factory --host 127.0.0.1 --port 8000 --reload --reload-dir src --no-access-log --log-config logging.json
```

별도 터미널:
```powershell
Invoke-RestMethod http://127.0.0.1:8000/health/live
Invoke-WebRequest http://127.0.0.1:8000/health/ready
```

live는 DB와 무관하게 200이다. ready는 SELECT 1 연결 확인 성공 시 200, 실패/응답 대기시간 초과 시 503이며 상세 DB 오류를 반환하지 않는다. 성공은 미래 업무 테이블·migration·권한·급여 계산 검증을 뜻하지 않는다. 설정 파일은 자동 로딩되지 않으며 --env-file은 명시적 개발 선택이다.

## 설정

| 환경변수 | 조건/기본값 |
| --- | --- |
| Y3_ENVIRONMENT | 필수: development / test / production |
| Y3_DATABASE_URL | 필수: 단일 postgresql+psycopg URL, 명시적 role/password/host/port/database. 출력 금지 |
| Y3_LOG_LEVEL | DEBUG/INFO/WARNING/ERROR/CRITICAL, INFO 기본. 앱 로그 수준 |
| Y3_DB_CONNECT_TIMEOUT_SECONDS | 2–30초, 3 기본 |
| Y3_DB_POOL_TIMEOUT_SECONDS | 0초 초과–30초, 2 기본 |
| Y3_DB_STATEMENT_TIMEOUT_MS | 100–30000ms, 2000 기본 |
| Y3_READINESS_TIMEOUT_SECONDS | 0초 초과–30초, 4 기본 |
| Y3_TEST_DATABASE_URL | 실제 DB 테스트의 별도 opt-in; 앱 URL을 대신 쓰지 않음 |

개발/테스트는 loopback과 지정 DB/role만 허용한다. 운영에는 개발/테스트 DB/role 및 예시 비밀번호를 거부하며 fallback이 없다. 현재 DB URL query는 sslmode/sslrootcert만 허용해 host/service/timeout 우회 설정을 차단한다. 운영 TLS·인증 방식은 배포 설계에서 결정한다.

기본 로그는 시작/종료/일반 오류 코드만 기록한다. 요청 URL·본문·인증 헤더·예외 traceback·DB URL을 기록하지 않는다. SQL echo/접근 로그도 끈다. 향후 민감정보 없는 관측 체계와 진단 코드는 별도 설계한다.

## 실행 가능한 검사

빠른 검사는 .env를 불러오지 않으며 PostgreSQL 성공 경로 3개를 명시적으로 제외한다. 제어된 로컬 연결 거부의 실제 드라이버 검사는 포함한다. 다음 wrapper는 하위 검사 실패 즉시 non-zero로 종료한다. ExecutionPolicy Bypass는 해당 PowerShell 프로세스에만 적용하며 전역 설정을 변경하지 않는다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\check.ps1 -Mode fast
```

실제 DB 필수 검사는 전용 테스트 서비스 준비 후 실행한다(아래는 Windows 명령이며, 당시에는 preflight 실패/non-zero까지 확인했다. 현재 WSL에서는 위의 `bash check.sh db`로 통과했다):
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\check.ps1 -Mode db -EnvFile .env.example
# 같은 pytest 직접 명령; 개인 로컬 설정은 .env.example 대신 .env 사용 가능
& $uv run --locked --env-file .env.example pytest -m postgres --require-postgres
```

Y3_TEST_DATABASE_URL 누락은 exit 4이며 개발 URL fallback은 없다. --require-postgres에서 선택된 postgres 테스트가 없으면 exit 4다. DB 테스트 skip/xfail/XPASS 또는 call 통과 누락도 non-zero다. 연결/preflight 실패는 exit 1이다. 일반 전체 pytest도 선택된 DB 테스트에 설정이 없으면 실패한다. DB 없는 검사에는 `-m "not postgres"`를 명시한다. wrapper의 EnvFile 생략 시 외부 환경변수만 사용한다.

쓰기 검사 전에 Settings 검증에 더해 `127.0.0.1:55433`, query override 없음, Docker 로컬 endpoint, Compose 프로젝트/서비스 label 및 포트 소유권을 확인한다. 이어 실제 DB/role `y3management_test` 및 서버 포트 5432를 확인한다. 비밀번호/DSN 대신 검증된 host/port/database/service만 출력한다. 통합 검사 대상은 Windows의 `desktop-linux` 또는 위 WSL의 `wsl-ubuntu`에 있는 이 전용 Compose 구성이다. 그 밖의 환경이나 native DB를 검증하려면 명시적인 대상 소유권 검증을 먼저 마련해야 한다.

통합 검사는 테스트 전용 `foundation002_<UUID>` 테이블 하나를 만들어 앱의 Engine/Session에서 commit 및 예외 rollback 후 다른 Session으로 결과를 확인한다. finally에서 자신이 만든 테이블만 삭제하며 schema/database reset은 없다. 앱 metadata나 Alembic revision에는 넣지 않는다. 정상 종료 후 별도 데이터 정리는 불필요하다. 강제 중단으로 객체가 남으면 실행 소유자가 해당 UUID 객체를 확인한 후 그 객체만 정리한다. 광범위한 drop/reset이나 볼륨 삭제를 실행하지 않는다. 다른 프로젝트 서비스는 중단하지 않는다.

## Alembic

```powershell
& $uv run --locked alembic heads
& $uv run --locked --env-file .env alembic upgrade head --sql
# 실제 전용 테스트 DB 준비 후: 대상 검증을 거쳐 온라인 current 실행
& $uv run --locked --env-file .env.example pytest -m postgres --require-postgres -k alembic
```

heads는 현재 revision 없음, offline upgrade는 환경 로딩/SQL 생성 경로 확인뿐이다. 현재 출력은 BEGIN/COMMIT이며 업무 schema 검증이 아니다. target_metadata와 revision이 없고 가짜 initial migration을 만들지 않았다. 앱은 create_all/자동 migration을 실행하지 않는다.

온라인 테스트는 preflight와 실제 연결 확인 후 자식 프로세스에 Y3_ENVIRONMENT=test, 검증한 Y3_TEST_DATABASE_URL을 Y3_DATABASE_URL로 주입해 `python -m alembic current`를 실행한다. 앱과 같은 load_settings/Database 경로를 사용한다. Windows 당시에는 preflight에서 차단됐지만 현재 WSL에서는 온라인 `current`가 통과했다. 첫 업무 revision의 upgrade/downgrade 검증은 별도 작업이다.

향후 schema 승인 뒤 별도 명령으로 migration을 작성·리뷰·적용한다. 운영에서는 앱 시작과 migration 실행 주체/순서를 분리해야 한다.

## 운영 형태의 실행 — 배포 미검증

서버용 환경변수는 외부에서 미리 주입한다. 개발 .env를 로딩하지 않는다. PowerShell 예시(backend/):
```powershell
& $uv sync --locked --no-dev
& $uv run --locked --no-dev uvicorn y3management.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log --log-config logging.json
```

Linux 서버 문서 예시(backend/, uv 설치 및 외부 설정 주입 후):
```sh
uv sync --locked --no-dev
uv run --locked --no-dev uvicorn y3management.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log --log-config logging.json
```

reload가 없고 loopback만 바인딩한다. 실제 서버/프로세스 관리자/프록시 구성은 미정이며 운영 Linux 서버 배포와 production DB 연결은 검증하지 않았다. Windows 로컬에서는 동일 factory의 비-reload liveness만 확인했다. --no-dev sync 이후 개발 검사는 uv sync --locked로 dev 그룹을 복구한다. migration은 별도 명령이며 배포 시 자동 실행하지 않는다.

WSL 이전 후 실제 검증 결과는 [WSL migration](../docs/architecture/wsl-migration.md)을 따른다.

## MFA-A 제한된 개발 실행

IAM을 켤 때 `Y3_IAM_MODE=s1_password`(과거 개발 예외) 또는 `Y3_IAM_MODE=mfa`를 명시한다.
설정 누락이나 등록 키 없음에 따른 자동 fallback은 없고 production 거부도 유지한다.
MFA 모드에서 새 설치 CLI에는 `--enrollment-file /절대경로/개인폴더/등록파일`이 추가된다.
개인폴더는 현재 Linux 사용자 소유의 0700이고 모든 경로 요소가 symlink가 아니어야 한다.
파일은 새 0600 파일로 생성된다. 비밀번호는 기존처럼 TTY에 직접 입력한다.
파일의 HTTPS `/enroll#token=...` 링크로 첫 키를 등록한 뒤 `/login`에서 비밀번호와 Passkey로 로그인한다.
정상 MFA 로그인 후 `/passkeys`에서 본인 키를 추가한다. Branch Admin은 기존 `/activate` 설정 링크에서
비밀번호와 첫 키 등록을 함께 완료한다. 실제 운영/복구/키 삭제/추가 Master 발급은 이번 범위가 아니다.

설치 CLI exit 2와 `INSTALLATION_COMMIT_UNKNOWN_RETAIN_PRIVATE_FILE`은 COMMIT 결과가 불명확하다는 뜻이다.
개인 등록 파일을 보존하고 실제 설치/전달 여부를 확인한다. bootstrap 재실행이나 직접 SQL 복구를 하지 않는다.
첫 등록 성공 또는 허가 미사용/만료와 정리 가능 여부를 확인한 뒤 자기 파일만 정리한다.
로그인 응답의 `mfa_cleanup_deferred`는 미전달 세션 철회 재시도/정리 확인이 필요한 실패이며 성공이 아니다.

개발 대상 검사는 `uv run --locked --env-file .env.example pytest -m postgres --require-postgres
 tests/test_iam_mfa.py tests/test_iam_mfa_security.py tests/test_iam_mfa_install.py tests/test_iam_mfa_races.py`
이고 실제 HTTPS 검사는 `tests/test_iam_browser.py::test_actual_https_mfa_browser`다.
기존 pytest의 소유 run/schema/process 정리 절차를 그대로 사용한다.
자세한 계약은 [IAM-005 MFA-A](../docs/architecture/iam-005-mfa-a-design.md)에 있다.

### IAM-006 MFA 관리·정상 Master 복구 개발 계약

`iam_mode=mfa`에서 본인 `/api/v1/auth/passkeys` 목록·삭제, 같은 조직 정상 Master의
`/api/v1/admin/master-accounts` 신규 발급·조회·설정 재발급, 다른 관리자의
`/api/v1/admin/accounts/{id}/passkey-recovery` 복구 시작·조회·재발급을 제공한다.
삭제는 다른 유효 키가 남을 때만 허용하며 현재 포함 모든 로그인을 종료한다.
`/passkeys`는 이 효과를 삭제 전에 설명하는 로컬 검수 화면이다.
복구 링크는 `/recover#token=...`에서 즉시 fragment를 제거하고 새 UV 키만 등록한다.
비밀번호는 보존되며 완료 후 기존 비밀번호와 새 키로 다시 로그인한다.
링크 원본을 로그·이슈·공유 결과에 복사하지 않는다. ACK 불명확 시 최소 상태 확인 뒤
명시적으로 재발급하며 옛 키/세션을 복원하지 않는다.

새 forward revision은 `0006_iam_mfa_management`다. 이전0001–0005를 수정하지 않으며
철회·복구·감사 사실이 남은 downgrade는 거부한다. 만료된 setup/recovery source의
GC는 잠긴 하위 context가 남으면 건너뛰고 다음 실행에서 정리한다. 임의 운영 보존기간을
정한 것이 아니다. 기존 QA 고유 실행·자기 자원 정리 절차를 그대로 사용한다.

실제 개발 검사와 독립 전체 인수는 [IAM-006 결과](../docs/architecture/iam-006-mfa-management-results.md),
최소 API/인가·원자성·실패 경계는 [IAM-006 설계](../docs/architecture/iam-006-mfa-management-design.md)를
확인한다. 정상 Master 기반 복구는 모든 Master 분실의 AB5나 production 운영 허가가 아니다.


### 관리자 비밀번호 재설정 (IAM-007, 결합 후보 인수 대기)

현재 정상 MFA Master는 같은 조직의 다른 ACTIVE Master/Branch Admin에 대해
`GET /api/v1/admin/accounts/{id}/password-reset`의 version/generation을 확인하고,
같은 경로에 `expected_account_version`, `expected_generation`, `identity_confirmed:true`로
POST한다. 시작 즉시 옛 비밀번호와 모든 로그인이 무효화된다. 반환 링크는 본인 확인 후
개인 전달하며 일반 로그·이슈에 복사하지 않는다. `/reset#token=...`에서 대상이 직접 새 암호를
설정한 다음 기존 Passkey와 새 암호로 로그인한다. 자동 로그인은 없다.

만료/전달 실패는 pending 상태를 조회한 뒤 `/reissue`에 현재 version/generation으로 명시
재발급한다. 본인 관리자 reset과 진행 중인 key recovery 중첩은 지원하지 않는다. C3 본인
암호 변경은 유지한다. 양쪽 요인을 잃었다면 M2와 reset을 순서대로 완료하며 중간 대상
로그인은 필요 없다. 운영 비상 복구 AB5는 별도다. [구현 계약](../docs/architecture/iam-007-password-reset-design.md).
