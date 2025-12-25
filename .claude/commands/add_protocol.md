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

#### ⚠️ 중요 주의사항
- **템플릿은 핸들러만 포함**: 전체 서버 코드가 아닌 프로토콜 핸들러 부분만 작성
- **Import 문 제외**: universal_server_template에서 이미 처리
- **서비스 인스턴스 생성 제외**: universal_server_template에서 생성됨

#### 예시: StreamableHTTP 프로토콜 (실제 구현 예제)
```jinja2
{# server_stream.jinja2 #}
# StreamableHTTP Protocol Implementation
import aiohttp
from aiohttp import web
from typing import AsyncIterator
import json

class StreamableHTTPMCPServer:
    """MCP StreamableHTTP Protocol Server

    HTTP 기반 스트리밍 프로토콜로 청크 단위의 응답을 지원합니다.
    Transfer-Encoding: chunked를 사용하여 점진적 응답 전송이 가능합니다.
    """

    def __init__(self):
        self.app = web.Application()
        self.setup_routes()
        logger.info("{{ server_title }} StreamableHTTP Server initialized")

    def setup_routes(self):
        """HTTP 라우트 설정"""
        # MCP 표준 엔드포인트
        self.app.router.add_post('/mcp/v1/initialize', self.handle_initialize)
        self.app.router.add_post('/mcp/v1/tools/list', self.handle_tools_list)
        self.app.router.add_post('/mcp/v1/tools/call', self.handle_tools_call)
        # Health check
        self.app.router.add_get('/health', self.handle_health)

    async def handle_tools_call(self, request: web.Request) -> web.Response:
        """도구 실행 - 스트리밍 응답 지원"""
        try:
            data = await request.json()
            tool_name = data.get('name')
            arguments = data.get('arguments', {})
            stream = data.get('stream', False)  # 스트리밍 옵션

            if stream:
                # 스트리밍 응답
                return await self.stream_tool_response(tool_name, arguments, request)
            else:
                # 일반 응답
                handler_name = f"handle_{tool_name.replace('-', '_')}"
                if handler_name in globals():
                    result = await globals()[handler_name](arguments)
                    return web.json_response({"content": [{"type": "text", "text": str(result)}]})
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")

        except Exception as e:
            return web.json_response(
                {"error": {"code": -32603, "message": str(e)}}, status=500
            )

    async def stream_tool_response(self, tool_name: str, arguments: dict, request: web.Request) -> web.StreamResponse:
        """도구 응답을 스트리밍으로 전송"""
        response = web.StreamResponse()
        response.headers['Content-Type'] = 'application/x-ndjson'  # Newline Delimited JSON
        response.headers['Transfer-Encoding'] = 'chunked'
        await response.prepare(request)

        try:
            # 예제: 청크 단위로 데이터 전송
            for i in range(5):
                chunk = {"type": "chunk", "content": f"Chunk {i}", "done": False}
                await response.write((json.dumps(chunk) + '\n').encode('utf-8'))
                await asyncio.sleep(0.5)  # 시뮬레이션

            # 완료 신호
            end_chunk = {"type": "end", "done": True}
            await response.write((json.dumps(end_chunk) + '\n').encode('utf-8'))
        finally:
            await response.write_eof()

        return response

    def run(self, host: str = '0.0.0.0', port: int = 8080):
        """서버 실행"""
        web.run_app(self.app, host=host, port=port)

# 메인 엔트리 포인트
def handle_streamablehttp(host: str = '0.0.0.0', port: int = 8080):
    """Handle MCP protocol via StreamableHTTP"""
    server = StreamableHTTPMCPServer()
    server.run(host, port)
```

### Step 2: Universal Template 업데이트
`universal_server_template.jinja2`에 새 프로토콜 포함:

```jinja2
{#- Include protocol-specific handlers based on protocol_type -#}
{%- if protocol_type == 'rest' %}
{% include 'server_rest.jinja2' %}
{%- elif protocol_type == 'stdio' %}
{% include 'server_stdio.jinja2' %}  {# ← 반드시 include 사용! TODO 코드로 남기지 말 것 #}
{%- elif protocol_type == 'stream' %}
{% include 'server_stream.jinja2' %}
{%- endif %}
```

**⚠️ 주의**: 절대 TODO나 pass 코드를 직접 작성하지 말고 반드시 `{% include %}` 사용

### Step 3: Protocol Base 업데이트
`protocol_base.jinja2`에 공통 유틸리티 추가:

```jinja2
# 지원 프로토콜 목록
SUPPORTED_PROTOCOLS = {"rest", "stdio", "stream"}

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
                       choices=['rest', 'stdio', 'stream'],
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

# StreamableHTTP 서버 생성
python jinja/generate_universal_server.py outlook --protocol stream

# STDIO 서버 생성
python jinja/generate_universal_server.py outlook --protocol stdio
```

### 테스트 실행
```bash
# 문법 검증
python -m py_compile mcp_outlook/mcp_server/server_stream.py

# 서버 시작
python mcp_outlook/mcp_server/server_stream.py

# 클라이언트 테스트 (curl 사용)
curl -X POST http://localhost:8080/mcp/v1/tools/list \
  -H "Content-Type: application/json" \
  -d '{}'

# 스트리밍 테스트
curl -X POST http://localhost:8080/mcp/v1/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "tool_name", "arguments": {}, "stream": true}' -N
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

### StreamableHTTP
- HTTP 기반 스트리밍 프로토콜
- Transfer-Encoding: chunked 사용
- NDJSON (Newline Delimited JSON) 형식
- 점진적 데이터 전송 지원
- SSE보다 유연한 커스텀 스트리밍

## 7. 프로토콜 템플릿 작성 시 중요 고려사항

### 필수 Import 관리
```jinja2
{# universal_server_template.jinja2에서 관리 #}
{%- if protocol_type == 'stdio' or protocol_type == 'stream' %}
import asyncio
from typing import AsyncIterator
{%- endif %}

{%- if protocol_type == 'rest' or protocol_type == 'stream' %}
import aiohttp
{%- endif %}
```
- **주의**: 각 프로토콜에 필요한 import를 universal_server_template에서 조건부로 관리
- 프로토콜 템플릿 자체에는 프로토콜 특화 import만 포함

### 비동기 실행 모델 선택
```python
# STDIO: asyncio.run() 사용
if protocol_type == 'stdio':
    asyncio.run(handle_stdio())

# StreamableHTTP: 일반 함수로 실행 (aiohttp가 자체 이벤트 루프 관리)
elif protocol_type == 'stream':
    handle_streamablehttp()  # NOT asyncio.run()
```
- **중요**: aiohttp의 web.run_app()은 자체 이벤트 루프를 생성하므로 asyncio.run()과 충돌
- 프로토콜별 이벤트 루프 관리 방식 확인 필수

### 엔트리 포인트 함수 시그니처
```python
# 비동기 함수 (STDIO 등)
async def handle_stdio():
    server = StdioMCPServer()
    await server.run()

# 동기 함수 (StreamableHTTP 등)
def handle_streamablehttp(host='0.0.0.0', port=8080):
    server = StreamableHTTPMCPServer()
    server.run(host, port)  # web.run_app 내부에서 이벤트 루프 관리
```

### 프로토콜별 응답 형식
```python
# REST/StreamableHTTP: web.Response 또는 web.StreamResponse
return web.json_response({"result": data})

# STDIO: 딕셔너리 반환 (JSON-RPC 형식)
return {"jsonrpc": "2.0", "id": request_id, "result": data}

# WebSocket: 직접 전송
await websocket.send(json.dumps({"result": data}))
```

### 스트리밍 구현 패턴
```python
# StreamableHTTP 스트리밍 예제
async def stream_tool_response(self, tool_name: str, arguments: dict):
    response = web.StreamResponse()
    response.headers['Content-Type'] = 'application/x-ndjson'
    response.headers['Transfer-Encoding'] = 'chunked'
    await response.prepare(request)

    # NDJSON 형식으로 청크 전송
    async for chunk in data_generator():
        await response.write((json.dumps(chunk) + '\n').encode())

    await response.write_eof()
    return response
```

## 8. 디버깅 및 문제 해결

### 일반적인 문제와 해결방법

#### 1. ImportError
```python
# 문제: asyncio가 정의되지 않음
NameError: name 'asyncio' is not defined

# 해결: universal_server_template.jinja2에서 조건부 import 추가
{%- if protocol_type == 'stdio' or protocol_type == 'stream' %}
import asyncio
{%- endif %}
```

#### 2. 이벤트 루프 충돌
```python
# 문제: Cannot run the event loop while another loop is running
RuntimeError: Cannot run the event loop while another loop is running

# 해결: asyncio.run()과 web.run_app() 동시 사용 금지
# 잘못된 코드
asyncio.run(handle_streamablehttp())  # X

# 올바른 코드
handle_streamablehttp()  # O
```

#### 3. 템플릿 Include 누락
```python
# 문제: TODO 코드가 그대로 생성됨
# Streaming protocol handler
async def handle_stream():
    """Handle MCP protocol via HTTP streaming"""
    # TODO: Implement streaming handler
    pass

# 해결: 반드시 {% include %} 사용
{%- elif protocol_type == 'stream' %}
{% include 'server_stream.jinja2' %}
{%- endif %}
```

### 테스트 방법
```bash
# 1. 문법 검증
python -m py_compile mcp_outlook/server_stream.py

# 2. 짧은 테스트 실행 (타임아웃 사용)
timeout 3 python mcp_outlook/server_stream.py

# 3. 백그라운드 실행 및 모니터링
python server_stream.py &
curl -X GET http://localhost:8080/health

# 4. 스트리밍 테스트 (-N 옵션으로 버퍼링 비활성화)
curl -X POST http://localhost:8080/mcp/v1/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "tool", "arguments": {}, "stream": true}' -N
```

### 로깅 추가
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info(f"Processing tool: {tool_name}")
logger.debug(f"Arguments: {arguments}")
```

## 9. 생성된 서버 파일 테스트 (필수)

### 테스트 순서
프로토콜 템플릿 작성 후 **반드시** 다음 순서로 테스트를 수행해야 합니다:

#### 1단계: 서버 파일 생성
```bash
# 템플릿으로부터 실제 서버 파일 생성
python jinja/generate_universal_server.py outlook --protocol stream

# 생성 확인
ls -la mcp_outlook/mcp_server/server_stream.py
```

#### 2단계: 문법 검증
```bash
# Python 문법 오류 확인
python -m py_compile mcp_outlook/mcp_server/server_stream.py

# 임포트 오류 확인
python -c "import mcp_outlook.mcp_server.server_stream"
```

#### 3단계: 서버 시작 테스트
```bash
# 짧은 시간 동안 실행하여 시작 오류 확인
timeout 3 python mcp_outlook/mcp_server/server_stream.py

# 백그라운드 실행
cd mcp_outlook/mcp_server && python server_stream.py &
```

#### 4단계: 엔드포인트 테스트
```bash
# Health check
curl -X GET http://localhost:8080/health

# Initialize
curl -X POST http://localhost:8080/mcp/v1/initialize \
  -H "Content-Type: application/json" \
  -d '{"clientInfo": {"name": "test-client"}}'

# Tools list
curl -X POST http://localhost:8080/mcp/v1/tools/list \
  -H "Content-Type: application/json" \
  -d '{}'

# Tool call (일반)
curl -X POST http://localhost:8080/mcp/v1/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "tool_name", "arguments": {}}'

# Tool call (스트리밍)
curl -X POST http://localhost:8080/mcp/v1/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "tool_name", "arguments": {}, "stream": true}' -N
```

#### 5단계: 오류 수정 사이클
```bash
# 오류 발생 시:
1. 템플릿 수정 (server_stream.jinja2)
2. 서버 재생성
   python jinja/generate_universal_server.py outlook --protocol stream
3. 재테스트
   python -m py_compile mcp_outlook/mcp_server/server_stream.py
4. 반복
```

### 자주 발생하는 테스트 실패와 해결

#### Import 누락
```python
# 오류: NameError: name 'asyncio' is not defined
# 해결: universal_server_template.jinja2에서 조건부 import 추가
```

#### 이벤트 루프 충돌
```python
# 오류: RuntimeError: Cannot run the event loop while another loop is running
# 해결: asyncio.run()과 web.run_app() 동시 사용 확인
```

#### 포트 충돌
```bash
# 오류: [Errno 48] Address already in use
# 해결:
lsof -i :8080
kill -9 [PID]
```

### 테스트 자동화 스크립트
```bash
#!/bin/bash
# test_new_protocol.sh

PROTOCOL=$1
SERVER_NAME=$2
PORT=${3:-8080}

echo "=== Testing $PROTOCOL protocol for $SERVER_NAME ==="

# 1. Generate server
echo "Generating server..."
python jinja/generate_universal_server.py $SERVER_NAME --protocol $PROTOCOL

# 2. Syntax check
echo "Checking syntax..."
python -m py_compile mcp_$SERVER_NAME/mcp_server/server_$PROTOCOL.py || exit 1

# 3. Start server
echo "Starting server..."
timeout 3 python mcp_$SERVER_NAME/mcp_server/server_$PROTOCOL.py &
sleep 2

# 4. Test endpoints
echo "Testing health..."
curl -s http://localhost:$PORT/health | jq .

echo "Testing initialize..."
curl -s -X POST http://localhost:$PORT/mcp/v1/initialize \
  -H "Content-Type: application/json" \
  -d '{"clientInfo": {"name": "test"}}' | jq .

echo "Testing tools list..."
curl -s -X POST http://localhost:$PORT/mcp/v1/tools/list \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.tools | length'

echo "=== Test completed ==="
```

## 10. 체크리스트

새 프로토콜 추가 시 확인사항:

### 필수 체크리스트
- [ ] 프로토콜 템플릿 파일 생성 (`server_[protocol].jinja2`)
- [ ] Universal template에 `{% include %}` 추가 (TODO 코드 금지)
- [ ] 메인 엔트리 포인트 함수 정의 (`handle_[protocol]()`)
- [ ] Protocol base에 프로토콜 추가
- [ ] 생성 스크립트에 옵션 추가
- [ ] 필요한 의존성 패키지 설치

### 생성 및 테스트 체크리스트 (필수)
- [ ] 템플릿으로 서버 파일 생성 완료
- [ ] Python 문법 검증 통과
- [ ] 서버 시작 오류 없음
- [ ] Health check 응답 정상
- [ ] Initialize 엔드포인트 정상
- [ ] Tools/list 엔드포인트 정상
- [ ] Tools/call 엔드포인트 정상
- [ ] 스트리밍 기능 테스트 (해당되는 경우)
- [ ] 에러 처리 검증

### 문서화 체크리스트
- [ ] 프로토콜 특징 문서화
- [ ] 테스트 방법 문서화
- [ ] 트러블슈팅 가이드 작성

## 9. 참고사항

상세한 구현 가이드와 문제 해결 방법은 `stdio_protocol_reference.md` 참조

**작성일**: 2025-12-25
**버전**: 2.1.0
**작성자**: Claude Assistant