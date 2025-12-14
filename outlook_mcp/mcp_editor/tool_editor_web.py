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

app = Flask(__name__)
CORS(app)

# Path to tool definitions file in mcp_server directory
TOOL_DEFINITIONS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mcp_server', 'tool_definitions.py')
# Path to template definitions (includes internal metadata)
TEMPLATE_DEFINITIONS_PATH = os.path.join(os.path.dirname(__file__), 'tool_definition_templates.py')
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')

# Create backup directory if it doesn't exist
os.makedirs(BACKUP_DIR, exist_ok=True)


def load_tool_definitions():
    """
    Load MCP_TOOLS, preferring the template file (with mcp_service metadata)
    so the editor displays the full structure. Falls back to cleaned definitions.
    """
    try:
        # Try loading from templates first
        if os.path.exists(TEMPLATE_DEFINITIONS_PATH):
            spec = importlib.util.spec_from_file_location("tool_definition_templates", TEMPLATE_DEFINITIONS_PATH)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.MCP_TOOLS

        # Fallback to cleaned definitions
        spec = importlib.util.spec_from_file_location("tool_definitions", TOOL_DEFINITIONS_PATH)
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


def save_tool_definitions(tools_data):
    """Save MCP_TOOLS to both tool_definitions.py and tool_definition_templates.py"""
    try:
        # Create backup first
        backup_filename = f"tool_definitions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        shutil.copy2(TOOL_DEFINITIONS_PATH, backup_path)

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
        with open(TOOL_DEFINITIONS_PATH, 'w', encoding='utf-8') as f:
            f.write(content)

        # 2. Save tool_definition_templates.py (with all metadata)
        template_path = os.path.join(os.path.dirname(__file__), 'tool_definition_templates.py')

        # Load signature information from mcp_services.json
        signatures_by_name = {}
        try:
            services_json_path = os.path.join(os.path.dirname(__file__), 'mcp_services.json')
            with open(services_json_path, 'r', encoding='utf-8') as f:
                services_data = json.load(f)
                for service in services_data.get('services_with_signatures', []):
                    # Build signature string from parameters
                    param_strs = []
                    for param in service['parameters']:
                        if param['name'] == 'self':
                            continue
                        param_str = param['name']
                        if param.get('type'):
                            param_str += f": {param['type']}"
                        if param.get('default') is not None:
                            param_str += f" = {param['default']}"
                        param_strs.append(param_str)

                    # Only store the parameters part (what's inside parentheses)
                    signature = f"{', '.join(param_strs)}"
                    signatures_by_name[service['name']] = signature
        except Exception as e:
            print(f"Warning: Could not load signatures from mcp_services.json: {e}")

        # Reorder fields for templates too
        template_tools = []
        for tool in tools_data:
            # Create template tool with specific field order
            template_tool = {}
            # Add fields in desired order
            if 'name' in tool:
                template_tool['name'] = tool['name']
            if 'description' in tool:
                template_tool['description'] = tool['description']
            if 'inputSchema' in tool:
                # Use the recursive ordering function for templates too
                template_tool['inputSchema'] = order_schema_fields(tool['inputSchema'])
            if 'mcp_service' in tool:
                # Check if mcp_service is already an object or a string
                if isinstance(tool['mcp_service'], dict):
                    # Already an object, just update signature if needed
                    mcp_service_obj = tool['mcp_service'].copy()
                    service_name = mcp_service_obj.get('name', '')
                    if service_name and service_name in signatures_by_name:
                        mcp_service_obj['signature'] = signatures_by_name[service_name]
                else:
                    # String format, convert to object
                    mcp_service_obj = {
                        'name': tool['mcp_service']
                    }
                    # Add signature if we have it
                    if tool['mcp_service'] in signatures_by_name:
                        mcp_service_obj['signature'] = signatures_by_name[tool['mcp_service']]
                template_tool['mcp_service'] = mcp_service_obj
            if 'mcp_service_factors' in tool:
                template_tool['mcp_service_factors'] = tool['mcp_service_factors']
            # Add any other fields
            for k, v in tool.items():
                if k not in ['name', 'description', 'inputSchema', 'mcp_service', 'mcp_service_factors']:
                    template_tool[k] = v
            template_tools.append(template_tool)

        template_content = '''"""
MCP Tool Definition Templates - AUTO-GENERATED FILE
DO NOT EDIT THIS FILE MANUALLY!

This file is automatically generated when you save changes in the MCP Tool Editor.
It contains the full tool definitions including internal metadata fields:
- mcp_service: Object containing:
  - name: The handler function name
  - signature: The function parameters from the @mcp_service decorator
- mcp_service_factors: Internal routing and parameter mapping information

Generated from: MCP Tool Editor Web Interface
To modify: Use the web editor at http://localhost:8091
"""

from typing import List, Dict, Any

# MCP Tool Templates with service field and service factors
MCP_TOOLS: List[Dict[str, Any]] = '''

        # Format the template tools data nicely
        formatted_template_tools = json.dumps(template_tools, indent=4, ensure_ascii=False)
        template_content += formatted_template_tools

        # Write tool_definition_templates.py
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)

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
    tools = load_tool_definitions()
    if isinstance(tools, dict) and "error" in tools:
        return jsonify(tools), 500
    return jsonify(tools)


@app.route('/api/tools', methods=['POST'])
def save_tools():
    """API endpoint to save tool definitions"""
    try:
        tools_data = request.json
        result = save_tool_definitions(tools_data)
        if "error" in result:
            return jsonify(result), 500
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/tools/<int:tool_index>', methods=['DELETE'])
def delete_tool(tool_index):
    """Delete a specific tool by index"""
    try:
        # Load current tools
        tools = load_tool_definitions()
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
        result = save_tool_definitions(tools)
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
        backups = []
        for filename in os.listdir(BACKUP_DIR):
            if filename.startswith('tool_definitions_') and filename.endswith('.py'):
                file_path = os.path.join(BACKUP_DIR, filename)
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

        file_path = os.path.join(BACKUP_DIR, filename)
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

        backup_path = os.path.join(BACKUP_DIR, filename)
        if not os.path.exists(backup_path):
            return jsonify({"error": "Backup not found"}), 404

        # Create a backup of current state before restoring
        current_backup = f"tool_definitions_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        shutil.copy2(TOOL_DEFINITIONS_PATH, os.path.join(BACKUP_DIR, current_backup))

        # Restore the backup
        shutil.copy2(backup_path, TOOL_DEFINITIONS_PATH)

        return jsonify({"success": True, "current_backup": current_backup})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/mcp-services', methods=['GET'])
def get_mcp_services():
    """Get available MCP services from mcp_services.json"""
    try:
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


@app.route('/api/graph-types-properties', methods=['GET'])
def get_graph_types_properties():
    """Get available properties from graph_types.py"""
    try:
        properties_path = os.path.join(os.path.dirname(__file__), 'graph_types_properties.json')
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
    """Get available BaseModel schemas from graph_types.py"""
    try:
        models = load_graph_types_models()
        schemas = generate_mcp_schemas_from_graph_types()

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
        data = request.json
        property_name = data.get('property_name')
        basemodel_name = data.get('basemodel_name')

        if not property_name or not basemodel_name:
            return jsonify({"error": "Missing property_name or basemodel_name"}), 400

        # Load current tools
        tools = load_tool_definitions()
        if isinstance(tools, dict) and "error" in tools:
            return jsonify(tools), 500

        if tool_index >= len(tools):
            return jsonify({"error": "Invalid tool index"}), 400

        # Apply BaseModel schema
        tool = tools[tool_index]
        updated_tool = update_tool_with_basemodel_schema(tool, basemodel_name, property_name)

        # Save the updated tools
        result = save_tool_definitions(tools)
        if "error" in result:
            return jsonify(result), 500

        return jsonify({"success": True, "tool": updated_tool})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Serve static files (CSS, JS)
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


if __name__ == '__main__':
    print("Starting MCP Tool Editor Web Interface...")
    print("Access the editor at: http://localhost:8091")
    print("Press Ctrl+C to stop the server")
    app.run(debug=True, host='0.0.0.0', port=8091)
