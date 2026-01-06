"""
Graph Mail Client - 통합 메일 처리 클라이언트
쿼리, 메일 처리, 첨부파일 관리를 통합하는 상위 클래스
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from .graph_mail_query import GraphMailQuery
from .graph_mail_id_batch import GraphMailIdBatch
from .outlook_types import FilterParams, ExcludeParams, SelectParams


class QueryMethod(Enum):
    """쿼리 방법 열거형"""

    FILTER = "filter"  # 필터 기반 쿼리
    SEARCH = "search"  # 검색어 기반 쿼리
    URL = "url"  # 직접 URL 제공
    BATCH_ID = "batch_id"  # 메일 ID 배치 조회


class ProcessingMode(Enum):
    """처리 모드 열거형"""

    FETCH_ONLY = "fetch_only"  # 메일만 가져오기
    FETCH_AND_DOWNLOAD = "fetch_download"  # 메일 + 첨부파일 다운로드
    FETCH_AND_CONVERT = "fetch_convert"  # 메일 + 첨부파일 변환
    FULL_PROCESS = "full_process"  # 전체 처리 (저장, 변환 등)


class GraphMailClient:
    """
    Graph API 메일 통합 클라이언트

    메일 쿼리부터 결과 처리, 첨부파일 관리까지 통합 관리
    """

    def __init__(self):
        """
        초기화
        """
        self.mail_query: Optional[GraphMailQuery] = None
        self.mail_batch: Optional[GraphMailIdBatch] = None
        self._initialized = False

    async def initialize(self) -> bool:
        """
        컴포넌트 초기화

        Returns:
            초기화 성공 여부
        """
        if self._initialized:
            return True

        try:
            # GraphMailQuery 초기화
            self.mail_query = GraphMailQuery()

            if not await self.mail_query.initialize():
                print("❌ Failed to initialize GraphMailQuery")
                return False

            # GraphMailIdBatch 초기화
            self.mail_batch = GraphMailIdBatch()

            if not await self.mail_batch.initialize():
                print("❌ Failed to initialize GraphMailIdBatch")
                return False

            self._initialized = True
            return True

        except Exception as e:
            print(f"❌ Initialization error: {str(e)}")
            return False

    def _ensure_initialized(self):
        """초기화 확인"""
        if not self._initialized:
            raise Exception("GraphMailClient not initialized. Call initialize() first.")

    async def build_and_fetch(
        self,
        user_email: str,
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
        order_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        쿼리를 빌드하고 메일을 가져오기

        Args:
            user_email: User email for authentication
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
                    return {"error": "No filter or exclude parameters provided", "status": "error", "value": []}

                result = await self.mail_query.query_filter(
                    user_email=user_email,
                    filter=filter_params or {},
                    exclude=exclude_params,
                    select=select_params,
                    client_filter=client_filter,
                    top=top,
                    orderby=order_by,
                )

            elif query_method == QueryMethod.SEARCH:
                if not search_term:
                    return {"error": "No search term provided", "status": "error", "value": []}

                result = await self.mail_query.query_search(
                    user_email=user_email,
                    search=search_term,
                    client_filter=client_filter,
                    select=select_params,
                    top=top,
                    orderby=order_by,
                )

            elif query_method == QueryMethod.URL:
                if not url:
                    return {"error": "No URL provided", "status": "error", "value": []}

                result = await self.mail_query.query_url(
                    user_email=user_email, url=url, top=top, client_filter=client_filter
                )

            else:
                return {"error": f"Unknown query method: {query_method}", "status": "error", "value": []}

            # 결과에 쿼리 방법 추가
            result["query_method"] = query_method.value
            return result

        except Exception as e:
            return {"error": str(e), "status": "error", "value": [], "query_method": query_method.value}

    async def fetch_and_process(
        self,
        user_email: str,
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
        mail_storage: str = "memory",
        attachment_handling: str = "skip",
        output_format: str = "combined",
        save_directory: Optional[str] = None,
        # 추가 옵션
        return_on_error: bool = True,
    ) -> Dict[str, Any]:
        """
        메일을 가져오고 처리하는 통합 메서드

        Args:
            user_email: User email for authentication
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

        # 2. 에러 체크
        if result.get("has_errors"):
            print(f"⚠️  Query completed with errors: {len(result.get('errors', []))} errors")
            if return_on_error:
                return {
                    "status": "error",
                    "error": "Query failed with errors",
                    "errors": result.get("errors", []),
                    "partial_results": result.get("value", []),
                    "query_method": query_method.value,
                }

        if result.get("error"):
            print(f"❌ Query failed: {result['error']}")
            return result

        # 3. 결과 확인
        emails = result.get("value", [])
        if not emails:
            print("ℹ️  No emails found")
            return {
                "status": "success",
                "message": "No emails found",
                "value": [],
                "processed_count": 0,
                "query_method": query_method.value,
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
                "query_method": query_method.value,
            }

        # 5. 추가 처리가 필요한 경우 - GraphAttachmentHandler 사용
        print(f"\n🔧 Processing emails with mode: {processing_mode.value}")

        # 첨부파일 처리가 필요한 경우 GraphAttachmentHandler 사용
        if processing_mode in [ProcessingMode.FETCH_AND_DOWNLOAD, ProcessingMode.FULL_PROCESS]:
            from .graph_mail_attachment import GraphAttachmentHandler

            message_ids = [email.get("id") for email in emails if email.get("id")]
            if message_ids:
                handler = GraphAttachmentHandler(base_directory=save_directory or "downloads")
                try:
                    attachment_result = await handler.fetch_and_save(
                        user_email=user_email,
                        message_ids=message_ids,
                        skip_duplicates=True,
                    )
                    print(f"📎 Processed {attachment_result.get('total_processed', 0)} emails with attachments")
                    return {
                        "status": "success",
                        "value": emails,
                        "total": len(emails),
                        "processing_mode": processing_mode.value,
                        "query_method": query_method.value,
                        "attachment_result": attachment_result,
                    }
                except Exception as e:
                    print(f"⚠️ Attachment processing failed: {e}")
                    return {
                        "status": "partial",
                        "value": emails,
                        "total": len(emails),
                        "processing_mode": processing_mode.value,
                        "query_method": query_method.value,
                        "attachment_error": str(e),
                    }

        # 그 외 모드는 쿼리 결과만 반환
        return {
            "status": "success",
            "value": emails,
            "total": len(emails),
            "processing_mode": processing_mode.value,
            "query_method": query_method.value,
        }

    async def batch_and_fetch(
        self, user_email: str, message_ids: List[str], select_params: Optional[SelectParams] = None
    ) -> Dict[str, Any]:
        """
        메일 ID 배치로 조회만 수행

        Args:
            user_email: 사용자 이메일
            message_ids: 메일 ID 리스트
            select_params: 선택할 필드

        Returns:
            조회 결과
        """
        self._ensure_initialized()

        if not message_ids:
            return {
                "status": "success",
                "value": [],
                "total": 0,
                "message": "No message IDs provided",
                "query_method": QueryMethod.BATCH_ID.value,
            }

        try:
            # 배치 조회 실행
            print(f"\n📧 Fetching {len(message_ids)} emails using batch method...")
            result = await self.mail_batch.batch_fetch_by_ids(
                user_email=user_email, message_ids=message_ids, select_params=select_params
            )

            # 결과 변환 (기존 형식과 일관성 유지)
            if result.get("success"):
                return {
                    "status": "success",
                    "value": result.get("value", []),
                    "total": result.get("total", 0),
                    "requested": result.get("requested", 0),
                    "errors": result.get("errors"),
                    "query_method": QueryMethod.BATCH_ID.value,
                    "batches_processed": result.get("batches_processed", 0),
                }
            else:
                return {
                    "status": "error",
                    "error": result.get("error", "Batch fetch failed"),
                    "value": result.get("value", []),
                    "errors": result.get("errors"),
                    "query_method": QueryMethod.BATCH_ID.value,
                }

        except Exception as e:
            return {"status": "error", "error": str(e), "value": [], "query_method": QueryMethod.BATCH_ID.value}

    async def batch_and_attachment(
        self,
        user_email: str,
        message_ids: List[str],
        select_params: Optional[SelectParams] = None,
        save_directory: str = "downloads",
        skip_duplicates: bool = True,
    ) -> Dict[str, Any]:
        """
        메일 ID로 메일 + 첨부파일 조회 ($expand=attachments)

        Args:
            user_email: 사용자 이메일
            message_ids: 메일 ID 리스트
            select_params: 선택할 필드
            save_directory: 첨부파일 저장 디렉토리
            skip_duplicates: 중복 메일 건너뛰기

        Returns:
            조회 및 저장 결과
        """
        self._ensure_initialized()

        if not message_ids:
            return {
                "status": "success",
                "value": [],
                "total": 0,
                "message": "No message IDs provided",
            }

        try:
            from .graph_mail_attachment import GraphAttachmentHandler
            from .outlook_types import build_select_query

            # SelectParams를 List[str]로 변환
            select_fields = None
            if select_params:
                select_query = build_select_query(select_params)
                select_fields = select_query.split(",") if select_query else None

            print(f"\n📧 Fetching {len(message_ids)} emails with attachments...")
            handler = GraphAttachmentHandler(base_directory=save_directory)
            result = await handler.fetch_and_save(
                user_email=user_email,
                message_ids=message_ids,
                select_fields=select_fields,
                skip_duplicates=skip_duplicates,
            )

            return {
                "status": "success",
                "value": result.get("messages", []),
                "total": result.get("total_processed", 0),
                "attachments_saved": result.get("attachments_saved", 0),
                "skipped": result.get("skipped", 0),
                "errors": result.get("errors"),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "value": []}

    async def batch_and_process(
        self,
        user_email: str,
        message_ids: List[str],
        select_params: Optional[SelectParams] = None,
        # 처리 파라미터
        processing_mode: ProcessingMode = ProcessingMode.FETCH_ONLY,
        mail_storage: str = "memory",
        attachment_handling: str = "skip",
        output_format: str = "combined",
        save_directory: Optional[str] = None,
        return_on_error: bool = True,
    ) -> Dict[str, Any]:
        """
        메일 ID 배치로 조회 + 처리

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

        # 1. 배치로 메일 가져오기
        print(f"\n📧 Fetching {len(message_ids)} emails using batch method...")
        result = await self.batch_and_fetch(user_email=user_email, message_ids=message_ids, select_params=select_params)

        # 2. 에러 체크
        if result.get("status") == "error":
            print(f"❌ Batch fetch failed: {result.get('error')}")
            if return_on_error:
                return result

        # 3. 결과 확인
        emails = result.get("value", [])
        if not emails:
            print("ℹ️  No emails found")
            return {
                "status": "success",
                "message": "No emails found",
                "value": [],
                "processed_count": 0,
                "query_method": QueryMethod.BATCH_ID.value,
            }

        print(f"✅ Found {len(emails)} email(s)")

        # 4. 처리 모드에 따라 처리
        if processing_mode == ProcessingMode.FETCH_ONLY:
            # 메일만 가져오기
            return {
                "status": "success",
                "value": emails,
                "total": len(emails),
                "processed_count": len(emails),
                "query_method": QueryMethod.BATCH_ID.value,
                "processing_mode": processing_mode.value,
            }

        # 5. 처리 옵션 준비
        processing_options = ProcessingOptions(
            mail_storage=mail_storage,
            attachment_handling=attachment_handling,
            output_format=output_format,
            save_directory=save_directory,
        )

        # Get access token for processing
        access_token = await self.mail_query._get_access_token(user_email)
        if not access_token:
            return {
                "status": "error",
                "error": f"Failed to get access token for {user_email}",
                "value": emails,
                "processing_mode": processing_mode.value,
                "query_method": QueryMethod.BATCH_ID.value,
            }

        # 6. 메일 처리
        processor = MailProcessorHandler(user_email, access_token)
        processed_results = []
        errors = []

        for email in emails:
            try:
                # 각 메일 처리
                processed = await processor.process_mail(email)
                processed_results.append(processed)
            except Exception as e:
                errors.append(
                    {"mail_id": email.get("id", "unknown"), "subject": email.get("subject", "unknown"), "error": str(e)}
                )

        # 7. 결과 정리
        return {
            "status": "success" if processed_results else "error",
            "value": processed_results,
            "original_emails": emails,
            "total": len(emails),
            "processed_count": len(processed_results),
            "errors": errors if errors else None,
            "query_method": QueryMethod.BATCH_ID.value,
            "processing_mode": processing_mode.value,
            "mail_storage": mail_storage.value,
            "attachment_handling": attachment_handling.value,
        }

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
        output.append("\n" + "=" * 80)

        # 상태 확인
        status = results.get("status", "unknown")
        if status == "error":
            output.append(f"❌ Error: {results.get('error', 'Unknown error')}")
            if results.get("errors"):
                output.append(f"   Details: {len(results['errors'])} errors occurred")
            return "\n".join(output)

        # 메일 정보
        emails = results.get("value", [])
        output.append(f"📧 Emails: {len(emails)}")

        # 처리 정보
        if results.get("processing_mode"):
            output.append(f"🔧 Processing Mode: {results['processing_mode']}")

        # 첨부파일 정보
        if results.get("downloaded_count"):
            output.append(f"📎 Downloaded Attachments: {results['downloaded_count']}")
        if results.get("converted_count"):
            output.append(f"🔄 Converted Files: {results['converted_count']}")

        # 필터링 정보
        if results.get("client_filtered"):
            output.append(f"🔍 Client Filtered: {results.get('filtered_count', 0)} items")

        # 메일 목록 (verbose 모드)
        if verbose and emails:
            output.append("\n" + "-" * 40)
            for idx, email in enumerate(emails[:10], 1):  # 최대 10개만
                subject = email.get("subject", "No Subject")
                from_addr = email.get("from", {}).get("emailAddress", {}).get("address", "Unknown")
                output.append(f"{idx}. {subject[:50]}")
                output.append(f"   From: {from_addr}")

        output.append("=" * 80)
        return "\n".join(output)

    async def close(self):
        """리소스 정리"""
        if self.mail_query:
            await self.mail_query.close()
        if self.mail_batch:
            await self.mail_batch.close()
