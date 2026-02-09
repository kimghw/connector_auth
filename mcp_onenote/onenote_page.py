"""
OneNote Page Manager - 페이지 CRUD + DB 동기화
Graph API 호출 후 DB 연동이 필요한 페이지 작업 담당
"""

import logging
from typing import Dict, Any, Optional

from .graph_onenote_client import GraphOneNoteClient
from .onenote_db_service import OneNoteDBService
from .onenote_types import PageAction

logger = logging.getLogger(__name__)


class OneNotePageManager:
    """
    페이지 CRUD + DB 동기화

    - Graph API 호출 후 DB에 자동 저장/삭제
    - 편집 시 기존 요약 자동 갱신
    - 전체 페이지 DB 동기화
    """

    def __init__(
        self,
        client: GraphOneNoteClient,
        db_service: OneNoteDBService,
        agent=None,
    ):
        self._client = client
        self._db_service = db_service
        self._agent = agent  # OneNoteAgent (요약 자동 갱신용)

    def set_agent(self, agent):
        """Agent 설정 (순환 참조 방지를 위한 후속 설정)"""
        self._agent = agent

    async def create_page(
        self,
        user_email: str,
        section_id: str,
        title: str,
        content: str,
    ) -> Dict[str, Any]:
        """페이지 생성 + DB 저장"""
        result = await self._client.create_page(user_email, section_id, title, content)

        if result.get("success") and self._db_service:
            page = result.get("page", {})
            self._db_service.save_item(
                user_id=user_email,
                item_type="page",
                item_id=page.get("id"),
                item_name=page.get("title", title),
                notebook_id=page.get("notebook_id"),
                notebook_name=page.get("notebook_name"),
                section_id=page.get("parent_section_id") or section_id,
                section_name=page.get("parent_section_name"),
                web_url=page.get("web_url"),
                update_accessed=True,
            )

        return result

    async def edit_page(
        self,
        user_email: str,
        page_id: str,
        action: PageAction = PageAction.APPEND,
        content: Optional[str] = None,
        target: Optional[str] = None,
        position: str = "after",
    ) -> Dict[str, Any]:
        """페이지 편집 + DB 업데이트 + 요약 자동 갱신"""
        if not content and action != PageAction.CLEAN:
            return {"success": False, "error": "content가 필요합니다."}

        result = await self._client.update_page(
            user_email=user_email,
            page_id=page_id,
            action=action,
            content=content or "",
            target=target,
            position=position,
        )

        if result.get("success") and self._db_service:
            self._db_service.save_item(
                user_id=user_email,
                item_type="page",
                item_id=page_id,
                item_name="",
                update_accessed=True,
            )

            # 페이지 편집 후 요약 자동 갱신 (기존 요약이 있는 경우만)
            existing_summary = self._db_service.get_summary(page_id)
            if existing_summary and self._agent:
                try:
                    await self._agent.summarize_page(user_email, page_id, force_refresh=True)
                    logger.info(f"✅ 페이지 편집 후 요약 자동 갱신: {page_id}")
                except Exception as e:
                    logger.warning(f"⚠️ 페이지 편집 후 요약 갱신 실패 (무시): {e}")

        return result

    async def delete_page(
        self,
        user_email: str,
        page_id: str,
    ) -> Dict[str, Any]:
        """페이지 삭제 + DB/요약 삭제"""
        result = await self._client.delete_page(user_email, page_id)

        if result.get("success") and self._db_service:
            self._db_service.delete_item(user_id=user_email, item_id=page_id)
            self._db_service.delete_summary(page_id=page_id)

        return result

    async def sync_db(
        self,
        user_email: str,
    ) -> Dict[str, Any]:
        """
        OneNote 전체 페이지를 DB에 동기화
        /me/onenote/pages로 전체 페이지를 조회하여 DB에 저장
        """
        result = {"success": True, "pages_synced": 0}

        pages_result = await self._client.list_pages(user_email)
        if pages_result.get("success"):
            pages = pages_result.get("pages", [])
            sync_result = await self._db_service.sync_pages_to_db(
                user_id=user_email,
                pages=pages,
            )
            result["pages_synced"] = sync_result.get("synced", 0)
        else:
            result["success"] = False
            result["error"] = pages_result.get("error", "페이지 조회 실패")

        return result
