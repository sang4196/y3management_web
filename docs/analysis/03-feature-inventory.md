# 03. 전체 기능 목록
> 역검증 기준: 아래 처리 로직과 결과는 이벤트 내부의 의도 및 성공 분기를 기술한다. MariaDB.Save/MultiSave는 ExecuteNonQuery의 영향 행 수를 검사하지 않으므로 true만으로 DB 변경을 보장하지 않는다. 특히 F20과 F22–F25의 실행 제약을 함께 읽어야 한다. 근거: Cores/Database/MariaDB.cs:109,135.


정상 메뉴·이벤트 경로의 업무를 기능 단위로 기록한다. 운영자는 Admin 로그인 사용자의 업무상 명칭(추정)이다. 별도 회원/트레이너 로그인 기능은 없다. “시도”는 버튼/처리 경로는 있으나 코드 제약으로 의도대로 수행되지 않을 수 있음을 뜻한다.

관련 DB 표기는 읽기와 쓰기를 포함한다. 모든 경로는 Y3/Y3 아래이며 모델·SQL의 공통 후속 호출은 [05](05-database-model.md)를 참조한다. 필드 초기화 버튼은 업무 데이터 삭제가 아니며 각 화면의 입력 초기화다.

## F01. 로그인

- **기능명:** 로그인
- **사용자:** 비로그인 사용자
- **진입 화면:** 로그인
- **입력값:** 센터, ID, 암호
- **처리 로직:** 센터/ID의 활성 계정 조회 후 DPAPI 복호화 비교; 접속일 저장, 현재 계정/센터 설정, 데이터/폼 초기화, 고정 거래 검사
- **관련 DB 테이블:** admin, gym 및 센터 업무 테이블
- **결과:** 메인 화면 표시
- **예외/제약사항:** 불일치 시 오류. 실패 횟수 제한/잠금 미확인
- **관련 코드 위치:** [Forms/frmLock.cs](../../Y3/Y3/Forms/frmLock.cs) — Login(89행)

## F02. 신규 회원 등록

- **기능명:** 신규 회원 등록
- **사용자:** 로그인 운영자
- **진입 화면:** 설정 → 유저관리
- **입력값:** 이름, 전화·생일 또는 없음, PT 종류, 일반/서비스 잔여, 담당, 메모
- **처리 로직:** 회원 모델 생성, 전화 포맷, 없음 생일 MinValue, 상품 미선택이면 횟수 0, INSERT
- **관련 DB 테이블:** user; 선택 trainer/session_price; 조회 locker
- **결과:** 회원 목록 갱신
- **예외/제약사항:** 이름 필수, 없음 체크 안 한 전화는 10자리 이상. 계약·결제 생성 없음
- **관련 코드 위치:** [Forms/Setting/frmSettingUser.cs](../../Y3/Y3/Forms/Setting/frmSettingUser.cs) — UpdateUser(371행)

## F03. 회원 개인정보 변경

- **기능명:** 회원 개인정보 변경
- **사용자:** 로그인 운영자
- **진입 화면:** 설정 → 유저관리
- **입력값:** 기존 행, 이름·연락처·생일·메모
- **처리 로직:** 더블클릭으로 로드 후 기존 모델 수정·UPDATE
- **관련 DB 테이블:** user
- **결과:** 변경된 회원 목록
- **예외/제약사항:** 이름·전화 검증은 신규와 동일. 실패 전 메모리 변경 가능
- **관련 코드 위치:** [Forms/Setting/frmSettingUser.cs](../../Y3/Y3/Forms/Setting/frmSettingUser.cs) — Grid_List_CellDoubleClick(202행), UpdateUser(371행)

## F04. 회원 PT 종류·담당·잔여 횟수 설정/조정

- **기능명:** 회원 PT 종류·담당·잔여 횟수 설정/조정
- **사용자:** 로그인 운영자
- **진입 화면:** 설정 → 유저관리
- **입력값:** 회원, 종류, 담당 트레이너, 일반/서비스 잔여
- **처리 로직:** 기존 필드를 입력값으로 덮어씀; 종류 미선택은 횟수 0
- **관련 DB 테이블:** user; trainer; session_price
- **결과:** 현재 상품/담당/잔여 변경
- **예외/제약사항:** 계약 이력·횟수 변경 원장·결제 조건 없음. 이전 상품 이력 보존 안 됨
- **관련 코드 위치:** [Forms/Setting/frmSettingUser.cs](../../Y3/Y3/Forms/Setting/frmSettingUser.cs) — UpdateUser(371행)

## F05. 회원 검색·목록 조회

- **기능명:** 회원 검색·목록 조회
- **사용자:** 로그인 운영자
- **진입 화면:** 설정 → 유저관리
- **입력값:** 이름 또는 전화 일부
- **처리 로직:** GetDataTable로 DB 재조회 후 Contains 필터, 검색 결과는 Id 내림차순
- **관련 DB 테이블:** user LEFT JOIN locker
- **결과:** 회원 목록
- **예외/제약사항:** 빈 검색은 전체. 일반 회원 화면은 잔여 0도 조회
- **관련 코드 위치:** [Forms/Setting/frmSettingUser.cs](../../Y3/Y3/Forms/Setting/frmSettingUser.cs) — LoadUserData(333행)

## F06. 회원 삭제

- **기능명:** 회원 삭제
- **사용자:** 로그인 운영자
- **진입 화면:** 설정 → 유저관리
- **입력값:** 선택 회원 ID, 삭제 확인
- **처리 로직:** useflag=0 저장 후 목록 갱신
- **관련 DB 테이블:** user
- **결과:** 활성 목록에서 제외
- **예외/제약사항:** 세션·락커 참조 검사/함께 삭제 없음
- **관련 코드 위치:** [Forms/Setting/frmSettingUser.cs](../../Y3/Y3/Forms/Setting/frmSettingUser.cs) — DeleteUser(464행)

## F07. 트레이너 신규 등록

- **기능명:** 트레이너 신규 등록
- **사용자:** 로그인 운영자
- **진입 화면:** 설정 → 유저관리
- **입력값:** 이름, 기본급, 전화·생일 또는 없음, 메모
- **처리 로직:** 모델 생성 후 INSERT, 콤보 갱신 이벤트
- **관련 DB 테이블:** trainer
- **결과:** 트레이너 목록과 선택 목록 갱신
- **예외/제약사항:** 이름·기본급 필수, 전화 없음 아닐 때 최소 10자리
- **관련 코드 위치:** [Forms/Setting/frmSettingUser.cs](../../Y3/Y3/Forms/Setting/frmSettingUser.cs) — UpdateTrainer(422행)

## F08. 트레이너 정보·기본급 변경

- **기능명:** 트레이너 정보·기본급 변경
- **사용자:** 로그인 운영자
- **진입 화면:** 설정 → 유저관리
- **입력값:** 기존 행, 인적정보, 기본급
- **처리 로직:** 기존 모델 UPDATE, 목록/콤보 갱신
- **관련 DB 테이블:** trainer
- **결과:** 현재 직원 정보 변경
- **예외/제약사항:** 급여 지급 또는 과거 정산 변경 기능 아님
- **관련 코드 위치:** [Forms/Setting/frmSettingUser.cs](../../Y3/Y3/Forms/Setting/frmSettingUser.cs) — UpdateTrainer(422행), Grid_List_CellDoubleClick(202행)

## F09. 트레이너 목록 조회

- **기능명:** 트레이너 목록 조회
- **사용자:** 로그인 운영자
- **진입 화면:** 설정 → 유저관리
- **입력값:** 화면 열기
- **처리 로직:** GetDataTable이 DB 재조회
- **관련 DB 테이블:** trainer LEFT JOIN locker
- **결과:** 트레이너 목록
- **예외/제약사항:** 별도 트레이너 텍스트 검색은 없음. locker owner_type 불일치 위험
- **관련 코드 위치:** [Forms/Setting/frmSettingUser.cs](../../Y3/Y3/Forms/Setting/frmSettingUser.cs) — LoadTrainerData(356행)

## F10. 트레이너 삭제

- **기능명:** 트레이너 삭제
- **사용자:** 로그인 운영자
- **진입 화면:** 설정 → 유저관리
- **입력값:** 선택 트레이너, 확인
- **처리 로직:** useflag=0, 목록·콤보 갱신
- **관련 DB 테이블:** trainer
- **결과:** 활성 목록에서 제외
- **예외/제약사항:** 담당 회원·과거 수업·매출 처리/삭제 차단 없음
- **관련 코드 위치:** [Forms/Setting/frmSettingUser.cs](../../Y3/Y3/Forms/Setting/frmSettingUser.cs) — DeleteTrainer(485행)

## F11. PT 종류와 기본 지급단가 등록

- **기능명:** PT 종류와 기본 지급단가 등록
- **사용자:** 로그인 운영자
- **진입 화면:** 설정 → 세션관련
- **입력값:** 이름, 가격, 지급률, 공제율
- **처리 로직:** 키 입력 시 공제 후 지급률 계산, 중복 이름 검사 후 INSERT
- **관련 DB 테이블:** session_price
- **결과:** 상품/지급단가 목록과 콤보 갱신
- **예외/제약사항:** 4항목 필수. 비율 범위 검사 없음
- **관련 코드 위치:** [Forms/Setting/frmSettingSession.cs](../../Y3/Y3/Forms/Setting/frmSettingSession.cs) — TxtPrice_KeyUp(155행), UpdateSessionPrice(261행)

## F12. PT 종류·정산 단가 변경 시도

- **기능명:** PT 종류·정산 단가 변경 시도
- **사용자:** 로그인 운영자
- **진입 화면:** 설정 → 세션관련
- **입력값:** 기존 종류, 이름·가격·지급률·공제율
- **처리 로직:** 기존 ID UPDATE 경로 있으나 이름 중복 검사 먼저 수행
- **관련 DB 테이블:** session_price
- **결과:** 검증 통과 시 변경
- **예외/제약사항:** 기존 이름을 유지하면 자신과 중복되어 거부. 정상 수정 완성 기능으로 단정하지 않음
- **관련 코드 위치:** [Forms/Setting/frmSettingSession.cs](../../Y3/Y3/Forms/Setting/frmSettingSession.cs) — UpdateSessionPrice(261행)

## F13. PT 종류 조회·삭제

- **기능명:** PT 종류 조회·삭제
- **사용자:** 로그인 운영자
- **진입 화면:** 설정 → 세션관련
- **입력값:** 종류 행, 삭제 확인
- **처리 로직:** 목록 조회, 삭제 시 useflag=0 및 콤보 갱신
- **관련 DB 테이블:** session_price
- **결과:** 활성 종류 목록 변경
- **예외/제약사항:** 사용 중 회원/수업 참조 차단 없음
- **관련 코드 위치:** [Forms/Setting/frmSettingSession.cs](../../Y3/Y3/Forms/Setting/frmSettingSession.cs) — LoadSessionData(250행), DeleteSessionPrice(354행)

## F14. 트레이너별 개별 지급률 등록

- **기능명:** 트레이너별 개별 지급률 등록
- **사용자:** 로그인 운영자
- **진입 화면:** 설정 → 세션관련
- **입력값:** 트레이너, PT 종류, 지급률
- **처리 로직:** 종류×트레이너 중복 확인 후 INSERT
- **관련 DB 테이블:** session_trainer; trainer; session_price
- **결과:** 지급률 재정의
- **예외/제약사항:** 3항목 필수. 같은 조합 거부
- **관련 코드 위치:** [Forms/Setting/frmSettingSession.cs](../../Y3/Y3/Forms/Setting/frmSettingSession.cs) — UpdateST(313행)

## F15. 개별 지급률 변경 시도

- **기능명:** 개별 지급률 변경 시도
- **사용자:** 로그인 운영자
- **진입 화면:** 설정 → 세션관련
- **입력값:** 기존 행, 조합, 지급률
- **처리 로직:** 기존 ID UPDATE 경로; 중복 검사는 수정 전 수행
- **관련 DB 테이블:** session_trainer
- **결과:** 조합을 변경해 중복 없으면 갱신 가능
- **예외/제약사항:** 기존 조합 유지 수정은 자기 중복으로 차단
- **관련 코드 위치:** [Forms/Setting/frmSettingSession.cs](../../Y3/Y3/Forms/Setting/frmSettingSession.cs) — UpdateST(313행)

## F16. 개별 지급률 조회·삭제

- **기능명:** 개별 지급률 조회·삭제
- **사용자:** 로그인 운영자
- **진입 화면:** 설정 → 세션관련
- **입력값:** 행, 삭제 확인
- **처리 로직:** 목록 조회 및 useflag=0
- **관련 DB 테이블:** session_trainer
- **결과:** 공통 지급단가로 돌아갈 조건 형성
- **예외/제약사항:** 이미 저장된 SessionTotalPrice 자동 재산정 없음
- **관련 코드 위치:** [Forms/Setting/frmSettingSession.cs](../../Y3/Y3/Forms/Setting/frmSettingSession.cs) — LoadSTData(256행), DeleteST(376행)

## F17. 진행 대상 회원 검색·선택

- **기능명:** 진행 대상 회원 검색·선택
- **사용자:** 로그인 운영자
- **진입 화면:** 세션정산 → 세션진행 등록
- **입력값:** 트레이너, 이름/전화 일부, 회원 행
- **처리 로직:** DB 재조회 후 담당·양수 잔여 필터; 종류 존재 확인; 개별 지급률 또는 기본 지급단가 표시
- **관련 DB 테이블:** user; locker JOIN; trainer; session_price; session_trainer
- **결과:** 진행 입력 대상과 단가 표시
- **예외/제약사항:** 트레이너 선택 필요, 상품 없는 회원/삭제 상품 거부
- **관련 코드 위치:** [Forms/Session/frmSessionRegister.cs](../../Y3/Y3/Forms/Session/frmSessionRegister.cs) — LoadUserData(501행), Grid_CellDoubleClick(356행)

## F18. PT 진행 기록 및 잔여 횟수 차감

- **기능명:** PT 진행 기록 및 잔여 횟수 차감
- **사용자:** 로그인 운영자
- **진입 화면:** 세션정산 → 세션진행 등록
- **입력값:** 선택 회원, 트레이너, 월, 횟수
- **처리 로직:** 1 이상/총잔여 이하 검사; 일반 우선 기록, 필요 시 서비스 분할; MultiSave 후 신규 ID면 별도 회원 차감 저장
- **관련 DB 테이블:** session, user; session_price/session_trainer 참조
- **결과:** 진행 기록·잔여 목록 갱신
- **예외/제약사항:** 기록+차감 원자성 없음. 혼합 일반 금액 과대 경로. 시간대 중복 검사 없음
- **관련 코드 위치:** [Forms/Session/frmSessionRegister.cs](../../Y3/Y3/Forms/Session/frmSessionRegister.cs) — UpdateSession(229행)

## F19. 트레이너별 월 진행 내역 조회

- **기능명:** 트레이너별 월 진행 내역 조회
- **사용자:** 로그인 운영자
- **진입 화면:** 세션정산 → 세션진행 등록
- **입력값:** 트레이너, 월
- **처리 로직:** 캐시를 트레이너+연월로 필터; 서비스 지급금액 셀 노랑
- **관련 DB 테이블:** session
- **결과:** 월별 진행 기록
- **예외/제약사항:** 트레이너 미선택은 빈 목록. 날짜 형식 yyyy-MM
- **관련 코드 위치:** [Forms/Session/frmSessionRegister.cs](../../Y3/Y3/Forms/Session/frmSessionRegister.cs) — LoadSessionData(524행)

## F20. 기존 진행 기록 수정 시도

- **기능명:** 기존 진행 기록 수정 시도
- **사용자:** 로그인 운영자
- **진입 화면:** 세션정산 → 세션진행 등록
- **입력값:** 기존 행 더블클릭, 표시된 기록
- **처리 로직:** 횟수 입력 비활성화; 현재 잔여 검증 후 기존 ID로 UPDATE
- **관련 DB 테이블:** session; user 검증
- **결과:** 검증 통과 후 UPDATE 시도; 새 Session 객체에 GymNo를 넣지 않아 일반적인 0이 아닌 센터에서는 변경 행이 없을 수 있음
- **예외/제약사항:** 회원 횟수 재조정 없음. 현재 잔여가 적으면 수정 거부. 서비스 구분 재계산 위험
- **관련 코드 위치:** [Forms/Session/frmSessionRegister.cs](../../Y3/Y3/Forms/Session/frmSessionRegister.cs) — Grid_CellDoubleClick(356행), UpdateSession(229행)

## F21. 진행 기록 삭제 및 선택적 횟수 복원

- **기능명:** 진행 기록 삭제 및 선택적 횟수 복원
- **사용자:** 로그인 운영자
- **진입 화면:** 세션정산 → 세션진행 등록
- **입력값:** 기존 기록, 삭제 확인, 복원 여부
- **처리 로직:** 복원 선택 시 회원 현재 상품 일치 검사; 논리삭제 후 IsService에 맞춰 횟수 가산·별도 Save
- **관련 DB 테이블:** session, user
- **결과:** 기록 숨김, 선택 시 회원 잔여 증가
- **예외/제약사항:** 상품 불일치+복원 선택 시 삭제 거부. 비활성 회원 null 위험. 환불 아님
- **관련 코드 위치:** [Forms/Session/frmSessionRegister.cs](../../Y3/Y3/Forms/Session/frmSessionRegister.cs) — DeleteSession(180행)

## F22. 트레이너 매출 신규 기록

- **기능명:** 트레이너 매출 신규 기록
- **사용자:** 로그인 운영자
- **진입 화면:** 세션정산 → 개인 매출등록
- **입력값:** 트레이너, 기준 월/날짜, 금액, 메모
- **처리 로직:** 필수값 검사 후 trainer_sales INSERT
- **관련 DB 테이블:** trainer_sales; trainer
- **결과:** 기본 초기화 경로에서는 트레이너 선택·목록 조회가 차단됨; 아래 처리기는 조건 충족 시의 구현
- **예외/제약사항:** InitComboEvent 호출 누락으로 콤보가 미바인딩됨. UpdateSales는 필수검사 전에 SelectedValue.ToString()을 호출하여 null 예외 경로가 있음.  트레이너·금액 필수, 중복검사 없음. 고객 결제 연결 없음
- **관련 코드 위치:** Core.InitForm(80행), frmTrainerSales 생성자(28행)/InitComboEvent(52행)/LoadSalesData(114행);  [Forms/Session/frmTrainerSales.cs](../../Y3/Y3/Forms/Session/frmTrainerSales.cs) — UpdateSales(148행)

## F23. 트레이너 매출 수정

- **기능명:** 트레이너 매출 수정
- **사용자:** 로그인 운영자
- **진입 화면:** 세션정산 → 개인 매출등록
- **입력값:** 기존 행, 금액, 메모
- **처리 로직:** 기존 객체에 금액·트레이너·날짜·메모 덮어써 UPDATE
- **관련 DB 테이블:** trainer_sales
- **결과:** 기본 초기화 경로에서는 트레이너 선택·목록 조회가 차단됨; 아래 처리기는 조건 충족 시의 구현
- **예외/제약사항:** InitComboEvent 호출 누락으로 콤보가 미바인딩됨. UpdateSales는 필수검사 전에 SelectedValue.ToString()을 호출하여 null 예외 경로가 있음.  가계부/실제 결제 상태 변경 아님
- **관련 코드 위치:** Core.InitForm(80행), frmTrainerSales 생성자(28행)/InitComboEvent(52행)/LoadSalesData(114행);  [Forms/Session/frmTrainerSales.cs](../../Y3/Y3/Forms/Session/frmTrainerSales.cs) — UpdateSales(148행)

## F24. 트레이너 매출 삭제

- **기능명:** 트레이너 매출 삭제
- **사용자:** 로그인 운영자
- **진입 화면:** 세션정산 → 개인 매출등록
- **입력값:** 기존 행, 확인
- **처리 로직:** useflag=0
- **관련 DB 테이블:** trainer_sales
- **결과:** 기본 초기화 경로에서는 트레이너 선택·목록 조회가 차단됨; 아래 처리기는 조건 충족 시의 구현
- **예외/제약사항:** InitComboEvent 호출 누락으로 콤보가 미바인딩됨. UpdateSales는 필수검사 전에 SelectedValue.ToString()을 호출하여 null 예외 경로가 있음.  환불이나 수업 횟수 복원 없음
- **관련 코드 위치:** Core.InitForm(80행), frmTrainerSales 생성자(28행)/InitComboEvent(52행)/LoadSalesData(114행);  [Forms/Session/frmTrainerSales.cs](../../Y3/Y3/Forms/Session/frmTrainerSales.cs) — DeleteSales(128행)

## F25. 트레이너 월 매출 조회

- **기능명:** 트레이너 월 매출 조회
- **사용자:** 로그인 운영자
- **진입 화면:** 세션정산 → 개인 매출등록
- **입력값:** 트레이너, 월
- **처리 로직:** 캐시를 트레이너 ID와 연월로 필터
- **관련 DB 테이블:** trainer_sales
- **결과:** 기본 초기화 경로에서는 트레이너 선택·목록 조회가 차단됨; 아래 처리기는 조건 충족 시의 구현
- **예외/제약사항:** InitComboEvent 호출 누락으로 콤보가 미바인딩됨. UpdateSales는 필수검사 전에 SelectedValue.ToString()을 호출하여 null 예외 경로가 있음.  트레이너 미선택이면 조회하지 않음
- **관련 코드 위치:** Core.InitForm(80행), frmTrainerSales 생성자(28행)/InitComboEvent(52행)/LoadSalesData(114행);  [Forms/Session/frmTrainerSales.cs](../../Y3/Y3/Forms/Session/frmTrainerSales.cs) — LoadSalesData(114행)

## F26. 당월·지정 월 범위 세션 정산 조회

- **기능명:** 당월·지정 월 범위 세션 정산 조회
- **사용자:** 로그인 운영자
- **진입 화면:** 세션정산 → 세션현황
- **입력값:** 시작 월, 종료 월
- **처리 로직:** 현재 활성 트레이너별 진행 지급액·횟수 합산, 종류별 횟수 표시
- **관련 DB 테이블:** session; trainer; session_price
- **결과:** 트레이너별 기간 정산 표
- **예외/제약사항:** 검색은 월 첫날~마지막날로 확장. 수입은 지급액이며 기본급 가산 없음
- **관련 코드 위치:** [Forms/Session/frmSessionStats.cs](../../Y3/Y3/Forms/Session/frmSessionStats.cs) — LoadData(194행)

## F27. 연간 월별 수업수·지급액·매출 조회

- **기능명:** 연간 월별 수업수·지급액·매출 조회
- **사용자:** 로그인 운영자
- **진입 화면:** 세션정산 → 세션현황
- **입력값:** 연도
- **처리 로직:** 트레이너별 연간 기록 수집, 1~12월 분류, 합계/12 평균
- **관련 DB 테이블:** session; trainer_sales; trainer
- **결과:** 월별 수업수·수입·매출 표
- **예외/제약사항:** 비활성 트레이너 제외 가능. 평균은 12개월 고정. 정수 표 컬럼
- **관련 코드 위치:** [Forms/Session/frmSessionStats.cs](../../Y3/Y3/Forms/Session/frmSessionStats.cs) — LoadMonthlyData(123행)

## F28. 회원/트레이너에게 락커 배정

- **기능명:** 회원/트레이너에게 락커 배정
- **사용자:** 로그인 운영자
- **진입 화면:** 메인 → 락커 설정
- **입력값:** 빈 락커 번호, 소유자 선택, 종료일/무기한
- **처리 로직:** 같은 유형+소유자 기존 사용 검사, 신규/기존 locker 저장, 타일 갱신
- **관련 DB 테이블:** locker; user 또는 trainer
- **결과:** 현재 소유자·기한 표시
- **예외/제약사항:** 사용 중 소유자 변경은 마감 선행. 소유자 미선택·시작일 설정 검증 부족
- **관련 코드 위치:** [Forms/Popup/popLocker.cs](../../Y3/Y3/Forms/Popup/popLocker.cs) — LoadOwner(167행), SaveLocker(207행)

## F29. 락커 기간 변경·연장 시도

- **기능명:** 락커 기간 변경·연장 시도
- **사용자:** 로그인 운영자
- **진입 화면:** 메인 → 락커 설정
- **입력값:** 종료일 직접 입력 또는 1/3/6/12/+1개월
- **처리 로직:** 버튼이 날짜 계산; 저장은 배정과 같은 중복검사 후 UPDATE
- **관련 DB 테이블:** locker
- **결과:** 검증 통과 시 종료일 갱신
- **예외/제약사항:** 자기 락커 제외가 없어 정상 사용자의 연장도 차단될 수 있음. 버튼은 현재 사용 시 원래 END_DATE 기준
- **관련 코드 위치:** [Forms/Popup/popLocker.cs](../../Y3/Y3/Forms/Popup/popLocker.cs) — BtnDt_Click(105행), SaveLocker(207행)

## F30. 락커 무기한 설정

- **기능명:** 락커 무기한 설정
- **사용자:** 로그인 운영자
- **진입 화면:** 메인 → 락커 설정
- **입력값:** 무기한 체크
- **처리 로직:** 날짜/기간 버튼 비활성화; 저장 시 EndDate=MinValue
- **관련 DB 테이블:** locker
- **결과:** 기한없음으로 표시
- **예외/제약사항:** 기존 사용 중 저장은 동일 중복검사 영향. DB 날짜 호환 미검증
- **관련 코드 위치:** [Forms/Popup/popLocker.cs](../../Y3/Y3/Forms/Popup/popLocker.cs) — ChkNoLimit_CheckedChanged(148행), SaveLocker(207행)

## F31. 락커 사용마감

- **기능명:** 락커 사용마감
- **사용자:** 로그인 운영자
- **진입 화면:** 메인 → 락커 설정
- **입력값:** 사용 중 락커, 확인
- **처리 로직:** 기간 남음 여부에 따라 확인; OwnerId=0, 이름 빈값, 타입 NONE UPDATE
- **관련 DB 테이블:** locker
- **결과:** 빈 락커 타일로 전환
- **예외/제약사항:** 기록 삭제 아님, 날짜는 남음. 결제/환불 없음
- **관련 코드 위치:** [Forms/Popup/popLocker.cs](../../Y3/Y3/Forms/Popup/popLocker.cs) — UseEnd(232행)

## F32. 락커 소유자 검색·선택

- **기능명:** 락커 소유자 검색·선택
- **사용자:** 로그인 운영자
- **진입 화면:** 락커 설정 → 회원/트레이너 선택
- **입력값:** 유형, 회원 검색어, 대상 행
- **처리 로직:** 회원은 이름/전화 필터, 트레이너는 전체 목록; 선택 또는 더블클릭으로 ID/NAME 반환
- **관련 DB 테이블:** user 또는 trainer; locker JOIN
- **결과:** 호출 팝업에 대상 전달
- **예외/제약사항:** 트레이너 모드 검색 패널 숨김. 무선택/헤더행 보호 부족
- **관련 코드 위치:** [Forms/Popup/popUser.cs](../../Y3/Y3/Forms/Popup/popUser.cs) — LoadUserData(145행), LoadTrainerData(140행), BtnChoose_Click(73행), Grid_List_CellDoubleClick(56행)

## F33. 락커 현황·만료 상태 조회

- **기능명:** 락커 현황·만료 상태 조회
- **사용자:** 로그인 운영자
- **진입 화면:** 메인화면
- **입력값:** 메인 진입
- **처리 로직:** 메인 폼 생성 시 설정 개수로 타일 생성, 캐시 소유자 표시, 렌더링 당시 오늘 이후 7일 이내 노랑/과거 빨강
- **관련 DB 테이블:** locker
- **결과:** 번호·소유자·기한·만료 경고
- **예외/제약사항:** 자동 마감 없음. PC 날짜 기준이며 날짜 변경이나 메인 복귀만으로 색상을 재계산하지 않음.  DB 번호가 설정 범위를 벗어나면 인덱스 위험
- **관련 코드 위치:** [Forms/frmMain.cs](../../Y3/Y3/Forms/frmMain.cs) — MakeLocker(450행), SetLockerColor(499행)

## F34. 락커 번호·소유자 글꼴 크기 조절

- **기능명:** 락커 번호·소유자 글꼴 크기 조절
- **사용자:** 로그인 운영자
- **진입 화면:** 메인화면
- **입력값:** 각 ± 버튼
- **처리 로직:** 0.25씩 Config 값 조정, JSON 저장, 모든 타일 갱신
- **관련 DB 테이블:** 없음; 로컬 Config.json
- **결과:** 글꼴 크기 변경·유지
- **예외/제약사항:** 최소/최대 크기 제한 미확인
- **관련 코드 위치:** [Forms/frmMain.cs](../../Y3/Y3/Forms/frmMain.cs) — BtnLockerFont_Click(132행)

## F35. 업무 메뉴 이동·메인 복귀

- **기능명:** 업무 메뉴 이동·메인 복귀
- **사용자:** 로그인 운영자
- **진입 화면:** 메인화면
- **입력값:** 주메뉴/하위메뉴
- **처리 로직:** Tag로 자식 폼 선택; 기존 폼 Hide, 선택 폼을 패널에 표시
- **관련 DB 테이블:** 직접 저장 없음; 각 화면 조회 참조
- **결과:** 선택한 업무 화면
- **예외/제약사항:** 폼 인스턴스와 입력 상태가 유지되는 구조. 관리자 메뉴만 조건 표시
- **관련 코드 위치:** [Forms/frmMain.cs](../../Y3/Y3/Forms/frmMain.cs) — BtnMenu_Click(233행), BtnSub_Click(172행), openChildForm(581행)

## F36. 창 최소화·이동·프로그램 종료

- **기능명:** 창 최소화·이동·프로그램 종료
- **사용자:** 로그인 운영자
- **진입 화면:** 메인화면
- **입력값:** 최소화, 로고 드래그, 종료 메뉴
- **처리 로직:** 최소화 상태, user32 창이동, 종료 확인 후 설정 저장/Application.Exit
- **관련 DB 테이블:** 없음; 로컬 설정
- **결과:** 창 상태 변경 또는 종료
- **예외/제약사항:** 로그아웃 후 다른 계정 로그인 흐름은 미확인
- **관련 코드 위치:** [Forms/frmMain.cs](../../Y3/Y3/Forms/frmMain.cs) — Btn_minimize_Click(161행), PictureBox1_MouseDown(166행), BtnMenu_Click(233행)

## F37. 가계부 월 거래 조회

- **기능명:** 가계부 월 거래 조회
- **사용자:** 로그인 운영자
- **진입 화면:** 가계부 → 내역
- **입력값:** 검색 월
- **처리 로직:** 월 1일 이상/다음달 1일 미만 SQL; 자산/분류명 JOIN, 날짜 정렬, 유형별 색
- **관련 DB 테이블:** finance_transaction, finance_account, finance_category
- **결과:** 월 내역 표시
- **예외/제약사항:** 세션 매출 또는 실제 결제내역 자동 합산 아님
- **관련 코드 위치:** [Forms/Finance/frmFinanceInput.cs](../../Y3/Y3/Forms/Finance/frmFinanceInput.cs) — LoadData(161행)

## F38. 수입 장부 기록·자산 반영

- **기능명:** 수입 장부 기록·자산 반영
- **사용자:** 로그인 운영자
- **진입 화면:** 가계부 → 내역
- **입력값:** 수입 유형, 자산, 수입분류, 금액, 일자, 메모
- **처리 로직:** 거래 INSERT 후 UpdateAccount; 일반 자산 가산/카드 차감
- **관련 DB 테이블:** finance_transaction, finance_account; finance_category
- **결과:** 장부와 잔액 변경
- **예외/제약사항:** 자산·분류·금액 필수. 장부+잔액 별도 커밋
- **관련 코드 위치:** [Forms/Finance/frmFinanceInput.cs](../../Y3/Y3/Forms/Finance/frmFinanceInput.cs) — UpdateTransaction(263행), UpdateAccount(318행)

## F39. 지출 장부 기록·자산 반영

- **기능명:** 지출 장부 기록·자산 반영
- **사용자:** 로그인 운영자
- **진입 화면:** 가계부 → 내역
- **입력값:** 지출 유형, 자산, 지출분류, 금액, 일자, 메모
- **처리 로직:** 거래 INSERT 후 일반 자산 차감/카드 증가
- **관련 DB 테이블:** finance_transaction, finance_account; finance_category
- **결과:** 장부와 잔액 변경
- **예외/제약사항:** 잔액 부족 검사 미확인. 실지급 API 없음
- **관련 코드 위치:** [Forms/Finance/frmFinanceInput.cs](../../Y3/Y3/Forms/Finance/frmFinanceInput.cs) — UpdateTransaction(263행), UpdateAccount(318행)

## F40. 자산 간 이체 기록

- **기능명:** 자산 간 이체 기록
- **사용자:** 로그인 운영자
- **진입 화면:** 가계부 → 내역
- **입력값:** 이체 유형, 출발/도착 자산, 금액, 날짜, 메모
- **처리 로직:** CategoryId에 도착 자산 ID, 거래 저장 후 양쪽 메모리 잔액 변경과 저장 시도
- **관련 DB 테이블:** finance_transaction, finance_account
- **결과:** 이체 기록과 잔액 변경 시도
- **예외/제약사항:** OR 단락으로 출발 Save 성공 시 도착 Save 생략. 동일 자산 금지 미확인
- **관련 코드 위치:** [Forms/Finance/frmFinanceInput.cs](../../Y3/Y3/Forms/Finance/frmFinanceInput.cs) — UpdateTransaction(263행), UpdateAccount(318행), SetComboCategory(213행)

## F41. 기존 거래 수정과 잔액 재반영

- **기능명:** 기존 거래 수정과 잔액 재반영
- **사용자:** 로그인 운영자
- **진입 화면:** 가계부 → 내역
- **입력값:** 기존 행, 새 유형·자산·분류·금액·날짜·메모
- **처리 로직:** Clone의 잔액을 먼저 역처리, 거래 UPDATE 후 새 잔액 반영
- **관련 DB 테이블:** finance_transaction, finance_account
- **결과:** 거래 수정
- **예외/제약사항:** 중간 실패 시 전체 롤백 없음. 이체 역처리도 동일 결함
- **관련 코드 위치:** [Forms/Finance/frmFinanceInput.cs](../../Y3/Y3/Forms/Finance/frmFinanceInput.cs) — UpdateTransaction(263행)

## F42. 거래 삭제와 잔액 역처리

- **기능명:** 거래 삭제와 잔액 역처리
- **사용자:** 로그인 운영자
- **진입 화면:** 가계부 → 내역
- **입력값:** 선택 거래, 삭제 확인
- **처리 로직:** useflag=0 저장 후 기존 거래 효과 역처리
- **관련 DB 테이블:** finance_transaction, finance_account
- **결과:** 활성 거래 숨김, 잔액 복원 시도
- **예외/제약사항:** 카드 승인취소/고객 환불 아님. 역처리 실패가 삭제 취소하지 않음
- **관련 코드 위치:** [Forms/Finance/frmFinanceInput.cs](../../Y3/Y3/Forms/Finance/frmFinanceInput.cs) — DeleteTransaction(241행), UpdateAccount(318행)

## F43. 자산 신규 등록

- **기능명:** 자산 신규 등록
- **사용자:** 로그인 운영자
- **진입 화면:** 가계부 → 설정
- **입력값:** 이름, 현금/은행/신용카드 유형, 초기 잔액
- **처리 로직:** 빈 잔액은 0; INSERT 후 콤보 갱신
- **관련 DB 테이블:** finance_account
- **결과:** 장부 자산 추가
- **예외/제약사항:** 이름·유형 필수. 실제 금융계좌 연결 아님
- **관련 코드 위치:** [Forms/Finance/frmFinanceSetting.cs](../../Y3/Y3/Forms/Finance/frmFinanceSetting.cs) — UpdateAccount(341행)

## F44. 자산 이름·유형·잔액 직접 변경

- **기능명:** 자산 이름·유형·잔액 직접 변경
- **사용자:** 로그인 운영자
- **진입 화면:** 가계부 → 설정
- **입력값:** 기존 자산 행, 이름·유형·잔액
- **처리 로직:** 기존 모델 UPDATE
- **관련 DB 테이블:** finance_account
- **결과:** 자산 값 변경
- **예외/제약사항:** 거래 원장에 조정 내역을 추가하지 않음
- **관련 코드 위치:** [Forms/Finance/frmFinanceSetting.cs](../../Y3/Y3/Forms/Finance/frmFinanceSetting.cs) — UpdateAccount(341행)

## F45. 자산 목록 조회·삭제

- **기능명:** 자산 목록 조회·삭제
- **사용자:** 로그인 운영자
- **진입 화면:** 가계부 → 설정
- **입력값:** 행, 삭제 확인
- **처리 로직:** 조회, useflag=0 후 콤보 갱신
- **관련 DB 테이블:** finance_account
- **결과:** 활성 자산 제외
- **예외/제약사항:** 기존 거래/고정거래 참조검사 미확인
- **관련 코드 위치:** [Forms/Finance/frmFinanceSetting.cs](../../Y3/Y3/Forms/Finance/frmFinanceSetting.cs) — LoadAccountData(294행), DeleteAccount(447행)

## F46. 거래 분류 신규 등록

- **기능명:** 거래 분류 신규 등록
- **사용자:** 로그인 운영자
- **진입 화면:** 가계부 → 설정
- **입력값:** 이름, 거래유형, 메모
- **처리 로직:** 필수값 검사, INSERT
- **관련 DB 테이블:** finance_category
- **결과:** 설정 목록 갱신; 거래 입력의 분류 콤보는 유형 변경 등 SetComboCategory 재호출 후 반영
- **예외/제약사항:** 이름·유형 필수, 중복 이름 검사 없음
- **관련 코드 위치:** [Forms/Finance/frmFinanceSetting.cs](../../Y3/Y3/Forms/Finance/frmFinanceSetting.cs) — UpdateCategory(372행)

## F47. 거래 분류 변경

- **기능명:** 거래 분류 변경
- **사용자:** 로그인 운영자
- **진입 화면:** 가계부 → 설정
- **입력값:** 기존 분류, 이름·유형·메모
- **처리 로직:** 기존 모델 UPDATE 및 콤보 갱신 이벤트 호출 시도; 수신 등록은 주석 처리되어 즉시 전파되지 않음
- **관련 DB 테이블:** finance_category
- **결과:** 현재 분류 변경
- **예외/제약사항:** 기존 거래와 변경 유형 일치 검증 미확인
- **관련 코드 위치:** [Forms/Finance/frmFinanceSetting.cs](../../Y3/Y3/Forms/Finance/frmFinanceSetting.cs) — UpdateCategory(372행)

## F48. 거래 분류 목록 조회·삭제

- **기능명:** 거래 분류 목록 조회·삭제
- **사용자:** 로그인 운영자
- **진입 화면:** 가계부 → 설정
- **입력값:** 행, 확인
- **처리 로직:** 목록 조회 및 useflag=0
- **관련 DB 테이블:** finance_category
- **결과:** 활성 분류 제외
- **예외/제약사항:** 기존 참조 정리 없음
- **관련 코드 위치:** [Forms/Finance/frmFinanceSetting.cs](../../Y3/Y3/Forms/Finance/frmFinanceSetting.cs) — LoadCategoryData(299행), DeleteCategory(469행)

## F49. 고정 수입·지출 설정 등록

- **기능명:** 고정 수입·지출 설정 등록
- **사용자:** 로그인 운영자
- **진입 화면:** 가계부 → 설정
- **입력값:** 이름, 유형, 금액, 자산, 분류, 지정일
- **처리 로직:** 이체 거부 후 INSERT
- **관련 DB 테이블:** finance_fixed; finance_account; finance_category
- **결과:** 자동 입력 후보 설정
- **예외/제약사항:** 지정일 빈값은 0, 유효일 검증 없음. 등록 즉시 거래 실행 아님
- **관련 코드 위치:** [Forms/Finance/frmFinanceSetting.cs](../../Y3/Y3/Forms/Finance/frmFinanceSetting.cs) — UpdateFixed(403행)

## F50. 고정 수입·지출 설정 변경

- **기능명:** 고정 수입·지출 설정 변경
- **사용자:** 로그인 운영자
- **진입 화면:** 가계부 → 설정
- **입력값:** 기존 설정 행과 변경값
- **처리 로직:** 기존 모델 UPDATE
- **관련 DB 테이블:** finance_fixed
- **결과:** 설정 변경
- **예외/제약사항:** UpdateDate 필드는 이 폼에서 지정하지 않음. 마지막 입력일 직접 편집 없음
- **관련 코드 위치:** [Forms/Finance/frmFinanceSetting.cs](../../Y3/Y3/Forms/Finance/frmFinanceSetting.cs) — UpdateFixed(403행)

## F51. 고정 거래 목록 조회·중단

- **기능명:** 고정 거래 목록 조회·중단
- **사용자:** 로그인 운영자
- **진입 화면:** 가계부 → 설정
- **입력값:** 설정 행, 삭제 확인
- **처리 로직:** DB 조회, useflag=0
- **관련 DB 테이블:** finance_fixed, finance_account, finance_category
- **결과:** 활성 설정 제외
- **예외/제약사항:** 기존 생성 거래를 취소하지 않음
- **관련 코드 위치:** [Forms/Finance/frmFinanceSetting.cs](../../Y3/Y3/Forms/Finance/frmFinanceSetting.cs) — LoadFixedData(304행), DeleteFixed(491행)

## F52. 자산·부채·순자산과 차트 조회

- **기능명:** 자산·부채·순자산과 차트 조회
- **사용자:** 로그인 운영자
- **진입 화면:** 가계부 → 통계
- **입력값:** 화면 표시
- **처리 로직:** 비카드 잔액 합, 카드 잔액 합, 차액 계산; 비카드 자산 차트
- **관련 DB 테이블:** finance_account
- **결과:** 자산 목록·차트·합계
- **예외/제약사항:** 신용카드만 존재하면 차트 빈 결과 예외 가능
- **관련 코드 위치:** [Forms/Finance/frmFinanceMain.cs](../../Y3/Y3/Forms/Finance/frmFinanceMain.cs) — LoadData(65행), UpdateBalaceText(77행), UpdateChart(92행)

## F53. 고정 수입·지출 장부 자동 생성

- **기능명:** 고정 수입·지출 장부 자동 생성
- **사용자:** 로그인 사용자가 촉발하는 시스템 처리
- **진입 화면:** 로그인 성공 직후 자동 처리
- **입력값:** 저장된 고정 설정, 현재 PC 날짜
- **처리 로직:** CheckLastInputDate 대상만 이번 월 지정일로 거래 저장, 폼 UpdateAccount, 마지막 입력일 별도 저장
- **관련 DB 테이블:** finance_fixed, finance_transaction, finance_account
- **결과:** 조건에 맞는 고정 거래 입력
- **예외/제약사항:** 월 반복 판정 결함, 업무 전체 원자성 없음, 과거 월 보충 없음
- **관련 코드 위치:** [Cores/Core.cs](../../Y3/Y3/Cores/Core.cs) — CheckFixedTransaction(167행)

## F54. 센터 신규 등록

- **기능명:** 센터 신규 등록
- **사용자:** 센터1 계정ID admin (정상 메뉴 경로)
- **진입 화면:** 어드민설정 → 어드민관리
- **입력값:** 센터명
- **처리 로직:** 새 Gym INSERT, 콤보 갱신
- **관련 DB 테이블:** gym
- **결과:** 센터 선택 가능
- **예외/제약사항:** 센터명 필수, 중복 이름 검사 없음
- **관련 코드 위치:** [Forms/admin/frmAdminRegister.cs](../../Y3/Y3/Forms/admin/frmAdminRegister.cs) — UpdateGym(227행)

## F55. 센터 이름 변경

- **기능명:** 센터 이름 변경
- **사용자:** 센터1 계정ID admin (정상 메뉴 경로)
- **진입 화면:** 어드민설정 → 어드민관리
- **입력값:** 센터 행, 새 이름
- **처리 로직:** ID로 UPDATE
- **관련 DB 테이블:** gym
- **결과:** 현재 센터 정보 변경
- **예외/제약사항:** 이미 표시한 메인 타이틀 자동 갱신은 미확인
- **관련 코드 위치:** [Forms/admin/frmAdminRegister.cs](../../Y3/Y3/Forms/admin/frmAdminRegister.cs) — UpdateGym(227행)

## F56. 센터 조회·비활성화

- **기능명:** 센터 조회·비활성화
- **사용자:** 센터1 계정ID admin (정상 메뉴 경로)
- **진입 화면:** 어드민설정 → 어드민관리
- **입력값:** 센터 행, 확인
- **처리 로직:** 활성 센터 목록, useflag=0
- **관련 DB 테이블:** gym
- **결과:** 활성 목록 제외
- **예외/제약사항:** 소속 계정·업무 자료 연쇄 비활성/검사 없음
- **관련 코드 위치:** [Forms/admin/frmAdminRegister.cs](../../Y3/Y3/Forms/admin/frmAdminRegister.cs) — LoadGymData(75행), DeleteGym(204행)

## F57. 운영 계정 신규 등록

- **기능명:** 운영 계정 신규 등록
- **사용자:** 센터1 계정ID admin (정상 메뉴 경로)
- **진입 화면:** 어드민설정 → 어드민관리
- **입력값:** 센터, ID, 암호
- **처리 로직:** 입력 암호 DPAPI 보호 후 INSERT
- **관련 DB 테이블:** admin; gym
- **결과:** 로그인 계정 추가
- **예외/제약사항:** 명시적 필수 검사는 센터. ID 중복/빈 암호 검사 미확인
- **관련 코드 위치:** [Forms/admin/frmAdminRegister.cs](../../Y3/Y3/Forms/admin/frmAdminRegister.cs) — UpdateAdmin(291행)

## F58. 운영 계정 센터·암호 변경

- **기능명:** 운영 계정 센터·암호 변경
- **사용자:** 센터1 계정ID admin (정상 메뉴 경로)
- **진입 화면:** 어드민설정 → 어드민관리
- **입력값:** 기존 계정 행, 센터, 새 암호 또는 빈값
- **처리 로직:** 기존 ID 입력 잠금; 새 암호 있으면 암호화, 없으면 기존 암호 유지; UPDATE
- **관련 DB 테이블:** admin
- **결과:** 계정 정보 변경
- **예외/제약사항:** 권한 역할 변경 필드 없음. DPAPI CurrentUser 종속
- **관련 코드 위치:** [Forms/admin/frmAdminRegister.cs](../../Y3/Y3/Forms/admin/frmAdminRegister.cs) — Grid_CellDoubleClick(124행), UpdateAdmin(291행)

## F59. 계정 조회·비활성화

- **기능명:** 계정 조회·비활성화
- **사용자:** 센터1 계정ID admin (정상 메뉴 경로)
- **진입 화면:** 어드민설정 → 어드민관리
- **입력값:** 계정 행, 확인
- **처리 로직:** 활성 계정+센터명 조회, useflag=0
- **관련 DB 테이블:** admin, gym
- **결과:** 활성 계정에서 제외
- **예외/제약사항:** 자기 자신/마지막 관리자 삭제 금지 없음
- **관련 코드 위치:** [Forms/admin/frmAdminRegister.cs](../../Y3/Y3/Forms/admin/frmAdminRegister.cs) — LoadAdminData(70행), DeleteAdmin(269행)

## 기본 UI에서 실행할 수 없는 구현 및 보조 동작

### H01. 이전 월 세션 복사 — 숨김

- 기능명: 트레이너 이전 월 진행 기록 복사
- 사용자: 기본 UI에서 실행 경로 없음
- 진입 화면: frmSessionRegister의 btnLoad/dtLoad (Visible=false)
- 입력값: 트레이너, 원본 월, 대상 월
- 처리 로직: 캐시 조회→확인→Clone→날짜 변경→MultiSave INSERT→연속 ID 가정→캐시 추가
- 관련 DB 테이블: session
- 결과: 대상 날짜의 진행 기록 복제
- 예외/제약사항: 중복 방지·잔여 검증·차감 없음
- 관련 코드 위치: Forms/Session/frmSessionRegister.cs LoadBeforeSession:129; Designer:285,297

### H02. 진행 등록에서 상품 직접 선택 — 숨김

- 기능명: 별도 상품 목록에서 지급단가 선택
- 사용자: 기본 UI에서 실행 경로 없음
- 진입 화면: frmSessionRegister의 groupBox2 (Visible=false)
- 입력값: 상품 행
- 처리 로직: 종류·단가 설정, 기존 진행 ID 비움; 기존 횟수 있으면 상품 ID×횟수로 합계를 설정하는 오류 경로
- 관련 DB 테이블: session_price, session_trainer (캐시 참조)
- 결과: 진행 입력 필드 변경
- 예외/제약사항: 저장은 별도 등록 버튼; 일반 회원 선택 경로와 구별
- 관련 코드 위치: Forms/Session/frmSessionRegister.cs Grid_CellDoubleClick SESSION_PRICE 분기; Designer:517

### H03. Excel 회원·락커 가져오기 — 호출 미확인

- 기능명: Excel에서 회원·락커 일괄 등록
- 사용자: 호출 경로 미확인
- 진입 화면: frmMain에 메서드만 존재
- 입력값: C 드라이브 user.xls의 첫 시트 4열(이름, 전화, 종료일, 락커번호)
- 처리 로직: Excel COM 읽기→회원 MultiSave→락커 MultiSave→COM 정리
- 관련 DB 테이블: user, locker
- 결과: 회원/락커 생성 코드 존재
- 예외/제약사항: 헤더 제외 없음, 별도 커밋, ID 연속 가정, owner_type 하드코딩, 실제 메뉴 없음
- 관련 코드 위치: Forms/frmMain.cs ReadExcelData:273, ReleaseExcelObject

### H04. 생일 목록 보조 메서드 — 호출 미확인

- 기능명: 이번 달 회원/트레이너 생일 필터
- 사용자: 호출 경로 미확인
- 진입 화면: 없음
- 입력값: 현재 PC 월
- 처리 로직: BirthDay.Month가 이번 달이고 Year>1900인 캐시 항목 필터
- 관련 DB 테이블: user, trainer (캐시)
- 결과: 생일 목록 반환
- 예외/제약사항: 실제 안내 화면/문자 발송 없음
- 관련 코드 위치: Models/ModelList.cs GetMonthBirthTrainer:328, GetMonthBirthUser:416

초기 DB 동기화·초기 계정 생성은 시작 시 시스템 동작이며 별도의 관리 버튼 기능이 아니다([01](01-system-overview.md), [08](08-auth-and-permissions.md)). 기타설정/급여 팝업은 빈 폼이다. 예약 등록·변경·취소, 계약 등록, 결제 승인·환불, 출석 체크, 회원권 만료, 일 매출 전용 조회는 확인되지 않아 기능으로 만들어 넣지 않았다.

### 추가로 확인한 기존 기능의 세부 경로

F36에는 로그인 화면의 닫기 버튼도 포함한다. frmLock.BtnClose_Click(79행)은 로그인 여부와 무관하게 Application.Exit을 직접 호출하며 메인 종료 메뉴의 확인·설정 저장 경로와 다르다. F46/F47의 분류 갱신은 frmFinanceInput.InitComboEvent(73행)의 구독 주석과 Radio_CheckedChanged/SetComboCategory를 함께 참조한다. 회원·트레이너 전화번호는 저장 처리기에서 최소 10자를 검사하고 Designer에서는 MaxLength=11로 제한한다(정상 직접 입력 기준 10–11자이며 완전한 전화번호 검증을 뜻하지 않는다).
