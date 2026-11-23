# WORKFORCE-004 — 보상 설정 조회·Rate/Fixed 변경

Status: **LOCAL ARCHITECT ACCEPTANCE PASS — FROZEN SELECTED VERIFICATION** (2026-11-24).
[결과](workforce-004-compensation-results.md) / [최소 근거](workforce-004-compensation-review.json).
Parent `7d9e5d05f8bccd27b0038a407ddab962b25da847`, branch `codex/workforce-compensation`.
BR-PAY-002/010/011/017/018/023, PR-007/008과 최신 L2/S2/AA 승인, W0/W1/WF3 계약을 따른다.
새 Product 결정/전역 모듈 ACCEPTED/전체 정산 구현 승인이 아니다. 기존 승인 범위의 다음 최소 구현이며 사전 기술 검토 후 허용한다.

## 최소 범위

기등록 Trainer의 현재 Rate/Fixed와 최초 일반 기본급 설정 금액·적용 시작 월, 초기 포함 변경 이력을 별도 관리 화면에서 조회한다.
Rate/Fixed를 명시 입력하여 한 명령으로 변경한다. 일반 Trainer 목록/identity/계정 응답에 보상값을 섞지 않는다.
Base는 이번에 변경하지 않으며 ‘최초 일반 기본급 설정/적용 시작 월’로 정확하게 표시한다. 시작 전 월을 적용 0원으로 위장하지 않는다.
기본급 일정 편집/월별 수동 지정·과거 정산 정정은 후속 별도 계약이다. 이미 승인된 시작 월 지정·다음 변경까지 유지·미래 월 업무상 상한 없음·
수동 지정 우선·미확정 자동 반영·확정본 불변 정책은 재질문하거나 변경하지 않는다. PT 지급 생성·시간별 설정 resolver/정산 구현은 없다.

## 권한·입력·보존

현재 Master는 자기 Organization, Branch Admin은 각 요청 시점 대상 Trainer의 현재 Home Branch가 관리 Branch인 범위에서
세 값/보상 변경 이력을 조회하고 Rate/Fixed를 변경한다. 관리 범위 안 관리자·Trainer 본인도 허용한다.
Operator/Trainer 단독은 본인 값도 조회/변경 불가다. 과거 Home/수업 지점/원래 발급자/변경자만으로 접근하지 않는다.
Trainer/계정 비활성·역할 회수는 관리자 권한을 새로 만들거나 기존 현재 Home 권한을 제거하는 별도 보상 규칙이 아니다.
해당 상태를 자동 변경하지 않고 기존 독립 관리자 Caller로 판단한다. 비활성 Home의 기등록 설정 관리도 현재 Scope를 따른다.

Rate는 0~100 정수%, Fixed는 기존 W0 정확한 정수원 문자열 codec/1024자리 표현 한도를 사용한다.
명시0 허용, 누락/null/소수/음수/임의 기본값·자동 절사/반올림 금지. 표현 한도를 새 업무상 임금 상한으로 부르지 않는다.
새 승인 대기·필수 사유는 없다. 실제 변경의 항목/전후값·Actor/Role/Branch Context/대상 당시 Home·시점 감사는 필수다.
초기 before=null과 명시0을 구분한다. 민감정보/계정ID·비밀번호/전화번호/이름을 로그나 receipt에 추가 복사하지 않는다.
이력 Actor UUID와 내부 receipt Actor FK는 허용된 최소 식별이다. 위 계정ID 복사 금지는 대상 로그인 계정 정보의 불필요한 복제 금지이며 canonical Actor 결속을 없애라는 뜻이 아니다. Login ID/계정 전체 감사 열람으로 넓히지 않는다.

Rate/Fixed 저장 성공 이후 생성되는 새 PT의 설정이라는 승인 의미를 보존하되 실제 PT가 없는 이번 단계에서 지급 적용 완료를 주장하지 않는다.
초기 snapshot/등록 fingerprint/원래 audit를 덮어쓰지 않는다. Home/업무 상태·Trainer version·계정/security/role epoch·AuthSession·
기존 링크·Base와 시작월은 그대로다. 보상 자체의 독립 positive version만 실제 변경 때 +1한다.
Home 이동으로 과거 감사의 당시 Branch Context를 현재 Home으로 수정하지 않는다.

## 공개 계약·UI

후보 API: `GET /api/v1/admin/trainers/{id}/compensation`,
`GET /api/v1/admin/trainers/{id}/compensation-history?offset=...&limit=...`,
`POST /api/v1/admin/trainers/{id}/compensation`,
`GET /api/v1/admin/trainer-compensation-operations/{uuid}`.
신규 경로에 UUID `X-Y3-Expected-Actor`를 적용하고 서버 현재 Caller와 대조한다. 클라이언트 role/branch는 인가 근거가 아니다.
명령: operation UUID, rate_percent, fixed_amount_won, expected_compensation_version, expected_trainer_version.
현재 Home/상태와 다른 값이 섞인 화면 쓰기를 막기 위해 둘을 구분하여 CAS한다. 보상 변경으로 Trainer version을 증가시키지 않는다.
조회 DTO는 최소 식별·현재 Home/Trainer version·Rate/Fixed/compensation version·명확히 표시된 초기 Base/시작월을 분리한다.
이력은 compensation version 오름차순 offset/limit 페이지(초기1부터)를 사용한다. append로 기존 prefix가 밀리지 않으며 total은 각 요청 시점 값이다. 초기 기록1과 실제 변경만 제공한다. 필터는 현재 Home 인가 후 적용한다.

canonical fingerprint는 원래 Actor/Trainer/명령 전부에 결속한다. receipt 조회/일치 replay도 원래 Actor인 현재 허용 관리자와
현재 조직/Home로 인가한다. 옛 Home BA가 receipt로 보상값을 보거나 현재 값을 복구하지 못한다.
같은 UUID/다른 Actor·payload는 비노출/충돌, stale 두 version은 값이 같아도 충돌이다. 일치 replay는 원래 결과와 현재 사실을 구분한다.
새 same-values 명령은 최초 receipt만 만들고 version/감사/이력/활동 시각을 바꾸지 않는다. replay도 같다.
ACK 불명은 원래 UUID 결과 대사, 자동 새 명령/rollback 없음. 현재 값이 과거 receipt 값으로 덮이지 않는다.
대사 응답의 current와 뒤따른 fresh 조회는 서로 다른 시점이다. fresh 게시 뒤에는 게시한 selection을 현재로 표시하거나 원래 응답값을 ‘결과 조회 당시’로 명시한다. fresh가 거부/미게시면 성공·최신 현재라고 표시하지 않는다. 기존 Home 대사 화면의 같은 시점 표현도 이 범위에서 최소 교정한다.

기존 workforce UI/runner를 확장한다. 관리자만 보상 패널을 쓰되 서버 인가를 대체하지 않는다.
정수원은 JS Number로 바꾸지 않는다. 최초 Base 입력과 편집 가능한 Rate/Fixed를 혼동하지 않게 표기한다.
각 패널은 자신이 읽은 Rate/Fixed·Home·두 version snapshot을 유지한다. 늦은 응답이 현재 shared Trainer 사실보다 오래되면
게시/쓰기 금지한다. 같은 Trainer version이어도 이미 관측한 더 높은 compensation version을 오래된 응답이 덮지 못한다. 다른 패널 변경 후 재조회가 필요하다. Actor/선택 generation·pending UUID/대상 결속과 중복 제출 방지를 유지한다.

## 트랜잭션·잠금

기존 composition/UoW와 공개 ports를 확장한다. 다른 모듈 private Repo/ORM 직접 접근은 추가하지 않는다.
설치/정렬 Actor 계정/AuthSessions/현재 Branch SHARE/Trainer UPDATE 순으로 현재 인가·설정 사실을 잠그고 확인한다.
대상 Trainer 계정 상태를 바꾸지 않으므로 대상 IAM 계정/원본에 새 쓰기 잠금이나 security version 변경을 도입하지 않는다.
현재 global installation 직렬화에 기대어 검증을 생략하지 않고 Home/상태·권한 변경 후 최종 현재 사실과 두 version을 검증한다.

AuditPort에 보상 전용 typed history read/append를 추가한다. Audit adapter가 원래 initial_compensation과 새 typed 보상 변경을 version ASC로 조회하고 Service가 앞뒤 현재 Home/Actor 인가를 확인한다. Workforce는 Audit private SQL을 읽지 않는다. 일반 감사 API는 만들지 않는다.

설정 current/독립version·operation receipt·변경 이력/typed Audit는 하나의 UoW다. 감사 실패/최종 Actor 원래 idle·absolute 만료/
정책·Scope 축소 시 모두 rollback한다. authenticate(touch=False)·snapshot/final confirm의 원래 기한을 사용하고 실제 변경 성공만 touch한다.
동일 설정 경합은 CAS로 한 번만 적용, Home 이동/관리자 철회/Branch 변경은 검증된 현재 사실 순서로 선형화한다.
실제 DB PID/잠금 대기로 증명하며 기존 global lock을 우회해 인위적 경합을 만들지 않는다.

## 0020·이력 기원

원래0001–0019/ADR/deps/lock·공통 harness는 보존한다. 새0020으로 workforce_trainers의 독립 compensation_version(기본1, positive)과 operation/typed audit·필요 제약을 추가한다. 별도 초기 origin 복제는 만들지 않는다.
기존 trainer행의 Rate/Fixed는 현재값으로 유지할 수 있으나 원래 immutable snapshot은 초기값으로 보존한다.
현재까지 보상 변경 기능이 없었다는 코드 사실만으로 초기 이력을 꾸미지 않는다. 새 구조 전환 전 각 Trainer의 등록 operation/creator·
initial_compensation 감사(Org/Trainer/operation/Actor/Role/원래 Home/초기 세 값/시작월·before null·version1)/snapshot/등록 시각을
대조한다. trainer.created_at=snapshot.created_at만 같은 등록 시각을 뜻하며 reg operation과 두 초기 감사의 독립 clock_timestamp가 서로 정확히 같을 것을 요구하지 않는다. 초기 history의 기록시각은 원래 initial_compensation audit.created_at이다. 기존 현재 Rate/Fixed/Base/시작월이 초기값과 다르면 임의 과거 변경이나 금액을 생성하지 않고 CREATE 전 fail closed한다.
Home/state version은 독립이므로 초기 Home/Trainer version을 현재와 강제로 같게 바꾸지 않는다.
기존 초기 감사는 원래 사실로 조회하고 새 등록도 기존 initial 감사와 동일 UoW로 버전1을 준비한다. migration 관측 시간을 최초 설정 시간으로 쓰지 않는다.
현재 소비/정산이 없으므로 timestamp만으로 역사 지급 설정을 해결했다고 주장하지 않는다. 기록시각은 서버 기록시각이며 PG 물리 commit시각이 아니다.

installation 관계 AEX 선취/정확한19↔20 head·정책2/target14 검증, 같은Org/FK/positive version/after=before+1·전후값/changed flag/
receipt/audit Actor·Role/Branch Context 결속·NOT NULL/NULL UNKNOWN 우회 방어를 적용한다. nullable actor_branch를 MATCH SIMPLE 복합FK identity에 넣어 Master NULL로 우회시키지 않는다. nonnullable Org/op/Trainer/Actor/Role/targetHome/전후값/version/changed/시각 identity를 FK로 결속하고 양쪽의 Master→NULL, BA→당시 targetHome CHECK로 Branch Context를 동일하게 도출한다.
모든 새 receipt(no-op 포함)/실제 변경·감사가 있으면 파괴 downgrade 전 정보 손실을 차단한다.
아무 업무 없는 원래 초기 중복 metadata만 원래 사실이 정확히 일치할 때 lossless inverse로 제거한다.
원래 행/초기 이력·독립 Home/state 이력은 양방향에서 보존한다. 기존 하위 guard 검사는 실제 DDL로 원래 head를 준비하며 marker만 바꾸거나
새 이력을 삭제해 guard를 우회하지 않는다. 새 WF4-local helper는 실제20 inverse+stamp19 뒤 기존19 helper에 위임한다. 0019 Home lossguard는20만 실제 역행한19 shape에서 검증하며 더 낮은 guard는 Home 업무 없는 적법 입력에서 원래 guard에 도달시킨다. current20/parent19는 서로 다른 head를 거부한다.

## 검증·범위 게이트

개발자와 독립 tester의 정적 진입 검토를 먼저 받는다. 진짜 Product 누락이 발견되면 관련 사항만 모아 사용자에게 질문한다.
그 외 기술 선택은 이 계약 범위에서 설계자가 확정한다. 구현 후 동결/독립fast·선정PG/native/설계자 인수/전담 한글 커밋·일반feature push다.
Master/BA/currentHome·겸임 본인/OperatorTrainer 거부, explicit0/정확 큰정수/입력 거부, 초기 포함 이력, no-op/replay/Actor/CSRF/ACK,
동시 변경/Home 이동/최종 Actor 기한·감사 rollback, 원래 IAM/Base/snapshot 보존, 실제19↔20/반례/lossguard/runtime을 선정한다.
기존 native manifest를 확장하고 실제 키집합/literaltrue/동일run·TLS/설치브라우저·소스동결/자원정리를 기록한다.
전기능×상태/전체PG 재반복 금지. 자기 auto 자원은 기존 도구로 정리하고 최소 근거만 유지한다.
Base 일정 편집·월별 수동/확정 정정·PT/Member/Settlement·과거 Home 정정/역사 resolver·원본 DB/배포·새 도구/의존성은 포함하지 않는다.
