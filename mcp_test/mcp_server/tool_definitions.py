"""
MCP Tool Definitions - AUTO-GENERATED FILE
"""
from typing import List, Dict, Any

MCP_TOOLS: List[Dict[str, Any]] = []


def get_tool_by_name(tool_name: str) -> Dict[str, Any] | None:
    for tool in MCP_TOOLS:
        if tool["name"] == tool_name:
            return tool
    return None


def get_tool_names() -> List[str]:
    return [tool["name"] for tool in MCP_TOOLS]
