"""
MCP Tool Definitions for Outlook Graph Mail Server
Contains all tool schemas and definitions for the MCP protocol
"""

from typing import List, Dict, Any

# MCP Tool Definitions
MCP_TOOLS: List[Dict[str, Any]] = [
    {
        "description": "Get a specific email by ID",
        "inputSchema": {
            "properties": {
                "message_id": {
                    "description": "Message ID",
                    "type": "string"
                },
                "user_email": {
                    "description": "User email address",
                    "type": "string"
                }
            },
            "required": [
                "user_email",
                "message_id"
            ],
            "type": "object"
        },
        "mcp_service": "query_url",
        "name": "get_email"
    }
]


def get_tool_by_name(tool_name: str) -> Dict[str, Any] | None:
    """Get a specific tool definition by name"""
    for tool in MCP_TOOLS:
        if tool["name"] == tool_name:
            return tool
    return None


def get_tool_names() -> List[str]:
    """Get list of all available tool names"""
    return [tool["name"] for tool in MCP_TOOLS]
