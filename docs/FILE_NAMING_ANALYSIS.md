# 파일 네이밍 규칙 및 일관성 분석

## 🌐 웹 에디터 데이터 흐름 (JavaScript → Python)

### 1. 데이터 생성 흐름
```
JavaScript (브라우저)
    ↓
    tools[] 배열 + internalArgs{} 객체 생성
    ↓
    POST /api/save-all (JSON 전송)
    ↓
Python (Flask 백엔드)
    ↓
    파일 시스템에 저장 (.py, .json)
```

### 2. JavaScript에서 생성되는 데이터 구조
```javascript
{
    "tools": [...],           // 툴 정의 배열
    "internal_args": {...},   // Internal Args 객체
    "file_mtimes": {...}      // 파일 충돌 감지용
}
```

## 📁 파일 네이밍 패턴 분석

### 1. 툴 정의 파일

| 파일명 | 위치 | 패턴 | 일관성 |
|--------|------|------|---------|
| `tool_definition_templates.py` | `mcp_{server}/` | `tool_definition_templates.py` | ✅ 일관됨 |
| `tool_definitions.py` | `../mcp_{server}/mcp_server/` | `tool_definitions.py` | ✅ 일관됨 |
| `tool_internal_args.json` | `mcp_{server}/` | `tool_internal_args.json` | ✅ 일관됨 |

### 2. 레지스트리 파일

| 파일명 | 위치 | 패턴 | 일관성 |
|--------|------|------|---------|
| `registry_{server}.json` | `mcp_service_registry/` | `registry_outlook.json`<br>`registry_file_handler.json` | ✅ 일관됨 |
| `types_property_{server}.json` | `mcp_service_registry/` | `types_property_outlook.json` | ✅ 일관됨 |

### 3. 서비스 파일 (레거시)

| 파일명 | 위치 | 패턴 | 일관성 |
|--------|------|------|---------|
| `{server}_mcp_services.json` | `mcp_{server}/` | `outlook_mcp_services.json`<br>`file_handler_mcp_services.json` | ✅ 일관됨 |
| `{server}_mcp_services_detailed.json` | `mcp_{server}/` | `outlook_mcp_services_detailed.json` | ✅ 일관됨 |

### 4. 백업 파일

| 파일명 | 위치 | 패턴 | 일관성 |
|--------|------|------|---------|
| `tool_definitions_{timestamp}.py` | `mcp_{server}/backups/` | `tool_definitions_20251218_134029.py` | ✅ 일관됨 |
| `tool_definition_templates_{timestamp}.py` | `mcp_{server}/backups/` | 동일 패턴 | ✅ 일관됨 |
| `tool_internal_args_{timestamp}.json` | `mcp_{server}/backups/` | 동일 패턴 | ✅ 일관됨 |

### 5. 타입 파일

| 파일명 | 위치 | 패턴 | 일관성 |
|--------|------|------|---------|
| `{server}_types.py` | `../mcp_{server}/` | `outlook_types.py` | ✅ 일관됨 |
| `types.py` | `../mcp_{server}/` | Fallback 옵션 | ✅ 일관됨 |
| `graph_types.py` | `../mcp_{server}/` | 특수 케이스 | ✅ 일관됨 |

## ✅ 일관성 개선 완료 (2025-12-21)

### 적용된 변경
- `types_property_mcp_outlook.json` → `types_property_outlook.json` 파일명 정규화
- DEFAULT_PROFILE 기본 경로: `../outlook_mcp` → `../mcp_outlook`
- SERVER_NAMES/템플릿 키를 decorator 값(`outlook`, `file_handler`)에 맞춤
- Pydantic schema 로더 기본 경로 정정: `../mcp_outlook`

### 현재 네이밍 규칙 (정식)
```python
def get_registry_filename(server_name: str) -> str:
    return f"registry_{server_name}.json"

def get_types_property_filename(server_name: str) -> str:
    return f"types_property_{server_name}.json"
```

### 현재 경로 구조
```
mcp_editor/
  mcp_{server}/
    tool_definition_templates.py
    tool_internal_args.json
    backups/

mcp_service_registry/
    registry_{server}.json
    types_property_{server}.json

../mcp_{server}/
    mcp_server/
      tool_definitions.py
```

### 레거시 파일 참고
- `{server}_mcp_services.json` 및 `{server}_mcp_services_detailed.json`은 레거시 호환용으로 유지

### 잔여 작업
- 현재 기준에서는 추가 수정 필요 없음 (레거시 정리 여부만 선택)
