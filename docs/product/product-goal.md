# Product Goal

상태: 사용자 Multi-Branch 변경 승인 반영(2026-09-17). 세부 정책은 [후속 질문](open-questions.md)에 남긴다.

## 목적과 경계

하나의 헬스장 브랜드/운영 조직인 Organization 아래 여러 실제 지점 Branch를 관리하는 Multi-Branch PT 관리 시스템을 만든다. Master Admin·Branch Admin·Operator·Trainer가 v1 로그인 Actor다. Desktop/Tablet/Smartphone Responsive Web을 제공하며 Trainer는 현장에서 Smartphone으로 실제 Session을 등록한다. Member는 v1 관리 대상이자 Future Self-Service Actor다. Multi-Tenant SaaS 제품을 확정한 것은 아니다. 이는 코드에서 발견한 사실이 아니라 승인된 TO-BE Product Decision이다(PD-001–006).

기존 C# 프로그램은 업무 발견을 위한 AS-IS reference다. 기존 DB schema, 화면 구조, 결함, 계산식의 불명확성을 호환성 요구사항으로 보존하지 않는다. 운영 데이터·계정·암호를 이관하지 않고 빈 운영 데이터에서 Master Admin과 기준정보를 새로 설정한다. 준비 및 acceptance criteria 충족 후 일괄 전환하며 장기 병행 입력은 하지 않는다(PD-017–019).

## 해결하려는 업무 문제와 가치

| AS-IS 근거 | 승인된 제품 방향 | 사용자 가치 |
| --- | --- | --- |
| 회원 현재 PT 종류·담당·잔여 중심(F04) | 회원별 여러 PT Pass 이력, 종료 이력 보존(PD-007/011) | 이용 단위별 현재 상태와 과거 이용을 구분 |
| 월 진행 입력·잔여 처리와 정정의 불일치 위험(F17–21, K02/K05) | 실제 날짜별 개별 Session 및 Pass 잔여·정산 일관성(PD-008/010) | 실제 진행일과 횟수 변화를 확인 |
| 공통/개별 지급률과 불명확한 금액 계산(F11–16, K04/K24/K25) | Organization 공통 Product의 Payment Type과 Trainer별 보상 설정을 분리하고 권한 있는 관리자가 관리(PD-009) | 지급 정책과 계산 근거를 설명 |
| 월/연 집계와 12개월 평균(F26/27) | 권한에 맞게 제공하는 기본급·Session Payment·추가실적을 구분하는 월 정산 정보(PD-012) | 진행 실적과 지급액을 구분하여 검토 |
| 메뉴·특수 계정 중심 권한과 감사 부족 | 직무별 접근 제한과 중요 행위 감사(PD-001/022) | 책임 있는 운영과 변경 확인 |

근거: [기능 목록](../analysis/03-feature-inventory.md), [도메인](../analysis/02-domain-model.md), [업무 흐름](../analysis/06-business-flows.md), [위험](../analysis/11-risks-and-unknowns.md). 위 가치는 제품 목표이며 생산성 향상 수치나 운영 성과를 측정한 결과가 아니다.

## 반드시 유지할 업무 능력과 승인된 개선

회원·트레이너·PT 상품을 관리하고, 이용정보를 확인하며, PT 진행을 기록하고, 잔여 횟수를 반영하고, 오류를 정정하고, 트레이너 월 지급액을 확인하는 업무 능력을 유지한다. 이용정보는 명시적 PT Pass로, 진행 원본은 날짜별 PT Session으로 개선한다. Product는 RATE/FIXED_AMOUNT 방식을 정하고 Trainer Compensation Setting은 Rate·Fixed Amount·월 고정 Base Salary를 제공한다. 추가실적도 v1에 포함한다. 종료·비활성화 이후에도 과거 Session과 정산 이력을 조회한다.

PT Pass는 회원, PT Product, 담당 트레이너, 구매 횟수, 잔여 횟수, 상태, 생성/시작 정보, PT Session 이력을 연결하는 제품 개념이다. 회원은 시간에 따라 여러 Pass 이력을 가질 수 있다. 복수 사용 가능한 Pass의 FIXED_AMOUNT 우선 차감과 동일 Payment Type FIFO는 확정이며 상태·사용 가능 조건·상한은 후속이다. 이는 DB 설계가 아니다.

## 웹 환경에서 기대하는 가치

Desktop/Tablet/Smartphone에서 사용자별 주요 정보와 Action을 실질적으로 사용할 수 있도록 터치 및 작은 화면을 고려한다. Trainer의 Smartphone Session 등록을 주요 수용 기준으로 삼는다. Role과 Data Scope를 분리하고 Branch 접근 제한을 Backend에서 강제하여 지점 운영 경계를 보호한다. 향후 다른 Client가 동일 업무를 사용할 수 있도록 Business Logic의 Web UI 종속을 피해야 한다. 외부 연동은 별도 승인 없이 추가하지 않는다. [웹 전환 참고](../analysis/10-web-migration-considerations.md), PD-004/005/020.

## 범위와 남은 질문

[확정 v1 범위](scope.md)는 핵심 PT 운영에 집중한다. 가계부·락커·수동 매출·고정 거래·신규 계약/출석/고객 결제/환불/회원권/상담은 v1 제외를 유지한다. Member 로그인/Self-Service, Schedule/Reservation/Cancellation, Member/Trainer Schedule 확장과 Mobile App은 명시적 Future Scope이며 v1에는 구현하지 않는다. 기존 자료 조회·이관 및 migration tooling도 제외한다.

지급 방식/값의 분리, 계산식, 서비스 지급, FIXED_AMOUNT 우선 차감, 과거 확정 지급 결과 보존 및 대상 Home Branch 기준 보상 설정 권한은 [BR-PAY-001–013](business-rules.md)으로 확정했다. RATE 1,000원 단위 올림, 저장 완료 이후 신규 Session부터 Rate/Fixed Amount 적용, 정상 등록 시 지급액 확정, Operator·Trainer의 설정 조회 금지는 확정이다. 정정·입력값 검증·Product 변경 적용 및 Pass 상태·횟수 상세는 후속 질문이다. PD-021 및 법적 보존 기간은 OPEN이다.

## Product Baseline — 2026-09-17 지점 관계·보상 개정

최신 사용자 확정사항을 반영한 Architecture Input Baseline이다. [현재 결정과 변경 이력](README.md), [권한](users-and-roles.md), [업무 규칙](business-rules.md), [남은 결정 게이트](open-questions.md), [Architecture 인계](architecture-handoff.md)를 함께 따른다. Baseline 갱신은 모든 상세 업무 정책 또는 구현 완료를 뜻하지 않는다.

## 확정 관계와 보상 경계

Trainer는 한 시점에 Home Branch 하나에 소속되고 Branch에는 여러 Trainer가 있을 수 있다. Branch당 Trainer 한 명인 1:1이나 Trainer 동시 복수 소속 N:M을 요구하지 않는다. Member도 Home Branch 하나를 가지며 Pass는 Issued Branch 하나를 가진다. Trainer·Member·Pass는 허용된 조건에서 타 지점 PT 업무를 수행·이용할 수 있다. Session은 실제 Performed Branch를 식별하고 소속·발급 지점 변경으로 과거 수행 지점이 바뀌지 않아야 한다. Product는 Organization 공통 Catalog이며 지점별 가격 정책은 추가하지 않는다. Branch Admin은 하나의 Branch를 관리하고 일부 여러 지점만 담당하는 중간 관리자 역할은 추가하지 않는다.

Monthly Settlement = 해당 월 적용 Base Salary + 유효한 Session Payment 합계 + 유효한 Additional Performance 합계다. Trainer·대상 월·적용 기본급·Session 수·Session Payment 합계·추가실적 내역/합계·월 정산 합계를 구분한다. 2,500,000원 + 1,200,000원 + 150,000원 = 3,850,000원이며 여러 지점 수업으로 동일 월 기본급을 중복 가산하지 않는다. 타 지점 Session Payment 포함 여부는 MB-009 결정 전 확정하지 않는다.

타 지점 지급 구성 MB-009, 추가실적 권한/금액 BR-013, 기본급 적용 월 BR-012, 지점 귀속 MB-010과 정산 공개 MB-006은 남은 업무 결정이다. 실제 운영에서 기존 C# 프로그램을 대체하며 기존 구현은 AS-IS 참고다.
