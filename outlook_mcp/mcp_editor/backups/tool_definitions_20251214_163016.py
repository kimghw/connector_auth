"""
MCP Tool Definitions for Outlook Graph Mail Server
Contains all tool schemas and definitions for the MCP protocol
"""

from typing import List, Dict, Any

# MCP Tool Definitions
MCP_TOOLS: List[Dict[str, Any]] = [
    {
        "description": "Query emails with advanced filtering options",
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
        "name": "query_emails",
        "mcp_service": "query_filter"
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
        "name": "get_email",
        "mcp_service": "query_url"
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
        "name": "get_email_attachments",
        "mcp_service": "query_url"
    },
    {
        "description": "Download a specific attachment",
        "inputSchema": {
            "properties": {
                "attachment_id": {
                    "description": "Attachment ID",
                    "type": "string"
                },
                "message_id": {
                    "description": "Message ID",
                    "type": "string"
                },
                "save_path": {
                    "description": "Path to save the attachment",
                    "type": "string"
                },
                "user_email": {
                    "description": "User email address",
                    "type": "string"
                }
            },
            "required": [
                "user_email",
                "message_id",
                "attachment_id"
            ],
            "type": "object"
        },
        "name": "download_attachment",
        "mcp_service": "query_url"
    },
    {
        "description": "Search emails within a date range",
        "inputSchema": {
            "properties": {
                "end_date": {
                    "description": "End date (YYYY-MM-DD)",
                    "format": "date",
                    "type": "string"
                },
                "orderby": {
                    "default": "receivedDateTime desc",
                    "description": "Sort order for results",
                    "type": "string"
                },
                "select_fields": {
                    "description": "Comma-separated fields to return",
                    "type": "string"
                },
                "start_date": {
                    "description": "Start date (YYYY-MM-DD)",
                    "format": "date",
                    "type": "string"
                },
                "top": {
                    "default": 10,
                    "description": "Maximum number of emails to return",
                    "type": "integer"
                },
                "user_email": {
                    "description": "User email address",
                    "type": "string"
                }
            },
            "required": [
                "user_email",
                "start_date",
                "end_date"
            ],
            "type": "object"
        },
        "name": "search_emails_by_date",
        "mcp_service": "query_search"
    },
    {
        "description": "Send an email",
        "inputSchema": {
            "properties": {
                "attachments": {
                    "description": "List of attachments",
                    "items": {
                        "properties": {
                            "content": {
                                "description": "Base64 encoded content",
                                "type": "string"
                            },
                            "name": {
                                "description": "Attachment filename",
                                "type": "string"
                            }
                        },
                        "required": [
                            "name",
                            "content"
                        ],
                        "type": "object"
                    },
                    "type": "array"
                },
                "bcc_recipients": {
                    "description": "List of BCC recipient email addresses",
                    "items": {
                        "type": "string"
                    },
                    "type": "array"
                },
                "body": {
                    "description": "Email body content",
                    "type": "string"
                },
                "body_type": {
                    "default": "text",
                    "description": "Email body type (text or HTML)",
                    "enum": [
                        "text",
                        "html"
                    ],
                    "type": "string"
                },
                "cc_recipients": {
                    "description": "List of CC recipient email addresses",
                    "items": {
                        "type": "string"
                    },
                    "type": "array"
                },
                "importance": {
                    "default": "normal",
                    "description": "Email importance level",
                    "enum": [
                        "low",
                        "normal",
                        "high"
                    ],
                    "type": "string"
                },
                "subject": {
                    "description": "Email subject",
                    "type": "string"
                },
                "to_recipients": {
                    "description": "List of recipient email addresses",
                    "items": {
                        "type": "string"
                    },
                    "type": "array"
                },
                "user_email": {
                    "description": "Sender email address",
                    "type": "string"
                }
            },
            "required": [
                "user_email",
                "to_recipients",
                "subject",
                "body"
            ],
            "type": "object"
        },
        "name": "send_email",
        "mcp_service": "query_url"
    },
    {
        "description": "Reply to an email",
        "inputSchema": {
            "properties": {
                "comment": {
                    "description": "Reply comment",
                    "type": "string"
                },
                "message_id": {
                    "description": "Original message ID",
                    "type": "string"
                },
                "reply_all": {
                    "default": False,
                    "description": "Reply to all recipients",
                    "type": "boolean"
                },
                "user_email": {
                    "description": "User email address",
                    "type": "string"
                }
            },
            "required": [
                "user_email",
                "message_id",
                "comment"
            ],
            "type": "object"
        },
        "name": "reply_to_email",
        "mcp_service": "query_url"
    },
    {
        "description": "Forward an email",
        "inputSchema": {
            "properties": {
                "comment": {
                    "description": "Forward comment",
                    "type": "string"
                },
                "message_id": {
                    "description": "Message ID to forward",
                    "type": "string"
                },
                "to_recipients": {
                    "description": "List of recipient email addresses",
                    "items": {
                        "type": "string"
                    },
                    "type": "array"
                },
                "user_email": {
                    "description": "User email address",
                    "type": "string"
                }
            },
            "required": [
                "user_email",
                "message_id",
                "to_recipients"
            ],
            "type": "object"
        },
        "name": "forward_email",
        "mcp_service": "query_url"
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
