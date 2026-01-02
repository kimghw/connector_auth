"""
MCP Tool Definition Templates for File Handler
Extracted from @mcp_service decorated functions in file_manager.py
"""

from typing import List, Dict, Any

MCP_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "convert_file_to_text",
        "description": "Convert a file to text format. Supports various file types including documents, spreadsheets, and PDFs.",
        "mcp_service": {"name": "process"},
        "inputSchema": {
            "type": "object",
            "properties": {"input_path": {"type": "string", "description": "The path to the file to convert"}},
            "required": ["input_path"],
        },
    },
    {
        "name": "process_directory",
        "description": "Process all files in a directory recursively and convert them to text",
        "mcp_service": {"name": "process_directory"},
        "inputSchema": {
            "type": "object",
            "properties": {"directory_path": {"type": "string", "description": "The path to the directory to process"}},
            "required": ["directory_path"],
        },
    },
    {
        "name": "save_file_metadata",
        "description": "Save metadata for a file including keywords and additional information",
        "mcp_service": {"name": "save_metadata"},
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_url": {"type": "string", "description": "URL or path to the file"},
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keywords associated with the file",
                },
                "additional_metadata": {"type": "object", "description": "Additional metadata as key-value pairs"},
            },
            "required": ["file_url", "keywords"],
        },
    },
    {
        "name": "search_metadata",
        "description": "Search for files based on metadata criteria",
        "mcp_service": {"name": "search_metadata"},
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
            "description": "Search criteria as key-value pairs",
        },
    },
    {
        "name": "convert_onedrive_to_text",
        "description": "Convert a file from OneDrive to text format",
        "mcp_service": {"name": "process_onedrive"},
        "inputSchema": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "The OneDrive URL of the file to convert"}},
            "required": ["url"],
        },
    },
    {
        "name": "get_file_metadata",
        "description": "Retrieve metadata for a specific file",
        "mcp_service": {"name": "get_metadata"},
        "inputSchema": {
            "type": "object",
            "properties": {"file_url": {"type": "string", "description": "URL or path to the file"}},
            "required": ["file_url"],
        },
    },
    {
        "name": "delete_file_metadata",
        "description": "Delete metadata for a specific file",
        "mcp_service": {"name": "delete_metadata"},
        "inputSchema": {
            "type": "object",
            "properties": {"file_url": {"type": "string", "description": "URL or path to the file"}},
            "required": ["file_url"],
        },
    },
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
