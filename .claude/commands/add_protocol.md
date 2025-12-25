# MCP Protocol 추가 구현 가이드

## 1. 개요
MCP(Model Communication Protocol) 서버에 새로운 프로토콜을 추가하기 위한 실무 가이드입니다.
Jinja2 템플릿 시스템을 활용하여 REST, STDIO, WebSocket 등 다양한 프로토콜을 지원합니다.

## 2. 시스템 구조
```
jinja/
├── generate_universal_server.py      # 메인 생성 스크립트
├── universal_server_template.jinja2   # 범용 서버 템플릿
├── protocol_base.jinja2              # 프로토콜 공통 유틸리티
├── server_rest.jinja2                # REST 프로토콜
├── server_stdio.jinja2               # STDIO 프로토콜
└── server_[new].jinja2               # 새 프로토콜 추가
```

## 3. 프로토콜 추가 단계별 가이드

### Step 1: 프로토콜 템플릿 작성
`jinja/server_[protocol_name].jinja2` 파일을 생성합니다.

#### 예시: WebSocket 프로토콜
```jinja2
{# server_websocket.jinja2 #}
import asyncio
import websockets
import json
from typing import Dict, Any

class WebSocketMCPServer:
    def __init__(self):
        self.connections = set()

    async def handle_connection(self, websocket, path):
        """WebSocket 연결 처리"""
        self.connections.add(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                response = await self.process_request(data)
                await websocket.send(json.dumps(response))
        finally:
            self.connections.remove(websocket)

    async def process_request(self, data: Dict[str, Any]):
        """MCP 요청 처리"""
        method = data.get('method')
        params = data.get('params', {})

        if method == 'tools/list':
            return await self.list_tools()
        elif method == 'tools/call':
            return await self.call_tool(params)
        else:
            return {"error": {"code": -32601, "message": "Method not found"}}

    async def list_tools(self):
        """도구 목록 반환"""
        return {
            "tools": [
                {% for tool in tools %}
                {
                    "name": "{{ tool.name }}",
                    "description": "{{ tool.description }}",
                    "inputSchema": {{ tool.inputSchema | tojson }}
                },
                {% endfor %}
            ]
        }

    async def call_tool(self, params: Dict[str, Any]):
        """도구 실행"""
        tool_name = params.get('name')
        arguments = params.get('arguments', {})

        {% for tool in tools %}
        if tool_name == "{{ tool.name }}":
            return await self.handle_{{ tool.name | replace('-', '_') }}(arguments)
        {% endfor %}

        return {"error": {"code": -32602, "message": f"Unknown tool: {tool_name}"}}

    {% for tool in tools %}
    async def handle_{{ tool.name | replace('-', '_') }}(self, args: Dict[str, Any]):
        """{{ tool.description }}"""
        try:
            # 서비스 인스턴스와 메서드 조회
            impl = TOOL_IMPLEMENTATIONS.get("{{ tool.name }}")
            if not impl:
                return {"error": {"code": -32603, "message": "Tool not implemented"}}

            service_instance = SERVICE_INSTANCES[impl['service_class']]
            method = getattr(service_instance, impl['method'])

            # Internal Args 처리
            {% if tool.internal_args %}
            processed_args = await process_internal_args("{{ tool.name }}", args)
            {% else %}
            processed_args = args
            {% endif %}

            # 메서드 실행
            result = await method(**processed_args)

            return {"result": result}
        except Exception as e:
            return {"error": {"code": -32603, "message": str(e)}}
    {% endfor %}

# 서버 시작 함수
async def start_websocket_server():
    server = WebSocketMCPServer()
    async with websockets.serve(server.handle_connection, "localhost", 8765):
        print("WebSocket MCP Server started on ws://localhost:8765")
        await asyncio.Future()  # 무한 대기

if __name__ == "__main__":
    asyncio.run(start_websocket_server())
```

### Step 2: Universal Template 업데이트
`universal_server_template.jinja2`에 새 프로토콜 포함:

```jinja2
{# 프로토콜별 핸들러 포함 섹션 #}
{% if protocol_type == 'rest' %}
{% include 'server_rest.jinja2' %}
{% elif protocol_type == 'stdio' %}
{% include 'server_stdio.jinja2' %}
{% elif protocol_type == 'websocket' %}
{% include 'server_websocket.jinja2' %}
{% endif %}
```

### Step 3: Protocol Base 업데이트
`protocol_base.jinja2`에 공통 유틸리티 추가:

```jinja2
# 지원 프로토콜 목록
SUPPORTED_PROTOCOLS = {"rest", "stdio", "websocket"}

# 도구 → 서비스 매핑
TOOL_IMPLEMENTATIONS = {
    {% for tool in tools %}
    "{{ tool.name }}": {
        "service_class": "{{ tool.implementation.class_name }}",
        "method": "{{ tool.implementation.method }}"
    },
    {% endfor %}
}

# 서비스 인스턴스
SERVICE_INSTANCES = {
    {% for key, service in unique_services.items() %}
    "{{ service.class_name }}": {{ service.instance }},
    {% endfor %}
}

# Internal Args 처리 함수
async def process_internal_args(tool_name: str, args: Dict[str, Any]):
    """Internal Args와 런타임 인자 병합"""
    internal = INTERNAL_ARGS.get(tool_name, {})
    merged = {}

    for key, value in internal.items():
        if key not in args or args[key] is None:
            merged[key] = value
        else:
            merged[key] = args[key]

    for key, value in args.items():
        if key not in merged:
            merged[key] = value

    return merged
```

### Step 4: 생성 스크립트 수정
`generate_universal_server.py`에 새 프로토콜 옵션 추가:

```python
import argparse
import json
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

def generate_server(server_name: str, protocol: str = 'rest'):
    """서버 코드 생성"""

    # 1. Registry 및 도구 정의 로드
    registry_path = f"mcp_{server_name}/{server_name}_registry.json"
    tools_path = f"mcp_{server_name}/tool_definition_templates.json"
    internal_args_path = f"mcp_{server_name}/tool_internal_args.json"

    with open(registry_path) as f:
        registry = json.load(f)

    with open(tools_path) as f:
        tools = json.load(f)

    with open(internal_args_path) as f:
        internal_args = json.load(f)

    # 2. Context 준비
    context = {
        'server_name': server_name,
        'server_title': f'{server_name.title()} MCP Server',
        'protocol_type': protocol,
        'services': extract_services(registry),
        'unique_services': extract_unique_services(registry),
        'tools': process_tools(tools, registry, internal_args),
        'param_types': extract_param_types(registry),
        'internal_args': internal_args
    }

    # 3. 템플릿 렌더링
    env = Environment(loader=FileSystemLoader('jinja'))
    template = env.get_template('universal_server_template.jinja2')
    output = template.render(context)

    # 4. 파일 생성
    output_path = f"mcp_{server_name}/server_{protocol}.py"
    with open(output_path, 'w') as f:
        f.write(output)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('server_name', help='Server name (e.g., outlook)')
    parser.add_argument('--protocol', default='rest',
                       choices=['rest', 'stdio', 'websocket'],
                       help='Protocol type')
    args = parser.parse_args()

    generate_server(args.server_name, args.protocol)
```

## 4. Registry 구조 설명

```json
{
  "services": {
    "service_name": {
      "implementation": {
        "class_name": "ServiceClass",
        "module_path": "module.path",
        "instance": "service_instance",
        "method": "handler_method"
      },
      "parameters": [...],
      "metadata": {
        "tool_names": ["tool1", "tool2"]
      }
    }
  }
}
```

## 5. 실행 및 테스트

### 코드 생성
```bash
# REST 서버 생성
python jinja/generate_universal_server.py outlook --protocol rest

# WebSocket 서버 생성
python jinja/generate_universal_server.py outlook --protocol websocket

# STDIO 서버 생성
python jinja/generate_universal_server.py outlook --protocol stdio
```

### 테스트 실행
```bash
# 문법 검증
python -m py_compile mcp_outlook/server_websocket.py

# 서버 시작
python mcp_outlook/server_websocket.py

# 클라이언트 테스트
wscat -c ws://localhost:8765
> {"method": "tools/list"}
> {"method": "tools/call", "params": {"name": "mail_search", "arguments": {}}}
```

## 6. 프로토콜별 특징

### REST (FastAPI)
- HTTP/HTTPS 통신
- RESTful API 엔드포인트
- Swagger 문서 자동 생성
- 동기/비동기 처리 지원

### STDIO (Standard I/O)
- JSON-RPC 메시지 형식
- stdin/stdout 통신
- 프로세스 간 통신 적합
- 낮은 오버헤드

### WebSocket
- 양방향 실시간 통신
- 연결 상태 유지
- 이벤트 기반 처리
- 스트리밍 데이터 지원

## 7. 디버깅 및 문제 해결

### 일반적인 문제
```python
# ImportError 해결
# module_path가 올바른지 확인
print(f"Importing {service_info['module_path']}")

# KeyError 해결
# Registry 구조 검증
assert 'services' in registry
assert all(key in service for key in ['implementation', 'parameters'])

# TypeError 해결
# 매개변수 타입 확인
print(f"Expected: {param_type}, Got: {type(value)}")
```

### 로깅 추가
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info(f"Processing tool: {tool_name}")
logger.debug(f"Arguments: {arguments}")
```

## 8. 체크리스트

새 프로토콜 추가 시 확인사항:

- [ ] 프로토콜 템플릿 파일 생성 (`server_[protocol].jinja2`)
- [ ] Universal template에 조건문 추가
- [ ] Protocol base에 프로토콜 추가
- [ ] 생성 스크립트에 옵션 추가
- [ ] 필요한 의존성 패키지 설치
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 수행
- [ ] 문서 업데이트

**작성일**: 2025-12-25
**버전**: 2.0.0
**작성자**: Claude Assistant