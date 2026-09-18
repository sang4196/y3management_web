# 사용자 및 역할

2026-09-17 Multi-Branch 변경 승인 반영. 아래는 Product 개념이며 RBAC/ABAC 기술 모델이나 Permission 목록이 아니다. AS-IS 계정·특수 메뉴 및 실제 권한 운영 미검증 사실은 [AS-IS 인증](../analysis/08-auth-and-permissions.md), [VAL-001](validation-needed.md#val-001)에 구분한다.

## Role과 Data Scope

Role은 어떤 행위를 수행할 수 있는가, Data Scope는 그 행위를 어느 데이터 범위에서 수행할 수 있는가다. Product 개념 예로 Master Admin과 Branch Admin 모두 Role ADMIN이며 Data Scope는 각각 ORGANIZATION과 BRANCH다. 실제 기술 표현은 Architecture에서 결정한다.

| Actor | v1 로그인 | Data Scope | Product Capability / 제한 |
| --- | --- | --- | --- |
| Master Admin | 예 | Organization 전체 | 모든 Branch 조회·생성·정보 관리, 전체 Branch Member/Trainer/PT Product/PT Pass/PT Session/Settlement 조회·관리, Trainer Compensation Setting 조회·변경, Branch Admin 및 계정/권한 관리. Organization 전체 통계 확장 가능 |
| Branch Admin | 예 | 자신의 단일 Branch | 해당 Branch Member/Trainer/PT Pass/PT Session/운영 데이터/Settlement 업무와 허용 통계 접근. 다른 Branch 전체 자료 접근은 불가하며 특정 교차 업무는 별도 허용 조건을 검증. Branch 구조 변경 및 다른 Branch 생성/수정 불가. 보상 설정은 대상 Trainer Home Branch가 자신의 Branch일 때 조회·변경 가능 |
| Operator | 예 | 허용된 Branch와 업무 범위 | 허용된 운영 업무. 구체 행위·Branch Scope 부여는 MB-004/ARCH-001. Compensation Setting 세 항목 조회·변경 불가 |
| Trainer | 예 | Allowed PT Scope | 허용된 Member/PT 정보와 자신의 PT 업무 조회, 자신이 실제 진행한 Session 등록, 자신의 Session 조회. Compensation Setting 세 항목 조회·변경 불가. 단일 Home Branch; Member 조회·교차 업무 조건·본인 정정/취소는 미정 |
| Member | 아니오 | v1 관리 대상 Domain; Future Self-Service Scope | 향후 자신의 Schedule/예약/Pass/잔여 조회, 예약·취소를 고려. 현재 Login Account와 동일 개념으로 취급하지 않음 |

Master Admin의 전체 업무 관리도 최소 개인정보·감사·이력 보존 규칙을 따른다. 관리 권한은 무제한 물리 삭제를 뜻하지 않는다. Branch Admin은 단일 Branch만 관리하며 중간 다지점 관리자 역할을 추가하지 않는다. Product는 Organization 공통이며 Master Admin 관리 권한을 유지한다. 자신의 Branch 기본정보 수정 항목과 Branch Admin 상품 관리 권한은 MB-004/007 OPEN이다.

## Backend 보안 경계

Trainer의 “Session 등록”은 기존 회원의 실제 수업 완료를 기록하는 PT 진행 등록이다. 사전 예약은 필수 조건이 아니며 진행 내역의 정정/취소는 미래 예약 취소와 별개다. 서버가 인가된 진행 업무 안에서 지급액을 계산하더라도 Trainer에게 Rate / Fixed Amount / Base Salary 조회 권한을 주지 않는다.

**Branch-scoped authorization MUST be enforced server-side.** Branch A Admin이 허용되지 않은 Branch B 업무 데이터의 ID를 알아도 조회·변경할 수 없어야 한다. 허용된 특정 Member/Pass/Session 교차 업무와 타 지점 전체 목록 접근은 별개이며 구체 조건은 MB-001/002/003/005다. 메뉴 숨김이나 Frontend 필터만으로 충족하지 않는다. Member·Trainer·Pass·Session·운영 데이터·Settlement·통계/집계에 허용 Data Scope를 적용하며 남은 귀속/교차 이용 조건은 MB-001–010에 남긴다. Cross-Branch unauthorized access는 금지한다.

## Trainer Compensation Setting 조회·변경

Trainer 기준 Rate(RATE 지급률), Fixed Amount(FIXED_AMOUNT 회당 지급액), Base Salary(월 고정 기본급)에 동일 정책을 적용한다. Product별 Trainer 지급 값이나 같은 테이블 저장을 요구하지 않는다.

| Actor / 대상 범위 | Rate 조회·변경 | Fixed Amount 조회·변경 | Base Salary 조회·변경 |
| --- | --- | --- | --- |
| Master Admin / Organization 전체 Trainer | 허용 | 허용 | 허용 |
| Branch Admin / 자기 Branch가 Home Branch인 Trainer | 허용 | 허용 | 허용 |
| Branch Admin / 다른 Home Branch의 Trainer | 불가 | 불가 | 불가 |
| Operator / 모든 Trainer | 불가 | 불가 | 불가 |
| Trainer / 본인 포함 모든 Trainer | 불가 | 불가 | 불가 |

Rate / Fixed Amount / Base Salary 세 항목의 조회·설정·변경은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 단일 Branch를 Home Branch로 가진 Trainer에게만 허용한다. Operator와 Trainer는 본인 설정을 포함하여 모두 불가하다. 타 지점 지원 수업은 보상 설정 접근 권한을 부여하지 않는다. Backend에서 대상 Trainer의 Home Branch를 검증하며 직접 ID 요청과 감사·정산 등 우회 경로에도 제한을 적용한다.

수원점 소속 Trainer A가 강남점에서 수업해도 수원점 Branch Admin만 A의 보상 설정에 접근 가능하다. 강남점 Branch Admin은 지원 수업 이력만으로 권한을 얻지 않는다.

모든 보상 설정 변경(최초 설정 포함)에 대상 Trainer, 변경 항목, 변경 전 값, 변경 후 값, 변경 Actor, Actor의 권한 및 Branch Context, 변경 시점을 추적한다. 별도 Master Admin 승인 없이 변경 가능하며 변경 요청→승인 대기→승인→반영 절차를 추가하지 않는다. 이 결정은 추가실적 승인이나 월 정산 마감/확정 절차를 면제하지 않는다.

Rate/Fixed Amount의 적용은 BR-PAY-011, 기본급 적용 월은 BR-012 OPEN이다. 추가실적 권한은 BR-013, 정산 공개는 MB-006 OPEN이며 설정 변경 권한으로 자동 허용하지 않는다. 감사 조회를 포함한 우회 노출도 금지한다. [BR-PAY-010](business-rules.md#br-pay-010).

## 계정 수명과 감사

Master Admin이 Branch Admin과 계정/권한을 관리한다. 관리자 발급 방식은 유지하며 Trainer 직접 로그인 계정을 포함한다. Branch Admin의 계정 발급 위임 범위는 미정이다. 초기 Master Admin, 비밀번호 설정/재설정, 계정 중단, 마지막 Master Admin 보호, 접근 종료/만료는 ARCH-002에서 상세화한다. 기존 계정·암호는 이관하지 않는다.

중요 관리 행위는 필요 시 Actor, Actor Role, Branch Context, 대상 데이터, 행위, 변경 전후 값, 수행 시점을 식별해야 한다. 비활성화 이후 과거 이력 조회에도 Data Scope와 기밀성 제한을 유지한다. 감사 schema는 여기서 정의하지 않는다.

추적: [PR-001/008/020/021/027/029/030](requirements.md), [PD-001–006/019/022](product-decisions.md), [MB-001–008 및 ARCH-001/002/LEGAL-001](open-questions.md), [Architecture 인계](architecture-handoff.md).
