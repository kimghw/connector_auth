---
description: MCP Service Decorator 작성 가이드 (project)
---

# MCP Service Decorator 작성 가이드

비즈니스 로직 함수에 `@mcp_service` 데코레이터를 작성할 때 참조하는 가이드입니다.

---

## 기본 양식

```python
from mcp_editor.mcp_service_registry.mcp_service_decorator import mcp_service

@mcp_service(
    tool_name="handle_query_search",      # 필수: MCP Tool 이름
    server_name="outlook",                # 필수: 서버 식별자
    service_name="query_search",          # 필수: 메서드명
    category="outlook_mail",              # 권장: 카테고리
    tags=["query", "search"],             # 권장: 태그
    priority=5,                           # 선택: 우선순위 (1-10)
    description="메일 검색 기능"           # 필수: 기능 설명
)
async def query_search(self, user_email: str, search: str, top: int = 250):
    pass
```

---

## 필드 설명

| 필드 | 필수 | 규칙 | 예시 |
|------|------|------|------|
| tool_name | O | handle_ + 기능명 | `handle_query_filter` |
| server_name | O | mcp_{server_name}/ 디렉토리와 일치 | `outlook`, `file_handler` |
| service_name | O | 실제 함수명 | `query_search` |
| category | - | server_name_기능영역 | `outlook_mail` |
| tags | - | 소문자 리스트 | `["query", "mail"]` |
| priority | - | 1-10 (높을수록 중요) | `5` |
| description | O | 한 줄 설명 | `"메일 검색"` |

---

## 체크리스트

- [ ] tool_name이 고유한가?
- [ ] server_name이 디렉토리와 일치하는가?
- [ ] 파라미터에 타입 힌트가 있는가?
- [ ] Optional 파라미터에 기본값이 있는가?

---

## 파싱 결과

```json
{
  "name": "handle_query_search",
  "metadata": {
    "tool_name": "handle_query_search",
    "server_name": "outlook",
    "service_name": "query_search"
  },
  "parameters": [
    {"name": "user_email", "type": "str", "required": true},
    {"name": "search", "type": "str", "required": true},
    {"name": "top", "type": "int", "required": false, "default": 250}
  ],
  "is_async": true,
  "class": "GraphMailQuery",
  "instance": "graph_mail_query"
}
```

---

*관련: docs/terminology.md*
