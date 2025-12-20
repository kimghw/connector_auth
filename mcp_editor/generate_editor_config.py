#!/usr/bin/env python3
"""
Generate editor_config.json automatically from @mcp_service decorators and MCP server directories

This script:
1. Scans the codebase for @mcp_service decorators to extract server_name values
2. Detects MCP server directories (mcp_* pattern)
3. Generates editor_config.json with appropriate profiles
"""

import ast
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Set


def extract_server_name_from_file(file_path: str) -> Set[str]:
    """Extract all server_name values from @mcp_service decorators in a Python file"""
    server_names = set()

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
                        # Extract server_name from decorator arguments
                        if isinstance(decorator, ast.Call):
                            for keyword in decorator.keywords:
                                if keyword.arg == 'server_name' and isinstance(keyword.value, ast.Constant):
                                    server_name = keyword.value.value
                                    if server_name:
                                        server_names.add(server_name)
                                        print(f"  Found server_name='{server_name}' in {file_path}")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

    return server_names


def scan_codebase_for_servers(base_dir: str) -> Set[str]:
    """Scan entire codebase for @mcp_service decorators and extract server names"""
    all_server_names = set()

    print(f"Scanning codebase in: {base_dir}")

    for py_file in Path(base_dir).rglob("*.py"):
        # Skip venv, __pycache__, and other non-source directories
        if any(part in str(py_file) for part in ['venv', '__pycache__', '.git', 'node_modules', 'backups']):
            continue

        server_names = extract_server_name_from_file(str(py_file))
        all_server_names.update(server_names)

    return all_server_names


def scan_mcp_directories(base_dir: str) -> Set[str]:
    """Scan for MCP server directories (mcp_* pattern)"""
    server_names = set()

    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)

        # Check if it's a directory starting with mcp_
        if os.path.isdir(item_path) and item.startswith('mcp_'):
            mcp_server_path = os.path.join(item_path, 'mcp_server')

            # Check if it has mcp_server subdirectory with server.py
            if os.path.isdir(mcp_server_path):
                server_py = os.path.join(mcp_server_path, 'server.py')
                if os.path.exists(server_py):
                    # Extract server name from directory name (mcp_XXX -> XXX)
                    server_name = item.replace('mcp_', '')
                    server_names.add(server_name)
                    print(f"  Found MCP directory: {item} -> server: {server_name}")

    return server_names


def detect_module_paths(server_name: str, base_dir: str) -> Dict[str, Any]:
    """
    Detect appropriate file paths for a server based on naming conventions

    Looks for patterns like:
    - mcp_{server_name}/
    - {server_name}_mcp/
    - mcp{server_name}/
    """
    # Normalize server name for directory patterns
    possible_patterns = [
        f"mcp_{server_name}",
        f"{server_name}_mcp",
        f"mcp{server_name}",
        server_name
    ]

    # Find matching directory
    module_dir = None
    for pattern in possible_patterns:
        candidate = os.path.join(base_dir, pattern)
        if os.path.isdir(candidate):
            module_dir = pattern
            print(f"  Detected module directory: {module_dir}")
            break

    if not module_dir:
        # Default fallback
        module_dir = f"mcp_{server_name}"
        print(f"  No directory found, using default: {module_dir}")

    # Construct paths
    mcp_server_dir = f"{module_dir}/mcp_server"

    # Check for types files - try multiple patterns
    types_files = []
    possible_type_files = [
        os.path.join(base_dir, module_dir, f"{server_name}_types.py"),
        os.path.join(base_dir, module_dir, "outlook_types.py"),  # Special case for outlook
        os.path.join(base_dir, module_dir, "types.py"),
        os.path.join(base_dir, module_dir, "graph_types.py"),
    ]

    for type_file_path in possible_type_files:
        if os.path.exists(type_file_path):
            # Get relative path from mcp_editor directory
            rel_path = os.path.relpath(type_file_path, os.path.join(base_dir, "mcp_editor"))
            types_files.append(rel_path)
            print(f"    Found types file: {rel_path}")
            break

    # If no types file found, leave empty array (optional types)
    if not types_files:
        print(f"    No types file found for {server_name}")

    # For new directory structure (profiles in mcp_editor/mcp_{server_name}/)
    editor_profile_dir = f"mcp_{server_name}"

    return {
        "template_definitions_path": f"{editor_profile_dir}/tool_definition_templates.py",
        "tool_definitions_path": f"../{mcp_server_dir}/tool_definitions.py",
        "backup_dir": f"{editor_profile_dir}/backups",
        "types_files": types_files,
        "host": "0.0.0.0",
        "port": 8091
    }


def generate_editor_config_json(server_names: Set[str], base_dir: str, output_path: str):
    """
    Generate editor_config.json with profiles for each discovered server

    Args:
        server_names: Set of server names discovered
        base_dir: Base directory of the project
        output_path: Path where editor_config.json will be saved
    """
    print(f"\nGenerating profiles for {len(server_names)} server(s):")

    # Prepare server configurations
    config = {}
    for server_name in sorted(server_names):
        print(f"  - {server_name}")
        server_config = detect_module_paths(server_name, base_dir)

        # Use mcp_{server_name} as the profile key to match directory structure
        profile_key = f"mcp_{server_name}"
        config[profile_key] = server_config

    # Write config file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Generated {output_path}")
    print(f"  Total profiles: {len(config)}")
    print(f"  Profiles: {', '.join(config.keys())}")


def main():
    """Main entry point"""
    # Determine project root (parent of this script's directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    print("=" * 60)
    print("Generate editor_config.json from MCP servers")
    print("=" * 60)
    print()

    # Method 1: Scan codebase for @mcp_service decorators
    decorator_servers = scan_codebase_for_servers(project_root)

    # Method 2: Scan for mcp_* directories
    directory_servers = scan_mcp_directories(project_root)

    # Combine both methods (union of both sets)
    all_server_names = decorator_servers | directory_servers

    if not all_server_names:
        print("\n⚠ No servers found via decorators or directories")
        print("  Creating default config with 'outlook' server")
        all_server_names = {"outlook"}

    print(f"\nDiscovered {len(all_server_names)} unique server name(s):")
    for name in sorted(all_server_names):
        print(f"  - {name}")

    # Generate config in mcp_editor directory
    config_output_path = os.path.join(project_root, "mcp_editor", "editor_config.json")

    # Backup existing config if it exists
    if os.path.exists(config_output_path):
        backup_path = config_output_path + ".backup"
        import shutil
        shutil.copy2(config_output_path, backup_path)
        print(f"\n📦 Backed up existing config to: {backup_path}")

    # Generate new config
    generate_editor_config_json(all_server_names, project_root, config_output_path)

    print("\n" + "=" * 60)
    print("✓ Done!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Review the generated config file")
    print("  2. Adjust paths if needed")
    print("  3. Restart the web editor to load new profiles")


if __name__ == "__main__":
    main()