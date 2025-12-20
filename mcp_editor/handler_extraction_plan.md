# Handler 정보 추출 계획

## 문제 상황
`outlook_registry.json`에서 `query_filter` 같은 메서드들의 handler 정보가 누락됨:
- handler.class (GraphMailQuery)
- handler.instance (graph_mail_query)
- handler.module (graph_mail_query)
- handler.method (query_filter)

## 현재 구조 분석

### query_filter는 클래스 메서드
```python
class GraphMailQuery:
    @mcp_service(tool_name="Handle_query_filter", ...)
    async def query_filter(self, user_email: str, ...):
        # self가 있으므로 인스턴스 메서드
        pass
```

## AST로 Handler 정보 추출하기

### 1단계: 클래스와 메서드 관계 파악
```python
import ast

class HandlerExtractor(ast.NodeVisitor):
    def __init__(self):
        self.current_class = None
        self.handlers = {}

    def visit_ClassDef(self, node):
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        if self.current_class and self._has_mcp_decorator(node):
            # 클래스 메서드인 경우
            self.handlers[node.name] = {
                'class': self.current_class,
                'instance': self._to_snake_case(self.current_class),
                'module': self._get_module_name(),
                'method': node.name
            }
```

### 2단계: 인스턴스명 규칙
- `GraphMailQuery` → `graph_mail_query`
- `FileManager` → `file_manager`
- CamelCase를 snake_case로 변환

### 3단계: 모듈명 결정
- 파일명 기반: `graph_mail_query.py` → `graph_mail_query`
- 클래스가 있는 파일의 stem 사용

## 구현 위치

### Option 1: mcp_service_scanner.py 개선
기존 AST 스캔 로직에 handler 추출 추가

### Option 2: MCPMetaRegistry/collectors에 추가
새로운 HandlerCollector 클래스 생성

### Option 3: meta_registry.py의 collect_from_scanner 개선
스캐너 결과에 handler 정보 병합

## 예상 출력

```json
{
  "outlook.query_filter": {
    "function_name": "query_filter",
    "handler": {
      "class": "GraphMailQuery",
      "instance": "graph_mail_query",
      "module": "graph_mail_query",
      "method": "query_filter"
    },
    "metadata": { ... },
    "signature": "...",
    "parameters": [ ... ]
  }
}
```

## 구현 순서
1. AST로 클래스-메서드 관계 파악
2. 인스턴스명 생성 규칙 적용 (snake_case 변환)
3. 모듈명 추출 (파일명 기반)
4. registry.json에 handler 섹션 추가

## 테스트 케이스
- `GraphMailQuery.query_filter` → handler.class="GraphMailQuery"
- `FileManager.get_file` → handler.class="FileManager"
- 클래스 없는 함수 → handler가 없어야 함