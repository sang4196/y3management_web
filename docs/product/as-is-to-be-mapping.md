# AS-IS → TO-BE Mapping

F01–F59 및 H01–H04의 63개 항목을 누락 없이 추적한다. 모든 IN-V1 업무에 PR-030의 Role·Data Scope를 적용하고 실제 관계 정책은 MB-001–008에서 추적한다. 현재 위치와 기능명은 AS-IS이며 TO-BE 화면·데이터 구조가 아니다. 승인된 배제도 매핑에 남긴다. KEEP/REDESIGN/TBD/DROP-CANDIDATE와 v1 포함 여부를 분리한다. TBD는 후속 세부사항 미정이며 승인된 v1 제외를 번복하지 않는다.

| AS-IS 기능 | 현재 위치 | TO-BE 취급 | 상태 / v1 | 근거 | 승인 및 후속사항 |
| --- | --- | --- | --- | --- | --- |
| F01 로그인 | 로그인 | [PR-001](requirements.md#pr-001) 운영 계정과 직무별 접근 | REDESIGN / IN-V1 | [AS-IS F01](../analysis/03-feature-inventory.md) | PD-001/002/003/004/019; ARCH-001/002 |
| F02 신규 회원 등록 | 설정 → 유저관리 | [PR-002](requirements.md#pr-002) 회원 기본정보 관리 | KEEP / IN-V1 | [AS-IS F02](../analysis/03-feature-inventory.md) | PD-006/022; LEGAL-001 |
| F03 회원 개인정보 변경 | 설정 → 유저관리 | [PR-002](requirements.md#pr-002) 회원 기본정보 관리 | KEEP / IN-V1 | [AS-IS F03](../analysis/03-feature-inventory.md) | PD-006/022; LEGAL-001 |
| F04 회원 PT 종류·담당·잔여 횟수 설정/조정 | 설정 → 유저관리 | [PR-003](requirements.md#pr-003) PT Pass 생성·이력·잔여 관리 | REDESIGN / IN-V1 | [AS-IS F04](../analysis/03-feature-inventory.md) | PD-007/008/010/011/022; BR-001/002, ARCH-003 |
| F05 회원 검색·목록 조회 | 설정 → 유저관리 | [PR-002](requirements.md#pr-002) 회원 기본정보 관리 | KEEP / IN-V1 | [AS-IS F05](../analysis/03-feature-inventory.md) | PD-006/022; LEGAL-001 |
| F06 회원 삭제 | 설정 → 유저관리 | [PR-004](requirements.md#pr-004) 업무 데이터 비활성화와 과거 조회 | REDESIGN / IN-V1 | [AS-IS F06](../analysis/03-feature-inventory.md) | PD-010/011/022; BR-001/007, LEGAL-001 |
| F07 트레이너 신규 등록 | 설정 → 유저관리 | [PR-005](requirements.md#pr-005) 트레이너 기본정보 관리 | KEEP / IN-V1 | [AS-IS F07](../analysis/03-feature-inventory.md) | PD-002/006/012/022; BR-009, LEGAL-001 |
| F08 트레이너 정보·기본급 변경 | 설정 → 유저관리 | [PR-005](requirements.md#pr-005) 일반 정보; [PR-007](requirements.md#pr-007) 월 기본급 보상 설정 | REDESIGN / IN-V1 | [AS-IS F08](../analysis/03-feature-inventory.md) | PD-002/006/012/022; BR-009, LEGAL-001 |
| F09 트레이너 목록 조회 | 설정 → 유저관리 | [PR-005](requirements.md#pr-005) 트레이너 기본정보 관리 | KEEP / IN-V1 | [AS-IS F09](../analysis/03-feature-inventory.md) | PD-002/006/012/022; BR-009, LEGAL-001 |
| F10 트레이너 삭제 | 설정 → 유저관리 | [PR-004](requirements.md#pr-004) 업무 데이터 비활성화와 과거 조회 | REDESIGN / IN-V1 | [AS-IS F10](../analysis/03-feature-inventory.md) | PD-010/011/022; BR-001/007, LEGAL-001 |
| F11 PT 종류와 기본 지급단가 등록 | 설정 → 세션관련 | [PR-006](requirements.md#pr-006) PT Product·기준정보 관리 | REDESIGN / IN-V1 | [AS-IS F11](../analysis/03-feature-inventory.md) | PD-001/006/007/009/011; BR-001/011 |
| F12 PT 종류·정산 단가 변경 시도 | 설정 → 세션관련 | [PR-006](requirements.md#pr-006) PT Product·기준정보 관리 | REDESIGN / IN-V1 | [AS-IS F12](../analysis/03-feature-inventory.md) | PD-001/006/007/009/011; BR-001/011 |
| F13 PT 종류 조회·삭제 | 설정 → 세션관련 | [PR-006](requirements.md#pr-006) PT Product·기준정보 관리 | REDESIGN / IN-V1 | [AS-IS F13](../analysis/03-feature-inventory.md) | PD-001/006/007/009/011; BR-001/011 |
| F14 트레이너별 개별 지급률 등록 | 설정 → 세션관련 | [PR-007](requirements.md#pr-007) Trainer Compensation Setting 관리 | REDESIGN / IN-V1 | [AS-IS F14](../analysis/03-feature-inventory.md) | PD-001/009/012/022; BR-PAY-009/010 확정; BR-011 CLOSED; BR-010, ARCH-001 후속 |
| F15 개별 지급률 변경 시도 | 설정 → 세션관련 | [PR-007](requirements.md#pr-007) Trainer Compensation Setting 관리 | REDESIGN / IN-V1 | [AS-IS F15](../analysis/03-feature-inventory.md) | PD-001/009/012/022; BR-PAY-009/010 확정; BR-011 CLOSED; BR-010, ARCH-001 후속 |
| F16 개별 지급률 조회·삭제 | 설정 → 세션관련 | [PR-007](requirements.md#pr-007) Trainer Compensation Setting 관리 | REDESIGN / IN-V1 | [AS-IS F16](../analysis/03-feature-inventory.md) | PD-001/009/012/022; BR-PAY-009/010 확정; BR-011 CLOSED; BR-010, ARCH-001 후속 |
| F17 진행 대상 회원 검색·선택 | 세션정산 → 세션진행 등록 | [PR-008](requirements.md#pr-008) 실제 진행일별 개별 PT Session | REDESIGN / IN-V1 | [AS-IS F17](../analysis/03-feature-inventory.md) | PD-007/008/009/010/012/022; BR-002/008/010/011, UX-001 |
| F18 PT 진행 기록 및 잔여 횟수 차감 | 세션정산 → 세션진행 등록 | [PR-008](requirements.md#pr-008) 실제 진행일별 개별 PT Session | REDESIGN / IN-V1 | [AS-IS F18](../analysis/03-feature-inventory.md) | PD-007/008/009/010/012/022; BR-002/008/010/011, UX-001 |
| F19 트레이너별 월 진행 내역 조회 | 세션정산 → 세션진행 등록 | [PR-008](requirements.md#pr-008) 실제 진행일별 개별 PT Session | REDESIGN / IN-V1 | [AS-IS F19](../analysis/03-feature-inventory.md) | PD-007/008/009/010/012/022; BR-002/008/010/011, UX-001 |
| F20 기존 진행 기록 수정 시도 | 세션정산 → 세션진행 등록 | [PR-009](requirements.md#pr-009) 제한된 권한의 Session 정정·취소 | REDESIGN / IN-V1 | [AS-IS F20](../analysis/03-feature-inventory.md) | PD-010/011/012/022; BR-007, ARCH-001 |
| F21 진행 기록 삭제 및 선택적 횟수 복원 | 세션정산 → 세션진행 등록 | [PR-009](requirements.md#pr-009) 제한된 권한의 Session 정정·취소 | REDESIGN / IN-V1 | [AS-IS F21](../analysis/03-feature-inventory.md) | PD-010/011/012/022; BR-007, ARCH-001 |
| F22 트레이너 매출 신규 기록 | 세션정산 → 개인 매출등록 | [PR-012](requirements.md#pr-012) 수동 트레이너 매출 | TBD / OUT-V1 | [AS-IS F22](../analysis/03-feature-inventory.md); K37 기본 경로 차단 | PD-006/013/017; 현재 구현 TODO 없음 |
| F23 트레이너 매출 수정 | 세션정산 → 개인 매출등록 | [PR-012](requirements.md#pr-012) 수동 트레이너 매출 | TBD / OUT-V1 | [AS-IS F23](../analysis/03-feature-inventory.md); K37 기본 경로 차단 | PD-006/013/017; 현재 구현 TODO 없음 |
| F24 트레이너 매출 삭제 | 세션정산 → 개인 매출등록 | [PR-012](requirements.md#pr-012) 수동 트레이너 매출 | TBD / OUT-V1 | [AS-IS F24](../analysis/03-feature-inventory.md); K37 기본 경로 차단 | PD-006/013/017; 현재 구현 TODO 없음 |
| F25 트레이너 월 매출 조회 | 세션정산 → 개인 매출등록 | [PR-012](requirements.md#pr-012) 수동 트레이너 매출 | TBD / OUT-V1 | [AS-IS F25](../analysis/03-feature-inventory.md); K37 기본 경로 차단 | PD-006/013/017; 현재 구현 TODO 없음 |
| F26 당월·지정 월 범위 세션 정산 조회 | 세션정산 → 세션현황 | [PR-010](requirements.md#pr-010) 기본급·Session·추가실적 월별 트레이너 정산 | REDESIGN / IN-V1 | [AS-IS F26](../analysis/03-feature-inventory.md) | PD-009/010/011/012/013; BR-007/008/009/010/011 |
| F27 연간 월별 수업수·지급액·매출 조회 | 세션정산 → 세션현황 | [PR-011](requirements.md#pr-011) 추가 연간 통계 검토 | TBD / OUT-V1 | [AS-IS F27](../analysis/03-feature-inventory.md) | PD-006/012; I4(v1 보류); BR-009 남은 정산 상세 |
| F28 회원/트레이너에게 락커 배정 | 메인 → 락커 설정 | [PR-013](requirements.md#pr-013) 락커 운영 | TBD / OUT-V1 | [AS-IS F28](../analysis/03-feature-inventory.md) | PD-006/016; 현재 구현 TODO 없음 |
| F29 락커 기간 변경·연장 시도 | 메인 → 락커 설정 | [PR-013](requirements.md#pr-013) 락커 운영 | TBD / OUT-V1 | [AS-IS F29](../analysis/03-feature-inventory.md) | PD-006/016; 현재 구현 TODO 없음 |
| F30 락커 무기한 설정 | 메인 → 락커 설정 | [PR-013](requirements.md#pr-013) 락커 운영 | TBD / OUT-V1 | [AS-IS F30](../analysis/03-feature-inventory.md) | PD-006/016; 현재 구현 TODO 없음 |
| F31 락커 사용마감 | 메인 → 락커 설정 | [PR-013](requirements.md#pr-013) 락커 운영 | TBD / OUT-V1 | [AS-IS F31](../analysis/03-feature-inventory.md) | PD-006/016; 현재 구현 TODO 없음 |
| F32 락커 소유자 검색·선택 | 락커 설정 → 회원/트레이너 선택 | [PR-013](requirements.md#pr-013) 락커 운영 | TBD / OUT-V1 | [AS-IS F32](../analysis/03-feature-inventory.md) | PD-006/016; 현재 구현 TODO 없음 |
| F33 락커 현황·만료 상태 조회 | 메인화면 | [PR-013](requirements.md#pr-013) 락커 운영 | TBD / OUT-V1 | [AS-IS F33](../analysis/03-feature-inventory.md) | PD-006/016; 현재 구현 TODO 없음 |
| F34 락커 번호·소유자 글꼴 크기 조절 | 메인화면 | [PR-014](requirements.md#pr-014) 락커 글꼴 조절 | DROP-CANDIDATE / OUT-V1 | [AS-IS F34](../analysis/03-feature-inventory.md) | PD-005/016/023; 실제 필요 확인 시 후속 검토 |
| F35 업무 메뉴 이동·메인 복귀 | 메인화면 | [PR-015](requirements.md#pr-015) Responsive Web에서 핵심 업무 이동 | REDESIGN / IN-V1 | [AS-IS F35](../analysis/03-feature-inventory.md) | PD-001/005/006/007/008; ARCH-004, UX-001 |
| F36 창 최소화·이동·프로그램 종료 | 메인화면 | [PR-016](requirements.md#pr-016) 데스크톱 창 조작·종료 | DROP-CANDIDATE / NOT-COMMITTED | [AS-IS F36](../analysis/03-feature-inventory.md) | PD-019/023; 실제 필요 확인 시 후속 검토 |
| F37 가계부 월 거래 조회 | 가계부 → 내역 | [PR-017](requirements.md#pr-017) 가계부 거래·자산·분류 | TBD / OUT-V1 | [AS-IS F37](../analysis/03-feature-inventory.md) | PD-006/014/017; 후속 Product Expansion |
| F38 수입 장부 기록·자산 반영 | 가계부 → 내역 | [PR-017](requirements.md#pr-017) 가계부 거래·자산·분류 | TBD / OUT-V1 | [AS-IS F38](../analysis/03-feature-inventory.md) | PD-006/014/017; 후속 Product Expansion |
| F39 지출 장부 기록·자산 반영 | 가계부 → 내역 | [PR-017](requirements.md#pr-017) 가계부 거래·자산·분류 | TBD / OUT-V1 | [AS-IS F39](../analysis/03-feature-inventory.md) | PD-006/014/017; 후속 Product Expansion |
| F40 자산 간 이체 기록 | 가계부 → 내역 | [PR-017](requirements.md#pr-017) 가계부 거래·자산·분류 | TBD / OUT-V1 | [AS-IS F40](../analysis/03-feature-inventory.md) | PD-006/014/017; 후속 Product Expansion |
| F41 기존 거래 수정과 잔액 재반영 | 가계부 → 내역 | [PR-017](requirements.md#pr-017) 가계부 거래·자산·분류 | TBD / OUT-V1 | [AS-IS F41](../analysis/03-feature-inventory.md) | PD-006/014/017; 후속 Product Expansion |
| F42 거래 삭제와 잔액 역처리 | 가계부 → 내역 | [PR-017](requirements.md#pr-017) 가계부 거래·자산·분류 | TBD / OUT-V1 | [AS-IS F42](../analysis/03-feature-inventory.md) | PD-006/014/017; 후속 Product Expansion |
| F43 자산 신규 등록 | 가계부 → 설정 | [PR-017](requirements.md#pr-017) 가계부 거래·자산·분류 | TBD / OUT-V1 | [AS-IS F43](../analysis/03-feature-inventory.md) | PD-006/014/017; 후속 Product Expansion |
| F44 자산 이름·유형·잔액 직접 변경 | 가계부 → 설정 | [PR-017](requirements.md#pr-017) 가계부 거래·자산·분류 | TBD / OUT-V1 | [AS-IS F44](../analysis/03-feature-inventory.md) | PD-006/014/017; 후속 Product Expansion |
| F45 자산 목록 조회·삭제 | 가계부 → 설정 | [PR-017](requirements.md#pr-017) 가계부 거래·자산·분류 | TBD / OUT-V1 | [AS-IS F45](../analysis/03-feature-inventory.md) | PD-006/014/017; 후속 Product Expansion |
| F46 거래 분류 신규 등록 | 가계부 → 설정 | [PR-017](requirements.md#pr-017) 가계부 거래·자산·분류 | TBD / OUT-V1 | [AS-IS F46](../analysis/03-feature-inventory.md) | PD-006/014/017; 후속 Product Expansion |
| F47 거래 분류 변경 | 가계부 → 설정 | [PR-017](requirements.md#pr-017) 가계부 거래·자산·분류 | TBD / OUT-V1 | [AS-IS F47](../analysis/03-feature-inventory.md) | PD-006/014/017; 후속 Product Expansion |
| F48 거래 분류 목록 조회·삭제 | 가계부 → 설정 | [PR-017](requirements.md#pr-017) 가계부 거래·자산·분류 | TBD / OUT-V1 | [AS-IS F48](../analysis/03-feature-inventory.md) | PD-006/014/017; 후속 Product Expansion |
| F49 고정 수입·지출 설정 등록 | 가계부 → 설정 | [PR-018](requirements.md#pr-018) 고정 거래 | TBD / OUT-V1 | [AS-IS F49](../analysis/03-feature-inventory.md) | PD-006/014/015; 후속 가계부 채택 전까지 보류 |
| F50 고정 수입·지출 설정 변경 | 가계부 → 설정 | [PR-018](requirements.md#pr-018) 고정 거래 | TBD / OUT-V1 | [AS-IS F50](../analysis/03-feature-inventory.md) | PD-006/014/015; 후속 가계부 채택 전까지 보류 |
| F51 고정 거래 목록 조회·중단 | 가계부 → 설정 | [PR-018](requirements.md#pr-018) 고정 거래 | TBD / OUT-V1 | [AS-IS F51](../analysis/03-feature-inventory.md) | PD-006/014/015; 후속 가계부 채택 전까지 보류 |
| F52 자산·부채·순자산과 차트 조회 | 가계부 → 통계 | [PR-019](requirements.md#pr-019) 가계부 자산·부채·순자산 통계 | TBD / OUT-V1 | [AS-IS F52](../analysis/03-feature-inventory.md) | PD-014; 후속 Product Expansion |
| F53 고정 수입·지출 장부 자동 생성 | 로그인 성공 직후 자동 처리 | [PR-018](requirements.md#pr-018) 고정 거래 | TBD / OUT-V1 | [AS-IS F53](../analysis/03-feature-inventory.md) | PD-006/014/015; 후속 가계부 채택 전까지 보류 |
| F54 센터 신규 등록 | 어드민설정 → 어드민관리 | [PR-020](requirements.md#pr-020) Organization / Branch 관리 | REDESIGN / IN-V1 | [AS-IS F54](../analysis/03-feature-inventory.md) | PD-004/006; MB-001–008; 활성/비활성 세부는 MB-008 |
| F55 센터 이름 변경 | 어드민설정 → 어드민관리 | [PR-020](requirements.md#pr-020) Branch 정보 관리; [PR-028](requirements.md#pr-028) 신규 준비 | REDESIGN / IN-V1 | [AS-IS F55](../analysis/03-feature-inventory.md) | PD-004/017/018/019; MB-004, OPS-001 |
| F56 센터 조회·비활성화 | 어드민설정 → 어드민관리 | [PR-020](requirements.md#pr-020) Organization / Branch 관리 | REDESIGN / IN-V1 | [AS-IS F56](../analysis/03-feature-inventory.md) | PD-004/006; MB-001–008; 활성/비활성 세부는 MB-008 |
| F57 운영 계정 신규 등록 | 어드민설정 → 어드민관리 | [PR-021](requirements.md#pr-021) 관리자 발급 운영 계정·권한 관리 | REDESIGN / IN-V1 | [AS-IS F57](../analysis/03-feature-inventory.md) | PD-001/019/022; ARCH-001/002 |
| F58 운영 계정 센터·암호 변경 | 어드민설정 → 어드민관리 | [PR-021](requirements.md#pr-021) 관리자 발급 운영 계정·권한 관리 | REDESIGN / IN-V1 | [AS-IS F58](../analysis/03-feature-inventory.md) | PD-001/019/022; ARCH-001/002 |
| F59 계정 조회·비활성화 | 어드민설정 → 어드민관리 | [PR-021](requirements.md#pr-021) 관리자 발급 운영 계정·권한 관리 | REDESIGN / IN-V1 | [AS-IS F59](../analysis/03-feature-inventory.md) | PD-001/019/022; ARCH-001/002 |
| H01 이전 월 세션 복사 — 숨김 | frmSessionRegister 숨김 불러오기 | [PR-022](requirements.md#pr-022) 숨김 월 복사·상품 직접 선택 | DROP-CANDIDATE / NOT-COMMITTED | [AS-IS H01](../analysis/03-feature-inventory.md); 숨김/미연결 | PD-008/023; UX-001과 별개; 후속 필요 확인 |
| H02 진행 등록에서 상품 직접 선택 — 숨김 | frmSessionRegister 숨김 상품 목록 | [PR-022](requirements.md#pr-022) 숨김 월 복사·상품 직접 선택 | DROP-CANDIDATE / NOT-COMMITTED | [AS-IS H02](../analysis/03-feature-inventory.md); 숨김/미연결 | PD-008/023; UX-001과 별개; 후속 필요 확인 |
| H03 Excel 회원·락커 가져오기 — 호출 미확인 | frmMain.ReadExcelData 호출 미확인 | [PR-023](requirements.md#pr-023) 기존 Excel 가져오기·migration tooling | DROP-CANDIDATE / OUT-V1 | [AS-IS H03](../analysis/03-feature-inventory.md); 숨김/미연결 | PD-017/020/023; 현재 이관 TODO 없음 |
| H04 생일 목록 보조 메서드 — 호출 미확인 | ModelList 생일 목록 호출 미확인 | [PR-024](requirements.md#pr-024) 미연결 생일 목록 | DROP-CANDIDATE / OUT-V1 | [AS-IS H04](../analysis/03-feature-inventory.md); 숨김/미연결 | PD-022/023; I2 생년월일 v1 제외 |

## AS-IS 개별 기능 밖의 추적

| AS-IS/출처 | TO-BE 취급 | 근거 |
| --- | --- | --- |
| 빈 기타설정·급여 팝업 S05/S15 | PR-025 DROP-CANDIDATE; 존재만으로 구현하지 않음 | PD-023; [화면](../analysis/04-screen-inventory.md) |
| 초기 계정 생성·로컬 설정 | PR-021/028: Master Admin·필요 기준정보를 새로 설정. 고정 자격증명·Config 복사 없음 | PD-017/019; [연동](../analysis/09-external-integrations.md) |
| DB 초기화·버전 SQL·DB 직접 연결 | 보존할 호환 기능이 아님. 운영 데이터 보호·복구의 참고 위험 | PD-017/021; [위험](../analysis/11-risks-and-unknowns.md) K09/K10/K22 |
| DPAPI·user32·프로세스 실행 제한 | 기존 환경/기술을 요구하지 않음. 웹 접근 정책 PR-001/026으로 구분 | PD-019/023; [개요](../analysis/01-system-overview.md) |
| S01/S03/S04/S06/S08/S12의 업무 | PR-001–010/015/021/028로 의미 재정의. 폼 배치 복제 없음 | [화면](../analysis/04-screen-inventory.md), PD-006–012 |
| 메인 S02의 락커/C01, S07/S09–S11/S13/S14 | 락커·매출·가계부 부분 OUT-V1; S02 메뉴 이동만 PR-015 | PD-006/013/014/016 |
| AS-IS에 없는 명시적 PT Pass | APPROVED-TO-BE PR-003 | PD-007 |
| AS-IS 월별 다회 기록에서 날짜별 개별 Session으로 변경 | APPROVED-TO-BE PR-008 | PD-008 |
| Product Payment Type / Trainer Compensation Setting 분리 | APPROVED-TO-BE PR-006/007 | PD-001/009; BR-PAY-001–005 |
| FIXED_AMOUNT Pass 우선 소비·동일 Payment Type FIFO | APPROVED-TO-BE PR-003/008 | BR-PAY-006 |
| 수행 Trainer의 Session Payment와 과거 확정 결과 보존 | APPROVED-TO-BE PR-008/010 | BR-PAY-007/008/009 |
| 기본급·Session Payment·추가실적 월 정산·과거 확정 결과 보존 | APPROVED-TO-BE PR-004/010 | PD-010/011/012 |
| 세 보상 설정의 Master/해당 Home Branch Admin 권한 및 Actor 권한·Branch Context 포함 감사 | APPROVED-TO-BE PR-007/027 | BR-PAY-010 |
| 중요 행위 감사·직무 권한 | APPROVED-TO-BE PR-001/027 | PD-001/022 |
| 실운영·Organization/Branch·빈 데이터·일괄 전환 | APPROVED-TO-BE PR-028; migration 없음 | PD-004/006/017/018 |
| Member 로그인/Self-Service·Schedule/Reservation | 명시적 Future Scope / OUT-V1 | PD-003/025 |
| Trainer 직접 로그인·자신의 실제 Session 등록/조회 | APPROVED-TO-BE PR-001/008/029 / IN-V1 | PD-002/006 |
| Organization/Branch·Role/Data Scope·Backend Branch 접근 제한 | APPROVED-TO-BE PR-020/030 / IN-V1 | PD-001/004 |
| Desktop/Tablet/Smartphone 및 현장 Trainer Workflow | APPROVED-TO-BE PR-015/029 / IN-V1 | PD-005 |
| Mobile App / 특정 UI Client 종속 방지 | Future Direction / OUT-V1; NFR-013 제약 | PD-026 |

## Product Baseline — 2026-09-17 지점 관계·보상 개정

최신 사용자 확정사항을 반영한 Architecture Input Baseline이다. [현재 결정과 변경 이력](README.md), [권한](users-and-roles.md), [업무 규칙](business-rules.md), [남은 결정 게이트](open-questions.md), [Architecture 인계](architecture-handoff.md)를 함께 따른다. Baseline 갱신은 모든 상세 업무 정책 또는 구현 완료를 뜻하지 않는다.

## 최신 사용자 결정의 별도 추적

| 출처 | TO-BE | 경계 |
| --- | --- | --- |
| 사용자 확정 지점 관계 | PR-002/003/005/006/008/020/030; BR-OPS-001 | 단일 Home/Issued Branch, 실제 Performed Branch, 공통 Catalog; 교차 조건은 OPEN |
| 사용자 확정 월 기본급 | PR-007/010; BR-PAY-014/016 | AS-IS F08/VAL-010은 참고이며 현재 운영 검증 완료가 아님 |
| 사용자 확정 추가실적 | PR-031; PD-027; BR-PAY-015 | Session 유무 모두 가능. F22–25 수동 매출과 동일하다는 AS-IS 사실을 만들지 않음 |

수동 매출 PR-012는 계속 OUT-V1이다. 추가실적 관리자 직접 등록 역할·Home Branch 대상 기준·Branch Admin의 본인이 아닌 소속 Trainer 직접 등록 시 별도 Master 승인 없음·관리 범위 안 본인 직접 등록 및 해당 본인 건 별도 승인 없음·타 지점 지원 수업 금액의 관리자 건별 수동 입력·진행 기록/차감 후 금액 저장 시 보상 확정·미입력과 확정 0원 구분 및 추적·미입력 지원 수업이 남은 해당 Trainer·월 정산 확정 차단은 확정했다. 타 지점 지원 수업 보상은 권한 있는 관리자가 사유를 기록하면 0원으로 명시적으로 확정할 수 있다. 사유 없는 0원 입력은 보상 확정이 불가하다. 사유를 남기고 확정한 0원은 금액 미입력이 아니므로 그 건으로 월 정산 확정을 차단하지 않는다. 다른 미입력 건이 남으면 기존 차단 조건을 유지한다. 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin에게 Organization 전체, Branch Admin에게 대상 Trainer Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안의 본인 건도 허용하고 변경 이력을 남긴다. 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin·Branch Admin 모두 관리 범위 안에서 본인 건을 포함해 별도 승인 없이 저장 성공 즉시 반영한다. Master나 다른 관리자의 승인 대기를 두지 않으며 권한 검증과 변경 이력을 유지한다. 월 정산 확정 전 지원 수업 보상 금액의 모든 수정에는 변경 사유가 필수다. 양수 간 변경·0원에서 양수로 변경·양수에서 0원으로 변경 모두 적용하며, 사유 없이는 금액을 수정할 수 없다. 변경 전후 금액·변경 사유·수정자·수정 시점을 이력으로 남긴다. 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer의 지원 수업 보상 정정을 위해 월 정산을 확정 해제·재확정할 때는 Master의 별도 승인을 두지 않는다. Master 승인 대기 단계 없이 관리 범위 안에서 직접 처리하며 이전 확정본과 해제·재확정 이력 및 감사를 유지한다. 지원 수업 보상 정정의 월 정산 확정 해제에는 사유가 필수이며, 사유 없이 해제할 수 없다. 사유·해제자·시점을 이력으로 남긴다. 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 남은 정정·취소 절차는 BR-009/013 등 관련 OPEN을 따른다. AS-IS 확인 결과가 아닌 후속 사용자 결정이다. 지원 수업 외 추가실적의 남은 입력 제약·금액 미입력 건의 추적 표현·정정 연동·연계 상세·정정 등 BR-013의 나머지 정책은 미결정이다. BR-011은 발급 당시 상품 조건 유지로 CLOSED 처리했으며 표의 BR-011 참조는 해결된 TO-BE 정책 추적이다. 타 지점 지급 구성 MB-009는 2026-10-10 사용자 결정으로 해당 수업의 보상 전체를 Additional Performance로 처리하는 방식으로 확정했다. AS-IS 사실을 새로 검증한 것은 아니다.

2026-10-12 I1–I4=1: 시작 날짜/시각 확인 후 수업별 개별 등록·여러 날짜 일괄 입력 v1 보류(UX-001 CLOSED), 이름/전화번호/Home Branch 필수·생년월일/성별 제외, 추가 연간 통계 후속 보류를 반영했다. F27과 H04는 현재 v1 제외이며 기존 월 정산/이미 승인된 Master 전용 지점 비용 보고서·Responsive Web은 유지한다. AS-IS 기능 존재/미연결 코드로 제외 기능을 구현하지 않는다. [2026-10-12 I 일괄 승인](product-decisions.md#review-20261012-i-batch).
