"""
FastAPI MCP Server for Outlook Graph Mail
Routes MCP protocol requests to existing Graph Mail functions
Now with SessionManager for safe multi-user support
"""
import json
from pathlib import Path
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
sys.path.insert(0, grandparent_dir)  # For session module and package imports (mcp_file_handler, mcp_outlook)
sys.path.insert(0, parent_dir)  # For direct module imports from parent directory
from outlook_types import ExcludeParams, FilterParams, SelectParams
from tool_definitions import MCP_TOOLS

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import SessionManager - optional feature
try:
    from session.session_manager import SessionManager
    session_manager = SessionManager()
    from session.session_manager import Session
    USE_SESSION_MANAGER = True
    logger.info("SessionManager imported successfully")
except ImportError:
    logger.warning("SessionManager not found, using legacy mode without session management")
    session_manager = None
    Session = None
    USE_SESSION_MANAGER = False

# Import legacy components for fallback
# Outlook services
from graph_mail_query import GraphMailQuery
from graph_mail_client import GraphMailClient

app = FastAPI(title="Outlook MCP Server", version="1.0.0")

# Global instances for legacy mode (when SessionManager not available)
if not USE_SESSION_MANAGER:
    graph_mail_query = GraphMailQuery()
    graph_mail_client = GraphMailClient()


@app.on_event("startup")
async def startup_event():
    """Start SessionManager on server startup (if available)"""
    if USE_SESSION_MANAGER:
        await session_manager.start()
        logger.info("SessionManager started")
    else:
        logger.info("Server started in legacy mode without SessionManager")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop SessionManager on server shutdown (if available)"""
    if USE_SESSION_MANAGER:
        await session_manager.stop()
        logger.info("SessionManager stopped")
    else:
        logger.info("Server shutdown in legacy mode")


async def ensure_graph_mail_client_legacy(user_email: Optional[str] = None):
    """
    Legacy method: Ensure GraphMailClient is initialized before use
    Used when SessionManager is not available
    """
    if user_email:
        graph_mail_client.user_email = user_email

    if not getattr(graph_mail_client, "_initialized", False):
        initialized = await graph_mail_client.initialize(user_email=user_email)
        if not initialized:
            raise HTTPException(status_code=500, detail="Failed to initialize GraphMailClient")


async def get_user_session_or_legacy(user_email: str, access_token: Optional[str] = None):
    """
    Get session if SessionManager available, otherwise return legacy instances

    Args:
        user_email: User's email address
        access_token: Optional access token for authentication

    Returns:
        Session object or dict with legacy instances

    Raises:
        HTTPException: If initialization fails
    """
    if USE_SESSION_MANAGER:
        # Use SessionManager
        try:
            session = await session_manager.get_or_create_session(user_email, access_token)
            if not session.initialized:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to initialize session for user: {user_email}"
                )
            return session
        except Exception as e:
            logger.error(f"Error getting session for {user_email}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # Legacy mode - return global instances wrapped in a dict
        await ensure_graph_mail_client_legacy(user_email)
        result = {
            'graph_mail_query': graph_mail_query,
            'graph_mail_client': graph_mail_client,
            'user_email': user_email
        }
        return result


def get_query_instance(context):
    """Get query service instance from session or legacy context"""
    return context.graph_mail_query if USE_SESSION_MANAGER else context['graph_mail_query']


def get_client_instance(context):
    """Get client service instance from session or legacy context"""
    return context.graph_mail_client if USE_SESSION_MANAGER else context['graph_mail_client']


async def handle_token_error(e: Exception, user_email: str):
    """Handle token-related errors"""
    if USE_SESSION_MANAGER and ("401" in str(e) or "unauthorized" in str(e).lower()):
        await session_manager.invalidate_session(user_email)
        raise HTTPException(status_code=401, detail="Access token expired")
    raise e


def extract_schema_defaults(arg_info: Dict[str, Any]) -> Dict[str, Any]:
    """Extract default values from internal arg schema metadata"""
    defaults = {}
    for prop_name, prop in arg_info.get("original_schema", {}).get("properties", {}).items():
        if "default" in prop:
            defaults[prop_name] = prop["default"]
    return defaults


def load_internal_args() -> Dict[str, Any]:
    """
    Load tool_internal_args.json (web editor output) and enrich empty values with schema defaults.
    Searches both the server directory and mcp_editor/outlook.
    """
    base_dir = Path(__file__).resolve().parent
    candidates = [
        base_dir / "tool_internal_args.json",
        base_dir.parent.parent / "mcp_editor" / "outlook" / "tool_internal_args.json",
    ]

    for path in candidates:
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as f:
                    raw_args = json.load(f)
                enriched = {}
                for tool_name, tool_args in raw_args.items():
                    enriched[tool_name] = {}
                    for arg_name, arg_info in tool_args.items():
                        arg_copy = dict(arg_info)
                        if arg_copy.get("value") == {}:
                            defaults = extract_schema_defaults(arg_copy)
                            if defaults:
                                arg_copy["value"] = defaults
                        enriched[tool_name][arg_name] = arg_copy
                logger.info(f"Loaded internal args from {path}")
                return enriched
            except Exception as exc:
                logger.warning(f"Failed to load internal args from {path}: {exc}")
    return {}


INTERNAL_ARGS = load_internal_args()

INTERNAL_ARG_TYPES = {
    "FilterParams": FilterParams,
    "ExcludeParams": ExcludeParams,
    "SelectParams": SelectParams,
}


def build_internal_param(tool_name: str, arg_name: str):
    """Instantiate internal parameter object for a tool based on internal args config"""
    arg_info = INTERNAL_ARGS.get(tool_name, {}).get(arg_name)
    if not arg_info:
        return None

    param_cls = INTERNAL_ARG_TYPES.get(arg_info.get("type"))
    if not param_cls:
        logger.warning(f"Unknown internal arg type for {tool_name}.{arg_name}: {arg_info.get('type')}")
        return None

    value = arg_info.get("value")
    if value is None:
        return None
    if value == {}:
        return param_cls()

    try:
        return param_cls(**value)
    except Exception as exc:
        logger.warning(f"Failed to build internal arg {tool_name}.{arg_name}: {exc}")
        return None


class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Any] = None
    method: str
    params: Optional[Dict[str, Any]] = {}


class MCPToolCall(BaseModel):
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
            "protocolVersion": "0.1.0",
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


# Tool handler functions - routing to session-specific implementations

async def handle_Outlook(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailClient.Outlook with session or legacy support"""
    user_email = args["user_email"]

    # Get session or legacy instances
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    # Extract parameters from args
    orderby = args.get("orderby")
    top = args.get("top")

    # Convert dicts to parameter objects where needed (Signature params from args)
    client_filter_raw = args.get("client_filter")
    client_filter_params = FilterParams(**client_filter_raw) if client_filter_raw is not None else None
    exclude_raw = args.get("exclude")
    exclude_params = ExcludeParams(**exclude_raw) if exclude_raw is not None else None
    filter_params = FilterParams(**args["filter"])
    select_raw = args.get("select")
    select_params = SelectParams(**select_raw) if select_raw is not None else None

    try:
        # Use helper to get the correct instance
        service_instance = get_client_instance(context)

        return await service_instance.Outlook(
            user_email=user_email,
            client_filter=client_filter_params,
            exclude=exclude_params,
            filter=filter_params,
            orderby=orderby,
            select=select_params,
            top=top
        )
    except Exception as e:
        await handle_token_error(e, user_email)

async def handle_keyword_search(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailQuery.keyword_search with session or legacy support"""
    user_email = args["user_email"]

    # Get session or legacy instances
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    # Extract parameters from args
    orderby = args.get("orderby")
    search = args["search"]
    top = args.get("top")

    # Convert dicts to parameter objects where needed (Signature params from args)
    client_filter_raw = args.get("client_filter")
    client_filter_params = FilterParams(**client_filter_raw) if client_filter_raw is not None else None
    select_raw = args.get("select")
    select_params = SelectParams(**select_raw) if select_raw is not None else None

    try:
        # Use helper to get the correct instance
        service_instance = get_client_instance(context)

        return await service_instance.keyword_search(
            user_email=user_email,
            client_filter=client_filter_params,
            orderby=orderby,
            search=search,
            select=select_params,
            top=top
        )
    except Exception as e:
        await handle_token_error(e, user_email)

async def handle_query_url(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailQuery.query_url with session or legacy support"""
    user_email = args["user_email"]

    # Get session or legacy instances
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    # Extract parameters from args
    top = args.get("top")
    url = args["url"]

    # Convert dicts to parameter objects where needed (Signature params from args)
    client_filter_raw = args.get("client_filter")
    client_filter_params = FilterParams(**client_filter_raw) if client_filter_raw is not None else None

    try:
        # Use helper to get the correct instance
        service_instance = get_query_instance(context)

        return await service_instance.query_url(
            user_email=user_email,
            client_filter=client_filter_params,
            top=top,
            url=url
        )
    except Exception as e:
        await handle_token_error(e, user_email)

async def handle_mail_list(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailQuery.query_filter with session or legacy support"""
    user_email = args["user_email"]

    # Get session or legacy instances
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    # Extract parameters from args
    top = args.get("top", 100)

    # Convert dicts to parameter objects where needed (Signature params from args)
    filter_params = FilterParams(**args["filter"])

    
    client_filter_params = build_internal_param("mail_list", "client_filter")
    exclude_params = build_internal_param("mail_list", "exclude")
    select_params = build_internal_param("mail_list", "select")

    try:
        # Use helper to get the correct instance
        service_instance = get_query_instance(context)

        return await service_instance.query_filter(
            user_email=user_email,
            client_filter=client_filter_params,
            exclude=exclude_params,
            filter=filter_params,
            select=select_params,
            top=top
        )
    except Exception as e:
        await handle_token_error(e, user_email)


def create_error_response(id: Any, code: int, message: str) -> JSONResponse:
    """Create MCP error response"""
    return JSONResponse(content={
        "jsonrpc": "2.0",
        "id": id,
        "error": {
            "code": code,
            "message": message
        }
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
