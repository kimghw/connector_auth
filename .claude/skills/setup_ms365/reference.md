# MS365 MCP STDIO 서버 배포 참고 문서

## 환경 요구사항

| 항목 | 요구 |
|------|------|
| OS | Windows (WSL에서 Windows 바이너리 호출) |
| Python | Windows 시스템 Python 3.10+ (`C:\Python3*\python.exe`) |
| venv 위치 | `/mnt/c/connector_auth/venv` (Windows: `C:\connector_auth\venv`) |
| 서버 엔트리포인트 | `mcp_{server_name}/mcp_server/server_stdio.py` |

## 지원 서버

| 서버명 | 엔트리포인트 | 설명 |
|--------|-------------|------|
| outlook | `mcp_outlook/mcp_server/server_stdio.py` | Outlook 메일 MCP 서버 |
| calendar | `mcp_calendar/mcp_server/server_stdio.py` | Calendar 일정 MCP 서버 |

> 새 서버 추가 시: `mcp_{name}/mcp_server/server_stdio.py`가 존재하면 자동 탐지됩니다.

## 핵심 의존성

| 패키지 | 용도 |
|--------|------|
| aiohttp | HTTP 비동기 클라이언트 (Graph API 호출) |
| pydantic | 데이터 모델 검증 |
| PyYAML | YAML 설정 파싱 |
| python-dotenv | .env 환경변수 로드 |
| fastapi, uvicorn | REST/Stream 프로토콜용 웹서버 |

전체 의존성: `/mnt/c/connector_auth/requirements.txt`

## 경로 매핑 (WSL ↔ Windows)

| WSL 경로 | Windows 경로 |
|----------|-------------|
| `/mnt/c/connector_auth/` | `C:\connector_auth\` |
| `/mnt/c/connector_auth/venv/Scripts/python.exe` | `C:\connector_auth\venv\Scripts\python.exe` |
| `/mnt/c/Users/<user>/AppData/Roaming/Claude/claude_desktop_config.json` | `%APPDATA%\Claude\claude_desktop_config.json` |

## Claude Desktop config 병합 규칙

- 소스: 프로젝트 루트의 `claude_desktop_config.json`
- 대상: Claude Desktop의 `claude_desktop_config.json`
- 지정된 `{server_name}` 항목만 upsert (같은 키 덮어쓰기, 없으면 추가)
- 대상의 `preferences` 등 기타 최상위 키는 유지
- 소스의 `mcpServers` 외 최상위 키는 무시

## 필수 환경변수 (Claude Desktop config env)

| 변수 | 값 | 용도 |
|------|-----|------|
| PYTHONPATH | `C:\connector_auth` | 프로젝트 모듈 import 경로 |
| PYTHONUTF8 | `1` | Windows UTF-8 모드 활성화 |
| PYTHONIOENCODING | `utf-8` | 입출력 인코딩 강제 |
