"""
MCP Tool Definitions for Outlook Graph Mail Server
Contains all tool schemas and definitions for the MCP protocol
"""

from typing import List, Dict, Any

# MCP Tool Definitions
MCP_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "query_emails",
        "description": "Query emails with advanced filtering options",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_email": {
                    "type": "string",
                    "description": "User email address"
                },
                "filter": {
                    "type": "object",
                    "description": "Filter criteria for searching emails (all fields are optional)",
                    "properties": {
                        "from_address": {
                            "type": "string",
                            "description": "Filter by sender's email address"
                        },
                        "subject": {
                            "type": "string",
                            "description": "Filter by email subject (partial match)"
                        },
                        "body": {
                            "type": "string",
                            "description": "Filter by email body content"
                        },
                        "has_attachments": {
                            "type": "boolean",
                            "description": "Filter emails with/without attachments"
                        },
                        "importance": {
                            "type": "string",
                            "enum": [
                                "low",
                                "normal",
                                "high"
                            ],
                            "description": "Filter by email importance level"
                        },
                        "is_read": {
                            "type": "boolean",
                            "description": "Filter by read/unread status"
                        },
                        "received_after": {
                            "type": "string",
                            "format": "date",
                            "description": "Filter emails received after this date (YYYY-MM-DD)"
                        },
                        "received_before": {
                            "type": "string",
                            "format": "date",
                            "description": "Filter emails received before this date (YYYY-MM-DD)"
                        },
                        "categories": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Filter by email categories/tags"
                        }
                    },
                    "required": []
                },
                "exclude": {
                    "type": "object",
                    "description": "Exclusion criteria to filter out unwanted emails",
                    "properties": {
                        "from_addresses": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of sender addresses to exclude"
                        },
                        "domains": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of sender domains to exclude"
                        },
                        "subject_keywords": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Keywords in subject to exclude"
                        },
                        "body_keywords": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Keywords in body to exclude"
                        }
                    },
                    "required": []
                },
                "select": {
                    "type": "object",
                    "description": "Fields to include in the response",
                    "properties": {
                        "fields": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of fields to return for each email"
                        }
                    },
                    "required": []
                },
                "top": {
                    "type": "integer",
                    "default": 10,
                    "maximum": 999,
                    "description": "Maximum number of emails to return"
                },
                "orderby": {
                    "type": "string",
                    "default": "receivedDateTime desc",
                    "description": "Sort order for results"
                }
            },
            "required": [
                "user_email",
                "filter"
            ]
        }
    },
    {
        "name": "get_email",
        "description": "Get a specific email by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_email": {
                    "type": "string",
                    "description": "User email address"
                },
                "message_id": {
                    "type": "string",
                    "description": "Message ID"
                }
            },
            "required": [
                "user_email",
                "message_id"
            ]
        }
    },
    {
        "name": "get_email_attachments",
        "description": "Get attachments for a specific email",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_email": {
                    "type": "string",
                    "description": "User email address"
                },
                "message_id": {
                    "type": "string",
                    "description": "Message ID"
                }
            },
            "required": [
                "user_email",
                "message_id"
            ]
        }
    },
    {
        "name": "download_attachment",
        "description": "Download a specific attachment",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_email": {
                    "type": "string",
                    "description": "User email address"
                },
                "message_id": {
                    "type": "string",
                    "description": "Message ID"
                },
                "attachment_id": {
                    "type": "string",
                    "description": "Attachment ID"
                },
                "save_path": {
                    "type": "string",
                    "description": "Path to save the attachment"
                }
            },
            "required": [
                "user_email",
                "message_id",
                "attachment_id"
            ]
        }
    },
    {
        "name": "search_emails_by_date",
        "description": "Search emails within a date range",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_email": {
                    "type": "string",
                    "description": "User email address"
                },
                "start_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Start date (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "format": "date",
                    "description": "End date (YYYY-MM-DD)"
                },
                "top": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum number of emails to return"
                },
                "orderby": {
                    "type": "string",
                    "default": "receivedDateTime desc",
                    "description": "Sort order for results"
                },
                "select_fields": {
                    "type": "string",
                    "description": "Comma-separated fields to return"
                }
            },
            "required": [
                "user_email",
                "start_date",
                "end_date"
            ]
        }
    },
    {
        "name": "send_email",
        "description": "Send an email",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_email": {
                    "type": "string",
                    "description": "Sender email address"
                },
                "to_recipients": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "List of recipient email addresses"
                },
                "cc_recipients": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "List of CC recipient email addresses"
                },
                "bcc_recipients": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "List of BCC recipient email addresses"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject"
                },
                "body": {
                    "type": "string",
                    "description": "Email body content"
                },
                "body_type": {
                    "type": "string",
                    "enum": [
                        "text",
                        "html"
                    ],
                    "default": "text",
                    "description": "Email body type (text or HTML)"
                },
                "importance": {
                    "type": "string",
                    "enum": [
                        "low",
                        "normal",
                        "high"
                    ],
                    "default": "normal",
                    "description": "Email importance level"
                },
                "attachments": {
                    "type": "array",
                    "description": "List of attachments",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Attachment filename"
                            },
                            "content": {
                                "type": "string",
                                "description": "Base64 encoded content"
                            }
                        },
                        "required": [
                            "name",
                            "content"
                        ]
                    }
                }
            },
            "required": [
                "user_email",
                "to_recipients",
                "subject",
                "body"
            ]
        }
    },
    {
        "name": "reply_to_email",
        "description": "Reply to an email",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_email": {
                    "type": "string",
                    "description": "User email address"
                },
                "message_id": {
                    "type": "string",
                    "description": "Original message ID"
                },
                "comment": {
                    "type": "string",
                    "description": "Reply comment"
                },
                "reply_all": {
                    "type": "boolean",
                    "default": False,
                    "description": "Reply to all recipients"
                }
            },
            "required": [
                "user_email",
                "message_id",
                "comment"
            ]
        }
    },
    {
        "name": "forward_email",
        "description": "Forward an email",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_email": {
                    "type": "string",
                    "description": "User email address"
                },
                "message_id": {
                    "type": "string",
                    "description": "Message ID to forward"
                },
                "to_recipients": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "List of recipient email addresses"
                },
                "comment": {
                    "type": "string",
                    "description": "Forward comment"
                }
            },
            "required": [
                "user_email",
                "message_id",
                "to_recipients"
            ]
        }
    },
    {
        "name": "delete_email",
        "description": "Delete an email",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_email": {
                    "type": "string",
                    "description": "User email address"
                },
                "message_id": {
                    "type": "string",
                    "description": "Message ID to delete"
                }
            },
            "required": [
                "user_email",
                "message_id"
            ]
        }
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
