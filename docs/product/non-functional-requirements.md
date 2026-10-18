# 비기능 요구사항

승인된 제품 결과와 아직 승인되지 않은 품질 후보를 구분한다. 적용 범위는 확정된 핵심 PT v1이다. 기술·저장 방식·구체 수치는 결정하지 않는다.

<a id="nfr-001"></a>
## NFR-001. 인증과 직무별 접근 통제

출처/상태: APPROVED-TO-BE

제품 필요: Master Admin·Branch Admin·Operator·Trainer 로그인 계정은 Role과 Data Scope에 허용된 자료/기능만 접근한다. Member 로그인은 Future Scope다.

수용 기준 / 남은 상세: Rate / Fixed Amount / Base Salary 세 항목의 조회·설정·변경은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 단일 Branch를 Home Branch로 가진 Trainer에게만 허용한다. 관리자와 Trainer를 겸하는 계정은 관리 권한 범위 안이면 본인의 세 항목도 조회·변경할 수 있다. Master Admin은 본인 포함 허용하며, Branch Admin은 본인 Trainer의 Home Branch가 관리 Branch일 때 본인도 허용한다. 관리자 권한이 없는 Operator·Trainer 계정은 본인 포함 모든 Trainer 설정 조회·변경이 불가하다. 타 지점 지원 수업은 보상 설정 접근 권한을 부여하지 않는다. Backend에서 대상 Trainer의 Home Branch를 검증하며 직접 ID 요청과 감사·정산 등 우회 경로에도 제한을 적용한다. UI 숨김으로 충족하지 않으며 목록·검색·집계·개별 요청에도 Scope를 적용한다. 특정 교차 업무 허용과 다른 지점 전체 목록 접근을 구분한다. 기술 모델은 ARCH-001, 계정 수명은 ARCH-002다.

추가 인가 수용 기준(2026-10-11): 월 정산의 최초 확정은 Master Admin에게 Organization 전체 Trainer, Branch Admin에게 확정 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 직접 확정한다. 직접 ID·위조 Branch Context·과거 소속·Performed Branch만을 근거로 한 우회와 관리자 권한이 없는 Operator·Trainer의 최초 확정을 Backend에서 거부한다. 상세 공개 권한까지 자동 부여하지 않는다(MB-006).

정산 조회 인가 수용 기준(2026-10-11): 현재 자기 Branch 소속 Trainer의 해당 월 정산 전체 금액·구성 내역은 타 지점 지원 수업 보상까지 공개한다(조회 시점 현재 Home Branch 기준, 2026-10-11 사용자 확정). 관리 범위 안 본인 Trainer도 동일하게 허용한다. 다른 Home Branch Trainer의 전체 월 정산은 자기 지점의 지원 수업 수행 사실·직접 ID·위조 Branch Context만으로 공개하지 않는다. 목록·검색·집계에서도 동일한 Scope를 적용하며 Operator·관리자 권한 없는 Trainer의 별도 정산 조회 권한을 이번 결정으로 추가하지 않는다.

비용 보고서 인가 수용 기준(2026-10-11 사용자 확정): v1 지점별 비용 보고서는 현재 Master Admin 권한과 Organization Scope를 Backend에서 검증한 요청에만 공개한다. Master·Trainer 겸임은 허용하되 Master 권한 없는 Branch Admin·Operator·Trainer 및 Branch Admin·Trainer 겸임은 거부한다. 자기 지점 비용 합계·직접 ID·위조 Branch Context·목록/검색/집계 등 보고서 경로에도 동일하게 적용한다. Branch Admin의 현재 소속 Trainer 해당 월 전체 정산 조회와 구분하며, 비용 귀속 지점만으로 보고서/타 소속 Trainer 열람 권한을 부여하지 않는다. PR-010/030; BR-PAY-016; MB-006/010을 따른다.

관련 요구·결정: PD-001/002/003/019/022; PR-001/021/026. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

2026-10-12 사용자 확정(회원 소속 지점 변경 권한): 이동은 Master Organization 전체 또는 요청 처리 시점 Member 현재 Home Branch 관리 Branch Admin만 허용하며 받는 지점의 별도 승인은 요구하지 않는다. Backend에서 현재 Caller/관리 Scope·서버 Member 현재 Home Branch·대상 Branch Organization을 검증하며 위조 ID/Branch Context·이전 소속/처리자·받는 지점 관리자라는 사실만으로 허용하지 않는다. 반영 후 Home Branch 기준 관리에는 변경된 현재 사실을 적용하고 기존 담당/지원 조회·다른 업무별 독립 Scope는 각각 유지한다. 구체 적용 시점·권한 경합/실패 일관성은 후속 계약 검증 대상이다(BR-OPS-007, PR-002/030, MB-002).

2026-10-12 사용자 확정(회원 소속 변경의 적용 시점): 저장 완료 즉시 새 Home Branch가 현재 소속이 되고 미래 예약은 지원하지 않는다. 성공한 저장 이후의 후속 요청에 새 현재 소속 기반 인가를 적용하며 별도 재로그인이나 Frontend 표시 갱신을 권한 반영 조건으로 두지 않는다. 실패하면 기존 소속을 유지한다. 이전 소속만의 Member 관리 근거는 종료하고 기존 담당/지원 조회·다른 독립 업무 Scope는 별도 판단한다. 이미 처리 중인 요청/동시 이동의 인가 일관성은 후속 계약 검증 대상이며 AuthSession 구현/ADR-0004 승인은 아니다(BR-OPS-007, PR-002/030, MB-002).

2026-10-12 사용자 확정(회원 이동 대상 지점): Member Home Branch 이동은 같은 Organization의 활성 Branch만 대상으로 허용한다. Backend가 현재 대상 상태를 확인하고 Master/Branch Admin도 비활성 대상 요청은 거부한다. 요청의 활성 표시값이나 Frontend 선택 제한만을 신뢰하지 않으며 거부 시 기존 소속/관계·이력 유지, 기존 Actor/관리 Scope 조건도 유지한다. Branch 비활성화 자체의 업무 영향·이동과 상태 변경 경쟁의 일관성은 후속이다(BR-OPS-007, PR-002/030, MB-002/008).

기존 회원 조회 원칙 적용(BR-OPS-005): 담당 관계를 인정하는 Pass의 현재 담당이 바뀌면 후속 회원 목록/검색/직접 ID·전화번호 공개도 Backend에서 변경된 현재 담당 관계와 별도의 개별 지원/관리 권한으로 판단한다. 이전 담당이라는 사실만으로 영구적인 Member 조회 권한을 부여하지 않는다. 새 담당은 기존 담당 회원 범위에서 인가하며 이전 담당도 다른 담당 Pass나 개별 지원/관리 권한이 있으면 그 독립 근거로 판단한다. 본인이 실제 수행한 과거 PT 기록 조회는 기존 별도 업무 Scope를 따르고, 이를 다른 Member/Pass/PT·보상 설정의 무제한 공개로 확대하지 않는다. 잔여 0만으로 담당 회원 조회를 막지 않는 규칙도 유지한다.

담당 교체 허용(2026-10-12)과 일반 교체 저장 후 현재 관계 반영은 BR-OPS-008을 따른다. 교체 Actor/Branch Scope는 Master Organization 전체/Branch Admin 처리 시점 Member 현재 Home Branch 기준으로 확정(2026-10-12)됐으며 Backend가 현재 Caller 관리 권한·실제 Pass/Member 관계와 현재 소속을 확인한다. 비관리자 Operator/Trainer·범위 밖 직접 ID/위조 role·Branch/Member 소속 요청은 거부하고 관리자 겸임은 관리자 Scope로 판단한다. Issued/Performed/Trainer Home Branch·과거 소속/담당/처리 사실만으로 교체 권한을 부여하지 않는다. 수동 만료/해제의 Issued Branch 기준과 보상 설정의 Trainer Home Branch 제한은 유지한다. 교체 대상은 같은 Organization의 다른 지점 Trainer도 허용으로 확정(2026-10-12, BR-OPS-008)됐으며 Backend는 대상 Trainer의 실제 Organization 관계를 검증한다. 클라이언트가 보낸 Trainer/Organization ID만으로 인가하지 않고 다른 Organization 대상 요청은 기존 담당/잔여·이력을 유지하며 거부한다. 타 지점 담당 교체 허용이 Trainer 보상 설정·전체 프로필/정산 또는 다른 지점 전체 목록 공개를 허용하는 것은 아니다. 교체 전 실제 본인 수업의 이전 담당 직접 등록은 허용으로 확정(2026-10-12, BR-OPS-003/008)됐다. 현재 Caller/본인 Trainer 연결·Organization와 실제 수업 당시 담당/수행 사실·기존 Pass/정산 조건을 확인하며, 현재 담당이 바뀌었다는 이유만으로 등록을 막지 않는다. 이 한정된 명령 인가로 과거 담당 회원 목록/상세·전화번호·다른 Pass/PT를 공개하거나 교체 후 새 수업을 과거 담당 근거만으로 허용하지 않는다. 위조 수행 Trainer/Member/Pass/진행일·과거 담당 표시만으로 인가할 수 없고 거부/실패 시 업무 일부 변경을 남기지 않는다. 대상 Trainer 최소 식별/응답/Trainer 선택 정보 및 과거 담당/수행 사실 확인 불가·정정·등록/교체/조회/소속·상태·월 확정 경합은 후속 계약 검증 대상이다.

2026-10-12 사용자 확정(잔여 0회인 이용권의 담당 교체 질문의 1번): Remaining이 0인 기존 Pass도 Assigned Trainer를 교체할 수 있다. 잔여를 모두 사용해 이용이 끝난 Pass도 포함한다. 같은 Pass에서 담당 A를 B로 바꾸며 Remaining 0·발급 조건/Issued Branch·과거 실제 수행 Trainer/PT 기록·확정 지급/정산 이력은 유지한다. 새 담당 B는 기존 현재 담당 관계에 따른 Member 조회·응대를 이어갈 수 있다. 기존 Master Organization 전체/Branch Admin 처리 시점 Member 현재 Home Branch 권한과 같은 Organization의 다른 지점 Trainer도 대상 허용 원칙은 유지한다(BR-OPS-005/008, PD-007, PR-003/029/030).

새 현재 담당의 회원 목록/검색/직접 ID·기존 허용 전화번호는 현재 Caller/Organization와 담당 관계로 인가한다. 이전 담당은 다른 현재 권한 근거 없이 과거 담당 사실만으로 조회를 유지할 수 없고 새 담당에게 이전 Trainer PT/보상·다른 Pass 전체를 공개하지 않는다. 잔여 0 교체는 정상 차감 조건이나 민감 설정 접근 제한을 면제하지 않는다. 선택 필터는 현재 인가된 Member 전체 Pass 잔여 기준으로 유지하며 다른 종료 사유/계약·경합은 후속이다.

2026-10-12 사용자 확정(이용권 횟수의 수동 조정 권한 질문의 1번): Pass 횟수의 수동 조정은 Master Admin의 Organization 전체 범위 또는 처리 시점 현재 관리 Branch가 해당 Pass의 Issued Branch인 Branch Admin에게 허용한다. 수원 발급/현재 강남 소속 Member의 이용권은 수원 Branch Admin 또는 Master가 조정하며, 강남 Branch Admin은 Member의 현재 소속만을 근거로 조정할 수 없다. 회원 소속이나 담당 Trainer가 바뀌어도 Issued Branch 기준은 유지한다. 이용권 수동 만료/해제와 같은 발급 지점 기준이며 담당 교체의 Member 현재 Home Branch 기준과 구별한다(BR-OPS-004/008/009, PD-007/010, PR-003/030).

Backend는 검증된 현재 Caller 관리 권한/Organization·관리 Branch와 실제 Pass Issued Branch·Pass/Member 관계를 확인하고 비관리자·범위 밖 직접 ID/위조 Scope 요청을 거부한다. Member/Trainer 소속·현재 담당·지원/수업 지점이나 과거 조정 Actor 사실은 권한 근거가 아니다. Role/Scope 축소 후 요청도 현재 권한으로 인가하며 다른 업무/민감 정보 열람 권한으로 확장하지 않는다(BR-OPS-009).

2026-10-12 사용자 확정(다른 지점에서 새 이용권 구매·발급 질문의 1번): Member는 같은 Organization의 Home Branch 밖 지점에서도 새 PT Pass를 구매·발급받을 수 있다. 수원 소속 회원이 강남에서 발급받으면 Member Home Branch는 수원으로 유지하고 새 Pass의 Issued Branch는 강남으로 기록한다. Member Home Branch와 Issued Branch가 같아야 한다는 제한을 두지 않는다. 기존 Member 식별자/소속·보유 Pass와 과거 PT/지급·정산 이력은 유지하며 타 지점 발급을 위해 Member를 지점별로 복제하거나 소속을 자동 이동하지 않는다(BR-OPS-001/010, PD-004/007, PR-002/003/030).

현재 Caller의 발급 Permission/Organization·허용 Issued Branch Scope와 Member/Product/Branch 실제 관계를 서버 검증하며 Home Branch 일치 여부로 대체하지 않는다. 직접 ID/위조 role/Organization/Branch로 범위를 넓힐 수 없다. 발급 대상 특정 회원의 최소 식별은 일반 회원 목록/상세·전화번호/다른 Pass/PT 조회 권한과 분리하며 Trainer 기존 담당/지원 조회와 보상 설정 제한을 유지한다. Master·Branch Admin·Operator의 발급 허용/각 역할의 실제 발급 지점 범위와 Trainer 단독 불가는 확정됐으며 발급용 이름·전화번호 일부의 Organization 전체 지점 검색도 확정됐으며 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·추가 공개 정보·Member 선택용 최소 식별 응답/계약은 후속 게이트이고 거부/실패 시 기존 Member/Pass/이력을 유지한다(BR-OPS-010, NFR-005).

2026-10-12 사용자 확정(새 이용권 발급 Actor 질문의 1번): 새 PT Pass 발급은 Master Admin·Branch Admin·Operator에게 각자의 허용된 실제 Issued Branch 범위에서 허용한다. Master는 Organization 전체, Branch Admin은 자신의 단일 관리 Branch, Operator는 부여된 허용 발급 Branch Scope에서 처리한다. 같은 Organization의 Member는 Home Branch가 발급 지점과 달라도 대상이 될 수 있으며 기존 Member/Home Branch를 유지하고 새 Pass에 실제 Issued Branch를 기록한다(BR-OPS-010, PD-004/007, PR-003/030).

Backend는 각 발급 요청에서 검증된 현재 Caller의 발급 역할/Organization·허용 실제 Issued Branch와 Member/Product/Branch의 실제 Organization 관계를 확인한다. 범위 밖 발급 지점·다른 Organization·Trainer 단독 권한·직접 ID/위조 role/Branch 값으로는 발급할 수 없으며 역할/Scope가 철회·축소되면 후속 발급 요청에도 현재 권한을 적용한다. 거부/실패 시 기존 Member/Home Branch·Pass·업무 이력을 유지한다. 발급 권한과 발급 이후의 관리 권한은 별도이므로 과거 발급 Actor였다는 사실만으로 후속 관리자 권한을 얻지 않는다.

권한 경계: Trainer 역할만으로는 새 Pass를 발급할 수 없다. Trainer를 겸하는 계정에 Master·Branch Admin·Operator의 발급 권한이 있으면 해당 역할의 독립적인 발급 Scope로 판단하며 별도 계정을 요구하지 않는다. Operator의 새 발급 권한은 공통 상품 생성/수정, 기존 Pass 수동 횟수 조정·만료/해제·담당 교체, Member 소속 이동, PT 정정/취소·Compensation Setting·Additional Performance·월 정산의 별도 권한을 추가하지 않는다. 발급 대상 식별을 타 지점 전체 Member 목록/전화번호·다른 Pass/PT/민감 보상 정보의 일반 조회 허용으로 확대하지 않는다. 기존 보상 설정 접근 제한과 Trainer의 담당/개별 지원 회원 조회는 그대로다.

2026-10-12 사용자 확정(발급용 타 지점 회원 검색 질문의 2번): Branch Admin·Operator는 자신의 허용된 실제 Issued Branch에서 새 PT Pass를 발급하기 위해 같은 Organization 전체 지점의 Member를 이름·전화번호 일부로 검색할 수 있다. 전화번호 전체 일치만을 요구하지 않으며 Member Home Branch가 Caller의 관리/발급 Branch와 다르다는 이유만으로 검색 후보에서 제외하지 않는다. Master의 기존 Organization 전체 범위는 유지한다. 검색은 기존 Member를 선택하여 실제 발급 지점의 새 Pass를 만드는 흐름이며 Member 소속 이동/복제나 기존 Pass·PT·지급·정산 변경을 수행하지 않는다(BR-OPS-010, PD-004/007/022, PR-002/003/030).

검색 인가/정보 공개 경계: 이 허용은 이용권 발급용 Member 검색의 후보 범위·검색 방식과 이름/전체 전화번호/현재 Member Home Branch 공개다. Backend는 매 검색/선택/발급 요청에서 현재 Caller의 발급 역할/Organization·허용 실제 Issued Branch와 대상 Member의 실제 Organization을 검증한다. 검색 Branch Context를 위조하거나 과거 검색 결과/선택 Member ID로 철회된 역할·Scope 또는 다른 Organization을 우회할 수 없다. 같은 전화번호/이름의 여러 Member는 별도 식별자로 구분하여 선택하며 번호만으로 병합하거나 첫 결과를 자동 선택하지 않는다. 이 세 항목의 읽기 허용이 회원 정보/전화번호 수정·일반 Member 상세·전체 무조건 목록/일괄 내보내기, 다른 개인정보/Pass/PT/보상 정보 열람 권한을 추가하지 않는다. Trainer 단독의 담당/개별 지원 Member 검색 및 기존 전체 전화번호 공개는 유지하고 발급 역할 겸임은 그 독립 발급 업무 Scope로 판단한다. 응답은 승인된 공개 범위 안에서 구성하며 Member 선택용 최소 식별 응답/계약과 추가 공개 정보는 후속이다. 실제 운영 연락처/검색어를 문서·일반 로그에 복사하지 않는다.

이번 결정으로 발급용 검색 후보의 Organization 전체 지점 범위·이름/전화번호 일부 검색과 결과의 이름/전체 전화번호/현재 Member Home Branch 공개는 해결됐다. 추가 공개 정보·Member 선택용 최소 식별 응답/계약 및 나머지 검색/대상 조건, 새 Operator 발급 절차·기존 계정 역할 부여·Master 전용 Operator 지점 변경의 대상/절차·실제 발급 지점 선택, 발급 시 활성 담당 필수/상품 최초 횟수의 나머지 상태·계약/저장/UoW·실패/재시도/중복·권한/소속/상품/지점 상태 변경 경합은 후속이다. 승인된 세 항목의 공개/전화번호 비마스킹을 다시 미결정으로 두지 않는다. Product OPEN/ADR·모듈/계약 상태와 기존 보상 설정 접근 제한을 유지하며 실제 검색/발급 구현·검증 완료를 뜻하지 않는다.

2026-10-12 사용자 확정(발급용 검색 결과 표시 정보 질문의 1번): 새 PT Pass 발급용 Member 검색 결과에는 이름·전체 전화번호·소속 지점을 표시한다. 소속 지점은 해당 Member의 현재 Home Branch이며 Caller 관리 지점/Pass Issued Branch/수업 Performed Branch와 구별한다. 같은 Organization의 타 지점 회원 검색 결과에도 동일하게 적용하고 부분 마스킹된 번호만 표시하도록 제한하지 않는다. 기존 이름·전화번호 일부의 Organization 전체 지점 검색과 현재 발급 역할/실제 Issued Branch Scope 인가는 유지한다(BR-OPS-010, PD-004/007/022, PR-002/003/030, NFR-001/005).

검색 인가/정보 공개 경계: 이 허용은 이용권 발급용 Member 검색의 후보 범위·검색 방식과 이름/전체 전화번호/현재 Member Home Branch 공개다. Backend는 매 검색/선택/발급 요청에서 현재 Caller의 발급 역할/Organization·허용 실제 Issued Branch와 대상 Member의 실제 Organization을 검증한다. 검색 Branch Context를 위조하거나 과거 검색 결과/선택 Member ID로 철회된 역할·Scope 또는 다른 Organization을 우회할 수 없다. 같은 전화번호/이름의 여러 Member는 별도 식별자로 구분하여 선택하며 번호만으로 병합하거나 첫 결과를 자동 선택하지 않는다. 이 세 항목의 읽기 허용이 회원 정보/전화번호 수정·일반 Member 상세·전체 무조건 목록/일괄 내보내기, 다른 개인정보/Pass/PT/보상 정보 열람 권한을 추가하지 않는다. Trainer 단독의 담당/개별 지원 Member 검색 및 기존 전체 전화번호 공개는 유지하고 발급 역할 겸임은 그 독립 발급 업무 Scope로 판단한다. 응답은 승인된 공개 범위 안에서 구성하며 Member 선택용 최소 식별 응답/계약과 추가 공개 정보는 후속이다. 실제 운영 연락처/검색어를 문서·일반 로그에 복사하지 않는다.

2026-10-12 사용자 확정(Operator 업무 허용 지점 수 질문의 1번): v1 Operator 역할의 업무 허용 Branch는 한 시점에 하나만 지정한다. Operator는 그 지정된 단일 Branch에서 명시적으로 허용된 업무를 수행하며 같은 계정의 Operator 권한을 여러 Branch에 동시 부여하지 않는다. Branch당 Operator 한 명이라는 1:1 인원 제한을 추가하지 않으며 하나의 Branch에 여러 Operator가 있을 수 있다. 이 결정은 Operator 역할의 업무 Scope이며 기존에 허용된 겸임 역할의 독립적인 관리/PT 권한이나 Trainer Home Branch를 바꾸지 않는다(BR-OPS-011, PD-001/007, PR-001/003/030, ARCH-001, MB-004).

인가 경계: Backend는 검증된 현재 Caller의 Operator 역할/Organization·지정된 단일 업무 Branch와 해당 요청의 실제 업무 Branch를 확인한다. 직접 Branch ID·클라이언트 branch_id/role/선택 지점·과거 업무/발급 지점만으로 다른 Branch의 업무를 수행할 수 없다. 동일 계정에 Operator 권한을 중복 부여하거나 여러 Branch 중 하나를 임의 선택하는 방식으로 단일 지점 제한을 우회하지 않는다. 현재 역할/Scope 철회·축소 이후 후속 요청은 현재 권한을 적용한다. 지정이 없거나 복수 지정된 상태를 유효한 Operator 업무 권한으로 간주하지 않되 구체 계정/역할 저장·활성화 제약과 오류 계약은 후속 Architecture다.

기존 발급/검색 규칙 유지: Operator의 새 Pass 발급은 자신의 지정된 단일 Branch를 실제 Issued Branch로 사용한다. 그 발급 업무에서는 같은 Organization 전체 지점 Member를 이름·전화번호 일부로 검색하고 결과의 이름·전체 전화번호·현재 Member Home Branch를 조회/선택할 수 있다(BR-OPS-010). Member Home Branch가 Operator 업무 Branch와 다르다고 검색/발급을 거부하거나 회원 소속을 자동 이동하지 않는다. 전체 지점 Member 검색이 다른 Branch의 Pass 발급이나 일반 회원 상세/다른 Pass/PT·보상/수정·일괄 내보내기 권한을 부여하지 않는다. 기존 Master 전용 공통 상품 변경 및 관리자 전용 Pass 수동 조정·만료/해제·담당 교체/보상 업무 제한은 유지한다.

남은 결정: 새 Operator 발급/최초 Branch 지정 Actor는 Master Organization 전체/Branch Admin 자기 단일 Branch, 기존 Operator 업무 Branch 변경 Actor는 Master Organization 범위 전용으로 해결됐다. 변경은 기존 저장 후 현재 Scope 반영/실패 보존·감사 원칙을 적용한다. 발급 절차·기존 계정 역할 추가/변경·Operator 지점 변경의 대상 Branch/계정 상태·세부 절차/감사 계약 및 나머지 운영 행위 권한은 MB-004·ARCH-001/002 후속이다. 한 계정의 Operator 동시 허용 지점 수나 신규 발급/지점 변경 Actor를 다시 OPEN으로 두지 않는다. 실제 발급 대상·초기 조건/선택 응답·역할/Scope 저장·Caller/인가 계약·실패/재시도/경합은 관련 Product/Architecture 후속이다. IAM-001 S1에 Operator 구현을 추가하거나 기존 PROPOSED 인증/모듈/저장 설계를 승인한 것은 아니다.

Operator 계정 발급 인가(2026-10-12, BR-OPS-011, PR-021): Master의 현재 Organization 또는 Branch Admin의 현재 단일 관리 Branch와 대상 Branch의 실제 Organization을 Backend에서 확인한다. Branch Admin의 타 지점/타 Organization 발급·직접 ID/위조 역할/클라이언트 Scope·철회/축소된 권한을 거부한다. 허용되는 생성은 Operator 역할/최초 단일 Branch이며 다른 역할 발급·기존 계정 역할/지점 변경 권한으로 확대하지 않는다. Operator/Trainer 단독의 계정 발급은 불가하며 겸임은 독립 관리자 권한으로 판단한다.

Operator 업무 Branch 변경 인가(2026-10-12, BR-OPS-011): 현재 Master 권한/Organization·실제 대상 계정 및 변경 전후 Branch 관계를 검증한다. Branch Admin은 출발/도착 지점 관리자·최초 발급자여도 불가하며 직접 ID·위조 Scope/철회된 Master 권한으로 우회할 수 없다. 저장 완료 이후 후속 Operator 요청은 새 단일 Branch를 적용하고 이전 지점/이전 발급 사실로 권한을 유지하지 않는다. 겸임의 다른 역할/Trainer Home Branch·별도 인가는 유지하며 변경 실패 시 기존 Scope를 보존한다. AuthSession 철회 기술이나 다른 역할/계정 수명 정책을 확정한 것은 아니다.

신규 Trainer 로그인 계정 발급 인가(2026-10-12, BR-OPS-012): Master의 현재 Organization Scope 또는 Branch Admin의 현재 관리 Branch=대상 Trainer 현재 Home Branch를 Backend에서 검증한다. 타 지점 수행/담당 관계·Operator 업무 Branch·과거 소속/발급 사실로 대체하지 않는다. 타 Organization·위조 role/branch_id/Trainer ID·철회/축소된 권한·Operator/Trainer 단독 요청은 거부하고 기존 계정 역할/Trainer 연결 덮어쓰기·관리자 승격으로 확대하지 않는다. Trainer 역할의 보상 설정 접근 제한 및 기존 PT 조회/진행 Scope는 유지한다.

Trainer Home Branch 변경 인가(2026-10-12, BR-OPS-013): 현재 Master/Organization·실제 Trainer/현재 소속과 대상 Branch의 Organization을 검증한다. 출발/도착 Branch Admin·계정 발급자·Operator/Trainer 단독·직접 ID/위조 role·철회된 Master 권한은 거부한다. 저장 완료 이후 현재 Home Branch 기준의 보상 설정/월 정산 관리·Trainer 발급 요청은 새 소속을 검증하며 이전 지점의 과거 소속/발급 사실로 권한을 유지하지 않는다. 같은 계정의 다른 관리자/Operator Scope는 그대로이며 본인 보상 설정도 현재 관리자 Scope와 새 Trainer Home Branch 조건을 충족해야 한다. 실패 시 이전 소속/인가 근거를 유지하고 과거 수행 지점·수업/지급/정산 인가를 임의 변경하지 않는다.

Trainer 비활성화 인가(2026-10-12, BR-OPS-014): 실제 Trainer 활성 상태와 현재 검증된 Caller의 역할/Scope를 확인하여 Trainer 역할에만 의존한 PT/회원 개인정보 요청을 차단한다. 기존 쿠키·캐시된 Caller·역할 표시/직접 ID·남은 담당/지원 관계로 우회할 수 없다. 겸임자의 독립 관리자 Scope는 유지하며 범위 밖 관리 업무/민감 설정 접근을 추가하지 않는다. 전체 계정 차단과 다른 활성 역할이 없는 계정의 로그인은 별도 계정 수명 게이트이고 구체 AuthSession 갱신/철회·캐시/동시성은 후속 설계다.

Trainer 비활성화 Actor 인가(2026-10-12, BR-OPS-014): Master의 현재 Organization 또는 Branch Admin 현재 관리 Branch=대상 Trainer 현재 Home Branch를 Backend에서 검증한다. 실제 Trainer/현재 소속·같은 Organization 확인 없이 role/branch_id/Trainer ID를 신뢰하지 않는다. 타 지점 지원/과거 소속·계정 발급자·Operator/Trainer 단독·권한 철회/소속 변경 전 정보로 우회 불가다. 허용된 Trainer 중단만 처리하고 겸임 관리자 역할/Scope 및 기존 보상 접근 제한을 유지한다.

비활성 Trainer의 담당 관계 인가(2026-10-12, BR-OPS-014): 잔여 Pass의 Assigned Trainer 정보를 유지하더라도 실제 비활성 상태면 Trainer 역할의 Member 목록/검색/직접 ID/전체 전화번호·PT 진행 등록을 허용하지 않는다. 과거 쿠키/Caller나 담당 관계로 우회하지 못하도록 현재 상태를 확인한다. 독립 관리자 Scope는 별도 유지하며 후속 담당 교체는 기존 Member 현재 Home Branch 관리자 권한을 검증한다. 비활성화 권한이 모든 담당 Pass 교체/다른 지점 정보 접근 권한을 추가하지 않는다.

새 담당 대상 상태 검증(2026-10-12, BR-OPS-008/014): 허용된 최초 지정/교체에서 실제 Trainer 현재 활성 상태/Organization와 현재 Caller 행위 Scope·Member/Pass 관계를 Backend에서 확인한다. 선택 목록·클라이언트 active/role/Trainer ID·과거 조회·관리자 역할이나 AuthSession 존재로 실제 비활성을 우회할 수 없다. 같은 Organization 타 지점 활성 Trainer 허용 및 기존 Member Home Branch 기반 교체 권한을 유지하고 기존 비활성 담당의 정보 보존을 접근 허용으로 취급하지 않는다. 계정/Branch 상태 조합·최소 선택 응답/현재 사실 계약·경합은 후속이다.

비활성 Trainer 과거 수업 대행 인가(2026-10-12, BR-OPS-015): 현재 검증된 관리자 Caller/Organization·대행 행위 Scope와 실제 대상 관계/비활성화 전 수업 사실을 Backend에서 확인한다. 실제 수행자를 Caller/현재 새 담당으로 대체하지 않으며 과거 Trainer 참조를 새 담당 지정과 구분한다. 비활성 Trainer 역할의 직접 등록/회원 정보 접근·Trainer 계정 로그인은 복구하지 않는다. 대행 인가의 현재 사실 검증/최소 선택·과거 사실 판정은 게이트이며 기존 Trainer Home Branch 기반 보상 설정 공개 제한/별도 추가실적·정산 권한을 우회하지 않는다.

2026-10-12 사용자 확정(비활성화 전 누락 수업 대행 등록의 Branch Admin 기준 질문 1번): Master Admin은 자신의 Organization 전체, Branch Admin은 처리 시점 현재 관리 Branch가 실제 수업의 Performed Branch인 경우에만 대행 등록할 수 있다. Trainer 현재 Home Branch가 다른 지점이어도 실제 수업이 자신의 관리 지점에서 진행됐다면 허용한다. Trainer Home Branch·Member Home Branch·Pass Issued Branch 또는 과거 관리자 Scope만으로 대행 권한을 얻지 않는다(BR-OPS-015).

2026-10-12 일괄 승인 반영: A1–A10의 승인된 인증/로그인·링크 수명/철회/Actor·마지막 Master 보호/MFA 시점을 적용한다. A5는 모든 역할 동일 idle 30분/absolute 8시간이다. 관리 역할/관리 Branch 변경 후 구 인증/Scope로 접근 불가, Trainer 비활성만으로 독립 관리자 권한을 종료하지 않는다. 운영 전 관리자 MFA 필수이며 개발 검사와 운영 허용은 별개다. JWT는 후속 재검토 후보이고 CSRF/쿠키/해시·MFA 수단/복구·경합은 구현 상세 검증이 필요하다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch).

2026-10-12 C 일괄 승인 반영: C1–C6의 현재 인증/Scope/CSRF·만료/MFA 경계를 유지하고 5분 이내 관리 비밀번호 재확인 후보는 미채택이다. 본인 변경의 현재 암호 확인은 별개다. 실패 제한·암호/ID 변경·reset의 전 로그인 철회/마지막 Master 보호는 구현 후 실제 경합까지 검증해야 한다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 E 일괄 승인 반영: E1/E2의 설치/수신자 확인·전달 방식과 E3/E4의 ID 대소문자 비교/이전 ID 예약을 적용한다. E5는 계정 전체가 아닌 대상 Operator/Trainer 역할의 현재 지점 Scope 인가와 Master 전용 경계·독립 겸임 역할을 검증한다. E6 일반 차단 해제의 유효 암호만 허용/폐기 인증·무효 암호·MFA/Trainer 상태 비복원을 유지한다. 실제 보안 구현/운영 인수 완료가 아니다. [2026-10-12 E 일괄 승인](product-decisions.md#review-20261012-e-batch)

2026-10-12 G 일괄 승인 반영: G1–G5의 비활성 지점 업무는 현재 계정/역할·Organization과 기존 행위별 Scope를 서버에서 검증한다. 유효 사용자 기존 조회, 비활성화 전 수업 처리, 다른 활성 지점 이용 및 권한별 이동을 허용하되 타 지점 전체 자료·Compensation Setting·인증 감사 권한을 늘리지 않는다. 계정/Trainer 자체 비활성·철회/만료 인증은 유지한다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). 구체 계약/감사 구조·실제 검증은 후속이다.

2026-10-12 H 일괄 승인 반영: H2–H4: 비지원 실적 수정/취소·대상 정정은 현재 Trainer Home Branch 관리 Scope로 단계별 인가하고, Trainer 단독 월 정산 읽기는 v1 거부한다. 기존 관리자 겸임 Scope/본인 PT 내역 읽기는 유지한다. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch). 실제 검사/업무 구현은 후속이다.

2026-10-12 J 일괄 승인 반영: 회원 등록/이름·전화번호 수정은 Master Organization 또는 Branch Admin·Operator의 지정/현재 Member Home Branch 범위다. Member 비활성화/재활성화는 Master Organization/Branch Admin 현재 Member Home Branch만이며 Operator/Trainer 단독은 불가다. 기존 겸임의 독립 Scope·이동 권한·최소 공개/다른 데이터 접근 제한을 유지한다. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch). 실제 업무 테스트는 미구성·미실행이다.

2026-10-12 K 일괄 승인 반영: Trainer 신규 등록/이름·연락처 수정은 Master Organization/Branch Admin 지정·현재 Trainer Home 기준이며 OP/Trainer 단독은 불가다. PT 날짜/시각 오류의 취소 후 재등록은 각 단계 기존 PT Scope와 영향받는 각 확정 월의 현재 Home Branch 관리자 인가를 구분한다. [2026-10-12 K 일괄 승인](product-decisions.md#review-20261012-k-batch). 실제 업무 검사 미구성·미실행이다.

추가 인가 경계(N1/N2): PT 기록 권한과 수업별 보상 금액 권한을 분리한다. 비관리자 Trainer 본인 금액 및 현재 다른 Home Branch Trainer의 자기 Performed Branch 수업 금액은 수행 지점 Branch Admin에게 공개하지 않는다. 현재 Home/현재 Caller/행위별 Scope·겸임 독립 관리 권한을 검증하고 기록 읽기·정정/본인 수행 사실만으로 금액 접근을 허용하지 않는다(BR-PAY-021; [N 승인](product-decisions.md#review-20261013-n-batch); V-108/109 미구성·미실행).

담당/개별 지원 본인 등록(O1/O2): 검증된 현재 Caller/Trainer와 허용 Member 관계를 확인한 뒤 서버가 해당 Member 전체 적격 Pass에서 선택한다. Pass 담당/Issued Branch만으로 후보를 좁히거나 후보 사용을 다른 회원/개별 Pass·Trainer PT/보상 금액 공개로 확대하지 않는다. 지원 지정/해제는 현재 Member Home 관리자/Master Scope·감사 조건을 유지하며 과거 지원 허용 시간 정책은 BR-OPS-027(P1/P2), 역사 사실/계약은 후속이다(BR-OPS-026; [O 승인](product-decisions.md#review-20261013-o-batch); V-110/111 미구성·미실행).

P1/P2 인가: 현재 유효한 지원 관계의 지정 전 본인 수업 등록과 해제 후 실제 허용 기간 수업의 제한된 늦은 등록을 구분한다. 지정 이력은 소급 변경하지 않는다. 현재 계정/Trainer·실제 수행/과거 허용 사실을 검증하며 해제 후 Member 목록/검색/상세·전화번호 접근은 복원하지 않는다. 최소 명령/과거 대상 식별·공개/오류 계약을 설계하고 과거 한때 지원 사실/요청 표시만으로 무제한 인가하지 않는다(BR-OPS-027; [P 승인](product-decisions.md#review-20261013-p-batch); V-112/113 미구성·미실행).

R2 필드/대상 인가: Branch Admin의 지점명/대표 연락처 수정은 현재 자기 단일 Branch/Organization과 허용 두 필드만 검증한다. 직접 ID·과거 Scope/요청 role·다른 상태/관리자 필드 주입으로 타 지점 또는 지점 생성/운영 상태/계정 Scope를 변경할 수 없다. Master의 기존 Organization 범위·겸임 독립 Scope와 중요 감사는 유지한다(BR-OPS-030; [R 승인](product-decisions.md#review-20261013-r-batch); V-117 미구성·미실행).

S 이력 인가: 정산의 이전 확정본·해제/재확정과 세 보상 설정 변경 이력은 Master Organization/현재 Trainer Home Branch Admin의 각 조회 시점 Scope를 검증한다. 목록/검색·직접 ID/상세·제공되는 중첩 응답도 같고 이전 Home/Performed·원래 변경자·과거 조회만으로 접근하지 못한다. Operator/Trainer 단독 금지·겸임 독립 관리 Scope·C7 인증/계정 관리 감사 Master 전용을 유지한다(BR-PAY-023; [S 승인](product-decisions.md#review-20261013-s-batch); V-118/119 미구성·미실행).

U1 상태/행위 인가: 수동 만료 자체로 담당 교체를 거부하지 않고 기존 Member 현재 Home 관리자 Scope·실제 활성 대상 Trainer/Organization을 검증한다. 타 Branch/Organization·Issued/Trainer Home/Performed/과거 Scope만의 권한 주장을 차단하며 새 담당/이전 담당의 후속 회원 조회는 현재 관계로 다시 검증한다. 만료 해제/조정·새 수업 사용·보상 접근 권한은 추가하지 않는다(BR-OPS-008/005; [U 승인](product-decisions.md#review-20261013-u-batch); V-122 미구성·미실행).

V1 과거 소속 정정 인가: 검증된 현재 Master·대상 Trainer/Member/정정 소속 사실의 자기 Organization 범위와 사유를 Backend에서 확인한다. Branch Admin의 현재 Member 관리/이동 권한·과거 Scope/직접 ID·위조 role로 정정할 수 없다. 겸임의 독립 Master Scope와 기존 업무별 읽기/정정·보상/정산 권한을 유지하고 과거 인가/역할·계정/지원 이력을 자동 복원하지 않는다(BR-OPS-032; [V 승인](product-decisions.md#review-20261013-v-batch); V-123 미구성·미실행).

W1/W2 인가/완전성: 과거 Trainer Home 오류의 수업 분류 정정은 현재 Master Organization 전용, 지원 금액 입력/정산 해제·확정은 기존 행위별 현재 Scope로 각각 검증한다. 분류 정정 권한으로 타 Home 수업 금액/설정·정산 공개를 확대하지 않고 영향 건 정정이 남은 해당 Trainer·월의 확정/재확정을 거부한다. 경고/위조 완료·직접 ID/과거 Scope로 우회하지 못한다(BR-OPS-033/PAY-024; [W 승인](product-decisions.md#review-20261013-w-batch); V-124/125 미구성·미실행).

AB3–AB5 확정: 후속 활성 계정 reset 링크30분, 운영 Master/Branch Admin 비밀번호 뒤 Passkey 추가 검증(서버 사용자 검증 확인), 전체 Master 로그인 불가의 조직 업무책임자 승인/별도 시스템 운영담당자 비상 복구를 적용한다. 생체 원본/Passkey 개인키는 서버에서 수집·저장하지 않는다. 정상 계정/보상 업무의 기존 Scope/승인 정책과 S1 개발 우선은 유지하며 MFA 등록/분실·복구 자격/본인확인·감사/철회·운영 검증은 후속이다([AB 승인](product-decisions.md#review-20261013-ab-batch); V-134–136 미구성·미실행).

2026-10-16 MFA M1/M2: 관리자 계정의 복수 Passkey 등록과 로그인 시 하나 사용을 허용한다. 같은 Organization의 다른 정상 Master만 관리자 Passkey 분실의 본인 확인·기존 Passkey/모든 AuthSession 폐기·일회용 링크 재등록을 처리한다. Branch Admin/타 조직 접근·비밀번호 reset/차단 해제·회수 역할 복원·MFA 미충족 운영 접근으로 확대하지 않는다. AB5 모든 Master 로그인 불가 비상 복구와 생체 원본/개인키 비수집을 유지한다. 추가 등록/삭제·마지막 인증수단 보호와 실제 권한/철회·원자성/재사용/실패·브라우저 검증은 후속 계획이다([승인](product-decisions.md#review-20261016-mfa-m-batch); V-135 미구성·미실행).

2026-10-18 MFA M3–M6: 첫 등록은 설치/본인 최초 설정의 신뢰 경로로 제한하고 정상 MFA 로그인한 본인에게 추가 등록을 허용한다. 마지막 Passkey 본인 삭제는 금지하며 다른 유효 key가 남아야 삭제 가능하다. M2 분실 재등록 링크는30분, 추가 Master 신규 발급은 같은 조직 정상 Master 전용이다. AB4/AB5·현재 인가/철회·감사/마지막 Master 보호를 유지한다. 구체 계약과 실제 등록/로그인·삭제/복구/추가 Master의 보안/원자성/경합 검증은 증분별 후속이다([승인](product-decisions.md#review-20261018-mfa-m3-m6); V-135 계획, 구현/실제 검증 완료 아님).

2026-10-18 MFA M7/M8: 본인 Passkey 삭제 성공은 현재 기기 포함 전 로그인 철회와 함께 처리한다. 마지막 key 삭제는 금지하며 실패 시 key/로그인을 보존하는 원자성·경합은 후속 검증한다. Master 본인 관리자 reset은 금지하고 C3 현재 암호 확인 본인 변경/다른 정상 Master reset·AB5를 유지한다. 해당 후속 구현/실제 검증은 미완료다([승인](product-decisions.md#review-20261018-mfa-m7-m8)).

<a id="nfr-002"></a>
## NFR-002. 업무 데이터 정합성

출처/상태: APPROVED-TO-BE

제품 필요: Session 생성·정정/취소와 Pass 잔여·정산 결과가 일치해야 한다. 부분 반영을 정상 완료로 취급하지 않는다.

수용 기준 / 남은 상세: 승인된 전후 수치 사례로 잔여와 월 지급액을 대사한다. 업무 단위 일관성은 필요하나 트랜잭션 구현 방식은 정하지 않는다. 지원 수업은 기록·Pass 차감을 먼저 완료하고 관리자 금액 저장 시 보상을 확정하는 두 업무 단계다. 미입력은 확정 0원과 구분하고 추적한다. 해당 Trainer의 해당 월 정산 대상 지원 수업에 금액 미입력 건이 하나라도 있으면 그 Trainer·월 정산을 확정할 수 없다. 타 지점 지원 수업 보상은 권한 있는 관리자가 사유를 기록하면 0원으로 명시적으로 확정할 수 있다. 사유 없는 0원 입력은 보상 확정이 불가하다. 사유를 남기고 확정한 0원은 금액 미입력이 아니므로 그 건으로 월 정산 확정을 차단하지 않는다. 다른 미입력 건이 남으면 기존 차단 조건을 유지한다. 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin에게 Organization 전체, Branch Admin에게 대상 Trainer Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안의 본인 건도 허용하고 변경 이력을 남긴다. 월 정산 확정 전 지원 수업 보상 금액 수정은 Master Admin·Branch Admin 모두 관리 범위 안에서 본인 건을 포함해 별도 승인 없이 저장 성공 즉시 반영한다. Master나 다른 관리자의 승인 대기를 두지 않으며 권한 검증과 변경 이력을 유지한다. 월 정산 확정 전 지원 수업 보상 금액의 모든 수정에는 변경 사유가 필수다. 양수 간 변경·0원에서 양수로 변경·양수에서 0원으로 변경 모두 적용하며, 사유 없이는 금액을 수정할 수 없다. 변경 전후 금액·변경 사유·수정자·수정 시점을 이력으로 남긴다. 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 지원 수업 보상 금액 오류 정정의 월 정산 확정 해제·재확정은 Master Admin은 Organization 전체 Trainer, Branch Admin은 자신의 관리 Branch를 Home Branch로 가진 Trainer에 대해 허용한다. Branch Admin이 자신의 관리 Branch를 Home Branch로 가진 Trainer의 지원 수업 보상 정정을 위해 월 정산을 확정 해제·재확정할 때는 Master의 별도 승인을 두지 않는다. Master 승인 대기 단계 없이 관리 범위 안에서 직접 처리하며 이전 확정본과 해제·재확정 이력 및 감사를 유지한다. 지원 수업 보상 정정의 월 정산 확정 해제에는 사유가 필수이며, 사유 없이 해제할 수 없다. 사유·해제자·시점을 이력으로 남긴다. 과거 지원 수업 보상 정정·해당 월 정산 확정 해제/재확정에서 Branch Admin의 권한은 각 업무 처리 시점의 Trainer 현재 Home Branch를 기준으로 검증한다. 이전 소속만으로 권한을 유지하지 않으며 Master Admin의 Organization 전체 권한은 유지한다. 남은 정정·취소 절차는 BR-009/013 등 관련 OPEN을 따른다. 이 조건은 Backend의 월 정산 확정 경로에서 검증해야 하며 UI 제한만으로 충족하지 않는다. BR-001–007/013.

지원 수업 비용 집계 정합성(2026-10-11 사용자 확정): 타 지점 지원 수업의 전체 보상으로 확정한 Additional Performance 금액은 해당 수업의 실제 Performed Branch 비용으로 집계한다. Trainer 월 정산의 한 번 합산과 같은 유효 보상 금액을 기준으로 대사할 수 있어야 한다. 비용 집계를 별도 지급/중복 추가실적으로 취급하지 않는다. 소속 이동만으로 과거 수행 지점·비용 귀속이 바뀌지 않도록 하고 허용된 정정/취소와 이전 확정본 보존의 일치를 후속 검증한다. 구체 조회 계약·집계 갱신/버전 전략은 후속 Architecture 대상이다.

이동월 기본급 비용 정합성(2026-10-11 사용자 확정): 월중 Trainer 지점 이동이 있는 달의 해당 월 적용 기본급 비용은 대상 월의 월말 Home Branch 한 곳에 전액 귀속한다. 해당 월 정산의 적용 기본급과 같은 금액을 한 지점에 한 번 집계하며 수동 적용액 우선·명시적 0원/미입력 구분·과거 확정본 보존을 유지한다. 이후 소속 이동만으로 과거 비용 지점을 바꾸거나 비용 귀속과 인가 Scope를 혼동하지 않는다. 월말 소속 사실·금액·정정 이력을 대사하는 구체 계약/저장/조회는 후속 검증 대상이다.

일반 PT 수당 비용 정합성(2026-10-11 사용자 확정): 일반 Session Payment는 해당 PT 진행 기록의 실제 Performed Branch 비용으로 집계한다. 이미 확정된 수업별 지급액을 지점별로 합산하며 대상 월말 Home Branch로 전액을 모으지 않는다. 지점별 비용 합계와 같은 유효 일반 지급 입력의 Trainer 합계를 대사할 수 있어야 한다. 현재 보상 설정 재계산·합계의 추가 올림·지원 수업 일반 지급 중복 합산·비용 귀속만을 근거로 한 권한 확대를 방지한다. 이후 소속 이동만으로 과거 수행 지점에 따른 비용 귀속을 바꾸지 않으며 허용된 정정/취소와 이전 확정본 보존의 일치를 후속 검증한다.

지원 수업 외 추가실적 비용 정합성(2026-10-11 사용자 확정): 지원 수업 외 Additional Performance의 비용은 실적 발생 당시 대상 Trainer의 Home Branch에 귀속한다. 등록 시점·금액 확정 시점·대상 월말 또는 조회 시점의 소속으로 대체하지 않는다. 같은 유효 추가실적의 금액을 Trainer 월 정산과 지점 비용에서 대사하며 별도 지급·중복 실적을 만들지 않는다. 이후 이동/등록/조회 시점의 소속으로 과거 비용 지점을 바꾸거나 비용 귀속을 인가 Scope로 대체하지 않는다. 허용된 정정/취소와 이전 확정본 보존의 일치·발생 시점/소속 사실 계약·조회/갱신/버전 전략은 후속 검토/검증 대상이다.

관련 요구·결정: PD-007/008/010/012; PR-003/008/009/010. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

2026-10-12 일괄 승인 반영: B3/B4/B5/B6: 최초 활성 담당/상품 횟수 부여·별도 관리자 잔여 초과 추가는 원본 조건/과거 지급을 보존한다. 지점 비활성화로 기존 소속/Pass/잔여·이력/정산을 삭제하거나 자동 이동하지 않는다. 거부/실패 시 요청 직전 데이터와 필수 감사 일관성을 검증해야 한다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch).

2026-10-12 C 일괄 승인 반영: C10/C12/C13: PT 참가자 오류는 취소/정정 재등록 연결과 Pass 복원/새 선택·지급/AP/정산을 일관되게 처리한다. 수동 조정 음수 거부와 소진 후 재사용/수동 만료 유지의 각 승인 조건을 적용한다. API/UoW/경합 구현 검증은 아직 없다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 E 일괄 승인 반영: E3/E4의 대소문자 유일성/예약과 발급·ID 변경이 경합해도 다른 계정에 같은 현재/예약 ID를 부여하지 않아야 한다. E5 허용 역할 변경/감사 실패는 현재 권한·연결/다른 역할/이력을 보존하고 Master 전용 이동을 회수/재부여로 우회하지 않는다. 원자성/잠금·역할/소속/계정 상태 경합은 후속 검증이다. [2026-10-12 E 일괄 승인](product-decisions.md#review-20261012-e-batch)

2026-10-12 G 일괄 승인 반영: G2/G3/G4/G5: 비활성 지점의 과거 수업 처리·타 활성 지점 Pass 사용·명시적 이동은 기존 잔여/복원/지급/AP·확정 월 해제/재확정/원본 보존과 실패 원자성을 적용한다. Home/Issued/Performed Branch와 실제 진행/생성 시점을 구분하고 과거 지급/비용 귀속을 현재 소속·지점 상태로 덮어쓰지 않는다. 활성 지점 사용의 정상 1회 차감과 비활성 Performed Branch 신규 수업 거부를 함께 검증해야 한다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). 구체 계약/감사 구조·실제 검증은 후속이다.

2026-10-12 H 일괄 승인 반영: H2/H3: 비지원 실적 취소는 원본/금액·귀속 이력 보존 및 유효 합산 제외다. 잘못된 Trainer/발생 날짜는 취소 후 재등록·연결하고 영향받는 각 확정 Trainer/월의 해제/처리/재확정·이전본 보존과 필수 변경 실패 원자성을 따른다. 실적 취소만으로 일반 PT/Pass/일반 지급을 바꾸지 않는다. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch). 실제 검사/업무 구현은 후속이다.

2026-10-12 J 일괄 승인 반영: Member 자체 비활성화는 잔여가 남아 있어도 가능하되 기존 Pass 잔여/조건/관계·과거 PT/확정 지급/정산을 보존하고 새 Pass/비활성 기간 실제 수업을 차단한다. 잔여 0은 자동 Member 비활성화 사유가 아니다. 같은 Member 재활성화가 개별 만료 해제/과거 지급 자동 재계산 또는 비활성 기간 수업 유효화를 의미하지 않는다. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch). 실제 업무 테스트는 미구성·미실행이다.

2026-10-12 K 일괄 승인 반영: 날짜/시각 오류는 원본 취소/보존·기존 소비 복원/수업 보상 합산 제외 후 올바르게 재등록한다. 새 실제 시점의 관계/상태·Pass와 현재 잔여/인가·정산을 재검증하고 기존 우선순위로 재선택/1회 차감·새 일반 지급 생성 시점 설정을 적용한다. 취소/재등록 실패·여러 월/연결·원자성 계약은 후속이다. [2026-10-12 K 일괄 승인](product-decisions.md#review-20261012-k-batch). 실제 업무 검사 미구성·미실행이다.

O1/O2 불변조건: 적격 후보는 해당 Member의 다른 담당분을 포함하되 실제 수업 당시 발급/사용 가능·현재 잔여 > 0·기존 상태/만료 예외/정산 조건을 검증하고 FIXED_AMOUNT 우선/동일 Type FIFO로 선택한다. 차감/진행 기록/필요한 확정 지급은 기존 업무 원자성 원칙을 따른다. 담당/지점 사실은 자동 변경하지 않으며 일반 지급은 실제 수행자 생성 시점 설정, 보상 구분은 실제 수업 당시 Trainer Home/Performed다. 구체 저장/계약/UoW/잠금은 PROPOSED이며 실행 검증 완료가 아니다(BR-OPS-026; [O 승인](product-decisions.md#review-20261013-o-batch); V-110/111 미구성·미실행).

P1/P2 이력/원자성: 실제 수업일과 지원 지정/해제의 실제 이력을 별도로 보존하며 현재 유효 지원에 의한 지정 전 등록을 과거 허용 사실로 바꾸지 않는다. 실제 허용 기간의 해제 후 등록은 기존 전체 적격 Pass/현재 잔여·수업/필요한 지급/진행 월 정산 조건을 함께 검증한다. 실패/권한 거부/미해제 확정 월·잔여 부족 시 일부 변경을 남기지 않는 기존 원칙을 적용한다. 실제 사실 확인 불가/충돌·이력/최소 계약·UoW/동시 지정·해제/월 확정 경합은 후속이다(BR-OPS-027; [P 승인](product-decisions.md#review-20261013-p-batch); V-112/113 미구성·미실행).

Q1 최초 등록 완료의 일관성: Trainer 등록/필수 보상 세 값·기본급 시작 월/필요한 최초 감사의 인가·입력을 검증하고 누락/실패를 등록 완료로 보고하지 않는다. 누락을 임의 0원/0%/현재 월로 대체하거나 사용할 수 있는 정상 Trainer만 일부 남기지 않도록 설계한다. 결합 입력이 같은 DB 테이블·소유권/구체 UoW 승인은 아니며 저장/계약·실패 재시도/경합은 PROPOSED다(BR-OPS-028; [Q 승인](product-decisions.md#review-20261013-q-batch); V-114 미구성·미실행).

T1/T2 일관성: 신규 Pass 발급 완료 시각/발급 당시 조건·최초 횟수/감사와 실제 수업 당시 발급된 후보 판정을 연결한다. 실패한 발급을 완료된 과거 Pass로 취급하거나 이후 발급·클라이언트 과거 날짜로 적격 후보를 만들지 않는다. 별도 사용 시작일 없이 기존 상태/잔여·인가 조건을 적용하고 만료 전 늦은 등록/원본·과거 확정 결과 보존을 유지한다. 발급/사용 경합·commit 응답 유실과 최소 계약은 후속이다(BR-OPS-031; [T 승인](product-decisions.md#review-20261013-t-batch); V-120/121 미구성·미실행).

<a id="nfr-003"></a>
## NFR-003. 동시 작업과 재시도

출처/상태: NEW-CANDIDATE — 승인된 정합성을 위한 검증 후보

제품 필요: 동시 운영이나 재시도로 Session과 잔여의 중복 반영·변경 유실이 발생하지 않는 결과가 필요하다.

수용 기준 / 남은 상세: 이중 제출·응답 유실·동시 정정 사례의 기대 결과를 상세화한다. 같은 날짜의 별개 Session을 중복으로 단정하지 않는다. BR-008, ARCH-004.

관련 요구·결정: PD-010/021; PR-008/009. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

2026-10-12 J 일괄 승인 반영: Member 등록/이름·전화번호 수정·상태 변경과 Home/역할/Branch 변경·Pass 발급/실제 수업/소급 처리/정산 확정의 경합에서 현재 인가와 해당 실제 수업 시점 상태를 구분한다. 비활성 완료 이후 새 발급/비활성 기간 수업을 오래된 선택 결과/역할/재시도로 우회하지 못해야 한다. 순서/잠금·UoW/실패 계약은 후속이다. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch). 실제 업무 테스트는 미구성·미실행이다.

<a id="nfr-004"></a>
## NFR-004. 중요 행위 감사

출처/상태: APPROVED-TO-BE

제품 필요: Session·Pass 잔여 변경, 보상 설정 세 항목의 변경, 추가실적 생성·정정·취소, 계정/권한·중요 Branch 관리 행위를 감사할 수 있어야 한다.

수용 기준 / 남은 상세: 모든 보상 설정 변경(최초 설정 포함)에 대상 Trainer, 변경 항목, 변경 전 값, 변경 후 값, 변경 Actor, Actor의 권한 및 Branch Context, 변경 시점을 추적한다. 별도 Master Admin 승인 없이 변경 가능하며 변경 요청→승인 대기→승인→반영 절차를 추가하지 않는다. 이 결정은 추가실적 승인이나 월 정산 마감/확정 절차를 면제하지 않는다. 감사 경로의 설정 우회 노출도 금지한다. 저장 구조·조회 구현은 Architecture, 보존 기간은 LEGAL-001이다.

관련 요구·결정: PD-010/022; PR-027. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

기존 사용자 일관성 지시 적용(2026-10-11): Member 소속 변경은 관리 Scope에 영향을 주는 중요 변경이므로 기존 중요 행위/인가 변경의 이력·감사 원칙을 적용한다. 대상 Member·변경 전후 Home Branch·변경 Actor/권한·Branch Context·시점을 추적한다. 이번 권한 승인이 감사 저장 구조나 이동 적용 시점·예약/소급·변경 사유 입력/정정 정책을 확정한 것은 아니다(NFR-004, MB-002).

기존 사용자 일관성 지시 적용(2026-10-11): 일반 담당 교체도 저장 완료 후 변경된 현재 담당을 적용하고 미래 예약 변경 절차를 추가하지 않는다. 중요 Pass/인가 관계 변경의 이력·감사 원칙에 따라 대상 Pass/Member·변경 전후 담당 Trainer·변경 Actor/권한·Branch Context·시점을 추적한다. 저장 실패 시 기존 담당과 잔여/이력을 유지한다. 저장/UoW·감사 구조·동시성 계약을 승인한 것은 아니다(NFR-001/004, BR-OPS-007/008).

2026-10-12 Pass 수동 횟수 조정 감사 적용(BR-OPS-009, PR-003/030): 기존 사유/이력 원칙을 적용해 대상 Pass/Member·변경 전후 Remaining·증감량·사유·처리 Actor/Role·Branch Context·시점을 추적한다. 사유는 필수이며 현재 잔여만 이력 없이 덮어쓰지 않는다. 기존 사용자 일관성 지시에 따라 허용된 관리자 Scope 안에서 별도 Master 승인 대기 없이 처리한다. 거부/저장 실패 시 조정/이력·필수 감사와 잔여에 일부 확정을 남기지 않는 정합성 원칙을 따른다. 저장/조회·UoW는 Architecture 후속이고 보존/열람 범위는 해당 기존 게이트를 유지한다.

2026-10-12 타 지점 새 Pass 발급의 기존 감사 원칙 적용(BR-OPS-010): Pass 생성/최초 잔여 변경도 기존 중요 Pass 행위 감사에 포함하며 실제 발급 Branch Context·대상 Member/Pass·발급 조건·현재 발급 Actor/권한·시점을 추적할 후속 계약을 설계한다. 기존 사용자 일관성 지시에 따라 신규 Pass/발급 조건과 필수 감사에 일부만 확정되는 상태를 허용하지 않는 정합성 원칙을 적용한다. 구체 저장/UoW·공개 필드/감사 열람/보존은 해당 Architecture/Product 게이트 후속이며 회원 연락처 등 불필요한 개인정보를 일반 로그에 복사하지 않는다.

Operator 최초 계정 발급(2026-10-12, BR-OPS-011)에 기존 감사/일관성 원칙을 적용한다. 기존 중요 계정/권한 변경의 감사·일관성 원칙 적용: 대상 계정·Operator 역할·최초 업무 Branch·발급 Actor/현재 권한·Branch Context·시점을 추적한다. 비밀번호/해시·설정 토큰·전체 설정 링크를 일반 로그/감사에 복사하지 않는다. 거부·실패 시 계정/역할/최초 Scope·필수 감사 중 일부만 확정되는 상태를 남기지 않는 경계를 설계한다. 구체 감사 저장/열람·보존, 계정 활성화·역할/Scope 표현·UoW/동시성은 후속이며 새로운 필수 입력 사유를 추가하지 않는다.

Operator 업무 Branch 변경(2026-10-12, BR-OPS-011)에도 중요 계정/권한 변경의 기존 감사·실패 보존 원칙을 적용한다. 대상 계정·변경 전후 Operator Branch·변경 Actor/현재 Master 권한·Branch Context·시점을 추적하며 변경/필수 감사 일부만 확정되는 상태를 남기지 않는 경계를 설계한다. 구체 저장/열람·보존/UoW는 후속이고 새로운 필수 사유 입력을 추가하지 않는다.

신규 Trainer 로그인 계정 발급(2026-10-12, BR-OPS-012)에 기존 중요 계정/권한 감사·실패 일관성을 적용한다. 대상 계정/Trainer·발급 시 Trainer Home Branch·역할/Trainer 연결·발급 Actor/현재 권한·Branch Context·시점을 추적하며 비밀번호/해시·토큰·전체 설정 링크는 일반 로그/감사에 남기지 않는다. 계정·역할·Trainer 연결/필수 감사 중 일부만 확정되지 않는 경계를 설계한다. 저장/조회·보존/UoW·전달/재발급·활성화는 후속이며 새 필수 사유를 정하지 않는다.

Trainer Home Branch 변경(2026-10-12, BR-OPS-013)은 중요 소속/인가 변경의 기존 감사·실패 일관성을 적용한다. 대상 Trainer·변경 전후 Home Branch·현재 Master Actor/권한·Branch Context·적용/변경 시점을 추적하며 현재 소속·소속 변경 이력/필수 감사 일부만 확정되는 상태를 남기지 않는 경계를 설계한다. 수업 당시 소속 확인에 필요한 사실을 보존하되 과거 사실 누락/오류 정정 정책·구체 저장/조회·보존/UoW·경합은 후속이다. 새 필수 변경 사유나 감사 구조를 확정하지 않는다.

Trainer 비활성화(2026-10-12, BR-OPS-014)에도 기존 중요 상태/권한 변경 감사·실패 보존 원칙을 적용한다. 대상 Trainer/계정·전후 Trainer 상태·처리 Actor/당시 권한·Branch Context·시점을 추적하고 상태 변경/필수 감사 일부만 확정하지 않는 경계를 설계한다. 비활성화 Actor는 승인된 현재 관리자 Scope로 검증하고 새 필수 사유를 추가하지 않으며 구체 저장/열람/보존·UoW는 후속이다.

Trainer 비활성화의 승인된 Actor/Scope(2026-10-12, BR-OPS-014): Master Organization 전체/Branch Admin 현재 Trainer Home Branch 인가 결과와 당시 권한/Branch Context를 기존 상태 변경 감사에 포함한다. 대상/전후 상태·처리자/시점 보존과 실패 일관성 원칙을 유지하며 재활성화/계정 전체 차단 권한·새 필수 사유·감사 저장/열람/보존 구조를 추가 승인하지 않는다.

담당 Pass 유지의 감사 경계(2026-10-12, BR-OPS-014): Trainer 비활성화에는 기존 Trainer 상태 변경/Actor/권한·Branch Context/시점 이력·감사와 실패 보존 원칙을 적용한다. 담당이 그대로인 Pass에 실제로 없던 담당 교체 이력을 만들지 않는다. 나중 별도 교체를 수행하면 BR-OPS-008의 전후 담당/처리자/시점 이력·감사를 남긴다. 구체 저장/UoW·경합 검증은 후속이다.

누락 수업 관리자 대행 감사(2026-10-12, BR-OPS-015): 기존 중요 PT/Pass/권한 행위 감사 원칙을 적용해 실제 수행 Trainer·입력 관리자/당시 권한·Branch Context·실제 수업일/기록 시점·Member/Pass/PT 대상과 차감/필요 지급 결과를 구분해 추적한다. 입력 관리자를 수행자로 덮어쓰지 않으며 상태/기록/차감/필요 지급·필수 감사의 부분 확정을 남기지 않는 경계를 검토한다. 지원 수업의 이후 별도 금액 입력 원칙을 유지한다. 추가 사유/증빙 필수 여부·저장/공개/보존/UoW·경합은 후속이며 비밀번호/토큰·민감 설정을 일반 로그에 복사하지 않는다.

2026-10-12 C 일괄 승인 반영: C7/C8: 인증/계정 관리 감사는 자기 Organization Master만 열람한다. 로그인 최소 사건은 계정·시각·행위·결과이고 원문 IP/브라우저 정보·비밀을 남기지 않는다. 계정 관리 필수 전후 값/Actor 감사와 보상 등 다른 업무 감사 권한·민감정보 제한은 유지한다. 보존/삭제는 미정이다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 E 일괄 승인 반영: E5 Branch Admin에게 허용한 역할 쓰기는 인증/계정 감사 읽기를 허용하지 않는다. 기존 대상/변경 전후/Actor·Role/Scope·시각의 감사와 실패 일관성을 유지하고 C7 Master 전용 읽기/C8 로그인 최소 정보·비밀 기록 금지를 따른다. 설치·링크 전달/역할/ID 예약의 구체 계약/보존은 후속이다. [2026-10-12 E 일괄 승인](product-decisions.md#review-20261012-e-batch)

2026-10-12 G 일괄 승인 반영: G2/G5의 기존 중요 업무에 적용되는 사유·전후 값/수량·처리 Actor/Role·Branch Context/시점 및 이전 확정본/이력 보존 의무를 지점 비활성 때문에 생략하지 않는다. 기존 수집 범위를 확대하거나 조회만으로 민감 설정/인증 감사를 공개하지 않는다. [2026-10-12 G 일괄 승인](product-decisions.md#review-20261012-g-batch). 구체 계약/감사 구조·실제 검증은 후속이다.

2026-10-12 H 일괄 승인 반영: H2/H3: 비지원 실적 내용 수정/취소는 사유·전후 내용/상태/금액·Actor/Role/Branch Context/시점 이력·감사 필수다. 원래 건 취소와 새 등록을 추적하고 이전 확정본을 보존한다. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch). 실제 검사/업무 구현은 후속이다.

2026-10-12 J 일괄 승인 반영: Member 비활성화/재활성화에 기존 중요 상태 변경의 대상 Member·전후 상태·Actor/Role·Branch Context·시점 이력을 적용한다. 회원 기본정보 수정의 개인정보 제한·기존 중요 변경 감사를 유지하고 일반 로그에 실제 연락처/민감정보를 남기지 않는다. 감사의 저장/열람·보존/삭제 계약은 후속이다. [2026-10-12 J 일괄 승인](product-decisions.md#review-20261012-j-batch). 실제 업무 테스트는 미구성·미실행이다.

2026-10-12 K 일괄 승인 반영: PT 날짜/시각 정정의 원본/취소/새 기록 연결·Actor/시점/사유/이전 확정본을 기존 감사 요구로 추적한다. Trainer 기본정보 관리도 기존 중요 변경 감사/개인정보 제한을 적용하고 실제 연락처를 일반 로그에 복사하지 않는다. [2026-10-12 K 일괄 승인](product-decisions.md#review-20261012-k-batch). 실제 업무 검사 미구성·미실행이다.

M1의 미사용 발급 오류 처리에는 기존 수동 만료 사유/전후 상태·Actor/현재 Issued Branch Scope·시점 이력/감사와 새 발급의 별도 중요 변경 감사를 적용한다. 원래 Pass의 회원/조건/담당·잔여/역사 기록을 새 발급으로 덮어쓰거나 삭제하지 않는다. 관련성/단계별 실패·재시도/저장·UoW는 후속이며 별도 발급 취소 기능은 v1 제외다(BR-OPS-025; [M 승인](product-decisions.md#review-20261013-m-batch); V-106 미구성·미실행).

R1/R2 중요 변경 추적: Trainer 필수 전화번호의 인가된 등록/변경과 Branch 지점명/대표 연락처 수정은 기존 중요 감사 원칙을 따른다. 지점 수정은 대상 Branch·항목/전후·Actor/Role/Branch Context·시점을 추적한다. 실제 번호/대표 연락처를 일반 로그/문서에 복사하지 않으며 감사의 저장/필드 공개·보존·최소 오류 계약은 후속이다(BR-OPS-029/030; [R 승인](product-decisions.md#review-20261013-r-batch); V-116/117 미구성·미실행).

S 이력 사실/공개: 정산 이전 버전·정정 이유/변경자/시점과 세 보상 설정 최초/변경 전후 값·당시 Actor/Role/Branch Context·시점은 보존하고 BR-PAY-023의 현재 Home 기반 관리 인가로 조회한다. 최초 이전 값 없음과 0원은 구별하며 현재 조회자의 Scope나 현재 설정으로 과거 감사/지급/확정 정산을 재작성하지 않는다. 인증/계정 관리 감사 Master 전용과 구별하고 일반 Audit 전체 읽기/불필요한 개인정보·인증정보 공개를 추가하지 않는다. 최소 응답/보존·저장/권한 변경 경합은 후속이다([S 승인](product-decisions.md#review-20261013-s-batch); V-118/119 미구성·미실행).

U1 담당 교체 감사/보존: 수동 만료 Pass의 담당 교체에도 기존 전후 담당·Actor/현재 권한/Branch Context·시점 이력/감사를 적용한다. 만료 상태/Remaining·발급 시각/조건/Issued Branch·과거 실제 수행/확정 지급·정산 사실은 보존한다. 추가 필수 사유/승인 대기를 도입하지 않으며 교체/감사·현재 인가/관계 조회의 저장/최소 공개·경합 계약은 후속이다(BR-OPS-008; [U 승인](product-decisions.md#review-20261013-u-batch); V-122 미구성·미실행).

V1 원본/정정 감사: 과거 Home 이력 오류는 대상·정정 전후 소속/사실 시점·원래 이력·사유/Actor/현재 Master 권한/Branch Context·정정 처리 시점을 추적한다. 사실 시점과 정정 시각을 구별하고 사유 누락을 거부하며 원래 기록/감사·PT/지급/정산 확정본을 보존한다. 소속 오류 정정만으로 과거 결과를 자동 재계산하지 않고 영향 건은 기존 권한/정정/재확정 절차로 처리한다. 최소 공개/저장/보존·현재 사실/영향 계약/경합은 후속이다(BR-OPS-032; [V 승인](product-decisions.md#review-20261013-v-batch); V-123 미구성·미실행).

W1/W2 보존/경합: 같은 PT/최초 생성 시각·기존 소비 Pass/차감을 유지하며 일반 전환은 최초 생성 시점 실제 수행 Trainer 설정/소비 Pass 발급 조건을 확인한다. 이전 보상 결과/사유·전후/Actor/시점을 보존하고 유효 일반/지원 이중 합산을 막는다. 기존 확정본 자동 변경 없이 필요한 월의 기존 해제/정정/동일 월 재확정·이전본 보존을 유지한다. 영향 건 식별/완료 증거·역사 사실 미확인/현재 설정 대체 금지와 분류 전환/감사·월 확정 원자성/경합 계약은 후속이며 검증 완료를 뜻하지 않는다(BR-OPS-033/PAY-024; [W 승인](product-decisions.md#review-20261013-w-batch); V-124/125 미구성·미실행).

<a id="nfr-005"></a>
## NFR-005. 개인정보와 지급 정보 보호

출처/상태: APPROVED-TO-BE

제품 필요: 업무에 필요한 최소 개인정보만 저장하고 회원·트레이너·지급 정보를 권한에 따라 제한한다.

수용 기준 / 남은 상세: Member 이름/전화번호/Home Branch 필수·생년월일/성별 v1 제외(I2, BR-OPS-020)를 적용한다. 기존 인가된 담당/지원 회원의 Trainer 전체 전화번호 읽기, 전화번호 중복 허용/별도 Member 식별·미인가 검색 정보 비공개·일반 수정의 필수값 유지와 보상/정산 열람 제한은 유지한다. 다른 필드 채택·전화번호 형식/정규화·역할/행위별 공개·보존/법적·운영상 삭제는 LEGAL-001 후속이며 기존 AS-IS 필드를 전부 승계하지 않는다. [2026-10-12 I 일괄 승인](product-decisions.md#review-20261012-i-batch).

2026-10-12 사용자 확정(Trainer의 회원 전화번호 조회 질문의 1번): Trainer는 기존 조회 권한이 확인된 담당 회원과 개별 허용 지원 회원의 등록된 전체 전화번호를 조회할 수 있다. 부분 마스킹된 번호만 허용하는 정책으로 제한하지 않는다. 담당 Pass 잔여가 모두 0이어도 기존 회원 조회 권한이 유지되면 전화번호도 같은 범위에서 조회한다. Backend는 전화번호를 반환하는 조회마다 현재 Caller/Organization·담당 또는 지원 관계를 검증하고 미담당/미허용 회원·타 Organization 번호를 공개하지 않는다. 지원 해제 후 별도의 유효한 담당/관리 권한이 없으면 해당 번호도 공개하지 않는다. 관리자 겸임자의 별도 관리 Scope는 유지한다. 이번 승인은 전화번호 읽기이며 수정/일괄 내보내기·다른 개인정보/개별 Pass·다른 Trainer PT/보상 공개 권한을 추가하지 않는다. 전화번호 필수 수집/형식·중복/검증과 나머지 필드/보존·조회 계약은 후속이다(BR-OPS-005, PR-002/029/030, NFR-001/005, LEGAL-001). 일반 로그/문서에 운영 개인정보를 복사하지 않는 저장소 지침을 유지하고 검증에는 비식별 가상 전화번호를 사용한다. 이 결정만으로 모든 전화번호 조회의 별도 승인/감사 보존 기간이나 새로운 인증 수단을 추가하지 않는다.

관련 요구·결정: PD-001/011/022; PR-002/004/005. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

2026-10-12 사용자 확정(회원 등록 시 전화번호 필수 여부 질문의 1번): 새 Member 등록을 완료하려면 전화번호를 반드시 입력해야 한다. 전화번호가 누락되거나 빈 문자열·공백만 있으면 등록을 완료하지 못한다. 임의 번호나 기본값으로 필수 입력을 대신하지 않는다. 이 결정은 전화번호 필수 입력이며 번호 중복 허용/금지·구체 형식/정규화·문자/본인 확인, 다른 개인정보 필수 수집이나 등록/수정 Actor 권한을 확정한 것은 아니다. 기존 Role·Data Scope와 Trainer의 인가된 담당/지원 회원 전체 전화번호 읽기는 유지한다(BR-OPS-006, PD-022, PR-002, NFR-005, LEGAL-001).

기존 사용자 일관성 지시 적용(2026-10-11): 일반 회원정보 수정에서도 필수 전화번호를 누락·빈 문자열·공백만인 값으로 지우는 변경은 허용하지 않는다. 전화번호를 변경하지 않는 다른 정보 수정에서는 기존 번호를 유지한다. 이는 등록 필수 요건을 일반 수정에 동일 적용한 것이며 전화번호 수정 권한을 새로 부여하거나 특정 API 입력 형태를 승인한 것은 아니다. 법적·운영상 필요한 개인정보 삭제/보존 예외는 LEGAL-001에서 별도 결정한다.

2026-10-12 사용자 확정(회원 간 전화번호 중복 허용 여부 질문의 1번): 같은 Organization의 여러 Member가 같은 전화번호를 사용할 수 있다. 가족 등 공유 연락처로도 각각 등록하며 전화번호가 같다는 이유만으로 신규 등록을 거부하지 않는다. Member는 전화번호와 별개의 고유 식별자로 구분한다. 동일 번호를 같은 회원으로 자동 병합하거나 Pass·PT 진행/지급 이력·담당/지원 관계를 공유하는 근거로 삼지 않는다. 전화번호 필수 입력과 기존 Role·Data Scope는 유지한다(BR-OPS-006, PD-022, PR-002, NFR-005, LEGAL-001).

기존 사용자 일관성 지시 적용(2026-10-11): 전화번호를 변경할 권한이 있는 Actor의 일반 수정에도 같은 중복 허용 원칙을 적용한다. 다른 Member가 이미 쓰는 번호라는 이유만으로 변경을 거부하지 않되 필수 번호 비움 금지와 현재 업무 인가는 그대로 적용한다. 이 결정으로 등록/수정 권한을 추가하지 않는다.

전화번호로 검색하는 경로가 제공되면 조회 권한이 있는 회원 집합 안에서 동일 번호의 회원을 각각 식별하고, 전화번호 일치만으로 한 명으로 단정하지 않는다. 미인가 회원의 존재·번호·지점이나 조회 권한을 중복 검사/검색으로 노출하지 않는다. 중복 허용은 별도 경고 화면·중복 회원 병합 기능·Member 로그인/본인 인증 승인이 아니며 번호 형식/정규화·다른 수집 항목·보존/필요 삭제 및 구체 응답·저장 계약은 후속이다.

2026-10-12 사용자 확정(발급용 타 지점 회원 검색 질문의 2번): Branch Admin·Operator는 자신의 허용된 실제 Issued Branch에서 새 PT Pass를 발급하기 위해 같은 Organization 전체 지점의 Member를 이름·전화번호 일부로 검색할 수 있다. 전화번호 전체 일치만을 요구하지 않으며 Member Home Branch가 Caller의 관리/발급 Branch와 다르다는 이유만으로 검색 후보에서 제외하지 않는다. Master의 기존 Organization 전체 범위는 유지한다. 검색은 기존 Member를 선택하여 실제 발급 지점의 새 Pass를 만드는 흐름이며 Member 소속 이동/복제나 기존 Pass·PT·지급·정산 변경을 수행하지 않는다(BR-OPS-010, PD-004/007/022, PR-002/003/030).

발급용 Member 후보 검색의 인가된 집합은 위 새 권한의 같은 Organization 전체 지점 검색 결과다. 기존 Trainer 담당/지원 회원의 전화번호 공개 결정과 다른 업무의 미인가 정보 비공개는 유지한다. 이름·전체 전화번호·현재 Member Home Branch 공개는 검색 결과 표시 정보 질문의 후속 1번 사용자 승인으로 해결됐다. 검색어가 일부이더라도 인가된 발급용 검색 결과에는 전체 전화번호를 표시한다. 다른 개인정보는 자동 공개하지 않으며 추가 공개 정보·Member 선택용 최소 식별 응답/계약은 후속 결정한다. 일반 회원 상세·일괄 내보내기·다른 Pass/PT/보상 설정 공개로 확대하지 않고 실제 운영 연락처/검색어를 문서·일반 로그에 복사하지 않는다. 공유 전화번호의 각각 다른 Member 식별자/이력·권한과 선택을 유지한다(BR-OPS-006/010, LEGAL-001).

2026-10-12 사용자 확정(발급용 검색 결과 표시 정보 질문의 1번): 새 PT Pass 발급용 Member 검색 결과에는 이름·전체 전화번호·소속 지점을 표시한다. 소속 지점은 해당 Member의 현재 Home Branch이며 Caller 관리 지점/Pass Issued Branch/수업 Performed Branch와 구별한다. 같은 Organization의 타 지점 회원 검색 결과에도 동일하게 적용하고 부분 마스킹된 번호만 표시하도록 제한하지 않는다. 기존 이름·전화번호 일부의 Organization 전체 지점 검색과 현재 발급 역할/실제 Issued Branch Scope 인가는 유지한다(BR-OPS-010, PD-004/007/022, PR-002/003/030, NFR-001/005).

검색 인가/정보 공개 경계: 이 허용은 이용권 발급용 Member 검색의 후보 범위·검색 방식과 이름/전체 전화번호/현재 Member Home Branch 공개다. Backend는 매 검색/선택/발급 요청에서 현재 Caller의 발급 역할/Organization·허용 실제 Issued Branch와 대상 Member의 실제 Organization을 검증한다. 검색 Branch Context를 위조하거나 과거 검색 결과/선택 Member ID로 철회된 역할·Scope 또는 다른 Organization을 우회할 수 없다. 같은 전화번호/이름의 여러 Member는 별도 식별자로 구분하여 선택하며 번호만으로 병합하거나 첫 결과를 자동 선택하지 않는다. 이 세 항목의 읽기 허용이 회원 정보/전화번호 수정·일반 Member 상세·전체 무조건 목록/일괄 내보내기, 다른 개인정보/Pass/PT/보상 정보 열람 권한을 추가하지 않는다. Trainer 단독의 담당/개별 지원 Member 검색 및 기존 전체 전화번호 공개는 유지하고 발급 역할 겸임은 그 독립 발급 업무 Scope로 판단한다. 응답은 승인된 공개 범위 안에서 구성하며 Member 선택용 최소 식별 응답/계약과 추가 공개 정보는 후속이다. 실제 운영 연락처/검색어를 문서·일반 로그에 복사하지 않는다.

2026-10-12 C 일괄 승인 반영: C8의 원문 IP/브라우저 정보 제외는 로그인 감사 수집 범위다. 반복 시도 보호의 일시적 IP 처리·미확인 계정 표현/보존 계약은 별도 검토하고 로그인/암호/토큰 원문은 기록하지 않는다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 H 일괄 승인 반영: H4: 관리자 권한 없는 Trainer의 본인 월 정산 총액/구성 조회를 v1 화면·API/직접 ID·집계 경로에 허용하지 않는다. 관리자 안내는 자동 발송/명세 기능 승인이 아니며 본인 PT 진행 내역·독립 관리자 겸임 Scope는 유지한다. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch). 실제 검사/업무 구현은 후속이다.

M2의 수동 만료 담당 조회에서는 현재 유효 Trainer의 실제 현재 담당 관계를 근거로 해당 Member/기존 허용 전체 전화번호만 공개한다. 현재 관계/Organization/계정·역할/인증/Trainer 상태는 요청마다 확인하고 만료만으로 조회를 막지 않되 미담당/지원 해제·이전 담당이나 비활성/차단된 접근을 허용하지 않는다. 조회 유지가 만료 후 새 수업 사용/다른 개인정보/개별 Pass·다른 Trainer PT/보상·수정/내보내기 권한을 뜻하지 않는다(BR-OPS-005; [M 승인](product-decisions.md#review-20261013-m-batch); V-107 미구성·미실행).

수업별 보상 비공개(N1/N2): 일반 Session Payment 및 수업 연결 지원 보상 금액을 비인가 Trainer/수행 지점 관리자에게 HTTP 본문·등록 성공/목록/상세/직접 ID·중첩 결과/제공되는 합계·계산 근거/감사/오류로 우회 노출하지 않는다. 내부 확정 결과/정산 입력은 유지하며 UI 숨김이나 가짜 0원/삭제/재계산으로 대체하지 않는다. 기존 관리자 Scope·H4 월 정산 제한/CompSetting 비공개와 독립된 PT 기록 조회는 유지한다. 금액 외 보상 상태/미입력 여부·새 공개 필드/기능은 이번 승인에 포함하지 않는다. 구체 최소 응답/오류·모듈 계약은 후속이다(BR-PAY-021; [N 승인](product-decisions.md#review-20261013-n-batch); V-108/109 미구성·미실행).

<a id="nfr-006"></a>
## NFR-006. 백업과 복구

출처/상태: TBD / PRODUCT-DECISION PD-021 OPEN

제품 필요: Organization 내 여러 Branch의 신규 운영 데이터의 백업·복구 요구를 현실적으로 정의한다. 기존 자료 이관이나 이관 실패 복구를 요구하지 않는다.

수용 기준 / 남은 상세: 허용 데이터 손실·복구시간·확인 주기·책임과 복구 결과 대사 기준은 ARCH-004. 수치와 방식 미정.

관련 요구·결정: PD-017/018/021. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

<a id="nfr-007"></a>
## NFR-007. 결과와 오류 안내

출처/상태: NEW-CANDIDATE — 품질 수용 기준 후보

제품 필요: 정상 완료·미반영·조회 실패·자료 없음을 구분하여 사용자가 업무 결과를 확인할 수 있게 한다.

수용 기준 / 남은 상세: Session/Pass 변경 후 결과 확인과 실패 시 다음 행동 안내를 검토한다. 세부 오류 경험은 후속 UX에서 결정하며 기술 상세와 개인정보를 노출하지 않는다.

관련 요구·결정: PD-010; PR-008/009/015. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

<a id="nfr-008"></a>
## NFR-008. Responsive Web 사용성

출처/상태: APPROVED-TO-BE; 접근성 세부 NEW-CANDIDATE

제품 필요: Desktop/Tablet/Smartphone responsive layout과 터치 기반 조작을 지원한다. 작은 화면에서도 사용자별 주요 정보 확인과 주요 Action이 실질적으로 가능해야 한다. Desktop 화면을 단순 축소하는 것으로 충족하지 않는다.

수용 기준 / 남은 상세: 브라우저/버전·breakpoint는 ARCH-004와 Frontend Design에서 정한다. 각 Actor의 허용된 회원 검색·Pass/Session 처리·정산 확인을 지원 기기에서 검증한다. 특히 Trainer가 Smartphone으로 로그인 → 허용 Member/PT 확인 → 실제 Branch/진행일 확인 → Session 등록 → 자신의 Session 및 결과 확인까지 수행할 수 있어야 한다. 지급 설정을 노출하지 않는다. 키보드·확대 등 상세 사용성 기준은 후속 검토.

관련 요구·결정: PD-005; PR-015. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

AB6 지원 품질 목표: v1 Chrome/Edge/Safari 최신2개 안정 주버전에서 Desktop/Tablet/Smartphone 주요 업무와 Trainer 현장폰 흐름을 검증한다. 구체 OS/기기·버전 매트릭스와 지원 갱신/터치·화면/Passkey 인수는 후속이며 현재 지원 검증 완료가 아니다. Firefox 지원 추가나 User-Agent 인가/차단 정책을 채택하지 않는다([AB 승인](product-decisions.md#review-20261013-ab-batch); V-137 미구성·미실행).

<a id="nfr-009"></a>
## NFR-009. 성능과 데이터 증가

출처/상태: TBD / PRODUCT-DECISION PD-021 OPEN

제품 필요: Organization의 Branch 수·Branch별 운영자·Trainer 직접 로그인 수 및 회원·Pass·Session 증가량을 기준으로 응답시간을 정의한다. 대규모 트래픽을 가정하지 않는다.

수용 기준 / 남은 상세: 검색·저장·월 정산의 자료량/동시량/시간 목표를 ARCH-004에서 합의한다. VAL-016은 현재 업무 측정 참고.

관련 요구·결정: PD-021; PR-002/008/010. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

<a id="nfr-010"></a>
## NFR-010. 가용성과 업무 연속성

출처/상태: TBD / PRODUCT-DECISION PD-021 OPEN

제품 필요: 지원 운영시간과 허용 중단·업무 재개 요구를 정의한다. 준비 완료 후 일괄 전환하며 장기 이중 입력은 하지 않는다.

수용 기준 / 남은 상세: 가용성 목표와 장애 시 업무 처리 여부 확인·대응은 ARCH-004, 짧은 전환 준비는 OPS-001. 오프라인 기능은 자동 포함하지 않는다.

관련 요구·결정: PD-018/021; PR-028. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

<a id="nfr-011"></a>
## NFR-011. 운영 상태와 장애 대응

출처/상태: TBD / PRODUCT-DECISION; 상세 관찰 항목 NEW-CANDIDATE

제품 필요: 실운영 시스템의 실패와 잘못된 반영을 발견하고 대응할 수 있는 운영 요구를 정한다.

수용 기준 / 남은 상세: 관찰할 사건, 대응 책임·시간·안내 방식은 ARCH-004. 특정 모니터링 도구·알림 연동을 선택하지 않는다.

관련 요구·결정: PD-021/022; NFR-004/006. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

<a id="nfr-012"></a>
## NFR-012. 날짜와 지급액의 일관성

출처/상태: APPROVED-TO-BE; 입력값 검증·날짜 경계 상세만 OPEN

제품 필요: Monthly Settlement = 해당 월 적용 Base Salary + 유효한 Session Payment 합계 + 유효한 Additional Performance 합계다. Trainer·대상 월·적용 기본급·Session 수·Session Payment 합계·추가실적 내역/합계·월 정산 합계를 구분한다. 2,500,000원 + 1,200,000원 + 150,000원 = 3,850,000원이며 여러 지점 수업으로 동일 월 기본급을 중복 가산하지 않는다. 타 지점 수업의 보상 전체는 Additional Performance로 반영하며 일반 Session Payment를 별도로 합산하지 않는다(MB-009 CLOSED, 2026-10-10 사용자 정정). 현재 설정 변경으로 과거 확정 Session Payment·월 정산의 적용 기본급/합계를 자동 변경하지 않는다. 소속·발급 지점 변경으로 과거 Session Performed Branch가 바뀌지 않아야 한다.

수용 기준 / 남은 상세: BR-PAY-001–017을 따른다. 일반 Session Payment 적용 대상의 RATE Session별 1,000원 올림과 FIXED_AMOUNT 설정값, 관리자 저장 완료 이후 신규 등록에 Rate/Fixed Amount 적용 및 정상 등록 시 확정은 유지한다. 타 지점 지원 수업은 보상 금액 없이도 허용된 PT 진행 기록과 Pass 차감을 먼저 완료한다. 권한 있는 관리자가 나중에 수업 건별 금액을 저장할 때 해당 Additional Performance 보상을 확정한다. 금액 미입력은 확정된 0원과 구분하고 누락 건을 추적할 수 있어야 한다. 해당 Trainer의 해당 월 정산 대상 지원 수업에 금액 미입력 건이 하나라도 있으면 그 Trainer·월 정산을 확정할 수 없다. 월 정산 확정 전 지원 수업 보상 금액의 모든 수정에는 변경 사유가 필수다. 양수 간 변경·0원에서 양수로 변경·양수에서 0원으로 변경 모두 적용하며, 사유 없이는 금액을 수정할 수 없다. 변경 전후 금액·변경 사유·수정자·수정 시점을 이력으로 남긴다. 확정된 월 정산에서 지원 수업 보상 금액 오류를 발견하면 해당 Trainer·월 정산의 확정을 해제하고 금액을 정정한 뒤 해당 월 정산을 다시 확정한다. 이전 확정본은 이력으로 보존한다. 월 귀속·나머지 확정 조건·진행 기록 연계 상세·나머지 정정/취소는 BR-009/013 등 관련 OPEN을 따른다. 타 지점 보상 구성 MB-009는 해당 수업의 보상 전체를 Additional Performance로 처리하는 방식으로 해결했다. 기본급 적용 시작 월은 권한 있는 관리자가 미확정인 과거 월을 포함해 지정하며 과거 확정 정산은 자동 변경하지 않는다. 변경이 적용되는 수동 지정 없는 기존 미확정 정산의 기본급·합계는 별도의 반영 작업 없이 자동 갱신하며 정산을 자동 확정하지 않는다. 확정 월 기본급 오류는 해당 월 확정 해제·기본급 정정·동일 월 재확정으로 처리하고 이전 확정본을 보존한다. 기본급 오류 정정의 확정 해제·재확정은 Master Admin에게 Organization 전체, Branch Admin에게 각 처리 시점 대상 Trainer의 현재 Home Branch가 자신의 관리 Branch인 경우 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 처리한다. 확정된 월의 기본급 오류 정정에서 확정 해제와 해당 월 기본급 수정 모두 사유가 필수다. Master Admin·Branch Admin 및 관리 범위 안 본인 건에 동일하게 적용한다. 해제 사유·해제자·시점과 변경 전후 기본급·수정 사유·수정자·시점을 이력으로 남긴다. 사유 없는 각 요청은 해당 작업을 거부하며 요청 직전 상태·금액·기존 확정본을 변경하지 않는다. 기본급 오류 정정은 대상 Trainer의 해당 월 정산에만 적용하며 현재·미래 기본급 설정과 다른 월 정산은 유지한다. 지속적인 기본급 변경은 별도로 적용 시작 월을 지정하는 기존 흐름을 따른다. 입사·퇴사·휴직이 있는 달의 적용 기본급은 관리자가 해당 Trainer·월의 금액을 직접 지정한다. 예를 들어 월 기본급 설정이 2,500,000원이어도 해당 월만 1,500,000원을 적용할 수 있으며, 이 지정으로 현재·미래 기본급 설정과 다른 월 정산은 변경하지 않는다. 월별로 수동 지정한 기본급은 이후 일반 기본급 설정이 변경되어도 유지한다. 일반 설정 변경의 미확정 정산 자동 반영은 수동 지정이 없는 월에 적용하며, 수동 지정 월의 금액을 바꾸려면 관리자가 해당 월 금액을 직접 수정한다. 미확정 월의 기본급을 최초 수동 지정하거나 다시 수정할 때 모두 사유가 필수다. 사유가 없는 요청은 거부하고 요청 직전의 수동 지정 여부·적용 금액·월 합계를 유지한다. 대상 Trainer·월, 지정/수정 전후 금액·사유·처리자·처리 시점을 이력으로 남긴다. 미확정 월 기본급의 최초 수동 지정·수정은 Master Admin의 Organization 전체, Branch Admin의 각 처리 시점 대상 Trainer 현재 Home Branch가 관리 Branch와 일치하는 범위에서 허용한다. 관리 범위 안 본인 건도 포함하며 별도 Master 승인 없이 직접 처리한다. 추가 사용자 확정(2026-10-11): 해당 월 기본급은 권한 있는 관리자가 사유를 남기면 0원으로 명시적으로 수동 지정할 수 있다. 수동 지정한 0원은 미입력과 구분하며, 미입력이나 누락된 일반 설정을 자동으로 0원으로 대체하지 않는다. 해당 월 기본급에만 적용하고 다른 유효 지급·추가실적은 기존 규칙대로 합산한다. 미래 적용 월의 입력 범위와 월별 수동 지정 상세 등 BR-012의 남은 정책, 추가실적 정책 BR-013, 귀속/열람 MB-010/006은 상세 결정 전 보류한다. 날짜 BR-008·입력 BR-010은 OPEN을 유지한다. Product 변경은 기존 Pass 발급 당시 가격·총횟수·Payment Type 유지로 BR-011 CLOSED다. 변경은 새 Pass부터 적용하고 Trainer 설정의 등록 시점 적용은 유지한다.

관련 요구·결정: PD-008/009/012; PR-007/008/010. [요구사항](requirements.md), [결정](product-decisions.md), [후속 질문](open-questions.md).

AS-IS 도출 참고: [위험 및 미확인 사항](../analysis/11-risks-and-unknowns.md), [역검증](../analysis/verification-report.md), [현재 사실 검증 목록](validation-needed.md). K02/K05는 정합성, K13/K15는 동시성, K18/K19/K38은 결과·감사, K06/K07/K35는 접근, K09/K10/K22는 복구, K24/K25는 계산 검증의 참고다. 기존 가계부·락커 결함을 v1 기능으로 승계하지 않는다.

2026-10-12 일괄 승인 반영: B7: Organization 공통 Asia/Seoul의 업무 날짜/달력 월 경계를 사용한다. 동일 실제 시점을 기기/지점별 다른 월로 집계하지 않는다. 실제 수업일/생성 시점·생성 시점 지급·확정 과거 결과 보존은 유지하며 날짜 정밀도/저장 형식/역사 사실 판정·월 확정 경합은 후속이다. [2026-10-12 일괄 승인](product-decisions.md#review-20261012-batch).

2026-10-12 C 일괄 승인 반영: C9/C11: 실제 수업 시작 날짜/시각의 Asia/Seoul 날짜/월과 정수 원 금액 입력/소수 원 거부를 적용한다(BR-OPS-017, BR-PAY-017). 일반 지급의 생성 시점 설정·RATE 1,000원 올림/FIXED 추가 올림 없음·기존 항목별 0원/양수 규칙을 유지한다. Rate 정밀도/나머지 금액 한도·실제 시각 확인 불가/저장·경합은 후속이다. [2026-10-12 C 일괄 승인](product-decisions.md#review-20261012-c-batch)

2026-10-12 H 일괄 승인 반영: H1: Trainer Rate는 정수 퍼센트만 입력하고 소수 비율을 임의 반올림/절사하지 않는다. 원화 정수/C11·RATE 지급 결과의 수업별 1,000원 올림/FIXED 추가 올림 없음·과거 확정 지급 보존을 유지한다. 범위/누락·실제 수치 표현은 별도다. [2026-10-12 H 일괄 승인](product-decisions.md#review-20261012-h-batch). 실제 검사/업무 구현은 후속이다.

2026-10-12 K 일괄 승인 반영: 날짜/시각 오류 후 재등록의 실제 업무 날짜/월과 새 기록 생성 시점 설정을 구분한다. 원래 지급 불변·취소 원본 보존/합산 제외를 유지하고 새 일반 지급만 재등록 생성 시점의 설정·선택 Pass 발급 조건으로 계산한다. Performed Branch 값 정정의 기록 유지/최초 생성 기준은 변경하지 않는다. [2026-10-12 K 일괄 승인](product-decisions.md#review-20261012-k-batch). 실제 업무 검사 미구성·미실행이다.

추가 수용 기준(L1/L2=1): 정산 확정의 종료 월은 서버에서 공통 Asia/Seoul 달력 경계로 검증하고 클라이언트 날짜·권한 주장으로 당월/미래 월 확정을 우회할 수 없어야 한다. 다음 달 1일 00:00 경계 전후·다른 필수 확정 조건·현재 인가·기존 결과 보존을 후속 검증한다(BR-PAY-020). Rate는 0~100% 정수만 허용하며 -1/101/50.25 거부·범위 보정/반올림/절사 없음·명시적 0%와 누락 구별·과거 확정 지급 불변을 검증한다(BR-PAY-018). 구체 저장/검증·오류/시계·UoW/경합은 후속이며 [L 승인](product-decisions.md#review-20261013-l-batch)의 V-104/105는 미구성·미실행 계획이다.

Q2 입력: 일반 Fixed Amount/Base Salary는 0원 이상 정수 원으로 최초/변경 모두 적용한다. 명시적 0원과 누락/null·비공개용 가짜 0원을 구별하고 음수/소수 원을 자동 보정/절사하지 않는다. Rate 0~100% 정수·FIXED 추가 올림 없음/실제 서비스 설정 사용·기본급 지속 적용과 다른 업무별 사유 필수 0원/양수·과거 확정 결과 보존을 유지한다. 금액 상한/저장 표현·오류 계약은 후속이다(BR-PAY-022; [Q 승인](product-decisions.md#review-20261013-q-batch); V-115 미구성·미실행).

T1/T2 시간 의미: Pass 발급 시각은 시스템 신규 발급 완료 시각이며 과거 날짜 입력/소급 발급은 v1 제외다. 별도 시작일 없이 발급부터 기존 조건으로 사용하고 실제 수업 당시 발급된 후보만 선택한다. 공통 Asia/Seoul 업무 기준·실제 PT 시작 시각/월과 PT 기록 생성 시각/일반 지급 적용 설정을 구별한다. 기존 우선순위/만료 예외/정산/과거 결과 보존은 유지하며 시간 저장/정밀도·동일 시각 정렬/최소 계약은 후속이다(BR-OPS-031; [T 승인](product-decisions.md#review-20261013-t-batch); V-120/121 미구성·미실행).

<a id="nfr-013"></a>
## NFR-013. Future Domain / Client 확장 제약

출처/상태: APPROVED-TO-BE / Future Constraint

제품 필요: 향후 Member Authentication/Self-Service와 Schedule/Reservation 도메인 추가를 불필요하게 어렵게 만드는 구조적 제약을 피해야 한다. Web UI에 Business Logic을 강하게 결합하여 Trainer·Member 대상 Mobile App 등 다른 Client에서 동일 업무 기능을 사용할 수 없게 만들지 않아야 한다.

수용 기준 / 남은 상세: 현재 예약 도메인·Mobile App·Member 로그인을 구현하지 않는다. Member와 Login Account를 동일시하지 않으며 향후 연결은 Architecture/Product Expansion에서 정의한다. 구체 API Architecture·인증·Web/Mobile Framework를 여기서 선택하지 않는다.

관련 요구·결정: PD-003/025/026; [Scope](scope.md), [Architecture Handoff](architecture-handoff.md).

## Product Baseline — 2026-09-17 지점 관계·보상 개정

최신 사용자 확정사항을 반영한 Architecture Input Baseline이다. [현재 결정과 변경 이력](README.md), [권한](users-and-roles.md), [업무 규칙](business-rules.md), [남은 결정 게이트](open-questions.md), [Architecture 인계](architecture-handoff.md)를 함께 따른다. Baseline 갱신은 모든 상세 업무 정책 또는 구현 완료를 뜻하지 않는다.
