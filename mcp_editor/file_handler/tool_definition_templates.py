"""
MCP Tool Definition Templates for File_Handler Server - AUTO-GENERATED FILE
This file contains tool definitions WITH mcp_service metadata for the web editor.

Generated from @mcp_service decorated functions in source code.
To regenerate: python mcp_editor/cli_regenerate_tools.py file_handler
"""

from typing import List, Dict, Any

# MCP Tool Definitions with metadata
MCP_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "delete_file_metadata",
        "description": "Delete metadata for a specific file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_url": {
                    "type": "string"
                }
            },
            "required": [
                "file_url"
            ]
        },
        "mcp_service": {
            "name": "delete_metadata",
            "signature": "file_url: str"
        }
    },
    {
        "name": "get_file_metadata",
        "description": "Get metadata for a specific file by URL",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_url": {
                    "type": "string"
                }
            },
            "required": [
                "file_url"
            ]
        },
        "mcp_service": {
            "name": "get_metadata",
            "signature": "file_url: str"
        }
    },
    {
        "name": "convert_file_to_text",
        "description": "Process file or URL for text extraction with support for PDF, DOCX, HWP, Excel, Images, and OneDrive URLs",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input_path": {
                    "type": "string"
                }
            },
            "required": [
                "input_path"
            ]
        },
        "mcp_service": {
            "name": "process",
            "signature": "input_path: str, **kwargs"
        }
    },
    {
        "name": "process_directory",
        "description": "Process all files in a directory with optional recursive scanning",
        "inputSchema": {
            "type": "object",
            "properties": {
                "directory_path": {
                    "type": "string"
                }
            },
            "required": [
                "directory_path"
            ]
        },
        "mcp_service": {
            "name": "process_directory",
            "signature": "directory_path: str, **kwargs"
        }
    },
    {
        "name": "convert_onedrive_to_text",
        "description": "Convert OneDrive file or folder to text",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string"
                }
            },
            "required": [
                "url"
            ]
        },
        "mcp_service": {
            "name": "process_onedrive",
            "signature": "url: str, **kwargs"
        }
    },
    {
        "name": "save_file_metadata",
        "description": "Save metadata for a processed file with keywords and additional information",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_url": {
                    "type": "string"
                },
                "keywords": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "additional_metadata": {
                    "type": "object"
                }
            },
            "required": [
                "file_url",
                "keywords"
            ]
        },
        "mcp_service": {
            "name": "save_metadata",
            "signature": "file_url: str, keywords: List[str], additional_metadata: Optional[Dict[str, Any]] = None"
        }
    },
    {
        "name": "search_metadata",
        "description": "Search file metadata by various criteria (keywords, date, file type, etc.)",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        },
        "mcp_service": {
            "name": "search_metadata",
            "signature": "**search_criteria"
        }
    }
]
