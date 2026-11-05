# IAM-016 결과 — Operator 발급·최초 설정·로그인

2026-11-05 **설계자 로컬 인수 PASS — 승인된 분할 검증**.
[OP-2/OP-3](../product/product-decisions.md#review-20261105-operator-onboarding)와
[제한 계약](iam-016-operator-onboarding-design.md)을 구현했다. Backend178개 SHA와 정확한299개 노드,
실제 브라우저33개 판정·교정/재사용 근거는 [최소 인수 근거](iam-016-operator-onboarding-review.json)를 따른다.

## 결과 동작

Master 또는 현재 관리 지점의 Branch Admin이 활성 지점에 새 Operator를 발급한다.
설정 대기 계정의 링크는 같은 조직 Master/현재 업무 지점 Branch Admin만 명시 재발급한다.
발급 후 지점이 비활성화돼도 기존 유효 링크 소비와 허용 재발급은 가능하며, 비활성 지점 신규 배정은 거부한다.
기존 발급자의 과거 Scope는 권한을 남기지 않는다. 링크는30분 단회이고 재발급은 이전 링크를 폐기한다.

수신자가 비밀번호를 설정한 뒤 별도로 로그인한다. 현재 Operator 역할·단일 업무 지점과 자기 지점 기본정보를
조회하고 본인 암호 변경·로그아웃을 수행한다. 관리자 Branch 필드와 Operator Scope를 분리해 관리자 API/보상 권한을
부여하지 않는다. 기존 Master 전용 차단/복구·ID 변경·정상 reset과 C2/CSRF·감사를 유지한다.

준비된 Operator 계정에 기존 I2 절차로 실제 Trainer를 연결할 수 있다. 업무 지점 B/Trainer Home A는 독립이다.
W1 Trainer 업무 비활성화는 Operator 로그인을 유지하고, 실제 I2 역할 변경은 모든 기존 로그인을 철회한다.
현재 비밀번호를 확인하는 본인 변경과 Master 정상 reset은 비활성 Trainer 겸임에서도 독립 Operator를 지원한다.

계정·grant·설정 원본·필수 감사는 하나의 업무 UoW에서 저장한다. 준비 증명/로그인은 raw grant의 단조 version,
계정/암호/정책·원래 기한에 결속된다. 현재 grant와 과거 감사 지점은 분리하고 GC의 child/orphan/release 검사를
함께 확장했다. 화면은 링크 폐기·늦은 조회·중복 클릭·409/응답 유실을 현재 상태 대사와 명시 재발급으로 처리한다.

신규0016은 grant/목적별 source/typed Audit와 세션 version을 추가한다. 기존 계정에 Operator를 추론하지 않는다.
원래0001–0015와 policy2의0014 전이 목적지는 불변이며 현재 runtime/CLI/UoW는 정확한 단일0016을 요구한다.
새 자료/이력이 있는 downgrade는 DDL 전에 거부한다. 원본 DB에 적용하지 않았다.

## 실제 검증

| 구분 | 실제 결과 | 범위 |
| --- | --- | --- |
| 최종 수집/fixture plan | 845개·100 fixture, lookup 오류0 | 실행0/exit1. 기존 필수 DB gate에 따른 미실행이며 PASS에 합산하지 않음 |
| C 새 fast | 197/197, exit0 | Ruff check/format·mypy·Import Linter8개 포함 |
| R1 | PG168 PASS/1 FAIL/128 미실행 | 최초 선정297. 원래 실패와 미도달 검증을 보존 |
| R2 | PG63 PASS/1 FAIL/65 미실행 | 교정 후 선정129. 이 성공은 최종 점수에 재사용하지 않음 |
| R3 C 새 PG | 고유181/181, 7회 실행 모두 exit0 | 신규 Operator8·원래 실패/역사43·두 순서 회귀·관련 인증/Trainer/W1/reset/native 포함 |
| 승인된 최종 분할 | A core118 재사용 + C 새181 = 고유299 | 교집합/누락/중복0. 단일299 또는 전체648 성공이 아님 |
| C 실제 HTTPS/native | 1사례·33개 literal true, Operator11 포함 | 새181에 포함. Chromium151.0.7922.34 |

전체PG648개 중349개는 선정하지 않았다. 개발 성적·R1/R2 fast·R2 성공을 최종 점수에 더하지 않았다.
R3의 모든 PG 실행은 `--require-postgres -x`를 사용했고 실패/error/skip/xfail/미실행0이다.
기존 Starlette HTTPX/AnyIO alias 경고 두 종류는 숨기지 않았다.

## 실패 교정과 근거의 한계

R1 retained-session 검사는 새 `operator_version=0` 열까지 과거 JSON과 비교해 실패했다. 원래0014의 보존/폐기
단언을 유지하고 실제0016으로 전진한 뒤 모든 원래 테이블의 전체 행 digest·알려진 기본값·빈 Operator 표와
현재 앱의 옛 cookie/source 거부까지 확인하도록 테스트 함수 한 곳을 고쳤다. 앱·guard를 완화하지 않았다.

R2는 감사 뒤 migration 대기를 관찰하고 발급 writer를 풀었지만 기대201 대신503을 받았다. 그 실행의 commit
결과/SQLSTATE는 수집하지 못했다. 별도 개발 음성 대조에서는 업무 commit 뒤 정리 연결 C가 M의
`iam_security_states`를 기다리고 M은 C의 `alembic_version`을 기다리는 실제 cycle·C의40P01·저장 건수1/1/1/1을
관측했다. 이를 원래 R2의 직접 관측으로 소급하지 않는다. 신규0016 **downgrade 진입에서만** installation 관계
배타 잠금을 선취해 policy reader를 정리한 뒤 자식 DDL/연속 revision을 처리하도록 고쳤다.
원래 실패 검사와 C 선행/M 선행 두 실제 연결 회귀가 모두201→guard 거부→이력/schema 보존→source204까지 통과했다.

A→B는 retained 테스트 본문만, B→C는 신규 downgrade 두 줄과 함수 내부 hook의 회귀 두 건 추가뿐이다.
최종 재사용은 **R1 core118만**이다. 현재0016 downgrade를 실행하지 않는 실제 fixture 경로·동일 upgrade/runtime,
함수 밖 AST/원래 노드와 fixture closure·역교정 bytes를 독립/설계자 검토했다. S2B의 해당 역사 검사는 고정0013→0003이다.
이 범위의 동등성은 무제한 동적 import/OS/시간 상태의 형식적 증명이 아니다. 다른 기존 성공은 C에서 다시 실행했다.

개발 초기 같은 문서의 새 fragment 진입이 설정 상태를 초기화하지 않는 문제도 고쳐 native로 검증했다.
최종 native 집계 중 generic58개 runner의 `latest-browser.json`을 복사한 메타데이터 오류는 점수에서 제외했다.
실제 `trainer=True`의 `latest-trainer-browser.json`은 해당 run-id/원본 SHA·33개 manifest와 일치한다. 브라우저 재시도는0이다.
모델 용량 오류로 담당 turn이 중단됐을 때도 기존 실행 session을 회수해 history43의 exit0을 확인했고 중복 실행하지 않았다.

## 정리·남은 경계

독립 실행의 소유 schema/프로세스/자동 실행 폴더를 정리했고 원래 schema 집합·다른 연결·소스/Git/trust 불변을
대조했다. SourceC Backend SHA는 `5bf4d1929d05d390026ab04824451a11cbcea7364966803c7108cea750f65ea2`다.
설계자의 후속 변경은 Product/Architecture 결과 문서뿐이다. 완료된 사적 원시 자료는 이 최소 근거와
미결정 사항을 보존한 뒤 정리한다. 고정 runtime lock/재사용 corpus·원본/다른 환경은 삭제하지 않는다.

기존 계정에 Operator 역할 추가/회수·재부여, 업무 지점 이동, 관리자+Operator 조합의 신규 생성은 미구현이다.
그 대상 계정 상태/조합의 Product 결정은 후속이며 기존 Actor·단일 Scope·Trainer 독립성을 재질문하지 않는다.
Member/PT/보상/정산, 원본/운영 DB 전환·배포, 실물/전체 브라우저·모바일/Responsive 인수는 수행하지 않았다.
다른22 OPEN/8 CLOSED·전역 모듈 PROPOSED와 운영 게이트는 유지한다. 전담 검토·한글 상세 커밋·일반 feature push가 후속이다.
