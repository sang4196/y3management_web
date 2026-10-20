# IAM-009 — 제한된 AB5 비상 인증요인 복구

2026-10-20. Product의 [AB5 R1–R3 승인](../product/product-decisions.md#review-20261020-ab5-r1-r3)과 설계자 기술 검토에 따른 구현 계약이다. 구현·독립 검증 완료 또는 운영 개시 승인을 뜻하지 않는다.

## 범위와 권한

기존 ACTIVE·현재 Organization Master 한 명의 승인된 비밀번호, Passkey 또는 두 요인만 복구한다. DISABLED 복원, PENDING_SETUP, 신규 계정, 회수 역할 복원, 다른 계정 철회는 제외한다. 기존 M2/reset, C3와 C2 제한을 유지한다. 일반 웹 Caller나 AuthSession을 만들어 운영 권한을 흉내 내지 않는다.

`OperatingRecoveryAuthority`는 실제 Linux UID/EUID 일치와 신뢰된 배포 설정의 권한 descriptor를 통해 환경·DB·schema·organization·허용 operation을 한정한다. USER 환경변수, CLI 실행자 문자열, 승인 입력 파일은 권한 근거가 아니다. 운영 descriptor는 root 소유이며 파일과 경로가 symlink 또는 비소유자 쓰기를 허용하면 거부한다. test 전용 descriptor는 fixture UID 소유를 검증하지만 실제 운영자의 OS 분리 증거가 아니다. 미구성은 거부하고 production은 계속 금지한다. 실제 /etc 설정이나 운영자 provision은 수행하지 않는다.

운영자는 업무책임자의 현재 권한, 원본 승인·취소·유효기간·요인 범위, 대상 본인/수신 가능 여부 및 모든 Master의 정상 경로 이용 불가를 기존 독립 확인 경로에서 확인한다. 시스템은 참조와 확인자·확인 시각을 기록한다. 문자열 차이, 파일 hash 또는 승인 boolean은 승인 진위나 서로 다른 사람의 증명이 아니다. 지원하지 않는 추가 승인 조건은 수동 범위 조정 전 실행을 거부한다.

## 운영 명령과 파일

`emergency-recovery inspect/execute/status`는 MFA test/development, TTY, 기존 전용 Compose DB 소유권 검증, database/schema/org 확인, 실제 DB identity 대조 및 ProcessGuard를 요구한다. 기존 웹이 guard를 보유하면 거부한다. 운영 절차는 웹 중지→CLI 실행→CLI 종료→웹 재기동이며 자동 강제 종료는 없다.

inspect는 current state/grant/row/security/keyset/reset/recovery generation, pending와 요인 준비 여부만 반환한다. execute는 보호된 JSON request의 operation ID, 대상, DB identity, 전체 현재 snapshot, 요인, target_only 범위, 승인 참조/책임자 참조, 수동 확인 시각, 명시적 approval_valid_until을 검사한다. status는 사건의 issued/completed/superseded/stale/expired 상태만 읽는다. 조회는 GC, 세션 touch, token 반환을 하지 않는다.

입력은 절대 경로, symlink 없는 경로, 현재 UID의 0700 부모와 0600 regular 단일 hardlink 파일, bounded JSON, 중복 key/extra 필드 거부를 적용한다. 권한 descriptor 경로는 배포 설정이며 request/CLI로 대체하지 않는다. 출력은 O_EXCL·0600, 부모0700, fd/inode 확인과 file/directory fsync를 적용한다. `/emergency-recover#token`만 파일에 쓰고 stdout/log에는 secret을 출력하지 않는다.

출력은 DB commit 전 작성한다. 알려진 실패는 rollback 후 자기 inode 출력만 삭제한다. 실제 COMMIT 결과가 불명하면 exit2로 출력을 유지하며 status로 확인한다. commit 확인 후 receipt write/flush 또는 출력·DB·guard 정리 실패도 exit2와 status 확인 대상으로 처리한다.
이때 confirmed commit과 COMMIT 결과 불명을 구분하며 stderr 전달 실패가 종료 분류를 바꾸지 않는다.
CLI는 UoW의 commit 시작/확인/명백한 제약 거부 경계를 관찰한다. 실제 commit 직후
KeyboardInterrupt/SystemExit가 발생해 확인 callback에 도달하지 못해도 결과 불명으로 파일을 보존한다.
두 자원의 원자성을 주장하지 않는다. commit 확인 전 링크를 전달하지 않는다. 전달 실패·출력 유실은 인증 철회를 되돌리지 않는다. 재발급은 새 operation, 새로 확인한 승인 참조, 최신 snapshot과 명시적 supersedes를 요구한다. 기존 operation 재실행이나 token 재조회는 없다.

## 요인 상태와 수신자

| 승인 요인 | 발급 조건/효과 | 수신자 최종 완료 |
| --- | --- | --- |
| password | recovery_pending=false, active key 존재. hash=NULL, reset_pending=true, reset_generation++, row/security++ | bounded hash 준비 후 최종 current 검사, hash 저장/reset_pending=false, row/security++ |
| passkey | hash 존재, reset_pending=false. 옛 active key tombstone, recovery_pending=true, recovery_generation/keyset/row/security++ | 실제 UV 등록 검증 후 새 key 저장, recovery_pending=false, keyset/row/security++ |
| both | 두 요인 승인. 위 두 발급 효과를 한 UoW로 적용 | 새 hash는 임시 context에만 보관. 실제 UV 후 hash+key와 두 pending 해제를 한 UoW로 완료 |

승인 밖 요인이 미준비이면 409로 거부하며 범위를 자동 확대하지 않는다. 발급은 대상의 모든 세션 및 setup/login/add/reset/recovery/emergency 대기 권한만 철회한다. 승인 밖 요인, 타 계정의 만료 자료까지 포함한 인증 행, C2 budgets/attempts/cooldowns는 유지한다. 비교는 후속 정상 UI 요청 전 명령 경계에서 수행한다.

전용 수신자 UI는 fragment를 즉시 제거한다. preauth+CSRF가 있는 inspect, password/complete, options, verify 경로만 사용한다. source는 30분 단회, 등록 context는 기존 최대5분과 source 만료 중 이른 시각이다. options 재시도는 source 수명을 연장하지 않으며 이전 같은 source context/hash를 소비한다. 승인 유효기간은 별도 명시 값으로 발급 시 검사하며 30분으로 추정하지 않는다.

password-only는 실제 hash 준비 이후, passkey/both는 실제 WebAuthn UV 검증 이후 최종 잠금 안에서 현재 Organization/ACTIVE/Master, source/case, 전체 epoch/generation을 재검사한다. 실패·만료·감사 실패로 부분 요인 완료가 생기지 않는다. 정상 목적 token과 양방향 교환을 거부하며 기존 cross-pending 차단은 유지한다. 완료는 자동 로그인하지 않는다. 철회된 cookie를 유지한 상태에서도 별도 정상 비밀번호+UV 로그인을 진행한다.

## 저장, 잠금과 감사

기존0001–0007을 보존하고 forward0008에서 영속 `iam_emergency_cases`와 bounded `iam_emergency_credentials`를 분리한다. operation과 조직 내 승인 참조는 unique이며 source GC 이후에도 사건/소비 참조를 유지한다. context의 emergency source FK와 purpose/hash 제약을 추가한다. 새 account readiness flag는 없다.

발급/최종 완료의 순서는 Installation→대상 Account→대상 AuthSessions(ID순)→Passkeys(key_id순)→대상 sources(activation,recovery,password_reset,emergency 순)→contexts(ID순)이다. 같은 대상의 기존 경로는 Account 잠금으로 직렬화한다. GC는 SKIP LOCKED로 부모를 잡은 뒤 새 statement snapshot에서 자식 존재를 재검사한다. release/orphan의 NOT EXISTS에도 새 source를 포함한다. 사건·감사는 GC하지 않는다.

hash/WebAuthn/입력파일 검증과 capacity 확보는 업무 잠금 밖에서 수행한다. AB5 allocation/release/completion은 전역 GC를 호출하지 않는다. capacity 부족은 다른 계정 자료를 제거하지 않고 실패한다. 전역 slot bookkeeping과 계정 인증 행의 보존은 구분한다.

issue/complete typed audit는 같은 UoW로 rollback한다. 운영 actor account는 NULL, role은 SYSTEM_RECOVERY_OPERATOR, scope는 EMERGENCY_RECOVERY이며 실제 실행자 참조와 case/factors 및 전후 epochs/generations/readiness를 기록한다. 수신자는 대상 account와 RECOVERY_RECIPIENT로 기록한다. 가짜 Master actor, 임의 JSON payload, 원본 승인/암호/hash/key/token은 기록하지 않는다. 영속 사건/신규 감사가 있는 downgrade는 거부한다.

## 검증과 인계

기존 fixture와 소유권 확인된 전용 DB를 사용한다. 보호파일/권한, 세 요인 및 pending 조합, current grant/epoch, 실제 crypto 뒤 경합, 대상 외 행/C2 불변, audit/DB/file 실패와 COMMIT ACK 불명, source/context GC/FK, migration 제약 및 실제 HTTPS UI를 검사한다. 기존 native manifest는 수정하지 않는다. 테스트 출력은 ignored 고유 QA 폴더의 최소 결과만 남기고 자기 프로세스/schema/profile을 정리한다.

개발자 표적 PG/native와 최종 fast/collection 후 source manifest를 동결하고 결과를 남긴다. 독립 전체 회귀와 설계자 인수는 별도다. 실제 운영 담당자/접근 통제/보존·삭제/배포/실물 및 전체 지원 브라우저 검수는 남아 있다. 구현 결과는 별도 결과 문서에 실제 수행 범위로 기록한다.

## 별도 후속: 복구 중 정상 관리자로의 인계

both 발급 후 링크가 만료된 사이 다른 정상 Master가 복귀한 경우, 사용자는 그 Master가 기존 사건을 이어받아
필요한 링크를 재발급하는 R4=1을 승인했다. 구현·검증은 IAM-009 인수·커밋 이후 별도 증분이다.
현재 정상 M2/reset의 opposite-pending 거부와 운영 원본의 현재 all-unavailable 확인을 유지한다.
이 조합을 처리하려고 정상 경로를 완화하거나 이전 수동 확인을 새 실행의 승인으로 재사용하지 않는다.
IAM-009의 세 요인 복구·현재 조건 아래 명시 재발급 인수와 이 인계 기능의 완료를 구분한다.
