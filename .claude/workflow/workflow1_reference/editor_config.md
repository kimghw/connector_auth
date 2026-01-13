# editor_config.json 데이터 흐름

## 파일 위치
`mcp_editor/editor_config.json`

## 생성 시점
- **최초 생성**: `python generate_editor_config.py` 실행 시
- **자동 생성**: 웹 에디터 시작 시 `app.py`가 자동으로 생성 스크립트 실행
- **업데이트**: 프로필 생성/삭제 시 자동 갱신

## 자동 설정 (데코레이터/JSDoc 기반)

**개발자는 `@mcp_service`만 설정하면 됩니다.** 나머지는 자동 처리됩니다.

### Python 프로젝트

데코레이터 방식으로 `server_name`을 지정합니다:

```python
@mcp_service(server_name="outlook")
async def query_mail_list(...):
    ...
```

### JavaScript 프로젝트

JSDoc 주석 방식으로 `@server_name`을 지정합니다:

```javascript
/**
 * @mcp_service
 * @server_name asset_management
 * @tool_name update_user_license
 * @description 선원 라이센스 수정
 * @param {number} id - 라이센스 레코드 ID
 * @param {Object} updateData - 수정할 라이센스 정보
 */
async function updateUserLicense(id, updateData) {
    ...
}
```

### 흐름
```
Python: @mcp_service(server_name="outlook")     ← 개발자가 설정
JavaScript: @mcp_service + @server_name xxx    ← 개발자가 설정
        ↓
웹 에디터 시작 (app.py)
        ↓
generate_editor_config.py 자동 실행
  - Python: AST 파싱으로 데코레이터에서 server_name 추출
  - JavaScript: 정규식으로 JSDoc에서 @server_name 추출
        ↓
editor_config.json 자동 생성/갱신
```

### 컨벤션 기반 자동 유추

| 설정 | 자동 생성 결과 |
|:-----|:--------------|
| `server_name="outlook"` (Python) | 경로: `../mcp_outlook`, 포트: 순차 할당 |
| `@server_name asset_management` (JS) | 경로: `../mcp_asset_management`, 포트: 순차 할당 |

### 수동 설정이 필요 없는 항목
- `template_definitions_path` → `mcp_{server_name}/tool_definition_templates.py`
- `tool_definitions_path` → `../mcp_{server_name}/mcp_server/tool_definitions.py`
- `backup_dir` → `mcp_{server_name}/backups`
- `types_files` → 자동 탐지 (`{server_name}_types.py` 등)
- `host` → `0.0.0.0`
- `port` → 8001부터 순차 할당

> **결론**: 수동으로 `editor_config.json`을 편집할 필요 없음

## 참조 파일 및 함수

| 파일 | 함수 | 용도 |
|:-----|:-----|:-----|
| `config.py` | `_load_config_file()` | 설정 파일 로딩 (메인 진입점) |
| `config.py` | `get_profile_config()` | 특정 프로필 설정 조회 |
| `config.py` | `list_profile_names()` | 프로필 목록 반환 |
| `config.py` | `save_config_file()` | 설정 파일 저장 |
| `config.py` | `get_source_path_for_profile()` | 소스 경로 유추 (컨벤션 기반) |
| `service_registry.py` | `scan_all_registries()` | 프로필별 스캔 경로 결정 |
| `profile_management.py` | `create_reused_profile()` | 재사용 프로필 추가 |
| `profile_management.py` | `create_derived_profile()` | 파생 프로필 생성 |
| `profile_management.py` | `delete_mcp_profile()` | 프로필 삭제 |
| `profile_routes.py` | `list_profiles()` | 프로필 목록 API (`GET /api/profiles`) |
| `profile_routes.py` | `create_profile()` | 프로필 생성 API (`POST /api/profiles`) |
| `server_routes.py` | `list_server_profiles()` | 서버 상태 조회 API (`GET /api/server/profiles`) |
| `server_routes.py` | `update_server_port()` | 포트 변경 API (`PUT /api/server/port`) |
| `app.py` | `run_app()` | 시작 시 자동 생성 트리거 |

> **참고**: MCP 서버 자체는 `editor_config.json`을 참조하지 않음. MCP 서버는 `tool_definitions.py`만 로드.

## 구조 예시
```json
{
  "calendar": {
    "template_definitions_path": "mcp_calendar/tool_definition_templates.py",
    "tool_definitions_path": "../mcp_calendar/mcp_server/tool_definitions.py",
    "backup_dir": "mcp_calendar/backups",
    "types_files": ["../mcp_calendar/calendar_types.py"],
    "host": "0.0.0.0",
    "port": 8001
  },
  "outlook": {
    "template_definitions_path": "mcp_outlook/tool_definition_templates.py",
    "tool_definitions_path": "../mcp_outlook/mcp_server/tool_definitions.py",
    "backup_dir": "mcp_outlook/backups",
    "types_files": ["../mcp_outlook/outlook_types.py"],
    "host": "0.0.0.0",
    "port": 8003,
    "is_base": true,
    "derived_profiles": ["outlook_read"]
  },
  "outlook_read": {
    "base_profile": "outlook",
    "is_reused": true
  }
}
```

> **포트 규칙**: `generate_editor_config.py` 실행 시 8001부터 순차 할당

## 프로필 스키마

| 필드 | 타입 | 설명 |
|:-----|:-----|:-----|
| `template_definitions_path` | str | 웹 에디터에서 편집하는 YAML 템플릿 경로 |
| `tool_definitions_path` | str | Jinja2로 생성될 Python 파일 경로 (MCP 서버가 로드) |
| `backup_dir` | str | 템플릿 저장 시 자동 백업 위치 |
| `types_files` | list | Pydantic/dataclass 타입 정의 파일 (타입 자동완성용) |
| `host` | str | MCP 서버 바인드 호스트 (기본: `0.0.0.0`) |
| `port` | int | MCP 서버 포트 번호 (프로필별 고유) |
| `is_base` | bool | Base 프로필 여부 (`true`면 부모가 될 수 있음) |
| `base_profile` | str | 파생된 부모 프로필명 |
| `derived_profiles` | list | Base에서 파생된 자식 프로필 목록 |
| `is_reused` | bool | 기존 서비스 재사용 여부 |

### 필드 관계도
```
[Base 프로필]                    [Derived 프로필]
is_base: true          ←───→     base_profile: "outlook"
derived_profiles: [...]          is_reused: true
```

---


## 읽기 (Load)

| 함수 | 파일 | 설명 |
|------|------|------|
| `_load_config_file()` | `config.py` | 메인 로딩 함수 |
| `get_profile_config()` | `config.py` | 특정 프로필 설정 조회 |
| `list_profile_names()` | `config.py` | 프로필 목록 조회 |
| `get_source_path_for_profile()` | `config.py` | 소스 경로 유추 (하위호환) |

### 로딩 흐름
```
1. MCP_EDITOR_CONFIG 환경변수 확인 → 없으면 기본 경로 사용
2. 파일 존재 시 JSON 파싱
3. 파일 없으면 _generate_config_from_template() 호출하여 자동 생성
```

---

## 쓰기 (Save)

| 함수 | 파일 | 설명 |
|------|------|------|
| `save_config_file()` | `config.py` | 설정 전체 저장 |
| `update_editor_config_for_reuse()` | `profile_management.py` | 재사용 프로필 추가 |
| `delete_mcp_profile()` | `profile_management.py` | 프로필 삭제 |

---

## 자동 생성 (Generate)

| 함수 | 파일 | 설명 |
|------|------|------|
| `scan_codebase_for_servers()` | `generate_editor_config.py` | Python/JS 통합 스캔 |
| `extract_server_name_from_py_file()` | `generate_editor_config.py` | Python AST 파싱 |
| `extract_server_name_from_js_file()` | `generate_editor_config.py` | JavaScript JSDoc 파싱 |
| `scan_mcp_directories()` | `generate_editor_config.py` | `mcp_*` 디렉토리 스캔 |
| `generate_editor_config_json()` | `generate_editor_config.py` | 설정 파일 생성 |
| `detect_module_paths()` | `generate_editor_config.py` | 모듈 경로 탐지 |

### 스캔 방식

| 언어 | 스캔 대상 | 파싱 방식 |
|------|----------|----------|
| **Python** | `*.py` | AST 파싱 → `@mcp_service(server_name="xxx")` 추출 |
| **JavaScript** | `*.js`, `*.mjs` | 정규식 → JSDoc `@mcp_service` + `@server_name xxx` 추출 |

### 자동 생성 흐름
```
프로젝트 루트 전체 스캔
    ├── [Python] @mcp_service(server_name="xxx") 추출 (AST 파싱)
    ├── [JavaScript] @mcp_service + @server_name xxx 추출 (JSDoc 정규식)
    └── 파일 경로 기록
           ↓
    server_name 병합
           ↓
    editor_config.json 생성
    mcp_{server}/registry_{server}.json 생성
```

---

## 파생 서버 지원 (Phase 1)

| 함수 | 파일 | 설명 |
|------|------|------|
| `get_base_profile()` | `config.py` | Base 프로필 조회 |
| `get_derived_profiles()` | `config.py` | 파생 프로필 목록 |
| `get_sibling_profiles()` | `config.py` | 형제 프로필 목록 |
| `is_base_profile()` | `config.py` | Base 여부 확인 |
| `get_profile_family()` | `config.py` | 프로필 패밀리 조회 |

### 프로필 관계
```
base 프로필 (outlook)
    ├── is_base: true
    └── derived_profiles: ["outlook_read", "outlook_write"]
              ↓
derived 프로필 (outlook_read)
    ├── base_profile: "outlook"
    └── is_reused: true
```

---

## 프로필 관리 함수

| 함수 | 파일 | 설명 |
|------|------|------|
| `copy_yaml_templates()` | `profile_management.py` | YAML 템플릿 복사 |
| `create_server_project_folder()` | `profile_management.py` | 서버 프로젝트 폴더 생성 |
| `create_reused_profile()` | `profile_management.py` | 재사용 프로필 생성 |
| `create_derived_profile()` | `profile_management.py` | 파생 프로필 생성 |
| `delete_mcp_server_only()` | `profile_management.py` | MCP 서버만 삭제 |

---

## 결과물 (Output)

editor_config.json이 사용되는 곳:

| 용도 | 설명 |
|------|------|
| 웹 에디터 프로필 전환 | 드롭다운에서 프로필 선택 |
| 템플릿 경로 해석 | `tool_definition_templates.yaml` 위치 |
| 서버 코드 생성 경로 | `tool_definitions.py` 출력 위치 |
| 타입 파일 참조 | Pydantic 타입 정의 경로 |
| 서버 실행 설정 | host/port 정보 |
| 파생 프로필 관리 | Base-Derived 관계 추적 |

---

## 환경 변수

| 변수 | 설명 |
|------|------|
| `MCP_EDITOR_CONFIG` | 설정 파일 경로 오버라이드 |

---

## 데이터 관계

```
editor_config.json          mcp_{server}/registry_{server}.json
─────────────────          ─────────────────────────────────────
프로필 설정                  서비스 메타데이터
├── 경로 설정                ├── handler.file (소스 경로)
├── 서버 설정 (host/port)    ├── handler.module_path
└── 프로필 관계              ├── parameters
                            └── metadata
         ↓                           ↓
    웹 에디터 UI              서비스 스캔/호출
```

## Registry 파일 경로

| 파일 | 경로 |
|------|------|
| **registry** | `mcp_editor/mcp_{server}/registry_{server}.json` |
| **types_property** | `mcp_editor/mcp_{server}/types_property_{server}.json` |

> **변경됨**: 기존 `mcp_service_registry/` 경로에서 `mcp_{server}/` 경로로 통일
