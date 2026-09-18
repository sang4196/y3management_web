# Product Decisions — 승인 반영

승인 근거: 기존 2026-09-15~17 결정 및 2026-09-17 최신 지점 관계·추가실적·월 기본급·보상 설정 권한 확정. 현재 유효 결정은 각 Decision에 기록하며 폐기된 방향은 README 변경 이력으로 구분한다.

Status 정의: CLOSED = 사용자가 제품 방향을 승인함(제외·보류 승인 포함). OPEN = 아직 후속 단계에서 결정할 내용이 남음. **PD-001–020 및 PD-022–027은 CLOSED(26개), PD-021은 OPEN(1개)**이다. 세부 규칙은 [Open Questions](open-questions.md)로 분리하여 기존 PD를 다시 OPEN으로 만들지 않는다.

<a id="pd-001"></a>
## PD-001

Question: 웹 시스템의 실제 운영 사용자는 누구이며 업무별 권한을 어떻게 나눌까?

Status: CLOSED

Decision / approved direction: Role은 행위, Data Scope는 허용 데이터 범위다. Master Admin은 Organization 전체, Branch Admin은 하나의 Branch, Operator는 허용 Branch·업무, Trainer는 Allowed PT Scope의 로그인 Actor다. Rate / Fixed Amount / Base Salary 세 항목의 조회·설정·변경은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 단일 Branch를 Home Branch로 가진 Trainer에게만 허용한다. Operator와 Trainer는 본인 설정을 포함하여 모두 불가하다. 타 지점 지원 수업은 보상 설정 접근 권한을 부여하지 않는다. Backend에서 대상 Trainer의 Home Branch를 검증하며 직접 ID 요청과 감사·정산 등 우회 경로에도 제한을 적용한다. 모든 보상 설정 변경(최초 설정 포함)에 대상 Trainer, 변경 항목, 변경 전 값, 변경 후 값, 변경 Actor, Actor의 권한 및 Branch Context, 변경 시점을 추적한다. 별도 Master Admin 승인 없이 변경 가능하며 변경 요청→승인 대기→승인→반영 절차를 추가하지 않는다. 이 결정은 추가실적 승인이나 월 정산 마감/확정 절차를 면제하지 않는다.

Approval source: 2026-09-17 최신 사용자 지점 관계·추가실적·월 기본급·보상 설정 권한 확정. 충돌하는 이전 방향은 대체하며 비충돌 결정을 유지한다.

Follow-up: ARCH-001/002, MB-004/006. RBAC/ABAC 등 기술 모델과 세부 Permission은 Architecture에서 결정한다. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): 08 인증·권한; R35. [분석 색인](../analysis/README.md)

<a id="pd-002"></a>
## PD-002

Question: 트레이너가 직접 로그인할 수 있어야 하는가?

Status: CLOSED

Decision / approved direction: Trainer는 v1부터 직접 로그인하며 허용된 Member/PT 업무 조회, 자신이 실제 진행한 Session 등록 및 자신의 Session 조회를 수행한다. 정상 등록 시 사용할 Pass 결정 → Pass 차감 → Product Payment Type 확인 → 해당 시점 Trainer Rate/Fixed Amount 적용 → Session Payment 계산·확정 흐름을 따른다. 지급 설정 조회·변경은 불가하다.

Approval source: 2026-09-17 사용자 Multi-Branch 제품 방향 변경 지시. 충돌하는 이전 결정은 본 결정으로 대체하며 기존 비충돌 규칙은 유지한다.

Follow-up: MB-001/005: 조회 가능한 Member와 교차 지점 업무 조건, 본인 정정/취소. 타 지점 보상 구성은 MB-009 결정 게이트. PR-008/029.

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): 02 도메인; 08 인증·권한. [분석 색인](../analysis/README.md)

<a id="pd-003"></a>
## PD-003

Question: 회원 본인의 웹 접근을 제공할까?

Status: CLOSED

Decision / approved direction: Member는 v1 관리 대상 Domain이며 직접 로그인 Actor가 아니다. Member Authentication/Self-Service는 추가 계획이 있는 명시적 Future Scope다. 향후 자신의 PT Schedule·예약 Session·Pass·잔여 조회, PT 예약 및 Schedule 취소를 고려한다. Member와 Login Account는 현재 동일 개념이 아니다.

Approval source: 2026-09-17 사용자 Multi-Branch 제품 방향 변경 지시. 충돌하는 이전 결정은 본 결정으로 대체하며 기존 비충돌 규칙은 유지한다.

Follow-up: PD-025/026; 향후 Account 연결은 Architecture/Product Expansion에서 정의한다. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): 02 도메인; 08 인증·권한. [분석 색인](../analysis/README.md)

<a id="pd-004"></a>
## PD-004

Question: v1에서 몇 개 센터와 어떤 센터 간 접근을 지원할까?

Status: CLOSED

Decision / approved direction: 하나의 헬스장 Organization이 여러 Branch를 운영한다. 독립 고객사 SaaS는 추가하지 않는다. Master Admin의 Branch 등록·전체 조회·정보/구조 관리와 활성/비활성 관리 가능성은 유지한다. Trainer는 한 시점에 Home Branch 하나에 소속되고 Branch에는 여러 Trainer가 있을 수 있다. Branch당 Trainer 한 명인 1:1이나 Trainer 동시 복수 소속 N:M을 요구하지 않는다. Member도 Home Branch 하나를 가지며 Pass는 Issued Branch 하나를 가진다. Trainer·Member·Pass는 허용된 조건에서 타 지점 PT 업무를 수행·이용할 수 있다. Session은 실제 Performed Branch를 식별하고 소속·발급 지점 변경으로 과거 수행 지점이 바뀌지 않아야 한다. Product는 Organization 공통 Catalog이며 지점별 가격 정책은 추가하지 않는다. Branch Admin은 하나의 Branch를 관리하고 일부 여러 지점만 담당하는 중간 관리자 역할은 추가하지 않는다.

Approval source: 2026-09-17 최신 사용자 지점 관계·추가실적·월 기본급·보상 설정 권한 확정. 충돌하는 이전 방향은 대체하며 비충돌 결정을 유지한다.

Follow-up: MB-001–008의 남은 이동·교차 업무 허용 조건·조회·관리 정책과 MB-010 지점 귀속. 확정된 단일 소속·공통 Catalog를 다시 미정으로 두지 않는다.

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): R01/R35; K35. [분석 색인](../analysis/README.md)

<a id="pd-005"></a>
## PD-005

Question: 모바일·태블릿과 지원 브라우저의 범위는 무엇인가?

Status: CLOSED

Decision / approved direction: v1은 Desktop/Tablet/Smartphone에서 주요 정보와 Action을 실질적으로 사용할 수 있는 Responsive Web이다. 터치 조작을 고려하며 Desktop 화면 단순 축소는 충족 기준이 아니다. Trainer의 현장 Smartphone Session 등록은 주요 Use Case다.

Approval source: 2026-09-17 사용자 Multi-Branch 제품 방향 변경 지시. 충돌하는 이전 결정은 본 결정으로 대체하며 기존 비충돌 규칙은 유지한다.

Follow-up: ARCH-004; breakpoint·지원 브라우저·Frontend 기술은 후속 설계. Mobile App은 PD-026의 Future Direction. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): 04 화면; 10 전환; NEW-CANDIDATE. [분석 색인](../analysis/README.md)

<a id="pd-006"></a>
## PD-006

Question: 제안한 v1 범위와 출시 수용 기준을 승인할까?

Status: CLOSED

Decision / approved direction: 기존 핵심 PT 운영, Organization/Branch, Backend 권한 제한, Trainer 로그인/Session 등록, Responsive Web을 유지한다. Trainer별 월 고정 Base Salary와 Additional Performance를 v1에 포함한다. 가계부·락커·수동 매출·고정 거래 및 기존 Future Scope는 v1에서 제외한다.

Approval source: 2026-09-17 최신 사용자 지점 관계·추가실적·월 기본급·보상 설정 권한 확정. 충돌하는 이전 방향은 대체하며 비충돌 결정을 유지한다.

Follow-up: 기존 BR/ARCH/OPS 및 MB-001–008. Future Scope는 PD-003/025/026. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): 03 기능; 06 흐름. [분석 색인](../analysis/README.md)

<a id="pd-007"></a>
## PD-007

Question: 회원의 PT 이용정보를 어느 수준으로 관리할까?

Status: CLOSED

Decision / approved direction: 명시적인 PT Pass를 도입한다. 회원은 시간에 따라 여러 Pass 이력을 가지며 종료된 Pass도 보존한다. Pass는 PT Product, Assigned Trainer, Purchased/Remaining Sessions, Status, 생성/시작 정보, PT Session 이력을 설명하는 이용 단위다.

Approval source: 2026-09-15 승인 및 2026-09-16 BR-PAY-001–008 정정 승인. 상세 TODO만 후속.

Follow-up: 2026-09-16 BR-PAY-006에 따라 복수 사용 가능한 Pass의 FIXED_AMOUNT 우선 차감을 지원한다. 동일 Payment Type FIFO도 확정이다. BR-001/002, ARCH-003은 상태·횟수·사용 조건 등 상세만 검토. [확정 규칙](business-rules.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): F04; R04/R05. [분석 색인](../analysis/README.md)

<a id="pd-008"></a>
## PD-008

Question: 진행 기록의 날짜·횟수 단위와 중복 판단을 어떻게 정할까?

Status: CLOSED

Decision / approved direction: 실제 진행 날짜별 개별 PT Session을 원본으로 기록한다. 월 단위 여러 회 합계를 원본으로 저장하지 않는다. 정상 Session 등록 시 지급액을 계산·확정하며 월 정산의 Session 구성은 유효 확정 결과 집계다. 전체 월 정산은 PD-012, 타 지점 지급 구성은 MB-009를 따른다.

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: BR-008, UX-001; 일괄 입력 편의와 원본 단위 구분. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): F18/F19; R13/R20/R21. [분석 색인](../analysis/README.md)

<a id="pd-009"></a>
## PD-009

Question: 지급단가·서비스 단가·반올림·공제 의미를 어떻게 정할까?

Status: CLOSED

Decision / approved direction: Product는 RATE/FIXED_AMOUNT 방식을 결정한다. Trainer Compensation Setting은 Product와 독립적인 Trainer별 Rate, Fixed Amount, 월 고정 Base Salary다. Product별 Trainer 지급 값은 도입하지 않는다. 일반 RATE는 해당 상품 회당 단가 × Trainer Rate 결과를 Session별 1,000원 단위 올림하며 FIXED_AMOUNT와 서비스 상품은 Trainer Fixed Amount 그대로다. Rate / Fixed Amount / Base Salary 세 항목의 조회·설정·변경은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 단일 Branch를 Home Branch로 가진 Trainer에게만 허용한다. Operator와 Trainer는 본인 설정을 포함하여 모두 불가하다. 타 지점 지원 수업은 보상 설정 접근 권한을 부여하지 않는다. Backend에서 대상 Trainer의 Home Branch를 검증하며 직접 ID 요청과 감사·정산 등 우회 경로에도 제한을 적용한다. 모든 보상 설정 변경(최초 설정 포함)에 대상 Trainer, 변경 항목, 변경 전 값, 변경 후 값, 변경 Actor, Actor의 권한 및 Branch Context, 변경 시점을 추적한다. 별도 Master Admin 승인 없이 변경 가능하며 변경 요청→승인 대기→승인→반영 절차를 추가하지 않는다. 이 결정은 추가실적 승인이나 월 정산 마감/확정 절차를 면제하지 않는다. Rate/Fixed Amount는 관리자 저장 완료 이후 새로 등록되는 Session부터 적용하고 정상 등록 시 지급액을 계산·확정한다. 과거 확정 지급액은 재계산하지 않는다. 기본급 적용 월은 BR-012, 타 지점 수업 지급 구성은 MB-009 OPEN이다.

Approval source: 2026-09-17 최신 사용자 지점 관계·추가실적·월 기본급·보상 설정 권한 확정. 충돌하는 이전 방향은 대체하며 비충돌 결정을 유지한다.

Follow-up: BR-003/004/005/006은 CLOSED. 입력값 BR-010, Product 변경 BR-011, 정정 BR-007, 기본급 BR-012, 타 지점 보상 MB-009 및 추가실적 BR-013은 후속 OPEN. [확정 규칙](business-rules.md), [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): R09/R10/R14/R15; K04/K24/K25. [분석 색인](../analysis/README.md)

<a id="pd-010"></a>
## PD-010

Question: 기록 정정·삭제·횟수 복원은 누가 어떤 조건으로 할까?

Status: CLOSED

Decision / approved direction: 제한된 권한과 허용 Branch Scope 안에서 운영자가 Session을 정정/취소할 수 있다. Trainer 본인 정정/취소 허용 여부는 MB-005 OPEN이다. Pass 잔여와 정산 데이터의 일관성이 반드시 유지되어야 하며 단순 행 삭제로 처리하지 않는다.

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: BR-007, ARCH-001, MB-005; 상세 취소/정정 모델은 후속. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): F20/F21; R16–R19. [분석 색인](../analysis/README.md)

<a id="pd-011"></a>
## PD-011

Question: 비활성화·이력 조회·완전 삭제를 어떻게 구분할까?

Status: CLOSED

Decision / approved direction: 운영 데이터는 비활성화/상태 변경과 이력 보존을 우선한다. 회원·트레이너·Pass 중단 후에도 과거 Session·정산 이력을 조회한다. Hard Delete는 기본 운영 기능이 아니다.

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: BR-001/007, LEGAL-001. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): R02; K14/K34. [분석 색인](../analysis/README.md)

<a id="pd-012"></a>
## PD-012

Question: 정산 지표의 정의와 대상은 무엇인가?

Status: CLOSED

Decision / approved direction: Monthly Settlement = 해당 월 적용 Base Salary + 유효한 Session Payment 합계 + 유효한 Additional Performance 합계다. Trainer·대상 월·적용 기본급·Session 수·Session Payment 합계·추가실적 내역/합계·월 정산 합계를 구분한다. 2,500,000원 + 1,200,000원 + 150,000원 = 3,850,000원이며 여러 지점 수업으로 동일 월 기본급을 중복 가산하지 않는다. 타 지점 Session Payment 포함 여부는 MB-009 결정 전 확정하지 않는다. 현재 Base Salary 변경으로 과거 확정 월 정산의 적용 기본급·합계가 자동 변경되어서는 안 된다. 현재 Rate/Fixed Amount로 과거 확정 Session Payment를 재계산하지 않는다. Master Admin은 전체 정산을 관리하며 Branch Admin 정산 공개 범위와 지점 귀속은 MB-006/010 OPEN이다. 기본급 일할·근무일수·휴직 기반 자동 계산과 12개월 고정 평균은 제공하지 않는다.

Approval source: 2026-09-17 최신 사용자 지점 관계·추가실적·월 기본급·보상 설정 권한 확정. 충돌하는 이전 방향은 대체하며 비충돌 결정을 유지한다.

Follow-up: BR-007/008/009/010/011/012, MB-006/009/010; 기본급 적용 월·미확정 정산 반영, 정정·마감/확정 절차, 지급 구성·귀속·열람 결정 전 관련 상세 설계 보류.

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): F26/F27; R22; K34. [분석 색인](../analysis/README.md)

<a id="pd-013"></a>
## PD-013

Question: 수동 트레이너 매출 기능을 유지하고 무엇을 매출로 부를까?

Status: CLOSED

Decision / approved direction: 수동 트레이너 매출은 v1 제외다. 기존 매출 자료 조회/이관도 하지 않는다. 향후 실제 필요가 확인되면 별도 요구사항화한다.

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: 후속 제품 확장 후보. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): F22–F25; K37; verification-report. [분석 색인](../analysis/README.md)

<a id="pd-014"></a>
## PD-014

Question: 가계부를 웹 v1에 포함하고 잔액 조정을 어떻게 허용할까?

Status: CLOSED

Decision / approved direction: 가계부는 v1 제외다. PT 관리와 별도 bounded context 후보이며 필요 시 Product Expansion으로 검토한다.

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: 경계 후보일 뿐 이번 문서에서 Architecture를 확정하지 않음. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): F37–F48/F52; R28–R31/R34. [분석 색인](../analysis/README.md)

<a id="pd-015"></a>
## PD-015

Question: 고정 거래 실행 시점·말일·누락분·중단 규칙은 무엇인가?

Status: CLOSED

Decision / approved direction: 가계부 제외에 따라 고정 거래 실행 정책 검토를 현재 보류한다. v1에 고정 거래를 구현하지 않는다.

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: 보류 결정은 승인됨; 실행 규칙은 후속 가계부 채택 시. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): F49–F51/F53; B07; R32/R33. [분석 색인](../analysis/README.md)

<a id="pd-016"></a>
## PD-016

Question: 락커 운영 정책과 v1 필요성은 무엇인가?

Status: CLOSED

Decision / approved direction: 락커는 v1 제외다. 향후 별도 기능으로 추가할 수 있다.

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: 후속 제품 확장 후보. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): F28–F33; R24–R27. [분석 색인](../analysis/README.md)

<a id="pd-017"></a>
## PD-017

Question: 기존 데이터 이관은 필요한가? 어느 기간·도메인까지 옮길까?

Status: CLOSED

Decision / approved direction: 기존 운영 데이터를 이관하지 않는다. 빈 운영 데이터에서 시작하며 Master Admin/기준정보도 새로 설정한다. 기존 schema·데이터·결함의 호환성을 요구하지 않는다. Migration tooling은 v1 제외다.

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: OPS-001; 기존 잔여·과거 Session·계정/암호·매출 조회도 이관 범위 없음. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): 05 DB; 10 전환; K11/K20/K21. [분석 색인](../analysis/README.md)

<a id="pd-018"></a>
## PD-018

Question: 기존 프로그램과 병행할까, 한 번에 전환할까?

Status: CLOSED

Decision / approved direction: 운영 준비와 acceptance criteria 충족 후 웹으로 일괄 전환한다. 장기간 동일 업무를 두 시스템에 병행 입력하는 구조를 만들지 않는다.

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: OPS-001; 짧은 준비/검증 기간만 cutover 계획에서 별도 정의. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): K13/K19; 10 전환. [분석 색인](../analysis/README.md)

<a id="pd-019"></a>
## PD-019

Question: 계정 발급·초기 관리자·암호 재설정·접근 종료 정책은?

Status: CLOSED

Decision / approved direction: 계정은 관리자 발급 방식을 유지하고 Master Admin이 Branch Admin 및 계정/권한을 관리한다. v1 Trainer 로그인 계정도 포함한다. 기존 계정/암호는 이관하지 않는다. Branch Admin의 계정 업무 위임 범위는 미정이다.

Approval source: 2026-09-17 사용자 Multi-Branch 제품 방향 변경 지시. 충돌하는 이전 결정은 본 결정으로 대체하며 기존 비충돌 규칙은 유지한다.

Follow-up: ARCH-001/002, MB-004; 초기 Master Admin·재설정·중단·마지막 Master Admin 보호 및 접근 종료 상세를 후속 설계한다. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): F01/F57–F59; K08/K29. [분석 색인](../analysis/README.md)

<a id="pd-020"></a>
## PD-020

Question: 파일 가져오기와 외부 업무 연동을 무엇까지 지원할까?

Status: CLOSED

Decision / approved direction: Migration용 파일 import를 v1 필수 기능으로 두지 않는다. 미확인 결제·SMS·카카오톡·이메일·장치 연동은 추가하지 않는다. CSV/Excel import/export도 실제 필요 확인 전 필수 요구가 아니다.

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: 승인된 v1 연동 없음; 새 필요는 별도 Product Requirement. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): 09 외부 연동; H03. [분석 색인](../analysis/README.md)

<a id="pd-021"></a>
## PD-021

Question: 성능·가용성·복구와 운영 책임의 수용 기준은 무엇인가?

Status: OPEN

Decision / approved direction: Organization의 여러 Branch와 Trainer 직접 로그인·다중 기기 이용 규모를 기준으로 동시 사용자·자료 증가·응답시간·백업·복구 요구와 운영 책임을 Architecture/NFR 단계에서 결정한다. 임의의 정량 목표나 대규모 트래픽 전제를 두지 않는다.

Approval source: 2026-09-15 승인 및 2026-09-17 Multi-Branch 변경 지시. 후속 결정 단계와 대상 범위만 지정됨; 정량 수용 기준은 미승인.

Follow-up: ARCH-004; 정량 목표와 수용 기준은 OPEN. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): K18/K36; NEW-CANDIDATE. [분석 색인](../analysis/README.md)

<a id="pd-022"></a>
## PD-022

Question: 개인정보 항목·열람 범위·보존 기간·감사기록 범위는?

Status: CLOSED

Decision / approved direction: 최소 개인정보와 Role·Data Scope 보호를 유지한다. Session 생성·정정/취소, Pass 잔여 변경, 계정/권한, 중요 Branch 관리 및 추가실적 생성·정정·취소는 감사 대상이다. 모든 보상 설정 변경(최초 설정 포함)에 대상 Trainer, 변경 항목, 변경 전 값, 변경 후 값, 변경 Actor, Actor의 권한 및 Branch Context, 변경 시점을 추적한다. 별도 Master Admin 승인 없이 변경 가능하며 변경 요청→승인 대기→승인→반영 절차를 추가하지 않는다. 이 결정은 추가실적 승인이나 월 정산 마감/확정 절차를 면제하지 않는다. 감사 및 다른 화면으로 비인가 사용자에게 보상 설정을 우회 노출하지 않는다.

Approval source: 2026-09-17 최신 사용자 지점 관계·추가실적·월 기본급·보상 설정 권한 확정. 충돌하는 이전 방향은 대체하며 비충돌 결정을 유지한다.

Follow-up: ARCH-001, BR-007, LEGAL-001; Audit Log schema·열람·보존 기간은 후속. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): F02/F07; 08 인증; K06/K07. [분석 색인](../analysis/README.md)

<a id="pd-023"></a>
## PD-023

Question: 숨김 기능·빈 화면·데스크톱 조작의 웹 제외 후보를 승인할까?

Status: CLOSED

Decision / approved direction: 숨김 기능·빈 화면·미연결 기능은 DROP-CANDIDATE를 유지한다. 존재 자체로 구현하지 않고 실제 업무 필요가 확인되면 요구사항으로 승격한다.

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: 영구 폐기 확정 아님; v1 필수 구현 아님. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): H01/H02/H04; S05/S15; F34/F36. [분석 색인](../analysis/README.md)

<a id="pd-024"></a>
## PD-024

Question: 계약·예약·출석·결제·환불·회원권·상담을 새로 추가할까?

Status: CLOSED

Decision / approved direction: 계약·출석·고객 결제·환불·회원권·상담을 v1에 추가하지 않는다. Reservation/Schedule도 v1 제외이지만 PD-025의 명시적 Future Scope다. PT Pass 도입 자체로 이 도메인을 v1에 추가하지 않는다.

Approval source: 2026-09-17 사용자 Multi-Branch 제품 방향 변경 지시. 충돌하는 이전 결정은 본 결정으로 대체하며 기존 비충돌 규칙은 유지한다.

Follow-up: Schedule/Reservation은 PD-025; 나머지는 후속 필요 확인 시 별도 범위 승인. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): 02 도메인; 12 용어집. [분석 색인](../analysis/README.md)

<a id="pd-025"></a>
## PD-025

Question: Schedule/Reservation은 어느 단계의 범위인가?

Status: CLOSED

Decision / approved direction: PT Schedule, Reservation, Reservation Cancellation, Member Schedule 및 Trainer Schedule 확장은 Member Self-Service와 함께 고려하는 명시적 Future Scope다. v1에는 구현하지 않는다. 향후 추가를 불필요하게 어렵게 만드는 구조적 제약을 피하도록 Handoff에 기록한다.

Approval source: 2026-09-17 사용자 제품 방향 변경 지시.

Follow-up: Product Expansion에서 상세 정책 결정. 현재 예약 Domain 설계 없음.

Related requirements: [Scope](scope.md), [Architecture Handoff](architecture-handoff.md)

<a id="pd-026"></a>
## PD-026

Question: Mobile App과 다른 Client 확장을 어떻게 고려하는가?

Status: CLOSED

Decision / approved direction: Trainer·Member 대상 Mobile App은 명시적 Future Direction이다. 현재 App이나 Framework를 선택·구현하지 않는다. Web UI에 Business Logic을 강하게 결합해 다른 Client에서 동일 업무 기능을 이용할 수 없게 만드는 구조를 피해야 한다.

Approval source: 2026-09-17 사용자 제품 방향 변경 지시.

Follow-up: API Architecture는 Architecture 단계, Mobile 기술은 후속 도입 단계에서 결정한다.

Related requirements: [NFR](non-functional-requirements.md#nfr-013), [Architecture Handoff](architecture-handoff.md)

## Product Baseline — 2026-09-17 지점 관계·보상 개정

최신 사용자 확정사항을 반영한 Architecture Input Baseline이다. [현재 결정과 변경 이력](README.md), [권한](users-and-roles.md), [업무 규칙](business-rules.md), [남은 결정 게이트](open-questions.md), [Architecture 인계](architecture-handoff.md)를 함께 따른다. Baseline 갱신은 모든 상세 업무 정책 또는 구현 완료를 뜻하지 않는다.

<a id="pd-027"></a>
## PD-027

Question: 추가실적을 v1에서 어떤 업무로 지원하는가?

Status: CLOSED

Decision / approved direction: Additional Performance는 Trainer에게 인정하는 인센티브이며 v1에 포함한다. 타 지점 지원 수업·회원 유지·기타 인정 실적이 예다. 특정 Session 관련 또는 Session 없는 실적을 지원하고 생성·정정·취소를 감사 가능하게 한다. 고객 결제·매출·가계부 또는 기존 수동 매출과 동일시하지 않는다. 타 지점 수업 보상은 추가실적으로 정산할 수 있어야 하지만 일반 Session Payment에 더하는지 전체를 대신하는지는 OPEN이다.

Approval source: 2026-09-17 최신 사용자 확정.

Follow-up: BR-013 등록/신청/승인·금액·정정/취소, MB-009 타 지점 보상 구성, MB-010 귀속. 보상 설정 권한을 추가실적 권한에 자동 적용하지 않는다.

Related requirements: [PR-031](requirements.md#pr-031), PR-010/027; BR-PAY-015.
