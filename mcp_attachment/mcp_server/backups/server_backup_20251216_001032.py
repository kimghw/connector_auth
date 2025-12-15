"""
FastAPI MCP Server for File Attachment Management
Routes MCP protocol requests to file and metadata management functions
With SessionManager for safe multi-user support
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
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
attachment_dir = os.path.join(grandparent_dir, "mcp_attachment")

# Important: Add attachment directory first for proper relative imports
sys.path.insert(0, attachment_dir)
sys.path.insert(0, grandparent_dir)  # For session module
sys.path.insert(0, parent_dir)  # For direct module imports

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

# Import attachment services
from file_manager import FileManager
from metadata.manager import MetadataManager

app = FastAPI(title="Attachment MCP Server", version="1.0.0")

# Global instances for legacy mode (when SessionManager not available)
if not USE_SESSION_MANAGER:
    file_manager = FileManager()
    metadata_manager = file_manager.metadata_manager


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
                # Initialize file manager for this session
                session.file_manager = FileManager()
                session.metadata_manager = session.file_manager.metadata_manager
                session.initialized = True
                logger.info(f"Initialized file manager for session: {user_email}")
            return session
        except Exception as e:
            logger.error(f"Error getting session for {user_email}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # Legacy mode - return global instances wrapped in a dict
        return {
            'file_manager': file_manager,
            'metadata_manager': metadata_manager,
            'user_email': user_email
        }


def get_file_manager_instance(context):
    """Get FileManager instance from session or legacy context"""
    return context.file_manager if USE_SESSION_MANAGER else context['file_manager']


def get_metadata_manager_instance(context):
    """Get MetadataManager instance from session or legacy context"""
    return context.metadata_manager if USE_SESSION_MANAGER else context['metadata_manager']


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
                "name": "attachment-mcp-server",
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
if tool_name == "convert_file_to_text":
            result = await handle_convert_file_to_text(arguments)
elif tool_name == "convert_onedrive_to_text":
            result = await handle_convert_onedrive_to_text(arguments)
elif tool_name == "process_directory":
            result = await handle_process_directory(arguments)
elif tool_name == "save_file_metadata":
            result = await handle_save_file_metadata(arguments)
elif tool_name == "search_metadata":
            result = await handle_search_metadata(arguments)
elif tool_name == "get_file_metadata":
            result = await handle_get_file_metadata(arguments)
elif tool_name == "delete_file_metadata":
            result = await handle_delete_file_metadata(arguments)
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

async def handle_convert_file_to_text(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to FileManager.convert_file_to_text with session or legacy support"""
    user_email = args.get("user_email", "default")

    # Get session or legacy instances
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        # Get the appropriate service instance        service_instance = get_file_manager_instance(context)
        # Call the service method
        return await service_instance.convert_file_to_text(            file_path=args.get("file_path"),            output_format=args.get("output_format"),            use_ocr=args.get("use_ocr"),            save_metadata=args.get("save_metadata"),            keywords=args.get("keywords")        )
    except Exception as e:
        await handle_token_error(e, user_email)

async def handle_convert_onedrive_to_text(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to FileManager.convert_onedrive_to_text with session or legacy support"""
    user_email = args.get("user_email", "default")

    # Get session or legacy instances
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        # Get the appropriate service instance        service_instance = get_file_manager_instance(context)
        # Call the service method
        return await service_instance.convert_onedrive_to_text(            url=args.get("url"),            recursive=args.get("recursive"),            output_format=args.get("output_format"),            save_metadata=args.get("save_metadata"),            keywords=args.get("keywords")        )
    except Exception as e:
        await handle_token_error(e, user_email)

async def handle_process_directory(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to FileManager.process_directory with session or legacy support"""
    user_email = args.get("user_email", "default")

    # Get session or legacy instances
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        # Get the appropriate service instance        service_instance = get_file_manager_instance(context)
        # Call the service method
        return await service_instance.process_directory(            directory_path=args.get("directory_path"),            pattern=args.get("pattern"),            recursive=args.get("recursive"),            output_format=args.get("output_format"),            save_metadata=args.get("save_metadata")        )
    except Exception as e:
        await handle_token_error(e, user_email)

async def handle_save_file_metadata(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to MetadataManager.save_file_metadata with session or legacy support"""
    user_email = args.get("user_email", "default")

    # Get session or legacy instances
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        # Get the appropriate service instance        service_instance = get_metadata_manager_instance(context)
        # Call the service method
        return await service_instance.save_file_metadata(            file_url=args.get("file_url"),            keywords=args.get("keywords"),            metadata=args.get("metadata")        )
    except Exception as e:
        await handle_token_error(e, user_email)

async def handle_search_metadata(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to MetadataManager.search_metadata with session or legacy support"""
    user_email = args.get("user_email", "default")

    # Get session or legacy instances
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        # Get the appropriate service instance        service_instance = get_metadata_manager_instance(context)
        # Call the service method
        return await service_instance.search_metadata(            keyword=args.get("keyword"),            file_url=args.get("file_url")        )
    except Exception as e:
        await handle_token_error(e, user_email)

async def handle_get_file_metadata(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to MetadataManager.get_file_metadata with session or legacy support"""
    user_email = args.get("user_email", "default")

    # Get session or legacy instances
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        # Get the appropriate service instance        service_instance = get_metadata_manager_instance(context)
        # Call the service method
        return await service_instance.get_file_metadata(            file_url=args.get("file_url")        )
    except Exception as e:
        await handle_token_error(e, user_email)

async def handle_delete_file_metadata(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to MetadataManager.delete_file_metadata with session or legacy support"""
    user_email = args.get("user_email", "default")

    # Get session or legacy instances
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        # Get the appropriate service instance        service_instance = get_metadata_manager_instance(context)
        # Call the service method
        return await service_instance.delete_file_metadata(            file_url=args.get("file_url")        )
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


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "server": "attachment-mcp-server"}


@app.get("/tools")
async def list_tools():
    """List available tools"""
    return {"tools": [tool["name"] for tool in MCP_TOOLS]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)