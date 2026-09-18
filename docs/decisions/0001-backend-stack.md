# ADR-0001 — Python + FastAPI 백엔드와 데이터 기술

Status: ACCEPTED
Decision date: 2026-09-17
Approval source: 이번 Architecture 1차 설계 요청의 사용자 승인 기술 목록.
Scope: 기술 제품 선택만 승인됨. 버전·드라이버·동기/비동기·인증·패키지 도구·배포 세부와 아래 연결 설계는 승인 범위가 아니다.

## Context

새 PT 웹 서비스는 일반 Session 등록의 Pass 차감·기록·지급 확정 일관성, 보상 설정의 지점 권한, 과거 지급/정산 보존을 요구한다. 기존 C# 구현/DB와 호환하거나 데이터를 이관할 필요가 없다. Product가 프레임워크를 선택한 것은 아니며, 이번 사용자 지시가 기술 선택 근거다.

## Decision

백엔드 언어는 Python, 웹 프레임워크는 FastAPI, 데이터 접근은 SQLAlchemy, 스키마 변경 관리는 Alembic, 데이터베이스는 PostgreSQL을 사용한다. 타입 검사·모듈 의존성 검사·업무/권한/동시성 테스트를 후속 검증 체계에 포함한다. 아직 설치·버전 고정·환경 구성은 하지 않는다.

## Alternatives considered

다른 언어/웹 프레임워크, 직접 SQL 중심 접근, 다른 관계형 DB, 수동 스키마 변경 관리를 비교 대상으로 식별했다. 이번 작업에서 성능 벤치마크나 후보별 실험은 수행하지 않았다. 사용자가 위 조합을 승인했으므로 다시 선택하지 않으며 다른 기술이 부적합하다고 단정하지 않는다.

## 선택 이유

사용자가 선택한 Python 기반으로 웹 입출력·데이터 접근·변경 관리의 역할을 구분할 수 있다. 아래 공식 문서의 트랜잭션·타입·migration 기능은 후속 검증을 설계할 근거다. 이 조합이 업무 정합성·권한을 자동 보장하거나 다른 스택보다 항상 빠르다는 뜻은 아니다.

## 단점과 감수하는 비용

타입 표기만으로 실행 중 타입 검증이 보장되지 않아 정적 검사와 업무 검증이 별도로 필요하다. ORM 수명과 트랜잭션을 잘못 다루면 부분 반영·동시성 오류가 생길 수 있어 통합 검증이 필요하다. Alembic 자동 생성 결과의 수동 검토와 PostgreSQL 운영·복구 책임을 감수한다. 구체 호환 버전 조합은 아직 검증하지 않았다.

## 후속 설계 제약

- FastAPI는 입출력 어댑터로 사용하고 업무 로직의 Request/Depends 직접 종속을 피하는 안은 PROPOSED다.
- SQLAlchemy의 업무 단위 트랜잭션 참여, 공개 계약의 ORM 비노출은 [데이터·트랜잭션 초안](../architecture/data-and-transactions.md)을 검토한다.
- Product의 migration tooling 제외는 C# 운영 데이터 이관 제외다. 새 DB 스키마 변경 관리용 Alembic 채택과 충돌하지 않는다.
- 버전, 동기/비동기 SQLAlchemy, PostgreSQL 드라이버, 패키지 관리, 인증 방식/라이브러리, 배포 환경은 [기술 게이트](../architecture/decision-gates.md#technical-gates) 결정 후 구성한다. 공식 문서 URL의 버전은 채택 버전이 아니다.
- 프론트엔드·브로커·캐시를 이 결정에 끼워 넣지 않는다. DB schema/API/설치 코드도 이번 산출물이 아니다.

## 공식 문서 확인

확인일은 모두 **2026-09-17**. 웹 문서 확인이며 로컬 설치/호환성 실행 시험은 아니다.

| 공식 자료 | 확인한 기능·제약 | 검증 한계 |
| --- | --- | --- |
| [Python typing](https://docs.python.org/3/library/typing.html) | 타입 표기는 Python 런타임에서 자동 강제되지 않으며 별도 검사 도구에 사용 가능 | 검사기와 Python 버전 미선정 |
| [FastAPI Features](https://fastapi.tiangolo.com/features/) | Python 타입 선언을 사용하고 OpenAPI 문서 기능 제공 | 업무 인가/정합성을 대신하지 않음; 성능 비교 미실시 |
| [SQLAlchemy PostgreSQL dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html) | PostgreSQL 접근을 위한 dialect/드라이버 지원 문서 존재 | 드라이버·구체 호환 버전 조합 미선정·미검증 |
| [SQLAlchemy transactions](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html) | 트랜잭션 범위와 commit/rollback 관리 지원 | 프로젝트 UoW 구현 미검증 |
| [SQLAlchemy Session basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html) | Session/AsyncSession은 동시 thread/task 공유 대상으로 사용하지 않음 | sync/async 선택 아님 |
| [Alembic 소개](https://alembic.sqlalchemy.org/en/latest/) | SQLAlchemy와 함께 사용하는 migration 도구 | migration 환경 미구성 |
| [Alembic autogenerate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html) | 자동 생성 migration은 후보이며 수동 검토·수정 필요 | 무검토 자동 배포 근거가 아님 |
| [PostgreSQL transactions](https://www.postgresql.org/docs/current/tutorial-transactions.html) | 트랜잭션 변경의 원자적 commit/rollback | 업무 경계와 격리 전략을 자동 결정하지 않음 |
| [PostgreSQL isolation](https://www.postgresql.org/docs/current/transaction-iso.html) | 격리 수준별 관찰/동시성 차이가 있음 | 특정 격리 수준 채택 없음 |

## 재검토 조건

선정할 버전/드라이버 조합이 요구 기능·지원 환경을 충족하지 못하거나, 실제 부하·복구 검증에서 운영 목표를 만족하지 못할 때 근거를 모아 새 ADR 또는 이 ADR의 명시적 대체를 검토한다. 성능 예상만으로 기술을 교체하지 않는다.

## 관련 Product 근거

[Architecture Handoff](../product/architecture-handoff.md), [PR-008](../product/requirements.md#pr-008), [PR-010](../product/requirements.md#pr-010), [BR-PAY-009](../product/business-rules.md#br-pay-009), [BR-PAY-010](../product/business-rules.md#br-pay-010), [NFR-001/002/012](../product/non-functional-requirements.md), [PD-017/021](../product/product-decisions.md). Product OPEN은 유지한다.
