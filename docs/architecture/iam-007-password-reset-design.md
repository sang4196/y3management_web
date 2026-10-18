# IAM-007 관리자 비밀번호 재설정 구현 계약

2026-10-18, 후보 3. 승인된 AB3/C4/C5/M8/A8/A9/C3/C2/AB4/E2를 적용하는
IAM-006과의 결합 증분이다. 독립 인수 전이며 운영 허가는 아니다. 범위 조정으로 이전의
«IAM-006 별도 인수·커밋 후 진입» 조건을 대체했다. Product/ADR 원문은 변경하지 않는다.

## 범위와 사용자 흐름

현재 정상 `password_uv` Master가 같은 Organization의 **다른 ACTIVE 관리자**를 대상으로
본인 확인을 명시하고 시작한다. Master/Branch Admin만 지원한다. 정상 actor 자체가
대상과 다른 사용 가능한 Master임을 최종 잠금 아래 확인하므로 A↔B 경쟁에서 둘 다
미준비가 될 수 없다. 본인 관리자 reset은 다른 Master 유무와 무관하게 금지한다.
마지막 Master도 기존 현재 비밀번호 확인 C3 변경은 가능하며 AB5 비상 복구는 별도다.

시작 즉시 옛 verifier를 NULL로 만들고 모든 세션·대기 MFA 증명을 무효화한다. 계정 업무
상태 ACTIVE, Login ID/예약, Scope, Passkey와 key_set_version, C2 실패/쿨다운은 보존한다.
30분 단회 링크로 새 암호를 설정한 뒤 새 암호와 **기존 UV Passkey**로 로그인한다.
자동 로그인·키 등록·폐기 키 부활·비밀번호 이력/재사용 금지·추가 step-up은 없다.

처음 지원하는 상태에서는 진행 중인 key recovery와 reset을 중첩하지 않는다. 이는 v1
영구 금지 정책이 아니다. 양쪽 요인 분실 시 M2 등록 완료→reset 또는 reset 완료→M2
등록을 순서대로 할 수 있으며 **중간 대상 로그인은 요구하지 않는다**. DISABLED나
PENDING_SETUP reset 시작, 역할 승격/강등, Operator/Trainer/Member, 익명 reset,
외부 발송 서비스, production은 이번 범위 밖이다.

## API와 저장

| 경로 | 계약 |
|---|---|
| GET `/api/v1/admin/accounts/{id}/password-reset` | 현재 actor/target 검사, account_version/pending/generation/expiry만 반환 |
| POST 같은 경로 | expected_account_version, expected_generation, identity_confirmed=true; 201 링크 한 번 반환 |
| POST 같은 경로 `/reissue` | pending 대상만 허용, generation/epochs 증가, 이전 source 소비, 새 30분 링크 |
| POST `/api/v1/auth/password-reset/complete` | reset_token/new_password와 preauth CSRF; 성공204·모든 인증 관련 cookie 제거 |
| GET `/reset#token=…` | 비변이 화면, fragment 즉시 제거, 암호 입력 후 완료 안내 |

IAM의 `password_reset_pending`, `reset_generation` 및 `iam_reset_credentials`를 새0007로
추가한다. source에는 digest·대상·row/security version·generation·만료·소비 여부만 저장한다.
원본 token이나 verifier는 저장하지 않는다. 별도 파생 context는 필요하지 않아 만들지 않는다.
Security capacity에서 `password_reset` 슬롯을 사용한다. 만료/GC가 pending이나 옛 verifier를
복원하지 않는다. GC 후 상태의 expiry는 null이며 정상 Master의 명시적 재발급으로 이어간다.

계정 제약은 PENDING_SETUP+NULL+not pending, 정상 ACTIVE/DISABLED+hash+not pending,
ACTIVE/DISABLED+NULL+pending+generation>0 조합만 허용한다. pending 계정의 기존 차단/
복원은 비밀번호를 만들지 않으며 row/security epoch 변경으로 옛 source를 무효화한다.
복원된 ACTIVE pending 대상의 새 재발급은 별도 명시 동작이다.

## 인증 소비자 점검

| 소비자 | 조회·판정 |
|---|---|
| IAM.verify_login | 명시 SELECT의 recovery_pending/password_reset_pending; 미준비는 dummy timing verify 후 실패 |
| legacy login final | SELECT *의 현재 state/pending/epoch/marker, 옛 proof로 verifier 복원 불가 |
| IAM.authenticate | JOIN에 두 pending 열 명시, 현재 assurance/epoch/grant/active key 확인 |
| C3 prepare/final | 두 SELECT에 두 pending 열 명시, hash 전/최종 거부; 기존 recovery SELECT 수정 보존 |
| MFA.begin_login/authenticate | account SELECT *의 pending 먼저 판정, NULL encode 전에 실패 |
| MFA.context | 현재 epoch와 두 pending 확인; recovery source도 reset pending 거부 |
| setup | PENDING_SETUP/source/epoch 조건과 새 DB 제약으로 ACTIVE reset 우회 불가 |
| M2 start/source | SELECT *의 reset pending 거부, 중첩 불가 |
| restore | hash/pending을 덮어쓰지 않는 UPDATE; ACTIVE 복원이 credential readiness 복원은 아님 |
| reset start/final | 현재 target role/state, key 준비, pending/generation/두 epoch/expiry/single-use |
| Master availability | 정상 다른 actor의 현재 authenticate와 require_master가 증명; 활성 session 수로 대체하지 않음 |

누락 열을 `.get(...,False)`로 숨기지 않는다. 키 metadata는 실제 기기 접근 가능성을 보장하지 않는다.

## 트랜잭션과 경합

start/reissue는 짧은 preflight 종료→Security 슬롯 별도 UoW→최종 Installation guard→정렬
actor/target Accounts→정렬 모든 관련 AuthSessions→source 순서다. actor 현재 권한·CSRF·
대상 version/generation을 다시 검사한다. 실패한 슬롯은 별도 짧은 Security UoW에서만 정리한다.

complete는 preauth 확인 후, 잠금 없는 source/account snapshot으로 기존 bounded Argon2
정책을 수행한다. 이후 Installation→target Account→정렬 sessions→reset source FOR UPDATE,
현재 grant/state/pending/epochs/generation/만료를 재검사하고 암호 저장·source 소비·전 세션
철회·pending 종료·감사를 원자적으로 commit한다. 마지막 preauth 소비도 같은 UoW다.
동일 source에 서로 다른 새 암호를 제출해도 한 번만 완료한다. source 재발급/대상 변경/
만료가 hash 사이에 일어나면 옛 proof는 실패한다.

source에는 파생 child가 없다. GC는 source FOR UPDATE SKIP LOCKED 후 parent를 삭제한다.
기존 setup/recovery의 child 부재 후보 검사와 parent 잠금 뒤 fresh-statement 재검사는 유지한다.
Account 잠금 안에서 Security guard를 취하지 않는다. 새0007 DDL도 control을 먼저 잠근다.

필수 감사 실패는 전체 rollback이다. 실제 COMMIT 이후 ACK 유실은 `commit_outcome_unknown`
503이며 이미 무효화된 암호·세션을 복원하지 않는다. 이미 발급된 source는 issuer의 단순
로그아웃에 의존하지 않는다. 최소 상태 조회 후 명시 재발급으로 전달 불확실성을 해결한다.

## 감사·migration·검증

reset_start/reissue/complete에 고정 typed before/after_reset_generation 및
before/after_password_ready를 기존 actor/target/Scope/row version과 함께 기록한다.
암호/hash/token/임의 JSON은 감사에 없다. 0001–0006은 바이트 보존한다. 새0007 downgrade는
pending/generation/source/parent/typed 감사 또는 새 action이 하나라도 남으면 거부하고,
아직 reset을 쓰지 않은 상태에서만 데이터 보존 왕복을 허용한다.

검증은 실제 API 발급·설정·MFA, PostgreSQL 별도 연결 경합, 필수 감사 rollback/실제 ACK,
새 head 보존, GC 잠금, native HTTPS로 나눈다. 기존 HTTPS58/MFA20/management15는 유지하고
별도 reset11 manifest를 추가한다. TestClient·가상 인증기 검증은 실물·전체 지원 브라우저·
운영 인수를 뜻하지 않는다. 실제 실행과 남은 검사는 별도 results에 기록한다.
