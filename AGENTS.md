# 저장소 작업 지침

- 승인된 제품 기준은 [docs/product/README.md](docs/product/README.md)다. [docs/analysis/](docs/analysis/README.md)는 역사적 AS-IS 참고이며 TO-BE의 정답이 아니다.
- 승인된 기술은 [ADR-0001](docs/decisions/0001-backend-stack.md), 시스템 형태는 [ADR-0002](docs/decisions/0002-modular-monolith.md)에서 확인한다. PROPOSED 설계를 승인된 정책으로 취급하지 않는다.
- 작업 전 관련 Requirement, Business Rule, [Product OPEN](docs/product/open-questions.md)과 [결정 게이트](docs/architecture/decision-gates.md)를 확인한다. 게이트에 걸린 금액·권한·상태 전이를 임의 기본값으로 구현하지 않는다.
- 각 작업에서 사용자가 허용한 수정 범위를 지킨다. 기존 사용자 변경을 임의로 되돌리거나 덮어쓰지 않는다.
- 사용자 승인된 작업 흐름은 개발 → 독립 테스트 → 설계자 검토 → 전담 `커밋노예` 세션의 변경 검토·커밋·푸시다. 커밋 메시지는 한글로 변경 이유·동작·검증을 구체적으로 작성한다. 사용자 결정/확인이 필요한 변경은 승인 전 구현·커밋하지 않으며 이미 승인된 부분과 구분한다. 완료된 증분 이후에도 승인 범위 안에서 진행하고 새로운 사용자 결정이 필요한 지점에서 질문을 모은다. 다른 작업의 채팅을 사용자에게 전달하지 않고 설계자가 결과 파일과 상태를 확인해 요약한다.
- 설계 탐색은 [Architecture README](docs/architecture/README.md), [모듈 경계](docs/architecture/module-boundaries.md), [데이터·트랜잭션](docs/architecture/data-and-transactions.md)을 따른다.
- [검증 계획](docs/architecture/validation-plan.md)의 미구성 검사와 실제 실행 가능한 검사를 구분한다. 수행하지 않은 테스트·migration·운영 검증을 통과했다고 보고하지 않는다.
- 보안정보와 운영 개인정보를 문서·일반 로그에 복사하지 않는다. 문서 예시는 비식별 가상 데이터를 사용한다.
- 테스트·검수 실행 자료는 ignored `.local/qa/`의 고유 실행 폴더에 둔다. 기존 pytest/fixture를 사용하고 별도 수명주기 관리 도구를 추가하지 않는다. 자동 실행 담당자는 최소 결과를 남긴 뒤 자기 프로세스·schema·폴더를 정리하고 실패/미정리 항목을 보고한다. 수동 검수·미해결 재현 환경은 이유와 정리 조건을 기록해 유지하며 검수 완료·미사용 확인 후에만 정리한다. 상세 절차는 [QA 안내](backend/README.md#qa-실행-자료와-정리)를 따른다.

이 파일은 작업 규칙과 탐색 안내이며 자동 검증 장치가 아니다. 현재 단계와 다음 작업의 진입 조건은 Architecture README에 있다.

기반은 [ADR-0003](docs/decisions/0003-foundation-tooling.md), [개발 안내](backend/README.md), [FOUNDATION-001](docs/architecture/foundation-001.md) 및 [FOUNDATION-002 결과](docs/architecture/foundation-002.md)를 따른다. backend/에서 `uv sync --locked` 후 `powershell -NoProfile -ExecutionPolicy Bypass -File ./check.ps1 -Mode fast`로 Ruff/mypy/DB 없는 pytest/Import Linter를 실행한다. 필수 DB 검사는 `uv run --locked --env-file .env.example pytest -m postgres --require-postgres`이며 별도 Y3_TEST_DATABASE_URL과 소유권이 확인된 전용 Compose DB가 필요하다. 설정 누락·skip/xfail·미수집을 성공으로 보고하지 않는다. 기반 검사를 미래 업무 모듈·권한·지급/동시성 검증 완료로 확대하지 않는다.

## WSL 현재 환경 (2026-09-18)

사용자 지시로 WSL Ubuntu로 이전했다. 현재 backend/ 검사는 `bash check.sh fast`, DB 검사는 `bash check.sh db`를 사용한다. Docker context는 `wsl-ubuntu`, 엔드포인트는 `unix:///run/docker-wsl.sock`이다. Windows용 기존 절차와 과거 미검증 기록은 이력으로 유지한다. 현재 사용법은 backend/README.md의 WSL 절을 따른다.
