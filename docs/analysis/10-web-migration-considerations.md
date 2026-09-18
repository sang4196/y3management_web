# 10. 웹 전환 관점의 현재 구조 분석

이 문서는 현재 구현의 이식 제약을 분류한다. 새 프레임워크 선정·구현안·새 기능 명세는 포함하지 않는다. 페이지/API 분리 항목은 **추정: 향후 책임 경계 후보**이며 현재 웹 기능이 아니다.

| 분류 | 현재 사실과 영향 | 근거 |
| --- | --- | --- |
| 재사용 가능한 비즈니스 개념 | 센터·회원·담당 트레이너·PT 종류·개별 지급률·일반/서비스 잔여 횟수·진행 기록·수동 매출·락커·가계부는 명확한 개념이다. 개념을 재사용할 수 있다는 뜻이며 기존 클래스를 그대로 재사용할 수 있다는 뜻은 아님 | [02](02-domain-model.md), `Models` |
| 재설계 판단 필요 | 현재 상품/잔여를 User에 덮어쓰며 계약·횟수 변경 이력 없음. 복수 계약·결제 흐름은 기존 사실로 정의할 수 없음 | `User`, `frmSettingUser.UpdateUser` |
| 재설계 판단 필요 | 가계부 거래·잔액, 진행 세션·횟수의 원자성 없음. 이체 받는 계좌 저장 누락 경로 존재 | `frmFinanceInput.UpdateAccount`, `frmSessionRegister.UpdateSession` |
| UI 강결합 | 필수값·중복 검사, 금액 계산, 횟수 분할, 거래 역처리, 정산 집계가 Form 메서드에 존재 | `frmSettingSession.UpdateST`, `frmSessionStats.LoadMonthlyData`, `frmFinanceInput.UpdateTransaction` |
| UI 강결합 | 모델 목록이 ComboBox를 채우고 Save가 MessageBox를 띄움. 고정 거래가 폼을 통해 잔액 처리 | `ModelList.*.SetCombo/Save`, `Core.CheckFixedTransaction` |
| DB 강결합 | 엔티티가 SQL 문자열을 반환하고 전역 로그인 GymNo를 참조. 테이블별 UPDATE JOIN, UNION ALL, MySQL LAST INSERT ID에 의존 | `GetQueryParam`, `DB*.GetMultiSaveQuery`, `MariaDB.MultiSave` |
| DB 강결합 | FK 없는 다형 owner_id, 이체 category_id의 이중 의미, 명칭 중복 저장, 논리삭제 | `QueryString`, `CreateTable.sql` |
| 데스크톱 의존 | WinForms 이벤트, 모달 팝업, Panel 자식 폼, 그리드/DataTable, 로컬 시간과 글꼴 설정 | `frmMain.openChildForm`, `UCLocker`, `TimeUtil` |
| 데스크톱 의존 | DPAPI CurrentUser, C 드라이브 고정 경로, user32.dll, Excel COM, 프로세스 종료 | `Secure`, `Core`, `frmMain.ReadExcelData`, `Program` |
| 전역 상태 | 현재 계정·센터·모델·폼이 싱글턴 하나에 있음. 여러 웹 사용자 요청을 같은 상태에 넣을 수 없음 | `Core`, `Singleton<T>`, `ModelList` |
| 실행 수명 의존 | 로그인할 때만 고정 거래 처리. 서버 지속 실행 시 동일 트리거 의미가 없음 | `frmLock.Login`, `FixedTransaction.CheckLastInputDate` |
| 인증/권한 경계 | 특정 ID/센터일 때 메뉴 표시, 계정 전체 선로딩, 금융 SQL의 센터 필터 불일치 | [08](08-auth-and-permissions.md) |

## API로 분리해야 할 책임 후보 — 추정

| 현재 화면/호출 | 웹에서 독립 요청 처리가 필요한 업무 단위 | 현재 의미를 확인할 지점 |
| --- | --- | --- |
| frmLock.Login | 인증 및 현재 센터 식별 | DPAPI 기존 암호, 초기 계정, 관리자 정의 |
| frmSettingUser | 회원/트레이너 검색·등록·상태 변경·PT 잔여 조정 | 계약으로 확장할지와 무관하게 현재는 직접 조정 |
| frmSettingSession | 종류·단가·개별 지급률 관리 및 지급단가 계산 | 중복 검사의 수정 차단 버그와 소수 처리 |
| frmSessionRegister | 진행 기록과 횟수 반영/복원 | 수정 시 횟수 재계산, 혼합 기록 금액, 숨겨진 복사 |
| frmTrainerSales / frmSessionStats | 수동 매출 입력 / 월·연 정산 조회 | 고객 결제와 수업 지급금액의 구별 |
| popLocker | 현재 락커 배정·마감·기간 관리 | 소유자 유형 충돌, 연장 차단, 만료는 강조만 |
| frmFinanceInput | 거래 입력·수정·삭제와 자산 잔액 반영 | 수입·지출·이체, 신용카드 부호 |
| Core.CheckFixedTransaction | 고정 거래 대상 판정·장부 반영 | 현재 날짜 조건은 월 반복을 보장하지 않음 |
| FrmAdminRegister | 센터·계정 관리 | UI 표시와 데이터 접근 권한의 차이 |

## 데이터 이관에서 현재 확인할 수 없는 사항

운영 DB가 DDL과 같은지, owner_type에 어떤 값이 실제로 저장되어 있는지, 비활성 부모를 참조하는 활성 데이터가 얼마나 있는지, 장부 잔액과 거래 합계가 일치하는지, 기존 DPAPI 암호를 복호화할 환경이 있는지 확인이 필요하다. 현재 코드에 없는 계약/예약/결제를 기존 데이터로 복원할 수 있다고 단정할 수 없다. 상세 질문은 [11](11-risks-and-unknowns.md)에 있다.

## 역검증에 따른 해석 제한

매출 도메인과 저장 처리기는 존재하지만 현재 입력 화면은 초기화 누락으로 막혀 있다. 따라서 위의 매출 API 분리 항목은 개념·처리기 책임에 대한 추정이며 기존에 정상 운영된 입력 절차라는 근거가 아니다(Core.InitForm, frmTrainerSales.InitComboEvent). DB Save의 true와 실제 변경 행 수, 분류 갱신 이벤트의 구독 유무도 현재 동작을 설명할 때 구분해야 한다(MariaDB.Save, frmFinanceInput.InitComboEvent).
