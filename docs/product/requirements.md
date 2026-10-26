# 기능 요구사항 — 승인된 제품 기준

기존 PR-001–030 ID를 유지하고 최신 지점 관계·보상 설정·월 정산 결정을 반영했다. 추가실적(PR-031)을 v1에 추가했다. 이전 후보 문장은 대체되었다. 아래는 제품 의미·기대 결과이며 DB schema·API·Architecture 설계가 아니다.

출처: AS-IS-DERIVED는 발견한 업무 능력, APPROVED-TO-BE는 이번 사용자 결정으로 승인된 개선이다. KEEP/REDESIGN은 업무 취급 방식이며 구현 완료 상태가 아니다. TBD는 후속 기능의 세부 요구 미정일 뿐 OUT-V1 여부를 다시 묻는 상태가 아니다. DROP-CANDIDATE는 후보 유지 승인이고 영구 폐기 확정이 아니다. Scope의 IN-V1/OUT-V1/NOT-COMMITTED를 별도로 읽는다.

[승인 결정](product-decisions.md) · [후속 질문](open-questions.md) · [Scope](scope.md) · [AS-IS 대응](as-is-to-be-mapping.md)

<a id="pr-001"></a>
## PR-001. 운영 계정과 직무별 접근

처리 상태: REDESIGN

v1 범위: IN-V1

출처: AS-IS-DERIVED + APPROVED-TO-BE

제품 요구: Master Admin·Branch Admin·Operator·Trainer가 발급된 계정으로 Role과 Data Scope에 허용된 업무에 접근한다. Member 직접 로그인은 Future Scope다.

수용 기준 / 범위 경계: Master Admin은 Organization 전체, Branch Admin은 자신의 단일 Branch, Operator는 지정된 단일 Branch의 허용 업무, Trainer는 Allowed PT Scope다. Backend에서 Scope를 강제하고 다른 지점 ID를 직접 요청해도 무단 접근은 불가하다. 보상 설정은 PR-007의 대상 Trainer Home Branch 기준을 따른다. 기술 모델은 ARCH-001이다.

승인 근거: PD-001/002/003/004/019. [Product Decisions](product-decisions.md)

후속 TODO: ARCH-001/002, MB-001/004/005/006. [Open Questions](open-questions.md)

AS-IS reference: F01. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

2026-10-12 사용자 확정(Operator 업무 허용 지점 수 질문의 1번): v1 Operator 역할의 업무 허용 Branch는 한 시점에 하나만 지정한다. Operator는 그 지정된 단일 Branch에서 명시적으로 허용된 업무를 수행하며 같은 계정의 Operator 권한을 여러 Branch에 동시 부여하지 않는다. Branch당 Operator 한 명이라는 1:1 인원 제한을 추가하지 않으며 하나의 Branch에 여러 Operator가 있을 수 있다. 이 결정은 Operator 역할의 업무 Scope이며 기존에 허용된 겸임 역할의 독립적인 관리/PT 권한이나 Trainer Home Branch를 바꾸지 않는다(BR-OPS-011, PD-001/007, PR-001/003/030, ARCH-001, MB-004).

인가 경계: Backend는 검증된 현재 Caller의 Operator 역할/Organization·지정된 단일 업무 Branch와 해당 요청의 실제 업무 Branch를 확인한다. 직접 Branch ID·클라이언트 branch_id/role/선택 지점·과거 업무/발급 지점만으로 다른 Branch의 업무를 수행할 수 없다. 동일 계정에 Operator 권한을 중복 부여하거나 여러 Branch 중 하나를 임의 선택하는 방식으로 단일 지점 제한을 우회하지 않는다. 현재 역할/Scope 철회·축소 이후 후속 요청은 현재 권한을 적용한다. 지정이 없거나 복수 지정된 상태를 유효한 Operator 업무 권한으로 간주하지 않되 구체 계정/역할 저장·활성화 제약과 오류 계약은 후속 Architecture다.

기존 발급/검색 규칙 유지: Operator의 새 Pass 발급은 자신의 지정된 단일 Branch를 실제 Issued Branch로 사용한다. 그 발급 업무에서는 같은 Organization 전체 지점 Member를 이름·전화번호 일부로 검색하고 결과의 이름·전체 전화번호·현재 Member Home Branch를 조회/선택할 수 있다(BR-OPS-010). Member Home Branch가 Operator 업무 Branch와 다르다고 검색/발급을 거부하거나 회원 소속을 자동 이동하지 않는다. 전체 지점 Member 검색이 다른 Branch의 Pass 발급이나 일반 회원 상세/다른 Pass/PT·보상/수정·일괄 내보내기 권한을 부여하지 않는다. 기존 Master 전용 공통 상품 변경 및 관리자 전용 Pass 수동 조정·만료/해제·담당 교체/보상 업무 제한은 유지한다.

남은 결정: 새 Operator 발급/최초 Branch 지정 Actor는 Master Organization 전체/Branch Admin 자기 단일 Branch, 기존 Operator 업무 Branch 변경 Actor는 Master Organization 범위 전용으로 해결됐다. 변경은 기존 저장 후 현재 Scope 반영/실패 보존·감사 원칙을 적용한다. 발급 절차·기존 계정 역할 추가/변경·Operator 지점 변경의 대상 Branch/계정 상태·세부 절차/감사 계약 및 나머지 운영 행위 권한은 MB-004·ARCH-001/002 후속이다. 한 계정의 Operator 동시 허용 지점 수나 신규 발급/지점 변경 Actor를 다시 OPEN으로 두지 않는다. 실제 발급 대상·초기 조건/선택 응답·역할/Scope 저장·Caller/인가 계약·실패/재시도/경합은 관련 Product/Architecture 후속이다. IAM-001 S1에 Operator 구현을 추가하거나 기존 PROPOSED 인증/모듈/저장 설계를 승인한 것은 아니다.

2026-10-12 일괄 승인 수용 기준: A1–A3/A5/A6/A8/A9: v1 PG 서버 AuthSession+opaque Cookie, 별도 영문·숫자 중심 3~64자 Login ID, 15~128자/조합·주기 강제 없음/흔한 암호 차단, 전 역할 idle 30분/absolute 8시간, 복수 기기 허용·일반 logout 현재 로그인만 종료. 계정 전체 차단/복구·관리자 reset은 같은 Organization Master 전용/복수 Master 허용·마지막 사용 가능 Master 보호. JWT는 후속 재검토 후보다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch).

2026-10-12 C 일괄 승인 수용 기준: C1–C6: 계정 관리 추가 비밀번호 재확인 없음/현재 인가·CSRF·만료·운영 MFA 유지. 계정당 15분 5회 실패 후 15분 대기, 현재 암호 확인 본인 변경 후 모든 로그인 종료, Master가 ACTIVE reset 확정 시 기존 암호/로그인 즉시 무효, 마지막 Master 일반 reset 거부/별도 비상복구, Master ID 변경/모든 로그인 종료·계정/업무 이력 보존. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 E 일괄 승인 수용 기준: E3/E4: 영문 대소문자 미구별 ID/같은 ID 중복 거부, 이전 ID 원래 계정 예약·다른 계정 재할당 금지/현재 ID만 로그인. E6: Master 일반 차단 해제 시 유효 기존 암호 재로그인/일괄 강제 reset 없음, 폐기 인증·reset 무효 암호/MFA·역할/Trainer 상태 자동 복원 없음. E5 Operator·Trainer 역할 변경은 BR-OPS-019 대상별 Scope를 따른다. [2026-10-12 E 일괄 승인](product-decisions.md#review-20261012-e-batch)

2026-10-12 G 일괄 승인 반영: G1: Branch가 비활성이라는 이유만으로 유효 계정/역할의 로그인을 차단하지 않는다. 기존 Scope 안의 조회만 허용하며 계정 차단·Trainer 업무 비활성·철회/만료 인증·다른 현재 로그인 조건을 면제하지 않는다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). 구체 계약/저장/UoW·동시성 검증은 후속이다.

<a id="pr-002"></a>
## PR-002. 회원 기본정보 관리

처리 상태: KEEP

v1 범위: IN-V1

출처: AS-IS-DERIVED

제품 요구: Master Admin은 자기 Organization 전체, Branch Admin·Operator는 자기 지점의 Member를 등록하고 이름/전화번호를 수정한다(J1, BR-OPS-021). 신규 등록은 지정할 Home Branch, 기존 수정은 현재 Home Branch 기준이며 Trainer 역할만으로는 불가다. Member는 단일 Home Branch를 가지며 허용된 타 지점 PT를 이용한다. 타 지점 발급용 최소 검색과 일반 목록/상세·수정 권한은 구별한다.

수용 기준 / 범위 경계: 이름·전화번호·하나의 Home Branch를 필수로 관리하며 생년월일·성별은 v1에서 제외한다(I2, BR-OPS-020). 누락/빈 이름·번호 또는 Home Branch 없는 정상 등록은 허용하지 않는다. 일반 수정으로 필수값을 비우지 않고 변경하지 않는 필수값은 유지한다. 기존 전화번호 중복 허용·별도 Member 식별/인가된 검색·열람 범위와 Home Branch 변경 권한/이력을 유지한다. 다른 필드 채택·전화번호 형식/검증·보존/필요 삭제는 LEGAL-001 후속이다. [2026-10-12 I 일괄 승인](product-decisions.md#review-20261012-i-batch).

2026-10-12 사용자 확정: Trainer의 회원 검색/조회 대상은 본인이 담당 Trainer로 지정된 Pass의 Member와 개별 허용된 지원 수업 대상 Member만이다. 같은 지점/Organization 소속만으로 전체 회원 목록·검색·직접 ID 상세를 허용하지 않는다. Backend가 검증된 Trainer 연결/Organization Scope와 대상별 담당·지원 허용 사실을 확인한다. 관리자의 별도 승인된 회원 관리 Scope는 유지하며 조회 필드·담당 관계 인정 조건/지원 지정 주체·기간·철회/절차는 후속이다(BR-OPS-005, PR-029/030, MB-001/002/003/005·LEGAL-001).

2026-10-12 사용자 확정: 해당 Member를 Trainer의 개별 지원 조회 대상으로 지정할 수 있는 Actor는 Master Organization 전체 또는 Branch Admin의 지정 시점 현재 관리 Branch=Member 현재 Home Branch 범위다. 수원 Member/강남 지원 수업이면 수원 관리자/Master가 지정하고 강남 수행 지점·Trainer 소속/Pass Issued Branch 사실만으로는 지정할 수 없다. Backend가 현재 관리 권한/Scope와 Member Home Branch·대상 Trainer/Member의 Organization 관계를 검증한다. 지정은 최소 대상 관계만 허용하며 Member/Trainer 소속을 바꾸거나 대상 Trainer의 민감 보상/전체 월 정산·전체 회원 조회 권한을 부여하지 않는다. 기존 권한 변경 감사 원칙을 적용하고 기간/철회 주체·이동 후 기존 허용·지정 절차/대상 상태/최소 Trainer 식별정보·공개 항목은 후속이다(BR-OPS-005, PR-029/030, NFR-004).

2026-10-12 사용자 확정: 개별 지원 조회 허용은 관리자가 해제할 때까지 유지하며 고정 종료일/기간 경과 자동 종료·반복 연장은 두지 않는다. 해제 Actor/Scope는 기존 지정 권한과 같은 Master Organization/Branch Admin 처리 시점 Member 현재 Home Branch 기준을 적용한다(2026-10-11 사용자 일관성 지시 적용). Backend 현재 권한/대상 Organization 검증과 NFR-004 감사를 유지한다. 해제는 해당 지원 관계의 조회 근거만 종료하며 별도의 담당/관리 권한과 기존 PT·Pass·지급/정산은 그대로 판단한다. 소속 이동 후 기존 허용·대상 상태/담당 관계 인정·절차/공개 정보는 후속이다(BR-OPS-005).

2026-10-12 사용자 확정: Member Home Branch 변경만으로 기존 개별 지원 조회 허용을 해제하거나 재지정하지 않고 유지한다. 이동 후 지정/해제는 Master Organization 또는 각 처리 시점 Member 현재 Home Branch 관리 Branch Admin이 담당하며 이전 소속/과거 지정 Actor만으로 권한을 유지하지 않는다. 동일 Organization 내 Trainer Home Branch만 변경된 경우도 같은 유지 원칙을 적용한다(2026-10-11 사용자 일관성 지시). 현재 Caller/대상 관계 검증과 기존 감사 이력·별도 담당/관리 Scope를 유지한다. 과거 수업/Pass/지급/정산 변경이나 일반/지원 구분 고정은 없고 수업 당시 Trainer 소속 기준을 따른다. 이동 자체의 권한/시점/이력·다른 대상 상태·담당 관계/공개 필드/절차·계약/저장은 후속이다(BR-OPS-005, MB-001/002/003/005).

2026-10-12 사용자 수정 확정(잔여 0 회원 조회와 제외 필터): 본인이 담당한 이용권의 잔여가 모두 0이어도 그 사실만으로 담당 회원의 목록·검색·상세 조회를 차단하지 않는다. 기본 조회에는 잔여 0 회원도 포함하고 선택 기능인 “잔여 0인 회원 제외” 필터를 제공한다. 필터 미사용 시 포함/사용 시 해당 조건의 회원을 결과에서 제외하며 조회 권한이나 담당/지원 관계·회원 상태를 변경하지 않는다. Backend의 현재 Caller/Organization·담당 또는 개별 지원 관계 인가는 필터와 독립적으로 유지한다. 조회 허용이 Remaining > 0 등 기존 PT 등록/차감 조건을 면제하지 않는다. 여러 이용권의 잔여 집계 범위·개별 지원 회원 등 담당 이용권 없는 대상의 판정과 수동 만료/취소·담당 변경 등 다른 상태의 조회 영향/공개 필드는 후속이다(BR-OPS-005, PR-002/029/030, MB-001/003/005).

2026-10-12 사용자 확정(잔여 제외 필터의 집계 기준 질문의 1번): “잔여 0인 회원 제외”는 조회 권한이 확인된 Member의 전체 이용권 잔여를 기준으로 판단한다. 조회 Trainer가 담당한 Pass만으로 제한하지 않으며 동일 Organization 내 다른 Trainer 담당/다른 Issued Branch의 Pass도 해당 Member의 집계 범위에 포함한다. 내 담당 Pass 0회+다른 Trainer 담당 Pass 10회인 Member는 필터를 켜도 표시하고 전체 집계 잔여가 0이면 제외한다. 개별 지원 회원도 자기 담당 Pass 존재 여부와 관계없이 같은 Member 전체 기준을 적용한다. 필터 미사용의 기본 조회/개별 상세 권한은 그대로이며 다른 회원/개별 Pass·다른 Trainer PT/보상 정보를 자동 공개하지 않는다. 집계 범위는 확정됐고 나머지 종료 상태의 잔여 취급·담당 변경/비활성·공개 필드 및 계약/저장/조회 일관성은 후속이다(BR-OPS-005, PR-002/029/030, MB-001/003/005).

2026-10-12 사용자 확정(Trainer의 회원 전화번호 조회 질문의 1번): Trainer는 기존 조회 권한이 확인된 담당 회원과 개별 허용 지원 회원의 등록된 전체 전화번호를 조회할 수 있다. 부분 마스킹된 번호만 허용하는 정책으로 제한하지 않는다. 담당 Pass 잔여가 모두 0이어도 기존 회원 조회 권한이 유지되면 전화번호도 같은 범위에서 조회한다. Backend는 전화번호를 반환하는 조회마다 현재 Caller/Organization·담당 또는 지원 관계를 검증하고 미담당/미허용 회원·타 Organization 번호를 공개하지 않는다. 지원 해제 후 별도의 유효한 담당/관리 권한이 없으면 해당 번호도 공개하지 않는다. 관리자 겸임자의 별도 관리 Scope는 유지한다. 이번 승인은 전화번호 읽기이며 수정/일괄 내보내기·다른 개인정보/개별 Pass·다른 Trainer PT/보상 공개 권한을 추가하지 않는다. 전화번호 필수 수집/형식·중복/검증과 나머지 필드/보존·조회 계약은 후속이다(BR-OPS-005, PR-002/029/030, NFR-001/005, LEGAL-001).

승인 근거: PD-006/022. [Product Decisions](product-decisions.md)

후속 TODO: LEGAL-001, MB-002/005; 이동·구체 교차 이용/조회 조건은 OPEN.

AS-IS reference: F02, F03, F05. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

2026-10-12 사용자 확정(회원 등록 시 전화번호 필수 여부 질문의 1번): 새 Member 등록을 완료하려면 전화번호를 반드시 입력해야 한다. 전화번호가 누락되거나 빈 문자열·공백만 있으면 등록을 완료하지 못한다. 임의 번호나 기본값으로 필수 입력을 대신하지 않는다. 이 결정은 전화번호 필수 입력이며 번호 중복 허용/금지·구체 형식/정규화·문자/본인 확인, 다른 개인정보 필수 수집이나 등록/수정 Actor 권한을 확정한 것은 아니다. 기존 Role·Data Scope와 Trainer의 인가된 담당/지원 회원 전체 전화번호 읽기는 유지한다(BR-OPS-006, PD-022, PR-002, NFR-005, LEGAL-001).

기존 사용자 일관성 지시 적용(2026-10-11): 일반 회원정보 수정에서도 필수 전화번호를 누락·빈 문자열·공백만인 값으로 지우는 변경은 허용하지 않는다. 전화번호를 변경하지 않는 다른 정보 수정에서는 기존 번호를 유지한다. 이는 등록 필수 요건을 일반 수정에 동일 적용한 것이며 전화번호 수정 권한을 새로 부여하거나 특정 API 입력 형태를 승인한 것은 아니다. 법적·운영상 필요한 개인정보 삭제/보존 예외는 LEGAL-001에서 별도 결정한다.

2026-10-12 사용자 확정(회원 간 전화번호 중복 허용 여부 질문의 1번): 같은 Organization의 여러 Member가 같은 전화번호를 사용할 수 있다. 가족 등 공유 연락처로도 각각 등록하며 전화번호가 같다는 이유만으로 신규 등록을 거부하지 않는다. Member는 전화번호와 별개의 고유 식별자로 구분한다. 동일 번호를 같은 회원으로 자동 병합하거나 Pass·PT 진행/지급 이력·담당/지원 관계를 공유하는 근거로 삼지 않는다. 전화번호 필수 입력과 기존 Role·Data Scope는 유지한다(BR-OPS-006, PD-022, PR-002, NFR-005, LEGAL-001).

기존 사용자 일관성 지시 적용(2026-10-11): 전화번호를 변경할 권한이 있는 Actor의 일반 수정에도 같은 중복 허용 원칙을 적용한다. 다른 Member가 이미 쓰는 번호라는 이유만으로 변경을 거부하지 않되 필수 번호 비움 금지와 현재 업무 인가는 그대로 적용한다. 이 결정으로 등록/수정 권한을 추가하지 않는다.

전화번호로 검색하는 경로가 제공되면 조회 권한이 있는 회원 집합 안에서 동일 번호의 회원을 각각 식별하고, 전화번호 일치만으로 한 명으로 단정하지 않는다. 미인가 회원의 존재·번호·지점이나 조회 권한을 중복 검사/검색으로 노출하지 않는다. 중복 허용은 별도 경고 화면·중복 회원 병합 기능·Member 로그인/본인 인증 승인이 아니며 번호 형식/정규화·다른 수집 항목·보존/필요 삭제 및 구체 응답·저장 계약은 후속이다.

2026-10-12 사용자 확정(회원 소속 지점 변경 권한 질문의 1번): 동일 Organization 안에서 Member의 Home Branch는 Master Admin 또는 변경 요청 처리 시점 Member의 현재 Home Branch를 관리하는 Branch Admin이 변경할 수 있다. 받는 지점의 별도 승인 없이 처리한다. Master는 Organization 전체 범위이며 Branch Admin은 변경 전 현재 관리 Member만 대상으로 한다. 받는 지점 관리자라는 이유나 과거 소속·이전 변경자/지원 지정자·Pass Issued Branch·수업 Performed Branch 사실만으로 다른 현재 소속 Member를 이동시킬 수 없다. 관리자 권한 없는 Operator·Trainer는 수행할 수 없고 관리자 겸임자는 해당 관리 권한으로 판단한다(BR-OPS-007, PD-004, PR-002/030, MB-002, NFR-001).

기존 결정 적용: 변경된 Home Branch가 반영된 이후의 Member 관리 및 개별 지원 지정/해제는 각 요청의 현재 Home Branch와 관리 Scope를 따른다. 이전 지점 관리자는 이전 소속/처리자라는 사실만으로 Home Branch 기반 관리 권한을 유지하지 않는다. 기존 담당·개별 지원 조회 허용과 별도의 Pass 발급 지점/수업 수행 지점 기준 업무 등 독립적으로 인가되는 권한은 각각 기존 규칙을 적용한다. 이동 자체로 개별 지원 허용을 해제/재지정하지 않고, Pass의 Issued Branch·발급 조건·잔여/담당 정보, Trainer Home Branch와 과거 PT 기록/Performed Branch·확정 지급/정산을 자동 변경하지 않는다(BR-OPS-001/004/005).

기존 사용자 일관성 지시 적용(2026-10-11): Member 소속 변경은 관리 Scope에 영향을 주는 중요 변경이므로 기존 중요 행위/인가 변경의 이력·감사 원칙을 적용한다. 대상 Member·변경 전후 Home Branch·변경 Actor/권한·Branch Context·시점을 추적한다. 이번 권한 승인이 감사 저장 구조나 이동 적용 시점·예약/소급·변경 사유 입력/정정 정책을 확정한 것은 아니다(NFR-004, MB-002).

2026-10-12 사용자 확정(회원 소속 변경의 적용 시점 질문의 1번): v1의 Member Home Branch 변경은 저장 완료 즉시 적용만 지원한다. 변경이 성공한 시점부터 새 Home Branch가 현재 소속이 되며, 미래 적용일을 지정해 소속 변경을 예약하는 기능은 제공하지 않는다. 성공한 저장 이후 시작하는 후속 요청의 Home Branch 기반 관리 및 지원 지정/해제는 새 소속 기준으로 인가한다. 저장에 실패하면 변경 전 Home Branch를 유지한다. 기존 Master Organization 전체/변경 전 Member 현재 Home Branch 관리 Branch Admin 권한과 받는 지점 별도 승인 없음은 유지한다(BR-OPS-007, PD-004, PR-002/030, MB-002, NFR-001/004).

즉시 적용의 경계: 소속 변경 이력은 보존하며 기존 개별 지원 조회 허용을 해제/재지정하지 않는다. Pass Issued Branch·발급/잔여/담당 사실과 과거 PT/Performed Branch·확정 지급/정산은 소속 변경으로 자동 갱신하지 않는다. 이전 소속/처리자만으로 Home Branch 기반 관리 권한을 유지하지 않되, 담당/지원 조회나 발급/수행 지점 기준의 독립 업무 Scope는 각각 기존 규칙을 적용한다. 과거 소속 이력의 오류 정정·소급 여부/방식, 대상 Branch 상태 및 구체 저장/UoW·이미 처리 중인 요청과 동시 이동의 인가/실패 일관성은 후속이다. 이번 결정은 Member 이동 시점이며 Trainer 이동 시점이나 AuthSession 철회 구현/ADR-0004를 승인한 것은 아니다.

2026-10-12 사용자 확정(회원 이동 대상에 비활성 지점을 허용할지 질문의 1번): Member Home Branch의 이동 대상은 동일 Organization 안에서 운영 중인 활성 Branch만 허용한다. 비활성 Branch로의 이동은 허용하지 않으며 Master Admin과 Branch Admin에 동일하게 적용한다. Backend에서도 대상 Branch의 활성 여부를 검증하고 비활성 대상 요청은 거부한다. 거부 시 기존 Member Home Branch·지원 허용·Pass·과거 업무 이력은 유지한다(BR-OPS-007, PD-004, PR-002/030, MB-002/008, NFR-001).

대상 활성 조건의 범위: 기존 이동 Actor/현재 관리 Scope·받는 지점 별도 승인 없음·저장 완료 즉시 적용/미래 예약 미지원은 유지한다. 이번 결정은 새 이동의 대상 Branch 조건이며 Branch 비활성화 가능 조건, 비활성화 당시 기존 Member/Trainer/Pass 처리·자동 이동, 이미 비활성인 출발 지점의 업무 조건이나 재활성화/과거 조회 정책까지 확정한 것은 아니다. 과거 소속 이력 정정/소급·Branch 상태의 저장 표현, 이동과 비활성화의 경합·필수 감사/UoW/실패 계약은 후속이다(MB-002/008).

2026-10-12 사용자 확정(다른 지점에서 새 이용권 구매·발급 질문의 1번): Member는 같은 Organization의 Home Branch 밖 지점에서도 새 PT Pass를 구매·발급받을 수 있다. 수원 소속 회원이 강남에서 발급받으면 Member Home Branch는 수원으로 유지하고 새 Pass의 Issued Branch는 강남으로 기록한다. Member Home Branch와 Issued Branch가 같아야 한다는 제한을 두지 않는다. 기존 Member 식별자/소속·보유 Pass와 과거 PT/지급·정산 이력은 유지하며 타 지점 발급을 위해 Member를 지점별로 복제하거나 소속을 자동 이동하지 않는다(BR-OPS-001/010, PD-004/007, PR-002/003/030).

발급 대상은 기존 Member로 식별하고 Home Branch를 유지한다. 타 지점 발급 허용으로 일반 회원 목록/전화번호·다른 Pass/PT 전체 조회나 Member 수정/이동 권한을 부여하지 않는다. 발급 전 필요한 최소 검색/식별·공개 정보는 MB-002/003·ARCH-001 후속이다(BR-OPS-010).

2026-10-12 사용자 확정(발급용 타 지점 회원 검색 질문의 2번): Branch Admin·Operator는 자신의 허용된 실제 Issued Branch에서 새 PT Pass를 발급하기 위해 같은 Organization 전체 지점의 Member를 이름·전화번호 일부로 검색할 수 있다. 전화번호 전체 일치만을 요구하지 않으며 Member Home Branch가 Caller의 관리/발급 Branch와 다르다는 이유만으로 검색 후보에서 제외하지 않는다. Master의 기존 Organization 전체 범위는 유지한다. 검색은 기존 Member를 선택하여 실제 발급 지점의 새 Pass를 만드는 흐름이며 Member 소속 이동/복제나 기존 Pass·PT·지급·정산 변경을 수행하지 않는다(BR-OPS-010, PD-004/007/022, PR-002/003/030).

검색 인가/정보 공개 경계: 이 허용은 이용권 발급용 Member 검색의 후보 범위·검색 방식과 이름/전체 전화번호/현재 Member Home Branch 공개다. Backend는 매 검색/선택/발급 요청에서 현재 Caller의 발급 역할/Organization·허용 실제 Issued Branch와 대상 Member의 실제 Organization을 검증한다. 검색 Branch Context를 위조하거나 과거 검색 결과/선택 Member ID로 철회된 역할·Scope 또는 다른 Organization을 우회할 수 없다. 같은 전화번호/이름의 여러 Member는 별도 식별자로 구분하여 선택하며 번호만으로 병합하거나 첫 결과를 자동 선택하지 않는다. 이 세 항목의 읽기 허용이 회원 정보/전화번호 수정·일반 Member 상세·전체 무조건 목록/일괄 내보내기, 다른 개인정보/Pass/PT/보상 정보 열람 권한을 추가하지 않는다. Trainer 단독의 담당/개별 지원 Member 검색 및 기존 전체 전화번호 공개는 유지하고 발급 역할 겸임은 그 독립 발급 업무 Scope로 판단한다. 응답은 승인된 공개 범위 안에서 구성하며 Member 선택용 최소 식별 응답/계약과 추가 공개 정보는 후속이다. 실제 운영 연락처/검색어를 문서·일반 로그에 복사하지 않는다.

회원 식별의 기존 원칙 적용: 같은 전화번호/이름으로 여러 Member가 일치하면 별도 Member 식별자로 구분하여 발급할 대상을 선택한다. 번호 일치/첫 결과만으로 자동 병합·동일 회원 취급·소속 이동 또는 다른 Member 이력/권한 공유를 하지 않는다(BR-OPS-006). 잔여 0만으로 회원을 제외하지 않는 기존 조회 원칙은 유지하며 발급용 검색을 Trainer 전용 선택 제외 필터/담당 회원 집합으로 제한하지 않는다. 비활성 Member/Branch 등 나머지 대상 조건·검색어/빈 검색 처리·추가 공개 정보·최소 선택 응답/계약·선택/발급 일관성은 후속이다. 검색 자체는 업무 데이터를 변경하지 않으며 검색 성공만으로 발급 완료나 발급 이후 관리자 권한을 얻지 않는다.

이번 결정으로 발급용 검색 후보의 Organization 전체 지점 범위·이름/전화번호 일부 검색과 결과의 이름/전체 전화번호/현재 Member Home Branch 공개는 해결됐다. 추가 공개 정보·Member 선택용 최소 식별 응답/계약 및 나머지 검색/대상 조건, 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·실제 발급 지점 선택, 발급 시 활성 담당 필수/상품 최초 횟수의 나머지 상태·계약/저장/UoW·실패/재시도/중복·권한/소속/상품/지점 상태 변경 경합은 후속이다. 승인된 세 항목의 공개/전화번호 비마스킹을 다시 미결정으로 두지 않는다. Product OPEN/ADR·모듈/계약 상태와 기존 보상 설정 접근 제한을 유지하며 실제 검색/발급 구현·검증 완료를 뜻하지 않는다.

2026-10-12 사용자 확정(발급용 검색 결과 표시 정보 질문의 1번): 새 PT Pass 발급용 Member 검색 결과에는 이름·전체 전화번호·소속 지점을 표시한다. 소속 지점은 해당 Member의 현재 Home Branch이며 Caller 관리 지점/Pass Issued Branch/수업 Performed Branch와 구별한다. 같은 Organization의 타 지점 회원 검색 결과에도 동일하게 적용하고 부분 마스킹된 번호만 표시하도록 제한하지 않는다. 기존 이름·전화번호 일부의 Organization 전체 지점 검색과 현재 발급 역할/실제 Issued Branch Scope 인가는 유지한다(BR-OPS-010, PD-004/007/022, PR-002/003/030, NFR-001/005).

수용 경계: 같은 Organization의 타 지점 일치 Member도 인가된 발급용 검색에서 이름·전체 전화번호·현재 Member Home Branch를 반환/표시한다. 발급 역할/실제 Issued Branch/Organization 인가가 없거나 철회·축소되면 후속 요청으로 해당 정보를 얻지 못한다. Trainer 역할만으로 전체 Organization 검색/번호 조회를 허용하지 않는다. 번호 중복/동명이인은 Member별로 구분/선택하며 검색 선택만으로 회원/소속·기존 Pass/PT/보상을 변경하지 않는다. 일반 상세·다른 개인정보/Pass/PT/보상 조회/수정·일괄 내보내기는 별도 권한을 따른다. 필드별 응답/선택용 최소 식별 계약·나머지 검색/대상 조건은 후속이다(BR-OPS-006/010, NFR-001/005).

2026-10-12 J1–J3 수용 경계: 등록/이름·전화번호 수정의 현재 역할/Organization·Home Branch 범위는 BR-OPS-021, Member 자체 비활성화/재활성화는 BR-OPS-022를 적용한다. Operator의 최초 Home 지정은 신규 등록이며 기존 회원 Home 이동은 불가다. 현재 Member Home Branch/역할이 바뀐 후 이전 Scope·과거 조회/직접 Member ID/위조 role로 수정·상태 변경을 우회할 수 없다. 필수값/번호 중복 허용·별도 식별·추가 공개 제한은 유지하고 구체 입력/선택/응답/다른 상태 계약은 후속이다. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch).

V1 수용 기준: 이미 기록된 Member 과거 Home 이력 오류 정정은 Master 자기 Organization 전용이며 사유/원래 이력·정정 전후/Actor·시점 감사를 남긴다. 현재 Home Branch Admin의 일반 이동 권한은 이 과거 정정 권한을 포함하지 않는다. 기존 일반 이동 즉시 적용/미래 예약 미지원과 업무 원본 보존을 유지하고 현재 Home까지 달라지는 정정/역사 사실·상태/최소 계약은 후속이다(BR-OPS-032; [V 승인](product-decisions.md#review-20261013-v-batch); V-123 미구성·미실행).

<a id="pr-003"></a>
## PR-003. PT Pass 생성·이력·잔여 관리

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: 회원 PT 이용을 명시적 Pass로 관리한다. Pass별 Issued Branch 하나와 상품·담당·구매/잔여 횟수·상태·생성/시작 정보·Session 이력을 구분한다. 허용 범위에서 타 지점 사용이 가능하며 발급 지점이 유일한 사용 지점은 아니다. 여러 시기의 Pass와 종료 이력을 보존한다. Pass는 발급 당시 상품 가격·총횟수·Payment Type을 유지하며 이후 Catalog 수정으로 해당 조건이나 잔여를 덮어쓰지 않는다(BR-011 CLOSED).

수용 기준 / 범위 경계: 사용 가능한 Pass 안에서 발급 당시 Payment Type으로 FIXED_AMOUNT 우선, 동일 Type FIFO를 적용한다. 잔여 0인 Pass를 정상 차감 대상으로 선택하지 않는다. 관리자 수동 조정은 사유·이력을 남기고 Session 정정/취소에 따른 횟수 복원과 이력을 유지한다. 상태·사용 조건·조정 상세는 BR-001/002/007, ARCH-003, 교차 사용 조건은 MB-003/005다.

2026-10-11 사용자 확정: 동일 Organization 내 사용 가능한 Pass의 타 지점 사용에는 발급 지점 관리자 등의 사전 승인을 두지 않는다. Issued Branch 차이로 사용 후보를 제외하거나 발급 지점 우선순위를 추가하지 않고 기존 FIXED_AMOUNT 우선/FIFO를 적용한다. Issued Branch와 소속 지점을 변경하지 않으며 실제 Performed Branch를 식별한다. 회원 조회/Actor 업무 권한과 잔여/상태 등 나머지 사용 조건은 별도 게이트다(BR-OPS-001/BR-PAY-006, MB-003/005).

2026-10-12 사용자 확정: 과거 수업을 늦게 등록할 때 실제 수업 당시 이미 발급된 Pass만 차감 후보로 삼고 이후 발급된 것은 제외한다. 예를 들어 9월 20일 수업의 10월 5일 등록에 10월 1일 발급 Pass를 사용하지 않는다. 발급 시점과 나머지 사용 조건을 충족한 후보 안에서 기존 FIXED_AMOUNT 우선/FIFO를 적용한다. 만료/종료/취소 상태의 시간 기준과 발급/시작 정보의 구체 의미·사실 확인/정정은 후속이다(BR-PAY-006, BR-001/002·ARCH-003).

2026-10-12 사용자 확정: PT Pass에 만료일/유효기간을 두지 않고 시간 경과로 자동 만료하지 않는다. 권한 있는 관리자의 수동 만료로 추가 이용을 종료할 수 있으며 종료 Pass/과거 수업·지급/정산 이력을 보존한다. 만료 이후 진행한 새 수업의 차감 후보에서 제외한다. 기존 수동 변경의 사유/이력·감사 원칙을 동일 적용한다(사용자 일관성 지시). Branch Admin 대상 범위·잔여 횟수 처리·만료 정정/재개·만료 전 수업의 소급 등록과 상태 표현은 후속이다(BR-OPS-004, BR-001/002/007·ARCH-003).

2026-10-12 사용자 확정: 이용권 수동 만료는 Master Organization 전체/Branch Admin 현재 관리 Branch와 Pass Issued Branch 일치 범위에서 허용한다. 수원 발급 Pass를 강남 소속 Member가 보유/이용해도 수원 관리자 또는 Master가 담당한다. Member/Trainer Home Branch·Performed Branch·이전 관리 지점/발급 Actor 사실만으로 만료 권한을 얻지 않는다. 기존 사유/이력·감사 및 과거 기록 보존은 유지한다(BR-OPS-004, PR-030).

2026-10-12 사용자 확정: 수동 만료 자체는 Remaining을 바꾸지 않으며 사용만 차단한다. 잔여 5회는 만료 후에도 5회로 조회하고 0으로 덮어쓰거나 소멸 차감하지 않는다. 잔여 양수만으로 사용 가능/자동 재개를 판단하지 않는다. 기존 Master/Issued Branch 관리자 범위·사유/이력과 과거 기록 보존은 유지한다. 만료 해제/재개·과거 수업 및 취소/조정 연계는 후속이다(BR-OPS-004).

2026-10-12 사용자 확정: 잘못된 수동 만료는 권한 있는 관리자가 같은 Pass에서 해제할 수 있다. 기존 만료와 동일하게 Master Organization 전체/Branch Admin 처리 시점 현재 관리 Branch=Issued Branch 범위, 사유 필수·전후 상태/처리자/시점 이력·감사 및 기존 만료 이력 보존을 적용한다. 기존 직접 처리 원칙을 동일 적용하며 별도 승인 대기를 추가하지 않는다. 해제 자체로 Remaining을 변경하거나 새 Pass를 발급하지 않는다(5회→5회). 해제 후에도 잔여 > 0 등 기존 사용 조건을 충족해야 사용 가능하며 잔여 0을 사용 가능하게 만들지 않는다. 과거 수업/지급/정산의 삭제·자동 재계산 없이 이력을 보존한다. 만료 전/중 수업 지연 등록·별도 취소 복원/횟수 조정 연계와 구체 상태/저장 방식은 후속이다(BR-OPS-004, BR-001/002/007·ARCH-003).

2026-10-12 사용자 확정: 실제 수업이 수동 만료 전에 진행됐고 당시 Pass가 사용 가능했다면 현재 만료 상태여도 기존 권한·정산·현재 잔여 조건을 충족하여 늦게 등록할 수 있다. 9월 20일 수업 → 9월 30일 만료 → 10월 5일 등록은 사전 만료 해제 없이 처리한다. 수업 당시 이미 발급되고 사용 가능했던 후보에 현재 잔여 > 0 등 나머지 조건과 기존 FIXED_AMOUNT 우선/FIFO를 적용하여 선택하고 1회를 차감한다. 만료/잔여 5회는 등록 후 만료/잔여 4회이며 현재 만료 상태/기존 만료 이력을 유지한다. 만료 해제 자체의 횟수 불변 규칙과 실제 수업 차감은 구별한다. 다른 종료 사유/나머지 상태 조건·시점 사실 판정 및 별도 취소 복원/조정 연계는 후속이다(BR-PAY-006, BR-OPS-003/004, BR-001/002/007·ARCH-003).

2026-10-12 사용자 확정: 공통 상품의 판매 중단은 해당 상품의 신규 Pass 발급만 막으며 이미 발급한 Pass는 기존 권한·잔여·사용 조건에 따라 계속 사용할 수 있다. 판매 중단 자체로 기존 Pass의 조건/잔여/사용 상태나 과거 수업/보상을 변경하지 않는다. Catalog 판매 상태를 기존 Pass의 일괄 사용 차단 조건으로 쓰지 않으며 개별 만료/잔여 0 등 다른 사용 불가 사유는 유지한다(BR-PAY-001/006, PR-006, PD-011).

승인 근거: PD-007/008/010/011/022. [Product Decisions](product-decisions.md)

후속 TODO: BR-001/002, ARCH-003, MB-002/003. [Open Questions](open-questions.md)

AS-IS reference: F04. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

2026-10-12 사용자 확정(이용권의 담당 Trainer 교체 질문의 1번): 기존 PT Pass에서 Assigned Trainer를 교체할 수 있다. 20회권을 5회 사용한 뒤 담당 A를 B로 바꾸어도 같은 Pass의 잔여 15회와 과거 수업·지급 이력을 유지한다. 교체를 위해 기존 Pass를 취소하거나 새 Pass를 발급하는 절차를 요구하지 않으며 횟수를 복원/추가/재차감하지 않는다. 발급 당시 상품 가격·총횟수·Payment Type과 Issued Branch는 그대로이고 Member/Trainer Home Branch도 이 변경으로 이동하지 않는다. 과거 PT 기록의 실제 수행 Trainer·Performed Branch, 확정 Session Payment·추가실적/정산을 새 담당 기준으로 자동 재작성/재계산하지 않는다(BR-OPS-008, PD-007, PR-003).

기존 사용자 일관성 지시 적용(2026-10-11): 일반 담당 교체도 저장 완료 후 변경된 현재 담당을 적용하고 미래 예약 변경 절차를 추가하지 않는다. 중요 Pass/인가 관계 변경의 이력·감사 원칙에 따라 대상 Pass/Member·변경 전후 담당 Trainer·변경 Actor/권한·Branch Context·시점을 추적한다. 저장 실패 시 기존 담당과 잔여/이력을 유지한다. 저장/UoW·감사 구조·동시성 계약을 승인한 것은 아니다(NFR-001/004, BR-OPS-007/008).

2026-10-12 사용자 확정(담당 교체 권한의 기준 지점 질문의 1번): 기존 Pass의 Assigned Trainer 교체는 Master Admin의 Organization 전체 범위 또는 처리 시점 Member의 현재 Home Branch를 관리하는 Branch Admin에게 허용한다. 수원 발급 Pass의 회원이 현재 강남 소속이면 강남 Branch Admin 또는 Master가 교체할 수 있으며, 수원 Branch Admin은 Issued Branch만을 근거로 교체할 수 없다. 회원 소속이 다시 변경되면 각 교체 요청은 변경된 현재 Home Branch 기준으로 인가한다. 이용권 수동 만료/해제의 Issued Branch 기준은 그대로 유지한다(BR-OPS-004/008, PD-007, PR-003/030).

Backend는 검증된 현재 Caller의 관리자 권한/Organization·관리 Branch Scope, 실제 Pass→Member 관계와 Member 현재 Home Branch를 확인한다. 직접 Pass/Member ID·클라이언트 role/Branch/Member 소속 값·과거 소속/담당 또는 이전 처리 Actor·Trainer Home Branch·수업 Performed Branch만으로 교체 권한을 인정하지 않는다. 관리자 권한 없는 Operator/Trainer는 수행할 수 없으며 관리자·Trainer 겸임자는 해당 관리자 Scope로 판단한다. 권한 거부/실패 시 기존 담당·잔여/발급 조건·업무 이력을 유지한다. 기존 범위 내 관리자 직접 처리 원칙을 동일 적용하여 별도 Master 승인 대기를 추가하지 않는다(2026-10-11 사용자 일관성 지시 적용). 교체 권한은 대상 Trainer의 Compensation Setting 조회/변경 권한이나 다른 지점 전체 Trainer/Member 정보 열람 권한을 부여하지 않는다. 기존 즉시 적용·전후 담당/Actor/Branch Context·시점 이력/감사·현재 관계 기반 조회와 과거 수업/보상 보존 원칙은 유지한다.

2026-10-12 사용자 확정(교체할 Trainer의 소속 지점 질문의 1번): 기존 Pass의 담당 교체 대상은 같은 Organization의 Trainer이며 Member 현재 Home Branch와 다른 지점 소속 Trainer도 허용한다. 강남 회원의 담당을 수원 소속 Trainer로 바꿀 수 있다. Member와 같은 지점 소속이어야 한다는 제한을 두지 않으며 다른 Organization Trainer는 지정할 수 없다. 교체 요청의 Actor 권한은 기존대로 Master Organization 전체 또는 Branch Admin 처리 시점 Member 현재 Home Branch 기준이다(BR-OPS-008, PD-007, PR-003/029/030).

기존 규칙 적용(BR-OPS-001/005/008, BR-PAY-011/015): 담당 교체는 Assigned Trainer 관계만 바꾸며 Member/Trainer Home Branch·Pass Issued Branch·발급 조건/잔여와 과거 실제 수업/확정 지급·정산을 바꾸지 않는다. 후속 회원 조회는 현재 담당 관계와 별도 지원/관리 권한으로 인가한다. 실제 PT 업무의 Allowed PT Scope·Pass 사용 조건은 별도로 검증한다. 일반/지원 보상 구분은 실제 수행 Trainer의 수업 당시 Home Branch와 실제 Performed Branch를 비교한다. 수원 소속 Trainer가 강남 회원을 수원에서 지도하면 일반 PT, 강남에서 지도하면 지원 수업으로 기존 보상 규칙을 적용하며 담당 지정만으로 일괄 일반/지원 처리하지 않는다. 지원 수업은 해당 수업의 보상 전체를 관리자 입력 Additional Performance로 처리하고 일반 Session Payment를 중복 합산하지 않는다. 타 지점 Trainer를 담당으로 지정할 수 있어도 그 Trainer의 Compensation Setting·전체 정산/프로필이나 타 지점 전체 회원/Trainer 목록 열람 권한은 늘어나지 않는다. Backend는 대상 Trainer의 실제 Organization 관계도 확인하고 요청의 Trainer/Organization ID·지점 값만으로 신뢰하지 않으며 범위 밖 요청 거부 시 기존 담당/잔여·업무 이력을 유지한다.

2026-10-12 사용자 확정(담당 교체 전 수업의 누락 등록 질문의 1번): A가 담당으로 실제 수업을 진행한 뒤 담당이 B로 바뀌어도 A는 교체 전 본인 수업을 직접 늦게 등록할 수 있다. 예: 9월 5일 A 수업 → 9월 6일 B로 담당 교체 → 9월 7일 A 누락 등록. 실제 수업 당시 A의 담당 관계와 본인 수행 사실, 현재 검증된 Caller/Trainer 연결·Organization 및 기존 Pass/정산 조건을 확인한다. 현재 담당이 B라는 이유만으로 관리자 대행이나 A 재배정을 요구하지 않는다. 이 허용만으로 A의 해당 회원 목록/상세·전화번호/다른 Pass·다른 Trainer 기록 조회 권한을 복원하지 않는다(BR-OPS-003/005/008, PD-008, PR-008/029/030).

2026-10-12 사용자 확정(잔여 0회인 이용권의 담당 교체 질문의 1번): Remaining이 0인 기존 Pass도 Assigned Trainer를 교체할 수 있다. 잔여를 모두 사용해 이용이 끝난 Pass도 포함한다. 같은 Pass에서 담당 A를 B로 바꾸며 Remaining 0·발급 조건/Issued Branch·과거 실제 수행 Trainer/PT 기록·확정 지급/정산 이력은 유지한다. 새 담당 B는 기존 현재 담당 관계에 따른 Member 조회·응대를 이어갈 수 있다. 기존 Master Organization 전체/Branch Admin 처리 시점 Member 현재 Home Branch 권한과 같은 Organization의 다른 지점 Trainer도 대상 허용 원칙은 유지한다(BR-OPS-005/008, PD-007, PR-003/029/030).

남은 결정: 교체 Actor/Branch Scope·대상 Trainer 지점 조건·교체 전 실제 본인 수업의 이전 담당 직접 누락 등록과 함께 잔여 0으로 이용을 마친 Pass의 담당 교체도 해결됐다(2026-10-12). 잔여 소진 외 Pass 수동 만료/취소 등 다른 사유의 상태별 교체/담당 조회 조건·과거 담당/수행 사실 확인 불가/정정·교체 후 수업/다른 관계의 나머지 인가와 구체 명령/응답·최소 식별/Trainer 선택 정보·이력/저장/UoW·조회/등록/교체 경합은 ARCH-001·MB-001/003/005·BR-001/008 및 후속 Architecture에서 결정한다. 잔여 0 승인만으로 별도 수동 만료/취소 조건을 일괄 허용하거나 상태명/저장 방식을 확정하지 않는다. 교체 허용은 계정/역할·보상 설정 수정 권한 승인이 아니다.

2026-10-12 사용자 확정(이용권 횟수의 수동 조정 권한 질문의 1번): Pass 횟수의 수동 조정은 Master Admin의 Organization 전체 범위 또는 처리 시점 현재 관리 Branch가 해당 Pass의 Issued Branch인 Branch Admin에게 허용한다. 수원 발급/현재 강남 소속 Member의 이용권은 수원 Branch Admin 또는 Master가 조정하며, 강남 Branch Admin은 Member의 현재 소속만을 근거로 조정할 수 없다. 회원 소속이나 담당 Trainer가 바뀌어도 Issued Branch 기준은 유지한다. 이용권 수동 만료/해제와 같은 발급 지점 기준이며 담당 교체의 Member 현재 Home Branch 기준과 구별한다(BR-OPS-004/008/009, PD-007/010, PR-003/030).

사유·대상 Pass/Member·전후 Remaining/증감량·처리 Actor/Role/Branch Context·시점 이력/감사를 요구한다. 기존 범위 내 직접 처리 원칙을 동일 적용하고 별도 Master 승인 대기를 추가하지 않는다(2026-10-11 사용자 일관성 지시). 비관리자 Operator/Trainer·범위 밖 직접 ID/위조 Scope·사유 누락은 거부하고 직전 잔여/이력을 유지한다. PT 취소 복원은 기존 수업 취소 권한/조건의 별도 업무다. 최초 부여/추가·감소의 수량/목적/상태 조건·과거 이력 연계와 조정/감사 저장/UoW·동시성은 BR-OPS-009 및 BR-001/002/007·ARCH-001/003 후속이다.

2026-10-12 사용자 확정(다른 지점에서 새 이용권 구매·발급 질문의 1번): Member는 같은 Organization의 Home Branch 밖 지점에서도 새 PT Pass를 구매·발급받을 수 있다. 수원 소속 회원이 강남에서 발급받으면 Member Home Branch는 수원으로 유지하고 새 Pass의 Issued Branch는 강남으로 기록한다. Member Home Branch와 Issued Branch가 같아야 한다는 제한을 두지 않는다. 기존 Member 식별자/소속·보유 Pass와 과거 PT/지급·정산 이력은 유지하며 타 지점 발급을 위해 Member를 지점별로 복제하거나 소속을 자동 이동하지 않는다(BR-OPS-001/010, PD-004/007, PR-002/003/030).

권한 있는 발급 업무의 실제 Issued Branch와 Member/Product/Branch Organization 관계를 확인하고 새 Pass에 발급 당시 공통 상품 조건을 보존한다. 판매 중단 상품의 새 발급은 거부하며 기존 Pass 조건/잔여·소속/담당·과거 기록/지급/정산은 그대로다. 새 Pass의 만료/해제·수동 횟수 조정은 Issued Branch, 담당 교체는 Member 현재 Home Branch의 기존 권한으로 판단한다. 발급 Actor는 Master·Branch Admin·Operator이며 각자의 승인된 발급 Scope를 따른다(2026-10-12). 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·발급 지점 선택·활성/초기 횟수/담당 조건·발급용 추가 공개 정보·Member 선택용 최소 식별 응답/계약과 저장/응답/감사·UoW/실패/재시도·동시성은 후속이다(BR-OPS-010, ARCH-001·MB-001/002/003/004/005·BR-001/002).

2026-10-12 사용자 확정(새 이용권 발급 Actor 질문의 1번): 새 PT Pass 발급은 Master Admin·Branch Admin·Operator에게 각자의 허용된 실제 Issued Branch 범위에서 허용한다. Master는 Organization 전체, Branch Admin은 자신의 단일 관리 Branch, Operator는 부여된 허용 발급 Branch Scope에서 처리한다. 같은 Organization의 Member는 Home Branch가 발급 지점과 달라도 대상이 될 수 있으며 기존 Member/Home Branch를 유지하고 새 Pass에 실제 Issued Branch를 기록한다(BR-OPS-010, PD-004/007, PR-003/030).

권한 경계: Trainer 역할만으로는 새 Pass를 발급할 수 없다. Trainer를 겸하는 계정에 Master·Branch Admin·Operator의 발급 권한이 있으면 해당 역할의 독립적인 발급 Scope로 판단하며 별도 계정을 요구하지 않는다. Operator의 새 발급 권한은 공통 상품 생성/수정, 기존 Pass 수동 횟수 조정·만료/해제·담당 교체, Member 소속 이동, PT 정정/취소·Compensation Setting·Additional Performance·월 정산의 별도 권한을 추가하지 않는다. 발급 대상 식별을 타 지점 전체 Member 목록/전화번호·다른 Pass/PT/민감 보상 정보의 일반 조회 허용으로 확대하지 않는다. 기존 보상 설정 접근 제한과 Trainer의 담당/개별 지원 회원 조회는 그대로다.

남은 결정: 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차과 실제 발급 지점 선택/계약, 지점/Member/Trainer 활성·발급 시 활성 담당 필수/상품 최초 횟수의 나머지 상태/선택 계약, 타 지점 Member 추가 공개 정보·Member 선택용 최소 식별 응답/계약과 업무 인가 경로는 ARCH-001·MB-001/002/003/004/005·BR-001/002/010 후속이다. 승인된 Master·Branch Admin·Operator의 발급 허용과 Trainer 단독 불가를 다시 미결정으로 두지 않으며, 미정 Scope 부여/조회·상태 조건을 임의 기본값으로 구현하지 않는다. 발급/상품 조건·감사 계약/저장·Application UoW·실패/재시도/중복 및 판매 중단/지점 상태/Member 이동/인가 변경 경합은 후속 Architecture 설계·검증 대상이다.

2026-10-12 사용자 확정(발급용 타 지점 회원 검색 질문의 2번): Branch Admin·Operator는 자신의 허용된 실제 Issued Branch에서 새 PT Pass를 발급하기 위해 같은 Organization 전체 지점의 Member를 이름·전화번호 일부로 검색할 수 있다. 전화번호 전체 일치만을 요구하지 않으며 Member Home Branch가 Caller의 관리/발급 Branch와 다르다는 이유만으로 검색 후보에서 제외하지 않는다. Master의 기존 Organization 전체 범위는 유지한다. 검색은 기존 Member를 선택하여 실제 발급 지점의 새 Pass를 만드는 흐름이며 Member 소속 이동/복제나 기존 Pass·PT·지급·정산 변경을 수행하지 않는다(BR-OPS-010, PD-004/007/022, PR-002/003/030).

검색 인가/정보 공개 경계: 이 허용은 이용권 발급용 Member 검색의 후보 범위·검색 방식과 이름/전체 전화번호/현재 Member Home Branch 공개다. Backend는 매 검색/선택/발급 요청에서 현재 Caller의 발급 역할/Organization·허용 실제 Issued Branch와 대상 Member의 실제 Organization을 검증한다. 검색 Branch Context를 위조하거나 과거 검색 결과/선택 Member ID로 철회된 역할·Scope 또는 다른 Organization을 우회할 수 없다. 같은 전화번호/이름의 여러 Member는 별도 식별자로 구분하여 선택하며 번호만으로 병합하거나 첫 결과를 자동 선택하지 않는다. 이 세 항목의 읽기 허용이 회원 정보/전화번호 수정·일반 Member 상세·전체 무조건 목록/일괄 내보내기, 다른 개인정보/Pass/PT/보상 정보 열람 권한을 추가하지 않는다. Trainer 단독의 담당/개별 지원 Member 검색 및 기존 전체 전화번호 공개는 유지하고 발급 역할 겸임은 그 독립 발급 업무 Scope로 판단한다. 응답은 승인된 공개 범위 안에서 구성하며 Member 선택용 최소 식별 응답/계약과 추가 공개 정보는 후속이다. 실제 운영 연락처/검색어를 문서·일반 로그에 복사하지 않는다.

회원 식별의 기존 원칙 적용: 같은 전화번호/이름으로 여러 Member가 일치하면 별도 Member 식별자로 구분하여 발급할 대상을 선택한다. 번호 일치/첫 결과만으로 자동 병합·동일 회원 취급·소속 이동 또는 다른 Member 이력/권한 공유를 하지 않는다(BR-OPS-006). 잔여 0만으로 회원을 제외하지 않는 기존 조회 원칙은 유지하며 발급용 검색을 Trainer 전용 선택 제외 필터/담당 회원 집합으로 제한하지 않는다. 비활성 Member/Branch 등 나머지 대상 조건·검색어/빈 검색 처리·추가 공개 정보·최소 선택 응답/계약·선택/발급 일관성은 후속이다. 검색 자체는 업무 데이터를 변경하지 않으며 검색 성공만으로 발급 완료나 발급 이후 관리자 권한을 얻지 않는다.

이번 결정으로 발급용 검색 후보의 Organization 전체 지점 범위·이름/전화번호 일부 검색과 결과의 이름/전체 전화번호/현재 Member Home Branch 공개는 해결됐다. 추가 공개 정보·Member 선택용 최소 식별 응답/계약 및 나머지 검색/대상 조건, 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·실제 발급 지점 선택, 발급 시 활성 담당 필수/상품 최초 횟수의 나머지 상태·계약/저장/UoW·실패/재시도/중복·권한/소속/상품/지점 상태 변경 경합은 후속이다. 승인된 세 항목의 공개/전화번호 비마스킹을 다시 미결정으로 두지 않는다. Product OPEN/ADR·모듈/계약 상태와 기존 보상 설정 접근 제한을 유지하며 실제 검색/발급 구현·검증 완료를 뜻하지 않는다.

2026-10-12 사용자 확정(발급용 검색 결과 표시 정보 질문의 1번): 새 PT Pass 발급용 Member 검색 결과에는 이름·전체 전화번호·소속 지점을 표시한다. 소속 지점은 해당 Member의 현재 Home Branch이며 Caller 관리 지점/Pass Issued Branch/수업 Performed Branch와 구별한다. 같은 Organization의 타 지점 회원 검색 결과에도 동일하게 적용하고 부분 마스킹된 번호만 표시하도록 제한하지 않는다. 기존 이름·전화번호 일부의 Organization 전체 지점 검색과 현재 발급 역할/실제 Issued Branch Scope 인가는 유지한다(BR-OPS-010, PD-004/007/022, PR-002/003/030, NFR-001/005).

수용 경계: 같은 Organization의 타 지점 일치 Member도 인가된 발급용 검색에서 이름·전체 전화번호·현재 Member Home Branch를 반환/표시한다. 발급 역할/실제 Issued Branch/Organization 인가가 없거나 철회·축소되면 후속 요청으로 해당 정보를 얻지 못한다. Trainer 역할만으로 전체 Organization 검색/번호 조회를 허용하지 않는다. 번호 중복/동명이인은 Member별로 구분/선택하며 검색 선택만으로 회원/소속·기존 Pass/PT/보상을 변경하지 않는다. 일반 상세·다른 개인정보/Pass/PT/보상 조회/수정·일괄 내보내기는 별도 권한을 따른다. 필드별 응답/선택용 최소 식별 계약·나머지 검색/대상 조건은 후속이다(BR-OPS-006/010, NFR-001/005).

2026-10-12 사용자 확정(Operator 업무 허용 지점 수 질문의 1번): v1 Operator 역할의 업무 허용 Branch는 한 시점에 하나만 지정한다. Operator는 그 지정된 단일 Branch에서 명시적으로 허용된 업무를 수행하며 같은 계정의 Operator 권한을 여러 Branch에 동시 부여하지 않는다. Branch당 Operator 한 명이라는 1:1 인원 제한을 추가하지 않으며 하나의 Branch에 여러 Operator가 있을 수 있다. 이 결정은 Operator 역할의 업무 Scope이며 기존에 허용된 겸임 역할의 독립적인 관리/PT 권한이나 Trainer Home Branch를 바꾸지 않는다(BR-OPS-011, PD-001/007, PR-001/003/030, ARCH-001, MB-004).

인가 경계: Backend는 검증된 현재 Caller의 Operator 역할/Organization·지정된 단일 업무 Branch와 해당 요청의 실제 업무 Branch를 확인한다. 직접 Branch ID·클라이언트 branch_id/role/선택 지점·과거 업무/발급 지점만으로 다른 Branch의 업무를 수행할 수 없다. 동일 계정에 Operator 권한을 중복 부여하거나 여러 Branch 중 하나를 임의 선택하는 방식으로 단일 지점 제한을 우회하지 않는다. 현재 역할/Scope 철회·축소 이후 후속 요청은 현재 권한을 적용한다. 지정이 없거나 복수 지정된 상태를 유효한 Operator 업무 권한으로 간주하지 않되 구체 계정/역할 저장·활성화 제약과 오류 계약은 후속 Architecture다.

기존 발급/검색 규칙 유지: Operator의 새 Pass 발급은 자신의 지정된 단일 Branch를 실제 Issued Branch로 사용한다. 그 발급 업무에서는 같은 Organization 전체 지점 Member를 이름·전화번호 일부로 검색하고 결과의 이름·전체 전화번호·현재 Member Home Branch를 조회/선택할 수 있다(BR-OPS-010). Member Home Branch가 Operator 업무 Branch와 다르다고 검색/발급을 거부하거나 회원 소속을 자동 이동하지 않는다. 전체 지점 Member 검색이 다른 Branch의 Pass 발급이나 일반 회원 상세/다른 Pass/PT·보상/수정·일괄 내보내기 권한을 부여하지 않는다. 기존 Master 전용 공통 상품 변경 및 관리자 전용 Pass 수동 조정·만료/해제·담당 교체/보상 업무 제한은 유지한다.

남은 결정: 새 Operator 발급/최초 Branch 지정 Actor는 Master Organization 전체/Branch Admin 자기 단일 Branch, 기존 Operator 업무 Branch 변경 Actor는 Master Organization 범위 전용으로 해결됐다. 변경은 기존 저장 후 현재 Scope 반영/실패 보존·감사 원칙을 적용한다. 발급 절차·기존 계정 역할 추가/변경·Operator 지점 변경의 대상 Branch/계정 상태·세부 절차/감사 계약 및 나머지 운영 행위 권한은 MB-004·ARCH-001/002 후속이다. 한 계정의 Operator 동시 허용 지점 수나 신규 발급/지점 변경 Actor를 다시 OPEN으로 두지 않는다. 실제 발급 대상·초기 조건/선택 응답·역할/Scope 저장·Caller/인가 계약·실패/재시도/경합은 관련 Product/Architecture 후속이다. IAM-001 S1에 Operator 구현을 추가하거나 기존 PROPOSED 인증/모듈/저장 설계를 승인한 것은 아니다.

잔여 Pass 보유 Trainer 비활성화 수용 기준(2026-10-12, BR-OPS-008/014): 잔여가 남은 담당 Pass가 있어도 비활성화할 수 있고 Assigned Trainer·같은 Pass/Member 식별·잔여/발급 조건·과거 수업/지급/정산을 유지한다. 자동 담당 해제/교체·사전 일괄 교체나 Pass 취소/재발급/횟수 재처리는 요구하지 않는다. 유지된 담당 정보로 비활성 Trainer의 회원 조회/PT 진행 권한을 주지 않는다. 후속 교체는 기존 Member 현재 Home Branch 관리자 Scope로 별도 수행하며 Trainer 비활성화 Actor에게 교체 권한을 자동 추가하지 않는다. 기타 상태·개별 지원/재활성화 등 미정은 기존 게이트다.

새 담당 Trainer 수용 기준(2026-10-12, BR-OPS-008/014): 허용된 최초 지정/교체는 같은 Organization의 실제 활성 Trainer만 대상으로 한다. Backend에서 현재 활성 상태/Caller 행위 Scope·대상 관계를 확인하고 비활성/다른 Organization·위조 상태/직접 ID·오래된 선택 결과는 거부한다. 타 지점 활성 Trainer도 기존 조건에서 허용한다. 지정 거부/실패 시 기존 담당·잔여/발급 조건·이력을 유지하며 이후 비활성화된 기존 담당은 자동 해제/교체하지 않는다. 최초 담당 필수는 해결됐고 나머지 상태 조합/선택 계약·동시성은 후속이다.

2026-10-12 일괄 승인 수용 기준: B3/B4/B5: 새 Pass는 실제 활성 담당 필수·상품 Session Count 최초 부여. 횟수 예외는 별도 인가 관리자 조정이고 최초 발급 횟수 초과 추가도 허용하며 기존 회당 지급식·원본 발급 조건/과거 결과·사유/이력/감사를 유지한다. 발급 Actor/Issued Branch Scope와 교체 Actor/Member Home Branch Scope는 구분한다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch).

2026-10-12 C 일괄 승인 수용 기준: C12/C13: 수동 조정 후 음수 잔여 요청 거부/0까지 허용. 사용 가능·소진·수동 만료 Pass 조정 허용, 소진 후 추가 시 다른 조건 충족하면 재사용, 수동 만료는 유지/별도 해제. 기존 Issued Branch 관리자 Scope·사유/이력/과거 발급 조건·감사를 유지하며 CANCELLED/비활성 지점의 나머지 조합은 후속. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 G 일괄 승인 반영: G3: 비활성 Issued Branch의 기존 Pass도 다른 활성 지점에서 기존 가용/인가·잔여/우선 선택 조건으로 사용할 수 있다. Issued Branch/발급 조건·과거 이력을 유지하고 정상 사용 시 1회 차감한다. 다른 사용 불가 사유를 해제하지 않는다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). 구체 계약/저장/UoW·동시성 검증은 후속이다.

2026-10-12 J3=1: Member 자체 비활성이면 새 Pass 발급을 차단한다. 기존 Pass 잔여/발급 조건/담당/이력은 보존하며 회원 상태 복귀가 Pass 발급/개별 만료 해제·현재 잔여 조건 면제를 의미하지 않는다. 기존 발급용 검색의 최소 공개/Actor·Issued Branch 인가와 Member Home Branch 유지·활성 담당/판매 상품 조건은 함께 적용한다. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch).

M1/M2 수용 기준: 잘못 발급한 미사용 Pass는 기존 Issued Branch 기반 관리자 수동 만료/사유·감사로 원본과 잔여를 유지하고, 올바른 Pass를 별도 정상 발급 조건/권한으로 새로 발급한다. 별도 Pass 발급 취소 기능은 v1 제외이며 기존 Pass를 새 회원/상품/발급 조건으로 덮어쓰거나 만료 잔여를 0으로 만들지 않는다(BR-OPS-025/004). 수동 만료 Pass도 유효한 현재 담당 Trainer의 Member/허용 전화번호 조회 근거로 인정하며 현재 관계·계정/Trainer 상태·목록/직접 ID 인가·기존 전체 잔여 필터는 유지한다(BR-OPS-005). 만료 후 실제 새 수업 사용 금지·만료 전 누락 수업의 기존 조건과 담당 교체의 별도 잔여 게이트를 구별한다. [M 승인](product-decisions.md#review-20261013-m-batch); V-106/107 미구성·미실행.

T1/T2 수용 기준: Pass는 시스템 신규 발급 완료 시각을 발급 시각으로 기록하며 과거 날짜 입력/소급 발급·기존 발급 시각 수정은 v1 제외다. 별도 사용 시작일/미래 시작 예약 없이 발급 시점부터 잔여/상태·인가 등 기존 사용 조건을 적용한다. 10월 3일 구매/10월 5일 시스템 발급이면 그 Pass는 10월 3일 수업의 후보가 아니다. 기존 발급 조건/최초 횟수·활성 담당/감사·원본과 과거 지급 보존·수동 만료/해제/만료 전 과거 수업 예외는 유지한다. 시간 정밀도/정렬·실패/최소 계약은 후속이다(BR-OPS-031; [T 승인](product-decisions.md#review-20261013-t-batch); V-120/121 미구성·미실행).

U1 수용 기준: 수동 만료된 Pass도 기존 Master Organization/처리 시점 Member 현재 Home Branch Admin 권한으로 같은 Organization의 실제 활성 Trainer에게 담당 교체할 수 있다. 만료 상태/잔여·발급 시각/조건/Issued Branch·과거 실제 수행/지급·정산은 유지하고 자동 해제/횟수 부여·새 발급은 하지 않는다. 만료 해제/횟수 조정의 Issued Branch Scope와 담당 교체의 Member 현재 Home Scope를 구별하며 기존 감사/이력·직접 처리/별도 Master 승인 없음·새 담당 현재 조회/M2를 적용한다. 다른 상태/최소 계약·경합은 후속이다(BR-OPS-008; [U 승인](product-decisions.md#review-20261013-u-batch); V-122 미구성·미실행).

<a id="pr-004"></a>
## PR-004. 업무 데이터 비활성화와 과거 조회

처리 상태: REDESIGN

v1 범위: IN-V1

출처: AS-IS-DERIVED + APPROVED-TO-BE

제품 요구: 회원·트레이너·PT Pass는 비활성화/상태 변경과 이력 보존을 우선한다.

수용 기준 / 범위 경계: Member 자체 비활성화/재활성화는 Master Organization 전체 또는 Branch Admin의 처리 시점 현재 Member Home Branch 범위만 허용하며 Operator/Trainer 단독은 불가다(J2). 잔여가 남아 있어도 비활성화할 수 있고 기존 잔여/관계·이력은 보존하되 새 Pass/비활성 기간 실제 수업을 차단한다. 복귀 시 같은 Member를 재활성화하고 기존 Pass의 독립 사용 조건을 다시 확인한다(J3). 잔여 0만으로 자동 비활성화하지 않는다. 비활성 회원·Trainer·종료 Pass의 과거 이력은 기존 권한 내에서 조회하며 Hard Delete는 기본 운영 기능이 아니다(BR-OPS-022).

승인 근거: PD-010/011/022. [Product Decisions](product-decisions.md)

후속 TODO: BR-001/007, LEGAL-001. [Open Questions](open-questions.md)

AS-IS reference: F06, F10. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

2026-10-12 일괄 승인 수용 기준: B1/B2/B6: Trainer 재활성화는 Master Organization/Trainer 현재 Home Branch 관리자 Scope. 비활성 Trainer에 다른 활성 역할이 없으면 로그인 불가/재활성화 후 이용하고 독립 관리자 역할은 유지한다. 기존 업무 데이터가 있어도 Master는 Branch 비활성화 가능, 해당 지점 신규 배정/발급/새 수업 차단·기존 소속/Pass/잔여/이력 보존/자동 이동·소멸 없음. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch).

2026-10-12 G 일괄 승인 반영: G1/G2: 지점 비활성 후에도 기존 권한 내 로그인·자료 조회와 비활성화 전 실제 수업 누락/정정/취소를 허용한다. 현재 계정/역할·업무별 대상 Scope/과거 사실/Pass 조건을 확인하고 확정 월은 기존 해제·재확정/이전본 보존을 따른다. 신규 수업 차단과 계정/Trainer 자체 비활성 제한은 유지한다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). 구체 계약/저장/UoW·동시성 검증은 후속이다.

2026-10-12 J2/J3 승인: Member 상태와 Home Branch/Trainer/계정 상태는 구별한다. 비활성 기간 실제 수업은 다른 지점이나 지연 등록으로 허용되지 않고 재활성화가 그 기간 수업·과거 지급/정산을 자동 유효화하지 않는다. 비활성화 전 실제 수업 누락/정정은 기존 현재 인가/과거 사실·Pass/정산 규칙을 따르며 새 접근 예외를 추가하지 않는다. 기존 전후 상태/Actor·Branch Context·시점 이력/감사를 적용하고 상태 저장/역사 사실/정정·UoW/경합은 후속이다. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch).

<a id="pr-005"></a>
## PR-005. 트레이너 기본정보 관리

처리 상태: KEEP

v1 범위: IN-V1

출처: AS-IS-DERIVED + APPROVED-TO-BE

제품 요구: Trainer는 한 시점에 단일 Home Branch에 소속되며 Branch에는 여러 Trainer가 있을 수 있다. 직접 로그인하여 허용된 타 지점 수업도 수행한다. 타 지점 수업으로 소속 변경이나 추가 소속을 만들지 않는다. Pass 담당 Trainer와 실제 Session 수행/지급 대상을 구분한다.

수용 기준 / 범위 경계: 일반 업무정보 관리와 보상 설정을 구분한다. Trainer별 월 고정 기본급은 PR-007/010에서 지원하며 조회·변경은 보상 설정 권한을 따른다. 동시 복수 소속 N:M은 v1 요구가 아니다. 일반 Home Branch 변경은 Master Organization 범위 전용이며 기존 저장 후 현재 사실 반영/실패 보존·감사를 적용한다(2026-10-12, BR-OPS-013). 대상 상태/과거 소속 이력 정정·소급/확인 불가 및 정산/비용 잔여 상세는 MB-001/005/010 OPEN이다.

승인 근거: PD-002/006/012/022. [Product Decisions](product-decisions.md)

후속 TODO: MB-001, BR-009, LEGAL-001. [Open Questions](open-questions.md)

AS-IS reference: F07, F08, F09. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

Trainer 소속 변경 수용 기준(2026-10-12, BR-OPS-013): 현재 Master만 같은 Organization의 대상 Trainer Home Branch를 변경한다. 출발/도착 Branch Admin·계정 발급자·Operator/Trainer 단독과 위조 Caller/Branch·다른 Organization 요청을 Backend에서 거부한다. 저장 완료 이후 현재 Home Branch 기반 관리/계정 발급 인가는 새 소속을 적용하고 실패 시 이전 소속을 유지한다. 변경/소속 이력·필수 감사의 일관성을 설계한다. 독립 관리자/Operator Scope·계정/Trainer 연결·담당/지원 관계·Member/Pass/과거 수업/지급/정산과 설정값은 보존한다. 수업 구분은 수업 당시 소속, 보상 설정/월 정산 관리 권한은 처리 시점 현재 소속을 사용한다. 대상 상태·과거 소속 이력 정정/소급/확인 불가 및 저장/계약·동시성은 후속이다.

Trainer 비활성화 수용 기준(2026-10-12, BR-OPS-014): 관리자·Trainer 겸임에서 Trainer 비활성화는 Trainer 권한만 중단하고 독립 관리자 역할/Scope의 업무는 유지한다. 후속 Trainer 업무는 실제 활성 상태를 Backend에서 검증하며 과거 Caller·담당/지원 관계나 직접 ID로 우회할 수 없다. 계정 전체 차단은 별도이며 재활성화·비활성 상태 예외와 기술 계약은 ARCH-001/002·MB-001 후속이다. 과거 PT/Pass 소비·확정 보상/정산 보존 및 기본급 수동 조정 원칙을 유지한다.

Trainer 비활성화 권한 수용 기준(2026-10-12, BR-OPS-014): Master Organization 전체 또는 Branch Admin 처리 시점 대상 Trainer 현재 Home Branch=관리 Branch에서 허용한다. 실제 Caller/대상 Organization·현재 소속을 Backend 검증하며 타 지점 지원/과거 소속·발급자/위조 Scope·권한 철회 후 요청은 거부한다. 다른 Organization/범위 밖 실패 시 요청 직전 Trainer 상태·독립 관리자 Scope·이력을 유지한다. 계정 전체 차단/재활성화의 권한 승인으로 확대하지 않는다.

잔여 Pass 보유 Trainer 비활성화 수용 기준(2026-10-12, BR-OPS-008/014): 잔여가 남은 담당 Pass가 있어도 비활성화할 수 있고 Assigned Trainer·같은 Pass/Member 식별·잔여/발급 조건·과거 수업/지급/정산을 유지한다. 자동 담당 해제/교체·사전 일괄 교체나 Pass 취소/재발급/횟수 재처리는 요구하지 않는다. 유지된 담당 정보로 비활성 Trainer의 회원 조회/PT 진행 권한을 주지 않는다. 후속 교체는 기존 Member 현재 Home Branch 관리자 Scope로 별도 수행하며 Trainer 비활성화 Actor에게 교체 권한을 자동 추가하지 않는다. 기타 상태·개별 지원/재활성화 등 미정은 기존 게이트다.

새 담당 Trainer 수용 기준(2026-10-12, BR-OPS-008/014): 허용된 최초 지정/교체는 같은 Organization의 실제 활성 Trainer만 대상으로 한다. Backend에서 현재 활성 상태/Caller 행위 Scope·대상 관계를 확인하고 비활성/다른 Organization·위조 상태/직접 ID·오래된 선택 결과는 거부한다. 타 지점 활성 Trainer도 기존 조건에서 허용한다. 지정 거부/실패 시 기존 담당·잔여/발급 조건·이력을 유지하며 이후 비활성화된 기존 담당은 자동 해제/교체하지 않는다. 최초 담당 필수는 해결됐고 나머지 상태 조합/선택 계약·동시성은 후속이다.

비활성 전 누락 수업 대행 수용 기준(2026-10-12, BR-OPS-015): 실제 비활성화 전에 수행한 미등록 수업은 관리자가 대행 등록할 수 있고 Trainer 비활성/계정·현재 담당 상태는 유지한다. 실제 수행 Trainer/수업일과 입력 관리자/생성 시점을 구분하며 현재 새 담당/관리자로 과거 수행자를 대체하지 않는다. 기존 실제 수업 기준 Pass 후보/현재 잔여·차감, 기록 생성 시점 실제 수행 Trainer 지급 입력·실제 진행 월 미확정/해제·등록·동일 월 재확정 조건을 적용한다. 대행 인가의 현재 사실 검증·과거 사실/시점 판정/최소 선택 정보·구체 계약/경합은 OPEN이며 비활성 Trainer 본인 직접 등록 권한을 복구하지 않는다.

2026-10-12 K2=1: Trainer 신규 등록/이름·연락처 수정은 Master Organization 전체 또는 Branch Admin 자기 지점에 허용한다. 등록 지정 Home/수정 실제 현재 Home 기준이며 Operator/Trainer 단독은 불가다(BR-OPS-024). 기존 Home 변경 Master 전용/계정 발급·역할/연결·보상 설정의 별도 권한과 개인정보·감사를 유지한다. 연락처 필수 여부·다른 항목·최소 공개·초기 보상/누락·등록/연결/대상 상태 계약은 후속이다. [2026-10-12 K 일괄 승인](product-decisions.md#review-20261012-k-batch).

최초 등록 수용 기준(Q1/Q2=1): Trainer 신규 등록 완료에 Rate/Fixed Amount/Base Salary와 기본급 적용 시작 월을 명시 입력한다. 기존 신규 Home Branch 기준 Master/Branch Admin 등록 인가와 보상 최초 설정 권한·감사를 검증한다. 필수 입력 누락을 임의 기본값으로 채우지 않고 등록 완료의 일관성을 보장한다. 이후 이름/연락처 수정에는 보상 재입력/미전달 초기화를 요구하지 않는다. IAM 계정 발급/연결·같은 저장 구조 승인이 아니며 K3 첫 관리자 개발 범위를 확대하지 않는다(BR-OPS-028/PAY-022; [Q 승인](product-decisions.md#review-20261013-q-batch); V-114/115 미구성·미실행).

R1 전화번호 수용 기준: 이름·단일 Home Branch와 함께 Trainer 전화번호를 필수로 관리한다. 최초/일반 수정으로 누락/null/빈 값 저장은 거부하고 미변경 값은 유지한다. 기존 신규 지정/현재 Home 관리자 인가·Q 최초 보상 필수 입력/감사·이후 보상 재입력/초기화 없음과 IAM/보상 권한 분리는 유지한다. 전화번호를 Login ID/본인인증 수단으로 쓰지 않으며 형식/정규화·중복/공개/보존·최소 계약은 후속이다(BR-OPS-029; [R 승인](product-decisions.md#review-20261013-r-batch); V-116 미구성·미실행).

V1 수용 기준: Trainer 과거 Home 이력 오류는 현재 Master만 자기 Organization에서 사유/원래 이력·정정 전후/Actor·시점을 남기고 정정한다. 일반 이동·실제 당시 Home/Performed 보상 구분/월말·발생 당시 Home 비용 귀속은 유지한다. 이미 있는 PT/Pass 소비·지급/월 정산을 자동 덮어쓰지 않고 영향 건은 기존 권한/정정·확정 해제/동일 월 재확정/이전본 보존으로 처리한다. 분류가 바뀌는 기존 PT의 정정 방식·지급 기준 등은 후속이다(BR-OPS-032; [V 승인](product-decisions.md#review-20261013-v-batch); V-123 미구성·미실행).

W1 수용 기준: Trainer 과거 Home 오류로 기존 수업 분류가 바뀌면 Master 자기 Organization의 명시적 정정으로 같은 PT/기존 Pass 차감을 유지한다. 현재 Home으로 과거를 대체하거나 소속 정정만으로 PT/지급/정산을 자동 갱신하지 않는다. 최초 기록 생성 시점 보상 설정·기존 소비 Pass 발급 조건을 보존/확인할 계약과 영향 건 식별/완료 증거·경합은 후속이다(BR-OPS-033/PAY-024; [W 승인](product-decisions.md#review-20261013-w-batch); V-124/125 미구성·미실행).

<a id="pr-006"></a>
## PR-006. PT Product·기준정보 관리

처리 상태: REDESIGN

v1 범위: IN-V1

출처: AS-IS-DERIVED + APPROVED-TO-BE

제품 요구: Product는 Organization 공통 상품이며 모든 Branch가 공통 Product Catalog를 사용한다. 생성/수정은 Master Admin만 Organization 범위에서 허용한다(2026-10-12 사용자 확정, MB-007 CLOSED). Master 권한 없는 Branch Admin·Operator·Trainer는 생성/수정할 수 없다. Product 총 횟수·판매가격·Payment Type(RATE/FIXED_AMOUNT)과 업무 사용 상태를 관리하며 서비스 Product는 FIXED_AMOUNT다. 지점별 가격 정책은 추가하지 않는다.

수용 기준 / 범위 경계: Product는 지급 방식만 정하며 Trainer Rate/Fixed Amount를 갖지 않는다. RATE 회당 단가는 Product Price ÷ Product Session Count다. 기존 공제율·FinalPrice는 필수 모델이 아니다. 기존 Pass는 발급 당시 상품 가격·총횟수·Payment Type을 유지하고 상품 수정은 새 Pass부터 적용한다(BR-011 CLOSED). 일반 지급 계산은 소비 Pass의 발급 당시 상품 조건과 등록 시점의 Trainer 설정을 사용한다.

2026-10-12 사용자 확정: 공통 상품 생성/수정은 Backend가 처리 시점의 검증된 Master 권한과 Organization Scope로 인가한다. 자기 Branch에서 사용할 상품·직접 Product ID·위조 role/Branch Context는 권한 근거가 아니다. Master 권한이 철회/축소된 이후 기존 Caller/브라우저 정보만으로 변경할 수 없어야 한다. 거부 시 기존 Catalog·Pass·PT/지급/정산 이력을 변경하지 않는다. 상품 조회와 Pass 발급 권한을 생성/수정 권한과 구별하며 상품 상태/삭제·입력값·계약/저장/경합 상세는 별도 후속이다(BR-PAY-001, PR-030).

2026-10-12 사용자 확정: Master가 공통 PT Product를 판매 중단하면 해당 상품의 새 Pass 발급만 차단한다. Backend는 발급 시 판매 가능 상태를 확인하고 직접 Product ID나 Master 권한으로 이를 우회할 수 없도록 한다. 이미 발급된 Pass는 기존 권한·잔여·사용 조건을 충족하면 계속 사용할 수 있으며 현재 Catalog의 판매 중단 상태만으로 차감 후보에서 제외하지 않는다. 기존 발급 조건/잔여·과거 수업/지급/정산을 유지하고 판매 중단만으로 Pass 취소·수동 만료·잔여 소멸/복원·지급 재계산을 수행하지 않는다. 이미 만료/잔여 0 등 다른 사용 불가 사유는 면제하지 않는다. 판매 중단 권한은 기존 Master 전용 상품 수정 원칙을 동일 적용한다. 판매 재개/나머지 상태·삭제/표현/경합 상세는 후속이다(BR-PAY-001/006, PR-003/030, PD-011).

승인 근거: PD-001/006/007/009/011. [Product Decisions](product-decisions.md)

후속 TODO: 상품 판매 재개/나머지 상태·삭제 상세, BR-001·BR-010 등 관련 사용 조건/입력값 및 계약·저장/경합 설계. 공통 Catalog·Master 전용 생성/수정·판매 중단 시 새 Pass 발급만 차단은 확정이며 MB-007 CLOSED다.

AS-IS reference: F11, F12, F13. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-007"></a>
## PR-007. Trainer Compensation Setting 관리

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: Trainer Compensation Setting은 Trainer별 Rate, Fixed Amount, 월 고정 Base Salary를 묶는 제품·권한 개념이다. Product는 RATE/FIXED_AMOUNT 계산 방식을 정하고 Product별 Trainer 지급 값은 두지 않는다. 같은 저장 구조를 요구하는 개념이 아니다. Rate / Fixed Amount / Base Salary 세 항목의 조회·설정·변경은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 단일 Branch를 Home Branch로 가진 Trainer에게만 허용한다. 관리자와 Trainer를 겸하는 계정은 관리 권한 범위 안이면 본인의 세 항목도 조회·변경할 수 있다. Master Admin은 본인 포함 허용하며, Branch Admin은 본인 Trainer의 Home Branch가 관리 Branch일 때 본인도 허용한다. 관리자 권한이 없는 Operator·Trainer 계정은 본인 포함 모든 Trainer 설정 조회·변경이 불가하다. 타 지점 지원 수업은 보상 설정 접근 권한을 부여하지 않는다. Backend에서 대상 Trainer의 Home Branch를 검증하며 직접 ID 요청과 감사·정산 등 우회 경로에도 제한을 적용한다.

수용 기준 / 범위 경계: 모든 보상 설정 변경(최초 설정 포함)에 대상 Trainer, 변경 항목, 변경 전 값, 변경 후 값, 변경 Actor, Actor의 권한 및 Branch Context, 변경 시점을 추적한다. 별도 Master Admin 승인 없이 변경 가능하며 변경 요청→승인 대기→승인→반영 절차를 추가하지 않는다. 이 결정은 추가실적 승인이나 월 정산 마감/확정 절차를 면제하지 않는다. Rate/Fixed Amount는 관리자 저장 완료 이후 새로 등록되는 Session부터 적용하며 정상 등록 시 계산·확정한다. 실제 수업일로 적용 기준을 바꾸지 않는다. Base Salary 변경 시 권한 있는 관리자가 적용 시작 월을 명시적으로 지정하며 아직 확정하지 않은 과거 월도 선택할 수 있다. 변경이 적용되며 월별 기본급을 수동 지정하지 않은 미확정 정산의 기본급과 월 합계는 별도의 반영 작업 없이 자동 갱신한다. 정산을 자동 확정하지 않으며 미입력 지원 수업 등 확정 차단 조건을 유지한다. 미리 등록할 수 있는 미래 적용 시작 월의 범위 등 남은 상세는 BR-012 OPEN이다. 현재 설정 변경으로 과거 확정 Session Payment 및 월 정산의 적용 기본급·합계를 자동 변경하지 않는다. 확정 월 기본급 오류는 PR-010의 별도 해제/정정/재확정 경로를 따르며 해당 정정의 확정 해제·재확정도 Master Organization 전체/Branch Admin 처리 시점 Trainer 현재 Home Branch 기준으로 별도 Master 승인 없이 허용한다. 확정된 월의 기본급 오류 정정에서 확정 해제와 해당 월 기본급 수정 모두 사유가 필수다. Master Admin·Branch Admin 및 관리 범위 안 본인 건에 동일하게 적용한다. 해제 사유·해제자·시점과 변경 전후 기본급·수정 사유·수정자·시점을 이력으로 남긴다. 기본급 오류 정정은 대상 Trainer의 해당 월 정산에만 적용하며 현재·미래 기본급 설정과 다른 월 정산은 유지한다. 지속적인 기본급 변경은 별도로 적용 시작 월을 지정하는 기존 흐름을 따른다. 미리 등록할 수 있는 미래 적용 시작 월의 범위 등 남은 정책은 BR-012 OPEN이다.

승인 근거: PD-001/009/012/022. [Product Decisions](product-decisions.md)

추가 수용 기준(2026-10-11, 일반 기본급의 지속 적용): 일반 Base Salary 설정은 관리자가 지정한 적용 시작 월부터 다음 기본급 변경의 적용 시작 월 전까지 매월 계속 적용한다. 적용 종료 월을 지정하거나 같은 금액을 매월 다시 등록할 필요는 없다. 10월부터 2,700,000원 적용 후 변경이 없으면 11월·12월 이후에도 동일 금액을 적용한다. 특정 월 수동 금액은 해당 월에만 적용하며 다른 월에는 일반 설정을 사용한다. 미래 변경을 미리 등록할 수 있는 시작 월 범위는 BR-012의 별도 질문이다.

월별 적용 금액과의 경계: 입사·퇴사·휴직이 있는 달의 적용 기본급은 관리자가 해당 Trainer·월의 금액을 직접 지정한다. 예를 들어 월 기본급 설정이 2,500,000원이어도 해당 월만 1,500,000원을 적용할 수 있으며, 이 지정으로 현재·미래 기본급 설정과 다른 월 정산은 변경하지 않는다. 해당 월 금액 지정은 지속적인 Compensation Setting 변경과 구분하며 월 정산은 PR-010을 따른다. 월별로 수동 지정한 기본급은 이후 일반 기본급 설정이 변경되어도 유지한다. 일반 설정 변경의 미확정 정산 자동 반영은 수동 지정이 없는 월에 적용하며, 수동 지정 월의 금액을 바꾸려면 관리자가 해당 월 금액을 직접 수정한다. 미확정 월의 기본급을 최초 수동 지정하거나 다시 수정할 때 모두 사유가 필수다. 사유가 없는 요청은 거부하고 요청 직전의 수동 지정 여부·적용 금액·월 합계를 유지한다. 대상 Trainer·월, 지정/수정 전후 금액·사유·처리자·처리 시점을 이력으로 남긴다. 미확정 월 기본급의 최초 수동 지정·수정은 Master Admin의 Organization 전체, Branch Admin의 각 처리 시점 대상 Trainer 현재 Home Branch가 관리 Branch와 일치하는 범위에서 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 직접 처리한다. 추가 사용자 확정(2026-10-11): 해당 월 기본급은 권한 있는 관리자가 사유를 남기면 0원으로 명시적으로 수동 지정할 수 있다. 수동 지정한 0원은 미입력과 구분하며, 미입력이나 누락된 일반 설정을 자동으로 0원으로 대체하지 않는다. 해당 월 기본급에만 적용하고 다른 유효 지급·추가실적은 기존 규칙대로 합산한다. 미리 등록할 수 있는 미래 적용 시작 월의 범위와 월별 수동 지정 금액의 나머지 입력 제약 등은 BR-012/BR-010 OPEN이다.

후속 TODO: BR-010/012, ARCH-001; 입력 검증·기본급 미리 등록할 수 있는 미래 적용 시작 월의 범위·자동 반영의 저장/조회 및 보존/권한 구현. 세 항목 동일 권한과 별도 승인 없음은 확정.

AS-IS reference: F14, F15, F16. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

2026-10-12 H 일괄 승인 반영: H1=2: Trainer Rate는 정수 퍼센트만 허용하고 소수 비율은 자동 반올림/절사하지 않고 거부한다(BR-PAY-018). 기존 권한/설정 감사·생성 시점 지급/과거 불변성과 RATE 결과 올림 규칙은 유지한다. 범위/누락·저장 표현은 후속이다. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch). 실제 계약/구현·검증은 후속이다.

Rate 입력 수용 기준 추가(L2=1): Trainer Rate는 0~100% 정수만 허용한다. 음수/100% 초과/소수는 거부·임의 보정/반올림/절사 없으며 명시적 0%의 일반 RATE 지급은 0원이다. 미설정을 자동 0%/기본값으로 대체하지 않는다. 기존 현재 관리자 Home Scope·감사/과거 지급 불변·1,000원 올림과 FIXED 별도 계산을 유지한다(BR-PAY-018; [L 승인](product-decisions.md#review-20261013-l-batch); V-105 미구성·미실행).

초기/금액 입력 수용 기준(Q1/Q2=1): 최초 Trainer 등록 완료에는 세 보상 값과 기본급 시작 월이 필요하다. Rate 0~100% 정수, Fixed Amount/Base Salary는 0원 이상 정수 원이며 누락/null·음수/소수 원을 자동 0원/반올림/절사로 바꾸지 않는다. 기본급 시작 월부터 다음 변경까지 지속/종료 월 불필요·기존 현재 Home 기반 인가/최초 감사/보상 비공개와 신규 생성 지급/과거 확정 결과 불변을 유지한다. 일반 설정의 0원과 지원 보상/월 수동 기본급 사유 필수 0원·기타 실적 양수 규칙은 구별한다. 상한/월 범위·저장/최소 계약은 후속이다(BR-OPS-028/PAY-022; [Q 승인](product-decisions.md#review-20261013-q-batch); V-114/115 미구성·미실행).

S2 이력 수용 기준: 세 보상 설정 변경 이력의 전후 값·변경자·시점(최초 설정 포함)은 Master 자기 Organization/각 조회 시점 대상 Trainer 현재 Home Branch Admin이 조회한다. 이전 Home/Performed·원래 변경자만으로 접근하지 못하고 Operator/Trainer 단독은 본인 포함 불가다. 독립 관리자 본인 Scope를 유지하며 당시 값/Role/Branch Context·시점을 보존하고 최초 이전 값 없음과 0원을 구별한다. 현재 설정 변경/과거 지급 재계산 권한 또는 인증/계정 감사 열람을 추가하지 않는다(BR-PAY-023; [S 승인](product-decisions.md#review-20261013-s-batch); V-119 미구성·미실행).

<a id="pr-008"></a>
## PR-008. 실제 진행일별 개별 PT Session

FOUNDATION-001 의미 명확화: Session 등록은 **기존 회원에게 실제로 PT 수업을 진행했다는 사실을 기록**하는 업무다. 사용자 문구는 “PT 진행 등록”, “수업 완료 기록”, “PT 진행 내역”을 우선한다. 상품 등록·Pass 발급·미래 예약·시간표 생성이 아니며 사전 Reservation이나 PLANNED/BOOKED 상태를 v1 진행 기록의 조건으로 도입하지 않는다. 실제 수업 진행일과 시스템 기록 시점은 별개다. 지급 설정 적용은 BR-PAY-011/012, 날짜 입력 허용 범위는 BR-008 OPEN을 그대로 따른다. 서버 내부의 인가된 지급 계산은 Trainer에게 Rate/Fixed Amount/Base Salary를 공개하는 행위가 아니다.

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: Trainer가 허용된 PT 업무 범위에서 자신이 실제 진행한 날짜별 Session 1회를 직접 등록하고 자신의 Session을 조회한다. 허용된 운영자의 등록도 유지한다. 일반 Session Payment 적용 대상은 사용할 Pass 결정(FIXED_AMOUNT 우선, 동일 Payment Type FIFO) → Pass 횟수 차감 → Pass 발급 당시 Product Payment Type 확인 → 해당 시점 수행 Trainer Rate/Fixed Amount 적용 → Session Payment 계산·확정 흐름을 따른다. RATE 결과는 1,000원 단위 올림, FIXED_AMOUNT는 그대로 지급한다.

수용 기준 / 범위 경계: 실제 진행일·소비 Pass·수행 Trainer·Session Performed Branch를 식별한다. Trainer Home Branch, Member Home Branch, Pass Issued Branch와 구별하고 소속/발급 지점 변경으로 과거 수행 지점을 바꾸지 않는다. 9월 2일/5일/9일은 날짜별 3개 원본이다. 일반 지급 대상의 정상 차감·확정 일관성, Branch별 조회, Smartphone 등록을 지원하며 Trainer에게 설정을 노출하지 않는다. 타 지점 수업은 일반 PT 수당 대신 보상 전체를 Additional Performance로 처리하고 일반 Session Payment와 중복 합산하지 않는다(MB-009 CLOSED, 2026-10-10 사용자 정정). 실제 기록·Pass 차감은 유지한다. 타 지점 지원 수업은 보상 금액 없이도 허용된 PT 진행 기록과 Pass 차감을 먼저 완료한다. 권한 있는 관리자가 나중에 수업 건별 금액을 저장할 때 해당 Additional Performance 보상을 확정한다. 금액 미입력은 확정된 0원과 구분하고 누락 건을 추적할 수 있어야 한다. 해당 Trainer의 해당 월 정산 대상 지원 수업에 금액 미입력 건이 하나라도 있으면 그 Trainer·월 정산을 확정할 수 없다. 타 지점 지원 수업 보상은 권한 있는 관리자가 사유를 기록하면 0원으로 명시적으로 확정할 수 있다. 사유 없는 0원 입력은 보상 확정이 불가하다. 사유를 남기고 확정한 0원은 금액 미입력이 아니므로 그 건으로 월 정산 확정을 차단하지 않는다. 다른 미입력 건이 남으면 기존 차단 조건을 유지한다. 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin에게 Organization 전체, Branch Admin에게 대상 Trainer Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안의 본인 건도 허용하고 변경 이력을 남긴다. 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin·Branch Admin 모두 관리 범위 안에서 본인 건을 포함해 별도 승인 없이 저장 성공 즉시 반영한다. Master나 다른 관리자의 승인 대기를 두지 않으며 권한 검증과 변경 이력을 유지한다. 월 정산 확정 전 지원 수업 보상 금액의 모든 수정에는 변경 사유가 필수다. 양수 간 변경·0원에서 양수로 변경·양수에서 0원으로 변경 모두 적용하며, 사유 없이는 금액을 수정할 수 없다. 변경 전후 금액·변경 사유·수정자·수정 시점을 이력으로 남긴다. 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer의 지원 수업 보상 정정을 위해 월 정산을 확정 해제·재확정할 때는 Master의 별도 승인을 두지 않는다. Master 승인 대기 단계 없이 관리 범위 안에서 직접 처리하며 이전 확정본과 해제·재확정 이력 및 감사를 유지한다. 지원 수업 보상 정정의 월 정산 확정 해제에는 사유가 필수이며, 사유 없이 해제할 수 없다. 사유·해제자·시점을 이력으로 남긴다. 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 남은 정정·취소 절차는 BR-009/013 등 관련 OPEN을 따른다. 미입력 건의 추적 표현·정정 연동·진행 기록 연계 상세은 BR-013, 업무 접근/귀속은 관련 OPEN을 따른다. 저장·관계·동시성·트랜잭션은 Architecture 결정이다.

2026-10-11 사용자 확정: 일반 PT/타 지점 지원 수업 구분은 실제 수업 당시 Trainer Home Branch와 Performed Branch의 일치 여부를 따른다(BR-OPS-001). 이동 후 늦은 등록도 당시 구분을 유지하며 일반 PT 지급 설정은 기록 생성 시점 기준을 유지한다. 과거 소속 확인 불가·이동 적용 시점·소급 등록 범위·사실 정정의 보상 전환은 관련 OPEN이다.

2026-10-11 사용자 확정: 같은 회원이 같은 날 실제로 여러 수업을 받았다면 수업마다 별도 기록/1회 차감을 수행한다. 하루 1회로 제한하지 않으며 오전/오후 두 수업은 기록 2개·총 2회 차감이다. 날짜가 같다는 이유만으로 실제 수업을 합치거나 거부하지 않는다. 재전송/중복 클릭으로 같은 수업의 차감/지급을 늘리지 않는 기존 요구와 구별한다(BR-OPS-002, NFR-002/003).

2026-10-11 사용자 확정: 해당 Trainer/실제 진행 월 정산이 미확정이면 Trainer는 기존 Allowed PT Scope에서 자신의 과거 수업을 직접 등록한다. 당월/최근 N일 제한을 추가하지 않으며 10월의 누락 9월 수업 등록도 9월 미확정 조건에서 허용한다. 실제 수업 당시 소속에 따른 일반/지원 구분과 신규 기록 생성 시점 지급 설정 적용, 기존 Member/Pass 업무 권한·사용 조건을 유지한다. Trainer의 정산 해제/재확정 권한은 추가하지 않으며 기존 관리자 해제 후 반영/같은 월 재확정 원칙을 따른다(BR-OPS-003).

승인 근거: PD-007/008/009/010/012/022. [Product Decisions](product-decisions.md)

2026-10-12 사용자 확정: 수동 만료 전 실제 수업 당시 사용 가능했던 Pass는 현재 만료 상태라는 이유만으로 늦은 PT 등록에서 제외하지 않는다. 해당 Trainer/실제 진행 월 미확정·기존 Allowed PT Scope/현재 잔여 등 기존 조건을 충족하면 별도 만료 해제 없이 후보 선택/1회 차감한다. 현재 만료 상태와 만료 이력은 유지하며 Trainer에게 만료 해제/정산 해제 권한을 부여하지 않는다. 실제 수업 당시 소속/수행 지점 구분과 신규 일반 지급의 기록 생성 시점 설정을 유지한다(BR-OPS-003/004, BR-PAY-006).

후속 TODO: BR-002/008/010/013, MB-001/002/003/005/010. UX-001은 I3으로 CLOSED(v1 개별 등록/일괄 입력 보류), MB-009 보상 분류도 CLOSED이며 남은 계약/업무 상세는 별도 OPEN이다.

AS-IS reference: F17, F18, F19. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

2026-10-12 사용자 확정(담당 교체 전 수업의 누락 등록 질문의 1번): A가 담당으로 실제 수업을 진행한 뒤 담당이 B로 바뀌어도 A는 교체 전 본인 수업을 직접 늦게 등록할 수 있다. 예: 9월 5일 A 수업 → 9월 6일 B로 담당 교체 → 9월 7일 A 누락 등록. 실제 수업 당시 A의 담당 관계와 본인 수행 사실, 현재 검증된 Caller/Trainer 연결·Organization 및 기존 Pass/정산 조건을 확인한다. 현재 담당이 B라는 이유만으로 관리자 대행이나 A 재배정을 요구하지 않는다. 이 허용만으로 A의 해당 회원 목록/상세·전화번호/다른 Pass·다른 Trainer 기록 조회 권한을 복원하지 않는다(BR-OPS-003/005/008, PD-008, PR-008/029/030).

기존 등록/지급 규칙 적용: 해당 Trainer A/실제 수업 월이 미확정이면 당월/최근 N일 제한 없이 처리한다. 확정 월은 Trainer가 해제할 수 없으며 기존 관리자 해제 → 누락 반영 → 같은 월 재확정·이전 확정본 보존을 따른다. 수업 당시 이미 발급되고 사용 가능했던 Pass 후보·현재 잔여 > 0·FIXED_AMOUNT 우선/동일 Type FIFO와 정상 1회 차감을 유지하며, 과거 담당 관계를 근거로 특정 Pass를 고정 선택하거나 잔여 조건을 면제하지 않는다. 수동 만료 전 사용 가능했던 수업의 늦은 등록은 사전 만료 해제 없이 현재 만료 상태/이력을 유지하는 기존 예외를 따른다. 실제 수행 Trainer는 A로 기록하고, 일반/지원 구분은 실제 수업 당시 A Home Branch와 Performed Branch, 신규 일반 지급 설정은 등록 시점 A의 Rate/Fixed Amount를 사용한다. 현재 담당 B의 보상 설정을 사용하거나 기존 확정 지급을 재계산하지 않는다. 지원 수업의 관리자 수동 추가실적/미입력 월 확정 차단도 유지한다(BR-PAY-006/011/012/015, BR-OPS-001/003/004).

과거 담당은 해당 누락 등록의 한정된 인가 근거이며 현재 회원 목록/상세·전화번호나 다른 업무 범위는 BR-OPS-005의 별도 현재 관계로 판단한다. 과거 담당/수행 사실·최소 대상 식별/응답과 등록/교체/월 확정 경합은 BR-OPS-003의 후속이다.

비활성 전 누락 수업 대행 수용 기준(2026-10-12, BR-OPS-015): 실제 비활성화 전에 수행한 미등록 수업은 관리자가 대행 등록할 수 있고 Trainer 비활성/계정·현재 담당 상태는 유지한다. 실제 수행 Trainer/수업일과 입력 관리자/생성 시점을 구분하며 현재 새 담당/관리자로 과거 수행자를 대체하지 않는다. 기존 실제 수업 기준 Pass 후보/현재 잔여·차감, 기록 생성 시점 실제 수행 Trainer 지급 입력·실제 진행 월 미확정/해제·등록·동일 월 재확정 조건을 적용한다. 대행 인가의 현재 사실 검증·과거 사실/시점 판정/최소 선택 정보·구체 계약/경합은 OPEN이며 비활성 Trainer 본인 직접 등록 권한을 복구하지 않는다.

2026-10-12 사용자 확정(비활성화 전 누락 수업 대행 등록의 Branch Admin 기준 질문 1번): Master Admin은 자신의 Organization 전체, Branch Admin은 처리 시점 현재 관리 Branch가 실제 수업의 Performed Branch인 경우에만 대행 등록할 수 있다. Trainer 현재 Home Branch가 다른 지점이어도 실제 수업이 자신의 관리 지점에서 진행됐다면 허용한다. Trainer Home Branch·Member Home Branch·Pass Issued Branch 또는 과거 관리자 Scope만으로 대행 권한을 얻지 않는다(BR-OPS-015).

2026-10-12 일괄 승인 수용 기준: B7: PT 실제 진행의 업무 날짜·월 귀속은 Organization 공통 Asia/Seoul 기준이며 입력 생성 월/기기 시간대로 대체하지 않는다. 실제 진행일/생성 시점·생성 시점 지급·과거 불변성은 유지한다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch).

2026-10-12 C 일괄 승인 수용 기준: C9: 완료 수업의 실제 시작 날짜/시각을 기록하고 Asia/Seoul 업무 날짜/월을 사용한다. 생성 시점과 구분하고 미래 예약/일정을 만들지 않는다. 실제 시각 확인 불가/초 이하 정밀도·저장/역사 사실은 후속이다(BR-OPS-017). [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 G 일괄 승인 반영: G2/G4: 비활성화 전 실제 수업은 기존 업무별 권한과 실제 진행 월·Pass 조건에서 소급 처리하고, 비활성 Home Branch의 Member/활성 Trainer도 다른 활성 지점에서 허용된 담당·개별 지원 관계로 수업할 수 있다. 현재 비활성 Performed Branch의 새 수업은 불가다. 기존 생성 시점 일반 지급·타 지점 지원 전체 추가실적/중복 지급 금지와 미입력 보상 월 확정 차단을 유지한다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). 구체 계약/저장/UoW·동시성 검증은 후속이다.

2026-10-12 I1/I3=1: 실제 수업 시작 날짜·시각을 확인한 뒤 수업별 개별 등록한다. 임의 시각/‘시각 미상’ 등록이나 관리자 대행 예외는 없으며 여러 날짜 일괄 입력은 v1 보류/UX-001 CLOSED다. 기존 Asia/Seoul 실제 날짜/월, 같은 날 별개 수업/각 1회 차감, 과거 수업의 기존 권한·Pass/정산 조건과 생성 시점 지급, Smartphone 현장 등록·중복 요청 방지는 유지한다. [2026-10-12 I 일괄 승인](product-decisions.md#review-20261012-i-batch).

2026-10-12 J3=1: Member 자체 비활성 기간의 실제 수업은 PT 등록/차감을 허용하지 않는다. 다른 활성 Performed Branch나 뒤늦은 등록·회원 재활성화로 당시 차단을 우회하지 않는다. Member 자체가 활성인 경우 G4 Home Branch 비활성/타 활성 지점 이용은 기존 조건에서 유지하고, 비활성화 전 실제 수업 누락·정정은 기존 과거 수업 업무 규칙을 따른다. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch).

2026-10-12 K1 반영: 날짜/시각 오류로 취소 후 재등록한 새 일반 PT 지급은 새 기록 생성 시점 설정/선택 Pass 발급 조건을 사용하며 원본 지급은 보존/유효 합산 제외한다. 올바른 실제 시작 날짜/월·그 시점 소속/담당/상태·Pass 발급 및 현재 잔여/정산·현재 인가를 검증한다. 새 지원 보상은 기존 별도 관리자 수동 입력·미입력 월 확정 차단을 따르고 원래 보상을 자동 복사하지 않는다. [2026-10-12 K 일괄 승인](product-decisions.md#review-20261012-k-batch).

보상 금액 공개 수용 기준(N1/N2=1): 비관리자 Trainer의 본인 PT 진행 내역과 현재 다른 Home Branch Trainer 수업을 읽는 Performed Branch Admin에게 수업별 일반 지급/수업 연결 지원 보상 금액을 공개하지 않는다. 기록 조회/정정 인가와 금액 열람을 분리하고 등록 성공·목록/직접 ID·중첩 응답 등 제공 경로에서 Backend 비공개를 검증한다. 확정 지급/지원 보상 원본·정산 입력을 유지하며 가짜 0원/삭제/재계산으로 숨기지 않는다. 현재 Home 기반 기존 관리자 보상·정산 업무·Master Organization/겸임 독립 권한 및 다른 비금액 필드의 기존 공개 제한은 유지한다(BR-PAY-021; [N 승인](product-decisions.md#review-20261013-n-batch); V-108/109 미구성·미실행).

담당/개별 지원 등록 수용 기준(O1/O2=1): 허용된 Member의 본인 실제 수업은 다른 Trainer 담당분도 포함한 전체 적격 Pass에서 FIXED_AMOUNT 우선/동일 Type FIFO로 차감한다. 개별 지원 회원은 본인 담당 Pass 없이도 등록할 수 있다. 실제 수업 당시 발급/사용 가능·현재 잔여 > 0·기존 상태/만료 예외/인가·정산 검증을 유지하고 담당자/지점은 자동 변경하지 않는다. 일반 지급은 실제 수행자의 생성 시점 설정으로 확정하고 일반/지원 보상 구분은 실제 수업 당시 Home/Performed로 판단한다. 전체 후보 사용과 외부 정보 공개를 분리하며 BR-PAY-021 금액 제한을 유지한다. 지원 관계의 시간 정책은 BR-OPS-027(P1/P2), 나머지 역사 사실/계약은 후속이다(BR-OPS-026; [O 승인](product-decisions.md#review-20261013-o-batch); V-110/111 미구성·미실행).

지원 관계의 시간 수용 기준(P1/P2=1): 5일 본인 실제 수업 → 6일 지원 지정 → 7일 등록은 현재 허용으로 처리한다. 1일 지정 → 5일 수업 → 6일 해제 → 7일 등록은 실제 허용 기간의 본인 수업에 한해 처리한다. 지정 이력 소급 변경·해제 후 일반 Member/전화번호 조회 복원은 없으며 현재 계정/Trainer·실제 수행/필요한 과거 허용 사실과 O 전체 적격 Pass·기존 잔여/상태/정산 조건을 검증한다. 일반 지급 생성 시점/당시 Home·Performed 보상 구분·N 비공개와 확정 월 관리자 해제 원칙은 유지한다(BR-OPS-027; [P 승인](product-decisions.md#review-20261013-p-batch); V-112/113 미구성·미실행).

Q2 명시적 Fixed Amount 0원도 일반 FIXED_AMOUNT 수업의 실제 설정값으로 계산한다. 서비스 상품도 동일하며 누락을 0원으로 대체하지 않는다. RATE 1,000원 올림을 추가 적용하지 않고 실제 수행자 생성 시점 설정·발급 Pass 조건/과거 확정 지급 불변·N 비공개를 유지한다(BR-PAY-022; [Q 승인](product-decisions.md#review-20261013-q-batch); V-115 미구성·미실행).

T1 후보 시간 기준: 실제 수업 당시 이미 발급된 조건의 발급 시각은 시스템에서 신규 발급을 완료한 시각이다. 이후 입력한 과거 구매일/소급 발급 또는 임의로 바꾼 수업 시각으로 후보를 만들지 않는다. 다른 적격 후보의 기존 우선순위·현재 잔여/만료 예외·현재 인가/정산 조건과 실제 수업 시점의 일반/지원 구분·신규 기록 생성 시점 일반 지급 설정은 유지한다(BR-OPS-031; [T 승인](product-decisions.md#review-20261013-t-batch); V-120 미구성·미실행).

<a id="pr-009"></a>
## PR-009. 제한된 권한의 Session 정정·취소

여기서 정정/취소는 이미 기록한 PT 진행 사실에 대한 처리이며 Future Scope의 미래 예약 취소와 구별한다.

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: Master Admin은 Organization 전체, Branch Admin은 실제 Performed Branch가 관리 Branch인 기록을 허용된 조건 안에서 정정/취소하며 Pass 잔여·월 정산의 일관성과 이력을 유지한다. Performed Branch 자체 오류 정정은 Master Admin만 담당하며 Branch Admin은 기존/실제 지점이 관리 Branch여도 해당 값을 정정할 수 없다(2026-10-11 사용자 확정). Operator 역할만으로는 정산 확정 전후 모두 정정/취소할 수 없다(2026-10-11 사용자 확정). Trainer 역할만으로는 본인 PT 진행 기록도 정산 확정 전후 모두 정정/취소할 수 없다(2026-10-11 사용자 확정). 관리자 겸임자는 해당 업무의 별도 관리 권한·Branch Scope로 판단하며 직접 등록 권한으로 정정 권한을 얻지 않는다.

관리 Scope 수용 기준(2026-10-11 사용자 확정): Master Admin은 Organization 전체, Branch Admin은 PT 진행 기록의 실제 Performed Branch가 관리 Branch인 경우 정정·취소한다. 수원 소속 Trainer의 강남 수업은 강남 Branch Admin이 담당하며 Home Branch만으로 수원 Branch Admin에게 기록 정정 권한을 부여하지 않는다. Trainer 이동으로 과거 수업의 담당 지점을 변경하지 않는다. 추가실적 금액 입력·보상 설정·월 정산 권한을 수행 지점 관리자에게 확대하지 않으며 Operator 권한·Performed Branch 자체 정정·확정 후 교차 담당자 흐름은 잔여 OPEN이다.

수용 기준 / 범위 경계: 단순 행 삭제로 처리하지 않는다. 권한·변경 행위가 감사 가능하며 원래 기록과 관련 과거 이력을 추적할 수 있어야 한다. 정정 허용 항목·잔여 복원·기간별 반영의 상세는 미정이다.

2026-10-11 사용자 확정(Trainer 본인 PT 진행 기록 정정·취소 권한 질문의 1번): Trainer 역할만으로는 본인이 등록하거나 수행한 PT 진행 기록도 정정·취소할 수 없다. 월 정산 확정 전후 모두 적용하며 직접 ID 요청으로도 우회할 수 없다. 허용된 관리 담당자가 해당 업무의 별도 권한·Branch Scope 안에서 처리한다. 관리자·Trainer 겸임자는 Trainer 역할의 본인 권한이 아니라 해당 업무의 관리 권한으로 판단한다. 이 결정으로 다른 역할의 정정 권한이나 Home/Performed Branch 기준을 자동 확정하지 않는다. Trainer의 허용된 PT 진행 등록·본인 내역 조회와 기존 보상 설정/추가실적 권한은 유지한다. 정정 항목·기간·취소 및 지급/정산 연동 상세는 BR-007/009, 관리 Scope와 교차 업무 조건은 ARCH-001/MB-005의 잔여 OPEN이다.

확정 월 타 지점 수업 취소 수용 기준(2026-10-11 사용자 확정): 해당 Trainer·월의 현재 Home Branch 관리자가 정산을 해제하고, 실제 Performed Branch 관리자가 기록을 취소한 뒤 현재 Home Branch 관리자가 같은 월 정산을 재확정한다. 각 요청에서 해당 업무의 현재 권한·관리 Scope를 검증한다. Master는 Organization 범위에서 전체 과정을 처리할 수 있다. 수행 지점의 기록 권한으로 다른 소속 Trainer의 금액 입력/전체 월 정산 권한을 얻지 않는다. 이전 확정본/이력·기존 해제 사유/감사·재확정 조건을 유지하며 취소만으로 자동 재확정하거나 다른 과거 지급/기본급을 현재 설정으로 재계산하지 않는다. 지급/연계 추가실적의 유효 결과·잔여 복원 예외 및 단계 계약/실패·재시도/경합은 잔여 OPEN 또는 PROPOSED다.

2026-10-11 사용자 확정(Operator의 PT 진행 기록 정정·취소 권한 질문의 1번): Operator 역할만으로는 PT 진행 기록을 정정·취소할 수 없다. 정산 미확정/확정 상태 모두 적용한다. Master Admin은 Organization 전체, Branch Admin은 해당 기록의 실제 Performed Branch 범위에서 담당한다. Trainer 역할의 정정·취소 금지와 관리자 겸임자의 해당 관리 권한 판단은 유지한다. Operator의 기존 허용 업무가 정정 권한을 부여하지 않으며 Branch Scope 부여·다른 운영 업무의 상세는 MB-004/ARCH-001 OPEN이다.

2026-10-11 사용자 확정: 허용된 PT 진행 기록 취소는 그 수업 보상의 추가실적 자동 무효 처리를 동반한다. 유효 월 정산/지점 비용에서 제외하되 기존 금액·이력을 보존하고 다른 추가실적은 유지한다. 기존 기록 취소 권한과 Home Branch 기준 금액 입력/전체 정산 권한은 구별하며 확정 월의 기존 해제 → 취소 → 같은 월 재확정 순서를 따른다. 상세 근거는 BR-PAY-015/PD-027. 나머지 정정/취소·복원 예외 및 계약/원자성/동시성은 후속 대상이다.

수행 지점 오류 정정 수용 기준(2026-10-11 사용자 확정): Master Admin의 Organization 범위를 확인한다. Branch Admin은 기존 기록/실제 수행 지점에 대한 관리 권한만으로 Performed Branch 값을 정정할 수 없고 직접 ID/위조 Role·Branch Context로 우회할 수 없다. 원본·변경 이력을 보존하며 이 권한 결정만으로 지급액/지급 방식 변경이나 확정 월의 자동 변경을 구현하지 않는다. 지점 오류 정정 방식·확정 월 연계·보상 전환 및 적용 설정 시점은 잔여 OPEN이다.

2026-10-11 사용자 확정: 수행 지점 오류는 Master가 기존 기록을 정정하고 일반/지원 보상 방식도 바로잡는다. 기록/원래 Pass 차감은 유지하며 취소/재등록·복원/재차감하지 않는다. 변경 전후 사실/보상 이력 보존·잘못된 방식의 보상 중복 합산 금지·지원 전환의 관리자 수동 금액 입력/미입력 월 확정 차단을 따른다. 확정 월에는 기존 해제 → 정정 → 같은 월 재확정·이전 확정본 보존을 동일 적용한다(사용자 일관성 지시). 지원→일반 전환의 지급 설정 기준 시점·나머지 정정 조건/계약 상세는 BR-007/MB-005의 잔여 OPEN이다.

2026-10-11 사용자 확정: 수행 지점 정정으로 지원 수업을 일반 PT로 바꿀 때 Rate/Fixed Amount는 기존 PT 기록의 최초 생성 시점 기준으로 적용한다(BR-PAY-011). 최초 등록 때 Rate 50%, 정정 때 60%이면 50%이며 Fixed Amount도 같은 원칙이다. 설정 근거 확인/이력·저장 계약은 후속 설계다.

승인 근거: PD-010/011/012/022. [Product Decisions](product-decisions.md)

후속 TODO: BR-007, ARCH-001, MB-005. [Open Questions](open-questions.md)

AS-IS reference: F20, F21. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

2026-10-12 C 일괄 승인 수용 기준: C10: Member/실제 Trainer 오류는 기존 PT 기록 취소→올바른 재등록으로 정정하고 원본·취소·정정 연결을 보존한다. 새 일반 지급은 재등록 생성 시점 설정, 지원 보상은 기존 수동 AP다. 기존 Pass 복원/우선 선택·Performed Branch 관리자 Scope와 그 값의 Master 전용 정정·영향받는 확정 Trainer/월의 해제/재확정 조건을 유지한다(BR-OPS-018). [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 K1=1: 실제 시작 날짜/시각 오류도 원본 취소 후 올바르게 재등록/연결하며 새 일반 지급은 재등록 생성 시점 설정으로 계산한다(BR-OPS-023). 기존 소비 복원·올바른 시점의 소속/상태·이미 발급된 적격 Pass/현재 잔여 재검증·우선 재선택/1회 차감과 각 단계 현재 인가/영향받는 확정 월 해제·처리·재확정을 따른다. Performed Branch 값 정정의 Master 전용/기록 유지·최초 생성 기준은 별개로 유지한다. [2026-10-12 K 일괄 승인](product-decisions.md#review-20261012-k-batch).

V1 영향 정정 경계: 과거 Home 이력 오류 정정 허용은 기존 수업의 수행자/Member·실제 시작/Performed Branch·Pass 소비·지급 원본을 자동 변경하는 지시가 아니다. 영향 건은 기존 행위별 정정/확정 해제·재확정 권한과 사유·이전본 보존 절차를 따르며, 소속 오류로 일반/지원 분류가 달라지는 PT의 유지/취소 재등록·일반 지급 적용 시점은 별도 미결정 게이트다(BR-OPS-032; [V 승인](product-decisions.md#review-20261013-v-batch); V-123 미구성·미실행).

W1 수용 기준: 실제 Member/수행자/시작/Performed가 그대로인 Trainer 과거 Home 오류의 일반/지원 전환은 같은 PT 식별자/최초 생성 시각·소비 Pass/차감을 유지하는 Master Organization 전용 정정이다. 취소 재등록/복원·재차감/재선택은 하지 않는다. 지원→일반은 최초 기록 생성 시점 실제 수행 Trainer 설정/기존 Pass 발급 조건을 적용하고 일반→지원은 기존 관리자 범위 수동 추가실적을 사용한다. 이전 보상 이력을 보존하되 두 종류를 유효 합계에 이중 반영하지 않는다. 실제 Member/수행자/시작 오류의 기존 취소 재등록 규칙은 유지한다(BR-OPS-033; [W 승인](product-decisions.md#review-20261013-w-batch); V-124 미구성·미실행).

<a id="pr-010"></a>
## PR-010. 기본급·Session·추가실적 월별 트레이너 정산

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: Monthly Settlement = 해당 월 적용 Base Salary + 유효한 Session Payment 합계 + 유효한 Additional Performance 합계다. Trainer·대상 월·적용 기본급·Session 수·Session Payment 합계·추가실적 내역/합계·월 정산 합계를 구분한다. 2,500,000원 + 1,200,000원 + 150,000원 = 3,850,000원이며 여러 지점 수업으로 동일 월 기본급을 중복 가산하지 않는다. 타 지점 수업의 보상 전체는 Additional Performance로 반영하며 일반 Session Payment를 별도로 합산하지 않는다(MB-009 CLOSED, 2026-10-10 사용자 정정).

정산 조회 수용 기준(2026-10-11 사용자 확정): Branch Admin은 조회 시점에 자신의 관리 Branch를 Home Branch로 가진 Trainer의 해당 월 정산 전체 금액과 구성 내역을 조회할 수 있다. 해당 월 적용 기본급·일반 Session Payment·타 지점 지원 수업을 포함한 Additional Performance·월 정산 총액을 모두 공개하며, 수업의 Performed Branch가 다른 지점이라는 이유로 해당 금액을 제외하거나 숨기지 않는다. 관리 범위 안 본인 Trainer도 포함하며 Master의 Organization 전체 조회는 유지한다. 자기 지점에서 수업한 다른 Home Branch Trainer의 전체 월 정산은 그 수행 사실만으로 공개하지 않는다. 직접 ID·목록·검색·집계 조회에 Backend Scope 검증을 적용하고, 대상 월·이전 확정본/세부 계산 근거·감사 공개 등 남은 상세와 비용 귀속은 MB-006/010을 따른다.

지원 수업 비용 집계 경계(2026-10-11 사용자 확정): 타 지점 지원 수업의 전체 보상으로 확정한 Additional Performance 금액은 해당 수업의 실제 Performed Branch 비용으로 집계한다. Trainer의 월 정산에는 같은 추가실적을 한 번만 합산하며 별도 지점별 Trainer 정산이나 추가 지급을 생성하지 않는다. 기존 권한·확정본 보존을 유지한다. 다른 보상 항목 귀속·비용 보고 공개/집계 상세는 MB-010/006 OPEN이다.

이동월 기본급 비용 수용 기준(2026-10-11 사용자 확정): 월중 Trainer 지점 이동이 있는 달의 해당 월 적용 기본급 비용은 대상 월의 월말 Home Branch 한 곳에 전액 귀속한다. 10월 수원→강남 이동, 적용 기본급 2,500,000원이면 강남점 비용에 전액 집계하고 수원/강남으로 분할하지 않는다. 해당 월 수동 적용액이 1,500,000원이면 강남점 비용도 1,500,000원이다. 지급액·한 번 합산·기존 관리 권한·확정본 보존은 유지한다. 이후 소속 이동만으로 과거 비용 지점을 바꾸지 않는다. 월말 소속 식별 불가 등 예외·다른 보상 귀속·비용 보고 공개/집계 상세는 MB-001/010/006 등 관련 OPEN이다.

일반 PT 수당 비용 수용 기준(2026-10-11 사용자 확정): 일반 Session Payment는 해당 PT 진행 기록의 실제 Performed Branch 비용으로 집계한다. 이미 확정된 수업별 지급액을 지점별로 합산하며 대상 월말 Home Branch로 전액을 모으지 않는다. 같은 Trainer의 수원점 일반 수당 200,000원·강남점 일반 수당 300,000원이면 각각의 비용으로 집계하고 Trainer 합계 500,000원은 유지한다. 현재 보상 설정으로 재계산·합계 추가 올림·별도 중복 지급은 하지 않는다. 지원 수업은 Additional Performance만 반영하고 이동월 기본급은 월말 Home Branch 전액 귀속을 유지한다. 이후 소속 이동만으로 과거 비용 지점을 바꾸지 않으며 비용 귀속으로 기존 인가/조회 Scope를 확대하지 않는다. 남은 정정/취소·다른 추가실적 귀속·비용 보고 공개/집계 상세는 관련 OPEN이다.

지원 수업 외 추가실적 비용 경계(2026-10-11 사용자 확정): 지원 수업 외 Additional Performance의 비용은 실적 발생 당시 대상 Trainer의 Home Branch에 귀속한다. 등록 시점·금액 확정 시점·대상 월말 또는 조회 시점의 소속으로 대체하지 않는다. 해당 보상의 Trainer 월 정산 금액과 한 번 합산은 유지한다. 등록/월말/조회 시점의 소속을 과거 비용 지점으로 대체하지 않으며 기존 관리 권한을 확대하지 않는다. 지원 수업 외 추가실적의 남은 입력 제약·정산 월과 비용 보고 공개/집계 상세는 관련 OPEN이다.

지점별 비용 보고서 조회 수용 기준(2026-10-11 사용자 확정): v1 지점별 비용 보고서는 Master Admin만 Organization 범위에서 조회한다(2026-10-11 사용자 확정). Branch Admin은 자기 지점 비용 합계도 이 보고서로 조회할 수 없으며 Master 권한 없는 Operator·Trainer도 불가하다. Branch Admin의 현재 자기 Home Branch 소속 Trainer 해당 월 정산 전체 금액·구성 내역 조회는 타 지점 지원 보상까지 포함하여 유지한다. 비용 귀속·지급액·기존 등록/정정/확정 권한은 유지하며 보고서 항목·대상 월·집계/완전성·버전 등 남은 상세는 MB-006/010 OPEN이다. Master Admin·Trainer 겸임은 Master 권한으로 허용하고 Branch Admin·Trainer 겸임만으로는 허용하지 않는다. Master에게도 다른 Organization 보고서를 공개하지 않는다.

지원 수업 외 추가실적의 월 정산 입력 기준(2026-10-11 사용자 확정): 실제 실적 발생 월의 유효 추가실적을 해당 Trainer·월 입력으로 집계한다. 9월 실적을 10월에 등록해도 9월분이며 10월 입력으로 이월하거나 두 월에 중복 합산하지 않는다. 비용의 발생 당시 Home Branch 귀속과 기존 관리/조회 권한·확정본 보존은 유지한다. 확정된 발생 월 후등록은 해당 Trainer·월의 해제 → 누락 실적 등록 → 재확정과 이전 확정본 보존으로 후속 확정했다. 해제/재확정 본인 건 허용·별도 승인 없음도 확정됐으며 남은 정정/취소 상세는 BR-009/013의 별도 OPEN이며 확정 상태에 자동 갱신하지 않는다.

지원 수업 외 누락 실적의 확정 월 후등록 수용 기준(2026-10-11 사용자 확정): 해당 Trainer·발생 월 확정 해제 → 누락 실적 등록 → 동일 월 재확정 순서를 따른다. 이전 확정본을 보존하고 새 재확정 결과와 구분하며 다른 월 이월/중복 합산 없음. 재확정은 기존 확정 조건을 재검증하고 과거 일반 지급/적용 기본급을 현재 설정으로 자동 변경하지 않는다. 이 흐름의 해제/재확정 본인 건 허용·별도 승인 없음도 확정했고 구체 단계별 계약/실패 처리는 별도 설계 대상이다.

지원 수업 외 실적 등록 및 확정 월 누락분 반영의 해제·재확정은 Master Organization 전체/Branch Admin 각 처리 시점 Trainer 현재 Home Branch 기준으로 인가(Product 확정, 2026-10-11). 단계마다 재검증하며 이전 소속/발생 당시 소속만으로 권한 없음. 발생 월 정산·발생 당시 Home Branch 비용 귀속은 유지. 이 후등록의 해제/재확정 본인 건 허용·별도 승인 없음은 확정(2026-10-11). 기존 실적 정정/취소는 별도 OPEN.

확정 월의 누락된 지원 수업 외 실적 반영을 위한 해제 사유 필수(Product 확정, 2026-10-11). 사유 없는 해제 요청은 거부하고 요청 직전 확정 상태/확정본/기존 실적·정산 구성/금액 유지. 성공 시 대상 Trainer/월·사유·해제자·시점 이력/감사와 이전 확정본 보존. 현재 Home Branch 인가·기존 후등록 순서/월/비용 귀속 유지. 이 흐름의 해제/재확정은 관리 범위 안 본인 건도 별도 승인 없이 허용(2026-10-11).

Branch Admin의 본인이 아닌 소속 Trainer 누락 실적 후등록 해제/재확정은 별도 Master 승인 없음(Product 확정, 2026-10-11). 각 처리 시점 현재 Home Branch 인가·해제 사유 필수·해제 후 등록/동일 월 재확정·이전 확정본/감사·기존 확정 조건/미입력 지원 수업 차단 유지. 관리 범위 안 관리자 본인 건의 해제/재확정 허용·별도 승인 없음도 확정(2026-10-11).

관리 범위 안 관리자·Trainer 겸임자의 본인 누락 실적 후등록 해제/재확정도 별도 승인 없이 허용(Product 확정, 2026-10-11). Master Organization 범위/Branch Admin 각 처리 시점 본인 현재 Home Branch 일치·해제 사유 필수·본인 감사/이전 확정본 보존·기존 후등록 순서/월/비용 귀속·재확정 조건/미입력 지원 수업 차단 유지. Trainer 단독 권한 없음. 비지원 실적의 금액 외 정보 수정/취소 등은 OPEN.

월 정산 확정 전 비지원 추가실적 금액 수정은 Master Organization 전체/Branch Admin 각 수정 시점 Trainer 현재 Home Branch 기준으로 허용(Product 확정, 2026-10-11). 관리 범위 안 본인 건 포함·별도 승인 없음·변경 사유 필수·전후 금액/사유/수정자/시점 이력과 감사. 사유 누락 거부/요청 직전 금액 유지. 발생 월/당시 Home Branch 비용 유지. 수정 금액의 나머지 입력 제약, 금액 외 정보 수정/취소는 OPEN.

지원 수업 외 추가실적은 최초 등록과 확정 전 금액 수정 모두 양수만 허용(Product 확정, 2026-10-11 사용자 일관성 지시 적용). 0원·음수·누락 수정 거부/요청 직전 금액·이력·정산 입력 상태 유지; 사유가 있어도 0원 수정 불가. 기존 관리자 Scope/본인 건/승인 생략/사유·이력/감사 유지. 지원 수업 보상 및 월별 수동 기본급의 승인된 사유 필수 0원 예외는 유지. 상한/정밀도·금액 외 정보 수정/취소는 OPEN.

지원 수업 외 실적의 확정 후 금액 오류도 해당 Trainer/월 해제 → 양수 금액 정정 → 같은 월 재확정·이전 확정본/구성/이력 보존(2026-10-11 사용자 일관성 지시 적용). Master Organization/Branch Admin 각 처리 시점 현재 Home Branch·본인 건 포함·별도 승인 없음·해제/정정 모두 사유 필수·감사·기존 재확정 조건/미입력 지원 수업 차단 유지. 발생 월/당시 Home Branch 비용 유지. 금액 외 정보 수정/취소·나머지 기간/금액 제약은 OPEN.

최초 확정 수용 기준(2026-10-11 사용자 확정): 월 정산의 최초 확정은 Master Admin에게 Organization 전체 Trainer, Branch Admin에게 확정 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 직접 확정한다. 관리자 권한이 없는 Operator·Trainer, 현재 관리 범위 밖의 Branch Admin은 직접 ID 요청과 위조 Branch Context로도 최초 확정할 수 없다. 과거 소속이나 수업 수행 지점만으로 허용하지 않는다. 아래 지원 수업 미입력 차단 등 승인된 확정 조건을 검증하며 자동 확정하지 않는다. 상세 공개·비용 귀속·나머지 확정/마감 조건은 관련 OPEN이다.

수용 기준 / 범위 경계: 해당 Trainer의 해당 월 정산 대상 지원 수업에 금액 미입력 건이 하나라도 있으면 그 Trainer·월 정산을 확정할 수 없다. 미입력 건을 제외하거나 0원으로 간주한 확정을 허용하지 않으며 해당 Trainer·월의 차단이다. 모든 금액 입력은 이 조건 해소이며 정산 자동 확정이 아니다. 타 지점 지원 수업 보상은 권한 있는 관리자가 사유를 기록하면 0원으로 명시적으로 확정할 수 있다. 사유 없는 0원 입력은 보상 확정이 불가하다. 사유를 남기고 확정한 0원은 금액 미입력이 아니므로 그 건으로 월 정산 확정을 차단하지 않는다. 다른 미입력 건이 남으면 기존 차단 조건을 유지한다. 현재 Base Salary 변경으로 과거 확정 정산의 적용 기본급과 합계가 자동 변경되지 않는다. 현재 Rate/Fixed Amount로 과거 확정 Session Payment를 재계산하지 않으며 월 합계에 RATE 올림을 다시 적용하지 않는다. 권한 있는 과거 정정과 현재 설정 변경의 자동 소급은 별개다. 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer의 지원 수업 보상 정정을 위해 월 정산을 확정 해제·재확정할 때는 Master의 별도 승인을 두지 않는다. Master 승인 대기 단계 없이 관리 범위 안에서 직접 처리하며 이전 확정본과 해제·재확정 이력 및 감사를 유지한다. 지원 수업 보상 정정의 월 정산 확정 해제에는 사유가 필수이며, 사유 없이 해제할 수 없다. 사유·해제자·시점을 이력으로 남긴다. 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 남은 절차는 BR-009/013 OPEN이다. Master Admin은 전체 정산 관리, Branch Admin 결과 공개 범위는 MB-006이며 설정 접근 권한으로 전체 정산 열람을 자동 허용하지 않는다. 기본급 일할·근무일수·휴직 자동 계산과 수동 매출 합산은 제공하지 않는다.

추가 수용 기준(2026-10-10 사용자 결정): 확정된 월의 기본급 오류는 해당 Trainer·월의 확정 해제 → 해당 월 적용 기본급 정정 → 동일 월 재확정으로 처리하고 이전 확정본은 이력으로 보존한다. 현재 설정 변경에 따른 자동 갱신과 구별한다. 기본급 오류 정정의 확정 해제·재확정은 Master Admin에게 Organization 전체, Branch Admin에게 각 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 처리한다. 확정된 월의 기본급 오류 정정에서 확정 해제와 해당 월 기본급 수정 모두 사유가 필수다. Master Admin·Branch Admin 및 관리 범위 안 본인 건에 동일하게 적용한다. 해제 사유·해제자·시점과 변경 전후 기본급·수정 사유·수정자·시점을 이력으로 남긴다. 사유 없는 각 요청은 해당 작업을 거부하며 요청 직전 상태·금액·기존 확정본을 변경하지 않는다. 기본급 오류 정정은 대상 Trainer의 해당 월 정산에만 적용하며 현재·미래 기본급 설정과 다른 월 정산은 유지한다. 지속적인 기본급 변경은 별도로 적용 시작 월을 지정하는 기존 흐름을 따른다. 미리 등록할 수 있는 미래 적용 시작 월의 범위 등 남은 정책은 BR-012 OPEN이다. 재확정에도 미입력 지원 수업 차단 등 승인된 확정 조건을 적용한다. 과거 일반 Session Payment를 현재 Rate/Fixed Amount로 재계산하거나 PT 진행 기록·Pass 차감을 재실행하지 않는다.

추가 수용 기준(2026-10-10, 입사·퇴사·휴직 월 기본급): 입사·퇴사·휴직이 있는 달의 적용 기본급은 관리자가 해당 Trainer·월의 금액을 직접 지정한다. 예를 들어 월 기본급 설정이 2,500,000원이어도 해당 월만 1,500,000원을 적용할 수 있으며, 이 지정으로 현재·미래 기본급 설정과 다른 월 정산은 변경하지 않는다. 해당 월 합계에는 지정 금액을 기본급으로 한 번만 가산한다. 이미 확정된 월은 기존 해제/정정/재확정 조건과 이전 확정본 보존을 따른다. 자동 일할 계산 및 정산 자동 확정은 제공하지 않는다. 월별로 수동 지정한 기본급은 이후 일반 기본급 설정이 변경되어도 유지한다. 일반 설정 변경의 미확정 정산 자동 반영은 수동 지정이 없는 월에 적용하며, 수동 지정 월의 금액을 바꾸려면 관리자가 해당 월 금액을 직접 수정한다. 미확정 월의 기본급을 최초 수동 지정하거나 다시 수정할 때 모두 사유가 필수다. 사유가 없는 요청은 거부하고 요청 직전의 수동 지정 여부·적용 금액·월 합계를 유지한다. 대상 Trainer·월, 지정/수정 전후 금액·사유·처리자·처리 시점을 이력으로 남긴다. 미확정 월 기본급의 최초 수동 지정·수정은 Master Admin의 Organization 전체, Branch Admin의 각 처리 시점 대상 Trainer 현재 Home Branch가 관리 Branch와 일치하는 범위에서 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 직접 처리한다. 추가 사용자 확정(2026-10-11): 해당 월 기본급은 권한 있는 관리자가 사유를 남기면 0원으로 명시적으로 수동 지정할 수 있다. 수동 지정한 0원은 미입력과 구분하며, 미입력이나 누락된 일반 설정을 자동으로 0원으로 대체하지 않는다. 해당 월 기본급에만 적용하고 다른 유효 지급·추가실적은 기존 규칙대로 합산한다. 미리 등록할 수 있는 미래 적용 시작 월의 범위와 월별 수동 지정 금액의 나머지 입력 제약 등은 BR-012/BR-010 OPEN이다.

확정 후 타 지점 수업 취소의 정산 연계(2026-10-11 사용자 확정): 해당 Trainer·월의 현재 Home Branch 관리자 해제 → 실제 Performed Branch 관리자 기록 취소 → 현재 Home Branch 관리자 같은 월 재확정 순서를 따른다. Master의 Organization 전체 처리 권한과 기존 확정본/이력·재확정 조건을 유지한다. PR-009/PD-010의 범위를 따르며 지급/추가실적 연동·잔여 복원 예외와 계약/단계 실패·동시성의 나머지 상세는 BR-007/009/013 및 Architecture 후속 대상이다.

승인 근거: PD-009/010/011/012/013. [Product Decisions](product-decisions.md)

후속 TODO: BR-007/008/009/010/012/013, MB-006/010; 추가실적 산정·확정·관리자가 지정하는 미리 등록할 수 있는 미래 적용 시작 월의 범위·귀속·공개 및 남은 마감/정정 정책. 지원 수업 금액 오류의 해당 월 확정 해제/정정/재확정과 이전 확정본 보존·지원 수업 정정 시 Master Organization/Branch Admin 대상 Trainer Home Branch 기준 해제·재확정 권한·해당 Branch Admin 정정의 별도 Master 승인 없음·지원 수업 정정의 확정 해제 사유 필수 기록·지원 수업 정정의 처리 시점 현재 Home Branch 인가 기준은 확정. MB-009의 보상 분류는 CLOSED다.

AS-IS reference: F26. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

2026-10-12 H 일괄 승인 반영: H2–H4=1: 비지원 추가실적 정정/취소가 확정 정산에 영향을 주면 각 대상 Trainer/월의 기존 해제/처리/재확정·사유/이전본 보존을 따른다. 관리자 권한 없는 Trainer의 본인 월 정산 시스템 조회는 v1 제외/관리자 안내이며 본인 PT 진행 내역 조회는 유지한다. 관리자 겸임은 독립 현재 관리 Scope로 본인 포함 기존 정산 조회가 가능하다. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch). 실제 계약/구현·검증은 후속이다.

확정 시점 수용 기준 추가(L1=1): Asia/Seoul 기준 종료된 월만 최초 확정/재확정할 수 있다. 다음 달 1일 00:00 전에는 해당 월을 확정할 수 없고 Master도 당월/미래 월 조기 확정이 불가하다. 당월은 기존 관리자 Scope 안에서 미확정 조회/검토하며 비관리자 Trainer 월 정산 공개를 추가하지 않는다. 종료만으로 자동 확정하지 않으며 기존 지원 보상 미입력 차단·구성/유효성·현재 Trainer Home 기반 확정 권한/감사·이전 확정본 보존을 모두 유지한다. 미래 기본급 적용 시작 월 지정과 별개다(BR-PAY-020; [L 승인](product-decisions.md#review-20261013-l-batch); V-104 미구성·미실행).

Q2 일반 Base Salary 0원은 해당 설정 적용 월의 기본급 0원이다. 다른 유효 지급/추가실적을 합산하고 설정 누락/미적용 월을 임의 0원으로 대체하지 않는다. 시작 월부터 다음 변경까지 지속·월별 수동 지정/사유/확정 해제/재확정·과거 확정본 보존을 유지하며 미래 시작 월 범위/다른 월 적용 사실은 후속이다(BR-PAY-022; [Q 승인](product-decisions.md#review-20261013-q-batch); V-115 미구성·미실행).

S1 이력 수용 기준: 이전 확정본·확정 해제/재확정 이력은 Master 자기 Organization 또는 각 조회 시점 대상 Trainer 현재 Home Branch Admin이 조회한다. 이전 소속 시기의 위 이력도 현재 Home 관리자가 확인하며 이전 소속 관리자는 과거 사실만으로 접근하지 못한다. 당시 확정 금액/구성·버전과 정정 이유/변경자/시점을 보존하고 현재 설정으로 재계산하지 않는다. 기존 전체 정산 공개·본인 독립 관리 Scope/비관리자 Trainer 월 정산 제외·Master 전용 지점 비용 보고 및 별도 쓰기 권한/조건은 유지한다. 추가 필드/최소 계약은 후속이다(BR-PAY-023; [S 승인](product-decisions.md#review-20261013-s-batch); V-118 미구성·미실행).

W2 수용 기준: 과거 Home 오류에 영향받은 분류/보상·비용 정정이 남아 있으면 해당 Trainer·월의 최초 확정/재확정을 거부한다. 경고만으로 확정 허용·임의 완료/0원 대입은 불가다. 관련 없는 Trainer·월은 차단하지 않고 소속 정정만으로 기존 확정본을 자동 해제/변경하지 않는다. 필요한 월의 기존 현재 권한/사유·해제/명시적 정정/같은 월 재확정·이전본 보존과 종료 월/지원 금액 미입력 차단 등 기존 조건을 유지한다. 영향 건 식별/완료 증거/최소 계약·경합은 상세 설계 대상이다(BR-PAY-024; [W 승인](product-decisions.md#review-20261013-w-batch); V-125 미구성·미실행).

Y1/Y2 수용 기준: Master 자기 Organization 전용 지점 비용 보고서는 한국 시간 기준 종료된 월만 조회하고, 각 Trainer·월의 미완료 영향 없는 현재 유효 최신 확정본만 비용 합계에 한 번 반영한다. 미확정/확정 해제 중/과거 Home 오류 영향 정정 대기는 합계에서 제외하고 대상·미완료 사유를 표시하며 전체 월 비용 완성·0원으로 취급하지 않는다. 현재 설정/소속으로 과거 비용 재계산·이전/최신본 이중 합산·원본 자동 해제/변경은 없다. 기존 당월 Trainer 월 정산 조회와 비용 귀속/이전본·감사 보존/현재 인가·정정/재확정은 유지한다. 월 대상 집합/보고 상세·완전성/역사 사실·버전/최소 계약·동시 조회는 후속이다(BR-PAY-025; [Y 승인](product-decisions.md#review-20261013-y-batch); V-127/128 미구성·미실행).

Z1 수용 기준: Master 전용 지점 비용 보고서에 지점별 합계와 기본급/일반 PT 수당/지원 수업 보상/기타 추가실적별 소계, 해당 지점 비용에 기여한 Trainer별 항목/금액을 제공한다. Trainer 월 전체 지급액을 각 지점에 복제하지 않고 기존 귀속/한 번 합산으로 Trainer별 합계↔지점 소계/총계↔포함된 전체 확정 비용을 검산한다. Y1/Y2 종료 월·미완료 영향 없는 최신 유효 확정본/미완료 제외·표시를 목록/상세/집계에 일관 적용하며 현재 Master Org Scope와 원본/이전본 보존을 유지한다. 최소 식별/응답·대상/미완료·역사 비용/버전/동시 조회 계약은 후속이다(BR-PAY-025; [Z 승인](product-decisions.md#review-20261013-z-batch); V-129 미구성·미실행).

AA1/AA2 수용 기준: 최초 일반 기본급 시작 월보다 이른 유효 PT/실적 정산 월은 기존 관리자 Scope에서 사유를 남겨 월별 기본급을 명시 지정하고 이후 일반 설정은 유지한다. 미래 시작 월은 지원 유효 연월 안에서 업무상 기간 상한 없이 선택하며 한 시작 월부터 다음 변경까지 계속 적용한다. 기존 명시0원/미입력 자동0 금지·인가/감사·수동 월/확정본 보존·확정 조건을 유지한다(BR-PAY-014; [AA 승인](product-decisions.md#review-20261013-aa-batch); V-130/131 미구성·미실행).

AB1/AB2 수용 기준: BR-PAY-026의 설정/유효 수업·실적/기존 이력·미완료 기반 대상 자동 선정과 확인된 월전체 비활성·명시 기본급0·무활동·정정대기 없음의 새 확정 의무 예외를 적용한다. 현재 상태/기존 정산 행만으로 누락을 숨기지 않고 현재 Home 인가·원본/미완료/확정 조건을 유지한다. 자동 확정/비활성 기본급 자동0은 하지 않는다([AB 승인](product-decisions.md#review-20261013-ab-batch); V-132/133 미구성·미실행).

<a id="pr-011"></a>
## PR-011. 추가 연간 통계 검토

처리 상태: TBD

v1 범위: OUT-V1

출처: AS-IS-DERIVED

제품 요구: 추가 연간 합계·월별 추이는 v1에서 제외하고 후속 필요 확인 시 별도 채택한다(I4). 필수 월 정산과 이미 승인된 Master 전용 지점 비용 보고서는 v1에서 유지한다.

수용 기준 / 범위 경계: 통계/집계에도 Branch Data Scope와 지급정보 기밀성을 적용한다. 12개월 고정 평균과 수입/매출 혼합 표를 자동 복제하지 않는다. 정산 업무 정보는 PR-010이며 Actor별 동일 노출을 요구하지 않는다.

승인 근거: PD-006/012 및 I4의 v1 제외/보류 승인. PD-013은 수동 매출 제외 결정이며 추가 연간 통계 승인 근거와 구분한다. [2026-10-12 I 일괄 승인](product-decisions.md#review-20261012-i-batch).

후속 TODO: 추가 연간 통계 채택 시 별도 요구/권한/범위 승인. BR-009·MB-006/010의 기존 월 정산/지점 비용 보고서 상세는 별도 OPEN이다.

AS-IS reference: F27. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

2026-10-12 I4=1: 추가 연간 통계 화면/API·합계/월별 추이는 v1 보류다. 기존 정산/비용 보고서 권한·민감정보 제한을 유지하고 클라이언트 합산으로 v1 범위/열람 제한을 우회하지 않는다. [2026-10-12 I 일괄 승인](product-decisions.md#review-20261012-i-batch).

<a id="pr-012"></a>
## PR-012. 수동 트레이너 매출

처리 상태: TBD

v1 범위: OUT-V1

출처: AS-IS-DERIVED

제품 요구: v1에 제공하지 않는다. 기존 자료 조회·이관도 하지 않는다.

수용 기준 / 범위 경계: 후속 실제 필요가 확인되면 별도 요구사항으로 정의한다. AS-IS 기본 입력 경로 차단(K37)은 그대로 참조로 남긴다.

승인 근거: PD-006/013/017. [Product Decisions](product-decisions.md)

후속 TODO: 현재 구현 TODO 없음. [Open Questions](open-questions.md)

AS-IS reference: F22, F23, F24, F25. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-013"></a>
## PR-013. 락커 운영

처리 상태: TBD

v1 범위: OUT-V1

출처: AS-IS-DERIVED

제품 요구: 배정·기간·소유자 검색·마감·현황은 모두 v1 제외다.

수용 기준 / 범위 경계: 향후 별도 기능 후보이며 PT 수용 기준에 락커를 끼워 넣지 않는다.

승인 근거: PD-006/016. [Product Decisions](product-decisions.md)

후속 TODO: 현재 구현 TODO 없음. [Open Questions](open-questions.md)

AS-IS reference: F28, F29, F30, F31, F32, F33. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-014"></a>
## PR-014. 락커 글꼴 조절

처리 상태: DROP-CANDIDATE

v1 범위: OUT-V1

출처: AS-IS-DERIVED

제품 요구: 기존 글꼴별 ± 기능은 후보로만 보존한다. 락커 자체가 v1 제외다.

수용 기준 / 범위 경계: 존재 자체를 구현 근거로 쓰지 않는다. Responsive Web은 별도 NFR-008 요구다.

승인 근거: PD-005/016/023. [Product Decisions](product-decisions.md)

후속 TODO: 실제 필요 확인 시 후속 검토. [Open Questions](open-questions.md)

AS-IS reference: F34. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-015"></a>
## PR-015. Responsive Web에서 핵심 업무 이동

처리 상태: REDESIGN

v1 범위: IN-V1

출처: AS-IS-DERIVED + APPROVED-TO-BE

제품 요구: Desktop/Tablet/Smartphone에서 허용된 Member·Pass·Session·Settlement 등 사용자별 핵심 업무를 수행하는 Responsive Web을 제공한다.

수용 기준 / 범위 경계: 터치 조작과 작은 화면의 주요 정보/Action을 지원하며 Desktop 단순 축소는 불충족이다. Trainer의 Smartphone 로그인·허용 Member/PT 조회·실제 Branch/날짜 확인·Session 등록·본인 Session 조회가 실질적으로 가능해야 한다. 현재 Branch·대상 Member·Pass·진행일·정산 기간을 혼동하지 않아야 한다. breakpoint와 Frontend 기술은 후속이다.

승인 근거: PD-001/005/006/007/008. [Product Decisions](product-decisions.md)

후속 TODO: ARCH-004, UX-001. [Open Questions](open-questions.md)

AS-IS reference: F35. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-016"></a>
## PR-016. 데스크톱 창 조작·종료

처리 상태: DROP-CANDIDATE

v1 범위: NOT-COMMITTED

출처: AS-IS-DERIVED

제품 요구: 창 드래그·최소화·프로세스 종료는 존재만으로 구현하지 않는다.

수용 기준 / 범위 경계: 안전한 웹 접근 종료는 PR-026으로 별도 취급한다. 후보의 영구 폐기를 확정하지 않는다.

승인 근거: PD-019/023. [Product Decisions](product-decisions.md)

후속 TODO: 실제 필요 확인 시 후속 검토. [Open Questions](open-questions.md)

AS-IS reference: F36. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-017"></a>
## PR-017. 가계부 거래·자산·분류

처리 상태: TBD

v1 범위: OUT-V1

출처: AS-IS-DERIVED

제품 요구: v1 제외. PT 관리와 별도 bounded context 후보로 취급한다.

수용 기준 / 범위 경계: 현재 별도 구조·연동·장부 규칙을 설계하지 않는다. 기존 거래·잔액 승계 없음.

승인 근거: PD-006/014/017. [Product Decisions](product-decisions.md)

후속 TODO: 후속 Product Expansion. [Open Questions](open-questions.md)

AS-IS reference: F37, F38, F39, F40, F41, F42, F43, F44, F45, F46, F47, F48. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-018"></a>
## PR-018. 고정 거래

처리 상태: TBD

v1 범위: OUT-V1

출처: AS-IS-DERIVED

제품 요구: 가계부 제외에 따라 v1 제외 및 실행 정책 보류다.

수용 기준 / 범위 경계: 로그인 시 고정 거래 생성은 웹 로그인 요구가 아니다.

승인 근거: PD-006/014/015. [Product Decisions](product-decisions.md)

후속 TODO: 후속 가계부 채택 전까지 보류. [Open Questions](open-questions.md)

AS-IS reference: F49, F50, F51, F53. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-019"></a>
## PR-019. 가계부 자산·부채·순자산 통계

처리 상태: TBD

v1 범위: OUT-V1

출처: AS-IS-DERIVED

제품 요구: 가계부와 함께 v1 제외다.

수용 기준 / 범위 경계: Session 지급 정산에 금융 잔액을 포함하지 않는다.

승인 근거: PD-014. [Product Decisions](product-decisions.md)

후속 TODO: 후속 Product Expansion. [Open Questions](open-questions.md)

AS-IS reference: F52. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-020"></a>
## PR-020. Organization / Branch 관리

처리 상태: REDESIGN

v1 범위: IN-V1

출처: AS-IS-DERIVED + APPROVED-TO-BE

제품 요구: 하나의 Organization 아래 여러 Branch를 운영한다. Master Admin은 모든 Branch 조회·등록·정보 관리 및 Branch 구조를 관리하고 기존 데이터가 있는 지점도 비활성화할 수 있다(B6/BR-OPS-016). 비활성 이후 처리는 G1–G5를 따르며 재활성화의 상세 절차는 후속이다. Branch는 실제 운영 지점이며 Multi-Branch는 Multi-Tenant SaaS 확정이 아니다.

수용 기준 / 범위 경계: Trainer는 한 시점에 Home Branch 하나에 소속되고 Branch에는 여러 Trainer가 있을 수 있다. Branch당 Trainer 한 명인 1:1이나 Trainer 동시 복수 소속 N:M을 요구하지 않는다. Member도 Home Branch 하나를 가지며 Pass는 Issued Branch 하나를 가진다. Trainer·Member·Pass는 허용된 조건에서 타 지점 PT 업무를 수행·이용할 수 있다. Session은 실제 Performed Branch를 식별하고 소속·발급 지점 변경으로 과거 수행 지점이 바뀌지 않아야 한다. Product는 Organization 공통 Catalog이며 지점별 가격 정책은 추가하지 않는다. Branch Admin은 하나의 Branch를 관리하고 일부 여러 지점만 담당하는 중간 관리자 역할은 추가하지 않는다. Master Admin이 Branch 구조를 관리한다. Branch Admin의 자기 지점 지점명·대표 연락처 수정은 BR-OPS-030으로 확정됐으며 나머지 필드/계정 Scope·지점 수명/절차는 MB-004/008 후속이다.

승인 근거: PD-004/006. [Product Decisions](product-decisions.md)

후속 TODO: MB-001–008, ARCH-001; 구체 데이터 모델은 Architecture 단계. [Open Questions](open-questions.md)

AS-IS reference: F54, F56. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

2026-10-12 일괄 승인 수용 기준: B6: Master의 기존 데이터가 있는 Branch 비활성화 허용·해당 지점 신규 배정/발급/실제 수업 차단·기존 소속/Pass/잔여/이력 보존/자동 이동·소멸 없음(BR-OPS-016). 비활성 지점 과거 업무·조회/관리/로그인·재활성화 상세는 MB-008 후속이다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch).

2026-10-12 G 일괄 승인 반영: G1–G5: 비활성 지점의 기존 권한 내 조회/과거 수업 처리와 타 활성 지점 이용·명시적 소속 이동을 지원한다. 신규 배정/발급/새 실제 수업 차단·원본 보존은 유지한다. 지점 재활성화의 세부 절차·역사 사실 확인/정정·미결정 신규 배정/다른 상태 조합은 MB-008 후속이며 G 승인이 구체 저장/계약/잠금 승인이나 구현 완료를 뜻하지 않는다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). 구체 계약/저장/UoW·동시성 검증은 후속이다.

R2 수정 수용 기준: Master의 기존 Organization 범위와 Branch Admin의 각 처리 시점 자기 단일 관리 Branch에서 지점명/대표 연락처 수정을 허용한다. 직접 ID/요청 Scope·과거 관리 사실로 타 Branch/Organization을 변경할 수 없으며 허용 두 필드와 중요 변경 감사를 Backend에서 검증한다. 지점 생성/운영 상태/관리자 배정·계정 Scope/식별자 변경은 포함하지 않고 Home/Issued/Performed 사실·잔여/지급/정산은 보존한다. 다른 필드/입력·과거 표시/최소 계약은 후속이다(BR-OPS-030; [R 승인](product-decisions.md#review-20261013-r-batch); V-117 미구성·미실행).

<a id="pr-021"></a>
## PR-021. 관리자 발급 운영 계정·권한 관리

2026-10-26 수용 조건 추가: [I1 세 선택](product-decisions.md#review-20261026-i1)에 따라 실제 활성 Trainer의
신규 계정 발급·미설정 초기 링크 재발급·최초 설정만 허용한다. Trainer와 계정은 일대일 연결하며
중복/덮어쓰기/자동 동일인 연결을 금지한다. PENDING_SETUP 재발급은 현재 Master 조직/실제 Home Branch
관리 범위에서만 허용하고, 활성 Trainer의 Home 비활성만으로 발급·재발급·유효 링크 설정을 막지 않는다.
BR-OPS-012의 최신 경계를 따르며 기존 계정 역할 연결과 나머지 수명/운영은 별도다.

처리 상태: REDESIGN

v1 범위: IN-V1

출처: AS-IS-DERIVED + APPROVED-TO-BE

제품 요구: Master Admin이 Branch Admin 및 계정/권한을 관리한다. 관리자 발급 방식을 유지하며 Trainer 로그인 계정과 사용자·Branch 관계도 다룬다. Branch Admin은 자기 단일 관리 Branch의 새 Operator 계정을 발급하고 최초 업무 Branch를 지정할 수 있다(2026-10-12, BR-OPS-011). 기존 Operator 업무 Branch 변경은 Master Organization 범위 전용이며 Branch Admin은 불가하다(2026-10-12, BR-OPS-011). 신규 Trainer 로그인 계정 발급은 Master Organization 전체/Branch Admin 대상 Trainer의 현재 Home Branch 관리 범위에서 승인됐다(2026-10-12, BR-OPS-012). E5로 기존 계정 Operator·Trainer 역할 추가/회수의 Branch Admin 관리 범위는 승인됐다(BR-OPS-019). 다른 역할/Scope·계정 수명 위임과 구체 상태/연결/재부여·계약은 후속이다.

수용 기준 / 범위 경계: 기존 계정·암호를 이관하지 않는다. Role/Data Scope를 분리하고 계정/권한 변경을 감사한다. 계정 발급 권한과 PR-007 보상 설정 권한은 별개다. 계정 수명과 기술 모델은 ARCH-001/002다.

승인 근거: PD-001/019/022. [Product Decisions](product-decisions.md)

후속 TODO: ARCH-001/002, MB-004. [Open Questions](open-questions.md)

AS-IS reference: F57, F58, F59. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

추가 수용 기준(2026-10-12, BR-OPS-011): 새 Operator 계정 발급/최초 단일 Branch 지정은 Master Organization 전체 또는 Branch Admin 자기 단일 관리 Branch에서 허용한다. 타 Branch/Organization·위조 role/Scope 요청을 Backend에서 거부하며 다른 역할 생성/기존 계정 역할·지점 변경 권한을 자동 부여하지 않는다. 허용 발급 관리자가 일회용 최초 비밀번호 설정 링크를 전달하고 대상자가 직접 설정하는 기존 방식을 재사용한다. 계정/역할/최초 Scope·필수 감사의 일관성을 검증할 후속 계약을 설계하며 계정 수명/저장/인증 방식은 기존 게이트다. IAM-001 S1의 관리자 발급 API를 이번 승인만으로 Operator 발급 API로 확장하지 않는다.

Operator 지점 변경 수용 기준(2026-10-12, BR-OPS-011): 현재 Master Admin만 같은 Organization의 기존 Operator 업무 Branch를 변경한다. 출발/도착 Branch Admin·최초 발급자·Operator/Trainer 단독·위조 role/직접 ID 요청은 거부한다. 일반 저장 후 반영/실패 보존·감사 원칙을 적용하며 후속 Operator 요청에 새 단일 Branch Scope를 사용한다. 기존 다른 역할/Trainer Home Branch·업무 이력은 보존한다. 대상 상태·구체 계약/저장/UoW·처리 중 요청/동시성은 후속이다.

Trainer 신규 발급 수용 기준(2026-10-12, BR-OPS-012): Master는 자기 Organization 전체, Branch Admin은 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 발급할 수 있다. Backend 현재 Caller/Organization·실제 Trainer/현재 소속을 확인하고 타 지점/타 Organization·위조 role/ID·철회된 권한 요청을 거부한다. 기존 일회용 최초 비밀번호 설정 링크·계정/권한 감사·필수 생성/연결의 실패 일관성 원칙을 적용한다. 기존 계정 역할 추가/재연결·Trainer Home Branch 변경/수명 위임은 별도이며 저장/계약·동시성은 후속이다.

2026-10-12 일괄 승인 수용 기준: A4/A7/A8/A9: 최초 설정 링크 30분 단일 사용·재발급 시 이전 링크 폐기. 관리자 역할/관리 Branch 변경 시 기존 로그인 전부 종료/재로그인. 계정 전체 차단/복구·관리자 reset Master 전용. 복수 Master 허용/마지막 사용 가능 Master 차단·권한 제거 금지. 설정 링크·관리자 reset·본인 비밀번호 변경·Trainer 업무 상태 변경을 구분한다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch).

2026-10-12 C 일괄 승인 수용 기준: C1/C3–C7: 추가 관리 비밀번호 재확인은 요구하지 않는다. 본인 변경은 현재 암호 확인/전 로그인 종료, Master reset 확정은 기존 암호/전 로그인 즉시 무효/마지막 Master 일반 reset 차단, Master ID 변경은 계정·역할/연결·이력 보존/전 로그인 종료. 인증/계정 관리 감사 열람은 Master 자기 Organization만이며 기존 신규 계정 발급 Scope는 유지한다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 E 일괄 승인 수용 기준: E1/E2: 최초 Master는 제한된 최초1회 설치 명령/본인 암호 설정, 이후 허용된 관리자가 수신자 본인 확인 후 대면/확인된 1:1로 설정·reset 링크 전달. E3/E4 ID 비교/이전 ID 예약, E5 Master Organization/Branch Admin 자기 관리 범위의 기존 Operator·Trainer 역할 추가/회수, E6 Master 일반 차단 해제 시 유효 기존 암호 재로그인을 적용한다. 대상 역할 Scope·독립 역할/연결·이력 보존/감사/실패 일관성과 기존 Master 전용 업무를 유지한다. S1 구현 범위를 자동 확대하지 않는다. [2026-10-12 E 일괄 승인](product-decisions.md#review-20261012-e-batch)

X1 수용 기준: 첫 IAM S1에서 Branch Admin 발급 응답을 잃어 ID/설정 링크를 못 받으면, 현재 Master가 자기 Organization의 Branch Admin을 정확한 Login ID로 조회해 ID/현재 상태·관리 Scope/version을 확인하고 설정 대기 상태에서 기존 최초 설정 링크를 재발급한다. 대소문자 미구별/30분 단일 사용·이전 링크 폐기/현재 인가·최신 상태/version 재검사·감사를 유지한다. 조회 자체는 대상 상태/Scope/설정 token을 변경하지 않고 다른 조직/비Master·일반 목록/부분 검색·원래 token 조회/중복 생성·숨은 자동 재시도·ACTIVE/DISABLED 강제 reset은 제공하지 않는다. X1 범위의 ID 미확보만으로 S1 중단하던 초안을 대체하며 Master 분실/복구·계정 수명 후속 분리는 유지한다. 기능 보완 승인과 구체 API/저장/계약/UoW/잠금 PROPOSED·별도 구현 지시를 구별한다([X 승인](product-decisions.md#review-20261013-x-batch); ARCH-001/002, V-126 미구성·미실행).

AB3–AB5 후속 수용 기준: reset 링크30분, 운영 관리자 비밀번호 뒤 사용자 검증 Passkey, 모든 Master 로그인 불가 시 조직 업무책임자 승인/별도 시스템 운영담당자 실행을 적용한다. 기존 Master 전용 일반 reset·확정 즉시 옛 암호/인증 무효·마지막 Master 보호/정상관리 추가승인 없음·Bootstrap 우회 금지와 K3/X1 첫 IAM 범위를 유지한다. 구체 등록/분실·본인확인/복구/감사·실패와 실제 운영 검증은 후속([AB 승인](product-decisions.md#review-20261013-ab-batch); V-134–136 미구성·미실행).

<a id="pr-022"></a>
## PR-022. 숨김 월 복사·상품 직접 선택

처리 상태: DROP-CANDIDATE

v1 범위: NOT-COMMITTED

출처: AS-IS-DERIVED

제품 요구: 숨김 기능은 필요 확인 전 구현하지 않는다.

수용 기준 / 범위 경계: 월 집계 원본 복사는 날짜별 Session 원칙과 호환 요구가 아니다. 여러 날짜 일괄 입력 UX-001과 혼동하지 않는다.

승인 근거: PD-008/023. [Product Decisions](product-decisions.md)

후속 TODO: UX-001과 별개; 후속 필요 확인. [Open Questions](open-questions.md)

AS-IS reference: H01, H02. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-023"></a>
## PR-023. 기존 Excel 가져오기·migration tooling

처리 상태: DROP-CANDIDATE

v1 범위: OUT-V1

출처: AS-IS-DERIVED

제품 요구: 기존 데이터 이관 및 migration용 import는 v1에서 제거한다. 미연결 도구는 후보로만 남긴다.

수용 기준 / 범위 경계: 운영 데이터를 복사·변환·적재하거나 기존 자료 조회를 제공하지 않는다. CSV/Excel 운영 편의는 실제 필요 확인 전 필수 아님.

승인 근거: PD-017/020/023. [Product Decisions](product-decisions.md)

후속 TODO: 현재 이관 TODO 없음. [Open Questions](open-questions.md)

AS-IS reference: H03. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-024"></a>
## PR-024. 미연결 생일 목록

처리 상태: DROP-CANDIDATE

v1 범위: OUT-V1

출처: AS-IS-DERIVED

제품 요구: 생년월일 수집과 이를 전제로 한 생일 목록은 I2에 따라 v1에서 제외한다. 향후 필요 시 수집 목적/공개 범위부터 별도 검토한다.

수용 기준 / 범위 경계: 회원 생일 저장이나 발송 기능을 이 기능의 존재로 필수화하지 않는다.

승인 근거: PD-022/023 및 생년월일/성별 v1 제외 I2. [2026-10-12 I 일괄 승인](product-decisions.md#review-20261012-i-batch).

후속 TODO: 후속 필요 확인. [Open Questions](open-questions.md)

AS-IS reference: H04. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-025"></a>
## PR-025. 빈 기타설정·급여 팝업

처리 상태: DROP-CANDIDATE

v1 범위: NOT-COMMITTED

출처: AS-IS-DERIVED

제품 요구: 내용 없는 화면을 자동 구현하지 않는다.

수용 기준 / 범위 경계: 빈 팝업 자체를 급여 지급·송금 기능으로 확대하지 않는다. 사용자 승인 보상 설정(PR-007)·월 정산(PR-010)·추가실적(PR-031)은 별도 요구다.

승인 근거: PD-023. [Product Decisions](product-decisions.md)

후속 TODO: 후속 필요 확인. [Open Questions](open-questions.md)

AS-IS reference: S05/S15. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

<a id="pr-026"></a>
## PR-026. 접근 종료·재진입

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: 운영 계정의 접근 종료·재진입을 계정 정책의 일부로 다룬다.

수용 기준 / 범위 경계: 만료·재인증·비밀번호 분실·중단 후 접근 정책은 Authentication/Authorization에서 정의한다. 기존 프로그램 종료와 동일시하지 않는다.

승인 근거: PD-019. [Product Decisions](product-decisions.md)

후속 TODO: ARCH-002. [Open Questions](open-questions.md)

AS-IS reference: 직접 대응 기능 없음; 사용자 승인. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

계정 전체 차단과 Trainer 역할 중단을 구분한다(2026-10-12, BR-OPS-014). 겸임자의 Trainer 비활성화만으로 독립 관리자 업무/로그인을 함께 차단하지 않는다. 다른 활성 역할 없는 비활성 Trainer 로그인 불가(B2)·계정 전체 차단/복구의 Master 전용 Actor(A8)·마지막 사용 가능 Master 보호(A9)는 확정이다. 구체 계정/Caller 전이·복구/보호 구현은 ARCH-002 후속이다.

2026-10-12 일괄 승인 수용 기준: A5/A6/A7: 모든 역할 idle 30분/absolute 8시간, 독립 복수 로그인/일반 logout 현재 로그인만 종료, 관리 역할/관리 Branch 변경 시 기존 인증 모두 철회/재로그인. 처리 중 요청/자동 polling·활동 판정/설정 토큰의 상세는 후속이다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch).

2026-10-12 C 일괄 승인 수용 기준: C3/C4/C6: 본인 암호 변경 성공/관리자 reset 확정/Login ID 변경 시 현재 포함 모든 기존 AuthSession을 종료한다. 일반 logout 현재 로그인만 종료(A6)와 구별하며 새 암호 설정 완료 전 옛 암호로 로그인할 수 없다. 실제 만료와 현재 인가·CSRF는 유지한다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 E 일괄 승인 수용 기준: E6: 일반 계정 차단 해제 뒤 새 로그인만 허용하고 옛 AuthSession을 되살리지 않는다. reset으로 기존 암호가 무효하거나 설정 대기/기타 로그인 요건 불충족이면 기존 암호로 로그인할 수 없다. A5 만료·C3/C4/C6 철회/A10 운영 MFA와 현재 역할/Trainer 상태를 유지한다. [2026-10-12 E 일괄 승인](product-decisions.md#review-20261012-e-batch)

<a id="pr-027"></a>
## PR-027. 중요 운영 행위 감사

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: Session 생성·정정/취소, Pass 잔여 영향 행위, 세 보상 설정 변경, 추가실적 생성·정정·취소, 계정/권한 및 중요 Branch 관리 행위를 감사 가능하게 한다.

수용 기준 / 범위 경계: 모든 보상 설정 변경(최초 설정 포함)에 대상 Trainer, 변경 항목, 변경 전 값, 변경 후 값, 변경 Actor, Actor의 권한 및 Branch Context, 변경 시점을 추적한다. 별도 Master Admin 승인 없이 변경 가능하며 변경 요청→승인 대기→승인→반영 절차를 추가하지 않는다. 이 결정은 추가실적 승인이나 월 정산 마감/확정 절차를 면제하지 않는다. 감사 열람이나 다른 화면에서 비인가 사용자에게 설정을 노출하지 않는다. Trainer 직접 등록 Actor와 실제 수행 Branch도 식별한다. 감사 구조·조회 구현은 Architecture, 보존 기간은 LEGAL-001이다.

승인 근거: PD-022. [Product Decisions](product-decisions.md)

후속 TODO: ARCH-001, BR-007, LEGAL-001. [Open Questions](open-questions.md)

AS-IS reference: 직접 대응 기능 없음; 사용자 승인. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

2026-10-12 C 일괄 승인 수용 기준: C7/C8: 로그인/계정 관리 감사의 앱 열람은 자기 Organization Master만. 로그인 감사는 계정·시각·행위·성공/실패 최소 정보/원문 IP·브라우저 정보 제외다. 계정 관리의 필수 변경 전후/Actor·Scope 감사 및 다른 업무의 기존 민감정보 권한을 유지한다. 보존/삭제·미확인 계정 표현·조회 계약은 후속이다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 E 일괄 승인 수용 기준: E5 역할 추가/회수와 E3/E4 ID 변경/예약은 허용된 행위의 검증된 Actor·대상/전후 값/Scope·시각을 감사하며 이력과 실패 일관성을 유지한다. E1 설치 실행자 감사/보호 입력·E2 링크 노출 방지의 상세는 구현 검증 대상이다. 계정 관리 감사 읽기는 C7 Master 자기 Organization만이며 지점 관리자 역할 쓰기 권한이 감사 열람 권한을 추가하지 않는다. [2026-10-12 E 일괄 승인](product-decisions.md#review-20261012-e-batch)

2026-10-12 J1/J2 인가/감사 경계: 회원 등록·이름/전화번호 수정은 BR-OPS-021의 각 현재 Scope로, 회원 비활성화/재활성화는 BR-OPS-022의 관리자 현재 Member Home Branch Scope로 인가한다. 기존 중요 변경 감사·개인정보 제한을 적용하고 상태 변경에는 대상 Member·전후 상태·Actor/Role·Branch Context·시점 이력을 남긴다. 구체 개인정보 변경/열람·감사 저장·보존/삭제 계약은 후속이며 실제 개인정보를 일반 로그에 복사하지 않는다. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch).

R2 지점 기본정보 수정 감사: 대상 Branch·변경 항목/전후 값·Actor/Role/Branch Context·시점을 기존 중요 변경 감사로 추적한다. R1 Trainer 필수 전화번호 등록/변경도 기존 인가/감사를 유지하며 실제 연락처를 일반 로그/문서로 복사하지 않는다. 감사 저장/필드별 공개·보존/최소 응답은 후속이다(BR-OPS-029/030; [R 승인](product-decisions.md#review-20261013-r-batch); V-116/117 미구성·미실행).

S 업무 이력 조회 경계: 정산의 이전 확정본·해제/재확정 및 세 보상 설정 변경 이력은 BR-PAY-023의 Master Organization/현재 Trainer Home 관리 Scope로 조회한다. 원래 감사 사실/전후 값·정정 이유/변경자/시점을 보존한다. C7 로그인·계정 관리 감사 Master 전용과 구별하며 일반 Audit 전체 열람/추가 개인정보 공개·내보내기는 승인하지 않는다. 최소 응답/저장/보존·현재 권한 변경 경합은 후속이다([S 승인](product-decisions.md#review-20261013-s-batch); V-118/119 미구성·미실행).

<a id="pr-028"></a>
## PR-028. 빈 운영 데이터에서 신규 설정·일괄 전환

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: 초기 Master Admin과 Organization/Branch의 필요한 기준정보를 새로 설정하고 운영/Trainer 계정·Member·Trainer·Product·Pass를 새로 준비한다. 수용 기준 충족 후 기존 프로그램에서 일괄 전환한다.

수용 기준 / 범위 경계: 기존 데이터·계정·암호·설정의 복제/이관은 요구하지 않는다. 장기 병행 입력 구조가 없어야 한다. 짧은 준비/검증 및 실제 시작 책임은 별도 cutover 계획이다.

승인 근거: PD-004/017/018/019/020. [Product Decisions](product-decisions.md)

후속 TODO: ARCH-002, OPS-001. [Open Questions](open-questions.md)

AS-IS reference: F55. [기능 목록](../analysis/03-feature-inventory.md), [규칙](../analysis/07-business-rules.md). 코드 제약을 TO-BE 조건으로 사용하지 않는다.

2026-10-12 E 일괄 승인 수용 기준: E1 최초 Master는 설치 담당자의 제한된 설치 명령 최초1회 실행과 본인 암호 설정으로 준비한다. 고정 자격/일반 가입/초기 웹 설치·기존 계정/데이터 이관 요구를 추가하지 않는다. 설치 권한/입력/동시 실행·실패/감사/운영 인수는 후속 설계·검증이며 명령이 이미 구현됐다는 뜻이 아니다. [2026-10-12 E 일괄 승인](product-decisions.md#review-20261012-e-batch)

<a id="pr-029"></a>
## PR-029. Trainer Authentication / Allowed PT Scope

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: Trainer는 v1 직접 로그인 Actor다. 허용된 Member/PT 정보와 자신의 PT 업무를 조회하고 실제 수행 Session을 직접 등록·조회한다.

2026-10-12 사용자 확정: Trainer 회원 조회 대상은 본인이 담당 Trainer로 지정된 Pass의 회원과 개별 허용된 지원 수업 대상 회원만이다. 같은 Home Branch/Organization 전체 조회 권한을 부여하지 않는다. 목록·검색·직접 Member ID 상세 모두 Backend가 검증된 Trainer 연결/Organization Scope와 대상의 담당 또는 개별 지원 허용 사실을 확인한다. 대상 회원 조회가 모든 Pass/PT 내역/민감정보의 무제한 공개나 회원·Pass 변경/수업 등록·정정·취소 권한의 자동 부여를 뜻하지 않는다. 관리자 겸임자의 별도 관리 Scope와 Trainer 보상 설정 금지를 유지한다. 담당 관계를 인정할 Pass 상태/종료·변경/이력, 지원 지정/철회 주체·기간/절차·공개 필드/나머지 교차 PT 업무는 후속이다(BR-OPS-005, PR-002/030, MB-001/003/005).

2026-10-12 사용자 확정: 개별 지원 대상 지정은 Master Organization 전체/Branch Admin 지정 시점 현재 관리 Branch=대상 Member 현재 Home Branch에서 허용한다. 동일 Organization의 타 지점 Trainer도 지원 대상이 될 수 있지만 그 Trainer Home Branch/실제 수업 지점/Pass 발급 지점은 지정 권한 기준이 아니다. 관리자 권한 없는 Operator/Trainer는 지정할 수 없다. 해당 Trainer/Member 관계와 기존 감사만 반영하며 Home Branch 변경·보상 설정/정산·지점 전체 열람 권한을 만들지 않는다. 지원 지정 주체는 해결됐고 기간/철회 주체·이동 후 기존 허용·절차/공개 정보/실제 PT 업무 나머지 조건은 후속이다(BR-OPS-005, PR-002/030, MB-001/002/003/005, NFR-004).

2026-10-12 사용자 확정: 개별 지원 조회 허용은 관리자가 해제할 때까지 유지하며 고정 종료일/기간 경과 자동 종료·반복 연장은 두지 않는다. 해제 Actor/Scope는 기존 지정 권한과 같은 Master Organization/Branch Admin 처리 시점 Member 현재 Home Branch 기준을 적용한다(2026-10-11 사용자 일관성 지시 적용). Backend 현재 권한/대상 Organization 검증과 NFR-004 감사를 유지한다. 해제는 해당 지원 관계의 조회 근거만 종료하며 별도의 담당/관리 권한과 기존 PT·Pass·지급/정산은 그대로 판단한다. 소속 이동 후 기존 허용·대상 상태/담당 관계 인정·절차/공개 정보는 후속이다(BR-OPS-005).

2026-10-12 사용자 확정: Member Home Branch 변경만으로 기존 개별 지원 조회 허용을 해제하거나 재지정하지 않고 유지한다. 이동 후 지정/해제는 Master Organization 또는 각 처리 시점 Member 현재 Home Branch 관리 Branch Admin이 담당하며 이전 소속/과거 지정 Actor만으로 권한을 유지하지 않는다. 동일 Organization 내 Trainer Home Branch만 변경된 경우도 같은 유지 원칙을 적용한다(2026-10-11 사용자 일관성 지시). 현재 Caller/대상 관계 검증과 기존 감사 이력·별도 담당/관리 Scope를 유지한다. 과거 수업/Pass/지급/정산 변경이나 일반/지원 구분 고정은 없고 수업 당시 Trainer 소속 기준을 따른다. 이동 자체의 권한/시점/이력·다른 대상 상태·담당 관계/공개 필드/절차·계약/저장은 후속이다(BR-OPS-005, MB-001/002/003/005).

2026-10-12 사용자 수정 확정(잔여 0 회원 조회와 제외 필터): 본인이 담당한 이용권의 잔여가 모두 0이어도 그 사실만으로 담당 회원의 목록·검색·상세 조회를 차단하지 않는다. 기본 조회에는 잔여 0 회원도 포함하고 선택 기능인 “잔여 0인 회원 제외” 필터를 제공한다. 필터 미사용 시 포함/사용 시 해당 조건의 회원을 결과에서 제외하며 조회 권한이나 담당/지원 관계·회원 상태를 변경하지 않는다. Backend의 현재 Caller/Organization·담당 또는 개별 지원 관계 인가는 필터와 독립적으로 유지한다. 조회 허용이 Remaining > 0 등 기존 PT 등록/차감 조건을 면제하지 않는다. 여러 이용권의 잔여 집계 범위·개별 지원 회원 등 담당 이용권 없는 대상의 판정과 수동 만료/취소·담당 변경 등 다른 상태의 조회 영향/공개 필드는 후속이다(BR-OPS-005, PR-002/029/030, MB-001/003/005).

2026-10-12 사용자 확정(잔여 제외 필터의 집계 기준 질문의 1번): “잔여 0인 회원 제외”는 조회 권한이 확인된 Member의 전체 이용권 잔여를 기준으로 판단한다. 조회 Trainer가 담당한 Pass만으로 제한하지 않으며 동일 Organization 내 다른 Trainer 담당/다른 Issued Branch의 Pass도 해당 Member의 집계 범위에 포함한다. 내 담당 Pass 0회+다른 Trainer 담당 Pass 10회인 Member는 필터를 켜도 표시하고 전체 집계 잔여가 0이면 제외한다. 개별 지원 회원도 자기 담당 Pass 존재 여부와 관계없이 같은 Member 전체 기준을 적용한다. 필터 미사용의 기본 조회/개별 상세 권한은 그대로이며 다른 회원/개별 Pass·다른 Trainer PT/보상 정보를 자동 공개하지 않는다. 집계 범위는 확정됐고 나머지 종료 상태의 잔여 취급·담당 변경/비활성·공개 필드 및 계약/저장/조회 일관성은 후속이다(BR-OPS-005, PR-002/029/030, MB-001/003/005).

2026-10-12 사용자 확정(Trainer의 회원 전화번호 조회 질문의 1번): Trainer는 기존 조회 권한이 확인된 담당 회원과 개별 허용 지원 회원의 등록된 전체 전화번호를 조회할 수 있다. 부분 마스킹된 번호만 허용하는 정책으로 제한하지 않는다. 담당 Pass 잔여가 모두 0이어도 기존 회원 조회 권한이 유지되면 전화번호도 같은 범위에서 조회한다. Backend는 전화번호를 반환하는 조회마다 현재 Caller/Organization·담당 또는 지원 관계를 검증하고 미담당/미허용 회원·타 Organization 번호를 공개하지 않는다. 지원 해제 후 별도의 유효한 담당/관리 권한이 없으면 해당 번호도 공개하지 않는다. 관리자 겸임자의 별도 관리 Scope는 유지한다. 이번 승인은 전화번호 읽기이며 수정/일괄 내보내기·다른 개인정보/개별 Pass·다른 Trainer PT/보상 공개 권한을 추가하지 않는다. 전화번호 필수 수집/형식·중복/검증과 나머지 필드/보존·조회 계약은 후속이다(BR-OPS-005, PR-002/029/030, NFR-001/005, LEGAL-001).

수용 기준 / 범위 경계: Smartphone 현장 흐름은 주요 Use Case다. PR-008의 기록·차감을 따르며 타 지점 수업은 일반 PT 수당 대신 보상 전체를 Additional Performance로 처리한다(MB-009 CLOSED). 일반 Session Payment와 중복 합산하지 않는다. 타 지점 지원 수업은 보상 금액 없이도 허용된 PT 진행 기록과 Pass 차감을 먼저 완료한다. 권한 있는 관리자가 나중에 수업 건별 금액을 저장할 때 해당 Additional Performance 보상을 확정한다. 금액 미입력은 확정된 0원과 구분하고 누락 건을 추적할 수 있어야 한다. 미입력 지원 수업이 남으면 해당 Trainer·월 정산 확정을 차단한다. 정산 확정 권한·나머지 마감/정정 절차는 BR-009/013 OPEN이다. Trainer 역할만으로는 본인을 포함한 모든 Rate/Fixed Amount/Base Salary 조회·변경이 불가하다. 관리자 겸임자는 PR-007의 관리 권한 범위 안에서 본인 설정도 조회·변경할 수 있다. 타 지점 수업 가능은 그 지점 전체 데이터 접근 권한이 아니며 Trainer 역할만으로는 본인 PT 진행 기록도 정정/취소할 수 없다(2026-10-11 사용자 확정). Branch Admin의 기록 정정/취소는 실제 Performed Branch 기준으로 확정했다(2026-10-11). Operator 역할의 정정/취소도 불가로 확정했다(2026-10-11). Performed Branch 자체 정정 및 교차 업무의 나머지 조건은 MB-005의 잔여 OPEN이다.

승인 근거: PD-001/002/005/006; PR-001/008/015; NFR-001/008.

후속 TODO: MB-001/005, ARCH-001/002. [Open Questions](open-questions.md)

기존 사용자 일관성 지시 적용(2026-10-11; 2026-10-12 담당 교체 허용 반영): 같은 Pass에서 담당이 바뀌어도 잔여/과거 실제 수행 Trainer·확정 지급은 유지한다(BR-OPS-008). 담당 관계 인정 조건을 충족하는 Pass의 새 현재 담당으로 회원 조회를 인가하며 이전 담당자는 과거 담당 사실만으로 Member/전체 번호를 계속 조회하지 않는다. 다른 담당 Pass·개별 지원/관리 Scope는 각각 독립 판단하고 자신의 과거 PT 기록 조회는 기존 별도 업무 권한을 따른다. 교체를 수행할 Actor/관리 Scope·대상 Trainer/Pass 상태·늦은 수업 등록 및 구체 계약은 후속이다(BR-OPS-005/008, ARCH-001, MB-001/003/005).

2026-10-12 사용자 확정(교체할 Trainer의 소속 지점 질문의 1번): 기존 Pass의 담당 교체 대상은 같은 Organization의 Trainer이며 Member 현재 Home Branch와 다른 지점 소속 Trainer도 허용한다. 강남 회원의 담당을 수원 소속 Trainer로 바꿀 수 있다. Member와 같은 지점 소속이어야 한다는 제한을 두지 않으며 다른 Organization Trainer는 지정할 수 없다. 교체 요청의 Actor 권한은 기존대로 Master Organization 전체 또는 Branch Admin 처리 시점 Member 현재 Home Branch 기준이다(BR-OPS-008, PD-007, PR-003/029/030).

현재 담당으로 연결된 타 지점 Trainer의 회원 조회에도 BR-OPS-005의 현재 관계/Organization 검증과 허용 필드 범위를 동일 적용한다. 위 이전 교체 관련 후속 표기 중 Actor/Branch Scope·대상 Trainer 지점 조건 및 교체 전 본인 수업의 이전 담당 직접 등록 허용은 해결됐다. 담당 교체 후에도 해당 수업의 과거 담당/본인 수행·현재 Caller/Organization와 기존 Pass/정산 조건을 검증하여 등록할 수 있지만 회원 목록/상세·전화번호 조회는 복원하지 않는다(2026-10-12, BR-OPS-003/008). 잔여 소진 외 수동 만료/취소 등 나머지 Pass 상태·과거 담당/수행 사실 확인 불가/정정 및 최소 정보/계약은 계속 후속이다. 담당 지정은 Home Branch 변경이나 보상 설정 접근 권한을 만들지 않고 일반/지원 구분은 실제 수업 당시 Trainer Home Branch와 Performed Branch를 따른다.

2026-10-12 사용자 확정(잔여 0회인 이용권의 담당 교체 질문의 1번): Remaining이 0인 기존 Pass도 Assigned Trainer를 교체할 수 있다. 잔여를 모두 사용해 이용이 끝난 Pass도 포함한다. 같은 Pass에서 담당 A를 B로 바꾸며 Remaining 0·발급 조건/Issued Branch·과거 실제 수행 Trainer/PT 기록·확정 지급/정산 이력은 유지한다. 새 담당 B는 기존 현재 담당 관계에 따른 Member 조회·응대를 이어갈 수 있다. 기존 Master Organization 전체/Branch Admin 처리 시점 Member 현재 Home Branch 권한과 같은 Organization의 다른 지점 Trainer도 대상 허용 원칙은 유지한다(BR-OPS-005/008, PD-007, PR-003/029/030).

기존 현재 담당 회원의 기본 조회/허용 전화번호와 선택 잔여 0 제외 필터를 새 담당에도 동일 적용한다. 필터는 Member 전체 이용권 합계이며 다른 담당/Issued Branch의 잔여도 포함한다. 잔여 0 교체는 Pass 사용 재개나 이전 담당의 전체 수업/보상 공개가 아니며 이전 담당의 다른 현재 관계·과거 PT/한정된 누락 등록 인가는 각각 기존 규칙으로 판단한다. 수동 만료/취소 등 다른 종료 사유의 교체/담당 관계와 기술 계약은 후속이다(BR-OPS-003/005/008).

Trainer 로그인 계정 발급 Actor/Scope는 BR-OPS-012를 따른다(2026-10-12 사용자 확정): Master Organization 전체/Branch Admin 대상 Trainer 현재 Home Branch. 기존 일회용 최초 비밀번호 설정 링크 방식을 재사용하고 실제 Trainer 연결/현재 Caller를 검증한다. Trainer 단독의 계정 발급/본인 보상 설정 권한을 추가하지 않으며 허용 PT Scope는 기존 규칙 그대로다. 이 결정으로 실제 Trainer 로그인 구현/검증이나 S1 확장을 완료했다고 판단하지 않는다.

Trainer Home Branch 변경 Actor는 Master Organization 전용(BR-OPS-013)이며 계정 발급 Actor와 구별한다. 일반 저장 후 현재 소속 인가·실패 보존/감사 원칙을 적용하되 계정의 독립 관리자/Operator Scope·Trainer 연결은 자동 변경하지 않는다. 기존 담당/개별 지원 조회 관계와 과거 수업 당시 소속/일반·지원 구분을 유지한다. 본인 보상 설정 제한·PT 정정/취소 인가는 기존 규칙을 따른다. Trainer 비활성화/계정 중단 정책이나 소속 이력 정정 예외를 이번에 확정하지 않는다.

2026-10-12 일괄 승인 수용 기준: B1/B2/A5: 다른 활성 역할 없는 비활성 Trainer 로그인 불가/재활성화 후 이용, 독립 관리자 겸임 역할 유지. Trainer 재활성화 Scope는 Master Organization/Trainer 현재 Home Branch 관리자이며 전 역할 동일 로그인 수명이다. 과거 직접 읽기/기록 예외를 새로 추가하지 않는다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch).

2026-10-12 G 일괄 승인 반영: G1/G4: Trainer Home Branch의 비활성만으로 활성 Trainer의 로그인/기존 Allowed PT Scope를 없애지 않는다. 다른 활성 지점 수업에는 현재 계정/역할·Trainer 활성/담당 또는 개별 지원 관계·Pass 조건을 적용하고 보상 설정 접근을 확대하지 않는다. Trainer 자체 비활성 및 신규 배정 조건은 별개다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). 구체 계약/저장/UoW·동시성 검증은 후속이다.

2026-10-12 H 일괄 승인 반영: H4=1: Trainer 역할만으로 본인 월 정산 총액/구성의 API/화면 조회를 허용하지 않는다. 기존 본인 PT 진행 내역/Allowed PT Scope는 유지하며 관리자 겸임의 정산 읽기는 독립 현재 관리자 Scope로 판단한다. 직접 ID/집계 등으로 정산/보상 설정 읽기를 우회할 수 없다. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch). 실제 계약/구현·검증은 후속이다.

수동 만료 담당 조회 추가(M2=1): 수동 만료된 Pass만 담당한 현재 유효 Trainer도 해당 Member/기존 허용 전체 전화번호를 조회한다. 만료만으로 조회 관계를 종료하지 않으며 현재 Caller/Organization·담당 또는 개별 지원 인가를 목록/검색/직접 ID마다 검증한다. 담당 교체·Trainer 자체 비활성/계정 차단·역할/인증 철회의 기존 접근 제한과 실제 PT 사용 조건은 유지한다. 전화번호 외 새 공개/수정·내보내기 권한은 추가하지 않는다(BR-OPS-005; [M 승인](product-decisions.md#review-20261013-m-batch); V-107 미구성·미실행).

수업별 보상 금액 추가 제한(N1=1): 비관리자 Trainer에게 본인의 일반 Session Payment/수업 연결 지원 보상 금액을 공개하지 않되 기존 본인 PT 진행 내역은 조회한다. 서버 내부 계산/보존·정산 반영과 Trainer에게 금액을 전달하는 행위를 구별한다. 화면/등록 성공/상세·중첩 응답에 금액을 남기지 않고 가짜 0원으로 바꾸지 않는다. 월 정산 v1 제외/보상 설정 금지 및 관리자 겸임자의 독립 관리 Scope는 유지한다(BR-PAY-021; [N 승인](product-decisions.md#review-20261013-n-batch); V-108 미구성·미실행).

개별 지원의 등록 범위(O2=1): 회원 조회에 더해 본인 실제 수업 등록을 허용하며 본인 담당 Pass가 없어도 그 Member의 다른 담당분 포함 전체 적격 Pass에서 차감한다. 정상 요청의 검증된 현재 Caller/Trainer·담당 또는 지원 관계와 기존 실제 시점/현재 잔여·상태/정산 조건을 확인한다. 지원 관계 자체를 보상상 지원 수업으로 분류하지 않는다. 보상 설정/금액·월 정산·다른 Trainer 대행·정정/취소/발급의 권한 확대는 없다. 지원 지정 전/해제 후 과거 등록은 BR-OPS-027(P1/P2)의 확정 경계를 따른다(BR-OPS-005/026; [O 승인](product-decisions.md#review-20261013-o-batch); V-111 미구성·미실행).

P1/P2 직접 등록 경계: 현재 지원 허용으로 지정 전 실제 본인 수업도 등록할 수 있다. 해제 후에는 실제 허용 기간의 본인 수업을 늦게 등록할 수 있으나 회원 일반 조회/전화번호·다른 Pass/Trainer 정보 공개를 복원하지 않는다. 필요한 최소 과거 대상 식별/등록 명령은 별도 계약으로 구체화한다. 현재 Trainer 비활성·계정/역할 차단을 우회하지 않고 해제 후 새 수업/허용 기간 밖 수업을 P2로 등록하지 않는다(BR-OPS-027; [P 승인](product-decisions.md#review-20261013-p-batch); V-112/113 미구성·미실행).

U1 담당 조회 수용 기준: 만료 Pass의 새 담당도 M2의 현재 담당 관계를 근거로 허용된 Member/전화번호를 조회한다. 이전 담당은 다른 유효 관계/독립 권한 없이 일반 조회를 유지하지 않는다. 기존 이전 담당의 교체 전 실제 본인 수업 늦은 등록/일반 조회 비복원·현재 계정/Trainer/Organization 검증·보상 금액 비공개와 만료된 Pass 새 사용 차단은 유지한다. 담당 교체 자체는 Trainer 단독 업무가 아니다(BR-OPS-008/005; [U 승인](product-decisions.md#review-20261013-u-batch); V-122 미구성·미실행).

<a id="pr-030"></a>
## PR-030. Branch-scoped Authorization / 업무 Context

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: Role과 Data Scope를 분리한다. Master Admin은 Organization 전체, Branch Admin은 허용 Branch, Operator는 허용 Branch·업무, Trainer는 Allowed PT Scope에 접근한다. Member·Trainer·Pass·Session·운영 데이터·Settlement·통계/집계에 허용 범위를 적용한다.

수용 기준 / 범위 경계: Branch-scoped authorization MUST be enforced server-side. 허용되지 않은 다른 지점 데이터 ID를 직접 요청해도 접근할 수 없으며 UI 숨김만으로 충족하지 않는다. 특정 Member/Pass/Session의 허용된 교차 이용과 타 지점 전체 목록 조회를 구별한다. PR-007 보상 설정은 대상 Trainer Home Branch로 제한하며 Performed Branch로 권한을 확대하지 않는다. 교차 업무 조건 MB-001/002/003/005, 정산 열람의 남은 상세 MB-006, 귀속 MB-010은 업무 결정 게이트다.

정산 조회 Scope 추가(2026-10-11 사용자 확정): 현재 자기 Branch 소속 Trainer의 해당 월 정산 전체 금액·구성 내역은 타 지점 지원 수업 보상까지 공개한다(조회 시점 현재 Home Branch 기준, 2026-10-11 사용자 확정). Performed Branch 기준으로 금액을 누락하거나 다른 Home Branch Trainer의 전체 정산을 공개하지 않는다. 다른 지점 전체 원본 업무 자료의 열람 권한을 함께 부여하지 않는다.

지점별 비용 보고서 Scope 추가(2026-10-11 사용자 확정): 보고서의 개별 요청·목록·검색·집계에서 현재 Master Admin 권한과 Organization Scope를 Backend에서 확인한다. Master 권한 없는 Branch Admin은 자기 지점 비용 합계만 요청하더라도 거부하며 Operator·Trainer 및 Branch Admin·Trainer 겸임자도 동일하다. 직접 ID·위조 Branch Context·비용 귀속 사실·UI 숨김으로 우회할 수 없다. 기존 Branch Admin의 현재 소속 Trainer 해당 월 정산 전체 금액·구성 내역 조회는 별도 권한으로 유지한다.

2026-10-11 사용자 확정: 동일 Organization의 타 지점 Pass 사용은 별도 사전 승인 없이 허용하지만, Backend는 요청 Actor의 PT 업무 권한·Organization/대상 Member·Pass 관계와 사용 가능 조건을 별도로 검증한다. 타 지점 Pass 사용 허용만으로 다른 지점 전체 회원 목록/정보나 민감 보상 정보를 공개하지 않는다. Member/Pass 조회와 교차 업무 Actor 범위의 나머지 결정은 MB-001/002/003/005 후속이다.

2026-10-12 사용자 확정: 수동 만료는 검증된 Master의 Organization 전체 권한 또는 Branch Admin의 현재 관리 Branch=대상 Pass Issued Branch 조건으로 Backend에서 인가한다. Member/Trainer 소속·Performed Branch·클라이언트가 보낸 Branch/role이나 직접 Pass ID로 우회할 수 없다. 관리자 권한 없는 Operator/Trainer는 만료할 수 없다. 타 지점 이용 가능 사실은 만료/전체 목록 열람 권한을 자동 부여하지 않는다(BR-OPS-004).

2026-10-12 사용자 확정: 수동 만료 해제도 만료와 같은 Master Organization 전체/Branch Admin 처리 시점 현재 관리 Branch=Pass Issued Branch 범위에서 Backend가 인가한다. 이전 만료 처리자라는 사실·현재 Member/Trainer 소속·Performed Branch·직접 ID/위조 role/Branch Context는 권한 근거가 아니다. 관리자 권한 없는 Operator/Trainer는 해제할 수 없다. 사유 없는 해제 요청은 거부하고 기존 만료 상태·잔여·이력을 유지한다. 허용된 해제는 사유와 전후 상태/Actor/시점을 감사 가능하게 남긴다(BR-OPS-004).

2026-10-12 사용자 확정: Organization 공통 PT 상품 생성/수정은 Master Admin만 허용한다. Backend에서 현재 Master 권한/Organization Scope를 확인하고 Master 권한 없는 Branch Admin·Operator·Trainer의 직접 Product ID/위조 role·Branch Context 요청을 차단한다. 상품 조회/Pass 발급 등 별도 업무 접근을 자동 제한하거나 허용하는 결정은 아니다(PR-006, BR-PAY-001, MB-007 CLOSED).

2026-10-12 사용자 확정: Trainer 회원 조회는 본인 담당 Pass의 Member 또는 개별 허용된 지원 Member로 제한한다. Backend가 목록·검색·직접 ID 상세마다 검증된 Caller의 Trainer 연결/Organization Scope와 대상별 허용 사실을 확인하고 client role/Branch/Trainer/Member ID·지원 표시만으로 범위를 넓히지 않는다. 같은 지점의 미담당/미허용 회원도 거부한다. 관리자 겸임자의 별도 관리 Scope·민감 보상 제한은 유지하며 담당/지원 관계 인정·지정/철회/기간·공개 항목 상세는 후속이다(BR-OPS-005, PR-002/029).

2026-10-12 사용자 확정: 지원 조회 대상 지정 요청은 Backend가 현재 Master 권한/Organization Scope 또는 Branch Admin의 현재 관리 Branch=Member 현재 Home Branch를 검증한다. 대상 Trainer와 Member의 실제 Organization 관계도 확인하며 현재 Performed/Trainer Home/Pass Issued Branch나 과거 소속·위조 role/Branch Context·직접 ID만으로 우회할 수 없다. 비관리자 Operator/Trainer·범위 밖 요청 거부 시 기존 지원 허용 관계/회원 조회 범위·과거 기록을 바꾸지 않는다. 지정/중요 권한 변경은 NFR-004 감사 원칙을 따른다. 철회/유효기간·이동 후 기존 허용·저장/인가 일관성 상세는 후속이다(BR-OPS-005).

2026-10-12 사용자 확정: 개별 지원 조회 허용은 관리자가 해제할 때까지 유지하며 고정 종료일/기간 경과 자동 종료·반복 연장은 두지 않는다. 해제 Actor/Scope는 기존 지정 권한과 같은 Master Organization/Branch Admin 처리 시점 Member 현재 Home Branch 기준을 적용한다(2026-10-11 사용자 일관성 지시 적용). Backend 현재 권한/대상 Organization 검증과 NFR-004 감사를 유지한다. 해제는 해당 지원 관계의 조회 근거만 종료하며 별도의 담당/관리 권한과 기존 PT·Pass·지급/정산은 그대로 판단한다. 소속 이동 후 기존 허용·대상 상태/담당 관계 인정·절차/공개 정보는 후속이다(BR-OPS-005).

2026-10-12 사용자 확정: Member Home Branch 변경만으로 기존 개별 지원 조회 허용을 해제하거나 재지정하지 않고 유지한다. 이동 후 지정/해제는 Master Organization 또는 각 처리 시점 Member 현재 Home Branch 관리 Branch Admin이 담당하며 이전 소속/과거 지정 Actor만으로 권한을 유지하지 않는다. 동일 Organization 내 Trainer Home Branch만 변경된 경우도 같은 유지 원칙을 적용한다(2026-10-11 사용자 일관성 지시). 현재 Caller/대상 관계 검증과 기존 감사 이력·별도 담당/관리 Scope를 유지한다. 과거 수업/Pass/지급/정산 변경이나 일반/지원 구분 고정은 없고 수업 당시 Trainer 소속 기준을 따른다. 이동 자체의 권한/시점/이력·다른 대상 상태·담당 관계/공개 필드/절차·계약/저장은 후속이다(BR-OPS-005, MB-001/002/003/005).

2026-10-12 사용자 수정 확정(잔여 0 회원 조회와 제외 필터): 본인이 담당한 이용권의 잔여가 모두 0이어도 그 사실만으로 담당 회원의 목록·검색·상세 조회를 차단하지 않는다. 기본 조회에는 잔여 0 회원도 포함하고 선택 기능인 “잔여 0인 회원 제외” 필터를 제공한다. 필터 미사용 시 포함/사용 시 해당 조건의 회원을 결과에서 제외하며 조회 권한이나 담당/지원 관계·회원 상태를 변경하지 않는다. Backend의 현재 Caller/Organization·담당 또는 개별 지원 관계 인가는 필터와 독립적으로 유지한다. 조회 허용이 Remaining > 0 등 기존 PT 등록/차감 조건을 면제하지 않는다. 여러 이용권의 잔여 집계 범위·개별 지원 회원 등 담당 이용권 없는 대상의 판정과 수동 만료/취소·담당 변경 등 다른 상태의 조회 영향/공개 필드는 후속이다(BR-OPS-005, PR-002/029/030, MB-001/003/005).

2026-10-12 사용자 확정(잔여 제외 필터의 집계 기준 질문의 1번): “잔여 0인 회원 제외”는 조회 권한이 확인된 Member의 전체 이용권 잔여를 기준으로 판단한다. 조회 Trainer가 담당한 Pass만으로 제한하지 않으며 동일 Organization 내 다른 Trainer 담당/다른 Issued Branch의 Pass도 해당 Member의 집계 범위에 포함한다. 내 담당 Pass 0회+다른 Trainer 담당 Pass 10회인 Member는 필터를 켜도 표시하고 전체 집계 잔여가 0이면 제외한다. 개별 지원 회원도 자기 담당 Pass 존재 여부와 관계없이 같은 Member 전체 기준을 적용한다. 필터 미사용의 기본 조회/개별 상세 권한은 그대로이며 다른 회원/개별 Pass·다른 Trainer PT/보상 정보를 자동 공개하지 않는다. 집계 범위는 확정됐고 나머지 종료 상태의 잔여 취급·담당 변경/비활성·공개 필드 및 계약/저장/조회 일관성은 후속이다(BR-OPS-005, PR-002/029/030, MB-001/003/005).

2026-10-12 사용자 확정(Trainer의 회원 전화번호 조회 질문의 1번): Trainer는 기존 조회 권한이 확인된 담당 회원과 개별 허용 지원 회원의 등록된 전체 전화번호를 조회할 수 있다. 부분 마스킹된 번호만 허용하는 정책으로 제한하지 않는다. 담당 Pass 잔여가 모두 0이어도 기존 회원 조회 권한이 유지되면 전화번호도 같은 범위에서 조회한다. Backend는 전화번호를 반환하는 조회마다 현재 Caller/Organization·담당 또는 지원 관계를 검증하고 미담당/미허용 회원·타 Organization 번호를 공개하지 않는다. 지원 해제 후 별도의 유효한 담당/관리 권한이 없으면 해당 번호도 공개하지 않는다. 관리자 겸임자의 별도 관리 Scope는 유지한다. 이번 승인은 전화번호 읽기이며 수정/일괄 내보내기·다른 개인정보/개별 Pass·다른 Trainer PT/보상 공개 권한을 추가하지 않는다. 전화번호 필수 수집/형식·중복/검증과 나머지 필드/보존·조회 계약은 후속이다(BR-OPS-005, PR-002/029/030, NFR-001/005, LEGAL-001).

승인 근거: PD-001/004/006/012/022; NFR-001/004/005.

후속 TODO: MB-001–008, ARCH-001. [Open Questions](open-questions.md)

2026-10-12 사용자 확정(회원 소속 지점 변경 권한): Master Organization 전체 또는 변경 전 Member 현재 Home Branch 관리 Branch Admin이 같은 Organization의 다른 Branch로 이동시킬 수 있고 받는 지점의 별도 승인은 없다. 각 요청에서 현재 Caller/관리 Scope와 서버 Member Home Branch·대상 Branch 사실을 검증한다. 받는 지점 관리자·과거 소속/변경자·발급/수행 지점만을 근거로 이동할 수 없다. 반영 이후의 Home Branch 기반 관리 권한은 새 현재 소속을 따르며 기존 지원/담당 조회와 다른 업무별 독립 Scope는 각각 유지한다. 이동 적용 시점·정정/상태 조건·구체 계약은 후속이다(BR-OPS-007, PR-002, MB-002, NFR-001/004).

2026-10-12 사용자 확정(회원 소속 변경의 적용 시점): 저장 완료 즉시 새 Member Home Branch를 적용하고 v1의 미래 적용일 예약 변경은 지원하지 않는다. 성공한 저장 이후 시작된 후속 요청은 새 현재 소속으로 Home Branch 기반 관리/지원 지정·해제를 인가한다. 실패 시 기존 소속 유지, 이전 소속/변경자만으로 관리 권한 유지 불가, 기존 지원/담당 조회·다른 독립 Scope와 과거 업무 이력 보존은 그대로다. 진행 중 요청/동시 이동의 인가 일관성·과거 소속 이력 정정/대상 Branch 상태 및 기술 계약은 후속이다(BR-OPS-007, PR-002, MB-002).

2026-10-12 사용자 확정(회원 이동 대상 지점): 기존 이동 Actor/관리 Scope/즉시 적용에 더해 Backend에서 대상 Branch의 동일 Organization 및 활성 상태를 확인한다. Master/Branch Admin 모두 비활성 지점 이동 불가이며 UI 선택 제한만으로 충족하지 않는다. 거부 시 Member 기존 소속과 관계/Pass·이력을 유지한다. Branch 비활성화 자체의 영향·상태 변경/이동 경합은 후속이다(BR-OPS-007, PR-002, MB-002/008).

2026-10-12 담당 교체 허용의 권한 경계: 기존 Pass에서 담당을 교체할 수 있고 잔여/과거 이력은 보존하지만 교체 명령의 Actor/Branch Scope는 ARCH-001·MB-001/003/005의 후속 결정이다(BR-OPS-008). 발급 지점 또는 Member Home Branch 중 하나를 기본값으로 구현하지 않는다. 후속 회원 조회는 기존 현재 담당/개별 지원/관리 인가 원칙을 적용하고 조회 허용만으로 교체/보상 설정 변경 권한을 부여하지 않는다.

2026-10-12 사용자 확정(담당 교체 권한의 기준 지점 질문의 1번): 기존 Pass의 Assigned Trainer 교체는 Master Admin의 Organization 전체 범위 또는 처리 시점 Member의 현재 Home Branch를 관리하는 Branch Admin에게 허용한다. 수원 발급 Pass의 회원이 현재 강남 소속이면 강남 Branch Admin 또는 Master가 교체할 수 있으며, 수원 Branch Admin은 Issued Branch만을 근거로 교체할 수 없다. 회원 소속이 다시 변경되면 각 교체 요청은 변경된 현재 Home Branch 기준으로 인가한다. 이용권 수동 만료/해제의 Issued Branch 기준은 그대로 유지한다(BR-OPS-004/008, PD-007, PR-003/030).

Backend는 검증된 현재 Caller의 관리자 권한/Organization·관리 Branch Scope, 실제 Pass→Member 관계와 Member 현재 Home Branch를 확인한다. 직접 Pass/Member ID·클라이언트 role/Branch/Member 소속 값·과거 소속/담당 또는 이전 처리 Actor·Trainer Home Branch·수업 Performed Branch만으로 교체 권한을 인정하지 않는다. 관리자 권한 없는 Operator/Trainer는 수행할 수 없으며 관리자·Trainer 겸임자는 해당 관리자 Scope로 판단한다. 권한 거부/실패 시 기존 담당·잔여/발급 조건·업무 이력을 유지한다. 기존 범위 내 관리자 직접 처리 원칙을 동일 적용하여 별도 Master 승인 대기를 추가하지 않는다(2026-10-11 사용자 일관성 지시 적용). 교체 권한은 대상 Trainer의 Compensation Setting 조회/변경 권한이나 다른 지점 전체 Trainer/Member 정보 열람 권한을 부여하지 않는다. 기존 즉시 적용·전후 담당/Actor/Branch Context·시점 이력/감사·현재 관계 기반 조회와 과거 수업/보상 보존 원칙은 유지한다.

담당 교체의 대상 Trainer 지점 조건은 같은 Organization의 다른 지점도 허용으로 확정(2026-10-12)됐다. Backend는 대상 Trainer의 실제 Organization 관계를 검증하며 위조 Trainer/Organization ID로 범위를 넓힐 수 없다. 기존 Actor/Member 현재 Home Branch 인가·보상 설정 제한은 유지한다. 교체 전 본인 수업의 이전 담당 직접 누락 등록은 허용으로 확정(2026-10-12)됐으며 현재 Caller/본인 Trainer 연결·Organization와 당시 담당/수행 사실·기존 Pass/정산 조건을 검증한다. 과거 담당 사실만으로 현재 회원 목록/상세·전화번호 조회나 교체 후 새 수업 등록 권한을 부여하지 않는다. 잔여 소진 외 수동 만료/취소 등 나머지 Pass 상태·과거 담당/수행 사실 확인 불가/정정과 최소 식별/Trainer 선택 정보·공개 계약/경합은 계속 후속이다(BR-OPS-003/008, ARCH-001·MB-001/003/005·BR-008). 위 이전 후속 기록의 Actor/Branch Scope·대상 Trainer 지점 조건 및 해당 과거 수업 등록 허용만 해결됐다.

2026-10-12 잔여 0 Pass 담당 교체의 인가 반영: 잔여가 0이라는 이유만으로 기존 Master/Member 현재 Home Branch 관리 Branch Admin의 담당 교체를 거부하지 않는다(BR-OPS-008). 현재 Caller 관리 권한·실제 Pass/Member·Organization와 대상 Trainer 관계를 검증하며 새 담당의 Member 조회는 기존 현재 담당 범위로 인가한다. 잔여 0 유지/정상 차감 금지·이력/감사와 보상 설정/다른 업무의 공개 제한을 유지한다. 다른 종료 사유의 상태별 조건과 저장/조회/교체 경합은 후속이다.

2026-10-12 사용자 확정(이용권 횟수의 수동 조정 권한 질문의 1번): Pass 횟수의 수동 조정은 Master Admin의 Organization 전체 범위 또는 처리 시점 현재 관리 Branch가 해당 Pass의 Issued Branch인 Branch Admin에게 허용한다. 수원 발급/현재 강남 소속 Member의 이용권은 수원 Branch Admin 또는 Master가 조정하며, 강남 Branch Admin은 Member의 현재 소속만을 근거로 조정할 수 없다. 회원 소속이나 담당 Trainer가 바뀌어도 Issued Branch 기준은 유지한다. 이용권 수동 만료/해제와 같은 발급 지점 기준이며 담당 교체의 Member 현재 Home Branch 기준과 구별한다(BR-OPS-004/008/009, PD-007/010, PR-003/030).

현재 Caller 관리 권한·Organization/관리 Branch와 실제 Pass Issued Branch를 Backend에서 검증한다. Member 현재 Home Branch/Trainer 소속·담당/개별 지원·Performed Branch/과거 처리자·직접 ID/클라이언트 role/Branch로 대체하지 않는다. 비관리자 Operator/Trainer는 불가, 관리자 겸임은 관리자 Scope로 판단한다. 수동 조정 허용이 PT 정정/취소·민감 보상/다른 지점 전체 자료 접근을 허용하지 않으며 거부/실패 시 기존 업무 상태를 유지한다(BR-OPS-009, NFR-001/004).

2026-10-12 사용자 확정(다른 지점에서 새 이용권 구매·발급 질문의 1번): Member는 같은 Organization의 Home Branch 밖 지점에서도 새 PT Pass를 구매·발급받을 수 있다. 수원 소속 회원이 강남에서 발급받으면 Member Home Branch는 수원으로 유지하고 새 Pass의 Issued Branch는 강남으로 기록한다. Member Home Branch와 Issued Branch가 같아야 한다는 제한을 두지 않는다. 기존 Member 식별자/소속·보유 Pass와 과거 PT/지급·정산 이력은 유지하며 타 지점 발급을 위해 Member를 지점별로 복제하거나 소속을 자동 이동하지 않는다(BR-OPS-001/010, PD-004/007, PR-002/003/030).

Backend는 현재 Caller의 발급 권한/Organization·허용 Issued Branch Scope와 실제 Member/Product/Branch 관계를 확인한다. Member Home Branch와 Issued Branch 일치를 전제하지 않으며 클라이언트 role/Organization/Branch/Member ID만으로 권한을 인정하지 않는다. 발급을 위한 특정 Member 식별과 타 지점 전체 목록/전화번호·다른 업무 조회는 구별한다. 승인된 발급 Actor/Scope를 적용하되 미정 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·추가 공개 정보·Member 선택용 최소 식별 응답/계약은 게이트 해결 전 임의 확정하지 않으며 거부/실패 시 기존 Member/Pass/업무 이력을 유지한다(BR-OPS-010, ARCH-001·MB-002/003/004/005, NFR-001/005).

2026-10-12 사용자 확정(새 이용권 발급 Actor 질문의 1번): 새 PT Pass 발급은 Master Admin·Branch Admin·Operator에게 각자의 허용된 실제 Issued Branch 범위에서 허용한다. Master는 Organization 전체, Branch Admin은 자신의 단일 관리 Branch, Operator는 부여된 허용 발급 Branch Scope에서 처리한다. 같은 Organization의 Member는 Home Branch가 발급 지점과 달라도 대상이 될 수 있으며 기존 Member/Home Branch를 유지하고 새 Pass에 실제 Issued Branch를 기록한다(BR-OPS-010, PD-004/007, PR-003/030).

Backend는 각 발급 요청에서 검증된 현재 Caller의 발급 역할/Organization·허용 실제 Issued Branch와 Member/Product/Branch의 실제 Organization 관계를 확인한다. 범위 밖 발급 지점·다른 Organization·Trainer 단독 권한·직접 ID/위조 role/Branch 값으로는 발급할 수 없으며 역할/Scope가 철회·축소되면 후속 발급 요청에도 현재 권한을 적용한다. 거부/실패 시 기존 Member/Home Branch·Pass·업무 이력을 유지한다. 발급 권한과 발급 이후의 관리 권한은 별도이므로 과거 발급 Actor였다는 사실만으로 후속 관리자 권한을 얻지 않는다.

권한 경계: Trainer 역할만으로는 새 Pass를 발급할 수 없다. Trainer를 겸하는 계정에 Master·Branch Admin·Operator의 발급 권한이 있으면 해당 역할의 독립적인 발급 Scope로 판단하며 별도 계정을 요구하지 않는다. Operator의 새 발급 권한은 공통 상품 생성/수정, 기존 Pass 수동 횟수 조정·만료/해제·담당 교체, Member 소속 이동, PT 정정/취소·Compensation Setting·Additional Performance·월 정산의 별도 권한을 추가하지 않는다. 발급 대상 식별을 타 지점 전체 Member 목록/전화번호·다른 Pass/PT/민감 보상 정보의 일반 조회 허용으로 확대하지 않는다. 기존 보상 설정 접근 제한과 Trainer의 담당/개별 지원 회원 조회는 그대로다.

2026-10-12 사용자 확정(발급용 타 지점 회원 검색 질문의 2번): Branch Admin·Operator는 자신의 허용된 실제 Issued Branch에서 새 PT Pass를 발급하기 위해 같은 Organization 전체 지점의 Member를 이름·전화번호 일부로 검색할 수 있다. 전화번호 전체 일치만을 요구하지 않으며 Member Home Branch가 Caller의 관리/발급 Branch와 다르다는 이유만으로 검색 후보에서 제외하지 않는다. Master의 기존 Organization 전체 범위는 유지한다. 검색은 기존 Member를 선택하여 실제 발급 지점의 새 Pass를 만드는 흐름이며 Member 소속 이동/복제나 기존 Pass·PT·지급·정산 변경을 수행하지 않는다(BR-OPS-010, PD-004/007/022, PR-002/003/030).

검색 인가/정보 공개 경계: 이 허용은 이용권 발급용 Member 검색의 후보 범위·검색 방식과 이름/전체 전화번호/현재 Member Home Branch 공개다. Backend는 매 검색/선택/발급 요청에서 현재 Caller의 발급 역할/Organization·허용 실제 Issued Branch와 대상 Member의 실제 Organization을 검증한다. 검색 Branch Context를 위조하거나 과거 검색 결과/선택 Member ID로 철회된 역할·Scope 또는 다른 Organization을 우회할 수 없다. 같은 전화번호/이름의 여러 Member는 별도 식별자로 구분하여 선택하며 번호만으로 병합하거나 첫 결과를 자동 선택하지 않는다. 이 세 항목의 읽기 허용이 회원 정보/전화번호 수정·일반 Member 상세·전체 무조건 목록/일괄 내보내기, 다른 개인정보/Pass/PT/보상 정보 열람 권한을 추가하지 않는다. Trainer 단독의 담당/개별 지원 Member 검색 및 기존 전체 전화번호 공개는 유지하고 발급 역할 겸임은 그 독립 발급 업무 Scope로 판단한다. 응답은 승인된 공개 범위 안에서 구성하며 Member 선택용 최소 식별 응답/계약과 추가 공개 정보는 후속이다. 실제 운영 연락처/검색어를 문서·일반 로그에 복사하지 않는다.

회원 식별의 기존 원칙 적용: 같은 전화번호/이름으로 여러 Member가 일치하면 별도 Member 식별자로 구분하여 발급할 대상을 선택한다. 번호 일치/첫 결과만으로 자동 병합·동일 회원 취급·소속 이동 또는 다른 Member 이력/권한 공유를 하지 않는다(BR-OPS-006). 잔여 0만으로 회원을 제외하지 않는 기존 조회 원칙은 유지하며 발급용 검색을 Trainer 전용 선택 제외 필터/담당 회원 집합으로 제한하지 않는다. 비활성 Member/Branch 등 나머지 대상 조건·검색어/빈 검색 처리·추가 공개 정보·최소 선택 응답/계약·선택/발급 일관성은 후속이다. 검색 자체는 업무 데이터를 변경하지 않으며 검색 성공만으로 발급 완료나 발급 이후 관리자 권한을 얻지 않는다.

이번 결정으로 발급용 검색 후보의 Organization 전체 지점 범위·이름/전화번호 일부 검색과 결과의 이름/전체 전화번호/현재 Member Home Branch 공개는 해결됐다. 추가 공개 정보·Member 선택용 최소 식별 응답/계약 및 나머지 검색/대상 조건, 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·실제 발급 지점 선택, 발급 시 활성 담당 필수/상품 최초 횟수의 나머지 상태·계약/저장/UoW·실패/재시도/중복·권한/소속/상품/지점 상태 변경 경합은 후속이다. 승인된 세 항목의 공개/전화번호 비마스킹을 다시 미결정으로 두지 않는다. Product OPEN/ADR·모듈/계약 상태와 기존 보상 설정 접근 제한을 유지하며 실제 검색/발급 구현·검증 완료를 뜻하지 않는다.

2026-10-12 사용자 확정(발급용 검색 결과 표시 정보 질문의 1번): 새 PT Pass 발급용 Member 검색 결과에는 이름·전체 전화번호·소속 지점을 표시한다. 소속 지점은 해당 Member의 현재 Home Branch이며 Caller 관리 지점/Pass Issued Branch/수업 Performed Branch와 구별한다. 같은 Organization의 타 지점 회원 검색 결과에도 동일하게 적용하고 부분 마스킹된 번호만 표시하도록 제한하지 않는다. 기존 이름·전화번호 일부의 Organization 전체 지점 검색과 현재 발급 역할/실제 Issued Branch Scope 인가는 유지한다(BR-OPS-010, PD-004/007/022, PR-002/003/030, NFR-001/005).

수용 경계: 같은 Organization의 타 지점 일치 Member도 인가된 발급용 검색에서 이름·전체 전화번호·현재 Member Home Branch를 반환/표시한다. 발급 역할/실제 Issued Branch/Organization 인가가 없거나 철회·축소되면 후속 요청으로 해당 정보를 얻지 못한다. Trainer 역할만으로 전체 Organization 검색/번호 조회를 허용하지 않는다. 번호 중복/동명이인은 Member별로 구분/선택하며 검색 선택만으로 회원/소속·기존 Pass/PT/보상을 변경하지 않는다. 일반 상세·다른 개인정보/Pass/PT/보상 조회/수정·일괄 내보내기는 별도 권한을 따른다. 필드별 응답/선택용 최소 식별 계약·나머지 검색/대상 조건은 후속이다(BR-OPS-006/010, NFR-001/005).

2026-10-12 사용자 확정(Operator 업무 허용 지점 수 질문의 1번): v1 Operator 역할의 업무 허용 Branch는 한 시점에 하나만 지정한다. Operator는 그 지정된 단일 Branch에서 명시적으로 허용된 업무를 수행하며 같은 계정의 Operator 권한을 여러 Branch에 동시 부여하지 않는다. Branch당 Operator 한 명이라는 1:1 인원 제한을 추가하지 않으며 하나의 Branch에 여러 Operator가 있을 수 있다. 이 결정은 Operator 역할의 업무 Scope이며 기존에 허용된 겸임 역할의 독립적인 관리/PT 권한이나 Trainer Home Branch를 바꾸지 않는다(BR-OPS-011, PD-001/007, PR-001/003/030, ARCH-001, MB-004).

인가 경계: Backend는 검증된 현재 Caller의 Operator 역할/Organization·지정된 단일 업무 Branch와 해당 요청의 실제 업무 Branch를 확인한다. 직접 Branch ID·클라이언트 branch_id/role/선택 지점·과거 업무/발급 지점만으로 다른 Branch의 업무를 수행할 수 없다. 동일 계정에 Operator 권한을 중복 부여하거나 여러 Branch 중 하나를 임의 선택하는 방식으로 단일 지점 제한을 우회하지 않는다. 현재 역할/Scope 철회·축소 이후 후속 요청은 현재 권한을 적용한다. 지정이 없거나 복수 지정된 상태를 유효한 Operator 업무 권한으로 간주하지 않되 구체 계정/역할 저장·활성화 제약과 오류 계약은 후속 Architecture다.

기존 발급/검색 규칙 유지: Operator의 새 Pass 발급은 자신의 지정된 단일 Branch를 실제 Issued Branch로 사용한다. 그 발급 업무에서는 같은 Organization 전체 지점 Member를 이름·전화번호 일부로 검색하고 결과의 이름·전체 전화번호·현재 Member Home Branch를 조회/선택할 수 있다(BR-OPS-010). Member Home Branch가 Operator 업무 Branch와 다르다고 검색/발급을 거부하거나 회원 소속을 자동 이동하지 않는다. 전체 지점 Member 검색이 다른 Branch의 Pass 발급이나 일반 회원 상세/다른 Pass/PT·보상/수정·일괄 내보내기 권한을 부여하지 않는다. 기존 Master 전용 공통 상품 변경 및 관리자 전용 Pass 수동 조정·만료/해제·담당 교체/보상 업무 제한은 유지한다.

남은 결정: 새 Operator 발급/최초 Branch 지정 Actor는 Master Organization 전체/Branch Admin 자기 단일 Branch, 기존 Operator 업무 Branch 변경 Actor는 Master Organization 범위 전용으로 해결됐다. 변경은 기존 저장 후 현재 Scope 반영/실패 보존·감사 원칙을 적용한다. 발급 절차·기존 계정 역할 추가/변경·Operator 지점 변경의 대상 Branch/계정 상태·세부 절차/감사 계약 및 나머지 운영 행위 권한은 MB-004·ARCH-001/002 후속이다. 한 계정의 Operator 동시 허용 지점 수나 신규 발급/지점 변경 Actor를 다시 OPEN으로 두지 않는다. 실제 발급 대상·초기 조건/선택 응답·역할/Scope 저장·Caller/인가 계약·실패/재시도/경합은 관련 Product/Architecture 후속이다. IAM-001 S1에 Operator 구현을 추가하거나 기존 PROPOSED 인증/모듈/저장 설계를 승인한 것은 아니다.

2026-10-12 G 일괄 승인 반영: G1–G5: 지점 상태와 행위별 Data Scope를 구분한다. Branch Admin의 PT 정정/취소·관리자 대행은 실제 Performed Branch, 정산 해제/재확정은 각 처리 시점 Trainer 현재 Home Branch로 각각 검증한다. 비활성 출발 지점에서 활성 지점으로의 Member 이동은 Master/변경 전 현재 Member Home Branch 관리자, Trainer·Operator 이동은 Master만 허용한다. G1/G3/G4의 교차 업무 허용으로 타 지점 전체 자료·보상·감사 권한을 확대하지 않는다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). 구체 계약/저장/UoW·동시성 검증은 후속이다.

2026-10-12 H 일괄 승인 반영: H2/H3=1: 비지원 실적 내용 수정·취소는 Master Organization/각 처리 시점 대상 Trainer 현재 Home Branch의 Branch Admin 기준이다. 대상 Trainer/발생 날짜 오류는 취소 후 재등록이며 원래 대상 취소/새 대상 등록·각 영향받는 확정 Trainer/월 해제/재확정 권한을 따로 검증한다. 본인 건 포함/별도 승인 없음·사유/이력·타 지점 권한 확대 금지는 유지한다. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch). 실제 계약/구현·검증은 후속이다.

2026-10-12 J1–J3 인가 입력: 등록은 지정할 Member Home Branch, 이름/전화번호 수정 및 관리자 상태 변경은 처리 시점 실제 Member 현재 Home Branch로 판단한다. Operator의 지정 업무 Branch와 Branch Admin 관리 Branch를 검증하며 Trainer 단독 회원 수정·Operator/Trainer 단독 비활성화·재활성화는 거부한다. 발급/Performed Branch나 과거 담당·지원/처리자 관계를 Home 기준 권한으로 사용하지 않는다. 같은 Organization 타 지점 발급/검색 허용과 Member 자체 비활성 차단은 함께 적용한다. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch).

2026-10-12 K1/K2 인가 경계: 날짜/시각 오류의 원본 취소와 올바른 재등록은 각각 기존 PT 실제 Performed Branch 관리 Scope·현재 인가로 판단하며 지점 값 정정은 계속 Master 전용이다. Trainer 등록/이름·연락처 수정은 Master Organization/Branch Admin 지정·현재 Trainer Home 기준이며 Operator 회원 관리 권한을 사용하지 않는다. K3 첫 개발 범위는 관리자 인증/지점 접근 제어이고 이 후속 v1 권한/업무의 구현 완료를 뜻하지 않는다. [2026-10-12 K 일괄 승인](product-decisions.md#review-20261012-k-batch).

기록/금액의 별도 인가(N2=1): 자신의 Branch에서 수행한 PT 기록 조회/정정 권한은 현재 다른 Home Branch Trainer의 그 수업 보상 금액 조회 권한을 주지 않는다. 대상 Trainer 현재 Home·현재 Caller/행위별 Scope를 별도로 확인하고 목록/직접 ID·등록/중첩 응답·제공되는 집계/감사/오류 우회를 막는다. Master Organization 및 기존 현재 Home 기반 관리자 보상·정산 업무/겸임 독립 Scope는 유지하되 그 금액 업무를 다른 지점 PT 기록 전체 조회 권한으로 확대하지 않는다(BR-PAY-021; [N 승인](product-decisions.md#review-20261013-n-batch); V-109 미구성·미실행).

O1/O2 Scope 경계: Member에 대한 본인 PT 등록 인가 후 그 Member 전체 적격 Pass에서 선택하되 Pass Assigned Trainer/Issued Branch만으로 후보를 좁히거나 다른 Member/Organization에 접근하지 않는다. 지원 지정/해제 권한은 계속 각 처리 시점 Member 현재 Home의 Branch Admin 또는 Master Organization 범위다. Trainer Home/Performed/Issued만으로 부여하지 않으며 후보 선택이 다른 Trainer 정보/금액 공개 권한으로 전파되지 않는다(BR-OPS-026; [O 승인](product-decisions.md#review-20261013-o-batch); V-110/111 미구성·미실행).

## PT Pass와 PT Session의 제품 개념

PT Pass는 Member가 특정 PT Product를 이용하는 명시적 단위다. Assigned Trainer, Purchased Sessions, Remaining Sessions, Status, Created/Started information, 해당 PT Session history를 업무적으로 구분한다. 이는 개념 설명이며 Table·컬럼 정의가 아니다.

회원은 시간에 따라 여러 Pass 이력을 가진다. 종료된 Pass를 새 Pass로 덮어쓰지 않으며 과거 Session과 정산은 계속 조회 가능해야 한다. 복수 사용 가능 Pass의 FIXED_AMOUNT 우선 차감은 BR-PAY-006이며 사용 가능 조건·상한은 ARCH-003, 상태 전이·잔여 세부는 BR-001/002다. Purchased Sessions라는 개념이 고객 결제·계약 관리 기능을 승인하는 것은 아니다.

PT Session은 실제 시작 날짜·시각의 1회 수업 완료 기록이다. 예시의 9월 2일/5일/9일 진행은 각각 개별 기록이며 월 합계는 3회다. I1/I3에 따라 시각을 확인한 뒤 수업별 개별 등록하고 여러 날짜 일괄 입력은 v1 보류(UX-001 CLOSED)다. 실제 수행 Trainer의 일반 지급 및 타 지점 지원 수업 추가실적을 구별하며 서비스 Product는 FIXED_AMOUNT다. 정정/시간 정밀도·역사 사실/중복 요청 식별의 상세는 후속이다.

[확정 지급 규칙과 적용 범위 BR-PAY-001–016](business-rules.md)을 따른다. 아래 RATE/FIXED_AMOUNT 계산은 일반 Session Payment 적용 대상의 규칙이다. Product는 Pass 발급 시의 Payment Type·가격·총횟수 조건을, Trainer Compensation Setting은 Product에 독립적인 Rate·Fixed Amount·월 Base Salary를 갖는다. 기본급은 Session마다 붙지 않는다. RATE = Product Price ÷ Product Session Count × Trainer Rate의 결과를 1,000원 단위 올림; FIXED_AMOUNT = Trainer Fixed Amount. 서비스도 후자를 지급하며 Monthly Settlement의 Session 구성은 유효한 확정 Session Payment 집계이며 전체 구성은 PR-010을 따른다. 타 지점 보상 구성은 해당 수업의 보상 전체를 Additional Performance로 처리하는 방식으로 확정했다(MB-009 CLOSED, 2026-10-10).

## AS-IS 규칙의 계승 경계

R03/R06의 필수 개인정보·기본급, R04/R05의 회원 잔여 덮어쓰기, R09/R10의 계산식·우선순위, R14/R15의 일반 우선·서비스 단가, R18의 현재 상품 일치 복원 조건은 참고 규칙이다. 승인된 Pass/Session/지급 정책에 맞는 BR로 확인되기 전 TO-BE의 확정 규칙이 아니다. R02의 이력 보존 의도는 PD-011로 강화되었고, R35의 특정 계정 메뉴 조건은 PD-001의 직무 권한으로 대체된다.

계약·출석·고객 결제·환불·회원권·상담, 락커·가계부·수동 매출·고정 거래는 v1 제외를 유지한다. Member 로그인/Self-Service, Schedule/Reservation 및 Mobile App은 명시적 Future Scope다. Trainer 직접 로그인과 Multi-Branch는 v1에 포함한다. 기존 데이터 이관·이관 도구도 제공하지 않는다.

## Product Baseline — 2026-09-17 지점 관계·보상 개정

최신 사용자 확정사항을 반영한 Architecture Input Baseline이다. [현재 결정과 변경 이력](README.md), [권한](users-and-roles.md), [업무 규칙](business-rules.md), [남은 결정 게이트](open-questions.md), [Architecture 인계](architecture-handoff.md)를 함께 따른다. Baseline 갱신은 모든 상세 업무 정책 또는 구현 완료를 뜻하지 않는다.

<a id="pr-031"></a>
## PR-031. 추가실적(Additional Performance)

처리 상태: REDESIGN

v1 범위: IN-V1

출처: APPROVED-TO-BE

제품 요구: Trainer에게 인정하는 보상·인센티브를 지원한다. 타 지점 수업 보상 전체는 Additional Performance로 반영한다(MB-009 CLOSED). 타 지점 지원 수업, 회원 유지, 기타 인정 추가실적이 예다. 회원 유지는 기존 추가실적의 지급 사유이며 별도 보상 기능으로 구분하지 않는다. 관리자가 기존 권한 범위에서 내용·금액을 직접 입력하고 월 정산에 반영하는 흐름을 사용한다(2026-10-11 사용자 명확화). 특정 Session 관련 또는 Session 없이 발생할 수 있다. 고객 결제·매출·가계부나 기존 수동 매출과 동일시하지 않는다. 2026-10-10 금액 계산 질문의 3번 답변으로 타 지점 지원 수업 보상은 권한 있는 관리자가 수업 건별 금액을 직접 입력한다. 입력 금액 전부를 추가실적으로 반영하고 일반 RATE/FIXED_AMOUNT 계산 결과나 지원 전용 고정금액을 자동 지급액으로 사용하지 않는다. 타 지점 지원 수업은 보상 금액 없이도 허용된 PT 진행 기록과 Pass 차감을 먼저 완료한다. 권한 있는 관리자가 나중에 수업 건별 금액을 저장할 때 해당 Additional Performance 보상을 확정한다. 금액 미입력은 확정된 0원과 구분하고 누락 건을 추적할 수 있어야 한다. 지원 수업 외 추가실적의 금액도 관리자 건별 수동 입력으로 확정했다(2026-10-11). 지원 수업 외 실적은 내용과 금액을 함께 입력해야 최초 등록이 완료된다(2026-10-11). 금액 미입력 등록 완료/자동 0원 대체는 허용하지 않으며 지원 수업 외 등록은 양수 금액만 허용한다. 상한액·정밀도 등 나머지 입력 제약·정정/취소는 관련 OPEN이다.

수용 기준 / 범위 경계: 대상 Trainer, 인정 사유 또는 유형, 금액, 발생 시점과 정산 대상 기간, 관련 Branch Context, 필요한 경우 Member/Session, 등록자와 등록 시점, 정정/취소 이력을 식별한다. 생성·정정·취소는 감사 가능한 금액 변경 업무다. 2026-10-10 사용자 확정으로 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer의 추가실적만 직접 등록할 수 있다. 타 지점 수업도 Trainer 소속 지점 관리자 또는 Master가 등록하며 지원받은 지점 관리자는 수행 지점만을 근거로 등록할 수 없다. Backend에서 대상 Trainer의 Home Branch와 관리 Scope를 검증한다.

Branch Admin이 본인이 아닌 자기 지점 소속 Trainer에게 직접 등록할 때는 별도 Master 승인이 필요 없으며 Master 승인 대기 단계를 추가하지 않는다. 생성·변경 감사는 유지한다. 같은 날 본인 등록 질문의 2번 답변으로 관리자·Trainer 겸임자도 관리 범위 안이면 본인의 추가실적을 직접 등록할 수 있다. Master Admin은 Organization 범위 안의 본인, Branch Admin은 본인 Trainer Home Branch가 관리 Branch와 일치할 때 허용하고 불일치하면 거부한다. 별도의 관리 권한·Scope 검증을 거치며 본인 건도 동일하게 감사한다.

관리 범위 안에서 직접 등록한 본인의 추가실적도 별도 승인이 필요 없다(2026-10-10 본인 건 승인 질문의 1번 답변). Master나 다른 관리자의 승인 대기를 추가하지 않으며 관리 Scope·대상 Home Branch 검증과 동일한 생성·변경 감사를 유지한다.

지원 수업 외 실적의 금액 외 정보 수정/취소의 소속 이동 시 권한 기준 시점은 BR-013 OPEN이며 등록 권한을 이번에 별도 승인한 월 정산 확정 전 지원 수업 금액 수정 외의 승인·정정·취소·타 지점 전체 자료 열람 권한으로 확대하지 않는다. 본인 등록 허용은 보상 설정에서 자동 상속하지 않은 별도 사용자 결정이다. 본인 건의 승인 생략을 월 정산 확정에 확대하지 않는다. 타 지점 지원 수업의 금액 미입력 건의 추적 표현·정정 연동, 진행 기록 연계 상세, 지원 수업 외 추가실적의 최초 등록 금액 필수는 확정이며 나머지 입력 제약과 월 정산 마감/확정은 별도 정책이다. 지원 수업의 다른 입력 금액 범위·정밀도와 지원 수업 외 추가실적의 상한액·정밀도 등은 BR-010 OPEN이다(등록은 양수만 허용, 2026-10-11 사용자 확정). 비용 귀속과 정산 공개는 MB-010/006에서 별도로 결정한다. 정확한 입력 항목·구현 구조는 후속 설계다.

2026-10-10 사용자 확정(타 지점 지원 수업 보상 0원 허용 질문의 2번 답변): 타 지점 지원 수업 보상은 권한 있는 관리자가 사유를 기록하면 0원으로 명시적으로 확정할 수 있다. 사유 없는 0원 입력은 보상 확정이 불가하다. 사유를 남기고 확정한 0원은 금액 미입력이 아니므로 그 건으로 월 정산 확정을 차단하지 않는다. 다른 미입력 건이 남으면 기존 차단 조건을 유지한다. 기존 관리자 역할·Home Branch Scope·관리 범위 안 본인 등록·별도 승인 없음·감사 정책을 따른다. 미입력을 자동 0원으로 바꾸지 않으며 0원 확정으로 진행 기록을 취소하거나 Pass 차감을 복원하지 않는다. 월 정산 자동 확정이나 나머지 확정 조건의 충족을 뜻하지 않는다. 일반 Session Payment/서비스 PT 계산이나 다른 추가실적의 0원 허용으로 확대하지 않는다.

2026-10-10 사용자 확정(월 정산 확정 전 지원 수업 보상 금액 수정 권한 질문의 1번 답변): 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin에게 Organization 전체, Branch Admin에게 대상 Trainer Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안의 본인 건도 허용하고 변경 이력을 남긴다. 당시 결정은 수정 역할·대상 범위·본인 건 허용·변경 이력에 한정했다. 별도 승인 없음과 저장 즉시 반영은 아래 후속 사용자 결정으로 확정했다. 수정 금액을 0원으로 확정할 때는 기존 사유 필수 정책을 유지한다. 금액 수정만으로 PT 진행 사실·Pass 차감을 취소/복원하거나 일반 Session Payment를 현재 설정으로 재계산하지 않는다. 다른 추가실적 수정 권한과 지원 수업 보상 정정 외 소속 이동 시 권한 기준 시점은 미정이다. 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin·Branch Admin 모두 관리 범위 안에서 본인 건을 포함해 별도 승인 없이 저장 성공 즉시 반영한다. Master나 다른 관리자의 승인 대기를 두지 않으며 권한 검증과 변경 이력을 유지한다. 월 정산 확정 전 지원 수업 보상 금액의 모든 수정에는 변경 사유가 필수다. 양수 간 변경·0원에서 양수로 변경·양수에서 0원으로 변경 모두 적용하며, 사유 없이는 금액을 수정할 수 없다. 변경 전후 금액·변경 사유·수정자·수정 시점을 이력으로 남긴다. 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer의 지원 수업 보상 정정을 위해 월 정산을 확정 해제·재확정할 때는 Master의 별도 승인을 두지 않는다. Master 승인 대기 단계 없이 관리 범위 안에서 직접 처리하며 이전 확정본과 해제·재확정 이력 및 감사를 유지한다. 지원 수업 보상 정정의 월 정산 확정 해제에는 사유가 필수이며, 사유 없이 해제할 수 없다. 사유·해제자·시점을 이력으로 남긴다. 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 남은 정정·취소 절차는 BR-009/013 등 관련 OPEN을 따른다.

2026-10-10 사용자 확정(월 정산 확정 전 지원 수업 보상 수정의 별도 승인·저장 즉시 반영 질문의 1번 답변): 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin·Branch Admin 모두 관리 범위 안에서 본인 건을 포함해 별도 승인 없이 저장 성공 즉시 반영한다. Master나 다른 관리자의 승인 대기를 두지 않으며 권한 검증과 변경 이력을 유지한다. Master의 Organization 전체·Branch Admin의 대상 Trainer Home Branch 기준 범위는 유지한다. 수정 금액을 0원으로 확정할 때는 기존 사유 필수 정책을 적용한다. 금액 수정만으로 진행 기록·Pass 차감을 취소/복원하거나 월 정산을 자동 확정하지 않는다. 다른 추가실적 수정과 확정된 월 정산의 정정 정책으로 확대하지 않는다. 월 정산 확정 전 지원 수업 보상 금액의 모든 수정에는 변경 사유가 필수다. 양수 간 변경·0원에서 양수로 변경·양수에서 0원으로 변경 모두 적용하며, 사유 없이는 금액을 수정할 수 없다. 변경 전후 금액·변경 사유·수정자·수정 시점을 이력으로 남긴다. 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer의 지원 수업 보상 정정을 위해 월 정산을 확정 해제·재확정할 때는 Master의 별도 승인을 두지 않는다. Master 승인 대기 단계 없이 관리 범위 안에서 직접 처리하며 이전 확정본과 해제·재확정 이력 및 감사를 유지한다. 지원 수업 보상 정정의 월 정산 확정 해제에는 사유가 필수이며, 사유 없이 해제할 수 없다. 사유·해제자·시점을 이력으로 남긴다. 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 남은 정정·취소 절차는 BR-009/013 등 관련 OPEN을 따른다.

2026-10-10 사용자 확정(월 정산 확정 전 지원 수업 보상 금액 수정의 변경 사유 질문의 1번 답변): 월 정산 확정 전 지원 수업 보상 금액의 모든 수정에는 변경 사유가 필수다. 양수 간 변경·0원에서 양수로 변경·양수에서 0원으로 변경 모두 적용하며, 사유 없이는 금액을 수정할 수 없다. 변경 전후 금액·변경 사유·수정자·수정 시점을 이력으로 남긴다. 기존 관리자 역할·Home Branch 범위·관리 범위 안 본인 건 허용·별도 승인 없음·저장 성공 즉시 반영은 유지한다. 일반 Session Payment, 다른 종류의 추가실적 및 월 정산 확정 이후 정정 정책으로 확대하지 않는다. 구체 사유 입력·저장 형식은 후속 설계한다.

2026-10-10 사용자 확정(월 정산 확정 후 지원 수업 보상 오류 처리 질문의 2번 답변): 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 이전 확정본의 적용 기본급·구성 금액·합계를 덮어쓰거나 삭제하지 않으며 이전본과 재확정본을 구분한다. 예를 들어 9월 지원 수업 보상 30,000원의 오류를 35,000원으로 정정할 때 9월 정산의 확정 해제 → 지원 수업 보상 금액 정정 → 9월 정산 재확정으로 처리하고 이전 30,000원 반영 확정본을 보존한다. 금액 정정 시 PT 진행 사실·Pass 차감을 재실행하거나 현재 Rate/Fixed Amount/Base Salary를 이유로 과거 확정 일반 지급·기본급을 자동 재계산하지 않는다. 재확정에도 해당 Trainer·월의 미입력 지원 수업 차단 등 승인된 확정 조건을 적용한다. 이번 결정은 지원 수업 보상 금액 오류의 정정 경로와 이전 확정본 보존에 한정한다. 당시 미결정이었던 지원 수업 정정의 해제·재확정 권한은 아래 후속 사용자 결정으로 확정했다. 다른 정정/취소 및 실제 지급과의 대사·차액 처리 상세는 미정이다.

2026-10-10 사용자 확정(지원 수업 보상 정정의 월 정산 확정 해제·재확정 권한 질문의 2번 답변): 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. 수업의 Performed Branch만으로 다른 Home Branch Trainer의 정산 확정 해제·재확정 권한을 얻지 않는다. 관리자 권한이 없는 Operator·Trainer는 이 작업을 수행할 수 없다. 해당 Trainer·월의 확정 해제 → 금액 정정 → 동일 월 재확정과 이전 확정본 보존은 유지한다. 이 결정은 지원 수업 보상 금액 오류 정정에 한정하며 최초 월 정산 확정 권한이나 전체 정산 공개 범위(MB-006)를 새로 확정하지 않는다. 위 지원 수업 보상 정정의 현재 Home Branch 권한 기준은 아래 후속 사용자 결정으로 확정했다.

2026-10-10 사용자 확정(지점 관리자의 지원 수업 보상 정정 시 월 정산 확정 해제·재확정의 별도 승인 질문의 1번 답변): Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer의 지원 수업 보상 정정을 위해 월 정산을 확정 해제·재확정할 때는 Master의 별도 승인을 두지 않는다. Master 승인 대기 단계 없이 관리 범위 안에서 직접 처리하며 이전 확정본과 해제·재확정 이력 및 감사를 유지한다. 기존 Master Organization 범위·Branch Admin 대상 Trainer Home Branch 기준과 범위 밖 접근 거부는 유지한다. 해당 Trainer·월의 확정 해제 → 금액 정정 → 동일 월 재확정 순서와 재확정 시 미입력 지원 수업 차단 등 승인된 확정 조건도 유지한다. 이번 결정은 위 정정의 별도 Master 승인 생략에 한정하며 최초 월 정산 확정 권한/승인, Trainer 신청 승인, 다른 정정/취소 또는 정산 공개 범위로 확대하지 않는다. 확정 해제 사유 필수는 아래 후속 사용자 결정으로 확정했다. 위 지원 수업 보상 정정의 현재 Home Branch 권한 기준은 아래 후속 사용자 결정으로 확정했다.

2026-10-10 사용자 확정(지원 수업 보상 정정 시 월 정산 확정 해제 사유 질문의 1번 답변): 지원 수업 보상 정정의 월 정산 확정 해제에는 사유가 필수이며, 사유 없이 해제할 수 없다. 사유·해제자·시점을 이력으로 남긴다. Master Admin·Branch Admin 모두에 적용한다. 기존 Master Organization 범위·Branch Admin 대상 Trainer Home Branch 기준, Branch Admin의 별도 Master 승인 없음, 이전 확정본 보존과 해제·정정·동일 월 재확정 경로를 유지한다. 금액 수정의 변경 사유 필수도 유지한다. 사유 없는 해제 요청은 기존 확정 상태·확정본·보상 금액을 변경하지 않는다. 이번 결정은 위 지원 수업 보상 정정의 확정 해제에 한정하며 다른 정정/취소 정책으로 확대하지 않는다. 구체 입력 화면·저장 구조는 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(지점 이동 후 과거 지원 수업 보상 정정·정산 해제/재확정의 Home Branch 기준 질문의 1번 답변): 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 9월 수원 소속 Trainer가 10월 강남으로 이동한 뒤 9월 지원 수업 보상을 정정하는 예에서는 강남 Branch Admin에게 해당 정정과 월 정산 확정 해제·재확정을 허용하고, 별도 Master 권한이 없는 수원 Branch Admin에게는 과거 소속만을 근거로 허용하지 않는다. 과거 수업의 Performed Branch·수업 사실·이전 확정본·기존 이력은 보존한다. 기존 관리 범위 검증·Branch Admin의 별도 Master 승인 없음·금액 수정 사유 및 확정 해제 사유 필수·감사 정책을 유지한다. 이번 결정은 지원 수업 보상 금액 정정과 해당 월 정산 해제/재확정의 인가 기준에 한정한다. 다른 추가실적 최초 등록/정정의 이동 기준, Trainer 이동 자체의 적용 시점·절차, 비용 귀속·정산 공개(MB-010/006)는 미결정으로 남긴다. 당시 미정이었던 최초 월 정산 확정 권한과 별도 Master 승인 없음은 2026-10-11 후속 사용자 결정으로 확정했다.

비용 집계 수용 기준(2026-10-11 사용자 확정): 타 지점 지원 수업의 전체 보상으로 확정한 Additional Performance 금액은 해당 수업의 실제 Performed Branch 비용으로 집계한다. 수원점 소속 Trainer의 강남점 지원 수업 보상 30,000원은 해당 Trainer 월 정산에 추가실적으로 한 번 합산하고 강남점 비용으로 집계한다. 두 집계를 별도 지급으로 중복 가산하지 않는다. 소속 이동만으로 과거 비용 지점을 바꾸지 않는다. 기존 금액 입력·정정·확정 권한과 조회 Scope는 유지하며 비용 귀속으로 권한을 확대하지 않는다. 일반 지급·기본급·다른 추가실적의 귀속, 비용 보고 공개/집계 상세는 MB-010/006 OPEN이다.

지원 수업 외 추가실적 비용 수용 기준(2026-10-11 사용자 확정): 지원 수업 외 Additional Performance의 비용은 실적 발생 당시 대상 Trainer의 Home Branch에 귀속한다. 등록 시점·금액 확정 시점·대상 월말 또는 조회 시점의 소속으로 대체하지 않는다. 수원 소속 당시 회원 유지 실적의 보상 100,000원은 월말 강남 이동 후나 이동 후 등록에도 수원점 비용으로 집계한다. 금액·월 합산 횟수·기존 관리 권한은 유지한다. Session 연결 여부만으로 지원 수업의 수행 지점 비용 기준을 적용하지 않는다. 금액 산정·입력 제약·소속 이동 시 등록/정정 인가 시점·정산 월·발생 시점/소속 확인 예외와 비용 보고 공개/집계 상세는 관련 OPEN이다.

지원 수업 외 추가실적 금액 수용 기준(2026-10-11 사용자 확정): 회원 유지 등 지원 수업 외 Additional Performance의 금액도 권한 있는 관리자가 실적 건별로 직접 입력한다. v1에서 유형별 사전 금액·산식으로 자동 계산하는 방식을 채택하지 않으며 일반 RATE/FIXED_AMOUNT 계산 결과로 입력액을 대체하지 않는다. 예를 들어 같은 회원 유지 사유의 서로 다른 실적에 관리자가 100,000원과 150,000원을 입력하면 유형별 기본 금액으로 통일하지 않고 각 입력액을 사용한다. 기존 관리자 대상 범위·본인 등록·승인 생략·감사와 발생 당시 Home Branch 비용 귀속은 유지한다. 최초 등록 금액 필수는 아래 후속 결정으로 확정했다. 지원 수업 외 등록은 양수 금액만 허용하도록 후속 결정으로 확정했다. 상한액·정밀도 등 나머지 입력 제약·정산 월·정정/취소는 별도 OPEN이며 지원 수업 처리 절차를 자동 상속하지 않는다.

추가실적 등록 흐름 수용 기준(2026-10-11 사용자 확정): v1 추가실적은 권한 있는 관리자의 직접 등록만 지원하고 Trainer의 시스템 내 별도 신청·승인/반려 흐름은 두지 않는다. Trainer는 실적 내용을 관리자에게 전달하며 기존 Master Admin/Branch Admin이 허용된 관리 범위에서 입력한다. 기존 관리 Scope·관리 범위 안 본인 직접 등록·승인 생략·감사를 유지한다. 관리자 권한 없는 Trainer에게 직접 등록/별도 신청 권한을 제공하지 않는다. 관리자·Trainer 겸임자는 관리 권한으로 본인 직접 등록이 가능하다. Trainer의 PT 진행 기록·지원 수업 기록과 Pass 차감은 별도 승인된 흐름으로 유지한다. 신청 대기 상태나 승인/반려 단계를 v1 추가실적 처리의 필수 조건으로 만들지 않는다. 남은 금액/정정/취소 정책과 비지원 실적의 금액 외 정보 수정/취소의 이동 시 인가 시점은 관련 OPEN이다.

지원 수업 외 추가실적 등록 완료 수용 기준(2026-10-11 사용자 확정): 회원 유지 등 지원 수업 외 Additional Performance는 권한 있는 관리자가 실적 내용과 금액을 함께 입력해야 등록이 완료된다. 금액 미입력 요청은 등록을 완료할 수 없으며, 금액 없는 실적을 먼저 등록하고 나중에 금액을 입력하는 흐름은 v1에 두지 않는다. 누락 금액을 자동으로 0원이나 계산식 결과로 대체하지 않는다. 예를 들어 회원 유지 실적을 금액 없이 저장하려는 요청은 유효 추가실적으로 등록하거나 정산 입력에 반영하지 않는다. 허용된 금액과 필요한 실적 정보를 함께 입력한 등록만 완료한다. 금액이 아직 정해지지 않은 실적의 선등록/후입력 상태는 도입하지 않는다. 기존 관리 Scope·본인 건 허용·승인 생략·감사와 발생 당시 Home Branch 비용 귀속을 유지한다. 지원 수업의 PT 기록/차감 선완료·후속 금액 저장 흐름 및 미입력 지원 수업 월 확정 차단은 그대로다. 이 요건으로 0원 허용·나머지 입력 제약·정정/취소나 정산 월/자동 확정 정책을 결정하지 않는다.

지원 수업 외 추가실적 금액 하한 수용 기준(2026-10-11 사용자 확정): 등록 금액은 0원 초과인 양수만 허용한다. 금액 0원·음수 또는 금액 누락 요청은 유효 실적/정산 입력으로 등록하지 않고 거부한다. 사유가 있어도 지원 수업 외 실적의 0원 등록은 허용하지 않는다. 허용된 양수와 내용을 함께 입력하는 기존 관리자 등록·감사를 유지하며 구체 상한액/정밀도는 후속 결정한다. 지원 수업의 사유 필수 0원 확정·기록/Pass 차감 선완료 및 미입력 지원 수업 월 확정 차단은 유지한다. 이 요건은 다른 금액 항목의 제약이나 지원 수업 외 실적의 정정/취소·정산 월 정책을 승인한 것이 아니다.

지원 수업 외 추가실적 정산 월 수용 기준(2026-10-11 사용자 확정): 회원 유지 등 지원 수업 외 Additional Performance는 실제 실적이 발생한 월의 Trainer 월 정산에 귀속한다. 9월에 발생한 실적을 10월에 등록해도 9월분이며 등록 월이나 금액 입력 월로 이월하거나 관리자가 반영 월을 임의 선택하지 않는다. 같은 실적을 9월·10월에 중복 합산하지 않는다. 예를 들어 9월 수원 소속 때 발생한 회원 유지 실적을 10월 강남 이동 후 등록해도 Trainer의 정산 귀속은 9월분이고 비용 지점은 발생 당시 소속인 수원이다. 발생 월과 발생 당시 소속을 등록 월/현재 소속으로 대체하지 않는다. 이 사실이 등록/정정 권한을 자동 부여하지 않으며 기존 관리 Scope·금액 필수/양수·승인 생략·감사를 유지한다. 9월이 이미 확정된 경우 해당 Trainer·9월의 해제 → 누락 실적 등록 → 재확정과 이전 확정본 보존은 후속 사용자 결정으로 확정했다. 이 흐름의 해제/재확정 본인 건 허용·별도 승인 없음도 확정됐으며 확정 상태에 자동 합산하지 않는다. 발생 시점 식별·월 경계/시간대·소급 기간·나머지 정정/취소와 보고 집계 기간은 별도 OPEN이다.

확정 월의 누락된 지원 수업 외 추가실적 수용 기준(2026-10-11 사용자 확정): 이미 확정된 발생 월의 누락된 지원 수업 외 Additional Performance는 해당 Trainer·월 정산의 확정 해제 → 누락 실적 등록 → 같은 발생 월 재확정으로 반영한다. 이전 확정본은 보존하고 재확정 결과와 구분한다. 확정 상태에 직접 추가하여 이전 확정본을 덮어쓰거나 등록 월/다른 월로 이월하지 않는다. 다른 구성 금액이 같다면 이전 9월 확정 합계 3,850,000원에 누락 실적 100,000원을 등록한 후 새 9월 확정 합계는 3,950,000원이고 이전 3,850,000원 확정본은 보존한다. 다른 Trainer/월이나 등록 월 10월에 이 누락분을 가산하지 않는다. 내용+양수 금액·기존 등록 Scope/본인 건/승인 생략/감사와 발생 당시 Home Branch 비용 귀속은 유지한다. 재확정 시 기존 확정 조건을 재검증하고 미입력 지원 수업이 남으면 차단한다. 나머지 정정/취소·단계별 실패/재시도는 별도 OPEN이다.

2026-10-11 사용자 확정(지원 수업 외 실적 등록·누락 후등록의 이동 후 담당 관리자 질문의 1번 답변 및 재확인): 지원 수업 외 Additional Performance의 등록과, 확정된 발생 월의 누락분 반영을 위한 해당 Trainer·월 정산 확정 해제·재확정은 Master Admin에게 Organization 전체, Branch Admin에게 각 업무 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 등록·해제·재확정 요청마다 현재 소속과 관리 권한을 검증하고 최초 단계의 소속으로 후속 권한을 고정하지 않는다. 이전 소속·실적 발생 당시 소속·Performed Branch·클라이언트가 전달한 Branch Context만으로 권한을 부여하지 않는다. 9월 수원점 소속 때 발생한 회원 유지 실적을 10월 강남점 이동 후 처리하면 강남점 Branch Admin/Master가 담당하고, 별도 Master 권한 없는 이전 수원점 Branch Admin은 처리할 수 없다. 실적은 여전히 9월 정산·수원점 비용이며 이전 확정본과 감사 이력을 보존한다. 등록의 내용+양수 금액 필수·관리 범위 안 본인 등록·별도 승인 없음과 재확정의 기존 확정 조건/미입력 지원 수업 차단을 유지한다. 이 결정은 위 등록 및 누락분 후등록의 역할·관리 범위·소속 기준 시점에 한정한다. 누락분 반영을 위한 해제·재확정의 본인 건 처리/별도 승인·해제 사유 정책, 지원 수업 외 기존 실적의 정정/취소 권한·소속 기준 및 처리 절차는 별도 OPEN이다. 기존 지원 수업 보상/기본급 정정 권한이나 비용/조회 범위를 확대하지 않는다.

2026-10-11 사용자 확정(누락 실적 반영을 위한 정산 확정 해제 사유 질문의 1번 답변): 확정된 발생 월의 누락된 지원 수업 외 Additional Performance를 반영하기 위해 해당 Trainer·월 정산의 확정을 해제할 때 사유를 필수로 기록한다. Master Admin과 Branch Admin의 허용된 해제에 동일하게 적용하며 사유 없는 해제 요청은 거부한다. 거부 시 요청 직전의 확정 상태·확정본·기존 실적과 정산 구성/금액을 유지한다. 해제 성공 시 대상 Trainer·월, 해제 사유·처리자·처리 시점을 감사 가능한 이력으로 남기고 이전 확정본을 보존한다. 예를 들어 9월 회원 유지 실적 누락 반영을 사유로 식별할 수 있어야 한다. 각 처리 시점 현재 Home Branch 인가·해제 → 누락 등록 → 같은 월 재확정·발생 월 정산/발생 당시 Home Branch 비용 귀속과 재확정 조건을 유지한다. 이번 결정은 누락분 반영의 확정 해제 사유 필수에 한정하며 이 흐름의 해제/재확정 본인 건 처리·별도 승인 여부와 기존 실적 정정/취소 등 남은 정책은 별도 OPEN이다. 등록 사유/내용을 해제 사유로 자동 대체하거나 별도 승인 정책을 임의 확정하지 않는다.

2026-10-11 사용자 확정(Branch Admin의 본인이 아닌 소속 Trainer 누락 실적 반영 시 Master 승인 질문의 1번 답변): Branch Admin이 본인이 아닌 소속 Trainer의 확정된 발생 월 누락 실적(지원 수업 외 Additional Performance)을 반영할 때, 해당 Trainer·월 정산의 확정 해제·재확정에 별도 Master 승인을 두지 않는다. 각 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인지 검증한 후 Master 승인 대기 없이 직접 처리한다. 해제 사유 필수·사유 없는 요청 거부와 요청 직전 확정 상태/금액 보존, 해제 → 내용과 양수 금액을 갖춘 누락 실적 등록 → 같은 발생 월 재확정 순서, 이전 확정본·처리 이력/감사 보존을 유지한다. 재확정은 기존 확정 조건을 다시 검증하고 미입력 지원 수업이 남으면 해당 Trainer·월을 확정하지 않는다. 승인 생략은 자동 등록/재확정이나 관리 범위 밖 접근을 허용하지 않는다. 발생 월 정산·발생 당시 Home Branch 비용 귀속과 과거 지급/적용 기본급 보존은 유지한다. 이번 결정은 Branch Admin의 본인이 아닌 소속 Trainer 건에 한정하며 관리자 본인의 누락 실적 반영을 위한 해제/재확정 허용 및 해당 본인 건의 별도 승인 정책은 OPEN이다. 이미 승인된 관리 범위 안 본인 실적 등록·기존 지원 수업 보상/기본급 정정 정책은 변경하지 않는다. 기존 비지원 실적 정정/취소·나머지 수명/입력 정책과 구체 계약/UoW/동시성은 별도 결정 또는 설계 대상이다.

2026-10-11 사용자 확정(관리자·Trainer 겸임자의 본인 누락 실적 반영을 위한 확정 해제·재확정 질문의 1번 답변): 관리자·Trainer 겸임자는 관리 권한 범위 안에서 본인의 확정 월 누락 실적(지원 수업 외 Additional Performance)을 반영하기 위한 정산 확정 해제·재확정을 별도 승인 없이 직접 처리할 수 있다. Master Admin은 Organization 범위 안의 본인 건, Branch Admin은 각 처리 시점 본인 Trainer의 현재 Home Branch가 자신의 관리 Branch와 일치하는 경우 허용한다. Actor와 대상 Trainer가 동일인이어도 해제 사유 필수·사유 누락 거부/요청 직전 상태 보존·처리 이력과 감사·이전 확정본 보존은 동일하게 적용한다. Trainer 역할만으로는 본인 정산을 해제/재확정할 수 없으며 관리자 권한/Scope와 현재 소속을 요청마다 검증한다. 해제 → 내용과 양수 금액을 갖춘 누락 실적 등록 → 동일 발생 월 재확정 순서와 발생 당시 Home Branch 비용 귀속을 유지한다. 재확정은 기존 승인 조건을 다시 검증하고 미입력 지원 수업이 남으면 차단하며 본인 건/승인 생략을 이유로 자동 확정하거나 검증을 생략하지 않는다. 기존 비지원 실적 정정/취소·발생 시점/월 경계·소급 기간·나머지 금액 제약은 별도 OPEN이며 구체 계약/저장/단계별 UoW·실패/재시도·이동 경합은 PROPOSED다.

2026-10-11 사용자 확정(정산 확정 전 지원 수업 외 추가실적 금액 수정 권한 질문의 1번 답변): 월 정산 확정 전, 이미 등록한 회원 유지 등 지원 수업 외 Additional Performance의 금액 수정은 Master Admin에게 Organization 전체, Branch Admin에게 수정 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안 관리자·Trainer 겸임자의 본인 건도 포함하며 Master/다른 관리자의 별도 승인 없이 직접 수정한다. 모든 금액 수정에 변경 사유가 필수이고 변경 전후 금액·변경 사유·수정 Actor·처리 시점을 감사 가능한 이력으로 남긴다. 사유 없는 수정 요청은 거부하고 요청 직전 금액·기존 이력·정산 입력 상태를 유지한다. 현재 권한·관리 Scope·대상 Trainer의 현재 소속을 각 요청에서 검증하며 이전 소속/실적 발생 당시 소속·Performed Branch·위조 Branch Context/직접 ID만으로 권한을 부여하지 않는다. 관리자 권한 없는 Operator/Trainer는 본인 건도 수정할 수 없다. 실적 발생 월 정산·발생 당시 Home Branch 비용 귀속과 이전 이력을 유지하고 금액 수정만으로 PT 진행 사실/Pass 차감이나 과거 일반 지급·적용 기본급을 변경하지 않는다. 이번 결정은 확정 전 금액 수정의 역할·Scope·현재 소속 기준·본인 건·별도 승인 없음·사유/이력에 한정한다. 수정 금액의 0원/음수 허용·상한/정밀도, 금액 외 정보 수정·취소 및 확정된 월의 금액 정정/해제·재확정 상세는 별도 OPEN이며 기존 누락 실적 후등록 정책과 구분한다. 구체 입력/저장 계약·UoW·실패/재시도·소속 이동/정산 확정 경합은 PROPOSED다.

2026-10-11 사용자 확정(상황이 달라도 이전 선택지를 참고해 같은 답으로 진행하라는 지시): 유사 상황은 이전 사용자 선택을 참고해 같은 기준으로 진행하라는 지시에 따라, 지원 수업 외 Additional Performance의 최초 등록 금액 > 0 기준을 월 정산 확정 전 금액 수정에도 동일하게 적용한다. 수정 후 금액은 양수만 허용하고 0원·음수·금액 누락 요청은 거부하며 사유를 남겨도 0원 수정 예외를 두지 않는다. 거부 시 요청 직전 금액·이력·정산 입력 상태를 유지한다. 허용된 수정에도 기존 Master Organization/Branch Admin 수정 시점 현재 Home Branch 인가·관리 범위 안 본인 건 허용·별도 승인 없음·변경 사유 필수와 전후 금액/사유/수정자/시점 이력·감사를 적용한다. 발생 월 정산·발생 당시 Home Branch 비용 귀속과 과거 확정 지급/적용 기본급 보존을 유지한다. 지원 수업 보상의 사유 필수 0원 확정/수정과 월별 수동 적용 기본급의 사유 필수 0원 지정은 기존 승인 범위대로 유지한다. 금액 상한·정밀도/표현을 새로 정하거나 0원 덮어쓰기/음수 입력을 실적 취소 절차의 대체로 도입하지 않는다. 확정 후 금액 정정·금액 외 정보 수정/취소 등 남은 정책 및 구체 계약/저장/UoW·실패/재시도·동시성은 별도 결정 또는 설계 대상이다.

2026-10-11 사용자 일관성 지시 적용(기존 지원 수업 보상·기본급의 확정 월 금액 오류 처리 재사용): 유사 상황에 이전 선택을 적용하라는 사용자 지시에 따라 지원 수업 보상/기본급의 확정 월 금액 오류 정정 흐름을 지원 수업 외 Additional Performance에도 적용한다. 확정된 발생 월 실적의 금액 오류는 해당 Trainer·월 확정 해제 → 해당 실적 금액 정정 → 같은 발생 월 재확정으로 처리하고 이전 확정본과 당시 적용 구성/금액/합계·정정 전후 이력을 보존한다. Master Admin은 Organization 전체, Branch Admin은 각 해제/정정/재확정 처리 시점 대상 Trainer의 현재 Home Branch가 관리 Branch인 경우 허용한다. 관리 범위 안 관리자·Trainer 겸임자의 본인 건도 포함하고 별도 Master/다른 관리자 승인 대기를 두지 않는다. 해제와 금액 정정 모두 사유가 필수이며 사유 없는 각 요청은 요청 직전 상태·금액·확정본/이력을 유지하고 거부한다. 해제 사유/처리자/시점과 정정 전후 금액/사유/수정자/시점을 감사 가능한 이력으로 남긴다. 정정 금액도 기존 등록/확정 전 수정과 동일하게 양수만 허용하며 0원·음수·금액 누락 요청은 사유가 있어도 거부한다. 재확정은 기존 승인 조건을 다시 검증하고 금액 미입력 지원 수업이 남으면 해당 Trainer·월을 확정하지 않는다. 정정 저장만으로 자동 재확정하지 않으며 현재 Rate/Fixed Amount/Base Salary로 과거 일반 지급/적용 기본급을 재계산하지 않는다. 실적의 발생 월 정산과 발생 당시 Home Branch 비용 귀속을 유지하고 다른 월/Trainer나 PT 진행 사실·Pass를 변경하지 않는다. 예를 들어 다른 구성 금액이 같고 기존 실적 100,000원을 120,000원으로 정정하면 이전 9월 확정 합계 3,850,000원을 보존하며 새 9월 합계는 3,870,000원이다. 금액 외 정보 수정·실적 취소·발생 시점 식별/월 경계·소급 기간·나머지 금액 제약은 별도 OPEN이다. 각 단계 계약/저장/버전·UoW·실패/재시도·이동/정산 경합은 PROPOSED이며 전체 흐름을 임의의 단일 commit으로 정하지 않는다.

보상 범위 수용 기준(2026-10-11 사용자 확정): 일반 PT 수당의 기존 RATE/FIXED_AMOUNT 계산·확정 및 기본급의 별도 월 정산 반영을 유지한다. 그 외 모든 보상은 사유와 무관하게 기존 추가실적에서 권한 있는 관리자가 직접 입력하며, 사유별 별도 자동 산정 기능을 두지 않는다. 타 지점 지원 수업 보상은 기존대로 추가실적만 반영하고 일반 Session Payment와 중복 합산하지 않는다.

2026-10-11 사용자 확정: 허용된 PT 진행 기록 취소는 그 수업 보상의 추가실적 자동 무효 처리를 동반한다. 유효 월 정산/지점 비용에서 제외하되 기존 금액·이력을 보존하고 다른 추가실적은 유지한다. 기존 기록 취소 권한과 Home Branch 기준 금액 입력/전체 정산 권한은 구별하며 확정 월의 기존 해제 → 취소 → 같은 월 재확정 순서를 따른다. 상세 근거는 BR-PAY-015/PD-027. 나머지 정정/취소·복원 예외 및 계약/원자성/동시성은 후속 대상이다.

승인 근거: PD-027; BR-PAY-015; PR-010/027.

후속 TODO: BR-013, MB-010/006. 관리자 직접 등록 역할·Home Branch 기준 대상 범위·Branch Admin의 본인이 아닌 소속 Trainer 직접 등록 시 별도 Master 승인 없음·관리 범위 안 본인 직접 등록 및 본인 건 별도 승인 없음·타 지점 지원 수업 금액의 관리자 건별 수동 입력·기록/차감 후 금액 저장 시 보상 확정·미입력과 확정 0원 구분 및 추적·미입력 지원 수업이 남은 해당 Trainer·월 정산 확정 차단·사유 필수의 지원 수업 0원 확정 허용·월 정산 확정 전 지원 수업 금액 수정의 관리자 대상 범위/본인 건 허용/변경 이력·본인 건 포함 수정의 별도 승인 없음/저장 즉시 반영·해당 모든 수정의 변경 사유 필수·지원 수업 금액 오류의 해당 월 확정 해제/정정/재확정과 이전 확정본 보존·지원 수업 정정 시 Master Organization/Branch Admin 대상 Trainer Home Branch 기준 해제·재확정 권한·해당 Branch Admin 정정의 별도 Master 승인 없음·지원 수업 정정의 확정 해제 사유 필수 기록·지원 수업 정정의 처리 시점 현재 Home Branch 인가 기준은 해결됨. Operator의 남은 업무 권한, 지원 수업 외 실적의 금액 외 정보 수정/취소의 소속 이동 시 권한 기준 시점·지원 수업 외 추가실적의 남은 입력 제약·금액 미입력 건의 추적 표현·정정 연동·진행 기록 연계 상세·나머지 정정/취소·마감 이후 처리 및 발생 시점/소속 확인 등 귀속의 남은 예외·비용 보고 공개/집계 상세는 결정 전 설계·구현 확정 보류. MB-009 보상 구성은 해결됨.

AS-IS reference: 직접 대응 사실을 확정하지 않음. F22–25/PR-012는 수동 매출 제외를 유지한다.

2026-10-12 H 일괄 승인 반영: H2/H3=1: 지원 수업 외 실적 내용 수정/취소는 현재 Trainer Home Branch 관리 Scope·본인 포함/별도 승인 없음·사유/이력/감사를 적용한다(BR-PAY-019). 대상 Trainer 또는 실제 발생 날짜 오류는 원본 취소 후 올바르게 재등록/연결하고 취소 건은 유효 합산에서 제외한다. 다른 Trainer/월 각각 현재 인가·기존 양수 금액/발생 월·당시 Home 비용·확정 월 해제/처리/재확정·이전본 보존을 유지한다. 지원 수업 보상 연결을 임의 변경하지 않는다. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch). 실제 계약/구현·검증은 후속이다.

W1 전환 보상: 과거 Trainer Home 오류로 일반→지원 정정 시 이전 일반 지급을 이력 보존/유효 합계 제외하고 전체 보상을 기존 Master/현재 Trainer Home Branch Admin 범위의 수동 추가실적으로 입력한다. 일반 금액 자동 복사/자동 0원은 불가하며 미입력 지원 보상은 해당 월 확정을 막는다. 지원→일반 정정의 이전 지원 보상도 보존/유효 합계 제외해 일반 지급과 중복하지 않는다. Master 전용 수업 분류 정정을 추가실적 입력 전부의 Master 전용 제한이나 수행 지점 관리자의 타 Home 금액 공개 권한으로 확대하지 않는다(BR-OPS-033/PAY-024; [W 승인](product-decisions.md#review-20261013-w-batch); V-124/125 미구성·미실행).
