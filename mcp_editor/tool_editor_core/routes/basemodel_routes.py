"""
BaseModel Routes

BaseModel 스키마 API 엔드포인트:
- GET /api/basemodels
- GET /api/graph-types-properties
- POST /api/tools/<int>/apply-basemodel
"""

import os
import sys
import json
from flask import request, jsonify

from . import basemodel_bp
from ..config import (
    BASE_DIR,
    get_profile_config,
    resolve_paths,
)
from ..tool_loader import load_tool_definitions
from ..tool_saver import save_tool_definitions
from tool_editor_web_server_mappings import get_server_name_from_profile
from pydantic_to_schema import (
    generate_mcp_schemas_from_graph_types,
    update_tool_with_basemodel_schema,
    load_graph_types_models,
)


@basemodel_bp.route("/api/graph-types-properties", methods=["GET"])
def get_graph_types_properties():
    """Get available properties from types files for the current profile"""
    try:
        profile = request.args.get("profile")
        profile_conf = get_profile_config(profile)
        paths = resolve_paths(profile_conf)

        types_files = paths.get("types_files", [])

        # If no types_files configured, return empty with a flag
        if not types_files:
            return jsonify(
                {"classes": [], "properties_by_class": {}, "all_properties": [], "has_types": False, "types_name": None}
            )

        # Get server name for display
        server_name = get_server_name_from_profile(profile) or "types"

        # Try to load from cached properties file for this profile
        profile_name = profile or "default"

        # Try new naming convention in mcp_service_registry folder first
        registry_path = os.path.join(BASE_DIR, "mcp_service_registry", f"types_property_{server_name}.json")

        # Then try profile-specific path
        if not os.path.exists(registry_path):
            properties_path = os.path.join(BASE_DIR, profile_name, "types_properties.json")
        else:
            properties_path = registry_path

        # Fallback to legacy path
        if not os.path.exists(properties_path):
            properties_path = os.path.join(BASE_DIR, "types_properties.json")

        if os.path.exists(properties_path):
            with open(properties_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["has_types"] = True
                # Remove 'mcp_' prefix from server_name for types file
                types_file_name = (
                    server_name.replace("mcp_", "") if server_name and server_name.startswith("mcp_") else server_name
                )
                data["types_name"] = f"{types_file_name}_types"
                return jsonify(data)
        else:
            # Try to generate using extract script
            import subprocess

            extract_script = os.path.join(BASE_DIR, "mcp_service_registry", "extract_types.py")
            if os.path.exists(extract_script):
                # Pass types files and server name so output matches the active profile
                cmd = [sys.executable, extract_script, "--server-name", server_name] + types_files
                subprocess.run(cmd, check=True)
                if os.path.exists(registry_path):
                    properties_path = registry_path
                if os.path.exists(properties_path):
                    with open(properties_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        data["has_types"] = True
                        # Remove 'mcp_' prefix from server_name for types file
                        types_file_name = (
                            server_name.replace("mcp_", "")
                            if server_name and server_name.startswith("mcp_")
                            else server_name
                        )
                        data["types_name"] = f"{types_file_name}_types"
                        return jsonify(data)

        # Remove 'mcp_' prefix from server_name for types file
        types_file_name = (
            server_name.replace("mcp_", "") if server_name and server_name.startswith("mcp_") else server_name
        )
        return jsonify(
            {
                "classes": [],
                "properties_by_class": {},
                "all_properties": [],
                "has_types": bool(types_files),
                "types_name": f"{types_file_name}_types" if types_files else None,
            }
        )
    except Exception as e:
        return (
            jsonify(
                {"error": str(e), "classes": [], "properties_by_class": {}, "all_properties": [], "has_types": False}
            ),
            500,
        )


@basemodel_bp.route("/api/basemodels", methods=["GET"])
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
            result.append({"name": name, "description": model.__doc__ or f"{name} BaseModel", "schema": schema})

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@basemodel_bp.route("/api/tools/<int:tool_index>/apply-basemodel", methods=["POST"])
def apply_basemodel_to_property(tool_index):
    """Apply a BaseModel schema to a specific property of a tool"""
    try:
        profile = request.args.get("profile")
        profile_conf = get_profile_config(profile)
        paths = resolve_paths(profile_conf)
        graph_type_paths = paths.get("types_files")

        data = request.json
        property_name = data.get("property_name")
        basemodel_name = data.get("basemodel_name")

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
