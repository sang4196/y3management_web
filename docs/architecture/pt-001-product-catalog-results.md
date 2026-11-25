# PT-001 실행 결과 — Organization 공통 PT 상품 관리

2026-11-25 **설계자 로컬 인수 PASS**. [CAT-1/CAT-2](../product/product-decisions.md#review-20261125-catalog-input-state)와 [제한 계약](pt-001-product-catalog-design.md)을 구현했다.
Parent `538c7b7955e49a694da595d38d69c8940787b984`, branch `codex/pt-product-catalog`.
개별58 판정·원시 조건·소스/근거 SHA와 초기 실패는 [최소 검토 근거](pt-001-product-catalog-review.json)에 있다.

## 구현과 검토

현재 같은 Organization Master의 상품 등록·목록/상세·정보 수정·판매중단·본인 작업 결과를 제공한다.
이름·0원 이상 가격·양수 횟수·지급방식·서비스 여부를 명시하며 가격/횟수는 정확한 십진 문자열이다.
서비스는 FIXED_AMOUNT만 허용한다. 처음 판매 중이고 중단 후 정보 수정은 중단 상태를 유지한다.
상품은 Trainer 지급액을 갖지 않는다. 실제 변경은 새 버전을 추가하고 이전 상품 사실은 수정하지 않는다.

현재 Caller/조직·ExpectedActor·CSRF·원래 요청 기한을 검증하고 version CAS/원 Actor의 operation UUID를 사용한다.
head/version/receipt/typed Audit가 같은 UoW에서 확정된다. no-op/replay는 추가 버전·Audit·활동 갱신을 만들지 않는다.
작은 nonnull core와 별도 nullable-before FK로 typed 관계를 검증하며 큰 이름/금액을 B-tree identity에 넣지 않는다.
원래 확정 결과와 현재 조회는 구분하고, 미확정 UUID/명령을 유지해 같은 작업으로 대사한다.
receipt404 뒤 재시도의 명백한 업무 거부는 원 Actor를 확인한 뒤 종료하고 fresh detail로만 새 CAS 편집을 허용한다.
네트워크/5xx·인가/Actor 변경은 미확정 상태를 유지한다. 페이지 이동·늦은 응답·계정 교체에 낡은 입력이 섞이지 않는다.
390px의 긴 ASCII 이름/가격 목록·편집 화면을 실제 브라우저에서 검사했다.

0022만 추가했다. 실제 parent21의 RF/Base 등록·수정·no-op·취소/Home/IAM 사실을 만든 뒤 전체 행의21→22→21 보존과 두 runtime의 잘못된 head 거부를 검증했다.
새 Catalog 사실이 있으면 파괴 downgrade를 거부한다. 실제 역변환으로 하위 shape를 준비하고 원래 guards를 검사한다.
원래0001–0021/ADR·공통 helpers·의존성/lock은 보존했으며 Import Linter는 기존8 계약을 유지하고 PT 경계9번째를 추가했다.

## 새 독립 실행

| 검사 | 실제 결과 |
| --- | --- |
| `bash check.sh fast` | 218 PASS, Ruff/format/mypy143 PASS, Import Linter9 kept |
| 선정 PostgreSQL | 정확58 단일 실행 PASS, `--require-postgres -x`, 457.049초 |
| Catalog native | 위58에 포함, 별도 manifest22 전부 literal true |
| 기존 Workforce native | 위58에 포함, 별도 manifest54 전부 literal true |
| 실패/error/skip/xfail/xpass·선정 누락 | 모두0 |
| 전체 collection | 1051=비PG218+PG833, 나머지PG775 미실행 |

두 native는 같은 `auto-e2b64c0c00d341bd8912827e6386ecbd`와 실제 Chromium151.0.7922.34다.
설계자가58개 JUnit 판정·raw/safe exact keyset/boolean·같은 run/binary·소스330/Backend212와 보호42·환경 보존을 직접 대조했다.
기존 TLS/NSS/bubblewrap/90초 cap/소유권/정리 body는 유지했다. 기존 Starlette/httpx·AnyIO 경고2개는 남아 있다.

## 교정·보존·범위

첫 독립 실행은32 PASS/1 FAIL/25 미실행이었다. target18 guard는 정상 거부했지만 observer가 실제22→18 준비 DDL14개도 포함했다.
같은 rollback Connection에서 실제18 준비/정확 head 확인 후 guard만 관측하도록 교정했다. targetDDL0과 rollback 뒤 원22 전체 행/shape/head 보존을3개 parameter에서 확인했다.
그 실패의 마지막 fingerprint/shape 단언은 미실행이었음을 구분한다. 최종 새58 성적에 초기32나 개발자 성적을 합산하지 않았다.

정적 검토에서 발견한5xx UUID 손실·페이지 이동의 이전 초안·늦은 refresh 후속 조회·pending 폐기와 추가404→409 복구 잠김을 수정했다.
새 native는 실제 미전달/커밋 후 ACK 손실, 원 UUID/body retry503 유지, 다른 Master의 실제 변경 뒤409, fresh/new UUID CAS 복구를 확인한다.
공유 UoW 실제 commit ACK 예외는 기존 Workforce node로 따로 검사했다. Catalog 전용 DB commit fault로 확대하지 않는다.
개발 중 foreign fixture 관계·정책 반례 준비와 실행0 메타데이터 판독 오류도 원래 제약을 바꾸지 않고 바로잡았다.

최종 전후 소스/HEAD/index/refs/trust/hosts/실제 binary는 동일하고 소유 schema58·프로세스·포트·auto 폴더 잔존은0이다.
원본/공유 DB·현재 개발 도구는 유지한다. 완료한 집계 raw는 커밋 검토 뒤 최소 결과를 남기고 정리한다.
인수 후 Architecture 문서와 새0022 SQL 문자열의 공백만 있는90행9칸을 정리했다. 이 한 곳은 staged 검사에서 발견됐으며 원래0001–0021은 불변이다.
변경 전후의 정확한 단일 빈줄 치환·전체 파일/SQL token 동일성을 설계자가 대조했다. 이 비의미 공백 제거 뒤 runtime은 반복하지 않았고, 전담 staged SHA/whitespace 검사를 다시 수행한다. 최소 근거에 runtime 동결 SHA와 최종 SHA를 각각 남겼다.
판매재개/삭제·일반 NonMaster 조회·Pass/PT/지급/정산·다른 플랫폼·원본 DB 적용/운영 배포는 이번 인수에 포함하지 않는다.
다른 Product OPEN/전역 PROPOSED 상태는 유지한다.
