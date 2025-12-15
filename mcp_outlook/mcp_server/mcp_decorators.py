"""
MCP Tool Decorator
Decorator for marking functions as MCP tools
"""
from functools import wraps
from typing import Any, Callable, Dict, Optional

# Registry to store MCP tool metadata
MCP_TOOL_REGISTRY = {}

def mcp_tool(
    tool_name: str,
    description: str = "",
    category: str = "",
    tags: list = None,
    priority: int = 0
) -> Callable:
    """
    Decorator to mark a function as an MCP tool

    Args:
        tool_name: Name of the tool in MCP
        description: Tool description
        category: Tool category
        tags: List of tags
        priority: Tool priority
    """
    def decorator(func: Callable) -> Callable:
        # Store metadata in registry
        MCP_TOOL_REGISTRY[tool_name] = {
            "function": func,
            "tool_name": tool_name,
            "description": description,
            "category": category,
            "tags": tags or [],
            "priority": priority,
            "module": func.__module__,
            "function_name": func.__name__
        }

        # Add metadata to function
        func._mcp_tool = True
        func._mcp_metadata = {
            "tool_name": tool_name,
            "description": description,
            "category": category,
            "tags": tags or [],
            "priority": priority
        }

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator

def get_mcp_tools() -> Dict[str, Any]:
    """Get all registered MCP tools"""
    return MCP_TOOL_REGISTRY

def get_mcp_tool(tool_name: str) -> Optional[Dict[str, Any]]:
    """Get a specific MCP tool by name"""
    return MCP_TOOL_REGISTRY.get(tool_name)