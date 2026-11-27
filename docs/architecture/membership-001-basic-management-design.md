# MEMBERSHIP-001 — 회원 기본관리

Status: **IMPLEMENTED / VERIFIED / ACCEPTED — LOCAL LIMITED MEMBERSHIP-001** (2026-11-27).
Parent `62857f75cca460d28465dc7fb8db61060dcfc80f`, branch `codex/membership-basics`.
[MEM-1=A-2 / MEM-2=B-1](../product/product-decisions.md#review-20261127-membership-basics), PR-002/004/027/030,
BR-OPS-006/020/021/022/011과 기존 I2/J1/J2/J3를 입력으로 한다. 정책은 승인됐으며 이 문서의 한정 기능을 설계자가 로컬 인수했다.
설계자·독립 tester·깃 담당자가 검토했고 설계자가 이 한정 범위의 기술 진입을 승인했다. QA root-entry-approval.json이 근거다. 구현·동결·독립 검증과 최종 변경 검토를 마쳤고 설계자가 로컬 인수했다. [결과](membership-001-basic-management-results.md)와 [최소 근거](membership-001-basic-management-review.json)를 따른다.
다른 Product OPEN/전역 모듈·UoW PROPOSED 및 ADR-0001–0005의 실제 Status/범위를 변경하지 않는다.

## 이번 증분과 승인 경계

등록, 현재 편집 권한 범위의 최소 대상 목록/상세, 이름·전화번호 완성값 수정, 자기 작업 receipt를 제안한다.
목록/상세는 BR-OPS-021의 허용 편집 대상을 고르고 현재값을 확인하는 경로다. 일반 전체 회원 열람 권한을 추가하지 않는다.
응답은 Member UUID/이름/canonical 전화번호/Home Branch 최소 식별·이름/Member active/Home active/version/기록시각으로 제한한다.
Operator의 Organization 전체 검색, Pass 발급용 타 Home 검색, Trainer 담당/개별 지원 회원 조회를 구현하지 않는다.

기존 승인된 BR-OPS-022의 명시적 비활성화/재활성화를 한정 포함하는 안을 제안한다. 실제 등록→관리자 비활성화→
현재 권한의 이름·전화 수정→관리자 재활성화를 사용해 MEM-2를 검증하고 DB에 상태만 직접 넣은 검사로 대체하지 않기 위해서다.
최초 정상 등록은 active=true, 상태 변경은 별도 명령이며 일반 수정으로 상태를 받지 않는다. 같은 Member UUID/Home을 유지한다.
상태 명령은 기존 Master/현재 Home Branch Admin만 허용한다. Operator/Trainer 단독에는 추가하지 않는다.
상태 변경 자체는 Branch 활성화나 Home 신규 배정이 아니며 기존 Home 비활성 상태를 유지한다.
새 필수 사유·별도 승인 단계·확인 SMS를 만들지 않는다. 구현 여부를 기술 검토할 뿐 J2/J3를 새 사용자 승인 대상으로 돌리지 않는다.

Member 자체 또는 기존 Home이 비활성이어도 현재 허용 Scope의 이름·번호 수정을 허용하고 두 상태를 유지한다(MEM-2).
신규 Home 배정은 같은 Organization의 활성 Branch만 허용한다. 비활성 Home의 기존 정보를 고치는 것과 신규 배정을 구분한다.
Home 이동/역사 Home 정정·개별 지원·Pass/PT/지급/추가실적/정산·MemberLogin·일괄 내보내기/삭제는 범위 밖이다.
J3의 비활성 Member 새 Pass/비활성 기간 수업 차단 정책을 보존하되 아직 없는 Pass/PT 실행 차단을 구현·검증했다고 보고하지 않는다.
이번 상태 버전은 서버 기록 이후의 사실만 보존한다. 과거 실제 수업 당시 상태 조회/확인 불가·정정 정책을 선행 구현하지 않는다.

## 이름·국내 휴대전화의 canonical 계약 제안

이름은 trimmed nonempty Unicode 문자열 1..200문자, 제어문자/서로게이트 금지로 제안한다. 내부 공백과 대소문자를 보존하며 이름 유일성은 없다.
전화는 필수 문자열이다. raw 입력 표현 한도64문자에서 ASCII 공백과 하이픈만 구분기호로 허용하고, 제거 후
`010[2-9][0-9]{7}` 또는 같은 번호의 `+8210[2-9][0-9]{7}`만 허용하는 안이다. +82형은 앞의 국내 trunk 0을 복원해
11자리 `010…` ASCII 숫자로 저장/응답한다. 화면은 `010-XXXX-XXXX`로 표시할 수 있다. 표기 차이만으로 실제 변경을 만들지 않는다.
유선/070/다른 국가번호, 짧거나 긴 값, 구형01X, 숫자 JSON/bool/null/빈값, 임의 문자·확장번호/Unicode 숫자·줄바꿈은 거부한다.
`+82(0)10`, bare `8210`, 국제접속번호 `0082` 등 지원하지 않는 표현은 추측 변환하지 않는다. 범위/길이와 canonical을 Backend에서도 검증한다.
+82가 한국 휴대전화의 다른 표기라는 계약은 외국 휴대전화 허용과 다르다. 통신사/번호 가입·도달 가능성/소유자 신원은 판정하지 않는다.

2026-11-27 확인한 1차 근거: [과학기술정보통신부 전기통신번호관리세칙](https://www.law.go.kr/LSW/admRulLsInfoP.do?admRulId=35486&efYd=0)의
이동전화 식별번호010 및 국번호 부여의 `010-ABYY-YYYY`, A=2..9 표현과 [ITU 대한민국 국가번호](https://www.itu.int/ITU-T/inr/nnp/)의 +82를 확인했다.
공식 번호 범위를 위 문법으로 옮기는 것은 기술적 해석/추천이다. 법령의 특수 예외까지 모든 번호의 사용 가능성을 증명한 것은 아니다.
통신사업자별 현행 할당 목록을 복제하거나 전화 라이브러리/외부 API 의존성을 추가하지 않는다. 구형01X를 임의010으로 바꾸지 않는다.
향후 실제 국내번호 범위 변경·특수 번호 지원 필요는 해당 근거/요구를 분리 검토하며 승인되지 않은 외국/유선 범위를 구현하지 않는다.

이름/전화/Home은 생성 시 모두 명시한다. 이름·전화 수정은 둘의 완성값만 받고 미변경 값도 fresh detail에서 유지한다.
Home/state/role/org를 정보 수정 body로 받거나 missing을 빈값·기본값으로 보정하지 않는다. Strict 입력 DTO는 extra field를 거부한다.
전화는 unique key가 아니다. 같은 canonical 번호/이름을 여러 Member UUID가 사용하며 자동 병합·첫 결과 자동 선택·관계/권한 공유는 없다.
동일 번호 존재 여부를 별도 중복 검사로 노출하지 않는다. 같은 번호의 독립 create는 서로 다른 UUID, 같은 operation replay만 같은 Member다.
전화/이름·raw body·fingerprint/SQL parameter·cookie/CSRF를 오류/일반 로그/진단 근거에 출력하지 않는다. DTO repr도 민감값을 숨긴다.
422 invalid_request/404 not_found/403 forbidden/409 conflict 등 기존 일반 코드를 재사용하고 제출 값을 echo하지 않는다. 인가된 편집 DTO 외 개인정보/감사를 공개하지 않는다.

## 소유권·공개 ports·상위 UoW

이번 책임만 `membership` 모듈로 추가한다. Member current head/불변 버전/operation receipt는 Membership의 단일 쓰기 소유다.
IAM은 현재 Actor/독립 역할·Scope·정책/원래 기한, Organization은 실제 Branch 소속·활성/row version, Audit는 typed 중요변경 저장을 계속 소유한다.
Membership는 IAM/Organization 공개 facts만 소비하고 다른 모듈 private Repo/ORM/테이블을 직접 읽거나 수정하지 않는다.
`use_cases.Service`는 공개 ports/불변 DTO로 조정하며 HTTP는 입력/응답·Actor 전달만 한다. 업무 규칙/SQL을 router에 넣지 않는다.
기존 `UnitOfWork.open()`만 동일 Session에 private adapter를 조립하고 한 번 commit/rollback한다. 모듈별 commit·독립 DBSession을 추가하지 않는다.

후보 불변 DTO: `MemberValues(name, phone)`, `Member(id, version, values, home_branch_id, active, recorded_at)`,
`MemberPage(items,total)`, `MemberCommand(operation_id,kind,member_id?,expected_member_version?,home_branch_id?,values?)`,
`MemberResult(operation_id,kind,changed,committed_member,current_member)`, `MemberMutation`의 작은 typed identity다.
committed의 이름/번호/Home UUID/Member active/version/기록시각은 원래 버전 사실이다. 두 Member DTO의 home_branch_name/home_active는
응답 시점 Organization의 현재 표시 metadata이며 과거 Branch 이름/상태를 추정하지 않는다. UI도 현재 Home 상태로 표시한다.
kind는 create/update/deactivate/reactivate이며 create만 Home/완성값을 받는다. update만 완성값, 상태 명령은 대상/기대version만 받는다.
`MembershipPort`는 list/get/operation/change/confirm/seal을 제공한다. DB/HTTP 객체를 노출하지 않는다.
Audit 공개 `MemberEvent`/append_member는 org/Member/원 Actor/실제 actor_role·branch context/종류/전후 version/changed/기록시각을 받는다.
큰 이름·전화 원문은 거대한 UNIQUE/FK identity나 일반 Audit payload에 반복 복사하지 않고 인가된 불변 버전 사실로 연결한다.

기존 Organization의 `_scope`/lock_scoped_branch/assignment_candidates는 Master·Branch Admin 중심이다.
이를 전 모듈에서 넓히거나 Operator를 가짜 master/branch Caller로 바꾸지 않는다. Organization 공개 port에 Membership용
`lock_member_branch(caller, branch_id)`/`confirm_member_branch(caller,fact)`/`member_assignment_candidates(caller,offset,limit)`를 한정 추가한다.
현재 검증된 Caller에서 Master 또는 일치 BA/Operator Scope를 확인하고 같은 Org의 실제 ScopedBranchFact를 SHARE 잠금해 반환한다.
후보는 활성 Branch만, lock fact는 기존 비활성 Home도 반환하고 create에서만 require_assignable을 적용한다.
Membership가 명령별 실제 역할을 최종 검증하며 state는 더 좁은 관리자 범위를 별도로 요구한다. 원래 Organization 공개 계약의 의미는 유지한다.
Branch 표시에 필요한 최소 이름/식별도 이 공개 계약에서 얻고 Membership SQL의 Organization table JOIN으로 우회하지 않는다.

## 현재 역할·Scope와 응답 게시

모든 신규 API는 필수 UUID `X-Y3-Expected-Actor`를 현재 인증 Caller.account_id와 대조한다. 헤더/클라이언트 role/org/branch는 권한 근거가 아니다.
현재 인증은 `authenticate(touch=False)`와 RoleActorSnapshot을 사용한다. 생성 지정 Home, 기존 대상의 현재 Home과 같은 Org를 확인한다.

| 현재 역할 | create / 최소 편집대상 list·detail / 이름·번호 update / 자기 receipt | deactivate/reactivate |
| --- | --- | --- |
| Master | 자기 Organization | 자기 Organization |
| Branch Admin | 자기 현재 관리 Branch = 지정/현재 Home | 자기 현재 관리 Branch = 현재 Home |
| Operator | 자기 현재 업무 Branch = 지정/현재 Home | 불가 |
| Trainer 단독 | 불가 | 불가 |

BA(A)+Operator(B)는 등록·편집 대상 조회/정보수정에 A∪B를 사용한다. B의 요청은 Operator로만 인가·감사하며 BA 권한을 B로 늘리지 않는다.
A와 B가 같아도 중복 목록 행을 만들지 않는다. 실제 허용 역할 중 감사 선택은 Master→일치 BA→일치 Operator 순서이며,
먼저 존재하는 불일치 역할 때문에 다른 유효 Scope를 잃지 않는다. 상태 명령은 Master 또는 일치 BA만 선택한다.
타 Org/타 Home 직접 ID는 정보·존재 비노출404다. Trainer/무관리·무Operator는 기능403이며 cookie 상태에 따른 기존401도 유지한다.
등록자/과거 Scope/지원·담당/Pass 발급·수업 지점·클라이언트 Home 선택으로 현재 인가를 대체하지 않는다.
receipt 조회/replay도 원 Actor=현재 Caller, 같은 Org·현재 대상 Home의 해당 kind 권한을 재검증한다. 과거 생성자라는 이유로 접근을 유지하지 않는다.

목록은 현재 편집 가능 Member만 active/inactive 모두 포함하며 created_at,id 안정 순서·offset0+·limit1..100을 쓴다.
count/rows는 한 UoW/현재 잠금에서 일관되게 읽는다. 페이지 사이 snapshot 고정은 보장하지 않으며 매 요청은 새 현재 결과다.
list row는 편집 CAS snapshot으로 재사용하지 않는다. 선택/페이지 갱신마다 fresh detail/version을 성공 게시한 뒤 편집한다.
UI는 account UUID뿐 아니라 현재 `/me`의 Organization/관리 Branch·Master 여부/Operator Branch·grant version으로 만든 유효 Scope fingerprint,
선택 generation·대상 UUID/version을 함께 고정한다. 현재 `/me`에는 Operator version이 없으므로 해당 role 응답에 version을 한정 추가하는 안이다.
기존 `/auth/csrf`의 세션별 token은 메모리 안에서만 같은 로그인 문맥인지 비교하고 변경 시 owner 세대를 폐기한다. 비밀 token을 fingerprint 근거나 QA/로그에 기록하지 않는다.
같은 계정 재로그인/Scope 이동·축소도 owner 세대 변경으로 처리하며 Backend의 인가 근거는 계속 실제 current Caller다.
새 CSRF를 옛 초안/pending에 조용히 재결속하지 않는다. nonce 변경을 발견하면 새 값을 사용하기 전에 owner부터 폐기한다.
Actor/Scope 교체·로그아웃 시 목록·선택·초안 이름/전화·결과·pending 민감표시를 비우고 옛 세대의 제출/대사 응답 게시를 차단한다.
불명 작업의 원 UUID/본문은 같은 owner의 대사에만 쓰며 새 Scope/Actor 초안에 가져오거나 개인정보를 계속 화면에 남기지 않는다.
목록/상세/새로고침의 늦은 응답이 높은 알려진 version/새 선택을 덮지 않게 하고 현재 Actor 확인 완료 후에만 게시한다.
현재 Home/Member active는 서로 다른 상태로 표시하며 inactive 편집을 잠그거나 저장으로 재활성화하지 않는다. Home 이동 입력을 편집에 넣지 않는다.
후보 route는 `/api/v1/admin/members` GET/POST, `/{id}` GET/POST, `/{id}/deactivate`·`/reactivate` POST,
`/api/v1/admin/member-operations/{uuid}` GET, `/api/v1/admin/member-branches` GET와 `/members` 화면이다. prefix admin은 Operator 권한 제거 근거가 아니다.
생성/변경은 기존 방식의200, 새 API의 쓰기는 Origin/CSRF가 필요하다. 새로운 framework/외부서비스·모바일 앱을 만들지 않는다.

## CAS·원 Actor operation·ACK 복구

서버 UUID Member와 positive bigint version을 사용한다. create는 version1, 실제 이름/번호/상태 변경만 +1이다.
기대 version은 strict positive bigint 범위 정수이며 stale는 같은 값/이미 같은 상태여도409다. overflow도 충돌이다.
현재 version에서 canonical same-values update/이미 같은 상태 명령은 receipt만 만들고 새 버전/Audit/활동 시각을 만들지 않는다.
새 UUID의 정상 등록은 같은 이름/번호여도 별도 실제 생성이다. replay/no-op/조회는 touch하지 않는다.

명령 UUID의 namespace/조회는 org·원 Actor에 결속하며 canonical schema version과 원 Actor/org/종류/대상/Home/전체 완성값·기대version을
canonical fingerprint에 포함한다. 수신한 명령을 다른 대상/Actor/내용으로 재사용하지 않는다. 다른 Actor는 receipt를 읽을 수 없고 payload 불일치는409다.
일치 replay는 해당 operation kind의 현재 인가를 다시 확인한다. 예전 state 명령은 현재 Master/일치 BA가 아니면 edit Scope가 남아 있어도 대사하지 못한다.
각 replay/receipt 요청도 최초 인증 snapshot의 원래 idle/absolute 기한을 최종 검증한다. 이는 과거 operation의 만료시각을 새로 연장하거나
현재 인증으로 옛 실패명령을 실행한다는 의미가 아니다. 원래 committed_member/version과 fresh current_member를 구분해 반환한다.
old committed는 현재값에 재적용하지 않는다. 최초 검증시각과 새 current 조회시각도 같은 시점인 것처럼 표시하지 않는다.

UI는 제출 전 operation UUID/원 Actor/대상/본문/CAS를 고정해 pending을 보존하고 중복 제출·새 UUID 자동 재시도를 막는다.
POST ACK 유실/네트워크/5xx는 동일 UUID receipt로 대사한다. receipt404만으로 실패 확정/새 UUID 제출을 하지 않고 원 명령을 재시도한다.
PT-001의 교정된404→409 복구를 재사용한다. 원 명령 재시도가 효과 없음이 확정된409/conflict 등 업무 거부면 원 Actor를 다시 확인한 뒤
pending을 종료하고 낡은 편집 snapshot을 폐기한다. fresh detail의 성공 게시 후에만 새 UUID/CAS 편집을 허용한다.
네트워크/5xx·receipt 인가 실패/actor_changed는 불명확 상태로 구분하고 원 명령을 유지한다. 모든4xx를 일괄 확정실패로 취급하지 않는다.
Actor 교체 후 옛 작업의 재전송·화면 게시를 금지하며 원 Actor와만 대사한다. 새 Actor 초안에 옛 UUID/입력을 이식하지 않는다.

## 잠금·최종 proof·작은 typed 관계

기존 installation 전역 잠금→Actor account/AuthSession→같은 Org Branch SHARE→Member head UPDATE→버전/receipt 순서를 따른다.
처음 최소 Member identity/Home을 읽더라도 잠금 후 현재 Home/version을 다시 확인하고 인가한다. current global installation 직렬화를 우회하지 않는다.
변경 head/불변 version/receipt/typed Audit와 최종 Actor/Org/역할·Scope/Branch fact 확인은 하나의 상위 UoW다.
Audit 뒤 원래 snapshot의 confirm_actor가 현재 인증/정책·원래 idle/absolute 기한을 확인하고 실제 변경만 touch한다.
touch로 원래 기한을 연장해 통과시키지 않는다. Branch 비활성 경합은 잠긴 실제 fact/current version과 create assignable을 확인한다.
조회/후보/receipt/replay/no-op도 최종 proof를 실행한다. 권한/Scope 축소·Actor 교체·기한 초과·Audit 오류는 Member/version/receipt/감사/활동 갱신 전부 rollback한다.
confirm_actor의 검증 DB clock을 receipt seal에 사용할 수 있으나 업무 기록시각을 물리PG commit timestamp라고 하지 않는다.
commit ACK 불명은 기존 UoW CommitUncertain으로 전달하며 서버의 단순503/실제 확정거부와 UI 복구를 구분한다.

후보 table은 `membership_members`, `membership_member_versions`, `membership_member_operations`, `audit_member_events`다.
작은 identity(org,member_id,version)를 사용하고 head는 실제 불변 version을 참조한다. 이름/번호 전체를 복합 B-tree key에 넣지 않는다.
항상 nonnull인 org/Member/Actor/operation/after version/종류/changed/core FK와 create에만 nullable인 before proof를 분리한다.
create의 before 없음은NULL이며 가짜 version0/가짜 이름·전화로 채우지 않는다. update/state는 before 필수다.
CHECK/FK로 org/Member/원 Actor·실제 역할/branch context/종류/버전delta/상태·Home 불변/전후version/source operation·Audit receipt를 결속한다.
Master branch context NULL도 핵심 FK를 통째로 건너뛰게 하지 않는다. 일치 BA/Operator context=대상 Home을 typed relation으로 검증한다.
nullable-before·SQL UNKNOWN/NULL 우회, update를 create로 위장, 무변경 operation을 변경 Audit로 위장하는 반례를 실제PG에서 검사한다.
민감 전후값은 인가된 버전 사실에 있고 Audit는 참조 identity를 보존한다. 무제한 Audit 조회 endpoint를 추가하지 않는다.

## 새0023·정확 runtime head·보호 원본

새 `0023_membership_basics`만 추가하고 원래0001–0022/ADR/dependency lock·공통 conftest/historical/legacy/password/WF/PT seed helpers는 불변이다.
현재 runtime의 IAM policy head만 정확23으로 좁히며 parent22는 정확22만 받아야 한다. 정책2와 transition target14는 변경하지 않는다.
migration은 iam_installation AEX를 선취한 뒤 alembic_version/정책 transition 잠금·정확22→23/23→22·정책2/target14를 DDL 전에 확인한다.
head가22도23도 아닌 상태/복수head/정책 불일치는 DDL 없이 거부한다. 앱 시작의 자동 migration/원본 DB 적용은 없다.
실제 parent22 archive/runtime으로 RF version>1·Base create/edit/noop/cancel·Home/state·IAM와 Catalog 생성/수정/중단/noop 사실을 만든 뒤
23 upgrade 전후 기존 모든 table raw row를 보존한다. 현재23 runtime이22, parent22 runtime이23에서 각각 시작 거부함을 관측한다.
빈 Membership만 lossless23 inverse를 허용한다. 어떤 Member/head/version/operation(no-op 포함)/typed Audit 새 사실도 파괴 DDL 전에 손실 guard로 막는다.
Catalog가 비어야23 inverse가 된다는 조건을 덧붙이지 않는다. 기존 Catalog/IAM/WF의 사실은 역변환으로 보존한다.

새 Membership-local actual23 inverse adapter는 실제23 downgrade+stamp22를 실행한 뒤 원래 PT22 adapter에 위임하고 목표 도달 즉시 멈춘다.
원래 helper body를 고치거나 새 자료를 삭제·head marker만 조작해 하위 guard를 우회하지 않는다. 필요한 기존 검사 caller의 import/current-head 기대만 한정 연결한다.
원래22 Catalog/21 Base/20 RF/19 Home/18 등 guard는 실제 목표 head/shape를 먼저 준비하고 확인한 뒤 원래 이유로 실행한다.
준비 inverse DDL과 target guard 관측 DDL을 구분한다. 같은 rollback-only Connection에서 준비 완료 뒤 observer를 붙여 target 파괴DDL0을 확인하고,
rollback 뒤 원래23 전체 row/head/shape 보존도 확인한다. PT-001의 준비DDL14개를 targetDDL로 세던 초기 실패를 반복하지 않는다.
pyproject는 Import Linter에 Membership의 layer/public/private 경계와 역방향 금지 항목만 추가한다. 기존9계약은 약화하지 않고 project/dev/build/uv·uv.lock은 변경하지 않는다.
BaseSalary·다른 업무 모듈·새 lifecycle tool/외부서비스/프레임워크·의존성 upgrade는 추가하지 않는다.

## 검증 선정 제안과 완료 인계

아래는 기술 진입 때 선정한 검증 계약이다. 현재 구현·개발 smoke와 실제 collection을 마쳤으며 실행별 결과/초기실패는 [결과](membership-001-basic-management-results.md)와 QA 개발자 보고를 따른다. 이전 PT의 성적을 이번 실행에 합산하지 않는다.
개발 구현 뒤 실제 collection/fixture·변경 graph로 정확 node ID/parameter를 봉인한다. 전체833 PG를 자동 반복하지 않는다.
개발자는 새 기능과 교정 smoke를 실행하고 source/backend/보호SHA를 동결한다. 기존 영향 검증 전체는 동결 뒤 새 독립 tester가 실행할 수 있다.

| 선정 묶음 | 실제 확인할 의미 |
| --- | --- |
| 새 Membership 정책/HTTP/PG | 필수/형식/표기 canonical·중복별도UUID/no merge/no echo, Master/BA/Operator 각 Scope·BA(A)+Operator(B) union·상태 관리자 전용·타Org/직접ID/ExpectedActor/CSRF |
| 비활성 네 조합 | Member active/inactive × Home active/inactive의 실제 상태명령 뒤 편집 성공/상태보존, 비활성 Home 신규배정 거부, Operator 명령별 범위·겸임 잘못된 역할 감사 금지 |
| 변경/원자성 | strict CAS/stale no-op409·valid no-op/replay 무touch·전체command binding/원Actor/current권한·새version/Audit, Audit 실패/Actor Scope변경/원idle·absolute 후 최종proof의 read/receipt/replay/no-op/변경 rollback |
| 실제 경합 | 서로 다른PG PID·installation lock 대기, 같은UUID 중복과 두CAS 충돌·Branch 상태/역할축소의 실제 순서. 가짜 독립 경합/전역gate 우회 없음 |
| 새 storage | 실제22 olddata→23/빈 inverse/raw row 보존/양runtime exacthead, 정책·head preflight DDL0, 새사실 각lossguard·NULL/core/before/typedFK·rollback 전체보존·actual lower guards |
| 새 native | 기존 신뢰 HTTPS runner의 짧은 독립 Membership mode/별도 manifest. 실제390px 긴Unicode/긴ASCII·scope/비활성 편집·Actor/동일계정 Scope변경 초안폐기/late response/중복제출·ACK유실404→409→fresh/newCAS 복구 |

기존 영향 후보는 변경 graph에 대응해 다음 현재 node를 우선 검토한다. 최종 목록은 실제 수집값과 대조하며 여기에 적힌 후보만으로 실행 성공을 주장하지 않는다.
`tests/test_pt_catalog.py::test_complete_history_stop_edit_noop_replay_and_exact_large_values`,
`tests/test_pt_catalog.py::test_final_original_proof_on_non_audited_paths`,
`tests/test_pt_catalog_storage.py::test_empty_catalog_adapter_reaches_actual21_and_keeps_original_base_guard`,
`tests/test_workforce_base_storage.py::test_each_new_fact_blocks_inverse[noop]`,
`tests/test_workforce_compensation_storage.py::test_actual0019_guard_retains_home_receipt`,
`tests/test_operator_withdrawn_move.py::test_withdrawn_history_blocks18_downgrade_before_ddl[both]`,
`tests/test_workforce_state_causal.py::test_downgrade_waits_for_actual_state_writer_and_preserves_history`,
`tests/test_workforce_integrity.py::test_commit_ack_loss_replay`, `tests/test_password_runtime.py`.
동일 계정·동일 Scope로 재로그인한 동안 옛 pending/늦은 응답을 돌려주어 옛 POST0/민감 게시0을 native의 독립 조건으로 확인한다.
BA 역할 회수 후 같은 계정의 해당 Home Operator 권한만 남긴 반례에서 정보 수정은 현재 Operator Scope로 허용하고 과거 state receipt/replay는 거부한다.
UoW/IAM policy/Organization 공개추가·shared navigation/native selector의 실제 수정에 따라 Catalog/Workforce native와 추가 경계 node를 독립 tester가 선정한다.

기존 `tests/test_iam_browser.py::run_browser`의 feature/manifest/config/evidence selector만 한정 확장하고 TLS/NSS/bubblewrap/원래90초 cap·소유권/프로세스/schema 정리 body는 보존한다.
새 mode는 기존 mode에 묶어90초를 늘리지 않는다. raw exact keyset/각 literal true·같은run_id/실제binary version·SHA와 safe 결과를 대조한다.
DB는 기존 전용 postgres fixture/소유권 검증과 `--require-postgres -x`를 사용했다. 실제 독립 결과는 보존28+교정 후64의 서로 겹치지 않는92 node이며 단일92 성공으로 부르지 않는다. skip/xfail/미수집·미실행을 성공에 포함하지 않는다.
fast는 `bash check.sh fast`의 새 실행이며 실패 시 초기 결과/교정/새 실행을 따로 기록하고 이전 성적을 합산하지 않는다.

staged 전 기존·신규 파일 모두 trailing whitespace/EOF와 `git diff --check`를 확인한다. 신규 untracked 파일은 별도 원시 검사로 포함해 PT-001의0022 단일 공백 예외를 반복하지 않는다.
완료 인계에는 source/backend/보호 파일 SHA·HEAD/branch/index/refs, 실제 node/결과·미실행/초기실패·native raw/safe 출처와 자기 환경 정리를 파일로 남긴다.
QA는 `.local/qa/membership-basic-549fbc994b844ec1/`에 최소 근거를 보존한다. 기존 auto fixture가 자기 process/schema/auto 폴더를 정리한 뒤 결과만 옮긴다.
Root keepalive/공유DB·원본자료·다른 worker 환경을 건드리지 않는다. 새 수명주기 도구/운영 배포는 없다.
개발→소스동결→새 독립검증→설계자 인수→깃 담당자의 상세 한글 커밋/일반 feature push 순서다. 개발자는 stage/commit/push/원본DB 적용/deploy하지 않는다.
## 2026-11-27 로컬 인수

이 한정 기능만 IMPLEMENTED/VERIFIED/ACCEPTED다. fast258, 독립 PG28+64의 고유92 node와 retry 동일 실행의 native5(12/9/9/22/54)를 확인했다.
최초29 실행의 관찰기 metadata 실패1·28 PASS/63 미실행과 ignored observer 교정 후64 PASS/533.29초를 구분한다.
이전11키 자료는 성적에서 제외하고 최초22개 근거는 검토 중 보존해 동결350/Backend228/보호42·환경 보존을 대조했다.
최소 SHA/실패 이력은 committed review JSON에 남긴다. 완료 QA 원본은 Root가 commit/push 후 정리할 수 있다.
PG875 중783·다른 브라우저/운영 배포는 미검증이며 전역 모듈/UoW PROPOSED·ADR/Product OPEN은 유지한다.
