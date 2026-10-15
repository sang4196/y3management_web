# IAM-001 구현 전 기술 사전검증

2026-10-12 C 승인 이후의 해석: [2026-10-12 C 일괄 승인](../product/product-decisions.md#review-20261012-c-batch)의 C1=2/C2–C13=1로 해결된 정책만 최신 설계/결정안에 반영했다. 아래 수치·추천/미결정과 실험 결과는 당시 기록이며 새 실험/구현 검증을 수행하지 않았다. 현재 암호 확인 본인 변경과 유효 인증/Scope·CSRF/MFA는 유지하고 중요 관리 5분 재인증 후보는 제외한다. 라이브러리/하네스/차단목록 적합성·모듈/잠금의 사전검증 한계는 그대로다.

2026-10-12 후속 정책 승인 안내: [2026-10-12 일괄 승인](../product/product-decisions.md#review-20261012-batch)으로 v1 인증 방식(ADR-0004 ACCEPTED)과 일부 계정/업무 정책이 이 실험 이후 승인됐다. 아래 PROPOSED/미승인·수치 유지 표현은 실험 작성 당시의 관찰 이력이다. 실험을 새 정책/제품 구현·운영 검증으로 재분류하거나 재실행한 것이 아니다. 차단목록 적합성·라이브러리/비용·실제 IAM/HTTPS/경합 검증의 미충족은 그대로 남는다.

Status: **기술 실험 결과 — 제품 구현·정책/인증 방식 채택 승인 아님**

확인일: 2026-09-18. 저장소: `main`, HEAD `b83defe3fc564b56d0f77cb075ddb5436759d191`.

[결정안](iam-001-decision-pack.md)의 기술 불확실성만 임시 환경에서 확인했다. **Python/고정 의존성과 해시 후보의 실행 호환성, 소형 실제 차단목록의 공급/조회, 전역 신뢰 저장소 변경 없는 HTTPS 브라우저 원시 실험은 확인했다. 차단목록의 보안 적합성과 실제 IAM 통합은 미해결이다.** D01~D12·S2 분리·수치·역할/상태·[ADR-0004](../decisions/0004-authentication-session.md) PROPOSED는 그대로다.

시작 Git 상태는 README tracked unstaged, decision-pack/설계/ADR-0004 untracked, staged 없음이었다. 작업 소유 경로는 `/tmp/y3-iam-preflight-o0qwlz8q`다. 실험 스크립트·가상 자료·결과는 오케스트레이터 재검토용으로 보존했고 띄운 listener/브라우저는 종료했다. 기존 개발/테스트 DB·Compose·볼륨에는 접근하거나 정리하지 않았다. backend의 코드·테스트·migration은 만들지 않았다.

## 1. 환경과 격리 방법

- WSL Ubuntu, kernel `6.18.33.2-microsoft-standard-WSL2`, x86_64/glibc 2.43, CPython 3.13.15, uv 0.12.16. CPU i7-6700 @ 3.40GHz, 논리 CPU 8개. 이 개발 머신 측정은 운영 사양/SLO가 아니다.
- backend의 `pyproject.toml`/`uv.lock`을 임시 `baseline/`에 복사하고 `uv export --locked --all-groups --no-emit-project --no-hashes`로 고정 버전을 추출했다. 원본 `.venv` 대신 임시 `hash-env/`를 만들고 `UV_CACHE_DIR`도 작업 경로 안으로 제한했다.
- Linux marker가 적용되는 기존 패키지 **41개는 정확한 버전을 유지**, Windows marker의 colorama/tzdata 2개는 설치 대상에서 제외했다. 신규 해시 관련 5개를 더해 46개이며 `uv pip check` 성공. 기존 lock 조합 변경을 요구하는 충돌은 관찰하지 않았다.
- Playwright 1.62.1과 Chromium 151.0.7922.34(revision 1234)는 WSL에 이미 있었다. 다른 저장소의 설치된 `playwright-core`와 기존 Chromium 파일을 **읽기 전용 마운트**로 재사용했다. 새 제품 프론트엔드·프레임워크·의존성 채택이 아니다. 전용 browser/computer MCP 도구는 발견되지 않아 로컬 실행 도구를 사용했다.
- bubblewrap 0.11.1로 별도 mount/user/pid/ipc namespace를 만들고 기존 HOME 환경변수는 바꾸지 않은 채 그 경로를 작업 소유 shadow-home에 매핑했다. 시스템 root는 읽기 전용, 쓰기 가능한 실험/프로필/TMPDIR은 `/tmp` 작업 경로뿐이다. 네트워크 namespace는 로컬 서버 접속을 위해 공유하되 실험 listener는 `127.0.0.1`에만 bind했다.

## 2. 해시 후보·출처·라이선스·호환성

| 배포 패키지 | 실제 설치 버전 / 출처 | 배포본 라이선스 확인 | 역할 |
| --- | --- | --- | --- |
| pwdlib | [0.3.1 PyPI](https://pypi.org/pypi/pwdlib/0.3.1/json) | wheel의 MIT LICENSE | `PasswordHash.recommended/hash/verify/verify_and_update` |
| argon2-cffi | [25.1.0 PyPI](https://pypi.org/pypi/argon2-cffi/25.1.0/json) | MIT | Argon2 고수준 구현 |
| argon2-cffi-bindings | [26.1.0 PyPI](https://pypi.org/pypi/argon2-cffi-bindings/26.1.0/json) | 배포본 MIT | cp310-abi3 manylinux_2_26/2_28 x86_64 native wheel |
| cffi | [2.1.1 PyPI](https://pypi.org/pypi/cffi/2.1.1/json) | MIT-0 | cp313 manylinux2014 native wheel |
| pycparser | [3.0 PyPI](https://pypi.org/pypi/pycparser/3.0/json) | BSD-3-Clause | cffi 의존성 |

PyPI의 정확한 버전 metadata 및 해당 플랫폼 wheel을 내려받아 게시 SHA-256을 대조하고, 설치된 원본 payload 70개 파일을 wheel과 바이트 비교했다. generated pyc·RECORD 및 설치기가 추가한 파일은 비교에서 제외했다. 라이선스 원문·metadata·wheel은 `sources/`, 전체 URL/크기/해시는 `package-artifacts.json`에 보존했다. metadata의 취약점 항목은 해당 5개 모두 빈 목록이었으나 별도 종합 취약점 감사·지원 수명·모든 vendored 코드의 법적 검토를 완료했다는 뜻은 아니다. 채택 시 공지/지원 상태를 다시 확인한다.

| wheel | SHA-256 |
| --- | --- |
| pwdlib-0.3.1-py3-none-any.whl | `944fa439198bed8ac3ea63dac76ea4ae43e2a35f4f21e9e725e82d3c2b97d6a5` |
| argon2_cffi-25.1.0-py3-none-any.whl | `fdc8b074db390fccb6eb4a3604ae7231f219aa669a2652e0f20e16ba513d5741` |
| argon2_cffi_bindings-26.1.0-cp310-abi3-manylinux_2_26_x86_64.manylinux_2_28_x86_64.whl | `27f1821903e2ceadcb88ec2b45ef190897b7682449c772f4d9b53e42c520cf29` |
| cffi-2.1.1-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl | `a931079504ecc49efed7744c476a5c343a92fabf66dec2db95edb1b2fdc770e2` |
| pycparser-3.0-py3-none-any.whl | `b727414169a36b7d524c1c3e31839a521725078d7b2ff038656844266160a992` |

`hash_probe.py`의 보정된 최종 실행에서 boolean 검사 **12개가 모두 True**였다. 매 실행 생성한 가상 암호만 사용했고 암호/encoded hash는 출력·결과 파일에 저장하지 않았다.

- 정상 검증, 오입력 거부, 매 hash의 새 salt, 현재 파라미터이면 불필요한 rehash 없음.
- 검증용 이전 비용(m=32768 KiB/t=2/p=2)의 hash를 `verify_and_update`로 현재 비용으로 갱신하고 새 hash 재검증. 틀린 암호는 갱신하지 않음. 이전 비용은 실계정 저장 추천값이 아니다.
- malformed hash는 **정확히 `pwdlib.exceptions.UnknownHashError`**로 거부. 임의 예외를 성공으로 세지 않음.
- 라이브러리는 NFC를 자동 적용하지 않는 것을 확인. 명시적 NFC 처리 후 동일 암호 검증은 성공하며 앞뒤 공백은 유의미했다. 길이·차단목록 등 제품 암호 정책은 라이브러리의 자동 보장이 아니다.
- 고정 FastAPI 0.141.1/Starlette 1.6.0/HTTPX 0.28.1의 임시 sync handler에서 hash 검증 성공. SQLAlchemy 2.0.54/psycopg 3.3.5/Alembic 1.20.0 import 확인. **DB 접속·실제 앱/IAM API는 시험하지 않았다.**

최초 스크립트는 Windows 전용 marker를 고려하지 않고 colorama 존재를 검사해 실패했다. marker-aware 비교로 수정했다. 그 뒤 오케스트레이터가 `bool`이 `int`의 subclass여서 False도 통과할 수 있는 판정식을 발견했다. 이를 `value is True`만 허용하는 `require_true`로 수정하고 count/제외 marker/예외 타입을 metadata 검사로 분리했다. `--inject-false`에서 **exit 1과 지정 실패 이름**을 확인한 후 정상 스크립트를 재실행해 exit 0을 확인했다. 아래 성능/성공 보고는 이 보정 후 결과만 사용한다. `hash-first-attempt.log`, `hash-negative.log`, `hash-negative-result.json`, `hash-results.json`을 보존했다. HTTPX fallback deprecation warning은 관찰됐고 숨기거나 의존성 변경으로 없애지 않았다.

### 소규모 비용 측정

관찰된 recommended 파라미터는 Argon2id v19, m=65536 KiB(64 MiB), t=3, p=4, salt 16 bytes, hash 32 bytes였다. [공식 API](https://argon2-cffi.readthedocs.io/en/stable/api.html)의 파라미터·rehash 기능을 참고했으며 제품 고정값으로 채택하지 않았다. 각 순차 측정은 warm-up 1회 후 12회다.

| 작업 | 중앙값 ms | 최소–최대 ms |
| --- | --- | --- |
| hash | 112.672 | 91.904–131.556 |
| verify | 177.180 | 120.132–238.064 |
| verify + 이전 비용 rehash | 181.174 | 152.503–321.356 |

독립 입력 12개 verify를 thread pool 1/2/4개로 실행한 wall time은 각각 1621.696/1173.043/1172.822 ms, 처리율은 7.40/10.23/10.23회/초였다. 전체 실험 프로세스 peak RSS는 337.96 MiB다. 이는 HTTP 라이브러리 import·모든 순차/병렬 실행이 합쳐진 최고치이며 요청당 메모리나 steady-state 사용량이 아니다. 4개 동시 hash는 Argon2 작업 영역만 명목상 256 MiB이며 별도 오버헤드가 있다.

표본이 작고 CPU 주파수/다른 작업/OS 스케줄링을 통제하지 않았다. p95·최대 처리량·운영 허용 로그인률·NAT 제한값·서비스 worker 수를 산출하지 않았다. D10의 수치나 D08 timeout을 이 측정으로 승인할 수 없다. 운영 CPU/메모리 상한에서 별도 부하·큐/동시 hash 제한 검증이 필요하다.

## 3. 실제 로컬 차단목록 공급 후보

**공급/조회 기술 후보:** SecLists의 `Passwords/Common-Credentials/xato-net-10-million-passwords-100000.txt`. 전체 유출 조합 자료나 대형 원본을 받지 않고 작은 password-only 파일 하나와 README/LICENSE만 받았다. 계정/이메일과 암호를 연결하는 자료는 수집하지 않았다.

- [고정 원본 파일](https://raw.githubusercontent.com/danielmiessler/SecLists/d9458f277ed978a608ad165e5eb2fdb389e4c7ee/Passwords/Common-Credentials/xato-net-10-million-passwords-100000.txt), commit `d9458f277ed978a608ad165e5eb2fdb389e4c7ee`.
- 781,879 bytes, 100,000행/100,000 고유 항목(빈 항목 1개 포함). SHA-256 `1472aafa2561df5e3293aee252aee3ca660c12b399a283cf808bb01b39be388b`.
- 해당 commit의 [SecLists LICENSE](https://github.com/danielmiessler/SecLists/blob/d9458f277ed978a608ad165e5eb2fdb389e4c7ee/LICENSE)는 MIT이며 저작권·허가 문구를 함께 배포하는 후보로 검토했다. [목록 README](https://github.com/danielmiessler/SecLists/blob/d9458f277ed978a608ad165e5eb2fdb389e4c7ee/Passwords/Common-Credentials/README.md)는 xato 원자료 유래를 명시한다. 확인 범위는 이 재배포 저장소의 게시 라이선스/출처이며 원자료 전체의 개별 권리를 독립적으로 검증한 법적 보증은 아니다.
- README/LICENSE도 `sources/manifest.json`에 고정 URL·크기·checksum과 함께 보존. 갱신 시 branch HEAD 자동 추종 대신 새 commit/license/diff/checksum/수량/분포를 검토하고 별도 artifact로 교체하는 방법을 추천한다. 갱신 책임 역할 후보는 backend 보안 의존성 담당자이며 운영 실명/주기는 미정이다.

`blocklist_probe.py`는 UTF-8 strict decode→LF 구분자 제거→NFC→정확한 전체 문자열 set 조회를 시험했다. trim/lower/casefold·부분문자열 거부는 적용하지 않았다. NFC 변화/충돌은 0이고 전체 실제 항목의 membership을 확인했다. 빈 항목 1개는 그대로 관찰·계수했으며 제품 공급 시 빈 행 제외 여부/개수 manifest를 명시해야 한다. 임의로 몇 단어만 만든 파일로 이 시험을 대체하지 않았다. 단일 실행 load 69.008 ms, 난수 기반 미포함 조회 1,000회의 중앙값 500 ns는 이 작은 파일의 기술 관찰값일 뿐 서비스 성능 보장이 아니다.

**중요 한계:** 이 파일은 전부 ASCII이고 길이 0–20자, 제안된 15–128자에 해당하는 항목은 **72개뿐**이다. D05의 긴 암호·한국어/Unicode·최근 유출 암호 차단 적합성을 해결하지 못한다. 이 파일을 단독으로 채택하여 “유출/흔한 암호 방어 완료”로 보고하지 않는다. exact matching은 대소문자 변형·공백 추가 등도 자동 차단하지 않는다. 해당 변형을 같은 암호로 취급하는 정책은 별도 검토 대상이다.

대안과 다음 선정 기준은 다음과 같다. 아래는 문서 확인/후보 제안이며 추가 corpus 설치·제품 정책 변경을 하지 않았다.

| 후보/접근 | 얻을 수 있는 것 | 추가 확인/한계 |
| --- | --- | --- |
| [Probable-Wordlists 원저장소](https://raw.githubusercontent.com/berzerk0/Probable-Wordlists/master/README.md)의 길이/문자 범위별 후보 | 다른 범위의 실제 빈도 자료를 비교할 후보 | [CC BY-SA 4.0](https://raw.githubusercontent.com/berzerk0/Probable-Wordlists/master/License.txt) 귀속·변경 표시·동일조건 배포 검토 필요. 긴/한국어 coverage·최신성 확인 전 해결안 아님; 대형 다운로드 미실행 |
| [HIBP Pwned Passwords](https://haveibeenpwned.com/API/v3#PwnedPasswords)의 offline hash 자료 | 외부로 입력을 보내지 않는 더 넓은 유출 corpus 후보 | 저장/검색/갱신 비용·배포 조건·정규화 의미 검토 필요. 전체 다운로드·API 질의 모두 미실행. SHA-1 조회 digest는 계정 암호 저장 방식이 아님 |
| 출처/허가가 명확한 긴 문구·한국어 자료 및 서비스 문맥 보조 목록 | 짧은 ASCII 빈도 목록의 공백을 보완할 후보 | 독립 선정/대표성·오탐 기준이 필요. 개발자가 만든 몇 개 문자열은 검사 보조일 뿐 제품 corpus를 대체하지 않음 |

최소 선정 체크는 15–128자 및 비ASCII 분포, 수집 시기/원출처·허가, 알려진 공개 사례에 대한 포함 범위, 정상 긴 문구의 오탐, 정규화/조회 방식, artifact 무결성/용량과 변경 대사다. 목표 coverage/오탐 수치는 미정이며 이번에 임의 승인하지 않는다. D05의 공급 구현 가능성과 **어느 보안 품질을 수용할 것인가**를 분리해야 한다.

## 4. HTTPS 브라우저 하네스 가능성

[Chromium Linux 인증서 문서](https://chromium.googlesource.com/chromium/src/+/HEAD/docs/linux/cert_management.md)의 NSS 저장 경로를 확인했다. M146 이후 기본 경로에 맞춰 **namespace 내부에서만 보이는 shadow-home의 `.local/share/pki/nssdb`**에 임시 CA를 넣었다. 호스트 사용자 `.pki/nssdb`/`.local/share/pki/nssdb`, 시스템 `/etc/ssl/certs`/`/usr/local/share/ca-certificates`는 변경하지 않았다.

certutil은 Ubuntu `libnss3-tools` 2:3.120-1ubuntu2.1의 627 kB deb를 `/tmp`에 다운로드·`dpkg-deb -x`로 추출해 사용했다. 시스템 package install/전역 trust import는 하지 않았다. deb SHA-256은 `80fd0c3717b6b3b63e0f82c92f1c050d7fed74ff646d871d8fd6e923eb38423d`다. OpenSSL로 2일짜리 가상 CA 및 localhost SAN 서버 인증서를 만들고, 별도 미신뢰 인증서도 음성 대조군으로 만들었다. private key는 해당 작업 경로에서 권한 0600이며 문서/출력에 복사하지 않았다.

임시 Python 표준 라이브러리 HTTPS 서버 3개를 loopback의 동적 port에만 열었다. 데이터는 메모리의 가상 probe cookie/nonce/counter뿐이다. 계정·인증 상태·역할·DB schema·IAM endpoint는 없다. Node/Playwright를 같은 namespace 안에서 실행해 Chromium sandbox를 켜고 `ignoreHTTPSErrors: false`로 검사했다. 인증서 오류 무시 flag/보안 비활성화 옵션은 사용하지 않았다. [Playwright BrowserType](https://playwright.dev/docs/api/class-browsertype)과 실제 실행 옵션을 참고했다.

| 실행한 원시 검사 | 결과 / 해석 |
| --- | --- |
| 신뢰한 임시 CA의 HTTPS 200·secure context | 통과 |
| Secure/HttpOnly/SameSite=Lax/Path=/·host cookie 속성 | 통과. 이 속성이 설정된 로컬 probe에 한정 |
| cookie 서버 왕복, JS에서 HttpOnly cookie 비노출 | 통과 |
| no-store, 동일 origin cookie+nonce 쓰기 허용 | 통과 |
| nonce 누락/위조 거부 | 각각 403 확인 |
| 같은 hostname·다른 port origin의 POST 거부 | Origin 거부 수 증가, 쓰기 수 불변. sibling origin과 SameSite가 서로 다른 경계임을 확인 |
| 별도 브라우저 context의 cookie 격리 | 통과 |
| 미신뢰 인증서 음성 대조 | 실제 `ERR_CERT_AUTHORITY_INVALID`로 거부. 오류 우회로 성공한 것이 아님 |
| 같은 cookie 속성으로 만료 응답 후 제거 | 통과 |

총 boolean **13개 True**, browser script exit 0. 최초 실행은 읽기 전용 `/tmp`에서 Playwright 임시 artifact 디렉터리를 만들 수 없어 실패했다. 작업 소유 `browser-tmp/`를 TMPDIR로 지정해 보정했고 최초 오류 로그도 보존했다. 브라우저 접근 로그·HAR·trace·스크린샷·영상은 수집하지 않았다.

**미검증:** 실제 IAM Cookie/CSRF 구현·로그인 fixation·활성화/로그아웃/철회·준비 token과 AuthSession의 결합, 실제 cross-site SameSite 전송/차단, HTTP에서 Secure cookie 전송 차단(특히 localhost 예외), 타 hostname Domain 공격, Windows/모바일 브라우저, 운영 reverse proxy/TLS, 부하/다중 worker. 임시 nonce 판정은 원시 동작 관찰용이며 제품 CSRF 라이브러리/설계 채택이나 보안 인수 완료가 아니다. Chromium 단일 런타임 성공은 지원 브라우저 목록 승인도 아니다.

실험 종료 시 3개 서버를 shutdown/close 후 각 port 연결 거부를 확인했다. `server-cleanup.json`에 `all_listeners_closed: true`. 브라우저는 finally에서 close했고, 전역 신뢰 파일 246개는 실험 전후 해시가 동일했다. 검토 뒤 정리할 수 있는 대상은 이 실험 경로의 파일뿐이며 기존 DB/볼륨은 포함하지 않는다.

## 5. 제품 설계와 실험 관리를 분리하는 문서 정정

사전검토에서 기존 D12의 24시간/전체 영역 폐기가 영속 서비스의 수명·삭제 정책처럼 읽힐 위험을 확인했다. 오케스트레이터에 구체 수정 문장을 보고한 후 **문서 정정 범위만** 승인받아 결정안·설계·ADR-0004·Architecture README의 관련 문장을 맞췄다. 이는 사용자의 제품 정책/인증 선택 승인으로 기록하지 않았다.

- **S1은 영속 PostgreSQL 기반 서비스의 첫 기능 증분**이다. 인수의 가상 데이터·24시간·소유 영역 폐기는 별도 실험/인수 하네스 관리 후보이며 **제품 수명/삭제 기본값으로 넣지 않는다.** 제품 startup reset·계정 TTL·24시간 감사 삭제를 구현할 근거가 아니다.
- 실제 제품 기록 수집·접근 정책의 D12/LEGAL-001 게이트는 유지한다. 기록 보존·필요 삭제는 O02와 관련 기능의 결정 전에 임의 확정하지 않는다. 허용된 임시 실험 도구·인증서·프로필·실행시간 같은 기술 상세마다 사용자 정책 승인을 반복 요구하지 않는다.
- D01~D12를 사용자 정책, 기술 선택 검토, 담당자 구현/하네스 상세로 구분했다. S2의 복구/재설정/Master 변경 분리는 잠정 추천이며 확정된 영구 금지 정책이 아니다. 기존 수치·역할·상태 전이는 바꾸지 않았다.
- 이전 “ㅇㅋ”, 보고 요청, 이번 사전검증 및 문서 정정 지시는 인증 정책·ADR ACCEPTED·실제 IAM 구현의 포괄 승인이 아니다.

## 6. 재현 명령과 증거 위치

실험 원본 경로는 `/tmp/y3-iam-preflight-o0qwlz8q`다. `/tmp`는 재부팅/정리로 사라질 수 있으므로 영구 재현 근거는 이 문서의 버전/해시/조건이며 스크립트는 현재 오케스트레이터 검토용이다. 결과를 덮어쓰지 않으려면 스크립트/자료를 새 작업 소유 `/tmp` 경로에 복사하고 별도 환경을 만든다. `setup_tls.sh`는 기존 TLS 증거가 있으면 종료하고 덮어쓰지 않는다. 인증서 만료 후에는 새 경로에서 다시 생성한다. 브라우저 하네스는 현재 WSL의 read-only 실행파일 경로가 전제이므로 다른 호스트에서는 검토한 동등 경로로 바꿔야 한다.

다음은 보존된 환경에서 재확인하는 명령이다. backend/.venv나 DB를 변경하지 않는다.

```bash
probe_root=/tmp/y3-iam-preflight-o0qwlz8q
"$probe_root/hash-env/bin/python" "$probe_root/hash_probe.py"
# 의도한 음성 검사: exit 1이어야 하며 정상 결과 파일은 갱신하지 않는다.
"$probe_root/hash-env/bin/python" "$probe_root/hash_probe.py" --inject-false
UV_CACHE_DIR="$probe_root/uv-cache" uv pip check --python "$probe_root/hash-env/bin/python"
"$probe_root/hash-env/bin/python" "$probe_root/package_artifacts.py"
python3 "$probe_root/blocklist_probe.py"
python3 "$probe_root/browser_harness.py"
```

환경 생성의 실제 방법은 `baseline/` 복사본을 대상으로 아래와 같았다. 다른 경로에서 재현하려면 먼저 두 파일을 그 작업 소유 `baseline/`에 복사한다. 명령은 저장소 원본 lock을 쓰기 대상으로 사용하지 않는다.

```bash
UV_CACHE_DIR="$probe_root/uv-cache" uv export --project "$probe_root/baseline" --locked --all-groups --no-emit-project --no-hashes --output-file "$probe_root/baseline-pins.txt"
UV_CACHE_DIR="$probe_root/uv-cache" uv venv --python /home/shlee/Workspace/ai/01.codex/y3management_web/backend/.venv/bin/python "$probe_root/hash-env"
UV_CACHE_DIR="$probe_root/uv-cache" uv pip install --python "$probe_root/hash-env/bin/python" -r "$probe_root/baseline-pins.txt" 'pwdlib[argon2]==0.3.1' 'argon2-cffi==25.1.0' 'argon2-cffi-bindings==26.1.0' 'cffi==2.1.1' 'pycparser==3.0'
```

최초 설치에서는 cffi/pycparser가 위 버전으로 해결됐으며 재현 명령에는 그 결과도 명시했다. 단순 버전 고정만으로 artifact 동일성을 보장하지 않으므로 보존한 wheel 및 위 checksum/`package-artifacts.json`도 대조한다. 브라우저 인증서/신뢰 설정 재현은 `setup_tls.sh`, mount/launch 전체 인자는 `browser-command.json`, 서버·프로필 생명주기는 `browser_harness.py`에서 검토할 수 있다. certutil 도구 준비는 새 작업 디렉터리에서 `apt download libnss3-tools=2:3.120-1ubuntu2.1` 후 그 deb만 `dpkg-deb -x`로 추출하는 방식이며 시스템 설치가 아니다.

| 임시 산출물 | 독립 검토할 근거 |
| --- | --- |
| `repo-before.json`, `README-before.md`, `venv-before.json` | 저장소 69개 파일·기존 .venv 4,427개 파일의 작업 시작 기준 |
| `baseline/`, `baseline-pins.txt`, `installed-pins.txt`, `install-hash.log`, `pip-check.log` | 기존 정확한 버전 유지·46개 호환 설치 |
| `hash_probe.py`, `hash-negative-result.json`, `hash-results.json` | 판정식/실패 주입/최종 비용·metadata |
| `package_artifacts.py`, `package-artifacts.json`, `sources/` | 정확한 배포본·해시·라이선스·설치 payload 비교 |
| `fetch_sources.py`, `sources/manifest.json`, `blocklist_probe.py`, `blocklist-results.json` | 차단목록 고정 출처/크기·분포·조회. fetch 스크립트 재실행은 HEAD를 다시 조회하므로 재현에는 기존 manifest의 고정 URL을 사용 |
| `setup_tls.sh`, `browser_harness.py`, `browser_probe.cjs`, `browser-command.json`, `browser-results.json` | 격리 trust·인증서 음성 대조·13개 원시 검사 |
| `browser-attempt-1.log`, `server-cleanup.json`, `trust-check.json`, `venv-check.json` | 초기 실패·listener 종료·전역 trust 및 원본 가상환경 불변 |

## 7. 남은 blocker와 다음 인계

| 구분 | 남은 일 / 책임 경계 |
| --- | --- |
| 기술 확인 완료 범위 | 현재 Python/고정 Linux 조합의 후보 설치·기본 해시/재해시 및 임시 HTTPS 원시 하네스 실행. 코드 채택 승인 아님 |
| 기술 미해결 | 차단목록 긴/한국어/최신 유출 coverage, 최종 공급 artifact 적합성, 운영 자원에서 해시 상한, 독립 프로젝트에서의 하네스 패키징. 현재 구현자를 통해 검토 가능 |
| 실제 사용자 정책 | Login ID·암호 규칙·전달/상태/수명·철회 UX·반복 제한·실제 기록 수집/접근. 기존 D 질문의 정책 부분은 미승인 그대로 |
| 후속 기능/운영 | 복구/추가·마지막 Master·재설정의 S2 범위, 운영 보존/삭제·MFA/복구/배포·지원 브라우저. 기술 실험으로 게이트를 닫지 않음 |
| 미실행 | backend fast/db 전체 재검사, PostgreSQL 로그인/인가/철회/감사/migration/경합, 실제 IAM 브라우저 Cookie/CSRF, 운영 배포. 기존 기반 검사 수치는 이전 기록 |

기술 후보 호환성과 하네스 가능성 때문에 더는 전역 인증서 변경을 선행조건으로 요구할 필요가 없다. 그러나 현재 원시 실험이 S1 인수 U1/P1/P2/C1/B1/B2를 통과한 것은 아니다. 제품 구현은 자동 시작하지 않고 이 결과를 오케스트레이터에게 넘긴다.


## 8. 변경 범위·문서 검증 결과

작업 시작 tracked/untracked 69개 파일 해시와 대조하여 변경은 Architecture README·IAM 설계·결정안·ADR-0004의 승인받은 문장 정정, 신규 preflight 문서 하나뿐임을 확인했다. backend/Product/AGENTS/ACCEPTED ADR/Foundation·WSL 기록/pyproject/uv.lock은 동일하다. backend/.venv 4,427개 일반 파일과 시스템/사용자 신뢰 저장소 246개 파일도 동일했다. HEAD/main 및 staged 없음 상태를 유지했고 commit/push/reset/checkout/clean/revert를 하지 않았다.

5개 문서의 로컬 링크/앵커 64개, 명시적 Product/기술 참조 ID 31개, Markdown 표 열 수·공백·conflict marker와 tracked `git diff --check`를 검사해 오류가 없었다. 정책 정정은 영속 제품과 임시 하네스의 분리 및 결정 책임의 구분에 한정했다. D04~D11의 수치·역할/전이, S2 후속 범위, Product OPEN 및 ADR PROPOSED를 유지했다. 증거는 `scope-and-doc-check.json`, `venv-check.json`, `trust-check.json`이며 실험 프로세스 종료와 12개 해시/13개 브라우저 boolean 및 음성 exit 1도 대조했다. 이 검사는 실제 IAM 기능·DB·운영 검증을 대신하지 않는다.
