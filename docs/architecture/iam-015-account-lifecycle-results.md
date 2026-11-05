# IAM-015 실행 결과 — 설정 대기 복구와 세 상태 Login ID 관리

2026-11-05 **설계자 로컬 인수 PASS — 승인된 소스 동등성 분할 검증**.
[LC-1/LC-2](../product/product-decisions.md#review-20261105-account-lifecycle)와
[제한 계약](iam-015-account-lifecycle-design.md)을 구현했다. 정확한 노드별 실행 근거·Backend176개 SHA·
브라우저67개 판정은 [최소 인수 근거](iam-015-account-lifecycle-review.json)에 있다.

## 결과 동작

같은 조직의 다른 정상 Master는 설정 대기 계정도 차단할 수 있다. 복구는 저장한 목적지에 따라
설정 대기 또는 기존 ACTIVE/reset 대기로 돌아간다. 옛 로그인·설정/복구 링크는 부활하지 않으며
필요한 최초 설정 링크는 기존 목적별 권한과 상태를 다시 확인해 별도로 발급한다.

ACTIVE/PENDING_SETUP/DISABLED에서 Login ID를 변경할 수 있다. 계정 UUID·기존 비밀번호/reset 대기·
역할/Scope·동일 Trainer 연결·업무 사실/보상 이력은 보존한다. 실제 변경은 이전 인증 입력을 폐기하고,
옛 ID 예약·동일 계정 실패 제한을 유지한다. 정규화 동일 ID는 현재 version/인가를 확인한 no-op이다.
Master/Branch Admin/Trainer/겸임·연결된 role0를 지원하며 복구로 역할이나 Trainer 업무 상태를 부여하지 않는다.

새 lifecycle 조회와 공통 mutation은 Master 전용/noSelf 보호를 적용한다. 기존 Branch Admin 대상 조회·
Scope 변경/최초 설정을 넓히지 않으며 Trainer-only/role0 응답에는 가짜 관리 Scope를 붙이지 않는다.
화면은 복구와 링크 재발급을 구분하고, 오래된 응답·중복 클릭·409·응답 유실을 현재 상태 조회로 처리한다.

신규0015는 `restore_state`와 readiness CHECK를 추가한다. 기존0014 DISABLED의 ACTIVE 목적지는
이전 복구 계약의 보존이며 역사 상태를 추측한 결과가 아니다. 원래0001–0014는 불변이다.
정확한0015 schema와 원래0014 대상 policy2 전이를 구분하고 손실 있는 downgrade를 거부한다.

## 실제 검증과 범위

| 구분 | 실행 결과 | 해석 |
| --- | --- | --- |
| 전체 수집·fixture plan | 835개 일치, lookup 오류0 | 실행0. PG call이 없는 기존 gate로 exit1이며 PASS에 합산하지 않음 |
| 교정본 새 fast | 197/197, 실제 exit0 | Ruff check/format·mypy·pytest·Import Linter 통과 |
| 독립 R1 선정 PG | 293 PASS / 1 FAIL / 17 미실행, exit1 | 원래 실패를 유지. 당시 선정311개의 전체 성공이 아님 |
| 독립 R2 PG | 실패1+미실행17의 정확한18/18, exit0 | 교정본에서 새 실행. skip/xfail/error/미실행0 |
| 승인된 분할 근거 | R1 미변경293 + R2 새18 = 고유311 | 교집합·누락·중복0. 단일 최종311 실행이나 전체638 성공이 아님 |
| 실제 HTTPS/native | R1의1사례·4manifest·67개 literal true | PG293에 포함. 신규6 lifecycle 조건 포함. R2 새 브라우저 실행을 주장하지 않음 |

전체 PostgreSQL638개 중327개는 선정하지 않았다. 개발자 검사·이전 IAM-014 성적·R1 fast를
최종 점수에 더하지 않는다. 브라우저 작성자는 개발 담당자, 정적 검토/실제 실행자는 독립 테스트 담당자다.
실제 브라우저 버전은151.0.7922.34다. 기존 Starlette HTTPX/AnyIO alias 경고 두 종류는 숨기지 않았다.

## 실패 교정과 동등성

R1의 `test_original_handoff_chain_requires_semantic_ancestry[valid]`는 원래0014 분류를 검증한 뒤
현재 UoW를0014에서 열어 `authentication_policy_unavailable`로 실패했다. 실제 exact0015 거부는 올바른 동작이다.
해당 valid 분기에서만0015로 전진하고 원래 정책 전이·계정별 분류·비상 사건의 전체 행 digest 보존을
확인하도록 고쳤다. 원래 기대값/0014 검사·migration·runtime guard·기한·인가를 완화하지 않았다.

Backend176개 중 바뀐 파일은 이 테스트1개뿐이며, 삽입을 역제거한 bytes가 R1 원본 SHA와 일치한다.
다른175개와 import/global/다른 함수 AST는 같고 수정 함수의 R1 PASS는0개다. 독립 검토와 설계자 승인을
거쳐 영향받지 않은293개와 새18개의 분할 근거를 사용했다. 무제한 동적 의존성 동등성 증명은 아니다.
최종 Backend SHA는 `442df0969ccfea0fcf00879ceffe90577e068f75cb1aacab1001854e7cd922ba`다.

초기 native 계획의107은 standalone58개 manifest를 잘못 더한 메타데이터 오류였다. 실제 선정 runner의
18+9+22+18=67개를 원본/안전 보고서/manifest와 대조했다. 실제 통과 수를107로 보고하지 않는다.
개발 중 Ruff 줄 길이·mypy 반환 타입 교정도 있었으며 개발 검사는 독립 인수와 분리했다.

## Git·정리·남은 경계

시작/검증 feature parent는 `af9de549a5511eae28e66ba092c84cd98d2c8ef5`다. R1 중 별도 사용자 요청의
IAM-014 main fast-forward로 main/origin/main이4deb779에서 이 parent로 이동했다. 원래 불변 실패를
기록하고 실제 reflog/원격/별도 작업 근거를 대조했다. 현재 feature HEAD/index/소스는 유지됐으며
이를 원복하지 않고 R2 보호 기준을af9de54로 설정했다. 최초부터 모든 Git ref가 불변이었다고 주장하지 않는다.
IAM-015 완료는 전담 검토·한글 상세 커밋·일반 feature push 절차를 따르며 새로운 main merge는 포함하지 않는다.

실행자의 전용 schema/프로세스/자동 실행 폴더는 정리됐고 원래 DB schema/table 집합·다른 연결과
소스/trust 불변을 대조했다. 완료된 원시 자료는 이 최소 요약과 미해결 다음 결정에 필요한 자료를 추린 뒤 정리한다.
현재 재사용 corpus·원본/공유 데이터·다른 작업 환경은 정리 대상이 아니다.

원본/운영 DB 적용·배포, 실물 기기·다른 지원 브라우저·전체 모바일 인수는 수행하지 않았다.
Operator·Member·PT/보상/정산 기능을 추가하지 않았으며 다른22 OPEN/8 CLOSED와 전역 모듈 PROPOSED는 유지한다.
