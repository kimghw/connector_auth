"""
MCP Tool Definition Templates - AUTO-GENERATED
Signatures extracted from source code using AST parsing
"""
from typing import List, Dict, Any

MCP_TOOLS: List[Dict[str, Any]] = [   {   'description': 'Build Microsoft Graph API query URL for email operations',
        'inputSchema': {   'properties': {   'client_filter': {   'baseModel': 'FilterParams',
                                                                  'description': 'Additional ExcludeParams for '
                                                                                 'client-side filtering',
                                                                  'properties': {   'received_date_from': {   'description': '메일 '
                                                                                                                             '수신 '
                                                                                                                             '시작 '
                                                                                                                             '날짜 '
                                                                                                                             '(포함, '
                                                                                                                             'receivedDateTime '
                                                                                                                             '>= '
                                                                                                                             '이 '
                                                                                                                             '값)',
                                                                                                              'type': 'string'}},
                                                                  'required': [],
                                                                  'type': 'object'},
                                             'exclude': {   'description': 'ExcludeParams for filtering out emails',
                                                            'properties': {   'exclude_attachment_status': {   'description': '제외할 '
                                                                                                                              '첨부파일 '
                                                                                                                              '상태',
                                                                                                               'type': 'boolean'},
                                                                              'exclude_body_keywords': {   'description': '본문에서 '
                                                                                                                          '제외할 '
                                                                                                                          '키워드 '
                                                                                                                          '목록',
                                                                                                           'items': {   'type': 'string'},
                                                                                                           'type': 'array'},
                                                                              'exclude_categories': {   'description': '제외할 '
                                                                                                                       '카테고리 '
                                                                                                                       '목록',
                                                                                                        'items': {   'type': 'string'},
                                                                                                        'type': 'array'},
                                                                              'exclude_classification': {   'description': '제외할 '
                                                                                                                           '받은 '
                                                                                                                           '편지함 '
                                                                                                                           '분류',
                                                                                                            'enum': [   'focused',
                                                                                                                        'other'],
                                                                                                            'type': 'string'},
                                                                              'exclude_conversation_id': {   'description': '제외할 '
                                                                                                                            '대화 '
                                                                                                                            '스레드 '
                                                                                                                            'ID',
                                                                                                             'type': 'string'},
                                                                              'exclude_delivery_receipt': {   'description': '제외할 '
                                                                                                                             '배달 '
                                                                                                                             '확인 '
                                                                                                                             '상태',
                                                                                                              'type': 'boolean'},
                                                                              'exclude_draft_status': {   'description': '제외할 '
                                                                                                                         '임시 '
                                                                                                                         '저장 '
                                                                                                                         '상태',
                                                                                                          'type': 'boolean'},
                                                                              'exclude_flag_status': {   'description': '제외할 '
                                                                                                                        '플래그 '
                                                                                                                        '상태',
                                                                                                         'enum': [   'notFlagged',
                                                                                                                     'complete',
                                                                                                                     'flagged'],
                                                                                                         'type': 'string'},
                                                                              'exclude_from_address': {   'description': '제외할 '
                                                                                                                         '발신자 '
                                                                                                                         '주소 '
                                                                                                                         '(from '
                                                                                                                         '필드)',
                                                                                                          'oneOf': [   {   'type': 'string'},
                                                                                                                       {   'items': {   'type': 'string'},
                                                                                                                           'type': 'array'}]},
                                                                              'exclude_id': {   'description': '제외할 메일 '
                                                                                                               'ID',
                                                                                                'type': 'string'},
                                                                              'exclude_importance': {   'description': '제외할 '
                                                                                                                       '중요도',
                                                                                                        'enum': [   'low',
                                                                                                                    'normal',
                                                                                                                    'high'],
                                                                                                        'type': 'string'},
                                                                              'exclude_parent_folder_id': {   'description': '제외할 '
                                                                                                                             '폴더 '
                                                                                                                             'ID',
                                                                                                              'type': 'string'},
                                                                              'exclude_preview_keywords': {   'description': '미리보기에서 '
                                                                                                                             '제외할 '
                                                                                                                             '키워드 '
                                                                                                                             '목록',
                                                                                                              'items': {   'type': 'string'},
                                                                                                              'type': 'array'},
                                                                              'exclude_read_receipt': {   'description': '제외할 '
                                                                                                                         '읽음 '
                                                                                                                         '확인 '
                                                                                                                         '상태',
                                                                                                          'type': 'boolean'},
                                                                              'exclude_read_status': {   'description': '제외할 '
                                                                                                                        '읽음 '
                                                                                                                        '상태',
                                                                                                         'type': 'boolean'},
                                                                              'exclude_sender_address': {   'description': '제외할 '
                                                                                                                           '실제 '
                                                                                                                           '발신자 '
                                                                                                                           '주소 '
                                                                                                                           '(sender '
                                                                                                                           '필드)',
                                                                                                            'oneOf': [   {   'type': 'string'},
                                                                                                                         {   'items': {   'type': 'string'},
                                                                                                                             'type': 'array'}]},
                                                                              'exclude_sensitivity': {   'description': '제외할 '
                                                                                                                        '민감도',
                                                                                                         'enum': [   'normal',
                                                                                                                     'personal',
                                                                                                                     'private',
                                                                                                                     'confidential'],
                                                                                                         'type': 'string'},
                                                                              'exclude_subject_keywords': {   'description': '제목에서 '
                                                                                                                             '제외할 '
                                                                                                                             '키워드 '
                                                                                                                             '목록',
                                                                                                              'items': {   'type': 'string'},
                                                                                                              'type': 'array'}},
                                                            'type': 'object'},
                                             'filter': {   'description': 'FilterParams for email filtering',
                                                           'properties': {   'body_content': {   'description': '본문에 '
                                                                                                                '포함될 '
                                                                                                                '키워드 '
                                                                                                                '(단일 '
                                                                                                                '문자열 '
                                                                                                                '또는 '
                                                                                                                '리스트)',
                                                                                                 'oneOf': [   {   'type': 'string'},
                                                                                                              {   'items': {   'type': 'string'},
                                                                                                                  'type': 'array'}]},
                                                                             'body_operator': {   'default': 'or',
                                                                                                  'description': '본문 '
                                                                                                                 '키워드 '
                                                                                                                 '연결 '
                                                                                                                 '방식',
                                                                                                  'enum': ['or', 'and'],
                                                                                                  'type': 'string'},
                                                                             'body_preview': {   'description': '미리보기에 '
                                                                                                                '포함될 '
                                                                                                                '키워드 '
                                                                                                                '(단일 '
                                                                                                                '문자열 '
                                                                                                                '또는 '
                                                                                                                '리스트)',
                                                                                                 'oneOf': [   {   'type': 'string'},
                                                                                                              {   'items': {   'type': 'string'},
                                                                                                                  'type': 'array'}]},
                                                                             'categories': {   'description': '메일 카테고리 '
                                                                                                              '목록',
                                                                                               'items': {   'type': 'string'},
                                                                                               'type': 'array'},
                                                                             'conversation_id': {   'description': '대화 '
                                                                                                                   '스레드 '
                                                                                                                   'ID',
                                                                                                    'type': 'string'},
                                                                             'created_date_time': {   'description': '메일 '
                                                                                                                     '생성 '
                                                                                                                     '날짜/시간 '
                                                                                                                     '- '
                                                                                                                     '이 '
                                                                                                                     '시간 '
                                                                                                                     '이후 '
                                                                                                                     '메일만 '
                                                                                                                     '조회 '
                                                                                                                     '(ISO '
                                                                                                                     '8601 '
                                                                                                                     '형식)',
                                                                                                      'type': 'string'},
                                                                             'flag_status': {   'description': '플래그 상태',
                                                                                                'enum': [   'notFlagged',
                                                                                                            'complete',
                                                                                                            'flagged'],
                                                                                                'type': 'string'},
                                                                             'from_address': {   'description': 'from/emailAddress/address '
                                                                                                                '- 단일 '
                                                                                                                '또는 여러 '
                                                                                                                '발신자 '
                                                                                                                '이메일 '
                                                                                                                '주소',
                                                                                                 'oneOf': [   {   'type': 'string'},
                                                                                                              {   'items': {   'type': 'string'},
                                                                                                                  'type': 'array'}]},
                                                                             'has_attachments': {   'description': '첨부파일 '
                                                                                                                   '포함 '
                                                                                                                   '여부',
                                                                                                    'type': 'boolean'},
                                                                             'id': {   'description': '메일 고유 ID',
                                                                                       'type': 'string'},
                                                                             'importance': {   'description': '메일 중요도',
                                                                                               'enum': [   'low',
                                                                                                           'normal',
                                                                                                           'high'],
                                                                                               'type': 'string'},
                                                                             'inference_classification': {   'description': '받은 '
                                                                                                                            '편지함 '
                                                                                                                            '분류',
                                                                                                             'enum': [   'focused',
                                                                                                                         'other'],
                                                                                                             'type': 'string'},
                                                                             'is_delivery_receipt_requested': {   'description': '배달 '
                                                                                                                                 '확인 '
                                                                                                                                 '요청 '
                                                                                                                                 '여부',
                                                                                                                  'type': 'boolean'},
                                                                             'is_draft': {   'description': '임시 저장 상태 '
                                                                                                            '필터',
                                                                                             'type': 'boolean'},
                                                                             'is_read': {   'description': '읽음 상태 필터 '
                                                                                                           '(true: 읽은 '
                                                                                                           '메일, false: '
                                                                                                           '읽지 않은 메일)',
                                                                                            'type': 'boolean'},
                                                                             'is_read_receipt_requested': {   'description': '읽음 '
                                                                                                                             '확인 '
                                                                                                                             '요청 '
                                                                                                                             '여부',
                                                                                                              'type': 'boolean'},
                                                                             'last_modified_date_time': {   'description': '메일 '
                                                                                                                           '최종 '
                                                                                                                           '수정 '
                                                                                                                           '날짜/시간 '
                                                                                                                           '- '
                                                                                                                           '이 '
                                                                                                                           '시간 '
                                                                                                                           '이후 '
                                                                                                                           '메일만 '
                                                                                                                           '조회 '
                                                                                                                           '(ISO '
                                                                                                                           '8601 '
                                                                                                                           '형식)',
                                                                                                            'type': 'string'},
                                                                             'parent_folder_id': {   'description': '폴더 '
                                                                                                                    'ID',
                                                                                                     'type': 'string'},
                                                                             'received_date_from': {   'description': '메일 '
                                                                                                                      '수신 '
                                                                                                                      '시작 '
                                                                                                                      '날짜 '
                                                                                                                      '(포함, '
                                                                                                                      'receivedDateTime '
                                                                                                                      '>= '
                                                                                                                      '이 '
                                                                                                                      '값)',
                                                                                                       'type': 'string'},
                                                                             'received_date_time': {   'description': '메일 '
                                                                                                                      '수신 '
                                                                                                                      '날짜/시간 '
                                                                                                                      '- '
                                                                                                                      '이 '
                                                                                                                      '시간 '
                                                                                                                      '이후 '
                                                                                                                      '메일만 '
                                                                                                                      '조회 '
                                                                                                                      '(ISO '
                                                                                                                      '8601 '
                                                                                                                      '형식)',
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
                                                                             'sender_address': {   'description': 'sender/emailAddress/address '
                                                                                                                  '- '
                                                                                                                  '실제 '
                                                                                                                  '발신자 '
                                                                                                                  '이메일 '
                                                                                                                  '주소',
                                                                                                   'oneOf': [   {   'type': 'string'},
                                                                                                                {   'items': {   'type': 'string'},
                                                                                                                    'type': 'array'}]},
                                                                             'sensitivity': {   'description': '메일 민감도',
                                                                                                'enum': [   'normal',
                                                                                                            'personal',
                                                                                                            'private',
                                                                                                            'confidential'],
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
                                                                             'sent_date_time': {   'description': '메일 '
                                                                                                                  '발신 '
                                                                                                                  '날짜/시간 '
                                                                                                                  '- 이 '
                                                                                                                  '시간 '
                                                                                                                  '이후 '
                                                                                                                  '메일만 '
                                                                                                                  '조회 '
                                                                                                                  '(ISO '
                                                                                                                  '8601 '
                                                                                                                  '형식)',
                                                                                                   'type': 'string'},
                                                                             'sent_date_to': {   'description': '메일 발신 '
                                                                                                                '종료 날짜 '
                                                                                                                '(포함, '
                                                                                                                'sentDateTime '
                                                                                                                '<= 이 '
                                                                                                                '값)',
                                                                                                 'type': 'string'},
                                                                             'subject': {   'description': '제목에 포함될 '
                                                                                                           '키워드 (단일 '
                                                                                                           '문자열 또는 '
                                                                                                           '리스트)',
                                                                                            'oneOf': [   {   'type': 'string'},
                                                                                                         {   'items': {   'type': 'string'},
                                                                                                             'type': 'array'}]},
                                                                             'subject_operator': {   'default': 'or',
                                                                                                     'description': '제목 '
                                                                                                                    '키워드 '
                                                                                                                    '연결 '
                                                                                                                    '방식',
                                                                                                     'enum': [   'or',
                                                                                                                 'and'],
                                                                                                     'type': 'string'}},
                                                           'type': 'object'},
                                             'orderby': {'description': '정렬 기준', 'type': 'string'},
                                             'select': {   'description': 'SelectParams for selecting fields',
                                                           'properties': {   'fields': {   'description': '조회할 필드 목록 '
                                                                                                          '(미지정 시 모든 '
                                                                                                          '필드 반환)',
                                                                                           'items': {'type': 'string'},
                                                                                           'type': 'array'}},
                                                           'type': 'object'},
                                             'top': {'default': 450, 'description': '반환할 최대 메일 수', 'type': 'integer'},
                                             'user_email': {   'description': 'User email for authentication',
                                                               'type': 'string'}},
                           'required': ['user_email', 'filter'],
                           'type': 'object'},
        'mcp_service': {   'name': 'query_filter',
                           'parameters': [   {   'default': None,
                                                 'has_default': False,
                                                 'is_required': True,
                                                 'name': 'user_email',
                                                 'type': 'str'},
                                             {   'default': None,
                                                 'has_default': False,
                                                 'is_required': True,
                                                 'name': 'filter',
                                                 'type': 'FilterParams'},
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'exclude',
                                                 'type': 'Optional[ExcludeParams]'},
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'select',
                                                 'type': 'Optional[SelectParams]'},
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'client_filter',
                                                 'type': 'Optional[ExcludeParams]'},
                                             {   'default': 450,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'top',
                                                 'type': 'int'},
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'orderby',
                                                 'type': 'Optional[str]'}],
                           'signature': 'user_email: str, filter: FilterParams, exclude: Optional[ExcludeParams] = '
                                        'None, select: Optional[SelectParams] = None, client_filter: '
                                        'Optional[ExcludeParams] = None, top: int = 450, orderby: Optional[str] = '
                                        'None'},
        'name': 'Outlook'},
    {   'description': 'Build Microsoft Graph API query URL for email operations',
        'inputSchema': {   'properties': {   'client_filter': {   'description': 'ExcludeParams for client-side '
                                                                                 'filtering',
                                                                  'properties': {   'exclude_attachment_status': {   'description': '제외할 '
                                                                                                                                    '첨부파일 '
                                                                                                                                    '상태',
                                                                                                                     'type': 'boolean'},
                                                                                    'exclude_body_keywords': {   'description': '본문에서 '
                                                                                                                                '제외할 '
                                                                                                                                '키워드 '
                                                                                                                                '목록',
                                                                                                                 'items': {   'type': 'string'},
                                                                                                                 'type': 'array'},
                                                                                    'exclude_categories': {   'description': '제외할 '
                                                                                                                             '카테고리 '
                                                                                                                             '목록',
                                                                                                              'items': {   'type': 'string'},
                                                                                                              'type': 'array'},
                                                                                    'exclude_classification': {   'description': '제외할 '
                                                                                                                                 '받은 '
                                                                                                                                 '편지함 '
                                                                                                                                 '분류',
                                                                                                                  'enum': [   'focused',
                                                                                                                              'other'],
                                                                                                                  'type': 'string'},
                                                                                    'exclude_conversation_id': {   'description': '제외할 '
                                                                                                                                  '대화 '
                                                                                                                                  '스레드 '
                                                                                                                                  'ID',
                                                                                                                   'type': 'string'},
                                                                                    'exclude_delivery_receipt': {   'description': '제외할 '
                                                                                                                                   '배달 '
                                                                                                                                   '확인 '
                                                                                                                                   '상태',
                                                                                                                    'type': 'boolean'},
                                                                                    'exclude_draft_status': {   'description': '제외할 '
                                                                                                                               '임시 '
                                                                                                                               '저장 '
                                                                                                                               '상태',
                                                                                                                'type': 'boolean'},
                                                                                    'exclude_flag_status': {   'description': '제외할 '
                                                                                                                              '플래그 '
                                                                                                                              '상태',
                                                                                                               'enum': [   'notFlagged',
                                                                                                                           'complete',
                                                                                                                           'flagged'],
                                                                                                               'type': 'string'},
                                                                                    'exclude_from_address': {   'description': '제외할 '
                                                                                                                               '발신자 '
                                                                                                                               '주소 '
                                                                                                                               '(from '
                                                                                                                               '필드)',
                                                                                                                'oneOf': [   {   'type': 'string'},
                                                                                                                             {   'items': {   'type': 'string'},
                                                                                                                                 'type': 'array'}]},
                                                                                    'exclude_id': {   'description': '제외할 '
                                                                                                                     '메일 '
                                                                                                                     'ID',
                                                                                                      'type': 'string'},
                                                                                    'exclude_importance': {   'description': '제외할 '
                                                                                                                             '중요도',
                                                                                                              'enum': [   'low',
                                                                                                                          'normal',
                                                                                                                          'high'],
                                                                                                              'type': 'string'},
                                                                                    'exclude_parent_folder_id': {   'description': '제외할 '
                                                                                                                                   '폴더 '
                                                                                                                                   'ID',
                                                                                                                    'type': 'string'},
                                                                                    'exclude_preview_keywords': {   'description': '미리보기에서 '
                                                                                                                                   '제외할 '
                                                                                                                                   '키워드 '
                                                                                                                                   '목록',
                                                                                                                    'items': {   'type': 'string'},
                                                                                                                    'type': 'array'},
                                                                                    'exclude_read_receipt': {   'description': '제외할 '
                                                                                                                               '읽음 '
                                                                                                                               '확인 '
                                                                                                                               '상태',
                                                                                                                'type': 'boolean'},
                                                                                    'exclude_read_status': {   'description': '제외할 '
                                                                                                                              '읽음 '
                                                                                                                              '상태',
                                                                                                               'type': 'boolean'},
                                                                                    'exclude_sender_address': {   'description': '제외할 '
                                                                                                                                 '실제 '
                                                                                                                                 '발신자 '
                                                                                                                                 '주소 '
                                                                                                                                 '(sender '
                                                                                                                                 '필드)',
                                                                                                                  'oneOf': [   {   'type': 'string'},
                                                                                                                               {   'items': {   'type': 'string'},
                                                                                                                                   'type': 'array'}]},
                                                                                    'exclude_sensitivity': {   'description': '제외할 '
                                                                                                                              '민감도',
                                                                                                               'enum': [   'normal',
                                                                                                                           'personal',
                                                                                                                           'private',
                                                                                                                           'confidential'],
                                                                                                               'type': 'string'},
                                                                                    'exclude_subject_keywords': {   'description': '제목에서 '
                                                                                                                                   '제외할 '
                                                                                                                                   '키워드 '
                                                                                                                                   '목록',
                                                                                                                    'items': {   'type': 'string'},
                                                                                                                    'type': 'array'}},
                                                                  'type': 'object'},
                                             'orderby': {'description': '정렬 기준', 'type': 'string'},
                                             'search': {'description': '검색어 ($search 파라미터)', 'type': 'string'},
                                             'select': {   'description': 'SelectParams for selecting fields',
                                                           'properties': {   'fields': {   'description': '조회할 필드 목록 '
                                                                                                          '(미지정 시 모든 '
                                                                                                          '필드 반환)',
                                                                                           'items': {'type': 'string'},
                                                                                           'type': 'array'}},
                                                           'type': 'object'},
                                             'top': {'default': 250, 'description': '반환할 최대 메일 수', 'type': 'integer'},
                                             'user_email': {'type': 'string'}},
                           'required': ['user_email', 'search'],
                           'type': 'object'},
        'mcp_service': {   'name': 'query_search',
                           'parameters': [   {   'default': None,
                                                 'has_default': False,
                                                 'is_required': True,
                                                 'name': 'user_email',
                                                 'type': 'str'},
                                             {   'default': None,
                                                 'has_default': False,
                                                 'is_required': True,
                                                 'name': 'search',
                                                 'type': 'str'},
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'client_filter',
                                                 'type': 'Optional[ExcludeParams]'},
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'select',
                                                 'type': 'Optional[SelectParams]'},
                                             {   'default': 250,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'top',
                                                 'type': 'int'},
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'orderby',
                                                 'type': 'Optional[str]'}],
                           'signature': 'user_email: str, search: str, client_filter: Optional[ExcludeParams] = None, '
                                        'select: Optional[SelectParams] = None, top: int = 250, orderby: Optional[str] '
                                        '= None'},
        'name': 'keyword_search'},
    {   'description': 'Build Microsoft Graph API query URL for email operations',
        'inputSchema': {   'properties': {   'client_filter': {   'description': 'ExcludeParams for client-side '
                                                                                 'filtering',
                                                                  'properties': {   'exclude_attachment_status': {   'description': '제외할 '
                                                                                                                                    '첨부파일 '
                                                                                                                                    '상태',
                                                                                                                     'type': 'boolean'},
                                                                                    'exclude_body_keywords': {   'description': '본문에서 '
                                                                                                                                '제외할 '
                                                                                                                                '키워드 '
                                                                                                                                '목록',
                                                                                                                 'items': {   'type': 'string'},
                                                                                                                 'type': 'array'},
                                                                                    'exclude_categories': {   'description': '제외할 '
                                                                                                                             '카테고리 '
                                                                                                                             '목록',
                                                                                                              'items': {   'type': 'string'},
                                                                                                              'type': 'array'},
                                                                                    'exclude_classification': {   'description': '제외할 '
                                                                                                                                 '받은 '
                                                                                                                                 '편지함 '
                                                                                                                                 '분류',
                                                                                                                  'enum': [   'focused',
                                                                                                                              'other'],
                                                                                                                  'type': 'string'},
                                                                                    'exclude_conversation_id': {   'description': '제외할 '
                                                                                                                                  '대화 '
                                                                                                                                  '스레드 '
                                                                                                                                  'ID',
                                                                                                                   'type': 'string'},
                                                                                    'exclude_delivery_receipt': {   'description': '제외할 '
                                                                                                                                   '배달 '
                                                                                                                                   '확인 '
                                                                                                                                   '상태',
                                                                                                                    'type': 'boolean'},
                                                                                    'exclude_draft_status': {   'description': '제외할 '
                                                                                                                               '임시 '
                                                                                                                               '저장 '
                                                                                                                               '상태',
                                                                                                                'type': 'boolean'},
                                                                                    'exclude_flag_status': {   'description': '제외할 '
                                                                                                                              '플래그 '
                                                                                                                              '상태',
                                                                                                               'enum': [   'notFlagged',
                                                                                                                           'complete',
                                                                                                                           'flagged'],
                                                                                                               'type': 'string'},
                                                                                    'exclude_from_address': {   'description': '제외할 '
                                                                                                                               '발신자 '
                                                                                                                               '주소 '
                                                                                                                               '(from '
                                                                                                                               '필드)',
                                                                                                                'oneOf': [   {   'type': 'string'},
                                                                                                                             {   'items': {   'type': 'string'},
                                                                                                                                 'type': 'array'}]},
                                                                                    'exclude_id': {   'description': '제외할 '
                                                                                                                     '메일 '
                                                                                                                     'ID',
                                                                                                      'type': 'string'},
                                                                                    'exclude_importance': {   'description': '제외할 '
                                                                                                                             '중요도',
                                                                                                              'enum': [   'low',
                                                                                                                          'normal',
                                                                                                                          'high'],
                                                                                                              'type': 'string'},
                                                                                    'exclude_parent_folder_id': {   'description': '제외할 '
                                                                                                                                   '폴더 '
                                                                                                                                   'ID',
                                                                                                                    'type': 'string'},
                                                                                    'exclude_preview_keywords': {   'description': '미리보기에서 '
                                                                                                                                   '제외할 '
                                                                                                                                   '키워드 '
                                                                                                                                   '목록',
                                                                                                                    'items': {   'type': 'string'},
                                                                                                                    'type': 'array'},
                                                                                    'exclude_read_receipt': {   'description': '제외할 '
                                                                                                                               '읽음 '
                                                                                                                               '확인 '
                                                                                                                               '상태',
                                                                                                                'type': 'boolean'},
                                                                                    'exclude_read_status': {   'description': '제외할 '
                                                                                                                              '읽음 '
                                                                                                                              '상태',
                                                                                                               'type': 'boolean'},
                                                                                    'exclude_sender_address': {   'description': '제외할 '
                                                                                                                                 '실제 '
                                                                                                                                 '발신자 '
                                                                                                                                 '주소 '
                                                                                                                                 '(sender '
                                                                                                                                 '필드)',
                                                                                                                  'oneOf': [   {   'type': 'string'},
                                                                                                                               {   'items': {   'type': 'string'},
                                                                                                                                   'type': 'array'}]},
                                                                                    'exclude_sensitivity': {   'description': '제외할 '
                                                                                                                              '민감도',
                                                                                                               'enum': [   'normal',
                                                                                                                           'personal',
                                                                                                                           'private',
                                                                                                                           'confidential'],
                                                                                                               'type': 'string'},
                                                                                    'exclude_subject_keywords': {   'description': '제목에서 '
                                                                                                                                   '제외할 '
                                                                                                                                   '키워드 '
                                                                                                                                   '목록',
                                                                                                                    'items': {   'type': 'string'},
                                                                                                                    'type': 'array'}},
                                                                  'type': 'object'},
                                             'top': {'default': 450, 'description': '반환할 최대 메일 수', 'type': 'integer'},
                                             'url': {'description': '직접 지정한 Graph API URL', 'type': 'string'},
                                             'user_email': {'type': 'string'}},
                           'required': ['user_email', 'url'],
                           'type': 'object'},
        'mcp_service': {   'name': 'query_url',
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
                                             {   'default': 450,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'top',
                                                 'type': 'int'},
                                             {   'default': None,
                                                 'has_default': True,
                                                 'is_required': False,
                                                 'name': 'client_filter',
                                                 'type': 'Optional[ExcludeParams]'}],
                           'signature': 'user_email: str, url: str, top: int = 450, client_filter: '
                                        'Optional[ExcludeParams] = None'},
        'name': 'query_url'},
    {   'description': 'New tool description',
        'inputSchema': {   'properties': {   'filter': {   'baseModel': 'FilterParams',
                                                           'description': '사용자가 요청한 기간을 언제부터 언제까지  포맷에 맞게 파싱하여 제공합니다. ',
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
                                                           'required': [],
                                                           'type': 'object'},
                                             'top': {'default': 100, 'description': '', 'type': 'integer'},
                                             'user_email': {'description': '', 'type': 'string'}},
                           'required': ['user_email', 'filter'],
                           'type': 'object'},
        'mcp_service': 'query_filter',
        'name': 'mail_list'}]
