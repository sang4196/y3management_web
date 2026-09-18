# ADR-0003 — FOUNDATION-001 동기 백엔드 기반과 검증 도구

Status: ACCEPTED  
Decision date: 2026-09-17  
Approval source: FOUNDATION-001 사용자 지시의 구성 지정 및 지원 버전 선택 위임.  
Scope: 동기 SQLAlchemy, psycopg 3, uv, Ruff, mypy, pytest, Import Linter와 이번 최소 기반 구현. 6개 업무 모듈 초안·업무 UoW/동시성·인증·운영 환경 전체를 승인하는 결정은 아니다.

## Context

[ADR-0001](0001-backend-stack.md)의 제품 선택, [ADR-0002](0002-modular-monolith.md)의 단일 배포/추출 방향을 유지한다. 이전 T-02/03/04의 기반 선택을 이번 지시로 구체화한다. PT 진행 등록은 기존 회원의 실제 수업 완료 기록이며 이번에는 구현하지 않는다([PR-008](../product/requirements.md#pr-008)).

## Decision 및 이유

- 동기 SQLAlchemy + psycopg 3: 현재 단일 업무 트랜잭션의 호출 흐름과 수명을 명시하기 쉽다. 동기 DB 경로는 일반 def로 호출한다. FastAPI event loop에서 blocking DB 작업을 직접 하지 않는다. 성능 우월성을 주장하지 않는다.
- uv: Python/가상환경과 의존성을 관리하고 uv.lock으로 재현한다. 실행 시 --locked로 의도하지 않은 해결 결과 변경을 막는다. 운영 의존성과 dev 그룹을 구별한다.
- Ruff lint/format, mypy strict(Pydantic plugin), pytest, Import Linter: 실제 패키지의 코드 품질·타입·기반 동작·의존성 방향을 검사한다. 현재 계약은 main → application → database → config 및 DB/설정의 HTTP Framework 비의존이며 미래 업무 모듈 검증을 대신하지 않는다.
- Python 3.13의 지원 중인 안정 패치를 선택했다. 설치된 기존 Python 3.9를 프로젝트 런타임으로 쓰지 않는다. 설치/실행을 확인한 조합을 고정하고 prerelease는 제외한다.
- psycopg binary wheel을 로컬 기반에서 사용한다. 운영 이미지의 libpq/OpenSSL 공급·패치 방식과 source/C 빌드 채택 여부는 서버 패키징 시 재검토한다.
- 설정은 Pydantic Settings로 외부 주입·검증하고 Uvicorn factory로 실행한다. .env 자동 로딩·DB fallback은 없다. 운영 실행은 reload 없이 외부 설정을 요구한다.
- 로컬 DB 후보는 PostgreSQL 17.11이다. 지원 중인 17 계열의 공식 현재 minor와 이미지 태그를 확인했다. Docker 엔진 부재로 이미지 실행/실제 서버 연결은 미검증이다. 운영 DB 버전/호스팅 승인으로 확대하지 않는다.

## 실제 설치 및 검증 버전

확인일: **2026-09-17**, Windows x64, CPython **3.13.15**, uv **0.12.15**.

| 용도 | 설치 버전 |
| --- | --- |
| Runtime | FastAPI 0.141.1, Uvicorn 0.53.0, SQLAlchemy 2.0.54, Alembic 1.20.0 |
| Driver/설정 | psycopg 및 psycopg-binary 3.3.5, pydantic-settings 2.15.0, Pydantic 2.13.5 |
| 주요 전이 의존성 | Starlette 1.6.0, AnyIO 4.15.1 |
| 개발·검사 | Ruff 0.16.8, mypy 2.3.1, pytest 9.1.1, Import Linter 2.15, HTTPX 0.28.1 |
| 로컬 DB 구성만 제공 | PostgreSQL 17.11 — 실제 실행/호환성 미검증 |

전체 해결 버전·배포 파일 해시는 [uv.lock](../../backend/uv.lock)에 있다. PyPI 안정 배포본 해결/설치와 아래 테스트는 확인했으나 모든 OS·서버·부하 조합의 호환성 보증은 아니다. Starlette TestClient의 HTTPX 및 BlockingPortal 관련 deprecation warning 2개가 있으며 숨기지 않았다. 후속 호환 업데이트 시 테스트 클라이언트 API를 함께 검토한다.

## Alternatives considered

async SQLAlchemy, 다른 드라이버, pip/Poetry, 별도 formatter/linter, 타입·의존성 검사를 리뷰에만 맡기는 방식은 비교 대안이다. 이번 사용자가 도구를 지정했으므로 재선정하지 않았다. Python 3.14 및 PostgreSQL 18도 지원 계열이나 이번 실행 조합으로 채택하지 않았다. 벤치마크는 하지 않았다.

## 비용과 제약

동기 DB 호출은 worker/thread와 connection pool 용량을 소비한다. Readiness는 단일 probe worker에서 동기 호출하며 응답 대기시간을 제한한다. 제한시간 만료가 실행 중인 native DB 호출을 강제 종료하지는 않는다. 대기 작업은 하나로 제한하고 연결/statement timeout을 함께 설정했지만 DNS/망 장애 시 프로세스 종료 지연은 운영 장애 시험 대상이다.

현재 DB Session context는 수명만 관리하며 자동 commit하지 않는다. 향후 Application Use Case가 명시적 begin/commit을 소유한다. 이는 일반 PT 진행 등록 원자성 구현 완료가 아니다. 앱 시작 create_all/migration은 금지하며 Alembic은 별도 실행한다. 아직 metadata/revision/업무 테이블이 없다.

보상 설정 조회 금지·지급 규칙·Product OPEN은 유지한다. 인증, 프론트엔드, 운영 패키징/호스팅, HTTPS, 비밀 관리, 업무 잠금/격리·멱등성·감사 구조는 미결정이다.

## 공식 문서 근거

모두 2026-09-17 확인. 문서 기능 확인과 설치/실행 확인을 구별한다.

| 공식 자료 | 확인한 범위 |
| --- | --- |
| [Python 지원 상태](https://devguide.python.org/versions/) | 3.13 지원 중; 3.9 지원 종료 |
| [uv 설치](https://docs.astral.sh/uv/getting-started/installation/) | 독립 도구/PyPI 설치 방식 |
| [FastAPI 동기 호출](https://fastapi.tiangolo.com/async/) | 일반 def 경로 호출과 비동기 처리 구분 |
| [SQLAlchemy psycopg](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg) | psycopg dialect 및 동기 Engine 사용 |
| [psycopg 설치](https://www.psycopg.org/psycopg3/docs/basic/install.html) | binary/local 설치 선택과 제약; 문서 dev 표기를 배포판 채택으로 취급하지 않음 |
| [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | 환경변수 기반 설정 |
| [Ruff](https://docs.astral.sh/ruff/), [mypy](https://mypy.readthedocs.io/en/stable/getting_started.html), [pytest](https://docs.pytest.org/en/stable/) | lint/format·타입·테스트 도구 역할 |
| [Import Linter layers](https://import-linter.readthedocs.io/en/stable/contract_types/layers/) | 실제 모듈의 단방향 import 계약 |
| [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html) | 환경/버전 스크립트와 명시적 명령 |
| [Uvicorn 설정](https://uvicorn.dev/settings/) | factory, reload, host, 로그 구성 |
| [PostgreSQL 지원](https://www.postgresql.org/support/versioning/), [공식 이미지](https://github.com/docker-library/docs/blob/master/postgres/README.md) | 17.11 지원 및 이미지 태그·전용 DB 초기 설정 |
| [libpq 연결](https://www.postgresql.org/docs/current/libpq-connect.html) | connect_timeout 등 연결 옵션; 모든 장애의 wall-clock 종료 보증은 아님 |

## 재검토 조건 및 추적

지원 종료/보안 업데이트, dependency 경고의 제거·호환성 변화, worker 부하 또는 DB 장애 시험 실패, 서버 이미지/SSL 빌드 요구가 생기면 버전과 선택을 재검토한다. lock 업데이트는 검사와 명시적 diff 검토를 동반한다.

[작업 범위·실행 결과](../architecture/foundation-001.md), [개발 안내](../../backend/README.md), [Product 게이트](../architecture/decision-gates.md), PR-008/009, BR-PAY-010/011/012, NFR-001/002/003/005.
