"""
Graph Mail Query - Entry point for mail operations
Combines filter helpers, filter builder, and mail search functionality
"""
import asyncio
import aiohttp
import sys
import os
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph_mail_filter import GraphMailFilter
from graph_mail_search import GraphMailSearch
from graph_filter_helpers import FilterHelpers, quick_filter
from auth.auth_manager import AuthManager
from graph_types import (
    FilterParams, ExcludeParams, SelectParams,
    build_filter_query, build_exclude_query, build_select_query
)


class GraphMailQuery:
    """
    Main entry point for Graph API mail operations
    Handles authentication, filter building, and mail retrieval
    """

    def __init__(self, user_email: Optional[str] = None, access_token: Optional[str] = None):
        """
        Initialize Graph Mail Query

        Args:
            user_email: User email for authentication (optional if token provided)
            access_token: Direct access token (optional if using auth manager)
        """
        self.user_email = user_email
        self.access_token = access_token
        self.mail_search = None
        self.mail_filter = None
        self.auth_manager = None

    async def initialize(self) -> bool:
        """
        Initialize authentication and mail components

        Returns:
            True if initialization successful
        """
        try:
            # If no access token, get it via auth manager
            if not self.access_token:
                self.auth_manager = AuthManager()

                if not self.user_email:
                    # Get first available user
                    users = self.auth_manager.list_users()
                    if not users:
                        print("No authenticated users found. Please authenticate first.")
                        return False
                    self.user_email = users[0]['email']

                # Get or refresh token
                self.access_token = await self.auth_manager.validate_and_refresh_token(self.user_email)

                if not self.access_token:
                    print(f"Failed to get access token for {self.user_email}")
                    return False

            # Initialize components
            self.mail_search = GraphMailSearch(self.access_token, user_id=self.user_email or "me")
            self.mail_filter = GraphMailFilter(user_id=self.user_email or "me")

            return True

        except Exception as e:
            print(f"Initialization error: {str(e)}")
            return False

    async def query_filter(self,
                          filter: FilterParams,
                          exclude: Optional[ExcludeParams] = None,
                          select: Optional[SelectParams] = None,
                          client_filter: Optional[ExcludeParams] = None,
                          top: int = 450,
                          orderby: Optional[str] = None) -> Dict[str, Any]:
        """
        Query with AND filter conditions

        Args:
            filter: FilterParams for inclusion criteria (AND conditions)
            exclude: ExcludeParams for server-side exclusion (API filter)
            select: SelectParams for field selection
            client_filter: ExcludeParams for client-side filtering (post-fetch)
            top: Maximum results (default 450)
            orderby: Sort order

        Returns:
            Email query results

        Example:
            filter_params: FilterParams = {
                'is_read': False,
                'has_attachments': True,
                'importance': 'high'
            }
            exclude_params: ExcludeParams = {
                'exclude_from_address': 'spam@mail.com'
            }
            select_params: SelectParams = {
                'fields': ['id', 'subject', 'from', 'receivedDateTime']
            }
            client_filter_params: ExcludeParams = {
                'exclude_subject_keywords': ['newsletter', 'unsubscribe']
            }

            await query_filter(
                filter=filter_params,
                exclude=exclude_params,
                select=select_params,
                client_filter=client_filter_params
            )
        """
        if not await self.initialize():
            raise Exception("Failed to initialize")

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

        # Get select fields
        select_fields = select.get('fields') if select else None

        # Build final URL
        base_url = self.mail_filter.build_query_url(
            filter_query=combined_filter,
            select_fields=select_fields,
            order_by=orderby
        )

        # Fetch data with immediate filtering if client_filter is provided
        return await self._fetch_parallel_with_url(base_url, top, client_filter)

    def _apply_client_side_filter(self, emails: List[Dict], exclude: ExcludeParams) -> List[Dict]:
        """
        Apply client-side filtering to exclude emails based on ExcludeParams

        Args:
            emails: List of email dictionaries
            exclude: ExcludeParams to apply

        Returns:
            Filtered list of emails
        """
        filtered_emails = []

        for email in emails:
            should_include = True

            # Check each exclude condition
            if exclude.get('exclude_from_address'):
                if email.get('from', {}).get('emailAddress', {}).get('address') == exclude['exclude_from_address']:
                    should_include = False
                    continue

            if exclude.get('exclude_subject_keywords'):
                subject = email.get('subject', '').lower()
                for keyword in exclude['exclude_subject_keywords']:
                    if keyword.lower() in subject:
                        should_include = False
                        break

            if exclude.get('exclude_importance'):
                if email.get('importance') == exclude['exclude_importance']:
                    should_include = False
                    continue

            if exclude.get('exclude_read_status') is not None:
                if email.get('isRead') == exclude['exclude_read_status']:
                    should_include = False
                    continue

            # Add more exclude conditions as needed...

            if should_include:
                filtered_emails.append(email)

        return filtered_emails

    async def query_url(self,
                        url: str,
                        top: int = 450,
                        client_filter: Optional[ExcludeParams] = None) -> Dict[str, Any]:
        """
        Query with pre-built URL

        Args:
            url: Complete Graph API URL with all parameters
            top: Maximum results (default 450)
            client_filter: ExcludeParams for client-side filtering (post-fetch)

        Returns:
            Email query results

        Example:
            url = "https://graph.microsoft.com/v1.0/users/me/messages?$filter=isRead eq false&$top=10"
            result = await query_url(url, top=100)
        """
        if not await self.initialize():
            raise Exception("Failed to initialize")

        # Fetch data with the provided URL and apply filtering immediately
        return await self._fetch_parallel_with_url(url, top, client_filter)

    async def query_search(self,
                           search: str,
                           client_filter: Optional[ExcludeParams] = None,
                           select: Optional[SelectParams] = None,
                           top: int = 250,
                           orderby: Optional[str] = None) -> Dict[str, Any]:
        """
        Query with keyword search ($search parameter)

        Args:
            search: Search keyword or phrase (e.g., "from:boss@company.com", "subject:meeting")
            client_filter: ExcludeParams for client-side filtering (post-fetch)
            select: SelectParams for field selection
            top: Maximum results (default 250 - Graph API search limit)
            orderby: Sort order

        Returns:
            Email query results

        Example:
            search_term = "from:ceo@company.com OR subject:urgent"
            select_params: SelectParams = {
                'fields': ['id', 'subject', 'from', 'receivedDateTime']
            }
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
        if not await self.initialize():
            raise Exception("Failed to initialize")

        # Get select fields
        select_fields = select.get('fields') if select else None

        # Build search URL
        base_url = f"https://graph.microsoft.com/v1.0/users/{self.mail_filter.user_id}/messages"

        # Add search parameter (따옴표로 감싸서 전체 구문 검색)
        base_url += f'?$search="{search}"'

        # Add select fields if provided
        if select_fields:
            select_query = build_select_query({'fields': select_fields})
            if select_query:
                base_url += f"&{select_query}"

        # Add orderby if provided
        if orderby:
            base_url += f"&$orderby={orderby}"

        # Fetch data (Graph API limits search to 250 results) with immediate filtering
        actual_top = min(top, 250)  # Enforce Graph API search limit

        # $search는 페이지네이션과 함께 사용할 수 없으므로 직접 처리
        # $top을 URL에 추가
        base_url += f"&$top={actual_top}"

        # 직접 호출 (페이지네이션 없이)
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                async with session.get(base_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        emails = data.get('value', [])

                        # Apply client-side filtering if provided
                        if client_filter and emails:
                            filtered_emails = self._apply_client_side_filter(emails, client_filter)
                            data['value'] = filtered_emails

                        return {
                            "value": data.get('value', []),
                            "total": len(data.get('value', [])),
                            "@odata.count": len(data.get('value', [])),
                            "request_url": base_url,
                            "search_term": search
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "value": [],
                            "error": f"Search failed with status {response.status}: {error_text[:200]}",
                            "status": "error"
                        }
        except Exception as e:
            return {
                "value": [],
                "error": str(e),
                "status": "error"
            }

    async def _fetch_parallel_with_url(self, base_url: str, total_items: int, client_filter: Optional[ExcludeParams] = None) -> Dict[str, Any]:
        """
        Internal method to fetch with parallel pagination
        Always fetches in pages of 150 items
        Applies client-side filtering immediately as data is received

        Args:
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

        async def fetch_page(session, url, page_num):
            async with semaphore:
                try:
                    async with session.get(url, headers=self.mail_search.headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            emails = data.get('value', [])

                            # Apply client-side filtering immediately if provided
                            if client_filter and emails:
                                filtered_emails = self._apply_client_side_filter(emails, client_filter)
                                data['value'] = filtered_emails
                                print(f"  ✓ Page {page_num}: Retrieved {len(emails)} emails, kept {len(filtered_emails)} after filtering")
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
            "fetch_time": elapsed
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
        emails = results.get('value', [])

        if not emails:
            return "No emails found."

        output = []
        output.append(f"\n{'='*80}")
        output.append(f"Found {len(emails)} email(s)")
        output.append(f"{'='*80}\n")

        for idx, email in enumerate(emails, 1):
            # Parse datetime
            received_dt = email.get('receivedDateTime', 'Unknown')
            if received_dt != 'Unknown':
                try:
                    dt = datetime.fromisoformat(received_dt.replace('Z', '+00:00'))
                    received_dt = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass

            # Get info
            subject = email.get('subject', 'No Subject')
            from_info = email.get('from', {})
            sender_name = from_info.get('emailAddress', {}).get('name', 'Unknown')
            sender_email = from_info.get('emailAddress', {}).get('address', 'Unknown')
            is_read = email.get('isRead', False)
            has_attachments = email.get('hasAttachments', False)
            importance = email.get('importance', 'normal')

            # Format
            read_status = "[READ]" if is_read else "[UNREAD]"
            attach_icon = "📎" if has_attachments else ""
            imp_icon = "❗" if importance == 'high' else ""

            output.append(f"[{idx}] {read_status} {imp_icon}{attach_icon} {subject}")
            output.append(f"    From: {sender_name} <{sender_email}>")
            output.append(f"    Date: {received_dt}")

            if verbose and email.get('bodyPreview'):
                preview = email.get('bodyPreview', '')[:150]
                output.append(f"    Preview: {preview}...")

            output.append("")

        return "\n".join(output)

    async def process_with_options(
        self,
        mail_data: Dict[str, Any],
        mail_storage: str = "memory",
        attachment_handling: str = "skip",
        output_format: str = "combined",
        save_directory: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        메일 데이터를 받아서 처리 옵션에 따라 처리

        Args:
            mail_data: 쿼리 결과 (fetch_parallel_with_url의 반환값)
            mail_storage: 메일 저장 방식 ("memory", "text", "json", "database")
            attachment_handling: 첨부파일 처리 ("skip", "download", "convert", "convert_delete")
            output_format: 출력 형식 ("combined", "separated", "structured")
            save_directory: 저장 디렉토리

        Returns:
            처리된 결과
        """
        from mail_processing_options import MailProcessorHandler, ProcessingOptions, MailStorageOption, AttachmentOption, OutputFormat

        # 옵션 매핑
        storage_map = {
            "memory": MailStorageOption.MEMORY,
            "text": MailStorageOption.TEXT_FILE,
            "json": MailStorageOption.JSON_FILE,
            "database": MailStorageOption.DATABASE
        }

        attachment_map = {
            "skip": AttachmentOption.SKIP,
            "download": AttachmentOption.DOWNLOAD_ONLY,
            "convert": AttachmentOption.DOWNLOAD_CONVERT,
            "convert_delete": AttachmentOption.CONVERT_DELETE
        }

        format_map = {
            "combined": OutputFormat.COMBINED,
            "separated": OutputFormat.SEPARATED,
            "structured": OutputFormat.STRUCTURED
        }

        # MailProcessorHandler 생성 및 처리
        handler = MailProcessorHandler(self.access_token)
        await handler.initialize()

        options = ProcessingOptions(
            mail_storage=storage_map.get(mail_storage, MailStorageOption.MEMORY),
            attachment_handling=attachment_map.get(attachment_handling, AttachmentOption.SKIP),
            output_format=format_map.get(output_format, OutputFormat.COMBINED),
            save_directory=save_directory
        )

        try:
            return await handler.process_mail(mail_data, options)
        finally:
            await handler.close()

    async def close(self):
        """Clean up resources"""
        if self.auth_manager:
            await self.auth_manager.close()

# Convenience function for quick queries
async def query_emails(filter_params: Optional[Dict[str, Any]] = None,
                       search_term: Optional[str] = None,
                       url: Optional[str] = None,
                       user_email: Optional[str] = None,
                       top: int = 450) -> Dict[str, Any]:
    """
    Quick function to query emails

    Args:
        filter_params: Filter parameters
        search_term: Search keyword
        url: Pre-built URL
        user_email: User email
        top: Maximum results

    Returns:
        Email query results
    """
    query = GraphMailQuery(user_email=user_email)
    try:
        return await query.query(
            url=url,
            filter_params=filter_params,
            search_term=search_term,
            top=top
        )
    finally:
        await query.close()


