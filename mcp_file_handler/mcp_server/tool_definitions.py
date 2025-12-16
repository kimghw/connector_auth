"""MCP tool definitions for attachment processing."""

from typing import Dict, Any, List

MCP_TOOLS = [
    {
        "name": "convert_file_to_text",
        "description": "Convert a file to text format",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to convert"
                },
                "output_format": {
                    "type": "string",
                    "enum": ["text", "json"],
                    "description": "Output format (default: text)",
                    "default": "text"
                },
                "use_ocr": {
                    "type": "boolean",
                    "description": "Use OCR for scanned documents",
                    "default": False
                },
                "save_metadata": {
                    "type": "boolean",
                    "description": "Save metadata to storage",
                    "default": False
                },
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keywords to associate with the file"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "convert_onedrive_to_text",
        "description": "Convert OneDrive file or folder to text",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "OneDrive share URL"
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Process folders recursively",
                    "default": True
                },
                "output_format": {
                    "type": "string",
                    "enum": ["text", "json"],
                    "description": "Output format",
                    "default": "text"
                },
                "save_metadata": {
                    "type": "boolean",
                    "description": "Save metadata to storage",
                    "default": False
                },
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keywords to associate with files"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "process_directory",
        "description": "Process all files in a directory",
        "inputSchema": {
            "type": "object",
            "properties": {
                "directory_path": {
                    "type": "string",
                    "description": "Path to the directory"
                },
                "pattern": {
                    "type": "string",
                    "description": "File pattern to match (e.g., '*.pdf')",
                    "default": "*"
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Process subdirectories",
                    "default": False
                },
                "output_format": {
                    "type": "string",
                    "enum": ["text", "json"],
                    "description": "Output format",
                    "default": "json"
                },
                "save_metadata": {
                    "type": "boolean",
                    "description": "Save metadata for each file",
                    "default": False
                }
            },
            "required": ["directory_path"]
        }
    },
    {
        "name": "save_file_metadata",
        "description": "Save metadata for a file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_url": {
                    "type": "string",
                    "description": "File URL or path"
                },
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keywords to associate with the file"
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional metadata to save"
                }
            },
            "required": ["file_url", "keywords"]
        }
    },
    {
        "name": "search_metadata",
        "description": "Search file metadata",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "Keyword to search for"
                },
                "file_url": {
                    "type": "string",
                    "description": "File URL pattern to match"
                }
            }
        }
    },
    {
        "name": "get_file_metadata",
        "description": "Get metadata for a specific file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_url": {
                    "type": "string",
                    "description": "File URL or path"
                }
            },
            "required": ["file_url"]
        }
    },
    {
        "name": "delete_file_metadata",
        "description": "Delete metadata for a file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_url": {
                    "type": "string",
                    "description": "File URL or path"
                }
            },
            "required": ["file_url"]
        }
    }
]


def get_tool_by_name(name: str) -> Dict[str, Any]:
    """Get tool definition by name.

    Args:
        name: Tool name

    Returns:
        Tool definition or None
    """
    for tool in MCP_TOOLS:
        if tool['name'] == name:
            return tool
    return None


def validate_tool_input(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Validate tool input against schema.

    Args:
        tool_name: Name of the tool
        arguments: Input arguments

    Returns:
        Validation result with 'valid' and 'errors' keys
    """
    tool = get_tool_by_name(tool_name)
    if not tool:
        return {'valid': False, 'errors': [f'Unknown tool: {tool_name}']}

    schema = tool.get('inputSchema', {})
    required = schema.get('required', [])
    properties = schema.get('properties', {})

    errors = []

    # Check required fields
    for field in required:
        if field not in arguments:
            errors.append(f'Missing required field: {field}')

    # Validate field types
    for field, value in arguments.items():
        if field in properties:
            prop_schema = properties[field]
            prop_type = prop_schema.get('type')

            if prop_type == 'string' and not isinstance(value, str):
                errors.append(f'{field} must be a string')
            elif prop_type == 'boolean' and not isinstance(value, bool):
                errors.append(f'{field} must be a boolean')
            elif prop_type == 'array' and not isinstance(value, list):
                errors.append(f'{field} must be an array')
            elif prop_type == 'object' and not isinstance(value, dict):
                errors.append(f'{field} must be an object')

            # Check enum values
            if 'enum' in prop_schema and value not in prop_schema['enum']:
                errors.append(f'{field} must be one of: {prop_schema["enum"]}')

    return {
        'valid': len(errors) == 0,
        'errors': errors
    }