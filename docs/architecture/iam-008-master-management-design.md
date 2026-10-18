# IAM-008 — 다른 Master 계정 관리 계약

상태: 승인된 구현 범위의 기술 계약. Product 정책 변경 없이 A8/A9/E6·C6/E3/E4 및 기존 C1/C2/M7/M8을 적용한다. 기준은 [Product](../product/README.md), [결정 게이트](decision-gates.md), [모듈 경계](module-boundaries.md), [트랜잭션](data-and-transactions.md)다. 독립 인수 전 구현 완료로 간주하지 않는다.

## 범위와 인가

현재 password_uv 세션으로 인증된 ACTIVE·password/key 준비 완료·reset/recovery pending 아닌 동일 조직의 다른 Master만 명령을 수행한다. 최종 잠금 아래 이 actor가 살아남는 Master의 근거다. 세션 개수나 과거 역할로 가용성을 추정하지 않는다. 기존 Branch Admin 전용 scoped_account와 onboarding 조회 계약은 유지한다. 자기 대상·승격/강등·복합 역할·AB5는 이번 증분 밖이며 영구 제품 금지로 선언하지 않는다.

## HTTP 계약

기존 GET `/api/v1/admin/master-accounts/{id}`의 최소 Account 응답을 재사용한다. 성공은 200, account_id/login_id/state/version/admin_scope만 반환하며 다른 actor 쿠키를 유지한다.

| 명령 | 입력 | 대상 상태 |
| --- | --- | --- |
| PATCH `/api/v1/admin/master-accounts/{id}/status` | expected_version, status=DISABLED | ACTIVE → DISABLED |
| POST `/api/v1/admin/master-accounts/{id}/restore` | expected_version | DISABLED → ACTIVE |
| PATCH `/api/v1/admin/master-accounts/{id}/login-id` | expected_version, login_id | ACTIVE |

HTTP 형태/Origin → 현재 actor·CSRF → 목적별 대상 인가 → expected_version → 상태 → ID no-op/충돌 순서다. 인증 실패401, 정상 비Master/CSRF403, 없는/다른 조직/비Master/자기 대상404, stale/상태/ID 충돌409, strict DTO422, 감사/DB 실패503이다. COMMIT ACK 유실은 기존 commit_outcome_unknown을 유지한다. 최신 최소 조회로 확인하며 맹목 재시도하지 않는다.

정규화한 동일 ID는 stale 검증 뒤 200과 원래 version을 반환한다. 이 경우 epoch·예약·세션·source·감사 효과가 없다. 반복 차단/복구는409다. 이전 ID는 원계정에 예약되고 원계정 재사용은 허용한다. C2 안정 키/실패창과 원래 암호·Passkey 전체 행/keyset·grant를 보존하며 새 ID로 암호를 재해시하지 않는다.

## 트랜잭션과 철회

Installation → UUID 정렬 actor/target Accounts → ID 정렬 관련 Sessions → activation credentials → MFA contexts → recovery credentials → reset credentials 순서다. 각 source는 ID 순서로 잠그며 모두 IAM 소유다. 명령 전체가 같은 UoW에서 row/security version 증가, 대상 세션 철회, 이전 setup/login/add/recovery/reset source 소비, 필수 typed audit를 commit한다. MFA context의 일시 password_hash는 제거하지만 계정 원본 암호는 변경하지 않는다. source 변경 뒤 actor 인증·CSRF·Master 목적 인가를 재확인한다. Security GC/allocate나 암호 hashing을 업무 잠금 안에 추가하지 않는다.

pending 대상도 상태 조건을 만족하면 관리할 수 있다. pending/generation·NULL 암호·키 폐기 사실은 보존하고 기존 source/proof는 무효화한다. 복구 ACTIVE는 준비 완료를 뜻하지 않고, pending factor는 명시적 재발급 뒤 완료해야 한다. 이전 세션/source는 복구로 살아나지 않는다. no-op은 유효한 pending source를 소비하지 않는다.

## 검증과 한계

실제 CLI 최초 Master와 API 발급/설정된 다른 Master로 lifecycle/ID/인가/no-op/예약/pending·rollback/ACK/경합을 검증한다. 실제 HTTPS native 도구에 별도 manifest를 추가하고 기존 58/20/15/11 항목을 보존한다. 개발 표적 검사와 fast 후 소스를 동결해 독립 전체 검사를 수행한다. 결과는 [실행 결과](iam-008-master-management-results.md)에 분리한다. migration0001–7, 의존성, Product/ADR 및 이전 인수 자료를 변경하지 않는다. 전 역할 가용성/업무 모듈/운영 인수를 완료했다고 확대하지 않는다.
