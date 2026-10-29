# WORKFORCE-002 Trainer 업무 상태 인수 결과

2026-10-30 **로컬 설계자 인수 PASS — 명시적 분할 검증**.
기준 parent `d55db2ef1e60d9ad8efa92b656545b348d8ab61a`, branch `codex/workforce-trainer-state`.
[제한 계약](workforce-002-trainer-state-design.md)과 [최소 판정·개별 결과](workforce-002-trainer-state-review.json)를 따른다.
Product/OPEN/ADR·전역 모듈 상태는 변경하지 않았다. 커밋·push는 별도의 전담 검토 단계다.

## 동작과 원자성

Master는 자기 Organization, Branch Admin은 처리 시점 실제 Trainer Home에서 업무 상태를 변경한다.
기존 Home가 비활성이어도 새 배정이 아니므로 허용한다. 계정 미발급/PENDING/ACTIVE/DISABLED/회수 grant와
업무 상태를 분리하며 account/grant/role epoch/security/account version, Home·보상·기존 업무 사실을 바꾸지 않는다.

실제 off 전이에만 독립 관리자 역할 없는 대상의 기존 AuthSession을 철회한다. 겸임 관리자와 본인 관리 로그인은
유지하며 on으로 복귀해도 철회 세션·차단 계정·회수 역할을 복구하지 않는다. I1의 원래 유효 source와 만료는 유지한다.
상태·operation·transition·typed audit·세션 변경은 같은 UoW다. 기존 정렬 잠금과 fresh actor snapshot을 사용하고,
모든 현재 사실·감사 이후 원래 idle/absolute 기한을 검사한다. 실패는 전체 rollback이다.

원래 커밋 결과와 현재 사실을 분리하며 replay/noop은 세션 철회나 version 증가를 반복하지 않는다.
현재 Home Scope를 status/direct ID에도 적용한다. `0013_workforce_trainer_state`는 기존 Web 현재 관찰과
실제 신규 등록·전이 사실을 구분하고 손실 downgrade를 거절한다. C# 이관·과거 시점 추정은 없다.

## 실제 독립 검증

| 구분 | 실제 판정 | 범위 |
|---|---|---|
| R2 fresh fast | 131 passed, 실제 exit0 | Ruff·format125·mypy108·Import Linter8 포함 |
| R1 첫 scoped PG315 | 209 passed / 1 failed / 105 미실행, exit1 | 실패로 보존, 신규 W1 35개도 당시 미실행 |
| R2 fresh scoped PG109 | 109 passed, exit0 | 이전 미실행105+실패 native1+앞선 native3 재검증 |
| 현재 PG 인수 근거 | 206 보존+109 fresh=315 | 기존280+신규35의 분할, 최종 새 단일315/전체576 아님 |
| R2 실제 HTTPS/native | 8 manifest/225항목 모두 literal true | 같은 R2 PG 실행의 browser pytest5개 안의 조건 |
| native 역할·상태 | 기존49조건 그대로+새 인과5=54 | 실제 지연 GET 전달·링크/상태 역행 방지 포함 |
| 전체 목록 | pytest707=비DB131+PG576; native265 | 전체 실행을 뜻하지 않음, 미선정 PG261은 미실행 |

PG109의 실제 노드는 승인 목록과 정확히 같고 누락·중복·failure/error/skip/xfail/xpass/incomplete는0이다.
원래206개는 실제 R1 passed이며 browser를 제외한다. 해당15개 테스트 파일과 서버 업무 Python/SQL·설정·의존성·
기존 guard는 그대로이고, HTTP는 WORKFORCE_SCRIPT 리터럴만 바뀌었다. Root가 AST/바이트·원래49개 native
assignment를 직접 대조했다. 앞선 native3개와 fast131은 R2 새 실행으로 대체해 중복 합산하지 않는다.

실제 scope·원래 source 만료·old cookie 미복구·관리자 겸임·no-op/replay·ACK 유실·감사와 마지막 clock rollback,
I1 prepared proof·I2 binding hint·C3/principal 양방향·migration writer 경합·신규 등록 origin 실패를 포함한다.
관찰한 최초 대기는 installation이며 Trainer/credential 행 대기로 과장하지 않는다. 원래 httpx/AnyIO 경고는 유지한다.

## 최초 실패와 UI 보완

최초 독립 실패는 `test_trainer_roles_native`의 w1-pending 단계였다. 실제 false는 w1_link_paused 하나이고
이후16조건은 미도달이다. 진단 parser가 숫자를 잘라 단계가 w로 기록되던 문제도 수정했다.
Root는 진행 중 last_case를 통과로 오독한 코멘트를 실제 XML/exit1 확인 직후 사용자에게 정정했다.

기존 앱에서 실제 계정 발급 전 GET 응답을 보류한 뒤 새 링크가 표시된 후 전달하면 링크가 사라지고
같은 w1_link_paused=false가 재현됐다. 패널별 최신 조회·쓰기 무효화와 Trainer 버전 역행 방지로 보완했다.
같은 실제 응답 순서와 비활성화 전 응답의 늦은 도착을 R2에서 확인했으며 기존49조건은 바꾸지 않았다.
단독 무계측 재시도 통과는 원인 규명이 아니다. 최초 독립 실행의 정확한 통신 순서는 여전히 미확정이며,
재현한 결함 클래스의 수정·새 인과 조건 통과를 최초 실패의 소급 PASS로 표현하지 않는다.

개발 당시 잘못된 파일 경로(exit4/미실행), PENDING→DISABLED seed 제약, 철회 cookie, parent archive cwd,
비노출 CLI 오류 문자열, GC 뒤 source 잔존 기대 및 중첩 lifespan 준비 오류도 최소 원인·개수로 보존했다.
실제 parent HTTP를 순차 기동하고 정확한 하위 DB guard를 rollback 가능한 실제 revision 순서로 확인했다.
ProcessGuard·timeout·기존 단언·보안·require-postgres를 완화하지 않았다. 개발자44개+전담 causal8개=52개의 개발 단계 근거를 독립 결과로 전용하지 않는다.

## 정리와 제한

Root가 이번 작업의 자동 실행21개 엄격 정리 영수증과 실제 경로 부재를 확인했다. 독립 관찰 subset은 R1 schema210/
process217/owner2, R2 schema106/process114/owner2이며 전체 등록 수라고 합산하지 않는다. 원본·공유 DB·미디어·
설정·인증정보·현행 QA 도구는 보존한다. 완료 실행 원본 자료는 최소 인수 근거·커밋 검증 후 정책에 따라 정리한다.

최종 동결248개/Backend162개·HEAD/index/trust가 실행 전후 같았다. Root 후속은 Architecture 문서와 최소 proof뿐이며
테스트한 Backend162개를 유지한다. Root는 runtime을 추가 실행하지 않았다. 운영·실물 기기·전체 브라우저·전체 모바일,
전역 PROPOSED·다른 Product OPEN과 PT/Pass/지급/정산 동시성은 이 인수 범위가 아니다.
