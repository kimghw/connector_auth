#!/usr/bin/env python3
"""
Extract all functions decorated with @mcp_service from the actual codebase
"""

import ast
import os
import json
from pathlib import Path
from typing import List, Dict, Any

def find_mcp_service_functions(file_path: str) -> List[Dict[str, Any]]:
    """Find all functions decorated with @mcp_service in a Python file"""
    services = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check if function has @mcp_service decorator
                for decorator in node.decorator_list:
                    decorator_name = None

                    # Handle simple decorator: @mcp_service
                    if isinstance(decorator, ast.Name):
                        decorator_name = decorator.id
                    # Handle decorator with args: @mcp_service(...)
                    elif isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name):
                            decorator_name = decorator.func.id

                    if decorator_name == 'mcp_service':
                        # Get line number
                        lineno = node.lineno

                        # Extract function info
                        service_info = {
                            'function_name': node.name,
                            'file': str(file_path),
                            'line': lineno,
                            'is_async': isinstance(node, ast.AsyncFunctionDef),
                            'parameters': []
                        }

                        # Extract function parameters
                        args = node.args
                        param_list = []

                        # Regular arguments
                        for i, arg in enumerate(args.args):
                            param = {
                                'name': arg.arg,
                                'type': None,
                                'default': None
                            }

                            # Check for type annotation
                            if arg.annotation:
                                param['type'] = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else str(arg.annotation)

                            # Check for default value
                            defaults_offset = len(args.args) - len(args.defaults)
                            if i >= defaults_offset:
                                default_idx = i - defaults_offset
                                if default_idx < len(args.defaults):
                                    default_node = args.defaults[default_idx]
                                    if isinstance(default_node, ast.Constant):
                                        param['default'] = default_node.value
                                    else:
                                        param['default'] = ast.unparse(default_node) if hasattr(ast, 'unparse') else str(default_node)

                            param_list.append(param)

                        # *args
                        if args.vararg:
                            param_list.append({
                                'name': f'*{args.vararg.arg}',
                                'type': ast.unparse(args.vararg.annotation) if args.vararg.annotation and hasattr(ast, 'unparse') else None,
                                'default': None
                            })

                        # **kwargs
                        if args.kwarg:
                            param_list.append({
                                'name': f'**{args.kwarg.arg}',
                                'type': ast.unparse(args.kwarg.annotation) if args.kwarg.annotation and hasattr(ast, 'unparse') else None,
                                'default': None
                            })

                        service_info['parameters'] = param_list

                        # Try to extract decorator arguments if present
                        if isinstance(decorator, ast.Call):
                            for keyword in decorator.keywords:
                                if keyword.arg == 'tool_name' and isinstance(keyword.value, ast.Constant):
                                    service_info['tool_name'] = keyword.value.value
                                elif keyword.arg == 'description' and isinstance(keyword.value, ast.Constant):
                                    service_info['description'] = keyword.value.value
                                elif keyword.arg == 'server_name' and isinstance(keyword.value, ast.Constant):
                                    service_info['server_name'] = keyword.value.value
                                elif keyword.arg == 'category' and isinstance(keyword.value, ast.Constant):
                                    service_info['category'] = keyword.value.value
                                elif keyword.arg == 'priority' and isinstance(keyword.value, ast.Constant):
                                    service_info['priority'] = keyword.value.value
                                elif keyword.arg == 'tags' and isinstance(keyword.value, ast.List):
                                    # Extract list of tags
                                    tags = []
                                    for elt in keyword.value.elts:
                                        if isinstance(elt, ast.Constant):
                                            tags.append(elt.value)
                                    service_info['tags'] = tags

                        services.append(service_info)
                        break

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

    return services

def scan_directory(directory: str, exclude_examples: bool = True) -> List[Dict[str, Any]]:
    """Scan directory recursively for Python files with @mcp_service decorators"""
    all_services = []

    for py_file in Path(directory).rglob("*.py"):
        # Skip venv, __pycache__, and other non-source directories
        if any(part in str(py_file) for part in ['venv', '__pycache__', '.git', 'node_modules']):
            continue

        # Skip example files if requested
        if exclude_examples and 'example' in str(py_file).lower():
            print(f"Skipping example file: {py_file}")
            continue

        services = find_mcp_service_functions(str(py_file))
        if services:
            print(f"Found {len(services)} service(s) in {py_file}")
            all_services.extend(services)

    return all_services

def main(server_name=None):
    """Main function to extract and export @mcp_service decorated functions

    Args:
        server_name: Name of the server (e.g., 'outlook', 'attachment'). If not provided, tries to detect from directory.
    """

    # Determine which server to scan
    if server_name:
        base_dir = f"/home/kimghw/Connector_auth/mcp_{server_name}"
    else:
        # Default to outlook for backward compatibility
        base_dir = "/home/kimghw/Connector_auth/mcp_outlook"
        server_name = "outlook"

    print(f"Scanning for @mcp_service decorators in {base_dir}...")

    all_services = scan_directory(base_dir)

    # Sort by file and line number for consistency
    all_services.sort(key=lambda x: (x['file'], x['line']))

    # Extract just function names for simple list
    function_names = [service['function_name'] for service in all_services]

    # Prepare simple output with signatures
    services_with_signatures = []
    for service in all_services:
        service_entry = {
            "name": service['function_name'],
            "parameters": service.get('parameters', []),
            "is_async": service.get('is_async', False)
        }
        services_with_signatures.append(service_entry)

    simple_output = {
        "decorated_services": function_names,  # Keep for backward compatibility
        "services_with_signatures": services_with_signatures,  # New field with full info
        "count": len(function_names),
        "description": "List of actual functions with @mcp_service decorator in codebase with signatures"
    }

    # Prepare detailed output
    detailed_output = {
        "services": all_services,
        "count": len(all_services),
        "by_file": {},
        "description": "Detailed information about @mcp_service decorated functions"
    }

    # Group by file
    for service in all_services:
        file_path = service['file']
        if file_path not in detailed_output['by_file']:
            detailed_output['by_file'][file_path] = []
        detailed_output['by_file'][file_path].append(service['function_name'])

    # Save to mcp_editor directory with server name prefix
    mcp_editor_dir = "/home/kimghw/Connector_auth/mcp_editor"
    os.makedirs(mcp_editor_dir, exist_ok=True)

    # Save simple version with server name prefix
    simple_file = os.path.join(mcp_editor_dir, f"{server_name}_mcp_services.json")
    with open(simple_file, 'w', encoding='utf-8') as f:
        json.dump(simple_output, f, indent=2, ensure_ascii=False)
    print(f"\nSimple service list saved to: {simple_file}")

    # Save detailed version with server name prefix
    detailed_file = os.path.join(mcp_editor_dir, f"{server_name}_mcp_services_detailed.json")
    with open(detailed_file, 'w', encoding='utf-8') as f:
        json.dump(detailed_output, f, indent=2, ensure_ascii=False)
    print(f"Detailed service info saved to: {detailed_file}")

    # Also save a copy without prefix for backward compatibility (only for outlook)
    if server_name == "outlook":
        legacy_file = os.path.join(mcp_editor_dir, "mcp_services.json")
        with open(legacy_file, 'w', encoding='utf-8') as f:
            json.dump(simple_output, f, indent=2, ensure_ascii=False)
        print(f"Legacy file saved to: {legacy_file} (for backward compatibility)")

    # Print summary
    print(f"\n=== Summary ===")
    print(f"Total @mcp_service decorated functions: {len(all_services)}")

    if all_services:
        print(f"\nFunctions found:")
        for service in all_services:
            file_name = os.path.basename(service['file'])
            async_marker = "async " if service.get('is_async') else ""
            tool_info = f" -> {service['tool_name']}" if 'tool_name' in service else ""
            print(f"  - {async_marker}{service['function_name']}() in {file_name}:{service['line']}{tool_info}")
    else:
        print("No @mcp_service decorated functions found in codebase")
        print("\nNote: The @mcp_service decorator was only used in example files.")
        print("Actual service implementations might use different patterns.")

if __name__ == "__main__":
    import sys

    # Check for command line argument
    server_name = None
    if len(sys.argv) > 1:
        server_name = sys.argv[1]
        print(f"Using server name from command line: {server_name}")

    main(server_name)