# MCP Server Template 작성 가이드

Connector_auth 프로젝트의 Jinja2 템플릿/생성기를 기준으로 MCP 서버 코드를 만드는 방법을 설명합니다. 웹 에디터(`mcp_editor/tool_editor_web.py`), Internal Args, 통합 생성기(`jinja/generate_server.py`)를 모두 반영했습니다.

## 목차

1. [아키텍처 개요](#아키텍처-개요)
2. [파일 구조](#파일-구조)
3. [Tool Definition 작성](#tool-definition-작성)
4. [Internal Args 설정](#internal-args-설정)
5. [템플릿 변수](#템플릿-변수)
6. [템플릿 작성 패턴](#템플릿-작성-패턴)
7. [서버 생성 프로세스](#서버-생성-프로세스)
8. [트러블슈팅](#트러블슈팅)
9. [베스트 프랙티스](#베스트-프랙티스)
10. [관련 파일 참조](#관련-파일-참조)

---

## 아키텍처 개요

```
┌────────────────────────────────────────────────────────────┐
│ Web Editor (8091, tool_editor_web.py)                      │
│ - tool_definition_templates.py (메타데이터 포함)           │
│ - tool_definitions.py (클린 버전)                          │
│ - tool_internal_args.json (Internal Args)                  │
│ - editor_config.json / server mappings                     │
│   ↑ POST /api/tools/save-all (백업 + 충돌검사)             │
└───────────────┬────────────────────────────────────────────┘
                ▼
┌────────────────────────────────────────────────────────────┐
│ Jinja Generator (jinja/generate_server.py)                 │
│ - tool_internal_args.json 자동 로드                        │
│ - outlook/file_handler/scaffold 템플릿 자동 선택           │
│ - AST 시그니처/서비스 메타데이터 반영                     │
└───────────────┬────────────────────────────────────────────┘
                ▼
┌────────────────────────────────────────────────────────────┐
│ Generated Server (mcp_{server}/mcp_server/)                │
│ - server.py (SessionManager 지원, legacy fallback)         │
│ - mcp_decorators.py, tool_definitions.py                   │
└────────────────────────────────────────────────────────────┘
```

---

## 파일 구조

```
Connector_auth/
├── jinja/
│   ├── generate_server.py                # 템플릿 자동 선택 (outlook/file_handler/scaffold)
│   ├── generate_outlook_server.py        # 실제 분석/렌더링 + internal args 병합
│   ├── generate_server_mappings.py       # @mcp_service 스캔 → server mappings 생성
│   ├── outlook_server_template.jinja2    # Outlook + SessionManager 템플릿
│   ├── file_handler_server_template.jinja2
│   ├── mcp_server_scaffold_template.jinja2
│   └── scaffold_generator.py             # 새 MCP 서버 스캐폴드 생성
│
├── mcp_editor/
│   ├── tool_editor_web.py                # 웹 에디터/백엔드 API
│   ├── tool_editor_web_server_mappings.py# 자동 생성된 서버 매핑
│   ├── editor_config.json                # 프로필별 경로/포트/타입 파일
│   ├── backups/                          # 공용 백업 디렉토리
│   ├── outlook/
│   │   ├── tool_definition_templates.py  # 메타데이터 포함 템플릿 입력
│   │   ├── tool_internal_args.json       # Internal Args 저장소
│   │   └── backups/
│   └── file_handler/                     # 다른 서버 프로필도 동일 구조
│       ├── tool_definition_templates.py
│       ├── tool_internal_args.json
│       └── backups/
│
├── mcp_outlook/mcp_server/
│   ├── server.py                         # 생성된 MCP 서버
│   ├── tool_definitions.py               # 클라이언트에 노출되는 정의
│   └── mcp_decorators.py
└── mcp_file_handler/mcp_server/
    ├── server.py
    └── tool_definitions.py
```

- `tool_definition_templates.py`: `mcp_service` 메타데이터, 함수 시그니처, Internal Args 이동 여부를 포함 (웹 에디터가 읽음).
- `tool_definitions.py`: 메타데이터 제거된 클린 버전 (MCP `tools/list` 응답용).
- `tool_internal_args.json`: Internal Args 기본값/타입 저장 (웹 에디터 `Save All`로 동기화).

---

## Tool Definition 작성

### 기본 구조

```python
MCP_TOOLS = [
    {
        "name": "tool_name",                  # MCP 호출 시 사용되는 이름
        "description": "도구 설명",
        "inputSchema": {                      # JSON Schema (type=object 필수)
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "파라미터 설명"},
                "param2": {
                    "type": "object",
                    "baseModel": "FilterParams",  # Pydantic 클래스명
                    "description": "필터 파라미터"
                }
            },
            "required": ["param1"]
        },
        "mcp_service": {                      # 서비스 메서드 메타데이터
            "name": "query_filter",           # 실제 호출할 메서드명
            "class": "GraphMailQuery",        # 서비스 클래스 (없으면 이름/패턴으로 추론)
            "module": "graph_mail_query",     # import 경로
            "parameters": [                   # AST로 추출한 시그니처 정보
                {"name": "user_email", "type": "str", "is_required": True, "has_default": False},
                {"name": "filter", "type": "FilterParams", "is_required": True},
                {"name": "top", "type": "int", "has_default": True, "default": 450}
            ],
            "signature": "user_email: str, filter: FilterParams, top: int = 450"  # fallback
        }
    }
]
```

### inputSchema 파라미터 타입

| type | 설명 | 예시 |
|------|------|------|
| `string` | 문자열 | `{"type": "string"}` |
| `integer` | 정수 | `{"type": "integer"}` |
| `number` | 숫자 (실수 포함) | `{"type": "number"}` |
| `boolean` | 불리언 | `{"type": "boolean"}` |
| `array` | 배열 | `{"type": "array", "items": {"type": "string"}}` |
| `object` | Pydantic 모델 | `{"type": "object", "baseModel": "FilterParams"}` |

`mcp_service`를 비워두면 생성기가 도구 이름/패턴을 보고 `GraphMailQuery`, `GraphMailClient`, `FileManager`, `MetadataManager` 중에서 추론합니다. 명시적으로 `class`/`module`/`parameters`를 채워두면 import와 호출 시그니처가 더 정확해집니다.

---

## Internal Args 설정

Internal Args는 MCP inputSchema에 노출되지 않는 파라미터를 서버 내부에서 주입할 때 사용합니다. **웹 에디터의 `Save All`(`POST /api/tools/save-all`)을 사용하면 tool definitions와 함께 동기화되고, 세 파일을 동시에 백업/충돌검사합니다.**

### 파일 위치

```
mcp_editor/{profile}/tool_internal_args.json   # profile 예: outlook, file_handler
```

### 구조 예시

```json
{
  "tool_name": {
    "param_name": {
      "type": "SelectParams",          // 필수: Pydantic 클래스명
      "description": "설명",
      "was_required": false,           // 원래 required 여부 (웹 에디터에서 관리)
      "original_schema": {             // 기본값 추출용 스키마
        "type": "object",
        "baseModel": "SelectParams",
        "properties": {
          "fields": { "type": "array", "items": {"type": "string"}, "default": ["id", "subject"] }
        }
      },
      "value": {                       // 선택: 명시적 값. {}는 빈 생성자 의미
        "fields": ["id", "subject"]
      }
    }
  }
}
```

### type 필드 규칙

- 사용: Pydantic 클래스명 (`FilterParams`, `ExcludeParams`, `SelectParams`, 사용자 정의 모델 등)
- 금지: JSON Schema 타입 (`object`, `string`, `array`, `integer`, `boolean`, `null`)

### 값 해석 우선순위 (템플릿 `build_internal_param`)

1. **runtime_value**: 함수 호출 시 전달된 값(있다면)  
2. **value**: `tool_internal_args.json`에 저장된 값 (웹 에디터에서 설정)  
3. **original_schema.properties.*.default**: 스키마 기본값 병합  
4. 위가 모두 없으면 빈 생성자 호출

`enrich_internal_args_with_defaults()`가 `value`가 `{}`이고 `original_schema`에 default가 있을 때 자동으로 기본값을 채워 줍니다. 그래서 `{}`를 저장해도 default가 있다면 실제 생성 코드는 해당 기본값을 사용합니다.

---

## 템플릿 변수

### 전역 변수

| 변수 | 타입 | 설명 |
|------|------|------|
| `tools` | List[Dict] | 분석된 도구 목록 |
| `services` | Dict[str, Dict] | `{"GraphMailQuery": {"module": "graph_mail_query", "instance_name": "graph_mail_query"}}` |
| `param_types` | List[str] | import할 Pydantic/타입 목록 (Signature + Internal Args 합집합) |
| `modules` | List[str] | import할 모듈 이름 |
| `internal_args` | Dict | 전체 Internal Args |
| `server_name` | str | 서버 이름 (선택) |

### 도구별 변수 (`tool`)

| 변수 | 타입 | 설명 |
|------|------|------|
| `tool.name` | str | 도구 이름 |
| `tool.mcp_service` | str | 서비스 메서드 이름 (string으로 강제 세팅) |
| `tool.service_method` | str | 서비스 메서드 이름 (fallback) |
| `tool.service_class` | str | 서비스 클래스 이름 |
| `tool.params` | Dict | 일반 파라미터 정보 |
| `tool.object_params` | Dict | 객체 파라미터 정보 |
| `tool.call_params` | Dict | 서비스 호출 시 전달할 파라미터 (`internal_args` 포함) |
| `tool.internal_args` | Dict | 해당 도구의 Internal Args |

### `object_params` 구조

```python
{
    "filter": {
        "class_name": "FilterParams",
        "is_optional": False,
        "is_dict": True,
        "has_default": True,
        "default": None,
        "default_json": "None"
    }
}
```

### `internal_args` 구조

```python
{
    "select": {
        "type": "SelectParams",
        "value": {"fields": ["subject"]},  # 또는 {} 또는 미지정
        "original_schema": {...}
    }
}
```

---

## 템플릿 작성 패턴

### 1) Signature 파라미터 추출

```jinja2
{# 필수 파라미터 #}
{{ param_name }} = args["{{ param_name }}"]

{# 선택적 + 기본값: falsy 값을 보존하려면 is not None 체크 #}
{{ param_name }}_raw = args.get("{{ param_name }}")
{{ param_name }} = {{ param_name }}_raw if {{ param_name }}_raw is not None else {{ default_value }}

{# 선택적 + 기본값 없음 #}
{{ param_name }} = args.get("{{ param_name }}")
```

### 2) 객체 파라미터 변환

```jinja2
{# 필수 객체 #}
{{ param_name }}_params = {{ class_name }}(**args["{{ param_name }}"])

{# 선택적 + default 존재: None일 때만 default 사용 (빈 dict/array는 그대로) #}
{{ param_name }}_raw = args.get("{{ param_name }}")
if {{ param_name }}_raw is not None:
    {{ param_name }}_params = {{ class_name }}(**{{ param_name }}_raw)
else:
    {{ param_name }}_params = {{ class_name }}(**{{ default_json }})  {# default_json이 None이면 None 할당 #}

{# 선택적 + default 없음 #}
{{ param_name }}_raw = args.get("{{ param_name }}")
{{ param_name }}_params = {{ class_name }}(**{{ param_name }}_raw) if {{ param_name }}_raw is not None else None
```

### 3) Internal Args 주입

```jinja2
{%- if tool.internal_args %}
    # Internal Args (MCP 시그니처에 미노출)
    {%- for arg_name, arg_info in tool.internal_args.items() %}
    {%- if arg_info.value is defined and arg_info.value is not none and arg_info.value != {} %}
    {{ arg_name }}_params = {{ arg_info.type }}(**{{ arg_info.value | pprint }})   {# 값이 있으면 그대로 #}
    {%- elif arg_info.value is defined and arg_info.value == {} %}
    {{ arg_name }}_params = {{ arg_info.type }}()                                  {# 빈 객체는 빈 생성자 #}
    {%- else %}
    {{ arg_name }}_params = build_internal_param("{{ tool.name }}", "{{ arg_name }}") {# schema default / stored value #}
    {%- endif %}
    {%- endfor %}
{%- endif %}
```

`generate_outlook_server.py`가 Internal Args를 `call_params`에 자동 병합하기 때문에 서비스 호출 시 별도 인자를 잊어도 전달됩니다.

### 4) 서비스 인스턴스 선택

- 기본 규칙: 메서드 이름에 `query`/`search`가 포함되면 `get_query_instance`, 그렇지 않으면 `get_client_instance`.
- 파일/메타데이터 계열 도구 이름에 `file`/`convert`/`onedrive`/`metadata`가 들어가면 `FileManager`/`MetadataManager` 인스턴스를 사용.

### 5) 서비스 호출

```jinja2
return await service_instance.{{ tool.mcp_service or tool.service_method }}(
    user_email=user_email,
    {%- for param_name, param_info in tool.call_params.items() if param_name != 'user_email' %}
    {{ param_name }}={{ param_info.value }}{{ "," if not loop.last else "" }}
    {%- endfor %}
)
```

SessionManager가 존재하면 세션별 인스턴스를, 없으면 전역 인스턴스를 사용하는 코드가 템플릿에 포함되어 있습니다.

---

## 서버 생성 프로세스

### 1) CLI

권장: 통합 생성기 `jinja/generate_server.py` 사용 (템플릿 자동 선택 + internal args 로드).

```bash
# Outlook 서버 생성
python jinja/generate_server.py \
  --tools mcp_editor/outlook/tool_definition_templates.py \
  --server outlook \
  --output mcp_outlook/mcp_server/server.py

# File Handler 서버 생성
python jinja/generate_server.py \
  --tools mcp_editor/file_handler/tool_definition_templates.py \
  --server file_handler \
  --output mcp_file_handler/mcp_server/server.py

# 스캐폴드 템플릿만 렌더링 (도구 정의 없이)
python jinja/generate_server.py \
  --template jinja/mcp_server_scaffold_template.jinja2 \
  --output mcp_new/mcp_server/server.py \
  --server new_server
```

레거시 옵션: `jinja/generate_outlook_server.py --replace`를 사용하면 현재 `server.py`를 덮어쓰면서 백업(`backups/`)을 자동 생성합니다.

### 2) 웹 에디터

1. `cd mcp_editor && ./run_tool_editor.sh` (또는 `python tool_editor_web.py`)
2. 프로필 선택 → Tool Definition/타입/Internal Args 편집
3. **Save All** 버튼 → `tool_definitions.py`, `tool_definition_templates.py`, `tool_internal_args.json`을 한 번에 저장/백업/충돌 검사
4. **Generate Server** 버튼 → `/api/server-generator` 호출, 내부적으로 `generate_server.py` 실행 (module/template/paths 자동 감지)
5. 새 서버가 필요하면 **Create New Server** → `/api/scaffold/create`로 기본 디렉토리와 프로필을 생성

---

## 트러블슈팅

- `ImportError: cannot import name 'object'`  
  - 원인: Internal Args `type`에 JSON Schema 타입 사용  
  - 해결: `FilterParams`/`SelectParams` 등 Pydantic 클래스명으로 교체

- `Invalid internal_args: missing required 'type' field` (400)  
  - 원인: `tool_internal_args.json`에 `type` 누락 또는 구조가 dict가 아님  
  - 해결: 모든 Internal Arg에 `type` 추가, 구조를 `{ tool: { arg: {type, ...} } }`로 맞춤

- 409 Conflict (Save All)  
  - 원인: 파일이 외부에서 수정되어 mtime 불일치  
  - 해결: 최신 파일 다시 로드 후 저장 (백업은 유지)

- Internal Args가 코드에 반영되지 않음  
  - 원인: tool 이름 불일치 또는 `tool_internal_args.json` 경로 오탐  
  - 해결: tool 이름을 Tool Definition과 동일하게 맞추고, `Save All`로 세 파일을 동기화. 생성기 실행 시 `--tools` 경로와 프로필 경로가 맞는지 확인

- 템플릿 선택 오류 (`No valid server template found`)  
  - 원인: 서버 이름을 추론하지 못하거나 템플릿 경로가 잘못됨  
  - 해결: `--server` 또는 `--template`를 명시, 새 서버를 추가했다면 `python jinja/generate_server_mappings.py`로 매핑 파일을 재생성

---

## 베스트 프랙티스

- 웹 에디터에서는 반드시 **Save All**을 사용해 세 파일을 함께 저장/백업/충돌검사.
- 객체 파라미터에는 항상 `baseModel`을 지정하고, Internal Args의 `type`은 Pydantic 클래스명을 사용.
- Optional 값에 기본값을 줄 때는 스키마의 `default`로 입력하면 템플릿이 `None`과 구분해 처리.
- 새 서버/프로필을 추가하면 `python jinja/generate_editor_config.py`와 `python jinja/generate_server_mappings.py`로 설정/매핑을 재생성.
- `mcp_service.parameters`를 최신으로 유지하려면 웹 에디터 저장 시 `force_rescan=true`를 사용하거나 서비스 코드를 수정한 뒤 다시 저장.
- 도구 이름은 소문자/스네이크 케이스(`mail_list`, `query_emails`)로 명확히 동작을 드러내도록 작성.

---

## 관련 파일 참조

- `jinja/generate_server.py` – 템플릿 자동 선택 통합 생성기
- `jinja/outlook_server_template.jinja2` / `jinja/file_handler_server_template.jinja2` – 서버 템플릿
- `jinja/mcp_server_scaffold_template.jinja2` – 신규 서버 스캐폴드 템플릿
- `mcp_editor/tool_editor_web.py` – 웹 에디터/생성기 API
- `mcp_editor/tool_editor_web_server_mappings.py` – 자동 생성된 서버 매핑
- `mcp_editor/run_tool_editor.sh` – 웹 에디터 실행 스크립트
- `mcp_outlook/mcp_server/server.py`, `mcp_file_handler/mcp_server/server.py` – 생성된 서버 코드 예제
