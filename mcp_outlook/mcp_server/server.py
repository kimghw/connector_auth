"""
FastAPI MCP Server for Outlook MCP Server
Routes MCP protocol requests to service functions
Generated from universal template with registry data
"""
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys
import os
import logging
import aiohttp

# Add parent directories to path for module access
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)

# Add paths for imports based on server type
sys.path.insert(0, grandparent_dir)  # For session module and package imports
sys.path.insert(0, parent_dir)  # For direct module imports

# Import parameter types if needed
from outlook_types import ExcludeParams, FilterParams, SelectParams

# Import tool definitions
try:
    from .tool_definitions import MCP_TOOLS
except ImportError:
    from tool_definitions import MCP_TOOLS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import service classes (unique)
from mail_service import MailService

# Create service instances
mail_service = MailService()


# ============================================================
# Internal Args Support
# ============================================================
def load_internal_args() -> dict:
    """Load internal args from tool_internal_args.json"""
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "mcp_editor", "mcp_outlook", "tool_internal_args.json"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tool_internal_args.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "tool_internal_args.json"),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    raw_args = json.load(f)
                logger.info(f"Loaded internal args from {path}")
                return raw_args
            except Exception as exc:
                logger.warning(f"Failed to load internal args from {path}: {exc}")
    return {}


INTERNAL_ARGS = load_internal_args()

# Build INTERNAL_ARG_TYPES dynamically based on imported types
INTERNAL_ARG_TYPES = {}
if 'ExcludeParams' in globals():
    INTERNAL_ARG_TYPES['ExcludeParams'] = ExcludeParams
if 'FilterParams' in globals():
    INTERNAL_ARG_TYPES['FilterParams'] = FilterParams
if 'SelectParams' in globals():
    INTERNAL_ARG_TYPES['SelectParams'] = SelectParams


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
    2. stored value: Value from tool_internal_args.json
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


def merge_param_data(internal_data: dict, runtime_data):
    if not runtime_data:
        return internal_data or None
    if internal_data:
        return {**internal_data, **runtime_data}
    return runtime_data


app = FastAPI(title="Outlook MCP Server", version="1.0.0")


@app.on_event("startup")
async def startup_event():
    """Initialize services on server startup"""
    if hasattr(mail_service, 'initialize'):
        await mail_service.initialize()
        logger.info("MailService initialized")
    logger.info("Outlook MCP Server started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown"""
    logger.info("Outlook MCP Server stopped")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Outlook MCP Server",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "server": "outlook"}


@app.post("/mcp/v1/initialize")
async def initialize(request: Request):
    """Initialize MCP session"""
    body = await request.json()
    return {
        "protocolVersion": "1.0",
        "serverInfo": {
            "name": "outlook-mcp-server",
            "version": "1.0.0"
        },
        "capabilities": {
            "tools": {}
        }
    }


@app.post("/mcp/v1/tools/list")
async def list_tools(request: Request):
    """List available MCP tools"""
    try:
        # Get tools metadata
        tools_list = []
        for tool in MCP_TOOLS:
            tools_list.append({
                "name": tool["name"],
                "description": tool.get("description", ""),
                "inputSchema": tool.get("inputSchema", {})
            })

        return JSONResponse(content={
            "result": {
                "tools": tools_list
            }
        })
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": {"message": str(e)}}
        )


@app.post("/mcp/v1/tools/call")
async def call_tool(request: Request):
    """Execute an MCP tool"""
    try:
        data = await request.json()
        tool_name = data.get("params", {}).get("name")
        arguments = data.get("params", {}).get("arguments", {})

        logger.info(f"Tool call: {tool_name} with args: {arguments}")

        # Map tool name to service implementation
        tool_implementations = {
            "mail_fetch_filter": {
                "service_class": "MailService",
                "method": "query_mail_list"
            },
            "mail_fetch_search": {
                "service_class": "MailService",
                "method": "query_mail_list"
            },
            "mail_process_with_download": {
                "service_class": "MailService",
                "method": "query_mail_list"
            },
            "mail_list": {
                "service_class": "MailService",
                "method": "query_mail_list"
            },
            "mail_query_url": {
                "service_class": "MailService",
                "method": "query_mail_list"
            },
        }

        if tool_name not in tool_implementations:
            return JSONResponse(
                status_code=404,
                content={"error": {"message": f"Unknown tool: {tool_name}"}}
            )

        implementation_info = tool_implementations[tool_name]

        # Get service instance by class name
        service_class = implementation_info["service_class"]
        service_instance = {
            "MailService": mail_service,
        }.get(service_class)

        if not service_instance:
            return JSONResponse(
                status_code=500,
                content={"error": {"message": f"Service not available: {service_class}"}}
            )

        # Get the method
        method = getattr(service_instance, implementation_info["method"], None)
        if not method:
            return JSONResponse(
                status_code=500,
                content={"error": {"message": f"Method not found: {implementation_info['method']}"}}
            )

        # Process arguments based on tool configuration
        # Handle parameter transformations
        processed_args = {}

        # Get tool configuration
        tool_config = next((t for t in MCP_TOOLS if t["name"] == tool_name), None)

        if tool_config:
            schema_props = tool_config.get("inputSchema", {}).get("properties", {})
            tool_internal_args = INTERNAL_ARGS.get(tool_name, {})

            # Process signature arguments
            for param_name, param_value in arguments.items():
                param_schema = schema_props.get(param_name, {})

                # Transform object parameters to their expected types
                if param_schema.get("type") == "object":
                    base_model = param_schema.get("baseModel")
                    target_param = param_schema.get("targetParam", param_name)  # Use targetParam if specified

                    # Create object instance based on baseModel
                    # Skip empty dicts - they should be treated as None for merging with internal args
                    if base_model and base_model in globals():
                        model_class = globals()[base_model]
                        if param_value:  # Only create object if param_value is not empty/None
                            processed_args[target_param] = model_class(**param_value)
                        # If empty, don't add to processed_args - let internal args take over
                    elif param_value:  # Only add non-empty values
                        processed_args[target_param] = param_value
                else:
                    # For non-object types, check if there's a targetParam mapping
                    target_param = param_schema.get("targetParam", param_name)
                    processed_args[target_param] = param_value

            # Process internal arguments
            for arg_name, arg_info in tool_internal_args.items():
                # Check if this internal arg has a targetParam
                target_param = arg_info.get("targetParam", arg_name)

                # Build internal parameter
                internal_value = build_internal_param(tool_name, arg_name)

                if internal_value is not None:
                    # Check if target_param already exists from signature args
                    if target_param in processed_args:
                        # Signature args have priority - merge internal into signature
                        sig_value = processed_args[target_param]

                        # If both are objects, merge them (signature priority)
                        if hasattr(sig_value, '__dict__') and hasattr(internal_value, '__dict__'):
                            # Convert to dict for merging (exclude None values)
                            sig_dict = {k: v for k, v in vars(sig_value).items() if v is not None}
                            internal_dict = {k: v for k, v in vars(internal_value).items() if v is not None}

                            # Merge with signature priority
                            merged_dict = {**internal_dict, **sig_dict}

                            # Recreate object with merged values
                            param_type = type(sig_value)
                            processed_args[target_param] = param_type(**merged_dict)
                        # Otherwise keep signature value (signature priority)
                    else:
                        # No signature arg, use internal arg
                        processed_args[target_param] = internal_value
        else:
            processed_args = arguments

        # Call the method
        result = await method(**processed_args)

        # Format response
        if isinstance(result, dict):
            response_content = result
        elif isinstance(result, list):
            response_content = {"items": result}
        elif isinstance(result, str):
            response_content = {"message": result}
        elif result is None:
            response_content = {"success": True}
        else:
            response_content = {"result": str(result)}

        return JSONResponse(content={
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(response_content, ensure_ascii=False, indent=2)
                    }
                ]
            }
        })

    except aiohttp.ClientResponseError as e:
        # HTTP-level errors from external API calls
        logger.error(f"API error executing tool {tool_name}: {e.status} {e.message}", exc_info=True)
        if e.status == 401:
            return JSONResponse(
                status_code=401,
                content={"error": {"code": "AUTH_EXPIRED", "message": "Access token expired or invalid. Re-authentication required."}}
            )
        elif e.status == 403:
            return JSONResponse(
                status_code=403,
                content={"error": {"code": "PERMISSION_DENIED", "message": "Insufficient permissions for this operation."}}
            )
        elif e.status == 404:
            return JSONResponse(
                status_code=404,
                content={"error": {"code": "NOT_FOUND", "message": f"Resource not found: {e.message}"}}
            )
        elif e.status == 429:
            return JSONResponse(
                status_code=429,
                content={"error": {"code": "RATE_LIMITED", "message": "API rate limit exceeded. Please retry later."}}
            )
        else:
            return JSONResponse(
                status_code=e.status,
                content={"error": {"code": "API_ERROR", "message": str(e)}}
            )
    except HTTPException as e:
        # FastAPI HTTP exceptions (pass through)
        logger.error(f"HTTP error executing tool {tool_name}: {e.status_code} {e.detail}", exc_info=True)
        return JSONResponse(
            status_code=e.status_code,
            content={"error": {"code": "HTTP_ERROR", "message": e.detail}}
        )
    except Exception as e:
        # Check for auth-related keywords in generic exceptions
        error_str = str(e).lower()
        if "401" in error_str or "unauthorized" in error_str or "token expired" in error_str:
            logger.error(f"Auth error executing tool {tool_name}: {e}", exc_info=True)
            return JSONResponse(
                status_code=401,
                content={"error": {"code": "AUTH_EXPIRED", "message": "Authentication failed. Re-authentication required."}}
            )
        elif "403" in error_str or "forbidden" in error_str or "permission" in error_str:
            logger.error(f"Permission error executing tool {tool_name}: {e}", exc_info=True)
            return JSONResponse(
                status_code=403,
                content={"error": {"code": "PERMISSION_DENIED", "message": "Permission denied."}}
            )

        # General internal error
        logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": str(e)}}
        )

# Tool handler functions

async def handle_mail_fetch_filter(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_fetch_filter tool call"""

    # Extract parameters from args
    exclude_params = args.get("exclude_params")
    filter_params = args.get("filter_params")
    # Internal overrides for object params
    exclude_params_internal_params = build_internal_param("mail_fetch_filter", "exclude_params_internal")
    exclude_params_internal_data = model_to_dict(exclude_params_internal_params)

    # Convert dicts to parameter objects where needed
    exclude_params_internal_data = exclude_params_internal_data
    exclude_params_raw = args.get("exclude_params")
    exclude_params_data = merge_param_data(exclude_params_internal_data, exclude_params_raw)
    exclude_params_params = ExcludeParams(**exclude_params_data) if exclude_params_data is not None else None
    filter_params_internal_data = {}
    filter_params_raw = args.get("filter_params")
    filter_params_data = merge_param_data(filter_params_internal_data, filter_params_raw)
    filter_params_params = FilterParams(**filter_params_data) if filter_params_data is not None else None
    # Prepare call arguments
    call_args = {}

    # Add signature parameters
    call_args["exclude_params"] = exclude_params_params
    call_args["filter_params"] = filter_params_params
    # Process internal args with targetParam mappings

    return await mail_service.query_mail_list(**call_args)

async def handle_mail_fetch_search(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_fetch_search tool call"""

    # Extract parameters from args
    search_term = args["search_term"]
    select_params = args.get("select_params")
    top = args.get("top")

    # Convert dicts to parameter objects where needed
    select_params_internal_data = {}
    select_params_raw = args.get("select_params")
    select_params_data = merge_param_data(select_params_internal_data, select_params_raw)
    select_params_params = SelectParams(**select_params_data) if select_params_data is not None else None
    # Prepare call arguments
    call_args = {}

    # Add signature parameters
    call_args["search_term"] = search_term
    call_args["select_params"] = select_params_params
    call_args["top"] = top

    return await mail_service.query_mail_list(**call_args)

async def handle_mail_process_with_download(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_process_with_download tool call"""

    # Extract parameters from args
    filter_params = args.get("filter_params")
    save_directory = args.get("save_directory")
    search_term = args.get("search_term")
    top = args.get("top")

    # Convert dicts to parameter objects where needed
    filter_params_internal_data = {}
    filter_params_raw = args.get("filter_params")
    filter_params_data = merge_param_data(filter_params_internal_data, filter_params_raw)
    filter_params_params = FilterParams(**filter_params_data) if filter_params_data is not None else None
    # Prepare call arguments
    call_args = {}

    # Add signature parameters
    call_args["filter_params"] = filter_params_params
    call_args["save_directory"] = save_directory
    call_args["search_term"] = search_term
    call_args["top"] = top

    return await mail_service.query_mail_list(**call_args)

async def handle_mail_list(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_list tool call"""

    # Extract parameters from args
    filter_params = args.get("filter_params")
    user_email = args.get("user_email")

    # Convert dicts to parameter objects where needed
    filter_params_internal_data = {}
    filter_params_raw = args.get("filter_params")
    filter_params_data = merge_param_data(filter_params_internal_data, filter_params_raw)
    filter_params_params = FilterParams(**filter_params_data) if filter_params_data is not None else None
    # Prepare call arguments
    call_args = {}

    # Add signature parameters
    call_args["filter_params"] = filter_params_params
    call_args["user_email"] = user_email
    # Process internal args with targetParam mappings

    # Build internal arg: client_filter
    _internal_client_filter = build_internal_param("mail_list", "client_filter")

    # Check if target param already exists from signature
    if "client_filter" in call_args:
        # Merge internal into signature (signature has priority, but skip None values)
        existing_value = call_args["client_filter"]
        if hasattr(existing_value, '__dict__') and hasattr(_internal_client_filter, '__dict__'):
            # Both are objects - merge them (exclude None values from existing)
            internal_dict = {k: v for k, v in vars(_internal_client_filter).items() if v is not None}
            existing_dict = {k: v for k, v in vars(existing_value).items() if v is not None}
            merged_dict = {**internal_dict, **existing_dict}
            call_args["client_filter"] = type(existing_value)(**merged_dict)
        # Otherwise keep existing signature value
    else:
        # No conflict, use internal value with targetParam mapping
        call_args["client_filter"] = _internal_client_filter

    return await mail_service.query_mail_list(**call_args)

async def handle_mail_query_url(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_query_url tool call"""

    # Extract parameters from args
    filter_params = args.get("filter_params")
    select = args.get("select")
    top = args.get("top")
    url = args["url"]
    user_email = args["user_email"]

    # Convert dicts to parameter objects where needed
    filter_params_internal_data = {}
    filter_params_raw = args.get("filter_params")
    filter_params_data = merge_param_data(filter_params_internal_data, filter_params_raw)
    filter_params_params = FilterParams(**filter_params_data) if filter_params_data is not None else None
    select_internal_data = {}
    select_raw = args.get("select")
    select_data = merge_param_data(select_internal_data, select_raw)
    select_params = SelectParams(**select_data) if select_data is not None else None
    # Prepare call arguments
    call_args = {}

    # Add signature parameters
    call_args["filter_params"] = filter_params_params
    call_args["select"] = select_params
    call_args["top"] = top
    call_args["url"] = url
    call_args["user_email"] = user_email

    return await mail_service.query_mail_list(**call_args)


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