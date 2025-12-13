"""
Graph Mail Client - 통합 메일 처리 클라이언트
쿼리, 메일 처리, 첨부파일 관리를 통합하는 상위 클래스
"""
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum

from graph_mail_query import GraphMailQuery
from mail_processor_handler import MailProcessorHandler, ProcessingOptions, MailStorageOption, AttachmentOption, OutputFormat
from attachment_handler import AttachmentHandler
from graph_types import FilterParams, ExcludeParams, SelectParams


class QueryMethod(Enum):
    """쿼리 방법 열거형"""
    FILTER = "filter"      # 필터 기반 쿼리
    SEARCH = "search"      # 검색어 기반 쿼리
    URL = "url"           # 직접 URL 제공


class ProcessingMode(Enum):
    """처리 모드 열거형"""
    FETCH_ONLY = "fetch_only"              # 메일만 가져오기
    FETCH_AND_DOWNLOAD = "fetch_download"   # 메일 + 첨부파일 다운로드
    FETCH_AND_CONVERT = "fetch_convert"     # 메일 + 첨부파일 변환
    FULL_PROCESS = "full_process"          # 전체 처리 (저장, 변환 등)


class GraphMailClient:
    """
    Graph API 메일 통합 클라이언트

    메일 쿼리부터 결과 처리, 첨부파일 관리까지 통합 관리
    """

    def __init__(self, user_email: Optional[str] = None, access_token: Optional[str] = None):
        """
        초기화

        Args:
            user_email: 사용자 이메일
            access_token: 액세스 토큰 (선택사항)
        """
        self.user_email = user_email
        self.access_token = access_token
        self.mail_query: Optional[GraphMailQuery] = None
        self.mail_processor: Optional[MailProcessorHandler] = None
        self.attachment_handler: Optional[AttachmentHandler] = None
        self._initialized = False

    async def initialize(self) -> bool:
        """
        컴포넌트 초기화

        Returns:
            초기화 성공 여부
        """
        try:
            # GraphMailQuery 초기화
            self.mail_query = GraphMailQuery(
                user_email=self.user_email,
                access_token=self.access_token
            )

            if not await self.mail_query.initialize():
                print("❌ Failed to initialize GraphMailQuery")
                return False

            # 액세스 토큰 가져오기
            if not self.access_token:
                self.access_token = self.mail_query.access_token

            # MailProcessorHandler 초기화
            self.mail_processor = MailProcessorHandler(self.access_token)
            if not await self.mail_processor.initialize():
                print("❌ Failed to initialize MailProcessorHandler")
                return False

            # AttachmentHandler 초기화
            self.attachment_handler = AttachmentHandler(self.access_token)

            self._initialized = True
            return True

        except Exception as e:
            print(f"❌ Initialization error: {str(e)}")
            return False

    def _ensure_initialized(self):
        """초기화 확인"""
        if not self._initialized:
            raise Exception("GraphMailClient not initialized. Call initialize() first.")

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
                             order_by: Optional[str] = None) -> Dict[str, Any]:
        """
        쿼리를 빌드하고 메일을 가져오기

        Args:
            query_method: 쿼리 방법 (FILTER, SEARCH, URL)
            filter_params: 필터 파라미터 (FILTER 방식)
            exclude_params: 제외 파라미터 (FILTER 방식)
            select_params: 선택 필드 (FILTER, SEARCH 방식)
            client_filter: 클라이언트 필터 (모든 방식)
            search_term: 검색어 (SEARCH 방식)
            url: 직접 URL (URL 방식)
            top: 최대 결과 수
            order_by: 정렬 순서

        Returns:
            쿼리 결과 (에러 정보 포함)
        """
        self._ensure_initialized()

        try:
            # 쿼리 방법에 따라 실행
            if query_method == QueryMethod.FILTER:
                if not filter_params and not exclude_params:
                    return {
                        "error": "No filter or exclude parameters provided",
                        "status": "error",
                        "value": []
                    }

                result = await self.mail_query.query_filter(
                    filter=filter_params or {},
                    exclude=exclude_params,
                    select=select_params,
                    client_filter=client_filter,
                    top=top,
                    orderby=order_by
                )

            elif query_method == QueryMethod.SEARCH:
                if not search_term:
                    return {
                        "error": "No search term provided",
                        "status": "error",
                        "value": []
                    }

                result = await self.mail_query.query_search(
                    search=search_term,
                    client_filter=client_filter,
                    select=select_params,
                    top=top,
                    orderby=order_by
                )

            elif query_method == QueryMethod.URL:
                if not url:
                    return {
                        "error": "No URL provided",
                        "status": "error",
                        "value": []
                    }

                result = await self.mail_query.query_url(
                    url=url,
                    top=top,
                    client_filter=client_filter
                )

            else:
                return {
                    "error": f"Unknown query method: {query_method}",
                    "status": "error",
                    "value": []
                }

            # 결과에 쿼리 방법 추가
            result['query_method'] = query_method.value
            return result

        except Exception as e:
            return {
                "error": str(e),
                "status": "error",
                "value": [],
                "query_method": query_method.value
            }

    async def fetch_and_process(self,
                               # 쿼리 파라미터
                               query_method: QueryMethod = QueryMethod.FILTER,
                               filter_params: Optional[FilterParams] = None,
                               exclude_params: Optional[ExcludeParams] = None,
                               select_params: Optional[SelectParams] = None,
                               client_filter: Optional[ExcludeParams] = None,
                               search_term: Optional[str] = None,
                               url: Optional[str] = None,
                               top: int = 50,
                               order_by: Optional[str] = None,
                               # 처리 파라미터
                               processing_mode: ProcessingMode = ProcessingMode.FETCH_ONLY,
                               mail_storage: MailStorageOption = MailStorageOption.MEMORY,
                               attachment_handling: AttachmentOption = AttachmentOption.SKIP,
                               output_format: OutputFormat = OutputFormat.COMBINED,
                               save_directory: Optional[str] = None,
                               # 추가 옵션
                               return_on_error: bool = True) -> Dict[str, Any]:
        """
        메일을 가져오고 처리하는 통합 메서드

        Args:
            쿼리 관련 파라미터는 build_and_fetch와 동일
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

        # 1. 메일 가져오기
        print(f"\n📧 Fetching emails using {query_method.value} method...")
        result = await self.build_and_fetch(
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

        # 2. 에러 체크
        if result.get('has_errors'):
            print(f"⚠️  Query completed with errors: {len(result.get('errors', []))} errors")
            if return_on_error:
                return {
                    "status": "error",
                    "error": "Query failed with errors",
                    "errors": result.get('errors', []),
                    "partial_results": result.get('value', []),
                    "query_method": query_method.value
                }

        if result.get('error'):
            print(f"❌ Query failed: {result['error']}")
            return result

        # 3. 결과 확인
        emails = result.get('value', [])
        if not emails:
            print("ℹ️  No emails found")
            return {
                "status": "success",
                "message": "No emails found",
                "value": [],
                "processed_count": 0,
                "query_method": query_method.value
            }

        print(f"✅ Found {len(emails)} email(s)")

        # 4. 처리 모드에 따라 처리
        if processing_mode == ProcessingMode.FETCH_ONLY:
            # 메일만 가져오기
            return {
                "status": "success",
                "value": emails,
                "total": len(emails),
                "processing_mode": processing_mode.value,
                "query_method": query_method.value
            }

        # 5. 추가 처리가 필요한 경우
        print(f"\n🔧 Processing emails with mode: {processing_mode.value}")

        # ProcessingOptions 생성
        processing_options = ProcessingOptions(
            mail_storage=mail_storage,
            attachment_handling=attachment_handling,
            output_format=output_format,
            save_directory=save_directory
        )

        # 처리 실행
        try:
            processed_result = await self.mail_processor.process_mail(
                mail_data=result,
                options=processing_options
            )

            # 처리 정보 추가
            processed_result['processing_mode'] = processing_mode.value
            processed_result['query_method'] = query_method.value
            processed_result['original_count'] = len(emails)

            # 처리 모드별 추가 정보
            if processing_mode == ProcessingMode.FETCH_AND_DOWNLOAD:
                if processed_result.get('attachments'):
                    processed_result['downloaded_count'] = len(processed_result['attachments'])
                    print(f"📎 Downloaded {processed_result['downloaded_count']} attachments")

            elif processing_mode == ProcessingMode.FETCH_AND_CONVERT:
                if processed_result.get('converted_files'):
                    processed_result['converted_count'] = len(processed_result['converted_files'])
                    print(f"🔄 Converted {processed_result['converted_count']} files")

            print(f"✅ Processing completed successfully")
            return processed_result

        except Exception as e:
            print(f"❌ Processing failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "value": emails,  # 원본 메일은 반환
                "processing_mode": processing_mode.value,
                "query_method": query_method.value
            }

    async def quick_search(self,
                          keyword: str,
                          max_results: int = 50,
                          process_attachments: bool = False) -> Dict[str, Any]:
        """
        빠른 검색 헬퍼 메서드

        Args:
            keyword: 검색어
            max_results: 최대 결과 수
            process_attachments: 첨부파일 처리 여부

        Returns:
            검색 결과
        """
        processing_mode = ProcessingMode.FETCH_AND_DOWNLOAD if process_attachments else ProcessingMode.FETCH_ONLY
        attachment_handling = AttachmentOption.DOWNLOAD_ONLY if process_attachments else AttachmentOption.SKIP

        return await self.fetch_and_process(
            query_method=QueryMethod.SEARCH,
            search_term=keyword,
            top=max_results,
            processing_mode=processing_mode,
            attachment_handling=attachment_handling
        )

    async def get_attachments_from_sender(self,
                                         sender_email: str,
                                         days_back: int = 30,
                                         download: bool = True,
                                         convert: bool = False) -> Dict[str, Any]:
        """
        특정 발신자의 첨부파일 가져오기

        Args:
            sender_email: 발신자 이메일
            days_back: 며칠 전까지
            download: 다운로드 여부
            convert: 변환 여부

        Returns:
            첨부파일 정보
        """
        # 필터 설정
        filter_params: FilterParams = {
            'from_address': sender_email,
            'has_attachments': True,
            'received_date_from': (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00Z")
        }

        # 처리 모드 설정
        if convert:
            processing_mode = ProcessingMode.FETCH_AND_CONVERT
            attachment_handling = AttachmentOption.DOWNLOAD_CONVERT
        elif download:
            processing_mode = ProcessingMode.FETCH_AND_DOWNLOAD
            attachment_handling = AttachmentOption.DOWNLOAD_ONLY
        else:
            processing_mode = ProcessingMode.FETCH_ONLY
            attachment_handling = AttachmentOption.SKIP

        return await self.fetch_and_process(
            query_method=QueryMethod.FILTER,
            filter_params=filter_params,
            top=100,
            order_by="receivedDateTime desc",
            processing_mode=processing_mode,
            attachment_handling=attachment_handling,
            save_directory=f"attachments/{sender_email.split('@')[0]}"
        )

    def format_results(self, results: Dict[str, Any], verbose: bool = False) -> str:
        """
        결과 포맷팅

        Args:
            results: 처리 결과
            verbose: 상세 출력 여부

        Returns:
            포맷된 문자열
        """
        output = []
        output.append("\n" + "="*80)

        # 상태 확인
        status = results.get('status', 'unknown')
        if status == 'error':
            output.append(f"❌ Error: {results.get('error', 'Unknown error')}")
            if results.get('errors'):
                output.append(f"   Details: {len(results['errors'])} errors occurred")
            return "\n".join(output)

        # 메일 정보
        emails = results.get('value', [])
        output.append(f"📧 Emails: {len(emails)}")

        # 처리 정보
        if results.get('processing_mode'):
            output.append(f"🔧 Processing Mode: {results['processing_mode']}")

        # 첨부파일 정보
        if results.get('downloaded_count'):
            output.append(f"📎 Downloaded Attachments: {results['downloaded_count']}")
        if results.get('converted_count'):
            output.append(f"🔄 Converted Files: {results['converted_count']}")

        # 필터링 정보
        if results.get('client_filtered'):
            output.append(f"🔍 Client Filtered: {results.get('filtered_count', 0)} items")

        # 메일 목록 (verbose 모드)
        if verbose and emails:
            output.append("\n" + "-"*40)
            for idx, email in enumerate(emails[:10], 1):  # 최대 10개만
                subject = email.get('subject', 'No Subject')
                from_addr = email.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')
                output.append(f"{idx}. {subject[:50]}")
                output.append(f"   From: {from_addr}")

        output.append("="*80)
        return "\n".join(output)

    async def close(self):
        """리소스 정리"""
        if self.mail_query:
            await self.mail_query.close()
        if self.mail_processor:
            await self.mail_processor.close()


# 사용 예제
async def example_usage():
    """GraphMailClient 사용 예제"""

    # 클라이언트 생성
    client = GraphMailClient(user_email="user@example.com")

    try:
        # 초기화
        if not await client.initialize():
            print("Failed to initialize client")
            return

        # 예제 1: 읽지 않은 메일 가져오기
        print("\n--- Example 1: Get Unread Emails ---")
        unread = await client.get_unread_emails(days_back=7)
        print(client.format_results(unread))

        # 예제 2: 키워드 검색
        print("\n--- Example 2: Search Emails ---")
        search_results = await client.quick_search(
            keyword="project update",
            max_results=20,
            process_attachments=True
        )
        print(client.format_results(search_results, verbose=True))

        # 예제 3: 특정 발신자의 첨부파일 다운로드
        print("\n--- Example 3: Download Attachments ---")
        attachments = await client.get_attachments_from_sender(
            sender_email="boss@company.com",
            days_back=30,
            download=True,
            convert=True
        )
        print(client.format_results(attachments))

        # 예제 4: 복잡한 필터링
        print("\n--- Example 4: Complex Filtering ---")
        complex_result = await client.fetch_and_process(
            query_method=QueryMethod.FILTER,
            filter_params={
                'has_attachments': True,
                'importance': 'high',
                'is_read': False
            },
            exclude_params={
                'exclude_subject_keywords': ['newsletter', 'spam']
            },
            top=50,
            processing_mode=ProcessingMode.FULL_PROCESS,
            mail_storage=MailStorageOption.JSON_FILE,
            attachment_handling=AttachmentOption.DOWNLOAD_CONVERT,
            save_directory="important_emails"
        )
        print(client.format_results(complex_result))

    finally:
        await client.close()


if __name__ == "__main__":
    # 예제 실행
    asyncio.run(example_usage())