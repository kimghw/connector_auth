"""
FastAPI MCP Server for Outlook Graph Mail
Routes MCP protocol requests to existing Graph Mail functions
Generated from template using tool definitions
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

from graph_mail_query import GraphMailQuery
from graph_mail_client import GraphMailClient
from graph_types import FilterParams, ExcludeParams, SelectParams
from tool_definitions import MCP_TOOLS

app = FastAPI(title="Outlook MCP Server", version="1.0.0")

# Initialize query and client objects
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


# Tool handler functions - routing to existing implementations

async def handle_query_emails(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailQuery.query_filter"""
    
    user_email = args["user_email"]
    filter_dict = args.get("filter", {})
    exclude_dict = args.get("exclude", {})
    select_dict = args.get("select", {})

    # Convert dicts to parameter objects
    filter_params = FilterParams(**filter_dict) if filter_dict else FilterParams()
    exclude_params = ExcludeParams(**exclude_dict) if exclude_dict else None
    select_params = SelectParams(**select_dict) if select_dict else None

    return await graph_mail_query.query_filter(
        user_email=user_email,
        filter=filter_params,
        exclude=exclude_params,
        select=select_params,
        top=args.get("top", 10),
        orderby=args.get("orderby", "receivedDateTime desc")
    )
    


async def handle_get_email(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailClient.get_message"""
    
    return await graph_mail_client.get_message(
        user_email=args["user_email"],
        message_id=args["message_id"]
    )
    


async def handle_get_attachments(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailClient.get_attachments"""
    
    return await graph_mail_client.get_attachments(
        user_email=args["user_email"],
        message_id=args["message_id"]
    )
    


async def handle_download_attachment(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailClient.download_attachment"""
    
    return await graph_mail_client.download_attachment(
        user_email=args["user_email"],
        message_id=args["message_id"],
        attachment_id=args["attachment_id"],
        save_path=args.get("save_path")
    )
    


async def handle_search_by_date(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to search by date using query_filter"""
    
    filter_params = FilterParams(
        received_after=args["start_date"],
        received_before=args["end_date"]
    )

    select_params = None
    if args.get("select_fields"):
        fields = [f.strip() for f in args["select_fields"].split(",")]
        select_params = SelectParams(fields=fields)

    return await graph_mail_query.query_filter(
        user_email=args["user_email"],
        filter=filter_params,
        select=select_params,
        top=args.get("top", 10),
        orderby=args.get("orderby", "receivedDateTime desc")
    )
    


async def handle_send_email(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailClient.send_mail"""
    
    return await graph_mail_client.send_mail(
        user_email=args["user_email"],
        to_recipients=args["to_recipients"],
        subject=args["subject"],
        body=args["body"],
        cc_recipients=args.get("cc_recipients", []),
        bcc_recipients=args.get("bcc_recipients", []),
        importance=args.get("importance", "normal"),
        body_type=args.get("body_type", "text"),
        attachments=args.get("attachments", [])
    )
    


async def handle_reply_email(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailClient.reply_to_message"""
    
    if args.get("reply_all", False):
        return await graph_mail_client.reply_all(
            user_email=args["user_email"],
            message_id=args["message_id"],
            comment=args["comment"]
        )
    else:
        return await graph_mail_client.reply_to_message(
            user_email=args["user_email"],
            message_id=args["message_id"],
            comment=args["comment"]
        )
    


async def handle_forward_email(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailClient.forward_message"""
    
    return await graph_mail_client.forward_message(
        user_email=args["user_email"],
        message_id=args["message_id"],
        to_recipients=args["to_recipients"],
        comment=args.get("comment", "")
    )
    


async def handle_delete_email(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailClient.delete_message"""
    
    return await graph_mail_client.delete_message(
        user_email=args["user_email"],
        message_id=args["message_id"]
    )
    


async def handle_mark_read(args: Dict[str, Any]) -> Dict[str, Any]:
    """Route to GraphMailClient.mark_as_read"""
    
    return await graph_mail_client.mark_as_read(
        user_email=args["user_email"],
        message_id=args["message_id"],
        is_read=args.get("is_read", True)
    )
    



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