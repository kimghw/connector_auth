"""
Template for exposing an existing project to the MCP web editor via a thin facade.

Copy this into `mcp_{server_name}/{server_name}_service.py` (or `service.py`) and
wrap only the functions you want to expose. The `@mcp_service` decorator captures
metadata for the registry and schema generation.
"""
from typing import List, Optional

from mcp_editor.mcp_service_registry.mcp_service_decorator import mcp_service

# Import your real implementation here
# from your_project.core import ProjectService
#
# svc = ProjectService()


@mcp_service(
    tool_name="list_entities",          # MCP tool name (LLM-visible)
    description="List domain entities with optional filters",
    server_name="demo",                 # -> mcp_demo folder name
    service_name="list_entities",       # underlying method you intend to call
    category="read",
    tags=["listing", "demo"],
)
def list_entities(status: Optional[str] = None, limit: int = 20) -> List[dict]:
    """
    Example read-only tool. Replace body with your facade call:
    return svc.list_entities(status=status, limit=limit)
    """
    return []


@mcp_service(
    tool_name="create_entity",
    description="Create a new domain entity from provided fields",
    server_name="demo",
    service_name="create_entity",
    category="write",
    tags=["create", "demo"],
)
def create_entity(name: str, owner: str, priority: Optional[int] = None) -> dict:
    """
    Example write tool. Replace body with your facade call:
    return svc.create_entity(name=name, owner=owner, priority=priority)
    """
    return {"name": name, "owner": owner, "priority": priority}


# Optional: consolidate existing functions instead of writing new facades
# def lift_existing():
#     for func in [svc.list_entities, svc.create_entity]:
#         decorate dynamically if you prefer automated extraction
