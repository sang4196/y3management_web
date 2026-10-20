# WORKFORCE-001 — Trainer 최초 등록 최소 계약

2026-10-21. 상태: **좁은 구현 계약·독립 검증·설계자 로컬 인수 완료**.
기준 HEAD `475dd8a1baaf5d5561a1a66742db0c00c7731450`, branch
`codex/workforce-initial-registration`. 이번 문서는 W0의 좁은 계약만 정의한다.
설계자 검토 뒤 별도 implementation entry로 W0 구현에 진입했다. 독립 회귀에서 발견된
기존 MFA 설치 테스트의 잠금 관찰은 revision 3에서 보완했다. 같은 원인의 Reset 저장
테스트 관찰 보완만 revision 4의 좁은 범위로 추가 허용됐다. 최종 candidate3의 독립 fast122/새 단일 전체PG419·
같은 run native188을 인수했다. [결과](workforce-001-initial-registration-results.md)와
[판정](workforce-001-initial-registration-review.json)을 따른다. 기존 Product OPEN·ADR 상태와
[모듈 경계](module-boundaries.md)·[데이터/트랜잭션](data-and-transactions.md) 전체 초안을 승인하지 않는다.

## 1. 근거와 완료 단위

기준은 [Product](../product/README.md), [요구사항](../product/requirements.md)의
PR-005/007/021/029/030, [Business Rule](../product/business-rules.md)의
BR-OPS-024/028/029, BR-PAY-010/018/022/023이다.
Q/R/AA 승인에 따라 이름·전화번호·단일 Home과 명시적인 최초 보상 세 값·기본급 시작 월을
함께 저장한다. 명시 0원, Rate 정수 0~100, 시작 월부터 다음 변경까지 지속,
지원 연월 안에서 미래 월의 업무상 기간 상한 없음은 재질문하지 않는다.
[OPEN](../product/open-questions.md)의 MB-001/008, BR-010/012, ARCH-001/002,
MB-004, LEGAL-001 잔여와 [결정 게이트](decision-gates.md)는 유지한다.

완료 단위는 현재 정상 MFA 관리자의 실제 등록 명령 → Trainer aggregate → 최초 Home/보상
snapshot → operation → 두 typed Audit → 확정 후 최소 결과다. 필수 저장/감사 실패 때
사용 가능한 Trainer만 남지 않는다. 별도 Master 승인 절차는 없다.
계정 자동 발급/연결/역할, Home 이동/업무 상태 전이, 기본정보·일반 보상 수정,
Member/Pass/PT/지급/월 정산/비용 보고, production 및 운영 개인정보 처리는 제외한다.

### W0-READ-ACTIVE-001: 기존 G1과의 정합

[BR-OPS-016 G1](../product/business-rules.md#br-ops-016), MB-008 및
[G 승인](../product/product-decisions.md#review-20261012-g-batch)을 적용한다.
이전 QA 초안의 읽기/replay 활성 조건은 이 계약으로 정정한다. 새 사용자 결정이 아니다.

| 행위 | 현재 실제 Home 관리 인가 | Branch 활성 조건 | 업무/감사 신규 생성 |
| --- | --- | --- | --- |
| 새 operation의 Trainer 등록 | 필수 | 필수 | aggregate/snapshot/operation/감사 두 건 |
| 신규 배정 후보 | 필수 | 활성 후보만 | 없음 |
| GET Trainer / operation / 목록 | 필수 | 비활성도 허용 | 없음 |
| 같은 operation·같은 payload replay | 필수 | 비활성도 허용 | 없음 |
| 같은 operation·다른 payload | 현재 대상 인가 후 비교 | 비활성도 비교 가능 | 409, 없음 |

Branch 비활성을 계정 차단·Trainer 비활성으로 해석하지 않고 로그인에 새 활성 조건을
추가하지 않는다. 유효하지 않은 계정/철회된 역할/만료 인증을 복원하지 않는다.
현재 Scope 밖의 기존 결과는 404이며 전화·금액·감사 열람 권한을 늘리지 않는다.

## 2. 입력과 정확한 표현

POST는 다음 **일곱 업무 입력**과 `operation_id`를 모두 명시한다.

| 필드 | 계약 |
| --- | --- |
| name | 필수 문자열, raw/정규화 후 각각 200 Unicode codepoint 이하 |
| phone | 필수 문자열, raw/정규화 후 각각 128 Unicode codepoint 이하 |
| home_branch_id | 필수 UUID, 실제 대상 Scope와 상태는 서버 확인 |
| rate_percent | strict JSON integer 0~100, bool/float/string 거부 |
| fixed_amount_won | 정규 십진 정수 문자열, `0` 또는 `[1-9][0-9]{0,1023}` 전체 일치 |
| base_salary_won | 위와 동일; 명시 0과 미입력 구분 |
| base_salary_start_month | `YYYY-MM`, 0001~9999년·01~12월 |

이름/전화는 바깥 공백을 제거하고 빈 값·null·누락을 거부한다. 내부 표시는 유지하며
NFC/NFKC/대소문자 동일인 정규화를 하지 않는다. NUL·Unicode 제어문자(Cc)·단독 surrogate는
거부한다. 이름/전화 중복 금지, 국내 휴대전화 전용, E.164 강제, OTP, 전화 기반 병합은 없다.
길이 상한은 API 표현/자원 한계이며 업무상 전화 종류·동일인 정책의 확정이 아니다.

금액은 공백/부호/선행 0/소수/지수/NaN/Infinity/빈 문자열을 거부한다.
소수 절사·반올림·clamp·default는 없다. UI는 문자열을 그대로 보관/전송하고
`Number`, `parseFloat`, `parseInt`를 금액에 사용하지 않는다. 서버는 검증 후 정확한
Decimal 또는 정수로 다루고 SQL bind에서 float를 거치지 않는다. Decimal 정밀도 context를
통한 산술/quantize도 필요 없다. DB에서 읽은 정수 금액의 재표현은 지수 없는 문자열이다.

DB 금액은 typmod 없는 `NUMERIC NOT NULL`이며 각 열에 다음 CHECK를 둔다.

```sql
CHECK (amount NOT IN ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
       AND amount >= 0 AND amount = trunc(amount))
```

`NUMERIC(p,0)`의 검사 전 반올림을 사용하지 않는다. 1024자리 한계는 HTTP와 공개 command의
입력 자원 계약이고 DB 업무 금액 상한이 아니다. DB 직접 SQL의 1025자리까지 막는다고
주장하지 않는다. Rate는 integer CHECK 0..100. 월은 첫날 DATE로 저장하고
0001-01-01~9999-12-01 및 day=1 CHECK를 둔다. 무한 날짜도 범위 CHECK로 거부한다.
연월 문자열은 수동 고정폭 codec으로 왕복하여 플랫폼별 작은 연도의 `%Y` 차이를 피한다.

기본급은 **적용 시작 월부터의 설정**이다. 미래 시작 값을 현재 적용 급여라고 표시하지 않는다.
시작 전 월을 0으로 만들거나 미래 월별 행·종료 월을 생성하지 않는다. Rate/Fixed는 등록 확정
시점의 설정 사실이고 Base 시작 월까지 적용을 미루는 계약이 아니다. 실제 지급/월 계산은 제외한다.

### 기존 8192바이트 요청 예산

`backend/src/y3management/http.py`의 BodyLimit 누적 **8192 bytes**를 그대로 유지한다.
W0 예외/16KiB 증가/전체 인증 예산 변경은 없다. 초과하면 기존 413 `invalid_request`다.
고정 필드명, UUID 두 개, Rate 100, 월 7자, 금액 각각 1024자리, 이름 200+전화 128개의
최대 4바이트 Unicode scalar를 compact JSON으로 표현하면 UTF-8 3,590 bytes,
모두 surrogate pair escape로 표현해도 6,214 bytes다. 이는 QA 초안의 **정적 계산**이며
실제 BodyLimit 인수 결과가 아니다. 추가 공백/escape/중복 키 등으로 예산을 넘는 요청까지
허용한다는 뜻이 아니다. 정상 UI는 compact JSON.stringify를 사용한다.
JS UTF-16 `.length`와 Unicode codepoint 수를 혼동하지 않도록 Array.from 등으로 검사하며
서버 검증을 최종 기준으로 한다. 월/금액/Rate 입력은 처음에 빈 값이고 현재 월/0을 채우지 않는다.

## 3. 소유권과 공개 port

IAM은 현재 계정/관리자 역할·Scope·세션·MFA·만료 사실을 소유한다.
기존 `authenticate(management=True, touch=False)`와 CSRF 검사를 사용하며 요청 JSON의
role/org/actor를 신뢰하지 않는다. Master는 자기 Organization, Branch Admin은 현재 관리
Branch와 실제 대상 Home이 같은 범위다. 등록과 최초 보상 설정 인가를 각각 명시적으로 검사한다.

Organization의 기존 `Branch(id, code, name)`과 Master-only `require_branch`는 유지한다.
새 공개 계약은 다음으로 분리한다.

- `ScopedBranchFact(organization_id, branch_id, active, version)`:
  `lock_scoped_branch(caller, id)`가 현재 Scope와 존재를 확인하고 소유 adapter의 FOR SHARE로
  잠근다. 비활성도 반환한다. 없는/Scope 밖이면 404다.
- `require_assignable(fact)`는 **새 등록에만** active를 요구하며 비활성이면 409다.
- `confirm_scoped_branch(caller, fact)`는 같은 UoW의 기존 lock 아래 현재 Scope·org/id/version과
  상태 사실을 재확인한다. active=true를 공통 전제조건으로 쓰지 않는다. 새 등록의 마지막에는
  별도로 `require_assignable`을 다시 호출한다.
- `list_assignment_candidates(caller, offset, limit)`는 현재 Scope의 활성 후보만
  `id/code/name/version`으로 반환한다. 기존 지점 조회의 필터를 바꾸지 않는다.

Workforce는 Trainer/현재 Home/업무 활성/version/초기 설정과 snapshot/operation을 소유한다.
`RegisterTrainer`는 일곱 업무값과 operation만 받는다. 상위 Service가 검증한 Caller와
ScopedBranchFact를 넘기고 `register_or_replay`는 타입 구분된 created/replayed 결과 및
최초 변경 사실을 반환한다. DBSession/Repository/ORM을 공개 계약으로 내보내지 않는다.

`registration_hint(org, operation)` 및 대상 조회 hint는 잠금 대상 탐색만 위한 내부 값이다.
인가된 응답이 아니며 hint를 최종 사실로 믿지 않는다. 관리자용
`get_managed_identity`, `get_managed_registration`, `list_managed_identities`는 실제
현재 Home에서 Scope를 검사한다. Branch 비활성을 이유로 기존 행을 숨기지 않는다.

I1의 신뢰 내부 `TrainerIdentityFact(trainer_id, organization_id, home_branch_id, active, version)`는
관리자 조회와 분리한다. 이름/전화/보상 값이 없다. 이후 상위 인증 조정자가 검증된 IAM
자격증명과 서버 소유 연결에서 얻은 org/id로 호출하는 `resolve_identity` 계약이며
관리자 Caller가 있어야 로그인 가능한 순환을 만들지 않는다. 미인증 HTTP나 임의 ID 조회
endpoint로 노출하지 않는다. I1 연결/로그인 구현과 잠금 조합은 후속이다.

Workforce가 IAM/Organization/Audit 내부 테이블을 SELECT하지 않는다. 상위 Service가 공개
port를 조합하고 UoW 구성점만 private adapter를 공유 DBSession에 연결한다.
composite FK는 저장 무결성 제약이며 다른 모듈 내부 읽기 예외가 아니다.

## 4. 저장과 필수 감사

| 소유 모듈 / 저장 | 최소 내용 |
| --- | --- |
| Organization / organization_branches | active boolean NOT NULL DEFAULT true, row_version bigint NOT NULL DEFAULT 1 CHECK >0 추가 |
| Workforce / workforce_trainers | UUID PK, org, 단일 Home, name/phone, active, version, DB created_at, 세 초기값·base_start_month 모두 NOT NULL |
| Workforce / workforce_initial_snapshots | Trainer별 하나, org·최초 Home·초기 세 값·시작 월·version 1·등록 시각 보존 |
| Workforce / workforce_registration_operations | PK(org, operation_id), Trainer UNIQUE 참조, 원래 creator_account_id/created_at, canonical_version=1, 32-byte fingerprint |
| Audit / audit_workforce_initial_events | 등록/초기설정 두 종류 typed 행, org/operation/Trainer/실제 actor·관리 role/actorBranch/targetHome·시각/version |

Trainer의 `(organization_id, home_branch_id)`는 Organization composite FK, `(org,id)`는 UNIQUE다.
snapshot/operation/Audit도 같은 org의 대상 composite FK로 제한한다. actor는 같은 org의
실제 IAM account FK로 보존한다. Trainer를 가짜 IAM target account로 만들지 않는다.
이름/전화에 UNIQUE를 두지 않고 phone/금액은 일반 로그나 IAM 감사 응답에 포함하지 않는다.
등록 당시 Home만 보존하며 등록 전의 과거 소속을 추정하지 않는다.

현재 Branch schema에는 active 정보가 없고 모든 기존 Branch가 사용 가능한 의미였다.
`true/version1` backfill은 이 의미를 표현하는 이행이지 현실 영업 상태의 인증이 아니다.
이름/AS-IS 추론이나 import로 상태를 만들지 않는다. 실제 원본 비활성 사실이 발견되면
해당 매핑을 보류하고 true로 덮지 않는다. 기존 Branch 생성 INSERT는 필요한 구현 범위에서
명시 column INSERT로 바꾸어 추가 열과 호환시킨다. 상태 전이 관리 UI는 제외한다.

Audit 공개 port에는 `append_trainer_registered(TrainerRegistered)`와
`append_initial_compensation(InitialCompensationSet)` 두 typed 명령만 추가한다.
기존 Event/append/IAM 감사 조회는 그대로 둔다. 등록 이벤트의 보상 열은 NULL,
최초설정 이벤트의 before는 NULL이고 after의 세 값·월은 필수다. 명시 after=0과
미입력/before 없음은 다르다. actor의 실제 선택 관리 역할과 당시 관리 Branch, 대상 Home을
각각 기록한다. 동일 org/operation/event_kind UNIQUE로 각 종류 최대 한 행이다.
이 테이블은 기존 IAM 감사 읽기에 포함하지 않고 W0에서 새 감사 조회 API도 만들지 않는다.
이름/전화 원본 JSON·arbitrary payload·범용 Audit framework는 없다.

### 강제 경계

**DB 강제:** 필수 초기값 NOT NULL, 금액 finite/정수/0 이상, Rate/연월/이름·전화 길이와
비어있지 않음 CHECK, 조직/Branch/대상/actor FK, 단일 Home, operation 고유,
Trainer별 snapshot 최대 하나, typed Audit의 필수/금지 열과 종류별 최대 한 행.

**Application-UoW 강제:** snapshot/operation/감사 두 행의 반드시 존재함, 최초 snapshot과
aggregate 값 일치, 원래 creator/이력의 변경 없음, 현재 권한·행위별 활성 조건·최종 DB 시각,
canonical 비교, 1024자리 입력 제한. 공개 명령에는 snapshot/원본 operation 수정·삭제가 없다.

UNIQUE만으로 필수 감사가 존재한다고 주장하지 않는다. privileged 임의 SQL의 삭제/변조까지
막는 reciprocal/deferred constraint trigger는 추가하지 않는다. Application 경로의
저장·각 감사 실패 주입과 DB 직접 제약 테스트를 구분한다.

## 5. Operation 재시도와 결과 불명

canonical v1은 순서가 고정된 일곱 normalized 업무 필드의 compact UTF-8 JSON이다.
UUID는 canonical lower-case, Rate는 정수, 금액은 정규 문자열, 월은 고정폭이다.
org는 operation namespace이며 actor/CSRF/operation은 payload에서 제외한다.
버전과 SHA-256 fingerprint를 내부 비교용으로 저장한다. JSON key 순서/바깥 공백 정규화
차이는 같은 명령이며 실제 필드 차이는 다른 명령이다. raw PII JSON은 저장/감사하지 않는다.
fingerprint는 인증·동일인 증명·전화 검색키·비밀 은닉 수단이 아니다. 응답/로그에 내보내지
않으며 HMAC/새 secret 관리 체계를 도입하지 않는다.

1. 같은 org+operation이 없으면 지정 Home 관리 Scope와 active를 확인해 새 등록한다.
   commit 확인 후 **201**이다.
2. 이미 있으면 요청이 주장한 Home이 아니라 **기존 Trainer의 실제 현재 Home**에서 먼저
   현재 관리 권한을 확인한다. 비활성 Home도 허용한다. 같은 canonical payload이면 **200**과
   기존 최소 결과를 반환한다. 원래 creator/등록시각/snapshot/감사 두 행을 그대로 보존한다.
   현재 Scope가 맞는 다른 관리자도 replay할 수 있다.
3. 현재 대상 인가 후 다른 payload이면 **409 operation_conflict**다. Scope 밖이면 먼저404로
   존재/차이를 숨긴다. 같은 operation의 요청 Home 변경은 이동 명령이 아니다.
4. commit ACK 유실은 기존 **503 commit_outcome_unknown**을 사용한다. 상태 GET(no-touch)으로
   확인하거나 같은 payload/operation으로 재시도한다. 자동 새 operation 생성은 없다.
   새 operation과 동일 전화는 별도 등록이며 자동 병합하지 않는다.

201 생성과 200 성공 replay는 최종 검증 뒤 실제 actor 세션의 정상 활동 시각을 갱신할 수 있다.
동일 payload 경합의 후행 200은 실패한 패자가 아니다. 다른 payload409/인가 실패/감사 실패는
활동 시각까지 rollback한다. ACK 유실은 실제 commit됐을 수 있어 활동 rollback을 보장하지 않는다.
replay는 Trainer/설정/Home/감사 row를 새로 만들거나 초기 설정 권한 변경을 실행하지 않는다.

## 6. 공유 UoW와 잠금/최종 검사

순서는 **IAM installation gate → actor account → AuthSession → Branch(UUID 정렬) →
Workforce operation → Trainer(UUID 정렬)/snapshot → Audit**다. 복수 account가 필요해지는
후속 명령은 기존 UUID 정렬 규약을 먼저 따른다. 새 lock을 마지막 검사에서 역순 획득하지 않는다.

1. strict 입력 검증 뒤 UoW 안에서 처음부터 IAM management=True/touch=False로 잠그고
   현재 계정·MFA·epoch·pending·관리 역할·CSRF를 검사한다. 사전 touch로 idle을 연장하지 않는다.
2. 기존 operation/대상 hint를 org 안에서 읽는다. existing이면 실제 Home, new면 지정 Home의
   scoped Branch fact를 잠근다. 그 뒤 operation/Trainer를 잠그고 hint의 org/Home/version과
   실제 값을 재검증한다. 불일치하면409 rollback 후 fresh retry하며 다른 Branch를 역순 잠그지 않는다.
3. new만 assignable-active와 등록/최초 보상 인가를 각각 확인하고 모든 저장·두 감사를 수행한다.
   replay는 현재 기존 결과 인가 및 payload 비교만 하고 비활성 Home에서도 새 저장을 하지 않는다.
4. 감사/DB 대기 후 기존 잠금 안에서 현재 actor 인증/역할/Scope·CSRF·idle/absolute를 다시
   PostgreSQL clock_timestamp 기준으로 검증한다. scoped Branch의 org/id/version/상태 사실,
   실제 Trainer Home/version도 확인한다. new만 다시 active를 요구한다. 성공할 actor만 touch한다.
5. UoW commit 확정 후 응답한다. 필수 실패는 전체 rollback한다. 이미 실패한 DB transaction에서
   IntegrityError를 잡고 계속하지 않는다. unique 충돌은 rollback 후 새 UoW의 같은 operation
   조회/재시도로 분류한다. C2와 타 계정 세션/보안 상태는 변경하지 않는다.

현재 management gate는 동시 등록을 직렬화하고 DB operation UNIQUE가 최종 중복을 방어한다.
Branch SHARE는 상태 UPDATE와 충돌한다. 비활성 변경 먼저면 새 등록 거부, 등록 먼저면
commit 뒤 비활성화 가능하다. **기존 읽기/replay는 비활성 먼저여도 현재 Scope 아래 허용**한다.
권한 철회 먼저면 모든 해당 요청을 거부하며 등록 먼저 확정된 업무를 이후 철회로 소급 취소하지 않는다.

GET/상태/목록/후보는 no-touch다. 목록은 현재 Scope로 Workforce에서 페이지와 total을 산출하고
Branch active로 기존 Trainer를 필터링하지 않는다. 해당 page의 hint Home을 UUID 순으로
scoped lock한 뒤 Trainer를 순서대로 잠가 재검증한다. hint 불일치 시 재조회/충돌 처리하며
일부 누락을 정상 페이지로 반환하지 않는다. 최종 현재 actor를 다시 확인한다.
미구현 Home 이동과의 완전한 동시성 인수는 W0의 성공으로 주장하지 않는다.

## 7. HTTP·DTO·최소 UI

| Endpoint | 성공 / 범위 |
| --- | --- |
| POST /api/v1/admin/trainers | 201 생성, 200 같은 명령 replay |
| GET /api/v1/admin/trainer-registrations/{operation_id} | 현재 실제 Home에서 인가된 기존 결과 |
| GET /api/v1/admin/trainers/{trainer_id} | 현재 실제 Home에서 인가된 최소 식별 |
| GET /api/v1/admin/trainers?offset&limit | offset>=0, limit1..100, 현재 Scope 기존 목록 |
| GET /api/v1/admin/trainer-home-candidates?offset&limit | 현재 Scope 활성 배정 후보 |

POST 결과 allowlist는 `{operation_id, trainer:{id,name,home_branch_id,active,version}}`다.
여기서 active는 **Trainer 업무 상태**다. 목록/직접 조회는 trainer 부분만 노출한다.
전화/금액/fingerprint/원본 payload/계정/설정 링크가 없다. 별도 보상 확인 GET은 W0에 넣지 않고
제출 전 입력 검토와 등록 결과로 최소화한다. 후보는 id/code/name/version만 반환한다.
클라이언트 org/role/account_id/created_at/상태 및 unknown 필드는 거부한다.

기존 HTTPS canonical origin, Cookie, CSRF, application/json, no-store, BodyLimit 경계를 재사용한다.
401 인증/만료,403 행위/CSRF,404 Scope 밖/없음,409 비활성 신규배정·충돌,
413 전송 크기,422 입력,503 DB/commit 불명을 기존 오류 envelope와 맞춘다.
Pydantic hide_input_in_errors만으로 응답 비노출를 가정하지 않고 실제 FastAPI validation
응답의 input/ctx 원문과 일반 로그를 확인한다. 필요한 오류 sanitation은 W0 구현 entry 범위에
명시하고 기존 인증 오류 의미를 바꾸지 않는다.

최소 관리자 화면은 기존 실제 MFA 로그인 뒤 일곱 필수 입력·등록 버튼·최소 결과/기존 목록을 제공한다.
Branch Admin 후보는 자기 활성 지점, Master 후보는 자기 조직 활성 지점이다.
지점 비활성 뒤 후보에서 빠져도 기존 목록/결과 조회/replay는 사용 가능하다.
금액·Rate·월은 빈 값부터 명시 입력하고 미래 기본급을 현재 급여라고 표시하지 않는다.
명시 새 등록 전까지 같은 제출의 operation을 유지한다. 성공 시 계정 발급 완료로 표시하지 않는다.
테스트에는 가상 개인정보만 쓰고 DOM에는 안전한 textContent 등으로 표시한다.

## 8. Forward migration과 Import Linter 변경 범위

다음 forward **0010**을 후보로 하며 실제 구현 진입에서 현재 head를 다시 확인한다.
기존0001~0009/env.py/dependency/lock은 유지한다. 새 Organization 열과 Workforce/typed Audit
테이블·제약만 추가한다. 기존 데이터/FK와 IAM 흐름을 보존한다.

Downgrade는 신규 aggregate/snapshot/operation/감사 중 한 행이라도 있거나 Branch에
active=false 또는 row_version!=1 사실이 있으면 정보 손실로 거부한다. 검사와 제거 사이
동시 write를 막도록 maintenance transaction에서 IAM gate/account/session→Organization Branch→
Workforce operation/Trainer/snapshot→typed Audit의 순서로 필요한 table lock을 획득한다.
FK 참조 테이블/DDL lock도 이 순서와 기존 IAM migration 순서에 맞게 구체 SQL을 검토한다.
전용 maintenance 연결의 lock timeout 실패는 원상 rollback이며 live 무중단 migration 인수가 아니다.
모든 신규 테이블이 비고 Branch가 true/version1일 때만 역순 제거한다.
거절 시 전체 transaction과 revision 유지, 기존 이력 보존을 검사한다.
기존 테스트의 고정 head 상수가 필요하면 별도 exact 예외 검토를 받으며 부분 commit/거절 완화는 없다.

`backend/pyproject.toml`의 기존 Import Linter **일곱 계약의 의미를 보존**한다.
구현 시 기술 설정 변경은 다음에 한정한다.

- exhaustive layers에 workforce를 uow 아래·organization 위에 추가하고 나머지 순서를 유지한다.
- use_cases/http의 private 금지 목록에 Workforce application/infrastructure 등 실제 private 모듈을
  추가한다. 기존 selector 삭제나 ignore 범위 확대는 없다.
- public contract의 SQLAlchemy/HTTP/driver 금지에 workforce.public을 추가한다.
- IAM/Organization/Audit의 기존 격리 규칙에 새 Workforce package 금지를 추가한다.
- Workforce outbound는 IAM/Organization의 public fact만 허용하도록 private 금지 규칙을 추가하고
  Audit import를 금지한다. Audit 조합은 상위 Service에서 한다.

새 public DTO는 Audit 타입을 import하지 않고 자체 immutable 변경 사실을 반환하며 Service가
Audit 공개 명령으로 매핑한다. 새 package 추가가 dependency upgrade는 아니다.
Import Linter는 SQL 문자열의 소유권까지 검사하지 않으므로 adapter SQL 별도 검토가 필요하다.
IAM에서 Workforce로 역방향 private import를 만들지 않고 향후 I1도 상위 조정자가 연결한다.

## 9. 구현 후 검증 계약과 실제 수행 범위

아래는 검토 범주다. 개별 사례의 실제 실행·정적 검토·미인수 범위는 연결된 결과와 판정 문서를 기준으로 한다.

| 수준 | 필수 사례 |
| --- | --- |
| DB 없는 검사 | strict 타입/누락/0/1024·1025자리/Unicode 길이/연월 경계·먼 미래, canonical equality, DTO allowlist, Import Linter 경계 |
| 실제 PostgreSQL | 실제 관리자 준비·로그인 등록, DB 제약/각 필수 저장·감사 실패 rollback, 정확한 큰 금액/NaN/Infinity/소수 거부, ACK 유실·동일 operation, migration/이력·Branch 정보 손실 보호 |
| 독립 연결 경합 | 실제 별도 MFA 관리자 같은 payload201+200/한 묶음·성공 활동, 다른 payload201+409/실패 활동 불변, actor 철회·Branch 비활성 양쪽 선후, 잠금/감사 대기 뒤 idle/absolute 만료 |
| 실제 HTTPS 브라우저 | 기존 Master/Branch Admin 로그인부터 실제 form 등록·기존조회, 명시0/큰금액/먼미래/빈값, 전송8192·8193와 chunked 경계, CSRF/직접ID Scope, 더블클릭/operation 유지 |

W0-READ-ACTIVE-001 필수 사례: 실제 등록 뒤 같은 Home을 비활성 fact로 전환한 fixture에서
유효 관리자 GET/operation/list/replay200이 성공하고 aggregate/snapshot/operation/감사 수·원본값이
불변임을 확인한다. 새 operation 등록은409이고 신규 후보에서 제외된다.
다른 payload는 현재 대상 인가 후409, 다른 Scope404/무효 계정401은 그대로다.
비활성 사실 fixture는 미구현 상태 UI를 인수했다고 주장하는 근거가 아니며 Trainer 등록 성공
경로를 raw SQL/fake Caller로 대체하지 않는다. 실제 브라우저 정상 흐름도 함께 검사한다.

기존 Foundation/IAM010 결과를 W0 또는 실제 Operator/Trainer 로그인·W1/I1/I2/PT/정산 검증으로
확대하지 않는다. 개발→독립 테스트→설계자 검토→전담 커밋 세션 순서를 유지한다.
기존 pytest/fixture의 소유 QA 폴더·프로세스/schema 정리와 최소 증거 절차를 사용하고
새 수명주기 도구를 추가하지 않는다.

## 10. 후속과 현재 인계

I1은 실제 Trainer identity에 신규 계정/본인 설정/로그인을 연결하는 별도 증분이다.
I2의 기존 계정 겸임·역할 추가/회수와 역할 없는 계정 로그인 정책을 W0 선행 질문으로 만들지 않는다.
현재 최소 계약에 새 Product 질문은 없다. 실제 추가 업무 금액 상한/전화 종류 제한/OTP 등을
추가하려는 경우에만 해당 OPEN을 별도 결정한다. 운영 보존/배포 승인은 별도다.

초기 계약 작성 단계는 설계 문서와 QA contract-result/progress에서 종료했으며 당시에는 구현/runtime/Git 작업을 하지 않았다.
이후 별도 구현 entry와 독립 검증 entry로 진행했고 최종 인수 근거는 연결된 결과/판정 문서에 기록한다.

## 구현 진입 추가 guard (2026-10-21)

좁은 계약에 대한 root 구현 entry가 발급되었다. 민감 form은 명시적인 POST action을 두고
submit handler 연결 전까지 버튼/fieldset을 disabled로 유지한다. JavaScript가 없거나 실패해도
GET query/history에 이름·전화·금액을 보내지 않는다. W0 validation 오류는 명시적인 일반
422 envelope로 sanitation하며 기존 인증 오류 의미는 유지한다. 실제 응답을 검사한다.
GET/상태/목록은 세션 활동·security GC·업무/감사 변경이 없고, 성공 replay만 실제 actor
활동 갱신을 허용한다. G1 비활성 기존 조회/replay와 신규 활성 배정은 계속 분리한다.

### 구현 세부 정합

실제 Alembic revision은 `0010_workforce_initial`(22자), 파일은
`0010_workforce_initial_registration.py`다. 기본 version column 범위를 늘리지 않는다.
canonical v1은 `[1,name,phone,home_branch_id,rate_percent,fixed_amount_won,
base_salary_won,base_salary_start_month]` 고정 순서 JSON 배열의 UTF-8 SHA-256이다.
초기안의 고정 필드 JSON과 동일한 명령 비교 의미이며 원문 payload 저장은 없다.
현재 등록 UI는 100개 page를 마지막까지 순차 로드해 선택 후보를 조용히 잘라내지 않는다.
스마트폰 viewport와 같은 origin 외부 CSS로 field 폭·간격을 제공하며 기존 CSP는 유지한다.
