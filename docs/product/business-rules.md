# Trainer Payment Business Rules

상태: APPROVED-TO-BE / 사용자 확정(2026-09-16 및 2026-09-17). 2026-09-17 Multi-Branch 변경 지시가 이전 결정과 충돌하면 우선하며 BR-PAY-001–013의 지급 계산·차감·확정 규칙은 유지한다. 보상 설정 권한은 BR-PAY-010으로 갱신한다. 이하 일반 Session 지급 규칙과 수치 사례로 타 지점 수업 보상 구성(MB-009)을 결정하지 않는다. AS-IS 구현 사실이나 DB Column/Table 정의가 아니다. [결정](product-decisions.md), [요구사항](requirements.md), [남은 질문](open-questions.md).

## 용어

| 용어 | 제품 의미 |
| --- | --- |
| Organization | 하나의 헬스장 브랜드/운영 조직 |
| Branch | Organization 아래 실제 운영 지점. 단일 Home/Issued Branch와 실제 Performed Branch를 구분; 정산 귀속은 MB-010 |
| PT Product | PT 상품 자체, 총 횟수, 판매가격, Payment Type; Organization 공통 Catalog; Branch Admin 관리 권한은 MB-007 |
| Trainer Compensation Setting | Trainer 기준 Rate·Fixed Amount·월 Base Salary |
| PT Pass | Member가 특정 Product를 이용하는 단위 |
| PT Session | 기존 회원에게 실제 수행한 PT 수업 1회의 완료 기록과 실제 Branch Context. 예약·시간표 생성 또는 상품 등록·Pass 발급이 아님 |
| Session Payment | 해당 Session에 대해 계산된 수행 Trainer의 지급 결과 |
| Monthly Settlement | 적용 기본급 + 유효 Session Payment 합계 + 유효 추가실적 합계 |

<a id="br-pay-001"></a>
## BR-PAY-001 — Product의 지급 방식

Status: APPROVED

각 PT Product는 총 횟수(Product Session Count), 판매가격(Product Price), Payment Type으로 설명한다. Payment Type은 RATE 또는 FIXED_AMOUNT다. 지급 계산에 관한 Product 설정은 방식이며 Trainer 지급률·고정 지급금액은 Product 값이 아니다. Master Admin이 주요 기준정보로 관리한다.

Traceability: 2026-09-16 사용자 확정; PR-006; PD-009. [요구사항](requirements.md).

<a id="br-pay-002"></a>
## BR-PAY-002 — Trainer Compensation Setting

Status: APPROVED

Trainer 기준 Rate, Fixed Amount, Base Salary를 제품·권한 개념으로 묶는다. Rate는 RATE 상품 지급률, Fixed Amount는 FIXED_AMOUNT 상품 회당 지급액, Base Salary는 월 고정 기본급이다. Product는 방식만 정하며 Product별 Trainer Rate/Fixed Amount는 두지 않는다. 세 항목을 같은 테이블에 저장하라는 뜻이 아니다. 예: A Rate 50%/Fixed Amount 20,000원, B 40%/15,000원은 예시이며 기본값이 아니다. Base Salary는 BR-PAY-014, 접근 권한은 BR-PAY-010이다.

Traceability: PD-009/012; PR-007.

<a id="br-pay-003"></a>
## BR-PAY-003 — RATE 계산

Status: APPROVED

소비한 Pass의 Product Payment Type이 RATE이면 기초 계산액 = Product Price ÷ Product Session Count × Session을 수행한 Trainer의 적용 Rate이며, Session Payment는 기초 계산액을 1,000원 단위로 올림한 금액이다(BR-PAY-013). Product A의 1,000,000원 ÷ 20회 = 회당 50,000원이다. A Trainer 50%이면 25,000원, B Trainer 40%이면 20,000원이다. 기존 공제율이나 상품별 Trainer 지급률을 계산에 추가하지 않는다. 1,000원 단위 올림은 확정이며 입력값 검증 상세만 BR-010에 남긴다.

Traceability: 2026-09-16 사용자 확정; PR-006/007/008/010; PD-009. [요구사항](requirements.md).

<a id="br-pay-004"></a>
## BR-PAY-004 — FIXED_AMOUNT 계산

Status: APPROVED

Product Payment Type이 FIXED_AMOUNT이면 Session Payment는 실제 수행 Trainer의 그 Session에 적용되는 Fixed Amount다. Product B의 Session을 Trainer A가 수행하면 20,000원, Trainer B가 수행하면 15,000원이다. 지급액을 Product B에 설정하는 것이 아니다.

Traceability: 2026-09-16 사용자 확정; PR-007/008/010; PD-009. [요구사항](requirements.md).

<a id="br-pay-005"></a>
## BR-PAY-005 — 서비스 상품

Status: APPROVED

서비스 PT Product는 FIXED_AMOUNT를 사용한다. 서비스 Session도 수행 Trainer의 Fixed Amount를 지급한다. 서비스라는 이유로 지급액을 0원으로 바꾸지 않는다. 서비스 Product S와 Trainer A Fixed Amount 20,000원이면 Session Payment는 20,000원이다. 모든 FIXED_AMOUNT Product가 서비스 상품이라는 역방향 정의는 하지 않는다.

Traceability: 2026-09-16 사용자 확정; PR-006/007/008/010; PD-009. [요구사항](requirements.md).

<a id="br-pay-006"></a>
## BR-PAY-006 — 여러 Pass의 차감 우선순위

Status: APPROVED

회원에게 동시에 사용 가능한 Pass가 여럿이면 FIXED_AMOUNT Product의 Pass를 RATE Product의 Pass보다 먼저 사용한다. 판단 기준은 Product Payment Type이며 Trainer의 Rate/Fixed Amount 값이 아니다. FIXED_AMOUNT 잔여 2회와 RATE 잔여 10회에서 3회 진행하면 FIXED → FIXED → RATE, 최종 잔여는 각각 0회와 9회다. 이 사례를 지원하며 복수 사용 가능한 Pass 자체를 미승인으로 취급하지 않는다. 동일 Payment Type에서는 먼저 들어온 Pass부터 사용하는 FIFO를 적용한다. Payment Type 우선순위를 먼저 적용하므로 더 오래된 RATE Pass보다 FIXED_AMOUNT Pass를 먼저 소비한다. 사용 가능 조건·상한과 횟수 조정은 BR-002/ARCH-003, 단일 Issued Branch와 타 지점 사용 가능은 확정이며 구체 사용 조건은 MB-003 후속이다. 잔여 0인 Pass를 정상 차감 대상으로 선택하지 않는다. 이 순서는 허용·사용 가능한 Pass에 적용하며 타 Branch 사용을 자동 허용하지 않는다.

Traceability: 2026-09-16 사용자 확정; PR-003/008; PD-007/008. [요구사항](requirements.md).

<a id="br-pay-007"></a>
## BR-PAY-007 — 지급 설정 변경과 과거 Session

Status: APPROVED

Trainer Rate 또는 Fixed Amount 변경으로 과거 확정 Session Payment를 변경해서는 안 된다. 9월 Rate 50%, Fixed Amount 20,000원에서 10월 60%, 25,000원으로 변경해도 9월 확정 RATE 결과 25,000원과 FIXED_AMOUNT 결과 20,000원은 유지된다. 과거 확정 결과를 현재 설정으로 재계산하지 않는다(BR-PAY-009). 과거 조회와 Monthly Settlement도 보존된 결과를 따른다. 권한 있는 Session 오류 정정/취소는 설정 변경과 구별하여 BR-007에서 상세화하며 잔여·정산 일관성과 감사 요구를 유지한다.

Traceability: 2026-09-16 사용자 확정; PR-007/009/010/027; PD-009/010/012/022. [요구사항](requirements.md).

<a id="br-pay-008"></a>
## BR-PAY-008 — Session 지급 계산의 개념 관계

Status: APPROVED

PT Session → 소비한 PT Pass → PT Product의 Payment Type과 계산 기준, 그리고 Session을 실제 수행한 Trainer → 그 Session에 적용되는 Trainer Rate/Fixed Amount로 Session Payment를 결정한다. 권한 있는 관리자 저장 완료 이후 새로 생성되는 Session부터 새 Rate/Fixed Amount를 적용하며 정상 Session 등록 시 계산·확정한다(BR-PAY-011/012). Pass 담당 Trainer와 실제 수행 Trainer를 혼동하지 않는다. RATE는 Product Price ÷ Product Session Count × Trainer Rate의 결과를 1,000원 단위로 올림하며, FIXED_AMOUNT는 Trainer Fixed Amount 그대로다. Monthly Settlement의 Session 구성은 수행 Trainer·대상 기간별 유효한 지급 결과 집계이며 전체 월 정산은 BR-PAY-016을 따른다. 현재 Trainer 설정으로 과거 확정 결과를 새로 계산하는 작업이 아니다.

Traceability: 2026-09-16 사용자 확정; PR-003/006/007/008/010; PD-009/012. [요구사항](requirements.md).


<a id="br-pay-009"></a>
## BR-PAY-009 — 확정된 Session Payment 불변성

Status: APPROVED

Trainer 지급 결과가 확정된 이후에는 현재 Rate 또는 Fixed Amount 변경으로 과거 결과를 변경해서는 안 된다. 과거 확정 Session Payment를 현재 Trainer 설정으로 재계산하지 않는다.

Product A가 20회/1,000,000원/RATE이고 9월 Trainer Rate가 50%라면 1회 지급 결과는 50,000 × 50% = 25,000원이다. 10월 Rate를 60%로 바꿔도 해당 9월 확정 결과는 25,000원이며 30,000원으로 다시 계산하지 않는다. FIXED_AMOUNT도 기존 확정 20,000원은 현재 설정을 25,000원으로 바꾼 뒤에도 20,000원으로 유지한다.

Monthly Settlement의 Session 구성은 해당 기간의 유효한 Session Payment 결과를 집계하며 전체 합계는 BR-PAY-016을 따른다. 과거 월을 다시 조회할 때도 현재 Trainer 설정을 적용해 지급액을 다시 계산하지 않는다. 권한 있는 Session 오류 정정/취소의 유효 결과 처리와 이력은 BR-007 후속이며, 설정 변경에 따른 과거 재계산을 허용하는 예외가 아니다.

새 Rate/Fixed Amount는 권한 있는 관리자 저장 완료 이후 새로 생성되는 Session에 적용한다. 정상 Session 등록 시 지급액을 계산·확정하며 월 정산에서 다시 계산하지 않는다(BR-PAY-011/012). 이력 또는 계산 snapshot 등 보존 구현 방법은 Architecture에서 결정한다.

Traceability: 2026-09-17 사용자 확정; BR-PAY-007/008을 구체화. PR-007/009/010; PD-009/012. [요구사항](requirements.md), [해결된 적용·확정 시점](open-questions.md#br-006).

<a id="br-pay-010"></a>
## BR-PAY-010 — Trainer Compensation Setting 조회·변경 권한

Status: APPROVED

Rate / Fixed Amount / Base Salary 세 항목의 조회·설정·변경은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 단일 Branch를 Home Branch로 가진 Trainer에게만 허용한다. Operator와 Trainer는 본인 설정을 포함하여 모두 불가하다. 타 지점 지원 수업은 보상 설정 접근 권한을 부여하지 않는다. Backend에서 대상 Trainer의 Home Branch를 검증하며 직접 ID 요청과 감사·정산 등 우회 경로에도 제한을 적용한다.

모든 보상 설정 변경(최초 설정 포함)에 대상 Trainer, 변경 항목, 변경 전 값, 변경 후 값, 변경 Actor, Actor의 권한 및 Branch Context, 변경 시점을 추적한다. 별도 Master Admin 승인 없이 변경 가능하며 변경 요청→승인 대기→승인→반영 절차를 추가하지 않는다. 이 결정은 추가실적 승인이나 월 정산 마감/확정 절차를 면제하지 않는다.

감사 조회를 포함한 다른 경로에서도 권한 없는 사용자에게 값을 노출하지 않는다. 정산 공개 범위는 MB-006, 추가실적 권한은 BR-013이며 자동 허용하지 않는다. 감사 저장 구조·조회 권한 구현은 Architecture에서 결정한다.

Traceability: PD-001/009/022; PR-007/027/030; NFR-001/004; [권한표](users-and-roles.md).

<a id="br-pay-011"></a>
## BR-PAY-011 — Trainer Rate/Fixed Amount 적용 시점

Status: APPROVED

권한 있는 관리자 저장 완료 이후 새로 생성되는 Session부터 새 Rate/Fixed Amount를 적용한다. 과거 확정 Session에는 소급 적용하지 않는다. 실제 진행일이 과거인 Session을 새로 등록하더라도 지급 설정 적용 기준은 Session 생성이며, 소급 날짜 입력 자체의 허용 범위는 BR-008에서 별도로 확인한다. Rate/Fixed Amount에 지정 effective date·다음 날·다음 달 적용을 도입하지 않는다. Base Salary 적용 월은 BR-012 OPEN이며 이 규칙을 적용하지 않는다.

Traceability: 2026-09-17 사용자 최종 확정; PR-007/008; PD-009; BR-006 CLOSED.

<a id="br-pay-012"></a>
## BR-PAY-012 — 정상 Session 등록 시 지급 결과 확정

Status: APPROVED

정상 Session 등록 시 지급액을 계산하고 확정한다. 월 정산의 Session 구성은 해당 기간의 유효한 확정 Session Payment를 집계하며 현재 Trainer 설정으로 재계산하지 않는다. Session 지급 결과 확정은 별도의 월 정산 마감 기능을 뜻하지 않는다. 오류 정정/취소의 허용 범위와 반영 상세는 BR-007에 남긴다.

Traceability: 2026-09-17 사용자 최종 확정; PR-008/010; PD-008/009/012; BR-006 CLOSED.

<a id="br-pay-013"></a>
## BR-PAY-013 — RATE 지급금액 1,000원 단위 올림

Status: APPROVED

RATE Session의 기초 계산액은 Product Price ÷ Product Session Count × 실제 수행 Trainer Rate다. 이 계산 결과를 Session별로 1,000원 단위 올림하여 지급액을 확정한다. 수식으로는 ceil(기초 계산액 ÷ 1,000) × 1,000원이다. 12,300원은 13,000원, 이미 1,000원 배수인 25,000원은 25,000원이다. 회당 Product 단가나 Rate에 먼저 올림하지 않으며, 월 합계에 다시 올림하지 않는다. FIXED_AMOUNT에는 이 규칙을 적용하지 않고 해당 Trainer Fixed Amount 그대로 지급한다.

Traceability: 2026-09-17 사용자 최종 확정; PR-007/008/010; PD-009/012; BR-005 CLOSED. 입력 허용 범위·정밀도는 BR-010 후속.

## 문서 수용 사례 검증

아래는 확정 규칙에 따른 문서 수준 검증이며 구현 실행 시험이 아니다. 아래 수치에는 RATE 1,000원 단위 올림과 동일 Payment Type FIFO를 적용한다.

| CASE | 입력/행위 | 규칙으로 도출되는 결과 | 판정 |
| --- | --- | --- | --- |
| 1 | Product A: 20회, 1,000,000원, RATE; Trainer A 50% | 1,000,000 ÷ 20 × 50% = 25,000원 | 일치 |
| 2 | 동일 Product A; Trainer B 40% | 1,000,000 ÷ 20 × 40% = 20,000원 | 일치 |
| 3 | Product B FIXED_AMOUNT; Trainer A Fixed Amount 20,000원 | 20,000원 | 일치 |
| 4 | 동일 Product B; Trainer B Fixed Amount 15,000원 | 15,000원 | 일치 |
| 5 | 동시에 사용 가능: FIXED_AMOUNT Pass 2회 + RATE Pass 10회; 3회 진행 | FIXED → FIXED → RATE, 잔여 0/9 | 일치 |
| 6 | 과거 확정 후 Trainer Rate 50→60%, Fixed Amount 20,000→25,000원 | 과거 RATE 25,000원 및 FIXED_AMOUNT 20,000원 유지 | 일치 |
| 서비스 보완 | 서비스 Product S FIXED_AMOUNT; Trainer A 20,000원 | 서비스여도 20,000원 지급 | 일치 |

## 남은 경계

Pass 상태·사용 조건·횟수 조정(BR-001/002, ARCH-003), 정정/취소(BR-007), 날짜·월 경계(BR-008), 입력값 검증(BR-010), Product 기준정보 변경의 기존 Pass 적용 범위(BR-011)는 남은 질문이다. Rate/Fixed Amount 적용 시점·등록 시 확정·BR-PAY-010 보상 권한·FIFO·RATE 올림은 확정이며 Architecture 공통 제약 검토는 가능하나 Branch 관련 상세 설계 확정은 MB-001–008의 Product 결정이 필요하다. 남은 세부사항은 관련 상세 설계 또는 구현 확정 전에 확인한다.

Architecture는 지급 설정 이력 또는 Session 계산 snapshot 등의 보존 방법을 검토한다. 이번 단계에서는 어느 방식도 선택하지 않으며 schema·API·기술을 설계하지 않는다.

## 추가 검증 CASE A–E

문서 수준에서 아래 결과가 BR-PAY-009/010과 요구사항·시나리오에 일치함을 검토했다. 애플리케이션 실행 시험은 아니다.

| CASE | 행위 | 기대 결과 및 근거 |
| --- | --- | --- |
| A | Master Admin이 Rate 50% → 60% 변경 | 과거 확정 25,000원 유지. 권한 있는 관리자 저장 완료 이후 새로 생성되는 Session에는 새 Rate 적용 |
| B | Master Admin이 Fixed Amount 20,000 → 25,000원 변경 | 과거 확정 Session Payment 20,000원 유지 |
| C | Operator 또는 Trainer가 Trainer Rate 변경 시도 | 허용되지 않는 업무. 일반 운영자는 Rate/Fixed Amount 설정·변경 불가 |
| D | Master Admin이 Trainer Rate 변경 | 허용. 대상 Trainer·항목·변경 전후 값·변경자·시점을 감사 가능 |
| E | 과거 월 Monthly Settlement 재조회 | 해당 기간 유효한 Session Payment 결과 집계. 현재 Rate/Fixed Amount로 과거 지급액 재계산 금지 |

BR-PAY-009/010은 확정 규칙이며, open-questions.md의 BR-009(추가 통계)/BR-010(입력값 검증)과 다른 ID다.

## Product Baseline 추가 수용 사례

| CASE | 입력/행위 | 기대 결과 |
| --- | --- | --- |
| F | Rate 50%에서 60%로 Master Admin 저장 완료 후 Product A Session 신규 등록 | 등록 시 30,000원 확정; 기존 확정 25,000원 유지 |
| G | Fixed Amount 20,000원에서 25,000원으로 저장 완료 후 신규 등록 | 등록 시 25,000원 확정; 기존 확정 20,000원 유지 |
| H | 일반 운영자가 Rate/Fixed Amount 조회 시도 | Operator·Trainer는 조회 불가; 관리자는 BR-PAY-010 대상 범위에서 허용 |
| I | 사용 가능한 RATE Pass가 가장 오래되고, FIXED_AMOUNT Pass F1이 F2보다 먼저 들어옴; 각 1회 잔여 | F1 → F2 → RATE 순서로 소비 |
| J | RATE 기초 계산액 12,300원인 Session 두 건 | 각각 13,000원 확정, 월 집계 26,000원; 월 원금 합계 24,600원을 올림한 25,000원이 아님 |
| K | FIXED_AMOUNT 설정 12,300원인 정상 Session | 12,300원 확정; 13,000원으로 올림하지 않음 |

현재 규칙은 Architecture 설계를 위한 Product Baseline이다. [인계 문서](architecture-handoff.md)를 따른다. 위 검증은 문서 수준이며 애플리케이션 실행 시험이 아니다.

<a id="br-ops-001"></a>
## BR-OPS-001 — 지점 관계·Context와 운영 이력

Status: APPROVED

Trainer는 한 시점에 Home Branch 하나에 소속되고 Branch에는 여러 Trainer가 있을 수 있다. Branch당 Trainer 한 명인 1:1이나 Trainer 동시 복수 소속 N:M을 요구하지 않는다. Member도 Home Branch 하나를 가지며 Pass는 Issued Branch 하나를 가진다. Trainer·Member·Pass는 허용된 조건에서 타 지점 PT 업무를 수행·이용할 수 있다. Session은 실제 Performed Branch를 식별하고 소속·발급 지점 변경으로 과거 수행 지점이 바뀌지 않아야 한다. Product는 Organization 공통 Catalog이며 지점별 가격 정책은 추가하지 않는다. Branch Admin은 하나의 Branch를 관리하고 일부 여러 지점만 담당하는 중간 관리자 역할은 추가하지 않는다.

특정 타 지점 Member/Pass/Session의 업무 이용과 그 Branch 전체 데이터 접근 권한은 구별한다. 구체 허용 조건은 MB-001/002/003/005 OPEN이며 기술 구현으로 대신 결정하지 않는다. Branch Scope는 Backend에서 강제한다. Trainer 이동 적용 시점·과거 기록 정책은 MB-001, 정산/비용 귀속은 MB-010이며 Performed Branch 보존은 확정이다.

Trainer 직접 로그인·등록/조회, 개별 날짜 기록, 정상 Pass 차감과 일반 Session 지급 규칙을 유지한다. 타 지점 보상 구성은 MB-009 결정 게이트다. 관리자 수동 횟수 조정은 사유와 이력을 남기며 Session 정정/취소에 따른 횟수 복원·이력·정산 일관성을 유지한다. 상세는 BR-002/007, 동시성·트랜잭션은 Architecture 결정이다.

Traceability: PD-001/002/004/007/010/012/022; PR-002/003/005/006/008/010/020/027/029/030.

## Multi-Branch 문서 수용 사례

| CASE | 행위 | 기대 결과 |
| --- | --- | --- |
| MB-A | Branch A Admin이 Branch B Member ID로 조회·수정 시도 | 허용되지 않은 접근은 Backend에서 금지. 특정 교차 업무 조건은 MB-002/005이며 전체 목록 접근을 자동 허용하지 않음 |
| MB-B | Branch Admin·Operator·Trainer가 보상 설정 조회·변경 시도 | Branch Admin은 자기 Branch 소속 Trainer만 허용, Operator·Trainer는 모두 불가 |
| MB-C | Trainer가 Smartphone으로 허용된 Member/Pass와 실제 Branch의 Session 등록 | 기존 우선순위·FIFO·차감·계산·확정 규칙 적용, 자신의 Session 조회 가능, 지급 설정은 비노출 |
| MB-D | Master Admin이 Branch별 Settlement 확인 | 기본급·유효 Session Payment·추가실적 구분, 현재 설정 재계산 금지; 지점 귀속은 MB-010 |
| MB-E | Branch A Admin의 Settlement 접근 | 허용 Branch만 접근. 금액 노출은 MB-006 결정 전 일괄 허용하지 않음 |

문서 기대 결과이며 Backend·UI 실행 시험은 수행하지 않았다.

<a id="br-pay-014"></a>
## BR-PAY-014 — 월 고정 기본급

Status: APPROVED

Trainer별 월 고정 Base Salary를 지원한다. 예: A 2,500,000원/월. Product나 Session마다 붙는 금액이 아니며 입퇴사 일할·근무일수·휴직 기반 자동 급여 계산은 v1 제외다. 그런 상황의 적용 금액 업무 정책과 변경 적용 월·관리자 월 지정·미확정 정산 반영은 BR-012 OPEN이다. 현재 기본급 변경으로 이미 확정된 과거 정산의 적용 기본급과 합계를 자동 변경하지 않는다. 별도 과거 정정 업무와 자동 소급은 구별한다. 이력·결과 보존 구현은 Architecture 결정이다.

Traceability: PD-009/012; PR-007/010; BR-PAY-010.

<a id="br-pay-015"></a>
## BR-PAY-015 — 추가실적

Status: APPROVED

추가실적은 Trainer에게 인정하는 인센티브이며 v1 범위다. 타 지점 지원 수업·회원 유지·기타 인정 실적이 예다. Session과 관련될 수도, Session 없이 발생할 수도 있다. 대상 Trainer·사유/유형·금액·발생 시점/정산 기간·Branch Context·필요시 Member/Session·등록자/시점·정정/취소 이력을 식별한다. 생성·정정·취소는 감사 가능한 금액 변경 업무다. 고객 결제·매출·가계부나 AS-IS 수동 매출과 동일시하지 않는다.

등록자 권한과 지점 기준·Trainer 신청·관리자 승인·수동/유형별 산정·정정/취소·마감 이후 처리는 BR-013 OPEN이다. 보상 설정 권한이나 승인 생략을 자동 적용하지 않는다. 타 지점 수업 보상은 추가실적으로 정산할 수 있어야 하지만 일반 Session Payment에 추가인지 전체 대체인지는 MB-009 결정 게이트다. 기록/Pass 차감은 유지하되 A/B 선택 전 기본 수당 0원 또는 이중 지급을 임의 확정하지 않는다.

Traceability: PD-027; PR-031/027/010; MB-009/010.

<a id="br-pay-016"></a>
## BR-PAY-016 — 월 정산 구성과 보존

Status: APPROVED

Monthly Settlement = 해당 월 적용 Base Salary + 유효한 Session Payment 합계 + 유효한 Additional Performance 합계다. Trainer·대상 월·적용 기본급·Session 수·Session Payment 합계·추가실적 내역/합계·월 정산 합계를 구분한다. 2,500,000원 + 1,200,000원 + 150,000원 = 3,850,000원이며 여러 지점 수업으로 동일 월 기본급을 중복 가산하지 않는다. 타 지점 Session Payment 포함 여부는 MB-009 결정 전 확정하지 않는다.

현재 Rate/Fixed Amount/Base Salary 변경으로 과거 확정 Session Payment 및 확정 월 정산의 적용 기본급·합계를 자동 변경하지 않는다. 정정 업무는 현재 설정 변경과 별개이며 정정/취소 반영과 마감/확정 절차는 BR-007/009/013 OPEN이다. 정산 공개는 MB-006, 기본급 적용 월은 BR-012, 지점 이동·교차 수업·추가실적 집계/비용 귀속은 MB-010 OPEN이다. Home Branch·Performed Branch·정산 귀속 Branch를 같다고 가정하지 않는다. 보존 방식은 Architecture에서 결정한다.

Traceability: PD-012/027; PR-010; BR-PAY-009/014/015.
