# MCP 웹 에디터 로드/저장 정리

## 웹 에디터 실행 시 로드되는 스크립트/데이터

### 서버(백엔드) 초기 로드
- 실행 스크립트: `mcp_editor/tool_editor_web.py` (Flask)
- 설정 파일: `mcp_editor/editor_config.json`
  - `MCP_EDITOR_CONFIG` 환경변수로 경로 override 가능
  - 없으면 `jinja/editor_config_template.jinja2` + `jinja/generate_editor_config.py`로 생성 시도 후 `DEFAULT_PROFILE` 사용
- 주요 모듈 import:
  - `mcp_editor/pydantic_to_schema.py`
  - `mcp_editor/tool_editor_web_server_mappings.py`
  - `mcp_editor/mcp_service_registry/mcp_service_scanner.py`

### 클라이언트(프론트엔드) 로드
- 템플릿: `mcp_editor/templates/tool_editor.html` (inline JS/CSS)
- 정적 자산: `mcp_editor/static/brands/*.svg`

### window.onload 기준 초기 요청 흐름
1. `GET /api/profiles`
   - 소스: `mcp_editor/editor_config.json` (프로파일 목록, active)
2. `GET /api/tools?profile=...`
   - 우선 로드: `<template_definitions_path>` (tool_definition_templates.py)
   - fallback: `<tool_definitions_path>` (tool_definitions.py)
   - 함께 로드: `<internal_args_path>` (tool_internal_args.json), `file_mtimes`
3. `GET /api/server-generator/defaults`
   - 모듈 스캔 결과 + 기본 경로 (Generator 모달용)
4. `GET /api/template-sources`
   - 현재 템플릿 + 백업 목록 (backup_dir 기준)
5. `GET /api/mcp-services`
   - 레지스트리 우선순위:
     - `mcp_editor/mcp_service_registry/registry_{server}.json`
     - `mcp_editor/mcp_{server}/{server}_mcp_services.json`
     - `mcp_editor/{server}_mcp_services.json`
6. `GET /api/graph-types-properties`
   - `mcp_editor/mcp_service_registry/types_property_{server}.json`
   - `<profile>/types_properties.json` 또는 `mcp_editor/types_properties.json`
   - 필요 시 `mcp_editor/extract_graph_types.py` 실행
7. `GET /api/server/status`
   - MCP 서버 상태 확인 (이후 10초 간격 폴링)

### 경로 결정 규칙 (resolve_paths)
- `<template_definitions_path>` / `<tool_definitions_path>` / `<backup_dir>` / `<types_files>`는
  `editor_config.json`의 프로파일 설정에 의해 결정됨
- `<internal_args_path>`는 프로파일에 명시되지 않으면
  `<template_definitions_path>`와 같은 디렉토리의 `tool_internal_args.json`로 자동 생성

## Save 시 업데이트/생성되는 스크립트/데이터

### Save Tools 버튼 (POST `/api/tools/save-all`)
- 입력: `tools` + `internal_args` + `file_mtimes`
- 처리 흐름 (`save_all_definitions()`):
  1. 충돌 체크 (`file_mtimes`) + `internal_args` 검증/정리
  2. `internal`로 표시된 속성 제거 (`prune_internal_properties`)
  3. 백업 생성 (동일 타임스탬프, 확장자 `.bak`)
     - `tool_definitions.py_YYYYMMDD_HHMMSS.bak`
     - `tool_definition_templates.py_YYYYMMDD_HHMMSS.bak`
     - `tool_internal_args.json_YYYYMMDD_HHMMSS.bak`
  4. `tool_definitions.py` 갱신
     - `mcp_service` 제거, `default` 제거, `_source` 제거, description 개행 제거
  5. `tool_definition_templates.py` 갱신
     - `mcp_service` 메타데이터 포함
     - `registry_{server}.json`에서 시그니처/파라미터 주입 (없으면 빈 값)
  6. `tool_internal_args.json` 갱신
  7. 백업 정리 (최신 10개 유지)
- 저장 후 프론트는 `/api/tools` 재호출로 `file_mtimes` 갱신

### 참고: 개별 저장 API
- `POST /api/tools` → `tool_definitions.py` + `tool_definition_templates.py`만 갱신
- `POST /api/internal-args` → `tool_internal_args.json`만 갱신
