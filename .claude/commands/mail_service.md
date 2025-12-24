---
description: GraphMailClient 함수 및 인자 정리 (project)
---

# GraphMailClient 함수 및 인자 정리

`mail_service.py` 생성 시 참고할 `graph_mail_client.py` 컨텍스트

---

## 설계 원칙

**Facade 디자인 패턴 적용**
- `mail_service.py`는 `GraphMailClient`의 Facade 역할
- **인자만 제어**하여 내부 복잡성을 숨김
- 실제 로직은 `GraphMailClient`에 위임
- MCP 도구에서 단순한 인터페이스로 호출 가능

```
┌─────────────────────────────────────────────┐
│                MCP Tools                    │
│  (search_emails, get_emails_by_filter)      │
└─────────────────┬───────────────────────────┘
                  │ 단순 인자 전달
                  ▼
┌─────────────────────────────────────────────┐
│              mail_service.py                │
│          (Facade - 인자만 제어)             │
└─────────────────┬───────────────────────────┘
                  │ 위임
                  ▼
┌─────────────────────────────────────────────┐
│           GraphMailClient                   │
│      (실제 비즈니스 로직 처리)              │
└─────────────────────────────────────────────┘
```

---

## Enum 타입

### QueryMethod
```python
class QueryMethod(Enum):
    FILTER = "filter"      # 필터 기반 쿼리
    SEARCH = "search"      # 검색어 기반 쿼리
    URL = "url"            # 직접 URL 제공
```

### ProcessingMode
```python
class ProcessingMode(Enum):
    FETCH_ONLY = "fetch_only"              # 메일만 가져오기
    FETCH_AND_DOWNLOAD = "fetch_download"  # 메일 + 첨부파일 다운로드
    FETCH_AND_CONVERT = "fetch_convert"    # 메일 + 첨부파일 변환
    FULL_PROCESS = "full_process"          # 전체 처리
```

---

## GraphMailClient 주요 메서드

### `build_and_fetch`
```python
async def build_and_fetch(self,
    query_method: QueryMethod = QueryMethod.FILTER,
    # Filter 방식 파라미터
    filter_params: Optional[FilterParams] = None,
    exclude_params: Optional[ExcludeParams] = None,
    select_params: Optional[SelectParams] = None,
    client_filter: Optional[ExcludeParams] = None,
    # Search 방식 파라미터
    search_term: Optional[str] = None,
    # URL 방식 파라미터
    url: Optional[str] = None,
    # 공통 파라미터
    top: int = 50,
    order_by: Optional[str] = None
) -> Dict[str, Any]
```

### `fetch_and_process`
```python
async def fetch_and_process(self,
    # 쿼리 파라미터 (build_and_fetch와 동일)
    # ...
    # 처리 파라미터
    processing_mode: ProcessingMode = ProcessingMode.FETCH_ONLY,
    mail_storage: MailStorageOption = MailStorageOption.MEMORY,
    attachment_handling: AttachmentOption = AttachmentOption.SKIP,
    output_format: OutputFormat = OutputFormat.COMBINED,
    save_directory: Optional[str] = None,
    return_on_error: bool = True
) -> Dict[str, Any]
```

### `quick_search`
```python
async def quick_search(self,
    keyword: str,
    max_results: int = 50,
    process_attachments: bool = False
) -> Dict[str, Any]
```

---

## 외부 의존성 타입

### FilterParams 예시
```python
filter_params: FilterParams = {
    'from_address': 'sender@example.com',
    'has_attachments': True,
    'received_date_from': '2024-01-01T00:00:00Z'
}
```

### ExcludeParams, SelectParams
- 제외 조건 및 필드 선택을 위한 타입
- `outlook_types.py`에 정의

---

## Facade 패턴 적용 예시

```python
class MailService:
    """GraphMailClient의 Facade - 인자만 제어"""

    async def search_emails(self, keyword: str, max_results: int = 50):
        """검색 - 인자만 전달"""
        return await self._client.quick_search(
            keyword=keyword,
            max_results=max_results
        )

    async def get_emails_by_filter(self,
        from_address: Optional[str] = None,
        has_attachments: Optional[bool] = None,
        max_results: int = 50
    ):
        """필터 조회 - 인자를 FilterParams로 변환 후 전달"""
        filter_params = {}
        if from_address:
            filter_params['from_address'] = from_address
        if has_attachments is not None:
            filter_params['has_attachments'] = has_attachments

        return await self._client.build_and_fetch(
            query_method=QueryMethod.FILTER,
            filter_params=filter_params,
            top=max_results
        )
```

---

## 관련 파일 경로

### 핵심 구현
- `mcp_outlook/graph_mail_client.py` - GraphMailClient 본체
- `mcp_outlook/mail_service.py` - Facade 레이어 (MCP 서비스)
- `mcp_outlook/outlook_types.py` - 타입 정의

### 헬퍼 모듈
- `mcp_outlook/graph_mail_filter.py` - 필터 로직
- `mcp_outlook/graph_mail_search.py` - 검색 로직
- `mcp_outlook/attachment_handler.py` - 첨부파일 처리
- `mcp_outlook/mail_processing_options.py` - 처리 옵션 Enum

### MCP 서버
- `mcp_outlook/mcp_server/server.py` - FastAPI 서버
- `mcp_outlook/mcp_server/tool_definitions.py` - MCP 도구 정의

### 설정 및 레지스트리
- `mcp_editor/mcp_outlook/tool_definition_templates.py` - 도구 템플릿
- `mcp_editor/mcp_outlook/tool_internal_args.json` - Internal 파라미터
- `mcp_editor/mcp_service_registry/registry_outlook.json` - 서비스 레지스트리

---

## 사용 예시

```python
# 클라이언트 생성 및 초기화
client = GraphMailClient(user_email="user@example.com")
await client.initialize()

# 빠른 검색
results = await client.quick_search("invoice", max_results=10)

# 필터 기반 조회 + 처리
results = await client.fetch_and_process(
    query_method=QueryMethod.FILTER,
    filter_params={'from_address': 'sender@example.com'},
    top=20,
    processing_mode=ProcessingMode.FETCH_AND_DOWNLOAD
)

# 리소스 정리
await client.close()
```