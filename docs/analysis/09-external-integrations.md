# 09. 외부 연동과 환경 의존성

## 확인된 연동

| 연동·상태 | 목적 / 라이브러리·프로토콜 | 호출 위치 | 입력 → 출력 |
| --- | --- | --- | --- |
| DB, 활성 | 로컬 MySQL 호환 DB 직접 접근 / MySql.Data 8.0.33 | `Cores/Database/MariaDB.cs:16,44,68,85,109,135` | SQL 문자열 → DataTable, 성공 여부, LastInsertedId |
| 설정 파일, 활성 | JSON 파일 저장·복원 / System.IO, Newtonsoft.Json | `Core.InitFolder/SaveConfig/SaveObjectToJson/ReadJsonToObject` | Config → `C:\Y3\Config\Config.json`; 재시작 시 읽기 |
| DB 초기화·버전 SQL, 활성 시작 경로 | 로컬 파일 SQL 실행 / System.IO + MySqlCommand | `Core.CheckVersion`, `VersionCheck.CreateTable/Sync` | 작업 디렉터리 상위 두 단계의 Utility/Version/sql 파일 → DB DDL 실행 |
| Windows 암호화, 활성 | 암호 보호 / DPAPI CurrentUser | `Secure.GetEncryptPw/CheckPw` | 암호·사용자별 보호 환경 → Base64 암호문 / 복호화 비교 |
| Windows 창 제어, 활성 | 제목 영역 드래그 / user32.dll SendMessage, ReleaseCapture | `frmMain.PictureBox1_MouseDown` | 마우스 이벤트·윈도 핸들 → 창 이동 |
| 프로세스 제어, 활성 | 같은 이름의 프로그램 중복 실행 검사 / System.Diagnostics | `Program.Main` | 현재 프로세스명 → 실행 거부 또는 로그인 폼 시작 |
| Excel 가져오기, 구현 있으나 호출 미확인 | 회원·락커 초기 데이터 로딩으로 **추정** / Office Interop COM, user32.dll | `frmMain.ReadExcelData:273`, `ReleaseExcelObject` | 고정 `C:\user.xls`, 첫 시트의 이름·전화·락커종료일·번호 4열 → user/locker 일괄 INSERT |

DB 연결 문자열은 코드에 하드코딩되어 있으며 loopback, 3306, y3db, root 계정과 암호를 포함한다. 암호 원문은 재기재하지 않는다. 실제 DB 서버 제품·버전·계정 권한·SQL mode·TLS 협상은 확인하지 않았다. `MariaDB`라는 클래스명만으로 운영 서버 종류까지 확정하지 않는다.

Excel 가져오기는 첫 행부터 순회하여 헤더 제외 처리가 없고 사용 영역을 object 배열로 읽는다. 저장은 회원과 락커 별도 호출이며 ID 연속 증가를 가정한다. 종료 시 COM 객체 해제와 Excel 프로세스 Kill 코드가 있다. 프로젝트에 참조가 있어도 사용자에게 제공되는 가져오기 메뉴로 볼 수 없다. 저장소 전체 `ReadExcelData` 검색에서 선언 외 호출이 없다. Excel 내보내기는 미확인이다.

설정에는 LAST_VERSION, LAST_GYM, LAST_ID, LOCKER_COUNT(기본 60), 락커 글꼴 크기(각 10), SERVICE_PRICE(25000), PAY_DAY(10)가 있다. UI에서 직접 변경 경로가 확인된 것은 메인의 락커 글꼴 크기다. 기타 설정 폼은 비어 있고 PAY_DAY의 업무 호출도 없다. 근거: `Utility/Config.cs`, `frmMain.BtnLockerFont_Click`, `frmSettingETC.cs`.

## 구현을 찾지 못한 연동

| 항목 | 판단 근거와 범위 |
| --- | --- |
| 카드 결제·은행 송금 | AccountType의 신용카드는 장부 분류. 승인·취소·계좌송금 통신 코드 없음 |
| 문자/SMS·카카오톡·이메일 | 연락처 필드는 있으나 발송 SDK·SMTP·발송 이벤트 미확인 |
| 프린터·바코드 | 출력/스캔 API·장치 입력 처리 미확인 |
| 출입 게이트·락커 하드웨어 | 락커는 DB와 화면 상태 관리. SerialPort·장치 제어 코드 미확인 |
| 외부 HTTP API | System.Net.Http 참조만으로 연동을 증명할 수 없음. 실제 HTTP 호출 미확인 |
| 파일 첨부·사진·영수증 | 리소스 이미지 외 업무 파일 업로드/저장 기능 미확인 |

조사 범위: 모든 프로젝트 C# 파일·Designer·csproj·packages.config의 호출/이벤트·참조. 패키지 내부 구현이나 운영 DB 트리거가 별도로 수행하는 연동은 이 분석으로 확정할 수 없다.

## 배포 경로 역검증

버전 SQL 로드는 현재 작업 디렉터리에서 두 단계 상위의 소스 Utility 경로를 구성한다(Utility/Version/VersionCheck.cs의 CreateTable). Y3.csproj의 CreateTable.sql Content 항목에는 CopyToOutputDirectory가 없다. 따라서 배포 환경에서 파일을 찾을 수 있는지는 미확인이다. 초기 DROP 실행 위험은 해당 파일을 읽고 DB 명령을 실행할 수 있는 조건에서 성립한다. 참조된 라이브러리 버전은 프로젝트 선언이며 실제 설치 상태를 확인한 것은 아니다.
