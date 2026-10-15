# PREP-IAM-001 새 실행 결과 — 2026-10-13

2026-10-14 자료 수명 갱신: 사용자 지시로 완료된 실행의 원본 로그·환경·전체 ZIP 보존을 종료한다. 최신 판정/한계와 현재 자동 테스트는 유지하며 미해결 S1 core 결함은 없다. 아래 과거 경로·checksum·실행 수치는 당시 기록이다. 과거 ZIP을 풀어 재실행하는 안내는 종료됐고, 현재 실행/자료 정리는 [Backend QA 안내](../../backend/README.md#qa-실행-자료와-정리)를 따른다. 원문 corpus는 필요한 입력 한 벌만 `.local/qa/corpus-inputs-3a5f62f0e18a/`에 보존했다. 삭제 대상 자료를 다시 복사·압축하지 않았다.

상태: **2026-10-13 독립 재현 및 설계자 검토 후 제한된 개발 S1 구현 진입 PASS**. [판정·독립 검사·같은 프로세스의 corpus/해시 메모리 관찰](prep-iam-001-review.json)을 근거로 S1a→S1b 구현 진행을 지시했다. 이 보고 아래의 수치는 구현 전 PREP 실험 결과이며 실제 IAM 인수 통과가 아니다. Product 정책 변경, 전체 IAM 완료, 운영 허용을 선언하지 않는다.

## 실행과 증거

- 기준: `main`, HEAD `b83defe3fc564b56d0f77cb075ddb5436759d191`. 시작 시 기존 tracked 문서 17개 변경/untracked 문서 4개를 보존했다. 최신 미커밋 Product와 TX01–TX06을 기준으로 삼았다.
- 새 실행 영역: `/tmp/y3-prep-iam-001-h90lpnpq`(0700). 과거 `/tmp/y3-iam-preflight-o0qwlz8q`는 현재 없으며, 9월 수치는 이번 성공 근거로 사용하지 않았다.
- 재현 증거 묶음(완료 자료 정리로 폐기): 실행한 Python/JS/sh probe, 원시 결과 JSON, 공급 manifest/라이선스, 실패 요약, 고정 의존성 목록. CA 개인키·쿠키·nonce·암호·해시·DB 접속 비밀·가상환경·corpus 원문은 포함하지 않는다. 실제 corpus와 wheel은 고정 URL/checksum으로 다시 받는다.
- WSL Python 3.13.15, uv 0.12.16. 원본 backend `.venv` 대신 임시 env 사용. 기존 41개 Linux 의존성 버전 유지, 신규 5개 포함 46개 `uv pip check` 통과.
- `preservation-results.json`: 기존 저장소 파일 변경 0개, 원본 `.venv` 4,427개 파일 동일. 이번 저장소 추가는 이 보고와 증거 zip뿐이다. commit/push/stage 없음.

## 1. 암호 공급과 보조 방어

SecLists commit `3a5f62f0e18a1b8a36b25399aff0077f3706e5af`의 실제 파일을 고정했다. 파일당 12 MB, 합계 25 MB 다운로드 상한을 적용했다. 저장소 MIT LICENSE와 출처 README를 보존했다. 개별 원천을 모두 독립적으로 권리 검증했다는 뜻은 아니며 German 목록의 upstream README에는 별도 원천 설명이 없다.

| 실제 목록 | 줄 수 | NFC 고유값 | 15–128자 | non-ASCII | 한글 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Xato top 1 million | 1,000,000 | 999,997 | 10,908 | 0 | 0 |
| German top 1 million | 1,000,000 | 1,000,000 | 44,280 | 377 | 0 |
| French top 20,000 | 19,994 | 19,994 | 24 | 5 | 0 |
| Arabic top 487 | 487 | 487 | 34 | 0 | 0 |
| 합집합 | — | 1,926,507 | 55,169 | 382 | 0 |

파일 이름의 언어/개수와 실제 문자 분포를 구별했다. UTF-8 strict decode, 줄 구분 제거, NFC 이후 전체 문자열 set 조회를 사용한다. 네 실제 목록에서 NFC 변경은 0개였다. 개별 URL/bytes/SHA-256은 `sources/corpus-manifest.json`, 측정은 `corpus-results.json`에 있다. 기존 10만 목록의 긴 암호 72개보다 범위는 넓어졌지만 한국어 유출 암호 대표성을 입증하지 못한다.

개발 S1 권고 조합은 **NFC → 승인 길이 15–128 → 고정 실제 corpus 전체 일치 → 명백한 짧은 반복 패턴 및 서비스/현재 Login ID의 제한된 전체 문맥 변형 차단**이다. 보조 규칙은 길이 1–4의 단위를 전체 반복한 문자열, 실제 corpus에서 존재를 확인한 네 seed(`password`, `administrator`, `qwerty`, `letmein`)의 2–16회 전체 반복, 서비스명/계정명에 흔한 숫자·연도·암호 표현을 붙인 제한된 집합을 다룬다. 반복/문맥 전체 뒤에 붙는 기호는 없음/`!`/`!!`/`@`/`#`/`$`/`?`/`.`의 유한 집합이다. 일반 길이 5 이상 단위의 반복을 포괄 거부하지 않는다. 비밀번호 해시 입력을 소문자화하거나 trim하지 않는다. 문맥 비교에만 casefold를 사용한다. 일반 단어의 부분 포함으로 거부하거나 문자 종류 조합을 강제하지 않는다. 보조 규칙을 실제 corpus의 대체물로 제시하지 않는다.

`corpus_probe.py` 6개, `corpus_supplement.py` 12개 boolean 통과: 실제 긴 목록 표본/긴 숫자열 거부, 명백한 한글 반복/서비스·계정 전체 문맥 거부, 정상 한국어 문구 수용, NFD/NFC 동일 판정, 서비스/암호 관련 단어를 일부 포함한 강한 입력 수용, 가상 난수 포함 입력 1,000개 수용. 이 표본 수용률은 실제 사용자 오탐률이 아니다. 유한 보완 후 보조검사 평균 약 0.158 ms는 이번 머신 관찰이며 SLO가 아니다.

**남는 한계:** 공백이나 열거하지 않은 구두점(예: `~`)으로 변형한 반복, 임의의 한글 5글자 이상 단위 반복, 생성 집합 밖 문맥, 알려지지 않은 한국어 약한 문구를 모두 찾아내지는 못한다. 문자 표현 전체를 금지하는 과잉 대응을 넣지 않았다. 이 조합은 긴 흔한 암호와 명백한 한글 약암호를 실제로 거부하는 개발 S1 후보이며 한국어 완전성/운영 적합성을 증명한 것은 아니다. 검토자가 A3의 개발 인수에 충분한지 판단해야 한다. 추가 원천이 필요하면 출처·라이선스가 확인된 한국어 자료를 별도 추가하거나, 대규모 오프라인 유출 해시 공급을 용량·라이선스 검토 후 도입할 수 있다. 외부 암호 조회 API나 거대 데이터 자동 다운로드는 채택하지 않았다.

독립 tester의 추가 사례를 반영한 유한 보완: 기존 후보가 흔한 단어의 전체 반복, 공개 예시, 서비스/계정명 뒤 `@`, 한글 반복 뒤 `!`를 놓쳤다. 위 제한된 규칙과 함께 [xkcd #936의 공개 예시](https://xkcd.com/936/)의 공백 있는 원문·공백 없는 연결형 두 문자열을 정확히 거부한다. 이미 공개된 특정 예시에 대한 보조 deny이며 임의의 여러 단어 passphrase가 약하다는 뜻은 아니다. 출처/확인일/정확한 두 형태는 `sources/public-example-provenance.json`에 기록했고 만화 이미지·본문은 배포하지 않는다.

`corpus_finite_regression.py`에서 20개 사례(거부 대상 10개, 정상 수용 8개, 명시적으로 남긴 수용 한계 2개)의 기대 결과와 전체 NFC/NFD 일치, 네 seed의 실제 corpus 존재, 공개 예시 출처를 확인했다. 합계 판정 4개 boolean 통과. 한계 2개를 약암호 차단 성공으로 세지 않는다. 기존 보조검사 12개와 가상 난수 포함 정상 입력 1,000개도 다시 통과했다. 비밀번호 해시 입력 trim/casefold·부분 단어 거부를 추가하지 않았고 정상 공백·한국어/강한 단어 포함은 유지한다. 실제 corpus 원문·공급 manifest는 변경하지 않았다. 이 보완에서 DB/HTTPS probe를 다시 실행하지 않았으며 기존 실행 결과와 구별한다.

공급/갱신 제안: 앱과 별도 준비 단계에서 commit·원문 checksum을 고정하고 무결성/UTF-8 실패면 새 공급을 거부한다. 정규화·분포·추가/삭제와 약암호/정상 문구 회귀를 비교한 후 버전 전체를 원자 교체한다. 로그인 요청 중 다운로드하거나 공급 실패를 빈 목록으로 대체하지 않는다. 이번 목록 배포 재현은 실행했지만 제품의 공급 오류 처리·원자 갱신 구현은 S1 검사 대상이다.

## 2. 해시 비용과 실행 상한

고정 후보는 pwdlib 0.3.1 / argon2-cffi 25.1.0 / argon2-cffi-bindings 26.1.0 / cffi 2.1.1 / pycparser 3.0이다. 배포 라이선스는 순서대로 MIT/MIT/MIT/MIT-0/BSD-3-Clause. PyPI 정확 버전 metadata와 wheel SHA-256을 대조하고 설치 payload 70개를 비교했다(`package_probe.py`, `package-results.json`). PyPI 취약점 배열 0개는 종합 보안 감사 완료가 아니다.

Argon2id v19, memory 65,536 KiB, time 3, parallelism 4, salt 16 bytes/hash 32 bytes를 명시했다. `hash_probe.py` boolean 14개 통과: 정상/오입력·salt·rehash·잘못된 형식의 정확한 예외·명시적 NFC·공백 의미·기존 버전 보존 및 자원 gate. 16개 동시 요청 중 2개만 해시, 14개는 대기열 없이 busy. 예외 뒤 슬롯 반환도 확인했다. 고의 False 주입은 exit 1로 거부했다.

| 측정 | 중앙값 | 최대 | 표본 |
| --- | ---: | ---: | ---: |
| hash | 120.39 ms | 154.79 ms | 8 |
| verify | 136.10 ms | 177.39 ms | 8 |
| 낮은 비용에서 rehash | 159.60 ms | 238.33 ms | 8 |

동시 verify 2개는 288.06/302.93 ms, 해당 프로세스 peak RSS 154.14 MiB였다. corpus 로딩·실제 앱·DB pool 포함 메모리나 운영 p95가 아니다.

`resource_probe.py`는 독립 OS 프로세스 4개에서 PostgreSQL advisory permit 2개만 해시하도록 검증했다. 2개 busy, 정상 종료와 permit 반환 확인; 각 프로세스 peak RSS 합 339.40 MiB(동일 시각 RSS가 아님). **이 방식은 해시 중 DB 연결 상실 시 permit만 먼저 풀릴 수 있어 S1 기본 권고로 채택하지 않는다.**

S1 권고는 **WSL 단일 서비스 프로세스/ASGI worker 1을 시작 시 강제 + 프로세스 내 해시 동시 2개, 대기열 없음**이다. `single_worker_probe.py`가 worker=2 거부, 같은 canonical lock 경로의 둘째 OS 프로세스 거부, 정상 종료/강제 종료 후 lock 반환 등 5개 검사를 통과했다. 실제 시작 경로에서도 우회 없이 이 조건을 강제해야 하며, 다중 컨테이너/호스트는 이 상한의 지원 범위가 아니다. 생성·검증·재해시가 같은 gate를 공유하고 용량 부족은 계정 존재와 무관한 503으로 종료하는 계약을 S1에 적용해야 한다.

## 3. 실패예산 원자성과 보안 상태 총량

Docker context `wsl-ubuntu`, endpoint `unix:///run/docker-wsl.sock`, Compose project/service/working_dir, loopback 55433 바인딩을 확인했다. 기존 중지된 `postgres-test`만 시작했다. 실제 DB/user/내부 포트도 확인했다. `db-owner.json`에 소유 근거를 기록하고 매 실행 새 `prep_*` schema만 생성·제거했다. 개발 DB/기존 schema·볼륨을 초기화하지 않았다. 공유 테스트 서비스는 다음 검사에 사용할 수 있도록 실행 상태로 남겼다.

`budget_probe.py`는 실제 PostgreSQL 독립 연결 20개와 barrier를 사용했다. 5개 예약/15개 제한, 완료 실패 5개 이후 900초 대기, 899초 거부/900초 재개, ID 대소문자 key 동일, 성공으로 타 요청 실패를 지우지 않음, 중복 완료 거부, lease 만료/늦은 결과, 업무 rollback과 별도 실패 상태 보존, 실제 접속 장애/잠금 timeout의 503, 새 연결의 상태 유지, 자체 schema 제거 등 **17개 boolean**을 통과했다. 경계 시각은 제어한 UTC 입력이며 실시간 15분 대기나 OS 프로세스 재시작 시험으로 표현하지 않는다.

구체화한 후보: 정규화 제출 ID의 keyed digest를 사용하고 해시 전에 실패+진행중 합계 5개까지 예약한다. 진행중만 가득 차면 짧은 일반 429, 실패 5개가 확정되면 15분 429. 성공은 자기 예약만 해제하고 다른 실패를 초기화하지 않는다. 실험 lease 30초를 넘긴 미완료는 다음 접근에서 보수적으로 실패로 처리하며 늦은 결과를 받아들이지 않는다. DB 실패는 503, 메모리 fallback 없음. 해시 자원 부족 등 검증 시작 전 거부는 실패로 세지 않고, 결과 기록 실패/불명확은 성공 인증 발급으로 진행하지 않아야 한다. 이 마지막 연결 계약은 실제 앱 인수에서 추가 검증한다.

존재/미존재/차단/설정대기 레이블은 같은 함수로 상태·본문·Retry-After가 같음을 확인했다. **실제 계정 조회/HTTP 응답/시간 비노출 증거는 아니다.** 동일 NAT의 가상 ID 40개는 각각 독립 예산을 얻었다. IP 100회 같은 미승인 hard quota를 도입하지 않았다. IP 공격 방어 전체를 통과했다고 주장하지 않는다.

`resource_probe.py`의 추가 실제 PG 실험은 ID/preparation/token 공통 allocator에서 16개 연결이 256개 새 상태를 요구할 때, 설정한 총량 128개만 만들고 나머지 128개를 503으로 거부했다. live 상태 강제 퇴거 없음, 만료 뒤 회수/재수용, 자체 schema 제거 확인. **128은 작은 부하 실험 설정이지 승인된 제품 계정 수/로그인 제한값이 아니다.** 공통 guard 잠금은 이 실험에서 256건 약 8.12초여서 무제한 확장성을 주장할 수 없다.

이 allocator는 실패예산과 별도 probe다. 실제 통합에서는 bucket뿐 아니라 attempt·LoginPreparation·CredentialSetup의 행 수/입력 크기/수명을 함께 제한해야 한다. 활성 실패창·cooldown·lease가 남은 ID를 삭제하면 제한을 우회하므로 마지막 유효 보안 상태가 끝나기 전에는 회수하면 안 된다. 실험 공통 TTL 30분을 제품의 인증/데이터 수명으로 채택하지 않는다. 생성 상한·기한 정리·정리 중 경합·검증 시작 전 예약 반환을 S1에서 통합 검사해야 한다. 공격자는 총량을 소진해 503을 유발할 수 있으나 제한을 삭제하거나 해시/상태를 무제한 허용하는 방식으로 복구하지 않는다.

## 4. 신뢰 HTTPS와 CSRF

`https_probe.py` + `browser_probe.cjs`: Playwright 1.62.1 / Chromium 151.0.7922.34, `chromiumSandbox:true`, `ignoreHTTPSErrors:false`. bubblewrap의 읽기 전용 시스템/별도 HOME mount에서 임시 CA를 NSS에 신뢰시켰고, Node 요청에는 같은 CA를 프로세스 한정 `NODE_EXTRA_CA_CERTS`로 지정했다. 시스템 설치나 전역 인증서 변경 없음.

**22개 boolean** 통과: 신뢰 HTTPS/secure context/no-store, `__Host-` preauth/auth의 Secure·HttpOnly·SameSite=Lax·Path, JS 비노출, nonce 누락/위조 거부, 같은 출처 요청/준비 소비, cookie 왕복, Origin 누락/위조·같은 사이트의 다른 포트 요청 차단, 독립 context 거부, 불신 인증서 음성 검사, fragment를 메모리로 이동하고 URL에서 제거, logout/삭제/복사 cookie 재사용 거부. 서버 측에서 정상 쓰기 1건만 발생하고 Origin 거부가 3건 이상임을 별도 확인했다. fragment는 GET 경로에 전달되지 않았다.

종료 시 listener 3개와 브라우저 종료, 기존 신뢰 파일 해시 동일. 이 서버는 임시 메모리 기반 원시 실험으로 제품 IAM/API/PG AuthSession/일회용 설정 token 상태기는 아니다. 설정 token의 30분·재발급·동시 소비, 실제 MFA/운영 프록시/다른 지원 브라우저는 검증하지 않았다. nonce/Origin 검사의 기술 근거를 실제 S1 route/UoW에 연결하는 인수가 필요하다.

## 실패 이력과 남은 검토

- 해시 probe 첫 실행은 의존성 목록의 들여쓰기된 주석을 Requirement로 읽어 실패했다. strip 후 주석 제외로 수정하고 정상/고의 False 검사를 실행했다.
- 브라우저 첫 실행의 Fetch `status()` 오용을 `status` 속성으로 수정했다. Chromium NSS만으로 Node APIRequest CA 신뢰가 구성되지 않아 임시 CA를 Node에도 지정했다. 불신 인증서 음성 검사 후 같은 페이지를 재사용하던 navigation 경합은 전용 페이지로 분리했다.
- Node 초기 오류가 가상 cookie/nonce를 포함한 요청 헤더를 출력했다. 해당 파일의 헤더를 제거하고 첫 줄/URL 비식별로 제한했으나 독립 tester의 canary 검사에서 첫 줄도 비밀을 포함할 수 있음이 확인됐다. 후속 수정에서 예외 메시지/stack을 전혀 읽거나 출력하지 않고 고정 코드 `PREP_HTTPS_PROBE_FAILED`와 exit 1만 내보내도록 변경했다. 해당 listener/가상 세션은 종료됐다. 정제된 실패 요약만 증거 묶음에 포함한다. `error_redaction_probe.py`는 실제 JS catch에 매번 새 canary를 첫째/둘째 예외 줄로 주입하고 stdout/stderr·작업 로그·zip 전 항목의 미포함, 고정 오류 코드와 exit 1, zip의 수정 스크립트 일치를 검사한다. canary 원문은 저장하지 않는다. 수정 후 정상 HTTPS 22개와 정리 검사를 다시 실행했다. DB DDL은 이 수정에서 수행하지 않았다.
- 이번에 Foundation fast/db pytest, 앱 migration, 실제 IAM 인수는 실행하지 않았다. 위 PG 실험을 기존 `bash check.sh db` 또는 실제 IAM 통합 통과로 대체하지 않는다.

중간 검토에서 판단할 구체안은 (1) 실제 corpus+보조 방어의 개발 S1 적합성, (2) 단일 worker 강제/해시 cap 2, (3) 성공 시 타 실패 보존·미완료 lease 처리 및 총량 제한을 실제 상태 모델에 통합하는 계약이다. 라이선스/공급·운영 언어 대표성, 다중 배포 및 트래픽 기준은 남는 한계다. 검토 전 앱 인증 구현을 시작하지 않으며, 검토자가 보완을 요구하면 해당 probe를 먼저 수정·재현한다.

## 재현

새 작업 소유 임시 디렉터리에 zip을 풀고 `bash run_probes.sh`를 실행한다. backend 원본 `.venv` Python, 현재 WSL Node/Chromium/Playwright 경로, `uv`, `openssl`, `bwrap`, `apt download`, 확인된 실행 중 `postgres-test`가 필요하다. apt 패키지는 임시 추출만 하며 전역 설치하지 않는다. DB DDL 슬롯은 오케스트레이터와 직렬화해야 한다. 스크립트는 같은 서비스의 새 무작위 schema만 정리한다. 모든 검증은 boolean `is True`/`===true` 또는 명시적 assertion으로 검사하며 누락·skip을 성공으로 처리하지 않는다. 묶음의 `run_probes.sh` 자체 전체 재실행은 하지 않았고, 구성 probe는 위 순서의 개별 명령으로 실행했다.
