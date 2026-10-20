# IAM-010 정상 Master 비상 복구 인계 — 구현·독립 검증·설계자 인수

2026-10-21. 기준 commit `fdab9b6971a1d8ba1dbc4e1855c9073fa5797239`,
branch `codex/iam-emergency-handoff`. [R4 계약](iam-010-emergency-handoff-design.md)에 따른
**제한된 로컬 개발 인수 PASS. 독립 전체 회귀와 설계자 검토 완료**이며 운영 승인과 구분한다.

## 구현한 동작

같은 조직의 다른 현재 정상 MFA Master가 만료된 최신 미완료 운영 사건을 인계하고,
동일 원본/요인 안에서 유실된 링크를 명시 재발급한다. 실제 운영 승인 원본과 새 정상
관리자 권한을 구분하며, 운영 CLI 조건과 일반 opposite-pending 차단은 유지했다.
새 발급은 불변 parent/origin을 참조한다. 상태 조회는 token 없이 no-touch/no-GC이고,
commit 응답 유실은 operation 상태 조회 및 별도 명시 재발급으로 처리한다.

최종 current actor·CSRF·DB 시각/idle·source lease·전체 target epoch/pending/readiness를
잠금 안에서 검증한다. 감사/DB 지연 뒤 검증까지 활동 시각을 먼저 갱신하지 않는다.
대상 로그인/대기 권한만 철회하고 C2·타 계정·선택 밖 요인은 보존한다. 성공한 실제
발급자 세션의 활동 시각만 정상 관리 활동으로 갱신하는 예외를 검사에 명시했다.
수신자는 기존 emergency UI에서 직접 요인을 준비하며 both는 실제 UV 뒤 원자적으로 완료한다.

forward0009는 operating/master_handoff variant의 필수/금지 NULL과 정상 인계 전용
동일 조직/대상/요인 parent/origin FK를 추가한다. 기존 operating 재발급은 새 적법한
수동 승인에 따른 기존 계약을 유지하며 요인 범위 변경을 전역 FK로 차단하지 않는다.
인계 감사는 실제 Master, 완료 감사는 실제 수신자다. handoff 이력의 downgrade는 거부한다.

## 독립 전체 검증과 설계자 판정

개발자가 멈춘 최종194개/Backend120개 소스에서 별도 담당자가 `bash check.sh fast`와 `bash check.sh db`를 새로 실행했다.
fast105개와 필수 PostgreSQL **전체391개(신규27+기존364)**가 모두 통과했다. 실패·오류·skip·xfail·xpass·미완료는0이다.
개발 표적 묶음이나 이전 인수를 합친 결과가 아니며 각 명령은 한 번 실행했다. 같은 PG run
`auto-d29dbe21b2b14296a18b92656de30176`의 실제 Chromium `151.0.7922.34`에서 기존139개와 새17개 확인이 모두 true였다.
156항목은 exact manifest이며391개 안의 브라우저 pytest4건에 포함된다. 새17개 native는 정상 Master 인계·live 자식 재발급과
both 수신자 실제 UV/재로그인 흐름이다. 세 종류의 신규 native UI 실행으로 확대하지 않으며, 세 요인은 실제 DB/서버 crypto로 검증했다.

설계자는 현재 계약·소스·정적 변경 검토와 독립 결과를 대조했다. HO-DB-TIME-001의 늦은 DB lease와 유효 actor를 분리한
rollback, HO-RACE-ACTORS-001의 실제 별도 B/C Master 경합, 늦은 actor idle, 실제 UV 뒤 재발급과 실제 COMMIT 뒤 ACK 유실이
이번 전체 실행에 포함된다. 같은 동결 소스의 수집/전체 성공과 테스트 정의의 실제 장벽·저장 결과를 연결하며 verbose 개별 실행
trace를 별도로 수집했다고 주장하지 않는다. [최소 설계자 근거](iam-010-emergency-handoff-review.json)를 보존한다.

보호172개 revision3와 소스·HEAD/index는 실행 전후 일치했다. HEAD와의 승인된 내용 차이는 정책7개와 기대 상수1개다.
별도의 과거 AS-IS13개는 원래 checkout CRLF/Git LF 차이이며 이전 IAM-009 raw SHA·정규화 byte·빈 Git diff로 확인했다.
이 파일들은 새 변경이 아니고 줄바꿈을 변환하지 않았다. 실제 테스트·출력 수집 환경4개의 프로세스/schema/profile/TLS/폴더 정리를
확인했고 미정리/새 finding은 없다. 추가 관찰한 소유 schema386개·프로세스75개도 잔류가 없으며 전체 정리 보장은 기존 fixture guard/receipt를 따른다.
기존 경고2개는 유지한다. root는 자료와 소스를 검토했으며 별도로 runtime을 실행하지 않았다.

## 개발자 표적 검증과 초기 실패 이력

아래는 독립 진입 전 개발 시점의 결과이며 최종 전체 인수는 위의 새 독립 실행을 따른다.

| 검사 | 결과 | 범위 |
| --- | --- | --- |
| 최종 fast | 105 passed | Ruff·format·mypy, DB 없는 pytest, Import Linter 7 kept |
| 신규 PG/native | 27 passed | 실제 세 요인·epoch/인가·GC·원자성·migration·응답 유실·HTTPS |
| 강화된 서로 다른 Master 경합 | 1 passed | 기존 같은 사례를 B/C 실제 MFA account/session으로 보완, 중복 새 테스트 아님 |
| 기존 PG 회귀 | 53 passed | 운영 복구/CLI·migration·reset 저장·GC, 53개 선택 |
| 기존 native 회귀 | 3 passed | 기존 공통 브라우저 helper의 정상·MFA·운영 복구 |
| 실제 수집 | 496 collected | 비DB105, DB391(전체−fast); 수집 전용 exit1은 mandatory PG no-pass gate이며 실행 성공 아님 |

신규 Chromium 151.0.7922.34의 실제 신뢰 HTTPS에서 17개 확인이 모두 true였다.
실제 정상 Master 발급→live 자식 명시 재발급→이전 사건 superseded→기존 recipient form의
실제 UV both 완료→자동 로그인 없음→정상 password+UV 재로그인을 확인했다.
기존 native의 58/20/15/11/12/23개 확인도 모두 true였다.
운영 원본은 기존 실제 CLI로 발급하고 fixture 시각 이동으로 만료시켰다. 실제 운영 담당자
신원/접근 불가·실물 인증기 검수를 의미하지 않는다.

신규27 검사 시점과 최종 동결 사이 제품 runtime source 변경은 없다. 설계자 요청으로
기존 새 경합 테스트 하나를 실제 distinct Master로 강화해 별도로 재실행했다. 기존 보호
회귀의 고정 head 기대 한 상수는 아래 승인 후 수정·재검증했다. 검증 당시 소스 manifest와
이 두 테스트 후속 근거를 QA에 함께 남긴다. 개발자가 전체 DB391을 실행한 것은 아니다.

## 발견과 보완

- HO-DB-TIME-001: Service의 application clock 비교를 제거하고 감사 후 IAM 공개 port에서
  DB clock/source/lease를 확인한다. 유효 actor·실제 짧은 DB lease·감사 지연·뒤처진 app clock
  조건에서 사건/source/대상/감사/활동 rollback 및 미전달을 검사했다.
- HO-RACE-ACTORS-001: 같은 actor 두 스레드였던 사례를 별도의 정상 Master B/C로 강화했다.
  공통 parent에서 한 child/source/audit만 확정되고 패자의 활동 시각은 유지됨을 확인했다.
- 기존 migration 회귀는 실패한 전체 downgrade 뒤 head를0008로 고정해 기대했다.
  실제 단일 transaction rollback은 새 head0009를 유지한다. 설계자가 승인한 마지막 기대
  상수 한 줄만0009로 수정했고 승인 후 SHA와 일치한다. old0001–8/env.py와 downgrade 거절,
  사건1건 보존 검사는 유지했다. 최초 회귀는52 passed/1 failed로 보존한다.
- 새 테스트의 stale cookie helper 전제·GC 호출명·fixture session 시간 CHECK 및
  statement timeout·migration 진단 비노출 기대 오류를 보완했다. 제품 제한을 풀어
  테스트를 통과시키지 않았다. 새 native driver는 기존 CSRF header/enrollment 경로를 따른다.

## 인계와 한계

최종 기존 PG 회귀53개는 exit0이며 해당 실행 폴더 제거를 확인했다. 초기 실패 실행과
최종 검사들의 자기 실행 폴더도 정리 결과 및 실제 부재를 확인했다. 보호 entry revision3의
172개 해시와 사용자/설계자 정책 문서7개 해시가 일치한다. HEAD는 위 기준 commit이며
index는 비어 있다. 전체 Git 관리 대상 및 비ignored 신규 파일과 backend 부분집합의 실제
SHA-256을 source-frozen.json에 기록하고 source_writer_stopped=true로 동결한다.
별도 승인된 test 한 상수 외 보호파일·dependency/lock·old migration을 보존했다.
개발 담당자는 stage/commit/push를 하지 않았다. 독립 전체 검증과 설계자 인수 완료 후 전담 커밋 세션의
최종 변경 검토·한글 상세 커밋·일반 push 절차를 따른다. Workforce 선행 계약/구현은 별도 후속이다.

근거는 ignored `.local/qa/iam-emergency-handoff-94b76c330a294b83/`의 최종 로그,
최소 브라우저 보고, `developer-finding-resolution.json`, source manifest와 결과 JSON이다.
실제 운영 담당자/승인 원본 확인·보존/열람/삭제·배포·실물/전체 지원 브라우저와
Workforce/PT/정산은 이번 구현·인수 범위가 아니다. 기존 Starlette HTTPX/AnyIO
DeprecationWarning은 남아 있으며 dependency 변경으로 우회하지 않았다.
