# 08. 인증과 권한

## 로그인 방식

`Program.Main`은 `frmLock`을 실행한다. 로그인 전 `ModelList` 생성자가 모든 활성 센터와 모든 활성 계정을 DB에서 읽는다. `frmLock.Login`은 선택한 센터와 입력 ID로 `AdminList.GetByGymNoAndId`를 호출하고, `Secure.CheckPw`로 입력 암호와 복호화한 저장 암호를 비교한다. 실패하면 메시지를 표시한다. 성공하면 최근 접속일을 UPDATE하고 `Core.LOGIN_USER/LOGIN_GYM`을 설정하여 센터 데이터를 로드한다.

근거: `Program.cs:17`, `Forms/frmLock.cs:89`, `Models/ModelList.cs:646,970`, `Models/DB/QueryString.cs:19,20`.

암호 저장은 해시가 아닌 **Windows DPAPI 가역 암호화**다. `ProtectedData.Protect/Unprotect`, `DataProtectionScope.CurrentUser`, 고정 entropy, Base64를 사용한다. 복호화 실패 시 빈 SecureString을 반환한다. 따라서 다른 Windows 사용자/실행 환경에서 기존 암호가 복호화되지 않을 수 있으며, 실패 결과와 빈 암호의 구분도 없다. `CheckPw`상 복호화 실패 결과와 빈 입력이 같아지는 경로가 존재한다.

근거: `Utility/Secure.cs:14,20,59,64`. 환경 간 실제 복호화 성공 여부는 미검증이다.

활성 계정 목록이 비어 있으면 `CheckAdmin`이 센터 1에 고정 초기 ID와 초기 암호로 계정을 생성한다. 초기 자격증명의 원문은 이 문서에 재기재하지 않는다. 정상적인 최초 설치와 DB 읽기 오류가 모두 빈 목록으로 보일 수 있다. 근거: `frmLock.cs:44`, `MariaDB.Get`.

## 사용자 종류와 권한 매트릭스

여기서 운영자는 `Admin` 계정으로 로그인한 사용자다. 실제 직원 직책은 코드에 없으므로 운영자라는 업무 명칭은 **추정**이다. `User`는 회원, `Trainer`는 직원 데이터이며 둘 다 로그인 계정 관계가 없다. `eUserType`은 락커 소유자 구분이고 권한 enum이 아니다.

| 화면/행위 | 비로그인 | 일반 로그인 계정 | 센터 1의 ID `admin` |
| --- | --- | --- | --- |
| 센터 선택·로그인 | 가능 | 별도 로그아웃 흐름 미확인 | 동일 |
| 메인·락커 배정/마감 | 메인 진입 전 | 메뉴 제공 | 제공 |
| 회원·트레이너 설정 | 메인 진입 전 | 제공 | 제공 |
| 세션 가격·개별 지급률 | 메인 진입 전 | 제공 | 제공 |
| 진행 등록·삭제·현황·매출 | 메인 진입 전 | 제공 | 제공 |
| 가계부 내역·통계·설정 | 메인 진입 전 | 제공 | 제공 |
| 기타 설정 | 메인 진입 전 | 메뉴 제공, 빈 화면 | 동일 |
| 센터·계정 관리 | 메인 진입 전 | 관리자 메뉴 숨김 | 관리자 메뉴 표시 |

근거: `Forms/frmMain.cs:79` 생성자의 `AdminId == "admin" && LOGIN_GYM.Id == 1`, `BtnSub_Click`, `frmMain.Designer.cs:175`. 표는 정상 UI 경로를 설명하며 보안 경계 보장을 의미하지 않는다.

## 관리자 기능과 데이터 범위

`FrmAdminRegister`는 센터 등록·변경·비활성화, 계정 등록·센터 지정·암호 변경·비활성화를 제공한다. 기존 계정 ID 입력은 더블클릭 시 비활성화되고, 비밀번호 입력이 비면 숨겨진 기존 암호 값을 유지한다. 계정 ID 중복·빈 ID/암호·마지막 관리자 삭제 금지 검증은 확인되지 않는다. 계정 생성/수정의 명시적 필수 검사는 센터 선택이다.

근거: `Forms/admin/frmAdminRegister.cs:124,269,291`, Designer의 `txtAdminOriginPw` 숨김.

권한 테이블, 역할 필드, 기능별 권한 검사, 서버 인증, 토큰·쿠키, 실패 횟수 제한, 세션 만료, 감사로그는 확인되지 않는다. 관리자 폼은 일반 계정 로그인 때도 `Core.InitForm`에서 생성된다. 접근 통제는 메뉴 표시 조건에 집중되어 있다.

대부분 조회는 현재 계정 GymNo로 제한되지만 admin/gym은 전체 활성 데이터 조회다. 금융 UPDATE/DELETE는 ID 기준 SQL이며 별도의 로그인 센터 조건이 없고 일부 UPDATE는 전달된 GymNo도 덮어쓴다. 이것을 서버 수준 다중 센터 격리로 간주할 수 없다. 근거: `Core.cs:80`, `QueryString.cs:50–91`.

최근 ID는 로컬 설정에 저장하고 센터는 `SetLoginGym`에서 ID로 저장한다. `SetLastInfo`는 그 값을 SelectedIndex로 사용하므로 ID와 목록 인덱스가 다르면 잘못 선택되거나 범위를 벗어날 수 있다. 근거: `Core.cs:200,206`, `frmLock.cs:38`.

## 접근 권한과 기능 실행의 구분

접근 표의 “제공”은 메뉴 노출과 폼 연결을 뜻한다. 개인 매출등록은 권한과 무관하게 콤보 초기화 누락으로 정상 입력·조회가 막힌다(Core.InitForm, frmTrainerSales.InitComboEvent/LoadSalesData/UpdateSales). 로그인 최근 접속일 Save 반환값은 무시한다(frmLock.Login). DPAPI 복호화 실패와 빈 암호 입력의 비교 경로는 조회된 기존 Admin이 있는 경우의 문제이며 임의의 미등록 ID로 로그인할 수 있다는 의미가 아니다(Secure.CheckPw/Decrypt, frmLock.Login).
