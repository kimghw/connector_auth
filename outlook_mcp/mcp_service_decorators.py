"""
MCP Service Decorator
Decorator for marking internal service methods (not exposed as MCP tools)
"""
from functools import wraps
from typing import Any, Callable, Dict, Optional

# Registry for internal service methods
MCP_SERVICE_REGISTRY = {}

def mcp_service(
    tool_name: str,
    description: str = "",
    category: str = "",
    tags: list = None,
    priority: int = 0
) -> Callable:
    """
    Decorator to mark a method as an internal MCP service (not exposed as tool)

    These are internal helper methods that support MCP operations but are not
    directly exposed as MCP tools to external clients.

    Args:
        tool_name: Internal service name
        description: Service description
        category: Service category
        tags: List of tags (often includes "internal")
        priority: Service priority
    """
    def decorator(func: Callable) -> Callable:
        # Store metadata in service registry
        MCP_SERVICE_REGISTRY[tool_name] = {
            "function": func,
            "service_name": tool_name,
            "description": description,
            "category": category,
            "tags": tags or [],
            "priority": priority,
            "module": func.__module__,
            "function_name": func.__name__,
            "is_internal": True  # Mark as internal service
        }

        # Add metadata to function
        func._mcp_service = True
        func._mcp_service_metadata = {
            "service_name": tool_name,
            "description": description,
            "category": category,
            "tags": tags or [],
            "priority": priority,
            "is_internal": True
        }

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator

def get_mcp_services() -> Dict[str, Any]:
    """Get all registered MCP services"""
    return MCP_SERVICE_REGISTRY

def get_mcp_service(service_name: str) -> Optional[Dict[str, Any]]:
    """Get a specific MCP service by name"""
    return MCP_SERVICE_REGISTRY.get(service_name)