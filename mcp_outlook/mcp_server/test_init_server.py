"""
FastAPI MCP Server for Outlook
Generated from registry-based tool definitions
Routes MCP protocol requests to service implementations
"""
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys
import os
import logging

# Add parent directories to path for module access
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
grandparent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, grandparent_dir)  # For session module and package imports
sys.path.insert(0, parent_dir)  # For direct module imports from parent directory
# Import parameter types
from outlook_types import FilterParams, SelectParams

# Import tool definitions
from tool_definitions import MCP_TOOLS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import server-specific initialization module
try:
    from server_init import (
        initialize_services,
        initialize_session,
        cleanup_services,
        get_service_config,
        validate_environment
    )
    HAS_CUSTOM_INIT = True
    logger.info("Custom initialization module loaded")
except ImportError:
    HAS_CUSTOM_INIT = False
    logger.info("No custom initialization module, using default behavior")
    # Default implementations
    async def initialize_services(context): pass
    async def initialize_session(session, user_email): pass
    async def cleanup_services(context): pass
    def get_service_config(): return {}
    def validate_environment(): return True

# Server context for sharing state
server_context = {
    'server_name': 'outlook',
    'use_session_manager': False,
    'services': {},
    'config': get_service_config()
}
# SessionManager is disabled for this server
USE_SESSION_MANAGER = False
session_manager = None
Session = None
logger.info("Server configured without SessionManager")

# Import service classes
# Import from nested module path
from mcp_outlook.graph_mail_query import GraphMailQuery
from mock_service import Service

app = FastAPI(title="Outlook MCP Server", version="1.0.0")

# Global instances for legacy mode (when SessionManager not available)
if not USE_SESSION_MANAGER:
    graph_mail_query = GraphMailQuery()
    server_context['services']['graph_mail_query'] = graph_mail_query
    service = Service()
    server_context['services']['service'] = service


@app.on_event("startup")
async def startup_event():
    """Initialize server on startup"""
    # Validate environment first
    if not validate_environment():
        logger.error("Environment validation failed, some features may not work correctly")

    # Initialize SessionManager if available
    if USE_SESSION_MANAGER:
        await session_manager.start()
        logger.info("SessionManager started")
    else:
        logger.info("Server started in legacy mode without SessionManager")

    # Call custom initialization
    await initialize_services(server_context)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup server on shutdown"""
    # Call custom cleanup first
    await cleanup_services(server_context)

    # Stop SessionManager if available
    if USE_SESSION_MANAGER:
        await session_manager.stop()
        logger.info("SessionManager stopped")
    else:
        logger.info("Server shutdown in legacy mode")


async def ensure_services_initialized_legacy(user_email: Optional[str] = None):
    """
    Legacy method: Ensure services are initialized before use
    Used when SessionManager is not available
    """
    # Use custom initialization if available
    if HAS_CUSTOM_INIT:
        # Create a temporary session-like context for legacy mode
        legacy_session = type('LegacySession', (), server_context['services'])()
        legacy_session.user_email = user_email
        await initialize_session(legacy_session, user_email)
    else:
        # Fallback to default behavior
        # Outlook services may need authentication initialization
        # Initialize each service instance
        if hasattr(graph_mail_query, 'initialize'):
            await graph_mail_query.initialize(user_email)
        if hasattr(service, 'initialize'):
            await service.initialize(user_email)


async def handle_token_error(e: Exception, user_email: str):
    """
    Handle authentication errors by clearing cache and raising appropriate error
    """
    import traceback
    error_str = str(e).lower()
    tb = traceback.format_exc()

    if 'invalid_grant' in error_str or 'token' in error_str or 'unauthorized' in error_str:
        # Clear token cache for this user
        logger.warning(f"Token error for {user_email}: {error_str}")

        # Try to invalidate session if using SessionManager
        if USE_SESSION_MANAGER:
            await session_manager.invalidate_session(user_email)

        raise HTTPException(
            status_code=401,
            detail={
                "error": "authentication_failed",
                "message": f"Authentication failed for {user_email}. Please re-authenticate.",
                "user": user_email
            }
        )
    else:
        # Other errors - log and re-raise
        logger.error(f"Error for {user_email}: {tb}")
        raise


async def get_user_session_or_legacy(user_email: str, access_token: Optional[str] = None) -> Any:
    """
    Get session for user (if SessionManager available) or return legacy context

    Returns:
        Either a Session object or a legacy context dict
    """
    if USE_SESSION_MANAGER:
        # Session-based approach
        session = await session_manager.get_or_create_session(user_email)

        # Initialize session with access token if provided
        if access_token and not session.initialized:
            await session.initialize(access_token)
            # Call custom session initialization if available
            if HAS_CUSTOM_INIT:
                await initialize_session(session, user_email)
        elif access_token:
            # Update the access token on already initialized session
            session.access_token = access_token
            if hasattr(session, 'graph_mail_client'):
                session.graph_mail_client.access_token = access_token

        return session
    else:
        # Legacy approach - ensure services are initialized
        await ensure_services_initialized_legacy(user_email)
        # Return a dict that mimics session structure for compatibility
        return {
            "user_email": user_email,
            "access_token": access_token,
            "is_legacy": True
        }


def get_service_instance(context: Any, service_name: str, service_class: str):
    """
    Get service instance from session context or legacy globals

    Args:
        context: Either a Session object or legacy context dict
        service_name: Variable name of the service instance
        service_class: Class name of the service
    """
    if USE_SESSION_MANAGER and not isinstance(context, dict):
        # Session-based approach - get service from session attributes
        # Services are stored as attributes on the session object
        # e.g., session.graph_mail_query, session.graph_mail_client
        if hasattr(context, service_name):
            return getattr(context, service_name)
        # Fallback to checking for the class name in lowercase
        elif hasattr(context, service_class.lower()):
            return getattr(context, service_class.lower())
        else:
            # Create instance if needed (for non-Outlook servers)
            instance = globals()[service_class]()
            setattr(context, service_name, instance)
            return instance
    else:
        # Legacy approach - use global instance
        return globals()[service_name]


# Helper functions for getting specific service instances
def get_graph_mail_query_instance(context: Any):
    """Get GraphMailQuery instance from context"""
    return get_service_instance(context, "graph_mail_query", "GraphMailQuery")


def get_service_instance(context: Any):
    """Get Service instance from context"""
    return get_service_instance(context, "service", "Service")




def build_internal_param(tool_name: str, param_name: str, param_config: Dict[str, Any] = None) -> Any:
    """
    Build internal parameter object from pre-configured values
    Used for parameters not exposed in MCP signature but needed by service
    """
    if not param_config:
        return None

    # Get the default value and type from config
    default_value = param_config.get('default')
    param_type = param_config.get('type', 'any')
    class_name = param_config.get('class')

    # If it's a class-based parameter, instantiate it
    if class_name:
        try:
            # Try to get the class from globals
            if class_name in globals():
                param_class = globals()[class_name]
                if isinstance(default_value, dict):
                    return param_class(**default_value)
                elif default_value is not None:
                    return param_class(default_value)
                else:
                    return param_class()
        except Exception as e:
            logger.warning(f"Could not instantiate {class_name} for {tool_name}.{param_name}: {e}")

    # Return the default value directly
    return default_value


def create_error_response(request_id: Any, code: int, message: str) -> JSONResponse:
    """Create MCP error response"""
    return JSONResponse(content={
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code,
            "message": message
        }
    })


# MCP Protocol Models
class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Any] = None
    method: str
    params: Optional[Dict[str, Any]] = {}


class ToolCallParams(BaseModel):
    name: str
    arguments: Dict[str, Any]


class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Any] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


@app.get("/sessions")
async def get_sessions_info():
    """Get information about active sessions"""
    if USE_SESSION_MANAGER:
        return session_manager.get_session_info()
    else:
        return {
            "message": "SessionManager not available - running in legacy mode",
            "mode": "legacy",
            "info": "All requests share global instances"
        }


@app.post("/")
async def handle_mcp_request(request: Request):
    """Main MCP protocol handler"""
    try:
        body = await request.json()
        mcp_request = MCPRequest(**body)

        # Route based on MCP method
        if mcp_request.method == "initialize":
            return handle_initialize(mcp_request)
        elif mcp_request.method == "tools/list":
            return handle_list_tools(mcp_request)
        elif mcp_request.method == "tools/call":
            return await handle_tool_call(mcp_request)
        else:
            return create_error_response(
                mcp_request.id,
                -32601,
                f"Method not found: {mcp_request.method}"
            )
    except Exception as e:
        return create_error_response(
            body.get("id") if "body" in locals() else None,
            -32603,
            f"Internal error: {str(e)}"
        )


def handle_initialize(request: MCPRequest) -> JSONResponse:
    """Handle MCP initialize request"""
    return JSONResponse(content={
        "jsonrpc": "2.0",
        "id": request.id,
        "result": {
            "protocolVersion": "2025-06-18",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "outlook-mcp-server",
                "version": "1.0.0"
            }
        }
    })


def handle_list_tools(request: MCPRequest) -> JSONResponse:
    """Handle MCP tools/list request"""
    return JSONResponse(content={
        "jsonrpc": "2.0",
        "id": request.id,
        "result": {
            "tools": MCP_TOOLS
        }
    })


async def handle_tool_call(request: MCPRequest) -> JSONResponse:
    """Handle MCP tools/call request - routes to appropriate function"""
    try:
        tool_name = request.params.get("name")
        arguments = request.params.get("arguments", {})

        # Route to appropriate handler
        if tool_name == "Outlook":
            result = await handle_Outlook(arguments)
        elif tool_name == "keyword_search":
            result = await handle_keyword_search(arguments)
        elif tool_name == "query_url":
            result = await handle_query_url(arguments)
        elif tool_name == "mail_list":
            result = await handle_mail_list(arguments)
        else:
            return create_error_response(
                request.id,
                -32602,
                f"Unknown tool: {tool_name}"
            )

        return JSONResponse(content={
            "jsonrpc": "2.0",
            "id": request.id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        })
    except Exception as e:
        return create_error_response(
            request.id,
            -32603,
            f"Tool execution error: {str(e)}"
        )


# Tool handler functions - routing to service implementations

async def handle_Outlook(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailQuery.query_filter with session or legacy support"""
    # Get session or legacy instances
    user_email = args.get("user_email", "default")
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))
    # Extract parameters from args
    top = args.get("top")
    # Convert dicts to parameter objects where needed
    filter_params = FilterParams(**args["filter"])
    # Internal Args (pre-configured defaults, not exposed to MCP)
    exclude_params = build_internal_param("Outlook", "exclude", {'description': 'ExcludeParams for filtering out emails', 'original_schema': {'description': 'ExcludeParams for filtering out emails', 'properties': {'exclude_sender_address': {'default': 'block@krs.co.kr', 'description': '제외할 실제 발신자 주소 (sender 필드)', 'oneOf': [{'type': 'string'}, {'items': {'type': 'string'}, 'type': 'array'}]}}, 'type': 'object'}, 'type': 'ExcludeParams', 'was_required': False})
    select_params = build_internal_param("Outlook", "select", {'description': 'SelectParams for selecting fields', 'original_schema': {'baseModel': 'SelectParams', 'description': 'SelectParams for selecting fields', 'properties': {'bcc_recipients': {'description': '숨은 참조 (Bcc:) 수신자 목록', 'type': 'boolean'}, 'body': {'description': '메시지 본문 (HTML 또는 텍스트 형식)', 'type': 'boolean'}, 'body_preview': {'description': '메시지 본문의 처음 255자 (텍스트 형식)', 'type': 'boolean'}, 'categories': {'description': '메시지에 연결된 카테고리 목록', 'type': 'boolean'}, 'cc_recipients': {'description': '참조 (Cc:) 수신자 목록', 'type': 'boolean'}, 'change_key': {'description': '메시지 버전 키', 'type': 'boolean'}, 'conversation_id': {'description': '이메일이 속한 대화의 ID', 'type': 'boolean'}, 'conversation_index': {'description': '대화 내 메시지 위치를 나타내는 인덱스', 'type': 'boolean'}, 'created_date_time': {'description': '메시지 생성 날짜/시간 (ISO 8601 형식, UTC)', 'type': 'boolean'}, 'fields': {'description': '조회할 필드 목록 (미지정 시 모든 필드 반환)', 'items': {'type': 'string'}, 'type': 'array'}, 'flag': {'description': '메시지의 플래그 상태, 시작 날짜, 기한, 완료 날짜', 'type': 'boolean'}, 'from_recipient': {'description': '메시지가 전송된 사서함의 소유자 (from 필드)', 'type': 'boolean'}, 'has_attachments': {'description': '첨부파일 포함 여부', 'type': 'boolean'}, 'id': {'description': '메시지 고유 식별자 (읽기 전용)', 'type': 'boolean'}, 'importance': {'description': '메시지 중요도 (low, normal, high)', 'type': 'boolean'}, 'inference_classification': {'description': '메시지 분류 (focused 또는 other)', 'type': 'boolean'}, 'internet_message_headers': {'description': 'RFC5322에 정의된 메시지 헤더 컬렉션 (읽기 전용)', 'type': 'boolean'}, 'internet_message_id': {'description': 'RFC2822 형식의 메시지 ID', 'type': 'boolean'}, 'is_delivery_receipt_requested': {'description': '배달 확인 요청 여부', 'type': 'boolean'}, 'is_draft': {'description': '메시지가 임시 저장 상태인지 여부', 'type': 'boolean'}, 'is_read': {'description': '메시지 읽음 상태', 'type': 'boolean'}, 'is_read_receipt_requested': {'description': '읽음 확인 요청 여부', 'type': 'boolean'}, 'last_modified_date_time': {'description': '메시지 최종 수정 날짜/시간 (ISO 8601 형식, UTC)', 'type': 'boolean'}, 'parent_folder_id': {'description': '부모 메일 폴더의 고유 식별자', 'type': 'boolean'}, 'received_date_time': {'description': '메시지 수신 날짜/시간 (ISO 8601 형식, UTC)', 'type': 'boolean'}, 'reply_to': {'description': '회신 시 사용할 이메일 주소 목록', 'type': 'boolean'}, 'sender': {'description': '메시지를 생성하는 데 사용된 계정', 'type': 'boolean'}, 'sent_date_time': {'description': '메시지 발신 날짜/시간 (ISO 8601 형식, UTC)', 'type': 'boolean'}, 'subject': {'description': '메시지 제목', 'type': 'boolean'}, 'to_recipients': {'description': '받는 사람 (To:) 목록', 'type': 'boolean'}, 'unique_body': {'description': '현재 메시지에 고유한 본문 부분', 'type': 'boolean'}, 'web_link': {'description': 'Outlook Web에서 메시지를 열기 위한 URL', 'type': 'boolean'}}, 'required': [], 'type': 'object'}, 'type': 'SelectParams', 'was_required': False})

    try:
        # Get the service instance
        service_instance = get_graph_mail_query_instance(context)

        # Build call parameters
        call_params = {}
        call_params["filter"] = filter_params
        call_params["top"] = top
        call_params["user_email"] = user_email
        call_params["exclude"] = exclude_params
        call_params["select"] = select_params

        # Call the service method
        return await service_instance.query_filter(**call_params)
    except Exception as e:
        await handle_token_error(e, user_email)

async def handle_keyword_search(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to Service.keyword_search with session or legacy support"""
    # Get session or legacy instances
    user_email = args.get("user_email", "default")
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))
    # Extract parameters from args
    client_filter = args.get("client_filter")
    orderby = args.get("orderby")
    search = args["search"]
    top = args.get("top")
    # Convert dicts to parameter objects where needed
    select_dict = args.get("select")
    select_params = SelectParams(**select_dict) if select_dict else None

    try:
        # Get the service instance
        service_instance = get_service_instance(context)

        # Build call parameters
        call_params = {}
        call_params["client_filter"] = client_filter
        call_params["orderby"] = orderby
        call_params["search"] = search
        call_params["select"] = select_params
        call_params["top"] = top
        call_params["user_email"] = user_email

        # Call the service method
        return await service_instance.keyword_search(**call_params)
    except Exception as e:
        await handle_token_error(e, user_email)

async def handle_query_url(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailQuery.query_url with session or legacy support"""
    # Get session or legacy instances
    user_email = args.get("user_email", "default")
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))
    # Extract parameters from args
    client_filter = args.get("client_filter")
    top = args.get("top")
    url = args["url"]

    try:
        # Get the service instance
        service_instance = get_graph_mail_query_instance(context)

        # Build call parameters
        call_params = {}
        call_params["client_filter"] = client_filter
        call_params["top"] = top
        call_params["url"] = url
        call_params["user_email"] = user_email

        # Call the service method
        return await service_instance.query_url(**call_params)
    except Exception as e:
        await handle_token_error(e, user_email)

async def handle_mail_list(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to Service.mail_list with session or legacy support"""
    # Get session or legacy instances
    user_email = args.get("user_email", "default")
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))
    # Extract parameters from args
    top = args.get("top")
    # Convert dicts to parameter objects where needed
    filter_params = FilterParams(**args["filter"])
    # Internal Args (pre-configured defaults, not exposed to MCP)
    client_filter_params = build_internal_param("mail_list", "client_filter", {'description': 'FilterParams for client-side filtering', 'original_schema': {'description': 'FilterParams for client-side filtering', 'type': 'object'}, 'type': 'FilterParams', 'was_required': False})
    exclude_params = build_internal_param("mail_list", "exclude", {'description': 'ExcludeParams parameters', 'original_schema': {'baseModel': 'ExcludeParams', 'description': 'ExcludeParams parameters', 'properties': {'exclude_from_address': {'default': 'block@krs.co.kr', 'description': '제외할 발신자 주소 (from 필드)', 'type': 'string'}}, 'required': [], 'type': 'object'}, 'type': 'ExcludeParams', 'was_required': False})
    select_params = build_internal_param("mail_list", "select", {'description': 'SelectParams parameters', 'original_schema': {'baseModel': 'SelectParams', 'description': 'SelectParams parameters', 'properties': {'body_preview': {'default': True, 'description': '메시지 본문의 처음 255자 (텍스트 형식)', 'type': 'boolean'}, 'has_attachments': {'default': True, 'description': '첨부파일 포함 여부', 'type': 'boolean'}, 'sender': {'default': True, 'description': '메시지를 생성하는 데 사용된 계정', 'type': 'boolean'}, 'subject': {'default': True, 'description': '메시지 제목', 'type': 'boolean'}}, 'required': [], 'type': 'object'}, 'type': 'SelectParams', 'was_required': False})

    try:
        # Get the service instance
        service_instance = get_service_instance(context)

        # Build call parameters
        call_params = {}
        call_params["filter"] = filter_params
        call_params["top"] = top
        call_params["user_email"] = user_email
        call_params["client_filter"] = client_filter_params
        call_params["exclude"] = exclude_params
        call_params["select"] = select_params

        # Call the service method
        return await service_instance.mail_list(**call_params)
    except Exception as e:
        await handle_token_error(e, user_email)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)