# MCP Server Scaffold Generator

새로운 MCP 서버 프로젝트를 자동으로 생성하는 도구입니다.

## 기능

- 완전한 MCP 서버 디렉토리 구조 생성
- FastAPI 기반 `server.py` 템플릿 생성
- 웹 에디터와 통합된 설정 파일 자동 업데이트
- Jinja2 템플릿 기반 서버 코드 생성

## 사용법

### CLI에서 사용

```bash
cd jinja

# 기본 사용
python scaffold_generator.py my_server

# 옵션 포함
python scaffold_generator.py calendar \
  --description "MCP server for Microsoft Graph Calendar API" \
  --port 8086

# 도움말
python scaffold_generator.py --help
```

### 웹 에디터에서 사용

웹 에디터([tool_editor_web.py](../mcp_editor/tool_editor_web.py))에서 제공하는 API를 통해 사용할 수 있습니다:

#### API 엔드포인트

**1. 서버 생성**

```http
POST /api/scaffold/create
Content-Type: application/json

{
  "server_name": "calendar",
  "description": "MCP server for calendar operations",
  "port": 8086
}
```

응답:
```json
{
  "success": true,
  "message": "Successfully created MCP server: calendar",
  "server_name": "calendar",
  "created_files": [...],
  "created_dirs": [...],
  "next_steps": [...]
}
```

**2. 서버 이름 유효성 검사**

```http
POST /api/scaffold/check
Content-Type: application/json

{
  "server_name": "calendar"
}
```

응답:
```json
{
  "valid": true,
  "exists": false,
  "server_name": "calendar",
  "path": "/path/to/mcp_calendar"
}
```

## 생성되는 파일 구조

```
mcp_{server_name}/
├── mcp_server/
│   ├── __init__.py              # 모듈 초기화
│   ├── server.py                # FastAPI 서버 (템플릿에서 생성)
│   ├── tool_definitions.py      # MCP 툴 정의 (웹 에디터에서 편집)
│   ├── mcp_decorators.py        # @mcp_service 데코레이터
│   ├── run.py                   # 서버 실행 스크립트
│   ├── README.md                # 서버 문서
│   └── backups/                 # 백업 디렉토리

mcp_editor/
└── tool_definition_{server_name}_templates.py  # 템플릿 (메타데이터 포함)

jinja/
└── {server_name}_server_template.jinja2        # Jinja2 템플릿

mcp_editor/editor_config.json   # 자동 업데이트 (새 프로필 추가)
```

## 생성된 서버 사용하기

### 1. 가상환경 설정

```bash
cd mcp_{server_name}/mcp_server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install fastapi uvicorn pydantic
```

### 2. 툴 정의 편집

```bash
cd ../../mcp_editor
./run_tool_editor.sh

# 브라우저에서:
# 1. 프로필 드롭다운에서 "{server_name}" 선택
# 2. "Add New Tool" 버튼으로 툴 추가
# 3. 파라미터, 스키마 편집
# 4. Save 버튼 클릭
```

### 3. 서비스 로직 구현

생성된 `server.py`의 `call_tool()` 함수에서 실제 비즈니스 로직을 구현합니다:

```python
# server.py

@app.post("/mcp/v1/tools/call")
async def call_tool(request: Request):
    body = await request.json()
    tool_name = body.get("name")
    arguments = body.get("arguments", {})

    # 툴별 라우팅
    if tool_name == "get_events":
        from calendar_service import get_calendar_events
        result = get_calendar_events(**arguments)
        return {"content": [{"type": "text", "text": json.dumps(result)}]}

    elif tool_name == "create_event":
        from calendar_service import create_calendar_event
        result = create_calendar_event(**arguments)
        return {"content": [{"type": "text", "text": json.dumps(result)}]}

    # ...
```

### 4. 서버 실행

```bash
cd mcp_{server_name}/mcp_server
./run.py
# 또는
python run.py
```

서버가 `http://localhost:{port}`에서 실행됩니다.

## 고급 기능

### 1. SessionManager 통합

생성된 서버는 자동으로 SessionManager를 지원합니다:

```python
# SessionManager가 있으면 자동으로 사용
if USE_SESSION_MANAGER:
    session = session_manager.get_session(session_id)
    # 세션별 상태 관리
```

### 2. 서버 템플릿 커스터마이징

생성된 Jinja2 템플릿을 수정하여 서버 구조를 커스터마이징할 수 있습니다:

```bash
# 템플릿 편집
nano jinja/{server_name}_server_template.jinja2

# 서버 재생성
cd jinja
python generate_{server_name}_server.py --replace
```

### 3. Pydantic 타입 통합

타입 정의 파일이 있으면 `editor_config.json`에서 지정:

```json
{
  "my_server": {
    "graph_types_files": ["../mcp_my_server/types.py"],
    ...
  }
}
```

웹 에디터에서 자동으로 Pydantic 모델을 JSON Schema로 변환합니다.

## 예제

### 예제 1: GitHub MCP 서버

```bash
python scaffold_generator.py github \
  --description "MCP server for GitHub API operations" \
  --port 8087

cd ../mcp_github
# github_service.py 구현
# types.py 추가 (Repository, Issue, PullRequest 등)
```

### 예제 2: Database MCP 서버

```bash
python scaffold_generator.py database \
  --description "MCP server for database operations" \
  --port 8088

cd ../mcp_database
# database_service.py 구현
# models.py 추가 (ORM 모델)
```

## 문제 해결

### 서버 이름이 이미 존재하는 경우

```
Error: Server 'mcp_calendar' already exists
```

- 다른 이름을 사용하거나
- 기존 서버를 삭제 후 재생성

### 포트가 이미 사용 중인 경우

- `--port` 옵션으로 다른 포트 지정
- 또는 생성 후 `run.py`에서 포트 수정

### 웹 에디터에서 새 프로필이 보이지 않는 경우

- 웹 에디터 재시작 (`./run_tool_editor.sh`)
- `editor_config.json`이 올바르게 업데이트되었는지 확인

## 참고

- [MCP Tool Editor README](../mcp_editor/README.md)
- [Jinja2 템플릿 문서](https://jinja.palletsprojects.com/)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
