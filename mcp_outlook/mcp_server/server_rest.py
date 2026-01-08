"""
FastAPI MCP Server for Outlook MCP Server
Routes MCP protocol requests to service functions
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

# Add parent directories to path for module access
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)

# Add paths for imports based on server type
sys.path.insert(0, grandparent_dir)  # For session module and package imports
sys.path.insert(0, parent_dir)  # For direct module imports

# Import types dynamically based on type_info
from mcp_outlook.outlook_types import ExcludeParams, FilterParams, SelectParams
from mcp_outlook.graph_mail_client import ProcessingMode, QueryMethod

# Load tool definitions from YAML (Single Source of Truth)
def _load_mcp_tools() -> List[Dict[str, Any]]:
    """Load MCP tools from tool_definition_templates.yaml."""
    yaml_path = Path(current_dir).parent.parent / "mcp_editor" / "mcp_outlook" / "tool_definition_templates.yaml"
    if yaml_path.exists():
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("tools", [])
    raise FileNotFoundError(f"Tool definition YAML not found: {yaml_path}")

MCP_TOOLS = _load_mcp_tools()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import service classes (unique)
from mcp_outlook.outlook_service import MailService

# Create service instances
mail_service = MailService()

# ============================================================
# Common MCP protocol utilities (shared across protocols)
# ============================================================

SUPPORTED_PROTOCOLS = {"rest", "stdio", "stream"}

# Pre-computed tool -> implementation mapping
TOOL_IMPLEMENTATIONS = {
    "mail_list_period": {
        "service_class": "MailService",
        "method": "query_mail_list"
    },
    "mail_list_keyword": {
        "service_class": "MailService",
        "method": "fetch_search"
    },
    "mail_query_if_emaidID": {
        "service_class": "MailService",
        "method": "batch_and_fetch"
    },
    "mail_attachment_meta": {
        "service_class": "MailService",
        "method": "fetch_attachments_metadata"
    },
    "mail_attachment_download": {
        "service_class": "MailService",
        "method": "download_attachments"
    },
    "mail_fetch_filter": {
        "service_class": "MailService",
        "method": "fetch_filter"
    },
    "mail_fetch_search": {
        "service_class": "MailService",
        "method": "fetch_search"
    },
    "mail_process_with_download": {
        "service_class": "MailService",
        "method": "process_with_download"
    },
    "mail_query_url": {
        "service_class": "MailService",
        "method": "fetch_url"
    },
}

# Pre-computed service class -> instance mapping
SERVICE_INSTANCES = {
    "MailService": mail_service,
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

async def handle_mail_list_period(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_list_period tool call"""

    # Extract parameters from args
    # Extract from input with source param name
    user_email = args["user_email"]
    DatePeriodFilter_raw = args.get("DatePeriodFilter")
    DatePeriodFilter = DatePeriodFilter_raw if DatePeriodFilter_raw is not None else None
    client_filter_keyword_raw = args.get("client_filter_keyword")
    client_filter_keyword = client_filter_keyword_raw if client_filter_keyword_raw is not None else None

    # Convert dicts to parameter objects where needed
    # Pre-computed defaults by targetParam: filter_params
    DatePeriodFilter_internal_defaults = {}
    DatePeriodFilter_sig_defaults = {}
    # Merge: Internal < Signature Defaults < Signature (user input)
    DatePeriodFilter_data = merge_param_data(DatePeriodFilter_internal_defaults, DatePeriodFilter, DatePeriodFilter_sig_defaults)
    if DatePeriodFilter_data is not None:
        DatePeriodFilter = FilterParams(**DatePeriodFilter_data)
    else:
        DatePeriodFilter = None
    # Pre-computed defaults by targetParam: client_filter
    client_filter_keyword_internal_defaults = {'exclude_from_address': 'block@krs.co.kr'}
    client_filter_keyword_sig_defaults = {}
    # Merge: Internal < Signature Defaults < Signature (user input)
    client_filter_keyword_data = merge_param_data(client_filter_keyword_internal_defaults, client_filter_keyword, client_filter_keyword_sig_defaults)
    if client_filter_keyword_data is not None:
        client_filter_keyword = ExcludeParams(**client_filter_keyword_data)
    else:
        client_filter_keyword = None
    # Prepare call arguments
    call_args = {}

    # Add signature parameters
    call_args["user_email"] = user_email
    call_args["filter_params"] = DatePeriodFilter
    call_args["client_filter"] = client_filter_keyword
    # Add internal args ONLY if not already handled by Signature with same targetParam
    
    
    call_args["select_params"] = SelectParams(**{'body_preview': True,
 'has_attachments': True,
 'id': True,
 'internet_message_id': True,
 'received_date_time': True,
 'sender': True,
 'subject': True})

    return await mail_service.query_mail_list(**call_args)

async def handle_mail_list_keyword(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_list_keyword tool call"""

    # Extract parameters from args
    # Extract from input with source param name
    user_email = args["user_email"]
    # Extract from input with source param name
    search_keywords = args["search_keywords"]
    top_raw = args.get("top")
    top = top_raw if top_raw is not None else 50

    return await mail_service.fetch_search(
        user_email=user_email,
        search_term=search_keywords,
        top=top
    )

async def handle_mail_query_if_emaidID(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_query_if_emaidID tool call"""

    # Extract parameters from args
    # Extract from input with source param name
    user_email = args["user_email"]
    # Extract from input with source param name
    message_ids = args["message_ids"]

    return await mail_service.batch_and_fetch(
        user_email=user_email,
        message_ids=message_ids
    )

async def handle_mail_attachment_meta(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_attachment_meta tool call"""

    # Extract parameters from args
    # Extract from input with source param name
    user_email = args["user_email"]
    # Extract from input with source param name
    message_ids = args["message_ids"]

    return await mail_service.fetch_attachments_metadata(
        user_email=user_email,
        message_ids=message_ids
    )

async def handle_mail_attachment_download(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_attachment_download tool call"""

    # Extract parameters from args
    # Extract from input with source param name
    user_email = args["user_email"]
    # Extract from input with source param name
    message_attachment_ids = args["message_attachment_ids"]
    save_directory_raw = args.get("save_directory")
    save_directory = save_directory_raw if save_directory_raw is not None else 'downloads'
    skip_duplicates_raw = args.get("skip_duplicates")
    skip_duplicates = skip_duplicates_raw if skip_duplicates_raw is not None else True

    return await mail_service.download_attachments(
        user_email=user_email,
        message_attachment_ids=message_attachment_ids,
        save_directory=save_directory,
        skip_duplicates=skip_duplicates
    )

async def handle_mail_fetch_filter(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_fetch_filter tool call"""

    # Extract parameters from args
    # Extract from input with source param name
    user_email = args["user_email"]
    filter_params_raw = args.get("filter_params")
    filter_params = filter_params_raw if filter_params_raw is not None else None
    exclude_params_raw = args.get("exclude_params")
    exclude_params = exclude_params_raw if exclude_params_raw is not None else None

    # Convert dicts to parameter objects where needed
    # Pre-computed defaults by targetParam: filter_params
    filter_params_internal_defaults = {}
    filter_params_sig_defaults = {'test_field': 'test_value'}
    # Merge: Internal < Signature Defaults < Signature (user input)
    filter_params_data = merge_param_data(filter_params_internal_defaults, filter_params, filter_params_sig_defaults)
    if filter_params_data is not None:
        filter_params = FilterParams(**filter_params_data)
    else:
        filter_params = None
    # Pre-computed defaults by targetParam: exclude_params
    exclude_params_internal_defaults = {}
    exclude_params_sig_defaults = {}
    # Merge: Internal < Signature Defaults < Signature (user input)
    exclude_params_data = merge_param_data(exclude_params_internal_defaults, exclude_params, exclude_params_sig_defaults)
    if exclude_params_data is not None:
        exclude_params = ExcludeParams(**exclude_params_data)
    else:
        exclude_params = None
    # Prepare call arguments
    call_args = {}

    # Add signature parameters
    call_args["user_email"] = user_email
    call_args["filter_params"] = filter_params
    call_args["exclude_params"] = exclude_params

    return await mail_service.fetch_filter(**call_args)

async def handle_mail_fetch_search(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_fetch_search tool call"""

    # Extract parameters from args
    # Extract from input with source param name
    user_email = args["user_email"]
    # Extract from input with source param name
    search_term = args["search_term"]
    select_params_raw = args.get("select_params")
    select_params = select_params_raw if select_params_raw is not None else None
    top_raw = args.get("top")
    top = top_raw if top_raw is not None else 50

    # Convert dicts to parameter objects where needed
    # Pre-computed defaults by targetParam: select_params
    select_params_internal_defaults = {}
    select_params_sig_defaults = {}
    # Merge: Internal < Signature Defaults < Signature (user input)
    select_params_data = merge_param_data(select_params_internal_defaults, select_params, select_params_sig_defaults)
    if select_params_data is not None:
        select_params = SelectParams(**select_params_data)
    else:
        select_params = None
    # Prepare call arguments
    call_args = {}

    # Add signature parameters
    call_args["user_email"] = user_email
    call_args["search_term"] = search_term
    call_args["select_params"] = select_params
    call_args["top"] = top

    return await mail_service.fetch_search(**call_args)

async def handle_mail_process_with_download(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_process_with_download tool call"""

    # Extract parameters from args
    # Extract from input with source param name
    user_email = args["user_email"]
    filter_params_raw = args.get("filter_params")
    filter_params = filter_params_raw if filter_params_raw is not None else None
    search_term_raw = args.get("search_term")
    search_term = search_term_raw if search_term_raw is not None else None
    top_raw = args.get("top")
    top = top_raw if top_raw is not None else 50
    save_directory_raw = args.get("save_directory")
    save_directory = save_directory_raw if save_directory_raw is not None else None

    # Convert dicts to parameter objects where needed
    # Pre-computed defaults by targetParam: filter_params
    filter_params_internal_defaults = {}
    filter_params_sig_defaults = {}
    # Merge: Internal < Signature Defaults < Signature (user input)
    filter_params_data = merge_param_data(filter_params_internal_defaults, filter_params, filter_params_sig_defaults)
    if filter_params_data is not None:
        filter_params = FilterParams(**filter_params_data)
    else:
        filter_params = None
    # Prepare call arguments
    call_args = {}

    # Add signature parameters
    call_args["user_email"] = user_email
    call_args["filter_params"] = filter_params
    call_args["search_term"] = search_term
    call_args["top"] = top
    call_args["save_directory"] = save_directory

    return await mail_service.process_with_download(**call_args)

async def handle_mail_query_url(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mail_query_url tool call"""

    # Extract parameters from args
    # Extract from input with source param name
    user_email = args["user_email"]
    # Extract from input with source param name
    url = args["url"]
    filter_params_raw = args.get("filter_params")
    filter_params = filter_params_raw if filter_params_raw is not None else None
    top_raw = args.get("top")
    top = top_raw if top_raw is not None else 50

    # Convert dicts to parameter objects where needed
    # Pre-computed defaults by targetParam: filter_params
    filter_params_internal_defaults = {}
    filter_params_sig_defaults = {}
    # Merge: Internal < Signature Defaults < Signature (user input)
    filter_params_data = merge_param_data(filter_params_internal_defaults, filter_params, filter_params_sig_defaults)
    if filter_params_data is not None:
        filter_params = FilterParams(**filter_params_data)
    else:
        filter_params = None
    # Prepare call arguments
    call_args = {}

    # Add signature parameters
    call_args["user_email"] = user_email
    call_args["url"] = url
    call_args["filter_params"] = filter_params
    call_args["top"] = top
    # Add internal args ONLY if not already handled by Signature with same targetParam
    
    call_args["select"] = SelectParams(**{'body_preview': True,
 'created_date_time': True,
 'from_recipient': True,
 'id': True,
 'received_date_time': True})

    return await mail_service.fetch_url(**call_args)
# ============================================================
# REST API Protocol Handlers for MCP
# ============================================================
# Note: This template is included by universal_server_template.jinja2
# All common imports and utilities are defined in the parent template

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


@app.post("/")
async def mcp_request_root(request: Request):
    """MCP Streamable HTTP - Root endpoint (alias for /mcp/v1)"""
    return await mcp_request(request)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "server": "outlook"}


@app.post("/mcp/v1")
async def mcp_request(request: Request):
    """MCP Streamable HTTP 단일 엔드포인트 - JSON-RPC 2.0"""
    try:
        data = await request.json()
        method = data.get('method', '')
        request_id = data.get('id')
        params = data.get('params', {})

        logger.info(f"MCP Request: method={method}, id={request_id}")

        if method == 'initialize':
            return await _handle_initialize(data)
        elif method == 'tools/list':
            return await _handle_tools_list(data)
        elif method == 'tools/call':
            return await _handle_tools_call(data)
        elif method == 'notifications/initialized':
            return JSONResponse(status_code=204, content=None)
        elif method == 'ping':
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {}
            })
        else:
            # MCP 프로토콜: 에러도 HTTP 200으로 응답
            return JSONResponse(
                content={"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}
            )
    except Exception as e:
        logger.error(f"Error in MCP request: {e}", exc_info=True)
        return JSONResponse(
            content={"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}
        )


async def _handle_initialize(data: dict):
    """내부 initialize 처리"""
    request_id = data.get('id')
    params = data.get('params', {})
    client_info = params.get('clientInfo', {})
    logger.info(f"Client connected: {client_info.get('name', 'unknown')}")

    return JSONResponse(content={
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "outlook",
                "version": "1.0.0"
            }
        }
    })


async def _handle_tools_list(data: dict):
    """내부 tools/list 처리"""
    request_id = data.get('id')

    tools_list = []
    for tool in MCP_TOOLS:
        tools_list.append({
            "name": tool["name"],
            "description": tool.get("description", ""),
            "inputSchema": tool.get("inputSchema", {})
        })

    return JSONResponse(content={
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "tools": tools_list
        }
    })


async def _handle_tools_call(data: dict):
    """내부 tools/call 처리"""
    request_id = data.get('id')
    params = data.get('params', {})
    tool_name = params.get('name')
    arguments = params.get('arguments', {})

    if not tool_name:
        return JSONResponse(
            content={"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": "Tool name is required"}}
        )

    arguments = apply_schema_defaults(tool_name, arguments)

    handler_name = f"handle_{tool_name.replace('-', '_')}"
    handler = globals().get(handler_name)
    if not handler:
        return JSONResponse(
            content={"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"}}
        )

    try:
        result = await handler(arguments)

        if isinstance(result, dict) and "content" in result:
            content = result["content"]
        elif isinstance(result, str):
            content = [{"type": "text", "text": result}]
        else:
            content = [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]

        return JSONResponse(content={
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": content
            }
        })
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
        # MCP 프로토콜: 에러도 HTTP 200으로 응답, JSON-RPC error로 전달
        return JSONResponse(
            content={"jsonrpc": "2.0", "id": request_id, "error": {"code": -32603, "message": str(e)}}
        )


@app.post("/mcp/v1/initialize")
async def initialize(request: Request):
    """Initialize MCP session - JSON-RPC 2.0"""
    data = await request.json()
    return await _handle_initialize(data)


@app.post("/mcp/v1/tools/list")
async def list_tools(request: Request):
    """List available MCP tools - JSON-RPC 2.0"""
    data = await request.json()
    return await _handle_tools_list(data)


def apply_schema_defaults(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
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


@app.post("/mcp/v1/tools/call")
async def call_tool(request: Request):
    """Execute an MCP tool - JSON-RPC 2.0"""
    data = await request.json()
    return await _handle_tools_call(data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)