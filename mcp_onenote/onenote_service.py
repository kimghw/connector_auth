"""
OneNote Service - GraphOneNoteClient Facade
인자를 그대로 위임하고, 필요시 일부 값만 조정하는 서비스 레이어
(mcp_outlook/outlook_service.py 구조 참조)
"""

from typing import Dict, Any, Optional, List

from .graph_onenote_client import GraphOneNoteClient
from .onenote_db_service import OneNoteDBService
from .onenote_types import (
    PageAction,
    SectionAction,
    ContentAction,
)

# mcp_service decorator is only needed for registry scanning, not runtime
try:
    from mcp_editor.mcp_service_registry.mcp_service_decorator import mcp_service
except ImportError:
    # Define a no-op decorator for runtime when mcp_editor is not available
    def mcp_service(**kwargs):
        def decorator(func):
            return func
        return decorator


class OneNoteService:
    """
    GraphOneNoteClient의 Facade

    - 동일 시그니처로 위임
    - 일부 값만 조정/하드코딩
    - DB 연동으로 최근 항목 추적 지원
    """

    def __init__(self):
        self._client: Optional[GraphOneNoteClient] = None
        self._db_service: Optional[OneNoteDBService] = None
        self._initialized = False

    async def initialize(self) -> bool:
        """서비스 초기화"""
        if self._initialized:
            return True

        self._client = GraphOneNoteClient()
        self._db_service = OneNoteDBService()

        if await self._client.initialize():
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

    @mcp_service(
        tool_name="handler_onenote_list_notebooks",
        server_name="onenote",
        service_name="list_notebooks",
        category="onenote_notebook",
        tags=["query", "notebook"],
        priority=5,
        description="OneNote 노트북 목록 조회",
    )
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

    @mcp_service(
        tool_name="handler_onenote_manage_sections",
        server_name="onenote",
        service_name="manage_sections",
        category="onenote_section",
        tags=["manage", "section"],
        priority=5,
        description="OneNote 섹션 관리 (생성, 목록 조회)",
    )
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

    @mcp_service(
        tool_name="handler_onenote_list_sections",
        server_name="onenote",
        service_name="list_sections",
        category="onenote_section",
        tags=["query", "section"],
        priority=5,
        description="OneNote 섹션 목록 조회",
    )
    async def list_sections(
        self,
        user_email: str,
        notebook_id: Optional[str] = None,
        top: int = 50,
    ) -> Dict[str, Any]:
        """섹션 목록 조회"""
        self._ensure_initialized()
        return await self._client.list_sections(user_email, notebook_id, top)

    @mcp_service(
        tool_name="handler_onenote_create_section",
        server_name="onenote",
        service_name="create_section",
        category="onenote_section",
        tags=["create", "section"],
        priority=5,
        description="OneNote 섹션 생성",
    )
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
    # 페이지 관련 메서드
    # ========================================================================

    @mcp_service(
        tool_name="handler_onenote_list_pages",
        server_name="onenote",
        service_name="list_pages",
        category="onenote_page",
        tags=["query", "page"],
        priority=5,
        description="OneNote 페이지 목록 조회",
    )
    async def list_pages(
        self,
        user_email: str,
        section_id: Optional[str] = None,
        top: int = 50,
    ) -> Dict[str, Any]:
        """페이지 목록 조회"""
        self._ensure_initialized()
        return await self._client.list_pages(user_email, section_id, top)

    @mcp_service(
        tool_name="handler_onenote_manage_page_content",
        server_name="onenote",
        service_name="manage_page_content",
        category="onenote_page",
        tags=["manage", "page", "content"],
        priority=5,
        description="OneNote 페이지 내용 관리 (조회, 생성, 삭제)",
    )
    async def manage_page_content(
        self,
        user_email: str,
        action: ContentAction,
        page_id: Optional[str] = None,
        section_id: Optional[str] = None,
        title: Optional[str] = None,
        content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """페이지 내용 관리 - action에 따라 동작"""
        self._ensure_initialized()

        if action == ContentAction.GET:
            if not page_id:
                return {"success": False, "error": "page_id가 필요합니다."}
            return await self._client.get_page_content(user_email, page_id)

        elif action == ContentAction.CREATE:
            if not section_id or not title or not content:
                return {"success": False, "error": "section_id, title, content가 필요합니다."}
            return await self._client.create_page(user_email, section_id, title, content)

        elif action == ContentAction.DELETE:
            if not page_id:
                return {"success": False, "error": "page_id가 필요합니다."}
            return await self._client.delete_page(user_email, page_id)

        else:
            return {"success": False, "error": f"알 수 없는 action: {action}"}

    @mcp_service(
        tool_name="handler_onenote_get_page_content",
        server_name="onenote",
        service_name="get_page_content",
        category="onenote_page",
        tags=["query", "page", "content"],
        priority=5,
        description="OneNote 페이지 내용 조회",
    )
    async def get_page_content(
        self,
        user_email: str,
        page_id: str,
    ) -> Dict[str, Any]:
        """페이지 내용 조회"""
        self._ensure_initialized()
        return await self._client.get_page_content(user_email, page_id)

    @mcp_service(
        tool_name="handler_onenote_create_page",
        server_name="onenote",
        service_name="create_page",
        category="onenote_page",
        tags=["create", "page"],
        priority=5,
        description="OneNote 페이지 생성",
    )
    async def create_page(
        self,
        user_email: str,
        section_id: str,
        title: str,
        content: str,
    ) -> Dict[str, Any]:
        """페이지 생성"""
        self._ensure_initialized()
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

    @mcp_service(
        tool_name="handler_onenote_edit_page",
        server_name="onenote",
        service_name="edit_page",
        category="onenote_page",
        tags=["edit", "page"],
        priority=5,
        description="OneNote 페이지 편집",
    )
    async def edit_page(
        self,
        user_email: str,
        page_id: str,
        action: PageAction = PageAction.APPEND,
        content: Optional[str] = None,
        target: Optional[str] = None,
        position: str = "after",
    ) -> Dict[str, Any]:
        """페이지 편집"""
        self._ensure_initialized()

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
            if existing_summary:
                try:
                    await self.summarize_page(user_email, page_id, force_refresh=True)
                    logger.info(f"✅ 페이지 편집 후 요약 자동 갱신: {page_id}")
                except Exception as e:
                    logger.warning(f"⚠️ 페이지 편집 후 요약 갱신 실패 (무시): {e}")

        return result

    @mcp_service(
        tool_name="handler_onenote_delete_page",
        server_name="onenote",
        service_name="delete_page",
        category="onenote_page",
        tags=["delete", "page"],
        priority=5,
        description="OneNote 페이지 삭제",
    )
    async def delete_page(
        self,
        user_email: str,
        page_id: str,
    ) -> Dict[str, Any]:
        """페이지 삭제"""
        self._ensure_initialized()
        result = await self._client.delete_page(user_email, page_id)

        if result.get("success") and self._db_service:
            self._db_service.delete_item(user_id=user_email, item_id=page_id)
            self._db_service.delete_summary(page_id=page_id)

        return result

    # ========================================================================
    # DB 연동 메서드 (최근 아이템, 동기화)
    # ========================================================================

    @mcp_service(
        tool_name="handler_onenote_sync_db",
        server_name="onenote",
        service_name="sync_db",
        category="onenote_db",
        tags=["sync", "db"],
        priority=5,
        description="OneNote 전체 페이지를 DB에 동기화",
    )
    async def sync_db(
        self,
        user_email: str,
    ) -> Dict[str, Any]:
        """
        OneNote 전체 페이지를 DB에 동기화
        /me/onenote/pages로 전체 페이지를 조회하여 DB에 저장

        Args:
            user_email: 사용자 이메일

        Returns:
            동기화 결과
        """
        self._ensure_initialized()

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

    @mcp_service(
        tool_name="handler_onenote_get_recent_items",
        server_name="onenote",
        service_name="get_recent_items",
        category="onenote_db",
        tags=["query", "recent"],
        priority=5,
        description="최근 접근한 OneNote 섹션/페이지 조회",
    )
    async def get_recent_items(
        self,
        user_email: str,
        item_type: str = "section",
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        최근 접근한 아이템 조회

        Args:
            user_email: 사용자 이메일
            item_type: 'section' 또는 'page'
            limit: 조회할 개수

        Returns:
            최근 아이템 목록
        """
        self._ensure_initialized()

        if item_type not in ("section", "page"):
            return {"success": False, "error": "item_type은 'section' 또는 'page'여야 합니다."}

        items = self._db_service.get_recent_items(user_email, item_type, limit)
        return {
            "success": True,
            "item_type": item_type,
            "items": items,
            "count": len(items),
        }

    @mcp_service(
        tool_name="handler_onenote_save_section_to_db",
        server_name="onenote",
        service_name="save_section_to_db",
        category="onenote_db",
        tags=["save", "section", "db"],
        priority=5,
        description="섹션 정보를 DB에 저장 (최근 접근 기록)",
    )
    async def save_section_to_db(
        self,
        user_email: str,
        notebook_id: str,
        section_id: str,
        section_name: str,
        notebook_name: Optional[str] = None,
        mark_as_recent: bool = True,
    ) -> Dict[str, Any]:
        """
        섹션 정보를 DB에 저장

        Args:
            user_email: 사용자 이메일
            notebook_id: 노트북 ID
            section_id: 섹션 ID
            section_name: 섹션 이름
            notebook_name: 노트북 이름
            mark_as_recent: 최근 접근으로 표시

        Returns:
            저장 결과
        """
        self._ensure_initialized()

        success = self._db_service.save_section(
            user_id=user_email,
            notebook_id=notebook_id,
            section_id=section_id,
            section_name=section_name,
            notebook_name=notebook_name,
            update_accessed=mark_as_recent,
        )

        if success:
            return {"success": True, "message": f"섹션 '{section_name}' 저장 완료"}
        return {"success": False, "message": "섹션 저장 실패"}

    @mcp_service(
        tool_name="handler_onenote_save_page_to_db",
        server_name="onenote",
        service_name="save_page_to_db",
        category="onenote_db",
        tags=["save", "page", "db"],
        priority=5,
        description="페이지 정보를 DB에 저장 (최근 접근 기록)",
    )
    async def save_page_to_db(
        self,
        user_email: str,
        section_id: str,
        page_id: str,
        page_title: str,
        mark_as_recent: bool = True,
    ) -> Dict[str, Any]:
        """
        페이지 정보를 DB에 저장

        Args:
            user_email: 사용자 이메일
            section_id: 섹션 ID
            page_id: 페이지 ID
            page_title: 페이지 제목
            mark_as_recent: 최근 접근으로 표시

        Returns:
            저장 결과
        """
        self._ensure_initialized()

        success = self._db_service.save_page(
            user_id=user_email,
            section_id=section_id,
            page_id=page_id,
            page_title=page_title,
            update_accessed=mark_as_recent,
        )

        if success:
            return {"success": True, "message": f"페이지 '{page_title}' 저장 완료"}
        return {"success": False, "message": "페이지 저장 실패"}

    @mcp_service(
        tool_name="handler_onenote_find_section_by_name",
        server_name="onenote",
        service_name="find_section_by_name",
        category="onenote_db",
        tags=["query", "search", "section"],
        priority=5,
        description="이름으로 섹션 검색 (DB에서)",
    )
    async def find_section_by_name(
        self,
        user_email: str,
        section_name: str,
    ) -> Dict[str, Any]:
        """
        이름으로 섹션 검색

        Args:
            user_email: 사용자 이메일
            section_name: 섹션 이름

        Returns:
            섹션 정보
        """
        self._ensure_initialized()

        section = self._db_service.get_section(user_email, section_name)
        if section:
            return {"success": True, "section": section}
        return {"success": False, "message": f"섹션 '{section_name}'을 찾을 수 없습니다."}

    @mcp_service(
        tool_name="handler_onenote_find_page_by_name",
        server_name="onenote",
        service_name="find_page_by_name",
        category="onenote_db",
        tags=["query", "search", "page"],
        priority=5,
        description="이름으로 페이지 검색 (DB에서)",
    )
    async def find_page_by_name(
        self,
        user_email: str,
        page_title: str,
    ) -> Dict[str, Any]:
        """
        이름으로 페이지 검색

        Args:
            user_email: 사용자 이메일
            page_title: 페이지 제목

        Returns:
            페이지 정보
        """
        self._ensure_initialized()

        page = self._db_service.get_page(user_email, page_title)
        if page:
            return {"success": True, "page": page}
        return {"success": False, "message": f"페이지 '{page_title}'을 찾을 수 없습니다."}

    # ========================================================================
    # 페이지 요약 관련 메서드
    # ========================================================================

    @mcp_service(
        tool_name="handler_onenote_summarize_page",
        server_name="onenote",
        service_name="summarize_page",
        category="onenote_summary",
        tags=["summarize", "page", "ai"],
        priority=5,
        description="OneNote 페이지 AI 요약 생성 (전체 요약 + 단락별 요약 + 키워드 추출)",
    )
    async def summarize_page(
        self,
        user_email: str,
        page_id: str,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        페이지 요약 생성/갱신

        Args:
            user_email: 사용자 이메일
            page_id: 페이지 ID
            force_refresh: True이면 캐시 무시하고 재생성

        Returns:
            요약 결과 (summary, paragraph_summaries, keywords, cached)
        """
        self._ensure_initialized()

        from .onenote_summarizer import summarize_page as run_summarize, compute_content_hash, load_config, is_sdk_available

        # 0. SDK 사용 가능 여부 확인
        if not is_sdk_available():
            return {"success": False, "skipped": True, "message": "Claude Code SDK가 설치되지 않았거나 ANTHROPIC_API_KEY가 설정되지 않았습니다."}

        # 1. 페이지 HTML 가져오기
        content_result = await self._client.get_page_content(user_email, page_id)
        if not content_result.get("success"):
            return {"success": False, "error": content_result.get("error", "페이지 내용 조회 실패")}

        html_content = content_result.get("content", "")
        page_title = content_result.get("title", "")

        # 2. 콘텐츠 해시로 변경 감지
        content_hash = compute_content_hash(html_content)

        if not force_refresh:
            existing = self._db_service.get_summary(page_id)
            if existing and existing.get("content_hash") == content_hash:
                return {
                    "success": True,
                    "cached": True,
                    "page_id": page_id,
                    "page_title": page_title,
                    "summary": existing["summary"],
                    "keywords": existing.get("keywords", []),
                    "content_hash": content_hash,
                    "summarized_at": existing.get("summarized_at"),
                }

        # 3. AI 요약 실행
        config = load_config()
        summary_result = await run_summarize(html_content, page_title, config)

        # 4. DB 저장
        self._db_service.save_summary(
            page_id=page_id,
            user_id=user_email,
            page_title=page_title,
            summary=summary_result["summary"],
            paragraph_summaries=[],
            keywords=summary_result["keywords"],
            content_hash=summary_result["content_hash"],
        )

        return {
            "success": True,
            "cached": False,
            "page_id": page_id,
            "page_title": page_title,
            "summary": summary_result["summary"],
            "keywords": summary_result["keywords"],
            "content_hash": summary_result["content_hash"],
        }

    @mcp_service(
        tool_name="handler_onenote_get_page_summary",
        server_name="onenote",
        service_name="get_page_summary",
        category="onenote_summary",
        tags=["query", "summary", "page"],
        priority=5,
        description="저장된 OneNote 페이지 요약 조회",
    )
    async def get_page_summary(
        self,
        user_email: str,
        page_id: str,
    ) -> Dict[str, Any]:
        """
        저장된 페이지 요약 조회

        Args:
            user_email: 사용자 이메일
            page_id: 페이지 ID

        Returns:
            저장된 요약 정보
        """
        self._ensure_initialized()

        summary = self._db_service.get_summary(page_id)
        if summary:
            return {"success": True, **summary}
        return {"success": False, "message": f"페이지 '{page_id}'의 요약이 없습니다."}

    @mcp_service(
        tool_name="handler_onenote_list_summarized_pages",
        server_name="onenote",
        service_name="list_summarized_pages",
        category="onenote_summary",
        tags=["query", "summary", "list"],
        priority=5,
        description="요약이 생성된 OneNote 페이지 목록 조회",
    )
    async def list_summarized_pages(
        self,
        user_email: str,
    ) -> Dict[str, Any]:
        """
        요약된 페이지 목록 조회

        Args:
            user_email: 사용자 이메일

        Returns:
            요약된 페이지 목록
        """
        self._ensure_initialized()

        summaries = self._db_service.list_summaries(user_email)
        return {
            "success": True,
            "pages": summaries,
            "count": len(summaries),
        }
