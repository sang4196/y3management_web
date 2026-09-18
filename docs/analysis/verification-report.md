# 분석 문서 역검증 기록

검증일: 2026-09-15. 기준 소스 커밋: `30cdc19992182d3216e1f855fe6a8e4ecb1dea53`. 소스 경로는 `Y3/Y3/` 기준이다. 기존 13개 문서를 다시 읽고 모델 속성, DDL, SQL, 생성자, 이벤트 구독, 화면 진입 및 저장 후 분기를 대조했다. 실행·운영 DB 검증은 수행하지 않았다.

## 주요 정정

1. **개인 매출등록을 정상 실행 가능한 기능으로 단정한 설명을 정정했다.** `Core.InitForm:80`과 `frmTrainerSales` 생성자(28행)는 해당 폼의 `InitComboEvent:52`를 호출하지 않는다. Designer에도 트레이너 목록 바인딩이 없다. `LoadSalesData:114`는 null이면 반환하고 `UpdateSales:148`는 필수값 검사 전에 null의 ToString을 호출한다. F22–F25는 처리기 존재와 실제 진입 가능성을 구분했다. 기존 DB 매출의 통계 집계는 별도로 존재한다.
2. **Transaction의 UseFlag 모델 속성 설명을 삭제했다.** 물리 `finance_transaction.useflag`와 SQL 처리는 존재하지만 `Models/Finance/Transaction.cs`에는 해당 속성이 없다.
3. **저장 성공과 실제 변경을 구분했다.** `MariaDB.Save:109/MultiSave:135`는 영향 행 수를 확인하지 않는다. `frmSessionRegister.UpdateSession:229`의 새 객체에 GymNo가 없어 UPDATE가 0행일 수 있다. INSERT 후 Id만 채운 캐시 객체는 재조회 전 수정 시 기본 GymNo를 SQL에 사용할 수 있다. SQL별 영향은 K05/K20/K38에 구분했다.
4. **거래 처리 순서와 실패 분기를 바로잡았다.** `frmFinanceInput.UpdateTransaction:263`은 기존 잔액 역처리 실패 시 거래 저장 전에 반환한다. `DeleteTransaction:241`은 거래 삭제 후 목록을 먼저 갱신하고 잔액을 역처리한다. 고정 거래 처리는 잔액 처리 및 마지막 입력일 저장의 반환값을 무시한다(`Core.CheckFixedTransaction:167`).
5. **즉시 갱신을 단정하지 않도록 수정했다.** 분류 콤보 이벤트 구독은 주석 처리되어 있다(`frmFinanceInput.InitComboEvent:73`). 락커 색상은 생성 및 개별 갱신 시 계산하며 날짜 변경·메인 복귀만으로 다시 계산하지 않는다(`frmMain.MakeLocker:450/SetLockerColor:499/UpdateLocker:525`).
6. **위험 설명의 조건을 좁혔다.** 잘못된 고정 거래 day는 대상 필터를 통과하지 못하는 경우가 있으므로 곧바로 DateTime 예외라고 단정하지 않았다. 다중 PC 공유 DB는 현재 배포 사실이 아닌 동시 쓰기 조건의 추정으로 표시했다. 기본 거래 조회의 포맷 오류는 DB Get에서 빈 결과로 처리되는 경로로 정정했다.

## 문서별 검증 결과

| 문서 | 대조 근거 및 반영 |
| --- | --- |
| [01](01-system-overview.md) | sln/csproj, Core, Program 대조. 참조 선언과 설치 버전 구분, 빌드 제외 C# 파일, 매출 초기화 누락 추가 |
| [02](02-domain-model.md) | 모델 속성과 SQL/DDL 대조. Transaction 속성 오류 삭제, 매출·Session 수정의 실행 제약 반영 |
| [03](03-feature-inventory.md) | 메뉴·버튼·이벤트·처리기 대조. F20/F22–F25 결과 정정, F33/F46/F47 갱신 조건, 로그인 종료 및 전화번호 입력 제약 보완 |
| [04](04-screen-inventory.md) | Form 선언·Designer·생성자 대조. S07 상태 정정, 분류 콤보와 락커 표시 갱신 조건 보완 |
| [05](05-database-model.md) | DDL 13개 테이블/107개 컬럼과 SQL 조립기 대조. 모델 속성 차이, 영향 행 수 및 GymNo 문제 보완 |
| [06](06-business-flows.md) | 처리기의 호출 순서·return 조건 대조. 매출 흐름 교체, 거래 수정/삭제 다이어그램 정정, 저장 반환값 제약 추가 |
| [07](07-business-rules.md) | 검증 조건과 실행 경로 대조. R23 필수검사 도달 제약, R21 조회 조건과 화면 실행 구분 |
| [08](08-auth-and-permissions.md) | 로그인·DPAPI·메뉴 대조. 접근 허용과 정상 기능 실행 구분, 접속일 저장·복호화 실패 조건 보완 |
| [09](09-external-integrations.md) | 호출 코드·프로젝트 참조 대조. 버전 SQL의 작업 디렉터리 의존과 출력 복사 선언 부재 보완 |
| [10](10-web-migration-considerations.md) | UI/DB 결합 근거 재확인. 매출 분리 논의를 정상 운영 사실과 구분 |
| [11](11-risks-and-unknowns.md) | SQL·객체 생성·실패 처리 대조. 위험 조건 정정, K37–K41 추가, 부정확한 메서드 행 수 삭제 |
| [12](12-glossary.md) | 실제 모델·메서드 의미 대조. 매출 입력·저장 성공·useflag 용어 범위 보완 |
| [README](README.md) | 문서 간 결과 대조. 위험 개수 및 역검증 요약·본 기록 링크 반영 |

## 누락 재탐색

- C# 파일 80개, csproj Compile 항목 79개. `Utility/Define/Defines.cs`는 프로젝트 빌드에 포함되지 않는다.
- Form 클래스 15개와 `UCLocker`가 화면 목록에 포함된다. 추가 Form은 발견하지 못했다. 빈 기타설정·미연결 급여 팝업·숨겨진 세션 복사/종류 선택은 기존 분류를 유지한다.
- 저장소 DDL은 `Utility/Version/sql/CreateTable.sql` 하나이며 13개 테이블, 107개 컬럼이다. SQL 조립기와 대조하여 추가 테이블은 발견하지 못했다. 운영 DB에만 존재하는 테이블·트리거·프로시저는 미확인이다.
- 기능 목록 59개와 숨김·미연결 항목 4개를 유지한다. 신규 업무 기능을 추측하여 추가하지 않았다. 누락된 세부 경로인 로그인 화면 종료, 분류 갱신 제약, 매출 실행 차단 등을 기존 기능에 반영했다.
- 계약·예약·출석·결제 승인·환불 등의 독립 기능은 재탐색에서도 구현 근거를 찾지 못했다. 외부 운영 절차의 부재까지 의미하지 않는다.

## 검증 한계

파일·클래스·SQL 정의 및 제어 흐름에 대한 정적 검증이다. 오류의 실제 운영 발생 횟수, 데이터 손상 여부, 배포된 바이너리와 저장소의 일치 여부는 알 수 없다. 빌드·UI 실행·DB 접속은 수행하지 않았으며 소스와 설정 파일은 수정하지 않았다. 문서 링크·코드 펜스·목록 개수도 검사했다.
