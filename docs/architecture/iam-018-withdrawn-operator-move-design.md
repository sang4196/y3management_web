# IAM-018 — 회수된 Operator의 업무 지점 변경

Status: **IMPLEMENTED / DESIGNER LOCAL ACCEPTANCE PASS — FRESH SINGLE SELECTED RUN** (2026-11-12).
Parent `7b64f5731ed993f5f8473a1476f27fb6c4931513`, branch `codex/iam-withdrawn-operator-move`.
[OP-7](../product/product-decisions.md#review-20261112-withdrawn-operator-move), BR-OPS-011,
PR-001/021/026/030 및 [IAM-017](iam-017-operator-management-design.md)의 제한 계약을 입력으로 사용한다.
전역 모듈/트랜잭션 PROPOSED·다른 Product OPEN·원본 DB 전환/운영 게이트는 유지한다.

개발·독립 정적 검토와 구현 후 최종 동결본에서 새 독립 fast197·선정 PG104 단일 실행을 통과했다.
같은 PG 실행의 실제 HTTPS/native1사례·54조건을 포함한다. [결과](iam-018-withdrawn-operator-move-results.md)와
[최소 인수 근거](iam-018-withdrawn-operator-move-review.json)를 따르며 전체728PG·운영 인수는 아니다.

## 변경 범위

기존 Operator grant가 있는 같은 조직 계정이면, Master는 `granted=true/false`와 계정 상태에 관계없이
업무 지점을 활성 목적 Branch로 변경할 수 있다. 비활성 출발지는 허용한다. `granted=false`를 그대로
유지하며 기존 계정 상태/restore_state·암호/reset/recovery intent·독립 관리자 Scope·Trainer binding/
Home/업무 상태·C2/과거 이력을 바꾸지 않는다. grant 없는 계정 이동은 계속 거부한다.

`can_move`는 현재 Master와 보존 grant 존재에 따라 반환한다. 기존 `/operator-roles` 화면과
`POST /api/v1/admin/operator-roles/{account_id}/branch`를 확장하며 새 화면/API/역할은 만들지 않는다.
회수 상태의 이동 성공도 회수 상태로 표시한다. 별도 재부여는 OP-5의 상태·현재 업무 지점 인가를 따른다.
DISABLED 이동 성공만으로 재부여·차단 해제·로그인을 허용하지 않는다.

## 유지할 명령·인가·원자성

IAM-017의 검증된 현재 Caller·필수 expected Actor·CSRF·현재 조직/Branch 사실·expected account/grant
versions·operation UUID와 fingerprint를 그대로 사용한다. Branch Admin은 출발/도착 Branch를 관리하거나
다른 역할을 겸해도 move를 호출할 수 없다. 타 조직/지점 직접 요청, stale version/Actor를 거부한다.

실제 이동은 Operator grant version을 한 번 전진시키고 **원래 granted 값을 보존**한다. 기존 잠금 순서와
단일 UoW 안에서 옛 로그인·기존 설정/reset/복구 링크 철회, typed 감사와 immutable receipt를 함께 확정한다.
새 링크/암호는 만들지 않는다. 필요한 링크는 원래 목적·현재 자격/권한에 따른 명시 재발급만 허용한다.
회수 상태 이동도 독립 역할의 기존 로그인/링크를 보존하는 예외를 만들지 않는다.

같은 Branch no-op와 일치 replay는 기존 활동/원본 기한을 검증하며 target/version·새 로그인·감사·원본을
다시 변경하지 않는다. 실제 변경이 아닌 같은 비활성 Branch no-op는 IAM-017 기준을 유지한다.
과거 receipt와 현재 상태를 분리하고 조회/replay는 원래 Actor identity와 **현재** Scope로 제한한다.
이동 전 Branch Admin은 보존 grant가 false여도 이동 후 역할 관리/receipt 접근을 계속할 수 없다.
새 Branch 관리자의 별도 재부여 역시 ACTIVE/PENDING_SETUP만 허용하고 DISABLED는 거부한다.

원래 idle/absolute 기한·감사 뒤 최종 사실·typed self post-state proof와 실패 rollback을 유지한다.
Master 본인도 회수된 Operator 이동 대상일 수 있으며 성공 시 본인의 옛 로그인을 철회하고 재로그인을
요구한다. 독립 Master 권한/계정 사실을 변경하거나 마지막 Master 보호를 우회하지 않는다.

## 새 migration과 호환 경계

원래0001–0017·의존성/lock·공통 검증 장치는 보존한다. 기존0017의 typed move 감사 CHECK가
`before_granted AND after_granted`를 요구하므로 새0018에서 move는 **전후 granted 동일** 조건으로
확장한다. before Branch NOT NULL/양의 version, 실제 Branch 변경, version+1, Master Actor와 복합
receipt/target/Actor FK는 유지한다. role add/revoke/regrant 조건은 완화하지 않는다.

기존 행/역할/회수 상태를 backfill하거나 새 grant/권한을 추론하지 않는다. 별도 이력·전환 시스템은 만들지 않는다.
설치 관계 AEX 선취·정확한 revision/policy 전제·동일 transaction DDL을 사용한다. downgrade는0017에서
표현할 수 없는 회수 이동 감사가 있으면 DDL 전 거부한다. `action=move AND granted=false` receipt도
감사가 없는 같은 지점 no-op를 포함해 거부한다. 원래17 명령 계약이 만들 수 없는 확정 결과의 호환 보호다.
보존된 회수 grant 자체나 일반 revoke/regrant 이력만으로 downgrade를 거부하지 않는다.
0017에서 이름을 지정하지 않은 전이 CHECK는 실제 catalog의 원래 전이 식/열을 확인해 정확히 하나만
교체하고 예상 밖 형상이면 중단한다. 다른 CHECK를 함께 지우거나 생성 이름 suffix를 추측하지 않는다.
빈/표현 가능한18↔17 왕복과 손실 차단 시 원래 schema/행/marker 보존을 검증한다.

현재 runtime/CLI는 정확한 single head18을 확인하고 이전17에서 거부한다. parent7b64의 runtime은17에서
동작하고18에서 거부해야 한다. 원래 auth policy2/transition target14는 유지한다. 과거 revision 직접 검사와
현재 앱용 head 준비를 구분하며 번호 일괄 치환·stamp만으로 실제 DDL을 대체하지 않는다.

## 구현·독립 검증

개발자와 독립 tester는 먼저 실제 영향을 read-only로 검토한다. 진입 결과를 확인한 뒤 개발자 한 명이
관련 backend source·새0018·테스트/필요 개발 안내를 작성하고 root는 Product/Architecture를 작성한다.
별도 lifecycle 도구/framework/dependency를 도입하지 않으며 사용자 변경을 되돌리지 않는다.

영향에 맞는 실제 검증을 선정하고 동결 소스·수집 node·실제 exit와 판정을 기록한다.

- ACTIVE/PENDING_SETUP/DISABLED/reset 대기의 회수 grant 이동과 grant 없음 거부, 원래 false/계정/독립 역할/Home 보존.
- 현재 Master 전용·타 조직/비활성 목적지·BA 출발/도착 Scope·expected Actor/version·이동 전후 현재 인가.
- 옛 인증/링크 철회·원래 목적 재발급 조건·role0 로그인 금지·DISABLED 재부여 금지·명시 재부여 시 새 지점 사용.
- receipt/no-op/replay·새 로그인 보존·ABA/stale 입력·감사 실패 rollback·경합/원래 기한과 self 철회.
- 실제 PG CHECK/FK·원래 이력 보존·18↔17/downgrade 손실 보호/잠금·parent/current runtime 경계.
- 기존 도구의 실제 신뢰 HTTPS/browser에서 회수 상태 조회→Master 이동→회수 유지와 별도 재부여 흐름.

공통 fast·Import Linter 및 선정 PG/브라우저를 독립 실행한다. 전체 회귀·단일 전체 실행과 선정/분할 검증을
구분하며 새 migration 영향 밖의 전체 기능을 반복하지 않는다. 실패 원인과 미실행·환경 제한을 숨기지 않는다.
QA는 ignored `.local/qa/`와 기존 pytest/fixture에 두고 자기 프로세스/schema/임시 폴더를 정리한다.
최소 결과만 보존한 뒤 설계자 검토→전담 한글 상세 커밋·일반 feature push로 마친다. 원본 DB 적용/배포는 없다.
