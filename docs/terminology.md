# MCP Server 용어 정의 (Terminology)

## 핵심 구조 (Core Structure)

### 표준 데이터 구조
```python
{
    'tool_name': 'Outlook',           # MCP Tool 이름 (사용자가 호출)
    'server_name': 'outlook',         # MCP 서버 이름 (서버 식별자)
    'profile_key': 'mcp_outlook',     # editor_config.json 프로필 키 (mcp_{server_name} 규칙)

    'implementation': {                      # Python 구현 정보 (registry_{server}.json에서는 implementation.* 키로 저장)
        'method': 'query_filter',     # Python 메서드명
        'class': 'GraphMailQuery',    # 클래스명
        'instance': 'graph_mail_query',   # 인스턴스 변수명
        'module_paht': 'graph_mail_query'      # import 경로
    },

    'params': {},                     # 파라미터 정보
    'metadata': {}                    # 메타데이터
}
```

## 용어 정의

### MCP 레벨
- **tool_name**: MCP Tool의 이름. 사용자/클라이언트가 호출할 때 사용하는 이름
  - 예: "Outlook", "keyword_search", "mail_list"

- **server_name**: MCP 서버의 이름. 서버를 식별하는 이름
  - 예: "outlook", "file_handler", "metadata"
  - 데코레이터(@mcp_service)의 `server_name` 값과 동일

- **profile_key**: editor_config.json에서 사용하는 프로필 키
  - 규칙: `mcp_{server_name}`
  - 예: "mcp_outlook", "mcp_file_handler"

### implementation 레벨 (Python 구현)
- **implementation**: Python 구현 정보를 담은 딕셔너리
  - registry_{server}.json에서는 동일 구조를 `implementation` 키로 저장하며 필드명은 다음과 같이 매핑됨
    - handler.class → implementation.class_name
    - handler.module → implementation.module_path (일반적으로 `server_name.` prefix 포함)
    - handler.instance → implementation.instance
    - handler.method → implementation.method
    - 추가 필드: implementation.is_async, implementation.file, implementation.line

- **implementation.method**: 실제 Python 클래스의 메서드 이름
  - 예: "query_filter", "query_search", "query_url"
  - 이전 명칭: service_method, service_name

- **implementation.class**: Python 클래스 이름
  - 예: "GraphMailQuery", "FileManager", "MetadataManager"
  - 이전 명칭: service_class

- **implementation.instance**: 클래스 인스턴스를 저장할 변수명
  - 예: "graph_mail_query", "file_manager", "metadata_manager"
  - 이전 명칭: service_object

- **implementation.module**: Python import 경로
  - 예: "graph_mail_query", "file_manager", "metadata.manager"
  - 신규 추가 필드

### 파라미터 레벨
- **Schema Property Name**: inputSchema.properties에 정의되는 이름
  - LLM이 인식하고 사용하는 파라미터 이름
  - MCP 도구 정의에서 args 딕셔너리의 키
  - tool_definitions.py의 inputSchema.properties에 들어가는 이름
  - 예시:
    ```python
    # tool_definitions.py
    {
        "name": "mail_fetch_filter",
        "inputSchema": {
            "properties": {
                "filter_params": {  # ← 이것이 Schema Property Name
                    "type": "object",
                    "baseModel": "FilterParams",
                    "targetParam": "filter"  # ← 실제 서비스 메서드 파라미터
                }
            }
        }
    }
    ```

- **params**: 단순 타입 파라미터 정보
  - 예: string, integer, boolean 타입의 파라미터

- **object_params**: 객체 타입 파라미터 정보
  - 예: FilterParams, ExcludeParams, SelectParams 등의 커스텀 클래스

- **call_params**: 함수 호출 시 사용할 파라미터 매핑
  - 예: `filter` → `filter_params` 매핑

- **targetParam**: Schema Property Name과 실제 서비스 메서드 파라미터를 매핑
  - Schema Property Name이 서비스 메서드 파라미터명과 다를 때 사용
  - 예: `"filter_params"` (Schema) → `"filter"` (메서드 파라미터)

### 메타데이터 레벨
- **metadata**: Tool의 부가 정보
  - category: Tool 카테고리 (예: "outlook_mail")
  - tags: Tool 태그 리스트 (예: ["query", "internal"])
  - priority: 우선순위
  - description: Tool 설명

## 데이터 흐름

### 1. 데코레이터 → Tool 정의
```python
@mcp_service(
    tool_name="handle_query_filter",    # 원본 이름
    service_name="query_filter",        # → implementation.method
    server_name="outlook",               # → server_name
    ...
)
```

### 2. Tool 정의 → Analyzed 구조
```python
# Tool Definition (사용자 편집)
{
    'name': 'outlook',  # → tool_name
    'mcp_service': {
        'name': 'query_filter'  # → handler.method
    }
}
```

### 3. Analyzed 구조 → 생성된 코드
```python
# 생성된 Python 코드
from {{ implementation.module }} import {{ implementation.class }}
{{ implementation.instance }} = {{ implementation.class }}()

async def handle_{{ tool_name }}(args):
    return await {{ implementation.instance }}.{{ implementation.method }}(...)
```

## 네이밍 규칙

### 1. tool_name
- PascalCase 또는 snake_case 사용
- 사용자 친화적인 이름
- 예: "outlook", "keyword_search"

### 2. server_name
- lowercase 사용
- 언더스코어(_) 허용
- 예: "outlook", "file_handler"

### 3. profile_key (editor_config.json)
- `mcp_{server_name}` 형식 고정
- 예: "mcp_outlook", "mcp_file_handler"

### 4. implementation.method
- snake_case 사용
- 동사로 시작 권장
- 예: "query_filter", "send_mail", "get_attachments"

### 5. implementation.class
- PascalCase 사용
- 명사형
- 예: "GraphMailQuery", "FileManager"

### 6. implementation.instance
- snake_case 사용
- 클래스명의 snake_case 버전
- 예: "graph_mail_query", "file_manager"

### 7. implementation.module
- snake_case 사용
- Python 모듈 경로 규칙 따름
- 예: "graph_mail_query", "metadata.manager"

## 파일/디렉토리 네이밍 규칙

| 구분 | 규칙 | 예시 |
|------|------|------|
| 서버 키 | `server_name` (decorator 값) | `outlook`, `file_handler` |
| 모듈 디렉토리 | `mcp_{server_name}/` | `mcp_outlook/`, `mcp_file_handler/` |
| 에디터 프로필 디렉토리 | `mcp_editor/mcp_{server_name}/` | `mcp_editor/mcp_outlook/` |
| 템플릿 정의 | `mcp_editor/mcp_{server_name}/tool_definition_templates.py` | `mcp_editor/mcp_outlook/tool_definition_templates.py` |
| Internal Args | `mcp_editor/mcp_{server_name}/tool_internal_args.json` | `mcp_editor/mcp_outlook/tool_internal_args.json` |
| 서버 정의 | `mcp_{server_name}/mcp_server/tool_definitions.py` | `mcp_outlook/mcp_server/tool_definitions.py` |
| 레지스트리 | `mcp_editor/mcp_service_registry/registry_{server_name}.json` | `registry_outlook.json` |
| 타입 속성 | `mcp_editor/mcp_service_registry/types_property_{server_name}.json` | `types_property_outlook.json` |

## 마이그레이션 가이드

### 이전 구조 → 새 구조
| 이전 | 새 구조 | 설명 |
|------|--------|------|
| `name` | `tool_name` | Tool 이름 |
| `service_method` | `implementation.method` | 메서드명 |
| `service_class` | `implementation.class` | 클래스명 |
| `service_object` | `implementation.instance` | 인스턴스명 |
| - | `implementation.module` | 모듈 경로 (신규) |
| - | `server_name` | 서버명 (명시화) |
| - | `profile_key` | editor_config.json 프로필 키 (`mcp_{server_name}`) |

## 예시

### Outlook Tool
```python
{
    'tool_name': 'Outlook',
    'server_name': 'outlook',
    'implementation': {
        'method': 'query_filter',
        'class': 'GraphMailQuery',
        'instance': 'graph_mail_query',
        'module_path': 'graph_mail_query'
    }
}
```

### File Handler Tool
```python
{
    'tool_name': 'file_upload',
    'server_name': 'file_handler',
    'implementation': {
        'method': 'upload_file',
        'class': 'FileManager',
        'instance': 'file_manager',
        'module_path': 'file_manager'
    }
}
```

## 장점

1. **명확성**: 각 필드의 용도가 명확함
2. **그룹화**: 관련 정보가 handler 딕셔너리로 그룹화
3. **일관성**: 네이밍이 일관되고 예측 가능
4. **확장성**: 새로운 필드 추가 시 적절한 그룹에 배치
5. **호환성**: 레거시 필드 유지로 점진적 마이그레이션 가능

---
*Last Updated: 2025-12-21*
*Version: 2.2*
