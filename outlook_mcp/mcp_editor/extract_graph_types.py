#!/usr/bin/env python3
"""
Extract property definitions from graph_types.py for the MCP tool editor
"""

import ast
import json
import os
import sys
from typing import Dict, List, Any, Optional

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)


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

            if is_base_model and node.name in ['FilterParams', 'ExcludeParams', 'SelectParams']:
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


def main():
    # Path to graph_types.py
    graph_types_path = os.path.join(parent_dir, 'graph_types.py')

    if not os.path.exists(graph_types_path):
        print(f"Error: {graph_types_path} not found")
        return

    # Extract properties
    properties = extract_class_properties(graph_types_path)

    # Create structured output
    output = {
        'classes': [],
        'properties_by_class': properties,
        'all_properties': []
    }

    # Add class list
    for class_name in properties:
        output['classes'].append({
            'name': class_name,
            'property_count': len(properties[class_name])
        })

    # Combine all properties with class prefix
    for class_name, props in properties.items():
        for prop in props:
            output['all_properties'].append({
                'name': prop['name'],
                'type': prop['type'],
                'description': prop['description'],
                'class': class_name,
                'full_path': f"{class_name}.{prop['name']}",
                'examples': prop.get('examples', [])
            })

    # Save to JSON file
    output_path = os.path.join(os.path.dirname(__file__), 'graph_types_properties.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Extracted {len(output['all_properties'])} properties from {len(output['classes'])} classes")
    print(f"Saved to: {output_path}")

    # Print summary
    for class_info in output['classes']:
        print(f"  - {class_info['name']}: {class_info['property_count']} properties")


if __name__ == '__main__':
    main()