"""
MCP Tool Definition Templates - Simplified version
Only commonly used parameters are included
"""
from typing import List, Dict, Any

MCP_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "handle_query_filter",
        "description": "Query emails with filter conditions",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_email": {"type": "string", "description": "User email for authentication"},
                "filter": {
                    "type": "object",
                    "description": "Filter conditions for emails",
                    "properties": {
                        "from_address": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}}
                            ],
                            "description": "Sender email address(es)"
                        },
                        "subject": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}}
                            ],
                            "description": "Keywords in subject"
                        },
                        "body_content": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}}
                            ],
                            "description": "Keywords in body"
                        },
                        "is_read": {"type": "boolean", "description": "Read status filter"},
                        "has_attachments": {"type": "boolean", "description": "Has attachments filter"},
                        "importance": {"type": "string", "enum": ["low", "normal", "high"], "description": "Email importance"},
                        "received_date_from": {"type": "string", "description": "Start date (ISO 8601)"},
                        "received_date_to": {"type": "string", "description": "End date (ISO 8601)"}
                    }
                },
                "exclude": {
                    "type": "object",
                    "description": "Exclude conditions",
                    "properties": {
                        "exclude_from_address": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}}
                            ],
                            "description": "Exclude sender addresses"
                        },
                        "exclude_subject_keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Keywords to exclude in subject"
                        }
                    }
                },
                "top": {"type": "integer", "default": 50, "description": "Max number of emails to return"},
                "orderby": {"type": "string", "default": "receivedDateTime desc", "description": "Sort order"}
            },
            "required": ["user_email"]
        }
    },
    {
        "name": "handle_query_search",
        "description": "Search emails with keyword",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_email": {"type": "string", "description": "User email for authentication"},
                "search": {"type": "string", "description": "Search keyword"},
                "top": {"type": "integer", "default": 50, "description": "Max number of emails to return"},
                "orderby": {"type": "string", "default": "receivedDateTime desc", "description": "Sort order"}
            },
            "required": ["user_email", "search"]
        }
    },
    {
        "name": "handle_query_url",
        "description": "Query emails with custom Graph API URL",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_email": {"type": "string", "description": "User email for authentication"},
                "url": {"type": "string", "description": "Custom Graph API URL"},
                "top": {"type": "integer", "default": 50, "description": "Max number of emails to return"}
            },
            "required": ["user_email", "url"]
        }
    }
]