# 웹 에디터 Generate 동작 정리

## 버튼 클릭부터 생성까지의 흐름
- UI: `mcp_editor/templates/tool_editor.html`
  - `openGeneratorModal()`로 모달 표시
  - `runServerGeneration()`에서 `POST /api/server-generator`
- API: `mcp_editor/tool_editor_web.py`
  - `generate_server_from_web()`에서 경로 결정 후 `jinja/generate_universal_server.py` 실행

## Generate가 참조하는 입력/템플릿

### 입력(도구 정의) 파일
- `tools_path`는 Generator 모달 값 또는 기본값 사용
- 기본값은 프로파일 설정의 `template_definitions_path`
  - 예: `mcp_editor/<profile>/tool_definition_templates.py`
- 모듈 선택 시 우선순위
  - `<module>/mcp_server/tool_definition_templates.py` 또는 `<module>/mcp_server/tool_definitions.py`
  - 없으면 프로파일 기본값으로 fallback

### 템플릿(Jinja2) 파일
- `template_path`는 Generator 모달 값 또는 기본값 사용
- 기본값(`_get_template_for_server`) 매핑
  - 현재는 모든 서버가 `jinja/universal_server_template.jinja2` 사용 (outlook_server_template.jinja2, file_handler_server_template.jinja2는 더 이상 사용 안함)
  - 템플릿이 없으면: `jinja/mcp_server_scaffold_template.jinja2` 사용
- `jinja/universal_server_template.jinja2`는 모든 MCP 서버를 위한 통합 템플릿

### 레지스트리(서비스 메타데이터) 파일
- `jinja/generate_universal_server.py`가 registry를 자동 탐색
  - 경로: `mcp_editor/mcp_service_registry/registry_{server}.json`
  - 예: `registry_outlook.json`, `registry_file_handler.json`
  - 레지스트리는 각 서비스의 메타데이터, 함수 매핑, 디펜던시 정보 포함

## Generate로 생성/갱신되는 파일

### 출력 파일
- `output_path`에 `server.py` 생성
  - 기본값: `<tool_definitions_path>`와 같은 디렉토리의 `server.py`
    - 일반적으로 `mcp_{server}/mcp_server/server.py`
  - 모듈 선택 시: `<module>/mcp_server/server.py` 또는 `<module>/mcp/server.py`
- 웹 에디터 Generate는 백업을 만들지 않고 덮어씀

### 참고(런타임에서 사용되는 파일)
- `tool_internal_args.json`은 생성 시점에는 사용되지 않지만,
  생성된 `server.py`가 런타임에 읽을 수 있도록 템플릿에 포함됨
  - `jinja/universal_server_template.jinja2`는 `tool_internal_args.json` 로드 로직 포함
  - 각 MCP 서버 디렉토리에 위치 (예: `mcp_outlook/mcp_server/tool_internal_args.json`)

## 경로/서버명 결정 규칙 요약
- `server_name`은 프로파일명 또는 경로에서 추론
  - `mcp_editor/tool_editor_web_server_mappings.py` 기준
- `tools_path`, `template_path`, `output_path`는
  - 모달 입력값 > 모듈 기본값 > 프로파일 기본값 순으로 결정
- 경로는 `mcp_editor` 기준 상대경로 또는 repo root 기준 상대경로를 허용

## 현재 프로젝트 구조
### MCP 서버 디렉토리
- `mcp_outlook/`: Outlook 메일 처리 서버
  - `mcp_server/`: 서버 코드 (server.py, tool_definitions.py)
  - `outlook_service.py`, `graph_mail_query.py`: 핵심 서비스 로직
- `mcp_file_handler/`: 파일 처리 서버
  - `mcp_server/`: 서버 코드
  - `file_manager.py`: 파일 관리 로직

### 웹 에디터 디렉토리
- `mcp_editor/`: 웹 기반 MCP 도구 편집기
  - `tool_editor_web.py`: Flask 웹 서버
  - `templates/tool_editor.html`: UI 템플릿
  - `mcp_service_registry/`: 레지스트리 파일 저장소
    - `registry_outlook.json`, `registry_file_handler.json`
  - `mcp_outlook/`, `mcp_file_handler/`: 프로파일별 템플릿 정의

### Jinja 템플릿 디렉토리
- `jinja/`: 서버 코드 생성 템플릿
  - `generate_universal_server.py`: 통합 서버 생성기
  - `universal_server_template.jinja2`: 범용 서버 템플릿
  - `mcp_server_scaffold_template.jinja2`: 새 프로젝트 스캐폴드 템플릿
  - `scaffold_generator.py`: 새 MCP 프로젝트 생성기
