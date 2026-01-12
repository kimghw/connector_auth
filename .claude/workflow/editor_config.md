# editor_config.json 데이터 흐름

## 파일 위치
`mcp_editor/editor_config.json`

## 구조 예시
```json
{
  "calendar": {
    "template_definitions_path": "mcp_calendar/tool_definition_templates.yaml",
    "tool_definitions_path": "../mcp_calendar/mcp_server/tool_definitions.py",
    "backup_dir": "mcp_calendar/backups",
    "types_files": ["../mcp_calendar/calendar_types.py"],
    "host": "0.0.0.0",
    "port": 8094
  }
}
```

## 읽기 (Load)

| 함수 | 파일 | 설명 |
|------|------|------|
| `_load_config_file()` | `tool_editor_core/config.py:137` | 메인 로딩 함수 |
| `get_profile_config(profile_name)` | `tool_editor_core/config.py:183` | 특정 프로필 설정 조회 |
| `list_profile_names()` | `tool_editor_core/config.py:173` | 프로필 목록 조회 |

### 로딩 흐름
1. `MCP_EDITOR_CONFIG` 환경변수 확인 → 없으면 기본 경로 사용
2. 파일 존재 시 JSON 파싱
3. 파일 없으면 `_generate_config_from_template()` 호출하여 자동 생성

## 쓰기 (Save)

| 함수 | 파일 | 설명 |
|------|------|------|
| `save_config_file(config)` | `tool_editor_core/config.py:491` | 설정 전체 저장 |
| `update_editor_config_for_reuse()` | `tool_editor_core/profile_management.py:116` | 재사용 프로필 추가 |
| `delete_mcp_profile()` | `tool_editor_core/profile_management.py:259` | 프로필 삭제 |

## 자동 생성 (Generate)

| 함수 | 파일 | 설명 |
|------|------|------|
| `scan_codebase_for_servers()` | `generate_editor_config.py:58` | `@mcp_service` 데코레이터 스캔 |
| `scan_mcp_directories()` | `generate_editor_config.py:75` | `mcp_*` 디렉토리 스캔 |
| `generate_editor_config_json()` | `generate_editor_config.py:161` | 설정 파일 생성 |

### 자동 생성 흐름
```
codebase 스캔
    ├── @mcp_service(server_name="xxx") 추출
    └── mcp_*/mcp_server/ 디렉토리 탐색
           ↓
    서버 이름 병합
           ↓
    editor_config.json 생성
```

## 결과물 (Output)

editor_config.json이 사용되는 곳:

| 용도 | 설명 |
|------|------|
| 웹 에디터 프로필 전환 | 드롭다운에서 프로필 선택 |
| 템플릿 경로 해석 | `tool_definition_templates.yaml` 위치 |
| 서버 코드 생성 경로 | `tool_definitions.py` 출력 위치 |
| 타입 파일 참조 | Pydantic 타입 정의 경로 |
| 서버 실행 설정 | host/port 정보 |

## 프로필 관계

```
base 프로필 (outlook)
    ├── is_base: true
    └── derived_profiles: ["outlook_read", "outlook_write"]
              ↓
derived 프로필 (outlook_read)
    ├── base_profile: "outlook"
    ├── is_reused: true
    └── source_dir: "../mcp_outlook"  (base와 동일)
```
