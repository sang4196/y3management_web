# IAM-010 — 정상 Master의 기존 비상 복구 인계

2026-10-20. [R4=1 승인](../product/product-decisions.md#review-20261020-ab5-r4) 및 별도 구현 진입에 따른 제한된 로컬 계약이다. 운영 인수나 전체 IAM 완료를 뜻하지 않는다.

## 범위와 진입

현재 정상 password+UV Master만 같은 Organization의 다른 ACTIVE Master를 처리한다. 최초 인계는 최신 미완료 운영 사건의 링크 만료 이후만 허용한다. 인계된 최신 자식은 전달 실패·유실·만료에 대해 어느 정상 Master든 명시 재발급할 수 있으며 전담 소유자를 만들지 않는다. 새 operation ID, 정확한 parent ID, 전체 현재 snapshot과 본인 확인을 요구한다. 원래 요인은 서버가 결정하며 확장·축소하지 않는다.

일반 M2/reset의 opposite-pending 차단, 운영 CLI의 권한·원본 수동 승인·현재 all-unavailable 조건은 유지한다. 이후 새 적법한 운영 재발급도 기존 계약대로 가능하다. 계정/역할/Scope 복원·자기 reset·Workforce/PT/정산은 제외한다.

## 사건과 권한

발급별 영속 case와 bounded source 모델을 유지한다. 새 case의 supersedes는 직전 발급, approval_origin_case_id는 인계 직전 운영 발급을 참조한다. 이후 정상 재발급은 같은 origin을 계승한다. 원래 운영 승인/실행 정보는 변경하거나 새 승인처럼 복사하지 않는다. 정상 Master의 현재 권한이 새 발급 근거다.

parent는 완료되지 않았고 최신이어야 한다. 대상 row/security/keyset/reset/recovery generation 모두 parent 발급 후 값과 같고 요청 snapshot과도 같아야 한다. password는 reset pending·hash 없음·recovery pending 없음·active key 존재, passkey는 그 반대, both는 두 pending·hash와 active key 모두 없음을 요구한다. GC가 old source를 삭제해도 durable case로 검증한다. 완료/대체/epoch 변경/불충분 요인은409, 타 조직/자기 대상/없는 사건은404, 잘못된 인증401/CSRF·Master 권한403이다. 최신 사건을 자동 선택해 재시도하지 않는다.

## API와 원자성

현재 관리자 API 이름을 따라 target별 emergency 상태/operation 상태 GET과 handoff POST를 추가한다. GET은 no-touch/no-GC이며 token·운영 개인정보를 반환하지 않는다. POST는 정상 AuthSession CSRF와 identity_confirmed=true를 요구하고 commit 확인 후 한 번만 recipient 링크를 반환한다. 모든 응답은 기존 no-store 규칙을 따른다. 전달 실패·commit 불명은 operation 상태 조회로 대사하며 원 token 조회·자동 재시도·철회 보상은 없다. 필요하면 새 operation/명시 parent로 재발급한다.

사전 인가는 touch=false, emergency slot 확보/해제는 collect=false다. 최종 업무 UoW에서 Installation → UUID순 actor/target Accounts → 두 계정 Sessions ID순 → target keys → 고정 순서 sources/contexts를 따른다. target Account가 사건/완료/관리 변경의 직렬화 지점이다. effect 직전 current actor/grant/session expiry·idle/CSRF를 재검사하며 선행 touch로 세션을 구제하지 않는다. 성공한 실제 actor AuthSession의 last_activity만 정상 관리 활동으로 갱신할 수 있다. 다른 actor 세션·credential/epoch·타 계정 인증 행·C2는 변경하지 않는다.

대상의 모든 로그인/대기 권한만 철회하고 선택 요인의 generation 및 row/security(키 포함 시 keyset)를 증가시킨다. 이미 폐기된 key tombstone 시각과 선택 밖 요인을 보존한다. 새 case/source 및 typed audit가 같은 UoW로 성공/실패한다. 감사 이후 commit 직전에도 touch 없이 actor 만료/인가를 재검사한다. slot의 실제 만료를 넘긴 발급은 거부한다.

## 수신자와 감사

기존 emergency UI/fragment 제거/preauth+CSRF/단회 source 최대30분/context 최대5분을 재사용한다. hash/실제 WebAuthn 검증은 업무 잠금 밖에서 수행하고 최종 target 잠금 안에서 case/source/context/proof·전체 epoch·현재 권한을 검증한다. both는 임시 hash와 실제 UV 새 key를 함께 저장하고 두 pending을 원자적으로 해제한다. 이전 링크/context 소비와 감사 실패 rollback을 유지하며 자동 로그인하지 않는다. 발급자 역할이 이후 변경돼도 수신자에게 미승인 지속 발급자 조건을 추가하지 않는다.

인계 감사 actor는 실제 Master, scope ORGANIZATION이며 takeover/reissue와 parent/origin을 typed 필드로 구별한다. 완료 actor는 실제 대상 RECOVERY_RECIPIENT다. 운영 완료는 기존 manual/executor 의미를 유지하고 정상 자식 완료는 current_master/origin으로 구별한다. 가짜 executor UID/owner 승인·임의 JSON payload·secret 감사는 없다.

## 저장과 검증

forward0009만 추가한다. case issuer_kind operating/master_handoff, 실제 issuer_account_id와 approval_origin_case_id, authority mode manual/current_master를 정규화한다. operating 필수 메타데이터/시간 제약과 handoff의 명시 NULL 조건을 variant CHECK로 분리한다. 정상 parent/origin 동일 org/account/factors 복합 FK, parent 분기 유일성, self-parent 금지를 추가한다. 기존 운영 재발급은 요인 변경이 가능하므로 handoff의 동일 요인 FK를 운영 parent까지 전역 적용하지 않는다. origin의 operating 종류·인과 row_version/최신성은 IAM 잠금 검증이며 FK가 자동 보장한다고 주장하지 않는다. 새 감사의 필수/금지 NULL을 명시하고 기존 운영 감사 의미를 보존한다. handoff 이력이 있으면 downgrade를 거부한다.

기존 테스트/migration/manifest/dependency는 보존한다. 새 검증은 세 요인/최종 인가·expiry/lineage/GC 후 인계/부족 요인/DB NULL·FK·downgrade, 대상 외 보존·원자성, 실제 crypto 이후 재발급 경합 및 실제 HTTPS 관리 발급→recipient→정상 로그인을 확인한다. 개발 표적 검증·fast/수집 이후 source를 동결하며 전체 독립 검증은 별도다. QA 자료는 기존 fixture의 고유 ignored 폴더에서 최소 증거 보존 후 자기 자원만 정리한다.

## 실제 HTTP 계약

공통 prefix는 `/api/v1`이다. `GET /admin/master-accounts/{ident}/emergency-recovery`는 최신 사건, `GET /admin/master-accounts/{ident}/emergency-recovery/{operation}`은 명시 사건을 조회한다. 알 수 없는 query parameter는422, 없는 사건은404다. 응답은 operation_id/factors/expires_at/status/issuer_kind/approval_origin_case_id/supersedes_case_id/snapshot만 포함한다. snapshot은 row_version/security_version/key_set_version/reset_generation/recovery_generation 및 두 pending·password_ready/key_ready다.

`POST /admin/master-accounts/{ident}/emergency-recovery/handoff`는 operation_id, supersedes_case_id, expected(snapshot), identity_confirmed만 허용한다. 정수/boolean은 strict이며 임의 factors/운영 승인 필드는422다. 201 응답은 operation_id/recipient_link/expires_at만 포함한다. commit 불명은503 commit_outcome_unknown이며 성공 링크를 반환하지 않는다. operation GET으로 존재/상태를 확인하고 필요 시 최신 parent에 새 operation으로 명시 재발급한다.

최종 lease 검사는 Service의 application clock을 사용하지 않는다. 감사 뒤 최종 actor 검사와 함께 IAM HandoffPort.confirm이 PostgreSQL clock_timestamp 기준 실제 source·slot·target/case를 재검증한다. actor 유효 상태라도 lease가 지났으면 전체 발급을 rollback하며 미전달한다. 마지막 인가 성공 전까지 last_activity를 변경하지 않는다.
