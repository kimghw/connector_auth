#!/usr/bin/env python3
"""
Generate attachment server.py from tool_definitions.py using Jinja2 template
Specialized for attachment file management services
"""
import os
import sys
import ast
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader


def load_tool_definitions(tool_def_path: str) -> List[Dict[str, Any]]:
    """Load tool definitions from file using AST parsing to avoid import issues"""
    path = Path(tool_def_path)
    if not path.exists():
        raise FileNotFoundError(f"Tool definitions file not found: {tool_def_path}")

    with open(path, 'r') as f:
        tree = ast.parse(f.read())

    for node in tree.body:
        if isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == 'MCP_TOOLS':
                return ast.literal_eval(node.value)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'MCP_TOOLS':
                    return ast.literal_eval(node.value)

    raise ValueError("Could not find MCP_TOOLS definition in file")


def analyze_attachment_tool(tool: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze attachment tool schema and map to appropriate service

    Attachment services:
    - FileManager: handles file operations, conversions, OneDrive integration
    - MetadataManager: handles metadata operations
    """
    tool_name = tool['name']

    # Determine service based on tool name
    if 'metadata' in tool_name:
        service_class = 'MetadataManager'
        service_method = tool_name
    else:
        # Default to FileManager for all file operations
        service_class = 'FileManager'
        service_method = tool_name

    # Extract parameters
    params = {}
    if 'inputSchema' in tool and 'properties' in tool['inputSchema']:
        for param_name, param_schema in tool['inputSchema']['properties'].items():
            params[param_name] = {
                'type': param_schema.get('type'),
                'is_required': param_name in tool['inputSchema'].get('required', []),
                'has_default': 'default' in param_schema,
                'default': param_schema.get('default')
            }

    return {
        'name': tool_name,
        'service_class': service_class,
        'service_method': service_method,
        'params': params
    }


def generate_server(template_path: str, tools_path: str, output_path: str = None, replace: bool = False, backup_dir: str = None):
    """
    Generate attachment server.py from template and tool definitions

    Args:
        template_path: Path to Jinja2 template
        tools_path: Path to tool_definitions.py
        output_path: Where to write generated server (optional)
        replace: If True, backup and replace existing server.py
        backup_dir: Directory for backups (default: ./backups)
    """
    # Load template
    env = Environment(
        loader=FileSystemLoader(os.path.dirname(template_path))
    )
    template = env.get_template(os.path.basename(template_path))

    # Load tool definitions
    tool_definitions = load_tool_definitions(tools_path)

    # Analyze tools for attachment services
    analyzed_tools = []
    for tool in tool_definitions:
        analyzed_tools.append(analyze_attachment_tool(tool))

    # Prepare template context
    context = {
        'tools': analyzed_tools
    }

    # Render template
    output = template.render(**context)

    # Determine output path
    if replace:
        tools_path = Path(tools_path)
        server_path = tools_path.parent / "server.py"

        # Create backup if file exists
        if server_path.exists():
            if backup_dir is None:
                backup_dir = tools_path.parent / "backups"
            else:
                backup_dir = Path(backup_dir)

            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"server_backup_{timestamp}.py"
            shutil.copy2(server_path, backup_path)
            print(f"Backed up existing server to: {backup_path}")

        output_path = server_path
    elif output_path is None:
        output_path = "server.py"

    # Write generated server
    with open(output_path, 'w') as f:
        f.write(output)

    print(f"Generated attachment server: {output_path}")
    print(f"Tools included: {', '.join(t['name'] for t in analyzed_tools)}")

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate attachment MCP server from tool definitions")
    parser.add_argument(
        "tools",
        help="Path to tool_definitions.py file"
    )
    parser.add_argument(
        "-t", "--template",
        default="/home/kimghw/Connector_auth/jinja/attachment_server_template.jinja2",
        help="Path to Jinja2 template (default: attachment_server_template.jinja2)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output path for generated server (default: server.py in same dir as tools)"
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Backup and replace existing server.py in the same directory as tool_definitions.py"
    )
    parser.add_argument(
        "--backup-dir",
        help="Directory for backups when using --replace (default: ./backups)"
    )

    args = parser.parse_args()

    generate_server(
        template_path=args.template,
        tools_path=args.tools,
        output_path=args.output,
        replace=args.replace,
        backup_dir=args.backup_dir
    )


if __name__ == "__main__":
    main()