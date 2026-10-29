# IAM-013 Trainer 비밀번호 재설정 인수 결과

2026-10-30 로컬 설계자 인수 **PASS**. 기준 parent는
`24a913454f3030336db0281c96f56748f721fa67`, branch는 `codex/iam-trainer-password-reset`다.
[계약](iam-013-trainer-password-reset-design.md), [최소 인수 근거](iam-013-trainer-password-reset-review.json)를 따른다.

같은 조직의 다른 정상 Master가 ACTIVE 실제 Trainer 연결 계정의 암호 복구를 시작·재발급한다.
옛 암호와 전 로그인은 즉시 무효화하고 대상자가 30분 단회 링크로 새 암호를 설정한다.
Trainer 업무 active/grant와 자격 복구는 독립이며 역할 0·업무 비활성의 접근 제한과 관리자 UV를 유지한다.
일반 MFA 대상 판정을 넓히지 않고 reset 여섯 경로에만 새 helper를 사용했다.

원래 Actor idle/absolute 기한을 필요한 감사·최종 사실 읽기 뒤 검사하고 성공 때만 같은 DB 시각으로
활동을 갱신한다. 인증 입력 검증 오류를 일반화해 입력 반사를 차단했다. Master 전용 최소 화면은
응답 유실·충돌 뒤 비밀 링크를 비우고 안전한 GET으로 대사하며 자동 명령 재시도·재발급을 하지 않는다.

## 최종 독립 검증

| 범위 | 실제 결과 |
| --- | --- |
| fast 전체 | pytest131, Ruff/format130파일, mypy113파일, Import Linter8계약 통과 |
| 새 단일 선정 PostgreSQL |179 passed = 신규38+기존141, 실제 child exit0,1154.949초 |
| 같은 PG run native |5개 pytest 사례·8개 manifest·243개 strict true |
| source/Git/trust |Backend167 및 runtime 후 전체256개 raw SHA·정확 파일 집합, HEAD/index, trust4개 보존 |
| 정리 |독립 실행 폴더2개 삭제, 관찰 schema179개·등록 OS 식별188개·PG PID8개 잔존0 |

fresh pytest는 총310개다. native243은 위 pytest 안의 검증 조건이므로 별도 테스트 수로 더하지 않는다.
PG run은 `auto-a25a9e1944294718b2a874131b19df1a`, fast run은
`auto-c3a8aeba179e40d8bb21e7aff895e6a2`다. 실패/error/skip/xfail/미수집·미실행0이며 과거 PASS 이월은 없다.
기존 관리자 reset51개·S1/dispatch·MFA·I2/W1 관련 회귀를 포함했다. 전담 검증자가 작성한 causal7개도
최종 고정 소스에서 새로 실행했으며 그 소유 관계를 최소 근거에 명시했다. 설계자는 runtime을 추가하지 않았다.

실제 다른 Home 관리자 비활성화 commit 뒤 준비된 reset 완료, 역할 회수만 commit한 뒤 옛 proof 거부와
같은 원래 source의 새 자격 복구, Account/source의 실제 잠금 대기 중 만료, 실제 commit 뒤 ACK 유실과
명시 재발급, 유효 대상 세션/감사 변경 뒤 실제 원래 Actor 기한 초과와 전체 rollback을 확인했다.
가상 now의 GET/시작/재발급 순서9개와 실제 PostgreSQL 기한 검증을 구분한다.

## 개발 실패와 정정 이력

개발 단계 PG 통과 합집합77개(신규38+기존39)는 서로 다른 시점의 분할 근거이며 최종 성적에 더하지 않는다.
최초8pass1fail은 이미 로그인한 대상에 중복 로그인409를 예상하지 못한 새 테스트 흐름 오류였다.
38pass3fail은 absolute fixture FK 순서 오류였고 기존 FK를 유지한 단일 CTE로 보완했다.
35pass5fail에는 중복 실제 기한2개, native 문법 준비1개, 기존 race 장벽2개가 있었다.
후속7pass1fail 뒤 잘못된 CSRF 준비 위치를 고친 해당1개가 통과했다.

privacy 준비 테이블 이름 오류를 고친 뒤 실제 수정 전 입력 반사를 확인하고 일반화422로 보완했다.
native의 중복 const는 실행 전 문법 오류였고 변수명만 고쳤다. 기존 race는 reset 두 단계 모두
`touch=False`가 된 점에 맞춰 실제 main 진입에서 동기화하며 원래 단언·timeout과 양쪽 도달 확인을 유지했다.
중복 deadline probe의 timeout 원인은 driver 취소 원문을 확보한 결론이 아니며 해당 파일은 더 강한
causal2개로 대체했다. causal 최초6pass1fail은 GC 후 소비 source 행 보존을 기대한 새 단언 위치 오류였고
r2의7개가 새 실행으로 통과했다. collect-only745/PG614는 필수DB 미실행 guard exit1이며 실행 PASS가 아니다.
실패를 성공으로 바꾸지 않고 이 최소 요약을 보존한다. 완료된 원본 로그·복제 자료는 검토 종료 후 정리한다.

## 보존·한계와 다음 단계

기존 비-reset MFA29개·Service.login AST, migration14개 raw와 기존 native54개 이름·단언을 보존했다.
의존성/lockfile·Product/OPEN/ADR 및 전역 모듈 PROPOSED는 바꾸지 않았다. 개발 자동 실행12개와
독립2개는 각자의 stdout run-id/cleanup receipt로 확인하며 공유 Compose DB·원본 설정/인증자료는 유지한다.
영구 근거는 이 결과·계약·review.json과 Git이다. 완료된 QA 원본은 복사·압축 보관 없이 정리 대상이다.
후속 결정 검토에 필요한 최소 초안만 별도로 유지한다.

전체 PostgreSQL614 중435개는 이번에 실행하지 않았다. AB5/handoff 전체·전체 migration·운영/실물·
지원 목표 전체 브라우저·모바일 전 흐름·PT/지급/정산 인수로 확대하지 않는다. 로컬 Chromium은
151.0.7922.34이며 실제 HTTPS·sandbox·별도 CA를 사용했다. privacy7개 실제 요청은 모든 DTO/모든 오류의
전수 증명이 아니다. 기존 HTTPX TestClient·AnyIO BlockingPortal 경고2개도 숨기지 않았다.

전담 한글 상세 커밋·일반 feature push 후 다음 IAM 계정 수명 작업으로 이어간다.
설정 전 계정 차단/복구 상태와 Login ID 변경 허용 상태 두 선택은 아직 사용자 결정 대기이며 구현하지 않았다.
