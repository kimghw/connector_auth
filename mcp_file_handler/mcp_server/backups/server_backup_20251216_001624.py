"""
FastAPI MCP Server for File Attachment Processing
Routes MCP protocol requests to file processing functions
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
import asyncio

# Add parent directories to path for module access
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
grandparent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, parent_dir)  # For mcp_attachment modules
sys.path.insert(0, grandparent_dir)  # For session module

from .tool_definitions import MCP_TOOLS

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
from ..file_manager import FileManager
from ..metadata.manager import MetadataManager

app = FastAPI(title="Attachment MCP Server", version="1.0.0")

# Global instances for legacy mode (when SessionManager not available)
if not USE_SESSION_MANAGER:
    file_manager = FileManager()
    metadata_manager = file_manager.metadata_manager


# ============= Session Management Helpers =============

async def ensure_file_manager_legacy(user_email: str = None):
    """
    Legacy mode: Ensure file manager is initialized
    In legacy mode, we use a single global instance
    """
    global file_manager
    if file_manager is None:
        file_manager = FileManager()
    logger.info(f"Using legacy file manager for user: {user_email or 'default'}")


async def get_user_session_or_legacy(user_email: str, access_token: Optional[str] = None):
    """
    Get session for user or fall back to legacy mode
    Returns either a Session object or a dict with legacy instances
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
        await ensure_file_manager_legacy(user_email)
        return {
            'file_manager': file_manager,
            'metadata_manager': file_manager.metadata_manager,
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


# ============= Request/Response Models =============

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


# ============= API Endpoints =============

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
    """Handle MCP tools/call request"""
    try:
        params = request.params
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        # Route to specific tool handler
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


# ============= Tool Handler Functions =============

async def handle_convert_file_to_text(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to FileManager.process for file conversion"""
    # Get user context (for future multi-user support)
    user_email = args.get("user_email", "default")

    # Get session or legacy instances
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        file_path = args.get("file_path")
        if not file_path:
            raise ValueError("file_path is required")

        # Get the file manager instance
        fm = get_file_manager_instance(context)

        # Process the file
        result = await asyncio.to_thread(
            fm.process,
            file_path,
            **args
        )

        if args.get("output_format") == "json":
            return result
        else:
            return {
                "success": result.get("success", False),
                "text": result.get("text", ""),
                "errors": result.get("errors", [])
            }

    except Exception as e:
        await handle_token_error(e, user_email)
        logger.error(f"File conversion error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def handle_convert_onedrive_to_text(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to FileManager.process for OneDrive URL processing"""
    user_email = args.get("user_email", "default")

    # Get session or legacy instances
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        url = args.get("url")
        if not url:
            raise ValueError("url is required")

        # Get the file manager instance
        fm = get_file_manager_instance(context)

        # Process the OneDrive URL
        result = await asyncio.to_thread(
            fm.process,
            url,
            **args
        )

        if args.get("output_format") == "json":
            return result
        else:
            return {
                "success": result.get("success", False),
                "text": result.get("text", ""),
                "errors": result.get("errors", [])
            }

    except Exception as e:
        await handle_token_error(e, user_email)
        logger.error(f"OneDrive conversion error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def handle_process_directory(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to FileManager.process_directory for batch processing"""
    user_email = args.get("user_email", "default")

    # Get session or legacy instances
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        directory_path = args.get("directory_path")
        if not directory_path:
            raise ValueError("directory_path is required")

        # Get the file manager instance
        fm = get_file_manager_instance(context)

        # Process the directory
        results = await asyncio.to_thread(
            fm.process_directory,
            directory_path,
            **args
        )

        # Create summary
        summary = {
            "total": len(results),
            "successful": sum(1 for r in results if r.get("success")),
            "failed": sum(1 for r in results if not r.get("success")),
            "results": results
        }

        if args.get("output_format") == "json":
            return summary
        else:
            text_parts = [
                f"Processed {summary['total']} files",
                f"Success: {summary['successful']}",
                f"Failed: {summary['failed']}"
            ]

            for result in results[:5]:  # Show first 5
                if result.get("success"):
                    text_parts.append(f"✓ {result.get('file', 'unknown')}")
                else:
                    text_parts.append(f"✗ {result.get('file', 'unknown')}: {result.get('errors', [])}")

            if len(results) > 5:
                text_parts.append(f"... and {len(results) - 5} more")

            return {
                "text": "\n".join(text_parts),
                "summary": summary
            }

    except Exception as e:
        await handle_token_error(e, user_email)
        logger.error(f"Directory processing error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def handle_save_file_metadata(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to MetadataManager.save for metadata storage"""
    user_email = args.get("user_email", "default")

    # Get session or legacy instances
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        file_url = args.get("file_url")
        keywords = args.get("keywords", [])

        if not file_url:
            raise ValueError("file_url is required")

        # Get the file manager instance
        fm = get_file_manager_instance(context)

        # Save metadata
        success = await asyncio.to_thread(
            fm.save_metadata,
            file_url,
            keywords,
            args.get("metadata")
        )

        return {
            "success": success,
            "message": "Metadata saved successfully" if success else "Failed to save metadata"
        }

    except Exception as e:
        await handle_token_error(e, user_email)
        logger.error(f"Save metadata error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def handle_search_metadata(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to MetadataManager.search for metadata queries"""
    user_email = args.get("user_email", "default")

    # Get session or legacy instances
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        # Get the file manager instance
        fm = get_file_manager_instance(context)

        # Search metadata
        results = await asyncio.to_thread(
            fm.search_metadata,
            **args
        )

        return {
            "success": True,
            "results": results,
            "count": len(results)
        }

    except Exception as e:
        await handle_token_error(e, user_email)
        logger.error(f"Search metadata error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def handle_get_file_metadata(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to MetadataManager.get for single file metadata"""
    user_email = args.get("user_email", "default")

    # Get session or legacy instances
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        file_url = args.get("file_url")
        if not file_url:
            raise ValueError("file_url is required")

        # Get the metadata manager instance
        mm = get_metadata_manager_instance(context)

        # Get metadata
        metadata = await asyncio.to_thread(
            mm.get,
            file_url
        )

        if metadata:
            return {
                "success": True,
                "metadata": metadata
            }
        else:
            return {
                "success": False,
                "message": "Metadata not found"
            }

    except Exception as e:
        await handle_token_error(e, user_email)
        logger.error(f"Get metadata error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def handle_delete_file_metadata(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to MetadataManager.delete for metadata removal"""
    user_email = args.get("user_email", "default")

    # Get session or legacy instances
    context = await get_user_session_or_legacy(user_email, args.get("access_token"))

    try:
        file_url = args.get("file_url")
        if not file_url:
            raise ValueError("file_url is required")

        # Get the metadata manager instance
        mm = get_metadata_manager_instance(context)

        # Delete metadata
        success = await asyncio.to_thread(
            mm.delete,
            file_url
        )

        return {
            "success": success,
            "message": "Metadata deleted successfully" if success else "Failed to delete metadata"
        }

    except Exception as e:
        await handle_token_error(e, user_email)
        logger.error(f"Delete metadata error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


# ============= Helper Functions =============

def create_error_response(request_id: Any, code: int, message: str) -> JSONResponse:
    """Create standard JSON-RPC error response"""
    return JSONResponse(
        content={
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        },
        status_code=200  # JSON-RPC always returns 200
    )


# ============= Health Check & Debug Endpoints =============

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "attachment-mcp-server",
        "version": "1.0.0",
        "session_manager": "enabled" if USE_SESSION_MANAGER else "disabled"
    }


@app.get("/tools")
async def list_tools():
    """List available tools (for debugging)"""
    return {
        "tools": [tool["name"] for tool in MCP_TOOLS],
        "count": len(MCP_TOOLS)
    }


if __name__ == "__main__":
    import uvicorn

    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,  # Different port from outlook server
        log_level="info"
    )