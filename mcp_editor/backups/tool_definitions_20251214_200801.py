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
                },
                "from_address": {
                    "type": "string",
                    "description": "from/emailAddress/address - 단일 또는 여러 발신자 이메일 주소"
                },
                "received_date_time": {
                    "type": "string",
                    "description": "메일 수신 날짜/시간 - 이 시간 이후 메일만 조회 (ISO 8601 형식)"
                }
            },
            "required": [
                "user_email",
                "from_address",
                "received_date_time"
            ],
            "type": "object"
        },
        "name": "get_email_handler"
    },
    {
        "name": "handler_mcp ",
        "description": "New tool description",
        "inputSchema": {
            "type": "object",
            "properties": {
                "example_param": {
                    "type": "string",
                    "description": "Example parameter"
                }
            },
            "required": []
        }
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
