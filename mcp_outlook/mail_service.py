"""
Mail Service - GraphMailClient Facade
인자를 그대로 위임하고, 필요시 일부 값만 조정하는 서비스 레이어
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from graph_mail_client import (
    GraphMailClient,
    QueryMethod,
    ProcessingMode
)
from mail_processing_options import (
    MailStorageOption,
    AttachmentOption,
    OutputFormat
)
from outlook_types import FilterParams, ExcludeParams, SelectParams

# mcp_service decorator is only needed for registry scanning, not runtime
try:
    from mcp_editor.mcp_service_registry.mcp_service_decorator import mcp_service
except ImportError:
    # Define a no-op decorator for runtime when mcp_editor is not available
    def mcp_service(**kwargs):
        def decorator(func):
            return func
        return decorator


class MailService:
    """
    GraphMailClient의 Facade

    - 동일 시그니처로 위임
    - 일부 값만 조정/하드코딩
    """

    def __init__(self):
        self._client: Optional[GraphMailClient] = None
        self._initialized = False

    async def initialize(self, user_email: Optional[str] = None, access_token: Optional[str] = None) -> bool:
        """서비스 초기화"""
        if self._initialized:
            return True

        self._client = GraphMailClient(
            user_email=user_email,
            access_token=access_token
        )

        if await self._client.initialize(user_email):
            self._initialized = True
            return True
        return False

    def _ensure_initialized(self):
        """초기화 확인"""
        if not self._initialized or not self._client:
            raise RuntimeError("MailService not initialized. Call initialize() first.")

    @mcp_service(
        tool_name="handler_mail_list",      # 필수: MCP Tool 이름
        server_name="outlook",                # 필수: 서버 식별자
        service_name="query_mail_list",       # 필수: 메서드명
        category="outlook_mail",              # 권장: 카테고리
        tags=["query", "search"],             # 권장: 태그
        priority=5,                           # 선택: 우선순위 (1-10)
        description="메일 리스트 조회 기능"           # 필수: 기능 설명
    )
    async def query_mail_list(
        self,
        query_method: QueryMethod = QueryMethod.FILTER,
        filter_params: Optional[FilterParams] = None,
        exclude_params: Optional[ExcludeParams] = None,
        select_params: Optional[SelectParams] = None,
        client_filter: Optional[ExcludeParams] = None,
        search_term: Optional[str] = None,
        url: Optional[str] = None,
        top: int = 50,
        order_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """메일 조회 - GraphMailClient.build_and_fetch 위임"""
        self._ensure_initialized()

        # 기본 정렬 순서
        if order_by is None:
            order_by = "receivedDateTime desc"

        return await self._client.build_and_fetch(
            query_method=query_method,
            filter_params=filter_params,
            exclude_params=exclude_params,
            select_params=select_params,
            client_filter=client_filter,
            search_term=search_term,
            url=url,
            top=top,
            order_by=order_by
        )

    @mcp_service(
        tool_name="handler_mail_fetch_and_process",      # 필수: MCP Tool 이름
        server_name="outlook",                            # 필수: 서버 식별자
        service_name="fetch_and_process",                 # 필수: 메서드명
        category="outlook_mail",                          # 권장: 카테고리
        tags=["query", "process", "download", "convert"], # 권장: 태그
        priority=5,                                       # 선택: 우선순위 (1-10)
        description="메일 조회 및 처리 기능"                  # 필수: 기능 설명
    )
    async def fetch_and_process(
        self,
        query_method: QueryMethod = QueryMethod.FILTER,
        filter_params: Optional[FilterParams] = None,
        exclude_params: Optional[ExcludeParams] = None,
        select_params: Optional[SelectParams] = None,
        client_filter: Optional[ExcludeParams] = None,
        search_term: Optional[str] = None,
        url: Optional[str] = None,
        top: int = 50,
        order_by: Optional[str] = None,
        processing_mode: ProcessingMode = ProcessingMode.FETCH_ONLY,
        mail_storage: MailStorageOption = MailStorageOption.MEMORY,
        attachment_handling: AttachmentOption = AttachmentOption.SKIP,
        output_format: OutputFormat = OutputFormat.COMBINED,
        save_directory: Optional[str] = None,
        return_on_error: bool = True
    ) -> Dict[str, Any]:
        """메일 조회 및 처리 - GraphMailClient.fetch_and_process 위임"""
        self._ensure_initialized()

        # 기본 정렬 순서
        if order_by is None:
            order_by = "receivedDateTime desc"

        return await self._client.fetch_and_process(
            query_method=query_method,
            filter_params=filter_params,
            exclude_params=exclude_params,
            select_params=select_params,
            client_filter=client_filter,
            search_term=search_term,
            url=url,
            top=top,
            order_by=order_by,
            processing_mode=processing_mode,
            mail_storage=mail_storage,
            attachment_handling=attachment_handling,
            output_format=output_format,
            save_directory=save_directory,
            return_on_error=return_on_error
        )
    @mcp_service(
        tool_name="handler_mail_fetch_filter",       # 필수: MCP Tool 이름
        server_name="outlook",                       # 필수: 서버 식별자
        service_name="fetch_filter",                 # 필수: 메서드명
        category="outlook_mail",                     # 권장: 카테고리
        tags=["query", "filter"],                    # 권장: 태그
        priority=5,                                  # 선택: 우선순위 (1-10)
        description="필터 방식 메일 조회 기능"           # 필수: 기능 설명
    )
    async def fetch_filter(
        self,
        filter_params: Optional[FilterParams] = None,
        exclude_params: Optional[ExcludeParams] = None,
        select_params: Optional[SelectParams] = None,
        top: int = 50
    ) -> Dict[str, Any]:
        """필터 방식 메일 조회 - query_method 고정"""
        return await self.build_and_fetch(
            query_method=QueryMethod.FILTER,
            filter_params=filter_params,
            exclude_params=exclude_params,
            select_params=select_params,
            top=top
        )
    @mcp_service(
        tool_name="handler_mail_fetch_search",       # 필수: MCP Tool 이름
        server_name="outlook",                       # 필수: 서버 식별자
        service_name="fetch_search",                 # 필수: 메서드명
        category="outlook_mail",                     # 권장: 카테고리
        tags=["query", "search"],                    # 권장: 태그
        priority=5,                                  # 선택: 우선순위 (1-10)
        description="검색 방식 메일 조회 기능"           # 필수: 기능 설명
    )
    async def fetch_search(
        self,
        search_term: str,
        select_params: Optional[SelectParams] = None,
        top: int = 50
    ) -> Dict[str, Any]:
        """검색 방식 메일 조회 - query_method 고정"""
        return await self.build_and_fetch(
            query_method=QueryMethod.SEARCH,
            search_term=search_term,
            select_params=select_params,
            top=top
        )

    @mcp_service(
        tool_name="handler_mail_fetch_url",          # 필수: MCP Tool 이름
        server_name="outlook",                        # 필수: 서버 식별자
        service_name="fetch_url",                     # 필수: 메서드명
        category="outlook_mail",                      # 권장: 카테고리
        tags=["query", "url"],                        # 권장: 태그
        priority=5,                                   # 선택: 우선순위 (1-10)
        description="URL 방식 메일 조회 기능"            # 필수: 기능 설명
    )
    async def fetch_url(
        self,
        url: str,
        top: int = 50
    ) -> Dict[str, Any]:
        """URL 방식 메일 조회 - query_method 고정"""
        return await self.build_and_fetch(
            query_method=QueryMethod.URL,
            url=url,
            top=top
        )

    @mcp_service(
        tool_name="handler_mail_process_with_download",  # 필수: MCP Tool 이름
        server_name="outlook",                            # 필수: 서버 식별자
        service_name="process_with_download",             # 필수: 메서드명
        category="outlook_mail",                          # 권장: 카테고리
        tags=["query", "process", "download"],            # 권장: 태그
        priority=5,                                       # 선택: 우선순위 (1-10)
        description="첨부파일 다운로드 포함 메일 처리 기능"     # 필수: 기능 설명
    )    
    async def process_with_download(
        self,
        filter_params: Optional[FilterParams] = None,
        search_term: Optional[str] = None,
        top: int = 50,
        save_directory: Optional[str] = None
    ) -> Dict[str, Any]:
        """첨부파일 다운로드 포함 처리 - processing_mode, attachment_handling 고정"""
        query_method = QueryMethod.SEARCH if search_term else QueryMethod.FILTER

        return await self.fetch_and_process(
            query_method=query_method,
            filter_params=filter_params,
            search_term=search_term,
            top=top,
            processing_mode=ProcessingMode.FETCH_AND_DOWNLOAD,
            attachment_handling=AttachmentOption.DOWNLOAD_ONLY,
            save_directory=save_directory
        )

    @mcp_service(
        tool_name="handler_mail_process_with_convert",    # 필수: MCP Tool 이름
        server_name="outlook",                            # 필수: 서버 식별자
        service_name="process_with_convert",              # 필수: 메서드명
        category="outlook_mail",                          # 권장: 카테고리
        tags=["query", "process", "convert"],             # 권장: 태그
        priority=5,                                       # 선택: 우선순위 (1-10)
        description="첨부파일 변환 포함 메일 처리 기능"        # 필수: 기능 설명
    )
    async def process_with_convert(
        self,
        filter_params: Optional[FilterParams] = None,
        search_term: Optional[str] = None,
        top: int = 50,
        save_directory: Optional[str] = None
    ) -> Dict[str, Any]:
        """첨부파일 변환 포함 처리 - processing_mode, attachment_handling 고정"""
        query_method = QueryMethod.SEARCH if search_term else QueryMethod.FILTER

        return await self.fetch_and_process(
            query_method=query_method,
            filter_params=filter_params,
            search_term=search_term,
            top=top,
            processing_mode=ProcessingMode.FETCH_AND_CONVERT,
            attachment_handling=AttachmentOption.DOWNLOAD_CONVERT,
            save_directory=save_directory
        )

    def format_results(self, results: Dict[str, Any], verbose: bool = False) -> str:
        """결과 포맷팅 위임"""
        self._ensure_initialized()
        return self._client.format_results(results, verbose)

    async def close(self):
        """리소스 정리"""
        if self._client:
            await self._client.close()
        self._initialized = False


# 싱글톤
_mail_service_instance: Optional[MailService] = None


async def get_mail_service(
    user_email: Optional[str] = None,
    access_token: Optional[str] = None,
    force_new: bool = False
) -> MailService:
    """MailService 싱글톤 인스턴스 반환"""
    global _mail_service_instance

    if force_new and _mail_service_instance:
        await _mail_service_instance.close()
        _mail_service_instance = None

    if _mail_service_instance is None:
        _mail_service_instance = MailService()
        await _mail_service_instance.initialize(user_email, access_token)

    return _mail_service_instance
