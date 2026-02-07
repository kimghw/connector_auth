"""
Graph Mail Query - 메일 조회 엔트리포인트
인증 처리 및 Graph API 호출을 담당

역할:
    - 인증 처리 (AuthManager 활용)
    - URL로 Graph API 호출
    - 페이지네이션 처리
    - 클라이언트 사이드 필터링

URL 빌드는 graph_mail_url.py에서 담당
"""

import asyncio
import aiohttp
import sys
import os
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if TYPE_CHECKING:
    from core.protocols import TokenProviderProtocol
from .outlook_types import (
    FilterParams,
    ExcludeParams,
    SelectParams,
    build_filter_query,
    build_exclude_query,
    build_select_query,
)
from .graph_mail_url import GraphMailUrlBuilder


class GraphMailQuery:
    """
    Graph API 메일 조회 클래스

    역할:
        - 인증 처리 (TokenProviderProtocol 활용)
        - URL로 Graph API 호출
        - 페이지네이션 처리
        - 클라이언트 사이드 필터링
    """

    def __init__(self, token_provider: Optional["TokenProviderProtocol"] = None):
        """
        Initialize Graph Mail Query

        Args:
            token_provider: 토큰 제공자 (None이면 기본 AuthManager 사용)
        """
        if token_provider is None:
            # 하위 호환성: 기본 AuthManager 사용
            from session.auth_manager import AuthManager
            token_provider = AuthManager()
        self.token_provider = token_provider
        self._url_builder: Optional[GraphMailUrlBuilder] = None

    async def initialize(self) -> bool:
        """
        Lightweight initializer to align with callers that expect async setup
        """
        # No initialization needed - tokens are fetched per-request
        return True

    async def _get_access_token(self, user_email: str) -> Optional[str]:
        """
        Get or refresh access token for a user
        Delegates to TokenProvider which handles caching and refresh

        Args:
            user_email: User email to get token for

        Returns:
            Access token or None if failed
        """
        try:
            # TokenProvider handles all token caching and refresh logic
            access_token = await self.token_provider.validate_and_refresh_token(user_email)

            if not access_token:
                print(f"Failed to get access token for {user_email}")

            return access_token

        except Exception as e:
            print(f"Token retrieval error for {user_email}: {str(e)}")
            return None

    async def _get_auth_url(self, user_email: str) -> Optional[Dict[str, Any]]:
        """
        인증 실패 시 로그인 URL을 생성하여 반환

        Args:
            user_email: 사용자 이메일

        Returns:
            auth_required 응답 dict 또는 None
        """
        if hasattr(self.token_provider, 'get_auth_url_for_login'):
            return await self.token_provider.get_auth_url_for_login(user_email)
        return None

    def _get_url_builder(self, user_email: str) -> GraphMailUrlBuilder:
        """
        URL 빌더 인스턴스 반환 (캐싱)

        Args:
            user_email: 사용자 이메일

        Returns:
            GraphMailUrlBuilder 인스턴스
        """
        if self._url_builder is None or self._url_builder.user_email != user_email:
            self._url_builder = GraphMailUrlBuilder(user_email)
        return self._url_builder

    def _build_query_url(
        self,
        user_email: str,
        filter_query: Optional[str] = None,
        select_fields: Optional[List[str]] = None,
        order_by: Optional[str] = None,
    ) -> str:
        """
        Build complete query URL with parameters

        Args:
            user_email: User email for building URL
            filter_query: Filter query string
            select_fields: Fields to select
            order_by: Sort order

        Returns:
            Complete URL with query parameters
        """
        url_builder = self._get_url_builder(user_email)
        return url_builder.build_filter_url(
            filter_query=filter_query,
            select_fields=select_fields,
            order_by=order_by,
        )

    async def query_filter(
        self,
        user_email: str,
        filter: FilterParams,
        exclude: Optional[ExcludeParams] = None,
        select: Optional[SelectParams] = None,
        client_filter: Optional[ExcludeParams] = None,
        top: int = 450,
        orderby: Optional[str] = None,
    ) -> Dict[str, Any]:

        # Get access token for the user
        access_token = await self._get_access_token(user_email)
        if not access_token:
            auth_response = await self._get_auth_url(user_email)
            if auth_response:
                return auth_response
            raise Exception(f"Failed to get access token for {user_email}")

        # Build filter parts using graph_types helper functions
        query_parts = []

        # Add filter query
        if filter:
            filter_query = build_filter_query(filter)
            if filter_query:
                query_parts.append(filter_query)

        # Add exclude query to API filter
        if exclude:
            exclude_query = build_exclude_query(exclude)
            if exclude_query:
                query_parts.append(exclude_query)

        # Combine filter and exclude with AND
        combined_filter = " and ".join(query_parts) if query_parts else None

        # Get select fields (새 SelectParams 구조에 맞게 처리)
        select_fields = None
        if select:
            if isinstance(select, SelectParams):
                select_fields = select.get_selected_fields()
            elif isinstance(select, dict):
                # Dict인 경우 build_select_query 사용
                select_query = build_select_query(select)
                select_fields = select_query.split(",") if select_query else None
            elif isinstance(select, list):
                # 리스트 형태는 그대로 사용 (이미 필드명이 들어 있다고 가정)
                select_fields = select

        # Build final URL
        base_url = self._build_query_url(
            user_email=user_email, filter_query=combined_filter, select_fields=select_fields, order_by=orderby
        )

        # Fetch data with immediate filtering if client_filter is provided
        return await self._fetch_parallel_with_url(user_email, access_token, base_url, top, client_filter)

    def _apply_client_side_filter(self, emails: List[Dict], exclude: ExcludeParams) -> List[Dict]:
        """
        Apply client-side filtering to exclude emails based on ExcludeParams
        Supports all ExcludeParams fields for comprehensive client-side filtering

        Args:
            emails: List of email dictionaries
            exclude: ExcludeParams to apply

        Returns:
            Filtered list of emails
        """
        filtered_emails = []

        for email in emails:
            should_include = True

            # === 발신자 제외 ===
            # exclude_from_address (from 또는 sender 필드) - 단일값/리스트 지원
            # Note: Graph API 응답에서 from이 없으면 sender를 사용
            if exclude.get("exclude_from_address"):
                from_data = email.get("from") or email.get("sender")
                from_addr = from_data.get("emailAddress", {}).get("address", "").lower() if from_data else ""
                exclude_from = exclude.get("exclude_from_address")
                if isinstance(exclude_from, list):
                    if from_addr in [addr.lower() for addr in exclude_from]:
                        should_include = False
                        continue
                elif from_addr == exclude_from.lower():
                    should_include = False
                    continue

            # exclude_sender_address (sender 필드) - 단일값/리스트 지원
            if exclude.get("exclude_sender_address"):
                sender_addr = email.get("sender", {}).get("emailAddress", {}).get("address", "").lower()
                exclude_sender = exclude.get("exclude_sender_address")
                if isinstance(exclude_sender, list):
                    if sender_addr in [addr.lower() for addr in exclude_sender]:
                        should_include = False
                        continue
                elif sender_addr == exclude_sender.lower():
                    should_include = False
                    continue

            # === 키워드 제외 ===
            # exclude_subject_keywords
            if exclude.get("exclude_subject_keywords") and should_include:
                subject = email.get("subject", "").lower()
                for keyword in exclude.get("exclude_subject_keywords"):
                    if keyword.lower() in subject:
                        should_include = False
                        break

            # exclude_body_keywords
            if exclude.get("exclude_body_keywords") and should_include:
                body_content = email.get("body", {}).get("content", "").lower()
                for keyword in exclude.get("exclude_body_keywords"):
                    if keyword.lower() in body_content:
                        should_include = False
                        break

            # exclude_preview_keywords
            if exclude.get("exclude_preview_keywords") and should_include:
                body_preview = email.get("bodyPreview", "").lower()
                for keyword in exclude.get("exclude_preview_keywords"):
                    if keyword.lower() in body_preview:
                        should_include = False
                        break

            # === 속성 제외 ===
            # exclude_importance
            if exclude.get("exclude_importance") and should_include:
                if email.get("importance") == exclude.get("exclude_importance"):
                    should_include = False
                    continue

            # exclude_sensitivity
            if exclude.get("exclude_sensitivity") and should_include:
                if email.get("sensitivity") == exclude.get("exclude_sensitivity"):
                    should_include = False
                    continue

            # exclude_classification (inferenceClassification)
            if exclude.get("exclude_classification") and should_include:
                if email.get("inferenceClassification") == exclude.get("exclude_classification"):
                    should_include = False
                    continue

            # === 상태 제외 ===
            # exclude_read_status
            if exclude.get("exclude_read_status") is not None and should_include:
                if email.get("isRead") == exclude.get("exclude_read_status"):
                    should_include = False
                    continue

            # exclude_draft_status
            if exclude.get("exclude_draft_status") is not None and should_include:
                if email.get("isDraft") == exclude.get("exclude_draft_status"):
                    should_include = False
                    continue

            # exclude_attachment_status
            if exclude.get("exclude_attachment_status") is not None and should_include:
                if email.get("hasAttachments") == exclude.get("exclude_attachment_status"):
                    should_include = False
                    continue

            # exclude_delivery_receipt
            if exclude.get("exclude_delivery_receipt") is not None and should_include:
                if email.get("isDeliveryReceiptRequested") == exclude.get("exclude_delivery_receipt"):
                    should_include = False
                    continue

            # exclude_read_receipt
            if exclude.get("exclude_read_receipt") is not None and should_include:
                if email.get("isReadReceiptRequested") == exclude.get("exclude_read_receipt"):
                    should_include = False
                    continue

            # === 플래그 및 카테고리 제외 ===
            # exclude_flag_status
            if exclude.get("exclude_flag_status") and should_include:
                flag_status = email.get("flag", {}).get("flagStatus")
                if flag_status == exclude.get("exclude_flag_status"):
                    should_include = False
                    continue

            # exclude_categories
            if exclude.get("exclude_categories") and should_include:
                email_categories = email.get("categories", [])
                for cat in exclude.get("exclude_categories"):
                    if cat in email_categories:
                        should_include = False
                        break

            # === ID 제외 ===
            # exclude_id
            if exclude.get("exclude_id") and should_include:
                if email.get("id") == exclude.get("exclude_id"):
                    should_include = False
                    continue

            # exclude_conversation_id
            if exclude.get("exclude_conversation_id") and should_include:
                if email.get("conversationId") == exclude.get("exclude_conversation_id"):
                    should_include = False
                    continue

            # exclude_parent_folder_id
            if exclude.get("exclude_parent_folder_id") and should_include:
                if email.get("parentFolderId") == exclude.get("exclude_parent_folder_id"):
                    should_include = False
                    continue

            if should_include:
                filtered_emails.append(email)

        return filtered_emails

    async def query_url(
        self, user_email: str, url: str, top: int = 450, client_filter: Optional[ExcludeParams] = None
    ) -> Dict[str, Any]:
        """
        Query with pre-built URL

        Args:
            user_email: User email for authentication
            url: Complete Graph API URL with all parameters
            top: Maximum results (default 450)
            client_filter: ExcludeParams for client-side filtering (post-fetch)

        Returns:
            Email query results

        Example:
            url = "https://graph.microsoft.com/v1.0/users/me/messages?$filter=isRead eq false&$top=10"
            result = await query_url("user@example.com", url, top=100)
        """
        # Get access token for the user
        access_token = await self._get_access_token(user_email)
        if not access_token:
            auth_response = await self._get_auth_url(user_email)
            if auth_response:
                return auth_response
            raise Exception(f"Failed to get access token for {user_email}")

        # Fetch data with the provided URL and apply filtering immediately
        return await self._fetch_parallel_with_url(user_email, access_token, url, top, client_filter)

    async def query_search(
        self,
        user_email: str,
        search: str,
        client_filter: Optional[ExcludeParams] = None,
        select: Optional[SelectParams] = None,
        top: int = 250,
        orderby: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Query with keyword search ($search parameter)

        Args:
            user_email: User email for authentication
            search: Search keyword or phrase (e.g., "from:boss@company.com", "subject:meeting")
            client_filter: ExcludeParams for client-side filtering (post-fetch)
            select: SelectParams for field selection
            top: Maximum results (default 250 - Graph API search limit)
            orderby: Sort order

        Returns:
            Email query results

        Example:
            search_term = "from:ceo@company.com OR subject:urgent"
            # SelectParams: 각 필드를 True로 지정
            select_params = SelectParams(
                id=True,
                subject=True,
                from_recipient=True,
                received_date_time=True
            )
            client_filter_params: ExcludeParams = {
                'exclude_subject_keywords': ['newsletter', 'spam']
            }

            await query_search(
                search=search_term,
                select=select_params,
                client_filter=client_filter_params
            )

        Note:
            - Graph API $search has a maximum of 250 results per query
            - $search cannot be combined with $filter
            - Search syntax follows KQL (Keyword Query Language)
        """
        # Get access token for the user
        access_token = await self._get_access_token(user_email)
        if not access_token:
            auth_response = await self._get_auth_url(user_email)
            if auth_response:
                return auth_response
            raise Exception(f"Failed to get access token for {user_email}")

        # Get select fields (새 SelectParams 구조에 맞게 처리)
        select_fields = None
        if select:
            if isinstance(select, SelectParams):
                select_fields = select.get_selected_fields()
            elif isinstance(select, dict):
                # Dict인 경우 build_select_query 사용
                select_query_str = build_select_query(select)
                select_fields = select_query_str.split(",") if select_query_str else None
            elif isinstance(select, list):
                # 리스트 형태는 그대로 사용 (이미 필드명이 들어 있다고 가정)
                select_fields = select

        # Enforce Graph API search limit
        actual_top = min(top, 250)

        # Build search URL using URL builder
        url_builder = self._get_url_builder(user_email)
        base_url = url_builder.build_search_url(
            search_query=search,
            select_fields=select_fields,
            order_by=orderby,
            top=actual_top,
        )

        # 직접 호출 (페이지네이션 없이)
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
                async with session.get(base_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        emails = data.get("value", [])

                        # Apply client-side filtering if provided
                        if client_filter and emails:
                            filtered_emails = self._apply_client_side_filter(emails, client_filter)
                            data["value"] = filtered_emails

                        return {
                            "value": data.get("value", []),
                            "total": len(data.get("value", [])),
                            "@odata.count": len(data.get("value", [])),
                            "request_url": base_url,
                            "search_term": search,
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "value": [],
                            "error": f"Search failed with status {response.status}: {error_text[:200]}",
                            "status": "error",
                        }
        except Exception as e:
            return {"value": [], "error": str(e), "status": "error"}

    async def _fetch_parallel_with_url(
        self,
        user_email: str,
        access_token: str,
        base_url: str,
        total_items: int,
        client_filter: Optional[ExcludeParams] = None,
    ) -> Dict[str, Any]:
        """
        Internal method to fetch with parallel pagination
        Always fetches in pages of 150 items
        Applies client-side filtering immediately as data is received

        Args:
            user_email: User email for context
            access_token: Access token for API calls
            base_url: Base URL without pagination
            total_items: Total items to fetch
            client_filter: Optional client-side filter to apply immediately on fetch

        Returns:
            All fetched and filtered emails
        """
        page_size = 150
        max_concurrent = 3

        # Calculate number of pages (even for small requests)
        num_pages = (total_items + page_size - 1) // page_size

        # For single page requests, still use parallel structure for consistency
        if num_pages == 1:
            print(f"\n📧 Fetching {total_items} emails (single page)")
        else:
            print(f"\n📧 Fetching {total_items} emails in {num_pages} pages ({page_size} per page)")

        tasks = []
        semaphore = asyncio.Semaphore(max_concurrent)

        # Create headers with the provided access token
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

        async def fetch_page(session, url, page_num):
            async with semaphore:
                try:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            emails = data.get("value", [])

                            # Apply client-side filtering immediately if provided
                            if client_filter and emails:
                                filtered_emails = self._apply_client_side_filter(emails, client_filter)
                                data["value"] = filtered_emails
                                print(
                                    f"  ✓ Page {page_num}: Retrieved {len(emails)} emails, kept {len(filtered_emails)} after filtering"
                                )
                            else:
                                print(f"  ✓ Page {page_num}: Retrieved {len(emails)} emails")

                            return data
                        else:
                            print(f"  ✗ Page {page_num}: Error {response.status}")
                            return {"value": []}
                except Exception as e:
                    print(f"  ✗ Page {page_num}: {str(e)}")
                    return {"value": []}

        async with aiohttp.ClientSession() as session:
            start_time = datetime.now()

            for page in range(num_pages):
                skip = page * page_size
                # Always use page_size of 150, except for the last page
                top = min(page_size, total_items - skip)

                separator = "&" if "?" in base_url else "?"
                page_url = f"{base_url}{separator}$top={top}&$skip={skip}"

                tasks.append(fetch_page(session, page_url, page + 1))

            results = await asyncio.gather(*tasks)
            elapsed = (datetime.now() - start_time).total_seconds()

        # Collect all emails and errors
        all_emails = []
        errors = []
        for result in results:
            all_emails.extend(result.get("value", []))
            # Collect error information if present
            if result.get("error"):
                errors.append(result)

        print(f"✅ Fetched {len(all_emails)} emails in {elapsed:.2f}s")
        if errors:
            print(f"⚠️  {len(errors)} page(s) had errors")

        return_data = {
            "value": all_emails,
            "total": len(all_emails),
            "@odata.count": len(all_emails),
            "request_url": base_url,  # Include the built URL
            "pages_requested": num_pages,
            "fetch_time": elapsed,
        }

        # Include error information if any errors occurred
        if errors:
            return_data["errors"] = errors
            return_data["has_errors"] = True

        return return_data

    def format_emails(self, results: Dict[str, Any], verbose: bool = False) -> str:
        """
        Format email results for display

        Args:
            results: Email query results
            verbose: Include body preview

        Returns:
            Formatted string
        """
        emails = results.get("value", [])

        if not emails:
            return "No emails found."

        output = []
        output.append(f"\n{'='*80}")
        output.append(f"Found {len(emails)} email(s)")
        output.append(f"{'='*80}\n")

        for idx, email in enumerate(emails, 1):
            # Parse datetime
            received_dt = email.get("receivedDateTime", "Unknown")
            if received_dt != "Unknown":
                try:
                    dt = datetime.fromisoformat(received_dt.replace("Z", "+00:00"))
                    received_dt = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass

            # Get info
            subject = email.get("subject", "No Subject")
            from_info = email.get("from", {})
            sender_name = from_info.get("emailAddress", {}).get("name", "Unknown")
            sender_email = from_info.get("emailAddress", {}).get("address", "Unknown")
            is_read = email.get("isRead", False)
            has_attachments = email.get("hasAttachments", False)
            importance = email.get("importance", "normal")

            # Format
            read_status = "[READ]" if is_read else "[UNREAD]"
            attach_icon = "📎" if has_attachments else ""
            imp_icon = "❗" if importance == "high" else ""

            output.append(f"[{idx}] {read_status} {imp_icon}{attach_icon} {subject}")
            output.append(f"    From: {sender_name} <{sender_email}>")
            output.append(f"    Date: {received_dt}")

            if verbose and email.get("bodyPreview"):
                preview = email.get("bodyPreview", "")[:150]
                output.append(f"    Preview: {preview}...")

            output.append("")

        return "\n".join(output)

    async def process_with_options(
        self,
        user_email: str,
        mail_data: Dict[str, Any],
        mail_storage: str = "memory",
        attachment_handling: str = "skip",
        output_format: str = "combined",
        save_directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        메일 데이터를 받아서 처리 옵션에 따라 처리

        Args:
            user_email: User email for authentication
            mail_data: 쿼리 결과 (fetch_parallel_with_url의 반환값)
            mail_storage: 메일 저장 방식 ("memory", "text", "json", "database")
            attachment_handling: 첨부파일 처리 ("skip", "download", "convert", "convert_delete")
            output_format: 출력 형식 ("combined", "separated", "structured")
            save_directory: 저장 디렉토리

        Returns:
            처리된 결과
        """
        from .mail_attachment import BatchAttachmentHandler

        # 메일 목록 추출
        if isinstance(mail_data, dict):
            emails = mail_data.get("value", [mail_data])
        else:
            emails = mail_data if isinstance(mail_data, list) else [mail_data]

        # 첨부파일 처리가 필요한 경우
        if attachment_handling in ["download", "convert", "convert_delete"]:
            message_ids = [email.get("id") for email in emails if email.get("id")]
            if message_ids:
                handler = BatchAttachmentHandler(base_directory=save_directory or "downloads")
                attachment_result = await handler.fetch_and_save(
                    user_email=user_email,
                    message_ids=message_ids,
                    skip_duplicates=True,
                )
                return {
                    "status": "success",
                    "value": emails,
                    "total": len(emails),
                    "attachment_result": attachment_result,
                }

        # 첨부파일 처리 없이 메일만 반환
        return {
            "status": "success",
            "value": emails,
            "total": len(emails),
        }

    async def close(self):
        """Clean up resources"""
        if self.token_provider and hasattr(self.token_provider, 'close'):
            await self.token_provider.close()


# Convenience function for quick queries
async def query_emails(
    user_email: str,
    filter_params: Optional[Dict[str, Any]] = None,
    search_term: Optional[str] = None,
    url: Optional[str] = None,
    top: int = 450,
) -> Dict[str, Any]:
    """
    Quick function to query emails

    Args:
        user_email: User email (required)
        filter_params: Filter parameters
        search_term: Search keyword
        url: Pre-built URL
        top: Maximum results

    Returns:
        Email query results
    """
    query = GraphMailQuery()

    if url:
        return await query.query_url(user_email=user_email, url=url, top=top)
    elif search_term:
        return await query.query_search(user_email=user_email, search=search_term, top=top)
    elif filter_params:
        return await query.query_filter(user_email=user_email, filter=FilterParams(**filter_params), top=top)
    else:
        return {"status": "error", "error": "Must provide either url, search_term, or filter_params"}
