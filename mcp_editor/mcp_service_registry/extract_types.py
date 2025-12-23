#!/usr/bin/env python3
"""
Extract property definitions from outlook_types.py (supports multiple files via config)
for the MCP tool editor.
"""

import ast
import json
import os
import sys
from typing import Dict, List, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    # Resolve relative to mcp_editor directory, not mcp_service_registry
    editor_dir = os.path.dirname(BASE_DIR)
    return os.path.normpath(os.path.join(editor_dir, path))


def _get_config_path() -> str:
    env_path = os.environ.get("MCP_EDITOR_CONFIG")
    if env_path:
        return _resolve_path(env_path)

    module_name = os.environ.get("MCP_EDITOR_MODULE")
    if module_name:
        candidate = os.path.join(BASE_DIR, f"editor_config.{module_name}.json")
        if os.path.exists(candidate):
            return candidate

    return os.path.join(os.path.dirname(BASE_DIR), "editor_config.json")


def load_graph_type_paths() -> List[str]:
    config_path = _get_config_path()
    default_paths = ["/home/kimghw/Connector_auth/mcp_outlook/outlook_types.py"]
    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # multi-profile - check first profile if no _default
                    if any(isinstance(v, dict) for v in data.values()):
                        # Try _default first, then first profile with types_files
                        profile = data.get("_default")

                        # If no _default or _default has no types, find first profile with types
                        if not profile or not (profile.get("types_files") or profile.get("graph_types_files")):
                            for profile_data in data.values():
                                if isinstance(profile_data, dict):
                                    if profile_data.get("types_files") or profile_data.get("graph_types_files"):
                                        profile = profile_data
                                        break

                        if isinstance(profile, dict):
                            # Support both types_files (new) and graph_types_files (legacy)
                            if isinstance(profile.get("types_files"), list) and profile["types_files"]:
                                return [_resolve_path(p) for p in profile["types_files"]]
                            elif isinstance(profile.get("graph_types_files"), list) and profile["graph_types_files"]:
                                return [_resolve_path(p) for p in profile["graph_types_files"]]

                    # legacy single profile
                    if isinstance(data.get("types_files"), list):
                        return [_resolve_path(p) for p in data["types_files"]]
                    elif isinstance(data.get("graph_types_files"), list):
                        return [_resolve_path(p) for p in data["graph_types_files"]]
    except Exception as e:
        print(f"Warning: could not load editor config: {e}")
    return [_resolve_path(p) for p in default_paths]


def extract_type_from_annotation(annotation) -> str:
    """Extract type string from AST annotation node"""
    if annotation is None:
        return "any"

    # Handle Optional[T]
    if isinstance(annotation, ast.Subscript):
        if hasattr(annotation.value, 'id') and annotation.value.id == 'Optional':
            if isinstance(annotation.slice, ast.Name):
                inner_type = annotation.slice.id
            else:
                inner_type = extract_type_from_annotation(annotation.slice)
            return map_python_to_json_type(inner_type)

        # Handle List[T]
        elif hasattr(annotation.value, 'id') and annotation.value.id == 'List':
            return "array"

        # Handle Union types
        elif hasattr(annotation.value, 'id') and annotation.value.id == 'Union':
            # For Union, we'll just use the first non-None type
            if isinstance(annotation.slice, ast.Tuple):
                for elt in annotation.slice.elts:
                    if isinstance(elt, ast.Name) and elt.id != 'None':
                        return map_python_to_json_type(elt.id)
            return "any"

        # Handle Literal types
        elif hasattr(annotation.value, 'id') and annotation.value.id == 'Literal':
            return "string"  # Literals are typically string enums

    # Handle simple types
    elif isinstance(annotation, ast.Name):
        return map_python_to_json_type(annotation.id)

    elif isinstance(annotation, ast.Constant):
        return map_python_to_json_type(type(annotation.value).__name__)

    return "any"


def map_python_to_json_type(python_type: str) -> str:
    """Map Python type to JSON Schema type"""
    type_mapping = {
        'str': 'string',
        'int': 'integer',
        'float': 'number',
        'bool': 'boolean',
        'list': 'array',
        'dict': 'object',
        'List': 'array',
        'Dict': 'object',
        'Any': 'any',
        'None': 'null',
        'Optional': 'any',
        'FilterParams': 'object',
        'ExcludeParams': 'object',
        'SelectParams': 'object'
    }
    return type_mapping.get(python_type, 'string')


def extract_field_info(node: ast.AnnAssign, class_name: str) -> Optional[Dict[str, Any]]:
    """Extract field information from a Field assignment"""
    if not isinstance(node.target, ast.Name):
        return None

    field_name = node.target.id
    field_info = {
        'name': field_name,
        'type': extract_type_from_annotation(node.annotation),
        'description': '',
        'examples': [],
        'default': None,
        'class': class_name
    }

    # Extract Field() parameters
    if isinstance(node.value, ast.Call):
        if hasattr(node.value.func, 'id') and node.value.func.id == 'Field':
            # Process Field arguments
            for i, arg in enumerate(node.value.args):
                if i == 0:  # First positional arg is default value
                    if isinstance(arg, ast.Constant):
                        field_info['default'] = arg.value

            # Process keyword arguments
            for keyword in node.value.keywords:
                if keyword.arg == 'description' and isinstance(keyword.value, ast.Constant):
                    field_info['description'] = keyword.value.value
                elif keyword.arg == 'examples' and isinstance(keyword.value, ast.List):
                    examples = []
                    for elt in keyword.value.elts:
                        if isinstance(elt, ast.Constant):
                            examples.append(elt.value)
                        elif isinstance(elt, ast.List):
                            # Handle list of lists
                            inner_list = []
                            for inner_elt in elt.elts:
                                if isinstance(inner_elt, ast.Constant):
                                    inner_list.append(inner_elt.value)
                            if inner_list:
                                examples.append(inner_list)
                    field_info['examples'] = examples
                elif keyword.arg == 'default' and isinstance(keyword.value, ast.Constant):
                    field_info['default'] = keyword.value.value

    return field_info


def extract_class_properties(file_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """Extract properties from Pydantic model classes"""
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())

    classes_info = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check if it's a BaseModel subclass
            is_base_model = False
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == 'BaseModel':
                    is_base_model = True
                    break

            if is_base_model:
                class_properties = []

                # Extract field definitions
                for item in node.body:
                    if isinstance(item, ast.AnnAssign):
                        field_info = extract_field_info(item, node.name)
                        if field_info and not field_info['name'].startswith('_'):
                            # Skip private/internal fields
                            class_properties.append(field_info)

                classes_info[node.name] = class_properties

    return classes_info


def _infer_server_name_from_paths(paths: List[str]) -> Optional[str]:
    if not paths:
        return None
    base_dir = os.path.basename(os.path.dirname(paths[0]))
    if base_dir.startswith('mcp_'):
        base_dir = base_dir[4:]
    return base_dir or None


def main(
    server_name: Optional[str] = None,
    output_dir: Optional[str] = None,
    graph_type_paths: Optional[List[str]] = None
):
    """
    Extract types and save to JSON file

    Args:
        server_name: Server name for output file (default: from config or 'default')
        output_dir: Output directory (default: MCPMetaRegistry folder)
    """
    if graph_type_paths:
        graph_type_paths = [_resolve_path(p) for p in graph_type_paths]
    else:
        graph_type_paths = load_graph_type_paths()
    if not graph_type_paths:
        print("Error: No graph_types paths configured")
        return

    # Determine server name
    if not server_name:
        server_name = _infer_server_name_from_paths(graph_type_paths)
    if not server_name:
        server_name = os.environ.get("MCP_EDITOR_MODULE", "default")

    merged_properties: Dict[str, List[Dict[str, Any]]] = {}

    for path in graph_type_paths:
        if not os.path.exists(path):
            print(f"Warning: graph_types file not found: {path}")
            continue
        props = extract_class_properties(path)
        for class_name, class_props in props.items():
            if class_name not in merged_properties:
                merged_properties[class_name] = []
            # Merge properties, prefer first occurrence if duplicates by name
            existing_names = {p['name'] for p in merged_properties[class_name]}
            for prop in class_props:
                if prop['name'] in existing_names:
                    continue
                merged_properties[class_name].append(prop)

    # Create structured output
    output = {
        'classes': [],
        'properties_by_class': merged_properties,
        'all_properties': []
    }

    for class_name, props in merged_properties.items():
        output['classes'].append({
            'name': class_name,
            'property_count': len(props)
        })
        for prop in props:
            output['all_properties'].append({
                'name': prop['name'],
                'type': prop['type'],
                'description': prop['description'],
                'class': class_name,
                'full_path': f"{class_name}.{prop['name']}",
                'examples': prop.get('examples', [])
            })

    # Determine output path
    if output_dir:
        base_dir = output_dir
    else:
        # Default to MCPMetaRegistry folder
        base_dir = os.path.dirname(__file__)

    # Generate filename with server name
    filename = f"types_property_{server_name}.json"
    output_path = os.path.join(base_dir, filename)

    # Save to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Extracted {len(output['all_properties'])} properties from {len(output['classes'])} classes")
    print(f"Server: {server_name}")
    print(f"Saved to: {output_path}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Extract Pydantic types to JSON")
    parser.add_argument(
        "--server-name",
        type=str,
        help="Server name for output file (default: from config or 'default')"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory (default: MCPMetaRegistry folder)"
    )
    parser.add_argument(
        "types_files",
        nargs="*",
        help="Optional types files to parse (overrides config)"
    )

    args = parser.parse_args()
    graph_type_paths = args.types_files if args.types_files else None
    main(server_name=args.server_name, output_dir=args.output_dir, graph_type_paths=graph_type_paths)
