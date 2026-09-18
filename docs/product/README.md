# Product Specification — Architecture Input Baseline

**2026-09-17 지점 관계·추가실적·월 기본급·보상 설정 권한 개정.** 최신 사용자 확정사항이 이전 Baseline의 권한·정산·미정 관계를 대체하여 Product 문서를 갱신했다. 기존 C# 프로그램을 실제 운영에서 대체하는 새 웹 서비스이며 C# 구현은 AS-IS 참고다. 기존 데이터·계정·암호 이관 없이 새로 시작한다. 수정 범위는 `docs/product/`이고 Architecture·애플리케이션 구현은 수행하지 않는다.

## 변경 이력과 현재 유효 기준

| 이전 기준 — 변경 이력이며 현재 규칙 아님 | 현재 유효 기준 |
| --- | --- |
| 이전 Single Branch / Trainer non-login / PC 중심 방향 | 하나의 Organization 아래 여러 Branch, Trainer 직접 로그인/Session 등록, Responsive Web 유지 |
| Trainer/Member 소속 및 Pass 발급·교차 이용 미정 | 각각 단일 Home Branch / 단일 Issued Branch, 허용된 타 지점 이용 가능 |
| Product 공통/지점별 미정 | Organization 공통 Catalog, 지점별 가격 정책 추가 없음 |
| Branch Admin 관리 Branch 수 미정 | 단일 Branch 관리, 중간 다지점 역할 추가 없음 |
| Master Admin 전용 Rate/Fixed Amount | 세 보상 항목에 Master 전체 / Branch Admin 자기 Home Branch 소속 Trainer 권한 |
| 기본급 관리/합산 미채택, Session 지급액 중심 정산 | 월 고정 기본급·추가실적 v1 도입, 세 구성 요소 월 합산 |

과거 방향은 활성 규칙으로 적용하지 않는다. 기존 Requirement/Business Rule/Decision ID는 유지하고 새로운 추가실적 PR-031/PD-027 및 새 규칙 BR-PAY-014–016만 추가했다.

## 확정 v1과 범위 경계

Trainer는 한 시점에 Home Branch 하나에 소속되고 Branch에는 여러 Trainer가 있을 수 있다. Branch당 Trainer 한 명인 1:1이나 Trainer 동시 복수 소속 N:M을 요구하지 않는다. Member도 Home Branch 하나를 가지며 Pass는 Issued Branch 하나를 가진다. Trainer·Member·Pass는 허용된 조건에서 타 지점 PT 업무를 수행·이용할 수 있다. Session은 실제 Performed Branch를 식별하고 소속·발급 지점 변경으로 과거 수행 지점이 바뀌지 않아야 한다. Product는 Organization 공통 Catalog이며 지점별 가격 정책은 추가하지 않는다. Branch Admin은 하나의 Branch를 관리하고 일부 여러 지점만 담당하는 중간 관리자 역할은 추가하지 않는다.

Trainer Compensation Setting은 Rate·Fixed Amount·Base Salary이며 Product별 Trainer 지급 값은 도입하지 않는다. Rate / Fixed Amount / Base Salary 세 항목의 조회·설정·변경은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 단일 Branch를 Home Branch로 가진 Trainer에게만 허용한다. Operator와 Trainer는 본인 설정을 포함하여 모두 불가하다. 타 지점 지원 수업은 보상 설정 접근 권한을 부여하지 않는다. Backend에서 대상 Trainer의 Home Branch를 검증하며 직접 ID 요청과 감사·정산 등 우회 경로에도 제한을 적용한다.

모든 보상 설정 변경(최초 설정 포함)에 대상 Trainer, 변경 항목, 변경 전 값, 변경 후 값, 변경 Actor, Actor의 권한 및 Branch Context, 변경 시점을 추적한다. 별도 Master Admin 승인 없이 변경 가능하며 변경 요청→승인 대기→승인→반영 절차를 추가하지 않는다. 이 결정은 추가실적 승인이나 월 정산 마감/확정 절차를 면제하지 않는다.

Monthly Settlement = 해당 월 적용 Base Salary + 유효한 Session Payment 합계 + 유효한 Additional Performance 합계다. Trainer·대상 월·적용 기본급·Session 수·Session Payment 합계·추가실적 내역/합계·월 정산 합계를 구분한다. 2,500,000원 + 1,200,000원 + 150,000원 = 3,850,000원이며 여러 지점 수업으로 동일 월 기본급을 중복 가산하지 않는다. 타 지점 Session Payment 포함 여부는 MB-009 결정 전 확정하지 않는다.

Rate/Fixed Amount는 관리자 저장 완료 이후 신규 등록 Session부터 적용하며 정상 등록 시 지급액을 확정한다. FIXED_AMOUNT 우선·동일 Type FIFO·RATE Session별 1,000원 올림·FIXED_AMOUNT 설정값 사용을 유지한다. 현재 설정으로 과거 확정 Session Payment와 확정 정산의 기본급/합계를 자동 변경하지 않는다. 기본급 일할·근무일수·휴직 자동 계산은 제외한다.

Desktop/Tablet/Smartphone 핵심 업무 Responsive Web은 v1이다. Member 로그인·일정 조회·예약/취소·Mobile App은 Future Scope이며 자동 승격하지 않는다. 가계부·락커·수동 매출·고정 거래·계약/출석/고객 결제/환불/회원권/상담·migration tooling 제외도 유지한다. 추가실적은 Trainer 인센티브이며 기존 수동 매출과 동일한 AS-IS 사실로 취급하지 않는다. 독립 고객사 SaaS 범위는 추가하지 않는다.

## 문서 안내

| 문서 | 역할 |
| --- | --- |
| [Product Goal](product-goal.md) | 운영 목적·가치·AS-IS 경계 |
| [Product Decisions](product-decisions.md) | PD-001–027: 26 CLOSED / PD-021 OPEN |
| [Scope](scope.md) | v1/Future/제외와 수용 경계 |
| [Users and Roles](users-and-roles.md) | 최종 세 항목 권한표·단일 Branch Scope |
| [Requirements](requirements.md) | PR-001–031 및 추가실적 요구 |
| [Business Rules](business-rules.md) | BR-PAY-001–016, BR-OPS-001 및 문서 사례 |
| [User Scenarios](user-scenarios.md) | 로그인·PT·보상 설정·정산·타 지점 흐름 |
| [Non-functional Requirements](non-functional-requirements.md) | Backend 권한·감사·보존·Responsive |
| [Open Questions](open-questions.md) | 26 OPEN / 4 CLOSED; 해결 부분과 남은 질문 분리 |
| [Validation Needed](validation-needed.md) | AS-IS 8 OPEN / 12 REFERENCE-ONLY 상태 보존 |
| [AS-IS → TO-BE Mapping](as-is-to-be-mapping.md) | 기존 F01–59/H01–04 63개 추적과 새 사용자 결정 구별 |
| [Architecture Handoff](architecture-handoff.md) | 공통 검토 입력과 상세 결정 게이트 |

## 해결된 부분과 남은 결정

MB-001/002/003/004/007의 단일 소속·발급·교차 이용 가능·단일 관리자 Scope·공통 Catalog와 BR-009의 기본급 도입/합산 질문 부분은 해결했다. 잔여 질문이 있으므로 해당 ID 전체는 OPEN이다. 기존 BR-003/004/005/006 CLOSED를 유지하며 전체가 새로 CLOSED된 기존 OPEN ID는 없다. PD-001/004/006/009/012/022를 최신 확정으로 갱신하고 PD-027을 추가했다.

지급액·권한·귀속에 영향을 주는 주요 OPEN은 다음과 같다.

- MB-009: 타 지점 보상 A(추가실적 전체 처리) / B(일반 지급 + 별도 인센티브). 어느 쪽도 확정하지 않으며 해당 보상 설계/구현 결정 게이트다.
- BR-013: 추가실적 등록 권한/Branch 기준·Trainer 신청·관리자 승인·수동/유형별 금액·정정/취소·마감 이후 처리.
- BR-012: 기본급 적용 월·관리자 지정·미확정 정산 반영·입퇴사 등 적용 금액 정책.
- MB-010/006: 소속 이동·타 지점 수업·추가실적의 정산/비용 귀속과 Branch Admin 정산 공개.
- MB-001–005/007/008: 이동·구체 교차 업무 접근·본인 정정·Operator/계정 위임·Branch Admin 상품 관리·Branch 수명.

기존 Pass 상태/사용·정정/취소·날짜·상품 변경·입력·개인정보/보존·운영 품질 OPEN도 유지한다. 구체 상태 집계는 각 문서의 실제 Status 기준이다. Product 결정으로 AS-IS 검증을 완료 처리하지 않는다.

확정 조직·관계·권한 경계·감사·정합성·보존·Responsive/Future 제약으로 공통 Architecture 검토가 가능하다. 위 미결정에 의존하는 상세 설계/구현은 사용자 결정 전 확정하지 않는다. DB/API·인증·기술 스택·snapshot/history 방식은 선택하지 않았다.

## 이번 개정 문서 검증

아래는 요구사항·권한표·업무 규칙의 대조 결과다. 애플리케이션 테스트나 운영 검증이 아니다.

| CASE | 문서상의 기대 결과 | 근거 |
| --- | --- | --- |
| 1 | Master Admin 전체 Trainer 세 항목 조회/변경 허용, 별도 승인 없음, 감사 | PR-007; BR-PAY-010; 역할표 |
| 2 | 수원점 Admin이 수원 소속 Trainer 세 항목 변경 허용, 승인 없음, 감사 | SC-012; 역할표 |
| 3 | 강남점 지원 수업 이력만으로 수원 소속 Trainer 설정 접근 불가 | PR-030; BR-PAY-010; 역할표 |
| 4 | Operator·Trainer는 본인 포함 세 항목 조회/변경 불가 | NFR-001; 역할표 |
| 5 | 타 지점 수업에도 Home Branch 유지, 실제 Performed Branch 식별 | PR-005/008; BR-OPS-001 |
| 6 | 허용 Pass 타 지점 이용 가능, 발급 지점 차이만으로 일률 차단 없음; 업무 권한 검증 필요 | PR-003/030; MB-003/005 |
| 7 | 2,500,000 + 1,200,000 + 150,000 = 3,850,000원; 기본급 중복 없음 | PR-010; BR-PAY-016 |
| 8 | 현재 세 설정 변경으로 과거 확정 지급·월 정산 자동 변경 없음 | PR-007/010; BR-PAY-009/014/016 |
| 9 | 타 지점 기본 수당 포함 여부 OPEN, 미정 금액 작성 없음 | MB-009; SC-016 |
| 10 | FIXED_AMOUNT 우선/FIFO/RATE 1,000원 올림/FIXED_AMOUNT 설정값 유지 | BR-PAY-003–006/013; CASE I–K |

검증 완료: 13개 Product 문서 전체를 읽고 위 CASE 1–10을 요구사항·권한표·규칙에 대조했다. 활성 규칙 충돌 검색, 기존 ID 보존, 상대 링크/앵커 오류 없음, 63개 AS-IS 매핑, Status 집계 및 AS-IS 검증 상태 불변을 확인했다. 작업 전후 실제 원문 diff와 저장소 파일 해시로 Product 13개 파일만 변경되고 삭제/외부 변경이 없음을 확인했다. docs/는 기존부터 Git 미추적 상태라 tracked diff가 비어 있어 원문 비교를 병행했다. 문서 신규 생성·애플리케이션 테스트·운영 검증·Architecture 설계는 수행하지 않았다.
