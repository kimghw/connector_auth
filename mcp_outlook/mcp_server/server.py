"""
FastAPI MCP Server for Outlook Graph Mail
Routes MCP protocol requests to existing Graph Mail functions
Now with SessionManager for safe multi-user support
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
sys.path.insert(0, parent_dir)  # For mcp_outlook modules
sys.path.insert(0, grandparent_dir)  # For auth module

from graph_types import FilterParams, ExcludeParams, SelectParams
from tool_definitions import MCP_TOOLS

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import SessionManager - optional feature
try:
    from session_manager import session_manager, Session
    USE_SESSION_MANAGER = True
    logger.info("SessionManager imported successfully")
except ImportError:
    logger.warning("SessionManager not found, using legacy mode without session management")
    session_manager = None
    Session = None
    USE_SESSION_MANAGER = False

# Import legacy components for fallback
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
        return {
            'graph_mail_query': graph_mail_query,
            'graph_mail_client': graph_mail_client,
            'user_email': user_email
        }


def get_query_instance(context):
    """Get GraphMailQuery instance from session or legacy context"""
    return context.graph_mail_query if USE_SESSION_MANAGER else context['graph_mail_query']


def get_client_instance(context):
    """Get GraphMailClient instance from session or legacy context"""
    return context.graph_mail_client if USE_SESSION_MANAGER else context['graph_mail_client']


async def handle_token_error(e: Exception, user_email: str):
    """Handle token-related errors"""
    if USE_SESSION_MANAGER and ("401" in str(e) or "unauthorized" in str(e).lower()):
        await session_manager.invalidate_session(user_email)
        raise HTTPException(status_code=401, detail="Access token expired")
    raise e


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
        if tool_name == "query_emails":
            result = await handle_query_emails(arguments)
        elif tool_name == "get_email":
            result = await handle_get_email(arguments)
        elif tool_name == "get_email_attachments":
            result = await handle_get_attachments(arguments)
        elif tool_name == "download_attachment":
            result = await handle_download_attachment(arguments)
        elif tool_name == "search_emails_by_date":
            result = await handle_search_by_date(arguments)
        elif tool_name == "send_email":
            result = await handle_send_email(arguments)
        elif tool_name == "reply_to_email":
            result = await handle_reply_email(arguments)
        elif tool_name == "forward_email":
            result = await handle_forward_email(arguments)
        elif tool_name == "delete_email":
            result = await handle_delete_email(arguments)
        elif tool_name == "mark_as_read":
            result = await handle_mark_read(arguments)
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
async def handle_query_emails(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailQuery.query_filter with session or legacy support"""
    user_email = args["user_email"]

    # Get session or legacy instances
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    filter_dict = args.get("filter", {})
    exclude_dict = args.get("exclude", {})
    select_dict = args.get("select", {})

    # Convert dicts to parameter objects
    filter_params = FilterParams(**filter_dict) if filter_dict else FilterParams()
    exclude_params = ExcludeParams(**exclude_dict) if exclude_dict else None
    select_params = SelectParams(**select_dict) if select_dict else None

    try:
        # Use helper to get the query instance
        query_instance = get_query_instance(context)

        return await query_instance.query_filter(
            user_email=user_email,
            filter=filter_params,
            exclude=exclude_params,
            select=select_params,
            top=args.get("top", 10),
            orderby=args.get("orderby", "receivedDateTime desc")
        )
    except Exception as e:
        await handle_token_error(e, user_email)


async def handle_get_email(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailClient.get_message with session or legacy support"""
    user_email = args["user_email"]
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        client_instance = get_client_instance(context)
        return await client_instance.get_message(
            user_email=user_email,
            message_id=args["message_id"]
        )
    except Exception as e:
        await handle_token_error(e, user_email)


async def handle_get_attachments(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailClient.get_attachments using session or legacy support"""
    user_email = args["user_email"]
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        client_instance = get_client_instance(context)
        return await client_instance.get_attachments(
            user_email=user_email,
            message_id=args["message_id"]
        )
    except Exception as e:
        await handle_token_error(e, user_email)


async def handle_download_attachment(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailClient.download_attachment using session or legacy support"""
    user_email = args["user_email"]
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        client_instance = get_client_instance(context)
        return await client_instance.download_attachment(
            user_email=user_email,
            message_id=args["message_id"],
            attachment_id=args["attachment_id"],
            save_path=args.get("save_path")
        )
    except Exception as e:
        await handle_token_error(e, user_email)


async def handle_search_by_date(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to search by date using query_filter with session or legacy support"""
    user_email = args["user_email"]
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    filter_params = FilterParams(
        received_after=args["start_date"],
        received_before=args["end_date"]
    )

    select_params = None
    if args.get("select_fields"):
        fields = [f.strip() for f in args["select_fields"].split(",")]
        select_params = SelectParams(fields=fields)

    try:
        query_instance = get_query_instance(context)
        return await query_instance.query_filter(
            user_email=user_email,
            filter=filter_params,
            select=select_params,
            top=args.get("top", 10),
            orderby=args.get("orderby", "receivedDateTime desc")
        )
    except Exception as e:
        await handle_token_error(e, user_email)


async def handle_send_email(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailClient.send_mail using session or legacy support"""
    user_email = args["user_email"]
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        client_instance = get_client_instance(context)
        return await client_instance.send_mail(
            user_email=user_email,
            to_recipients=args["to_recipients"],
            subject=args["subject"],
            body=args["body"],
            cc_recipients=args.get("cc_recipients", []),
            bcc_recipients=args.get("bcc_recipients", []),
            importance=args.get("importance", "normal"),
            body_type=args.get("body_type", "text"),
            attachments=args.get("attachments", [])
        )
    except Exception as e:
        await handle_token_error(e, user_email)


async def handle_reply_email(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailClient.reply_to_message using session or legacy support"""
    user_email = args["user_email"]
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        client_instance = get_client_instance(context)
        if args.get("reply_all", False):
            return await client_instance.reply_all(
                user_email=user_email,
                message_id=args["message_id"],
                comment=args["comment"]
            )
        else:
            return await client_instance.reply_to_message(
                user_email=user_email,
                message_id=args["message_id"],
                comment=args["comment"]
            )
    except Exception as e:
        await handle_token_error(e, user_email)


async def handle_forward_email(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailClient.forward_message using session or legacy support"""
    user_email = args["user_email"]
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        client_instance = get_client_instance(context)
        return await client_instance.forward_message(
            user_email=user_email,
            message_id=args["message_id"],
            to_recipients=args["to_recipients"],
            comment=args.get("comment", "")
        )
    except Exception as e:
        await handle_token_error(e, user_email)


async def handle_delete_email(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailClient.delete_message using session or legacy support"""
    user_email = args["user_email"]
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        client_instance = get_client_instance(context)
        return await client_instance.delete_message(
            user_email=user_email,
            message_id=args["message_id"]
        )
    except Exception as e:
        await handle_token_error(e, user_email)


async def handle_mark_read(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailClient.mark_as_read using session or legacy support"""
    user_email = args["user_email"]
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        client_instance = get_client_instance(context)
        return await client_instance.mark_as_read(
            user_email=user_email,
            message_id=args["message_id"],
            is_read=args.get("is_read", True)
        )
    except Exception as e:
        await handle_token_error(e, user_email)


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
