# 비기능 요구사항

승인된 제품 결과와 아직 승인되지 않은 품질 후보를 구분한다. 적용 범위는 확정된 핵심 PT v1이다. 기술·저장 방식·구체 수치는 결정하지 않는다.

<a id="nfr-001"></a>
## NFR-001. 인증과 직무별 접근 통제

출처/상태: APPROVED-TO-BE

제품 필요: Master Admin·Branch Admin·Operator·Trainer 로그인 계정은 Role과 Data Scope에 허용된 자료/기능만 접근한다. Member 로그인은 Future Scope다.

수용 기준 / 남은 상세: Rate / Fixed Amount / Base Salary 세 항목의 조회·설정·변경은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 단일 Branch를 Home Branch로 가진 Trainer에게만 허용한다. Operator와 Trainer는 본인 설정을 포함하여 모두 불가하다. 타 지점 지원 수업은 보상 설정 접근 권한을 부여하지 않는다. Backend에서 대상 Trainer의 Home Branch를 검증하며 직접 ID 요청과 감사·정산 등 우회 경로에도 제한을 적용한다. UI 숨김으로 충족하지 않으며 목록·검색·집계·개별 요청에도 Scope를 적용한다. 특정 교차 업무 허용과 다른 지점 전체 목록 접근을 구분한다. 기술 모델은 ARCH-001, 계정 수명은 ARCH-002다.

관련 요구·결정: PD-001/002/003/019/022; PR-001/021/026. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

<a id="nfr-002"></a>
## NFR-002. 업무 데이터 정합성

출처/상태: APPROVED-TO-BE

제품 필요: Session 생성·정정/취소와 Pass 잔여·정산 결과가 일치해야 한다. 부분 반영을 정상 완료로 취급하지 않는다.

수용 기준 / 남은 상세: 승인된 전후 수치 사례로 잔여와 월 지급액을 대사한다. 업무 단위 일관성은 필요하나 트랜잭션 구현 방식은 정하지 않는다. BR-001–007.

관련 요구·결정: PD-007/008/010/012; PR-003/008/009/010. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

<a id="nfr-003"></a>
## NFR-003. 동시 작업과 재시도

출처/상태: NEW-CANDIDATE — 승인된 정합성을 위한 검증 후보

제품 필요: 동시 운영이나 재시도로 Session과 잔여의 중복 반영·변경 유실이 발생하지 않는 결과가 필요하다.

수용 기준 / 남은 상세: 이중 제출·응답 유실·동시 정정 사례의 기대 결과를 상세화한다. 같은 날짜의 별개 Session을 중복으로 단정하지 않는다. BR-008, ARCH-004.

관련 요구·결정: PD-010/021; PR-008/009. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

<a id="nfr-004"></a>
## NFR-004. 중요 행위 감사

출처/상태: APPROVED-TO-BE

제품 필요: Session·Pass 잔여 변경, 보상 설정 세 항목의 변경, 추가실적 생성·정정·취소, 계정/권한·중요 Branch 관리 행위를 감사할 수 있어야 한다.

수용 기준 / 남은 상세: 모든 보상 설정 변경(최초 설정 포함)에 대상 Trainer, 변경 항목, 변경 전 값, 변경 후 값, 변경 Actor, Actor의 권한 및 Branch Context, 변경 시점을 추적한다. 별도 Master Admin 승인 없이 변경 가능하며 변경 요청→승인 대기→승인→반영 절차를 추가하지 않는다. 이 결정은 추가실적 승인이나 월 정산 마감/확정 절차를 면제하지 않는다. 감사 경로의 설정 우회 노출도 금지한다. 저장 구조·조회 구현은 Architecture, 보존 기간은 LEGAL-001이다.

관련 요구·결정: PD-010/022; PR-027. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

<a id="nfr-005"></a>
## NFR-005. 개인정보와 지급 정보 보호

출처/상태: APPROVED-TO-BE

제품 필요: 업무에 필요한 최소 개인정보만 저장하고 회원·트레이너·지급 정보를 권한에 따라 제한한다.

수용 기준 / 남은 상세: 항목별 필요성·열람·보존·법적/운영상 삭제 정책은 LEGAL-001. 기존 생일·급여 등 모든 필드를 필수로 승계하지 않는다.

관련 요구·결정: PD-001/011/022; PR-002/004/005. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

<a id="nfr-006"></a>
## NFR-006. 백업과 복구

출처/상태: TBD / PRODUCT-DECISION PD-021 OPEN

제품 필요: Organization 내 여러 Branch의 신규 운영 데이터의 백업·복구 요구를 현실적으로 정의한다. 기존 자료 이관이나 이관 실패 복구를 요구하지 않는다.

수용 기준 / 남은 상세: 허용 데이터 손실·복구시간·확인 주기·책임과 복구 결과 대사 기준은 ARCH-004. 수치와 방식 미정.

관련 요구·결정: PD-017/018/021. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

<a id="nfr-007"></a>
## NFR-007. 결과와 오류 안내

출처/상태: NEW-CANDIDATE — 품질 수용 기준 후보

제품 필요: 정상 완료·미반영·조회 실패·자료 없음을 구분하여 사용자가 업무 결과를 확인할 수 있게 한다.

수용 기준 / 남은 상세: Session/Pass 변경 후 결과 확인과 실패 시 다음 행동 안내를 검토한다. 세부 오류 경험은 후속 UX에서 결정하며 기술 상세와 개인정보를 노출하지 않는다.

관련 요구·결정: PD-010; PR-008/009/015. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

<a id="nfr-008"></a>
## NFR-008. Responsive Web 사용성

출처/상태: APPROVED-TO-BE; 접근성 세부 NEW-CANDIDATE

제품 필요: Desktop/Tablet/Smartphone responsive layout과 터치 기반 조작을 지원한다. 작은 화면에서도 사용자별 주요 정보 확인과 주요 Action이 실질적으로 가능해야 한다. Desktop 화면을 단순 축소하는 것으로 충족하지 않는다.

수용 기준 / 남은 상세: 브라우저/버전·breakpoint는 ARCH-004와 Frontend Design에서 정한다. 각 Actor의 허용된 회원 검색·Pass/Session 처리·정산 확인을 지원 기기에서 검증한다. 특히 Trainer가 Smartphone으로 로그인 → 허용 Member/PT 확인 → 실제 Branch/진행일 확인 → Session 등록 → 자신의 Session 및 결과 확인까지 수행할 수 있어야 한다. 지급 설정을 노출하지 않는다. 키보드·확대 등 상세 사용성 기준은 후속 검토.

관련 요구·결정: PD-005; PR-015. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

<a id="nfr-009"></a>
## NFR-009. 성능과 데이터 증가

출처/상태: TBD / PRODUCT-DECISION PD-021 OPEN

제품 필요: Organization의 Branch 수·Branch별 운영자·Trainer 직접 로그인 수 및 회원·Pass·Session 증가량을 기준으로 응답시간을 정의한다. 대규모 트래픽을 가정하지 않는다.

수용 기준 / 남은 상세: 검색·저장·월 정산의 자료량/동시량/시간 목표를 ARCH-004에서 합의한다. VAL-016은 현재 업무 측정 참고.

관련 요구·결정: PD-021; PR-002/008/010. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

<a id="nfr-010"></a>
## NFR-010. 가용성과 업무 연속성

출처/상태: TBD / PRODUCT-DECISION PD-021 OPEN

제품 필요: 지원 운영시간과 허용 중단·업무 재개 요구를 정의한다. 준비 완료 후 일괄 전환하며 장기 이중 입력은 하지 않는다.

수용 기준 / 남은 상세: 가용성 목표와 장애 시 업무 처리 여부 확인·대응은 ARCH-004, 짧은 전환 준비는 OPS-001. 오프라인 기능은 자동 포함하지 않는다.

관련 요구·결정: PD-018/021; PR-028. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

<a id="nfr-011"></a>
## NFR-011. 운영 상태와 장애 대응

출처/상태: TBD / PRODUCT-DECISION; 상세 관찰 항목 NEW-CANDIDATE

제품 필요: 실운영 시스템의 실패와 잘못된 반영을 발견하고 대응할 수 있는 운영 요구를 정한다.

수용 기준 / 남은 상세: 관찰할 사건, 대응 책임·시간·안내 방식은 ARCH-004. 특정 모니터링 도구·알림 연동을 선택하지 않는다.

관련 요구·결정: PD-021/022; NFR-004/006. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

<a id="nfr-012"></a>
## NFR-012. 날짜와 지급액의 일관성

출처/상태: APPROVED-TO-BE; 입력값 검증·날짜 경계 상세만 OPEN

제품 필요: Monthly Settlement = 해당 월 적용 Base Salary + 유효한 Session Payment 합계 + 유효한 Additional Performance 합계다. Trainer·대상 월·적용 기본급·Session 수·Session Payment 합계·추가실적 내역/합계·월 정산 합계를 구분한다. 2,500,000원 + 1,200,000원 + 150,000원 = 3,850,000원이며 여러 지점 수업으로 동일 월 기본급을 중복 가산하지 않는다. 타 지점 Session Payment 포함 여부는 MB-009 결정 전 확정하지 않는다. 현재 설정 변경으로 과거 확정 Session Payment·월 정산의 적용 기본급/합계를 자동 변경하지 않는다. 소속·발급 지점 변경으로 과거 Session Performed Branch가 바뀌지 않아야 한다.

수용 기준 / 남은 상세: BR-PAY-001–016을 따른다. RATE Session별 1,000원 올림과 FIXED_AMOUNT 설정값, 관리자 저장 완료 이후 신규 등록에 Rate/Fixed Amount 적용 및 정상 등록 시 확정은 유지한다. 기본급 적용 월 BR-012, 추가실적 정책 BR-013, 타 지점 보상 MB-009, 귀속/열람 MB-010/006은 상세 결정 전 보류한다. 날짜 BR-008·입력 BR-010·Product 변경 BR-011도 유지한다.

관련 요구·결정: PD-008/009/012; PR-007/008/010. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

AS-IS 도출 참고: [위험 및 미확인 사항](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md), [현재 사실 검증 목록](validation-needed.md). K02/K05는 정합성, K13/K15는 동시성, K18/K19/K38은 결과·감사, K06/K07/K35는 접근, K09/K10/K22는 복구, K24/K25는 계산 검증의 참고다. 기존 가계부·락커 결함을 v1 기능으로 승계하지 않는다.

<a id="nfr-013"></a>
## NFR-013. Future Domain / Client 확장 제약

출처/상태: APPROVED-TO-BE / Future Constraint

제품 필요: 향후 Member Authentication/Self-Service와 Schedule/Reservation 도메인 추가를 불필요하게 어렵게 만드는 구조적 제약을 피해야 한다. Web UI에 Business Logic을 강하게 결합하여 Trainer·Member 대상 Mobile App 등 다른 Client에서 동일 업무 기능을 사용할 수 없게 만들지 않아야 한다.

수용 기준 / 남은 상세: 현재 예약 도메인·Mobile App·Member 로그인을 구현하지 않는다. Member와 Login Account를 동일시하지 않으며 향후 연결은 Architecture/Product Expansion에서 정의한다. 구체 API Architecture·인증·Web/Mobile Framework를 여기서 선택하지 않는다.

관련 요구·결정: PD-003/025/026; [Scope](scope.md), [Architecture Handoff](architecture-handoff.md).

## Product Baseline — 2026-09-17 지점 관계·보상 개정

최신 사용자 확정사항을 반영한 Architecture Input Baseline이다. [현재 결정과 변경 이력](README.md), [권한](users-and-roles.md), [업무 규칙](business-rules.md), [남은 결정 게이트](open-questions.md), [Architecture 인계](architecture-handoff.md)를 함께 따른다. Baseline 갱신은 모든 상세 업무 정책 또는 구현 완료를 뜻하지 않는다.
