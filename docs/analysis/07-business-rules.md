# 07. 비즈니스 규칙

유지 여부는 **웹 재구현 검토 판단(추정)**이다. `유지`는 확인된 업무 의미의 보존, `정책 확인`은 담당자의 결정 필요, `결함 수정`은 현재 동작을 그대로 보존하지 말아야 한다는 뜻이다. 행의 원문 근거는 모두 `Y3/Y3/` 아래에 있다.

| ID | 실제 코드의 규칙·동작 | 근거 | 웹 재구현 시 유지 판단 |
| --- | --- | --- | --- |
| R01 | 대부분 업무 데이터는 로그인 계정의 GymNo로 조회/등록한다 | `Models/DB/QueryString.cs`, 엔티티 `GetQueryParam` | 유지. 쓰기 센터 검사 누락은 결함 수정 |
| R02 | 대부분 삭제는 useflag=0. locker는 삭제 대신 소유자를 비운다 | `QueryString.QUERY_DELETE_*`, `popLocker.UseEnd` | 의미 유지. 역사 보존·재활성 정책 확인 |
| R03 | 회원 이름 필수. 전화번호 없음 체크가 아니면 최소 10자리. 생일 없음은 DateTime.MinValue | `frmSettingUser.UpdateUser:371` | 필수/선택 의미 유지, 최소 날짜 직렬화는 재검토 |
| R04 | 상품 미선택 시 회원의 일반·서비스 잔여 횟수를 0으로 저장 | `frmSettingUser.UpdateUser` | 정책 확인. 상품 제거 시 잔여 소멸 의미 |
| R05 | 회원 상품·담당·잔여 횟수는 계약/입금 확인 없이 직접 덮어쓴다 | `frmSettingUser.UpdateUser` | 정책 확인. 결제 완료 조건이 있다고 추가 해석 금지 |
| R06 | 트레이너 이름·기본급 필수, 연락처/생일은 없음 선택 가능 | `frmSettingUser.UpdateTrainer:422` | 유지 |
| R07 | PT 종류 이름·가격·지급률·공제율 필수. 같은 이름은 거부 | `frmSettingSession.UpdateSessionPrice:261`, `SessionPriceList.Duplication` | 중복 방지 의도 유지. 수정 자기 자신 제외 안 하는 결함 수정 |
| R08 | 트레이너×PT 종류 지급률 조합은 중복 거부 | `frmSettingSession.UpdateST:313`, `SessionTrainerList.Duplication` | 의도 유지. 기존 조합 수정도 차단하는 결함 수정 |
| R09 | 기본 지급단가 = (가격 − 가격×공제율/100)×지급률/100 | `Core.CalcTotalPrice:135` | 유지. 세율의 법적 의미는 이 코드로 확정 불가 |
| R10 | 개별 지급률이 있으면 기본 지급률을 대체, 없으면 저장된 FinalPrice 사용 | `ModelList.GetSessionTrainerTotalPrice:1013`, `frmSessionRegister.Grid_CellDoubleClick` | 유지. 금액의 반올림/절사 정책 확인 |
| R11 | 진행 대상 목록은 일반+서비스 잔여 > 0; 선택한 트레이너 담당 회원으로 제한 | `ModelList.UserList.GetUsersHaveSessionDataTableByTrainerId:388` | 유지. 이것은 예약 가능 조건이 아님 |
| R12 | 회원 선택 전에 트레이너 선택 필요. 회원 상품 ID 및 해당 상품 존재 확인 | `frmSessionRegister.Grid_CellDoubleClick` USER 분기 | 유지 |
| R13 | 진행 저장은 회원·종류·트레이너·횟수 필수. 횟수 ≥1, 총 잔여 이하여야 함 | `frmSessionRegister.UpdateSession:229` | 유지. 서버에서도 동일 판단 필요 |
| R14 | 일반 횟수를 먼저 소진하고 초과분만 서비스에서 차감 | `UserList.MinusUserSessionCount:397`, `UpdateSession` | 유지 |
| R15 | 일반과 서비스를 함께 진행하면 세션 기록을 2행으로 나눔. 서비스 지급은 SERVICE_PRICE×횟수 | `UpdateSession`, `Config.SERVICE_PRICE` | 구분 개념 유지. 기본 25000의 업무 정책과 혼합 금액 결함 확인 |
| R16 | 신규 INSERT의 ID가 반환된 경우에만 회원 잔여를 차감. 수정은 차감하지 않음 | `UpdateSession` 성공 분기 | 결함 수정 검토. 기존 자료 편집 정책 확인 |
| R17 | 기존 기록 더블클릭 시 횟수 입력 비활성화. 저장 시에는 신규와 같은 현재 잔여 검사 수행 | `Grid_CellDoubleClick` SESSION 분기, `UpdateSession` | 정책 확인/결함 수정. 잔여 0인 기록 수정 불가 경로 |
| R18 | 삭제 시 횟수 복원 여부를 사용자에게 묻고, 복원은 회원 현재 상품과 기록 상품이 같을 때만 허용 | `DeleteSession:180` | 선택 복원·상품 일치 의미 유지. 원자성과 삭제 회원 예외 보완 필요 |
| R19 | 삭제 복원은 IsService에 따라 일반/서비스에 해당 기록 횟수를 더함 | `DeleteSession` | 유지 |
| R20 | 수업 중복 검사 없음. 숨겨진 월 복사는 중복·잔여 차감 없이 INSERT | `UpdateSession`, `LoadBeforeSession:129`, Designer:285 | 정책 확인. 숨김 기능을 필수 업무로 간주하지 않음 |
| R21 | 세션·매출 목록은 트레이너+연월 기준, 정산 기간 검색은 시작 월 1일~종료 월 말일 | `SessionList.GetList`, `TrainerSalesList.GetList`, `frmSessionStats.LoadData:194` | 월 단위 의미 유지 |
| R22 | 연간 월 평균은 데이터가 있는 개월 수가 아니라 항상 12로 나눔 | `frmSessionStats.LoadMonthlyData:123` | 정책 확인 |
| R23 | 매출 처리기에는 트레이너·금액 검사가 있으나 미바인딩 콤보의 null 접근이 검사보다 먼저 발생; 중복검사 및 회원 결제 연결 없음 | `frmTrainerSales.UpdateSales:148` | 수동 매출 개념 유지 |
| R24 | 사용 중 락커의 소유자 변경은 먼저 마감 필요 | `popLocker.LoadOwner` | 유지 |
| R25 | 동일 소유자 유형+ID가 이미 락커를 쓰면 저장 거부. 자신의 현재 락커도 제외 안 함 | `popLocker.SaveLocker`, `LockerList.GetByOwnerId:546` | 1인 1락커 의도는 정책 확인. 연장 차단 결함 수정 |
| R26 | 무기한은 EndDate=DateTime.MinValue. 만료 후 빨강, 오늘~7일 이내 노랑. 자동 반납 없음 | `popLocker.SaveLocker`, `frmMain.SetLockerColor`, `UCLocker.SetLockerOwner` | 기간·경고 의미 유지, 날짜 표현은 재검토 |
| R27 | 락커 마감은 OwnerId=0, OwnerName 빈 문자열, OwnerType=NONE으로 변경. 날짜는 남음 | `popLocker.UseEnd` | 현재 상태 전환 의미 유지. 이용 이력 정책 확인 |
| R28 | 자산은 이름·유형 필수, 잔액 빈칸은 0. 직접 잔액 수정 가능 | `frmFinanceSetting.UpdateAccount:341` | 정책 확인 |
| R29 | 거래는 자산·분류(이체는 도착 자산)·금액 필수. 입력 유형에 따라 선택 분류 변경 | `frmFinanceInput.UpdateTransaction:263`, `SetComboCategory:213` | 유지 |
| R30 | 현금/은행 수입은 잔액 증가·지출은 감소, 신용카드는 반대 부호 | `Account.AddBalance:47/MinusBalance:59` | 유지 |
| R31 | 거래 수정은 원거래 잔액부터 역처리, 삭제는 논리삭제 후 잔액 역처리 | `frmFinanceInput.UpdateTransaction/DeleteTransaction` | 역처리 의미 유지. 부분 실패·이체 저장 결함 수정 |
| R32 | 고정 거래는 이체 미지원. 이름·금액·유형·자산·분류 필수 | `frmFinanceSetting.UpdateFixed:403` | 현재 지원 범위 유지, 실행일 검증 결함 수정 |
| R33 | 고정 거래 대상은 마지막 입력 연도≤현재 연도 AND 월≤현재 월 AND 마지막 일<지정일 AND 지정일≤오늘 | `FixedTransaction.CheckLastInputDate:73` | 결함 수정. 이 식은 매월 반복을 보장하지 않음 |
| R34 | 순자산 = 비카드 잔액 합 − 카드 잔액 합 | `frmFinanceMain.UpdateBalaceText:77` | 유지 |
| R35 | 관리자 메뉴는 센터 ID 1 + 계정 ID admin일 때만 표시 | `frmMain` 생성자, Designer:175 | 정책 확인. 보안 경계로 그대로 재사용 불가 |

시간대는 서버 설정값이 아니라 실행 PC의 `DateTime.Now`에 의존한다. 수업/매출의 저장 날짜는 datetime이지만 화면 조회는 월 중심이다. 예약 중복금지, 결제 완료 후 계약 활성화, 회원권 만료 시 사용불가 같은 규칙은 확인되지 않았다.

역검증 주의: R21의 매출 필터는 구현된 조회 조건이며 개인 매출등록 화면의 정상 실행을 보장하지 않는다(K37). R23의 필수값 검증은 현재 초기화 결함을 통과한 경우에만 도달한다. Save의 true를 데이터 변경 확정 규칙으로 사용하지 않는다(K38).
