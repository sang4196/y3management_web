# 결정 게이트

Status: PROPOSED — 설계 진행 순서와 보류 경계의 제안
기준일: 2026-09-17
Product 질문/상태의 원본은 [open-questions.md](../product/open-questions.md)다. 실제 확인 결과 MB-009, BR-013, BR-012, MB-010/MB-006의 ID와 내용은 사용자 최근 보고와 일치한다. 원본 26 OPEN / 4 CLOSED 및 PD-021 OPEN은 이 작업에서 변경하지 않는다.

## 주요 금액·권한 게이트

| 실제 Product OPEN | 영향 모듈·업무 | 현재 설계 가능 | 결정 전 확정 금지 | 결정 시점 |
| --- | --- | --- | --- | --- |
| [MB-009](../product/open-questions.md#mb-009) 타 지점 보상 구성 | PT/Workforce/Settlement의 타 지점 지급 | 실제 Session/Performed Branch·Pass 일관성, 소유권과 대사 책임 | 일반 Session Payment+추가실적 자동 지급, 기본 Payment 0원+추가실적, A/B 어느 쪽의 예상 금액/저장 흐름 | 타 지점 보상 상세 설계·구현 전 |
| [BR-013](../product/open-questions.md#br-013) 추가실적 처리 | Workforce·연계 PT/회원·Settlement | 실적 업무 개념·감사 경계·Session 비연계 가능 | Master/Branch Admin 등록 허용, Branch 기준, Trainer 신청, 승인 생략/단계, 수동/유형 금액·정정/취소·마감 이후 전이 | 실적 권한·명령/상태/금액 상세 전 |
| [BR-012](../product/open-questions.md#br-012) 기본급 적용 | Workforce/Settlement | 월 고정 설정·과거 확정 기본급 보존·중복 가산 방지 | 당월/익월 자동 적용, 적용 월 지정 UI, 미확정 월 자동 갱신, 입퇴사 등의 임의 금액 | 기본급 적용/정산 반영 상세 전 |
| [MB-010](../product/open-questions.md#mb-010) 지점 귀속 | Workforce/PT/Settlement | Home/Issued/Performed/귀속 개념 분리 | 이동 시 기본급/실적 귀속, 수행 지점=비용 지점 가정, 지점별 합산/배분 규칙 | 지점 정산/비용 집계·공개 전 |
| [MB-006](../product/open-questions.md#mb-006) 정산 공개 | Settlement/PT/Workforce/Audit | 제한된 읽기 계약·우회 노출 방지 | Branch Admin의 공개 Trainer·월·금액·계산 근거 범위, 정산 권한으로 타 지점 설정 접근 허용 | 정산/Session/감사 지급정보 열람 상세 전 |

보상 설정 변경 권한과 별도 승인 없음은 이미 확정이다. 이를 BR-013 추가실적 승인 또는 BR-009 월 마감/확정에 적용하지 않는다. OPEN을 “일단 허용”, “일단 0원”, “일단 모든 지점 차단”이라는 업무 기본값으로 구현할 수 있다고 처리하지 않는다. 해당 기능의 상세 확정·구현을 보류하고 독립적인 승인 범위 작업을 진행한다.

## 나머지 Product OPEN의 추적

| 실제 OPEN | 영향 모듈·업무 | 현재 가능한 설계 | 미정 동작/결정 필요 시점 |
| --- | --- | --- | --- |
| [MB-001](../product/open-questions.md#mb-001) | Workforce/PT: Trainer 이동·대상 회원 | 단일 소속·지원 수업과 소속 불변, 권한 경쟁 식별 | 이동 적용 시점/과거 정책·조회 Member 범위; 이동/교차 PT 상세 전 |
| [MB-002](../product/open-questions.md#mb-002) | Membership/PT: Member 이동·교차 이용 | 단일 Home Branch와 제한된 대상 사실 계약 | 이동/교차 업무·열람 조건; 관련 상세 전 |
| [MB-003](../product/open-questions.md#mb-003) | PT: Pass 교차 사용 | Issued Branch와 사용 가능 지점 구분·우선순위 유지 | 발급 지점 밖 구체 이용 조건; Pass 선택/권한 상세 전 |
| [MB-004](../product/open-questions.md#mb-004) | IAM/Organization | 단일 Branch Admin Scope·Master 구조 관리 | Operator Scope, 자기 지점 수정·계정 발급 위임; 관련 권한 상세 전 |
| [MB-005](../product/open-questions.md#mb-005) | PT/회원/Trainer | 본인 등록과 정정 권한 구별·서버 검증 경로 | Trainer 본인 정정/취소 및 교차 대상 조건; Session 권한 상세 전 |
| [MB-007](../product/open-questions.md#mb-007) | PT Catalog | 공통 상품, 기존 Master 생성/수정 유지 | Branch Admin 상품 생성/수정 허용; 상품 권한 상세 전 |
| [MB-008](../product/open-questions.md#mb-008) | Organization 및 전체 참조 모듈 | 비활성 이후 과거 결과 보존 | 비활성 조건·진행 업무 자동 이동/중단; 지점 수명 상세 전 |
| [BR-001](../product/open-questions.md#br-001) | PT Pass | 종료 이력 보존·상태 책임 소유 | 시작/종료/재개/자동 만료·잔여 소멸; 상태 상세 전 |
| [BR-002](../product/open-questions.md#br-002) | PT 횟수 | 정상 차감/사유·이력/복원 일관성 | 최초 부여·추가/조정 범위·사용 조건; 잔여 명령 상세 전 |
| [ARCH-003](../product/open-questions.md#arch-003) | PT 후보 Pass | 복수 Pass 지원·FIXED_AMOUNT 우선/FIFO | 상태/사용 조건/수량 상한; 후보 선택 상세 전 |
| [BR-007](../product/open-questions.md#br-007) | PT/Settlement | 원자적 정정 경계 후보·이력 | 허용 항목/기간/사유·종료/잔여0·확정 이후 정정; 정정 구현 전 |
| [BR-008](../product/open-questions.md#br-008) | PT/Settlement | 개별 날짜 원본·중복 요청과 별개 수업 구분 | 시간대·소급 허용·동일 날짜 복수 수업/월 경계; 날짜/집계 상세 전 |
| [BR-009](../product/open-questions.md#br-009) | Settlement | 세 구성 합계·과거 결과 보존 | 추가 통계 채택, 확인/마감/확정·후속 정정 전이; 정산 수명 상세 전 |
| [BR-010](../product/open-questions.md#br-010) | PT/Workforce/Settlement | 계산식과 오류 발생 시 원자성 | 범위·정밀도·누락값·0회 분모 안내; 입력 검증/금액 표현 상세 전 |
| [BR-011](../product/open-questions.md#br-011) | PT 상품/Pass/Payment | 과거 확정 지급 불변·상품 쓰기 소유 | 상품 Price/Count/Type 변경의 기존 Pass 이후 Session 적용; 상품 변경 상세 전 |
| [ARCH-001](../product/open-questions.md#arch-001) | IAM/전체 업무/Audit | Role/Scope 분리·확정 설정 인가 | 정정/감사 세부 열람의 Product 확인과 기술 모델; 권한 상세 확정 전 |
| [ARCH-002](../product/open-questions.md#arch-002) | IAM | 관리자 발급·계정 분리 | 초기 계정/재설정/중단/마지막 Master/만료; 인증·계정 상세 전 |
| [ARCH-004](../product/open-questions.md#arch-004), [PD-021](../product/product-decisions.md#pd-021) | 전체 운영·Responsive | 품질 검증 분류/측정 항목 | 브라우저·성능·백업/복구·가용성·책임 정량 목표; NFR 수용 기준·실운영 전 |
| [UX-001](../product/open-questions.md#ux-001) | PT 입력 | 개별 Session 원본 단위 | 여러 날짜 일괄 입력 채택과 오류 UX; 편의 기능 채택 전 |
| [OPS-001](../product/open-questions.md#ops-001) | 운영 준비/전체 | 빈 데이터 신규 시작·이관 없음 | 책임/시작일/준비·전환 판정; 실운영 전 |
| [LEGAL-001](../product/open-questions.md#legal-001) | 개인정보·감사/전체 | 최소 수집·제한 열람·보존 책임 | 필드·열람·보존 기간·필요 삭제; 관련 상세 및 실운영 전 |

BR-003/004/005/006은 CLOSED다. RATE/서비스/FIFO/적용·확정의 해결된 규칙을 재질문하지 않는다. 위 표의 ARCH 접두어가 기술만으로 모든 업무 정책을 결정해도 된다는 의미는 아니다.

## Product에서 후속으로 확인할 표현·누락

원문은 수정하지 않았다. 아래는 새 승인 사항이 아닌 해석 경계/변경 제안이다.

- 일부 요약 참조는 MB-001–008까지만 적혀 있으나 실제 MB-009/010과 BR-012/013이 존재한다. 이 설계는 실제 항목 전체를 추적한다. Product의 요약 참조 범위 정리는 별도 수정 후보다.
- SC-005는 “정산 조회 권한을 가진 Operator”를 조건으로 쓰지만 BR-PAY-010은 Base Salary를 포함한 설정 조회를 금지한다. 정산 구성/계산 근거에서 설정을 노출·추론하게 되는 경우 공개 범위를 ARCH-001/MB-006에서 명확히 해야 한다. Operator 정산 권한이나 기본급 열람을 새로 허용하지 않는다.
- FIFO의 “먼저 들어온” 값과 동률 기준, 등록/설정 경합의 일관 순서점은 구현 전에 문서화할 필요가 있다. 기술 표현을 선택할 수 있으나 실제 업무 우선순위나 BR-PAY-011 적용 의미를 바꾸게 되면 BR-002/ARCH-003 또는 해당 규칙의 사용자 확인으로 되돌린다.

<a id="technical-gates"></a>
## 미승인 기술 결정

아래 T-ID는 이 Architecture 문서의 추적 ID이며 Product OPEN을 새로 생성하거나 CLOSED 처리하지 않는다. 아래 표는 1차 설계 당시 OPEN 목록이다. FOUNDATION-001에서는 [ADR-0003](../decisions/0003-foundation-tooling.md)에 따라 T-03(동기 SQLAlchemy·psycopg 3), T-04(uv·Ruff·mypy·pytest·Import Linter)를 선택했다. T-02의 Windows 기반 버전 선택/설치 검증 이후, [WSL 이전 검증](wsl-migration.md)에서 실제 PostgreSQL 기반 검사까지 통과했다. 업무 schema migration·지급 계산 및 업무 동시성·운영 조합 검증은 남는다. 다른 게이트와 구체 업무 모듈 PROPOSED 상태는 유지한다.

| ID | 결정할 항목 | 선행 근거·결정 시점 |
| --- | --- | --- |
| T-01 | 구체 모듈 경계·데이터 소유권·공개 계약·Audit 배치·UoW 구성 | 이 초안 검토 후 패키지/저장 상세 확정 전 |
| T-02 | Python/FastAPI/SQLAlchemy/Alembic/PostgreSQL 및 전이 의존성 버전 | 지원 수명·공식 호환 조건 검토와 선택 조합 시험 후 환경 고정 전 |
| T-03 | 동기/비동기 SQLAlchemy와 PostgreSQL 드라이버 | 호출 방식·운영 부하·세션 수명·T-02 호환성 검토 후 데이터 어댑터 전 |
| T-04 | 패키지 관리·의존성 고정·타입/의존성/테스트 검사 도구 | 재현 환경·검증 계획 검토 후 scaffold/검사 구성 전 |
| T-05 | 인증 방식·라이브러리 | ARCH-001/002·계정 수명·클라이언트 경계 검토 후 인증 설계 전; JWT/Cookie/OAuth 미선정 |
| T-06 | 프론트엔드 프레임워크 | Responsive 및 Future 제약을 근거로 UI 상세/구현 전 |
| T-07 | 배포 환경·서버 운영 구성·비밀 관리·복구 절차 | ARCH-004/PD-021·OPS-001 후 운영 설계/출시 전 |
| T-08 | 메시지 브로커·캐시 필요 여부와 제품 | 실제 전달/성능 필요가 확인될 때. 지금 필수 의존성이나 기본 선택 없음 |
| T-09 | 잠금/격리·재시도·멱등성 구조·금액 표현·과거 결과 보존·migration 운용 | 관련 Product 게이트와 실제 PostgreSQL 검증 전략을 갖춘 뒤 DB/동시성 상세 전 |

모든 게이트가 해결될 때까지 공통 검토를 멈추지는 않는다. 다음 작업의 대상과 필요한 게이트를 좁혀 확인한다. 게이트 해소는 문서/승인 근거로 확인하며 시간이 지났다는 이유로 승인으로 보지 않는다.
