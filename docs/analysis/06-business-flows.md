# 06. 주요 업무 흐름

아래는 현재 코드의 순서다. DB 호출이 분리된 곳은 다이어그램에서도 나누었다. 운영자가 어떤 순서로 상품·회원을 준비하는지는 **추정**이며, 호출 순서와 검증 분기는 코드로 확인했다. 계약→결제→예약 흐름은 구현 근거가 없어 만들지 않았다.

## B01. 시작·로그인·업무 화면 진입

```mermaid
sequenceDiagram
    actor O as 운영자
    participant L as frmLock
    participant C as Core
    participant D as DB
    O->>L: 프로그램 실행
    L->>C: InitCore
    C->>C: 로컬 설정 읽기
    C->>D: 연결 검사 및 필요 시 버전 SQL
    C->>D: 활성 센터와 계정 로드
    L->>L: 계정 목록이 비면 초기 계정 생성 시도
    O->>L: 센터와 ID 및 암호 입력
    L->>L: 계정 검색 및 DPAPI 복호화 비교
    alt 인증 실패
        L-->>O: 로그인 오류
    else 인증 성공
        L->>D: 최근 접속일 저장
        L->>C: 현재 사용자와 센터 설정
        C->>D: 센터별 업무 데이터 로드
        L->>C: InitForm 및 CheckFixedTransaction
        L-->>O: 메인 모달 표시
    end
```

근거: `Program.Main`, `frmLock.cs:21,44,89`, `Core.cs:68,80,105`, `ModelList.cs:970`. 버전 SQL은 읽기 전용이 아니다. 이 분석에서는 실행하지 않았다.

## B02. PT 이용정보 준비와 진행 횟수 등록

```mermaid
flowchart TD
    A[트레이너와 PT 종류 등록] --> B[선택적으로 개별 지급률 등록]
    B --> C[회원에 상품과 담당 및 일반 서비스 잔여 입력]
    C --> D[진행 등록 화면에서 담당 트레이너와 월 선택]
    D --> E[잔여 합계가 양수인 담당 회원 검색]
    E --> F[회원 선택 및 종류 존재 확인]
    F --> G[지급단가 표시 후 진행 횟수 입력]
    G --> H{1 이상이며 잔여 합계 이하인가}
    H -->|아니오| X[오류 표시]
    H -->|예| I{일반 잔여로 충족하는가}
    I -->|예| J[일반 기록 1행]
    I -->|아니오| K[일반 잔여분과 서비스 초과분 기록 분할]
    J --> L[MultiSave로 진행 기록 커밋]
    K --> L
    L --> M{신규 ID가 반환되었는가}
    M -->|예| N[별도 회원 Save로 일반 우선 잔여 차감]
    M -->|아니오| O[잔여 차감 없음]
    N --> P[캐시와 목록 갱신]
    O --> P
```

근거: `frmSettingUser.UpdateUser`, `frmSettingSession.UpdateSessionPrice/UpdateST`, `frmSessionRegister.UpdateSession:229`, `UserList.GetUsersHaveSessionDataTableByTrainerId:388/MinusUserSessionCount:397`. 준비 단계의 운영 순서는 **추정**이다. 기록 저장 실패 시 차감하지 않지만 차감 저장 실패는 기록을 취소하지 않는다. 혼합 시 일반 기록 금액 계산 결함은 K04 참조.

## B03. 진행 기록 수정·삭제·횟수 복원

```mermaid
flowchart TD
    A[트레이너와 월로 기존 기록 조회] --> B[행 더블클릭]
    B --> C{등록 또는 삭제}
    C -->|등록| D[횟수 입력은 비활성 상태]
    D --> E[현재 회원 잔여로 다시 검증하고 분할 계산]
    E --> F[기존 ID로 UPDATE]
    F --> G[회원 잔여 조정 없음]
    C -->|삭제| H[삭제 확인]
    H --> I{횟수 복원 선택}
    I -->|예| J{현재 상품과 기록 상품 동일}
    J -->|아니오| K[삭제 거부]
    J -->|예| L[세션 useflag를 0으로 저장]
    I -->|아니오| L
    L --> M{복원 선택했는가}
    M -->|예| N[IsService에 맞는 잔여에 기록 횟수 가산]
    N --> O[별도 회원 UPDATE]
    M -->|아니오| P[목록 갱신]
    O --> P
```

근거: `frmSessionRegister.Grid_CellDoubleClick/UpdateSession/DeleteSession:180`. 삭제/복원은 환불 처리가 아니다. 회원이 이미 비활성화된 경우 null 접근 등은 보호되지 않은 경로다.

## B04. 트레이너 매출 화면의 막힌 경로와 기존 자료 집계

```mermaid
flowchart TD
    A[Core.InitForm에서 매출 폼 생성] --> B[InitComboEvent 호출 없음]
    B --> C[트레이너 콤보 미바인딩]
    C --> D[LoadSalesData는 null 검사 후 반환]
    C --> E[등록 버튼 UpdateSales]
    E --> F[필수검사 전 SelectedValue.ToString null 예외 경로]
    G[(기존 trainer_sales 자료)] --> H[ModelList에서 로드]
    H --> I[운영자가 별도로 세션 현황 화면 선택]
    I --> J[LoadMonthlyData의 월별 매출 합계]
```

근거: Core.InitForm(80행), frmTrainerSales 생성자(28행)/InitComboEvent(52행)/LoadSalesData(114행)/UpdateSales(148행), frmSessionStats.LoadMonthlyData(123행). 저장 처리기는 있으나 표준 초기화에서는 정상 입력 흐름에 도달하지 못한다. 기존 DB 매출의 집계는 별도 경로다. 수업에서 매출 자동 생성이나 저장 후 통계 화면 자동 이동은 없다.

## B05. 가계부 거래 등록·수정·삭제

```mermaid
flowchart TD
    A[거래 입력 검증 통과] --> B{기존 거래인가}
    B -->|예| C[Clone 후 기존 잔액 역처리]
    C --> D{역처리 true}
    D -->|아니오| X[오류 표시 후 반환]
    D -->|예| E[거래 객체 수정 및 Save]
    B -->|아니오| E
    E --> F{거래 Save true}
    F -->|아니오| Y[새 잔액 반영 없이 종료]
    F -->|예| G[새 거래 잔액 반영]
    G --> H{잔액 처리 true}
    H -->|아니오| X
    H -->|예| I[입력 초기화 후 월 목록 재조회]
    J[삭제 대상 및 확인] --> K[거래 삭제 Save]
    K --> L{Save true}
    L -->|예| M[입력 초기화 후 월 목록 재조회]
    M --> N[삭제 거래 잔액 역처리]
    N --> O[역처리 반환값 확인 없음]
    L -->|아니오| Y
```

근거: frmFinanceInput.DeleteTransaction(241행), UpdateTransaction(263행), UpdateAccount(318행). 각 저장은 독립 호출이며 실패 시 이전 커밋을 되돌리지 않는다. true는 영향 행 수를 보장하지 않는다. 삭제는 목록 갱신 후 역처리한다. 카드 취소·환불 API 흐름이 아니다.

## B06. 이체 잔액 반영의 실제 경로

```mermaid
flowchart TD
    A[이체 유형 거래] --> B[AccountId의 출발 자산 조회]
    B --> C[CategoryId의 도착 자산 조회]
    C --> D[메모리에서 출발 차감과 도착 가산]
    D --> E{출발 자산 Save 성공}
    E -->|예| F[OR 단락으로 도착 Save 생략]
    F --> G[성공 반환]
    E -->|아니오| H{도착 자산 Save 성공}
    H -->|예| G
    H -->|아니오| I[실패 반환]
```

근거: `frmFinanceInput.UpdateAccount:318`. 이것은 의도된 정산 규칙이 아니라 현재 조건식의 결함이다. 역처리도 같은 저장 조건을 사용한다.

## B07. 로그인 시 고정 거래 자동 입력

```mermaid
sequenceDiagram
    participant L as frmLock
    participant C as Core
    participant F as FixedTransaction
    participant D as DB
    L->>C: 로그인 후 CheckFixedTransaction
    C->>F: CheckLastInputDate로 대상 필터
    loop 판정된 각 설정
        C->>C: 이번 연월과 지정 일로 DateTime 생성
        C->>D: finance_transaction INSERT
        alt 저장 성공
            C->>D: 폼 UpdateAccount를 통해 잔액 저장
            C->>F: LastInputDate 변경
            C->>D: finance_fixed UPDATE
        end
    end
```

근거: `Core.CheckFixedTransaction:167`, `ModelList.FixedTransactionList.GetListInput:853`, `FixedTransaction.CheckLastInputDate:73`. 지난달 누락분의 반복 보충은 없으며 판정식 자체에 월 반복 결함이 있다. 거래에 fixed ID를 남기지 않아 원본 추적은 메모에 의존한다.

## B08. 락커 배정·기간·마감

```mermaid
flowchart TD
    A[메인 락커 타일 클릭] --> B[popLocker 표시]
    B --> C{사용 중인가}
    C -->|아니오| D[회원 또는 트레이너 팝업 선택]
    D --> E[종료일 또는 무기한 설정]
    E --> F{동일 유형과 소유자 ID의 락커 존재}
    F -->|예| X[저장 거부]
    F -->|아니오| G[locker INSERT 또는 UPDATE]
    G --> H[타일 사용자와 기간 및 색상 갱신]
    C -->|예| I[기간 변경 후 저장 시도]
    I --> F
    C -->|마감 선택| J[기간 남음 또는 마감 확인]
    J --> K[소유자 ID 0과 이름 빈값과 NONE 저장]
    K --> L[타일 초기화]
```

근거: `frmMain.Locker_ButtonClickEvent`, `popLocker.LoadOwner/SaveLocker/UseEnd`, `frmMain.SetLockerColor`. 만료는 표시만 바꾸며 자동 마감하지 않는다. 기존 소유자를 제외하지 않는 중복 검사 때문에 연장 시도는 거부될 수 있다.

## B09. 숨겨진 이전 월 복사

```mermaid
flowchart LR
    A[숨김 불러오기 이벤트] --> B[트레이너와 원본 월의 캐시 기록 조회]
    B --> C[확인 후 Clone과 대상 날짜 설정]
    C --> D[MultiSave INSERT]
    D --> E[연속 ID 가정 후 캐시 추가]
    E --> F[잔여 검증과 차감 없이 목록 표시]
```

근거: `frmSessionRegister.LoadBeforeSession:129`, `frmSessionRegister.Designer.cs:285,297`. 버튼·날짜 입력이 Visible=false이고 다시 표시하는 코드는 찾지 못했다. 정상 사용자가 실행하는 현재 업무로 분류하지 않는다.

## 흐름 해석 보완

B01의 최근 접속일 저장은 시도이며 반환값을 확인하지 않는다. B03의 기존 ID UPDATE도 실제 변경을 보장하지 않는다(GymNo 누락, K05/K38). B07은 거래 Save가 true이면 UpdateAccount의 false를 검사하지 않고 LastInputDate를 변경하며 finance_fixed Save의 반환값도 무시한다(예외가 발생하지 않은 경로 기준). B08은 저장 성공 분기의 표현이며 마감 후 팝업 내부 선택 ID가 남는 별도 문제가 있다(K40).
