"""
Graph Mail Search - 메일 검색 기능
"""
from typing import Optional, Dict, Any


class GraphMailSearch:
    """Graph API 메일 검색"""

    def __init__(self, access_token: str, user_id: str = "me"):
        """
        Initialize mail search

        Args:
            access_token: Access token for Graph API
            user_id: User ID or "me" for current user
        """
        self.access_token = access_token
        self.user_id = user_id
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        self.base_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/messages"

    def build_search_url(self, search_term: str, select_fields: Optional[list] = None) -> str:
        """
        Build search URL

        Args:
            search_term: Search keyword
            select_fields: Fields to select

        Returns:
            Search URL
        """
        url = self.base_url
        params = [f"$search=\"{search_term}\""]

        if select_fields:
            params.append(f"$select={','.join(select_fields)}")

        url += "?" + "&".join(params)
        return url