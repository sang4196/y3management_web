# Open Questions / 후속 TODO

승인된 Product Decision을 다시 OPEN으로 돌리지 않고 남은 세부사항을 분리한 목록이다. BR-003/004/005/006은 CLOSED이며 남은 질문은 26개 OPEN이다(기존 22개 유지, BR-012/013 및 MB-009/010 추가). 복합 질문의 해결된 부분과 남은 부분을 분리한다. 공통 제약을 바탕으로 Architecture 검토는 가능하지만 신규 Branch 관련 상세 설계 확정에는 사용자 결정이 필요하다. 남은 업무 질문은 해당 상세 설계·구현 확정 전, 운영 질문은 실운영 전에 확인한다. [Architecture 인계](architecture-handoff.md). 이 문서는 질문과 검토 시점만 정하며 Architecture·데이터 구조·기술을 설계하지 않는다. BR은 미래 업무 규칙, ARCH는 후속 설계 질문, UX는 입력 편의, OPS는 운영 전환, LEGAL은 별도 개인정보·보존 검토다. 현재 사실 확인 VAL과 구분한다.

<a id="br-001"></a>
## BR-001. PT Pass 상태·시작·종료 규칙

Question / TODO: Pass 생성/시작 정보의 의미, 허용 상태와 전이, 종료 조건, 미사용 횟수가 있는 종료·중단 및 재개를 어떻게 다룰까?

Related decisions / requirements: PD-007/011; PR-003. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Architecture 착수 가능; 관련 업무 상세 설계·구현 확정 전

확정된 경계: 상태명·자동 만료·종료 시 잔여 소멸을 이 문서에서 결정하지 않는다. 종료 Pass 이력 보존은 승인됨.

Status: OPEN

확인 주체: 사용자/업무 책임자와 해당 후속 단계 담당자. 답변·기한은 미정.

<a id="br-002"></a>
## BR-002. Pass 횟수 부여·차감·조정

Question / TODO: 최초 횟수 부여·추가·조정·취소 복원, 잔여 부족·사용 가능 조건은?

Related decisions / requirements: PD-007/008/010; PR-003/008/009. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Architecture 착수 가능; 관련 업무 상세 설계·구현 확정 전

확정된 경계: BR-PAY-006에 따라 동시에 사용 가능한 FIXED_AMOUNT Pass를 RATE Pass보다 먼저 차감한다. 동일 Payment Type에서는 FIFO이며 이 순서와 1회 Session 단위는 확정이다. 따라서 기존 일반 우선 차감은 계승하지 않는다.

Status: OPEN

확인 주체: 사용자/업무 책임자와 해당 후속 단계 담당자. 답변·기한은 미정.

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

Resolution: 권한 있는 관리자 저장 완료 이후 새로 등록되는 Session부터 새 Rate/Fixed Amount를 적용한다. 정상 Session 등록 시 지급액 계산·확정, 과거 확정 결과 재계산 금지. 월 정산의 Session 구성은 유효 확정 결과 집계다. 기본급 적용 월은 BR-012, Product 변경은 BR-011, 타 지점 보상 구성은 MB-009로 별도 추적하며 이 CLOSED를 확대 해석하지 않는다. 보존 구현은 Architecture 결정이다.

<a id="br-007"></a>
## BR-007. Session 정정·취소와 정산 반영

Question / TODO: 허용 정정 항목·기간·사유, 종료 Pass·비활성 회원·잔여0 사례, 잔여 복원과 월 정산 재반영, 이미 확인한 정산의 후속 정정은?

Related decisions / requirements: PD-010/011/012; PR-009/010. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Architecture 착수 가능; 정정 상세 설계·구현 확정 전 업무 기대 결과 확인

확정된 경계: 제한된 권한의 운영자가 수행하며 Trainer 본인 정정/취소 허용 여부는 MB-005에서 확인한다.  Pass 잔여·정산 일관성과 이력 보존은 승인됨. 월 정산 확인·마감/확정 절차는 BR-009 OPEN이다. 확정된 과거 정산의 자동 변경 금지는 승인되었으나 구체 확정 절차를 승인한 것은 아니다. 정정/취소의 상세를 정하더라도 Trainer 설정 변경을 이유로 과거 확정 지급액을 현재 Rate/Fixed Amount로 재계산할 수는 없다(BR-PAY-009).

Status: OPEN

확인 주체: 사용자/업무 책임자와 해당 후속 단계 담당자. 답변·기한은 미정.

<a id="br-008"></a>
## BR-008. 진행일·동일 일자 중복·월 경계

Question / TODO: 실제 진행 날짜의 기준 시간대, 동일 날짜 복수 Session 판단, 소급 날짜 허용 범위 및 월 경계는?

Related decisions / requirements: PD-008/012; PR-008/010. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Architecture 착수 가능; 관련 업무 상세 설계·구현 확정 전

확정된 경계: 같은 날이면 무조건 중복이라는 규칙은 없다. 월 단위 집계 원본 저장은 승인 범위 밖이다.

Status: OPEN

확인 주체: 사용자/업무 책임자와 해당 후속 단계 담당자. 답변·기한은 미정.

<a id="arch-001"></a>
## ARCH-001. Role/Permission 상세

Question / TODO: Role과 Data Scope를 구분하는 기술 모델, Master Admin/Branch Admin/Operator/Trainer의 세부 Permission, 제한된 Session 정정 권한을 상세화한다. Branch 관계 정책은 MB-001–008의 Product 결정에 의존한다. 설정 값 조회 금지를 준수하는 정산·감사 정보 열람 범위도 확인한다.

Related decisions / requirements: PD-001/010/022; PR-001/021/027. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Architecture의 Authentication/Authorization 설계 중 검토; 미정인 정정·감사 열람 범위는 관련 상세 권한 확정 전 Product 확인

확정된 경계: Rate / Fixed Amount / Base Salary 세 항목의 조회·설정·변경은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 단일 Branch를 Home Branch로 가진 Trainer에게만 허용한다. Operator와 Trainer는 본인 설정을 포함하여 모두 불가하다. 타 지점 지원 수업은 보상 설정 접근 권한을 부여하지 않는다. Backend에서 대상 Trainer의 Home Branch를 검증하며 직접 ID 요청과 감사·정산 등 우회 경로에도 제한을 적용한다. 모든 보상 설정 변경(최초 설정 포함)에 대상 Trainer, 변경 항목, 변경 전 값, 변경 후 값, 변경 Actor, Actor의 권한 및 Branch Context, 변경 시점을 추적한다. 별도 Master Admin 승인 없이 변경 가능하며 변경 요청→승인 대기→승인→반영 절차를 추가하지 않는다. 이 결정은 추가실적 승인이나 월 정산 마감/확정 절차를 면제하지 않는다. 세부 기술 모델과 감사 조회 구현은 Architecture에서 결정하며 미정 업무 열람 범위는 사용자 결정이 필요하다.

Status: OPEN

확인 주체: 사용자/업무 책임자와 해당 후속 단계 담당자. 답변·기한은 미정.

<a id="arch-002"></a>
## ARCH-002. 계정 수명 정책

Question / TODO: 초기 Master Admin 생성, 관리자 발급 이후 비밀번호 설정/재설정, 계정 중단, 마지막 Master Admin 보호, 접근 종료/만료를 상세화한다.

Related decisions / requirements: PD-019; PR-001/021/026/028. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Authentication/Authorization 설계

확정된 경계: 기존 계정/암호 이관과 기본 고정 자격증명은 요구하지 않는다. 인증 기술 선택은 이번 작업 아님.

Status: OPEN

확인 주체: 사용자/업무 책임자와 해당 후속 단계 담당자. 답변·기한은 미정.

<a id="arch-003"></a>
## ARCH-003. 복수 사용 가능 Pass의 상세 경계

Question / TODO: 복수 사용 가능한 Pass 지원을 전제로 사용 가능 상태/조건과 수량 상한 등 필요한 경계를 정의한다. 같은 Payment Type 내 FIFO는 확정이며 재검토하지 않는다.

Related decisions / requirements: PD-007; PR-003. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Architecture/domain modeling

확정된 경계: BR-PAY-006의 FIXED_AMOUNT 2회 + RATE 10회 사례와 FIXED → FIXED → RATE를 지원한다. 복수 Pass 허용 여부를 다시 미정으로 두지 않는다.

Status: OPEN

확인 주체: 사용자/업무 책임자와 해당 후속 단계 담당자. 답변·기한은 미정.

<a id="arch-004"></a>
## ARCH-004. 브라우저·운영 품질 상세

Question / TODO: Desktop/Tablet/Smartphone의 브라우저 지원 목록과 버전, Multi-Branch 및 Trainer 직접 로그인 동시 사용자·자료 증가·응답시간·백업·복구·장애 대응 책임을 정한다.

Related decisions / requirements: PD-005/021; NFR-006/008/009/010/011. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Architecture/NFR 단계, 구현 수용 기준 확정 전

확정된 경계: 주요 업무의 Responsive Web과 Smartphone Trainer Session 등록은 v1 확정이다. 터치·작은 화면의 정보/Action 수행을 검증하며 breakpoint와 지원 환경 상세만 미정이다. PD-021은 OPEN 유지.

Status: OPEN

확인 주체: 사용자/업무 책임자와 해당 후속 단계 담당자. 답변·기한은 미정.

<a id="ux-001"></a>
## UX-001. 여러 날짜 Session 일괄 입력 편의

Question / TODO: 여러 실제 날짜의 개별 Session을 한 번의 입력 작업으로 등록하는 편의가 필요한가? 필요하면 확인·오류 안내 경험을 정의한다.

Related decisions / requirements: PD-008; PR-008/015. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: UX 단계; v1 편의 기능 채택 전

확정된 경계: 개별 날짜 원본 단위는 확정이며 이 질문과 무관하다. 기존 월 복사 기능 채택이 아니다.

Status: OPEN

확인 주체: 사용자/업무 책임자와 해당 후속 단계 담당자. 답변·기한은 미정.

<a id="ops-001"></a>
## OPS-001. 신규 운영 시작과 일괄 전환 준비

Question / TODO: 빈 데이터에서 Master Admin·Organization/Branch·계정·기준정보·회원·Trainer·Pass를 새로 생성하는 준비 책임, 업무 시작 기준일, 짧은 검증 기간과 준비완료 판정은?

Related decisions / requirements: PD-006/017/018/019; PR-028. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: deployment/cutover 계획; 실운영 전

확정된 경계: 이관과 장기 이중 입력은 하지 않는다. 기존 이용자의 남은 업무를 누가 어떻게 새로 설정할지 확인하되 기존 DB 복사로 대체하지 않는다.

Status: OPEN

확인 주체: 사용자/업무 책임자와 해당 후속 단계 담당자. 답변·기한은 미정.

<a id="legal-001"></a>
## LEGAL-001. 최소 개인정보·보존·필요 삭제

Question / TODO: 항목별 수집 필요성·열람, 개인정보/감사기록 보존 기간, 법적·운영상 필요한 삭제와 과거 업무 이력 보존의 관계를 검토한다.

Related decisions / requirements: PD-011/022; NFR-004/005. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: 항목·열람은 관련 설계 전; 기간·법적 정책은 별도 검토 및 실운영 전

확정된 경계: 최소 저장·권한 제한·중요 행위 감사는 승인됨. 구체 기간과 Hard Delete 예외를 임의로 정하지 않는다.

Status: OPEN

확인 주체: 사용자/업무 책임자와 해당 후속 단계 담당자. 답변·기한은 미정.

<a id="br-009"></a>
## BR-009. 월 정산 추가 지표·확인 절차

Question / TODO: 필수 월 정산 외 추가 통계가 필요한가? 월 정산 확인·마감/확정·확정 후 정정 절차는 어떻게 정하는가?

Related decisions / requirements: PD-012; PR-010/011; BR-007/012/013.

Required timing: 추가 통계 채택 전; 정산 수명·정정 상세 설계 확정 전.

확정된 경계: 기본급 지원·별도 표시와 월 정산 합산은 CLOSED(PD-009/012). Monthly Settlement = 해당 월 적용 Base Salary + 유효한 Session Payment 합계 + 유효한 Additional Performance 합계다. Trainer·대상 월·적용 기본급·Session 수·Session Payment 합계·추가실적 내역/합계·월 정산 합계를 구분한다. 2,500,000원 + 1,200,000원 + 150,000원 = 3,850,000원이며 여러 지점 수업으로 동일 월 기본급을 중복 가산하지 않는다. 타 지점 Session Payment 포함 여부는 MB-009 결정 전 확정하지 않는다. 12개월 고정 평균은 요구하지 않는다. 보상 설정 변경의 별도 승인 없음은 월 정산 승인 절차 결정이 아니다.

Status: OPEN

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

<a id="br-010"></a>
## BR-010. 지급 계산 입력값 검증

Question / TODO: Product Session Count·Price, Trainer Rate/Fixed Amount/Base Salary와 Additional Performance 금액의 허용 범위·정밀도·누락값 처리는? RATE 0회 분모 등 계산 불가능한 입력은 어떻게 안내하는가?

확정된 경계: 지급 값은 Trainer 기준이며 RATE 결과의 1,000원 단위 올림은 BR-PAY-013으로 확정이다. 누락된 설정을 임의의 기본값이나 서비스 0원으로 대체하지 않는다. 허용 최솟값·최댓값은 임의 확정하지 않는다.

Related decisions / requirements: PD-009; PR-006/007/008; [BR-PAY-001–005](business-rules.md)

Required timing: Architecture 착수 가능; 입력 검증 상세 설계·구현 확정 전

Status: OPEN

확인 주체: 사용자/업무 책임자.

<a id="br-011"></a>
## BR-011. Product 기준정보 변경과 기존 Pass

Question / TODO: Product Price·Session Count·Payment Type 변경 시 기존 Pass에 연결된 이후 신규 Session에는 어떤 Product 기준을 적용하는가?

Related decisions / requirements: PD-007/009/012; PR-003/006/008/010. 기존 BR-006에서 남은 Product 변경 질문을 분리했다.

Required timing: Architecture 착수 가능; Product 변경의 기존 Pass 적용 상세 설계·구현 확정 전 사용자 확인

확정된 경계: Trainer Rate/Fixed Amount 적용 시점과 정상 등록 시 확정은 BR-PAY-011/012로 해결되었다. 이 질문으로 해당 결정을 다시 OPEN으로 만들지 않는다. 과거 확정 Session Payment를 현재 Trainer 설정으로 재계산하지 않는다.

Status: OPEN

확인 주체: 사용자/업무 책임자와 관련 설계 담당자.

## Multi-Branch 변경에 따른 Product Open Questions

아래 질문의 결정 주체는 사용자/업무 책임자다. 기술 설계로 대신 결정하지 않는다. 공통 제약 검토 자체를 중단할 필요는 없지만 각 영향 영역은 답변 전 확정할 수 없다.

<a id="mb-001"></a>
## MB-001. Branch / Trainer

Question / TODO: Trainer가 조회 가능한 Member와 타 지점 업무 조건은? Trainer 지점 이동의 적용 시점과 과거 기록 처리는?

Status: OPEN

Related decisions / requirements: PD-002/004; PR-005/008/020/029/030. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Trainer 관계·허용 PT Scope 및 Session 권한 상세 설계 확정 전

확정된 경계: 단일 Home Branch 소속과 타 지점 수업 가능은 CLOSED. Branch에는 여러 Trainer가 있을 수 있고 지원 수업으로 소속을 변경하거나 추가하지 않는다. 과거 Session Performed Branch는 보존한다.

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

<a id="mb-002"></a>
## MB-002. Branch / Member

Question / TODO: Member의 타 지점 업무 허용·조회 조건과 Home Branch 이동/변경 정책은?

Status: OPEN

Related decisions / requirements: PD-004/007; PR-002/003/008/030. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Member 관계·Branch 이동·조회 범위 상세 설계 확정 전

확정된 경계: 단일 Home Branch와 허용된 타 지점 PT 이용은 CLOSED. Home Branch가 다르다는 이유만으로 PT 이용을 일률 차단하지 않는다. Member는 Login Account와 별개다.

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

<a id="mb-003"></a>
## MB-003. Pass Branch 귀속 / 교차 사용

Question / TODO: Issued Branch 밖에서 Pass를 사용할 구체 조건과 관련 업무 접근 범위는?

Status: OPEN

Related decisions / requirements: PD-004/007; PR-003/008/030; BR-PAY-006. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Pass 사용 가능 범위·선택·차감 및 관련 권한 상세 설계 확정 전

확정된 경계: Pass의 단일 Issued Branch와 허용된 타 지점 사용 가능은 CLOSED. 발급 지점이 유일한 사용 지점은 아니다. 사용 가능한 Pass 내 FIXED_AMOUNT 우선/FIFO는 유지한다.

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

<a id="mb-004"></a>
## MB-004. Administration / Branch Scope 부여

Question / TODO: Operator의 Branch Scope 부여, Branch Admin의 자기 Branch 기본정보 수정 항목과 계정 발급 위임 범위는?

Status: OPEN

Related decisions / requirements: PD-001/004/019; PR-001/020/021/030. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: 계정·Branch 관리·Scope 부여의 상세 권한 설계 확정 전

확정된 경계: Branch Admin은 v1에서 단일 Branch 관리로 CLOSED. 일부 여러 지점만 관리하는 중간 역할은 추가하지 않는다. Master Admin의 Organization 전체 및 구조/계정 관리는 유지한다.

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

<a id="mb-005"></a>
## MB-005. Trainer Session 정정 / Cross-Branch 검증

Question / TODO: Trainer 본인 Session 정정/취소 허용 여부와 타 지점 업무에서 Trainer·Member·Pass·Performed Branch의 구체 허용 조건은? 특정 대상 이용 권한과 다른 Branch 전체 Member 목록 조회 권한을 어떻게 구분하는가?

Status: OPEN

Related decisions / requirements: PD-002/010; PR-008/009/029/030; BR-007. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Trainer 정정·취소 및 교차 Branch Session 상세 설계 확정 전

확정된 경계: 허용되지 않은 Cross-Branch 접근은 금지한다. Backend 검증 의무는 확정이며 허용 관계에 대한 정책과 기술 구현은 구분한다. 본인 등록 권한이 정정 권한을 자동 부여하지 않는다.

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

<a id="mb-006"></a>
## MB-006. Branch Settlement 금액 노출

Question / TODO: Branch Admin에게 어떤 Trainer·대상 월·지점 귀속의 정산 결과와 실제 금액·계산 근거를 공개하는가? 타 지점 Trainer의 설정을 추론하거나 감사 경로로 우회 노출하지 않으려면 어떤 업무 열람 제한이 필요한가?

Status: OPEN

Related decisions / requirements: PD-012; PR-010/030; BR-PAY-010. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Settlement·Session·감사 정보의 지급 관련 열람 상세 설계 확정 전

확정된 경계: Rate / Fixed Amount / Base Salary 세 항목의 조회·설정·변경은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 단일 Branch를 Home Branch로 가진 Trainer에게만 허용한다. Operator와 Trainer는 본인 설정을 포함하여 모두 불가하다. 타 지점 지원 수업은 보상 설정 접근 권한을 부여하지 않는다. Backend에서 대상 Trainer의 Home Branch를 검증하며 직접 ID 요청과 감사·정산 등 우회 경로에도 제한을 적용한다. 보상 설정 권한과 정산 결과 공개 범위는 별개다. 지점 귀속은 MB-010과 함께 결정한다.

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

<a id="mb-007"></a>
## MB-007. PT Product의 Organization / Branch 범위

Question / TODO: Organization 공통 Product를 Branch Admin도 생성/수정할 수 있는가?

Status: OPEN

Related decisions / requirements: PD-004/009; PR-006/020/030. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Product 공유·귀속·관리 권한 상세 설계 확정 전

확정된 경계: Organization 공통 Catalog는 CLOSED. 지점별 가격 정책은 추가하지 않는다. 기존 Master Admin의 상품 생성/수정 권한은 유지한다(PR-006, BR-PAY-001). Branch Admin 권한은 OPEN이며 미정을 허용으로 취급하지 않는다.

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

<a id="mb-008"></a>
## MB-008. Branch 활성/비활성 정책

Question / TODO: Branch 활성/비활성 관리를 어떻게 지원할 것인가? 비활성화 가능 조건, 진행 중 Pass·Member·Trainer·Session의 처리와 과거 정산/감사 조회는 어떻게 다루는가?

Status: OPEN

Related decisions / requirements: PD-004/011/022; PR-004/020/027. [결정](product-decisions.md), [요구사항](requirements.md)

Required timing: Branch 수명·비활성화 상세 설계 확정 전

확정된 경계: Branch 비활성화 가능성을 고려한다. 구조 관리 주체는 Master Admin이며 상태·자동 이동·잔여 소멸·과거 이력 삭제를 임의 확정하지 않는다.

확인 주체: 사용자/업무 책임자. 답변·기한 미정.


<a id="br-012"></a>
## BR-012. 월 기본급 적용 월·미확정 정산

Question / TODO: 변경한 Base Salary는 어느 월부터 적용하는가? 관리자가 적용 월을 지정하는가? 미확정 월 정산에는 어떻게 반영하는가? 입사·퇴사·휴직 등에서 운영자가 적용할 금액은 어떤 정책으로 정하는가?

Status: OPEN

Related decisions / requirements: PD-009/012; PR-007/010; BR-PAY-014/016.

Required timing: 기본급 적용·정산 반영 상세 설계/구현 확정 전.

확정된 경계: 월 고정 기본급 지원과 과거 확정 기본급/합계 보존은 확정이다. 입퇴사 일할·근무일수·휴직 기반 자동 급여 계산은 v1에서 제공하지 않는다. Rate/Fixed Amount의 신규 Session 적용 규칙을 기본급에 적용하지 않는다.

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

<a id="br-013"></a>
## BR-013. 추가실적 권한·금액·처리 절차

Question / TODO: Master Admin만 등록하는가, Branch Admin도 가능한가? 가능하다면 대상 Trainer Home Branch·수행 지점 등 어느 기준인가? Trainer 신청이 필요한가? 관리자 별도 승인 단계가 필요한가? 수동 금액인가 유형별 계산인가? 정정/취소 및 정산 마감 이후 처리는?

Status: OPEN

Related decisions / requirements: PD-027; PR-031/027/010; BR-PAY-015.

Required timing: 추가실적 입력·권한·계산·승인·정정 상세 설계/구현 확정 전.

확정된 경계: 추가실적 v1 도입과 생성·정정·취소 감사는 확정이다. 보상 설정 권한·승인 생략을 자동 적용하지 않고 미정 권한을 허용하지 않는다.

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

<a id="mb-009"></a>
## MB-009. 타 지점 수업 보상 구성 — 결정 게이트

Question / TODO: 타 지점 수업 보상은 일반 Session 수당에 추가되는 인센티브인가, 아니면 해당 수업에 대한 보상 전체를 추가실적으로 처리하는가?

Status: OPEN

Related decisions / requirements: PD-009/012/027; PR-008/010/031; BR-PAY-015/016.

Required timing: 타 지점 Session 보상 상세 설계 및 구현 확정 전 필수 사용자 결정.

확정된 경계: 검토 선택지 A: 수업 기록과 Pass 차감은 유지하고 해당 보상은 추가실적으로만 반영. B: 일반 Session Payment를 지급하고 별도 추가 인센티브가 있을 때 추가실적을 더함. A/B 모두 미확정이다. 사용자 결정 전 기본 수당을 0원으로 정하거나 일반 수당+추가실적을 자동 이중 지급하지 않는다. 실제 수업 이력·Pass 사용 횟수의 일관성은 유지한다.

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

<a id="mb-010"></a>
## MB-010. 지점 이동·교차 수업의 정산 귀속

Question / TODO: Trainer 소속 이동 시 기본급/실적은 어느 Branch에 귀속되는가? 타 지점 Session 및 추가실적을 어느 지점 정산/비용으로 집계하는가? Branch Admin에게 어느 범위 정산을 공개하는가(MB-006 연결)?

Status: OPEN

Related decisions / requirements: PD-004/012/027; PR-010/030; MB-001/006.

Required timing: 지점별 정산 집계·비용 귀속·공개 상세 설계/구현 확정 전.

확정된 경계: Home Branch·Performed Branch·정산 집계/비용 귀속 Branch가 같다고 가정하지 않는다. 동일 월 기본급은 지점 수만큼 중복 가산하지 않는다. Trainer 이동 시점/과거 기록은 MB-001과 연결한다.

확인 주체: 사용자/업무 책임자. 답변·기한 미정.

## 이번 개정의 CLOSED 처리

기존 복합 질문 MB-001/002/003/004/007 및 BR-009는 해결된 부분을 각 `확정된 경계`에 CLOSED로 분리했다. 남은 질문이 있어 ID 전체는 OPEN을 유지한다. 기존 BR-003/004/005/006 CLOSED도 유지하며 이번에 전체가 새로 CLOSED된 기존 OPEN ID는 없다. 보상 설정 권한·승인 불필요·감사는 PD-001/009/022의 CLOSED 결정을 갱신했다. 추가실적 도입은 PD-027 CLOSED이며 상세 권한·보상 구성은 OPEN이다.
