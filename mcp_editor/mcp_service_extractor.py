"""
Extract @mcp_service decorator metadata and function signatures from source code using AST

This module provides utilities to parse Python source files and extract:
- Decorator metadata (tool_name, server_name, category, tags, priority, description)
- Function signatures (parameters, types, defaults)
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Any, Optional


def extract_decorator_metadata(decorator: ast.Call) -> Dict[str, Any]:
    """
    Extract metadata from @mcp_service decorator

    Args:
        decorator: AST Call node representing the decorator

    Returns:
        Dictionary with decorator metadata
    """
    metadata = {}

    for keyword in decorator.keywords:
        if isinstance(keyword.value, ast.Constant):
            # Simple values: tool_name, server_name, category, priority, description
            metadata[keyword.arg] = keyword.value.value
        elif isinstance(keyword.value, ast.List):
            # List values: tags
            values = []
            for element in keyword.value.elts:
                if isinstance(element, ast.Constant):
                    values.append(element.value)
            metadata[keyword.arg] = values
        elif isinstance(keyword.value, ast.Name):
            # Variable reference
            metadata[keyword.arg] = keyword.value.id

    return metadata


def extract_function_signature(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """
    Extract function signature as a string

    Args:
        func_node: AST function definition node

    Returns:
        Signature string like "param1: str, param2: int = 10"
    """
    args = func_node.args
    param_parts = []

    # Regular arguments
    for i, arg in enumerate(args.args):
        # Skip 'self' parameter
        if arg.arg == 'self':
            continue

        param_str = arg.arg

        # Add type annotation
        if arg.annotation:
            param_str += f": {ast.unparse(arg.annotation)}"

        # Add default value
        defaults_offset = len(args.args) - len(args.defaults)
        if i >= defaults_offset:
            default_idx = i - defaults_offset
            if default_idx < len(args.defaults):
                default_node = args.defaults[default_idx]
                if isinstance(default_node, ast.Constant):
                    if isinstance(default_node.value, str):
                        param_str += f' = "{default_node.value}"'
                    else:
                        param_str += f" = {default_node.value}"
                else:
                    param_str += f" = {ast.unparse(default_node)}"

        param_parts.append(param_str)

    # *args
    if args.vararg:
        vararg_str = f"*{args.vararg.arg}"
        if args.vararg.annotation:
            vararg_str += f": {ast.unparse(args.vararg.annotation)}"
        param_parts.append(vararg_str)

    # **kwargs
    if args.kwarg:
        kwarg_str = f"**{args.kwarg.arg}"
        if args.kwarg.annotation:
            kwarg_str += f": {ast.unparse(args.kwarg.annotation)}"
        param_parts.append(kwarg_str)

    return ", ".join(param_parts)


def find_mcp_services_in_file(file_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Find all @mcp_service decorated functions in a Python file

    Args:
        file_path: Path to Python source file

    Returns:
        Dictionary mapping function names to their metadata and signatures
        {
            "function_name": {
                "metadata": {...},  # Decorator metadata
                "signature": "...",  # Function signature
                "is_async": bool
            }
        }
    """
    services = {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check if function has @mcp_service decorator
                for decorator in node.decorator_list:
                    is_mcp_service = False
                    decorator_metadata = {}

                    # Handle simple decorator: @mcp_service
                    if isinstance(decorator, ast.Name) and decorator.id == 'mcp_service':
                        is_mcp_service = True

                    # Handle decorator with args: @mcp_service(...)
                    elif isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name) and decorator.func.id == 'mcp_service':
                            is_mcp_service = True
                            decorator_metadata = extract_decorator_metadata(decorator)

                    if is_mcp_service:
                        services[node.name] = {
                            "metadata": decorator_metadata,
                            "signature": extract_function_signature(node),
                            "is_async": isinstance(node, ast.AsyncFunctionDef),
                            "file": file_path,
                            "line": node.lineno
                        }
                        break  # Only process first matching decorator

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")

    return services


def scan_codebase_for_mcp_services(base_dir: str, server_name: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Scan entire codebase for @mcp_service decorated functions

    Args:
        base_dir: Base directory to scan
        server_name: Optional server name to filter by

    Returns:
        Dictionary mapping function names to their metadata and signatures
    """
    all_services = {}

    for py_file in Path(base_dir).rglob("*.py"):
        # Skip venv, __pycache__, and other non-source directories
        if any(part in str(py_file) for part in ['venv', '__pycache__', '.git', 'node_modules', 'backups']):
            continue

        services = find_mcp_services_in_file(str(py_file))

        # Filter by server_name if specified
        if server_name:
            services = {
                name: info for name, info in services.items()
                if info["metadata"].get("server_name") == server_name
            }

        all_services.update(services)

    return all_services


def get_signature_for_service(service_name: str, base_dir: str) -> Optional[str]:
    """
    Get function signature for a specific service by name

    Args:
        service_name: Name of the service function
        base_dir: Base directory to scan

    Returns:
        Function signature string or None if not found
    """
    services = scan_codebase_for_mcp_services(base_dir)

    if service_name in services:
        return services[service_name]["signature"]

    return None


def get_signatures_by_name(base_dir: str, server_name: Optional[str] = None) -> Dict[str, str]:
    """
    Get a simple mapping of service names to signatures

    Args:
        base_dir: Base directory to scan
        server_name: Optional server name to filter by

    Returns:
        Dictionary mapping service names to signatures
        {"service_name": "param1: str, param2: int = 10"}
    """
    services = scan_codebase_for_mcp_services(base_dir, server_name)
    return {name: info["signature"] for name, info in services.items()}
