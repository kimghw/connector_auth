"""
Sample MCP tool definition templates.

Use this as a starting point for new `mcp_{server}` projects so the web editor
is not empty before auto-extraction. Replace descriptions and parameter details
with real values that match your `@mcp_service` facades.
"""
from typing import Any, Dict, List

MCP_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "list_entities",
        "description": "목록 조회 (status 필터와 limit 지원)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "필터 상태", "targetParam": "status"},
                "limit": {
                    "type": "integer",
                    "description": "최대 반환 개수",
                    "default": 20,
                    "targetParam": "limit",
                },
            },
            "required": [],
        },
        "mcp_service": {
            "name": "list_entities",
            "signature": "status: Optional[str] = None, limit: int = 20",
            "parameters": [
                {"name": "status", "type": "Optional[str]", "has_default": True, "default": None, "is_required": False},
                {"name": "limit", "type": "int", "has_default": True, "default": 20, "is_required": False},
            ],
        },
    },
    {
        "name": "create_entity",
        "description": "엔티티 생성 (필수 name/owner)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "엔티티 이름", "targetParam": "name"},
                "owner": {"type": "string", "description": "소유자", "targetParam": "owner"},
                "priority": {
                    "type": "integer",
                    "description": "우선순위 (선택)",
                    "targetParam": "priority",
                },
            },
            "required": ["name", "owner"],
        },
        "mcp_service": {
            "name": "create_entity",
            "signature": "name: str, owner: str, priority: Optional[int] = None",
            "parameters": [
                {"name": "name", "type": "str", "has_default": False, "default": None, "is_required": True},
                {"name": "owner", "type": "str", "has_default": False, "default": None, "is_required": True},
                {"name": "priority", "type": "Optional[int]", "has_default": True, "default": None, "is_required": False},
            ],
        },
    },
]
