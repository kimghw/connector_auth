"""
STDIO MCP Server for Outlook MCP Server
Handles MCP protocol via standard input/output
Generated from universal template with registry data and protocol selection
"""
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import sys
import os
import logging
import asyncio
from typing import AsyncIterator

# Add parent directories to path for module access
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)

# Add paths for imports based on server type
sys.path.insert(0, grandparent_dir)  # For session module and package imports
sys.path.insert(0, parent_dir)  # For direct module imports

# Import types dynamically based on type_info
from mcp_outlook.outlook_types import ExcludeParams, FilterParams, SelectParams
from mcp_outlook.graph_mail_client import ProcessingMode, QueryMethod

# Import tool definitions
try:
    from .tool_definitions import MCP_TOOLS
except ImportError:
    from tool_definitions import MCP_TOOLS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import service classes (unique)
from mcp_outlook.outlook_service import MailService

# Create service instances
mail_service = MailService()

# ============================================================
# Common MCP protocol utilities (shared across protocols)
# ============================================================

SUPPORTED_PROTOCOLS = {"rest", "stdio", "stream"}

# Pre-computed tool -> implementation mapping
TOOL_IMPLEMENTATIONS = {
    "mail_list_period": {
        "service_class": "MailService",
        "method": "query_mail_list"
    },
    "mail_list_keyword": {
        "service_class": "MailService",
        "method": "fetch_search"
    },
    "mail_query_if_emaidID": {
        "service_class": "MailService",
        "method": "batch_and_fetch"
    },
    "mail_attachment_meta": {
        "service_class": "MailService",
        "method": "fetch_attachments_metadata"
    },
    "mail_attachment_download": {
        "service_class": "MailService",
        "method": "download_attachments"
    },
    "mail_fetch_filter": {
        "service_class": "MailService",
        "method": "fetch_filter"
    },
    "mail_fetch_search": {
        "service_class": "MailService",
        "method": "fetch_search"
    },
    "mail_process_with_download": {
        "service_class": "MailService",
        "method": "process_with_download"
    },
    "mail_query_url": {
        "service_class": "MailService",
        "method": "fetch_url"
    },
}

# Pre-computed service class -> instance mapping
SERVICE_INSTANCES = {
    "MailService": mail_service,
}


def get_tool_config(tool_name: str) -> Optional[dict]:
    """Lookup MCP tool definition by name"""
    for tool in MCP_TOOLS:
        if tool.get("name") == tool_name:
            return tool
    return None


def get_tool_implementation(tool_name: str) -> Optional[dict]:
    """Get implementation mapping for a tool"""
    return TOOL_IMPLEMENTATIONS.get(tool_name)


def get_service_instance(service_class: str):
    """Get instantiated service by class name"""
    return SERVICE_INSTANCES.get(service_class)


def format_tool_result(result: Any) -> Dict[str, Any]:
    """Normalize service results into a consistent MCP payload"""
    if isinstance(result, dict):
        return result
    if isinstance(result, list):
        return {"items": result}
    if isinstance(result, str):
        return {"message": result}
    if result is None:
        return {"success": True}
    return {"result": str(result)}


def build_mcp_content(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Wrap normalized payload into MCP content envelope"""
    return {
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(payload, ensure_ascii=False, indent=2)
                }
            ]
        }
    }


# ============================================================
# Service Factors Support (Internal + Signature Defaults)
# ============================================================
# Service factors are now embedded in tool definitions via mcp_service_factors
# This data is passed from the generator as part of the context
# Structure: { tool_name: { 'internal': {...}, 'signature_defaults': {...} } }
SERVICE_FACTORS = {'mail_attachment_download': {'internal': {'select_params': {'original_schema': {'properties': {'body': {'description': '메시지 '
                                                                                                                        '본문 '
                                                                                                                        '(HTML '
                                                                                                                        '또는 '
                                                                                                                        '텍스트 '
                                                                                                                        '형식)',
                                                                                                         'type': 'boolean'},
                                                                                                'categories': {'description': '메시지에 '
                                                                                                                              '연결된 '
                                                                                                                              '카테고리 '
                                                                                                                              '목록',
                                                                                                               'type': 'boolean'},
                                                                                                'change_key': {'description': '메시지 '
                                                                                                                              '버전 '
                                                                                                                              '키',
                                                                                                               'type': 'boolean'},
                                                                                                'created_date_time': {'description': '메시지 '
                                                                                                                                     '생성 '
                                                                                                                                     '날짜/시간 '
                                                                                                                                     '(ISO '
                                                                                                                                     '8601 '
                                                                                                                                     '형식, '
                                                                                                                                     'UTC)',
                                                                                                                      'type': 'boolean'},
                                                                                                'id': {'description': '메시지 '
                                                                                                                      '고유 '
                                                                                                                      '식별자 '
                                                                                                                      '(읽기 '
                                                                                                                      '전용)',
                                                                                                       'type': 'boolean'},
                                                                                                'last_modified_date_time': {'description': '메시지 '
                                                                                                                                           '최종 '
                                                                                                                                           '수정 '
                                                                                                                                           '날짜/시간 '
                                                                                                                                           '(ISO '
                                                                                                                                           '8601 '
                                                                                                                                           '형식, '
                                                                                                                                           'UTC)',
                                                                                                                            'type': 'boolean'},
                                                                                                'subject': {'description': '메시지 '
                                                                                                                           '제목',
                                                                                                            'type': 'boolean'}},
                                                                                 'targetParam': 'select_params',
                                                                                 'type': 'object'},
                                                             'source': 'internal',
                                                             'targetParam': 'select_params',
                                                             'type': 'object',
                                                             'value': {}}},
                              'signature_defaults': {}},
 'mail_attachment_meta': {'internal': {'select_params': {'original_schema': {'properties': {'body': {'default': True,
                                                                                                     'description': '메시지 '
                                                                                                                    '본문 '
                                                                                                                    '(HTML '
                                                                                                                    '또는 '
                                                                                                                    '텍스트 '
                                                                                                                    '형식)',
                                                                                                     'type': 'boolean'},
                                                                                            'id': {'default': True,
                                                                                                   'description': '메시지 '
                                                                                                                  '고유 '
                                                                                                                  '식별자 '
                                                                                                                  '(읽기 '
                                                                                                                  '전용)',
                                                                                                   'type': 'boolean'},
                                                                                            'received_date_time': {'default': True,
                                                                                                                   'description': '메시지 '
                                                                                                                                  '수신 '
                                                                                                                                  '날짜/시간 '
                                                                                                                                  '(ISO '
                                                                                                                                  '8601 '
                                                                                                                                  '형식, '
                                                                                                                                  'UTC)',
                                                                                                                   'type': 'boolean'},
                                                                                            'subject': {'default': True,
                                                                                                        'description': '메시지 '
                                                                                                                       '제목',
                                                                                                        'type': 'boolean'}},
                                                                             'targetParam': 'select_params',
                                                                             'type': 'object'},
                                                         'source': 'internal',
                                                         'targetParam': 'select_params',
                                                         'type': 'SelectParams',
                                                         'value': {'body': True,
                                                                   'id': True,
                                                                   'received_date_time': True,
                                                                   'subject': True}}},
                          'signature_defaults': {}},
 'mail_fetch_filter': {'internal': {},
                       'signature_defaults': {'filter_params': {'original_schema': {'properties': {'test_field': {'default': 'test_value',
                                                                                                                  'type': 'string'}},
                                                                                    'targetParam': 'filter_params',
                                                                                    'type': 'object'},
                                                                'source': 'signature_defaults',
                                                                'targetParam': 'filter_params',
                                                                'type': 'FilterParams',
                                                                'value': {'test_field': 'test_value'}}}},
 'mail_list_keyword': {'internal': {'select_params': {'original_schema': {'properties': {},
                                                                          'targetParam': 'select_params',
                                                                          'type': 'object'},
                                                      'source': 'internal',
                                                      'targetParam': 'select_params',
                                                      'type': 'SelectParams',
                                                      'value': {}}},
                       'signature_defaults': {}},
 'mail_list_period': {'internal': {'client_filter': {'original_schema': {'properties': {'exclude_from_address': {'default': 'block@krs.co.kr',
                                                                                                                 'description': '제외할 '
                                                                                                                                '발신자 '
                                                                                                                                '주소 '
                                                                                                                                '(from '
                                                                                                                                '필드)',
                                                                                                                 'type': 'string'}},
                                                                         'targetParam': 'client_filter',
                                                                         'type': 'object'},
                                                     'source': 'internal',
                                                     'targetParam': 'client_filter',
                                                     'type': 'ExcludeParams',
                                                     'value': {'exclude_from_address': 'block@krs.co.kr'}},
                                   'select': {'original_schema': {'properties': {'body_preview': {'default': True,
                                                                                                  'description': '메시지 '
                                                                                                                 '본문의 '
                                                                                                                 '처음 '
                                                                                                                 '255자 '
                                                                                                                 '(텍스트 '
                                                                                                                 '형식)',
                                                                                                  'type': 'boolean'},
                                                                                 'has_attachments': {'default': True,
                                                                                                     'description': '첨부파일 '
                                                                                                                    '포함 '
                                                                                                                    '여부',
                                                                                                     'type': 'boolean'},
                                                                                 'id': {'default': True,
                                                                                        'description': '메시지 '
                                                                                                       '고유 '
                                                                                                       '식별자 '
                                                                                                       '(읽기 '
                                                                                                       '전용)',
                                                                                        'type': 'boolean'},
                                                                                 'internet_message_id': {'default': True,
                                                                                                         'description': 'RFC2822 '
                                                                                                                        '형식의 '
                                                                                                                        '메시지 '
                                                                                                                        'ID',
                                                                                                         'type': 'boolean'},
                                                                                 'received_date_time': {'default': True,
                                                                                                        'description': '메시지 '
                                                                                                                       '수신 '
                                                                                                                       '날짜/시간 '
                                                                                                                       '(ISO '
                                                                                                                       '8601 '
                                                                                                                       '형식, '
                                                                                                                       'UTC)',
                                                                                                        'type': 'boolean'},
                                                                                 'sender': {'default': True,
                                                                                            'description': '메시지를 '
                                                                                                           '생성하는 '
                                                                                                           '데 '
                                                                                                           '사용된 '
                                                                                                           '계정',
                                                                                            'type': 'boolean'},
                                                                                 'subject': {'default': True,
                                                                                             'description': '메시지 '
                                                                                                            '제목',
                                                                                             'type': 'boolean'}},
                                                                  'targetParam': 'select_params',
                                                                  'type': 'object'},
                                              'source': 'internal',
                                              'targetParam': 'select_params',
                                              'type': 'SelectParams',
                                              'value': {'body_preview': True,
                                                        'has_attachments': True,
                                                        'id': True,
                                                        'internet_message_id': True,
                                                        'received_date_time': True,
                                                        'sender': True,
                                                        'subject': True}}},
                      'signature_defaults': {}},
 'mail_query_url': {'internal': {'select': {'original_schema': {'properties': {'body_preview': {'default': True,
                                                                                                'description': '메시지 '
                                                                                                               '본문의 '
                                                                                                               '처음 '
                                                                                                               '255자 '
                                                                                                               '(텍스트 '
                                                                                                               '형식)',
                                                                                                'type': 'boolean'},
                                                                               'created_date_time': {'default': True,
                                                                                                     'description': '메시지 '
                                                                                                                    '생성 '
                                                                                                                    '날짜/시간 '
                                                                                                                    '(ISO '
                                                                                                                    '8601 '
                                                                                                                    '형식, '
                                                                                                                    'UTC)',
                                                                                                     'type': 'boolean'},
                                                                               'from_recipient': {'default': True,
                                                                                                  'description': '메시지가 '
                                                                                                                 '전송된 '
                                                                                                                 '사서함의 '
                                                                                                                 '소유자 '
                                                                                                                 '(from '
                                                                                                                 '필드)',
                                                                                                  'type': 'boolean'},
                                                                               'id': {'default': True,
                                                                                      'description': '메시지 '
                                                                                                     '고유 '
                                                                                                     '식별자 '
                                                                                                     '(읽기 '
                                                                                                     '전용)',
                                                                                      'type': 'boolean'},
                                                                               'received_date_time': {'default': True,
                                                                                                      'description': '메시지 '
                                                                                                                     '수신 '
                                                                                                                     '날짜/시간 '
                                                                                                                     '(ISO '
                                                                                                                     '8601 '
                                                                                                                     '형식, '
                                                                                                                     'UTC)',
                                                                                                      'type': 'boolean'}},
                                                                'targetParam': 'select',
                                                                'type': 'object'},
                                            'source': 'internal',
                                            'targetParam': 'select',
                                            'type': 'SelectParams',
                                            'value': {'body_preview': True,
                                                      'created_date_time': True,
                                                      'from_recipient': True,
                                                      'id': True,
                                                      'received_date_time': True}}},
                    'signature_defaults': {}}}

# Legacy format for backward compatibility
INTERNAL_ARGS = {'mail_attachment_download': {'select_params': {'original_schema': {'properties': {'body': {'description': '메시지 '
                                                                                                           '본문 '
                                                                                                           '(HTML '
                                                                                                           '또는 '
                                                                                                           '텍스트 '
                                                                                                           '형식)',
                                                                                            'type': 'boolean'},
                                                                                   'categories': {'description': '메시지에 '
                                                                                                                 '연결된 '
                                                                                                                 '카테고리 '
                                                                                                                 '목록',
                                                                                                  'type': 'boolean'},
                                                                                   'change_key': {'description': '메시지 '
                                                                                                                 '버전 '
                                                                                                                 '키',
                                                                                                  'type': 'boolean'},
                                                                                   'created_date_time': {'description': '메시지 '
                                                                                                                        '생성 '
                                                                                                                        '날짜/시간 '
                                                                                                                        '(ISO '
                                                                                                                        '8601 '
                                                                                                                        '형식, '
                                                                                                                        'UTC)',
                                                                                                         'type': 'boolean'},
                                                                                   'id': {'description': '메시지 '
                                                                                                         '고유 '
                                                                                                         '식별자 '
                                                                                                         '(읽기 '
                                                                                                         '전용)',
                                                                                          'type': 'boolean'},
                                                                                   'last_modified_date_time': {'description': '메시지 '
                                                                                                                              '최종 '
                                                                                                                              '수정 '
                                                                                                                              '날짜/시간 '
                                                                                                                              '(ISO '
                                                                                                                              '8601 '
                                                                                                                              '형식, '
                                                                                                                              'UTC)',
                                                                                                               'type': 'boolean'},
                                                                                   'subject': {'description': '메시지 '
                                                                                                              '제목',
                                                                                               'type': 'boolean'}},
                                                                    'targetParam': 'select_params',
                                                                    'type': 'object'},
                                                'targetParam': 'select_params',
                                                'type': 'object',
                                                'value': {}}},
 'mail_attachment_meta': {'select_params': {'original_schema': {'properties': {'body': {'default': True,
                                                                                        'description': '메시지 '
                                                                                                       '본문 '
                                                                                                       '(HTML '
                                                                                                       '또는 '
                                                                                                       '텍스트 '
                                                                                                       '형식)',
                                                                                        'type': 'boolean'},
                                                                               'id': {'default': True,
                                                                                      'description': '메시지 '
                                                                                                     '고유 '
                                                                                                     '식별자 '
                                                                                                     '(읽기 '
                                                                                                     '전용)',
                                                                                      'type': 'boolean'},
                                                                               'received_date_time': {'default': True,
                                                                                                      'description': '메시지 '
                                                                                                                     '수신 '
                                                                                                                     '날짜/시간 '
                                                                                                                     '(ISO '
                                                                                                                     '8601 '
                                                                                                                     '형식, '
                                                                                                                     'UTC)',
                                                                                                      'type': 'boolean'},
                                                                               'subject': {'default': True,
                                                                                           'description': '메시지 '
                                                                                                          '제목',
                                                                                           'type': 'boolean'}},
                                                                'targetParam': 'select_params',
                                                                'type': 'object'},
                                            'targetParam': 'select_params',
                                            'type': 'SelectParams',
                                            'value': {'body': True,
                                                      'id': True,
                                                      'received_date_time': True,
                                                      'subject': True}}},
 'mail_list_keyword': {'select_params': {'original_schema': {'properties': {},
                                                             'targetParam': 'select_params',
                                                             'type': 'object'},
                                         'targetParam': 'select_params',
                                         'type': 'SelectParams',
                                         'value': {}}},
 'mail_list_period': {'client_filter': {'original_schema': {'properties': {'exclude_from_address': {'default': 'block@krs.co.kr',
                                                                                                    'description': '제외할 '
                                                                                                                   '발신자 '
                                                                                                                   '주소 '
                                                                                                                   '(from '
                                                                                                                   '필드)',
                                                                                                    'type': 'string'}},
                                                            'targetParam': 'client_filter',
                                                            'type': 'object'},
                                        'targetParam': 'client_filter',
                                        'type': 'ExcludeParams',
                                        'value': {'exclude_from_address': 'block@krs.co.kr'}},
                      'select': {'original_schema': {'properties': {'body_preview': {'default': True,
                                                                                     'description': '메시지 '
                                                                                                    '본문의 '
                                                                                                    '처음 '
                                                                                                    '255자 '
                                                                                                    '(텍스트 '
                                                                                                    '형식)',
                                                                                     'type': 'boolean'},
                                                                    'has_attachments': {'default': True,
                                                                                        'description': '첨부파일 '
                                                                                                       '포함 '
                                                                                                       '여부',
                                                                                        'type': 'boolean'},
                                                                    'id': {'default': True,
                                                                           'description': '메시지 '
                                                                                          '고유 '
                                                                                          '식별자 '
                                                                                          '(읽기 '
                                                                                          '전용)',
                                                                           'type': 'boolean'},
                                                                    'internet_message_id': {'default': True,
                                                                                            'description': 'RFC2822 '
                                                                                                           '형식의 '
                                                                                                           '메시지 '
                                                                                                           'ID',
                                                                                            'type': 'boolean'},
                                                                    'received_date_time': {'default': True,
                                                                                           'description': '메시지 '
                                                                                                          '수신 '
                                                                                                          '날짜/시간 '
                                                                                                          '(ISO '
                                                                                                          '8601 '
                                                                                                          '형식, '
                                                                                                          'UTC)',
                                                                                           'type': 'boolean'},
                                                                    'sender': {'default': True,
                                                                               'description': '메시지를 '
                                                                                              '생성하는 '
                                                                                              '데 '
                                                                                              '사용된 '
                                                                                              '계정',
                                                                               'type': 'boolean'},
                                                                    'subject': {'default': True,
                                                                                'description': '메시지 '
                                                                                               '제목',
                                                                                'type': 'boolean'}},
                                                     'targetParam': 'select_params',
                                                     'type': 'object'},
                                 'targetParam': 'select_params',
                                 'type': 'SelectParams',
                                 'value': {'body_preview': True,
                                           'has_attachments': True,
                                           'id': True,
                                           'internet_message_id': True,
                                           'received_date_time': True,
                                           'sender': True,
                                           'subject': True}}},
 'mail_query_url': {'select': {'original_schema': {'properties': {'body_preview': {'default': True,
                                                                                   'description': '메시지 '
                                                                                                  '본문의 '
                                                                                                  '처음 '
                                                                                                  '255자 '
                                                                                                  '(텍스트 '
                                                                                                  '형식)',
                                                                                   'type': 'boolean'},
                                                                  'created_date_time': {'default': True,
                                                                                        'description': '메시지 '
                                                                                                       '생성 '
                                                                                                       '날짜/시간 '
                                                                                                       '(ISO '
                                                                                                       '8601 '
                                                                                                       '형식, '
                                                                                                       'UTC)',
                                                                                        'type': 'boolean'},
                                                                  'from_recipient': {'default': True,
                                                                                     'description': '메시지가 '
                                                                                                    '전송된 '
                                                                                                    '사서함의 '
                                                                                                    '소유자 '
                                                                                                    '(from '
                                                                                                    '필드)',
                                                                                     'type': 'boolean'},
                                                                  'id': {'default': True,
                                                                         'description': '메시지 '
                                                                                        '고유 '
                                                                                        '식별자 '
                                                                                        '(읽기 '
                                                                                        '전용)',
                                                                         'type': 'boolean'},
                                                                  'received_date_time': {'default': True,
                                                                                         'description': '메시지 '
                                                                                                        '수신 '
                                                                                                        '날짜/시간 '
                                                                                                        '(ISO '
                                                                                                        '8601 '
                                                                                                        '형식, '
                                                                                                        'UTC)',
                                                                                         'type': 'boolean'}},
                                                   'targetParam': 'select',
                                                   'type': 'object'},
                               'targetParam': 'select',
                               'type': 'SelectParams',
                               'value': {'body_preview': True,
                                         'created_date_time': True,
                                         'from_recipient': True,
                                         'id': True,
                                         'received_date_time': True}}}}

# Build INTERNAL_ARG_TYPES dynamically based on imported types
INTERNAL_ARG_TYPES = {}
if 'ExcludeParams' in globals():
    INTERNAL_ARG_TYPES['ExcludeParams'] = ExcludeParams
if 'FilterParams' in globals():
    INTERNAL_ARG_TYPES['FilterParams'] = FilterParams
if 'SelectParams' in globals():
    INTERNAL_ARG_TYPES['SelectParams'] = SelectParams


def extract_schema_defaults(arg_info: dict) -> dict:
    """Extract default values from original_schema.properties."""
    original_schema = arg_info.get("original_schema", {})
    properties = original_schema.get("properties", {})
    defaults = {}
    for prop_name, prop_def in properties.items():
        if "default" in prop_def:
            defaults[prop_name] = prop_def["default"]
    return defaults


def build_internal_param(tool_name: str, arg_name: str, runtime_value: dict = None):
    """Instantiate internal parameter object for a tool.

    Value resolution priority:
    1. runtime_value: Dynamic value passed from function arguments at runtime
    2. stored value: Value from INTERNAL_ARGS (generated from mcp_service_factors)
    3. defaults: Static value from original_schema.properties
    """
    arg_info = INTERNAL_ARGS.get(tool_name, {}).get(arg_name)
    if not arg_info:
        return None

    param_cls = INTERNAL_ARG_TYPES.get(arg_info.get("type"))
    if not param_cls:
        logger.warning(f"Unknown internal arg type for {tool_name}.{arg_name}: {arg_info.get('type')}")
        return None

    defaults = extract_schema_defaults(arg_info)
    stored_value = arg_info.get("value")

    if runtime_value is not None and runtime_value != {}:
        final_value = {**defaults, **runtime_value}
    elif stored_value is not None and stored_value != {}:
        final_value = {**defaults, **stored_value}
    else:
        final_value = defaults

    if not final_value:
        return param_cls()

    try:
        return param_cls(**final_value)
    except Exception as exc:
        logger.warning(f"Failed to build internal arg {tool_name}.{arg_name}: {exc}")
        return None


def get_signature_defaults(tool_name: str, factor_name: str) -> dict:
    """Get signature default values for a tool factor.

    Signature defaults are used to provide default values for user input parameters.
    These are applied when the user doesn't provide a value for an optional parameter.
    """
    tool_factors = SERVICE_FACTORS.get(tool_name, {})
    sig_defaults = tool_factors.get('signature_defaults', {})
    factor_info = sig_defaults.get(factor_name, {})
    return factor_info.get('value', {})


def apply_signature_defaults(signature_data: dict, tool_name: str, factor_name: str) -> dict:
    """Apply signature defaults to user-provided data.

    Merge order (priority high to low):
    1. User signature values (non-None)
    2. Signature defaults
    3. Schema defaults
    """
    if signature_data is None:
        signature_data = {}

    # Get signature defaults
    defaults = get_signature_defaults(tool_name, factor_name)
    if not defaults:
        return signature_data

    # Merge: defaults first, then user values override
    merged = {**defaults}
    for key, value in signature_data.items():
        if value is not None:
            merged[key] = value

    return merged


def merge_with_priority(signature_value, signature_defaults_value, internal_value):
    """Merge values with priority: Signature > Signature Defaults > Internal.

    Args:
        signature_value: User-provided value from LLM
        signature_defaults_value: Default value for user input
        internal_value: Hidden system value

    Returns:
        Final merged value with correct priority
    """
    # If all are None, return None
    if signature_value is None and signature_defaults_value is None and internal_value is None:
        return None

    # If signature has value, use it (possibly merged with defaults for objects)
    if signature_value is not None:
        # For dict/object types, merge with signature_defaults
        if isinstance(signature_value, dict):
            base = {}
            if internal_value and isinstance(internal_value, dict):
                base = {**internal_value}
            if signature_defaults_value and isinstance(signature_defaults_value, dict):
                base = {**base, **signature_defaults_value}
            return {**base, **signature_value}
        return signature_value

    # If signature is None but signature_defaults has value
    if signature_defaults_value is not None:
        if isinstance(signature_defaults_value, dict):
            base = {}
            if internal_value and isinstance(internal_value, dict):
                base = {**internal_value}
            return {**base, **signature_defaults_value}
        return signature_defaults_value

    # Fall back to internal value
    return internal_value


def model_to_dict(model):
    if model is None:
        return {}
    if isinstance(model, dict):
        return model
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)
    if hasattr(model, "dict"):
        return model.dict(exclude_none=True)
    return {}


def merge_param_data(internal_data: dict, runtime_data, signature_defaults: dict = None):
    """Merge parameter data with priority: runtime > signature_defaults > internal.

    Args:
        internal_data: Internal override data (lowest priority, not used for signature params)
        runtime_data: User-provided runtime data (highest priority)
        signature_defaults: Default values for signature params (middle priority)
    """
    # Start with internal data as base (if any)
    result = dict(internal_data) if internal_data else {}

    # Apply signature defaults (overrides internal)
    if signature_defaults:
        result = {**result, **signature_defaults}

    # Apply runtime data (highest priority, overrides all)
    if runtime_data:
        if isinstance(runtime_data, dict):
            result = {**result, **runtime_data}
        else:
            return runtime_data

    return result if result else None

# Tool handler functions

async def handle_mail_list_period(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_list_period tool call"""

    # Extract parameters from args
    # Extract from input with source param name
    user_email = args["user_email"]
    DatePeriodFilter_raw = args.get("DatePeriodFilter")
    DatePeriodFilter = DatePeriodFilter_raw if DatePeriodFilter_raw is not None else None

    # Convert dicts to parameter objects where needed
    # Pre-computed defaults by targetParam: filter_params
    DatePeriodFilter_internal_defaults = {}
    DatePeriodFilter_sig_defaults = {}
    # Merge: Internal < Signature Defaults < Signature (user input)
    DatePeriodFilter_data = merge_param_data(DatePeriodFilter_internal_defaults, DatePeriodFilter, DatePeriodFilter_sig_defaults)
    if DatePeriodFilter_data is not None:
        DatePeriodFilter = FilterParams(**DatePeriodFilter_data)
    else:
        DatePeriodFilter = None
    # Prepare call arguments
    call_args = {}

    # Add signature parameters
    call_args["user_email"] = user_email
    call_args["filter_params"] = DatePeriodFilter
    # Add internal args (Internal has different targetParam from Signature, no overlap)
    call_args["client_filter"] = ExcludeParams(**{'exclude_from_address': 'block@krs.co.kr'})
    call_args["select_params"] = SelectParams(**{'body_preview': True,
 'has_attachments': True,
 'id': True,
 'internet_message_id': True,
 'received_date_time': True,
 'sender': True,
 'subject': True})

    return await mail_service.query_mail_list(**call_args)

async def handle_mail_list_keyword(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_list_keyword tool call"""

    # Extract parameters from args
    # Extract from input with source param name
    user_email = args["user_email"]
    # Extract from input with source param name
    search_keywords = args["search_keywords"]
    top_raw = args.get("top")
    top = top_raw if top_raw is not None else 50

    return await mail_service.fetch_search(
        user_email=user_email,
        search_term=search_keywords,
        top=top
    )

async def handle_mail_query_if_emaidID(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_query_if_emaidID tool call"""

    # Extract parameters from args
    # Extract from input with source param name
    user_email = args["user_email"]
    # Extract from input with source param name
    message_ids = args["message_ids"]

    return await mail_service.batch_and_fetch(
        user_email=user_email,
        message_ids=message_ids
    )

async def handle_mail_attachment_meta(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_attachment_meta tool call"""

    # Extract parameters from args
    # Extract from input with source param name
    user_email = args["user_email"]
    # Extract from input with source param name
    message_ids = args["message_ids"]

    return await mail_service.fetch_attachments_metadata(
        user_email=user_email,
        message_ids=message_ids
    )

async def handle_mail_attachment_download(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_attachment_download tool call"""

    # Extract parameters from args
    # Extract from input with source param name
    user_email = args["user_email"]
    # Extract from input with source param name
    message_attachment_ids = args["message_attachment_ids"]
    save_directory_raw = args.get("save_directory")
    save_directory = save_directory_raw if save_directory_raw is not None else 'downloads'
    skip_duplicates_raw = args.get("skip_duplicates")
    skip_duplicates = skip_duplicates_raw if skip_duplicates_raw is not None else True

    return await mail_service.download_attachments(
        user_email=user_email,
        message_attachment_ids=message_attachment_ids,
        save_directory=save_directory,
        skip_duplicates=skip_duplicates
    )

async def handle_mail_fetch_filter(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_fetch_filter tool call"""

    # Extract parameters from args
    # Extract from input with source param name
    user_email = args["user_email"]
    filter_params_raw = args.get("filter_params")
    filter_params = filter_params_raw if filter_params_raw is not None else None
    exclude_params_raw = args.get("exclude_params")
    exclude_params = exclude_params_raw if exclude_params_raw is not None else None

    # Convert dicts to parameter objects where needed
    # Pre-computed defaults by targetParam: filter_params
    filter_params_internal_defaults = {}
    filter_params_sig_defaults = {'test_field': 'test_value'}
    # Merge: Internal < Signature Defaults < Signature (user input)
    filter_params_data = merge_param_data(filter_params_internal_defaults, filter_params, filter_params_sig_defaults)
    if filter_params_data is not None:
        filter_params = FilterParams(**filter_params_data)
    else:
        filter_params = None
    # Pre-computed defaults by targetParam: exclude_params
    exclude_params_internal_defaults = {}
    exclude_params_sig_defaults = {}
    # Merge: Internal < Signature Defaults < Signature (user input)
    exclude_params_data = merge_param_data(exclude_params_internal_defaults, exclude_params, exclude_params_sig_defaults)
    if exclude_params_data is not None:
        exclude_params = ExcludeParams(**exclude_params_data)
    else:
        exclude_params = None
    # Prepare call arguments
    call_args = {}

    # Add signature parameters
    call_args["user_email"] = user_email
    call_args["filter_params"] = filter_params
    call_args["exclude_params"] = exclude_params

    return await mail_service.fetch_filter(**call_args)

async def handle_mail_fetch_search(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_fetch_search tool call"""

    # Extract parameters from args
    # Extract from input with source param name
    user_email = args["user_email"]
    # Extract from input with source param name
    search_term = args["search_term"]
    select_params_raw = args.get("select_params")
    select_params = select_params_raw if select_params_raw is not None else None
    top_raw = args.get("top")
    top = top_raw if top_raw is not None else 50

    # Convert dicts to parameter objects where needed
    # Pre-computed defaults by targetParam: select_params
    select_params_internal_defaults = {}
    select_params_sig_defaults = {}
    # Merge: Internal < Signature Defaults < Signature (user input)
    select_params_data = merge_param_data(select_params_internal_defaults, select_params, select_params_sig_defaults)
    if select_params_data is not None:
        select_params = SelectParams(**select_params_data)
    else:
        select_params = None
    # Prepare call arguments
    call_args = {}

    # Add signature parameters
    call_args["user_email"] = user_email
    call_args["search_term"] = search_term
    call_args["select_params"] = select_params
    call_args["top"] = top

    return await mail_service.fetch_search(**call_args)

async def handle_mail_process_with_download(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_process_with_download tool call"""

    # Extract parameters from args
    # Extract from input with source param name
    user_email = args["user_email"]
    filter_params_raw = args.get("filter_params")
    filter_params = filter_params_raw if filter_params_raw is not None else None
    search_term_raw = args.get("search_term")
    search_term = search_term_raw if search_term_raw is not None else None
    top_raw = args.get("top")
    top = top_raw if top_raw is not None else 50
    save_directory_raw = args.get("save_directory")
    save_directory = save_directory_raw if save_directory_raw is not None else None

    # Convert dicts to parameter objects where needed
    # Pre-computed defaults by targetParam: filter_params
    filter_params_internal_defaults = {}
    filter_params_sig_defaults = {}
    # Merge: Internal < Signature Defaults < Signature (user input)
    filter_params_data = merge_param_data(filter_params_internal_defaults, filter_params, filter_params_sig_defaults)
    if filter_params_data is not None:
        filter_params = FilterParams(**filter_params_data)
    else:
        filter_params = None
    # Prepare call arguments
    call_args = {}

    # Add signature parameters
    call_args["user_email"] = user_email
    call_args["filter_params"] = filter_params
    call_args["search_term"] = search_term
    call_args["top"] = top
    call_args["save_directory"] = save_directory

    return await mail_service.process_with_download(**call_args)

async def handle_mail_query_url(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_query_url tool call"""

    # Extract parameters from args
    # Extract from input with source param name
    user_email = args["user_email"]
    # Extract from input with source param name
    url = args["url"]
    filter_params_raw = args.get("filter_params")
    filter_params = filter_params_raw if filter_params_raw is not None else None
    top_raw = args.get("top")
    top = top_raw if top_raw is not None else 50

    # Convert dicts to parameter objects where needed
    # Pre-computed defaults by targetParam: filter_params
    filter_params_internal_defaults = {}
    filter_params_sig_defaults = {}
    # Merge: Internal < Signature Defaults < Signature (user input)
    filter_params_data = merge_param_data(filter_params_internal_defaults, filter_params, filter_params_sig_defaults)
    if filter_params_data is not None:
        filter_params = FilterParams(**filter_params_data)
    else:
        filter_params = None
    # Prepare call arguments
    call_args = {}

    # Add signature parameters
    call_args["user_email"] = user_email
    call_args["url"] = url
    call_args["filter_params"] = filter_params
    call_args["top"] = top
    # Add internal args (Internal has different targetParam from Signature, no overlap)
    call_args["select"] = SelectParams(**{'body_preview': True,
 'created_date_time': True,
 'from_recipient': True,
 'id': True,
 'received_date_time': True})

    return await mail_service.fetch_url(**call_args)

# ============================================================
# STDIO Protocol Implementation for MCP Server
# ============================================================
# Note: This template is included by universal_server_template.jinja2
# All common imports and utilities are defined in the parent template

# Configure logging for STDIO (stderr to avoid interfering with stdout)
# Override the parent's logger to use stderr
import sys
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Important: use stderr for logging
)
logger = logging.getLogger(__name__)

class StdioMCPServer:
    """MCP STDIO Protocol Server

    Handles MCP protocol communication via standard input/output using JSON-RPC format.
    Messages are delimited by newlines for easy parsing.
    """

    def __init__(self):
        self.running = False
        self.request_id_counter = 0
        logger.info(f"Outlook MCP Server STDIO Server initialized")

    async def read_message(self) -> Optional[Dict[str, Any]]:
        """Read a single JSON-RPC message from stdin"""
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                return None

            message = json.loads(line.strip())
            logger.debug(f"Received message: {message}")
            return message
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading message: {e}")
            return None

    def write_message(self, message: Dict[str, Any]):
        """Write a JSON-RPC message to stdout"""
        try:
            json_str = json.dumps(message, ensure_ascii=False)
            sys.stdout.write(json_str + '\n')
            sys.stdout.flush()
            logger.debug(f"Sent message: {message}")
        except Exception as e:
            logger.error(f"Error writing message: {e}")

    def send_error(self, request_id: Any, code: int, message: str, data: Any = None):
        """Send JSON-RPC error response"""
        error_response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
        if data is not None:
            error_response["error"]["data"] = data
        self.write_message(error_response)

    def send_result(self, request_id: Any, result: Any):
        """Send JSON-RPC success response"""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        self.write_message(response)

    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request"""
        client_info = params.get("clientInfo", {})
        logger.info(f"Client connected: {client_info.get('name', 'unknown')}")

        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "outlook",
                "version": "1.0.0"
            }
        }

    async def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request"""
        return {"tools": MCP_TOOLS}

    def apply_schema_defaults(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values from inputSchema to arguments if not provided."""
        tool_config = get_tool_config(tool_name)
        if not tool_config:
            return arguments

        input_schema = tool_config.get("inputSchema", {})
        properties = input_schema.get("properties", {})

        # Create a copy of arguments to avoid modifying the original
        merged_args = dict(arguments) if arguments else {}

        # Apply defaults for properties that have them and are not in arguments
        for prop_name, prop_def in properties.items():
            if prop_name not in merged_args and "default" in prop_def:
                merged_args[prop_name] = prop_def["default"]
                logger.debug(f"Applied default for {prop_name}: {prop_def['default']}")

        return merged_args

    async def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            raise ValueError("Tool name is required")

        # Apply default values from inputSchema
        arguments = self.apply_schema_defaults(tool_name, arguments)

        # Look up the handler function
        handler_name = f"handle_{tool_name.replace('-', '_')}"
        if handler_name not in globals():
            raise ValueError(f"Unknown tool: {tool_name}")

        try:
            # Call the tool handler
            result = await globals()[handler_name](arguments)

            # Format result for MCP
            if isinstance(result, dict) and "content" in result:
                return result
            elif isinstance(result, str):
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ]
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2)
                        }
                    ]
                }
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            raise

    async def handle_request(self, request: Dict[str, Any]):
        """Handle a single JSON-RPC request"""
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if not method:
            self.send_error(request_id, -32600, "Invalid Request: missing method")
            return

        try:
            # Route to appropriate handler based on method
            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                result = await self.handle_tools_list(params)
            elif method == "tools/call":
                result = await self.handle_tools_call(params)
            elif method == "shutdown":
                logger.info("Shutdown requested")
                self.running = False
                result = {}
            elif method == "ping":
                result = {"pong": True}
            else:
                self.send_error(request_id, -32601, f"Method not found: {method}")
                return

            # Send successful response
            self.send_result(request_id, result)

        except ValueError as e:
            self.send_error(request_id, -32602, f"Invalid params: {str(e)}")
        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            self.send_error(request_id, -32603, f"Internal error: {str(e)}")

    async def handle_notification(self, notification: Dict[str, Any]):
        """Handle JSON-RPC notifications (no response expected)"""
        method = notification.get("method")
        params = notification.get("params", {})

        logger.info(f"Received notification: {method}")

        # Notifications don't require responses
        if method == "notifications/initialized":
            logger.info("Client initialization complete")
        elif method == "cancelled":
            logger.info(f"Request cancelled: {params.get('id')}")
        elif method == "progress":
            logger.info(f"Progress update: {params}")
        # Add more notification handlers as needed

    async def run(self):
        """Main server loop"""
        self.running = True

        # Initialize services before starting
        if hasattr(mail_service, 'initialize'):
            await mail_service.initialize()
            logger.info("MailService initialized")

        logger.info(f"Outlook MCP Server STDIO Server started")
        logger.info("Waiting for messages on stdin...")

        # Send server ready notification
        self.write_message({
            "jsonrpc": "2.0",
            "method": "server.ready",
            "params": {}
        })

        try:
            while self.running:
                # Read next message
                message = await self.read_message()

                if message is None:
                    # EOF or error - exit gracefully
                    logger.info("Input stream closed, shutting down")
                    break

                # Check if it's a request or notification
                if "id" in message:
                    # Request - requires response
                    await self.handle_request(message)
                else:
                    # Notification - no response needed
                    await self.handle_notification(message)

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
        finally:
            logger.info("Outlook MCP Server STDIO Server stopped")

# Main entry point for STDIO protocol
async def handle_stdio():
    """Handle MCP protocol via stdin/stdout"""
    server = StdioMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(handle_stdio())