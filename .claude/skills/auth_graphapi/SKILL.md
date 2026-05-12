---
name: auth_graphapi
description: Azure AD Graph API OAuth 인증 스킬. 사용자에게 Azure 자격증명을 받아 .env로 저장하고, 브라우저 OAuth 플로우를 실행해 Graph API 토큰을 auth.db에 채웁니다. .env가 이미 존재하면 입력 단계를 건너뜁니다.
---

# Azure AD Graph API OAuth 인증 스킬

**OAuth 2.0 Authorization Code Flow** 방식으로 동작합니다.

`mcp_outlook`, `mcp_calendar` 등 Graph API를 호출하는 MCP 서버가 사용할 토큰을 발급받아 `database/auth.db`에 저장합니다.

## OAuth Flow 종류

이 스킬은 **Authorization Code Flow** (인증 코드 흐름)를 사용합니다.

- **Grant Type**: `authorization_code`
- **흐름**:
  1. 사용자를 브라우저로 `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize`로 리다이렉트
  2. 사용자가 MS 계정 로그인 + 권한 동의
  3. Azure가 `AZURE_REDIRECT_URI`(기본 `http://localhost:5000/callback`)로 **authorization code**를 전달
  4. `callback_server.py`가 코드를 받아 `/oauth2/v2.0/token` 엔드포인트에서 **access_token + refresh_token**으로 교환
  5. 토큰을 `database/auth.db`(`azure_token_info` 테이블)에 저장
- **사용 이유**: 사용자가 직접 동의(consent)해야 하는 위임(delegated) 권한 시나리오 — Mail.Read, Calendars.ReadWrite 등 사용자 데이터 접근
- **대안 (이 스킬에서는 사용 안 함)**:
  - Client Credentials Flow → 사용자 없이 앱 자체 권한으로 동작 (백그라운드 서비스용)
  - Device Code Flow → 브라우저가 없는 디바이스용
  - Implicit Flow → 비권장(deprecated)

## 스킬 구성 파일

```
auth_graphapi/
└── SKILL.md     ← 실행 지침 (이 파일)
```

스크립트는 별도로 두지 않고 프로젝트 루트의 [_reauth.py](../../../_reauth.py)와 [session/auth_manager.py](../../../session/auth_manager.py)를 그대로 활용합니다.

> 코드 경로(`session/auth_manager.py`, `database/auth.db`)는 [1단계](#1단계-코드문서-경로-일치-확인)에서 자동 검증합니다. 불일치 시 사용자에게 묻고 진행합니다.

## 인자

- `/auth_graphapi` → 기본 OAuth 플로우 실행
- `/auth_graphapi --force` → `.env`가 이미 있어도 새로 입력받아 덮어쓰기

`--force` 여부를 `{force}` 플래그로 기억합니다.

---

## 사전 확인

다음 경로를 기준으로 동작합니다 (절대 경로 사용).

- 프로젝트 루트: `/home/kimghw/connector_auth`
- venv Python: `/home/kimghw/connector_auth/.venv/bin/python`
- `.env` 위치: `/home/kimghw/connector_auth/.env`
- `.env` 템플릿: `/home/kimghw/connector_auth/.env.example`
- 인증 스크립트: `/home/kimghw/connector_auth/_reauth.py`
- 인증 매니저 모듈: `/home/kimghw/connector_auth/session/auth_manager.py`
- 토큰 저장 DB: `/home/kimghw/connector_auth/database/auth.db`

---

## Instructions

아래 단계를 **순서대로** 자동 실행하세요.

### 1단계: 코드/문서 경로 일치 확인

이 스킬은 다음 두 경로를 가정합니다:

| 항목 | 문서 기준 경로 |
|---|---|
| 인증 매니저 모듈 | `session/auth_manager.py` |
| 토큰 저장 DB | `database/auth.db` |

코드가 실제로 사용하는 경로를 grep으로 확인:

```bash
# 인증 매니저 모듈 존재 확인
ls /home/kimghw/connector_auth/session/auth_manager.py 2>/dev/null \
  && echo "module_ok" || echo "module_missing"

# 코드에서 사용하는 DB 파일명 추출
grep -RhoE "['\"]?[A-Za-z_]*\.db['\"]?" \
  /home/kimghw/connector_auth/session/auth_manager.py \
  /home/kimghw/connector_auth/session/auth_database.py \
  /home/kimghw/connector_auth/session/azure_config.py 2>/dev/null \
  | sort -u
```

- 출력이 **문서 기준과 동일**(`auth.db`, `auth_manager.py`) → 2단계로 진행
- **불일치**(예: 코드가 `auth_graphapi.db`를 사용하거나, 모듈명이 다름) → 아래 `AskUserQuestion`으로 사용자 의사를 묻고 결정

**AskUserQuestion 예시 (불일치 발견 시에만 호출):**

- question: `"코드의 DB/모듈 경로가 문서와 다릅니다(코드: {발견된 경로}, 문서: auth.db / auth_manager.py). 어떻게 정렬할까요?"`
- header: `"경로 정렬"`
- multiSelect: `false`
- options:
  1. `label: "문서를 코드에 맞춤 (권장)"`, `description: "SKILL.md를 코드의 현재 경로로 갱신. 기존 DB/모듈 유지, 즉시 인증 진행 가능."`
  2. `label: "코드를 문서에 맞춰 변경"`, `description: "session/*.py 안의 DB/모듈 경로를 문서 기준으로 수정. 기존 DB 파일이 있으면 함께 rename 필요. 인증 전에 코드 수정/재테스트 필요."`
  3. `label: "이대로 진행 (불일치 무시)"`, `description: "이번 실행만 코드 경로 사용. SKILL.md/코드 모두 그대로 둠."`

선택 결과 처리:
- **옵션 1** → 본 SKILL.md 안의 `auth.db` / `auth_manager.py` 표기를 코드 실제값으로 일괄 치환(`Edit` 도구)
- **옵션 2** → 코드 파일에서 해당 경로 상수를 문서 기준으로 변경하고, 기존 DB가 있으면 `mv old.db new.db` 안내. 변경 후 `import` 동작을 `.venv/bin/python -c "from session.auth_manager import AuthManager"`로 확인
- **옵션 3** → 이번 세션에서만 코드 경로를 사용. 변경 없음

선택이 끝난 후 2단계로 진행합니다.

### 2단계: venv 존재 확인

```bash
ls /home/kimghw/connector_auth/.venv/bin/python 2>/dev/null
```

- 없으면 venv부터 생성:
  ```bash
  python3 -m venv /home/kimghw/connector_auth/.venv && \
  /home/kimghw/connector_auth/.venv/bin/pip install -r /home/kimghw/connector_auth/requirements.txt
  ```
- 생성 실패 → **중단** 후 사용자에게 안내

### 3단계: `.env` 파일 상태 확인

```bash
ls /home/kimghw/connector_auth/.env 2>/dev/null
```

- `.env`가 **이미 존재**하고 `{force}`가 false → 4단계 건너뛰고 5단계로
- `.env`가 **없거나** `{force}`가 true → 4단계로

### 4단계: Azure 자격증명 입력받기

`AskUserQuestion` 도구를 사용해 사용자에게 값을 받습니다. 다음 4개 항목을 한 번에 질문하세요 (multiSelect 사용 금지, 각각 single-select + "Other"로 직접 입력).

각 질문은 **단일 옵션 "직접 입력"만 제시**하고 사용자가 Other를 통해 실제 값을 넣게 합니다. 또는 더 자연스럽게 **AskUserQuestion 대신 사용자에게 "다음 4개 값을 한 번에 알려주세요" 형식으로 텍스트 요청**해도 됩니다 (권장).

수집할 필드:

| 환경변수 | 설명 | 필수 | 기본값 |
|---|---|---|---|
| `AZURE_CLIENT_ID` | Azure AD App의 Application (client) ID | 필수 | 없음 |
| `AZURE_CLIENT_SECRET` | Azure AD App의 Client Secret 값 | 필수 | 없음 |
| `AZURE_TENANT_ID` | Tenant ID (UUID) 또는 `common` | 필수 | `common` |
| `AZURE_REDIRECT_URI` | OAuth 콜백 URI | 선택 | `http://localhost:5000/callback` |
| `AZURE_SCOPES` | 권한 스코프 (쉼표 구분) | 선택 | `User.Read,Mail.Read` |

**검증 규칙:**
- `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`는 비어 있으면 **중단**, 다시 요청
- `AZURE_TENANT_ID`는 UUID 형식 또는 `common`/`organizations`/`consumers` 중 하나
- `AZURE_REDIRECT_URI`는 미입력 시 기본값 사용

### 5단계: `.env` 파일 생성/갱신

이미 `.env`가 있고 `{force}`가 true인 경우 백업:

```bash
cp /home/kimghw/connector_auth/.env /home/kimghw/connector_auth/.env.bak.$(date +%Y%m%d_%H%M%S)
```

`Write` 도구로 `.env`를 다음 포맷으로 작성:

```
# Azure AD OAuth 설정
AZURE_CLIENT_ID={CLIENT_ID}
AZURE_CLIENT_SECRET={CLIENT_SECRET}
AZURE_TENANT_ID={TENANT_ID}
AZURE_REDIRECT_URI={REDIRECT_URI}

# 선택적 설정
AZURE_AUTHORITY=https://login.microsoftonline.com
AZURE_SCOPES={SCOPES}
```

**민감정보 출력 금지:** 생성 후 `cat .env`로 값 노출하지 말 것. 라인 수만 확인.

```bash
wc -l /home/kimghw/connector_auth/.env
```

### 6단계: 기존 MCP 서버 프로세스 확인

콜백 서버 포트(기본 5000)가 다른 프로세스에 점유되어 있는지 확인:

```bash
ss -tlnp 2>/dev/null | grep ':5000 ' || echo "port 5000 free"
```

- 5000번 점유 시 → 사용자에게 알리고 종료 여부 확인

기존에 실행 중인 `server_stream.py`는 종료할 필요 없음 (포트 8091/8001 사용).

### 7단계: OAuth 인증 실행

```bash
cd /home/kimghw/connector_auth && /home/kimghw/connector_auth/.venv/bin/python _reauth.py
```

- 타임아웃 320초 (`_reauth.py` 내부 타임아웃이 300초)
- 백그라운드 실행하지 말 것 — 동기 실행 후 결과 확인
- 실행하면 브라우저가 열리거나 콘솔에 인증 URL이 출력됨
- 사용자가 브라우저에서 MS 계정 로그인 → 권한 동의 → `http://localhost:5000/callback`으로 리다이렉트
- `callback_server.py`가 코드를 받아 토큰 교환 → `auth.db`에 저장

**에러 처리:**
- `AADSTS50011` (redirect URI mismatch) → Azure Portal에서 앱의 Redirect URI에 `http://localhost:5000/callback`이 등록되어 있는지 확인 안내
- `AADSTS7000215` (invalid client secret) → Client Secret 값을 다시 입력받기 (`/auth_graphapi --force`로 재실행 안내)
- `AADSTS700016` (app not found in tenant) → `AZURE_TENANT_ID` 확인 안내
- 타임아웃 → 사용자가 브라우저 인증을 완료했는지 확인, 미완료면 다시 실행 안내
- 포트 5000 이미 점유 → 점유 프로세스 종료 안내

### 8단계: 토큰 저장 확인

```bash
/home/kimghw/connector_auth/.venv/bin/python -c "
import sqlite3
con = sqlite3.connect('/home/kimghw/connector_auth/database/auth.db')
cur = con.cursor()
cur.execute('SELECT COUNT(*) FROM azure_user_info')
user_count = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM azure_token_info')
token_count = cur.fetchone()[0]
print(f'users={user_count} tokens={token_count}')
if user_count > 0:
    cur.execute('SELECT user_email FROM azure_user_info LIMIT 1')
    print(f'first_user={cur.fetchone()[0]}')
con.close()
"
```

- `users=0 tokens=0` → 인증 실패. `_reauth.py` 출력을 다시 확인하고 7단계 재시도 안내
- `users>=1 tokens>=1` → 성공

### 9단계: 최종 요약

성공 시 다음 형식으로 출력:

```
✅ 인증 완료
- 사용자: {user_email}
- 토큰: 발급됨 (auth.db에 저장)
- 다음 단계: MCP 서버 실행 — .venv/bin/python mcp_outlook/mcp_server/server_stream.py
```

이미 server_stream.py가 실행 중인 경우, `.env` 변경을 반영하려면 **재시작 필요** 안내.

---

## 보안 주의사항

- `.env` 파일 내용을 채팅에 그대로 출력하지 말 것 (Client Secret이 평문 노출)
- `.env`는 `.gitignore`에 포함되어 있어야 함 — 누락 시 사용자에게 추가 권고
- `.env.bak.*` 백업 파일도 마찬가지로 커밋되지 않도록 유의
- 입력받은 자격증명은 절대 메모리(memory) 시스템에 저장하지 말 것

---

## Examples

**입력**: `/auth_graphapi`

```
1. 경로 일치 확인 OK (auth.db, auth_manager.py)
2. venv 확인 OK
3. .env 미존재 → 자격증명 입력 요청
4. 사용자 입력 수신 → .env 작성 완료 (8 lines)
5. 포트 5000 사용 가능
6. _reauth.py 실행 → 브라우저 인증 진행
7. 토큰 확인: users=1 tokens=1
✅ 인증 완료
   - 사용자: kimghw@krs.co.kr
   - 토큰: 발급됨
```

**입력**: `/auth_graphapi --force` (기존 .env 덮어쓰기)

```
1. 경로 일치 확인 OK
2. venv 확인 OK
3. .env 존재 + --force → 백업 후 재입력 요청 (.env.bak.20260512_133012 생성)
4. ...
```

**입력**: `/auth_graphapi` (코드가 다른 DB 파일명을 사용하는 경우)

```
1. 경로 일치 확인 → 불일치 발견 (코드: my_auth.db, 문서: auth.db)
   → AskUserQuestion 호출
   → 사용자가 "문서를 코드에 맞춤" 선택
   → SKILL.md를 my_auth.db로 갱신
2. venv 확인 OK
3. ...
```

---

## 주의사항

- 토큰을 수동으로 INSERT하지 말 것 — Microsoft가 발급한 서명된 값이라야 유효
- Azure Portal에서 앱 등록 시 Redirect URI에 `http://localhost:5000/callback` 등록 필수
- 권한 스코프는 `User.Read`, `Mail.Read`가 최소 — Send/Calendar 사용 시 `Mail.Send`, `Calendars.ReadWrite` 등 추가 필요
- WSL 환경에서 브라우저가 자동으로 안 열릴 수 있음 → `_reauth.py` 출력의 URL을 수동으로 복사해 Windows 브라우저에 붙여넣기
