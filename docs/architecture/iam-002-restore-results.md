# IAM S2a — Branch Admin 일반 차단 해제

2026-10-14. 상태: **IAM S2a 제한된 로컬 개발 인수 PASS**. 개발 결과, 독립 검사와 설계자 재검토를 대조했다. S2 전체/운영 복구 완료가 아니다.

## 범위와 승인

A8의 같은 Organization Master 전용 계정 복구, E6의 유효 기존 암호 재로그인,
C1의 추가 관리 비밀번호 재확인 없음, C2의 독립 로그인 실패 제한을 적용한다.
근거는 [Product 결정](../product/product-decisions.md), [F01](iam-001-decision-pack.md),
[S1 인수](iam-001-s1-review.json)다. 2026-10-14 설계자 지시로 이 좁은 범위를 승인받았다.
추가 Master 발급 Actor의 적용 해석은 별도 검토하며 이번에 구현하지 않는다.
reset/본인 암호·ID 변경, Master 차단·강등/비상 복구, Trainer/Operator 업무,
MFA/운영 배포는 포함하지 않는다. 기존 Product/ADR/OPEN 상태는 변경하지 않았다.

## 동작

`POST /api/v1/admin/accounts/{id}/restore`는 `{expected_version}`을 받고 기존 Account DTO를 반환한다.
현재 Master·자기 Organization Branch Admin·DISABLED·version을 잠금 안에서 확인한다.
PENDING_SETUP/ACTIVE 및 version 불일치는 409, 타 조직/없는 대상/Master는 404,
비Master는 403이다. 기존 Origin/JSON/CSRF 방어를 사용한다.

성공하면 ACTIVE로 바꾸고 두 version을 전진시키며 같은 UoW에 `account_restore` 감사를 기록한다.
기존 password_hash·Login ID·관리 Branch는 유지한다. 폐기된 AuthSession/credential을
되살리거나 새 쿠키를 발급하지 않는다. 기존 유효 암호로 새 로그인해야 하며
대상의 실패 budget/cooldown과 실행 Master의 인증은 유지한다.
감사 실패는 복구까지 rollback한다. commit 응답 유실은 503을 반환하고 실제 커밋을 되돌리지 않는다.

Installation→정렬된 Account→정렬된 AuthSession→credential 잠금 순서를 재사용한다.
복구 중 로그인은 세션 정리의 Account 잠금에서 대기할 수 있고 커밋 후 새 상태로 인증한다.
이 경로를 잠금 없이 옛 DISABLED snapshot을 읽는다고 가정하지 않았다.

## 변경 파일

- `backend/src/y3management/iam/public.py`: restore 공개 계약.
- `backend/src/y3management/iam/infrastructure.py`: DISABLED→ACTIVE 전이.
- `backend/src/y3management/use_cases.py`: 현재 인가/version·잠금·감사 원자 조합.
- `backend/src/y3management/http.py`: 명시적 restore endpoint.
- `backend/alembic/versions/0002_iam_restore.py`: audit action 제약만 확장. 기존 0001은 보존.
- `backend/tests/test_iam_s2.py`: 별도 실제 PostgreSQL 인수 검사.

0002 downgrade는 restore 감사가 있으면 제약 복원이 실패하며 트랜잭션 전체가 rollback된다.
기존 감사를 삭제해 downgrade하지 않는다. restore 감사가 없는 경우 0001 왕복은 허용하며
계정·권한·예약 ID·credential·감사를 보존한다. 운영 downgrade/백업 복구 절차의 검증은 아니다.
IAM 구현에서 의존성·lockfile·DB 설정은 변경하지 않았다. 기존 pytest/browser 실행 자료 정리는 별도 QA 작업으로 적용했다.

## 개발 검증과 증거

최신 기계 판독 판정과 6개 구현/검사 파일의 SHA-256은
[설계자 인수 요약](iam-002-restore-review.json)에 기록했다.
완료된 private 실행 폴더와 원본 로그는 사용자 보존 정책에 따라 정리했다.
가상 데이터로 검사했으며 비밀값은 결과 문서/JSON에 복사하지 않는다.

- fast: 58 passed / 25 deselected, Ruff 통과, mypy 39 source files 통과, Import Linter 7 kept.
- S2 실제 PG: HTTP 복구/옛 쿠키/기존 암호/Scope·권한·상태·version·CSRF,
  감사 rollback/commit ACK 유실, cooldown 보존, 독립 연결 PG blocking 두 사례,
  migration 데이터 보존/감사 존재 시 downgrade 실패를 검사한다.
- 개발 과정의 오류는 로그인 경합에서 GC 잠금 대기를 놓친 테스트 가정과
  Account DTO의 중첩 Branch 경로를 잘못 읽은 테스트였다. 앱 로직 변경 없이 검사를 바로잡았다.
- 개발 담당자의 실행에는 실제 HTTPS 브라우저 인수가 포함되지 않았다.
  아래 독립 검사의 실제 브라우저 결과를 별도로 대조했다.
- pytest의 기존 HTTPX TestClient / AnyIO BlockingPortal 경고 2개는 유지한다.

전체/대상 실행의 정확한 수집·성공 수치와 최종 상태는 아래 최종 결과에 기록한다.

## 최종 실행 판정

현재 S2 구현 6개 파일의 freeze manifest와 실제 내용이 일치한다. PostgreSQL 선택 검사
24개 통합 실행은 **23 passed / 1 failed**였고, 실패 원인은 새 테스트의 중첩 응답 경로였다.
그 1개를 수정한 대상 재실행은 **1 passed / 6 deselected**다. 두 실행으로 선택한 24개 사례의
성공을 확인했으며 단일 실행 24 passed 또는 브라우저 포함 전체 DB 통과로 표기하지 않는다.
S2 사례는 7개, S1/기반 회귀는 17개다. 수정 후 Ruff와 mypy39도 통과했다.
추가로 최종 경합 대상 실행은 2 passed / 5 deselected다. skip/xfail은 없다.

위 수치는 개발 담당자의 실행 이력이다. 독립 검사는 필수 PostgreSQL 실행에서
**24 passed / 1 failed**였으며 S2 7개와 S1/기반 17개가 통과했다. 실패한 실제 브라우저는
길어진 TMPDIR의 Unix socket 경로 제한이 원인이었다. 소유한 호스트 실행 폴더를
브라우저 namespace의 `/tmp`로 연결해 수정한 뒤 해당 검사만 **1 passed**로 재검증했다.
총 25개 DB 사례의 성공을 여러 실행에서 확인했으며 단일 실행 전체 DB 통과로 보고하지 않는다.

실제 신뢰된 HTTPS·Chromium sandbox 검사에서 기존 S1 25개와 복구 6개, **31개 필수 항목**이
모두 참이었다. 차단 전 두 장치의 실제 로그인 성공·유효한 서로 다른 쿠키를 먼저 검증해
차단/복구 후 옛 인증이 되살아나지 않는다는 근거를 보완했다. README 서식 게이트도 바로잡았다.
최종 독립 `bash check.sh fast`는 **68 passed / 25 deselected**, Ruff 검사/서식,
mypy 40개 파일 및 Import Linter 7개 계약 통과다. skip/xfail을 성공으로 계산하지 않았다.

설계자 재검토에서 민감한 DB 행 비교의 실패 출력 가능성도 보완했다. 모든 필드의 동일성 검증은
유지하면서 실행별 임시 키의 지문만 비교하고, 가상 인증정보의 출력도 가렸다.
영향받은 실제 PG 2개를 재검증했으며 의도한 실패를 `--showlocals`로 발생시켜
원문 canary가 출력되지 않음을 확인했다. 이 변경은 테스트만 수정했고 앱/migration은 유지했다.

독립 검사는 실행 폴더·테스트 schema·자체 프로세스·포트·인증서/브라우저 프로필 정리를 확인했다.
기존 DB·공유 서비스·전역 인증서 저장소는 유지했다. 인수는 단일 WSL 호스트/worker 1의 개발 범위이며
reset/본인 암호·Login ID 변경, 추가 Master, MFA/비상 복구, Workforce 및 운영 준비는 후속이다.
