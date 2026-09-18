# 백엔드 개발·검증 안내
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
