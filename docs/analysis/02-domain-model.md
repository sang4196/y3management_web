# 02. 도메인 모델

`Session`이라는 이름만으로 계약·예약으로 해석하지 않는다. 현재 모델은 진행 횟수와 지급금액을 담는 기록이다. 아래 공통 `Id/GymNo`는 `BasicDBModel`에서 상속한다. DB 전체 컬럼은 [05](05-database-model.md)에 있다.

| 도메인 / 엔티티 | 목적·주요 필드 | 주요 기능 | 관계·근거 |
| --- | --- | --- | --- |
| 센터 / `Gym` | 센터 식별. Id, GymName, UseFlag | 센터 등록·이름 변경·비활성화, 로그인 센터 선택 | 업무 테이블 gym_no의 논리적 기준. `Models/Gym.cs`, `FrmAdminRegister.UpdateGym/DeleteGym` |
| 로그인 계정 / `Admin` | 운영자 로그인. AdminId, AdminPw, GymNo, GymName(조회), LastVisitDate, UseFlag | 로그인, 계정 생성·암호 변경·비활성화 | Gym 소속. User/Trainer와 연결 없음. `Models/Admin.cs`, `frmLock.Login`, `FrmAdminRegister.UpdateAdmin` |
| 회원 / `User` | 회원 및 현재 PT 이용 상태. Name, BirthDay, PhoneNumber, SessionId/Name, RemainSession, RemainService, TrainerId/Name, Memo, LockerNo(조회) | 회원 등록·검색·수정·삭제, 상품/담당 지정, 잔여 횟수 직접 설정·차감·복원 | 현재 상품 1개·담당 1개를 필드로 보유. Session/Locker와 연결. `Models/User.cs`, `frmSettingUser.UpdateUser`, `ModelList.UserList` |
| 트레이너 / `Trainer` | 직원 기본정보. Name, BirthDay, PhoneNumber, Salary, Memo, LockerNo(조회) | 등록·기본급 수정·삭제·목록 선택 | 회원 담당, 진행 수업, 개별 지급률, 매출, 락커. 로그인 역할 아님. `Models/Trainer.cs`, `frmSettingUser.UpdateTrainer` |
| PT 종류·정산 단가 / `SessionPrice` | 세션 종류별 단가·지급 기준. SessionName, Price, Percentage, Deduct, FinalPrice | 종류 등록·수정 시도·삭제, 지급단가 계산 | User.SessionId와 SessionTrainer.SessionId는 이 모델을 가리킴. `Models/SessionPrice.cs`, `frmSettingSession.UpdateSessionPrice`, `Core.CalcTotalPrice` |
| 트레이너별 지급률 / `SessionTrainer` | 공통 지급률을 개별 트레이너에 대해 대체. SessionId/Name, TrainerId/Name, Percentage | 조합별 등록·수정 시도·삭제 | SessionPrice × Trainer 연결. `session` 수업기록의 배정 테이블이 아님. `Models/SessionTrainer.cs`, `ModelList.GetSessionTrainerTotalPrice` |
| 진행 수업·정산 기록 / `Session` | 날짜·회원·트레이너별 진행 횟수와 지급금액. Date, UserId/Name, TrainerId/Name, SessionPriceId/Name, SessionCount, SessionTotalPrice, IsService | 진행 등록·잔여 차감, 기록 조회·수정·삭제 및 선택 복원, 월/연 집계 | 한 행에 여러 횟수 가능. 보통/서비스 분할 가능. 예약 슬롯·출석 상태 없음. `Models/Session.cs`, `frmSessionRegister.UpdateSession/DeleteSession` |
| 트레이너 매출 / `TrainerSales` | 트레이너 귀속 매출을 수동 기록. TrainerId/Name, SalesDate, SalesPrice, Memo | 월별 등록·수정·삭제 처리기는 있으나 화면 초기화 누락으로 기본 경로 차단; 기존 DB 자료의 연간 월별 합계 | Trainer만 직접 참조. 회원·계약·결제·가계부 FK 없음. `Models/TrainerSales.cs`, `frmTrainerSales.UpdateSales`, `frmSessionStats.LoadMonthlyData` |
| 락커 이용 / `Locker` | 번호별 현재 소유자와 기간. LockerNo, OwnerType/Id/Name, StartDate, EndDate | 배정, 종료일 편집 시도, 무기한 지정, 수동 마감, 만료 강조 | 소유자가 회원 또는 트레이너인 다형 관계. 사용 이력 테이블 없음. `Models/Locker.cs`, `popLocker`, `UCLocker` |
| 가계부 자산 / `Account` | 현금·은행·신용카드 잔액. Name, AccountType, Balance, UseFlag | 자산 등록·잔액 직접 수정·삭제, 자산/부채/순자산 조회 | 거래·고정 거래의 자산 및 이체 도착 자산. 실제 금융계좌 API 아님. `Models/Finance/Account.cs`, `frmFinanceSetting.UpdateAccount` |
| 거래 분류 / `Category` | 수입·지출 등의 분류. Name, TransactionType, Memo, UseFlag | 등록·수정·삭제, 유형별 선택 목록 | Transaction/FixedTransaction에서 참조. `Models/Finance/Category.cs`, `frmFinanceSetting.UpdateCategory` |
| 가계부 거래 / `Transaction` | 수입·지출·이체 장부. AccountId, CategoryId, TransactionType, Amount, Date, Memo; 조회용 명칭 (DB useflag는 있으나 Transaction 모델 속성은 없음) | 월 조회, 등록·수정·삭제 및 잔액 반영/역처리 | 이체 시 CategoryId는 수취 Account.Id. 회원 결제 승인 데이터 아님. `Models/Finance/Transaction.cs`, `frmFinanceInput.UpdateTransaction/UpdateAccount` |
| 고정 수입·지출 / `FixedTransaction` | 정기 장부 입력 설정. Name, Amount, Day, AccountId, CategoryId, TransactionType, LastInputDate, UpdateDate, UseFlag | 설정 관리, 로그인 시 입력 대상 검사·장부 생성 | Transaction 생성하지만 원본 fixed ID는 거래에 저장하지 않음. `Models/Finance/FixedTransaction.cs:73`, `Core.CheckFixedTransaction` |

## 존재 범위를 오해하기 쉬운 개념

- **PT 계약**: 독립 엔티티·계약번호·체결일·계약금액·상태는 미확인. 회원의 현재 종류/잔여 횟수 편집이 그 일부 업무를 대신하는 것으로 **추정**할 수 있지만 계약 이력으로 볼 수 없다.
- **예약·출석**: 시작/종료 슬롯, 예약 상태, 출석 체크, 중복 시간 검사 구현 미확인. 진행 세션을 출석 기록으로 취급하는지는 운영 확인이 필요하다.
- **결제·환불**: 승인번호·결제수단별 승인 처리·원거래 환불 관계 미확인. 매출 수동 입력, 가계부 거래 삭제/역처리, 세션 삭제/횟수 복원은 서로 다른 기능이다.
- **회원권·상담**: 기간형 회원권, 만료 처리, 상담 기록 모델 미확인. Memo는 자유 텍스트이며 별도 상담 도메인의 근거가 아니다.
- **급여 지급**: Salary, 세션 지급금액, Config.PAY_DAY와 빈 popPaySalary는 있으나 지급 확정·실제 송금·지급 이력 기능은 미확인.

근거 범위: 전체 `Models`, `Forms`, `Models/DB/QueryString.cs`, `Utility/Version/sql/CreateTable.sql`, `popPaySalary.cs` 및 Designer.

## 관계의 한계

이름을 ID 옆에 중복 저장한다. 기록 시점 명칭 보존 목적은 **추정**이며, 이름 변경에 대한 일괄 동기화나 버전 정책은 없다. 회원의 상품·횟수·담당 변경도 이력 없이 덮어쓴다. `SessionTotalPrice`는 UI에서 **지급금액**이라고 표시되므로 고객 결제금액과 구별해야 한다. DDL에는 FK가 없어 위 관계는 애플리케이션상 논리 관계다.

매출 화면의 실행 제약은 frmTrainerSales.InitComboEvent 미호출과 LoadSalesData의 null 검사로 확인한다. 매출 모델·테이블·통계 코드의 존재를 정상 입력 가능성으로 해석하지 않는다. Session 수정 역시 UPDATE 시도이며 GymNo 누락으로 실제 행 변경이 없을 수 있다([K05/K37](11-risks-and-unknowns.md)).
