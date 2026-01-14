"""
Streaming MCP Server for Calendar MCP Server
Handles MCP protocol via HTTP streaming (SSE)
Generated from universal template with registry data and protocol selection
"""
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys
import os
import logging
import aiohttp
import asyncio
from typing import AsyncIterator

# Add parent directories to path for module access
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)

# Add paths for imports (generalized for all servers)
server_module_dir = os.path.join(grandparent_dir, "mcp_calendar")
if os.path.isdir(server_module_dir):
    sys.path.insert(0, server_module_dir)  # For server-specific relative imports
sys.path.insert(0, grandparent_dir)  # For session module and package imports
sys.path.insert(0, parent_dir)  # For direct module imports

# Import types dynamically based on type_info
# Fallback to simple import if type_locations not available
from mcp_calendar.calendar_types import EventFilterParams, EventSelectParams

# Load tool definitions from YAML (Single Source of Truth)
def _convert_boolean_schema_to_enabled_disabled(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Convert boolean type properties to enabled/disabled enum for OpenAI compatibility.

    OpenAI API does not support boolean type in function parameters.
    This converts at runtime:
        type: boolean, default: true  -> type: string, enum: ["enabled", "disabled"], default: "enabled"
        type: boolean, default: false -> type: string, enum: ["enabled", "disabled"], default: "disabled"
    """
    if not isinstance(schema, dict):
        return schema

    result = dict(schema)

    if 'properties' in result:
        new_properties = {}
        for prop_name, prop_def in result['properties'].items():
            if isinstance(prop_def, dict) and prop_def.get('type') == 'boolean':
                new_prop = dict(prop_def)
                new_prop['type'] = 'string'
                new_prop['enum'] = ['enabled', 'disabled']
                if 'default' in new_prop:
                    new_prop['default'] = 'enabled' if new_prop['default'] else 'disabled'
                new_properties[prop_name] = new_prop
            elif isinstance(prop_def, dict) and prop_def.get('type') == 'object':
                new_properties[prop_name] = _convert_boolean_schema_to_enabled_disabled(prop_def)
            else:
                new_properties[prop_name] = prop_def
        result['properties'] = new_properties

    return result


def _load_mcp_tools() -> List[Dict[str, Any]]:
    """Load MCP tools from tool_definition_templates.yaml and convert boolean types.

    YAML path resolution order:
    1. Environment variable MCP_YAML_PATH (for explicit override)
    2. mcp_editor/mcp_{profile_name}/tool_definition_templates.yaml (profile-specific)
       - Uses calendar which is set correctly at generation time for reused profiles
    3. Fallback to mcp_editor/mcp_{server_name}/tool_definition_templates.yaml (original service)
    """
    # Option 1: Environment variable override
    yaml_path_str = os.environ.get("MCP_YAML_PATH")
    if yaml_path_str:
        yaml_path = Path(yaml_path_str)
    else:
        # Option 2: Profile-specific YAML path (supports reused profiles like outlook_read)
        yaml_path = Path(current_dir).parent.parent / "mcp_editor" / "mcp_calendar" / "tool_definition_templates.yaml"
        if not yaml_path.exists():
            # Option 3: Fallback to original server name (for backwards compatibility)
            yaml_path = Path(current_dir).parent.parent / "mcp_editor" / "mcp_calendar" / "tool_definition_templates.yaml"

    if yaml_path.exists():
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            tools = data.get("tools", [])

            # Convert boolean types to enabled/disabled for OpenAI compatibility
            for tool in tools:
                if 'inputSchema' in tool:
                    tool['inputSchema'] = _convert_boolean_schema_to_enabled_disabled(tool['inputSchema'])

            return tools
    raise FileNotFoundError(f"Tool definition YAML not found: {yaml_path}")

MCP_TOOLS = _load_mcp_tools()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================
# Boolean Parameter Conversion (enabled/disabled <-> bool)
# ============================================================
# OpenAI API does not support boolean type in function parameters.
# We use "enabled"/"disabled" strings externally and convert to bool internally.

def convert_enabled_to_bool(value: Any) -> bool:
    """Convert enabled/disabled string to boolean.

    Args:
        value: "enabled", "disabled", True, False, or None

    Returns:
        True if enabled, False otherwise
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "enabled"
    return False


def convert_bool_to_enabled(value: bool) -> str:
    """Convert boolean to enabled/disabled string.

    Args:
        value: Boolean value

    Returns:
        "enabled" if True, "disabled" if False
    """
    return "enabled" if value else "disabled"

# Import service classes (unique)
# ============================================================
# 기본 서버: calendar
# ============================================================
from mcp_calendar.calendar_service import CalendarService

# Create service instances
calendar_service = CalendarService()

# ============================================================
# Common MCP protocol utilities (shared across protocols)
# ============================================================

SUPPORTED_PROTOCOLS = {"rest", "stdio", "stream"}

# Pre-computed tool -> implementation mapping
TOOL_IMPLEMENTATIONS = {
    "calendar_view": {
        "service_class": "CalendarService",
        "method": "calendar_view"
    },
    "get_event": {
        "service_class": "CalendarService",
        "method": "get_event"
    },
    "create_event": {
        "service_class": "CalendarService",
        "method": "create_event"
    },
    "delete_event": {
        "service_class": "CalendarService",
        "method": "delete_event"
    },
}

# Pre-computed service class -> instance mapping
SERVICE_INSTANCES = {
    "CalendarService": calendar_service,
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
# Service factors are extracted at runtime from MCP_TOOLS mcp_service_factors
# Structure: { tool_name: { 'internal': {...}, 'signature_defaults': {...} } }


def _extract_service_factors(tools: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Extract service factors from mcp_service_factors in tool definitions at runtime.

    Returns:
        Dict with structure:
        {
            tool_name: {
                'internal': { factor_name: {...}, ... },
                'signature_defaults': { factor_name: {...}, ... }
            }
        }
    """
    service_factors = {}

    for tool in tools:
        tool_name = tool.get('name', '')
        mcp_service_factors = tool.get('mcp_service_factors', {})

        tool_factors = {
            'internal': {},
            'signature_defaults': {}
        }

        for factor_name, factor_data in mcp_service_factors.items():
            source = factor_data.get('source', '')

            # Only process 'internal' and 'signature_defaults' sources
            if source not in ('internal', 'signature_defaults'):
                continue

            # Support both 'type' (new) and 'baseModel' (legacy) field names
            factor_type = factor_data.get('type') or factor_data.get('baseModel', '')

            # targetParam handling
            target_param = factor_data.get('targetParam', factor_name)

            # Get parameters - handle both list format (new) and dict format (legacy)
            raw_params = factor_data.get('parameters', [])
            if isinstance(raw_params, list):
                params_dict = {}
                for param in raw_params:
                    name = param.get("name")
                    if not name:
                        continue
                    param_dict = {"type": param.get("type", "string")}
                    if param.get("has_default", False):
                        param_dict["default"] = param.get("default")
                    if param.get("description"):
                        param_dict["description"] = param["description"]
                    params_dict[name] = param_dict
            else:
                params_dict = raw_params  # Already a dict

            # Extract default values from parameters
            default_values = {}
            for param_name, param_def in params_dict.items():
                if 'default' in param_def:
                    default_values[param_name] = param_def['default']

            # Build the factor structure
            factor_info = {
                'targetParam': target_param,
                'type': factor_type,
                'source': source,
                'value': default_values,
                'original_schema': {
                    'targetParam': target_param,
                    'properties': params_dict,
                    'type': 'object'
                }
            }

            tool_factors[source][factor_name] = factor_info

        # Only add if there are any factors
        if tool_factors['internal'] or tool_factors['signature_defaults']:
            service_factors[tool_name] = tool_factors

    return service_factors


def _extract_internal_args(tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract internal args from service factors (legacy compatibility)."""
    service_factors = _extract_service_factors(tools)

    # Convert to legacy internal_args format
    internal_args = {}
    for tool_name, factors in service_factors.items():
        tool_internal = {}
        for factor_name, factor_info in factors.get('internal', {}).items():
            tool_internal[factor_name] = {
                'targetParam': factor_info['targetParam'],
                'type': factor_info['type'],
                'value': factor_info['value'],
                'original_schema': factor_info['original_schema']
            }
        if tool_internal:
            internal_args[tool_name] = tool_internal

    return internal_args


# MCP_TOOLS already loaded from YAML above (contains mcp_service_factors)
# Use it directly for service factors extraction

# Extract at module load time from MCP_TOOLS (which have mcp_service_factors)
SERVICE_FACTORS = _extract_service_factors(MCP_TOOLS)
INTERNAL_ARGS = _extract_internal_args(MCP_TOOLS)

# Build INTERNAL_ARG_TYPES dynamically based on imported types
INTERNAL_ARG_TYPES = {}
if 'EventFilterParams' in globals():
    INTERNAL_ARG_TYPES['EventFilterParams'] = EventFilterParams
if 'EventSelectParams' in globals():
    INTERNAL_ARG_TYPES['EventSelectParams'] = EventSelectParams


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

async def handle_calendar_view(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle calendar_view tool call"""

    # ========================================
    # Step 1: Signature 파라미터 수신
    # - LLM으로부터 전달받은 인자 추출
    # ========================================
    user_email = args["user_email"]
    start_datetime = args["start_datetime"]
    end_datetime = args["end_datetime"]

    # ========================================
    # Step 2: 서비스 호출 인자 구성
    # ========================================
    call_args = {}
    call_args["user_email"] = user_email
    call_args["start_datetime"] = start_datetime
    call_args["end_datetime"] = end_datetime

    # ========================================
    # Step 3: 서비스 메서드 호출
    # ========================================
    return await calendar_service.calendar_view(**call_args)

async def handle_get_event(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get_event tool call"""

    # ========================================
    # Step 1: Signature 파라미터 수신
    # - LLM으로부터 전달받은 인자 추출
    # ========================================
    user_email = args["user_email"]
    event_id = args["event_id"]

    # ========================================
    # Step 2: 서비스 호출 인자 구성
    # ========================================
    call_args = {}
    call_args["user_email"] = user_email
    call_args["event_id"] = event_id

    # ========================================
    # Step 3: 서비스 메서드 호출
    # ========================================
    return await calendar_service.get_event(**call_args)

async def handle_create_event(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle create_event tool call"""

    # ========================================
    # Step 1: Signature 파라미터 수신
    # - LLM으로부터 전달받은 인자 추출
    # ========================================
    user_email = args["user_email"]
    subject = args["subject"]
    start = args["start"]
    end = args["end"]
    body_sig = args.get("body")
    body = body_sig if body_sig is not None else None
    location_sig = args.get("location")
    location = location_sig if location_sig is not None else None

    # ========================================
    # Step 2: 서비스 호출 인자 구성
    # ========================================
    call_args = {}
    call_args["user_email"] = user_email
    call_args["subject"] = subject
    call_args["start"] = start
    call_args["end"] = end
    call_args["body"] = body
    call_args["location"] = location

    # ========================================
    # Step 3: 서비스 메서드 호출
    # ========================================
    return await calendar_service.create_event(**call_args)

async def handle_delete_event(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle delete_event tool call"""

    # ========================================
    # Step 1: Signature 파라미터 수신
    # - LLM으로부터 전달받은 인자 추출
    # ========================================
    user_email = args["user_email"]
    event_id = args["event_id"]

    # ========================================
    # Step 2: 서비스 호출 인자 구성
    # ========================================
    call_args = {}
    call_args["user_email"] = user_email
    call_args["event_id"] = event_id

    # ========================================
    # Step 3: 서비스 메서드 호출
    # ========================================
    return await calendar_service.delete_event(**call_args)

# ============================================================
# StreamableHTTP Protocol Implementation for MCP Server
# ============================================================
# Note: This template is included by universal_server_template.jinja2
# All common imports and utilities are defined in the parent template

from aiohttp import web

# Use the logger from parent template
logger = logging.getLogger(__name__)

class StreamableHTTPMCPServer:
    """MCP StreamableHTTP Protocol Server

    HTTP 기반 스트리밍 프로토콜로 청크 단위의 응답을 지원합니다.
    Transfer-Encoding: chunked를 사용하여 점진적 응답 전송이 가능합니다.
    """

    def __init__(self):
        self.app = web.Application()
        self.setup_routes()
        logger.info(f"Calendar MCP Server StreamableHTTP Server initialized")

    def setup_routes(self):
        """HTTP 라우트 설정"""
        # MCP Streamable HTTP 단일 엔드포인트 (표준)
        self.app.router.add_post('/mcp/v1', self.handle_mcp_request)
        self.app.router.add_get('/mcp/v1', self.handle_sse_connection)  # SSE 연결
        # Legacy 개별 엔드포인트 (호환성)
        self.app.router.add_post('/mcp/v1/initialize', self.handle_initialize)
        self.app.router.add_post('/mcp/v1/tools/list', self.handle_tools_list)
        self.app.router.add_post('/mcp/v1/tools/call', self.handle_tools_call)
        # Health check
        self.app.router.add_get('/health', self.handle_health)
        # CORS 처리
        self.app.router.add_route('OPTIONS', '/{path:.*}', self.handle_options)

    async def handle_options(self, request: web.Request) -> web.Response:
        """CORS preflight 요청 처리"""
        return web.Response(
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '3600'
            }
        )

    def add_cors_headers(self, response: web.Response) -> web.Response:
        """CORS 헤더 추가"""
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    async def handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        response = web.json_response({
            "status": "healthy",
            "server": "calendar",
            "protocol": "streamableHTTP",
            "version": "1.0.0"
        })
        return self.add_cors_headers(response)

    async def handle_sse_connection(self, request: web.Request) -> web.StreamResponse:
        """SSE 연결 핸들러 - MCP Streamable HTTP GET 요청 처리"""
        logger.info("SSE connection established")

        response = web.StreamResponse()
        response.headers['Content-Type'] = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        response.headers['Access-Control-Allow-Origin'] = '*'

        await response.prepare(request)

        # 초기 연결 확인 이벤트 전송
        init_event = {
            "jsonrpc": "2.0",
            "method": "connection/ready",
            "params": {
                "serverInfo": {
                    "name": "calendar",
                    "version": "1.0.0"
                }
            }
        }
        await response.write(f"data: {json.dumps(init_event)}\n\n".encode())

        # SSE 연결 유지 (keep-alive)
        try:
            while True:
                # 30초마다 ping 전송
                await asyncio.sleep(30)
                ping_event = {"jsonrpc": "2.0", "method": "ping"}
                await response.write(f"data: {json.dumps(ping_event)}\n\n".encode())
        except asyncio.CancelledError:
            logger.info("SSE connection closed")
        except Exception as e:
            logger.error(f"SSE error: {e}")

        return response

    async def handle_mcp_request(self, request: web.Request) -> web.Response:
        """MCP Streamable HTTP 단일 엔드포인트 - JSON-RPC method로 분기"""
        try:
            data = await request.json()
            method = data.get('method', '')
            request_id = data.get('id')
            params = data.get('params', {})

            logger.info(f"MCP Request: method={method}, id={request_id}")

            # Method별 분기
            if method == 'initialize':
                return await self._handle_initialize(data)
            elif method == 'tools/list':
                return await self._handle_tools_list(data)
            elif method == 'tools/call':
                return await self._handle_tools_call(data, request)
            elif method == 'notifications/initialized':
                # 클라이언트 초기화 완료 알림 - 응답 불필요
                return web.Response(status=204)
            elif method == 'ping':
                response = web.json_response({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {}
                })
                return self.add_cors_headers(response)
            else:
                # MCP 프로토콜: 에러도 HTTP 200으로 응답
                response = web.json_response({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                })
                return self.add_cors_headers(response)

        except Exception as e:
            logger.error(f"Error in MCP request: {e}", exc_info=True)
            return web.json_response(
                {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}
            )

    async def _handle_initialize(self, data: dict) -> web.Response:
        """내부 initialize 처리"""
        request_id = data.get('id')
        params = data.get('params', {})
        client_info = params.get('clientInfo', {})
        logger.info(f"Client connected: {client_info.get('name', 'unknown')}")

        response_data = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "calendar",
                    "version": "1.0.0"
                }
            }
        }
        response = web.json_response(response_data)
        return self.add_cors_headers(response)

    async def _handle_tools_list(self, data: dict) -> web.Response:
        """내부 tools/list 처리"""
        request_id = data.get('id')

        tools_with_streaming = []
        for tool in MCP_TOOLS:
            tool_copy = tool.copy()
            tool_copy['supportsStreaming'] = True
            tools_with_streaming.append(tool_copy)

        response_data = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": tools_with_streaming
            }
        }
        response = web.json_response(response_data)
        return self.add_cors_headers(response)

    async def _handle_tools_call(self, data: dict, request: web.Request) -> web.Response:
        """내부 tools/call 처리"""
        request_id = data.get('id')
        params = data.get('params', {})
        tool_name = params.get('name')
        arguments = params.get('arguments', {})

        if not tool_name:
            response = web.json_response(
                {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": "Tool name is required"}}
            )
            return self.add_cors_headers(response)

        arguments = self.apply_schema_defaults(tool_name, arguments)

        handler_name = f"handle_{tool_name.replace('-', '_')}"
        if handler_name not in globals():
            response = web.json_response(
                {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"}}
            )
            return self.add_cors_headers(response)

        try:
            result = await globals()[handler_name](arguments)

            if isinstance(result, dict) and "content" in result:
                content = result["content"]
            elif isinstance(result, str):
                content = [{"type": "text", "text": result}]
            else:
                content = [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]

            response_data = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": content
                }
            }
            response = web.json_response(response_data)
            return self.add_cors_headers(response)

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            # MCP 프로토콜: 에러도 HTTP 200으로 응답, JSON-RPC error로 전달
            response = web.json_response(
                {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32603, "message": str(e)}}
            )
            return self.add_cors_headers(response)

    async def handle_initialize(self, request: web.Request) -> web.Response:
        """Initialize endpoint - JSON-RPC 2.0 compliant"""
        try:
            data = await request.json()
            request_id = data.get('id')
            params = data.get('params', {})
            client_info = params.get('clientInfo', {})
            logger.info(f"Client connected: {client_info.get('name', 'unknown')}")

            response_data = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "calendar",
                        "version": "1.0.0"
                    }
                }
            }

            response = web.json_response(response_data)
            return self.add_cors_headers(response)

        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            return web.json_response(
                {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}},
                status=500
            )

    async def handle_tools_list(self, request: web.Request) -> web.Response:
        """List available tools - JSON-RPC 2.0 compliant"""
        try:
            data = await request.json()
            request_id = data.get('id')

            # MCP_TOOLS에 스트리밍 지원 정보 추가
            tools_with_streaming = []
            for tool in MCP_TOOLS:
                tool_copy = tool.copy()
                tool_copy['supportsStreaming'] = True
                tools_with_streaming.append(tool_copy)

            response_data = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": tools_with_streaming
                }
            }

            response = web.json_response(response_data)
            return self.add_cors_headers(response)

        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return web.json_response(
                {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}},
                status=500
            )

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

    async def handle_tools_call(self, request: web.Request) -> web.Response:
        """도구 실행 - JSON-RPC 2.0 compliant"""
        tool_name = None
        request_id = None
        try:
            data = await request.json()
            request_id = data.get('id')
            params = data.get('params', {})
            tool_name = params.get('name')
            arguments = params.get('arguments', {})
            stream = params.get('stream', False)

            if not tool_name:
                response = web.json_response(
                    {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": "Tool name is required"}}
                )
                return self.add_cors_headers(response)

            # Apply default values from inputSchema
            arguments = self.apply_schema_defaults(tool_name, arguments)

            # 도구 핸들러 검색
            handler_name = f"handle_{tool_name.replace('-', '_')}"
            if handler_name not in globals():
                response = web.json_response(
                    {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"}}
                )
                return self.add_cors_headers(response)

            if stream:
                # 스트리밍 응답
                return await self.stream_tool_response(tool_name, arguments, request)
            else:
                # 일반 응답
                result = await globals()[handler_name](arguments)

                # 결과 포맷팅
                if isinstance(result, dict) and "content" in result:
                    content = result["content"]
                elif isinstance(result, str):
                    content = [{"type": "text", "text": result}]
                else:
                    content = [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]

                response_data = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": content
                    }
                }

                response = web.json_response(response_data)
                return self.add_cors_headers(response)

        except ValueError as e:
            response = web.json_response(
                {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": str(e)}}
            )
            return self.add_cors_headers(response)
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            # MCP 프로토콜: 에러도 HTTP 200으로 응답, JSON-RPC error로 전달
            response = web.json_response(
                {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32603, "message": str(e)}}
            )
            return self.add_cors_headers(response)

    async def stream_tool_response(self, tool_name: str, arguments: dict, request: web.Request) -> web.StreamResponse:
        """도구 응답을 스트리밍으로 전송"""
        response = web.StreamResponse()
        response.headers['Content-Type'] = 'application/x-ndjson'  # Newline Delimited JSON
        response.headers['Transfer-Encoding'] = 'chunked'
        response.headers['Cache-Control'] = 'no-cache'

        # CORS 헤더 추가
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'

        await response.prepare(request)

        try:
            # 도구 핸들러 실행
            handler_name = f"handle_{tool_name.replace('-', '_')}"
            handler = globals()[handler_name]

            # 스트리밍 가능한 도구인지 확인
            if asyncio.iscoroutinefunction(handler):
                result = await handler(arguments)

                # 결과를 청크로 분할하여 전송 (시뮬레이션)
                if isinstance(result, str):
                    # 텍스트를 청크로 분할
                    chunks = [result[i:i+100] for i in range(0, len(result), 100)]
                    for i, chunk in enumerate(chunks):
                        chunk_data = {
                            "type": "chunk",
                            "content": chunk,
                            "index": i,
                            "done": False
                        }
                        await response.write((json.dumps(chunk_data) + '\n').encode('utf-8'))
                        await asyncio.sleep(0.1)  # 스트리밍 효과

                elif isinstance(result, dict):
                    # 딕셔너리를 부분적으로 전송
                    chunk_data = {
                        "type": "chunk",
                        "content": result,
                        "index": 0,
                        "done": False
                    }
                    await response.write((json.dumps(chunk_data) + '\n').encode('utf-8'))

                elif isinstance(result, list):
                    # 리스트 항목을 하나씩 전송
                    for i, item in enumerate(result):
                        chunk_data = {
                            "type": "chunk",
                            "content": item,
                            "index": i,
                            "done": False
                        }
                        await response.write((json.dumps(chunk_data) + '\n').encode('utf-8'))
                        await asyncio.sleep(0.05)  # 스트리밍 효과

            # 완료 신호
            end_chunk = {
                "type": "end",
                "done": True,
                "summary": f"Completed {tool_name} execution"
            }
            await response.write((json.dumps(end_chunk) + '\n').encode('utf-8'))

        except Exception as e:
            # 에러 청크 전송
            error_chunk = {
                "type": "error",
                "error": {"code": -32603, "message": str(e)},
                "done": True
            }
            await response.write((json.dumps(error_chunk) + '\n').encode('utf-8'))
            logger.error(f"Streaming error for {tool_name}: {e}", exc_info=True)

        finally:
            await response.write_eof()

        return response

    async def on_startup(self, app):
        """서버 시작 시 실행"""
        logger.info(f"Calendar MCP Server StreamableHTTP Server starting on port {app['port']}")

        # Initialize services
        if hasattr(calendar_service, 'initialize'):
            await calendar_service.initialize()
            logger.info("CalendarService initialized")

    async def on_cleanup(self, app):
        """서버 종료 시 정리"""
        logger.info(f"Calendar MCP Server StreamableHTTP Server shutting down")

    def run(self, host: str = '0.0.0.0', port: int = 8001):
        """서버 실행"""
        self.app['port'] = port
        self.app.on_startup.append(self.on_startup)
        self.app.on_cleanup.append(self.on_cleanup)

        logger.info(f"Starting Calendar MCP Server StreamableHTTP Server on {host}:{port}")
        web.run_app(self.app, host=host, port=port, print=lambda _: None)

# 메인 엔트리 포인트
def handle_streamablehttp(host: str = '0.0.0.0', port: int = 8001):
    """Handle MCP protocol via StreamableHTTP"""
    server = StreamableHTTPMCPServer()
    server.run(host, port)

if __name__ == "__main__":
    # Port can be set via environment variable or defaults to template value
    port = int(os.environ.get("MCP_SERVER_PORT", 8080))
    handle_streamablehttp(host="0.0.0.0", port=port)  # StreamableHTTP server