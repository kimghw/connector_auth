"""
Web interface for editing MCP Tool Definitions
"""
import json
import os
import sys
import pprint
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import importlib.util
from datetime import datetime
import shutil
import copy

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import pydantic schema converter
from pydantic_to_schema import (
    generate_mcp_schemas_from_graph_types,
    update_tool_with_basemodel_schema,
    load_graph_types_models
)

# Import server name mappings
from tool_editor_web_server_mappings import (
    get_server_name_from_profile,
    get_server_name_from_path
)

# Import MCP service scanner (shared)
from mcp_service_scanner import get_services_map

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
CONFIG_PATH = os.path.join(BASE_DIR, 'editor_config.json')
DEFAULT_PROFILE = {
    "template_definitions_path": "tool_definition_templates.py",
    "tool_definitions_path": "../outlook_mcp/mcp_server/tool_definitions.py",
    "backup_dir": "backups",
    "types_files": ["../outlook_mcp/outlook_types.py"],
    "host": "127.0.0.1",
    "port": 8091
}

JINJA_DIR = os.path.join(ROOT_DIR, 'jinja')
SERVER_TEMPLATES = {
    "outlook": os.path.join(JINJA_DIR, "outlook_server_template.jinja2"),
    "mcp_file_handler": os.path.join(JINJA_DIR, "file_handler_server_template.jinja2"),
    "scaffold": os.path.join(JINJA_DIR, "mcp_server_scaffold_template.jinja2"),
}
DEFAULT_SERVER_TEMPLATE = SERVER_TEMPLATES["outlook"]
GENERATOR_SCRIPT_PATH = os.path.join(JINJA_DIR, 'generate_server.py')
EDITOR_CONFIG_TEMPLATE = os.path.join(JINJA_DIR, 'editor_config_template.jinja2')
EDITOR_CONFIG_GENERATOR = os.path.join(JINJA_DIR, 'generate_editor_config.py')


def _resolve_path(path: str) -> str:
    """Resolve relative paths against the editor directory"""
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(BASE_DIR, path))


def _get_config_path() -> str:
    """Allow overriding config path via MCP_EDITOR_CONFIG env"""
    env_path = os.environ.get("MCP_EDITOR_CONFIG")
    if env_path:
        return _resolve_path(env_path)
    return CONFIG_PATH


def _get_template_for_server(server_name: str | None) -> str:
    """Return the best template path for a given server name."""
    if server_name and server_name in SERVER_TEMPLATES:
        candidate = SERVER_TEMPLATES[server_name]
        if os.path.exists(candidate):
            return candidate

    for candidate in SERVER_TEMPLATES.values():
        if os.path.exists(candidate):
            return candidate

    return ""


def _guess_server_name(profile_conf: dict | None, profile_name: str | None = None) -> str | None:
    """Attempt to infer the server name from profile info or config keys."""
    if profile_name:
        guessed = get_server_name_from_profile(profile_name)
        if guessed:
            return guessed

    profile_conf = profile_conf or {}
    for key in ("template_definitions_path", "tool_definitions_path"):
        value = profile_conf.get(key)
        if isinstance(value, str):
            guessed = get_server_name_from_path(value)
            if guessed:
                return guessed

    return None


def _generate_config_from_template(config_path: str) -> dict | None:
    """
    Try to render editor_config.json using the Jinja template and generator utility.
    Falls back silently if the template or generator script is missing.
    """
    if not (os.path.exists(EDITOR_CONFIG_TEMPLATE) and os.path.exists(EDITOR_CONFIG_GENERATOR)):
        return None

    try:
        spec = importlib.util.spec_from_file_location("editor_config_generator", EDITOR_CONFIG_GENERATOR)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        server_names = module.scan_codebase_for_servers(ROOT_DIR)
        if not server_names:
            fallback = _guess_server_name(None, "_default") or "outlook"
            server_names = {fallback}

        module.generate_editor_config(server_names, ROOT_DIR, config_path, EDITOR_CONFIG_TEMPLATE)
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:  # pragma: no cover - best effort
        print(f"Warning: Could not generate editor_config.json from template: {e}")
    return None


def _load_config_file():
    config_path = _get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load editor_config.json: {e}")
        generated = _generate_config_from_template(config_path)
        if generated:
            return generated
    else:
        generated = _generate_config_from_template(config_path)
        if generated:
            return generated
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({"_default": DEFAULT_PROFILE}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not write default editor_config.json: {e}")
    return {"_default": DEFAULT_PROFILE}


def _merge_profile(default_profile: dict, override_profile: dict) -> dict:
    merged = DEFAULT_PROFILE.copy()
    merged.update(default_profile or {})
    if override_profile:
        for k, v in override_profile.items():
            if k in merged and isinstance(v, (str, list, int)):
                merged[k] = v
    return merged


def list_profile_names() -> list:
    data = _load_config_file()
    if isinstance(data, dict):
        # legacy single-profile dict (values not dict) -> single pseudo profile
        if all(not isinstance(v, dict) for v in data.values()):
            return ["_default"]
        return list(data.keys())
    return []


def get_profile_config(profile_name: str | None = None) -> dict:
    data = _load_config_file()
    # legacy single-profile dict
    if isinstance(data, dict) and all(not isinstance(v, dict) for v in data.values()):
        return _merge_profile({}, data)

    if isinstance(data, dict) and data:
        # If no profile specified, use first available profile
        if not profile_name:
            first_profile_name = next(iter(data.keys()))
            return _merge_profile({}, data[first_profile_name])
        # Use specified profile if exists
        if profile_name in data:
            return _merge_profile({}, data[profile_name])

    return DEFAULT_PROFILE.copy()


def resolve_paths(profile_conf: dict) -> dict:
    # internal_args_path는 선택적 - 없으면 template_path 기반으로 자동 생성
    internal_args_path = profile_conf.get("internal_args_path")
    if internal_args_path:
        internal_args_path = _resolve_path(internal_args_path)
    else:
        # 기본값: template_path와 같은 디렉토리의 tool_internal_args.json
        template_dir = os.path.dirname(_resolve_path(profile_conf["template_definitions_path"]))
        internal_args_path = os.path.join(template_dir, "tool_internal_args.json")

    return {
        "template_path": _resolve_path(profile_conf["template_definitions_path"]),
        "tool_path": _resolve_path(profile_conf["tool_definitions_path"]),
        "internal_args_path": internal_args_path,
        "backup_dir": _resolve_path(profile_conf["backup_dir"]),
        "types_files": profile_conf.get("types_files", profile_conf.get("graph_types_files", ["../outlook_mcp/outlook_types.py"])),
        "host": profile_conf.get("host", "127.0.0.1"),
        "port": profile_conf.get("port", 8091)
    }


def _default_generator_paths(profile_conf: dict, profile_name: str | None = None) -> dict:
    """Return default generator paths for the active profile"""
    resolved = resolve_paths(profile_conf)
    output_dir = os.path.dirname(resolved["tool_path"])
    output_path = os.path.join(output_dir, 'server.py')
    server_name = _guess_server_name(profile_conf, profile_name)
    template_path = _get_template_for_server(server_name)

    return {
        "tools_path": resolved["template_path"],
        "template_path": template_path,
        "output_path": output_path
    }


def discover_mcp_modules(profile_conf: dict | None = None) -> list:
    """
    Detect modules that contain an MCP server folder.
    Assumes each module has the same mcp/mcp_server structure.
    """
    modules = []
    profile_conf = profile_conf or DEFAULT_PROFILE
    fallback = _default_generator_paths(profile_conf)

    if not os.path.isdir(ROOT_DIR):
        return modules

    for entry in os.listdir(ROOT_DIR):
        module_dir = os.path.join(ROOT_DIR, entry)
        if not os.path.isdir(module_dir):
            continue

        # Look for either mcp_server or a generic mcp folder
        for candidate in ("mcp_server", "mcp"):
            mcp_dir = os.path.join(module_dir, candidate)
            if not os.path.isdir(mcp_dir):
                continue

            server_name = get_server_name_from_path(module_dir) or get_server_name_from_profile(entry)
            template_path = _get_template_for_server(server_name) or fallback["template_path"]
            tools_candidates = [
                os.path.join(mcp_dir, "tool_definition_templates.py"),
                os.path.join(mcp_dir, "tool_definitions.py"),
                fallback["tools_path"]
            ]
            tools_path = next((p for p in tools_candidates if p and os.path.exists(p)), fallback["tools_path"])

            modules.append({
                "name": entry,
                "server_name": server_name,
                "mcp_dir": mcp_dir,
                "tools_path": tools_path,
                "template_path": template_path,
                "output_path": os.path.join(mcp_dir, "server.py")
            })
            break

    modules.sort(key=lambda x: x["name"].lower())
    return modules


def load_generator_module():
    """Load the Jinja2 generator module dynamically"""
    if not os.path.exists(GENERATOR_SCRIPT_PATH):
        raise FileNotFoundError(f"Generator script not found at {GENERATOR_SCRIPT_PATH}")

    spec = importlib.util.spec_from_file_location("mcp_jinja_generator", GENERATOR_SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ensure_dirs(paths: dict):
    os.makedirs(paths["backup_dir"], exist_ok=True)


def load_tool_definitions(paths: dict):
    """
    Load MCP_TOOLS, preferring the template file (with mcp_service metadata)
    Templates are auto-generated with AST-extracted signatures
    """
    try:
        # Try loading from templates first (has metadata)
        if os.path.exists(paths["template_path"]):
            spec = importlib.util.spec_from_file_location("tool_definition_templates", paths["template_path"])
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.MCP_TOOLS

        # Fallback to cleaned definitions
        spec = importlib.util.spec_from_file_location("tool_definitions", paths["tool_path"])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.MCP_TOOLS
    except Exception as e:
        return {"error": str(e)}


def load_internal_args(paths: dict) -> dict:
    """
    Load internal args from tool_internal_args.json
    Returns empty dict if file doesn't exist (graceful fallback)
    """
    internal_args_path = paths.get("internal_args_path")
    if not internal_args_path or not os.path.exists(internal_args_path):
        return {}
    try:
        with open(internal_args_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load internal_args from {internal_args_path}: {e}")
        return {}


def get_file_mtimes(paths: dict) -> dict:
    """
    Collect file modification times for conflict detection
    """
    mtimes = {}
    path_keys = [
        ("tool_path", "definitions"),
        ("template_path", "templates"),
        ("internal_args_path", "internal_args")
    ]
    for path_key, mtime_key in path_keys:
        path = paths.get(path_key)
        if path and os.path.exists(path):
            mtimes[mtime_key] = os.path.getmtime(path)
    return mtimes


def order_schema_fields(schema):
    """Recursively order schema fields according to JSON Schema standard"""
    if not isinstance(schema, dict):
        return schema

    ordered = {}

    # Add type first
    if 'type' in schema:
        ordered['type'] = schema['type']

    # Add description second
    if 'description' in schema:
        ordered['description'] = schema['description']

    # Add enum if present
    if 'enum' in schema:
        ordered['enum'] = schema['enum']

    # Add format if present
    if 'format' in schema:
        ordered['format'] = schema['format']

    # Process properties recursively
    if 'properties' in schema:
        ordered_props = {}
        for prop_name, prop_value in schema['properties'].items():
            ordered_props[prop_name] = order_schema_fields(prop_value)
        ordered['properties'] = ordered_props

    # Add items for arrays
    if 'items' in schema:
        ordered['items'] = order_schema_fields(schema['items'])

    # Add required
    if 'required' in schema:
        ordered['required'] = schema['required']

    # Add any other fields
    for k, v in schema.items():
        if k not in ['type', 'description', 'enum', 'format', 'properties', 'items', 'required']:
            ordered[k] = v

    return ordered


def remove_defaults(schema):
    """Recursively remove 'default' keys from schema"""
    if isinstance(schema, dict):
        schema = {k: remove_defaults(v) for k, v in schema.items() if k != 'default'}
        # Handle properties
        if 'properties' in schema and isinstance(schema['properties'], dict):
            schema['properties'] = {k: remove_defaults(v) for k, v in schema['properties'].items()}
        # Handle items
        if 'items' in schema:
            schema['items'] = remove_defaults(schema['items'])
    elif isinstance(schema, list):
        schema = [remove_defaults(item) for item in schema]
    return schema


def clean_newlines_from_schema(schema):
    """Recursively remove newline characters from all description fields in schema"""
    if isinstance(schema, dict):
        cleaned = {}
        for key, value in schema.items():
            if key == 'description' and isinstance(value, str):
                # Remove newline and carriage return characters
                cleaned_value = value.replace('\n', ' ').replace('\r', ' ')
                # Remove multiple spaces that might result from the replacement
                cleaned[key] = ' '.join(cleaned_value.split())
            else:
                cleaned[key] = clean_newlines_from_schema(value)
        return cleaned
    elif isinstance(schema, list):
        return [clean_newlines_from_schema(item) for item in schema]
    else:
        return schema


def prune_internal_properties(tools_data: list, internal_args: dict):
    """Remove inputSchema properties that are marked as internal args.

    This keeps tool_definition_templates/tool_definitions in sync even if
    internal_args were added/edited outside the UI toggle flow.
    """
    if not internal_args:
        return tools_data

    for tool in tools_data:
        name = tool.get("name")
        internal_props = internal_args.get(name)
        if not internal_props:
            continue

        schema = tool.get("inputSchema")
        if not isinstance(schema, dict):
            continue

        props = schema.get("properties")
        if not isinstance(props, dict):
            continue

        for prop_name in list(internal_props.keys()):
            if prop_name in props:
                del props[prop_name]
            if isinstance(schema.get("required"), list):
                schema["required"] = [r for r in schema["required"] if r != prop_name]

    return tools_data


SERVICE_SCAN_CACHE: dict[tuple[str, str], dict] = {}


def _load_services_for_server(server_name: str | None, scan_dir: str | None, force_rescan: bool = False):
    """Load service metadata with simple in-process caching."""
    if not scan_dir:
        return {}

    cache_key = (server_name or "", scan_dir)
    if not force_rescan and cache_key in SERVICE_SCAN_CACHE:
        print(f"Using cached service signatures for {cache_key[0] or 'default'}")
        return SERVICE_SCAN_CACHE[cache_key]

    services = get_services_map(scan_dir, server_name)
    SERVICE_SCAN_CACHE[cache_key] = services
    print(f"Extracted {len(services)} services from source code ({'rescan' if force_rescan else 'fresh'})")
    return services


def save_tool_definitions(tools_data, paths: dict, force_rescan: bool = False, skip_backup: bool = False):
    """Save MCP_TOOLS to both tool_definitions.py and tool_definition_templates.py

    Args:
        tools_data: List of tool definitions to save
        paths: Resolved paths dict from resolve_paths()
        force_rescan: Force rescan of service signatures
        skip_backup: Skip internal backup (use when caller already handles backup)
    """
    try:
        ensure_dirs(paths)
        backup_filename = None
        # Create backup first (unless caller is handling backups)
        if not skip_backup:
            backup_filename = f"tool_definitions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            backup_path = os.path.join(paths["backup_dir"], backup_filename)
            if os.path.exists(paths["tool_path"]):
                shutil.copy2(paths["tool_path"], backup_path)

        # 1. Save tool_definitions.py (without mcp_service fields)
        # Remove mcp_service field from all tools before saving
        # and reorder fields for better readability
        cleaned_tools = []
        for tool in tools_data:
            # Create cleaned tool with specific field order
            cleaned_tool = {}
            # Add fields in desired order
            if 'name' in tool:
                cleaned_tool['name'] = tool['name']
            if 'description' in tool:
                # Remove newline characters from description to prevent JSON parsing errors
                cleaned_description = tool['description'].replace('\n', ' ').replace('\r', ' ')
                # Also remove multiple spaces that might result from the replacement
                cleaned_description = ' '.join(cleaned_description.split())
                cleaned_tool['description'] = cleaned_description
            if 'inputSchema' in tool:
                # Remove defaults for the public definitions and order schema
                cleaned_input = copy.deepcopy(tool['inputSchema'])
                cleaned_input = remove_defaults(cleaned_input)
                # Recursively clean newlines from all descriptions in inputSchema
                cleaned_input = clean_newlines_from_schema(cleaned_input)
                cleaned_tool['inputSchema'] = order_schema_fields(cleaned_input)
            # Add any other fields except mcp_service and mcp_service_factors
            for k, v in tool.items():
                if k not in ['name', 'description', 'inputSchema', 'mcp_service', 'mcp_service_factors']:
                    cleaned_tool[k] = v
            cleaned_tools.append(cleaned_tool)

        # Generate tool_definitions.py content
        server_name = get_server_name_from_path(paths.get("tool_path", "")) or get_server_name_from_path(paths.get("template_path", ""))
        server_label = (server_name or "MCP").replace("_", " ").title()
        content = f'''"""
MCP Tool Definitions for {server_label} Server - AUTO-GENERATED FILE
DO NOT EDIT THIS FILE MANUALLY!

This file is automatically generated when you save changes in the MCP Tool Editor.
It contains clean tool definitions for use with Claude/OpenAI APIs.
Internal metadata fields (mcp_service, mcp_service_factors) are removed.

Generated from: MCP Tool Editor Web Interface
To modify: Use the web editor at http://localhost:8091
"""

from typing import List, Dict, Any
import json

# MCP Tool Definitions
MCP_TOOLS: List[Dict[str, Any]] = json.loads("""
'''

        # Format the tools data using JSON for consistent alignment/readability
        formatted_tools = json.dumps(cleaned_tools, indent=4, ensure_ascii=False)
        content += formatted_tools
        content += '\n""")\n\n'

        # Add helper functions
        content += '''


def get_tool_by_name(tool_name: str) -> Dict[str, Any] | None:
    """Get a specific tool definition by name"""
    for tool in MCP_TOOLS:
        if tool["name"] == tool_name:
            return tool
    return None


def get_tool_names() -> List[str]:
    """Get list of all available tool names"""
    return [tool["name"] for tool in MCP_TOOLS]
'''

        # Write tool_definitions.py
        with open(paths["tool_path"], 'w', encoding='utf-8') as f:
            f.write(content)

        # 2. Save tool_definition_templates.py (with AST-extracted metadata)
        # Extract signatures from source code using AST (cached)
        services_by_name = {}
        if server_name:
            module_patterns = [
                os.path.join(ROOT_DIR, f'mcp_{server_name}'),
                os.path.join(ROOT_DIR, f'{server_name}_mcp'),
            ]
            scan_dir = next((p for p in module_patterns if os.path.isdir(p)), None)

            if scan_dir:
                services_by_name = _load_services_for_server(server_name, scan_dir, force_rescan=force_rescan)

        # Build template tools
        template_tools = []
        for tool in tools_data:
            template_tool = {k: v for k, v in tool.items()}
            if 'inputSchema' in template_tool:
                template_tool['inputSchema'] = order_schema_fields(template_tool['inputSchema'])

            # Add signature if available
            if 'mcp_service' in template_tool and isinstance(template_tool['mcp_service'], dict):
                service_name = template_tool['mcp_service'].get('name')
                if service_name and service_name in services_by_name:
                    service_info = services_by_name[service_name]
                    template_tool['mcp_service']['signature'] = service_info.get('signature')
                    if service_info.get('parameters'):
                        template_tool['mcp_service']['parameters'] = service_info['parameters']

            template_tools.append(template_tool)

        # Write template file (use path from config, which includes server folder structure)
        template_path = paths.get("template_path")

        template_content = f'''"""
MCP Tool Definition Templates - AUTO-GENERATED
Signatures extracted from source code using AST parsing
"""
from typing import List, Dict, Any

MCP_TOOLS: List[Dict[str, Any]] = {pprint.pformat(template_tools, indent=4, width=120, compact=False)}
'''

        # Ensure template directory exists
        os.makedirs(os.path.dirname(template_path), exist_ok=True)

        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)

        print(f"Saved template to: {os.path.relpath(template_path, BASE_DIR)}")

        return {"success": True, "backup": backup_filename}
    except Exception as e:
        return {"error": str(e)}


@app.route('/')
def index():
    """Main editor page"""
    return render_template('tool_editor.html')


@app.route('/debug')
def debug():
    """Debug test page"""
    return render_template('debug_test.html')


@app.route('/simple-test')
def simple_test():
    """Simple API test page"""
    return render_template('simple_test.html')


@app.route('/debug-editor')
def debug_editor():
    """Debug version of the main editor"""
    return render_template('tool_editor_debug.html')


@app.route('/debug-index')
def debug_index():
    """Debug tools index page"""
    return render_template('debug_index.html')


@app.route('/api/tools', methods=['GET'])
def get_tools():
    """API endpoint to get current tool definitions + internal args"""
    profile = request.args.get("profile")
    profile_conf = get_profile_config(profile)
    paths = resolve_paths(profile_conf)

    # 1. Load tool definitions (templates)
    tools = load_tool_definitions(paths)
    if isinstance(tools, dict) and "error" in tools:
        return jsonify(tools), 500

    # 2. Load internal args
    internal_args = load_internal_args(paths)

    # 3. Collect file mtimes for conflict detection
    file_mtimes = get_file_mtimes(paths)

    actual_profile = profile or list_profile_names()[0] if list_profile_names() else "default"
    return jsonify({
        "tools": tools,
        "internal_args": internal_args,
        "profile": actual_profile,
        "file_mtimes": file_mtimes
    })


@app.route('/api/tools', methods=['POST'])
def save_tools():
    """API endpoint to save tool definitions"""
    try:
        profile = request.args.get("profile")
        profile_conf = get_profile_config(profile)
        paths = resolve_paths(profile_conf)
        tools_data = request.json
        force_rescan = str(request.args.get("force_rescan", "")).lower() in ("1", "true", "yes")
        result = save_tool_definitions(tools_data, paths, force_rescan=force_rescan)
        if "error" in result:
            return jsonify(result), 500
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/tools/<int:tool_index>', methods=['DELETE'])
def delete_tool(tool_index):
    """Delete a specific tool by index"""
    try:
        profile = request.args.get("profile")
        profile_conf = get_profile_config(profile)
        paths = resolve_paths(profile_conf)
        # Load current tools
        tools = load_tool_definitions(paths)
        if isinstance(tools, dict) and "error" in tools:
            return jsonify(tools), 500

        if tool_index >= len(tools) or tool_index < 0:
            return jsonify({"error": "Invalid tool index"}), 400

        # Get the tool name for response
        deleted_tool = tools[tool_index]
        tool_name = deleted_tool.get("name", f"Tool {tool_index}")

        # Remove the tool
        tools.pop(tool_index)

        # Save the updated tools
        force_rescan = str(request.args.get("force_rescan", "")).lower() in ("1", "true", "yes")
        result = save_tool_definitions(tools, paths, force_rescan=force_rescan)
        if "error" in result:
            return jsonify(result), 500

        # CRITICAL: Clean up internal args for deleted tool (Issue 3 fix)
        internal_args = load_internal_args(paths)
        internal_args_cleaned = False
        if tool_name in internal_args:
            del internal_args[tool_name]
            internal_args_cleaned = True
            save_internal_args(internal_args, paths)

        return jsonify({
            "success": True,
            "message": f"Tool '{tool_name}' deleted successfully",
            "backup": result.get("backup"),
            "internal_args_cleaned": internal_args_cleaned
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/tools/validate', methods=['POST'])
def validate_tools():
    """Validate tool definitions"""
    try:
        tools_data = request.json

        # Basic validation
        if not isinstance(tools_data, list):
            return jsonify({"valid": False, "error": "Tools must be a list"}), 400

        for i, tool in enumerate(tools_data):
            if not isinstance(tool, dict):
                return jsonify({"valid": False, "error": f"Tool {i} must be a dictionary"}), 400

            # Check required fields
            if "name" not in tool:
                return jsonify({"valid": False, "error": f"Tool {i} missing 'name' field"}), 400
            if "description" not in tool:
                return jsonify({"valid": False, "error": f"Tool {i} missing 'description' field"}), 400
            if "inputSchema" not in tool:
                return jsonify({"valid": False, "error": f"Tool {i} missing 'inputSchema' field"}), 400

            # Validate inputSchema structure
            schema = tool.get("inputSchema", {})
            if not isinstance(schema, dict):
                return jsonify({"valid": False, "error": f"Tool {i} inputSchema must be a dictionary"}), 400
            if "type" not in schema or schema["type"] != "object":
                return jsonify({"valid": False, "error": f"Tool {i} inputSchema type must be 'object'"}), 400
            if "properties" not in schema:
                return jsonify({"valid": False, "error": f"Tool {i} inputSchema missing 'properties'"}), 400

        return jsonify({"valid": True})
    except Exception as e:
        return jsonify({"valid": False, "error": str(e)}), 500


@app.route('/api/backups', methods=['GET'])
def list_backups():
    """List available backups"""
    try:
        profile = request.args.get("profile")
        profile_conf = get_profile_config(profile)
        paths = resolve_paths(profile_conf)
        ensure_dirs(paths)
        backups = []
        for filename in os.listdir(paths["backup_dir"]):
            if filename.startswith('tool_definitions_') and filename.endswith('.py'):
                file_path = os.path.join(paths["backup_dir"], filename)
                stat = os.stat(file_path)
                backups.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        backups.sort(key=lambda x: x["modified"], reverse=True)
        return jsonify(backups)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/backups/<filename>', methods=['GET'])
def get_backup(filename):
    """Get a specific backup file"""
    try:
        # Security check - ensure filename is safe
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({"error": "Invalid filename"}), 400

        profile = request.args.get("profile")
        profile_conf = get_profile_config(profile)
        paths = resolve_paths(profile_conf)

        file_path = os.path.join(paths["backup_dir"], filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "Backup not found"}), 404

        spec = importlib.util.spec_from_file_location("backup", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return jsonify(module.MCP_TOOLS)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/backups/<filename>/restore', methods=['POST'])
def restore_backup(filename):
    """Restore from a backup"""
    try:
        # Security check
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({"error": "Invalid filename"}), 400

        profile = request.args.get("profile")
        profile_conf = get_profile_config(profile)
        paths = resolve_paths(profile_conf)
        ensure_dirs(paths)

        backup_path = os.path.join(paths["backup_dir"], filename)
        if not os.path.exists(backup_path):
            return jsonify({"error": "Backup not found"}), 404

        # Create a backup of current state before restoring
        current_backup = f"tool_definitions_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        if os.path.exists(paths["tool_path"]):
            shutil.copy2(paths["tool_path"], os.path.join(paths["backup_dir"], current_backup))

        # Restore the backup
        shutil.copy2(backup_path, paths["tool_path"])

        return jsonify({"success": True, "current_backup": current_backup})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/mcp-services', methods=['GET'])
def get_mcp_services():
    """Get available MCP services from server-specific mcp_services.json"""
    try:
        # Get profile parameter to determine which server
        profiles = list_profile_names()
        profile = request.args.get('profile') or (profiles[0] if profiles else 'default')

        # Determine server name from profile using mappings
        server_name = get_server_name_from_profile(profile)

        # Try server-specific file first from server folder
        mcp_services_path = None
        if server_name:
            # New path: mcp_editor/{server_name}/{server_name}_mcp_services.json
            specific_path = os.path.join(os.path.dirname(__file__), server_name, f'{server_name}_mcp_services.json')
            if os.path.exists(specific_path):
                mcp_services_path = specific_path
                print(f"Loading services from {server_name}/{server_name}_mcp_services.json")
            else:
                # Fallback to old location for backward compatibility
                old_path = os.path.join(os.path.dirname(__file__), f'{server_name}_mcp_services.json')
                if os.path.exists(old_path):
                    mcp_services_path = old_path
                    print(f"Loading services from {server_name}_mcp_services.json (legacy location)")

        # Fallback to generic file
        if not mcp_services_path or not os.path.exists(mcp_services_path):
            mcp_services_path = os.path.join(os.path.dirname(__file__), 'mcp_services.json')

        if os.path.exists(mcp_services_path):
            with open(mcp_services_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                decorated = data.get("decorated_services", [])

                # Build signature strings from parameter metadata
                detailed = []
                for service in data.get("services_with_signatures", []):
                    params = service.get("parameters", [])
                    param_strings = []
                    for param in params:
                        if param.get("name") == "self":
                            continue
                        part = param.get("name", "")
                        if param.get("type"):
                            part += f": {param['type']}"
                        if param.get("default") is not None:
                            part += f" = {param['default']}"
                        param_strings.append(part)

                    detailed.append({
                        "name": service.get("name"),
                        "parameters": params,
                        "signature": ", ".join(param_strings)
                    })

                return jsonify({
                    "services": decorated,
                    "services_with_signatures": detailed
                })
        return jsonify({"services": [], "services_with_signatures": []})
    except Exception as e:
        return jsonify({"error": str(e), "services": [], "services_with_signatures": []}), 500


@app.route('/api/template-sources', methods=['GET'])
def get_template_sources():
    """Get available template files (tool_definition_templates.py and backups) for loading"""
    try:
        profile = request.args.get('profile')
        profile_conf = get_profile_config(profile)
        paths = resolve_paths(profile_conf)

        sources = []
        editor_dir = os.path.dirname(__file__)

        # 1. Current template file (primary)
        template_path = paths.get("template_path")
        if template_path and os.path.exists(template_path):
            try:
                spec = importlib.util.spec_from_file_location("template", template_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                tool_count = len(getattr(module, 'MCP_TOOLS', []))
                sources.append({
                    "name": "Current Template",
                    "path": template_path,
                    "type": "current",
                    "count": tool_count,
                    "modified": datetime.fromtimestamp(os.path.getmtime(template_path)).isoformat()
                })
            except Exception as e:
                print(f"Warning: Could not read current template {template_path}: {e}")

        # 2. Backup files
        backup_dir = paths.get("backup_dir")
        if backup_dir and os.path.isdir(backup_dir):
            for filename in os.listdir(backup_dir):
                if filename.startswith('tool_definitions_') and filename.endswith('.py'):
                    filepath = os.path.join(backup_dir, filename)
                    try:
                        spec = importlib.util.spec_from_file_location("backup", filepath)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        tool_count = len(getattr(module, 'MCP_TOOLS', []))
                        sources.append({
                            "name": filename,
                            "path": filepath,
                            "type": "backup",
                            "count": tool_count,
                            "modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                        })
                    except Exception as e:
                        print(f"Warning: Could not read backup {filepath}: {e}")

        # 3. Other profile templates
        all_profiles = list_profile_names()
        current_profile_name = profile or (all_profiles[0] if all_profiles else None)
        for other_profile in all_profiles:
            if other_profile == current_profile_name:
                continue
            other_conf = get_profile_config(other_profile)
            other_paths = resolve_paths(other_conf)
            other_template = other_paths.get("template_path")
            if other_template and os.path.exists(other_template):
                try:
                    spec = importlib.util.spec_from_file_location("other", other_template)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    tool_count = len(getattr(module, 'MCP_TOOLS', []))
                    sources.append({
                        "name": f"{other_profile} template",
                        "path": other_template,
                        "type": "other_profile",
                        "profile": other_profile,
                        "count": tool_count,
                        "modified": datetime.fromtimestamp(os.path.getmtime(other_template)).isoformat()
                    })
                except Exception as e:
                    print(f"Warning: Could not read {other_profile} template: {e}")

        # Sort: current first, then by modified date descending
        sources.sort(key=lambda x: (0 if x['type'] == 'current' else 1, x.get('modified', ''), x['name']), reverse=False)

        return jsonify({"sources": sources})
    except Exception as e:
        return jsonify({"error": str(e), "sources": []}), 500


@app.route('/api/template-sources/load', methods=['POST'])
def load_from_template_source():
    """Load MCP_TOOLS from a specific template file"""
    try:
        data = request.json or {}
        source_path = data.get('path')

        if not source_path:
            return jsonify({"error": "path is required"}), 400

        if not os.path.exists(source_path):
            return jsonify({"error": f"File not found: {source_path}"}), 404

        # Security check - only allow .py files in expected directories
        editor_dir = os.path.dirname(__file__)
        abs_source = os.path.abspath(source_path)
        abs_editor = os.path.abspath(editor_dir)
        abs_root = os.path.abspath(ROOT_DIR)

        if not (abs_source.startswith(abs_editor) or abs_source.startswith(abs_root)):
            return jsonify({"error": "Access denied: path outside allowed directories"}), 403

        if not source_path.endswith('.py'):
            return jsonify({"error": "Only .py files are allowed"}), 400

        # Load MCP_TOOLS from the file
        spec = importlib.util.spec_from_file_location("source_template", source_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        tools = getattr(module, 'MCP_TOOLS', [])

        return jsonify({
            "success": True,
            "tools": tools,
            "source": source_path,
            "count": len(tools)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/profiles', methods=['GET'])
def get_profiles():
    """List available profiles from editor_config.json"""
    try:
        profiles = list_profile_names()
        active = request.args.get("profile") or os.environ.get("MCP_EDITOR_MODULE") or (profiles[0] if profiles else "default")
        return jsonify({"profiles": profiles, "active": active})
    except Exception as e:
        return jsonify({"error": str(e), "profiles": []}), 500


@app.route('/api/profiles', methods=['POST'])
def create_profile():
    """Create a new profile (project) with directory structure"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        profile_name = data.get("name", "").strip().lower().replace(" ", "_")
        if not profile_name:
            return jsonify({"error": "Profile name is required"}), 400

        # Check if profile already exists
        existing = list_profile_names()
        if profile_name in existing:
            return jsonify({"error": f"Profile '{profile_name}' already exists"}), 400

        # Get paths from request or generate defaults
        mcp_server_path = data.get("mcp_server_path", f"../mcp_{profile_name}/mcp_server")
        template_path = data.get("template_path", f"{profile_name}/tool_definition_templates.py")
        backup_dir = data.get("backup_dir", f"{profile_name}/backups")
        port = data.get("port", 8091)

        # Create profile config
        new_profile = {
            "template_definitions_path": template_path,
            "tool_definitions_path": f"{mcp_server_path}/tool_definitions.py",
            "backup_dir": backup_dir,
            "types_files": [],
            "host": "0.0.0.0",
            "port": port
        }

        # Create directory structure in mcp_editor
        editor_profile_dir = os.path.join(BASE_DIR, profile_name)
        os.makedirs(editor_profile_dir, exist_ok=True)
        os.makedirs(os.path.join(editor_profile_dir, "backups"), exist_ok=True)

        # Create empty tool_definition_templates.py
        template_file_path = os.path.join(BASE_DIR, template_path)
        if not os.path.exists(template_file_path):
            with open(template_file_path, 'w', encoding='utf-8') as f:
                f.write('''"""
MCP Tool Definition Templates - AUTO-GENERATED
Signatures extracted from source code using AST parsing
"""
from typing import List, Dict, Any

MCP_TOOLS: List[Dict[str, Any]] = []
''')

        # Create MCP server directory structure if requested
        if data.get("create_mcp_structure", False):
            mcp_dir = _resolve_path(mcp_server_path)
            os.makedirs(mcp_dir, exist_ok=True)

            # Create empty tool_definitions.py
            tool_def_path = os.path.join(mcp_dir, "tool_definitions.py")
            if not os.path.exists(tool_def_path):
                with open(tool_def_path, 'w', encoding='utf-8') as f:
                    f.write('''"""
MCP Tool Definitions - AUTO-GENERATED FILE
"""
from typing import List, Dict, Any

MCP_TOOLS: List[Dict[str, Any]] = []


def get_tool_by_name(tool_name: str) -> Dict[str, Any] | None:
    for tool in MCP_TOOLS:
        if tool["name"] == tool_name:
            return tool
    return None


def get_tool_names() -> List[str]:
    return [tool["name"] for tool in MCP_TOOLS]
''')

        # Update editor_config.json
        config_path = os.path.join(BASE_DIR, 'editor_config.json')
        config_data = _load_config_file()
        config_data[profile_name] = new_profile

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, indent=2, ensure_ascii=False, fp=f)

        return jsonify({
            "success": True,
            "profile": profile_name,
            "config": new_profile,
            "created_dirs": [editor_profile_dir]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/server-generator/defaults', methods=['GET'])
def get_server_generator_defaults():
    """Expose detected modules and default paths for the Jinja2 server generator"""
    try:
        profile = request.args.get("profile")
        profile_conf = get_profile_config(profile)
        modules = discover_mcp_modules(profile_conf)
        fallback = _default_generator_paths(profile_conf, profile)
        preferred_server = _guess_server_name(profile_conf, profile)
        active_module = None

        if preferred_server:
            for mod in modules:
                mod_server = mod.get("server_name") or get_server_name_from_path(mod.get("mcp_dir", "")) \
                    or get_server_name_from_profile(mod.get("name", ""))
                if mod_server == preferred_server:
                    active_module = mod.get("name")
                    break

        if not active_module and modules:
            active_module = modules[0]["name"]

        return jsonify({
            "modules": modules,
            "fallback": fallback,
            "active_module": active_module,
            "server_name": preferred_server
        })
    except Exception as e:
        return jsonify({"error": str(e), "modules": [], "fallback": {}}), 500


@app.route('/api/graph-types-properties', methods=['GET'])
def get_graph_types_properties():
    """Get available properties from types files for the current profile"""
    try:
        profile = request.args.get('profile')
        profile_conf = get_profile_config(profile)
        paths = resolve_paths(profile_conf)

        types_files = paths.get("types_files", [])

        # If no types_files configured, return empty with a flag
        if not types_files:
            return jsonify({
                "classes": [],
                "properties_by_class": {},
                "all_properties": [],
                "has_types": False,
                "types_name": None
            })

        # Get server name for display
        server_name = get_server_name_from_profile(profile) or "types"

        # Try to load from cached properties file for this profile
        profile_name = profile or "default"

        # Try new naming convention in MCPMetaRegistry folder first
        registry_path = os.path.join(os.path.dirname(__file__), 'MCPMetaRegistry', f'{server_name}_types_properties.json')

        # Then try profile-specific path
        if not os.path.exists(registry_path):
            properties_path = os.path.join(os.path.dirname(__file__), profile_name, 'types_properties.json')
        else:
            properties_path = registry_path

        # Fallback to legacy path
        if not os.path.exists(properties_path):
            properties_path = os.path.join(os.path.dirname(__file__), 'types_properties.json')

        if os.path.exists(properties_path):
            with open(properties_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data["has_types"] = True
                data["types_name"] = f"{server_name}_types"
                return jsonify(data)
        else:
            # Try to generate using extract script
            import subprocess
            extract_script = os.path.join(os.path.dirname(__file__), 'extract_graph_types.py')
            if os.path.exists(extract_script):
                # Pass types files as arguments
                subprocess.run([sys.executable, extract_script] + types_files, check=True)
                if os.path.exists(properties_path):
                    with open(properties_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        data["has_types"] = True
                        data["types_name"] = f"{server_name}_types"
                        return jsonify(data)

        return jsonify({
            "classes": [],
            "properties_by_class": {},
            "all_properties": [],
            "has_types": bool(types_files),
            "types_name": f"{server_name}_types" if types_files else None
        })
    except Exception as e:
        return jsonify({"error": str(e), "classes": [], "properties_by_class": {}, "all_properties": [], "has_types": False}), 500


@app.route('/api/basemodels', methods=['GET'])
def get_basemodels():
    """Get available BaseModel schemas from outlook_types.py"""
    try:
        profile = request.args.get("profile")
        profile_conf = get_profile_config(profile)
        paths = resolve_paths(profile_conf)
        graph_type_paths = paths.get("types_files")

        models = load_graph_types_models(graph_type_paths)
        schemas = generate_mcp_schemas_from_graph_types(graph_type_paths)

        result = []
        for name, model in models.items():
            schema = schemas.get(name, {})
            result.append({
                "name": name,
                "description": model.__doc__ or f"{name} BaseModel",
                "schema": schema
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/tools/<int:tool_index>/apply-basemodel', methods=['POST'])
def apply_basemodel_to_property(tool_index):
    """Apply a BaseModel schema to a specific property of a tool"""
    try:
        profile = request.args.get("profile")
        profile_conf = get_profile_config(profile)
        paths = resolve_paths(profile_conf)
        graph_type_paths = paths.get("types_files")

        data = request.json
        property_name = data.get('property_name')
        basemodel_name = data.get('basemodel_name')

        if not property_name or not basemodel_name:
            return jsonify({"error": "Missing property_name or basemodel_name"}), 400

        # Load current tools
        tools = load_tool_definitions(paths)
        if isinstance(tools, dict) and "error" in tools:
            return jsonify(tools), 500

        if tool_index >= len(tools):
            return jsonify({"error": "Invalid tool index"}), 400

        # Apply BaseModel schema
        tool = tools[tool_index]
        updated_tool = update_tool_with_basemodel_schema(tool, basemodel_name, property_name, graph_type_paths)

        # Save the updated tools
        force_rescan = str(request.args.get("force_rescan", "")).lower() in ("1", "true", "yes")
        result = save_tool_definitions(tools, paths, force_rescan=force_rescan)
        if "error" in result:
            return jsonify(result), 500

        return jsonify({"success": True, "tool": updated_tool})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/server-generator', methods=['POST'])
def generate_server_from_web():
    """Run the Jinja2 server generator with paths provided by the web editor"""
    try:
        profile = request.args.get("profile")
        profile_conf = get_profile_config(profile)
        modules = discover_mcp_modules(profile_conf)
        defaults = _default_generator_paths(profile_conf, profile)

        data = request.json or {}
        module_name = data.get("module")
        selected_module = next((m for m in modules if m.get("name") == module_name), None)
        server_name = data.get("server_name") or get_server_name_from_profile(profile)
        if not server_name and selected_module:
            server_name = get_server_name_from_path(selected_module.get("mcp_dir", ""))

        tools_path = data.get("tools_path") or (selected_module["tools_path"] if selected_module else defaults["tools_path"])
        template_path = data.get("template_path") or (selected_module["template_path"] if selected_module else defaults["template_path"])
        output_path = data.get("output_path") or (selected_module["output_path"] if selected_module else defaults["output_path"])

        if not server_name:
            for candidate_path in (tools_path, template_path, output_path):
                if candidate_path:
                    server_name = get_server_name_from_path(str(candidate_path))
                    if server_name:
                        break

        if not template_path:
            template_path = _get_template_for_server(server_name)

        if not tools_path:
            return jsonify({"error": "tools_path is required"}), 400
        if not template_path:
            return jsonify({"error": "template_path is required"}), 400
        if not output_path:
            return jsonify({"error": "output_path is required"}), 400

        def resolve_for_generator(path_value: str) -> str:
            """Resolve a provided path against both editor and repo roots"""
            if os.path.isabs(path_value):
                return path_value
            editor_path = _resolve_path(path_value)
            if os.path.exists(editor_path):
                return editor_path
            return os.path.normpath(os.path.join(ROOT_DIR, path_value))

        tools_path = resolve_for_generator(tools_path)
        template_path = resolve_for_generator(template_path)
        output_path = resolve_for_generator(output_path)

        if not os.path.exists(tools_path):
            return jsonify({"error": f"Tools file not found: {tools_path}"}), 400
        if not os.path.exists(template_path):
            return jsonify({"error": f"Template file not found: {template_path}"}), 400

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        generator_module = load_generator_module()
        loaded_tools = generator_module.load_tool_definitions(tools_path)
        try:
            # Pass tools_path so generator can find internal_args
            generator_module.generate_server(template_path, output_path, loaded_tools,
                                            tools_path=tools_path, server_name=server_name)
        except TypeError:
            # Backwards compatibility with older generator signature
            try:
                generator_module.generate_server(template_path, output_path, loaded_tools, server_name=server_name)
            except TypeError:
                generator_module.generate_server(template_path, output_path, loaded_tools)

        return jsonify({
            "success": True,
            "module": module_name,
            "tools_path": tools_path,
            "template_path": template_path,
            "output_path": output_path,
            "tool_count": len(loaded_tools)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scaffold/create', methods=['POST'])
def create_new_server():
    """Create a new MCP server project from scratch"""
    try:
        data = request.json
        server_name = data.get('server_name', '').strip()
        description = data.get('description', '').strip()
        port = data.get('port', 8080)

        # Validation
        if not server_name:
            return jsonify({"error": "Server name is required"}), 400

        # Check if server already exists
        server_dir = os.path.join(ROOT_DIR, f"mcp_{server_name}")
        if os.path.exists(server_dir):
            return jsonify({"error": f"Server 'mcp_{server_name}' already exists"}), 409

        # Import scaffold generator
        scaffold_path = os.path.join(JINJA_DIR, "scaffold_generator.py")
        if not os.path.exists(scaffold_path):
            return jsonify({"error": f"scaffold_generator.py not found at {scaffold_path}"}), 500
        sys.path.insert(0, JINJA_DIR)
        from scaffold_generator import MCPServerScaffold

        # Create the server
        generator = MCPServerScaffold(ROOT_DIR)
        result = generator.create_server_project(
            server_name=server_name,
            description=description,
            port=port,
            create_venv=False  # Don't create venv in web context
        )

        if result.get("errors"):
            return jsonify({
                "error": "Server created with errors",
                "details": result
            }), 500

        return jsonify({
            "success": True,
            "message": f"Successfully created MCP server: {server_name}",
            "server_name": server_name,
            "created_files": result["created_files"],
            "created_dirs": result["created_dirs"],
            "next_steps": [
                f"cd mcp_{server_name}/mcp_server",
                "python -m venv venv && source venv/bin/activate",
                "pip install fastapi uvicorn pydantic",
                f"Select '{server_name}' profile in web editor"
            ]
        })

    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route('/api/scaffold/check', methods=['POST'])
def check_server_exists():
    """Check if a server name is available"""
    try:
        data = request.json
        server_name = data.get('server_name', '').strip()

        if not server_name:
            return jsonify({"valid": False, "error": "Server name is required"}), 400

        # Check naming rules
        if not server_name.replace('_', '').isalnum():
            return jsonify({
                "valid": False,
                "error": "Server name must contain only letters, numbers, and underscores"
            }), 400

        # Check if exists
        server_dir = os.path.join(ROOT_DIR, f"mcp_{server_name}")
        exists = os.path.exists(server_dir)

        return jsonify({
            "valid": not exists,
            "exists": exists,
            "server_name": server_name,
            "path": server_dir
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# Internal Args API Endpoints
# ============================================================

def save_internal_args(internal_args: dict, paths: dict) -> dict:
    """Save internal args to JSON file.

    Structure:
    - default: Static values stored in original_schema.properties[prop].default
              (from UI/Pydantic/saved settings)
    - value: Optional stored runtime value (if needed for persistence)

    The server's build_internal_param function uses priority:
    1. runtime_value (passed at function call time)
    2. stored value field (if exists)
    3. defaults from original_schema.properties
    """
    try:
        internal_args_path = paths.get("internal_args_path")
        if not internal_args_path:
            return {"error": "internal_args_path not configured"}

        # Ensure directory exists
        os.makedirs(os.path.dirname(internal_args_path), exist_ok=True)

        with open(internal_args_path, 'w', encoding='utf-8') as f:
            json.dump(internal_args, f, indent=2, ensure_ascii=False)

        return {"success": True, "path": internal_args_path}
    except Exception as e:
        return {"error": str(e)}


def backup_file(file_path: str, backup_dir: str, timestamp: str) -> str | None:
    """Create backup of a file with shared timestamp"""
    if not os.path.exists(file_path):
        return None

    os.makedirs(backup_dir, exist_ok=True)
    filename = os.path.basename(file_path)
    backup_path = os.path.join(backup_dir, f"{filename}_{timestamp}.bak")

    shutil.copy2(file_path, backup_path)
    return backup_path


def cleanup_old_backups(backup_dir: str, keep_count: int = 10):
    """Remove old backups keeping only the most recent ones (by timestamp group)"""
    if not os.path.exists(backup_dir):
        return

    # Group backups by timestamp
    backup_groups = {}
    for filename in os.listdir(backup_dir):
        if not filename.endswith('.bak'):
            continue
        # Extract timestamp from filename (format: filename_YYYYMMDD_HHMMSS.bak)
        parts = filename.rsplit('_', 2)
        if len(parts) >= 3:
            timestamp = f"{parts[-2]}_{parts[-1].replace('.bak', '')}"
            if timestamp not in backup_groups:
                backup_groups[timestamp] = []
            backup_groups[timestamp].append(filename)

    # Sort timestamps and remove old groups
    sorted_timestamps = sorted(backup_groups.keys(), reverse=True)
    for old_timestamp in sorted_timestamps[keep_count:]:
        for filename in backup_groups[old_timestamp]:
            try:
                os.remove(os.path.join(backup_dir, filename))
            except Exception as e:
                print(f"Warning: Could not remove old backup {filename}: {e}")


@app.route('/api/internal-args', methods=['GET'])
def get_internal_args():
    """Get internal args for the current profile"""
    try:
        profile = request.args.get("profile")
        profile_conf = get_profile_config(profile)
        paths = resolve_paths(profile_conf)

        internal_args = load_internal_args(paths)
        return jsonify({
            "internal_args": internal_args,
            "profile": profile or list_profile_names()[0] if list_profile_names() else "default",
            "path": paths.get("internal_args_path")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/internal-args', methods=['POST'])
def post_internal_args():
    """Save internal args (full replacement)"""
    try:
        profile = request.args.get("profile")
        profile_conf = get_profile_config(profile)
        paths = resolve_paths(profile_conf)

        internal_args = request.json
        if not isinstance(internal_args, dict):
            return jsonify({"error": "Request body must be a JSON object"}), 400

        # Create backup before saving
        backup_dir = paths.get("backup_dir")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_file(paths.get("internal_args_path"), backup_dir, timestamp)

        result = save_internal_args(internal_args, paths)
        if "error" in result:
            return jsonify(result), 500

        result["backup"] = backup_path
        result["warning"] = "internal_args saved but tool_definitions may be out of sync. Consider using POST /api/tools/save-all"
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/internal-args/<tool_name>', methods=['PUT'])
def put_internal_args_tool(tool_name: str):
    """Update internal args for a specific tool (merge)"""
    try:
        profile = request.args.get("profile")
        profile_conf = get_profile_config(profile)
        paths = resolve_paths(profile_conf)

        tool_args = request.json
        if not isinstance(tool_args, dict):
            return jsonify({"error": "Request body must be a JSON object"}), 400

        # Load existing internal args
        internal_args = load_internal_args(paths)

        # Merge tool args
        internal_args[tool_name] = tool_args

        # Create backup before saving
        backup_dir = paths.get("backup_dir")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_file(paths.get("internal_args_path"), backup_dir, timestamp)

        result = save_internal_args(internal_args, paths)
        if "error" in result:
            return jsonify(result), 500

        result["backup"] = backup_path
        result["tool"] = tool_name
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/tools/save-all', methods=['POST'])
def save_all_definitions():
    """
    Atomic save of all 3 files: tool_definitions.py, tool_definition_templates.py, tool_internal_args.json
    This is the recommended API for saving to ensure consistency.
    """
    try:
        profile = request.args.get("profile")
        profile_conf = get_profile_config(profile)
        paths = resolve_paths(profile_conf)
        ensure_dirs(paths)

        data = request.json
        if not isinstance(data, dict):
            return jsonify({"error": "Request body must be a JSON object"}), 400

        tools_data = data.get("tools")
        internal_args = data.get("internal_args", {})
        loaded_mtimes = data.get("file_mtimes")  # For conflict detection

        if not tools_data or not isinstance(tools_data, list):
            return jsonify({"error": "tools must be a list"}), 400

        # CRITICAL: Clean up orphaned internal_args (Issue 3 fix)
        # Remove internal_args for tools that no longer exist
        tool_names = {tool.get("name") for tool in tools_data if tool.get("name")}
        orphaned_tools = [t for t in internal_args.keys() if t not in tool_names]
        for orphaned in orphaned_tools:
            del internal_args[orphaned]

        # CRITICAL: Validate internal_args structure (Issue 5 fix)
        # Each internal arg must have a 'type' field for code generation
        validation_errors = []
        for tool_name, tool_args in internal_args.items():
            for arg_name, arg_info in tool_args.items():
                if not isinstance(arg_info, dict):
                    validation_errors.append(f"{tool_name}.{arg_name}: must be an object")
                elif not arg_info.get("type"):
                    validation_errors.append(f"{tool_name}.{arg_name}: missing required 'type' field")

        if validation_errors:
            return jsonify({
                "error": "Invalid internal_args",
                "validation_errors": validation_errors,
                "action": "fix_required",
                "message": "Each internal arg must have a 'type' field (e.g., SelectParams, FilterParams)"
            }), 400

        # CRITICAL: Strip any properties that are marked as internal before saving
        tools_data = prune_internal_properties(tools_data, internal_args)

        # Check for file conflicts (optional)
        if loaded_mtimes:
            current_mtimes = get_file_mtimes(paths)
            conflicts = []
            for key in ["definitions", "templates", "internal_args"]:
                if key in loaded_mtimes and key in current_mtimes:
                    if abs(current_mtimes[key] - loaded_mtimes[key]) > 1:  # 1 second tolerance
                        conflicts.append(key)
            if conflicts:
                return jsonify({
                    "error": "File conflict detected",
                    "conflicts": conflicts,
                    "action": "reload_required",
                    "message": "Files were modified externally. Please reload before saving."
                }), 409

        # Create backups with shared timestamp
        backup_dir = paths.get("backup_dir")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backups = {
            "definitions": backup_file(paths.get("tool_path"), backup_dir, timestamp),
            "templates": backup_file(paths.get("template_path"), backup_dir, timestamp),
            "internal_args": backup_file(paths.get("internal_args_path"), backup_dir, timestamp)
        }

        saved_files = []
        try:
            # 1. Save tool_definitions.py and templates (existing function)
            # skip_backup=True because we already created backups above with backup_file()
            force_rescan = str(request.args.get("force_rescan", "")).lower() in ("1", "true", "yes")
            result = save_tool_definitions(tools_data, paths, force_rescan=force_rescan, skip_backup=True)
            if "error" in result:
                raise Exception(result["error"])
            saved_files.extend(["definitions", "templates"])

            # 2. Save internal_args.json
            result = save_internal_args(internal_args, paths)
            if "error" in result:
                raise Exception(result["error"])
            saved_files.append("internal_args")

            # Cleanup old backups
            cleanup_old_backups(backup_dir, keep_count=10)

            return jsonify({
                "success": True,
                "saved": saved_files,
                "backups": backups,
                "timestamp": timestamp,
                "profile": profile or list_profile_names()[0] if list_profile_names() else "default"
            })

        except Exception as e:
            # Rollback: restore from backups
            for key, backup_path in backups.items():
                if backup_path and os.path.exists(backup_path):
                    target_key = {
                        "definitions": "tool_path",
                        "templates": "template_path",
                        "internal_args": "internal_args_path"
                    }.get(key)
                    if target_key and paths.get(target_key):
                        try:
                            shutil.copy2(backup_path, paths[target_key])
                        except Exception as restore_error:
                            print(f"Warning: Could not restore {key}: {restore_error}")

            return jsonify({
                "error": str(e),
                "rolled_back": saved_files,
                "action": "all_files_restored"
            }), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# MCP Server Control API Endpoints
@app.route('/api/server/status', methods=['GET'])
def get_server_status():
    """Check if MCP server is running"""
    try:
        from mcp_server_manager import MCPServerManager

        profile = request.args.get("profile", "default")
        manager = MCPServerManager(profile)
        result = manager.status()

        return jsonify(result)
    except Exception as e:
        return jsonify({'running': False, 'error': str(e)})


@app.route('/api/server/start', methods=['POST'])
def start_server():
    """Start the MCP server"""
    try:
        from mcp_server_manager import MCPServerManager

        profile = request.args.get("profile", "default")
        manager = MCPServerManager(profile)
        result = manager.start()

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/server/stop', methods=['POST'])
def stop_server():
    """Stop the MCP server"""
    try:
        from mcp_server_manager import MCPServerManager

        profile = request.args.get("profile", "default")
        force = request.json.get("force", False) if request.json else False
        manager = MCPServerManager(profile)
        result = manager.stop(force=force)

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/server/restart', methods=['POST'])
def restart_server():
    """Restart the MCP server"""
    try:
        from mcp_server_manager import MCPServerManager

        profile = request.args.get("profile", "default")
        manager = MCPServerManager(profile)
        result = manager.restart()

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/server/logs', methods=['GET'])
def get_server_logs():
    """Get MCP server logs"""
    try:
        from mcp_server_manager import MCPServerManager

        profile = request.args.get("profile", "default")
        lines = int(request.args.get("lines", 50))
        manager = MCPServerManager(profile)
        logs = manager.logs(lines=lines)

        return jsonify({
            'success': True,
            'logs': logs,
            'profile': profile
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# Serve static files (CSS, JS)
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory(os.path.join(BASE_DIR, 'static'), path)


if __name__ == '__main__':
    print("Starting MCP Tool Editor Web Interface...")
    profile_name = os.environ.get("MCP_EDITOR_MODULE")
    profile_conf = get_profile_config(profile_name)
    paths = resolve_paths(profile_conf)
    ensure_dirs(paths)
    host = paths.get("host", "127.0.0.1")
    port = paths.get("port", 8091)
    print(f"Active profile: {profile_name or '_default'}")
    print(f"Access the editor at: http://{host}:{port}")
    print("Press Ctrl+C to stop the server")
    app.run(debug=True, host=host, port=port)
