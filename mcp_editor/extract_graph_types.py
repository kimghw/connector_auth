#!/usr/bin/env python3
"""
Extract properties from Python type definition files (e.g., outlook_types.py)
for use in the MCP Editor's Add Property feature.
"""

import os
import sys
import json
import ast
import inspect
from typing import Dict, List, Set, Any
import importlib.util


def extract_class_properties(file_path: str) -> Dict[str, Any]:
    """Extract BaseModel class properties from a Python file"""

    result = {
        "classes": [],
        "properties_by_class": {},
        "all_properties": []
    }

    try:
        # Parse the Python file
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=file_path)

        all_properties_set = set()

        # Find all class definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name

                # Check if it's a Pydantic BaseModel
                is_pydantic = False
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == 'BaseModel':
                        is_pydantic = True
                        break
                    elif isinstance(base, ast.Attribute) and base.attr == 'BaseModel':
                        is_pydantic = True
                        break

                if is_pydantic:
                    result["classes"].append(class_name)
                    class_props = []

                    # Extract properties from class body
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            prop_name = item.target.id
                            if not prop_name.startswith('_'):  # Skip private properties
                                class_props.append(prop_name)
                                all_properties_set.add(prop_name)

                    if class_props:
                        result["properties_by_class"][class_name] = sorted(class_props)

        # Sort results
        result["classes"] = sorted(result["classes"])
        result["all_properties"] = sorted(list(all_properties_set))

    except Exception as e:
        print(f"Error extracting from {file_path}: {e}", file=sys.stderr)

    return result


def merge_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge results from multiple files"""

    merged = {
        "classes": [],
        "properties_by_class": {},
        "all_properties": []
    }

    all_classes_set = set()
    all_properties_set = set()

    for result in results:
        all_classes_set.update(result.get("classes", []))
        all_properties_set.update(result.get("all_properties", []))

        # Merge properties_by_class
        for class_name, props in result.get("properties_by_class", {}).items():
            if class_name not in merged["properties_by_class"]:
                merged["properties_by_class"][class_name] = []
            # Merge and deduplicate properties
            existing_props = set(merged["properties_by_class"][class_name])
            existing_props.update(props)
            merged["properties_by_class"][class_name] = sorted(list(existing_props))

    merged["classes"] = sorted(list(all_classes_set))
    merged["all_properties"] = sorted(list(all_properties_set))

    return merged


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python extract_graph_types.py <types_file1> [types_file2 ...]", file=sys.stderr)
        sys.exit(1)

    types_files = sys.argv[1:]
    results = []

    for file_path in types_files:
        if os.path.exists(file_path):
            print(f"Extracting from: {file_path}", file=sys.stderr)
            result = extract_class_properties(file_path)
            if result["classes"]:  # Only add if we found classes
                results.append(result)
        else:
            print(f"File not found: {file_path}", file=sys.stderr)

    # Merge all results
    if results:
        merged = merge_results(results)
    else:
        merged = {
            "classes": [],
            "properties_by_class": {},
            "all_properties": []
        }

    # Determine output path based on the first types file
    if types_files:
        first_file = types_files[0]
        # Extract server name from path (e.g., ../mcp_outlook/outlook_types.py -> outlook)
        dir_name = os.path.dirname(first_file)
        base_name = os.path.basename(dir_name)

        if base_name.startswith('mcp_'):
            server_name = base_name[4:]  # Remove 'mcp_' prefix
        else:
            server_name = base_name

        # Save to mcp_service_registry with new naming convention
        output_dir = os.path.join(os.path.dirname(__file__), 'mcp_service_registry')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f'types_property_{server_name}.json')
    else:
        # Fallback path
        output_path = os.path.join(os.path.dirname(__file__), 'types_properties.json')

    # Write the output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2)

    print(f"Properties extracted to: {output_path}", file=sys.stderr)
    print(f"Found {len(merged['classes'])} classes with {len(merged['all_properties'])} unique properties", file=sys.stderr)


if __name__ == "__main__":
    main()