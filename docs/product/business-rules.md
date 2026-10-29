# Trainer Payment Business Rules

상태: APPROVED-TO-BE / 사용자 확정(2026-09-16/17 및 2026-10-10). 2026-09-17 Multi-Branch 변경 지시가 이전 결정과 충돌하면 우선하며 비충돌 규칙은 유지한다. 보상 설정 권한은 BR-PAY-010으로 갱신한다. 2026-10-10 사용자 정정으로 타 지점 수업의 보상 전체를 일반 PT 수당 대신 추가실적으로 처리하도록 MB-009를 확정했다(BR-PAY-015/016). AS-IS 구현 사실이나 DB Column/Table 정의가 아니다. [결정](product-decisions.md), [요구사항](requirements.md), [남은 질문](open-questions.md).

## 지급 규칙의 적용 범위 — 2026-10-10 정정

BR-PAY-001–013의 일반 Session Payment 계산·적용·등록 시 확정 규칙은 유지한다. 타 지점 수업에는 MB-009/BR-PAY-015의 보상 전체 추가실적 처리를 적용하고 일반 Session Payment를 별도로 정산에 합산하지 않는다. 타 지점 지원 수업 보상은 관리자가 수업 건별 금액을 직접 입력한다. 일반 RATE/FIXED_AMOUNT 결과를 자동 지급액으로 사용하지 않는다. 타 지점 지원 수업은 보상 금액 없이도 허용된 PT 진행 기록과 Pass 차감을 먼저 완료한다. 권한 있는 관리자가 나중에 수업 건별 금액을 저장할 때 해당 Additional Performance 보상을 확정한다. 금액 미입력은 확정된 0원과 구분하고 누락 건을 추적할 수 있어야 한다. 해당 Trainer의 해당 월 정산 대상 지원 수업에 금액 미입력 건이 하나라도 있으면 그 Trainer·월 정산을 확정할 수 없다. 타 지점 지원 수업 보상은 권한 있는 관리자가 사유를 기록하면 0원으로 명시적으로 확정할 수 있다. 사유 없는 0원 입력은 보상 확정이 불가하다. 사유를 남기고 확정한 0원은 금액 미입력이 아니므로 그 건으로 월 정산 확정을 차단하지 않는다. 다른 미입력 건이 남으면 기존 차단 조건을 유지한다. 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin에게 Organization 전체, Branch Admin에게 대상 Trainer Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안의 본인 건도 허용하고 변경 이력을 남긴다. 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin·Branch Admin 모두 관리 범위 안에서 본인 건을 포함해 별도 승인 없이 저장 성공 즉시 반영한다. Master나 다른 관리자의 승인 대기를 두지 않으며 권한 검증과 변경 이력을 유지한다. 월 정산 확정 전 지원 수업 보상 금액의 모든 수정에는 변경 사유가 필수다. 양수 간 변경·0원에서 양수로 변경·양수에서 0원으로 변경 모두 적용하며, 사유 없이는 금액을 수정할 수 없다. 변경 전후 금액·변경 사유·수정자·수정 시점을 이력으로 남긴다. 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer의 지원 수업 보상 정정을 위해 월 정산을 확정 해제·재확정할 때는 Master의 별도 승인을 두지 않는다. Master 승인 대기 단계 없이 관리 범위 안에서 직접 처리하며 이전 확정본과 해제·재확정 이력 및 감사를 유지한다. 지원 수업 보상 정정의 월 정산 확정 해제에는 사유가 필수이며, 사유 없이 해제할 수 없다. 사유·해제자·시점을 이력으로 남긴다. 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 남은 정정·취소 절차는 BR-009/013 등 관련 OPEN을 따른다. 금액 미입력 건의 추적 표현·정정 연동·연계 상세·나머지 정정/취소는 BR-013 OPEN이다. 실제 PT 진행 기록·Pass 차감 우선순위와 잔여·감사 원칙은 타 지점 수업에도 유지한다. 이 문서의 일반 Session Payment 수치 사례는 해당 일반 지급 정책의 적용 대상을 전제로 한다.

## 용어

| 용어 | 제품 의미 |
| --- | --- |
| Organization | 하나의 헬스장 브랜드/운영 조직 |
| Branch | Organization 아래 실제 운영 지점. 단일 Home/Issued Branch와 실제 Performed Branch를 구분; 정산 귀속은 MB-010 |
| PT Product | PT 상품 자체, 총 횟수, 판매가격, Payment Type; Organization 공통 Catalog; 생성·수정은 Master Admin 전용(MB-007 CLOSED) |
| Trainer Compensation Setting | Trainer 기준 Rate·Fixed Amount·월 Base Salary |
| PT Pass | Member가 특정 Product를 이용하는 단위 |
| PT Session | 기존 회원에게 실제 수행한 PT 수업 1회의 완료 기록과 실제 Branch Context. 예약·시간표 생성 또는 상품 등록·Pass 발급이 아님 |
| Session Payment | 일반 지급 정책이 적용되는 PT Session의 수행 Trainer 지급 결과. 타 지점 수업 보상 전체는 별도의 Additional Performance 구성으로 반영 |
| Monthly Settlement | 적용 기본급 + 유효 Session Payment 합계 + 유효 추가실적 합계 |

<a id="br-pay-001"></a>
## BR-PAY-001 — Product의 지급 방식

Status: APPROVED

각 PT Product는 총 횟수(Product Session Count), 판매가격(Product Price), Payment Type으로 설명한다. Payment Type은 RATE 또는 FIXED_AMOUNT다. 지급 계산에 관한 Product 설정은 방식이며 Trainer 지급률·고정 지급금액은 Product 값이 아니다. Master Admin이 주요 기준정보로 관리한다.

2026-10-10 사용자 확정(BR-011 CLOSED): 기존 Pass는 발급 당시 상품 가격·총횟수·Payment Type을 유지한다. 상품 변경은 이후 새로 발급하는 Pass부터 적용하며 기존 Pass의 조건·잔여를 덮어쓰지 않는다. 이 문서의 Session Payment 계산에 쓰는 Product Price/Session Count/Payment Type은 소비 Pass 발급 당시 상품 조건을 뜻한다. Trainer Rate/Fixed Amount는 발급 시 고정하지 않고 BR-PAY-011의 등록 시점 적용을 유지한다. 수동 횟수 조정(BR-002)과 타 지점 추가실적 산정(BR-013)은 별도 정책이다. 조건 보존의 물리 저장 구조는 Architecture 결정이다.

2026-10-12 사용자 확정(Organization 공통 PT 상품의 생성·수정 권한 질문의 1번): 공통 Product Catalog의 상품 생성·수정은 Master Admin만 Organization 범위에서 허용한다. Master 권한 없는 Branch Admin·Operator·Trainer는 생성·수정할 수 없으며 관리자/Trainer 겸임도 보유한 Master 권한으로 판단한다. 자기 지점에서 사용할 목적·직접 Product ID·클라이언트가 보낸 role/Organization/Branch Context로 권한을 우회할 수 없다. Backend는 처리 시점 검증된 Caller의 현재 Master 권한과 Organization Scope를 확인한다. 상품 가격·총횟수·Payment Type 변경은 이후 새 Pass부터 적용하고 기존 Pass의 발급 당시 조건·잔여·과거 수업/지급/정산을 덮어쓰거나 자동 재계산하지 않는다(BR-011). 이 결정은 상품 생성·수정 권한이며 상품 조회/Pass 발급 등 다른 행위 권한이나 상품 상태 전이·삭제 정책을 추가 확정하지 않는다. MB-007은 CLOSED다.

2026-10-12 사용자 확정(상품 판매 중단이 기존 이용권에 미치는 영향 질문의 1번): PT Product의 판매 중단은 해당 상품의 새 Pass 발급만 차단한다. 이미 발급한 Pass는 기존 권한·잔여·사용 조건을 충족하면 계속 사용할 수 있다. 현재 Catalog의 판매 중단 상태만으로 기존 Pass를 차감 후보에서 제외하거나 사용을 중단시키지 않는다. 기존 Pass의 발급 당시 가격·총횟수·Payment Type, 잔여 및 과거 수업/지급/정산을 덮어쓰거나 자동 재계산하지 않는다. 상품 판매 중단 자체는 PT 진행/차감 또는 Pass 취소/수동 만료가 아니다.

판매 중단은 공통 상품 정보 변경이므로 기존 Master 전용 생성/수정 권한과 현재 Organization Scope 검증을 동일 적용한다(2026-10-11 사용자 일관성 지시 적용, MB-007 CLOSED). 새 Pass 발급 요청은 Backend에서 상품의 판매 가능 상태를 검증하며 Master 권한이나 직접 Product ID만으로 판매 중단을 우회할 수 없다. 기존 Pass의 이용에는 기존 FIXED_AMOUNT 우선/FIFO·현재 잔여 > 0·개별 수동 만료와 과거 수업 등록 정책·Actor/Organization/Member 관계 조건을 유지한다. 잔여 0이나 수동 만료 등 다른 차단 사유를 면제하거나 자동 해제하지 않는다. 상품 판매 재개 및 그 밖의 상태 전이/삭제·정확한 상태명/저장·동시 발급 경합의 구체 계약은 이번 결정으로 확정하지 않는다.

Traceability: 2026-09-16 사용자 확정; PR-006; PD-009. [요구사항](requirements.md).

<a id="br-pay-002"></a>
## BR-PAY-002 — Trainer Compensation Setting

Status: APPROVED

Trainer 기준 Rate, Fixed Amount, Base Salary를 제품·권한 개념으로 묶는다. Rate는 RATE 상품 지급률, Fixed Amount는 FIXED_AMOUNT 상품 회당 지급액, Base Salary는 월 고정 기본급이다. Product는 방식만 정하며 Product별 Trainer Rate/Fixed Amount는 두지 않는다. 세 항목을 같은 테이블에 저장하라는 뜻이 아니다. 예: A Rate 50%/Fixed Amount 20,000원, B 40%/15,000원은 예시이며 기본값이 아니다. Base Salary는 BR-PAY-014, 접근 권한은 BR-PAY-010이다.

Traceability: PD-009/012; PR-007.

2026-10-12 H1=2 승인: Rate는 정수 퍼센트만 허용하며 소수 비율을 자동 반올림/절사하지 않는다(BR-PAY-018). 현재/과거 지급 공식·적용 시점과 설정 권한은 유지하고 범위/누락 정책은 별도다. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch).

<a id="br-pay-003"></a>
## BR-PAY-003 — RATE 계산

Status: APPROVED

소비한 Pass 발급 당시 Product Payment Type이 RATE이면 기초 계산액 = Product Price ÷ Product Session Count × Session을 수행한 Trainer의 적용 Rate이며, Session Payment는 기초 계산액을 1,000원 단위로 올림한 금액이다(BR-PAY-013). Product A의 1,000,000원 ÷ 20회 = 회당 50,000원이다. A Trainer 50%이면 25,000원, B Trainer 40%이면 20,000원이다. 기존 공제율이나 상품별 Trainer 지급률을 계산에 추가하지 않는다. 1,000원 단위 올림은 확정이며 입력값 검증 상세만 BR-010에 남긴다.

Traceability: 2026-09-16 사용자 확정; PR-006/007/008/010; PD-009. [요구사항](requirements.md).

<a id="br-pay-004"></a>
## BR-PAY-004 — FIXED_AMOUNT 계산

Status: APPROVED

소비한 Pass 발급 당시 Product Payment Type이 FIXED_AMOUNT이면 Session Payment는 실제 수행 Trainer의 그 Session에 적용되는 Fixed Amount다. Product B의 Session을 Trainer A가 수행하면 20,000원, Trainer B가 수행하면 15,000원이다. 지급액을 Product B에 설정하는 것이 아니다.

Traceability: 2026-09-16 사용자 확정; PR-007/008/010; PD-009. [요구사항](requirements.md).

일반 Fixed Amount 입력은 BR-PAY-022(Q2)의 0원 이상 정수 원이다. 명시적 0원도 실제 설정값으로 사용하지만 미설정을 0원으로 대체하지 않는다. 기존 FIXED_AMOUNT 그대로/추가 올림 없음과 서비스의 실제 Trainer 설정 사용·지원 전체 추가실적 규칙은 유지한다. [Q 승인](product-decisions.md#review-20261013-q-batch); V-115 미구성·미실행.

<a id="br-pay-005"></a>
## BR-PAY-005 — 서비스 상품

Status: APPROVED

서비스 PT Product는 FIXED_AMOUNT를 사용한다. 서비스 Session도 수행 Trainer의 Fixed Amount를 지급한다. 서비스라는 이유로 지급액을 0원으로 바꾸지 않는다. 서비스 Product S와 Trainer A Fixed Amount 20,000원이면 Session Payment는 20,000원이다. 모든 FIXED_AMOUNT Product가 서비스 상품이라는 역방향 정의는 하지 않는다.

Traceability: 2026-09-16 사용자 확정; PR-006/007/008/010; PD-009. [요구사항](requirements.md).

<a id="br-pay-006"></a>
## BR-PAY-006 — 여러 Pass의 차감 우선순위

Status: APPROVED

회원에게 동시에 사용 가능한 Pass가 여럿이면 FIXED_AMOUNT Product의 Pass를 RATE Product의 Pass보다 먼저 사용한다. 판단 기준은 각 Pass 발급 당시 Product Payment Type이며 현재 Catalog의 변경된 Type이나 Trainer의 Rate/Fixed Amount 값이 아니다. FIXED_AMOUNT 잔여 2회와 RATE 잔여 10회에서 3회 진행하면 FIXED → FIXED → RATE, 최종 잔여는 각각 0회와 9회다. 이 사례를 지원하며 복수 사용 가능한 Pass 자체를 미승인으로 취급하지 않는다. 동일 Payment Type에서는 먼저 들어온 Pass부터 사용하는 FIFO를 적용한다. Payment Type 우선순위를 먼저 적용하므로 더 오래된 RATE Pass보다 FIXED_AMOUNT Pass를 먼저 소비한다. 사용 가능 조건·상한과 횟수 조정은 BR-002/ARCH-003 후속이다. 동일 Organization 안의 타 지점 사용에 별도 사전 승인을 두지 않으며 Issued Branch 차이로 후보를 제외하거나 발급 지점 우선순위를 추가하지 않는다(2026-10-11 사용자 확정, BR-OPS-001). 잔여 0인 Pass를 정상 차감 대상으로 선택하지 않는다. 이 순서는 허용·사용 가능한 Pass에 적용하며 Actor의 Member 조회/PT 업무 권한을 자동 부여하지 않는다. 관련 업무 접근 범위의 나머지는 MB-003/005 후속이다.

2026-10-12 사용자 확정(과거 수업 등록 시 이용권 범위 질문의 1번): 늦게 등록하는 PT 수업의 Pass 차감 후보는 실제 수업 당시 이미 발급되어 있던 이용권으로 한정한다. 수업 이후 발급된 Pass는 등록 시점에 보유 중이고 잔여가 있어도 그 과거 수업의 후보에 포함하지 않는다. 9월 20일 수업을 10월 5일 등록할 때 10월 1일 발급한 새 Pass는 제외한다.

발급 시점 조건과 기존 Actor/Organization/Member 관계·사용 조건을 충족한 후보 안에서 FIXED_AMOUNT 우선·동일 Payment Type FIFO를 적용한다. 이후 발급된 FIXED_AMOUNT를 우선 차감하려고 포함하지 않으며 발급 시점 조건을 만족한 RATE가 사용 가능하다면 그 Pass가 후보가 된다. 잔여 > 0 등 기존 사용 조건·동일 Organization의 타 지점 사용 사전 승인 없음·발급 조건 보존은 유지한다. 발급 시점 조건은 확정이며 수동 만료 전 사용 가능했던 수업의 늦은 등록은 아래 2026-10-12 확정 정책을 따른다. 발급/사용 시작 의미는 BR-OPS-031로 확정됐다. 다른 종료 조건·역사 사실 확인 불가/충돌·같은 날짜 내 순서/시각 정밀도는 BR-001/002·ARCH-003 및 관련 Architecture 후속 대상이다. 발급 시점을 과거로 임의 변경하거나 현재 보유만으로 당시 발급 사실을 대체하지 않는다.

2026-10-12 사용자 확정: 수동 만료 전 실제 수업 당시 사용 가능했던 Pass는 현재 만료 상태여도 해당 과거 수업의 후보에 포함할 수 있다(BR-OPS-004). 현재 만료만으로 제외하지 않고 기존 권한·정산·현재 잔여 > 0 등 나머지 조건과 FIXED_AMOUNT 우선/FIFO를 적용한다. 선택된 Pass는 현재 잔여 1회 차감/현재 만료 상태·이력 유지이며 만료 해제를 선행 요구하지 않는다. 다른 종료 사유나 수업 당시 사용 불가 조건까지 면제하지 않는다.

2026-10-12 사용자 확정: Product 판매 중단은 새 Pass 발급만 차단하며 이미 발급된 Pass의 사용 조건을 변경하지 않는다(BR-PAY-001). 나머지 권한·잔여/상태·시점 조건을 충족한 기존 Pass는 현재 Catalog의 판매 중단만으로 후보에서 제외하지 않고 기존 FIXED_AMOUNT 우선/FIFO를 적용한다. 판매 중단을 이유로 기존 Pass 잔여를 소멸시키거나 자동 만료/해제하지 않는다.

Traceability: 2026-09-16 사용자 확정; PR-003/008; PD-007/008. [요구사항](requirements.md).

2026-10-13 O1/O2=1: 허용된 담당/개별 지원 회원의 본인 실제 수업 등록은 다른 Trainer 담당분도 포함한 그 Member 전체 적격 Pass에서 선택한다. 본인 담당 Pass만으로 후보를 좁히지 않으며 개별 지원 회원은 본인 담당 Pass 없이도 등록할 수 있다. 위 실제 발급/사용 가능 시점·현재 잔여·만료 예외와 기존 인가/정산 조건 안에서 FIXED_AMOUNT 우선/동일 Type FIFO를 유지한다. 차감으로 Assigned Trainer를 바꾸지 않으며 일반 지급은 실제 수행자의 생성 시점 설정을 사용한다. 전체 후보의 서버 내부 사용은 개별 Pass/다른 Trainer 정보·금액 무제한 공개가 아니다. 지원 허용과 보상 구분은 별개다(BR-OPS-026; [O 승인](product-decisions.md#review-20261013-o-batch); V-110/111 미구성·미실행).

T1/T2 시간 기준 후속: 시스템 신규 발급 완료 시각을 발급 시각으로 기록하고 별도 사용 시작일 없이 기존 사용 조건을 적용한다. 과거 발급 날짜 입력/소급 발급은 v1 제외이므로 구매/등록 지연이나 이후 발급 Pass로 과거 수업 후보 조건을 우회하지 않는다. 기존 FIXED_AMOUNT 우선/FIFO·만료 전 늦은 등록/현재 잔여·정산/인가 조건과 생성 시점 지급은 유지한다(BR-OPS-031; [T 승인](product-decisions.md#review-20261013-t-batch); V-120/121 미구성·미실행).

<a id="br-pay-007"></a>
## BR-PAY-007 — 지급 설정 변경과 과거 Session

Status: APPROVED

Trainer Rate 또는 Fixed Amount 변경으로 과거 확정 Session Payment를 변경해서는 안 된다. 9월 Rate 50%, Fixed Amount 20,000원에서 10월 60%, 25,000원으로 변경해도 9월 확정 RATE 결과 25,000원과 FIXED_AMOUNT 결과 20,000원은 유지된다. 과거 확정 결과를 현재 설정으로 재계산하지 않는다(BR-PAY-009). 과거 조회와 Monthly Settlement도 보존된 결과를 따른다. 권한 있는 Session 오류 정정/취소는 설정 변경과 구별하여 BR-007에서 상세화하며 잔여·정산 일관성과 감사 요구를 유지한다.

Traceability: 2026-09-16 사용자 확정; PR-007/009/010/027; PD-009/010/012/022. [요구사항](requirements.md).

<a id="br-pay-008"></a>
## BR-PAY-008 — Session 지급 계산의 개념 관계

Status: APPROVED

PT Session → 소비한 PT Pass → 그 Pass 발급 당시 PT Product의 Payment Type과 계산 기준, 그리고 Session을 실제 수행한 Trainer → 그 Session에 적용되는 Trainer Rate/Fixed Amount로 Session Payment를 결정한다. 권한 있는 관리자 저장 완료 이후 새로 생성되는 Session부터 새 Rate/Fixed Amount를 적용하며 정상 Session 등록 시 계산·확정한다(BR-PAY-011/012). Pass 담당 Trainer와 실제 수행 Trainer를 혼동하지 않는다. RATE는 Product Price ÷ Product Session Count × Trainer Rate의 결과를 1,000원 단위로 올림하며, FIXED_AMOUNT는 Trainer Fixed Amount 그대로다. Monthly Settlement의 Session 구성은 수행 Trainer·대상 기간별 유효한 지급 결과 집계이며 전체 월 정산은 BR-PAY-016을 따른다. 현재 Trainer 설정으로 과거 확정 결과를 새로 계산하는 작업이 아니다.

Traceability: 2026-09-16 사용자 확정; PR-003/006/007/008/010; PD-009/012. [요구사항](requirements.md).


<a id="br-pay-009"></a>
## BR-PAY-009 — 확정된 Session Payment 불변성

Status: APPROVED

Trainer 지급 결과가 확정된 이후에는 현재 Rate 또는 Fixed Amount 변경으로 과거 결과를 변경해서는 안 된다. 과거 확정 Session Payment를 현재 Trainer 설정으로 재계산하지 않는다.

Product A가 20회/1,000,000원/RATE이고 9월 Trainer Rate가 50%라면 1회 지급 결과는 50,000 × 50% = 25,000원이다. 10월 Rate를 60%로 바꿔도 해당 9월 확정 결과는 25,000원이며 30,000원으로 다시 계산하지 않는다. FIXED_AMOUNT도 기존 확정 20,000원은 현재 설정을 25,000원으로 바꾼 뒤에도 20,000원으로 유지한다.

Monthly Settlement의 Session 구성은 해당 기간의 유효한 Session Payment 결과를 집계하며 전체 합계는 BR-PAY-016을 따른다. 과거 월을 다시 조회할 때도 현재 Trainer 설정을 적용해 지급액을 다시 계산하지 않는다. 권한 있는 Session 오류 정정/취소의 유효 결과 처리와 이력은 BR-007 후속이며, 설정 변경에 따른 과거 재계산을 허용하는 예외가 아니다.

새 Rate/Fixed Amount는 권한 있는 관리자 저장 완료 이후 새로 생성되는 Session에 적용한다. 정상 Session 등록 시 지급액을 계산·확정하며 월 정산에서 다시 계산하지 않는다(BR-PAY-011/012). 이력 또는 계산 snapshot 등 보존 구현 방법은 Architecture에서 결정한다.

2026-10-11 사용자 확정(이동 전후 일반 PT 수당의 비용 귀속 질문의 1번 답변): 일반 Session Payment는 해당 PT 진행 기록의 실제 Performed Branch 비용으로 집계한다. 이미 확정된 수업별 지급액을 지점별로 합산하며 대상 월말 Home Branch로 전액을 모으지 않는다. 이는 확정된 지급액의 내부 비용 집계 기준이며 현재 Trainer 설정으로 과거 지급을 재계산하거나 지점 합계에 올림을 다시 적용하지 않는다. 이후 Home Branch 변경만으로 과거 수행 지점에 따른 귀속을 바꾸지 않는다. 정정/취소 절차의 남은 정책은 BR-007/009, 비용 보고 공개/집계 상세는 MB-010/006을 따른다.

Traceability: 2026-09-17 사용자 확정; BR-PAY-007/008을 구체화. PR-007/009/010; PD-009/012. [요구사항](requirements.md), [해결된 적용·확정 시점](open-questions.md#br-006).

<a id="br-pay-010"></a>
## BR-PAY-010 — Trainer Compensation Setting 조회·변경 권한

Status: APPROVED

Rate / Fixed Amount / Base Salary 세 항목의 조회·설정·변경은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 단일 Branch를 Home Branch로 가진 Trainer에게만 허용한다. 관리자와 Trainer를 겸하는 계정은 관리 권한 범위 안이면 본인의 세 항목도 조회·변경할 수 있다. Master Admin은 본인 포함 허용하며, Branch Admin은 본인 Trainer의 Home Branch가 관리 Branch일 때 본인도 허용한다. 관리자 권한이 없는 Operator·Trainer 계정은 본인 포함 모든 Trainer 설정 조회·변경이 불가하다. 타 지점 지원 수업은 보상 설정 접근 권한을 부여하지 않는다. Backend에서 대상 Trainer의 Home Branch를 검증하며 직접 ID 요청과 감사·정산 등 우회 경로에도 제한을 적용한다.

모든 보상 설정 변경(최초 설정 포함)에 대상 Trainer, 변경 항목, 변경 전 값, 변경 후 값, 변경 Actor, Actor의 권한 및 Branch Context, 변경 시점을 추적한다. 별도 Master Admin 승인 없이 변경 가능하며 변경 요청→승인 대기→승인→반영 절차를 추가하지 않는다. 이 결정은 추가실적 승인이나 월 정산 마감/확정 절차를 면제하지 않는다.

감사 조회를 포함한 다른 경로에서도 권한 없는 사용자에게 값을 노출하지 않는다. 정산 공개 범위는 MB-006, 추가실적 권한은 BR-013이며 자동 허용하지 않는다. 감사 저장 구조·조회 권한 구현은 Architecture에서 결정한다.

Traceability: 2026-10-10 사용자 최종 정정 — 관리 범위 안이면 본인 설정 허용; PD-001/009/022; PR-007/027/030; NFR-001/004; [권한표](users-and-roles.md).

수업별 확정 보상 금액의 공개는 BR-PAY-021(N1/N2)의 별도 제한을 따른다. 비관리자 Trainer 본인 금액과 현재 다른 Home Branch Trainer의 자기 Performed Branch 수업 금액을 수행 지점 Branch Admin에게 공개하지 않는다. 보상 설정·PT 기록·보상 금액·전체 월 정산의 인가를 서로 자동 상속하지 않으며 현재 관리자 Scope/겸임의 독립 권한은 유지한다. [N 승인](product-decisions.md#review-20261013-n-batch).

<a id="br-pay-011"></a>
## BR-PAY-011 — Trainer Rate/Fixed Amount 적용 시점

Status: APPROVED

권한 있는 관리자 저장 완료 이후 새로 생성되는 Session부터 새 Rate/Fixed Amount를 적용한다. 과거 확정 Session에는 소급 적용하지 않는다. 실제 진행일이 과거인 Session을 새로 등록하더라도 지급 설정 적용 기준은 Session 생성이며, 소급 날짜 입력 자체의 허용 범위는 BR-008에서 별도로 확인한다. Rate/Fixed Amount에 지정 effective date·다음 날·다음 달 적용을 도입하지 않는다. Base Salary는 관리자가 적용 시작 월을 지정하며(BR-PAY-014), 이 신규 Session 적용 규칙을 적용하지 않는다. 변경이 적용되는 수동 지정 없는 기존 미확정 정산의 기본급·합계는 자동 반영한다. 미확정인 과거 월도 기본급 적용 시작 월로 지정할 수 있다. 미리 등록할 수 있는 미래 적용 시작 월의 범위 등 남은 상세는 BR-012 OPEN이다.

2026-10-11 사용자 확정(지원→일반 정정의 지급 설정 기준 시점 질문의 1번, 답변 “1벙.”): 잘못된 수행 지점 때문에 지원 수업으로 기록했던 PT를 일반 PT로 정정할 때도, 기존 PT 진행 기록을 최초 생성한 시점에 적용되는 Trainer Rate/Fixed Amount를 사용한다. 최초 생성 시 Rate 50%, 정정 시 60%이면 50%를 적용하며 Fixed Amount도 같은 시점 기준이다. 실제 수업일이나 정정 시점 설정으로 대체하지 않는다. 최초 기록 때 일반 지급을 계산하지 않았어도 이 기준을 따른다.

이는 해당 입력 오류의 보상 정정 기준이며, 현재 설정 변경만으로 다른 과거 확정 지급을 재계산하지 않는다. 기존 기록/Pass 차감 유지·변경 전 사실/보상 이력 보존·중복 지급 금지·확정 월의 해제/정정/같은 월 재확정·이전 확정본 보존은 유지한다(BR-OPS-001/BR-PAY-012). 최초 생성 시점 설정을 확인할 근거가 필요하며 확인 불가 시 현재 설정으로 임의 대체하지 않는다. 설정의 시점/버전 조회·이력/스냅샷 저장·경합 처리 등 구체 방식은 Architecture 후속 설계(PROPOSED)다.

Traceability: 2026-09-17 사용자 최종 확정; PR-007/008; PD-009; BR-006 CLOSED.

W1/W2 후속: Trainer 과거 Home 오류로 바뀌는 기존 PT 분류는 BR-OPS-033의 Master Organization 전용 명시적 정정으로 같은 PT/차감·최초 생성 시각을 유지한다. 일반은 최초 기록 생성 시점 설정/기존 소비 Pass 발급 조건, 지원은 기존 관리자 Scope의 수동 추가실적이며 이전 보상 이력/유효 합계 단일 반영을 보장한다. 영향 건의 분류/보상·비용 정정 완료 전 해당 Trainer·월 확정/재확정은 BR-PAY-024로 차단한다. 기존 확정본 자동 변경 없이 필요한 월의 기존 권한/사유·해제/정정/같은 월 재확정·이전본 보존을 따른다. [W 승인](product-decisions.md#review-20261013-w-batch); V-124/125 미구성·미실행.

<a id="br-pay-012"></a>
## BR-PAY-012 — 정상 Session 등록 시 지급 결과 확정

Status: APPROVED

일반 Session Payment 적용 대상은 정상 Session 등록 시 지급액을 계산하고 확정한다. 타 지점 지원 수업은 진행 기록·Pass 차감을 먼저 완료하고 관리자의 건별 수동 금액 저장 시 Additional Performance 보상을 확정한다. 금액 미입력은 확정된 0원이 아니다. 월 정산의 Session 구성은 해당 기간의 유효한 확정 Session Payment를 집계하며 현재 Trainer 설정으로 재계산하지 않는다. Session 지급 결과 확정은 별도의 월 정산 마감 기능을 뜻하지 않는다. 오류 정정/취소의 허용 범위와 반영 상세는 BR-007에 남긴다.

일반/지원 구분은 실제 수업 당시 Trainer Home Branch와 Performed Branch를 비교한다(2026-10-11 사용자 확정, BR-OPS-001). 일반 PT의 Rate/Fixed Amount는 기존대로 기록 생성 시점 기준이며, 이 구분 기준으로 지급 설정을 수업 당시 값으로 바꾸지 않는다(BR-PAY-011).

Performed Branch 오류 정정은 기존 PT 기록/Pass 차감을 유지하면서 일반/지원 보상 방식도 바로잡고 잘못된 방식의 지급을 유효 집계에서 제외한다(2026-10-11 사용자 확정, BR-OPS-001). 지원→일반 전환의 Rate/Fixed Amount는 기존 PT 기록의 최초 생성 시점 기준으로 확정됐다(2026-10-11 사용자 확정, BR-PAY-011). 일반적인 신규 기록의 생성 시점 적용과 정정 대상 외 과거 지급의 불변성을 유지하며 설정 근거 확인/저장·나머지 정정 상세는 후속이다.

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

## 상품 변경 수용 사례 — BR-011 CLOSED

아래는 일반 Session Payment 적용 대상의 문서 기대 결과이며 실행된 테스트가 아니다. Pass 사용 가능 조건은 충족했다고 가정한다.

| 사례 | 입력/행위 | 기대 결과 |
| --- | --- | --- |
| 기존 Pass 보존 | 20회/1,000,000원/RATE로 발급한 Pass를 가진 회원. Catalog를 12회/1,200,000원/FIXED_AMOUNT로 수정, Trainer Rate 50% | 기존 Pass의 이후 진행은 1,000,000 ÷ 20 × 50% = 25,000원. 기존 발급 조건과 상품 수정 직전 잔여는 수정만으로 바뀌지 않음 |
| 새 Pass | 위 Catalog 수정 이후 별도 회원에게 새 Pass 발급, Trainer Fixed Amount 18,000원 | 새 Pass는 12회/1,200,000원/FIXED_AMOUNT 조건. 해당 Pass의 일반 지급은 18,000원 |
| Trainer 설정 변경 | 위 기존 RATE Pass를 사용하고 Rate 60% 저장 완료 후 새 PT 진행 등록 | 발급 조건은 유지하면서 1,000,000 ÷ 20 × 60% = 30,000원 확정. 과거 확정 25,000원은 유지 |
| 차감 순위 유지 | 기존 RATE Pass의 원본 Product를 FIXED_AMOUNT로 수정 | 기존 Pass의 우선순위 분류는 RATE 유지. 각 Pass의 발급 당시 Type으로 FIXED_AMOUNT 우선/FIFO 판단 |

## 남은 경계

Pass 상태·사용 조건·횟수 조정(BR-001/002, ARCH-003), 정정/취소(BR-007), 날짜·월 경계(BR-008), 입력값 검증(BR-010)은 남은 질문이다. Product 기준정보 변경의 기존 Pass 적용은 발급 당시 상품 조건 유지로 해결됐다(BR-011 CLOSED). Rate/Fixed Amount 적용 시점·등록 시 확정·BR-PAY-010 보상 권한·FIFO·RATE 올림은 확정이며 Architecture 공통 제약 검토는 가능하나 Branch 관련 상세 설계 확정은 MB-001–008의 Product 결정이 필요하다. 남은 세부사항은 관련 상세 설계 또는 구현 확정 전에 확인한다.

Architecture는 지급 설정 이력 또는 Session 계산 snapshot 등의 보존 방법을 검토한다. 이번 단계에서는 어느 방식도 선택하지 않으며 schema·API·기술을 설계하지 않는다.

## 추가 검증 CASE A–E

문서 수준에서 아래 결과가 BR-PAY-009/010과 요구사항·시나리오에 일치함을 검토했다. 애플리케이션 실행 시험은 아니다.

| CASE | 행위 | 기대 결과 및 근거 |
| --- | --- | --- |
| A | Master Admin이 Rate 50% → 60% 변경 | 과거 확정 25,000원 유지. 권한 있는 관리자 저장 완료 이후 새로 생성되는 Session에는 새 Rate 적용 |
| B | Master Admin이 Fixed Amount 20,000 → 25,000원 변경 | 과거 확정 Session Payment 20,000원 유지 |
| C | 관리자 권한 없는 Operator 또는 Trainer가 Trainer Rate 변경 시도 | 허용되지 않는 업무. 일반 운영자는 Rate/Fixed Amount 설정·변경 불가 |
| D | Master Admin이 Trainer Rate 변경 | 허용. 대상 Trainer·항목·변경 전후 값·변경자·시점을 감사 가능 |
| E | 과거 월 Monthly Settlement 재조회 | 해당 기간 유효한 Session Payment 결과 집계. 현재 Rate/Fixed Amount로 과거 지급액 재계산 금지 |

BR-PAY-009/010은 확정 규칙이며, open-questions.md의 BR-009(추가 통계)/BR-010(입력값 검증)과 다른 ID다.

## Product Baseline 추가 수용 사례

| CASE | 입력/행위 | 기대 결과 |
| --- | --- | --- |
| F | Rate 50%에서 60%로 Master Admin 저장 완료 후 Product A Session 신규 등록 | 등록 시 30,000원 확정; 기존 확정 25,000원 유지 |
| G | Fixed Amount 20,000원에서 25,000원으로 저장 완료 후 신규 등록 | 등록 시 25,000원 확정; 기존 확정 20,000원 유지 |
| H | 일반 운영자가 Rate/Fixed Amount 조회 시도 | 관리자 권한 없는 Operator·Trainer는 조회 불가; 관리자는 본인 포함 BR-PAY-010 대상 범위에서 허용 |
| I | 사용 가능한 RATE Pass가 가장 오래되고, FIXED_AMOUNT Pass F1이 F2보다 먼저 들어옴; 각 1회 잔여 | F1 → F2 → RATE 순서로 소비 |
| J | RATE 기초 계산액 12,300원인 Session 두 건 | 각각 13,000원 확정, 월 집계 26,000원; 월 원금 합계 24,600원을 올림한 25,000원이 아님 |
| K | FIXED_AMOUNT 설정 12,300원인 정상 Session | 12,300원 확정; 13,000원으로 올림하지 않음 |

현재 규칙은 Architecture 설계를 위한 Product Baseline이다. [인계 문서](architecture-handoff.md)를 따른다. 위 검증은 문서 수준이며 애플리케이션 실행 시험이 아니다.

<a id="br-ops-001"></a>
## BR-OPS-001 — 지점 관계·Context와 운영 이력

Status: APPROVED

Trainer는 한 시점에 Home Branch 하나에 소속되고 Branch에는 여러 Trainer가 있을 수 있다. Branch당 Trainer 한 명인 1:1이나 Trainer 동시 복수 소속 N:M을 요구하지 않는다. Member도 Home Branch 하나를 가지며 Pass는 Issued Branch 하나를 가진다. Trainer·Member·Pass는 허용된 조건에서 타 지점 PT 업무를 수행·이용할 수 있다. Session은 실제 Performed Branch를 식별하고 소속·발급 지점 변경으로 과거 수행 지점이 바뀌지 않아야 한다. Product는 Organization 공통 Catalog이며 지점별 가격 정책은 추가하지 않는다. Branch Admin은 하나의 Branch를 관리하고 일부 여러 지점만 담당하는 중간 관리자 역할은 추가하지 않는다.

특정 타 지점 Member/Pass/Session의 업무 이용과 그 Branch 전체 데이터 접근 권한은 구별한다. 구체 허용 조건은 MB-001/002/003/005 OPEN이며 기술 구현으로 대신 결정하지 않는다. Branch Scope는 Backend에서 강제한다. Trainer 일반 이동 Actor/저장 후 반영은 BR-OPS-013의 후속 Master 전용 승인과 기존 일관성 원칙을 적용한다. 변경 대상/과거 소속 이력 정정은 MB-001, 정산/비용 귀속 잔여 상세는 MB-010이며 Performed Branch 보존은 확정이다.

Trainer 직접 로그인·등록/조회, 개별 날짜 기록과 정상 Pass 차감은 유지한다. 일반 Session Payment 규칙의 적용 대상과 타 지점 보상 전체의 추가실적 처리를 구분한다(MB-009 CLOSED). 관리자 수동 횟수 조정은 사유와 이력을 남기며 Session 정정/취소에 따른 횟수 복원·이력·정산 일관성을 유지한다. 상세는 BR-002/007/013, 동시성·트랜잭션은 Architecture 결정이다.

2026-10-11 사용자 확정(타 지점 PT 진행 기록 정정·취소 담당 지점 질문의 1번): Master Admin은 Organization 전체, Branch Admin은 대상 기록의 실제 Performed Branch가 자신의 관리 Branch인 경우 PT 진행 기록을 정정·취소한다. 수원 소속 Trainer의 강남 수업 기록은 강남 Branch Admin이 담당하며, 수원 Branch Admin에게 Trainer Home Branch만을 근거로 해당 기록의 정정 권한을 부여하지 않는다. Trainer 이동만으로 기록의 담당 지점이 바뀌지 않는다. Backend에서 수업 사실·현재 관리 권한을 검증하며 요청의 Branch ID를 그대로 신뢰하지 않는다. 추가실적 금액 입력·보상 설정·Trainer 전체 월 정산의 기존 Home Branch 권한은 유지하고 수행 지점의 기록 권한으로 확대하지 않는다. Trainer 역할의 정정·취소 금지는 유지하며 관리자 겸임자는 해당 관리 권한으로 판단한다. Operator의 정정 권한·Performed Branch 자체 오류 정정·정산 확정 후 서로 다른 지점 담당자의 처리 순서·취소에 따른 지급/추가실적 연동은 잔여 OPEN이다.

2026-10-11 사용자 확정(확정 월의 타 지점 수업 취소 질문의 “11”을 1번으로 해석): 이미 확정된 해당 Trainer·월 정산은 현재 Home Branch 담당자의 해제 → 실제 Performed Branch 담당자의 PT 진행 기록 취소 → 현재 Home Branch 담당자의 같은 월 재확정 순서로 처리한다. Master는 Organization 범위에서 전체 흐름을 수행할 수 있다. 기록과 금액/월 정산의 기존 권한·이전 확정본/이력·해제 사유/감사·재확정 조건을 유지하며 수행 지점에 다른 소속 Trainer의 금액/전체 정산 권한을 추가하지 않는다. 취소 시 지급/추가실적 연동과 잔여 복원의 나머지 예외·구체 단계 계약은 BR-007/009/013 및 Architecture의 잔여 항목이다. 상세 근거는 PD-010/PR-009를 따른다.

2026-10-11 사용자 확정(Operator의 PT 진행 기록 정정·취소 권한 질문의 1번): Operator 역할만으로는 PT 진행 기록을 정정·취소할 수 없다. 정산 미확정/확정 상태 모두 적용한다. Master Admin은 Organization 전체, Branch Admin은 해당 기록의 실제 Performed Branch 범위에서 담당한다. Trainer 역할의 정정·취소 금지와 관리자 겸임자의 해당 관리 권한 판단은 유지한다. Operator의 기존 허용 업무가 정정 권한을 부여하지 않으며 Branch Scope 부여·다른 운영 업무의 상세는 MB-004/ARCH-001 OPEN이다.

2026-10-11 사용자 확정: 허용된 PT 진행 기록 취소는 그 수업 보상의 추가실적 자동 무효 처리를 동반한다. 유효 월 정산/지점 비용에서 제외하되 기존 금액·이력을 보존하고 다른 추가실적은 유지한다. 기존 기록 취소 권한과 Home Branch 기준 금액 입력/전체 정산 권한은 구별하며 확정 월의 기존 해제 → 취소 → 같은 월 재확정 순서를 따른다. 상세 근거는 BR-PAY-015/PD-027. 나머지 정정/취소·복원 예외 및 계약/원자성/동시성은 후속 대상이다.

2026-10-11 사용자 확정(수업 지점 자체 오류 정정 담당자 질문의 1번): PT 진행 기록의 Performed Branch 오류 정정은 Master Admin만 담당한다. Branch Admin은 기존 기록의 지점이나 실제 수행 지점이 자신의 관리 Branch여도 해당 지점 값을 정정할 수 없다. 일반 정정/취소의 수행 지점 기준과 Operator/Trainer 역할의 금지는 유지한다. Master의 Organization 범위와 원본/변경 이력 보존 원칙을 따른다. 소속·발급 지점 변경으로 과거 수행 지점을 자동 변경하지 않는 기존 규칙도 유지한다. 이번 결정은 담당 권한에 한정하며 정정 방식·확정 월 연계·일반/지원 수업 구분에 따른 보상 전환·적용 설정 시점은 BR-007/009/013 및 MB-005의 잔여 OPEN이다.

2026-10-11 사용자 확정(일반 PT/타 지점 지원 수업의 소속 기준 시점 질문의 1번): 실제 수업 당시 Trainer Home Branch와 실제 Performed Branch가 같으면 일반 PT, 다르면 타 지점 지원 수업으로 구분한다. 수원 소속일 때 강남에서 수행한 수업은 이후 강남으로 이동한 뒤 등록해도 지원 수업이며, 보상 전체를 관리자 수동 추가실적으로 처리하고 일반 Session Payment와 중복 지급하지 않는다. 늦은 등록이나 이후 소속 이동만으로 구분을 바꾸지 않는다.

수업 구분의 실제 수행 시점과 일반 PT Rate/Fixed Amount의 기록 생성 시점(BR-PAY-011/012), 보상/월 정산 관리 권한의 각 처리 시점 현재 Home Branch는 별개다. 기록 정정/취소의 Performed Branch 기준·해당 지점 값 오류 정정의 Master 전용 권한도 유지한다. 당시 소속 확인 불가 시 현재 소속을 임의 대입하지 않으며, 일반 이동은 BR-OPS-013을 따르며 과거 소속 사실 확인 예외·소급 등록 범위·허용된 사실 정정에 따른 보상 전환/적용 설정 시점은 MB-001/005 및 BR-007/008/013의 잔여 OPEN이다. 소속 이력/스냅샷 저장과 계약은 Architecture 후속 설계다.

2026-10-11 사용자 확정(Performed Branch 오류 정정 방법 질문의 1번): Master Admin은 기존 PT 진행 기록을 유지한 채 실제 Performed Branch를 정정하고 변경 전후 사실과 이력을 남긴다. 지점 오류 정정을 위해 기록을 취소/재등록하지 않으며 기존 Pass 차감은 유지한다. 횟수 복원·재차감이나 Pass 재선택을 하지 않는다. 정정된 실제 수행 지점과 실제 수업 당시 Trainer Home Branch에 따라 일반 PT/지원 수업 구분 및 보상 방식도 바로잡는다. 정정 전 잘못된 방식의 보상 결과는 이력으로 보존하되 유효 정산/지점 비용에 중복 합산하지 않는다.

일반 PT로 바뀌면 일반 Session Payment 방식, 지원 수업으로 바뀌면 관리자 건별 수동 추가실적 방식을 적용한다. 지원 수업으로 전환할 때 기존 일반 지급액을 자동으로 추가실적 금액에 복사하지 않으며, 기존 수동 금액 입력·미입력과 0원의 구별·미입력 시 해당 Trainer/월 확정 차단을 따른다(BR-PAY-012/015). 이미 올바른 구분의 수업을 이후 Trainer 이동만으로 재분류/재계산하지 않는다. 이번 결정으로 지원→일반 전환 시 Rate/Fixed Amount를 원래 기록 생성 시점과 정정 시점 중 언제 기준으로 적용할지는 확정하지 않는다.

2026-10-11 사용자 일관성 지시 적용(확정 월 정정): 기존 보상 오류 정정과 동일하게 해당 Trainer/월 확정 해제 → 지점/보상 정정 → 같은 월 재확정 순서를 적용하며 이전 확정본·구성/금액·변경 이력을 보존한다. Master의 Organization 권한·수행 지점 정정 전용 권한과 기존 해제/정정 사유·감사 원칙을 따른다. Branch Admin의 지점 정정 권한을 추가하지 않는다. 정정할 지급 설정 기준 시점·당시 소속 확인 예외·나머지 정정 항목/기간과 구체 계약/상태 표현·실패/재시도/동시성은 후속 OPEN 또는 PROPOSED다.

2026-10-11 사용자 확정(PT 이용권의 타 지점 사용 사전 승인 질문의 1번): 같은 Organization 안에서는 기존 사용 가능 조건을 충족한 PT Pass를 발급 지점과 다른 Branch에서도 별도 사전 승인 없이 사용할 수 있다. 발급 지점 관리자나 Master의 교차 사용 승인 대기 단계를 두지 않는다. 예를 들어 수원 발급 Pass를 강남 수업에서 사용할 때 Issued Branch 차이만으로 사용을 막지 않는다. Issued Branch·Trainer/Member Home Branch는 이 이용만으로 바뀌지 않으며 실제 Performed Branch를 기록한다.

이 정책은 이용 지점에 따른 승인/제한을 해결한 것이며 잔여 > 0 등 이용권 사용 조건, 허용된 PT 업무의 Actor/Organization Scope, FIXED_AMOUNT 우선·동일 Payment Type FIFO는 유지한다. 동일 Organization에서 사용할 수 있는 Pass를 발급 지점별로 먼저 나눠 선택하는 우선순위를 추가하지 않는다. 특정 Member/Pass의 업무 이용 허용은 다른 지점 전체 회원 목록·개인정보·Trainer 보상 설정/전체 정산 접근 권한을 부여하지 않는다. 남은 Member/Pass 정보 조회·Actor의 교차 업무 범위는 MB-001/002/003/005, 상태/잔여 등 사용 가능 조건의 나머지 상세는 BR-001/002·ARCH-003 OPEN이며 기술 설계로 대신 정하지 않는다.

Traceability: PD-001/002/004/007/010/012/022; PR-002/003/005/006/008/010/020/027/029/030.

## Multi-Branch 문서 수용 사례

| CASE | 행위 | 기대 결과 |
| --- | --- | --- |
| MB-A | Branch A Admin이 Branch B Member ID로 조회·수정 시도 | 허용되지 않은 접근은 Backend에서 금지. 특정 교차 업무 조건은 MB-002/005이며 전체 목록 접근을 자동 허용하지 않음 |
| MB-B | Branch Admin·Operator·Trainer가 보상 설정 조회·변경 시도 | Branch Admin은 본인 포함 자기 Branch 소속 Trainer만 허용. 관리자 권한 없는 Operator·Trainer는 모두 불가 |
| MB-C | Trainer가 Smartphone으로 허용된 Member/Pass와 실제 Branch의 Session 등록 | 우선순위·FIFO·차감 유지. 일반 지급 대상과 MB-009 타 지점 보상 처리를 구분하며 후자는 진행 기록·차감 후 관리자의 건별 금액 저장 시 보상 확정. 미입력은 확정 0원과 구분하며 해당 Trainer·월 정산 확정을 차단. 추적 표현·정정 연동은 BR-013 OPEN. 자신의 Session 조회 가능, 지급 설정은 비노출 |
| MB-D | Master Admin이 Branch별 Settlement 확인 | 기본급·유효 Session Payment·추가실적 구분, 현재 설정 재계산 금지; 지점 귀속은 MB-010 |
| MB-E | Branch A Admin의 Settlement 접근 | 허용 Branch만 접근. 금액 노출은 MB-006 결정 전 일괄 허용하지 않음 |

문서 기대 결과이며 Backend·UI 실행 시험은 수행하지 않았다.

<a id="br-ops-002"></a>
## BR-OPS-002 — 실제 수업 단위와 동일 일자 복수 수업

Status: APPROVED

2026-10-11 사용자 확정(같은 회원의 하루 두 번 실제 PT 수업 질문의 1번): 같은 Member가 같은 날 실제로 서로 다른 PT 수업을 여러 번 받았다면 각 수업을 별도 PT 진행 기록으로 등록하고, 각 기록마다 사용할 Pass를 기존 우선순위로 선택하여 1회씩 차감한다. 회원당 하루 1회 제한을 두지 않으며 날짜가 같다는 이유만으로 별개 수업을 합치거나 거부하지 않는다. 오전/오후 두 수업 모두 허용 업무/이용권 사용 조건을 충족하고 같은 Pass의 잔여가 20회라면 기록 2개와 잔여 18회가 결과다.

일반 PT의 지급은 각 수업의 기존 계산/확정 규칙을 따르고, 지원 수업은 기존 관리자 건별 수동 추가실적/미입력 정산 확정 차단을 따른다. 같은 실제 수업의 재전송/중복 클릭은 별개 수업이 아니며 추가 차감/지급을 만들지 않아야 한다(NFR-002/003). 실제 수업 구별과 요청 재시도 식별·충돌/수명/동시성의 구체 계약은 Architecture 후속 설계(PROPOSED)다. 시간대·소급 등록 범위·월 경계는 BR-008 OPEN이며 수업 시간 입력이나 일괄 등록 UI를 이번 결정으로 확정하지 않는다.

Traceability: PD-008; PR-008; BR-PAY-006/012/015; BR-008; 2026-10-11 사용자 1번 답변.

2026-10-12 I3=1: v1은 실제 수업별 개별 등록이며 여러 날짜 일괄 입력은 후속으로 보류한다(UX-001 CLOSED). 같은 날 실제 별개 수업 각각 허용/1회 차감과 같은 요청 재전송의 추가 차감/지급 방지, Responsive Smartphone 등록은 유지한다. 월 합계 입력/이전 월 복사로 대신하지 않는다. [2026-10-12 I 일괄 승인](product-decisions.md#review-20261012-i-batch).

<a id="br-ops-003"></a>
## BR-OPS-003 — Trainer의 과거 수업 직접 등록

Status: APPROVED

2026-10-11 사용자 확정(Trainer의 과거 수업 등록 범위 질문의 1번): Trainer는 해당 Trainer·실제 진행 월의 정산이 미확정이면 기존 Allowed PT Scope 안에서 자신이 실제로 진행한 과거 수업을 직접 등록할 수 있다. 당월 수업으로 제한하거나 월이 바뀌었다는 이유만으로 관리자 대행을 요구하지 않는다. 예를 들어 10월에 누락된 9월 수업을 발견했으며 9월 정산이 미확정이면 직접 등록할 수 있다. 같은 조건의 미확정 과거 월에 별도의 최근 N일/당월 제한을 추가하지 않는다.

해당 수업의 실제 진행일과 시스템 기록 시점은 구별한다. 일반/지원 구분은 실제 수업 당시 Home Branch와 Performed Branch, 신규 일반 지급 설정은 기록 생성 시점 Rate/Fixed Amount를 따른다(BR-OPS-001, BR-PAY-011/012). 기존 Member/PT 업무 권한·Pass 사용 조건/우선순위·1회 차감·지원 수업 수동 보상/미입력 월 확정 차단을 유지한다. 미확정 월이라는 조건만으로 다른 Member/Branch 정보에 접근하거나 잔여 부족 등 사용 조건을 면제하지 않는다. 수업 당시 발급 및 수동 만료 전 사용 가능 Pass의 늦은 등록 조건은 BR-PAY-006/BR-OPS-004를 따른다. 나머지 사용 조건/사실 확인·교차 업무 범위는 BR-001/002·MB-001/002/003/005의 잔여 게이트다.

Trainer 역할만으로 월 정산을 해제/재확정하거나 확정본을 자동 변경할 권한을 부여하지 않는다. 이미 확정된 월은 기존 관리자 확정 해제 → 누락 기록 반영 → 같은 월 재확정/이전 확정본 보존 원칙과 연계한다(기존 보상 오류/누락 정정의 사용자 일관성 지시 적용). 권한 있는 관리자가 해제하여 미확정이 된 월의 등록도 기존 Allowed PT Scope와 위 조건을 다시 검증한다. 실제 수업 사실·과거 소속 확인, 시간대/월 경계와 월 확정 경쟁/실패·구체 계약/저장/UoW는 후속 설계이며 이번 승인으로 구현 완료 처리하지 않는다.

2026-10-12 사용자 확정: 과거 수업의 Pass 후보는 실제 수업 당시 이미 발급된 이용권만 포함한다(BR-PAY-006). 수업 후 발급된 Pass는 제외한 뒤 기존 사용 조건과 우선순위를 적용한다. 신규 기록 생성 시점 지급 설정 및 실제 수업 당시 소속 기준 구분과 별개의 시간 기준이다.

2026-10-12 사용자 확정: 수동 만료 전에 실제 진행했고 당시 Pass가 사용 가능했다면 현재 만료 상태여도 기존 권한·정산·현재 잔여 조건을 충족하여 늦게 등록할 수 있다(BR-OPS-004). 별도 만료 해제 없이 후보 선택/1회 차감하며 현재 만료 상태·이력은 유지한다. Trainer의 기존 Allowed PT Scope/미확정 월 조건을 면제하거나 만료 해제·정산 해제 권한을 추가하지 않는다.

2026-10-12 사용자 확정(담당 교체 전 수업의 누락 등록 질문의 1번): A가 담당으로 실제 수업을 진행한 뒤 담당이 B로 바뀌어도 A는 교체 전 본인 수업을 직접 늦게 등록할 수 있다. 예: 9월 5일 A 수업 → 9월 6일 B로 담당 교체 → 9월 7일 A 누락 등록. 실제 수업 당시 A의 담당 관계와 본인 수행 사실, 현재 검증된 Caller/Trainer 연결·Organization 및 기존 Pass/정산 조건을 확인한다. 현재 담당이 B라는 이유만으로 관리자 대행이나 A 재배정을 요구하지 않는다. 이 허용만으로 A의 해당 회원 목록/상세·전화번호/다른 Pass·다른 Trainer 기록 조회 권한을 복원하지 않는다(BR-OPS-003/005/008, PD-008, PR-008/029/030).

기존 등록/지급 규칙 적용: 해당 Trainer A/실제 수업 월이 미확정이면 당월/최근 N일 제한 없이 처리한다. 확정 월은 Trainer가 해제할 수 없으며 기존 관리자 해제 → 누락 반영 → 같은 월 재확정·이전 확정본 보존을 따른다. 수업 당시 이미 발급되고 사용 가능했던 Pass 후보·현재 잔여 > 0·FIXED_AMOUNT 우선/동일 Type FIFO와 정상 1회 차감을 유지하며, 과거 담당 관계를 근거로 특정 Pass를 고정 선택하거나 잔여 조건을 면제하지 않는다. 수동 만료 전 사용 가능했던 수업의 늦은 등록은 사전 만료 해제 없이 현재 만료 상태/이력을 유지하는 기존 예외를 따른다. 실제 수행 Trainer는 A로 기록하고, 일반/지원 구분은 실제 수업 당시 A Home Branch와 Performed Branch, 신규 일반 지급 설정은 등록 시점 A의 Rate/Fixed Amount를 사용한다. 현재 담당 B의 보상 설정을 사용하거나 기존 확정 지급을 재계산하지 않는다. 지원 수업의 관리자 수동 추가실적/미입력 월 확정 차단도 유지한다(BR-PAY-006/011/012/015, BR-OPS-001/003/004).

인가 경계: 이 결정은 교체 전 담당 기간에 실제 수행한 본인 수업의 누락 등록에 한정한다. 과거 한때 담당했다는 이유만으로 교체 후 새 수업·담당이 아니던 기간·다른 Trainer 수업까지 등록할 수 없다. 별도의 현재 담당/개별 지원/관리 권한은 각 기존 규칙으로 독립 판단한다. Backend는 검증된 현재 Caller의 본인 Trainer 연결·Organization와 과거 담당/수업 대상 사실을 확인하며 클라이언트가 보낸 수행 Trainer/Member/Pass/진행일·과거 담당 표시만으로 인가하지 않는다. 허용된 명령을 위한 최소 대상 식별/과거 사실 확인·응답 경로는 후속 Architecture에서 설계하고 회원 목록/상세·전체 전화번호/다른 Pass 원본 공개로 확대하지 않는다. 권한 없는 요청·미해제 확정 월·잔여 부족 등 거부/실패 시 Pass·담당 관계·PT/지급·정산 이력에 일부 변경을 남기지 않는 기존 원칙을 따른다. 담당 이력/실제 수업 사실 확인 불가·충돌/정정·동일 시점 순서, 최소 정보/명령 계약·저장/UoW·중복/재시도·담당 변경/월 확정 경합은 후속이며 현재 담당이나 요청 주장으로 과거 사실을 임의 대체하지 않는다.

Traceability: PD-002/008/012; PR-008/010/029; BR-PAY-011/012/015; BR-008; 2026-10-11 사용자 1번 답변.

비활성 Trainer의 누락 수업(2026-10-12, BR-OPS-015): 비활성 전 실제 수행한 미등록 수업은 관리자 대행 경로를 허용한다. Trainer 비활성/계정 상태를 복구하거나 현재 Pass 담당을 되돌리지 않으며 실제 수행자/수업일·기존 Pass/생성 시점 지급/해당 진행 월 정산 조건을 유지한다. 비활성 Trainer 직접 등록 권한의 예외를 부여한 것이 아니다. 대행 인가의 현재 사실 검증·과거 사실/시점 판정과 구체 계약/저장/경합은 후속이다.

2026-10-13 P1/P2=1: 개별 지원의 과거 본인 수업 등록도 BR-OPS-027에 따라 허용한다. 현재 유효 지원으로 지정 전 실제 수업을 등록할 수 있고, 해제 후에는 실제 허용 기간의 본인 수업만 늦게 등록할 수 있다. 지정/해제 이력은 소급 변경하지 않고 해제된 Member 일반 조회/전화번호는 복원하지 않는다. 현재 계정/Trainer·실제 수행/허용 사실과 기존 Pass/잔여/정산 검증은 유지하며 담당 교체 전 수업 예외와 별도 근거로 판단한다. [P 승인](product-decisions.md#review-20261013-p-batch); V-112/113 미구성·미실행.

<a id="br-ops-004"></a>
## BR-OPS-004 — 이용권의 수동 만료

Status: APPROVED

2026-10-12 사용자 확정(이용권 유효기간 질문의 직접 답변): PT Pass에 별도 만료일/유효기간을 두지 않으며 시간 경과로 자동 만료시키지 않는다. 대신 권한 있는 관리자가 필요할 때 이용권을 수동 만료 처리할 수 있다. 수동 만료는 해당 Pass의 추가 이용을 종료하는 업무이며, 만료 이후 실제로 진행한 새 수업의 차감 후보로 사용할 수 없다. 기존 Member/Pass 관계·Organization/관리 Scope 검증을 생략하지 않는다.

종료 Pass와 과거 수업/차감·지급/정산 이력 보존 원칙을 따른다(PD-007/011). 이용권 만료만으로 기존 PT 진행 기록을 취소하거나 이미 확정된 보상을 현재 설정으로 재계산하지 않는다. 기존 수동 운영 변경의 사유·이력/감사 원칙을 동일 적용한다(2026-10-11 사용자 일관성 지시): 사유·대상 Pass·변경 전후 사용 상태·처리 Actor/Role·Branch Context·처리 시점을 추적한다. 구체 감사 저장 계약은 Architecture 후속이다.

수동 만료 전 사용 가능했던 수업의 지연 등록은 아래 확정 정책을 따른다. 나머지 상태/시점 사실 확인과 수업 취소 시 복원/재사용 연계는 BR-001/002/007·ARCH-003의 잔여 OPEN이다. 수동 만료의 해제는 아래 2026-10-12 확정 정책을 따른다. 수동 만료와 다른 종료 사유의 구분·상태 저장/계산 및 상태값 이름을 이번 결정으로 확정하지 않으며 휴회 기능을 추가하지 않는다.

2026-10-12 사용자 확정(지점 관리자의 만료 처리 범위 질문의 1번): Master Admin은 Organization 전체 Pass, Branch Admin은 자신의 현재 관리 Branch에서 발급한 Pass만 수동 만료 처리할 수 있다. Branch Admin의 기준은 Pass Issued Branch이며 Member/Trainer Home Branch나 수업 Performed Branch가 아니다. 수원 발급 Pass를 강남 소속 Member가 보유하거나 강남에서 사용해도 만료 담당은 수원 Branch Admin 또는 Master다. 회원 소속 변경/타 지점 이용만으로 해당 발급 지점 기준을 바꾸지 않는다.

Backend는 처리 시점의 검증된 Actor 관리 권한/Organization Scope와 Pass의 실제 Issued Branch를 확인한다. 요청의 role/Branch ID·이전 관리 지점·발급 Actor였다는 사실만으로 권한을 인정하지 않으며 범위 밖 직접 Pass ID 요청도 거부한다. 타 지점 Pass 사용 허용은 그 지점 관리자의 만료 권한이나 다른 지점 전체 자료 접근으로 확장되지 않는다. 관리자 권한 없는 Operator/Trainer에게 수동 만료 권한을 부여하지 않는다. 기존 만료 사유/이력·감사·과거 수업/지급/정산 보존 원칙을 유지한다. 이번 범위 확정은 수동 만료에 관한 것으로 Pass 발급/횟수 조정 등 다른 관리 업무의 잔여 정책을 임의 확정하지 않는다.

2026-10-12 사용자 확정(수동 만료 시 잔여 횟수 처리 질문의 1번): 이용권 수동 만료 자체로는 Remaining을 변경하지 않고 사용만 차단한다. 만료 직전 잔여가 5회면 만료 직후에도 잔여 5회를 조회할 수 있어야 한다. 만료 때문에 잔여를 0으로 덮어쓰거나 소멸 차감하지 않으며 PT를 실제로 사용한 횟수로 처리하지 않는다. 만료 처리와 기존 횟수 조정/수업 차감·복원은 구별한다.

잔여가 양수라는 사실만으로 해당 이용권이 사용 가능한 것은 아니다. 기존 수동 만료에 따른 사용 종료를 유지하며 잔여가 남았다는 이유로 자동 재개하지 않는다. Master Organization 전체/Branch Admin 현재 관리 Branch=Issued Branch, 사유/이력·감사 및 과거 수업/지급·정산 보존 원칙은 유지한다. 수동 만료의 해제는 아래 확정 정책을 따른다. 수동 만료 전 사용 가능했던 수업 지연 등록은 아래 확정 정책을 따른다. 별도 허용된 수업 취소·횟수 조정과 만료 상태의 연계 및 시점/이력 판정 상세는 여전히 후속이다. 다른 종료 사유의 잔여 처리까지 이번 결정으로 확정하지 않는다.

2026-10-12 사용자 확정(잘못 만료한 이용권의 복구 질문의 1번): 권한 있는 관리자는 같은 Pass의 수동 만료를 해제할 수 있다. 해제는 Master Admin의 Organization 전체 또는 Branch Admin의 처리 시점 현재 관리 Branch=Pass Issued Branch 범위에서 허용한다. 기존 만료 처리와 같은 관리 권한/사유·이력 원칙을 적용하며 별도 승인 대기를 추가하지 않는다(2026-10-11 사용자 일관성 지시 적용). 해제 사유와 대상 Pass·전후 사용 상태·처리 Actor/Role·Branch Context·처리 시점을 남기고 기존 만료 이력을 보존한다. 해제 자체로 Remaining을 변경하거나 새 Pass/횟수를 부여하지 않는다. 잔여 5회는 해제 후에도 5회이며, 만료/해제 반복만으로 횟수가 늘지 않는다.

만료 해제 후에는 잔여 > 0 등 기존 사용 조건을 충족할 때 같은 Pass를 다시 사용할 수 있다. 잔여 0회이거나 다른 사용 조건을 충족하지 못하면 해제만으로 차감 가능해지지 않는다. Backend는 해제 요청마다 현재 관리 권한과 대상 Issued Branch를 확인하며 관리자 권한 없는 Operator/Trainer·범위 밖 직접 ID/위조 Scope 요청은 거부한다. 기존 만료 사실·과거 수업/차감·확정 보상/정산 이력을 삭제하거나 해제만으로 재계산하지 않는다. 이번 결정은 수동 만료의 해제이며 다른 종료 사유나 휴회 기능의 재개를 허용한 것이 아니다. 수동 만료 전 사용 가능했던 수업의 지연 등록은 아래 확정 정책을 따른다. 별도 수업 취소·횟수 조정과 만료 상태의 연계 및 구체 상태/시점 판정·저장/경합 처리는 후속이다.

2026-10-12 사용자 확정(만료 전에 진행한 수업의 늦은 등록 질문의 1번): 실제 수업이 Pass의 수동 만료 전에 진행됐고 그 당시 해당 Pass가 사용 가능했다면, 현재 수동 만료 상태여도 기존 권한·정산·잔여 조건을 충족하여 늦게 등록할 수 있다. 9월 20일 수업 → 9월 30일 수동 만료 → 10월 5일 누락 등록 사례에서 수업 당시 사용 가능했던 Pass는 후보에서 제외하지 않는다. 등록을 위해 먼저 만료를 해제하거나 발급 지점 관리자의 별도 해제를 받을 필요는 없다. 기존 PT 업무 권한으로 처리하며 만료/해제 전용 관리 권한을 부여하는 것은 아니다.

수업 당시 이미 발급됐고 사용 가능했던 사실을 확인한 후보 안에서 기존 FIXED_AMOUNT 우선·동일 Payment Type FIFO를 적용한다(BR-PAY-006). 현재 수동 만료라는 이유만으로 위 조건의 후보를 제외하지 않되 이후 발급된 Pass·현재 잔여 0 등 다른 부적격 후보는 포함하지 않는다. 선택된 Pass의 현재 Remaining에서 정상 수업 1회당 1을 차감하며, 예를 들어 현재 만료/잔여 5회면 누락 수업 1회 등록 후에도 만료 상태인 채 잔여 4회다. 이것은 실제 수업의 차감이며 만료/해제 자체의 잔여 불변 규칙과 구별한다. 현재 만료 상태/기존 만료 이력을 유지하고 자동 해제·새 Pass 발급·과거 기록 삭제를 하지 않는다.

해당 Trainer/실제 진행 월 미확정 조건과 기존 Allowed PT Scope를 유지한다. 확정 월은 기존 관리자 확정 해제 → 누락 반영 → 동일 월 재확정·이전 확정본 보존을 따른다(BR-OPS-003). 일반/지원 구분은 실제 수업 당시 소속/수행 지점, 신규 일반 지급 설정은 기록 생성 시점 Rate/Fixed Amount, 지원 수업은 기존 수동 추가실적 처리다. 기존 지급/확정본을 자동 재계산하지 않는다. 이번 결정은 수동 만료 전 사용 가능했던 수업의 늦은 등록이며 다른 종료 사유의 이용 조건을 확정하지 않는다. 수업/발급/만료 시점 사실 확인·동일 시점 순서/정밀도·만료/해제 반복 이력의 판정, 별도 취소 복원/횟수 조정 및 계약/저장/동시성 상세는 관련 게이트의 후속이다.

Traceability: PD-007/011; PR-003; BR-001/002/007·ARCH-003; 2026-10-12 사용자 “만료일은 따로 없지만 관리자가 만료 처리가능하도록.”

2026-10-13 M1=1: 잘못 발급한 미사용 Pass는 기존 수동 만료로 잔여·원본 이력을 보존한 뒤 올바른 Pass를 새로 발급한다(BR-OPS-025). 별도 Pass 발급 취소 기능은 v1 제외이며 PT 진행 취소/잔여 복원과 구별한다. 만료·해제의 기존 Issued Branch 기반 관리자 인가/사유·감사·잔여 유지, 새 발급의 별도 기존 권한/대상/상품/활성 담당 조건은 유지한다. M2=1로 수동 만료만으로 현재 담당 Trainer의 허용 Member/전화번호 조회를 차단하지 않는다(BR-OPS-005). 만료 후 실제 새 수업 차단/만료 전 누락 수업의 기존 예외는 그대로다. [M 승인](product-decisions.md#review-20261013-m-batch).

<a id="br-ops-005"></a>
## BR-OPS-005 — Trainer의 회원 검색·조회 대상

Status: APPROVED

2026-10-12 사용자 확정(Trainer의 회원 검색·조회 범위 질문의 1번): Trainer 권한의 회원 검색·조회 대상은 본인 담당 회원과 개별 허용된 지원 수업 대상 회원이다. 담당 회원은 본인이 Assigned Trainer(담당 Trainer)로 지정된 Pass의 Member를 뜻한다. 같은 Home Branch 소속이라는 사실만으로 지점 전체 회원을 조회할 수 없으며 Organization 전체 조회도 허용하지 않는다. 지원 대상은 해당 Trainer와 해당 Member의 개별 허용 사실로 판단하고 타 지점 수업/Pass 교차 사용 가능이라는 일반 정책만으로 다른 회원 전체를 허용하지 않는다.

Backend는 목록·검색·개별 Member ID 상세마다 검증된 Caller의 Trainer 연결/Organization Scope와 대상에 대한 담당 관계 또는 개별 지원 허용 사실을 확인한다. 클라이언트의 Trainer/Member/Branch ID·role/지원 표시나 Frontend 필터만으로 권한을 부여하지 않는다. 같은 지점과 타 지점 모두 미담당/미허용 회원은 Trainer 검색·목록·상세 대상에서 제외한다. 회원 대상 조회 허용이 모든 Pass/다른 Trainer의 PT 내역·민감정보/보상 설정의 무제한 열람이나 등록·정정·취소·발급 권한을 뜻하지 않는다. 실제 수행 Trainer와 Pass 담당 Trainer를 구별하고 기존 PT/Pass 선택·차감·지급·정산 규칙을 유지한다.

관리자·Trainer 겸임자의 별도 관리 업무는 기존 Master Organization/Branch Admin의 허용된 관리 Scope로 판단하며 이번 Trainer 조회 범위로 승인된 관리 권한을 축소하거나 관리 권한 없이 확대하지 않는다. Trainer 역할만으로 Rate/Fixed Amount/Base Salary 조회·변경 불가 및 PT 기록 정정/취소·정산 확정 해제 권한 없음은 유지한다. 회원 검색·조회 대상 범위와 아래 확정된 전화번호 필드 공개를 구분한다. 기존 Pass의 담당 교체 허용/잔여·과거 이력 보존과 현재 담당 기반 조회 원칙은 BR-OPS-008의 후속 승인을 따른다. 교체 Actor/관리 Scope·대상 Trainer 지점·교체 전 본인 수업 누락 등록·잔여 0 담당 교체는 BR-OPS-008의 확정 기록을 따른다. 수동 만료 Pass의 담당 관계/교체는 M2/U1로 해결됐고 다른 상태 조합·과거 담당/수행 사실과 선택 잔여 필터의 다른 종료 상태별 잔여 정의/집계, 지원 허용의 지정·해제 절차 및 소속 이동의 권한/시점·이력, 전화번호 외 공개할 회원/Pass/PT 정보 항목과 실제 수업 등록의 나머지 교차 조건은 MB-001/002/003/005·ARCH-001·LEGAL-001 후속이다. 지원 허용은 기존 발급 지점의 Pass 사용 사전 승인 없음과 구별하며 발급 지점 승인 절차를 추가하지 않는다. 구체 권한 저장/모듈 계약/조회 일관성은 Architecture 후속이다.

2026-10-12 사용자 확정(지원 대상 지정 권한 질문의 1번): Trainer에게 개별 Member를 지원 수업 조회 대상으로 지정하는 권한은 Master Admin에게 Organization 전체, Branch Admin에게 지정 처리 시점 현재 관리 Branch가 해당 Member의 현재 Home Branch인 경우만 허용한다. 회원 정보를 관리하는 지점이 기준이며 Trainer Home Branch·수업 Performed Branch·Pass Issued Branch만으로 지정 권한을 얻지 않는다. 수원 소속 Member가 강남점에서 지원 수업을 받고 대상 Trainer도 강남 소속인 경우 수원 Branch Admin 또는 Master가 지정할 수 있으며, Member Home Branch를 관리하지 않는 강남 Branch Admin은 지정할 수 없다.

Backend는 지정 요청마다 검증된 Actor의 현재 관리 권한/Organization Scope와 실제 Member Home Branch, 대상 Trainer·Member의 Organization 관계를 확인한다. 이전 관리 지점·과거 회원 소속·직접 Trainer/Member ID·요청 role/Branch/지원 표시·과거 지정 Actor였다는 사실만으로 인가하지 않는다. 관리자 권한 없는 Operator/Trainer는 지정할 수 없다. 동일 Organization의 타 지점 Trainer를 지원 대상으로 삼는 것은 가능하되 지정 권한이 그 Trainer의 전체 프로필·Compensation Setting·추가실적 금액/월 정산 권한으로 확장되지 않는다. 지정은 해당 Trainer/Member 관계만 허용하며 양쪽 Home Branch나 Pass Issued/Performed Branch를 변경하거나 지점 전체 회원을 공개하지 않는다.

개별 지원 대상 지정은 권한 부여 중요 행위로 기존 NFR-004 감사 원칙을 적용하고 대상 Trainer/Member·변경 내용·Actor/권한·Branch Context·시점을 추적할 수 있어야 한다. 구체 감사 저장/공개 계약은 후속 Architecture다. 지정 Actor/관리 Scope·관리자 해제 전 유지 기간과 동일 관리 범위의 수동 해제는 아래 후속 결정까지 반영해 확정됐고, Member 이동 권한과 저장 완료 즉시 적용은 BR-OPS-007의 별도 후속 승인으로 확정됐으며 Master 전용 Trainer 이동의 대상/절차·과거 소속 사실 정정·Member/Trainer 이동 이력/정정·지정/해제 절차·대상 상태 조건과 최소 대상 Trainer 식별정보/전화번호 외 회원 공개 항목, 나머지 실제 PT 업무 인가는 후속이다. Pass 교차 사용에 발급 지점 사전 승인을 추가하지 않으며 개인정보 조회 허용과 기존 지급/정산 권한을 구별한다.

2026-10-12 사용자 확정(지원 대상 조회 허용 기간 질문의 1번): Trainer/Member의 개별 지원 조회 허용은 관리자가 해제할 때까지 유지한다. v1에서 고정 종료일이나 기간 경과에 따른 자동 종료·기간 연장 절차를 두지 않는다. 단순 시간 경과·월 변경·지원 수업 한 건 완료만으로 허용을 종료하지 않는다. 현재 Caller/Organization Scope와 유효한 담당 또는 지원 관계를 확인하는 기존 Backend 조회 인가는 계속 적용한다.

2026-10-12 기존 결정의 동일 기준 적용: 2026-10-11 사용자의 같은 기준 반복 질문 생략 지시와 승인된 지원 대상 지정 권한을 따라, 수동 해제도 Master에게 Organization 전체, Branch Admin에게 각 해제 처리 시점 현재 관리 Branch=Member 현재 Home Branch인 경우 허용한다. 이전 지정 Actor·과거 Member 소속·Trainer Home/Performed/Pass Issued Branch만으로 해제할 수 없으며 관리자 권한 없는 Operator/Trainer는 불가하다. Backend의 현재 관리 Scope·실제 Member/Trainer Organization 검증과 NFR-004 중요 권한 변경 감사를 동일 적용한다.

해제 성공 후 해당 지원 관계를 근거로 한 후속 회원 조회는 허용하지 않는다. 같은 Member에 대해 별도의 유효한 담당 관계나 관리자 관리 Scope가 있으면 그 권한은 별도로 판단한다. 조회 허용 해제로 기존 PT 기록·Pass 차감·지급/정산을 자동 취소하거나 변경하지 않는다. 동일 Organization의 Member/Trainer Home Branch 변경 후 기존 허용 유지는 아래 후속 결정에 따른다. 이동 자체의 권한/시점·이력, 다른 대상 상태/담당 관계 인정·필터의 다른 종료 상태별 잔여 정의·공개 필드·지정/해제 절차와 계약/저장/동시성은 후속이다.

2026-10-12 사용자 확정(회원 소속 지점 변경 시 기존 지원 조회 허용 질문의 1번): 동일 Organization 안에서 Member Home Branch가 변경되어도 기존 Trainer/Member의 개별 지원 조회 허용은 유지하며 이동만으로 자동 해제하거나 재지정을 요구하지 않는다. 이동 후 지정·수동 해제는 각 처리 시점 Member의 현재 Home Branch를 관리하는 Branch Admin 또는 Master가 담당한다. 수원 Member S가 강남으로 이동하면 기존 Trainer A/S 허용은 유지하고, 강남 Branch Admin/Master가 관리하며 별도 현재 관리 권한 없는 이전 수원 Branch Admin은 과거 지정 사실만으로 지정/해제할 수 없다.

2026-10-12 기존 결정의 동일 기준 적용: 2026-10-11 사용자의 같은 원칙 반복 질문 생략 지시를 따라 동일 Organization 안에서 Trainer Home Branch만 변경된 경우에도 동일 Trainer/Member의 개별 지원 조회 허용을 유지한다. 관계는 특정 Trainer와 Member 사이의 허용이며 Trainer의 새 소속 관리자에게 그 Member의 지정/해제 권한이 자동 생기지 않는다. 관리 기준은 계속 Member의 현재 Home Branch다.

조회 허용 유지가 현재 Caller/Organization Scope·대상 관계 검증을 면제하거나 타 지점 전체 회원/Pass/PT 정보·보상 설정/정산을 공개하지 않는다. 기존 지정/해제 감사 이력을 보존하며 이동만으로 Pass Issued Branch·과거 PT Performed Branch·차감/확정 지급·정산을 바꾸지 않는다. 일반/지원 보상 구분은 계속 실제 수업 당시 Trainer Home Branch와 Performed Branch로 판단한다. 이동의 권한/적용 시점·이력/정정·대상 비활성/계정 차단 등 다른 상태 조건과 잔여 0 외 담당 관계 인정/필터의 다른 종료 상태별 잔여 정의·공개 필드·절차·저장/동시성은 후속이다.

2026-10-12 사용자 수정 확정(잔여 0 회원 조회와 제외 필터): 본인이 담당한 이용권의 잔여가 모두 0이어도 그 사실만으로 담당 회원의 목록·검색·상세 조회를 차단하지 않는다. 기본 조회에는 잔여 0 회원도 포함하고 선택 기능인 “잔여 0인 회원 제외” 필터를 제공한다. 필터 미사용 시 포함/사용 시 해당 조건의 회원을 결과에서 제외하며 조회 권한이나 담당/지원 관계·회원 상태를 변경하지 않는다. Backend의 현재 Caller/Organization·담당 또는 개별 지원 관계 인가는 필터와 독립적으로 유지한다. 조회 허용이 Remaining > 0 등 기존 PT 등록/차감 조건을 면제하지 않는다. 여러 이용권의 잔여 집계 범위·개별 지원 회원 등 담당 이용권 없는 대상의 판정과 수동 만료/취소·담당 변경 등 다른 상태의 조회 영향/공개 필드는 후속이다(BR-OPS-005, PR-002/029/030, MB-001/003/005).

잔여 필터는 인가된 회원 결과를 좁히는 조회 조건이며 미담당/미허용 회원·다른 Organization을 공개하는 수단이 아니다. 필터를 끄거나 직접 Member ID로 요청해도 기존 인가를 재검증한다. 단일 담당 Pass Remaining 0인 Member M과 Remaining 1인 Member N이 다른 조건을 만족하면 기본 조회에는 둘 다 포함하며 제외 필터를 선택하면 M만 제외한다. M의 개별 상세 조회 권한과 본인 과거 PT 내역 조회는 기존 범위에서 유지한다. Remaining 0을 양수로 만들거나 Pass를 재발급/자동 조정하지 않으며 수동 만료의 양수 잔여를 0으로 덮어써 판정하지 않는다. 여러 Pass/지원 대상의 집계 범위는 아래 후속 결정을 따른다. 다른 종료 상태별 잔여 정의 및 필터 계약/페이징·집계 일관성은 후속이다.

2026-10-12 사용자 확정(잔여 제외 필터의 집계 기준 질문의 1번): “잔여 0인 회원 제외”는 조회 권한이 확인된 Member의 전체 이용권 잔여를 기준으로 판단한다. 조회 Trainer가 담당한 Pass만으로 제한하지 않으며 동일 Organization 내 다른 Trainer 담당/다른 Issued Branch의 Pass도 해당 Member의 집계 범위에 포함한다. 내 담당 Pass 0회+다른 Trainer 담당 Pass 10회인 Member는 필터를 켜도 표시하고 전체 집계 잔여가 0이면 제외한다. 개별 지원 회원도 자기 담당 Pass 존재 여부와 관계없이 같은 Member 전체 기준을 적용한다. 필터 미사용의 기본 조회/개별 상세 권한은 그대로이며 다른 회원/개별 Pass·다른 Trainer PT/보상 정보를 자동 공개하지 않는다. 집계 범위는 확정됐고 나머지 종료 상태의 잔여 취급·담당 변경/비활성·공개 필드 및 계약/저장/조회 일관성은 후속이다(BR-OPS-005, PR-002/029/030, MB-001/003/005).

집계 기준의 기존 결정 적용: 수동 만료 자체가 잔여를 바꾸지 않는 BR-OPS-004에 따라 만료 후 보존된 5회는 이 필터에서도 0회로 간주하지 않는다. 전체 집계가 5회이면 잔여 0 제외 조건으로 숨기지 않되, 현재 만료 Pass의 실제 PT 사용 제한은 그대로다. 조회 원천에서 보유 Pass 없음이 확인된 경우 합산할 잔여는 0회로 판정한다(확인된 빈 집합의 횟수 합계). 미조회/인가 실패·불완전한 잔여 사실을 빈 집합이나 0회로 대체하지 않는다. 필터 판단에 필요한 회원 단위 집계 사실을 사용하는 결정이며 전체 잔여 숫자/개별 Pass·다른 Trainer 정보의 화면 공개 항목을 일괄 승인한 것은 아니다. 수동 만료 외 다른 종료/취소 상태의 잔여 정의·집계와 전화번호 외 필드 공개는 해당 Product/LEGAL 게이트를 유지한다.

2026-10-12 사용자 확정(Trainer의 회원 전화번호 조회 질문의 1번): Trainer는 기존 조회 권한이 확인된 담당 회원과 개별 허용 지원 회원의 등록된 전체 전화번호를 조회할 수 있다. 부분 마스킹된 번호만 허용하는 정책으로 제한하지 않는다. 담당 Pass 잔여가 모두 0이어도 기존 회원 조회 권한이 유지되면 전화번호도 같은 범위에서 조회한다. Backend는 전화번호를 반환하는 조회마다 현재 Caller/Organization·담당 또는 지원 관계를 검증하고 미담당/미허용 회원·타 Organization 번호를 공개하지 않는다. 지원 해제 후 별도의 유효한 담당/관리 권한이 없으면 해당 번호도 공개하지 않는다. 관리자 겸임자의 별도 관리 Scope는 유지한다. 이번 승인은 전화번호 읽기이며 수정/일괄 내보내기·다른 개인정보/개별 Pass·다른 Trainer PT/보상 공개 권한을 추가하지 않는다. 전화번호 필수 수집/형식·중복/검증과 나머지 필드/보존·조회 계약은 후속이다(BR-OPS-005, PR-002/029/030, NFR-001/005, LEGAL-001).

전화번호 필드 공개도 기존 회원 조회 인가와 함께 Backend에서 강제한다. 같은 Home Branch·과거 지원/지정 Actor·직접 Member ID/요청 role·필드 선택이나 Frontend 표시 상태만으로 범위를 넓히지 않는다. 전화번호로 검색하는 경로가 제공되는 경우도 인가된 회원 집합 안에서만 조회하며 미인가 회원의 번호/존재를 응답으로 노출하지 않는다. 실제 전화번호를 문서/일반 로그에 복사하지 않는 기존 지침을 적용하고 검증 예시는 비식별 가상 데이터를 사용한다. 전화번호 필수 입력과 중복 허용은 BR-OPS-006의 별도 후속 승인을 따른다. 형식·검증·다른 항목/행위 권한·보존 기간/감사 조회 정책·구체 응답/저장 계약은 후속이다.

Traceability: PD-002/004; PR-002/008/029/030; MB-001/002/003/005·ARCH-001·LEGAL-001; 2026-10-12 사용자 1번 답변.

2026-10-12 후속 조회/교체 확정: 잔여 0으로 이용을 마친 Pass도 담당 교체 가능하며 새 현재 담당의 Member 기본 조회/허용 전화번호 읽기를 유지한다(BR-OPS-008). 선택 제외 필터는 여전히 Member 전체 Pass 잔여 기준이다. 이전 담당은 다른 현재 담당/지원/관리 근거가 없으면 과거 담당 사실만으로 회원 조회를 유지하지 않는다. 잔여 0 담당 교체는 실제 PT 사용/차감 허용이나 이전 Trainer의 전체 수업·보상 공개가 아니다. 수동 만료/취소 등 다른 종료 사유의 담당 관계 인정/교체는 별도 잔여 게이트다.

2026-10-13 M2=1: 수동 만료된 Pass만 담당해도 현재 유효한 Trainer는 그 Member와 기존 허용 전체 전화번호를 조회할 수 있다. 수동 만료 Pass를 현재 담당 관계의 조회 근거로 인정하고 만료만으로 관계를 자동 해제하지 않는다. 목록/검색/직접 ID마다 검증된 Caller·실제 Organization/현재 담당 관계 또는 개별 지원을 확인한다. Trainer 자체 비활성/계정 차단·역할 회수/폐기 AuthSession의 접근을 복구하지 않으며 담당 교체 후 이전 담당은 다른 현재 담당/지원/관리 근거가 없으면 조회하지 못한다. 보존된 만료 잔여는 기존 전체 Pass 기준 선택 필터에서 0으로 바꾸지 않는다. 조회가 만료 후 실제 새 수업 사용/차감을 허용하지 않으며 만료 전 실제 수업의 늦은 등록 예외는 기존 조건을 따른다. 다른 개인정보/개별 Pass·다른 Trainer PT/보상·수정/내보내기 권한과 수동 만료 Pass 담당 교체 허용을 추가하지 않는다. PR-002/003/029/030·NFR-001/005·MB-001/003; V-107 미구성·미실행; [M 승인](product-decisions.md#review-20261013-m-batch).

2026-10-13 O2=1: 개별 지원 허용의 업무는 기존 회원 조회와 해당 Trainer 본인의 실제 수업 등록을 포함한다. 본인 담당 Pass가 없어도 O1과 동일하게 그 Member 전체 적격 Pass에서 선택/차감하며 다른 담당자의 Pass도 포함한다(BR-OPS-026). 지정/해제의 현재 Member Home 관리자/Master Scope·자동 종료 없음·같은 Organization Home 이동 후 유지/감사는 유지한다. 개별 지원 허용을 보상의 일반/지원 분류나 무제한 Pass/PT/금액 공개·정정/취소/발급 권한으로 확대하지 않는다. 지원 지정 전 수업 및 해제 후 과거 수업 등록의 시간 경계는 별도 후속이다. [O 승인](product-decisions.md#review-20261013-o-batch); V-111 미구성·미실행.

2026-10-13 P1/P2=1 후속: 현재 유효한 지원 허용은 지정 전 실제 본인 수업 등록도 허용하고, 지원 해제 후에는 허용 기간에 실제 수행한 본인 수업의 늦은 등록만 허용한다(BR-OPS-027). 해제 후 일반 Member 목록/검색/상세·전화번호 접근을 복원하지 않는다. 기존 “해제 후 회원 조회 불가”와 제한된 과거 수업 등록 명령을 구별한다. 지정/해제 이력·현재 계정/Trainer·기존 Pass/정산·금액 비공개는 유지한다. [P 승인](product-decisions.md#review-20261013-p-batch); V-112/113 미구성·미실행.

U1 조회 관계 후속: 수동 만료 Pass 담당도 BR-OPS-008의 기존 Member 현재 Home 관리자 인가로 교체할 수 있다. 새 실제 활성 담당은 M2의 만료 담당 근거로 허용된 회원/전체 전화번호 조회를 이어가며 이전 담당은 다른 현재 유효 관계/권한 없이 일반 조회를 유지하지 않는다. 과거 본인 수업 늦은 등록과 그 최소 식별/인가·다른 Pass/PT/보상 기밀성은 별개로 유지하고 만료 해제/새 수업 사용 권한을 부여하지 않는다. [U 승인](product-decisions.md#review-20261013-u-batch); V-122 미구성·미실행.

<a id="br-ops-006"></a>
## BR-OPS-006 — 회원 전화번호 필수 입력

Status: APPROVED

2026-10-12 사용자 확정(회원 등록 시 전화번호 필수 여부 질문의 1번): 새 Member 등록을 완료하려면 전화번호를 반드시 입력해야 한다. 전화번호가 누락되거나 빈 문자열·공백만 있으면 등록을 완료하지 못한다. 임의 번호나 기본값으로 필수 입력을 대신하지 않는다. 이 결정은 전화번호 필수 입력이며 번호 중복 허용/금지·구체 형식/정규화·문자/본인 확인, 다른 개인정보 필수 수집이나 등록/수정 Actor 권한을 확정한 것은 아니다. 기존 Role·Data Scope와 Trainer의 인가된 담당/지원 회원 전체 전화번호 읽기는 유지한다(BR-OPS-006, PD-022, PR-002, NFR-005, LEGAL-001).

기존 사용자 일관성 지시 적용(2026-10-11): 일반 회원정보 수정에서도 필수 전화번호를 누락·빈 문자열·공백만인 값으로 지우는 변경은 허용하지 않는다. 전화번호를 변경하지 않는 다른 정보 수정에서는 기존 번호를 유지한다. 이는 등록 필수 요건을 일반 수정에 동일 적용한 것이며 전화번호 수정 권한을 새로 부여하거나 특정 API 입력 형태를 승인한 것은 아니다. 법적·운영상 필요한 개인정보 삭제/보존 예외는 LEGAL-001에서 별도 결정한다.

Frontend 입력 안내와 별개로 Backend도 등록/일반 수정의 필수 입력 조건을 강제한다. 필수 번호가 없는 요청을 성공한 회원 등록으로 확정하거나 기존 번호를 빈값으로 덮어쓰지 않는다. 전화번호의 정확성·소유를 문자 인증으로 확인해야 한다는 뜻은 아니다. 중복 허용은 아래 후속 사용자 승인으로 확정했다. 구체 형식·검증 정책, 다른 수집 항목·보존/삭제, Member 등록/정보 수정 권한 상세와 응답·저장/UoW 계약은 후속이다. Member 로그인은 계속 Future Scope다.

2026-10-12 사용자 확정(회원 간 전화번호 중복 허용 여부 질문의 1번): 같은 Organization의 여러 Member가 같은 전화번호를 사용할 수 있다. 가족 등 공유 연락처로도 각각 등록하며 전화번호가 같다는 이유만으로 신규 등록을 거부하지 않는다. Member는 전화번호와 별개의 고유 식별자로 구분한다. 동일 번호를 같은 회원으로 자동 병합하거나 Pass·PT 진행/지급 이력·담당/지원 관계를 공유하는 근거로 삼지 않는다. 전화번호 필수 입력과 기존 Role·Data Scope는 유지한다(BR-OPS-006, PD-022, PR-002, NFR-005, LEGAL-001).

기존 사용자 일관성 지시 적용(2026-10-11): 전화번호를 변경할 권한이 있는 Actor의 일반 수정에도 같은 중복 허용 원칙을 적용한다. 다른 Member가 이미 쓰는 번호라는 이유만으로 변경을 거부하지 않되 필수 번호 비움 금지와 현재 업무 인가는 그대로 적용한다. 이 결정으로 등록/수정 권한을 추가하지 않는다.

전화번호로 검색하는 경로가 제공되면 조회 권한이 있는 회원 집합 안에서 동일 번호의 회원을 각각 식별하고, 전화번호 일치만으로 한 명으로 단정하지 않는다. 미인가 회원의 존재·번호·지점이나 조회 권한을 중복 검사/검색으로 노출하지 않는다. 중복 허용은 별도 경고 화면·중복 회원 병합 기능·Member 로그인/본인 인증 승인이 아니며 번호 형식/정규화·다른 수집 항목·보존/필요 삭제 및 구체 응답·저장 계약은 후속이다.

Traceability: PD-022; PR-002; NFR-005; LEGAL-001; 2026-10-12 사용자 1번 답변 및 2026-10-11 사용자 일관성 지시.

2026-10-12 J1=1: 회원 등록/이름·전화번호 수정 Actor·Scope는 BR-OPS-021로 확정했다. 기존 필수 입력/중복 허용·별도 Member 식별과 일반 수정 필수값 유지·미인가 검색/개인정보 비공개를 유지한다. 형식/정규화·다른 항목/권한·계약·보존/삭제는 별도다. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch).

<a id="br-ops-007"></a>
## BR-OPS-007 — 회원 소속 지점 변경 권한

Status: APPROVED

2026-10-12 사용자 확정(회원 소속 지점 변경 권한 질문의 1번): 동일 Organization 안에서 Member의 Home Branch는 Master Admin 또는 변경 요청 처리 시점 Member의 현재 Home Branch를 관리하는 Branch Admin이 변경할 수 있다. 받는 지점의 별도 승인 없이 처리한다. Master는 Organization 전체 범위이며 Branch Admin은 변경 전 현재 관리 Member만 대상으로 한다. 받는 지점 관리자라는 이유나 과거 소속·이전 변경자/지원 지정자·Pass Issued Branch·수업 Performed Branch 사실만으로 다른 현재 소속 Member를 이동시킬 수 없다. 관리자 권한 없는 Operator·Trainer는 수행할 수 없고 관리자 겸임자는 해당 관리 권한으로 판단한다(BR-OPS-007, PD-004, PR-002/030, MB-002, NFR-001).

기존 결정 적용: 변경된 Home Branch가 반영된 이후의 Member 관리 및 개별 지원 지정/해제는 각 요청의 현재 Home Branch와 관리 Scope를 따른다. 이전 지점 관리자는 이전 소속/처리자라는 사실만으로 Home Branch 기반 관리 권한을 유지하지 않는다. 기존 담당·개별 지원 조회 허용과 별도의 Pass 발급 지점/수업 수행 지점 기준 업무 등 독립적으로 인가되는 권한은 각각 기존 규칙을 적용한다. 이동 자체로 개별 지원 허용을 해제/재지정하지 않고, Pass의 Issued Branch·발급 조건·잔여/담당 정보, Trainer Home Branch와 과거 PT 기록/Performed Branch·확정 지급/정산을 자동 변경하지 않는다(BR-OPS-001/004/005).

기존 사용자 일관성 지시 적용(2026-10-11): Member 소속 변경은 관리 Scope에 영향을 주는 중요 변경이므로 기존 중요 행위/인가 변경의 이력·감사 원칙을 적용한다. 대상 Member·변경 전후 Home Branch·변경 Actor/권한·Branch Context·시점을 추적한다. 이번 권한 승인이 감사 저장 구조나 이동 적용 시점·예약/소급·변경 사유 입력/정정 정책을 확정한 것은 아니다(NFR-004, MB-002).

Backend는 이동 요청마다 검증된 Caller의 현재 역할·Organization/관리 Scope와 서버의 Member 현재 Home Branch 및 대상 Branch의 동일 Organization 관계를 확인한다. 요청의 role·source/target branch_id·Member ID를 권한 근거로 신뢰하지 않는다. 이동 권한으로 다른 지점 전체 Member/Trainer/Branch 상세·보상 정보를 공개하지 않는다. Member 이동의 저장 완료 즉시 적용과 미래 예약 미지원은 아래 후속 승인으로 확정했다. 이동 대상은 활성 Branch만 허용하는 것으로 아래 후속 승인에서 확정했다. 지점 비활성화 자체의 나머지 업무 영향, 과거 소속 이력 정정/소급 상세와 최소 대상 Branch 조회·명령/저장/UoW·실패/재시도·동시성 계약은 후속이다. Trainer 소속 변경 권한이나 기존 IAM-001의 지점 조회 범위를 이번 결정으로 확대하지 않는다.

2026-10-12 사용자 확정(회원 소속 변경의 적용 시점 질문의 1번): v1의 Member Home Branch 변경은 저장 완료 즉시 적용만 지원한다. 변경이 성공한 시점부터 새 Home Branch가 현재 소속이 되며, 미래 적용일을 지정해 소속 변경을 예약하는 기능은 제공하지 않는다. 성공한 저장 이후 시작하는 후속 요청의 Home Branch 기반 관리 및 지원 지정/해제는 새 소속 기준으로 인가한다. 저장에 실패하면 변경 전 Home Branch를 유지한다. 기존 Master Organization 전체/변경 전 Member 현재 Home Branch 관리 Branch Admin 권한과 받는 지점 별도 승인 없음은 유지한다(BR-OPS-007, PD-004, PR-002/030, MB-002, NFR-001/004).

즉시 적용의 경계: 소속 변경 이력은 보존하며 기존 개별 지원 조회 허용을 해제/재지정하지 않는다. Pass Issued Branch·발급/잔여/담당 사실과 과거 PT/Performed Branch·확정 지급/정산은 소속 변경으로 자동 갱신하지 않는다. 이전 소속/처리자만으로 Home Branch 기반 관리 권한을 유지하지 않되, 담당/지원 조회나 발급/수행 지점 기준의 독립 업무 Scope는 각각 기존 규칙을 적용한다. 과거 소속 이력의 오류 정정·소급 여부/방식, 대상 Branch 상태 및 구체 저장/UoW·이미 처리 중인 요청과 동시 이동의 인가/실패 일관성은 후속이다. 이번 결정은 Member 이동 시점이며 Trainer 이동 시점이나 AuthSession 철회 구현/ADR-0004를 승인한 것은 아니다.

2026-10-12 사용자 확정(회원 이동 대상에 비활성 지점을 허용할지 질문의 1번): Member Home Branch의 이동 대상은 동일 Organization 안에서 운영 중인 활성 Branch만 허용한다. 비활성 Branch로의 이동은 허용하지 않으며 Master Admin과 Branch Admin에 동일하게 적용한다. Backend에서도 대상 Branch의 활성 여부를 검증하고 비활성 대상 요청은 거부한다. 거부 시 기존 Member Home Branch·지원 허용·Pass·과거 업무 이력은 유지한다(BR-OPS-007, PD-004, PR-002/030, MB-002/008, NFR-001).

대상 활성 조건의 범위: 기존 이동 Actor/현재 관리 Scope·받는 지점 별도 승인 없음·저장 완료 즉시 적용/미래 예약 미지원은 유지한다. 이번 결정은 새 이동의 대상 Branch 조건이며 Branch 비활성화 가능 조건, 비활성화 당시 기존 Member/Trainer/Pass 처리·자동 이동, 이미 비활성인 출발 지점의 업무 조건이나 재활성화/과거 조회 정책까지 확정한 것은 아니다. 과거 소속 이력 정정/소급·Branch 상태의 저장 표현, 이동과 비활성화의 경합·필수 감사/UoW/실패 계약은 후속이다(MB-002/008).

Traceability: PD-004; PR-002/030; MB-002/008; NFR-001/004; BR-OPS-001/004/005; 2026-10-12 사용자 1번 답변 및 기존 사용자 일관성 지시.

V1 후속: Member의과거 Home Branch 이력 오류 정정은 BR-OPS-032로 Master Organization 전용/사유 필수·원래 이력 보존이 확정됐다. 일반 Member 이동의 현재 Home Branch Admin 허용·즉시 적용/미래 예약 미지원과 구별한다. 과거 PT/지급/정산 자동 변경 없이 기존 영향 정정/재확정 절차를 유지하며 구체 정정/현재 사실 영향·상태/계약은 후속이다. [V 승인](product-decisions.md#review-20261013-v-batch); V-123 미구성·미실행.

<a id="br-ops-008"></a>
## BR-OPS-008 — 기존 이용권의 담당 Trainer 교체

Status: APPROVED

2026-10-12 사용자 확정(이용권의 담당 Trainer 교체 질문의 1번): 기존 PT Pass에서 Assigned Trainer를 교체할 수 있다. 20회권을 5회 사용한 뒤 담당 A를 B로 바꾸어도 같은 Pass의 잔여 15회와 과거 수업·지급 이력을 유지한다. 교체를 위해 기존 Pass를 취소하거나 새 Pass를 발급하는 절차를 요구하지 않으며 횟수를 복원/추가/재차감하지 않는다. 발급 당시 상품 가격·총횟수·Payment Type과 Issued Branch는 그대로이고 Member/Trainer Home Branch도 이 변경으로 이동하지 않는다. 과거 PT 기록의 실제 수행 Trainer·Performed Branch, 확정 Session Payment·추가실적/정산을 새 담당 기준으로 자동 재작성/재계산하지 않는다(BR-OPS-008, PD-007, PR-003).

기존 사용자 일관성 지시 적용(2026-10-11): 일반 담당 교체도 저장 완료 후 변경된 현재 담당을 적용하고 미래 예약 변경 절차를 추가하지 않는다. 중요 Pass/인가 관계 변경의 이력·감사 원칙에 따라 대상 Pass/Member·변경 전후 담당 Trainer·변경 Actor/권한·Branch Context·시점을 추적한다. 저장 실패 시 기존 담당과 잔여/이력을 유지한다. 저장/UoW·감사 구조·동시성 계약을 승인한 것은 아니다(NFR-001/004, BR-OPS-007/008).

기존 회원 조회 원칙 적용(BR-OPS-005): 담당 관계를 인정하는 Pass의 현재 담당이 바뀌면 후속 회원 목록/검색/직접 ID·전화번호 공개도 Backend에서 변경된 현재 담당 관계와 별도의 개별 지원/관리 권한으로 판단한다. 이전 담당이라는 사실만으로 영구적인 Member 조회 권한을 부여하지 않는다. 새 담당은 기존 담당 회원 범위에서 인가하며 이전 담당도 다른 담당 Pass나 개별 지원/관리 권한이 있으면 그 독립 근거로 판단한다. 본인이 실제 수행한 과거 PT 기록 조회는 기존 별도 업무 Scope를 따르고, 이를 다른 Member/Pass/PT·보상 설정의 무제한 공개로 확대하지 않는다. 잔여 0만으로 담당 회원 조회를 막지 않는 규칙도 유지한다.

2026-10-12 사용자 확정(담당 교체 권한의 기준 지점 질문의 1번): 기존 Pass의 Assigned Trainer 교체는 Master Admin의 Organization 전체 범위 또는 처리 시점 Member의 현재 Home Branch를 관리하는 Branch Admin에게 허용한다. 수원 발급 Pass의 회원이 현재 강남 소속이면 강남 Branch Admin 또는 Master가 교체할 수 있으며, 수원 Branch Admin은 Issued Branch만을 근거로 교체할 수 없다. 회원 소속이 다시 변경되면 각 교체 요청은 변경된 현재 Home Branch 기준으로 인가한다. 이용권 수동 만료/해제의 Issued Branch 기준은 그대로 유지한다(BR-OPS-004/008, PD-007, PR-003/030).

Backend는 검증된 현재 Caller의 관리자 권한/Organization·관리 Branch Scope, 실제 Pass→Member 관계와 Member 현재 Home Branch를 확인한다. 직접 Pass/Member ID·클라이언트 role/Branch/Member 소속 값·과거 소속/담당 또는 이전 처리 Actor·Trainer Home Branch·수업 Performed Branch만으로 교체 권한을 인정하지 않는다. 관리자 권한 없는 Operator/Trainer는 수행할 수 없으며 관리자·Trainer 겸임자는 해당 관리자 Scope로 판단한다. 권한 거부/실패 시 기존 담당·잔여/발급 조건·업무 이력을 유지한다. 기존 범위 내 관리자 직접 처리 원칙을 동일 적용하여 별도 Master 승인 대기를 추가하지 않는다(2026-10-11 사용자 일관성 지시 적용). 교체 권한은 대상 Trainer의 Compensation Setting 조회/변경 권한이나 다른 지점 전체 Trainer/Member 정보 열람 권한을 부여하지 않는다. 기존 즉시 적용·전후 담당/Actor/Branch Context·시점 이력/감사·현재 관계 기반 조회와 과거 수업/보상 보존 원칙은 유지한다.

2026-10-12 사용자 확정(교체할 Trainer의 소속 지점 질문의 1번): 기존 Pass의 담당 교체 대상은 같은 Organization의 Trainer이며 Member 현재 Home Branch와 다른 지점 소속 Trainer도 허용한다. 강남 회원의 담당을 수원 소속 Trainer로 바꿀 수 있다. Member와 같은 지점 소속이어야 한다는 제한을 두지 않으며 다른 Organization Trainer는 지정할 수 없다. 교체 요청의 Actor 권한은 기존대로 Master Organization 전체 또는 Branch Admin 처리 시점 Member 현재 Home Branch 기준이다(BR-OPS-008, PD-007, PR-003/029/030).

기존 규칙 적용(BR-OPS-001/005/008, BR-PAY-011/015): 담당 교체는 Assigned Trainer 관계만 바꾸며 Member/Trainer Home Branch·Pass Issued Branch·발급 조건/잔여와 과거 실제 수업/확정 지급·정산을 바꾸지 않는다. 후속 회원 조회는 현재 담당 관계와 별도 지원/관리 권한으로 인가한다. 실제 PT 업무의 Allowed PT Scope·Pass 사용 조건은 별도로 검증한다. 일반/지원 보상 구분은 실제 수행 Trainer의 수업 당시 Home Branch와 실제 Performed Branch를 비교한다. 수원 소속 Trainer가 강남 회원을 수원에서 지도하면 일반 PT, 강남에서 지도하면 지원 수업으로 기존 보상 규칙을 적용하며 담당 지정만으로 일괄 일반/지원 처리하지 않는다. 지원 수업은 해당 수업의 보상 전체를 관리자 입력 Additional Performance로 처리하고 일반 Session Payment를 중복 합산하지 않는다. 타 지점 Trainer를 담당으로 지정할 수 있어도 그 Trainer의 Compensation Setting·전체 정산/프로필이나 타 지점 전체 회원/Trainer 목록 열람 권한은 늘어나지 않는다. Backend는 대상 Trainer의 실제 Organization 관계도 확인하고 요청의 Trainer/Organization ID·지점 값만으로 신뢰하지 않으며 범위 밖 요청 거부 시 기존 담당/잔여·업무 이력을 유지한다.

2026-10-12 사용자 확정(담당 교체 전 수업의 누락 등록 질문의 1번): A가 담당으로 실제 수업을 진행한 뒤 담당이 B로 바뀌어도 A는 교체 전 본인 수업을 직접 늦게 등록할 수 있다. 예: 9월 5일 A 수업 → 9월 6일 B로 담당 교체 → 9월 7일 A 누락 등록. 실제 수업 당시 A의 담당 관계와 본인 수행 사실, 현재 검증된 Caller/Trainer 연결·Organization 및 기존 Pass/정산 조건을 확인한다. 현재 담당이 B라는 이유만으로 관리자 대행이나 A 재배정을 요구하지 않는다. 이 허용만으로 A의 해당 회원 목록/상세·전화번호/다른 Pass·다른 Trainer 기록 조회 권한을 복원하지 않는다(BR-OPS-003/005/008, PD-008, PR-008/029/030).

관련 등록/인가의 상세는 BR-OPS-003을 따른다. 교체 전 A의 수업을 새로 등록하는 업무이며 기존 B 담당 관계나 과거 지급을 다시 쓰지 않는다. 담당 이력/수행 사실·최소 식별/응답 계약과 등록/교체/월 확정 경합은 후속이다.

2026-10-12 사용자 확정(잔여 0회인 이용권의 담당 교체 질문의 1번): Remaining이 0인 기존 Pass도 Assigned Trainer를 교체할 수 있다. 잔여를 모두 사용해 이용이 끝난 Pass도 포함한다. 같은 Pass에서 담당 A를 B로 바꾸며 Remaining 0·발급 조건/Issued Branch·과거 실제 수행 Trainer/PT 기록·확정 지급/정산 이력은 유지한다. 새 담당 B는 기존 현재 담당 관계에 따른 Member 조회·응대를 이어갈 수 있다. 기존 Master Organization 전체/Branch Admin 처리 시점 Member 현재 Home Branch 권한과 같은 Organization의 다른 지점 Trainer도 대상 허용 원칙은 유지한다(BR-OPS-005/008, PD-007, PR-003/029/030).

기존 규칙 적용: 담당 교체만으로 Pass를 새로 발급하거나 횟수를 복원/추가하지 않고 사용 상태를 재개하지 않는다. 잔여는 0이며 해당 Pass는 정상 PT 차감 후보가 될 수 없다. 교체 전 누락 수업의 이전 담당 직접 등록도 기존 현재 잔여 > 0 등 Pass/정산 조건을 면제하지 않는다. Member/Trainer Home Branch·Pass Issued Branch와 과거 실제 수업/지급은 바꾸지 않고 현재 B 설정으로 과거 보상을 재계산하지 않는다. 저장 후 즉시 현재 담당 반영·전후 담당/Actor/Role·Branch Context/시점 이력·감사, 거부/실패 시 기존 담당·잔여/이력 유지 원칙을 적용한다(BR-OPS-003/008, BR-PAY-006/009/011).

회원 조회 경계: B는 잔여 0이라는 이유만으로 담당 Member의 기본 목록/검색/직접 ID 상세·기존 허용 전화번호 읽기를 차단당하지 않는다. 잔여 0 제외 필터는 기존대로 기본 미사용이며 켜면 조회 인가된 Member 전체 Pass 잔여를 기준으로 판단한다. 해당 Pass 0/다른 담당 Trainer 또는 Issued Branch의 Pass 10이면 필터 사용 후에도 표시하고 전체 합계가 0이면 제외한다. 필터로 담당 관계나 개별 상세 인가를 제거하지 않는다. A는 다른 현재 담당/개별 지원/관리 근거가 없으면 과거 담당 사실만으로 Member/전화번호 조회를 유지하지 않으며 자기 과거 PT 조회·한정된 누락 등록은 별도 기존 Scope를 따른다. 새 담당 B에게 A의 모든 과거 PT/지급·다른 Pass 원본이나 Compensation Setting/전체 정산 공개 권한을 부여하지 않는다(BR-OPS-003/005/008, NFR-001/004).

남은 결정: 교체 Actor/Branch Scope·대상 Trainer 지점 조건·교체 전 실제 본인 수업의 이전 담당 직접 누락 등록과 함께 잔여 0으로 이용을 마친 Pass의 담당 교체도 해결됐다(2026-10-12). 수동 만료 Pass의 담당 조회는 M2/BR-OPS-005, 담당 교체 허용은 U1로 해결됐다. 다른 상태 조합·과거 담당/수행 사실 확인 불가/정정·교체 후 수업/다른 관계의 나머지 인가와 구체 명령/응답·최소 식별/Trainer 선택 정보·이력/저장/UoW·조회/등록/교체 경합은 ARCH-001·MB-001/003/005·BR-001/008 및 후속 Architecture에서 결정한다. 별도 Pass 발급 취소 기능은 M1으로 v1 제외이며 상태명/저장 방식을 이번에 확정하지 않는다. 교체 허용은 계정/역할·보상 설정 수정 권한 승인이 아니다.

Traceability: PD-007; PR-003/029/030; BR-OPS-005; NFR-001/004; ARCH-001; MB-001/003/005; BR-001; 2026-10-12 사용자 1번 답변 및 2026-10-11 사용자 일관성 지시.

비활성 기존 담당의 교체(2026-10-12, BR-OPS-014): Trainer 비활성화는 잔여 Pass의 Assigned Trainer를 유지하며 일괄 사전 교체를 요구하지 않는다. 이후 기존 담당이 비활성인 Pass도 권한 있는 관리자가 위 담당 교체 규칙으로 별도 처리할 수 있고 이전 담당 재활성화를 선행 요구하지 않는다. 교체 Actor는 Member 현재 Home Branch 기준이며 비활성화 Actor의 Trainer Home Branch 기준과 다르다. 기존 잔여/이력 유지·현재 담당 조회 원칙을 따르되 비활성 Trainer 역할에는 접근을 주지 않는다. 새로 지정할 Trainer는 활성만 허용하며 다른 상태별 교체 조건은 여전히 후속이다.

2026-10-12 사용자 확정(담당 Trainer를 새로 지정할 때의 조건 질문의 1번): PT Pass의 담당 Trainer를 새로 지정할 때는 실제 활성 Trainer만 허용한다. 기존 Pass의 담당 교체 및 허용된 새 Pass 발급 흐름에서 담당을 최초 지정하는 경우 모두 적용하며 비활성 Trainer를 미리 배정하지 않는다(BR-OPS-008/014, PD-007, PR-003/005/029/030, NFR-001, ARCH-001, MB-001/003/005, BR-001).

Backend는 지정 요청의 현재 Caller/행위 Scope·실제 Member/Pass 관계와 대상 Trainer의 실제 Organization/현재 활성 상태를 확인한다. 선택 목록에 있었거나 과거 Caller/클라이언트 active 표시가 있더라도 지정 확정 시 실제 비활성 Trainer는 거부한다. 비활성화가 먼저 확정되면 새 지정은 거부하고 요청 직전 담당·잔여/발급 조건·이력을 유지한다. 지정이 먼저 확정된 뒤 Trainer가 비활성화되면 BR-OPS-014에 따라 기존 담당 정보는 유지하고 Trainer 역할의 후속 업무 접근은 차단한다. 정확한 검증 시점/순서·잠금/저장/UoW·실패/재시도는 후속 Architecture에서 증명한다.

기존 허용 관계/권한 유지: 같은 Organization의 다른 Home Branch Trainer도 실제 활성이면 기존 조건 안에서 지정할 수 있다. 대상 Trainer Home Branch를 Member Home Branch/Pass Issued Branch와 같게 강제하지 않는다. 담당 교체는 기존 Master Organization 전체/Branch Admin 처리 시점 Member 현재 Home Branch 기준이며 Trainer 비활성화의 Trainer Home Branch Scope로 대체하지 않는다. 새 Pass 발급 중 최초 지정은 해당 흐름에서 허용되는 경우 이 대상 조건을 적용하는 것이며 최초 담당 필수 여부/미지정 Pass 허용·구체 Actor/절차를 이번에 새로 승인하지 않는다. Operator의 새 Pass 발급 권한을 기존 Pass 담당 교체 권한으로 확대하지 않는다.

활성의 의미/보존: 실제 Trainer 업무 활성 상태와 IAM 계정 전체 상태·현재 AuthSession/로그인 유무를 구분한다. 로그인 중이라는 사실이나 관리자 역할 보유만으로 비활성 Trainer를 활성으로 간주하지 않는다. Trainer 활성/계정 차단·비밀번호 설정 대기·Branch 상태의 조합 등 남은 대상 조건은 별도 게이트이며 활성 Trainer라는 필요조건만으로 모든 조합을 허용하지 않는다. 기존 비활성 담당의 저장 사실은 유지 대상이며 새 지정 금지 때문에 자동 해제/교체·Pass 취소/재발급/횟수 재처리를 하지 않는다. 과거 PT의 실제 수행 Trainer·지급/정산을 현 활성 Trainer로 바꾸지 않고 비활성 전 실제 수업의 늦은 등록 정책을 현재 담당 신규 지정과 혼동하지 않는다.

남은 결정: 최소 Trainer 선택/공개 정보·최초 담당/미지정 조건·다른 Pass/Branch/계정 상태 조합, 개별 지원 관계·Trainer 재활성화/비활성 상태 과거 PT 예외 및 실제 계약/저장/현재 사실 검증·UoW/동시성은 후속이다. 기존 OPEN 전체·ADR-0004 v1 인증 방식 ACCEPTED/Architecture 구체안 PROPOSED·IAM-001 S1 범위는 유지하며 V-68은 미구성·미실행 계획이다.

2026-10-12 일괄 승인 B3/B4: 새 Pass 발급 시 실제 활성 Assigned Trainer 지정은 필수이며 최초 Remaining은 발급 상품의 Session Count와 같다. 미지정 발급/발급 중 별도 횟수 입력을 기본 제공하지 않는다. 같은 Organization 타 지점 활성 Trainer 허용은 유지하고 최초 발급의 기존 Actor/Issued Branch Scope(BR-OPS-010)를 적용한다. 기존 Pass 담당 교체의 Member 현재 Home Branch 인가와는 구분한다. 횟수 예외는 BR-OPS-009의 별도 허용 관리자 조정으로 처리하며 Operator에게 조정 권한을 추가하지 않는다. 발급 당시 가격/총횟수/Payment Type·원본 조건을 보존한다. 다른 계정/Branch/Pass 상태 조합·최소 선택 계약/저장·경합은 후속이다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch).

2026-10-13 U1=1: 수동 만료된 Pass도 담당 Trainer를 교체할 수 있다. 기존 Master 자기 Organization/각 처리 시점 Member 현재 Home Branch Admin 인가·같은 Organization 실제 활성 Trainer 대상·타 지점 Home 허용·Operator/Trainer 단독 금지와 독립 관리자 겸임 Scope를 유지한다. 현재 만료 상태·Remaining·발급 시각/조건/Issued Branch·과거 실제 수행 Trainer/PT·확정 지급/정산은 보존한다. 자동 만료 해제/잔여 부여·새 Pass 발급·과거 수행/지급 재작성은 하지 않는다. 기존 직접 처리/별도 Master 승인 없음·전후 담당/Actor/Branch Context·시점 감사/이력을 적용하며 추가 필수 사유는 도입하지 않는다. 새 담당의 현재 회원 조회는 BR-OPS-005/M2를 따르고 이전 담당은 다른 유효 현재 관계 없이 일반 조회를 유지하지 않는다. 만료 Pass의 새 수업 사용은 허용하지 않으며 만료 전 실제 본인 수업 지연 등록 예외·기존 만료 해제/횟수 조정의 Issued Branch Scope는 별개다. 다른 상태/역사 사실·최소 계약/경합은 후속이다. [U 승인](product-decisions.md#review-20261013-u-batch); V-122 미구성·미실행.

<a id="br-ops-009"></a>
## BR-OPS-009 — 이용권 횟수 수동 조정의 관리자 범위

Status: APPROVED

2026-10-12 사용자 확정(이용권 횟수의 수동 조정 권한 질문의 1번): Pass 횟수의 수동 조정은 Master Admin의 Organization 전체 범위 또는 처리 시점 현재 관리 Branch가 해당 Pass의 Issued Branch인 Branch Admin에게 허용한다. 수원 발급/현재 강남 소속 Member의 이용권은 수원 Branch Admin 또는 Master가 조정하며, 강남 Branch Admin은 Member의 현재 소속만을 근거로 조정할 수 없다. 회원 소속이나 담당 Trainer가 바뀌어도 Issued Branch 기준은 유지한다. 이용권 수동 만료/해제와 같은 발급 지점 기준이며 담당 교체의 Member 현재 Home Branch 기준과 구별한다(BR-OPS-004/008/009, PD-007/010, PR-003/030).

Backend는 매 조정 요청에서 검증된 현재 Caller의 관리자 권한/Organization·관리 Branch Scope와 실제 Pass Issued Branch·Pass/Member Organization 관계를 확인한다. 요청의 role/Branch/Pass/Member ID·Member/Trainer Home Branch·현재 담당/개별 지원/Performed Branch·과거 관리 지점/발급 Actor라는 사실만으로 조정 권한을 부여하지 않는다. 관리자 권한 없는 Operator/Trainer는 수동 조정할 수 없고 관리자·Trainer 겸임자는 해당 관리자 Scope로 판단한다. 범위 밖 직접 ID/위조 Scope 요청은 거부한다. 계정 차단·현재 Role/Scope 축소에 대한 기존 서버 인가 원칙을 따르며 과거 조정자라는 이유로 권한을 유지하지 않는다.

기존 Pass 조정 사유/이력 및 중요 변경 감사 원칙 적용(PR-003, BR-OPS-001, NFR-004; 2026-10-11 사용자 일관성 지시): 허용된 수동 조정에는 사유가 필수다. 대상 Pass/Member·변경 전후 Remaining·증감량·사유·처리 Actor/Role·Branch Context·처리 시점을 추적한다. 이력 없이 현재 잔여만 덮어쓰는 절차로 처리하지 않는다. 기존 범위 내 관리자 직접 처리 원칙을 동일 적용하여 별도 Master 승인 대기를 추가하지 않는다. 권한 없는 요청·사유 누락·거부/저장 실패는 기존 잔여/Pass 조건·담당/수업·지급/정산 이력에 일부 변경을 남기지 않는 기존 정합성 원칙을 따른다. 구체 조정 이력/감사 저장·조회 계약과 UoW는 Architecture 후속이다.

업무 경계: 수동 횟수 조정 권한은 과거 PT 진행 사실의 정정/취소·확정 지급/정산 재계산 권한이 아니다. 실제 PT 취소에 따른 횟수 복원은 기존 Performed Branch 기준의 허용된 수업 취소 업무/조건을 따르는 별도 처리이며 이번 Issued Branch 수동 조정 기준으로 대체하지 않는다. 수동 조정을 이용해 PT 이력을 삭제하거나 과거 지급을 현재 설정으로 재계산하지 않는다. Member/Trainer Home Branch·Pass Issued Branch/Assigned Trainer·발급 당시 Product 가격/총횟수/Payment Type과 보상 설정 접근 제한은 유지한다. 수동 조정 권한만으로 새 Pass 발급/담당 교체·수동 만료 해제나 타 지점 전체 자료 열람 권한을 부여하지 않는다.

남은 결정: 최초 상품 횟수 부여/발급 횟수 초과 추가·C12 음수 잔여 금지/C13 사용 가능·소진·수동 만료의 조정 허용은 해결됐다. 나머지 목적/입력 상한·CANCELLED 등 상태/비활성 지점 결합·복원 연계는 BR-001/002·ARCH-003에 남긴다. 이번 승인은 관리자/지점 기준과 기존 사유/이력 원칙의 적용이며 모든 수량/상태의 조정을 일괄 허용한 것이 아니다. 명령/응답·조정 이력/감사 저장·Application UoW·실패/재시도/중복·동시 수업 차감/복원/만료/권한 변경 경합은 후속 Architecture 설계·검증 대상이다.

Traceability: PD-007/010; PR-003/009/030; BR-OPS-001/004/008; NFR-001/002/003/004; BR-001/002/007; ARCH-001/003; 2026-10-12 사용자 1번 답변 및 2026-10-11 사용자 일관성 지시.

2026-10-12 일괄 승인 B4/B5: 최초 횟수는 상품 Session Count대로 부여하며 기존 인가된 관리자의 별도 수동 추가 조정으로 최초 발급 횟수를 넘는 Remaining도 허용한다. 예: 최초 20회/현재 20회에 +2회 조정하면 현재 22회이나 원본 상품 총횟수 20회·가격/Payment Type은 유지한다. 이후 일반 수업은 기존 원본 발급 조건과 생성 시점 Trainer 설정의 회당 지급 규칙을 적용하고 원본 분모를 22로 재작성/과거 지급 재계산하지 않는다. 기존 Issued Branch 인가·사유/전후 잔여·증감/Actor·시점 이력·감사와 실패 일관성을 적용한다. 음수/나머지 수량·상태별 조정/재개 조건과 구체 계약/경합은 계속 후속이며 모든 수량/상태를 일괄 허용한 것은 아니다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch).

2026-10-12 C12/C13 승인: 수동 감소는 Remaining 0까지 허용하고 음수가 되는 요청은 거부한다. 자동으로 0에 맞춰 일부만 감소시키거나 부채/다음 이용권 상계로 처리하지 않는다. 사용 가능·잔여 소진·수동 만료 Pass 모두 기존 Issued Branch 관리자 Scope와 사유/이력/감사 안에서 조정할 수 있다. 소진 Pass는 횟수 추가 후 다른 사용 조건을 충족하면 다시 이용할 수 있다. 수동 만료 Pass는 추가해도 만료 상태를 유지하고 별도 승인된 만료 해제가 필요하다. 기존 만료 전 실제 수업 누락 등록 예외는 유지한다. CANCELLED 등 다른 상태/비활성 지점 조합을 일괄 허용하지 않는다. 원본 발급 조건/과거 지급은 보존하고 실패/경합 시 부분 반영은 허용하지 않는다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

<a id="br-ops-010"></a>
## BR-OPS-010 — 회원 소속 밖 지점에서 새 이용권 발급

Status: APPROVED

2026-10-12 사용자 확정(다른 지점에서 새 이용권 구매·발급 질문의 1번): Member는 같은 Organization의 Home Branch 밖 지점에서도 새 PT Pass를 구매·발급받을 수 있다. 수원 소속 회원이 강남에서 발급받으면 Member Home Branch는 수원으로 유지하고 새 Pass의 Issued Branch는 강남으로 기록한다. Member Home Branch와 Issued Branch가 같아야 한다는 제한을 두지 않는다. 기존 Member 식별자/소속·보유 Pass와 과거 PT/지급·정산 이력은 유지하며 타 지점 발급을 위해 Member를 지점별로 복제하거나 소속을 자동 이동하지 않는다(BR-OPS-001/010, PD-004/007, PR-002/003/030).

인가/조회 경계: 발급 업무의 실제 Issued Branch를 식별하고 검증된 현재 Caller의 발급 권한/Organization·허용 발급 Branch Scope와 Member/Product/Branch의 실제 Organization 관계를 Backend에서 확인한다. Member Home Branch가 다르다는 사실만으로 허용된 발급을 차단하지 않되 요청의 role/organization_id/branch_id/Member ID·고객이 방문했다는 표시만으로 발급 권한을 인정하지 않는다. 타 지점 Member를 대상으로 발급할 수 있다는 결정이 그 지점 전체 회원 목록/전화번호·다른 Pass/PT/보상 자료의 일반 조회나 Member Home Branch 변경 권한을 부여하지 않는다. 발급용 같은 Organization 전체 지점 Member의 이름·전화번호 일부 검색은 아래 2번 후속 승인으로 해결됐고 추가 공개 정보·Member 선택용 최소 식별 응답/계약은 Product/Architecture 후속이며 Trainer의 기존 담당/개별 지원 회원 조회 범위를 확대하지 않는다.

기존 규칙 적용: Organization 공통 Product Catalog를 사용하고 새 Pass에 발급 당시 상품 가격·총횟수·Payment Type을 보존한다. 공통 상품 생성/수정은 여전히 Master 전용이며 타 지점 발급 권한으로 Catalog를 변경하거나 지점별 가격 정책을 추가하지 않는다. 판매 중단 Product로 새 Pass를 발급할 수 없고 이미 발급된 다른 Pass의 조건/잔여·과거 이력을 덮어쓰지 않는다. 실제 수업에서 사용할 Pass는 기존 사용 가능 조건·FIXED_AMOUNT 우선/동일 Type FIFO와 수업 당시 발급 사실을 따른다. 새 Pass 발급만으로 과거 수업에 소급 사용하거나 과거 지급을 재계산하지 않는다(BR-PAY-001/006/009, BR-011 CLOSED).

후속 관리 기준: 새 강남 Issued Pass의 수동 만료/해제·수동 횟수 조정은 기존 Master Organization 전체/Branch Admin 처리 시점 현재 관리 Branch=Issued Branch 원칙을 따른다. 수원 Member Home Branch라는 사실만으로 수원 관리자에게 그 Pass의 해당 발급 지점 기준 업무 권한이 생기지 않는다. Pass 담당 교체는 기존 Member 현재 Home Branch 기준이고 실제 PT 기록 정정/취소는 기존 Performed Branch 업무 기준이다. Trainer Compensation Setting 권한·실제 수업 당시 Trainer Home Branch/Performed Branch의 일반·지원 보상 구분과 과거 불변성도 유지한다(BR-OPS-004/008/009, BR-PAY-010/015).

2026-10-12 사용자 확정(새 이용권 발급 Actor 질문의 1번): 새 PT Pass 발급은 Master Admin·Branch Admin·Operator에게 각자의 허용된 실제 Issued Branch 범위에서 허용한다. Master는 Organization 전체, Branch Admin은 자신의 단일 관리 Branch, Operator는 부여된 허용 발급 Branch Scope에서 처리한다. 같은 Organization의 Member는 Home Branch가 발급 지점과 달라도 대상이 될 수 있으며 기존 Member/Home Branch를 유지하고 새 Pass에 실제 Issued Branch를 기록한다(BR-OPS-010, PD-004/007, PR-003/030).

권한 경계: Trainer 역할만으로는 새 Pass를 발급할 수 없다. Trainer를 겸하는 계정에 Master·Branch Admin·Operator의 발급 권한이 있으면 해당 역할의 독립적인 발급 Scope로 판단하며 별도 계정을 요구하지 않는다. Operator의 새 발급 권한은 공통 상품 생성/수정, 기존 Pass 수동 횟수 조정·만료/해제·담당 교체, Member 소속 이동, PT 정정/취소·Compensation Setting·Additional Performance·월 정산의 별도 권한을 추가하지 않는다. 발급 대상 식별을 타 지점 전체 Member 목록/전화번호·다른 Pass/PT/민감 보상 정보의 일반 조회 허용으로 확대하지 않는다. 기존 보상 설정 접근 제한과 Trainer의 담당/개별 지원 회원 조회는 그대로다.

Backend는 각 발급 요청에서 검증된 현재 Caller의 발급 역할/Organization·허용 실제 Issued Branch와 Member/Product/Branch의 실제 Organization 관계를 확인한다. 범위 밖 발급 지점·다른 Organization·Trainer 단독 권한·직접 ID/위조 role/Branch 값으로는 발급할 수 없으며 역할/Scope가 철회·축소되면 후속 발급 요청에도 현재 권한을 적용한다. 거부/실패 시 기존 Member/Home Branch·Pass·업무 이력을 유지한다. 발급 권한과 발급 이후의 관리 권한은 별도이므로 과거 발급 Actor였다는 사실만으로 후속 관리자 권한을 얻지 않는다.

남은 결정: 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차과 실제 발급 지점 선택/계약, 지점/Member/Trainer 활성·발급 시 활성 담당 필수/상품 최초 횟수의 나머지 상태/선택 계약, 타 지점 Member 추가 공개 정보·Member 선택용 최소 식별 응답/계약과 업무 인가 경로는 ARCH-001·MB-001/002/003/004/005·BR-001/002/010 후속이다. 승인된 Master·Branch Admin·Operator의 발급 허용과 Trainer 단독 불가를 다시 미결정으로 두지 않으며, 미정 Scope 부여/조회·상태 조건을 임의 기본값으로 구현하지 않는다. 발급/상품 조건·감사 계약/저장·Application UoW·실패/재시도/중복 및 판매 중단/지점 상태/Member 이동/인가 변경 경합은 후속 Architecture 설계·검증 대상이다.

2026-10-12 사용자 확정(발급용 타 지점 회원 검색 질문의 2번): Branch Admin·Operator는 자신의 허용된 실제 Issued Branch에서 새 PT Pass를 발급하기 위해 같은 Organization 전체 지점의 Member를 이름·전화번호 일부로 검색할 수 있다. 전화번호 전체 일치만을 요구하지 않으며 Member Home Branch가 Caller의 관리/발급 Branch와 다르다는 이유만으로 검색 후보에서 제외하지 않는다. Master의 기존 Organization 전체 범위는 유지한다. 검색은 기존 Member를 선택하여 실제 발급 지점의 새 Pass를 만드는 흐름이며 Member 소속 이동/복제나 기존 Pass·PT·지급·정산 변경을 수행하지 않는다(BR-OPS-010, PD-004/007/022, PR-002/003/030).

검색 인가/정보 공개 경계: 이 허용은 이용권 발급용 Member 검색의 후보 범위·검색 방식과 이름/전체 전화번호/현재 Member Home Branch 공개다. Backend는 매 검색/선택/발급 요청에서 현재 Caller의 발급 역할/Organization·허용 실제 Issued Branch와 대상 Member의 실제 Organization을 검증한다. 검색 Branch Context를 위조하거나 과거 검색 결과/선택 Member ID로 철회된 역할·Scope 또는 다른 Organization을 우회할 수 없다. 같은 전화번호/이름의 여러 Member는 별도 식별자로 구분하여 선택하며 번호만으로 병합하거나 첫 결과를 자동 선택하지 않는다. 이 세 항목의 읽기 허용이 회원 정보/전화번호 수정·일반 Member 상세·전체 무조건 목록/일괄 내보내기, 다른 개인정보/Pass/PT/보상 정보 열람 권한을 추가하지 않는다. Trainer 단독의 담당/개별 지원 Member 검색 및 기존 전체 전화번호 공개는 유지하고 발급 역할 겸임은 그 독립 발급 업무 Scope로 판단한다. 응답은 승인된 공개 범위 안에서 구성하며 Member 선택용 최소 식별 응답/계약과 추가 공개 정보는 후속이다. 실제 운영 연락처/검색어를 문서·일반 로그에 복사하지 않는다.

회원 식별의 기존 원칙 적용: 같은 전화번호/이름으로 여러 Member가 일치하면 별도 Member 식별자로 구분하여 발급할 대상을 선택한다. 번호 일치/첫 결과만으로 자동 병합·동일 회원 취급·소속 이동 또는 다른 Member 이력/권한 공유를 하지 않는다(BR-OPS-006). 잔여 0만으로 회원을 제외하지 않는 기존 조회 원칙은 유지하며 발급용 검색을 Trainer 전용 선택 제외 필터/담당 회원 집합으로 제한하지 않는다. 비활성 Member/Branch 등 나머지 대상 조건·검색어/빈 검색 처리·추가 공개 정보·최소 선택 응답/계약·선택/발급 일관성은 후속이다. 검색 자체는 업무 데이터를 변경하지 않으며 검색 성공만으로 발급 완료나 발급 이후 관리자 권한을 얻지 않는다.

이번 결정으로 발급용 검색 후보의 Organization 전체 지점 범위·이름/전화번호 일부 검색과 결과의 이름/전체 전화번호/현재 Member Home Branch 공개는 해결됐다. 추가 공개 정보·Member 선택용 최소 식별 응답/계약 및 나머지 검색/대상 조건, 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·실제 발급 지점 선택, 발급 시 활성 담당 필수/상품 최초 횟수의 나머지 상태·계약/저장/UoW·실패/재시도/중복·권한/소속/상품/지점 상태 변경 경합은 후속이다. 승인된 세 항목의 공개/전화번호 비마스킹을 다시 미결정으로 두지 않는다. Product OPEN/ADR·모듈/계약 상태와 기존 보상 설정 접근 제한을 유지하며 실제 검색/발급 구현·검증 완료를 뜻하지 않는다.

2026-10-12 사용자 확정(발급용 검색 결과 표시 정보 질문의 1번): 새 PT Pass 발급용 Member 검색 결과에는 이름·전체 전화번호·소속 지점을 표시한다. 소속 지점은 해당 Member의 현재 Home Branch이며 Caller 관리 지점/Pass Issued Branch/수업 Performed Branch와 구별한다. 같은 Organization의 타 지점 회원 검색 결과에도 동일하게 적용하고 부분 마스킹된 번호만 표시하도록 제한하지 않는다. 기존 이름·전화번호 일부의 Organization 전체 지점 검색과 현재 발급 역할/실제 Issued Branch Scope 인가는 유지한다(BR-OPS-010, PD-004/007/022, PR-002/003/030, NFR-001/005).

표시/식별 경계: 같은 번호의 가족 Member A/B나 동명이인은 이름·전체 번호·현재 소속을 확인하고 별도 Member 식별자로 선택한다. 전체 전화번호 공개가 고유 로그인 ID/회원 자동 병합이나 전화번호 수정/내보내기 권한을 뜻하지 않는다. 검색에서 확인한 현재 Member Home Branch를 새 Pass Issued Branch로 자동 대체하거나 기존 소속/Pass/PT·지급/정산 이력을 변경하지 않는다. 필드별 응답 인가·최소 식별 계약/표현은 후속 Architecture이며 업무 구현/검증 결과가 아니다.

Traceability: PD-004/007/011/022; PR-002/003/006/030; BR-OPS-001/004/007/008/009; BR-PAY-001/006; NFR-001/002/004/005; ARCH-001; MB-001/002/003/004/005; BR-001/002; 2026-10-12 타 지점 발급/Actor 질문의 1번 및 발급용 회원 검색 질문의 2번·검색 결과 표시 정보 질문의 1번 답변.

2026-10-12 Operator 지점 수 후속 승인 반영: Operator 업무 Scope는 지정된 단일 Branch이며 새 Pass의 실제 Issued Branch도 그 지점을 따른다(BR-OPS-011). 발급용 검색의 Organization 전체 지점 Member 범위·이름/전체 전화번호/현재 Member Home Branch 공개는 유지한다. Member 소속과 Issued Branch 일치를 요구하거나 다른 Branch에서 발급할 권한을 추가하지 않는다. 계정/Scope 부여·지정 지점 변경 정책/절차는 후속이다.


<a id="br-ops-011"></a>
## BR-OPS-011 — Operator의 단일 업무 지점

Status: APPROVED

2026-10-12 사용자 확정(Operator 업무 허용 지점 수 질문의 1번): v1 Operator 역할의 업무 허용 Branch는 한 시점에 하나만 지정한다. Operator는 그 지정된 단일 Branch에서 명시적으로 허용된 업무를 수행하며 같은 계정의 Operator 권한을 여러 Branch에 동시 부여하지 않는다. Branch당 Operator 한 명이라는 1:1 인원 제한을 추가하지 않으며 하나의 Branch에 여러 Operator가 있을 수 있다. 이 결정은 Operator 역할의 업무 Scope이며 기존에 허용된 겸임 역할의 독립적인 관리/PT 권한이나 Trainer Home Branch를 바꾸지 않는다(BR-OPS-011, PD-001/007, PR-001/003/030, ARCH-001, MB-004).

인가 경계: Backend는 검증된 현재 Caller의 Operator 역할/Organization·지정된 단일 업무 Branch와 해당 요청의 실제 업무 Branch를 확인한다. 직접 Branch ID·클라이언트 branch_id/role/선택 지점·과거 업무/발급 지점만으로 다른 Branch의 업무를 수행할 수 없다. 동일 계정에 Operator 권한을 중복 부여하거나 여러 Branch 중 하나를 임의 선택하는 방식으로 단일 지점 제한을 우회하지 않는다. 현재 역할/Scope 철회·축소 이후 후속 요청은 현재 권한을 적용한다. 지정이 없거나 복수 지정된 상태를 유효한 Operator 업무 권한으로 간주하지 않되 구체 계정/역할 저장·활성화 제약과 오류 계약은 후속 Architecture다.

기존 발급/검색 규칙 유지: Operator의 새 Pass 발급은 자신의 지정된 단일 Branch를 실제 Issued Branch로 사용한다. 그 발급 업무에서는 같은 Organization 전체 지점 Member를 이름·전화번호 일부로 검색하고 결과의 이름·전체 전화번호·현재 Member Home Branch를 조회/선택할 수 있다(BR-OPS-010). Member Home Branch가 Operator 업무 Branch와 다르다고 검색/발급을 거부하거나 회원 소속을 자동 이동하지 않는다. 전체 지점 Member 검색이 다른 Branch의 Pass 발급이나 일반 회원 상세/다른 Pass/PT·보상/수정·일괄 내보내기 권한을 부여하지 않는다. 기존 Master 전용 공통 상품 변경 및 관리자 전용 Pass 수동 조정·만료/해제·담당 교체/보상 업무 제한은 유지한다.

남은 결정: 새 Operator 발급/최초 Branch 지정 Actor는 Master Organization 전체/Branch Admin 자기 단일 Branch, 기존 Operator 업무 Branch 변경 Actor는 Master Organization 범위 전용으로 해결됐다. 변경은 기존 저장 후 현재 Scope 반영/실패 보존·감사 원칙을 적용한다. 발급 절차·기존 계정 역할 추가/변경·Operator 지점 변경의 대상 Branch/계정 상태·세부 절차/감사 계약 및 나머지 운영 행위 권한은 MB-004·ARCH-001/002 후속이다. 한 계정의 Operator 동시 허용 지점 수나 신규 발급/지점 변경 Actor를 다시 OPEN으로 두지 않는다. 실제 발급 대상·초기 조건/선택 응답·역할/Scope 저장·Caller/인가 계약·실패/재시도/경합은 관련 Product/Architecture 후속이다. IAM-001 S1에 Operator 구현을 추가하거나 기존 PROPOSED 인증/모듈/저장 설계를 승인한 것은 아니다.

Traceability: PD-001/007/019; PR-001/003/021/030; BR-OPS-010; NFR-001/004/005; ARCH-001/002; MB-004; 2026-10-12 Operator 업무 허용 지점 수·계정 발급과 최초 지점 지정·기존 Operator 근무 지점 이동 권한 질문의 각 1번 답변.

2026-10-12 사용자 확정(Operator 계정 발급과 최초 지점 지정 권한 질문의 1번): Master Admin은 자신의 Organization 범위에서, Branch Admin은 자신의 단일 관리 Branch 범위에서 새 Operator 계정을 발급하고 그 한 지점을 최초 업무 Branch로 지정할 수 있다. Branch Admin의 타 지점 Operator 발급은 허용하지 않는다. Backend는 처리 시점의 검증된 현재 Caller 역할/Organization·관리 Branch와 대상 Branch의 실제 Organization 관계를 확인하며 직접 ID·위조 role/branch_id·과거 권한으로 범위를 우회할 수 없다. Operator 단독·Trainer 단독의 로그인 계정 발급은 허용하지 않는다(BR-OPS-011, PD-019, PR-021/030, NFR-001/004, MB-004, ARCH-001/002).

승인 범위: 새 Operator 계정 발급과 단일 Branch의 최초 지정이다. Branch Admin의 Master/Branch Admin 역할 발급, 기존 계정의 역할 추가·변경·계정 중단/복구·비밀번호 재설정 권한을 추가하지 않는다. 신규 Trainer 계정 발급은 별도 후속 승인된 BR-OPS-012의 현재 Trainer Home Branch 규칙을 적용한다. 기존 Operator Branch 변경은 별도 후속 승인된 Master 전용 규칙을 적용한다. 기존 겸임 역할의 독립 Scope·Trainer Home Branch 및 민감 보상 접근 제한을 유지한다. 계정 발급과 새 Pass 발급은 서로 다른 업무이며 Operator의 Pass 발급 허용을 계정 발급 권한으로 해석하지 않는다.

기존 사용자 일관성 지시(2026-10-11) 적용: 이번에 허용된 Operator 발급에도 기존 최초 비밀번호 설정 방식을 사용한다. 권한 있는 발급 관리자가 일회용 비밀번호 설정 링크를 대상자에게 전달하고 대상자가 직접 설정한다. 허용 범위 내 Branch Admin 발급에 별도 Master 승인 대기를 추가하지 않는다. 고정/임시 평문 비밀번호를 계정에 넣거나 긴 토큰 수동 입력을 기본 흐름으로 요구하지 않는다. 최초 설정 링크 30분/단일 사용·재발급 시 이전 링크 폐기는 A4로 해결됐다. 전달 채널/수신자 확인·활성 계정 재설정·나머지 계정 수명 상세는 ARCH-002의 게이트를 유지한다.

기존 중요 계정/권한 변경의 감사·일관성 원칙 적용: 대상 계정·Operator 역할·최초 업무 Branch·발급 Actor/현재 권한·Branch Context·시점을 추적한다. 비밀번호/해시·설정 토큰·전체 설정 링크를 일반 로그/감사에 복사하지 않는다. 거부·실패 시 계정/역할/최초 Scope·필수 감사 중 일부만 확정되는 상태를 남기지 않는 경계를 설계한다. 구체 감사 저장/열람·보존, 계정 활성화·역할/Scope 표현·UoW/동시성은 후속이며 새로운 필수 입력 사유를 추가하지 않는다.

2026-10-12 사용자 확정(기존 Operator의 근무 지점 이동 권한 질문의 1번): 기존 Operator의 단일 업무 허용 Branch 변경은 Master Admin만 자신의 Organization 범위에서 수행할 수 있다. Branch Admin은 변경 전/후 지점 관리자이거나 해당 계정의 최초 발급자여도 변경할 수 없다. Operator·Trainer 단독도 불가하며 겸임자는 현재 Master 권한이 있을 때만 그 관리 Scope로 처리한다(BR-OPS-011, PD-019, PR-021/030, NFR-001/004, MB-004, ARCH-001).

기존 사용자 일관성 지시(2026-10-11) 적용: 일반 관리 변경의 저장 완료 후 현재 사실 반영·실패 시 기존 상태 보존·중요 권한 변경 감사 원칙을 적용한다. 저장 완료 이후 시작되는 Operator 업무 요청은 새 단일 Branch와 현재 역할/Organization으로 인가하고 이전 Branch의 업무 접근을 유지하지 않는다. 재로그인·Frontend 갱신·배치까지 이전 Scope를 유효하게 두지 않으며 미래 적용일 예약 절차를 추가하지 않는다. 변경 실패 시 이전 Branch/Scope를 유지한다. 대상 계정·변경 전후 Operator Branch·변경 Actor/권한·Branch Context·시점을 추적하고 변경/필수 감사 일부만 확정되는 상태를 남기지 않는 경계를 설계한다. 구체 저장/UoW·감사/캐시·처리 중 요청·동시 변경의 일관 순서와 AuthSession 철회 방식은 후속이며 변경 사유 입력을 새 필수 조건으로 정하지 않는다.

변경 경계: Backend는 현재 Master 권한/Organization과 실제 대상 Operator 계정 및 변경 전후 Branch의 Organization을 확인한다. 다른 Organization 이동·위조 role/branch_id/직접 ID·철회된 Master 권한은 거부하며 새 Operator 발급 요청으로 기존 계정의 Branch를 덮어쓰는 우회를 허용하지 않는다. 변경 후에도 Operator 업무 Branch는 하나다. 같은 계정의 독립 관리자/Trainer 역할·Trainer Home Branch와 기존 Member 소속·Pass Issued Branch/담당/잔여·과거 PT/지급/정산은 변경하지 않는다. 새 Pass 발급의 실제 Issued Branch와 발급용 Organization 전체 지점 Member 검색은 현재 Operator Branch에서 기존 규칙으로 인가하며 과거 발급자/이전 지점 사실은 권한을 보존하지 않는다. Branch Admin의 자기 지점 신규 Operator 발급/최초 지정 권한은 그대로다. 대상 Branch/계정 상태·나머지 역할 변경/계정 수명 권한·구체 계약/동시성은 기존 게이트다. IAM-001 S1 확장이나 ADR-0004/모듈 설계 승인에 해당하지 않는다.


<a id="br-ops-012"></a>
## BR-OPS-012 — Trainer 로그인 계정 발급 권한

2026-10-26 추가 승인([I1-Q1/Q2/Q3 모두1](product-decisions.md#review-20261026-i1)):
실제 활성 Trainer만 신규 발급·미설정 초기 링크 재발급·최초 비밀번호 설정 완료를 허용한다.
중간 비활성화 시 설정 완료를 보류하며 자동 재활성화/연결 삭제/링크 만료 연장은 없다.
Trainer당 연결 계정 하나·계정당 연결 Trainer 하나로 중복 발급/덮어쓰기/자동 동일인 연결을 금지한다.
PENDING_SETUP만 현재 Master 조직 또는 대상 Trainer의 실제 현재 Home Branch 관리자의 명시 재발급을 허용한다.
ACTIVE/DISABLED 및 기존 Login ID 계정은 신규 발급/초기 링크 재발급·자동 역할 추가로 우회하지 않는다.
활성 Trainer의 Home 비활성만으로 신규 발급/재발급/유효 링크 설정을 거부하지 않는다.
현재 Caller/조직/Scope 및 A4·B2·G1·C3·AB4·E5는 유지한다. 아래 과거 후속 문구 중 이 세 선택만 해결됐고,
I2 기존 계정 역할 연결/역할 없는 계정 정책·분실 암호 reset·상태/이동 및 구현 계약은 별도다.

Status: APPROVED

2026-10-12 사용자 확정(신규 Trainer 로그인 계정 발급 권한 질문의 1번): Master Admin은 자신의 Organization 전체 Trainer, Branch Admin은 발급 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 단일 관리 Branch인 경우 신규 Trainer 로그인 계정을 발급할 수 있다. Branch Admin은 타 지점 소속 Trainer 계정을 발급할 수 없다. 타 지점 지원 수업·담당 회원/Pass·Performed Branch·Operator 업무 Branch·최초 발급자/과거 소속 사실만으로 이 권한이 생기지 않는다. Operator·Trainer 단독은 본인 포함 로그인 계정 발급 불가이며 관리자 겸임은 현재 관리자 역할의 독립 Scope로 판단한다(BR-OPS-012, PD-019, PR-021/029/030, NFR-001/004, MB-004, ARCH-001/002).

인가 경계: Backend는 검증된 현재 Caller의 역할/Organization·관리 Branch와 대상 Trainer의 실제 Organization/현재 Home Branch 사실을 확인한다. 클라이언트 role/organization_id/branch_id·Trainer ID 또는 과거 조회 결과를 권한 근거로 신뢰하지 않는다. 직접 ID·다른 Organization/타 지점 Trainer·철회/축소된 권한은 거부한다. 발급용 Trainer 최소 식별/선택의 공개 범위·실제 Trainer 연결 계약은 후속이며 무제한 타 지점 Trainer 목록/프로필·보상 조회를 추가하지 않는다.

승인 범위: 신규 Trainer 로그인 계정 발급 Actor와 관리 Scope다. 기존 계정의 Trainer 역할 추가/다른 Trainer로 재연결·연결 덮어쓰기, 관리자 역할 추가/승격, Trainer Home Branch 변경, 기존 계정 중단/복구·비밀번호 재설정 권한을 추가하지 않는다. 기존 계정의 관리자/Trainer 겸임 허용은 유지하되 그 역할 추가/연결 처리 권한과 절차는 별도 게이트다. 새 발급 입력의 임의 role/admin_scope로 Master/Branch Admin을 생성하거나 기존 계정 역할/Trainer 연결을 덮어쓰는 우회를 허용하지 않는다. Trainer Home Branch를 IAM 관리 Scope나 Operator 업무 Branch로 대체하지 않으며 기존 Member/Pass/수업·지급·정산 사실을 변경하지 않는다. 계정 발급과 Compensation Setting 조회/변경은 별도 권한이고 Trainer 역할 자체는 본인 설정도 조회/변경할 수 없다.

기존 사용자 일관성 지시(2026-10-11) 적용: 권한 있는 발급 관리자가 일회용 최초 비밀번호 설정 링크를 대상자에게 전달하고 대상자가 직접 설정하는 기존 방식을 재사용한다. 허용 범위 내 Branch Admin 발급에 별도 Master 승인 대기를 추가하지 않는다. 고정/임시 평문 비밀번호나 긴 토큰의 수동 입력을 기본 흐름으로 두지 않는다. 전달 채널·링크 유효기간/재발급·활성 계정 비밀번호 재설정·나머지 계정 수명/인증 보안 정책은 ARCH-002와 인증 설계 게이트를 유지한다.

기존 중요 계정/권한 변경의 감사·일관성 원칙 적용: 대상 계정/Trainer·발급 시 Trainer Home Branch·생성 역할/Trainer 연결·발급 Actor/현재 권한·Branch Context·시점을 추적한다. 비밀번호/해시·설정 토큰·전체 설정 링크를 일반 로그/감사에 복사하지 않는다. 거부/실패 시 계정·역할·Trainer 연결/필수 감사 중 일부만 확정되지 않는 경계를 설계한다. 프로필 생성과 계정 발급의 순서·기존 연결/중복 발급 처리·계정/Trainer 활성 조건·감사 저장/열람/보존과 구체 UoW/실패·재시도/동시성은 후속이며 새 필수 입력 사유를 추가하지 않는다.

구현 경계: Trainer 로그인은 v1 요구사항이지만 이 승인은 Product 권한 결정이다. IAM-001 S1의 최소 관리자 흐름/발급 API를 확장하거나 실제 Trainer 모델·로그인·인가를 구현/검증한 것이 아니다. IAM 계정/역할/Trainer 연결과 Workforce의 Trainer/Home Branch 원본을 공개 계약으로 조합하는 책임·저장·Caller/UoW 구체 설계는 PROPOSED이며 ADR-0004 v1 인증 방식은 ACCEPTED다. AuthSession 수단/만료·철회/CSRF/MFA·Bootstrap과 기존 계정의 역할/수명 정책을 이번에 확정하지 않는다.

Traceability: PD-001/019; PR-001/021/029/030; BR-OPS-001/011; NFR-001/004; MB-004; ARCH-001/002; 2026-10-12 신규 Trainer 로그인 계정 발급 권한 질문의 1번 답변.

<a id="br-ops-013"></a>
## BR-OPS-013 — Trainer 소속 지점 변경

Status: APPROVED

2026-10-12 사용자 확정(Trainer 소속 지점(Home Branch) 변경 권한 질문의 1번): Trainer의 Home Branch 변경은 Master Admin만 자신의 Organization 범위에서 수행한다. Branch Admin은 변경 전/후 지점 관리자 또는 해당 Trainer 계정 발급자여도 변경할 수 없다. Operator·Trainer 단독은 본인 포함 불가하며 관리자/Trainer 겸임도 현재 Master 권한이 있을 때만 해당 Organization Scope로 처리한다. Branch Admin의 자기 지점 Trainer 신규 로그인 계정 발급 권한(BR-OPS-012)은 유지하며 이를 소속 변경 권한으로 확대하지 않는다(BR-OPS-013, PD-004, PR-005/029/030, NFR-001/004, MB-001/004/005, ARCH-001).

인가 경계: Backend는 검증된 현재 Caller의 Master 역할/Organization과 실제 대상 Trainer의 현재 Organization/Home Branch·변경 대상 Branch의 Organization을 확인한다. 같은 Organization 안의 변경만 허용하며 직접 Trainer/Branch ID·위조 role/organization_id/branch_id/과거 Master 권한으로 우회할 수 없다. 지원 수업·담당 Member/Pass·Performed/Issued Branch 또는 기존 계정 발급 권한은 대체 근거가 아니다. 새 계정 발급/일반 기본정보 수정으로 기존 Trainer Home Branch를 덮어써 권한을 우회하지 않는다. 변경 후에도 Trainer Home Branch는 한 시점 하나이며 다른 지점 수업 수행만으로 Home Branch를 자동 변경하지 않는다.

기존 사용자 일관성 지시(2026-10-11) 적용: 일반 이동은 기존 관리 변경과 같이 저장 완료 즉시 새 현재 Home Branch를 적용하고 미래 적용일 예약을 추가하지 않는다. 변경 완료 이후 시작되는 요청의 보상 설정·월 정산 관리/조회·Trainer 계정 발급 등 기존 현재 Home Branch 기반 인가는 새 소속과 현재 Caller Scope를 사용한다. 재로그인/Frontend 갱신·배치까지 이전 소속의 관리 권한을 유지하지 않는다. 실패 시 기존 소속/권한 근거를 보존한다. 현재 Home Branch 변경·소속 변경 이력·필수 감사 중 일부만 확정되지 않는 경계를 설계한다. 대상 Trainer·변경 전후 Home Branch·변경 Actor/현재 Master 권한·Branch Context·적용/변경 시점을 추적하고 새 필수 사유 입력을 정하지 않는다. 구체 UoW·캐시·처리 중 요청/동시 이동의 순서는 후속 설계다.

독립 역할/관계 보존: 같은 계정의 관리자 역할/관리 Branch·Operator 업무 Branch·실제 계정/Trainer 연결을 Home Branch와 함께 자동 이동하지 않는다. Branch Admin/Trainer 겸임의 관리자 관리 Branch가 그대로인 상태에서 본인 Trainer Home Branch가 다른 곳으로 바뀌면 본인 보상 설정도 기존 관리 Scope 조건을 다시 확인한다. Trainer Home Branch 변경만으로 다른 관리 권한을 새로 부여하지 않는다. 기존 담당 Pass/Member 관계와 개별 지원 조회 허용은 같은 Organization 내 이동에서 유지하며 실제 조회/PT 업무는 기존 현재 Caller/관계/상태 조건을 따른다(BR-OPS-005/008). Member Home Branch·Pass Issued Branch/담당/잔여·과거 실제 수행 Trainer/Performed Branch는 변경하지 않는다.

보상/과거 사실 보존: 일반/지원 구분은 실제 수업 당시 Trainer Home Branch와 Performed Branch를 비교한다. 이동 후 늦게 등록하는 수업도 당시 소속을 사용하고 현재 소속을 임의 대입하지 않는다. 기존 일반 지급 확정액·지원 수업 보상/추가실적·정산 확정본/과거 비용 귀속을 이동만으로 재계산·덮어쓰지 않는다. Rate/Fixed Amount/Base Salary 설정값과 월별 수동 적용 기본급은 이동으로 초기화하지 않으며 일반 지급의 기록 생성 시점 설정 적용·지원 수업 관리자 수동 추가실적·월말 Home Branch 기본급 한 번 귀속 등 기존 규칙을 유지한다. 설정/금액 관리 Actor는 각 처리 시점 현재 Home Branch 기준이고 PT 정정/취소는 기존 Performed Branch 기준이다. 소속 이동은 별도 PT/보상 정정 명령이 아니다.

남은 결정: 일반 이동 Actor와 기존 저장 후 현재 사실 반영/실패 보존·감사 원칙은 해결됐다. 대상 Branch/Trainer 상태·최소 대상 선택 정보/절차, 과거 소속 이력 오류 정정의 Master 전용/사유·원본 보존은 BR-OPS-032로 해결됐다. 구체 정정 범위/현재 사실·수업/보상 영향 처리·수업 당시 소속 확인 불가 예외는 MB-001/005 등 기존 게이트다. 과거 사실이 없거나 정정됐다고 현재 소속을 임의 대입하거나 과거 지급을 자동 재계산하지 않는다. 소속 이력/유효 시점 표현·Caller/공개 계약·저장/UoW·실패/재시도/동시성·AuthSession 철회 방식은 Architecture 후속(PROPOSED)이며 IAM-001 S1/ADR-0004 상태를 변경하지 않는다. Trainer 비활성화·계정 중단/복구/기존 역할 변경 권한을 이번에 확정하지 않는다.

Traceability: PD-004/019/022; PR-005/007/008/010/021/029/030/031; BR-OPS-001/005/008/011/012; BR-PAY-011/012/015/016; NFR-001/004; MB-001/004/005/006/010; ARCH-001/002; 2026-10-12 Trainer 소속 지점(Home Branch) 변경 권한 질문의 1번 답변.

V1 후속: Trainer 과거 Home Branch 이력 오류도 BR-OPS-032의 Master Organization 전용/사유 필수·원본 보존으로 정정한다. 현재 Home으로 과거를 대체하거나 기존 PT 분류/지급/정산을 자동 재계산하지 않는다. 기존 실제 당시 Home/Performed 구분·현재 Home 기반 인가/비용 규칙을 유지하며 영향 수업의 명시적 정정 방식/지급 적용 시점·정정 후 현재 사실/상태/최소 계약은 후속이다. [V 승인](product-decisions.md#review-20261013-v-batch); V-123 미구성·미실행.

<a id="br-ops-014"></a>
## BR-OPS-014 — Trainer 비활성화와 계정 전체 차단의 분리

상태: APPROVED-TO-BE

2026-10-12 사용자 확정(관리자·Trainer 겸임 계정의 Trainer 비활성화 질문의 1번): Trainer 비활성화는 Trainer 역할에 따른 권한만 중단하며, 같은 계정에 독립적으로 부여된 관리자 역할/Scope와 그 범위의 업무는 유지한다. 계정 전체 로그인 차단은 별도 업무다(BR-OPS-014, PD-011/019, PR-005/026, NFR-001/004, ARCH-001/002, MB-001).

인가 경계: Backend는 검증된 현재 Caller의 역할/Scope와 실제 Trainer 활성 상태를 확인한다. 비활성 Trainer 역할만을 근거로 PT 진행 등록이나 담당/개별 지원 Member의 개인정보 조회를 허용하지 않는다. 과거 쿠키·Caller·역할 표시·직접 ID 또는 담당/지원 관계가 남아 있다는 사실로 중단된 권한을 우회할 수 없다. 겸임자의 관리 업무는 독립된 현재 관리자 역할/Scope로 별도 인가하며 Trainer 비활성화를 관리자 Scope 확대 근거로 사용하지 않는다. 기존 Trainer/Operator 단독의 Compensation Setting 접근 금지와 관리자 현재 Home Branch 기반 설정 인가는 유지한다. 비활성 Trainer에게 과거 본인 PT 열람/누락 등록 예외를 새로 부여한 것은 아니다.

계정 수명 경계: Trainer 비활성화만으로 IAM 계정 전체를 차단하거나 모든 AuthSession 철회를 필수 효과로 묶지 않는다. 관리자 권한을 유지하면서 후속 Trainer 업무에는 중단된 권한이 반영되어야 한다. 별도 계정 전체 차단은 모든 역할의 접근 종료를 다루며 Actor는 같은 Organization Master 전용(A8), 마지막 사용 가능 Master 보호는 A9로 확정됐다. 구체 상태 전이·사용 가능 판정/철회·복구 계약은 ARCH-002 후속이다. 기존에 독립적으로 허용된 다른 역할/Scope도 Trainer 비활성화만으로 함께 중단하지 않는 원칙은 기존 역할 독립성/사용자 일관성 지시의 적용이며 새로운 겸임 조합을 승인하지 않는다.

기존 규칙 적용: 일반 저장 완료 이후 후속 인가는 변경된 Trainer 상태를 확인하고 실패하면 요청 직전 상태와 다른 역할/Scope를 보존한다. 중요 상태/권한 변경의 이력·감사에 대상 Trainer/계정·변경 전후 Trainer 상태·Actor/당시 권한·Branch Context·시점을 남기는 경계를 설계한다. 비활성화는 아래 승인된 현재 관리자 Scope에서 처리하며 새 필수 변경 사유나 재활성화/계정 전체 차단 권한을 임의 추가하지 않는다. Trainer/계정 연결·Home Branch·다른 역할/Scope를 비활성화만으로 재연결/이동하지 않는다. 과거 PT 진행/수행 지점·Pass 소비 이력·확정 지급/추가실적·정산 확정본을 삭제/자동 정정하지 않으며, 비활성화만으로 Pass 횟수를 복원하거나 Base Salary를 자동 0원 처리/일할 계산하지 않는다. 기존 인가된 운영자의 과거 이력 조회와 월별 기본급 수동 조정 원칙을 유지한다.

확정된 범위는 겸임 계정의 Trainer 비활성화/전체 계정 차단 분리와 Master Organization 전체·Branch Admin 처리 시점 Trainer 현재 Home Branch 기준의 비활성화 권한이다. Trainer 재활성화의 상태 조합/구체 절차, 재활성화 절차/권한 복구, 관리자 대행 등록의 상세 인가/사실 판정·비활성 Trainer 본인의 직접 등록/이력 열람 예외, 개별 지원 조회 허용 관계의 비활성화/재활성화 시 처리는 후속 결정이다. 구체 상태/역할 저장·Caller 계약·AuthSession 갱신/철회·캐시/처리 중 요청·UoW/동시성은 후속 Architecture이며 ADR-0004 v1 인증 방식은 ACCEPTED/모듈 구체 설계는 PROPOSED를 유지한다.

Traceability: PD-002/011/019/022; PR-005/007/010/021/026/029/030; NFR-001/004; ARCH-001/002, MB-001; SC-011. 실제 업무 구현/검증은 미완료이며 V-65는 계획이다.

2026-10-12 사용자 확정(Trainer 비활성화 권한 질문의 1번): Master Admin은 자신의 Organization 전체 Trainer, Branch Admin은 비활성화 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 단일 관리 Branch인 경우 Trainer를 비활성화할 수 있다. 타 지점 Branch Admin·Operator/Trainer 단독은 불가하며 겸임자는 독립된 현재 관리자 역할/Scope로 판단한다(BR-OPS-014, PD-011/019, PR-005/029/030, NFR-001/004, ARCH-001/002, MB-001).

Backend는 현재 검증된 Caller 역할/Organization·관리 Branch와 실제 대상 Trainer의 Organization/현재 Home Branch를 확인한다. 타 지점 지원 수업/Performed Branch·Member/Pass 담당 관계·Operator 업무 Branch·과거 Trainer 소속이나 계정 발급자였다는 사실만으로 비활성화 권한을 인정하지 않는다. 직접 Trainer ID·위조 role/branch_id/Organization 또는 철회·축소된 권한으로 우회할 수 없다. Trainer 소속 변경 후에는 새 현재 Home Branch로 인가한다.

이 승인은 Trainer 비활성화에 한정한다. 대상이 Master/Branch Admin 겸임자여도 중단하는 것은 Trainer 권한이며 그 계정의 독립 관리자 역할/Scope를 차단·축소하지 않는다. 신규 계정 발급/Trainer Home Branch 변경·재활성화·비밀번호 재설정·전체 계정 차단의 권한으로 확대하지 않는다. 기존 범위 내 직접 처리·저장 후 현재 사실 반영/실패 보존·감사 원칙을 사용자 일관성 지시에 따라 적용하며 별도 Master 승인 대기나 새 필수 사유를 추가하지 않는다. 재활성화 Actor/Scope·다른 활성 역할이 없는 Trainer 계정 로그인·대상 상태/중복 요청·개별 지원 관계/재활성화 처리·비활성 상태의 과거 PT 예외 및 구체 계약/저장/UoW·동시성은 후속이다.

검증 추적: V-66은 위 비활성화 Actor/현재 Home Branch 인가의 계획이며 V-65의 권한 중단/겸임 관리자 유지와 함께 검증한다. 실제 업무 구현·테스트는 미구성·미실행이다.

2026-10-12 사용자 확정(잔여가 남은 담당 이용권이 있는 Trainer의 비활성화 질문의 1번): 잔여가 남은 담당 PT Pass가 있어도 Trainer 비활성화를 허용하며 기존 Assigned Trainer 정보는 유지한다. 비활성화 전에 모든 Pass를 다른 Trainer에게 교체하도록 요구하지 않고 자동 담당 해제/재배정도 하지 않는다. 이후 필요할 때 권한 있는 관리자가 BR-OPS-008의 기존 조건/Scope로 담당을 교체한다(BR-OPS-014, PD-007/011, PR-003/005, NFR-001/004, ARCH-001/002, MB-001/003/005, BR-001).

담당 정보 보존과 업무 인가는 별개다. 비활성 Trainer 역할만으로 담당 Member 목록/검색·직접 ID 상세/전화번호 조회 또는 PT 진행 등록을 허용하지 않는다. 남아 있는 Assigned Trainer ID·담당 이력·과거 쿠키/Caller로 활성 상태 검증을 우회할 수 없으며 겸임자의 독립 관리자 역할/Scope는 기존대로 별도 인가한다. Pass/Member ID·Remaining·발급 조건/Issued Branch와 기존 Member/Trainer Home Branch·과거 실제 수업/수행자/지급/정산은 유지한다. Trainer 중단만으로 Pass를 취소/만료·재발급하거나 횟수를 복원/추가/차감하지 않고 다른 사용 불가 사유를 해제하지 않는다.

후속 담당 교체 권한은 Master Organization 전체/Branch Admin 처리 시점 Member 현재 Home Branch 기준(BR-OPS-008)이며 Trainer 비활성화 권한의 Trainer 현재 Home Branch 기준과 구분한다. 비활성화 Actor가 자동으로 모든 담당 Pass의 교체 권한을 얻지는 않는다. 기존 담당이 비활성이라는 이유만으로 허용된 별도 담당 교체를 막거나 먼저 재활성화하도록 요구하지 않는다. 같은 Pass의 잔여/과거 이력을 유지하고 새 현재 담당의 회원 조회는 실제 현재 Caller/Trainer 상태·관계와 기존 Scope로 검증한다. 새 담당은 활성 Trainer만 허용하며 다른 Pass 상태별 교체 조건은 기존 게이트로 남긴다.

이번에 해결한 것은 잔여가 남은 담당 Pass가 있다는 사실로 Trainer 비활성화를 막지 않는 점과 기존 담당 정보 유지/별도 수동 교체다. 재활성화 Actor/절차·Trainer 단독 로그인·개별 지원 허용 관계 처리·비활성 상태 과거 PT 예외 및 실제 계약/저장/UoW·경합은 후속이다. 담당 정보 보존을 비활성 Trainer의 접근 허용으로 확대하지 않으며 Product OPEN 전체·ADR-0004 v1 인증 방식 ACCEPTED/Architecture 구체안 PROPOSED·IAM-001 S1 범위는 유지한다.

검증 추적: V-67 예정. 실제 업무 구현·테스트는 미구성·미실행이다.

새 담당 지정과 기존 비활성 담당 유지의 구분(2026-10-12, BR-OPS-008): 새로 지정할 대상은 실제 활성 Trainer만 허용한다. 이미 담당인 Trainer가 나중에 비활성화되는 경우는 기존 담당 정보 유지/접근 차단을 적용하며 자동 담당 해제·교체나 사전 일괄 교체를 요구하지 않는다. 새 지정과 비활성화의 확정 순서/현재 상태 검증은 후속 계약·UoW/경합 검증으로 증명한다. 재활성화/비활성 상태의 과거 PT 기록 예외와 IAM/Branch 상태 조합은 별도 게이트다.

2026-10-12 일괄 승인 B1/B2/A8/A9: Trainer 재활성화는 Master 자신의 Organization 전체/Branch Admin 처리 시점 Trainer 현재 Home Branch Scope로 허용한다. 다른 활성 역할 없는 비활성 Trainer는 로그인 불가/재활성화 후 이용하며 관리자 겸임의 독립 역할/관리 Scope는 유지한다. Trainer 업무 재활성화는 계정 전체 DISABLED 복구나 AuthSession·관리 권한의 자동 복구가 아니다. 계정 전체 차단/복구·관리자 비밀번호 재설정은 같은 Organization Master만 수행하며 마지막 사용 가능 Master의 차단/권한 제거는 금지한다. 기존 Pass 담당/개별 지원 관계가 있다는 이유로 비활성 Trainer의 직접 업무/과거 본인 읽기를 허용하지 않는다. 비활성/재활성 자체로 소속/담당·과거 PT/지급·기본급/정산을 변경하지 않는다. 구체 재활성화 절차·개별 지원 기록 수명/계정 상태 조합·기존 인증의 경합/일관성은 후속이다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch).

<a id="br-ops-015"></a>
## BR-OPS-015 — 비활성 Trainer의 비활성화 전 누락 수업 관리자 대행 등록

상태: APPROVED-TO-BE

2026-10-12 사용자 확정(비활성화 전 진행했지만 누락된 PT 수업 등록 질문의 1번): Trainer 비활성화 전에 실제로 수행한 미등록 PT 수업은 관리자가 대행 등록하는 경로를 허용한다. 대상 Trainer의 비활성 상태를 유지하며 잠시 재활성화/본인 로그인·담당 재배정을 선행 요구하지 않는다. 실제 수행 Trainer·실제 수업일과 기존 Pass 잔여/정산 조건을 그대로 적용한다(BR-OPS-015, PD-008/011, PR-008/029/030, BR-OPS-003/008/014, BR-PAY-006/011/012).

대행 인가 기준: Master Admin은 자신의 Organization 전체, Branch Admin은 처리 시점 현재 관리 Branch=실제 수업 Performed Branch인 경우 허용한다. Backend는 현재 검증된 Caller의 역할/Organization·관리 Branch와 실제 Trainer/Member/Pass/Performed Branch의 Organization 관계 및 비활성화 전 수행 사실을 확인한다. 클라이언트가 보낸 role/branch_id/Performed Branch를 인가 근거로 신뢰하거나 실제 진행 지점을 자신의 관리 지점으로 바꿔 권한을 얻을 수 없다. Trainer 현재 Home Branch·Member Home Branch·Pass Issued Branch·과거 관리자 Scope를 대행 기준으로 대신 쓰지 않는다. 권한 축소/관리 지점 변경 뒤의 후속 요청도 현재 Scope로 판단하며 과거 AuthSession/Caller 캐시·직접 ID로 우회하지 않는다. 실제 수행/지점·과거 사실을 확인하는 최소 계약과 시점/확인 불가 정책은 후속이다. 기존 Trainer 비활성화/담당 교체·보상 설정 권한이나 과거 발급자였다는 사실로 대행 권한을 추정하지 않는다. Operator/Trainer 단독에 이 대행 권한을 새로 부여하거나 비활성 Trainer 자신의 직접 등록/회원 개인정보 접근을 복구하지 않는다. 관리자 겸임 요청은 독립 현재 관리자 권한으로 별도 판단하며 전체 계정 차단/재활성화 권한과 구분한다.

실제 수업/수행자와 대행 Actor: 실제 비활성화 전 수행 사실·당시 수행 Trainer/필요 담당 관계·소속/Performed Branch를 확인해야 한다. 기록의 수행/지급 대상은 실제 수업을 한 Trainer이며 입력 관리자를 수행자로 저장하거나 현재 새 담당으로 바꾸지 않는다. 실제 진행일은 과거 수업일, 생성 시점은 이번 실제 기록 생성 시점으로 구분한다. 현재 Pass 담당이 B여도 과거 실제 수행자 A를 이 대행 기록에서 참조할 수 있고 A를 새 Assigned Trainer로 재지정하지 않는다. 새 담당은 활성 Trainer만 가능하다는 BR-OPS-008을 과거 실제 수행자의 역사적 참조에 잘못 적용하지 않는다. 비활성 후 새로운 수업을 허용하거나 수업일/상태를 임의 조작하는 경로가 아니다. 과거 상태/비활성화 시점·날짜 정밀도/사실 확인 불가·추가 증빙/사유 입력의 상세 정책과 표현은 후속이다.

기존 Pass/보상/정산 적용: 실제 수업 당시 이미 발급되고 사용 가능했던 Pass 후보·현재 잔여 > 0·FIXED_AMOUNT 우선/동일 Type FIFO·정상 진행 1회 차감, 수동 만료 전 수업의 늦은 등록 등 기존 조건을 유지한다. 현재 담당이 바뀌었다는 이유로 A에게 재배정/새 발급·횟수 복원 후 등록하도록 요구하지 않으며 실제 Pass 후보의 나머지 관계/상태 조건은 기존 게이트다. 일반/지원 구분은 실제 수업 당시 A Home Branch와 실제 Performed Branch를 비교하고 일반 지급은 이번 기록 생성 시점 A의 적용 Rate/Fixed Amount 및 기존 계산·확정 규칙을 따른다. 관리자/현재 새 담당의 설정이나 수업일 당시 설정으로 임의 대체하지 않는다. 지원 수업 보상 전체는 기존 관리자 수동 Additional Performance이며 대행 수업/Pass 기록만으로 금액을 자동 확정하거나 미입력을 0원으로 대체하지 않는다. 실제 수행 Trainer·진행 월 정산이 미확정이어야 하며 확정 월은 권한 있는 관리자의 기존 해제 → 누락 등록 → 같은 월 재확정/이전 확정본 보존 경로를 따른다. 현재 생성 월로 수업/정산을 이월하거나 기존 확정 지급을 다시 계산하지 않는다. 대행 등록 허용으로 Compensation Setting/Additional Performance/정산 해제·재확정의 별도 권한/공개 범위를 추가하지 않는다.

일관성/감사: 일반 수업의 Pass 선택/차감·PT 기록·필요 지급/이력·필수 감사가 함께 성공/실패하는 기존 경계를 적용하며 지원 수업의 기록/차감과 이후 보상 금액 입력은 기존 두 단계다. 기존 중요 PT/Pass/권한 행위 감사 원칙을 재사용해 실제 수행 Trainer·대행 관리자/당시 권한·Branch Context·실제 수업일/기록 시점·대상 Member/Pass/PT 기록을 구분해 추적한다. 거부/실패 시 요청 직전 비활성 상태/역할·담당/잔여·기존 PT/지급·정산 확정본을 보존한다. 필요한 사실/지급 입력의 확인 실패를 임의 현재 소속/0원 등으로 대체하지 않는다. 현재 보상 설정을 인가된 서버 내부 계산에서 참조하는 것과 Caller에게 민감 설정을 공개하는 것은 별개다.

남은 결정: 대행 인가의 현재 사실 검증·최소 Trainer/Member/Pass 선택 정보·당시 비활성/담당/수행/소속 사실의 확인 방법·날짜/시점 경계·확인 불가/사유·증빙 정책, 나머지 대상/Pass 상태·중복 요청, 계정 수명/개별 지원·재활성화 및 공개 계약/저장/UoW·월 확정/권한·비활성화/차감 경합은 후속이다. 이 경로의 남은 사실 판정/최소 공개 계약·상태 조건 게이트를 임의 기본값으로 구현하지 않는다. Product OPEN 전체 상태·ADR-0004 v1 인증 방식 ACCEPTED/Architecture 구체안 PROPOSED·IAM-001 S1 범위는 유지한다. V-69는 계획이며 실제 업무 구현/테스트는 미구성·미실행이다.

2026-10-12 사용자 확정(비활성화 전 누락 수업 대행 등록의 Branch Admin 기준 질문 1번): Master Admin은 자신의 Organization 전체, Branch Admin은 처리 시점 현재 관리 Branch가 실제 수업의 Performed Branch인 경우에만 대행 등록할 수 있다. Trainer 현재 Home Branch가 다른 지점이어도 실제 수업이 자신의 관리 지점에서 진행됐다면 허용한다. Trainer Home Branch·Member Home Branch·Pass Issued Branch 또는 과거 관리자 Scope만으로 대행 권한을 얻지 않는다(BR-OPS-015).

지점별 수용 사례: A의 현재 Home Branch가 수원이고 비활성화 전 강남에서 실제 수업을 수행했다면 강남 Branch Admin/Master가 대행 등록한다. 수원 Branch Admin은 A의 Home Branch 관리자라는 이유만으로 강남 수업을 대행하지 못한다. 강남 관리자의 대행 허용은 A의 Compensation Setting/Additional Performance/월 정산 조회·해제/재확정 권한을 추가하지 않는다. Trainer 비활성화는 Trainer 현재 Home Branch, Pass 담당 교체는 Member 현재 Home Branch, 이 대행 등록은 실제 Performed Branch 기준으로 각각 검증한다. 기존 실제 수행자/수업일·입력 Actor/생성 시점·현재 비활성/담당 유지·Pass/보상/해당 월 정산·감사 조건을 유지한다. V-70은 계획이며 실제 업무 구현/테스트는 미구성·미실행이다.

<a id="br-ops-016"></a>
## BR-OPS-016 — 기존 업무 데이터가 있는 지점의 비활성화

상태: APPROVED-TO-BE

2026-10-12 일괄 승인 B6: 기존 Member/Trainer/Pass가 남아 있어도 Master Admin은 자신의 Organization의 Branch를 비활성화할 수 있다. 해당 Branch의 신규 배정·새 Pass 발급·새 실제 수업은 Backend에서 차단하고 기존 소속 관계·Pass/잔여·실제 진행/확정 지급·정산/감사 이력은 보존한다. 선행 일괄 이동/이용권 소진을 필수 조건으로 두지 않고 자동 소속 이동·Pass 잔여 소멸·기존 Trainer 일괄 비활성화/계정 차단으로 처리하지 않는다. 클라이언트 상태/직접 Branch ID로 신규 업무 차단을 우회하지 않는다. 소속 지점/발급 지점이 비활성화됐다는 사실만으로 보존된 업무 원본을 삭제하거나 과거 비용 귀속을 옮기지 않는다.

범위/후속: B6 신규 업무 차단에 더해 G1–G5의 비활성 이후 처리는 아래 승인 규칙을 따른다. Member 새 소속 이동 대상은 활성 Branch만이라는 기존 결정을 유지한다. 지점 재활성화의 상세 절차·과거 운영/소속/담당/수행 사실 확인 불가/정정·미결정 신규 배정/다른 상태 조합과 공개 계약/저장/UoW·동시 요청은 MB-008 및 관련 OPEN에 남으며 기술안은 PROPOSED/미검증이다. PR-004/020/030, NFR-001/002/004. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch).

2026-10-12 G1–G5 모두 1번 승인 — 비활성 지점의 기존 업무 처리:

- G1: 계정/역할이 유효하면 기존 Scope 안의 로그인·조회는 허용한다. Branch 비활성은 계정 전체 차단/Trainer 비활성과 별개이며 철회·만료된 인증/역할을 복원하지 않는다. 새로운 자료/보상 설정·감사 읽기 권한은 생기지 않는다.
- G2: 비활성화 전에 실제로 진행한 수업은 지점 재활성화 없이 기존 업무별 권한으로 누락 등록·정정·취소할 수 있다. 실제 시작/당시 지점 운영·담당/수행/Pass 조건을 확인하고 기존 사유/이력·취소 Pass 복원/보상 무효·참가자 취소 후 재등록·Performed Branch 값 Master 전용 규칙을 유지한다. Trainer 직접 소급 등록은 본인 수행/Allowed PT Scope·미확정 실제 진행 월 조건, 비활성 Trainer는 관리자 대행 경로를 따른다. Branch Admin의 PT 정정/취소·대행은 실제 Performed Branch, 영향받는 확정 Trainer/월 해제·재확정은 각 처리 시점 Trainer 현재 Home Branch로 별도 인가한다. 이전 확정본을 보존하고 생성 시점 일반 지급 규칙을 유지한다. 비활성 기간의 새 실제 수업을 허용하지 않는다.
- G3: Issued Branch가 비활성이어도 다른 활성 Performed Branch에서 기존 Pass를 사용할 수 있다. 현재 인가/조직·Pass 가용성/잔여 > 0·기존 우선순위를 검증하고 정상 수업 1회에 잔여 1회를 차감한다. Issued Branch·발급 조건/과거 이력은 유지하며 수동 만료/잔여 0 등 다른 사용 불가 사유를 면제하지 않는다.
- G4: Member/Trainer Home Branch가 비활성이어도 다른 활성 지점에서 기존 담당·개별 지원 등 허용 조건을 충족하면 수업할 수 있다. Trainer 자체는 활성 상태여야 한다. Home Branch 변경을 선행 요구하지 않고 실제 수업 당시 Trainer Home Branch와 Performed Branch로 일반/지원을 구분한다. 지원 보상 전부를 관리자 입력 Additional Performance로 처리/일반 지급 중복 합산 금지·미입력 지원 보상 해당 월 확정 차단·민감 보상 설정 접근 제한을 유지한다. 신규 배정 조건을 일괄 허용하지 않는다.
- G5: 비활성 출발 지점에서 같은 Organization의 활성 지점으로 명시적인 소속 이동을 허용한다. Member는 Master 또는 변경 전 현재 Home Branch 관리 Branch Admin, Trainer Home Branch·Operator 업무 Branch는 Master만 가능하다. 출발 지점 재활성화 없이 기존 즉시 적용/실패 보존·감사·독립 역할/담당/지원/Pass/과거 지급·정산 보존을 적용한다. 과거 소속/수행 지점·비용 귀속을 소급 변경하거나 계정/Trainer 상태·회수 역할을 복구하지 않는다.

수용 사례(문서): 수원점 비활성화 후 기존 수원 발급 Pass 잔여 5회로 강남점에서 허용된 수업을 수행하면 Issued Branch는 수원/Remaining은 4회다. 활성인 수원 Home Trainer가 강남에서 수업하면 기존 지원 보상 규칙을 따른다. 수원점의 비활성화 전 누락 수업은 기존 권한/실제 시점·Pass·정산 조건으로 처리하지만 비활성 기간의 새 수원 수업은 거부한다. 수원 관리 Branch Admin은 현재 수원 Home Member를 활성 강남으로 옮길 수 있고, Trainer/Operator 소속 이동은 Master에게만 허용한다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). V-85–89는 미구성·미실행 후속 검증 계획이다.

<a id="br-ops-017"></a>
## BR-OPS-017 — Organization 공통 업무 시간대

상태: APPROVED-TO-BE

2026-10-12 일괄 승인 B7: 실제 PT 진행의 업무 날짜와 월 정산의 소속 월은 Organization 공통 한국 시간(Asia/Seoul)으로 판단한다. 같은 실제 시점을 지점/Actor·기기별 시간대로 서로 다른 월에 집계하지 않는다. 월별 집계의 시작/종료도 이 업무 시간대의 달력 월을 따른다. 예를 들어 UTC 9월 30일 15:00은 한국 시간 10월 1일 00:00으로 10월 경계다. 기록 생성 시점과 실제 수업일은 구분하고, 생성 월로 과거 실제 수업 월을 대체하지 않는 기존 규칙을 유지한다.

C9/I1 승인: 완료된 실제 수업의 시작 날짜와 시각을 기록하고 그 시작 시점의 Asia/Seoul 날짜/월을 사용한다. 실제 시작과 기록 생성 시점을 구분한다. 시각을 모르면 확인한 뒤 등록하며 임의 시각이나 ‘시각 미상’ 기록·관리자 대행 예외를 허용하지 않는다. 시각 정밀도·비활성/담당/소속 이력 경계·소급 정정과 UTC 저장 여부/형식·쿼리/잠금은 후속 설계다. 시간대/시각 확인 정책으로 과거 확정 지급/정산을 자동 재계산하거나 생성 시점 보상 규칙을 수업일 당시 보상 규칙으로 바꾸지 않는다. PR-008/010, NFR-012, BR-008, MB-010. [2026-10-12 I 일괄 승인](product-decisions.md#review-20261012-i-batch).

2026-10-12 C9 승인 근거: [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch). 미래 예약/일정 등록 기능을 추가하거나 일반 지급의 생성 시점 설정 적용을 실제 수업 시점 설정으로 변경하지 않는다.

2026-10-12 K1=1: 실제 시작 날짜/시각 오류는 기존 PT 원본 취소 후 올바른 시점으로 재등록한다(BR-OPS-023). I1 시각 확인/시각 미상 불가·Asia/Seoul 실제 날짜/월·과거 원본 보존을 유지하며 새 일반 지급만 재등록 생성 시점 설정을 적용한다. [2026-10-12 K 일괄 승인](product-decisions.md#review-20261012-k-batch).

<a id="br-pay-014"></a>
## BR-PAY-014 — 월 고정 기본급

Status: APPROVED

Trainer별 월 고정 Base Salary를 지원한다. 일반 Base Salary 설정은 관리자가 지정한 적용 시작 월부터 다음 기본급 변경의 적용 시작 월 전까지 매월 계속 적용한다. 적용 종료 월을 지정하거나 같은 금액을 매월 다시 등록할 필요는 없다. 예: A 2,500,000원/월. Product나 Session마다 붙는 금액이 아니며 입퇴사 일할·근무일수·휴직 기반 자동 급여 계산은 v1 제외다. 입사·퇴사·휴직이 있는 달의 적용 기본급은 관리자가 해당 Trainer·월의 금액을 직접 지정한다. 예를 들어 월 기본급 설정이 2,500,000원이어도 해당 월만 1,500,000원을 적용할 수 있으며, 이 지정으로 현재·미래 기본급 설정과 다른 월 정산은 변경하지 않는다. 월별로 수동 지정한 기본급은 이후 일반 기본급 설정이 변경되어도 유지한다. 일반 설정 변경의 미확정 정산 자동 반영은 수동 지정이 없는 월에 적용하며, 수동 지정 월의 금액을 바꾸려면 관리자가 해당 월 금액을 직접 수정한다. 미확정 월의 기본급을 최초 수동 지정하거나 다시 수정할 때 모두 사유가 필수다. 사유가 없는 요청은 거부하고 요청 직전의 수동 지정 여부·적용 금액·월 합계를 유지한다. 대상 Trainer·월, 지정/수정 전후 금액·사유·처리자·처리 시점을 이력으로 남긴다. 미확정 월 기본급의 최초 수동 지정·수정은 Master Admin의 Organization 전체, Branch Admin의 각 처리 시점 대상 Trainer 현재 Home Branch가 관리 Branch와 일치하는 범위에서 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 직접 처리한다. 추가 사용자 확정(2026-10-11): 해당 월 기본급은 권한 있는 관리자가 사유를 남기면 0원으로 명시적으로 수동 지정할 수 있다. 수동 지정한 0원은 미입력과 구분하며, 미입력이나 누락된 일반 설정을 자동으로 0원으로 대체하지 않는다. 해당 월 기본급에만 적용하고 다른 유효 지급·추가실적은 기존 규칙대로 합산한다. 미래 시작 월 범위/최초 시작 월 이전 월 처리는 아래 AA1/AA2로 해결됐다. 월별 입력 상한·다른 월/역사 사실·검증/저장 계약 등 BR-012/BR-010의 잔여는 OPEN이다. 현재 기본급 변경으로 이미 확정된 과거 정산의 적용 기본급과 합계를 자동 변경하지 않는다. 별도 과거 정정 업무와 자동 소급은 구별한다. 이력·결과 보존 구현은 Architecture 결정이다.

2026-10-10 사용자 확정(기본급 적용 시작 월 질문의 1번 답변): Base Salary를 변경할 때 권한 있는 관리자가 적용 시작 월을 명시적으로 지정한다. 변경한 달 또는 다음 달로 일괄 자동 지정하지 않는다. 예를 들어 10월 10일에 기본급을 2,500,000원에서 2,700,000원으로 변경하면 관리자가 10월 또는 11월 등 적용 시작 월을 선택한다. 기존 BR-PAY-010의 관리 범위·본인 설정 허용 조건·별도 승인 없음·필수 감사는 유지한다. 이미 확정된 월 정산의 적용 기본급과 합계는 자동 변경하지 않는다. 당시 미결정이었던 이미 작성된 미확정 정산의 반영 방식은 아래 후속 사용자 결정으로 확정했다. 미확정인 과거 월의 지정 허용은 아래 후속 사용자 결정으로 확정했다. 당시 미결정이었던 기본급 오류 정정과 현재·예정 기본급 설정의 관계는 아래 후속 사용자 결정으로 해당 월 정산에만 영향을 주는 것으로 확정했다. 미래 적용 월의 입력 범위 등 남은 정책은 BR-012 OPEN이다. Rate/Fixed Amount의 관리자 저장 완료 이후 신규 Session 적용 규칙과 구별한다. 적용 월·이력의 저장 구조와 월 정산 입력 계약은 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(이미 작성된 미확정 정산의 기본급 변경 반영 질문의 1번 답변): Base Salary 변경이 적용되는 월의 이미 작성된 미확정 정산에는 변경한 기본급과 그에 따른 월 합계를 자동 반영한다. 관리자가 정산에서 별도의 반영 작업을 실행해야 하는 절차는 두지 않는다. 예를 들어 10월 미확정 정산의 기본급이 2,500,000원이고 관리자가 10월부터 2,700,000원으로 변경하면, 그 미확정 정산의 적용 기본급은 2,700,000원이 되고 나머지 유효 구성 금액이 같을 때 합계는 200,000원 증가한다. 적용 시작 월 전의 정산과 이미 확정된 정산은 이 변경으로 자동 갱신하지 않는다. 기존 보상 설정 권한·별도 승인 없음·필수 감사와 과거 확정본 보존은 유지한다. 기본급 자동 반영은 정산 자동 확정이 아니며 미입력 지원 수업 등 기존 확정 차단 조건도 유지한다. Rate/Fixed Amount나 확정 Session Payment를 재계산하는 결정이 아니다. 지원 수업 보상 정정을 위한 확정 해제만을 이유로 현재 기본급을 과거 정산에 자동 적용하지 않는 기존 경계도 유지한다. 자동 반영의 저장/조회 방식과 기본급 변경·정산 확정 경합의 구체 일관성 전략은 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(과거 월을 기본급 적용 시작 월로 지정할 수 있는지 질문의 1번 답변): 아직 확정하지 않은 과거 월도 Base Salary 적용 시작 월로 지정할 수 있다. 예를 들어 10월에 기본급을 2,500,000원에서 2,700,000원으로 변경하면서 아직 미확정인 9월을 적용 시작 월로 지정할 수 있으며, 해당 변경이 적용되는 기존 9월 미확정 정산의 기본급·합계는 앞서 확정한 자동 반영 규칙을 따른다. 현재 월 이후로만 지정하도록 제한하지 않는다. 기존 관리 범위·별도 승인 없음·필수 감사와 적용 시작 월 전/확정된 정산의 자동 변경 금지를 유지한다. 과거 일반 Session Payment를 재계산하거나 정산을 자동 확정하지 않는다. 당시 미결정이었던 확정된 과거 월의 기본급 오류 정정 경로는 아래 후속 사용자 결정으로 해당 월 확정 해제·기본급 정정·동일 월 재확정 및 이전 확정본 보존으로 확정했다. 당시 미결정이었던 기본급 오류 정정과 현재·예정 기본급 설정의 관계는 아래 후속 사용자 결정으로 해당 월 정산에만 영향을 주는 것으로 확정했다. 미래 적용 월의 입력 범위 및 적용 월/이력의 저장·경합 처리 상세도 후속 검토 대상이다.

2026-10-10 사용자 확정(이미 확정된 월의 기본급 오류 처리 질문의 1번 답변): 이미 확정된 월 정산의 적용 기본급에 오류가 있으면 해당 Trainer·월의 확정을 해제하고 그 월의 기본급을 정정한 뒤 동일 월 정산을 재확정한다. 이전 확정본의 적용 기본급·구성 금액·합계를 이력으로 보존하고 재확정본과 구분한다. 예를 들어 9월 기본급을 2,500,000원으로 확정했지만 2,700,000원이어야 했다면 9월 확정 해제 → 9월 적용 기본급 2,700,000원으로 정정 → 9월 재확정으로 처리한다. 나머지 유효 구성 금액이 같으면 재확정 합계는 200,000원 증가하고, 이전 기본급 2,500,000원이 반영된 확정본은 보존한다. 현재 Base Salary 설정 변경에 따른 자동 갱신과 구별되는 명시적 오류 정정 업무다. 과거 일반 Session Payment는 현재 Rate/Fixed Amount로 재계산하지 않으며 PT 진행 기록·Pass 차감을 재실행하지 않는다. 재확정에도 해당 Trainer·월의 미입력 지원 수업 차단 등 승인된 확정 조건을 적용한다. 이번 결정은 정정 순서와 이전 확정본 보존에 한정한다. 당시 미결정이었던 기본급 오류 정정의 확정 해제·재확정 권한과 별도 Master 승인 여부는 아래 후속 사용자 결정으로 확정했다. 당시 미결정이었던 확정 해제·해당 월 기본급 수정의 사유 필수 여부는 아래 후속 사용자 결정으로 확정했다. 당시 미결정이었던 기본급 오류 정정과 현재·예정 기본급 설정의 관계는 아래 후속 사용자 결정으로 해당 월 정산에만 영향을 주는 것으로 확정했다. 기존 보상 설정 권한과 지원 수업 보상 정정에 승인된 권한·승인·사유 정책은 각각 기존 범위를 유지한다. 구체 저장 모델·공개 계약·업무 트랜잭션·경합 전략은 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(기본급 오류 정정을 직접 처리할 권한 질문의 1번 답변): 기본급 오류 정정의 확정 해제·재확정은 Master Admin에게 Organization 전체, Branch Admin에게 각 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 처리한다. 수업의 Performed Branch나 과거 Home Branch만을 근거로 다른 소속 Trainer의 위 정정 권한을 얻지 않는다. Branch Admin은 확정 해제와 재확정 등 각 업무 처리 시점에 현재 Home Branch를 다시 검증하며 이전 소속만으로 권한을 유지하지 않는다. 관리자 권한 없는 Operator·Trainer는 이 작업을 수행할 수 없다. 해당 Trainer·월의 확정 해제 → 해당 월 적용 기본급 정정 → 동일 월 재확정, 이전 확정본과 정정 이력·감사 보존 및 재확정 시 미입력 지원 수업 차단 등 승인된 조건은 유지한다. 이번 결정은 기본급 오류 정정의 관리 역할/대상 범위와 별도 Master 승인 없음에 한정한다. 최초 월 정산 확정 권한과 전체 정산 공개 범위(MB-006)는 이번에 확정하지 않는다. 당시 미결정이었던 기본급 오류 정정과 현재·예정 기본급 설정의 관계는 아래 후속 사용자 결정으로 해당 월 정산에만 영향을 주는 것으로 확정했다. 당시 미결정이었던 확정 해제·해당 월 기본급 수정의 사유 필수 여부는 아래 후속 사용자 결정으로 확정했다. 구체 인증/인가 계약·저장·경합 처리 전략은 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(기본급 오류 정정 사유 질문의 1번 답변): 확정된 월의 기본급 오류 정정에서 확정 해제와 해당 월 기본급 수정 모두 사유가 필수다. Master Admin·Branch Admin 및 관리 범위 안 본인 건에 동일하게 적용한다. 해제 사유·해제자·시점과 변경 전후 기본급·수정 사유·수정자·시점을 이력으로 남긴다. 사유가 없는 확정 해제 요청과 사유가 없는 해당 월 기본급 수정 요청은 각각 해당 작업을 거부하며, 요청 직전의 상태·금액·기존 확정본을 변경하지 않는다. 기존 Master Organization 전체/Branch Admin 각 처리 시점 대상 Trainer 현재 Home Branch 기준 인가와 관리 범위 안 본인 건 허용·별도 Master 승인 없음은 유지한다. 해당 Trainer·월 확정 해제 → 해당 월 적용 기본급 정정 → 동일 월 재확정 경로, 이전 확정본과 정정 이력·감사 보존, 재확정 시 미입력 지원 수업 차단 등 승인된 조건도 유지한다. 이번 결정은 확정된 월의 기본급 오류 정정에 한정한다. 일반 보상 설정 변경은 BR-PAY-010의 기존 감사 요건을 따른다. 당시 미결정이었던 기본급 오류 정정과 현재·예정 기본급 설정의 관계는 아래 후속 사용자 결정으로 해당 월 정산에만 영향을 주는 것으로 확정했다. 미래 적용 월의 입력 범위 등 남은 정책은 BR-012 OPEN이다. 사유 입력 화면·저장 형식·업무 계약/트랜잭션의 구체 구성은 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(과거 월 정정이 다른 월에 미치는 영향 질문의 1번 답변): 기본급 오류 정정은 대상 Trainer의 해당 월 정산에만 적용하며 현재·미래 기본급 설정과 다른 월 정산은 유지한다. 지속적인 기본급 변경은 별도로 적용 시작 월을 지정하는 기존 흐름을 따른다. 예를 들어 9월 기본급을 2,500,000원에서 2,700,000원으로 정정하면 9월 재확정에는 명시적으로 정정한 2,700,000원을 사용하고 이전 확정본은 보존한다. 이 정정만으로 현재 기본급 설정, 미래에 적용하도록 지정한 설정 또는 10월 등 다른 월 정산의 적용 기본급·합계를 바꾸지 않는다. 10월 미확정 정산이 2,500,000원인 예에서는 그 금액을 그대로 유지한다. 일반 보상 설정 변경의 적용 시작 월 지정 및 적용되는 기존 미확정 정산 자동 반영은 별도의 명시적 변경 업무로 유지한다. 기존 Master Organization 전체/Branch Admin 각 처리 시점 Trainer 현재 Home Branch 기준 인가·관리 범위 안 본인 건 허용·별도 Master 승인 없음, 확정 해제와 해당 월 기본급 수정의 사유 필수, 이전 확정본·전후 값·처리자/시점 이력·감사 및 재확정 조건은 유지한다. 월 정산의 정정 기본급 보존과 설정 입력 계약·저장 모델·경합 처리는 후속 Architecture 검토 대상이며 이번 결정으로 기술안을 승인하지 않는다.

2026-10-10 사용자 확정(입사·퇴사·휴직이 있는 달의 기본급 질문의 1번 답변): 입사·퇴사·휴직이 있는 달의 적용 기본급은 관리자가 해당 Trainer·월의 금액을 직접 지정한다. 예를 들어 월 기본급 설정이 2,500,000원이어도 해당 월만 1,500,000원을 적용할 수 있으며, 이 지정으로 현재·미래 기본급 설정과 다른 월 정산은 변경하지 않는다. 해당 월 정산의 기본급 구성과 월 합계는 직접 지정한 적용 금액을 사용하며, 입퇴사 일할·근무일수·휴직 기반 자동 급여 계산은 v1에서 제공하지 않는다. 지속적인 기본급 변경은 기존 적용 시작 월 지정 업무로 구분한다. 월별 금액 지정만으로 정산을 자동 확정하거나 미입력 지원 수업 등 승인된 확정 조건을 우회하지 않는다. 이미 확정된 월의 금액을 변경하려면 기존 해당 월 확정 해제 → 기본급 정정 → 동일 월 재확정 경로와 승인된 권한·사유·이력/감사·이전 확정본 보존 조건을 따른다. 과거 일반 Session Payment와 PT 진행 기록·Pass 차감은 재계산/재실행하지 않는다. 이번 결정은 월별 수동 지정 방식과 해당 월에 한정된 효과를 확정한 것이며, 미확정 월 수동 지정의 입력 한도를 새로 확정하지 않는다. 당시 미결정이었던 미확정 월 수동 지정의 역할/대상 범위와 별도 승인 여부는 아래 후속 사용자 결정으로 Master Organization 전체/Branch Admin 처리 시점 Trainer 현재 Home Branch 기준·관리 범위 안 본인 포함·별도 Master 승인 없음으로 확정했다. 당시 미결정이었던 최초 수동 지정·수정의 사유 필수 여부는 아래 후속 사용자 결정으로 모두 필수로 확정했다. 당시 미결정이었던 수동 지정 뒤 일반 기본급 설정 변경 시 우선순위는 아래 후속 사용자 결정으로 수동 지정 금액 유지·수동 지정 없는 월만 자동 반영하도록 확정했다. 저장 모델·공개 계약·감사 구성·경합 전략은 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(수동 지정 금액과 이후 설정 변경의 우선순위 질문의 1번 답변): 월별로 수동 지정한 기본급은 이후 일반 기본급 설정이 변경되어도 유지한다. 일반 설정 변경의 미확정 정산 자동 반영은 수동 지정이 없는 월에 적용하며, 수동 지정 월의 금액을 바꾸려면 관리자가 해당 월 금액을 직접 수정한다. 예를 들어 미확정인 10월 적용 기본급을 1,500,000원으로 직접 지정한 뒤 일반 기본급 설정을 10월부터 2,500,000원에서 2,700,000원으로 변경하면, 일반 설정은 2,700,000원으로 변경하되 10월의 수동 지정 기본급은 1,500,000원을 유지한다. 다른 유효 구성 금액이 같다면 해당 10월 정산의 합계도 이 설정 변경만으로 바뀌지 않는다. 같은 변경의 적용 대상인 수동 지정 없는 미확정 월에는 일반 설정의 2,700,000원과 그에 따른 합계를 기존 규칙대로 자동 반영한다. 월별 수동 지정 자체로 현재·미래 기본급 설정이나 다른 월을 변경하지 않는 기존 경계와 구분한다. 이미 확정된 월 정산의 자동 변경 금지·정정 시 해제/정정/재확정과 이전 확정본 보존, 미입력 지원 수업 등 확정 조건 및 정산 자동 확정 금지는 유지한다. Rate/Fixed Amount 적용이나 과거 일반 Session Payment·PT 진행 기록·Pass 차감 처리도 변경하지 않는다. 이번 결정으로 미확정 월 수동 지정의 입력 한도 또는 자동 반영으로 복귀하는 기능을 승인하지 않는다. 당시 미결정이었던 미확정 월 수동 지정의 역할/대상 범위와 별도 승인 여부는 아래 후속 사용자 결정으로 Master Organization 전체/Branch Admin 처리 시점 Trainer 현재 Home Branch 기준·관리 범위 안 본인 포함·별도 Master 승인 없음으로 확정했다. 당시 미결정이었던 최초 수동 지정·수정의 사유 필수 여부는 아래 후속 사용자 결정으로 모두 필수로 확정했다. 수동 지정 여부와 월 적용 금액을 보존하는 저장 모델·공개 계약·감사·설정 변경/월 확정 경합 전략은 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(미확정 월의 기본급 수동 지정 사유 질문의 1번 답변): 미확정 월의 기본급을 최초 수동 지정하거나 다시 수정할 때 모두 사유가 필수다. 사유가 없는 요청은 거부하고 요청 직전의 수동 지정 여부·적용 금액·월 합계를 유지한다. 대상 Trainer·월, 지정/수정 전후 금액·사유·처리자·처리 시점을 이력으로 남긴다. 예를 들어 월 기본급 설정 2,500,000원과 별개로 중도 입사 월을 1,500,000원으로 최초 지정할 때도 사유를 남기며, 이후 해당 월 금액을 다시 수정할 때도 수정 사유를 남긴다. 이 업무를 수행할 권한이 있는 관리자에게 동일하게 적용하는 사유 요건이며 이번 결정만으로 새로운 인가 범위나 추가 승인 절차를 정하지 않는다. 월별 수동 지정으로 현재·미래 기본급 설정과 다른 월 정산을 변경하지 않는 경계, 이후 일반 설정 변경에도 수동 지정액 유지·수동 지정 없는 미확정 월만 자동 반영, 정산 자동 확정 금지 및 미입력 지원 수업 등 승인된 확정 조건을 유지한다. 이미 확정된 월의 변경은 기존 해제/정정/재확정과 사유 필수·인가·이력/감사·이전 확정본 보존 조건을 따른다. 일반 Rate/Fixed Amount/Base Salary 설정 변경 전체에 사유 필수를 새로 적용하는 결정이 아니며 그 업무의 기존 감사 요건을 유지한다. 당시 미결정이었던 미확정 월 수동 지정의 역할/대상 범위와 별도 승인 여부는 아래 후속 사용자 결정으로 Master Organization 전체/Branch Admin 처리 시점 Trainer 현재 Home Branch 기준·관리 범위 안 본인 포함·별도 Master 승인 없음으로 확정했다. 입력 제약은 BR-012 등 관련 OPEN을 따르고, 사유 저장 형식·월별 적용 금액/수동 지정 상태·감사 이력의 공개 계약과 트랜잭션/경합 전략은 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(미확정 월 기본급 수동 지정·수정의 처리 권한 질문의 1번 답변): 미확정 월 기본급의 최초 수동 지정·수정은 Master Admin의 Organization 전체, Branch Admin의 각 처리 시점 대상 Trainer 현재 Home Branch가 관리 Branch와 일치하는 범위에서 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 직접 처리한다. 최초 수동 지정과 이후 수정 요청마다 서버에서 현재 권한·관리 Scope·대상 Trainer의 현재 Home Branch를 검증한다. 예를 들어 Trainer가 수원 Home Branch에서 강남으로 이동한 뒤의 미확정 월 수동 지정·수정은 현재 강남 Branch Admin의 관리 범위에서 허용하며, 별도 Master 권한 없는 이전 수원 Branch Admin에게는 과거 소속만으로 허용하지 않는다. Performed Branch가 자기 지점이라는 이유로 다른 Home Branch Trainer의 월 기본급을 지정/수정할 권한을 얻지 않는다. 관리자 권한 없는 Operator·Trainer는 수행할 수 없으며 직접 ID·위조 Branch Context로 우회할 수 없다. Master·Branch Admin과 관리 범위 안 본인 건 모두 기존 최초 지정/수정 사유 필수·사유 누락 요청 변경 없이 거부·전후 금액/사유/처리자/시점 이력 및 감사 원칙을 따른다. 월별 지정으로 현재·미래 설정과 다른 월 정산을 변경하지 않으며 이후 일반 설정 변경에도 수동 지정액을 유지한다. 이 권한으로 전체 정산 조회나 최초 월 정산 확정 권한을 자동 부여하지 않으며 MB-006과 남은 정산 확정 정책은 OPEN을 유지한다. 확정된 월의 변경은 기존 해제/정정/재확정 경로와 승인 조건을 따른다. 미래 적용 월의 입력 범위·금액 입력 제약은 BR-012/BR-010의 남은 질문이며 구체 인가 계약·저장 모델·필수 감사/UoW·소속 이동 및 월 확정 경합 처리는 후속 Architecture 검토 대상이다.

2026-10-11 사용자 확정(해당 월 기본급의 0원 수동 지정 허용 질문의 1번 답변): 해당 월 기본급은 권한 있는 관리자가 사유를 남기면 0원으로 명시적으로 수동 지정할 수 있다. 수동 지정한 0원은 미입력과 구분하며, 미입력이나 누락된 일반 설정을 자동으로 0원으로 대체하지 않는다. 해당 월 기본급에만 적용하고 다른 유효 지급·추가실적은 기존 규칙대로 합산한다. 예를 들어 해당 월 기본급을 0원으로 수동 지정하고 유효 일반 Session Payment가 1,200,000원, 유효 Additional Performance가 150,000원이면 월 합계는 1,350,000원이다. 0원 지정으로 PT 진행 기록·Pass 차감을 취소/복원하거나 다른 지급·실적을 0원으로 변경하지 않는다. 기존 Master Organization 전체/Branch Admin 각 처리 시점 Trainer 현재 Home Branch 기준 인가·관리 범위 안 본인 허용·별도 Master 승인 없음, 최초 수동 지정/수정 사유 필수 및 사유 누락 요청 변경 없이 거부·전후 금액/사유/처리자/시점 이력과 감사 원칙을 동일하게 적용한다. 이 월별 지정으로 현재·미래 일반 기본급 설정과 다른 월 정산을 변경하지 않으며, 이후 일반 설정이 바뀌어도 해당 월의 명시적 수동 지정 0원을 유지한다. 수동 지정하지 않은 월은 기존 일반 설정 적용 규칙을 따른다. 정산 자동 확정이나 미입력 지원 수업 등 기존 확정 차단 조건의 해소를 뜻하지 않으며, 이미 확정된 월의 금액 변경은 기존 해제/정정/재확정과 이전 확정본 보존 조건을 따른다. 이번 허용은 월별 수동 적용 기본급에 한정하며 일반 Compensation Setting의 Base Salary/Rate/Fixed Amount, Product 가격·일반 Session Payment 또는 다른 추가실적의 0원 허용으로 확대하지 않는다. 음수·상한·정밀도·누락값 처리 등 나머지 입력 정책과 미래 적용 월 범위는 BR-010/BR-012 OPEN을 유지한다. 명시적 0원·미입력·수동 지정 여부를 구분하는 저장/조회 계약 및 감사·UoW·경합 전략은 후속 Architecture 검토 대상이다.

2026-10-11 사용자 명확화(기본급 변경 후 다음 변경까지 유지): 일반 Base Salary 설정은 관리자가 지정한 적용 시작 월부터 다음 기본급 변경의 적용 시작 월 전까지 매월 계속 적용한다. 적용 종료 월을 지정하거나 같은 금액을 매월 다시 등록할 필요는 없다. 예를 들어 10월부터 2,700,000원으로 변경하고 이후 변경이 없으면 11월·12월 이후에도 매월 2,700,000원을 적용한다. 이후 12월에 다시 변경하여 12월부터 2,800,000원을 적용하도록 정하면 10월·11월은 2,700,000원, 12월부터는 다음 변경 전까지 매월 2,800,000원이다. 이는 일반 기본급 설정의 지속 적용 원칙이며, 입사·퇴사·휴직 등으로 특정 월 금액을 수동 지정하는 기존 예외는 해당 월에만 적용한다. 일반 설정이 10월부터 2,700,000원이고 10월만 1,500,000원으로 수동 지정한 경우 10월은 1,500,000원, 수동 지정이 없는 11월부터는 일반 설정의 2,700,000원을 적용한다. 기존 수동 지정액 유지·미확정 정산 자동 반영·확정 정산의 자동 변경 금지·권한/사유/이력/감사 규칙은 유지한다. 이번 명확화는 금액의 지속 적용에 관한 것이며, 변경을 얼마나 먼 미래의 시작 월로 미리 등록할 수 있는지에 대한 앞선 선택지의 답변으로 간주하지 않는다. 해당 입력 범위와 나머지 금액 입력 제약은 BR-012/BR-010 OPEN을 유지한다. 구체 유효 월 이력·조회 계약·저장 모델·경합 전략은 후속 Architecture 검토 대상이다.

2026-10-11 사용자 확정(월중 지점 이동 시 기본급 비용 귀속 질문의 1번 답변): 월중 Trainer 지점 이동이 있는 달의 해당 월 적용 기본급 비용은 대상 월의 월말 Home Branch 한 곳에 전액 귀속한다. 10월 중 수원점에서 강남점으로 이동했고 10월 적용 기본급이 2,500,000원이라면 강남점 비용으로 2,500,000원을 집계한다. 기본급 지급액을 변경하거나 이동 전후 지점으로 분할/일할 계산하지 않으며, Trainer 월 정산에는 기존대로 기본급을 한 번만 합산한다. 해당 월 수동 지정 금액이 있으면 그 적용 금액을 사용한다. 예를 들어 10월 수동 기본급이 1,500,000원이면 강남점 기본급 비용도 1,500,000원이며 현재 일반 설정액으로 대체하지 않는다. 명시적 사유를 남긴 월별 수동 기본급 0원과 미입력의 구분도 유지한다. 이후 월의 소속 이동만으로 과거 대상 월말 소속에 따른 비용 귀속을 바꾸지 않는다. 기존 현재 Home Branch 기준의 입력·정정·확정·조회 권한과 과거 확정본 보존은 유지한다. 비용 귀속 지점은 인가의 관리 Branch와 별개이며, 귀속 사실만으로 과거/다른 소속 Trainer에 대한 처리·전체 정산 열람 권한을 부여하지 않는다. 일반 기본급의 적용 시작 월부터 다음 변경까지 지속 적용·월별 수동 지정 우선·확정 월 정정의 해제/정정/재확정은 기존 규칙을 따른다. 이 결정은 이동월 기본급의 내부 비용 집계 기준이며 일반 지급·지원 수업 외 추가실적의 귀속, 월말 소속을 식별할 수 없는 상황의 처리, 지점별 비용 보고의 공개/집계 상세는 관련 OPEN을 유지한다. 소속 이동의 적용 시점/이력과 월 경계, 구체 저장·조회·갱신/버전 전략은 후속 검토 대상이다.

Traceability: 2026-10-10 사용자 기본급 적용 시작 월 지정·수동 지정 없는 기존 미확정 정산 자동 반영·미확정 과거 월 지정 허용·확정 월 기본급 오류의 해제/정정/재확정과 이전 확정본 보존·해당 정정의 현재 Home Branch 관리자 권한과 별도 Master 승인 없음·확정 해제/해당 월 기본급 수정 사유 필수·정정의 해당 월 한정·입퇴사/휴직 월의 관리자 수동 금액 지정·일반 설정 변경 시 수동 지정액 유지·미확정 월 최초 수동 지정/수정 모두 사유 필수·현재 Home Branch 관리자 범위의 직접 수동 지정/수정과 본인 건 포함·별도 Master 승인 없음 확정; 2026-10-11 사용자 월별 수동 기본급의 사유 필수 0원 허용·일반 기본급의 적용 시작 월부터 다음 변경까지 지속 적용 확정; PD-009/012; PR-007/010; BR-PAY-010.

2026-10-13 AA1/AA2=1 추가: 최초 일반 기본급 적용 시작 월보다 이른 정산 월에 유효 수업/추가실적이 있으면, 기존 현재 Master Organization/Trainer 현재 Home Branch Admin 범위에서 사유를 남겨 해당 월 기본급을 명시적으로 수동 지정한다. 명시0원 허용/미입력 자동0 금지·월별 지정/감사·확정/정정 조건을 유지하고 최초 시작 월 이후 일반 설정·다른 월/과거 지급은 변경하지 않는다. 미래 적용 시작 월은 지원하는 유효 연월 범위 안에서 업무상 기간 상한 없이 미리 지정할 수 있다. 시작 월 한 번 지정/다음 변경까지 지속하며 종료 월/미래 월 목록은 요구하지 않는다. 기존 수동 지정 월/확정본 보존·미확정 반영을 유지한다. 남은 월/입력·역사 사실/대상/버전·저장/경합은 후속이다. [AA 승인](product-decisions.md#review-20261013-aa-batch); PR-007/010/027/030, BR-012, V-130/131 미구성·미실행.

<a id="br-pay-015"></a>
## BR-PAY-015 — 추가실적

Status: APPROVED

추가실적은 Trainer에게 인정하는 보상·인센티브이며 v1 범위다. 타 지점 지원 수업·회원 유지·기타 인정 실적이 예다. 회원 유지는 권한 있는 관리자가 기존 추가실적으로 지급을 인정하는 사유의 예시이며, 별도 회원 유지 보상 제도나 자동 산정 기능을 뜻하지 않는다(2026-10-11 사용자 명확화). Session과 관련될 수도, Session 없이 발생할 수도 있다. 대상 Trainer·사유/유형·금액·발생 시점/정산 기간·Branch Context·필요시 Member/Session·등록자/시점·정정/취소 이력을 식별한다. 생성·정정·취소는 감사 가능한 금액 변경 업무다. 고객 결제·매출·가계부나 AS-IS 수동 매출과 동일시하지 않는다.

2026-10-11 사용자 확정(타 지점 지원 수업 보상의 비용 집계 지점 질문의 1번, 복잡도와 적용 범위 설명 후 최종 확인): 타 지점 지원 수업의 전체 보상으로 확정한 Additional Performance 금액은 해당 수업의 실제 Performed Branch 비용으로 집계한다. 예를 들어 수원점 소속 Trainer가 강남점에서 지원 수업을 수행하고 보상 30,000원을 확정했다면, Trainer의 월 정산에는 추가실적 30,000원을 한 번 합산하고 지점별 비용 보고에서는 강남점 비용으로 30,000원을 집계한다. Trainer 지급액과 지점 비용은 같은 보상의 서로 다른 집계 관점이며 별도 지급이나 중복 추가실적을 만들지 않는다. Trainer 월 정산에는 해당 보상을 한 번만 합산하고, 기존 금액 입력·정정·월 정산 확정 권한과 조회 Scope는 유지한다. 비용 귀속만으로 수행 지점 관리자에게 다른 Home Branch Trainer의 보상 설정·전체 정산 열람이나 금액 입력 권한을 부여하지 않는다. 수업 이후 Trainer의 Home Branch 변경만으로 과거 지원 수업 보상의 비용 귀속 지점이 바뀌지 않는다. 허용된 정정·취소의 유효 상태/금액과 같은 기준으로 Trainer 정산 입력과 지점 비용 집계를 대사할 수 있어야 하며, 기존 확정본·변경 이력 보존은 유지한다. 이 결정은 지원 수업 보상의 내부 지점별 비용 집계에 한정한다. 일반 Session Payment·기본급·지원 수업 외 추가실적의 비용 귀속, 지점별 비용 보고의 공개 범위·집계 기준/완전성 표현, 지점 간 청구·송금 및 기본급 자동 배분은 이번 결정으로 확정하거나 도입하지 않는다. 구체 조회 계약·저장 구조·정정 연동과 갱신/버전 전략은 후속 Architecture 검토 대상이며 MB-010/006 및 BR-013의 잔여 질문은 OPEN이다.

2026-10-10 사용자 정정 확정(MB-009 CLOSED): 타 지점 수업은 일반 PT 수당 대신 해당 수업의 보상 전체를 Additional Performance로 처리한다. 동일 수업의 일반 Session Payment를 정산에 별도로 합산하지 않는다. 앞선 일반 수당+추가 인센티브 방식은 현재 유효 규칙이 아니다. 같은 날 금액 계산 질문의 3번 답변으로 타 지점 지원 수업 보상은 권한 있는 관리자가 수업 건별 금액을 직접 입력하도록 확정했다. 입력 금액 전부를 해당 수업의 Additional Performance로 처리한다. 일반 RATE/FIXED_AMOUNT 계산 결과나 Trainer별 지원 전용 고정금액을 자동 지급액으로 사용하지 않는다. 기존 관리자 범위·본인 등록·승인 생략·감사와 PT 진행 기록·Pass 선택/차감 원칙을 유지한다.

2026-10-10 사용자 확정: Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에게만 추가실적을 직접 등록할 수 있다. 지원 수업의 Performed Branch가 관리자 지점과 같아도 다른 Home Branch Trainer의 추가실적을 등록할 수 없다. 타 지점 수업도 Trainer 소속 지점 관리자 또는 Master가 등록한다.

같은 날 별도 승인 질문의 1번 답변으로 Branch Admin이 본인이 아닌 자기 지점 소속 Trainer의 추가실적을 직접 등록할 때는 별도 Master 승인을 두지 않는다. Master 승인 대기 단계를 추가하지 않으며 생성·변경 감사는 유지한다. 이는 보상 설정에서 자동 상속한 정책이 아닌 별도 사용자 결정이다. 월 정산 확정으로 확대하지 않는다. 본인 건은 아래의 별도 사용자 결정을 따른다.

같은 날 본인 등록 질문의 2번 답변으로 관리자·Trainer 겸임자도 관리 범위 안이면 본인의 추가실적을 직접 등록할 수 있다. Master Admin은 Organization 범위 안의 본인, Branch Admin은 본인 Trainer의 Home Branch가 관리 Branch일 때 허용한다. 다른 Home Branch의 본인 Trainer에게는 Branch Admin 관리 권한으로 등록할 수 없다. 본인 건도 동일하게 감사하며 Actor와 대상 Trainer가 같은 사람임을 추적한다. 보상 설정의 본인 접근에서 자동 상속한 것이 아닌 별도 승인이다.

같은 날 본인 건 승인 질문의 1번 답변으로 관리 범위 안에서 직접 등록한 본인의 추가실적에도 별도 승인을 두지 않는다. Master Admin/Branch Admin과 Trainer를 겸하는 본인 건 모두에 적용하며 Master나 다른 관리자의 승인 대기를 추가하지 않는다. 관리 범위 검증과 동일한 생성·변경 감사, Actor/대상 동일인 추적은 유지한다.

2026-10-10 사용자 확정(진행 기록과 보상 확정 시점 질문의 1번 답변): 타 지점 지원 수업은 보상 금액 없이도 허용된 PT 진행 기록과 Pass 차감을 먼저 완료한다. 권한 있는 관리자가 나중에 수업 건별 금액을 저장할 때 해당 Additional Performance 보상을 확정한다. 금액 미입력은 확정된 0원과 구분하고 누락 건을 추적할 수 있어야 한다. 일반 Session Payment의 등록 시 계산·확정 규칙은 유지한다. 관리자 역할·Home Branch 범위·본인 등록·별도 승인 없음·감사 정책도 유지한다. 당시 미결정이었던 금액 미입력 월의 정산 확정 조건은 아래 후속 사용자 결정으로 해결했다. 월 귀속·마감 이후 처리의 남은 세부 정책은 OPEN이다.

2026-10-10 사용자 확정(금액 미입력 지원 수업이 남은 월의 정산 확정 질문의 1번 답변): 해당 Trainer의 해당 월 정산 대상 지원 수업에 금액 미입력 건이 하나라도 있으면 그 Trainer·월 정산을 확정할 수 없다. 미입력 수업을 제외하거나 0원으로 간주해 확정하지 않는다. 이미 완료한 진행 기록·Pass 차감은 유지한다. 차단 범위는 해당 Trainer·월이며 다른 Trainer·월로 확대하지 않는다. 모든 금액 입력 완료는 이 차단 조건의 해소이며 월 정산 자동 확정이나 나머지 확정 조건의 충족을 뜻하지 않는다. 최초 월 정산 확정 권한과 별도 Master 승인 없음은 2026-10-11 후속 사용자 결정으로 확정했다. 월 귀속·나머지 확정 조건·확정/마감 절차와 남은 정정/취소 및 남은 마감 이후 처리는 OPEN을 유지한다. 당시 미결정이었던 지원 수업 0원 허용은 후속 사용자 결정으로 해결했다.

2026-10-10 사용자 확정(타 지점 지원 수업 보상 0원 허용 질문의 2번 답변): 타 지점 지원 수업 보상은 권한 있는 관리자가 사유를 기록하면 0원으로 명시적으로 확정할 수 있다. 사유 없는 0원 입력은 보상 확정이 불가하다. 사유를 남기고 확정한 0원은 금액 미입력이 아니므로 그 건으로 월 정산 확정을 차단하지 않는다. 다른 미입력 건이 남으면 기존 차단 조건을 유지한다. 기존 관리자 역할·Home Branch Scope·관리 범위 안 본인 등록·별도 승인 없음·감사 정책을 따른다. 미입력을 자동 0원으로 바꾸지 않으며 0원 확정으로 진행 기록을 취소하거나 Pass 차감을 복원하지 않는다. 월 정산 자동 확정이나 나머지 확정 조건의 충족을 뜻하지 않는다. 일반 Session Payment/서비스 PT 계산이나 다른 추가실적의 0원 허용으로 확대하지 않는다.

2026-10-10 사용자 확정(월 정산 확정 전 지원 수업 보상 금액 수정 권한 질문의 1번 답변): 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin에게 Organization 전체, Branch Admin에게 대상 Trainer Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안의 본인 건도 허용하고 변경 이력을 남긴다. 당시 결정은 수정 역할·대상 범위·본인 건 허용·변경 이력에 한정했다. 별도 승인 없음과 저장 즉시 반영은 아래 후속 사용자 결정으로 확정했다. 수정 금액을 0원으로 확정할 때는 기존 사유 필수 정책을 유지한다. 금액 수정만으로 PT 진행 사실·Pass 차감을 취소/복원하거나 일반 Session Payment를 현재 설정으로 재계산하지 않는다. 다른 추가실적 수정 권한과 지원 수업 보상 정정 외 소속 이동 시 권한 기준 시점은 미정이다. 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin·Branch Admin 모두 관리 범위 안에서 본인 건을 포함해 별도 승인 없이 저장 성공 즉시 반영한다. Master나 다른 관리자의 승인 대기를 두지 않으며 권한 검증과 변경 이력을 유지한다. 월 정산 확정 전 지원 수업 보상 금액의 모든 수정에는 변경 사유가 필수다. 양수 간 변경·0원에서 양수로 변경·양수에서 0원으로 변경 모두 적용하며, 사유 없이는 금액을 수정할 수 없다. 변경 전후 금액·변경 사유·수정자·수정 시점을 이력으로 남긴다. 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer의 지원 수업 보상 정정을 위해 월 정산을 확정 해제·재확정할 때는 Master의 별도 승인을 두지 않는다. Master 승인 대기 단계 없이 관리 범위 안에서 직접 처리하며 이전 확정본과 해제·재확정 이력 및 감사를 유지한다. 지원 수업 보상 정정의 월 정산 확정 해제에는 사유가 필수이며, 사유 없이 해제할 수 없다. 사유·해제자·시점을 이력으로 남긴다. 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 남은 정정·취소 절차는 BR-009/013 등 관련 OPEN을 따른다.

2026-10-10 사용자 확정(월 정산 확정 전 지원 수업 보상 수정의 별도 승인·저장 즉시 반영 질문의 1번 답변): 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin·Branch Admin 모두 관리 범위 안에서 본인 건을 포함해 별도 승인 없이 저장 성공 즉시 반영한다. Master나 다른 관리자의 승인 대기를 두지 않으며 권한 검증과 변경 이력을 유지한다. Master의 Organization 전체·Branch Admin의 대상 Trainer Home Branch 기준 범위는 유지한다. 수정 금액을 0원으로 확정할 때는 기존 사유 필수 정책을 적용한다. 금액 수정만으로 진행 기록·Pass 차감을 취소/복원하거나 월 정산을 자동 확정하지 않는다. 다른 추가실적 수정과 확정된 월 정산의 정정 정책으로 확대하지 않는다. 월 정산 확정 전 지원 수업 보상 금액의 모든 수정에는 변경 사유가 필수다. 양수 간 변경·0원에서 양수로 변경·양수에서 0원으로 변경 모두 적용하며, 사유 없이는 금액을 수정할 수 없다. 변경 전후 금액·변경 사유·수정자·수정 시점을 이력으로 남긴다. 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer의 지원 수업 보상 정정을 위해 월 정산을 확정 해제·재확정할 때는 Master의 별도 승인을 두지 않는다. Master 승인 대기 단계 없이 관리 범위 안에서 직접 처리하며 이전 확정본과 해제·재확정 이력 및 감사를 유지한다. 지원 수업 보상 정정의 월 정산 확정 해제에는 사유가 필수이며, 사유 없이 해제할 수 없다. 사유·해제자·시점을 이력으로 남긴다. 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 남은 정정·취소 절차는 BR-009/013 등 관련 OPEN을 따른다.

2026-10-10 사용자 확정(월 정산 확정 전 지원 수업 보상 금액 수정의 변경 사유 질문의 1번 답변): 월 정산 확정 전 지원 수업 보상 금액의 모든 수정에는 변경 사유가 필수다. 양수 간 변경·0원에서 양수로 변경·양수에서 0원으로 변경 모두 적용하며, 사유 없이는 금액을 수정할 수 없다. 변경 전후 금액·변경 사유·수정자·수정 시점을 이력으로 남긴다. 기존 관리자 역할·Home Branch 범위·관리 범위 안 본인 건 허용·별도 승인 없음·저장 성공 즉시 반영은 유지한다. 일반 Session Payment, 다른 종류의 추가실적 및 월 정산 확정 이후 정정 정책으로 확대하지 않는다. 구체 사유 입력·저장 형식은 후속 설계한다.

2026-10-10 사용자 확정(월 정산 확정 후 지원 수업 보상 오류 처리 질문의 2번 답변): 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 이전 확정본의 적용 기본급·구성 금액·합계를 덮어쓰거나 삭제하지 않으며 이전본과 재확정본을 구분한다. 예를 들어 9월 지원 수업 보상 30,000원의 오류를 35,000원으로 정정할 때 9월 정산의 확정 해제 → 지원 수업 보상 금액 정정 → 9월 정산 재확정으로 처리하고 이전 30,000원 반영 확정본을 보존한다. 금액 정정 시 PT 진행 사실·Pass 차감을 재실행하거나 현재 Rate/Fixed Amount/Base Salary를 이유로 과거 확정 일반 지급·기본급을 자동 재계산하지 않는다. 재확정에도 해당 Trainer·월의 미입력 지원 수업 차단 등 승인된 확정 조건을 적용한다. 이번 결정은 지원 수업 보상 금액 오류의 정정 경로와 이전 확정본 보존에 한정한다. 당시 미결정이었던 지원 수업 정정의 해제·재확정 권한은 아래 후속 사용자 결정으로 확정했다. 다른 정정/취소 및 실제 지급과의 대사·차액 처리 상세는 미정이다.

2026-10-10 사용자 확정(지원 수업 보상 정정의 월 정산 확정 해제·재확정 권한 질문의 2번 답변): 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. 수업의 Performed Branch만으로 다른 Home Branch Trainer의 정산 확정 해제·재확정 권한을 얻지 않는다. 관리자 권한이 없는 Operator·Trainer는 이 작업을 수행할 수 없다. 해당 Trainer·월의 확정 해제 → 금액 정정 → 동일 월 재확정과 이전 확정본 보존은 유지한다. 이 결정은 지원 수업 보상 금액 오류 정정에 한정하며 최초 월 정산 확정 권한이나 전체 정산 공개 범위(MB-006)를 새로 확정하지 않는다. 위 지원 수업 보상 정정의 현재 Home Branch 권한 기준은 아래 후속 사용자 결정으로 확정했다.

2026-10-10 사용자 확정(지점 관리자의 지원 수업 보상 정정 시 월 정산 확정 해제·재확정의 별도 승인 질문의 1번 답변): Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer의 지원 수업 보상 정정을 위해 월 정산을 확정 해제·재확정할 때는 Master의 별도 승인을 두지 않는다. Master 승인 대기 단계 없이 관리 범위 안에서 직접 처리하며 이전 확정본과 해제·재확정 이력 및 감사를 유지한다. 기존 Master Organization 범위·Branch Admin 대상 Trainer Home Branch 기준과 범위 밖 접근 거부는 유지한다. 해당 Trainer·월의 확정 해제 → 금액 정정 → 동일 월 재확정 순서와 재확정 시 미입력 지원 수업 차단 등 승인된 확정 조건도 유지한다. 이번 결정은 위 정정의 별도 Master 승인 생략에 한정하며 최초 월 정산 확정 권한/승인, Trainer 신청 승인, 다른 정정/취소 또는 정산 공개 범위로 확대하지 않는다. 확정 해제 사유 필수는 아래 후속 사용자 결정으로 확정했다. 위 지원 수업 보상 정정의 현재 Home Branch 권한 기준은 아래 후속 사용자 결정으로 확정했다.

2026-10-10 사용자 확정(지원 수업 보상 정정 시 월 정산 확정 해제 사유 질문의 1번 답변): 지원 수업 보상 정정의 월 정산 확정 해제에는 사유가 필수이며, 사유 없이 해제할 수 없다. 사유·해제자·시점을 이력으로 남긴다. Master Admin·Branch Admin 모두에 적용한다. 기존 Master Organization 범위·Branch Admin 대상 Trainer Home Branch 기준, Branch Admin의 별도 Master 승인 없음, 이전 확정본 보존과 해제·정정·동일 월 재확정 경로를 유지한다. 금액 수정의 변경 사유 필수도 유지한다. 사유 없는 해제 요청은 기존 확정 상태·확정본·보상 금액을 변경하지 않는다. 이번 결정은 위 지원 수업 보상 정정의 확정 해제에 한정하며 다른 정정/취소 정책으로 확대하지 않는다. 구체 입력 화면·저장 구조는 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(지점 이동 후 과거 지원 수업 보상 정정·정산 해제/재확정의 Home Branch 기준 질문의 1번 답변): 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 9월 수원 소속 Trainer가 10월 강남으로 이동한 뒤 9월 지원 수업 보상을 정정하는 예에서는 강남 Branch Admin에게 해당 정정과 월 정산 확정 해제·재확정을 허용하고, 별도 Master 권한이 없는 수원 Branch Admin에게는 과거 소속만을 근거로 허용하지 않는다. 과거 수업의 Performed Branch·수업 사실·이전 확정본·기존 이력은 보존한다. 기존 관리 범위 검증·Branch Admin의 별도 Master 승인 없음·금액 수정 사유 및 확정 해제 사유 필수·감사 정책을 유지한다. 이번 결정은 지원 수업 보상 금액 정정과 해당 월 정산 해제/재확정의 인가 기준에 한정한다. 다른 추가실적 최초 등록/정정의 이동 기준, Trainer 이동 자체의 적용 시점·절차, 비용 귀속·정산 공개(MB-010/006)는 미결정으로 남긴다. 당시 미정이었던 최초 월 정산 확정 권한과 별도 Master 승인 없음은 2026-10-11 후속 사용자 결정으로 확정했다.

후속 경계: H2/H3으로 지원 수업 외 실적 내용 수정/취소의 Master Organization·Branch Admin 처리 시점 Trainer 현재 Home Branch 인가/본인 포함·별도 승인 없음/사유·이력, 대상 Trainer·발생 날짜 오류의 취소 후 재등록을 확정했다(BR-PAY-019). Operator/Trainer 단독 권한은 추가하지 않는다. 나머지 입력 범위·발생/소속 사실/소급 기간·내용/연결 필드/정정 연결·미입력 지원 보상 추적/연동 및 단계별 계약/UoW·실패/경합은 BR-010/013 후속이다. 비용 귀속·정산 공개의 기존 승인 범위도 유지한다. 지원 수업 기록/Pass 차감과 후속 수동 보상 확정은 별도 업무 단계이며 이번 비지원 실적 정정 정책으로 지원 수업 연결을 임의 변경하지 않는다. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch).

2026-10-11 사용자 확정(회원 유지 등 지원 수업 외 추가실적의 비용 귀속 질문의 1번 답변): 지원 수업 외 Additional Performance의 비용은 실적 발생 당시 대상 Trainer의 Home Branch에 귀속한다. 등록 시점·금액 확정 시점·대상 월말 또는 조회 시점의 소속으로 대체하지 않는다. 예를 들어 수원점 소속일 때 발생한 회원 유지 추가실적의 보상이 100,000원이고 그달 말 강남점으로 이동했다면, 비용은 수원점 100,000원이며 Trainer 월 정산의 해당 추가실적 금액은 그대로 한 번 합산한다. 이동 후 늦게 등록하더라도 비용 귀속 기준은 실적 발생 당시 소속이다. 이후 Home Branch 변경만으로 과거 비용 지점을 바꾸지 않는다. 이 기준은 지원 수업 외 추가실적에 적용하며 PTSession 연결 여부만으로 지원 수업의 Performed Branch 기준을 가져오지 않는다. 타 지점 지원 수업 보상·일반 Session Payment의 실제 Performed Branch 비용 집계와 이동월 기본급의 대상 월말 Home Branch 전액 귀속은 기존 별도 규칙을 유지한다. 기존 관리 권한·보상 금액·월 정산 한 번 합산·확정본/변경 이력 보존을 유지하며, 비용 귀속만으로 그 지점 관리자에게 등록·정정·전체 정산/설정 열람 권한을 부여하지 않는다. 지원 수업 외 추가실적의 금액 산정·0원 등 입력 제약·신청 승인·소속 이동 시 등록/정정 인가 기준 시점은 BR-013 등 관련 OPEN을 유지한다. 발생 시점과 소속 사실의 정의/확인 불가 처리·정산 월 귀속·허용된 정정/취소 절차·비용 보고 공개/집계 상세는 이번에 확정하지 않는다. 계약·이력/저장·조회·정정 연동·갱신/버전 전략은 후속 Architecture 검토 대상이다.

2026-10-11 사용자 확정(회원 유지 등 지원 수업 외 추가실적의 금액 산정 방식 질문의 1번 답변): 회원 유지 등 지원 수업 외 Additional Performance의 금액도 권한 있는 관리자가 실적 건별로 직접 입력한다. v1에서 유형별 사전 금액·산식으로 자동 계산하는 방식을 채택하지 않으며 일반 RATE/FIXED_AMOUNT 계산 결과로 입력액을 대체하지 않는다. 기존 Master Organization 전체/Branch Admin 대상 Trainer Home Branch 범위·관리 범위 안 본인 등록·별도 승인 없음·감사는 유지한다. 비용은 실적 발생 당시 Trainer Home Branch에 귀속하는 기존 기준을 따른다. 이 결정은 금액 산정 방식에 한정하며 지원 수업 외 실적의 금액 확정 시점·미입력/0원·입력 제약·정산 월·이동 시 등록/정정 인가 시점·Trainer 신청/승인·정정/취소 등 남은 정책은 관련 OPEN이다. 지원 수업에 승인된 기록/차감 후 보상 확정·사유 필수 0원·금액 미입력 월 정산 차단을 다른 실적에 자동 적용하지 않는다.

2026-10-11 사용자 확정(Trainer의 별도 추가실적 신청 기능 질문의 1번 답변): v1 추가실적은 권한 있는 관리자의 직접 등록만 지원하고 Trainer의 시스템 내 별도 신청·승인/반려 흐름은 두지 않는다. Trainer는 실적 내용을 관리자에게 전달하며 기존 Master Admin/Branch Admin이 허용된 관리 범위에서 입력한다. Master Organization 전체/Branch Admin 대상 Trainer Home Branch 범위·관리 범위 안 본인 등록·별도 승인 없음·감사는 유지한다. 관리자·Trainer 겸임자는 관리 권한 범위 안에서 본인에게 직접 등록할 수 있으며 Trainer 역할만으로 등록 권한을 얻지 않는다. Trainer의 실제 PT 진행 기록 등록은 계속 지원하며 이를 추가실적 신청으로 취급하지 않는다. 지원 수업의 진행 기록·Pass 차감 완료 후 관리자 금액 저장 시 보상 확정과 미입력 지원 수업의 해당 Trainer·월 정산 확정 차단은 유지한다. 금액 산정·비용 귀속·기존 정정/확정/조회 권한은 변경하지 않는다. 추가실적의 남은 입력 제약/확정 시점·소속 이동 시 인가 시점·정산 월·정정/취소 등은 관련 OPEN이며 신청 기능의 향후 도입은 별도 결정 대상이다.

2026-10-11 사용자 확정(지원 수업 외 추가실적의 등록 시점 질문의 1번 답변): 회원 유지 등 지원 수업 외 Additional Performance는 권한 있는 관리자가 실적 내용과 금액을 함께 입력해야 등록이 완료된다. 금액 미입력 요청은 등록을 완료할 수 없으며, 금액 없는 실적을 먼저 등록하고 나중에 금액을 입력하는 흐름은 v1에 두지 않는다. 누락 금액을 자동으로 0원이나 계산식 결과로 대체하지 않는다. 기존 관리자 역할/대상 Home Branch 범위·관리 범위 안 본인 등록·별도 승인 없음·감사와 발생 당시 Home Branch 비용 귀속을 유지한다. 지원 수업은 기존대로 PT 진행 기록·Pass 차감을 먼저 완료하고 관리자 금액 저장 시 보상을 확정하며, 미입력 지원 수업의 해당 Trainer·월 정산 확정 차단도 유지한다. 이번 결정은 지원 수업 외 실적의 최초 등록 금액 입력 요건에 한정한다. 0원 허용·금액 범위/정밀도·이동 시 등록/정정 인가 시점·정산 월·수정/취소 등은 관련 OPEN이며 월 정산을 자동 확정하거나 지원 수업의 정산 차단 규칙을 다른 실적에 확장하지 않는다.

2026-10-11 사용자 확정(지원 수업 외 추가실적의 0원 등록 허용 여부 질문의 1번 답변): 회원 유지 등 지원 수업 외 Additional Performance의 등록 금액은 0원보다 큰 양수만 허용한다. 0원과 음수 입력은 등록을 거부하며, 사유를 남겨도 0원으로 등록할 수 없다. 기존대로 내용과 금액을 함께 입력해야 등록이 완료되고 누락 금액을 자동으로 채우지 않는다. 지원 수업의 사유 필수 0원 확정 허용·금액 미입력과 명시적 0원 구분·PT 진행 기록/Pass 차감 선완료 및 미입력 지원 수업 월 정산 확정 차단은 유지한다. 기존 관리자 역할/대상 Home Branch 범위·관리 범위 안 본인 등록·별도 승인 없음·감사와 발생 당시 Home Branch 비용 귀속도 유지한다. 이 결정은 지원 수업 외 실적의 등록 금액에 한정한다. 상한액·정밀도/금액 표현·정산 월·이동 시 인가·정정/취소는 관련 OPEN이며 음수 금액 등록이나 0원 덮어쓰기를 미정 정정/취소 절차의 대체로 도입하지 않는다. 일반 보상 설정·상품·월별 적용 기본급의 금액 제약을 변경하지 않는다.

2026-10-11 사용자 확정(지원 수업 외 추가실적을 반영할 정산 월 질문의 1번 답변): 회원 유지 등 지원 수업 외 Additional Performance는 실제 실적이 발생한 월의 Trainer 월 정산에 귀속한다. 9월에 발생한 실적을 10월에 등록해도 9월분이며 등록 월이나 금액 입력 월로 이월하거나 관리자가 반영 월을 임의 선택하지 않는다. 같은 실적을 9월·10월에 중복 합산하지 않는다. 금액을 함께 입력해야 최초 등록이 완료되고 양수만 허용하는 기존 규칙·관리자 직접 등록/관리 범위 안 본인 등록·승인 생략·감사를 유지한다. 비용은 실적 발생 당시 Trainer Home Branch에 귀속하는 기존 기준을 따르며 발생 월/비용 지점이 등록 권한을 자동 부여하지 않는다. 이 결정은 Trainer 월 정산의 귀속 월 기준에 한정한다. 이미 확정된 발생 월에 뒤늦게 추가하는 허용 여부·확정 해제/재확정·권한/사유·이전 확정본 처리의 상세는 BR-009/013에서 별도 결정하며 확정본을 자동 변경하지 않는다. 발생 시점 식별/월 경계·시간대·소급 등록 허용 기간·이동 시 등록/정정 인가 시점·정정/취소 및 비용 보고의 대상 기간/집계 상세는 관련 OPEN이다. 지원 수업/일반 지급의 남은 월 귀속·마감 정책을 이 결정으로 확정하지 않는다.

2026-10-11 사용자 확정(확정된 월의 누락된 지원 수업 외 추가실적 처리 질문의 1번 답변): 이미 확정된 발생 월의 누락된 지원 수업 외 Additional Performance는 해당 Trainer·월 정산의 확정 해제 → 누락 실적 등록 → 같은 발생 월 재확정으로 반영한다. 이전 확정본은 보존하고 재확정 결과와 구분한다. 확정 상태에 직접 추가하여 이전 확정본을 덮어쓰거나 등록 월/다른 월로 이월하지 않는다. 누락 실적은 기존대로 내용과 양수 금액을 함께 입력하며 관리자 직접 등록 역할/대상 범위·관리 범위 안 본인 등록·승인 생략·감사와 발생 당시 Home Branch 비용 귀속을 유지한다. 재확정은 기존 승인된 확정 조건을 다시 검증하고 미입력 지원 수업이 남으면 해당 Trainer·월을 확정하지 않는다. 누락분 등록만으로 자동 확정하지 않는다. 현재 Rate/Fixed Amount/Base Salary 설정으로 과거 확정 지급이나 적용 기본급을 자동 재계산하지 않는다. 이번 결정은 후등록 순서와 이전 확정본 보존에 한정하며 이 후등록을 위한 확정 해제/재확정의 역할·관리 Scope/소속 기준 시점·본인 건/별도 승인 상세·해제 사유 정책은 관련 OPEN이다. 발생 시점 식별/월 경계·소급 기간·금액 상한/정밀도·기존 실적 수정/취소와 각 단계 실패/재시도·UoW·동시성/버전 표현은 별도 정책 또는 Architecture 설계 대상이다.

2026-10-11 사용자 확정(지원 수업 외 실적 등록·누락 후등록의 이동 후 담당 관리자 질문의 1번 답변 및 재확인): 지원 수업 외 Additional Performance의 등록과, 확정된 발생 월의 누락분 반영을 위한 해당 Trainer·월 정산 확정 해제·재확정은 Master Admin에게 Organization 전체, Branch Admin에게 각 업무 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 등록·해제·재확정 요청마다 현재 소속과 관리 권한을 검증하고 최초 단계의 소속으로 후속 권한을 고정하지 않는다. 이전 소속·실적 발생 당시 소속·Performed Branch·클라이언트가 전달한 Branch Context만으로 권한을 부여하지 않는다. 9월 수원점 소속 때 발생한 회원 유지 실적을 10월 강남점 이동 후 처리하면 강남점 Branch Admin/Master가 담당하고, 별도 Master 권한 없는 이전 수원점 Branch Admin은 처리할 수 없다. 실적은 여전히 9월 정산·수원점 비용이며 이전 확정본과 감사 이력을 보존한다. 등록의 내용+양수 금액 필수·관리 범위 안 본인 등록·별도 승인 없음과 재확정의 기존 확정 조건/미입력 지원 수업 차단을 유지한다. 이 결정은 위 등록 및 누락분 후등록의 역할·관리 범위·소속 기준 시점에 한정한다. 누락분 반영을 위한 해제·재확정의 본인 건 처리/별도 승인·해제 사유 정책, 지원 수업 외 기존 실적의 정정/취소 권한·소속 기준 및 처리 절차는 별도 OPEN이다. 기존 지원 수업 보상/기본급 정정 권한이나 비용/조회 범위를 확대하지 않는다.

2026-10-11 사용자 확정(누락 실적 반영을 위한 정산 확정 해제 사유 질문의 1번 답변): 확정된 발생 월의 누락된 지원 수업 외 Additional Performance를 반영하기 위해 해당 Trainer·월 정산의 확정을 해제할 때 사유를 필수로 기록한다. Master Admin과 Branch Admin의 허용된 해제에 동일하게 적용하며 사유 없는 해제 요청은 거부한다. 거부 시 요청 직전의 확정 상태·확정본·기존 실적과 정산 구성/금액을 유지한다. 해제 성공 시 대상 Trainer·월, 해제 사유·처리자·처리 시점을 감사 가능한 이력으로 남기고 이전 확정본을 보존한다. 예를 들어 9월 회원 유지 실적 누락 반영을 사유로 식별할 수 있어야 한다. 각 처리 시점 현재 Home Branch 인가·해제 → 누락 등록 → 같은 월 재확정·발생 월 정산/발생 당시 Home Branch 비용 귀속과 재확정 조건을 유지한다. 이번 결정은 누락분 반영의 확정 해제 사유 필수에 한정하며 이 흐름의 해제/재확정 본인 건 처리·별도 승인 여부와 기존 실적 정정/취소 등 남은 정책은 별도 OPEN이다. 등록 사유/내용을 해제 사유로 자동 대체하거나 별도 승인 정책을 임의 확정하지 않는다.

2026-10-11 사용자 확정(Branch Admin의 본인이 아닌 소속 Trainer 누락 실적 반영 시 Master 승인 질문의 1번 답변): Branch Admin이 본인이 아닌 소속 Trainer의 확정된 발생 월 누락 실적(지원 수업 외 Additional Performance)을 반영할 때, 해당 Trainer·월 정산의 확정 해제·재확정에 별도 Master 승인을 두지 않는다. 각 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인지 검증한 후 Master 승인 대기 없이 직접 처리한다. 해제 사유 필수·사유 없는 요청 거부와 요청 직전 확정 상태/금액 보존, 해제 → 내용과 양수 금액을 갖춘 누락 실적 등록 → 같은 발생 월 재확정 순서, 이전 확정본·처리 이력/감사 보존을 유지한다. 재확정은 기존 확정 조건을 다시 검증하고 미입력 지원 수업이 남으면 해당 Trainer·월을 확정하지 않는다. 승인 생략은 자동 등록/재확정이나 관리 범위 밖 접근을 허용하지 않는다. 발생 월 정산·발생 당시 Home Branch 비용 귀속과 과거 지급/적용 기본급 보존은 유지한다. 이번 결정은 Branch Admin의 본인이 아닌 소속 Trainer 건에 한정하며 관리자 본인의 누락 실적 반영을 위한 해제/재확정 허용 및 해당 본인 건의 별도 승인 정책은 OPEN이다. 이미 승인된 관리 범위 안 본인 실적 등록·기존 지원 수업 보상/기본급 정정 정책은 변경하지 않는다. 기존 비지원 실적 정정/취소·나머지 수명/입력 정책과 구체 계약/UoW/동시성은 별도 결정 또는 설계 대상이다.

2026-10-11 사용자 확정(관리자·Trainer 겸임자의 본인 누락 실적 반영을 위한 확정 해제·재확정 질문의 1번 답변): 관리자·Trainer 겸임자는 관리 권한 범위 안에서 본인의 확정 월 누락 실적(지원 수업 외 Additional Performance)을 반영하기 위한 정산 확정 해제·재확정을 별도 승인 없이 직접 처리할 수 있다. Master Admin은 Organization 범위 안의 본인 건, Branch Admin은 각 처리 시점 본인 Trainer의 현재 Home Branch가 자신의 관리 Branch와 일치하는 경우 허용한다. Actor와 대상 Trainer가 동일인이어도 해제 사유 필수·사유 누락 거부/요청 직전 상태 보존·처리 이력과 감사·이전 확정본 보존은 동일하게 적용한다. Trainer 역할만으로는 본인 정산을 해제/재확정할 수 없으며 관리자 권한/Scope와 현재 소속을 요청마다 검증한다. 해제 → 내용과 양수 금액을 갖춘 누락 실적 등록 → 동일 발생 월 재확정 순서와 발생 당시 Home Branch 비용 귀속을 유지한다. 재확정은 기존 승인 조건을 다시 검증하고 미입력 지원 수업이 남으면 차단하며 본인 건/승인 생략을 이유로 자동 확정하거나 검증을 생략하지 않는다. 기존 비지원 실적 정정/취소·발생 시점/월 경계·소급 기간·나머지 금액 제약은 별도 OPEN이며 구체 계약/저장/단계별 UoW·실패/재시도·이동 경합은 PROPOSED다.

2026-10-11 사용자 확정(정산 확정 전 지원 수업 외 추가실적 금액 수정 권한 질문의 1번 답변): 월 정산 확정 전, 이미 등록한 회원 유지 등 지원 수업 외 Additional Performance의 금액 수정은 Master Admin에게 Organization 전체, Branch Admin에게 수정 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안 관리자·Trainer 겸임자의 본인 건도 포함하며 Master/다른 관리자의 별도 승인 없이 직접 수정한다. 모든 금액 수정에 변경 사유가 필수이고 변경 전후 금액·변경 사유·수정 Actor·처리 시점을 감사 가능한 이력으로 남긴다. 사유 없는 수정 요청은 거부하고 요청 직전 금액·기존 이력·정산 입력 상태를 유지한다. 현재 권한·관리 Scope·대상 Trainer의 현재 소속을 각 요청에서 검증하며 이전 소속/실적 발생 당시 소속·Performed Branch·위조 Branch Context/직접 ID만으로 권한을 부여하지 않는다. 관리자 권한 없는 Operator/Trainer는 본인 건도 수정할 수 없다. 실적 발생 월 정산·발생 당시 Home Branch 비용 귀속과 이전 이력을 유지하고 금액 수정만으로 PT 진행 사실/Pass 차감이나 과거 일반 지급·적용 기본급을 변경하지 않는다. 이번 결정은 확정 전 금액 수정의 역할·Scope·현재 소속 기준·본인 건·별도 승인 없음·사유/이력에 한정한다. 수정 금액의 0원/음수 허용·상한/정밀도, 금액 외 정보 수정·취소 및 확정된 월의 금액 정정/해제·재확정 상세는 별도 OPEN이며 기존 누락 실적 후등록 정책과 구분한다. 구체 입력/저장 계약·UoW·실패/재시도·소속 이동/정산 확정 경합은 PROPOSED다.

2026-10-11 사용자 확정(상황이 달라도 이전 선택지를 참고해 같은 답으로 진행하라는 지시): 유사 상황은 이전 사용자 선택을 참고해 같은 기준으로 진행하라는 지시에 따라, 지원 수업 외 Additional Performance의 최초 등록 금액 > 0 기준을 월 정산 확정 전 금액 수정에도 동일하게 적용한다. 수정 후 금액은 양수만 허용하고 0원·음수·금액 누락 요청은 거부하며 사유를 남겨도 0원 수정 예외를 두지 않는다. 거부 시 요청 직전 금액·이력·정산 입력 상태를 유지한다. 허용된 수정에도 기존 Master Organization/Branch Admin 수정 시점 현재 Home Branch 인가·관리 범위 안 본인 건 허용·별도 승인 없음·변경 사유 필수와 전후 금액/사유/수정자/시점 이력·감사를 적용한다. 발생 월 정산·발생 당시 Home Branch 비용 귀속과 과거 확정 지급/적용 기본급 보존을 유지한다. 지원 수업 보상의 사유 필수 0원 확정/수정과 월별 수동 적용 기본급의 사유 필수 0원 지정은 기존 승인 범위대로 유지한다. 금액 상한·정밀도/표현을 새로 정하거나 0원 덮어쓰기/음수 입력을 실적 취소 절차의 대체로 도입하지 않는다. 확정 후 금액 정정·금액 외 정보 수정/취소 등 남은 정책 및 구체 계약/저장/UoW·실패/재시도·동시성은 별도 결정 또는 설계 대상이다.

2026-10-11 사용자 일관성 지시 적용(기존 지원 수업 보상·기본급의 확정 월 금액 오류 처리 재사용): 유사 상황에 이전 선택을 적용하라는 사용자 지시에 따라 지원 수업 보상/기본급의 확정 월 금액 오류 정정 흐름을 지원 수업 외 Additional Performance에도 적용한다. 확정된 발생 월 실적의 금액 오류는 해당 Trainer·월 확정 해제 → 해당 실적 금액 정정 → 같은 발생 월 재확정으로 처리하고 이전 확정본과 당시 적용 구성/금액/합계·정정 전후 이력을 보존한다. Master Admin은 Organization 전체, Branch Admin은 각 해제/정정/재확정 처리 시점 대상 Trainer의 현재 Home Branch가 관리 Branch인 경우 허용한다. 관리 범위 안 관리자·Trainer 겸임자의 본인 건도 포함하고 별도 Master/다른 관리자 승인 대기를 두지 않는다. 해제와 금액 정정 모두 사유가 필수이며 사유 없는 각 요청은 요청 직전 상태·금액·확정본/이력을 유지하고 거부한다. 해제 사유/처리자/시점과 정정 전후 금액/사유/수정자/시점을 감사 가능한 이력으로 남긴다. 정정 금액도 기존 등록/확정 전 수정과 동일하게 양수만 허용하며 0원·음수·금액 누락 요청은 사유가 있어도 거부한다. 재확정은 기존 승인 조건을 다시 검증하고 금액 미입력 지원 수업이 남으면 해당 Trainer·월을 확정하지 않는다. 정정 저장만으로 자동 재확정하지 않으며 현재 Rate/Fixed Amount/Base Salary로 과거 일반 지급/적용 기본급을 재계산하지 않는다. 실적의 발생 월 정산과 발생 당시 Home Branch 비용 귀속을 유지하고 다른 월/Trainer나 PT 진행 사실·Pass를 변경하지 않는다. 예를 들어 다른 구성 금액이 같고 기존 실적 100,000원을 120,000원으로 정정하면 이전 9월 확정 합계 3,850,000원을 보존하며 새 9월 합계는 3,870,000원이다. 금액 외 정보 수정·실적 취소·발생 시점 식별/월 경계·소급 기간·나머지 금액 제약은 별도 OPEN이다. 각 단계 계약/저장/버전·UoW·실패/재시도·이동/정산 경합은 PROPOSED이며 전체 흐름을 임의의 단일 commit으로 정하지 않는다.

2026-10-11 사용자 확정(“모든 보상”의 범위 확인 질문의 1번): 일반 PT 수당(Session Payment)의 기존 RATE/FIXED_AMOUNT 자동 계산·확정과 기본급(Base Salary)의 별도 월 정산 반영은 유지한다. 그 외 타 지점 지원 수업·회원 유지·기타 보상은 모두 권한 있는 관리자가 기존 Additional Performance에 직접 입력한다. 지급 사유별로 별도 보상 제도나 자동 산정 기능을 만들지 않는다. 기존 관리자 Scope·입력 제약·정정/감사 정책을 유지하며, 타 지점 지원 수업에는 일반 Session Payment를 중복 합산하지 않는다.

2026-10-11 사용자 확정(수업 취소 시 그 수업의 추가실적 보상 처리 질문의 1번): 허용된 PT 진행 기록 취소 시 해당 수업의 보상으로 입력한 Additional Performance도 함께 자동 무효 처리한다. 해당 보상은 유효한 Trainer 월 정산 및 지점 비용 집계에서 제외하며 기존 금액·원본과 취소/변경 이력은 보존한다. 금액을 0원으로 덮어쓰거나 관리자의 별도 추가실적 취소를 기다리는 방식이 아니다. 수행 지점 관리자가 기존 권한으로 해당 수업을 취소하면 그 수업 보상의 무효 처리가 동반되지만, 보상 금액의 입력/임의 수정이나 다른 소속 Trainer의 보상 설정·전체 정산 조회 권한을 추가로 얻지는 않는다. 수업과 무관한 다른 추가실적까지 무효 처리하지 않는다. 확정 월은 기존 현재 Home Branch 담당자 해제 → Performed Branch 담당자 취소 → 현재 Home Branch 담당자 같은 월 재확정 순서와 이전 확정본 보존을 따른다. 등록 금액의 관리자 직접 입력·기존 해제 사유/감사·재확정 조건은 유지한다. 상태 저장/계산 표현·모듈 계약·필수 변경/감사의 원자성·실패/재시도/동시성은 후속 Architecture 설계·검증 대상이며 다른 정정/취소의 나머지 정책은 OPEN이다.

Traceability: PD-027; PR-031/027/010; MB-009/010.

2026-10-12 H2/H3 승인 반영: 지원 수업 외 실적 내용 수정/취소·대상 Trainer/실제 발생 날짜 오류는 BR-PAY-019를 따른다. 원본/취소/정정 이력과 금액·발생 당시 비용 이력을 보존하고 취소 건은 유효 합산에서 제외한다. 일반 PT/Pass/일반 지급은 실적 취소만으로 바꾸지 않는다. 영향받는 확정 정산은 기존 권한/사유·해제/처리/재확정·이전본 보존을 적용한다. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch).

W1/W2 후속: Trainer 과거 Home 오류로 바뀌는 기존 PT 분류는 BR-OPS-033의 Master Organization 전용 명시적 정정으로 같은 PT/차감·최초 생성 시각을 유지한다. 일반은 최초 기록 생성 시점 설정/기존 소비 Pass 발급 조건, 지원은 기존 관리자 Scope의 수동 추가실적이며 이전 보상 이력/유효 합계 단일 반영을 보장한다. 영향 건의 분류/보상·비용 정정 완료 전 해당 Trainer·월 확정/재확정은 BR-PAY-024로 차단한다. 기존 확정본 자동 변경 없이 필요한 월의 기존 권한/사유·해제/정정/같은 월 재확정·이전본 보존을 따른다. [W 승인](product-decisions.md#review-20261013-w-batch); V-124/125 미구성·미실행.

<a id="br-pay-016"></a>
## BR-PAY-016 — 월 정산 구성과 보존

Status: APPROVED

2026-10-11 사용자 확정(월 정산을 처음 확정할 권한 질문의 1번 답변): 월 정산의 최초 확정은 Master Admin에게 Organization 전체 Trainer, Branch Admin에게 확정 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 직접 확정한다. 관리자 권한이 없는 Operator·Trainer는 최초 확정할 수 없다. Backend에서 현재 Actor 권한·관리 Scope와 대상 Trainer의 현재 Home Branch를 검증하며, 과거 Home Branch·수업의 Performed Branch·직접 ID 요청·위조 Branch Context만으로 권한을 부여하지 않는다. 해당 Trainer·월에 금액 미입력 지원 수업이 남으면 기존 규칙대로 최초 확정을 차단하고, 사유를 기록해 명시적으로 확정한 지원 수업 0원은 미입력으로 취급하지 않는다. 모든 보상 입력 완료만으로 정산을 자동 확정하지 않는다. 기본급 한 번 가산·유효한 일반 지급과 추가실적 합산·과거 확정본 보존은 유지한다. 이번 결정은 최초 확정의 역할·관리 범위·별도 Master 승인 없음에 한정하며, 상세 정산 공개(MB-006)·지점 비용 귀속(MB-010)·나머지 확정 조건과 마감/정정 절차(BR-009)는 OPEN을 유지한다.

2026-10-11 사용자 확정(지점장이 조회할 정산 내역의 범위 질문의 1번 답변): Branch Admin은 조회 시점에 자신의 관리 Branch를 Home Branch로 가진 Trainer의 해당 월 정산 전체 금액과 구성 내역을 조회할 수 있다. 해당 월 적용 기본급·일반 Session Payment·타 지점 지원 수업을 포함한 Additional Performance·월 정산 총액을 모두 공개하며, 수업의 Performed Branch가 다른 지점이라는 이유로 해당 금액을 제외하거나 숨기지 않는다. 관리 범위 안의 본인 Trainer도 같은 기준을 적용하고 Master Admin의 Organization 전체 조회 권한은 유지한다. 반대로 다른 Home Branch Trainer는 자기 지점에서 지원 수업을 했다는 사실만으로 전체 월 정산 조회 대상이 되지 않는다. Backend는 직접 ID·목록/검색·집계 등 각 조회 경로에서 현재 관리 Scope와 대상 Trainer의 현재 Home Branch를 검증한다. 이는 정산 구성 금액·내역의 공개에 관한 결정이며, 다른 지점의 전체 회원/Trainer 자료나 원본 업무 데이터·감사 이력의 포괄적 열람을 허용하지 않는다. 조회할 대상 월·이전 확정본/세부 계산 근거·감사 정보의 남은 공개 상세 및 Operator·관리자 권한 없는 Trainer의 정산 조회 권한은 관련 OPEN을 유지한다. 지점별 정산/비용 귀속(MB-010), 과거 확정 금액 보존, 지원 수업 보상의 일반 지급과의 중복 합산 금지 및 기존 확정/정정 권한·조건은 변경하지 않는다.

2026-10-11 사용자 확정(타 지점 지원 수업 보상의 비용 집계 지점 질문의 1번, 복잡도와 적용 범위 설명 후 최종 확인): 타 지점 지원 수업의 전체 보상으로 확정한 Additional Performance 금액은 해당 수업의 실제 Performed Branch 비용으로 집계한다. 이는 지점별 비용 보고의 분류 기준이며 Trainer 월 정산 구성 금액이나 합산 횟수를 늘리지 않는다. 지원 수업 보상은 일반 Session Payment와 중복 합산하지 않고 기존 확정/정정 권한·조건을 유지한다. 상세 경계는 BR-PAY-015, 나머지 비용 귀속·보고 공개/집계 상세는 MB-010/006 OPEN이다.

2026-10-11 사용자 확정(월중 지점 이동 시 기본급 비용 귀속 질문의 1번 답변): 월중 Trainer 지점 이동이 있는 달의 해당 월 적용 기본급 비용은 대상 월의 월말 Home Branch 한 곳에 전액 귀속한다. Trainer 월 정산의 기본급 한 번 합산과 해당 월 수동 지정 우선·지급액 유지·과거 확정본 보존을 따른다. 이후 소속 이동을 이유로 과거 대상 월말 기준 비용 지점을 바꾸지 않으며 비용 귀속으로 관리 권한을 확대하지 않는다. 상세 경계는 BR-PAY-014, 나머지 귀속·비용 보고 공개/집계 상세는 MB-010/006 OPEN이다.

2026-10-11 사용자 확정(이동 전후 일반 PT 수당의 비용 귀속 질문의 1번 답변): 일반 Session Payment는 해당 PT 진행 기록의 실제 Performed Branch 비용으로 집계한다. 이미 확정된 수업별 지급액을 지점별로 합산하며 대상 월말 Home Branch로 전액을 모으지 않는다. 예를 들어 같은 Trainer의 해당 월 정산 대상 일반 지급이 이동 전 수원점 수업 200,000원·이동 후 강남점 수업 300,000원이면, 비용은 수원점 200,000원·강남점 300,000원으로 집계하고 Trainer의 일반 PT 수당 합계는 500,000원을 유지한다. 기존 RATE/FIXED_AMOUNT·서비스 PT의 지급 계산과 등록 시 확정·과거 지급 불변성을 유지하며 현재 보상 설정으로 지급액을 다시 계산하지 않는다. 지점/월 합계에 RATE 올림을 다시 적용하거나 별도 지급·중복 보상을 생성하지 않는다. 타 지점 지원 수업은 기존대로 보상 전체를 Additional Performance로 처리하므로 같은 지원 수업의 일반 Session Payment를 별도로 더하지 않는다. 이동월 기본급 비용의 대상 월말 Home Branch 전액 귀속은 별도 규칙으로 유지한다. 이후 Home Branch 변경만으로 과거 수업의 실제 Performed Branch에 따른 비용 지점을 바꾸지 않는다. 기존 입력·정정·확정·조회 권한을 유지하며 비용 귀속만으로 다른 Home Branch Trainer의 설정/전체 정산 열람·정정 권한을 부여하지 않는다. 허용된 정정/취소의 같은 유효 상태·금액·확정본 기준으로 Trainer 정산 입력과 지점 비용 집계를 대사할 수 있어야 하고 이전 확정본/이력을 보존한다. 이번 결정은 비용 집계 기준이며 일반 지급/진행 기록의 정정·취소 절차(BR-007/009)를 새로 승인하지 않는다. 지원 수업 외 추가실적의 비용 귀속·기본급 귀속의 남은 예외·비용 보고 공개/집계 상세는 MB-010/006 OPEN이며 연계 계약·저장/조회·정정 반영과 갱신/버전 전략은 후속 Architecture 대상이다.

2026-10-11 사용자 확정(회원 유지 등 지원 수업 외 추가실적의 비용 귀속 질문의 1번 답변): 지원 수업 외 Additional Performance의 비용은 실적 발생 당시 대상 Trainer의 Home Branch에 귀속한다. 등록 시점·금액 확정 시점·대상 월말 또는 조회 시점의 소속으로 대체하지 않는다. Trainer 월 정산의 추가실적 금액·한 번 합산·기존 권한은 유지한다. 수업 보상의 수행 지점 기준·이동월 기본급의 월말 Home Branch 기준과 별도다. 다른 추가실적의 금액 산정이나 정산 월을 새로 정한 결정이 아니다. 상세 경계는 BR-PAY-015, 남은 예외·비용 보고 공개/집계 상세는 MB-010/006 및 관련 OPEN을 따른다.

2026-10-11 사용자 확정(지점별 비용 보고서 조회 권한 질문의 1번 답변): v1 지점별 비용 보고서는 Master Admin만 자신의 Organization 범위에서 조회할 수 있다. Branch Admin은 자기 지점의 비용 합계만 조회하는 경우에도 이 보고서에 접근할 수 없으며, Master 권한이 없는 Operator·Trainer도 접근할 수 없다. Master Admin·Trainer 겸임자는 Master 권한으로 조회할 수 있지만 Branch Admin·Trainer 겸임만으로는 허용하지 않는다. Backend에서 보고서의 개별 요청·목록·검색·집계 경로마다 현재 Master 권한과 Organization Scope를 검증하며, 직접 ID·위조 Branch Context·비용 귀속 지점 또는 UI 메뉴 숨김으로 이 검증을 대신하지 않는다. Branch Admin의 조회 시점 현재 자기 Home Branch 소속 Trainer에 대한 해당 월 정산 전체 금액·구성 내역 조회 권한은 타 지점 지원 수업 보상까지 포함하여 그대로 유지한다. 두 조회 권한을 구분하며, 비용 귀속으로 그 지점 관리자에게 보고서나 다른 소속 Trainer의 보상 설정/전체 정산 열람 권한을 부여하지 않는다. 기존 지급액·비용 귀속·추가실적 등록/정정·정산 확정 권한은 변경하지 않는다. 이번 결정은 v1 비용 보고서의 조회 역할·관리 Scope에 한정한다. 보고서 항목/상세 수준·대상 월/집계 기준·미확정/확정 자료의 완전성 표현·이전 확정본/버전 및 원본/감사 정보 공개 등 남은 상세는 MB-006/010 OPEN이며, Branch Admin에게 보고서를 확대 공개하려면 별도 결정이 필요하다.

2026-10-11 사용자 확정(지원 수업 외 추가실적을 반영할 정산 월 질문의 1번 답변): 회원 유지 등 지원 수업 외 Additional Performance는 실제 실적이 발생한 월의 Trainer 월 정산에 귀속한다. 9월에 발생한 실적을 10월에 등록해도 9월분이며 등록 월이나 금액 입력 월로 이월하거나 관리자가 반영 월을 임의 선택하지 않는다. 같은 실적을 9월·10월에 중복 합산하지 않는다. 기존 유효 실적 한 번 합산·확정본 보존은 유지한다. 확정된 발생 월에 대한 후등록 처리·소급 허용 기간과 월 경계 등은 BR-009/013 관련 OPEN이다.

2026-10-11 사용자 확정(확정된 월의 누락된 지원 수업 외 추가실적 처리 질문의 1번 답변): 이미 확정된 발생 월의 누락된 지원 수업 외 Additional Performance는 해당 Trainer·월 정산의 확정 해제 → 누락 실적 등록 → 같은 발생 월 재확정으로 반영한다. 이전 확정본은 보존하고 재확정 결과와 구분한다. 확정 상태에 직접 추가하여 이전 확정본을 덮어쓰거나 등록 월/다른 월로 이월하지 않는다. 재확정은 기존 확정 조건을 재검증하고 과거 지급/적용 기본급을 현재 설정으로 자동 재계산하지 않는다. 이 후등록의 해제·재확정 권한/소속 기준·사유 등은 BR-009/013 OPEN이며 기존 지원 수업/기본급 정정 권한을 자동 확장하지 않는다.

지원 수업 외 실적 등록 및 확정 월 누락분 반영의 해제·재확정은 Master Organization 전체/Branch Admin 각 처리 시점 Trainer 현재 Home Branch 기준으로 인가(Product 확정, 2026-10-11). 단계마다 재검증하며 이전 소속/발생 당시 소속만으로 권한 없음. 발생 월 정산·발생 당시 Home Branch 비용 귀속은 유지. 이 후등록의 해제/재확정 본인 건 허용·별도 승인 없음은 확정(2026-10-11). 기존 실적 정정/취소는 별도 OPEN.

확정 월의 누락된 지원 수업 외 실적 반영을 위한 해제 사유 필수(Product 확정, 2026-10-11). 사유 없는 해제 요청은 거부하고 요청 직전 확정 상태/확정본/기존 실적·정산 구성/금액 유지. 성공 시 대상 Trainer/월·사유·해제자·시점 이력/감사와 이전 확정본 보존. 현재 Home Branch 인가·기존 후등록 순서/월/비용 귀속 유지. 이 흐름의 해제/재확정은 관리 범위 안 본인 건도 별도 승인 없이 허용(2026-10-11).

Branch Admin의 본인이 아닌 소속 Trainer 누락 실적 후등록 해제/재확정은 별도 Master 승인 없음(Product 확정, 2026-10-11). 각 처리 시점 현재 Home Branch 인가·해제 사유 필수·해제 후 등록/동일 월 재확정·이전 확정본/감사·기존 확정 조건/미입력 지원 수업 차단 유지. 관리 범위 안 관리자 본인 건의 해제/재확정 허용·별도 승인 없음도 확정(2026-10-11).

관리 범위 안 관리자·Trainer 겸임자의 본인 누락 실적 후등록 해제/재확정도 별도 승인 없이 허용(Product 확정, 2026-10-11). Master Organization 범위/Branch Admin 각 처리 시점 본인 현재 Home Branch 일치·해제 사유 필수·본인 감사/이전 확정본 보존·기존 후등록 순서/월/비용 귀속·재확정 조건/미입력 지원 수업 차단 유지. Trainer 단독 권한 없음. 비지원 실적의 금액 외 정보 수정/취소 등은 OPEN.

월 정산 확정 전 비지원 추가실적 금액 수정은 Master Organization 전체/Branch Admin 각 수정 시점 Trainer 현재 Home Branch 기준으로 허용(Product 확정, 2026-10-11). 관리 범위 안 본인 건 포함·별도 승인 없음·변경 사유 필수·전후 금액/사유/수정자/시점 이력과 감사. 사유 누락 거부/요청 직전 금액 유지. 발생 월/당시 Home Branch 비용 유지. 수정 금액의 나머지 입력 제약, 금액 외 정보 수정/취소는 OPEN.

지원 수업 외 추가실적은 최초 등록과 확정 전 금액 수정 모두 양수만 허용(Product 확정, 2026-10-11 사용자 일관성 지시 적용). 0원·음수·누락 수정 거부/요청 직전 금액·이력·정산 입력 상태 유지; 사유가 있어도 0원 수정 불가. 기존 관리자 Scope/본인 건/승인 생략/사유·이력/감사 유지. 지원 수업 보상 및 월별 수동 기본급의 승인된 사유 필수 0원 예외는 유지. 상한/정밀도·금액 외 정보 수정/취소는 OPEN.

지원 수업 외 실적의 확정 후 금액 오류도 해당 Trainer/월 해제 → 양수 금액 정정 → 같은 월 재확정·이전 확정본/구성/이력 보존(2026-10-11 사용자 일관성 지시 적용). Master Organization/Branch Admin 각 처리 시점 현재 Home Branch·본인 건 포함·별도 승인 없음·해제/정정 모두 사유 필수·감사·기존 재확정 조건/미입력 지원 수업 차단 유지. 발생 월/당시 Home Branch 비용 유지. 금액 외 정보 수정/취소·나머지 기간/금액 제약은 OPEN.

Monthly Settlement = 해당 월 적용 Base Salary + 유효한 Session Payment 합계 + 유효한 Additional Performance 합계다. Trainer·대상 월·적용 기본급·Session 수·Session Payment 합계·추가실적 내역/합계·월 정산 합계를 구분한다. 2,500,000원 + 1,200,000원 + 150,000원 = 3,850,000원이며 여러 지점 수업으로 동일 월 기본급을 중복 가산하지 않는다. 타 지점 수업의 보상 전체는 Additional Performance로 반영하며 일반 Session Payment를 별도로 합산하지 않는다(MB-009 CLOSED, 2026-10-10 사용자 정정).

해당 Trainer의 해당 월 정산 대상 지원 수업에 금액 미입력 건이 하나라도 있으면 그 Trainer·월 정산을 확정할 수 없다. 미입력 수업을 제외하거나 0원으로 간주해 확정하지 않는다. 이미 완료한 진행 기록·Pass 차감은 유지한다. 차단 범위는 해당 Trainer·월이며 다른 Trainer·월로 확대하지 않는다. 모든 금액 입력 완료는 이 차단 조건의 해소이며 월 정산 자동 확정이나 나머지 확정 조건의 충족을 뜻하지 않는다. 타 지점 지원 수업 보상은 권한 있는 관리자가 사유를 기록하면 0원으로 명시적으로 확정할 수 있다. 사유 없는 0원 입력은 보상 확정이 불가하다. 사유를 남기고 확정한 0원은 금액 미입력이 아니므로 그 건으로 월 정산 확정을 차단하지 않는다. 다른 미입력 건이 남으면 기존 차단 조건을 유지한다.

2026-10-10 사용자 확정(월 정산 확정 후 지원 수업 보상 오류 처리 질문의 2번 답변): 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 이전 확정본의 적용 기본급·구성 금액·합계를 덮어쓰거나 삭제하지 않으며 이전본과 재확정본을 구분한다. 예를 들어 9월 지원 수업 보상 30,000원의 오류를 35,000원으로 정정할 때 9월 정산의 확정 해제 → 지원 수업 보상 금액 정정 → 9월 정산 재확정으로 처리하고 이전 30,000원 반영 확정본을 보존한다. 금액 정정 시 PT 진행 사실·Pass 차감을 재실행하거나 현재 Rate/Fixed Amount/Base Salary를 이유로 과거 확정 일반 지급·기본급을 자동 재계산하지 않는다. 재확정에도 해당 Trainer·월의 미입력 지원 수업 차단 등 승인된 확정 조건을 적용한다. 이번 결정은 지원 수업 보상 금액 오류의 정정 경로와 이전 확정본 보존에 한정한다. 당시 미결정이었던 지원 수업 정정의 해제·재확정 권한은 아래 후속 사용자 결정으로 확정했다. 다른 정정/취소 및 실제 지급과의 대사·차액 처리 상세는 미정이다.

2026-10-10 사용자 확정(지원 수업 보상 정정의 월 정산 확정 해제·재확정 권한 질문의 2번 답변): 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. 수업의 Performed Branch만으로 다른 Home Branch Trainer의 정산 확정 해제·재확정 권한을 얻지 않는다. 관리자 권한이 없는 Operator·Trainer는 이 작업을 수행할 수 없다. 해당 Trainer·월의 확정 해제 → 금액 정정 → 동일 월 재확정과 이전 확정본 보존은 유지한다. 이 결정은 지원 수업 보상 금액 오류 정정에 한정하며 최초 월 정산 확정 권한이나 전체 정산 공개 범위(MB-006)를 새로 확정하지 않는다. 위 지원 수업 보상 정정의 현재 Home Branch 권한 기준은 아래 후속 사용자 결정으로 확정했다.

2026-10-10 사용자 확정(지점 관리자의 지원 수업 보상 정정 시 월 정산 확정 해제·재확정의 별도 승인 질문의 1번 답변): Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer의 지원 수업 보상 정정을 위해 월 정산을 확정 해제·재확정할 때는 Master의 별도 승인을 두지 않는다. Master 승인 대기 단계 없이 관리 범위 안에서 직접 처리하며 이전 확정본과 해제·재확정 이력 및 감사를 유지한다. 기존 Master Organization 범위·Branch Admin 대상 Trainer Home Branch 기준과 범위 밖 접근 거부는 유지한다. 해당 Trainer·월의 확정 해제 → 금액 정정 → 동일 월 재확정 순서와 재확정 시 미입력 지원 수업 차단 등 승인된 확정 조건도 유지한다. 이번 결정은 위 정정의 별도 Master 승인 생략에 한정하며 최초 월 정산 확정 권한/승인, Trainer 신청 승인, 다른 정정/취소 또는 정산 공개 범위로 확대하지 않는다. 확정 해제 사유 필수는 아래 후속 사용자 결정으로 확정했다. 위 지원 수업 보상 정정의 현재 Home Branch 권한 기준은 아래 후속 사용자 결정으로 확정했다.

2026-10-10 사용자 확정(지원 수업 보상 정정 시 월 정산 확정 해제 사유 질문의 1번 답변): 지원 수업 보상 정정의 월 정산 확정 해제에는 사유가 필수이며, 사유 없이 해제할 수 없다. 사유·해제자·시점을 이력으로 남긴다. Master Admin·Branch Admin 모두에 적용한다. 기존 Master Organization 범위·Branch Admin 대상 Trainer Home Branch 기준, Branch Admin의 별도 Master 승인 없음, 이전 확정본 보존과 해제·정정·동일 월 재확정 경로를 유지한다. 금액 수정의 변경 사유 필수도 유지한다. 사유 없는 해제 요청은 기존 확정 상태·확정본·보상 금액을 변경하지 않는다. 이번 결정은 위 지원 수업 보상 정정의 확정 해제에 한정하며 다른 정정/취소 정책으로 확대하지 않는다. 구체 입력 화면·저장 구조는 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(지점 이동 후 과거 지원 수업 보상 정정·정산 해제/재확정의 Home Branch 기준 질문의 1번 답변): 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 9월 수원 소속 Trainer가 10월 강남으로 이동한 뒤 9월 지원 수업 보상을 정정하는 예에서는 강남 Branch Admin에게 해당 정정과 월 정산 확정 해제·재확정을 허용하고, 별도 Master 권한이 없는 수원 Branch Admin에게는 과거 소속만을 근거로 허용하지 않는다. 과거 수업의 Performed Branch·수업 사실·이전 확정본·기존 이력은 보존한다. 기존 관리 범위 검증·Branch Admin의 별도 Master 승인 없음·금액 수정 사유 및 확정 해제 사유 필수·감사 정책을 유지한다. 이번 결정은 지원 수업 보상 금액 정정과 해당 월 정산 해제/재확정의 인가 기준에 한정한다. 다른 추가실적 최초 등록/정정의 이동 기준, Trainer 이동 자체의 적용 시점·절차, 비용 귀속·정산 공개(MB-010/006)는 미결정으로 남긴다. 당시 미정이었던 최초 월 정산 확정 권한과 별도 Master 승인 없음은 2026-10-11 후속 사용자 결정으로 확정했다.

현재 Rate/Fixed Amount/Base Salary 변경으로 과거 확정 Session Payment 및 확정 월 정산의 적용 기본급·합계를 자동 변경하지 않는다. 지원 수업 금액 오류의 위 정정 경로는 현재 설정 변경과 별개다. 다른 정정/취소 반영·마감/최초 확정 절차의 남은 상세는 BR-007/009/013 OPEN이다. 정산 공개는 MB-006, 기본급 적용 시작 월의 관리자 지정·미확정 과거 월 지정 허용·수동 지정 없는 기존 미확정 정산의 기본급·합계 자동 반영은 확정이며 미리 등록할 수 있는 미래 적용 시작 월의 범위 등 남은 기본급 정책은 BR-012, 지점 이동·교차 수업·추가실적 집계/비용 귀속은 MB-010 OPEN이다. Home Branch·Performed Branch·정산 귀속 Branch를 같다고 가정하지 않는다. 보존 방식은 Architecture에서 결정한다.

확정된 월의 기본급 오류는 해당 Trainer·월의 확정 해제 → 해당 월 적용 기본급 정정 → 동일 월 재확정으로 처리하고 이전 확정본은 이력으로 보존한다. 현재 설정 변경에 따른 자동 갱신과 구별한다. 기본급 오류 정정의 확정 해제·재확정은 Master Admin에게 Organization 전체, Branch Admin에게 각 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 처리한다. 확정된 월의 기본급 오류 정정에서 확정 해제와 해당 월 기본급 수정 모두 사유가 필수다. Master Admin·Branch Admin 및 관리 범위 안 본인 건에 동일하게 적용한다. 해제 사유·해제자·시점과 변경 전후 기본급·수정 사유·수정자·시점을 이력으로 남긴다. 기본급 오류 정정은 대상 Trainer의 해당 월 정산에만 적용하며 현재·미래 기본급 설정과 다른 월 정산은 유지한다. 지속적인 기본급 변경은 별도로 적용 시작 월을 지정하는 기존 흐름을 따른다. 입사·퇴사·휴직이 있는 달의 적용 기본급은 관리자가 해당 Trainer·월의 금액을 직접 지정한다. 예를 들어 월 기본급 설정이 2,500,000원이어도 해당 월만 1,500,000원을 적용할 수 있으며, 이 지정으로 현재·미래 기본급 설정과 다른 월 정산은 변경하지 않는다. 월별로 수동 지정한 기본급은 이후 일반 기본급 설정이 변경되어도 유지한다. 일반 설정 변경의 미확정 정산 자동 반영은 수동 지정이 없는 월에 적용하며, 수동 지정 월의 금액을 바꾸려면 관리자가 해당 월 금액을 직접 수정한다. 미확정 월의 기본급을 최초 수동 지정하거나 다시 수정할 때 모두 사유가 필수다. 사유가 없는 요청은 거부하고 요청 직전의 수동 지정 여부·적용 금액·월 합계를 유지한다. 대상 Trainer·월, 지정/수정 전후 금액·사유·처리자·처리 시점을 이력으로 남긴다. 미확정 월 기본급의 최초 수동 지정·수정은 Master Admin의 Organization 전체, Branch Admin의 각 처리 시점 대상 Trainer 현재 Home Branch가 관리 Branch와 일치하는 범위에서 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 직접 처리한다. 추가 사용자 확정(2026-10-11): 해당 월 기본급은 권한 있는 관리자가 사유를 남기면 0원으로 명시적으로 수동 지정할 수 있다. 수동 지정한 0원은 미입력과 구분하며, 미입력이나 누락된 일반 설정을 자동으로 0원으로 대체하지 않는다. 해당 월 기본급에만 적용하고 다른 유효 지급·추가실적은 기존 규칙대로 합산한다. 미리 등록할 수 있는 미래 적용 시작 월의 범위와 월별 수동 지정 금액의 나머지 입력 제약 등은 BR-012/BR-010 OPEN이다.

Traceability: PD-012/027; PR-010; BR-PAY-009/014/015.

2026-10-12 H2–H4 승인 반영: 비지원 실적 내용 수정/취소·대상/발생 날짜 정정이 확정 정산에 영향을 주면 관련 Trainer/월 각각의 기존 해제/처리/재확정과 이전본 보존을 따른다. 관리자 권한 없는 Trainer의 본인 월 정산 시스템 조회는 v1 제외이며 기존 본인 PT 진행 내역 조회는 유지한다. 관리자 겸임의 독립 현재 관리 Scope 및 Master Organization/Branch Admin 현재 소속 Trainer 월 정산 조회는 그대로다. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch).

확정 시간 조건 추가: 월 정산 최초 확정/해제 후 재확정은 BR-PAY-020의 한국 시간 기준 종료된 월만 허용한다. 당월은 기존 관리자 Scope에서 미확정 조회·검토하며 월 종료가 지원 보상 미입력 등 다른 확정 조건 충족이나 자동 확정을 뜻하지 않는다. 미래 기본급 적용 시작 월 지정과는 별개다. [2026-10-13 L1 승인](product-decisions.md#review-20261013-l-batch).

W1/W2 후속: Trainer 과거 Home 오류로 바뀌는 기존 PT 분류는 BR-OPS-033의 Master Organization 전용 명시적 정정으로 같은 PT/차감·최초 생성 시각을 유지한다. 일반은 최초 기록 생성 시점 설정/기존 소비 Pass 발급 조건, 지원은 기존 관리자 Scope의 수동 추가실적이며 이전 보상 이력/유효 합계 단일 반영을 보장한다. 영향 건의 분류/보상·비용 정정 완료 전 해당 Trainer·월 확정/재확정은 BR-PAY-024로 차단한다. 기존 확정본 자동 변경 없이 필요한 월의 기존 권한/사유·해제/정정/같은 월 재확정·이전본 보존을 따른다. [W 승인](product-decisions.md#review-20261013-w-batch); V-124/125 미구성·미실행.

Y1/Y2 보고 경계: Master 전용 지점 비용 보고서는 BR-PAY-025의 종료 월·미완료 영향 없는 최신 유효 확정본만 합산한다. 미확정/해제 중/소속 오류 영향 정정 대기 Trainer·월은 합계 제외/미완료 표시하며 전체 월 비용 완성·0원으로 대체하지 않는다. 이전 확정본 보존/현재 설정으로 과거 재계산 금지와 기존 비용 귀속·당월 Trainer 월 정산 조회는 유지한다. 소속 정정에 따른 보고 제외는 원래 확정본의 자동 해제/수정이 아니다. [Y 승인](product-decisions.md#review-20261013-y-batch); V-127/128 미구성·미실행.

AB1/AB2 대상 기준: 월 정산 자동 대상/비활성 무지급 월 새 확정 의무의 예외는 BR-PAY-026을 따른다. 설정/유효 구성·기존 정산/미완료를 대조하고 현재 활성 목록/기존 정산 행만으로 누락을 숨기지 않는다. 자동 확정/비활성 기본급 자동0/이력 삭제 없이 기존 확정/공개·비용 보고 조건을 유지한다. [AB 승인](product-decisions.md#review-20261013-ab-batch); V-132/133 미구성·미실행.

<a id="br-ops-018"></a>
## BR-OPS-018 — PT 기록의 Member/실제 수행 Trainer 정정

상태: APPROVED-TO-BE

완료 수업의 Member 또는 실제 수행 Trainer를 잘못 기록한 경우 기존 기록을 취소하고 올바르게 다시 등록한다(C10). 기존 참가자를 덮어쓰지 않고 원본·취소와 정정 재등록의 연결/이력을 보존한다. 실제 수업을 추가로 한 것으로 중복 처리하지 않는다. 취소에 따른 기존 Pass 횟수 복원·유효 지급/연계 추가실적 무효화 후 재등록에는 기존 FIXED_AMOUNT 우선/FIFO/Remaining > 0 및 실제 사용 자격을 적용한다. 일반 Session Payment는 재등록 생성 시점의 실제 수행 Trainer 설정으로 새로 확정하며 취소 원본의 금액과 다른 유효 과거 지급을 재계산하지 않는다. 타 지점 지원 수업은 기존대로 일반 지급 대신 관리자 수동 Additional Performance 보상을 사용한다.

정정/취소의 Actor는 Master Organization 또는 Branch Admin 실제 Performed Branch 범위다. Performed Branch 값 자체의 정정은 Master 전용이며 취소·재등록으로 우회하지 않는다. 정산이 확정돼 있으면 영향받는 각 Trainer·월에 기존 해제→정정→같은 월 재확정과 사유/이전 확정본 보존·재확정 차단 조건을 적용한다. 정산 Actor의 현재 Trainer Home Branch 기준과 PT Actor의 Performed Branch 기준은 별개다. 다른 Trainer/월에 걸친 작업 순서·최소 과거 사실/정정 연결 계약·실패/재시도/UoW·경합은 후속 설계다.

Traceability: C10; PR-008/009/010; BR-007; MB-005/010; BR-OPS-017; BR-PAY-006/015/016. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch).

2026-10-12 K1=1: Member/실제 수행 Trainer 오류의 기존 C10 취소 후 재등록 외에 실제 시작 날짜/시각 오류도 BR-OPS-023에 따라 취소 후 재등록한다. 올바른 실제 시점의 Pass·소속/상태와 현재 인가/각 영향받는 확정 월을 검증하고 원본/새 기록을 연결한다. Performed Branch 값 정정의 기존 별도 Master 전용/기록 유지 정책은 변경하지 않는다. [2026-10-12 K 일괄 승인](product-decisions.md#review-20261012-k-batch).

<a id="br-pay-017"></a>
## BR-PAY-017 — 원화 금액 입력 단위

상태: APPROVED-TO-BE

원화 금액 입력은 원 단위 정수만 허용하고 소수 원 입력은 거부한다(C11). 상품 가격·Fixed Amount·Base Salary·수동 추가실적/정산 적용 금액에도 같은 입력 단위를 적용한다. 비율인 Rate의 소수 정밀도를 원화 입력 단위로 정하지 않는다. RATE 지급 계산의 나눗셈/비율 중간값은 소수일 수 있고 최종 지급은 기존대로 회당 1,000원 올림한다. FIXED_AMOUNT에는 해당 올림을 추가 적용하지 않는다.

지원 수업 보상과 해당 월 수동 기본급의 사유 필수 0원 예외, 지원 수업 외 추가실적의 양수 입력 조건을 유지한다. 정수 원 승인으로 모든 항목 0원/음수/누락을 허용하지 않는다. Trainer Rate 정밀도/범위는 H1/L2의 0~100% 정수로 확정됐다. 다른 항목별 남은 범위/상한·저장/계산 표현과 오류 계약은 BR-010 및 Architecture 후속이다.

Traceability: C11; PR-006/007/010/031; BR-010; BR-PAY-003/004/014/015; NFR-012. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch).

<a id="br-ops-019"></a>
## BR-OPS-019 — 기존 계정의 Operator·Trainer 역할 추가/회수

상태: APPROVED-TO-BE

2026-10-30 추가 승인: [I2-1/2/3 모두 1번](product-decisions.md#review-20261030-i2).
첫 Trainer 연결은 ACTIVE이며 로그인 준비가 된 기존 계정과 실제 활성 Trainer에만 허용한다.
같은 불변 연결의 재부여는 ACTIVE 또는 PENDING_SETUP 계정과 활성 Trainer에 허용하며 DISABLED는
추가/재부여할 수 없다. Home Branch 비활성만으로 거부하지 않는다. 회수는 현재 E5 관리 Scope에서
계정/Trainer 상태와 무관하게 허용한다. PENDING_SETUP 회수→재부여→명시 새 초기 링크 발급→설정
완료 경로를 제공하며 회수된 옛 링크를 복원하지 않는다.

유효 로그인 역할이 0이면 새 로그인과 기존 인증 접근을 허용하지 않는다. 마지막 역할 회수 자체는
허용하되 계정·암호·동일인 연결·역사를 보존하며 자동 DISABLED/삭제/암호 reset은 하지 않는다.
재부여 후에는 현재 계정 상태와 인증 조건을 충족할 때 기존 유효 암호를 다시 사용할 수 있다.
실제 Trainer 역할 추가·회수·재부여 성공은 대상의 현재 로그인 포함 모든 AuthSession을 철회한다.
독립 관리자 역할·Passkey·다른 계정·C2는 보존하며 남은 관리자는 password+UV로 재로그인한다.
no-op·replay·status는 새 로그인을 다시 철회하지 않는다. 이 승인은 Trainer 역할 범위이며
Operator 구현·관리자 승격·다른 사람 재연결·소속/상태 변경·분실 암호 reset을 포함하지 않는다.

E5의 2번 승인: Master Admin은 자기 Organization, Branch Admin은 자기 관리 범위에서 기존 계정의 Operator·Trainer 역할만 추가·회수할 수 있다. Operator의 단일 지정 Branch/추가할 최초 Branch와 실제 Trainer의 현재 Home Branch를 각 대상 역할의 관리 범위로 검증한다. 같은 계정의 관리자 역할이나 다른 역할이 자기 지점이라는 사실만으로 범위 밖 대상 역할을 변경하지 않는다. 현재 Caller·대상 계정/역할·실제 Organization/지점 사실과 동일인/Trainer 연결 확인이 필요하다. 연결을 임의로 덮어쓰거나 역할 부여로 Trainer 소속을 변경하지 않는다.

독립 Master/Branch Admin 역할·다른 역할/Scope, 기존 Trainer/계정 식별과 업무/감사 이력을 보존한다. Master 전용 관리 역할/관리 Branch 변경·Operator 지점 변경·Trainer Home Branch 이동·계정 전체 차단/복구·관리자 암호 reset·Login ID 변경/인증 감사 열람 권한은 위임하지 않는다. 역할 회수/재부여를 지점/소속/연결 변경의 우회 수단으로 사용하지 않는다. 기존 Trainer 업무 비활성화/재활성화와 계정 전체 상태는 별개다.

저장 이후 후속 업무는 현재 역할/Scope로 검증하고 회수된 권한을 허용하지 않는다. 변경 전후 역할/Scope·대상·검증된 Actor/역할·Branch Context·시점을 감사하며 거부/저장·필수 감사 실패에 일부 권한 변경이나 이력 손실을 남기지 않는다. 2026-10-30 Trainer 대상 상태·무역할 로그인·전 로그인 철회는 위 I2 승인으로 해결됐다. Operator의 나머지 상태/역할 조합과 최소 선택/연결 기술 계약·진행 중 요청·UoW/잠금/경합은 Architecture 및 관련 OPEN 후속이다. A7 관리 역할/관리 Branch 변경의 전 로그인 철회와 혼동하지 않는다.

Traceability: E5; PD-001/019; PR-001/021/027/029/030; BR-OPS-011/012/013/014; ARCH-001/002; MB-001/004; NFR-001/002/004. [2026-10-12 E 일괄 승인](product-decisions.md#review-20261012-e-batch).

<a id="br-pay-018"></a>
## BR-PAY-018 — Trainer Rate 정수 퍼센트 입력

상태: APPROVED-TO-BE

2026-10-12 H1=2: Trainer Rate는 정수 퍼센트만 허용한다. 50%는 허용하고 50.25%처럼 소수 부분이 있는 비율은 입력을 거부하며 임의 반올림/절사로 바꾸지 않는다. 입력 실패 시 기존 설정/감사/확정 지급을 변경하지 않는 원칙을 따른다. RATE 계산 결과는 기존 BR-PAY-003/013의 수업별 1,000원 단위 올림을 적용하고 FIXED_AMOUNT에는 추가 적용하지 않는다. 기존 생성 시점 Trainer 설정·발급 Pass 조건 사용과 과거 확정 지급 불변성을 유지한다.

범위/후속: 정수 원화 입력(C11/BR-PAY-017)과 비율 단위를 구별한다. 50% 예시는 기본값이 아니다. L2로 Rate 허용 범위는 0~100% 정수로 추가 확정됐고 명시적 0%와 누락/미설정은 구분한다. 저장 타입/계약·수치 표현과 다른 금액 항목의 남은 제약은 후속이다. PR-007/008, NFR-012, BR-010. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch). V-90은 미구성·미실행 계획이다.

2026-10-13 L2=1: Trainer Rate는 최소 0%, 최대 100%를 포함한 정수만 허용한다. 0/50/100 허용, -1/101/50.25 거부이며 임의 범위 보정·반올림/절사는 하지 않는다. 명시적으로 설정한 0%의 일반 RATE 수업 지급액은 기존 계산식상 0원이다. 누락/미설정을 0%나 예시 50%로 대체하지 않는다. Master Organization/Branch Admin 현재 Trainer Home Branch 기준의 설정 권한·본인 포함/별도 승인 없음·감사, OP/Trainer 단독 조회/변경 금지와 과거 확정 지급 불변을 유지한다. 100%에서도 기존 수업별 1,000원 올림을 적용하며 회당 판매 단가 이하라는 새 지급 상한을 두지 않는다. FIXED_AMOUNT/추가실적/기본급의 별도 조건은 변경하지 않는다. [L 일괄 승인](product-decisions.md#review-20261013-l-batch), PR-007/008·NFR-012·BR-010; V-105는 미구성·미실행 계획이다.

<a id="br-pay-019"></a>
## BR-PAY-019 — 지원 수업 외 추가실적의 내용 정정·취소

상태: APPROVED-TO-BE

2026-10-12 H2=1: Master Admin은 자기 Organization, Branch Admin은 각 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 범위에서 지원 수업 외 Additional Performance의 내용 수정/취소를 허용한다. 관리 범위 안 본인 건 포함·별도 승인 없음·사유와 변경 전후 내용/상태·Actor/Role/Branch Context/시점 이력·감사 필수다. 과거 등록자/소속·지원받은 지점만으로 권한을 유지하지 않고 Operator/Trainer 단독은 불가다. 취소는 원래 금액/내용·발생/귀속 이력을 보존하면서 해당 실적을 유효 정산/지점 비용 합산에서 제외한다. 0원/음수 덮어쓰기·다른 월 상계로 취소를 대신하지 않는다. 비지원 실적 취소만으로 연결된 일반 PT/Pass 차감·일반 지급을 취소하지 않는다.

2026-10-12 H3=1: 대상 Trainer 또는 실제 발생 날짜 오류는 원래 실적 취소 후 올바르게 재등록하고 원본/취소/새 기록을 연결한다. 원본 Trainer/발생 날짜를 덮어쓰지 않는다. 원래 건 취소와 새 건 등록의 현재 Trainer Home Branch/Organization 권한을 각각 검증하며 한쪽 지점의 권한으로 다른 쪽 업무를 허용하지 않는다. 새 금액도 기존 관리자 수동 입력/양수, 실제 발생 월 정산 및 당시 Home Branch 비용 귀속을 따른다. 영향받는 각 확정 Trainer/월은 기존 관리자 Scope/사유·해제 → 처리 → 해당 월 재확정/이전 확정본 보존을 적용한다. 확정 상태에 직접 변경하거나 새 등록 월로 이월하지 않는다. 사유 누락/범위 밖 요청은 기존 데이터 보존·필수 변경 원자성 원칙을 따른다.

범위/후속: 타 지점 지원 수업 보상의 PT 연결 관계를 임의 교체하는 정책이 아니다. 지원 수업의 기존 수업 취소/보상 무효·미입력 추적/확정 차단 규칙은 유지한다. 실제 발생/소속 사실 확인 불가·나머지 내용/연결 필드·정산 결과 영향 판정·여러 Trainer/월 단계별 순서/실패·재시도/정정 연결 저장·UoW/잠금은 후속이다. PR-031/010/027/030, NFR-001/002/004, BR-009/013, MB-006/010. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch). V-91/92는 미구성·미실행 계획이다.

<a id="br-ops-020"></a>
## BR-OPS-020 — 회원 기본 필수정보와 v1 제외 항목

상태: APPROVED-TO-BE

2026-10-12 I2=1: 회원 이름·전화번호·하나의 Home Branch를 필수로 관리하며 생년월일·성별은 v1에서 제외한다. 정상 등록 시 누락/빈 이름·번호 또는 Home Branch 없는 상태를 허용하지 않고 일반 수정으로 필수값을 비우지 않는다. 기존 전화번호 중복 허용/별도 Member 식별·임의 병합/첫 검색 결과 자동 선택 금지는 유지한다. 이름을 고유 식별자로 삼지 않는다.

기존 역할/행위별 Organization·Branch/담당·개별 지원 인가와 Home Branch 변경·이력 규칙을 유지한다. 필수정보 채택이 새 등록/수정/조회 권한·Member 인증 승인으로 확대되지 않는다. 다른 추가 필드·전화번호 형식/정규화·최소 공개 계약/보존/필요 삭제는 LEGAL-001·ARCH-001·MB-002 후속이다. 생년월일 저장을 전제로 하는 생일 목록(PR-024)은 v1에서 제공하지 않는다. PR-002/024, NFR-005, BR-OPS-006. [2026-10-12 I 일괄 승인](product-decisions.md#review-20261012-i-batch). V-95는 미구성·미실행 계획이다.

2026-10-12 J1–J3 승인: 등록/이름·전화번호 수정 권한은 BR-OPS-021, Member 자체 비활성화/재활성화의 관리자 범위·새 Pass/비활성 기간 수업 차단과 기존 잔여/이력 보존은 BR-OPS-022를 따른다. 필수 정보/별도 Member 식별·독립 소속 이동/현재 인가·다른 공개 제한은 유지한다. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch).

<a id="br-ops-021"></a>
## BR-OPS-021 — 회원 등록·이름/전화번호 수정 권한

상태: APPROVED-TO-BE

2026-10-12 J1=1: Master Admin은 자신의 Organization 전체 Member 등록/이름·전화번호 수정을 허용한다. Branch Admin은 단일 관리 Branch, Operator는 지정 단일 업무 Branch에 한해 허용한다. 신규 등록은 지정할 Member Home Branch, 기존 수정은 처리 시점 실제 Member 현재 Home Branch가 해당 지점인지 검증한다. Trainer 역할만으로는 불가며 겸임자의 독립 관리/Operator Scope는 각각 검증한다. 등록자/이전 소속·Pass Issued Branch/실제 Performed Branch 또는 담당/지원 관계만으로 수정 권한을 얻지 않는다.

I2의 필수 이름/전화번호/하나의 Home Branch·생년월일/성별 v1 제외와 전화번호 중복 허용·별도 Member 식별/임의 병합 금지를 유지한다. 일반 수정으로 필수값을 비우지 않고 변경하지 않는 값은 유지한다. Operator의 신규 회원 Home 지정은 등록 권한이며 기존 Member Home 이동은 계속 불가다. 다른 필드/대상 상태·전체 목록/상세·일괄 내보내기나 Pass/PT/보상·정산 권한은 자동 추가하지 않는다. 기존 Branch 비활성의 새 배정 차단·Organization/현재 역할·Scope 검증과 중요 변경 감사·실패 보존을 적용한다. 최소 선택/수정 응답·필드별 인가/입력/감사 저장·UoW/동시 소속·역할/Branch 변경 계약은 후속이다. PR-002/027/030, NFR-001/004/005, ARCH-001, MB-002, BR-OPS-006/007/011/020. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch). V-98은 미구성·미실행 계획이다.

<a id="br-ops-022"></a>
## BR-OPS-022 — 회원 비활성화·재활성화와 이용권 보존

상태: APPROVED-TO-BE

2026-10-12 J2=1: Master Admin은 자기 Organization 전체, Branch Admin은 각 처리 시점 실제 Member 현재 Home Branch가 자신의 단일 관리 Branch인 경우 Member 비활성화/재활성화를 허용한다. Operator·Trainer 역할만으로는 불가며 겸임자의 독립 관리자 Scope로 판단한다. 이전 소속/처리자·Pass 발급/수업 수행 지점만으로 권한을 유지하지 않는다. 기존 중요 상태 변경의 대상/전후 상태·Actor/Role/Branch Context·시점 이력/감사를 적용하며 이번 결정으로 새 필수 사유/별도 승인 단계를 도입하지 않는다.

2026-10-12 J3=1: Member 자체 비활성 상태에서는 새 Pass 발급과 비활성 기간 실제 수업을 차단한다. 잔여가 남아 있어도 비활성화할 수 있고 기존 Pass의 잔여·발급 조건/담당·Home/지원 관계/과거 PT 소비·확정 지급/추가실적·정산/감사는 보존한다. 다른 지점/지연 등록으로 비활성 기간 수업을 우회하지 않는다. 잔여 0은 자동 Member 비활성화 사유가 아니고 기본 조회/선택 제외 필터의 기존 규칙을 유지한다. Member 비활성화만으로 Pass를 삭제/자동 만료하거나 잔여를 0/복원 처리하지 않는다.

복귀 시 같은 Member를 재활성화하며 기존 Pass는 현재 잔여 > 0·개별 만료/실제 Trainer/Performed Branch 상태·현재 인가 등 독립 사용 조건을 충족해야 이용한다. 상태 복귀가 기존 Pass의 수동 만료 해제/새 발급·다른 대상 상태 변경/권한 확대 또는 비활성 기간 실제 수업·과거 확정 지급/정산 자동 유효화/재계산을 의미하지 않는다. 비활성화 전 실제 수업 누락/정정은 기존 과거 업무의 인가/Pass·사실/정산 규칙을 유지하며 새 조회/대행 권한을 추가하지 않는다.

Member 상태와 Home Branch 상태·Trainer 상태/계정 수명은 구분한다. G4의 Home Branch 비활성 회원의 다른 활성 지점 이용은 Member 자체가 활성이고 기존 업무 조건을 충족할 때 유지한다. 실제 수업 당시 Member 상태 이력과 현재 발급/수정·PT 인가·월 확정을 구분하는 계약·확인 불가/역사 정정·다른 상태 조합/공개·상태 저장/UoW/잠금·경합은 후속이다. PR-003/004/008/009/027/030, NFR-001/002/003/004, ARCH-001/003, BR-001/007/008, MB-002/003/005/008. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch). V-99/100은 미구성·미실행 계획이다.

<a id="br-ops-023"></a>
## BR-OPS-023 — PT 시작 날짜·시각 오류의 취소 후 재등록

상태: APPROVED-TO-BE

2026-10-12 K1=1: PT 실제 시작 날짜/시각 오류는 원본 취소 후 올바른 실제 시작 시점으로 재등록하고 원본·취소·새 기록/정정 연결·감사를 보존한다. 소비 횟수 복원/원래 수업 보상 유효 합산 제외는 기존 취소 규칙을 따르고, 새 기록은 올바른 수업 시점의 실제 소속/담당·Member/Trainer/Branch 상태·당시 발급된 적격 Pass와 현재 잔여 및 현재 Caller/업무 Scope·월 정산 조건을 확인한다. FIXED_AMOUNT 우선/동일 Type FIFO로 재선택·1회 차감하며 원래 Pass 고정/수업 후 발급 Pass 사용은 허용하지 않는다. 시각 확인/I1·Member 비활성 기간 차단/J3를 유지한다.

새 일반 지급은 선택 Pass 발급 조건과 재등록 생성 시점 실제 수행 Trainer Rate/Fixed Amount로 계산·확정하고 기존 RATE 1,000원 올림/FIXED 추가 올림 없음 규칙을 적용한다. 일반/지원은 올바른 실제 시점 Home Branch와 Performed Branch 기준이다. 원래 지급/지원 보상은 이력으로 보존/유효 합산 제외하며 새 지원 수업은 기존 관리자 수동 보상·미입력/0원 구별/미입력 월 확정 차단을 따른다. 새 지급을 원본에 덮어쓰거나 기존 지원 금액을 자동 복사해 확정하지 않는다.

기존 PT 취소/정정의 Master Organization/Branch Admin 실제 Performed Branch 범위·각 단계 인가와 Performed Branch 값 정정 Master 전용을 유지한다. 영향받는 각 확정 Trainer/월은 현재 Trainer Home Branch 기반 관리자 Scope·사유/해제·처리/해당 월 재확정·이전 확정본 보존을 각각 적용한다. 원본 날짜/시각을 덮어쓰는 경로로 월/상태·수업/Pass 사실 검증을 우회하지 않는다. 기존 Performed Branch 값 정정의 기록 유지/최초 생성 시점 설정 정책은 별개다. 정정 연결/여러 월 순서·취소/재등록 실패·재시도/UoW/잠금/역사 사실 확인 불가·정정은 후속이다. PR-008/009/010, NFR-001/002/004/012, BR-007/008/009, MB-005/010. [2026-10-12 K 일괄 승인](product-decisions.md#review-20261012-k-batch). V-101은 미구성·미실행 계획이다.

<a id="br-ops-024"></a>
## BR-OPS-024 — Trainer 신규 등록·이름/연락처 수정 권한

상태: APPROVED-TO-BE

2026-10-12 K2=1: Master Admin은 자기 Organization 전체, Branch Admin은 자기 단일 관리 Branch에 Trainer 신규 등록과 이름/연락처 수정을 허용한다. 신규 등록은 지정할 Home Branch, 기존 수정은 처리 시점 실제 Trainer 현재 Home Branch를 검증한다. Operator·Trainer 역할만으로는 불가며 겸임자의 허용된 독립 관리자 Scope로 판단한다. 과거 소속/등록자·계정 발급자·지원 수업/Pass·Member 지점만으로 권한을 얻지 않는다.

기존 Trainer Home Branch 변경은 Master 전용이며 기본정보 수정에 섞어 우회하지 않는다. 회원 관리 Operator 권한(J1)을 Trainer 관리로 확대하지 않고 일반 기본정보와 IAM 계정/ID·역할/연결·암호, Compensation Setting 권한을 구별한다. 기본정보 수정만으로 다른 역할/Scope·계정 연결·보상 설정/과거 PT·지급/정산을 변경하지 않는다. 기존 비활성 Branch 신규 배정 차단·중요 변경 감사/개인정보 제한을 유지하며 최초 보상 필수 입력은 BR-OPS-028, 일반 Fixed Amount/Base Salary의 입력 범위는 BR-PAY-022로 확정됐다. Trainer 전화번호 필수는 BR-OPS-029로 확정됐다. 형식/정규화·다른 필드/공개·미결정 월 경계/상한·최소 읽기/저장·계정 준비/연결·현재 인가/UoW/경합은 후속이다. PR-005/007/021/027/029/030, NFR-001/004/005, ARCH-001/002, MB-001/004. [2026-10-12 K 일괄 승인](product-decisions.md#review-20261012-k-batch). V-102는 미구성·미실행 계획이다.

2026-10-13 Q1/Q2=1 후속: Trainer 최초 등록 완료에는 BR-OPS-028의 세 보상 값/기본급 시작 월 명시 입력과 최초 설정 인가·감사가 필요하다. 일반 Fixed Amount/Base Salary는 BR-PAY-022의 0원 이상 정수 원이다. 기존 기본정보 수정/이동/계정·보상의 권한 분리는 유지하며 기본정보 수정으로 보상 재입력/미전달 초기화를 요구하지 않는다. 연락처 필수 여부/다른 필드·월 범위/상한/최소 계약은 별도 후속이다. [Q 승인](product-decisions.md#review-20261013-q-batch); V-114/115 미구성·미실행.

2026-10-13 R1=1 후속: Trainer 전화번호는 필수이며 최초/일반 수정의 필수값 유지는 BR-OPS-029를 따른다. 기존 신규 지정/수정 현재 Home의 관리 인가·Operator/Trainer 단독 금지와 IAM/보상 권한 분리는 유지한다. [R 승인](product-decisions.md#review-20261013-r-batch); V-116 미구성·미실행.

<a id="br-pay-020"></a>
## BR-PAY-020 — 종료된 월의 정산 확정

상태: APPROVED-TO-BE

2026-10-13 L1=1: 월 정산은 Organization 공통 시간대 Asia/Seoul의 달력 기준으로 종료된 월만 확정할 수 있다. 다음 달 1일 00:00부터 직전 월이 시간상 확정 대상이 된다. 당월/미래 월 확정은 Master Admin을 포함하여 허용하지 않는다. 당월은 미확정 상태로 기존 관리자 공개 범위 안에서 조회·검토할 수 있고 관리자 권한 없는 Trainer의 월 정산 조회는 v1 제외(H4)를 유지한다.

시간 조건과 별개로 Master Organization/Branch Admin 각 처리 시점 대상 Trainer 현재 Home Branch 인가·관리 범위 안 본인 포함/별도 승인 없음·감사와 기존 구성/유효성·미입력 지원 수업의 해당 Trainer·월 확정 차단을 적용한다. 월 종료만으로 자동 확정하지 않는다. 오류 정정의 해제 → 반영 → 동일 월 재확정 및 이전 확정본 보존을 유지하며 재확정 시에도 종료된 월이어야 한다. 기본급의 미래 적용 시작 월을 미리 지정하는 기능의 범위를 이 규칙으로 제한하거나 확정하지 않는다.

추적: PR-010, NFR-012, BR-009, BR-PAY-014/016, [2026-10-13 L 일괄 승인](product-decisions.md#review-20261013-l-batch). 시간의 신뢰 근거·경계 판정/조회·동시 확정/등록·버전/UoW/잠금 계약은 후속 PROPOSED이며 V-104는 미구성·미실행 계획이다.


<a id="br-ops-025"></a>
## BR-OPS-025 — 미사용 이용권 발급 오류 처리

상태: APPROVED-TO-BE

2026-10-13 M1=1: 잘못 발급한 미사용 Pass는 기존 수동 만료로 잔여·원본 이력을 보존하고 올바른 Pass를 새로 발급한다. 별도 Pass 발급 취소 기능은 v1 제외다. 기존 Pass의 Member/상품/Issued Branch·발급 조건/담당·잔여·업무 이력을 새 발급 내용으로 덮어쓰거나 삭제하지 않는다. 수동 만료는 잔여를 0으로 만들거나 실제 수업 차감으로 처리하지 않는다.

만료는 BR-OPS-004의 Master Organization/Branch Admin 각 처리 시점 현재 관리 Branch=Issued Branch 인가·사유/전후 사용 상태/Actor/시점 이력·감사를 적용한다. 올바른 새 Pass는 별도 식별자로 기존 발급 권한·허용 Issued Branch/같은 Organization Member·판매 가능 상품/발급 조건·활성 담당/최초 상품 횟수·감사 등 정상 발급 조건을 검증한다. 두 업무 권한을 서로 자동 상속하지 않는다. 기존 만료 해제 정책은 유지하며 재발급만으로 원본을 자동 해제하지 않는다. 이 결정은 이미 수행된 PT의 취소/횟수 복원이나 결제·환불 기능 추가가 아니다.

추적: PR-003/027, BR-OPS-004/005/010, BR-001/002·ARCH-003, [2026-10-13 M 승인](product-decisions.md#review-20261013-m-batch). 단계별 실패/재시도·정정 관계 표현/조회·원자성/UoW·동시성은 후속 PROPOSED이며 V-106은 미구성·미실행 계획이다.


<a id="br-pay-021"></a>
## BR-PAY-021 — 수업별 보상 금액의 공개 제한

상태: APPROVED-TO-BE

2026-10-13 N1/N2=1: 관리자 권한 없는 Trainer에게 본인 PT 내역의 수업별 보상 금액을 공개하지 않는다. 현재 다른 Home Branch의 Trainer가 자기 지점에서 수업했더라도 해당 Performed Branch의 Branch Admin에게 그 수업의 보상 금액을 공개하지 않는다. 일반 Session Payment와 지원 수업에 연결된 Additional Performance 금액 모두 해당한다. 허용된 PT 진행 기록 조회는 유지하고 금액 조회와 독립적으로 인가한다.

Backend는 현재 Caller의 역할/Organization·행위별 Scope와 실제 현재 Trainer Home을 확인한다. PT 기록을 읽거나 정정할 수 있다는 사실, 본인 실제 수행·자기 Performed Branch·과거 Home/최초 Actor 사실을 금액 공개 근거로 사용하지 않는다. Master Organization 범위 및 현재 Home 기반 관리자의 기존 보상·정산 업무·월 정산 구성 공개는 유지하며 관리자·Trainer 겸임은 독립 관리 Scope를 검증한다. 본인이라는 이유만으로 인가된 관리자 조회를 거부하지 않으며 관리자 역할 보유만으로 범위 밖 금액을 공개하지 않는다. 다른 역할의 미결정 지급 조회 권한이나 다른 지점 PT 기록 전체 조회 권한을 추가하지 않는다.

비공개 금액은 기존 확정 지급/지원 보상의 원본과 정산 입력에 그대로 보존한다. 화면뿐 아니라 등록 성공 응답·목록/검색/상세/직접 ID·중첩 결과 및 제공되는 집계/감사/오류 경로의 우회 노출도 제한한다. 비공개를 가짜 0원이나 원본 삭제/재계산으로 표현하지 않는다. 보상 설정 비공개·H4 비관리자 Trainer 월 정산 v1 제외와 Master 전용 지점 비용 보고 제한을 유지한다. 금액 외 상태/계산 근거·필드 생략/응답 분리/오류 계약은 별도 후속이다.

추적: PR-008/010/029/030, BR-PAY-010/016, NFR-001/005, ARCH-001·MB-005/006/010, [2026-10-13 N 승인](product-decisions.md#review-20261013-n-batch). V-108/109는 미구성·미실행 계획이며 구체 모듈/조회·응답 계약/UoW/현재 권한 변경 경합은 PROPOSED다.


<a id="br-ops-026"></a>
## BR-OPS-026 — 담당·개별 지원 회원의 본인 PT 등록과 전체 적격 이용권 선택

상태: APPROVED-TO-BE

2026-10-13 O1/O2=1: Trainer는 허용된 담당 회원과 개별 허용 지원 회원에게 자신이 실제 수행한 수업을 등록할 수 있다. 개별 지원 회원은 본인 담당 Pass가 없어도 등록할 수 있다. 서버는 다른 Trainer 담당분/다른 Issued Branch도 포함한 해당 Member 전체 적격 Pass에서 BR-PAY-006의 FIXED_AMOUNT 우선/동일 Payment Type FIFO를 적용한다. Pass Assigned Trainer와 실제 수행 Trainer를 구별하며 선택/차감으로 담당자·Home/Issued/Performed Branch를 자동 변경하지 않는다.

같은 Organization/Member·검증된 현재 Caller/Trainer 연결·담당 또는 개별 지원 허용, 실제 수업 당시 이미 발급/사용 가능·현재 잔여 > 0와 기존 상태/늦은 등록·만료 예외/대상 월 정산 검증을 유지한다. 수업 이후 발급한 Pass나 부적격 Pass를 포함하지 않는다. 일반 수업의 지급은 실제 수행 Trainer의 기록 생성 시점 설정/선택 Pass 발급 조건으로 확정하며 Pass 담당자의 설정을 사용하지 않는다. 일반/타 지점 지원 보상 구분은 실제 수업 당시 Trainer Home과 Performed Branch를 비교한다. 개별 지원 관계 자체를 지원 보상 분류로 사용하지 않는다. 지원 수업 전체 보상은 기존 관리자 수동 추가실적 정책을 따른다.

지원 지정/해제의 각 처리 시점 Member 현재 Home Branch 관리자/Master Organization 인가, 관리자 해제 전 유지/같은 Organization Home 이동 후 유지·감사는 그대로다. 지원 지정 전/해제 후 과거 본인 수업 등록은 P1/P2의 BR-OPS-027을 따른다. 현재 유효 지원으로 지정 전 실제 수업을 허용하고 해제 후에는 실제 허용 기간의 수업만 허용하며 일반 Member/전화번호 조회를 복원하지 않는다. 역사 사실 확인 불가/충돌·정정/최소 계약은 MB-001/005 후속이다. BR-OPS-003의 이전 담당 당시 본인 실제 수업 등록 예외는 유지한다.

전체 후보의 내부 선택/차감은 다른 Member/개별 Pass·다른 Trainer 정보 무제한 공개가 아니다. 기존 회원/전화번호 조회와 N1/N2 금액 비공개·보상 설정/월 정산 제한을 유지한다. 지원 허용으로 다른 Trainer 대행·회원/Pass 발급/변경·PT 정정/취소·보상/정산 권한을 추가하지 않는다. 관리자 겸임자의 독립적인 기존 행위별 관리 Scope는 별도로 검증한다.

추적: PR-008/029/030, BR-OPS-003/005, BR-PAY-006/011/021, NFR-001/002/005, ARCH-003·MB-001/003/005, [2026-10-13 O 승인](product-decisions.md#review-20261013-o-batch). V-110/111는 미구성·미실행 계획이며 후보/최소 응답·역사 사실/인가·UoW/동시성의 구체 설계는 PROPOSED다.


<a id="br-ops-027"></a>
## BR-OPS-027 — 개별 지원 허용과 과거 본인 수업의 등록

상태: APPROVED-TO-BE

2026-10-13 P1/P2=1: 현재 Trainer/Member 개별 지원 허용이 유효하면 지정 전에 실제 진행한 본인 수업도 등록할 수 있다. 지원 지정 시점은 그대로 보존하고 실제 수업일로 기록하며 지원 이력을 소급 변경하지 않는다. 지원 해제 후에는 허용 기간에 실제 진행한 본인 수업에 한해 늦은 직접 등록을 허용한다. 과거 한때 지원 관계가 있었다는 이유로 허용 기간 밖 수업/다른 Trainer 수업을 P2로 등록하지 않는다. P1 지정 전 수업 등록의 근거는 현재 유효한 지원 허용이며 P2의 근거는 실제 수업 당시 지원 허용이다.

P2는 일반 Member 목록/검색/상세·전화번호 조회를 복원하지 않는다. 지원 해제 후 새로 진행한 수업까지 허용하지 않으며 별도의 현재 담당/지원/독립 관리자 근거는 해당 규칙으로 판단한다. 과거 본인 수업 등록에 필요한 최소 대상 식별/허용 명령의 응답과 사실 확인 경로는 후속 Architecture 대상이다. 재지정이나 담당 되돌리기·별도 관리자 승인을 필수로 추가하지 않는다. 기존 담당 교체 전 본인 수업의 늦은 등록 예외는 유지한다.

현재 검증된 Caller/본인 Trainer 연결·Organization·계정/Trainer 유효성, 실제 본인 수행 및 기존 수업 당시 상태/소속 사실을 확인한다. P2는 수업 당시 해당 지원 관계의 허용 기간도 검증한다. 요청이 주장하는 과거 허용이나 현재 사실로 역사 사실을 대신하지 않는다. P1의 현재 허용을 과거 허용 이력으로 기록하지 않는다. 계정 차단/역할 철회/Trainer 비활성의 접근을 되살리거나 미확인 사실을 임의 생성하지 않는다. 사실 확인 불가/충돌·정정/같은 시점 순서 및 저장/최소 공개·오류 계약은 후속이다.

해당 Member 전체 적격 Pass에서 다른 담당분도 포함한 FIXED_AMOUNT 우선/동일 Type FIFO, 실제 수업 당시 발급/사용 가능·현재 잔여 > 0·기존 만료 예외/1회 차감·진행 월 정산 조건을 유지한다. 일반 지급은 신규 생성 시점 실제 수행자 설정, 보상 구분은 실제 당시 Trainer Home/Performed Branch다. 지원 전체 수동 추가실적/미입력 월 확정 차단·금액 비공개를 유지한다. 확정 월은 기존 관리자 해제/반영/동일 월 재확정·사유/이전 확정본 보존을 따르며 Trainer에게 해제 권한을 부여하지 않는다. 지원 지정/해제의 현재 Member Home 관리자/Master Scope·기존 유지 기간/이동·감사를 유지하고 다른 업무/조회 권한을 추가하지 않는다.

추적: PR-008/029/030, BR-OPS-003/005/026, BR-PAY-006/011/021, NFR-001/002/005, MB-001/003/005, [2026-10-13 P 승인](product-decisions.md#review-20261013-p-batch). V-112/113은 미구성·미실행 계획이며 구체 계약/이력·최소 선택 경로/UoW/동시성은 PROPOSED다.


<a id="br-ops-028"></a>
## BR-OPS-028 — Trainer 최초 등록의 보상 필수 입력

상태: APPROVED-TO-BE

2026-10-13 Q1=1: 새 Trainer를 등록 완료하려면 Rate·Fixed Amount·Base Salary와 기본급 적용 시작 월을 명시적으로 입력한다. 기본정보만 등록 완료한 뒤 보상을 나중에 설정하는 흐름은 채택하지 않는다. 누락을 0%/50%/0원·현재 월로 채우지 않는다. 기본급은 시작 월부터 다음 변경까지 지속하며 적용 종료 월/미래 월 목록을 요구하지 않는다.

기존 Master Organization/Branch Admin 신규 Home Branch 기준의 Trainer 등록 권한과 보상 최초 설정 권한을 각각 검증하고 최초 보상/중요 등록 감사를 적용한다. Operator/Trainer 단독은 불가며 관리자 겸임의 독립 Scope는 유지한다. 필수값 누락/오류·권한 거부·저장 실패를 등록 완료로 보고하거나 사용할 수 있는 정상 Trainer만 일부 남기지 않도록 완료의 일관성을 설계한다. 구체 테이블/소유권·공개 계약/UoW/잠금/실패 재시도는 후속이다.

이후 이름/연락처 일반 수정에서 보상 세 값 재입력을 요구하거나 미전달 값을 초기화하지 않는다. 결합 입력이 같은 테이블/모듈 저장·IAM 계정/역할/암호/Trainer 연결의 자동 준비를 뜻하지 않는다. 기존 Trainer Home 변경 Master 전용·비활성 Branch 신규 배정 금지·보상 비공개와 생성 시점 지급/과거 확정 결과 불변을 유지한다. 미래 시작 월 범위·최초 시작 월 이전 월의 적용 사실 등 미결정 월 상세를 0원으로 대체하지 않는다.

추적: PR-005/007/027, BR-OPS-024, BR-PAY-022, NFR-001/002/004/012, BR-010/012·MB-001, [2026-10-13 Q 승인](product-decisions.md#review-20261013-q-batch). V-114는 미구성·미실행 계획이며 구체 등록/감사·저장/계약/UoW/동시성은 PROPOSED다.

R1 필수 기본정보 추가: 최초 Trainer 등록에는 BR-OPS-029의 전화번호 필수도 적용한다. 기존 세 보상 값/시작 월 명시 입력과 등록 완료/최초 감사의 일관성은 유지하며 연락처 입력을 계정/본인인증·보상 공개 권한으로 사용하지 않는다. [R 승인](product-decisions.md#review-20261013-r-batch); V-116 미구성·미실행.

<a id="br-pay-022"></a>
## BR-PAY-022 — 일반 Fixed Amount·Base Salary의 0원 허용과 음수 금지

상태: APPROVED-TO-BE

2026-10-13 Q2=1: Trainer 일반 Compensation Setting의 Fixed Amount·Base Salary는 0원 이상 정수 원만 허용한다. 최초 설정/이후 변경 모두 적용하며 음수/소수 원·누락/null을 거부하고 자동 0원/범위 보정/절사하지 않는다. Rate는 기존 0~100% 정수 규칙을 유지한다. 금액 상한·수치 저장/검증·오류 계약은 별도 후속이다.

명시적 Fixed Amount 0원은 일반 FIXED_AMOUNT 수업에 0원을 적용한다. 서비스 상품도 해당 Trainer의 실제 설정값을 사용하며 미설정을 서비스라는 이유로 0원 대체하지 않는다. RATE 올림을 다시 적용하지 않는다. 명시적 Base Salary 0원은 해당 설정 적용 월의 일반 기본급 0원이며 다른 지급/추가실적은 기존대로 합산한다. 일반 기본급은 시작 월부터 다음 변경까지 유지하고 종료 월을 요구하지 않는다.

기존 현재 Trainer Home 기반 Master/Branch Admin 설정 권한·관리 범위 안 본인 허용/별도 Master 승인 없음·최초/변경 감사와 Operator/Trainer 단독 비공개·타 지점 지원 관리자 접근 금지를 유지한다. 일반 설정 0원에 다른 업무의 별도 사유/승인 절차를 복사하지 않는다. 지원 수업 보상/월별 수동 기본급의 사유 필수 0원과 기타 추가실적 양수 전용 규칙은 그대로다. 설정값 변경의 신규 생성 일반 지급 적용·기본급 월 적용/미확정 반영과 과거 확정 지급/월 정산 자동 변경 금지를 유지한다. 0원은 누락이나 비공개용 가짜 값이 아니다.

추적: PR-007/008/010, BR-PAY-004/005/011/012/015/016/017/018/021, NFR-012, BR-010/012, [2026-10-13 Q 승인](product-decisions.md#review-20261013-q-batch). V-115는 미구성·미실행 계획이며 입력/최소 응답·저장/계약/UoW/경합은 PROPOSED다.


<a id="br-ops-029"></a>
## BR-OPS-029 — Trainer 전화번호 필수 입력

상태: APPROVED-TO-BE

2026-10-13 R1=1: Trainer 전화번호는 이름·단일 Home Branch와 함께 관리하는 필수 기본정보다. 최초 등록 및 일반 수정으로 전화번호를 누락/null/빈 값으로 저장하지 않는다. 미변경 필드는 유지하며 이름만 수정할 때 보상 세 값/전화번호의 재입력을 요구하지 않는다. 신규 등록은 Q1/Q2의 세 보상 값/기본급 시작 월 명시 입력·일반 금액 범위/최초 감사·등록 완료 일관성을 함께 적용한다.

기존 Master Organization/Branch Admin 신규 지정 Home·수정 시 현재 Home 기준 인가, Operator/Trainer 단독 수정 금지·관리자 겸임의 독립 Scope를 유지한다. 전화번호를 Login ID/본인인증 수단으로 사용하거나 값만으로 계정/Trainer/Member를 합치지 않는다. IAM 계정/역할/연결·보상 설정/과거 PT·지급/정산은 자동 변경하지 않는다. 다른 개인정보/공개 권한·형식/정규화·중복/보존·삭제/계약은 후속이고 실제 번호를 문서/일반 로그에 남기지 않는다.

추적: PR-005/027/030, BR-OPS-024/028, NFR-001/002/004/005, MB-001·LEGAL-001, [2026-10-13 R 승인](product-decisions.md#review-20261013-r-batch). V-116은 미구성·미실행 계획이며 필드/최소 응답·저장/UoW/경합은 PROPOSED다.

<a id="br-ops-030"></a>
## BR-OPS-030 — 자기 지점의 지점명·대표 연락처 수정 권한

상태: APPROVED-TO-BE

2026-10-13 R2=1: Branch Admin은 각 처리 시점 현재 자기 단일 관리 Branch의 지점명·대표 연락처를 수정할 수 있다. Master는 기존 자기 Organization 전체 Branch 관리 권한을 유지한다. Operator/Trainer 단독은 불가며 관리자 겸임의 독립 관리 Scope를 적용한다. Backend는 검증된 현재 Actor/Organization·대상 Branch/현재 관리 범위와 수정할 두 필드를 검증하고 직접 ID·요청 role/Branch·과거 Scope/등록자만으로 다른 지점/업무를 변경하지 않는다.

대상 Branch·변경 항목/전후 값·Actor/Role/Branch Context·시점의 기존 중요 변경 감사를 적용하며 별도 Master 승인 대기를 추가하지 않는다. 지점 생성·운영 상태 변경·관리자 배정/계정 관리 Branch·Organization/Branch 식별자/소속 이동·상품/보상/정산은 이번 수정 권한에 포함하지 않는다. 이름/연락처 변경으로 기존 Home/Issued/Performed 지점 사실·잔여/확정 지급·정산을 재작성하지 않는다.

두 필드의 입력 조건/대표 연락처 필수 여부·과거 표시 이름/이력 표현·최소 응답/감사 공개·현재 권한 변경/실패 계약은 후속이다. K3 첫 관리자 개발 범위를 이 승인으로 확대하지 않는다.

추적: PR-020/027/030, NFR-001/002/004/005, MB-004·ARCH-001, [2026-10-13 R 승인](product-decisions.md#review-20261013-r-batch). V-117은 미구성·미실행 계획이며 모듈/공개 계약·저장/UoW/경합은 PROPOSED다.


<a id="br-pay-023"></a>
## BR-PAY-023 — 과거 정산·보상 설정 변경 이력 조회

상태: APPROVED-TO-BE

2026-10-13 S1/S2=1: 이전 월 정산 확정본·확정 해제/재확정 이력과 Rate/Fixed Amount/Base Salary 변경 이력의 전후 값·변경자·시점은 Master 자기 Organization 또는 조회 시점 해당 Trainer의 현재 Home Branch를 관리하는 Branch Admin에게 공개한다. 기존 정정 이유/당시 버전·최초 설정 이력도 포함한다. 조회마다 Backend가 현재 검증된 역할/Organization·관리 Branch와 대상 Trainer 현재 Home을 확인하며 목록/검색·상세/직접 ID·제공되는 중첩 응답에도 적용한다. 이전 소속/변경자·Performed Branch만으로 계속 접근하지 못한다. 관리 범위 안 본인 Trainer의 독립 관리자 겸임 Scope는 허용하고 Operator/Trainer 단독은 본인 포함 불가다.

수원 소속 때의 월 정산/설정 변경 이력도 강남으로 이동한 뒤 현재 강남 Branch Admin이 조회한다. 이전 수원 Branch Admin은 별도 현재 권한 없이 조회하지 못한다. 조회 권한이 바뀌어도 원래 확정 금액/구성·이전 버전·정정 이유/변경자·당시 Role/Branch Context·시점은 보존한다. 최초 설정 이전 값 없음과 명시적 0원을 구별하며 현재 설정으로 과거 지급/확정 정산을 재계산하거나 감사 사실을 재작성하지 않는다.

기존 정산 전체 금액/구성(타 지점 수업 포함) 공개와 보상 설정 세 항목 동일 인가·직접 변경/감사를 유지한다. 이력 조회만으로 확정 해제/정정/재확정 또는 현재 설정 변경 권한/조건을 면제하지 않는다. 다른 지점 PT/Member/Pass 전체 원본·다른 Trainer 이력·지점 비용 보고서 접근은 추가하지 않는다. N1/N2 수업별 보상 기밀성·H4 비관리자 Trainer 월 정산 v1 제외와 C7 인증/계정 관리 감사 Master 전용은 유지한다. 일반 Audit 전체 조회/내보내기 기능 승인이 아니다.

최소 변경자 식별/응답·추가 계산 근거/버전 필드·개인정보/감사 보존·현재 권한 변경과 조회 경합·저장/계약은 후속이다. 인증정보/불필요한 개인정보 필드를 추가 공개하지 않는다.

추적: PR-007/010/027/030, NFR-001/004/005, ARCH-001·MB-006·BR-009, [2026-10-13 S 승인](product-decisions.md#review-20261013-s-batch). V-118/119는 미구성·미실행 계획이며 구체 모듈/최소 응답·저장/UoW/잠금은 PROPOSED다.


<a id="br-ops-031"></a>
## BR-OPS-031 — Pass 발급 시각과 사용 시작

상태: APPROVED-TO-BE

2026-10-13 T1/T2=1: Pass 발급 시각은 시스템에서 신규 발급을 완료한 시각으로 Backend가 기록한다. 과거 발급 날짜 입력/소급 발급과 기존 발급 시각 수정은 v1 제외다. 별도 사용 시작일 없이 발급 시점부터 기존 잔여/상태·인가 등 사용 조건을 충족할 때 사용할 수 있다. 미래 시작일 예약/변경·별도 시작 명령을 추가하지 않는다.

실제 수업 당시 이미 발급된 적격 Pass만 차감 후보에 포함한다(BR-PAY-006). 10월 3일 구매/10월 5일 시스템 발급이면 그 Pass로 10월 3일 수업을 등록할 수 없다. 현재 보유/잔여·담당/지원·관리자 권한 또는 구매/입력 지연을 이유로 발급 시각을 소급하거나 실제 수업 시각을 임의 변경하여 우회하지 않는다. 다른 적격 후보에는 기존 FIXED_AMOUNT 우선/동일 Type FIFO를 적용하며 적격 후보가 없으면 이후 발급된 Pass로 대체하지 않는다.

기존 발급 인가/Organization·활성 담당·최초 횟수/발급 조건 보존·감사와 Member 전체 적격 후보·현재 잔여 > 0/정상 1회 차감은 유지한다. 별도 만료일/자동 만료 없음·관리자 수동 만료/해제와 원본/잔여 보존·만료 전 실제 수업의 늦은 등록 예외도 유지한다. 발급만으로 Caller/Member/PT 권한·실제 수업 상태/정산 조건을 면제하지 않는다. 발급 시각은 실제 수업 시작 및 PT 기록 생성 시각/일반 지급의 생성 시점 설정과 구별하며 과거 확정 지급/정산은 재계산하지 않는다. 오류 Pass의 수동 만료 후 정상 새 발급에도 새 발급 시각을 적용하고 원본을 덮어쓰지 않는다.

같은 시각 정밀도/정렬·동시 발급/사용·실패/commit 응답 유실·최소 시간/응답·과거 만료/해제 사실·취소 복원/저장 계약은 후속이다. 시간 저장 형식/상태명·모듈/UoW/잠금은 이 제품 승인으로 채택하지 않는다.

추적: PR-003/008/027/030, BR-PAY-006·BR-OPS-003/004/025/026, NFR-002/004/012, BR-001·ARCH-003, [2026-10-13 T 승인](product-decisions.md#review-20261013-t-batch). V-120/121은 미구성·미실행 계획이다.


<a id="br-ops-032"></a>
## BR-OPS-032 — 과거 Home Branch 소속 이력 오류 정정

상태: APPROVED-TO-BE

2026-10-13 V1=1: 이미 기록된 Trainer/Member의 과거 Home Branch 소속 이력 오류는 Master만 자기 Organization 범위에서 사유를 남기고 정정할 수 있다. Backend는 현재 검증된 Master·대상 Trainer/Member와 소속 지점 사실의 Organization을 확인한다. Branch Admin은 현재 Home/이동 전후 지점의 관리자여도 불가하며 Operator/Trainer 단독도 불가다. 겸임자는 현재 Master의 독립 관리 Scope로 판단한다. 사유 누락 시 정정을 거부하고 기존 사실/이력·업무 결과를 유지한다.

원래 소속 이력과 정정 대상/전후 사실·사유/Actor/현재 권한·Branch Context·정정 처리 시점을 보존/추적한다. 소속 사실의 과거 시점과 정정 처리 시각을 구별하고 원래 기록을 삭제하거나 감사 없이 덮어쓰지 않는다. 일반 이동은 기존 즉시 적용/미래 예약 미지원·Actor 범위를 유지하며 과거 오류 정정은 별도 작업으로 취급한다. 확인되지 않은 과거를 현재 Home/임의 지점·시각으로 대체하지 않는다.

과거 PT/Pass 소비·일반 지급/지원 보상·월 정산 확정본은 이력 정정만으로 자동 재작성/재계산하지 않는다. 영향 건은 기존 업무별 권한·정정/사유/이력과 필요한 각 Trainer/월 확정 해제 → 반영 → 같은 월 재확정/이전본 보존 절차를 따른다. 정정 후 일반/지원 분류가 달라지는 기존 PT의 정정 방식/Pass 처리·지급 적용 설정 시점·비용 보고 정정/버전 계약은 후속이다. 기존 실제 당시 Home/Performed 보상 구분과 월말/발생 당시 Home 비용 귀속·한 번 합산은 유지한다.

과거 오류 정정으로 Pass 발급 시각/지원 지정 이력을 소급 변경하거나 계정/역할/관리 Scope·담당/지원·설정/인증 이력을 자동 재작성하지 않는다. 현재 Home에 미치는 영향·상태 조합·최소 응답/이력 공개/영향 식별·역사 사실·저장/UoW/경합은 후속이며 일반 Audit 열람 권한을 추가하지 않는다.

추적: PR-002/005/009/010/027/030, BR-OPS-007/013, NFR-001/002/004/012, MB-001/002/005/010, [2026-10-13 V 승인](product-decisions.md#review-20261013-v-batch). V-123은 미구성·미실행 계획이며 구체 모듈/최소 계약·저장/UoW/잠금은 PROPOSED다.

W1/W2 후속: Trainer 과거 Home 오류로 바뀌는 기존 PT 분류는 BR-OPS-033의 Master Organization 전용 명시적 정정으로 같은 PT/차감·최초 생성 시각을 유지한다. 일반은 최초 기록 생성 시점 설정/기존 소비 Pass 발급 조건, 지원은 기존 관리자 Scope의 수동 추가실적이며 이전 보상 이력/유효 합계 단일 반영을 보장한다. 영향 건의 분류/보상·비용 정정 완료 전 해당 Trainer·월 확정/재확정은 BR-PAY-024로 차단한다. 기존 확정본 자동 변경 없이 필요한 월의 기존 권한/사유·해제/정정/같은 월 재확정·이전본 보존을 따른다. [W 승인](product-decisions.md#review-20261013-w-batch); V-124/125 미구성·미실행.

<a id="br-ops-033"></a>
## BR-OPS-033 — 과거 소속 오류에 따른 수업 분류·보상 정정

상태: APPROVED-TO-BE

2026-10-13 W1=1: Trainer 과거 Home 오류 정정으로 실제 Member/수행자/시작/Performed가 그대로인 기존 PT의 일반/지원 분류가 달라지면 현재 Master가 자기 Organization 범위에서 같은 PT 기록·기존 소비 Pass/차감을 유지하며 명시적으로 분류·보상을 정정한다. 최초 기록 생성 시각을 바꾸거나 취소 재등록·잔여 복원/재차감·Pass 재선택/Assigned Trainer 재작성을 하지 않는다. 현재 Trainer Home/수행 지점 Branch Admin 권한으로 이 분류 정정을 대신하지 않는다. 정정된 실제 당시 Trainer Home과 실제 Performed로 판단하고 현재 Home을 과거 사실로 대체하지 않는다.

지원→일반은 실제 수행 Trainer의 최초 PT 기록 생성 시점 Rate/Fixed Amount와 기존 소비 Pass의 발급 Price/Session Count/Payment Type을 적용한다. 최초 기록에서 일반 지급을 계산하지 않았어도 동일하며 당시 설정 미확인/부재를 현재 설정/임의 값·0원으로 대체하지 않는다. RATE 올림/FIXED_AMOUNT 재올림 없음·서비스 PT 실제 설정/명시적 0원 규칙을 유지한다. 이전 지원 보상은 이력 보존/유효 합계 제외하며 일반 지급과 이중 합산하지 않는다.

일반→지원은 이전 일반 지급을 이력 보존/유효 합계 제외하고 수업 보상 전체를 기존 관리자 Scope의 수동 추가실적으로 처리한다. 일반 지급 자동 복사/자동 0원 입력은 하지 않는다. 입력은 기존 Master Organization/각 행위 시점 Trainer 현재 Home Branch Admin 범위이며 분류 정정의 Master 전용 권한과 구별한다. 수행 지점만으로 타 Home Trainer 금액/설정 권한을 얻지 않는다. 지원 금액 미입력은 명시적 사유 있는 0원과 다르며 해당 Trainer·월 확정을 막는다.

원래 소속/수업·이전 보상 결과와 정정 사유/전후/Actor/시점·감사를 보존한다. 소속 오류 정정만으로 기존 PT/지급/정산을 자동 갱신하지 않으며 필요한 각 확정 Trainer·월은 기존 현재 권한/사유·해제/정정/같은 월 재확정·이전본 보존을 따른다. Member/실제 수행자/시작 오류의 취소 재등록·새 생성 시점 설정 및 Master 전용 Performed 값 정정은 별개로 유지한다. 영향 식별/완료 증거·역사 설정/전환·최소 계약/저장/UoW/경합은 후속이다.

추적: PR-005/009/010/027/030/031, BR-OPS-032/018/023, BR-PAY-011/015/024, NFR-001/002/004/012, BR-007/009, MB-001/005/006/010, [W 승인](product-decisions.md#review-20261013-w-batch). V-124 미구성·미실행, 구체 모듈/계약/UoW/잠금 PROPOSED.

<a id="br-pay-024"></a>
## BR-PAY-024 — 과거 소속 오류 영향 정정과 월 정산 확정 조건

상태: APPROVED-TO-BE

2026-10-13 W2=1: 과거 Home 오류로 영향을 받은 분류/보상·비용 정정이 모두 완료되어야 해당 Trainer·월 정산을 최초 확정·재확정할 수 있다. 미완료 상태의 경고 확인/임의 완료 표시·현재 값 또는 0원 대입으로 확정하지 않는다. 관련 없는 Trainer·월과 전체 개발을 차단하지 않는다.

소속 이력 정정만으로 기존 확정본을 자동 해제/재계산하지 않는다. 기존 행위별 현재 권한·사유/감사를 적용해 필요한 각 확정 Trainer·월을 해제 → 명시적 정정 → 같은 월 재확정하고 이전 확정본을 보존한다. 종료된 월만 확정/미입력 지원 보상 차단/현재 Trainer Home 기준 확정 권한과 기존 구성 유효성 조건은 유지한다. 영향 건 식별/완료 증거·비용 보고 버전/최소 계약·동시 정정/확정 원자성·경합은 상세 설계 대상이며 새 상태 enum/완료 기본값·일괄 정정 기능 승인이 아니다.

추적: PR-010/027/030, BR-PAY-015/016/020, BR-OPS-032/033, NFR-001/002/004/012, BR-009, MB-005/006/010, [W 승인](product-decisions.md#review-20261013-w-batch). V-125 미구성·미실행, 구체 모듈/계약/UoW/잠금 PROPOSED.

Y2 후속: 영향 정정 미완료는 해당 Trainer·월 확정/재확정 차단 외에 BR-PAY-025 지점 비용 보고서의 합계 제외/미완료 현황 표시에도 적용한다. 기존 확정본을 자동 해제/수정하는 것은 아니며 정정/재확정 완료 후 현재 유효 최신 확정본으로 한 번 반영한다. 이전 확정본 대체 합산·0원 대입/전체 월 완료 오표시는 하지 않는다. [Y 승인](product-decisions.md#review-20261013-y-batch); V-128 미구성·미실행.

<a id="br-pay-025"></a>
## BR-PAY-025 — 지점 비용 보고서의 대상 월·확정 비용과 미완료 현황

상태: APPROVED-TO-BE

2026-10-13 Y1/Y2=1: Master 전용 v1 지점 비용 보고서는 공통 Asia/Seoul 기준 종료된 월만 조회한다. 다음 달 1일 00:00부터 직전 월을 조회할 수 있으며 당월/미래 월 잠정 보고는 포함하지 않는다. 기존 관리자 범위의 당월 Trainer 월 정산 미확정 조회·검토는 유지한다. Backend의 현재 Master/자기 Organization 검증을 적용하며 Branch Admin은 자기 지점 비용 합계도 이 보고서로 읽지 못하고 Operator/Trainer 단독도 불가하다.

각 Trainer·대상 월의 미완료 영향이 없는 현재 유효한 최신 확정본만 비용 합계에 한 번 반영한다. 미확정/확정 해제 중/과거 Home 오류 영향의 분류·보상/비용 정정 대기 Trainer·월은 합계에서 제외하고 대상/미완료 사유를 별도 표시한다. 이전/해제된 확정본을 끌어오거나 최신/이전 버전을 중복 합산하지 않는다. 미완료가 남으면 전체 월 비용 완성으로 안내하지 않고 누락/미입력을 0원으로 대입하지 않는다. 정상적으로 확정된 명시적 0원과 미입력은 구별한다. 대상 집합/상세 미완료 응답·완료 증거/역사 사실/동시 조회 계약은 후속이며 단순히 기존 정산 행만 대상을 삼아 누락을 숨기지 않는다.

기존 일반/지원 비용의 실제 Performed·기본급 월말 Home 한 곳 전액·비지원 추가실적 발생 당시 Home 귀속과 한 번 합산을 유지한다. 현재 보상 설정/현재 Home·지점 활성 여부로 과거 확정 비용을 재계산/배분하지 않는다. 소속 오류 정정만으로 기존 확정본을 자동 해제/변경하지 않더라도 정정 대기 영향 Trainer·월은 보고서 완료 비용에 합산하지 않는다. 필요한 각 월의 기존 권한/사유·해제/명시적 정정/같은 월 재확정이 끝나면 현재 유효 최신 확정본으로 반영한다. 보고서 필터가 원본 PT/Pass 차감·지급/AP/확정본 취소·수정 명령은 아니다.

보고서의 지점/네 비용 항목·Trainer별 기여 금액 상세 수준은 아래 Z1으로 해결됐다. 최소 Trainer 식별/응답·월 대상 집합/역사 사실·비용 구성과 버전·소유권/UoW/잠금·동시 조회는 후속이다. 연간 통계/미래 예측·실제 지급/청구/송금 기능이나 다른 Actor의 보고서 권한을 추가하지 않는다.

추적: PR-010/011/027/030, BR-PAY-014/015/016/020/024, NFR-001/002/004/012, BR-009, MB-006/010, [Y 승인](product-decisions.md#review-20261013-y-batch). V-127/128 미구성·미실행, 구체 모듈/API/계약/UoW/잠금 PROPOSED.

2026-10-13 Z1=1 추가: 보고서 상세 수준은 지점별 합계·기본급/일반 PT 수당/지원 수업 보상/기타 추가실적별 소계 및 그 지점 비용에 기여한 Trainer별 해당 항목/금액이다. 현재 Master 자기 Organization 전용이며 비Master의 직접 지점/Trainer ID·집계 경로도 거부한다. Trainer 월 전체 지급액을 지점마다 반복하지 않고 기존 일반/지원 실제 Performed·기본급 월말 Home 한 곳 전액·기타 실적 발생 당시 Home 귀속으로 기여액을 구성한다. Trainer별 항목 합계↔지점 항목 소계/총계↔포함된 모든 지점 비용/유효 Trainer월 확정 구성 합계를 대조하며 기본급·지원 보상/이전·최신 버전을 중복하지 않는다.

Z1 집계/경계: Y1/Y2의 종료 월/미완료 영향 없는 최신 유효 확정본과 미확정·해제 중·소속 오류 정정 대기 제외/미완료 표시를 합계와 Trainer별 상세에 동일하게 적용한다. 원본/확정본·감사는 자동 변경하지 않으며 기존 당월 Trainer 정산 조회/인가와 K3/X1은 유지한다. 최소 Trainer 식별/응답·월 대상 집합/미완료·역사 비용/버전·조회 일관성/공개 계약/UoW/잠금은 후속 PROPOSED다. 새 개인정보/내보내기/연간 통계·별도 보고 확정/실제 지급 기능을 추가하지 않는다. [Z 승인](product-decisions.md#review-20261013-z-batch); PR-010/027/030, V-129 미구성·미실행.


<a id="br-pay-026"></a>
## BR-PAY-026 — 월 정산 대상 자동 선정과 비활성 무지급 월의 확정 의무

상태: APPROVED-TO-BE

2026-10-13 AB1/AB2=1: 대상 월 적용 일반 기본급 설정/월별 지정·유효 PT/금액 미입력 지원 PT·유효 추가실적 등 정산 구성 사실이 있는 Trainer를 자동 대상으로 선정한다. 명시0 설정도 존재로 취급하고 기존 월 정산/정정 이력·미완료 영향을 대조한다. 현재 활성 Trainer 목록이나 이미 생성된 정산 행만으로 대상을 제한해 누락을 숨기지 않는다. 조회/확정은 기존 현재 Master Organization/Trainer 현재 Home Branch Admin 범위를 적용한다.

그 월 전체 Trainer 비활성·명시적으로 확인된 적용 기본급0·유효/보상대기 PT 및 추가실적 없음·정정 대기 없음이면 새 정산 확정 의무에서 제외한다. 월중 활성/지급 구성/설정·역사 사실 미확인/미완료 영향이 있으면 이 예외로 제외하지 않는다. 현재 Trainer 비활성·계정 차단/역할 회수/Branch 비활성만으로 기본급을 자동0으로 바꾸지 않는다. 기존 정산/확정·정정 이력과 미완료 작업을 삭제/자동 해제·완료하지 않고 이전본 공개/비용 보고의 기존 포함·미완료 표시를 유지한다. 자동 선정은 자동 확정/cron·임의 월기본급0 생성이 아니다.

대상 구성/상태 역사 사실·AB2 조건 증거·월별 생성/최소 조회·미완료/확정본 버전·소속/보상/상태 변경과 선정/확정·비용 보고의 일관성은 후속 계약/검증 대상이다. 현재 Home 관리자 공개/수업별 금액 기밀성·종료 월 확정/지원 금액/영향 정정 미완료 차단·감사/이전본 보존은 유지한다.

추적: PR-010/027/030, BR-PAY-014/016/024/025, NFR-001/002/004/012, BR-009, MB-006/010, [AB 승인](product-decisions.md#review-20261013-ab-batch); V-132/133 미구성·미실행. 구체 모듈/API/계약/UoW/잠금 PROPOSED.
