"""
MCP Tool Definitions for Outlook Graph Mail Server
Contains all tool schemas and definitions for the MCP protocol
"""

from typing import List, Dict, Any

# MCP Tool Definitions
MCP_TOOLS: List[Dict[str, Any]] = [
    {
        "description": "[TEST EDIT 2025-12-14 17:14:44] Query emails with advanced filtering options",
        "inputSchema": {
            "properties": {
                "exclude": {
                    "description": "Exclusion criteria to filter out unwanted emails",
                    "properties": {
                        "body_keywords": {
                            "description": "Keywords in body to exclude",
                            "items": {
                                "type": "string"
                            },
                            "type": "array"
                        },
                        "domains": {
                            "description": "List of sender domains to exclude",
                            "items": {
                                "type": "string"
                            },
                            "type": "array"
                        },
                        "from_addresses": {
                            "description": "List of sender addresses to exclude",
                            "items": {
                                "type": "string"
                            },
                            "type": "array"
                        },
                        "subject_keywords": {
                            "description": "Keywords in subject to exclude",
                            "items": {
                                "type": "string"
                            },
                            "type": "array"
                        }
                    },
                    "required": [],
                    "type": "object"
                },
                "filter": {
                    "description": "Filter criteria for searching emails (all fields are optional)",
                    "properties": {
                        "body": {
                            "description": "Filter by email body content",
                            "type": "string"
                        },
                        "categories": {
                            "description": "Filter by email categories/tags",
                            "items": {
                                "type": "string"
                            },
                            "type": "array"
                        },
                        "from_address": {
                            "description": "Filter by sender's email address",
                            "type": "string"
                        },
                        "has_attachments": {
                            "description": "Filter emails with/without attachments",
                            "type": "boolean"
                        },
                        "importance": {
                            "description": "Filter by email importance level",
                            "enum": [
                                "low",
                                "normal",
                                "high"
                            ],
                            "type": "string"
                        },
                        "is_read": {
                            "description": "Filter by read/unread status",
                            "type": "boolean"
                        },
                        "received_after": {
                            "description": "Filter emails received after this date (YYYY-MM-DD)",
                            "format": "date",
                            "type": "string"
                        },
                        "received_before": {
                            "description": "Filter emails received before this date (YYYY-MM-DD)",
                            "format": "date",
                            "type": "string"
                        },
                        "subject": {
                            "description": "Filter by email subject (partial match)",
                            "type": "string"
                        }
                    },
                    "required": [],
                    "type": "object"
                },
                "orderby": {
                    "default": "receivedDateTime desc",
                    "description": "Sort order for results",
                    "type": "string"
                },
                "select": {
                    "description": "Fields to include in the response",
                    "properties": {
                        "fields": {
                            "description": "List of fields to return for each email",
                            "items": {
                                "type": "string"
                            },
                            "type": "array"
                        }
                    },
                    "required": [],
                    "type": "object"
                },
                "top": {
                    "default": 10,
                    "description": "Maximum number of emails to return",
                    "maximum": 999,
                    "type": "integer"
                },
                "user_email": {
                    "description": "User email address",
                    "type": "string"
                }
            },
            "required": [
                "user_email",
                "filter"
            ],
            "type": "object"
        },
        "mcp_service": "query_filter",
        "name": "query_emails"
    },
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
    },
    {
        "description": "Get attachments for a specific email",
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
        "name": "get_email_attachments"
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
