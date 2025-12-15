"""
FastAPI MCP Server for Outlook Graph Mail
Routes MCP protocol requests to existing Graph Mail functions
"""
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys
import os

# Add parent directories to path for module access
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
grandparent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, parent_dir)  # For outlook_mcp modules
sys.path.insert(0, grandparent_dir)  # For auth module

# Dynamic imports based on tool definitions
from graph_mail_query import GraphMailQuery
from graph_mail_client import GraphMailClient
from graph_types import ExcludeParams, FilterParams, SelectParams
from tool_definitions import MCP_TOOLS

app = FastAPI(title="Outlook MCP Server", version="1.0.0")

# Initialize service objects
graph_mail_query = GraphMailQuery()
graph_mail_client = GraphMailClient()


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
        elif tool_name == "mail_search":
            result = await handle_mail_search(arguments)
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


# Tool handler functions - routing to existing implementations

async def handle_query_emails(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailQuery.query_filter"""

    # Extract parameters from args
    user_email = args["user_email"]
    top = args.get("top", 10)
    orderby = args.get("orderby", "receivedDateTime desc")
    filter = args.get("filter", {})
    exclude = args.get("exclude", {})
    select = args.get("select", {})

    # Convert dicts to parameter objects where needed
    filter_params = None
    if filter:
        filter_params = FilterParams(**filter)
    exclude_params = None
    if exclude:
        exclude_params = ExcludeParams(**exclude)
    select_params = None
    if select:
        select_params = SelectParams(**select)

    return await graph_mail_query.query_filter(
        user_email=user_email,
        filter=filter_params,
        exclude=exclude_params,
        select=select_params,
        top=args.get("top", 10),
        orderby=args.get("orderby", "receivedDateTime desc")
    )

async def handle_mail_search(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailQuery.query_search"""

    # Extract parameters from args
    user_email = args["user_email"]
    search = args["search"]
    top = args.get("top", 250)
    orderby = args.get("orderby")
    client_filter = args.get("client_filter", {})
    select = args.get("select", {})

    # Convert dicts to parameter objects where needed
    client_filter_params = None
    if client_filter:
        client_filter_params = FilterParams(**client_filter)
    select_params = None
    if select:
        select_params = SelectParams(**select)

    return await graph_mail_query.query_search(
        user_email=user_email,
        search=search,
        client_filter=client_filter_params,
        select=select_params,
        top=args.get("top", 250),
        orderby=orderby
    )


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
    uvicorn.run(app, host="0.0.0.0", port=8000)