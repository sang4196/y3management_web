# IAM S2c — Login ID 변경 기술 설계

2026-10-15. 승인된 A2/C1/C2/C6/E3/E4, PR-021/027, NFR-001 및 ARCH-002 범위의 개발 증분이다. Product/ADR 승인 상태를 변경하지 않는다. 구현 검증 결과는 별도 `iam-004-login-id-results.md`에서 보고한다.

## 범위와 계약

현재 Master가 같은 Organization의 ACTIVE Branch Admin을 대상으로 `PATCH /api/v1/admin/accounts/{id}/login-id`를 호출한다. body는 `login_id`와 양의 정수 `expected_version`만 허용한다. 기존 ASCII 3–64자 패턴과 소문자 정규화를 재사용하고 공백을 trim하지 않는다. 추가 암호 확인은 요구하지 않는다.

현재 인증/CSRF/Master/scope/state/version을 검사한다. 다른 조직·존재하지 않는 대상 및 범위 밖 Master 대상은 404, 비Master/CSRF 실패는 403, stale/state/타계정 예약 충돌은 409다. 소유자나 다른 조직 정보는 응답하지 않는다. 응답은 기존 최소 Account DTO이며 내부 budget key는 노출하지 않는다.

버전 검사를 통과한 정규화 동일 ID는 no-op다. `touch=False`로 Master 세션의 last_activity까지 보존하고 ID/예약/key/버전/대상 세션/감사를 바꾸지 않는다. stale 동일 ID 요청은 409다. 다른 상태·Master·Trainer의 ID 변경은 후속 미구현 범위이며 영구 금지가 아니다.

## 계정 변경과 감사

기존 Installation → 정렬 Account → 정렬 affected AuthSession → Credentials 잠금 순서를 따른다. 미예약 ID를 대상 소유로 예약하거나 대상의 과거 예약을 재사용한다. 타계정 예약을 가져오지 않고 이전 예약을 삭제하지 않는다. 기존 current-ID 소유자 deferred FK 및 전역 유일성을 유지한다.

첫 실제 변경은 변경 전 current ID의 legacy HMAC을 nullable `login_budget_key`에 고정한다. 이후 변경은 nonnull key를 덮어쓰지 않는다. 새 current ID와 key를 같은 UPDATE로 저장하고 row/security version을 각각 1 증가시킨다. 대상의 모든 기존 AuthSession을 철회하고 잔여 credential을 무효화한다. ID/예약/key/version/철회/필수 감사는 한 Application UoW다. 암호/hash, 계정 UUID, 역할·Scope·업무 이력 및 Master 자신의 인증은 보존한다.

실제 version 변경 분기에서는 같은 UoW에서 같은 `management=True`/target으로 기존
`authenticate(...touch=True)`와 CSRF 검사를 다시 수행한다. 현재 actor 세션의 last_activity만 갱신하고
다른 Master 세션·actor account version·absolute expires_at은 보존한다. 이미 보유한 동일 Account와
AuthSession 잠금만 재사용한다. 최종 재인증 시 idle/absolute 만료라면 갱신 없이 전체 변경을 rollback한다.
no-op는 이 분기를 지나지 않는다. 활동 갱신도 필수 감사와 함께 commit/rollback한다.

관리 감사 `login_id_change`는 명시적 전후 정규화 ID와 기존 actor/target/역할/Scope/전후 version 필드를 사용한다. DB CHECK는 전후 ID를 이 action에만 허용하고 유효한 서로 다른 정규화 ID를 요구한다. 로그인 실패에는 입력 ID를 기록하지 않는다. 감사 조회 UI/권한은 추가하지 않는다.

## C2 실패 제한의 연속성

Security.reserve는 기존 security_control guard 안에서 하나의 SQL snapshot으로 현재 account UUID/security_version/key와 ID 예약 여부를 읽는다. Account row lock이나 ACTIVE 조건을 추가하지 않는다. 따라서 DISABLED/restore에서도 같은 current-ID budget을 선택한다.

- 현재 ID: 고정 key가 있으면 사용하고, 없으면 기존 HMAC(current ID)를 사용한다.
- 과거 예약 ID: 유효 Login ID에 없는 `:`를 포함한 `reserved:` domain의 익명 HMAC을 사용한다. 계정 alias가 아니다.
- 미예약 ID: 기존 익명 HMAC(ID)를 사용한다.

Reservation에는 실제 key/id와 admission 당시 current account UUID/security_version(익명이면 None)을 묶는다. 암호 검증의 조회 snapshot이 이 principal/version과 다르면 **해시 검증 전에 503**으로 종료한다. 따라서 익명 admission 이후 새 current ID가 된 계정을 다른 bucket으로 검증하거나 잘못된 암호를 새 계정의 실패 감사로 귀속시키지 않는다. 일반 잘못된 암호/없는 ID는 기존 401 및 dummy hash 방어를 유지한다.

최종 IAM.login의 account lock 아래에서도 proof/account/reservation의 UUID/security_version을 결합하고 실제 reservation.key가 고정 key 또는 legacy HMAC(current ID)와 일치하는지 검사한다. 불일치는 session 생성·preauth 소비·성공 audit·hash upgrade 저장 전에 503이다. 검증 뒤 rename이 선행한 old proof는 기존 security_version 검사로 거부한다. A→B→A의 admission ABA 역시 version으로 차단한다.

503은 새 admission 재시도가 가능하다는 뜻이며 pending 즉시 반환을 보장하지 않는다. 기존 pending/lease는 보수적으로 보존하고 live child 없는 session slot만 기존 안전한 release로 정리한다. attempt rekey, 실패/cooldown reset, 무한 재시도, 새 횟수 정책은 없다. HashAdmissionRejected의 기존 cancel과 구분한다.

변경 전 실제 계정으로 검증을 시작한 요청은 원래 key에서 완료된다. login business commit이 먼저면 뒤따르는 rename이 그 세션까지 철회한다. 늦은 finish(success)가 세션을 되살리거나 실패를 지우지 않는다. 새 이름의 과거 익명 실패는 익명 bucket에 남으며 계정에 병합하지 않는다. 과거 ID의 변경 후 익명 공격도 별도 domain에 남는다.

## 용량·GC·migration·실패

영구 key는 Account 메타데이터이며 ephemeral budget과 FK로 연결하지 않는다. 기존 budget/attempt의 PK/FK/TTL/capacity/GC를 유지하고 동일 key로 다시 생성할 수 있다. 반복 rename으로 영구 보안 redirect 목록이나 budget을 추가하지 않는다. 영구 예약 ID는 E4의 업무 데이터다.

rename UoW에서 Security.guard/reserve/finish를 호출하지 않는다. reserve의 account 조회는 nonlocking MVCC read다. 기존 로그인 slot 할당은 account lock 전에, finish는 business UoW 후 실행한다. 새 역방향 잠금 edge를 추가하지 않는다.

새 `0004_iam_login_id`만 작성하며 0001–0003은 보존한다. key는 nullable/32byte CHECK/UNIQUE이며 migration에서 secret을 읽거나 legacy key를 일괄 생성하지 않는다. downgrade는 테이블 잠금 뒤 신규 감사 또는 nonnull key가 하나라도 있으면 DDL 전에 거부한다. active cooldown을 삭제하거나 감사 없이 anchor를 drop하는 downgrade는 허용하지 않는다.

감사/저장 실패는 원자 rollback한다. commit ACK 유실은 이미 전체 저장되었을 수 있으므로 account UUID로 현재 ID/version을 조회한다. 이전 이름·key를 보상 복원하거나 예약을 삭제하지 않는다. 실제 운영 키 회전, MFA, 추가 역할 및 전체 IAM 완료를 이 개발 인수 범위로 확대하지 않는다.
