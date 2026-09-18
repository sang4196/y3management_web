# 기능 요구사항 — 승인된 제품 기준

기존 PR-001–030 ID를 유지하고 최신 지점 관계·보상 설정·월 정산 결정을 반영했다. 추가실적(PR-031)을 v1에 추가했다. 이전 후보 문장은 대체되었다. 아래는 제품 의미·기대 결과이며 DB schema·API·Architecture 설계가 아니다.

출처: AS-IS-DERIVED는 발견한 업무 능력, APPROVED-TO-BE는 이번 사용자 결정으로 승인된 개선이다. KEEP/REDESIGN은 업무 취급 방식이며 구현 완료 상태가 아니다. TBD는 후속 기능의 세부 요구 미정일 뿐 OUT-V1 여부를 다시 묻는 상태가 아니다. DROP-CANDIDATE는 후보 유지 승인이고 영구 폐기 확정이 아니다. Scope의 IN-V1/OUT-V1/NOT-COMMITTED를 별도로 읽는다.

[승인 결정](product-decisions.md) · [후속 질문](open-questions.md) · [Scope](scope.md) · [AS-IS 대응](as-is-to-be-mapping.md)

<a id="pr-001"></a>
## PR-001. 운영 계정과 직무별 접근

처리 상태: REDESIGN

v1 범위: IN-V1

출처: AS-IS-DERIVED + APPROVED-TO-BE

제품 요구: Master Admin·Branch Admin·Operator·Trainer가 발급된 계정으로 Role과 Data Scope에 허용된 업무에 접근한다. Member 직접 로그인은 Future Scope다.

수용 기준 / 범위 경계: Master Admin은 Organization 전체, Branch Admin은 자신의 단일 Branch, Operator는 허용 Branch·업무, Trainer는 Allowed PT Scope다. Backend에서 Scope를 강제하고 다른 지점 ID를 직접 요청해도 무단 접근은 불가하다. 보상 설정은 PR-007의 대상 Trainer Home Branch 기준을 따른다. 기술 모델은 ARCH-001이다.

승인 근거: PD-001/002/003/004/019. [Product Decisions](product-decisions.md)

후속 TODO: ARCH-001/002, MB-001/004/005/006. [Open Questions](open-questions.md)

AS-IS reference: F01. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-002"></a>
## PR-002. 회원 기본정보 관리

처리 상태: KEEP

v1 범위: IN-V1

출처: AS-IS-DERIVED

제품 요구: 허용된 업무 범위에서 최소 Member 정보를 등록·조회·검색·변경한다. Member는 단일 Home Branch를 가지며 허용된 타 지점 PT를 이용할 수 있다. 타 지점 회원 전체 목록 접근과 특정 Member 업무 이용을 구분한다.

수용 기준 / 범위 경계: 회원 식별과 필요한 연락정보 검색을 지원한다. 생일·메모 등 필드 존재만으로 필수 수집하지 않는다. 최소 항목은 LEGAL-001에서 확정한다.

승인 근거: PD-006/022. [Product Decisions](product-decisions.md)

후속 TODO: LEGAL-001, MB-002/005; 이동·구체 교차 이용/조회 조건은 OPEN.

AS-IS reference: F02, F03, F05. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-003"></a>
## PR-003. PT Pass 생성·이력·잔여 관리

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: 회원 PT 이용을 명시적 Pass로 관리한다. Pass별 Issued Branch 하나와 상품·담당·구매/잔여 횟수·상태·생성/시작 정보·Session 이력을 구분한다. 허용 범위에서 타 지점 사용이 가능하며 발급 지점이 유일한 사용 지점은 아니다. 여러 시기의 Pass와 종료 이력을 보존한다.

수용 기준 / 범위 경계: 사용 가능한 Pass 안에서 FIXED_AMOUNT 우선, 동일 Payment Type FIFO다. 잔여 0인 Pass를 정상 차감 대상으로 선택하지 않는다. 관리자 수동 조정은 사유·이력을 남기고 Session 정정/취소에 따른 횟수 복원과 이력을 유지한다. 상태·사용 조건·조정 상세는 BR-001/002/007, ARCH-003, 교차 사용 조건은 MB-003/005다.

승인 근거: PD-007/008/010/011/022. [Product Decisions](product-decisions.md)

후속 TODO: BR-001/002, ARCH-003, MB-002/003. [Open Questions](open-questions.md)

AS-IS reference: F04. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-004"></a>
## PR-004. 업무 데이터 비활성화와 과거 조회

처리 상태: REDESIGN

v1 범위: IN-V1

출처: AS-IS-DERIVED + APPROVED-TO-BE

제품 요구: 회원·트레이너·PT Pass는 비활성화/상태 변경과 이력 보존을 우선한다.

수용 기준 / 범위 경계: 비활성 회원·트레이너·종료 Pass의 과거 Session 및 정산 이력을 권한 내에서 조회할 수 있다. Hard Delete는 기본 운영 기능이 아니다.

승인 근거: PD-010/011/022. [Product Decisions](product-decisions.md)

후속 TODO: BR-001/007, LEGAL-001. [Open Questions](open-questions.md)

AS-IS reference: F06, F10. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-005"></a>
## PR-005. 트레이너 기본정보 관리

처리 상태: KEEP

v1 범위: IN-V1

출처: AS-IS-DERIVED

제품 요구: Trainer는 한 시점에 단일 Home Branch에 소속되며 Branch에는 여러 Trainer가 있을 수 있다. 직접 로그인하여 허용된 타 지점 수업도 수행한다. 타 지점 수업으로 소속 변경이나 추가 소속을 만들지 않는다. Pass 담당 Trainer와 실제 Session 수행/지급 대상을 구분한다.

수용 기준 / 범위 경계: 일반 업무정보 관리와 보상 설정을 구분한다. Trainer별 월 고정 기본급은 PR-007/010에서 지원하며 조회·변경은 보상 설정 권한을 따른다. 동시 복수 소속 N:M은 v1 요구가 아니다. 이동 시점·과거 기록 정책은 MB-001/010 OPEN이다.

승인 근거: PD-002/006/012/022. [Product Decisions](product-decisions.md)

후속 TODO: MB-001, BR-009, LEGAL-001. [Open Questions](open-questions.md)

AS-IS reference: F07, F08, F09. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-006"></a>
## PR-006. PT Product·기준정보 관리

처리 상태: REDESIGN

v1 범위: IN-V1

출처: AS-IS-DERIVED + APPROVED-TO-BE

제품 요구: Product는 Organization 공통 상품이며 모든 Branch가 공통 Product Catalog를 사용한다. 기존 Master Admin의 생성/수정 권한을 유지한다. Product 총 횟수·판매가격·Payment Type(RATE/FIXED_AMOUNT)과 업무 사용 상태를 관리하며 서비스 Product는 FIXED_AMOUNT다. 지점별 가격 정책은 추가하지 않는다.

수용 기준 / 범위 경계: Product는 지급 방식만 정하며 Trainer Rate/Fixed Amount를 갖지 않는다. RATE 회당 단가는 Product Price ÷ Product Session Count다. 기존 공제율·FinalPrice는 필수 모델이 아니다. 기존 Pass에 대한 Product 변경 적용 상세는 BR-011이다.

승인 근거: PD-001/006/007/009/011. [Product Decisions](product-decisions.md)

후속 TODO: BR-001/011, MB-007; Branch Admin 공통 상품 관리 권한만 OPEN. 공통 Catalog 여부는 확정.

AS-IS reference: F11, F12, F13. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-007"></a>
## PR-007. Trainer Compensation Setting 관리

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: Trainer Compensation Setting은 Trainer별 Rate, Fixed Amount, 월 고정 Base Salary를 묶는 제품·권한 개념이다. Product는 RATE/FIXED_AMOUNT 계산 방식을 정하고 Product별 Trainer 지급 값은 두지 않는다. 같은 저장 구조를 요구하는 개념이 아니다. Rate / Fixed Amount / Base Salary 세 항목의 조회·설정·변경은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 단일 Branch를 Home Branch로 가진 Trainer에게만 허용한다. Operator와 Trainer는 본인 설정을 포함하여 모두 불가하다. 타 지점 지원 수업은 보상 설정 접근 권한을 부여하지 않는다. Backend에서 대상 Trainer의 Home Branch를 검증하며 직접 ID 요청과 감사·정산 등 우회 경로에도 제한을 적용한다.

수용 기준 / 범위 경계: 모든 보상 설정 변경(최초 설정 포함)에 대상 Trainer, 변경 항목, 변경 전 값, 변경 후 값, 변경 Actor, Actor의 권한 및 Branch Context, 변경 시점을 추적한다. 별도 Master Admin 승인 없이 변경 가능하며 변경 요청→승인 대기→승인→반영 절차를 추가하지 않는다. 이 결정은 추가실적 승인이나 월 정산 마감/확정 절차를 면제하지 않는다. Rate/Fixed Amount는 관리자 저장 완료 이후 새로 등록되는 Session부터 적용하며 정상 등록 시 계산·확정한다. 실제 수업일로 적용 기준을 바꾸지 않는다. Base Salary 적용 월은 BR-012 OPEN이다. 현재 설정 변경으로 과거 확정 Session Payment 및 월 정산의 적용 기본급·합계를 자동 변경하지 않는다.

승인 근거: PD-001/009/012/022. [Product Decisions](product-decisions.md)

후속 TODO: BR-010/012, ARCH-001; 입력 검증·기본급 적용 월·보존/권한 구현. 세 항목 동일 권한과 별도 승인 없음은 확정.

AS-IS reference: F14, F15, F16. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-008"></a>
## PR-008. 실제 진행일별 개별 PT Session

FOUNDATION-001 의미 명확화: Session 등록은 **기존 회원에게 실제로 PT 수업을 진행했다는 사실을 기록**하는 업무다. 사용자 문구는 “PT 진행 등록”, “수업 완료 기록”, “PT 진행 내역”을 우선한다. 상품 등록·Pass 발급·미래 예약·시간표 생성이 아니며 사전 Reservation이나 PLANNED/BOOKED 상태를 v1 진행 기록의 조건으로 도입하지 않는다. 실제 수업 진행일과 시스템 기록 시점은 별개다. 지급 설정 적용은 BR-PAY-011/012, 날짜 입력 허용 범위는 BR-008 OPEN을 그대로 따른다. 서버 내부의 인가된 지급 계산은 Trainer에게 Rate/Fixed Amount/Base Salary를 공개하는 행위가 아니다.

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: Trainer가 허용된 PT 업무 범위에서 자신이 실제 진행한 날짜별 Session 1회를 직접 등록하고 자신의 Session을 조회한다. 허용된 운영자의 등록도 유지한다. 사용할 Pass 결정(FIXED_AMOUNT 우선, 동일 Payment Type FIFO) → Pass 횟수 차감 → Product Payment Type 확인 → 해당 시점 수행 Trainer Rate/Fixed Amount 적용 → Session Payment 계산·확정 흐름을 따른다. RATE 결과는 1,000원 단위 올림, FIXED_AMOUNT는 그대로 지급한다.

수용 기준 / 범위 경계: 실제 진행일·소비 Pass·수행 Trainer·Session Performed Branch를 식별한다. Trainer Home Branch, Member Home Branch, Pass Issued Branch와 구별하고 소속/발급 지점 변경으로 과거 수행 지점을 바꾸지 않는다. 9월 2일/5일/9일은 날짜별 3개 원본이다. 정상 차감·확정의 일관성, Branch별 조회, Smartphone 등록을 지원하며 Trainer에게 설정을 노출하지 않는다. 위 일반 지급 흐름으로 타 지점 보상 구성을 확정하지 않는다(MB-009 결정 게이트). 기록·Pass 차감은 유지하며 기본 수당 0원 또는 이중 지급을 임의 결정하지 않는다. 저장·관계·동시성·트랜잭션은 Architecture 결정이다.

승인 근거: PD-007/008/009/010/012/022. [Product Decisions](product-decisions.md)

후속 TODO: BR-002/008/010/011, MB-001/002/003/005/009/010, UX-001.

AS-IS reference: F17, F18, F19. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-009"></a>
## PR-009. 제한된 권한의 Session 정정·취소

여기서 정정/취소는 이미 기록한 PT 진행 사실에 대한 처리이며 Future Scope의 미래 예약 취소와 구별한다.

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: 허용된 Branch와 제한된 정정 권한 안에서 운영자가 Session을 정정/취소하며 Pass 잔여·월 정산의 일관성과 이력을 유지한다. Trainer 본인 정정/취소 허용 여부는 MB-005 OPEN이며 직접 등록 권한으로 자동 허용하지 않는다.

수용 기준 / 범위 경계: 단순 행 삭제로 처리하지 않는다. 권한·변경 행위가 감사 가능하며 원래 기록과 관련 과거 이력을 추적할 수 있어야 한다. 정정 허용 항목·잔여 복원·기간별 반영의 상세는 미정이다.

승인 근거: PD-010/011/012/022. [Product Decisions](product-decisions.md)

후속 TODO: BR-007, ARCH-001, MB-005. [Open Questions](open-questions.md)

AS-IS reference: F20, F21. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-010"></a>
## PR-010. 기본급·Session·추가실적 월별 트레이너 정산

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: Monthly Settlement = 해당 월 적용 Base Salary + 유효한 Session Payment 합계 + 유효한 Additional Performance 합계다. Trainer·대상 월·적용 기본급·Session 수·Session Payment 합계·추가실적 내역/합계·월 정산 합계를 구분한다. 2,500,000원 + 1,200,000원 + 150,000원 = 3,850,000원이며 여러 지점 수업으로 동일 월 기본급을 중복 가산하지 않는다. 타 지점 Session Payment 포함 여부는 MB-009 결정 전 확정하지 않는다.

수용 기준 / 범위 경계: 현재 Base Salary 변경으로 과거 확정 정산의 적용 기본급과 합계가 자동 변경되지 않는다. 현재 Rate/Fixed Amount로 과거 확정 Session Payment를 재계산하지 않으며 월 합계에 RATE 올림을 다시 적용하지 않는다. 권한 있는 과거 정정과 현재 설정 변경의 자동 소급은 별개다. Master Admin은 전체 정산 관리, Branch Admin 결과 공개 범위는 MB-006이며 설정 접근 권한으로 전체 정산 열람을 자동 허용하지 않는다. 기본급 일할·근무일수·휴직 자동 계산과 수동 매출 합산은 제공하지 않는다.

승인 근거: PD-009/010/011/012/013. [Product Decisions](product-decisions.md)

후속 TODO: BR-007/008/009/010/011/012/013, MB-006/009/010; 지급 구성·기본급 적용 월·미확정 정산 반영·귀속·공개·마감/정정 정책.

AS-IS reference: F26. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-011"></a>
## PR-011. 추가 연간 통계 검토

처리 상태: TBD

v1 범위: NOT-COMMITTED

출처: AS-IS-DERIVED

제품 요구: Branch별 및 Organization 전체 통계/집계 확장 가능성을 고려하되 필수 월 정산 외 추가 연간 통계는 필요 확인 후 별도 정의한다.

수용 기준 / 범위 경계: 통계/집계에도 Branch Data Scope와 지급정보 기밀성을 적용한다. 12개월 고정 평균과 수입/매출 혼합 표를 자동 복제하지 않는다. 정산 업무 정보는 PR-010이며 Actor별 동일 노출을 요구하지 않는다.

승인 근거: PD-006/012/013. [Product Decisions](product-decisions.md)

후속 TODO: BR-009. [Open Questions](open-questions.md)

AS-IS reference: F27. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-012"></a>
## PR-012. 수동 트레이너 매출

처리 상태: TBD

v1 범위: OUT-V1

출처: AS-IS-DERIVED

제품 요구: v1에 제공하지 않는다. 기존 자료 조회·이관도 하지 않는다.

수용 기준 / 범위 경계: 후속 실제 필요가 확인되면 별도 요구사항으로 정의한다. AS-IS 기본 입력 경로 차단(K37)은 그대로 참조로 남긴다.

승인 근거: PD-006/013/017. [Product Decisions](product-decisions.md)

후속 TODO: 현재 구현 TODO 없음. [Open Questions](open-questions.md)

AS-IS reference: F22, F23, F24, F25. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-013"></a>
## PR-013. 락커 운영

처리 상태: TBD

v1 범위: OUT-V1

출처: AS-IS-DERIVED

제품 요구: 배정·기간·소유자 검색·마감·현황은 모두 v1 제외다.

수용 기준 / 범위 경계: 향후 별도 기능 후보이며 PT 수용 기준에 락커를 끼워 넣지 않는다.

승인 근거: PD-006/016. [Product Decisions](product-decisions.md)

후속 TODO: 현재 구현 TODO 없음. [Open Questions](open-questions.md)

AS-IS reference: F28, F29, F30, F31, F32, F33. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-014"></a>
## PR-014. 락커 글꼴 조절

처리 상태: DROP-CANDIDATE

v1 범위: OUT-V1

출처: AS-IS-DERIVED

제품 요구: 기존 글꼴별 ± 기능은 후보로만 보존한다. 락커 자체가 v1 제외다.

수용 기준 / 범위 경계: 존재 자체를 구현 근거로 쓰지 않는다. Responsive Web은 별도 NFR-008 요구다.

승인 근거: PD-005/016/023. [Product Decisions](product-decisions.md)

후속 TODO: 실제 필요 확인 시 후속 검토. [Open Questions](open-questions.md)

AS-IS reference: F34. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-015"></a>
## PR-015. Responsive Web에서 핵심 업무 이동

처리 상태: REDESIGN

v1 범위: IN-V1

출처: AS-IS-DERIVED + APPROVED-TO-BE

제품 요구: Desktop/Tablet/Smartphone에서 허용된 Member·Pass·Session·Settlement 등 사용자별 핵심 업무를 수행하는 Responsive Web을 제공한다.

수용 기준 / 범위 경계: 터치 조작과 작은 화면의 주요 정보/Action을 지원하며 Desktop 단순 축소는 불충족이다. Trainer의 Smartphone 로그인·허용 Member/PT 조회·실제 Branch/날짜 확인·Session 등록·본인 Session 조회가 실질적으로 가능해야 한다. 현재 Branch·대상 Member·Pass·진행일·정산 기간을 혼동하지 않아야 한다. breakpoint와 Frontend 기술은 후속이다.

승인 근거: PD-001/005/006/007/008. [Product Decisions](product-decisions.md)

후속 TODO: ARCH-004, UX-001. [Open Questions](open-questions.md)

AS-IS reference: F35. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-016"></a>
## PR-016. 데스크톱 창 조작·종료

처리 상태: DROP-CANDIDATE

v1 범위: NOT-COMMITTED

출처: AS-IS-DERIVED

제품 요구: 창 드래그·최소화·프로세스 종료는 존재만으로 구현하지 않는다.

수용 기준 / 범위 경계: 안전한 웹 접근 종료는 PR-026으로 별도 취급한다. 후보의 영구 폐기를 확정하지 않는다.

승인 근거: PD-019/023. [Product Decisions](product-decisions.md)

후속 TODO: 실제 필요 확인 시 후속 검토. [Open Questions](open-questions.md)

AS-IS reference: F36. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-017"></a>
## PR-017. 가계부 거래·자산·분류

처리 상태: TBD

v1 범위: OUT-V1

출처: AS-IS-DERIVED

제품 요구: v1 제외. PT 관리와 별도 bounded context 후보로 취급한다.

수용 기준 / 범위 경계: 현재 별도 구조·연동·장부 규칙을 설계하지 않는다. 기존 거래·잔액 승계 없음.

승인 근거: PD-006/014/017. [Product Decisions](product-decisions.md)

후속 TODO: 후속 Product Expansion. [Open Questions](open-questions.md)

AS-IS reference: F37, F38, F39, F40, F41, F42, F43, F44, F45, F46, F47, F48. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-018"></a>
## PR-018. 고정 거래

처리 상태: TBD

v1 범위: OUT-V1

출처: AS-IS-DERIVED

제품 요구: 가계부 제외에 따라 v1 제외 및 실행 정책 보류다.

수용 기준 / 범위 경계: 로그인 시 고정 거래 생성은 웹 로그인 요구가 아니다.

승인 근거: PD-006/014/015. [Product Decisions](product-decisions.md)

후속 TODO: 후속 가계부 채택 전까지 보류. [Open Questions](open-questions.md)

AS-IS reference: F49, F50, F51, F53. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-019"></a>
## PR-019. 가계부 자산·부채·순자산 통계

처리 상태: TBD

v1 범위: OUT-V1

출처: AS-IS-DERIVED

제품 요구: 가계부와 함께 v1 제외다.

수용 기준 / 범위 경계: Session 지급 정산에 금융 잔액을 포함하지 않는다.

승인 근거: PD-014. [Product Decisions](product-decisions.md)

후속 TODO: 후속 Product Expansion. [Open Questions](open-questions.md)

AS-IS reference: F52. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-020"></a>
## PR-020. Organization / Branch 관리

처리 상태: REDESIGN

v1 범위: IN-V1

출처: AS-IS-DERIVED + APPROVED-TO-BE

제품 요구: 하나의 Organization 아래 여러 Branch를 운영한다. Master Admin은 모든 Branch 조회·등록·정보 관리 및 Branch 구조를 관리한다. 활성/비활성 관리 가능성도 고려한다. Branch는 실제 운영 지점이며 Multi-Branch는 Multi-Tenant SaaS 확정이 아니다.

수용 기준 / 범위 경계: Trainer는 한 시점에 Home Branch 하나에 소속되고 Branch에는 여러 Trainer가 있을 수 있다. Branch당 Trainer 한 명인 1:1이나 Trainer 동시 복수 소속 N:M을 요구하지 않는다. Member도 Home Branch 하나를 가지며 Pass는 Issued Branch 하나를 가진다. Trainer·Member·Pass는 허용된 조건에서 타 지점 PT 업무를 수행·이용할 수 있다. Session은 실제 Performed Branch를 식별하고 소속·발급 지점 변경으로 과거 수행 지점이 바뀌지 않아야 한다. Product는 Organization 공통 Catalog이며 지점별 가격 정책은 추가하지 않는다. Branch Admin은 하나의 Branch를 관리하고 일부 여러 지점만 담당하는 중간 관리자 역할은 추가하지 않는다. Master Admin이 Branch 구조를 관리하고 Branch Admin의 자기 지점 기본정보 수정 항목·비활성화 상세는 MB-004/008 OPEN이다.

승인 근거: PD-004/006. [Product Decisions](product-decisions.md)

후속 TODO: MB-001–008, ARCH-001; 구체 데이터 모델은 Architecture 단계. [Open Questions](open-questions.md)

AS-IS reference: F54, F56. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-021"></a>
## PR-021. 관리자 발급 운영 계정·권한 관리

처리 상태: REDESIGN

v1 범위: IN-V1

출처: AS-IS-DERIVED + APPROVED-TO-BE

제품 요구: Master Admin이 Branch Admin 및 계정/권한을 관리한다. 관리자 발급 방식을 유지하며 Trainer 로그인 계정과 사용자·Branch 관계도 다룬다. Branch Admin의 계정 발급 위임 범위는 미정이다.

수용 기준 / 범위 경계: 기존 계정·암호를 이관하지 않는다. Role/Data Scope를 분리하고 계정/권한 변경을 감사한다. 계정 발급 권한과 PR-007 보상 설정 권한은 별개다. 계정 수명과 기술 모델은 ARCH-001/002다.

승인 근거: PD-001/019/022. [Product Decisions](product-decisions.md)

후속 TODO: ARCH-001/002, MB-004. [Open Questions](open-questions.md)

AS-IS reference: F57, F58, F59. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-022"></a>
## PR-022. 숨김 월 복사·상품 직접 선택

처리 상태: DROP-CANDIDATE

v1 범위: NOT-COMMITTED

출처: AS-IS-DERIVED

제품 요구: 숨김 기능은 필요 확인 전 구현하지 않는다.

수용 기준 / 범위 경계: 월 집계 원본 복사는 날짜별 Session 원칙과 호환 요구가 아니다. 여러 날짜 일괄 입력 UX-001과 혼동하지 않는다.

승인 근거: PD-008/023. [Product Decisions](product-decisions.md)

후속 TODO: UX-001과 별개; 후속 필요 확인. [Open Questions](open-questions.md)

AS-IS reference: H01, H02. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-023"></a>
## PR-023. 기존 Excel 가져오기·migration tooling

처리 상태: DROP-CANDIDATE

v1 범위: OUT-V1

출처: AS-IS-DERIVED

제품 요구: 기존 데이터 이관 및 migration용 import는 v1에서 제거한다. 미연결 도구는 후보로만 남긴다.

수용 기준 / 범위 경계: 운영 데이터를 복사·변환·적재하거나 기존 자료 조회를 제공하지 않는다. CSV/Excel 운영 편의는 실제 필요 확인 전 필수 아님.

승인 근거: PD-017/020/023. [Product Decisions](product-decisions.md)

후속 TODO: 현재 이관 TODO 없음. [Open Questions](open-questions.md)

AS-IS reference: H03. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-024"></a>
## PR-024. 미연결 생일 목록

처리 상태: DROP-CANDIDATE

v1 범위: NOT-COMMITTED

출처: AS-IS-DERIVED

제품 요구: 미연결 생일 목록은 후보 유지다.

수용 기준 / 범위 경계: 회원 생일 저장이나 발송 기능을 이 기능의 존재로 필수화하지 않는다.

승인 근거: PD-022/023. [Product Decisions](product-decisions.md)

후속 TODO: 후속 필요 확인. [Open Questions](open-questions.md)

AS-IS reference: H04. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-025"></a>
## PR-025. 빈 기타설정·급여 팝업

처리 상태: DROP-CANDIDATE

v1 범위: NOT-COMMITTED

출처: AS-IS-DERIVED

제품 요구: 내용 없는 화면을 자동 구현하지 않는다.

수용 기준 / 범위 경계: 빈 팝업 자체를 급여 지급·송금 기능으로 확대하지 않는다. 사용자 승인 보상 설정(PR-007)·월 정산(PR-010)·추가실적(PR-031)은 별도 요구다.

승인 근거: PD-023. [Product Decisions](product-decisions.md)

후속 TODO: 후속 필요 확인. [Open Questions](open-questions.md)

AS-IS reference: S05/S15. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-026"></a>
## PR-026. 접근 종료·재진입

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: 운영 계정의 접근 종료·재진입을 계정 정책의 일부로 다룬다.

수용 기준 / 범위 경계: 만료·재인증·비밀번호 분실·중단 후 접근 정책은 Authentication/Authorization에서 정의한다. 기존 프로그램 종료와 동일시하지 않는다.

승인 근거: PD-019. [Product Decisions](product-decisions.md)

후속 TODO: ARCH-002. [Open Questions](open-questions.md)

AS-IS reference: 직접 대응 기능 없음; 사용자 승인. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-027"></a>
## PR-027. 중요 운영 행위 감사

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: Session 생성·정정/취소, Pass 잔여 영향 행위, 세 보상 설정 변경, 추가실적 생성·정정·취소, 계정/권한 및 중요 Branch 관리 행위를 감사 가능하게 한다.

수용 기준 / 범위 경계: 모든 보상 설정 변경(최초 설정 포함)에 대상 Trainer, 변경 항목, 변경 전 값, 변경 후 값, 변경 Actor, Actor의 권한 및 Branch Context, 변경 시점을 추적한다. 별도 Master Admin 승인 없이 변경 가능하며 변경 요청→승인 대기→승인→반영 절차를 추가하지 않는다. 이 결정은 추가실적 승인이나 월 정산 마감/확정 절차를 면제하지 않는다. 감사 열람이나 다른 화면에서 비인가 사용자에게 설정을 노출하지 않는다. Trainer 직접 등록 Actor와 실제 수행 Branch도 식별한다. 감사 구조·조회 구현은 Architecture, 보존 기간은 LEGAL-001이다.

승인 근거: PD-022. [Product Decisions](product-decisions.md)

후속 TODO: ARCH-001, BR-007, LEGAL-001. [Open Questions](open-questions.md)

AS-IS reference: 직접 대응 기능 없음; 사용자 승인. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-028"></a>
## PR-028. 빈 운영 데이터에서 신규 설정·일괄 전환

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: 초기 Master Admin과 Organization/Branch의 필요한 기준정보를 새로 설정하고 운영/Trainer 계정·Member·Trainer·Product·Pass를 새로 준비한다. 수용 기준 충족 후 기존 프로그램에서 일괄 전환한다.

수용 기준 / 범위 경계: 기존 데이터·계정·암호·설정의 복제/이관은 요구하지 않는다. 장기 병행 입력 구조가 없어야 한다. 짧은 준비/검증 및 실제 시작 책임은 별도 cutover 계획이다.

승인 근거: PD-004/017/018/019/020. [Product Decisions](product-decisions.md)

후속 TODO: ARCH-002, OPS-001. [Open Questions](open-questions.md)

AS-IS reference: F55. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-029"></a>
## PR-029. Trainer Authentication / Allowed PT Scope

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: Trainer는 v1 직접 로그인 Actor다. 허용된 Member/PT 정보와 자신의 PT 업무를 조회하고 실제 수행 Session을 직접 등록·조회한다.

수용 기준 / 범위 경계: Smartphone 현장 흐름은 주요 Use Case다. PR-008의 기록·차감과 일반 지급 규칙을 따르되 타 지점 보상 구성은 MB-009 결정 전 보류한다. Trainer는 본인을 포함한 모든 Rate/Fixed Amount/Base Salary 조회·변경이 불가하다. 타 지점 수업 가능은 그 지점 전체 데이터 접근 권한이 아니며 본인 정정/취소도 OPEN이다.

승인 근거: PD-001/002/005/006; PR-001/008/015; NFR-001/008.

후속 TODO: MB-001/005, ARCH-001/002. [Open Questions](open-questions.md)

<a id="pr-030"></a>
## PR-030. Branch-scoped Authorization / 업무 Context

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: Role과 Data Scope를 분리한다. Master Admin은 Organization 전체, Branch Admin은 허용 Branch, Operator는 허용 Branch·업무, Trainer는 Allowed PT Scope에 접근한다. Member·Trainer·Pass·Session·운영 데이터·Settlement·통계/집계에 허용 범위를 적용한다.

수용 기준 / 범위 경계: Branch-scoped authorization MUST be enforced server-side. 허용되지 않은 다른 지점 데이터 ID를 직접 요청해도 접근할 수 없으며 UI 숨김만으로 충족하지 않는다. 특정 Member/Pass/Session의 허용된 교차 이용과 타 지점 전체 목록 조회를 구별한다. PR-007 보상 설정은 대상 Trainer Home Branch로 제한하며 Performed Branch로 권한을 확대하지 않는다. 교차 업무 조건 MB-001/002/003/005, 정산 열람 MB-006, 귀속 MB-010은 업무 결정 게이트다.

승인 근거: PD-001/004/006/012/022; NFR-001/004/005.

후속 TODO: MB-001–008, ARCH-001. [Open Questions](open-questions.md)

## PT Pass와 PT Session의 제품 개념

PT Pass는 Member가 특정 PT Product를 이용하는 명시적 단위다. Assigned Trainer, Purchased Sessions, Remaining Sessions, Status, Created/Started information, 해당 PT Session history를 업무적으로 구분한다. 이는 개념 설명이며 Table·컬럼 정의가 아니다.

회원은 시간에 따라 여러 Pass 이력을 가진다. 종료된 Pass를 새 Pass로 덮어쓰지 않으며 과거 Session과 정산은 계속 조회 가능해야 한다. 복수 사용 가능 Pass의 FIXED_AMOUNT 우선 차감은 BR-PAY-006이며 사용 가능 조건·상한은 ARCH-003, 상태 전이·잔여 세부는 BR-001/002다. Purchased Sessions라는 개념이 고객 결제·계약 관리 기능을 승인하는 것은 아니다.

PT Session은 실제 진행 날짜의 1회 기록이다. 예시의 9월 2일/5일/9일 진행은 각 날짜의 개별 기록이며 월 합계는 3회다. 여러 날짜를 한 번에 입력할지는 UX-001이고 원본의 단위는 바뀌지 않는다. 실제 수행 Trainer에 지급하며 서비스 Product는 FIXED_AMOUNT다. 정정·날짜 중복 판단의 상세만 후속 규칙으로 남긴다.

[확정 지급 규칙 BR-PAY-001–013](business-rules.md)을 따른다. Product는 Payment Type을, Trainer Compensation Setting은 Product에 독립적인 Rate·Fixed Amount·월 Base Salary를 갖는다. 기본급은 Session마다 붙지 않는다. RATE = Product Price ÷ Product Session Count × Trainer Rate의 결과를 1,000원 단위 올림; FIXED_AMOUNT = Trainer Fixed Amount. 서비스도 후자를 지급하며 Monthly Settlement의 Session 구성은 유효한 확정 Session Payment 집계이며 전체 구성은 PR-010을 따른다. 타 지점 보상 구성은 MB-009 OPEN이다.

## AS-IS 규칙의 계승 경계

R03/R06의 필수 개인정보·기본급, R04/R05의 회원 잔여 덮어쓰기, R09/R10의 계산식·우선순위, R14/R15의 일반 우선·서비스 단가, R18의 현재 상품 일치 복원 조건은 참고 규칙이다. 승인된 Pass/Session/지급 정책에 맞는 BR로 확인되기 전 TO-BE의 확정 규칙이 아니다. R02의 이력 보존 의도는 PD-011로 강화되었고, R35의 특정 계정 메뉴 조건은 PD-001의 직무 권한으로 대체된다.

계약·출석·고객 결제·환불·회원권·상담, 락커·가계부·수동 매출·고정 거래는 v1 제외를 유지한다. Member 로그인/Self-Service, Schedule/Reservation 및 Mobile App은 명시적 Future Scope다. Trainer 직접 로그인과 Multi-Branch는 v1에 포함한다. 기존 데이터 이관·이관 도구도 제공하지 않는다.

## Product Baseline — 2026-09-17 지점 관계·보상 개정

최신 사용자 확정사항을 반영한 Architecture Input Baseline이다. [현재 결정과 변경 이력](README.md), [권한](users-and-roles.md), [업무 규칙](business-rules.md), [남은 결정 게이트](open-questions.md), [Architecture 인계](architecture-handoff.md)를 함께 따른다. Baseline 갱신은 모든 상세 업무 정책 또는 구현 완료를 뜻하지 않는다.

<a id="pr-031"></a>
## PR-031. 추가실적(Additional Performance)

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: Trainer에게 인정하는 인센티브를 지원한다. 타 지점 지원 수업, 회원 유지, 기타 인정 추가실적이 예다. 특정 Session 관련 또는 Session 없이 발생할 수 있다. 고객 결제·매출·가계부나 기존 수동 매출과 동일시하지 않는다.

수용 기준 / 범위 경계: 대상 Trainer, 인정 사유 또는 유형, 금액, 발생 시점과 정산 대상 기간, 관련 Branch Context, 필요한 경우 Member/Session, 등록자와 등록 시점, 정정/취소 이력을 식별한다. 생성·정정·취소는 감사 가능한 금액 변경 업무다. 정확한 입력 항목·구현 구조는 후속 설계다. 보상 설정 권한을 등록/승인 권한으로 자동 확장하지 않고 OPEN을 권한 허용으로 취급하지 않는다.

승인 근거: PD-027; BR-PAY-015; PR-010/027.

후속 TODO: BR-013, MB-009/010. 추가실적 상세 권한·신청·승인·금액 산정·정정/취소·마감 이후 처리 및 타 지점 보상 구성/귀속은 결정 전 설계·구현 확정 보류.

AS-IS reference: 직접 대응 사실을 확정하지 않음. F22–25/PR-012는 수동 매출 제외를 유지한다.
