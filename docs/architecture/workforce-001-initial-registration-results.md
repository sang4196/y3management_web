# WORKFORCE-001 최초 등록 — 개발·독립 검증 결과

2026-10-21. 기준 HEAD `475dd8a1baaf5d5561a1a66742db0c00c7731450`, branch
`codex/workforce-initial-registration`. [좁은 계약](workforce-001-initial-registration-design.md)의
개발 과정과 최종 독립 전체 검증을 구분해 기록한다. 최종 candidate3는 설계자 로컬 인수 PASS다.

## 구현 결과

실제 현재 MFA Master/Branch Admin이 이름·전화·단일 Home·세 보상 값·명시 시작 월을
한 업무로 등록한다. 초기 aggregate/snapshot/operation/두 typed 감사가 함께 확정된다.
금액은 API 문자열과 정확한 NUMERIC으로 저장하고 JS Number·반올림·누락 기본값을 쓰지 않는다.
Base Salary는 명시 시작 월부터의 설정이며 미래 월 행이나 시작 전 0원을 생성하지 않는다.

G1에 따라 신규 등록/배정 후보는 활성 Home만 허용한다. 기존 Trainer/operation/목록 조회와
동일 operation·동일 payload의 replay는 비활성 Home에서도 현재 실제 Home 관리 Scope로
허용한다. replay200은 원래 creator/snapshot/감사를 보존하고 실제 성공 actor의 활동만 갱신한다.
다른 payload409와 실패는 활동까지 rollback한다. 상태/목록은 no-touch/no-GC다.
전화/금액/fingerprint를 최소 식별 DTO·기존 IAM 감사 조회에 넣지 않는다.

Organization scoped fact와 assignable 조건을 분리하고 기존 Branch DTO/Master-only
require_branch 의미를 보존했다. Workforce private SQL은 자기 테이블만 읽는다.
UoW가 공개 port를 조합하고 감사 후 DB 시간으로 현재 계정·권한·CSRF·idle/absolute를
재검사한다. Import Linter의 기존 일곱 계약을 보존하며 Workforce 경계 한 계약을 추가했다.

forward `0010_workforce_initial`은 22자 revision이며 기존 migration/env는 수정하지 않았다.
업무 이력 및 비활성/버전 변경 Branch 사실의 downgrade 정보 손실을 거부한다.
DB의 NOT NULL/FK/CHECK/유일성과 application-UoW의 필수 snapshot/두 감사 존재를 구분한다.
privileged raw SQL 변조까지 막는 trigger/새 Audit framework/secret 체계는 없다.

UI는 명시 POST form과 handler 연결 전 disabled 상태로 no-JS GET 유출을 막는다.
모바일 viewport/같은 origin CSS, 전체 후보 page 순차 로딩을 추가했다. 기존 CSP·8192-byte
예산을 유지하며 W0 validation 오류는 원문 없는 일반 envelope로 반환한다.

## 개발자가 실제 수행한 검증

신규 PostgreSQL/native **28개 서로 다른 사례**를 대상 실행과 보완 재실행으로 확인했다.
하나의 전체 회귀 실행으로 표현하지 않는다. 기본 PG10, integrity7, Branch 선후2,
추가 guard8, native1로 구성된다. 강화한 경합/만료6은 이 중 기존 사례의 재실행이다.
기존 승인된 retained-head 회귀2와 공통 helper의 기존 native3도 별도로 실행했다.

| 검증 | 결과/근거 |
| --- | --- |
| 최종 fast | 122 passed, Ruff/format/mypy86파일, Import Linter8 kept |
| 신규 PG/native | 28개 대상 사례 확인, 강화한 경합/만료6 재실행 passed |
| 실제 HTTPS 신규 브라우저 | 1 passed, Chromium 151.0.7922.34, 32개 확인 모두 true |
| 기존 retained-head 회귀 | 2 passed, 기존 거절/이력 보존 조건 유지 |
| 기존 HTTPS 브라우저 | 3 passed, 확인58/20/15/11/12/23개 모두 true(총139) |
| 전체 수집 | 541개 = 비DB122 + PostgreSQL419, 실행 결과와 구분 |

신규 native는 실제 Master/Branch Admin 설정·MFA 로그인·각 form 신규 등록,
390px overflow/field 폭, 101번째 후보 선택/등록, 1024자리·0·먼 미래 입력,
더블클릭/같은 operation replay/상태 버튼/명시 새 operation을 검사했다.
신뢰 TLS의 Node HTTPS 요청에서 Content-Length 없이 실제 분할 chunk를 전송해 유효 JSON
8192 bytes replay200/8193 bytes413을 확인했다. ASGI 별도 receive 조각 검사도 있다.
no-JS form 강제 제출은 명시 POST이고 URL/query에 민감값이 없다.

DB 검사는 각 Trainer/snapshot/operation/두 감사 저장 단계의 실제 trigger 오류 주입과
전체 rollback, typed 감사/FK/NULL/금액/월 제약, aggregate/snapshot/감사의 정확한
2^53 초과 값과1024자리 값, creator/초기 이력 replay 불변, 현재 Home fixture 변경 후 인가,
실제 다른 관리자 같은 operation 경합과 C2/타 계정·세션 보존을 포함한다.
상태 fixture SQL은 해당 제품 상태변경/이동 기능의 구현·인수가 아니다.

최종 수집만 하는 실행의 exit1은 mandatory PG no-pass gate다. 수집을 실행 성공으로
표시하지 않는다. 개발자는 전체 PostgreSQL419를 실행하지 않았다. 원래 IAM010의 전체
인수를 W0 인수로 확대하지 않으며 독립 전체 검증은 별도 진입 뒤 수행한다.

## 실패 기록과 설계자 지적 보완

- 최초10개는 새 fixture가 기존 지점 생성 URL을 잘못 호출한405 준비 오류였다.
  `/admin/branches`로 바로잡았다. 제품 인가를 낮추지 않았다.
- 초기 native는 테스트의 제출값 캡처가 후속 오류 요청으로 덮이고 form의 submit ID가
  메서드를 가리는 문제였다. 최초 명령만 캡처하고 prototype submit으로 no-JS 검사를 보완했다.
- 추가 guard는6 passed/2 failed였다. absolute fixture는 Session과 slot FK의 만료를 동일 CTE로
  이동하도록 수정했고, C2 실패 로그인은 로그인된 사용자409를 받지 않도록 별도 비인증 client를
  사용했다. 두 사례를 실제 재실행해 통과했다.
- 확장 native manifest가 숫자를 포함한8192/8193 키를 누락해 실패했다. 실제32개 키로 바로잡고
  다시 통과했다. 처음부터 통과한 것으로 덮어쓰지 않았다.
- WF-UI-MOBILE-001: 최소 모바일 viewport/CSS와 native390px 폭 검사를 추가했다.
- WF-UI-CANDIDATES-001: limit100을 업무 상한으로 쓰지 않도록 끝까지 순차 로딩하고
  실제101번째 후보 등록을 확인했다.
- WF-RACE-BLOCK-001: 단순 future 제출 순서에서 강화해 첫 transaction release 전에 실제
  두 번째 소유 PID가 첫 PID에 막혔음을 pg_blocking_pids로 확인하고 worker 미완료를 검사한다.
- WF-LATE-PHASE-001: 감사 callback의 실제 도달/같은 transaction의 필수 쓰기 전부 존재와
  처음 두 deadline 유효를 확인하고, DB 대기 뒤 선택한 idle 또는 absolute만 만료됐음을 확인한
  후401/전체 rollback을 검사한다. 사전 touch나 expiry 완화는 없다.

고정 head 기대값은 설계자가 승인한 두 파일의 비교 상수 한 번씩만
`0009_iam_emergency_handoff`에서 `0010_workforce_initial`로 변경했다.
35자 파일 stem 대신22자 revision을 써 기존 version column 범위를 보존한다.
old migration/env/거절 guard/역사 보존 검사는 유지했다.

## 인계 범위

QA는 ignored `.local/qa/workforce-initial-registration-aac0d3a0d2db4c7b/`의 로그,
최소 browser 보고, `developer-result.json`, `source-frozen.json`, finding resolution에 남긴다.
candidate1에서는 보호 entry revision2의182개 및 exact 승인 예외2개의 SHA를 확인했다. root 단계 문서 두 개와
HEAD/index도 보존했다. 모든 기록된 자기 실행은 removed=true 및 실행 폴더 부재를 확인했다.
소스 manifest 이후 제품 runtime은 바뀌지 않았고 경합/만료 테스트 두 파일만 강화 후
6개 재실행과 최종 fast/수집을 마쳤다. 전체/Backend 파일 SHA manifest와 결과 JSON을
기록하고 source_writer_stopped=true로 동결했다.
기존 Product/ADR·IAM package·conftest·dependency/lock과 root 단계 문서 두 개를 보존한다.
계정 연결·Trainer 로그인·일반 수정·Home 이동·PT/정산·production·실물/전체 지원 브라우저
인수는 제외한다. 기존 Starlette HTTPX/AnyIO 경고는 남아 있다.
개발자는 stage/commit/push나 다른 세션 메시지를 수행하지 않는다.


## candidate2 — 기존 MFA 설치 잠금 관찰 보완

최초 독립 전체 PG 실행은 204 passed / 1 failed / 214 미완료로 중단·정리됐다.
동일 소스 개별 진단에서 실제 migration 연결이 allocation 연결에 막혀 있었지만,
기존 SQL prefix 관찰이 새 migration의 LOCK 문을 놓친 것으로 확인됐다.
이는 독립 담당의 기록이며 전체419 통과 결과가 아니다.

설계자의 revision3 제한 승인으로 `test_iam_mfa_install.py`의 해당 테스트 한 함수와
고유 식별용 uuid4 import만 수정했다. 자식에 고유 PGAPPNAME을 주고 동일 DB의 해당
migration PID에 대해 pg_blocking_pids가 실제 allocation PID를 포함하는지 검사한다.
기존5초 관찰 deadline, 실제 미확정 allocation, commit 이후10초 communicate,
비0 종료·fingerprint 보존과 finally 자기 프로세스 정리를 유지한다.
제품 runtime·migration·fixtures·의존성 및 다른 테스트 함수는 변경하지 않았다.

보완 후 개발자가 해당 모듈 전체10개 DB 검사와 fast122개를 통과했다.
Ruff/format/mypy86파일·Import Linter8 kept, 수집541개를 확인했다.
수집 전용 실행은 필수 PG 통과 조건에 따라 exit1이며 실행 성공이 아니다.
이번에는 브라우저/전체419를 재실행하지 않았다. candidate2 동결 후 설계자 재검토와
새 독립 전체419 검증을 기다린다. revision3 보호181개와 고정207개,
기존 타 함수 AST·runtime 바이트 보존 및 자기 실행 정리 증빙은 repair-result.json에 기록한다.


## candidate3 — Reset 저장 잠금 관찰 보완

candidate2의 독립 fast/전체 PG는 시작되지 않았다. 설계자 사전 검색에서 남은 같은
SQL prefix 관찰을 발견했고, 독립 단일 재현에서 실제 Reset allocation이 migration을
막고 있어도 관찰식이 놓치는 동일 원인이 확인됐다. 원래 전체 PG 결과는 여전히
204 passed / 1 failed / 214 미완료이며 통과로 바꾸지 않는다.

revision4 제한 승인으로 `test_iam_password_reset_storage.py`의 지정 함수 하나만
고유 PGAPPNAME과 실제 allocation PID의 pg_blocking_pids 검사로 보완했다.
기존 import·타 함수, 실제 password_reset allocation/commit,5초 관찰·10초 communicate,
비0 종료/fingerprint 보존/finally 정리 및 candidate2 MFA 보완을 그대로 유지했다.
제품 runtime·migration·fixtures·의존성과 다른207개 파일은 변경하지 않았다.

보완 뒤 해당 Reset 모듈15개 DB 검사와 fast122개가 통과했다.
Ruff/format/mypy86파일·Import Linter8 kept 및 전체 수집541개(122+419)를 확인했다.
수집 전용 실행은 필수 PG 통과 조건으로 exit1이며 실행 성공이 아니다.
개발자의 전체419/브라우저 재실행은 없었다. 보호 revision4/180개 및 고정207개,
AST·runtime 바이트 보존·자기 실행 정리 증빙은 repair-result-candidate3.json에 기록했다.
candidate3 동결 후 설계자 범위 검토와 새 독립 전체 검증을 기다린다.


## 최종 candidate3 — 독립 전체 검증·설계자 인수 PASS

동결210개/Backend133개·보호180개 revision4에서 독립 fast122개와 PostgreSQL 전체419개를 통과했다.
이 PG는 기존391개와 신규28개를 포함한 **새 단일 전체 실행**이다. 총541개가 통과했고,
실패/error/skip/xfail/xpass/incomplete는0이다. 최종 PG 소요 시간은2,265.57초다.
개발 subset이나 최초 중단 실행의 성공을 이번 수치에 합치지 않는다. candidate2의 독립 fast/전체PG는 시작하지 않았다.

같은 PG run `auto-7b0a9340c8ab4817b41ca93e2e47b651`의 실제 HTTPS/native8개 manifest
58/20/15/11/12/23/17/32항목 총188개가 exact keys/literal true로 확인됐다.
Chromium151.0.7922.34, 신뢰 CA/hostname/sandbox/전역 trust 경계를 유지했다.
188항목은 브라우저 pytest5건 안의 항목이며541개에 더하는 별도 테스트가 아니다.
새32항목은 실제 Master/Branch Admin의 등록 form·390px·101번째 후보·큰 금액/명시0/먼 미래·
더블클릭/같은 operation/상태 확인/명시 새 등록·신뢰 TLS chunked8192/8193·no-JS POST를 포함한다.

실제 JUnit419개 전부 passed였으며 이전 관찰 실패 두 node의 passed도 확인했다.
최소 verdict와 report digest를 남긴 뒤 비공개 원본 JUnit은 제거했다. 처음 중단한204 passed/1 failed/214 미완료,
동일 소스 개별 진단 두 건의 실패와 원인은 그대로 기록한다. 최초 중단 시 다른 fixture bootstrap 중의
KeyboardInterrupt와 뒤따른 tmp_path stash KeyError는 원래 실패와 구분한다. fixture 정리는 완료됐다.

최종 전체 실행에서 현재 Scope/G1·필수 저장/각 typed 감사의 실제 실패 rollback·정확한 값 저장·
두 실제 MFA Actor의 operation 경합·실제 PID 대기 선후·감사 이후 선택한 idle/absolute만 만료·
실제 COMMIT 뒤 ACK 상실/상태/replay·기존 이력과0010 정보 손실 보호를 확인했다.
등록 성공/재요청의 정상 활동과 실패/조회 no-touch, C2/타 계정 보존을 구분했다.

전후 전체 source/보호 SHA·HEAD/index·전역 trust 일치와 fixture/capture 자동 환경4개 정리를 확인했다.
추가 읽기 관찰의413개 schema/14개 process 잔존 없음은 전체 fixture 정리 guard를 보충한다.
관찰 목록만으로 모든 자원의 완전한 목록을 주장하지 않는다. 미정리 항목은 없다.
설계자는 소스와 실행 근거를 검토했으며 runtime을 추가 실행하지 않았다.

이후 변경은 현재 단계/설계/결과/검증 계획/최소 판정 문서뿐이다. 테스트된 Backend133개 바이트는 유지한다.
[설계자 판정](workforce-001-initial-registration-review.json)에 최종 source manifest와 실제 최소 근거를 남긴다.
전담 커밋 담당자가 최종 변경 검토 후 한글 상세 커밋·일반 push를 수행하는 순서다.

최소 등록 화면의 기존 목록은 첫25개 보조 표시이며 API의 offset/limit 조회는 제공한다. 업무상25명 상한은 없다.
계정 발급·Trainer 로그인은 I1 후속이며 필요한 세 운영 선택은 사용자 답변 대기다. I2/상태·Home 이동/일반 수정·
PT/지급/정산·production·실물/지원 브라우저 전체·운영 보존을 이번 인수로 확대하지 않는다.
Product22 OPEN/8 CLOSED·PD1 OPEN/26 CLOSED 및 ADR/전체 모듈 PROPOSED 상태를 유지한다.
