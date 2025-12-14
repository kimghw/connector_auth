"""
Generate inputSchema from @mcp_service decorated function signatures
"""

import json
from typing import Dict, Any, List, Optional

# Mapping from Python types to JSON Schema types
TYPE_MAPPING = {
    "str": {"type": "string"},
    "int": {"type": "integer"},
    "float": {"type": "number"},
    "bool": {"type": "boolean"},
    "Dict": {"type": "object"},
    "dict": {"type": "object"},
    "List": {"type": "array"},
    "list": {"type": "array"},
    "Any": {"type": ["string", "number", "boolean", "object", "array", "null"]},
    "None": {"type": "null"},
    "Optional": {"type": ["string", "null"]},  # Will be refined based on inner type
    "FilterParams": {"type": "object", "description": "Filter parameters for querying"},
    "ExcludeParams": {"type": "object", "description": "Exclude parameters for filtering"},
    "SelectParams": {"type": "object", "description": "Select specific fields to return"}
}


def convert_type_to_schema(type_str: Optional[str]) -> Dict[str, Any]:
    """Convert Python type annotation to JSON Schema type"""
    if not type_str:
        return {"type": "string"}  # Default type

    # Handle Optional[Type]
    if type_str.startswith("Optional["):
        inner_type = type_str[9:-1]  # Remove "Optional[" and "]"
        inner_schema = convert_type_to_schema(inner_type)
        if isinstance(inner_schema.get("type"), str):
            return {**inner_schema, "type": [inner_schema["type"], "null"]}
        return inner_schema

    # Handle List[Type]
    if type_str.startswith("List[") or type_str.startswith("list["):
        inner_type = type_str[5:-1]  # Remove "List[" and "]"
        return {
            "type": "array",
            "items": convert_type_to_schema(inner_type)
        }

    # Handle Dict[Type, Type]
    if type_str.startswith("Dict[") or type_str.startswith("dict["):
        return {"type": "object"}

    # Direct type mapping
    if type_str in TYPE_MAPPING:
        return TYPE_MAPPING[type_str].copy()

    # Default for unknown types
    return {"type": "object", "description": f"{type_str} object"}


def generate_schema_from_service(service_name: str, mcp_services_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate inputSchema from @mcp_service function signature"""

    # Find the service in the data
    service_info = None
    for service in mcp_services_data.get("services_with_signatures", []):
        if service["name"] == service_name:
            service_info = service
            break

    if not service_info:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    properties = {}
    required = []

    for param in service_info["parameters"]:
        param_name = param["name"]

        # Skip 'self' parameter
        if param_name == "self":
            continue

        # Convert type to schema
        param_schema = convert_type_to_schema(param.get("type"))

        # Add description based on parameter name
        if param_name == "user_email":
            param_schema["description"] = "User email address"
        elif param_name == "search":
            param_schema["description"] = "Search query string"
        elif param_name == "url":
            param_schema["description"] = "Graph API URL"
        elif param_name == "top":
            param_schema["description"] = f"Maximum number of results (default: {param.get('default', 10)})"
        elif param_name == "orderby":
            param_schema["description"] = "Sort order for results"
        elif param_name == "filter":
            param_schema = {
                "type": "object",
                "description": "Filter parameters for querying",
                "properties": {
                    "from": {"type": "string", "description": "Filter by sender email"},
                    "subject": {"type": "string", "description": "Filter by subject"},
                    "body": {"type": "string", "description": "Filter by body content"},
                    "has_attachments": {"type": "boolean", "description": "Filter emails with attachments"},
                    "is_read": {"type": "boolean", "description": "Filter by read status"},
                    "importance": {"type": "string", "enum": ["low", "normal", "high"], "description": "Filter by importance"},
                    "received_after": {"type": "string", "format": "date-time", "description": "Filter emails received after this date"},
                    "received_before": {"type": "string", "format": "date-time", "description": "Filter emails received before this date"}
                }
            }
        elif param_name == "exclude" or param_name == "client_filter":
            param_schema = {
                "type": "object",
                "description": "Exclude parameters for filtering",
                "properties": {
                    "from": {"type": "string", "description": "Exclude sender email"},
                    "subject": {"type": "string", "description": "Exclude by subject"},
                    "body": {"type": "string", "description": "Exclude by body content"}
                }
            }
        elif param_name == "select":
            param_schema = {
                "type": "object",
                "description": "Select specific fields to return",
                "properties": {
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of fields to return"
                    }
                }
            }

        properties[param_name] = param_schema

        # Add to required if not optional and no default value
        param_type = param.get("type", "")
        if not param_type.startswith("Optional") and param.get("default") is None:
            required.append(param_name)

    return {
        "type": "object",
        "properties": properties,
        "required": required
    }


def create_tool_from_mcp_service(tool_name: str,
                                description: str,
                                mcp_service: str,
                                mcp_services_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a complete tool definition from an @mcp_service function"""

    input_schema = generate_schema_from_service(mcp_service, mcp_services_data)

    return {
        "name": tool_name,
        "description": description,
        "inputSchema": input_schema,
        "mcp_service": mcp_service
    }


if __name__ == "__main__":
    # Example usage
    import os

    # Load MCP services data
    mcp_services_path = os.path.join(os.path.dirname(__file__), "mcp_services.json")
    with open(mcp_services_path, 'r') as f:
        mcp_services_data = json.load(f)

    # Example: Generate tool for query_search
    tool = create_tool_from_mcp_service(
        tool_name="search_emails",
        description="Search emails using Microsoft Graph API",
        mcp_service="query_search",
        mcp_services_data=mcp_services_data
    )

    print(json.dumps(tool, indent=2))