# IAM-005 MFA-A 개발 결과

2026-10-18. 상태는 **제한된 로컬 MFA-A 개발 인수 PASS**다. 운영 인수와 IAM 전체 완료가 아니다.
[설계자 인수 근거](iam-005-mfa-a-review.json)는 개발·독립 실행과 소스 대조를 구분한다.
[구현 계약](iam-005-mfa-a-design.md)의 좁은 등록·로그인·추가 키 범위를 구현했다.
M7/M8 추가 결정도 삭제/reset 후속에 적용하며 이번 구현 범위를 확장하지 않았다.

## 실행 결과

| 검사 | 실제 결과와 범위 |
| --- | --- |
| 최종 fast | **88 passed**, PG144 deselected; Ruff/format/mypy48 통과, Import Linter7 kept |
| 개발 PostgreSQL 대상 | **50 passed**: 당시 MFA 전체 대상과 영향받는 S1/S2c migration 검사 |
| 최종 변경 확인 PostgreSQL | **10 passed**: 실제 CLI·COMMIT 실패/응답 유실·확장 경합·목적/Actor/소유권 |
| 개발 실제 HTTPS | 신뢰된 Chromium151.0.7922.34, native WebAuthn **20개 필수 확인 통과** |
| 독립 fast 전체 | **88 passed**, PG144 deselected; Ruff/format57개·mypy48개·Import Linter7 kept/0 broken |
| 독립 필수 PostgreSQL 전체 | **144 passed**, fast88 deselected, 993.86초. skip/xfail/xpass/실패0 |
| 독립 실제 HTTPS | 동일 PG 실행의 Chromium151.0.7922.34, 기존 **58항목**·새 native MFA **20항목** 전부 true |

숫자를 합쳐 전체 통과 수로 주장하지 않는다. 여러 대상 검사에는 중복이 있다. 50개 실행 중 CLI의
정확0600/생성 실패 정리와 테스트 privacy/추가 사례를 보강했으며 최종10개와 fast는 동일 backend
candidate에서 실행했다. 이후 설계 문서의 상태/결과 링크만 갱신했다. 개발 HTTPS는 R5 실패 감사 귀속,
활성화 필수 감사, CLI 최종 보강 이전의 증거이므로 최종 동결 브라우저 인수는 독립 담당자에게 넘긴다.
총232 = fast88 + PG144이며 HTTPS boolean58/20은 PG 안의 두 pytest 검사다. 별도 통과 수로 더하지 않는다.
독립 fast와 DB 실행의 HTTPX fallback/AnyIO 경고는 각각2개이며 숨기지 않았다.
webauthn3.0.1 및 필요한 새 전이 의존성만 추가했고 기존 잠금 버전은 유지했다.

## 검토 보완과 검증

- R1: 시작/최종 계정·security_version·고정 budget key/attempt 결합과 실제 ID 변경 경합.
- R2/PF1: crypto 후 현재 Actor 재인증. ceremony는 살아 있고 세션만 idle/absolute 만료·철회되는
  원인을 분리해 key/소비/활동/감사 전체 보존 확인.
- R3: onboarding/add 양방향 목적 혼용과 타 Actor·credential 소유권 거부.
- R4: 빈 migration 왕복, key/context/assurance/attempt/감사/부모 예약 각각의 downgrade 거부·원본 보존,
  실제 할당 transaction과 migration의 잠금 대기.
- R5: 검증된 admission principal의 조직에 비밀번호·MFA 실패 감사 귀속. unknown은 일반 최소 기록.
- 설치 COMMIT 응답 유실 시 개인파일 보존 후 실제 등록 가능, 명확 감사 실패 시 전체 rollback/자기 파일 제거.
- 로그인 finish/ACK 실패는 cookie를 주지 않고 해당 미전달 sid만 철회한다. 정상 기존 세션은 보존한다.
  정리 실패도 숨기지 않는 검사를 수행하고 테스트의 자기 자료는 정리했다.
- 등록/활성화와 두 필수 감사의 원자성, C2 실패 합산·성공 비초기화, 자원 한도·GC,
  동기화 키의 0 counter/backup state와 nonadvancing counter, 실제 독립 연결 경합을 확인했다.
- MFA 및 기존 --showlocals privacy canary를 통과했다. 테스트용 private payload/cookie도 repr에서 숨긴다.

초기 PG preflight는 서비스 중지로 검사에 진입하지 못했다. 테스트의 중복 lifespan/GC 기대값과
새 explicit mode를 누락한 기존 startup 검사(87 pass/1 fail)도 보완했다. 초기 정적 검사 cwd 오류와
중간 형식/type 실패는 최종 통과와 구분한다. 실패 이력 요약을 인수 JSON에 남긴다.
모든 기록된 자동 실행의 자기 프로세스/schema/run은 정리됐다. 공유 결과 폴더는 보존하고,
검증된 전용 Compose postgres-test 서비스는 이어질 독립 검증을 위해 유지한다. 공유 volume은 삭제하지 않았다.

## 동결과 인계

실행·실패·정리·변경 파일 SHA는 ignored
`.local/qa/iam-mfa-a-51e5747733d7439c/developer-result.json`에 있다.
동결 소스 목록은 같은 폴더 `source-frozen.json`이며 root 소유 정책9개 문서는 제외한다.
결과 문서 자체는 순환 해시를 피하기 위해 소스 목록에서 제외한다. ignored 인계 JSON은 진행용 자료이며
완료 후 영구 보존을 요구하지 않는다. 보존할 최소 결과·실패·정리 근거는 공개 인수 JSON에 포함한다.

동결 manifest SHA-256: `98c173b960614f6d9d1d4aac2c8a7b066e391d735dd237672b7b8569c838a443`.

독립 실행 전후 동결79개가 일치했다. 설계자는 R1–R5/PF1 보완·권한/잠금/트랜잭션·실제 결과와
4개 자동 실행 폴더 정리를 대조해 인수했다. 설계자가 전체 테스트를 별도로 반복 실행한 것은 아니다.
실행 뒤 설계서의 가상 서명 생성 도구 표현만 바로잡았으며 앱/테스트/lock/migration 소스는 동일하다.
개발 자동11회와 독립4개 실행 폴더의 자기 프로세스/schema/자료는 정리했고 미정리 항목은 없다.
전용 Compose 검증 DB·공유 volume과 활성 corpus 입력은 후속 검증에 사용하므로 유지한다.

전담 커밋 세션의 최종 변경 검토·한글 커밋·일반 push 순서를 따른다. 운영 허용, 삭제/분실 복구,
추가 Master, 관리자 reset, AB5·실물 기기/OS/모바일/지원 브라우저 전체 인수는 포함하지 않는다.
