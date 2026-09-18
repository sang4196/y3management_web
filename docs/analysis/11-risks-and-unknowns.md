# 11. 위험과 불명확한 부분

아래는 정적 코드 경로로 확인한 결함·위험이다. 실제 장애 발생 여부와 데이터 영향 규모는 운영 자료로 검증하지 않았다. 원문 경로는 `Y3/Y3/` 기준이다. `높음`은 금액·잔여·계정·데이터 보존에 직접 영향을 줄 수 있다는 분석 판단이다.

## 우선 확인할 문제

| ID / 중요도 | 확인 사실·재현 조건 또는 영향 | 코드 근거 |
| --- | --- | --- |
| K01 높음 | 이체 잔액 저장의 `Save(from) || Save(to)`는 첫 저장 성공 시 두 번째를 실행하지 않음. 메모리상 받는 계좌는 변경되지만 DB 저장 누락. 반대로 첫 실패·둘째 성공도 성공 반환 | `Forms/Finance/frmFinanceInput.cs:318`, 특히 366 부근 |
| K02 높음 | 진행 세션 MultiSave 커밋 후 회원 횟수를 별도 Save. 두 번째 실패해도 수업은 남고 차감 성공 여부를 확인하지 않음. 삭제와 복원도 분리 | `frmSessionRegister.UpdateSession/DeleteSession`, `ModelList.cs:397`, `MariaDB` |
| K03 높음 | 거래 수정은 원거래 잔액 역처리 후 거래 저장. 거래 저장 실패 시 역처리된 잔액 복구 없음. 삭제 후 역처리 실패에도 삭제는 이미 커밋 | `frmFinanceInput.UpdateTransaction:263/DeleteTransaction:241` |
| K04 높음 | 일반 2회+서비스 1회를 입력하면 일반 기록의 count는 2인데 금액은 입력 3회 전체 금액을 사용하고 서비스 금액도 추가. 일반 단가 50000이면 일반 150000+서비스 25000으로 저장 경로가 계산됨 | `frmSessionRegister.UpdateSession` d1/d2 생성, `TxtSessionUseCount_KeyUp` |
| K05 | 기존 수업 수정도 현재 잔여를 검증하고 IsService를 재계산한다. 특히 새 Session 객체에 GymNo를 지정하지 않아 id+gym_no UPDATE가 0행일 수 있으나 성공으로 처리된다. | frmSessionRegister.UpdateSession:229, Models/Session.GetQueryParam, QueryString |
| K06 높음 | 모델의 SQL 값은 문자열 보간. 이름·메모의 작은따옴표만으로도 구문 오류 가능. 파라미터 바인딩 미확인으로 SQL 주입 위험 | `Models/User.cs:45`, 다른 `GetQueryParam`, `DB*.GetSaveQuery`, `MariaDB` |
| K07 높음 | DB 암호가 소스에 고정되고 root 계정 사용. 운영 권한은 미확인 | `Cores/Database/MariaDB.cs:16` |
| K08 높음 | 계정 암호가 DPAPI CurrentUser 의존. 복호화 실패 시 빈 값 반환 후 입력과 비교하므로 빈 입력이 실패 결과와 일치하는 경로. 다른 PC/OS 사용자로 이관 시 인증 장애 가능 | `Utility/Secure.cs:20,64` |
| K09 높음 | 초기 설정 LAST_VERSION이 빈 경우 CreateTable.sql 실행. 스크립트는 기존 핵심 9개 테이블 DROP 후 생성. 로컬 설정 유실과 DB 보존의 조합이 데이터 손실 경로가 됨 | `VersionCheck.Loop/CreateTable`, `CreateTable.sql` |
| K10 높음 | 버전 동기화가 실패해도 Core.CheckVersion은 현재 버전을 설정파일에 기록. 다음 시작에서 필요한 동기화를 건너뛸 수 있음 | `Core.cs:105`, `VersionCheck.CheckSync` |
| K11 높음 | 락커 enum은 NONE=1, USER=2, TRAINER=3. JOIN은 회원=1, 트레이너=2. DDL 주석은 회원=0, 트레이너=1. 회원/트레이너 목록의 락커 표시 오연결 가능 | `Enums.cs:21`, `QueryString.cs:12,13`, `CreateTable.sql` locker |
| K12 높음 | 고정 거래 완료 후 LastInputDate.Day=Day가 되어 다음 달에도 `< Day`가 거짓. 연말→연초는 월 비교도 실패. 정기 반복을 수행하지 못할 수 있음 | `FixedTransaction.cs:73`, `Core.CheckFixedTransaction:167` |
| K13 | 잔여/잔액을 캐시에서 읽어 절대값으로 UPDATE하며 충돌 검출이 없다. 추정: 다른 동시 쓰기 주체가 같은 DB를 변경하면 갱신 유실 가능. 현재 연결은 127.0.0.1이며 여러 PC의 공유 배포는 확인하지 않았다. | Program.Main, UserList.MinusUserSessionCount, Account, QueryString |
| K14 높음 | FK/업무 UNIQUE/CHECK 없음. 삭제한 회원/트레이너/상품/자산을 참조하는 기록이 남을 수 있음. 중복검사는 로컬 캐시만 사용 | DDL 전체, `Delete*`, `Duplication` |
| K15 높음 | 단일 현재 사용자/센터/모델/폼을 프로세스 전체에서 공유. 웹 다중 사용자 환경에서 같은 구조를 쓰면 상태 혼선 위험 | `Core`, `Singleton<T>`, `ModelList` |

## 추가 결함과 유지보수 위험

| ID | 사실·영향 | 근거 |
| --- | --- | --- |
| K16 | 단가 이름/개별 지급률 중복 검사는 수정 대상 자신도 포함해 같은 이름·조합 유지 수정 불가 | `frmSettingSession.UpdateSessionPrice/UpdateST`, `ModelList.Duplication` |
| K17 | 락커 저장은 소유자의 기존 락커를 무조건 거부하므로 정상 연장 시에도 자신과 충돌. 소유자 미선택 검증·시작일 설정도 없음 | `popLocker.SaveLocker` |
| K18 | DB Get/Save/MultiSave/ExecuteQuery는 예외를 삼켜 빈 목록 또는 false만 반환. 진단 로그 없음. 실패와 실제 빈 데이터 구분 어려움 | `MariaDB.cs:44,85,109,135`; 반면 `GetDataByQueryString`은 예외 전파 |
| K19 | 기존 모델 객체를 먼저 수정한 뒤 Save하므로 실패 시 메모리와 DB 불일치. 일부 UI는 캐시 재사용 | `frmSettingUser.UpdateUser`, `frmFinanceInput.UpdateTransaction`, `ModelList.GetById` |
| K20 | INSERT는 로그인 GymNo를 SQL에 사용하지만 객체에는 Id만 채우는 경로가 있다. 재조회 전 객체 GymNo=0으로 UPDATE하면 session/locker/session_price/session_trainer/trainer_sales는 대상 0행 가능; finance_account/category/transaction은 id로 찾아 gym_no를 0으로 변경 가능. 재조회 여부에 따라 영향이 다름. | BasicDBModel, 각 GetQueryParam, QueryString, ModelList.*.Save |
| K21 | MultiSave는 1000건씩 실행하고 마지막 명령의 LastInsertedId만 반환. 호출자는 전체 데이터 ID를 그 값부터 1씩 증가시켜 할당 | `MariaDB.MultiSave:135`, `LoadBeforeSession`, `UpdateSession`, `ReadExcelData` |
| K22 | 새 SQL 초기화의 finance 테이블 4개에는 DROP/IF NOT EXISTS 없음. 일부 테이블만 존재할 때 반복 실행 실패 가능. DDL 전체 원자성을 코드의 BeginTransaction만으로 확정할 수 없음 | `CreateTable.sql`, `MariaDB.ExecuteQuery` |
| K23 | DateTime.MinValue를 birthday·end_date 등의 datetime SQL 문자열로 출력. DB 버전/SQL mode와 날짜 범위 호환성 미검증 | `User.GetQueryParam`, `Locker.GetQueryParam`, `frmSettingUser`, `popLocker` |
| K24 | 금액은 decimal 필드와 int.Parse/UI 문자열/정수 DataColumn을 혼용. `ToString("00")` 후 파싱 등으로 소수 보존이 일관되지 않음 | `frmSessionRegister.Grid_CellDoubleClick/UpdateSession`, `frmSessionStats` |
| K25 | 지급률·공제율 DDL decimal(4,2)는 100.00을 표현할 수 없는 정의. UI는 비율 범위 검사를 하지 않음 | `CreateTable.sql` session_price/session_trainer, `frmSettingSession` |
| K26 | 고정 거래 day의 유효 범위 검사가 없다. 빈값 0·음수·31 초과는 CheckLastInputDate 조건을 통과하지 못하며, 31일 설정은 30일까지인 달에 실행되지 않는다. 잘못된 day가 곧바로 DateTime 생성 예외를 낸다고 단정할 수 없다. LastInputDate 저장도 별도 커밋이다. | frmFinanceSetting.UpdateFixed, FixedTransaction.CheckLastInputDate:73, Core.CheckFixedTransaction |
| K27 | 자산이 신용카드만 있으면 비카드 필터가 빈 상태에서 CopyToDataTable 호출 경로가 있다. 폼 생성자가 LoadData를 호출하고 로그인 InitForm에서 생성하므로 메인 표시 전 예외 가능. 실행 재현은 하지 않았다. | frmFinanceMain 생성자/UpdateChart:92, Core.InitForm |
| K28 | 그리드 헤더 더블클릭(RowIndex=-1), 선택행 없는 선택 버튼, null 모델 등에 대한 보호 부족 | `popUser.Grid_List_CellDoubleClick/BtnChoose_Click`, `frmSessionRegister.DeleteSession` |
| K29 | 로그인센터 ID를 SelectedIndex로 복원. 목록 순서/센터 삭제에 따라 다른 센터 또는 범위 오류 | `frmLock.SetLastInfo`, `Core.SetLoginGym` |
| K30 | session_trainer 복수 UPDATE용 UNION 분기의 Id 누락으로 첫 SELECT와 열 개수 불일치. 현재 UI는 단건 저장이며 해당 복수 경로는 미연결 | `Models/SessionTrainer.cs:37`, `DBSessionTrainer.GetMultiSaveQuery` |
| K31 | 기본 DBTransaction.GetSelectQuery는 날짜 인수가 필요한 템플릿에 GymNo만 전달한다. FormatException은 MariaDB.Get에서 잡혀 빈 DataTable로 반환되는 경로다. ModelList의 초기 Transaction.ReadData 호출은 주석이며 활성 화면은 날짜 오버로드 사용. | DBTransaction.cs:71, MariaDB.Get, ModelList.ReadData, frmFinanceInput.LoadData |
| K32 | 숨겨진 종류 선택 분기에서 지급단가 대신 상품 ID×횟수로 합계 설정. 월 복사는 잔여 검증/차감 없음 | `frmSessionRegister.Grid_CellDoubleClick` SESSION_PRICE 분기, `LoadBeforeSession`, Designer 숨김 |
| K33 | 이름이 여러 테이블에 중복 저장되고 현재 상품·담당을 이름으로 콤보 복원. 이름 변경 시 과거 기록/화면 선택 불일치 가능 | 모델 `*Name` 필드, `frmSettingUser.Grid_List_CellDoubleClick` |
| K34 | 정산은 현재 활성 트레이너를 순회하므로 비활성 트레이너의 과거 기록은 표에서 빠질 수 있음. 종류별 열도 현재 활성 종류 기준 | `frmSessionStats.FrmSessionMain_VisibleChanged/LoadMonthlyData/LoadData` |
| K35 | 금융 UPDATE/DELETE의 로그인 센터 조건 부재, 계정/센터 전체 로드, 관리자 메뉴 표시만 제어 | `QueryString`, `Core.InitForm`, `frmMain` |
| K36 | 사용자 이벤트에서 동기 DB I/O, JSON 왕복 변환과 전량 캐시 조회로 UI 지연/데이터량 증가 부담 가능 | `Core.DataTableToObject`, `ModelList.ReadData`, 폼 조회 이벤트 |

## 중복·긴 메서드·강결합

- `ModelList.cs` 한 파일에 13개의 목록 클래스와 공통 저장/조합 계산이 있다. 테이블별 Read/Save/Add/Update 패턴이 반복되고 일부 Add/UpdateMultiData는 빈 구현이다. `DB*.cs`도 비슷한 INSERT/UPDATE 문자열 조립을 반복한다.
- 긴 업무 메서드: frmSessionRegister.UpdateSession(229행), frmMain.ReadExcelData(273행), frmSessionStats.LoadMonthlyData(123행). 검증·계산·DB 저장·메시지·UI 갱신이 한 메서드에 혼합된다. 행 수 자체를 결함의 근거로 삼지 않는다.
- `InitGrid`/Designer의 긴 코드는 주로 화면 선언이다. 긴 업무 메서드와 동일 위험으로 취급하지 않는다.
- Core의 폼 생성 순서와 콤보 이벤트 등록 순서에 의존한다. 숨겨진 화면도 객체가 만들어지고, 모델층의 저장도 UI 메시지에 의존한다.

근거: `ModelList.cs`, `DB*.cs`, `Core.InitForm:80`, `Core.SetEventUpdateComboTrainer`, `ModelList.Save:995`.

## 운영 확인 질문

1. 운영 DB의 실제 CREATE TABLE, FK/인덱스/트리거/프로시저, 서버 버전과 SQL mode가 저장소 DDL과 같은가?
2. owner_type의 실제 분포와 회원/트레이너의 올바른 연결값은 무엇인가?
3. 일반·서비스 혼합 수업의 지급금액과 기존 이체 거래의 양쪽 잔액은 맞는가? 기록 수정·직접 잔여 조정은 어떻게 운영했는가?
4. 계약·예약·결제·환불을 다른 시스템/수기에서 처리하는가? 현재 저장소에는 관계를 복원할 열이 없다.
5. 숨겨진 이전 월 복사·Excel 가져오기를 별도 빌드에서 사용했는가?
6. 지급률 소수/반올림, 서비스 단가, 12개월 평균, 비활성 트레이너의 과거 정산 표시가 의도와 일치하는가?
7. DB 암호문을 만든 Windows 사용자 환경을 보유하는가? 계정별 관리 범위는 실제로 어떻게 나뉘는가?
8. 로컬 Config.json의 배포·백업 방식은 무엇인가? 빈 설정으로 기존 DB에 접속한 적이 있는가?

이 질문들의 답은 미확인이며 코드 결함을 정상 업무 규칙으로 추정하여 채우지 않았다.

## 재검증에서 추가한 위험

| ID | 확인된 조건과 영향 | 코드 근거 |
| --- | --- | --- |
| K37 | 개인 매출등록의 InitComboEvent가 호출되지 않아 트레이너 콤보가 빈 상태. 조회는 반환되고 등록은 null 접근. 기존 매출 자료의 통계 집계와 구분해야 함 | Core.InitForm:80, frmTrainerSales 생성자:28/InitComboEvent:52/LoadSalesData:114/UpdateSales:148, Designer |
| K38 | ExecuteNonQuery 영향 행 수를 검사하지 않음. 0행 UPDATE도 true이며 화면 성공과 실제 데이터 변경이 다를 수 있음 | MariaDB.Save:109/MultiSave:135/ExecuteQuery:85 |
| K39 | 거래 분류 변경 이벤트 구독이 주석 처리됨. 저장 직후 현재 콤보 갱신을 보장하지 않으며 유형 변경 등에서 재구성 | frmFinanceInput.InitComboEvent:73/Radio_CheckedChanged/SetComboCategory, frmFinanceSetting.UpdateComboCategory:325 |
| K40 | 락커 마감은 모델 소유자를 지우지만 팝업의 _id/_type/_name 등 선택 상태는 남김. 새 소유자 선택 없이 다시 저장하면 이전 소유자를 재사용할 수 있음(저장·중복 검사 통과 조건) | popLocker.UseEnd:232/InitControl:159/SaveLocker:207 |
| K41 | 락커 색상은 생성과 개별 갱신 때 계산. 날짜가 바뀌거나 메인으로 돌아오는 것만으로 갱신되는 경로 없음. 오래 열린 화면의 만료색이 최신 날짜와 다를 수 있음 | frmMain 생성자/MakeLocker:450/SetLockerColor:499/UpdateLocker:525 |

