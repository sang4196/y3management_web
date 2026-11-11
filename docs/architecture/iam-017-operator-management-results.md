# IAM-017 — Operator 역할 관리·지점 이동 실행 결과

Status: **DESIGNER LOCAL ACCEPTANCE PASS — APPROVED SPLIT VERIFICATION** (2026-11-12).
검증 parent `33c9e20ea36a7ce35833dbc1864b03d0b2c08355`, branch `codex/iam-operator-management`.
[OP-4/OP-5/OP-6](../product/product-decisions.md#review-20261111-operator-management),
[제한 계약](iam-017-operator-management-design.md), [기계 판독 최소 근거](iam-017-operator-management-review.json)를 따른다.

## 구현한 동작

같은 조직의 기존 Master·Branch Admin·Trainer·role0 계정과 허용 관리자 본인에 Operator를 부여하고,
현재/보존 업무 지점 범위에서 회수·같은 지점 재부여를 처리한다. 첫 부여는 ACTIVE/암호 준비/재설정 대기 아님,
회수는 모든 계정 상태, 재부여는 ACTIVE/PENDING_SETUP·DISABLED 제외다. 실제 배정은 활성 Branch만 허용한다.
유효 Operator의 업무 지점 이동은 Master만 모든 계정 상태에서 활성 목적지로 수행한다.
계정 상태/암호·복구 목적·독립 관리자 Scope·Trainer Home/상태·과거 이력을 보존한다.

실제 변경은 raw Operator version을 전진시키고 옛 AuthSession 및 목적별 원본을 폐기한다.
계정 row/security/reset generation은 보존해 원래 비상 복구 사건·승인 lineage를 재기준화하지 않는다.
같은 UoW에서 typed 감사·요청 receipt까지 확정하며 감사/기한/최종 사실 실패는 함께 rollback한다.
no-op/replay는 이전 세션 폐기·감사·Actor 활동을 반복하지 않는다. role0는 로그인할 수 없지만
보존 grant를 근거로 기존 Master 수명/정상 reset 대상에 남는다.

`/operator-roles`는 목적별 exact-ID 조회·역할/지점 명령·현재 권한으로 원래 Actor의 receipt 대사를 제공한다.
새 역할 관리 API의 필수 `X-Y3-Expected-Actor`는 실제 인증 Caller와 비교하는 문맥 전제이며 권한 근거가 아니다.
탭 간 계정 변경·검증 후 전송 경합·늦은 응답에서 이전 선택/UUID를 다른 Actor에 연결하지 않는다.
본인 실제 변경은 다시 로그인한다. 기존 `/operator-accounts` 및 lifecycle의 Operator 초기 재발급은
계정 version과 Operator version을 함께 검사하며 현재 Branch/두 version이 맞을 때만 링크를 표시한다.

신규 `0017_operator_management`는 source의 안정 계정 FK와 원래 Branch snapshot을 분리하고,
관리자 겸임의 실제 인증 Actor·관리 Branch와 Operator Branch를 구분한다. receipt/감사는 대상·Actor 복합 FK로
결속하며 비초기 감사의 NULL 이전 Branch/0 이전 version을 거부한다. downgrade는 installation 관계 AEX를
먼저 획득하고 새 관리 이력·구16이 표현하지 못하는 auth Actor/source snapshot 손실을 DDL 전에 차단한다.
원래0001–0016·의존성/lock·공통 검사 도구·ADR은 변경하지 않았다.

## 독립 검증과 범위

| 검사 | 실제 결과 | 해석 |
| --- | --- | --- |
| 최종 sourceB 수집/fixture plan | 892개 = nonPG197 + PG695 | 실행0/필수PG gate exit1은 PASS가 아님 |
| 새 sourceB fast | 197 passed, Ruff/format/mypy, Import Linter8 kept | 기본 `bash check.sh fast`, 전역 PYTEST_ADDOPTS 미주입 |
| 선정 PostgreSQL | 중복 없는 380개 = 승인 재사용282 + 새 실행98 | 새98은 수정 실패1+이전 미실행97. native2 포함 |
| HTTPS Trainer/Operator | 1사례·trainer manifest50조건 | 실제 현재 Actor/CSRF200→계정 전환→POST409·pending/늦은 읽기 포함 |
| HTTPS 관리자/암호 관리 | 1사례·4manifest(18/9/22/18) | 같은 실행의 각 manifest/결과/run-id를 직접 대조 |
| 선택 검사 실패/skip/xfail/미수집 | 최종0 | 전체PG695·모든 브라우저/운영 배포 인수가 아님 |

sourceA backend181 raw-map SHA는 `ea4fe00095821d6fd2770cfb4f587d5881fd0e2bb8d5871a7cf56671d716620d`,
최종 sourceB는 `52ab16519bffb6b9020880f5dffb14a85b87d1890faa0186c38f9b18dffb50ed`다.
차이는 `test_iam_password_reset_authorization.py`의 실패 테스트 함수 하나뿐이다.
다른283파일, APP/UI/migration/fixture/공통 도구·나머지 함수 AST와 해당 함수 signature/decorator가 동일하다.
같은 모듈의 재사용3사례도 독립 검토했다. 설계자가 이 제한 동등성을 승인했으며 282+98의 정확한 노드 집합은
최소 근거에 남긴다. 단일 최종 source380 실행이나 개발자 성적 합산으로 표현하지 않는다.

실제 Chromium은 `151.0.7922.34`다. native는 매 실행의 TLS 검증 DoH와 process 전용 hosts/dev namespace,
원래 UID1000·동일 APT package/hash를 사용했다. 전역 hosts/resolver는 바꾸지 않았고 원래 HTTPS/NSS/ownership
검사는 유지했다. 기본 DNS 복구 또는 다른 지원 브라우저/운영 환경의 성공으로 확대하지 않는다.
기존 Starlette TestClient HTTPX·AnyIO BlockingPortal alias 경고 두 종류를 숨기지 않았다.

## 발견한 문제와 교정

- 독립 정적 검토에서 열린 화면의 Actor 변경 결속과 감사 CHECK의 NULL/0 경계를 보완했다.
  BA 실제 역할 명령/current receipt 인가 및 두 독립 downgrade 손실 원인도 실제 검사에 추가했다.
- 개발 native의 CSRF 중계가403을 반환해 POST가 없는데 응답을 기다렸다. allHeaders만으로도 해결되지 않아
  특정 헤더 누락 원인은 확정하지 않는다. 원래 브라우저 fetch의 실제 Response200을 확인한 뒤 반환만 보류하는
  테스트 gate로 고쳤다. 앱의 Origin/CSRF/Actor 검사·timeout·50 manifest는 완화하지 않았다.
- 독립 R1 fast는135통과/1실패/61미실행이었다. 전역 `PYTEST_ADDOPTS -x`가 두 의도적 실패를 요구하는
  자식 canary에 상속된 호출 문제였다. 원래 명령으로 바로잡았으며 과거135를 최종197에 더하지 않았다.
- 독립 R2는 Google DoH 성공 전제에서 native 준비 전에 멈췄다. 당시 정확한 DNS Status는 보존되지 않아
  unknown으로 남긴다. 이후 실제 성공한 Cloudflare 경로를 매번 새로 검증했다.
- 독립 sourceA PG는282통과/1실패/97미실행이었다. ACTIVE Master의 일반 restore를404로 기대한 옛 검사와
  승인된 IAM-015 공통 lifecycle 계약이 충돌했다. 제품 코드는 바꾸지 않고 해당 함수만 activation404·restore409·
  현재 ID no-op200 및 version/state/ID/로그인 불변으로 교정했다. 본인 reset/identity false/실제 다른 조직의
  음성 검증은 보존했고 수정 함수와 미실행97을 sourceB에서 새로 통과시켰다.

## 정리와 남은 경계

기존 pytest/fixture만 사용했고 자기 자동 실행의 프로세스/schema/폴더 제거 및 namespace hosts 제거를 확인했다.
공유 Compose DB·재사용 corpus·고정 앱 잠금 경로·원본·누적 변경은 보존한다. 원본 로그/실행 사본은 영구 보존
의무가 없으며 최신 최소 근거를 반영한 뒤 완료·미사용인 자기 QA 자료만 정리한다. 별도 QA 관리 시스템은 없다.

회수된 Operator의 다른 Branch 재배정은 이번 승인에 포함되지 않는다. Member/PT 진행/보상/정산·관리자 승격·
Trainer Home 이동, 전역 모듈 PROPOSED 및 다른 Product OPEN·원본 DB 전환/운영 배포는 이 인수로 승인되지 않는다.
커밋·feature 일반 push는 전담 검토 흐름을 따르며 main 병합/force push는 포함하지 않는다.
