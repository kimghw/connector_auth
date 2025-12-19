# MCP Server 용어 정의 (Terminology)

## 핵심 구조 (Core Structure)

### 표준 데이터 구조
```python
{
    'tool_name': 'Outlook',           # MCP Tool 이름 (사용자가 호출)
    'server_name': 'outlook',         # MCP 서버 이름 (서버 식별자)

    'handler': {                      # Python 핸들러 정보 (그룹화)
        'method': 'query_filter',     # Python 메서드명
        'class': 'GraphMailQuery',    # 클래스명
        'instance': 'graph_mail_query',   # 인스턴스 변수명
        'module': 'graph_mail_query'      # import 경로
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

### Handler 레벨 (Python 구현)
- **handler**: Python 구현 정보를 담은 딕셔너리

- **handler.method**: 실제 Python 클래스의 메서드 이름
  - 예: "query_filter", "query_search", "query_url"
  - 이전 명칭: service_method, service_name

- **handler.class**: Python 클래스 이름
  - 예: "GraphMailQuery", "FileManager", "MetadataManager"
  - 이전 명칭: service_class

- **handler.instance**: 클래스 인스턴스를 저장할 변수명
  - 예: "graph_mail_query", "file_manager", "metadata_manager"
  - 이전 명칭: service_object

- **handler.module**: Python import 경로
  - 예: "graph_mail_query", "file_manager", "metadata.manager"
  - 신규 추가 필드

### 파라미터 레벨
- **params**: 단순 타입 파라미터 정보
  - 예: string, integer, boolean 타입의 파라미터

- **object_params**: 객체 타입 파라미터 정보
  - 예: FilterParams, ExcludeParams, SelectParams 등의 커스텀 클래스

- **call_params**: 함수 호출 시 사용할 파라미터 매핑
  - 예: `filter` → `filter_params` 매핑

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
    tool_name="Handle_query_filter",    # 원본 이름
    service_name="query_filter",        # → handler.method
    server_name="outlook",               # → server_name
    ...
)
```

### 2. Tool 정의 → Analyzed 구조
```python
# Tool Definition (사용자 편집)
{
    'name': 'Outlook',  # → tool_name
    'mcp_service': {
        'name': 'query_filter'  # → handler.method
    }
}
```

### 3. Analyzed 구조 → 생성된 코드
```python
# 생성된 Python 코드
from {{ handler.module }} import {{ handler.class }}
{{ handler.instance }} = {{ handler.class }}()

async def handle_{{ tool_name }}(args):
    return await {{ handler.instance }}.{{ handler.method }}(...)
```

## 네이밍 규칙

### 1. tool_name
- PascalCase 또는 snake_case 사용
- 사용자 친화적인 이름
- 예: "Outlook", "keyword_search"

### 2. server_name
- lowercase 사용
- 언더스코어(_) 허용
- 예: "outlook", "file_handler"

### 3. handler.method
- snake_case 사용
- 동사로 시작 권장
- 예: "query_filter", "send_mail", "get_attachments"

### 4. handler.class
- PascalCase 사용
- 명사형
- 예: "GraphMailQuery", "FileManager"

### 5. handler.instance
- snake_case 사용
- 클래스명의 snake_case 버전
- 예: "graph_mail_query", "file_manager"

### 6. handler.module
- snake_case 사용
- Python 모듈 경로 규칙 따름
- 예: "graph_mail_query", "metadata.manager"

## 마이그레이션 가이드

### 이전 구조 → 새 구조
| 이전 | 새 구조 | 설명 |
|------|--------|------|
| `name` | `tool_name` | Tool 이름 |
| `service_method` | `handler.method` | 메서드명 |
| `service_class` | `handler.class` | 클래스명 |
| `service_object` | `handler.instance` | 인스턴스명 |
| - | `handler.module` | 모듈 경로 (신규) |
| - | `server_name` | 서버명 (명시화) |

## 예시

### Outlook Tool
```python
{
    'tool_name': 'Outlook',
    'server_name': 'outlook',
    'handler': {
        'method': 'query_filter',
        'class': 'GraphMailQuery',
        'instance': 'graph_mail_query',
        'module': 'graph_mail_query'
    }
}
```

### File Handler Tool
```python
{
    'tool_name': 'file_upload',
    'server_name': 'file_handler',
    'handler': {
        'method': 'upload_file',
        'class': 'FileManager',
        'instance': 'file_manager',
        'module': 'file_manager'
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
*Last Updated: 2024-12-19*
*Version: 2.0*