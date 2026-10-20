# IAM-009 구현·독립 검증·설계자 인수 결과

2026-10-20. **제한된 AB5 로컬 개발 인수 PASS. 독립 전체 검증·설계자 검토 완료.**
기준 HEAD는 `3e8ad3a363d28a2bdf469bb8a896074ef480f977`, 브랜치는
`codex/iam-emergency-recovery`다. [계약](iam-009-emergency-recovery-design.md)과
[AB5 R1–R3](../product/product-decisions.md#review-20261020-ab5-r1-r3)의 제한된 개발 범위다.

## 구현한 동작

기존 ACTIVE·현재 Master 한 명의 비밀번호/Passkey/both 복구를 별도 OS 운영 권한으로 실행한다.
보호 descriptor와 별도 strict request, 실제 UID/EUID, 기존 전용 DB 소유권·ProcessGuard,
현재 snapshot·명시 승인 만료·새 operation/승인 참조를 검사한다. inspect/status는 읽기만 수행한다.
execute-only 권한은 inspect 권한을 추가하지 않고 실행하며 inspect-only는 실행할 수 없다.

발급은 대상 세션·대기 권한과 승인 요인만 철회한다. 다른 요인·다른 계정·C2를 보존하고
AB5 allocation/release는 전역 GC를 호출하지 않는다. 수신자는 전용 실제 화면에서 승인 요인을
준비하며, both는 임시 context의 hash와 실제 UV 검증 뒤 한 UoW로 두 요인을 완료한다.
자동 로그인 없이 정상 비밀번호+UV로 다시 로그인한다. 철회된 cookie를 유지한 재로그인도 검증한다.

신규0008은 영속 사건과 일시 source를 분리하고 사건/대상/요인의 FK, context purpose/hash 제약,
최대5분 context와30분 source, typed audit의 필수 metadata를 적용한다. 재발급의 직전 사건은
벽시계가 아닌 증가하는 account row_version으로 선택한다. source GC 뒤에도 소비한 operation과
승인 참조는 남으며 사건/감사 이력이 있는 downgrade는 거부한다. 기존0001–0007은 변경하지 않았다.

보호 출력의 작성/fsync 실패는 업무 rollback과 자기 파일 제거로 처리한다. COMMIT 결과 불명,
확인된 commit 뒤 receipt/정리 실패는 구분하여 파일을 보존하고 exit2/status 확인을 요구한다.
UoW의 commit 경계를 관찰하므로 실제 commit 직후 KeyboardInterrupt/SystemExit도 실행 전 실패로
단정하지 않는다. stdout/stderr는 실제 pipe 실패가 인터프리터 종료 단계에서 분류를 덮지 않도록
버퍼 없이 전달한다. Bootstrap의 동작은 변경하지 않았다.

## 독립 검증과 설계자 판정

개발자가 멈춘 동결183개 소스에서 별도 담당자가 `bash check.sh fast`와 `bash check.sh db`를 새로 실행했다.
fast105개와 PostgreSQL **전체364개(신규37+기존327)**가 모두 통과했다. 실패·skip·xfail·xpass·error·미완료는0이다.
PG는 하나의 최종 소스 전체 실행이며 개발자37/40개 표적 검사나 이전 증분 결과를 합친 인수가 아니다.
같은 PG 실행 `auto-8cc6340c52214db88b1f18bc749c915a`의 Chromium `151.0.7922.34`에서
기존58/20/15/11/12 및 신규23개 exact manifest 항목139개가 모두 literal true였다.
실제 HTTPS chain/hostname·sandbox 검증과 전역 trust 불변을 확인했다. 브라우저 pytest3건은364개 안에 포함된다.

설계자는 최종 계약·CLI/UoW의 commit 관찰 경계·실제 commit 후 인터럽트/OS pipe 검사와 네 finding의 수정,
새0008 잠금 순서 수정·검증 결과를 대조해 인수했다. 인터럽트 사례의 durable case/출력 보존과 같은 UoW의 철회 원자성
근거를 구분하며 모든 실패 조합이 각각 모든 인증 행을 비교했다고 주장하지 않는다.
소스183개·보호72개(승인된 정책7개와 정확한 import 계층1개는 HEAD 차이 허용)·HEAD/index는 실행 전후 일치했다.
자동 pytest/출력 수집 환경4개의 자기 프로세스·schema·profile·TLS·보호 파일·실행 폴더 정리를 확인했다.
미정리/새 finding은 없고 기존 경고2개는 유지한다. [최소 설계자 근거](iam-009-emergency-recovery-review.json)를 보존한다.
root는 자료와 소스를 검토했으며 별도로 테스트를 실행하지 않았다. 실제 운영/실물/전체 브라우저 인수는 아래 한계를 따른다.

## 개발자 표적 검증 이력

아래는 독립 진입 전 개발 시점의 검사다. 최종 전체 검증은 위의 별도 독립 결과를 따른다.

| 검사 | 최종 상태 |
| --- | --- |
| Ruff/format/mypy | 통과 |
| DB 없는 pytest | 105 passed |
| Import Linter | 7 kept / 0 broken |
| 신규 emergency PostgreSQL·실제 HTTPS | 37 passed |
| 기존 HTTPS·MFA security·GC·reset storage 표적 회귀 | 40 passed |
| 전체 수집 | 469개: DB 없음105 / PostgreSQL364 |

수집은 실행이 아니다. collection-only는 필수 PostgreSQL no-pass 게이트 때문에 exit1이며
이것을 실행 성공이나364개 PostgreSQL 통과로 보고하지 않는다. 개발자는 전체 PostgreSQL 독립
회귀를 수행하지 않았다. 최종 소스 동결 뒤 필요한 별도 독립 실행과 설계자 인수는 위 결과로 완료했다.

신규 검사에는 실제 준비된 계정의 세 요인 복구, normal pending에서 승인 부족 거부,
실제 UV 후 재발급 경합, 부분 완료/감사/DB 실패 rollback, 타 계정·C2 불변, 잠긴 context의 GC,
migration 왕복/이력 보호, 보호 파일·실제 CLI·단독 operation 권한, 실제 commit 뒤 응답/정리/인터럽트
실패 및 닫힌 OS 파이프가 포함된다. UI 검사는 TestClient와 별도로 신뢰 HTTPS Chromium에서 실행한다.
각 CLI 발급은 검사 소유 웹만 중지→실제 CLI→같은 서버 재기동하며 기존 native manifest는 보존한다.
Chromium `151.0.7922.34`에서 신규 세 분기23개와 기존58/20/15/11/12개 항목이 모두 true다.
37건과40건은 각각 실행한 표적 묶음이며 전체364건 PostgreSQL 회귀 인수로 확대하지 않는다.

증거는 ignored `.local/qa/iam-emergency-recovery-184c0caf1b644cbc/`에 둔다.
최종 로그·수집 목록·manifest·개발 결과와 초기 실패/수정 근거를 함께 남긴다. 최종 fast·신규PG/native·기존PG/native·수집
네 실행 모두 기존 fixture가 자기 프로세스/schema/profile/실행 폴더를 정리했고 removed=true다.
미정리 항목은 없다. 최종 검증 시작 이후 backend112개 파일 hash가 일치함을 확인했다. 원본 secret과 승인 원문은
인계 결과에 포함하지 않는다. 기존 Starlette HTTPX/AnyIO 경고2개는 유지한다.

## 발견·수정 이력

- 초기 native 검사는 테스트 child_env의 고정 origin 때문에 잘못된 포트의 복구 링크를 열었다.
  새 CLI 시험 보조 함수에 실제 검사 origin을 전달하도록 수정했고 세 UI 분기가 통과했다.
- 새0008 downgrade의 security_states→accounts 잠금이 기존 fingerprint 조회와 교착했다.
  실제 PostgreSQL에서 재현했고 새0008의 계정 우선 순서로 수정했다. 기존 재설정 저장 검사와
  새 migration 왕복/이력 보호16건이 수정 후 통과했다. 기존 migration/시험을 완화하지 않았다.
- 설계자 정적 검토의 감사 NULL 허용, 시각 기반 직전 사건 선택, execute에 inspect를 요구하는
  문제를 수정했다. NULL DB 제약·같은 시각 사건·실제 operation별 권한 검사로 확인했다.
- commit 이후 stdout/flush/정리/인터럽트가 알려진 사전 실패로 분류될 수 있는 경계를 보완했다.
  실제 commit 뒤 실패 주입 및 닫힌 OS pipe12건이 통과했다. 단순 mock 결과로 DB 효과를 대신하지 않았다.

## 남은 범위

수동 원본 확인은 승인 진위·별개 인간·모든 Master의 실제 접근 불가를 자동 증명하지 않는다.
비특권 test authority는 실제 운영 OS 분리의 증거가 아니며 production은 계속 거부한다.
실제 운영 담당자/권한 provision, 보존·열람·삭제, 배포, 실물 인증기와 전체 지원 브라우저 인수는 남아 있다.

both 발급·링크 만료 후 다른 정상 Master가 복귀한 경우의 정상 관리자 인계는 R4 별도 후속이다.
이번 구현은 normal M2/reset의 opposite-pending 거부를 완화하거나 과거 all-unavailable 확인을
새 승인으로 재사용하지 않는다. IAM-009의 제한된 핵심 복구와 전체 운영 AB5 완료를 구분한다.

전담 커밋 세션의 최종 변경 검토·한글 상세 커밋·일반 push 절차를 따른다. R4는 사용자1번 승인을 받았고
이번 인수와 커밋 뒤 별도의 정상 Master 인계 계약·구현·검증으로 진행한다.
