# IAM-006 개발 결과

2026-10-18 최신 판정: **IAM-007과 결합한 관리자 자격 관리의 제한된 로컬 인수 PASS**.
[최종 결합 결과](iam-007-password-reset-results.md)와 [설계자 근거](iam-007-password-reset-review.json)를 따른다.
최종 fast91, 원래 전체PG245의244 성공 및 테스트 전용 정정 후 독립2 성공으로 최종PG246 항목을 분할 검증했다.
원래 전체 실행의 키 선택 테스트1 실패/exit1은 그대로 남긴다. 앱·다른105개 파일과 같은 모듈의
나머지 AST는 보존했고 최종 항목 집합에 누락/추가/중복이 없다. 246 단일 전체 실행 PASS가 아니다.
실제 같은 앱의 HTTPS58/MFA20/management15/reset11은 모두 true다. M8 관리자 reset은 IAM-007에 포함된다.

아래 후보1/2/3의 수치·동결·인계 지시·후속 범위는 당시 개발 이력이다.
특히 아래 fast90/PG195 인계 문구나 M8 미포함 설명을 현재 결합 인수 상태로 읽지 않는다.
현재 실행 환경/정리와 남은 운영 범위는 IAM-007 결과를 따른다.

2026-10-18 후보2 동결은 제한 해동됐으며 **candidate revision3**에서 IAM-007 reset과 결합한다.
후보2 독립 PG155 통과·40 미완료 후 중단했으며 전체 인수가 아니다.
후보3는 개발 완료·동결했으며 fast91/대상 검증 결과와 새336개 수집은 아래 IAM-007 결과를 따른다.
[후보3 결과](iam-007-password-reset-results.md)의 최종 동결·독립 검증이 후속이다.
부모 commit `49eadf724185f6ece67ba1daa264823553e58ba7`, 작업 branch
`codex/iam-mfa-management`. 개발자가 commit/push하지 않았다.


## 후보 1 중단과 C3 제한 수정

후보1 독립 검사에서 fast90 통과, PG14 통과·기존 HTTPS1 실패·179 미완료 후 중단했다.
child pytest exit1, shell exit130이며 **전체 인수 통과가 아니다**. 독립 HTTPS 실패의 원인을
자동으로 C3로 단정하지 않는다. 독립 실행의 종료·자원 정리를 root가 확인한 뒤 제한 해동했다.

개발자가 후속 계획을 읽기 전용으로 검토하던 중 MGM-C3-SELECT-001을 발견했고 root가
확인했다. C3 `IAM.change_password`가 SELECT에 없는 recovery_pending을 참조했다.
수정 전 기존 Master 정상 변경·두 세션 검사가 실제 실패했다
(`auto-d15a8f8e728047038f64955ecb57b1a8`, 1 failed, traceback 비출력).
제품 변경은 최종 SELECT에 해당 열을 명시적으로 추가한 것뿐이다. guard는 유지했다.

수정 후 기존 Master/Branch C3 성공·모든 세션 철회, 잘못된 현재 암호·정책·철회 세션 거부,
stale proof 경쟁, hashing 중 차단/Scope 변경, 감사/ACK 원자성 및 새 정상 MFA 양성 회귀를
합쳐 **11 passed**였다(`auto-e860e6f8366f4406ab735149239b33ae`). 새 검사는 실제 MFA
두 로그인에서 본인 암호 변경 → 옛 세션/암호 거부 → 같은 Passkey와 새 암호 로그인,
키 metadata/키셋/Scope 보존을 검증한다. 실행 폴더·process·schema는 모두 정리됐다.
비밀번호 reset 기능이나 정책·의존성·migration 변경은 없다.

후보2에서는 새 fast90 및 위 C3 대상11을 실행했다. 아래 후보1 개발 native/부분PG 결과를
후보2 전체 독립 결과로 재사용하지 않는다. fresh 전체 독립 검증은 별도 진입 후 수행한다.

## 구현

- B1 본인 active Passkey 최소 목록·마지막 키 보호·삭제 시 모든 기존 로그인/대기 권한 철회.
- B2 정상 같은 조직 Master의 추가 Master 신규 발급·조회·최초 설정 재발급과 실제 본인 MFA 설정.
- C 다른 정상 Master의 ACTIVE 관리자 분실 복구, 별도30분 단회 source와5분 context,
  모든 옛 키/로그인 철회·새 UV 키·기존 비밀번호 보존·명시적 재발급.
- 새0006 forward migration, 키 tombstone/키셋/복구 세대, 정확한 서버 키 UUID와 전후
  키셋·세대 감사. 이전0001–0005·ADR·AGENTS·의존성 lock을 보존했다.
- 복구 대기 권한 우회 방지, 마지막 키 및 상호 복구 직렬화, crypto 후 최종 권한 재검사,
  감사 원자성·COMMIT ACK 불확실성의 상태 확인 계약을 유지했다.

[설계](iam-006-mfa-management-design.md)의 API/인가/잠금/운영 경계를 따른다.

## 실제 개발 검사

최종 `backend/`의 `bash check.sh fast`: Ruff/format, mypy55개 파일,
DB 없는 pytest **90 passed**, Import Linter **7 kept**.
수집은 총 **285개 = fast90 + PostgreSQL195**였다.
실행 ID: `auto-7c571255b4d54ec2b4c4bb832606a2c3` (candidate2).

다음 표는 candidate1 개발 중 PostgreSQL 대상 검사 이력이다. 아래 수치는 겹치는 검사를 포함하므로
합산하거나 최종 필수PG195 전체 통과로 해석하지 않는다.

| 대상 실행 | 실제 결과 | 근거 |
| --- | --- | --- |
| B1/B2 초기 실제 설정·로그인 | 2 passed | `auto-855fd5613e8b453297a4d63ca41ac1eb` |
| 초기 B1/B2/실제 Master·Branch 복구 | 4 passed | `auto-422023ee8d3746b79620e5f3e48caa25` |
| 최종 감사 metadata를 포함한 B1/B2/복구 핵심 | 핵심4개 통과; 뒤의 별도 absolute-expiry fixture에서 중단 | `auto-54c4678560234cb2b2f34dbb27b77901` |
| 현재 인가/만료/상태변경·GC·migration·감사 rollback/ACK·C2 | **40 passed** | `auto-bbe36b0b29694c24b057df26bb843d42` |
| 독립 연결 관리 경합4개 + 기존 MFA 설치/migration10개 | **14 passed** | `auto-f616c84d885b4703ab3afae35a8c26bf` |
| crypto 후 삭제가 login/add 최종 저장을 앞서는 경합 | **2 passed** | `auto-ea71ac4d26f04094a63e97ca457485bf` |
| 재발급의 정확한 키셋·세대 감사 metadata | **1 passed** | `auto-8410617c91f54f3c83668bd9f804adf0` |
| 최종 DDL guard의 실제 할당 대기·빈 왕복 | **2 passed** | `auto-a13c9e2e9eb84073bc842506c5408534` |
| trusted HTTPS/native WebAuthn | **1 passed**, 기존MFA20+관리15 전부true | `auto-251ecf5146d1482d8e8bd9cf51378c6d` |

native 브라우저는 Chromium **151.0.7922.34**다. 실제 navigator.credentials.create/get,
서로 다른 가상 인증기, 복수 browser 세션, 삭제 후 모든 옛 세션 거부/남은 키 로그인,
추가 Master 본인 설정, Master·Branch Admin 복구를 검사했다. 기존HTTPS58 manifest와
MFA20 manifest를 보존했다. 기존HTTPS58 전체의 이번 변경 후 재실행은 독립PG 전체에 맡긴다.
가상 인증기 검증을 실물 장치·모바일·전체 지원 브라우저 인수로 확대하지 않는다.

## 발견·수정과 실패 이력

MGM-GC-001: 잠긴 하위 context를 SKIP LOCKED로 건너뛰어도 만료 source의 FK cascade가
그 context에 다시 진입했다. 독립 PG 연결/300ms lock_timeout으로 setup/recovery 각각
실패를 재현했다(`auto-c8bf7095562c4245afeda7a06bee8e3b`, 2 failed).
source의 남은 하위 절차를 제외하고 부모 잠금 뒤 새 snapshot에서 재검사하도록 수정했다.
잠금 중 부모 보존·해제 후 다음 GC 제거가 두 사례 모두 통과했다. 최종 대상40에도 포함됐다.
0006 DDL은 security_control을 먼저 잠근 뒤 업무 테이블 잠금을 얻는다.

MGM-PRIV-001: 보호된 문자열의 split 결과가 일반 str로 변하는 테스트 위험을 보완했다.
공통 link_token extractor와 CSRF 반환을 repr 보호하고, 비밀번호 보존은 SQL fingerprint로
비교한다. 실제 extractor→enroll/recovery_options→실패 locals 경로와 입력 DTO에 대해
unbound 가상 canary를 사용했다. child pytest의 의도적 실패를 parent가 확인하는2개 검사와
최종 fast가 통과했다. 실제 유효 토큰/비밀번호 hash를 보고서에 출력하지 않았다.

MGM-AUD-001: 삭제 키 UUID와 키셋·복구 세대 전후 값의 typed 감사 필드를 추가했다.
실제 DB metadata, 각 명령의 감사 실패/ACK 유실, metadata 자체의 downgrade 보존을 검사했다.

그 밖의 개발 중 실패는 새 audit seed의 request_id 누락, 감사 조회 timestamp 필드명 오기,
만료 fixture의 session 시각 제약/FK 불일치, native driver의 인증기 선택이었다. 각각 원인을
수정해 해당 조건을 다시 실행했다. native driver는 현재 signCount를 가져오고 새 키에는
별도 인증기를 사용한다. 제품 verifier/counter/UV·backup 계약이나 DB counter를 낮추지 않았다.
초기 실패와 이후 통과를 구분한 최소 이력은 공유 developer-result/progress에 남긴다.

## 정리·인계·남은 범위

모든 기록된 자동 실행은 자기 process/schema/고유 실행 폴더를 정리했다. 미정리·보존 환경은
없다. 기존 공유 Compose postgres-test/volume과 root 공유 인계 폴더는 보존한다.
Starlette/httpx·AnyIO 기존 deprecation warning2개를 숨기거나 dependency upgrade하지 않았다.

동결 manifest와 최소 개발 결과는 `.local/qa/iam-mfa-management-b2f1b730a9614672/`의
`source-frozen.json`, `developer-result.json`에 있다. 독립 담당자는 같은 동결에서
fast90와 **필수PG195 전체**, 기존HTTPS58·MFA20·관리15 및 정리를 실제 실행해야 한다.
독립 결과와 설계자 인수 전에는 전체 통과·운영 허가·commit/push 완료로 보고하지 않는다.

새 제품 질문은 없다. production·AB5·운영 본인확인/전달·기록 보존/열람/파기·실물 기기와
지원 브라우저 인수는 미완료다. M8 관리자 password reset, DISABLED/PENDING_SETUP 복구 변형,
승격/강등, 최종 Responsive UI도 이번 완료 범위에 포함하지 않는다.
