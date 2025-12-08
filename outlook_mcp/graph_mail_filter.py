"""
Graph Mail Filter - 메일 필터링 URL 빌더
"""
from typing import Optional, List, Dict, Any


class GraphMailFilter:
    """Graph API 메일 필터 빌더"""

    def __init__(self, user_id: str = "me"):
        """
        Initialize filter builder

        Args:
            user_id: User ID or "me" for current user
        """
        self.user_id = user_id
        self.base_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/messages"

    def build_filter_query(self, **kwargs) -> str:
        """
        Build filter query from parameters

        Returns:
            Filter query string
        """
        filters = []

        # Handle various filter conditions
        if kwargs.get('unread') is not None:
            filters.append(f"isRead eq {str(not kwargs['unread']).lower()}")

        if kwargs.get('has_attachments') is not None:
            filters.append(f"hasAttachments eq {str(kwargs['has_attachments']).lower()}")

        if kwargs.get('importance'):
            filters.append(f"importance eq '{kwargs['importance']}'")

        if kwargs.get('from_sender'):
            filters.append(f"from/emailAddress/address eq '{kwargs['from_sender']}'")

        if kwargs.get('from_any'):
            sender_filters = [f"from/emailAddress/address eq '{sender}'" for sender in kwargs['from_any']]
            if sender_filters:
                filters.append(f"({' or '.join(sender_filters)})")

        if kwargs.get('subject'):
            filters.append(f"contains(subject, '{kwargs['subject']}')")

        if kwargs.get('subject_any'):
            subject_filters = [f"contains(subject, '{subj}')" for subj in kwargs['subject_any']]
            if subject_filters:
                filters.append(f"({' or '.join(subject_filters)})")

        if kwargs.get('days_back'):
            from datetime import datetime, timedelta, timezone
            date_from = datetime.now(timezone.utc) - timedelta(days=kwargs['days_back'])
            filters.append(f"receivedDateTime ge {date_from.strftime('%Y-%m-%dT%H:%M:%SZ')}")

        # Exclusions
        if kwargs.get('exclude_senders'):
            for sender in kwargs['exclude_senders']:
                filters.append(f"from/emailAddress/address ne '{sender}'")

        if kwargs.get('exclude_subjects'):
            for subject in kwargs['exclude_subjects']:
                filters.append(f"not contains(subject, '{subject}')")

        return " and ".join(filters) if filters else ""

    def build_query_url(self,
                        filter_query: Optional[str] = None,
                        select_fields: Optional[List[str]] = None,
                        order_by: Optional[str] = None) -> str:
        """
        Build complete query URL

        Args:
            filter_query: Filter query string
            select_fields: Fields to select
            order_by: Sort order

        Returns:
            Complete URL with query parameters
        """
        url = self.base_url
        params = []

        if filter_query:
            params.append(f"$filter={filter_query}")

        if select_fields:
            params.append(f"$select={','.join(select_fields)}")

        if order_by:
            params.append(f"$orderby={order_by}")

        if params:
            url += "?" + "&".join(params)

        return url