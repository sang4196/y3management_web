# v1 Scope — 승인된 범위

2026-09-17 Multi-Branch 제품 방향 변경 승인 반영. 핵심 기능의 포함·제외는 더 이상 AI 제안이 아니다. 확정된 관계 안의 교차 이용 조건·정산 귀속·금액 노출 및 기존 BR·권한·NFR·cutover TODO는 미정이다. 실운영에서 기존 C# 프로그램을 대체하되 전체 기능 복제나 운영 데이터 이관을 요구하지 않는다.

## IN-V1 — 핵심 필수 범위

| 요구사항 | 승인 근거 | 후속 상세 |
| --- | --- | --- |
| [PR-001](requirements.md#pr-001) 운영 계정과 직무별 접근 | PD-001/002/003/004/019 | ARCH-001/002 |
| [PR-002](requirements.md#pr-002) 회원 기본정보 관리 | PD-006/022 | LEGAL-001, MB-002 |
| [PR-003](requirements.md#pr-003) PT Pass 생성·이력·잔여 관리 | PD-007/008/010/011/022 | BR-001/002, ARCH-003, MB-002/003 |
| [PR-004](requirements.md#pr-004) 업무 데이터 비활성화와 과거 조회 | PD-010/011/022 | BR-001/007, LEGAL-001 |
| [PR-005](requirements.md#pr-005) 트레이너 기본정보 관리 | PD-002/006/012/022 | BR-009, LEGAL-001, MB-001 |
| [PR-006](requirements.md#pr-006) PT Product·기준정보 관리 | PD-001/006/007/009/011 | BR-001/011, MB-007 |
| [PR-007](requirements.md#pr-007) Trainer Compensation Setting 관리 | PD-001/009/012/022; BR-PAY-009/010 | BR-010/011, ARCH-001 |
| [PR-008](requirements.md#pr-008) 실제 진행일별 개별 PT Session | PD-007/008/009/010/012/022 | BR-002/008/010/011, MB-001/002/003/005, UX-001 |
| [PR-009](requirements.md#pr-009) 제한된 권한의 Session 정정·취소 | PD-010/011/012/022 | BR-007, ARCH-001, MB-005 |
| [PR-010](requirements.md#pr-010) 기본급·Session·추가실적 월별 트레이너 정산 | PD-009/010/011/012/013 | BR-007/008/009/010/011, MB-006 |
| [PR-015](requirements.md#pr-015) Responsive Web에서 핵심 업무 이동 | PD-001/005/006/007/008 | ARCH-004, UX-001 |
| [PR-021](requirements.md#pr-021) 관리자 발급 운영 계정·권한 관리 | PD-001/019/022 | ARCH-001/002, MB-004 |
| [PR-026](requirements.md#pr-026) 접근 종료·재진입 | PD-019 | ARCH-002 |
| [PR-027](requirements.md#pr-027) 중요 운영 행위 감사 | PD-022 | ARCH-001, BR-007, LEGAL-001 |
| [PR-028](requirements.md#pr-028) 빈 운영 데이터에서 신규 설정·일괄 전환 | PD-004/017/018/019/020 | ARCH-002, OPS-001 |
| [PR-020](requirements.md#pr-020) Organization / Branch 관리 | PD-004/006 | MB-001–008 |
| [PR-029](requirements.md#pr-029) Trainer Authentication / Allowed PT Scope | PD-001/002/005/006 | MB-001/005, ARCH-001/002 |
| [PR-031](requirements.md#pr-031) 추가실적 | PD-027 | BR-013, MB-009/010 |
| [PR-030](requirements.md#pr-030) Backend Branch-scoped Authorization / Context | PD-001/004/006/012/022 | MB-001–008, ARCH-001 |

## 명시적 Future Scope — OUT-V1

v1의 PT 진행 등록은 실제 수업 완료 기록이다(PR-008). 사전 Reservation을 요구하거나 PLANNED/BOOKED 같은 예약 상태를 추가하지 않는다. 진행 기록 정정/취소(PR-009)는 아래 미래 예약 취소와 별개다.

| 항목 | 향후 방향 | 승인 |
| --- | --- | --- |
| Member Authentication / Member Self-Service | 자신의 PT Schedule·예약 Session·Pass·잔여 조회, PT 예약·Schedule 취소 후보. Member와 Login Account는 별개이며 연결은 후속 | PD-003 |
| PT Schedule / Reservation / Reservation Cancellation | v1에 Domain을 추가하지 않으며 향후 확장을 불필요하게 어렵게 만드는 구조적 제약 방지 | PD-025 |
| Member Schedule / Trainer Schedule 확장 | Self-Service와 함께 향후 도입 검토 | PD-025 |
| Mobile App | Trainer·Member Actor 후보. Business Logic의 Web UI 종속 방지; 기술 선택 없음 | PD-026 |

이 항목들은 단순 미채택 후보가 아닌 명시적 제품 Roadmap이다. 현재 v1 구현 승인은 아니다. Responsive Web은 이미 v1에 포함한다. Multi-Branch와 달리 여러 독립 고객사를 격리하는 Multi-Tenant 제품은 확정하지 않았다.

## OUT-V1 — 승인된 제외

| 요구사항/영역 | 취급 | 승인 근거 |
| --- | --- | --- |
| [PR-012](requirements.md#pr-012) 수동 트레이너 매출 | v1 제외; 후속 필요 확인 시 별도 검토 | PD-006/013/017 |
| [PR-013](requirements.md#pr-013) 락커 운영 | v1 제외; 후속 필요 확인 시 별도 검토 | PD-006/016 |
| [PR-014](requirements.md#pr-014) 락커 글꼴 조절 | v1 제외; 후속 필요 확인 시 별도 검토 | PD-005/016/023 |
| [PR-017](requirements.md#pr-017) 가계부 거래·자산·분류 | v1 제외; 후속 필요 확인 시 별도 검토 | PD-006/014/017 |
| [PR-018](requirements.md#pr-018) 고정 거래 | v1 제외; 후속 필요 확인 시 별도 검토 | PD-006/014/015 |
| [PR-019](requirements.md#pr-019) 가계부 자산·부채·순자산 통계 | v1 제외; 후속 필요 확인 시 별도 검토 | PD-014 |
| [PR-023](requirements.md#pr-023) 기존 Excel 가져오기·migration tooling | v1 제외; 기존 이관 도구는 구현하지 않음 | PD-017/020/023 |
| 계약·출석·고객 결제·환불·회원권·상담 | v1 추가하지 않음. Pass는 이 영역의 승인 아님 | PD-024 |
| 운영 데이터·계정·암호 이관, migration tooling | v1 제공하지 않음; 빈 데이터로 신규 운영 | PD-017/019/020 |
| 미확인 결제·SMS·카카오톡·이메일·장치 연동 | 임의 추가 없음. CSV/Excel import/export도 필수 아님 | PD-020 |

## NOT-COMMITTED — 필수로 채택하지 않은 후보

| 요구사항 | 상태 | 후속 |
| --- | --- | --- |
| [PR-011](requirements.md#pr-011) 추가 연간 통계 검토 | TBD | BR-009 |
| [PR-016](requirements.md#pr-016) 데스크톱 창 조작·종료 | DROP-CANDIDATE | 실제 필요 확인 시 후속 검토 |
| [PR-022](requirements.md#pr-022) 숨김 월 복사·상품 직접 선택 | DROP-CANDIDATE | UX-001과 별개; 후속 필요 확인 |
| [PR-024](requirements.md#pr-024) 미연결 생일 목록 | DROP-CANDIDATE | 후속 필요 확인 |
| [PR-025](requirements.md#pr-025) 빈 기타설정·급여 팝업 | DROP-CANDIDATE | 후속 필요 확인 |

여러 날짜 일괄 입력 UI는 후속 편의 후보로 유지한다. Desktop/Tablet/Smartphone Responsive Web과 Trainer의 Smartphone Session 등록은 v1 필수다. Branch별 및 Organization 전체 통계/집계 확장 가능성을 고려하지만 추가 통계 자체를 v1 필수로 승격하지 않는다.

## 출시 수용 기준과 미결정 경계

1. 빈 업무 데이터에서 새 Master Admin·Organization/Branch·운영 및 Trainer 계정·기준정보·회원·트레이너·상품·Pass를 준비할 수 있다. 기존 DB 접근·복제·암호 해독은 필요 조건이 아니다.
2. 동일 Payment Type FIFO, RATE 결과의 1,000원 단위 올림(FIXED_AMOUNT 제외), 저장 완료 이후 신규 Session부터 Rate/Fixed Amount 적용과 정상 등록 시 지급액 확정을 확인한다. Pass 이력과 실제 진행일별 개별 Session, Pass 잔여, Product Payment Type과 Trainer Compensation Setting, 월 정산의 일관성을 승인된 BR 예제로 확인한다.
3. 제한된 권한의 정정/취소가 잔여·정산에 일관되게 반영되고 회원·트레이너·Pass 비활성화 후 과거 조회가 가능하다.
4. Master Admin은 전체 Branch 정산, Branch Admin은 허용 Branch 정산만 접근한다. Branch Admin의 실제 지급금액 노출 수준은 MB-006 결정 후 검증하며 모든 Actor에게 동일 노출하지 않는다. 월 정산에서 트레이너·기간·Session 수·지급 정책·계산 기준·지급금액을 구분한다. 과거 월 재조회는 해당 기간의 유효한 Session Payment 결과를 집계하며 현재 Trainer Rate/Fixed Amount로 재계산하지 않는다(BR-PAY-009, CASE A/B/E). 적용 기본급과 유효 추가실적을 월 합계에 포함하고 기본급을 지점 수만큼 중복 가산하지 않는다. 과거 확정 정산의 기본급·합계도 현재 설정으로 자동 변경하지 않는다. 12개월 고정 평균·수동 매출 합산은 요구하지 않는다.
5. 세 보상 설정은 Master Admin이 전체 Trainer, Branch Admin이 자기 Home Branch 소속 Trainer에 대해 조회·변경 가능하고 Operator·Trainer(본인 포함)는 불가하다. 별도 승인 없이 변경하며 BR-PAY-010의 대상·항목·전후 값·Actor·권한/Branch Context·시점 감사를 확인한다. 최소 개인정보·직무 권한·Branch Context를 포함한 중요 행위 감사 요구를 확인한다. 구체 권한·보존 정책은 해당 TODO의 후속 승인 필요.
6. Desktop/Tablet/Smartphone 지원 브라우저와 현실적인 성능·백업·복구 기준은 PD-021/ARCH-004에서 정의한 뒤 실운영 준비를 검증한다.
7. 수용 기준 충족 후 일괄 전환한다. 장기 동일 업무 이중 입력은 하지 않는다. 짧은 검증/준비와 새로 생성할 운영 기준의 책임은 OPS-001이다.

8. Master Admin의 Branch 생성/관리와 Branch Admin의 구조 변경 금지를 확인한다. Branch A Admin은 허용되지 않은 Branch B 자료의 ID나 경로를 알아도 Backend에서 무단 접근이 거부되어야 한다. 특정 대상 교차 업무 조건은 MB-001/002/003/005와 구별해 검증한다.
9. Trainer가 Smartphone으로 로그인하여 허용 Member/PT 정보 확인 → 실제 Branch/날짜 확인 → 자신의 실제 Session 등록 → 잔여 및 자신의 Session 결과 확인까지 수행할 수 있다. 지급 설정 값은 노출하지 않는다. Desktop/Tablet에서도 주요 업무가 가능하며 화면 단순 축소만으로 통과하지 않는다.
10. 실제 Session Branch Context, Branch별 Session/Settlement 조회, 중요 행위의 Actor·Role·Branch Context와 관리자 Remaining Adjustment 이력을 추적한다. 확정 관계는 BR-OPS-001로 검증하며 남은 교차 업무 조건·정산 귀속/공개는 MB-001–010 결정 후 검증한다.

위 항목은 제품 기대 결과다. 테스트 구현·배포·전환은 이번 작업에서 실행하지 않았다. [Open Questions](open-questions.md)의 남은 업무 상세는 관련 상세 설계·구현 확정 전에 확인한다. Architecture 공통 제약 검토는 가능하나 MB-001–008에 의존하는 관계·권한·정산 등 상세 설계는 사용자 결정 전 확정할 수 없다. [Validation](validation-needed.md)의 AS-IS 미검증 항목을 모두 v1 출시 조건으로 요구하지 않는다.

## 변경 원칙

새로운 범위는 사용자 승인과 별도 요구사항으로 추가한다. 후속 상세 질문 때문에 CLOSED PD를 다시 OPEN으로 바꾸지 않는다. PT Pass·Session·지급 정책은 제품 개념이며 데이터 schema·API·기술·Architecture는 아직 정의하지 않았다.

## Product Baseline — 2026-09-17 지점 관계·보상 개정

최신 사용자 확정사항을 반영한 Architecture Input Baseline이다. [현재 결정과 변경 이력](README.md), [권한](users-and-roles.md), [업무 규칙](business-rules.md), [남은 결정 게이트](open-questions.md), [Architecture 인계](architecture-handoff.md)를 함께 따른다. Baseline 갱신은 모든 상세 업무 정책 또는 구현 완료를 뜻하지 않는다.

## 이번 개정의 포함·제외 및 결정 게이트

Trainer별 월 고정 Base Salary(PR-007/010)와 추가실적(PR-031)을 IN-V1으로 포함한다. 기본급 일할·근무일수·휴직 자동 계산은 OUT-V1이다. 세 보상 설정 권한은 [권한표](users-and-roles.md)를 따른다. 타 지점 지급 구성 MB-009, 추가실적 상세 BR-013, 기본급 적용 월 BR-012, 귀속 MB-010, 정산 공개 MB-006은 관련 상세 설계/구현 확정 전 사용자 결정이 필요하다. 미결정을 기능 제외나 권한 허용으로 해석하지 않는다.
