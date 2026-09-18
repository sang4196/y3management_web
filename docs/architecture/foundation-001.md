# FOUNDATION-001 — 최소 백엔드 기반

작성/확인일: 2026-09-17  
상태: 로컬 기반 구현. 실제 PostgreSQL 검증은 환경 제약으로 미수행이며 운영 배포 준비 완료가 아니다.

## 범위와 완료 조건

- PT 진행 등록은 기존 회원에게 실제 수업을 수행했다는 완료 기록으로 명확화한다. 상품/Pass 생성·예약·시간표가 아니고 사전 Reservation을 요구하지 않는다. PR-008/009·기존 지급 규칙/권한/OPEN을 유지한다.
- Python/FastAPI, 동기 SQLAlchemy/psycopg 3, uv, Ruff/mypy/pytest/Import Linter, Alembic 환경과 전용 로컬 DB 구성을 제공한다.
- 앱 생성/외부 설정/수명/로그, DB Session 정리, live/ready 및 최소 검사 명령이 실행 가능해야 한다.
- DB 접근이 불가능하면 mock·오프라인 검증을 수행하고 실제 연결/migration 검증을 미수행으로 구별한다.
- 업무 모델·진행 등록·급여/정산·로그인/가짜 관리자·프론트엔드·예약·MSA 통신은 구현하지 않는다. 이 작업 뒤 자동으로 업무 기능을 시작하지 않는다.

[개발 설치/실행/검사 안내](../../backend/README.md), [실제 선택·버전 ADR](../decisions/0003-foundation-tooling.md).

## 코드 경계와 수명

backend/src/y3management/의 main(factory 진입점), application(HTTP/자원 조립), database(Engine·Session factory·probe), config(설정 검증)만 구현했다. 빈 서비스/Repository/6개 업무 모듈을 미리 만들지 않았다. [업무 모듈 초안](module-boundaries.md)은 PROPOSED로 유지한다.

Engine은 앱 수명에 하나씩 소유하고 각 업무는 database.session()으로 독립 SQLAlchemy Session을 얻는다. 자동 commit은 없으며 종료/예외에 미완료 트랜잭션을 정리한다. 향후 Application Use Case가 명시적 transaction을 소유한다. SQLAlchemy Session은 PTSession이라는 수업 완료 기록과 다르다.

동기 DB 작업은 일반 def 흐름에서 실행한다. async lifespan 종료에서는 threadpool을 통해 dispose한다. 앱 시작 시 DB 연결을 강제하지 않아 DB 장애 중에도 live가 응답한다. ready는 별도 NullPool/단일 worker에서 SELECT 1을 수행하며 제한시간 내 200/503으로 응답한다. 기존 probe가 진행 중이면 공유하고 새 대기 작업을 쌓지 않는다.

응답 timeout이 native DB 호출의 강제 종료는 아니다. connect_timeout과 statement_timeout을 같이 설정하지만 DNS/네트워크 블랙홀·종료 시 thread join 지연·과부하에서의 응답시간은 실제 운영 장애 시험이 필요하다. shutdown은 새 검사를 막고 진행 중 호출의 context가 연결을 반환한다. 현재 성공 응답은 업무 schema/version readiness가 아니다.

요청 본문/자격증명/DB URL·예외 문자열은 로그와 오류 응답에서 제외한다. 일반 오류 코드만 남기므로 상세 진단은 향후 민감정보 없는 관측 설계가 필요하다.

## 실행 기록

작업 환경: Windows x64 PowerShell. 모든 backend 명령은 backend/에서 수행했다. 로컬 도구 경로 ../.tools/uv/bin/uv.exe를 uv로 줄여 표기한다. 루트 bootstrap은 python -m pip install --target .tools/uv uv로 실행하여 0.12.15를 설치했다. 재현 안내는 같은 버전을 지정한다.

| 실행 | 결과/범위 |
| --- | --- |
| 루트: git status, 파일 목록·상위 AGENTS 확인 | 기존 AGENTS/문서 미추적 상태 보존, 새 애플리케이션 없음 확인 |
| uv python install 3.13 (루트) | 안정판 3.13.15 설치, .python-version에 patch 고정 |
| uv sync | 44개 패키지 해결/설치; lock 생성 |
| uv run ruff check --fix / ruff format | 최초 import 정렬 및 긴 줄 발견, format 적용 |
| uv run mypy (최초) | Settings 환경 주입 생성자와 Any 반환 3건 발견; Pydantic plugin·bool 반환으로 수정 |
| uv run pytest (최초) | 26 passed / 실제 PG 1 skipped / 의존성 deprecation warning 2개 |
| uv run lint-imports | 실제 2개 계약 통과 |
| 역방향 config → application 임시 import 후 lint-imports --no-cache | 2개 계약 BROKEN 확인, 원본 bytes 복원. 첫 python -m importlinter 시도는 실행 진입점 부재로 실패하여 설치된 lint-imports 실행파일로 재검증 |
| Windows Uvicorn subprocess + loopback /health/live 요청 | 200 확인 후 해당 프로세스 종료. production DB·운영 서버는 사용하지 않음 |
| uv run --env-file .env.example alembic upgrade head --sql | 성공, BEGIN/COMMIT만 생성. offline env 실행 |
| uv run alembic heads | 성공, revision 없음 |
| docker compose config --quiet | 성공, 정적 구성 검사 |
| docker version | 클라이언트 28.3.2 존재, Docker Desktop Linux 엔진 pipe 없음. DB 기동/이미지 실행 미수행 |

최종 검사(backend/, uv 0.12.15):

| 명령 | 최종 결과 |
| --- | --- |
| uv sync --locked | 44개 해결 결과 유지/설치 상태 확인 |
| uv run --locked ruff check | 통과 |
| uv run --locked ruff format --check | 12개 파일 형식 통과 |
| uv run --locked mypy | 11개 소스 파일 통과 |
| uv run --locked pytest | 27 passed, 1 skipped(실제 PostgreSQL), 2 dependency deprecation warnings |
| uv run --locked lint-imports --no-cache | 실제 코드 2개 계약 KEPT, 0 BROKEN |

DB mock 검사와 실제 연결은 같지 않다. Alembic current/online upgrade, 실제 PostgreSQL 제약/동시성, 지급 계산, 지점 권한, Pass 차감, 운영 성능/복구/배포는 완료하지 않았다. 테스트 코드의 postgres marker는 명시적 전용 URL 없으면 skip하고, 잘못된 대상은 연결 전에 거부한다.

문서 검증은 별도로 로컬 링크/앵커 104개를 확인했고 깨진 참조가 없었다. Product 수정은 아래 5개 문서의 완료 기록 의미 명확화에 한정했다. 시작 시 기존 파일 해시와 최종 파일 목록을 대조했으며 docs/analysis/와 Product OPEN·기존 ADR-0001/0002는 변경하지 않았다. 기존 미추적 문서를 staging/commit하거나 되돌리지 않았다. 허용 범위 밖 소스/문서 변경은 없다.

## 변경 파일 목록

기존 파일 수정 11개:

- AGENTS.md
- docs/product/requirements.md, business-rules.md, users-and-roles.md, user-scenarios.md, scope.md
- docs/architecture/README.md, module-boundaries.md, data-and-transactions.md, decision-gates.md, validation-plan.md

신규 파일 24개:

- .gitignore
- backend/pyproject.toml, uv.lock, .python-version, .env.example, README.md, logging.json, compose.yaml, alembic.ini
- backend/src/y3management/__init__.py, main.py, application.py, config.py, database.py
- backend/tests/conftest.py, test_application.py, test_database.py, test_settings.py, test_postgres.py
- backend/alembic/env.py, script.py.mako, versions/.gitkeep
- docs/decisions/0003-foundation-tooling.md, docs/architecture/foundation-001.md

ignored 로컬 도구/가상환경/cache는 검증용이며 납품 소스가 아니다. 실제 .env는 생성하지 않았고 검증 시 명시적으로 예시 파일을 사용했다. 개인 PC 절대 경로·실제 비밀번호·운영 개인정보는 소스/문서에 넣지 않았다.

## 배포 준비와 남은 작업

준비한 것은 lock/버전 파일, 외부 설정 검증, 운영 형태의 비-reload 실행 명령, 자원 수명, 상태 endpoint, 명시적 migration 환경, 로컬 검사뿐이다.

| 후속 작업 | 결정/검증 필요 |
| --- | --- |
| 패키징/이미지 | wheel 또는 서버 이미지, OS/아키텍처, psycopg binary/libpq 패치 공급, 이미지 취약점/기동 검증 |
| HTTPS·프록시 | TLS 종료, 신뢰 프록시/헤더, health 노출 범위. 현재 인증 기능 없음 |
| 프로세스 시작/재시작 | 관리자·worker 수·종료 유예·재시도·과부하/정상 종료 검증 |
| 비밀정보 | 환경별 주입/권한/교체/회수, 운영 DB 최소 권한 role, 개발 예시 차단 외 실환경 검증 |
| migration | 실행 주체·앱과의 적용 순서·이전 버전 호환·실패 시 복구. 실제 schema 승인 후 작성/DB 검증 |
| 로그·모니터링 | 민감정보 없는 진단/지표, readiness 지연·DB pool·오류율·경보 |
| 백업·복구 | 보존/접근/주기·복구 목표 승인, 실제 복원·대사 시험 |
| 배포 후 점검·되돌림 | version/schema/업무 smoke, 트래픽 전환 기준, 데이터 변경 호환·복구 경로 |

클라우드 자원/공개 서버/운영 DB/CI/CD/비밀 등록을 하지 않았다. AWS/Kubernetes/운영 호스팅은 선택하지 않았다. Linux 명령은 문서만 제공했으며 실제 서버 배포를 검증하지 않았다.

## 남은 결정 게이트

T-03과 T-04 도구 선택은 ADR-0003으로 해결했다. T-02는 이번 Windows 기반 조합만 검증했고 실제 PostgreSQL/운영 OS 조합은 남았다. T-01 업무 모듈, T-05 인증, T-06 프론트엔드, T-07 운영 환경, T-08 브로커/캐시 필요성, T-09 업무 동시성/금액/보존 상세는 미결정이다.

Product 26 OPEN과 기존 CLOSED는 그대로다. 특히 MB-009 타 지점 보상, BR-013 추가실적, BR-012 기본급 적용 월, MB-010/MB-006 귀속/공개는 [결정 게이트](decision-gates.md)를 따른다. 예약을 선행 조건으로 추가하지 않았으며 본인 PT 진행 기록 권한을 보상 설정 조회 권한으로 확대하지 않았다.
