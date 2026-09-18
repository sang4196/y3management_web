# Architecture 및 현재 개발 단계

현재 단계: 최소 백엔드 기반 구성 및 WSL에서 실제 PostgreSQL 기반 검증 완료. [FOUNDATION-001](foundation-001.md)과 [ADR-0003](../decisions/0003-foundation-tooling.md)에 따라 backend/를 구성했으며, 현재 [실행 안내](../../backend/README.md)와 [WSL 이전 검증 기록](wsl-migration.md)을 따른다. 빠른 검사와 실제 PostgreSQL 검사 3개(트랜잭션·세션 정리, health, Alembic 온라인 `current`)가 통과했다. FOUNDATION-001/002의 Windows 당시 미검증·BLOCKED 기록은 이력으로 유지한다. 업무 schema migration·지급 계산 및 업무 동시성·운영 배포 준비 검증은 완료하지 않았고, PT 진행 등록 등 업무 기능도 구현하지 않았다. 6개 업무 모듈 상세는 PROPOSED다.

아래는 **Architecture 1차 설계 당시의 결정·검증 기록**이다. 당시의 구현 금지/도구 미선정/검사 미구성 설명은 그 작업 시점에 한정하며 현재 기반 상태는 위 문서와 ADR-0003이 갱신한다.

작성일: 2026-09-17
상태: **기술/시스템 형태 ADR은 ACCEPTED, 구체 설계는 PROPOSED**.
이 단계는 문서 설계이며 scaffold·애플리케이션·DB schema·API·테스트 코드·migration 환경을 만들지 않는다. 다음 작업을 자동 시작하지 않는다.

## 입력과 문서 상태

[Product Baseline](../product/README.md)의 13개 문서 전체를 읽고 현재 규칙과 이전 결정 이력을 구분했다. [Architecture Handoff](../product/architecture-handoff.md)와 [OPEN](../product/open-questions.md)을 입력으로 사용했다. Product/analysis는 수정하지 않는다. 기존 AGENTS.md 및 Architecture/ADR 문서는 작업 시작 시 발견되지 않아 아래 문서를 새로 구성했다. 기존 docs/ 미커밋·미추적 자료를 보존한다.

이 저장소 파일 목록에 C# 소스는 없으며 C# 구현을 확인했다고 주장하지 않는다. 이번 설계는 승인된 Product로 충분하여 docs/analysis/ 본문을 추가 조사하지 않았다. [Validation Needed](../product/validation-needed.md)의 AS-IS 미검증 상태도 유지한다.

## 승인된 방향과 제안의 경계

| 상태 | 범위 |
| --- | --- |
| ACCEPTED — ADR-0001 | Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL. 타입·의존성·업무/권한/동시성 검사 포함 방향 |
| ACCEPTED — ADR-0002 | 초기 단일 백엔드 배포, Modular Monolith, 모듈 데이터 소유권/계약·업무 트랜잭션 관리, 선택적 서비스 추출 |
| PROPOSED — 이 Architecture | IAM/Organization/Membership/Workforce/PT Operations/Settlement 6개, Audit 기반, 의존성 DAG, 내부 계약, Application UoW, 추출 후보·검증 상세 |
| OPEN | 버전·sync/async·드라이버·패키지 도구·인증·배포·프론트엔드·브로커/캐시·모듈 상세 승인 |

ADR의 ACCEPTED는 구체 모듈/트랜잭션 설계를 승인한 것이 아니다. 공식 문서 기능 확인일과 한계는 각 ADR에 기록했다. Product 문서가 당시 “기술 선택 없음”이라고 기록한 부분은 이전 단계의 범위 설명이며, 이번 사용자 기술 승인만 ADR로 추가한다. Product 업무 정책을 변경하지 않는다.

## 읽기 순서

1. [루트 AGENTS.md](../../AGENTS.md)와 [Product Handoff](../product/architecture-handoff.md)
2. [ADR-0001 Backend Stack](../decisions/0001-backend-stack.md), [ADR-0002 Modular Monolith](../decisions/0002-modular-monolith.md)
3. [모듈 경계·소유권·서비스 추출](module-boundaries.md)
4. [데이터 접근·트랜잭션·권한](data-and-transactions.md)
5. [Product/기술 결정 게이트](decision-gates.md)
6. [후속 검증 계획](validation-plan.md)

별도 ADR 형식이 없으므로 순번 파일에 Status/Context/Decision/대안/이유/비용/제약/재검토/근거를 기록한다. 후속 ADR은 기존 번호와 충돌하지 않게 추가하고 기존 결정 변경 시 대체 관계를 명시한다.

## 핵심 제안

PT Operations가 Product·Pass·Session·확정 Payment를 함께 소유한다. 정책이 확정된 일반 Session 등록의 차감·기록·지급 결과·필수 감사를 Application Use Case의 한 PostgreSQL 트랜잭션에서 완료하거나 취소하는 안이다. Repository별 commit은 기본 구조로 사용하지 않는다.

Workforce의 보상 설정 소비, IAM의 현재 권한, Member/Trainer 소속 사실도 이 업무의 일관성에 참여한다. 공개 인터페이스를 둬도 이 결합이 사라지지 않으며 서비스 추출 전에 적용 순서·권한·실패 복구를 다시 설계해야 한다. Audit은 공통 기반으로 제안하고 독립 서비스로 만들지 않는다. 직접 cross-module DB 조회 예외는 승인 0건이다.

설정 조회/변경은 Master 전체 및 Branch Admin의 자기 Home Branch 소속 Trainer만 허용하고 Operator/Trainer는 본인 포함 불가다. 별도 Master 승인 없이 변경하며 감사한다. Performed Branch를 설정 권한 근거로 쓰지 않는다. 계산용 내부 소비와 사용자 조회 권한은 구별한다.

## 주요 Product 결정 게이트

MB-009(타 지점 보상 대체/추가), BR-013(추가실적 권한·승인·금액·정정), BR-012(기본급 적용 월/미확정 정산), MB-010/MB-006(지점 귀속/정산 공개)은 실제 원문과 일치한다. 금액·권한·상태를 임의 확정하지 않는다. 나머지 21개 OPEN과 PD-021도 [게이트 표](decision-gates.md)에 추적했다.

Product 요약 참조 범위, Operator 정산 화면을 통한 설정 노출, FIFO 동률/설정 경합 순서점의 해석 경계는 같은 문서에 후속 확인으로 남겼다. 이번에 Product OPEN을 CLOSED 처리한 항목은 없다. Responsive Web은 v1, Member 로그인·일정/예약/취소·Mobile App은 Future를 유지한다. 독립 고객사 SaaS는 추가하지 않는다.

## 다음 결정과 진입 조건

공통 모듈 책임·계약·인가·원자성 검토는 계속 가능하다. 모든 OPEN이 끝나야만 모든 설계를 시작한다는 의미는 아니다.

- 상세 설계 전: 대상 기능을 정하고 T-01 모듈/소유권 제안을 검토한다. 해당 기능의 Product 게이트가 해소됐는지 근거를 확인한다. 미결정 기능의 금액/권한/상태 상세는 보류한다.
- 환경/scaffold 전: 사용자의 다음 작업 범위와 T-02 버전, T-03 sync/async·드라이버, T-04 패키지/검사 도구를 결정한다. 인증·UI·배포 작업은 각각 T-05/06/07을 선행한다. 브로커·캐시 T-08은 필요가 생길 때 검토한다.
- 업무 구현 전: 선택한 흐름의 계약·인가·금액·트랜잭션/동시성·보존 설계(T-09)를 검토하고 필요한 테스트 환경/기준을 구성한다. 실제 PostgreSQL 동시성 검증을 단위 테스트로 대체하지 않는다.
- 서비스 추출 전: 별도 필요성/비용 근거와 추출 ADR, 공유 트랜잭션 해소, 계약 호환·이전/대사·실패/되돌림 검증을 마련한다.

AGENTS.md는 다음 구현을 영구 금지하지 않는다. 지금은 자동 검사 장치/실행 가능한 pytest·linter·Alembic 환경이 없으며 명령을 실행 가능하다고 안내하지 않는다.

## 이번 작업 검증

2026-09-17에 다음 문서 검증을 수행했다.

- 링크 검사: 신규 8개 문서의 로컬 링크 81개에 대해 대상 파일 및 지정 앵커 존재를 확인했다. 깨진 참조는 없었다. Product ID 참조의 존재와 실제 26개 OPEN의 게이트 표 포함도 확인했다.
- 설계 정합성 검토: 단일 쓰기 소유권, 의존성 방향, 일반 Session의 차감/기록/지급/감사 원자성, 보상 설정 권한, 과거 확정 결과 보존, 타 지점 보상 등 OPEN의 보류 경계를 원문과 대조했다. 모듈 구성·UoW·추출안은 PROPOSED로 유지했다. 이는 구현 검증이 아니다.
- 변경 범위: 작업 시작 시 기존 28개 파일의 SHA-256과 대조하여 변경/삭제가 없음을 확인했다. 추가 파일은 AGENTS.md, Architecture 5개, ADR 2개뿐이다. 기존 docs/는 미추적 상태이므로 일반 git diff만으로 범위를 판단하지 않고 파일 목록과 해시도 대조했다.
- 공식 문서 확인과 확인일은 각 ADR에 기록했다. 라이브러리 설치·호환성 시험, 애플리케이션 테스트, PostgreSQL 동시성/제약 시험, migration, 자동 타입/의존성 검사, 운영 검증은 수행하지 않았다. [V-01–20](validation-plan.md)은 실행 결과가 아닌 후속 검증 계획이다.
