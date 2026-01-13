# editor_config.json 데이터 흐름

## 파일 위치
`mcp_editor/editor_config.json`

## 생성 시점
- **최초 생성**: `python generate_editor_config.py` 실행 시
- **자동 생성**: 웹 에디터 시작 시 파일이 없으면 `_generate_config_from_template()` 호출
- **업데이트**: 프로필 생성/삭제 시 자동 갱신

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

## 소스 경로 (source_dir 불필요)

### 왜 source_dir이 필요 없는가?

`@mcp_service` 데코레이터 스캔 시 **파일 경로를 이미 알고 있습니다**.

```python
# 스캔 결과 - registry_{server}.json
{
  "services": {
    "query_mail_list": {
      "handler": {
        "file": "/home/user/mcp_outlook/outlook_service.py",  # ← 경로 있음
        "module_path": "mcp_outlook.outlook_service"
      }
    }
  }
}
```

### 스캔 방식

| 방식 | 설명 |
|------|------|
| **전체 스캔** | 프로젝트 루트에서 모든 `.py` 파일 스캔 |
| **자동 감지** | `@mcp_service` 데코레이터 발견 시 `server_name` 추출 |
| **경로 저장** | `registry_{server}.json`에 파일 경로 저장 |

### 지원 가능한 구조

어떤 구조든 **전체 스캔**으로 자동 감지:

```
# 구조 1: 형제 디렉토리
project/
├── mcp_editor/
├── mcp_outlook/        ← 자동 감지
└── mcp_calendar/       ← 자동 감지

# 구조 2: 웹에디터가 프로젝트 내부
mcp_outlook/
├── mcp_editor/
└── outlook_service.py  ← 자동 감지

# 구조 3: 다른 경로
project/
├── mcp_editor/
└── services/
    └── outlook/        ← 자동 감지
```

### 진실의 원천 (Single Source of Truth)

```
@mcp_service 데코레이터 (소스 코드)
         ↓ 스캔
registry_{server}.json (메타데이터)
         ↓ 참조
웹 에디터, 서버 실행
```

`registry_{server}.json`이 모든 경로 정보를 가지고 있으므로 `source_dir` 설정이 불필요합니다.

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
| `scan_codebase_for_servers()` | `generate_editor_config.py` | `@mcp_service` 데코레이터 스캔 |
| `scan_mcp_directories()` | `generate_editor_config.py` | `mcp_*` 디렉토리 스캔 |
| `generate_editor_config_json()` | `generate_editor_config.py` | 설정 파일 생성 |
| `extract_server_name_from_file()` | `generate_editor_config.py` | 파일에서 서버명 추출 |
| `detect_module_paths()` | `generate_editor_config.py` | 모듈 경로 탐지 |

### 자동 생성 흐름
```
프로젝트 루트 전체 스캔
    ├── @mcp_service(server_name="xxx") 추출
    └── 파일 경로 기록
           ↓
    server_name 병합
           ↓
    editor_config.json 생성
    registry_{server}.json 생성
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
editor_config.json          registry_{server}.json
─────────────────          ─────────────────────
프로필 설정                  서비스 메타데이터
├── 경로 설정                ├── handler.file (소스 경로)
├── 서버 설정 (host/port)    ├── handler.module_path
└── 프로필 관계              ├── parameters
                            └── metadata
         ↓                           ↓
    웹 에디터 UI              서비스 스캔/호출
```
