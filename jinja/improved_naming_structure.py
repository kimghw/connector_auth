"""
개선된 네이밍 구조 제안
- 실제 용도에 맞는 정확한 이름 사용
- 관련된 정보를 딕셔너리로 그룹화
"""

# ============================================
# 현재 문제점
# ============================================
current_issues = """
1. service_name이 실제로는 '함수 이름'인데 service라고 부름
2. class_name과 instance_name이 따로 있어서 관리 불편
3. 모듈 import 정보가 명확하지 않음
4. MCP 서버 이름과 Tool 이름이 혼재
"""

# ============================================
# 개선된 네이밍 구조
# ============================================
improved_structure = {
    # 1. MCP/Tool 관련 정보
    'mcp': {
        'server_name': 'outlook',  # MCP 서버 이름 (outlook, file_handler 등)
        'tool_name': 'Outlook',    # 사용자가 호출하는 Tool 이름
        'internal_name': 'Handle_query_filter',  # 데코레이터의 원래 이름
    },

    # 2. Python 함수/메서드 정보
    'method': {
        'name': 'query_filter',     # 실제 Python 메서드/함수 이름
        'is_async': True,           # async 함수인지
        'returns_function': False,  # 함수를 반환하는지 (고차 함수)
    },

    # 3. Python 클래스/인스턴스 정보 (딕셔너리로 관리)
    'service': {
        'class_name': 'GraphMailQuery',      # 클래스 이름
        'instance_name': 'graph_mail_query', # 인스턴스 변수명
        'module_path': 'graph_mail_query',   # import 경로
        'import_from': 'mcp_outlook',        # from 절 (optional)
    },

    # 4. 파라미터 정보 (구조 유지)
    'parameters': {
        'simple': {},
        'objects': {},
        'mapping': {},  # call_mapping보다 간결
    },

    # 5. 메타데이터
    'metadata': {
        'category': 'outlook_mail',
        'tags': ['query', 'internal'],
        'description': 'Query emails with filters',
    }
}

# ============================================
# 사용 예시
# ============================================

# 1. Import 생성
def generate_import(service):
    """Import 문 생성"""
    if service.get('import_from'):
        return f"from {service['import_from']}.{service['module_path']} import {service['class_name']}"
    else:
        return f"from {service['module_path']} import {service['class_name']}"

# 2. 인스턴스 생성
def generate_instance(service):
    """인스턴스 생성 코드"""
    return f"{service['instance_name']} = {service['class_name']}()"

# 3. 메서드 호출
def generate_method_call(method, service, params):
    """메서드 호출 코드 생성"""
    if method['is_async']:
        return f"await {service['instance_name']}.{method['name']}({params})"
    else:
        return f"{service['instance_name']}.{method['name']}({params})"

# ============================================
# 템플릿에서 사용
# ============================================
template_example = """
# Jinja2 템플릿에서 더 명확하게 사용:

{# Import 생성 #}
{% for tool in tools %}
from {{ tool.service.module_path }} import {{ tool.service.class_name }}
{% endfor %}

{# 인스턴스 생성 #}
{% for tool in tools %}
{{ tool.service.instance_name }} = {{ tool.service.class_name }}()
{% endfor %}

{# API 핸들러 #}
{% for tool in tools %}
async def handle_{{ tool.mcp.tool_name }}(args):
    # MCP 서버: {{ tool.mcp.server_name }}
    # 실제 메서드: {{ tool.method.name }}

    # 서비스 인스턴스 가져오기
    service = {{ tool.service.instance_name }}

    # 메서드 호출
    {% if tool.method.is_async %}
    result = await service.{{ tool.method.name }}(...)
    {% else %}
    result = service.{{ tool.method.name }}(...)
    {% endif %}

    return result
{% endfor %}
"""

# ============================================
# 대안 1: 더 간단한 구조 (flat)
# ============================================
alternative_flat = {
    # MCP 정보
    'mcp_server': 'outlook',
    'mcp_tool': 'Outlook',

    # Python 정보
    'method_name': 'query_filter',
    'class_info': {  # 딕셔너리로 관리
        'name': 'GraphMailQuery',
        'instance': 'graph_mail_query',
        'module': 'graph_mail_query',
    },

    # 파라미터
    'params': {},

    # 메타데이터
    'meta': {},
}

# ============================================
# 대안 2: 계층 구조 단순화
# ============================================
alternative_simple = {
    'tool_name': 'Outlook',          # MCP Tool 이름
    'server_name': 'outlook',        # MCP 서버 이름

    'handler': {  # 핸들러 정보 (service보다 명확)
        'method': 'query_filter',    # 메서드 이름
        'class': 'GraphMailQuery',   # 클래스 이름
        'instance': 'graph_mail_query',  # 인스턴스
        'module': 'graph_mail_query',    # 모듈
    },

    'params': {},
    'meta': {},
}

# ============================================
# 네이밍 비교표
# ============================================
naming_comparison = """
| 현재 | 제안 1 (상세) | 제안 2 (플랫) | 제안 3 (단순) | 설명 |
|------|------------|-----------|-----------|------|
| service_name | method.name | method_name | handler.method | 실제 Python 메서드 이름 |
| service_class | service.class_name | class_info.name | handler.class | Python 클래스 이름 |
| service_object | service.instance_name | class_info.instance | handler.instance | 인스턴스 변수명 |
| - | service.module_path | class_info.module | handler.module | import 경로 |
| name | mcp.tool_name | mcp_tool | tool_name | MCP Tool 이름 |
| - | mcp.server_name | mcp_server | server_name | MCP 서버 이름 |
"""

# ============================================
# 추천: alternative_simple (제안 3)
# ============================================
"""
이유:
1. 'handler'가 'service'보다 더 명확함 (HTTP 핸들러 컨텍스트)
2. 플랫하면서도 논리적 그룹화 유지
3. 클래스 관련 정보가 딕셔너리로 관리됨
4. MCP 관련 정보와 Python 정보가 명확히 구분됨
5. 간단하면서도 확장 가능
"""