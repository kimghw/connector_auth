# MCP Server Template 작성 가이드

Connector_auth 프로젝트의 **Jinja2 템플릿 기반 MCP 서버 자동 생성 시스템**을 사용하여 MCP 서버를 개발하는 완벽한 가이드입니다.

## 목차

1. [아키텍처 개요](#아키텍처-개요)
2. [Jinja 템플릿 시스템](#jinja-템플릿-시스템)
3. [파일 구조](#파일-구조)
4. [Tool Definition 작성](#tool-definition-작성)
5. [Internal Args 설정](#internal-args-설정)
6. [템플릿 변수](#템플릿-변수)
7. [서버 생성 프로세스](#서버-생성-프로세스)
8. [템플릿 작성 패턴](#템플릿-작성-패턴)
9. [트러블슈팅](#트러블슈팅)
10. [베스트 프랙티스](#베스트-프랙티스)
11. [관련 파일 참조](#관련-파일-참조)

---

## 아키텍처 개요

```
┌────────────────────────────────────────────────────────────┐
│ Tool Definitions & Internal Args                           │
│ - mcp_editor/{server}/tool_definition_templates.py         │
│ - mcp_editor/{server}/tool_internal_args.json              │
│   ↓ (입력)                                                 │
└───────────────┬────────────────────────────────────────────┘
                ▼
┌────────────────────────────────────────────────────────────┐
│ Jinja2 Template System (jinja/)                            │
│ - generate_server.py (통합 생성기)                         │
│ - generate_outlook_server.py (서비스 분석 & 렌더링)        │
│ - outlook_server_template.jinja2 (템플릿)                  │
│ - file_handler_server_template.jinja2 (템플릿)             │
│   ↓ (자동 생성)                                            │
└───────────────┬────────────────────────────────────────────┘
                ▼
┌────────────────────────────────────────────────────────────┐
│ Generated MCP Server (mcp_{server}/mcp_server/)            │
│ - server.py (완전한 MCP 서버 코드)                         │
│ - tool_definitions.py (클라이언트용 스키마)                │
│ - mcp_decorators.py (데코레이터)                           │
└────────────────────────────────────────────────────────────┘
```

---

## Jinja 템플릿 시스템

### 핵심 개념

Jinja2 템플릿 시스템은 **Tool Definitions에서 완전한 MCP 서버 코드를 자동 생성**하는 강력한 도구입니다.

### 주요 기능

✅ **자동 코드 생성**: Tool definitions → 완전한 server.py
✅ **타입 변환**: Object 파라미터를 Pydantic 클래스로 자동 변환
✅ **Internal Args 주입**: 내부 파라미터 자동 관리
✅ **동적 Import**: 필요한 모듈과 타입 자동 import
✅ **서비스 매핑**: @mcp_service 데코레이터 기반 자동 연결
✅ **템플릿 선택**: 서버 타입에 따른 템플릿 자동 선택

### 왜 Jinja가 핵심인가?

1. **개발 속도**: 수동으로 서버 코드를 작성하는 대신 자동 생성
2. **일관성**: 모든 서버가 동일한 패턴과 구조를 따름
3. **유지보수**: 템플릿만 수정하면 모든 서버에 변경사항 적용
4. **타입 안정성**: AST 분석을 통한 정확한 타입 추론
5. **확장성**: 새로운 서버 타입을 쉽게 추가 가능

---

## 파일 구조

```
Connector_auth/
├── jinja/                                  # 🔥 Jinja 템플릿 시스템 (핵심!)
│   ├── generate_server.py                 # 통합 서버 생성기
│   ├── generate_outlook_server.py         # Outlook 서버 분석 & 생성 (1179줄의 마법)
│   ├── generate_file_handler_server.py    # 파일 핸들러 서버 생성기
│   ├── generate_editor_config.py          # editor_config.json 자동 생성
│   ├── generate_server_mappings.py        # @mcp_service 스캔 → 매핑 생성
│   ├── scaffold_generator.py              # 새 MCP 서버 스캐폴드 생성
│   │
│   ├── outlook_server_template.jinja2     # Outlook 서버 템플릿
│   ├── file_handler_server_template.jinja2# 파일 핸들러 템플릿
│   ├── mcp_server_scaffold_template.jinja2# 새 서버 기본 템플릿
│   ├── editor_config_template.jinja2      # 설정 파일 템플릿
│   │
│   └── run_generator.sh                   # 실행 예제 스크립트
│
├── mcp_editor/                             # 웹 에디터 & 도구 정의
│   ├── mcp_outlook/
│   │   ├── tool_definition_templates.py   # 🎯 도구 정의 (입력)
│   │   ├── tool_internal_args.json        # Internal Args 설정
│   │   └── backups/                       # 백업 디렉토리
│   ├── mcp_file_handler/
│   │   └── (동일 구조)
│   └── editor_config.json                 # 에디터 설정 (자동 생성 가능)
│
├── mcp_service_registry/                  # 서비스 메타데이터
│   ├── outlook_registry.json
│   ├── file_handler_registry.json
│   └── generate_editor_config.py          # editor_config.json 생성기
│
└── mcp_outlook/mcp_server/                # 🎉 생성된 서버 코드
    ├── server.py                          # Jinja로 자동 생성된 완전한 서버
    ├── tool_definitions.py
    └── mcp_decorators.py
```

---

## Tool Definition 작성

### 기본 구조 (tool_definition_templates.py)

```python
MCP_TOOLS = [
    {
        "name": "query_emails",
        "description": "이메일 검색 도구",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_email": {"type": "string", "description": "사용자 이메일"},
                "filter": {
                    "type": "object",
                    "baseModel": "FilterParams",  # 🔥 Pydantic 클래스 지정
                    "description": "검색 필터"
                }
            },
            "required": ["user_email"]
        },
        "mcp_service": {  # 🔥 서비스 메타데이터
            "name": "query_with_filter",
            "class": "GraphMailQuery",
            "module": "graph_mail_query",
            "parameters": [
                {"name": "user_email", "type": "str", "is_required": True},
                {"name": "filter", "type": "FilterParams", "is_required": True}
            ]
        }
    }
]
```

### 파라미터 타입

| Type | 설명 | Jinja 템플릿 처리 |
|------|------|------------------|
| `string` | 문자열 | 직접 전달 |
| `integer` | 정수 | 직접 전달 |
| `boolean` | 불리언 | 직접 전달 |
| `array` | 배열 | 직접 전달 |
| `object` + `baseModel` | Pydantic 모델 | 🔥 **자동으로 클래스 인스턴스로 변환** |

---

## Internal Args 설정

Internal Args는 MCP 클라이언트에 노출되지 않는 서버 내부 파라미터입니다.

### tool_internal_args.json 구조

```json
{
  "query_emails": {
    "select": {
      "type": "SelectParams",  // Pydantic 클래스명
      "description": "선택할 필드",
      "value": {
        "fields": ["id", "subject", "from"]
      }
    }
  }
}
```

### Jinja 템플릿에서의 처리

```jinja2
{%- if tool.internal_args %}
    # Internal Args (자동 주입)
    {%- for arg_name, arg_info in tool.internal_args.items() %}
    {{ arg_name }}_params = {{ arg_info.type }}(**{{ arg_info.value | pprint }})
    {%- endfor %}
{%- endif %}
```

---

## 템플릿 변수

Jinja 템플릿에서 사용 가능한 변수들:

### 전역 변수

| 변수 | 설명 |
|------|------|
| `tools` | 모든 도구 정의 목록 |
| `services` | 서비스 클래스 매핑 |
| `param_types` | Import할 Pydantic 타입들 |
| `internal_args` | Internal Args 전체 |

### 도구별 변수 (`tool`)

| 변수 | 설명 |
|------|------|
| `tool.name` | 도구 이름 |
| `tool.mcp_service` | 서비스 메서드 이름 |
| `tool.object_params` | 객체 파라미터 정보 |
| `tool.internal_args` | 해당 도구의 Internal Args |

---

## 서버 생성 프로세스

### 1. 기본 사용법 (Outlook 서버)

```bash
python jinja/generate_server.py \
  --tools mcp_editor/mcp_outlook/tool_definition_templates.py \
  --server outlook \
  --output mcp_outlook/mcp_server/server.py
```

### 2. File Handler 서버

```bash
python jinja/generate_server.py \
  --tools mcp_editor/mcp_file_handler/tool_definition_templates.py \
  --server file_handler \
  --output mcp_file_handler/mcp_server/server.py
```

### 3. 새 서버 스캐폴드 생성

```bash
# 1단계: 스캐폴드 생성
python jinja/scaffold_generator.py --name my_service

# 2단계: tool definitions 작성
vi mcp_editor/mcp_my_service/tool_definition_templates.py

# 3단계: 서버 코드 생성
python jinja/generate_server.py \
  --tools mcp_editor/mcp_my_service/tool_definition_templates.py \
  --template jinja/mcp_server_scaffold_template.jinja2 \
  --output mcp_my_service/mcp_server/server.py
```

### 4. editor_config.json 자동 생성

```bash
# @mcp_service 데코레이터와 mcp_* 디렉토리를 스캔해서 자동 생성
python jinja/generate_editor_config.py
```

---

## 템플릿 작성 패턴

### 1. Object 파라미터 변환 (핵심!)

```jinja2
{# Jinja 템플릿이 자동으로 처리 #}
{% for param_name, param_info in tool.object_params.items() %}
    {% if param_info.is_optional %}
        {{ param_name }}_raw = args.get("{{ param_name }}")
        {{ param_name }}_params = {{ param_info.class_name }}(**{{ param_name }}_raw) if {{ param_name }}_raw else None
    {% else %}
        {{ param_name }}_params = {{ param_info.class_name }}(**args["{{ param_name }}"])
    {% endif %}
{% endfor %}
```

생성된 코드:
```python
filter_params = FilterParams(**args["filter"])  # 🔥 자동 변환!
```

### 2. 서비스 호출

```jinja2
result = await service_instance.{{ tool.mcp_service }}(
    user_email=user_email,
    {%- for param_name in tool.call_params %}
    {{ param_name }}={{ param_name }}_params,
    {%- endfor %}
)
```

---

## 트러블슈팅

### 문제: ImportError

```bash
ImportError: cannot import name 'FilterParams'
```

**해결**: types 파일 경로를 editor_config.json에 추가
```json
"types_files": ["../mcp_outlook/outlook_types.py"]
```

### 문제: 템플릿 렌더링 오류

**해결**: `--server` 옵션으로 올바른 템플릿 선택
```bash
python jinja/generate_server.py --server outlook ...
```

### 문제: Internal Args가 반영되지 않음

**해결**: tool_internal_args.json 파일 확인 및 동기화

---

## 베스트 프랙티스

### 1. Tool Definition 작성 시

- ✅ Object 파라미터에는 항상 `baseModel` 지정
- ✅ `mcp_service` 메타데이터 정확히 입력
- ✅ 명확한 설명(description) 작성

### 2. 템플릿 수정 시

- ✅ 생성된 코드가 Python 문법에 맞는지 확인
- ✅ Import 문이 올바르게 생성되는지 확인
- ✅ 들여쓰기 주의 (Jinja의 `-` 옵션 활용)

### 3. 서버 생성 시

- ✅ 항상 백업 생성 (`--backup` 옵션)
- ✅ 생성된 코드 검토 후 테스트
- ✅ Internal Args 동기화 확인

---

## 관련 파일 참조

### 핵심 생성기

- `jinja/generate_server.py` – 🔥 **통합 서버 생성기 (이거 하나로 모든 서버 생성)**
- `jinja/generate_outlook_server.py` – Outlook 서버 전문 생성기 (1179줄의 정수)
- `jinja/scaffold_generator.py` – 새 서버 스캐폴드 생성

### 템플릿 파일

- `jinja/outlook_server_template.jinja2` – Outlook 서버 템플릿
- `jinja/file_handler_server_template.jinja2` – 파일 핸들러 템플릿
- `jinja/mcp_server_scaffold_template.jinja2` – 기본 서버 템플릿

### 유틸리티

- `jinja/generate_editor_config.py` – editor_config.json 자동 생성
- `jinja/generate_server_mappings.py` – 서버 매핑 생성
- `jinja/run_generator.sh` – 실행 예제 모음

---

## 결론

**Jinja 템플릿 시스템은 MCP 서버 개발의 핵심입니다.**

수동으로 서버 코드를 작성하는 것은:
- ❌ 시간 낭비
- ❌ 실수 유발
- ❌ 일관성 부족
- ❌ 유지보수 어려움

Jinja 템플릿을 사용하면:
- ✅ **몇 초 만에 완전한 서버 코드 생성**
- ✅ **타입 안전성 보장**
- ✅ **일관된 코드 구조**
- ✅ **쉬운 유지보수**

**"Jinja 없이 MCP 서버 개발? 그건 삽으로 땅 파는 것과 같다!"**