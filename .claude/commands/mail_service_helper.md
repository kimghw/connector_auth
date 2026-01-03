---
description: Custom command (project)
---

# Mail Service Helper - GraphMailClient 작업 가이드

`outlook_service.py` 작업 시 GraphMailClient를 감싸는 Facade 레이어 구현 가이드

---

## 핵심 개념

### Facade 패턴
- **목적**: 복잡한 GraphMailClient를 단순한 인터페이스로 제공
- **역할**: 인자만 제어하고 실제 로직은 GraphMailClient에 위임
- **장점**: MCP 도구에서 쉽게 호출 가능한 단순한 메서드 제공

### 데이터 흐름
```
MCP Tool Call → outlook_service.py (Facade) → GraphMailClient → MS Graph API
```

---

## 주요 타입 정의

### FilterParams (outlook_types.py)
```python
# 필터 조건을 위한 타입
FilterParams = {
    'from_address': str,           # 발신자 이메일
    'has_attachments': bool,        # 첨부파일 유무
    'importance': str,              # 중요도 (high/normal/low)
    'received_date_from': str,      # 시작 날짜 (ISO 8601)
    'received_date_to': str,        # 종료 날짜 (ISO 8601)
    'subject_contains': str,        # 제목 포함 문자열
    'body_contains': str,           # 본문 포함 문자열
}
```

### ExcludeParams (outlook_types.py)
```python
# 제외 조건을 위한 타입
ExcludeParams = {
    'exclude_from': List[str],      # 제외할 발신자 목록
    'exclude_domains': List[str],   # 제외할 도메인 목록
    'exclude_subjects': List[str],  # 제외할 제목 패턴
}
```

### SelectParams (outlook_types.py)
```python
# 필드 선택을 위한 타입
SelectParams = {
    'fields': List[str],           # 선택할 필드 목록
    'expand': List[str],           # 확장할 관계 필드
}
```

---

## Facade 구현 패턴

### 기본 구조
```python
class MailService:
    def __init__(self):
        self._client: Optional[GraphMailClient] = None
        self._initialized = False

    async def _ensure_initialized(self, user_email: str):
        """클라이언트 초기화 보장"""
        if not self._initialized:
            self._client = GraphMailClient(user_email=user_email)
            await self._client.initialize()
            self._initialized = True
```

### 메서드 변환 예시

#### 단순 위임
```python
async def search_emails(self, user_email: str, keyword: str, max_results: int = 50):
    """단순 검색 - 인자만 전달"""
    await self._ensure_initialized(user_email)
    return await self._client.quick_search(
        keyword=keyword,
        max_results=max_results
    )
```

#### 파라미터 변환
```python
async def get_emails_by_date(self,
    user_email: str,
    start_date: str,
    end_date: Optional[str] = None,
    max_results: int = 50
):
    """날짜 기반 조회 - 파라미터를 FilterParams로 변환"""
    await self._ensure_initialized(user_email)

    filter_params = {
        'received_date_from': start_date
    }
    if end_date:
        filter_params['received_date_to'] = end_date

    return await self._client.build_and_fetch(
        query_method=QueryMethod.FILTER,
        filter_params=filter_params,
        top=max_results
    )
```

---

## @mcp_service 데코레이터 사용

```python
from mcp_editor.mcp_service_registry.mcp_service_decorator import mcp_service

@mcp_service(
    tool_name="handle_search_emails",
    server_name="outlook",
    service_name="search_emails",
    category="outlook_mail",
    tags=["search", "mail"],
    description="이메일 검색"
)
async def search_emails(self, user_email: str, keyword: str, max_results: int = 50):
    # 구현...
```

---

## 관련 파일 경로

### 타입 정의
- `mcp_outlook/outlook_types.py` - FilterParams, ExcludeParams, SelectParams
- `mcp_outlook/mail_processing_options.py` - ProcessingMode, AttachmentOption

### 구현 파일
- `mcp_outlook/graph_mail_client.py` - GraphMailClient 본체
- `mcp_outlook/outlook_service.py` - Facade 레이어 (작성 대상)

### 헬퍼 모듈
- `mcp_outlook/graph_mail_filter.py` - 필터 쿼리 생성
- `mcp_outlook/graph_mail_search.py` - 검색 쿼리 생성
- `mcp_outlook/graph_filter_helpers.py` - 필터 헬퍼 함수

### MCP 설정
- `mcp_editor/mcp_outlook/tool_definition_templates.py` - 도구 정의 템플릿
- `mcp_editor/mcp_outlook/tool_internal_args.json` - Internal 파라미터
- `mcp_editor/mcp_service_registry/registry_outlook.json` - 서비스 레지스트리

---

## 체크리스트

작업 시 확인사항:
- [ ] @mcp_service 데코레이터 추가
- [ ] 파라미터에 타입 힌트 추가
- [ ] Optional 파라미터에 기본값 설정
- [ ] user_email 파라미터 필수 포함
- [ ] GraphMailClient 초기화 확인
- [ ] 에러 처리 및 반환값 검증

---

## 디버깅 팁

```python
# 레지스트리 확인
python mcp_editor/mcp_service_registry/mcp_service_scanner.py

# 웹에디터에서 도구 정의 확인
python mcp_editor/tool_editor_web.py
# http://localhost:8080 접속

# 서버 테스트
python mcp_outlook/mcp_server/server.py
```