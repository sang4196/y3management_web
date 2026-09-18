# Architecture 설계를 위한 Product Input Baseline

상태: **2026-09-17 지점 관계·추가실적·월 기본급·보상 설정 권한 개정**. 공통 Architecture 검토의 입력이며 모든 상세 업무 정책이 결정되었다는 뜻이 아니다. [결정](product-decisions.md), [요구사항](requirements.md), [업무 규칙](business-rules.md), [권한표](users-and-roles.md), [OPEN](open-questions.md)을 함께 따른다.

## 공통 검토가 가능한 확정 제품 제약

| 영역 | 확정된 입력 | 추적 |
| --- | --- | --- |
| 운영 목적 | 실제 운영에서 C# 프로그램을 대체. 기존 데이터·계정·암호 이관 없이 새로 시작하고 준비 후 일괄 전환. C#은 AS-IS 참고 | PD-017/018/019; PR-028 |
| 조직 | 하나의 Organization 아래 여러 Branch. 독립 고객사 여러 곳의 SaaS 범위를 추가하지 않음 | PD-004; PR-020 |
| Trainer | 한 시점 Home Branch 하나, Branch에는 여러 Trainer. 타 지점 수업으로 소속 변경/추가 없음. 동시 복수 소속 N:M 요구 없음 | PR-005; BR-OPS-001 |
| Member / Pass | Member Home Branch 하나, Pass Issued Branch 하나. 허용된 타 지점 PT/Pass 이용 가능. 소속/발급 지점 차이만으로 일률 차단하지 않음 | PR-002/003 |
| Session | 실제 Performed Branch 식별. Trainer/Member Home Branch 및 Pass Issued Branch와 구별. 소속·발급 변경으로 과거 수행 지점 변경 금지 | PR-008; BR-OPS-001 |
| Product | Organization 공통 Catalog, 지점별 가격 정책 추가 없음. 기존 Master Admin 관리 권한 유지; Branch Admin 관리 권한은 OPEN | PR-006; MB-007 |
| 관리자 범위 | Master Admin은 Organization 전체, Branch Admin은 단일 Branch. 일부 여러 지점만 담당하는 중간 역할 없음 | PD-001/004; PR-030 |
| 업무 접근 | Role과 Data Scope 분리. 특정 Member/Pass/Session의 교차 업무 허용과 다른 지점 전체 목록 조회는 별개. Backend에서 직접 ID 요청·목록·검색·집계에도 제한 강제 | PR-001/030; NFR-001 |
| Trainer 로그인 | 직접 로그인하여 허용 Session 등록·본인 조회. Smartphone 현장 흐름이 주요 v1 Use Case | PR-008/029; SC-003 |
| 보상 설정 | Trainer별 Rate / Fixed Amount / 월 고정 Base Salary. Product는 RATE/FIXED_AMOUNT 방식만 결정. Product별 Trainer 지급 값 없음 | PR-007; BR-PAY-001/002/014 |
| 보상 설정 권한 | Master Admin은 전체 Trainer, Branch Admin은 자기 Branch가 Home Branch인 Trainer만 세 항목 조회·변경. Operator·Trainer(본인 포함) 불가. Performed Branch는 권한 근거가 아님 | BR-PAY-010; SC-012 |
| 승인과 감사 | 권한 있는 관리자는 별도 Master 승인 없이 설정 변경. 대상·항목·전후 값·Actor·권한/Branch Context·시점 감사. 감사/정산 경로의 비인가 노출 금지 | PR-027; NFR-004 |
| 추가실적 | Trainer 인센티브로 v1 도입. 타 지점 지원 수업·회원 유지 등; Session 연계 또는 비연계 가능. 생성·정정·취소 감사. 고객 매출/결제·가계부와 구별 | PR-031; PD-027; BR-PAY-015 |
| 월 기본급 | Trainer별 월 고정 금액. Product/Session별 금액 아님. 입퇴사 일할·근무일수·휴직 자동 급여 계산 제외 | BR-PAY-014 |
| 월 정산 | 적용 기본급 + 유효 Session Payment 합계 + 유효 추가실적 합계. Trainer/월/기본급/Session 수/지급 합계/추가실적 내역·합계/전체 합계 구분. 여러 지점 수업에도 기본급 중복 가산 금지 | PR-010; BR-PAY-016 |
| 과거 결과 | 현재 보상 설정 변경으로 과거 확정 Session Payment 및 확정 정산의 적용 기본급·합계 자동 변경 금지. 별도 정정 업무와 구별 | BR-PAY-009/014/016 |
| Responsive Web | Desktop/Tablet/Smartphone에서 핵심 업무·터치·작은 화면 주요 정보/Action 지원. Desktop 단순 축소로 충족하지 않음 | PR-015; NFR-008 |

수원점 소속 Trainer가 강남점에서 수업해도 강남점 Branch Admin에게 보상 설정 권한은 생기지 않는다. 추가실적 등록/승인 권한과 정산 공개 범위도 보상 설정 권한에서 자동 도출하지 않는다.

추가실적은 대상 Trainer·사유/유형·금액·발생 시점/정산 기간·Branch Context·필요시 Member/Session·등록자/시점·정정/취소 이력을 업무적으로 식별한다. 정확한 입력 항목은 후속 설계다.

## 보존할 일반 Session 규칙

| 규칙 | 기대 결과 |
| --- | --- |
| Pass 선택 | 사용 가능한 Pass의 FIXED_AMOUNT 우선, 동일 Payment Type FIFO. 잔여 0인 Pass 정상 차감 금지 |
| 기록·차감 | 실제 진행 날짜별 개별 Session; 정상 등록 시 Pass 횟수 차감 |
| RATE | 해당 Session 상품 회당 단가 × Trainer Rate를 Session별 1,000원 단위 올림. 12,300→13,000원, 13,000→13,000원 |
| FIXED_AMOUNT / 서비스 | 해당 Trainer Fixed Amount 그대로 사용; RATE 올림 추가 적용 없음 |
| 적용·확정 | 권한 있는 관리자 저장 완료 이후 새로 등록되는 Session부터 Rate/Fixed Amount 적용, 정상 등록 시 지급액 계산·확정. 실제 수업일과 등록 시점 구별 |
| 월 집계 | 유효 확정 Session Payment 합산. 현재 설정으로 최초 계산/재계산하거나 월 합계에 재올림하지 않음 |
| 조정·정정 | 관리자 수동 횟수 조정 사유·이력, Session 취소/정정의 횟수 복원·이력·정산 일관성 유지 |

추적: BR-PAY-001–013, BR-OPS-001. 이 일반 지급 규칙으로 타 지점 보상 구성 A/B를 확정하지 않는다. MB-009 결정 전 기본 수당 0원이나 일반 수당+추가실적의 자동 이중 지급을 가정하지 않는다. 예시 월 합계 2,500,000 + 1,200,000 + 150,000 = 3,850,000원은 유효 구성 합계 예시이며 미결정 타 지점 수업의 예상 금액이 아니다.

## Future 및 제외 경계

Member 로그인/Self-Service, 일정 조회·예약/취소, Member/Trainer Schedule 확장, Mobile App은 명시적 Future Scope다. v1에 예약 Domain·Member 로그인·App을 구현하지 않는다. 향후 도입을 불필요하게 어렵게 하는 구조적 제약과 Business Logic의 특정 Web UI 종속을 피해야 한다(NFR-013). 현재 API/Client 기술 선택은 없다.

기존 가계부·락커·수동 매출·고정 거래·계약/출석/고객 결제/환불/회원권/상담·migration tooling 제외를 유지한다. 추가 통계·일괄 입력 편의·미확인 연동·import/export는 필수로 자동 승격하지 않는다. 빈 급여 팝업을 구현하는 요구와 승인된 기본급/추가실적은 구별한다.

## 상세 설계·구현 확정을 보류할 결정 게이트

| OPEN | 남은 업무 결정 | 결정이 필요한 지점 |
| --- | --- | --- |
| MB-001/002/003/005 | Trainer/Member 이동, Member 조회·교차 PT/Pass 업무 허용 조건, Trainer 본인 정정/취소 | 이동·교차 대상 선택·권한·정정 상세 |
| MB-004 | Operator Scope, Branch Admin 자기 지점 정보 변경·계정 발급 위임 | 운영/계정 권한 상세 |
| MB-006 | Branch Admin에게 공개할 Trainer·월·정산 금액/계산 근거, 설정 우회 노출 방지 | 정산·Session·감사 열람 상세 |
| MB-007/008 | Branch Admin 공통 상품 관리; Branch 비활성 조건·진행 업무/이력 | 상품 권한·Branch 수명 |
| MB-009 | A: 기록/차감 유지, 보상 전체를 추가실적 처리 / B: 일반 지급 + 별도 인센티브 | 타 지점 Session 보상 상세 설계 및 구현의 필수 사용자 결정 게이트 |
| MB-010 | 소속 이동 기본급/실적, 타 지점 Session/추가실적의 정산·비용 귀속 | 지점별 집계·공개. Home/Performed/귀속 Branch 동일 가정 금지 |
| BR-012 | 기본급 적용 월·관리자 지정 여부·미확정 정산 반영·입퇴사 등 적용 금액 정책 | 기본급 적용·월 정산 반영 |
| BR-013 | 추가실적 등록 권한/지점 기준·Trainer 신청·승인·수동/유형 계산·정정/취소·마감 이후 처리 | 추가실적 입력·권한·산정·수명 |
| BR-001/002, ARCH-003 | Pass 상태·횟수 조정·사용 조건·상한 | Pass 수명·차감 상세 |
| BR-007/008/009 | 정정/취소·확정 이후 정정, 시간대·중복·소급/월 경계, 추가 통계·정산 확인/마감/확정 절차 | 정정·날짜·정산 수명 |
| BR-010/011 | 금액·횟수 입력 범위/누락, Product 변경의 기존 Pass 적용 | 입력 검증·상품 변경 상세 |
| ARCH-001/002 | 권한 기술 모델·감사 열람 구현·계정 수명; 미정 업무 열람은 Product 확인 | 인증/인가 설계 |
| ARCH-004 / PD-021 | 브라우저·성능·가용성·백업/복구·운영 책임 | NFR 수용 기준 및 실운영 준비 |
| UX-001 / OPS-001 / LEGAL-001 | 일괄 입력 편의, 준비 책임/시작일/전환, 개인정보·보존·삭제 | 기능 채택/관련 설계 및 실운영 전 |

보상 설정의 별도 승인 없음은 추가실적 승인이나 월 정산 마감/확정의 승인 생략을 뜻하지 않는다. 미정 업무 조건을 테이블 편의나 기술 기본값으로 대신 결정하지 않는다.

## Architecture 결정 책임

확정 관계·권한 경계·감사·정합성·결과 보존·Responsive/Future 제약은 공통 검토 가능하다. 위 OPEN에 의존하는 상세만 결정 전 보류한다. DB schema·관계 저장 모델·API endpoint·인증 방식·프레임워크·라이브러리·동시성·트랜잭션 경계·지급/정산 snapshot 또는 history 보존 방식은 Architecture에서 결정하며 이 문서에서 선택하지 않는다. 세 보상 항목을 반드시 같은 테이블에 저장하지 않아도 된다.

Product Decisions 26 CLOSED / 1 OPEN(PD-021), Open Questions 26 OPEN / 4 CLOSED, AS-IS Validation 8 OPEN / 12 REFERENCE-ONLY다. AS-IS 검증 상태는 변경하지 않았다. Baseline은 상세 결정 완료·구현 완료·출시 준비 완료를 뜻하지 않는다.
