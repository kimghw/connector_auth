"""
MCP Tool Definition Templates - AUTO-GENERATED
Signatures extracted from source code using AST parsing
"""
from typing import List, Dict, Any

MCP_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "Handle_query_filter",
        "description": "Build Microsoft Graph API query URL for email operations",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_email": {"type": "string"},
                "filter": {"type": "string"},
                "exclude": {"type": "string"},
                "select": {"type": "string"},
                "client_filter": {"type": "string"},
                "top": {"type": "integer"},
                "orderby": {"type": "string"}
            },
            "required": ["user_email", "filter"]
        },
        "mcp_service": {
            "name": "query_filter",
            "signature": "user_email: str, filter: FilterParams, exclude: Optional[ExcludeParams] = None, select: Optional[SelectParams] = None, client_filter: Optional[ExcludeParams] = None, top: int = 450, orderby: Optional[str] = None",
            "parameters": [
                {"name": "user_email", "type": "str", "default": None, "has_default": False, "is_required": True},
                {"name": "filter", "type": "FilterParams", "default": None, "has_default": False, "is_required": True},
                {"name": "exclude", "type": "Optional[ExcludeParams]", "default": None, "has_default": True, "is_required": False},
                {"name": "select", "type": "Optional[SelectParams]", "default": None, "has_default": True, "is_required": False},
                {"name": "client_filter", "type": "Optional[ExcludeParams]", "default": None, "has_default": True, "is_required": False},
                {"name": "top", "type": "int", "default": 450, "has_default": True, "is_required": False},
                {"name": "orderby", "type": "Optional[str]", "default": None, "has_default": True, "is_required": False}
            ]
        }
    },
    {
        "name": "handle_query_search",
        "description": "Build Microsoft Graph API query URL for email operations",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_email": {"type": "string"},
                "search": {"type": "string"},
                "client_filter": {"type": "string"},
                "select": {"type": "string"},
                "top": {"type": "integer"},
                "orderby": {"type": "string"}
            },
            "required": ["user_email", "search"]
        },
        "mcp_service": {
            "name": "query_search",
            "signature": "user_email: str, search: str, client_filter: Optional[ExcludeParams] = None, select: Optional[SelectParams] = None, top: int = 250, orderby: Optional[str] = None",
            "parameters": [
                {"name": "user_email", "type": "str", "default": None, "has_default": False, "is_required": True},
                {"name": "search", "type": "str", "default": None, "has_default": False, "is_required": True},
                {"name": "client_filter", "type": "Optional[ExcludeParams]", "default": None, "has_default": True, "is_required": False},
                {"name": "select", "type": "Optional[SelectParams]", "default": None, "has_default": True, "is_required": False},
                {"name": "top", "type": "int", "default": 250, "has_default": True, "is_required": False},
                {"name": "orderby", "type": "Optional[str]", "default": None, "has_default": True, "is_required": False}
            ]
        }
    },
    {
        "name": "handlequery_url",
        "description": "Build Microsoft Graph API query URL for email operations",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_email": {"type": "string"},
                "url": {"type": "string"},
                "top": {"type": "integer"},
                "client_filter": {"type": "string"}
            },
            "required": ["user_email", "url"]
        },
        "mcp_service": {
            "name": "query_url",
            "signature": "user_email: str, url: str, top: int = 450, client_filter: Optional[ExcludeParams] = None",
            "parameters": [
                {"name": "user_email", "type": "str", "default": None, "has_default": False, "is_required": True},
                {"name": "url", "type": "str", "default": None, "has_default": False, "is_required": True},
                {"name": "top", "type": "int", "default": 450, "has_default": True, "is_required": False},
                {"name": "client_filter", "type": "Optional[ExcludeParams]", "default": None, "has_default": True, "is_required": False}
            ]
        }
    }
]
