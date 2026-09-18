# 12. 용어집

| 용어 | 현재 코드에서의 의미 | 근거 / 주의 |
| --- | --- | --- |
| 센터 / Gym | 로그인·데이터 소속 단위 | `Models/Gym.cs`, `BasicDBModel.GymNo` |
| 어드민 / Admin | 프로그램 로그인 계정 | `Models/Admin.cs`, `frmLock.Login`; 모든 계정이 최상위 관리자라는 뜻은 아님 |
| User / 회원 | 헬스장 회원정보 | `Models/User.cs`; 웹 사용자 계정 의미와 다름 |
| Trainer / 트레이너 | 회원 담당 및 수업·매출 귀속 대상 | `Models/Trainer.cs`; 인증 계정과 연결 없음 |
| 세션 종류 / SessionPrice | PT 종류와 트레이너 정산 단가 설정 | `Models/SessionPrice.cs`; 계약 아님 |
| SessionId | User와 SessionTrainer에서 PT 종류의 ID | `frmSettingUser.UpdateUser`, `frmSettingSession.UpdateST`; Session 기록 ID 아님 |
| 세션진행 / Session | 날짜·회원·트레이너·종류별 진행 횟수/지급액 기록 | `Models/Session.cs`; 한 행에 여러 회차 가능, 예약 아님 |
| SessionPriceId | 진행 기록의 종류 ID | `Session.SessionPriceId` |
| SessionTrainer | 트레이너·종류 조합의 별도 지급률 | `Models/SessionTrainer.cs`; 수업 담당 배정 이력 아님 |
| RemainSession | 일반 잔여 횟수 | `UserList.MinusUserSessionCount`에서 우선 차감 |
| RemainService | 서비스 잔여 횟수 | 일반 잔여 소진 후 차감 |
| IsService | 해당 진행 기록이 서비스 횟수인지 | `Session`, `frmSessionRegister.UpdateSession` |
| Price | 세션 종류의 기준 가격 | `SessionPrice.Price` |
| Percentage / 지급률 | 공제 후 기준금액에서 트레이너에게 적용하는 비율 | `Core.CalcTotalPrice` |
| Deduct / 공제율 | 기준 가격에서 먼저 공제하는 비율 | `SessionPrice` 주석은 세금이라 부르지만 법적 세목/세율은 미확인 |
| FinalPrice / 지급단가 | 공통 지급률·공제율로 계산한 금액 | `SessionPrice`, `frmSettingSession` |
| SessionTotalPrice / 지급금액 | 진행 기록의 트레이너 지급금액 | 화면 라벨과 정산 합계 근거. 고객 결제액으로 해석 금지 |
| 수입(세션 현황) | 세션 지급금액 합 | `frmSessionStats.LoadMonthlyData`의 gridIncome |
| 매출 / TrainerSales | 트레이너 귀속 수동 입력액 | 세션 지급금액·가계부 수입과 자동 연동 없음 |
| Salary / 기본급 | 트레이너에 저장하는 정수 급여 정보 | `Trainer.Salary`; 정산 화면 합계에 더하는 코드 미확인 |
| Transaction | 가계부의 수입·지출·이체 기록 | DB 트랜잭션 또는 카드승인과 구별 |
| DB transaction | BeginTransaction~Commit 명령 범위 | `MariaDB.Save/MultiSave/ExecuteQuery` |
| Account / 자산 | 현금·은행·신용카드 장부의 잔액 보유 단위 | `Finance/Account.cs`; 실제 은행 API 없음 |
| CategoryId | 수입/지출은 분류 ID, 이체는 도착 자산 ID | `QueryString.QUERY_SELECT_TRANSACTION` |
| FixedTransaction | 로그인 시 자동 장부입력 후보가 되는 고정 수입/지출 설정 | `CheckLastInputDate`, 현재 반복 판정 결함 주의 |
| useflag | 일반적으로 1=활성, 0=논리삭제 | `QueryString`; locker에는 없음 |
| OwnerType | 락커 소유자 종류 | enum/SQL/DDL 값 불일치. [05](05-database-model.md) 참조 |
| 락커 마감 | 소유자 ID/이름/종류를 비워 반납 처리 | `popLocker.UseEnd`; 자동 만료 반납 아님 |
| 기한없음 | EndDate=DateTime.MinValue | `popLocker`, `UCLocker`; DB NULL과 동일하지 않음 |
| LAST_GYM | 마지막 로그인 센터 ID 저장값 | 복원 시 SelectedIndex로 사용되는 불일치 존재 |
| MultiSave | 한 연결 트랜잭션에서 최대 1000개씩 나누어 SQL 실행 | 다중 업무 전체 원자성을 의미하지 않음 |
| 계약·예약·출석·결제·환불 | 이번 코드에서 독립 도메인으로 확인되지 않은 개념 | 자유 메모·수동 장부를 근거로 존재를 단정하지 않음 |

역검증 보완: “매출 입력”은 모델과 처리기의 명칭이며 현재 개인 매출등록 화면의 정상 실행을 뜻하지 않는다(초기화 누락, K37). “저장 성공”은 예외 없는 SQL 실행·커밋의 반환값이며 변경 행 수 확인과 다르다(MariaDB.Save/MultiSave, K38). “useflag”는 물리 컬럼과 모델 속성을 구분한다. Transaction에는 같은 이름의 모델 속성이 없다.
