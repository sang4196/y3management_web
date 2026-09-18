# 핵심 사용자 시나리오

승인된 TO-BE 업무 시나리오다. AS-IS에서 유래한 업무와 새 승인 방향을 근거에 구분한다. 세부 정책의 미정 부분은 실행 규칙으로 확정하지 않는다. 모든 흐름에 Role과 Data Scope를 적용하며 Master Admin은 Organization 전체, Branch Admin은 허용 Branch, Operator는 허용 Branch·업무, Trainer는 Allowed PT Scope에 한정한다. Branch 관계 정책은 MB-001–008을 따른다. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

<a id="sc-001"></a>
## SC-001. 운영 계정으로 담당 업무 시작

Scenario: 운영 계정으로 담당 업무 시작

Actor: Master Admin / Branch Admin / Operator / Trainer

Goal: 허용된 핵심 PT 업무에 접근

Preconditions: 신규 운영 계정 발급 및 해당 권한 설정

Main Flow: 계정으로 접근 → 권한 범위 업무 확인 → 회원/Pass/Session 등 담당 업무 수행

Alternative Flow: 인증 실패·비활성 계정·권한 없는 업무의 상세 처리는 ARCH-001/002에서 정의

Business Rules: 관리자 발급 계정, Trainer v1 로그인, Member 로그인은 Future Scope. Role과 Data Scope 분리 및 Backend Branch 접근 제한

Result: 허용된 업무에만 접근

Related AS-IS Evidence: F01/F57–59; AS-IS 인증; APPROVED-TO-BE PD-001–004/019/022. [기능](../analysis/03-feature-inventory.md), [흐름](../analysis/06-business-flows.md).

Open Questions: ARCH-001/002

<a id="sc-002"></a>
## SC-002. 회원에게 PT Pass 생성하고 이용정보 확인

Scenario: 회원에게 PT Pass 생성하고 이용정보 확인

Actor: Master Admin 또는 허용 Branch의 Branch Admin / 권한 있는 Operator

Goal: 회원의 이용 단위와 이력을 관리

Preconditions: 회원·트레이너·상품 등록 및 해당 업무의 Branch Scope 허용. 확정 관계는 BR-OPS-001을 따르며 교차 이용 상세 조건은 MB-001/002/003/005 결정 필요

Main Flow: 회원 검색 또는 신규 등록 → 상품/담당 트레이너와 구매 횟수·생성/시작 정보 확인 → Pass 생성 → 잔여·상태·이력 확인

Alternative Flow: 이전 종료 Pass는 보존한다. 복수 사용 가능 Pass에서 FIXED_AMOUNT 우선 사용은 확정이며 추가 횟수·중단·재개 등만 후속이다.

Business Rules: 회원 현재 PT 필드 덮어쓰기 모델을 복제하지 않음; 구매와 잔여 정책 별도

Result: 회원에게 연결된 명시적인 Pass와 조회 가능한 이용 이력

Related AS-IS Evidence: F02–06; B02; APPROVED-TO-BE PD-007/011. [기능](../analysis/03-feature-inventory.md), [흐름](../analysis/06-business-flows.md).

Open Questions: BR-001/002, ARCH-003, LEGAL-001

<a id="sc-003"></a>
## SC-003. Smartphone에서 Trainer의 PT 진행 등록(수업 완료 기록)

Scenario: Trainer의 현장 Smartphone 주요 업무; Desktop/Tablet에서도 수행 가능

Actor: 직접 로그인한 Trainer; 허용된 운영자 등록도 유지

Goal: 진행 사실을 남기고 Pass 잔여에 반영

의미: 기존 회원에게 실제 수행한 수업을 기록한다. 상품/Pass 생성이나 미래 예약·시간표 생성이 아니며 사전 Reservation은 필수가 아니다. 진행일과 시스템 기록 시점은 구별한다. 아래 지급 계산은 서버 내부 처리이고 Trainer에게 보상 설정을 표시하는 단계가 아니다.

Preconditions: Trainer 로그인 및 Allowed PT Scope 확인, 실제 Branch·Member·사용 가능한 Pass 확인. 미정 교차 Branch 정책은 MB-001/002/003/005 결정 후 적용

Main Flow: Smartphone 로그인 → 허용 Member/PT 정보 조회 → 실제 진행 Branch·날짜 확인 → 자신이 실제 수행한 Session 등록 → 사용할 Pass 결정(FIXED_AMOUNT 우선, 동일 Payment Type FIFO) → Pass 횟수 차감 → Product Payment Type 확인 → 권한 있는 관리자 저장 완료 이후 신규 Session에 적용되는 수행 Trainer Rate/Fixed Amount 적용 → Session Payment 계산·확정(RATE 1,000원 단위 올림; FIXED_AMOUNT 그대로) → 자신의 Session·잔여 반영 결과 확인 → 유효 Session Payment의 월 집계 대상 확인(지점 귀속은 MB-010 결정 필요)

Alternative Flow: 잔여 부족·종료 Pass·소급 날짜·같은 날 여러 회의 처리는 규칙 확정 필요. 여러 날짜 일괄 UI는 선택 미정

Business Rules: BR-PAY-001–013. Session 등록 권한과 보상 설정 접근 권한은 별개이며 BR-PAY-010을 따른다. 이 일반 Session 흐름으로 타 지점 지급 구성을 확정하지 않으며 MB-009 결정 전 해당 보상 상세는 보류한다. 작은 화면에서 주요 정보와 터치 Action을 실질적으로 지원해야 한다. FIXED_AMOUNT 2회 + RATE 10회에서 3회 진행하면 FIXED → FIXED → RATE. 실제 날짜별 1회 원본이며 지급/잔여 일관성과 감사 유지.

Result: 실제 진행 Branch·날짜·수행 Trainer가 식별되는 Session, 일치하는 잔여·확정 Payment·월 집계. 지급 설정은 Trainer에게 비노출

Related AS-IS Evidence: F17–19; B02; APPROVED-TO-BE PD-008/009/012/022. [기능](../analysis/03-feature-inventory.md), [흐름](../analysis/06-business-flows.md).

Open Questions: BR-002/008/010/011, MB-001/002/003/005/009/010, UX-001

<a id="sc-004"></a>
## SC-004. 잘못된 Session 정정 또는 취소

Scenario: 잘못된 Session 정정 또는 취소

Actor: 제한된 정정 권한과 해당 Branch Scope를 부여받은 운영자. Trainer 본인 정정/취소 허용 여부는 MB-005 OPEN

Goal: 오류를 바로잡으면서 업무 이력을 보존

Preconditions: 대상 Session 확인 및 정정 권한 보유

Main Flow: 대상 기록/영향 확인 → 허용된 정정 또는 취소 수행 → Pass 잔여와 정산 반영 결과 확인 → 감사 가능한 변경 이력 확인

Alternative Flow: 권한 없는 처리는 허용하지 않음. 이미 검토한 정산·종료 Pass·비활성 회원 관련 기대 결과는 BR-007

Business Rules: 단순 row 삭제 금지; Pass 잔여·정산 일관성 및 이력 유지

Result: 정정 결과와 영향이 일치하고 과거 변경을 확인 가능

Related AS-IS Evidence: F20/21; B03; APPROVED-TO-BE PD-010/011/022. [기능](../analysis/03-feature-inventory.md), [흐름](../analysis/06-business-flows.md).

Open Questions: BR-007, ARCH-001; 정산 마감/확정 절차는 미승인

<a id="sc-005"></a>
## SC-005. 월별 트레이너 지급액 검토

Scenario: 월별 트레이너 지급액 검토

Actor: Master Admin / 허용 Branch의 Branch Admin / 정산 조회 권한을 가진 Operator

Goal: 진행 실적과 지급액의 계산 근거 확인

Preconditions: 대상 Trainer·월의 적용 기본급, 유효 Session Payment 및 추가실적 확인. 적용 월·지점 귀속·공개·타 지점 지급 구성은 해당 OPEN 결정 필요.

Main Flow: 허용 정산 범위/Trainer/월 선택 → 적용 기본급 + 유효 Session Payment 합계 + 유효 추가실적 합계 구분 → 월 합계와 상세 검토. Branch Admin 공개 범위 MB-006과 지점 귀속 MB-010은 결정 전 확정하지 않는다.

Alternative Flow: 현재 설정이 바뀌어도 과거 확정 Session Payment를 유지한다. 권한 있는 오류 정정/취소의 반영은 BR-007 후속이다. RATE는 정상 등록 시 Session별 1,000원 단위 올림하여 확정했으므로 월 합계에 다시 올림하지 않는다.

Business Rules: Monthly Settlement = 해당 월 적용 Base Salary + 유효한 Session Payment 합계 + 유효한 Additional Performance 합계다. Trainer·대상 월·적용 기본급·Session 수·Session Payment 합계·추가실적 내역/합계·월 정산 합계를 구분한다. 2,500,000원 + 1,200,000원 + 150,000원 = 3,850,000원이며 여러 지점 수업으로 동일 월 기본급을 중복 가산하지 않는다. 타 지점 Session Payment 포함 여부는 MB-009 결정 전 확정하지 않는다. 보상 설정 노출은 BR-PAY-010을 따른다. 현재 기본급 변경으로 과거 확정 정산을 자동 변경하지 않는다. 12개월 고정 평균은 요구하지 않는다.

Result: 세 구성 요소를 설명 가능한 월 정산. 예시 합계 3,850,000원, 여러 지점 수업에도 기본급 중복 없음.

Related AS-IS Evidence: F26/27; APPROVED-TO-BE PD-009/012. [기능](../analysis/03-feature-inventory.md), [흐름](../analysis/06-business-flows.md).

Open Questions: BR-007/008/009/010/011/012/013, MB-006/009/010. 지급 이체/고객 결제 시나리오가 아니다.

<a id="sc-010"></a>
## SC-010. 빈 운영 데이터에서 준비하고 일괄 전환

Scenario: 빈 운영 데이터에서 준비하고 일괄 전환

Actor: Master Admin 및 운영 전환 책임자(책임 배정 TBD)

Goal: 신규 웹 시스템으로 실제 운영 시작

Preconditions: 운영 준비 및 acceptance criteria 확인; 구체 준비 계획 OPS-001

Main Flow: 초기 Master Admin·Organization/Branch 준비 → 운영 및 Trainer 계정/기준정보·지급 정책 설정 → 필요한 회원/트레이너/Pass 새로 생성 → 준비 및 수용 기준 확인 → 일괄 전환

Alternative Flow: 짧은 준비/검증 기간은 별도 계획. 준비 미충족 상태에서 운영 전환을 완료로 보지 않음

Business Rules: 기존 데이터·계정·암호 이관 및 장기 이중 입력 없음. 최초 보상 설정도 Master Admin 또는 대상 Home Branch의 Branch Admin만 수행하며 감사 대상이다. 전환 책임자라는 이유로 권한이 생기지 않는다.

Result: 새로 생성한 데이터로 운영 시작

Related AS-IS Evidence: APPROVED-TO-BE PD-017/018/019; 기존 설정 F55는 AS-IS 센터 정보 변경의 참고. [기능](../analysis/03-feature-inventory.md), [흐름](../analysis/06-business-flows.md).

Open Questions: ARCH-002, OPS-001, PD-021; 전환 책임자는 새 로그인 Role 확정이 아님

<a id="sc-011"></a>
## SC-011. 비활성화 이후 과거 이력 확인

Scenario: 비활성화 이후 과거 이력 확인

Actor: 해당 변경/조회 권한을 가진 운영자

Goal: 업무 대상 사용을 중단하되 과거 진행과 정산 보존

Preconditions: 회원·트레이너·Pass 및 연결 이력 존재

Main Flow: 대상 확인 → 허용된 비활성화/상태 변경 → 과거 Session과 정산 이력 조회

Alternative Flow: 남은 횟수·진행 중 Pass의 종료 조건은 BR-001/002. 법적 필요 삭제는 LEGAL-001 별도

Business Rules: Hard Delete가 기본 운영 기능이 아님; 과거 이력 조회 가능

Result: 비활성 업무 대상과 과거 결과를 구분하여 확인

Related AS-IS Evidence: F06/F10; APPROVED-TO-BE PD-011. [기능](../analysis/03-feature-inventory.md), [흐름](../analysis/06-business-flows.md).

Open Questions: BR-001/002/007, LEGAL-001

<a id="sc-012"></a>
## SC-012. 트레이너 지급 정책 설정·변경

Scenario: 트레이너 지급 정책 설정·변경

Actor: Master Admin 또는 대상 Trainer Home Branch의 Branch Admin

Goal: 트레이너별 적절한 지급 기준 관리

Preconditions: 대상 Trainer 등록과 보상 설정 권한 확인. 수원점 소속 Trainer의 세 항목은 수원점 Branch Admin이 접근 가능하며 강남점 지원 수업 이력은 강남점 Admin의 권한을 만들지 않는다.

Main Flow: Backend에서 Actor 권한·대상 Home Branch 확인 → Rate/Fixed Amount/Base Salary 조회·설정/변경 → 별도 Master 승인 없이 저장 → 대상·항목·전후 값·Actor·권한/Branch Context·시점 감사 → Rate/Fixed Amount는 이후 신규 등록 Session에 적용 → 과거 확정 지급·정산 불변 확인

Alternative Flow: 타 지점 Branch Admin·Operator·Trainer(본인 포함)는 직접 ID 요청과 감사 등 다른 경로로도 설정에 접근 불가. Base Salary 변경의 적용 월/미확정 정산 반영은 BR-012 결정 후 상세화한다.

Business Rules: BR-PAY-009/010/011/014. 별도 승인 없음은 보상 설정 변경에만 적용한다. 추가실적 승인과 월 마감/확정 절차는 OPEN이다.

Result: 트레이너별 설명 가능한 정책과 과거 계산 기준

Related AS-IS Evidence: F14–16은 개별 지급률 참고; APPROVED-TO-BE PD-009/022. [기능](../analysis/03-feature-inventory.md), [흐름](../analysis/06-business-flows.md).

Open Questions: BR-010/012, ARCH-001. 설정 권한 자체는 확정이며 기본급 적용 월·입력·구현 상세만 후속.

<a id="sc-006"></a>
## SC-006. 수동 트레이너 매출 — v1 제외

기존 초안의 시나리오 ID를 추적용으로 보존한다. PD-013 승인에 따라 v1 업무 흐름/수용 기준에서 제외하며 실행 절차를 정의하지 않는다. [AS-IS mapping](as-is-to-be-mapping.md).

<a id="sc-007"></a>
## SC-007. 락커 — v1 제외

기존 초안의 시나리오 ID를 추적용으로 보존한다. PD-016 승인에 따라 v1 업무 흐름/수용 기준에서 제외하며 실행 절차를 정의하지 않는다. [AS-IS mapping](as-is-to-be-mapping.md).

<a id="sc-008"></a>
## SC-008. 가계부 — v1 제외

기존 초안의 시나리오 ID를 추적용으로 보존한다. PD-014 승인에 따라 v1 업무 흐름/수용 기준에서 제외하며 실행 절차를 정의하지 않는다. [AS-IS mapping](as-is-to-be-mapping.md).

<a id="sc-009"></a>
## SC-009. 고정 거래 — v1 제외

기존 초안의 시나리오 ID를 추적용으로 보존한다. PD-015 승인에 따라 v1 업무 흐름/수용 기준에서 제외하며 실행 절차를 정의하지 않는다. [AS-IS mapping](as-is-to-be-mapping.md).

<a id="sc-013"></a>
## SC-013. Master Admin의 Branch 관리

Actor: Master Admin

Goal: Organization의 여러 운영 지점을 조회·등록·관리

Main Flow: Organization의 Branch 목록 조회 → Branch 등록 또는 정보 관리 → 허용 Branch 업무 데이터 조회 → Branch별 Session/Settlement 확인

Business Rules: Branch 구조 관리 주체는 Master Admin. Branch Admin은 Organization 구조 및 다른 Branch 생성/수정 불가. 활성/비활성 가능성을 고려하되 상태·처리 규칙은 MB-008 결정 전 확정하지 않음. 중요 관리 행위의 Actor·Role·Branch Context 감사.

Open Questions: MB-004/007/008. [PR-020](requirements.md#pr-020), PD-004/022.

<a id="sc-014"></a>
## SC-014. Branch 간 무단 접근 차단

Actor: Branch A만 허용된 Branch Admin

Goal: 자신의 Branch 업무를 수행하면서 다른 Branch의 정보 보호

Main Flow: Branch A Member/Trainer/Pass/Session/운영 데이터/Settlement의 허용 업무 수행 → Branch A 범위 결과만 확인

Alternative Flow: 허용되지 않은 Branch B Member 등의 ID로 조회·수정 시도하면 Backend에서 금지. 목록·검색·집계·정산에서도 허용하지 않은 Branch 자료를 제공하지 않음. 메뉴를 숨기는 것만으로 통과하지 않음.

Business Rules: 단일 Branch Admin Scope를 Backend에서 강제한다. 자기 Branch 소속 Trainer 보상 설정은 허용되나 타 지점 Trainer의 지원 수업만으로는 접근 불가다. 특정 교차 업무 허용 조건과 타 지점 전체 목록 조회는 구별한다. 정산 공개는 MB-006 OPEN이다.

Result: 허용 Branch 범위의 운영 결과와 타 Branch 접근 차단

Related requirements: [PR-030](requirements.md#pr-030), NFR-001; PD-001/004.

Open Questions: MB-002/003/004/005/006. Branch Admin 단일 Branch 관리는 확정이다.

<a id="sc-015"></a>
## SC-015. Member Self-Service / Mobile App — Future Scope

Member는 향후 로그인하여 자신의 Schedule·예약 Session·Pass·잔여 조회와 예약·취소를 사용할 계획이다. Trainer/Member Mobile App도 향후 방향이다. v1 실행 시나리오나 예약 Domain 요구로 승격하지 않는다. Member와 Login Account의 연결, Schedule 정책과 App 기술은 후속 Architecture/Product Expansion에서 결정한다. PD-003/025/026; NFR-013.

## Product Baseline — 2026-09-17 지점 관계·보상 개정

최신 사용자 확정사항을 반영한 Architecture Input Baseline이다. [현재 결정과 변경 이력](README.md), [권한](users-and-roles.md), [업무 규칙](business-rules.md), [남은 결정 게이트](open-questions.md), [Architecture 인계](architecture-handoff.md)를 함께 따른다. Baseline 갱신은 모든 상세 업무 정책 또는 구현 완료를 뜻하지 않는다.

<a id="sc-016"></a>
## SC-016. 타 지점 수업과 추가실적

Actor: 허용된 PT 업무 범위의 Trainer; 추가실적 처리 Actor는 BR-013 OPEN

Goal: 실제 수업·Pass 사용 이력과 인센티브를 구분

Main Flow: 수원점 소속 Trainer가 허용된 강남점 수업 수행 → Member Home Branch와 Pass Issued Branch가 달라도 허용 조건 확인 → 실제 Performed Branch/날짜 기록 및 Pass 차감. Home Branch 변경이나 추가 소속을 만들지 않는다.

Business Rules: 추가실적은 관련 Session이 있거나 회원 유지처럼 없을 수도 있다. 필요한 업무 정보와 변경 감사는 PR-031을 따른다. 등록/승인 절차는 BR-013 결정 전 실행 흐름으로 확정하지 않는다.

Result: 기록·횟수 일관성을 유지하고 보상 구성 A/B는 MB-009 결정 게이트로 식별한다. 일반 수당 0원 또는 일반 수당+추가실적의 미정 예상 금액을 작성하지 않는다.

Open Questions: MB-001/002/003/005의 교차 허용 조건, BR-013 추가실적 처리, MB-009 지급 구성, MB-010 정산 귀속.
