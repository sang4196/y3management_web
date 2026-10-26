# IAM-011 Trainer 로그인 개발·독립 검증·인수 결과

2026-10-27 **설계자 로컬 인수 PASS**. [영구 판정](iam-011-trainer-login-review.json)의 실제 판정·
소스 SHA·원래 실패와 한계를 따른다. r3 동결225개/Backend145개에서 새 독립 fast131 및
**단일 전체 PostgreSQL499(기존419+신규80)**가 모두 통과했다. 총630개는 서로 다른 pytest 사례이며,
실제 HTTPS/native211항목은 그중 브라우저 pytest6건 안의 검사다. 같은 실행의9개 manifest에서
정확한 key 집합과 모든 literal true를 확인했다. 실패/error/skip/xfail/xpass/incomplete는0이고
pytest/child bash/runner의 실제 exit는0이다. PG 실행 시간은3000.14초였다.

실제 W0→현재 Master/해당 Home Branch Admin 발급→수신자 직접 설정→Trainer 암호 로그인/me→
본인 암호 변경·자기 전 로그인 철회→새 로그인/로그아웃을 검증했다. 비활성 Home 허용과 실제 Trainer 활성,
일대일/중복 방지·현재 Scope·설정 source 단회/재발급·token 없는 replay/status·typed Audit/rollback,
실제 PG 대기·원래 기한의 최종 DB 시각·COMMIT/finish ACK 불명도 확인했다.
기존 S1 호환 및403/401 경계를 앱에서 복원했고, 원래 실패 단언과 새 ACK/인가 보호를 유지했다.

검증 전후 소스/보호/HEAD/index/trust 불변과 소유 자동 환경7개 정리를 확인했다. 설계자는 추가 runtime을
실행하지 않고 소스와 실제 사례·native·정리 근거를 대조했다. 이후 수정은 결과/단계/판정 문서뿐이며
테스트한 Backend145개 바이트를 유지한다. 전담 변경 검토·한글 상세 커밋·feature branch 일반 push가 후속 절차다.

두 중단 실행15/2/464와89/1/396, 개발 당시 부분 실행·fixture 실패를 아래 이력과 판정에 보존한다.
이전 bootstrap 오류는 원인 미확정이다. 동일 node가 단독 및 최종 전체에서 통과한 사실을 원인 규명으로
바꾸지 않는다. 완료한 원본 로그/캡처/실패 환경은 영구 요약·최소 재현 근거로 대체한 뒤 QA 정책에 따라 정리한다.
아래 파일명과 부분 검사 기록은 개발 당시 이력이며 영구 근거는 위 판정이다.

인수 한계: 로컬 desktop Chromium 인증 흐름이다. 신규 Trainer 모바일 viewport/실물/전체 지원 브라우저,
운영 설치·전달·보존·배포는 미인수다. 기존 공용 MFA 로그인 화면의 모바일 viewport 보완도 남는다.
정적 `/trainers` shell은 열릴 수 있지만 개인정보/목록/직접ID/쓰기 API 권한을 부여하지 않는다.
최소 관리 목록 UI의 첫25개 표시와 후속 전체 관리 UX도 별도다. I2 역할 연결/회수·무역할 로그인,
상태/Home 변경·분실 암호 reset·Operator/회원/PT/정산을 구현했다고 보고하지 않는다.

2026-10-27 r3 개발 검증: r2 독립 whole은 **89 passed/1 failed/396 미완료**로 중단·정리했다.
실제 실패는 `test_current_actor_authority[DELETE FROM iam_admin_grants WHERE account_id=:a-403]`의
`401 == 403` 불일치다. 같은 실행 native156항목은 모두 true였지만 전체211 인수는 아니다.
`independent-second-attempt.json`에 원래 assertion/중단/소유 환경 정리 결과를 보존했다.

승인된 r3 앱 수정은 `IAM.authenticate` 하나다. 세션·계정·security version·만료·철회 및
필요 MFA UV/유효 키를 먼저 검증하고, 유효하지만 현재 grant/binding 없는 관리 audience는
활동 시각 갱신/Caller 반환 전403으로 거절한다. 무효 인증401, account audience 미지원 계정401,
Trainer-only 관리 audience401과 self의 현재 Workforce 검사, 관리자 Scope 인가는 유지한다.
무역할 로그인/새 역할 정책을 추가하지 않았다. r2 Service 복원과 기존 모든 테스트는 그대로다.

`r3-targeted-pg.log`는 **39 passed/2 failed**였다. 기존 handoff authority3·Master guard18,
Trainer self/거부/혼합 UV/ACK/finish7개와 신규 matrix11개가 통과했다. 새 matrix의 absolute/reset
두 fixture는 인증 검사 전 각각 `iam_sessions_check`/`iam_accounts_check`를 위반했다.
앱/기존 테스트/DB 제약을 바꾸지 않고 신규 fixture만 기존 slot 동시 만료 패턴과 유효한 reset
상태로 고쳤다. `r3-fixture-retry-pg.log`는 해당 **2 passed**다. 원래 실패 로그는 QA에 보존한다.
새 matrix13개는 실제 MFA 또는 S1 로그인 후 소유 schema에서 경계 상태를 구성한다. 거절을 UoW
안에서 잡고 commit한 뒤 기존 snapshot을 비교해 잘못된 touch/audit가 rollback에 가려지지 않게 한다.
39+2는 분할 검증 결과이며 단일 whole PASS가 아니다.

r3 최종 fast는 Ruff/format/mypy95·pytest131·Import Linter8을 통과했다. 정확 수집은
총630/PG499/비PG131, W0 이후 신규89(정책9/PG80), r2 대비 신규 matrix13개다.
기존 native manifest211은 그대로이며 이번 r3에서는 브라우저를 재실행하지 않았다.
collect-only 종료1은 기존 PG 미실행 guard이며 수집만 확인했고 실행 통과로 해석하지 않았다.
r3 자동 실행 receipt5개는 모두 removed=true 및 경로 부재를 확인했다. 공유 Compose는 유지한다.

r3 최종 fast·정확 수집·파일 동결은 `developer-result-r3.json`, `case-inventory-r3.json`,
`source-frozen-r3.json`을 따른다. 원래 r1/r2 파일은 덮어쓰지 않는다. 새 단일 전체 PG와 native211의
독립 검증·설계자 인수·커밋/푸시는 별도 진입이며 아직 완료하지 않았다.

아래는 r2 및 r1 당시 기록이다.

2026-10-26 r2 개발 동결: 첫 독립 전체 실행에서 기존 S1 회귀2건이 확인되어 중단·정리 후 좁게 복원했다.
아래 최초 개발 결과는 당시 부분 검사 기록이며 전체 인수 PASS가 아니다.

원래 whole은 JUnit17개 중15 passed/2 failed, 나머지464개 미완료였다.
`test_commit_ack_loss_preserves_committed_children`은 live child 기대1에 실제0,
`test_business_commit_precedes_waiting_management[login]`은 account 잠금 도달 대기 실패였다.
새 공통 login cleanup/installation 선취를 제한 S1까지 적용한 범위 확대가 원인이었다.
기존 두 assertion을 수정하지 않고 서버 mode에 따라 HEAD S1 본문을 복원했다.
S1의 ACK503/no-cookie/커밋된 child 보존과 MFA Trainer 미전달 sid 철회를 명시적으로 구분한다.
재귀/중복 admission 방지와 S1 실제 admin guard만 HEAD 본문에 추가했다.
앱 변경은 `use_cases.py` 하나이며 초기 freeze/실패/중단 증거는 보존한다.

r2의 `r2-old-failures-pg.log`는 기존 실패2건과 setup parameter까지 **3 passed**다.
`r2-trainer-guards-pg.log`는 dispatch5·Trainer ACK·단일 proof·G01–G06 포함 **22 passed**다.
`r2-legacy-and-native-pg.log`는 **16 passed/1 setup error**였다. 기존
`test_crypto_rejection[up]`의 MFA fixture에서 bootstrap CLI code1(기대0)로 실패했다.
기존 CLI는 예외를 `IAM_COMMAND_FAILED`로 감추고 helper는 보호된 출력 원문을 저장하지 않으므로
이 기록만으로 구체 예외/timeout/환경 경합/앱 회귀를 특정할 수 없다. bootstrap 메서드는 HEAD와 AST가 같고 CLI,
fixture/assertion/timeout은 r1과 동일하다. 다른 대상군 종료 후 소스를 바꾸지 않고 동일 node를
단독 실행한 `r2-crypto-serial-pg.log`는 **1 passed**다. 이는 최초 오류 원인 해결의 증거가 아니며
**원인 미확정·단독 재현 안 됨**으로 남긴다. 원래 오류 로그를 보존하고 독립 검증에 인계한다.

r2 fast는 Ruff/format/mypy94·pytest131·Import Linter8개 계약을 통과했다.
위 legacy/native 실행의 실제 HTTPS Trainer 항목23/23은 모두 true였다(`native-r2-checks.json`).
새 테스트는 dispatch5개뿐이며 기존 실패2건과 모든 r1 ACK/finish/G01–G06 assertion은 그대로다.
수집은 **총617/PG486/비PG131**, W0 이후 신규76(정책9/PG67), native manifest211이다.
collect-only 종료1은 기존 sessionfinish의 PG 미실행 guard에 따른 것으로 수집 목록만 검증했고
실행 PASS로 처리하지 않았다. 여러 대상 실행과 재실행을 단일 전체 실행으로 합산하지 않는다.

최종 근거는 QA `developer-result-r2.json`, `case-inventory-r2.json`, `source-frozen-r2.json`이다.
전체 독립 PG486/native211 재검증은 별도 진입이다. 초기 `source-frozen.json`을 덮어쓰지 않는다.
r2 실행 receipt7개는 모두 removed=true 및 경로 부재를 확인했다. 공유 Compose와 원래 이력은 유지한다.
아래는 **r1 당시 결과**이며 현재 r2 독립 인수 결과가 아니다.

2026-10-26 최초 개발 검증 결과. 독립 전체 검사·설계자 인수·커밋/푸시는 수행하지 않았다.
[계약](iam-011-trainer-login-design.md)과 [I1-Q1–Q3 승인](../product/product-decisions.md#review-20261026-i1)을 따른다.
기준 HEAD는 `4deb779b622f34d3aac17c30259b47faf781f629`, 브랜치는 `codex/iam-trainer-login`이다.

## 구현 범위

실제 W0 Trainer와 명시적 일대일 IAM binding을 연결한다. 현재 Master 또는 실제 Home Branch Admin이
활성 Trainer에게 신규 계정을 발급하며 PENDING_SETUP에서만 명시 재발급한다. 비활성 Home는 허용한다.
operation replay/status는 원래 비밀을 반환하지 않으며, COMMIT 응답 유실 뒤 상태 확인과 새 operation의
명시 재발급으로 복구한다. 기존 Login ID 재사용/기존 계정 자동 연결/ACTIVE 덮어쓰기는 허용하지 않는다.

단회 목적별 초기 source로 본인 비밀번호를 설정한다. Trainer-only는 기존 로그인 요청의 한 번의
reserve/암호 검증 뒤 password AuthSession을 받는다. 실제 관리자 grant가 있으면 기존 UV 경로를 유지한다.
me·csrf·logout·본인 암호 변경·기존 쿠키 검사에서 현재 Workforce active/Home를 다시 확인한다.
초기 설정·발급·로그인·로그아웃·암호 변경과 typed 감사는 같은 업무 transaction으로 처리한다.

`/trainers`에 계정 발급·상태·초기 링크 재발급 UI를 추가했다. 수신자는 `/trainer-activate`와 `/account`를
사용한다. 링크 fragment를 즉시 제거하고, 상태 확인 시 화면의 이전 링크도 지운다. 새 I1 validation 응답은
입력 원문을 반환하지 않는다. 기존 8192-byte 요청 예산, old migrations/env/dependencies는 유지한다.
`/trainers`의 개인정보 없는 정적 shell은 열릴 수 있으나 데이터/쓰기 API는 관리자 인가를 요구한다.
본인 `/account`는 현재 인증을 확인한다. shell 표시를 관리 권한 또는 페이지 전체 차단으로 보고하지 않는다.

## 개발 검증과 정확한 범위

최종 실행 값은 아래 QA 파일에서 확인한다. 여러 부분 실행을 단일 전체 실행으로 합산하지 않는다.
실행 루트: `.local/qa/iam-trainer-login-07f93e7705ed497d/`.

| 실행 | 검증 범위 | 결과 |
| --- | --- | --- |
| `fast-source-final.log` | Ruff/format/mypy, DB 없는 pytest, Import Linter | 131 passed; Ruff/format/mypy·8 contracts 통과 |
| `trainer-final-targeted-pg.log` | 실제 수직 흐름·권한/상태·ACK·저장 제약/GC·5경합·감사/기한·native | 40 passed; 같은 실행의 신규 native23/23 true |
| `trainer-source-races-pg.log` | 재발급→소비, 소비→재발급, 소비→소비; 서로 다른 PID와 `pg_blocking_pids` | 3 passed |
| `trainer-final-boundaries-pg.log` | body413와 여섯 INSERT 실패 경계, 최초 self deadline fixture | 2 passed / 2 failed; 아래 수정 이력 |
| `trainer-self-deadlines-second.log` | C3/logout 감사 후 실제 idle 만료·전이 rollback | 2 passed |
| `targeted-legacy-pg.log` | S1 수직 흐름, MFA crypto/UV/C2, Login ID, 기존 migration 보호 3건 | 16 passed |
| `trainer-review-gaps-pg.log`, `trainer-review-deadlines-second.log` | 사전 검토 G01–G06 추가15개 | 첫7 passed/8 failed 뒤 만료8개 재실행 passed |
| `trainer-api-boundary-pg.log` | Trainer 관리 목록/직접ID/상태/쓰기 거부 추가 단언 | 1 passed (기존 신규 case 중복 재검증) |
| `collection-final-all.log`, `collection-final-pg.log`, `case-inventory.json` | 전체/신규 node ID, native manifest 정확 집합 | 총612; 기존541 + 신규71 |

신규71개는 정책9/PG62이다. 신규 PG62개는 위 대상 실행들에서 모두 확인했으며 단일 전체 실행 합계가 아니다. 기존 PG419를 포함한 **전체481개 단일 독립 PG 실행은 아직 하지 않았다**.
기존 native188개와 신규23개를 합친 manifest211개도 전체 인수 결과가 아니다.
개발 native는 기존 TLS/CA/NSS/Chromium sandbox/cleanup helper를 재사용하며 TestClient 결과와 구분한다.

동결 전 검토의 추가15개는 `test_iam_trainer_review.py`에 구성했다. stale preflight를 끝낸 요청을
잠금 전 멈춘 뒤 다른 actor의 실제 commit을 완료하고 재개한다. finish 자체 실패/finish COMMIT ACK 유실에서
독립 reader가 business commit을 확인하며 자기 미전달 session만 철회하고 C2/다른 session을 보존한다.
양방향 일대일을 각각 다른 유효 원본으로 검사하고 wrong-org/nonexistent FK를 분리한다.
새 downgrade의 실제 PGAPPNAME/PID 대기와 현재 이력 보존, 같은 account의 inactive Trainer+admin UV도 검사한다.
발급/재발급/C3/logout × idle-only/absolute-only의8개는 감사 전 두 기한 유효, 감사 후 선택 기한만 만료,
원래 last_activity와 계정/감사 rollback을 직접 비교한다. 최종 실행 결과는 `trainer-review-gaps-pg.log`와
`trainer-review-deadlines-second.log`, `pre-freeze-gap-resolution.json`을 따른다.

## 발견과 수정 이력

- 전용 Compose DB 중지로 최초 대상 실행은 사전조건10 errors였다. DB에 접근하지 않았고 소유 fixture를 정리했다.
  기존 소유 Compose 서비스만 시작한 뒤 첫 수직 흐름10개가 통과했다. 원래 실패 로그를 보존한다.
- expanded 실행24 passed/2 failed: 13KB 입력은 기존 body413이 먼저 적용되므로 field422 테스트를
  650-byte 입력으로 수정하고, 별도 oversized413/비노출 검사를 추가했다. 요청 예산은 변경하지 않았다.
- 첫 native는 발급 응답 직후 상태 갱신 중 refresh 클릭을 busy guard가 무시했다. 갱신 완료까지 버튼을
  비활성화했다. 다음 native에서 status 링크 제거가 통과했다.
- 다음 native의 23항목 중2개는 테스트가 roles 문자열과 잘못된 GET 경로를 가정했다.
  실제 DTO의 `roles[].role=TRAINER`, trainer ID/capabilities 및 기존 `/branches` 경로로 수정했다.
- 감사 rollback 검사에서 로그인 준비의 정상 GC가 이미 소비한 transient source를 정리했다.
  GC를 먼저 완료한 뒤 기준을 잡고 durable binding/operation/audit의 정확한 rollback 검사는 유지했다.
- self deadline fixture는 기존 session/slot composite FK를 무시한 expires_at 수정으로2개 실패했다.
  기존 FK와 runtime을 그대로 두고 실제 idle 만료의 유효한 created_at/last_activity fixture로 바꿔2개 통과했다.
- 추가 deadline 첫 실행8개는 기존 statement_timeout 2000ms보다 긴 단일 pg_sleep(2.1) 때문에503이었다.
  기존 W0 검사처럼 pg_sleep(1.1) 두 번으로 실제 경과 시간을 만들었으며 DB timeout/runtime은 바꾸지 않았다.
- 로그인 업무 COMMIT ACK 유실은 응답 미전달 시 자신의 새 session ID를 별도 transaction으로 철회하도록
  보완했다. 실제 commit 후 OperationalError 주입을 검사한다. 발급 ACK 유실의 영속 source 보존도 검사한다.
- 동시 동일 operation의 binding hint는 installation 잠금 이후 조회하도록 고쳤다. 실제 서로 다른 관리자
  연결에서 동일 payload201/200, 다른 payload201/409와 비밀 없는 replay를 검사한다.
- C3 credential 선취는 원래 기존 `lock_credentials` 다음 새 Trainer source 순서였다. 해당 결함 지적은
  철회되었으며 불필요하게 다른 순서로 바꾸지 않았다.

## 보존과 다음 단계

`scope-check.json`은 구현 시작 raw SHA 기준 허용 범위 밖 변경이 없음을 확인한다.
기존 보호 테스트의 head 상수 변경은 각각1/1/3개이고 기존 assertion/downgrade 대상을 보존했다.
`developer-result.json`, `source-frozen.json`에서 최종 소스/보호 파일 SHA, HEAD/index, 각 실행의 정리
receipt를 확인한다. 실패 실행을 포함한 자동 fixture는 최소 결과를 남기고 자신이 만든 자원을 정리한다.
공유 Compose 서비스/volume은 임의 제거하지 않는다. QA 보고는 설계자 검토가 끝날 때까지 보존한다.

다음은 별도 승인된 독립 실행 담당자의 동결 소스 검증, 전체 PG/native, 설계자 최종 검토다.
기존 계정 역할 추가/겸임(I2), Trainer 상태·Home 변경 명령, 분실 암호 복구, PT/정산,
운영 배포·실물 인증기·전체 브라우저/보존 인수는 이 결과의 범위가 아니다.
