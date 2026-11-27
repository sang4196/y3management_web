# MEMBERSHIP-001 로컬 인수 결과 — 회원 기본관리

Status: **IMPLEMENTED / VERIFIED / ACCEPTED — LOCAL LIMITED MEMBERSHIP-001** (2026-11-27).
Parent `62857f75cca460d28465dc7fb8db61060dcfc80f`, branch `codex/membership-basics`.
[MEM-1/2](../product/product-decisions.md#review-20261127-membership-basics)와 [한정 계약](membership-001-basic-management-design.md)의 구현이다.
설계자가 동결350의 독립 검증과 최종 변경 검토를 확인해 이 한정 기능을 로컬 인수했다. [최소 검토 근거](membership-001-basic-management-review.json)에 확정 SHA·실제 node·native raw/manifest hash를 보존한다.

## 구현과 경계

Membership의 최소 편집대상 목록/상세/등록·이름/국내 휴대전화 수정과 기존 BR-OPS-022의 관리자 전용 상태 명령을 추가했다.
Master Organization·현재 Home의 BA/Operator Scope를 독립적으로 판단하고 실제 일치 역할로 감사한다.
전화는 중복을 허용하며 동일 국내번호 입력 표현만 canonical화한다. 별도 Member UUID와 현재 상태/Home을 보존하고 자동 병합하지 않는다.
타 지점 발급용 검색/Trainer 담당 조회·Home 이동/Pass/PT/지급·정산·MemberLogin·내보내기는 구현하지 않았다.

불변 버전·명령 전체/원 Actor operation·typed Audit와 마지막 현재 권한/원래 기한 검증은 상위 UoW에서 함께 완료/rollback한다.
상태 명령 receipt는 현재 관리자 권한으로만 대사한다. old committed와 fresh current를 분리하고 stale no-op도409로 거부한다.
실제 변경만 version/Audit/활동 시각을 갱신한다. no-op/replay/조회는 touch하지 않는다.
UI는 현재 계정/Org/독립 Scope·Operator version과 세션별 CSRF 문맥을 메모리에서 비교하고 변경 시 옛 개인정보·초안/선택 게시·전송을 차단한다.
ACK 불명은 원 UUID/본문을 유지하며404→동일 명령 재시도→명확409 거부→fresh detail 이후 새CAS를 사용한다.

새0023만 작성했다. 원래0001–0022/ADR/lock·공통 QA/역사/helper를 보존하고 실제23 inverse adapter를 새 테스트에 추가했다.
기존 guard caller는 이 adapter에 연결하고 정확 현재head 기대·/me Operator version의 두 exact-role 기대를 보완했다.
Catalog preflight는 원래 scene의 실제 Session/Branch 표본을 유지하고 rollback-only Connection에서 실제22를 준비한다.
원래 guard의 실제 target 준비 뒤 관측을 유지한다. 신규 table/receipt가 비어 있을 때만 lossless22 inverse를 허용한다.
Import Linter는 기존9 계약을 유지하고 Membership 경계를10번째로 추가했다. 의존성/도구/타 업무 모듈을 추가하지 않았다.

## 독립 검증·설계자 인수

| 검사 | 실제 결과 |
| --- | --- |
| 새 `bash check.sh fast` |258 PASS·exit0, Ruff/format/mypy·Import Linter10 kept. 관찰기 교정 뒤 반복하지 않고 동일 동결본 성적을 보존 |
| 독립 PG 최초 실행 |92 선정 중29 실행:28 PASS·관찰기 metadata 실패1,63 미실행 |
| ignored observer 교정 후 잔여 실행 |64 수집/실행/성공·exit0,533.29초. 이전 보존28과 겹치지 않으며 합집합은 원래92와 정확히 일치 |
| native5 |같은 retry run의 Membership12/경합9/Scope9/Catalog22/Workforce54 조건 모두 raw exact keyset·literal true·safe/manifest 일치 |
| 최종 선정의 실패/skip/xfail·누락 |없음. 최초 metadata 실패는 이력으로 유지하며 단일92 성공이라고 주장하지 않음 |
| 실제 collection·미선정 |1133=비PG258+PG875. PG783은 미선정/미실행 |

최초 관찰기는 종료된 bwrap의 가상 mount 경로를 hash하려다 실패했다. ignored observer만 현재 raw를 먼저 보존하고 동결된 실제 host ro-bind 원본을 hash하도록 교정했다.
제품/소스/테스트는 바꾸지 않았다. 최초 leg의 raw native는 확보되지 않았으며 이전11키 latest 자료는 성적에서 제외하고 검토 중 보존했다. 최소 SHA/실패 이력은 committed review JSON에 남기며 완료 원본은 정리할 수 있다.
해당 node와 미실행63을 합친64를 새 실행했다. 개발자 점수를 독립 성적으로 차용하거나 실패 실행을 성공으로 바꾸지 않았다.

다섯 native는 `auto-41ebbed096694076a536a49d03aaba12`, 실제 Chromium151.0.7922.34다.
raw/safe/manifest SHA·실제 원본 binary SHA와 현재 run 출처를 [최소 근거](membership-001-basic-management-review.json)에서 대조할 수 있다.
동결 source350/Backend228/보호42·HEAD/branch/기준 index·refs·trust/hosts/DNS/NSS·browser/Node bytes는 독립 실행 전후 동일하다.
검토 중 최초22개 근거의 SHA 동일성과 실제 parent22 원본행 보존/역변환 검증을 확인했다. 최소 SHA는 committed JSON에 남긴다. 자기 schema/process/port/auto 잔존은0이다.
보존된 raw/JUnit/native JSON 폴더는 검토 근거이며 실행 환경이 아니다. Root가 commit/push 후 정리를 결정한다.

검증은 현재 WSL 신뢰 Chromium 조합의 로컬 범위다. 다른 플랫폼/브라우저·원본 업무 DB 적용/운영 배포·범위 밖 Pass/PT/지급·정산은 검증하지 않았다.
다른 Product OPEN/전역 모듈·UoW PROPOSED/ADR 상태는 바꾸지 않는다.

## 개발 검증과 초기 실패

개발자 smoke이며 독립 인수 성적이 아니다. 실행을 합산한 단일 성적/전체PG 통과로 보고하지 않는다.

| 실행 | 실제 결과와 한계 |
| --- | --- |
| 최종 `bash check.sh fast` |258 PASS, Ruff/format/mypy152 PASS, Import Linter10 kept. 기존 경고2개 유지 |
| 새 Membership PG/storage 2차 |39 PASS 뒤 basic native1 FAIL. 나머지 native2 미실행. 실제22 olddata/양runtime/empty inverse/typed guard 포함 |
| 한정 교정4차 |core5+native2=7 PASS/basic1 FAIL. BA/Operator 비활성 Home 편집·typed identity를 보강했고 races9/Scope9 조건은 모두 literal true |
| 원래 scene 보존 PT guard 교정 |head/policy2 PASS. 실제 Session/Branch 행을 유지한 actual22 준비 뒤 targetDDL0·target 전체행/rollback23 전체행·shape 보존 확인 |
| CSS 교정 후 basic 새 실행 |1 PASS, 별도 manifest12 조건 모두 literal true. 실제390px 상세/목록·CSP self stylesheet·후보101+·BA 상태버튼 포함 |
| 실제 collection |1133=비PG258+PG875. collection-only exit1은 required-PG hook의 미실행 메타데이터이며 runtime 실패/통과와 구분 |

races/Scope의 두 native는 `auto-6625ee4f252d4b27bd9db759c0819509`, CSS 교정 후 basic은
`auto-1354ce46f66740e4a6a90d4ca191dc2e`이며 실제 Chromium151.0.7922.34다. 서로 다른 실행을 같은 run으로 부르지 않는다.
각 profile의 raw exact keyset/literal true를 기존 validator로 확인한 뒤 동일 실행의 safe boolean 근거를 보존했다.
기존 TLS/NSS/bubblewrap/90초 cap·소유권/프로세스/schema 정리 body는 변경하지 않았다.

첫 새 PG 실행은24 PASS 뒤 historical archive의 child PATH에서 uv를 찾지 못해1 FAIL로 중단됐다.
기존 helper를 고치지 않고 검사 실행 PATH를 보완했다. 첫 실행의 나머지 node는 미실행이며 자기 schema/auto 정리는 완료됐다.
이어39 새 PG/storage는 통과했고 첫 basic의 후보/모바일 false와 BA 준비 실패를 교정했다.
준비 대기는 fieldset의 상속 disabled를 확인하도록 고쳤고 BA /activate selector는 기존 화면의 #password를 사용한다.
390px의 실제 원인은 공통 CSP가 새 inline style을 차단한 것이었다. 초기 margin 가설과 구분한다.
공통 CSP는 유지하고 `/members.css`의 같은 origin 외부 stylesheet로 옮긴 뒤 적용/실제390px/긴값을 새 실행으로 확인했다.

WIP 검토에서 후보100개 이후 접근·새 선택의 BA 상태 버튼·HTTP DTO repr·Operator 메뉴 진입도 교정했다.
검증에는 parent22 실제 Trainer 상태 이력, full constraint/index/column shape, 늦은 목록/상세 응답과 원UUID/새CAS의 인과 단언을 보완했다.
Operator native는 실제 업무 Branch 이동/동일 계정 재로그인을 사용하고 옛 nonce를 고정해 Scope fingerprint 자체의 이전POST0을 확인한다.
이는 실제 OS 시계를 바꾸거나 다른 플랫폼을 인수했다는 뜻이 아니다.

정확 선정은 QA `developer-selected-impact.json`이다. 새42 PG와 실제 바뀐 옛 guard/head·/me 기대 및 한정 공유 경계 회귀를 합쳐
94 node를 독립 tester에 추천했다. 독립 tester는 byte가 동일한 Base native2만 제외하고 새42+기존변경38+공통12의 정확92로 확정했다. PG783은 독립 미선정이며 이 개발자가92/94 또는 기존 영향전체를 실행한 성적은 없다.
실행별 JUnit/초기실패·미실행과 최종 source/backend/보호SHA·환경정리는 QA 개발자 최종 보고를 따른다.

## 인계

동결 source와 개발자·독립 tester·Git 검토 근거를 검토에서 확인했다. [최소 committed review JSON](membership-001-basic-management-review.json)을 최종 재검토 근거로 남긴다.
완료 QA의 중간 freeze/report·raw/JUnit/native JSON은 Root가 commit/push 성공 뒤 정리할 수 있다. 해당 원본의 영구 보존이나 이후 존재를 약속하지 않는다.
최초 metadata 실패·제외한11키 자료와 최초22개 근거는 검토 중 보존했고 최소 SHA/실패 이력은 committed JSON에 남긴다.
개발자는 별도 전면검사·코드 수정·stage/commit/push/원본DB 적용/deploy를 수행하지 않았다. 다른 Product OPEN/전역 PROPOSED는 유지한다.
