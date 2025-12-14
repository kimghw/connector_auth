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

# Path to tool definitions file
TOOL_DEFINITIONS_PATH = os.path.join(os.path.dirname(__file__), 'tool_definitions.py')
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')

# Create backup directory if it doesn't exist
os.makedirs(BACKUP_DIR, exist_ok=True)


def load_tool_definitions():
    """Load MCP_TOOLS from tool_definitions.py"""
    try:
        spec = importlib.util.spec_from_file_location("tool_definitions", TOOL_DEFINITIONS_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.MCP_TOOLS
    except Exception as e:
        return {"error": str(e)}


def save_tool_definitions(tools_data):
    """Save MCP_TOOLS back to tool_definitions.py"""
    try:
        # Create backup first
        backup_filename = f"tool_definitions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        shutil.copy2(TOOL_DEFINITIONS_PATH, backup_path)

        # Generate new file content
        content = '''"""
MCP Tool Definitions for Outlook Graph Mail Server
Contains all tool schemas and definitions for the MCP protocol
"""

from typing import List, Dict, Any

# MCP Tool Definitions
MCP_TOOLS: List[Dict[str, Any]] = '''

        # Format the tools data nicely
        formatted_tools = json.dumps(tools_data, indent=4, ensure_ascii=False)
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

        # Write to file
        with open(TOOL_DEFINITIONS_PATH, 'w', encoding='utf-8') as f:
            f.write(content)

        return {"success": True, "backup": backup_filename}
    except Exception as e:
        return {"error": str(e)}


@app.route('/')
def index():
    """Main editor page"""
    return render_template('tool_editor.html')


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
    print("Access the editor at: http://localhost:8080")
    print("Press Ctrl+C to stop the server")
    app.run(debug=True, host='0.0.0.0', port=8080)