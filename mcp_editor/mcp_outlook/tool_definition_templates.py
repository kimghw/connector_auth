"""
MCP Tool Definition Templates - AUTO-GENERATED
Signatures extracted from source code using AST parsing
"""
from typing import List, Dict, Any

MCP_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "handler_mail_fetch_filter",
        "description": "필터 방식 메일 조회 기능",
        "inputSchema": {
            "type": "object",
            "required": [],
            "properties": {
                "filter_params": {
                    "type": "object",
                    "baseModel": "FilterParams",
                    "description": "메일 필터링 조건",
                    "properties": {
                        "received_date_from": {
                            "type": "string",
                            "description": "메일 수신 시작 날짜 (포함, receivedDateTime >= 이 값)"
                        },
                        "received_date_to": {
                            "type": "string",
                            "description": "메일 수신 종료 날짜 (포함, receivedDateTime <= 이 값)"
                        },
                        "sent_date_from": {
                            "type": "string",
                            "description": "메일 발신 시작 날짜 (포함, sentDateTime >= 이 값)"
                        },
                        "sent_date_to": {
                            "type": "string",
                            "description": "메일 발신 종료 날짜 (포함, sentDateTime <= 이 값)"
                        }
                    }
                },
                "exclude_params": {
                    "type": "object",
                    "baseModel": "ExcludeParams",
                    "description": "제외 조건"
                },
                "select_params": {
                    "type": "object",
                    "baseModel": "SelectParams",
                    "description": "조회할 필드 선택",
                    "properties": {
                        "fields": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "조회할 필드 목록"
                        }
                    }
                },
                "top": {
                    "type": "integer",
                    "default": 50,
                    "description": "반환할 최대 메일 수"
                }
            }
        },
        "mcp_service": {
            "name": "fetch_filter",
            "signature": "filter_params: Optional[FilterParams] = None, exclude_params: Optional[ExcludeParams] = None, select_params: Optional[SelectParams] = None, top: int = 50",
            "parameters": [
                {"name": "filter_params", "type": "Optional[FilterParams]", "is_required": False, "has_default": True, "default": None},
                {"name": "exclude_params", "type": "Optional[ExcludeParams]", "is_required": False, "has_default": True, "default": None},
                {"name": "select_params", "type": "Optional[SelectParams]", "is_required": False, "has_default": True, "default": None},
                {"name": "top", "type": "int", "is_required": False, "has_default": True, "default": 50}
            ]
        }
    },
    {
        "name": "handler_mail_fetch_search",
        "description": "검색 방식 메일 조회 기능",
        "inputSchema": {
            "type": "object",
            "required": ["search_term"],
            "properties": {
                "search_term": {
                    "type": "string",
                    "description": "검색어 ($search 파라미터)"
                },
                "select_params": {
                    "type": "object",
                    "baseModel": "SelectParams",
                    "description": "조회할 필드 선택",
                    "properties": {
                        "fields": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "조회할 필드 목록"
                        }
                    }
                },
                "top": {
                    "type": "integer",
                    "default": 50,
                    "description": "반환할 최대 메일 수"
                }
            }
        },
        "mcp_service": {
            "name": "fetch_search",
            "signature": "search_term: str, select_params: Optional[SelectParams] = None, top: int = 50",
            "parameters": [
                {"name": "search_term", "type": "str", "is_required": True, "has_default": False, "default": None},
                {"name": "select_params", "type": "Optional[SelectParams]", "is_required": False, "has_default": True, "default": None},
                {"name": "top", "type": "int", "is_required": False, "has_default": True, "default": 50}
            ]
        }
    },
    {
        "name": "handler_mail_process_with_download",
        "description": "첨부파일 다운로드 포함 메일 처리 기능",
        "inputSchema": {
            "type": "object",
            "required": [],
            "properties": {
                "filter_params": {
                    "type": "object",
                    "baseModel": "FilterParams",
                    "description": "메일 필터링 조건",
                    "properties": {
                        "received_date_from": {
                            "type": "string",
                            "description": "메일 수신 시작 날짜"
                        },
                        "received_date_to": {
                            "type": "string",
                            "description": "메일 수신 종료 날짜"
                        }
                    }
                },
                "search_term": {
                    "type": "string",
                    "description": "검색어 (지정시 검색 모드로 전환)"
                },
                "top": {
                    "type": "integer",
                    "default": 50,
                    "description": "반환할 최대 메일 수"
                },
                "save_directory": {
                    "type": "string",
                    "description": "첨부파일 저장 디렉토리 경로"
                }
            }
        },
        "mcp_service": {
            "name": "process_with_download",
            "signature": "filter_params: Optional[FilterParams] = None, search_term: Optional[str] = None, top: int = 50, save_directory: Optional[str] = None",
            "parameters": [
                {"name": "filter_params", "type": "Optional[FilterParams]", "is_required": False, "has_default": True, "default": None},
                {"name": "search_term", "type": "Optional[str]", "is_required": False, "has_default": True, "default": None},
                {"name": "top", "type": "int", "is_required": False, "has_default": True, "default": 50},
                {"name": "save_directory", "type": "Optional[str]", "is_required": False, "has_default": True, "default": None}
            ]
        }
    }
]
