# Azure Authentication Module

Azure AD OAuth 2.0 인증을 처리하는 Python 모듈입니다.

## 🆕 새로운 기능: MCP 서버 자동 생성

이제 웹 에디터 또는 CLI를 통해 **새로운 MCP 서버를 자동으로 생성**할 수 있습니다!

### 빠른 시작

```bash
# CLI로 새 서버 생성
cd jinja
python scaffold_generator.py my_server --description "My custom server" --port 8086

# 또는 웹 에디터에서 생성
cd mcp_editor
./run_tool_editor.sh
# 브라우저에서 "Create New Server" 버튼 클릭
```

자세한 내용은 [Scaffold Generator 문서](jinja/README_scaffold.md)를 참고하세요.

---

## 기능

- Azure AD OAuth 2.0 인증 플로우 구현
- 액세스 토큰 및 리프레시 토큰 관리
- 사용자 정보 및 세션 관리
- 토큰 자동 갱신
- 다중 Azure AD 앱 지원

## 데이터베이스 구조

### azure_app_info
Azure AD 앱 정보를 저장합니다.
- application_id: Azure AD 애플리케이션 ID
- client_secret: 클라이언트 시크릿
- tenant_id: 테넌트 ID
- redirect_uri: 리다이렉트 URI

### azure_user_info
로그인한 사용자 정보를 저장합니다.
- object_id: 사용자 고유 ID
- user_email: 사용자 이메일
- display_name: 표시 이름
- 기타 프로필 정보

### azure_session_info
인증 토큰 및 세션 정보를 관리합니다.
- session_id: 세션 고유 ID
- access_token: 액세스 토큰
- refresh_token: 리프레시 토큰
- expires_at: 토큰 만료 시간

## 설치

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 환경 변수 설정:
```bash
cp .env.example .env
# .env 파일을 편집하여 Azure AD 앱 정보 입력
```

## 사용 방법

### 1. 기본 사용

```python
from auth import AuthService

# 서비스 초기화
auth_service = AuthService()

# 인증 플로우 시작
auth_info = auth_service.start_auth_flow()
print(f"Auth URL: {auth_info['auth_url']}")

# 인증 완료 (콜백에서 받은 코드로)
session = await auth_service.complete_auth_flow(
    authorization_code="received_code",
    state=auth_info['state']
)
print(f"Session ID: {session['session_id']}")
```

### 2. 토큰 갱신

```python
# 자동 토큰 갱신이 포함된 유효한 토큰 가져오기
token = await auth_service.get_valid_token(session_id)
```

### 3. 세션 관리

```python
# 세션 정보 조회
session_info = auth_service.get_session_info(session_id)

# 로그아웃
auth_service.logout(session_id)

# 만료된 세션 정리
cleaned = auth_service.cleanup_expired_sessions()
```

## 환경 변수

- `AZURE_CLIENT_ID`: Azure AD 애플리케이션 ID
- `AZURE_CLIENT_SECRET`: Azure AD 클라이언트 시크릿
- `AZURE_TENANT_ID`: Azure AD 테넌트 ID (기본값: common)
- `AZURE_REDIRECT_URI`: OAuth 콜백 URI
- `DB_PATH`: 데이터베이스 파일 경로
- `LOG_LEVEL`: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)

## 주요 클래스

### AuthService
메인 인증 서비스 클래스로 전체 인증 플로우를 관리합니다.

### AzureConfig
Azure AD 설정 및 앱 정보를 관리합니다.

### OAuthClient
OAuth 2.0 프로토콜 구현 및 Azure AD와의 통신을 담당합니다.

### TokenManager
토큰 및 세션 정보를 데이터베이스에 저장/관리합니다.

## MCP 웹 에디터 시스템

MCP 서버의 Tool Definition을 웹 인터페이스에서 편집할 수 있는 시스템입니다.

### 1. editor_config.json 생성

#### 1.1 자동 생성 (권장)

`generate_editor_config.py` 스크립트를 사용하여 코드베이스를 스캔하고 자동으로 설정 파일을 생성합니다.

```bash
python jinja/generate_editor_config.py
```

**동작 방식:**
1. 프로젝트 전체를 스캔하여 `@mcp_service` 데코레이터를 찾음
2. 각 데코레이터의 `server_name` 파라미터 값을 추출
3. Jinja2 템플릿([editor_config_template.jinja2](jinja/editor_config_template.jinja2))을 사용하여 설정 파일 생성
4. 각 서버별 프로필을 자동으로 구성

**생성되는 설정 구조:**
```json
{
  "_default": {
    "template_definitions_path": "tool_definition_outlook_templates.py",
    "tool_definitions_path": "../mcp_outlook/mcp_server/tool_definitions.py",
    "backup_dir": "backups",
    "graph_types_files": ["../mcp_outlook/graph_types.py"],
    "host": "0.0.0.0",
    "port": 8091
  },
  "outlook": { ... },
  "file_handler": { ... }
}
```

#### 1.2 수동 생성

[mcp_editor/editor_config.json](mcp_editor/editor_config.json) 파일을 직접 작성할 수 있습니다.

**주요 설정 필드:**
- `template_definitions_path`: 템플릿 파일 경로 (mcp_service 메타데이터 포함)
- `tool_definitions_path`: 실제 Tool Definition 파일 경로 (깔끔한 버전)
- `backup_dir`: 백업 파일 저장 디렉토리
- `graph_types_files`: Pydantic 타입 정의 파일 목록
- `host`, `port`: 웹 서버 설정

### 2. 웹 에디터에서 Tool Definition 표출

#### 2.1 웹 서버 시작

```bash
cd mcp_editor
python tool_editor_web.py
```

또는 특정 프로필 지정:
```bash
MCP_EDITOR_MODULE=outlook python tool_editor_web.py
```

#### 2.2 데이터 로딩 프로세스

웹 에디터는 다음 순서로 Tool Definition을 로드합니다:

1. **설정 파일 읽기** ([tool_editor_web.py:68-82](mcp_editor/tool_editor_web.py#L68-L82))
   - `editor_config.json`에서 프로필 설정 로드
   - 환경 변수 `MCP_EDITOR_CONFIG`로 경로 override 가능

2. **템플릿 파일 우선 로딩** ([tool_editor_web.py:206-218](mcp_editor/tool_editor_web.py#L206-L218))
   ```python
   def load_tool_definitions(paths: dict):
       # 템플릿 파일 우선 (mcp_service 메타데이터 포함)
       if os.path.exists(paths["template_path"]):
           module = load_module(paths["template_path"])
           return module.MCP_TOOLS
       # Fallback: 깔끔한 정의 파일
       module = load_module(paths["tool_path"])
       return module.MCP_TOOLS
   ```

3. **API를 통한 데이터 전송** ([tool_editor_web.py:444-453](mcp_editor/tool_editor_web.py#L444-L453))
   - GET `/api/tools?profile=outlook`
   - 응답: `{"tools": [...], "profile": "outlook"}`

4. **웹 UI 렌더링**
   - JSON 데이터를 기반으로 폼 생성
   - `mcp_service` 메타데이터를 활용하여 서비스 매핑 정보 표시

### 3. 웹에서 데이터 편집 및 저장

#### 3.1 Save 버튼 동작

**프론트엔드:**
1. 사용자가 폼에서 Tool Definition 편집
2. "Save" 버튼 클릭
3. POST `/api/tools` 요청으로 JSON 데이터 전송

**백엔드 처리** ([tool_editor_web.py:456-469](mcp_editor/tool_editor_web.py#L456-L469)):
1. JSON 데이터 수신
2. `save_tool_definitions()` 함수 호출
3. **두 개의 파일 생성:**

   **a) tool_definitions.py** (깔끔한 버전)
   - `mcp_service`, `mcp_service_factors` 필드 제거
   - 스키마 필드 순서 정렬 (type → description → properties)
   - default 값 제거
   - Claude/OpenAI API에서 사용하는 공개 버전

   **b) tool_definition_{server}_templates.py** (템플릿 버전)
   - `mcp_service` 메타데이터 유지
   - AST 파싱으로 추출한 함수 시그니처 포함
   - 웹 에디터에서 다시 로드할 때 사용

4. **백업 생성** ([tool_editor_web.py:289-292](mcp_editor/tool_editor_web.py#L289-L292))
   ```python
   backup_filename = f"tool_definitions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
   backup_path = os.path.join(paths["backup_dir"], backup_filename)
   shutil.copy2(paths["tool_path"], backup_path)
   ```

#### 3.2 서비스 시그니처 추출

저장 시 자동으로 소스 코드에서 함수 시그니처를 추출합니다 ([tool_editor_web.py:363-374](mcp_editor/tool_editor_web.py#L363-L374)):

```python
signatures_by_name = get_signatures_by_name(scan_dir, server_name)
# 예: {"query_search": "user_email: str, search: str, top: int = 250"}

for tool in tools_data:
    if 'mcp_service' in tool:
        service_name = tool['mcp_service']['name']
        if service_name in signatures_by_name:
            tool['mcp_service']['signature'] = signatures_by_name[service_name]
```

### 4. 템플릿 생성 (Generate Server)

#### 4.1 Generate Server 버튼 동작

웹 에디터에서 "Generate Server Template" 버튼을 클릭하면 Jinja2 템플릿을 사용하여 MCP 서버 코드를 자동 생성합니다.

#### 4.2 생성 프로세스

**API 호출** ([tool_editor_web.py:795-852](mcp_editor/tool_editor_web.py#L795-L852)):
```http
POST /api/server-generator?profile=outlook
{
  "module": "mcp_outlook",
  "tools_path": "tool_definition_outlook_templates.py",
  "template_path": "../jinja/outlook_server_template.jinja2",
  "output_path": "../mcp_outlook/mcp_server/server_generated.py"
}
```

**서버 생성 단계:**
1. **모듈 자동 감지** ([tool_editor_web.py:143-183](mcp_editor/tool_editor_web.py#L143-L183))
   - `mcp_{name}`, `{name}_mcp` 패턴으로 디렉토리 검색
   - 각 모듈의 tool_definitions.py 경로 자동 탐지

2. **Jinja2 템플릿 로드**
   - 서버별 템플릿 사용 (예: `outlook_server_template.jinja2`)
   - Tool Definition을 템플릿 변수로 전달

3. **서버 코드 생성**
   - MCP 서버 기본 구조 생성
   - Tool Definition을 기반으로 핸들러 함수 매핑
   - `@mcp_tool` 데코레이터 자동 적용

4. **출력 파일 저장**
   - `{module}/mcp_server/server_generated.py`에 저장
   - 기존 파일 자동 덮어쓰기

#### 4.3 생성되는 파일 구조

```python
# server_generated.py 예시
from mcp_decorators import mcp_tool
from tool_definitions import MCP_TOOLS

@mcp_tool(
    tool_name="query_emails",
    description="Query and filter emails..."
)
async def handle_query_emails(**kwargs):
    # mcp_service 메타데이터 기반 함수 호출
    return await outlook_service.query_emails(**kwargs)
```

### 5. 파일 참조 관계

```
mcp_editor/
├── editor_config.json                    # 1. 설정 파일 (generate_editor_config.py로 생성)
├── tool_definition_{server}_templates.py # 2. 템플릿 (웹 에디터가 읽음)
└── tool_editor_web.py                    # 3. 웹 서버

mcp_{server}/mcp_server/
├── tool_definitions.py                   # 4. 깔끔한 정의 (Save 시 생성)
└── server_generated.py                   # 5. 서버 코드 (템플릿 생성 시 생성)

jinja/
├── generate_editor_config.py             # 설정 생성 스크립트
├── editor_config_template.jinja2         # 설정 파일 템플릿
├── generate_{server}_server.py           # 서버 생성 스크립트
└── {server}_server_template.jinja2       # 서버 코드 템플릿
```

### 6. 주요 워크플로우

#### 6.1 초기 설정
```bash
# 1. editor_config.json 자동 생성
python jinja/generate_editor_config.py

# 2. 웹 에디터 시작
cd mcp_editor
python tool_editor_web.py
```

#### 6.2 Tool Definition 편집
1. 웹 브라우저에서 `http://localhost:8091` 접속
2. 프로필 선택 (예: outlook, file_handler)
3. Tool Definition 편집
4. Save 버튼 클릭
   - → `tool_definitions.py` 갱신 (깔끔한 버전)
   - → `tool_definition_{server}_templates.py` 갱신 (메타데이터 포함)
   - → `backups/` 디렉토리에 백업 생성

#### 6.3 MCP 서버 코드 생성
1. "Generate Server Template" 버튼 클릭
2. 모듈 선택 (자동 감지된 목록에서)
3. 경로 확인 및 조정
4. Generate 클릭
   - → `server_generated.py` 생성
   - → MCP 서버 즉시 사용 가능

## 라이선스

MIT
