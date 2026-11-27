# PT-001 — Organization 공통 PT Product Catalog

Status: **LOCAL ACCEPTANCE PASS — IMPLEMENTED / INDEPENDENTLY VERIFIED** (2026-11-25).
Parent `538c7b7955e49a694da595d38d69c8940787b984`, branch `codex/pt-product-catalog`.
[CAT-1/CAT-2](../product/product-decisions.md#review-20261125-catalog-input-state), BR-PAY-001/005/011, PR-006을 따른다.
이 한정된 PT Operations Catalog의 책임·공개 계약만 기술 검토하며 전체 모듈 PROPOSED/다른 OPEN을 ACCEPTED로 바꾸지 않는다.
구현·한정 교정·재동결·새 독립 실행을 마쳤고 설계자가 로컬 인수했다. [결과](pt-001-product-catalog-results.md)와 [최소 근거](pt-001-product-catalog-review.json)를 따른다.

## 범위·소유권

현재 같은 Organization Master만 목록/직접 조회/생성/정보 수정/판매중단/자신의 작업 결과를 사용한다.
Branch Admin/Operator/Trainer 단독은 불가며 겸임은 독립 Master 권한으로 판단한다. 다른 Organization/이전 권한/클라이언트role·Scope를 믿지 않는다.
Branch별 중복 Catalog·가격은 도입하지 않는다. 일반 NonMaster Catalog 조회/발급 후보, 판매재개/삭제/Pass·PTSession/Payment/Settlement는 미구현 범위다.
판매중단은 새 Pass 발급만 차단한다는 기존 규칙을 유지하되 아직 Pass 발급 기능이 없으므로 실제 발급 차단을 구현했다고 주장하지 않는다.

`pt_operations`가 상품 current head/불변 버전 사실/operation receipt를 소유한다. Organization은 Branch, Workforce는 Trainer 보상을 계속 소유한다.
상품을 Organization private Repo에 넣거나 Workforce 내부를 읽지 않는다. Audit는 중요 변경의 typed 저장을 소유한다.
Application UoW만 모듈 private adapter를 조합한다. HTTP/use_cases는 공개 ports/DTO만 소비한다.
새 내부 HTTP/queue/service/프레임워크·dependency upgrade는 없다.

## 입력·상품 상태

생성/완성 정보 수정은 상품명·가격·총횟수·Payment Type·명시적 strict bool is_service를 입력한다.
is_service는 기존 서비스⇒FIXED 제약의 검증 가능한 사실이며 이름/가격0으로 추정하지 않는다. 모든 FIXED가 서비스라는 역정의도 하지 않는다.
is_service=true이면 FIXED_AMOUNT만 허용하며 false는 RATE/FIXED 둘 다 가능하다. 서비스 가격을0으로 강제하는 새 규칙은 만들지 않는다.
Product에는 Trainer Rate/Fixed 지급액/Base Salary를 저장하지 않는다.

이름은 비어있지 않은 trimmed 문자열/제어문자 금지/200문자 표현 한도다. UUID가 식별자이며 이름 유일성·이름으로 병합을 발명하지 않는다.
가격은 기존 금액과 같은 canonical0+정수 원 문자열(최대1024자리 표현), 소수/음수/null/누락·자동반올림/절사/지수·JS Number 변환은 금지한다.
횟수는 canonical positive decimal string으로 입력/응답하고 PostgreSQL bigint의1..9223372036854775807 표현 범위를 사용한다. JSON Number를 거치지 않아2^53 초과도 정확히 보존한다. bool/숫자형 JSON/소수/0/음수/누락·leading zero를 거부한다. 업무상 정수라는 의미와 wire string 표현을 구분한다.
표현상 한도를 새 업무상 가격/수량 상한으로 부르거나 AS-IS C# 타입 한도로 대체하지 않는다.
처음 selling=true다. 정보 수정은 판매 상태를 그대로 유지하며 selling 입력으로 중단 상품을 재개하지 못한다. 중단은 별도 명령이다.
일반 변경에 새 필수 사유/추가 Master 승인 절차를 도입하지 않는다. 생성/실제 수정/중단은 전후 버전·Actor/Role/시점 typed Audit를 남긴다.

## 불변 상품 버전·공개 계약

Product ID는 서버 UUID, version은 positive bigint다. 실제 정보 변경/판매중단만 version+1하며 각 버전의 이름/가격/횟수/방식/서비스/판매상태를 보존한다.
큰 이름/금액 전체를 거대한 UNIQUE/FK identity에 넣지 않는다. 최대200문자 Unicode와1024자리 가격의 전후값은 B-tree index 한계를 넘길 수 있다.
버전 identity(org,product_id,version)로 불변 사실을 참조하고 operation/Audit는 작은 typed identity/전후 version FK로 결속한다.
create의 before 없음은 null이며 가짜version0/가짜가격0으로 표시하지 않는다. edit/stop은 before 버전을 필수로 한다.
nullable-before FK가 create의 핵심 Actor/상품/after 결속까지 건너뛰지 않게 nonnull core와 optional-before proof를 분리한다.
같은Org/Actor Master·Branch Context null, kind/changed/version delta/source version과 audit/receipt identity를 CHECK/FK로 검증한다.
현재 head는 실제 불변 version을 참조하고 DB null/UNKNOWN/nonfinite numeric 우회를 막는다.

향후 Pass 발급은 검증된 현재 판매가능 상품의 버전/가격/총횟수/방식 사실을 공개 port로 소비해 발급 당시 조건을 보존해야 한다.
이번에는 실제 Pass/입력가격의 별도 할인·지급 계산을 만들지 않는다. 상품 변경으로 과거 버전이나 미래 Pass 원본을 mutable current row에 종속시키지 않는다.
역사 상품 사실을 current Catalog 설정으로 재계산하지 않는다. Source version은 이 설계의 감사/receipt/미래 발급 근거이지 새 청구/결제 기능이 아니다.

후보 API: GET/POST /api/v1/admin/products, GET/POST /api/v1/admin/products/{id},
POST /api/v1/admin/products/{id}/stop, GET /api/v1/admin/product-operations/{uuid}.
신규 경로는 UUID X-Y3-Expected-Actor를 현재 인증 Caller.account_id와 대조한다. 헤더는 권한 근거가 아니다. 쓰기는 CSRF를 요구한다.
create는 operation UUID+완성 입력, update는 operation UUID+expected_product_version+완성 입력, stop은 operation UUID+expected_product_version이다.
canonical fingerprint는 원래 Actor/Organization/상품/명령 전체에 결속한다. operation namespace와 receipt 조회는 org/원래 Actor·현재 Master로 제한한다.
일치 replay는 현재 인가·원래 기한 검증 후 원래 committed version과 current 상태를 구분한다. 다른 Actor/payload는 비노출/충돌이다.
새 stale version은 같은 값/이미중단이어도409다. valid same-values update/이미중단 stop은 receipt만 만들고 버전/Audit/활동 시각을 바꾸지 않는다.
create replay는 중복 상품을 만들지 않고 처음 기록한 상품/버전과 현재 상태를 반환한다.
목록은 created_at,id의 안정 순서와 offset/limit을 쓰며 한 요청 안 count/rows는 일관되게 읽는다. 페이지 간 snapshot 고정은 보장하지 않고 각 요청의 현재 결과다. 목록 갱신 시 선택/편집 snapshot을 섞지 않으며 쓰기는 별도 현재 detail/version CAS를 요구한다. 전체 Audit 열람/불필요 개인정보를 노출하지 않는다.

## 권한·잠금·화면

기존 installation→Actor accounts/AuthSessions→Product head UPDATE/공개 version 조회 순서로 검증한다.
현재 실제 global installation 직렬화를 우회한 가짜 경합을 만들지 않으며 실제 PID/잠금 대기와 CAS로 중복·충돌을 증명한다.
current head/불변 version/operation/typed Audit는 하나의 UoW다. Audit 실패/현재 Master 축소/원래 idle·absolute 만료면 전부 rollback한다.
authenticate(touch=False)와 원래 snapshot/final confirm_actor를 사용하고 실제 변경 성공만 touch한다. Repository별 commit은 금지다.
조회/receipt/replay/no-op도 최종 현재 Actor/Org/원래 기한을 확인하며 이전 권한으로 후속 데이터를 읽지 못한다.
버전 기록시각은 서버 기록시각이며 물리 PostgreSQL commit timestamp라고 하지 않는다.

기존 스타일의 Master 관리 화면 /products와 메뉴를 추가한다. 서비스 구분과 방식 제약·가격/횟수 명시 입력/판매중단 상태를 정확히 표시한다.
정보 수정으로 판매가 재개되지 않으며 판매재개/삭제 버튼을 넣지 않는다. UI는 인가의 대체가 아니다.
자신이 읽은 Product/version·Actor/generation을 고정하고 늦은 응답이 더 높은 알려진 version을 덮지 못하게 한다.
pending UUID/body/대상/Actor를 유지해 중복 제출을 막고 ACK 불명은 같은 UUID로 대사한다. 원래 결과를 현재로 재적용하지 않는다.
fresh 조회 게시 성공을 확인한 뒤 현재값을 표시하며, 원래 receipt 조회 시점과 fresh 시점을 섞지 않는다.
receipt404는 원 UUID/명령을 재시도하는 근거이며 그 자체로 최종 실패를 단정하지 않는다. 재시도의 효과 없음이 확정된 업무 거부(예:409/conflict)는 원 Actor를 다시 확인한 뒤 pending을 종료하고 낡은 편집 snapshot을 무효화한다. 현재 detail의 fresh 게시가 성공해야 새 CAS 편집을 허용한다. 네트워크/5xx·receipt 조회 인가 실패·actor_changed는 미확정 상태와 원 명령을 유지하며 모든4xx를 일괄 종료하지 않는다.
긴 가격/이름은 기존 반응형 wrapping/input 규칙을 유지한다. 원화는 문자열로 다룬다.

## 0022·의존성·검증

새0022만 추가하고 원래0001–0021/ADR/lockfile·공통 conftest/historical/legacy/WF3/WF4/WF5 helpers는 불변이다.
설치 관계 AEX 선취·정확21↔22 head·정책2/target14를 검증한다. 새 Catalog가 기존 업무 데이터를 소유한다고 재해석하거나 RF/Base 자료를 초기값으로 되돌리지 않는다.
empty Catalog만 lossless inverse 가능하며 head/version/operation(no-op 포함)/Audit 등 어떤 새 사실이 있어도 파괴 downgrade 전 거부한다.
실제 parent21에서 정상 RF/Base/Home/계정 사실을 만든 뒤22 전후 원래 전체 행을 보존하고 parent21/current22 서로 다른 head 거부를 검증한다.
새 Catalog-local helper는 실제22 inverse+stamp21 뒤 기존WF5 helper를 사용하며 요청 target 도달 시 즉시 멈춘다. 자료를 지워 하위 guard를 우회하지 않는다.
원래 target의 DDL 전 거부를 검사할 때는 같은 rollback-only Connection에서 실제 target shape를 준비·확인한 뒤 해당 guard만 관측한다. 준비 inverse DDL을 guard 실행으로 계산하거나 단언을 없애지 않으며, 마지막 rollback 뒤 원래22 전체 행/shape 보존도 검사한다.

pyproject.toml은 tool.importlinter만 한정 확장 가능하다. project/dependencies/dev/uv/build 내용·uv.lock은 바꾸지 않는다.
새 PT를 layer/공개계약/업무 모듈 private 접근 금지에 연결하고 기존 누락 Workforce Base private 경로도 forbidden 목록에 포함한다.
기존8개 계약은 약화하지 않으며 새 모듈 경계의 정적 검사를 추가한다. UseCase/router에 업무 규칙이나 private SQL을 몰지 않는다.

현재 Master/타Org/NonMaster/겸임·ExpectedActor/CSRF, 필수값/0원/1회/서비스FX/큰값·Unicode 최대값,
중복create/두CAS·no-op/replay·stop후update중단보존·이전version불변·Audit/원래Actor기한 rollback을 선정한다.
typed FK/NULL/큰 index key 회피, 실제21↔22/빈inverse/새사실 lossguard/하위 원래guard 보존을 실제PG로 검사한다.
기존 native fixture의 짧은 Catalog profile/별도manifest를 한정 확장하고 원래TLS/NSS/소유권/90초 cap/cleanup을 유지한다.
이전모드 회귀는 영향 기반으로 선정하며 Catalog mode를 기존모드 성적으로 대체하지 않는다. raw exact keyset/literaltrue/같은 run/binary를 기록한다.
개발→동결→새 독립 fast/의미 있는 선정PG/native→설계자 인수→전담 한글 상세 커밋/일반 feature push다.
Source/raw SHA·HEAD/index/ref/trust/hosts·실제 node/실패·미실행/경고와 자기 process/schema/auto 환경 정리를 대조한다.
원본 DB 적용/배포·새 lifecycle tool/framework/dependency·Pass/PT 지급/정산·다른 Product OPEN/전역 PROPOSED는 범위 밖이다.

## 2026-11-27 후속 증분 — 기본 PT 이용권 발급 (로컬 인수)

Parent `bfa1e1dec5c136ece20b8ed1e968db8715ac2de4`, branch `codex/pt-pass-issuance`.
[담당 A-1/B-1](../product/product-decisions.md#review-20261127-pass-issuance-trainer), BR-OPS-010/B3/B4/J3/B6/T1/T2를 적용한다.
현재 Master Organization/BA 관리 Branch/Operator 업무 Branch를 독립 union으로 검사하고 활성 Issued Branch에서 발급한다.
같은 조직 활성 Member는 Home 활성과 무관하며, 최초 담당은 실제 활성 Trainer만이다. Trainer Home/IAM 로그인 상태는 각각 독립이다.
선택용 Member의 이름/전체 전화/현재 Home 및 UUID/version, Trainer 최소 식별·Home/version, 판매 상품/허용 지점만 공개한다.
일반 Member/Trainer/상품 관리·보상/계정 권한을 확대하지 않고 기존 공개 port/상위 UoW를 조합해 Import Linter 경계를 유지한다.

Member 검색은 nonempty bounded POST JSON이며 query는 repr/error·URL/일반 로그에 노출하지 않는다.
`strpos` literal 부분 검색으로 %, _와 빈 정규화가 무조건 browse가 되지 않으며 동명/동일 번호·Home도 UUID로 명시 선택한다.
UI는 지점 선택지 로딩 중 검색을 막고 짧은/빈 후보 페이지에서 종료한다. Actor/Org/Scope/세션 nonce 세대와 늦은 응답 차단을 적용한다.

PT Operations가 발급 원본/원 Actor receipt를 소유한다. operation UUID+전체 명령/Actor·Org·선택 Branch/Member/Trainer/Product version을 묶고,
기존 설치행 FOR UPDATE→Branch 사실→Member UPDATE/Home 재검증→Trainer SHARE/Product UPDATE→typed Audit/최종 Actor proof를 사용한다.
최종 proof는 최초 세션 기한을 유지하며 성공 시각에 Pass/receipt/Audit를 함께 seal한다. 이 Audit 시각은 발급 완료 시각이다.
receipt/replay는 원 Actor+현재 Issued Branch 발급 Scope로 읽고 새 발급 적격성/최신 Member PII를 재공개하지 않으며 seal/touch에 도달하지 않는다.
상품 version의 정수 가격/총횟수/지급방식/서비스 snapshot을 FK로 정확히 묶는다. numeric key는 기존1024자리 상한 안이며 이름/PII를 넣지 않는다.
최초 잔여=상품 횟수·최초 담당·실제 발급 완료 시각은 원 발급 사실이다. receipt/UI는 최초 잔여를 표시하며 이후 조정/교체의 현재 값으로 해석하지 않는다.
할인/금액·횟수 입력/증빙·별도 시작일/만료일·후속 조정/만료/담당 교체/PT 진행/정산은 구현하지 않는다.

새0025만 추가하고 기존0001–24/행·정책2 target14를 보존한다. 정확25 runtime, 실제24↔25 rows/shape inverse와
발급/receipt/Audit가 있으면 손실 거부하는 guard를 검증했다. 개발자는 정적/로컬 검사, 독립 tester는 동결 뒤 PG/native를 수행했다.
기존 native runner의 selector/manifest만 확장하고 TLS/NSS/bwrap/90초 cap과 소유 환경 정리는 유지한다.
2026-11-28 이 기본 발급 증분을 설계자가 로컬 인수했다.
독립 PG는 실제24↔25 smoke1·1차 신규33·교정 native1·잔여32의 고유67개이며 fast279와 native4(16/22/9/14)를 통과했다.
최초 native 실패는 option의 visible 대기 결함으로 CJS1파일만 교정했고 실제 제품 byte는 불변이며 소유 실행 환경 정리를 완료했다.
기존 경고2건(Starlette httpx TestClient 사용·anyio BlockingPortal alias 폐기 예정)은 남아 있고 전체 PG 전수검사·원본 DB/운영 검증은 범위 밖이며 다른 Product OPEN·전역 PROPOSED/ADR은 유지한다.
