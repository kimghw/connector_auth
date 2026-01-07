"""
Mail Service - GraphMailClient Facade
인자를 그대로 위임하고, 필요시 일부 값만 조정하는 서비스 레이어
"""

from typing import Dict, Any, Optional, List, Union

from .graph_mail_client import GraphMailClient, QueryMethod, ProcessingMode
from .outlook_types import (
    FilterParams, ExcludeParams, SelectParams,
    build_filter_query, build_select_query
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


class MailService:
    """
    GraphMailClient의 Facade

    - 동일 시그니처로 위임
    - 일부 값만 조정/하드코딩
    """

    def __init__(self):
        self._client: Optional[GraphMailClient] = None
        self._initialized = False

    async def initialize(self) -> bool:
        """서비스 초기화"""
        if self._initialized:
            return True

        self._client = GraphMailClient()

        if await self._client.initialize():
            self._initialized = True
            return True
        return False

    def _ensure_initialized(self):
        """초기화 확인"""
        if not self._initialized or not self._client:
            raise RuntimeError("MailService not initialized. Call initialize() first.")

    @mcp_service(
        tool_name="handler_mail_list",  # 필수: MCP Tool 이름
        server_name="outlook",  # 필수: 서버 식별자
        service_name="query_mail_list",  # 필수: 메서드명
        category="outlook_mail",  # 권장: 카테고리
        tags=["query", "search"],  # 권장: 태그
        priority=5,  # 선택: 우선순위 (1-10)
        description="메일 리스트 조회 기능",  # 필수: 기능 설명
    )
    async def query_mail_list(
        self,
        user_email: str,
        query_method: QueryMethod = QueryMethod.FILTER,
        filter_params: Optional[FilterParams] = None,
        exclude_params: Optional[ExcludeParams] = None,
        select_params: Optional[SelectParams] = None,
        client_filter: Optional[ExcludeParams] = None,
        search_term: Optional[str] = None,
        url: Optional[str] = None,
        top: int = 50,
        order_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """메일 조회 - GraphMailClient.build_and_fetch 위임"""
        self._ensure_initialized()

        # 기본 정렬 순서
        if order_by is None:
            order_by = "receivedDateTime desc"

        result = await self._client.build_and_fetch(
            user_email=user_email,
            query_method=query_method,
            filter_params=filter_params,
            exclude_params=exclude_params,
            select_params=select_params,
            client_filter=client_filter,
            search_term=search_term,
            url=url,
            top=top,
            order_by=order_by,
        )

        # 반환 형식 변환: value -> emails
        if "value" in result:
            result["emails"] = result.pop("value")
            result["success"] = True
            result["user"] = user_email
            result["method"] = query_method.value

        return result

    @mcp_service(
        tool_name="handler_mail_fetch_and_process",  # 필수: MCP Tool 이름
        server_name="outlook",  # 필수: 서버 식별자
        service_name="fetch_and_process",  # 필수: 메서드명
        category="outlook_mail",  # 권장: 카테고리
        tags=["query", "process", "download", "convert"],  # 권장: 태그
        priority=5,  # 선택: 우선순위 (1-10)
        description="메일 조회 및 처리 기능",  # 필수: 기능 설명
    )
    async def fetch_and_process(
        self,
        user_email: str,
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
        mail_storage: str = "memory",
        attachment_handling: str = "skip",
        output_format: str = "combined",
        save_directory: Optional[str] = None,
        return_on_error: bool = True,
    ) -> Dict[str, Any]:
        """메일 조회 및 처리 - GraphMailClient.fetch_and_process 위임"""
        self._ensure_initialized()

        # 기본 정렬 순서
        if order_by is None:
            order_by = "receivedDateTime desc"

        return await self._client.fetch_and_process(
            user_email=user_email,
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
            return_on_error=return_on_error,
        )

    @mcp_service(
        tool_name="handler_mail_fetch_filter",  # 필수: MCP Tool 이름
        server_name="outlook",  # 필수: 서버 식별자
        service_name="fetch_filter",  # 필수: 메서드명
        category="outlook_mail",  # 권장: 카테고리
        tags=["query", "filter"],  # 권장: 태그
        priority=5,  # 선택: 우선순위 (1-10)
        description="필터 방식 메일 조회 기능",  # 필수: 기능 설명
    )
    async def fetch_filter(
        self,
        user_email: str,
        filter_params: Optional[FilterParams] = None,
        exclude_params: Optional[ExcludeParams] = None,
        select_params: Optional[SelectParams] = None,
        top: int = 50,
    ) -> Dict[str, Any]:
        """필터 방식 메일 조회 - query_method 고정"""
        self._ensure_initialized()
        return await self._client.build_and_fetch(
            user_email=user_email,
            query_method=QueryMethod.FILTER,
            filter_params=filter_params,
            exclude_params=exclude_params,
            select_params=select_params,
            top=top,
        )

    @mcp_service(
        tool_name="handler_mail_fetch_search",  # 필수: MCP Tool 이름
        server_name="outlook",  # 필수: 서버 식별자
        service_name="fetch_search",  # 필수: 메서드명
        category="outlook_mail",  # 권장: 카테고리
        tags=["query", "search"],  # 권장: 태그
        priority=5,  # 선택: 우선순위 (1-10)
        description="검색 방식 메일 조회 기능",  # 필수: 기능 설명
    )
    async def fetch_search(
        self,
        user_email: str,
        search_term: str,
        select_params: Optional[SelectParams] = None,
        client_filter: Optional[ExcludeParams] = None,
        top: int = 50
    ) -> Dict[str, Any]:
        """검색 방식 메일 조회 - query_method 고정"""
        self._ensure_initialized()
        return await self._client.build_and_fetch(
            user_email=user_email,
            query_method=QueryMethod.SEARCH,
            search_term=search_term,
            select_params=select_params,
            client_filter=client_filter,
            top=top,
        )

    @mcp_service(
        tool_name="handler_mail_fetch_url",  # 필수: MCP Tool 이름
        server_name="outlook",  # 필수: 서버 식별자
        service_name="fetch_url",  # 필수: 메서드명
        category="outlook_mail",  # 권장: 카테고리
        tags=["query", "url"],  # 권장: 태그
        priority=5,  # 선택: 우선순위 (1-10)
        description="URL 방식 메일 조회 기능",  # 필수: 기능 설명
    )
    async def fetch_url(
        self,
        user_email: str,
        url: str,
        filter_params: Optional[FilterParams] = None,
        select_params: Optional[SelectParams] = None,
        client_filter: Optional[ExcludeParams] = None,
        top: int = 50,
    ) -> Dict[str, Any]:
        """URL 방식 메일 조회 - query_method 고정"""
        self._ensure_initialized()

        final_url = url

        # filter_params가 있으면 URL에 $filter 추가
        if filter_params:
            filter_query = build_filter_query(filter_params)
            if filter_query:
                separator = "&" if "?" in final_url else "?"
                final_url = f"{final_url}{separator}$filter={filter_query}"

        # select_params가 있으면 URL에 $select 추가
        if select_params:
            select_query = build_select_query(select_params)
            if select_query:
                separator = "&" if "?" in final_url else "?"
                final_url = f"{final_url}{separator}$select={select_query}"

        return await self._client.build_and_fetch(
            user_email=user_email, query_method=QueryMethod.URL, url=final_url, client_filter=client_filter, top=top
        )

    @mcp_service(
        tool_name="handler_mail_process_with_download",  # 필수: MCP Tool 이름
        server_name="outlook",  # 필수: 서버 식별자
        service_name="process_with_download",  # 필수: 메서드명
        category="outlook_mail",  # 권장: 카테고리
        tags=["query", "process", "download"],  # 권장: 태그
        priority=5,  # 선택: 우선순위 (1-10)
        description="첨부파일 다운로드 포함 메일 처리 기능",  # 필수: 기능 설명
    )
    async def process_with_download(
        self,
        user_email: str,
        filter_params: Optional[FilterParams] = None,
        search_term: Optional[str] = None,
        top: int = 50,
        save_directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """첨부파일 다운로드 포함 처리 - processing_mode, attachment_handling 고정"""
        query_method = QueryMethod.SEARCH if search_term else QueryMethod.FILTER

        return await self.fetch_and_process(
            user_email=user_email,
            query_method=query_method,
            filter_params=filter_params,
            search_term=search_term,
            top=top,
            processing_mode=ProcessingMode.FETCH_AND_DOWNLOAD,
            attachment_handling="download",
            save_directory=save_directory,
        )

    @mcp_service(
        tool_name="handler_mail_process_with_convert",  # 필수: MCP Tool 이름
        server_name="outlook",  # 필수: 서버 식별자
        service_name="process_with_convert",  # 필수: 메서드명
        category="outlook_mail",  # 권장: 카테고리
        tags=["query", "process", "convert"],  # 권장: 태그
        priority=5,  # 선택: 우선순위 (1-10)
        description="첨부파일 변환 포함 메일 처리 기능",  # 필수: 기능 설명
    )
    async def process_with_convert(
        self,
        user_email: str,
        filter_params: Optional[FilterParams] = None,
        search_term: Optional[str] = None,
        top: int = 50,
        save_directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """첨부파일 변환 포함 처리 - processing_mode, attachment_handling 고정"""
        query_method = QueryMethod.SEARCH if search_term else QueryMethod.FILTER

        return await self.fetch_and_process(
            user_email=user_email,
            query_method=query_method,
            filter_params=filter_params,
            search_term=search_term,
            top=top,
            processing_mode=ProcessingMode.FETCH_AND_CONVERT,
            attachment_handling="convert",
            save_directory=save_directory,
        )

    @mcp_service(
        tool_name="handler_mail_batch_and_process",  # 필수: MCP Tool 이름
        server_name="outlook",  # 필수: 서버 식별자
        service_name="batch_and_process",  # 필수: 메서드명
        category="outlook_mail",  # 권장: 카테고리
        tags=["batch", "process", "id"],  # 권장: 태그
        priority=5,  # 선택: 우선순위 (1-10)
        description="메일 ID 배치 조회 및 처리 기능",  # 필수: 기능 설명
    )
    async def batch_and_process(
        self,
        user_email: str,
        message_ids: List[str],
        select_params: Optional[SelectParams] = None,
        processing_mode: ProcessingMode = ProcessingMode.FETCH_ONLY,
        mail_storage: str = "memory",
        attachment_handling: str = "skip",
        output_format: str = "combined",
        save_directory: Optional[str] = None,
        return_on_error: bool = True,
    ) -> Dict[str, Any]:
        """
        메일 ID 배치로 조회 + 처리 - GraphMailClient.batch_and_process 위임

        Args:
            user_email: 사용자 이메일
            message_ids: 메일 ID 리스트
            select_params: 선택할 필드
            processing_mode: 처리 모드
            mail_storage: 메일 저장 방식
            attachment_handling: 첨부파일 처리 방식
            output_format: 출력 형식
            save_directory: 저장 디렉토리
            return_on_error: 에러 시 즉시 반환 여부

        Returns:
            처리된 결과
        """
        self._ensure_initialized()

        return await self._client.batch_and_process(
            user_email=user_email,
            message_ids=message_ids,
            select_params=select_params,
            processing_mode=processing_mode,
            mail_storage=mail_storage,
            attachment_handling=attachment_handling,
            output_format=output_format,
            save_directory=save_directory,
            return_on_error=return_on_error,
        )

    @mcp_service(
        tool_name="handler_mail_batch_fetch",  # 필수: MCP Tool 이름
        server_name="outlook",  # 필수: 서버 식별자
        service_name="batch_and_fetch",  # 필수: 메서드명
        category="outlook_mail",  # 권장: 카테고리
        tags=["batch", "query", "id"],  # 권장: 태그
        priority=5,  # 선택: 우선순위 (1-10)
        description="메일 ID 배치 조회 기능",  # 필수: 기능 설명
    )
    async def batch_and_fetch(
        self, user_email: str, message_ids: List[str], select_params: Optional[SelectParams] = None
    ) -> Dict[str, Any]:
        """
        메일 ID 배치로 조회만 수행 - GraphMailClient.batch_and_fetch 위임

        Args:
            user_email: 사용자 이메일
            message_ids: 메일 ID 리스트
            select_params: 선택할 필드

        Returns:
            조회 결과
        """
        self._ensure_initialized()

        return await self._client.batch_and_fetch(
            user_email=user_email, message_ids=message_ids, select_params=select_params
        )

    @mcp_service(
        tool_name="handle_attachments_metadata",  # 필수: MCP Tool 이름
        server_name="outlook",  # 필수: 서버 식별자
        service_name="fetch_attachments_metadata",  # 필수: 메서드명
        category="outlook_mail",  # 권장: 카테고리
        tags=["attachment", "metadata", "batch"],  # 권장: 태그
        priority=5,  # 선택: 우선순위 (1-10)
        description="이도구 호출하기 전에 메일 리스트를 조회해야함. 메일과 첨부파일의 메타데이터만 조회 (다운로드 없음)",  # 필수: 기능 설명
    )
    async def fetch_attachments_metadata(
        self,
        user_email: str,
        message_ids: List[str],
        select_params: Optional[SelectParams] = None,
    ) -> Dict[str, Any]:
        """
        메일과 첨부파일의 메타데이터만 조회 - GraphMailClient.fetch_attachments_metadata 위임

        Args:
            user_email: 사용자 이메일
            message_ids: 메일 ID 리스트
            select_params: 선택할 필드

        Returns:
            메일 및 첨부파일 메타데이터
        """
        self._ensure_initialized()

        return await self._client.fetch_attachments_metadata(
            user_email=user_email,
            message_ids=message_ids,
            select_params=select_params,
        )

    @mcp_service(
        tool_name="handle_download_attachments",  # 필수: MCP Tool 이름
        server_name="outlook",  # 필수: 서버 식별자
        service_name="download_attachments",  # 필수: 메서드명
        category="outlook_mail",  # 권장: 카테고리
        tags=["attachment", "download", "batch"],  # 권장: 태그
        priority=5,  # 선택: 우선순위 (1-10)
        description="첨부파일 다운로드 (메일ID 또는 첨부파일ID 지정)",  # 필수: 기능 설명
    )
    async def download_attachments(
        self,
        user_email: str,
        message_attachment_ids: Union[List[str], List[Dict[str, str]]],
        save_directory: str = "downloads",
        skip_duplicates: bool = True,
        select_params: Optional[SelectParams] = None,
    ) -> Dict[str, Any]:
        """
        첨부파일 다운로드 - GraphMailClient.download_attachments 위임

        Args:
            user_email: 사용자 이메일
            message_attachment_ids:
                - 메일 ID 리스트: ["msg_id1", "msg_id2"] -> 모든 첨부파일 다운로드
                - 첨부파일 ID 쌍: [{"message_id": "...", "attachment_id": "..."}] -> 특정 첨부파일만
            save_directory: 저장 디렉토리
            skip_duplicates: 중복 건너뛰기
            select_params: 선택할 필드

        Returns:
            다운로드 결과
        """
        self._ensure_initialized()

        return await self._client.download_attachments(
            user_email=user_email,
            message_attachment_ids=message_attachment_ids,
            save_directory=save_directory,
            skip_duplicates=skip_duplicates,
            select_params=select_params,
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
