# 04. 화면 목록

Form 클래스 15개와 재사용 UserControl 1개를 확인했다. 활성 화면·빈 화면·숨김/미연결을 구분한다. 운영자는 로그인 Admin 사용자를 뜻하며 직책 해석은 추정이다. 웹 페이지 분리 가능성은 모두 **추정**이다. 화면/버튼 명칭은 frmMain.Designer 및 각 Designer, 이벤트 연결은 각 Form의 InitEvent를 근거로 한다. 실행 화면 캡처를 확인한 것은 아니다.

## S01. 로그인

| 항목 | 내용 |
| --- | --- |
| 화면명 / 클래스 | 로그인 / frmLock |
| 상태 | 활성 |
| 목적 | 센터와 계정을 확인하여 프로그램 접근을 시작 |
| 진입 | 프로그램 시작 |
| 사용자 | 비로그인 사용자 |
| 주요 입력 항목 | 센터, ID, 비밀번호 |
| 주요 조회 항목 | 활성 센터, 마지막 ID/센터 |
| 주요 버튼/액션 | 로그인, Enter, 종료 |
| 호출되는 로직 | Login, CheckAdmin, SetLastInfo |
| 관련 코드 | [Forms/frmLock.cs](../../Y3/Y3/Forms/frmLock.cs) — Login(89행), CheckAdmin(44행), SetLastInfo(38행) |
| 디자인 코드 | [frmLock Designer](../../Y3/Y3/Forms/frmLock.Designer.cs) |
| 웹 분리 가능성 — 추정 | 인증 진입 화면 1개 |

## S02. 메인·락커 현황

| 항목 | 내용 |
| --- | --- |
| 화면명 / 클래스 | 메인·락커 현황 / frmMain |
| 상태 | 활성 |
| 목적 | 업무 메뉴 이동과 락커 현재 배정·만료 상태 확인 |
| 진입 | 로그인 성공 / 메인화면 |
| 사용자 | 로그인 운영자 |
| 주요 입력 항목 | 락커 타일 선택, 번호/소유자 글꼴 크기 |
| 주요 조회 항목 | 센터명, 락커 번호·소유자·기간·상태색, 버전 |
| 주요 버튼/액션 | 메뉴 이동, 락커 열기, 글꼴 ±, 최소화, 창 이동, 종료 |
| 호출되는 로직 | MakeLocker, SetLockerColor, BtnSub_Click, BtnLockerFont_Click |
| 관련 코드 | [Forms/frmMain.cs](../../Y3/Y3/Forms/frmMain.cs) — MakeLocker(450행), SetLockerColor(499행), BtnSub_Click(172행), BtnLockerFont_Click(132행) |
| 디자인 코드 | [frmMain Designer](../../Y3/Y3/Forms/frmMain.Designer.cs) |
| 웹 분리 가능성 — 추정 | 메인 현황과 공통 메뉴 영역 분리 가능 |

## S03. 유저관리

| 항목 | 내용 |
| --- | --- |
| 화면명 / 클래스 | 유저관리 / frmSettingUser |
| 상태 | 활성 |
| 목적 | 회원의 현재 PT 이용정보와 트레이너 기본정보 관리 |
| 진입 | 설정 → 유저관리 |
| 사용자 | 로그인 운영자 |
| 주요 입력 항목 | 회원 이름·생일·전화·없음 체크·상품·일반/서비스 잔여·담당·메모; 트레이너 이름·생일·전화·없음 체크·기본급·메모; 회원 검색 |
| 주요 조회 항목 | 회원 및 트레이너 목록, 회원 잔여·종류·담당, 락커 조회값 |
| 주요 버튼/액션 | 등록(신규/수정), 삭제, 초기화, 행 더블클릭, 회원 검색 |
| 호출되는 로직 | UpdateUser, UpdateTrainer, DeleteUser, DeleteTrainer, LoadUserData |
| 관련 코드 | [Forms/Setting/frmSettingUser.cs](../../Y3/Y3/Forms/Setting/frmSettingUser.cs) — UpdateUser(371행), UpdateTrainer(422행), DeleteUser(464행), DeleteTrainer(485행), LoadUserData(333행) |
| 디자인 코드 | [frmSettingUser Designer](../../Y3/Y3/Forms/Setting/frmSettingUser.Designer.cs) |
| 웹 분리 가능성 — 추정 | 회원 목록/상세·PT정보와 트레이너 관리 분리 가능 |

## S04. 세션관련 설정

| 항목 | 내용 |
| --- | --- |
| 화면명 / 클래스 | 세션관련 설정 / frmSettingSession |
| 상태 | 활성 |
| 목적 | PT 종류별 기본 단가와 트레이너별 개별 지급률 관리 |
| 진입 | 설정 → 세션관련 |
| 사용자 | 로그인 운영자 |
| 주요 입력 항목 | 종류 이름·가격·지급률·공제율; 종류·트레이너·개별 지급률 |
| 주요 조회 항목 | 종류별 지급단가, 개별 지급률 목록 |
| 주요 버튼/액션 | 각 등록(신규/수정), 삭제, 초기화, 행 더블클릭 |
| 호출되는 로직 | UpdateSessionPrice, UpdateST, DeleteSessionPrice, DeleteST, TxtPrice_KeyUp |
| 관련 코드 | [Forms/Setting/frmSettingSession.cs](../../Y3/Y3/Forms/Setting/frmSettingSession.cs) — UpdateSessionPrice(261행), UpdateST(313행), DeleteSessionPrice(354행), DeleteST(376행), TxtPrice_KeyUp(155행) |
| 디자인 코드 | [frmSettingSession Designer](../../Y3/Y3/Forms/Setting/frmSettingSession.Designer.cs) |
| 웹 분리 가능성 — 추정 | PT 종류와 개별 정산 조건을 별도 페이지/탭으로 분리 가능 |

## S05. 기타설정

| 항목 | 내용 |
| --- | --- |
| 화면명 / 클래스 | 기타설정 / frmSettingETC |
| 상태 | 빈 화면 |
| 목적 | 화면 틀만 존재 |
| 진입 | 설정 → 기타설정 |
| 사용자 | 로그인 운영자 |
| 주요 입력 항목 | 없음 |
| 주요 조회 항목 | 없음 |
| 주요 버튼/액션 | 없음 |
| 호출되는 로직 | frmSettingETC |
| 관련 코드 | [Forms/Setting/frmSettingETC.cs](../../Y3/Y3/Forms/Setting/frmSettingETC.cs) — frmSettingETC(18행) |
| 디자인 코드 | [frmSettingETC Designer](../../Y3/Y3/Forms/Setting/frmSettingETC.Designer.cs) |
| 웹 분리 가능성 — 추정 | 현재 업무가 없어 독립 페이지 근거 없음 |

## S06. 세션진행 등록

| 항목 | 내용 |
| --- | --- |
| 화면명 / 클래스 | 세션진행 등록 / frmSessionRegister |
| 상태 | 활성, 일부 숨김 |
| 목적 | 진행한 수업 횟수·지급액 기록 및 회원 잔여 차감/복원 |
| 진입 | 세션정산 → 세션진행 등록 |
| 사용자 | 로그인 운영자 |
| 주요 입력 항목 | 트레이너·기준 월·회원 검색·회원 선택·진행 횟수 |
| 주요 조회 항목 | 진행 목록, 대상 회원 잔여, 상품·계산 지급단가·지급액, 서비스 금액 색 |
| 주요 버튼/액션 | 등록, 삭제/복원 질문, 초기화, 목록 더블클릭; 이전 월 복사와 상품 목록은 숨김 |
| 호출되는 로직 | UpdateSession, DeleteSession, LoadUserData, LoadSessionData, LoadBeforeSession |
| 관련 코드 | [Forms/Session/frmSessionRegister.cs](../../Y3/Y3/Forms/Session/frmSessionRegister.cs) — UpdateSession(229행), DeleteSession(180행), LoadUserData(501행), LoadSessionData(524행), LoadBeforeSession(129행) |
| 디자인 코드 | [frmSessionRegister Designer](../../Y3/Y3/Forms/Session/frmSessionRegister.Designer.cs) |
| 웹 분리 가능성 — 추정 | 진행 조회와 입력/삭제 확인 분리 가능. 계약/예약 페이지와 동일시 금지 |

## S07. 개인 매출등록

| 항목 | 내용 |
| --- | --- |
| 화면명 / 클래스 | 개인 매출등록 / frmTrainerSales |
| 상태 | 메뉴 연결됨; 트레이너 콤보 초기화 누락으로 정상 입력·조회 차단 |
| 목적 | 트레이너에 귀속되는 수동 매출 기록 관리 |
| 진입 | 세션정산 → 개인 매출등록 |
| 사용자 | 로그인 운영자 |
| 주요 입력 항목 | 트레이너·기준 월·금액·메모 |
| 주요 조회 항목 | 트레이너 월별 매출 목록 처리기 존재; 기본 경로에서는 조회되지 않음 |
| 주요 버튼/액션 | 등록(신규/수정), 삭제, 초기화, 행 더블클릭 |
| 호출되는 로직 | UpdateSales, DeleteSales, LoadSalesData |
| 관련 코드 | [Forms/Session/frmTrainerSales.cs](../../Y3/Y3/Forms/Session/frmTrainerSales.cs) — UpdateSales(148행), DeleteSales(128행), LoadSalesData(114행) |
| 디자인 코드 | [frmTrainerSales Designer](../../Y3/Y3/Forms/Session/frmTrainerSales.Designer.cs) |
| 웹 분리 가능성 — 추정 | 매출 기록 목록과 편집 페이지/모달 가능 |

## S08. 세션현황

| 항목 | 내용 |
| --- | --- |
| 화면명 / 클래스 | 세션현황 / frmSessionStats |
| 상태 | 활성 |
| 목적 | 트레이너의 기간별 진행 수업·지급금액·매출 집계 확인 |
| 진입 | 세션정산 → 세션현황 |
| 사용자 | 로그인 운영자 |
| 주요 입력 항목 | 검색 시작 월·종료 월, 검색 연도 |
| 주요 조회 항목 | 당월/지정 범위 트레이너별 종류별 횟수·지급 합계; 연도 월별 수업수·수입·매출·합계·평균 |
| 주요 버튼/액션 | 기간 검색, 연도 검색 |
| 호출되는 로직 | LoadData, LoadMonthlyData |
| 관련 코드 | [Forms/Session/frmSessionStats.cs](../../Y3/Y3/Forms/Session/frmSessionStats.cs) — LoadData(194행), LoadMonthlyData(123행) |
| 디자인 코드 | [frmSessionStats Designer](../../Y3/Y3/Forms/Session/frmSessionStats.Designer.cs) |
| 웹 분리 가능성 — 추정 | 기간 정산표와 연간 통계를 여러 탭/페이지로 분리 가능 |

## S09. 가계부 통계

| 항목 | 내용 |
| --- | --- |
| 화면명 / 클래스 | 가계부 통계 / frmFinanceMain |
| 상태 | 활성 |
| 목적 | 장부 자산·카드 부채·순자산 현황 확인 |
| 진입 | 가계부 → 통계 |
| 사용자 | 로그인 운영자 |
| 주요 입력 항목 | 업무 입력 없음 |
| 주요 조회 항목 | 자산별 유형·잔액, 비카드 자산합·카드 부채합·순자산, 자산 차트 |
| 주요 버튼/액션 | 화면 재표시 시 갱신, 차트 금액 툴팁 |
| 호출되는 로직 | LoadData, UpdateBalaceText, UpdateChart |
| 관련 코드 | [Forms/Finance/frmFinanceMain.cs](../../Y3/Y3/Forms/Finance/frmFinanceMain.cs) — LoadData(65행), UpdateBalaceText(77행), UpdateChart(92행) |
| 디자인 코드 | [frmFinanceMain Designer](../../Y3/Y3/Forms/Finance/frmFinanceMain.Designer.cs) |
| 웹 분리 가능성 — 추정 | 자산 현황 페이지 1개 가능 |

## S10. 가계부 내역

| 항목 | 내용 |
| --- | --- |
| 화면명 / 클래스 | 가계부 내역 / frmFinanceInput |
| 상태 | 활성 |
| 목적 | 수입·지출·이체 장부와 관련 자산 잔액 관리 |
| 진입 | 가계부 → 내역 |
| 사용자 | 로그인 운영자 |
| 주요 입력 항목 | 검색 월, 거래일, 수입/지출/이체, 자산, 분류/도착자산, 금액, 메모 |
| 주요 조회 항목 | 월 거래 목록·계좌명·분류명·유형·금액·날짜·메모 |
| 주요 버튼/액션 | 등록(신규/수정), 삭제, 초기화, 행 더블클릭, 유형 선택 |
| 호출되는 로직 | LoadData, UpdateTransaction, DeleteTransaction, UpdateAccount |
| 관련 코드 | [Forms/Finance/frmFinanceInput.cs](../../Y3/Y3/Forms/Finance/frmFinanceInput.cs) — LoadData(161행), UpdateTransaction(263행), DeleteTransaction(241행), UpdateAccount(318행) |
| 디자인 코드 | [frmFinanceInput Designer](../../Y3/Y3/Forms/Finance/frmFinanceInput.Designer.cs) |
| 웹 분리 가능성 — 추정 | 내역 조회와 거래 입력/수정/취소 확인 분리 가능 |

## S11. 가계부 설정

| 항목 | 내용 |
| --- | --- |
| 화면명 / 클래스 | 가계부 설정 / frmFinanceSetting |
| 상태 | 활성 |
| 목적 | 자산·거래 분류·고정 수입/지출 설정 관리 |
| 진입 | 가계부 → 설정 |
| 사용자 | 로그인 운영자 |
| 주요 입력 항목 | 자산 이름·유형·잔액; 분류 이름·유형·메모; 고정거래 이름·유형·금액·자산·분류·일 |
| 주요 조회 항목 | 자산·분류·고정거래 각각 목록, 고정거래 자산·분류·지정일·금액·내용(최근 입력일/갱신일은 숨김) |
| 주요 버튼/액션 | 각 등록(신규/수정), 삭제, 초기화, 행 더블클릭 |
| 호출되는 로직 | UpdateAccount, UpdateCategory, UpdateFixed, DeleteAccount, DeleteCategory, DeleteFixed |
| 관련 코드 | [Forms/Finance/frmFinanceSetting.cs](../../Y3/Y3/Forms/Finance/frmFinanceSetting.cs) — UpdateAccount(341행), UpdateCategory(372행), UpdateFixed(403행), DeleteAccount(447행), DeleteCategory(469행), DeleteFixed(491행) |
| 디자인 코드 | [frmFinanceSetting Designer](../../Y3/Y3/Forms/Finance/frmFinanceSetting.Designer.cs) |
| 웹 분리 가능성 — 추정 | 자산·분류·고정거래 3페이지/탭 분리 가능 |

## S12. 어드민관리

| 항목 | 내용 |
| --- | --- |
| 화면명 / 클래스 | 어드민관리 / FrmAdminRegister |
| 상태 | 조건부 메뉴 |
| 목적 | 전체 센터와 운영 로그인 계정 관리 |
| 진입 | 어드민설정 → 어드민관리 |
| 사용자 | 센터1 계정ID admin의 정상 메뉴 경로 |
| 주요 입력 항목 | 센터 이름; 계정 센터·ID·새 비밀번호 |
| 주요 조회 항목 | 센터 목록, 계정 목록·센터·최근 접속(사용여부는 숨김) |
| 주요 버튼/액션 | 센터/계정 등록(신규/수정), 삭제, 초기화, 행 더블클릭 |
| 호출되는 로직 | UpdateGym, DeleteGym, UpdateAdmin, DeleteAdmin |
| 관련 코드 | [Forms/admin/frmAdminRegister.cs](../../Y3/Y3/Forms/admin/frmAdminRegister.cs) — UpdateGym(227행), DeleteGym(204행), UpdateAdmin(291행), DeleteAdmin(269행) |
| 디자인 코드 | [FrmAdminRegister Designer](../../Y3/Y3/Forms/admin/frmAdminRegister.Designer.cs) |
| 웹 분리 가능성 — 추정 | 센터와 계정 관리 분리 가능 |

## S13. 락커 설정 팝업

| 항목 | 내용 |
| --- | --- |
| 화면명 / 클래스 | 락커 설정 팝업 / popLocker |
| 상태 | 활성 |
| 목적 | 락커 소유자 배정·종료일 설정·수동 마감 |
| 진입 | 메인 락커 타일 |
| 사용자 | 로그인 운영자 |
| 주요 입력 항목 | 소유자 유형/선택, 종료일, 무기한 |
| 주요 조회 항목 | 락커 번호·소유자·현재 종료일 |
| 주요 버튼/액션 | 회원 선택, 트레이너 선택, 1/3/6/12개월·+1개월, 저장, 사용마감, 닫기 |
| 호출되는 로직 | LoadOwner, SaveLocker, UseEnd, BtnDt_Click |
| 관련 코드 | [Forms/Popup/popLocker.cs](../../Y3/Y3/Forms/Popup/popLocker.cs) — LoadOwner(167행), SaveLocker(207행), UseEnd(232행), BtnDt_Click(105행) |
| 디자인 코드 | [popLocker Designer](../../Y3/Y3/Forms/Popup/popLocker.Designer.cs) |
| 웹 분리 가능성 — 추정 | 락커 상세 모달/페이지 가능. 배정과 마감은 별도 행위 |

## S14. 회원/트레이너 선택 팝업

| 항목 | 내용 |
| --- | --- |
| 화면명 / 클래스 | 회원/트레이너 선택 팝업 / popUser |
| 상태 | 활성 |
| 목적 | 락커 배정 대상의 ID와 이름 선택 |
| 진입 | 락커 설정 → 회원/트레이너 |
| 사용자 | 로그인 운영자 |
| 주요 입력 항목 | 회원 이름/전화 검색, 대상 행 선택; 트레이너 모드는 검색 패널 숨김 |
| 주요 조회 항목 | 회원 또는 트레이너의 이름·전화 등 목록 |
| 주요 버튼/액션 | 선택, 더블클릭 선택, 닫기 |
| 호출되는 로직 | LoadUserData, LoadTrainerData, BtnChoose_Click, Grid_List_CellDoubleClick |
| 관련 코드 | [Forms/Popup/popUser.cs](../../Y3/Y3/Forms/Popup/popUser.cs) — LoadUserData(145행), LoadTrainerData(140행), BtnChoose_Click(73행), Grid_List_CellDoubleClick(56행) |
| 디자인 코드 | [popUser Designer](../../Y3/Y3/Forms/Popup/popUser.Designer.cs) |
| 웹 분리 가능성 — 추정 | 공통 대상 검색/선택 모달 가능 |

## S15. 급여 팝업

| 항목 | 내용 |
| --- | --- |
| 화면명 / 클래스 | 급여 팝업 / popPaySalary |
| 상태 | 빈 폼, 미연결 |
| 목적 | 화면 틀만 존재 |
| 진입 | 호출부 미확인 |
| 사용자 | 확인 불가 |
| 주요 입력 항목 | 없음 |
| 주요 조회 항목 | 없음 |
| 주요 버튼/액션 | 없음 |
| 호출되는 로직 | popPaySalary |
| 관련 코드 | [Forms/Popup/popPaySalary.cs](../../Y3/Y3/Forms/Popup/popPaySalary.cs) — popPaySalary(15행) |
| 디자인 코드 | [popPaySalary Designer](../../Y3/Y3/Forms/Popup/popPaySalary.Designer.cs) |
| 웹 분리 가능성 — 추정 | 현재 기능 근거가 없어 급여 페이지로 취급 불가 |

## C01. UCLocker 재사용 컨트롤

메인에서 설정 LOCKER_COUNT(기본 60)만큼 동적으로 만든다. 번호·소유자·기간을 표시하고 클릭 시 소유자 유형/ID/락커 번호를 부모 이벤트로 전달한다. 회원은 초록, 트레이너는 연한 파랑, NONE은 흰색이다. 만료일 경고는 부모가 빨강/노랑으로 덮어쓴다. 만료 소유자명에는 날짜 차이가 음수 일수로 붙는다.

근거: [UCLocker.cs](../../Y3/Y3/UserControls/UCLocker.cs) SetLockerOwner/SetOwnerColor/InitOwner/Btn_locker_Click, frmMain.MakeLocker/SetLockerColor. 추정: 웹에서는 락커 목록의 타일 구성 요소에 해당한다.

## 숨김과 사용 불가의 차이

- frmSessionRegister의 btnLoad, dtLoad, 상품 목록 groupBox2는 Designer에서 Visible=false다. 해당 로직은 존재하지만 표시를 다시 켜는 코드는 미확인이다.
- 관리자 메뉴는 Designer에서 숨기고 조건부로 표시한다. 사용자별 필드 Enabled 상태는 권한 체계가 아니다.
- 기타 설정과 급여 팝업은 Designer에도 업무 컨트롤이 없다.
- frmMain.ReadExcelData와 GetMonthBirthUser/GetMonthBirthTrainer는 호출이 확인되지 않아 별도 사용자 화면으로 세지 않는다.

## 역검증: 화면 존재와 실행 가능성

- S07 개인 매출등록: 메뉴와 버튼은 연결되지만 트레이너 콤보 초기화가 누락된다. Core.InitForm은 frmTrainerSales.InitComboEvent를 호출하지 않고 생성자도 호출하지 않는다. Designer에도 Items/DataSource가 없다. LoadSalesData(114행)는 null이면 반환하고 UpdateSales(148행)는 null의 ToString을 호출한다. 따라서 주요 조회·액션 항목은 구현된 처리기이며 정상 사용 가능하다고 확인한 기능이 아니다.
- 가계부 입력/설정: 분류 변경 이벤트 구독이 주석 처리되어 분류 콤보의 즉시 갱신을 보장하지 않는다(frmFinanceInput.InitComboEvent:73, frmFinanceSetting.UpdateComboCategory:325).
- 메인 락커: MakeLocker(450행)는 생성 시 호출된다. SetLockerColor(499행)는 생성 및 개별 UpdateLocker 시 호출되며 메인 복귀나 날짜 변경에 따른 자동 재평가 경로는 찾지 못했다.
