"""
MCP Tool Definition Templates - AUTO-GENERATED
Signatures extracted from source code using AST parsing
"""
from typing import List, Dict, Any

MCP_TOOLS: List[Dict[str, Any]] = [   {   'description': '필터 방식 메일 조회 기능',
        'inputSchema': {   'properties': {   'exclude_params': {   'baseModel': 'ExcludeParams',
                                                                   'description': '제외 조건',
                                                                   'type': 'object'},
                                             'filter_params': {   'baseModel': 'FilterParams',
                                                                  'description': '메일 필터링 조건',
                                                                  'properties': {   'received_date_from': {   'description': '메일 '
                                                                                                                             '수신 '
                                                                                                                             '시작 '
                                                                                                                             '날짜 '
                                                                                                                             '(포함, '
                                                                                                                             'receivedDateTime '
                                                                                                                             '>= '
                                                                                                                             '이 '
                                                                                                                             '값)',
                                                                                                              'type': 'string'},
                                                                                    'received_date_to': {   'description': '메일 '
                                                                                                                           '수신 '
                                                                                                                           '종료 '
                                                                                                                           '날짜 '
                                                                                                                           '(포함, '
                                                                                                                           'receivedDateTime '
                                                                                                                           '<= '
                                                                                                                           '이 '
                                                                                                                           '값)',
                                                                                                            'type': 'string'},
                                                                                    'sent_date_from': {   'description': '메일 '
                                                                                                                         '발신 '
                                                                                                                         '시작 '
                                                                                                                         '날짜 '
                                                                                                                         '(포함, '
                                                                                                                         'sentDateTime '
                                                                                                                         '>= '
                                                                                                                         '이 '
                                                                                                                         '값)',
                                                                                                          'type': 'string'},
                                                                                    'sent_date_to': {   'description': '메일 '
                                                                                                                       '발신 '
                                                                                                                       '종료 '
                                                                                                                       '날짜 '
                                                                                                                       '(포함, '
                                                                                                                       'sentDateTime '
                                                                                                                       '<= '
                                                                                                                       '이 '
                                                                                                                       '값)',
                                                                                                        'type': 'string'}},
                                                                  'type': 'object'}},
                           'required': [],
                           'type': 'object'},
        'mcp_service': {   'name': 'fetch_filter',
                           'parameters': [   {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'filter_params',
                                                 'type': 'Optional[FilterParams]'},
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'exclude_params',
                                                 'type': 'Optional[ExcludeParams]'},
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'select_params',
                                                 'type': 'Optional[SelectParams]'},
                                             {   'default': 50,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'top',
                                                 'type': 'int'}],
                           'signature': 'filter_params: Optional[FilterParams] = None, exclude_params: '
                                        'Optional[ExcludeParams] = None, select_params: Optional[SelectParams] = None, '
                                        'top: int = 50'},
        'name': 'handler_mail_fetch_filter'},
    {   'description': '검색 방식 메일 조회 기능',
        'inputSchema': {   'properties': {   'search_term': {'description': '검색어 ($search 파라미터)', 'type': 'string'},
                                             'select_params': {   'baseModel': 'SelectParams',
                                                                  'description': '조회할 필드 선택',
                                                                  'properties': {   'fields': {   'description': '조회할 '
                                                                                                                 '필드 '
                                                                                                                 '목록',
                                                                                                  'items': {   'type': 'string'},
                                                                                                  'type': 'array'}},
                                                                  'type': 'object'},
                                             'top': {'default': 50, 'description': '반환할 최대 메일 수', 'type': 'integer'}},
                           'required': ['search_term'],
                           'type': 'object'},
        'mcp_service': {   'name': 'fetch_search',
                           'parameters': [   {   'default': None,
                                                 'has_default': False,
                                                 'is_required': True,
                                                 'name': 'search_term',
                                                 'type': 'str'},
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'select_params',
                                                 'type': 'Optional[SelectParams]'},
                                             {   'default': 50,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'top',
                                                 'type': 'int'}],
                           'signature': 'search_term: str, select_params: Optional[SelectParams] = None, top: int = '
                                        '50'},
        'name': 'handler_mail_fetch_search'},
    {   'description': '첨부파일 다운로드 포함 메일 처리 기능',
        'inputSchema': {   'properties': {   'filter_params': {   'baseModel': 'FilterParams',
                                                                  'description': '메일 필터링 조건',
                                                                  'properties': {   'received_date_from': {   'description': '메일 '
                                                                                                                             '수신 '
                                                                                                                             '시작 '
                                                                                                                             '날짜',
                                                                                                              'type': 'string'},
                                                                                    'received_date_to': {   'description': '메일 '
                                                                                                                           '수신 '
                                                                                                                           '종료 '
                                                                                                                           '날짜',
                                                                                                            'type': 'string'}},
                                                                  'type': 'object'},
                                             'save_directory': {'description': '첨부파일 저장 디렉토리 경로', 'type': 'string'},
                                             'search_term': {'description': '검색어 (지정시 검색 모드로 전환)', 'type': 'string'},
                                             'top': {'default': 50, 'description': '반환할 최대 메일 수', 'type': 'integer'}},
                           'required': [],
                           'type': 'object'},
        'mcp_service': {   'name': 'process_with_download',
                           'parameters': [   {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'filter_params',
                                                 'type': 'Optional[FilterParams]'},
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'search_term',
                                                 'type': 'Optional[str]'},
                                             {   'default': 50,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'top',
                                                 'type': 'int'},
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'save_directory',
                                                 'type': 'Optional[str]'}],
                           'signature': 'filter_params: Optional[FilterParams] = None, search_term: Optional[str] = '
                                        'None, top: int = 50, save_directory: Optional[str] = None'},
        'name': 'handler_mail_process_with_download'}]
