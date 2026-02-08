# MCP OneNote Module

Microsoft Graph API를 사용한 OneNote 서비스 모듈입니다.
`mcp_outlook` 모듈과 동일한 구조로 리팩토링되었습니다.

## 구조

```
mcp_onenote/
├── __init__.py              # 모듈 초기화
├── onenote_types.py         # 타입 정의 (dataclass)
├── graph_onenote_client.py  # Graph API 클라이언트
├── onenote_service.py       # 서비스 레이어 (Facade 패턴)
├── onenote_db_service.py    # DB 관리 (최근 항목 추적)
├── mcp_server/              # MCP 서버
│   └── __init__.py
├── tests/                   # 테스트
│   ├── __init__.py
│   └── test_onenote_service.py
└── README.md
```

## 기능

### 노트북 관리
- `list_notebooks`: 노트북 목록 조회

### 섹션 관리
- `list_sections`: 섹션 목록 조회
- `create_section`: 새 섹션 생성
- `manage_sections`: 섹션 관리 (통합 인터페이스)

### 페이지 관리
- `list_pages`: 페이지 목록 조회
- `get_page_content`: 페이지 내용 조회
- `create_page`: 새 페이지 생성
- `edit_page`: 페이지 편집 (append, prepend, insert, replace)
- `delete_page`: 페이지 삭제
- `manage_page_content`: 페이지 내용 관리 (통합 인터페이스)

### DB 연동 (최근 항목 추적)
- `sync_db`: 섹션/페이지를 DB에 동기화
- `get_recent_items`: 최근 접근한 섹션/페이지 조회
- `save_section_to_db`: 섹션 정보를 DB에 저장
- `save_page_to_db`: 페이지 정보를 DB에 저장
- `find_section_by_name`: 이름으로 섹션 검색
- `find_page_by_name`: 이름으로 페이지 검색

## 사용법

```python
from mcp_onenote import OneNoteService

async def main():
    service = OneNoteService()
    await service.initialize()

    try:
        # 노트북 목록 조회
        result = await service.list_notebooks("user@example.com")
        print(result)

        # 섹션 목록 조회
        sections = await service.list_sections("user@example.com", notebook_id="nb_id")
        print(sections)

        # 페이지 생성
        page = await service.create_page(
            user_email="user@example.com",
            section_id="section_id",
            title="새 페이지",
            content="<p>Hello World</p>",
        )
        print(page)
    finally:
        await service.close()
```

## 인증

`session` 모듈의 `AuthManager`를 사용하여 인증을 처리합니다.
Azure AD OAuth 2.0 플로우를 통해 사용자 인증을 수행합니다.

## 테스트

```bash
cd /home/kimghw/connector_auth
pytest mcp_onenote/tests/ -v
```

## 원본 모듈

이 모듈은 [KR365](https://github.com/kimghw/KR365) 레포지토리의 `modules/onenote_mcp`를 기반으로 리팩토링되었습니다.
