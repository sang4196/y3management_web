# Product Decisions — 승인 반영

2026-10-18 추가 승인: [MFA M7/M8](#review-20261018-mfa-m7-m8)로 본인 Passkey 삭제 성공 시 현재 기기 포함 모든 기존 로그인 종료, Master의 본인 계정 관리자 비밀번호 재설정 금지를 확정했다. M4 마지막 key 삭제 금지·C3 현재 비밀번호 확인 본인 변경·M2/AB5 분실 복구를 유지한다. 해당 후속 기능 구현/인수 완료는 아니다.

2026-10-18 최신 부분 승인: [MFA M3–M6](#review-20261018-mfa-m3-m6) 모두 1번이다. 설치/본인 최초 설정에 연계한 첫 Passkey 등록·정상 MFA 로그인한 본인 추가 등록, 마지막 Passkey 본인 삭제 금지, 분실 재등록 링크30분, 같은 Organization 정상 Master의 추가 Master 신규 발급을 확정한다. 구체 계약/구현·독립 검증 및 운영 게이트와 기존 OPEN 상태는 구별한다.

2026-10-16 최신 부분 승인: [MFA 후속 M1/M2](#review-20261016-mfa-m-batch)로 관리자 계정의 복수 Passkey 등록을 허용하고, 같은 Organization의 다른 정상 Master가 관리자 Passkey 분실의 본인 확인·기존 Passkey/모든 로그인 폐기·일회용 재등록 링크 전달을 처리한다. AB4 추가 인증·AB5 모든 Master 로그인 불가 비상 복구와 기존 OPEN 상태를 유지한다.

현재 후속 정책: [2026-10-13 AB 승인](product-decisions.md#review-20261013-ab-batch)의 AB1–AB6 모두 1번이다. 월 정산 대상은 적용 기본급/월별 지정·유효 PT/보상대기 지원 PT/추가실적 등으로 자동 선정하며, 한 달 전체 Trainer 비활성·명시 기본급0·무활동·정정 대기 없는 경우 새 정산 확정 의무에서 제외한다. 기존 이력/미완료와 비활성만으로 기본급을 자동0으로 바꾸지 않음은 유지한다. 후속 reset 링크30분·운영 관리자 비밀번호 뒤 Passkey·업무책임자 승인/별도 운영담당자 비상 복구·Chrome/Edge/Safari 최신2개 안정 주버전을 선택했다. K3/X1 첫 IAM/별도 구현 지시·구체 계약 PROPOSED와 22 OPEN/8 CLOSED는 유지한다.

승인 근거: 기존 2026-09-15~17 결정 및 2026-09-17 최신 지점 관계·추가실적·월 기본급·보상 설정 권한 확정. 현재 유효 결정은 각 Decision에 기록하며 폐기된 방향은 README 변경 이력으로 구분한다.

Status 정의: CLOSED = 사용자가 제품 방향을 승인함(제외·보류 승인 포함). OPEN = 아직 후속 단계에서 결정할 내용이 남음. **PD-001–020 및 PD-022–027은 CLOSED(26개), PD-021은 OPEN(1개)**이다. 세부 규칙은 [Open Questions](open-questions.md)로 분리하여 기존 PD를 다시 OPEN으로 만들지 않는다.

<a id="pd-001"></a>
## PD-001

Question: 웹 시스템의 실제 운영 사용자는 누구이며 업무별 권한을 어떻게 나눌까?

Status: CLOSED

Decision / approved direction: Role은 행위, Data Scope는 허용 데이터 범위다. Master Admin은 Organization 전체, Branch Admin은 하나의 Branch, Operator는 지정된 단일 Branch의 허용 업무, Trainer는 Allowed PT Scope의 로그인 Actor다. Rate / Fixed Amount / Base Salary 세 항목의 조회·설정·변경은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 단일 Branch를 Home Branch로 가진 Trainer에게만 허용한다. 관리자와 Trainer를 겸하는 계정은 관리 권한 범위 안이면 본인의 세 항목도 조회·변경할 수 있다. Master Admin은 본인 포함 허용하며, Branch Admin은 본인 Trainer의 Home Branch가 관리 Branch일 때 본인도 허용한다. 관리자 권한이 없는 Operator·Trainer 계정은 본인 포함 모든 Trainer 설정 조회·변경이 불가하다. 타 지점 지원 수업은 보상 설정 접근 권한을 부여하지 않는다. Backend에서 대상 Trainer의 Home Branch를 검증하며 직접 ID 요청과 감사·정산 등 우회 경로에도 제한을 적용한다. 모든 보상 설정 변경(최초 설정 포함)에 대상 Trainer, 변경 항목, 변경 전 값, 변경 후 값, 변경 Actor, Actor의 권한 및 Branch Context, 변경 시점을 추적한다. 별도 Master Admin 승인 없이 변경 가능하며 변경 요청→승인 대기→승인→반영 절차를 추가하지 않는다. 이 결정은 추가실적 승인이나 월 정산 마감/확정 절차를 면제하지 않는다.

Approval source: 2026-09-17 최신 사용자 지점 관계·추가실적·월 기본급·보상 설정 권한 확정. 충돌하는 이전 방향은 대체하며 비충돌 결정을 유지한다.

Follow-up: ARCH-001/002, MB-004/006. RBAC/ABAC 등 기술 모델과 세부 Permission은 Architecture에서 결정한다. [후속 질문](open-questions.md)

추가 사용자 확정(2026-10-10, 이번 설계 검토의 직접 답변): Master Admin 또는 Branch Admin이 Trainer를 겸할 수 있으며 한 계정으로 관리 업무와 본인의 PT 진행 기록을 모두 수행한다. Actor를 사람의 상호 배타적 분류로 취급하지 않는다. 같은 날 사용자의 최종 정정에 따라 보유한 관리 권한 범위 안이면 본인 보상 설정 조회·변경도 허용한다. Master는 본인 포함, Branch Admin은 본인 Trainer의 Home Branch가 관리 Branch일 때 허용하며 “본인은 Master만 가능” 답변을 대체한다. 관리자 권한이 없는 Trainer의 설정 접근 금지는 유지한다. 구체 역할 부여·행위별 인가·감사 표현은 ARCH-001에서 상세화한다.

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): 08 인증·권한; R35. [분석 색인](../analysis/README.md)

2026-10-12 사용자 확정(Operator 업무 허용 지점 수 질문의 1번): v1 Operator 역할의 업무 허용 Branch는 한 시점에 하나만 지정한다. Operator는 그 지정된 단일 Branch에서 명시적으로 허용된 업무를 수행하며 같은 계정의 Operator 권한을 여러 Branch에 동시 부여하지 않는다. Branch당 Operator 한 명이라는 1:1 인원 제한을 추가하지 않으며 하나의 Branch에 여러 Operator가 있을 수 있다. 이 결정은 Operator 역할의 업무 Scope이며 기존에 허용된 겸임 역할의 독립적인 관리/PT 권한이나 Trainer Home Branch를 바꾸지 않는다(BR-OPS-011, PD-001/007, PR-001/003/030, ARCH-001, MB-004).

기존 발급/검색 규칙 유지: Operator의 새 Pass 발급은 자신의 지정된 단일 Branch를 실제 Issued Branch로 사용한다. 그 발급 업무에서는 같은 Organization 전체 지점 Member를 이름·전화번호 일부로 검색하고 결과의 이름·전체 전화번호·현재 Member Home Branch를 조회/선택할 수 있다(BR-OPS-010). Member Home Branch가 Operator 업무 Branch와 다르다고 검색/발급을 거부하거나 회원 소속을 자동 이동하지 않는다. 전체 지점 Member 검색이 다른 Branch의 Pass 발급이나 일반 회원 상세/다른 Pass/PT·보상/수정·일괄 내보내기 권한을 부여하지 않는다. 기존 Master 전용 공통 상품 변경 및 관리자 전용 Pass 수동 조정·만료/해제·담당 교체/보상 업무 제한은 유지한다.

남은 결정: 새 Operator 발급/최초 Branch 지정 Actor는 Master Organization 전체/Branch Admin 자기 단일 Branch, 기존 Operator 업무 Branch 변경 Actor는 Master Organization 범위 전용으로 해결됐다. 변경은 기존 저장 후 현재 Scope 반영/실패 보존·감사 원칙을 적용한다. 발급 절차·기존 계정 역할 추가/변경·Operator 지점 변경의 대상 Branch/계정 상태·세부 절차/감사 계약 및 나머지 운영 행위 권한은 MB-004·ARCH-001/002 후속이다. 한 계정의 Operator 동시 허용 지점 수나 신규 발급/지점 변경 Actor를 다시 OPEN으로 두지 않는다. 실제 발급 대상·초기 조건/선택 응답·역할/Scope 저장·Caller/인가 계약·실패/재시도/경합은 관련 Product/Architecture 후속이다. IAM-001 S1에 Operator 구현을 추가하거나 기존 PROPOSED 인증/모듈/저장 설계를 승인한 것은 아니다.


<a id="pd-002"></a>
## PD-002

Question: 트레이너가 직접 로그인할 수 있어야 하는가?

Status: CLOSED

Decision / approved direction: Trainer는 v1부터 직접 로그인하며 허용된 Member/PT 업무 조회, 자신이 실제 진행한 Session 등록 및 자신의 Session 조회를 수행한다. 일반 Session Payment 적용 대상은 정상 등록 시 사용할 Pass 결정 → Pass 차감 → Pass 발급 당시 Product Payment Type 확인 → 해당 시점 Trainer Rate/Fixed Amount 적용 → Session Payment 계산·확정 흐름을 따른다. 지급 설정 조회·변경은 불가하다.

2026-10-12 사용자 확정(Trainer 회원 검색·조회 범위 질문의 1번): Trainer 조회 대상은 본인이 담당 Trainer로 지정된 Pass의 회원과 개별 허용된 지원 수업 대상 회원만이다. 같은 Home Branch/타 지점 PT 가능 사실만으로 지점·Organization 전체 회원 조회는 불가하다. Backend는 검증된 Trainer 연결/Organization Scope와 담당 또는 개별 지원 허용 사실로 목록·검색·직접 ID 상세를 제한한다. 관리자 겸임자의 별도 관리 Scope, Trainer의 민감 보상 금지와 기존 PT/Pass 규칙은 유지한다. 담당 관계 인정 조건·지원 지정/철회/기간·공개 정보 항목/나머지 PT 업무 인가는 후속이며 MB-001/003/005는 잔여 질문 때문에 OPEN이다(BR-OPS-005, PR-002/029/030).

2026-10-12 사용자 확정(지원 대상 지정 권한 질문의 1번): 개별 지원 대상 지정은 Master Organization 전체/Branch Admin 처리 시점 현재 관리 Branch=Member 현재 Home Branch 범위에서만 허용한다. 수원 소속 Member를 강남 Trainer의 지원 대상으로 지정할 때 수원 관리자/Master는 가능하고 Member 소속을 관리하지 않는 강남 수행 지점 관리자는 불가하다. Trainer Home/Performed/Pass Issued Branch·과거 소속/지정 Actor 사실은 대체 권한 근거가 아니다. Backend 현재 Scope/회원 소속·같은 Organization의 대상 관계를 검증하고 비관리자 Operator/Trainer의 지정을 차단하며 기존 권한 변경 감사 원칙을 적용한다. 대상 Trainer 설정/보상·전체 회원 공개 권한이나 Home Branch 변경을 부여하지 않는다. 지정 주체/Scope 질문은 해결됐고 기간/철회 주체·이동 후 기존 허용·절차/공개 항목은 후속이다(BR-OPS-005, PR-002/029/030, MB-001/002/003/005, NFR-004).

2026-10-12 사용자 확정: 개별 지원 조회 허용은 관리자가 해제할 때까지 유지하며 고정 종료일/기간 경과 자동 종료·반복 연장은 두지 않는다. 해제 Actor/Scope는 기존 지정 권한과 같은 Master Organization/Branch Admin 처리 시점 Member 현재 Home Branch 기준을 적용한다(2026-10-11 사용자 일관성 지시 적용). Backend 현재 권한/대상 Organization 검증과 NFR-004 감사를 유지한다. 해제는 해당 지원 관계의 조회 근거만 종료하며 별도의 담당/관리 권한과 기존 PT·Pass·지급/정산은 그대로 판단한다. 소속 이동 후 기존 허용·대상 상태/담당 관계 인정·절차/공개 정보는 후속이다(BR-OPS-005).

2026-10-12 사용자 확정: Member Home Branch 변경만으로 기존 개별 지원 조회 허용을 해제하거나 재지정하지 않고 유지한다. 이동 후 지정/해제는 Master Organization 또는 각 처리 시점 Member 현재 Home Branch 관리 Branch Admin이 담당하며 이전 소속/과거 지정 Actor만으로 권한을 유지하지 않는다. 동일 Organization 내 Trainer Home Branch만 변경된 경우도 같은 유지 원칙을 적용한다(2026-10-11 사용자 일관성 지시). 현재 Caller/대상 관계 검증과 기존 감사 이력·별도 담당/관리 Scope를 유지한다. 과거 수업/Pass/지급/정산 변경이나 일반/지원 구분 고정은 없고 수업 당시 Trainer 소속 기준을 따른다. 이동 자체의 권한/시점/이력·다른 대상 상태·담당 관계/공개 필드/절차·계약/저장은 후속이다(BR-OPS-005, MB-001/002/003/005).

2026-10-12 사용자 수정 확정(잔여 0 회원 조회와 제외 필터): 본인이 담당한 이용권의 잔여가 모두 0이어도 그 사실만으로 담당 회원의 목록·검색·상세 조회를 차단하지 않는다. 기본 조회에는 잔여 0 회원도 포함하고 선택 기능인 “잔여 0인 회원 제외” 필터를 제공한다. 필터 미사용 시 포함/사용 시 해당 조건의 회원을 결과에서 제외하며 조회 권한이나 담당/지원 관계·회원 상태를 변경하지 않는다. Backend의 현재 Caller/Organization·담당 또는 개별 지원 관계 인가는 필터와 독립적으로 유지한다. 조회 허용이 Remaining > 0 등 기존 PT 등록/차감 조건을 면제하지 않는다. 여러 이용권의 잔여 집계 범위·개별 지원 회원 등 담당 이용권 없는 대상의 판정과 수동 만료/취소·담당 변경 등 다른 상태의 조회 영향/공개 필드는 후속이다(BR-OPS-005, PR-002/029/030, MB-001/003/005).

2026-10-12 사용자 확정(잔여 제외 필터의 집계 기준 질문의 1번): “잔여 0인 회원 제외”는 조회 권한이 확인된 Member의 전체 이용권 잔여를 기준으로 판단한다. 조회 Trainer가 담당한 Pass만으로 제한하지 않으며 동일 Organization 내 다른 Trainer 담당/다른 Issued Branch의 Pass도 해당 Member의 집계 범위에 포함한다. 내 담당 Pass 0회+다른 Trainer 담당 Pass 10회인 Member는 필터를 켜도 표시하고 전체 집계 잔여가 0이면 제외한다. 개별 지원 회원도 자기 담당 Pass 존재 여부와 관계없이 같은 Member 전체 기준을 적용한다. 필터 미사용의 기본 조회/개별 상세 권한은 그대로이며 다른 회원/개별 Pass·다른 Trainer PT/보상 정보를 자동 공개하지 않는다. 집계 범위는 확정됐고 나머지 종료 상태의 잔여 취급·담당 변경/비활성·공개 필드 및 계약/저장/조회 일관성은 후속이다(BR-OPS-005, PR-002/029/030, MB-001/003/005).

2026-10-12 사용자 확정(Trainer의 회원 전화번호 조회 질문의 1번): Trainer는 기존 조회 권한이 확인된 담당 회원과 개별 허용 지원 회원의 등록된 전체 전화번호를 조회할 수 있다. 부분 마스킹된 번호만 허용하는 정책으로 제한하지 않는다. 담당 Pass 잔여가 모두 0이어도 기존 회원 조회 권한이 유지되면 전화번호도 같은 범위에서 조회한다. Backend는 전화번호를 반환하는 조회마다 현재 Caller/Organization·담당 또는 지원 관계를 검증하고 미담당/미허용 회원·타 Organization 번호를 공개하지 않는다. 지원 해제 후 별도의 유효한 담당/관리 권한이 없으면 해당 번호도 공개하지 않는다. 관리자 겸임자의 별도 관리 Scope는 유지한다. 이번 승인은 전화번호 읽기이며 수정/일괄 내보내기·다른 개인정보/개별 Pass·다른 Trainer PT/보상 공개 권한을 추가하지 않는다. 전화번호 필수 수집/형식·중복/검증과 나머지 필드/보존·조회 계약은 후속이다(BR-OPS-005, PR-002/029/030, NFR-001/005, LEGAL-001).

Approval source: 2026-09-17 사용자 Multi-Branch 제품 방향 변경 지시. 충돌하는 이전 결정은 본 결정으로 대체하며 기존 비충돌 규칙은 유지한다.

Follow-up: MB-001/003/005: 본인 담당 회원+개별 허용 지원 회원 조회 대상은 확정(BR-OPS-005). 기존 Pass의 담당 교체 허용/잔여·과거 이력 보존은 확정(BR-OPS-008, 2026-10-12); 현재 담당 기반 조회는 기존 원칙을 적용한다. 교체 권한은 Master Organization 전체/Branch Admin 처리 시점 Member 현재 Home Branch 기준으로 확정(2026-10-12)됐다. 교체 대상은 같은 Organization의 다른 지점 Trainer도 허용(2026-10-12); 교체 전 본인 수업은 이전 담당도 직접 누락 등록 가능/회원 조회 권한 비복원으로 확정(2026-10-12, BR-OPS-003/008)됐다. 잔여 0으로 이용을 마친 Pass도 담당 교체/새 현재 담당의 기존 회원 조회 허용으로 확정(2026-10-12, BR-OPS-008)됐다. 수동 만료/취소 등 다른 사유의 상태·과거 담당/수행 사실 확인 불가/정정과 계약은 후속이다. 잔여 0만으로 담당 회원 조회를 제한하지 않음/선택 제외 필터는 확정. 필터는 인가된 Member 전체 Pass 잔여 기준(다른 담당 Trainer/Issued Branch 및 개별 지원 회원 포함)으로 확정했다. 인가된 담당/지원 회원의 전체 전화번호 조회도 확정했다. 그 외 담당 관계 인정·다른 종료 상태의 잔여 정의/집계·지원 지정/해제 절차·Master 전용 Trainer 이동의 대상/절차·과거 소속 사실 정정·Trainer/Member 이동 이력/정정·전화번호 외 공개 항목/전화번호 형식·검증 정책과 나머지 교차 PT 업무, 관리 담당자의 정정 상세는 후속이다. 지원 지정과 수동 해제는 Master Organization/Branch Admin 각 처리 시점 Member 현재 Home Branch 기준이며, 개별 지원 허용은 관리자 해제 전까지 유지/기간 자동 종료 없음이며 동일 Organization 내 Member Home Branch 변경에도 유지한다. Trainer Home Branch만 바뀌는 경우에도 사용자 일관성 지시로 같은 원칙을 적용한다. Trainer 역할의 본인 정정/취소는 불가로 확정(2026-10-11). 타 지점 보상 구성은 해당 수업의 보상 전체를 Additional Performance로 처리하는 방식으로 확정(MB-009 CLOSED, 2026-10-10). PR-008/029.

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): 02 도메인; 08 인증·권한. [분석 색인](../analysis/README.md)

<a id="pd-003"></a>
## PD-003

Question: 회원 본인의 웹 접근을 제공할까?

Status: CLOSED

Decision / approved direction: Member는 v1 관리 대상 Domain이며 직접 로그인 Actor가 아니다. Member Authentication/Self-Service는 추가 계획이 있는 명시적 Future Scope다. 향후 자신의 PT Schedule·예약 Session·Pass·잔여 조회, PT 예약 및 Schedule 취소를 고려한다. Member와 Login Account는 현재 동일 개념이 아니다.

Approval source: 2026-09-17 사용자 Multi-Branch 제품 방향 변경 지시. 충돌하는 이전 결정은 본 결정으로 대체하며 기존 비충돌 규칙은 유지한다.

Follow-up: PD-025/026; 향후 Account 연결은 Architecture/Product Expansion에서 정의한다. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): 02 도메인; 08 인증·권한. [분석 색인](../analysis/README.md)

<a id="pd-004"></a>
## PD-004

Question: v1에서 몇 개 센터와 어떤 센터 간 접근을 지원할까?

Status: CLOSED

Decision / approved direction: 하나의 헬스장 Organization이 여러 Branch를 운영한다. 독립 고객사 SaaS는 추가하지 않는다. Master Admin의 Branch 등록·전체 조회·정보/구조 관리와 활성/비활성 관리 가능성은 유지한다. Trainer는 한 시점에 Home Branch 하나에 소속되고 Branch에는 여러 Trainer가 있을 수 있다. Branch당 Trainer 한 명인 1:1이나 Trainer 동시 복수 소속 N:M을 요구하지 않는다. Member도 Home Branch 하나를 가지며 Pass는 Issued Branch 하나를 가진다. Trainer·Member·Pass는 허용된 조건에서 타 지점 PT 업무를 수행·이용할 수 있다. Session은 실제 Performed Branch를 식별하고 소속·발급 지점 변경으로 과거 수행 지점이 바뀌지 않아야 한다. Product는 Organization 공통 Catalog이며 지점별 가격 정책은 추가하지 않는다. Branch Admin은 하나의 Branch를 관리하고 일부 여러 지점만 담당하는 중간 관리자 역할은 추가하지 않는다.

2026-10-12 사용자 확정(공통 PT 상품 생성·수정 권한 질문의 1번): Organization 공통 상품의 생성·수정은 Master Admin만 허용한다. Master 권한 없는 Branch Admin·Operator·Trainer의 직접 변경은 불가하며 Backend에서 현재 Master 권한/Organization Scope를 검증한다. 기존 Pass의 발급 당시 가격·총횟수·Payment Type 및 잔여/과거 이력은 보존하고 변경은 새 Pass부터 적용한다. 상품 조회·Pass 발급 권한 및 상품 상태/삭제의 미정 상세를 자동 확정하지 않는다. MB-007은 CLOSED로 해결됐다(PR-006/030, BR-PAY-001).

Approval source: 2026-09-17 최신 사용자 지점 관계·추가실적·월 기본급·보상 설정 권한 확정. 충돌하는 이전 방향은 대체하며 비충돌 결정을 유지한다.

Follow-up: MB-001–008의 남은 이동·교차 업무 허용 조건·조회·관리 정책과 MB-010 지점 귀속. 확정된 단일 소속·공통 Catalog를 다시 미정으로 두지 않는다.

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): R01/R35; K35. [분석 색인](../analysis/README.md)

2026-10-12 사용자 확정(회원 소속 지점 변경 권한 질문의 1번): 동일 Organization 안에서 Member의 Home Branch는 Master Admin 또는 변경 요청 처리 시점 Member의 현재 Home Branch를 관리하는 Branch Admin이 변경할 수 있다. 받는 지점의 별도 승인 없이 처리한다. Master는 Organization 전체 범위이며 Branch Admin은 변경 전 현재 관리 Member만 대상으로 한다. 받는 지점 관리자라는 이유나 과거 소속·이전 변경자/지원 지정자·Pass Issued Branch·수업 Performed Branch 사실만으로 다른 현재 소속 Member를 이동시킬 수 없다. 관리자 권한 없는 Operator·Trainer는 수행할 수 없고 관리자 겸임자는 해당 관리 권한으로 판단한다(BR-OPS-007, PD-004, PR-002/030, MB-002, NFR-001).

기존 결정 적용: 변경된 Home Branch가 반영된 이후의 Member 관리 및 개별 지원 지정/해제는 각 요청의 현재 Home Branch와 관리 Scope를 따른다. 이전 지점 관리자는 이전 소속/처리자라는 사실만으로 Home Branch 기반 관리 권한을 유지하지 않는다. 기존 담당·개별 지원 조회 허용과 별도의 Pass 발급 지점/수업 수행 지점 기준 업무 등 독립적으로 인가되는 권한은 각각 기존 규칙을 적용한다. 이동 자체로 개별 지원 허용을 해제/재지정하지 않고, Pass의 Issued Branch·발급 조건·잔여/담당 정보, Trainer Home Branch와 과거 PT 기록/Performed Branch·확정 지급/정산을 자동 변경하지 않는다(BR-OPS-001/004/005).

기존 사용자 일관성 지시 적용(2026-10-11): Member 소속 변경은 관리 Scope에 영향을 주는 중요 변경이므로 기존 중요 행위/인가 변경의 이력·감사 원칙을 적용한다. 대상 Member·변경 전후 Home Branch·변경 Actor/권한·Branch Context·시점을 추적한다. 이번 권한 승인이 감사 저장 구조나 이동 적용 시점·예약/소급·변경 사유 입력/정정 정책을 확정한 것은 아니다(NFR-004, MB-002).

2026-10-12 사용자 확정(회원 소속 변경의 적용 시점 질문의 1번): v1의 Member Home Branch 변경은 저장 완료 즉시 적용만 지원한다. 변경이 성공한 시점부터 새 Home Branch가 현재 소속이 되며, 미래 적용일을 지정해 소속 변경을 예약하는 기능은 제공하지 않는다. 성공한 저장 이후 시작하는 후속 요청의 Home Branch 기반 관리 및 지원 지정/해제는 새 소속 기준으로 인가한다. 저장에 실패하면 변경 전 Home Branch를 유지한다. 기존 Master Organization 전체/변경 전 Member 현재 Home Branch 관리 Branch Admin 권한과 받는 지점 별도 승인 없음은 유지한다(BR-OPS-007, PD-004, PR-002/030, MB-002, NFR-001/004).

즉시 적용의 경계: 소속 변경 이력은 보존하며 기존 개별 지원 조회 허용을 해제/재지정하지 않는다. Pass Issued Branch·발급/잔여/담당 사실과 과거 PT/Performed Branch·확정 지급/정산은 소속 변경으로 자동 갱신하지 않는다. 이전 소속/처리자만으로 Home Branch 기반 관리 권한을 유지하지 않되, 담당/지원 조회나 발급/수행 지점 기준의 독립 업무 Scope는 각각 기존 규칙을 적용한다. 과거 소속 이력의 오류 정정·소급 여부/방식, 대상 Branch 상태 및 구체 저장/UoW·이미 처리 중인 요청과 동시 이동의 인가/실패 일관성은 후속이다. 이번 결정은 Member 이동 시점이며 Trainer 이동 시점이나 AuthSession 철회 구현/ADR-0004를 승인한 것은 아니다.

2026-10-12 사용자 확정(회원 이동 대상에 비활성 지점을 허용할지 질문의 1번): Member Home Branch의 이동 대상은 동일 Organization 안에서 운영 중인 활성 Branch만 허용한다. 비활성 Branch로의 이동은 허용하지 않으며 Master Admin과 Branch Admin에 동일하게 적용한다. Backend에서도 대상 Branch의 활성 여부를 검증하고 비활성 대상 요청은 거부한다. 거부 시 기존 Member Home Branch·지원 허용·Pass·과거 업무 이력은 유지한다(BR-OPS-007, PD-004, PR-002/030, MB-002/008, NFR-001).

대상 활성 조건의 범위: 기존 이동 Actor/현재 관리 Scope·받는 지점 별도 승인 없음·저장 완료 즉시 적용/미래 예약 미지원은 유지한다. 이번 결정은 새 이동의 대상 Branch 조건이며 Branch 비활성화 가능 조건, 비활성화 당시 기존 Member/Trainer/Pass 처리·자동 이동, 이미 비활성인 출발 지점의 업무 조건이나 재활성화/과거 조회 정책까지 확정한 것은 아니다. 과거 소속 이력 정정/소급·Branch 상태의 저장 표현, 이동과 비활성화의 경합·필수 감사/UoW/실패 계약은 후속이다(MB-002/008).

2026-10-12 사용자 확정(다른 지점에서 새 이용권 구매·발급 질문의 1번): Member는 같은 Organization의 Home Branch 밖 지점에서도 새 PT Pass를 구매·발급받을 수 있다. 수원 소속 회원이 강남에서 발급받으면 Member Home Branch는 수원으로 유지하고 새 Pass의 Issued Branch는 강남으로 기록한다. Member Home Branch와 Issued Branch가 같아야 한다는 제한을 두지 않는다. 기존 Member 식별자/소속·보유 Pass와 과거 PT/지급·정산 이력은 유지하며 타 지점 발급을 위해 Member를 지점별로 복제하거나 소속을 자동 이동하지 않는다(BR-OPS-001/010, PD-004/007, PR-002/003/030).

새 Pass 발급 지점의 사실과 Member 소속은 별개이며 이후 만료/해제·수동 횟수 조정은 해당 Pass Issued Branch, 담당 교체는 Member 현재 Home Branch의 기존 원칙을 따른다. 공통 상품/발급 조건·과거 이력/수업 보상 규칙과 일반 조회 범위는 유지한다. 발급은 Master Organization 전체/Branch Admin 자신의 단일 관리 Branch/Operator 부여된 허용 발급 Branch Scope로 확정됐으며 Trainer 단독은 불가하다(2026-10-12). 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·실제 발급 지점 선택/상태 조건·발급용 추가 공개 정보·Member 선택용 최소 식별 응답/계약 및 계약/UoW·동시성은 후속이다. 같은 Organization 전체 지점 Member의 이름·전화번호 일부 검색은 후속 2번 사용자 승인으로 해결됐다(BR-OPS-010).

2026-10-12 사용자 확정(새 이용권 발급 Actor 질문의 1번): 새 PT Pass 발급은 Master Admin·Branch Admin·Operator에게 각자의 허용된 실제 Issued Branch 범위에서 허용한다. Master는 Organization 전체, Branch Admin은 자신의 단일 관리 Branch, Operator는 부여된 허용 발급 Branch Scope에서 처리한다. 같은 Organization의 Member는 Home Branch가 발급 지점과 달라도 대상이 될 수 있으며 기존 Member/Home Branch를 유지하고 새 Pass에 실제 Issued Branch를 기록한다(BR-OPS-010, PD-004/007, PR-003/030).

권한 경계: Trainer 역할만으로는 새 Pass를 발급할 수 없다. Trainer를 겸하는 계정에 Master·Branch Admin·Operator의 발급 권한이 있으면 해당 역할의 독립적인 발급 Scope로 판단하며 별도 계정을 요구하지 않는다. Operator의 새 발급 권한은 공통 상품 생성/수정, 기존 Pass 수동 횟수 조정·만료/해제·담당 교체, Member 소속 이동, PT 정정/취소·Compensation Setting·Additional Performance·월 정산의 별도 권한을 추가하지 않는다. 발급 대상 식별을 타 지점 전체 Member 목록/전화번호·다른 Pass/PT/민감 보상 정보의 일반 조회 허용으로 확대하지 않는다. 기존 보상 설정 접근 제한과 Trainer의 담당/개별 지원 회원 조회는 그대로다.

2026-10-12 사용자 확정(발급용 타 지점 회원 검색 질문의 2번): Branch Admin·Operator는 자신의 허용된 실제 Issued Branch에서 새 PT Pass를 발급하기 위해 같은 Organization 전체 지점의 Member를 이름·전화번호 일부로 검색할 수 있다. 전화번호 전체 일치만을 요구하지 않으며 Member Home Branch가 Caller의 관리/발급 Branch와 다르다는 이유만으로 검색 후보에서 제외하지 않는다. Master의 기존 Organization 전체 범위는 유지한다. 검색은 기존 Member를 선택하여 실제 발급 지점의 새 Pass를 만드는 흐름이며 Member 소속 이동/복제나 기존 Pass·PT·지급·정산 변경을 수행하지 않는다(BR-OPS-010, PD-004/007/022, PR-002/003/030).

검색 인가/정보 공개 경계: 이 허용은 이용권 발급용 Member 검색의 후보 범위·검색 방식과 이름/전체 전화번호/현재 Member Home Branch 공개다. Backend는 매 검색/선택/발급 요청에서 현재 Caller의 발급 역할/Organization·허용 실제 Issued Branch와 대상 Member의 실제 Organization을 검증한다. 검색 Branch Context를 위조하거나 과거 검색 결과/선택 Member ID로 철회된 역할·Scope 또는 다른 Organization을 우회할 수 없다. 같은 전화번호/이름의 여러 Member는 별도 식별자로 구분하여 선택하며 번호만으로 병합하거나 첫 결과를 자동 선택하지 않는다. 이 세 항목의 읽기 허용이 회원 정보/전화번호 수정·일반 Member 상세·전체 무조건 목록/일괄 내보내기, 다른 개인정보/Pass/PT/보상 정보 열람 권한을 추가하지 않는다. Trainer 단독의 담당/개별 지원 Member 검색 및 기존 전체 전화번호 공개는 유지하고 발급 역할 겸임은 그 독립 발급 업무 Scope로 판단한다. 응답은 승인된 공개 범위 안에서 구성하며 Member 선택용 최소 식별 응답/계약과 추가 공개 정보는 후속이다. 실제 운영 연락처/검색어를 문서·일반 로그에 복사하지 않는다.

회원 식별의 기존 원칙 적용: 같은 전화번호/이름으로 여러 Member가 일치하면 별도 Member 식별자로 구분하여 발급할 대상을 선택한다. 번호 일치/첫 결과만으로 자동 병합·동일 회원 취급·소속 이동 또는 다른 Member 이력/권한 공유를 하지 않는다(BR-OPS-006). 잔여 0만으로 회원을 제외하지 않는 기존 조회 원칙은 유지하며 발급용 검색을 Trainer 전용 선택 제외 필터/담당 회원 집합으로 제한하지 않는다. 비활성 Member/Branch 등 나머지 대상 조건·검색어/빈 검색 처리·추가 공개 정보·최소 선택 응답/계약·선택/발급 일관성은 후속이다. 검색 자체는 업무 데이터를 변경하지 않으며 검색 성공만으로 발급 완료나 발급 이후 관리자 권한을 얻지 않는다.

2026-10-12 사용자 확정(발급용 검색 결과 표시 정보 질문의 1번): 새 PT Pass 발급용 Member 검색 결과에는 이름·전체 전화번호·소속 지점을 표시한다. 소속 지점은 해당 Member의 현재 Home Branch이며 Caller 관리 지점/Pass Issued Branch/수업 Performed Branch와 구별한다. 같은 Organization의 타 지점 회원 검색 결과에도 동일하게 적용하고 부분 마스킹된 번호만 표시하도록 제한하지 않는다. 기존 이름·전화번호 일부의 Organization 전체 지점 검색과 현재 발급 역할/실제 Issued Branch Scope 인가는 유지한다(BR-OPS-010, PD-004/007/022, PR-002/003/030, NFR-001/005).

전화번호 읽기 공개 범위만 확정한다. 회원/번호 수정·내보내기나 일반 회원 상세·다른 Pass/PT/보상 권한은 추가하지 않으며 별도 Member 구분/선택과 기존 소속·이력/발급 지점 원칙을 유지한다. 선택 응답/계약·추가 공개 정보/나머지 대상 조건은 후속이다(BR-OPS-006/010).

2026-10-12 사용자 확정(Trainer 소속 지점(Home Branch) 변경 권한 질문의 1번): Trainer의 Home Branch 변경은 Master Admin만 자신의 Organization 범위에서 수행한다. Branch Admin은 변경 전/후 지점 관리자 또는 해당 Trainer 계정 발급자여도 변경할 수 없다. Operator·Trainer 단독은 본인 포함 불가하며 관리자/Trainer 겸임도 현재 Master 권한이 있을 때만 해당 Organization Scope로 처리한다. Branch Admin의 자기 지점 Trainer 신규 로그인 계정 발급 권한(BR-OPS-012)은 유지하며 이를 소속 변경 권한으로 확대하지 않는다(BR-OPS-013, PD-004, PR-005/029/030, NFR-001/004, MB-001/004/005, ARCH-001).

기존 사용자 일관성 지시를 적용해 일반 이동은 저장 완료 후 새 현재 소속/관리 Scope 반영·실패 시 이전 상태 보존·소속 이력/감사를 따른다. 독립 관리자/Operator 역할·담당/지원 관계와 과거 수업 당시 소속·보상/정산은 보존한다. 대상 상태/과거 소속 이력 오류 정정·소급/확인 불가와 구체 계약은 BR-OPS-013 및 기존 게이트 후속이다.


<a id="pd-005"></a>
## PD-005

Question: 모바일·태블릿과 지원 브라우저의 범위는 무엇인가?

Status: CLOSED

Decision / approved direction: v1은 Desktop/Tablet/Smartphone에서 주요 정보와 Action을 실질적으로 사용할 수 있는 Responsive Web이다. 터치 조작을 고려하며 Desktop 화면 단순 축소는 충족 기준이 아니다. Trainer의 현장 Smartphone Session 등록은 주요 Use Case다.

Approval source: 2026-09-17 사용자 Multi-Branch 제품 방향 변경 지시. 충돌하는 이전 결정은 본 결정으로 대체하며 기존 비충돌 규칙은 유지한다.

Follow-up: ARCH-004; breakpoint·지원 브라우저·Frontend 기술은 후속 설계. Mobile App은 PD-026의 Future Direction. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): 04 화면; 10 전환; NEW-CANDIDATE. [분석 색인](../analysis/README.md)

<a id="pd-006"></a>
## PD-006

Question: 제안한 v1 범위와 출시 수용 기준을 승인할까?

Status: CLOSED

Decision / approved direction: 기존 핵심 PT 운영, Organization/Branch, Backend 권한 제한, Trainer 로그인/Session 등록, Responsive Web을 유지한다. Trainer별 월 고정 Base Salary와 Additional Performance를 v1에 포함한다. 가계부·락커·수동 매출·고정 거래 및 기존 Future Scope는 v1에서 제외한다.

Approval source: 2026-09-17 최신 사용자 지점 관계·추가실적·월 기본급·보상 설정 권한 확정. 충돌하는 이전 방향은 대체하며 비충돌 결정을 유지한다.

Follow-up: 기존 BR/ARCH/OPS 및 MB-001–008. Future Scope는 PD-003/025/026. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): 03 기능; 06 흐름. [분석 색인](../analysis/README.md)

<a id="pd-007"></a>
## PD-007

Question: 회원의 PT 이용정보를 어느 수준으로 관리할까?

Status: CLOSED

Decision / approved direction: 명시적인 PT Pass를 도입한다. 회원은 시간에 따라 여러 Pass 이력을 가지며 종료된 Pass도 보존한다. Pass는 PT Product, Assigned Trainer, Purchased/Remaining Sessions, Status, 생성/시작 정보, PT Session 이력을 설명하는 이용 단위다. 2026-10-10 사용자 결정(BR-011 CLOSED): 발급 당시 상품 가격·총횟수·Payment Type을 유지하며 Catalog 변경은 새 Pass부터 적용한다. 기존 Pass의 이후 수업도 발급 조건을 사용하고 상품 수정으로 잔여를 덮어쓰지 않는다.

2026-10-11 사용자 확정(이용권 타 지점 사용 사전 승인 질문의 1번): 같은 Organization의 사용 가능한 Pass는 발급 Branch 밖에서도 별도 사전 승인 없이 사용한다. 기존 사용 가능 조건·FIXED_AMOUNT 우선/FIFO·Issued Branch 보존을 유지하고 발급 지점 우선순위를 추가하지 않는다. 이용 허용과 Member 정보 조회/업무 Actor 권한은 구별한다(BR-OPS-001/BR-PAY-006, PR-003/030).

2026-10-12 사용자 확정(과거 수업의 이용권 범위 질문의 1번): 실제 수업 당시 이미 발급된 Pass만 해당 수업의 차감 후보로 삼는다. 수업 후 발급된 Pass는 늦은 등록 시점에 보유 중이어도 제외하며, 후보 안에서 기존 FIXED_AMOUNT 우선/FIFO와 사용 조건을 적용한다. 발급/시작 정보 의미·만료/종료/취소 이용 조건·발급 사실 정정/확인 상세는 후속이다(BR-PAY-006, PR-003, BR-001/002·ARCH-003).

2026-10-12 사용자 확정(유효기간 질문의 직접 답변): 이용권에 별도 만료일은 없으며 관리자 수동 만료를 지원한다. 시간 경과로 자동 만료하지 않는다. 수동 만료는 추가 이용 종료이며 과거 수업/정산 이력을 삭제·자동 취소하지 않는다. 기존 수동 운영 변경의 사유/이력 원칙을 동일 적용한다(사용자 일관성 지시). 지점별 관리 Scope·남은 횟수·정정/재개·만료 전 수업 지연 등록·상태 표현은 잔여 후속이다(BR-OPS-004, PR-003, BR-001/002/007·ARCH-003).

2026-10-12 사용자 확정(이용권 수동 만료의 관리 범위 질문의 1번): Master는 Organization 전체, Branch Admin은 자신의 현재 관리 Branch에서 발급한 Pass만 만료 처리한다. Member/Trainer Home Branch나 수업 Performed Branch는 만료 권한 기준이 아니다. 처리 시점의 검증된 관리 권한과 Issued Branch를 Backend에서 확인하고 범위 밖 직접 ID 요청을 차단한다. 기존 사유/이력과 과거 기록 보존을 유지하며 잔여/재개·과거 수업 연계는 후속이다(BR-OPS-004, PR-003/030).

2026-10-12 사용자 확정(수동 만료 시 잔여 처리 질문의 1번): 수동 만료 자체로 잔여를 변경하지 않고 사용만 차단한다. 잔여 5회는 만료 후에도 5회이며 0원 처리와 무관한 횟수 규칙이다. 잔여를 0으로 만들거나 소멸/수업 사용으로 차감하지 않는다. 양수 잔여만으로 자동 재개하지 않으며 기존 관리 권한/사유·이력 보존을 유지한다. 만료 해제/재개·과거 수업 연계와 다른 종료 사유의 잔여 처리는 후속이다(BR-OPS-004, PR-003, BR-001/002/007·ARCH-003).

2026-10-12 사용자 확정(잘못된 만료의 복구 질문의 1번): 같은 Pass의 수동 만료 해제를 허용한다. 기존 만료와 같은 Master Organization 전체/Branch Admin 처리 시점 현재 관리 Branch=Issued Branch 범위에서 사유/전후 상태·처리자/시점 이력과 감사를 남기고 직접 해제한다(기존 정책 동일 적용, 별도 승인 없음). 기존 만료 이력을 지우지 않고 잔여 횟수도 바꾸지 않는다. 만료/해제 시 잔여 5회는 계속 5회이며 기존 나머지 사용 조건을 충족하면 다시 사용할 수 있다. 잔여 0 등 다른 사용 불가 사유를 해제하지 않으며 새 Pass나 횟수를 부여하지 않는다. 과거 수업/지급/정산 보존을 유지하고 만료 전/중 수업 지연 등록·별도 취소 복원/조정 연계는 후속이다(BR-OPS-004, PR-003/030, BR-001/002/007·ARCH-003).

2026-10-12 사용자 확정(만료 전 수업의 늦은 등록 질문의 1번): 수동 만료 전에 실제 진행했고 당시 이용권이 사용 가능했다면, 현재 만료 상태여도 기존 PT 권한·정산·현재 잔여 조건을 충족하여 등록할 수 있다. 9월 20일 수업/9월 30일 만료/10월 5일 등록은 만료 해제를 먼저 요구하지 않는다. 해당 Pass를 조건 충족 후보에 포함한 뒤 FIXED_AMOUNT 우선/FIFO로 선택하고 현재 잔여에서 1회 차감한다(만료/5회→만료/4회). 현재 만료 상태·이력과 기존 기록을 보존하며 만료 해제 권한을 추가하지 않는다. 미확정 월/확정 월 해제 후 반영·재확정, 기록 생성 시점 신규 일반 지급·수업 당시 소속 기준 구분은 유지한다. 다른 종료 사유·시점/이력 사실 판정 및 취소 복원/조정 연계는 후속이다(BR-PAY-006, BR-OPS-003/004, PR-003/008/029).

Approval source: 2026-09-15 승인 및 2026-09-16 BR-PAY-001–008 정정 승인. 상세 TODO만 후속.

Follow-up: 2026-09-16 BR-PAY-006에 따라 복수 사용 가능한 Pass의 FIXED_AMOUNT 우선 차감을 지원한다. 동일 Payment Type FIFO도 확정이다. BR-001/002, ARCH-003은 상태·횟수·사용 조건 등 상세만 검토. [확정 규칙](business-rules.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): F04; R04/R05. [분석 색인](../analysis/README.md)

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

조정 사유·전후 잔여/증감량·Actor/Role/Branch Context·시점 이력/감사와 기존 범위 내 직접 처리 원칙을 적용한다(BR-OPS-009). 수량/상태 범위와 저장/UoW·동시성은 BR-002·ARCH-003/001 후속이며 원래 발급 상품 조건·담당/소속·과거 PT/지급/정산을 자동 변경하지 않는다.

2026-10-12 사용자 확정(다른 지점에서 새 이용권 구매·발급 질문의 1번): Member는 같은 Organization의 Home Branch 밖 지점에서도 새 PT Pass를 구매·발급받을 수 있다. 수원 소속 회원이 강남에서 발급받으면 Member Home Branch는 수원으로 유지하고 새 Pass의 Issued Branch는 강남으로 기록한다. Member Home Branch와 Issued Branch가 같아야 한다는 제한을 두지 않는다. 기존 Member 식별자/소속·보유 Pass와 과거 PT/지급·정산 이력은 유지하며 타 지점 발급을 위해 Member를 지점별로 복제하거나 소속을 자동 이동하지 않는다(BR-OPS-001/010, PD-004/007, PR-002/003/030).

새 Pass 발급 지점의 사실과 Member 소속은 별개이며 이후 만료/해제·수동 횟수 조정은 해당 Pass Issued Branch, 담당 교체는 Member 현재 Home Branch의 기존 원칙을 따른다. 공통 상품/발급 조건·과거 이력/수업 보상 규칙과 일반 조회 범위는 유지한다. 발급은 Master Organization 전체/Branch Admin 자신의 단일 관리 Branch/Operator 부여된 허용 발급 Branch Scope로 확정됐으며 Trainer 단독은 불가하다(2026-10-12). 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·실제 발급 지점 선택/상태 조건·발급용 추가 공개 정보·Member 선택용 최소 식별 응답/계약 및 계약/UoW·동시성은 후속이다. 같은 Organization 전체 지점 Member의 이름·전화번호 일부 검색은 후속 2번 사용자 승인으로 해결됐다(BR-OPS-010).

2026-10-12 사용자 확정(새 이용권 발급 Actor 질문의 1번): 새 PT Pass 발급은 Master Admin·Branch Admin·Operator에게 각자의 허용된 실제 Issued Branch 범위에서 허용한다. Master는 Organization 전체, Branch Admin은 자신의 단일 관리 Branch, Operator는 부여된 허용 발급 Branch Scope에서 처리한다. 같은 Organization의 Member는 Home Branch가 발급 지점과 달라도 대상이 될 수 있으며 기존 Member/Home Branch를 유지하고 새 Pass에 실제 Issued Branch를 기록한다(BR-OPS-010, PD-004/007, PR-003/030).

권한 경계: Trainer 역할만으로는 새 Pass를 발급할 수 없다. Trainer를 겸하는 계정에 Master·Branch Admin·Operator의 발급 권한이 있으면 해당 역할의 독립적인 발급 Scope로 판단하며 별도 계정을 요구하지 않는다. Operator의 새 발급 권한은 공통 상품 생성/수정, 기존 Pass 수동 횟수 조정·만료/해제·담당 교체, Member 소속 이동, PT 정정/취소·Compensation Setting·Additional Performance·월 정산의 별도 권한을 추가하지 않는다. 발급 대상 식별을 타 지점 전체 Member 목록/전화번호·다른 Pass/PT/민감 보상 정보의 일반 조회 허용으로 확대하지 않는다. 기존 보상 설정 접근 제한과 Trainer의 담당/개별 지원 회원 조회는 그대로다.

2026-10-12 사용자 확정(발급용 타 지점 회원 검색 질문의 2번): Branch Admin·Operator는 자신의 허용된 실제 Issued Branch에서 새 PT Pass를 발급하기 위해 같은 Organization 전체 지점의 Member를 이름·전화번호 일부로 검색할 수 있다. 전화번호 전체 일치만을 요구하지 않으며 Member Home Branch가 Caller의 관리/발급 Branch와 다르다는 이유만으로 검색 후보에서 제외하지 않는다. Master의 기존 Organization 전체 범위는 유지한다. 검색은 기존 Member를 선택하여 실제 발급 지점의 새 Pass를 만드는 흐름이며 Member 소속 이동/복제나 기존 Pass·PT·지급·정산 변경을 수행하지 않는다(BR-OPS-010, PD-004/007/022, PR-002/003/030).

검색 인가/정보 공개 경계: 이 허용은 이용권 발급용 Member 검색의 후보 범위·검색 방식과 이름/전체 전화번호/현재 Member Home Branch 공개다. Backend는 매 검색/선택/발급 요청에서 현재 Caller의 발급 역할/Organization·허용 실제 Issued Branch와 대상 Member의 실제 Organization을 검증한다. 검색 Branch Context를 위조하거나 과거 검색 결과/선택 Member ID로 철회된 역할·Scope 또는 다른 Organization을 우회할 수 없다. 같은 전화번호/이름의 여러 Member는 별도 식별자로 구분하여 선택하며 번호만으로 병합하거나 첫 결과를 자동 선택하지 않는다. 이 세 항목의 읽기 허용이 회원 정보/전화번호 수정·일반 Member 상세·전체 무조건 목록/일괄 내보내기, 다른 개인정보/Pass/PT/보상 정보 열람 권한을 추가하지 않는다. Trainer 단독의 담당/개별 지원 Member 검색 및 기존 전체 전화번호 공개는 유지하고 발급 역할 겸임은 그 독립 발급 업무 Scope로 판단한다. 응답은 승인된 공개 범위 안에서 구성하며 Member 선택용 최소 식별 응답/계약과 추가 공개 정보는 후속이다. 실제 운영 연락처/검색어를 문서·일반 로그에 복사하지 않는다.

회원 식별의 기존 원칙 적용: 같은 전화번호/이름으로 여러 Member가 일치하면 별도 Member 식별자로 구분하여 발급할 대상을 선택한다. 번호 일치/첫 결과만으로 자동 병합·동일 회원 취급·소속 이동 또는 다른 Member 이력/권한 공유를 하지 않는다(BR-OPS-006). 잔여 0만으로 회원을 제외하지 않는 기존 조회 원칙은 유지하며 발급용 검색을 Trainer 전용 선택 제외 필터/담당 회원 집합으로 제한하지 않는다. 비활성 Member/Branch 등 나머지 대상 조건·검색어/빈 검색 처리·추가 공개 정보·최소 선택 응답/계약·선택/발급 일관성은 후속이다. 검색 자체는 업무 데이터를 변경하지 않으며 검색 성공만으로 발급 완료나 발급 이후 관리자 권한을 얻지 않는다.

2026-10-12 사용자 확정(발급용 검색 결과 표시 정보 질문의 1번): 새 PT Pass 발급용 Member 검색 결과에는 이름·전체 전화번호·소속 지점을 표시한다. 소속 지점은 해당 Member의 현재 Home Branch이며 Caller 관리 지점/Pass Issued Branch/수업 Performed Branch와 구별한다. 같은 Organization의 타 지점 회원 검색 결과에도 동일하게 적용하고 부분 마스킹된 번호만 표시하도록 제한하지 않는다. 기존 이름·전화번호 일부의 Organization 전체 지점 검색과 현재 발급 역할/실제 Issued Branch Scope 인가는 유지한다(BR-OPS-010, PD-004/007/022, PR-002/003/030, NFR-001/005).

전화번호 읽기 공개 범위만 확정한다. 회원/번호 수정·내보내기나 일반 회원 상세·다른 Pass/PT/보상 권한은 추가하지 않으며 별도 Member 구분/선택과 기존 소속·이력/발급 지점 원칙을 유지한다. 선택 응답/계약·추가 공개 정보/나머지 대상 조건은 후속이다(BR-OPS-006/010).

2026-10-12 사용자 확정(Operator 업무 허용 지점 수 질문의 1번): v1 Operator 역할의 업무 허용 Branch는 한 시점에 하나만 지정한다. Operator는 그 지정된 단일 Branch에서 명시적으로 허용된 업무를 수행하며 같은 계정의 Operator 권한을 여러 Branch에 동시 부여하지 않는다. Branch당 Operator 한 명이라는 1:1 인원 제한을 추가하지 않으며 하나의 Branch에 여러 Operator가 있을 수 있다. 이 결정은 Operator 역할의 업무 Scope이며 기존에 허용된 겸임 역할의 독립적인 관리/PT 권한이나 Trainer Home Branch를 바꾸지 않는다(BR-OPS-011, PD-001/007, PR-001/003/030, ARCH-001, MB-004).

기존 발급/검색 규칙 유지: Operator의 새 Pass 발급은 자신의 지정된 단일 Branch를 실제 Issued Branch로 사용한다. 그 발급 업무에서는 같은 Organization 전체 지점 Member를 이름·전화번호 일부로 검색하고 결과의 이름·전체 전화번호·현재 Member Home Branch를 조회/선택할 수 있다(BR-OPS-010). Member Home Branch가 Operator 업무 Branch와 다르다고 검색/발급을 거부하거나 회원 소속을 자동 이동하지 않는다. 전체 지점 Member 검색이 다른 Branch의 Pass 발급이나 일반 회원 상세/다른 Pass/PT·보상/수정·일괄 내보내기 권한을 부여하지 않는다. 기존 Master 전용 공통 상품 변경 및 관리자 전용 Pass 수동 조정·만료/해제·담당 교체/보상 업무 제한은 유지한다.

남은 결정: 새 Operator 발급/최초 Branch 지정 Actor는 Master Organization 전체/Branch Admin 자기 단일 Branch, 기존 Operator 업무 Branch 변경 Actor는 Master Organization 범위 전용으로 해결됐다. 변경은 기존 저장 후 현재 Scope 반영/실패 보존·감사 원칙을 적용한다. 발급 절차·기존 계정 역할 추가/변경·Operator 지점 변경의 대상 Branch/계정 상태·세부 절차/감사 계약 및 나머지 운영 행위 권한은 MB-004·ARCH-001/002 후속이다. 한 계정의 Operator 동시 허용 지점 수나 신규 발급/지점 변경 Actor를 다시 OPEN으로 두지 않는다. 실제 발급 대상·초기 조건/선택 응답·역할/Scope 저장·Caller/인가 계약·실패/재시도/경합은 관련 Product/Architecture 후속이다. IAM-001 S1에 Operator 구현을 추가하거나 기존 PROPOSED 인증/모듈/저장 설계를 승인한 것은 아니다.

2026-10-12 사용자 확정(잔여가 남은 담당 이용권이 있는 Trainer의 비활성화 질문의 1번): 잔여가 남은 담당 PT Pass가 있어도 Trainer 비활성화를 허용하며 기존 Assigned Trainer 정보는 유지한다. 비활성화 전에 모든 Pass를 다른 Trainer에게 교체하도록 요구하지 않고 자동 담당 해제/재배정도 하지 않는다. 이후 필요할 때 권한 있는 관리자가 BR-OPS-008의 기존 조건/Scope로 담당을 교체한다(BR-OPS-014, PD-007/011, PR-003/005, NFR-001/004, ARCH-001/002, MB-001/003/005, BR-001).

기존 잔여/발급 조건·과거 이력 보존과 비활성 Trainer 접근 차단을 함께 적용한다. 후속 담당 교체 Actor는 Member 현재 Home Branch이며 Trainer 비활성화 Actor의 Trainer Home Branch로 대체하지 않는다. 개별 지원·재활성화와 기술 상세는 기존 게이트를 따른다.

2026-10-12 사용자 확정(담당 Trainer를 새로 지정할 때의 조건 질문의 1번): PT Pass의 담당 Trainer를 새로 지정할 때는 실제 활성 Trainer만 허용한다. 기존 Pass의 담당 교체 및 허용된 새 Pass 발급 흐름에서 담당을 최초 지정하는 경우 모두 적용하며 비활성 Trainer를 미리 배정하지 않는다(BR-OPS-008/014, PD-007, PR-003/005/029/030, NFR-001, ARCH-001, MB-001/003/005, BR-001).

이번에 새 대상의 활성 필요조건만 해결됐다. 이미 담당인 Trainer가 나중에 비활성화되면 기존 담당을 유지/접근 차단하는 정책과 구분한다. 최초 지정 필수/미지정·나머지 계정/Branch/Pass 상태 조합과 재활성화·비활성 전 수업 누락 등록/구체 계약·경합은 후속이며 현재 담당 조건으로 과거 수업 수행자를 바꾸지 않는다.

<a id="pd-008"></a>
## PD-008

Question: 진행 기록의 날짜·횟수 단위와 중복 판단을 어떻게 정할까?

Status: CLOSED

Decision / approved direction: 실제 진행 날짜별 개별 PT Session을 원본으로 기록한다. 월 단위 여러 회 합계를 원본으로 저장하지 않는다. 일반 Session Payment 적용 대상은 정상 Session 등록 시 지급액을 계산·확정하며 월 정산의 Session 구성은 유효 확정 결과 집계다. 타 지점 보상 전체는 MB-009에 따라 추가실적으로 처리한다. 지원 수업은 진행 기록·차감을 먼저 완료하고 관리자의 건별 수동 금액 저장 시 보상 확정하며 미입력은 확정된 0원이 아니다. 전체 월 정산은 PD-012, 타 지점 지급 구성은 MB-009를 따른다.

2026-10-11 사용자 확정(같은 회원의 하루 두 번 실제 PT 수업 질문의 1번): 실제로 별개인 수업은 같은 날짜여도 각각 기록하고 각각 1회씩 차감한다. 회원당 하루 1회 제한이나 날짜만으로 합치기/중복 거부를 하지 않는다. 같은 수업의 재전송/중복 저장은 별개로 방지하며 시간대·소급 범위·월 경계·구체 요청 식별 방식은 후속이다(BR-OPS-002, PR-008, BR-008).

2026-10-11 사용자 확정(Trainer의 과거 수업 등록 범위 질문의 1번): 해당 Trainer/실제 진행 월 정산이 미확정이면 기존 허용 PT 업무 범위에서 과거 수업도 직접 등록한다. 당월 또는 최근 N일만으로 제한하거나 월 변경 때문에 관리자 대행을 요구하지 않는다. 일반 지급 설정은 신규 기록 생성 시점, 일반/지원 구분은 실제 수업 당시 소속 기준을 유지한다. 확정 월 해제/재확정 권한을 Trainer에게 추가하지 않는다(BR-OPS-003, PR-008, BR-008).

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: BR-008, UX-001; 일괄 입력 편의와 원본 단위 구분. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): F18/F19; R13/R20/R21. [분석 색인](../analysis/README.md)

2026-10-12 사용자 확정(담당 교체 전 수업의 누락 등록 질문의 1번): A가 담당으로 실제 수업을 진행한 뒤 담당이 B로 바뀌어도 A는 교체 전 본인 수업을 직접 늦게 등록할 수 있다. 예: 9월 5일 A 수업 → 9월 6일 B로 담당 교체 → 9월 7일 A 누락 등록. 실제 수업 당시 A의 담당 관계와 본인 수행 사실, 현재 검증된 Caller/Trainer 연결·Organization 및 기존 Pass/정산 조건을 확인한다. 현재 담당이 B라는 이유만으로 관리자 대행이나 A 재배정을 요구하지 않는다. 이 허용만으로 A의 해당 회원 목록/상세·전화번호/다른 Pass·다른 Trainer 기록 조회 권한을 복원하지 않는다(BR-OPS-003/005/008, PD-008, PR-008/029/030).

등록/차감·수행 Trainer A 기준 지급/월 조건과 회원 조회 비복원 경계는 BR-OPS-003을 따른다. 과거 사실 확인 불가/정정·최소 식별/응답 및 계약/UoW·동시성은 후속이다.

2026-10-12 사용자 확정(비활성화 전 진행했지만 누락된 PT 수업 등록 질문의 1번): Trainer 비활성화 전에 실제로 수행한 미등록 PT 수업은 관리자가 대행 등록하는 경로를 허용한다. 대상 Trainer의 비활성 상태를 유지하며 잠시 재활성화/본인 로그인·담당 재배정을 선행 요구하지 않는다. 실제 수행 Trainer·실제 수업일과 기존 Pass 잔여/정산 조건을 그대로 적용한다(BR-OPS-015, PD-008/011, PR-008/029/030, BR-OPS-003/008/014, BR-PAY-006/011/012).

대행 등록은 과거 실제 수행자 참조이고 활성 대상만 가능한 새 담당 지정과 별개다. 비활성 상태/현재 담당·기존 잔여/해당 월 조건과 생성 시점 실제 수행 Trainer 보상 입력을 유지하고 대행 관리자/당시 권한은 별도 감사한다. 대행 인가의 현재 사실 검증·역사 사실/시점 판정/최소 선택 정보·저장/경합은 후속이다. 비활성 Trainer 본인 접근이나 보상 설정/추가실적/정산의 별도 권한을 추가하지 않는다.

2026-10-12 사용자 확정(비활성화 전 누락 수업 대행 등록의 Branch Admin 기준 질문 1번): Master Admin은 자신의 Organization 전체, Branch Admin은 처리 시점 현재 관리 Branch가 실제 수업의 Performed Branch인 경우에만 대행 등록할 수 있다. Trainer 현재 Home Branch가 다른 지점이어도 실제 수업이 자신의 관리 지점에서 진행됐다면 허용한다. Trainer Home Branch·Member Home Branch·Pass Issued Branch 또는 과거 관리자 Scope만으로 대행 권한을 얻지 않는다(BR-OPS-015).

<a id="pd-009"></a>
## PD-009

Question: 지급단가·서비스 단가·반올림·공제 의미를 어떻게 정할까?

Status: CLOSED

Decision / approved direction: Product는 RATE/FIXED_AMOUNT 방식을 결정한다. Trainer Compensation Setting은 Product와 독립적인 Trainer별 Rate, Fixed Amount, 월 고정 Base Salary다. Product별 Trainer 지급 값은 도입하지 않는다. 일반 RATE는 해당 상품 회당 단가 × Trainer Rate 결과를 Session별 1,000원 단위 올림하며 FIXED_AMOUNT와 서비스 상품은 Trainer Fixed Amount 그대로다. Rate / Fixed Amount / Base Salary 세 항목의 조회·설정·변경은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 단일 Branch를 Home Branch로 가진 Trainer에게만 허용한다. 관리자와 Trainer를 겸하는 계정은 관리 권한 범위 안이면 본인의 세 항목도 조회·변경할 수 있다. Master Admin은 본인 포함 허용하며, Branch Admin은 본인 Trainer의 Home Branch가 관리 Branch일 때 본인도 허용한다. 관리자 권한이 없는 Operator·Trainer 계정은 본인 포함 모든 Trainer 설정 조회·변경이 불가하다. 타 지점 지원 수업은 보상 설정 접근 권한을 부여하지 않는다. Backend에서 대상 Trainer의 Home Branch를 검증하며 직접 ID 요청과 감사·정산 등 우회 경로에도 제한을 적용한다. 모든 보상 설정 변경(최초 설정 포함)에 대상 Trainer, 변경 항목, 변경 전 값, 변경 후 값, 변경 Actor, Actor의 권한 및 Branch Context, 변경 시점을 추적한다. 별도 Master Admin 승인 없이 변경 가능하며 변경 요청→승인 대기→승인→반영 절차를 추가하지 않는다. 이 결정은 추가실적 승인이나 월 정산 마감/확정 절차를 면제하지 않는다. 일반 Session Payment의 Rate/Fixed Amount는 관리자 저장 완료 이후 새로 등록되는 Session부터 적용하고 정상 등록 시 지급액을 계산·확정한다. 타 지점 지원 수업은 보상 금액 없이도 허용된 PT 진행 기록과 Pass 차감을 먼저 완료한다. 권한 있는 관리자가 나중에 수업 건별 금액을 저장할 때 해당 Additional Performance 보상을 확정한다. 금액 미입력은 확정된 0원과 구분하고 누락 건을 추적할 수 있어야 한다. 해당 Trainer의 해당 월 정산 대상 지원 수업에 금액 미입력 건이 하나라도 있으면 그 Trainer·월 정산을 확정할 수 없다. 타 지점 지원 수업 보상은 권한 있는 관리자가 사유를 기록하면 0원으로 명시적으로 확정할 수 있다. 사유 없는 0원 입력은 보상 확정이 불가하다. 사유를 남기고 확정한 0원은 금액 미입력이 아니므로 그 건으로 월 정산 확정을 차단하지 않는다. 다른 미입력 건이 남으면 기존 차단 조건을 유지한다. 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin에게 Organization 전체, Branch Admin에게 대상 Trainer Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안의 본인 건도 허용하고 변경 이력을 남긴다. 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin·Branch Admin 모두 관리 범위 안에서 본인 건을 포함해 별도 승인 없이 저장 성공 즉시 반영한다. Master나 다른 관리자의 승인 대기를 두지 않으며 권한 검증과 변경 이력을 유지한다. 월 정산 확정 전 지원 수업 보상 금액의 모든 수정에는 변경 사유가 필수다. 양수 간 변경·0원에서 양수로 변경·양수에서 0원으로 변경 모두 적용하며, 사유 없이는 금액을 수정할 수 없다. 변경 전후 금액·변경 사유·수정자·수정 시점을 이력으로 남긴다. 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer의 지원 수업 보상 정정을 위해 월 정산을 확정 해제·재확정할 때는 Master의 별도 승인을 두지 않는다. Master 승인 대기 단계 없이 관리 범위 안에서 직접 처리하며 이전 확정본과 해제·재확정 이력 및 감사를 유지한다. 지원 수업 보상 정정의 월 정산 확정 해제에는 사유가 필수이며, 사유 없이 해제할 수 없다. 사유·해제자·시점을 이력으로 남긴다. 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 남은 정정·취소 절차는 BR-009/013 등 관련 OPEN을 따른다. 미입력 건의 추적 표현·정정 연동·정정/취소는 BR-013 OPEN이다. 과거 확정 지급액은 재계산하지 않는다. 기본급 적용 시작 월의 관리자 지정·미확정 과거 월 지정 허용·수동 지정 없는 기존 미확정 정산의 기본급·합계 자동 반영은 확정했고 미리 등록할 수 있는 미래 적용 시작 월의 범위 등 남은 상세는 BR-012 OPEN이다. 타 지점 수업 지급 구성은 해당 수업의 보상 전체를 Additional Performance로 처리하는 방식으로 확정했다(MB-009 CLOSED, 2026-10-10).

Approval source: 2026-09-17 최신 사용자 지점 관계·추가실적·월 기본급·보상 설정 권한 확정. 충돌하는 이전 방향은 대체하며 비충돌 결정을 유지한다.

추가 사용자 확정(2026-10-10): Base Salary 변경 시 관리자가 적용 시작 월을 지정한다. 기존 보상 설정 권한·별도 승인 없음·필수 감사를 유지하며 과거 확정 월 정산을 자동 변경하지 않는다. 추가 후속 사용자 확정으로 변경이 적용되는 수동 지정 없는 기존 미확정 정산의 기본급·합계는 별도의 반영 작업 없이 자동 갱신한다. 이미 확정된 정산은 자동 변경하지 않으며 정산 자동 확정도 하지 않는다. 추가 후속 사용자 확정으로 아직 확정하지 않은 과거 월도 적용 시작 월로 지정할 수 있다. 확정된 월의 기본급 오류는 해당 월 확정 해제·기본급 정정·동일 월 재확정으로 처리하며 이전 확정본을 보존한다. 기본급 오류 정정의 확정 해제·재확정은 Master Admin에게 Organization 전체, Branch Admin에게 각 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 처리한다. 확정된 월의 기본급 오류 정정에서 확정 해제와 해당 월 기본급 수정 모두 사유가 필수다. Master Admin·Branch Admin 및 관리 범위 안 본인 건에 동일하게 적용한다. 해제 사유·해제자·시점과 변경 전후 기본급·수정 사유·수정자·시점을 이력으로 남긴다. 기본급 오류 정정은 대상 Trainer의 해당 월 정산에만 적용하며 현재·미래 기본급 설정과 다른 월 정산은 유지한다. 지속적인 기본급 변경은 별도로 적용 시작 월을 지정하는 기존 흐름을 따른다. 미리 등록할 수 있는 미래 적용 시작 월의 범위 등 남은 정책은 BR-012 OPEN이다.

Follow-up: BR-003/004/005/006은 CLOSED. 입력값 BR-010, 정정 BR-007, 기본급 BR-012 및 추가실적 BR-013은 후속 OPEN. Product 변경은 기존 Pass의 발급 당시 조건 유지로 BR-011 CLOSED이며 Trainer 설정 적용 시점은 유지한다. 타 지점 보상 구성 MB-009는 CLOSED. [확정 규칙](business-rules.md), [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): R09/R10/R14/R15; K04/K24/K25. [분석 색인](../analysis/README.md)

추가 사용자 확정(2026-10-10, 입사·퇴사·휴직 월 기본급 질문의 1번 답변): 입사·퇴사·휴직이 있는 달의 적용 기본급은 관리자가 해당 Trainer·월의 금액을 직접 지정한다. 예를 들어 월 기본급 설정이 2,500,000원이어도 해당 월만 1,500,000원을 적용할 수 있으며, 이 지정으로 현재·미래 기본급 설정과 다른 월 정산은 변경하지 않는다. 월별로 수동 지정한 기본급은 이후 일반 기본급 설정이 변경되어도 유지한다. 일반 설정 변경의 미확정 정산 자동 반영은 수동 지정이 없는 월에 적용하며, 수동 지정 월의 금액을 바꾸려면 관리자가 해당 월 금액을 직접 수정한다. 미확정 월의 기본급을 최초 수동 지정하거나 다시 수정할 때 모두 사유가 필수다. 사유가 없는 요청은 거부하고 요청 직전의 수동 지정 여부·적용 금액·월 합계를 유지한다. 대상 Trainer·월, 지정/수정 전후 금액·사유·처리자·처리 시점을 이력으로 남긴다. 미확정 월 기본급의 최초 수동 지정·수정은 Master Admin의 Organization 전체, Branch Admin의 각 처리 시점 대상 Trainer 현재 Home Branch가 관리 Branch와 일치하는 범위에서 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 직접 처리한다. 추가 사용자 확정(2026-10-11): 해당 월 기본급은 권한 있는 관리자가 사유를 남기면 0원으로 명시적으로 수동 지정할 수 있다. 수동 지정한 0원은 미입력과 구분하며, 미입력이나 누락된 일반 설정을 자동으로 0원으로 대체하지 않는다. 해당 월 기본급에만 적용하고 다른 유효 지급·추가실적은 기존 규칙대로 합산한다. 미리 등록할 수 있는 미래 적용 시작 월의 범위와 월별 수동 지정 금액의 나머지 입력 제약 등은 BR-012/BR-010 OPEN이다.

추가 사용자 명확화(2026-10-11): 일반 Base Salary 설정은 관리자가 지정한 적용 시작 월부터 다음 기본급 변경의 적용 시작 월 전까지 매월 계속 적용한다. 적용 종료 월을 지정하거나 같은 금액을 매월 다시 등록할 필요는 없다. 특정 월 수동 지정은 해당 월에만 적용하는 기존 예외를 따른다. 미래 시작 월로 변경을 얼마나 미리 등록할 수 있는지는 이번 답변으로 확정하지 않는다.

<a id="pd-010"></a>
## PD-010

Question: 기록 정정·삭제·횟수 복원은 누가 어떤 조건으로 할까?

Status: CLOSED

Decision / approved direction: Master Admin은 Organization 전체, Branch Admin은 실제 Performed Branch가 관리 Branch인 기록을 허용된 조건 안에서 정정/취소한다. Performed Branch 자체 오류 정정은 Master Admin 전용이며 Branch Admin은 해당 지점이 관리 Branch여도 정정할 수 없다(2026-10-11 사용자 확정). Operator 역할만으로는 정정/취소할 수 없다(2026-10-11 사용자 확정). Trainer 역할만으로는 본인 PT 진행 기록도 정산 확정 전후 모두 정정/취소할 수 없다(2026-10-11 사용자 확정). 관리자 겸임자는 해당 업무의 별도 관리 권한·Branch Scope로 판단한다. Pass 잔여와 정산 데이터의 일관성이 반드시 유지되어야 하며 단순 행 삭제로 처리하지 않는다.

2026-10-11 사용자 확정(Trainer 본인 PT 진행 기록 정정·취소 권한 질문의 1번): Trainer 역할만으로는 본인이 등록하거나 수행한 PT 진행 기록도 정정·취소할 수 없다. 월 정산 확정 전후 모두 적용하며 직접 ID 요청으로도 우회할 수 없다. 허용된 관리 담당자가 해당 업무의 별도 권한·Branch Scope 안에서 처리한다. 관리자·Trainer 겸임자는 Trainer 역할의 본인 권한이 아니라 해당 업무의 관리 권한으로 판단한다. 이 결정으로 다른 역할의 정정 권한이나 Home/Performed Branch 기준을 자동 확정하지 않는다. Trainer의 허용된 PT 진행 등록·본인 내역 조회와 기존 보상 설정/추가실적 권한은 유지한다. 정정 항목·기간·취소 및 지급/정산 연동 상세는 BR-007/009, 관리 Scope와 교차 업무 조건은 ARCH-001/MB-005의 잔여 OPEN이다.

2026-10-11 사용자 확정(타 지점 PT 진행 기록 정정·취소 담당 지점 질문의 1번): Master Admin은 Organization 전체, Branch Admin은 대상 기록의 실제 Performed Branch가 자신의 관리 Branch인 경우 PT 진행 기록을 정정·취소한다. 수원 소속 Trainer의 강남 수업 기록은 강남 Branch Admin이 담당하며, 수원 Branch Admin에게 Trainer Home Branch만을 근거로 해당 기록의 정정 권한을 부여하지 않는다. Trainer 이동만으로 기록의 담당 지점이 바뀌지 않는다. Backend에서 수업 사실·현재 관리 권한을 검증하며 요청의 Branch ID를 그대로 신뢰하지 않는다. 추가실적 금액 입력·보상 설정·Trainer 전체 월 정산의 기존 Home Branch 권한은 유지하고 수행 지점의 기록 권한으로 확대하지 않는다. Trainer 역할의 정정·취소 금지는 유지하며 관리자 겸임자는 해당 관리 권한으로 판단한다. Operator의 정정 권한·Performed Branch 자체 오류 정정·정산 확정 후 서로 다른 지점 담당자의 처리 순서·취소에 따른 지급/추가실적 연동은 잔여 OPEN이다.

2026-10-11 사용자 확정(확정 월의 타 지점 수업 취소 처리 질문의 “11”을 1번 답변으로 해석): 이미 월 정산이 확정된 타 지점 PT 수업을 취소할 때 기존 권한을 유지한다. 대상 Trainer·월 정산의 확정 해제 → 해당 PT 진행 기록 취소 → 같은 Trainer·월 정산 재확정 순서로 처리한다. Branch Admin은 해제/재확정 각 처리 시점 Trainer의 현재 Home Branch가 관리 Branch인 경우 정산을 담당하고, 기록 취소는 해당 수업의 실제 Performed Branch 관리자가 담당한다. 예를 들어 현재 수원 소속 Trainer의 강남 수업이면 수원 Branch Admin이 해당 월 정산을 해제하고 강남 Branch Admin이 기록을 취소한 뒤 수원 Branch Admin이 재확정한다. 두 지점 담당자가 각자의 권한으로 협업하며 Master Admin은 Organization 범위 안에서 전체 과정을 처리할 수 있다. 수행 지점 관리자에게 다른 소속 Trainer의 전체 월 정산이나 추가실적 금액 입력 권한을 부여하지 않는다. 이전 확정본·변경 이력 보존, 기존 해제 사유/감사와 재확정 조건은 유지한다. 현재 설정으로 다른 과거 지급/적용 기본급을 재계산하거나 취소 저장만으로 자동 재확정하지 않는다. 이 결정은 위 취소의 처리 순서와 담당 권한에 한정한다. Operator 권한·취소 시 지급/연계 추가실적의 유효 결과·잔여 복원 예외·정정 항목/기간·Performed Branch 자체 오류 정정 및 각 단계 계약/실패·재시도/경합은 잔여 OPEN 또는 PROPOSED다.

2026-10-11 사용자 확정(Operator의 PT 진행 기록 정정·취소 권한 질문의 1번): Operator 역할만으로는 PT 진행 기록을 정정·취소할 수 없다. 정산 미확정/확정 상태 모두 적용한다. Master Admin은 Organization 전체, Branch Admin은 해당 기록의 실제 Performed Branch 범위에서 담당한다. Trainer 역할의 정정·취소 금지와 관리자 겸임자의 해당 관리 권한 판단은 유지한다. Operator의 기존 허용 업무가 정정 권한을 부여하지 않으며 Branch Scope 부여·다른 운영 업무의 상세는 MB-004/ARCH-001 OPEN이다.

2026-10-11 사용자 확정: 허용된 PT 진행 기록 취소는 그 수업 보상의 추가실적 자동 무효 처리를 동반한다. 유효 월 정산/지점 비용에서 제외하되 기존 금액·이력을 보존하고 다른 추가실적은 유지한다. 기존 기록 취소 권한과 Home Branch 기준 금액 입력/전체 정산 권한은 구별하며 확정 월의 기존 해제 → 취소 → 같은 월 재확정 순서를 따른다. 상세 근거는 BR-PAY-015/PD-027. 나머지 정정/취소·복원 예외 및 계약/원자성/동시성은 후속 대상이다.

2026-10-11 사용자 확정(수업 지점 자체 오류 정정 담당자 질문의 1번): PT 진행 기록의 Performed Branch 오류 정정은 Master Admin만 담당한다. Branch Admin은 기존 기록의 지점이나 실제 수행 지점이 자신의 관리 Branch여도 해당 지점 값을 정정할 수 없다. 일반 정정/취소의 수행 지점 기준과 Operator/Trainer 역할의 금지는 유지한다. Master의 Organization 범위와 원본/변경 이력 보존 원칙을 따른다. 소속·발급 지점 변경으로 과거 수행 지점을 자동 변경하지 않는 기존 규칙도 유지한다. 이번 결정은 담당 권한에 한정하며 정정 방식·확정 월 연계·일반/지원 수업 구분에 따른 보상 전환·적용 설정 시점은 BR-007/009/013 및 MB-005의 잔여 OPEN이다.

2026-10-11 사용자 확정(Performed Branch 오류 정정 방법 질문의 1번): Master가 기존 기록을 유지하며 수행 지점과 일반/지원 보상 방식을 정정한다. 기존 Pass 차감 유지, 취소/재등록·복원/재차감 없음. 변경 전 사실/보상은 이력으로 보존하고 유효 보상은 정정된 방식에 맞게 처리하여 중복 합산하지 않는다. 지원 전환의 관리자 수동 보상 원칙은 유지한다. 확정 월은 기존 해제 → 정정 → 같은 월 재확정/이전 확정본 보존 원칙을 동일 적용한다(사용자 일관성 지시). 지원→일반의 지급 설정 기준 시점·나머지 정정/계약 상세는 후속이다(BR-OPS-001, PR-009, BR-007/MB-005).

2026-10-11 사용자 확정(지원→일반 정정의 지급 설정 기준 시점 질문의 1번): 기존 PT 기록을 최초 생성할 때 적용되는 Rate/Fixed Amount를 사용한다. 처음부터 일반 지급을 계산하지 않은 기록도 동일하며 실제 수업일/정정 시점의 값으로 바꾸지 않는다. 기존 기록/Pass 차감·정정/확정본 이력 보존 원칙은 유지한다. 구체 설정 근거/이력 조회·저장 방식은 후속 설계다(BR-PAY-011/012, PR-009).

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: BR-007, ARCH-001, MB-005; 상세 취소/정정 모델은 후속. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): F20/F21; R16–R19. [분석 색인](../analysis/README.md)

2026-10-12 사용자 확정(이용권 횟수의 수동 조정 권한 질문의 1번): Pass 횟수의 수동 조정은 Master Admin의 Organization 전체 범위 또는 처리 시점 현재 관리 Branch가 해당 Pass의 Issued Branch인 Branch Admin에게 허용한다. 수원 발급/현재 강남 소속 Member의 이용권은 수원 Branch Admin 또는 Master가 조정하며, 강남 Branch Admin은 Member의 현재 소속만을 근거로 조정할 수 없다. 회원 소속이나 담당 Trainer가 바뀌어도 Issued Branch 기준은 유지한다. 이용권 수동 만료/해제와 같은 발급 지점 기준이며 담당 교체의 Member 현재 Home Branch 기준과 구별한다(BR-OPS-004/008/009, PD-007/010, PR-003/030).

수동 횟수 조정과 실제 수업 취소의 자동 복원은 별도 업무다. 기존 PT 기록 정정/취소의 Performed Branch 기준·Master 전용 Performed Branch 값 정정과 이력/정산 일관성은 유지한다. 수동 조정으로 과거 수업을 삭제/취소하거나 확정 지급을 재계산할 수 없다. 구체 수량/상태·계약/UoW는 후속이다(BR-OPS-009, BR-002/007).


<a id="pd-011"></a>
## PD-011

Question: 비활성화·이력 조회·완전 삭제를 어떻게 구분할까?

Status: CLOSED

Decision / approved direction: 운영 데이터는 비활성화/상태 변경과 이력 보존을 우선한다. 회원·트레이너·Pass 중단 후에도 과거 Session·정산 이력을 조회한다. Hard Delete는 기본 운영 기능이 아니다.

2026-10-12 사용자 확정(상품 판매 중단의 기존 이용권 영향 질문의 1번): 상품 판매 중단은 새 Pass 발급만 차단하고 이미 발급된 Pass는 기존 조건을 충족하면 계속 사용할 수 있다. 기존 Master 전용 상품 수정 원칙을 판매 중단에도 동일 적용한다. Backend는 새 발급의 판매 가능 상태를 검증하고 기존 Pass 선택에서는 상품 판매 중단만으로 후보를 제외하지 않는다. 기존 Pass의 발급 조건·잔여/사용 상태·과거 수업/지급/정산을 보존하며 잔여 0/개별 수동 만료 등 다른 불가 사유를 면제하지 않는다. 상품 판매 중단과 Pass 만료/취소를 구별하고 판매 재개·나머지 상태/삭제/계약·저장 상세는 후속으로 남긴다(PR-006/003, BR-PAY-001/006).

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: BR-001/007, LEGAL-001. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): R02; K14/K34. [분석 색인](../analysis/README.md)

2026-10-12 사용자 확정(관리자·Trainer 겸임 계정의 Trainer 비활성화 질문의 1번): Trainer 비활성화는 Trainer 역할에 따른 권한만 중단하며, 같은 계정에 독립적으로 부여된 관리자 역할/Scope와 그 범위의 업무는 유지한다. 계정 전체 로그인 차단은 별도 업무다(BR-OPS-014, PD-011/019, PR-005/026, NFR-001/004, ARCH-001/002, MB-001).

기존 이력 보존/인가된 운영자의 조회 원칙은 유지한다. Trainer 비활성화는 과거 수업·지급/정산의 삭제나 자동 기본급 0원/일할 계산이 아니며, 비활성 Trainer 자신의 과거 이력 조회/늦은 등록 예외는 이번에 승인하지 않았다. 재활성화 권한/관계 처리 및 계정 수명 상세는 ARCH-001/002·MB-001 후속이다.

2026-10-12 사용자 확정(Trainer 비활성화 권한 질문의 1번): Master Admin은 자신의 Organization 전체 Trainer, Branch Admin은 비활성화 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 단일 관리 Branch인 경우 Trainer를 비활성화할 수 있다. 타 지점 Branch Admin·Operator/Trainer 단독은 불가하며 겸임자는 독립된 현재 관리자 역할/Scope로 판단한다(BR-OPS-014, PD-011/019, PR-005/029/030, NFR-001/004, ARCH-001/002, MB-001).

허용된 비활성화는 기존 겸임 분리/현재 사실 인가·실패 보존/감사 원칙을 따르며 전체 계정 차단/재활성화 권한은 별도다. 나머지 미정은 BR-OPS-014·ARCH-001/002·MB-001을 따른다.

2026-10-12 사용자 확정(잔여가 남은 담당 이용권이 있는 Trainer의 비활성화 질문의 1번): 잔여가 남은 담당 PT Pass가 있어도 Trainer 비활성화를 허용하며 기존 Assigned Trainer 정보는 유지한다. 비활성화 전에 모든 Pass를 다른 Trainer에게 교체하도록 요구하지 않고 자동 담당 해제/재배정도 하지 않는다. 이후 필요할 때 권한 있는 관리자가 BR-OPS-008의 기존 조건/Scope로 담당을 교체한다(BR-OPS-014, PD-007/011, PR-003/005, NFR-001/004, ARCH-001/002, MB-001/003/005, BR-001).

기존 잔여/발급 조건·과거 이력 보존과 비활성 Trainer 접근 차단을 함께 적용한다. 후속 담당 교체 Actor는 Member 현재 Home Branch이며 Trainer 비활성화 Actor의 Trainer Home Branch로 대체하지 않는다. 개별 지원·재활성화와 기술 상세는 기존 게이트를 따른다.

2026-10-12 사용자 확정(담당 Trainer를 새로 지정할 때의 조건 질문의 1번): PT Pass의 담당 Trainer를 새로 지정할 때는 실제 활성 Trainer만 허용한다. 기존 Pass의 담당 교체 및 허용된 새 Pass 발급 흐름에서 담당을 최초 지정하는 경우 모두 적용하며 비활성 Trainer를 미리 배정하지 않는다(BR-OPS-008/014, PD-007, PR-003/005/029/030, NFR-001, ARCH-001, MB-001/003/005, BR-001).

이번에 새 대상의 활성 필요조건만 해결됐다. 이미 담당인 Trainer가 나중에 비활성화되면 기존 담당을 유지/접근 차단하는 정책과 구분한다. 최초 지정 필수/미지정·나머지 계정/Branch/Pass 상태 조합과 재활성화·비활성 전 수업 누락 등록/구체 계약·경합은 후속이며 현재 담당 조건으로 과거 수업 수행자를 바꾸지 않는다.

2026-10-12 사용자 확정(비활성화 전 진행했지만 누락된 PT 수업 등록 질문의 1번): Trainer 비활성화 전에 실제로 수행한 미등록 PT 수업은 관리자가 대행 등록하는 경로를 허용한다. 대상 Trainer의 비활성 상태를 유지하며 잠시 재활성화/본인 로그인·담당 재배정을 선행 요구하지 않는다. 실제 수행 Trainer·실제 수업일과 기존 Pass 잔여/정산 조건을 그대로 적용한다(BR-OPS-015, PD-008/011, PR-008/029/030, BR-OPS-003/008/014, BR-PAY-006/011/012).

대행 등록은 과거 실제 수행자 참조이고 활성 대상만 가능한 새 담당 지정과 별개다. 비활성 상태/현재 담당·기존 잔여/해당 월 조건과 생성 시점 실제 수행 Trainer 보상 입력을 유지하고 대행 관리자/당시 권한은 별도 감사한다. 대행 인가의 현재 사실 검증·역사 사실/시점 판정/최소 선택 정보·저장/경합은 후속이다. 비활성 Trainer 본인 접근이나 보상 설정/추가실적/정산의 별도 권한을 추가하지 않는다.

<a id="pd-012"></a>
## PD-012

Question: 정산 지표의 정의와 대상은 무엇인가?

Status: CLOSED

Decision / approved direction: Monthly Settlement = 해당 월 적용 Base Salary + 유효한 Session Payment 합계 + 유효한 Additional Performance 합계다. Trainer·대상 월·적용 기본급·Session 수·Session Payment 합계·추가실적 내역/합계·월 정산 합계를 구분한다. 2,500,000원 + 1,200,000원 + 150,000원 = 3,850,000원이며 여러 지점 수업으로 동일 월 기본급을 중복 가산하지 않는다. 타 지점 수업의 보상 전체는 Additional Performance로 반영하며 일반 Session Payment를 별도로 합산하지 않는다(MB-009 CLOSED, 2026-10-10 사용자 정정). 현재 Base Salary 변경으로 과거 확정 월 정산의 적용 기본급·합계가 자동 변경되어서는 안 된다. 현재 Rate/Fixed Amount로 과거 확정 Session Payment를 재계산하지 않는다. Master Admin은 전체 정산을 관리하며 Branch Admin 정산 공개의 남은 상세와 지점 귀속은 MB-006/010 OPEN이다. 기본급 일할·근무일수·휴직 기반 자동 계산과 12개월 고정 평균은 제공하지 않는다.

2026-10-11 사용자 확정(월 정산을 처음 확정할 권한 질문의 1번 답변): 월 정산의 최초 확정은 Master Admin에게 Organization 전체 Trainer, Branch Admin에게 확정 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 직접 확정한다. 지원 수업 미입력에 의한 해당 Trainer·월 확정 차단과 과거 확정본 보존은 유지한다. 최초 확정의 상세 기준은 BR-PAY-016을 따르며, 전체 정산 공개·비용 귀속과 나머지 확정/마감 절차는 MB-006/010 및 BR-009 OPEN이다.

2026-10-11 사용자 확정(지점장이 조회할 정산 내역의 범위 질문의 1번 답변): Branch Admin은 조회 시점에 자신의 관리 Branch를 Home Branch로 가진 Trainer의 해당 월 정산 전체 금액과 구성 내역을 조회할 수 있다. 해당 월 적용 기본급·일반 Session Payment·타 지점 지원 수업을 포함한 Additional Performance·월 정산 총액을 모두 공개하며, 수업의 Performed Branch가 다른 지점이라는 이유로 해당 금액을 제외하거나 숨기지 않는다. 관리 범위 안 본인 Trainer도 포함한다. Master Organization 전체 조회는 유지한다. Performed Branch만으로 다른 Home Branch Trainer의 전체 정산을 공개하지 않으며 대상 월·이전 확정본/세부 계산 근거·감사 공개의 남은 상세는 MB-006, 비용 귀속은 MB-010 OPEN이다. BR-PAY-016과 PR-010에 추적한다.

2026-10-11 사용자 확정(타 지점 지원 수업 보상의 비용 집계 지점 질문의 1번, 복잡도와 적용 범위 설명 후 최종 확인): 타 지점 지원 수업의 전체 보상으로 확정한 Additional Performance 금액은 해당 수업의 실제 Performed Branch 비용으로 집계한다. Trainer·월 정산은 기존 세 구성 합계와 한 번 합산을 유지하며 지점별로 나누어 별도 Trainer 정산을 만들지 않는다. 일반 지급·기본급·다른 추가실적의 비용 귀속과 보고 공개/집계 상세는 MB-010/006 OPEN이다.

2026-10-11 사용자 확정(월중 지점 이동 시 기본급 비용 귀속 질문의 1번 답변): 월중 Trainer 지점 이동이 있는 달의 해당 월 적용 기본급 비용은 대상 월의 월말 Home Branch 한 곳에 전액 귀속한다. 10월 수원→강남 이동, 적용 기본급 2,500,000원이면 강남점 비용 2,500,000원으로 집계한다. 수동 지정된 해당 월 기본급이 있으면 그 금액 전액을 사용하고 지급액이나 자동 일할 계산·지점별 분할을 추가하지 않는다. 이후 월의 이동만으로 과거 비용 귀속을 바꾸지 않는다. 기존 처리 시점 현재 Home Branch 기준 관리 권한은 유지한다. 월말 소속 식별 불가 등 예외·일반 지급/다른 추가실적 귀속·비용 보고 공개/집계 상세는 OPEN이다. BR-PAY-014/016, PR-010 및 MB-010에 추적한다.

2026-10-11 사용자 확정(이동 전후 일반 PT 수당의 비용 귀속 질문의 1번 답변): 일반 Session Payment는 해당 PT 진행 기록의 실제 Performed Branch 비용으로 집계한다. 이미 확정된 수업별 지급액을 지점별로 합산하며 대상 월말 Home Branch로 전액을 모으지 않는다. 이동 전 수원 수업 200,000원·이동 후 강남 수업 300,000원은 각 수행 지점 비용으로 합산하되 Trainer 일반 지급 총액은 500,000원이다. 지급 계산·과거 지급 불변성·지원 수업 보상의 일반 지급과의 중복 합산 금지·이동월 기본급의 월말 소속 전액 귀속·기존 관리 권한은 유지한다. 다른 추가실적 귀속과 비용 보고 공개/집계 상세·일반 지급/진행 기록 정정·취소의 남은 정책은 관련 OPEN이다. BR-PAY-009/016, PR-010 및 MB-010에 추적한다.

2026-10-11 사용자 확정(지점별 비용 보고서 조회 권한 질문의 1번 답변): v1 지점별 비용 보고서는 Master Admin만 Organization 범위에서 조회한다(2026-10-11 사용자 확정). Branch Admin은 자기 지점 비용 합계도 이 보고서로 조회할 수 없으며 Master 권한 없는 Operator·Trainer도 불가하다. Branch Admin의 현재 자기 Home Branch 소속 Trainer 해당 월 정산 전체 금액·구성 내역 조회는 타 지점 지원 보상까지 포함하여 유지한다. 비용 귀속·지급액·기존 등록/정정/확정 권한은 유지하며 보고서 항목·대상 월·집계/완전성·버전 등 남은 상세는 MB-006/010 OPEN이다. Branch Admin에 대한 보고서 공개 확대는 별도 결정한다.

2026-10-11 사용자 확정(지원 수업 외 추가실적을 반영할 정산 월 질문의 1번 답변): 회원 유지 등 지원 수업 외 Additional Performance는 실제 실적이 발생한 월의 Trainer 월 정산에 귀속한다. 9월에 발생한 실적을 10월에 등록해도 9월분이며 등록 월이나 금액 입력 월로 이월하거나 관리자가 반영 월을 임의 선택하지 않는다. 같은 실적을 9월·10월에 중복 합산하지 않는다. 이는 월 정산 입력의 기간 귀속 결정이며 확정된 발생 월의 후등록 절차나 비용 보고 집계 기간을 자동 확정하지 않는다. 기존 금액/한 번 합산·확정본 보존을 유지한다.

2026-10-11 사용자 확정(확정된 월의 누락된 지원 수업 외 추가실적 처리 질문의 1번 답변): 이미 확정된 발생 월의 누락된 지원 수업 외 Additional Performance는 해당 Trainer·월 정산의 확정 해제 → 누락 실적 등록 → 같은 발생 월 재확정으로 반영한다. 이전 확정본은 보존하고 재확정 결과와 구분한다. 확정 상태에 직접 추가하여 이전 확정본을 덮어쓰거나 등록 월/다른 월로 이월하지 않는다. 재확정 시 기존 승인 조건·유효 구성 합계·과거 지급 불변성을 유지한다. 이 후등록의 해제/재확정 권한·소속 기준·사유 등 상세는 BR-009/013의 별도 OPEN이다.

지원 수업 외 실적 등록 및 확정 월 누락분 반영의 해제·재확정은 Master Organization 전체/Branch Admin 각 처리 시점 Trainer 현재 Home Branch 기준으로 인가(Product 확정, 2026-10-11). 단계마다 재검증하며 이전 소속/발생 당시 소속만으로 권한 없음. 발생 월 정산·발생 당시 Home Branch 비용 귀속은 유지. 이 후등록의 해제/재확정 본인 건 허용·별도 승인 없음은 확정(2026-10-11). 기존 실적 정정/취소는 별도 OPEN.

확정 월의 누락된 지원 수업 외 실적 반영을 위한 해제 사유 필수(Product 확정, 2026-10-11). 사유 없는 해제 요청은 거부하고 요청 직전 확정 상태/확정본/기존 실적·정산 구성/금액 유지. 성공 시 대상 Trainer/월·사유·해제자·시점 이력/감사와 이전 확정본 보존. 현재 Home Branch 인가·기존 후등록 순서/월/비용 귀속 유지. 이 흐름의 해제/재확정은 관리 범위 안 본인 건도 별도 승인 없이 허용(2026-10-11).

Branch Admin의 본인이 아닌 소속 Trainer 누락 실적 후등록 해제/재확정은 별도 Master 승인 없음(Product 확정, 2026-10-11). 각 처리 시점 현재 Home Branch 인가·해제 사유 필수·해제 후 등록/동일 월 재확정·이전 확정본/감사·기존 확정 조건/미입력 지원 수업 차단 유지. 관리 범위 안 관리자 본인 건의 해제/재확정 허용·별도 승인 없음도 확정(2026-10-11).

관리 범위 안 관리자·Trainer 겸임자의 본인 누락 실적 후등록 해제/재확정도 별도 승인 없이 허용(Product 확정, 2026-10-11). Master Organization 범위/Branch Admin 각 처리 시점 본인 현재 Home Branch 일치·해제 사유 필수·본인 감사/이전 확정본 보존·기존 후등록 순서/월/비용 귀속·재확정 조건/미입력 지원 수업 차단 유지. Trainer 단독 권한 없음. 비지원 실적의 금액 외 정보 수정/취소 등은 OPEN.

월 정산 확정 전 비지원 추가실적 금액 수정은 Master Organization 전체/Branch Admin 각 수정 시점 Trainer 현재 Home Branch 기준으로 허용(Product 확정, 2026-10-11). 관리 범위 안 본인 건 포함·별도 승인 없음·변경 사유 필수·전후 금액/사유/수정자/시점 이력과 감사. 사유 누락 거부/요청 직전 금액 유지. 발생 월/당시 Home Branch 비용 유지. 수정 금액의 나머지 입력 제약, 금액 외 정보 수정/취소는 OPEN.

지원 수업 외 추가실적은 최초 등록과 확정 전 금액 수정 모두 양수만 허용(Product 확정, 2026-10-11 사용자 일관성 지시 적용). 0원·음수·누락 수정 거부/요청 직전 금액·이력·정산 입력 상태 유지; 사유가 있어도 0원 수정 불가. 기존 관리자 Scope/본인 건/승인 생략/사유·이력/감사 유지. 지원 수업 보상 및 월별 수동 기본급의 승인된 사유 필수 0원 예외는 유지. 상한/정밀도·금액 외 정보 수정/취소는 OPEN.

지원 수업 외 실적의 확정 후 금액 오류도 해당 Trainer/월 해제 → 양수 금액 정정 → 같은 월 재확정·이전 확정본/구성/이력 보존(2026-10-11 사용자 일관성 지시 적용). Master Organization/Branch Admin 각 처리 시점 현재 Home Branch·본인 건 포함·별도 승인 없음·해제/정정 모두 사유 필수·감사·기존 재확정 조건/미입력 지원 수업 차단 유지. 발생 월/당시 Home Branch 비용 유지. 금액 외 정보 수정/취소·나머지 기간/금액 제약은 OPEN.

Approval source: 2026-09-17 최신 사용자 지점 관계·추가실적·월 기본급·보상 설정 권한 확정. 충돌하는 이전 방향은 대체하며 비충돌 결정을 유지한다.

2026-10-10 사용자 확정(금액 미입력 지원 수업이 남은 월의 정산 확정 질문의 1번 답변): 해당 Trainer의 해당 월 정산 대상 지원 수업에 금액 미입력 건이 하나라도 있으면 그 Trainer·월 정산을 확정할 수 없다. 미입력 수업을 제외하거나 0원으로 간주해 확정하지 않는다. 이미 완료한 진행 기록·Pass 차감은 유지한다. 차단 범위는 해당 Trainer·월이며 다른 Trainer·월로 확대하지 않는다. 모든 금액 입력 완료는 이 차단 조건의 해소이며 월 정산 자동 확정이나 나머지 확정 조건의 충족을 뜻하지 않는다. 최초 월 정산 확정 권한과 별도 Master 승인 없음은 2026-10-11 후속 사용자 결정으로 확정했다. 월 귀속·나머지 확정 조건·확정/마감 절차와 남은 정정/취소 및 남은 마감 이후 처리는 OPEN을 유지한다. 당시 미결정이었던 지원 수업 0원 허용은 후속 사용자 결정으로 해결했다.

타 지점 지원 수업 보상은 권한 있는 관리자가 사유를 기록하면 0원으로 명시적으로 확정할 수 있다. 사유 없는 0원 입력은 보상 확정이 불가하다. 사유를 남기고 확정한 0원은 금액 미입력이 아니므로 그 건으로 월 정산 확정을 차단하지 않는다. 다른 미입력 건이 남으면 기존 차단 조건을 유지한다. 지원 수업의 사유 필수 0원 확정은 금액 미입력 건을 임의로 제외하는 절차가 아니다. 나머지 확정 조건·정정/마감 정책은 별도다.

2026-10-10 사용자 확정(월 정산 확정 후 지원 수업 보상 오류 처리 질문의 2번 답변): 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 이전 확정본의 적용 기본급·구성 금액·합계를 덮어쓰거나 삭제하지 않으며 이전본과 재확정본을 구분한다. 예를 들어 9월 지원 수업 보상 30,000원의 오류를 35,000원으로 정정할 때 9월 정산의 확정 해제 → 지원 수업 보상 금액 정정 → 9월 정산 재확정으로 처리하고 이전 30,000원 반영 확정본을 보존한다. 금액 정정 시 PT 진행 사실·Pass 차감을 재실행하거나 현재 Rate/Fixed Amount/Base Salary를 이유로 과거 확정 일반 지급·기본급을 자동 재계산하지 않는다. 재확정에도 해당 Trainer·월의 미입력 지원 수업 차단 등 승인된 확정 조건을 적용한다. 이번 결정은 지원 수업 보상 금액 오류의 정정 경로와 이전 확정본 보존에 한정한다. 당시 미결정이었던 지원 수업 정정의 해제·재확정 권한은 아래 후속 사용자 결정으로 확정했다. 다른 정정/취소 및 실제 지급과의 대사·차액 처리 상세는 미정이다.

2026-10-10 사용자 확정(지원 수업 보상 정정의 월 정산 확정 해제·재확정 권한 질문의 2번 답변): 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. 수업의 Performed Branch만으로 다른 Home Branch Trainer의 정산 확정 해제·재확정 권한을 얻지 않는다. 관리자 권한이 없는 Operator·Trainer는 이 작업을 수행할 수 없다. 해당 Trainer·월의 확정 해제 → 금액 정정 → 동일 월 재확정과 이전 확정본 보존은 유지한다. 이 결정은 지원 수업 보상 금액 오류 정정에 한정하며 최초 월 정산 확정 권한이나 전체 정산 공개 범위(MB-006)를 새로 확정하지 않는다. 위 지원 수업 보상 정정의 현재 Home Branch 권한 기준은 아래 후속 사용자 결정으로 확정했다.

2026-10-10 사용자 확정(지점 관리자의 지원 수업 보상 정정 시 월 정산 확정 해제·재확정의 별도 승인 질문의 1번 답변): Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer의 지원 수업 보상 정정을 위해 월 정산을 확정 해제·재확정할 때는 Master의 별도 승인을 두지 않는다. Master 승인 대기 단계 없이 관리 범위 안에서 직접 처리하며 이전 확정본과 해제·재확정 이력 및 감사를 유지한다. 기존 Master Organization 범위·Branch Admin 대상 Trainer Home Branch 기준과 범위 밖 접근 거부는 유지한다. 해당 Trainer·월의 확정 해제 → 금액 정정 → 동일 월 재확정 순서와 재확정 시 미입력 지원 수업 차단 등 승인된 확정 조건도 유지한다. 이번 결정은 위 정정의 별도 Master 승인 생략에 한정하며 최초 월 정산 확정 권한/승인, Trainer 신청 승인, 다른 정정/취소 또는 정산 공개 범위로 확대하지 않는다. 확정 해제 사유 필수는 아래 후속 사용자 결정으로 확정했다. 위 지원 수업 보상 정정의 현재 Home Branch 권한 기준은 아래 후속 사용자 결정으로 확정했다.

2026-10-10 사용자 확정(지원 수업 보상 정정 시 월 정산 확정 해제 사유 질문의 1번 답변): 지원 수업 보상 정정의 월 정산 확정 해제에는 사유가 필수이며, 사유 없이 해제할 수 없다. 사유·해제자·시점을 이력으로 남긴다. Master Admin·Branch Admin 모두에 적용한다. 기존 Master Organization 범위·Branch Admin 대상 Trainer Home Branch 기준, Branch Admin의 별도 Master 승인 없음, 이전 확정본 보존과 해제·정정·동일 월 재확정 경로를 유지한다. 금액 수정의 변경 사유 필수도 유지한다. 사유 없는 해제 요청은 기존 확정 상태·확정본·보상 금액을 변경하지 않는다. 이번 결정은 위 지원 수업 보상 정정의 확정 해제에 한정하며 다른 정정/취소 정책으로 확대하지 않는다. 구체 입력 화면·저장 구조는 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(지점 이동 후 과거 지원 수업 보상 정정·정산 해제/재확정의 Home Branch 기준 질문의 1번 답변): 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 9월 수원 소속 Trainer가 10월 강남으로 이동한 뒤 9월 지원 수업 보상을 정정하는 예에서는 강남 Branch Admin에게 해당 정정과 월 정산 확정 해제·재확정을 허용하고, 별도 Master 권한이 없는 수원 Branch Admin에게는 과거 소속만을 근거로 허용하지 않는다. 과거 수업의 Performed Branch·수업 사실·이전 확정본·기존 이력은 보존한다. 기존 관리 범위 검증·Branch Admin의 별도 Master 승인 없음·금액 수정 사유 및 확정 해제 사유 필수·감사 정책을 유지한다. 이번 결정은 지원 수업 보상 금액 정정과 해당 월 정산 해제/재확정의 인가 기준에 한정한다. 다른 추가실적 최초 등록/정정의 이동 기준, Trainer 이동 자체의 적용 시점·절차, 비용 귀속·정산 공개(MB-010/006)는 미결정으로 남긴다. 당시 미정이었던 최초 월 정산 확정 권한과 별도 Master 승인 없음은 2026-10-11 후속 사용자 결정으로 확정했다.

추가 사용자 확정(2026-10-10, 확정 월 기본급 오류 처리 질문의 1번 답변): 확정된 월의 기본급 오류는 해당 Trainer·월의 확정 해제 → 해당 월 적용 기본급 정정 → 동일 월 재확정으로 처리하고 이전 확정본은 이력으로 보존한다. 현재 설정 변경에 따른 자동 갱신과 구별한다. 기본급 오류 정정의 확정 해제·재확정은 Master Admin에게 Organization 전체, Branch Admin에게 각 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 처리한다. 확정된 월의 기본급 오류 정정에서 확정 해제와 해당 월 기본급 수정 모두 사유가 필수다. Master Admin·Branch Admin 및 관리 범위 안 본인 건에 동일하게 적용한다. 해제 사유·해제자·시점과 변경 전후 기본급·수정 사유·수정자·시점을 이력으로 남긴다. 기본급 오류 정정은 대상 Trainer의 해당 월 정산에만 적용하며 현재·미래 기본급 설정과 다른 월 정산은 유지한다. 지속적인 기본급 변경은 별도로 적용 시작 월을 지정하는 기존 흐름을 따른다. 미리 등록할 수 있는 미래 적용 시작 월의 범위 등 남은 정책은 BR-012 OPEN이다.

Follow-up: BR-007/008/009/010/012/013, MB-006/010; 관리자가 지정하는 미리 등록할 수 있는 미래 적용 시작 월의 범위, 추가실적과 남은 정정·마감/확정 절차, 귀속·열람 결정 전 관련 상세 설계 보류. BR-011 상품 변경 및 MB-009 보상 분류는 CLOSED다.

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): F26/F27; R22; K34. [분석 색인](../analysis/README.md)

추가 사용자 확정(2026-10-10, 입사·퇴사·휴직 월 기본급 질문의 1번 답변): 입사·퇴사·휴직이 있는 달의 적용 기본급은 관리자가 해당 Trainer·월의 금액을 직접 지정한다. 예를 들어 월 기본급 설정이 2,500,000원이어도 해당 월만 1,500,000원을 적용할 수 있으며, 이 지정으로 현재·미래 기본급 설정과 다른 월 정산은 변경하지 않는다. 월별로 수동 지정한 기본급은 이후 일반 기본급 설정이 변경되어도 유지한다. 일반 설정 변경의 미확정 정산 자동 반영은 수동 지정이 없는 월에 적용하며, 수동 지정 월의 금액을 바꾸려면 관리자가 해당 월 금액을 직접 수정한다. 미확정 월의 기본급을 최초 수동 지정하거나 다시 수정할 때 모두 사유가 필수다. 사유가 없는 요청은 거부하고 요청 직전의 수동 지정 여부·적용 금액·월 합계를 유지한다. 대상 Trainer·월, 지정/수정 전후 금액·사유·처리자·처리 시점을 이력으로 남긴다. 미확정 월 기본급의 최초 수동 지정·수정은 Master Admin의 Organization 전체, Branch Admin의 각 처리 시점 대상 Trainer 현재 Home Branch가 관리 Branch와 일치하는 범위에서 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 직접 처리한다. 추가 사용자 확정(2026-10-11): 해당 월 기본급은 권한 있는 관리자가 사유를 남기면 0원으로 명시적으로 수동 지정할 수 있다. 수동 지정한 0원은 미입력과 구분하며, 미입력이나 누락된 일반 설정을 자동으로 0원으로 대체하지 않는다. 해당 월 기본급에만 적용하고 다른 유효 지급·추가실적은 기존 규칙대로 합산한다. 미리 등록할 수 있는 미래 적용 시작 월의 범위와 월별 수동 지정 금액의 나머지 입력 제약 등은 BR-012/BR-010 OPEN이다.

추가 사용자 명확화(2026-10-11): 일반 Base Salary 설정은 관리자가 지정한 적용 시작 월부터 다음 기본급 변경의 적용 시작 월 전까지 매월 계속 적용한다. 적용 종료 월을 지정하거나 같은 금액을 매월 다시 등록할 필요는 없다. 특정 월 수동 지정은 해당 월에만 적용하는 기존 예외를 따른다. 미래 시작 월로 변경을 얼마나 미리 등록할 수 있는지는 이번 답변으로 확정하지 않는다.

<a id="pd-013"></a>
## PD-013

Question: 수동 트레이너 매출 기능을 유지하고 무엇을 매출로 부를까?

Status: CLOSED

Decision / approved direction: 수동 트레이너 매출은 v1 제외다. 기존 매출 자료 조회/이관도 하지 않는다. 향후 실제 필요가 확인되면 별도 요구사항화한다.

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: 후속 제품 확장 후보. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): F22–F25; K37; verification-report. [분석 색인](../analysis/README.md)

<a id="pd-014"></a>
## PD-014

Question: 가계부를 웹 v1에 포함하고 잔액 조정을 어떻게 허용할까?

Status: CLOSED

Decision / approved direction: 가계부는 v1 제외다. PT 관리와 별도 bounded context 후보이며 필요 시 Product Expansion으로 검토한다.

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: 경계 후보일 뿐 이번 문서에서 Architecture를 확정하지 않음. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): F37–F48/F52; R28–R31/R34. [분석 색인](../analysis/README.md)

<a id="pd-015"></a>
## PD-015

Question: 고정 거래 실행 시점·말일·누락분·중단 규칙은 무엇인가?

Status: CLOSED

Decision / approved direction: 가계부 제외에 따라 고정 거래 실행 정책 검토를 현재 보류한다. v1에 고정 거래를 구현하지 않는다.

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: 보류 결정은 승인됨; 실행 규칙은 후속 가계부 채택 시. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): F49–F51/F53; B07; R32/R33. [분석 색인](../analysis/README.md)

<a id="pd-016"></a>
## PD-016

Question: 락커 운영 정책과 v1 필요성은 무엇인가?

Status: CLOSED

Decision / approved direction: 락커는 v1 제외다. 향후 별도 기능으로 추가할 수 있다.

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: 후속 제품 확장 후보. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): F28–F33; R24–R27. [분석 색인](../analysis/README.md)

<a id="pd-017"></a>
## PD-017

Question: 기존 데이터 이관은 필요한가? 어느 기간·도메인까지 옮길까?

Status: CLOSED

Decision / approved direction: 기존 운영 데이터를 이관하지 않는다. 빈 운영 데이터에서 시작하며 Master Admin/기준정보도 새로 설정한다. 기존 schema·데이터·결함의 호환성을 요구하지 않는다. Migration tooling은 v1 제외다.

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: OPS-001; 기존 잔여·과거 Session·계정/암호·매출 조회도 이관 범위 없음. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): 05 DB; 10 전환; K11/K20/K21. [분석 색인](../analysis/README.md)

<a id="pd-018"></a>
## PD-018

Question: 기존 프로그램과 병행할까, 한 번에 전환할까?

Status: CLOSED

Decision / approved direction: 운영 준비와 acceptance criteria 충족 후 웹으로 일괄 전환한다. 장기간 동일 업무를 두 시스템에 병행 입력하는 구조를 만들지 않는다.

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: OPS-001; 짧은 준비/검증 기간만 cutover 계획에서 별도 정의. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): K13/K19; 10 전환. [분석 색인](../analysis/README.md)

<a id="pd-019"></a>
## PD-019

Question: 계정 발급·초기 관리자·암호 재설정·접근 종료 정책은?

Status: CLOSED

Decision / approved direction: 계정은 관리자 발급 방식을 유지하고 Master Admin이 Branch Admin 및 계정/권한을 관리한다. v1 Trainer 로그인 계정도 포함한다. 기존 계정/암호는 이관하지 않는다. Branch Admin의 자기 단일 관리 Branch 새 Operator 발급/최초 업무 Branch 지정은 승인됐다(2026-10-12, BR-OPS-011). 기존 Operator 업무 Branch 변경은 Master Organization 범위 전용이며 Branch Admin은 불가하다(2026-10-12, BR-OPS-011). 신규 Trainer 로그인 계정 발급은 Master Organization 전체/Branch Admin 대상 Trainer의 현재 Home Branch 관리 범위에서 승인됐다(2026-10-12, BR-OPS-012). E5로 기존 계정 Operator·Trainer 역할 추가/회수의 Branch Admin 관리 범위는 승인됐다(BR-OPS-019). 다른 역할/Scope·계정 수명 위임과 구체 상태/연결/재부여·계약은 후속이다.

추가 사용자 확정(2026-10-10, 이번 설계 검토의 직접 답변): 최초 비밀번호 설정은 Master가 일회용 비밀번호 설정 링크를 대상자에게 전달하고 대상자가 직접 설정하는 흐름이다. 긴 토큰 수동 입력을 기본 흐름으로 요구하지 않는다. 전달 채널·유효기간·재발급·활성 계정 재설정은 ARCH-002의 남은 질문이다.

Approval source: 2026-09-17 사용자 Multi-Branch 제품 방향 변경 지시. 충돌하는 이전 결정은 본 결정으로 대체하며 기존 비충돌 규칙은 유지한다.

Follow-up: ARCH-001/002, MB-004; 초기 Master Admin·재설정·중단·마지막 Master Admin 보호 및 접근 종료 상세를 후속 설계한다. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): F01/F57–F59; K08/K29. [분석 색인](../analysis/README.md)

2026-10-12 사용자 확정(Operator 계정 발급과 최초 지점 지정 권한 질문의 1번): Master Admin은 자신의 Organization 범위에서, Branch Admin은 자신의 단일 관리 Branch 범위에서 새 Operator 계정을 발급하고 그 한 지점을 최초 업무 Branch로 지정할 수 있다. Branch Admin의 타 지점 Operator 발급은 허용하지 않는다. Backend는 처리 시점의 검증된 현재 Caller 역할/Organization·관리 Branch와 대상 Branch의 실제 Organization 관계를 확인하며 직접 ID·위조 role/branch_id·과거 권한으로 범위를 우회할 수 없다. Operator 단독·Trainer 단독의 로그인 계정 발급은 허용하지 않는다(BR-OPS-011, PD-019, PR-021/030, NFR-001/004, MB-004, ARCH-001/002).

승인 범위: 새 Operator 계정 발급과 단일 Branch의 최초 지정이다. Branch Admin의 Master/Branch Admin 역할 발급, 기존 계정의 역할 추가·변경·계정 중단/복구·비밀번호 재설정 권한을 추가하지 않는다. 신규 Trainer 계정 발급은 별도 후속 승인된 BR-OPS-012의 현재 Trainer Home Branch 규칙을 적용한다. 기존 Operator Branch 변경은 별도 후속 승인된 Master 전용 규칙을 적용한다. 기존 겸임 역할의 독립 Scope·Trainer Home Branch 및 민감 보상 접근 제한을 유지한다. 계정 발급과 새 Pass 발급은 서로 다른 업무이며 Operator의 Pass 발급 허용을 계정 발급 권한으로 해석하지 않는다.

기존 사용자 일관성 지시(2026-10-11) 적용: 이번에 허용된 Operator 발급에도 기존 최초 비밀번호 설정 방식을 사용한다. 권한 있는 발급 관리자가 일회용 비밀번호 설정 링크를 대상자에게 전달하고 대상자가 직접 설정한다. 허용 범위 내 Branch Admin 발급에 별도 Master 승인 대기를 추가하지 않는다. 고정/임시 평문 비밀번호를 계정에 넣거나 긴 토큰 수동 입력을 기본 흐름으로 요구하지 않는다. 최초 설정 링크 30분/단일 사용·재발급 시 이전 링크 폐기는 A4로 해결됐다. 전달 채널/수신자 확인·활성 계정 재설정·나머지 계정 수명 상세는 ARCH-002의 게이트를 유지한다.

2026-10-12 사용자 확정(기존 Operator의 근무 지점 이동 권한 질문의 1번): 기존 Operator의 단일 업무 허용 Branch 변경은 Master Admin만 자신의 Organization 범위에서 수행할 수 있다. Branch Admin은 변경 전/후 지점 관리자이거나 해당 계정의 최초 발급자여도 변경할 수 없다. Operator·Trainer 단독도 불가하며 겸임자는 현재 Master 권한이 있을 때만 그 관리 Scope로 처리한다(BR-OPS-011, PD-019, PR-021/030, NFR-001/004, MB-004, ARCH-001).

지점 변경은 새 Operator 발급과 구별하며 기존 저장 후 현재 Scope 반영/실패 보존·감사 원칙을 적용한다. Branch Admin의 자기 지점 신규 발급은 유지하고 기존 역할/나머지 Scope 변경·계정 수명 위임은 OPEN이다. 자세한 경계는 BR-OPS-011을 따른다.

2026-10-12 사용자 확정(신규 Trainer 로그인 계정 발급 권한 질문의 1번): Master Admin은 자신의 Organization 전체 Trainer, Branch Admin은 발급 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 단일 관리 Branch인 경우 신규 Trainer 로그인 계정을 발급할 수 있다. Branch Admin은 타 지점 소속 Trainer 계정을 발급할 수 없다. 타 지점 지원 수업·담당 회원/Pass·Performed Branch·Operator 업무 Branch·최초 발급자/과거 소속 사실만으로 이 권한이 생기지 않는다. Operator·Trainer 단독은 본인 포함 로그인 계정 발급 불가이며 관리자 겸임은 현재 관리자 역할의 독립 Scope로 판단한다(BR-OPS-012, PD-019, PR-021/029/030, NFR-001/004, MB-004, ARCH-001/002).

최초 비밀번호 설정은 기존 일회용 링크/대상자 직접 설정 방식을 적용한다. 기존 계정 역할 추가/Trainer 재연결·소속 변경·수명 업무의 권한은 이번 승인 범위가 아니며 구체 발급/연결/감사·일관성 계약은 BR-OPS-012 및 기존 게이트 후속이다.

Trainer 비활성화와 계정 수명의 경계(2026-10-12, BR-OPS-014): 관리자·Trainer 겸임의 Trainer 권한 중단은 독립 관리자 역할/Scope를 유지하며 계정 전체 차단과 분리한다. 비활성화 Actor는 Master Organization 전체/Branch Admin 처리 시점 Trainer 현재 Home Branch로 추가 확정됐고 전체 계정 복구/마지막 Master 보호의 구체 전이·Trainer 상태/Caller 처리·AuthSession 기술 계약은 후속이다. 상세 승인/미정 범위는 BR-OPS-014와 ARCH-001/002를 따른다.

2026-10-12 사용자 확정(Trainer 비활성화 권한 질문의 1번): Master Admin은 자신의 Organization 전체 Trainer, Branch Admin은 비활성화 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 단일 관리 Branch인 경우 Trainer를 비활성화할 수 있다. 타 지점 Branch Admin·Operator/Trainer 단독은 불가하며 겸임자는 독립된 현재 관리자 역할/Scope로 판단한다(BR-OPS-014, PD-011/019, PR-005/029/030, NFR-001/004, ARCH-001/002, MB-001).

허용된 비활성화는 기존 겸임 분리/현재 사실 인가·실패 보존/감사 원칙을 따르며 전체 계정 차단/재활성화 권한은 별도다. 나머지 미정은 BR-OPS-014·ARCH-001/002·MB-001을 따른다.

<a id="pd-020"></a>
## PD-020

Question: 파일 가져오기와 외부 업무 연동을 무엇까지 지원할까?

Status: CLOSED

Decision / approved direction: Migration용 파일 import를 v1 필수 기능으로 두지 않는다. 미확인 결제·SMS·카카오톡·이메일·장치 연동은 추가하지 않는다. CSV/Excel import/export도 실제 필요 확인 전 필수 요구가 아니다.

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: 승인된 v1 연동 없음; 새 필요는 별도 Product Requirement. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): 09 외부 연동; H03. [분석 색인](../analysis/README.md)

<a id="pd-021"></a>
## PD-021

Question: 성능·가용성·복구와 운영 책임의 수용 기준은 무엇인가?

Status: OPEN

Decision / approved direction: Organization의 여러 Branch와 Trainer 직접 로그인·다중 기기 이용 규모를 기준으로 동시 사용자·자료 증가·응답시간·백업·복구 요구와 운영 책임을 Architecture/NFR 단계에서 결정한다. 임의의 정량 목표나 대규모 트래픽 전제를 두지 않는다.

Approval source: 2026-09-15 승인 및 2026-09-17 Multi-Branch 변경 지시. 후속 결정 단계와 대상 범위만 지정됨; 정량 수용 기준은 미승인.

Follow-up: ARCH-004; 정량 목표와 수용 기준은 OPEN. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): K18/K36; NEW-CANDIDATE. [분석 색인](../analysis/README.md)

<a id="pd-022"></a>
## PD-022

Question: 개인정보 항목·열람 범위·보존 기간·감사기록 범위는?

Status: CLOSED

Decision / approved direction: 최소 개인정보와 Role·Data Scope 보호를 유지한다. Session 생성·정정/취소, Pass 잔여 변경, 계정/권한, 중요 Branch 관리 및 추가실적 생성·정정·취소는 감사 대상이다. 모든 보상 설정 변경(최초 설정 포함)에 대상 Trainer, 변경 항목, 변경 전 값, 변경 후 값, 변경 Actor, Actor의 권한 및 Branch Context, 변경 시점을 추적한다. 별도 Master Admin 승인 없이 변경 가능하며 변경 요청→승인 대기→승인→반영 절차를 추가하지 않는다. 이 결정은 추가실적 승인이나 월 정산 마감/확정 절차를 면제하지 않는다. 감사 및 다른 화면으로 비인가 사용자에게 보상 설정을 우회 노출하지 않는다.

Approval source: 2026-09-17 최신 사용자 지점 관계·추가실적·월 기본급·보상 설정 권한 확정. 충돌하는 이전 방향은 대체하며 비충돌 결정을 유지한다.

Follow-up: ARCH-001, BR-007, LEGAL-001; Audit Log schema·열람·보존 기간은 후속. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): F02/F07; 08 인증; K06/K07. [분석 색인](../analysis/README.md)

2026-10-12 사용자 확정(회원 등록 시 전화번호 필수 여부 질문의 1번): 새 Member 등록을 완료하려면 전화번호를 반드시 입력해야 한다. 전화번호가 누락되거나 빈 문자열·공백만 있으면 등록을 완료하지 못한다. 임의 번호나 기본값으로 필수 입력을 대신하지 않는다. 이 결정은 전화번호 필수 입력이며 번호 중복 허용/금지·구체 형식/정규화·문자/본인 확인, 다른 개인정보 필수 수집이나 등록/수정 Actor 권한을 확정한 것은 아니다. 기존 Role·Data Scope와 Trainer의 인가된 담당/지원 회원 전체 전화번호 읽기는 유지한다(BR-OPS-006, PD-022, PR-002, NFR-005, LEGAL-001).

기존 사용자 일관성 지시 적용(2026-10-11): 일반 회원정보 수정에서도 필수 전화번호를 누락·빈 문자열·공백만인 값으로 지우는 변경은 허용하지 않는다. 전화번호를 변경하지 않는 다른 정보 수정에서는 기존 번호를 유지한다. 이는 등록 필수 요건을 일반 수정에 동일 적용한 것이며 전화번호 수정 권한을 새로 부여하거나 특정 API 입력 형태를 승인한 것은 아니다. 법적·운영상 필요한 개인정보 삭제/보존 예외는 LEGAL-001에서 별도 결정한다.

2026-10-12 사용자 확정(회원 간 전화번호 중복 허용 여부 질문의 1번): 같은 Organization의 여러 Member가 같은 전화번호를 사용할 수 있다. 가족 등 공유 연락처로도 각각 등록하며 전화번호가 같다는 이유만으로 신규 등록을 거부하지 않는다. Member는 전화번호와 별개의 고유 식별자로 구분한다. 동일 번호를 같은 회원으로 자동 병합하거나 Pass·PT 진행/지급 이력·담당/지원 관계를 공유하는 근거로 삼지 않는다. 전화번호 필수 입력과 기존 Role·Data Scope는 유지한다(BR-OPS-006, PD-022, PR-002, NFR-005, LEGAL-001).

기존 사용자 일관성 지시 적용(2026-10-11): 전화번호를 변경할 권한이 있는 Actor의 일반 수정에도 같은 중복 허용 원칙을 적용한다. 다른 Member가 이미 쓰는 번호라는 이유만으로 변경을 거부하지 않되 필수 번호 비움 금지와 현재 업무 인가는 그대로 적용한다. 이 결정으로 등록/수정 권한을 추가하지 않는다.

2026-10-12 사용자 확정(발급용 타 지점 회원 검색 질문의 2번): Branch Admin·Operator는 자신의 허용된 실제 Issued Branch에서 새 PT Pass를 발급하기 위해 같은 Organization 전체 지점의 Member를 이름·전화번호 일부로 검색할 수 있다. 전화번호 전체 일치만을 요구하지 않으며 Member Home Branch가 Caller의 관리/발급 Branch와 다르다는 이유만으로 검색 후보에서 제외하지 않는다. Master의 기존 Organization 전체 범위는 유지한다. 검색은 기존 Member를 선택하여 실제 발급 지점의 새 Pass를 만드는 흐름이며 Member 소속 이동/복제나 기존 Pass·PT·지급·정산 변경을 수행하지 않는다(BR-OPS-010, PD-004/007/022, PR-002/003/030).

검색 인가/정보 공개 경계: 이 허용은 이용권 발급용 Member 검색의 후보 범위·검색 방식과 이름/전체 전화번호/현재 Member Home Branch 공개다. Backend는 매 검색/선택/발급 요청에서 현재 Caller의 발급 역할/Organization·허용 실제 Issued Branch와 대상 Member의 실제 Organization을 검증한다. 검색 Branch Context를 위조하거나 과거 검색 결과/선택 Member ID로 철회된 역할·Scope 또는 다른 Organization을 우회할 수 없다. 같은 전화번호/이름의 여러 Member는 별도 식별자로 구분하여 선택하며 번호만으로 병합하거나 첫 결과를 자동 선택하지 않는다. 이 세 항목의 읽기 허용이 회원 정보/전화번호 수정·일반 Member 상세·전체 무조건 목록/일괄 내보내기, 다른 개인정보/Pass/PT/보상 정보 열람 권한을 추가하지 않는다. Trainer 단독의 담당/개별 지원 Member 검색 및 기존 전체 전화번호 공개는 유지하고 발급 역할 겸임은 그 독립 발급 업무 Scope로 판단한다. 응답은 승인된 공개 범위 안에서 구성하며 Member 선택용 최소 식별 응답/계약과 추가 공개 정보는 후속이다. 실제 운영 연락처/검색어를 문서·일반 로그에 복사하지 않는다.

회원 식별의 기존 원칙 적용: 같은 전화번호/이름으로 여러 Member가 일치하면 별도 Member 식별자로 구분하여 발급할 대상을 선택한다. 번호 일치/첫 결과만으로 자동 병합·동일 회원 취급·소속 이동 또는 다른 Member 이력/권한 공유를 하지 않는다(BR-OPS-006). 잔여 0만으로 회원을 제외하지 않는 기존 조회 원칙은 유지하며 발급용 검색을 Trainer 전용 선택 제외 필터/담당 회원 집합으로 제한하지 않는다. 비활성 Member/Branch 등 나머지 대상 조건·검색어/빈 검색 처리·추가 공개 정보·최소 선택 응답/계약·선택/발급 일관성은 후속이다. 검색 자체는 업무 데이터를 변경하지 않으며 검색 성공만으로 발급 완료나 발급 이후 관리자 권한을 얻지 않는다.

2026-10-12 사용자 확정(발급용 검색 결과 표시 정보 질문의 1번): 새 PT Pass 발급용 Member 검색 결과에는 이름·전체 전화번호·소속 지점을 표시한다. 소속 지점은 해당 Member의 현재 Home Branch이며 Caller 관리 지점/Pass Issued Branch/수업 Performed Branch와 구별한다. 같은 Organization의 타 지점 회원 검색 결과에도 동일하게 적용하고 부분 마스킹된 번호만 표시하도록 제한하지 않는다. 기존 이름·전화번호 일부의 Organization 전체 지점 검색과 현재 발급 역할/실제 Issued Branch Scope 인가는 유지한다(BR-OPS-010, PD-004/007/022, PR-002/003/030, NFR-001/005).

전화번호 읽기 공개 범위만 확정한다. 회원/번호 수정·내보내기나 일반 회원 상세·다른 Pass/PT/보상 권한은 추가하지 않으며 별도 Member 구분/선택과 기존 소속·이력/발급 지점 원칙을 유지한다. 선택 응답/계약·추가 공개 정보/나머지 대상 조건은 후속이다(BR-OPS-006/010).


<a id="pd-023"></a>
## PD-023

Question: 숨김 기능·빈 화면·데스크톱 조작의 웹 제외 후보를 승인할까?

Status: CLOSED

Decision / approved direction: 숨김 기능·빈 화면·미연결 기능은 DROP-CANDIDATE를 유지한다. 존재 자체로 구현하지 않고 실제 업무 필요가 확인되면 요구사항으로 승격한다.

Approval source: 사용자 승인 지시(2026-09-15). 제품 방향 승인; 상세 TODO는 미결정.

Follow-up: 영구 폐기 확정 아님; v1 필수 구현 아님. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): H01/H02/H04; S05/S15; F34/F36. [분석 색인](../analysis/README.md)

<a id="pd-024"></a>
## PD-024

Question: 계약·예약·출석·결제·환불·회원권·상담을 새로 추가할까?

Status: CLOSED

Decision / approved direction: 계약·출석·고객 결제·환불·회원권·상담을 v1에 추가하지 않는다. Reservation/Schedule도 v1 제외이지만 PD-025의 명시적 Future Scope다. PT Pass 도입 자체로 이 도메인을 v1에 추가하지 않는다.

Approval source: 2026-09-17 사용자 Multi-Branch 제품 방향 변경 지시. 충돌하는 이전 결정은 본 결정으로 대체하며 기존 비충돌 규칙은 유지한다.

Follow-up: Schedule/Reservation은 PD-025; 나머지는 후속 필요 확인 시 별도 범위 승인. [후속 질문](open-questions.md)

Related requirements: [요구사항](requirements.md), [Scope](scope.md)

AS-IS Evidence (reference only): 02 도메인; 12 용어집. [분석 색인](../analysis/README.md)

<a id="pd-025"></a>
## PD-025

Question: Schedule/Reservation은 어느 단계의 범위인가?

Status: CLOSED

Decision / approved direction: PT Schedule, Reservation, Reservation Cancellation, Member Schedule 및 Trainer Schedule 확장은 Member Self-Service와 함께 고려하는 명시적 Future Scope다. v1에는 구현하지 않는다. 향후 추가를 불필요하게 어렵게 만드는 구조적 제약을 피하도록 Handoff에 기록한다.

Approval source: 2026-09-17 사용자 제품 방향 변경 지시.

Follow-up: Product Expansion에서 상세 정책 결정. 현재 예약 Domain 설계 없음.

Related requirements: [Scope](scope.md), [Architecture Handoff](architecture-handoff.md)

<a id="pd-026"></a>
## PD-026

Question: Mobile App과 다른 Client 확장을 어떻게 고려하는가?

Status: CLOSED

Decision / approved direction: Trainer·Member 대상 Mobile App은 명시적 Future Direction이다. 현재 App이나 Framework를 선택·구현하지 않는다. Web UI에 Business Logic을 강하게 결합해 다른 Client에서 동일 업무 기능을 이용할 수 없게 만드는 구조를 피해야 한다.

Approval source: 2026-09-17 사용자 제품 방향 변경 지시.

Follow-up: API Architecture는 Architecture 단계, Mobile 기술은 후속 도입 단계에서 결정한다.

Related requirements: [NFR](non-functional-requirements.md#nfr-013), [Architecture Handoff](architecture-handoff.md)

## Product Baseline — 2026-09-17 지점 관계·보상 개정

최신 사용자 확정사항을 반영한 Architecture Input Baseline이다. [현재 결정과 변경 이력](README.md), [권한](users-and-roles.md), [업무 규칙](business-rules.md), [남은 결정 게이트](open-questions.md), [Architecture 인계](architecture-handoff.md)를 함께 따른다. Baseline 갱신은 모든 상세 업무 정책 또는 구현 완료를 뜻하지 않는다.

<a id="pd-027"></a>
## PD-027

Question: 추가실적을 v1에서 어떤 업무로 지원하는가?

Status: CLOSED

Decision / approved direction: Additional Performance는 Trainer에게 인정하는 보상·인센티브이며 v1에 포함한다. 타 지점 지원 수업·회원 유지·기타 인정 실적이 예다. 특정 Session 관련 또는 Session 없는 실적을 지원하고 생성·정정·취소를 감사 가능하게 한다. 고객 결제·매출·가계부 또는 기존 수동 매출과 동일시하지 않는다. 2026-10-10 사용자 정정에 따라 타 지점 수업은 일반 PT 수당 대신 해당 수업의 보상 전체를 Additional Performance로 처리한다. 동일 수업의 일반 Session Payment를 정산에 별도로 합산하지 않는다(MB-009 CLOSED). 타 지점 지원 수업은 보상 금액 없이도 허용된 PT 진행 기록과 Pass 차감을 먼저 완료한다. 권한 있는 관리자가 나중에 수업 건별 금액을 저장할 때 해당 Additional Performance 보상을 확정한다. 금액 미입력은 확정된 0원과 구분하고 누락 건을 추적할 수 있어야 한다. 미입력 건의 추적 표현·정정 연동·진행 기록 연계 상세는 BR-013 OPEN이다.

2026-10-11 사용자 확정(타 지점 지원 수업 보상의 비용 집계 지점 질문의 1번, 복잡도와 적용 범위 설명 후 최종 확인): 타 지점 지원 수업의 전체 보상으로 확정한 Additional Performance 금액은 해당 수업의 실제 Performed Branch 비용으로 집계한다. Trainer 월 정산에는 한 번만 합산하고 기존 금액 입력·정정·확정 권한은 유지한다. 지원 수업 이후 소속 이동만으로 과거 수행 지점에 따른 비용 귀속이 바뀌지 않는다. 수행 지점 비용 귀속을 다른 소속 Trainer의 보상 설정/전체 정산 열람·금액 입력 권한으로 확대하지 않는다. 지원 수업 외 보상 항목의 귀속·비용 보고 공개/집계 상세·지점 간 청구/송금·기본급 자동 배분은 이번에 확정하지 않는다. BR-PAY-015/016, PR-031/010 및 MB-010에 추적한다.

2026-10-11 사용자 확정(회원 유지 등 지원 수업 외 추가실적의 비용 귀속 질문의 1번 답변): 지원 수업 외 Additional Performance의 비용은 실적 발생 당시 대상 Trainer의 Home Branch에 귀속한다. 등록 시점·금액 확정 시점·대상 월말 또는 조회 시점의 소속으로 대체하지 않는다. 수원 소속일 때 발생한 회원 유지 실적 보상 100,000원은 같은 달 말 강남으로 이동하거나 이동 후 등록해도 수원점 비용이다. 금액·월 정산 한 번 합산·기존 관리 권한·이력 보존을 유지한다. 비용 귀속을 등록/정정 인가 기준으로 자동 상속하지 않는다. 지원 수업 외 추가실적 금액 산정·발생 시점/소속 사실 확인 예외·정산 월·남은 정정/취소와 보고 공개/집계 상세는 OPEN이다. BR-PAY-015/016, PR-031/010 및 MB-010에 추적한다.

2026-10-11 사용자 확정(회원 유지 등 지원 수업 외 추가실적의 금액 산정 방식 질문의 1번 답변): 회원 유지 등 지원 수업 외 Additional Performance의 금액도 권한 있는 관리자가 실적 건별로 직접 입력한다. v1에서 유형별 사전 금액·산식으로 자동 계산하는 방식을 채택하지 않으며 일반 RATE/FIXED_AMOUNT 계산 결과로 입력액을 대체하지 않는다. 기존 Master Organization 전체/Branch Admin 대상 Trainer Home Branch 범위·관리 범위 안 본인 등록·별도 승인 없음·감사는 유지한다. 비용은 실적 발생 당시 Trainer Home Branch에 귀속하는 기존 기준을 따른다. 이 결정은 금액 산정 방식에 한정하며 지원 수업 외 실적의 금액 확정 시점·미입력/0원·입력 제약·정산 월·이동 시 등록/정정 인가 시점·Trainer 신청/승인·정정/취소 등 남은 정책은 관련 OPEN이다. 지원 수업에 승인된 기록/차감 후 보상 확정·사유 필수 0원·금액 미입력 월 정산 차단을 다른 실적에 자동 적용하지 않는다.

2026-10-11 사용자 확정(Trainer의 별도 추가실적 신청 기능 질문의 1번 답변): v1 추가실적은 권한 있는 관리자의 직접 등록만 지원하고 Trainer의 시스템 내 별도 신청·승인/반려 흐름은 두지 않는다. Trainer는 실적 내용을 관리자에게 전달하며 기존 Master Admin/Branch Admin이 허용된 관리 범위에서 입력한다. Master Organization 전체/Branch Admin 대상 Trainer Home Branch 범위·관리 범위 안 본인 등록·별도 승인 없음·감사는 유지한다. 관리자·Trainer 겸임자는 관리 권한 범위 안에서 본인에게 직접 등록할 수 있으며 Trainer 역할만으로 등록 권한을 얻지 않는다. Trainer의 실제 PT 진행 기록 등록은 계속 지원하며 이를 추가실적 신청으로 취급하지 않는다. 지원 수업의 진행 기록·Pass 차감 완료 후 관리자 금액 저장 시 보상 확정과 미입력 지원 수업의 해당 Trainer·월 정산 확정 차단은 유지한다. 금액 산정·비용 귀속·기존 정정/확정/조회 권한은 변경하지 않는다. 추가실적의 남은 입력 제약/확정 시점·소속 이동 시 인가 시점·정산 월·정정/취소 등은 관련 OPEN이며 신청 기능의 향후 도입은 별도 결정 대상이다.

2026-10-11 사용자 확정(지원 수업 외 추가실적의 등록 시점 질문의 1번 답변): 회원 유지 등 지원 수업 외 Additional Performance는 권한 있는 관리자가 실적 내용과 금액을 함께 입력해야 등록이 완료된다. 금액 미입력 요청은 등록을 완료할 수 없으며, 금액 없는 실적을 먼저 등록하고 나중에 금액을 입력하는 흐름은 v1에 두지 않는다. 누락 금액을 자동으로 0원이나 계산식 결과로 대체하지 않는다. 기존 관리자 역할/대상 Home Branch 범위·관리 범위 안 본인 등록·별도 승인 없음·감사와 발생 당시 Home Branch 비용 귀속을 유지한다. 지원 수업은 기존대로 PT 진행 기록·Pass 차감을 먼저 완료하고 관리자 금액 저장 시 보상을 확정하며, 미입력 지원 수업의 해당 Trainer·월 정산 확정 차단도 유지한다. 이번 결정은 지원 수업 외 실적의 최초 등록 금액 입력 요건에 한정한다. 0원 허용·금액 범위/정밀도·이동 시 등록/정정 인가 시점·정산 월·수정/취소 등은 관련 OPEN이며 월 정산을 자동 확정하거나 지원 수업의 정산 차단 규칙을 다른 실적에 확장하지 않는다.

2026-10-11 사용자 확정(지원 수업 외 추가실적의 0원 등록 허용 여부 질문의 1번 답변): 회원 유지 등 지원 수업 외 Additional Performance의 등록 금액은 0원보다 큰 양수만 허용한다. 0원과 음수 입력은 등록을 거부하며, 사유를 남겨도 0원으로 등록할 수 없다. 기존대로 내용과 금액을 함께 입력해야 등록이 완료되고 누락 금액을 자동으로 채우지 않는다. 지원 수업의 사유 필수 0원 확정 허용·금액 미입력과 명시적 0원 구분·PT 진행 기록/Pass 차감 선완료 및 미입력 지원 수업 월 정산 확정 차단은 유지한다. 기존 관리자 역할/대상 Home Branch 범위·관리 범위 안 본인 등록·별도 승인 없음·감사와 발생 당시 Home Branch 비용 귀속도 유지한다. 이 결정은 지원 수업 외 실적의 등록 금액에 한정한다. 상한액·정밀도/금액 표현·정산 월·이동 시 인가·정정/취소는 관련 OPEN이며 음수 금액 등록이나 0원 덮어쓰기를 미정 정정/취소 절차의 대체로 도입하지 않는다. 일반 보상 설정·상품·월별 적용 기본급의 금액 제약을 변경하지 않는다.

2026-10-11 사용자 확정(지원 수업 외 추가실적을 반영할 정산 월 질문의 1번 답변): 회원 유지 등 지원 수업 외 Additional Performance는 실제 실적이 발생한 월의 Trainer 월 정산에 귀속한다. 9월에 발생한 실적을 10월에 등록해도 9월분이며 등록 월이나 금액 입력 월로 이월하거나 관리자가 반영 월을 임의 선택하지 않는다. 같은 실적을 9월·10월에 중복 합산하지 않는다. 금액을 함께 입력해야 최초 등록이 완료되고 양수만 허용하는 기존 규칙·관리자 직접 등록/관리 범위 안 본인 등록·승인 생략·감사를 유지한다. 비용은 실적 발생 당시 Trainer Home Branch에 귀속하는 기존 기준을 따르며 발생 월/비용 지점이 등록 권한을 자동 부여하지 않는다. 이 결정은 Trainer 월 정산의 귀속 월 기준에 한정한다. 이미 확정된 발생 월에 뒤늦게 추가하는 허용 여부·확정 해제/재확정·권한/사유·이전 확정본 처리의 상세는 BR-009/013에서 별도 결정하며 확정본을 자동 변경하지 않는다. 발생 시점 식별/월 경계·시간대·소급 등록 허용 기간·이동 시 등록/정정 인가 시점·정정/취소 및 비용 보고의 대상 기간/집계 상세는 관련 OPEN이다. 지원 수업/일반 지급의 남은 월 귀속·마감 정책을 이 결정으로 확정하지 않는다.

2026-10-11 사용자 확정(확정된 월의 누락된 지원 수업 외 추가실적 처리 질문의 1번 답변): 이미 확정된 발생 월의 누락된 지원 수업 외 Additional Performance는 해당 Trainer·월 정산의 확정 해제 → 누락 실적 등록 → 같은 발생 월 재확정으로 반영한다. 이전 확정본은 보존하고 재확정 결과와 구분한다. 확정 상태에 직접 추가하여 이전 확정본을 덮어쓰거나 등록 월/다른 월로 이월하지 않는다. 누락 실적은 기존대로 내용과 양수 금액을 함께 입력하며 관리자 직접 등록 역할/대상 범위·관리 범위 안 본인 등록·승인 생략·감사와 발생 당시 Home Branch 비용 귀속을 유지한다. 재확정은 기존 승인된 확정 조건을 다시 검증하고 미입력 지원 수업이 남으면 해당 Trainer·월을 확정하지 않는다. 누락분 등록만으로 자동 확정하지 않는다. 현재 Rate/Fixed Amount/Base Salary 설정으로 과거 확정 지급이나 적용 기본급을 자동 재계산하지 않는다. 이번 결정은 후등록 순서와 이전 확정본 보존에 한정하며 이 후등록을 위한 확정 해제/재확정의 역할·관리 Scope/소속 기준 시점·본인 건/별도 승인 상세·해제 사유 정책은 관련 OPEN이다. 발생 시점 식별/월 경계·소급 기간·금액 상한/정밀도·기존 실적 수정/취소와 각 단계 실패/재시도·UoW·동시성/버전 표현은 별도 정책 또는 Architecture 설계 대상이다.

2026-10-11 사용자 확정(지원 수업 외 실적 등록·누락 후등록의 이동 후 담당 관리자 질문의 1번 답변 및 재확인): 지원 수업 외 Additional Performance의 등록과, 확정된 발생 월의 누락분 반영을 위한 해당 Trainer·월 정산 확정 해제·재확정은 Master Admin에게 Organization 전체, Branch Admin에게 각 업무 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 등록·해제·재확정 요청마다 현재 소속과 관리 권한을 검증하고 최초 단계의 소속으로 후속 권한을 고정하지 않는다. 이전 소속·실적 발생 당시 소속·Performed Branch·클라이언트가 전달한 Branch Context만으로 권한을 부여하지 않는다. 9월 수원점 소속 때 발생한 회원 유지 실적을 10월 강남점 이동 후 처리하면 강남점 Branch Admin/Master가 담당하고, 별도 Master 권한 없는 이전 수원점 Branch Admin은 처리할 수 없다. 실적은 여전히 9월 정산·수원점 비용이며 이전 확정본과 감사 이력을 보존한다. 등록의 내용+양수 금액 필수·관리 범위 안 본인 등록·별도 승인 없음과 재확정의 기존 확정 조건/미입력 지원 수업 차단을 유지한다. 이 결정은 위 등록 및 누락분 후등록의 역할·관리 범위·소속 기준 시점에 한정한다. 누락분 반영을 위한 해제·재확정의 본인 건 처리/별도 승인·해제 사유 정책, 지원 수업 외 기존 실적의 정정/취소 권한·소속 기준 및 처리 절차는 별도 OPEN이다. 기존 지원 수업 보상/기본급 정정 권한이나 비용/조회 범위를 확대하지 않는다.

2026-10-11 사용자 확정(누락 실적 반영을 위한 정산 확정 해제 사유 질문의 1번 답변): 확정된 발생 월의 누락된 지원 수업 외 Additional Performance를 반영하기 위해 해당 Trainer·월 정산의 확정을 해제할 때 사유를 필수로 기록한다. Master Admin과 Branch Admin의 허용된 해제에 동일하게 적용하며 사유 없는 해제 요청은 거부한다. 거부 시 요청 직전의 확정 상태·확정본·기존 실적과 정산 구성/금액을 유지한다. 해제 성공 시 대상 Trainer·월, 해제 사유·처리자·처리 시점을 감사 가능한 이력으로 남기고 이전 확정본을 보존한다. 예를 들어 9월 회원 유지 실적 누락 반영을 사유로 식별할 수 있어야 한다. 각 처리 시점 현재 Home Branch 인가·해제 → 누락 등록 → 같은 월 재확정·발생 월 정산/발생 당시 Home Branch 비용 귀속과 재확정 조건을 유지한다. 이번 결정은 누락분 반영의 확정 해제 사유 필수에 한정하며 이 흐름의 해제/재확정 본인 건 처리·별도 승인 여부와 기존 실적 정정/취소 등 남은 정책은 별도 OPEN이다. 등록 사유/내용을 해제 사유로 자동 대체하거나 별도 승인 정책을 임의 확정하지 않는다.

2026-10-11 사용자 확정(Branch Admin의 본인이 아닌 소속 Trainer 누락 실적 반영 시 Master 승인 질문의 1번 답변): Branch Admin이 본인이 아닌 소속 Trainer의 확정된 발생 월 누락 실적(지원 수업 외 Additional Performance)을 반영할 때, 해당 Trainer·월 정산의 확정 해제·재확정에 별도 Master 승인을 두지 않는다. 각 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인지 검증한 후 Master 승인 대기 없이 직접 처리한다. 해제 사유 필수·사유 없는 요청 거부와 요청 직전 확정 상태/금액 보존, 해제 → 내용과 양수 금액을 갖춘 누락 실적 등록 → 같은 발생 월 재확정 순서, 이전 확정본·처리 이력/감사 보존을 유지한다. 재확정은 기존 확정 조건을 다시 검증하고 미입력 지원 수업이 남으면 해당 Trainer·월을 확정하지 않는다. 승인 생략은 자동 등록/재확정이나 관리 범위 밖 접근을 허용하지 않는다. 발생 월 정산·발생 당시 Home Branch 비용 귀속과 과거 지급/적용 기본급 보존은 유지한다. 이번 결정은 Branch Admin의 본인이 아닌 소속 Trainer 건에 한정하며 관리자 본인의 누락 실적 반영을 위한 해제/재확정 허용 및 해당 본인 건의 별도 승인 정책은 OPEN이다. 이미 승인된 관리 범위 안 본인 실적 등록·기존 지원 수업 보상/기본급 정정 정책은 변경하지 않는다. 기존 비지원 실적 정정/취소·나머지 수명/입력 정책과 구체 계약/UoW/동시성은 별도 결정 또는 설계 대상이다.

2026-10-11 사용자 확정(관리자·Trainer 겸임자의 본인 누락 실적 반영을 위한 확정 해제·재확정 질문의 1번 답변): 관리자·Trainer 겸임자는 관리 권한 범위 안에서 본인의 확정 월 누락 실적(지원 수업 외 Additional Performance)을 반영하기 위한 정산 확정 해제·재확정을 별도 승인 없이 직접 처리할 수 있다. Master Admin은 Organization 범위 안의 본인 건, Branch Admin은 각 처리 시점 본인 Trainer의 현재 Home Branch가 자신의 관리 Branch와 일치하는 경우 허용한다. Actor와 대상 Trainer가 동일인이어도 해제 사유 필수·사유 누락 거부/요청 직전 상태 보존·처리 이력과 감사·이전 확정본 보존은 동일하게 적용한다. Trainer 역할만으로는 본인 정산을 해제/재확정할 수 없으며 관리자 권한/Scope와 현재 소속을 요청마다 검증한다. 해제 → 내용과 양수 금액을 갖춘 누락 실적 등록 → 동일 발생 월 재확정 순서와 발생 당시 Home Branch 비용 귀속을 유지한다. 재확정은 기존 승인 조건을 다시 검증하고 미입력 지원 수업이 남으면 차단하며 본인 건/승인 생략을 이유로 자동 확정하거나 검증을 생략하지 않는다. 기존 비지원 실적 정정/취소·발생 시점/월 경계·소급 기간·나머지 금액 제약은 별도 OPEN이며 구체 계약/저장/단계별 UoW·실패/재시도·이동 경합은 PROPOSED다.

2026-10-11 사용자 확정(정산 확정 전 지원 수업 외 추가실적 금액 수정 권한 질문의 1번 답변): 월 정산 확정 전, 이미 등록한 회원 유지 등 지원 수업 외 Additional Performance의 금액 수정은 Master Admin에게 Organization 전체, Branch Admin에게 수정 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안 관리자·Trainer 겸임자의 본인 건도 포함하며 Master/다른 관리자의 별도 승인 없이 직접 수정한다. 모든 금액 수정에 변경 사유가 필수이고 변경 전후 금액·변경 사유·수정 Actor·처리 시점을 감사 가능한 이력으로 남긴다. 사유 없는 수정 요청은 거부하고 요청 직전 금액·기존 이력·정산 입력 상태를 유지한다. 현재 권한·관리 Scope·대상 Trainer의 현재 소속을 각 요청에서 검증하며 이전 소속/실적 발생 당시 소속·Performed Branch·위조 Branch Context/직접 ID만으로 권한을 부여하지 않는다. 관리자 권한 없는 Operator/Trainer는 본인 건도 수정할 수 없다. 실적 발생 월 정산·발생 당시 Home Branch 비용 귀속과 이전 이력을 유지하고 금액 수정만으로 PT 진행 사실/Pass 차감이나 과거 일반 지급·적용 기본급을 변경하지 않는다. 이번 결정은 확정 전 금액 수정의 역할·Scope·현재 소속 기준·본인 건·별도 승인 없음·사유/이력에 한정한다. 수정 금액의 0원/음수 허용·상한/정밀도, 금액 외 정보 수정·취소 및 확정된 월의 금액 정정/해제·재확정 상세는 별도 OPEN이며 기존 누락 실적 후등록 정책과 구분한다. 구체 입력/저장 계약·UoW·실패/재시도·소속 이동/정산 확정 경합은 PROPOSED다.

2026-10-11 사용자 확정(상황이 달라도 이전 선택지를 참고해 같은 답으로 진행하라는 지시): 유사 상황은 이전 사용자 선택을 참고해 같은 기준으로 진행하라는 지시에 따라, 지원 수업 외 Additional Performance의 최초 등록 금액 > 0 기준을 월 정산 확정 전 금액 수정에도 동일하게 적용한다. 수정 후 금액은 양수만 허용하고 0원·음수·금액 누락 요청은 거부하며 사유를 남겨도 0원 수정 예외를 두지 않는다. 거부 시 요청 직전 금액·이력·정산 입력 상태를 유지한다. 허용된 수정에도 기존 Master Organization/Branch Admin 수정 시점 현재 Home Branch 인가·관리 범위 안 본인 건 허용·별도 승인 없음·변경 사유 필수와 전후 금액/사유/수정자/시점 이력·감사를 적용한다. 발생 월 정산·발생 당시 Home Branch 비용 귀속과 과거 확정 지급/적용 기본급 보존을 유지한다. 지원 수업 보상의 사유 필수 0원 확정/수정과 월별 수동 적용 기본급의 사유 필수 0원 지정은 기존 승인 범위대로 유지한다. 금액 상한·정밀도/표현을 새로 정하거나 0원 덮어쓰기/음수 입력을 실적 취소 절차의 대체로 도입하지 않는다. 확정 후 금액 정정·금액 외 정보 수정/취소 등 남은 정책 및 구체 계약/저장/UoW·실패/재시도·동시성은 별도 결정 또는 설계 대상이다.

2026-10-11 사용자 일관성 지시 적용(기존 지원 수업 보상·기본급의 확정 월 금액 오류 처리 재사용): 유사 상황에 이전 선택을 적용하라는 사용자 지시에 따라 지원 수업 보상/기본급의 확정 월 금액 오류 정정 흐름을 지원 수업 외 Additional Performance에도 적용한다. 확정된 발생 월 실적의 금액 오류는 해당 Trainer·월 확정 해제 → 해당 실적 금액 정정 → 같은 발생 월 재확정으로 처리하고 이전 확정본과 당시 적용 구성/금액/합계·정정 전후 이력을 보존한다. Master Admin은 Organization 전체, Branch Admin은 각 해제/정정/재확정 처리 시점 대상 Trainer의 현재 Home Branch가 관리 Branch인 경우 허용한다. 관리 범위 안 관리자·Trainer 겸임자의 본인 건도 포함하고 별도 Master/다른 관리자 승인 대기를 두지 않는다. 해제와 금액 정정 모두 사유가 필수이며 사유 없는 각 요청은 요청 직전 상태·금액·확정본/이력을 유지하고 거부한다. 해제 사유/처리자/시점과 정정 전후 금액/사유/수정자/시점을 감사 가능한 이력으로 남긴다. 정정 금액도 기존 등록/확정 전 수정과 동일하게 양수만 허용하며 0원·음수·금액 누락 요청은 사유가 있어도 거부한다. 재확정은 기존 승인 조건을 다시 검증하고 금액 미입력 지원 수업이 남으면 해당 Trainer·월을 확정하지 않는다. 정정 저장만으로 자동 재확정하지 않으며 현재 Rate/Fixed Amount/Base Salary로 과거 일반 지급/적용 기본급을 재계산하지 않는다. 실적의 발생 월 정산과 발생 당시 Home Branch 비용 귀속을 유지하고 다른 월/Trainer나 PT 진행 사실·Pass를 변경하지 않는다. 예를 들어 다른 구성 금액이 같고 기존 실적 100,000원을 120,000원으로 정정하면 이전 9월 확정 합계 3,850,000원을 보존하며 새 9월 합계는 3,870,000원이다. 금액 외 정보 수정·실적 취소·발생 시점 식별/월 경계·소급 기간·나머지 금액 제약은 별도 OPEN이다. 각 단계 계약/저장/버전·UoW·실패/재시도·이동/정산 경합은 PROPOSED이며 전체 흐름을 임의의 단일 commit으로 정하지 않는다.

2026-10-11 사용자 명확화(“따로 회원 유지 보상이라기 보다 기존에 있는 기능인 추가 실적으로 관리자가 지급한다.”): 회원 유지는 기존 Additional Performance의 지급 사유의 예시이며 별도 보상 제도를 만들지 않는다. 권한 있는 관리자가 실적 건별 내용·금액을 입력하고 월 정산에 반영하는 기존 정책을 유지한다. 사유별 자동 산정이나 회원 유지율 평가 기능을 추가하지 않는다. 발생 월·비용 귀속의 기존 결정은 유지하며, 이 답변을 직전 발생일/월 전체 성과 질문의 선택으로 해석하지 않는다.

2026-10-11 사용자 확정(“모든 보상”의 범위 확인 질문의 1번): 일반 PT 수당(Session Payment)의 기존 RATE/FIXED_AMOUNT 자동 계산·확정과 기본급(Base Salary)의 별도 월 정산 반영은 유지한다. 그 외 타 지점 지원 수업·회원 유지·기타 보상은 모두 권한 있는 관리자가 기존 Additional Performance에 직접 입력한다. 지급 사유별로 별도 보상 제도나 자동 산정 기능을 만들지 않는다. 기존 관리자 Scope·입력 제약·정정/감사 정책을 유지하며, 타 지점 지원 수업에는 일반 Session Payment를 중복 합산하지 않는다.

2026-10-11 사용자 확정(수업 취소 시 그 수업의 추가실적 보상 처리 질문의 1번): 허용된 PT 진행 기록 취소 시 해당 수업의 보상으로 입력한 Additional Performance도 함께 자동 무효 처리한다. 해당 보상은 유효한 Trainer 월 정산 및 지점 비용 집계에서 제외하며 기존 금액·원본과 취소/변경 이력은 보존한다. 금액을 0원으로 덮어쓰거나 관리자의 별도 추가실적 취소를 기다리는 방식이 아니다. 수행 지점 관리자가 기존 권한으로 해당 수업을 취소하면 그 수업 보상의 무효 처리가 동반되지만, 보상 금액의 입력/임의 수정이나 다른 소속 Trainer의 보상 설정·전체 정산 조회 권한을 추가로 얻지는 않는다. 수업과 무관한 다른 추가실적까지 무효 처리하지 않는다. 확정 월은 기존 현재 Home Branch 담당자 해제 → Performed Branch 담당자 취소 → 현재 Home Branch 담당자 같은 월 재확정 순서와 이전 확정본 보존을 따른다. 등록 금액의 관리자 직접 입력·기존 해제 사유/감사·재확정 조건은 유지한다. 상태 저장/계산 표현·모듈 계약·필수 변경/감사의 원자성·실패/재시도/동시성은 후속 Architecture 설계·검증 대상이며 다른 정정/취소의 나머지 정책은 OPEN이다.

2026-10-11 사용자 확정(일반/지원 구분 시점 질문의 1번): 실제 수업 당시 Trainer Home Branch와 Performed Branch를 비교해 일반 PT/타 지점 지원 수업을 구분한다. 이동 후 늦게 등록해도 당시 구분을 유지한다. 일반 PT 지급 설정의 기록 생성 시점·현재 Home Branch 기준 관리 권한은 유지하며 당시 소속 확인 예외/사실 정정의 보상 전환은 후속 OPEN이다(BR-OPS-001, PR-008, MB-001/005).

Approval source: 2026-09-17 최신 사용자 확정; 2026-10-10 추가실적 직접 등록 역할 질문의 1번 답변과 대상 범위 질문의 2번 답변. Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer의 추가실적만 직접 등록한다. 타 지점 수업도 Trainer 소속 지점 관리자 또는 Master가 등록하며 지원받은 지점이라는 이유만으로 등록 권한을 주지 않는다.

추가 사용자 확정(2026-10-10, 별도 승인 질문의 1번 답변): Branch Admin이 본인이 아닌 자기 지점 소속 Trainer의 추가실적을 직접 등록할 때는 별도 Master 승인이 필요 없다. Master 승인 대기를 추가하지 않으며 생성·변경 감사는 유지한다. Trainer 신청 승인·월 정산 확정으로 확대하지 않는다. 본인 건은 아래의 후속 결정을 따른다.

추가 사용자 확정(2026-10-10, 본인 등록 질문의 2번 답변): 관리자·Trainer 겸임자도 관리 범위 안이면 본인의 추가실적을 직접 등록할 수 있다. Master Admin은 Organization 범위 안의 본인, Branch Admin은 본인 Trainer Home Branch가 관리 Branch와 같을 때 허용하며 다른 Branch이면 거부한다. 동일한 감사 요구를 적용한다. 본인 건의 별도 승인 여부는 아래의 후속 사용자 결정으로 확정했다.

추가 사용자 확정(2026-10-10, 본인 건 승인 질문의 1번 답변): 관리 범위 안에서 직접 등록한 본인의 추가실적도 별도 승인 없이 처리한다. Master나 다른 관리자의 승인 대기를 추가하지 않으며 관리 범위 검증·동일한 생성/변경 감사·Actor/대상 동일인 추적을 유지한다. Trainer 신청 승인·월 정산 확정 및 금액·확정 시점으로 확대하지 않는다.

추가 사용자 확정(2026-10-10, 타 지점 지원 수업 금액 계산 질문의 3번 답변): 권한 있는 관리자가 수업 건별 보상 금액을 직접 입력한다. 입력 금액 전부를 Additional Performance로 반영하며 일반 RATE/FIXED_AMOUNT 결과나 지원 전용 고정금액을 자동 지급액으로 사용하지 않는다. 등록자 Home Branch 범위·관리 범위 안 본인 등록·승인 생략·감사 및 PT 진행 기록·Pass 차감은 유지한다. 다른 추가실적의 금액 산정·입력/확정 시점·입력값 범위를 확정한 것은 아니다.

추가 사용자 확정(2026-10-10, 진행 기록과 보상 확정 시점 질문의 1번 답변): 타 지점 지원 수업은 보상 금액 없이도 허용된 PT 진행 기록과 Pass 차감을 먼저 완료한다. 권한 있는 관리자가 나중에 수업 건별 금액을 저장할 때 해당 Additional Performance 보상을 확정한다. 금액 미입력은 확정된 0원과 구분하고 누락 건을 추적할 수 있어야 한다. 일반 Session Payment의 등록 시 계산·확정 규칙은 유지한다. 관리자 역할·Home Branch 범위·본인 등록·별도 승인 없음·감사 정책도 유지한다. 당시 미결정이었던 금액 미입력 월의 정산 확정 조건은 아래 후속 사용자 결정으로 해결했다. 월 귀속·마감 이후 처리의 남은 세부 정책은 OPEN이다.

2026-10-10 사용자 확정(금액 미입력 지원 수업이 남은 월의 정산 확정 질문의 1번 답변): 해당 Trainer의 해당 월 정산 대상 지원 수업에 금액 미입력 건이 하나라도 있으면 그 Trainer·월 정산을 확정할 수 없다. 미입력 수업을 제외하거나 0원으로 간주해 확정하지 않는다. 이미 완료한 진행 기록·Pass 차감은 유지한다. 차단 범위는 해당 Trainer·월이며 다른 Trainer·월로 확대하지 않는다. 모든 금액 입력 완료는 이 차단 조건의 해소이며 월 정산 자동 확정이나 나머지 확정 조건의 충족을 뜻하지 않는다. 최초 월 정산 확정 권한과 별도 Master 승인 없음은 2026-10-11 후속 사용자 결정으로 확정했다. 월 귀속·나머지 확정 조건·확정/마감 절차와 남은 정정/취소 및 남은 마감 이후 처리는 OPEN을 유지한다. 당시 미결정이었던 지원 수업 0원 허용은 후속 사용자 결정으로 해결했다.

2026-10-10 사용자 확정(타 지점 지원 수업 보상 0원 허용 질문의 2번 답변): 타 지점 지원 수업 보상은 권한 있는 관리자가 사유를 기록하면 0원으로 명시적으로 확정할 수 있다. 사유 없는 0원 입력은 보상 확정이 불가하다. 사유를 남기고 확정한 0원은 금액 미입력이 아니므로 그 건으로 월 정산 확정을 차단하지 않는다. 다른 미입력 건이 남으면 기존 차단 조건을 유지한다. 기존 관리자 역할·Home Branch Scope·관리 범위 안 본인 등록·별도 승인 없음·감사 정책을 따른다. 미입력을 자동 0원으로 바꾸지 않으며 0원 확정으로 진행 기록을 취소하거나 Pass 차감을 복원하지 않는다. 월 정산 자동 확정이나 나머지 확정 조건의 충족을 뜻하지 않는다. 일반 Session Payment/서비스 PT 계산이나 다른 추가실적의 0원 허용으로 확대하지 않는다.

2026-10-10 사용자 확정(월 정산 확정 전 지원 수업 보상 금액 수정 권한 질문의 1번 답변): 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin에게 Organization 전체, Branch Admin에게 대상 Trainer Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안의 본인 건도 허용하고 변경 이력을 남긴다. 당시 결정은 수정 역할·대상 범위·본인 건 허용·변경 이력에 한정했다. 별도 승인 없음과 저장 즉시 반영은 아래 후속 사용자 결정으로 확정했다. 수정 금액을 0원으로 확정할 때는 기존 사유 필수 정책을 유지한다. 금액 수정만으로 PT 진행 사실·Pass 차감을 취소/복원하거나 일반 Session Payment를 현재 설정으로 재계산하지 않는다. 다른 추가실적 수정 권한과 지원 수업 보상 정정 외 소속 이동 시 권한 기준 시점은 미정이다. 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin·Branch Admin 모두 관리 범위 안에서 본인 건을 포함해 별도 승인 없이 저장 성공 즉시 반영한다. Master나 다른 관리자의 승인 대기를 두지 않으며 권한 검증과 변경 이력을 유지한다. 월 정산 확정 전 지원 수업 보상 금액의 모든 수정에는 변경 사유가 필수다. 양수 간 변경·0원에서 양수로 변경·양수에서 0원으로 변경 모두 적용하며, 사유 없이는 금액을 수정할 수 없다. 변경 전후 금액·변경 사유·수정자·수정 시점을 이력으로 남긴다. 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer의 지원 수업 보상 정정을 위해 월 정산을 확정 해제·재확정할 때는 Master의 별도 승인을 두지 않는다. Master 승인 대기 단계 없이 관리 범위 안에서 직접 처리하며 이전 확정본과 해제·재확정 이력 및 감사를 유지한다. 지원 수업 보상 정정의 월 정산 확정 해제에는 사유가 필수이며, 사유 없이 해제할 수 없다. 사유·해제자·시점을 이력으로 남긴다. 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 남은 정정·취소 절차는 BR-009/013 등 관련 OPEN을 따른다.

2026-10-10 사용자 확정(월 정산 확정 전 지원 수업 보상 수정의 별도 승인·저장 즉시 반영 질문의 1번 답변): 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin·Branch Admin 모두 관리 범위 안에서 본인 건을 포함해 별도 승인 없이 저장 성공 즉시 반영한다. Master나 다른 관리자의 승인 대기를 두지 않으며 권한 검증과 변경 이력을 유지한다. Master의 Organization 전체·Branch Admin의 대상 Trainer Home Branch 기준 범위는 유지한다. 수정 금액을 0원으로 확정할 때는 기존 사유 필수 정책을 적용한다. 금액 수정만으로 진행 기록·Pass 차감을 취소/복원하거나 월 정산을 자동 확정하지 않는다. 다른 추가실적 수정과 확정된 월 정산의 정정 정책으로 확대하지 않는다. 월 정산 확정 전 지원 수업 보상 금액의 모든 수정에는 변경 사유가 필수다. 양수 간 변경·0원에서 양수로 변경·양수에서 0원으로 변경 모두 적용하며, 사유 없이는 금액을 수정할 수 없다. 변경 전후 금액·변경 사유·수정자·수정 시점을 이력으로 남긴다. 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer의 지원 수업 보상 정정을 위해 월 정산을 확정 해제·재확정할 때는 Master의 별도 승인을 두지 않는다. Master 승인 대기 단계 없이 관리 범위 안에서 직접 처리하며 이전 확정본과 해제·재확정 이력 및 감사를 유지한다. 지원 수업 보상 정정의 월 정산 확정 해제에는 사유가 필수이며, 사유 없이 해제할 수 없다. 사유·해제자·시점을 이력으로 남긴다. 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 남은 정정·취소 절차는 BR-009/013 등 관련 OPEN을 따른다.

2026-10-10 사용자 확정(월 정산 확정 전 지원 수업 보상 금액 수정의 변경 사유 질문의 1번 답변): 월 정산 확정 전 지원 수업 보상 금액의 모든 수정에는 변경 사유가 필수다. 양수 간 변경·0원에서 양수로 변경·양수에서 0원으로 변경 모두 적용하며, 사유 없이는 금액을 수정할 수 없다. 변경 전후 금액·변경 사유·수정자·수정 시점을 이력으로 남긴다. 기존 관리자 역할·Home Branch 범위·관리 범위 안 본인 건 허용·별도 승인 없음·저장 성공 즉시 반영은 유지한다. 일반 Session Payment, 다른 종류의 추가실적 및 월 정산 확정 이후 정정 정책으로 확대하지 않는다. 구체 사유 입력·저장 형식은 후속 설계한다.

2026-10-10 사용자 확정(월 정산 확정 후 지원 수업 보상 오류 처리 질문의 2번 답변): 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 이전 확정본의 적용 기본급·구성 금액·합계를 덮어쓰거나 삭제하지 않으며 이전본과 재확정본을 구분한다. 예를 들어 9월 지원 수업 보상 30,000원의 오류를 35,000원으로 정정할 때 9월 정산의 확정 해제 → 지원 수업 보상 금액 정정 → 9월 정산 재확정으로 처리하고 이전 30,000원 반영 확정본을 보존한다. 금액 정정 시 PT 진행 사실·Pass 차감을 재실행하거나 현재 Rate/Fixed Amount/Base Salary를 이유로 과거 확정 일반 지급·기본급을 자동 재계산하지 않는다. 재확정에도 해당 Trainer·월의 미입력 지원 수업 차단 등 승인된 확정 조건을 적용한다. 이번 결정은 지원 수업 보상 금액 오류의 정정 경로와 이전 확정본 보존에 한정한다. 당시 미결정이었던 지원 수업 정정의 해제·재확정 권한은 아래 후속 사용자 결정으로 확정했다. 다른 정정/취소 및 실제 지급과의 대사·차액 처리 상세는 미정이다.

2026-10-10 사용자 확정(지원 수업 보상 정정의 월 정산 확정 해제·재확정 권한 질문의 2번 답변): 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. 수업의 Performed Branch만으로 다른 Home Branch Trainer의 정산 확정 해제·재확정 권한을 얻지 않는다. 관리자 권한이 없는 Operator·Trainer는 이 작업을 수행할 수 없다. 해당 Trainer·월의 확정 해제 → 금액 정정 → 동일 월 재확정과 이전 확정본 보존은 유지한다. 이 결정은 지원 수업 보상 금액 오류 정정에 한정하며 최초 월 정산 확정 권한이나 전체 정산 공개 범위(MB-006)를 새로 확정하지 않는다. 위 지원 수업 보상 정정의 현재 Home Branch 권한 기준은 아래 후속 사용자 결정으로 확정했다.

2026-10-10 사용자 확정(지점 관리자의 지원 수업 보상 정정 시 월 정산 확정 해제·재확정의 별도 승인 질문의 1번 답변): Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer의 지원 수업 보상 정정을 위해 월 정산을 확정 해제·재확정할 때는 Master의 별도 승인을 두지 않는다. Master 승인 대기 단계 없이 관리 범위 안에서 직접 처리하며 이전 확정본과 해제·재확정 이력 및 감사를 유지한다. 기존 Master Organization 범위·Branch Admin 대상 Trainer Home Branch 기준과 범위 밖 접근 거부는 유지한다. 해당 Trainer·월의 확정 해제 → 금액 정정 → 동일 월 재확정 순서와 재확정 시 미입력 지원 수업 차단 등 승인된 확정 조건도 유지한다. 이번 결정은 위 정정의 별도 Master 승인 생략에 한정하며 최초 월 정산 확정 권한/승인, Trainer 신청 승인, 다른 정정/취소 또는 정산 공개 범위로 확대하지 않는다. 확정 해제 사유 필수는 아래 후속 사용자 결정으로 확정했다. 위 지원 수업 보상 정정의 현재 Home Branch 권한 기준은 아래 후속 사용자 결정으로 확정했다.

2026-10-10 사용자 확정(지원 수업 보상 정정 시 월 정산 확정 해제 사유 질문의 1번 답변): 지원 수업 보상 정정의 월 정산 확정 해제에는 사유가 필수이며, 사유 없이 해제할 수 없다. 사유·해제자·시점을 이력으로 남긴다. Master Admin·Branch Admin 모두에 적용한다. 기존 Master Organization 범위·Branch Admin 대상 Trainer Home Branch 기준, Branch Admin의 별도 Master 승인 없음, 이전 확정본 보존과 해제·정정·동일 월 재확정 경로를 유지한다. 금액 수정의 변경 사유 필수도 유지한다. 사유 없는 해제 요청은 기존 확정 상태·확정본·보상 금액을 변경하지 않는다. 이번 결정은 위 지원 수업 보상 정정의 확정 해제에 한정하며 다른 정정/취소 정책으로 확대하지 않는다. 구체 입력 화면·저장 구조는 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(지점 이동 후 과거 지원 수업 보상 정정·정산 해제/재확정의 Home Branch 기준 질문의 1번 답변): 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 9월 수원 소속 Trainer가 10월 강남으로 이동한 뒤 9월 지원 수업 보상을 정정하는 예에서는 강남 Branch Admin에게 해당 정정과 월 정산 확정 해제·재확정을 허용하고, 별도 Master 권한이 없는 수원 Branch Admin에게는 과거 소속만을 근거로 허용하지 않는다. 과거 수업의 Performed Branch·수업 사실·이전 확정본·기존 이력은 보존한다. 기존 관리 범위 검증·Branch Admin의 별도 Master 승인 없음·금액 수정 사유 및 확정 해제 사유 필수·감사 정책을 유지한다. 이번 결정은 지원 수업 보상 금액 정정과 해당 월 정산 해제/재확정의 인가 기준에 한정한다. 다른 추가실적 최초 등록/정정의 이동 기준, Trainer 이동 자체의 적용 시점·절차, 비용 귀속·정산 공개(MB-010/006)는 미결정으로 남긴다. 당시 미정이었던 최초 월 정산 확정 권한과 별도 Master 승인 없음은 2026-10-11 후속 사용자 결정으로 확정했다.

Follow-up: BR-013의 Operator의 남은 업무 권한, 지원 수업 외 실적의 금액 외 정보 수정/취소의 소속 이동 시 권한 기준 시점·지원 수업 외 추가실적의 남은 입력 제약·금액 미입력 건의 추적 표현·정정 연동·진행 기록 연계 상세·나머지 정정/취소, MB-010/006 귀속의 남은 예외·비용 보고 공개/집계 상세. 관리자 직접 등록 역할·Home Branch 기준 대상 범위·타인 직접 등록에 대한 위 범위의 Master 승인 없음·관리 범위 안 본인 직접 등록 및 본인 건 별도 승인 없음·타 지점 지원 수업 금액의 관리자 건별 수동 입력·진행 기록/차감 후 금액 저장 시 보상 확정·미입력과 확정 0원 구분·미입력 건이 남은 해당 Trainer·월 정산 확정 차단·사유 필수의 지원 수업 0원 확정 허용·월 정산 확정 전 지원 수업 금액 수정의 관리자 대상 범위/본인 건 허용/변경 이력·본인 건 포함 수정의 별도 승인 없음/저장 즉시 반영·해당 모든 수정의 변경 사유 필수·지원 수업 금액 오류의 해당 월 확정 해제/정정/재확정과 이전 확정본 보존·지원 수업 정정 시 Master Organization/Branch Admin 대상 Trainer Home Branch 기준 해제·재확정 권한·해당 Branch Admin 정정의 별도 Master 승인 없음·지원 수업 정정의 확정 해제 사유 필수 기록·지원 수업 정정의 처리 시점 현재 Home Branch 인가 기준 및 MB-009 보상 구성은 해결됨. 본인 등록은 보상 설정에서 자동 상속한 것이 아닌 별도 사용자 결정이다.

Related requirements: [PR-031](requirements.md#pr-031), PR-010/027; BR-PAY-015.

<a id="review-20261012-batch"></a>
## 2026-10-12 일괄 승인 — B1–B7 / A1–A10

2026-10-12 사용자 일괄 승인: “A4,5번은 2번. 나머지 전부 1번. A1은 v1에서 1번으로 진행하되 추후 버전에서 jwt사용을 고려.” 직전 질문 목록의 B1–B7/A1–A10에 대한 답변이며 다른 D/F/O 항목 전체의 승인이 아니다.

| 질문 ID | 선택 | 항목 | 승인된 정책 | 남은 상세/게이트 |
| --- | --- | --- | --- | --- |
| B1 | 1 | Trainer 재활성화 | Master 자신의 Organization 전체 또는 처리 시점 Trainer 현재 Home Branch의 Branch Admin이 허용한다. 현재 Caller/대상 사실을 Backend에서 검증하며 Trainer 업무 상태 복구와 계정 전체 복구·관리 Scope 변경을 구분한다. | 재활성화의 공개 계약·상태 조합/개별 지원 관계·경합 |
| B2 | 1 | 다른 활성 역할 없는 비활성 Trainer 로그인 | 다른 활성 역할이 없는 비활성 Trainer는 로그인할 수 없고 재활성화 후 이용한다. 관리자 겸임자의 독립 현재 관리자 역할/Scope는 유지한다. 비활성 Trainer 본인의 과거 PT 읽기 예외는 추가하지 않는다. | 계정 전체 DISABLED와 구분한 로그인/Caller 상태 처리·기존 인증/재활성화 경합 |
| B3 | 1 | 새 Pass 최초 담당 | 새 Pass 발급에는 실제 활성 Trainer 지정이 필수다. 담당 미지정 발급을 v1 기본 경로로 제공하지 않는다. 같은 Organization의 다른 Home Branch Trainer도 기존 조건 안에서 지정할 수 있다. | 발급용 최소 선택 계약·나머지 계정/Branch/Pass 상태 조건 |
| B4 | 1 | 새 Pass 최초 횟수 | 상품의 Session Count를 그대로 최초 부여한다. 발급 중 임의 횟수 입력 대신 허용된 관리자의 별도 횟수 조정으로 예외를 처리한다. 발급 조건/원본 총횟수는 보존한다. | 상품 횟수의 나머지 입력 범위·조정 상태/수량 제약 |
| B5 | 1 | 발급 횟수 초과 추가 조정 | 기존 인가된 관리자는 최초 발급 횟수를 넘도록 잔여 횟수를 추가할 수 있다. 추가 횟수에도 기존 회당 지급 계산을 적용하고 사유·전후 잔여/증감·Actor/시점 이력과 감사를 남긴다. 원본 상품 가격/총횟수·과거 지급은 변경하지 않는다. | 음수 등 나머지 수량/목적·상태 제약, 저장/UoW·차감/복원 경합 |
| B6 | 1 | 기존 데이터가 있는 Branch 비활성화 | 기존 Member/Trainer/Pass가 남아 있어도 Master가 지점을 비활성화할 수 있다. 해당 지점의 신규 배정·새 Pass 발급·새 실제 수업은 차단하고 기존 소속·Pass·잔여/이력은 보존한다. 자동 소속 이동·잔여 소멸·과거 정산 삭제는 없다. | 비활성 지점의 과거 업무/조회·로그인/관리·재활성화와 다른 상태 조합·경합 |
| B7 | 1 | 수업 날짜/월 정산 시간대 | Organization 전체의 업무 날짜와 월 경계는 한국 시간(Asia/Seoul)으로 통일한다. 지점/사용자 기기별 시간대를 월 경계로 사용하지 않는다. | 진행일 정밀도·입력/저장 계약, 소속 변경/비활성 시점 비교·과거 오류 정정 |
| A1 | 1 + 후속 재검토 | v1 인증 방식 | v1은 PostgreSQL 서버 저장 AuthSession + 무작위 opaque 식별자 Cookie를 채택한다. JWT는 후속 버전의 재검토 후보로 남기며 도입/전환을 미리 확정하지 않는다. | 라이브러리/해시 비용·쿠키/CSRF 상세·저장/잠금/검증·후속 JWT 별도 ADR |
| A2 | 1 | Login ID | 이메일과 별개인 영문·숫자 중심의 3~64자 Login ID를 사용한다. 이메일을 필수 로그인 식별자로 채택하지 않는다. | 허용 구분자/대소문자·정규화·변경/재사용의 구체 계약 |
| A3 | 1 | 비밀번호 | 15~128자, 문자 종류 조합 강제와 주기적 변경 강제 없이 흔한 비밀번호를 차단한다. 비밀번호 전용 해시/평문 금지의 기존 요구는 유지한다. | Unicode/길이·정규화 계약과 차단목록의 적합한 공급·호환/비용 검증 |
| A4 | 2 | 최초 비밀번호 설정 링크 | 최초 설정 링크는 30분 유효·단일 사용이며 재발급 시 이전 링크를 폐기한다. 기존 대상자 본인 설정/허용된 계정 발급·전달 흐름을 유지한다. 24시간 안은 채택하지 않는다. | 실제 전달 채널/수신자 확인·활성 계정 재설정 링크 수명·소비/CSRF 계약 |
| A5 | 2 | AuthSession 만료 | 모든 역할에 미사용 30분/로그인 후 최대 8시간을 동일 적용한다. Trainer 전용 2시간/24시간이나 역할별 분기는 채택하지 않는다. | 활동 인정/자동 polling 제외·갱신/회전·만료 경계 구현과 중요 작업 재인증 |
| A6 | 1 | 복수 기기/로그아웃 | 여러 기기의 독립 AuthSession을 허용하고 일반 로그아웃은 현재 기기/현재 AuthSession만 종료한다. | 개별/전체 세션 조회·사용자 전체 로그아웃 기능, 저장/동시성 |
| A7 | 1 | 관리 역할/관리 지점 변경 | 관리자 역할 또는 관리 Branch Scope 변경 시 기존 로그인을 모두 종료하고 새 권한으로 재로그인한다. 변경 후 이전 인증/Scope로 후속 업무를 허용하지 않는다. Trainer 업무 비활성화만으로 전체 계정을 차단하는 정책은 아니다. | 처리 중 요청의 순서·보안 버전/설정 토큰 처리·잠금/캐시 계약 |
| A8 | 1 | 계정 전체 차단/복구·관리자가 수행하는 비밀번호 재설정 Actor | 같은 Organization의 Master만 실행할 수 있다. 여기서 재설정은 관리자가 수행하는 계정 비밀번호 재설정이며 본인 비밀번호 변경과 별개다. Branch Admin에 Operator/Trainer 전용 계정의 같은 권한을 위임하지 않는다. Trainer 비활성화/재활성화(B1)의 지점 관리자 권한은 유지한다. | 본인 비밀번호 변경/신원 확인·재설정/복구 효과·비상복구·재인증 |
| A9 | 1 | 추가/마지막 Master | 여러 Master를 허용하되 마지막 사용 가능한 Master의 차단·권한 제거는 금지한다. 단일 Master 고정안은 채택하지 않는다. | 발급/변경 Actor·사용 가능 판정·재설정/동시 변경·비상복구 계약 |
| A10 | 1 | 운영 관리자 MFA 시점 | 관리자 MFA는 실제 운영 시작 전에 필수다. 제한된 로컬 개발/첫 기능 검증은 먼저 진행할 수 있다. 무MFA 운영 허용이 아니며 구현 완료도 아니다. | MFA 수단·등록/분실/복구·운영 배포/브라우저/품질 인수 |

승인 경계: 이 표의 정책만 확정한다. 기존 보상 설정/추가실적/정산 공개·정정 권한, 기본급 적용 시작 월 이후 유지, 확정 과거 결과 보존, 수동 만료·기존 Pass 우선순위와 관리자 역할 독립성은 유지한다. 새 Pass 발급의 Actor/Issued Branch Scope(BR-OPS-010)와 기존 Pass 담당 교체의 Member 현재 Home Branch Scope(BR-OPS-008)를 혼동하지 않는다. B4는 Operator에게 수동 횟수 조정 권한을 부여하지 않는다. B6은 기존 Trainer를 자동 비활성화하거나 모든 계정을 차단하지 않는다. A4는 최초 설정 링크에 관한 승인으로 활성 계정 reset 정책 전체의 승인이 아니다. A1은 v1 인증 방식의 채택이며 JWT 의무 전환/시기·pwdlib/Argon2 및 버전/모듈/UoW/운영 구성을 일괄 채택하지 않는다. A5는 AuthSession 수명으로 중요 관리 재인증 5분 후보의 승인이 아니다. A7의 로그인 철회와 Trainer 업무 비활성화/재활성화·계정 전체 차단/복구는 서로 구분한다. A9는 마지막 Master의 실제 복구 방법/추가 발급 세부까지 승인하지 않는다.

검증 상태: 문서 반영이며 코드/SQLAlchemy 모델/Alembic migration·의존성/lockfile·실행 테스트는 변경/수행하지 않았다. 앞선 날짜의 PROPOSED/미결정 기록은 당시 이력이고, 위 승인으로 해결된 부분에 한해서만 대체한다. Product OPEN의 남은 상세는 OPEN을 유지하며 전체 구현/운영 허용이나 IAM-001 S1 범위·구체 계약의 일괄 승인이 아니다.

<a id="review-20261012-c-batch"></a>
## 2026-10-12 일괄 승인 — C1–C13

2026-10-12 사용자 일괄 승인: “C1 만 2번. 나머지 전부 1번”. 직전 C1–C13 질문에 한정하며 B/A 승인과 비충돌 정책은 유지한다. 이전 문서의 미결정/추천 기록은 아래에서 해결한 항목에 한해서 대체한다.

| 질문 ID | 선택 | 항목 | 승인된 정책 | 남은 상세/게이트 |
| --- | --- | --- | --- | --- |
| C1 | 2 | 중요 계정 관리의 추가 확인 | 유효하게 로그인한 관리자는 기존 행위/Organization/Branch Scope 안에서 계정 발급·차단·역할 변경·관리자 재설정을 추가 비밀번호 재확인 없이 수행한다. 5분 이내 비밀번호 확인·이를 위한 강제 재로그인/별도 재인증 요구는 채택하지 않는다. | 현재 인증/인가·CSRF·로그인 만료·운영 전 관리자 MFA는 유지. C3 본인 암호 변경의 현재 암호 검증은 별개 |
| C2 | 1 | 로그인 실패 제한 | 계정당 15분 내 5회 로그인 실패 시 15분 대기 후 다시 시도할 수 있다. 반복 실패만으로 영구 잠금/관리자 수동 해제를 요구하지 않는다. | 계정 비노출·원자적 집계/경합·창/초기화의 세부 계약. IP/NAT·자원 보호의 수치/보관은 별도 기술 후보 |
| C3 | 1 | 본인 비밀번호 변경 | 기존 로그인 Actor는 현재 비밀번호 확인 후 본인 비밀번호를 변경할 수 있다. 성공하면 현재 로그인 포함 모든 AuthSession을 종료하고 재로그인한다. | 상태/해시·철회·감사/실패 원자성. Member 로그인 추가나 MFA 초기화·차단 계정 복구가 아님 |
| C4 | 1 | 관리자 재설정 시작 효과 | Master가 ACTIVE 대상 계정의 비밀번호 재설정을 명시적으로 확정하면 기존 비밀번호와 모든 기존 로그인을 즉시 무효화한다. 대상자는 새 암호를 설정한 뒤 로그인한다. | reset 링크 수명/전달·본인 확인/소비 계약. 익명 요청/단순 링크 열람과 구별; 계정/Trainer 상태 자동 복구 없음 |
| C5 | 1 | 마지막 Master 재설정 | 마지막 사용 가능한 Master에 대한 일반 관리자 비밀번호 재설정은 차단한다. 암호 분실은 별도 비상 복구로 처리한다. | 사용 가능 판정/동시 변경·비상 복구 책임/증거/절차·운영 전 검증. 현재 암호를 아는 본인 변경(C3)과 구별 |
| C6 | 1 | Login ID 변경 | 같은 Organization의 Master만 Login ID를 변경할 수 있다. 계정 식별자·역할/Scope·Trainer 연결과 기존 업무/감사 이력을 보존하고 모든 기존 로그인을 종료한다. | ID 정규화·이전 ID 재사용/예약·유일성/감사·경합. S1 구현 범위 자동 추가 아님 |
| C7 | 1 | 인증/계정 감사 열람 | 로그인과 계정 관리 감사 기록의 앱 사용자 열람은 같은 Organization의 Master만 허용한다. Branch Admin/Operator/Trainer 단독 권한으로는 조회할 수 없다. | 조회 API/필드·보존/삭제·운영 접근. PT/보상/정산 등 다른 업무 감사의 권한을 일괄 변경하지 않음 |
| C8 | 1 | 로그인 감사 최소 정보 | 로그인 감사에는 계정·시각·행위·성공/실패 결과를 최소 기록하고 원문 IP/브라우저 정보는 남기지 않는다. 비밀번호·쿠키/토큰·링크 등 비밀 금지는 유지한다. | 미확인 계정 사건 표현·보존/백업/삭제. 반복 시도 방어의 일시적 IP 처리는 별도이며 영구 감사 수집 승인이 아님 |
| C9 | 1 | 실제 수업 시점 | 완료된 실제 수업의 시작 날짜와 시각을 기록한다. Asia/Seoul 기준 실제 시작 시점으로 업무 날짜/소속 월을 판단하며 입력 생성 시점과 구별한다. | 초 이하 정밀도·입력/UTC 저장·과거 소속/비활성 경계와 시각 확인 불가의 예외. 예약/미래 일정 생성 아님 |
| C10 | 1 | 회원/수행 Trainer 오류 | 기존 PT 기록을 취소한 뒤 올바른 Member/실제 Trainer로 다시 등록한다. 원본·취소·정정 연결을 보존한다. 새 일반 Session Payment는 재등록 생성 시점 설정을 적용하며 기존 확정 지급을 덮어쓰지 않는다. | 기존 수행 지점 기준 관리자 인가·Pass 복원/우선 선택·지원 보상 별도 입력·확정 월 해제/재확정 유지. 다른 Trainer/월 영향의 순서·UoW/경합 상세 |
| C11 | 1 | 금액 입력 단위 | 원화 금액은 원 단위 정수로 입력하고 소수 원은 허용하지 않는다. RATE 회당 1,000원 올림/FIXED_AMOUNT 추가 올림 없음과 항목별 기존 0원/양수 정책은 유지한다. | 비율(Rate)의 소수 정밀도·항목별 나머지 상한/음수/누락 및 저장/계산 정밀도 |
| C12 | 1 | Pass 감소 하한 | 수동 감소는 Remaining 0까지 허용하고 결과가 음수인 요청은 거부한다. 음수 차감/부채·자동 0 보정 모델을 추가하지 않는다. | 기존 Issued Branch 관리자 Scope·사유/이력/감사·원자성, 동시 차감/복원 경합 |
| C13 | 1 | Pass 상태별 조정 | 사용 가능·잔여 소진·수동 만료 Pass의 수동 횟수 조정을 허용한다. 소진 후 추가하면 다른 사용 조건 충족 시 다시 이용할 수 있다. 수동 만료 Pass는 횟수를 늘려도 만료를 유지하며 별도 해제가 필요하다. | CANCELLED 등 나머지 상태·비활성 지점 조합/수량 상한·상태 저장 방식. 기존 만료 전 실제 수업의 누락 입력 예외 유지 |

승인 경계: C1은 인증·현재 대상 Scope/행위 인가·CSRF/HTTPS·A5 만료·A10 운영 전 MFA를 생략하지 않는다. C4는 Master가 확정하는 관리자 재설정이며 공개 “비밀번호 찾기” 요청으로 기존 자격을 무효화하는 정책이 아니다. C5는 암호를 아는 마지막 Master의 C3 본인 변경을 막지 않는다. C6/C7은 Master 전용이며 기존 Branch Admin의 허용된 신규 계정 발급 Scope를 변경하지 않는다. C8의 로그인 최소 기록을 계정 관리의 필수 변경 전후/Actor 감사 삭제로 확대하지 않는다.

C10은 기존 PT 정정/취소의 Master Organization/Branch Admin 실제 Performed Branch 범위를 따른다. Performed Branch 값 정정은 Master 전용이며 취소·재등록으로 이를 우회할 수 없다. 지원 수업 보상은 일반 지급 대신 수동 Additional Performance로 처리하고 취소 수업의 연계 추가실적 무효화 규칙을 유지한다. 확정 월에 영향이 있으면 각 대상 Trainer·월의 기존 확정 해제/재확정 권한과 사유·이전 확정본 보존을 적용한다. C11은 비율 정밀도나 모든 항목 0원 허용을 승인하지 않는다. C13은 수동 만료 해제나 비활성 Branch의 금지 업무를 자동 허용하지 않는다.

검증 상태: 설계 문서 반영이며 코드·의존성/lockfile·migration·실행 테스트는 변경/수행하지 않았다. ADR-0004의 ACCEPTED 범위는 v1 인증 방식 그대로이고 모듈/계약/UoW·잠금은 PROPOSED다. 복합 OPEN의 남은 정책/기술 상세·실제 운영 조건은 유지하며 S1/S2 범위나 구현 착수를 일괄 승인한 것은 아니다.

<a id="review-20261012-e-batch"></a>
## 2026-10-12 일괄 승인 — E1–E6

2026-10-12 사용자 일괄 승인: “E5는 2번. 나머지 1번”. 직전 E1–E6 질문의 정책만 확정한다. B/A/C 승인과 비충돌 결정은 유지한다.

| 질문 ID | 선택 | 항목 | 승인된 정책 | 남은 상세/게이트 |
| --- | --- | --- | --- | --- |
| E1 | 1 | 최초 Master 준비 | 설치 담당자가 제한된 설치 명령을 최초 1회 실행하고 Master 본인이 비밀번호를 설정한다. 일반/초기 설정 웹 화면 방식은 채택하지 않는다. | 설치 권한의 구체 지급/회수·운영 담당 지정/본인 확인·보호된 입력/실패·동시 실행/감사. 명령/코드가 이미 있다는 뜻이 아님 |
| E2 | 1 | 설정·재설정 링크 전달 | 각 발급/재설정 권한이 있는 관리자가 본인을 확인한 뒤 대면 또는 확인된 1:1 업무 연락으로 링크를 전달한다. 시스템 이메일 자동 발송은 이번 범위에 도입하지 않는다. | 확인/전달 운영 절차·신뢰 URL/노출/재발급·reset 링크 수명/소비·보존. 실제 연락처/비밀을 문서·일반 로그에 기록하지 않음 |
| E3 | 1 | Login ID 대소문자 | 영문 대소문자를 구별하지 않는다. TrainerA/trainera는 같은 Login ID로 판단하며 중복 발급/변경과 이전 ID 예약에도 같은 비교 원칙을 적용한다. | 허용 구분자/공백·정규화/표시·유일성/예약 저장 및 경합. 비밀번호의 대소문자를 무시하는 정책이 아님 |
| E4 | 1 | 변경 전 Login ID | 변경 전 ID는 원래 계정에 예약하고 다른 계정에 재할당하지 않는다. 원래 계정의 재사용도 기존 C6 Master 전용 ID 변경 절차를 따른다. 현재 ID만 로그인에 사용하며 이전 ID를 로그인 별칭으로 허용하지 않는다. | 예약/이력·동시 발급/변경·응답/감사 계약. 기존 계정/Trainer/업무 식별자는 보존 |
| E5 | 2 | 기존 계정의 Operator·Trainer 역할 추가/회수 | Master는 자신의 Organization, Branch Admin도 자신의 관리 범위에서 해당 역할만 추가·회수할 수 있다. 대상 역할의 Scope를 검증하며 계정의 독립 Master/Branch Admin 역할·다른 범위 역할/연결·업무 이력은 보존한다. | 대상 역할/현재 지점 사실·동일인/Trainer 연결·상태/역할 조합·재부여·최소 조회/명령·인가/감사/철회·UoW/경합. 모든 계정 관리 권한의 위임이 아님 |
| E6 | 1 | 계정 차단 해제와 비밀번호 | 같은 Organization의 Master가 일반 계정 차단을 해제할 때 기존 비밀번호가 여전히 유효하면 재로그인을 허용한다. 매 차단 해제마다 비밀번호 재설정을 강제하지 않으며 필요한 경우 별도로 재설정한다. | 정확한 상태 전이/현재 역할·Trainer/MFA·남은 로그인 제한/경합 계약. 침해 의심 계정의 비상 복구와 별개 |

E5 Scope 적용은 기존 단일 Operator Branch·Trainer 현재 Home Branch의 관리 범위를 따른다(기존 2026-10-11 사용자 일관성 지시 적용). Operator 회수는 해당 역할의 현재 지정 Branch, 신규 역할 추가의 최초 Branch는 관리자의 허용 Branch 범위로 검증한다. Trainer 역할은 실제 대상 Trainer의 현재 Home Branch를 검증한다. 같은 계정의 다른 역할이 자기 지점이라고 범위 밖 대상 역할을 변경하지 않는다. 대상 사실/동일인 연결을 확인할 수 없을 때 임의 Branch를 부여하거나 기존 Trainer 연결을 덮어쓰지 않는다. 구체 대상 상태/재부여·역할 조합/연결 계약은 후속이다.

권한 경계: E5는 Master/Branch Admin 역할 부여·변경, 기존 Operator 업무 Branch 변경, Trainer Home Branch 이동, Login ID 변경, 계정 전체 차단/복구·관리자 password reset, 인증 감사 열람의 Master 전용 권한을 Branch Admin에게 추가하지 않는다. 역할 회수/재부여로 기존 Operator 지점 변경이나 Trainer 소속/연결 변경을 우회하지 않는다. 역할 회수와 Trainer 업무 비활성화·전체 계정 차단은 별개이며 다른 유효 역할/Scope를 일괄 회수하지 않는다. 이후 요청은 현재 역할/Scope를 확인하여 회수된 권한을 허용하지 않고 필수 변경 감사와 실패 원자성을 적용한다. Operator/Trainer 역할 변경 시 전 AuthSession 철회 여부/진행 중 요청 계약은 상세 후속으로 남기며 A7 관리 역할/관리 Branch 변경의 전 로그인 종료 정책은 그대로다.

E6은 폐기된 로그인·설정 링크를 되살리거나 reset으로 무효화한 옛 비밀번호를 복원하지 않는다. 자격 설정 대기·비활성 Trainer/다른 역할·MFA 등 기존 로그인/업무 조건은 유지한다. 이전에 회수된 역할/Scope를 복원하거나 MFA를 초기화하지 않는다. 침해 의심 시 별도 자격·MFA/복구 수단 점검은 운영 복구 절차의 후속이다. E1/E2 승인으로 최초/비상 복구를 같은 명령으로 처리하거나 reset 링크 수명을 최초 링크 30분으로 자동 확정하지 않는다.

검증 상태: 설계 문서 반영이며 코드·migration·의존성/lockfile·실행 테스트 변경/수행은 없다. 구체 계약/UoW/잠금·S1/S2 범위는 PROPOSED이고 운영 전 MFA/비상복구·배포/검증 게이트를 유지한다. 복합 Product OPEN의 다른 항목은 닫지 않는다.

<a id="review-20261012-g-batch"></a>
## 2026-10-12 일괄 승인 — G1–G5

2026-10-12 사용자 일괄 승인: “전부 1번”. 직전 G1–G5 지점 비활성화 이후 처리 질문의 1번만 확정한다. B/A/C/E 승인과 비충돌 결정은 유지한다.

| 질문 ID | 선택 | 항목 | 승인된 정책 | 남은 상세/게이트 |
| --- | --- | --- | --- | --- |
| G1 | 1 | 비활성 지점 소속 사용자의 로그인·조회 | 계정과 역할이 유효하면 로그인하고 기존 조회 권한이 있는 자료만 조회할 수 있다. Branch 비활성 자체를 계정 전체 차단이나 Trainer 업무 비활성으로 취급하지 않는다. | 현재 계정/역할·행위별 대상 Scope·Branch 상태 계약/처리 중 요청·철회/경합. 새로운 열람 권한 승인 아님 |
| G2 | 1 | 비활성화 전 실제 수업의 누락·오류 | 비활성화 전에 실제 진행한 수업은 지점을 재활성화하지 않고 기존 업무별 권한으로 소급 등록·정정·취소할 수 있다. 영향받는 확정 Trainer/월은 기존 해제·정정/등록·재확정 및 이전 확정본 보존 절차를 따른다. | 실제 시작/지점 운영 이력·당시 담당/수행/Pass 사실 확인, 확인 불가 예외·다른 상태 조합·UoW/실패/경합. 비활성 기간의 새 수업 허용 아님 |
| G3 | 1 | 비활성 지점 발급 Pass의 타 지점 사용 | 발급 지점이 비활성이어도 다른 활성 지점에서 기존 사용 조건을 충족하면 기존 Pass를 사용할 수 있다. Issued Branch·발급 조건·잔여/이력은 유지하고 실제 정상 사용에 따라 1회 차감한다. | 다른 종료/계정/대상 상태·역사 사실/선택 계약·차감/지점 상태 경합. 수동 만료/잔여 0 등 사용 불가 조건 면제 아님 |
| G4 | 1 | Home Branch 비활성 회원·Trainer의 타 지점 수업 | Member/Trainer의 Home Branch가 비활성이어도 다른 활성 지점에서 기존 담당·개별 지원 등 허용 조건을 충족하면 수업할 수 있다. Trainer 자체는 활성 상태여야 한다. | 현재 인가/관계·소속/운영 이력·나머지 상태 조합/경합. 신규 배정·계정 차단/Trainer 비활성 예외 승인 아님 |
| G5 | 1 | 비활성 지점에서 활성 지점으로 소속 이동 | 같은 Organization의 활성 지점으로 기존 권한에 따라 이동할 수 있다. Member는 Master 또는 변경 전 현재 Home Branch의 Branch Admin, Trainer Home Branch와 Operator 업무 Branch 이동은 Master만 허용한다. 출발 지점 재활성화는 필요 없다. | 이동 대상/절차·과거 소속 이력 정정·계약/저장/이동과 상태 변경 경합. Branch Admin 관리 Scope 이동 권한 추가 아님 |

공통 인가 경계: 각 요청은 현재 검증된 Caller의 계정/역할·Organization과 해당 업무의 대상 Scope를 따른다. G1은 기존 자료에 대한 권한 내 조회이며 Operator/Trainer의 보상 설정, 타 지점 전체 자료 또는 인증 감사 열람 권한을 늘리지 않는다. 계정 전체 차단·철회된 역할·만료/폐기 AuthSession·다른 활성 역할 없는 비활성 Trainer의 로그인 제한은 그대로다. Branch 활성 상태만으로 유효하지 않은 인증을 복원하지 않는다.

G2 적용은 실제 수업이 해당 지점의 비활성화 전에 이루어졌다는 조건이다. 현재 비활성 지점에서 새 실제 수업을 진행하고 과거 날짜로 기록하는 것을 허용하지 않는다. Trainer의 직접 소급 등록은 기존 본인 수행/Allowed PT Scope·미확정 실제 진행 월/Pass 조건을 따르며 본인 기록 정정·취소 권한을 추가하지 않는다. 비활성 Trainer의 과거 수업은 기존 관리자 대행 경로(BR-OPS-015)를 따른다. PT 정정/취소·대행 등록의 Branch Admin 기준은 실제 Performed Branch, 확정 해제/재확정의 Branch Admin 기준은 각 처리 시점 대상 Trainer 현재 Home Branch다. Performed Branch 값 변경은 Master 전용이며 Member/실제 수행 Trainer 오류는 C10 취소 후 재등록이다. Branch 비활성만을 이유로 사유·Pass 복원/선택·보상 연동·과거 확정본 보존을 생략하지 않는다. 일반 지급은 기존 생성 시점 설정을 따르고 과거 확정 지급을 현재 설정으로 재계산하지 않는다.

G3/G4는 다른 활성 Performed Branch에서 허용된 수업을 진행하는 경우다. Issued Branch 또는 Home Branch를 먼저 옮기도록 요구하지 않고 기존 담당/개별 지원 등 관계를 검증한다. 실제 수업 당시 Trainer Home Branch와 Performed Branch로 일반/지원 보상을 구분하고, 타 지점 지원 수업 보상 전체는 관리자 입력 Additional Performance로 처리한다. 일반 Session Payment를 중복 합산하지 않으며 금액 미입력 지원 수업이 남은 Trainer/월 정산 확정 차단과 보상 설정 접근 제한을 유지한다. 비활성 Home Branch를 가진 Trainer의 새 담당 지정 등 G 질문에 없는 신규 배정 조건은 이번 승인으로 일괄 해결하지 않는다.

G5는 권한 있는 관리자의 명시적인 이동이다. 기존 즉시 적용·실패 시 원상 유지·변경 감사 및 독립 역할/계정·Trainer 연결/담당·지원 관계·Pass/잔여·과거 수업/확정 지급/정산 보존을 적용한다. Member 이동 후 Home Branch 기반 관리는 새 현재 소속을 따르며, Trainer 이동 후 보상 설정/정산의 현재 Home Branch 인가도 기존 규칙대로 판단한다. 과거 수업 당시 소속/Performed Branch·비용 귀속을 소급 변경하거나 비활성화만으로 자동 이동하지 않는다. 계정 차단·Trainer 비활성·회수 역할을 복원하는 명령도 아니다.

남은 게이트/검증 상태: 지점 재활성화의 세부 절차·과거 운영/소속/수행 사실의 확인 불가·정정, 미결정 신규 배정/다른 상태 조합과 구체 계약·저장/UoW/잠금·동시 요청은 별도다. 복합 Product OPEN은 23 OPEN/7 CLOSED, PD-021은 OPEN을 유지한다. 모듈/구체 IAM 설계는 PROPOSED이며 ADR-0004 v1 인증 방식 ACCEPTED·IAM-001 S1/S2 범위와 별도 구현 지시 경계를 유지한다. 코드·migration·의존성/lockfile·실행 테스트 변경/수행은 없다.

<a id="review-20261012-h-batch"></a>
## 2026-10-12 일괄 승인 — H1–H4

2026-10-12 사용자 일괄 승인: “H1만 2번. 나머지 1번”. 직전 H1–H4의 선택만 확정하며 B/A/C/E/G 및 비충돌 결정을 유지한다.

| 질문 ID | 선택 | 항목 | 승인된 정책 | 남은 상세/게이트 |
| --- | --- | --- | --- | --- |
| H1 | 2 | Trainer Rate 입력 정밀도 | 정수 퍼센트만 허용한다. 50%는 허용하고 50.25%처럼 소수 부분이 있는 비율은 거부한다. 소수 비율을 임의 반올림/절사하지 않으며 기존 RATE 지급 결과의 1,000원 단위 올림은 유지한다. | Rate 허용 범위/최솟값·최댓값/누락·구체 저장/검증 계약. 원화 정수 입력 C11과 다른 비율 단위 |
| H2 | 1 | 지원 수업 외 추가실적 내용 수정·취소 권한 | Master는 자신의 Organization, Branch Admin은 각 처리 시점 대상 Trainer의 현재 Home Branch가 관리 Branch인 범위에서 허용한다. 관리 범위 안 본인 건 포함·별도 승인 없음·사유/변경 이력/감사 필수다. | 대상 상태·내용/연결 필드별 공개 계약·실제 발생 사실·확정 결과 영향 판정/버전·UoW/경합. Operator/Trainer 단독 권한 추가 아님 |
| H3 | 1 | 지원 수업 외 추가실적 대상 Trainer·발생 날짜 오류 | 원래 건을 취소하고 올바른 대상/실제 발생 날짜로 재등록하며 원본·취소·새 기록을 연결한다. 대상/발생 날짜를 원본에 덮어쓰지 않는다. 영향을 받는 확정 정산은 기존 해제·처리·재확정/이전 확정본 보존 절차를 따른다. | 서로 다른 Trainer/월/현재 Home Branch의 단계별 인가·발생/소속 사실·정정 연결/실패·재시도/UoW 상세. 지원 수업 보상의 연결 관계 임의 변경 승인 아님 |
| H4 | 1 | Trainer의 본인 월 정산 조회 | 관리자 권한이 없는 Trainer의 본인 월 정산 시스템 조회는 v1에서 제외하고 관리자가 안내한다. 기존 본인 PT 진행 내역 조회는 유지한다. 관리자 겸임자의 허용된 독립 관리 Scope 조회는 유지한다. | 관리자용 대상 월/이전 확정본·계산 근거/감사 공개 및 보고서 상세는 MB-006 후속. 별도 급여 안내/발송 기능 승인 아님 |

H1은 입력 비율의 정밀도만 확정한다. 예시 50%는 승인 기본값이 아니며 0%/100% 등 경계·누락/범위 정책을 새로 확정하지 않는다. 기존 RATE 공식과 Session별 1,000원 올림·FIXED_AMOUNT 추가 올림 없음, 생성 시점 Trainer 설정/발급 Pass 조건 적용·과거 확정 지급 보존을 유지한다.

H2/H3의 기존 금액 수정·취소 및 정정 후 등록은 각각 현재 권한과 실제 대상 Trainer/Organization을 검증한다. 이전 소속 지점/과거 등록자/수업 지원 지점만으로 수정·취소 권한을 유지하지 않는다. 취소는 원래 금액/내용·Actor/발생 시점/비용 귀속 이력을 보존하고 해당 실적을 유효 정산·지점 비용 합산에서 제외하는 업무이며 0원/음수 덮어쓰기나 다음 달 음수 상계로 대신하지 않는다. 일반 PT 진행 기록·Pass 잔여/일반 Session Payment를 실적 취소만으로 취소·복원하지 않는다. 지원 수업 외 실적의 기존 양수 금액/발생 월 정산·발생 당시 Home Branch 비용 원칙은 유지한다.

H3의 취소 대상과 새 등록 대상/월은 서로 다를 수 있다. 각 처리 단계에서 원래 Trainer의 현재 Home Branch 기반 취소 권한과 새 Trainer의 현재 Home Branch 기반 등록 권한을 각각 확인하며, 한쪽 권한이 다른 지점 대상의 권한을 주지 않는다. 영향받는 확정 Trainer/월은 기존 허용 관리자가 사유를 남겨 해제하고 처리 후 같은 해당 월을 재확정하며 각 이전 확정본을 보존한다. 새 실제 발생 날짜/당시 소속 사실에 따른 정산 월·비용 귀속을 적용하고 재등록 금액도 관리자 수동 입력/양수 규칙을 따른다. 역사 사실이 불명확할 때 임의 소속/발생 시점으로 기본 처리하지 않는다. 지원 수업 보상의 PT 연결·수업 취소 연동 규칙은 별도 기존 정책이며 H3으로 연결을 임의 교체하지 않는다.

H4는 Trainer 역할만의 월 정산 API/화면·총액/구성 조회를 v1 허용하지 않는 결정이다. 숨긴 화면을 직접 ID/API/집계 요청으로 우회할 수 없도록 Backend에서 현재 행위/대상 권한을 검증한다. 기존 본인 PT 진행 내역 조회 허용을 월 정산이나 Compensation Setting 읽기로 확대하지 않는다. Master/Branch Admin과 Trainer 겸임자는 이미 허용된 독립 관리 Scope 안에서 본인 포함 정산을 조회할 수 있다. 관리자가 안내한다는 것은 시스템 이메일/문자·급여명세 자동 발송 등 새 기능을 추가하는 승인이 아니다.

남은 게이트/검증 상태: 나머지 Rate/금액 입력 범위·실제 발생/소속 사실 확인 불가/소급 기간·구체 내용/연결 필드/정정 연결·영향받는 Trainer/월의 처리 순서/실패·재시도 및 현재 인가/UoW/잠금·정산 공개 상세는 후속이다. BR-013의 내용 수정/취소 Actor·현재 Home 기준과 대상/발생 날짜 취소 후 재등록, BR-010 Rate 정밀도, MB-006 Trainer 단독 v1 정산 조회 여부는 다시 미결정으로 취급하지 않는다. 23 OPEN/7 CLOSED·PD 1 OPEN/26 CLOSED, ADR-0004 v1 인증 방식 ACCEPTED/모듈·구체 계약 PROPOSED·IAM-001 S1/S2 범위 및 별도 구현 지시는 유지한다. 코드·migration·의존성/lockfile·실행 테스트 변경/수행은 없다.

<a id="review-20261012-i-batch"></a>
## 2026-10-12 일괄 승인 — I1–I4

2026-10-12 사용자 일괄 승인: “전부 1번.” 직전 I1–I4 질문의 선택을 확정하며 기존 B/A/C/E/G/H 및 비충돌 결정을 유지한다.

| 질문 ID | 선택 | 항목 | 승인된 정책 | 남은 상세/게이트 |
| --- | --- | --- | --- | --- |
| I1 | 1 | 과거 수업 시작 시각을 모를 때 | 실제 시작 날짜·시각을 확인한 뒤 등록한다. 임의 시각이나 ‘시각 미상’ 기록은 허용하지 않으며 관리자 대행에도 시각 미상 예외를 추가하지 않는다. | 시각 정밀도/저장·역사적 소속/담당/발급 사실·정정/경합의 계약은 별도. Asia/Seoul 실제 시작 기준 날짜/월과 생성 시점 보상은 유지 |
| I2 | 1 | 회원 기본 인적정보 | 이름·전화번호·하나의 Home Branch를 필수로 관리한다. 생년월일·성별은 v1에서 제외한다. | 전화번호 형식/정규화·다른 항목/행위별 권한·개인정보 보존/삭제는 LEGAL-001 후속. Member 로그인은 Future |
| I3 | 1 | 여러 날짜 수업 일괄 입력 | v1은 실제 수업별 개별 등록을 제공한다. 여러 날짜를 한 번에 등록하는 편의는 후속으로 보류하며 UX-001을 CLOSED 처리한다. | 향후 필요 확인 후 별도 채택/오류 UX 설계. 동일 날짜 별개 수업 허용·실제 수업당 원본/1회 차감·중복 요청 방지는 유지 |
| I4 | 1 | 추가 연간 통계 | 필수 월 정산과 기존에 정한 Master 전용 지점 비용 보고서까지 v1에 포함한다. 추가 연간 합계·월별 추이는 v1에서 제외하고 후속으로 보류한다. | 기존 관리자 정산/비용 보고서 항목·계산 근거/이전본/집계 완전성·상태/권한의 남은 상세는 BR-009·MB-006/010 후속 |

I1은 ‘수업 시각 미상’을 등록할 별도 관리자 예외를 두지 않는 결정이다. 실제 시각을 모를 때 기본 시각을 임의 입력하거나 날짜만 저장해 통과시키지 않는다. 시작 시각 확인만으로 과거 소속/담당·Pass 발급/사용 가능 사실이 자동 입증되는 것은 아니며 각 기존 조건을 검증한다. 과거 수업의 기존 미확정 월 직접 등록/확정 월 관리자 해제·처리·재확정·이전본 보존과 현재 인가는 유지한다. 새 소급 N일 제한이나 미래 예약을 추가하지 않고 일반 지급의 신규 기록 생성 시점 설정 적용을 유지한다.

I2의 필수 이름/전화번호/Home Branch는 일반 등록과 인가된 기본정보 수정에서 유지한다. 누락·빈 이름/번호 또는 Home Branch 없는 회원을 정상 등록 완료로 취급하지 않는다. 기존 필수값을 일반 수정으로 비우지 않되 법적/운영상 삭제 예외는 별도다. 같은 이름/전화번호의 회원은 별도 Member 식별자로 구분하고 중복 번호만으로 병합/첫 결과 자동 선택을 하지 않는다. 이 결정으로 주소·이메일·메모 등 다른 필드의 채택/제외나 새로운 등록/수정/열람 권한을 승인하지 않는다. Home Branch 변경은 기존 인가/이력·단일 소속/즉시 적용 규칙을 따르고 담당/지원 회원 읽기 범위를 확대하지 않는다. 생년월일·성별 입력/저장·생일 목록을 v1의 숨은 전제로 도입하지 않는다.

I3은 여러 날짜의 입력 편의에 대한 v1 보류 승인이고 실제 수업 원본 단위를 바꾸지 않는다. 한 날짜에 실제 별개 수업을 여러 번 받은 경우는 기존대로 각각 개별 등록/차감한다. 월 합계 입력·기존 월 기록 복사·여러 날짜 일괄 요청 API를 별도 기본 기능으로 도입하지 않는다. 같은 저장 요청 재전송은 별개 수업이 아니며 기존 중복 차감/지급 방지 요구를 유지한다. Smartphone 현장 등록과 Desktop/Tablet/Smartphone Responsive Web은 v1 필수다.

I4는 추가 연간 통계의 v1 보류이며 기존 월 정산/지점 비용 보고서까지 제외하는 결정이 아니다. 기존 Master Organization/Branch Admin 현재 Home Branch Trainer 정산 조회, Master 전용 지점 비용 보고서 및 H4 비관리자 Trainer 정산 조회 제외를 유지한다. v1에서 추가 연간 합계/월별 추이 화면·API를 제공하거나 권한/노출 범위를 클라이언트 합산으로 우회하지 않는다. PR-011을 OUT-V1로 정리하고 생년월일 기반 PR-024도 I2에 따라 OUT-V1로 정리한다. BR-009의 정산 수명/남은 조건·MB-006/010의 보고서 상세와 LEGAL-001은 OPEN을 유지한다.

남은 상태/검증 경계: UX-001은 이 승인으로 CLOSED이며 Product OPEN은 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED다. ADR-0004 v1 인증 방식 ACCEPTED 및 나머지 모듈/공개 계약·UoW/잠금 PROPOSED, IAM-001 S1/S2 범위와 별도 구현 지시는 유지한다. V-94–97은 미구성·미실행 검증 계획이다. 코드·migration·의존성/lockfile·실행 테스트 변경/수행은 없다.

<a id="review-20261012-j-batch"></a>
## 2026-10-12 일괄 승인 — J1–J3

2026-10-12 사용자 일괄 승인: “전부 1번.” 직전 J1–J3 질문의 선택을 확정하며 기존 B/A/C/E/G/H/I 및 비충돌 결정을 유지한다.

| 질문 ID | 선택 | 항목 | 승인된 정책 | 남은 상세/게이트 |
| --- | --- | --- | --- | --- |
| J1 | 1 | 회원 등록·이름/전화번호 수정 권한 | Master Admin은 자신의 Organization 전체, Branch Admin·Operator는 자기 지점 회원에 허용한다. 신규 등록은 지정할 Home Branch, 기존 회원 수정은 처리 시점 현재 Home Branch를 기준으로 한다. Trainer 역할만으로는 불가다. | 구체 선택/입력·최소 공개/행위별 계약·다른 필드/대상 상태·현재 인가/UoW/경합. Operator의 기존 Home Branch 이동 금지는 유지 |
| J2 | 1 | 회원 비활성화·재활성화 권한 | Master Admin은 자기 Organization 전체, Branch Admin은 처리 시점 Member 현재 Home Branch가 자신의 관리 Branch인 회원만 허용한다. Operator·Trainer 역할만으로는 불가다. | 상태 이력/감사·다른 상태/역사 사실·복귀 시 각 독립 조건·저장/경합 계약. 계정/Trainer/Branch 상태 변경 권한과 구분 |
| J3 | 1 | 비활성 회원의 남은 이용권 | 기존 잔여와 이력은 보존하되 새 Pass 발급과 회원 비활성 기간의 실제 수업은 차단한다. 복귀할 때 같은 Member를 재활성화하고 기존 이용권을 사용 조건에 따라 이용한다. | 비활성화 전 실제 수업 누락/정정은 기존 과거 업무 규칙 유지. 상태 변경 경계·역사 사실/정정·현재 인가/발급·차감 경합 계약 |

J1의 신규 등록 권한은 지정할 Member Home Branch가 Master의 Organization, Branch Admin의 단일 관리 Branch 또는 Operator의 지정 단일 업무 Branch에 속하는지 Backend에서 검증한다. 기존 이름/전화번호 수정은 실제 Member의 현재 Home Branch로 인가하며 이전 소속/등록자·Pass Issued Branch·수업 Performed Branch·담당/개별 지원 관계만으로 수정 권한을 얻지 않는다. Trainer와 관리자/Operator를 겸임하면 허용된 독립 역할/Scope로 판단한다. Operator의 최초 Home Branch 지정은 새 회원 등록의 일부이며 기존 회원 소속 이동 권한은 추가하지 않는다. 기존 Master/변경 전 현재 Member Home Branch Branch Admin의 이동 규칙은 유지한다. 비활성 Branch의 신규 배정 차단 등 기존 대상 조건도 유지하며 Master의 조직 범위를 다른 Organization으로 확대하지 않는다.

J1은 이름/전화번호 수정과 회원 등록의 Actor/Scope 결정이다. I2의 필수 이름/전화번호/단일 Home Branch·생년월일/성별 v1 제외, 번호 중복 허용·별도 Member 식별·임의 병합/첫 결과 자동 선택 금지를 유지한다. 일반 수정으로 필수값을 비우지 않고 변경하지 않는 값은 보존한다. 다른 필드/일반 전체 목록·타 지점 회원 상세/일괄 내보내기·Pass/PT/보상·정산 열람 권한을 일괄 추가하지 않는다. 기존 Pass 발급용 Organization 전체 검색/최소 공개와 Trainer 담당/지원 읽기 허용은 각각 기존 업무 Scope로 판단한다. 요청의 role/organization_id/home_branch_id만 믿거나 비허용 Home Branch 변경을 이름/전화번호 수정에 섞어 통과시키지 않는다. 수정용 최소 선택/응답·현재 인가/저장·실패 계약은 후속 기술 설계다.

J2의 두 상태 변경은 각각 현재 역할/Member 현재 Home Branch를 확인한다. 이전 지점 관리자·과거 처리자·지원/발급/수행 지점이라는 사실만으로 비활성화/재활성화 권한을 유지하지 않는다. Member의 상태 변경은 Member 로그인이나 계정 전체 차단, Trainer·Branch 비활성화/재활성화와 별개다. 기존 중요 상태 변경의 전후 상태·대상 Member·Actor/Role/Branch Context·시점 이력/감사 원칙을 적용한다. 새 필수 사유나 별도 승인 단계를 이번 답변만으로 추가하지 않는다.

J3의 비활성화는 Member나 기존 Pass를 삭제/다시 발급/자동 수동 만료 처리하는 업무가 아니다. 잔여 0만으로 Member를 자동 비활성화하지 않고, 잔여가 남아 있어도 관리자 비활성화를 처리할 수 있으며 기존 잔여·발급 조건/담당·소속 관계/과거 PT 소비/확정 지급·추가실적·정산/감사를 보존한다. 비활성 기간의 실제 수업은 다른 Branch에서 수행하거나 나중에 등록한다고 허용되지 않는다. 비활성화 전 실제 수업 누락/정정은 기존 과거 수업의 인가·Pass/실제 사실·정산 조건을 따르며 이번 결정만으로 대행/조회 권한을 새로 만들지 않는다. 재활성화 이후에는 같은 Member/Pass의 기존 잔여와 관계를 바탕으로 기존 사용 조건을 확인한다. 잔여 0·개별 수동 만료·비활성 Trainer/Performed Branch·현재 권한 제한 등 독립 차단 사유는 따로 검증하고, 회원 재활성화가 비활성 기간 수업이나 과거 확정 결과를 자동 유효화/재계산하지 않는다.

Branch 자체 비활성과 Member 자체 비활성을 구별한다. G4의 Home Branch 비활성 회원이 다른 활성 지점에서 허용된 수업을 이용하는 정책은 유지하되 Member 자체도 활성이고 기존 PT 조건을 충족해야 한다. 현재 Member 상태·실제 수업 당시 활성 이력과 현재 역할/Scope·월 확정 상태를 구분하는 계약/원자성/잠금은 PROPOSED다. 과거 사실 확인 불가·정정, 나머지 조회/공개·추가 필드/보존/삭제·다른 상태 조합은 관련 OPEN에 남는다.

상태/검증 경계: 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED를 유지하며 ARCH-001·MB-002·BR-001/007/008·ARCH-003 등 복합 질문은 해당 부분만 해결됐다. ADR-0004 v1 인증 방식 ACCEPTED, 구체 모듈/공개 계약/UoW/잠금 PROPOSED 및 IAM-001 S1/S2 범위/별도 구현 지시 경계를 유지한다. V-98–100은 미구성·미실행 검증 계획이다. 코드·migration·의존성/lockfile·실행 테스트 변경/수행은 없다.

<a id="review-20261012-k-batch"></a>
## 2026-10-12 일괄 승인 — K1–K3

2026-10-12 사용자 일괄 승인: “전부 1번”. 직전 K1–K3 질문의 선택을 확정하며 기존 B/A/C/E/G/H/I/J 및 비충돌 결정을 유지한다.

| 질문 ID | 선택 | 항목 | 승인된 정책 | 남은 상세/게이트 |
| --- | --- | --- | --- | --- |
| K1 | 1 | PT 진행 날짜·시각 오류 | 원본을 취소하고 올바른 실제 시작 날짜·시각으로 재등록한다. 새 일반 Session Payment는 재등록 생성 시점 수행 Trainer 설정을 사용한다. | 원래/정정 기록의 현재 인가·실제 과거 관계/상태/Pass 가용성·소비 복원/재선택·영향받는 각 확정 월·정정 연결/단계별 실패·UoW/경합 계약 |
| K2 | 1 | Trainer 신규 등록·이름/연락처 수정 | Master Admin은 자기 Organization 전체, Branch Admin은 자기 지점에 허용한다. Operator·Trainer 역할만으로는 불가다. 신규 등록은 지정할 Home Branch, 기존 수정은 현재 Home Branch 기준이다. | 다른 수집 필드/필수 여부·형식/최소 공개·대상 상태·인가/등록·수정/계정 연결 계약. 기존 Trainer Home 변경 Master 전용 유지 |
| K3 | 1 | 첫 개발 증분의 기능 범위·순서 | 관리자 인증·지점 접근 제어부터 개발 검증한다. 계정 복구·추가 Master·Trainer 연결은 후속 증분으로 분리한다. 운영 전 관리자 MFA·복구 검증 의무는 유지한다. | S1의 구체 모듈/공개 계약·DB/상태 enum/API/UoW/잠금/보안·인수 상세는 제안/후속 검토. 코드 작성·운영 개시 승인 아님 |

K1은 날짜·시각을 기존 PT 원본에 덮어쓰는 정책이 아니다. 원본/취소/새 기록과 정정 연결·감사를 보존하며 원래 지급/지원 보상과 과거 정산본을 삭제하지 않는다. 기존 취소 규칙에 따라 소비 횟수를 복원하고 기존 수업 연계 보상을 유효 합산에서 제외하며, 새 기록에는 올바른 실제 시작 시점의 소속/담당·Member/Trainer/Branch 상태·이미 발급된 적격 Pass 및 현재 잔여·현재 인가/정산 조건을 확인해 FIXED_AMOUNT 우선/동일 Type FIFO로 재선택·1회 차감한다. 원래 Pass를 무조건 재사용하거나 소급 수업에 이후 발급된 Pass를 쓰지 않는다.

일반/지원 구분은 올바른 실제 수업 시점의 Trainer Home Branch와 Performed Branch로 다시 판단한다. 새 일반 지급은 선택 Pass의 발급 당시 조건과 재등록 생성 시점 실제 수행 Trainer의 Rate/Fixed Amount를 사용하고 RATE 결과 1,000원 올림/FIXED 추가 올림 없음 규칙을 따른다. 예를 들어 같은 적격 RATE Pass의 1회 단가가 50,000원이고 원래 기록 때 Rate 50%, 재등록 때 60%라면 취소 원본의 25,000원은 이력으로 보존/유효 합산 제외하고 새 기록의 일반 지급은 30,000원이다. 과거 원본 지급액을 30,000원으로 덮어쓰는 것이 아니다. 새 지원 수업은 기존 관리자 수동 추가실적/미입력과 명시적 0원 구별·해당 Trainer/월 미입력 확정 차단을 따르며 원래 지원 금액을 자동 복사해 확정하지 않는다.

원본 취소와 정정 후 등록은 각각 기존 현재 Caller/Organization·PT 업무 Scope를 검증한다. PT 정정/취소의 Master Organization/Branch Admin 실제 Performed Branch와 Performed Branch 값 정정 Master 전용을 유지하며 날짜 정정 경로를 지점 변경 우회로 쓰지 않는다. 바뀐 실제 월에 따라 영향받는 각 확정 Trainer/월은 기존 현재 Trainer Home Branch 관리자 인가·사유/해제 → 처리 → 해당 월 재확정/이전 확정본 보존 절차를 따른다. 한쪽 월 권한/해제가 다른 쪽 월의 권한/해제를 대신하지 않는다. I1의 시각 확인 후 등록/임의 시각·시각 미상 예외 불가와 J3의 Member 비활성 기간 수업 차단을 유지한다. 구체 복원/재등록 실패·재시도/연결·여러 월 처리 순서/UoW/잠금은 후속이다. 기존 Performed Branch 값 정정 시 기록 유지/최초 생성 시점 보상 기준 정책은 별개이며 K1으로 바꾸지 않는다.

K2는 Workforce의 실제 Trainer 신규 등록과 이름/연락처 수정에 관한 권한이다. Master의 Organization 범위, Branch Admin의 신규 지정 Home/기존 실제 현재 Home 범위를 Backend에서 확인한다. 과거 소속/계정 발급자·지원 수업 지점·Pass 담당/발급/Member 소속만으로 수정 권한을 얻지 않는다. 관리자·Trainer 겸임은 허용된 독립 관리자 Scope로 판단한다. Operator의 회원 등록/수정(J1)을 Trainer 관리로 확대하지 않는다. 기존 Trainer Home Branch 변경은 Master 전용이며 기본정보 수정에 소속 변경을 섞어 우회하지 않는다. IAM Login ID/역할/연결·암호와 Workforce 이름/연락처·Home/보상 설정은 별개다. 기본정보 수정으로 Login ID/계정 연결·다른 역할/Scope나 과거 PT/지급·정산을 자동 변경하지 않는다. 수집 항목/연락처 필수 여부·형식/보존/최소 읽기와 최초 보상 값·누락/한도는 새로 승인하지 않는다.

K3은 첫 개발 증분의 기능 범위와 작업 순서를 선택한 것이다. 실제 최초 계정 준비/관리자 로그인·검증된 현재 사용자/Scope → 지점 조회/타 지점 직접 접근 차단 → 로그아웃/관리자 차단·관리 Scope 변경 반영 흐름을 개발 환경에서 검증하는 S1을 먼저 준비한다. 구체 준비/발급·활성화·API·모듈 소유권/공유 UoW·잠금 순서/인수 하네스는 기존 IAM-001 제안을 상세 검토한다. 인증 방식 ADR-0004와 기존 승인 ID/비밀번호·설정 링크/수명·계정 철회/반복 시도·최소 기록 정책은 유지한다. 후속 v1 Trainer 로그인/실제 Workforce 연결을 제외 기능이나 완료 상태로 바꾸지 않고 가짜 Trainer/fixture만으로 대체하지 않는다.

S1 개발 검증과 전체 IAM 완료/실운영 허용은 구별한다. 복구·재설정/추가 Master·Trainer 연결 및 운영 전 관리자 MFA/비상 복구·설치/보존/배포 품질의 해당 상세/실제 검증은 후속이다. 복구 전 제한된 개발 환경에서 관리 불능이 발생하면 중단하며 bootstrap 재사용/기존 DB 초기화로 계정 복구를 대신하지 않는다. 구현 착수는 별도 사용자 지시가 필요하다. 이번 답변은 구체 계약/트랜잭션/검사 방식의 일괄 채택이나 코드·migration 작성 지시가 아니다. 기술·하네스 세부를 업무 질문으로 반복하지 않고 설계자가 구체화하며 정책/권한/관측 결과 변경이 필요할 때 확인한다.

상태/검증 경계: 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED를 유지한다. BR-007/008·MB-001/005와 ARCH-001/002·MB-004의 해당 부분만 해결됐고 남은 상태/역사 사실/권한·입력/계약/운영 상세는 유지한다. ADR-0004 v1 인증 방식 ACCEPTED 및 구체 모듈/공개 계약/UoW/잠금 PROPOSED를 구별한다. V-101–103은 미구성·미실행 검증 계획이다. 코드·migration·의존성/lockfile·실행 테스트 변경/수행은 없다.


<a id="review-20261013-l-batch"></a>
## 2026-10-13 일괄 승인 — L1–L2

사용자 답변: **“전부 1번”**. 직전 질문 목록 L1–L2의 각 1번을 승인했다. 이전 승인 이력은 보존하고 해당 미결정 범위만 다음과 같이 확정한다.

| 항목 | 선택 | 승인된 내용 | 유지할 경계 | 추적 |
| --- | --- | --- | --- | --- |
| L1 | 1 | 월 정산은 Asia/Seoul 기준으로 종료된 월만 확정한다. 당월은 미확정 상태로 조회·검토하며 당월 조기 확정은 허용하지 않는다 | Master Organization/Branch Admin 각 처리 시점 Trainer 현재 Home Branch 인가·본인 포함/별도 승인 없음과 기존 지원 보상 미입력 차단·이전 확정본/감사 유지. 월 종료만으로 자동 확정하지 않음 | BR-PAY-020/016; PR-010; NFR-012; BR-009; V-104 |
| L2 | 1 | Trainer Rate는 0~100%의 정수만 허용한다. 음수·100% 초과·소수 비율은 거부하고 반올림/절사·범위 보정하지 않는다. 명시적 0%의 일반 RATE 지급액은 0원이며 설정 누락을 0%로 대체하지 않는다 | 보상 설정의 현재 관리자 Home Branch Scope/감사·정상 지급 생성 시점 설정/발급 조건·기존 RATE 수업별 1,000원 올림/FIXED 별도 규칙·과거 확정 지급 불변 | BR-PAY-018/003/013; PR-007/008; NFR-012; BR-010; V-105 |

L1의 시간 조건은 Organization 공통 한국 시간의 달력 월 기준이다. 다음 달 1일 00:00부터 직전 월이 시간상 확정 대상이 될 수 있다. 예를 들어 한국 시간 2026-10-31 23:59에는 10월 확정이 불가하고 2026-11-01 00:00부터는 시간 조건을 충족한다. Master도 당월/미래 월을 조기 확정할 수 없다. 월 종료가 다른 필수 구성/유효성·현재 인가·지원 수업 보상 미입력 차단 등 기존 확정 조건을 대신하지 않는다. 해제 후 같은 과거 월 재확정도 종료된 월 조건을 따른다. 당월 조회/검토는 기존 관리자 공개 범위이며 H4의 관리자 권한 없는 Trainer 월 정산 조회 제외를 바꾸지 않는다. 미래 기본급의 적용 시작 월을 미리 지정하는 정책/범위와 정산 확정 가능 시점은 별개다.

L2는 H1의 정수 퍼센트에 최소 0/최대 100을 확정한 것이다. 0/50/100은 허용하고 -1/101/50.25는 거부한다. 명시적 0%는 기존 일반 RATE 계산식에 따라 0원이며 사유 필수 지원 보상 0원이나 월별 수동 기본급 0원의 별도 규칙을 복사하지 않는다. 누락/미설정에 임의 0%·50% 등 기본값을 부여하지 않으며 저장 실패 시 기존 값/감사/확정 지급을 변경하지 않는다. 100%에도 기존 수업별 1,000원 단위 올림을 적용하므로 회당 판매 단가 이하라는 별도 상한을 도입하지 않는다. FIXED_AMOUNT·지원/기타 추가실적·기본급의 별도 금액 조건과 과거 확정 지급은 유지한다. 저장 타입/정규화·검증/오류 계약·동시 적용 순서는 기술 설계 대상이다.

상태/검증 경계: 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED를 유지한다. BR-009의 확정 시간 조건과 BR-010의 Rate 범위만 추가 해결됐으며 다른 입력/정산 조건·운영/계약 상세는 OPEN을 유지한다. K3의 첫 관리자 인증·지점 접근 제어 개발 검증 범위/순서와 별도 코드 작성 지시·운영 전 MFA/복구 검증 경계는 유지한다. ADR-0004 v1 인증 방식 ACCEPTED와 구체 모듈/공개 계약/UoW/잠금 PROPOSED를 구별한다. V-104–105는 미구성·미실행 검증 계획이다. 코드·migration·의존성/lockfile·실행 테스트 변경/수행은 없다.


<a id="review-20261013-m-batch"></a>
## 2026-10-13 일괄 승인 — M1–M2

사용자 답변: **“전부 1번. 이어서 계속 진행하자”**. 직전 질문 M1–M2의 각 1번을 승인했다. 기존 결정·이력을 보존하고 해당 범위만 추가 확정한다.

| 항목 | 선택 | 승인된 내용 | 유지할 경계 | 추적 |
| --- | --- | --- | --- | --- |
| M1 | 1 | 잘못 발급한 미사용 이용권은 기존 수동 만료로 잔여/이력을 보존한 뒤 올바른 이용권을 새로 발급한다. 별도 Pass 발급 취소 기능은 v1 제외 | 만료는 Master Organization/Branch Admin 현재 Issued Branch Scope·사유/감사. 새 발급은 별도 기존 Actor/Issued Branch·대상/상품/활성 담당 조건을 검증. 기존 Pass의 Member/발급 조건/잔여·PT/지급/정산 이력을 덮어쓰지 않음 | BR-OPS-025/004; PR-003/027; scope; BR-001/002·ARCH-003; V-106 |
| M2 | 1 | 수동 만료된 Pass만 담당한 현재 유효 Trainer도 해당 Member 및 이미 허용된 전체 전화번호를 조회할 수 있다. 수동 만료만으로 담당 조회 관계를 종료하지 않는다 | 목록/검색/직접 ID마다 현재 Caller/Organization·실제 현재 담당 또는 개별 지원 관계 확인. Trainer 자체 비활성/계정 차단/역할 회수·담당 교체/지원 해제의 기존 접근 제한과 만료 후 실제 새 수업 사용 차단은 유지 | BR-OPS-005/004/008/014; PR-002/003/029/030; NFR-001/005; MB-001/003; V-107 |

M1은 미사용 Pass의 발급 오류 처리 방식과 별도 발급 취소 기능의 v1 제외를 정한 것이다. 기존 Pass의 회원/상품/발급 조건·Issued Branch·담당·잔여와 이력을 삭제하거나 정상 새 발급으로 덮어쓰지 않는다. 만료 자체로 잔여를 0으로 만들지 않는다. 올바른 새 Pass는 별도 식별자와 발급 당시 조건/최초 횟수를 가지며 현재 허용된 발급 권한·Organization/Member/Branch/상품/활성 담당/중요 변경 감사 등의 기존 조건을 검증한다. 만료할 권한이 새 발급 권한을 자동 부여하지 않고 그 반대도 마찬가지다. 기존 수동 만료 해제는 유지하며 재발급 완료를 이유로 자동 해제하지 않는다. 잘못된 발급의 취소용 별도 상태/명령을 v1 필수 기능으로 추가하지 않는다. 이미 수행된 PT의 취소/잔여 복원이나 고객 결제/환불을 이 결정에 포함하지 않는다. 단계별 실패/재시도·원본과 새 발급의 관련성 표현/조회·UoW는 후속 기술 설계다.

M2는 수동 만료 Pass도 현재 담당 회원 조회의 근거로 인정한 것이다. 활성의 유효한 Trainer 연결/현재 권한과 실제 현재 담당 관계를 Backend에서 확인하며 만료를 우회해 미담당/미허용 Member 또는 다른 Organization을 조회하지 않는다. 담당이 바뀌면 이전 담당은 해당 과거 관계만으로 조회를 유지하지 않고 다른 현재 담당 Pass/개별 지원/독립 관리자 권한으로 각각 판단한다. 비활성 Trainer나 전체 계정 차단/회수 역할·폐기 AuthSession의 접근을 복구하지 않는다. 만료 Pass의 새 실제 수업 사용은 계속 차단하고 만료 전 실제 수업의 늦은 등록은 기존 예외/인가/현재 잔여·정산 조건을 따른다. 잔여 0 선택 제외 필터는 기존 Member 전체 Pass의 보존 잔여 기준이며 만료 잔여 5회를 0으로 바꾸거나 가용 횟수로 해석하지 않는다. 허용 전화번호 외 새 개인정보/개별 Pass·다른 Trainer PT/보상·내보내기/수정 권한은 추가하지 않는다. 수동 만료 Pass의 담당 교체 허용 여부는 이번 조회 결정과 구별하며 해당 잔여 게이트를 유지한다.

상태/검증 경계: 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED를 유지한다. BR-001/002·ARCH-003의 별도 발급 취소 v1 채택과 MB-001/003의 수동 만료 담당 조회 부분만 해결됐고 나머지 역사 사실·수량/다른 상태·입력/인가·공개/계약 상세는 유지한다. L1/L2 종료 월 확정·0~100% 정수 Rate와 K3 첫 관리자 개발 증분의 범위/순서·별도 코드 작성 지시/운영 전 MFA·복구 검증은 유지한다. ADR-0004 v1 인증 방식 ACCEPTED와 구체 모듈/공개 계약/UoW/잠금 PROPOSED를 구별한다. V-106/107은 미구성·미실행 검증 계획이다. 코드·migration·의존성/lockfile·실행 테스트 변경/수행은 없다.


<a id="review-20261013-n-batch"></a>
## 2026-10-13 일괄 승인 — N1–N2

사용자 답변: **“전부 1번.”**. 직전 N1–N2 질문의 각 1번을 승인했다. 기존 월 정산/보상 설정 정책과 구별해 개별 수업의 일반 Session Payment 및 지원 수업에 연결된 Additional Performance 금액의 공개 제한을 추가 확정한다.

| 항목 | 선택 | 승인된 내용 | 유지할 경계 | 추적 |
| --- | --- | --- | --- | --- |
| N1 | 1 | 관리자 권한 없는 Trainer에게 본인 PT 내역의 수업별 보상 금액을 공개하지 않는다. 허용된 본인 PT 진행 내역은 계속 조회한다 | 일반 Session Payment/지원 수업 연결 보상 모두 적용. H4 비관리자 Trainer 월 정산 v1 제외와 보상 설정 제한 유지. 관리자 겸임은 독립적인 기존 행위별 관리 Scope 적용 | BR-PAY-021/010/016; PR-008/029/030; NFR-001/005; ARCH-001·MB-005/006; V-108 |
| N2 | 1 | 현재 다른 Home Branch Trainer가 자기 지점에서 수행한 수업의 보상 금액은 수행 지점 Branch Admin에게 공개하지 않는다. 수업 기록은 기존 허용 Scope에서 조회한다 | Performed Branch는 해당 Trainer 보상 정보의 조회 근거가 아님. 현재 Trainer Home 기반 관리자 보상·정산 업무 Scope·Master Organization 및 겸임 독립 권한, 기존 CompSetting/전체 정산/지점 비용 보고 제한 유지 | BR-PAY-021/010/016; BR-OPS-001; PR-008/010/030; NFR-001/005; MB-005/006/010; V-109 |

N1/N2는 금액의 비공개이며 지급을 0원으로 만들거나 기존 확정 결과를 삭제/재계산하는 결정이 아니다. Backend는 등록 성공 응답·목록/검색/상세/직접 ID의 본문과 중첩 결과 등 제공되는 경로에서 비공개 금액이 전달되지 않도록 검증한다. Frontend에서만 숨기거나 원래 금액 대신 가짜 0원을 반환하지 않는다. 우회 합계/계산 근거·일반 오류/감사 조회 등으로 같은 비공개 금액을 노출하지 않으며 새 조회/집계/내보내기 기능을 추가하는 근거로 사용하지 않는다. 필드 생략/응답 분리·정확한 조회/오류 계약은 Architecture 상세다. 금액 미입력/0원·보상 상태의 공개 항목을 이번 금액 제한으로 일괄 승인하지 않는다.

예: 수원 Home Trainer A가 강남에서 수행한 지원 수업의 보상을 관리자가 30,000원으로 확정했어도 비관리자 A에게 본인 PT 내역의 그 금액을 공개하지 않는다. A의 현재 Home이 수원인 동안 강남 Branch Admin도 그 수업을 자기 지점에서 수행했다는 사실만으로 30,000원을 조회할 수 없다. 강남 관리자의 수업 기록 조회/정정 권한과 보상 설정·수업 보상 금액/월 정산 열람 권한은 각각 분리한다. 수원 관리자의 기존 현재 Home 기반 보상·정산 업무/전체 월 정산 구성 조회와 Master의 Organization 범위는 유지하되 그 권한만으로 다른 Performed Branch PT 기록 전체의 무제한 조회를 추가하지 않는다.

현재 Trainer Home은 각 조회 처리 시점의 실제 소속으로 검증한다. 과거 소속·지급 계산 시점/기록 시점·지원 수행 지점이나 최초 등록 Actor만으로 보상·정산 업무 Scope를 대체하지 않는다. 관리자·Trainer 겸임은 기존 독립 관리 권한/대상 Scope를 통과한 경우에만 해당 업무의 허용된 금액을 읽으며 겸임 자체로 무조건 공개하거나 본인이라는 이유로 차단하지 않는다. Operator 등 다른 역할의 미결정 지급 조회 권한을 추가하지 않는다. 본인 PT/소비 Pass·Member 정보 등 비금액 필드도 기존 공개 권한을 각각 따른다. 후속 Mobile/MSA에도 같은 업무 인가 경계를 유지하며 구현/기술 선택은 추가하지 않는다.

상태/검증 경계: 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED를 유지한다. ARCH-001·MB-005/006의 수업별 금액 공개 중 위 제한만 해결됐고 나머지 공개 필드·상태/역사 사실·세부 계산 근거/감사·계약 상세는 OPEN이다. M/L/K와 앞선 승인/감사·과거 결과 보존 및 별도 코드 작성 지시·운영 전 MFA/복구 의무는 유지한다. ADR-0004 v1 인증 방식 ACCEPTED와 구체 모듈/공개 계약/UoW/잠금 PROPOSED를 구별한다. V-108/109는 미구성·미실행 검증 계획이다. 코드·migration·의존성/lockfile·실행 테스트 변경/수행은 없다.


<a id="review-20261013-o-batch"></a>
## 2026-10-13 일괄 승인 — O1–O2

사용자 답변: **“모두 1번”**. 직전 O1–O2 질문의 각 1번을 승인했다.

| 항목 | 선택 | 승인된 내용 | 유지할 경계 | 추적 |
| --- | --- | --- | --- | --- |
| O1 | 1 | Trainer가 허용된 담당 회원의 실제 본인 수업을 등록할 때 다른 Trainer 담당분도 포함한 회원 전체 적격 Pass에서 FIXED_AMOUNT 우선/동일 Type FIFO로 차감한다 | 실제 수업 당시 이미 발급·사용 가능/현재 잔여 > 0 등 기존 조건 유지. Pass Assigned Trainer는 자동 변경하지 않고 실제 수행 Trainer의 보상 기준과 구별. 전체 후보 사용은 다른 Pass/Trainer 정보 무제한 조회 권한이 아님 | BR-OPS-026; BR-PAY-006/011; PR-008/029/030; ARCH-003·MB-001/003/005; V-110 |
| O2 | 1 | 개별 Trainer/Member 지원 허용은 회원 조회와 그 Trainer 본인의 실제 수업 등록 모두를 허용한다. 자기 담당 Pass가 없어도 해당 Member 전체 적격 Pass에서 차감한다 | 현재 Member Home 기반 Master/Branch Admin 지정·해제, 자동 종료 없음/동일 Organization Home 이동 후 유지 및 감사 유지. 지정 자체로 지원 보상 분류/금액 권한·정정/취소/발급 권한을 부여하지 않음. 과거 수업의 지원 허용 시간 경계는 별도 후속 | BR-OPS-005/026; BR-PAY-006/021; PR-008/029/030; NFR-001/002/005; MB-001/003/005; V-111 |

예: 같은 회원에게 A 담당 RATE 10회와 B 담당 FIXED_AMOUNT 2회가 있고 둘 다 적격이면 A가 본인 수업을 등록해도 FIXED_AMOUNT를 먼저 차감한다. 첫 등록 후 FIXED_AMOUNT 1회/RATE 10회이며 담당 B를 A로 바꾸지 않는다. 일반 수업의 확정 Session Payment는 실제 수행 A의 기록 생성 시점 설정과 선택한 Pass의 발급 조건으로 계산한다. B의 설정을 가져오지 않는다. 지원 수업은 기존대로 일반 지급 대신 전체 보상을 관리자가 추가실적으로 입력하며 미입력과 명시적 0원/정산 확정 차단을 구별한다.

개별 지원은 Member 접근/본인 수업 등록의 허용 관계다. 보상에서 말하는 일반/타 지점 지원 구분은 실제 수업 당시 Trainer Home Branch와 Performed Branch를 비교한다. 수원 Home Trainer가 개별 허용된 강남 Home 회원에게 수원에서 수업하면 일반 수업이고, 강남에서 수업하면 타 지점 지원 수업이다. Member Home·Pass Issued/Assigned Trainer나 지원 대상 지정 표시로 보상 구분을 대체하지 않는다.

전체 적격 후보는 같은 Organization/Member·실제 수업 당시 발급/사용 가능 여부·현재 잔여 > 0·현재 Caller/Trainer 연결과 기존 수업 당시/현재 상태·만료 전 실제 수업의 늦은 등록 예외·대상 월 정산 등 기존 검증을 통과한 Pass다. 이후 발급 Pass/잔여 0/해당 수업에 사용 불가인 Pass를 포함하거나 우선순위를 사용자 임의 선택으로 바꾸지 않는다. 회원 대상 인가와 서버의 후보 선택/차감은 별개 단계다. 다른 Member/Organization 접근, 다른 Trainer 프로필·PT 기록·보상 설정/금액의 무제한 조회를 추가하지 않는다. N1/N2의 등록 응답/조회 등 금액 비공개와 H4의 비관리자 Trainer 월 정산 v1 제외를 유지한다.

지원 지정/해제는 각 처리 시점 Member 현재 Home Branch의 Branch Admin 또는 Master Organization 범위로 검증하며 Trainer Home/수행/발급 지점만으로 권한을 주지 않는다. 기존 관리자가 해제할 때까지 유지/같은 Organization 내 Home 이동 후 자동 해제 없음·중요 변경 감사를 적용한다. 다른 Trainer 수업 대행, 회원/Pass 발급·변경, PT 정정/취소, 보상 조회·입력/월 정산 권한을 이 허용으로 추가하지 않는다. 지원 지정 전 수업 및 지정 당시 허용됐으나 해제 후 늦게 등록하는 과거 수업의 시간 경계/역사 사실은 이번 질문에 포함되지 않았으므로 후속 결정 없이 임의 허용/차단을 구현하지 않는다. BR-OPS-003의 이전 담당 당시 본인 실제 수업 등록 예외는 그대로 유지한다.

상태/검증 경계: 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED를 유지한다. ARCH-003·MB-001/003/005 중 다른 담당 Pass의 후보 포함과 개별 지원의 본인 등록 허용만 해결했다. 남은 지원 관계 시간 경계·역사 사실/상태·최소 공개/인가·저장/계약은 후속이다. ADR-0004의 v1 인증 방식 ACCEPTED와 구체 모듈/공개 계약/UoW/잠금 PROPOSED를 구별한다. K3 첫 관리자 개발 증분/별도 구현 지시 및 운영 전 MFA/복구 의무를 유지한다. V-110/111는 미구성·미실행 검증 계획이다. 코드·migration·의존성/lockfile·실행 테스트 변경/수행은 없다.


<a id="review-20261013-p-batch"></a>
## 2026-10-13 일괄 승인 — P1–P2

사용자 답변: **“모두 1번”**. 직전 P1–P2 질문의 각 1번을 승인했다. O2에서 남긴 지원 허용과 과거 수업 등록의 시간 관계를 확정한다.

| 항목 | 선택 | 승인된 내용 | 유지할 경계 | 추적 |
| --- | --- | --- | --- | --- |
| P1 | 1 | 현재 지원 허용이 유효하면 지정 전에 실제 진행한 본인 수업도 실제 수업일로 등록할 수 있다 | 지정 시점은 그대로 보존하며 과거에 이미 허용됐다고 이력을 소급 변경하지 않는다. 실제 수행·기존 계정/Trainer/Organization·Pass/잔여/정산 조건은 유지 | BR-OPS-027; BR-OPS-003/005/026; PR-008/029/030; MB-001/003/005; V-112 |
| P2 | 1 | 지원 해제 후에도 허용 기간에 실제 진행한 본인 수업은 늦게 직접 등록할 수 있다 | 일반 Member 목록/상세·전화번호 접근은 복원하지 않음. 해제 후 새 수업 등록까지 허용하지 않으며 현재 계정/Trainer 유효성·과거 허용/수행 사실·기존 Pass/정산 조건을 검증 | BR-OPS-027; BR-OPS-003/005/026; PR-008/029/030; NFR-001/002/005; MB-001/003/005; V-113 |

P1 예: 10월 5일 본인 실제 수업 → 6일 관리자 지원 지정 → 7일 등록을 허용한다. 6일의 현재 유효한 지원 허용으로 과거 본인 수업을 등록하는 것이며 지정일을 5일 이전으로 바꾸거나 그때 이미 지원 허용이 있었다고 기록하지 않는다. 미래 예약/수업 사전 승인 절차를 새로 도입하지 않는다.

P2 예: 10월 1일 지원 지정 → 5일 본인 실제 수업 → 6일 지원 해제 → 7일 등록을 허용한다. 이 허용만으로 해당 Member의 일반 목록/검색/상세·전체 전화번호·다른 Pass 원본/다른 Trainer 수업을 다시 조회하지 않는다. 과거 허용 기간에 실제 수행한 본인 수업을 등록하는 데 필요한 최소 대상 식별/명령 경로는 후속 Architecture에서 설계한다. 현재 지원 허용도 별도 담당/관리 근거도 없는 상태에서 해제 후 새로 진행한 수업을 P2로 등록할 수 없다. 과거 한때 지원 관계가 있었다는 사실만으로 지정 전 수업까지 P2의 허용 기간에 포함하지 않는다. P1의 지정 전 등록은 현재 유효한 지원 허용을 근거로 하며, P2는 해제 전 실제 허용 기간의 수업에 한정한다. 별도의 유효한 담당/현재 지원 또는 독립 관리자 권한은 해당 기존 규칙으로 판단한다.

두 경우 모두 검증된 현재 Caller와 본인 Trainer 연결·같은 Organization·계정/Trainer 유효성, 실제 본인 수행 날짜/시각과 기존 실제 수업 당시 Member/Trainer/Performed Branch 상태를 확인한다. P2에서는 실제 수업 당시 해당 Trainer/Member 지원 허용 사실/기간도 확인한다. 클라이언트가 보낸 과거 허용 표시/Member·Trainer ID/수업일만으로 인가하지 않으며 P1의 현재 허용을 과거 허용 이력으로 위조하지 않는다. 사실 확인 불가·충돌/정정과 같은 시점 순서/최소 공개·오류 계약은 후속이다. 임의 사실·현재 소속/상태로 과거 사실을 대체하지 않는다. 계정 차단·역할 회수/무효 AuthSession·Trainer 비활성 접근을 복구하지 않는다. 기존 비활성 전 수업의 인가된 관리자 대행 경로는 별개다.

O1/O2에 따라 그 Member 전체 적격 Pass에서 다른 담당분도 포함해 FIXED_AMOUNT 우선/동일 Type FIFO를 적용한다. 실제 수업 당시 이미 발급/사용 가능·현재 잔여 > 0·만료 전 실제 수업의 늦은 등록 예외와 일반 1회 차감을 유지한다. 지정/해제나 늦은 등록으로 Pass 담당자·Home/Issued/Performed·기존 소비/확정 지급을 자동 변경하지 않는다. 일반 지급은 신규 기록 생성 시점 실제 수행자 설정/선택 Pass 발급 조건, 보상 구분은 실제 수업 당시 Trainer Home과 Performed Branch다. 타 지점 지원 전체 보상의 관리자 수동 추가실적/미입력과 0원 구별·해당 월 확정 차단 및 N 금액 비공개/H4 월 정산 제한을 유지한다.

실제 진행 월이 미확정이면 기존 당월/최근 N일 제한 없는 늦은 등록 정책을 적용한다. 확정 월은 기존 인가된 관리자 해제 → 누락 반영 → 동일 월 재확정·사유/이전 확정본 보존을 따르며 Trainer에게 해제 권한을 주지 않는다. 지원 지정/해제 Actor는 각 처리 시점 Member 현재 Home Branch의 Branch Admin 또는 Master Organization 범위이고 자동 종료 없음/Home 이동 후 유지·중요 변경 감사는 그대로다. 이 결정으로 재지정·추가 관리자 승인·담당 되돌리기를 필수로 만들지 않는다. 다른 Trainer 수업 대행·회원/Pass 발급/변경·PT 정정/취소·보상 조회/입력/정산 권한은 추가하지 않는다.

상태/검증 경계: 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED를 유지한다. MB-001/003/005의 위 시간 정책은 해결됐으며 역사 사실 확인 불가/충돌·다른 상태/공개·구체 저장/계약은 후속이다. 기존 승인된 담당 교체 전 수업의 늦은 등록과 구별해 함께 유지한다. ADR-0004 v1 인증 방식 ACCEPTED와 구체 모듈/공개 계약/UoW/잠금 PROPOSED를 구별한다. K3 첫 관리자 개발 증분/별도 구현 지시 및 운영 전 MFA/복구 의무를 유지한다. V-112/113은 미구성·미실행 계획이다. 코드·migration·의존성/lockfile·실행 테스트 변경/수행은 없다.


<a id="review-20261013-q-batch"></a>
## 2026-10-13 일괄 승인 — Q1–Q2

사용자 답변: **“전부 1번”**. 직전 Q1–Q2 질문의 각 1번을 승인했다.

| 항목 | 선택 | 승인된 내용 | 유지할 경계 | 추적 |
| --- | --- | --- | --- | --- |
| Q1 | 1 | 새 Trainer 등록을 완료하려면 Rate·Fixed Amount·Base Salary를 명시적으로 입력한다. 기본급 적용 시작 월도 기존대로 명시한다 | 기본정보만 저장해 등록 완료한 뒤 보상을 나중에 설정하는 흐름은 채택하지 않음. 누락/미설정을 0·예시 값으로 대체하지 않으며 최초 보상 감사 적용. IAM 계정 발급/연결과 구별 | BR-OPS-028; BR-OPS-024; PR-005/007/027; BR-010·MB-001; V-114 |
| Q2 | 1 | 일반 보상 설정의 Fixed Amount·Base Salary는 명시적 0원 허용/음수 거부다. 기존 정수 원 입력과 관리 권한·변경 감사를 적용한다 | 누락≠0원. Rate 0~100% 정수·서비스 FIXED 계산/추가 올림 없음·지원 보상/월 수동 기본급의 사유 필수 0원 및 기타 추가실적 양수 규칙을 구별. 금액 상한/저장 표현은 후속 | BR-PAY-022; PR-007/008/010; NFR-012; BR-010/012; V-115 |

Q1은 Trainer 업무정보의 최초 등록 완료 조건이다. Master Admin은 자기 Organization 전체, Branch Admin은 등록할 Trainer Home Branch가 자기 단일 관리 Branch인 경우 기존 기본정보 등록 권한과 보상 최초 설정 권한을 각각 검증한다. Operator/Trainer 단독은 불가하며 관리자 겸임의 독립 Scope는 유지한다. 세 보상 값과 기본급 적용 시작 월 중 필수 입력을 누락하면 등록 완료로 처리하지 않는다. 시스템이 임의의 0%/50%/0원/현재 월을 기본값으로 채우지 않는다. 최초 설정에도 대상 Trainer·항목·변경 전/후·Actor/Role/Branch Context·시점의 기존 감사를 적용한다. 부분 저장으로 사용할 수 있는 정상 Trainer만 남기지 않도록 등록 완료의 일관성을 설계한다. 구체 테이블/모듈·공개 계약/UoW/잠금/재시도는 후속 PROPOSED다.

기본급은 지정한 적용 시작 월부터 다음 기본급 변경의 적용 시작 월 전까지 계속 유지한다. 적용 종료 월이나 유지할 미래 월 목록을 입력하지 않는다. 기존 미확정인 과거 월 지정/수동 지정 없는 미확정 정산 자동 반영·수동 지정 유지/과거 확정 정산 자동 변경 금지를 유지한다. 미래 시작 월을 얼마나 미리 등록할지와 최초 시작 월 이전의 월 적용 사실 등 미결정 월 범위/이력은 이번 필수 입력 결정으로 임의 확정하지 않는다. 월 정산을 자동 확정하거나 미입력 지원 보상 등 기존 조건을 면제하지 않는다.

Q2는 최초 설정과 이후 일반 설정 변경에 동일 적용한다. Fixed Amount/Base Salary는 0원·양수 정수 원을 허용하고 음수/소수 원은 거부하며 누락/null을 유효 0원으로 바꾸거나 자동 범위 보정/절사하지 않는다. Rate는 기존 0~100% 정수 규칙 그대로다. 명시적 Fixed Amount 0원은 일반 FIXED_AMOUNT 수업에 0원으로 계산되며 서비스 상품도 그 Trainer의 실제 설정값을 사용한다. 서비스라는 이유로 미입력 값을 자동 0원으로 만드는 것은 계속 금지다. 일반 FIXED_AMOUNT에 RATE의 1,000원 단위 올림을 적용하지 않는다. Base Salary 0원은 해당 설정이 적용되는 월의 일반 기본급 0원이며 다른 유효 Session Payment/추가실적을 지우지 않는다. 예: 적용 기본급 0원+유효 지급 100,000원+유효 추가실적 20,000원이면 월 합계는 120,000원이다.

기존 Master Organization/Branch Admin 각 처리 시점 Trainer 현재 Home Branch 설정 권한·관리 범위 안 본인 허용/별도 Master 승인 없음·감사를 유지한다. 0원이어도 Operator/Trainer 단독 또는 타 지점 지원 관리자에게 설정/금액 공개 권한을 주지 않는다. 이후 이름/연락처 등 일반 기본정보 수정에 세 보상 값 재입력을 요구하거나 미전달 보상 값을 0으로 덮어쓰지 않는다. 최초 등록의 결합 입력을 같은 DB 테이블/저장 소유권이나 IAM 계정·암호·역할/Trainer 연결의 자동 생성/변경으로 취급하지 않는다. 기존 IAM-001 첫 관리자 개발 증분에 Trainer 기능을 추가하지 않는다.

Rate/Fixed Amount는 관리자 저장 완료 이후 새로 생성하는 일반 지급에 적용하고, 현재 설정 변경으로 과거 확정 지급을 재계산하지 않는다. Base Salary도 과거 확정 정산을 자동 변경하지 않는다. 타 지점 지원 보상의 사유 필수 0원, 월별 수동 기본급의 사유 필수 0원/최초·수정 사유, 지원 수업 외 추가실적의 양수 전용 및 모든 기존 정정/해제/재확정 정책을 유지한다. Q2로 일반 설정의 0원에 별도 Master 승인이나 다른 업무의 사유 규칙을 새로 복사하지 않는다. 보상 설정/수업별 금액/정산의 기존 비공개와 겸임의 독립 관리 Scope를 유지한다.

상태/검증 경계: 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED를 유지한다. BR-010·MB-001 중 최초 보상 필수 입력/일반 Fixed Amount·Base Salary의 명시적 0원/음수 범위만 해결했다. 나머지 Product/Pass 입력 조건·금액 상한/저장 표현·역사 사실/월 범위·최소 공개/계약은 후속이다. ADR-0004 v1 인증 방식 ACCEPTED와 구체 모듈/공개 계약/UoW/잠금 PROPOSED를 구별하며 K3 첫 개발 범위/별도 구현 지시 및 운영 전 MFA/복구 의무를 유지한다. V-114/115는 미구성·미실행 계획이다. 코드·migration·의존성/lockfile·실행 테스트 변경/수행은 없다.


<a id="review-20261013-r-batch"></a>
## 2026-10-13 일괄 승인 — R1–R2

사용자 답변: **“전부 1번”**. 직전 R1–R2 질문의 각 1번을 승인했다.

| 항목 | 선택 | 승인된 내용 | 유지할 경계 | 추적 |
| --- | --- | --- | --- | --- |
| R1 | 1 | Trainer 전화번호는 이름·단일 Home Branch와 함께 관리하는 필수 기본정보다 | 기존 Master Organization/Branch Admin 신규 지정 Home·수정 시 현재 Home 인가 유지. 전화번호를 Login ID/본인인증 수단으로 사용하지 않으며 다른 개인정보/공개·중복/정규화/보존 정책은 별도 | BR-OPS-029; BR-OPS-024/028; PR-005/027; MB-001·LEGAL-001; V-116 |
| R2 | 1 | Branch Admin은 자기 관리 지점의 지점명·대표 연락처를 수정할 수 있다. 변경 감사를 적용한다 | 각 처리 시점 검증된 현재 단일 관리 Branch/Organization 범위만 허용. Master의 기존 Organization 관리 권한 유지. 지점 생성/운영 상태·관리자 배정/계정 Scope 변경과 구별 | BR-OPS-030; PR-020/027/030; NFR-001/004; MB-004; V-117 |

R1: 최초 Trainer 등록과 일반 이름/전화번호 수정에서 필수 전화번호를 누락/null/빈 값으로 저장하지 않는다. 변경하지 않는 전화번호는 유지하며 이름만 수정한다고 보상 세 값이나 전화번호를 재입력하도록 요구하지 않는다. Q1의 최초 세 보상 값/기본급 시작 월 명시 입력·Q2 일반 금액 범위·최초 감사/등록 완료 일관성을 함께 적용한다. 수정 인가는 Master Organization 또는 해당 Trainer의 현재 Home Branch 관리자, 신규 등록은 지정 Home Branch 기준이고 Operator/Trainer 단독은 계속 불가다. 전화번호 값만으로 IAM 계정·역할/Trainer 연결·Member를 합치거나 Login ID/비밀번호·보상 설정을 변경하지 않는다. 자동 SMS/전화 본인인증·비밀번호 재설정 전달 기능을 추가하지 않는다. 형식/정규화·중복 처리/필드 공개·보존/삭제와 구체 최소 응답/저장 계약은 후속이다. 실제 전화번호를 문서/일반 로그에 복사하지 않는다.

R2: Master는 기존 자기 Organization 전체 Branch 관리 범위를 유지한다. Branch Admin은 각 요청 처리 시점 현재 관리 Branch가 대상 Branch인 경우 지점명/대표 연락처를 수정한다. 클라이언트의 Branch ID/role·과거 Scope/최초 처리자라는 사실만으로 다른 Branch/Organization을 수정하지 않는다. Operator/Trainer 단독에는 수정 권한이 없으며 겸임자는 독립 관리 Scope로 판단한다. 위 두 필드 수정만으로 지점 생성/운영 상태·Organization/Branch 식별자·소속 이동/계정 역할/관리 Branch·상품/보상/정산을 변경하지 않는다. 다른 지점/필드에 대한 권한 우회 요청은 Backend에서 인가/허용 필드 경계를 검증한다. 대상 Branch·변경 항목/전후 값·Actor/Role/Branch Context·시점의 기존 중요 변경 감사를 적용하며 별도 Master 승인 대기를 도입하지 않는다.

지점명/대표 연락처 변경으로 같은 Branch의 식별자나 Trainer/Member Home·Pass Issued·과거 PT Performed의 지점 사실, 잔여·확정 지급/정산을 재작성하지 않는다. 과거 조회에 표시할 지점 이름/현재 기준정보와 이력 표현·필드별 입력 조건/대표 연락처 필수 여부·변경 실패/현재 권한 경합·최소 응답/감사 공개 계약은 후속이다. 이 승인을 IAM-001 첫 관리자 개발 증분에 두 편집 기능을 추가하는 지시로 취급하지 않는다.

상태/검증 경계: 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED를 유지한다. MB-001/004·LEGAL-001 중 Trainer 전화번호 필수와 자기 지점 두 기본정보 수정 권한만 해결했다. 나머지 개인정보/필드·상태/역사 사실·계정 위임/최소 계약은 후속이다. ADR-0004 v1 인증 방식 ACCEPTED와 구체 모듈/공개 계약/UoW/잠금 PROPOSED를 구별하며 K3 첫 개발 범위/별도 구현 지시 및 운영 전 MFA/복구 의무를 유지한다. V-116/117은 미구성·미실행 계획이다. 코드·migration·의존성/lockfile·실행 테스트 변경/수행은 없다.


<a id="review-20261013-s-batch"></a>
## 2026-10-13 일괄 승인 — S1–S2

사용자 답변: **“전부 1번”**. 직전 S1–S2 질문의 각 1번을 승인했다.

| 항목 | 선택 | 승인된 내용 | 유지할 경계 | 추적 |
| --- | --- | --- | --- | --- |
| S1 | 1 | 이전 월 정산 확정본과 확정 해제·재확정 이력은 Master 자기 Organization 또는 해당 Trainer의 현재 Home Branch Admin이 조회한다 | 각 조회 시점 현재 관리 Scope 기준. 과거 소속/Performed만으로 권한 없음. 원래 버전/정정 이유·변경자/시점 보존. 조회 권한을 쓰기·다른 업무 감사 열람으로 확대하지 않음 | BR-PAY-023; PR-010/027/030; ARCH-001·MB-006·BR-009; V-118 |
| S2 | 1 | Rate·Fixed Amount·Base Salary 변경 이력의 전후 값·변경자·시점은 Master 자기 Organization 또는 해당 Trainer의 현재 Home Branch Admin이 조회한다 | 세 항목 동일 정책·관리 Scope 안 본인 포함. Operator/Trainer 단독 불가. 당시 감사 사실 보존. 인증/계정 관리 감사는 계속 Master 전용 | BR-PAY-023; PR-007/027/030; NFR-001/004/005; ARCH-001; V-119 |

현재 Home 기준: 각 목록/검색·상세/직접 ID·제공되는 중첩 응답 등 조회마다 Backend가 검증된 현재 Actor/역할·Organization/관리 Branch와 대상 Trainer의 현재 Home Branch를 확인한다. Trainer가 수원에서 강남으로 이동하면 강남 Branch Admin은 수원 소속 시기의 위 정산/보상 설정 이력도 조회할 수 있다. 수원 Branch Admin은 과거 소속/기존 조회·원래 변경자 또는 수업 Performed Branch라는 사실만으로 계속 조회하지 못한다. Master Organization 전체와 관리 범위 안 본인 Trainer의 독립 관리자 겸임 권한을 유지한다. Operator/관리 권한 없는 Trainer는 본인 포함 위 이력을 조회하지 못한다.

S1: 이전 확정 버전과 확정 해제·재확정의 정정 이유/변경자/시점을 확인할 수 있다. 당시 확정 금액/적용 구성·과거 버전과 정정 사실을 보존하며 현재 보상 설정으로 재계산하거나 이전 버전을 덮어쓰지 않는다. 기존 현재 Home Branch Admin의 전체 월 정산 금액/구성 내역 공개(타 지점 수업 포함)를 유지한다. 이 조회 허용이 확정 해제/정정/재확정의 별도 행위 권한/조건을 면제하거나 다른 지점의 PT/Member/Pass 전체 원본 조회·다른 Trainer 이력·Master 전용 지점 비용 보고서 접근을 추가하지 않는다. N1/N2 수업별 보상 기밀성과 H4 비관리자 Trainer 월 정산 v1 제외를 유지한다.

S2: 세 설정의 최초 설정을 포함한 실제 변경 이력을 같은 Scope로 조회한다. 변경 전 값이 없었던 최초 설정과 명시적 0원을 구별한다. 원래 변경 전후 값·Actor/당시 Role/Branch Context·시점은 현재 조회자의 Scope에 맞춰 재작성하지 않는다. 설정 변경 권한·직접 반영/감사·새 PT 기록부터 적용·과거 지급/확정 정산 불변성은 유지하며 이력 조회 자체로 현재 값/기본급 적용 월을 변경하지 않는다. 타 지점 지원 수업/Performed Branch만으로 이력 접근 권한이 생기지 않는다.

업무 이력과 보안 감사의 경계: 위 정산/보상 설정 이력 조회만 승인했으며 C7의 로그인·계정 관리 감사는 자기 Organization Master만 조회한다. 일반 Audit 전체 열람 권한이나 신규 내보내기/통계 기능을 부여하지 않는다. 필요한 변경자 식별·이유/시점과 기존 이력 사실을 읽되 불필요한 개인정보/인증정보·원문 IP·전체 Login ID 등 추가 필드 공개를 이 승인으로 정하지 않는다. 현재 권한 철회·소속 변경과 조회의 경합, 최소 응답/필드 조합·저장/보존·추가 계산 근거/지점 비용 보고 계약은 후속이다.

상태/검증 경계: 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED를 유지한다. ARCH-001·MB-006·BR-009의 위 이력 조회 Actor/Scope만 해결했다. 구체 모듈/공개 계약/UoW/잠금은 PROPOSED이며 직접 DB 읽기 예외를 추가하지 않는다. K3 첫 개발 범위/별도 구현 지시 및 운영 전 MFA/복구 의무는 유지한다. V-118/119는 미구성·미실행 계획이다. 코드·migration·의존성/lockfile·실행 테스트 변경/수행은 없다.


<a id="review-20261013-t-batch"></a>
## 2026-10-13 일괄 승인 — T1–T2

사용자 답변: **“전부 1번”**. 직전 T1–T2 질문의 각 1번을 승인했다.

| 항목 | 선택 | 승인된 내용 | 유지할 경계 | 추적 |
| --- | --- | --- | --- | --- |
| T1 | 1 | Pass 발급 시각은 시스템에서 신규 발급을 완료한 시각으로 기록한다. 과거 발급 날짜 입력/소급 발급은 v1 제외다 | 실제 수업 당시 이미 발급된 Pass만 사용. 구매/입력 지연·현재 보유/담당·관리자 권한으로 발급 시각 소급 변경 불가. 원본/발급 조건·이력 보존 | BR-OPS-031; BR-PAY-006; PR-003/008; BR-001·ARCH-003; V-120 |
| T2 | 1 | 별도 사용 시작일 없이 발급 시점부터 기존 사용 조건을 충족하면 사용할 수 있다 | 별도 미래 시작일 예약/변경·시작 전 상태를 v1 기능으로 추가하지 않는다. 잔여/수동 만료·인가/실제 수업·정산 조건을 면제하지 않음 | BR-OPS-031; PR-003; BR-001·ARCH-003; V-121 |

T1의 시간 기준: Backend가 신규 발급 완료 시각을 기록한다. 클라이언트가 보낸 과거 날짜·실제 구매가 먼저였다는 주장/등록 지연을 근거로 발급 사실을 과거로 만들거나 기존 발급 시각을 수정하는 v1 기능은 두지 않는다. 10월 3일 구매했어도 시스템 발급이 10월 5일이면 해당 Pass는 10월 3일 실제 수업의 후보에 포함하지 않는다. 다른 적격 Pass가 있으면 그 후보 안에서 기존 우선순위를 적용하고, 후보가 없으면 이후 발급 Pass로 과거 수업의 조건을 우회하지 않는다. 실제 수업 시각을 발급 후로 임의 바꾸거나 오류 정정의 취소/재등록으로 이를 우회하지 않는다.

T2의 시작 의미: 별도 사용 시작 날짜/미래 시작 예약이나 수동 시작 명령은 두지 않고 발급 시점부터 잔여 > 0 등 기존 사용 조건으로 판단한다. 발급되었다는 사실만으로 누구나 조회/차감할 수 있는 것은 아니며 현재 Caller/Organization·허용 Member/본인 수행·실제 수업 시점의 상태와 정산/이력 조건을 검증한다. 별도 만료일/시간 경과 자동 만료는 기존대로 없고 관리자 수동 만료/해제·잔여 보존과 만료 전 실제 수업의 늦은 등록 예외를 유지한다. 과거 수업 등록은 실제 수업 당시 이미 발급된 조건을 계속 충족해야 한다.

기존 정책과 구별: 발급 시각은 PT 실제 시작 시각이나 PT 기록 생성 시각/일반 지급 적용 설정 시각과 구별한다. 발급 당시 Product 가격/총횟수/Payment Type·Issued Branch 및 원본 이력 보존, 최초 횟수 부여·활성 Assigned Trainer/기존 발급 인가·감사, 전체 적격 Pass의 FIXED_AMOUNT 우선/동일 Type FIFO는 유지한다. 발급 시각/별도 시작일 결정을 새 Pass 발급 권한·과거 지급 재계산·지원 보상 자동 입력 또는 기존 Pass 발급 오류 수정/소급 복구 권한으로 확대하지 않는다. M1의 미사용 오류 Pass 수동 만료 후 정상 새 발급도 새 발급 시각을 가지며 원래 Pass를 덮어쓰지 않는다.

상태/검증 경계: BR-001·ARCH-003의 발급/사용 시작 의미만 해결했다. 같은 시각의 정밀도/동시 순서·실패/commit 응답 유실·시간 저장/최소 응답·현재 상태와 과거 만료/해제 사실 판정/취소 복원·저장/UoW/잠금은 후속 설계다. 구현되지 않은 미래 시작/소급 발급을 임의 기본 기능으로 추가하지 않는다. 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED를 유지한다. 구체 모듈/공개 계약/UoW/잠금 PROPOSED와 K3 첫 개발 범위/별도 구현 지시·운영 전 MFA/복구 의무는 유지한다. V-120/121은 미구성·미실행 계획이다. 코드·migration·의존성/lockfile·실행 테스트 변경/수행은 없다.


<a id="review-20261013-u-batch"></a>
## 2026-10-13 승인 — U1

사용자 답변: **“1번”**. 직전 U1의 수동 만료 이용권 담당 교체 허용을 승인했다.

| 항목 | 선택 | 승인된 내용 | 유지할 경계 | 추적 |
| --- | --- | --- | --- | --- |
| U1 | 1 | 관리자가 수동 만료한 Pass도 기존 권한 범위에서 담당 Trainer를 교체할 수 있다 | 만료 상태·잔여·발급 시각/조건·과거 수업/지급/정산 유지. Master Organization/처리 시점 Member 현재 Home Branch Admin, 같은 Organization 실제 활성 Trainer 조건/감사 유지 | BR-OPS-008/005/004; PR-003/029/030; BR-001·MB-001·ARCH-001; V-122 |

교체 인가: Master는 자기 Organization 범위에서, Branch Admin은 각 교체 처리 시점 대상 Pass의 Member 현재 Home Branch가 자신의 현재 관리 Branch인 경우 처리한다. Pass Issued Branch/Trainer Home Branch·수업 Performed Branch 또는 최초 발급자/과거 Scope만으로 권한을 얻지 않는다. 같은 Organization의 실제 활성 Trainer만 새로 지정하며 타 지점 Home도 기존 조건 안에서 허용한다. Operator/Trainer 단독은 교체 불가이고 겸임자는 해당 독립 관리자 Scope로 판단한다. 기존 범위 내 직접 처리·별도 Master 승인 대기 없음과 전후 담당/Actor·Branch Context·시점 이력/감사를 유지한다. 새로운 필수 변경 사유를 추가하지 않는다.

만료와 담당의 분리: 수원 발급·강남 Home Member의 수동 만료/잔여 5회 Pass를 강남 Branch Admin이 A→B로 교체해도 같은 Pass의 만료/잔여 5회·Issued Branch·발급 시각/조건과 과거 A의 실제 수업/확정 지급·정산은 유지한다. 이 교체 권한은 수원 Issued Branch 기준의 만료 해제/횟수 조정 권한을 추가하지 않는다. 자동 만료 해제·새 Pass 발급·잔여 증가/초기화·과거 수행자/보상 재작성은 하지 않는다. 담당만 바뀐 현재 만료 Pass로 새 수업을 진행/차감할 수 있는 것은 아니며 만료 전 실제 수업의 늦은 등록 예외는 기존 조건을 그대로 따른다.

조회 관계: 새 담당 B는 만료 Pass도 담당 관계의 근거로 인정하는 M2/BR-OPS-005에 따라 허용된 Member/전체 전화번호 조회·응대를 이어간다. 이전 담당 A는 다른 현재 담당 Pass/개별 지원/독립 관리 권한 등 유효 근거 없이 과거 담당이었다는 이유만으로 일반 Member 조회를 유지하지 않는다. 교체 전 실제 본인 수업의 늦은 등록 허용과 그 최소 식별/인가 계약은 별개로 유지한다. 다른 Pass/PT/Trainer의 정보·보상 설정/금액 또는 정정·계정 관리 권한을 추가하지 않는다.

상태/검증 경계: 수동 만료라는 상태 자체를 담당 교체 금지 사유로 두지 않는 것만 해결했다. 다른 Member/Trainer·Branch/계정 상태 조합·역사 사실 확인 불가/정정·최소 선택/응답/감사 계약과 현재 Member Home 이동/역할 회수·Trainer 비활성/담당 교체/만료·수업 등록의 경합은 후속이다. 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED를 유지한다. 구체 모듈/공개 계약/UoW/잠금은 PROPOSED이며 직접 DB 읽기 예외를 추가하지 않는다. K3 첫 개발 범위/별도 구현 지시와 운영 전 MFA/복구 의무는 유지한다. V-122는 미구성·미실행 계획이다. 코드·migration·의존성/lockfile·실행 테스트 변경/수행은 없다.


<a id="review-20261013-v-batch"></a>
## 2026-10-13 승인 — V1

사용자 답변: **“1”**. 직전 V1의 1번, 과거 소속 이력 오류의 Master 전용 정정을 승인했다.

| 항목 | 선택 | 승인된 내용 | 유지할 경계 | 추적 |
| --- | --- | --- | --- | --- |
| V1 | 1 | 이미 기록된 Trainer·Member의 과거 Home Branch 소속 이력 오류는 Master만 자기 Organization 범위에서 사유를 남기고 정정한다. 원래 이력도 보존한다 | 일반 이동은 즉시 적용 유지. 과거 지급액/정산 확정본 자동 덮어쓰기 없음. 영향 건은 기존 정정/확정 해제·재확정 절차. 상세 수업 분류 정정/보상 기준·계약은 후속 | BR-OPS-032/007/013; PR-002/005/009/010/027/030; MB-001/002/005/010; V-123 |

인가/사유: Backend는 정정 처리 시점의 검증된 현재 Master 역할과 대상 Trainer/Member·소속 지점 사실의 자기 Organization 범위를 확인한다. Branch Admin은 Member의 현재 Home 관리자이거나 이동 전후 지점/Trainer 계정 발급자여도 이 과거 이력을 정정하지 못한다. Operator/Trainer 단독도 불가하며 관리자 겸임은 현재 Master 권한이 있을 때만 허용한다. 직접 대상 ID/클라이언트 role·과거 Scope로 우회할 수 없다. 오류 정정 사유는 필수이며 누락 시 정정을 거부하고 요청 직전 사실/이력·기존 업무 결과를 유지한다.

원래 기록과 정정 사실: 대상 Trainer/Member·정정 대상 소속/시점 사실·정정 전후 내용·원래 이력·사유/Actor/현재 Master 권한/Branch Context·정정 처리 시점을 추적한다. 과거 소속의 사실 시점과 이번 정정 처리 시각을 구별하며 원래 이력을 삭제하거나 조용히 덮어쓰지 않는다. 실제 과거 오류를 바로잡는 별도 관리 작업이며 일반 Member/Trainer 이동의 저장 완료 즉시 적용·미래 예약 미지원/기존 Actor 범위는 유지한다. 과거 사실이 없거나 확인 불가하다고 현재 Home/임의 지점·시각을 대입하지 않는다.

업무 영향: Trainer의 실제 당시 Home/Performed에 따른 일반·지원 분류, 대상 월말 Home 기본급 비용/비지원 실적 발생 당시 Home 비용 등 영향 사실을 대조한다. 유효하게 정정된 소속 사실은 후속 역사 사실 확인 계약의 입력이지만, 이미 있는 PT/Pass 소비·확정 지급/지원 보상·월 정산 원본을 일괄 갱신하거나 현재 설정으로 자동 재계산하지 않는다. 영향 수업/정산은 기존 행위별 권한·정정 이력/사유와 필요한 각 Trainer/월 확정 해제 → 정정 반영 → 같은 월 재확정/이전 확정본 보존 절차를 따른다. 과거 소속 오류로 일반/지원 분류가 달라지는 기존 PT의 정정 방식·Pass 처리/일반 지급 적용 설정 시점 및 비용 보고 정정/버전 계약은 이번 답변으로 추가 확정하지 않는다.

권한/기능 경계: 이 승인은 일반 소속 이동의 과거 날짜 선택이나 Pass 발급 시각·지원 지정/해제 이력의 소급 변경 권한을 부여하지 않는다. 현재 계정/역할·관리 Branch/Operator Scope, 현재 담당/지원 관계·원래 보상 설정/인증 이력은 자동 재작성/복원하지 않는다. 정정 이력 저장/공개·최소 응답/영향 건 식별과 현재 Home까지 달라지는 정정의 상태/인가·변경 경합은 후속이다. 관련 이력 열람은 기존 업무별 Scope를 따르며 일반 Audit 전체 열람 권한을 추가하지 않는다.

상태/검증 경계: MB-001/002/005/010의 과거 Home 이력 오류 정정 허용/Master Organization 전용·사유/원본 보존만 해결했다. 나머지 상태·확인 불가/영향 처리·최소 계약/저장/보존·수업/보상 정정 정책은 관련 게이트를 유지한다. 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED를 유지한다. 구체 모듈/공개 계약/UoW/잠금은 PROPOSED이며 직접 DB 읽기 예외를 추가하지 않는다. K3 첫 개발 범위/별도 구현 지시와 운영 전 MFA/복구 의무는 유지한다. V-123은 미구성·미실행 계획이다. 코드·migration·의존성/lockfile·실행 테스트 변경/수행은 없다.


<a id="review-20261013-w-batch"></a>
## 2026-10-13 일괄 승인 — W1–W2

사용자 답변: **“전부 1번”**. 직전 W1/W2의 1번을 모두 승인했다.

| 항목 | 선택 | 승인된 내용 | 유지할 경계 | 추적 |
| --- | --- | --- | --- | --- |
| W1 | 1 | Trainer 과거 Home 오류 정정으로 기존 수업의 일반/지원 분류가 달라지면 Master가 같은 PT 기록·기존 Pass 차감을 유지하며 분류·보상을 명시적으로 정정한다. 일반 지급은 최초 기록 생성 시점 설정, 지원 보상은 관리자 수동 추가실적 | 실제 수업의 Member/수행자/시작/Performed는 그대로. 취소 재등록·복원/재차감·재선택 없음. 이전 보상 결과 이력 보존/유효 합계 이중 반영 금지. 기존 보상 입력·정산 해제 권한 유지 | BR-OPS-033; BR-PAY-011/015/024; PR-005/009/010/030/031; BR-007; MB-001/005/010; V-124 |
| W2 | 1 | 과거 Home 오류의 영향을 받는 분류/보상·비용 정정이 모두 완료되어야 해당 Trainer·월 정산을 확정·재확정할 수 있다 | 미완료 경고만으로 확정 허용 안 함. 해당 Trainer·월만 적용. 기존 확정본 자동 해제/변경 없음. 종료 월·지원 금액 미입력 차단/현재 확정 권한 등 기존 조건 유지 | BR-PAY-024; PR-010/027/030; BR-009; MB-005/006/010; V-125 |

W1 대상/인가: 실제 Member·수행 Trainer·수업 시작 날짜/시각·Performed Branch가 그대로인데 V1의 Trainer 과거 Home 오류 정정 때문에 일반/지원 분류가 달라진 기존 PT를 대상으로 한다. Backend가 정정 처리 시점의 현재 Master·자기 Organization 및 대상 사실을 검증한다. Branch Admin의 현재 Trainer Home/수행 지점 관리 권한으로 이 분류 정정을 대신하지 못한다. 사유/원래 Home 이력·PT/이전 보상 결과와 정정 전후/Actor/시점·감사를 보존한다. 소속 이력 정정 자체가 자동 일괄 정정/보상 계산 명령은 아니다.

같은 기록/차감: 기존 PT 식별자·최초 기록 생성 시각·기존 소비 Pass와 1회 차감을 유지한다. 취소 재등록·잔여 복원/재차감·Pass 재선택이나 Assigned Trainer 재작성을 하지 않는다. 정정된 실제 당시 Trainer Home과 실제 Performed로 분류하며 현재 Home으로 과거를 대체하지 않는다. Member/실제 수행자/실제 시작 오류의 기존 취소 후 재등록 및 새 기록 생성 시점 설정 적용은 별개로 유지한다. 기존 Master 전용 Performed 값 정정 규칙도 유지한다.

지원 → 일반: 실제 수행 Trainer의 **최초 PT 기록 생성 시점 Rate/Fixed Amount**와 이미 소비한 Pass의 발급 시 Price/Session Count/Payment Type을 사용한다. 당시 Rate 50%, 정정 시 60%이면 50%다. RATE 1,000원 단위 올림·FIXED_AMOUNT 재올림 없음/서비스 PT 실제 Fixed Amount·명시적 0원과 미입력 구별을 유지한다. 최초 기록 때 일반 지급을 계산하지 않았어도 동일하며 역사 설정이 없거나 불명확하면 현재 설정/임의 값·0원으로 대체하지 않는다. 이전 지원 보상은 이력으로 보존하고 유효 합계에서 제외해 일반 지급과 중복 합산하지 않는다.

일반 → 지원: 이전 일반 지급은 이력으로 보존하되 유효 합계에서 제외한다. 해당 수업의 보상 전체를 추가실적으로 처리하며 기존 일반 지급액을 자동 복사하거나 0원으로 대입하지 않는다. 추가실적 입력은 기존 Master Organization/각 행위 시점 Trainer 현재 Home Branch Admin의 허용 범위에서 관리자가 직접 수행한다. 수업 분류 정정의 Master 전용 권한을 모든 후속 추가실적 입력의 Master 전용 제한으로 확대하지 않으며 수행 지점 관리자에게 타 Home Trainer의 금액/보상 설정 권한을 추가하지 않는다. 미입력과 사유를 남긴 명시적 0원을 구별하고 미입력 지원 보상은 해당 Trainer·월 확정을 차단한다. 정정 전후 유효 일반 지급/지원 추가실적을 동시에 합산하지 않는다.

W2 확정 조건: 과거 Home 오류로 영향을 받은 해당 Trainer·월의 분류/보상·비용 정정이 남으면 최초 확정과 재확정을 거부한다. 관리자 경고 확인/임의 완료 표시/현재 값 또는 0원 대입으로 우회하지 않는다. 관련 없는 Trainer·월이나 전체 개발을 차단하는 전역 게이트가 아니다. 소속 이력 정정만으로 기존 확정본을 자동 해제/재계산하지 않으며 필요한 각 확정 Trainer·월은 기존 행위별 현재 권한/사유·확정 해제 → 명시적 정정 → 같은 월 재확정/이전본 보존 절차를 따른다. 종료 월만 확정·미입력 지원 보상 차단·현재 Trainer Home 기반 확정 권한 및 기존 유효 구성 조건도 계속 적용한다.

남은 설계/검증: 영향 건 식별·완료 증거/반복 정정·역사 설정 확인/분류 전환·비용 보고 버전의 최소 계약/소유권·실패 원자성/동시 정정·월 확정 경합은 상세 설계 대상이다. 임의 완료 기본값/새 상태 enum·일괄 정정 API·자동 금액 재사용·과거 인가/지원 관계 복원은 채택하지 않는다. 수업별 금액 비공개/현재 Trainer Home 기준 보상·정산/이력 공개·C7 Master 전용 인증 감사와 기존 비용 귀속은 유지한다. BR-007/009·MB-001/005/006/010 등의 해당 부분만 해결하며 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED를 유지한다. 구체 모듈/계약/UoW/잠금 PROPOSED·직접 DB 읽기 예외 0건과 K3 첫 개발 범위/별도 구현 지시 경계를 유지한다. V-124/125는 미구성·미실행 계획이다. 코드·migration·의존성/lockfile·실행 테스트 변경/수행은 없다.


<a id="review-20261013-x-batch"></a>
## 2026-10-13 승인 — X1

사용자 답변: **“1”**. 직전 X1의 1번, 첫 IAM 구현에서 Branch Admin 계정 발급 응답 유실을 정확한 Login ID 조회/설정 대기 링크 재발급으로 복구하는 기능 보완을 승인했다.

| 항목 | 선택 | 승인된 내용 | 유지할 경계 | 추적 |
| --- | --- | --- | --- | --- |
| X1 | 1 | S1에 Master의 자기 Organization Branch Admin 정확한 Login ID 조회를 포함한다. 발급 응답을 잃어 account ID/설정 링크를 못 받아도 현재 계정 상태·관리 Scope/version을 확인하고 설정 대기 상태에서 기존 최초 설정 링크 재발급으로 진행한다 | A4 30분 단일 사용/이전 링크 폐기, 현재 Master/Organization·상태/경합 재검사·감사 유지. 원래 token 사후 조회/중복 생성·숨은 자동 재시도·ACTIVE/DISABLED 강제 reset 없음. API/모듈/UoW/잠금 채택·코드 작성 지시 아님 | PR-021/027/030, NFR-001/002/004, ARCH-001/002, IAM-001 S1, V-126 |

허용 범위: Backend는 매 조회/재발급 요청에서 검증된 현재 Master·자기 Organization과 대상 Branch Admin 사실을 확인한다. 정확한 Login ID 비교에는 기존 대소문자 미구별 정책을 적용한다. Branch Admin/Operator/Trainer 단독·다른 Organization·철회된 과거 Caller/직접 대상 ID·클라이언트 role/organization_id로 우회하지 못한다. Master 겸임은 독립 현재 Master Scope로 판단한다. 이는 S1 Branch Admin 발급 결과 확인용이며 일반 계정 목록/부분 검색·추가 Master/Operator/Trainer 계정 관리나 다른 개인정보 공개를 추가하지 않는다.

결과 확인과 재발급: 조회는 ID·현재 Login ID/설정 상태·관리 Scope/version 확인용이며 계정/Scope·설정 token 상태를 변경하지 않는다. 조회된 계정이 의도한 대상/지점인지 확인하며 같은 Login ID가 있다는 것만으로 직전 발급 시도의 성공을 단정하지 않는다. PENDING_SETUP에서만 기존 최초 설정 재발급을 실행하고 현재 권한/대상 상태·최신 version을 다시 확인한다. 새 링크는 30분 단일 사용이며 이전 최초 설정 링크 폐기·version/감사를 함께 반영한다. ACTIVE/DISABLED/Master 등 후속 대상에는 이 경로로 암호 재설정/상태 복구를 제공하지 않는다. 원래 token 원문은 다시 조회하지 않고 새 token은 성공 응답에서 한 번만 제공한다.

불명확한 결과/실패: 발급/재발급 응답 유실은 rollback 증거가 아니며 성공/실패를 추정하거나 계정을 자동 중복 생성/링크 자동 반복 발급하지 않는다. 미존재 조회만으로 진행 중 commit 부재를 단정하지 않고 상태/version을 재확인한다. 알려진 실패/감사 실패는 변경/철회/소비를 rollback해 기존 유효 상태를 보존하며 commit 결과 불명확은 재확인 전 실패 확정으로 보고하지 않는다. 새 조회와 재발급은 각각 현재 권한/상태를 검증하므로 그 사이 활성화·차단·Scope 변경이 있으면 옛 조회 결과로 재발급을 승인하지 않는다.

이전 설계 한계의 대체: X1 범위의 account ID 미확보만으로 S1 개발 run 중단/S2 재조회 보완을 요구하던 초안은 위 조회/재발급 흐름으로 대체한다. 유일 Master 분실/침해·DB 불능/소유권 불명 등 다른 중단 조건과 DISABLED 복구·ACTIVE reset/추가 Master·Trainer 연결의 후속 분리, 운영 전 MFA/복구 의무는 유지한다. Bootstrap 재실행/DB 초기화/고정 fixture로 계정 복구를 대신하지 않는다.

승인/검증 경계: 기능 보완/인가 범위만 승인됐으며 API 명칭/필드·물리 저장/소유권/공개 계약·UoW/잠금·오류/하네스 상세는 PROPOSED다. ARCH-001/002의 나머지 수명·역할/상태·최소 계약·반복 제한/보안·보존/운영 게이트 때문에 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED를 유지한다. 직접 DB 읽기 예외 0건·기존 PT/보상/정산 정책과 K3 첫 흐름·별도 구현 지시 경계도 유지한다. V-126은 실제 PostgreSQL 발급 응답 유실→조회→재발급→옛 링크 거부/새 링크 설정→실제 로그인 및 인가/경합/실패 원자성의 미구성·미실행 계획이다. 코드·migration·의존성/lockfile·제품/DB/브라우저 검사 변경/수행은 없다.


<a id="review-20261013-y-batch"></a>
## 2026-10-13 일괄 승인 — Y1–Y2

사용자 답변: **“1”**. 직전 Y1–Y2 표의 공통 1번 답변으로 반영하며 Y1/Y2 모두 1번으로 이해했음을 사용자에게 알렸다.

| 항목 | 선택 | 승인된 내용 | 유지할 경계 | 추적 |
| --- | --- | --- | --- | --- |
| Y1 | 1 | v1 Master 전용 지점 비용 보고서는 한국 시간 기준 종료된 월만 조회한다 | 당월 Trainer 월 정산 미확정 조회·검토는 유지. 당월 잠정 지점 비용/미래 월 예측·추가 연간 통계를 이번 범위에 포함하지 않음. 기존 비용 귀속 유지 | BR-PAY-025; PR-010/011/030; NFR-001/012; BR-009; MB-006/010; V-127 |
| Y2 | 1 | 미완료 영향이 없는 현재 유효한 최신 Trainer·월 확정본만 지점 비용 합계에 반영한다. 미확정·확정 해제 중·소속 오류 영향 정정 대기 Trainer·월은 합계에서 제외하고 미완료 현황을 별도 표시한다 | 미완료를 0원/전체 월 비용 완성으로 취급하지 않음. 확정본/원본 지급 자동 변경 없음. 이전/해제된 확정본 중복 합산 금지. 상세 항목/완전성·버전/동시 조회 계약 후속 | BR-PAY-025; PR-010/027/030; NFR-001/002/004; BR-009; MB-006/010; V-128 |

기간/인가: Backend에서 현재 Master·자기 Organization과 요청한 대상 월이 공통 Asia/Seoul 기준 종료됐는지 확인한다. 다음 달 1일 00:00부터 직전 월 조회가 가능하다. Master도 당월/미래 월의 지점 비용 보고서를 이 기능으로 조회하지 않는다. 보고서 기간 제한은 L1의 월 확정 시간 조건과 구별되는 별도 결정이며 기존 관리자 범위의 당월 Trainer 월 정산 조회·검토는 유지한다. Branch Admin은 자기 지점 비용 합계도 이 보고서로 열람하지 못하고 Operator/Trainer 단독도 불가하다. 겸임은 현재 Master의 독립 Scope로 판단한다.

집계 입력: 각 Trainer·대상 월의 현재 유효한 최신 확정본 중 미완료 영향이 없는 것만 한 번 반영한다. 아직 미확정/확정 해제 중이거나 과거 Home 오류 영향의 분류/보상·비용 정정이 남은 Trainer·월은 그 월의 비용 합계에서 제외한다. 이전 확정본이나 해제된 확정본을 대체 입력으로 끌어오거나 최신/이전 버전을 더하지 않는다. 소속 오류 정정으로 기존 확정본 자체를 자동 해제/변경하지 않더라도 정정 대기 영향 건은 이 보고서에서 정상 완료 비용으로 합산하지 않는다. 필요한 해제/정정/동일 월 재확정이 완료되면 그때 현재 유효한 최신 확정본으로 반영한다.

미완료 공개: 제외된 Trainer·월과 미확정/해제 중/소속 오류 영향 정정 대기 등 미완료 사유를 식별할 수 있어야 한다. 합계는 포함된 확정 비용의 합계이며 미완료가 남아 있는데 Organization 전체 월 비용이 완성됐다고 표시하지 않는다. 미완료 금액을 0원으로 대입하거나 누락을 숨겨 정확한 총비용처럼 보여주지 않는다. 명시적으로 확정된 정상 0원은 미입력과 구별한다. 미완료 항목의 구체 응답/목록·대상 집합 식별/완료 증거/정정 해제·재확정과 조회의 일관성은 후속 계약이며 임의로 존재하는 정산 행만 대상을 정해 누락을 숨기지 않는다.

금액/비용 귀속: Trainer 월 정산 합계와 Branch 비용은 같은 보상의 서로 다른 집계 관점이다. 일반 지급/지원 수업 보상은 실제 Performed Branch, 기본급은 대상 월말 Home Branch 한 곳에 해당 월 적용액 전액, 비지원 추가실적은 발생 당시 Home Branch를 유지한다. 현재 Rate/Fixed Amount/Base Salary·현재 Home/지점 활성 여부로 과거 확정 비용을 다시 계산/배분하지 않으며 기본급/지원 보상·이전/최신 버전을 중복 가산하지 않는다. 입력/역사 사실을 확인할 수 없으면 현재 값/임의 지점·0원으로 완성하지 않고 기존 게이트를 유지한다. 이 승인은 비용 귀속/원본 정정 권한·실제 지급/청구·송금 기능을 추가하지 않는다.

원본/범위 보존: 보고서의 합산 필터·미완료 표시이며 PT/Pass 차감·일반 지급/지원 보상·이전/현재 확정본을 자동 수정/취소/해제하는 명령이 아니다. 기존 W2의 영향 정정 완료 전 해당 Trainer·월 확정/재확정 차단과 기존 현재 인가·사유/감사·해제/정정/같은 월 재확정·이전본 보존을 유지한다. K3/X1 첫 IAM 흐름/후속 수명·Trainer 분리와 운영 전 MFA/복구 의무는 변하지 않는다.

승인/검증 경계: 기간/집계 입력·미완료 공개만 해결했다. 보고서 상세 항목/Trainer별 내역·월 정산 대상 집합/미완료 식별/역사 사실·비용 배분의 버전/최소 계약/소유권·UoW/잠금·실패/동시 조회는 후속 설계/관련 게이트다. BR-009·MB-006/010 등의 복합 OPEN과 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED를 유지한다. 구체 모듈/API/공개 계약/UoW/잠금 PROPOSED·직접 DB 읽기 예외 0건과 별도 구현 지시 경계를 유지한다. V-127/128은 미구성·미실행 계획이다. 코드·migration·의존성/lockfile·제품/DB/브라우저 검사 변경/수행은 없다.


<a id="review-20261013-z-batch"></a>
## 2026-10-13 승인 — Z1

사용자 답변: **“1”**. 직전 Z1의 1번, Master 전용 지점 비용 보고서에서 지점별·항목별 합계와 Trainer별 기여 금액까지 조회하는 상세 수준을 승인했다.

| 항목 | 선택 | 승인된 내용 | 유지할 경계 | 추적 |
| --- | --- | --- | --- | --- |
| Z1 | 1 | v1 Master 전용 지점 비용 보고서는 지점별 합계와 기본급/일반 PT 수당/지원 수업 보상/기타 추가실적 구분, 해당 지점 비용에 기여한 Trainer별 항목/금액 내역까지 제공한다 | 기존 비용 귀속/한 번 합산, Master Org 전용·Y1/Y2 종료 월/최신 유효 확정본·미완료 제외/표시 유지. Trainer 월 전체 지급액을 각 지점에 복제하지 않음. 최소 응답/소유권·버전/동시 조회 계약 후속 | BR-PAY-025; PR-010/027/030; NFR-001/002/004; BR-009; MB-006/010; V-129 |

상세 조회/인가: 현재 Master가 자기 Organization 범위의 지점 비용 합계와 기본급·일반 PT 수당·지원 수업 보상·기타 추가실적별 소계, 그 비용에 기여한 Trainer별 해당 항목/금액을 조회한다. Backend는 목록/상세·직접 지점/Trainer ID와 제공되는 집계 모두에 현재 Master/Organization Scope를 적용한다. Branch Admin은 자기 지점 비용 합계/Trainer별 비용 내역도 이 보고서로 열람하지 못하며 Operator/Trainer 단독도 불가하다. 겸임은 독립 현재 Master Scope로 판단한다. 보고서에 Trainer가 나타나는 사실만으로 다른 Actor에게 보상 설정/금액·전체 정산 권한을 추가하지 않는다.

기여 금액/검산: Trainer별 내역은 해당 Trainer의 **그 지점에 귀속되는 비용**이다. 그 Trainer 월 정산 전체 금액을 모든 관련 지점에 반복 표시/합산하지 않는다. 기본급은 대상 월말 Home 한 곳에 해당 월 적용액 전액, 일반 지급/지원 수업 보상은 실제 Performed, 비지원 추가실적은 실제 발생 당시 Home을 유지한다. 지원 수업은 전체 보상 추가실적이며 일반 지급을 별도로 더하지 않는다. 지점의 Trainer별 항목 합계와 지점 항목별 소계·총계, 포함된 모든 지점 비용 합계와 포함된 유효 Trainer월 확정본의 구성/합계를 대조할 수 있어야 한다. 현재 Home/설정·지점 활성 여부로 과거 귀속/금액을 다시 계산하거나 기본급을 지점 수만큼 복제하지 않는다.

비식별 예: 포함 가능한 Trainer A의 9월 비용이 기본급 2,500,000원(월말 강남), 일반 PT 수원 200,000원/강남 300,000원, 지원 수업 강남 80,000원, 기타 추가실적 수원 50,000원이면 수원 기여액은 250,000원, 강남 기여액은 2,880,000원이며 합계는 3,130,000원이다. 각 지점에 3,130,000원을 다시 더하지 않고 지원 보상 80,000원을 일반 PT 항목에도 중복하지 않는다. 이 예는 기존 귀속 규칙의 설명이며 새로운 지급/비용 계산 정책이나 실제 운영 데이터가 아니다.

집계 입력/미완료: Y1/Y2의 종료된 월과 미완료 영향 없는 현재 유효 최신 Trainer월 확정본만 사용한다. 미확정/해제 중/소속 오류 영향 정정 대기 Trainer·월은 소계·총계뿐 아니라 확정 비용의 Trainer별 상세에서도 제외하고 미완료 현황으로 구별한다. Trainer 상세에서 제외한 금액을 합계에 몰래 포함하거나 미완료를 0원/전체 월 비용 완성으로 표시하지 않는다. 이전 확정본을 대체 입력으로 사용하지 않고 정정/재확정 완료 후 현재 유효 최신본을 한 번 반영한다. 원래 PT/Pass 차감·지급/AP·확정본/감사는 보존하고 자동 수정/해제하지 않는다. 기존 당월 Trainer 월 정산 조회·현재 Home 관리자 공개 범위도 유지한다.

기능/검증 경계: 지점·항목·Trainer 기여 금액의 상세 수준만 해결했다. Trainer 선택용 최소 식별/이름·응답 DTO/화면·월 대상 집합/미완료 식별·역사 비용/버전·일관된 목록/상세/합계·소유권/공개 계약·UoW/잠금은 후속이다. 회원 전화번호/개별 PT 원본 전체·새 개인정보·내보내기/추가 연간 통계/별도 보고서 확정·실제 지급/청구/송금 기능을 이번 선택으로 포함하지 않는다. BR-009·MB-006/010의 복합 OPEN 및 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED를 유지한다. 구체 모듈/API/공개 계약/UoW/잠금 PROPOSED·직접 DB 읽기 예외 0건과 K3/X1 첫 IAM 흐름/별도 구현 지시 경계를 유지한다. V-129는 미구성·미실행 계획이다. 코드·migration·의존성/lockfile·제품/DB/브라우저 검사 변경/수행은 없다.


<a id="review-20261013-aa-batch"></a>
## 2026-10-13 일괄 승인 — AA1–AA2

사용자 답변: **“전부 1번. 질문 좀 모아서해...너 무오래걸리잖아..”**. AA1/AA2 모두 1번이다. 이후 실제로 남은 운영 판단은 한 목록으로 묶고, 이미 승인한 정책/유사 원칙과 설계자가 정할 기술 세부를 반복 질문하지 않는다.

| 항목 | 선택 | 승인된 내용 | 유지할 경계 | 추적 |
| --- | --- | --- | --- | --- |
| AA1 | 1 | 최초 일반 기본급 시작 월보다 이른 달에 유효 PT/추가실적이 있어 정산해야 하면 관리자가 사유를 남겨 해당 월 기본급을 명시적으로 직접 지정한다 | 최초 시작 월 이후 일반 설정은 유지. 기존 명시0원 허용/미입력 자동0 금지·현재 Master Org/Trainer 현재 Home Branch Admin·월 정정/확정 조건·원본/이전본 보존 유지 | BR-PAY-014; PR-010/027/030; BR-012; V-130 |
| AA2 | 1 | 일반 기본급의 미래 적용 시작 월은 지원하는 유효 연월 범위 안에서 별도의 업무상 기간 상한 없이 선택할 수 있다 | 시작 월 한 번 지정/다음 변경까지 지속. 적용 종료 월/유지할 미래 월 목록 요구 없음. 미래 변경 미리 등록은 선택적. 월별 수동 지정/확정본 보존 유지 | BR-PAY-014; PR-007/010; BR-012; V-131 |

AA1 범위: 예를 들어 일반 기본급 최초 시작이 11월인데 실제 10월 수업/실적이 있으면, 권한 있는 관리자가 10월 기본급만 직접 지정한다. 11월 이후 일반 설정·다른 월을 앞당기거나 덮어쓰지 않는다. 명시적 0원은 기존 정책대로 허용하되 사유가 필수이고 미입력은 자동 0원으로 계산하지 않는다. 처리 시점 Master Organization/Trainer 현재 Home Branch Admin 인가·본인 독립 관리 Scope/감사와 종료 월만 확정·지원 금액/영향 정정 미완료 차단·필요한 해제/정정/같은 월 재확정·이전본 보존을 유지한다. 수업/실적의 과거 사실·Pass 적격/정산 대상 자격을 확인할 수 없는 월을 임의 허용하거나 Rate/Fixed·PT/Pass 소비/과거 지급을 변경하는 선택은 아니다.

AA2 범위: 다음 달/그 이후 미래 월을 미리 시작 월로 지정할 수 있다. 매월 금액을 재입력하거나 종료 월·미래 월 목록을 지정하지 않으며 새 값은 해당 시작 월부터 다음 변경까지 계속 적용한다. 기술상 유효하지 않거나 표현할 수 없는 연월을 허용하는 뜻은 아니다. 기존 현재 관리자 Scope·명시 입력/감사·수동 지정 없는 미확정 월 반영/수동 지정 월 유지·과거 확정본 자동 변경 금지를 유지한다. 같은 시작 월/예약 변경의 버전·수정 순서/동시 저장·최소 입력/저장 계약은 후속 기술 설계다.

상태/검증: BR-012의 최초 시작 월 이전 처리와 미래 시작 월 범위만 해결했다. 다른 월 경계/금액 상한·월 대상/역사 사실/최소 계약·저장/UoW/경합은 남아 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED를 유지한다. 구체 모듈/API/공개 계약/UoW/잠금 PROPOSED·직접 DB 읽기 예외 0건과 K3/X1 첫 IAM 범위/별도 구현 지시를 유지한다. V-130/131은 미구성·미실행 계획이다. 코드·migration·의존성/lockfile·제품/DB/브라우저 검사 변경/수행은 없다.


<a id="review-20261013-ab-batch"></a>
## 2026-10-13 일괄 승인 — AB1–AB6

사용자 답변: **“전부 1번. 이어서 진행하자.”**. AB1–AB6 모두 1번이며 아래 정책 승인과 구체 기술계약/코드 구현 지시는 구별한다.

| 항목 | 선택 | 승인된 내용 | 유지할 경계 | 추적 |
| --- | --- | --- | --- | --- |
| AB1 | 1 | 대상 월 적용 일반 기본급 설정/월별 지정·유효 PT/보상대기 지원 PT·유효 추가실적 등 정산 구성 사실이 있는 Trainer를 월 정산 대상으로 자동 선정 | 명시0 설정도 존재로 판단·미생성 정산 행만으로 누락 금지. 자동확정/임의0 생성 아님. 현재 Master Org/Trainer 현재 Home 관리자 Scope·기존 이력/미완료 유지 | BR-PAY-026; PR-010/030; BR-009; MB-006/010; V-132 |
| AB2 | 1 | 대상 월 전체 Trainer 비활성·확인된 적용 기본급0·유효 PT/보상대기 PT/추가실적 없음·정정 대기 없음이면 새 월 정산 확정 의무 대상에서 제외 | 비활성화만으로 기본급 자동0 금지. 월중 활성/미확인 사실/기존 미완료는 예외 불가. 기존 정산/확정/정정 이력 삭제·자동 해제·자동 확정 없음 | BR-PAY-026; PR-010; BR-009; MB-006/010; V-133 |
| AB3 | 1 | 활성 계정의 후속 비밀번호 재설정 링크 유효시간30분 | 최초 설정과 reset 목적/상태 구별·기존 Master 전용/확정즉시 옛 암호·전 인증 무효/마지막 Master 보호·본인확인 전달 유지. 만료로 옛 인증 복원 없음 | PR-021/026; NFR-001; ARCH-002/F01; V-134 |
| AB4 | 1 | 실운영 Master/Branch Admin은 비밀번호 뒤 Passkey로 추가 검증. 기기 지문/얼굴/PIN 등 사용자 검증 필수 | 서버 사용자 검증 확인 필요·등록/분실/복구/호환성 설계/검증 후속. TOTP/약한 자동 fallback·passwordless 전환/특정SDK 채택 아님. S1 개발 우선/K3 범위 유지 | PR-001/021/026; NFR-001/008; ARCH-002/004/O03; V-135 |
| AB5 | 1 | 모든 Master가 로그인 불가한 비상 복구는 조직 업무책임자 확인/승인 후 별도의 배포·복구 운영담당자가 실행 | 제품 Operator와 별개·확인/실행 분리. 정상 계정/보상 업무에2인 승인 추가 아님. Bootstrap/DB 초기화/직접SQL 우회 금지·구체 절차/자격/감사/철회/실패 검증 후속 | PR-021/026/028; NFR-001/004; ARCH-002/OPS-001/F03; V-136 |
| AB6 | 1 | v1 Chrome/Edge/Safari의 최신2개 안정 주버전 지원 | Desktop/Tablet/Smartphone 반응형/Trainer 현장폰 흐름 유지. 구체 OS/기기·지원 갱신/실행 검증 후속. Firefox 지원 추가/브라우저 검증 완료 아님 | NFR-008; PR-001/029; ARCH-004/PD-021; V-137 |

정산 대상/예외: 적용 기본급이 명시적으로0이어도 설정은 존재한다. 실제 대상 월의 구성 사실과 기존 정산/정정 이력·미완료 영향을 대조하며 현재 활성 Trainer 목록이나 이미 생성된 정산 행만으로 대상을 한정하지 않는다. AB2는 그 월 전체 비활성·명시 기본급0·무활동·미완료 없음이 확인되는 새 확정 의무의 예외다. 현재 비활성이라는 이유로 월중 활동/지급 구성·미확인 설정/역사 사실·지원 금액 미입력·정정 대기를 제외하지 않는다. 기존 확정본/미완료 작업을 삭제·자동 해제/완료하지 않고 정상 이력 공개와 Y1/Y2 비용 보고 포함/미완료 표시를 유지한다. Trainer 자체 상태는 계정 차단/역할 회수/Branch 비활성과 구별하고 비활성만으로 일반 기본급을0으로 바꾸지 않는다. 자동 선정은 자동 확정/월별 생성 job 채택이 아니다.

후속 인증/복구: reset30분은 S2/해당 기능에 적용하며 기존 C4/A4/E2/마지막 Master 보호를 바꾸지 않는다. Passkey는 비밀번호에 더하는 운영 관리자 인증 수단이며 WebAuthn 사용자 검증 결과를 서버에서 확인해야 한다. 서버는 생체 원본/Passkey 개인키를 수집·저장하지 않는다. 운영 비상 복구의 업무책임자와 시스템 운영담당자는 별도 확인/실행 주체이며 실제 신원/승인 증거·대상/자격·보안 상태 철회/감사·실패/분실 절차는 별도 설계/검증 후 제공한다. S1에서 Master 분실 시 중단하고 실제 운영 전 MFA/복구를 완료하는 경계는 유지한다. 이 정책이 S1에 reset/Passkey/비상CLI를 선행 구현하는 지시는 아니다.

브라우저/운영: 최신2개 안정 주버전은 지원 품질 목표이며 현재 지원 검증 결과가 아니다. 실제 OS/기기/버전 매트릭스·주요 업무/터치/화면/Passkey 검증과 지원 갱신 절차는 후속이다. 지원 범위 선택이 User-Agent 기반 인가/접속 차단 정책은 아니다. 보존기간/백업 복구 목표·실제 담당자 신원/운영 규모는 임의 확정하지 않는다.

상태/검증: BR-009·MB-006/010 대상 기준과 ARCH-002/004 일부 운영 선택만 해결했다. 대상/역사 사실·미완료/버전·실제 계정 절차/본인확인·보존/운영/부하·최소 계약/저장/UoW/경합은 남아22 OPEN / 8 CLOSED, PD1 OPEN /26 CLOSED를 유지한다. 구체 모듈/API/공개 계약/UoW/잠금 PROPOSED·직접 DB 읽기 예외0건 및 K3/X1 첫 IAM/별도 구현 지시 경계를 유지한다. V-132–137은 미구성·미실행 계획이다. 코드·migration·의존성/lockfile·제품/DB/브라우저 검사 변경/수행은 없다.

<a id="review-20261016-mfa-m-batch"></a>
## 2026-10-16 MFA 후속 검토 — M1/M2 승인

사용자 답변: M1의 최초 **“패스키 는이중보안때문에???”**는 설명 요청이었다. 로그인은 비밀번호 뒤 등록된 Passkey 중 하나로 추가 인증하며 복수 등록은 기기 분실에 대비한다는 설명 후, **“여러 Passkey 허용 (추천)”**으로 확정했다. M2는 **“정상 Master가 재등록 처리 (추천)”**로 승인됐다. 이전 Pass 상태 검토의 M1/M2와 구분하여 이 날짜/앵커로 추적한다.

| 항목 | 상태 | 확정한 내용 / 남은 결정 | 경계 / 추적 |
| --- | --- | --- | --- |
| MFA M1 | 승인 | 관리자 계정에 Passkey를 여러 개 등록하고 로그인 시 그중 하나를 사용 | 복수 기기의 동시 인증을 요구하지 않음. AB4 비밀번호 뒤 Passkey 사용자 검증 유지. 구체 개수 상한/등록·삭제 계약은 후속. PR-001/021/026; NFR-001/008; ARCH-002/O03; V-135 |
| MFA M2 | 승인 | 다른 정상 Master가 로그인 가능한 경우, 그 Master가 같은 Organization 관리자의 본인 확인 후 기존 Passkey와 모든 AuthSession을 폐기하고 일회용 링크를 전달하여 대상자가 Passkey를 재등록 | Master/Branch Admin 대상. Branch Admin에게 복구 권한 위임 없음·타 Organization 금지. PR-001/021/026; NFR-001; ARCH-002/O03; V-135 |

정상 Master는 현재 유효한 로그인·Master 권한과 기존 운영 MFA 요건을 충족하는 다른 관리자다. 이름/과거 역할·요청 role만으로 권한을 인정하지 않는다. M2는 비밀번호 reset·계정 차단 해제·회수 역할/Scope 복원이나 비밀번호만으로 운영 업무에 접근하는 우회를 승인하지 않는다. 재등록 완료 전 기존 AB4 MFA 요건을 충족하지 못한 업무 접근을 허용하지 않으며 마지막 Master 보호를 유지한다. 모든 Master가 로그인할 수 없으면 AB5의 업무책임자 확인/승인·별도 시스템 운영담당자 실행 경로를 유지하고 Bootstrap 재실행·DB 초기화·직접 SQL을 복구 수단으로 삼지 않는다.

남은 설계/검증: Passkey 추가 등록/삭제·마지막 인증수단 보호의 계약, 본인 확인·전달 운영 절차, 재등록 링크의 목적/수명/소비·중복 발급/실패 처리, 철회·등록·감사의 원자성/경합, 실제 WebAuthn·브라우저 검증을 별도로 구체화한다. 비밀번호 설정/reset 링크의 30분을 재등록 링크에 자동 전용하지 않는다. ARCH-002/004·OPS/보존 게이트와 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED를 유지한다. 이번 반영은 정책 문서 변경이며 MFA 코드·migration·의존성 변경이나 제품/DB/브라우저 검사 실행·운영 허용이 아니다.

<a id="review-20261018-mfa-m3-m6"></a>
## 2026-10-18 MFA 후속 검토 — M3–M6 승인

사용자 답변: **“전부1번”**. 직전 M3–M6의 추천안을 모두 선택했다. [2026-10-16 M1/M2](#review-20261016-mfa-m-batch), AB4 비밀번호 뒤 사용자 검증 Passkey, AB5 전체 Master 로그인 불가의 별도 비상 복구를 유지한다.

| 항목 | 선택 | 승인한 정책 | 경계 / 추적 |
| --- | --- | --- | --- |
| MFA M3 | 1 | 첫 Passkey는 최초 Master의 설치 절차 또는 새 관리자의 본인 전용 계정 설정 절차에서 등록한다. 이후 추가 등록은 정상적으로 2단계 로그인한 본인이 수행 | 최초 설치 외 매번 Master 승인하는 대안은 미채택. 첫 등록 전 업무 접근 금지·비밀번호만으로 임의 첫 등록 허가 없음. C1 추가 관리 비밀번호 재확인 미채택 유지. PR-001/021/026; NFR-001; ARCH-002/O03; V-135 |
| MFA M4 | 1 | 본인 Passkey 삭제는 다른 유효한 Passkey가 남을 때만 허용하고 마지막 하나는 삭제할 수 없다 | 분실/전체 재등록은 M2, 모든 Master 로그인 불가는 AB5. 타인 credential 직접 관리 권한으로 확대하지 않음. PR-021/026; NFR-001; ARCH-002/O03; V-135 |
| MFA M5 | 1 | Passkey 분실 재등록 일회용 링크 유효시간은 30분 | 비밀번호 최초 설정/reset과 목적·대상·상태를 혼용하지 않음. M2의 정상 Master 본인 확인/전달·기존 Passkey/모든 로그인 철회 유지. 만료/실패가 옛 인증을 복원하지 않음. PR-021/026; NFR-001; ARCH-002/O03; V-135 |
| MFA M6 | 1 | 추가 Master 계정의 신규 발급은 같은 Organization의 현재 정상 Master만 수행 | 복수 Master 허용(A9)의 발급 Actor를 확정. Branch Admin 위임·타 조직 발급·기존 계정 승격/강등은 포함하지 않음. 최초 설치 E1·마지막 사용 가능 Master 보호는 유지. PR-001/021/028; NFR-001/004; ARCH-002/F02 |

등록 신뢰와 권한: M3은 설치/본인 계정 설정의 신뢰 경로와 정상 MFA 로그인한 본인의 추가 등록을 허용한다. 다른 사람이 대신 본인의 Passkey를 등록하거나 기존 password-only 로그인을 자동으로 MFA 완료/첫 등록 권한으로 승격하는 선택이 아니다. 생체 원본/Passkey 개인키는 서버에 수집·저장하지 않는다. 관리자/Trainer 겸임의 독립 업무 권한을 유지하되 약한 인증으로 관리 권한을 우회할 수 없다.

이번 결정으로 재질문하지 않을 항목: M1/M2·M3–M6, AB4/AB5, C1, 기존 A4/AB3의 비밀번호 링크30분과 A9 마지막 Master 보호. 등록/로그인 전용 컨텍스트·WebAuthn 검증·AuthSession 검증 수준/철회·저장/공개 계약/UoW/잠금·감사/경합·실제 CLI/브라우저 검증은 기술 설계와 검증으로 구체화한다. M4 삭제·M2 복구·M6 추가 Master 발급을 첫 MFA 등록/로그인 증분에 모두 포함할 의무는 없고 후속 인수 범위를 구분한다.

상태/검증: ARCH-002/004·OPS/보존 및 기타 남은 게이트, 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED를 유지한다. 사용자 지속 지시에 따라 승인된 범위의 구현·독립 검증·설계자 검토·전담 커밋/푸시를 진행하되 정책 승인 자체를 코드/검사 통과·운영 허용으로 보고하지 않는다. V-135와 추가 Master/비상 복구의 실제 검증은 각 증분에서 별도로 증명한다.

<a id="review-20261018-mfa-m7-m8"></a>
## 2026-10-18 MFA 후속 검토 — M7/M8 승인

사용자 답변: M7 **“삭제 시 모든 로그인 종료 (추천)”**, M8 **“본인 관리자 재설정 금지 (추천)”**. [M3–M6](#review-20261018-mfa-m3-m6)와 앞선 M1/M2·AB4/AB5를 유지한다.

| 항목 | 승인한 정책 | 경계 / 추적 |
| --- | --- | --- |
| MFA M7 | 본인 Passkey 하나의 삭제가 성공하면 현재 기기를 포함한 모든 기존 AuthSession을 종료하고 남은 Passkey로 다시 2단계 로그인한다 | M4에 따라 마지막 하나 삭제 금지. 삭제한 key만 신규 로그인에서 차단하고 옛 로그인을 유지하는 대안은 미채택. 실패 시 기존 key/로그인 보존·철회/감사/경합은 기술 계약/실제 검증 대상. PR-021/026; NFR-001/004; ARCH-002/O03 |
| MFA M8 | Master도 본인 계정에는 관리자 비밀번호 재설정을 수행할 수 없다 | 현재 암호를 알면 C3 본인 변경, 잊었다면 같은 조직의 다른 정상 Master에게 관리자 재설정 요청. 마지막 Master 분실은 AB5 별도 복구. C4 reset 효과·AB3 링크30분·마지막 Master 보호/회수 역할·MFA 비복원 유지. PR-021/026/028; NFR-001; ARCH-002/F01/F02 |

M8은 현재 비밀번호를 확인하는 본인 변경과 관리자 reset을 구분한다. 다른 정상 Master가 존재하더라도 본인 관리자 reset을 허용하지 않으며 C3의 현재 비밀번호 확인을 우회하는 별도 본인 경로를 만들지 않는다. 이미 로그인한 Master의 정상 관리 권한 전체에 추가 비밀번호 확인이나 2인 승인을 도입하는 선택은 아니다.

검증/상태: MFA-A 최초/복수 등록·2단계 로그인 증분과 분리해 삭제/관리자 reset 구현 시 검증한다. 정책 승인만으로 해당 기능 또는 운영 복구를 인수하지 않는다. 22 OPEN / 8 CLOSED, PD 1 OPEN / 26 CLOSED와 구체 계약/운영 게이트를 유지한다.

<a id="review-20261020-ab5-r1-r3"></a>
## 2026-10-20 비상 복구 후속 — AB5 R1–R3 승인

사용자 답변: **“전부 1”**. 직전 설계자 보고의 AB5 세 항목을 모두1번으로 확정했다. 기존 AB5 업무책임자 확인/승인·별도 배포/복구 운영담당자 실행, M2/reset 정상 경로와 AB4 비밀번호 뒤 사용자 검증 Passkey를 유지한다.

| 항목 | 선택 | 승인한 내용 | 경계 / 추적 |
| --- | --- | --- | --- |
| AB5 R1 | 1 | 기존 ACTIVE Master 한 명의 인증요인 복구 | 현재 Master 역할/Organization/account ID·Scope 유지. DISABLED 차단 해제·신규 계정·회수 역할 복원 제외. PR-021/026/028; ARCH-002/F03; V-136 |
| AB5 R2 | 1 | 대상 계정의 모든 기존 로그인과 대기 인증 권한만 철회 | 다른 계정의 로그인/대기 인증·저장된 비밀번호/Passkey 유지. 대상도 승인된 분실 요인만 재설정하며 다른 요인·C2·업무 이력 보존. 조직 전체 침해 대응으로 확대하지 않음. PR-021/026; NFR-001/004; ARCH-002/F03; V-136 |
| AB5 R3 | 1 | 별도 운영담당자가 보호된 수동 절차로 업무책임자 승인 원본/참조를 확인하고 확인·실행 이력 기록 | 실행자 단독 자기승인·임의 approved=true는 승인 아님. 승인자 실제 신원/권한·승인 진위·사람의 역할 분리는 운영 확인/접근 통제·기록 대조에 의존하며 시스템의 암호적 자동 증명을 주장하지 않음. 별도 전자서명 승인 서비스 도입 제외. PR-026/028; NFR-001/004; ARCH-002/OPS-001/F03; V-136 |

적용 조건: 모든 Master가 정상 경로를 이용할 수 없는 상황을 업무책임자가 확인한다. 서버의 세션 개수나 저장된 Passkey 존재만으로 사람의 실제 접근 가능/불가를 자동 판정하지 않는다. 정상 다른 Master가 이용 가능하면 기존 M2/reset을 사용한다. 제품 Operator 역할과 운영 실행 권한은 별개이며 일반 웹 요청이 운영 권한을 만들지 않는다.

대상은 제한된 단회 절차에서 승인된 비밀번호/Passkey 요인을 직접 준비한 뒤 별도의 정상 비밀번호+UV 로그인으로 복귀한다. 준비/조회는 인증을 폐기하지 않는다. 부분 준비·만료·전달 실패·응답 유실로 옛 인증을 되살리거나 자동 로그인하지 않는다. 현재 pending/readiness 때문에 승인 외 요인이 더 필요하면 필요한 범위를 다시 확인하며 복구 범위를 자동 확대하지 않는다. Bootstrap 재사용·설치 표시 제거·DB 초기화·직접 SQL·새 Master 자동 생성은 복구 경로가 아니다.

검증/상태: 승인 범위의 구현→독립 테스트→설계자 검토→전담 커밋·푸시 지속 지시를 적용한다. 구체 운영 권한·보호 입력/전달·사건/승인 결합·단회 소비·현재 권한/epoch 확인·UoW/잠금·필수 감사·실제 COMMIT ACK 불명확/실패 처리는 기술 계약과 실제 검사로 구체화한다. 실제 운영 담당자/확인 경로·보존/열람/삭제·배포·실물/전체 지원 브라우저 인수는 남아 있으며22 OPEN /8 CLOSED, PD1 OPEN /26 CLOSED·ADR/전체 모듈의 상태를 유지한다.
