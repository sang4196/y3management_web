# FOUNDATION-002 — 실제 PostgreSQL 검증과 필수 검사 모드

확인일: 2026-09-17  
상태: **BLOCKED — 로컬 Docker 엔진 접근 불가**. 검사 기준/테스트 보완과 DB 없는 검증은 완료했지만 PostgreSQL 성공 경로 검증을 완료하지 않았다. 운영 배포 준비 완료가 아니다. [FOUNDATION-001](foundation-001.md)의 당시 미검증 기록은 그대로 보존했다.

## 환경 진단

Windows x64 PowerShell, 기존 Python 3.13.15/uv 0.12.15와 uv.lock을 사용했다. 의존성·Compose 이미지 버전은 변경하지 않았다.

- Docker CLI 28.3.2 사용 가능. context는 전후 모두 desktop-linux, endpoint는 로컬 npipe:////./pipe/dockerDesktopLinuxEngine이다. DOCKER_HOST/DOCKER_CONTEXT 환경 override는 발견하지 않았다.
- 최초 docker version: 엔진 pipe 없음. docker desktop status: 실행 상태 조회 불가.
- 지원 명령 docker desktop start --timeout 45 시도: exit 1, “Docker Desktop is still starting: context deadline exceeded”.
- 이후 명시적 context의 version 조회에서 HTTP 500 응답 및 20초 제한 재조회 timeout. 최종 docker desktop status는 stopped였다. 엔진 정상 연결을 확인하지 못했다.
- Docker API 버전 호환성이나 앱 결함으로 원인을 단정하지 않았다. 사용자 터미널에서 성공한다는 증거는 없으므로 사용자/Codex 권한 차이도 확정하지 않는다.
- Desktop 재설치, WSL/OS 설정, 전역 context 변경, 컨테이너/볼륨 삭제, prune, 다른 서비스 중단은 하지 않았다. 엔진이 준비되지 않아 compose up도 실행하지 않았다.

## 대상과 접근 제한

아래는 **Compose에서 확인한 예정 대상**이며 실제 DB 연결 성공 정보가 아니다.

| 서비스 | 호스트 포트 | DB / role | 용도 |
| --- | --- | --- | --- |
| postgres-dev | 127.0.0.1:55432 | y3management_dev | 프로젝트 개발 |
| postgres-test | 127.0.0.1:55433 | y3management_test | 프로젝트 검증 전용 |

프로젝트는 y3management-foundation, 이미지 postgres:17.11, 두 서비스의 볼륨은 분리돼 있다. 정적 compose config 검사를 통과했다. 비밀번호/환경 파일 내용은 기록하지 않는다.

통합 fixture는 앱 Settings 검증에 더해 정확한 host/port, URL query 없음, 로컬 Docker endpoint, Compose project/service label, 실제 host port 소유권을 먼저 확인한다. 이후 앱 Database/Session에서 current_database/current_user/inet_server_port를 조회해 테스트 대상인지 다시 확인한다. 안전 확인 실패는 DB 연결/DDL 전에 중단한다. 개발 URL fallback은 없다. 현재 이 검사는 Windows Docker Desktop의 해당 Compose만 지원하며 다른 환경은 별도 대상 검증이 필요하다.

## 구현한 검증

- 기존 postgres marker를 유지하고 --require-postgres를 추가했다. postgres 테스트가 선택되면 URL 누락은 exit 4다. 옵션 사용 시 postgres 미수집도 exit 4이며, 기본 pytest의 완전 미수집 exit 5도 성공이 아니다.
- 선택한 DB 검사에서 skip/xfail/XPASS 또는 call 통과 누락은 non-zero다. 일반 전체 pytest도 DB 설정 없이 조용히 skip하지 않는다. DB 없는 검사는 -m "not postgres"로 명시한다.
- check.ps1은 fast/db 모드를 제공하며 하위 실패 코드를 그대로 반환하고 fast 모드에서 실패 이후 검사를 계속하지 않는다.
- 정상 DB용 검사는 앱 Engine/Session factory로 UUID 이름의 테스트 소유 테이블을 만든다. 실제 insert+commit 후 새 Session에서 확인하고, 다른 insert 직후 예외가 발생한 경우 Session 정리에 의한 rollback 후 새 Session에서 값이 남지 않음을 확인한다. 바깥 fixture rollback으로 결과를 가장하지 않는다.
- 성공/실패 후 pool 반환, Session 객체 독립성, 후속 쿼리, 실제 DB 기반 live/ready, Alembic current를 검사하도록 작성했다. 해당 정상 DB 검사 3개는 현재 preflight에서 차단됐다.
- 테이블은 해당 테스트가 생성한 단일 foundation002_<UUID> 객체만 finally에서 drop한다. 앱 metadata/revision에는 추가하지 않았다. 실제 실행은 차단돼 객체를 생성/삭제한 적 없다.
- 별도 DB 없는 테스트는 로컬 socket을 bind하되 listen하지 않아 다른 서비스에 닿지 않는 실패 포트를 확보한다. 실제 앱 Database/psycopg 경로로 /health/live 200, /health/ready 503, 대기시간 제한 및 비밀번호/전체 DSN/traceback 비노출을 확인했다. DB 정상 연결 증거는 아니다.
- 검사 정책 subprocess 테스트는 pass/missing/empty/skip/xfail/XPASS/fail/실제 드라이버 연결 거부의 종료 코드를 확인한다. 합성 pass는 검사 하네스 동작일 뿐 정상 PostgreSQL 통과로 집계하지 않는다.

## 실행 명령과 결과

위치: backend/ (진단 일부는 저장소 루트). uv는 실제 ../.tools/uv/bin/uv.exe를 사용했으며 아래에는 uv로 줄여 표기했다.

| 명령/검증 | 실제 결과 |
| --- | --- |
| 기존 uv run --locked pytest -m "not postgres" | 변경 전 27 passed / 1 deselected, 경고 2건 재현 |
| Ruff check --fix / format, mypy | import 정렬·긴 줄 수정 후 통과 |
| powershell -NoProfile -ExecutionPolicy Bypass -File ./check.ps1 -Mode fast | Ruff lint/format, mypy, pytest, Import Linter 순차 실행; 최종 결과 아래 |
| 빠른 pytest | 36 passed, 정상 DB 검사 3 deselected, 0 skipped, 경고 2건 |
| Ruff / mypy / Import Linter | lint·format 통과(14개), 타입 13개 소스 통과, 의존성 계약 2개 KEPT |
| DB URL을 제거한 자식 프로세스 pytest -m postgres --require-postgres | exit 4, 명확한 필수 설정 누락 오류 |
| check.ps1 -Mode db (URL 없음) | 실제 자식 PowerShell exit 4 확인 |
| uv run --locked --env-file .env.example pytest -m postgres --require-postgres | exit 1, 3 setup errors. Docker compose ps timeout으로 소유권 확인 실패, DB 미접근. skip 아님 |
| 합성 검사 정책 subprocess | pass=0, missing/empty=4, skip/xfail/XPASS/fail=1 |
| 제어된 실제 드라이버 연결 거부 subprocess | exit 1. 앱 Database/Session 사용, 다른 서비스 미접근 |
| 테스트 URL에 개발 포트 55432를 지정한 필수 검사 | exit 1, 실제 연결 전에 거부. 출력에 비밀번호 sentinel/전체 DSN이 없음을 확인 |
| docker --context desktop-linux compose config --quiet | 통과, 엔진 연결을 증명하지 않음 |
| uv run --locked alembic heads | 성공, revision 없음 |
| 실제 Alembic online current | BLOCKED. 통합 테스트 preflight에서 중단, 온라인 연결은 미검증 |

정상 DB 설정으로 통과 → 잘못된 연결로 실패 → 정상 복원 후 재통과 순서는 엔진 부재로 완료하지 못했다. 연결 거부/설정 누락/skip 차단의 실제 종료 검증을 정상 DB 검증으로 대체하지 않는다. 기존 앱 자원 관리 코드에서 확인된 결함은 없으며 이번 작업에서 앱 코드는 변경하지 않았다.

## 의존성 경고 분석

기존 경고 2건을 실제 재현하고 설치된 소스를 읽었다. 개인 PC 절대 경로 대신 환경 내 상대 위치를 기록한다.

1. StarletteDeprecationWarning:
   > Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.

   표시 위치는 .venv/Lib/site-packages/fastapi/testclient.py:1, 실제 warn 호출은 starlette/testclient.py:47이다. FastAPI가 재노출한 Starlette 1.6.0 TestClient가 httpx2 import 실패 시 HTTPX 0.28.1로 fallback하면서 발생한다. 프로젝트 업무 코드의 경고가 아니며 현재 테스트 요청은 통과한다. 향후 fallback 제거/클라이언트 API 변화 가능성이 있어 테스트 클라이언트 호환성 업데이트 때 재검토해야 한다.

2. DeprecationWarning:
   > The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.

   표시 위치는 starlette/testclient.py:53의 타입 별칭 참조다. AnyIO 4.15.1의 anyio/abc/__init__.py:61에서 deprecated alias 대상을 확인했다. 의존성 내부 참조이며 현재 TestClient 수명/요청 테스트는 통과한다. 향후 alias 제거 시 import/테스트 실행에 영향을 줄 수 있어 Starlette/AnyIO 호환 업데이트 시 재검토한다.

이번에는 warning filter나 전체 출력 억제를 추가하지 않았고, 단순 최신화·HTTPX2 설치·lock 변경도 하지 않았다. 이 두 경고가 현재 테스트를 실패시키지 않는다는 사실만 확인했으며 모든 상황에서 무해하다고 판단하지 않는다.

## 재실행 및 정리

[개발 안내](../../backend/README.md)의 정확한 명령을 따른다. 엔진을 정상 시작한 뒤 기존 context를 변경하지 않고 version 확인 → 프로젝트 compose up → 필수 DB 검사를 수행한다. 최소 검사:

```powershell
# backend/에서; 먼저 Docker Desktop 로컬 엔진 및 전용 서비스 준비
powershell -NoProfile -ExecutionPolicy Bypass -File ./check.ps1 -Mode fast
powershell -NoProfile -ExecutionPolicy Bypass -File ./check.ps1 -Mode db -EnvFile .env.example
```

위 두 명령은 별도 검사이며 하나의 배치로 연결한다면 첫 실패 코드를 확인해 중단해야 한다. 온라인 Alembic만 확인할 때는 다음 명령을 사용한다. 이번에는 preflight 이후 실행은 BLOCKED다.

```powershell
& $uv run --locked --env-file .env.example pytest -m postgres --require-postgres -k alembic
```

테스트가 명시적 환경 주입으로 python -m alembic current를 호출한다. 현재 revision 없음 상태를 그대로 검사하며 stamp/가짜 migration/create_all을 추가하지 않았다. 정상 테스트 종료 시 테스트 객체만 자동 정리한다. 컨테이너/볼륨을 자동 삭제하지 않는다. 강제 중단으로 잔여 객체가 생겼다면 소유 UUID를 확인해 해당 객체만 정리하며 광범위 reset을 하지 않는다.

## 변경 범위와 남은 작업

수정: AGENTS.md, backend/README.md, backend/tests/conftest.py, backend/tests/test_postgres.py.  
생성: backend/check.ps1, backend/tests/test_driver_failure.py, backend/tests/test_postgres_gate.py, 이 기록.

Product/AS-IS/업무 규칙/모듈 책임, 기존 FOUNDATION-001 기록과 ADR, pyproject.toml/uv.lock, 앱 소스, Compose, Alembic 환경/revision은 변경하지 않는다. 실제 DB 업무 객체·운영 환경도 변경하지 않았다.

완료 전 작업 시작 시 파일 해시와 최종 목록을 대조해 위 수정 4개/생성 4개만 확인했다. 기존 파일 삭제는 없고 허용 범위 밖 변경도 없다. 변경 문서의 로컬 링크 19개는 대상이 존재한다. 문서 링크 확인과 코드/실제 DB 검증은 별개다. 기존 미추적 파일 상태를 보존했으며 커밋하지 않았다.

다음 검증을 막는 것은 로컬 Docker 엔진의 미기동이다. 엔진이 정상화되면 실제 연결·commit/rollback·자원 반환·정상 readiness 및 Alembic 온라인을 재실행해야 한다. 첫 업무 schema upgrade/downgrade, Pass 동시 차감·지급 원자성, 업무 API/인증/예약/급여와 운영 배포는 이번 범위 밖이다.

설계 근거 확인(2026-09-17): [pytest hooks](https://docs.pytest.org/en/stable/reference/reference.html#pytest.hookspec.pytest_sessionfinish), [SQLAlchemy Session transaction](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#framing-out-a-begin-commit-rollback-block). 설치된 버전에서 종료 정책을 별도로 실행 검증했다.
