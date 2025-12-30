"""
Mail Service - GraphMailClient Facade
인자를 그대로 위임하고, 필요시 일부 값만 조정하는 서비스 레이어
"""
from typing import Dict, Any, Optional, List
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
from outlook_types import FilterParams, ExcludeParams, SelectParams, build_filter_query, build_select_query

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
        user_email: str,
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
            user_email=user_email,
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
        user_email: str,
        filter_params: Optional[FilterParams] = None,
        exclude_params: Optional[ExcludeParams] = None,
        select_params: Optional[SelectParams] = None,
        top: int = 50
    ) -> Dict[str, Any]:
        """필터 방식 메일 조회 - query_method 고정"""
        self._ensure_initialized()
        return await self._client.build_and_fetch(
            user_email=user_email,
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
        user_email: str,
        search_term: str,
        select_params: Optional[SelectParams] = None,
        top: int = 50
    ) -> Dict[str, Any]:
        """검색 방식 메일 조회 - query_method 고정"""
        self._ensure_initialized()
        return await self._client.build_and_fetch(
            user_email=user_email,
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
        user_email: str,
        url: str,
        filter_params: Optional[FilterParams] = None,
        select_params: Optional[SelectParams] = None,
        client_filter: Optional[ExcludeParams] = None,
        top: int = 50
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
            user_email=user_email,
            query_method=QueryMethod.URL,
            url=final_url,
            client_filter=client_filter,
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
        user_email: str,
        filter_params: Optional[FilterParams] = None,
        search_term: Optional[str] = None,
        top: int = 50,
        save_directory: Optional[str] = None
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
        user_email: str,
        filter_params: Optional[FilterParams] = None,
        search_term: Optional[str] = None,
        top: int = 50,
        save_directory: Optional[str] = None
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
            attachment_handling=AttachmentOption.DOWNLOAD_CONVERT,
            save_directory=save_directory
        )

    @mcp_service(
        tool_name="handler_mail_batch_and_process",  # 필수: MCP Tool 이름
        server_name="outlook",                        # 필수: 서버 식별자
        service_name="batch_and_process",             # 필수: 메서드명
        category="outlook_mail",                      # 권장: 카테고리
        tags=["batch", "process", "id"],              # 권장: 태그
        priority=5,                                   # 선택: 우선순위 (1-10)
        description="메일 ID 배치 조회 및 처리 기능"        # 필수: 기능 설명
    )
    async def batch_and_process(
        self,
        user_email: str,
        message_ids: List[str],
        select_params: Optional[SelectParams] = None,
        processing_mode: ProcessingMode = ProcessingMode.FETCH_ONLY,
        mail_storage: MailStorageOption = MailStorageOption.MEMORY,
        attachment_handling: AttachmentOption = AttachmentOption.SKIP,
        output_format: OutputFormat = OutputFormat.COMBINED,
        save_directory: Optional[str] = None,
        return_on_error: bool = True
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
            return_on_error=return_on_error
        )

    @mcp_service(
        tool_name="handler_mail_batch_fetch",         # 필수: MCP Tool 이름
        server_name="outlook",                        # 필수: 서버 식별자
        service_name="batch_and_fetch",               # 필수: 메서드명
        category="outlook_mail",                      # 권장: 카테고리
        tags=["batch", "query", "id"],                # 권장: 태그
        priority=5,                                   # 선택: 우선순위 (1-10)
        description="메일 ID 배치 조회 기능"             # 필수: 기능 설명
    )
    async def batch_and_fetch(
        self,
        user_email: str,
        message_ids: List[str],
        select_params: Optional[SelectParams] = None
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
            user_email=user_email,
            message_ids=message_ids,
            select_params=select_params
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


# 테스트 코드: 최근 일주일간 메일 조회
async def test_fetch_recent_week_mails():
    """최근 일주일간 받은 메일 조회 테스트"""
    import asyncio
    from datetime import datetime, timedelta

    # MailService 인스턴스 생성
    service = MailService()

    try:
        # 서비스 초기화
        print("서비스 초기화 중...")
        if not await service.initialize():
            print("서비스 초기화 실패")
            return

        # 일주일 전 날짜 계산 (ISO 8601 형식)
        one_week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%dT00:00:00Z')

        # 사용자 이메일 (실제 사용 시 적절한 이메일로 변경 필요)
        user_email = "your-email@example.com"  # 실제 이메일로 변경하세요

        # URL 방식으로 최근 일주일간 메일 조회
        # Microsoft Graph API URL 형식
        base_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages"

        # FilterParams를 사용하여 날짜 필터 적용
        filter_params = FilterParams(
            receivedDateTime_ge=one_week_ago  # 일주일 전 이후로 받은 메일
        )

        # SelectParams로 필요한 필드만 선택
        select_params = SelectParams(
            subject=True,
            from_=True,
            receivedDateTime=True,
            bodyPreview=True,
            hasAttachments=True
        )

        print(f"\n최근 일주일간 메일 조회 중... (from {one_week_ago})")
        print("=" * 60)

        # fetch_url 메서드를 사용하여 메일 조회
        results = await service.fetch_url(
            user_email=user_email,
            url=base_url,
            filter_params=filter_params,
            select_params=select_params,
            top=20  # 최대 20개까지만 조회
        )

        # 결과 출력
        if results.get("success"):
            mail_count = results.get("total_count", 0)
            mails = results.get("mails", [])

            print(f"\n총 {mail_count}개의 메일을 찾았습니다.")
            print("=" * 60)

            for idx, mail in enumerate(mails, 1):
                print(f"\n[메일 {idx}]")
                print(f"제목: {mail.get('subject', 'N/A')}")
                print(f"보낸 사람: {mail.get('from', {}).get('emailAddress', {}).get('address', 'N/A')}")
                print(f"받은 시간: {mail.get('receivedDateTime', 'N/A')}")
                print(f"첨부파일: {'있음' if mail.get('hasAttachments') else '없음'}")

                # 본문 미리보기 (첫 100자만)
                body_preview = mail.get('bodyPreview', '')
                if body_preview:
                    print(f"내용 미리보기: {body_preview[:100]}...")
                print("-" * 40)
        else:
            error_msg = results.get("error", "알 수 없는 오류")
            print(f"메일 조회 실패: {error_msg}")

    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # 리소스 정리
        await service.close()
        print("\n서비스 종료 완료")


# 실행 예제
if __name__ == "__main__":
    import asyncio

    # 비동기 함수 실행
    asyncio.run(test_fetch_recent_week_mails())

