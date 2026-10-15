# IAM S2c — Login ID 변경 구현·검증 결과

2026-10-15. **독립 전체 검증·설계자 검토를 마친 제한된 로컬 개발 인수 PASS**다.
기준 commit `0a947f9bccc615140b4a3ea24809790aa452172e`, branch `codex/iam-s2c-login-id`.

현재 Master가 같은 Organization의 ACTIVE Branch Admin Login ID를 변경한다. 이전 ID는 원계정에 예약하고 그 계정으로의 복귀만 허용하며 로그인 별칭으로 쓰지 않는다. 계정 UUID·암호·독립 Scope·기존 이력을 보존하고 대상 모든 인증을 철회한다. ID/예약/불변 예산 key/버전/철회/감사는 같은 Application UoW다.

로그인 admission의 account/version/key를 실제 proof와 잠금 이후 계정에 결합한다. 이전 실패·pending·cooldown을 옮기거나 초기화하지 않으며 과거 예약 ID 익명 시도는 별도 domain으로 제한한다. 실제 변경은 현재 Master 인증의 활동만 갱신하고 absolute 종료·다른 인증/계정은 유지한다. 동일 ID no-op는 전체 상태를 보존하고 최종 재인증 만료나 감사 실패는 전체 rollback한다. [기술 설계](iam-004-login-id-design.md)를 따른다.

## 최종 검증

독립 담당자가 같은 최종 source revision4에서 다음을 실제 실행했다.

| 검사 | 실제 결과 |
| --- | --- |
| `bash check.sh fast` | 81 passed / 97 deselected, 17.70초 |
| `bash check.sh db` | **97 passed / 81 deselected**, 728.34초, exit0 |
| 실제 신뢰 HTTPS Chromium 151.0.7922.34 | 기존48 + 신규10 = **58/58 true**, DB97에 포함 |
| 정적 검사 | Ruff/format, mypy42 files, Import Linter7 kept/0 broken |

전체 수집178개이며 skip/xfail/미수집을 성공으로 센 항목은 없다. 각 canonical 실행의 경고2종(Starlette/httpx, AnyIO BlockingPortal)은 유지했다. source70개와 manifest checksum은 실행 전후 같았고 추가 독립 중복 probe는 필요하지 않았다. 최종 코드 파일14개의 SHA·실행/정리·인수 판정은 [검토 요약](iam-004-login-id-review.json)에 둔다. root는 결과·소스·자원 보존을 검토했으며 전체 검사를 직접 실행했다고 주장하지 않는다.

## 이전 실행과 보완

- 개발 초기 PG86은 85pass/1fail이었다. reserved-ID 경합 테스트가 다른 기존 GC 유예 슬롯을 이번 요청 누수로 세었고, 실제 할당한 슬롯만 추적하도록 수정했다. 보정 및 신규 사례12개를 재검사했다. 초기 전체 manifest는 없었으므로 최종 소스에 소급하지 않는다.
- 독립 최초 인계는 두 테스트 파일의 해시 차이를 발견해 실행 전 중단했다. 재인계된 이전 revision3은 fast81, PG51개 통과 후 root 지시로 중단됐고 43개는 완료하지 않았다. SIGINT 뒤 보수적 schema-marker 정리 보류로 종료1이었으며 실제 schema 부재를 확인해 기존 정리 경로로 처리했다. 전체 성공으로 계산하지 않는다.
- root가 실제 ID 변경의 Master idle 활동 누락을 발견했다. 수정 전 회귀 테스트 실패를 재현했고 같은 UoW의 최종 재인증/CSRF 뒤 활동을 갱신하도록 보완했다. near-idle/idle·absolute 처리 중 만료3개를 추가했고 revision4 fast81 및 관련 PG23개를 개발자가 확인했다. 첫 회귀 선택 명령의 exit4와 두 RED 실행도 인수 요약에 구분한다.
- 개인정보 검사는 `--showlocals` child의 의도적 실패1건에서 암호/쿠키/nonce/hash/anchor의 문자열·bytes 표현이 노출되지 않는지 확인한다. child 실패를 정상 PASS 건수에 더하지 않는다.
- 브라우저 항목 수는 기존48+신규10=58이다. 초기 root 안내의59는 수치 오기였으며 항목을 제거한 것이 아니다.

## 보존과 한계

Product/ADR/복합 OPEN, 원본 migration0001–0003, 의존성/lock/corpus 및 공용 QA/UoW/runtime은 보존했다. 기존 두 Port 경합 wrapper와 migration head 기대만 호환 조정했고 비교 의미는 유지했다. 새0004는 32byte/unique key와 전후ID 감사 제약, key/감사가 남은 downgrade 거부를 검증한다.

기존 pytest 도구가 자동 실행의 자기 process/schema/폴더/TLS·브라우저 프로필을 정리했다. 독립 확인에서 원래 schema 집합·trust246개(심볼릭 링크 포함)·원본 corpus7개·공유 runtime/dependency를 유지했으며 남은 자기 process/schema는0이다. 이 최소 결과와 인수 JSON을 보존한 뒤 완료된 private 검토 폴더6개/파일33개, 180,647bytes를 정리했다. dry-run과 실제 대상이 일치했고 보류/미정리 항목은0이다. 최초 대조는 JavaScript 나노초 정수 정밀도 차이로 삭제 전에 중단됐으며 정확한 문자열 표현으로 재검증 후 정리했다. 사용 중 corpus 입력과 전담 커밋 담당자의 현재 검토 자료는 유지한다.

제한된 로컬 개발 인수이며 운영 배포·MFA/비상 복구·부하·키 회전·전체 IAM/v1 완료가 아니다. 다른 역할 및 Master·비활성 대상 ID 변경은 후속 구현 범위다. 전담 커밋 담당자가 최종 인수 뒤 승인된 증분만 한글 상세 커밋·일반 push한다.
