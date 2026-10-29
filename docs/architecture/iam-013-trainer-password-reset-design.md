# IAM-013 실제 Trainer 연결 계정 분실 암호 재설정 계약

2026-10-30 제한 기술 계약·구현·독립 선정 검증 및 로컬 설계자 인수 PASS. 운영 승인은 미완료다.
기준 parent는 WORKFORCE-002 인수·전담 커밋을 마친 `24a913454f3030336db0281c96f56748f721fa67`,
작업 branch는 `codex/iam-trainer-password-reset`이다. 검토된 r3 입력의 SHA-256은
`3ff4bcab6bcf5eb26db134915381ffd154b6cd89a3acc2417337f3d8e2a0c032`다.
Product/OPEN/ADR 및 전역 모듈 PROPOSED 상태는 변경하지 않는다.

## 범위와 정책 근거

기존 [IAM-007](iam-007-password-reset-design.md)의 비밀번호 재설정을 실제 Trainer와
불변 동일인 연결이 있는 ACTIVE 계정까지 확장한다. 새 Product 질문은 없다.

| 근거 | 적용 |
| --- | --- |
| A8, BR-OPS-014 | 같은 Organization Master만 관리자 reset 수행. Trainer-only도 BA 위임 금지. 발급자/현재 Home 관리자라는 사실은 reset 권한이 아니다. |
| C4, PR-021/026 | 명시 시작 즉시 옛 비밀번호와 전 로그인 무효화. 대상자가 새 암호 설정 후 현재 조건으로 다시 로그인. |
| C3/C5, M8, A9 | 본인 관리자 reset 금지. 현재 암호를 알면 C3, 분실하면 다른 정상 Master, 마지막 Master 분실은 AB5. 마지막 정상 Master 보호 유지. |
| AB3, E2 | 30분 단회 링크, 관리자 본인 확인 후 대면/확인된 1:1 연락으로 전달. 자동 이메일 없음. |
| AB4, M1/M2 | 현재 관리자 역할이면 비밀번호+UV Passkey. reset은 기존 key나 Scope를 복구하지 않는다. |
| B2/G1/I2, BR-OPS-012/019 | Trainer 업무 상태·역할 grant·IAM 계정 상태 분리. 역할 0/비활성 Trainer 단독 로그인 금지 유지. |
| C7 | 인증/계정 감사 앱 열람은 같은 조직 Master 전용. Trainer 상태 관리 권한으로 확대하지 않는다. |

C4의 ACTIVE 계정 자격 복구는 B2/I2의 로그인·업무 접근 허가와 별개다. 따라서 inactive 또는
회수된 grant의 연결 계정도 암호만 복구할 수 있으며 계정·연결·역할·업무 상태를 자동 복원하지 않는다.
IAM-007/I1/I2에서 reset이 범위 밖이었다는 것은 해당 증분의 미구현 경계이지 A8의 미승인을 뜻하지 않는다.

Operator 일반 지원, 공개 비밀번호 찾기, 계정 발급/최초 설정, 역할 승격, Home/보상 변경,
추가 복구 수단과 실운영은 이 증분에 포함하지 않는다. ARCH-002 및 관련 결정 게이트는 전체 종결하지 않는다.

## 대상 상태 조합

공통 대상은 admin 또는 같은 조직의 실제 Trainer binding을 가진 계정이다. 같은 조직의 다른
정상 `password_uv` Master가 현재 세션·권한·CSRF를 충족해야 한다.

| 대상 | 시작/재발급/완료 | 완료 뒤 접근 |
| --- | --- | --- |
| ACTIVE, Trainer active/grant=true, admin 없음 | 대상 Passkey 없이 가능 | 현재 조건을 충족하면 새 암호 로그인 |
| ACTIVE, Trainer inactive 또는 grant=false, admin 없음 | 자격만 복구 가능 | 업무 비활성/역할 0 로그인 차단 유지 |
| ACTIVE, 관리자 겸임, Trainer active/grant 임의 | 기존 관리자 계약. 시작/재발급에 live key 필요 | 관리자 로그인은 기존 UV 필요, Trainer 업무는 별도 판단 |
| ACTIVE, Home만 비활성 | 기존 G1 조건 유지 | Home 상태 자동 변경 없음 |
| PENDING_SETUP | reset 불가 | 기존 I1 최초 설정/명시 재발급 조건 유지 |
| DISABLED | reset 불가 | 별도 승인된 계정 복구 경로 필요 |
| admin도 binding도 없음 | 미지원 | reset으로 계정 생성/연결하지 않음 |
| recovery_pending | 기존 중첩 거부 유지 | 기존 M2/reset 순차 복구, 중간 대상 로그인 불필요 |

시작은 reset pending=false, 재발급은 pending=true 및 기대 버전 일치가 필요하다.
완료는 현재 ACTIVE/pending 및 유효 source가 필요하다. 본인 Master는 Trainer 카드로 접근해도
관리자 reset을 수행할 수 없다. 단순 링크 열람은 상태·자격을 변경하지 않는다.

## IAM 소유권과 공개 계약

기존 MFA adapter 내부의 `_reset_supported`, `_reset_target`, `_reset_account`만 추가한다.
reset_state/reset_change/start_reset/reset_source/prepare_reset/complete_reset의 여섯 경로에서
이 helper를 사용한다. MFA.account/recovery_target/context 및 WebAuthn/M2/AB5 일반 경로의
관리자 전용 조건은 그대로 둔다. 새 adapter/프레임워크/UoW 조립 변경은 없다.

AccountRoles의 현재 admin 및 조직 일치 binding을 사용하며, grant나 Trainer active를 암호 자격
복구의 허용 조건으로 오용하지 않는다. Workforce 내부 SQL을 읽지 않는다. 대상 live-key 조건은
현재 admin일 때만 적용한다. 기존 ResetState/ResetChange/ResetProof와 MFAPort 네 reset 메서드
서명을 유지한다. S1 Service.login 본문은 보존한다.

관리 진입은 enabled → require_master → 현재 account/roles → 같은 조직/noSelf/지원 대상 → ACTIVE
순서다. 기존 무인증/만료/미충족 assurance는 401, 유효 BA는 403, 조직 밖/본인/미지원 대상은 404,
상태/버전 충돌은 409를 유지한다. 익명 완료의 부적합 source/미지원 대상은 invalid_reset 401이다.
DB 장애를 401로 바꾸거나 CSRF/정상 정책 오류를 입력 오류로 통합하지 않는다.

## API와 최소 화면

| API | 계약 |
| --- | --- |
| GET /api/v1/admin/accounts/{id}/password-reset | account_id/account_version/pending/generation/expiry. raw token 재조회 없음 |
| POST 같은 경로 | expected_account_version>0, expected_generation>=0, identity_confirmed=true. 성공 201 reset_link/expires_at |
| POST 같은 경로 /reissue | pending/기대 버전 검증, 옛 source 소비 후 새 30분 source |
| POST /api/v1/auth/password-reset/complete | reset_token/new_password 및 기존 preauth CSRF. 성공 204·인증 cookie 제거 |
| /reset#token=… | 기존 fragment 제거 및 암호 설정 화면. 자동 로그인 없음 |

기존 Trainer 계정 패널 옆 별도 `[data-trainer-reset]` 영역은 현재 Master에게만 표시하고 조회한다.
BA의 초기 계정 발급/최초 설정과 분리한다. 이미 확인한 연결 account_id만 사용하며 새 계정 디렉터리를
만들지 않는다. 본인 확인 checkbox, 명시 시작/재발급/현재 상태 조회, 발급 응답의 일회성 링크를 제공한다.

기존 latestRead/updateTrainer 보호를 재사용한다. reset 성공 뒤 계정/역할 패널 및 reset 기대 버전을
갱신하고 발급 generation/expiry와 현재 응답이 일치할 때만 링크를 표시한다. 오래된 조회가 새 상태나
링크를 덮지 못하게 한다. I1의 inactive 링크 보류 규칙을 reset에 복사하지 않는다.

409·권한 변경·전송 불확실성에는 링크를 지우고 안전한 GET으로 현재 상태를 다시 읽는다.
명령 자동 재전송/자동 재발급은 없다. GET까지 실패하면 상태를 비활성화하고 재조회를 안내한다.
명시 refresh는 화면의 비밀 링크를 지울 수 있지만 서버 source를 소비하거나 만료를 늘리지 않는다.
완료 화면은 관리자 역할이 있으면 기존 Passkey가 필요하며 계정/역할/Trainer 제한이 유지됨을 안내한다.
익명 응답에 역할 metadata를 추가하지 않는다.

## Actor 기한과 트랜잭션

시작/재발급은 touch=false preflight 종료 → 별도 Security password_reset 슬롯 UoW → 최종
Installation → 정렬 actor/target Account → 정렬 관련 AuthSession → source 순서를 유지한다.
현재 다른 정상 Master가 잠금 아래 확인되므로 A↔B 동시 reset으로 마지막 Master를 잃지 않는다.

최종 business UoW 순서:

1. `authenticate(management=True,target=ident,touch=False)`와 CSRF.
2. 같은 요청의 fresh `RoleActorSnapshot` 생성. preflight snapshot을 재사용하지 않는다.
3. reset 변경 및 필수 typed 감사.
4. `confirm_actor(snapshot,self_change=False,touch=True)`.
5. return 뒤 기존 UoW commit.

TrainerRolesPort.confirm_actor에 `touch: bool=False`만 추가한다. revoked/현재 role epoch/
stable digest의 account/session/roles/live key 읽기를 모두 끝낸 뒤 마지막 DB clock을 읽는다.
원래 idle/absolute 기한과 digest/epoch/철회를 검사하고 성공한 경우에만 그 동일 now로 해당 session의
last_activity를 UPDATE한다. clock 뒤 추가 인가용 DB 읽기나 감사는 없다. 실패는 전체 rollback이다.

기본 touch=False인 W1/I2와 자기 역할 회수는 그대로다. self_change=True와 touch=True의 조합은
SQL 변경 전에 내부 호출 계약 오류로 거부한다. GET reset 상태도 touch=false 인증 → fresh snapshot →
상태 읽기 → 최종 검사 및 touch 순서를 적용하여 기존 성공 활동 갱신 정책을 유지한다.
검사 시점의 기한 보장이며 물리적 COMMIT 완료 순간까지의 기한 보장으로 확대하지 않는다.

시작/재발급은 hash=NULL, pending=true, generation/row/security version을 증가시키고 대상 전 세션과
대기 MFA 증명을 폐기한다. 기존 reset/credential 소비 계약을 유지하며 role epoch/grant/binding,
Passkey/key_set_version/C2, Trainer/Home/보상은 보존한다.

익명 완료는 기존 preauth → 잠금 없는 source/account 검사와 bounded Argon2 → Installation →
target Account → 정렬 sessions → source FOR UPDATE → 현재 source/account/proof 검사 → 암호 저장,
pending 종료, row/security 증가, source 소비, 전 세션 철회, 필수 감사 및 preauth 소비를 같은 UoW로 수행한다.

익명 source expiry는 잠금 획득 후 reset_source의 DB 시각에서 판정한다. 그 뒤 role/proof 검사와
변경/감사가 있으며 source의 외부 소비 가시성은 commit 때 생긴다. hash 또는 잠금 대기 중 만료는
최종 검사에서 거부하지만 감사 이후/물리적 commit 순간의 TTL 보장을 새로 주장하지 않는다.

## 원래 source, 실패, 감사와 보호

| 동시 변화 | 계약 |
| --- | --- |
| W1 off/on | reset source/version/원래 expiry/role epoch 보존. 암호 설정과 현재 로그인 가능 여부 분리 |
| I2 역할 회수/재부여 | 옛 prepared proof는 role epoch로 실패. 원래 미만료 source로 새 준비 가능. 역할 0 접근 차단 유지 |
| 계정 차단/복구 또는 row/security 변경 | 옛 source 무효. ACTIVE pending 복구 후 새 명시 재발급 필요 |
| 재발급/완료/C3 경합 | 잠금 및 version 검증으로 옛 hash/proof가 새 자격을 덮지 못함. 동일 source 완료는 한 번 |
| 만료/GC | 옛 hash/로그인/pending 복원 없음. GC 뒤 expiry=null 가능, 명시 새 재발급만 새 수명 |
| 발급 Master logout | 기존 source 수명과 무관. recipient가 issuer의 현재 세션을 요구하지 않음 |

Security capacity 및 기존 GC/잠금/실패 슬롯 정리를 재사용한다. Account 잠금 안에서 Security guard를
새로 취하지 않는다. raw token/hash/실제 개인정보를 일반 로그나 감사에 저장하지 않는다.
기존 password_reset_start/reissue/complete 및 typed generation/password_ready, actor/target/Scope/row
감사를 유지하며 실패 시 전체 rollback한다. C7 열람 권한은 확대하지 않는다.

실제 commit 뒤 ACK 유실은 기존 commit_outcome_unknown 503이며 자격을 되돌리지 않는다.
상태 조회 및 명시 재발급으로 전달 불확실성을 해결한다. 새 operation 테이블/receipt/복구 endpoint는 없다.
0007의 계정/source 스키마가 Trainer 연결 계정도 수용하므로 새 migration은 없다. 기존 migration과
보호된 하향 제약의 바이트는 보존한다.

## 인증 입력 오류 비노출

실제 malformed 요청에서 repr/hide_input_in_errors만으로 FastAPI 응답 input이 숨겨지지 않음을 확인했다.
인증 prefix `/api/v1/auth/`의 RequestValidationError만 `422 {detail: invalid_request}`로 통일한다.
업무 API의 기존 오류와 인증 401/403/404·CSRF·DB 장애 의미는 유지한다. 합성 marker를 사용한 실제
HTTP 타입/길이/extra 오류에서 원문 부재 및 DB/budget 무변경을 확인한다. 전체 운영 로그 검증을 뜻하지 않는다.

## 검증과 완료 경계

개발 검증은 실제 W0/I1→reset→새 로그인, state/grant/admin/Home 조합, 현재 Actor·MFA 음성 대조,
원래 source/proof·W1/I2/C3/동시 완료, 감사/실제 ACK/GC, 마지막 기한·정확한 touch, 입력 비노출,
Master UI·BA 미조회·응답 유실 대사 및 기존 native 54항목 유지에 집중한다.
가상 now 순서 검사는 실제 PostgreSQL 기한 경과 검사와 구분한다. 경합 probe는 새 touch=false 계약에서
실제 main 진입을 동기화하고 기존 결과 단언을 유지한다. 실행 수와 실패 원인은 별도 결과에 기록한다.

독립 담당자의 보완 causal 파일과 개발자 변경을 합친 뒤 모든 쓰기·runtime 종료 후 한 번 동결한다.
실제 delta/정확한 node/coverage로 독립 범위를 선정하며 전체 576개 자동 반복이나 운영 인수로 확대하지 않는다.
독립 테스트 → 설계자 검토 → 전담 한글 커밋·일반 feature push는 후속이다.
