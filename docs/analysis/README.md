# Y3 PT 관리 프로그램 역분석

분석일: 2026-09-14 · 기준 커밋: `30cdc19992182d3216e1f855fe6a8e4ecb1dea53`

## 핵심 요약

현재 시스템은 **.NET Framework 4.7.2 Windows Forms 단일 프로젝트**다. 회원의 현재 PT 종류·잔여 횟수와 진행 세션, 트레이너 지급금액·수동 매출, 락커, 가계부, 센터·계정을 관리한다. 화면·업무 로직·SQL 생성은 폴더로 나뉘지만 전역 Core와 폼/모델에 강하게 결합되어 있다. **추정: DB 직접 접속형 2-tier 데스크톱 구조**다. 근거: `Y3/Y3/Y3.csproj`, `Cores/Core.cs`, `Models/ModelList.cs`, `Forms/Session/frmSessionRegister.cs`.

**Session은 예약이나 PT 계약이 아닌 진행 횟수·지급금액 기록**이다. User는 회원이고 로그인 계정은 Admin이다. 계약·예약·출석·고객 결제 승인·환불·회원권·상담의 독립 구현은 찾지 못했다. 가계부 거래 삭제를 고객 결제 취소로, 횟수 복원을 환불로 해석하면 안 된다. 근거: `Models/User.cs`, `Models/Admin.cs`, `Models/Session.cs`, `QueryString.cs`, `CreateTable.sql`.

## 산출물

| 문서 | 내용 |
| --- | --- |
| [01 시스템 개요](01-system-overview.md) | 솔루션·디렉터리·참조 라이브러리·계층·시작 순서 |
| [02 도메인 모델](02-domain-model.md) | 실제 13개 엔티티의 목적·필드·기능·관계, 미확인 도메인 구분 |
| [03 전체 기능 목록](03-feature-inventory.md) | 59개 기능/시도 및 숨김·미연결 항목 4개, 요청한 9개 항목별 명세 |
| [04 화면 목록](04-screen-inventory.md) | Form 15개와 UCLocker, 입력·조회·액션·진입·웹 분리 가능성 |
| [05 데이터베이스](05-database-model.md) | 13개 테이블 전체 컬럼, 논리 관계·JOIN·트랜잭션·Mermaid ERD |
| [06 업무 흐름](06-business-flows.md) | 로그인·진행·정산·장부·이체·고정거래·락커·숨김 복사, Mermaid 9개 |
| [07 비즈니스 규칙](07-business-rules.md) | 35개 규칙/현재 동작, 근거와 유지 여부 판단 |
| [08 인증·권한](08-auth-and-permissions.md) | DPAPI 로그인, 사용자 종류, 메뉴 접근, 센터 범위 |
| [09 외부 연동](09-external-integrations.md) | DB·설정파일·버전 SQL·Windows·미연결 Excel 및 미확인 연동 |
| [10 웹 전환 관점](10-web-migration-considerations.md) | 재사용 가능한 개념과 현재 코드의 UI/DB/OS 결합·분리 책임 |
| [11 위험·불명확 사항](11-risks-and-unknowns.md) | 위험 41개, 중복·긴 업무 메서드·정합성·운영 확인 질문 |
| [12 용어집](12-glossary.md) | 세션/지급금액/매출/회원/계정/거래 등 의미 구분 |

15개 Form 중 기타설정은 연결된 빈 화면이고 급여 팝업은 빈 미연결 폼이다. 세션 복사와 직접 상품 선택은 기본 Designer에서 숨김이다. 기능 수는 초기화 버튼마다 늘린 수가 아니라 업무 단위 분류다.

## 우선 확인할 발견

1. **이체 도착 자산 DB 저장 누락**: `frmFinanceInput.UpdateAccount`의 OR 단락으로 출발 자산 저장 성공 시 도착 자산 저장을 생략한다. [K01](11-risks-and-unknowns.md)
2. **횟수·금액 정합성**: 세션+차감과 거래+잔액이 별도 커밋이다. 일반/서비스 혼합 진행 시 일반 기록 금액이 전체 진행 횟수 기준으로 저장되는 경로도 있다. `frmSessionRegister.UpdateSession`, `frmFinanceInput.UpdateTransaction`. [K02–K05](11-risks-and-unknowns.md)
3. **락커 유형 충돌**: DDL 주석·조회 SQL·C# enum 값이 서로 다르다. 실제 DB 값을 확인하기 전 관계를 정규화해 해석할 수 없다. `Enums.cs`, `QueryString.cs`, DDL. [K11](11-risks-and-unknowns.md)
4. **고정 거래 반복 판정 결함**: LastInputDate의 일자를 지정일과 비교하여 다음 달에도 처리 대상이 되지 않을 수 있다. `FixedTransaction.CheckLastInputDate`. [K12](11-risks-and-unknowns.md)
5. **인증·초기화 환경 의존**: DPAPI CurrentUser 암호, 하드코딩 DB 연결, 로컬 버전 설정 유실 시 DROP TABLE 경로가 있다. `Secure`, `MariaDB`, `VersionCheck`. [K07–K10](11-risks-and-unknowns.md)

이 발견은 정적 코드의 경로 분석이며 실제 운영 데이터가 손상되었다는 단정은 아니다. 결함을 웹에서 유지해야 할 업무 규칙으로 취급하지 않았다.

## 조사 방법과 한계

- 솔루션/프로젝트·패키지 참조 → 폼/Designer의 메뉴·이벤트 → 모델 → SQL 조립/DDL → 부수 저장과 집계를 추적했다. 주요 결론에 파일·클래스·메서드 또는 행을 붙였다.
- 문서의 추정은 아키텍처 명칭, 사용자 직책, 페이지/API 분리 가능성, 유지 정책처럼 코드만으로 결정할 수 없는 판단에 표시했다.
- 운영 DB·실데이터·실행 UI는 확인하지 않았다. DB 연결·앱 실행·스키마 동기화는 수행하지 않았다. 빌드·기능 테스트 결과를 주장하지 않는다.
- 패키지 압축 내부 바이너리는 분석하지 않았다. 도구/파일 이름이나 using 문만으로 외부 연동 존재를 확정하지 않았다.
- 문서 검증은 요청 파일 존재, 상대 링크, Form/테이블 누락, 기능 명세 항목, UTF-8, 코드 변경 여부를 대상으로 했다. Mermaid는 소스 형식으로 제공하며 실행 UI의 시각적 검증 결과는 아니다.

소스 파일은 `Y3/Y3/` 기준이고 문서 링크는 저장소 안에서 이동할 수 있다. 이후 검토는 [기능 목록](03-feature-inventory.md)과 [업무 흐름](06-business-flows.md)을 운영 담당자와 대조하고, [불명확 사항](11-risks-and-unknowns.md)의 실제 DB/운영 질문을 확인하는 데 사용할 수 있다.

## 2026-09-15 역검증

전체 문서를 코드와 다시 대조했다. [역검증 기록](verification-report.md)에 문서별 변경과 탐색 범위를 정리했다. 가장 큰 정정은 개인 매출등록의 콤보 초기화 누락으로 F22–F25를 정상 사용 가능한 기능으로 단정할 수 없다는 점이다. Transaction의 잘못된 UseFlag 속성 설명, 저장 성공의 의미, 거래 처리 순서, 분류 콤보 갱신 및 락커 갱신 조건도 수정했다. 추가 테이블·Form은 발견하지 못했다. 소스 수정·프로그램 실행·운영 DB 접속은 하지 않았다.
