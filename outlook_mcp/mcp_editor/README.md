# MCP Tool Editor 개요

에디터가 참고/생성하는 주요 경로와 파일(`tool_editor_web.py`가 제공하는 CLI/UI):

- `tool_editor_web.py`: Flask 서버. 에디터 UI/API(`/api/tools`, `/api/mcp-services`, `/api/graph-types-properties` 등)를 제공하고 저장/백업을 처리.
- `templates/tool_editor.html`: 메인 프런트엔드. 프로퍼티 편집, graph_types 가져오기, MCP 서비스 시그니처 자동 채움, 기본값 입력, 저장/리로드 UI 제공.
- `tool_definition_templates.py`: 내부 메타데이터(`mcp_service` 등)와 기본값을 포함한 전체 도구 정의. **리로드 시 이 파일을 우선 읽음.**
- `../mcp_server/tool_definitions.py`: 런타임용 정리된 정의(내부 메타 제거, 기본값 제거). 저장 시 템플릿 파일과 함께 자동 생성.
- `backups/`: 저장 시마다 `tool_definitions.py` 백업을 생성(`tool_definitions_YYYYMMDD_HHMMSS.py` 등).
- `mcp_services.json` / `mcp_services_detailed.json`: MCP 서비스 이름과 파라미터 시그니처. MCP 서비스 드롭다운과 스키마 자동 채움에 사용.
- `graph_types_properties.json`: `outlook_mcp/graph_types.py`(FilterParams/ExcludeParams/SelectParams)에서 추출된 필드 목록. “Add from graph_types”에 사용.
- `pydantic_to_schema.py`: Pydantic 모델을 MCP 스키마로 변환하는 헬퍼. 백엔드 라우트에서 사용.
- `extract_graph_types.py`: 필요 시 `graph_types_properties.json`을 다시 생성.
- `editor_config.json`: 에디터 경로 설정 파일. 기본값으로 생성되며 아래 경로 키를 가진다:
  - `template_definitions_path`: 템플릿 도구 정의 파일 경로 (기본: `tool_definition_templates.py`)
  - `tool_definitions_path`: 런타임 도구 정의 파일 경로 (기본: `../mcp_server/tool_definitions.py`)
  - `backup_dir`: 백업 디렉터리 경로 (기본: `backups`)
  - `graph_types_files`: graph_types.py 위치 목록 (복수 지원, 기본: `["../graph_types.py"]`)

저장 시 생성/갱신:
- `tool_definition_templates.py`와 `../mcp_server/tool_definitions.py` 둘 다 업데이트.
- `backups/`에 백업 파일 추가.

리로드 동작:
- 에디터 리로드는 `tool_definition_templates.py`를 읽어 내부 메타데이터/기본값까지 모두 표시.
