# Unknown / Validation Needed

현재·과거 사실 검증 목록이다. 미래 선택은 [Product Decisions](product-decisions.md)와 [후속 TODO](open-questions.md)에서 관리한다. 기존 20개 항목의 미검증 사실·방법·근거를 보존한다. 이번 문서 갱신에서 실행/운영 DB 검증을 수행하지 않았다.

OPEN 8개는 현재 업무 파악에 유용한 확인 항목이다. REFERENCE-ONLY 12개는 이관 없음 또는 v1 제외에 따라 AS-IS 참고로 보존하며 v1 필수 검증/출시 차단 조건이 아니다. REFERENCE-ONLY는 검증 완료를 뜻하지 않는다. OPEN 또한 기존 프로그램 재현 시험 전체를 출시 필수로 만드는 의미가 아니다. TO-BE 수용 검증과 구분한다.

<a id="val-001"></a>
## VAL-001

Description: 실제 배포 프로그램·버전이 저장소와 일치하는지, 누가 어떤 메뉴를 사용하는지 확인

Why validation is needed: 정적 분석은 배포 바이너리와 실제 직책·공유 계정을 증명하지 못함

How to validate: 담당자 인터뷰와 배포 버전·메뉴를 읽기 전용으로 비교

Impact if incorrect: 현재 업무 담당자 파악 오류. 승인된 Master Admin/Branch Admin/Operator/Trainer Actor 범위를 자동 변경하지 않고 권한 상세 분석에 참고한다.

Related AS-IS Evidence: 08 인증; verification-report; K29/K35. [위험 목록](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md)

Related product: PD-001; ARCH-001

Status: OPEN

<a id="val-002"></a>
## VAL-002

Description: 운영 DB 테이블·제약·트리거·프로시저·서버 설정 확인

Why validation is needed: DDL 13개/107컬럼은 운영 실체를 보장하지 않음

How to validate: 승인된 DB 메타데이터와 복제본을 저장소 DDL/SQL에 대조

Impact if incorrect: 현행 시스템 해석에 남는 불확실성이다. 기존 데이터/계정 이관 및 제외 기능의 호환성을 요구하지 않으므로 이 항목의 미검증 자체는 v1 장애 요인이 아니다. 향후 해당 업무 재검토 시 참고한다.

Related AS-IS Evidence: 05 DB; K14/K22/K23/K25/K30/K31. [위험 목록](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md)

Related product: PD-013–020/023 중 해당 제외·이관 없음 결정; AS-IS 참고만 유지

Status: REFERENCE-ONLY

<a id="val-003"></a>
## VAL-003

Description: 진행 기록·잔여 차감·삭제 복원·수정의 실제 결과 확인

Why validation is needed: 분리 저장과 0행 성공 경로의 운영 영향은 미확인

How to validate: 비식별 복제본에서 일반/서비스·잔여0·상품변경·실패 사례 전후 자료 대사

Impact if incorrect: 필요한 정정 사례를 놓칠 수 있다. 결함 복제나 기존 잔여 이관이 아니라 BR-002/007의 업무 사례 참고다.

Related AS-IS Evidence: B02/B03; K02/K05/K19/K20/K38. [위험 목록](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md)

Related product: PR-003/008/009; BR-002/007

Status: OPEN

<a id="val-004"></a>
## VAL-004

Description: 일반·서비스 혼합 지급금액, 소수·공제·서비스 단가의 실제 관행 확인

Why validation is needed: 코드 계산 결함과 운영자가 인정한 금액은 다를 수 있음

How to validate: 정산 담당자의 승인 사례 및 비식별 표본과 계산값 비교

Impact if incorrect: 잘못된 지급 관행을 새 규칙으로 확정할 위험. 현재 AS-IS 관행은 미검증이지만 TO-BE 계산식·서비스 지급은 BR-PAY-001–008, 과거 확정 결과 보존은 BR-PAY-009로 이미 승인되었다. RATE 결과의 1,000원 단위 올림도 BR-PAY-013으로 확정이다. 남은 입력값 검증 등만 별도 확인하며 AS-IS 관행으로 승인 규칙을 바꾸지 않는다.

Related AS-IS Evidence: R09/R10/R14/R15; K04/K24/K25. [위험 목록](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md)

Related product: PR-007/010; BR-010/011

Status: OPEN

<a id="val-005"></a>
## VAL-005

Description: 이체 양쪽 잔액과 수정·삭제·직접 잔액 조정의 운영 정합성 확인

Why validation is needed: 한쪽 저장 누락과 부분 실패는 정적 경로이며 손상 규모 미확인

How to validate: 기초잔액·장부·별도 조정 자료와 자산 잔액을 복제본에서 대사

Impact if incorrect: 현행 시스템 해석에 남는 불확실성이다. 기존 데이터/계정 이관 및 제외 기능의 호환성을 요구하지 않으므로 이 항목의 미검증 자체는 v1 장애 요인이 아니다. 향후 해당 업무 재검토 시 참고한다.

Related AS-IS Evidence: B05/B06; K01/K03/K19/K20/K38. [위험 목록](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md)

Related product: PD-013–020/023 중 해당 제외·이관 없음 결정; AS-IS 참고만 유지

Status: REFERENCE-ONLY

<a id="val-006"></a>
## VAL-006

Description: 고정 거래의 실제 실행·누락·반복 및 수동 보충 관행 확인

Why validation is needed: 월 반복 결함과 마지막 입력일 별도 저장이 있음

How to validate: 연말/월말/지정일 표본·실제 생성 내역·담당자 처리 기록 비교

Impact if incorrect: 현행 시스템 해석에 남는 불확실성이다. 기존 데이터/계정 이관 및 제외 기능의 호환성을 요구하지 않으므로 이 항목의 미검증 자체는 v1 장애 요인이 아니다. 향후 해당 업무 재검토 시 참고한다.

Related AS-IS Evidence: B07; K12/K26. [위험 목록](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md)

Related product: PD-013–020/023 중 해당 제외·이관 없음 결정; AS-IS 참고만 유지

Status: REFERENCE-ONLY

<a id="val-007"></a>
## VAL-007

Description: 락커 owner_type 실제 값과 소유자 연결 확인

Why validation is needed: DDL·enum·JOIN의 의미가 불일치

How to validate: 비식별 표본의 번호·소유자·현장 배정표 대사

Impact if incorrect: 현행 시스템 해석에 남는 불확실성이다. 기존 데이터/계정 이관 및 제외 기능의 호환성을 요구하지 않으므로 이 항목의 미검증 자체는 v1 장애 요인이 아니다. 향후 해당 업무 재검토 시 참고한다.

Related AS-IS Evidence: 05 DB; K11. [위험 목록](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md)

Related product: PD-013–020/023 중 해당 제외·이관 없음 결정; AS-IS 참고만 유지

Status: REFERENCE-ONLY

<a id="val-008"></a>
## VAL-008

Description: 락커 연장·무기한·마감 직후 재저장·날짜 경고 실제 동작 확인

Why validation is needed: 미검증 UI 경로·날짜 호환·선택 상태 잔존이 있음

How to validate: 운영 DB와 분리된 복제 환경에서 관련 입력과 날짜 경계 확인

Impact if incorrect: 현행 시스템 해석에 남는 불확실성이다. 기존 데이터/계정 이관 및 제외 기능의 호환성을 요구하지 않으므로 이 항목의 미검증 자체는 v1 장애 요인이 아니다. 향후 해당 업무 재검토 시 참고한다.

Related AS-IS Evidence: B08; K17/K23/K28/K40/K41. [위험 목록](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md)

Related product: PD-013–020/023 중 해당 제외·이관 없음 결정; AS-IS 참고만 유지

Status: REFERENCE-ONLY

<a id="val-009"></a>
## VAL-009

Description: 개인 매출등록이 배포본에서 사용되는지와 기존 매출 자료의 출처 확인

Why validation is needed: 저장소에서는 초기화 누락으로 입력·조회 경로가 막힘

How to validate: 배포본 메뉴·트레이너 선택 재현 및 기존 자료 입력 방식 인터뷰

Impact if incorrect: 현행 시스템 해석에 남는 불확실성이다. 기존 데이터/계정 이관 및 제외 기능의 호환성을 요구하지 않으므로 이 항목의 미검증 자체는 v1 장애 요인이 아니다. 향후 해당 업무 재검토 시 참고한다.

Related AS-IS Evidence: B04; K37; verification-report. [위험 목록](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md)

Related product: PD-013–020/023 중 해당 제외·이관 없음 결정; AS-IS 참고만 유지

Status: REFERENCE-ONLY

<a id="val-010"></a>
## VAL-010

Description: 정산 범위·12개월 평균·비활성 트레이너/종류·기본급의 실제 해석 확인

Why validation is needed: 표의 수입은 지급금액이고 운영 해석은 미확인

How to validate: 담당자 정산표와 월/연 화면 표본을 비교

Impact if incorrect: 월 지급액의 업무 의미를 오해할 수 있다. 12개월 평균은 요구하지 않는다. 월 고정 기본급 합산은 최신 TO-BE 결정(PD-012, BR-PAY-014/016)으로 도입했으나 AS-IS 실제 해석 검증을 완료한 것은 아니다. BR-009/012 참고로 사용한다.

Related AS-IS Evidence: F26/F27; R22; K24/K33/K34. [위험 목록](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md)

Related product: PR-010/011; BR-009

Status: OPEN

<a id="val-011"></a>
## VAL-011

Description: 숨겨진 월 복사·직접 상품 선택·Excel·생일 목록·빈 폼의 실제 사용 확인

Why validation is needed: 다른 빌드나 수작업 경로의 존재는 저장소만으로 알 수 없음

How to validate: 버전별 메뉴와 사용 매뉴얼·파일 표본을 담당자와 대조

Impact if incorrect: 현행 시스템 해석에 남는 불확실성이다. 기존 데이터/계정 이관 및 제외 기능의 호환성을 요구하지 않으므로 이 항목의 미검증 자체는 v1 장애 요인이 아니다. 향후 해당 업무 재검토 시 참고한다.

Related AS-IS Evidence: H01–H04; S05/S15; K21/K30/K32. [위험 목록](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md)

Related product: PD-013–020/023 중 해당 제외·이관 없음 결정; AS-IS 참고만 유지

Status: REFERENCE-ONLY

<a id="val-012"></a>
## VAL-012

Description: 계약·예약·출석·결제·환불·회원권·상담이 외부/수기에서 수행되는지 확인

Why validation is needed: 독립 구현 미확인이 실제 업무 부재를 뜻하지 않음

How to validate: 사용 도구·입력 책임·원본 자료·후속 업무를 인터뷰

Impact if incorrect: 전환 시 외부/수기 업무의 책임을 놓칠 수 있다. PD-024의 v1 제외는 유지하며 확인만으로 신규 도메인을 추가하지 않는다.

Related AS-IS Evidence: 02 도메인; 09 연동; 11 운영 질문. [위험 목록](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md)

Related product: PD-024; OPS-001

Status: OPEN

<a id="val-013"></a>
## VAL-013

Description: 기존 계정 암호의 복호화 환경·발급 방식·계정 공유 실태 확인

Why validation is needed: DPAPI 환경 이전과 빈 입력 경로를 운영 검증하지 않음

How to validate: 관리자 입회하에 격리 복제 환경과 계정 발급 기록 점검; 암호 원문 수집 금지

Impact if incorrect: 현행 시스템 해석에 남는 불확실성이다. 기존 데이터/계정 이관 및 제외 기능의 호환성을 요구하지 않으므로 이 항목의 미검증 자체는 v1 장애 요인이 아니다. 향후 해당 업무 재검토 시 참고한다.

Related AS-IS Evidence: 08 인증; K07/K08/K35. [위험 목록](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md)

Related product: PD-013–020/023 중 해당 제외·이관 없음 결정; AS-IS 참고만 유지

Status: REFERENCE-ONLY

<a id="val-014"></a>
## VAL-014

Description: Config 값·SQL 배포 경로·초기화/동기화·백업 관행 확인

Why validation is needed: 설정 유실과 SQL 실행 가능 여부에 따라 파괴 경로가 달라짐

How to validate: 기존 파일·백업·배포 기록을 읽기 전용 점검; 원본에서 초기화 재현 금지

Impact if incorrect: 현행 시스템 해석에 남는 불확실성이다. 기존 데이터/계정 이관 및 제외 기능의 호환성을 요구하지 않으므로 이 항목의 미검증 자체는 v1 장애 요인이 아니다. 향후 해당 업무 재검토 시 참고한다.

Related AS-IS Evidence: 09 연동; K09/K10/K22; verification-report. [위험 목록](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md)

Related product: PD-013–020/023 중 해당 제외·이관 없음 결정; AS-IS 참고만 유지

Status: REFERENCE-ONLY

<a id="val-015"></a>
## VAL-015

Description: 비활성 부모 참조·이름 불일치·센터0·일괄 입력 ID의 데이터 품질 확인

Why validation is needed: 제약 부재·캐시 GymNo·연속 ID 가정의 영향은 미확인

How to validate: 승인된 복제본에서 관계·센터·중복·누락 분포 대사

Impact if incorrect: 현행 시스템 해석에 남는 불확실성이다. 기존 데이터/계정 이관 및 제외 기능의 호환성을 요구하지 않으므로 이 항목의 미검증 자체는 v1 장애 요인이 아니다. 향후 해당 업무 재검토 시 참고한다.

Related AS-IS Evidence: 05 DB; K14/K20/K21/K33/K34. [위험 목록](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md)

Related product: PD-013–020/023 중 해당 제외·이관 없음 결정; AS-IS 참고만 유지

Status: REFERENCE-ONLY

<a id="val-016"></a>
## VAL-016

Description: 현재 사용자 수·자료량·동시 쓰기 주체·업무 지연·중단 허용 관행 확인

Why validation is needed: 현재 loopback 연결을 다중 PC 공유 배포라고 볼 수 없음

How to validate: 운영 인터뷰·자료량 통계·허용된 측정과 다른 입력 도구 조사

Impact if incorrect: AS-IS 규모만으로 Multi-Branch·Trainer 직접 로그인·다중 기기 사용의 성능·복구 목표를 잘못 설정할 수 있다. PD-021/ARCH-004와 OPS-001의 참고다.

Related AS-IS Evidence: 01 개요; K13/K15/K36. [위험 목록](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md)

Related product: PD-021; ARCH-004/OPS-001

Status: OPEN

<a id="val-017"></a>
## VAL-017

Description: 분류 갱신·빈 목록·신용카드만 있는 상태·미선택 입력의 실제 영향 확인

Why validation is needed: 오류 반환과 UI 예외 경로를 실행 검증하지 않음

How to validate: 격리 환경에서 읽기 실패·분류 변경·카드만 존재·미선택을 확인

Impact if incorrect: 현행 시스템 해석에 남는 불확실성이다. 기존 데이터/계정 이관 및 제외 기능의 호환성을 요구하지 않으므로 이 항목의 미검증 자체는 v1 장애 요인이 아니다. 향후 해당 업무 재검토 시 참고한다.

Related AS-IS Evidence: K18/K27/K28/K31/K39; verification-report. [위험 목록](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md)

Related product: PD-013–020/023 중 해당 제외·이관 없음 결정; AS-IS 참고만 유지

Status: REFERENCE-ONLY

<a id="val-018"></a>
## VAL-018

Description: 실제 외부 도구·Excel 형식·하드웨어·알림·파일 보관 관행 확인

Why validation is needed: 코드의 미확인 연동과 업무의 외부 의존은 별개

How to validate: 기존 입출력 파일과 운영 도구 목록을 담당자가 확인

Impact if incorrect: 현행 시스템 해석에 남는 불확실성이다. 기존 데이터/계정 이관 및 제외 기능의 호환성을 요구하지 않으므로 이 항목의 미검증 자체는 v1 장애 요인이 아니다. 향후 해당 업무 재검토 시 참고한다.

Related AS-IS Evidence: 09 연동; H03. [위험 목록](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md)

Related product: PD-013–020/023 중 해당 제외·이관 없음 결정; AS-IS 참고만 유지

Status: REFERENCE-ONLY

<a id="val-019"></a>
## VAL-019

Description: 현재 개인정보 항목의 수집 목적·기존 동의/보존 절차·열람 관행 확인

Why validation is needed: 코드 필드만으로 실제 처리 목적과 조직 절차를 판단할 수 없음

How to validate: 책임자에게 절차·항목·접근 대상을 확인하고 문서에 원문 개인정보는 남기지 않음

Impact if incorrect: 불필요한 개인정보를 새로 수집하거나 열람 범위를 잘못 정할 수 있다. 기존 정보 승계가 아니라 LEGAL-001의 현황 참고다.

Related AS-IS Evidence: F02/F07; 08 인증; K06/K07. [위험 목록](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md)

Related product: PD-022; LEGAL-001

Status: OPEN

<a id="val-020"></a>
## VAL-020

Description: PT 종류/개별률 수정 차단과 수동 보정 관행 확인

Why validation is needed: 자기중복 거부·영향 행 수 무시 때문에 화면 표시와 실제 적용이 다를 수 있음

How to validate: 격리 표본에서 같은 이름/조합 수정 후 저장값 및 운영 우회방법 비교

Impact if incorrect: 기존 결함을 필요한 지급 정책 제약으로 오인할 수 있다. BR-010/011에 필요한 업무 의도를 확인한다.

Related AS-IS Evidence: F12/F15; K16/K20/K38. [위험 목록](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md)

Related product: PR-006/007; BR-010/011

Status: OPEN

## 위험 계승 경계

K01–K41의 AS-IS 결함과 실행/운영 DB 미검증 상태는 원본 [위험 목록](../analysis/11-risks-and-unknowns.md)과 [역검증 보고](../analysis/verification-report.md)에 유지한다. 운영 schema·트리거·DPAPI·Config·기존 ID·락커 값 등을 TO-BE 호환 조건으로 삼지 않는다. 계약·예약 자료를 복원하거나 누락값을 기본값으로 채우는 이관 작업은 없다. 법적 보존 기간 결정은 VAL-019의 현황 확인과 별개인 LEGAL-001이다.

## Product Baseline — 2026-09-17 지점 관계·보상 개정

최신 사용자 확정사항을 반영한 Architecture Input Baseline이다. [현재 결정과 변경 이력](README.md), [권한](users-and-roles.md), [업무 규칙](business-rules.md), [남은 결정 게이트](open-questions.md), [Architecture 인계](architecture-handoff.md)를 함께 따른다. Baseline 갱신은 모든 상세 업무 정책 또는 구현 완료를 뜻하지 않는다.
