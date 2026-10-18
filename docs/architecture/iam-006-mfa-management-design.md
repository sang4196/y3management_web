# IAM-006 MFA 자격 관리·정상 Master 복구

2026-10-18 승인 정책 중 M1–M7/AB4/C1·2·3/E2의 아래 범위에 한정한 개발 계약이다.
M8 관리자 password reset은 [IAM-007](iam-007-password-reset-design.md)에서 별도로 구현해
[결합 인수](iam-007-password-reset-review.json)했다. AB5 비상 복구는 미구현이다.
부모 인수는 IAM-005, 부모 commit은 `49eadf724185f6ece67ba1daa264823553e58ba7`다.
이 문서는 운영 인수나 Product OPEN 해소를 선언하지 않는다.

## 경계와 순서

B1 본인 키 목록·삭제 → B2 추가 Master 신규 발급·본인 최초 설정 → C 다른 정상
Master의 분실 복구를 한 마일스톤으로 구현한다. 기존 Branch Admin 전용
`scoped_account`를 확장하지 않는다. 승격·강등, 관리자 password reset, DISABLED 또는
PENDING_SETUP 대상 복구 변형, AB5 비상 복구는 구현 범위 밖이다. 그 상태의 복구를
v1 영구 금지로 결정한 것은 아니다. C3 현재 암호 확인 본인 변경은 유지한다.

## HTTP 계약

모든 경로의 prefix는 `/api/v1`이다. 기존 canonical HTTPS/Origin/CSRF와 명시적 MFA
모드를 사용한다. 목록·조회도 현재 정상 password_uv 세션이 필요하다.

| 경로 | 입력/효과 |
| --- | --- |
| GET `/auth/passkeys` | 본인 active 키의 surrogate UUID, 생성 시각, WebAuthn device_type/backed_up, key_set_version |
| DELETE `/auth/passkeys/{key_id}` | expected_key_set_version. 다른 유효 키가 있어야 성공204. 모든 기존 로그인 철회 및 AUTH/PREAUTH/CEREMONY cookie 제거 |
| POST `/admin/master-accounts` | login_id만 입력. Actor 조직에 PENDING_SETUP Master 신규 발급. 201과 최초 설정 링크 |
| POST `/admin/master-accounts/lookup` | 정확 login_id의 최소 계정 상태. 원본 링크 재조회 없음 |
| GET `/admin/master-accounts/{id}` | 동일 조직 Master의 최소 계정 상태 |
| POST `/admin/master-accounts/{id}/activation` | expected_version. PENDING_SETUP Master만 최초 설정 링크 재발급 |
| GET `/admin/accounts/{id}/passkey-recovery` | account_version/key_set_version/pending/generation/expiry. 다른 동일 조직 Master만 |
| POST `/admin/accounts/{id}/passkey-recovery` | expected_account_version, expected_key_set_version, identity_confirmed=true. ACTIVE 대상의 기존 키/세션 철회 및 복구 시작 |
| POST `/admin/accounts/{id}/passkey-recovery/reissue` | 동일 입력. recovery_pending 대상에 새 generation/30분 링크. 이전 권한 부활 없음 |
| POST `/auth/passkeys/recovery/options` | recovery_token + preauth CSRF. 5분 이하 challenge와 제한 cookie |
| POST `/auth/passkeys/recovery/verify` | 제한 cookie/CSRF + 새 UV credential. 204, 자동 로그인 없음 |

삭제 대상이 없거나 타인 소유면404, 현재 본인의 stale keyset/마지막 키면409다.
실패는 키·epoch·세션·감사 변경을 롤백한다. 동시 삭제 패자는 이미 자신의 세션이 철회되어
401일 수 있다. 남은 키로 새 MFA 로그인한 후 마지막 키409를 별도로 검증한다.
키 추가 등록은 key_set_version을 올리지만 기존 정상 로그인은 종료하지 않는다.

추가 Master의 최초 설정은 기존 purpose=setup 원자 처리를 사용한다. 비밀번호와 첫 UV 키,
ACTIVE 전이, setup_complete/passkey_register 감사가 함께 반영된다. 어떤 같은 조직 정상
Master든 설정 대기 계정을 관리할 수 있다. 기존 ACTIVE 계정을 이 경로로 재설정하지 않는다.

복구 시작/재발급은 Actor의 명시적 본인확인 attestation을 요구한다. 이는 서버가 실제 사람의
신원을 독립 검증했다는 증거가 아니다. E2의 확인된 개인 전달 경로를 사용하며 외부 자동
발송, 자유문 개인정보, 신분증 첨부를 추가하지 않는다. raw 링크는 명령 응답에서 한 번만
전달하며 상태 조회로 복원하지 않는다.

## 저장과 원자성

0001–0005는 불변이고 새 `0006_iam_mfa_management`만 추가한다.

- 계정의 key_set_version, recovery_pending, recovery_generation은 업무 상태
  ACTIVE/DISABLED와 분리한다.
- 키는 surrogate UUID와 revoked_at을 갖는다. 삭제는 서버 인증 효력 철회이며 OS 기기의
  인증정보 원격 삭제가 아니다. credential_id의 전역 유일성을 보존하여 묵시적 부활을 막는다.
- 별도 bounded `iam_recovery_credentials`가 hash/대상/version/generation/expiry/consumed를
  보유한다. context의 recovery_id와 purpose=recovery는 setup source_id와 분리된다.
- 시작은 기존 모든 키·모든 세션·대기 context를 폐기하고 계정 row/security/keyset version과
  recovery generation을 올리며 source와 필수 감사까지 같은 UoW로 commit한다.
- 완료는 새 키/키셋 version, pending 종료, row/security version, source/context 소비,
  recovery_complete 감사를 함께 commit한다. 비밀번호·login ID·grant·C2 key/실패 예산은 유지한다.
- 원본30분 source와 context5분은 각각 검사하며 context는 source deadline을 넘지 않는다.
  source 재발급, 계정 보안 변경, 차단 후 복원은 옛 proof를 되살리지 않는다.
- recovery_pending은 약한 모드의 session/password 로그인에도 업무 권한을 주지 않는다.

감사의 허용목록 typed 필드는 key_id, before/after_key_set_version,
before/after_recovery_generation이다. 삭제는 정확한 surrogate UUID와 전후 키셋을,
복구 시작·재발급은 키셋/세대 전이를, 완료·일반 등록은 새 서버 키 UUID와 해당 전이를
저장한다. raw credential ID나 임의 JSON payload는 없다. 과거 사건의 대상 키를
시간 근접성으로 추측하지 않는다. 새 감사 metadata가 남으면 downgrade도 거부한다.

정상 Master는 최종 시점의 ACTIVE/current Organization grant/유효 password_uv 세션/
MFA-ready/active key가 필요하다. 자신에 대한 복구는 금지한다. 따라서 명령을 수행하는
다른 정상 Master가 살아 있는 대안이다. 물리적 기기 소유/실제 접근 가능성을 DB 사실로
보장하지 않으며 모두 접근 불가할 때는 AB5다.

## 잠금과 실패

관리 명령은 Installation guard → 정렬 Account → 정렬 AuthSession → key/source/context
순서를 따른다. WebAuthn 암호 검증은 긴 business 잠금 밖에서 수행하고 저장 직전 목적,
Actor, epoch, source, challenge, 단회 조건을 다시 검사한다. A→B와 B→A 복구는 guard 뒤
현재 Actor를 재검증하여 먼저 철회된 Actor의 반대 요청을 거부한다.

Security allocation은 짧은 별도 선행 UoW다. Account 잠금 안에서 전역 Security guard를
요청하지 않는다. GC는 잠긴 context를 SKIP LOCKED로 건너뛰고, 하위 context가 남은
setup/recovery source도 건너뛴다. source UPDATE 잠금 후 새 statement snapshot으로
하위 context 부재를 다시 확인하여 FK cascade가 잠긴 child를 다시 기다리지 않게 한다.
원본 유효기간/자원 상한은 바꾸지 않고 잠금 해제 뒤 다음 GC가 정리한다.
0006 DDL은 먼저 security_control을 잠가 진행 중의 짧은 할당/GC가 끝나게 한 뒤
업무 테이블 잠금을 얻는다. 업무 테이블 일부를 잠근 채 GC guard를 뒤늦게 기다리지 않는다.
이는 운영 무중단 migration 승인이 아니며 별도 유지보수 migration 게이트는 유지한다.

명확한 실패는 롤백한다. COMMIT ACK 유실은 `commit_outcome_unknown`503이며 이미 반영된
철회를 보상 복원하거나 링크를 자동 재발급하지 않는다. 현재 상태를 조회한 후 사용자가
명시적으로 새 generation을 재발급한다. 실패 응답을 성공 인수로 집계하지 않는다.

## 검증과 운영 한계

실제 CLI 설치·추가 Master 발급·본인 설정·MFA를 사용하는 pytest와 독립 PG 연결/barrier를
사용한다. TestClient의 합성 서명과 native navigator.credentials 브라우저 증거를 구분한다.
기존 HTTPS58/MFA20 manifest를 보존하고 management 별도 manifest를 추가한다.
`/passkeys`는 삭제 전 전 로그인 종료/남은 키 재로그인을 안내하는 얇은 로컬 검수 화면이다.
이를 최종 Responsive 제품 UI 인수로 확대하지 않는다.

운영 production, AB5, 신원확인/안전한 전달 담당자, 기록 보존·열람·파기, 실물 기기와
지원 Chrome/Edge/Safari 최신2개 안정 버전 검수 게이트는 열린 상태다. 새 의존성이나
보존기간/step-up/2인 승인 정책을 추가하지 않는다. 실제 검사 결과는 별도 결과 문서에 기록한다.
