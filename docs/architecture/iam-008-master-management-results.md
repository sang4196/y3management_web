# IAM-008 — 다른 Master 관리 개발 결과

상태: **제한된 로컬 개발 인수 PASS**. 기준 커밋은
`a78e2ac3dd7534816d036f3f80cc7069db07f445`, 작업 브랜치는
`codex/iam-master-management`다. [계약](iam-008-master-management-design.md)의
다른 정상 MFA Master 차단·복구·ACTIVE Login ID 변경만 구현한다.

## 최종 독립 검사와 설계자 판정

2026-10-18 동결 revision3의155개 파일을 기준으로 독립 담당자가 다음 검사를 새로 실행했다.
[설계자 판정](iam-008-master-management-review.json)에 최소 근거와 범위를 남긴다.

| 검사 | 실제 최종 결과 |
| --- | --- |
| `bash check.sh fast` | 96 passed, exit0; Ruff/format/mypy 및 Import Linter7 계약 통과 |
| `bash check.sh db` | 전체327 passed, exit0; 신규81 + 기존246, 단일 실행 |
| 실제 수집 | 423 = fast96 + PG327; 실패/skip/xfail/xpass/error/incomplete0 |
| 같은 전체 실행의 native | Chromium151.0.7922.34, HTTPS58/MFA20/관리15/reset11/새 Master12 모두 정확한 집합·true |
| 불변성·정리 | 실행 전후 소스155/보호62·HEAD/index 일치, 자동 실행4개 정리, 공유 DB/volume/corpus·시스템 신뢰 보존 |

fast pytest run은 `auto-33c5104708ce43dfa2107ba035b1024a`, 전체 PG/native run은
`auto-38e823985f1a4a90b2200cdde732e5f3`다. PG 명령은1796.618초에 종료했다.
기존 의존성 경고2개를 숨기지 않았다. 개발 중79건/정정2건 등의 부분 결과나 이전 증분의
분할246 근거를 이번 전체327 결과로 재사용하지 않았다. 아래 검토 보완3건도 최종 동결 소스에서 확인했다.
설계자는 결과·소스/해시·manifest·정리를 검토했고 별도 runtime 검사를 수행한 것으로 보고하지 않는다.

새 migration/의존성 및 Product/ADR 변경은 없다. AB5 결정·구현, 자기 관리/승격강등/복합 역할,
실물/모바일/전체 지원 브라우저와 운영 인수는 남아 있다. 계정 전달/본인 확인·기록 정책 또는 production을
검증한 것으로 확대하지 않는다. 다음 개발 실행 자료는 현행 QA 절차를 사용한다.

## 변경과 보존 경계

새 purpose helper와 세 API를 통해 같은 조직의 다른 Master만 관리한다. 기존 BA 전용
`scoped_account`와 onboarding 조회 동작을 변경하지 않았다. Installation/Account/Session
잠금 후 current actor·CSRF·대상·version을 검증하고 실제 변경에 epoch 증가, 대상 세션과
setup/login/add/reset/recovery 증명 폐기, 기존 typed audit를 한 UoW로 반영한다.
최종 actor 재인증으로 현재 사용 가능한 다른 Master를 확인한다.

원래 암호·Passkey 전체 행/keyset·grant·pending/generation은 보존한다. 복구는 옛 세션이나
source를 되살리지 않으며 pending 요인은 명시 재발급이 필요하다. ID 정규화 no-op은
stale 검증 이후 효과 없이 반환한다. 과거 ID 예약과 C2 안정 키/쿨다운을 재사용한다.
새 migration/의존성·운영 승인·Product 결정은 없다. self/승격강등/복합 역할/AB5는 범위 밖이다.

## 개발 표적 검사 이력

2026-10-18 WSL 전용 Compose 시험 DB에서 기존 pytest fixture를 사용했다.

| 검사 | 결과 | 범위 |
| --- | --- | --- |
| 최종 `bash check.sh fast` | PASS: 96 pytest, Ruff/format/mypy, Import Linter 7 계약 | DB 없는 검사, PG 327 deselected |
| 새 PostgreSQL 표적 검사 | PASS: 기존 유효77 + recovery2 + 정정 login2 = 81 고유 node | 수정 전79건 이력 보존, 정정된2건으로 대체; 전체 PG 회귀와 구분 |
| 실제 trusted HTTPS MFA browser | PASS: pytest 1 | MFA20 + 관리15 + reset11 + 새 Master12 |
| 실제 수집 | 전체423 / fast96 / PG327 / 신규PG81 | 고유 node 수 일치, collect-only exit1은 실행 성공이 아닌 metadata |
| 보호 파일 | 62개 HEAD와 동일 | Product/ADR/기존 Architecture·인수/migration/의존성/AGENTS |

최종 fast 실행은 `auto-5bc67e1778774ef496a0c96bc6b11d2c`, 신규 PG 주 실행은
`auto-c6e7f5b6ece548d6b59ba1cc547fe173`(79 PASS), 추가 recovery proof 실행은
`auto-4af38cba77cc49279146993ca79426b6`(2 PASS), native 실행은
`auto-0389d271b216401fb8d30b6c1979c810`(native1 + 정정 경합2 PASS)다. 주 실행 착수 뒤 추가한 recovery
검사 2건만 별도로 실행했으며, 기존 79건의 검증 의미와 제품 코드는 변경하지 않았다.
최종 fast/수집은 추가된 검사를 포함한다. 각 실행은 skip/xfail 없이 종료했고 fixture가
소유한 schema·process·실행 폴더를 정리했다. 공유 인계 JSON은 root 검토를 위해 유지한다.

브라우저는 기존 도구와 Chromium 151.0.7922.34를 사용하며 TLS/UV/counter 검증을 완화하지 않았다.
기존58/20/15/11 manifest가 byte 단위로 동일하다. 개발에서 기존 S1 58개 native 항목을
이번에 별도로 재실행한 것은 아니며, 독립 전체 PG 단계에서 함께 검증한다. 새 manifest의
boolean 수는 pytest node 수에 더하지 않는다.

MM-BROWSER-RELOGIN-001 보완으로 native driver의 수동 cookie 삭제를 제거했다.
복구 후와 ID 변경 후 실제 `/login` 폼에서 철회 AUTH cookie가 CSRF 요청에 계속 전송되고,
CSRF fallback → 비밀번호 → UV 성공 후 값이 다른 새 AUTH cookie와 정상 `/auth/me`로
복귀하는 것을 확인했다. 복사한 옛 cookie의 명시 재사용401 검사는 유지한다. TestClient
공통 login helper의 빈 cookie jar 전제 때문에 사용하는 테스트 준비와 실제 브라우저의
재로그인 동작을 구분한다. 앱·인가·verifier·CSRF·PG 테스트 코드는 변경하지 않았다.
이 native 보완만 재실행했고 기존 PG81 증거는 유지했다. 최종 fast96도 다시 통과했다.

MM-TEST-LATELOGIN-001 보완으로 두 login 경합의 대기 지점을 실제
`verify_authentication_response` 성공 직후로 이동했다. verifier 성공 Event를 확인한 뒤
관리 command의 commit을 기다리고 release하며, 최종 lock=True context에서401과
pending/target 세션 거부·actor 생존을 확인한다. 수정 전79건의 두 login 결과는 서명 검증
전 대기의 이력이며, 최종 증거는 `auto-e761c99f1dd341378abbe5074a53ef54`의 정정2건이다.
나머지77건·recovery2건과 합친 고유 신규PG 범위는81건이다. 제품 verifier는 변경하지 않았다.

공통 native login helper의 password_stage_no_auth는 단계 전후 AUTH 값이 동일함
(없으면 둘 다 없음)과 `/auth/me`401을 누적 AND로 검사한다. 옛 철회 cookie 존재와
새 업무 인증 발급을 구분하며, password 단계에서 새/바뀐 AUTH가 발급되면 실패한다.
유효한 기존 로그인에 대한 logout_required는 유지한다. 검사 보완 중 발생한 mypy의
재수출 import 오류는 기존 테스트처럼 WebAuthn의 직접 import로 수정하고 최종 fast와
정정2건을 다시 실행했다.

## 표적 검증 내용

- 실제 CLI 최초 Master/API 추가 Master, 복수 로그인과 대기 login/add proof 철회,
  복구 후 원래 암호·동일 key 로그인, ID 예약/현재 ID·정규화 no-op/stale 우선/C2 쿨다운.
- 자기/없는/다른 조직/BA 대상과 BA actor·weak/revoked/idle/키 철회/role 회수 거부,
  기존 BA API의 Master 거부, DTO·최소 응답, 모든 세 명령의 최종 idle/absolute 만료 rollback.
- reset/recovery pending 보존과 옛 source·proof 거부, 명시 재발급·실제 완료,
  pending 중 ID no-op의 source 불변.
- 독립 연결의 상호 차단/ID 변경과 같은 대상 경쟁, C3/add/login/reset/M2/M7의 최종
  잠금 전 증명 보류 후 관리 선행, 요인 명령 선행 뒤 stale/current version 처리,
  실제 actor 권한 상실 뒤 예전 인증 거부.
- 세 명령 각각 필수 감사/DB 실패 rollback과 실제 COMMIT 뒤 ACK 유실의 영속 효과 확인.
  테스트 snapshot/factors는 SQL 내부 비교 digest만 반환하며 실제 helper 오류 경로에
  환경변수의 비결합 canary와 `--showlocals`를 적용해 원문 비노출을 확인했다.

초기 개발 실패는 테스트 컬럼명, 철회 cookie가 남은 재로그인 준비, assurance의 설정명과
저장값 구분, 경합 hook의 사전 상태조회/최종 명령 구분 문제였다. 실행 실패를 성공으로
합산하지 않는다. 비밀을 포함할 수 있는 raw DB row/traceback은 결과 문서에 복사하지 않는다.

## 개발 인계 당시 상태

최종 manifest, 수집 node와 실행별 상태는 ignored 공유 QA 폴더의
`developer-result.json`, `source-frozen.json`, `collection.json`으로 인계한다.
개발 인계 당시에는 전체327 PostgreSQL의 새 실행, 기존 S1 native58을 포함한 전체 browser 인수와
설계자 검토가 후속 단계였다. 해당 검사·검토는 위 최종 독립 결과로 대체하며 전담 커밋·푸시 절차를 따른다.
기존 검증 결과를 새 app 변경의 전체 검증으로 재사용하지 않았다.
