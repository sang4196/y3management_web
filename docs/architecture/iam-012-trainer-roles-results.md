# IAM-012 기존 계정 Trainer 역할 검증 결과

2026-10-30. **새 단일 전체 검증·설계자 로컬 인수 PASS**.
[승인 정책](../product/product-decisions.md#review-20261030-i2)과
[제한 계약](iam-012-trainer-roles-design.md)에 따른 구현이다.
기준 HEAD는 `08f2ef5a26fbe8f91058bf3767efe4b1b382d1a5`, 작업 브랜치는
`codex/iam-trainer-roles`다. 이 판정은 커밋 전 동결 소스 기준이며 전담 변경 검토·한글 상세 커밋·일반 feature push 절차를 따른다.

## 구현

불변 일대일 binding과 현재 Trainer grant를 분리했다. 최초 연결·회수·같은 연결 재부여의 실제
전이는 role version/epoch만 증가시키고 대상 전체 세션·MFA context·Trainer 초기 source를
무효화한다. 계정 상태·암호·row/security version·독립 관리자 grant·Passkey는 유지한다.
현재 E5/실제 Home, 첫 연결 ACTIVE/login-ready+명시 동일인 확인, 재부여 ACTIVE/PENDING_SETUP,
활성 Trainer 조건을 적용한다. 회수는 대상 상태와 무관하며 무역할 계정의 로그인은 거부한다.

정확 Login ID 후보 조회, 역할 상태·작업 영수증 조회, typed 감사와 원자적 역할 전이를 추가했다.
no-op/replay/status는 새 로그인 철회나 새 링크 발급을 하지 않는다. 자기 세션 철회는 원래 Actor의
독립 권한·키·세션 snapshot과 기대 epoch 전이를 확인하고, 모든 조회 후 DB clock으로 원래 idle/
절대 기한을 재검사한다. 별도 target account/state/security와 Workforce 사실도 감사 후 확인한다.

관리자 장기 reset/recovery/emergency source의 원래 버전·세대·기한을 보존하고 transient context와
준비된 proof에는 role epoch를 적용했다. 같은 유효 장기 source로 새 ceremony를 시작할 수 있다.
I1 초기 발급도 binding+grant+epoch를 한 UoW에서 만든다. 기존 S1 `Service.login` 본문은 보존했다.

UI는 역할 변경 후 계정 panel·초기 링크 표시와 재발급 가능 여부를 함께 갱신한다. 폐기된 링크는
제거하고 회수 중 재발급을 차단한다. 재부여 뒤 새 링크는 명시적으로 발급한다. 작업 UUID는 제출
전에 표시하며 재로그인 후 수동 입력으로 원래 영수증을 조회할 수 있다. 다른 Trainer의 번호는
현재 카드의 결과로 표시하지 않는다. 자동 mutation 재전송은 없다.
공용 MFA 로그인 화면은 viewport와 기존 stylesheet를 적용했다. 실물 모바일 인수는 아니다.

## 독립 전체 검증과 설계자 인수

독립 fast **131개**, 새 단일 PostgreSQL **전체541개**(기존499+신규42)를 통과했다.
서로 다른 pytest 사례는672개다. 같은 PG 실행의 실제 신뢰 HTTPS/native10개 manifest
**247항목**(기존211+신규36)은 모두 literal true이며 브라우저 pytest7건 안의 항목이다.
실패/error/skip/xfail/xpass/incomplete·누락/중복·비사례 오류는 모두0이다. 실제 bash/pytest exit0을
XML 분석 전에 저장했고, 설계자가 실제 XML·정확한 node 집합·개별 passed와 같은 실행의 native를 대조했다.

동결238개/Backend155개·보호200개·HEAD/index와4개 전역 신뢰 파일의 전후 일치를 확인했다.
설계자 후속 변경은 이 결과·계약/단계/검증 문서와 [영구 최소 판정](iam-012-trainer-roles-review.json)뿐이며
테스트한 Backend155개 바이트는 유지한다. 자동 실행의 제거 receipt·실제 경로 부재를 대조했다.
관찰538개 schema/558개 process identity 및 owner의 잔존 없음은 기존 전체 fixture 정리를 보충하며
관찰 목록을 전체 자원 목록으로 주장하지 않는다. 공유 Compose DB/서비스/볼륨과 원본은 보존했다.

아래 개발 대상·분할 검사와 초기 실패는 당시 이력이다. 완료된 QA 원본 로그/XML/캡처/seed 복제본은
최소 판정으로 축약한 뒤 정리할 수 있으며, 과거 임시 경로 참조가 영구 보존 사유는 아니다.

## 개발 검증 근거

QA 경로는 ignored `.local/qa/iam-trainer-roles-d0db5a92e51c420b/`다.
당시 실행별 수치·수집 목록·소스 raw SHA는 `developer-result.json`, `case-inventory.json`,
`source-frozen.json`에 기록했다. 보존할 최종 실행·개별 중요 판정·Backend raw SHA는 위 영구 최소 판정을 따른다. 추가 검사 파일·Import Linter 설정을 포함하는 마지막 fast는
Ruff/format/mypy102·pytest131·Import Linter8 통과다.

신규 PG는 기존 역할 대상32 + epoch downgrade2 + native1 + 첫 binding/DDL 경합3 +
전담 추가 proof/credential 경합4의 서로 다른42개를 검증했다. 전담 추가4개도 제한 대상 실행이며
독립 전체 검증 인수는 아니다. 기존 보호 대상23 + 원래 S1 회귀3 + 기존 I1 native1의 서로 다른27개도
통과했다. 이는 분할 대상PG69개이며 단일 전체PG 통과가 아니다. 실제 최종 수집은 총672개,
비PG131/PG541(기존499+신규42), native10개 manifest247항목(기존211+신규36)이다.
이번 개발의 native는 신규36+기존I1 23=59항목이다. 나머지는 독립 전체 실행 대상이다.
collect-only의 기존 PG 미실행 guard exit1은 수집 확인이며 실행 통과가 아니다.

- 신규 핵심 lifecycle 3개, 상태/버전/rollback 대상 11개, 최종 조회 지연 후 idle/절대 만료 2개를 확인했다.
- 현재 Home/BA scope, 독립 관리자 source 보존, 실제 PG 잠금 대기, COMMIT ACK 유실 후 replay,
  오래된 password login proof 차단 7개를 확인했다. 대상 모든 세션·대기 UV context·다른 계정/C2 보존과 준비된 reset proof 거부도 최종 대상 실행에서 확인했다.
- 실제 신뢰 HTTPS Chromium `151.0.7922.34`: 신규 역할 manifest 36항목과 기존 I1 23항목이 모두 true.
  브라우저 pytest 2개 안의 항목이며 별도 pytest 사례 수에 합산하지 않는다.
- 본인 실제 commit 후 응답 drop → 기존 세션401 → 정상 UV 로그인 → 원래 작업 UUID 조회 →
  새 세션 유지, 역할 회수 후 초기 링크 제거/재발급 차단 → 재부여 → 명시 새 링크 설정/로그인을 확인했다.
- 기존 S1 COMMIT ACK의 committed child 보존 및 관리 요청과 login/setup 잠금 대기 3개를 확인했다.
- 첫 연결의 같은 Trainer/다른 계정 및 같은 계정/다른 Trainer 경쟁에서 서로 다른 실제 Actor와
  PG blocker를 확인하고 정확히 한 쌍·전이·영수증·감사만 남겼다. 실제 I2 역할 transaction을 기다린
  downgrade가 commit 후 이력을 보존하고 거부함도 확인했다.
- 전담 추가 파일에서 실제 UV 검증 완료 proof와 Trainer 초기 hash proof 뒤 역할 회수/재부여 commit을
  확인했다. 옛 완료는 거부되고 새 흐름은 성공했다. 초기 링크 재발급↔회수는 양방향 순서의 실제
  PID 차단과 성공/충돌·원자성을 확인했다. 정확한 사례와 경계는 `coverage-map.json`을 따른다.
- 원래 0011 코드의 실제 API로 활성 Trainer 세션과 미설정 source를 준비했다. 보존된 HEAD archive는
  **이전 상태 seed 전용**이며 검증 대상은 현재 0012 migration과 현재 앱이다. upgrade/backfill은
  기존 모든 account/session/context/source 컬럼을 보존했고 pure-backfill downgrade/upgrade 후
  기존 세션 인증과 초기 source 설정이 성공했다. epoch 정보를 잃어 인증을 되살리는 downgrade는 거부한다.

기존 보호 migration/manifest/assertion을 변경하지 않는다. 기존 테스트 5파일의 7곳은 실패한
하향 migration 후 유지되는 head literal만 0011→0012로 갱신했다. Import Linter는 새 IAM roles adapter의 직접 참조 금지를 명시했다. 의존성 버전/lockfile은 유지했다.
공용 브라우저 helper에는 새
선택 flag와 manifest/최소 결과 파일 분기만 추가하며 기존 모든 판정과 cleanup 절차를 유지한다.
이전 I1 전체PG499/native211 결과를 새 증분의 독립 전체 통과로 재사용하지 않는다.

## 실패 이력과 정리

초기 전용 테스트 DB 중지로 사전검사 4개가 종료됐고 소유권 확인된 Compose postgres-test만 재개했다.
다음 실행은 snapshot의 Passkey 컬럼 `id`/`key_id` 오류로 신규 3개가 실패했고 수정 후 통과했다.
최종 clock 신규 검사 최초 2개는 2.2초 단일 query가 기존 2초 statement timeout에 걸렸다.
설정을 늘리지 않고 1.1초 두 번으로 바꿔 before-valid/after-expired와401·전체 rollback을 확인했다.

신규 fixture의 비활성 Home에서 W0 신규 생성, 철회된 쿠키를 가진 client의 기존 login helper 사용,
GC 후 빈 MFA context, 이전 앱의 중복 TestClient lifespan 및 closing import 오류를 수정했다.
앱의 기존 인증 assertion이나 DB 제약을 낮추지 않았다. native의 관리자 로그인 자동 redirect 가정,
자기 변경 응답 읽기 실패, panel 갱신 전 disabled 검사, 같은 문서 fragment 이동으로
이전 token이 남는 준비 오류를 보완했다. 자기 변경 응답 읽기 실패는 원본 예외를 저장하지 않아
정확한 원인은 미확정이며, navigation 전 실제 응답을 확보하도록 보완한 뒤 통과했다.
전담 초기 hash proof 사례의 최종 old-link 요청은 로그인 상태의 CSRF로403을 받았다.
동일400 기대를 유지하고 별도 비로그인 client의 실제 preauth로 수정한 뒤4개 모두 통과했다. 현재 native는
실제 서버 응답을 받아 전달하고 UI 상태를
기다리며 새 링크는 새 문서에서 연다. 과거 실패 verdict 파일을 최신 성공 결과로 해석하지 않는다.

기존 pytest fixture가 자동 실행별 schema·프로세스·HTTPS/seed private 자료·임시 폴더를 정리한다.
완료 receipt의 removed=true와 경로 부재를 대조하며 최소 실패/판정만 남긴다. 공유 Compose 서비스와
볼륨, 다른 실행의 환경은 제거하지 않는다. 최종 정리 상태는 `cleanup-receipts.json`을 따른다.

## 후속 진입과 한계

개발 source freeze 후 독립 fast·새 단일 전체PG·전체 native 대조와 설계자 검토를 완료했다.
전담 커밋 세션의 변경 검토·커밋·일반 push 후, B1/B2에 이미 승인된 Trainer 업무 비활성화/재활성화의
가장 작은 W1 계약을 구체화한다. 이 결과는 W1 구현/검증 완료를 뜻하지 않는다. 운영 설치·전달·전달 수단 보안·실물 인증기·
전체 지원 브라우저·모바일 전 흐름은 미인수다. Operator, 관리자 승격/회수, Trainer 상태/Home 변경,
다른 사람 재연결, Trainer 분실 암호 reset, PT/금융 및 전체 모듈/공유 UoW 승인은 범위 밖이다.
