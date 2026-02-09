"""
OneNote Service Tests
리팩토링된 구조 반영:
- svc.page  → OneNotePageManager (create_page, edit_page, delete_page, sync_db)
- svc.agent → OneNoteAgent (AI 요약/검색)
- svc.db    → OneNoteDBQuery (get_recent_items, save_section, save_page, find_*)
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mcp_onenote.onenote_service import OneNoteService
from mcp_onenote.onenote_page import OneNotePageManager
from mcp_onenote.onenote_db_query import OneNoteDBQuery
from mcp_onenote.onenote_types import (
    PageAction,
    SectionAction,
    ContentAction,
)


class TestOneNoteService:
    """OneNoteService Facade 테스트"""

    @pytest.fixture
    def service(self):
        """서비스 인스턴스 생성"""
        return OneNoteService()

    @pytest.fixture
    def mock_client(self):
        """Mock GraphOneNoteClient"""
        mock = AsyncMock()
        return mock

    @pytest.fixture
    def mock_db_service(self):
        """Mock OneNoteDBService"""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def initialized_service(self, service, mock_client, mock_db_service):
        """초기화된 서비스 (page, db 접근자 포함)"""
        service._client = mock_client
        service._db_service = mock_db_service
        service._initialized = True

        service._page_manager = OneNotePageManager(
            mock_client, mock_db_service
        )
        service._db_query = OneNoteDBQuery(mock_db_service)

        return service

    # ========================================================================
    # 초기화 테스트
    # ========================================================================

    @pytest.mark.asyncio
    async def test_initialize(self, service):
        """서비스 초기화 테스트"""
        with patch.object(service, '_client', new_callable=AsyncMock) as mock_client:
            mock_client.initialize = AsyncMock(return_value=True)
            service._client = mock_client
            service._initialized = True

            assert service._initialized is True

    @pytest.mark.asyncio
    async def test_not_initialized_error(self, service):
        """초기화되지 않은 상태에서 호출 시 에러 테스트"""
        with pytest.raises(RuntimeError, match="not initialized"):
            await service.list_notebooks("test@example.com")

    # ========================================================================
    # Graph API 순수 위임 테스트 (OneNoteService 직접 메서드)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_list_notebooks(self, service, mock_client):
        """노트북 목록 조회 테스트"""
        mock_client.list_notebooks = AsyncMock(return_value={
            "success": True,
            "notebooks": [
                {"id": "nb1", "display_name": "Notebook 1"},
                {"id": "nb2", "display_name": "Notebook 2"},
            ],
            "count": 2,
        })

        service._client = mock_client
        service._initialized = True

        result = await service.list_notebooks("test@example.com")

        assert result["success"] is True
        assert result["count"] == 2
        mock_client.list_notebooks.assert_called_once_with("test@example.com")

    @pytest.mark.asyncio
    async def test_list_sections(self, service, mock_client):
        """섹션 목록 조회 테스트"""
        mock_client.list_sections = AsyncMock(return_value={
            "success": True,
            "sections": [
                {"id": "s1", "display_name": "Section 1"},
            ],
            "count": 1,
        })

        service._client = mock_client
        service._initialized = True

        result = await service.list_sections("test@example.com", notebook_id="nb1")

        assert result["success"] is True
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_create_section(self, service, mock_client):
        """섹션 생성 테스트"""
        mock_client.create_section = AsyncMock(return_value={
            "success": True,
            "section": {"id": "s_new", "display_name": "New Section"},
        })

        service._client = mock_client
        service._initialized = True

        result = await service.create_section(
            user_email="test@example.com",
            notebook_id="nb1",
            section_name="New Section",
        )

        assert result["success"] is True
        assert result["section"]["display_name"] == "New Section"

    @pytest.mark.asyncio
    async def test_list_pages(self, service, mock_client):
        """페이지 목록 조회 테스트"""
        mock_client.list_pages = AsyncMock(return_value={
            "success": True,
            "pages": [
                {"id": "p1", "title": "Page 1"},
                {"id": "p2", "title": "Page 2"},
            ],
            "count": 2,
        })

        service._client = mock_client
        service._initialized = True

        result = await service.list_pages("test@example.com", section_id="s1")

        assert result["success"] is True
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_get_page_content(self, service, mock_client):
        """페이지 내용 조회 테스트"""
        mock_client.get_page_content = AsyncMock(return_value={
            "success": True,
            "page_id": "p1",
            "content": "<html><body>Test content</body></html>",
        })

        service._client = mock_client
        service._initialized = True

        result = await service.get_page_content("test@example.com", "p1")

        assert result["success"] is True
        assert "content" in result

    @pytest.mark.asyncio
    async def test_manage_sections_create(self, service, mock_client):
        """manage_sections - 섹션 생성 테스트"""
        mock_client.create_section = AsyncMock(return_value={
            "success": True,
            "section": {"id": "s_new", "display_name": "Test Section"},
        })

        service._client = mock_client
        service._initialized = True

        result = await service.manage_sections(
            user_email="test@example.com",
            action=SectionAction.CREATE_SECTION,
            notebook_id="nb1",
            section_name="Test Section",
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_manage_page_content_get(self, service, mock_client):
        """manage_page_content - 내용 조회 테스트"""
        mock_client.get_page_content = AsyncMock(return_value={
            "success": True,
            "page_id": "p1",
            "content": "<html><body>Content</body></html>",
        })

        service._client = mock_client
        service._initialized = True

        result = await service.manage_page_content(
            user_email="test@example.com",
            action=ContentAction.GET,
            page_id="p1",
        )

        assert result["success"] is True

    # ========================================================================
    # svc.page 테스트 (OneNotePageManager)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_create_page(self, initialized_service, mock_client, mock_db_service):
        """페이지 생성 테스트 (svc.page.create_page)"""
        mock_client.create_page = AsyncMock(return_value={
            "success": True,
            "page": {"id": "p_new", "title": "New Page"},
        })

        result = await initialized_service.page.create_page(
            user_email="test@example.com",
            section_id="s1",
            title="New Page",
            content="<p>Hello World</p>",
        )

        assert result["success"] is True
        assert result["page"]["title"] == "New Page"

    @pytest.mark.asyncio
    async def test_edit_page_append(self, initialized_service, mock_client, mock_db_service):
        """페이지 편집(append) 테스트 (svc.page.edit_page)"""
        mock_client.update_page = AsyncMock(return_value={
            "success": True,
        })
        mock_db_service.get_summary = MagicMock(return_value=None)

        result = await initialized_service.page.edit_page(
            user_email="test@example.com",
            page_id="p1",
            action=PageAction.APPEND,
            content="<p>Appended content</p>",
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_delete_page(self, initialized_service, mock_client, mock_db_service):
        """페이지 삭제 테스트 (svc.page.delete_page)"""
        mock_client.delete_page = AsyncMock(return_value={
            "success": True,
        })

        result = await initialized_service.page.delete_page(
            "test@example.com", "p1"
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_sync_db(self, initialized_service, mock_client, mock_db_service):
        """DB 동기화 테스트 (svc.page.sync_db)"""
        mock_client.list_pages = AsyncMock(return_value={
            "success": True,
            "pages": [{"id": "p1", "title": "Page 1"}],
        })
        mock_db_service.sync_pages_to_db = AsyncMock(return_value={"synced": 1})

        result = await initialized_service.page.sync_db(
            user_email="test@example.com",
        )

        assert result["success"] is True
        assert result["pages_synced"] == 1

    # ========================================================================
    # svc.db 테스트 (OneNoteDBQuery)
    # ========================================================================

    def test_get_recent_items_sections(self, initialized_service, mock_db_service):
        """최근 섹션 조회 테스트 (svc.db.get_recent_items)"""
        mock_db_service.get_recent_items = MagicMock(return_value=[
            {"item_id": "s1", "item_name": "Section 1", "item_type": "section"},
            {"item_id": "s2", "item_name": "Section 2", "item_type": "section"},
        ])

        result = initialized_service.db.get_recent_items(
            "test@example.com", "section", 5
        )

        assert result["success"] is True
        assert result["count"] == 2
        mock_db_service.get_recent_items.assert_called_once_with(
            "test@example.com", "section", 5
        )

    def test_get_recent_items_pages(self, initialized_service, mock_db_service):
        """최근 페이지 조회 테스트 (svc.db.get_recent_items)"""
        mock_db_service.get_recent_items = MagicMock(return_value=[
            {"item_id": "p1", "item_name": "Page 1", "item_type": "page"},
        ])

        result = initialized_service.db.get_recent_items(
            "test@example.com", "page", 5
        )

        assert result["success"] is True
        assert result["count"] == 1

    def test_save_section_to_db(self, initialized_service, mock_db_service):
        """섹션 DB 저장 테스트 (svc.db.save_section)"""
        mock_db_service.save_section = MagicMock(return_value=True)

        result = initialized_service.db.save_section(
            user_email="test@example.com",
            notebook_id="nb1",
            section_id="s1",
            section_name="Test Section",
            notebook_name="Test Notebook",
        )

        assert result["success"] is True
        mock_db_service.save_section.assert_called_once()

    def test_save_page_to_db(self, initialized_service, mock_db_service):
        """페이지 DB 저장 테스트 (svc.db.save_page)"""
        mock_db_service.save_page = MagicMock(return_value=True)

        result = initialized_service.db.save_page(
            user_email="test@example.com",
            section_id="s1",
            page_id="p1",
            page_title="Test Page",
        )

        assert result["success"] is True
        mock_db_service.save_page.assert_called_once()

    def test_find_section_by_name(self, initialized_service, mock_db_service):
        """이름으로 섹션 검색 테스트 (svc.db.find_section_by_name)"""
        mock_db_service.get_section = MagicMock(return_value={
            "section_id": "s1",
            "section_name": "My Section",
            "notebook_id": "nb1",
        })

        result = initialized_service.db.find_section_by_name(
            "test@example.com", "My Section"
        )

        assert result["success"] is True
        assert result["section"]["section_id"] == "s1"

    def test_find_section_by_name_not_found(self, initialized_service, mock_db_service):
        """섹션 검색 실패 테스트 (svc.db.find_section_by_name)"""
        mock_db_service.get_section = MagicMock(return_value=None)

        result = initialized_service.db.find_section_by_name(
            "test@example.com", "Unknown"
        )

        assert result["success"] is False

    def test_find_page_by_name(self, initialized_service, mock_db_service):
        """이름으로 페이지 검색 테스트 (svc.db.find_page_by_name)"""
        mock_db_service.get_page = MagicMock(return_value={
            "page_id": "p1",
            "page_title": "My Page",
            "section_id": "s1",
        })

        result = initialized_service.db.find_page_by_name(
            "test@example.com", "My Page"
        )

        assert result["success"] is True
        assert result["page"]["page_id"] == "p1"

    # ========================================================================
    # 접근자 테스트
    # ========================================================================

    def test_page_property_not_initialized(self, service):
        """초기화 전 page 접근 시 에러"""
        with pytest.raises(RuntimeError, match="not initialized"):
            _ = service.page

    def test_agent_property_not_initialized(self, service):
        """초기화 전 agent 접근 시 에러"""
        with pytest.raises(RuntimeError, match="not initialized"):
            _ = service.agent

    def test_db_property_not_initialized(self, service):
        """초기화 전 db 접근 시 에러"""
        with pytest.raises(RuntimeError, match="not initialized"):
            _ = service.db


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
