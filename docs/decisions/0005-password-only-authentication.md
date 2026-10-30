# ADR-0005 — v1 아이디·비밀번호 인증과 Passkey 완전 제거

Status: **ACCEPTED** — 사용자 승인 인증수단 선택만.

작성/채택일: 2026-10-31. 승인 원문은 “둘 다 귀찮을 것 같아. Passkey는 완전히 없애고
아이디·비밀번호로만 로그인하도록 재설계하자.”다.
[Product PW-1–PW-6](../product/product-decisions.md#review-20261031-password-only)을 따른다.

## 범위와 결정

지원하는 v1 Master/Branch Admin/Operator/Trainer 및 겸임은 아이디·비밀번호만 사용한다.
Passkey 등록·추가/삭제·로그인·분실 재등록, 사용자 검증 WebAuthn 조건을 현행 기능에서 제거한다.
선택 Passkey·Master 예외·OTP/SMS/다른 MFA를 추가하지 않는다. Member 로그인은 Future Scope다.

ADR-0004의 PostgreSQL AuthSession+무작위 opaque Cookie, ADR-0001–0003의 기반은 유지한다.
인증 성공은 현재 Role/Scope/Organization·Trainer 상태의 행위 인가를 대체하지 않는다.
기존 강한 비밀번호/실패 제한·HTTPS·CSRF·원래30분/8시간 수명·철회·감사를 유지한다.
C1 추가 관리 암호 확인 없음, C3 본인 암호 변경의 현재 암호 확인, A8·C5·A9·AB5/R4 보호도 유지한다.

## 대체와 보존

A10 운영 전 관리자 MFA 의무·AB4 비밀번호 뒤 Passkey·MFA M1–M5/M7의 Passkey 기능을 대체한다.
M6 추가 Master 발급 Actor와 M8 본인 관리자 reset 금지 등 독립 정책은 유지한다.
기존 승인·migration·검증 결과는 당시 이력이며 삭제/성공 성적 변경을 하지 않는다.
과거 Passkey 감사 참조 보존은 현행 사용자 기능·인증 권한 유지가 아니다.

## 비용과 경계

등록/기기관리와 매 로그인 추가 인증 부담이 사라진다. 비밀번호 탈취에 대한 추가 인증 방어는 포기하며
기존 실패 제한/CSRF가 피싱 방어를 대신한다고 주장하지 않는다. 보안 수준 변화는 이번 인증수단 선택에 따른다.

현재 코드7855786에는 이전 MFA가 있다. 이번 ACCEPTED는 코드/DB 전환·상세 잠금/UoW/공개계약·
테스트 PASS·production 허용·원본 자료 삭제 승인이 아니다. 별도 제한 기술 계약과 독립 검증으로 구체화한다.
새 정책 때문에 기존 계정/역할/소속/업무 데이터·원본 암호/감사 이력을 초기화하지 않는다.
기존13 migration은 그대로 두고 필요한 전환은 후속 forward migration으로 다룬다.
운영/개인정보 보존·브라우저/배포 게이트와 다른 OPEN/전역 모듈 PROPOSED는 유지한다.

구체 흐름/유지 경계는 [IAM-014 설계](../architecture/iam-014-password-only-design.md),
직접 영향 저장·proof·복구 연결과 검증 계획은 [전환 상세](../architecture/iam-014-password-only-transition.md)를 따른다.
이 문서들의 설계 검토 완료는 실제 코드·migration·원본 DB 전환·실행 인수 완료가 아니다.
