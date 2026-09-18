# ADR-0002 — 선택적 MSA 추출을 고려한 Modular Monolith

Status: ACCEPTED
Decision date: 2026-09-17
Approval source: 이번 사용자 지시의 단일 백엔드 배포·Modular Monolith·선택적 서비스 추출 방향 승인.
Scope: 시스템 형태, 모듈 데이터 소유권/계약 및 업무 트랜잭션 경계 관리 원칙만 ACCEPTED. 모듈 수·이름·배치·계약·공유 UoW·감사 배치는 PROPOSED다.

## Context

하나의 Organization에 여러 Branch가 있으며 독립 고객사 SaaS는 범위가 아니다. Pass·Session·Session Payment의 강한 일관성이 필요하다. 업무 정책 일부는 OPEN이며 초기부터 네트워크 경계로 나누면 그 정책 변화와 실패 처리를 함께 다뤄야 한다.

## Decision

초기에는 하나의 백엔드 애플리케이션으로 배포하고 PostgreSQL을 사용한다. 내부는 논리적 업무 모듈로 구분하고 각 데이터의 소유권·공개 인터페이스 및 업무 트랜잭션 경계를 관리한다. 실제 필요가 입증된 모듈을 향후 선택적으로 독립 서비스로 추출할 수 있게 설계한다. 모든 모듈의 서비스화를 약속하지 않는다. 단일 배포 단위는 프로세스/worker 수나 배포 환경을 확정하는 결정이 아니다.

## Alternatives considered

| 대안 | 이번에 채택하지 않는 이유/비용 비교 |
| --- | --- |
| 경계 없는 단일 애플리케이션 | 시작은 단순할 수 있으나 데이터 쓰기 책임과 영향 추적을 관리하기 어려움 |
| 처음부터 MSA | 현재 확정되지 않은 정책 위에 통신 실패·배포·분산 정합성 비용을 먼저 추가함 |
| 업무별 완전 독립 DB부터 구성 | 일반 Session의 원자성을 유지할 별도 해결책이 필요하고 현 단계 요구가 아님 |

위 비교는 본 제품에 대한 설계 판단이며 성능 실험 결과가 아니다.

## 선택 이유

현재의 원자적 업무 처리를 유지하면서 모듈 계약·소유권·의존성 검사를 먼저 정리한다. 추출 여부는 실제 운영·조직·배포 수요와 분리 비용을 비교하여 정한다. 인터페이스만 존재한다고 분산 트랜잭션 문제가 해결되지는 않는다.

## 단점과 감수하는 비용

초기 모듈들이 같은 배포·DB 장애 범위를 공유한다. 공유 트랜잭션, 제약 및 읽기 일관성은 추출을 제한한다. 경계 유지에는 코드 리뷰·의존성 검사·계약 테스트가 필요하며 자동 장치는 아직 없다. 서비스 추출 시 데이터 이전·대사·권한 전달·재시도·계약 호환성 비용이 추가된다.

## 후속 설계 제약

현재 정합성을 미래 MSA를 위해 약화시키거나 FK를 일괄 제거하지 않는다. 모듈 공개 계약은 내부 계약이며 HTTP/gRPC 명세가 아니다. 내부 HTTP, Kafka, Redis, 서비스 디스커버리, API Gateway, Kubernetes를 선행 도입하지 않는다. 필수 Session Payment와 감사 저장을 비동기 알림으로 대체하지 않는다.

[6개 모듈과 감사 기반 제안](../architecture/module-boundaries.md), [Application Use Case 트랜잭션 제안](../architecture/data-and-transactions.md), [추출 검토](../architecture/module-boundaries.md#extraction)은 모두 PROPOSED다. 이벤트/Outbox는 향후 필요가 확인될 때 검토하며 이번에는 이벤트 기반 구조를 채택하지 않는다.

## 공식 문서 확인

확인일: **2026-09-17**. 업무 경계 선택의 근거는 Product와 사용자 결정이며 공식 프레임워크 문서가 이 제품의 모듈 구성을 승인한 것은 아니다.

| 공식 자료 | 확인한 사실 | 이 ADR에서의 한계 |
| --- | --- | --- |
| [FastAPI Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/) | 여러 파일의 APIRouter를 하나의 애플리케이션에 포함 가능 | Router 분리가 업무 모듈/보안 경계의 자동 보장이라는 뜻 아님 |
| [SQLAlchemy transactions](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html) | 트랜잭션 범위를 명시하고 commit/rollback 관리 가능 | 모듈 간 같은 DB 트랜잭션 참여의 실제 구성은 후속 검증 |
| [PostgreSQL transactions](https://www.postgresql.org/docs/current/tutorial-transactions.html) | 한 트랜잭션 안 변경의 원자성 제공 | 서로 다른 서비스/DB까지 자동 확장되지 않음 |

선정 버전 조합, 네트워크 전환, 서비스 계약/장애 성능은 미검증이다.

## 재검토 조건

독립 배포 빈도·팀 소유권·부하 격리·장애 격리에 실제 수요가 생기고, 공유 트랜잭션을 해소할 승인 정책과 검증 근거가 마련되면 특정 후보의 추출 ADR을 별도로 작성한다. 원자성·권한·대사 요건을 만족하지 못하면 모놀리식 내부 경계를 유지한다.

## 관련 Product 근거

[PR-003/008/009/010/027/030/031](../product/requirements.md), [BR-PAY-006/009/010/011/012/014/015/016 및 BR-OPS-001](../product/business-rules.md), [MB-009](../product/open-questions.md#mb-009), [BR-013](../product/open-questions.md#br-013), [Architecture Handoff](../product/architecture-handoff.md).
