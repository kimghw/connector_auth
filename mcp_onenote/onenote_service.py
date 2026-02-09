"""
OneNote Service - GraphOneNoteClient Facade
Graph API 순수 위임 + 하위 모듈 접근자
"""

import logging
from typing import Dict, Any, Optional, List

from .graph_onenote_client import GraphOneNoteClient
from .onenote_db_service import OneNoteDBService
from .onenote_types import (
    SectionAction,
    ContentAction,
)

logger = logging.getLogger(__name__)


class OneNoteService:
    """
    GraphOneNoteClient의 Facade

    - Graph API 순수 위임 (노트북, 섹션, 페이지 조회)
    - svc.page   → OneNotePageManager (CRUD + DB)
    - svc.agent  → OneNoteAgent (AI 요약/검색)
    - svc.db     → OneNoteDBQuery (DB 조회/저장)
    """

    def __init__(self):
        self._client: Optional[GraphOneNoteClient] = None
        self._db_service: Optional[OneNoteDBService] = None
        self._page_manager = None
        self._agent = None
        self._db_query = None
        self._initialized = False

    async def initialize(self) -> bool:
        """서비스 초기화"""
        if self._initialized:
            return True

        self._client = GraphOneNoteClient()
        self._db_service = OneNoteDBService()

        if await self._client.initialize():
            from .onenote_agent import OneNoteAgent
            from .onenote_page import OneNotePageManager
            from .onenote_db_query import OneNoteDBQuery

            self._agent = OneNoteAgent(self._client, self._db_service)
            self._page_manager = OneNotePageManager(
                self._client, self._db_service, self._agent
            )
            self._db_query = OneNoteDBQuery(self._db_service)
            self._initialized = True
            return True
        return False

    def _ensure_initialized(self):
        """초기화 확인"""
        if not self._initialized or not self._client:
            raise RuntimeError("OneNoteService not initialized. Call initialize() first.")

    async def close(self):
        """리소스 정리"""
        if self._client:
            await self._client.close()
            self._client = None
        self._initialized = False

    # ========================================================================
    # 노트북 관련 메서드
    # ========================================================================

    async def list_notebooks(
        self,
        user_email: str,
    ) -> Dict[str, Any]:
        """노트북 목록 조회"""
        self._ensure_initialized()
        return await self._client.list_notebooks(user_email)

    # ========================================================================
    # 섹션 관련 메서드
    # ========================================================================

    async def manage_sections(
        self,
        user_email: str,
        action: SectionAction,
        notebook_id: Optional[str] = None,
        section_name: Optional[str] = None,
        section_id: Optional[str] = None,
        top: int = 50,
    ) -> Dict[str, Any]:
        """섹션 관리 - action에 따라 동작"""
        self._ensure_initialized()

        if action == SectionAction.CREATE_SECTION:
            if not notebook_id or not section_name:
                return {"success": False, "error": "notebook_id와 section_name이 필요합니다."}
            return await self._client.create_section(user_email, notebook_id, section_name)

        elif action == SectionAction.LIST_SECTIONS:
            return await self._client.list_sections(user_email, notebook_id, top)

        elif action == SectionAction.LIST_PAGES:
            return await self._client.list_pages(user_email, section_id, top)

        else:
            return {"success": False, "error": f"알 수 없는 action: {action}"}

    async def list_sections(
        self,
        user_email: str,
        notebook_id: Optional[str] = None,
        top: int = 50,
    ) -> Dict[str, Any]:
        """섹션 목록 조회"""
        self._ensure_initialized()
        return await self._client.list_sections(user_email, notebook_id, top)

    async def create_section(
        self,
        user_email: str,
        notebook_id: str,
        section_name: str,
    ) -> Dict[str, Any]:
        """섹션 생성"""
        self._ensure_initialized()
        return await self._client.create_section(user_email, notebook_id, section_name)

    # ========================================================================
    # 페이지 조회 (순수 위임)
    # ========================================================================

    async def list_pages(
        self,
        user_email: str,
        section_id: Optional[str] = None,
        top: int = 50,
    ) -> Dict[str, Any]:
        """페이지 목록 조회"""
        self._ensure_initialized()
        return await self._client.list_pages(user_email, section_id, top)

    async def manage_page_content(
        self,
        user_email: str,
        action: ContentAction,
        page_id: Optional[str] = None,
        section_id: Optional[str] = None,
        title: Optional[str] = None,
        content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """페이지 내용 관리 - action에 따라 동작 (CREATE/DELETE는 PageManager 위임)"""
        self._ensure_initialized()

        if action == ContentAction.GET:
            if not page_id:
                return {"success": False, "error": "page_id가 필요합니다."}
            return await self._client.get_page_content(user_email, page_id)

        elif action == ContentAction.CREATE:
            if not section_id or not title or not content:
                return {"success": False, "error": "section_id, title, content가 필요합니다."}
            return await self.page.create_page(user_email, section_id, title, content)

        elif action == ContentAction.DELETE:
            if not page_id:
                return {"success": False, "error": "page_id가 필요합니다."}
            return await self.page.delete_page(user_email, page_id)

        else:
            return {"success": False, "error": f"알 수 없는 action: {action}"}

    async def get_page_content(
        self,
        user_email: str,
        page_id: str,
    ) -> Dict[str, Any]:
        """페이지 내용 조회"""
        self._ensure_initialized()
        return await self._client.get_page_content(user_email, page_id)

    # ========================================================================
    # 접근자 (PageManager, Agent, DBQuery)
    # ========================================================================

    @property
    def page(self):
        """OneNotePageManager 인스턴스 반환"""
        if not self._page_manager:
            raise RuntimeError("OneNoteService not initialized. Call initialize() first.")
        return self._page_manager

    @property
    def agent(self):
        """OneNoteAgent 인스턴스 반환"""
        if not self._agent:
            raise RuntimeError("OneNoteService not initialized. Call initialize() first.")
        return self._agent

    @property
    def db(self):
        """OneNoteDBQuery 인스턴스 반환"""
        if not self._db_query:
            raise RuntimeError("OneNoteService not initialized. Call initialize() first.")
        return self._db_query
