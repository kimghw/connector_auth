"""
MCP Tool Definition Templates - AUTO-GENERATED
Signatures extracted from source code using AST parsing
"""
from typing import List, Dict, Any

MCP_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "Outlook",
        "description": "Build Microsoft Graph API query URL for email operations",
        "inputSchema": {
            "type": "object",
            "required": ["user_email", "filter"],
            "properties": {
                "user_email": {
                    "type": "string",
                    "default": "kimghw@krs.co.kr",
                    "description": "User email for authentication"
                },
                "filter": {
                    "type": "object",
                    "description": "FilterParams for email filtering",
                    "properties": {
                        "sent_date_from": {
                            "type": "string",
                            "default": "12",
                            "description": "메일 발신 시작 날짜 (포함, sentDateTime >= 이 값)"
                        },
                        "sent_date_to": {
                            "type": "string",
                            "default": "12",
                            "description": "메일 발신 종료 날짜 (포함, sentDateTime <= 이 값)"
                        }
                    }
                },
                "top": {
                    "type": "integer",
                    "_source": "mcp_service",
                    "description": "Parameter from MCP service (int)"
                },
                "topp": {
                    "type": "string",
                    "description": ""
                }
            }
        },
        "mcp_service": {
            "name": "query_filter",
            "signature": "user_email: str, filter: FilterParams, exclude: Optional[ExcludeParams] = None, select: Optional[SelectParams] = None, client_filter: Optional[ExcludeParams] = None, top: int = 450, orderby: Optional[str] = None",
            "parameters": [
                {"name": "user_email", "type": "str", "is_required": True, "has_default": False, "default": None},
                {"name": "filter", "type": "FilterParams", "is_required": True, "has_default": False, "default": None},
                {"name": "exclude", "type": "Optional[ExcludeParams]", "is_required": False, "has_default": True, "default": None},
                {"name": "select", "type": "Optional[SelectParams]", "is_required": False, "has_default": True, "default": None},
                {"name": "client_filter", "type": "Optional[ExcludeParams]", "is_required": False, "has_default": True, "default": None},
                {"name": "top", "type": "int", "is_required": False, "has_default": True, "default": 450},
                {"name": "orderby", "type": "Optional[str]", "is_required": False, "has_default": True, "default": None}
            ]
        }
    },
    {
        "name": "keyword_search",
        "description": "Build Microsoft Graph API query URL for email operations",
        "inputSchema": {
            "type": "object",
            "required": ["user_email", "search"],
            "properties": {
                "user_email": {
                    "type": "string"
                },
                "search": {
                    "type": "string",
                    "description": "검색어 ($search 파라미터)"
                },
                "top": {
                    "type": "integer",
                    "default": 250,
                    "description": "반환할 최대 메일 수"
                },
                "orderby": {
                    "type": "string",
                    "description": "정렬 기준"
                },
                "select": {
                    "type": "object",
                    "description": "SelectParams for selecting fields",
                    "properties": {
                        "fields": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "조회할 필드 목록 (미지정 시 모든 필드 반환)"
                        }
                    }
                },
                "client_filter": {
                    "type": "object",
                    "description": "ExcludeParams for client-side filtering",
                    "properties": {
                        "exclude_from_address": {
                            "description": "제외할 발신자 주소 (from 필드)",
                            "oneOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}}
                            ]
                        },
                        "exclude_sender_address": {
                            "description": "제외할 실제 발신자 주소 (sender 필드)",
                            "oneOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}}
                            ]
                        },
                        "exclude_subject_keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "제목에서 제외할 키워드 목록"
                        },
                        "exclude_body_keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "본문에서 제외할 키워드 목록"
                        },
                        "exclude_preview_keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "미리보기에서 제외할 키워드 목록"
                        },
                        "exclude_categories": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "제외할 카테고리 목록"
                        },
                        "exclude_importance": {
                            "type": "string",
                            "enum": ["low", "normal", "high"],
                            "description": "제외할 중요도"
                        },
                        "exclude_sensitivity": {
                            "type": "string",
                            "enum": ["normal", "personal", "private", "confidential"],
                            "description": "제외할 민감도"
                        },
                        "exclude_flag_status": {
                            "type": "string",
                            "enum": ["notFlagged", "complete", "flagged"],
                            "description": "제외할 플래그 상태"
                        },
                        "exclude_classification": {
                            "type": "string",
                            "enum": ["focused", "other"],
                            "description": "제외할 받은 편지함 분류"
                        },
                        "exclude_read_status": {
                            "type": "boolean",
                            "description": "제외할 읽음 상태"
                        },
                        "exclude_draft_status": {
                            "type": "boolean",
                            "description": "제외할 임시 저장 상태"
                        },
                        "exclude_attachment_status": {
                            "type": "boolean",
                            "description": "제외할 첨부파일 상태"
                        },
                        "exclude_read_receipt": {
                            "type": "boolean",
                            "description": "제외할 읽음 확인 상태"
                        },
                        "exclude_delivery_receipt": {
                            "type": "boolean",
                            "description": "제외할 배달 확인 상태"
                        },
                        "exclude_id": {
                            "type": "string",
                            "description": "제외할 메일 ID"
                        },
                        "exclude_conversation_id": {
                            "type": "string",
                            "description": "제외할 대화 스레드 ID"
                        },
                        "exclude_parent_folder_id": {
                            "type": "string",
                            "description": "제외할 폴더 ID"
                        }
                    }
                }
            }
        },
        "mcp_service": {
            "name": "query_search",
            "signature": "user_email: str, search: str, client_filter: Optional[ExcludeParams] = None, select: Optional[SelectParams] = None, top: int = 250, orderby: Optional[str] = None",
            "parameters": [
                {"name": "user_email", "type": "str", "is_required": True, "has_default": False, "default": None},
                {"name": "search", "type": "str", "is_required": True, "has_default": False, "default": None},
                {"name": "client_filter", "type": "Optional[ExcludeParams]", "is_required": False, "has_default": True, "default": None},
                {"name": "select", "type": "Optional[SelectParams]", "is_required": False, "has_default": True, "default": None},
                {"name": "top", "type": "int", "is_required": False, "has_default": True, "default": 250},
                {"name": "orderby", "type": "Optional[str]", "is_required": False, "has_default": True, "default": None}
            ]
        }
    },
    {
        "name": "query_url",
        "description": "Build Microsoft Graph API query URL for email operations",
        "inputSchema": {
            "type": "object",
            "required": ["user_email", "url"],
            "properties": {
                "user_email": {
                    "type": "string"
                },
                "url": {
                    "type": "string",
                    "description": "직접 지정한 Graph API URL"
                },
                "top": {
                    "type": "integer",
                    "default": 450,
                    "description": "반환할 최대 메일 수"
                },
                "client_filter": {
                    "type": "object",
                    "description": "ExcludeParams for client-side filtering",
                    "properties": {
                        "exclude_from_address": {
                            "description": "제외할 발신자 주소 (from 필드)",
                            "oneOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}}
                            ]
                        },
                        "exclude_sender_address": {
                            "description": "제외할 실제 발신자 주소 (sender 필드)",
                            "oneOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}}
                            ]
                        },
                        "exclude_subject_keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "제목에서 제외할 키워드 목록"
                        },
                        "exclude_body_keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "본문에서 제외할 키워드 목록"
                        },
                        "exclude_preview_keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "미리보기에서 제외할 키워드 목록"
                        },
                        "exclude_categories": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "제외할 카테고리 목록"
                        },
                        "exclude_importance": {
                            "type": "string",
                            "enum": ["low", "normal", "high"],
                            "description": "제외할 중요도"
                        },
                        "exclude_sensitivity": {
                            "type": "string",
                            "enum": ["normal", "personal", "private", "confidential"],
                            "description": "제외할 민감도"
                        },
                        "exclude_flag_status": {
                            "type": "string",
                            "enum": ["notFlagged", "complete", "flagged"],
                            "description": "제외할 플래그 상태"
                        },
                        "exclude_classification": {
                            "type": "string",
                            "enum": ["focused", "other"],
                            "description": "제외할 받은 편지함 분류"
                        },
                        "exclude_read_status": {
                            "type": "boolean",
                            "description": "제외할 읽음 상태"
                        },
                        "exclude_draft_status": {
                            "type": "boolean",
                            "description": "제외할 임시 저장 상태"
                        },
                        "exclude_attachment_status": {
                            "type": "boolean",
                            "description": "제외할 첨부파일 상태"
                        },
                        "exclude_read_receipt": {
                            "type": "boolean",
                            "description": "제외할 읽음 확인 상태"
                        },
                        "exclude_delivery_receipt": {
                            "type": "boolean",
                            "description": "제외할 배달 확인 상태"
                        },
                        "exclude_id": {
                            "type": "string",
                            "description": "제외할 메일 ID"
                        },
                        "exclude_conversation_id": {
                            "type": "string",
                            "description": "제외할 대화 스레드 ID"
                        },
                        "exclude_parent_folder_id": {
                            "type": "string",
                            "description": "제외할 폴더 ID"
                        }
                    }
                }
            }
        },
        "mcp_service": {
            "name": "query_url",
            "signature": "user_email: str, url: str, top: int = 450, client_filter: Optional[ExcludeParams] = None",
            "parameters": [
                {"name": "user_email", "type": "str", "is_required": True, "has_default": False, "default": None},
                {"name": "url", "type": "str", "is_required": True, "has_default": False, "default": None},
                {"name": "top", "type": "int", "is_required": False, "has_default": True, "default": 450},
                {"name": "client_filter", "type": "Optional[ExcludeParams]", "is_required": False, "has_default": True, "default": None}
            ]
        }
    },
    {
        "name": "mail_list",
        "description": "New tool description",
        "inputSchema": {
            "type": "object",
            "required": ["user_email", "filter"],
            "properties": {
                "user_email": {
                    "type": "string",
                    "description": ""
                },
                "filter": {
                    "type": "object",
                    "baseModel": "FilterParams",
                    "description": "사용자가 요청한 기간을 언제부터 언제까지 포맷에 맞게 파싱하여 제공합니다.",
                    "required": [],
                    "properties": {
                        "received_date_from": {
                            "type": "string",
                            "description": "메일 수신 시작 날짜 (포함, receivedDateTime >= 이 값)"
                        },
                        "received_date_to": {
                            "type": "string",
                            "description": "메일 수신 종료 날짜 (포함, receivedDateTime <= 이 값)"
                        }
                    }
                },
                "top": {
                    "type": "integer",
                    "default": 100,
                    "description": ""
                }
            }
        },
        "mcp_service": "query_filter"
    }
]
