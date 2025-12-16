"""
MCP Tool Definition Templates - AUTO-GENERATED
Signatures extracted from source code using AST parsing
"""
from typing import List, Dict, Any

MCP_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "handle_query_filter",
        "description": "Build Microsoft Graph API query URL for email operations",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_email": {"type": "string", "description": "User email for authentication"},
                "filter": {
                    "type": "object",
                    "description": "FilterParams for email filtering",
                    "properties": {
                        "from_address": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}}
                            ],
                            "description": "from/emailAddress/address - 단일 또는 여러 발신자 이메일 주소"
                        },
                        "sender_address": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}}
                            ],
                            "description": "sender/emailAddress/address - 실제 발신자 이메일 주소"
                        },
                        "received_date_time": {"type": "string", "description": "메일 수신 날짜/시간 - 이 시간 이후 메일만 조회 (ISO 8601 형식)"},
                        "sent_date_time": {"type": "string", "description": "메일 발신 날짜/시간 - 이 시간 이후 메일만 조회 (ISO 8601 형식)"},
                        "created_date_time": {"type": "string", "description": "메일 생성 날짜/시간 - 이 시간 이후 메일만 조회 (ISO 8601 형식)"},
                        "last_modified_date_time": {"type": "string", "description": "메일 최종 수정 날짜/시간 - 이 시간 이후 메일만 조회 (ISO 8601 형식)"},
                        "received_date_from": {"type": "string", "description": "메일 수신 시작 날짜 (포함, receivedDateTime >= 이 값)"},
                        "received_date_to": {"type": "string", "description": "메일 수신 종료 날짜 (포함, receivedDateTime <= 이 값)"},
                        "sent_date_from": {"type": "string", "description": "메일 발신 시작 날짜 (포함, sentDateTime >= 이 값)"},
                        "sent_date_to": {"type": "string", "description": "메일 발신 종료 날짜 (포함, sentDateTime <= 이 값)"},
                        "is_read": {"type": "boolean", "description": "읽음 상태 필터 (true: 읽은 메일, false: 읽지 않은 메일)"},
                        "is_draft": {"type": "boolean", "description": "임시 저장 상태 필터"},
                        "has_attachments": {"type": "boolean", "description": "첨부파일 포함 여부"},
                        "is_delivery_receipt_requested": {"type": "boolean", "description": "배달 확인 요청 여부"},
                        "is_read_receipt_requested": {"type": "boolean", "description": "읽음 확인 요청 여부"},
                        "importance": {"type": "string", "enum": ["low", "normal", "high"], "description": "메일 중요도"},
                        "sensitivity": {"type": "string", "enum": ["normal", "personal", "private", "confidential"], "description": "메일 민감도"},
                        "inference_classification": {"type": "string", "enum": ["focused", "other"], "description": "받은 편지함 분류"},
                        "subject": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}}
                            ],
                            "description": "제목에 포함될 키워드 (단일 문자열 또는 리스트)"
                        },
                        "body_content": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}}
                            ],
                            "description": "본문에 포함될 키워드 (단일 문자열 또는 리스트)"
                        },
                        "body_preview": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}}
                            ],
                            "description": "미리보기에 포함될 키워드 (단일 문자열 또는 리스트)"
                        },
                        "subject_operator": {"type": "string", "enum": ["or", "and"], "default": "or", "description": "제목 키워드 연결 방식"},
                        "body_operator": {"type": "string", "enum": ["or", "and"], "default": "or", "description": "본문 키워드 연결 방식"},
                        "id": {"type": "string", "description": "메일 고유 ID"},
                        "conversation_id": {"type": "string", "description": "대화 스레드 ID"},
                        "parent_folder_id": {"type": "string", "description": "폴더 ID"},
                        "categories": {"type": "array", "items": {"type": "string"}, "description": "메일 카테고리 목록"},
                        "flag_status": {"type": "string", "enum": ["notFlagged", "complete", "flagged"], "description": "플래그 상태"}
                    }
                },
                "exclude": {
                    "type": "object",
                    "description": "ExcludeParams for filtering out emails",
                    "properties": {
                        "exclude_from_address": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}}
                            ],
                            "description": "제외할 발신자 주소 (from 필드)"
                        },
                        "exclude_sender_address": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}}
                            ],
                            "description": "제외할 실제 발신자 주소 (sender 필드)"
                        },
                        "exclude_subject_keywords": {"type": "array", "items": {"type": "string"}, "description": "제목에서 제외할 키워드 목록"},
                        "exclude_body_keywords": {"type": "array", "items": {"type": "string"}, "description": "본문에서 제외할 키워드 목록"},
                        "exclude_preview_keywords": {"type": "array", "items": {"type": "string"}, "description": "미리보기에서 제외할 키워드 목록"},
                        "exclude_importance": {"type": "string", "enum": ["low", "normal", "high"], "description": "제외할 중요도"},
                        "exclude_sensitivity": {"type": "string", "enum": ["normal", "personal", "private", "confidential"], "description": "제외할 민감도"},
                        "exclude_classification": {"type": "string", "enum": ["focused", "other"], "description": "제외할 받은 편지함 분류"},
                        "exclude_read_status": {"type": "boolean", "description": "제외할 읽음 상태"},
                        "exclude_draft_status": {"type": "boolean", "description": "제외할 임시 저장 상태"},
                        "exclude_attachment_status": {"type": "boolean", "description": "제외할 첨부파일 상태"},
                        "exclude_delivery_receipt": {"type": "boolean", "description": "제외할 배달 확인 상태"},
                        "exclude_read_receipt": {"type": "boolean", "description": "제외할 읽음 확인 상태"},
                        "exclude_flag_status": {"type": "string", "enum": ["notFlagged", "complete", "flagged"], "description": "제외할 플래그 상태"},
                        "exclude_categories": {"type": "array", "items": {"type": "string"}, "description": "제외할 카테고리 목록"},
                        "exclude_id": {"type": "string", "description": "제외할 메일 ID"},
                        "exclude_conversation_id": {"type": "string", "description": "제외할 대화 스레드 ID"},
                        "exclude_parent_folder_id": {"type": "string", "description": "제외할 폴더 ID"}
                    }
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
                    "description": "Additional ExcludeParams for client-side filtering"
                },
                "top": {"type": "integer", "default": 450, "description": "반환할 최대 메일 수"},
                "orderby": {"type": "string", "description": "정렬 기준"}
            },
            "required": ["user_email", "filter"]
        },
        "mcp_service": {
            "name": "query_filter",
            "signature": "user_email: str, filter: FilterParams, exclude: Optional[ExcludeParams] = None, select: Optional[SelectParams] = None, client_filter: Optional[ExcludeParams] = None, top: int = 450, orderby: Optional[str] = None",
            "parameters": [
                {"name": "user_email", "type": "str", "default": None, "has_default": False, "is_required": True},
                {"name": "filter", "type": "FilterParams", "default": None, "has_default": False, "is_required": True},
                {"name": "exclude", "type": "Optional[ExcludeParams]", "default": None, "has_default": True, "is_required": False},
                {"name": "select", "type": "Optional[SelectParams]", "default": None, "has_default": True, "is_required": False},
                {"name": "client_filter", "type": "Optional[ExcludeParams]", "default": None, "has_default": True, "is_required": False},
                {"name": "top", "type": "int", "default": 450, "has_default": True, "is_required": False},
                {"name": "orderby", "type": "Optional[str]", "default": None, "has_default": True, "is_required": False}
            ]
        }
    },
    {
        "name": "handle_query_search",
        "description": "Build Microsoft Graph API query URL for email operations",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_email": {"type": "string"},
                "search": {"type": "string", "description": "검색어 ($search 파라미터)"},
                "client_filter": {
                    "type": "object",
                    "description": "ExcludeParams for client-side filtering",
                    "properties": {
                        "exclude_from_address": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}}
                            ],
                            "description": "제외할 발신자 주소 (from 필드)"
                        },
                        "exclude_sender_address": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}}
                            ],
                            "description": "제외할 실제 발신자 주소 (sender 필드)"
                        },
                        "exclude_subject_keywords": {"type": "array", "items": {"type": "string"}, "description": "제목에서 제외할 키워드 목록"},
                        "exclude_body_keywords": {"type": "array", "items": {"type": "string"}, "description": "본문에서 제외할 키워드 목록"},
                        "exclude_preview_keywords": {"type": "array", "items": {"type": "string"}, "description": "미리보기에서 제외할 키워드 목록"},
                        "exclude_importance": {"type": "string", "enum": ["low", "normal", "high"], "description": "제외할 중요도"},
                        "exclude_sensitivity": {"type": "string", "enum": ["normal", "personal", "private", "confidential"], "description": "제외할 민감도"},
                        "exclude_classification": {"type": "string", "enum": ["focused", "other"], "description": "제외할 받은 편지함 분류"},
                        "exclude_read_status": {"type": "boolean", "description": "제외할 읽음 상태"},
                        "exclude_draft_status": {"type": "boolean", "description": "제외할 임시 저장 상태"},
                        "exclude_attachment_status": {"type": "boolean", "description": "제외할 첨부파일 상태"},
                        "exclude_delivery_receipt": {"type": "boolean", "description": "제외할 배달 확인 상태"},
                        "exclude_read_receipt": {"type": "boolean", "description": "제외할 읽음 확인 상태"},
                        "exclude_flag_status": {"type": "string", "enum": ["notFlagged", "complete", "flagged"], "description": "제외할 플래그 상태"},
                        "exclude_categories": {"type": "array", "items": {"type": "string"}, "description": "제외할 카테고리 목록"},
                        "exclude_id": {"type": "string", "description": "제외할 메일 ID"},
                        "exclude_conversation_id": {"type": "string", "description": "제외할 대화 스레드 ID"},
                        "exclude_parent_folder_id": {"type": "string", "description": "제외할 폴더 ID"}
                    }
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
                "top": {"type": "integer", "default": 250, "description": "반환할 최대 메일 수"},
                "orderby": {"type": "string", "description": "정렬 기준"}
            },
            "required": ["user_email", "search"]
        },
        "mcp_service": {
            "name": "query_search",
            "signature": "user_email: str, search: str, client_filter: Optional[ExcludeParams] = None, select: Optional[SelectParams] = None, top: int = 250, orderby: Optional[str] = None",
            "parameters": [
                {"name": "user_email", "type": "str", "default": None, "has_default": False, "is_required": True},
                {"name": "search", "type": "str", "default": None, "has_default": False, "is_required": True},
                {"name": "client_filter", "type": "Optional[ExcludeParams]", "default": None, "has_default": True, "is_required": False},
                {"name": "select", "type": "Optional[SelectParams]", "default": None, "has_default": True, "is_required": False},
                {"name": "top", "type": "int", "default": 250, "has_default": True, "is_required": False},
                {"name": "orderby", "type": "Optional[str]", "default": None, "has_default": True, "is_required": False}
            ]
        }
    },
    {
        "name": "handle_query_url",
        "description": "Build Microsoft Graph API query URL for email operations",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_email": {"type": "string"},
                "url": {"type": "string", "description": "직접 지정한 Graph API URL"},
                "top": {"type": "integer", "default": 450, "description": "반환할 최대 메일 수"},
                "client_filter": {
                    "type": "object",
                    "description": "ExcludeParams for client-side filtering",
                    "properties": {
                        "exclude_from_address": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}}
                            ],
                            "description": "제외할 발신자 주소 (from 필드)"
                        },
                        "exclude_sender_address": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}}
                            ],
                            "description": "제외할 실제 발신자 주소 (sender 필드)"
                        },
                        "exclude_subject_keywords": {"type": "array", "items": {"type": "string"}, "description": "제목에서 제외할 키워드 목록"},
                        "exclude_body_keywords": {"type": "array", "items": {"type": "string"}, "description": "본문에서 제외할 키워드 목록"},
                        "exclude_preview_keywords": {"type": "array", "items": {"type": "string"}, "description": "미리보기에서 제외할 키워드 목록"},
                        "exclude_importance": {"type": "string", "enum": ["low", "normal", "high"], "description": "제외할 중요도"},
                        "exclude_sensitivity": {"type": "string", "enum": ["normal", "personal", "private", "confidential"], "description": "제외할 민감도"},
                        "exclude_classification": {"type": "string", "enum": ["focused", "other"], "description": "제외할 받은 편지함 분류"},
                        "exclude_read_status": {"type": "boolean", "description": "제외할 읽음 상태"},
                        "exclude_draft_status": {"type": "boolean", "description": "제외할 임시 저장 상태"},
                        "exclude_attachment_status": {"type": "boolean", "description": "제외할 첨부파일 상태"},
                        "exclude_delivery_receipt": {"type": "boolean", "description": "제외할 배달 확인 상태"},
                        "exclude_read_receipt": {"type": "boolean", "description": "제외할 읽음 확인 상태"},
                        "exclude_flag_status": {"type": "string", "enum": ["notFlagged", "complete", "flagged"], "description": "제외할 플래그 상태"},
                        "exclude_categories": {"type": "array", "items": {"type": "string"}, "description": "제외할 카테고리 목록"},
                        "exclude_id": {"type": "string", "description": "제외할 메일 ID"},
                        "exclude_conversation_id": {"type": "string", "description": "제외할 대화 스레드 ID"},
                        "exclude_parent_folder_id": {"type": "string", "description": "제외할 폴더 ID"}
                    }
                }
            },
            "required": ["user_email", "url"]
        },
        "mcp_service": {
            "name": "query_url",
            "signature": "user_email: str, url: str, top: int = 450, client_filter: Optional[ExcludeParams] = None",
            "parameters": [
                {"name": "user_email", "type": "str", "default": None, "has_default": False, "is_required": True},
                {"name": "url", "type": "str", "default": None, "has_default": False, "is_required": True},
                {"name": "top", "type": "int", "default": 450, "has_default": True, "is_required": False},
                {"name": "client_filter", "type": "Optional[ExcludeParams]", "default": None, "has_default": True, "is_required": False}
            ]
        }
    }
]
