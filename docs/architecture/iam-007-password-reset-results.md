# IAM-007 개발 결과

2026-10-18 최종 설계자 판정: **IAM-006/007 결합 증분의 제한된 로컬 인수 PASS(분할 검증)**.
[인수 요약과 소스·검증 근거](iam-007-password-reset-review.json).

후보3의 독립 `bash check.sh db`는 245개를 모두 실행해 **244 passed, 1 failed, exit1**이었다
(`auto-8b3e202dc2c64765a3857aca29edba3c`, 1868.505초). 실패는 새 테스트가 UUID 정렬 첫 항목을
특정 인증기라고 가정한 RESET-TEST-KEYSELECT-001이다. 원래 실패·종료코드를 보존했다.
앱·브라우저·의존성·migration·다른105개 파일은 그대로 두고, 해당 한 테스트에서 추가 전 원래
서버 키 UUID를 묶어 그 키만 삭제하게 고쳤다. 테스트 안에서만 추가 surrogate UUID의 두 정렬
순서를 강제하고 순서 자체를 검사한다. hash 거부의 원자성, 모든 key/tombstone fingerprint,
남은 키 로그인 및 폐기 키 재등록409 등 원래 검사는 유지했다. 나머지 모듈 AST도 동일하다.

후보4 동결106개 파일에서 독립 최종 fast는 **91 passed/PG246 deselected**였다
(`auto-93dbb6e7f40446daa602bdd10e394993`; Ruff/format72/mypy61/Import Linter7).
수정된 실제 PostgreSQL 두 정렬 경우는 **2 passed/exit0**였다
(`auto-6d5813a542f4494bb360b13c8bbabbe4`).
최종 실제 수집337=fast91+PG246과 원래 성공244+새2의 정확한 항목 집합·파일 해시·AST를
기계적으로 대조해 누락/추가/중복0을 확인했다. skip/xfail/xpass/error/미완료는 모두0이다.
**최종 소스로 PG246 전체를 단일 실행해 통과했다고 보고하지 않는다.** 이 테스트 전용 정정의
분할 검증 방침은 원래 실패 결과를 알기 전에 기록했고 전담 검토자도 조건/근거를 대조했다.
앱이나 미승인 테스트 변경이 생기면 이 재사용 근거가 무효이며 전체 검사가 다시 필요하다.

후보3의 실제 신뢰 HTTPS **58**, native MFA **20**, management **15**, reset **11** 항목은 모두
정확한 true였다. Chromium151.0.7922.34, 실제 navigator.credentials.create/get·가상 인증기와
TLS hostname/chain 검증·sandbox·전역 trust 보존을 확인했다. 앱/브라우저 소스가 같은 후보4에
근거를 연결했으며 이를 재실행 또는 실물/모바일/지원 브라우저 전체 인수로 쓰지 않는다.

독립 후보3과 후보4는 각각 자기 실행 폴더6개/process/schema/profile/TLS 자료를 정리했고
개발자의 테스트 전용 정정 실행도 정리했다. 공유 Compose DB/volume·전역 runtime·활성 corpus는
보존했다. 인계 메타자료는 전담 커밋/다음 계획 인계 후 설계자가 정리한다. 원본 로그/캡처를
영구 보존하는 대신 이 최소 결과와 실패 이력을 남긴다. 기존 의존성 경고2개는 숨기지 않았다.

본인 삭제 시 전 로그인 종료(M7), 마지막 키 보호, 추가 Master 본인 준비, 다른 정상 Master의
분실 복구와 비밀번호 재설정, 본인 관리자 reset 금지(M8)/C3 유지에 한정한 인수다.
0001–0005·Product/ADR/OPEN·dependency/lock은 보존했고 새0006/0007 외 migration은 없다.
AB5/production·운영 확인/전달/기록 보존·열람·파기·실물/전체 플랫폼·남은 대상 상태/역할 변형과
전체 IAM/v1 완료는 아니다. 전담 최종 검토·커밋·일반 push 뒤 승인된 Master 관리 후속으로 진행한다.
아래 후보3 개발 완료/독립 대기 문구와 수치는 개발 인계 당시의 이력이다.

2026-10-18 **candidate revision3 개발 완료·소스 동결**. IAM-006 관리와 결합한 후보이며
**독립 전체 PostgreSQL·HTTPS 인수와 설계자 최종 검토는 대기**다.
부모 `49eadf724185f6ece67ba1daa264823553e58ba7`, branch `codex/iam-mfa-management`.
커밋·푸시는 하지 않았다. [설계와 소비자 점검](iam-007-password-reset-design.md).

## 변경

같은 조직의 다른 정상 MFA Master가 ACTIVE 관리자 reset을 명시 시작하면 옛 verifier를
NULL로 만들고 모든 로그인·대기 권한을 철회한다. 30분 단회 source로 새 암호를 설정한 후
기존 UV Passkey로 로그인한다. 재발급·만료·세대/epoch 검사, 필수 typed 감사, COMMIT ACK
불확실성, GC를 포함한다. Passkey 전체 행/폐기 tombstone·key_set_version·Scope·C2를 유지한다.
본인 관리자 reset은 금지하고 C3는 유지한다. 동일 비밀번호 재사용 금지를 추가하지 않았다.
양쪽 요인 분실은 M2와 reset의 순차 완료로 지원하며 중간 로그인을 요구하지 않는다.

0001–0006/AGENTS/ADR/dependency/lock 및 기존 browser manifest는 변경하지 않았다.
새0007만 추가했고 같은 후보에서 개발한0006의 SHA256은
`2534c339c4be0cbcda8306ee0c719b0aa8a51cd3c88a81ff36b21cbc9b7c5f42` 그대로다.
Product·공통 Architecture·게이트는 root 소유로 수정하지 않았다. 신규 제품 질문은 0개다.

MGM-HEAD-001은 실제 시작 head를 닫힌 DBSession에서 읽어 종료 후 비교하도록 고쳤다.
기존 역사적 downgrade target/4개 guard/데이터·감사 보존은 유지했다. reset 구현 전에
실제 PostgreSQL **4 passed** (`auto-13e44b89e2404d8da3db436b9dea3880`), 새0007 적용 후에도
아래 회귀 실행에서 같은 4개가 통과했다.

## 실제 개발 검증

| 실행 | 결과와 범위 |
|---|---|
| `auto-a199e32713bf49c1a10e793ca38e6ac2` | **12 passed, 1 failed**: core reset9+audit rollback3 통과, ACK 검사의 오류 응답 필드명 오류. 아래38에서 수정된 ACK3 포함 통과 |
| `auto-5a57b26a3b124ce7adff10f30b3ba750` | **38 passed**: start/reissue/complete 감사 rollback·실제 COMMIT ACK6, A↔B/same/M2/M7/C3·다른 암호 단회 소비·hash 사이 재발급/만료/차단/Scope/ID 경쟁11, migration/제약/GC/실제 allocation DDL 잠금15, 현재 actor·다른 조직·self/Branch/대상 상태·C2 인가6 |
| `auto-a2f109b5be624d868cccb201ba38f56b` | **3 passed**: hash capacity 거부의 source 보존, key/tombstone 전체 행 fingerprint 보존, disabled/restore 후 새 재발급, M2→reset 중간 로그인 없는 경로 |
| `auto-ca07e424d7494e0e87793367217efa95` | **9 passed**: s1 C3 Master/Branch2, MFA C3, 실제 MFA 설치/발급/로그인, 현재 head migration4, native HTTPS MFA |
| `auto-6b6c9b5b4b184fde87003a63fe123f83` | 최종 **fast91 passed**, PostgreSQL245 deselected; Ruff/format/mypy61/Import Linter7 통과 |

native는 Chromium **151.0.7922.34**, 기존 **MFA20/management15**와 새 **reset11** 모두
정확한 boolean true다. fragment 제거·GET 비변이·옛 세션/암호 거부·form 완료·재사용 거부·
자동 로그인 없음·기존 UV 키 로그인·키 목록 보존을 실제 브라우저에서 확인했다. TLS 우회 없이
검증했고 전역 trust 전후 동일성을 검사했다. 기존 **HTTPS58 manifest는 보존**했으나 이번
개발 대상 실행에서는 해당 s1 브라우저 테스트를 다시 실행하지 않았다. 최종 독립 전체에 포함한다.

새 privacy canary도 실제 link_token→complete helper의 `--showlocals` 실패 경로에서 비밀이
노출되지 않음을 확인했다(`auto-3f5d39ca993b498db1fc83066d2246b5`, 1 passed, 최종fast에도 포함).
초기 purpose 오류코드 예상400/401 및 ACK 응답 필드명(error/code→실제 detail) 오류는 테스트
수정 이력이다. 실패 run은 삭제하지 않고 공유 progress 기록에 남겼으며 검증을 통과로 바꾸지 않았다.

실제 수집은 **336 = fast91 + PostgreSQL245**다. 별도 `--collect-only`도 336개를 출력했으나
기존 PG 필수 gate가 실제 pass 없음으로 exit1을 반환했다
(`auto-328a4f35e328428390f319a7003ea225`). 이는 수집 근거이며 테스트 성공이 아니다.
설정 누락·skip/xfail을 성공으로 처리하거나 검사 gate를 완화하지 않았다.

각 기록된 자기 pytest run의 process/schema/profile/NSS/TLS/폴더는 fixture 정리 완료 및
폴더 부재를 확인했다. 공유 Compose DB와 volume은 유지했다. 기존 Starlette/httpx 및 AnyIO
deprecation 경고 2개는 유지한다. 개발자가 전체 PostgreSQL을 중복 실행하지 않았다.

## 동결·인계

공유 폴더 `.local/qa/iam-mfa-management-b2f1b730a9614672/`의
`source-frozen.json` 후보3 전체 파일 해시, `developer-result.json`, `progress.json`,
`password-reset-browser-result.json`이 인계 근거다. 소스 동결 뒤 변경하지 않는다.
후보1/2 중단·실패 이력과 원본 independent 기록은 보존한다. 후보2 PG155 통과·40 미완료는
전체 인수가 아니며 후보3 전체 통과로 재사용하지 않는다.

다음 단계는 root의 독립 검사 진입 → 동결 후보의 fast 및 필수 PG245 전체(HTTPS58/MFA20/
management15/reset11 포함) → 설계자 검토 → 전담 커밋 담당자의 검토·커밋·푸시다.
AB5/production, 운영 본인 확인·전달/기록 보존·접근 정책, 실물·전체 지원 플랫폼 인수,
이번 좁은 범위 밖 상태·역할 변형은 완료하지 않았다.
