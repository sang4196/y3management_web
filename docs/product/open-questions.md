# Open Questions / 후속 TODO

현재 후속 정책: [2026-10-13 AB 승인](product-decisions.md#review-20261013-ab-batch)의 AB1–AB6 모두 1번이다. 월 정산 대상은 적용 기본급/월별 지정·유효 PT/보상대기 지원 PT/추가실적 등으로 자동 선정하며, 한 달 전체 Trainer 비활성·명시 기본급0·무활동·정정 대기 없는 경우 새 정산 확정 의무에서 제외한다. 기존 이력/미완료와 비활성만으로 기본급을 자동0으로 바꾸지 않음은 유지한다. 후속 reset 링크30분·운영 관리자 비밀번호 뒤 Passkey·업무책임자 승인/별도 운영담당자 비상 복구·Chrome/Edge/Safari 최신2개 안정 주버전을 선택했다. K3/X1 첫 IAM/별도 구현 지시·구체 계약 PROPOSED와 22 OPEN/8 CLOSED는 유지한다.

승인된 Product Decision을 다시 OPEN으로 돌리지 않고 남은 세부사항을 분리한 목록이다. 2026-10-10 현재 24개 OPEN / 6개 CLOSED다. BR-003/004/005/006에 더해 MB-009와 BR-011이 사용자 결정으로 CLOSED되었으며 ARCH-001/002는 부분 해결 상태로 OPEN을 유지한다. 복합 질문의 해결된 부분과 남은 부분을 분리한다. 공통 제약을 바탕으로 Architecture 검토는 가능하지만 신규 Branch 관련 상세 설계 확정에는 사용자 결정이 필요하다. 남은 업무 질문은 해당 상세 설계·구현 확정 전, 운영 질문은 실운영 전에 확인한다. [Architecture 인계](architecture-handoff.md). 이 문서는 질문과 검토 시점만 정하며 Architecture·데이터 구조·기술을 설계하지 않는다. BR은 미래 업무 규칙, ARCH는 후속 설계 질문, UX는 입력 편의, OPS는 운영 전환, LEGAL은 별도 개인정보·보존 검토다. 현재 사실 확인 VAL과 구분한다.

<a id="br-001"></a>
## BR-001. PT Pass 상태·시작·종료 규칙

Question / TODO: 남은 상태 전이/종료 조건·시각 정밀도/동시 순서·만료/해제의 역사 사실 판정·PT 취소 복원/조정과 사용 상태 연계 및 다른 상태 조합/최소 계약을 구체화한다. U1로 수동 만료 Pass도 기존 Member 현재 Home 관리자 Scope/실제 활성 대상 조건으로 담당 교체 가능하고 만료 상태/잔여·과거 이력은 유지함이 확정됐다. T1/T2 시스템 신규 발급 완료 시각·과거 날짜 입력/소급 발급 v1 제외·별도 시작일 없음과 만료일/자동 만료 없음·수동 만료/해제/잔여 보존·만료 전 늦은 등록·M1 발급 오류 처리/별도 발급 취소 v1 제외·M2 만료 담당 조회는 유지한다. 수동 만료 상태 자체의 담당 교체 허용을 재질문하지 않는다.

Related decisions / requirements: PD-007/011; PR-003. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Architecture 착수 가능; 관련 업무 상세 설계·구현 확정 전

확정된 경계: 별도 만료일/유효기간과 시간 경과 자동 만료는 두지 않으며 관리자 수동 만료와 같은 Pass의 만료 해제를 지원한다(2026-10-12 사용자 확정, BR-OPS-004). 만료/해제 자체는 잔여를 유지하며 사용 차단/해제를 구별한다. 동일 현재 관리 Scope·사유/이력·감사와 종료 Pass/과거 수업/정산 이력 보존을 적용한다. 해제 후에도 잔여 > 0 등 다른 사용 조건을 충족해야 한다. 수동 만료 전 실제 수업 당시 사용 가능했던 Pass의 지연 등록은 현재 만료 상태를 유지하며 기존 권한·정산·현재 잔여 조건 충족 시 허용한다. 상태명/저장 방식·다른 종료 사유의 잔여 처리·시점/만료·해제 이력 사실 판정 및 별도 취소 복원/조정과 사용 상태 연계는 여전히 후속이다. 상품 판매 중단은 새 Pass 발급만 차단하며 기존 Pass의 사용 상태/잔여는 유지한다(2026-10-12 사용자 확정, BR-PAY-001). 개별 수동 만료 등 기존 Pass의 사용 불가 사유를 면제하지 않는다.

Status: OPEN

2026-10-12 사용자 확정(유효기간 질문의 직접 답변): “만료일은 따로 없지만 관리자가 만료 처리가능하도록.” 자동 만료일 없이 관리자 수동 만료 업무를 지원한다. 기존 이력 보존 및 수동 변경의 사유/감사 원칙을 동일 적용한다(사용자 일관성 지시). 수동 만료의 관리 지점 기준·잔여/정정/재개·과거 수업 연계와 구체 상태 표현은 잔여 게이트다(BR-OPS-004).

2026-10-12 사용자 확정(지점 관리자의 만료 범위 질문의 1번): Master Organization 전체/Branch Admin 현재 관리 Branch=Pass Issued Branch로 수동 만료를 인가한다. Member/Trainer 소속이나 Performed Branch는 기준이 아니며 타 지점 이용 사실로 만료 권한이 확대되지 않는다. 관리 지점 기준 질문은 해결됐고 잔여/정정·재개/과거 수업 연계·상태 표현은 잔여다(BR-OPS-004).

2026-10-12 사용자 확정(수동 만료 시 잔여 처리 질문의 1번): 잔여 횟수는 유지하고 사용만 차단하며 5회 잔여는 만료 후에도 5회다. 만료 자체로 소멸 차감/0 덮어쓰기/수업 사용 처리를 하지 않고 양수 잔여라는 이유로 자동 재개하지 않는다. 수동 만료의 잔여 처리 질문은 해결됐고 해제/재개·과거 수업/취소 복원 연계·다른 종료 사유는 후속이다(BR-OPS-004).

2026-10-12 사용자 확정(잘못된 만료 복구 질문의 1번): 같은 Pass의 수동 만료 해제를 허용한다. 만료와 같은 Master Organization 전체/Branch Admin 처리 시점 현재 관리 Branch=Issued Branch 범위에서 사유/전후 상태·Actor/시점 이력과 감사를 남기며 기존 만료 사실은 보존한다. 기존 직접 처리 원칙을 동일 적용하고 별도 승인 없이 해제한다. 해제 자체로 잔여/새 Pass를 만들지 않으며 잔여 5회는 5회로 유지한다. 나머지 사용 조건을 충족하면 다시 사용 가능하나 잔여 0 등 다른 차단 사유는 면제하지 않는다. 해제 허용 질문은 해결됐고 과거 수업·취소 복원/조정 연계 및 상태/저장 방식은 후속이다(BR-OPS-004).

2026-10-12 사용자 확정(만료 전 수업 늦은 등록 질문의 1번): 실제 수업이 수동 만료 전에 진행됐고 당시 Pass가 사용 가능했다면 현재 만료여도 기존 권한·정산·현재 잔여 조건 충족 시 별도 해제 없이 늦게 등록할 수 있다. 후보 내 기존 FIXED_AMOUNT 우선/FIFO로 선택한 Pass의 현재 잔여에서 1회 차감하고 현재 만료 상태·이력은 유지한다(만료/5회→만료/4회). 만료 전 수업 지연 등록 허용 질문은 해결됐으며 다른 종료 조건·시점/이력 사실 판정과 별도 취소 복원/조정 연계는 후속이다(BR-PAY-006, BR-OPS-003/004).

확인 주체: 사용자/업무 책임자와 해당 후속 단계 담당자. 답변·기한은 미정.

2026-10-12 후속 확정: 기존 Pass에서 담당 교체 가능/잔여·발급 조건/과거 이력 유지(BR-OPS-008). 종료/만료/취소 등 모든 상태의 교체까지 일괄 승인한 것은 아니며 대상 상태·과거 사실 정정 등 상세는 후속이다. 교체 자체로 상태를 재개하거나 횟수를 복원/추가하지 않는다.

2026-10-12 사용자 확정(잔여 0회인 이용권의 담당 교체 질문의 1번): Remaining이 0인 기존 Pass도 Assigned Trainer를 교체할 수 있다. 잔여를 모두 사용해 이용이 끝난 Pass도 포함한다. 같은 Pass에서 담당 A를 B로 바꾸며 Remaining 0·발급 조건/Issued Branch·과거 실제 수행 Trainer/PT 기록·확정 지급/정산 이력은 유지한다. 새 담당 B는 기존 현재 담당 관계에 따른 Member 조회·응대를 이어갈 수 있다. 기존 Master Organization 전체/Branch Admin 처리 시점 Member 현재 Home Branch 권한과 같은 Organization의 다른 지점 Trainer도 대상 허용 원칙은 유지한다(BR-OPS-005/008, PD-007, PR-003/029/030).

후속 게이트 갱신: 잔여 0으로 이용을 마친 Pass의 담당 교체/새 담당 Member 조회만 추가 해결됐다. 잔여 0 유지·현재 Caller/Member/Organization/담당 관계 검증·선택 필터의 Member 전체 Pass 기준과 실제 PT 잔여 > 0 조건은 유지한다. 수동 만료/취소 등 다른 종료 사유의 담당 관계/교체와 과거 사실/최소 정보·저장/응답/UoW·동시성은 계속 OPEN이다.

2026-10-12 사용자 확정(잔여가 남은 담당 이용권이 있는 Trainer의 비활성화 질문의 1번): 잔여가 남은 담당 PT Pass가 있어도 Trainer 비활성화를 허용하며 기존 Assigned Trainer 정보는 유지한다. 비활성화 전에 모든 Pass를 다른 Trainer에게 교체하도록 요구하지 않고 자동 담당 해제/재배정도 하지 않는다. 이후 필요할 때 권한 있는 관리자가 BR-OPS-008의 기존 조건/Scope로 담당을 교체한다(BR-OPS-014, PD-007/011, PR-003/005, NFR-001/004, ARCH-001/002, MB-001/003/005, BR-001).

기존 담당 정보 유지와 별도 담당 교체가 해결됐으며 비활성 Trainer의 접근은 계속 차단한다. Member 현재 Home Branch 기반 담당 교체와 Trainer Home Branch 기반 비활성화 권한을 구분하고 잔여/발급 조건·과거 PT/보상을 유지한다. 다른 상태별 교체/사용 조건·개별 지원/재활성화·비활성 상태의 과거 PT 예외 및 구체 저장/현재 인가·UoW/동시성은 후속이다. 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 사용자 확정(담당 Trainer를 새로 지정할 때의 조건 질문의 1번): PT Pass의 담당 Trainer를 새로 지정할 때는 실제 활성 Trainer만 허용한다. 기존 Pass의 담당 교체 및 허용된 새 Pass 발급 흐름에서 담당을 최초 지정하는 경우 모두 적용하며 비활성 Trainer를 미리 배정하지 않는다(BR-OPS-008/014, PD-007, PR-003/005/029/030, NFR-001, ARCH-001, MB-001/003/005, BR-001).

새 지정 대상의 활성 필요조건은 해결됐으며 같은 Organization의 타 지점 허용/기존 행위별 Actor·Scope, 이후 비활성화된 기존 담당 정보 유지·접근 차단을 적용한다. 최초 담당 필수는 해결됐고 나머지 Pass/계정/Branch 상태 조합·최소 선택 정보, 재활성화·개별 지원/비활성 전 수업 예외 및 실제 현재 사실 검증/저장/UoW·지정·비활성화 경합은 후속이다. 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 사용자 확정(비활성화 전 진행했지만 누락된 PT 수업 등록 질문의 1번): Trainer 비활성화 전에 실제로 수행한 미등록 PT 수업은 관리자가 대행 등록하는 경로를 허용한다. 대상 Trainer의 비활성 상태를 유지하며 잠시 재활성화/본인 로그인·담당 재배정을 선행 요구하지 않는다. 실제 수행 Trainer·실제 수업일과 기존 Pass 잔여/정산 조건을 그대로 적용한다(BR-OPS-015, PD-008/011, PR-008/029/030, BR-OPS-003/008/014, BR-PAY-006/011/012).

관리자 대행 경로와 Master Organization/Branch Admin 실제 Performed Branch Scope는 해결됐다. 현재 인가 검증·비활성화 전 실제 수업/담당/소속 사실·시점/확인 불가·최소 선택 정보/사유·증빙과 구체 계약/저장/UoW·경합은 후속이다. 비활성/현재 담당 유지·실제 수행자/수업일·기존 Pass/생성 시점 보상/진행 월 정산·민감 설정 접근 제한을 적용한다. 비활성 Trainer 본인 직접 등록/회원 조회 예외가 아니며 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 일괄 승인 반영: B3/B4/B6: 새 Pass는 활성 담당 지정 필수/상품 Session Count 최초 부여이며 비활성 지점 새 발급은 차단한다. 기존 Pass/잔여·소속/이력은 보존한다. 나머지 시작/상태/취소/복원과 비활성 지점 결합 조건은 후속이다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch). 이 복합 OPEN의 다른 미결정 항목은 유지한다.

2026-10-12 C 일괄 승인 반영: C13: 사용 가능·잔여 소진·수동 만료 Pass 조정 허용. 소진 후 추가는 다른 조건 충족 시 재사용 가능하고 수동 만료는 추가 후에도 유지/별도 해제한다. CANCELLED 등 나머지 상태/비활성 지점 조합은 후속이다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 G 일괄 승인 반영: G3/G4: 비활성 Issued/Home Branch만을 이유로 기존 Pass의 다른 활성 지점 사용을 차단하지 않는다. 기존 가용/잔여/담당·지원 조건과 수동 만료 등 다른 차단은 유지한다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). 다른 상태/신규 배정·역사 사실/구체 계약·경합 등 나머지 게이트로 이 복합 OPEN은 유지한다.

2026-10-12 J 일괄 승인 반영: J3로 Member 자체 비활성이 기존 Pass 잔여/조건/상태를 자동 변경하지 않으며 새 발급/비활성 기간 실제 수업은 차단됨을 확정했다. 같은 Member 재활성화 후에도 잔여 > 0/개별 수동 만료 등 기존 독립 사용 조건이 필요하다. 다른 Pass 상태·시작/종료/이력 사실/경합 계약은 후속이다. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch). 이 복합 OPEN의 나머지 항목은 유지한다.

2026-10-13 M1=1: 잘못 발급한 미사용 Pass는 기존 수동 만료로 잔여/원본을 보존하고 기존 정상 발급 권한/조건으로 올바른 Pass를 새로 발급한다. 별도 Pass 발급 취소 기능은 v1 제외다. 과거 PT 취소/복원과 다른 업무이며 만료/해제의 기존 인가·사유/감사/잔여·늦은 등록 조건을 유지한다. 이전 취소 Pass/CANCELLED의 구현 게이트 표현을 별도 발급 취소 v1 요구로 사용하지 않는다. 나머지 역사 사실·상태/조정/단계 계약으로 이 복합 OPEN은 유지한다. BR-OPS-025/004; PR-003·scope; V-106 예정; [M 승인](product-decisions.md#review-20261013-m-batch).

2026-10-13 M2=1: 수동 만료 Pass도 현재 유효 Trainer의 담당 Member/허용 전체 전화번호 조회 근거로 인정하며 만료만으로 조회 관계를 끝내지 않는다. Backend 현재 Caller/Organization·담당 또는 개별 지원 인가, 담당 변경/Trainer 비활성·계정/역할/인증 철회 제한과 실제 PT 사용/만료 전 늦은 등록·전체 잔여 필터를 유지한다. 새 개인정보/다른 Pass/PT/보상·내보내기/수정 권한이나 수동 만료 Pass의 담당 교체 허용은 추가하지 않는다. 해당 조회 부분만 해결됐고 나머지 교체/역사 사실/공개/계약으로 이 복합 OPEN은 유지한다. BR-OPS-005/004; PR-002/003/029/030·NFR-001/005; V-107 예정; [M 승인](product-decisions.md#review-20261013-m-batch).

2026-10-13 T1/T2=1 부분 해결: Pass 발급은 시스템 신규 발급 완료 시각 기준이며 과거 발급 날짜 입력/소급 발급은 v1 제외다. 별도 사용 시작일 없이 발급 시점부터 기존 잔여/상태·인가 조건을 적용한다. 실제 구매가 먼저여도 시스템 발급 전 수업에는 그 Pass를 사용하지 않는다. 기존 실제 수업 당시 발급된 후보/FIXED_AMOUNT 우선/FIFO·수동 만료/해제/만료 전 늦은 등록·현재 잔여/정산/보상·원본 보존은 유지한다. 나머지 시각/역사 사실·상태/취소 복원/담당 교체·최소 계약 때문에 Status는 OPEN이다. [T 승인](product-decisions.md#review-20261013-t-batch); BR-OPS-031; V-120/121 미구성·미실행.

2026-10-13 U1=1 부분 해결: 수동 만료 Pass의 담당도 기존 Master Organization/처리 시점 Member 현재 Home Branch Admin 범위에서 같은 Organization 실제 활성 Trainer로 교체할 수 있다. 만료 상태/잔여·발급 조건/시각·과거 수행/지급·정산을 보존하고 자동 만료 해제/횟수 부여·새 수업 사용은 허용하지 않는다. 기존 감사·M2 현재 담당 조회/이전 담당 다른 관계 없는 일반 조회 비복원·독립 관리자 Scope를 유지한다. 다른 상태/역사 사실·최소 선택/인가 계약/경합 때문에 Status는 OPEN이다. [U 승인](product-decisions.md#review-20261013-u-batch); BR-OPS-008/005; V-122 미구성·미실행.

<a id="br-002"></a>
## BR-002. Pass 횟수 부여·차감·조정

Question / TODO: 최초 상품 횟수 부여·발급 횟수 초과 추가와 C12/C13 음수 잔여 금지·사용 가능/소진/수동 만료 조정은 해결됐고 수동 추가/감소의 나머지 목적·수량 상한·PT 진행 취소 복원/사용 상태 연계와 상태 조합은? M1의 미사용 발급 오류는 수동 만료/잔여 보존 후 정상 새 발급이며 별도 Pass 발급 취소 기능은 v1 제외다. 과거 수업의 실제 시점 발급 Pass 조건·만료 전 실제 수업 지연 등록의 현재 잔여 차감/만료 유지와 기존 Issued Branch 관리자 조정 Scope·사유/이력/감사는 유지한다. 발급/시작 정보의 의미·역사 사실 확인/정정·계약은 BR-001/ARCH-003과 연결한다.

Related decisions / requirements: PD-007/008/010; PR-003/008/009. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Architecture 착수 가능; 관련 업무 상세 설계·구현 확정 전

확정된 경계: BR-PAY-006에 따라 동시에 사용 가능한 FIXED_AMOUNT Pass를 RATE Pass보다 먼저 차감한다. 동일 Payment Type에서는 FIFO이며 이 순서와 1회 Session 단위는 확정이다. 따라서 기존 일반 우선 차감은 계승하지 않는다.

Status: OPEN

2026-10-12 사용자 확정(과거 수업 이용권 범위 질문의 1번): 실제 수업 당시 발급돼 있던 Pass만 후보이며 이후 발급된 것은 제외한다(BR-PAY-006). 발급 시점 조건과 나머지 사용 조건을 충족한 후보 안에서 FIXED_AMOUNT 우선/FIFO를 적용한다. 발급 시점 선택은 해결됐으며 상태/잔여 등 나머지 이용 조건·발급 사실 확인/정정·시각 정밀도 등은 후속이다.

2026-10-12 사용자 확정: 수동 만료 전 실제 수업 당시 사용 가능했던 Pass는 현재 만료 상태여도 늦은 등록 후보가 될 수 있다. 기존 PT 권한·정산·현재 잔여 조건과 FIXED_AMOUNT 우선/FIFO로 선택하여 현재 잔여 1회 차감/현재 만료 유지하며 사전 만료 해제는 요구하지 않는다. 나머지 횟수 조정/취소 복원·다른 종료 조건·시점/이력 사실 판정은 OPEN이다(BR-PAY-006, BR-OPS-003/004).

확인 주체: 사용자/업무 책임자와 해당 후속 단계 담당자. 답변·기한은 미정.

2026-10-12 사용자 확정(이용권 횟수의 수동 조정 권한 질문의 1번): Pass 횟수의 수동 조정은 Master Admin의 Organization 전체 범위 또는 처리 시점 현재 관리 Branch가 해당 Pass의 Issued Branch인 Branch Admin에게 허용한다. 수원 발급/현재 강남 소속 Member의 이용권은 수원 Branch Admin 또는 Master가 조정하며, 강남 Branch Admin은 Member의 현재 소속만을 근거로 조정할 수 없다. 회원 소속이나 담당 Trainer가 바뀌어도 Issued Branch 기준은 유지한다. 이용권 수동 만료/해제와 같은 발급 지점 기준이며 담당 교체의 Member 현재 Home Branch 기준과 구별한다(BR-OPS-004/008/009, PD-007/010, PR-003/030).

관리자/지점 기준은 해결됐으며 기존 사유/전후 잔여·증감량/Actor·시점 이력·감사를 적용한다. PT 취소 복원의 기존 업무 권한/조건과 담당 교체의 Member 현재 Home Branch 기준은 유지한다. 수동 추가/감소의 목적·수량/상태·사용 재개/복원 연계 및 저장/계약/UoW·중복/동시성은 계속 OPEN이다(BR-OPS-009, BR-001/002/007, ARCH-003).

2026-10-12 일괄 승인 반영: B4/B5: 최초 횟수는 상품 Session Count, 별도 인가된 관리자 조정으로 최초 발급 횟수 초과 추가를 허용하고 기존 회당 지급식을 유지한다. 원본 발급 조건/과거 결과·조정 Scope/사유·이력은 유지한다. 음수/나머지 수량 한도·상태별 조정/복원 연계·UoW/경합은 남는다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch). 이 복합 OPEN의 다른 미결정 항목은 유지한다.

2026-10-12 C 일괄 승인 반영: C12/C13: 수동 감소 결과 Remaining < 0이면 거부하며 0까지는 허용한다. 사용 가능·소진·수동 만료 Pass 조정을 허용하고 수동 만료 자동 해제는 없다. 기존 Issued Branch 관리자 Scope/사유·이력/발급 조건을 유지한다. 나머지 상한/취소 상태·복원/경합은 후속이다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-13 M1=1: 잘못 발급한 미사용 Pass는 기존 수동 만료로 잔여/원본을 보존하고 기존 정상 발급 권한/조건으로 올바른 Pass를 새로 발급한다. 별도 Pass 발급 취소 기능은 v1 제외다. 과거 PT 취소/복원과 다른 업무이며 만료/해제의 기존 인가·사유/감사/잔여·늦은 등록 조건을 유지한다. 이전 취소 Pass/CANCELLED의 구현 게이트 표현을 별도 발급 취소 v1 요구로 사용하지 않는다. 나머지 역사 사실·상태/조정/단계 계약으로 이 복합 OPEN은 유지한다. BR-OPS-025/004; PR-003·scope; V-106 예정; [M 승인](product-decisions.md#review-20261013-m-batch).

<a id="br-003"></a>
## BR-003. RATE 계산 기준 — 해결됨

Status: CLOSED

Resolution: Product Price ÷ Product Session Count × 실제 수행 Trainer Rate의 결과를 Session별로 1,000원 단위 올림하여 확정한다. Product는 Payment Type만 지급 방식으로 정하고 지급 값은 Trainer 기준이다. [BR-PAY-001–003/008](business-rules.md). BR-005의 올림과 BR-006의 적용·확정 시점도 CLOSED이며 다시 미정으로 두지 않는다.

<a id="br-004"></a>
## BR-004. 서비스 PT 지급 — 해결됨

Status: CLOSED

Resolution: 서비스 PT Product는 FIXED_AMOUNT이며 수행 Trainer의 Fixed Amount를 지급한다. 서비스라는 이유로 0원 처리하지 않는다. [BR-PAY-004/005](business-rules.md). 서비스 표시의 구체적 표현은 후속 설계이며 지급 방식은 확정이다.

<a id="br-005"></a>
## BR-005. RATE 지급금액 처리 — 해결됨

Status: CLOSED

Resolution: RATE 계산 결과를 Session별로 1,000원 단위 올림한다. 12,300원 → 13,000원이며 FIXED_AMOUNT에는 적용하지 않는다. 정상 등록 시 계산·확정한 지급액을 월 정산에서 합산하고 재계산·재올림하지 않는다. [BR-PAY-013](business-rules.md#br-pay-013). 입력값의 허용 범위·정밀도와 누락 처리는 BR-010에 남긴다.

<a id="br-006"></a>
## BR-006. Trainer 설정 적용·Session Payment 확정 시점 — 해결됨

Status: CLOSED

Resolution: 권한 있는 관리자 저장 완료 이후 새로 등록되는 Session부터 새 Rate/Fixed Amount를 적용한다. 일반 Session Payment 적용 대상은 정상 등록 시 지급액 계산·확정, 과거 확정 결과 재계산 금지. 월 정산의 Session 구성은 유효 확정 결과 집계다. 기본급 적용 시작 월의 관리자 지정·미확정 과거 월 지정 허용·수동 지정 없는 기존 미확정 정산의 기본급·합계 자동 반영은 확정했고 미리 등록할 수 있는 미래 적용 시작 월의 범위 등 남은 상세는 BR-012, Product 변경의 기존 Pass 적용은 발급 당시 상품 조건 유지로 BR-011 CLOSED, 타 지점 보상 전체는 MB-009에 따라 추가실적으로 처리한다. 지원 수업은 BR-013의 후속 사용자 결정에 따라 관리자 건별 수동 금액 저장 시 보상을 확정하며 미입력 건이 남으면 해당 Trainer·월 정산 확정을 차단한다. 나머지 추가실적 정책은 BR-013을 따른다. 이 CLOSED를 타 지점 추가실적 정책으로 확대 해석하지 않는다. 보존 구현은 Architecture 결정이다.

<a id="br-007"></a>
## BR-007. Session 정정·취소와 정산 반영

Question / TODO: 남은 정정 항목·상태/기간·역사 사실 확인 불가·최소 계약/실패·경합과 월 반영을 구체화한다. W1로 Trainer 과거 Home 오류의 일반/지원 분류 변경은 Master Organization 전용 명시적 정정/같은 PT·기존 Pass 차감 유지로 해결됐다. 일반 지급은 최초 기록 생성 시점 실제 수행 Trainer 설정/기존 소비 Pass 발급 조건, 지원 보상은 기존 관리자 범위 수동 추가실적이며 이전 결과 보존/유효 합계 이중 반영 금지다. W2 영향 건 정정 완료 전 해당 Trainer·월 확정/재확정 차단·기존 확정본 자동 변경 없음과 기존 Member/실제 수행자/시작 오류 취소 재등록·Performed 값 Master 정정 및 필요한 월 해제/동일 월 재확정 권한/사유는 유지한다. 이미 승인된 정정 방식/지급 기준을 재질문하지 않는다.

Related decisions / requirements: PD-010/011/012; PR-009/010. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Architecture 착수 가능; 정정 상세 설계·구현 확정 전 업무 기대 결과 확인

확정된 경계: Master Admin 또는 실제 Performed Branch 범위 Branch Admin이 담당하며 Operator 역할만으로는 PT 진행 기록 정정/취소를 할 수 없다(2026-10-11 사용자 확정). Trainer 역할만으로는 본인 PT 진행 기록도 정정/취소할 수 없다(2026-10-11 사용자 확정). 관리자 겸임자는 해당 업무의 별도 관리 권한·Branch Scope로 판단한다. Pass 잔여·정산 일관성과 이력 보존은 승인됨. 월 정산 확인·마감/확정 절차의 남은 상세는 BR-009 OPEN이다. 지원 수업 보상 금액 오류에 한해 확정 해제 → 정정 → 해당 월 재확정과 이전 확정본 보존을 별도로 승인했다(BR-009/013). 이를 PT 진행 사실 정정·취소나 일반 Session Payment 정정에 자동 적용하지 않는다. 확정된 과거 정산의 자동 변경 금지는 승인되었으나 구체 확정 절차를 승인한 것은 아니다. 정정/취소의 상세를 정하더라도 Trainer 설정 변경을 이유로 과거 확정 지급액을 현재 Rate/Fixed Amount로 재계산할 수는 없다(BR-PAY-009).

2026-10-11 비용 집계 결정과의 경계: 일반 Session Payment는 해당 PT 진행 기록의 실제 Performed Branch 비용으로 집계한다. 이미 확정된 수업별 지급액을 지점별로 합산하며 대상 월말 Home Branch로 전액을 모으지 않는다. 허용된 정정/취소의 같은 유효 상태·금액·확정본 기준으로 정산 입력과 비용 집계의 일치를 후속 검증한다. 이 비용 귀속 결정으로 PT 진행 사실/일반 지급의 정정 항목·기간·권한·절차나 확정 후 재처리 정책을 새로 승인하지 않으며 위 잔여 질문은 OPEN이다.

Status: OPEN

2026-10-11 기록 정정 Scope 확정: Master Organization 전체/Branch Admin 실제 Performed Branch 기준이다. 추가실적 금액 입력·Trainer 전체 월 정산은 기존 현재 Home Branch 기준으로 유지한다. 확정된 타 지점 수업의 정정/취소에서 기록 담당자와 정산 해제·재확정 담당자가 다른 경우의 순서·권한 연계, 지급/추가실적 반영 및 Performed Branch 자체 오류 정정은 미결정이다. 기록 권한으로 확정 정산을 직접 변경하거나 금액 관리 권한을 확대하지 않는다.

2026-10-11 사용자 확정(확정 월의 타 지점 수업 취소 처리 질문의 “11”을 1번 답변으로 해석): 이미 월 정산이 확정된 타 지점 PT 수업을 취소할 때 기존 권한을 유지한다. 대상 Trainer·월 정산의 확정 해제 → 해당 PT 진행 기록 취소 → 같은 Trainer·월 정산 재확정 순서로 처리한다. Branch Admin은 해제/재확정 각 처리 시점 Trainer의 현재 Home Branch가 관리 Branch인 경우 정산을 담당하고, 기록 취소는 해당 수업의 실제 Performed Branch 관리자가 담당한다. 예를 들어 현재 수원 소속 Trainer의 강남 수업이면 수원 Branch Admin이 해당 월 정산을 해제하고 강남 Branch Admin이 기록을 취소한 뒤 수원 Branch Admin이 재확정한다. 두 지점 담당자가 각자의 권한으로 협업하며 Master Admin은 Organization 범위 안에서 전체 과정을 처리할 수 있다. 수행 지점 관리자에게 다른 소속 Trainer의 전체 월 정산이나 추가실적 금액 입력 권한을 부여하지 않는다. 이전 확정본·변경 이력 보존, 기존 해제 사유/감사와 재확정 조건은 유지한다. 현재 설정으로 다른 과거 지급/적용 기본급을 재계산하거나 취소 저장만으로 자동 재확정하지 않는다. 이 결정은 위 취소의 처리 순서와 담당 권한에 한정한다. Operator 권한·취소 시 지급/연계 추가실적의 유효 결과·잔여 복원 예외·정정 항목/기간·Performed Branch 자체 오류 정정 및 각 단계 계약/실패·재시도/경합은 잔여 OPEN 또는 PROPOSED다.

2026-10-11 사용자 확정(수업 취소 시 그 수업의 추가실적 보상 처리 질문의 1번): 허용된 PT 진행 기록 취소 시 해당 수업의 보상으로 입력한 Additional Performance도 함께 자동 무효 처리한다. 해당 보상은 유효한 Trainer 월 정산 및 지점 비용 집계에서 제외하며 기존 금액·원본과 취소/변경 이력은 보존한다. 금액을 0원으로 덮어쓰거나 관리자의 별도 추가실적 취소를 기다리는 방식이 아니다. 수행 지점 관리자가 기존 권한으로 해당 수업을 취소하면 그 수업 보상의 무효 처리가 동반되지만, 보상 금액의 입력/임의 수정이나 다른 소속 Trainer의 보상 설정·전체 정산 조회 권한을 추가로 얻지는 않는다. 수업과 무관한 다른 추가실적까지 무효 처리하지 않는다. 확정 월은 기존 현재 Home Branch 담당자 해제 → Performed Branch 담당자 취소 → 현재 Home Branch 담당자 같은 월 재확정 순서와 이전 확정본 보존을 따른다. 등록 금액의 관리자 직접 입력·기존 해제 사유/감사·재확정 조건은 유지한다. 상태 저장/계산 표현·모듈 계약·필수 변경/감사의 원자성·실패/재시도/동시성은 후속 Architecture 설계·검증 대상이며 다른 정정/취소의 나머지 정책은 OPEN이다.

2026-10-11 사용자 확정: Performed Branch 자체 오류 정정 권한은 Master Admin 전용으로 해결됐다(PD-010/MB-005). Branch Admin의 일반 기록 정정/취소와 구분한다. 지점 오류 정정 방식·확정 월 연계·일반/지원 수업 보상 전환·적용 설정 시점 및 나머지 항목은 OPEN이며 기존 과거 지급 결과를 현재 Trainer 설정으로 재계산하는 기본값을 두지 않는다.

2026-10-11 사용자 확정: Master의 수행 지점 오류 정정은 기존 기록/Pass 차감을 유지하며 보상 방식도 정정한다(BR-OPS-001). 정정 전 사실/보상 이력 보존·중복 합산 금지, 확정 월은 기존 해제/정정/같은 월 재확정 원칙 동일 적용(사용자 일관성 지시). 지원→일반 전환의 지급 설정 기준 시점과 나머지 정정 항목/기간·잔여 복원 예외 등은 OPEN을 유지한다.

2026-10-11 사용자 확정: 수행 지점 정정으로 지원→일반 전환 시 최초 PT 기록 생성 시점 Rate/Fixed Amount를 적용한다(BR-PAY-011). 시점 선택은 해결됐으며 나머지 정정 조건·과거 설정 근거 확인/계약 상세는 후속이다.

확인 주체: 사용자/업무 책임자와 해당 후속 단계 담당자. 답변·기한은 미정.

2026-10-12 C 일괄 승인 반영: C10: Member/실제 수행 Trainer 오류는 기존 기록 취소 후 올바르게 재등록한다. 원본/취소/정정 연결 보존, 일반 지급은 재등록 생성 시점 설정 적용, 지원 보상/취소 연계 AP 무효화·Pass 복원과 기존 우선 선택을 유지한다. PT 인가는 실제 Performed Branch, 정산 인가는 각 처리 시점 Trainer 현재 Home Branch 기준이며 영향받는 확정 Trainer·월은 기존 해제/재확정과 사유/이전 확정본을 보존한다. Performed Branch 값 정정의 Master 전용은 유지한다. 다른 Trainer/월의 순서·오류/정정 상세·계약/경합은 후속이다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 G 일괄 승인 반영: G2: 지점 비활성 이후에도 비활성화 전 실제 수업의 기존 권한별 정정/취소·확정 월 해제/재확정/이전본 보존을 허용한다. PT 실제 Performed/정산 현재 Trainer Home 인가·기존 취소/참가자 재등록·지급/AP 규칙을 유지한다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). 다른 상태/신규 배정·역사 사실/구체 계약·경합 등 나머지 게이트로 이 복합 OPEN은 유지한다.

2026-10-12 J 일괄 승인 반영: J3의 Member 비활성화/재활성화 자체는 과거 PT/Pass 소비/확정 지급·정산을 삭제·자동 정정하거나 비활성 기간 수업을 자동 유효화하지 않는다. 비활성화 전 수업 누락/정정은 기존 현재 인가·실제 과거 사실/Pass·정산 규칙을 따르며 그 나머지 계약/역사 사실은 후속이다. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch). 이 복합 OPEN의 나머지 항목은 유지한다.

2026-10-12 K 일괄 승인 반영: K1로 PT 실제 시작 날짜/시각 오류는 원본 취소 후 재등록·새 일반 지급은 재등록 생성 시점 설정 적용으로 확정했다(BR-OPS-023). 소비 복원/우선 재선택·올바른 시점 관계/상태/Pass·현재 인가와 각 영향받는 확정 월 해제/처리/재확정/이전본 보존은 기존 규칙을 유지한다. Performed Branch 값 정정의 기록 유지/최초 생성 기준과 구별하며 정정 연결·단계별 실패/여러 월/UoW·경합은 후속이다. [2026-10-12 K 일괄 승인](product-decisions.md#review-20261012-k-batch). 이 복합 OPEN의 다른 항목은 유지한다.

2026-10-13 W1/W2=1 부분 해결: 과거 Trainer Home 오류에 따른 일반/지원 전환은 Master Organization 전용 명시적 정정으로 같은 PT/기존 Pass 차감·최초 생성 시각을 유지한다. 일반은 최초 기록 생성 시점 설정/소비 Pass 발급 조건, 지원은 기존 관리자 범위 수동 추가실적이다. 이전 결과 이력/유효 합계 단일 반영을 보존하고 영향 건 분류/보상·비용 정정 완료 전 해당 Trainer·월 확정/재확정을 차단한다. 소속 정정만으로 기존 확정본 자동 해제/변경 없음·기존 권한/사유·필요한 월 해제/명시적 정정/동일 월 재확정·이전본 보존을 유지한다. 역사 사실·영향/완료 증거·나머지 상태/최소 계약/경합이 남아 OPEN을 유지한다. [W 승인](product-decisions.md#review-20261013-w-batch); BR-OPS-033/PAY-024; V-124/125 미구성·미실행.

<a id="br-008"></a>
## BR-008. 진행일·동일 일자 중복·월 경계

Question / TODO: 실제 수업 시작 시각의 정밀도·소속/담당/Pass 발급 및 사용 사실의 과거 경계·확인 불가/정정과 요청 식별/월 정산 확정 경합을 어떻게 설계하는가? Asia/Seoul 시작 날짜/시각 기준(C9), 시각 확인 후 등록·시각 미상/임의 시각/관리자 예외 불가(I1), 같은 날 별개 수업 각각 기록/차감·하루 1회 제한 없음, 기존 미확정 월의 당월/최근 N일 제한 없는 과거 본인 수업 등록은 확정이며 재질문하지 않는다. 관련 Pass·인가 조건은 별도 유지한다.

Related decisions / requirements: PD-008/012; PR-008/010. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Architecture 착수 가능; 관련 업무 상세 설계·구현 확정 전

확정된 경계: 같은 날이면 무조건 중복이라는 규칙은 없다. 월 단위 집계 원본 저장은 승인 범위 밖이다.

Status: OPEN

2026-10-11 사용자 확정(같은 회원 하루 두 번 실제 수업 질문의 1번): 수업별 기록/1회 차감·같은 날짜라는 이유로 합치거나 거부하지 않음·하루 1회 제한 없음(BR-OPS-002). 같은 수업의 재전송/중복 클릭은 기존 중복 처리 방지 요구를 따른다. 동일 날짜 복수 수업 허용 여부는 해결됐으며 시간대/소급 범위/월 경계와 요청 식별 계약·실패/동시성은 후속이다.

2026-10-11 사용자 확정(Trainer의 과거 수업 등록 범위 질문의 1번): 해당 Trainer/실제 진행 월 정산이 미확정이면 기존 Allowed PT Scope에서 자신의 과거 수업을 직접 등록하며 당월/최근 N일 제한을 추가하지 않는다(BR-OPS-003). 신규 일반 지급은 기록 생성 시점 설정, 수업 구분은 실제 수업 당시 소속 기준을 유지한다. Trainer에 확정 해제/재확정 권한을 주지 않고 확정 월은 기존 관리자 해제 후 반영/같은 월 재확정 원칙과 연계한다(사용자 일관성 지시 적용). 날짜의 소급 허용 범위 선택은 해결됐으며 시간대/월 경계와 다른 게이트의 Member/Pass 사용·사실 확인 조건, 계약/실패/동시성은 후속이다.

확인 주체: 사용자/업무 책임자와 해당 후속 단계 담당자. 답변·기한은 미정.

2026-10-12 사용자 확정(담당 교체 전 수업의 누락 등록 질문의 1번): A가 담당으로 실제 수업을 진행한 뒤 담당이 B로 바뀌어도 A는 교체 전 본인 수업을 직접 늦게 등록할 수 있다. 예: 9월 5일 A 수업 → 9월 6일 B로 담당 교체 → 9월 7일 A 누락 등록. 실제 수업 당시 A의 담당 관계와 본인 수행 사실, 현재 검증된 Caller/Trainer 연결·Organization 및 기존 Pass/정산 조건을 확인한다. 현재 담당이 B라는 이유만으로 관리자 대행이나 A 재배정을 요구하지 않는다. 이 허용만으로 A의 해당 회원 목록/상세·전화번호/다른 Pass·다른 Trainer 기록 조회 권한을 복원하지 않는다(BR-OPS-003/005/008, PD-008, PR-008/029/030).

이번 결정은 교체 전 실제 본인 수업의 이전 담당 직접 등록 허용을 해결한 것이다. BR-OPS-003의 기존 미확정 월/Pass 조건·실제 수행 A 기준 지급과 회원 조회 비복원 경계를 유지한다. 과거 담당/수행 사실 확인 불가/정정·동일 시점 순서·다른 관계의 나머지 인가, 최소 식별/응답 및 계약/저장/UoW·교체/등록/월 확정 경합은 계속 OPEN이다.

2026-10-12 사용자 확정(비활성화 전 진행했지만 누락된 PT 수업 등록 질문의 1번): Trainer 비활성화 전에 실제로 수행한 미등록 PT 수업은 관리자가 대행 등록하는 경로를 허용한다. 대상 Trainer의 비활성 상태를 유지하며 잠시 재활성화/본인 로그인·담당 재배정을 선행 요구하지 않는다. 실제 수행 Trainer·실제 수업일과 기존 Pass 잔여/정산 조건을 그대로 적용한다(BR-OPS-015, PD-008/011, PR-008/029/030, BR-OPS-003/008/014, BR-PAY-006/011/012).

관리자 대행 경로와 Master Organization/Branch Admin 실제 Performed Branch Scope는 해결됐다. 현재 인가 검증·비활성화 전 실제 수업/담당/소속 사실·시점/확인 불가·최소 선택 정보/사유·증빙과 구체 계약/저장/UoW·경합은 후속이다. 비활성/현재 담당 유지·실제 수행자/수업일·기존 Pass/생성 시점 보상/진행 월 정산·민감 설정 접근 제한을 적용한다. 비활성 Trainer 본인 직접 등록/회원 조회 예외가 아니며 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 일괄 승인 반영: B7로 Organization 공통 Asia/Seoul 업무 날짜/달력 월 경계가 해결됐다(BR-OPS-017). 날짜 정밀도·실제 시점/소급 상태 사실/확인 불가·중복/월 확정 경합은 남는다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch). 이 복합 OPEN의 다른 미결정 항목은 유지한다.

2026-10-12 C 일괄 승인 반영: C9: 완료 수업의 실제 시작 날짜/시각을 기록하고 Asia/Seoul로 업무 일자/월을 판단한다. 생성 시점과 구별하며 일반 지급은 기존 생성 시점 설정을 따른다. 초 이하 정밀도/시각 확인 불가·역사 사실 정정·저장/월 확정 경합은 후속이다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 G 일괄 승인 반영: G2: 비활성화 전 실제 수업의 기존 권한별 소급 처리는 지점 재활성화 없이 허용한다. 실제 시작/운영 이력의 확인 불가·정정과 시각 정밀도/월 확정 경합은 남는다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). 다른 상태/신규 배정·역사 사실/구체 계약·경합 등 나머지 게이트로 이 복합 OPEN은 유지한다.

2026-10-12 I 일괄 승인 반영: I1=1: 시작 시각을 모르면 확인 후 등록하며 임의 시각/시각 미상·관리자 예외는 불가다. 정밀도/과거 관계·발급/사용 사실/경합 계약은 별도이며 이 복합 OPEN을 모두 닫지는 않는다. [2026-10-12 I 일괄 승인](product-decisions.md#review-20261012-i-batch).

2026-10-12 J 일괄 승인 반영: J3의 실제 수업 시점 Member 비활성 여부와 현재 Member 상태/Caller·월 정산 상태를 구분한다. 비활성 기간 수업은 나중에 등록/재활성화해도 허용되지 않으며 비활성화 전 실제 수업 처리는 기존 규칙을 유지한다. 실제 시작 시각 확인/I1 및 나머지 역사 사실/시점/정정·경합 계약은 후속이다. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch). 이 복합 OPEN의 나머지 항목은 유지한다.

2026-10-12 K 일괄 승인 반영: K1 날짜/시각 오류의 취소 후 올바른 재등록·새 일반 지급 생성 시점 적용은 해결됐다. 실제 시점 소속/담당·상태/Pass 발급 사실과 현재 잔여/권한·월 확정을 구분한다. I1 시각 미상/임의 시각 예외 불가·J3 Member 비활성 기간 수업 차단을 유지하고 역사 사실/정정·정밀도/경합 계약은 후속이다. [2026-10-12 K 일괄 승인](product-decisions.md#review-20261012-k-batch). 이 복합 OPEN의 다른 항목은 유지한다.

<a id="arch-001"></a>
## ARCH-001. Role/Permission 상세

2026-10-10 사용자 결정 — 역할 겸임: Master Admin 또는 Branch Admin이 Trainer를 겸하며 한 계정으로 관리 업무와 본인의 PT 진행 기록을 모두 수행한다. 계정당 단일 역할만 허용하는 제약은 두지 않는다. 기존 역할별 Branch Scope·보상 설정 제한은 유지하며 행위별 인가·감사의 구체 표현은 상세 설계 대상이다. 같은 날 최종 정정으로 겸임 계정도 관리 권한 범위 안이면 본인의 Rate/Fixed Amount/Base Salary를 조회·변경할 수 있도록 확정했다. Master는 본인 포함, Branch Admin은 본인 Trainer의 Home Branch가 관리 Branch와 일치할 때 허용하며 “본인은 Master만 가능” 답변을 대체한다. 관리자 권한이 없는 Trainer의 본인 설정 접근은 여전히 불가다. ARCH-001은 나머지 권한·인가/감사 상세가 남아 부분 해결 상태로 OPEN을 유지한다.

Question / TODO: Role/Data Scope 기술 모델·행위별 Permission/현재 권한 확인·최소 응답/오류 계약을 구체화한다. S1/S2로 이전 정산 확정본·해제/재확정 및 세 보상 설정 변경 이력 조회의 Master Organization/현재 Trainer Home Branch Admin 범위가 확정됐다. N1/N2 수업별 금액 기밀성·H4 비관리자 Trainer 월 정산 제외·C7 인증/계정 관리 감사 Master 전용·겸임 독립 관리 Scope를 유지한다. 남은 세부 공개 필드/계산 근거·다른 업무 감사/정정/권한 변경 경합과 계약은 후속이며 승인된 이력 조회 자체를 다시 미결정으로 두지 않는다.

Related decisions / requirements: PD-001/010/022; PR-001/021/027. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Architecture의 Authentication/Authorization 설계 중 검토; 미정인 정정·감사 열람 범위는 관련 상세 권한 확정 전 Product 확인

확정된 경계: Rate / Fixed Amount / Base Salary 세 항목의 조회·설정·변경은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 단일 Branch를 Home Branch로 가진 Trainer에게만 허용한다. 관리자와 Trainer를 겸하는 계정은 관리 권한 범위 안이면 본인의 세 항목도 조회·변경할 수 있다. Master Admin은 본인 포함 허용하며, Branch Admin은 본인 Trainer의 Home Branch가 관리 Branch일 때 본인도 허용한다. 관리자 권한이 없는 Operator·Trainer 계정은 본인 포함 모든 Trainer 설정 조회·변경이 불가하다. 타 지점 지원 수업은 보상 설정 접근 권한을 부여하지 않는다. Backend에서 대상 Trainer의 Home Branch를 검증하며 직접 ID 요청과 감사·정산 등 우회 경로에도 제한을 적용한다. 모든 보상 설정 변경(최초 설정 포함)에 대상 Trainer, 변경 항목, 변경 전 값, 변경 후 값, 변경 Actor, Actor의 권한 및 Branch Context, 변경 시점을 추적한다. 별도 Master Admin 승인 없이 변경 가능하며 변경 요청→승인 대기→승인→반영 절차를 추가하지 않는다. 이 결정은 추가실적 승인이나 월 정산 마감/확정 절차를 면제하지 않는다. 세부 기술 모델과 감사 조회 구현은 Architecture에서 결정하며 미정 업무 열람 범위는 사용자 결정이 필요하다.

Status: OPEN

확인 주체: 사용자/업무 책임자와 해당 후속 단계 담당자. 답변·기한은 미정.

2026-10-12 후속 확정: 회원 Home Branch 변경의 Actor/Scope는 Master Organization 전체 또는 변경 전 Member 현재 Home Branch 관리 Branch Admin, 받는 지점의 별도 승인 없음이다(BR-OPS-007, MB-002). 관리자 권한 없는 Operator/Trainer는 불가하며 인증/인가 기술 모델·이동 시점·Trainer 이동 권한 등 나머지 상세는 계속 OPEN이다.

2026-10-12 후속 결정 게이트 — Pass 담당 교체: 기존 이용권에서 담당 교체 허용/잔여·과거 이력 보존은 확정(BR-OPS-008). 교체 명령을 수행할 Actor와 Branch Scope는 아직 미결정이며 Issued Branch 또는 Member 현재 Home Branch 기준을 임의 선택하지 않는다. 현재 담당/개별 지원/관리 관계에 따른 조회는 기존 원칙을 유지하며 교체 권한과 구별한다.

2026-10-12 사용자 확정(담당 교체 권한의 기준 지점 질문의 1번): 기존 Pass의 Assigned Trainer 교체는 Master Admin의 Organization 전체 범위 또는 처리 시점 Member의 현재 Home Branch를 관리하는 Branch Admin에게 허용한다. 수원 발급 Pass의 회원이 현재 강남 소속이면 강남 Branch Admin 또는 Master가 교체할 수 있으며, 수원 Branch Admin은 Issued Branch만을 근거로 교체할 수 없다. 회원 소속이 다시 변경되면 각 교체 요청은 변경된 현재 Home Branch 기준으로 인가한다. 이용권 수동 만료/해제의 Issued Branch 기준은 그대로 유지한다(BR-OPS-004/008, PD-007, PR-003/030).

후속 게이트 갱신: 담당 교체 Actor/Branch Scope와 대상 Trainer 지점 조건은 2026-10-12 사용자 결정으로 해결됐다. 조회 허용과 교체 명령 인가는 구별하며 비관리자/위조 Scope/Issued Branch만의 권한 주장은 거부한다. 교체 전 실제 본인 수업의 이전 담당 직접 등록 허용은 해결됐다(2026-10-12, BR-OPS-003/008). 잔여 소진 외 수동 만료/취소 등 나머지 Pass 상태·과거 담당/수행 사실 확인 불가/정정과 최소 식별/Trainer 선택 정보·공개 계약/이력/저장/UoW·동시성은 계속 OPEN이다. 보상 설정 인가와 수동 만료/해제의 Issued Branch 기준은 바꾸지 않는다.

2026-10-12 사용자 확정(교체할 Trainer의 소속 지점 질문의 1번): 기존 Pass의 담당 교체 대상은 같은 Organization의 Trainer이며 Member 현재 Home Branch와 다른 지점 소속 Trainer도 허용한다. 강남 회원의 담당을 수원 소속 Trainer로 바꿀 수 있다. Member와 같은 지점 소속이어야 한다는 제한을 두지 않으며 다른 Organization Trainer는 지정할 수 없다. 교체 요청의 Actor 권한은 기존대로 Master Organization 전체 또는 Branch Admin 처리 시점 Member 현재 Home Branch 기준이다(BR-OPS-008, PD-007, PR-003/029/030).

타 지점 담당 허용은 현재 관계 기반 회원 조회와 기존 수업 수행 지점/당시 Trainer Home Branch 보상 구분을 유지한다. 교체 전 본인 수업의 이전 담당 직접 등록 허용은 해결(2026-10-12)됐으며 잔여 소진 외 수동 만료/취소 등 나머지 Pass 상태·과거 담당/수행 사실 확인 불가/정정 및 최소 식별/Trainer 선택 정보·계약/경합은 계속 OPEN이며 다른 지점 전체 목록/민감 보상 공개 권한을 부여하지 않는다.

2026-10-12 사용자 확정(담당 교체 전 수업의 누락 등록 질문의 1번): A가 담당으로 실제 수업을 진행한 뒤 담당이 B로 바뀌어도 A는 교체 전 본인 수업을 직접 늦게 등록할 수 있다. 예: 9월 5일 A 수업 → 9월 6일 B로 담당 교체 → 9월 7일 A 누락 등록. 실제 수업 당시 A의 담당 관계와 본인 수행 사실, 현재 검증된 Caller/Trainer 연결·Organization 및 기존 Pass/정산 조건을 확인한다. 현재 담당이 B라는 이유만으로 관리자 대행이나 A 재배정을 요구하지 않는다. 이 허용만으로 A의 해당 회원 목록/상세·전화번호/다른 Pass·다른 Trainer 기록 조회 권한을 복원하지 않는다(BR-OPS-003/005/008, PD-008, PR-008/029/030).

이번 결정은 교체 전 실제 본인 수업의 이전 담당 직접 등록 허용을 해결한 것이다. BR-OPS-003의 기존 미확정 월/Pass 조건·실제 수행 A 기준 지급과 회원 조회 비복원 경계를 유지한다. 과거 담당/수행 사실 확인 불가/정정·동일 시점 순서·다른 관계의 나머지 인가, 최소 식별/응답 및 계약/저장/UoW·교체/등록/월 확정 경합은 계속 OPEN이다.

2026-10-12 사용자 확정(잔여 0회인 이용권의 담당 교체 질문의 1번): Remaining이 0인 기존 Pass도 Assigned Trainer를 교체할 수 있다. 잔여를 모두 사용해 이용이 끝난 Pass도 포함한다. 같은 Pass에서 담당 A를 B로 바꾸며 Remaining 0·발급 조건/Issued Branch·과거 실제 수행 Trainer/PT 기록·확정 지급/정산 이력은 유지한다. 새 담당 B는 기존 현재 담당 관계에 따른 Member 조회·응대를 이어갈 수 있다. 기존 Master Organization 전체/Branch Admin 처리 시점 Member 현재 Home Branch 권한과 같은 Organization의 다른 지점 Trainer도 대상 허용 원칙은 유지한다(BR-OPS-005/008, PD-007, PR-003/029/030).

후속 게이트 갱신: 잔여 0으로 이용을 마친 Pass의 담당 교체/새 담당 Member 조회만 추가 해결됐다. 잔여 0 유지·현재 Caller/Member/Organization/담당 관계 검증·선택 필터의 Member 전체 Pass 기준과 실제 PT 잔여 > 0 조건은 유지한다. 수동 만료/취소 등 다른 종료 사유의 담당 관계/교체와 과거 사실/최소 정보·저장/응답/UoW·동시성은 계속 OPEN이다.

2026-10-12 사용자 확정(이용권 횟수의 수동 조정 권한 질문의 1번): Pass 횟수의 수동 조정은 Master Admin의 Organization 전체 범위 또는 처리 시점 현재 관리 Branch가 해당 Pass의 Issued Branch인 Branch Admin에게 허용한다. 수원 발급/현재 강남 소속 Member의 이용권은 수원 Branch Admin 또는 Master가 조정하며, 강남 Branch Admin은 Member의 현재 소속만을 근거로 조정할 수 없다. 회원 소속이나 담당 Trainer가 바뀌어도 Issued Branch 기준은 유지한다. 이용권 수동 만료/해제와 같은 발급 지점 기준이며 담당 교체의 Member 현재 Home Branch 기준과 구별한다(BR-OPS-004/008/009, PD-007/010, PR-003/030).

관리자/지점 기준은 해결됐으며 기존 사유/전후 잔여·증감량/Actor·시점 이력·감사를 적용한다. PT 취소 복원의 기존 업무 권한/조건과 담당 교체의 Member 현재 Home Branch 기준은 유지한다. 수동 추가/감소의 목적·수량/상태·사용 재개/복원 연계 및 저장/계약/UoW·중복/동시성은 계속 OPEN이다(BR-OPS-009, BR-001/002/007, ARCH-003).

2026-10-12 사용자 확정(다른 지점에서 새 이용권 구매·발급 질문의 1번): Member는 같은 Organization의 Home Branch 밖 지점에서도 새 PT Pass를 구매·발급받을 수 있다. 수원 소속 회원이 강남에서 발급받으면 Member Home Branch는 수원으로 유지하고 새 Pass의 Issued Branch는 강남으로 기록한다. Member Home Branch와 Issued Branch가 같아야 한다는 제한을 두지 않는다. 기존 Member 식별자/소속·보유 Pass와 과거 PT/지급·정산 이력은 유지하며 타 지점 발급을 위해 Member를 지점별로 복제하거나 소속을 자동 이동하지 않는다(BR-OPS-001/010, PD-004/007, PR-002/003/030).

이번 결정은 발급 대상 Member 소속과 실제 Issued Branch가 달라도 새 발급 가능하다는 경계를 해결했다. Member/기존 Pass·과거 이력 유지, 공통 상품/판매 중단·발급 조건 보존과 이후 Issued Branch 관리 원칙을 적용한다. Master·Branch Admin·Operator의 발급 허용/각 역할의 실제 발급 Branch 범위와 Trainer 단독 불가는 후속 승인으로 해결됐다(2026-10-12). 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·실제 발급 지점 선택 및 활성/초기 조건, 타 지점 Member 발급용 추가 공개 정보·Member 선택용 최소 식별 응답/계약 및 계약/저장/UoW·재시도/동시성은 계속 OPEN이다. 발급용 같은 Organization 전체 지점 이름·전화번호 일부 검색은 후속 2번 승인으로 해결됐다(BR-OPS-010).

2026-10-12 사용자 확정(새 이용권 발급 Actor 질문의 1번): 새 PT Pass 발급은 Master Admin·Branch Admin·Operator에게 각자의 허용된 실제 Issued Branch 범위에서 허용한다. Master는 Organization 전체, Branch Admin은 자신의 단일 관리 Branch, Operator는 부여된 허용 발급 Branch Scope에서 처리한다. 같은 Organization의 Member는 Home Branch가 발급 지점과 달라도 대상이 될 수 있으며 기존 Member/Home Branch를 유지하고 새 Pass에 실제 Issued Branch를 기록한다(BR-OPS-010, PD-004/007, PR-003/030).

이번 결정은 새 Pass 발급 Actor와 역할별 발급 지점 경계만 해결했다. 권한 경계: Trainer 역할만으로는 새 Pass를 발급할 수 없다. Trainer를 겸하는 계정에 Master·Branch Admin·Operator의 발급 권한이 있으면 해당 역할의 독립적인 발급 Scope로 판단하며 별도 계정을 요구하지 않는다. Operator의 새 발급 권한은 공통 상품 생성/수정, 기존 Pass 수동 횟수 조정·만료/해제·담당 교체, Member 소속 이동, PT 정정/취소·Compensation Setting·Additional Performance·월 정산의 별도 권한을 추가하지 않는다. 발급 대상 식별을 타 지점 전체 Member 목록/전화번호·다른 Pass/PT/민감 보상 정보의 일반 조회 허용으로 확대하지 않는다. 기존 보상 설정 접근 제한과 Trainer의 담당/개별 지원 회원 조회는 그대로다.

남은 결정: 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차과 실제 발급 지점 선택/계약, 지점/Member/Trainer 활성·발급 시 활성 담당 필수/상품 최초 횟수의 나머지 상태/선택 계약, 타 지점 Member 추가 공개 정보·Member 선택용 최소 식별 응답/계약과 업무 인가 경로는 ARCH-001·MB-001/002/003/004/005·BR-001/002/010 후속이다. 승인된 Master·Branch Admin·Operator의 발급 허용과 Trainer 단독 불가를 다시 미결정으로 두지 않으며, 미정 Scope 부여/조회·상태 조건을 임의 기본값으로 구현하지 않는다. 발급/상품 조건·감사 계약/저장·Application UoW·실패/재시도/중복 및 판매 중단/지점 상태/Member 이동/인가 변경 경합은 후속 Architecture 설계·검증 대상이다.

2026-10-12 사용자 확정(발급용 타 지점 회원 검색 질문의 2번): Branch Admin·Operator는 자신의 허용된 실제 Issued Branch에서 새 PT Pass를 발급하기 위해 같은 Organization 전체 지점의 Member를 이름·전화번호 일부로 검색할 수 있다. 전화번호 전체 일치만을 요구하지 않으며 Member Home Branch가 Caller의 관리/발급 Branch와 다르다는 이유만으로 검색 후보에서 제외하지 않는다. Master의 기존 Organization 전체 범위는 유지한다. 검색은 기존 Member를 선택하여 실제 발급 지점의 새 Pass를 만드는 흐름이며 Member 소속 이동/복제나 기존 Pass·PT·지급·정산 변경을 수행하지 않는다(BR-OPS-010, PD-004/007/022, PR-002/003/030).

검색 인가/정보 공개 경계: 이 허용은 이용권 발급용 Member 검색의 후보 범위·검색 방식과 이름/전체 전화번호/현재 Member Home Branch 공개다. Backend는 매 검색/선택/발급 요청에서 현재 Caller의 발급 역할/Organization·허용 실제 Issued Branch와 대상 Member의 실제 Organization을 검증한다. 검색 Branch Context를 위조하거나 과거 검색 결과/선택 Member ID로 철회된 역할·Scope 또는 다른 Organization을 우회할 수 없다. 같은 전화번호/이름의 여러 Member는 별도 식별자로 구분하여 선택하며 번호만으로 병합하거나 첫 결과를 자동 선택하지 않는다. 이 세 항목의 읽기 허용이 회원 정보/전화번호 수정·일반 Member 상세·전체 무조건 목록/일괄 내보내기, 다른 개인정보/Pass/PT/보상 정보 열람 권한을 추가하지 않는다. Trainer 단독의 담당/개별 지원 Member 검색 및 기존 전체 전화번호 공개는 유지하고 발급 역할 겸임은 그 독립 발급 업무 Scope로 판단한다. 응답은 승인된 공개 범위 안에서 구성하며 Member 선택용 최소 식별 응답/계약과 추가 공개 정보는 후속이다. 실제 운영 연락처/검색어를 문서·일반 로그에 복사하지 않는다.

이번 결정으로 발급용 검색 후보의 Organization 전체 지점 범위·이름/전화번호 일부 검색과 결과의 이름/전체 전화번호/현재 Member Home Branch 공개는 해결됐다. 추가 공개 정보·Member 선택용 최소 식별 응답/계약 및 나머지 검색/대상 조건, 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·실제 발급 지점 선택, 발급 시 활성 담당 필수/상품 최초 횟수의 나머지 상태·계약/저장/UoW·실패/재시도/중복·권한/소속/상품/지점 상태 변경 경합은 후속이다. 승인된 세 항목의 공개/전화번호 비마스킹을 다시 미결정으로 두지 않는다. Product OPEN/ADR·모듈/계약 상태와 기존 보상 설정 접근 제한을 유지하며 실제 검색/발급 구현·검증 완료를 뜻하지 않는다.

2026-10-12 사용자 확정(발급용 검색 결과 표시 정보 질문의 1번): 새 PT Pass 발급용 Member 검색 결과에는 이름·전체 전화번호·소속 지점을 표시한다. 소속 지점은 해당 Member의 현재 Home Branch이며 Caller 관리 지점/Pass Issued Branch/수업 Performed Branch와 구별한다. 같은 Organization의 타 지점 회원 검색 결과에도 동일하게 적용하고 부분 마스킹된 번호만 표시하도록 제한하지 않는다. 기존 이름·전화번호 일부의 Organization 전체 지점 검색과 현재 발급 역할/실제 Issued Branch Scope 인가는 유지한다(BR-OPS-010, PD-004/007/022, PR-002/003/030, NFR-001/005).

공개 범위 게이트 갱신: 검색 결과의 이름·전체 전화번호·현재 Member Home Branch 표시는 해결됐다. 검색/선택/발급마다 기존 현재 Caller/역할·실제 Issued Branch/Organization을 검증하며 다른 개인정보/일반 회원 상세·다른 Pass/PT·보상/내보내기·수정 권한을 추가하지 않는다. 공유 번호/동명이인의 Member 구분·선택과 기존 Trainer 조회 제한을 유지한다. 추가 공개 정보·최소 선택 응답/계약과 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·나머지 검색/대상/발급 조건/일관성은 후속이며 이 OPEN 전체를 CLOSED로 바꾸지 않는다(BR-OPS-010).

2026-10-12 사용자 확정(Operator 업무 허용 지점 수 질문의 1번): v1 Operator 역할의 업무 허용 Branch는 한 시점에 하나만 지정한다. Operator는 그 지정된 단일 Branch에서 명시적으로 허용된 업무를 수행하며 같은 계정의 Operator 권한을 여러 Branch에 동시 부여하지 않는다. Branch당 Operator 한 명이라는 1:1 인원 제한을 추가하지 않으며 하나의 Branch에 여러 Operator가 있을 수 있다. 이 결정은 Operator 역할의 업무 Scope이며 기존에 허용된 겸임 역할의 독립적인 관리/PT 권한이나 Trainer Home Branch를 바꾸지 않는다(BR-OPS-011, PD-001/007, PR-001/003/030, ARCH-001, MB-004).

이번 결정은 Operator 동시 허용 Branch를 하나로 확정한 것이다. 새 Operator 발급/최초 지점 지정 Actor는 Master Organization 전체/Branch Admin 자기 단일 Branch로 후속 승인됐다. 발급 절차·기존 계정 역할 부여/변경·지점 변경의 대상/절차·나머지 행위 권한은 계속 OPEN이다. Operator 지점 변경 Actor는 Master 전용으로 후속 승인됐으며 기존 저장 후 현재 Scope 반영/실패 보존·감사 원칙을 적용한다. 발급용 이름/전화번호 일부의 같은 Organization 전체 지점 Member 검색과 이름·전체 전화번호·현재 Member Home Branch 공개는 유지하고 다른 Branch 발급/일반 조회 권한을 추가하지 않는다. 기존 겸임의 독립 Scope와 민감 보상 제한·IAM S1 후속 범위를 유지한다(BR-OPS-010/011).

2026-10-12 사용자 확정(Operator 계정 발급과 최초 지점 지정 권한 질문의 1번): Master Admin은 자신의 Organization 범위에서, Branch Admin은 자신의 단일 관리 Branch 범위에서 새 Operator 계정을 발급하고 그 한 지점을 최초 업무 Branch로 지정할 수 있다. Branch Admin의 타 지점 Operator 발급은 허용하지 않는다. Backend는 처리 시점의 검증된 현재 Caller 역할/Organization·관리 Branch와 대상 Branch의 실제 Organization 관계를 확인하며 직접 ID·위조 role/branch_id·과거 권한으로 범위를 우회할 수 없다. Operator 단독·Trainer 단독의 로그인 계정 발급은 허용하지 않는다(BR-OPS-011, PD-019, PR-021/030, NFR-001/004, MB-004, ARCH-001/002).

이번에 해결된 것은 새 Operator 계정 발급/최초 지점 지정 Actor와 허용 Scope다. Operator 지정 Branch 변경은 Master 전용으로 후속 승인됐다. 기존 계정 역할 추가/변경·Operator 변경 대상/절차·계정 수명 업무 및 Operator·Trainer 신규 발급 외 계정 업무 위임은 계속 OPEN이다. 신규 Trainer 발급 Actor/Scope는 BR-OPS-012의 후속 승인을 적용한다. 발급 관리자의 일회용 최초 비밀번호 설정 링크 전달은 기존 승인 방식을 재사용하며 상세 전달/수명은 ARCH-002다. IAM-001 S1의 기존 최소 관리자 흐름/ADR-0004 v1 인증 방식 ACCEPTED를 변경하지 않는다.

2026-10-12 사용자 확정(기존 Operator의 근무 지점 이동 권한 질문의 1번): 기존 Operator의 단일 업무 허용 Branch 변경은 Master Admin만 자신의 Organization 범위에서 수행할 수 있다. Branch Admin은 변경 전/후 지점 관리자이거나 해당 계정의 최초 발급자여도 변경할 수 없다. Operator·Trainer 단독도 불가하며 겸임자는 현재 Master 권한이 있을 때만 그 관리 Scope로 처리한다(BR-OPS-011, PD-019, PR-021/030, NFR-001/004, MB-004, ARCH-001).

Operator 지점 변경의 Actor는 해결됐으며 일반 저장 후 현재 Scope 반영/실패 보존·감사 원칙을 재사용한다. 대상 Branch/계정 상태·세부 절차·기존 계정의 다른 역할/Scope 변경·계정 수명 권한은 미정이고 실제 저장/Caller/인가/UoW·처리 중 요청/동시성은 후속이다. 신규 Operator 발급 Actor·단일 Branch 수 및 기존 발급용 검색 범위/필드는 재질문하지 않는다. 이 OPEN 전체를 CLOSED로 바꾸거나 IAM-001 S1/ADR-0004를 승인한 것은 아니다.

2026-10-12 사용자 확정(신규 Trainer 로그인 계정 발급 권한 질문의 1번): Master Admin은 자신의 Organization 전체 Trainer, Branch Admin은 발급 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 단일 관리 Branch인 경우 신규 Trainer 로그인 계정을 발급할 수 있다. Branch Admin은 타 지점 소속 Trainer 계정을 발급할 수 없다. 타 지점 지원 수업·담당 회원/Pass·Performed Branch·Operator 업무 Branch·최초 발급자/과거 소속 사실만으로 이 권한이 생기지 않는다. Operator·Trainer 단독은 본인 포함 로그인 계정 발급 불가이며 관리자 겸임은 현재 관리자 역할의 독립 Scope로 판단한다(BR-OPS-012, PD-019, PR-021/029/030, NFR-001/004, MB-004, ARCH-001/002).

Trainer 신규 발급 Actor/Scope는 해결됐고 기존 일회용 최초 비밀번호 설정 링크/감사·일관성 원칙을 재사용한다. 기존 계정의 Trainer 역할 추가/재연결·관리자 승격/Master 전용 Trainer 이동의 미정 대상/절차·중단/복구·재설정 등 수명 업무 권한과 대상 상태/중복·선택/연결/전달 세부 절차는 기존 게이트다. IAM/Workforce/Organization/Audit 계약·저장/UoW·실패/재시도/동시성은 후속이며 IAM-001 S1/ADR-0004 v1 인증 방식 ACCEPTED는 유지한다. 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 사용자 확정(Trainer 소속 지점(Home Branch) 변경 권한 질문의 1번): Trainer의 Home Branch 변경은 Master Admin만 자신의 Organization 범위에서 수행한다. Branch Admin은 변경 전/후 지점 관리자 또는 해당 Trainer 계정 발급자여도 변경할 수 없다. Operator·Trainer 단독은 본인 포함 불가하며 관리자/Trainer 겸임도 현재 Master 권한이 있을 때만 해당 Organization Scope로 처리한다. Branch Admin의 자기 지점 Trainer 신규 로그인 계정 발급 권한(BR-OPS-012)은 유지하며 이를 소속 변경 권한으로 확대하지 않는다(BR-OPS-013, PD-004, PR-005/029/030, NFR-001/004, MB-001/004/005, ARCH-001).

일반 이동은 기존 사용자 일관성 지시에 따라 저장 완료 후 현재 소속 반영/실패 보존·감사를 적용하고 미래 예약을 추가하지 않는다. 독립 역할/Scope·Trainer 연결/담당·지원 관계와 과거 수업 당시 소속·확정 보상/정산은 보존한다. 대상 Branch/Trainer 상태·최소 선택 정보/절차·과거 소속 이력 정정/소급/확인 불가 및 저장/계약/UoW·캐시/처리 중 요청/동시성은 후속이며 이 OPEN 전체를 CLOSED로 바꾸지 않는다(BR-OPS-013).

2026-10-12 사용자 확정(관리자·Trainer 겸임 계정의 Trainer 비활성화 질문의 1번): Trainer 비활성화는 Trainer 역할에 따른 권한만 중단하며, 같은 계정에 독립적으로 부여된 관리자 역할/Scope와 그 범위의 업무는 유지한다. 계정 전체 로그인 차단은 별도 업무다(BR-OPS-014, PD-011/019, PR-005/026, NFR-001/004, ARCH-001/002, MB-001).

확정된 범위는 겸임 계정의 Trainer 비활성화/전체 계정 차단 분리와 Master Organization 전체·Branch Admin 처리 시점 Trainer 현재 Home Branch 기준의 비활성화 권한이다. Trainer 재활성화의 상태 조합/구체 절차, 재활성화 절차/권한 복구, 관리자 대행 등록의 상세 인가/사실 판정·비활성 Trainer 본인의 직접 등록/이력 열람 예외, 개별 지원 조회 허용 관계의 비활성화/재활성화 시 처리는 후속 결정이다. 구체 상태/역할 저장·Caller 계약·AuthSession 갱신/철회·캐시/처리 중 요청·UoW/동시성은 후속 Architecture이며 ADR-0004 v1 인증 방식은 ACCEPTED/모듈 구체 설계는 PROPOSED를 유지한다. 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 사용자 확정(Trainer 비활성화 권한 질문의 1번): Master Admin은 자신의 Organization 전체 Trainer, Branch Admin은 비활성화 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 단일 관리 Branch인 경우 Trainer를 비활성화할 수 있다. 타 지점 Branch Admin·Operator/Trainer 단독은 불가하며 겸임자는 독립된 현재 관리자 역할/Scope로 판단한다(BR-OPS-014, PD-011/019, PR-005/029/030, NFR-001/004, ARCH-001/002, MB-001).

Backend는 현재 검증된 Caller 역할/Organization·관리 Branch와 실제 대상 Trainer의 Organization/현재 Home Branch를 확인한다. 타 지점 지원 수업/Performed Branch·Member/Pass 담당 관계·Operator 업무 Branch·과거 Trainer 소속이나 계정 발급자였다는 사실만으로 비활성화 권한을 인정하지 않는다. 직접 Trainer ID·위조 role/branch_id/Organization 또는 철회·축소된 권한으로 우회할 수 없다. Trainer 소속 변경 후에는 새 현재 Home Branch로 인가한다. 비활성화 Actor/현재 소속 기준은 해결됐고 재활성화 절차·대상 상태/중복 요청·개별 지원 관계/재활성화 처리·비활성 상태 예외 및 실제 계약/저장/철회·동시성은 후속이다. 겸임 관리자 유지·별도 전체 계정 차단 게이트와 OPEN 전체 상태는 유지한다.

2026-10-12 사용자 확정(잔여가 남은 담당 이용권이 있는 Trainer의 비활성화 질문의 1번): 잔여가 남은 담당 PT Pass가 있어도 Trainer 비활성화를 허용하며 기존 Assigned Trainer 정보는 유지한다. 비활성화 전에 모든 Pass를 다른 Trainer에게 교체하도록 요구하지 않고 자동 담당 해제/재배정도 하지 않는다. 이후 필요할 때 권한 있는 관리자가 BR-OPS-008의 기존 조건/Scope로 담당을 교체한다(BR-OPS-014, PD-007/011, PR-003/005, NFR-001/004, ARCH-001/002, MB-001/003/005, BR-001).

기존 담당 정보 유지와 별도 담당 교체가 해결됐으며 비활성 Trainer의 접근은 계속 차단한다. Member 현재 Home Branch 기반 담당 교체와 Trainer Home Branch 기반 비활성화 권한을 구분하고 잔여/발급 조건·과거 PT/보상을 유지한다. 다른 상태별 교체/사용 조건·개별 지원/재활성화·비활성 상태의 과거 PT 예외 및 구체 저장/현재 인가·UoW/동시성은 후속이다. 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 사용자 확정(담당 Trainer를 새로 지정할 때의 조건 질문의 1번): PT Pass의 담당 Trainer를 새로 지정할 때는 실제 활성 Trainer만 허용한다. 기존 Pass의 담당 교체 및 허용된 새 Pass 발급 흐름에서 담당을 최초 지정하는 경우 모두 적용하며 비활성 Trainer를 미리 배정하지 않는다(BR-OPS-008/014, PD-007, PR-003/005/029/030, NFR-001, ARCH-001, MB-001/003/005, BR-001).

새 지정 대상의 활성 필요조건은 해결됐으며 같은 Organization의 타 지점 허용/기존 행위별 Actor·Scope, 이후 비활성화된 기존 담당 정보 유지·접근 차단을 적용한다. 최초 담당 필수는 해결됐고 나머지 Pass/계정/Branch 상태 조합·최소 선택 정보, 재활성화·개별 지원/비활성 전 수업 예외 및 실제 현재 사실 검증/저장/UoW·지정·비활성화 경합은 후속이다. 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 사용자 확정(비활성화 전 진행했지만 누락된 PT 수업 등록 질문의 1번): Trainer 비활성화 전에 실제로 수행한 미등록 PT 수업은 관리자가 대행 등록하는 경로를 허용한다. 대상 Trainer의 비활성 상태를 유지하며 잠시 재활성화/본인 로그인·담당 재배정을 선행 요구하지 않는다. 실제 수행 Trainer·실제 수업일과 기존 Pass 잔여/정산 조건을 그대로 적용한다(BR-OPS-015, PD-008/011, PR-008/029/030, BR-OPS-003/008/014, BR-PAY-006/011/012).

관리자 대행 경로와 Master Organization/Branch Admin 실제 Performed Branch Scope는 해결됐다. 현재 인가 검증·비활성화 전 실제 수업/담당/소속 사실·시점/확인 불가·최소 선택 정보/사유·증빙과 구체 계약/저장/UoW·경합은 후속이다. 비활성/현재 담당 유지·실제 수행자/수업일·기존 Pass/생성 시점 보상/진행 월 정산·민감 설정 접근 제한을 적용한다. 비활성 Trainer 본인 직접 등록/회원 조회 예외가 아니며 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 일괄 승인 반영: B1/B2/A7/A8: Trainer 재활성화의 현재 Home Branch 관리자 Scope·독립 역할 유지, 다른 활성 역할 없는 비활성 Trainer 로그인 불가, 관리 역할/Branch 변경 시 전체 로그인 철회, 계정 전체 차단/복구·관리자 암호 재설정의 Master 전용 Actor는 확정이다. 역할 저장/Caller·대상별 나머지 권한·계약/경합은 남는다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch). 이 복합 OPEN의 다른 미결정 항목은 유지한다.

2026-10-12 C 일괄 승인 반영: C1/C6/C7: 계정 관리 추가 비밀번호 재확인 없음, Master 전용 Login ID 변경/모든 로그인 종료, Master 전용 자기 Organization 인증/계정 관리 감사 열람으로 부분 해결됐다. 현재 행위/대상 Scope·CSRF·기존 보상/업무 감사 권한은 유지하고 Caller/역할 저장·나머지 행위/경합은 후속이다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 E 일괄 승인 반영: E5: Master Organization/Branch Admin 자기 관리 범위에서 기존 계정의 Operator·Trainer 역할만 추가/회수 가능. 각 대상 역할의 Operator 지정 Branch/실제 Trainer 현재 Home Branch로 현재 인가하며 다른 역할/Scope·연결/업무 이력 보존. Master 전용 관리 역할/계정 수명·지점 이동 등은 위임하지 않는다. 대상 상태/역할 조합·재부여/동일인 연결·최소 조회/감사·AuthSession/처리 중 요청 계약은 후속이다(BR-OPS-019). [2026-10-12 E 일괄 승인](product-decisions.md#review-20261012-e-batch)

2026-10-12 G 일괄 승인 반영: G1/G2/G5: 비활성 지점의 기존 권한 내 로그인/조회·과거 수업 처리 및 활성 지점으로의 기존 권한별 이동은 허용한다. Member Home 이동은 Master/변경 전 현재 Home Branch 관리자, Trainer·Operator 이동은 Master만 가능하며 새 열람/역할 관리 권한을 추가하지 않는다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). 다른 상태/신규 배정·역사 사실/구체 계약·경합 등 나머지 게이트로 이 복합 OPEN은 유지한다.

2026-10-12 H 일괄 승인 반영: H2/H3=1의 비지원 실적 수정/취소 현재 Home Branch 관리자 Scope·본인 포함/승인 없음·사유/이력과 H4=1 Trainer 단독 정산 조회 v1 제외를 적용한다. 다른 업무별 권한·최소 공개/Caller 계약은 후속이다. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch). 이 복합 OPEN의 남은 항목은 유지한다.

2026-10-12 J 일괄 승인 반영: J1=1: Member 등록/이름·전화번호 수정은 Master Organization 전체/Branch Admin·Operator 자기 지점이며 등록 지정 Home·수정 현재 Home 기준이다. J2=1: Member 비활성화/재활성화는 Master Organization/Branch Admin 현재 Member Home만 허용하고 OP/Trainer 단독은 불가다. 독립 겸임 Scope·다른 업무 최소 공개/이동 제한을 유지한다(BR-OPS-021/022). 나머지 권한/필드·최소 선택/응답·계약은 후속이다. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch). 이 복합 OPEN의 나머지 항목은 유지한다.

2026-10-12 K 일괄 승인 반영: K2 Trainer 신규 등록/이름·연락처 수정은 Master Organization/Branch Admin 지정·현재 Trainer Home 범위이며 OP/Trainer 단독은 불가다(BR-OPS-024). 기존 Home 이동 Master 전용·계정/보상 권한과 최소 공개를 유지한다. K1 날짜/시각 정정의 기존 PT/정산 인가는 유지하고 K3 첫 개발 범위는 관리자 인증/지점 접근 제어 개발 검증이다. 구체 계약/다른 권한·입력/상태는 후속이다. [2026-10-12 K 일괄 승인](product-decisions.md#review-20261012-k-batch). 이 복합 OPEN의 다른 항목은 유지한다.

2026-10-13 N1/N2=1: 비관리자 Trainer 본인 PT 내역의 수업별 금액과 현재 다른 Home Branch Trainer의 자기 지점 수업 금액은 Performed Branch Admin에게 공개하지 않는다. 일반 지급/수업 연결 지원 보상 모두 적용하고 기존 PT 기록 조회/정정과 금액 열람을 분리한다. 현재 Home 기반 기존 관리자 보상·정산 업무·Master Organization/겸임 독립 Scope, CompSetting/월 정산/지점 비용 보고 제한을 유지한다. 등록/중첩/직접 ID·제공되는 집계/감사/오류 등 Backend 우회 노출을 막고 비공개를 가짜 0원/원본 삭제/재계산으로 표현하지 않는다. 다른 공개 필드/상태·계산 근거/최소 응답/인가·현재 권한/소속 변경 경합은 후속으로 이 복합 OPEN은 유지한다. BR-PAY-021, PR-008/029/030, NFR-001/005; V-108/109 예정; [N 승인](product-decisions.md#review-20261013-n-batch).

2026-10-13 S1/S2=1 부분 해결: 이전 정산 확정본·해제/재확정 이력과 Rate/Fixed Amount/Base Salary 변경 이력은 Master 자기 Organization/조회 시점 현재 Trainer Home Branch Admin이 확인한다. 이전 소속 이력도 현재 관리자가 조회하며 과거 Home/Performed만으로 권한을 유지하지 않는다. 원래 금액/버전·감사 사실/당시 Context를 보존한다. 비관리자 금액 기밀성·겸임 독립 Scope·인증/계정 관리 감사 Master 전용은 유지한다. 추가 공개 필드/최소 계약·다른 업무 감사/정산 조건·저장/보존 때문에 Status는 OPEN이다. [S 승인](product-decisions.md#review-20261013-s-batch); BR-PAY-023; V-118/119 미구성·미실행.

2026-10-13 U1=1 부분 해결: 수동 만료 Pass의 담당도 기존 Master Organization/처리 시점 Member 현재 Home Branch Admin 범위에서 같은 Organization 실제 활성 Trainer로 교체할 수 있다. 만료 상태/잔여·발급 조건/시각·과거 수행/지급·정산을 보존하고 자동 만료 해제/횟수 부여·새 수업 사용은 허용하지 않는다. 기존 감사·M2 현재 담당 조회/이전 담당 다른 관계 없는 일반 조회 비복원·독립 관리자 Scope를 유지한다. 다른 상태/역사 사실·최소 선택/인가 계약/경합 때문에 Status는 OPEN이다. [U 승인](product-decisions.md#review-20261013-u-batch); BR-OPS-008/005; V-122 미구성·미실행.

<a id="arch-002"></a>
## ARCH-002. 계정 수명 정책

Question / TODO: 승인된 정책을 재질문하지 않고 실제 계정/역할 상태·운영 설치/본인확인·Passkey 등록/분실/복구 및 비상 승인/실행 자격·감사/철회·보존·최소 계약/경합을 구체화한다. AB3 reset 링크30분, AB4 운영 관리자 비밀번호 뒤 사용자 검증 Passkey, AB5 전체 Master 로그인 불가 시 업무책임자 승인/별도 시스템 운영담당자 실행은 확정됐다. K3/X1 S1 관리자 인증/지점 접근 제어·정확한 발급 결과 조회/설정 대기 재발급과 후속 수명/Trainer 분리, Master 분실 시 S1중단·운영 전 MFA/복구 검증 및 기존 현재 인가/마지막 Master 보호/감사는 유지한다. 구체 API/소유권/UoW/잠금은 PROPOSED이며 별도 구현 지시가 필요하다.

Related decisions / requirements: PD-019; PR-001/021/026/028. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Authentication/Authorization 설계

확정된 경계: 기존 계정/암호 이관과 기본 고정 자격증명은 요구하지 않는다. 인증 기술 선택은 이번 작업 아님.

2026-10-10 사용자 결정 — 최초 비밀번호 설정: Master가 관리자·Trainer 계정을 발급한 뒤 일회용 비밀번호 설정 링크를 대상자에게 전달하고, 대상자가 직접 비밀번호를 설정한다. 긴 토큰의 수동 입력을 기본 사용자 흐름으로 요구하지 않는다. 이 결정은 최초 설정 방식에 한정하며 링크 전달 채널·유효기간·재발급, 활성 계정의 비밀번호 재설정, 최초 Master 준비·복구와 나머지 계정 수명 정책은 미정이다. ARCH-002는 부분 해결 상태로 OPEN을 유지한다.

Status: OPEN

확인 주체: 사용자/업무 책임자와 해당 후속 단계 담당자. 답변·기한은 미정.

2026-10-12 사용자 확정(Operator 계정 발급과 최초 지점 지정 권한 질문의 1번): Master Admin은 자신의 Organization 범위에서, Branch Admin은 자신의 단일 관리 Branch 범위에서 새 Operator 계정을 발급하고 그 한 지점을 최초 업무 Branch로 지정할 수 있다. Branch Admin의 타 지점 Operator 발급은 허용하지 않는다. Backend는 처리 시점의 검증된 현재 Caller 역할/Organization·관리 Branch와 대상 Branch의 실제 Organization 관계를 확인하며 직접 ID·위조 role/branch_id·과거 권한으로 범위를 우회할 수 없다. Operator 단독·Trainer 단독의 로그인 계정 발급은 허용하지 않는다(BR-OPS-011, PD-019, PR-021/030, NFR-001/004, MB-004, ARCH-001/002).

기존 사용자 일관성 지시(2026-10-11) 적용: 이번에 허용된 Operator 발급에도 기존 최초 비밀번호 설정 방식을 사용한다. 권한 있는 발급 관리자가 일회용 비밀번호 설정 링크를 대상자에게 전달하고 대상자가 직접 설정한다. 허용 범위 내 Branch Admin 발급에 별도 Master 승인 대기를 추가하지 않는다. 고정/임시 평문 비밀번호를 계정에 넣거나 긴 토큰 수동 입력을 기본 흐름으로 요구하지 않는다. 최초 설정 링크 30분/단일 사용·재발급 시 이전 링크 폐기는 A4로 해결됐다. 전달 채널/수신자 확인·활성 계정 재설정·나머지 계정 수명 상세는 ARCH-002의 게이트를 유지한다.

초기 Master Bootstrap·Login ID/Password·계정 활성화·중단/복구·기존 계정 재설정/마지막 Master 보호·AuthSession/철회 세부 정책은 기존 미결정 상태를 유지한다. 새 Operator 생성 권한 승인을 이 수명 업무의 위임 승인으로 확대하지 않는다.

2026-10-12 사용자 확정(신규 Trainer 로그인 계정 발급 권한 질문의 1번): Master Admin은 자신의 Organization 전체 Trainer, Branch Admin은 발급 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 단일 관리 Branch인 경우 신규 Trainer 로그인 계정을 발급할 수 있다. Branch Admin은 타 지점 소속 Trainer 계정을 발급할 수 없다. 타 지점 지원 수업·담당 회원/Pass·Performed Branch·Operator 업무 Branch·최초 발급자/과거 소속 사실만으로 이 권한이 생기지 않는다. Operator·Trainer 단독은 본인 포함 로그인 계정 발급 불가이며 관리자 겸임은 현재 관리자 역할의 독립 Scope로 판단한다(BR-OPS-012, PD-019, PR-021/029/030, NFR-001/004, MB-004, ARCH-001/002).

Trainer 신규 발급 Actor/Scope는 해결됐고 기존 일회용 최초 비밀번호 설정 링크/감사·일관성 원칙을 재사용한다. 기존 계정의 Trainer 역할 추가/재연결·관리자 승격/Master 전용 Trainer 이동의 미정 대상/절차·중단/복구·재설정 등 수명 업무 권한과 대상 상태/중복·선택/연결/전달 세부 절차는 기존 게이트다. IAM/Workforce/Organization/Audit 계약·저장/UoW·실패/재시도/동시성은 후속이며 IAM-001 S1/ADR-0004 v1 인증 방식 ACCEPTED는 유지한다. 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 사용자 확정(관리자·Trainer 겸임 계정의 Trainer 비활성화 질문의 1번): Trainer 비활성화는 Trainer 역할에 따른 권한만 중단하며, 같은 계정에 독립적으로 부여된 관리자 역할/Scope와 그 범위의 업무는 유지한다. 계정 전체 로그인 차단은 별도 업무다(BR-OPS-014, PD-011/019, PR-005/026, NFR-001/004, ARCH-001/002, MB-001).

확정된 범위는 겸임 계정의 Trainer 비활성화/전체 계정 차단 분리와 Master Organization 전체·Branch Admin 처리 시점 Trainer 현재 Home Branch 기준의 비활성화 권한이다. Trainer 재활성화의 상태 조합/구체 절차, 재활성화 절차/권한 복구, 관리자 대행 등록의 상세 인가/사실 판정·비활성 Trainer 본인의 직접 등록/이력 열람 예외, 개별 지원 조회 허용 관계의 비활성화/재활성화 시 처리는 후속 결정이다. 구체 상태/역할 저장·Caller 계약·AuthSession 갱신/철회·캐시/처리 중 요청·UoW/동시성은 후속 Architecture이며 ADR-0004 v1 인증 방식은 ACCEPTED/모듈 구체 설계는 PROPOSED를 유지한다. 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 사용자 확정(Trainer 비활성화 권한 질문의 1번): Master Admin은 자신의 Organization 전체 Trainer, Branch Admin은 비활성화 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 단일 관리 Branch인 경우 Trainer를 비활성화할 수 있다. 타 지점 Branch Admin·Operator/Trainer 단독은 불가하며 겸임자는 독립된 현재 관리자 역할/Scope로 판단한다(BR-OPS-014, PD-011/019, PR-005/029/030, NFR-001/004, ARCH-001/002, MB-001).

Backend는 현재 검증된 Caller 역할/Organization·관리 Branch와 실제 대상 Trainer의 Organization/현재 Home Branch를 확인한다. 타 지점 지원 수업/Performed Branch·Member/Pass 담당 관계·Operator 업무 Branch·과거 Trainer 소속이나 계정 발급자였다는 사실만으로 비활성화 권한을 인정하지 않는다. 직접 Trainer ID·위조 role/branch_id/Organization 또는 철회·축소된 권한으로 우회할 수 없다. Trainer 소속 변경 후에는 새 현재 Home Branch로 인가한다. 비활성화 Actor/현재 소속 기준은 해결됐고 재활성화 절차·대상 상태/중복 요청·개별 지원 관계/재활성화 처리·비활성 상태 예외 및 실제 계약/저장/철회·동시성은 후속이다. 겸임 관리자 유지·별도 전체 계정 차단 게이트와 OPEN 전체 상태는 유지한다.

2026-10-12 사용자 확정(잔여가 남은 담당 이용권이 있는 Trainer의 비활성화 질문의 1번): 잔여가 남은 담당 PT Pass가 있어도 Trainer 비활성화를 허용하며 기존 Assigned Trainer 정보는 유지한다. 비활성화 전에 모든 Pass를 다른 Trainer에게 교체하도록 요구하지 않고 자동 담당 해제/재배정도 하지 않는다. 이후 필요할 때 권한 있는 관리자가 BR-OPS-008의 기존 조건/Scope로 담당을 교체한다(BR-OPS-014, PD-007/011, PR-003/005, NFR-001/004, ARCH-001/002, MB-001/003/005, BR-001).

기존 담당 정보 유지와 별도 담당 교체가 해결됐으며 비활성 Trainer의 접근은 계속 차단한다. Member 현재 Home Branch 기반 담당 교체와 Trainer Home Branch 기반 비활성화 권한을 구분하고 잔여/발급 조건·과거 PT/보상을 유지한다. 다른 상태별 교체/사용 조건·개별 지원/재활성화·비활성 상태의 과거 PT 예외 및 구체 저장/현재 인가·UoW/동시성은 후속이다. 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 사용자 확정(담당 Trainer를 새로 지정할 때의 조건 질문의 1번): PT Pass의 담당 Trainer를 새로 지정할 때는 실제 활성 Trainer만 허용한다. 기존 Pass의 담당 교체 및 허용된 새 Pass 발급 흐름에서 담당을 최초 지정하는 경우 모두 적용하며 비활성 Trainer를 미리 배정하지 않는다(BR-OPS-008/014, PD-007, PR-003/005/029/030, NFR-001, ARCH-001, MB-001/003/005, BR-001).

새 지정 대상의 활성 필요조건은 해결됐으며 같은 Organization의 타 지점 허용/기존 행위별 Actor·Scope, 이후 비활성화된 기존 담당 정보 유지·접근 차단을 적용한다. 최초 담당 필수는 해결됐고 나머지 Pass/계정/Branch 상태 조합·최소 선택 정보, 재활성화·개별 지원/비활성 전 수업 예외 및 실제 현재 사실 검증/저장/UoW·지정·비활성화 경합은 후속이다. 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 사용자 확정(비활성화 전 진행했지만 누락된 PT 수업 등록 질문의 1번): Trainer 비활성화 전에 실제로 수행한 미등록 PT 수업은 관리자가 대행 등록하는 경로를 허용한다. 대상 Trainer의 비활성 상태를 유지하며 잠시 재활성화/본인 로그인·담당 재배정을 선행 요구하지 않는다. 실제 수행 Trainer·실제 수업일과 기존 Pass 잔여/정산 조건을 그대로 적용한다(BR-OPS-015, PD-008/011, PR-008/029/030, BR-OPS-003/008/014, BR-PAY-006/011/012).

관리자 대행 경로와 Master Organization/Branch Admin 실제 Performed Branch Scope는 해결됐다. 현재 인가 검증·비활성화 전 실제 수업/담당/소속 사실·시점/확인 불가·최소 선택 정보/사유·증빙과 구체 계약/저장/UoW·경합은 후속이다. 비활성/현재 담당 유지·실제 수행자/수업일·기존 Pass/생성 시점 보상/진행 월 정산·민감 설정 접근 제한을 적용한다. 비활성 Trainer 본인 직접 등록/회원 조회 예외가 아니며 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 일괄 승인 반영: A1–A10과 B1/B2는 위 표 범위로 해결됐다. v1 PG AuthSession+opaque Cookie, 별도 3~64자 ID, 15~128자/조합·주기 강제 없음/흔한 암호 차단, 최초 설정 링크 30분·단일 사용/재발급 철회, 전 역할 idle 30분/absolute 8시간, 복수 기기/현재 로그인만 logout, 관리 역할/관리 Branch 변경 전체 재로그인, Master 전용 계정 전체 차단/복구·관리자 reset, 복수 Master/마지막 사용 가능 Master 보호, 운영 전 관리자 MFA 필수다. JWT는 후속 재검토 후보다. Bootstrap 책임/구체 절차·전달 채널/본인 확인·중요 관리 재인증·반복 시도 제한·실제 기록 수집/접근/보존·MFA/복구 수단·나머지 계약/전이는 미결정/상세 검토로 남는다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch). 이 복합 OPEN의 다른 미결정 항목은 유지한다.

2026-10-12 C 일괄 승인 반영: C1–C8: 5분 이내 중요 관리 재인증 후보 미채택, 계정 15분 5회 실패→15분 대기, 현재 암호 확인 본인 변경/모든 로그인 종료, Master 확정 reset 즉시 기존 암호/로그인 무효, 마지막 Master 일반 reset 차단/별도 비상 복구, Master ID 변경/모든 로그인 종료, Master 인증/계정 감사 열람과 로그인 최소 기록/원문 IP·브라우저 제외가 해결됐다. A5 만료/A10 운영 전 MFA는 유지한다. Bootstrap/수신자 확인·reset 링크 수명/ID 재사용·IP 방어/집계·보존/삭제·복구/MFA 수단·S1/S2 범위/계약/전이는 후속이다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 E 일괄 승인 반영: E1–E6: 제한된 최초1회 설치 명령/첫 Master 본인 암호 설정, 본인 확인 후 권한 있는 관리자 대면/확인된 1:1 연락 링크 전달, ID 대소문자 미구별/이전 ID 원래 계정 예약·다른 계정 재할당 금지/현재 ID만 로그인, 지점 범위 Operator·Trainer 역할 추가/회수, 일반 계정 차단 해제 시 유효 기존 암호로 재로그인 허용이 해결됐다. 운영 설치 자격/담당·확인/전달 절차·reset TTL·ID 구분자/정규화/예약 계약·역할/상태/재부여·AuthSession/실패 집계/IP 방어·미확인 감사/보존/복구/MFA 수단과 S1/S2 범위는 후속이다. [2026-10-12 E 일괄 승인](product-decisions.md#review-20261012-e-batch)

2026-10-12 G 일괄 승인 반영: G1: Branch 비활성은 유효 계정/역할의 로그인 차단 사유로 쓰지 않는다. 계정 차단·Trainer 자체 비활성/철회 역할·만료/폐기 인증 등 기존 제한은 유지하며 Branch 재활성화로 인증을 복원하지 않는다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). 다른 상태/신규 배정·역사 사실/구체 계약·경합 등 나머지 게이트로 이 복합 OPEN은 유지한다.

2026-10-12 K 일괄 승인 반영: K3로 첫 개발은 관리자 인증/지점 접근 제어부터 개발 검증하고 계정 복구·추가 Master·Trainer 연결은 후속으로 분리한다. 운영 전 관리자 MFA·비상 복구 및 전체 v1 의무는 유지하며 개발 검증과 실운영을 구별한다. 구체 계약·남은 계정 수명/실제 기록·보존/운영 상세와 별도 구현 지시는 유지한다. [2026-10-12 K 일괄 승인](product-decisions.md#review-20261012-k-batch). 이 복합 OPEN의 다른 항목은 유지한다.

2026-10-13 X1=1 부분 해결: S1에 현재 Master의 자기 Organization Branch Admin 정확한 Login ID 발급 결과 조회와 PENDING_SETUP의 기존 최초 설정 링크 재발급을 포함한다. account ID 미확보만으로 개발 run을 중단하던 초안을 대체하고 기존 현재 인가·상태/version 재검사·A4 30분 단일 사용/이전 링크 폐기·감사를 유지한다. 원래 token 조회·일반 목록/부분 검색·ACTIVE/DISABLED reset·추가 역할 관리·중복 생성/숨은 자동 재시도는 추가하지 않는다. Master 분실/비상복구/운영 게이트·나머지 수명/역할 상태·최소 계약/경합이 남아 OPEN을 유지한다. [X 승인](product-decisions.md#review-20261013-x-batch); PR-021/027/030; V-126 미구성·미실행.

2026-10-13 AB3–AB5=1 부분 해결: 후속 reset 링크30분·운영 관리자 비밀번호 뒤 Passkey 사용자 검증·비상 업무책임자 승인/별도 시스템 운영담당자 실행을 선택했다. 정상 관리 Scope/추가승인 없음·마지막 Master 보호·S1 개발 우선/분실 중단·운영 전 MFA/복구 검증은 유지한다. 실제 운영 확인/자격·등록/분실/복구·감사/철회·보존/최소 계약이 남아 OPEN이다. [AB 승인](product-decisions.md#review-20261013-ab-batch); V-134–136 미구성·미실행.

2026-10-16 MFA M1/M2 부분 해결: 관리자 계정에 복수 Passkey 등록/로그인 시 하나 사용을 허용하고, 같은 Organization의 다른 정상 Master가 관리자 본인 확인 후 기존 Passkey/모든 AuthSession 폐기·일회용 링크 재등록을 처리한다. Branch Admin 위임/타 조직 접근·비밀번호 reset·계정/회수 역할 자동 복원은 포함하지 않고 AB4 추가 인증/AB5 전체 Master 로그인 불가 비상 복구는 유지한다. 추가 등록/삭제·마지막 인증수단 보호·링크 수명/소비·운영 확인·감사/철회/경합·실제 WebAuthn 검증이 남아 ARCH-002는 OPEN이다. [M1/M2 승인](product-decisions.md#review-20261016-mfa-m-batch); V-135 계획만 갱신, 미구성·미실행.

2026-10-18 MFA M3–M6 부분 해결: 설치/본인 최초 설정 첫 등록·정상 MFA 본인 추가 등록, 다른 유효 Passkey가 없으면 본인 삭제 금지, 분실 재등록 링크30분, 같은 Organization 정상 Master의 추가 Master 신규 발급을 확정했다. 해당 정책은 재질문하지 않고 M1/M2·AB4/AB5·마지막 Master 보호를 유지한다. 등록/삭제/복구·발급의 구체 상태/계약·철회/감사/원자성/경합·운영 본인 확인/전달·실제 검증이 남아 ARCH-002는 OPEN이다([승인](product-decisions.md#review-20261018-mfa-m3-m6); V-135 및 각 후속 검증 미완료).

2026-10-18 MFA M7/M8 부분 해결: 본인 Passkey 삭제 성공 시 현재 기기 포함 모든 로그인 종료·Master 본인 관리자 reset 금지를 확정했다. M4 마지막 key 삭제 금지·C3 현재 암호 확인 본인 변경/다른 정상 Master reset·AB5는 유지한다. 삭제/관리자 reset의 실제 상태·인가/철회/감사/동시성 계약과 운영 확인·실제 검증이 남아 ARCH-002 OPEN을 유지한다([승인](product-decisions.md#review-20261018-mfa-m7-m8)).

<a id="arch-003"></a>
## ARCH-003. 복수 사용 가능 Pass의 상세 경계

Question / TODO: 복수 Pass의 나머지 사용 가능 상태/필요 수량 상한·같은 시각 정밀도/동시 정렬·역사 사실 확인 불가/충돌·상태/취소 복원/최소 계약을 구체화한다. T1/T2로 시스템 신규 발급 완료 시각/과거 날짜 입력·소급 발급 v1 제외·별도 시작일 없이 발급부터 기존 조건 사용이 확정됐다. O1/O2의 다른 담당분 포함 Member 전체 적격 Pass/본인 담당 Pass 없는 개별 지원 등록, FIXED_AMOUNT 우선/FIFO·실제 수업 당시 이미 발급/현재 잔여 > 0·만료 전 실제 수업 지연 등록/현재 만료 유지·판매 중단은 새 발급만 차단 및 M1 발급 오류 정상 새 발급/별도 발급 취소 v1 제외는 유지한다. 이미 확정된 후보 범위와 발급/사용 시작 의미를 재질문하지 않는다.

Related decisions / requirements: PD-007; PR-003. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Architecture/domain modeling

확정된 경계: BR-PAY-006의 FIXED_AMOUNT 2회 + RATE 10회 사례와 FIXED → FIXED → RATE를 지원한다. 복수 Pass 허용 여부를 다시 미정으로 두지 않는다.

Status: OPEN

확인 주체: 사용자/업무 책임자와 해당 후속 단계 담당자. 답변·기한은 미정.

2026-10-12 일괄 승인 반영: B3/B4/B5/B6: 새 Pass 활성 담당 필수·상품 최초 횟수, 관리자 발급 횟수 초과 잔여 추가, 비활성 지점 신규 발급/실제 수업 차단과 기존 Pass 보존은 해결됐다. 다른 가용 상태/과거 사실/시점·상태 조합과 실제 선택/차감·동시성은 후속이다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch). 이 복합 OPEN의 다른 미결정 항목은 유지한다.

2026-10-12 G 일괄 승인 반영: G3/G4: 비활성 발급/Home Branch의 기존 Pass·Member/활성 Trainer는 다른 활성 지점에서 기존 인가/가용·잔여/우선 선택·담당/지원 조건으로 수업할 수 있다. 수동 만료/취소 등 나머지 상태·역사 사실/신규 배정 조건은 후속이다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). 다른 상태/신규 배정·역사 사실/구체 계약·경합 등 나머지 게이트로 이 복합 OPEN은 유지한다.

2026-10-12 J 일괄 승인 반영: J3로 Member 자체 비활성 기간 실제 수업은 다른 Branch/지연 등록으로 우회할 수 없고 새 Pass 발급도 차단한다. 기존 Pass·잔여/과거 결과를 보존하고 같은 Member 재활성화 후 독립 사용 조건을 확인한다. 비활성화 전 실제 수업은 기존 과거 업무 규칙을 유지하며 역사 사실 확인 불가/정정·다른 상태/인가/경합 계약은 후속이다. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch). 이 복합 OPEN의 나머지 항목은 유지한다.

2026-10-13 M1=1: 잘못 발급한 미사용 Pass는 기존 수동 만료로 잔여/원본을 보존하고 기존 정상 발급 권한/조건으로 올바른 Pass를 새로 발급한다. 별도 Pass 발급 취소 기능은 v1 제외다. 과거 PT 취소/복원과 다른 업무이며 만료/해제의 기존 인가·사유/감사/잔여·늦은 등록 조건을 유지한다. 이전 취소 Pass/CANCELLED의 구현 게이트 표현을 별도 발급 취소 v1 요구로 사용하지 않는다. 나머지 역사 사실·상태/조정/단계 계약으로 이 복합 OPEN은 유지한다. BR-OPS-025/004; PR-003·scope; V-106 예정; [M 승인](product-decisions.md#review-20261013-m-batch).

2026-10-13 O1/O2=1 부분 해결: 담당/개별 지원 회원의 본인 실제 수업 등록은 다른 Trainer 담당분을 포함한 전체 적격 Pass의 FIXED_AMOUNT 우선/FIFO 차감이다. 개별 지원은 본인 담당 Pass 없이도 조회/본인 등록을 허용한다. 담당자·Home/Issued/Performed·실제 수행자 보상/금액 비공개 및 기존 상태/잔여·정산 검증은 유지한다. 지원 관계의 지정 전/해제 후 과거 등록 시간 경계·역사 사실과 나머지 공개/계약 때문에 Status는 OPEN이다. [O 승인](product-decisions.md#review-20261013-o-batch); BR-OPS-026; V-110/111 미구성·미실행.

2026-10-13 T1/T2=1 부분 해결: Pass 발급은 시스템 신규 발급 완료 시각 기준이며 과거 발급 날짜 입력/소급 발급은 v1 제외다. 별도 사용 시작일 없이 발급 시점부터 기존 잔여/상태·인가 조건을 적용한다. 실제 구매가 먼저여도 시스템 발급 전 수업에는 그 Pass를 사용하지 않는다. 기존 실제 수업 당시 발급된 후보/FIXED_AMOUNT 우선/FIFO·수동 만료/해제/만료 전 늦은 등록·현재 잔여/정산/보상·원본 보존은 유지한다. 나머지 시각/역사 사실·상태/취소 복원/담당 교체·최소 계약 때문에 Status는 OPEN이다. [T 승인](product-decisions.md#review-20261013-t-batch); BR-OPS-031; V-120/121 미구성·미실행.

<a id="arch-004"></a>
## ARCH-004. 브라우저·운영 품질 상세

Question / TODO: AB6로 Chrome/Edge/Safari 최신2개 안정 주버전 지원 목표는 확정됐다. 실제 Desktop/Tablet/Smartphone OS/기기·버전 매트릭스/지원 갱신·터치/화면/Passkey 인수, 운영 규모/동시 사용자·응답/부하·백업 복구/가용성·운영 책임 사실과 측정/수용 기준을 구체화한다. 지원 목표와 실제 검증 결과를 구별하고 운영 수치/실명·보존기간을 임의 확정하지 않는다.

Related decisions / requirements: PD-005/021; NFR-006/008/009/010/011. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Architecture/NFR 단계, 구현 수용 기준 확정 전

확정된 경계: 주요 업무의 Responsive Web과 Smartphone Trainer Session 등록은 v1 확정이다. 터치·작은 화면의 정보/Action 수행을 검증하며 breakpoint와 지원 환경 상세만 미정이다. PD-021은 OPEN 유지.

Status: OPEN

확인 주체: 사용자/업무 책임자와 해당 후속 단계 담당자. 답변·기한은 미정.

2026-10-12 일괄 승인 반영: A10으로 운영 전 관리자 MFA 필수는 해결됐다. 지원 브라우저·부하/지연·NAT 오탐·백업/복구·가용성 등 품질/운영 기준은 후속이다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch). 이 복합 OPEN의 다른 미결정 항목은 유지한다.

2026-10-13 AB6=1 부분 해결: v1 Chrome/Edge/Safari 최신2개 안정 주버전 지원을 품질 목표로 선택했다. 실제 OS/기기 매트릭스/반응형·Passkey·지원 갱신/부하·운영 복구 검증은 후속이며 현재 통과한 브라우저 목록이 아니다. 남은 품질/운영 기준 때문에 OPEN이다. [AB 승인](product-decisions.md#review-20261013-ab-batch); V-137 미구성·미실행.

<a id="ux-001"></a>
## UX-001. 여러 날짜 Session 일괄 입력 편의

Question / TODO: 해결됨 — I3=1로 v1은 실제 수업별 개별 등록, 여러 날짜 일괄 입력은 후속 보류로 확정했다. 향후 필요 확인 시 별도 채택/확인·오류 UX를 설계한다.

Related decisions / requirements: PD-008; PR-008/015. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: v1 채택 여부 결정 완료; 후속 버전의 별도 채택 전 재검토

확정된 경계: 실제 수업당 개별 원본/1회 차감·동일 일자 별개 수업 허용과 중복 요청 방지는 유지한다. 월 합계 입력/기존 월 복사나 여러 날짜 일괄 요청 API를 v1 기본 기능으로 도입하지 않는다. Smartphone 현장 등록/Responsive Web은 v1 필수다.

Status: CLOSED

확인 주체/승인 근거: 사용자 2026-10-12 I3=1. [2026-10-12 I 일괄 승인](product-decisions.md#review-20261012-i-batch).

<a id="ops-001"></a>
## OPS-001. 신규 운영 시작과 일괄 전환 준비

Question / TODO: 빈 데이터에서 Master Admin·Organization/Branch·계정·기준정보·회원·Trainer·Pass를 새로 생성하는 준비 책임, 업무 시작 기준일, 짧은 검증 기간과 준비완료 판정은?

Related decisions / requirements: PD-006/017/018/019; PR-028. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: deployment/cutover 계획; 실운영 전

확정된 경계: 이관과 장기 이중 입력은 하지 않는다. 기존 이용자의 남은 업무를 누가 어떻게 새로 설정할지 확인하되 기존 DB 복사로 대체하지 않는다.

Status: OPEN

확인 주체: 사용자/업무 책임자와 해당 후속 단계 담당자. 답변·기한은 미정.

2026-10-12 일괄 승인 반영: A10은 운영 전 관리자 MFA 필수로 확정됐다. B6의 지점 비활성화와 A9의 마지막 Master 보호는 운영 계정/데이터를 임의 삭제하는 근거가 아니다. 실제 Bootstrap 책임/전달·비상복구·배포/준비 검증은 남으며 로컬 개발/첫 기능 검사 허용을 운영 승인으로 사용하지 않는다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch). 이 복합 OPEN의 다른 미결정 항목은 유지한다.

2026-10-12 C 일괄 승인 반영: C5: 마지막 사용 가능 Master의 일반 관리자 reset은 거부하고 별도 비상 복구가 필요하다. 현재 암호 확인 본인 변경(C3)과 구별하며 복구 책임/확인 증거·도구/절차·실패 인수는 아직 미정이다. Bootstrap 재실행/DB 초기화를 복구 완료로 취급하지 않는다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 E 일괄 승인 반영: E1/E2: 설치 담당자의 제한된 최초1회 설치 명령/첫 Master 본인 암호 설정과 권한 있는 관리자의 본인 확인/대면 또는 확인된 1:1 연락 링크 전달로 방식은 해결됐다. 담당자 실제 지정·자격 지급/회수/입력·수신자 확인과 전달 운영 절차/실패·실제 설치/백업/비상복구 인수는 아직 필요하다. E6 일반 차단 해제를 침해 복구나 Bootstrap 재실행 허용으로 해석하지 않는다. [2026-10-12 E 일괄 승인](product-decisions.md#review-20261012-e-batch)

<a id="legal-001"></a>
## LEGAL-001. 최소 개인정보·보존·필요 삭제

Question / TODO: Member/Trainer 전화번호 형식/정규화·추가 항목별 수집 필요성/행위별 공개·개인정보 및 감사기록 보존/필요 삭제와 과거 이력 보존의 관계를 구체화한다. R1 Trainer 전화번호 필수/일반 수정 필수값 유지·Login ID/본인인증 수단으로 사용하지 않음은 확정됐다. I2 회원 이름/전화번호/단일 Home 필수·생년월일/성별 v1 제외, Trainer의 인가된 담당/지원 회원 전체 전화번호 읽기·회원 번호 중복 허용/별도 식별도 유지한다. R2 자기 지점 지점명/대표 연락처 수정 인가는 다른 개인정보/공개·보존/삭제 정책 승인이 아니다.

Related decisions / requirements: PD-011/022; NFR-004/005. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: 항목·열람은 관련 설계 전; 기간·법적 정책은 별도 검토 및 실운영 전

확정된 경계: 최소 저장·권한 제한·중요 행위 감사는 승인됨. 구체 기간과 Hard Delete 예외를 임의로 정하지 않는다.

2026-10-12 사용자 확정(Trainer의 회원 전화번호 조회 질문의 1번): Trainer는 기존 조회 권한이 확인된 담당 회원과 개별 허용 지원 회원의 등록된 전체 전화번호를 조회할 수 있다. 부분 마스킹된 번호만 허용하는 정책으로 제한하지 않는다. 담당 Pass 잔여가 모두 0이어도 기존 회원 조회 권한이 유지되면 전화번호도 같은 범위에서 조회한다. Backend는 전화번호를 반환하는 조회마다 현재 Caller/Organization·담당 또는 지원 관계를 검증하고 미담당/미허용 회원·타 Organization 번호를 공개하지 않는다. 지원 해제 후 별도의 유효한 담당/관리 권한이 없으면 해당 번호도 공개하지 않는다. 관리자 겸임자의 별도 관리 Scope는 유지한다. 이번 승인은 전화번호 읽기이며 수정/일괄 내보내기·다른 개인정보/개별 Pass·다른 Trainer PT/보상 공개 권한을 추가하지 않는다. 전화번호 필수 수집/형식·중복/검증과 나머지 필드/보존·조회 계약은 후속이다(BR-OPS-005, PR-002/029/030, NFR-001/005, LEGAL-001). 전체 번호 읽기 허용은 전화번호 필수 등록이나 보존 기간·다른 정보/행위 승인이 아니므로 LEGAL-001은 OPEN을 유지한다.

Status: OPEN

확인 주체: 사용자/업무 책임자와 해당 후속 단계 담당자. 답변·기한은 미정.

2026-10-12 사용자 확정(회원 등록 시 전화번호 필수 여부 질문의 1번): 새 Member 등록을 완료하려면 전화번호를 반드시 입력해야 한다. 전화번호가 누락되거나 빈 문자열·공백만 있으면 등록을 완료하지 못한다. 임의 번호나 기본값으로 필수 입력을 대신하지 않는다. 이 결정은 전화번호 필수 입력이며 번호 중복 허용/금지·구체 형식/정규화·문자/본인 확인, 다른 개인정보 필수 수집이나 등록/수정 Actor 권한을 확정한 것은 아니다. 기존 Role·Data Scope와 Trainer의 인가된 담당/지원 회원 전체 전화번호 읽기는 유지한다(BR-OPS-006, PD-022, PR-002, NFR-005, LEGAL-001).

기존 사용자 일관성 지시 적용(2026-10-11): 일반 회원정보 수정에서도 필수 전화번호를 누락·빈 문자열·공백만인 값으로 지우는 변경은 허용하지 않는다. 전화번호를 변경하지 않는 다른 정보 수정에서는 기존 번호를 유지한다. 이는 등록 필수 요건을 일반 수정에 동일 적용한 것이며 전화번호 수정 권한을 새로 부여하거나 특정 API 입력 형태를 승인한 것은 아니다. 법적·운영상 필요한 개인정보 삭제/보존 예외는 LEGAL-001에서 별도 결정한다.

2026-10-12 사용자 확정(회원 간 전화번호 중복 허용 여부 질문의 1번): 같은 Organization의 여러 Member가 같은 전화번호를 사용할 수 있다. 가족 등 공유 연락처로도 각각 등록하며 전화번호가 같다는 이유만으로 신규 등록을 거부하지 않는다. Member는 전화번호와 별개의 고유 식별자로 구분한다. 동일 번호를 같은 회원으로 자동 병합하거나 Pass·PT 진행/지급 이력·담당/지원 관계를 공유하는 근거로 삼지 않는다. 전화번호 필수 입력과 기존 Role·Data Scope는 유지한다(BR-OPS-006, PD-022, PR-002, NFR-005, LEGAL-001).

기존 사용자 일관성 지시 적용(2026-10-11): 전화번호를 변경할 권한이 있는 Actor의 일반 수정에도 같은 중복 허용 원칙을 적용한다. 다른 Member가 이미 쓰는 번호라는 이유만으로 변경을 거부하지 않되 필수 번호 비움 금지와 현재 업무 인가는 그대로 적용한다. 이 결정으로 등록/수정 권한을 추가하지 않는다.

전화번호로 검색하는 경로가 제공되면 조회 권한이 있는 회원 집합 안에서 동일 번호의 회원을 각각 식별하고, 전화번호 일치만으로 한 명으로 단정하지 않는다. 미인가 회원의 존재·번호·지점이나 조회 권한을 중복 검사/검색으로 노출하지 않는다. 중복 허용은 별도 경고 화면·중복 회원 병합 기능·Member 로그인/본인 인증 승인이 아니며 번호 형식/정규화·다른 수집 항목·보존/필요 삭제 및 구체 응답·저장 계약은 후속이다.

2026-10-12 C 일괄 승인 반영: C7/C8: 자기 Organization의 Master만 인증/계정 관리 감사 열람, 로그인 감사는 계정·시각·행위·결과 최소 기록/원문 IP·브라우저 정보 제외다. 제한 방어의 일시적 IP 처리와 일반 보상/업무 감사 권한은 별개다. 미확인 계정 사건 표현·보존/백업/필요 삭제/운영 접근은 후속이다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 E 일괄 승인 반영: E2는 관리자가 확인된 수신자에게 대면/1:1로 설정 링크 전달하는 방식이며 시스템 이메일 자동 발송이나 이메일 필수 수집을 채택하지 않는다. E3/E4 Login ID 비교/이전 ID 예약도 구현 시 필요한 접근/보존을 설계한다. 실제 운영 연락처/링크/비밀은 문서/일반 로그 금지이고 인증 사건/예약 이력·보안 상태/백업의 보존/필요 삭제는 여전히 후속이다. [2026-10-12 E 일괄 승인](product-decisions.md#review-20261012-e-batch)

2026-10-12 I 일괄 승인 반영: I2=1: 이름/전화번호/Home Branch 필수, 생년월일/성별 v1 제외(BR-OPS-020). 다른 필드·행위별 공개/전화번호 형식/보존/필요 삭제는 계속 OPEN이다. [2026-10-12 I 일괄 승인](product-decisions.md#review-20261012-i-batch).

2026-10-13 R1/R2=1 부분 해결: Trainer 전화번호는 필수 기본정보이며 Branch Admin의 자기 지점 지점명/대표 연락처 수정과 중요 변경 감사를 허용한다. 기존 신규/현재 Home 인가·계정/보상 권한 분리·Branch 구조/상태/관리자 배정/과거 지점 사실은 유지한다. 형식/정규화·다른 필드/공개·보존/이력/계약 때문에 Status는 OPEN이다. [R 승인](product-decisions.md#review-20261013-r-batch); BR-OPS-029/030; V-116/117 미구성·미실행.

<a id="br-009"></a>
## BR-009. 월 정산 추가 지표·확인 절차

Question / TODO: 월 정산 나머지 구성 유효성·증빙/추가 계산 근거·버전별 최소 필드·월 대상 사실/선정 검증과 지점 비용 보고의 최소 Trainer 식별/응답·역사 비용/버전·미완료 식별/완료 증거·동시 조회 계약을 구체화한다. Z1로 Master 보고의 지점/네 비용 항목 소계·총계/Trainer별 해당 지점 기여 금액 상세 수준이 해결됐다. Y1/Y2 종료 월·미완료 영향 없는 최신 유효 확정본 합산/미확정·해제 중·소속 오류 정정 대기 제외·표시와 W2 영향 정정 완료 후 확정/재확정·원본 자동 변경 금지/기존 권한·사유·해제/정정/같은 월 재확정·이전본 보존을 유지한다. 현재 Home 전체 정산/이력 공개·H4/N1/N2/C7 기밀성·L1 종료 월 확정/당월 Trainer 정산 조회·미입력 지원 보상 차단/I4 연간·추이 제외도 유지한다. AB1/AB2 정산 구성 기반 대상 자동 선정/월전체 비활성·명시기본급0·무활동·미완료없음의 새 확정 의무 제외는 해결됐다. 기존 이력/미완료/비활성 기본급 자동0 금지는 유지한다. 승인된 보고 기간/집계/상세 수준을 재질문하지 않는다.

2026-10-11 사용자 확정(월 정산을 처음 확정할 권한 질문의 1번 답변): 월 정산의 최초 확정은 Master Admin에게 Organization 전체 Trainer, Branch Admin에게 확정 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 직접 확정한다. 이는 기존 보상 설정·금액 수정 권한에서 자동으로 도출한 권한이 아닌 별도 사용자 결정이다. 금액 미입력 지원 수업의 해당 Trainer·월 확정 차단을 유지한다. 상세 정산 공개(MB-006)·지점 귀속(MB-010)과 나머지 확정 조건·마감/정정 절차는 미정이다. BR-PAY-016 및 PR-010에 추적한다.

Related decisions / requirements: PD-012; PR-010/011; BR-007/012/013.

확정된 월의 기본급 오류는 해당 Trainer·월의 확정 해제 → 해당 월 적용 기본급 정정 → 동일 월 재확정으로 처리하고 이전 확정본은 이력으로 보존한다. 현재 설정 변경에 따른 자동 갱신과 구별한다. 기본급 오류 정정의 확정 해제·재확정은 Master Admin에게 Organization 전체, Branch Admin에게 각 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 처리한다. 확정된 월의 기본급 오류 정정에서 확정 해제와 해당 월 기본급 수정 모두 사유가 필수다. Master Admin·Branch Admin 및 관리 범위 안 본인 건에 동일하게 적용한다. 해제 사유·해제자·시점과 변경 전후 기본급·수정 사유·수정자·시점을 이력으로 남긴다. 기본급 오류 정정은 대상 Trainer의 해당 월 정산에만 적용하며 현재·미래 기본급 설정과 다른 월 정산은 유지한다. 지속적인 기본급 변경은 별도로 적용 시작 월을 지정하는 기존 흐름을 따른다. 입사·퇴사·휴직이 있는 달의 적용 기본급은 관리자가 해당 Trainer·월의 금액을 직접 지정한다. 예를 들어 월 기본급 설정이 2,500,000원이어도 해당 월만 1,500,000원을 적용할 수 있으며, 이 지정으로 현재·미래 기본급 설정과 다른 월 정산은 변경하지 않는다. 월별로 수동 지정한 기본급은 이후 일반 기본급 설정이 변경되어도 유지한다. 일반 설정 변경의 미확정 정산 자동 반영은 수동 지정이 없는 월에 적용하며, 수동 지정 월의 금액을 바꾸려면 관리자가 해당 월 금액을 직접 수정한다. 미확정 월의 기본급을 최초 수동 지정하거나 다시 수정할 때 모두 사유가 필수다. 사유가 없는 요청은 거부하고 요청 직전의 수동 지정 여부·적용 금액·월 합계를 유지한다. 대상 Trainer·월, 지정/수정 전후 금액·사유·처리자·처리 시점을 이력으로 남긴다. 미확정 월 기본급의 최초 수동 지정·수정은 Master Admin의 Organization 전체, Branch Admin의 각 처리 시점 대상 Trainer 현재 Home Branch가 관리 Branch와 일치하는 범위에서 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 직접 처리한다. 추가 사용자 확정(2026-10-11): 해당 월 기본급은 권한 있는 관리자가 사유를 남기면 0원으로 명시적으로 수동 지정할 수 있다. 수동 지정한 0원은 미입력과 구분하며, 미입력이나 누락된 일반 설정을 자동으로 0원으로 대체하지 않는다. 해당 월 기본급에만 적용하고 다른 유효 지급·추가실적은 기존 규칙대로 합산한다. 미리 등록할 수 있는 미래 적용 시작 월의 범위와 월별 수동 지정 금액의 나머지 입력 제약 등은 BR-012/BR-010 OPEN이다.

Required timing: 추가 통계 채택 전; 정산 수명·정정 상세 설계 확정 전.

확정된 경계: 기본급 지원·별도 표시와 월 정산 합산은 CLOSED(PD-009/012). Monthly Settlement = 해당 월 적용 Base Salary + 유효한 Session Payment 합계 + 유효한 Additional Performance 합계다. Trainer·대상 월·적용 기본급·Session 수·Session Payment 합계·추가실적 내역/합계·월 정산 합계를 구분한다. 2,500,000원 + 1,200,000원 + 150,000원 = 3,850,000원이며 여러 지점 수업으로 동일 월 기본급을 중복 가산하지 않는다. 타 지점 수업의 보상 전체는 Additional Performance로 반영하며 일반 Session Payment를 별도로 합산하지 않는다(MB-009 CLOSED, 2026-10-10 사용자 정정). 12개월 고정 평균은 요구하지 않는다. 보상 설정 변경의 별도 승인 없음은 월 정산 승인 절차 결정이 아니다. 2026-10-10 사용자의 미입력 월 정산 질문 1번 답변으로 해당 Trainer의 해당 월 정산 대상 지원 수업에 금액 미입력 건이 하나라도 있으면 그 Trainer·월 정산을 확정할 수 없다. 타 지점 지원 수업 보상은 권한 있는 관리자가 사유를 기록하면 0원으로 명시적으로 확정할 수 있다. 사유 없는 0원 입력은 보상 확정이 불가하다. 사유를 남기고 확정한 0원은 금액 미입력이 아니므로 그 건으로 월 정산 확정을 차단하지 않는다. 다른 미입력 건이 남으면 기존 차단 조건을 유지한다. 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin에게 Organization 전체, Branch Admin에게 대상 Trainer Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안의 본인 건도 허용하고 변경 이력을 남긴다. 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin·Branch Admin 모두 관리 범위 안에서 본인 건을 포함해 별도 승인 없이 저장 성공 즉시 반영한다. Master나 다른 관리자의 승인 대기를 두지 않으며 권한 검증과 변경 이력을 유지한다. 월 정산 확정 전 지원 수업 보상 금액의 모든 수정에는 변경 사유가 필수다. 양수 간 변경·0원에서 양수로 변경·양수에서 0원으로 변경 모두 적용하며, 사유 없이는 금액을 수정할 수 없다. 변경 전후 금액·변경 사유·수정자·수정 시점을 이력으로 남긴다. 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer의 지원 수업 보상 정정을 위해 월 정산을 확정 해제·재확정할 때는 Master의 별도 승인을 두지 않는다. Master 승인 대기 단계 없이 관리 범위 안에서 직접 처리하며 이전 확정본과 해제·재확정 이력 및 감사를 유지한다. 지원 수업 보상 정정의 월 정산 확정 해제에는 사유가 필수이며, 사유 없이 해제할 수 없다. 사유·해제자·시점을 이력으로 남긴다. 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 남은 정정·취소 절차는 BR-009/013 등 관련 OPEN을 따른다. 미입력 수업을 제외하거나 0원으로 간주해 확정하지 않는다. 이미 완료한 진행 기록·Pass 차감은 유지한다. 차단 범위는 해당 Trainer·월이며 다른 Trainer·월로 확대하지 않는다. 모든 금액 입력 완료는 이 차단 조건의 해소이며 월 정산 자동 확정이나 나머지 확정 조건의 충족을 뜻하지 않는다. 타 지점 지원 수업 보상은 권한 있는 관리자가 사유를 기록하면 0원으로 명시적으로 확정할 수 있다. 사유 없는 0원 입력은 보상 확정이 불가하다. 사유를 남기고 확정한 0원은 금액 미입력이 아니므로 그 건으로 월 정산 확정을 차단하지 않는다. 다른 미입력 건이 남으면 기존 차단 조건을 유지한다. 최초 월 정산 확정 권한과 별도 Master 승인 없음은 아래 2026-10-11 사용자 결정으로 확정했다. 나머지 확정 조건과 마감/정정 절차가 남아 BR-009 전체는 OPEN이다. 추가 연간 통계는 I4로 v1 제외/후속 보류됐으며 기존 월 정산/지점 비용 보고서는 유지한다.

2026-10-10 사용자 확정(월 정산 확정 후 지원 수업 보상 오류 처리 질문의 2번 답변): 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 이전 확정본의 적용 기본급·구성 금액·합계를 덮어쓰거나 삭제하지 않으며 이전본과 재확정본을 구분한다. 예를 들어 9월 지원 수업 보상 30,000원의 오류를 35,000원으로 정정할 때 9월 정산의 확정 해제 → 지원 수업 보상 금액 정정 → 9월 정산 재확정으로 처리하고 이전 30,000원 반영 확정본을 보존한다. 금액 정정 시 PT 진행 사실·Pass 차감을 재실행하거나 현재 Rate/Fixed Amount/Base Salary를 이유로 과거 확정 일반 지급·기본급을 자동 재계산하지 않는다. 재확정에도 해당 Trainer·월의 미입력 지원 수업 차단 등 승인된 확정 조건을 적용한다. 이번 결정은 지원 수업 보상 금액 오류의 정정 경로와 이전 확정본 보존에 한정한다. 당시 미결정이었던 지원 수업 정정의 해제·재확정 권한은 아래 후속 사용자 결정으로 확정했다. 다른 정정/취소 및 실제 지급과의 대사·차액 처리 상세는 미정이다.

2026-10-10 사용자 확정(지원 수업 보상 정정의 월 정산 확정 해제·재확정 권한 질문의 2번 답변): 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. 수업의 Performed Branch만으로 다른 Home Branch Trainer의 정산 확정 해제·재확정 권한을 얻지 않는다. 관리자 권한이 없는 Operator·Trainer는 이 작업을 수행할 수 없다. 해당 Trainer·월의 확정 해제 → 금액 정정 → 동일 월 재확정과 이전 확정본 보존은 유지한다. 이 결정은 지원 수업 보상 금액 오류 정정에 한정하며 최초 월 정산 확정 권한이나 전체 정산 공개 범위(MB-006)를 새로 확정하지 않는다. 위 지원 수업 보상 정정의 현재 Home Branch 권한 기준은 아래 후속 사용자 결정으로 확정했다.
2026-10-10 사용자 확정(지점 관리자의 지원 수업 보상 정정 시 월 정산 확정 해제·재확정의 별도 승인 질문의 1번 답변): Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer의 지원 수업 보상 정정을 위해 월 정산을 확정 해제·재확정할 때는 Master의 별도 승인을 두지 않는다. Master 승인 대기 단계 없이 관리 범위 안에서 직접 처리하며 이전 확정본과 해제·재확정 이력 및 감사를 유지한다. 기존 Master Organization 범위·Branch Admin 대상 Trainer Home Branch 기준과 범위 밖 접근 거부는 유지한다. 해당 Trainer·월의 확정 해제 → 금액 정정 → 동일 월 재확정 순서와 재확정 시 미입력 지원 수업 차단 등 승인된 확정 조건도 유지한다. 이번 결정은 위 정정의 별도 Master 승인 생략에 한정하며 최초 월 정산 확정 권한/승인, Trainer 신청 승인, 다른 정정/취소 또는 정산 공개 범위로 확대하지 않는다. 확정 해제 사유 필수는 아래 후속 사용자 결정으로 확정했다. 위 지원 수업 보상 정정의 현재 Home Branch 권한 기준은 아래 후속 사용자 결정으로 확정했다.

2026-10-10 사용자 확정(지원 수업 보상 정정 시 월 정산 확정 해제 사유 질문의 1번 답변): 지원 수업 보상 정정의 월 정산 확정 해제에는 사유가 필수이며, 사유 없이 해제할 수 없다. 사유·해제자·시점을 이력으로 남긴다. Master Admin·Branch Admin 모두에 적용한다. 기존 Master Organization 범위·Branch Admin 대상 Trainer Home Branch 기준, Branch Admin의 별도 Master 승인 없음, 이전 확정본 보존과 해제·정정·동일 월 재확정 경로를 유지한다. 금액 수정의 변경 사유 필수도 유지한다. 사유 없는 해제 요청은 기존 확정 상태·확정본·보상 금액을 변경하지 않는다. 이번 결정은 위 지원 수업 보상 정정의 확정 해제에 한정하며 다른 정정/취소 정책으로 확대하지 않는다. 구체 입력 화면·저장 구조는 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(지점 이동 후 과거 지원 수업 보상 정정·정산 해제/재확정의 Home Branch 기준 질문의 1번 답변): 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 9월 수원 소속 Trainer가 10월 강남으로 이동한 뒤 9월 지원 수업 보상을 정정하는 예에서는 강남 Branch Admin에게 해당 정정과 월 정산 확정 해제·재확정을 허용하고, 별도 Master 권한이 없는 수원 Branch Admin에게는 과거 소속만을 근거로 허용하지 않는다. 과거 수업의 Performed Branch·수업 사실·이전 확정본·기존 이력은 보존한다. 기존 관리 범위 검증·Branch Admin의 별도 Master 승인 없음·금액 수정 사유 및 확정 해제 사유 필수·감사 정책을 유지한다. 이번 결정은 지원 수업 보상 금액 정정과 해당 월 정산 해제/재확정의 인가 기준에 한정한다. 다른 추가실적 최초 등록/정정의 이동 기준, Trainer 이동 자체의 적용 시점·절차, 비용 귀속·정산 공개(MB-010/006)는 미결정으로 남긴다. 당시 미정이었던 최초 월 정산 확정 권한과 별도 Master 승인 없음은 2026-10-11 후속 사용자 결정으로 확정했다.


Status: OPEN

지원 수업 외 추가실적 월 귀속 경계(2026-10-11 사용자 확정): 지원 수업 외 실적은 실제 발생 월의 Trainer 정산분으로 귀속하며 등록 월로 이월하지 않는다. 당시 미정이었던 확정된 발생 월 후등록은 아래 후속 결정으로 해당 Trainer·월의 해제 → 등록 → 재확정과 이전 확정본 보존으로 확정했다. 이 흐름의 해제/재확정 본인 건 허용·별도 승인 없음도 후속 사용자 결정으로 확정했다. 남은 정정/취소 상세는 BR-013과 함께 별도 결정한다. 이 월 귀속 결정으로 확정본을 자동 변경하거나 기존 지원 수업/기본급 정정 절차를 다른 실적 후등록에 자동 적용하지 않는다. BR-009 전체는 OPEN을 유지한다.

2026-10-11 사용자 확정(확정된 월의 누락된 지원 수업 외 추가실적 처리 질문의 1번 답변): 이미 확정된 발생 월의 누락된 지원 수업 외 Additional Performance는 해당 Trainer·월 정산의 확정 해제 → 누락 실적 등록 → 같은 발생 월 재확정으로 반영한다. 이전 확정본은 보존하고 재확정 결과와 구분한다. 확정 상태에 직접 추가하여 이전 확정본을 덮어쓰거나 등록 월/다른 월로 이월하지 않는다. 기존 승인된 확정 조건을 재검증하며 금액 미입력 지원 수업이 남으면 재확정하지 않는다. 등록만으로 자동 재확정하거나 과거 구성 금액을 현재 설정으로 자동 바꾸지 않는다. 이 후등록의 해제/재확정 역할·Scope/소속 기준·본인 건/별도 승인·사유와 단계별 실패/재시도 상세는 별도 OPEN이다. BR-009 전체는 OPEN을 유지한다.

지원 수업 외 실적 등록 및 확정 월 누락분 반영의 해제·재확정은 Master Organization 전체/Branch Admin 각 처리 시점 Trainer 현재 Home Branch 기준으로 인가(Product 확정, 2026-10-11). 단계마다 재검증하며 이전 소속/발생 당시 소속만으로 권한 없음. 발생 월 정산·발생 당시 Home Branch 비용 귀속은 유지. 이 후등록의 해제/재확정 본인 건 허용·별도 승인 없음은 확정(2026-10-11). 기존 실적 정정/취소는 별도 OPEN.

확정 월의 누락된 지원 수업 외 실적 반영을 위한 해제 사유 필수(Product 확정, 2026-10-11). 사유 없는 해제 요청은 거부하고 요청 직전 확정 상태/확정본/기존 실적·정산 구성/금액 유지. 성공 시 대상 Trainer/월·사유·해제자·시점 이력/감사와 이전 확정본 보존. 현재 Home Branch 인가·기존 후등록 순서/월/비용 귀속 유지. 이 흐름의 해제/재확정은 관리 범위 안 본인 건도 별도 승인 없이 허용(2026-10-11).

Branch Admin의 본인이 아닌 소속 Trainer 누락 실적 후등록 해제/재확정은 별도 Master 승인 없음(Product 확정, 2026-10-11). 각 처리 시점 현재 Home Branch 인가·해제 사유 필수·해제 후 등록/동일 월 재확정·이전 확정본/감사·기존 확정 조건/미입력 지원 수업 차단 유지. 관리 범위 안 관리자 본인 건의 해제/재확정 허용·별도 승인 없음도 확정(2026-10-11).

관리 범위 안 관리자·Trainer 겸임자의 본인 누락 실적 후등록 해제/재확정도 별도 승인 없이 허용(Product 확정, 2026-10-11). Master Organization 범위/Branch Admin 각 처리 시점 본인 현재 Home Branch 일치·해제 사유 필수·본인 감사/이전 확정본 보존·기존 후등록 순서/월/비용 귀속·재확정 조건/미입력 지원 수업 차단 유지. Trainer 단독 권한 없음. 비지원 실적의 금액 외 정보 수정/취소 등은 OPEN.

월 정산 확정 전 비지원 추가실적 금액 수정은 Master Organization 전체/Branch Admin 각 수정 시점 Trainer 현재 Home Branch 기준으로 허용(Product 확정, 2026-10-11). 관리 범위 안 본인 건 포함·별도 승인 없음·변경 사유 필수·전후 금액/사유/수정자/시점 이력과 감사. 사유 누락 거부/요청 직전 금액 유지. 발생 월/당시 Home Branch 비용 유지. 수정 금액의 나머지 입력 제약, 금액 외 정보 수정/취소는 OPEN.

지원 수업 외 실적의 확정 후 금액 오류도 해당 Trainer/월 해제 → 양수 금액 정정 → 같은 월 재확정·이전 확정본/구성/이력 보존(2026-10-11 사용자 일관성 지시 적용). Master Organization/Branch Admin 각 처리 시점 현재 Home Branch·본인 건 포함·별도 승인 없음·해제/정정 모두 사유 필수·감사·기존 재확정 조건/미입력 지원 수업 차단 유지. 발생 월/당시 Home Branch 비용 유지. 금액 외 정보 수정/취소·나머지 기간/금액 제약은 OPEN.

2026-10-11 사용자 확정: 확정된 타 지점 수업 취소는 현재 Home Branch 담당자의 해당 Trainer·월 해제 → 실제 Performed Branch 담당자의 기록 취소 → 현재 Home Branch 담당자의 같은 월 재확정으로 처리한다. Master도 전체 흐름을 수행할 수 있다. 기록/금액/월 정산 권한과 이전 확정본/이력을 유지한다. 상세 근거는 BR-007/PD-010/PR-009. 이 취소 순서는 해결됐으며 지급/연계 추가실적·잔여 복원 예외와 단계 계약/경합 등 잔여 항목으로 BR-009는 OPEN이다.

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

2026-10-12 H 일괄 승인 반영: H2–H4=1: 비지원 실적 내용 정정/취소가 확정 정산에 영향을 주면 해당 Trainer/월 각각 해제/처리/재확정·이전본 보존을 따른다. Trainer 단독 본인 월 정산 조회는 v1 제외이고 관리자 겸임의 독립 Scope는 유지한다. 나머지 확인/마감 상세는 후속이다. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch). 이 복합 OPEN의 남은 항목은 유지한다.

2026-10-12 I 일괄 승인 반영: I4=1: 추가 연간 통계 v1 제외/후속 보류(PR-011 OUT-V1). 필수 월 정산과 기존 Master 전용 지점 비용 보고서·기존 권한/이전 확정본 보존은 유지하며 나머지 정산 수명/보고서 상세로 OPEN이다. [2026-10-12 I 일괄 승인](product-decisions.md#review-20261012-i-batch).

2026-10-13 L1=1: 종료된 월만 확정한다. 공통 한국 시간 다음 달 1일 00:00부터 직전 월의 시간 조건을 충족하며 Master 포함 당월/미래 월 조기 확정은 불가하다. 당월은 기존 관리자 범위에서 미확정 조회/검토하고 비관리자 Trainer 공개는 추가하지 않는다. 기존 현재 Trainer Home 기반 인가·지원 보상 미입력 차단/다른 필수 조건·해제/동일 월 재확정·이전 확정본/감사 유지·자동 확정 없음이다. 미래 기본급 적용 시작 월 지정과 구분한다. 나머지 구성/유효성·공개/절차/계약 상세로 BR-009는 OPEN이다. BR-PAY-020, PR-010, NFR-012, V-104 예정; [L 승인](product-decisions.md#review-20261013-l-batch).

2026-10-13 S1/S2=1 부분 해결: 이전 정산 확정본·해제/재확정 이력과 Rate/Fixed Amount/Base Salary 변경 이력은 Master 자기 Organization/조회 시점 현재 Trainer Home Branch Admin이 확인한다. 이전 소속 이력도 현재 관리자가 조회하며 과거 Home/Performed만으로 권한을 유지하지 않는다. 원래 금액/버전·감사 사실/당시 Context를 보존한다. 비관리자 금액 기밀성·겸임 독립 Scope·인증/계정 관리 감사 Master 전용은 유지한다. 추가 공개 필드/최소 계약·다른 업무 감사/정산 조건·저장/보존 때문에 Status는 OPEN이다. [S 승인](product-decisions.md#review-20261013-s-batch); BR-PAY-023; V-118/119 미구성·미실행.

2026-10-13 W1/W2=1 부분 해결: 과거 Trainer Home 오류에 따른 일반/지원 전환은 Master Organization 전용 명시적 정정으로 같은 PT/기존 Pass 차감·최초 생성 시각을 유지한다. 일반은 최초 기록 생성 시점 설정/소비 Pass 발급 조건, 지원은 기존 관리자 범위 수동 추가실적이다. 이전 결과 이력/유효 합계 단일 반영을 보존하고 영향 건 분류/보상·비용 정정 완료 전 해당 Trainer·월 확정/재확정을 차단한다. 소속 정정만으로 기존 확정본 자동 해제/변경 없음·기존 권한/사유·필요한 월 해제/명시적 정정/동일 월 재확정·이전본 보존을 유지한다. 역사 사실·영향/완료 증거·나머지 상태/최소 계약/경합이 남아 OPEN을 유지한다. [W 승인](product-decisions.md#review-20261013-w-batch); BR-OPS-033/PAY-024; V-124/125 미구성·미실행.

2026-10-13 Y1/Y2=1 부분 해결: Master 전용 지점 비용 보고서는 한국 시간 기준 종료된 월만 조회하고 각 Trainer·월의 미완료 영향 없는 현재 유효 최신 확정본만 합산한다. 미확정/확정 해제 중/과거 Home 오류 영향 정정 대기 Trainer월은 합계 제외/미완료 현황 표시하며 전체 월 비용 완성이나 0원으로 취급하지 않는다. 기존 당월 Trainer 월 정산 조회/비용 귀속·과거 확정본 보존/자동 변경 금지·권한/사유·해제/정정/재확정은 유지한다. 상세 보고 항목/월 대상 집합·미완료 식별/역사 사실·비용 버전/최소 계약·동시 조회 때문에 OPEN을 유지한다. [Y 승인](product-decisions.md#review-20261013-y-batch); BR-PAY-025; V-127/128 미구성·미실행.

2026-10-13 Z1=1 부분 해결: Master 자기 Organization 전용 지점 비용 보고서의 지점별 합계/기본급·일반 PT 수당·지원 수업 보상·기타 추가실적 소계와 해당 지점 비용에 기여한 Trainer별 항목/금액 상세를 제공한다. 기존 귀속/한 번 합산과 Y1/Y2 종료 월/미완료 영향 없는 최신 유효 확정본·미완료 제외/표시를 상세/집계에 함께 적용한다. Trainer 월 전체 지급액을 각 지점에 복제하지 않고 현재 설정/소속으로 과거 비용을 다시 계산하지 않는다. 최소 식별/응답·월 대상/미완료·역사 비용/버전·동시 조회 계약이 남아 OPEN을 유지한다. [Z 승인](product-decisions.md#review-20261013-z-batch); BR-PAY-025; V-129 미구성·미실행.

2026-10-13 AB1/AB2=1 부분 해결: 설정/유효 수업·지원 보상대기/추가실적 기반 월 대상 자동 선정과 확인된 월전체 Trainer 비활성·명시 기본급0·무활동·미완료없음의 새 확정 의무 제외를 적용한다. 기존 이력/미완료·현재 Home 인가/확정·비용 보고 조건을 유지하고 현재상태/기존정산행만으로 누락·자동0/자동확정을 하지 않는다. 대상/역사 사실·조건 증거·최소 계약/경합이 남아 OPEN이다. [AB 승인](product-decisions.md#review-20261013-ab-batch); BR-PAY-026; V-132/133 미구성·미실행.

<a id="br-010"></a>
## BR-010. 지급 계산 입력값 검증

Question / TODO: Product Session Count·Price, 금액별 상한/저장 표현·검증/오류 계약과 다른 미결정 항목의 누락/계산 불가 처리를 구체화한다. Q1/Q2로 Trainer 최초 등록 완료의 세 보상 값/기본급 시작 월 필수 입력, 일반 Fixed Amount/Base Salary의 0원 이상 정수 원/음수·소수·누락 거부가 확정됐다. Rate 0~100% 정수·누락 기본값 금지와 지원 수업/월별 수동 기본급의 사유 필수 0원·기타 추가실적 양수 규칙은 유지한다. 일반 설정의 명시적 0원/최초 입력을 다시 미결정으로 두지 않는다. 다른 금액 항목/월 범위·최소 계약은 해당 게이트를 따른다.

확정된 경계: 지급 값은 Trainer 기준이며 RATE 결과의 1,000원 올림, Rate 0~100% 정수 및 일반 Fixed Amount/Base Salary 0원 이상 정수 원은 확정이다. Q1의 최초 등록 완료에는 세 보상 값/기본급 시작 월 명시 입력과 기존 최초 감사가 필요하다. 누락을 임의 0/예시 값/현재 월로 대체하지 않는다. 기존 현재 Home 관리자 Scope·신규 생성 지급/과거 확정 결과 보존·다른 업무별 0원/양수 조건은 유지한다. 금액 상한/다른 입력값과 오류·저장/월 범위 계약은 후속이다.

2026-10-10 사용자 확정(타 지점 지원 수업 보상 0원 허용 질문의 2번 답변): 타 지점 지원 수업 보상은 권한 있는 관리자가 사유를 기록하면 0원으로 명시적으로 확정할 수 있다. 사유 없는 0원 입력은 보상 확정이 불가하다. 사유를 남기고 확정한 0원은 금액 미입력이 아니므로 그 건으로 월 정산 확정을 차단하지 않는다. 다른 미입력 건이 남으면 기존 차단 조건을 유지한다. 기존 관리자 역할·Home Branch Scope·관리 범위 안 본인 등록·별도 승인 없음·감사 정책을 따른다. 미입력을 자동 0원으로 바꾸지 않으며 0원 확정으로 진행 기록을 취소하거나 Pass 차감을 복원하지 않는다. 월 정산 자동 확정이나 나머지 확정 조건의 충족을 뜻하지 않는다. 일반 Session Payment/서비스 PT 계산이나 다른 추가실적의 0원 허용으로 확대하지 않는다. 지원 수업의 사유 필수 0원 허용만 해결됐으며 다른 금액 항목의 0원 허용이나 다른 입력 한계를 확정하지 않아 BR-010 전체는 OPEN이다.

2026-10-11 사용자 확정(해당 월 기본급의 0원 수동 지정 허용 질문의 1번 답변): 해당 월 기본급은 권한 있는 관리자가 사유를 남기면 0원으로 명시적으로 수동 지정할 수 있다. 수동 지정한 0원은 미입력과 구분하며, 미입력이나 누락된 일반 설정을 자동으로 0원으로 대체하지 않는다. 해당 월 기본급에만 적용하고 다른 유효 지급·추가실적은 기존 규칙대로 합산한다. 예를 들어 해당 월 기본급을 0원으로 수동 지정하고 유효 일반 Session Payment가 1,200,000원, 유효 Additional Performance가 150,000원이면 월 합계는 1,350,000원이다. 0원 지정으로 PT 진행 기록·Pass 차감을 취소/복원하거나 다른 지급·실적을 0원으로 변경하지 않는다. 기존 Master Organization 전체/Branch Admin 각 처리 시점 Trainer 현재 Home Branch 기준 인가·관리 범위 안 본인 허용·별도 Master 승인 없음, 최초 수동 지정/수정 사유 필수 및 사유 누락 요청 변경 없이 거부·전후 금액/사유/처리자/시점 이력과 감사 원칙을 동일하게 적용한다. 이 월별 지정으로 현재·미래 일반 기본급 설정과 다른 월 정산을 변경하지 않으며, 이후 일반 설정이 바뀌어도 해당 월의 명시적 수동 지정 0원을 유지한다. 수동 지정하지 않은 월은 기존 일반 설정 적용 규칙을 따른다. 정산 자동 확정이나 미입력 지원 수업 등 기존 확정 차단 조건의 해소를 뜻하지 않으며, 이미 확정된 월의 금액 변경은 기존 해제/정정/재확정과 이전 확정본 보존 조건을 따른다. 이번 허용은 월별 수동 적용 기본급에 한정하며 일반 Compensation Setting의 Base Salary/Rate/Fixed Amount, Product 가격·일반 Session Payment 또는 다른 추가실적의 0원 허용으로 확대하지 않는다. 음수·상한·정밀도·누락값 처리 등 나머지 입력 정책과 미래 적용 월 범위는 BR-010/BR-012 OPEN을 유지한다. 명시적 0원·미입력·수동 지정 여부를 구분하는 저장/조회 계약 및 감사·UoW·경합 전략은 후속 Architecture 검토 대상이다.

BR-010의 현재 해결 범위는 기존 업무별 사유 필수 0원/기타 추가실적 양수, 정수 원·Rate 0~100% 정수와 Q1/Q2 최초 보상 필수 입력/일반 Fixed Amount·Base Salary 0원 이상이다. 다른 Product 입력·금액 상한/저장 표현·남은 누락/월 경계·오류 계약은 OPEN을 유지한다.

Related decisions / requirements: PD-009/027; PR-006/007/008/010/031; [BR-PAY-001–005](business-rules.md)

Required timing: Architecture 착수 가능; 입력 검증 상세 설계·구현 확정 전

Status: OPEN

추가 확정 경계(2026-10-11): 지원 수업 외 추가실적의 최초 등록은 금액을 함께 입력해야 완료하며 미입력 금액을 자동 0원/계산식으로 대체하지 않는다(BR-013; BR-PAY-015). 이는 0원 허용이나 금액 범위/정밀도를 확정한 결정이 아니다. 지원 수업과 일반 보상 설정의 누락값 처리에는 각각 기존 승인 규칙을 적용하며 BR-010 전체는 OPEN이다.

2026-10-11 사용자 확정(지원 수업 외 추가실적의 0원 등록 허용 여부 질문의 1번 답변): 지원 수업 외 추가실적 등록은 금액 > 0이며 0원·음수는 사유 유무와 관계없이 거부한다. 지원 수업의 사유 필수 0원 확정 허용과 월별 수동 기본급의 사유 필수 0원 지정은 유지한다. 다른 금액 항목으로 확대하지 않으며 상한액·정밀도/금액 표현 등 나머지 질문으로 BR-010 전체는 OPEN을 유지한다. BR-PAY-015; PR-031에 추적한다.

지원 수업 외 추가실적은 최초 등록과 확정 전 금액 수정 모두 양수만 허용(Product 확정, 2026-10-11 사용자 일관성 지시 적용). 0원·음수·누락 수정 거부/요청 직전 금액·이력·정산 입력 상태 유지; 사유가 있어도 0원 수정 불가. 기존 관리자 Scope/본인 건/승인 생략/사유·이력/감사 유지. 지원 수업 보상 및 월별 수동 기본급의 승인된 사유 필수 0원 예외는 유지. 상한/정밀도·금액 외 정보 수정/취소는 OPEN.

확인 주체: 사용자/업무 책임자.

2026-10-12 C 일괄 승인 반영: C11: 원화 입력은 정수 원만 허용/소수 원 거부로 해결됐다. 비율 Rate 소수 정밀도·항목별 남은 상한/음수/누락은 미정이며 기존 RATE 1,000원 올림/FIXED 추가 올림 없음과 승인된 0원 예외/다른 AP 양수만 허용은 유지한다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 H 일괄 승인 반영: H1=2: Trainer Rate 정수 퍼센트만 허용/소수 비율 거부·임의 반올림/절사 없음(BR-PAY-018). 기존 원화 정수/지급 결과 올림·범위/누락/0원 예외는 구분한다. 나머지 입력 범위·수치 표현/검증 상세는 후속이다. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch). 이 복합 OPEN의 남은 항목은 유지한다.

2026-10-13 L2=1: Trainer Rate는 최소 0/최대 100 포함 정수 퍼센트만 허용한다. 음수/100 초과/소수 입력 거부·자동 범위 보정/반올림/절사 없음, 명시적 0%의 일반 RATE 지급 0원·미설정의 임의 0% 대체 없음이다. 100%에도 기존 수업별 1,000원 올림을 적용하고 회당 판매 단가 이하라는 새 지급 상한을 도입하지 않는다. 현재 보상 설정 권한/감사·과거 확정 지급·FIXED/지원 보상/다른 실적/기본급의 별도 금액 조건은 유지한다. 다른 항목의 입력 제약·오류/누락 안내·수치 표현/계약으로 BR-010은 OPEN이다. BR-PAY-018, PR-007/008, NFR-012, V-105 예정; [L 승인](product-decisions.md#review-20261013-l-batch).

2026-10-13 Q1/Q2=1 부분 해결: Trainer 최초 등록 완료에는 세 보상 값과 기본급 적용 시작 월이 필요하며 일반 Fixed Amount/Base Salary는 명시적 0원 이상 정수 원이다. 누락 기본값·미전달 초기화는 금지하고 기존 인가/최초 감사·시작 월부터 지속/종료 월 불필요·신규 지급 적용/과거 확정 결과 불변 및 다른 업무의 금액 규칙을 유지한다. 초기/일반 금액 부분은 확정됐고 상한/월 경계·다른 필드/역사 사실·최소 계약 때문에 Status는 OPEN이다. [Q 승인](product-decisions.md#review-20261013-q-batch); BR-OPS-028/PAY-022; V-114/115 미구성·미실행.

<a id="br-011"></a>
## BR-011. Product 기준정보 변경과 기존 Pass — 해결됨

Question: Product Price·Session Count·Payment Type 변경 시 기존 Pass에 연결된 이후 신규 Session에는 어떤 Product 기준을 적용하는가?

Status: CLOSED

Resolution / approval source: 2026-10-10 사용자가 “기존 Pass는 발급 당시 상품 가격·총횟수·지급방식을 유지하고, 변경된 상품 조건은 새 Pass부터 적용”하는 1번을 선택했다. 기존 Pass의 이후 PT 진행에도 발급 당시 Product Price·Session Count·Payment Type을 사용한다. 상품 수정으로 기존 Pass의 조건이나 잔여를 덮어쓰지 않으며 Pass 선택의 FIXED_AMOUNT 우선/FIFO 판단에도 발급 당시 Payment Type을 사용한다.

Related decisions / requirements: PD-007/009/012; PR-003/006/008/010; BR-PAY-001/003/006/008/013. 기존 BR-006에서 분리한 Product 변경 질문을 해결했다.

Required timing: 기존 Pass 적용 정책 결정 완료. 발급 시 상품 조건의 일관된 확보·보존과 동시성 검증은 Architecture 후속이다.

확정된 경계: 상품 조건의 유지와 Trainer 설정의 적용 시점은 별개다. 일반 Session Payment의 Rate/Fixed Amount는 기존 BR-PAY-011/012대로 권한 있는 관리자 저장 완료 이후 새로 등록되는 PT 진행에 적용하고 등록 시 지급액을 확정한다. 과거 확정 Session Payment는 재계산하지 않는다. Pass 횟수 수동 조정 등 BR-002, 타 지점 추가실적의 남은 정책은 BR-013 OPEN이다. 지원 수업의 관리자 건별 금액 입력·기록/차감 후 금액 저장 시 보상 확정·미입력 건이 남은 Trainer·월의 정산 확정 차단은 후속 사용자 결정으로 해결했다. snapshot 또는 상품 버전 참조 등의 저장 구조는 이 결정으로 채택하지 않는다.

확인 주체: 사용자. 답변 완료(2026-10-10).

## Multi-Branch 변경에 따른 Product Open Questions

아래 질문의 결정 주체는 사용자/업무 책임자다. 기술 설계로 대신 결정하지 않는다. 공통 제약 검토 자체를 중단할 필요는 없지만 각 영향 영역은 답변 전 확정할 수 없다.

<a id="mb-001"></a>
## MB-001. Branch / Trainer

Question / TODO: Trainer 과거 Home 이력 오류의 구체 정정 범위/현재 Home 영향·역사 사실 확인 불가/충돌·분류 전환/역사 보상 설정 확인·영향 건 식별/완료 증거 및 전화번호 형식/정규화·중복/공개·다른 상태/최소 계약을 구체화한다. V1 Master Organization 전용/사유·원래 이력 보존에 이어 W1 같은 PT/Pass 차감 유지·일반 최초 기록 생성 시점 설정/기존 소비 Pass 조건·지원 관리자 수동 추가실적과 W2 해당 Trainer·월 영향 정정 완료 후 확정/재확정이 해결됐다. 소속 정정만으로 과거 PT/지급/정산을 자동 변경하지 않고 기존 권한·해제/정정/같은 월 재확정·이전본 보존을 유지한다. U/R/Q/P/O/M2의 만료 담당 교체/조회·전화 필수/초기 보상·전체 적격 Pass/지원/현재 Home 인가/실제 당시 Home·Performed 구분도 유지한다. 승인된 허용/방식·지급 시점을 재질문하지 않는다.

Status: OPEN

Related decisions / requirements: PD-002/004; PR-005/008/020/029/030. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Trainer 관계·허용 PT Scope 및 Session 권한 상세 설계 확정 전

확정된 경계: 단일 Home Branch 소속과 타 지점 수업 가능은 CLOSED. Branch에는 여러 Trainer가 있을 수 있고 지원 수업으로 소속을 변경하거나 추가하지 않는다. 과거 Session Performed Branch는 보존한다.

2026-10-12 사용자 확정(Trainer 회원 검색·조회 범위 질문의 1번): 본인이 담당 Trainer로 지정된 Pass의 Member와 개별 허용된 지원 수업 대상 Member만 검색/조회한다. 같은 Home Branch의 미담당/미허용 회원·Organization 전체 조회는 불가하며 Backend가 목록·검색·직접 ID 상세에서 검증된 Trainer 연결/Organization Scope와 대상별 허용 사실을 확인한다. 관리자 겸임자의 별도 관리 권한은 유지한다. 조회 대상 경계는 해결됐고 담당 관계 인정·지원 지정/철회/기간·공개 항목/나머지 PT 업무 및 이동 정책이 남아 MB-001은 OPEN이다(BR-OPS-005).

2026-10-12 사용자 확정(지원 대상 지정 권한 질문의 1번): Master는 Organization 전체, Branch Admin은 지정 처리 시점 자신의 현재 관리 Branch가 Member 현재 Home Branch인 경우만 지정한다. 대상 Trainer 소속·Performed Branch·Pass Issued Branch/과거 소속은 기준이 아니며 비관리자 Operator/Trainer는 불가하다. 수원 Member/강남 Trainer·수업이면 수원 관리자/Master가 지정한다. Backend 현재 권한·회원 소속/대상 Organization 검증과 중요 권한 변경 감사를 적용한다. 지정 주체/Scope는 해결됐고 기간·철회 주체/이동 후 기존 허용·절차/공개 항목과 다른 잔여 질문으로 OPEN을 유지한다(BR-OPS-005).

2026-10-12 사용자 확정: 개별 지원 조회 허용은 관리자가 해제할 때까지 유지하며 고정 종료일/기간 경과 자동 종료·반복 연장은 두지 않는다. 해제 Actor/Scope는 기존 지정 권한과 같은 Master Organization/Branch Admin 처리 시점 Member 현재 Home Branch 기준을 적용한다(2026-10-11 사용자 일관성 지시 적용). Backend 현재 권한/대상 Organization 검증과 NFR-004 감사를 유지한다. 해제는 해당 지원 관계의 조회 근거만 종료하며 별도의 담당/관리 권한과 기존 PT·Pass·지급/정산은 그대로 판단한다. 소속 이동 후 기존 허용·대상 상태/담당 관계 인정·절차/공개 정보는 후속이다(BR-OPS-005). 기간·동일 Scope 해제 주체 질문은 해결됐고 이동/담당 관계/절차/공개 항목 등의 잔여 질문 때문에 MB-001/002/003/005는 OPEN을 유지한다.

2026-10-12 사용자 확정: Member Home Branch 변경만으로 기존 개별 지원 조회 허용을 해제하거나 재지정하지 않고 유지한다. 이동 후 지정/해제는 Master Organization 또는 각 처리 시점 Member 현재 Home Branch 관리 Branch Admin이 담당하며 이전 소속/과거 지정 Actor만으로 권한을 유지하지 않는다. 동일 Organization 내 Trainer Home Branch만 변경된 경우도 같은 유지 원칙을 적용한다(2026-10-11 사용자 일관성 지시). 현재 Caller/대상 관계 검증과 기존 감사 이력·별도 담당/관리 Scope를 유지한다. 과거 수업/Pass/지급/정산 변경이나 일반/지원 구분 고정은 없고 수업 당시 Trainer 소속 기준을 따른다. 이동 자체의 권한/시점/이력·다른 대상 상태·담당 관계/공개 필드/절차·계약/저장은 후속이다(BR-OPS-005, MB-001/002/003/005). 허용 유지 질문은 해결됐지만 위 이동 자체/담당 관계/다른 상태/절차/공개 항목 때문에 MB-001/002/003/005는 OPEN을 유지한다.

2026-10-12 사용자 수정 확정(잔여 0 회원 조회와 제외 필터): 본인이 담당한 이용권의 잔여가 모두 0이어도 그 사실만으로 담당 회원의 목록·검색·상세 조회를 차단하지 않는다. 기본 조회에는 잔여 0 회원도 포함하고 선택 기능인 “잔여 0인 회원 제외” 필터를 제공한다. 필터 미사용 시 포함/사용 시 해당 조건의 회원을 결과에서 제외하며 조회 권한이나 담당/지원 관계·회원 상태를 변경하지 않는다. Backend의 현재 Caller/Organization·담당 또는 개별 지원 관계 인가는 필터와 독립적으로 유지한다. 조회 허용이 Remaining > 0 등 기존 PT 등록/차감 조건을 면제하지 않는다. 여러 이용권의 잔여 집계 범위·개별 지원 회원 등 담당 이용권 없는 대상의 판정과 수동 만료/취소·담당 변경 등 다른 상태의 조회 영향/공개 필드는 후속이다(BR-OPS-005, PR-002/029/030, MB-001/003/005). 잔여 0 회원의 조회 유지/필터 제공은 해결됐으나 필터 집계 범위·다른 상태/담당 관계·이동/공개 조건 때문에 MB-001/003/005는 OPEN을 유지한다.

2026-10-12 사용자 확정(잔여 제외 필터의 집계 기준 질문의 1번): “잔여 0인 회원 제외”는 조회 권한이 확인된 Member의 전체 이용권 잔여를 기준으로 판단한다. 조회 Trainer가 담당한 Pass만으로 제한하지 않으며 동일 Organization 내 다른 Trainer 담당/다른 Issued Branch의 Pass도 해당 Member의 집계 범위에 포함한다. 내 담당 Pass 0회+다른 Trainer 담당 Pass 10회인 Member는 필터를 켜도 표시하고 전체 집계 잔여가 0이면 제외한다. 개별 지원 회원도 자기 담당 Pass 존재 여부와 관계없이 같은 Member 전체 기준을 적용한다. 필터 미사용의 기본 조회/개별 상세 권한은 그대로이며 다른 회원/개별 Pass·다른 Trainer PT/보상 정보를 자동 공개하지 않는다. 집계 범위는 확정됐고 나머지 종료 상태의 잔여 취급·담당 변경/비활성·공개 필드 및 계약/저장/조회 일관성은 후속이다(BR-OPS-005, PR-002/029/030, MB-001/003/005). 수동 만료의 보존된 양수 잔여는 0으로 간주하지 않고 실제 사용 가능 여부와 구별한다. 집계 범위/지원 대상 판정은 해결됐지만 다른 종료 상태/담당 관계·이동/절차·공개 정보 때문에 MB-001/003/005는 OPEN을 유지한다.

2026-10-12 사용자 확정(Trainer의 회원 전화번호 조회 질문의 1번): Trainer는 기존 조회 권한이 확인된 담당 회원과 개별 허용 지원 회원의 등록된 전체 전화번호를 조회할 수 있다. 부분 마스킹된 번호만 허용하는 정책으로 제한하지 않는다. 담당 Pass 잔여가 모두 0이어도 기존 회원 조회 권한이 유지되면 전화번호도 같은 범위에서 조회한다. Backend는 전화번호를 반환하는 조회마다 현재 Caller/Organization·담당 또는 지원 관계를 검증하고 미담당/미허용 회원·타 Organization 번호를 공개하지 않는다. 지원 해제 후 별도의 유효한 담당/관리 권한이 없으면 해당 번호도 공개하지 않는다. 관리자 겸임자의 별도 관리 Scope는 유지한다. 이번 승인은 전화번호 읽기이며 수정/일괄 내보내기·다른 개인정보/개별 Pass·다른 Trainer PT/보상 공개 권한을 추가하지 않는다. 전화번호 필수 수집/형식·중복/검증과 나머지 필드/보존·조회 계약은 후속이다(BR-OPS-005, PR-002/029/030, NFR-001/005, LEGAL-001). 전체 전화번호 조회는 해결됐고 나머지 관계/상태/필드·이동/절차 때문에 MB-001/003/005는 OPEN을 유지한다.

2026-10-10 사용자 확정(지점 이동 후 과거 지원 수업 보상 정정·정산 해제/재확정의 Home Branch 기준 질문의 1번 답변): 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 9월 수원 소속 Trainer가 10월 강남으로 이동한 뒤 9월 지원 수업 보상을 정정하는 예에서는 강남 Branch Admin에게 해당 정정과 월 정산 확정 해제·재확정을 허용하고, 별도 Master 권한이 없는 수원 Branch Admin에게는 과거 소속만을 근거로 허용하지 않는다. 과거 수업의 Performed Branch·수업 사실·이전 확정본·기존 이력은 보존한다. 기존 관리 범위 검증·Branch Admin의 별도 Master 승인 없음·금액 수정 사유 및 확정 해제 사유 필수·감사 정책을 유지한다. 이번 결정은 지원 수업 보상 금액 정정과 해당 월 정산 해제/재확정의 인가 기준에 한정한다. 다른 추가실적 최초 등록/정정의 이동 기준, Trainer 이동 자체의 적용 시점·절차, 비용 귀속·정산 공개(MB-010/006)는 미결정으로 남긴다. 당시 미정이었던 최초 월 정산 확정 권한과 별도 Master 승인 없음은 2026-10-11 후속 사용자 결정으로 확정했다.

2026-10-11 비용 귀속 결정과의 경계: 이동월 기본급 비용은 대상 월말 Home Branch 한 곳에 해당 월 적용액 전액 귀속(2026-10-11 Product 확정). 이는 Trainer 이동의 적용 시점·이력 저장·수정/취소 절차를 확정한 결정이 아니며, 이후 이동만으로 과거 대상 월말 소속에 따른 기본급 비용 지점을 변경하지 않는다. 실제 대상 월말 소속 사실을 확인하는 계약/이력 설계는 후속이다(MB-010).

2026-10-11 사용자 확정(일반/지원 구분 시점 질문의 1번): 이동 후 등록에도 실제 수업 당시 Home Branch 기준의 구분을 유지한다. 일반 PT 지급 설정의 기록 생성 시점·관리 권한의 현재 Home Branch 기준은 유지한다. 당시 소속을 확인할 수 없을 때 현재 소속으로 임의 대체하지 않는다. 이 결정으로 이동 적용 시점/이력 예외나 소급 등록·사실 정정의 보상 전환을 닫지 않는다(BR-OPS-001, BR-PAY-011, MB-005/BR-008).

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

2026-10-12 사용자 확정(이용권의 담당 Trainer 교체 질문의 1번): 기존 PT Pass에서 Assigned Trainer를 교체할 수 있다. 20회권을 5회 사용한 뒤 담당 A를 B로 바꾸어도 같은 Pass의 잔여 15회와 과거 수업·지급 이력을 유지한다. 교체를 위해 기존 Pass를 취소하거나 새 Pass를 발급하는 절차를 요구하지 않으며 횟수를 복원/추가/재차감하지 않는다. 발급 당시 상품 가격·총횟수·Payment Type과 Issued Branch는 그대로이고 Member/Trainer Home Branch도 이 변경으로 이동하지 않는다. 과거 PT 기록의 실제 수행 Trainer·Performed Branch, 확정 Session Payment·추가실적/정산을 새 담당 기준으로 자동 재작성/재계산하지 않는다(BR-OPS-008, PD-007, PR-003).

기존 사용자 일관성 지시 적용(2026-10-11): 일반 담당 교체도 저장 완료 후 변경된 현재 담당을 적용하고 미래 예약 변경 절차를 추가하지 않는다. 중요 Pass/인가 관계 변경의 이력·감사 원칙에 따라 대상 Pass/Member·변경 전후 담당 Trainer·변경 Actor/권한·Branch Context·시점을 추적한다. 저장 실패 시 기존 담당과 잔여/이력을 유지한다. 저장/UoW·감사 구조·동시성 계약을 승인한 것은 아니다(NFR-001/004, BR-OPS-007/008).

기존 회원 조회 원칙 적용(BR-OPS-005): 담당 관계를 인정하는 Pass의 현재 담당이 바뀌면 후속 회원 목록/검색/직접 ID·전화번호 공개도 Backend에서 변경된 현재 담당 관계와 별도의 개별 지원/관리 권한으로 판단한다. 이전 담당이라는 사실만으로 영구적인 Member 조회 권한을 부여하지 않는다. 새 담당은 기존 담당 회원 범위에서 인가하며 이전 담당도 다른 담당 Pass나 개별 지원/관리 권한이 있으면 그 독립 근거로 판단한다. 본인이 실제 수행한 과거 PT 기록 조회는 기존 별도 업무 Scope를 따르고, 이를 다른 Member/Pass/PT·보상 설정의 무제한 공개로 확대하지 않는다. 잔여 0만으로 담당 회원 조회를 막지 않는 규칙도 유지한다.

2026-10-12 사용자 확정(담당 교체 권한의 기준 지점 질문의 1번): 기존 Pass의 Assigned Trainer 교체는 Master Admin의 Organization 전체 범위 또는 처리 시점 Member의 현재 Home Branch를 관리하는 Branch Admin에게 허용한다. 수원 발급 Pass의 회원이 현재 강남 소속이면 강남 Branch Admin 또는 Master가 교체할 수 있으며, 수원 Branch Admin은 Issued Branch만을 근거로 교체할 수 없다. 회원 소속이 다시 변경되면 각 교체 요청은 변경된 현재 Home Branch 기준으로 인가한다. 이용권 수동 만료/해제의 Issued Branch 기준은 그대로 유지한다(BR-OPS-004/008, PD-007, PR-003/030).

Backend는 검증된 현재 Caller의 관리자 권한/Organization·관리 Branch Scope, 실제 Pass→Member 관계와 Member 현재 Home Branch를 확인한다. 직접 Pass/Member ID·클라이언트 role/Branch/Member 소속 값·과거 소속/담당 또는 이전 처리 Actor·Trainer Home Branch·수업 Performed Branch만으로 교체 권한을 인정하지 않는다. 관리자 권한 없는 Operator/Trainer는 수행할 수 없으며 관리자·Trainer 겸임자는 해당 관리자 Scope로 판단한다. 권한 거부/실패 시 기존 담당·잔여/발급 조건·업무 이력을 유지한다. 기존 범위 내 관리자 직접 처리 원칙을 동일 적용하여 별도 Master 승인 대기를 추가하지 않는다(2026-10-11 사용자 일관성 지시 적용). 교체 권한은 대상 Trainer의 Compensation Setting 조회/변경 권한이나 다른 지점 전체 Trainer/Member 정보 열람 권한을 부여하지 않는다. 기존 즉시 적용·전후 담당/Actor/Branch Context·시점 이력/감사·현재 관계 기반 조회와 과거 수업/보상 보존 원칙은 유지한다.

2026-10-12 사용자 확정(교체할 Trainer의 소속 지점 질문의 1번): 기존 Pass의 담당 교체 대상은 같은 Organization의 Trainer이며 Member 현재 Home Branch와 다른 지점 소속 Trainer도 허용한다. 강남 회원의 담당을 수원 소속 Trainer로 바꿀 수 있다. Member와 같은 지점 소속이어야 한다는 제한을 두지 않으며 다른 Organization Trainer는 지정할 수 없다. 교체 요청의 Actor 권한은 기존대로 Master Organization 전체 또는 Branch Admin 처리 시점 Member 현재 Home Branch 기준이다(BR-OPS-008, PD-007, PR-003/029/030).

기존 규칙 적용(BR-OPS-001/005/008, BR-PAY-011/015): 담당 교체는 Assigned Trainer 관계만 바꾸며 Member/Trainer Home Branch·Pass Issued Branch·발급 조건/잔여와 과거 실제 수업/확정 지급·정산을 바꾸지 않는다. 후속 회원 조회는 현재 담당 관계와 별도 지원/관리 권한으로 인가한다. 실제 PT 업무의 Allowed PT Scope·Pass 사용 조건은 별도로 검증한다. 일반/지원 보상 구분은 실제 수행 Trainer의 수업 당시 Home Branch와 실제 Performed Branch를 비교한다. 수원 소속 Trainer가 강남 회원을 수원에서 지도하면 일반 PT, 강남에서 지도하면 지원 수업으로 기존 보상 규칙을 적용하며 담당 지정만으로 일괄 일반/지원 처리하지 않는다. 지원 수업은 해당 수업의 보상 전체를 관리자 입력 Additional Performance로 처리하고 일반 Session Payment를 중복 합산하지 않는다. 타 지점 Trainer를 담당으로 지정할 수 있어도 그 Trainer의 Compensation Setting·전체 정산/프로필이나 타 지점 전체 회원/Trainer 목록 열람 권한은 늘어나지 않는다. Backend는 대상 Trainer의 실제 Organization 관계도 확인하고 요청의 Trainer/Organization ID·지점 값만으로 신뢰하지 않으며 범위 밖 요청 거부 시 기존 담당/잔여·업무 이력을 유지한다.

2026-10-12 사용자 확정(담당 교체 전 수업의 누락 등록 질문의 1번): A가 담당으로 실제 수업을 진행한 뒤 담당이 B로 바뀌어도 A는 교체 전 본인 수업을 직접 늦게 등록할 수 있다. 예: 9월 5일 A 수업 → 9월 6일 B로 담당 교체 → 9월 7일 A 누락 등록. 실제 수업 당시 A의 담당 관계와 본인 수행 사실, 현재 검증된 Caller/Trainer 연결·Organization 및 기존 Pass/정산 조건을 확인한다. 현재 담당이 B라는 이유만으로 관리자 대행이나 A 재배정을 요구하지 않는다. 이 허용만으로 A의 해당 회원 목록/상세·전화번호/다른 Pass·다른 Trainer 기록 조회 권한을 복원하지 않는다(BR-OPS-003/005/008, PD-008, PR-008/029/030).

2026-10-12 사용자 확정(잔여 0회인 이용권의 담당 교체 질문의 1번): Remaining이 0인 기존 Pass도 Assigned Trainer를 교체할 수 있다. 잔여를 모두 사용해 이용이 끝난 Pass도 포함한다. 같은 Pass에서 담당 A를 B로 바꾸며 Remaining 0·발급 조건/Issued Branch·과거 실제 수행 Trainer/PT 기록·확정 지급/정산 이력은 유지한다. 새 담당 B는 기존 현재 담당 관계에 따른 Member 조회·응대를 이어갈 수 있다. 기존 Master Organization 전체/Branch Admin 처리 시점 Member 현재 Home Branch 권한과 같은 Organization의 다른 지점 Trainer도 대상 허용 원칙은 유지한다(BR-OPS-005/008, PD-007, PR-003/029/030).

남은 결정: 교체 Actor/Branch Scope·대상 Trainer 지점 조건·교체 전 실제 본인 수업의 이전 담당 직접 누락 등록과 함께 잔여 0으로 이용을 마친 Pass의 담당 교체도 해결됐다(2026-10-12). 잔여 소진 외 Pass 수동 만료/취소 등 다른 사유의 상태별 교체/담당 조회 조건·과거 담당/수행 사실 확인 불가/정정·교체 후 수업/다른 관계의 나머지 인가와 구체 명령/응답·최소 식별/Trainer 선택 정보·이력/저장/UoW·조회/등록/교체 경합은 ARCH-001·MB-001/003/005·BR-001/008 및 후속 Architecture에서 결정한다. 잔여 0 승인만으로 별도 수동 만료/취소 조건을 일괄 허용하거나 상태명/저장 방식을 확정하지 않는다. 교체 허용은 계정/역할·보상 설정 수정 권한 승인이 아니다.

2026-10-12 사용자 확정(Trainer 소속 지점(Home Branch) 변경 권한 질문의 1번): Trainer의 Home Branch 변경은 Master Admin만 자신의 Organization 범위에서 수행한다. Branch Admin은 변경 전/후 지점 관리자 또는 해당 Trainer 계정 발급자여도 변경할 수 없다. Operator·Trainer 단독은 본인 포함 불가하며 관리자/Trainer 겸임도 현재 Master 권한이 있을 때만 해당 Organization Scope로 처리한다. Branch Admin의 자기 지점 Trainer 신규 로그인 계정 발급 권한(BR-OPS-012)은 유지하며 이를 소속 변경 권한으로 확대하지 않는다(BR-OPS-013, PD-004, PR-005/029/030, NFR-001/004, MB-001/004/005, ARCH-001).

일반 이동은 기존 사용자 일관성 지시에 따라 저장 완료 후 현재 소속 반영/실패 보존·감사를 적용하고 미래 예약을 추가하지 않는다. 독립 역할/Scope·Trainer 연결/담당·지원 관계와 과거 수업 당시 소속·확정 보상/정산은 보존한다. 대상 Branch/Trainer 상태·최소 선택 정보/절차·과거 소속 이력 정정/소급/확인 불가 및 저장/계약/UoW·캐시/처리 중 요청/동시성은 후속이며 이 OPEN 전체를 CLOSED로 바꾸지 않는다(BR-OPS-013).

2026-10-12 사용자 확정(관리자·Trainer 겸임 계정의 Trainer 비활성화 질문의 1번): Trainer 비활성화는 Trainer 역할에 따른 권한만 중단하며, 같은 계정에 독립적으로 부여된 관리자 역할/Scope와 그 범위의 업무는 유지한다. 계정 전체 로그인 차단은 별도 업무다(BR-OPS-014, PD-011/019, PR-005/026, NFR-001/004, ARCH-001/002, MB-001).

확정된 범위는 겸임 계정의 Trainer 비활성화/전체 계정 차단 분리와 Master Organization 전체·Branch Admin 처리 시점 Trainer 현재 Home Branch 기준의 비활성화 권한이다. Trainer 재활성화의 상태 조합/구체 절차, 재활성화 절차/권한 복구, 관리자 대행 등록의 상세 인가/사실 판정·비활성 Trainer 본인의 직접 등록/이력 열람 예외, 개별 지원 조회 허용 관계의 비활성화/재활성화 시 처리는 후속 결정이다. 구체 상태/역할 저장·Caller 계약·AuthSession 갱신/철회·캐시/처리 중 요청·UoW/동시성은 후속 Architecture이며 ADR-0004 v1 인증 방식은 ACCEPTED/모듈 구체 설계는 PROPOSED를 유지한다. 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 사용자 확정(Trainer 비활성화 권한 질문의 1번): Master Admin은 자신의 Organization 전체 Trainer, Branch Admin은 비활성화 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 단일 관리 Branch인 경우 Trainer를 비활성화할 수 있다. 타 지점 Branch Admin·Operator/Trainer 단독은 불가하며 겸임자는 독립된 현재 관리자 역할/Scope로 판단한다(BR-OPS-014, PD-011/019, PR-005/029/030, NFR-001/004, ARCH-001/002, MB-001).

Backend는 현재 검증된 Caller 역할/Organization·관리 Branch와 실제 대상 Trainer의 Organization/현재 Home Branch를 확인한다. 타 지점 지원 수업/Performed Branch·Member/Pass 담당 관계·Operator 업무 Branch·과거 Trainer 소속이나 계정 발급자였다는 사실만으로 비활성화 권한을 인정하지 않는다. 직접 Trainer ID·위조 role/branch_id/Organization 또는 철회·축소된 권한으로 우회할 수 없다. Trainer 소속 변경 후에는 새 현재 Home Branch로 인가한다. 비활성화 Actor/현재 소속 기준은 해결됐고 재활성화 절차·대상 상태/중복 요청·개별 지원 관계/재활성화 처리·비활성 상태 예외 및 실제 계약/저장/철회·동시성은 후속이다. 겸임 관리자 유지·별도 전체 계정 차단 게이트와 OPEN 전체 상태는 유지한다.

2026-10-12 사용자 확정(잔여가 남은 담당 이용권이 있는 Trainer의 비활성화 질문의 1번): 잔여가 남은 담당 PT Pass가 있어도 Trainer 비활성화를 허용하며 기존 Assigned Trainer 정보는 유지한다. 비활성화 전에 모든 Pass를 다른 Trainer에게 교체하도록 요구하지 않고 자동 담당 해제/재배정도 하지 않는다. 이후 필요할 때 권한 있는 관리자가 BR-OPS-008의 기존 조건/Scope로 담당을 교체한다(BR-OPS-014, PD-007/011, PR-003/005, NFR-001/004, ARCH-001/002, MB-001/003/005, BR-001).

기존 담당 정보 유지와 별도 담당 교체가 해결됐으며 비활성 Trainer의 접근은 계속 차단한다. Member 현재 Home Branch 기반 담당 교체와 Trainer Home Branch 기반 비활성화 권한을 구분하고 잔여/발급 조건·과거 PT/보상을 유지한다. 다른 상태별 교체/사용 조건·개별 지원/재활성화·비활성 상태의 과거 PT 예외 및 구체 저장/현재 인가·UoW/동시성은 후속이다. 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 사용자 확정(담당 Trainer를 새로 지정할 때의 조건 질문의 1번): PT Pass의 담당 Trainer를 새로 지정할 때는 실제 활성 Trainer만 허용한다. 기존 Pass의 담당 교체 및 허용된 새 Pass 발급 흐름에서 담당을 최초 지정하는 경우 모두 적용하며 비활성 Trainer를 미리 배정하지 않는다(BR-OPS-008/014, PD-007, PR-003/005/029/030, NFR-001, ARCH-001, MB-001/003/005, BR-001).

새 지정 대상의 활성 필요조건은 해결됐으며 같은 Organization의 타 지점 허용/기존 행위별 Actor·Scope, 이후 비활성화된 기존 담당 정보 유지·접근 차단을 적용한다. 최초 담당 필수는 해결됐고 나머지 Pass/계정/Branch 상태 조합·최소 선택 정보, 재활성화·개별 지원/비활성 전 수업 예외 및 실제 현재 사실 검증/저장/UoW·지정·비활성화 경합은 후속이다. 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 사용자 확정(비활성화 전 진행했지만 누락된 PT 수업 등록 질문의 1번): Trainer 비활성화 전에 실제로 수행한 미등록 PT 수업은 관리자가 대행 등록하는 경로를 허용한다. 대상 Trainer의 비활성 상태를 유지하며 잠시 재활성화/본인 로그인·담당 재배정을 선행 요구하지 않는다. 실제 수행 Trainer·실제 수업일과 기존 Pass 잔여/정산 조건을 그대로 적용한다(BR-OPS-015, PD-008/011, PR-008/029/030, BR-OPS-003/008/014, BR-PAY-006/011/012).

관리자 대행 경로와 Master Organization/Branch Admin 실제 Performed Branch Scope는 해결됐다. 현재 인가 검증·비활성화 전 실제 수업/담당/소속 사실·시점/확인 불가·최소 선택 정보/사유·증빙과 구체 계약/저장/UoW·경합은 후속이다. 비활성/현재 담당 유지·실제 수행자/수업일·기존 Pass/생성 시점 보상/진행 월 정산·민감 설정 접근 제한을 적용한다. 비활성 Trainer 본인 직접 등록/회원 조회 예외가 아니며 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 일괄 승인 반영: B1/B2/B3: Trainer 재활성화는 Master Organization/현재 Trainer Home Branch 관리자, 다른 활성 역할 없는 비활성 Trainer 로그인 불가, 새 Pass는 활성 담당 지정 필수로 해결됐다. 개별 지원 기록 수명·계정/Branch 상태 조합·최소 공개 계약/현재/과거 사실·경합은 남는다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch). 이 복합 OPEN의 다른 미결정 항목은 유지한다.

2026-10-12 E 일괄 승인 반영: E5: Trainer 역할 추가/회수에서 Branch Admin은 실제 대상 Trainer 현재 Home Branch 기준으로 인가한다. 다른 역할의 Branch/Performed/Member·Pass 관계로 권한을 확대하지 않고 기존 Workforce 소속·Trainer 업무 상태/계정 전체 상태/과거 PT·지급/담당 관계와 역할 변경을 구분한다. 동일인/역할 연결·재부여/상태 조합/Caller·경합은 후속이다. [2026-10-12 E 일괄 승인](product-decisions.md#review-20261012-e-batch)

2026-10-12 G 일괄 승인 반영: G1/G4/G5: Home Branch 비활성만으로 활성 Trainer의 기존 로그인/조회·타 활성 지점 허용 수업을 차단하지 않는다. Master는 활성 지점으로 Trainer Home Branch를 이동할 수 있고 현재 Home 기반 보상 설정/정산 인가와 과거 소속/보상/비용 보존을 따른다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). 다른 상태/신규 배정·역사 사실/구체 계약·경합 등 나머지 게이트로 이 복합 OPEN은 유지한다.

2026-10-12 K 일괄 승인 반영: K2로 실제 Trainer 등록/이름·연락처 수정 Actor·Home 범위를 확정했다. 기존 Master 전용 Home 이동·활성 필요조건/현재와 수업 시점 소속 구별은 유지하고 다른 필드/연락처 필수·공개/초기 보상·연결/대상 상태·역사 정정/경합은 후속이다. K3의 Trainer 연결 후속 분리는 v1 Trainer 로그인 의무 제외가 아니다. [2026-10-12 K 일괄 승인](product-decisions.md#review-20261012-k-batch). 이 복합 OPEN의 다른 항목은 유지한다.

2026-10-13 M2=1: 수동 만료 Pass도 현재 유효 Trainer의 담당 Member/허용 전체 전화번호 조회 근거로 인정하며 만료만으로 조회 관계를 끝내지 않는다. Backend 현재 Caller/Organization·담당 또는 개별 지원 인가, 담당 변경/Trainer 비활성·계정/역할/인증 철회 제한과 실제 PT 사용/만료 전 늦은 등록·전체 잔여 필터를 유지한다. 새 개인정보/다른 Pass/PT/보상·내보내기/수정 권한이나 수동 만료 Pass의 담당 교체 허용은 추가하지 않는다. 해당 조회 부분만 해결됐고 나머지 교체/역사 사실/공개/계약으로 이 복합 OPEN은 유지한다. BR-OPS-005/004; PR-002/003/029/030·NFR-001/005; V-107 예정; [M 승인](product-decisions.md#review-20261013-m-batch).

2026-10-13 O1/O2=1 부분 해결: 담당/개별 지원 회원의 본인 실제 수업 등록은 다른 Trainer 담당분을 포함한 전체 적격 Pass의 FIXED_AMOUNT 우선/FIFO 차감이다. 개별 지원은 본인 담당 Pass 없이도 조회/본인 등록을 허용한다. 담당자·Home/Issued/Performed·실제 수행자 보상/금액 비공개 및 기존 상태/잔여·정산 검증은 유지한다. 지원 관계의 지정 전/해제 후 과거 등록 시간 경계·역사 사실과 나머지 공개/계약 때문에 Status는 OPEN이다. [O 승인](product-decisions.md#review-20261013-o-batch); BR-OPS-026; V-110/111 미구성·미실행.

2026-10-13 P1/P2=1 부분 해결: 현재 유효한 지원 허용으로 지정 전 실제 본인 수업 등록을 허용하며, 해제 후에는 허용 기간에 실제 진행한 본인 수업만 늦게 등록한다. 일반 Member/전화번호 조회 비복원·지정 이력 비소급, 현재 계정/Trainer/실제 수행·과거 허용 사실 및 기존 Pass/정산 조건을 유지한다. 시간 정책은 확정됐고 역사 사실 확인 불가/충돌·나머지 상태/공개·최소 계약 때문에 Status는 OPEN이다. [P 승인](product-decisions.md#review-20261013-p-batch); BR-OPS-027; V-112/113 미구성·미실행.

2026-10-13 Q1/Q2=1 부분 해결: Trainer 최초 등록 완료에는 세 보상 값과 기본급 적용 시작 월이 필요하며 일반 Fixed Amount/Base Salary는 명시적 0원 이상 정수 원이다. 누락 기본값·미전달 초기화는 금지하고 기존 인가/최초 감사·시작 월부터 지속/종료 월 불필요·신규 지급 적용/과거 확정 결과 불변 및 다른 업무의 금액 규칙을 유지한다. 초기/일반 금액 부분은 확정됐고 상한/월 경계·다른 필드/역사 사실·최소 계약 때문에 Status는 OPEN이다. [Q 승인](product-decisions.md#review-20261013-q-batch); BR-OPS-028/PAY-022; V-114/115 미구성·미실행.

2026-10-13 R1/R2=1 부분 해결: Trainer 전화번호는 필수 기본정보이며 Branch Admin의 자기 지점 지점명/대표 연락처 수정과 중요 변경 감사를 허용한다. 기존 신규/현재 Home 인가·계정/보상 권한 분리·Branch 구조/상태/관리자 배정/과거 지점 사실은 유지한다. 형식/정규화·다른 필드/공개·보존/이력/계약 때문에 Status는 OPEN이다. [R 승인](product-decisions.md#review-20261013-r-batch); BR-OPS-029/030; V-116/117 미구성·미실행.

2026-10-13 U1=1 부분 해결: 수동 만료 Pass의 담당도 기존 Master Organization/처리 시점 Member 현재 Home Branch Admin 범위에서 같은 Organization 실제 활성 Trainer로 교체할 수 있다. 만료 상태/잔여·발급 조건/시각·과거 수행/지급·정산을 보존하고 자동 만료 해제/횟수 부여·새 수업 사용은 허용하지 않는다. 기존 감사·M2 현재 담당 조회/이전 담당 다른 관계 없는 일반 조회 비복원·독립 관리자 Scope를 유지한다. 다른 상태/역사 사실·최소 선택/인가 계약/경합 때문에 Status는 OPEN이다. [U 승인](product-decisions.md#review-20261013-u-batch); BR-OPS-008/005; V-122 미구성·미실행.

2026-10-13 V1=1 부분 해결: Trainer/Member의 이미 기록된 과거 Home 이력 오류는 Master 자기 Organization 전용/사유 필수·원래 이력/감사 보존으로 정정한다. 일반 이동의 즉시 적용/미래 예약 미지원은 유지하고 기존 PT/지급·정산 확정본을 자동 덮어쓰지 않는다. 영향 건은 기존 업무별 권한/정정·필요한 월 확정 해제/동일 월 재확정·이전본 보존을 따른다. 구체 역사 사실/현재 Home 영향·분류가 바뀌는 수업 정정/지급 기준·비용 보고/최소 계약은 남아 Status는 OPEN이다. [V 승인](product-decisions.md#review-20261013-v-batch); BR-OPS-032; V-123 미구성·미실행.

2026-10-13 W1/W2=1 부분 해결: 과거 Trainer Home 오류에 따른 일반/지원 전환은 Master Organization 전용 명시적 정정으로 같은 PT/기존 Pass 차감·최초 생성 시각을 유지한다. 일반은 최초 기록 생성 시점 설정/소비 Pass 발급 조건, 지원은 기존 관리자 범위 수동 추가실적이다. 이전 결과 이력/유효 합계 단일 반영을 보존하고 영향 건 분류/보상·비용 정정 완료 전 해당 Trainer·월 확정/재확정을 차단한다. 소속 정정만으로 기존 확정본 자동 해제/변경 없음·기존 권한/사유·필요한 월 해제/명시적 정정/동일 월 재확정·이전본 보존을 유지한다. 역사 사실·영향/완료 증거·나머지 상태/최소 계약/경합이 남아 OPEN을 유지한다. [W 승인](product-decisions.md#review-20261013-w-batch); BR-OPS-033/PAY-024; V-124/125 미구성·미실행.

<a id="mb-002"></a>
## MB-002. Branch / Member

Question / TODO: Member 과거 Home 오류의 구체 정정 범위/현재 Home 영향·역사 사실/상태·최소 계약과 타 지점 발급용 추가 공개 정보/선택 응답·나머지 계정 절차를 구체화한다. V1로 이미 기록된 과거 Home 오류는 Master Organization 전용/사유 필수·원래 이력 보존으로 정정한다. 현재 Home Branch Admin의 일반 이동 권한으로 과거 이력을 정정하지 않는다. 일반 이동의 기존 Actor/현재 Home 기준·즉시 적용/미래 예약 미지원·활성 대상/받는 지점 별도 승인 없음·지원 조회 유지와 타 지점 새 Pass 발급/Member Home 유지/실제 Issued 기록은 유지한다. 과거 PT/지급/정산을 자동 변경하지 않으며 이미 승인된 이동/정정 허용을 재질문하지 않는다.

Status: OPEN

Related decisions / requirements: PD-004/007; PR-002/003/008/030. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Member 관계·Branch 이동·조회 범위 상세 설계 확정 전

확정된 경계: 단일 Home Branch와 허용된 타 지점 PT 이용은 CLOSED. Home Branch가 다르다는 이유만으로 PT 이용을 일률 차단하지 않는다. Member는 Login Account와 별개다.

2026-10-12 사용자 확정: Member를 Trainer의 지원 조회 대상으로 지정할 권한은 Master Organization 전체/Branch Admin 지정 시점 현재 관리 Branch=Member 현재 Home Branch 범위다(BR-OPS-005). 수행/발급/Trainer 소속 지점만으로 권한을 얻지 않고 Member Home Branch도 지정만으로 바뀌지 않는다. Member 이동 후 기존 지원 허용의 유지/철회 등은 이번 결정으로 확정하지 않는다.

2026-10-12 사용자 확정(회원 소속 지점 변경 시 기존 지원 조회 허용 질문의 1번): 동일 Organization 안에서 Member Home Branch가 변경되어도 기존 Trainer/Member의 개별 지원 조회 허용은 유지하며 이동만으로 자동 해제하거나 재지정을 요구하지 않는다. 이동 후 지정·수동 해제는 각 처리 시점 Member의 현재 Home Branch를 관리하는 Branch Admin 또는 Master가 담당한다. 수원 Member S가 강남으로 이동하면 기존 Trainer A/S 허용은 유지하고, 강남 Branch Admin/Master가 관리하며 별도 현재 관리 권한 없는 이전 수원 Branch Admin은 과거 지정 사실만으로 지정/해제할 수 없다. 기존 지정/해제 감사 이력과 현재 Caller 인가를 유지한다. 이동 자체의 권한/시점·이력/정정·다른 조회 조건은 OPEN이다.

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

2026-10-12 사용자 확정(회원 소속 지점 변경 권한 질문의 1번): 동일 Organization 안에서 Member의 Home Branch는 Master Admin 또는 변경 요청 처리 시점 Member의 현재 Home Branch를 관리하는 Branch Admin이 변경할 수 있다. 받는 지점의 별도 승인 없이 처리한다. Master는 Organization 전체 범위이며 Branch Admin은 변경 전 현재 관리 Member만 대상으로 한다. 받는 지점 관리자라는 이유나 과거 소속·이전 변경자/지원 지정자·Pass Issued Branch·수업 Performed Branch 사실만으로 다른 현재 소속 Member를 이동시킬 수 없다. 관리자 권한 없는 Operator·Trainer는 수행할 수 없고 관리자 겸임자는 해당 관리 권한으로 판단한다(BR-OPS-007, PD-004, PR-002/030, MB-002, NFR-001).

기존 결정 적용: 변경된 Home Branch가 반영된 이후의 Member 관리 및 개별 지원 지정/해제는 각 요청의 현재 Home Branch와 관리 Scope를 따른다. 이전 지점 관리자는 이전 소속/처리자라는 사실만으로 Home Branch 기반 관리 권한을 유지하지 않는다. 기존 담당·개별 지원 조회 허용과 별도의 Pass 발급 지점/수업 수행 지점 기준 업무 등 독립적으로 인가되는 권한은 각각 기존 규칙을 적용한다. 이동 자체로 개별 지원 허용을 해제/재지정하지 않고, Pass의 Issued Branch·발급 조건·잔여/담당 정보, Trainer Home Branch와 과거 PT 기록/Performed Branch·확정 지급/정산을 자동 변경하지 않는다(BR-OPS-001/004/005).

기존 사용자 일관성 지시 적용(2026-10-11): Member 소속 변경은 관리 Scope에 영향을 주는 중요 변경이므로 기존 중요 행위/인가 변경의 이력·감사 원칙을 적용한다. 대상 Member·변경 전후 Home Branch·변경 Actor/권한·Branch Context·시점을 추적한다. 이번 권한 승인이 감사 저장 구조나 이동 적용 시점·예약/소급·변경 사유 입력/정정 정책을 확정한 것은 아니다(NFR-004, MB-002).

Backend는 이동 요청마다 검증된 Caller의 현재 역할·Organization/관리 Scope와 서버의 Member 현재 Home Branch 및 대상 Branch의 동일 Organization 관계를 확인한다. 요청의 role·source/target branch_id·Member ID를 권한 근거로 신뢰하지 않는다. 이동 권한으로 다른 지점 전체 Member/Trainer/Branch 상세·보상 정보를 공개하지 않는다. 대상 Branch의 활성/비활성 조건, 이동 적용 시점·예약/소급·정정/이력 상세와 최소 대상 Branch 조회·명령/저장/UoW·실패/재시도·동시성 계약은 후속이다. Trainer 소속 변경 권한이나 기존 IAM-001의 지점 조회 범위를 이번 결정으로 확대하지 않는다.

2026-10-12 사용자 확정(회원 소속 변경의 적용 시점 질문의 1번): v1의 Member Home Branch 변경은 저장 완료 즉시 적용만 지원한다. 변경이 성공한 시점부터 새 Home Branch가 현재 소속이 되며, 미래 적용일을 지정해 소속 변경을 예약하는 기능은 제공하지 않는다. 성공한 저장 이후 시작하는 후속 요청의 Home Branch 기반 관리 및 지원 지정/해제는 새 소속 기준으로 인가한다. 저장에 실패하면 변경 전 Home Branch를 유지한다. 기존 Master Organization 전체/변경 전 Member 현재 Home Branch 관리 Branch Admin 권한과 받는 지점 별도 승인 없음은 유지한다(BR-OPS-007, PD-004, PR-002/030, MB-002, NFR-001/004).

즉시 적용의 경계: 소속 변경 이력은 보존하며 기존 개별 지원 조회 허용을 해제/재지정하지 않는다. Pass Issued Branch·발급/잔여/담당 사실과 과거 PT/Performed Branch·확정 지급/정산은 소속 변경으로 자동 갱신하지 않는다. 이전 소속/처리자만으로 Home Branch 기반 관리 권한을 유지하지 않되, 담당/지원 조회나 발급/수행 지점 기준의 독립 업무 Scope는 각각 기존 규칙을 적용한다. 과거 소속 이력의 오류 정정·소급 여부/방식, 대상 Branch 상태 및 구체 저장/UoW·이미 처리 중인 요청과 동시 이동의 인가/실패 일관성은 후속이다. 이번 결정은 Member 이동 시점이며 Trainer 이동 시점이나 AuthSession 철회 구현/ADR-0004를 승인한 것은 아니다.

2026-10-12 사용자 확정(회원 이동 대상에 비활성 지점을 허용할지 질문의 1번): Member Home Branch의 이동 대상은 동일 Organization 안에서 운영 중인 활성 Branch만 허용한다. 비활성 Branch로의 이동은 허용하지 않으며 Master Admin과 Branch Admin에 동일하게 적용한다. Backend에서도 대상 Branch의 활성 여부를 검증하고 비활성 대상 요청은 거부한다. 거부 시 기존 Member Home Branch·지원 허용·Pass·과거 업무 이력은 유지한다(BR-OPS-007, PD-004, PR-002/030, MB-002/008, NFR-001).

대상 활성 조건의 범위: 기존 이동 Actor/현재 관리 Scope·받는 지점 별도 승인 없음·저장 완료 즉시 적용/미래 예약 미지원은 유지한다. 이번 결정은 새 이동의 대상 Branch 조건이며 Branch 비활성화 가능 조건, 비활성화 당시 기존 Member/Trainer/Pass 처리·자동 이동, 이미 비활성인 출발 지점의 업무 조건이나 재활성화/과거 조회 정책까지 확정한 것은 아니다. 과거 소속 이력 정정/소급·Branch 상태의 저장 표현, 이동과 비활성화의 경합·필수 감사/UoW/실패 계약은 후속이다(MB-002/008).

2026-10-12 사용자 확정(다른 지점에서 새 이용권 구매·발급 질문의 1번): Member는 같은 Organization의 Home Branch 밖 지점에서도 새 PT Pass를 구매·발급받을 수 있다. 수원 소속 회원이 강남에서 발급받으면 Member Home Branch는 수원으로 유지하고 새 Pass의 Issued Branch는 강남으로 기록한다. Member Home Branch와 Issued Branch가 같아야 한다는 제한을 두지 않는다. 기존 Member 식별자/소속·보유 Pass와 과거 PT/지급·정산 이력은 유지하며 타 지점 발급을 위해 Member를 지점별로 복제하거나 소속을 자동 이동하지 않는다(BR-OPS-001/010, PD-004/007, PR-002/003/030).

이번 결정은 발급 대상 Member 소속과 실제 Issued Branch가 달라도 새 발급 가능하다는 경계를 해결했다. Member/기존 Pass·과거 이력 유지, 공통 상품/판매 중단·발급 조건 보존과 이후 Issued Branch 관리 원칙을 적용한다. Master·Branch Admin·Operator의 발급 허용/각 역할의 실제 발급 Branch 범위와 Trainer 단독 불가는 후속 승인으로 해결됐다(2026-10-12). 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·실제 발급 지점 선택 및 활성/초기 조건, 타 지점 Member 발급용 추가 공개 정보·Member 선택용 최소 식별 응답/계약 및 계약/저장/UoW·재시도/동시성은 계속 OPEN이다. 발급용 같은 Organization 전체 지점 이름·전화번호 일부 검색은 후속 2번 승인으로 해결됐다(BR-OPS-010).

2026-10-12 사용자 확정(새 이용권 발급 Actor 질문의 1번): 새 PT Pass 발급은 Master Admin·Branch Admin·Operator에게 각자의 허용된 실제 Issued Branch 범위에서 허용한다. Master는 Organization 전체, Branch Admin은 자신의 단일 관리 Branch, Operator는 부여된 허용 발급 Branch Scope에서 처리한다. 같은 Organization의 Member는 Home Branch가 발급 지점과 달라도 대상이 될 수 있으며 기존 Member/Home Branch를 유지하고 새 Pass에 실제 Issued Branch를 기록한다(BR-OPS-010, PD-004/007, PR-003/030).

이번 결정은 새 Pass 발급 Actor와 역할별 발급 지점 경계만 해결했다. 권한 경계: Trainer 역할만으로는 새 Pass를 발급할 수 없다. Trainer를 겸하는 계정에 Master·Branch Admin·Operator의 발급 권한이 있으면 해당 역할의 독립적인 발급 Scope로 판단하며 별도 계정을 요구하지 않는다. Operator의 새 발급 권한은 공통 상품 생성/수정, 기존 Pass 수동 횟수 조정·만료/해제·담당 교체, Member 소속 이동, PT 정정/취소·Compensation Setting·Additional Performance·월 정산의 별도 권한을 추가하지 않는다. 발급 대상 식별을 타 지점 전체 Member 목록/전화번호·다른 Pass/PT/민감 보상 정보의 일반 조회 허용으로 확대하지 않는다. 기존 보상 설정 접근 제한과 Trainer의 담당/개별 지원 회원 조회는 그대로다.

남은 결정: 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차과 실제 발급 지점 선택/계약, 지점/Member/Trainer 활성·발급 시 활성 담당 필수/상품 최초 횟수의 나머지 상태/선택 계약, 타 지점 Member 추가 공개 정보·Member 선택용 최소 식별 응답/계약과 업무 인가 경로는 ARCH-001·MB-001/002/003/004/005·BR-001/002/010 후속이다. 승인된 Master·Branch Admin·Operator의 발급 허용과 Trainer 단독 불가를 다시 미결정으로 두지 않으며, 미정 Scope 부여/조회·상태 조건을 임의 기본값으로 구현하지 않는다. 발급/상품 조건·감사 계약/저장·Application UoW·실패/재시도/중복 및 판매 중단/지점 상태/Member 이동/인가 변경 경합은 후속 Architecture 설계·검증 대상이다.

2026-10-12 사용자 확정(발급용 타 지점 회원 검색 질문의 2번): Branch Admin·Operator는 자신의 허용된 실제 Issued Branch에서 새 PT Pass를 발급하기 위해 같은 Organization 전체 지점의 Member를 이름·전화번호 일부로 검색할 수 있다. 전화번호 전체 일치만을 요구하지 않으며 Member Home Branch가 Caller의 관리/발급 Branch와 다르다는 이유만으로 검색 후보에서 제외하지 않는다. Master의 기존 Organization 전체 범위는 유지한다. 검색은 기존 Member를 선택하여 실제 발급 지점의 새 Pass를 만드는 흐름이며 Member 소속 이동/복제나 기존 Pass·PT·지급·정산 변경을 수행하지 않는다(BR-OPS-010, PD-004/007/022, PR-002/003/030).

검색 인가/정보 공개 경계: 이 허용은 이용권 발급용 Member 검색의 후보 범위·검색 방식과 이름/전체 전화번호/현재 Member Home Branch 공개다. Backend는 매 검색/선택/발급 요청에서 현재 Caller의 발급 역할/Organization·허용 실제 Issued Branch와 대상 Member의 실제 Organization을 검증한다. 검색 Branch Context를 위조하거나 과거 검색 결과/선택 Member ID로 철회된 역할·Scope 또는 다른 Organization을 우회할 수 없다. 같은 전화번호/이름의 여러 Member는 별도 식별자로 구분하여 선택하며 번호만으로 병합하거나 첫 결과를 자동 선택하지 않는다. 이 세 항목의 읽기 허용이 회원 정보/전화번호 수정·일반 Member 상세·전체 무조건 목록/일괄 내보내기, 다른 개인정보/Pass/PT/보상 정보 열람 권한을 추가하지 않는다. Trainer 단독의 담당/개별 지원 Member 검색 및 기존 전체 전화번호 공개는 유지하고 발급 역할 겸임은 그 독립 발급 업무 Scope로 판단한다. 응답은 승인된 공개 범위 안에서 구성하며 Member 선택용 최소 식별 응답/계약과 추가 공개 정보는 후속이다. 실제 운영 연락처/검색어를 문서·일반 로그에 복사하지 않는다.

이번 결정으로 발급용 검색 후보의 Organization 전체 지점 범위·이름/전화번호 일부 검색과 결과의 이름/전체 전화번호/현재 Member Home Branch 공개는 해결됐다. 추가 공개 정보·Member 선택용 최소 식별 응답/계약 및 나머지 검색/대상 조건, 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·실제 발급 지점 선택, 발급 시 활성 담당 필수/상품 최초 횟수의 나머지 상태·계약/저장/UoW·실패/재시도/중복·권한/소속/상품/지점 상태 변경 경합은 후속이다. 승인된 세 항목의 공개/전화번호 비마스킹을 다시 미결정으로 두지 않는다. Product OPEN/ADR·모듈/계약 상태와 기존 보상 설정 접근 제한을 유지하며 실제 검색/발급 구현·검증 완료를 뜻하지 않는다.

2026-10-12 사용자 확정(발급용 검색 결과 표시 정보 질문의 1번): 새 PT Pass 발급용 Member 검색 결과에는 이름·전체 전화번호·소속 지점을 표시한다. 소속 지점은 해당 Member의 현재 Home Branch이며 Caller 관리 지점/Pass Issued Branch/수업 Performed Branch와 구별한다. 같은 Organization의 타 지점 회원 검색 결과에도 동일하게 적용하고 부분 마스킹된 번호만 표시하도록 제한하지 않는다. 기존 이름·전화번호 일부의 Organization 전체 지점 검색과 현재 발급 역할/실제 Issued Branch Scope 인가는 유지한다(BR-OPS-010, PD-004/007/022, PR-002/003/030, NFR-001/005).

공개 범위 게이트 갱신: 검색 결과의 이름·전체 전화번호·현재 Member Home Branch 표시는 해결됐다. 검색/선택/발급마다 기존 현재 Caller/역할·실제 Issued Branch/Organization을 검증하며 다른 개인정보/일반 회원 상세·다른 Pass/PT·보상/내보내기·수정 권한을 추가하지 않는다. 공유 번호/동명이인의 Member 구분·선택과 기존 Trainer 조회 제한을 유지한다. 추가 공개 정보·최소 선택 응답/계약과 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·나머지 검색/대상/발급 조건/일관성은 후속이며 이 OPEN 전체를 CLOSED로 바꾸지 않는다(BR-OPS-010).

2026-10-12 사용자 확정(Operator 업무 허용 지점 수 질문의 1번): v1 Operator 역할의 업무 허용 Branch는 한 시점에 하나만 지정한다. Operator는 그 지정된 단일 Branch에서 명시적으로 허용된 업무를 수행하며 같은 계정의 Operator 권한을 여러 Branch에 동시 부여하지 않는다. Branch당 Operator 한 명이라는 1:1 인원 제한을 추가하지 않으며 하나의 Branch에 여러 Operator가 있을 수 있다. 이 결정은 Operator 역할의 업무 Scope이며 기존에 허용된 겸임 역할의 독립적인 관리/PT 권한이나 Trainer Home Branch를 바꾸지 않는다(BR-OPS-011, PD-001/007, PR-001/003/030, ARCH-001, MB-004).

이번 결정은 Operator 동시 허용 Branch를 하나로 확정한 것이다. 새 Operator 발급/최초 지점 지정 Actor는 Master Organization 전체/Branch Admin 자기 단일 Branch로 후속 승인됐다. 발급 절차·기존 계정 역할 부여/변경·지점 변경의 대상/절차·나머지 행위 권한은 계속 OPEN이다. Operator 지점 변경 Actor는 Master 전용으로 후속 승인됐으며 기존 저장 후 현재 Scope 반영/실패 보존·감사 원칙을 적용한다. 발급용 이름/전화번호 일부의 같은 Organization 전체 지점 Member 검색과 이름·전체 전화번호·현재 Member Home Branch 공개는 유지하고 다른 Branch 발급/일반 조회 권한을 추가하지 않는다. 기존 겸임의 독립 Scope와 민감 보상 제한·IAM S1 후속 범위를 유지한다(BR-OPS-010/011).

2026-10-12 사용자 확정(Operator 계정 발급과 최초 지점 지정 권한 질문의 1번): Master Admin은 자신의 Organization 범위에서, Branch Admin은 자신의 단일 관리 Branch 범위에서 새 Operator 계정을 발급하고 그 한 지점을 최초 업무 Branch로 지정할 수 있다. Branch Admin의 타 지점 Operator 발급은 허용하지 않는다. Backend는 처리 시점의 검증된 현재 Caller 역할/Organization·관리 Branch와 대상 Branch의 실제 Organization 관계를 확인하며 직접 ID·위조 role/branch_id·과거 권한으로 범위를 우회할 수 없다. Operator 단독·Trainer 단독의 로그인 계정 발급은 허용하지 않는다(BR-OPS-011, PD-019, PR-021/030, NFR-001/004, MB-004, ARCH-001/002).

이번에 해결된 것은 새 Operator 계정 발급/최초 지점 지정 Actor와 허용 Scope다. Operator 지정 Branch 변경은 Master 전용으로 후속 승인됐다. 기존 계정 역할 추가/변경·Operator 변경 대상/절차·계정 수명 업무 및 Operator·Trainer 신규 발급 외 계정 업무 위임은 계속 OPEN이다. 신규 Trainer 발급 Actor/Scope는 BR-OPS-012의 후속 승인을 적용한다. 발급 관리자의 일회용 최초 비밀번호 설정 링크 전달은 기존 승인 방식을 재사용하며 상세 전달/수명은 ARCH-002다. IAM-001 S1의 기존 최소 관리자 흐름/ADR-0004 v1 인증 방식 ACCEPTED를 변경하지 않는다.

2026-10-12 G 일괄 승인 반영: G4/G5: Home Branch 비활성 Member도 다른 활성 지점에서 기존 허용 조건으로 수업할 수 있다. Master/변경 전 현재 Home Branch 관리 Branch Admin이 활성 지점으로 명시적 이동할 수 있고 받는 지점 별도 승인 없음/즉시 적용·관계/이력 보존과 이동 후 현재 소속 인가를 유지한다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). 다른 상태/신규 배정·역사 사실/구체 계약·경합 등 나머지 게이트로 이 복합 OPEN은 유지한다.

2026-10-12 J 일괄 승인 반영: J1/J2로 회원 등록/이름·전화번호 수정 및 Member 비활성화/재활성화 Actor·Home Branch Scope를 확정했다(BR-OPS-021/022). J3로 Member 자체 비활성의 새 Pass/비활성 기간 실제 수업 차단·잔여/관계·이력 보존/같은 Member 재활성화 후 조건부 이용을 확정했다. Home Branch 자체 비활성의 G4 타 지점 이용과 구별하고 기존 다른 공개/상태·역사 사실/정정·인가/계약/경합은 남는다. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch). 이 복합 OPEN의 나머지 항목은 유지한다.

2026-10-13 V1=1 부분 해결: Trainer/Member의 이미 기록된 과거 Home 이력 오류는 Master 자기 Organization 전용/사유 필수·원래 이력/감사 보존으로 정정한다. 일반 이동의 즉시 적용/미래 예약 미지원은 유지하고 기존 PT/지급·정산 확정본을 자동 덮어쓰지 않는다. 영향 건은 기존 업무별 권한/정정·필요한 월 확정 해제/동일 월 재확정·이전본 보존을 따른다. 구체 역사 사실/현재 Home 영향·분류가 바뀌는 수업 정정/지급 기준·비용 보고/최소 계약은 남아 Status는 OPEN이다. [V 승인](product-decisions.md#review-20261013-v-batch); BR-OPS-032; V-123 미구성·미실행.

<a id="mb-003"></a>
## MB-003. Pass Branch 귀속 / 교차 사용

Question / TODO: 새 Pass 발급/사용을 위한 나머지 Member·Trainer/Pass 검색·최소 식별/공개 정보와 Operator/관리 Scope 지정·변경의 절차/계약을 구체화한다(MB-001/002/004/005 연결). 타 지점 발급/Member Home 유지/실제 Issued 기록·같은 Organization 적격 Pass 타 지점 사용 사전 승인 없음·O 전체 적격 Pass 선택/본인 담당 Pass 없는 지원 등록을 유지한다. P1/P2의 현재 지원으로 지정 전 본인 수업 등록·해제 후 실제 허용 기간 본인 수업의 늦은 등록/일반 조회·전화번호 비복원은 확정됐다. 현재 Member Home 관리자 지원 지정/해제·자동 종료 없음/Home 이동 유지·전체 잔여 선택 필터/허용 전체 전화번호를 유지한다. 전체 후보/제한된 과거 등록은 개별 Pass·다른 Trainer PT/금액 무제한 공개가 아니다. 역사 사실 확인 불가/충돌·상태/최소 응답·계약은 후속이다.

Status: OPEN

Related decisions / requirements: PD-004/007; PR-003/008/030; BR-PAY-006. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Pass 사용 가능 범위·선택·차감 및 관련 권한 상세 설계 확정 전

확정된 경계: Pass의 단일 Issued Branch와 허용된 타 지점 사용 가능은 CLOSED. 발급 지점이 유일한 사용 지점은 아니다. 사용 가능한 Pass 내 FIXED_AMOUNT 우선/FIFO는 유지한다. Trainer는 본인 담당 또는 개별 허용 지원 회원만 검색/조회하며 같은 지점·교차 사용 가능 사실만으로 전체 회원 조회를 허용하지 않는다(2026-10-12 확정, BR-OPS-005). 지원 대상 허용과 Pass 사용의 발급 지점 사전 승인 없음은 구별한다.

2026-10-11 사용자 확정(타 지점 이용권 사용 사전 승인 질문의 1번): 동일 Organization 안에서 사용 가능한 Pass의 교차 사용에 발급 지점 관리자 등의 사전 승인을 두지 않는다. Issued Branch 차이로 후보를 제외하거나 발급 지점 우선순위를 추가하지 않고 기존 FIXED_AMOUNT 우선/FIFO·지점 사실 보존을 유지한다. 타 지점 전체 목록 조회나 PT 업무 Actor 권한을 자동 부여하지 않는다. 승인 필요 여부는 해결됐으며 관련 조회/업무 접근과 나머지 사용 조건은 위 연결 게이트에서 계속 검토한다(BR-OPS-001/BR-PAY-006).

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

2026-10-12 사용자 확정(이용권의 담당 Trainer 교체): 기존 Pass에서 담당을 바꿀 수 있으며 잔여/발급 조건·Issued Branch·과거 PT/지급 이력을 보존한다(BR-OPS-008). 교체 Actor/Branch Scope·대상 Trainer의 지점/활성·Pass 상태 조건은 후속으로 남긴다. 동일 Organization 교차 Pass 사용이나 지원 조회 허용만으로 교체 명령 권한을 부여하지 않는다. 현재 담당 기반 조회와 이력/감사는 기존 사용자 일관성 지시를 적용한다.

2026-10-12 사용자 확정(담당 교체 권한의 기준 지점 질문의 1번): 기존 Pass의 Assigned Trainer 교체는 Master Admin의 Organization 전체 범위 또는 처리 시점 Member의 현재 Home Branch를 관리하는 Branch Admin에게 허용한다. 수원 발급 Pass의 회원이 현재 강남 소속이면 강남 Branch Admin 또는 Master가 교체할 수 있으며, 수원 Branch Admin은 Issued Branch만을 근거로 교체할 수 없다. 회원 소속이 다시 변경되면 각 교체 요청은 변경된 현재 Home Branch 기준으로 인가한다. 이용권 수동 만료/해제의 Issued Branch 기준은 그대로 유지한다(BR-OPS-004/008, PD-007, PR-003/030).

후속 게이트 갱신: 담당 교체 Actor/Branch Scope와 대상 Trainer 지점 조건은 2026-10-12 사용자 결정으로 해결됐다. 조회 허용과 교체 명령 인가는 구별하며 비관리자/위조 Scope/Issued Branch만의 권한 주장은 거부한다. 교체 전 실제 본인 수업의 이전 담당 직접 등록 허용은 해결됐다(2026-10-12, BR-OPS-003/008). 잔여 소진 외 수동 만료/취소 등 나머지 Pass 상태·과거 담당/수행 사실 확인 불가/정정과 최소 식별/Trainer 선택 정보·공개 계약/이력/저장/UoW·동시성은 계속 OPEN이다. 보상 설정 인가와 수동 만료/해제의 Issued Branch 기준은 바꾸지 않는다.

2026-10-12 사용자 확정(교체할 Trainer의 소속 지점 질문의 1번): 기존 Pass의 담당 교체 대상은 같은 Organization의 Trainer이며 Member 현재 Home Branch와 다른 지점 소속 Trainer도 허용한다. 강남 회원의 담당을 수원 소속 Trainer로 바꿀 수 있다. Member와 같은 지점 소속이어야 한다는 제한을 두지 않으며 다른 Organization Trainer는 지정할 수 없다. 교체 요청의 Actor 권한은 기존대로 Master Organization 전체 또는 Branch Admin 처리 시점 Member 현재 Home Branch 기준이다(BR-OPS-008, PD-007, PR-003/029/030).

타 지점 담당 허용은 현재 관계 기반 회원 조회와 기존 수업 수행 지점/당시 Trainer Home Branch 보상 구분을 유지한다. 교체 전 본인 수업의 이전 담당 직접 등록 허용은 해결(2026-10-12)됐으며 잔여 소진 외 수동 만료/취소 등 나머지 Pass 상태·과거 담당/수행 사실 확인 불가/정정 및 최소 식별/Trainer 선택 정보·계약/경합은 계속 OPEN이며 다른 지점 전체 목록/민감 보상 공개 권한을 부여하지 않는다.

2026-10-12 사용자 확정(담당 교체 전 수업의 누락 등록 질문의 1번): A가 담당으로 실제 수업을 진행한 뒤 담당이 B로 바뀌어도 A는 교체 전 본인 수업을 직접 늦게 등록할 수 있다. 예: 9월 5일 A 수업 → 9월 6일 B로 담당 교체 → 9월 7일 A 누락 등록. 실제 수업 당시 A의 담당 관계와 본인 수행 사실, 현재 검증된 Caller/Trainer 연결·Organization 및 기존 Pass/정산 조건을 확인한다. 현재 담당이 B라는 이유만으로 관리자 대행이나 A 재배정을 요구하지 않는다. 이 허용만으로 A의 해당 회원 목록/상세·전화번호/다른 Pass·다른 Trainer 기록 조회 권한을 복원하지 않는다(BR-OPS-003/005/008, PD-008, PR-008/029/030).

이번 결정은 교체 전 실제 본인 수업의 이전 담당 직접 등록 허용을 해결한 것이다. BR-OPS-003의 기존 미확정 월/Pass 조건·실제 수행 A 기준 지급과 회원 조회 비복원 경계를 유지한다. 과거 담당/수행 사실 확인 불가/정정·동일 시점 순서·다른 관계의 나머지 인가, 최소 식별/응답 및 계약/저장/UoW·교체/등록/월 확정 경합은 계속 OPEN이다.

2026-10-12 사용자 확정(잔여 0회인 이용권의 담당 교체 질문의 1번): Remaining이 0인 기존 Pass도 Assigned Trainer를 교체할 수 있다. 잔여를 모두 사용해 이용이 끝난 Pass도 포함한다. 같은 Pass에서 담당 A를 B로 바꾸며 Remaining 0·발급 조건/Issued Branch·과거 실제 수행 Trainer/PT 기록·확정 지급/정산 이력은 유지한다. 새 담당 B는 기존 현재 담당 관계에 따른 Member 조회·응대를 이어갈 수 있다. 기존 Master Organization 전체/Branch Admin 처리 시점 Member 현재 Home Branch 권한과 같은 Organization의 다른 지점 Trainer도 대상 허용 원칙은 유지한다(BR-OPS-005/008, PD-007, PR-003/029/030).

후속 게이트 갱신: 잔여 0으로 이용을 마친 Pass의 담당 교체/새 담당 Member 조회만 추가 해결됐다. 잔여 0 유지·현재 Caller/Member/Organization/담당 관계 검증·선택 필터의 Member 전체 Pass 기준과 실제 PT 잔여 > 0 조건은 유지한다. 수동 만료/취소 등 다른 종료 사유의 담당 관계/교체와 과거 사실/최소 정보·저장/응답/UoW·동시성은 계속 OPEN이다.

2026-10-12 사용자 확정(다른 지점에서 새 이용권 구매·발급 질문의 1번): Member는 같은 Organization의 Home Branch 밖 지점에서도 새 PT Pass를 구매·발급받을 수 있다. 수원 소속 회원이 강남에서 발급받으면 Member Home Branch는 수원으로 유지하고 새 Pass의 Issued Branch는 강남으로 기록한다. Member Home Branch와 Issued Branch가 같아야 한다는 제한을 두지 않는다. 기존 Member 식별자/소속·보유 Pass와 과거 PT/지급·정산 이력은 유지하며 타 지점 발급을 위해 Member를 지점별로 복제하거나 소속을 자동 이동하지 않는다(BR-OPS-001/010, PD-004/007, PR-002/003/030).

이번 결정은 발급 대상 Member 소속과 실제 Issued Branch가 달라도 새 발급 가능하다는 경계를 해결했다. Member/기존 Pass·과거 이력 유지, 공통 상품/판매 중단·발급 조건 보존과 이후 Issued Branch 관리 원칙을 적용한다. Master·Branch Admin·Operator의 발급 허용/각 역할의 실제 발급 Branch 범위와 Trainer 단독 불가는 후속 승인으로 해결됐다(2026-10-12). 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·실제 발급 지점 선택 및 활성/초기 조건, 타 지점 Member 발급용 추가 공개 정보·Member 선택용 최소 식별 응답/계약 및 계약/저장/UoW·재시도/동시성은 계속 OPEN이다. 발급용 같은 Organization 전체 지점 이름·전화번호 일부 검색은 후속 2번 승인으로 해결됐다(BR-OPS-010).

2026-10-12 사용자 확정(새 이용권 발급 Actor 질문의 1번): 새 PT Pass 발급은 Master Admin·Branch Admin·Operator에게 각자의 허용된 실제 Issued Branch 범위에서 허용한다. Master는 Organization 전체, Branch Admin은 자신의 단일 관리 Branch, Operator는 부여된 허용 발급 Branch Scope에서 처리한다. 같은 Organization의 Member는 Home Branch가 발급 지점과 달라도 대상이 될 수 있으며 기존 Member/Home Branch를 유지하고 새 Pass에 실제 Issued Branch를 기록한다(BR-OPS-010, PD-004/007, PR-003/030).

이번 결정은 새 Pass 발급 Actor와 역할별 발급 지점 경계만 해결했다. 권한 경계: Trainer 역할만으로는 새 Pass를 발급할 수 없다. Trainer를 겸하는 계정에 Master·Branch Admin·Operator의 발급 권한이 있으면 해당 역할의 독립적인 발급 Scope로 판단하며 별도 계정을 요구하지 않는다. Operator의 새 발급 권한은 공통 상품 생성/수정, 기존 Pass 수동 횟수 조정·만료/해제·담당 교체, Member 소속 이동, PT 정정/취소·Compensation Setting·Additional Performance·월 정산의 별도 권한을 추가하지 않는다. 발급 대상 식별을 타 지점 전체 Member 목록/전화번호·다른 Pass/PT/민감 보상 정보의 일반 조회 허용으로 확대하지 않는다. 기존 보상 설정 접근 제한과 Trainer의 담당/개별 지원 회원 조회는 그대로다.

남은 결정: 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차과 실제 발급 지점 선택/계약, 지점/Member/Trainer 활성·발급 시 활성 담당 필수/상품 최초 횟수의 나머지 상태/선택 계약, 타 지점 Member 추가 공개 정보·Member 선택용 최소 식별 응답/계약과 업무 인가 경로는 ARCH-001·MB-001/002/003/004/005·BR-001/002/010 후속이다. 승인된 Master·Branch Admin·Operator의 발급 허용과 Trainer 단독 불가를 다시 미결정으로 두지 않으며, 미정 Scope 부여/조회·상태 조건을 임의 기본값으로 구현하지 않는다. 발급/상품 조건·감사 계약/저장·Application UoW·실패/재시도/중복 및 판매 중단/지점 상태/Member 이동/인가 변경 경합은 후속 Architecture 설계·검증 대상이다.

2026-10-12 사용자 확정(발급용 타 지점 회원 검색 질문의 2번): Branch Admin·Operator는 자신의 허용된 실제 Issued Branch에서 새 PT Pass를 발급하기 위해 같은 Organization 전체 지점의 Member를 이름·전화번호 일부로 검색할 수 있다. 전화번호 전체 일치만을 요구하지 않으며 Member Home Branch가 Caller의 관리/발급 Branch와 다르다는 이유만으로 검색 후보에서 제외하지 않는다. Master의 기존 Organization 전체 범위는 유지한다. 검색은 기존 Member를 선택하여 실제 발급 지점의 새 Pass를 만드는 흐름이며 Member 소속 이동/복제나 기존 Pass·PT·지급·정산 변경을 수행하지 않는다(BR-OPS-010, PD-004/007/022, PR-002/003/030).

검색 인가/정보 공개 경계: 이 허용은 이용권 발급용 Member 검색의 후보 범위·검색 방식과 이름/전체 전화번호/현재 Member Home Branch 공개다. Backend는 매 검색/선택/발급 요청에서 현재 Caller의 발급 역할/Organization·허용 실제 Issued Branch와 대상 Member의 실제 Organization을 검증한다. 검색 Branch Context를 위조하거나 과거 검색 결과/선택 Member ID로 철회된 역할·Scope 또는 다른 Organization을 우회할 수 없다. 같은 전화번호/이름의 여러 Member는 별도 식별자로 구분하여 선택하며 번호만으로 병합하거나 첫 결과를 자동 선택하지 않는다. 이 세 항목의 읽기 허용이 회원 정보/전화번호 수정·일반 Member 상세·전체 무조건 목록/일괄 내보내기, 다른 개인정보/Pass/PT/보상 정보 열람 권한을 추가하지 않는다. Trainer 단독의 담당/개별 지원 Member 검색 및 기존 전체 전화번호 공개는 유지하고 발급 역할 겸임은 그 독립 발급 업무 Scope로 판단한다. 응답은 승인된 공개 범위 안에서 구성하며 Member 선택용 최소 식별 응답/계약과 추가 공개 정보는 후속이다. 실제 운영 연락처/검색어를 문서·일반 로그에 복사하지 않는다.

이번 결정으로 발급용 검색 후보의 Organization 전체 지점 범위·이름/전화번호 일부 검색과 결과의 이름/전체 전화번호/현재 Member Home Branch 공개는 해결됐다. 추가 공개 정보·Member 선택용 최소 식별 응답/계약 및 나머지 검색/대상 조건, 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·실제 발급 지점 선택, 발급 시 활성 담당 필수/상품 최초 횟수의 나머지 상태·계약/저장/UoW·실패/재시도/중복·권한/소속/상품/지점 상태 변경 경합은 후속이다. 승인된 세 항목의 공개/전화번호 비마스킹을 다시 미결정으로 두지 않는다. Product OPEN/ADR·모듈/계약 상태와 기존 보상 설정 접근 제한을 유지하며 실제 검색/발급 구현·검증 완료를 뜻하지 않는다.

2026-10-12 사용자 확정(발급용 검색 결과 표시 정보 질문의 1번): 새 PT Pass 발급용 Member 검색 결과에는 이름·전체 전화번호·소속 지점을 표시한다. 소속 지점은 해당 Member의 현재 Home Branch이며 Caller 관리 지점/Pass Issued Branch/수업 Performed Branch와 구별한다. 같은 Organization의 타 지점 회원 검색 결과에도 동일하게 적용하고 부분 마스킹된 번호만 표시하도록 제한하지 않는다. 기존 이름·전화번호 일부의 Organization 전체 지점 검색과 현재 발급 역할/실제 Issued Branch Scope 인가는 유지한다(BR-OPS-010, PD-004/007/022, PR-002/003/030, NFR-001/005).

공개 범위 게이트 갱신: 검색 결과의 이름·전체 전화번호·현재 Member Home Branch 표시는 해결됐다. 검색/선택/발급마다 기존 현재 Caller/역할·실제 Issued Branch/Organization을 검증하며 다른 개인정보/일반 회원 상세·다른 Pass/PT·보상/내보내기·수정 권한을 추가하지 않는다. 공유 번호/동명이인의 Member 구분·선택과 기존 Trainer 조회 제한을 유지한다. 추가 공개 정보·최소 선택 응답/계약과 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·나머지 검색/대상/발급 조건/일관성은 후속이며 이 OPEN 전체를 CLOSED로 바꾸지 않는다(BR-OPS-010).

2026-10-12 사용자 확정(Operator 업무 허용 지점 수 질문의 1번): v1 Operator 역할의 업무 허용 Branch는 한 시점에 하나만 지정한다. Operator는 그 지정된 단일 Branch에서 명시적으로 허용된 업무를 수행하며 같은 계정의 Operator 권한을 여러 Branch에 동시 부여하지 않는다. Branch당 Operator 한 명이라는 1:1 인원 제한을 추가하지 않으며 하나의 Branch에 여러 Operator가 있을 수 있다. 이 결정은 Operator 역할의 업무 Scope이며 기존에 허용된 겸임 역할의 독립적인 관리/PT 권한이나 Trainer Home Branch를 바꾸지 않는다(BR-OPS-011, PD-001/007, PR-001/003/030, ARCH-001, MB-004).

이번 결정은 Operator 동시 허용 Branch를 하나로 확정한 것이다. 새 Operator 발급/최초 지점 지정 Actor는 Master Organization 전체/Branch Admin 자기 단일 Branch로 후속 승인됐다. 발급 절차·기존 계정 역할 부여/변경·지점 변경의 대상/절차·나머지 행위 권한은 계속 OPEN이다. Operator 지점 변경 Actor는 Master 전용으로 후속 승인됐으며 기존 저장 후 현재 Scope 반영/실패 보존·감사 원칙을 적용한다. 발급용 이름/전화번호 일부의 같은 Organization 전체 지점 Member 검색과 이름·전체 전화번호·현재 Member Home Branch 공개는 유지하고 다른 Branch 발급/일반 조회 권한을 추가하지 않는다. 기존 겸임의 독립 Scope와 민감 보상 제한·IAM S1 후속 범위를 유지한다(BR-OPS-010/011).

2026-10-12 사용자 확정(Operator 계정 발급과 최초 지점 지정 권한 질문의 1번): Master Admin은 자신의 Organization 범위에서, Branch Admin은 자신의 단일 관리 Branch 범위에서 새 Operator 계정을 발급하고 그 한 지점을 최초 업무 Branch로 지정할 수 있다. Branch Admin의 타 지점 Operator 발급은 허용하지 않는다. Backend는 처리 시점의 검증된 현재 Caller 역할/Organization·관리 Branch와 대상 Branch의 실제 Organization 관계를 확인하며 직접 ID·위조 role/branch_id·과거 권한으로 범위를 우회할 수 없다. Operator 단독·Trainer 단독의 로그인 계정 발급은 허용하지 않는다(BR-OPS-011, PD-019, PR-021/030, NFR-001/004, MB-004, ARCH-001/002).

이번에 해결된 것은 새 Operator 계정 발급/최초 지점 지정 Actor와 허용 Scope다. Operator 지정 Branch 변경은 Master 전용으로 후속 승인됐다. 기존 계정 역할 추가/변경·Operator 변경 대상/절차·계정 수명 업무 및 Operator·Trainer 신규 발급 외 계정 업무 위임은 계속 OPEN이다. 신규 Trainer 발급 Actor/Scope는 BR-OPS-012의 후속 승인을 적용한다. 발급 관리자의 일회용 최초 비밀번호 설정 링크 전달은 기존 승인 방식을 재사용하며 상세 전달/수명은 ARCH-002다. IAM-001 S1의 기존 최소 관리자 흐름/ADR-0004 v1 인증 방식 ACCEPTED를 변경하지 않는다.

Trainer Home Branch 일반 변경의 Actor는 Master Organization 범위 전용으로 후속 승인됐다(2026-10-12, BR-OPS-013). 기존 저장 후 현재 소속 인가/실패 보존·감사 원칙을 적용하며 계정 역할/관리·Operator Scope·담당/지원 관계와 기존 수업 당시 소속/지급·정산/비용 귀속 규칙은 유지한다. 이동 대상 상태/절차·과거 소속 이력 정정/소급/확인 불가 및 상세 계약·동시성은 후속이며 이 OPEN 전체를 해결한 것은 아니다.

2026-10-12 사용자 확정(잔여가 남은 담당 이용권이 있는 Trainer의 비활성화 질문의 1번): 잔여가 남은 담당 PT Pass가 있어도 Trainer 비활성화를 허용하며 기존 Assigned Trainer 정보는 유지한다. 비활성화 전에 모든 Pass를 다른 Trainer에게 교체하도록 요구하지 않고 자동 담당 해제/재배정도 하지 않는다. 이후 필요할 때 권한 있는 관리자가 BR-OPS-008의 기존 조건/Scope로 담당을 교체한다(BR-OPS-014, PD-007/011, PR-003/005, NFR-001/004, ARCH-001/002, MB-001/003/005, BR-001).

기존 담당 정보 유지와 별도 담당 교체가 해결됐으며 비활성 Trainer의 접근은 계속 차단한다. Member 현재 Home Branch 기반 담당 교체와 Trainer Home Branch 기반 비활성화 권한을 구분하고 잔여/발급 조건·과거 PT/보상을 유지한다. 다른 상태별 교체/사용 조건·개별 지원/재활성화·비활성 상태의 과거 PT 예외 및 구체 저장/현재 인가·UoW/동시성은 후속이다. 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 사용자 확정(담당 Trainer를 새로 지정할 때의 조건 질문의 1번): PT Pass의 담당 Trainer를 새로 지정할 때는 실제 활성 Trainer만 허용한다. 기존 Pass의 담당 교체 및 허용된 새 Pass 발급 흐름에서 담당을 최초 지정하는 경우 모두 적용하며 비활성 Trainer를 미리 배정하지 않는다(BR-OPS-008/014, PD-007, PR-003/005/029/030, NFR-001, ARCH-001, MB-001/003/005, BR-001).

새 지정 대상의 활성 필요조건은 해결됐으며 같은 Organization의 타 지점 허용/기존 행위별 Actor·Scope, 이후 비활성화된 기존 담당 정보 유지·접근 차단을 적용한다. 최초 담당 필수는 해결됐고 나머지 Pass/계정/Branch 상태 조합·최소 선택 정보, 재활성화·개별 지원/비활성 전 수업 예외 및 실제 현재 사실 검증/저장/UoW·지정·비활성화 경합은 후속이다. 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 사용자 확정(비활성화 전 진행했지만 누락된 PT 수업 등록 질문의 1번): Trainer 비활성화 전에 실제로 수행한 미등록 PT 수업은 관리자가 대행 등록하는 경로를 허용한다. 대상 Trainer의 비활성 상태를 유지하며 잠시 재활성화/본인 로그인·담당 재배정을 선행 요구하지 않는다. 실제 수행 Trainer·실제 수업일과 기존 Pass 잔여/정산 조건을 그대로 적용한다(BR-OPS-015, PD-008/011, PR-008/029/030, BR-OPS-003/008/014, BR-PAY-006/011/012).

관리자 대행 경로와 Master Organization/Branch Admin 실제 Performed Branch Scope는 해결됐다. 현재 인가 검증·비활성화 전 실제 수업/담당/소속 사실·시점/확인 불가·최소 선택 정보/사유·증빙과 구체 계약/저장/UoW·경합은 후속이다. 비활성/현재 담당 유지·실제 수행자/수업일·기존 Pass/생성 시점 보상/진행 월 정산·민감 설정 접근 제한을 적용한다. 비활성 Trainer 본인 직접 등록/회원 조회 예외가 아니며 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 일괄 승인 반영: B3/B4/B5/B6: 새 Pass 활성 담당 필수/상품 횟수 최초 부여, 기존 인가 관리자 발급 횟수 초과 잔여 추가, 비활성 Branch 신규 배정/발급/실제 수업 차단과 기존 소속/Pass/이력 보존으로 부분 해결됐다. 발급 Actor Scope는 BR-OPS-010, 조정은 BR-OPS-009를 유지하며 다른 상태 조합/선택 정보·계약은 남는다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch). 이 복합 OPEN의 다른 미결정 항목은 유지한다.

2026-10-12 C 일괄 승인 반영: C12/C13의 Pass 조정 하한/사용 가능·소진·수동 만료 허용을 적용한다. 소진 후 추가의 다른 사용 조건과 수동 만료 별도 해제·Issued Branch 조정 Scope는 유지하며 취소/비활성 지점 결합 상태와 계약은 후속이다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 G 일괄 승인 반영: G3/G4: 비활성 Issued/Home Branch를 먼저 변경하지 않고 다른 활성 지점에서 기존 조건을 충족하는 Pass·Member/활성 Trainer 수업을 허용한다. Issued/발급 조건과 과거 귀속은 보존하고 정상 수업은 1회 차감하며 다른 차단 사유를 면제하지 않는다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). 다른 상태/신규 배정·역사 사실/구체 계약·경합 등 나머지 게이트로 이 복합 OPEN은 유지한다.

2026-10-12 J 일괄 승인 반영: J3의 Member 자체 비활성은 Organization 내 다른 Issued/Performed Branch에서도 새 Pass/비활성 기간 실제 수업을 차단한다. 기존 타 지점 발급/최소 검색 허용은 Member 수정/상태 변경 권한을 주지 않고 J1/J2는 별도 Home Branch 기반 인가다. 기존 잔여/조건/관계·이력은 유지하며 나머지 상태/선택·조회/계약은 후속이다. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch). 이 복합 OPEN의 나머지 항목은 유지한다.

2026-10-13 M2=1: 수동 만료 Pass도 현재 유효 Trainer의 담당 Member/허용 전체 전화번호 조회 근거로 인정하며 만료만으로 조회 관계를 끝내지 않는다. Backend 현재 Caller/Organization·담당 또는 개별 지원 인가, 담당 변경/Trainer 비활성·계정/역할/인증 철회 제한과 실제 PT 사용/만료 전 늦은 등록·전체 잔여 필터를 유지한다. 새 개인정보/다른 Pass/PT/보상·내보내기/수정 권한이나 수동 만료 Pass의 담당 교체 허용은 추가하지 않는다. 해당 조회 부분만 해결됐고 나머지 교체/역사 사실/공개/계약으로 이 복합 OPEN은 유지한다. BR-OPS-005/004; PR-002/003/029/030·NFR-001/005; V-107 예정; [M 승인](product-decisions.md#review-20261013-m-batch).

2026-10-13 O1/O2=1 부분 해결: 담당/개별 지원 회원의 본인 실제 수업 등록은 다른 Trainer 담당분을 포함한 전체 적격 Pass의 FIXED_AMOUNT 우선/FIFO 차감이다. 개별 지원은 본인 담당 Pass 없이도 조회/본인 등록을 허용한다. 담당자·Home/Issued/Performed·실제 수행자 보상/금액 비공개 및 기존 상태/잔여·정산 검증은 유지한다. 지원 관계의 지정 전/해제 후 과거 등록 시간 경계·역사 사실과 나머지 공개/계약 때문에 Status는 OPEN이다. [O 승인](product-decisions.md#review-20261013-o-batch); BR-OPS-026; V-110/111 미구성·미실행.

2026-10-13 P1/P2=1 부분 해결: 현재 유효한 지원 허용으로 지정 전 실제 본인 수업 등록을 허용하며, 해제 후에는 허용 기간에 실제 진행한 본인 수업만 늦게 등록한다. 일반 Member/전화번호 조회 비복원·지정 이력 비소급, 현재 계정/Trainer/실제 수행·과거 허용 사실 및 기존 Pass/정산 조건을 유지한다. 시간 정책은 확정됐고 역사 사실 확인 불가/충돌·나머지 상태/공개·최소 계약 때문에 Status는 OPEN이다. [P 승인](product-decisions.md#review-20261013-p-batch); BR-OPS-027; V-112/113 미구성·미실행.

<a id="mb-004"></a>
## MB-004. Administration / Branch Scope 부여

Question / TODO: 승인된 신규 Operator/Trainer 발급·기존 역할 추가/회수(E5)와 Master 전용 Operator 지점 변경의 나머지 대상/연결/절차·최소 공개/현재 인가·계약, 나머지 계정 업무 위임 및 Branch 기본정보의 다른 필드/입력/감사 공개를 구체화한다. R2로 Branch Admin의 각 처리 시점 자기 단일 관리 Branch 지점명/대표 연락처 수정·중요 감사가 확정됐고 지점 생성/운영 상태/관리자 배정 권한을 추가하지 않는다. 기존 Master Organization 범위·Operator 단일 Branch·Pass 발급 권한/같은 Organization 타 지점 Member 발급·최소 Member 검색 승인과 별도 일반 목록/상세 인가는 유지한다. 이미 승인된 역할/Scope·두 필드 수정 자체를 다시 미결정으로 두지 않는다.

Status: OPEN

Related decisions / requirements: PD-001/004/019; PR-001/020/021/030. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: 계정·Branch 관리·Scope 부여의 상세 권한 설계 확정 전

확정된 경계: Branch Admin은 v1에서 단일 Branch 관리로 CLOSED. 일부 여러 지점만 관리하는 중간 역할은 추가하지 않는다. Master Admin의 Organization 전체 및 구조/계정 관리는 유지한다.

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

2026-10-12 사용자 확정(다른 지점에서 새 이용권 구매·발급 질문의 1번): Member는 같은 Organization의 Home Branch 밖 지점에서도 새 PT Pass를 구매·발급받을 수 있다. 수원 소속 회원이 강남에서 발급받으면 Member Home Branch는 수원으로 유지하고 새 Pass의 Issued Branch는 강남으로 기록한다. Member Home Branch와 Issued Branch가 같아야 한다는 제한을 두지 않는다. 기존 Member 식별자/소속·보유 Pass와 과거 PT/지급·정산 이력은 유지하며 타 지점 발급을 위해 Member를 지점별로 복제하거나 소속을 자동 이동하지 않는다(BR-OPS-001/010, PD-004/007, PR-002/003/030).

이번 결정은 발급 대상 Member 소속과 실제 Issued Branch가 달라도 새 발급 가능하다는 경계를 해결했다. Member/기존 Pass·과거 이력 유지, 공통 상품/판매 중단·발급 조건 보존과 이후 Issued Branch 관리 원칙을 적용한다. Master·Branch Admin·Operator의 발급 허용/각 역할의 실제 발급 Branch 범위와 Trainer 단독 불가는 후속 승인으로 해결됐다(2026-10-12). 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·실제 발급 지점 선택 및 활성/초기 조건, 타 지점 Member 발급용 추가 공개 정보·Member 선택용 최소 식별 응답/계약 및 계약/저장/UoW·재시도/동시성은 계속 OPEN이다. 발급용 같은 Organization 전체 지점 이름·전화번호 일부 검색은 후속 2번 승인으로 해결됐다(BR-OPS-010).

2026-10-12 사용자 확정(새 이용권 발급 Actor 질문의 1번): 새 PT Pass 발급은 Master Admin·Branch Admin·Operator에게 각자의 허용된 실제 Issued Branch 범위에서 허용한다. Master는 Organization 전체, Branch Admin은 자신의 단일 관리 Branch, Operator는 부여된 허용 발급 Branch Scope에서 처리한다. 같은 Organization의 Member는 Home Branch가 발급 지점과 달라도 대상이 될 수 있으며 기존 Member/Home Branch를 유지하고 새 Pass에 실제 Issued Branch를 기록한다(BR-OPS-010, PD-004/007, PR-003/030).

이번 결정은 새 Pass 발급 Actor와 역할별 발급 지점 경계만 해결했다. 권한 경계: Trainer 역할만으로는 새 Pass를 발급할 수 없다. Trainer를 겸하는 계정에 Master·Branch Admin·Operator의 발급 권한이 있으면 해당 역할의 독립적인 발급 Scope로 판단하며 별도 계정을 요구하지 않는다. Operator의 새 발급 권한은 공통 상품 생성/수정, 기존 Pass 수동 횟수 조정·만료/해제·담당 교체, Member 소속 이동, PT 정정/취소·Compensation Setting·Additional Performance·월 정산의 별도 권한을 추가하지 않는다. 발급 대상 식별을 타 지점 전체 Member 목록/전화번호·다른 Pass/PT/민감 보상 정보의 일반 조회 허용으로 확대하지 않는다. 기존 보상 설정 접근 제한과 Trainer의 담당/개별 지원 회원 조회는 그대로다.

남은 결정: 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차과 실제 발급 지점 선택/계약, 지점/Member/Trainer 활성·발급 시 활성 담당 필수/상품 최초 횟수의 나머지 상태/선택 계약, 타 지점 Member 추가 공개 정보·Member 선택용 최소 식별 응답/계약과 업무 인가 경로는 ARCH-001·MB-001/002/003/004/005·BR-001/002/010 후속이다. 승인된 Master·Branch Admin·Operator의 발급 허용과 Trainer 단독 불가를 다시 미결정으로 두지 않으며, 미정 Scope 부여/조회·상태 조건을 임의 기본값으로 구현하지 않는다. 발급/상품 조건·감사 계약/저장·Application UoW·실패/재시도/중복 및 판매 중단/지점 상태/Member 이동/인가 변경 경합은 후속 Architecture 설계·검증 대상이다.

2026-10-12 사용자 확정(발급용 타 지점 회원 검색 질문의 2번): Branch Admin·Operator는 자신의 허용된 실제 Issued Branch에서 새 PT Pass를 발급하기 위해 같은 Organization 전체 지점의 Member를 이름·전화번호 일부로 검색할 수 있다. 전화번호 전체 일치만을 요구하지 않으며 Member Home Branch가 Caller의 관리/발급 Branch와 다르다는 이유만으로 검색 후보에서 제외하지 않는다. Master의 기존 Organization 전체 범위는 유지한다. 검색은 기존 Member를 선택하여 실제 발급 지점의 새 Pass를 만드는 흐름이며 Member 소속 이동/복제나 기존 Pass·PT·지급·정산 변경을 수행하지 않는다(BR-OPS-010, PD-004/007/022, PR-002/003/030).

검색 인가/정보 공개 경계: 이 허용은 이용권 발급용 Member 검색의 후보 범위·검색 방식과 이름/전체 전화번호/현재 Member Home Branch 공개다. Backend는 매 검색/선택/발급 요청에서 현재 Caller의 발급 역할/Organization·허용 실제 Issued Branch와 대상 Member의 실제 Organization을 검증한다. 검색 Branch Context를 위조하거나 과거 검색 결과/선택 Member ID로 철회된 역할·Scope 또는 다른 Organization을 우회할 수 없다. 같은 전화번호/이름의 여러 Member는 별도 식별자로 구분하여 선택하며 번호만으로 병합하거나 첫 결과를 자동 선택하지 않는다. 이 세 항목의 읽기 허용이 회원 정보/전화번호 수정·일반 Member 상세·전체 무조건 목록/일괄 내보내기, 다른 개인정보/Pass/PT/보상 정보 열람 권한을 추가하지 않는다. Trainer 단독의 담당/개별 지원 Member 검색 및 기존 전체 전화번호 공개는 유지하고 발급 역할 겸임은 그 독립 발급 업무 Scope로 판단한다. 응답은 승인된 공개 범위 안에서 구성하며 Member 선택용 최소 식별 응답/계약과 추가 공개 정보는 후속이다. 실제 운영 연락처/검색어를 문서·일반 로그에 복사하지 않는다.

이번 결정으로 발급용 검색 후보의 Organization 전체 지점 범위·이름/전화번호 일부 검색과 결과의 이름/전체 전화번호/현재 Member Home Branch 공개는 해결됐다. 추가 공개 정보·Member 선택용 최소 식별 응답/계약 및 나머지 검색/대상 조건, 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·실제 발급 지점 선택, 발급 시 활성 담당 필수/상품 최초 횟수의 나머지 상태·계약/저장/UoW·실패/재시도/중복·권한/소속/상품/지점 상태 변경 경합은 후속이다. 승인된 세 항목의 공개/전화번호 비마스킹을 다시 미결정으로 두지 않는다. Product OPEN/ADR·모듈/계약 상태와 기존 보상 설정 접근 제한을 유지하며 실제 검색/발급 구현·검증 완료를 뜻하지 않는다.

2026-10-12 사용자 확정(발급용 검색 결과 표시 정보 질문의 1번): 새 PT Pass 발급용 Member 검색 결과에는 이름·전체 전화번호·소속 지점을 표시한다. 소속 지점은 해당 Member의 현재 Home Branch이며 Caller 관리 지점/Pass Issued Branch/수업 Performed Branch와 구별한다. 같은 Organization의 타 지점 회원 검색 결과에도 동일하게 적용하고 부분 마스킹된 번호만 표시하도록 제한하지 않는다. 기존 이름·전화번호 일부의 Organization 전체 지점 검색과 현재 발급 역할/실제 Issued Branch Scope 인가는 유지한다(BR-OPS-010, PD-004/007/022, PR-002/003/030, NFR-001/005).

공개 범위 게이트 갱신: 검색 결과의 이름·전체 전화번호·현재 Member Home Branch 표시는 해결됐다. 검색/선택/발급마다 기존 현재 Caller/역할·실제 Issued Branch/Organization을 검증하며 다른 개인정보/일반 회원 상세·다른 Pass/PT·보상/내보내기·수정 권한을 추가하지 않는다. 공유 번호/동명이인의 Member 구분·선택과 기존 Trainer 조회 제한을 유지한다. 추가 공개 정보·최소 선택 응답/계약과 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·나머지 검색/대상/발급 조건/일관성은 후속이며 이 OPEN 전체를 CLOSED로 바꾸지 않는다(BR-OPS-010).

2026-10-12 사용자 확정(Operator 업무 허용 지점 수 질문의 1번): v1 Operator 역할의 업무 허용 Branch는 한 시점에 하나만 지정한다. Operator는 그 지정된 단일 Branch에서 명시적으로 허용된 업무를 수행하며 같은 계정의 Operator 권한을 여러 Branch에 동시 부여하지 않는다. Branch당 Operator 한 명이라는 1:1 인원 제한을 추가하지 않으며 하나의 Branch에 여러 Operator가 있을 수 있다. 이 결정은 Operator 역할의 업무 Scope이며 기존에 허용된 겸임 역할의 독립적인 관리/PT 권한이나 Trainer Home Branch를 바꾸지 않는다(BR-OPS-011, PD-001/007, PR-001/003/030, ARCH-001, MB-004).

이번 결정은 Operator 동시 허용 Branch를 하나로 확정한 것이다. 새 Operator 발급/최초 지점 지정 Actor는 Master Organization 전체/Branch Admin 자기 단일 Branch로 후속 승인됐다. 발급 절차·기존 계정 역할 부여/변경·지점 변경의 대상/절차·나머지 행위 권한은 계속 OPEN이다. Operator 지점 변경 Actor는 Master 전용으로 후속 승인됐으며 기존 저장 후 현재 Scope 반영/실패 보존·감사 원칙을 적용한다. 발급용 이름/전화번호 일부의 같은 Organization 전체 지점 Member 검색과 이름·전체 전화번호·현재 Member Home Branch 공개는 유지하고 다른 Branch 발급/일반 조회 권한을 추가하지 않는다. 기존 겸임의 독립 Scope와 민감 보상 제한·IAM S1 후속 범위를 유지한다(BR-OPS-010/011).

2026-10-12 사용자 확정(Operator 계정 발급과 최초 지점 지정 권한 질문의 1번): Master Admin은 자신의 Organization 범위에서, Branch Admin은 자신의 단일 관리 Branch 범위에서 새 Operator 계정을 발급하고 그 한 지점을 최초 업무 Branch로 지정할 수 있다. Branch Admin의 타 지점 Operator 발급은 허용하지 않는다. Backend는 처리 시점의 검증된 현재 Caller 역할/Organization·관리 Branch와 대상 Branch의 실제 Organization 관계를 확인하며 직접 ID·위조 role/branch_id·과거 권한으로 범위를 우회할 수 없다. Operator 단독·Trainer 단독의 로그인 계정 발급은 허용하지 않는다(BR-OPS-011, PD-019, PR-021/030, NFR-001/004, MB-004, ARCH-001/002).

이번에 해결된 것은 새 Operator 계정 발급/최초 지점 지정 Actor와 허용 Scope다. Operator 지정 Branch 변경은 Master 전용으로 후속 승인됐다. 기존 계정 역할 추가/변경·Operator 변경 대상/절차·계정 수명 업무 및 Operator·Trainer 신규 발급 외 계정 업무 위임은 계속 OPEN이다. 신규 Trainer 발급 Actor/Scope는 BR-OPS-012의 후속 승인을 적용한다. 발급 관리자의 일회용 최초 비밀번호 설정 링크 전달은 기존 승인 방식을 재사용하며 상세 전달/수명은 ARCH-002다. IAM-001 S1의 기존 최소 관리자 흐름/ADR-0004 v1 인증 방식 ACCEPTED를 변경하지 않는다.

2026-10-12 사용자 확정(기존 Operator의 근무 지점 이동 권한 질문의 1번): 기존 Operator의 단일 업무 허용 Branch 변경은 Master Admin만 자신의 Organization 범위에서 수행할 수 있다. Branch Admin은 변경 전/후 지점 관리자이거나 해당 계정의 최초 발급자여도 변경할 수 없다. Operator·Trainer 단독도 불가하며 겸임자는 현재 Master 권한이 있을 때만 그 관리 Scope로 처리한다(BR-OPS-011, PD-019, PR-021/030, NFR-001/004, MB-004, ARCH-001).

Operator 지점 변경의 Actor는 해결됐으며 일반 저장 후 현재 Scope 반영/실패 보존·감사 원칙을 재사용한다. 대상 Branch/계정 상태·세부 절차·기존 계정의 다른 역할/Scope 변경·계정 수명 권한은 미정이고 실제 저장/Caller/인가/UoW·처리 중 요청/동시성은 후속이다. 신규 Operator 발급 Actor·단일 Branch 수 및 기존 발급용 검색 범위/필드는 재질문하지 않는다. 이 OPEN 전체를 CLOSED로 바꾸거나 IAM-001 S1/ADR-0004를 승인한 것은 아니다.

2026-10-12 사용자 확정(신규 Trainer 로그인 계정 발급 권한 질문의 1번): Master Admin은 자신의 Organization 전체 Trainer, Branch Admin은 발급 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 단일 관리 Branch인 경우 신규 Trainer 로그인 계정을 발급할 수 있다. Branch Admin은 타 지점 소속 Trainer 계정을 발급할 수 없다. 타 지점 지원 수업·담당 회원/Pass·Performed Branch·Operator 업무 Branch·최초 발급자/과거 소속 사실만으로 이 권한이 생기지 않는다. Operator·Trainer 단독은 본인 포함 로그인 계정 발급 불가이며 관리자 겸임은 현재 관리자 역할의 독립 Scope로 판단한다(BR-OPS-012, PD-019, PR-021/029/030, NFR-001/004, MB-004, ARCH-001/002).

Trainer 신규 발급 Actor/Scope는 해결됐고 기존 일회용 최초 비밀번호 설정 링크/감사·일관성 원칙을 재사용한다. 기존 계정의 Trainer 역할 추가/재연결·관리자 승격/Master 전용 Trainer 이동의 미정 대상/절차·중단/복구·재설정 등 수명 업무 권한과 대상 상태/중복·선택/연결/전달 세부 절차는 기존 게이트다. IAM/Workforce/Organization/Audit 계약·저장/UoW·실패/재시도/동시성은 후속이며 IAM-001 S1/ADR-0004 v1 인증 방식 ACCEPTED는 유지한다. 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

Trainer Home Branch 일반 변경의 Actor는 Master Organization 범위 전용으로 후속 승인됐다(2026-10-12, BR-OPS-013). 기존 저장 후 현재 소속 인가/실패 보존·감사 원칙을 적용하며 계정 역할/관리·Operator Scope·담당/지원 관계와 기존 수업 당시 소속/지급·정산/비용 귀속 규칙은 유지한다. 이동 대상 상태/절차·과거 소속 이력 정정/소급/확인 불가 및 상세 계약·동시성은 후속이며 이 OPEN 전체를 해결한 것은 아니다.

2026-10-12 일괄 승인 반영: A8/A9: 계정 전체 차단/복구·관리자 비밀번호 재설정은 같은 Organization Master 전용이며 Branch Admin에 Operator/Trainer 전용 계정의 해당 권한을 위임하지 않는다. 여러 Master 허용/마지막 사용 가능 Master 차단·권한 제거 금지는 확정이다. 기존 Operator/Trainer 새 계정 발급의 지점 관리자 Scope는 유지하고 기존 계정의 역할 부여/변경·Master 추가 발급 세부·Branch 기본 정보 수정과 나머지 절차/인가 계약은 후속이다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch). 이 복합 OPEN의 다른 미결정 항목은 유지한다.

2026-10-12 C 일괄 승인 반영: C1/C4/C5/C6/C7: 추가 비밀번호 재확인 없음, Master reset 확정 즉시 자격/로그인 철회와 마지막 Master 일반 reset 차단, Master Login ID 변경/인증·계정 관리 감사 열람이 해결됐다. 기존 지점 관리자 신규 Operator/Trainer 발급 권한은 유지하고 ID 재사용/역할 전이·계약/경합은 후속이다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 E 일괄 승인 반영: E5: 기존 계정의 Operator·Trainer 역할 추가/회수는 Master Organization 또는 Branch Admin 자신의 관리 범위에서 허용한다. Operator 단일 Branch/Trainer 현재 Home Branch의 대상 역할 Scope와 동일 Organization을 검증하고 독립 관리자/타범위 역할·기존 연결/이력을 보존한다. 회수/재부여로 Master 전용 Operator 지점 이동·Trainer 소속/연결 변경/계정 reset 등을 우회하지 않는다. E1/E2/E3/E4/E6의 설치/전달/ID/일반 복구 정책도 해결됐으며 나머지 역할/상태·재부여/계약은 후속이다. [2026-10-12 E 일괄 승인](product-decisions.md#review-20261012-e-batch)

2026-10-12 G 일괄 승인 반영: G1/G5: 비활성 지점에 관련된 유효 계정/역할의 기존 로그인/조회는 허용하고 Master는 Operator 업무 Branch를 활성 지점으로 변경할 수 있다. 독립 역할/Scope·현재 인가/철회 정책을 유지하며 Branch Admin 관리 Branch 변경 권한은 추가하지 않는다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). 다른 상태/신규 배정·역사 사실/구체 계약·경합 등 나머지 게이트로 이 복합 OPEN은 유지한다.

2026-10-12 K 일괄 승인 반영: K3 첫 기능 범위/개발 순서는 승인됐으나 구체 IAM/Organization/Audit 소유권·공유 UoW/잠금/API·상태 enum/인가·준비/인수 상세는 PROPOSED다. K2 Trainer 기본정보 권한은 기존 계정 발급/역할·보상 설정 및 Master 전용 Home/ID/계정 전체 차단과 구별하며 다른 권한/상태/연결·운영 상세는 후속이다. [2026-10-12 K 일괄 승인](product-decisions.md#review-20261012-k-batch). 이 복합 OPEN의 다른 항목은 유지한다.

2026-10-13 R1/R2=1 부분 해결: Trainer 전화번호는 필수 기본정보이며 Branch Admin의 자기 지점 지점명/대표 연락처 수정과 중요 변경 감사를 허용한다. 기존 신규/현재 Home 인가·계정/보상 권한 분리·Branch 구조/상태/관리자 배정/과거 지점 사실은 유지한다. 형식/정규화·다른 필드/공개·보존/이력/계약 때문에 Status는 OPEN이다. [R 승인](product-decisions.md#review-20261013-r-batch); BR-OPS-029/030; V-116/117 미구성·미실행.

<a id="mb-005"></a>
## MB-005. Trainer Session 정정 / Cross-Branch 검증

Question / TODO: 과거 Home 오류의 분류 전환/이전 보상 유효성·역사 설정 확인·영향 건 식별/완료 증거, 역사 소속/담당/수행·지원 사실 확인 불가/충돌·상태/최소 공개 계약을 구체화한다. W1로 바뀐 일반/지원 분류는 Master Organization 전용 명시적 정정/같은 PT·기존 Pass 차감 유지·일반 최초 기록 생성 시점 실제 수행 Trainer 설정/기존 소비 Pass 조건·지원 기존 관리자 수동 추가실적으로 해결됐다. W2 영향 건 정정 완료 전 해당 Trainer·월 확정/재확정 차단과 V1 사유/원래 이력 보존·기존 확정본 자동 변경 금지를 유지한다. 기존 Member/실제 수행자/시작 오류 취소 재등록·새 생성 시점 설정 및 Master Performed 값 정정은 구별한다. P/O 지원·전체 적격 Pass/실제 당시 Home·Performed/금액 비공개·기존 권한과 필요한 월 해제/같은 월 재확정은 유지한다. 승인된 유지/취소 방식·지급 기준을 재질문하지 않는다.

Status: OPEN

Related decisions / requirements: PD-002/010; PR-008/009/029/030; BR-007. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Trainer 정정·취소 및 교차 Branch Session 상세 설계 확정 전

확정된 경계: 허용되지 않은 Cross-Branch 접근은 금지한다. Backend 검증 의무는 확정이며 허용 관계에 대한 정책과 기술 구현은 구분한다. 본인 등록 권한이 정정 권한을 자동 부여하지 않는다.

2026-10-11 사용자 확정(Trainer 본인 PT 진행 기록 정정·취소 권한 질문의 1번): Trainer 역할만으로는 본인이 등록하거나 수행한 PT 진행 기록도 정정·취소할 수 없다. 월 정산 확정 전후 모두 적용하며 직접 ID 요청으로도 우회할 수 없다. 허용된 관리 담당자가 해당 업무의 별도 권한·Branch Scope 안에서 처리한다. 관리자·Trainer 겸임자는 Trainer 역할의 본인 권한이 아니라 해당 업무의 관리 권한으로 판단한다. 이 결정으로 다른 역할의 정정 권한이나 Home/Performed Branch 기준을 자동 확정하지 않는다. Trainer의 허용된 PT 진행 등록·본인 내역 조회와 기존 보상 설정/추가실적 권한은 유지한다. 정정 항목·기간·취소 및 지급/정산 연동 상세는 BR-007/009, 관리 Scope와 교차 업무 조건은 ARCH-001/MB-005의 잔여 OPEN이다.

2026-10-11 사용자 확정(타 지점 PT 진행 기록 정정·취소 담당 지점 질문의 1번): Master Admin은 Organization 전체, Branch Admin은 대상 기록의 실제 Performed Branch가 자신의 관리 Branch인 경우 PT 진행 기록을 정정·취소한다. 수원 소속 Trainer의 강남 수업 기록은 강남 Branch Admin이 담당하며, 수원 Branch Admin에게 Trainer Home Branch만을 근거로 해당 기록의 정정 권한을 부여하지 않는다. Trainer 이동만으로 기록의 담당 지점이 바뀌지 않는다. Backend에서 수업 사실·현재 관리 권한을 검증하며 요청의 Branch ID를 그대로 신뢰하지 않는다. 추가실적 금액 입력·보상 설정·Trainer 전체 월 정산의 기존 Home Branch 권한은 유지하고 수행 지점의 기록 권한으로 확대하지 않는다. Trainer 역할의 정정·취소 금지는 유지하며 관리자 겸임자는 해당 관리 권한으로 판단한다. Operator의 정정 권한·Performed Branch 자체 오류 정정·정산 확정 후 서로 다른 지점 담당자의 처리 순서·취소에 따른 지급/추가실적 연동은 잔여 OPEN이다.

2026-10-11 사용자 확정: 정산 확정 후 타 지점 수업 취소의 담당 순서는 현재 Home Branch 관리자의 해당 월 해제 → 실제 Performed Branch 관리자의 기록 취소 → 현재 Home Branch 관리자의 같은 월 재확정이다. Master 전체 처리 가능, 기존 지점별 기록/금액/전체 정산 권한 유지. 처리 순서는 BR-007/PD-010에서 해결됐으며 Operator 권한·Performed Branch 자체 오류 정정·나머지 교차 대상 조건은 OPEN이다.

2026-10-11 사용자 확정(Operator의 PT 진행 기록 정정·취소 권한 질문의 1번): Operator 역할만으로는 PT 진행 기록을 정정·취소할 수 없다. 정산 미확정/확정 상태 모두 적용한다. Master Admin은 Organization 전체, Branch Admin은 해당 기록의 실제 Performed Branch 범위에서 담당한다. Trainer 역할의 정정·취소 금지와 관리자 겸임자의 해당 관리 권한 판단은 유지한다. Operator의 기존 허용 업무가 정정 권한을 부여하지 않으며 Branch Scope 부여·다른 운영 업무의 상세는 MB-004/ARCH-001 OPEN이다.

2026-10-11 사용자 확정(수업 지점 자체 오류 정정 담당자 질문의 1번): PT 진행 기록의 Performed Branch 오류 정정은 Master Admin만 담당한다. Branch Admin은 기존 기록의 지점이나 실제 수행 지점이 자신의 관리 Branch여도 해당 지점 값을 정정할 수 없다. 일반 정정/취소의 수행 지점 기준과 Operator/Trainer 역할의 금지는 유지한다. Master의 Organization 범위와 원본/변경 이력 보존 원칙을 따른다. 소속·발급 지점 변경으로 과거 수행 지점을 자동 변경하지 않는 기존 규칙도 유지한다. 이번 결정은 담당 권한에 한정하며 정정 방식·확정 월 연계·일반/지원 수업 구분에 따른 보상 전환·적용 설정 시점은 BR-007/009/013 및 MB-005의 잔여 OPEN이다.

2026-10-11 사용자 확정(수행 지점 오류 정정 방법 질문의 1번): 기존 기록/Pass 차감 유지·지점과 보상 방식 정정·변경 전후 이력 보존·중복 지급 없음. 취소/재등록·복원/재차감하지 않는다. 기존 수동 지원 보상과 미입력 확정 차단 정책을 적용한다. 확정 월은 기존 해제 → 정정 → 같은 월 재확정과 이전 확정본 보존을 동일 적용한다(사용자 일관성 지시). 지원→일반의 지급 설정 기준 시점·나머지 정정 조건/계약·실패/동시성은 잔여 대상이다(BR-OPS-001, PD-010, PR-009).

2026-10-11 사용자 확정: 지원→일반 정정의 Rate/Fixed Amount는 기존 PT 기록 최초 생성 시점 기준이다(BR-PAY-011). 최초에 일반 지급을 계산하지 않았어도 당시 설정 근거를 사용하며 현재 값으로 임의 대체하지 않는다. 이 시점 질문은 해결됐으며 나머지 업무 접근/정정 조건은 OPEN, 설정 근거 확인/저장·계약/동시성은 Architecture 후속이다.

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

2026-10-12 사용자 확정(담당 교체 전 수업의 누락 등록 질문의 1번): A가 담당으로 실제 수업을 진행한 뒤 담당이 B로 바뀌어도 A는 교체 전 본인 수업을 직접 늦게 등록할 수 있다. 예: 9월 5일 A 수업 → 9월 6일 B로 담당 교체 → 9월 7일 A 누락 등록. 실제 수업 당시 A의 담당 관계와 본인 수행 사실, 현재 검증된 Caller/Trainer 연결·Organization 및 기존 Pass/정산 조건을 확인한다. 현재 담당이 B라는 이유만으로 관리자 대행이나 A 재배정을 요구하지 않는다. 이 허용만으로 A의 해당 회원 목록/상세·전화번호/다른 Pass·다른 Trainer 기록 조회 권한을 복원하지 않는다(BR-OPS-003/005/008, PD-008, PR-008/029/030).

이번 결정은 교체 전 실제 본인 수업의 이전 담당 직접 등록 허용을 해결한 것이다. BR-OPS-003의 기존 미확정 월/Pass 조건·실제 수행 A 기준 지급과 회원 조회 비복원 경계를 유지한다. 과거 담당/수행 사실 확인 불가/정정·동일 시점 순서·다른 관계의 나머지 인가, 최소 식별/응답 및 계약/저장/UoW·교체/등록/월 확정 경합은 계속 OPEN이다.

Trainer Home Branch 일반 변경의 Actor는 Master Organization 범위 전용으로 후속 승인됐다(2026-10-12, BR-OPS-013). 기존 저장 후 현재 소속 인가/실패 보존·감사 원칙을 적용하며 계정 역할/관리·Operator Scope·담당/지원 관계와 기존 수업 당시 소속/지급·정산/비용 귀속 규칙은 유지한다. 이동 대상 상태/절차·과거 소속 이력 정정/소급/확인 불가 및 상세 계약·동시성은 후속이며 이 OPEN 전체를 해결한 것은 아니다.

2026-10-12 사용자 확정(잔여가 남은 담당 이용권이 있는 Trainer의 비활성화 질문의 1번): 잔여가 남은 담당 PT Pass가 있어도 Trainer 비활성화를 허용하며 기존 Assigned Trainer 정보는 유지한다. 비활성화 전에 모든 Pass를 다른 Trainer에게 교체하도록 요구하지 않고 자동 담당 해제/재배정도 하지 않는다. 이후 필요할 때 권한 있는 관리자가 BR-OPS-008의 기존 조건/Scope로 담당을 교체한다(BR-OPS-014, PD-007/011, PR-003/005, NFR-001/004, ARCH-001/002, MB-001/003/005, BR-001).

기존 담당 정보 유지와 별도 담당 교체가 해결됐으며 비활성 Trainer의 접근은 계속 차단한다. Member 현재 Home Branch 기반 담당 교체와 Trainer Home Branch 기반 비활성화 권한을 구분하고 잔여/발급 조건·과거 PT/보상을 유지한다. 다른 상태별 교체/사용 조건·개별 지원/재활성화·비활성 상태의 과거 PT 예외 및 구체 저장/현재 인가·UoW/동시성은 후속이다. 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 사용자 확정(담당 Trainer를 새로 지정할 때의 조건 질문의 1번): PT Pass의 담당 Trainer를 새로 지정할 때는 실제 활성 Trainer만 허용한다. 기존 Pass의 담당 교체 및 허용된 새 Pass 발급 흐름에서 담당을 최초 지정하는 경우 모두 적용하며 비활성 Trainer를 미리 배정하지 않는다(BR-OPS-008/014, PD-007, PR-003/005/029/030, NFR-001, ARCH-001, MB-001/003/005, BR-001).

새 지정 대상의 활성 필요조건은 해결됐으며 같은 Organization의 타 지점 허용/기존 행위별 Actor·Scope, 이후 비활성화된 기존 담당 정보 유지·접근 차단을 적용한다. 최초 담당 필수는 해결됐고 나머지 Pass/계정/Branch 상태 조합·최소 선택 정보, 재활성화·개별 지원/비활성 전 수업 예외 및 실제 현재 사실 검증/저장/UoW·지정·비활성화 경합은 후속이다. 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 사용자 확정(비활성화 전 진행했지만 누락된 PT 수업 등록 질문의 1번): Trainer 비활성화 전에 실제로 수행한 미등록 PT 수업은 관리자가 대행 등록하는 경로를 허용한다. 대상 Trainer의 비활성 상태를 유지하며 잠시 재활성화/본인 로그인·담당 재배정을 선행 요구하지 않는다. 실제 수행 Trainer·실제 수업일과 기존 Pass 잔여/정산 조건을 그대로 적용한다(BR-OPS-015, PD-008/011, PR-008/029/030, BR-OPS-003/008/014, BR-PAY-006/011/012).

관리자 대행 경로와 Master Organization/Branch Admin 실제 Performed Branch Scope는 해결됐다. 현재 인가 검증·비활성화 전 실제 수업/담당/소속 사실·시점/확인 불가·최소 선택 정보/사유·증빙과 구체 계약/저장/UoW·경합은 후속이다. 비활성/현재 담당 유지·실제 수행자/수업일·기존 Pass/생성 시점 보상/진행 월 정산·민감 설정 접근 제한을 적용한다. 비활성 Trainer 본인 직접 등록/회원 조회 예외가 아니며 이 OPEN 전체를 CLOSED로 바꾸지 않는다.

2026-10-12 일괄 승인 반영: B3/B6/B7: 새 Pass 활성 담당 필수, 비활성 Branch 새 실제 수업 차단/원본 보존, PT 업무 날짜와 월 경계 한국 시간 공통은 확정이다. 과거 누락/정정의 비활성 지점 조합·기존 Pass 사용의 다른 상태·역사 사실/일자 정밀도·최소 계약/경합은 남는다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch). 이 복합 OPEN의 다른 미결정 항목은 유지한다.

2026-10-12 C 일괄 승인 반영: C9/C10: 실제 수업 시작 날짜/시각, Member/실제 수행 Trainer 오류의 취소 후 재등록을 적용한다. PT 행위 Scope와 별도 보상/정산 권한·수행 지점 값의 Master 전용 정정·지원 보상 별도 입력/과거 보존을 유지한다. 역사 사실/시각 확인 불가·다른 Trainer/월 영향·최소 계약/경합은 후속이다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 G 일괄 승인 반영: G2/G4: 비활성화 전 실제 수업의 기존 권한별 처리와 Home Branch가 비활성인 활성 Trainer의 타 활성 지점 허용 수업은 가능하다. 정정/취소의 실제 Performed Branch·정산 현재 Home 인가/확정본 보존·과거 소속 기준 일반/지원 구분을 유지한다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). 다른 상태/신규 배정·역사 사실/구체 계약·경합 등 나머지 게이트로 이 복합 OPEN은 유지한다.

2026-10-12 K 일괄 승인 반영: K1 날짜/시각 오류는 원본 취소 후 재등록/연결이며 새 일반 지급은 재등록 생성 시점 설정을 사용한다. 기존 실제 Performed Branch PT 관리 Scope·그 값 정정 Master 전용, 각 확정 Trainer/월 현재 Home 인가와 해제/처리/재확정/이전본 보존을 유지한다. 올바른 실제 소속/상태·Pass/관계 사실·정정 연결/실패 계약은 후속이다. [2026-10-12 K 일괄 승인](product-decisions.md#review-20261012-k-batch). 이 복합 OPEN의 다른 항목은 유지한다.

2026-10-13 N1/N2=1: 비관리자 Trainer 본인 PT 내역의 수업별 금액과 현재 다른 Home Branch Trainer의 자기 지점 수업 금액은 Performed Branch Admin에게 공개하지 않는다. 일반 지급/수업 연결 지원 보상 모두 적용하고 기존 PT 기록 조회/정정과 금액 열람을 분리한다. 현재 Home 기반 기존 관리자 보상·정산 업무·Master Organization/겸임 독립 Scope, CompSetting/월 정산/지점 비용 보고 제한을 유지한다. 등록/중첩/직접 ID·제공되는 집계/감사/오류 등 Backend 우회 노출을 막고 비공개를 가짜 0원/원본 삭제/재계산으로 표현하지 않는다. 다른 공개 필드/상태·계산 근거/최소 응답/인가·현재 권한/소속 변경 경합은 후속으로 이 복합 OPEN은 유지한다. BR-PAY-021, PR-008/029/030, NFR-001/005; V-108/109 예정; [N 승인](product-decisions.md#review-20261013-n-batch).

2026-10-13 O1/O2=1 부분 해결: 담당/개별 지원 회원의 본인 실제 수업 등록은 다른 Trainer 담당분을 포함한 전체 적격 Pass의 FIXED_AMOUNT 우선/FIFO 차감이다. 개별 지원은 본인 담당 Pass 없이도 조회/본인 등록을 허용한다. 담당자·Home/Issued/Performed·실제 수행자 보상/금액 비공개 및 기존 상태/잔여·정산 검증은 유지한다. 지원 관계의 지정 전/해제 후 과거 등록 시간 경계·역사 사실과 나머지 공개/계약 때문에 Status는 OPEN이다. [O 승인](product-decisions.md#review-20261013-o-batch); BR-OPS-026; V-110/111 미구성·미실행.

2026-10-13 P1/P2=1 부분 해결: 현재 유효한 지원 허용으로 지정 전 실제 본인 수업 등록을 허용하며, 해제 후에는 허용 기간에 실제 진행한 본인 수업만 늦게 등록한다. 일반 Member/전화번호 조회 비복원·지정 이력 비소급, 현재 계정/Trainer/실제 수행·과거 허용 사실 및 기존 Pass/정산 조건을 유지한다. 시간 정책은 확정됐고 역사 사실 확인 불가/충돌·나머지 상태/공개·최소 계약 때문에 Status는 OPEN이다. [P 승인](product-decisions.md#review-20261013-p-batch); BR-OPS-027; V-112/113 미구성·미실행.

2026-10-13 V1=1 부분 해결: Trainer/Member의 이미 기록된 과거 Home 이력 오류는 Master 자기 Organization 전용/사유 필수·원래 이력/감사 보존으로 정정한다. 일반 이동의 즉시 적용/미래 예약 미지원은 유지하고 기존 PT/지급·정산 확정본을 자동 덮어쓰지 않는다. 영향 건은 기존 업무별 권한/정정·필요한 월 확정 해제/동일 월 재확정·이전본 보존을 따른다. 구체 역사 사실/현재 Home 영향·분류가 바뀌는 수업 정정/지급 기준·비용 보고/최소 계약은 남아 Status는 OPEN이다. [V 승인](product-decisions.md#review-20261013-v-batch); BR-OPS-032; V-123 미구성·미실행.

2026-10-13 W1/W2=1 부분 해결: 과거 Trainer Home 오류에 따른 일반/지원 전환은 Master Organization 전용 명시적 정정으로 같은 PT/기존 Pass 차감·최초 생성 시각을 유지한다. 일반은 최초 기록 생성 시점 설정/소비 Pass 발급 조건, 지원은 기존 관리자 범위 수동 추가실적이다. 이전 결과 이력/유효 합계 단일 반영을 보존하고 영향 건 분류/보상·비용 정정 완료 전 해당 Trainer·월 확정/재확정을 차단한다. 소속 정정만으로 기존 확정본 자동 해제/변경 없음·기존 권한/사유·필요한 월 해제/명시적 정정/동일 월 재확정·이전본 보존을 유지한다. 역사 사실·영향/완료 증거·나머지 상태/최소 계약/경합이 남아 OPEN을 유지한다. [W 승인](product-decisions.md#review-20261013-w-batch); BR-OPS-033/PAY-024; V-124/125 미구성·미실행.

<a id="mb-006"></a>
## MB-006. Branch Settlement 금액 노출

Question / TODO: 관리자 월 정산의 추가 계산 근거·버전별 최소 응답/필드와 Master 전용 지점 비용 보고의 최소 Trainer 식별/응답·월 대상 사실/선정 검증/미완료 식별·역사 비용/버전·동시 조회 계약을 구체화한다. Z1로 지점별 합계/기본급·일반 PT·지원 수업·기타 추가실적 구분/Trainer별 해당 지점 기여 금액 조회가 해결됐다. Y1/Y2 종료 월/미완료 영향 없는 최신 유효 확정본 합산·미확정/해제 중/소속 오류 정정 대기 제외·표시를 상세에도 적용한다. 보고 필터는 확정본 자동 변경 명령이 아니며 당월 Trainer 정산 조회·S1/S2 과거 정산/보상 이력 공개·현재 Home 전체 정산·H4/N1/N2/C7 기밀성과 현재 인가/원래 금액·버전 보존을 유지한다. AB1/AB2 정산 구성 기반 대상 자동 선정/월전체 비활성·명시기본급0·무활동·미완료없음의 새 확정 의무 제외는 해결됐다. 기존 이력/미완료/비활성 기본급 자동0 금지는 유지한다. 승인된 보고 상세 수준/기간/집계·공개 범위를 반복 질문하지 않는다.

Status: OPEN

Related decisions / requirements: PD-012; PR-010/030; BR-PAY-010. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Settlement·Session·감사 정보의 지급 관련 열람 상세 설계 확정 전

확정된 경계: Rate / Fixed Amount / Base Salary 세 항목의 조회·설정·변경은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 단일 Branch를 Home Branch로 가진 Trainer에게만 허용한다. 관리자와 Trainer를 겸하는 계정은 관리 권한 범위 안이면 본인의 세 항목도 조회·변경할 수 있다. Master Admin은 본인 포함 허용하며, Branch Admin은 본인 Trainer의 Home Branch가 관리 Branch일 때 본인도 허용한다. 관리자 권한이 없는 Operator·Trainer 계정은 본인 포함 모든 Trainer 설정 조회·변경이 불가하다. 타 지점 지원 수업은 보상 설정 접근 권한을 부여하지 않는다. Backend에서 대상 Trainer의 Home Branch를 검증하며 직접 ID 요청과 감사·정산 등 우회 경로에도 제한을 적용한다. 보상 설정 권한과 정산 결과 공개 범위는 별개다. 지점 귀속은 MB-010과 함께 결정한다.

2026-10-11 후속 결정과의 경계: 최초 월 정산 확정은 Master의 Organization 전체/Branch Admin의 처리 시점 Trainer 현재 Home Branch 기준으로 본인 건 포함·별도 Master 승인 없이 허용한다(BR-009, BR-PAY-016). 이 역할·관리 범위 결정으로 공개할 대상 월·금액·계산 근거·전체 과거 내역이나 지점 비용 귀속까지 확정하지 않는다. MB-006은 OPEN이다.

2026-10-11 사용자 확정(지점장이 조회할 정산 내역의 범위 질문의 1번 답변): Branch Admin은 조회 시점에 자신의 관리 Branch를 Home Branch로 가진 Trainer의 해당 월 정산 전체 금액과 구성 내역을 조회할 수 있다. 해당 월 적용 기본급·일반 Session Payment·타 지점 지원 수업을 포함한 Additional Performance·월 정산 총액을 모두 공개하며, 수업의 Performed Branch가 다른 지점이라는 이유로 해당 금액을 제외하거나 숨기지 않는다. 관리 범위 안의 본인 Trainer도 같은 기준을 적용하고 Master Admin의 Organization 전체 조회 권한은 유지한다. 반대로 다른 Home Branch Trainer는 자기 지점에서 지원 수업을 했다는 사실만으로 전체 월 정산 조회 대상이 되지 않는다. Backend는 직접 ID·목록/검색·집계 등 각 조회 경로에서 현재 관리 Scope와 대상 Trainer의 현재 Home Branch를 검증한다. 이는 정산 구성 금액·내역의 공개에 관한 결정이며, 다른 지점의 전체 회원/Trainer 자료나 원본 업무 데이터·감사 이력의 포괄적 열람을 허용하지 않는다. 조회할 대상 월·이전 확정본/세부 계산 근거·감사 정보의 남은 공개 상세 및 Operator·관리자 권한 없는 Trainer의 정산 조회 권한은 관련 OPEN을 유지한다. 지점별 정산/비용 귀속(MB-010), 과거 확정 금액 보존, 지원 수업 보상의 일반 지급과의 중복 합산 금지 및 기존 확정/정정 권한·조건은 변경하지 않는다. 위 대상 Trainer·해당 월 정산의 공개 금액·구성 내역을 다시 미정으로 취급하지 않으며 잔여 질문으로 MB-006은 OPEN을 유지한다.

2026-10-11 사용자 확정(지점별 비용 보고서 조회 권한 질문의 1번 답변): v1 지점별 비용 보고서는 Master Admin만 Organization 범위에서 조회한다(2026-10-11 사용자 확정). Branch Admin은 자기 지점 비용 합계도 이 보고서로 조회할 수 없으며 Master 권한 없는 Operator·Trainer도 불가하다. Branch Admin의 현재 자기 Home Branch 소속 Trainer 해당 월 정산 전체 금액·구성 내역 조회는 타 지점 지원 보상까지 포함하여 유지한다. 비용 귀속·지급액·기존 등록/정정/확정 권한은 유지하며 보고서 항목·대상 월·집계/완전성·버전 등 남은 상세는 MB-006/010 OPEN이다. 보고서 인가를 다른 정산 조회 권한과 혼동하지 않으며 MB-006 전체는 잔여 질문으로 OPEN을 유지한다.

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

2026-10-12 H 일괄 승인 반영: H4=1: 관리자 권한 없는 Trainer 본인 월 정산 총액/구성의 시스템 조회는 v1 제외/관리자 안내다. 본인 PT 진행 내역 및 기존 관리자 겸임 Scope의 본인 포함 정산 조회는 유지한다. 화면 숨김만으로 충족하지 않으며 직접 ID/API/집계로 우회할 수 없다. 별도 안내 자동화/명세 기능은 추가하지 않는다. 나머지 관리자용 공개 상세는 후속이다. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch). 이 복합 OPEN의 남은 항목은 유지한다.

2026-10-13 N1/N2=1: 비관리자 Trainer 본인 PT 내역의 수업별 금액과 현재 다른 Home Branch Trainer의 자기 지점 수업 금액은 Performed Branch Admin에게 공개하지 않는다. 일반 지급/수업 연결 지원 보상 모두 적용하고 기존 PT 기록 조회/정정과 금액 열람을 분리한다. 현재 Home 기반 기존 관리자 보상·정산 업무·Master Organization/겸임 독립 Scope, CompSetting/월 정산/지점 비용 보고 제한을 유지한다. 등록/중첩/직접 ID·제공되는 집계/감사/오류 등 Backend 우회 노출을 막고 비공개를 가짜 0원/원본 삭제/재계산으로 표현하지 않는다. 다른 공개 필드/상태·계산 근거/최소 응답/인가·현재 권한/소속 변경 경합은 후속으로 이 복합 OPEN은 유지한다. BR-PAY-021, PR-008/029/030, NFR-001/005; V-108/109 예정; [N 승인](product-decisions.md#review-20261013-n-batch).

2026-10-13 S1/S2=1 부분 해결: 이전 정산 확정본·해제/재확정 이력과 Rate/Fixed Amount/Base Salary 변경 이력은 Master 자기 Organization/조회 시점 현재 Trainer Home Branch Admin이 확인한다. 이전 소속 이력도 현재 관리자가 조회하며 과거 Home/Performed만으로 권한을 유지하지 않는다. 원래 금액/버전·감사 사실/당시 Context를 보존한다. 비관리자 금액 기밀성·겸임 독립 Scope·인증/계정 관리 감사 Master 전용은 유지한다. 추가 공개 필드/최소 계약·다른 업무 감사/정산 조건·저장/보존 때문에 Status는 OPEN이다. [S 승인](product-decisions.md#review-20261013-s-batch); BR-PAY-023; V-118/119 미구성·미실행.

2026-10-13 Y1/Y2=1 부분 해결: Master 전용 지점 비용 보고서는 한국 시간 기준 종료된 월만 조회하고 각 Trainer·월의 미완료 영향 없는 현재 유효 최신 확정본만 합산한다. 미확정/확정 해제 중/과거 Home 오류 영향 정정 대기 Trainer월은 합계 제외/미완료 현황 표시하며 전체 월 비용 완성이나 0원으로 취급하지 않는다. 기존 당월 Trainer 월 정산 조회/비용 귀속·과거 확정본 보존/자동 변경 금지·권한/사유·해제/정정/재확정은 유지한다. 상세 보고 항목/월 대상 집합·미완료 식별/역사 사실·비용 버전/최소 계약·동시 조회 때문에 OPEN을 유지한다. [Y 승인](product-decisions.md#review-20261013-y-batch); BR-PAY-025; V-127/128 미구성·미실행.

2026-10-13 Z1=1 부분 해결: Master 자기 Organization 전용 지점 비용 보고서의 지점별 합계/기본급·일반 PT 수당·지원 수업 보상·기타 추가실적 소계와 해당 지점 비용에 기여한 Trainer별 항목/금액 상세를 제공한다. 기존 귀속/한 번 합산과 Y1/Y2 종료 월/미완료 영향 없는 최신 유효 확정본·미완료 제외/표시를 상세/집계에 함께 적용한다. Trainer 월 전체 지급액을 각 지점에 복제하지 않고 현재 설정/소속으로 과거 비용을 다시 계산하지 않는다. 최소 식별/응답·월 대상/미완료·역사 비용/버전·동시 조회 계약이 남아 OPEN을 유지한다. [Z 승인](product-decisions.md#review-20261013-z-batch); BR-PAY-025; V-129 미구성·미실행.

2026-10-13 AB1/AB2=1 부분 해결: 설정/유효 수업·지원 보상대기/추가실적 기반 월 대상 자동 선정과 확인된 월전체 Trainer 비활성·명시 기본급0·무활동·미완료없음의 새 확정 의무 제외를 적용한다. 기존 이력/미완료·현재 Home 인가/확정·비용 보고 조건을 유지하고 현재상태/기존정산행만으로 누락·자동0/자동확정을 하지 않는다. 대상/역사 사실·조건 증거·최소 계약/경합이 남아 OPEN이다. [AB 승인](product-decisions.md#review-20261013-ab-batch); BR-PAY-026; V-132/133 미구성·미실행.

<a id="mb-007"></a>
## MB-007. PT Product의 Organization / Branch 범위 — 해결됨

Question / TODO: Organization 공통 Product를 Branch Admin도 생성/수정할 수 있는가?

Status: CLOSED

Related decisions / requirements: PD-004/009; PR-006/020/030. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: 2026-10-12 사용자 결정으로 공통 상품 생성/수정 권한 해결. 구체 권한 계약/저장/검증은 후속 Architecture 대상

확정된 경계: Organization 공통 Catalog와 지점별 가격 정책 추가 없음은 유지한다. 2026-10-12 사용자 확정으로 상품 생성/수정은 Master Admin만 Organization 범위에서 허용한다. Master 권한 없는 Branch Admin·Operator·Trainer는 불가하며 Backend는 현재 Master 권한/Organization Scope를 검증한다. 기존 Pass의 발급 조건·잔여·과거 수업/지급/정산 보존을 유지하고 상품 변경은 새 Pass부터 적용한다(PR-006/030, BR-PAY-001, BR-011). 상품 판매 중단은 기존 Master 전용 수정 권한을 동일 적용하고 새 Pass 발급만 차단/기존 Pass 조건부 사용 유지로 별도 확정됐다(2026-10-12, BR-PAY-001). 상품 조회/Pass 발급 Actor 권한 및 판매 재개 등 나머지 상품 상태/삭제의 미정 상세는 별도 정책이며 MB-007의 생성/수정 권한 질문을 다시 OPEN으로 취급하지 않는다.

2026-10-12 사용자 확정(공통 PT 상품 생성·수정 권한 질문의 1번): “Master만 허용”을 선택했다. MB-007을 CLOSED로 처리한다.

확인 주체 / 승인 근거: 사용자, 2026-10-12 1번 답변.

<a id="mb-008"></a>
## MB-008. Branch 활성/비활성 정책

Question / TODO: Branch 재활성화의 구체 절차, 실제 운영 이력/비활성화 전 수업의 사실 확인 불가·정정, 미결정 신규 배정/다른 상태 조합 및 현재 업무와 지점 상태 변경의 경합은 어떻게 다루는가? B6 비활성화 가능/신규 업무 차단·기존 원본 보존과 G1–G5 기존 권한 내 로그인/조회·과거 수업 처리·타 활성 지점 기존 Pass/회원·활성 Trainer 이용·활성 지점으로의 권한별 이동은 확정됐으므로 재질문하지 않는다.

Status: OPEN

Related decisions / requirements: PD-004/011/022; PR-004/020/027. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Branch 수명·비활성화 상세 설계 확정 전

확정된 경계: Master는 기존 데이터가 있어도 지점을 비활성화할 수 있고 해당 지점 신규 배정/새 Pass 발급/새 실제 수업은 차단한다(B6). 기존 계정·역할/관계·Pass 잔여·과거 지급/정산/감사는 보존하며 자동 이동/소멸은 없다. G1–G5의 비활성 이후 업무 허용은 현재 행위별 권한/대상 조건을 유지하는 부분 해결이고, 지점 재활성화/역사 사실·미결정 신규 배정/다른 상태 조합을 일괄 승인한 것이 아니다.

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

2026-10-12 사용자 확정(회원 이동 대상에 비활성 지점을 허용할지 질문의 1번): Member Home Branch의 이동 대상은 동일 Organization 안에서 운영 중인 활성 Branch만 허용한다. 비활성 Branch로의 이동은 허용하지 않으며 Master Admin과 Branch Admin에 동일하게 적용한다. Backend에서도 대상 Branch의 활성 여부를 검증하고 비활성 대상 요청은 거부한다. 거부 시 기존 Member Home Branch·지원 허용·Pass·과거 업무 이력은 유지한다(BR-OPS-007, PD-004, PR-002/030, MB-002/008, NFR-001).

대상 활성 조건의 범위: 기존 이동 Actor/현재 관리 Scope·받는 지점 별도 승인 없음·저장 완료 즉시 적용/미래 예약 미지원은 유지한다. 이번 결정은 새 이동의 대상 Branch 조건이며 Branch 비활성화 가능 조건, 비활성화 당시 기존 Member/Trainer/Pass 처리·자동 이동, 이미 비활성인 출발 지점의 업무 조건이나 재활성화/과거 조회 정책까지 확정한 것은 아니다. 과거 소속 이력 정정/소급·Branch 상태의 저장 표현, 이동과 비활성화의 경합·필수 감사/UoW/실패 계약은 후속이다(MB-002/008).

2026-10-12 일괄 승인 반영: B6으로 기존 Member/Trainer/Pass가 있어도 Master의 지점 비활성화 허용, 해당 지점 신규 배정/새 Pass 발급/새 실제 수업 차단, 기존 소속/Pass/잔여·이력 보존, 선행 정리 강제/자동 이동/잔여 소멸 없음이 해결됐다(BR-OPS-016). 비활성 지점 과거 업무/조회·로그인/관리·재활성화와 다른 상태 조합/동시 요청의 상세는 후속이므로 전체 OPEN은 유지한다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch). 이 복합 OPEN의 다른 미결정 항목은 유지한다.

2026-10-12 G1–G5 모두 1번 승인: 유효 계정/역할의 기존 로그인·조회, 비활성화 전 실제 수업의 기존 권한별 누락 등록/정정/취소, 다른 활성 지점에서의 기존 Pass 사용 및 비활성 Home Branch Member/활성 Trainer의 허용된 수업, 활성 지점으로의 기존 권한별 소속 이동을 허용한다. 출발/발급/Home Branch를 먼저 재활성화하거나 옮기도록 요구하지 않는다. Member 이동은 Master/변경 전 현재 Home Branch 관리 Branch Admin, Trainer·Operator 이동은 Master만 가능하다. PT 업무의 실제 Performed Branch 인가와 정산 현재 Trainer Home Branch 인가는 구분하고 확정 월은 기존 해제/재확정·사유/이전본 보존을 따른다. 유효하지 않은 인증/Trainer 상태·회수 역할을 복원하거나 과거 보상/비용 귀속을 변경하지 않는다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch).

남은 게이트: 지점 재활성화의 상세 절차·실제 운영/소속/담당/수행 사실 확인 불가/정정, 미결정 신규 배정/다른 상태 조합·현재 요청/상태 변경 순서와 공개 계약/저장/UoW·잠금/경합이다. G1–G5 정책을 다시 OPEN으로 취급하지 않으며 MB-008 전체는 나머지 상세 때문에 OPEN을 유지한다.

2026-10-12 J 일괄 승인 반영: J2/J3의 Member 자체 상태와 Branch 자체 상태를 구별한다. G4 Home Branch 비활성 회원의 타 활성 지점 이용은 Member 자체도 활성이고 기존 PT 조건을 만족할 때 유지한다. Member 재활성화만으로 Branch/Trainer/Pass 상태를 복귀하지 않으며 나머지 Branch 재활성/역사 사실/다른 상태·경합 계약은 후속이다. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch). 이 복합 OPEN의 나머지 항목은 유지한다.

<a id="br-012"></a>
## BR-012. 월 기본급 적용 월·미확정 정산

Question / TODO: 나머지 월 경계/정산 대상·역사 사실 확인과 월별 금액 상한/누락·검증/버전/저장 계약을 구체화한다. AA1로 최초 일반 기본급 시작 월 이전의 유효 수업/실적 정산은 관리자가 사유를 남겨 해당 월 기본급을 명시적으로 직접 지정하고 이후 일반 설정을 유지한다. AA2로 미래 시작 월은 지원 유효 연월 안에서 업무상 기간 상한 없이 선택한다. 시작 월 한 번 지정/다음 변경까지 지속·종료 월/미래 월 목록 미요구, Q1 초기 세 값/시작 월 입력·Q2 일반 Base Salary 0원 이상 정수 원 및 기존 월별 사유 필수 명시0원/미입력 자동0 금지·수동 월 유지·미확정 반영/확정본 보존을 유지한다. 해결된 월 범위/이전 월 처리·0원/지속 적용을 재질문하지 않는다.

Status: OPEN

Related decisions / requirements: PD-009/012; PR-007/010; BR-PAY-014/016.

Required timing: 기본급 적용·정산 반영 상세 설계/구현 확정 전.

확정된 경계: 월 고정 기본급 지원, 관리자의 적용 시작 월 명시 지정과 아직 확정하지 않은 과거 월 지정 허용, 변경이 적용되는 수동 지정 없는 기존 미확정 정산의 기본급·합계 자동 반영, 과거 확정 기본급/합계의 자동 변경 금지와 확정된 월의 기본급 오류 시 해당 월 확정 해제·기본급 정정·동일 월 재확정 및 이전 확정본 보존은 확정이다. 기본급 오류 정정의 확정 해제·재확정은 Master Admin에게 Organization 전체, Branch Admin에게 각 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 처리한다. 입퇴사 일할·근무일수·휴직 기반 자동 급여 계산은 v1에서 제공하지 않는다. Rate/Fixed Amount의 신규 Session 적용 규칙을 기본급에 적용하지 않는다.

2026-10-10 사용자 확정(기본급 적용 시작 월 질문의 1번 답변): Base Salary를 변경할 때 권한 있는 관리자가 적용 시작 월을 명시적으로 지정한다. 변경한 달 또는 다음 달로 일괄 자동 지정하지 않는다. 예를 들어 10월 10일에 기본급을 2,500,000원에서 2,700,000원으로 변경하면 관리자가 10월 또는 11월 등 적용 시작 월을 선택한다. 기존 BR-PAY-010의 관리 범위·본인 설정 허용 조건·별도 승인 없음·필수 감사는 유지한다. 이미 확정된 월 정산의 적용 기본급과 합계는 자동 변경하지 않는다. 당시 미결정이었던 이미 작성된 미확정 정산의 반영 방식은 아래 후속 사용자 결정으로 확정했다. 미확정인 과거 월의 지정 허용은 아래 후속 사용자 결정으로 확정했다. 당시 미결정이었던 기본급 오류 정정과 현재·예정 기본급 설정의 관계는 아래 후속 사용자 결정으로 해당 월 정산에만 영향을 주는 것으로 확정했다. 미래 적용 월의 입력 범위 등 남은 정책은 BR-012 OPEN이다. Rate/Fixed Amount의 관리자 저장 완료 이후 신규 Session 적용 규칙과 구별한다. 적용 월·이력의 저장 구조와 월 정산 입력 계약은 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(이미 작성된 미확정 정산의 기본급 변경 반영 질문의 1번 답변): Base Salary 변경이 적용되는 월의 이미 작성된 미확정 정산에는 변경한 기본급과 그에 따른 월 합계를 자동 반영한다. 관리자가 정산에서 별도의 반영 작업을 실행해야 하는 절차는 두지 않는다. 예를 들어 10월 미확정 정산의 기본급이 2,500,000원이고 관리자가 10월부터 2,700,000원으로 변경하면, 그 미확정 정산의 적용 기본급은 2,700,000원이 되고 나머지 유효 구성 금액이 같을 때 합계는 200,000원 증가한다. 적용 시작 월 전의 정산과 이미 확정된 정산은 이 변경으로 자동 갱신하지 않는다. 기존 보상 설정 권한·별도 승인 없음·필수 감사와 과거 확정본 보존은 유지한다. 기본급 자동 반영은 정산 자동 확정이 아니며 미입력 지원 수업 등 기존 확정 차단 조건도 유지한다. Rate/Fixed Amount나 확정 Session Payment를 재계산하는 결정이 아니다. 지원 수업 보상 정정을 위한 확정 해제만을 이유로 현재 기본급을 과거 정산에 자동 적용하지 않는 기존 경계도 유지한다. 자동 반영의 저장/조회 방식과 기본급 변경·정산 확정 경합의 구체 일관성 전략은 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(과거 월을 기본급 적용 시작 월로 지정할 수 있는지 질문의 1번 답변): 아직 확정하지 않은 과거 월도 Base Salary 적용 시작 월로 지정할 수 있다. 예를 들어 10월에 기본급을 2,500,000원에서 2,700,000원으로 변경하면서 아직 미확정인 9월을 적용 시작 월로 지정할 수 있으며, 해당 변경이 적용되는 기존 9월 미확정 정산의 기본급·합계는 앞서 확정한 자동 반영 규칙을 따른다. 현재 월 이후로만 지정하도록 제한하지 않는다. 기존 관리 범위·별도 승인 없음·필수 감사와 적용 시작 월 전/확정된 정산의 자동 변경 금지를 유지한다. 과거 일반 Session Payment를 재계산하거나 정산을 자동 확정하지 않는다. 당시 미결정이었던 확정된 과거 월의 기본급 오류 정정 경로는 아래 후속 사용자 결정으로 해당 월 확정 해제·기본급 정정·동일 월 재확정 및 이전 확정본 보존으로 확정했다. 당시 미결정이었던 기본급 오류 정정과 현재·예정 기본급 설정의 관계는 아래 후속 사용자 결정으로 해당 월 정산에만 영향을 주는 것으로 확정했다. 미래 적용 월의 입력 범위 및 적용 월/이력의 저장·경합 처리 상세도 후속 검토 대상이다.

2026-10-10 사용자 확정(이미 확정된 월의 기본급 오류 처리 질문의 1번 답변): 이미 확정된 월 정산의 적용 기본급에 오류가 있으면 해당 Trainer·월의 확정을 해제하고 그 월의 기본급을 정정한 뒤 동일 월 정산을 재확정한다. 이전 확정본의 적용 기본급·구성 금액·합계를 이력으로 보존하고 재확정본과 구분한다. 예를 들어 9월 기본급을 2,500,000원으로 확정했지만 2,700,000원이어야 했다면 9월 확정 해제 → 9월 적용 기본급 2,700,000원으로 정정 → 9월 재확정으로 처리한다. 나머지 유효 구성 금액이 같으면 재확정 합계는 200,000원 증가하고, 이전 기본급 2,500,000원이 반영된 확정본은 보존한다. 현재 Base Salary 설정 변경에 따른 자동 갱신과 구별되는 명시적 오류 정정 업무다. 과거 일반 Session Payment는 현재 Rate/Fixed Amount로 재계산하지 않으며 PT 진행 기록·Pass 차감을 재실행하지 않는다. 재확정에도 해당 Trainer·월의 미입력 지원 수업 차단 등 승인된 확정 조건을 적용한다. 이번 결정은 정정 순서와 이전 확정본 보존에 한정한다. 당시 미결정이었던 기본급 오류 정정의 확정 해제·재확정 권한과 별도 Master 승인 여부는 아래 후속 사용자 결정으로 확정했다. 당시 미결정이었던 확정 해제·해당 월 기본급 수정의 사유 필수 여부는 아래 후속 사용자 결정으로 확정했다. 당시 미결정이었던 기본급 오류 정정과 현재·예정 기본급 설정의 관계는 아래 후속 사용자 결정으로 해당 월 정산에만 영향을 주는 것으로 확정했다. 기존 보상 설정 권한과 지원 수업 보상 정정에 승인된 권한·승인·사유 정책은 각각 기존 범위를 유지한다. 구체 저장 모델·공개 계약·업무 트랜잭션·경합 전략은 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(기본급 오류 정정을 직접 처리할 권한 질문의 1번 답변): 기본급 오류 정정의 확정 해제·재확정은 Master Admin에게 Organization 전체, Branch Admin에게 각 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 처리한다. 수업의 Performed Branch나 과거 Home Branch만을 근거로 다른 소속 Trainer의 위 정정 권한을 얻지 않는다. Branch Admin은 확정 해제와 재확정 등 각 업무 처리 시점에 현재 Home Branch를 다시 검증하며 이전 소속만으로 권한을 유지하지 않는다. 관리자 권한 없는 Operator·Trainer는 이 작업을 수행할 수 없다. 해당 Trainer·월의 확정 해제 → 해당 월 적용 기본급 정정 → 동일 월 재확정, 이전 확정본과 정정 이력·감사 보존 및 재확정 시 미입력 지원 수업 차단 등 승인된 조건은 유지한다. 이번 결정은 기본급 오류 정정의 관리 역할/대상 범위와 별도 Master 승인 없음에 한정한다. 최초 월 정산 확정 권한과 전체 정산 공개 범위(MB-006)는 이번에 확정하지 않는다. 당시 미결정이었던 기본급 오류 정정과 현재·예정 기본급 설정의 관계는 아래 후속 사용자 결정으로 해당 월 정산에만 영향을 주는 것으로 확정했다. 당시 미결정이었던 확정 해제·해당 월 기본급 수정의 사유 필수 여부는 아래 후속 사용자 결정으로 확정했다. 구체 인증/인가 계약·저장·경합 처리 전략은 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(기본급 오류 정정 사유 질문의 1번 답변): 확정된 월의 기본급 오류 정정에서 확정 해제와 해당 월 기본급 수정 모두 사유가 필수다. Master Admin·Branch Admin 및 관리 범위 안 본인 건에 동일하게 적용한다. 해제 사유·해제자·시점과 변경 전후 기본급·수정 사유·수정자·시점을 이력으로 남긴다. 사유가 없는 확정 해제 요청과 사유가 없는 해당 월 기본급 수정 요청은 각각 해당 작업을 거부하며, 요청 직전의 상태·금액·기존 확정본을 변경하지 않는다. 기존 Master Organization 전체/Branch Admin 각 처리 시점 대상 Trainer 현재 Home Branch 기준 인가와 관리 범위 안 본인 건 허용·별도 Master 승인 없음은 유지한다. 해당 Trainer·월 확정 해제 → 해당 월 적용 기본급 정정 → 동일 월 재확정 경로, 이전 확정본과 정정 이력·감사 보존, 재확정 시 미입력 지원 수업 차단 등 승인된 조건도 유지한다. 이번 결정은 확정된 월의 기본급 오류 정정에 한정한다. 일반 보상 설정 변경은 BR-PAY-010의 기존 감사 요건을 따른다. 당시 미결정이었던 기본급 오류 정정과 현재·예정 기본급 설정의 관계는 아래 후속 사용자 결정으로 해당 월 정산에만 영향을 주는 것으로 확정했다. 미래 적용 월의 입력 범위 등 남은 정책은 BR-012 OPEN이다. 사유 입력 화면·저장 형식·업무 계약/트랜잭션의 구체 구성은 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(과거 월 정정이 다른 월에 미치는 영향 질문의 1번 답변): 기본급 오류 정정은 대상 Trainer의 해당 월 정산에만 적용하며 현재·미래 기본급 설정과 다른 월 정산은 유지한다. 지속적인 기본급 변경은 별도로 적용 시작 월을 지정하는 기존 흐름을 따른다. 예를 들어 9월 기본급을 2,500,000원에서 2,700,000원으로 정정하면 9월 재확정에는 명시적으로 정정한 2,700,000원을 사용하고 이전 확정본은 보존한다. 이 정정만으로 현재 기본급 설정, 미래에 적용하도록 지정한 설정 또는 10월 등 다른 월 정산의 적용 기본급·합계를 바꾸지 않는다. 10월 미확정 정산이 2,500,000원인 예에서는 그 금액을 그대로 유지한다. 일반 보상 설정 변경의 적용 시작 월 지정 및 적용되는 기존 미확정 정산 자동 반영은 별도의 명시적 변경 업무로 유지한다. 기존 Master Organization 전체/Branch Admin 각 처리 시점 Trainer 현재 Home Branch 기준 인가·관리 범위 안 본인 건 허용·별도 Master 승인 없음, 확정 해제와 해당 월 기본급 수정의 사유 필수, 이전 확정본·전후 값·처리자/시점 이력·감사 및 재확정 조건은 유지한다. 월 정산의 정정 기본급 보존과 설정 입력 계약·저장 모델·경합 처리는 후속 Architecture 검토 대상이며 이번 결정으로 기술안을 승인하지 않는다.

2026-10-10 사용자 확정(입사·퇴사·휴직이 있는 달의 기본급 질문의 1번 답변): 입사·퇴사·휴직이 있는 달의 적용 기본급은 관리자가 해당 Trainer·월의 금액을 직접 지정한다. 예를 들어 월 기본급 설정이 2,500,000원이어도 해당 월만 1,500,000원을 적용할 수 있으며, 이 지정으로 현재·미래 기본급 설정과 다른 월 정산은 변경하지 않는다. 해당 월 정산의 기본급 구성과 월 합계는 직접 지정한 적용 금액을 사용하며, 입퇴사 일할·근무일수·휴직 기반 자동 급여 계산은 v1에서 제공하지 않는다. 지속적인 기본급 변경은 기존 적용 시작 월 지정 업무로 구분한다. 월별 금액 지정만으로 정산을 자동 확정하거나 미입력 지원 수업 등 승인된 확정 조건을 우회하지 않는다. 이미 확정된 월의 금액을 변경하려면 기존 해당 월 확정 해제 → 기본급 정정 → 동일 월 재확정 경로와 승인된 권한·사유·이력/감사·이전 확정본 보존 조건을 따른다. 과거 일반 Session Payment와 PT 진행 기록·Pass 차감은 재계산/재실행하지 않는다. 이번 결정은 월별 수동 지정 방식과 해당 월에 한정된 효과를 확정한 것이며, 미확정 월 수동 지정의 입력 한도를 새로 확정하지 않는다. 당시 미결정이었던 미확정 월 수동 지정의 역할/대상 범위와 별도 승인 여부는 아래 후속 사용자 결정으로 Master Organization 전체/Branch Admin 처리 시점 Trainer 현재 Home Branch 기준·관리 범위 안 본인 포함·별도 Master 승인 없음으로 확정했다. 당시 미결정이었던 최초 수동 지정·수정의 사유 필수 여부는 아래 후속 사용자 결정으로 모두 필수로 확정했다. 당시 미결정이었던 수동 지정 뒤 일반 기본급 설정 변경 시 우선순위는 아래 후속 사용자 결정으로 수동 지정 금액 유지·수동 지정 없는 월만 자동 반영하도록 확정했다. 저장 모델·공개 계약·감사 구성·경합 전략은 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(수동 지정 금액과 이후 설정 변경의 우선순위 질문의 1번 답변): 월별로 수동 지정한 기본급은 이후 일반 기본급 설정이 변경되어도 유지한다. 일반 설정 변경의 미확정 정산 자동 반영은 수동 지정이 없는 월에 적용하며, 수동 지정 월의 금액을 바꾸려면 관리자가 해당 월 금액을 직접 수정한다. 예를 들어 미확정인 10월 적용 기본급을 1,500,000원으로 직접 지정한 뒤 일반 기본급 설정을 10월부터 2,500,000원에서 2,700,000원으로 변경하면, 일반 설정은 2,700,000원으로 변경하되 10월의 수동 지정 기본급은 1,500,000원을 유지한다. 다른 유효 구성 금액이 같다면 해당 10월 정산의 합계도 이 설정 변경만으로 바뀌지 않는다. 같은 변경의 적용 대상인 수동 지정 없는 미확정 월에는 일반 설정의 2,700,000원과 그에 따른 합계를 기존 규칙대로 자동 반영한다. 월별 수동 지정 자체로 현재·미래 기본급 설정이나 다른 월을 변경하지 않는 기존 경계와 구분한다. 이미 확정된 월 정산의 자동 변경 금지·정정 시 해제/정정/재확정과 이전 확정본 보존, 미입력 지원 수업 등 확정 조건 및 정산 자동 확정 금지는 유지한다. Rate/Fixed Amount 적용이나 과거 일반 Session Payment·PT 진행 기록·Pass 차감 처리도 변경하지 않는다. 이번 결정으로 미확정 월 수동 지정의 입력 한도 또는 자동 반영으로 복귀하는 기능을 승인하지 않는다. 당시 미결정이었던 미확정 월 수동 지정의 역할/대상 범위와 별도 승인 여부는 아래 후속 사용자 결정으로 Master Organization 전체/Branch Admin 처리 시점 Trainer 현재 Home Branch 기준·관리 범위 안 본인 포함·별도 Master 승인 없음으로 확정했다. 당시 미결정이었던 최초 수동 지정·수정의 사유 필수 여부는 아래 후속 사용자 결정으로 모두 필수로 확정했다. 수동 지정 여부와 월 적용 금액을 보존하는 저장 모델·공개 계약·감사·설정 변경/월 확정 경합 전략은 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(미확정 월의 기본급 수동 지정 사유 질문의 1번 답변): 미확정 월의 기본급을 최초 수동 지정하거나 다시 수정할 때 모두 사유가 필수다. 사유가 없는 요청은 거부하고 요청 직전의 수동 지정 여부·적용 금액·월 합계를 유지한다. 대상 Trainer·월, 지정/수정 전후 금액·사유·처리자·처리 시점을 이력으로 남긴다. 예를 들어 월 기본급 설정 2,500,000원과 별개로 중도 입사 월을 1,500,000원으로 최초 지정할 때도 사유를 남기며, 이후 해당 월 금액을 다시 수정할 때도 수정 사유를 남긴다. 이 업무를 수행할 권한이 있는 관리자에게 동일하게 적용하는 사유 요건이며 이번 결정만으로 새로운 인가 범위나 추가 승인 절차를 정하지 않는다. 월별 수동 지정으로 현재·미래 기본급 설정과 다른 월 정산을 변경하지 않는 경계, 이후 일반 설정 변경에도 수동 지정액 유지·수동 지정 없는 미확정 월만 자동 반영, 정산 자동 확정 금지 및 미입력 지원 수업 등 승인된 확정 조건을 유지한다. 이미 확정된 월의 변경은 기존 해제/정정/재확정과 사유 필수·인가·이력/감사·이전 확정본 보존 조건을 따른다. 일반 Rate/Fixed Amount/Base Salary 설정 변경 전체에 사유 필수를 새로 적용하는 결정이 아니며 그 업무의 기존 감사 요건을 유지한다. 당시 미결정이었던 미확정 월 수동 지정의 역할/대상 범위와 별도 승인 여부는 아래 후속 사용자 결정으로 Master Organization 전체/Branch Admin 처리 시점 Trainer 현재 Home Branch 기준·관리 범위 안 본인 포함·별도 Master 승인 없음으로 확정했다. 입력 제약은 BR-012 등 관련 OPEN을 따르고, 사유 저장 형식·월별 적용 금액/수동 지정 상태·감사 이력의 공개 계약과 트랜잭션/경합 전략은 후속 Architecture 검토 대상이다.

2026-10-10 사용자 확정(미확정 월 기본급 수동 지정·수정의 처리 권한 질문의 1번 답변): 미확정 월 기본급의 최초 수동 지정·수정은 Master Admin의 Organization 전체, Branch Admin의 각 처리 시점 대상 Trainer 현재 Home Branch가 관리 Branch와 일치하는 범위에서 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 직접 처리한다. 최초 수동 지정과 이후 수정 요청마다 서버에서 현재 권한·관리 Scope·대상 Trainer의 현재 Home Branch를 검증한다. 예를 들어 Trainer가 수원 Home Branch에서 강남으로 이동한 뒤의 미확정 월 수동 지정·수정은 현재 강남 Branch Admin의 관리 범위에서 허용하며, 별도 Master 권한 없는 이전 수원 Branch Admin에게는 과거 소속만으로 허용하지 않는다. Performed Branch가 자기 지점이라는 이유로 다른 Home Branch Trainer의 월 기본급을 지정/수정할 권한을 얻지 않는다. 관리자 권한 없는 Operator·Trainer는 수행할 수 없으며 직접 ID·위조 Branch Context로 우회할 수 없다. Master·Branch Admin과 관리 범위 안 본인 건 모두 기존 최초 지정/수정 사유 필수·사유 누락 요청 변경 없이 거부·전후 금액/사유/처리자/시점 이력 및 감사 원칙을 따른다. 월별 지정으로 현재·미래 설정과 다른 월 정산을 변경하지 않으며 이후 일반 설정 변경에도 수동 지정액을 유지한다. 이 권한으로 전체 정산 조회나 최초 월 정산 확정 권한을 자동 부여하지 않으며 MB-006과 남은 정산 확정 정책은 OPEN을 유지한다. 확정된 월의 변경은 기존 해제/정정/재확정 경로와 승인 조건을 따른다. 미래 적용 월의 입력 범위·금액 입력 제약은 BR-012/BR-010의 남은 질문이며 구체 인가 계약·저장 모델·필수 감사/UoW·소속 이동 및 월 확정 경합 처리는 후속 Architecture 검토 대상이다.

2026-10-11 사용자 확정(해당 월 기본급의 0원 수동 지정 허용 질문의 1번 답변): 해당 월 기본급은 권한 있는 관리자가 사유를 남기면 0원으로 명시적으로 수동 지정할 수 있다. 수동 지정한 0원은 미입력과 구분하며, 미입력이나 누락된 일반 설정을 자동으로 0원으로 대체하지 않는다. 해당 월 기본급에만 적용하고 다른 유효 지급·추가실적은 기존 규칙대로 합산한다. 예를 들어 해당 월 기본급을 0원으로 수동 지정하고 유효 일반 Session Payment가 1,200,000원, 유효 Additional Performance가 150,000원이면 월 합계는 1,350,000원이다. 0원 지정으로 PT 진행 기록·Pass 차감을 취소/복원하거나 다른 지급·실적을 0원으로 변경하지 않는다. 기존 Master Organization 전체/Branch Admin 각 처리 시점 Trainer 현재 Home Branch 기준 인가·관리 범위 안 본인 허용·별도 Master 승인 없음, 최초 수동 지정/수정 사유 필수 및 사유 누락 요청 변경 없이 거부·전후 금액/사유/처리자/시점 이력과 감사 원칙을 동일하게 적용한다. 이 월별 지정으로 현재·미래 일반 기본급 설정과 다른 월 정산을 변경하지 않으며, 이후 일반 설정이 바뀌어도 해당 월의 명시적 수동 지정 0원을 유지한다. 수동 지정하지 않은 월은 기존 일반 설정 적용 규칙을 따른다. 정산 자동 확정이나 미입력 지원 수업 등 기존 확정 차단 조건의 해소를 뜻하지 않으며, 이미 확정된 월의 금액 변경은 기존 해제/정정/재확정과 이전 확정본 보존 조건을 따른다. 이번 허용은 월별 수동 적용 기본급에 한정하며 일반 Compensation Setting의 Base Salary/Rate/Fixed Amount, Product 가격·일반 Session Payment 또는 다른 추가실적의 0원 허용으로 확대하지 않는다. 음수·상한·정밀도·누락값 처리 등 나머지 입력 정책과 미래 적용 월 범위는 BR-010/BR-012 OPEN을 유지한다. 명시적 0원·미입력·수동 지정 여부를 구분하는 저장/조회 계약 및 감사·UoW·경합 전략은 후속 Architecture 검토 대상이다.

2026-10-11 사용자 명확화(기본급 변경 후 다음 변경까지 유지): 일반 Base Salary 설정은 관리자가 지정한 적용 시작 월부터 다음 기본급 변경의 적용 시작 월 전까지 매월 계속 적용한다. 적용 종료 월을 지정하거나 같은 금액을 매월 다시 등록할 필요는 없다. 예를 들어 10월부터 2,700,000원으로 변경하고 이후 변경이 없으면 11월·12월 이후에도 매월 2,700,000원을 적용한다. 이후 12월에 다시 변경하여 12월부터 2,800,000원을 적용하도록 정하면 10월·11월은 2,700,000원, 12월부터는 다음 변경 전까지 매월 2,800,000원이다. 이는 일반 기본급 설정의 지속 적용 원칙이며, 입사·퇴사·휴직 등으로 특정 월 금액을 수동 지정하는 기존 예외는 해당 월에만 적용한다. 일반 설정이 10월부터 2,700,000원이고 10월만 1,500,000원으로 수동 지정한 경우 10월은 1,500,000원, 수동 지정이 없는 11월부터는 일반 설정의 2,700,000원을 적용한다. 기존 수동 지정액 유지·미확정 정산 자동 반영·확정 정산의 자동 변경 금지·권한/사유/이력/감사 규칙은 유지한다. 이번 명확화는 금액의 지속 적용에 관한 것이며, 변경을 얼마나 먼 미래의 시작 월로 미리 등록할 수 있는지에 대한 앞선 선택지의 답변으로 간주하지 않는다. 해당 입력 범위와 나머지 금액 입력 제약은 BR-012/BR-010 OPEN을 유지한다. 구체 유효 월 이력·조회 계약·저장 모델·경합 전략은 후속 Architecture 검토 대상이다.

BR-012는 월별 수동 기본급의 사유 필수 0원 허용과 일반 기본급의 다음 변경까지 지속 적용을 부분 해결했다. 얼마나 먼 미래의 시작 월로 변경을 미리 등록할 수 있는지 및 나머지 금액 입력 제약이 남아 OPEN을 유지한다.

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

2026-10-13 Q1/Q2=1 부분 해결: Trainer 최초 등록 완료에는 세 보상 값과 기본급 적용 시작 월이 필요하며 일반 Fixed Amount/Base Salary는 명시적 0원 이상 정수 원이다. 누락 기본값·미전달 초기화는 금지하고 기존 인가/최초 감사·시작 월부터 지속/종료 월 불필요·신규 지급 적용/과거 확정 결과 불변 및 다른 업무의 금액 규칙을 유지한다. 초기/일반 금액 부분은 확정됐고 상한/월 경계·다른 필드/역사 사실·최소 계약 때문에 Status는 OPEN이다. [Q 승인](product-decisions.md#review-20261013-q-batch); BR-OPS-028/PAY-022; V-114/115 미구성·미실행.

2026-10-13 AA1/AA2=1 부분 해결: 최초 시작 월 이전 유효 PT/실적의 정산 월 기본급은 기존 관리자 범위에서 사유를 남겨 해당 월만 직접 지정하며 이후 일반 설정은 유지한다. 미래 시작 월은 지원 유효 연월 안에서 업무상 기간 상한 없이 선택한다. 명시0원/사유·현재 인가/감사·수동 월·확정본 보존과 한 시작 월부터 다음 변경까지 지속을 유지한다. 나머지 월/역사 사실·대상/입력 상한/최소 계약·버전/저장/경합 때문에 OPEN이다. [AA 승인](product-decisions.md#review-20261013-aa-batch); BR-PAY-014; V-130/131 미구성·미실행.

<a id="br-013"></a>
## BR-013. 추가실적 권한·금액·처리 절차

Question / TODO: 지원 수업 외 추가실적의 나머지 입력 범위·실제 발생/소속 사실과 월 경계·소급 기간·내용/연결 필드별 계약·정정 연결·여러 Trainer/월 영향의 단계별 처리/실패·재시도는 어떻게 다루는가? 지원 수업 미입력 보상 추적 표현/후속 금액 입력·기존 수업 취소 연동의 계약 상세는? 관리자 수동 등록/양수 금액·발생 월/당시 Home 비용·확정 월 해제/처리/재확정, 금액 정정과 H2/H3 내용 수정/취소의 현재 Home Branch 관리자 Scope·본인 포함/승인 없음·사유/이력, 대상 Trainer/발생 날짜 오류의 취소 후 재등록은 확정이며 재질문하지 않는다. Operator/Trainer 단독 정정 권한은 추가하지 않는다.

2026-10-11 비용 집계와의 경계: 타 지점 지원 수업의 전체 보상으로 확정한 Additional Performance 금액은 해당 수업의 실제 Performed Branch 비용으로 집계한다. 기존 관리자 입력·정정 권한·지원 수업 보상의 중복 지급 금지·이력 보존은 유지한다. 이 결정으로 나머지 정정/취소 절차·이동 시점·비용 보고 공개/집계 상세를 확정하지 않는다(MB-010/006).

2026-10-11 지원 수업 외 추가실적 비용 결정과의 경계: 지원 수업 외 Additional Performance의 비용은 실적 발생 당시 대상 Trainer의 Home Branch에 귀속한다. 등록 시점·금액 확정 시점·대상 월말 또는 조회 시점의 소속으로 대체하지 않는다. 이 발생 당시 Home Branch는 비용 집계 기준이며 최초 등록/정정 인가의 시점 기준을 확정한 것이 아니다. 금액 산정·0원 등 입력 제약·신청 승인·정산 월 귀속·남은 정정/취소 및 발생 시점/소속 확인 예외는 미정으로 남긴다(MB-010 연결).

Status: OPEN

Related decisions / requirements: PD-027; PR-031/027/010; BR-PAY-015.

Required timing: 추가실적 입력·권한·계산·승인·정정 상세 설계/구현 확정 전.

확정된 경계: 추가실적 v1 도입과 생성·정정·취소 감사는 확정이다. 2026-10-10 사용자가 관리자 역할 질문의 1번을 선택하여 Master Admin과 Branch Admin 모두 직접 등록할 수 있도록 확정했다. 이어 대상 범위 질문의 2번을 선택하여 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에게만 직접 등록하도록 확정했다. 타 지점 수업도 Trainer 소속 지점 관리자 또는 Master가 등록한다. 자기 지점에서 지원 수업을 했다는 이유로 다른 Home Branch Trainer의 추가실적 등록 권한을 얻지 않는다. 이 권한은 보상 설정에서 자동 상속한 것이 아니라 별도로 사용자 승인된 규칙이다.

같은 날 승인 질문의 1번 답변으로 Branch Admin이 본인이 아닌 자기 지점 소속 Trainer의 추가실적을 직접 등록할 때는 별도 Master 승인이 필요 없다고 확정했다. 이 등록에 Master 승인 대기 단계를 추가하지 않으며 생성·변경 감사는 유지한다. Trainer 신청 승인·월 정산 확정 절차에 이 결정을 확대하지 않는다. 본인 건은 아래의 후속 사용자 결정으로 별도 확정했다. 승인 생략만으로 금액 산정·확정 시점·정정/취소 정책까지 정하지 않는다.

같은 날 본인 등록 질문의 2번 답변으로 관리자와 Trainer를 겸하면 관리 범위 안에서 본인의 추가실적도 직접 등록할 수 있다고 확정했다. Master Admin은 Organization 범위 안의 본인 Trainer에게, Branch Admin은 본인 Trainer의 Home Branch가 관리 Branch와 일치할 때 허용한다. Branch Admin의 본인 Home Branch가 다른 경우에는 허용하지 않는다. 기존 한 계정 겸임과 별도의 관리 권한·대상 Scope 검증을 따르며 Trainer 역할만으로 이 권한을 얻지 않는다. 본인 등록도 동일하게 감사 대상이며 등록 Actor와 대상 Trainer가 같은 사람인 경우를 구분할 수 있어야 한다. 보상 설정의 본인 접근 권한에서 자동 상속한 것이 아닌 추가실적 업무의 별도 사용자 결정이다.

같은 날 본인 건 승인 질문의 1번 답변으로 Master Admin/Branch Admin과 Trainer를 겸하는 관리자가 관리 범위 안에서 본인에게 직접 등록한 추가실적도 별도 승인 없이 처리한다고 확정했다. Master 또는 다른 관리자의 승인 대기 단계를 추가하지 않는다. 관리 Scope와 대상 Trainer Home Branch 검증, 본인 등록의 생성·변경 감사 및 Actor/대상 동일인 추적은 유지한다. 이 결정은 Trainer 신청 승인·월 정산 마감/확정·금액 산정·확정 시점·정정/취소 정책으로 확대하지 않는다.

같은 날 타 지점 지원 수업의 금액 계산 질문에서 3번을 선택하여 관리자가 수업 건별 보상 금액을 직접 입력하도록 확정했다. 권한 있는 Master Admin 또는 해당 Trainer Home Branch의 Branch Admin이 입력하며 관리 범위 안의 본인 건도 기존 승인 생략·감사 정책을 따른다. 입력 금액 전부를 해당 수업의 Additional Performance로 처리하고 일반 Session Payment를 별도로 합산하지 않는다. 일반 RATE/FIXED_AMOUNT 계산 결과를 자동 지급액으로 사용하거나 Trainer별 지원 전용 고정금액을 채택하지 않는다. PT 진행 기록·Pass 선택/차감·감사 원칙은 유지한다.

2026-10-10 사용자 확정(진행 기록과 보상 확정 시점 질문의 1번 답변): 타 지점 지원 수업은 보상 금액 없이도 허용된 PT 진행 기록과 Pass 차감을 먼저 완료한다. 권한 있는 관리자가 나중에 수업 건별 금액을 저장할 때 해당 Additional Performance 보상을 확정한다. 금액 미입력은 확정된 0원과 구분하고 누락 건을 추적할 수 있어야 한다. 해당 Trainer의 해당 월 정산 대상 지원 수업에 금액 미입력 건이 하나라도 있으면 그 Trainer·월 정산을 확정할 수 없다. 일반 Session Payment의 등록 시 계산·확정 규칙은 유지한다. 관리자 역할·Home Branch 범위·본인 등록·별도 승인 없음·감사 정책도 유지한다. 당시 미결정이었던 금액 미입력 월의 정산 확정 조건은 아래 후속 사용자 결정으로 해결했다. 월 귀속·마감 이후 처리의 남은 세부 정책은 OPEN이다.

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

이번 결정은 타 지점 지원 수업에 한정한다. 금액 미입력 건의 추적 표현·정정 연동, PT 진행 기록 연계 상세·나머지 정정/취소는 BR-013 OPEN이며 지원 수업의 다른 입력값 범위·정밀도와 지원 수업 외 추가실적의 상한액·정밀도 등은 BR-010 OPEN이다(등록은 양수만 허용, 2026-10-11 사용자 확정). 지원 수업 외 추가실적의 남은 입력 제약과 Operator의 남은 업무 권한, 지원 수업 외 실적의 금액 외 정보 수정/취소의 소속 이동 시 권한 기준 시점도 미정이다. 이번에 별도로 승인한 월 정산 확정 전 지원 수업 금액 수정 외에는 등록 권한만으로 정정/취소·타 지점 전체 자료 열람을 허용하지 않고 비용 귀속·정산 공개(MB-010/006)도 정하지 않는다. 남은 권한·금액·상태 전이 질문이 있어 BR-013 전체는 OPEN을 유지한다.

2026-10-11 사용자 확정(회원 유지 등 지원 수업 외 추가실적의 금액 산정 방식 질문의 1번 답변): 회원 유지 등 지원 수업 외 Additional Performance의 금액도 권한 있는 관리자가 실적 건별로 직접 입력한다. v1에서 유형별 사전 금액·산식으로 자동 계산하는 방식을 채택하지 않으며 일반 RATE/FIXED_AMOUNT 계산 결과로 입력액을 대체하지 않는다. 기존 Master Organization 전체/Branch Admin 대상 Trainer Home Branch 범위·관리 범위 안 본인 등록·별도 승인 없음·감사는 유지한다. 비용은 실적 발생 당시 Trainer Home Branch에 귀속하는 기존 기준을 따른다. 이 결정은 금액 산정 방식에 한정하며 지원 수업 외 실적의 금액 확정 시점·미입력/0원·입력 제약·정산 월·이동 시 등록/정정 인가 시점·Trainer 신청/승인·정정/취소 등 남은 정책은 관련 OPEN이다. 지원 수업에 승인된 기록/차감 후 보상 확정·사유 필수 0원·금액 미입력 월 정산 차단을 다른 실적에 자동 적용하지 않는다. BR-013 전체는 잔여 질문으로 OPEN을 유지한다.

2026-10-11 사용자 확정(Trainer의 별도 추가실적 신청 기능 질문의 1번 답변): v1 추가실적은 권한 있는 관리자의 직접 등록만 지원하고 Trainer의 시스템 내 별도 신청·승인/반려 흐름은 두지 않는다. Trainer는 실적 내용을 관리자에게 전달하며 기존 Master Admin/Branch Admin이 허용된 관리 범위에서 입력한다. Master Organization 전체/Branch Admin 대상 Trainer Home Branch 범위·관리 범위 안 본인 등록·별도 승인 없음·감사는 유지한다. 관리자·Trainer 겸임자는 관리 권한 범위 안에서 본인에게 직접 등록할 수 있으며 Trainer 역할만으로 등록 권한을 얻지 않는다. Trainer의 실제 PT 진행 기록 등록은 계속 지원하며 이를 추가실적 신청으로 취급하지 않는다. 지원 수업의 진행 기록·Pass 차감 완료 후 관리자 금액 저장 시 보상 확정과 미입력 지원 수업의 해당 Trainer·월 정산 확정 차단은 유지한다. 금액 산정·비용 귀속·기존 정정/확정/조회 권한은 변경하지 않는다. 추가실적의 남은 입력 제약/확정 시점·소속 이동 시 인가 시점·정산 월·정정/취소 등은 관련 OPEN이며 신청 기능의 향후 도입은 별도 결정 대상이다. 신청 기능 여부는 다시 미정으로 취급하지 않으며 BR-013 전체는 나머지 질문으로 OPEN을 유지한다.

2026-10-11 사용자 확정(지원 수업 외 추가실적의 등록 시점 질문의 1번 답변): 회원 유지 등 지원 수업 외 Additional Performance는 권한 있는 관리자가 실적 내용과 금액을 함께 입력해야 등록이 완료된다. 금액 미입력 요청은 등록을 완료할 수 없으며, 금액 없는 실적을 먼저 등록하고 나중에 금액을 입력하는 흐름은 v1에 두지 않는다. 누락 금액을 자동으로 0원이나 계산식 결과로 대체하지 않는다. 기존 관리자 역할/대상 Home Branch 범위·관리 범위 안 본인 등록·별도 승인 없음·감사와 발생 당시 Home Branch 비용 귀속을 유지한다. 지원 수업은 기존대로 PT 진행 기록·Pass 차감을 먼저 완료하고 관리자 금액 저장 시 보상을 확정하며, 미입력 지원 수업의 해당 Trainer·월 정산 확정 차단도 유지한다. 이번 결정은 지원 수업 외 실적의 최초 등록 금액 입력 요건에 한정한다. 0원 허용·금액 범위/정밀도·이동 시 등록/정정 인가 시점·정산 월·수정/취소 등은 관련 OPEN이며 월 정산을 자동 확정하거나 지원 수업의 정산 차단 규칙을 다른 실적에 확장하지 않는다. BR-013 전체는 나머지 질문으로 OPEN을 유지한다.

2026-10-11 사용자 확정(지원 수업 외 추가실적의 0원 등록 허용 여부 질문의 1번 답변): 회원 유지 등 지원 수업 외 Additional Performance의 등록 금액은 0원보다 큰 양수만 허용한다. 0원과 음수 입력은 등록을 거부하며, 사유를 남겨도 0원으로 등록할 수 없다. 기존대로 내용과 금액을 함께 입력해야 등록이 완료되고 누락 금액을 자동으로 채우지 않는다. 지원 수업의 사유 필수 0원 확정 허용·금액 미입력과 명시적 0원 구분·PT 진행 기록/Pass 차감 선완료 및 미입력 지원 수업 월 정산 확정 차단은 유지한다. 기존 관리자 역할/대상 Home Branch 범위·관리 범위 안 본인 등록·별도 승인 없음·감사와 발생 당시 Home Branch 비용 귀속도 유지한다. 이 결정은 지원 수업 외 실적의 등록 금액에 한정한다. 상한액·정밀도/금액 표현·정산 월·이동 시 인가·정정/취소는 관련 OPEN이며 음수 금액 등록이나 0원 덮어쓰기를 미정 정정/취소 절차의 대체로 도입하지 않는다. 일반 보상 설정·상품·월별 적용 기본급의 금액 제약을 변경하지 않는다. BR-013 전체는 나머지 질문으로 OPEN을 유지한다.

2026-10-11 사용자 확정(지원 수업 외 추가실적을 반영할 정산 월 질문의 1번 답변): 회원 유지 등 지원 수업 외 Additional Performance는 실제 실적이 발생한 월의 Trainer 월 정산에 귀속한다. 9월에 발생한 실적을 10월에 등록해도 9월분이며 등록 월이나 금액 입력 월로 이월하거나 관리자가 반영 월을 임의 선택하지 않는다. 같은 실적을 9월·10월에 중복 합산하지 않는다. 금액을 함께 입력해야 최초 등록이 완료되고 양수만 허용하는 기존 규칙·관리자 직접 등록/관리 범위 안 본인 등록·승인 생략·감사를 유지한다. 비용은 실적 발생 당시 Trainer Home Branch에 귀속하는 기존 기준을 따르며 발생 월/비용 지점이 등록 권한을 자동 부여하지 않는다. 이 결정은 Trainer 월 정산의 귀속 월 기준에 한정한다. 이미 확정된 발생 월에 뒤늦게 추가하는 허용 여부·확정 해제/재확정·권한/사유·이전 확정본 처리의 상세는 BR-009/013에서 별도 결정하며 확정본을 자동 변경하지 않는다. 발생 시점 식별/월 경계·시간대·소급 등록 허용 기간·이동 시 등록/정정 인가 시점·정정/취소 및 비용 보고의 대상 기간/집계 상세는 관련 OPEN이다. 지원 수업/일반 지급의 남은 월 귀속·마감 정책을 이 결정으로 확정하지 않는다. BR-013 전체는 나머지 질문으로 OPEN을 유지한다.

2026-10-11 사용자 확정(확정된 월의 누락된 지원 수업 외 추가실적 처리 질문의 1번 답변): 이미 확정된 발생 월의 누락된 지원 수업 외 Additional Performance는 해당 Trainer·월 정산의 확정 해제 → 누락 실적 등록 → 같은 발생 월 재확정으로 반영한다. 이전 확정본은 보존하고 재확정 결과와 구분한다. 확정 상태에 직접 추가하여 이전 확정본을 덮어쓰거나 등록 월/다른 월로 이월하지 않는다. 누락 실적은 기존대로 내용과 양수 금액을 함께 입력하며 관리자 직접 등록 역할/대상 범위·관리 범위 안 본인 등록·승인 생략·감사와 발생 당시 Home Branch 비용 귀속을 유지한다. 재확정은 기존 승인된 확정 조건을 다시 검증하고 미입력 지원 수업이 남으면 해당 Trainer·월을 확정하지 않는다. 누락분 등록만으로 자동 확정하지 않는다. 현재 Rate/Fixed Amount/Base Salary 설정으로 과거 확정 지급이나 적용 기본급을 자동 재계산하지 않는다. 이번 결정은 후등록 순서와 이전 확정본 보존에 한정하며 이 후등록을 위한 확정 해제/재확정의 역할·관리 Scope/소속 기준 시점·본인 건/별도 승인 상세·해제 사유 정책은 관련 OPEN이다. 발생 시점 식별/월 경계·소급 기간·금액 상한/정밀도·기존 실적 수정/취소와 각 단계 실패/재시도·UoW·동시성/버전 표현은 별도 정책 또는 Architecture 설계 대상이다. 후등록 흐름 자체를 다시 미정으로 취급하지 않으며 BR-013 전체는 나머지 질문으로 OPEN을 유지한다.

2026-10-11 사용자 확정(지원 수업 외 실적 등록·누락 후등록의 이동 후 담당 관리자 질문의 1번 답변 및 재확인): 지원 수업 외 Additional Performance의 등록과, 확정된 발생 월의 누락분 반영을 위한 해당 Trainer·월 정산 확정 해제·재확정은 Master Admin에게 Organization 전체, Branch Admin에게 각 업무 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 등록·해제·재확정 요청마다 현재 소속과 관리 권한을 검증하고 최초 단계의 소속으로 후속 권한을 고정하지 않는다. 이전 소속·실적 발생 당시 소속·Performed Branch·클라이언트가 전달한 Branch Context만으로 권한을 부여하지 않는다. 9월 수원점 소속 때 발생한 회원 유지 실적을 10월 강남점 이동 후 처리하면 강남점 Branch Admin/Master가 담당하고, 별도 Master 권한 없는 이전 수원점 Branch Admin은 처리할 수 없다. 실적은 여전히 9월 정산·수원점 비용이며 이전 확정본과 감사 이력을 보존한다. 등록의 내용+양수 금액 필수·관리 범위 안 본인 등록·별도 승인 없음과 재확정의 기존 확정 조건/미입력 지원 수업 차단을 유지한다. 이 결정은 위 등록 및 누락분 후등록의 역할·관리 범위·소속 기준 시점에 한정한다. 누락분 반영을 위한 해제·재확정의 본인 건 처리/별도 승인·해제 사유 정책, 지원 수업 외 기존 실적의 정정/취소 권한·소속 기준 및 처리 절차는 별도 OPEN이다. 기존 지원 수업 보상/기본급 정정 권한이나 비용/조회 범위를 확대하지 않는다.

2026-10-11 사용자 확정(누락 실적 반영을 위한 정산 확정 해제 사유 질문의 1번 답변): 확정된 발생 월의 누락된 지원 수업 외 Additional Performance를 반영하기 위해 해당 Trainer·월 정산의 확정을 해제할 때 사유를 필수로 기록한다. Master Admin과 Branch Admin의 허용된 해제에 동일하게 적용하며 사유 없는 해제 요청은 거부한다. 거부 시 요청 직전의 확정 상태·확정본·기존 실적과 정산 구성/금액을 유지한다. 해제 성공 시 대상 Trainer·월, 해제 사유·처리자·처리 시점을 감사 가능한 이력으로 남기고 이전 확정본을 보존한다. 예를 들어 9월 회원 유지 실적 누락 반영을 사유로 식별할 수 있어야 한다. 각 처리 시점 현재 Home Branch 인가·해제 → 누락 등록 → 같은 월 재확정·발생 월 정산/발생 당시 Home Branch 비용 귀속과 재확정 조건을 유지한다. 이번 결정은 누락분 반영의 확정 해제 사유 필수에 한정하며 이 흐름의 해제/재확정 본인 건 처리·별도 승인 여부와 기존 실적 정정/취소 등 남은 정책은 별도 OPEN이다. 등록 사유/내용을 해제 사유로 자동 대체하거나 별도 승인 정책을 임의 확정하지 않는다.

2026-10-11 사용자 확정(Branch Admin의 본인이 아닌 소속 Trainer 누락 실적 반영 시 Master 승인 질문의 1번 답변): Branch Admin이 본인이 아닌 소속 Trainer의 확정된 발생 월 누락 실적(지원 수업 외 Additional Performance)을 반영할 때, 해당 Trainer·월 정산의 확정 해제·재확정에 별도 Master 승인을 두지 않는다. 각 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인지 검증한 후 Master 승인 대기 없이 직접 처리한다. 해제 사유 필수·사유 없는 요청 거부와 요청 직전 확정 상태/금액 보존, 해제 → 내용과 양수 금액을 갖춘 누락 실적 등록 → 같은 발생 월 재확정 순서, 이전 확정본·처리 이력/감사 보존을 유지한다. 재확정은 기존 확정 조건을 다시 검증하고 미입력 지원 수업이 남으면 해당 Trainer·월을 확정하지 않는다. 승인 생략은 자동 등록/재확정이나 관리 범위 밖 접근을 허용하지 않는다. 발생 월 정산·발생 당시 Home Branch 비용 귀속과 과거 지급/적용 기본급 보존은 유지한다. 이번 결정은 Branch Admin의 본인이 아닌 소속 Trainer 건에 한정하며 관리자 본인의 누락 실적 반영을 위한 해제/재확정 허용 및 해당 본인 건의 별도 승인 정책은 OPEN이다. 이미 승인된 관리 범위 안 본인 실적 등록·기존 지원 수업 보상/기본급 정정 정책은 변경하지 않는다. 기존 비지원 실적 정정/취소·나머지 수명/입력 정책과 구체 계약/UoW/동시성은 별도 결정 또는 설계 대상이다.

2026-10-11 사용자 확정(관리자·Trainer 겸임자의 본인 누락 실적 반영을 위한 확정 해제·재확정 질문의 1번 답변): 관리자·Trainer 겸임자는 관리 권한 범위 안에서 본인의 확정 월 누락 실적(지원 수업 외 Additional Performance)을 반영하기 위한 정산 확정 해제·재확정을 별도 승인 없이 직접 처리할 수 있다. Master Admin은 Organization 범위 안의 본인 건, Branch Admin은 각 처리 시점 본인 Trainer의 현재 Home Branch가 자신의 관리 Branch와 일치하는 경우 허용한다. Actor와 대상 Trainer가 동일인이어도 해제 사유 필수·사유 누락 거부/요청 직전 상태 보존·처리 이력과 감사·이전 확정본 보존은 동일하게 적용한다. Trainer 역할만으로는 본인 정산을 해제/재확정할 수 없으며 관리자 권한/Scope와 현재 소속을 요청마다 검증한다. 해제 → 내용과 양수 금액을 갖춘 누락 실적 등록 → 동일 발생 월 재확정 순서와 발생 당시 Home Branch 비용 귀속을 유지한다. 재확정은 기존 승인 조건을 다시 검증하고 미입력 지원 수업이 남으면 차단하며 본인 건/승인 생략을 이유로 자동 확정하거나 검증을 생략하지 않는다. 기존 비지원 실적 정정/취소·발생 시점/월 경계·소급 기간·나머지 금액 제약은 별도 OPEN이며 구체 계약/저장/단계별 UoW·실패/재시도·이동 경합은 PROPOSED다.

2026-10-11 사용자 확정(정산 확정 전 지원 수업 외 추가실적 금액 수정 권한 질문의 1번 답변): 월 정산 확정 전, 이미 등록한 회원 유지 등 지원 수업 외 Additional Performance의 금액 수정은 Master Admin에게 Organization 전체, Branch Admin에게 수정 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안 관리자·Trainer 겸임자의 본인 건도 포함하며 Master/다른 관리자의 별도 승인 없이 직접 수정한다. 모든 금액 수정에 변경 사유가 필수이고 변경 전후 금액·변경 사유·수정 Actor·처리 시점을 감사 가능한 이력으로 남긴다. 사유 없는 수정 요청은 거부하고 요청 직전 금액·기존 이력·정산 입력 상태를 유지한다. 현재 권한·관리 Scope·대상 Trainer의 현재 소속을 각 요청에서 검증하며 이전 소속/실적 발생 당시 소속·Performed Branch·위조 Branch Context/직접 ID만으로 권한을 부여하지 않는다. 관리자 권한 없는 Operator/Trainer는 본인 건도 수정할 수 없다. 실적 발생 월 정산·발생 당시 Home Branch 비용 귀속과 이전 이력을 유지하고 금액 수정만으로 PT 진행 사실/Pass 차감이나 과거 일반 지급·적용 기본급을 변경하지 않는다. 이번 결정은 확정 전 금액 수정의 역할·Scope·현재 소속 기준·본인 건·별도 승인 없음·사유/이력에 한정한다. 수정 금액의 0원/음수 허용·상한/정밀도, 금액 외 정보 수정·취소 및 확정된 월의 금액 정정/해제·재확정 상세는 별도 OPEN이며 기존 누락 실적 후등록 정책과 구분한다. 구체 입력/저장 계약·UoW·실패/재시도·소속 이동/정산 확정 경합은 PROPOSED다.

2026-10-11 사용자 확정(상황이 달라도 이전 선택지를 참고해 같은 답으로 진행하라는 지시): 유사 상황은 이전 사용자 선택을 참고해 같은 기준으로 진행하라는 지시에 따라, 지원 수업 외 Additional Performance의 최초 등록 금액 > 0 기준을 월 정산 확정 전 금액 수정에도 동일하게 적용한다. 수정 후 금액은 양수만 허용하고 0원·음수·금액 누락 요청은 거부하며 사유를 남겨도 0원 수정 예외를 두지 않는다. 거부 시 요청 직전 금액·이력·정산 입력 상태를 유지한다. 허용된 수정에도 기존 Master Organization/Branch Admin 수정 시점 현재 Home Branch 인가·관리 범위 안 본인 건 허용·별도 승인 없음·변경 사유 필수와 전후 금액/사유/수정자/시점 이력·감사를 적용한다. 발생 월 정산·발생 당시 Home Branch 비용 귀속과 과거 확정 지급/적용 기본급 보존을 유지한다. 지원 수업 보상의 사유 필수 0원 확정/수정과 월별 수동 적용 기본급의 사유 필수 0원 지정은 기존 승인 범위대로 유지한다. 금액 상한·정밀도/표현을 새로 정하거나 0원 덮어쓰기/음수 입력을 실적 취소 절차의 대체로 도입하지 않는다. 확정 후 금액 정정·금액 외 정보 수정/취소 등 남은 정책 및 구체 계약/저장/UoW·실패/재시도·동시성은 별도 결정 또는 설계 대상이다.

2026-10-11 사용자 일관성 지시 적용(기존 지원 수업 보상·기본급의 확정 월 금액 오류 처리 재사용): 유사 상황에 이전 선택을 적용하라는 사용자 지시에 따라 지원 수업 보상/기본급의 확정 월 금액 오류 정정 흐름을 지원 수업 외 Additional Performance에도 적용한다. 확정된 발생 월 실적의 금액 오류는 해당 Trainer·월 확정 해제 → 해당 실적 금액 정정 → 같은 발생 월 재확정으로 처리하고 이전 확정본과 당시 적용 구성/금액/합계·정정 전후 이력을 보존한다. Master Admin은 Organization 전체, Branch Admin은 각 해제/정정/재확정 처리 시점 대상 Trainer의 현재 Home Branch가 관리 Branch인 경우 허용한다. 관리 범위 안 관리자·Trainer 겸임자의 본인 건도 포함하고 별도 Master/다른 관리자 승인 대기를 두지 않는다. 해제와 금액 정정 모두 사유가 필수이며 사유 없는 각 요청은 요청 직전 상태·금액·확정본/이력을 유지하고 거부한다. 해제 사유/처리자/시점과 정정 전후 금액/사유/수정자/시점을 감사 가능한 이력으로 남긴다. 정정 금액도 기존 등록/확정 전 수정과 동일하게 양수만 허용하며 0원·음수·금액 누락 요청은 사유가 있어도 거부한다. 재확정은 기존 승인 조건을 다시 검증하고 금액 미입력 지원 수업이 남으면 해당 Trainer·월을 확정하지 않는다. 정정 저장만으로 자동 재확정하지 않으며 현재 Rate/Fixed Amount/Base Salary로 과거 일반 지급/적용 기본급을 재계산하지 않는다. 실적의 발생 월 정산과 발생 당시 Home Branch 비용 귀속을 유지하고 다른 월/Trainer나 PT 진행 사실·Pass를 변경하지 않는다. 예를 들어 다른 구성 금액이 같고 기존 실적 100,000원을 120,000원으로 정정하면 이전 9월 확정 합계 3,850,000원을 보존하며 새 9월 합계는 3,870,000원이다. 금액 외 정보 수정·실적 취소·발생 시점 식별/월 경계·소급 기간·나머지 금액 제약은 별도 OPEN이다. 각 단계 계약/저장/버전·UoW·실패/재시도·이동/정산 경합은 PROPOSED이며 전체 흐름을 임의의 단일 commit으로 정하지 않는다.

2026-10-11 사용자 명확화: 회원 유지는 기존 추가실적의 지급 사유로 다루며 별도 보상 제도의 설계 질문으로 분리하지 않는다. 관리자 직접 건별 등록·월 정산 반영 정책을 유지한다. 이번 답변은 발생일 또는 월 단위 실적 중 하나를 선택한 것이 아니며, 발생 시점 식별/월 경계·소급 등록 등의 잔여 질문은 OPEN이다.

2026-10-11 사용자 확정(보상 범위 질문의 1번): 일반 PT 수당의 자동 계산·확정과 기본급의 별도 반영을 유지하고, 그 외 모든 보상은 관리자가 기존 추가실적에 직접 입력한다. 지급 사유별 별도 제도는 설계하지 않는다. 이 범위는 해결됐으며 나머지 입력/날짜·정정/취소 및 연계 상세가 남아 BR-013은 OPEN을 유지한다.

2026-10-11 사용자 확정: 허용된 PT 진행 기록 취소는 그 수업 보상의 추가실적 자동 무효 처리를 동반한다. 유효 월 정산/지점 비용에서 제외하되 기존 금액·이력을 보존하고 다른 추가실적은 유지한다. 기존 기록 취소 권한과 Home Branch 기준 금액 입력/전체 정산 권한은 구별하며 확정 월의 기존 해제 → 취소 → 같은 월 재확정 순서를 따른다. 상세 근거는 BR-PAY-015/PD-027. 나머지 정정/취소·복원 예외 및 계약/원자성/동시성은 후속 대상이다.

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

2026-10-12 H 일괄 승인 반영: H2/H3=1: 비지원 실적 내용 수정/취소는 Master Organization/Branch Admin 각 처리 시점 대상 Trainer 현재 Home Branch 범위·본인 포함/별도 승인 없음·사유/이력/감사다(BR-PAY-019). 대상 Trainer/실제 발생 날짜 오류는 원본 취소 후 재등록/연결, 영향받는 각 확정 Trainer/월은 기존 해제/처리/재확정/이전본 보존을 적용한다. 원래 대상과 새 대상의 현재 인가를 구분하고 지원 수업 보상 연결을 임의 변경하지 않는다. 금액/발생·소속 사실/소급 기간·필드/연결·단계별 실패/계약은 후속이다. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch). 이 복합 OPEN의 남은 항목은 유지한다.

<a id="mb-009"></a>
## MB-009. 타 지점 수업 보상 구성 — 해결됨

Question: 타 지점 수업 보상은 일반 Session 수당에 추가되는 인센티브인가, 아니면 해당 수업에 대한 보상 전체를 추가실적으로 처리하는가?

Status: CLOSED

Resolution / approval source: 2026-10-10 사용자가 앞선 1번 답변을 정정하여 “일반 PT 수당 대신, 해당 수업의 보상 전체를 추가실적으로 처리한다”고 명시했다. 이 정정 답변이 앞선 일반 수당+추가 인센티브 결정을 대체한다. 타 지점 수업의 보상 전체를 Additional Performance로 반영하고, 동일 수업의 일반 Session Payment를 정산에 별도로 더하지 않는다.

Related decisions / requirements: PD-009/012/027; PR-008/010/031; BR-PAY-015/016.

Required timing: 타 지점 Session 보상 상세 설계·구현 전 구성 결정 완료. 관련 교차 업무 권한·추가실적 상세·정산 귀속 게이트는 별도로 확인한다.

확정된 경계: 실제 수업 이력·Pass 차감·감사와 정산의 일관성, 과거 확정 결과 보존을 유지한다. 보상 분류 결정만으로 일반 Session Payment를 0원으로 저장하는 모델이나 추가실적 금액·자동 생성·확정 시점을 정하지 않는다. 후속 BR-013 사용자 결정으로 타 지점 지원 수업은 금액 없이도 진행 기록·Pass 차감을 먼저 완료하고 권한 있는 관리자의 건별 수동 금액 저장 시 보상을 확정한다. 미입력은 확정 0원과 구분하고 추적한다. 일반 RATE/FIXED_AMOUNT 수당을 자동 계산해 추가실적으로 옮기는 방식을 적용하지 않는다. 다른 추가실적 산정·미입력 건의 추적 표현·정정 연동·연계 상세·나머지 정정/취소는 BR-013, 업무 접근은 MB-001/002/003/005, 귀속과 공개는 MB-010/006 OPEN이다.

확인 주체: 사용자. 보상 구성 정정 답변 완료(2026-10-10).

<a id="mb-010"></a>
## MB-010. 지점 이동·교차 수업의 정산 귀속

Question / TODO: 비용 구성/귀속의 확정본 버전·과거 Home 오류 보고 정정/영향 식별·완료 증거·월말/발생 당시 Home 확인 불가/충돌, 보고서 최소 Trainer 식별/응답·월 대상 사실/선정 검증/미완료 식별·동시 조회 계약을 구체화한다. Z1로 지점별 합계/네 항목 소계와 Trainer별 해당 지점 기여 금액 조회가 해결됐다. Y1/Y2 종료 월/미완료 영향 없는 최신 유효 확정본만 합산·미확정/해제 중/소속 오류 정정 대기 제외/표시를 상세에도 적용한다. 기존 일반/지원 실제 Performed·기본급 월말 Home 한 번·기타 실적 발생 당시 Home 귀속/한 번 합산과 V1/W1/W2 명시적 정정·정정 완료 후 확정·원본 자동 변경 금지/현재 권한·사유·해제/정정/같은 월 재확정·이전본 보존은 유지한다. 확인 불가를 현재 값/임의 지점·0원으로 대체하지 않는다. AB1/AB2 자동 대상/비활성 무지급 월 예외는 해결됐으며 사실 조회/검증 계약은 후속이다.

Status: OPEN

Related decisions / requirements: PD-004/012/027; PR-010/030; MB-001/006.

Required timing: 지점별 정산 집계·비용 귀속·공개 상세 설계/구현 확정 전.

확정된 경계: Home Branch·Performed Branch·비용 귀속 Branch는 구분한다. 일반 Session Payment·지원 수업 보상은 각각 실제 Performed Branch, 이동월 기본급은 대상 월말 Home Branch 한 곳에 적용액 전액, 지원 수업 외 추가실적은 발생 당시 Home Branch에 비용을 귀속한다(2026-10-11 사용자 확정). Trainer 월 정산의 기존 지급액·한 번 합산·과거 결과 보존·관리 권한은 유지하고 이후 소속 변경만으로 과거 비용 지점을 바꾸지 않는다. Trainer 일반 이동의 Master 전용/저장 후 반영은 BR-OPS-013을 따르고 대상 조건/과거 소속 이력 정정은 MB-001과 연결한다.

2026-10-11 정산 공개 결정과의 구분: 현재 자기 Branch 소속 Trainer의 해당 월 정산 전체 금액·구성 내역은 타 지점 지원 수업 보상까지 공개한다(조회 시점 현재 Home Branch 기준, 2026-10-11 사용자 확정). 이 공개 범위는 지점별 비용을 어느 Branch에 귀속할지 정한 결정이 아니다. 당시 미정이었던 타 지점 지원 수업 보상의 비용 집계 귀속은 아래 후속 사용자 결정으로 확정했다. 당시 미정이었던 이동월 기본급 비용은 아래 후속 결정으로 대상 월말 Home Branch 한 곳에 전액 귀속하도록 확정했다. 당시 미정이었던 일반 지급의 비용 귀속은 아래 후속 결정으로 실제 Performed Branch 기준 집계로 확정했다. 당시 미정이었던 지원 수업 외 추가실적 비용은 아래 후속 결정으로 실적 발생 당시 Home Branch 귀속으로 확정했다. 기본급/추가실적 귀속의 남은 예외와 비용 보고 공개/집계 상세 등은 계속 OPEN이다.

2026-10-11 사용자 확정(타 지점 지원 수업 보상의 비용 집계 지점 질문의 1번, 복잡도와 적용 범위 설명 후 최종 확인): 타 지점 지원 수업의 전체 보상으로 확정한 Additional Performance 금액은 해당 수업의 실제 Performed Branch 비용으로 집계한다. Trainer 월 정산에는 한 번만 반영하고 기존 입력·정정·확정·조회 권한은 유지한다. 비용 귀속으로 지원받은 지점 관리자에게 다른 소속 Trainer의 설정/전체 정산 열람이나 금액 입력 권한이 생기지 않는다. 소속 이동만으로 과거 지원 수업의 비용 지점을 바꾸지 않는다. 지원 수업 보상의 집계 기준 확정이며 다른 보상 항목 귀속·보고 공개/집계 상세·지점 간 청구/송금·기본급 자동 배분으로 확대하지 않는다. BR-PAY-015/016 및 PR-031/010을 따르며 MB-010 전체는 잔여 질문으로 OPEN이다.

2026-10-11 사용자 확정(월중 지점 이동 시 기본급 비용 귀속 질문의 1번 답변): 월중 Trainer 지점 이동이 있는 달의 해당 월 적용 기본급 비용은 대상 월의 월말 Home Branch 한 곳에 전액 귀속한다. 수동 지정이 있으면 해당 월 적용액 전액을 사용하며 지급액·지점별 분할/일할 계산·기존 관리 권한은 바꾸지 않는다. 이후 소속 이동만으로 과거 월의 비용 지점을 바꾸지 않는다. 수업 보상의 수행 지점 기준과 기본급의 대상 월말 Home Branch 기준은 별도 규칙이다. 월말 소속을 식별할 수 없는 경우 등 예외와 나머지 비용 귀속·보고 공개/집계 상세가 남으므로 MB-010 전체는 OPEN이다. BR-PAY-014/016 및 PR-010에 추적한다.

2026-10-11 사용자 확정(이동 전후 일반 PT 수당의 비용 귀속 질문의 1번 답변): 일반 Session Payment는 해당 PT 진행 기록의 실제 Performed Branch 비용으로 집계한다. 이미 확정된 수업별 지급액을 지점별로 합산하며 대상 월말 Home Branch로 전액을 모으지 않는다. 수원 수업 200,000원·강남 수업 300,000원의 지점별 비용과 Trainer 일반 수당 합계 500,000원을 함께 대사한다. 지급액·과거 불변성·지원 수업 일반 지급 중복 합산 금지·이동월 기본급 월말 소속 전액 귀속·기존 권한은 유지한다. 이후 소속 이동만으로 과거 수행 지점에 따른 비용 귀속을 바꾸지 않는다. 비용 기준 확정이 일반 지급/진행 기록 정정·취소 절차나 보고 공개/집계 상세의 승인은 아니다. 나머지 질문으로 MB-010 전체는 OPEN이다. BR-PAY-009/016 및 PR-010에 추적한다.

2026-10-11 사용자 확정(회원 유지 등 지원 수업 외 추가실적의 비용 귀속 질문의 1번 답변): 지원 수업 외 Additional Performance의 비용은 실적 발생 당시 대상 Trainer의 Home Branch에 귀속한다. 등록 시점·금액 확정 시점·대상 월말 또는 조회 시점의 소속으로 대체하지 않는다. 수원 소속일 때 발생한 회원 유지 실적 보상 100,000원은 월말 강남 이동 후에도 수원점 비용이다. 금액·월 정산 한 번 합산·기존 관리 권한은 유지하며 비용 귀속을 등록/정정 권한으로 자동 상속하지 않는다. 발생 시점/당시 소속을 식별할 수 없는 상황과 정산 월·정정/취소·비용 보고 공개/집계 상세는 관련 OPEN이다. BR-PAY-015/016 및 PR-031/010에 추적하며 MB-010 전체는 잔여 질문으로 OPEN이다.

2026-10-11 사용자 확정(지점별 비용 보고서 조회 권한 질문의 1번 답변): v1 지점별 비용 보고서는 Master Admin만 Organization 범위에서 조회한다(2026-10-11 사용자 확정). Branch Admin은 자기 지점 비용 합계도 이 보고서로 조회할 수 없으며 Master 권한 없는 Operator·Trainer도 불가하다. Branch Admin의 현재 자기 Home Branch 소속 Trainer 해당 월 정산 전체 금액·구성 내역 조회는 타 지점 지원 보상까지 포함하여 유지한다. 비용 귀속·지급액·기존 등록/정정/확정 권한은 유지하며 보고서 항목·대상 월·집계/완전성·버전 등 남은 상세는 MB-006/010 OPEN이다. 비용 지점에 따른 Branch Admin의 보고서 권한은 없으며 MB-010 전체는 잔여 질문으로 OPEN을 유지한다.

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

Trainer Home Branch 일반 변경의 Actor는 Master Organization 범위 전용으로 후속 승인됐다(2026-10-12, BR-OPS-013). 기존 저장 후 현재 소속 인가/실패 보존·감사 원칙을 적용하며 계정 역할/관리·Operator Scope·담당/지원 관계와 기존 수업 당시 소속/지급·정산/비용 귀속 규칙은 유지한다. 이동 대상 상태/절차·과거 소속 이력 정정/소급/확인 불가 및 상세 계약·동시성은 후속이며 이 OPEN 전체를 해결한 것은 아니다.

2026-10-12 C 일괄 승인 반영: C9/C10: 실제 시작 시점의 Asia/Seoul 업무 일자/월 기준과 Member/수행 Trainer 정정의 취소·재등록을 적용한다. 기존 일반/지원 보상 구분과 비용 귀속은 유지한다. 대상 Trainer/월이 바뀌어도 영향받는 각 확정본을 직접 덮어쓰지 않으며 각 해제/재확정 권한·순서/경합 상세는 후속이다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 H 일괄 승인 반영: H3=1: 비지원 실적의 잘못된 Trainer/실제 발생 날짜는 취소 후 재등록/연결로 정정하며 새 실제 발생 월·당시 Home Branch 비용 귀속을 따른다. 원본 귀속/취소 및 각 확정본은 보존하고 유효 합산만 정정한다. 역사 사실 확인 불가·다른 Trainer/월 계약·보고서 상세는 후속이다. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch). 이 복합 OPEN의 남은 항목은 유지한다.

2026-10-13 N1/N2=1: 비관리자 Trainer 본인 PT 내역의 수업별 금액과 현재 다른 Home Branch Trainer의 자기 지점 수업 금액은 Performed Branch Admin에게 공개하지 않는다. 일반 지급/수업 연결 지원 보상 모두 적용하고 기존 PT 기록 조회/정정과 금액 열람을 분리한다. 현재 Home 기반 기존 관리자 보상·정산 업무·Master Organization/겸임 독립 Scope, CompSetting/월 정산/지점 비용 보고 제한을 유지한다. 등록/중첩/직접 ID·제공되는 집계/감사/오류 등 Backend 우회 노출을 막고 비공개를 가짜 0원/원본 삭제/재계산으로 표현하지 않는다. 다른 공개 필드/상태·계산 근거/최소 응답/인가·현재 권한/소속 변경 경합은 후속으로 이 복합 OPEN은 유지한다. BR-PAY-021, PR-008/029/030, NFR-001/005; V-108/109 예정; [N 승인](product-decisions.md#review-20261013-n-batch).

2026-10-13 V1=1 부분 해결: Trainer/Member의 이미 기록된 과거 Home 이력 오류는 Master 자기 Organization 전용/사유 필수·원래 이력/감사 보존으로 정정한다. 일반 이동의 즉시 적용/미래 예약 미지원은 유지하고 기존 PT/지급·정산 확정본을 자동 덮어쓰지 않는다. 영향 건은 기존 업무별 권한/정정·필요한 월 확정 해제/동일 월 재확정·이전본 보존을 따른다. 구체 역사 사실/현재 Home 영향·분류가 바뀌는 수업 정정/지급 기준·비용 보고/최소 계약은 남아 Status는 OPEN이다. [V 승인](product-decisions.md#review-20261013-v-batch); BR-OPS-032; V-123 미구성·미실행.

2026-10-13 W1/W2=1 부분 해결: 과거 Trainer Home 오류에 따른 일반/지원 전환은 Master Organization 전용 명시적 정정으로 같은 PT/기존 Pass 차감·최초 생성 시각을 유지한다. 일반은 최초 기록 생성 시점 설정/소비 Pass 발급 조건, 지원은 기존 관리자 범위 수동 추가실적이다. 이전 결과 이력/유효 합계 단일 반영을 보존하고 영향 건 분류/보상·비용 정정 완료 전 해당 Trainer·월 확정/재확정을 차단한다. 소속 정정만으로 기존 확정본 자동 해제/변경 없음·기존 권한/사유·필요한 월 해제/명시적 정정/동일 월 재확정·이전본 보존을 유지한다. 역사 사실·영향/완료 증거·나머지 상태/최소 계약/경합이 남아 OPEN을 유지한다. [W 승인](product-decisions.md#review-20261013-w-batch); BR-OPS-033/PAY-024; V-124/125 미구성·미실행.

2026-10-13 Y1/Y2=1 부분 해결: Master 전용 지점 비용 보고서는 한국 시간 기준 종료된 월만 조회하고 각 Trainer·월의 미완료 영향 없는 현재 유효 최신 확정본만 합산한다. 미확정/확정 해제 중/과거 Home 오류 영향 정정 대기 Trainer월은 합계 제외/미완료 현황 표시하며 전체 월 비용 완성이나 0원으로 취급하지 않는다. 기존 당월 Trainer 월 정산 조회/비용 귀속·과거 확정본 보존/자동 변경 금지·권한/사유·해제/정정/재확정은 유지한다. 상세 보고 항목/월 대상 집합·미완료 식별/역사 사실·비용 버전/최소 계약·동시 조회 때문에 OPEN을 유지한다. [Y 승인](product-decisions.md#review-20261013-y-batch); BR-PAY-025; V-127/128 미구성·미실행.

2026-10-13 Z1=1 부분 해결: Master 자기 Organization 전용 지점 비용 보고서의 지점별 합계/기본급·일반 PT 수당·지원 수업 보상·기타 추가실적 소계와 해당 지점 비용에 기여한 Trainer별 항목/금액 상세를 제공한다. 기존 귀속/한 번 합산과 Y1/Y2 종료 월/미완료 영향 없는 최신 유효 확정본·미완료 제외/표시를 상세/집계에 함께 적용한다. Trainer 월 전체 지급액을 각 지점에 복제하지 않고 현재 설정/소속으로 과거 비용을 다시 계산하지 않는다. 최소 식별/응답·월 대상/미완료·역사 비용/버전·동시 조회 계약이 남아 OPEN을 유지한다. [Z 승인](product-decisions.md#review-20261013-z-batch); BR-PAY-025; V-129 미구성·미실행.

2026-10-13 AB1/AB2=1 부분 해결: 설정/유효 수업·지원 보상대기/추가실적 기반 월 대상 자동 선정과 확인된 월전체 Trainer 비활성·명시 기본급0·무활동·미완료없음의 새 확정 의무 제외를 적용한다. 기존 이력/미완료·현재 Home 인가/확정·비용 보고 조건을 유지하고 현재상태/기존정산행만으로 누락·자동0/자동확정을 하지 않는다. 대상/역사 사실·조건 증거·최소 계약/경합이 남아 OPEN이다. [AB 승인](product-decisions.md#review-20261013-ab-batch); BR-PAY-026; V-132/133 미구성·미실행.

## 2026-09-17 개정 당시의 CLOSED 처리 — 이력

기존 복합 질문 MB-001/002/003/004/007 및 BR-009는 해결된 부분을 각 `확정된 경계`에 CLOSED로 분리했다. 남은 질문이 있어 ID 전체는 OPEN을 유지한다. 기존 BR-003/004/005/006 CLOSED도 유지하며 이번에 전체가 새로 CLOSED된 기존 OPEN ID는 없다. 보상 설정 권한·승인 불필요·감사는 PD-001/009/022의 CLOSED 결정을 갱신했다. 추가실적 도입은 PD-027 CLOSED이며 상세 권한·보상 구성은 OPEN이다.

## 2026-10-10 후속 결정

ARCH-001의 관리자/Trainer 한 계정 겸임 및 관리 범위 안에서의 본인 보상 설정 접근, ARCH-002의 일회용 링크를 통한 최초 비밀번호 설정은 부분 해결이다. MB-009는 해당 수업의 보상 전체를 Additional Performance로 처리하는 방식으로 CLOSED 처리했다. 같은 날 BR-011은 기존 Pass의 발급 당시 상품 가격·총횟수·Payment Type 유지로 CLOSED 처리했다. 상품 변경은 새 Pass부터 적용한다. Trainer Rate/Fixed Amount 적용 시점은 기존 결정을 유지한다. 기본급 적용 시작 월의 관리자 지정·미확정 과거 월 지정 허용·수동 지정 없는 기존 미확정 정산 자동 반영으로 부분 해결했고 확정된 월의 기본급 오류는 해당 월 확정 해제·기본급 정정·재확정과 이전 확정본 보존으로 부분 해결했다. 해당 기본급 정정도 Master Organization 전체/Branch Admin 처리 시점 Trainer 현재 Home Branch 기준으로 별도 Master 승인 없이 처리하도록 확정했다. 해당 기본급 정정의 확정 해제·해당 월 기본급 수정 모두 사유 필수로 확정했다. 기본급 오류 정정은 해당 월 정산에만 적용하고 현재·미래 기본급 설정과 다른 월 정산은 유지하도록 확정했다. 입사·퇴사·휴직 월의 기본급은 관리자가 해당 월 금액을 수동 지정하고 설정과 다른 월은 유지하도록 확정했다. 일반 기본급 설정이 나중에 변경되어도 월별 수동 지정 금액은 유지하고 수동 지정 없는 미확정 월에만 자동 반영하도록 확정했다. 미확정 월의 최초 기본급 수동 지정·수정 모두 사유 필수로 확정했으며 사유 누락 요청은 상태/금액/합계 변경 없이 거부하고 지정/수정 이력을 남긴다. 미확정 월의 수동 지정·수정도 Master Organization 전체/Branch Admin 처리 시점 Trainer 현재 Home Branch 기준으로 관리 범위 안 본인 포함·별도 Master 승인 없이 직접 허용하도록 확정했다. 2026-10-11에는 월별 수동 기본급을 사유 필수로 0원 지정할 수 있도록 확정했다. 명시적 0원은 미입력과 구분하고 기존 권한/감사/확정 조건을 유지한다. BR-012/010의 미리 등록할 수 있는 미래 적용 시작 월 범위와 나머지 금액 입력 제약은 남았다. BR-013·BR-012·MB-010/006 등 나머지 질문의 상태와 AS-IS 검증 상태는 변경하지 않았다.

같은 날 BR-013의 관리자 직접 등록 역할은 Master Admin과 Branch Admin 모두 허용으로 부분 해결했다. 이어 대상 범위는 Master가 Organization 전체, Branch Admin이 자기 Branch를 Home Branch로 가진 Trainer만 등록하는 2번으로 확정했다. Branch Admin이 본인이 아닌 소속 Trainer에게 직접 등록할 때는 별도 Master 승인 없음으로 확정했다. 관리자·Trainer 겸임자도 관리 범위 안이면 본인에게 직접 등록하는 2번을 추가 확정했다. 본인 건도 별도 승인 없음으로 추가 확정했다. 타 지점 지원 수업 금액은 관리자 건별 수동 입력의 3번으로 추가 확정했다. 이후 시점 질문의 1번 답변으로 진행 기록·차감을 먼저 완료하고 관리자 금액 저장 시 보상을 확정하며 미입력을 확정 0원과 구분·추적하도록 확정했다. 이어 미입력 월 정산 질문의 1번 답변으로 미입력 지원 수업이 남은 해당 Trainer·월 정산 확정을 차단하도록 확정했다. 이후 0원 질문의 2번 답변으로 지원 수업은 사유를 기록하면 0원 확정 가능하며 명시적 0원 확정 건은 미입력 차단에서 제외하도록 확정했다. 이어 수정 권한 질문의 1번 답변으로 월 정산 확정 전 지원 수업 금액 수정에 동일한 관리자 대상 범위·관리 범위 안 본인 건 허용·변경 이력을 확정했다. 이후 수정 승인 질문의 1번 답변으로 Master·Branch Admin의 관리 범위 안 수정은 본인 건 포함 별도 승인 없이 저장 즉시 반영하도록 확정했다. 이후 변경 사유 질문의 1번 답변으로 월 정산 확정 전 지원 수업 금액의 모든 수정에 변경 사유 필수와 변경 전후 금액·사유·수정자·시점의 이력을 확정했다. 이후 확정 후 오류 처리 질문의 2번 답변으로 지원 수업 보상 금액 오류는 해당 Trainer·월의 확정 해제 → 금액 정정 → 해당 월 재확정으로 처리하고 이전 확정본을 보존하도록 확정했다. 이어 해제·재확정 권한 질문의 2번 답변으로 지원 수업 보상 정정은 Master의 Organization 전체·Branch Admin의 대상 Trainer Home Branch 범위에서 월 정산 확정 해제·재확정을 허용하도록 확정했다. 이어 별도 승인 질문의 1번 답변으로 위 Branch Admin의 지원 수업 보상 정정에 월 정산 확정 해제·재확정의 별도 Master 승인 없음과 기존 범위·이력·감사를 유지하도록 확정했다. 이어 해제 사유 질문의 1번 답변으로 지원 수업 보상 정정을 위한 월 정산 확정 해제는 사유를 필수 기록하고 사유 없이는 해제할 수 없도록 확정했다. 이어 이동 후 권한 기준 질문의 1번 답변으로 과거 지원 수업 보상 정정과 해당 월 정산의 확정 해제/재확정은 처리 시점의 Trainer 현재 Home Branch 기준으로 확정했다. 이전 소속만으로 권한을 유지하지 않으며 Master Organization 범위와 과거 기록/확정본 보존을 유지한다. 나머지 정정/취소는 미정이다. 지원 수업 외 실적의 금액 외 정보 수정/취소의 소속 이동 시 권한 기준 시점·다른 추가실적 산정·미입력 건의 추적 표현·정정 연동·연계 상세·정정 등은 남아 있으며 24 OPEN / 6 CLOSED와 다른 결정의 상태는 유지한다.

2026-10-12 후속 결정: Organization 공통 PT 상품 생성·수정은 Master Admin만 허용하도록 MB-007을 CLOSED 처리했다. 현재 Product OPEN은 23 OPEN / 7 CLOSED다. 다른 OPEN/승인된 Product 규칙과 ADR/Architecture의 PROPOSED 상태는 유지한다. 앞선 날짜의 OPEN/CLOSED 수치는 당시 기록이다.

2026-10-12 I 승인 후 상태: UX-001은 v1 개별 등록/여러 날짜 일괄 입력 보류 승인으로 CLOSED가 됐다. 현재 Product OPEN은 22 OPEN / 8 CLOSED다. 앞선 날짜의 수치는 당시 이력이며 나머지 ID 상태/PD 1 OPEN·26 CLOSED/ADR/Architecture 상태는 유지한다. [2026-10-12 I 일괄 승인](product-decisions.md#review-20261012-i-batch).
