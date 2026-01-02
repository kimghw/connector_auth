"""
MCP Tool Definition Templates - AUTO-GENERATED
Signatures extracted from source code using AST parsing
"""
from typing import List, Dict, Any

MCP_TOOLS: List[Dict[str, Any]] = [   {   'description': '필터 방식 메일 조회 기능',
        'inputSchema': {   'properties': {   'exclude_params': {   'baseModel': 'ExcludeParams',
                                                                   'description': '제외 조건',
                                                                   'targetParam': 'exclude_params',
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
                                                                  'targetParam': 'filter_params',
                                                                  'type': 'object'}},
                           'required': [],
                           'type': 'object'},
        'mcp_service': {   'name': 'fetch_filter',
                           'parameters': [   {   'default': None,
                                                 'has_default': False,
                                                 'is_required': True,
                                                 'name': 'user_email',
                                                 'type': 'str'},
                                             {   'default': None,
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
                           'signature': 'user_email: str, filter_params: Optional[FilterParams] = None, '
                                        'exclude_params: Optional[ExcludeParams] = None, select_params: '
                                        'Optional[SelectParams] = None, top: int = 50'},
        'mcp_service_factors': {   'exclude_params_internal': {   'baseModel': 'ExcludeParams',
                                                                  'description': 'ExcludeParams parameters',
                                                                  'parameters': {   'exclude_body_keywords': {   'description': '본문에서 '
                                                                                                                                '제외할 '
                                                                                                                                '키워드 '
                                                                                                                                '목록',
                                                                                                                 'type': 'string'},
                                                                                    'exclude_from_address': {   'description': '제외할 '
                                                                                                                               '발신자 '
                                                                                                                               '주소 '
                                                                                                                               '(from '
                                                                                                                               '필드)',
                                                                                                                'type': 'string'},
                                                                                    'exclude_preview_keywords': {   'description': '미리보기에서 '
                                                                                                                                   '제외할 '
                                                                                                                                   '키워드 '
                                                                                                                                   '목록',
                                                                                                                    'type': 'string'},
                                                                                    'exclude_sender_address': {   'description': '제외할 '
                                                                                                                                 '실제 '
                                                                                                                                 '발신자 '
                                                                                                                                 '주소 '
                                                                                                                                 '(sender '
                                                                                                                                 '필드)',
                                                                                                                  'type': 'string'},
                                                                                    'exclude_subject_keywords': {   'description': '제목에서 '
                                                                                                                                   '제외할 '
                                                                                                                                   '키워드 '
                                                                                                                                   '목록',
                                                                                                                    'type': 'string'}},
                                                                  'source': 'internal'}},
        'name': 'mail_fetch_filter'},
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
                                                 'name': 'user_email',
                                                 'type': 'str'},
                                             {   'default': None,
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
                           'signature': 'user_email: str, search_term: str, select_params: Optional[SelectParams] = '
                                        'None, top: int = 50'},
        'name': 'mail_fetch_search'},
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
                                                 'has_default': False,
                                                 'is_required': True,
                                                 'name': 'user_email',
                                                 'type': 'str'},
                                             {   'default': None,
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
                           'signature': 'user_email: str, filter_params: Optional[FilterParams] = None, search_term: '
                                        'Optional[str] = None, top: int = 50, save_directory: Optional[str] = None'},
        'name': 'mail_process_with_download'},
    {   'description': '특정 기간 동안 메일조회하고 body를 제외하고 대략적인 내용만 추출할 수 있는 데이터만 수신하여 테이블로 정리하는 도구 입니다. ',
        'inputSchema': {   'properties': {   'DatePeriodFilter': {   'baseModel': 'FilterParams',
                                                                     'description': '에이전트는 는 사용자의 질의에 따라 검색 범위의 날짜를 '
                                                                                    '추출한다. ',
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
                                                                                                               'type': 'string'}},
                                                                     'required': [   'received_date_from',
                                                                                     'received_date_to'],
                                                                     'targetParam': 'filter_params',
                                                                     'type': 'object'},
                                             'user_email': {   'description': '이메일 주소를 입력하고 입력하지 않을 경우 내부에서 연결정보를 메일 '
                                                                              '주소를 추정함',
                                                               'type': 'string'}},
                           'required': ['DatePeriodFilter'],
                           'type': 'object'},
        'mcp_service': 'query_mail_list',
        'mcp_service_factors': {   'client_filter': {   'baseModel': 'ExcludeParams',
                                                        'description': 'ExcludeParams parameters',
                                                        'parameters': {   'exclude_from_address': {   'default': 'block@krs.co.kr',
                                                                                                      'description': '제외할 '
                                                                                                                     '발신자 '
                                                                                                                     '주소 '
                                                                                                                     '(from '
                                                                                                                     '필드)',
                                                                                                      'type': 'string'}},
                                                        'source': 'internal'}},
        'name': 'mail_list'},
    {   'description': 'URL 방식 메일 조회 기능 - $filter 와 $select를 설정 가능',
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
                                                                  'required': [],
                                                                  'targetParam': 'filter_params',
                                                                  'type': 'object'},
                                             'select': {   'baseModel': 'SelectParams',
                                                           'description': 'SelectParams parameters',
                                                           'properties': {   'body_preview': {   'description': '메시지 '
                                                                                                                '본문의 '
                                                                                                                '처음 '
                                                                                                                '255자 '
                                                                                                                '(텍스트 '
                                                                                                                '형식)',
                                                                                                 'type': 'boolean'},
                                                                             'created_date_time': {   'description': '메시지 '
                                                                                                                     '생성 '
                                                                                                                     '날짜/시간 '
                                                                                                                     '(ISO '
                                                                                                                     '8601 '
                                                                                                                     '형식, '
                                                                                                                     'UTC)',
                                                                                                      'type': 'boolean'},
                                                                             'from_recipient': {   'description': '메시지가 '
                                                                                                                  '전송된 '
                                                                                                                  '사서함의 '
                                                                                                                  '소유자 '
                                                                                                                  '(from '
                                                                                                                  '필드)',
                                                                                                   'type': 'boolean'},
                                                                             'id': {   'description': '메시지 고유 식별자 (읽기 '
                                                                                                      '전용)',
                                                                                       'type': 'boolean'},
                                                                             'received_date_time': {   'description': '메시지 '
                                                                                                                      '수신 '
                                                                                                                      '날짜/시간 '
                                                                                                                      '(ISO '
                                                                                                                      '8601 '
                                                                                                                      '형식, '
                                                                                                                      'UTC)',
                                                                                                       'type': 'boolean'}},
                                                           'required': [],
                                                           'targetParam': 'select_params',
                                                           'type': 'object'},
                                             'top': {'default': 50, 'description': '최대 결과 수', 'type': 'integer'},
                                             'url': {   'default': 'https://graph.microsoft.com/v1.0/me/mailFolders/junkemail/messages?',
                                                        'description': 'only baseURL : '
                                                                       'https://graph.microsoft.com/v1.0/me/mailFolders/junkemail/messages?',
                                                        'targetParam': 'url',
                                                        'type': 'string'},
                                             'user_email': {'description': '사용자 이메일 (인증용)', 'type': 'string'}},
                           'required': ['url', 'user_email'],
                           'type': 'object'},
        'mcp_service': 'fetch_url',
        'name': 'mail_query_url'}]
