# Product Specification — Architecture Input Baseline

2026-10-16 MFA 후속 부분 승인: [M1/M2](product-decisions.md#review-20261016-mfa-m-batch)로 관리자 계정의 복수 Passkey 등록/로그인 시 그중 하나 사용과, 같은 Organization의 다른 정상 Master에 의한 본인 확인·기존 Passkey/모든 로그인 폐기·일회용 링크 재등록을 확정했다. AB4/AB5와 22 OPEN/8 CLOSED를 유지하며 등록/삭제·복구 계약/운영 확인·실제 검증은 후속이다.

현재 후속 정책: [2026-10-13 AB 승인](product-decisions.md#review-20261013-ab-batch)의 AB1–AB6 모두 1번이다. 월 정산 대상은 적용 기본급/월별 지정·유효 PT/보상대기 지원 PT/추가실적 등으로 자동 선정하며, 한 달 전체 Trainer 비활성·명시 기본급0·무활동·정정 대기 없는 경우 새 정산 확정 의무에서 제외한다. 기존 이력/미완료와 비활성만으로 기본급을 자동0으로 바꾸지 않음은 유지한다. 후속 reset 링크30분·운영 관리자 비밀번호 뒤 Passkey·업무책임자 승인/별도 운영담당자 비상 복구·Chrome/Edge/Safari 최신2개 안정 주버전을 선택했다. K3/X1 첫 IAM/별도 구현 지시·구체 계약 PROPOSED와 22 OPEN/8 CLOSED는 유지한다.

2026-10-12 일괄 승인 반영: B1–B7/A1–A10의 선택은 [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch)을 따른다. A4/A5만 2번으로 최초 설정 링크 30분 및 전 역할 공통 idle 30분/absolute 8시간이다. 다른 항목은 1번이며 v1 PG AuthSession+opaque Cookie 방식은 ADR-0004 ACCEPTED, JWT는 후속 버전의 재검토 후보다. 새 Pass 활성 담당 필수/상품 횟수 최초 부여·인가 관리자 발급 횟수 초과 추가, Trainer 재활성화/비활성 전용 로그인 제한, 데이터 있는 Branch 비활성화/신규 업무 차단·원본 보존, 공통 한국 시간도 확정됐다. 모듈·저장/계약/UoW·경합의 기술 제안/남은 Product OPEN은 유지하며 코드/migration·의존성·실행 검사는 변경/수행하지 않았다. 앞선 PROPOSED/미결정 기록은 당시 이력이고 이번 승인 범위에 한해 대체한다.

2026-10-12 사용자 확정(비활성화 전 누락 수업 대행 등록의 Branch Admin 기준 질문 1번): Master Admin은 자신의 Organization 전체, Branch Admin은 처리 시점 현재 관리 Branch가 실제 수업의 Performed Branch인 경우에만 대행 등록할 수 있다. Trainer 현재 Home Branch가 다른 지점이어도 실제 수업이 자신의 관리 지점에서 진행됐다면 허용한다. Trainer Home Branch·Member Home Branch·Pass Issued Branch 또는 과거 관리자 Scope만으로 대행 권한을 얻지 않는다(BR-OPS-015). 현재 비활성/담당·Pass/보상/진행 월 정산과 별도 민감정보 접근 제한은 유지한다. 과거 사실 확인/선택 계약·구체 저장/경합은 후속이며 ADR-0004/Architecture PROPOSED·IAM-001 S1 범위와 OPEN 상태는 유지한다.

2026-10-12 비활성 Trainer 누락 수업 관리자 대행 경로 승인: 비활성화 전 실제 수업은 비활성 상태를 유지한 채 관리자가 실제 수행자/수업일로 등록할 수 있다. Pass/담당 재처리 없이 기존 잔여·생성 시점 수행 Trainer 지급 설정/실제 진행 월 정산 조건을 적용하며 입력 관리자는 별도 추적한다. Branch Admin 기준 지점 등 상세 인가/사실 판정·계약/경합은 후속이다. OPEN 23/7·ADR-0004/Architecture PROPOSED·S1 범위 유지, 실제 업무 구현/검증 미완료(BR-OPS-015; V-69 예정).

2026-10-12 새 담당 Trainer 활성 조건 확정: 허용된 최초 지정/담당 교체에서는 실제 활성 Trainer만 지정하고 비활성 Trainer 사전 배정은 금지한다. Backend 현재 상태/같은 Organization·기존 Actor/행위 Scope를 확인하며 같은 Organization의 타 지점 활성 Trainer 허용은 유지한다. 지정 후 비활성화된 기존 담당 정보 유지/접근 차단과 구별한다. 최초 담당 필수 여부/나머지 상태 조합·과거 수업 예외/재활성화·계약/경합은 후속이며 OPEN 23/7·ADR-0004/Architecture PROPOSED·S1 유지. 업무 구현/검증 미완료(BR-OPS-008/014; V-68 예정).

2026-10-12 잔여 Pass 보유 Trainer 비활성화 확정: 잔여가 남은 담당 Pass가 있어도 비활성화 가능하며 Assigned Trainer 정보를 유지/자동 해제·교체와 사전 일괄 교체를 요구하지 않는다. 필요 시 기존 Member 현재 Home Branch 기반 관리자 권한으로 별도 교체한다. 담당 유지로 비활성 Trainer의 접근을 허용하지 않으며 잔여/발급 조건·과거 PT/지급/정산·독립 관리자 Scope를 보존한다. 새 담당 활성 조건/개별 지원·재활성화 등은 후속이다. OPEN 23/7·ADR-0004/Architecture PROPOSED·S1 범위 유지, 업무 구현/검증 미완료(BR-OPS-008/014; V-67 예정).

2026-10-12 Trainer 비활성화 권한 확정: Master Organization 전체/Branch Admin 처리 시점 대상 Trainer 현재 Home Branch 범위에서 허용한다. 지원 수업/과거 소속·계정 발급 사실은 근거가 아니며 Backend 현재 권한/실제 대상 사실을 검증한다. 겸임자의 독립 관리자 권한 유지·계정 전체 차단 분리는 그대로다. 재활성화/Trainer 단독 로그인·관계 처리·기술 계약은 후속이며 Product OPEN 23 OPEN / 7 CLOSED·ADR-0004/Architecture PROPOSED·IAM-001 S1 범위를 유지한다. 문서 반영이며 업무 구현/검증 미완료다(BR-OPS-014; V-66 예정).

2026-10-12 Trainer 비활성화의 겸임 처리 확정: Trainer 권한만 중단하고 독립 관리자 역할/Scope 및 관리 업무는 유지하며 계정 전체 차단은 별도다. 후속 인가에 실제 Trainer 상태를 적용하고 과거 PT/지급/정산·다른 역할을 자동 변경하지 않는다. 처리 Actor/재활성화·Trainer 단독 계정 로그인·비활성 상태의 예외와 기술 계약은 후속이다. Product OPEN 23 OPEN / 7 CLOSED, ADR-0004/Architecture PROPOSED 및 IAM-001 S1 범위 유지. 문서 반영이며 업무 구현/검증 미완료다(BR-OPS-014; V-65 예정).

2026-10-12 Trainer Home Branch 변경 권한 확정: Master Admin만 자기 Organization 범위에서 변경하며 출발/도착 Branch Admin·계정 발급자·Operator/Trainer 단독은 불가하다. 기존 사용자 일관성 지시에 따라 일반 저장 후 새 현재 소속 반영·실패 시 이전 소속 보존·중요 소속/권한 변경 이력·감사를 적용한다. 현재 Home Branch 기반 보상/정산 관리·Trainer 발급 인가는 새 소속을 사용하고 독립 관리자/Operator Scope·Trainer 연결/담당·지원 관계와 과거 수업 당시 소속/지급·정산/설정값은 보존한다. 대상 상태·과거 소속 이력 오류 정정/소급/확인 불가 및 실제 계약/저장/UoW·동시성은 후속이다. 이전 미정 중 일반 이동 Actor만 직접 승인됐으며 Product OPEN 23 OPEN / 7 CLOSED, ADR-0004/Architecture PROPOSED·IAM-001 S1 범위는 유지한다. 설계 문서 변경/업무 구현·검증 미완료다(BR-OPS-013, PD-004, PR-005/029/030, NFR-001/004, MB-001/004/005/010, ARCH-001; V-64 예정).

2026-10-12 신규 Trainer 로그인 계정 발급 권한 확정: Master Admin은 자기 Organization 전체, Branch Admin은 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 발급할 수 있다. 타 지점 지원 수업·담당 관계·과거 소속/발급 사실은 근거가 아니며 현재 Caller/Organization·실제 Trainer/현재 소속을 Backend에서 검증한다. 기존 일회용 최초 비밀번호 설정 링크/대상자 직접 설정·계정 권한 감사/실패 일관성 원칙을 재사용한다. 기존 계정 역할 추가/Trainer 재연결·관리자 승격·Trainer 이동/수명 위임과 상세 계약/저장/UoW·동시성은 후속이다. 아래 당시 Trainer 발급 위임 미정 부분만 이번 Actor/Scope 승인으로 해결했다. Product OPEN 23 OPEN / 7 CLOSED 및 ADR-0004/Architecture PROPOSED·IAM-001 S1 범위 유지. 설계 문서 변경/실제 Trainer 인증 구현·검증 미완료다(BR-OPS-012, PD-019, PR-021/029/030, NFR-001/004, MB-004, ARCH-001/002; V-63 예정).

2026-10-12 기존 Operator 업무 지점 변경 권한 확정: Master Admin만 자기 Organization 범위에서 변경할 수 있다. 출발/도착 Branch Admin·최초 발급자·Operator/Trainer 단독은 불가하고 Branch Admin의 자기 지점 신규 발급/최초 지정은 유지한다. 기존 사용자 일관성 지시에 따라 저장 후 새 단일 Scope 반영·실패 시 이전 Scope 보존·중요 권한 변경 감사를 적용한다. 독립 겸임 역할/Trainer Home Branch·기존 Member/Pass/과거 PT·지급/정산은 보존한다. 이전 미정 중 변경 Actor만 직접 승인됐고 대상 상태/절차·계정 수명/다른 역할 권한·계약/저장/UoW·동시성은 후속이다. Product OPEN 23 OPEN / 7 CLOSED 및 ADR-0004/Architecture PROPOSED·IAM-001 S1 범위 유지. 설계 문서 변경/업무 구현·검증 미완료다(BR-OPS-011, PD-019, PR-021/030, NFR-001/004, MB-004, ARCH-001; V-62 예정).

2026-10-12 Operator 계정 발급/최초 지점 지정 권한 확정: Master Admin은 자기 Organization 전체, Branch Admin은 자기 단일 관리 Branch의 새 Operator 계정을 발급하고 그 한 지점을 최초 업무 Branch로 지정할 수 있다. 기존 최초 비밀번호 설정 링크·계정/권한 감사·실패 시 부분 확정 방지 원칙을 재사용한다. 다른 역할 발급/기존 계정 역할 변경·Operator 지점 이동/계정 수명 위임은 이번에 승인하지 않았다. 아래 당시 미결정 중 신규 Operator 발급/최초 Scope 지정 Actor만 해결했고 발급 절차·기술 계약/저장/UoW/동시성은 후속이다. Product OPEN 23 OPEN / 7 CLOSED 및 ADR-0004/Architecture PROPOSED·IAM-001 S1 범위를 유지한다. 설계 문서 변경이며 업무 구현·검증 미완료다(BR-OPS-011, PD-019, PR-021, NFR-001/004, MB-004, ARCH-001/002; V-61 예정).

2026-10-12 Operator 업무 지점 수 확정: v1 Operator 역할의 허용 업무 Branch는 한 시점에 하나만 지정하며 동일 계정의 복수 Branch 동시 Scope는 허용하지 않는다. 하나의 Branch에 여러 Operator는 가능하고 기존에 허용된 겸임의 독립 Scope·Trainer Home Branch는 별개다. 새 Pass는 지정된 단일 지점에서 발급하되 그 발급용 Member 검색은 기존 같은 Organization 전체 지점 이름·전화번호 일부 검색/이름·전체 전화번호·현재 Member Home Branch 공개를 유지한다. 직접 ID/클라이언트 지점 선택·중복 Operator 부여로 다른 지점 업무를 허용하지 않는다. 계정/Scope 부여 주체·절차와 지정 지점 변경 Actor/적용 시점·나머지 업무/저장·계약·동시성은 후속이다. 이전 미정 중 Operator 동시 지점 수만 해결했다. Product OPEN 23 OPEN / 7 CLOSED 및 ADR/Architecture 상태 유지. 설계 문서 변경/업무 구현·검증 미완료다(BR-OPS-011, PD-001/007, PR-001/003/030, NFR-001, ARCH-001/002, MB-004; V-60 예정).

2026-10-12 발급용 검색 결과 표시 정보 확정: 같은 Organization 전체 지점 Member의 발급용 이름·전화번호 일부 검색 결과에 이름·전체 전화번호·현재 Member Home Branch를 표시한다. 타 지점 회원도 동일하게 공개하고 부분 마스킹만으로 제한하지 않는다. 현재 발급 Caller/실제 Issued Branch Scope·Organization을 검증하며 같은 번호/동명이인도 별도 Member로 구분/선택한다. 공개 소속은 실제 Member 현재 소속이며 새 Pass 발급 지점으로 대체하지 않는다. 읽기 공개만 확정하고 회원/번호 수정·일괄 내보내기·일반 상세/다른 Pass/PT/보상 권한은 별도다. 추가 공개 정보·최소 선택 응답/계약·Operator Scope 부여/허용 지점 수·나머지 검색/대상/발급 조건·저장/UoW·동시성은 후속이다. 이전 미결정 기록 중 이 세 항목/전화번호 공개 형태만 해결했다. Product OPEN 23 OPEN / 7 CLOSED 및 ADR/Architecture 상태 유지. 설계 문서 변경/업무 구현·검증 미완료다(BR-OPS-010, PD-004/007/022, PR-002/003/030, NFR-001/005, ARCH-001, MB-002/003/004; V-59 예정).

2026-10-12 발급용 타 지점 Member 검색 확정: Branch Admin·Operator는 허용된 실제 Issued Branch의 새 Pass 발급에서 같은 Organization 전체 지점 Member를 이름·전화번호 일부로 검색할 수 있다. 전화번호 전체 일치/Member Home Branch 일치를 요구하지 않는다. 매 검색/선택/발급에서 현재 역할·실제 발급 지점/Organization을 검증하며 같은 번호의 Member도 별도 식별/선택·소속과 기존 이력을 유지한다. 이 권한은 발급용 검색에 한정하고 일반 Member 상세/전체 무조건 목록·내보내기/다른 Pass/PT·보상 공개로 확대하지 않는다. 검색 결과 공개 필드/전화번호 공개 형태·최소 식별 응답·나머지 검색/대상 조건·Operator Scope 부여/허용 지점 수·계약/저장/UoW·동시성은 후속이다. 이전 기록에서 검색 범위/방식이 미정이던 부분만 이번 승인으로 해결했다. Product OPEN 23 OPEN / 7 CLOSED 및 ADR/Architecture 상태 유지. 설계 문서 변경/업무 구현·검증 미완료다(BR-OPS-010, PD-004/007/022, PR-002/003/030, NFR-001/005, ARCH-001, MB-002/003/004; V-59 예정).

2026-10-12 새 Pass 발급 Actor 확정: Master Organization 전체/Branch Admin 자신의 단일 관리 Branch/Operator 부여된 허용 발급 Branch Scope에서 허용한다. Trainer 단독은 불가하며 겸임자는 독립 발급 역할/Scope로 판단한다. 같은 Organization의 타 Home Branch Member도 대상이고 기존 소속 유지/실제 Issued Branch 기록 원칙을 적용한다. Operator의 발급 허용으로 상품 수정·기존 Pass 수동 관리·보상/정산 권한을 추가하지 않는다. 각 요청의 현재 Caller/실제 지점·Organization 사실을 Backend 검증하며 발급용 최소 회원 식별은 일반 타 지점 정보 공개와 분리한다. Operator Scope 부여/허용 지점 수·최소 Member 검색/공개 정보·활성/초기 조건·계약/저장/UoW·동시성은 후속이다. Product OPEN 23 OPEN / 7 CLOSED 및 ADR/Architecture 상태 유지. 설계 문서 변경/업무 구현·검증 미완료다(BR-OPS-010, PD-004/007, PR-003/030, ARCH-001, MB-002/003/004/005).

2026-10-12 Member 소속 밖 지점의 새 Pass 발급 허용 확정: 같은 Organization의 수원 소속 회원이 강남에서 새 이용권을 발급받을 수 있다. 기존 Member/Home Branch는 수원으로 유지하고 새 Pass Issued Branch는 강남으로 기록한다. 지점별 회원 복제/소속 자동 이동·기존 Pass/과거 PT/지급·정산 덮어쓰기 없음. 공통 상품/판매 중단·발급 조건 보존은 유지하며 새 Pass의 만료/해제·수동 횟수 조정은 Issued Branch, 담당 교체는 Member 현재 Home Branch 기준이다. 발급 Actor 세부 권한/허용 실제 발급 지점·활성/초기 조건과 타 지점 Member 최소 식별/조회·계약/저장/UoW·동시성은 후속이며 전체 회원 목록/민감 정보 접근을 자동 허용하지 않는다. Product OPEN 23 OPEN / 7 CLOSED 및 ADR/Architecture 상태 유지. 설계 문서 변경/업무 구현·검증 미완료다(BR-OPS-010, PD-004/007, PR-002/003/030, ARCH-001, MB-002/003/004/005, NFR-001/005).

2026-10-12 Pass 횟수 수동 조정 관리자 범위 확정: Master Organization 전체 또는 Branch Admin 처리 시점 관리 Branch=Pass Issued Branch로 인가한다. 수원 발급/강남 현재 소속 회원은 수원 관리자 또는 Master가 조정하며 Member 소속·담당/Performed Branch만으로 강남 관리자에게 권한이 생기지 않는다. 비관리자 Operator/Trainer는 불가·관리자 겸임은 관리자 Scope. 기존 사유/전후 잔여·증감량/Actor/Role·Branch Context·시점 이력/감사와 범위 내 직접 처리 원칙을 적용한다. PT 취소 자동 복원은 기존 취소 업무 권한/조건, 담당 교체는 Member 현재 Home Branch 기준을 유지한다. 수량/목적/상태·저장/계약/UoW·동시성은 후속이며 모든 조정값/상태를 허용한 것이 아니다. Product OPEN 23 OPEN / 7 CLOSED 및 ADR/Architecture 상태 유지. 설계 문서 변경/업무 구현·검증 미완료다(BR-OPS-009, PD-007/010, PR-003/030, BR-002, ARCH-001/003, NFR-001/004).

2026-10-12 잔여 0 Pass 담당 교체 허용 확정: 잔여를 모두 사용해 이용을 마친 Pass도 같은 Pass에서 A→B 교체 가능하며 잔여 0·발급 조건/Issued Branch·과거 수업/확정 지급·정산은 유지한다. 새 현재 담당은 기존 Member 기본 조회/허용 전화번호로 후속 응대를 이어간다. 선택 제외 필터는 기존 Member 전체 Pass 잔여 기준이며 담당 교체로 횟수 복원/추가·상태 재개/정상 차감 허용을 만들지 않는다. 기존 관리자 Scope/동일 Organization 대상·감사와 보상 설정 제한 유지. 아래 당시 미결정 중 잔여 소진 완료 Pass의 담당 교체만 추가 해결됐으며 수동 만료/취소 등 다른 사유의 상태·대상 Trainer 활성·과거 사실/기술 계약·경합은 후속이다. Product OPEN 23 OPEN / 7 CLOSED 및 ADR/Architecture 상태는 유지한다. 설계 문서 변경/업무 구현·검증 미완료다(BR-OPS-005/008, PD-007, PR-003/029/030, BR-001, ARCH-001, MB-001/003/005).

2026-10-12 담당 교체 전 수업의 이전 담당 직접 누락 등록 허용 확정: A가 실제 수업 후 B로 교체돼도 A는 당시 담당/본인 수행·현재 Caller/Trainer 연결/Organization와 기존 Pass/정산 조건을 검증하여 직접 등록한다. 현재 B라는 이유만의 관리자 대행/재배정은 요구하지 않으며 A의 현재 회원 목록/상세·전화번호 권한은 복원하지 않는다. 기존 미확정 월/Pass 선택·차감 및 실제 수업 당시 A Home Branch/Performed Branch의 보상 구분, 등록 시점 A 설정 적용과 지원 수업 수동 추가실적 원칙은 유지한다. 아래 당시 미결정 중 해당 누락 등록 허용만 추가 해결됐으며 과거 담당/수행 사실 확인 불가/정정·다른 관계의 인가/최소 식별·기술 계약/동시성은 후속이다. Product OPEN 23 OPEN / 7 CLOSED 및 ADR/Architecture 상태는 유지한다. 설계 문서 변경/업무 구현·검증 미완료다(BR-OPS-003/005/008, PD-008, PR-008/029/030, BR-008, ARCH-001, MB-001/003/005).

2026-10-12 기존 Pass 담당 교체 대상의 지점 조건 확정: 같은 Organization의 다른 지점 Trainer도 지정할 수 있다. 강남 회원의 담당을 수원 Trainer로 바꿀 수 있으며 Member/Trainer Home Branch·Pass Issued Branch·잔여/발급 조건·과거 지급 이력은 유지한다. 교체 권한은 Master Organization 전체/Branch Admin 처리 시점 Member 현재 Home Branch, 보상 설정 접근은 기존 대상 Trainer Home Branch 기준이다. 후속 회원 조회는 현재 담당/별도 지원·관리 관계, 일반/지원 보상 구분은 실제 수업 당시 실제 수행 Trainer Home Branch와 Performed Branch를 따른다. 아래 당시 미결정 중 대상 Trainer 지점 조건만 추가 해결됐으며 활성·Pass 상태·과거 사실/늦은 등록 및 최소 Trainer 선택 정보/계약·경합은 후속이다. Product OPEN 23 OPEN / 7 CLOSED와 ADR/Architecture 상태는 유지하며 설계 문서 변경/업무 구현·검증 미완료다(BR-OPS-008, PD-007, PR-003/029/030, ARCH-001, MB-001/003/005, BR-001).

2026-10-12 기존 Pass 담당 교체 권한 확정: Master Organization 전체 또는 Branch Admin 처리 시점 Member 현재 Home Branch 기준이다. 수원 발급/강남 현재 소속 회원은 강남 관리자 또는 Master가 교체하며 수원 발급 사실만으로는 불가하다. 비관리자 Operator/Trainer는 불가, 관리자 겸임은 관리자 Scope로 판단한다. 각 요청에서 현재 권한·Pass/Member 관계/현재 소속을 Backend 검증하고 범위 밖 직접 ID/위조 Scope는 거부한다. 수동 만료/해제는 기존 Issued Branch 기준을 유지한다. 기존 즉시 적용/이력·감사/잔여·과거 지급 보존과 보상 설정 제한은 유지한다. 아래 당시 미결정 중 교체 Actor/Branch Scope만 해결됐으며 대상 Trainer 지점/활성·Pass 상태·과거 사실/늦은 등록과 기술 계약/경합은 후속이다. Product OPEN 23 OPEN / 7 CLOSED 및 ADR/Architecture 상태는 유지한다. 설계 문서 변경이며 업무 구현·검증 결과가 아니다(BR-OPS-008, PD-007, PR-003/030, ARCH-001, MB-001/003/005, BR-001).

2026-10-12 기존 이용권의 담당 Trainer 교체 허용 확정: 같은 Pass에서 A→B로 담당을 바꿀 수 있으며 20회 중 5회 진행한 경우 잔여 15회·발급 조건/Issued Branch·과거 실제 수업/지급·정산을 유지한다. 취소/새 발급·횟수 재처리는 요구하지 않는다. 기존 사용자 일관성 지시로 일반 교체의 저장 후 현재 담당 반영·이력/감사와 현재 담당/별도 지원/관리 관계 기반 조회를 적용한다. 교체 Actor/Branch Scope·대상 Trainer/Pass 상태·과거 사실/늦은 등록과 기술 계약/경합은 후속이며 임의 권한 기본값을 두지 않는다. Product OPEN 23 OPEN / 7 CLOSED 및 ADR/Architecture 상태는 유지한다. 설계 문서 변경/업무 구현·검증 미완료다(BR-OPS-008, PD-007, PR-003/029/030, ARCH-001, MB-001/003/005, BR-001, NFR-001/004).

2026-10-12 회원 이동 대상 지점 확정: 같은 Organization의 운영 중인 활성 Branch로만 Member Home Branch를 변경할 수 있다. Master/Branch Admin 모두 비활성 대상은 Backend에서 거부하고 기존 소속/관계·Pass/이력을 유지한다. 기존 이동 권한·별도 승인 없음·즉시 적용/미래 예약 미지원은 유지한다. 아래 당시 미결정 중 새 이동 대상의 활성 조건만 해결됐으며 Branch 비활성화 자체의 기존 데이터/업무 영향·과거 소속 이력 정정 및 상태 변경/이동 경합·계약은 후속이다. Product OPEN 23 OPEN / 7 CLOSED와 ADR/Architecture 상태는 유지하며 설계 문서 변경/업무 구현·검증 미완료다(BR-OPS-007, PD-004, PR-002/030, MB-002/008, NFR-001).

2026-10-12 회원 Home Branch 변경 시점 확정: v1은 저장 완료 즉시 적용만 지원하고 미래 적용일 예약은 지원하지 않는다. 성공한 저장 이후의 후속 요청은 새 현재 소속 기준으로 관리/지원 지정·해제를 인가하며 실패하면 기존 소속을 유지한다. 기존 이동 권한·받는 지점 별도 승인 없음/지원 허용·독립 업무 Scope·Pass/과거 이력 보존은 유지한다. 아래 당시 미결정 중 Member 이동 적용 시점/미래 예약은 해결됐으며 과거 소속 이력 정정/소급·대상 Branch 상태·진행 중 요청/동시성 및 계약은 후속이다. Product OPEN 23 OPEN / 7 CLOSED 및 ADR/Architecture 상태는 유지한다. 설계 문서 변경이며 업무 구현/검증 미완료다(BR-OPS-007, PD-004, PR-002/030, MB-002, NFR-001/004).

2026-10-12 회원 Home Branch 변경 권한 확정: Master Organization 전체 또는 변경 전 회원 현재 Home Branch를 관리하는 Branch Admin이 동일 Organization 내 이동을 처리하며 받는 지점 별도 승인은 없다. Backend 현재 권한/대상 사실을 검증하고 반영 이후의 Home Branch 기반 관리는 새 소속을 따른다. 기존 지원 허용·다른 독립 업무 Scope와 Pass/과거 기록·지급/정산을 보존하며 중요 변경 이력/감사 원칙을 적용한다. 아래 당시 미결정 기록 중 회원 이동 Actor/Scope만 해결됐고 적용 시점·이력/정정·Branch 상태 조건과 Trainer 이동 권한·구체 계약은 후속이다. Product OPEN 23 OPEN / 7 CLOSED 및 ADR/Architecture 상태는 유지한다. 설계 문서 변경이며 업무 구현/검증은 미완료다(BR-OPS-007, PD-004, PR-002/030, MB-002, NFR-001/004).

2026-10-12 회원 전화번호 중복 허용 확정: 같은 Organization의 여러 회원이 같은 연락처를 사용할 수 있고 별도 Member 식별자로 구분한다. 번호 일치만으로 등록을 거부하거나 회원/Pass·이력·권한을 합치지 않는다. 일반 수정의 중복 허용도 기존 사용자 일관성 지시를 적용하며 전화번호 필수 입력·기존 인가 범위는 유지한다. 전화번호 검색은 인가된 회원 집합 안에서 각각 식별한다. 아래 이전 결정 당시의 중복 미결정 기록은 이 후속 승인으로 해당 부분만 해결됐다. 형식·검증·다른 항목/보존/필요 삭제·구체 계약은 후속이다. Product OPEN 23 OPEN / 7 CLOSED 및 ADR/Architecture 상태는 유지하며 설계 문서 반영/업무 구현·검증 미완료다(BR-OPS-006, PD-022, PR-002, NFR-005, LEGAL-001).

2026-10-12 회원 전화번호 필수 입력 확정: 새 회원 등록은 전화번호 필수이며 누락·빈값·공백만으로 완료할 수 없다. 일반 정보 수정에서도 필수 번호를 빈값으로 지우지 않는 원칙은 2026-10-11 사용자 일관성 지시로 적용한다. 기존 역할/관리 Scope·Trainer의 인가된 전체 번호 읽기는 유지하며 형식·중복/문자 인증·다른 수집 항목·보존/필요 삭제와 구체 계약은 후속이다. 아래 이전 결정 당시의 “필수 수집 미결정” 기록은 이 후속 승인으로 해당 부분만 해결됐다. Product OPEN 23 OPEN / 7 CLOSED 및 ADR/Architecture 상태는 유지한다. 설계 문서 반영이며 구현/업무 검증 완료가 아니다(BR-OPS-006, PD-022, PR-002, NFR-005, LEGAL-001).

2026-10-12 Trainer 회원 전화번호 조회 확정: 기존 조회 권한이 있는 담당/개별 지원 회원의 전체 전화번호를 조회할 수 있다. 잔여 0에도 기존 조회 권한이 유지되면 번호 조회를 유지하고 지원 해제 후 별도 권한이 없으면 공개하지 않는다. Backend 현재 Caller/대상 관계 검증·기존 관리 Scope와 로그/가상 예시 지침을 적용한다. 회원 범위·연락처 수정/내보내기·다른 필드/보상 권한을 넓히거나 전화번호 필수 수집을 결정한 것은 아니다. 필수 수집/형식·중복/검증·다른 필드/보존 및 계약은 후속이며 Product OPEN 23 OPEN / 7 CLOSED 및 ADR/Architecture 상태는 유지한다(BR-OPS-005, PD-002, PR-002/029/030, NFR-001/005, LEGAL-001).

2026-10-12 잔여 제외 필터 집계 기준 확정: 조회 권한이 확인된 Member의 전체 Pass 잔여로 판단하며 다른 담당 Trainer/Issued Branch도 포함한다. 내 담당 0회+다른 담당 10회이면 필터를 켜도 표시하고 전체 0회이면 제외한다. 개별 지원 회원도 같은 Member 전체 기준이며 기본 조회 포함/기존 인가는 유지한다. 기존 수동 만료로 보존된 5회는 0으로 간주하지 않으며 현재 사용 가능 여부와 구별한다. 개별 Pass/다른 Trainer 정보·전체 잔여 숫자 표시 권한을 일괄 부여하지 않는다. 다른 종료 상태의 잔여 정의/집계·담당 변경/비활성·필드/계약은 후속이다. Product OPEN 23 OPEN / 7 CLOSED 및 ADR/Architecture 상태는 유지한다(BR-OPS-005, PD-002, PR-002/029/030, MB-001/003/005).

2026-10-12 잔여 0 회원 조회/선택 필터 확정: 담당 Pass 잔여가 모두 0이어도 기존 담당 회원 조회는 유지하고 기본 조회에 포함한다. “잔여 0인 회원 제외”는 선택 필터로 제공하며 인가/담당·지원 관계·회원 상태를 변경하지 않는다. Backend Scope 검증과 Remaining > 0 등 실제 PT 사용 조건은 유지한다. 여러 Pass의 잔여 집계 범위/지원 대상 판정·수동 만료/취소 등 다른 상태의 조회 영향·필드/계약은 후속이다. Product OPEN 23 OPEN / 7 CLOSED와 ADR/Architecture 상태는 유지하며 이번 변경은 설계 문서뿐이다(BR-OPS-005, PD-002, PR-002/029/030, MB-001/003/005).

2026-10-12 회원 소속 이동 후 지원 조회 허용 유지 확정: 동일 Organization의 Member Home Branch 변경만으로 기존 Trainer/Member의 개별 지원 조회 허용을 해제하거나 재지정하지 않는다. 지정/해제는 계속 Master Organization/각 처리 시점 Member 현재 Home Branch 관리 Branch Admin이며 이전 지점/과거 지정자 권한은 유지하지 않는다. Trainer Home Branch만 변경되는 경우도 사용자 일관성 지시로 같은 유지 원칙을 적용한다. Backend 인가·기존 감사/과거 PT·Pass·지급/정산은 유지하며 일반/지원 구분은 수업 당시 Trainer 소속 기준이다. 이동 자체/다른 상태/담당 관계·절차/필드·Architecture 계약은 후속이다. Product OPEN 23 OPEN / 7 CLOSED와 ADR/Architecture 상태는 유지한다(BR-OPS-005, PD-002, PR-002/029/030, MB-001/002/003/005).

2026-10-12 지원 조회 허용 기간 확정: 개별 Trainer/Member 허용은 관리자 해제 전까지 유지하며 고정 종료일/기간 자동 종료·연장을 두지 않는다. 수동 해제 권한은 기존 지정 권한과 같은 Master Organization/Branch Admin 처리 시점 Member 현재 Home Branch 기준을 적용한다(2026-10-11 사용자 일관성 지시). Backend 인가·중요 권한 변경 감사와 별도의 담당/관리 권한을 유지한다. 소속 이동 후 기존 허용·대상 상태/담당 관계 인정·절차/공개 항목은 후속이며 Product OPEN 23 OPEN / 7 CLOSED 및 ADR/Architecture 상태는 유지한다(BR-OPS-005, PD-002, PR-002/029/030, NFR-004).

2026-10-12 지원 대상 지정 권한 확정: Master는 Organization 전체, Branch Admin은 지정 시점 현재 관리 Branch=Member 현재 Home Branch인 경우만 허용한다. 수원 Member를 강남 Trainer의 지원 조회 대상으로 지정할 때 수원 관리자/Master가 담당하며 수행/Trainer 소속/Pass 발급 지점만으로는 지정할 수 없다. Backend가 현재 Actor 권한/Scope·Member 소속·대상 Organization을 확인하고 기존 중요 권한 변경 감사를 적용한다. 대상 Trainer 보상/정산·전체 회원 공개 권한이나 Home Branch 변경을 부여하지 않는다. 기간/철회 주체·이동 후 기존 허용·절차/공개 항목은 후속이며 Product OPEN은 23 OPEN / 7 CLOSED를 유지한다(BR-OPS-005, PD-002, PR-002/029/030, MB-001/002/003/005, NFR-004).

2026-10-12 Trainer 회원 검색·조회 대상 확정: 본인이 담당 Trainer로 지정된 Pass의 회원과 개별 허용된 지원 수업 대상 회원만이다. 같은 Home Branch/타 지점 PT 가능 사실만으로 지점·Organization 전체 조회는 불가하다. Backend는 목록·검색·직접 ID 상세마다 검증된 Trainer 연결/Organization Scope와 대상별 담당·지원 허용 사실을 확인한다. 관리자 겸임자의 별도 관리 Scope·민감 보상 금지·기존 PT/Pass 규칙은 유지한다. 담당 관계 인정·지원 지정/철회 주체·기간/절차·공개 항목/나머지 PT 업무 인가는 후속이며 Product OPEN은 23 OPEN / 7 CLOSED를 유지한다(BR-OPS-005, PD-002, PR-002/029/030, MB-001/003/005).

2026-10-12 상품 판매 중단의 영향 확정: Master가 공통 PT 상품을 판매 중단하면 새 Pass 발급만 차단하고 이미 발급된 Pass는 기존 권한·잔여·사용 조건에 따라 계속 사용할 수 있다. 기존 Pass를 상품 판매 중단만으로 후보에서 제외하거나 자동 만료/취소하지 않으며 발급 조건·잔여/사용 상태·과거 수업/지급/정산을 보존한다. 잔여 0/개별 수동 만료 등 다른 사용 불가 사유를 면제하지 않는다. Backend에서 새 발급의 판매 가능 상태와 기존 Pass의 사용 조건을 구별하여 검증한다. 판매 재개/나머지 상태·삭제/계약·저장 상세는 후속이며 Product OPEN은 23 OPEN / 7 CLOSED를 유지한다(BR-PAY-001/006, PD-011, PR-003/006).

2026-10-12 공통 PT 상품 생성·수정 권한 확정: Master Admin만 Organization 범위에서 허용한다. Master 권한 없는 Branch Admin·Operator·Trainer는 생성·수정할 수 없으며 Backend에서 현재 Master 권한/Organization Scope를 검증한다. 기존 Pass의 발급 당시 상품 조건·잔여·과거 기록은 보존하고 변경은 새 Pass부터 적용한다. 상품 조회/Pass 발급 권한 및 상태/삭제의 미정 상세는 별도다(BR-PAY-001, PD-004, PR-006/030). MB-007 CLOSED로 현재 Product OPEN은 23 OPEN / 7 CLOSED이며 아래 이전 날짜의 수치는 당시 기록이다.

2026-10-12 수동 만료 전 수업의 늦은 등록 확정: 실제 수업 당시 사용 가능했고 수동 만료 전에 진행했다면 현재 만료 상태여도 기존 PT 권한·정산·현재 잔여 조건을 충족하여 등록할 수 있다. 별도 만료 해제 없이 해당 Pass를 후보에 포함하고 기존 FIXED_AMOUNT 우선/FIFO로 선택하여 현재 잔여에서 1회 차감한다(만료/5회→만료/4회). 현재 만료 상태·이력과 기존 기록을 보존한다. 신규 일반 지급은 기록 생성 시점 설정, 일반/지원 구분은 실제 수업 당시 소속/수행 지점, 확정 월 반영은 기존 해제/재확정 원칙을 유지한다. 다른 종료 사유·시점/이력 사실 판정 및 취소 복원/조정 연계는 후속이다(BR-PAY-006, BR-OPS-003/004, PD-007, PR-003/008, BR-001/002/007·ARCH-003).

2026-10-12 수동 만료 해제 확정: 권한 있는 관리자는 같은 Pass의 만료를 해제할 수 있다. 만료와 동일한 Master Organization 전체/Branch Admin 처리 시점 현재 관리 Branch=Issued Branch 범위에서 사유/전후 상태·처리자/시점 이력과 감사를 남기며 기존 만료 사실을 보존한다. 기존 직접 처리 원칙을 동일 적용하고 별도 승인 대기를 추가하지 않는다. 해제 자체로 잔여 횟수를 바꾸거나 새 Pass를 만들지 않는다(5회→5회). 해제 후에도 잔여 > 0 등 기존 사용 조건을 충족해야 한다. 과거 수업/지급/정산 이력 보존을 유지하며 만료 전/중 수업 지연 등록·별도 취소 복원/조정 연계·상태 표현은 후속이다(BR-OPS-004, PD-007, PR-003/030, BR-001/002/007·ARCH-003).

2026-10-12 수동 만료의 잔여 처리 확정: 만료 자체로 Remaining을 변경하지 않고 사용만 차단한다. 잔여 5회는 만료 후에도 5회이며 0 덮어쓰기/소멸 차감/수업 사용으로 처리하지 않는다. 양수 잔여라는 이유로 자동 재개하지 않는다. 기존 관리 Scope·사유/이력/과거 기록 보존을 유지하며 해제/재개·과거 수업/취소 복원·다른 종료 사유의 잔여 처리는 후속이다(BR-OPS-004, PD-007, PR-003, BR-001/002/007·ARCH-003).

2026-10-12 수동 만료의 관리 범위 확정: Master는 Organization 전체, Branch Admin은 자신의 현재 관리 Branch에서 발급한 Pass만 만료 처리한다. Member/Trainer 소속이나 실제 수업 지점은 만료 권한 기준이 아니다. Backend의 현재 Actor Scope/Issued Branch 검증과 기존 사유/이력·과거 기록 보존을 유지한다. 잔여 처리·만료 정정/재개·과거 수업 연계·상태 표현은 후속이다(BR-OPS-004, PD-007, PR-003/030, BR-001).

2026-10-12 이용권 수동 만료 확정: 별도 만료일/유효기간·시간 경과 자동 만료는 두지 않고 관리자가 수동 만료 처리할 수 있다. 과거 수업/지급/정산 이력을 보존하고 기존 수동 변경의 사유/이력 원칙을 동일 적용한다. 관리 지점 기준·남은 횟수·잘못된 만료 정정/재개·만료 전 수업의 지연 등록·상태 표현은 후속이다(BR-OPS-004, PD-007/011, PR-003, BR-001/002/007·ARCH-003).

2026-10-12 과거 수업의 이용권 후보 확정: 실제 수업 당시 이미 발급된 Pass만 해당 수업의 차감 후보이며, 이후 발급된 것은 늦은 등록 시 보유 중이어도 제외한다. 조건을 충족한 후보 안에서 기존 FIXED_AMOUNT 우선/FIFO를 적용한다. 만료/종료/취소 상태의 시간 기준과 발급/시작 정보·사실 확인/정정·시각 정밀도는 후속이다(BR-PAY-006, BR-OPS-003, PD-007, PR-003, BR-001/002·ARCH-003).

2026-10-11 Trainer 과거 수업 직접 등록 확정: 해당 Trainer/실제 진행 월 정산이 미확정이면 기존 Allowed PT Scope에서 자신의 과거 수업을 직접 등록할 수 있다. 당월/최근 N일 제한을 추가하지 않는다. 신규 일반 지급 설정은 기록 생성 시점, 일반/지원 구분은 실제 수업 당시 소속 기준을 유지한다. Trainer의 정산 해제/재확정 권한은 추가하지 않으며 확정 월은 기존 관리자 해제 후 반영/재확정 원칙과 연계한다. 나머지 대상/Pass 조건·시간대/월 경계·계약/동시성은 후속이다(BR-OPS-003, PD-008, PR-008, BR-008).

2026-10-11 동일 일자 복수 PT 수업 확정: 같은 회원이 하루에 실제로 여러 수업을 받으면 수업마다 별도 기록/1회 차감을 수행하며 하루 1회로 제한하지 않는다. 날짜가 같다는 이유로 별개 수업을 합치거나 거부하지 않고, 같은 수업의 재전송/중복 저장은 별도로 방지한다. 시간대/소급 범위/월 경계·구체 식별 계약은 후속이다(BR-OPS-002, PD-008, PR-008, BR-008).

2026-10-11 타 지점 이용권 사용 확정: 동일 Organization의 사용 가능한 PT Pass는 발급 Branch 밖에서도 별도 사전 승인 없이 사용한다. Issued Branch 차이로 후보를 제외하거나 발급 지점 우선순위를 추가하지 않고 기존 FIXED_AMOUNT 우선/FIFO·지점 사실을 유지한다. 특정 이용 허용과 Member 정보 조회/Actor 업무 권한은 별개이며 나머지 접근·상태/잔여 조건은 후속이다(BR-OPS-001/BR-PAY-006, PD-007, PR-003/030, MB-003/005).

2026-10-11 지원→일반 정정의 지급 설정 기준 확정: 기존 PT 기록의 최초 생성 시점 Rate/Fixed Amount를 적용한다. 정정 시점/실제 수업일 설정으로 바꾸지 않으며 기존 기록·Pass 차감·정정/확정본 이력 보존 원칙을 유지한다. 당시 설정 근거 확인/저장·계약과 나머지 정정 조건은 후속이다(BR-PAY-011/012, PD-010, PR-009, MB-005/BR-007).

2026-10-11 수행 지점 정정 방법 확정: Master가 기존 PT 기록을 정정하고 일반/지원 보상 방식도 바로잡는다. 원래 Pass 차감 유지·취소/재등록 없음·변경 전 사실/보상 이력 보존·중복 합산 금지. 확정 월은 기존 해제 → 정정 → 같은 월 재확정 원칙을 동일 적용한다. 지원→일반의 지급 설정 기준 시점과 나머지 정정/계약 상세는 후속이다(BR-OPS-001, BR-PAY-012, PD-010, PR-009, MB-005/BR-007).

2026-10-11 일반/지원 수업 구분 시점 확정: 실제 수업 당시 Trainer Home Branch와 Performed Branch를 비교한다. 이동 후 늦은 등록도 당시 구분을 유지한다. 일반 PT 지급 설정은 기록 생성 시점, 보상/월 정산 관리 권한은 처리 시점 현재 Home Branch 기준을 유지한다. 당시 소속 확인 예외·이동 적용 시점/소급 범위·사실 정정의 보상 전환은 잔여 OPEN이다(BR-OPS-001, BR-PAY-011/012, PR-008, PD-027, MB-001/005).

2026-10-11 수행 지점 오류 정정 권한 확정: PT 기록의 Performed Branch 자체 오류 정정은 Master Admin 전용이다. Branch Admin은 기존/실제 수행 지점이 관리 Branch여도 해당 값을 정정할 수 없다. 일반 기록 정정/취소의 기존 범위는 유지하며 지점 정정 방식·확정 월 연계·보상 전환/적용 설정 시점은 잔여 OPEN이다(PD-010, PR-009, BR-OPS-001, BR-007/MB-005).

2026-10-11 수업 취소의 보상 연동 확정: PT 진행 기록을 취소하면 해당 수업의 보상으로 입력한 추가실적도 함께 자동 무효 처리하여 유효 정산/지점 비용에서 제외한다. 원래 금액·이력은 보존하며 관리자 직접 금액 입력과 기존 지점별 권한을 유지한다. 확정 월은 기존 해제 → 기록 취소/보상 무효 → 같은 월 재확정 순서다. 다른 추가실적·다른 정정 정책 및 계약/저장/UoW·동시성 상세는 잔여 OPEN 또는 PROPOSED다(BR-PAY-015, BR-OPS-001, PD-010/027, PR-009/031).

2026-10-11 Operator 정정·취소 권한 확정: Operator 역할만으로는 PT 진행 기록을 정산 확정 전후 모두 정정·취소할 수 없다. Master Organization 전체/Branch Admin 실제 Performed Branch 기준으로 담당하며 Trainer 역할의 금지도 유지한다. Operator의 다른 업무·Branch Scope 부여와 나머지 취소/정산 연동 상세는 잔여 OPEN이다(PD-010, PR-009, MB-005/BR-007, MB-004/ARCH-001).

2026-10-11 확정된 타 지점 수업 취소 순서 확정: Trainer 현재 소속 지점의 해당 월 정산 해제 → 실제 수행 지점의 기록 취소 → 현재 소속 지점의 같은 월 재확정. 각 업무의 기존 권한을 유지하며 Master는 전체 흐름을 처리할 수 있다. 이전 확정본·이력과 기존 사유/감사·재확정 조건을 유지한다. 취소의 지급/추가실적 연동·잔여 복원 예외·Operator 권한과 구체 단계 계약/동시성은 잔여 OPEN 또는 PROPOSED다(PD-010, PR-009/010, BR-007/009).

2026-10-11 PT 기록 정정·취소 담당 지점 확정: Master는 Organization 전체, Branch Admin은 실제 Performed Branch 기준으로 담당한다. Trainer Home Branch만으로 다른 지점 수업 기록을 정정할 수 없다. 추가실적 금액 입력·보상 설정·월 정산 권한은 기존 Home Branch 기준을 유지한다. Operator 권한·수행 지점 자체 정정·확정 정산과 연계된 교차 지점 처리 상세는 잔여 OPEN이다(PD-010, PR-009, MB-005/BR-007).

2026-10-11 Trainer 정정·취소 권한 확정: Trainer 역할만으로는 본인 PT 진행 기록도 정산 확정 전후 모두 정정·취소할 수 없다. 허용된 관리 담당자가 해당 업무의 권한·Branch Scope 안에서 처리한다. 관리자 겸임자는 해당 관리 권한으로 판단하며 세부 관리 Scope·정정 절차는 잔여 OPEN이다(PD-010, PR-009, MB-005/BR-007).

2026-10-11 보상 입력 범위 확정: 일반 PT 수당의 기존 RATE/FIXED_AMOUNT 자동 계산·확정과 기본급의 별도 반영을 유지한다. 그 외 타 지점 지원 수업·회원 유지·기타 보상은 모두 권한 있는 관리자가 기존 추가실적에 직접 입력하며 사유별 별도 보상 제도를 만들지 않는다. 상세 근거는 PD-027과 BR-PAY-015/PR-031을 따른다.

2026-10-11 지원 수업 외 추가실적 확정 후 금액 오류의 동일 정정 흐름: 지원 수업 외 실적의 확정 후 금액 오류도 해당 Trainer/월 해제 → 양수 금액 정정 → 같은 월 재확정·이전 확정본/구성/이력 보존(2026-10-11 사용자 일관성 지시 적용). Master Organization/Branch Admin 각 처리 시점 현재 Home Branch·본인 건 포함·별도 승인 없음·해제/정정 모두 사유 필수·감사·기존 재확정 조건/미입력 지원 수업 차단 유지. 발생 월/당시 Home Branch 비용 유지. 금액 외 정보 수정/취소·나머지 기간/금액 제약은 OPEN.

2026-10-11 지원 수업 외 추가실적 등록·수정의 동일 양수 기준: 지원 수업 외 추가실적은 최초 등록과 확정 전 금액 수정 모두 양수만 허용(Product 확정, 2026-10-11 사용자 일관성 지시 적용). 0원·음수·누락 수정 거부/요청 직전 금액·이력·정산 입력 상태 유지; 사유가 있어도 0원 수정 불가. 기존 관리자 Scope/본인 건/승인 생략/사유·이력/감사 유지. 지원 수업 보상 및 월별 수동 기본급의 승인된 사유 필수 0원 예외는 유지. 상한/정밀도·금액 외 정보 수정/취소는 OPEN.

2026-10-11 확정 전 지원 수업 외 추가실적 금액 수정: 월 정산 확정 전 비지원 추가실적 금액 수정은 Master Organization 전체/Branch Admin 각 수정 시점 Trainer 현재 Home Branch 기준으로 허용(Product 확정, 2026-10-11). 관리 범위 안 본인 건 포함·별도 승인 없음·변경 사유 필수·전후 금액/사유/수정자/시점 이력과 감사. 사유 누락 거부/요청 직전 금액 유지. 발생 월/당시 Home Branch 비용 유지. 수정 금액의 나머지 입력 제약, 금액 외 정보 수정/취소는 OPEN.

2026-10-11 관리자 본인 누락 실적 반영: 관리 범위 안 관리자·Trainer 겸임자의 본인 누락 실적 후등록 해제/재확정도 별도 승인 없이 허용(Product 확정, 2026-10-11). Master Organization 범위/Branch Admin 각 처리 시점 본인 현재 Home Branch 일치·해제 사유 필수·본인 감사/이전 확정본 보존·기존 후등록 순서/월/비용 귀속·재확정 조건/미입력 지원 수업 차단 유지. Trainer 단독 권한 없음. 비지원 실적의 금액 외 정보 수정/취소 등은 OPEN.

2026-10-11 비본인 누락 실적 반영의 별도 Master 승인 생략: Branch Admin의 본인이 아닌 소속 Trainer 누락 실적 후등록 해제/재확정은 별도 Master 승인 없음(Product 확정, 2026-10-11). 각 처리 시점 현재 Home Branch 인가·해제 사유 필수·해제 후 등록/동일 월 재확정·이전 확정본/감사·기존 확정 조건/미입력 지원 수업 차단 유지. 관리 범위 안 관리자 본인 건의 해제/재확정 허용·별도 승인 없음도 확정(2026-10-11).

2026-10-11 누락 실적 반영의 확정 해제 사유: 확정 월의 누락된 지원 수업 외 실적 반영을 위한 해제 사유 필수(Product 확정, 2026-10-11). 사유 없는 해제 요청은 거부하고 요청 직전 확정 상태/확정본/기존 실적·정산 구성/금액 유지. 성공 시 대상 Trainer/월·사유·해제자·시점 이력/감사와 이전 확정본 보존. 현재 Home Branch 인가·기존 후등록 순서/월/비용 귀속 유지. 이 흐름의 해제/재확정은 관리 범위 안 본인 건도 별도 승인 없이 허용(2026-10-11).

2026-10-11 지원 수업 외 실적 등록·누락 후등록의 현재 소속 기준: 지원 수업 외 Additional Performance의 등록과, 확정된 발생 월의 누락분 반영을 위한 해당 Trainer·월 정산 확정 해제·재확정은 Master Admin에게 Organization 전체, Branch Admin에게 각 업무 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 등록·해제·재확정 요청마다 현재 소속과 관리 권한을 검증하고 최초 단계의 소속으로 후속 권한을 고정하지 않는다. 이전 소속·실적 발생 당시 소속·Performed Branch·클라이언트가 전달한 Branch Context만으로 권한을 부여하지 않는다. 9월 수원점 소속 때 발생한 회원 유지 실적을 10월 강남점 이동 후 처리하면 강남점 Branch Admin/Master가 담당하고, 별도 Master 권한 없는 이전 수원점 Branch Admin은 처리할 수 없다. 실적은 여전히 9월 정산·수원점 비용이며 이전 확정본과 감사 이력을 보존한다. 등록의 내용+양수 금액 필수·관리 범위 안 본인 등록·별도 승인 없음과 재확정의 기존 확정 조건/미입력 지원 수업 차단을 유지한다. 이 결정은 위 등록 및 누락분 후등록의 역할·관리 범위·소속 기준 시점에 한정한다. 누락분 반영을 위한 해제·재확정의 관리 범위 안 본인 건 허용·별도 승인 없음도 후속 사용자 결정으로 확정했다. 지원 수업 외 기존 실적의 정정/취소 권한·소속 기준 및 처리 절차는 별도 OPEN이다. 기존 지원 수업 보상/기본급 정정 권한이나 비용/조회 범위를 확대하지 않는다.

**2026-10-10 후속 사용자 확정:** Master Admin/Branch Admin이 Trainer를 겸하며 한 계정으로 관리 업무와 본인의 PT 진행 기록을 수행할 수 있다. 최초 비밀번호는 Master가 전달한 일회용 설정 링크로 대상자가 직접 설정한다. [역할표](users-and-roles.md)와 [PD-001/019](product-decisions.md)에 반영했다. 겸임자의 보상 설정은 사용자의 최종 정정에 따라 관리 권한 범위 안이면 본인도 조회·변경 가능하다. Master는 본인 포함, Branch Admin은 본인 Trainer의 Home Branch가 관리 지점과 일치할 때 허용한다. 역할/인가의 구체 모델, 링크 전달 채널·유효기간·재발급 등 잔여 질문은 ARCH-001/002 OPEN을 유지한다.

같은 날 MB-009를 CLOSED 처리하고 사용자 정정 답변을 최종 반영했다. 타 지점 수업은 일반 PT 수당 대신 해당 수업의 보상 전체를 Additional Performance로 처리한다. 타 지점 지원 수업 금액은 권한 있는 관리자가 수업 건별로 직접 입력한다(같은 날 금액 계산 질문의 3번). 같은 수업의 일반 Session Payment를 정산에 별도로 더하지 않는다. 추가실적 직접 등록은 Master Admin이 Organization 전체 Trainer, Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer에게만 허용하는 것으로 확정했다. 지원받은 지점이라는 이유만으로 다른 소속 Trainer에게 등록할 수 없다. 관리자·Trainer 겸임자도 관리 범위 안이면 본인의 추가실적을 직접 등록할 수 있다. Master는 Organization 범위 안의 본인, Branch Admin은 본인 Trainer Home Branch가 관리 Branch일 때 허용한다. 본인 등록도 동일하게 감사한다. Branch Admin이 본인이 아닌 소속 Trainer에게 직접 등록할 때는 별도 Master 승인을 두지 않는다. 관리 범위 안에서 직접 등록한 본인 건도 별도 승인 없이 처리하며 동일하게 감사한다. 타 지점 지원 수업은 보상 금액 없이도 허용된 PT 진행 기록과 Pass 차감을 먼저 완료한다. 권한 있는 관리자가 나중에 수업 건별 금액을 저장할 때 해당 Additional Performance 보상을 확정한다. 금액 미입력은 확정된 0원과 구분하고 누락 건을 추적할 수 있어야 한다. 해당 Trainer의 해당 월 정산 대상 지원 수업에 금액 미입력 건이 하나라도 있으면 그 Trainer·월 정산을 확정할 수 없다. 타 지점 지원 수업 보상은 권한 있는 관리자가 사유를 기록하면 0원으로 명시적으로 확정할 수 있다. 사유 없는 0원 입력은 보상 확정이 불가하다. 사유를 남기고 확정한 0원은 금액 미입력이 아니므로 그 건으로 월 정산 확정을 차단하지 않는다. 다른 미입력 건이 남으면 기존 차단 조건을 유지한다. 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin에게 Organization 전체, Branch Admin에게 대상 Trainer Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안의 본인 건도 허용하고 변경 이력을 남긴다. 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin·Branch Admin 모두 관리 범위 안에서 본인 건을 포함해 별도 승인 없이 저장 성공 즉시 반영한다. Master나 다른 관리자의 승인 대기를 두지 않으며 권한 검증과 변경 이력을 유지한다. 월 정산 확정 전 지원 수업 보상 금액의 모든 수정에는 변경 사유가 필수다. 양수 간 변경·0원에서 양수로 변경·양수에서 0원으로 변경 모두 적용하며, 사유 없이는 금액을 수정할 수 없다. 변경 전후 금액·변경 사유·수정자·수정 시점을 이력으로 남긴다. 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer의 지원 수업 보상 정정을 위해 월 정산을 확정 해제·재확정할 때는 Master의 별도 승인을 두지 않는다. Master 승인 대기 단계 없이 관리 범위 안에서 직접 처리하며 이전 확정본과 해제·재확정 이력 및 감사를 유지한다. 지원 수업 보상 정정의 월 정산 확정 해제에는 사유가 필수이며, 사유 없이 해제할 수 없다. 사유·해제자·시점을 이력으로 남긴다. 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 남은 정정·취소 절차는 BR-009/013 등 관련 OPEN을 따른다. 지원 수업 외 실적의 금액 외 정보 수정/취소의 소속 이동 시 권한 기준 시점·지원 수업 외 추가실적의 남은 입력 제약·금액 미입력 건의 추적 표현·정정 연동(BR-013), 지점 귀속·공개(MB-010/006)는 계속 OPEN이다.

같은 날 BR-011은 기존 Pass의 발급 당시 상품 가격·총횟수·Payment Type 유지로 CLOSED 처리했다. 변경된 상품 조건은 새로 발급하는 Pass부터 적용한다. Trainer의 Rate/Fixed Amount는 기존대로 PT 진행 등록 시점의 설정을 적용한다.

**2026-09-17 지점 관계·추가실적·월 기본급·보상 설정 권한 개정.** 최신 사용자 확정사항이 이전 Baseline의 권한·정산·미정 관계를 대체하여 Product 문서를 갱신했다. 기존 C# 프로그램을 실제 운영에서 대체하는 새 웹 서비스이며 C# 구현은 AS-IS 참고다. 기존 데이터·계정·암호 이관 없이 새로 시작한다. 수정 범위는 `docs/product/`이고 Architecture·애플리케이션 구현은 수행하지 않는다.

## 변경 이력과 현재 유효 기준

| 이전 기준 — 변경 이력이며 현재 규칙 아님 | 현재 유효 기준 |
| --- | --- |
| 이전 Single Branch / Trainer non-login / PC 중심 방향 | 하나의 Organization 아래 여러 Branch, Trainer 직접 로그인/Session 등록, Responsive Web 유지 |
| Trainer/Member 소속 및 Pass 발급·교차 이용 미정 | 각각 단일 Home Branch / 단일 Issued Branch, 허용된 타 지점 이용 가능 |
| Product 공통/지점별 미정 | Organization 공통 Catalog, 지점별 가격 정책 추가 없음 |
| Branch Admin 관리 Branch 수 미정 | 단일 Branch 관리, 중간 다지점 역할 추가 없음 |
| Master Admin 전용 Rate/Fixed Amount | 세 보상 항목에 Master 전체 / Branch Admin 자기 Home Branch 소속 Trainer 권한 |
| 기본급 관리/합산 미채택, Session 지급액 중심 정산 | 월 고정 기본급·추가실적 v1 도입, 세 구성 요소 월 합산 |

과거 방향은 활성 규칙으로 적용하지 않는다. 기존 Requirement/Business Rule/Decision ID는 유지하고 새로운 추가실적 PR-031/PD-027 및 새 규칙 BR-PAY-014–016만 추가했다.

## 확정 v1과 범위 경계

Trainer는 한 시점에 Home Branch 하나에 소속되고 Branch에는 여러 Trainer가 있을 수 있다. Branch당 Trainer 한 명인 1:1이나 Trainer 동시 복수 소속 N:M을 요구하지 않는다. Member도 Home Branch 하나를 가지며 Pass는 Issued Branch 하나를 가진다. Trainer·Member·Pass는 허용된 조건에서 타 지점 PT 업무를 수행·이용할 수 있다. Session은 실제 Performed Branch를 식별하고 소속·발급 지점 변경으로 과거 수행 지점이 바뀌지 않아야 한다. Product는 Organization 공통 Catalog이며 지점별 가격 정책은 추가하지 않는다. Branch Admin은 하나의 Branch를 관리하고 일부 여러 지점만 담당하는 중간 관리자 역할은 추가하지 않는다.

Trainer Compensation Setting은 Rate·Fixed Amount·Base Salary이며 Product별 Trainer 지급 값은 도입하지 않는다. Rate / Fixed Amount / Base Salary 세 항목의 조회·설정·변경은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 단일 Branch를 Home Branch로 가진 Trainer에게만 허용한다. 관리자와 Trainer를 겸하는 계정은 관리 권한 범위 안이면 본인의 세 항목도 조회·변경할 수 있다. Master Admin은 본인 포함 허용하며, Branch Admin은 본인 Trainer의 Home Branch가 관리 Branch일 때 본인도 허용한다. 관리자 권한이 없는 Operator·Trainer 계정은 본인 포함 모든 Trainer 설정 조회·변경이 불가하다. 타 지점 지원 수업은 보상 설정 접근 권한을 부여하지 않는다. Backend에서 대상 Trainer의 Home Branch를 검증하며 직접 ID 요청과 감사·정산 등 우회 경로에도 제한을 적용한다.

모든 보상 설정 변경(최초 설정 포함)에 대상 Trainer, 변경 항목, 변경 전 값, 변경 후 값, 변경 Actor, Actor의 권한 및 Branch Context, 변경 시점을 추적한다. 별도 Master Admin 승인 없이 변경 가능하며 변경 요청→승인 대기→승인→반영 절차를 추가하지 않는다. 이 결정은 추가실적 승인이나 월 정산 마감/확정 절차를 면제하지 않는다.

Base Salary 변경 시 권한 있는 관리자가 적용 시작 월을 지정하며 아직 확정하지 않은 과거 월도 선택할 수 있다(BR-PAY-014). 변경이 적용되며 월별 기본급을 수동 지정하지 않은 미확정 정산의 기본급·합계는 자동 반영하며 별도의 반영 작업을 요구하지 않는다. 이미 확정된 월 정산의 적용 기본급·합계는 자동 변경하지 않으며 미확정 정산을 자동 확정하지도 않는다. 확정된 월의 기본급 오류는 해당 월 확정 해제 → 기본급 정정 → 동일 월 재확정으로 처리하고 이전 확정본을 보존한다. 기본급 오류 정정의 확정 해제·재확정은 Master Admin에게 Organization 전체, Branch Admin에게 각 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 처리한다. 확정된 월의 기본급 오류 정정에서 확정 해제와 해당 월 기본급 수정 모두 사유가 필수다. Master Admin·Branch Admin 및 관리 범위 안 본인 건에 동일하게 적용한다. 해제 사유·해제자·시점과 변경 전후 기본급·수정 사유·수정자·시점을 이력으로 남긴다. 기본급 오류 정정은 대상 Trainer의 해당 월 정산에만 적용하며 현재·미래 기본급 설정과 다른 월 정산은 유지한다. 지속적인 기본급 변경은 별도로 적용 시작 월을 지정하는 기존 흐름을 따른다. 입사·퇴사·휴직이 있는 달의 적용 기본급은 관리자가 해당 Trainer·월의 금액을 직접 지정한다. 예를 들어 월 기본급 설정이 2,500,000원이어도 해당 월만 1,500,000원을 적용할 수 있으며, 이 지정으로 현재·미래 기본급 설정과 다른 월 정산은 변경하지 않는다. 월별로 수동 지정한 기본급은 이후 일반 기본급 설정이 변경되어도 유지한다. 일반 설정 변경의 미확정 정산 자동 반영은 수동 지정이 없는 월에 적용하며, 수동 지정 월의 금액을 바꾸려면 관리자가 해당 월 금액을 직접 수정한다. 미확정 월의 기본급을 최초 수동 지정하거나 다시 수정할 때 모두 사유가 필수다. 사유가 없는 요청은 거부하고 요청 직전의 수동 지정 여부·적용 금액·월 합계를 유지한다. 대상 Trainer·월, 지정/수정 전후 금액·사유·처리자·처리 시점을 이력으로 남긴다. 미확정 월 기본급의 최초 수동 지정·수정은 Master Admin의 Organization 전체, Branch Admin의 각 처리 시점 대상 Trainer 현재 Home Branch가 관리 Branch와 일치하는 범위에서 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 직접 처리한다. 추가 사용자 확정(2026-10-11): 해당 월 기본급은 권한 있는 관리자가 사유를 남기면 0원으로 명시적으로 수동 지정할 수 있다. 수동 지정한 0원은 미입력과 구분하며, 미입력이나 누락된 일반 설정을 자동으로 0원으로 대체하지 않는다. 해당 월 기본급에만 적용하고 다른 유효 지급·추가실적은 기존 규칙대로 합산한다. 미리 등록할 수 있는 미래 적용 시작 월의 범위와 월별 수동 지정 금액의 나머지 입력 제약 등은 BR-012/BR-010 OPEN이다.

2026-10-11 기본급 지속 적용 명확화: 일반 Base Salary 설정은 관리자가 지정한 적용 시작 월부터 다음 기본급 변경의 적용 시작 월 전까지 매월 계속 적용한다. 적용 종료 월을 지정하거나 같은 금액을 매월 다시 등록할 필요는 없다. 예를 들어 10월부터 2,700,000원으로 변경하고 이후 변경이 없으면 11월·12월 이후에도 같은 금액을 적용한다. 특정 월 수동 지정은 그 월에만 적용하는 별도 예외다.

2026-10-11 최초 월 정산 확정 권한: 월 정산의 최초 확정은 Master Admin에게 Organization 전체 Trainer, Branch Admin에게 확정 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 직접 확정한다. 미입력 지원 수업에 의한 해당 Trainer·월 확정 차단은 유지한다. 상세 공개·지점 귀속과 나머지 확정/마감 조건은 BR-009 및 MB-006/010 OPEN이다.

2026-10-11 월 정산 조회 범위: 현재 자기 Branch 소속 Trainer의 해당 월 정산 전체 금액·구성 내역은 타 지점 지원 수업 보상까지 공개한다(조회 시점 현재 Home Branch 기준, 2026-10-11 사용자 확정). 관리 범위 안 본인도 포함하고 Master의 Organization 전체 조회는 유지한다. 대상 월·이전 확정본/세부 계산 근거·감사 공개의 남은 상세와 지점 비용 귀속은 MB-006/010 OPEN이다.

2026-10-11 지원 수업 보상의 비용 집계: 타 지점 지원 수업의 전체 보상으로 확정한 Additional Performance 금액은 해당 수업의 실제 Performed Branch 비용으로 집계한다. Trainer 월 정산에는 한 번 합산하고 기존 입력·정정·확정·조회 권한은 유지한다. 다른 보상 항목의 비용 귀속과 비용 보고 공개/집계 상세는 MB-010/006 OPEN이다.

2026-10-11 이동월 기본급 비용 귀속: 월중 Trainer 지점 이동이 있는 달의 해당 월 적용 기본급 비용은 대상 월의 월말 Home Branch 한 곳에 전액 귀속한다. 수동 지정이 있으면 그 월 적용액 전액을 사용하고 지급액·한 번 합산·기존 관리 권한은 유지한다. 이후 소속 이동만으로 과거 귀속을 바꾸지 않는다. 월말 소속 식별 불가 등 예외와 나머지 비용 귀속·보고 공개/집계 상세는 MB-010/006 OPEN이다.

2026-10-11 일반 PT 수당 비용 귀속: 일반 Session Payment는 해당 PT 진행 기록의 실제 Performed Branch 비용으로 집계한다. 이미 확정된 수업별 지급액을 지점별로 합산하며 대상 월말 Home Branch로 전액을 모으지 않는다. Trainer 월 지급 합계·과거 확정 지급·기존 권한은 유지한다. 지원 수업은 추가실적만 합산하고 이동월 기본급은 대상 월말 Home Branch 전액 귀속을 유지한다. 다른 추가실적 귀속·기본급 귀속의 남은 예외·비용 보고 공개/집계 상세는 MB-010/006 OPEN이다.

2026-10-11 지원 수업 외 추가실적 비용 귀속: 지원 수업 외 Additional Performance의 비용은 실적 발생 당시 대상 Trainer의 Home Branch에 귀속한다. 등록 시점·금액 확정 시점·대상 월말 또는 조회 시점의 소속으로 대체하지 않는다. 지급 금액·월 정산 한 번 합산·기존 관리 권한은 유지한다. 금액 산정·발생 시점/소속 확인 예외·정산 월·비용 보고 공개/집계 상세는 관련 OPEN이다.

2026-10-11 확정 월의 누락된 지원 수업 외 추가실적: 이미 확정된 발생 월의 누락된 지원 수업 외 Additional Performance는 해당 Trainer·월 정산의 확정 해제 → 누락 실적 등록 → 같은 발생 월 재확정으로 반영한다. 이전 확정본은 보존하고 재확정 결과와 구분한다. 확정 상태에 직접 추가하여 이전 확정본을 덮어쓰거나 등록 월/다른 월로 이월하지 않는다. 기존 금액 필수/양수·등록 권한/감사·발생 당시 Home Branch 비용 귀속을 유지하고 재확정 시 기존 확정 조건을 검증한다. 이 흐름의 해제/재확정은 관리 범위 안 본인 건도 별도 승인 없이 허용한다(2026-10-11).

2026-10-11 지원 수업 외 추가실적 정산 월: 회원 유지 등 지원 수업 외 Additional Performance는 실제 실적이 발생한 월의 Trainer 월 정산에 귀속한다. 9월에 발생한 실적을 10월에 등록해도 9월분이며 등록 월이나 금액 입력 월로 이월하거나 관리자가 반영 월을 임의 선택하지 않는다. 같은 실적을 9월·10월에 중복 합산하지 않는다. 금액 필수/양수·기존 관리 권한/감사·발생 당시 Home Branch 비용 귀속은 유지한다. 확정된 발생 월 후등록·발생 시점 식별/월 경계·소급 기간·정정/취소 등은 별도 OPEN이며 확정본에 자동 합산하지 않는다.

2026-10-11 지원 수업 외 추가실적 양수 금액 요건: 회원 유지 등 지원 수업 외 Additional Performance의 등록 금액은 0원보다 큰 양수만 허용한다. 0원과 음수 입력은 등록을 거부하며, 사유를 남겨도 0원으로 등록할 수 없다. 기존대로 내용과 금액을 함께 입력해야 등록이 완료되고 누락 금액을 자동으로 채우지 않는다. 지원 수업의 사유 필수 0원 허용과 기존 권한·감사·비용 귀속은 유지한다. 상한액·정밀도/금액 표현·정산 월·정정/취소 등은 관련 OPEN이다.

2026-10-11 지원 수업 외 추가실적 등록 완료 요건: 회원 유지 등 지원 수업 외 Additional Performance는 권한 있는 관리자가 실적 내용과 금액을 함께 입력해야 등록이 완료된다. 금액 미입력 요청은 등록을 완료할 수 없으며, 금액 없는 실적을 먼저 등록하고 나중에 금액을 입력하는 흐름은 v1에 두지 않는다. 누락 금액을 자동으로 0원이나 계산식 결과로 대체하지 않는다. 지원 수업의 기록/차감 후 금액 저장 흐름은 유지한다. 기존 권한·감사·비용 귀속과 금액 제약/정산 월/정정·취소의 남은 OPEN은 유지한다.

2026-10-11 추가실적 등록 흐름: v1 추가실적은 권한 있는 관리자의 직접 등록만 지원하고 Trainer의 시스템 내 별도 신청·승인/반려 흐름은 두지 않는다. Trainer는 실적 내용을 관리자에게 전달하며 기존 Master Admin/Branch Admin이 허용된 관리 범위에서 입력한다. 기존 관리자·Trainer 겸임자의 관리 범위 안 본인 등록·승인 생략·감사를 유지한다. Trainer의 PT 진행 기록 등록은 계속 지원한다. 남은 입력 제약·금액 확정 시점·정산 월·정정/취소 등은 관련 OPEN이다.

2026-10-11 지원 수업 외 추가실적 금액 산정: 회원 유지 등 지원 수업 외 Additional Performance의 금액도 권한 있는 관리자가 실적 건별로 직접 입력한다. v1에서 유형별 사전 금액·산식으로 자동 계산하는 방식을 채택하지 않으며 일반 RATE/FIXED_AMOUNT 계산 결과로 입력액을 대체하지 않는다. 기존 관리자 등록 범위·본인 건 허용/별도 승인 없음·감사와 발생 당시 Home Branch 비용 귀속은 유지한다. 금액 확정 시점·0원/미입력·입력 제약·정산 월·정정/취소 등은 관련 OPEN이다.

2026-10-11 지점별 비용 보고서 조회 권한: v1 지점별 비용 보고서는 Master Admin만 Organization 범위에서 조회한다(2026-10-11 사용자 확정). Branch Admin은 자기 지점 비용 합계도 이 보고서로 조회할 수 없으며 Master 권한 없는 Operator·Trainer도 불가하다. Branch Admin의 현재 자기 Home Branch 소속 Trainer 해당 월 정산 전체 금액·구성 내역 조회는 타 지점 지원 보상까지 포함하여 유지한다. 비용 귀속·지급액·기존 등록/정정/확정 권한은 유지하며 보고서 항목·대상 월·집계/완전성·버전 등 남은 상세는 MB-006/010 OPEN이다.

Monthly Settlement = 해당 월 적용 Base Salary + 유효한 Session Payment 합계 + 유효한 Additional Performance 합계다. Trainer·대상 월·적용 기본급·Session 수·Session Payment 합계·추가실적 내역/합계·월 정산 합계를 구분한다. 2,500,000원 + 1,200,000원 + 150,000원 = 3,850,000원이며 여러 지점 수업으로 동일 월 기본급을 중복 가산하지 않는다. 타 지점 수업의 보상 전체는 Additional Performance로 반영하며 일반 Session Payment를 별도로 합산하지 않는다(MB-009 CLOSED, 2026-10-10 사용자 정정).

일반 Session Payment의 Rate/Fixed Amount는 관리자 저장 완료 이후 신규 등록 Session부터 적용하며 정상 등록 시 지급액을 확정한다. 타 지점 지원 수업은 진행 기록·Pass 차감 후 관리자의 건별 수동 금액 저장 시 보상을 확정한다. 미입력은 확정된 0원과 구분·추적하고 해당 Trainer·월 정산 확정을 차단한다. 월 귀속·나머지 확정 조건·마감/정정 절차는 관련 OPEN이다. FIXED_AMOUNT 우선·동일 Type FIFO·RATE Session별 1,000원 올림·FIXED_AMOUNT 설정값 사용을 유지한다. 현재 설정으로 과거 확정 Session Payment와 확정 정산의 기본급/합계를 자동 변경하지 않는다. 기본급 일할·근무일수·휴직 자동 계산은 제외한다.

Desktop/Tablet/Smartphone 핵심 업무 Responsive Web은 v1이다. Member 로그인·일정 조회·예약/취소·Mobile App은 Future Scope이며 자동 승격하지 않는다. 가계부·락커·수동 매출·고정 거래·계약/출석/고객 결제/환불/회원권/상담·migration tooling 제외도 유지한다. 추가실적은 Trainer 인센티브이며 기존 수동 매출과 동일한 AS-IS 사실로 취급하지 않는다. 독립 고객사 SaaS 범위는 추가하지 않는다.

## 문서 안내

| 문서 | 역할 |
| --- | --- |
| [Product Goal](product-goal.md) | 운영 목적·가치·AS-IS 경계 |
| [Product Decisions](product-decisions.md) | PD-001–027: 26 CLOSED / PD-021 OPEN |
| [Scope](scope.md) | v1/Future/제외와 수용 경계 |
| [Users and Roles](users-and-roles.md) | 최종 세 항목 권한표·단일 Branch Scope |
| [Requirements](requirements.md) | PR-001–031 및 추가실적 요구 |
| [Business Rules](business-rules.md) | BR-PAY-001–016, BR-OPS-001 및 문서 사례 |
| [User Scenarios](user-scenarios.md) | 로그인·PT·보상 설정·정산·타 지점 흐름 |
| [Non-functional Requirements](non-functional-requirements.md) | Backend 권한·감사·보존·Responsive |
| [Open Questions](open-questions.md) | 22 OPEN / 8 CLOSED; MB-007·MB-009·BR-011 및 UX-001 해결, 복합 질문의 남은 부분 분리 |
| [Validation Needed](validation-needed.md) | AS-IS 8 OPEN / 12 REFERENCE-ONLY 상태 보존 |
| [AS-IS → TO-BE Mapping](as-is-to-be-mapping.md) | 기존 F01–59/H01–04 63개 추적과 새 사용자 결정 구별 |
| [Architecture Handoff](architecture-handoff.md) | 공통 검토 입력과 상세 결정 게이트 |

## 해결된 부분과 남은 결정

2026-09-17에는 MB-001/002/003/004/007의 단일 소속·발급·교차 이용 가능·단일 관리자 Scope·공통 Catalog와 BR-009의 기본급 도입/합산 질문 부분을 해결했다. 잔여 질문이 있으므로 해당 ID 전체는 OPEN이다. 당시 BR-003/004/005/006 CLOSED를 유지하고 PD-001/004/006/009/012/022를 갱신하며 PD-027을 추가했다. 2026-10-10에는 MB-009와 BR-011을 추가로 CLOSED 처리했다. 2026-10-12에는 공통 PT 상품 생성·수정을 Master 전용으로 확정하여 MB-007을 추가 CLOSED 처리했다.

타 지점 보상 구성의 해결 내용과 지급액·권한·귀속에 영향을 주는 주요 OPEN은 다음과 같다.

- MB-009는 2026-10-10 CLOSED: 사용자 정정에 따라 타 지점 수업 보상 전체를 Additional Performance로 처리한다. 일반 Session Payment와 중복 합산하지 않는다. 추가실적 상세 BR-013과 귀속/공개 MB-010/006은 계속 OPEN이다.
- BR-013: 관리자 직접 등록 역할·Home Branch 대상 기준·Branch Admin의 본인이 아닌 소속 Trainer 직접 등록 시 별도 Master 승인 없음·관리 범위 안 본인 직접 등록 및 본인 건 별도 승인 없음·타 지점 지원 수업 금액의 관리자 건별 수동 입력·진행 기록/차감 후 금액 저장 시 보상 확정·미입력과 확정 0원 구분 및 추적·미입력 지원 수업이 남은 해당 Trainer·월 정산 확정 차단·사유 필수의 지원 수업 0원 확정 허용·월 정산 확정 전 지원 수업 금액 수정의 관리자 대상 범위/본인 건 허용/변경 이력·본인 건 포함 수정의 별도 승인 없음/저장 즉시 반영·해당 모든 수정의 변경 사유 필수·지원 수업 금액 오류의 해당 월 확정 해제/정정/재확정과 이전 확정본 보존·지원 수업 정정 시 Master Organization/Branch Admin 대상 Trainer Home Branch 기준 해제·재확정 권한·해당 Branch Admin 정정의 별도 Master 승인 없음·지원 수업 정정의 확정 해제 사유 필수 기록·지원 수업 정정의 처리 시점 현재 Home Branch 인가 기준과 지원 수업 외 추가실적의 관리자 건별 수동 금액 입력 및 v1 관리자 직접 등록만 지원/Trainer 별도 신청·승인 제외 및 지원 수업 외 최초 등록의 금액 필수·양수만 허용/0원·음수 거부·지원 수업 외 실적의 발생 월 정산 귀속·확정된 해당 Trainer/월 해제 후 누락 등록/재확정·이전 확정본 보존은 확정. Operator의 남은 업무 권한·지원 수업 외 실적의 금액 외 정보 수정/취소의 소속 이동 시 권한 기준 시점·지원 수업 외 추가실적의 남은 입력 제약·금액 미입력 건의 추적 표현·정정 연동·연계 상세·나머지 정정/취소 및 남은 마감 이후 처리는 OPEN.
- BR-009: 최초 확정의 Master Organization 전체/Branch Admin 처리 시점 Trainer 현재 Home Branch 범위·본인 건 포함·별도 Master 승인 없음은 2026-10-11 확정. 추가 통계·나머지 확인/마감/확정 조건·남은 정정 절차는 OPEN.
- BR-012: 기본급 적용 시작 월의 관리자 지정·미확정 과거 월 지정 허용·수동 지정 없는 기존 미확정 정산 자동 반영·확정 월 기본급 오류의 해제/정정/재확정과 이전 확정본 보존·해당 정정의 현재 Home Branch 관리자 권한과 별도 Master 승인 없음·확정 해제/해당 월 기본급 수정 사유 필수·오류 정정의 해당 월 한정 및 현재/미래 설정·다른 월 유지·입퇴사/휴직 월의 관리자 수동 금액 지정·이후 일반 설정 변경에도 수동 지정액 유지·미확정 월 최초 수동 지정/수정 모두 사유 필수·현재 Home Branch 관리자 범위의 직접 수동 지정/수정(본인 포함·별도 Master 승인 없음)까지 확정. 2026-10-11에는 사유 필수의 월별 수동 기본급 0원 허용도 확정. 미리 등록할 수 있는 미래 적용 시작 월의 범위·월별 수동 지정 금액의 나머지 입력 제약은 OPEN.
- MB-010/006: 현재 소속 Trainer의 해당 월 정산 전체 금액·구성 내역 공개(타 지점 지원 보상 포함), 일반 지급·지원 수업 보상의 실제 Performed Branch 비용 집계, 이동월 기본급의 월말 Home Branch 적용액 전액 귀속, 지원 수업 외 추가실적의 발생 당시 Home Branch 귀속은 2026-10-11 확정. v1 지점별 비용 보고서 Master 전용 조회도 확정. 귀속의 남은 사실 확인 예외·보고서 항목/상세 수준·대상 월·집계/완전성·버전과 조회 대상 월·이전 확정본/세부 계산 근거·감사 공개의 잔여 질문은 OPEN.
- MB-001–005/007/008: 이동·구체 교차 업무 접근·관리 담당자의 정정 Scope·Operator/계정 위임·Branch Admin 상품 관리·Branch 수명.

기존 Pass 상태/사용·정정/취소·날짜·입력·개인정보/보존·운영 품질 OPEN도 유지한다. 상품 변경의 기존 Pass 적용은 발급 당시 조건 유지로 해결됐다(BR-011 CLOSED). 구체 상태 집계는 각 문서의 실제 Status 기준이다. Product 결정으로 AS-IS 검증을 완료 처리하지 않는다.

확정 조직·관계·권한 경계·감사·정합성·보존·Responsive/Future 제약으로 공통 Architecture 검토가 가능하다. 위 미결정에 의존하는 상세 설계/구현은 사용자 결정 전 확정하지 않는다. DB/API·인증·기술 스택·snapshot/history 방식은 선택하지 않았다.

## 이번 개정 문서 검증

아래는 요구사항·권한표·업무 규칙의 대조 결과다. 애플리케이션 테스트나 운영 검증이 아니다.

| CASE | 문서상의 기대 결과 | 근거 |
| --- | --- | --- |
| 1 | Master Admin 전체 Trainer 세 항목 조회/변경 허용, 별도 승인 없음, 감사 | PR-007; BR-PAY-010; 역할표 |
| 2 | 수원점 Admin이 수원 소속 Trainer 세 항목 변경 허용, 승인 없음, 감사 | SC-012; 역할표 |
| 3 | 강남점 지원 수업 이력만으로 수원 소속 Trainer 설정 접근 불가 | PR-030; BR-PAY-010; 역할표 |
| 4 | 관리자 권한 없는 Operator·Trainer는 본인 포함 불가. 관리자·Trainer 겸임자는 관리 범위 안이면 본인 세 항목 허용, 범위 밖이면 불가 | NFR-001; 역할표; ARCH-001 |
| 5 | 타 지점 수업에도 Home Branch 유지, 실제 Performed Branch 식별 | PR-005/008; BR-OPS-001 |
| 6 | 허용 Pass 타 지점 이용 가능, 발급 지점 차이만으로 일률 차단 없음; 업무 권한 검증 필요 | PR-003/030; MB-003/005 |
| 7 | 2,500,000 + 1,200,000 + 150,000 = 3,850,000원; 기본급 중복 없음 | PR-010; BR-PAY-016 |
| 8 | 현재 세 설정 변경으로 과거 확정 지급·월 정산 자동 변경 없음 | PR-007/010; BR-PAY-009/014/016 |
| 9 | 타 지점 수업 보상 전체는 Additional Performance로 반영, 일반 Session Payment와 중복 합산 없음. Branch Admin의 본인이 아닌 소속 Trainer 직접 등록은 Master 승인 없음. 관리 범위 안 본인 직접 등록 및 별도 승인 없음. 지원 수업은 금액 없이 기록·차감을 먼저 완료하고 관리자 건별 금액 저장 시 보상 확정. 미입력은 확정 0원과 구분·추적. 미입력 지원 수업이 남으면 해당 Trainer·월 정산 확정 차단. 사유를 기록해 명시적으로 확정한 지원 수업 0원은 미입력에서 제외. 월 확정 전 금액 수정은 Master Organization 전체/Branch Admin Trainer Home Branch 기준으로 본인 포함 허용하며 별도 승인 없이 저장 즉시 반영, 변경 전후 금액·사유·수정자·시점 보존. 해당 모든 수정에 변경 사유 필수. 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. Branch Admin의 위 정정은 별도 Master 승인 없이 처리. 확정 해제는 사유 필수이며 사유·해제자·시점 보존. 과거 지원 수업 보상 정정·해제·재확정의 Branch Admin 인가는 처리 시점의 Trainer 현재 Home Branch 기준. 나머지 정정/취소·월 귀속은 미정 | MB-009 CLOSED; BR-013; MB-010; SC-016 |
| 10 | FIXED_AMOUNT 우선/FIFO/RATE 1,000원 올림/FIXED_AMOUNT 설정값 유지 | BR-PAY-003–006/013; CASE I–K |

검증 완료: 13개 Product 문서 전체를 읽고 위 CASE 1–10을 요구사항·권한표·규칙에 대조했다. 활성 규칙 충돌 검색, 기존 ID 보존, 상대 링크/앵커 오류 없음, 63개 AS-IS 매핑, Status 집계 및 AS-IS 검증 상태 불변을 확인했다. 작업 전후 실제 원문 diff와 저장소 파일 해시로 Product 13개 파일만 변경되고 삭제/외부 변경이 없음을 확인했다. docs/는 기존부터 Git 미추적 상태라 tracked diff가 비어 있어 원문 비교를 병행했다. 문서 신규 생성·애플리케이션 테스트·운영 검증·Architecture 설계는 수행하지 않았다.
