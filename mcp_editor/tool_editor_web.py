"""
Web interface for editing MCP Tool Definitions
"""
import json
import os
import sys
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

# Import MCP service extractor
from mcp_service_extractor import get_signatures_by_name

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
CONFIG_PATH = os.path.join(BASE_DIR, 'editor_config.json')
DEFAULT_PROFILE = {
    "template_definitions_path": "tool_definition_templates.py",
    "tool_definitions_path": "../outlook_mcp/mcp_server/tool_definitions.py",
    "backup_dir": "backups",
    "graph_types_files": ["../outlook_mcp/graph_types.py"],
    "host": "127.0.0.1",
    "port": 8091
}

JINJA_DIR = os.path.join(ROOT_DIR, 'jinja')
DEFAULT_SERVER_TEMPLATE = os.path.join(JINJA_DIR, 'server_template.jinja2')
GENERATOR_SCRIPT_PATH = os.path.join(JINJA_DIR, 'generate_server.py')


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


def _load_config_file():
    config_path = _get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load editor_config.json: {e}")
    else:
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
    return ["_default"]


def get_profile_config(profile_name: str | None = None) -> dict:
    data = _load_config_file()
    # legacy single-profile dict
    if isinstance(data, dict) and all(not isinstance(v, dict) for v in data.values()):
        return _merge_profile({}, data)

    if isinstance(data, dict):
        default_profile = data.get("_default", {})
        selected = data.get(profile_name) if profile_name else None
        return _merge_profile(default_profile, selected)

    return DEFAULT_PROFILE.copy()


def resolve_paths(profile_conf: dict) -> dict:
    return {
        "template_path": _resolve_path(profile_conf["template_definitions_path"]),
        "tool_path": _resolve_path(profile_conf["tool_definitions_path"]),
        "backup_dir": _resolve_path(profile_conf["backup_dir"]),
        "graph_types_files": profile_conf.get("graph_types_files", ["../outlook_mcp/graph_types.py"]),
        "host": profile_conf.get("host", "127.0.0.1"),
        "port": profile_conf.get("port", 8091)
    }


def _default_generator_paths(profile_conf: dict) -> dict:
    """Return default generator paths for the active profile"""
    resolved = resolve_paths(profile_conf)
    output_dir = os.path.dirname(resolved["tool_path"])
    output_path = os.path.join(output_dir, 'server_generated.py')

    return {
        "tools_path": resolved["template_path"],
        "template_path": DEFAULT_SERVER_TEMPLATE if os.path.exists(DEFAULT_SERVER_TEMPLATE) else "",
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

            tools_candidates = [
                os.path.join(mcp_dir, "tool_definition_templates.py"),
                os.path.join(mcp_dir, "tool_definitions.py"),
                fallback["tools_path"]
            ]
            tools_path = next((p for p in tools_candidates if p and os.path.exists(p)), fallback["tools_path"])

            modules.append({
                "name": entry,
                "mcp_dir": mcp_dir,
                "tools_path": tools_path,
                "template_path": fallback["template_path"],
                "output_path": os.path.join(mcp_dir, "server_generated.py")
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


def save_tool_definitions(tools_data, paths: dict):
    """Save MCP_TOOLS to both tool_definitions.py and tool_definition_templates.py"""
    try:
        ensure_dirs(paths)
        # Create backup first
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
                cleaned_tool['description'] = tool['description']
            if 'inputSchema' in tool:
                # Remove defaults for the public definitions and order schema
                cleaned_input = copy.deepcopy(tool['inputSchema'])
                cleaned_input = remove_defaults(cleaned_input)
                cleaned_tool['inputSchema'] = order_schema_fields(cleaned_input)
            # Add any other fields except mcp_service and mcp_service_factors
            for k, v in tool.items():
                if k not in ['name', 'description', 'inputSchema', 'mcp_service', 'mcp_service_factors']:
                    cleaned_tool[k] = v
            cleaned_tools.append(cleaned_tool)

        # Generate tool_definitions.py content
        content = '''"""
MCP Tool Definitions for Outlook Graph Mail Server - AUTO-GENERATED FILE
DO NOT EDIT THIS FILE MANUALLY!

This file is automatically generated when you save changes in the MCP Tool Editor.
It contains clean tool definitions for use with Claude/OpenAI APIs.
Internal metadata fields (mcp_service, mcp_service_factors) are removed.

Generated from: MCP Tool Editor Web Interface
To modify: Use the web editor at http://localhost:8091
"""

from typing import List, Dict, Any

# MCP Tool Definitions
MCP_TOOLS: List[Dict[str, Any]] = '''

        # Format the tools data nicely
        formatted_tools = json.dumps(cleaned_tools, indent=4, ensure_ascii=False)
        content += formatted_tools

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
        server_name = get_server_name_from_path(paths.get("tool_path", ""))

        # Extract signatures from source code using AST
        signatures_by_name = {}
        if server_name:
            module_patterns = [
                os.path.join(ROOT_DIR, f'mcp_{server_name}'),
                os.path.join(ROOT_DIR, f'{server_name}_mcp'),
            ]
            scan_dir = next((p for p in module_patterns if os.path.isdir(p)), None)

            if scan_dir:
                signatures_by_name = get_signatures_by_name(scan_dir, server_name)
                print(f"Extracted {len(signatures_by_name)} signatures from source code")

        # Build template tools
        template_tools = []
        for tool in tools_data:
            template_tool = {k: v for k, v in tool.items()}
            if 'inputSchema' in template_tool:
                template_tool['inputSchema'] = order_schema_fields(template_tool['inputSchema'])

            # Add signature if available
            if 'mcp_service' in template_tool and isinstance(template_tool['mcp_service'], dict):
                service_name = template_tool['mcp_service'].get('name')
                if service_name and service_name in signatures_by_name:
                    template_tool['mcp_service']['signature'] = signatures_by_name[service_name]

            template_tools.append(template_tool)

        # Write template file
        template_filename = f'tool_definition_{server_name}_templates.py' if server_name else 'tool_definition_templates.py'
        template_path = os.path.join(os.path.dirname(__file__), template_filename)

        template_content = f'''"""
MCP Tool Definition Templates - AUTO-GENERATED
Signatures extracted from source code using AST parsing
"""
from typing import List, Dict, Any

MCP_TOOLS: List[Dict[str, Any]] = {json.dumps(template_tools, indent=4, ensure_ascii=False)}
'''

        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)

        print(f"Saved template to: {template_filename}")

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
    """API endpoint to get current tool definitions"""
    profile = request.args.get("profile")
    profile_conf = get_profile_config(profile)
    paths = resolve_paths(profile_conf)
    tools = load_tool_definitions(paths)
    if isinstance(tools, dict) and "error" in tools:
        return jsonify(tools), 500
    return jsonify({"tools": tools, "profile": profile or "_default"})


@app.route('/api/tools', methods=['POST'])
def save_tools():
    """API endpoint to save tool definitions"""
    try:
        profile = request.args.get("profile")
        profile_conf = get_profile_config(profile)
        paths = resolve_paths(profile_conf)
        tools_data = request.json
        result = save_tool_definitions(tools_data, paths)
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
        result = save_tool_definitions(tools, paths)
        if "error" in result:
            return jsonify(result), 500

        return jsonify({
            "success": True,
            "message": f"Tool '{tool_name}' deleted successfully",
            "backup": result.get("backup")
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
        profile = request.args.get('profile', 'outlook')

        # Determine server name from profile using mappings
        server_name = get_server_name_from_profile(profile)

        # Try server-specific file first
        mcp_services_path = None
        if server_name:
            specific_path = os.path.join(os.path.dirname(__file__), f'{server_name}_mcp_services.json')
            if os.path.exists(specific_path):
                mcp_services_path = specific_path
                print(f"Loading services from {server_name}_mcp_services.json")

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


@app.route('/api/profiles', methods=['GET'])
def get_profiles():
    """List available profiles from editor_config.json"""
    try:
        profiles = list_profile_names()
        active = request.args.get("profile") or os.environ.get("MCP_EDITOR_MODULE") or "_default"
        return jsonify({"profiles": profiles, "active": active})
    except Exception as e:
        return jsonify({"error": str(e), "profiles": []}), 500


@app.route('/api/server-generator/defaults', methods=['GET'])
def get_server_generator_defaults():
    """Expose detected modules and default paths for the Jinja2 server generator"""
    try:
        profile = request.args.get("profile")
        profile_conf = get_profile_config(profile)
        modules = discover_mcp_modules(profile_conf)
        fallback = _default_generator_paths(profile_conf)

        return jsonify({
            "modules": modules,
            "fallback": fallback
        })
    except Exception as e:
        return jsonify({"error": str(e), "modules": [], "fallback": {}}), 500


@app.route('/api/graph-types-properties', methods=['GET'])
def get_graph_types_properties():
    """Get available properties from outlook_types.py"""
    try:
        properties_path = os.path.join(os.path.dirname(__file__), 'types_properties.json')
        if os.path.exists(properties_path):
            with open(properties_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return jsonify(data)
        else:
            # Try to generate if not exists
            import subprocess
            extract_script = os.path.join(os.path.dirname(__file__), 'extract_graph_types.py')
            if os.path.exists(extract_script):
                subprocess.run([sys.executable, extract_script], check=True)
                if os.path.exists(properties_path):
                    with open(properties_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return jsonify(data)
        return jsonify({"classes": [], "properties_by_class": {}, "all_properties": []})
    except Exception as e:
        return jsonify({"error": str(e), "classes": [], "properties_by_class": {}, "all_properties": []}), 500


@app.route('/api/basemodels', methods=['GET'])
def get_basemodels():
    """Get available BaseModel schemas from outlook_types.py"""
    try:
        profile = request.args.get("profile")
        profile_conf = get_profile_config(profile)
        paths = resolve_paths(profile_conf)
        graph_type_paths = paths.get("graph_types_files")

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
        graph_type_paths = paths.get("graph_types_files")

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
        result = save_tool_definitions(tools, paths)
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
        defaults = _default_generator_paths(profile_conf)

        data = request.json or {}
        module_name = data.get("module")
        selected_module = next((m for m in modules if m.get("name") == module_name), None)

        tools_path = data.get("tools_path") or (selected_module["tools_path"] if selected_module else defaults["tools_path"])
        template_path = data.get("template_path") or (selected_module["template_path"] if selected_module else defaults["template_path"])
        output_path = data.get("output_path") or (selected_module["output_path"] if selected_module else defaults["output_path"])

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


# Serve static files (CSS, JS)
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


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
