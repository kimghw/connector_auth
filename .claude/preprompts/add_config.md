# editor_config.json 업데이트 조건

## 자동 업데이트 시점

| 시점 | 명령/동작 | 타입/서비스 스캔 |
|------|----------|-----------------|
| 웹에디터 시작 | `python tool_editor_web.py` | O |
| sh 스크립트 실행 | `./run_tool_editor.sh` | O |
| 수동 생성 | `python jinja/generate_editor_config.py` | O |
| 서버 병합 | `merge` 명령 또는 웹 UI "Merge" | O |
| 새 프로젝트 생성 | 웹에디터 "New Project" | X (기본값만) |
| 파생 서버 생성 | 웹에디터 "Derive" | X |

## 서버 인식 조건

`@mcp_service` 데코레이터의 `server_name` 파라미터로 인식:

```python
@mcp_service(server_name="outlook")  # → "outlook" 프로필 생성
async def some_function():
    pass
```

## 자동 스캔 패턴

| 파일 유형 | 스캔 패턴 | 스캔 방식 |
|----------|----------|----------|
| 타입 파일 | `*_types.py` | 재귀 스캔 (rglob) |
| 서비스 파일 | `*_service.py` | 재귀 스캔 (rglob) |

## 스캔 제외 디렉토리

- `__pycache__`
- `venv`
- `node_modules`
- `test`, `tests`
- `.`으로 시작하는 숨김 폴더

## 관련 파일

- `jinja/generate_editor_config.py` - config 생성 스크립트
- `jinja/generate_universal_server.py` - 스캔 함수 정의 (`scan_types_files`, `scan_service_files`)
- `mcp_editor/tool_editor_core/app.py` - 웹에디터 시작 시 자동 호출

---
*Last Updated: 2026-01-11*
