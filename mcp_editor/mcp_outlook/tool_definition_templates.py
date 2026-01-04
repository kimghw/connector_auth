"""
MCP Tool Definition Templates - AUTO-GENERATED
Signatures extracted from source code using AST parsing
"""
from typing import List, Dict, Any

MCP_TOOLS: List[Dict[str, Any]] = [   {   'description': 'Outlook 메일을 날짜, 발신자, 제목 등 다양한 필터 조건을 사용하여 조회합니다. 특정 기간이나 조건에 맞는 메일을 효율적으로 검색할 수 있습니다. '
                       'mail_list_xx 와 달리 본문을 포함해서 반환한다.',
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
                                                                  'type': 'object'},
                                             'user_email': {'description': '', 'type': 'string'}},
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
                                                                  'parameters': {   'exclude_body_keywords': {   'default': None,
                                                                                                                 'description': '본문에서 '
                                                                                                                                '제외할 '
                                                                                                                                '키워드 '
                                                                                                                                '목록',
                                                                                                                 'type': 'string'},
                                                                                    'exclude_from_address': {   'default': None,
                                                                                                                'description': '제외할 '
                                                                                                                               '발신자 '
                                                                                                                               '주소 '
                                                                                                                               '(from '
                                                                                                                               '필드)',
                                                                                                                'type': 'string'},
                                                                                    'exclude_preview_keywords': {   'default': None,
                                                                                                                    'description': '미리보기에서 '
                                                                                                                                   '제외할 '
                                                                                                                                   '키워드 '
                                                                                                                                   '목록',
                                                                                                                    'type': 'string'},
                                                                                    'exclude_sender_address': {   'default': None,
                                                                                                                  'description': '제외할 '
                                                                                                                                 '실제 '
                                                                                                                                 '발신자 '
                                                                                                                                 '주소 '
                                                                                                                                 '(sender '
                                                                                                                                 '필드)',
                                                                                                                  'type': 'string'},
                                                                                    'exclude_subject_keywords': {   'default': None,
                                                                                                                    'description': '제목에서 '
                                                                                                                                   '제외할 '
                                                                                                                                   '키워드 '
                                                                                                                                   '목록',
                                                                                                                    'type': 'string'}},
                                                                  'source': 'internal'}},
        'name': 'mail_fetch_filter'},
    {   'description': 'Outlook 메일을 키워드로 검색합니다. 제목, 본문, 발신자 등 모든 필드에서 지정한 검색어를 포함하는 메일을 찾아 반환합니다.',
        'inputSchema': {   'properties': {   'search_term': {'description': '검색어 ($search 파라미터)', 'type': 'string'},
                                             'select_params': {   'baseModel': 'SelectParams',
                                                                  'description': '조회할 필드 선택',
                                                                  'properties': {   'fields': {   'description': '조회할 '
                                                                                                                 '필드 '
                                                                                                                 '목록',
                                                                                                  'items': {   'type': 'string'},
                                                                                                  'type': 'array'}},
                                                                  'type': 'object'},
                                             'top': {'default': 50, 'description': '반환할 최대 메일 수', 'type': 'integer'},
                                             'user_email': {'description': '', 'type': 'string'}},
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
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'client_filter',
                                                 'type': 'Optional[ExcludeParams]'},
                                             {   'default': 50,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'top',
                                                 'type': 'int'}],
                           'signature': 'user_email: str, search_term: str, select_params: Optional[SelectParams] = '
                                        'None, client_filter: Optional[ExcludeParams] = None, top: int = 50'},
        'name': 'mail_fetch_search'},
    {   'description': '메일을 조회하고 첨부파일이 있는 경우 자동으로 다운로드합니다. 필터나 검색 조건으로 메일을 찾은 후 첨부파일을 지정된 폴더에 저장합니다.',
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
                                             'top': {'default': 50, 'description': '반환할 최대 메일 수', 'type': 'integer'},
                                             'user_email': {'description': '', 'type': 'string'}},
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
    {   'description': '지정된 기간의 메일 목록을 미리보기 형태로 조회합니다. 메일 본문 전체가 아닌 제목, 발신자, 날짜, 요약 등 핵심 정보만을 효율적으로 가져와 테이블 형태로 정리합니다.',
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
        'mcp_service': {   'name': 'query_mail_list',
                           'parameters': [   {   'default': None,
                                                 'has_default': False,
                                                 'is_required': True,
                                                 'name': 'user_email',
                                                 'type': 'str'},
                                             {   'default': 'QueryMethod.FILTER',
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'query_method',
                                                 'type': 'QueryMethod'},
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
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'client_filter',
                                                 'type': 'Optional[ExcludeParams]'},
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'search_term',
                                                 'type': 'Optional[str]'},
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'url',
                                                 'type': 'Optional[str]'},
                                             {   'default': 50,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'top',
                                                 'type': 'int'},
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'order_by',
                                                 'type': 'Optional[str]'}],
                           'signature': 'user_email: str, query_method: QueryMethod = "QueryMethod.FILTER", '
                                        'filter_params: Optional[FilterParams] = None, exclude_params: '
                                        'Optional[ExcludeParams] = None, select_params: Optional[SelectParams] = None, '
                                        'client_filter: Optional[ExcludeParams] = None, search_term: Optional[str] = '
                                        'None, url: Optional[str] = None, top: int = 50, order_by: Optional[str] = '
                                        'None'},
        'mcp_service_factors': {   'select': {   'baseModel': 'SelectParams',
                                                 'description': 'SelectParams parameters',
                                                 'parameters': {   'body_preview': {   'default': True,
                                                                                       'description': '메시지 본문의 처음 255자 '
                                                                                                      '(텍스트 형식)',
                                                                                       'type': 'boolean'},
                                                                   'has_attachments': {   'default': True,
                                                                                          'description': '첨부파일 포함 여부',
                                                                                          'type': 'boolean'},
                                                                   'id': {   'default': True,
                                                                             'description': '메시지 고유 식별자 (읽기 전용)',
                                                                             'type': 'boolean'},
                                                                   'internet_message_id': {   'default': True,
                                                                                              'description': 'RFC2822 '
                                                                                                             '형식의 메시지 '
                                                                                                             'ID',
                                                                                              'type': 'boolean'},
                                                                   'received_date_time': {   'default': True,
                                                                                             'description': '메시지 수신 '
                                                                                                            '날짜/시간 '
                                                                                                            '(ISO 8601 '
                                                                                                            '형식, UTC)',
                                                                                             'type': 'boolean'},
                                                                   'sender': {   'default': True,
                                                                                 'description': '메시지를 생성하는 데 사용된 계정',
                                                                                 'type': 'boolean'},
                                                                   'subject': {   'default': True,
                                                                                  'description': '메시지 제목',
                                                                                  'type': 'boolean'}},
                                                 'source': 'internal'}},
        'name': 'mail_list_period'},
    {   'description': 'Microsoft Graph API URL을 직접 사용하여 메일을 조회합니다. 고급 사용자를 위한 기능으로, OData 쿼리 파라미터($filter, $select '
                       '등)를 직접 지정할 수 있습니다.',
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
        'mcp_service': {   'name': 'fetch_url',
                           'parameters': [   {   'default': None,
                                                 'has_default': False,
                                                 'is_required': True,
                                                 'name': 'user_email',
                                                 'type': 'str'},
                                             {   'default': None,
                                                 'has_default': False,
                                                 'is_required': True,
                                                 'name': 'url',
                                                 'type': 'str'},
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'filter_params',
                                                 'type': 'Optional[FilterParams]'},
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'select_params',
                                                 'type': 'Optional[SelectParams]'},
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'client_filter',
                                                 'type': 'Optional[ExcludeParams]'},
                                             {   'default': 50,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'top',
                                                 'type': 'int'}],
                           'signature': 'user_email: str, url: str, filter_params: Optional[FilterParams] = None, '
                                        'select_params: Optional[SelectParams] = None, client_filter: '
                                        'Optional[ExcludeParams] = None, top: int = 50'},
        'name': 'mail_query_url'},
    {   'description': '특정 메일 ID 목록을 사용하여 해당 메일들의 상세 정보를 일괄 조회합니다. 이미 알고 있는 메일 ID를 통해 여러 메일의 전체 내용을 한 번에 가져올 수 있습니다.',
        'inputSchema': {   'properties': {   'test_message_ids': {   'description': 'Auto-added parameter for '
                                                                                    'message_ids ',
                                                                     'targetParam': 'message_ids',
                                                                     'type': 'string'},
                                             'user_email': {   'description': '이전 대화 내역에서 메일 주소를 찾아서 적용 없다면, 내부에서 자동으로 '
                                                                              '처리해 줄 거임',
                                                               'type': 'string'}},
                           'required': ['test_message_ids'],
                           'type': 'object'},
        'mcp_service': {   'name': 'batch_and_fetch',
                           'parameters': [   {   'default': None,
                                                 'has_default': False,
                                                 'is_required': True,
                                                 'name': 'user_email',
                                                 'type': 'str'},
                                             {   'default': None,
                                                 'has_default': False,
                                                 'is_required': True,
                                                 'name': 'message_ids',
                                                 'type': 'List[str]'},
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'select_params',
                                                 'type': 'Optional[SelectParams]'}],
                           'signature': 'user_email: str, message_ids: List[str], select_params: '
                                        'Optional[SelectParams] = None'},
        'name': 'mail_query_if_emaidID'},
    {   'description': 'New tool description',
        'inputSchema': {   'properties': {   'client_filter': {   'baseModel': 'ExcludeParams',
                                                                  'description': 'ExcludeParams parameters',
                                                                  'properties': {   'exclude_from_address': {   'default': 'block@krs.co.kr',
                                                                                                                'description': '제외할 '
                                                                                                                               '발신자 '
                                                                                                                               '주소 '
                                                                                                                               '(from '
                                                                                                                               '필드)',
                                                                                                                'type': 'string'}},
                                                                  'required': [],
                                                                  'type': 'object'},
                                             'search_keywords': {'description': '', 'type': 'string'},
                                             'select_params': {   'baseModel': 'SelectParams',
                                                                  'description': 'SelectParams parameters',
                                                                  'properties': {   'body_preview': {   'description': '메시지 '
                                                                                                                       '본문의 '
                                                                                                                       '처음 '
                                                                                                                       '255자 '
                                                                                                                       '(텍스트 '
                                                                                                                       '형식)',
                                                                                                        'type': 'boolean'},
                                                                                    'has_attachments': {   'description': '첨부파일 '
                                                                                                                          '포함 '
                                                                                                                          '여부',
                                                                                                           'type': 'boolean'},
                                                                                    'id': {   'description': '메시지 고유 '
                                                                                                             '식별자 (읽기 '
                                                                                                             '전용)',
                                                                                              'type': 'boolean'},
                                                                                    'received_date_time': {   'description': '메시지 '
                                                                                                                             '수신 '
                                                                                                                             '날짜/시간 '
                                                                                                                             '(ISO '
                                                                                                                             '8601 '
                                                                                                                             '형식, '
                                                                                                                             'UTC)',
                                                                                                              'type': 'boolean'},
                                                                                    'sender': {   'description': '메시지를 '
                                                                                                                 '생성하는 '
                                                                                                                 '데 '
                                                                                                                 '사용된 '
                                                                                                                 '계정',
                                                                                                  'type': 'boolean'},
                                                                                    'subject': {   'description': '메시지 '
                                                                                                                  '제목',
                                                                                                   'type': 'boolean'},
                                                                                    'web_link': {   'description': 'Outlook '
                                                                                                                   'Web에서 '
                                                                                                                   '메시지를 '
                                                                                                                   '열기 '
                                                                                                                   '위한 '
                                                                                                                   'URL',
                                                                                                    'type': 'boolean'}},
                                                                  'required': [],
                                                                  'type': 'object'},
                                             'top': {'description': '', 'type': 'integer'},
                                             'user_email': {'description': '', 'type': 'string'}},
                           'required': ['search_keywords'],
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
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'client_filter',
                                                 'type': 'Optional[ExcludeParams]'},
                                             {   'default': 50,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'top',
                                                 'type': 'int'}],
                           'signature': 'user_email: str, search_term: str, select_params: Optional[SelectParams] = '
                                        'None, client_filter: Optional[ExcludeParams] = None, top: int = 50'},
        'name': 'mail_list_keyword'}]
