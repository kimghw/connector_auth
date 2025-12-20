# MCPMetaRegistry 데이터 소스 분석

## 데이터 출처 구분

### 1. **metadata** - @mcp_service 데코레이터에서 수집
```python
@mcp_service(
    tool_name="Handle_query_filter",
    server_name="outlook",
    service_name="query_filter",
    category="outlook_mail",
    tags=["query", "url-builder", "internal"],
    priority=5,
    description="Build Microsoft Graph API query URL for email operations"
)
def query_filter(...):
    pass
```

**데코레이터에서 오는 정보**:
- `tool_name`: MCP 툴 이름
- `server_name`: 서버 식별자
- `service_name`: 서비스 이름
- `category`: 카테고리 분류
- `tags`: 태그 리스트
- `priority`: 우선순위
- `description`: 설명

### 2. **signature & parameters** - AST 분석에서 수집
```python
def query_filter(
    user_email: str,
    filter: FilterParams,
    exclude: Optional[ExcludeParams] = None,
    select: Optional[SelectParams] = None,
    client_filter: Optional[ExcludeParams] = None,
    top: int = 450,
    orderby: Optional[str] = None
):
    pass
```

**AST 분석으로 오는 정보**:
- `signature`: 함수 시그니처 전체 문자열
- `parameters`: 각 파라미터별 상세 정보
  - `name`: 파라미터 이름
  - `type`: 타입 힌트
  - `default`: 기본값
  - `has_default`: 기본값 유무
  - `is_required`: 필수 여부

## 데이터 수집 프로세스

### Step 1: 데코레이터 수집 (Runtime)
```python
# mcp_service_decorator.py
@mcp_service(...)
def function():
    # 데코레이터가 실행되면서 metadata 저장
    pass
```

### Step 2: AST 스캔 (Static Analysis)
```python
# ast_scanner.py
import ast

class FunctionAnalyzer(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        # 함수 시그니처 분석
        # 파라미터 타입 추출
        # 기본값 파싱
```

### Step 3: 통합 (MCPMetaRegistry)
```python
# registry.py
class MCPMetaRegistry:
    def combine_metadata(self):
        # 데코레이터 metadata + AST signature/parameters
        combined = {
            "metadata": decorator_data,      # from @mcp_service
            "signature": ast_data.signature, # from AST
            "parameters": ast_data.params    # from AST
        }
```

## 왜 두 가지 방법을 사용하는가?

### 데코레이터 (Runtime)
- **장점**:
  - 개발자가 명시한 메타데이터 정확히 수집
  - 비즈니스 로직 정보 (category, tags, priority)
- **단점**:
  - 코드 실행 필요 (import 해야 함)
  - 함수 시그니처 정보 부족

### AST (Static Analysis)
- **장점**:
  - 코드 실행 없이 분석 가능
  - 정확한 함수 시그니처와 타입 정보
- **단점**:
  - 런타임 메타데이터 접근 불가
  - 동적 생성 코드 분석 어려움

## 실제 사용 예시

outlook_registry.json에서:
```json
{
  "outlook.query_filter": {
    // 데코레이터에서 온 데이터
    "metadata": {
      "tool_name": "Handle_query_filter",
      "server_name": "outlook",
      "category": "outlook_mail",
      "tags": ["query", "url-builder", "internal"]
    },

    // AST에서 온 데이터
    "signature": "user_email: str, filter: FilterParams, ...",
    "parameters": [
      {
        "name": "user_email",
        "type": "str",
        "is_required": true
      }
    ]
  }
}
```

## 결론

**두 소스의 상호보완적 관계**:
- 데코레이터: "이 함수가 무엇인지" (What)
- AST: "이 함수를 어떻게 호출하는지" (How)

이 두 가지를 결합하여 완전한 메타데이터를 구성합니다.