#!/usr/bin/env python3
"""
Generate server.py from tool definitions using Jinja2 template
"""
import os
import sys
import re
import argparse
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader


def copy_mcp_decorators(output_dir: str) -> Path:
    """Generate mcp_decorators.py file"""
    decorators_content = '''"""
MCP Tool Decorator
Decorator for marking functions as MCP tools
"""
from functools import wraps
from typing import Any, Callable, Dict, Optional

# Registry to store MCP tool metadata
MCP_TOOL_REGISTRY = {}

def mcp_tool(
    tool_name: str,
    description: str = "",
    category: str = "",
    tags: list = None,
    priority: int = 0
) -> Callable:
    """
    Decorator to mark a function as an MCP tool

    Args:
        tool_name: Name of the tool in MCP
        description: Tool description
        category: Tool category
        tags: List of tags
        priority: Tool priority
    """
    def decorator(func: Callable) -> Callable:
        # Store metadata in registry
        MCP_TOOL_REGISTRY[tool_name] = {
            "function": func,
            "tool_name": tool_name,
            "description": description,
            "category": category,
            "tags": tags or [],
            "priority": priority,
            "module": func.__module__,
            "function_name": func.__name__
        }

        # Add metadata to function
        func._mcp_tool = True
        func._mcp_metadata = {
            "tool_name": tool_name,
            "description": description,
            "category": category,
            "tags": tags or [],
            "priority": priority
        }

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator

def get_mcp_tools() -> Dict[str, Any]:
    """Get all registered MCP tools"""
    return MCP_TOOL_REGISTRY

def get_mcp_tool(tool_name: str) -> Optional[Dict[str, Any]]:
    """Get a specific MCP tool by name"""
    return MCP_TOOL_REGISTRY.get(tool_name)
'''

    decorators_path = Path(output_dir) / 'mcp_decorators.py'
    decorators_path.parent.mkdir(parents=True, exist_ok=True)
    with open(decorators_path, 'w') as f:
        f.write(decorators_content)
    return decorators_path


def parse_signature(signature: str) -> Dict[str, Any]:
    """Parse function signature to extract parameters and their types"""
    params = {}

    # Remove spaces around equals for easier parsing
    signature = signature.replace(" = ", "=")

    # Split by comma, but be careful with nested brackets
    param_strings = []
    current = []
    bracket_count = 0

    for char in signature:
        if char == '[':
            bracket_count += 1
        elif char == ']':
            bracket_count -= 1
        elif char == ',' and bracket_count == 0:
            param_strings.append(''.join(current).strip())
            current = []
            continue
        current.append(char)

    if current:
        param_strings.append(''.join(current).strip())

    for param_str in param_strings:
        # Parse each parameter
        if ':' in param_str:
            name, type_and_default = param_str.split(':', 1)
            name = name.strip()
            type_and_default = type_and_default.strip()

            # Check for default value
            if '=' in type_and_default:
                type_str, default = type_and_default.split('=', 1)
                type_str = type_str.strip()
                default = default.strip()
                params[name] = {
                    'type': type_str,
                    'has_default': True,
                    'default': default,
                    'is_required': False
                }
            else:
                params[name] = {
                    'type': type_and_default,
                    'has_default': False,
                    'default': None,
                    'is_required': 'Optional' not in type_and_default
                }
        else:
            # No type annotation
            name = param_str.strip()
            if '=' in name:
                name, default = name.split('=', 1)
                params[name.strip()] = {
                    'type': 'Any',
                    'has_default': True,
                    'default': default.strip(),
                    'is_required': False
                }
            else:
                params[name] = {
                    'type': 'Any',
                    'has_default': False,
                    'default': None,
                    'is_required': True
                }

    return params


def analyze_tool_schema(tool: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze tool schema to understand parameter types and requirements"""

    # Determine service based on tool name
    tool_name = tool['name']

    # Attachment server tools
    if 'file' in tool_name or 'convert' in tool_name or 'onedrive' in tool_name or 'directory' in tool_name:
        service_class = 'FileManager'
        service_object = 'file_manager'
        service_method = tool_name
    elif 'metadata' in tool_name:
        service_class = 'MetadataManager'
        service_object = 'metadata_manager'
        service_method = tool_name
    # Outlook server tools
    else:
        service_class = 'GraphMailQuery' if 'query' in tool_name or 'search' in tool_name else 'GraphMailClient'
        service_object = 'graph_mail_query' if 'query' in tool_name or 'search' in tool_name else 'graph_mail_client'
        service_method = tool_name

    analyzed = {
        'name': tool_name,
        'params': {},
        'object_params': {},
        'call_params': {},
        'service_class': service_class,
        'service_object': service_object,
        'service_method': service_method,
    }

    # Check if tool has mcp_service metadata
    if 'mcp_service' in tool:
        service_info = tool['mcp_service']
        analyzed['service_method'] = service_info.get('name', tool['name'])

        # Parse signature if available
        if 'signature' in service_info:
            signature_params = parse_signature(service_info['signature'])
    else:
        signature_params = {}

    # Analyze input schema
    schema = tool.get('inputSchema', {})
    properties = schema.get('properties', {})
    required = schema.get('required', [])

    for param_name, param_schema in properties.items():
        param_type = param_schema.get('type', 'string')

        # Check if this is an object parameter that needs conversion
        if param_type == 'object':
            # This is an object that needs to be converted to a class
            base_model = param_schema.get('baseModel')
            if not base_model:
                # Try to infer from description or name
                if 'filter' in param_name.lower():
                    base_model = 'FilterParams'
                elif 'exclude' in param_name.lower():
                    base_model = 'ExcludeParams'
                elif 'select' in param_name.lower():
                    base_model = 'SelectParams'

            if base_model:
                analyzed['object_params'][param_name] = {
                    'class_name': base_model,
                    'is_optional': param_name not in required,
                    'is_dict': True  # Most are dict-based
                }

                # Add to call_params with the converted name
                param_info = signature_params.get(param_name, {})
                analyzed['call_params'][param_name] = {
                    'value': f"{param_name}_params" if base_model else param_name
                }
        elif param_type == 'array':
            # Arrays typically pass through directly
            analyzed['params'][param_name] = {
                'is_required': param_name in required,
                'has_default': False,
                'default': None
            }
            analyzed['call_params'][param_name] = {
                'value': param_name
            }
        else:
            # Regular parameters
            param_info = signature_params.get(param_name, {})
            analyzed['params'][param_name] = {
                'is_required': param_name in required,
                'has_default': 'default' in param_info,
                'default': param_info.get('default')
            }

            # Add to call_params if not an object param
            if param_name not in analyzed['object_params']:
                analyzed['call_params'][param_name] = {
                    'value': param_name
                }

    # Special handling for specific tools based on existing server.py patterns
    if tool['name'] == 'query_emails':
        analyzed['service_method'] = 'query_filter'  # Actual method name in GraphMailQuery
        analyzed['object_params'] = {
            'filter': {'class_name': 'FilterParams', 'is_optional': True, 'is_dict': True},
            'exclude': {'class_name': 'ExcludeParams', 'is_optional': True, 'is_dict': True},
            'select': {'class_name': 'SelectParams', 'is_optional': True, 'is_dict': True},
        }
        analyzed['params'] = {
            'user_email': {'is_required': True, 'has_default': False},
            'top': {'is_required': False, 'has_default': True, 'default': '10'},
            'orderby': {'is_required': False, 'has_default': True, 'default': '"receivedDateTime desc"'},
        }
        analyzed['call_params'] = {
            'user_email': {'value': 'user_email'},
            'filter': {'value': 'filter_params'},
            'exclude': {'value': 'exclude_params'},
            'select': {'value': 'select_params'},
            'top': {'value': 'args.get("top", 10)'},
            'orderby': {'value': 'args.get("orderby", "receivedDateTime desc")'},
        }
    elif tool['name'] == 'mail_search':
        # Handle mail_search which maps to query_search
        if 'mcp_service' in tool:
            analyzed['service_method'] = tool['mcp_service']['name']
        else:
            analyzed['service_method'] = 'query_search'  # Default mapping for mail_search

        analyzed['object_params'] = {
            'client_filter': {'class_name': 'FilterParams', 'is_optional': True, 'is_dict': True},
            'select': {'class_name': 'SelectParams', 'is_optional': True, 'is_dict': True},
        }
        analyzed['params'] = {
            'user_email': {'is_required': True, 'has_default': False},
            'search': {'is_required': True, 'has_default': False},
            'top': {'is_required': False, 'has_default': True, 'default': '250'},
            'orderby': {'is_required': False, 'has_default': False},
        }
        analyzed['call_params'] = {
            'user_email': {'value': 'user_email'},
            'search': {'value': 'search'},
            'client_filter': {'value': 'client_filter_params'},
            'select': {'value': 'select_params'},
            'top': {'value': 'args.get("top", 250)'},
            'orderby': {'value': 'orderby'},
        }

    return analyzed


def extract_service_metadata(tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract metadata about services and imports from tools"""
    metadata = {
        'services': {},
        'param_types': set(),
        'modules': set()
    }

    # Analyze all tools to determine what services and types are needed
    for tool in tools:
        # Check for service information
        if 'mcp_service' in tool:
            service_info = tool['mcp_service']
            # Extract service class info if available
            if 'class' in service_info:
                class_name = service_info['class']
                module = service_info.get('module', 'graph_mail_query')
                metadata['services'][class_name] = {
                    'module': module,
                    'instance_name': class_name[0].lower() + class_name[1:] if class_name else 'service'
                }
                metadata['modules'].add(module)

        # Extract parameter types
        schema = tool.get('inputSchema', {})
        properties = schema.get('properties', {})

        for prop_name, prop_schema in properties.items():
            if prop_schema.get('type') == 'object':
                base_model = prop_schema.get('baseModel')
                if base_model:
                    metadata['param_types'].add(base_model)

    # Add default services based on tool names if none found
    if not metadata['services']:
        # Check if it's attachment or outlook server
        has_attachment_tools = any('file' in tool['name'] or 'metadata' in tool['name']
                                  or 'convert' in tool['name'] or 'onedrive' in tool['name']
                                  for tool in tools)

        if has_attachment_tools:
            metadata['services'] = {
                'FileManager': {
                    'module': 'file_manager',
                    'instance_name': 'file_manager'
                },
                'MetadataManager': {
                    'module': 'metadata.manager',
                    'instance_name': 'metadata_manager'
                }
            }
            metadata['modules'] = {'file_manager', 'metadata.manager'}
        else:
            metadata['services'] = {
                'GraphMailQuery': {
                    'module': 'graph_mail_query',
                    'instance_name': 'graph_mail_query'
                },
                'GraphMailClient': {
                    'module': 'graph_mail_client',
                    'instance_name': 'graph_mail_client'
                }
            }
            metadata['modules'] = {'graph_mail_query', 'graph_mail_client'}

    # Ensure we have the basic parameter types
    metadata['param_types'].update(['FilterParams', 'ExcludeParams', 'SelectParams'])

    return metadata


def generate_server(template_path: str, output_path: str, tools: List[Dict[str, Any]] = None):
    """Generate server.py from template and tool definitions"""
    # Use provided tools or fall back to global MCP_TOOLS
    if tools is None:
        tools = MCP_TOOLS

    # Set up Jinja2 environment
    template_dir = os.path.dirname(template_path)
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(os.path.basename(template_path))

    # Extract service metadata
    service_metadata = extract_service_metadata(tools)

    # Analyze all tools
    analyzed_tools = []
    for tool in tools:
        analyzed = analyze_tool_schema(tool)

        # Add service info from metadata if available
        if 'mcp_service' in tool and 'class' in tool['mcp_service']:
            class_name = tool['mcp_service']['class']
            if class_name in service_metadata['services']:
                analyzed['service_class'] = class_name
                analyzed['service_object'] = service_metadata['services'][class_name]['instance_name']
                analyzed['service_module'] = service_metadata['services'][class_name]['module']

        analyzed_tools.append(analyzed)

    # Prepare context for template
    context = {
        'tools': analyzed_tools,
        'services': service_metadata['services'],
        'param_types': sorted(service_metadata['param_types']),
        'modules': sorted(service_metadata['modules'])
    }

    # Render template
    rendered = template.render(**context)

    # Write output
    with open(output_path, 'w') as f:
        f.write(rendered)

    print(f"Generated {output_path} successfully!")
    print(f"Processed {len(analyzed_tools)} tools:")
    for tool in analyzed_tools:
        print(f"  - {tool['name']} -> {tool['service_method']}()")
    print(f"\nServices detected:")
    for service, info in service_metadata['services'].items():
        print(f"  - {service} from {info['module']}")
    print(f"\nParameter types: {', '.join(sorted(service_metadata['param_types']))}")


def load_tool_definitions(tool_def_path: str) -> List[Dict[str, Any]]:
    """Load tool definitions from a Python module or JSON file"""
    path = Path(tool_def_path)

    if path.suffix == '.json':
        # Load from JSON file
        with open(path, 'r') as f:
            data = json.load(f)
            return data.get('MCP_TOOLS', data)
    elif path.suffix == '.py':
        # Use AST to parse the file without importing
        import ast

        with open(path, 'r') as f:
            tree = ast.parse(f.read())

        for node in tree.body:
            # Handle regular assignment (MCP_TOOLS = [...])
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'MCP_TOOLS':
                        return ast.literal_eval(node.value)

            # Handle type-annotated assignment (MCP_TOOLS: List[Dict[str, Any]] = [...])
            if isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and node.target.id == 'MCP_TOOLS':
                    return ast.literal_eval(node.value)

        raise ValueError("Could not find MCP_TOOLS in the Python file")
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}. Use .py or .json")


def main():
    parser = argparse.ArgumentParser(description='Generate MCP server from tool definitions')
    parser.add_argument(
        '--tools', '-t',
        required=True,
        help='Path to tool definitions file (Python or JSON)'
    )
    parser.add_argument(
        '--template', '-p',
        default=None,
        help='Path to Jinja2 template file (default: outlook_server_template.jinja2 in same directory as this script)'
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Output path for generated server.py (default: temp file, or server.py location with --replace)'
    )
    parser.add_argument(
        '--replace', '-r',
        action='store_true',
        help='Replace existing server.py in place (creates backup first)'
    )
    parser.add_argument(
        '--backup-dir',
        help='Directory for backups when using --replace (default: ./backups)'
    )
    parser.add_argument(
        '--config', '-c',
        help='Path to configuration file with service metadata (JSON)'
    )
    parser.add_argument(
        '--include-decorators',
        action='store_true',
        default=True,
        help='Also generate mcp_decorators.py file (default: True)'
    )

    args = parser.parse_args()

    # Set default template path if not provided
    if args.template is None:
        script_dir = Path(__file__).parent
        template_path = script_dir / "outlook_server_template.jinja2"
    else:
        template_path = Path(args.template)

    # Load tool definitions
    print(f"Loading tool definitions from: {args.tools}")
    global MCP_TOOLS
    MCP_TOOLS = load_tool_definitions(args.tools)
    print(f"  Loaded {len(MCP_TOOLS)} tool definitions")

    # Load additional config if provided
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
            # You can use this config to override service metadata
            print(f"  Loaded configuration from: {args.config}")

    # Handle output path
    if args.replace:
        # Replace mode - output to the actual server.py location
        tools_path = Path(args.tools)
        server_path = tools_path.parent / "server.py"

        # Create backup if file exists
        if server_path.exists():
            from datetime import datetime
            backup_dir = Path(args.backup_dir) if args.backup_dir else server_path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"server_backup_{timestamp}.py"
            backup_path = backup_dir / backup_name

            import shutil
            shutil.copy2(server_path, backup_path)
            print(f"✅ Created backup: {backup_path}")

        output_path = server_path
        use_temp = False
    elif args.output:
        output_path = Path(args.output)
        use_temp = False
    else:
        import tempfile
        temp_fd, temp_path = tempfile.mkstemp(prefix='mcp_server_', suffix='.py')
        os.close(temp_fd)  # Close the file descriptor
        output_path = Path(temp_path)
        use_temp = True
        print(f"Using temporary file: {output_path}")

    # Generate server
    generate_server(str(template_path), str(output_path), MCP_TOOLS)

    print(f"\n✅ Generated server successfully!")
    print(f"   Output: {output_path}")

    # Generate mcp_decorators.py if requested
    decorators_path = None
    if args.include_decorators:
        # Put decorators in same directory as server.py
        output_dir = output_path.parent
        decorators_path = copy_mcp_decorators(str(output_dir))
        print(f"✅ Generated mcp_decorators.py")
        print(f"   Output: {decorators_path}")

    if use_temp:
        print(f"\n📋 Next steps:")
        print(f"1. Review the generated files:")
        print(f"   cat {output_path}")
        if decorators_path:
            print(f"   cat {decorators_path}")
        print(f"\n2. If satisfied, copy to your project:")
        print(f"   cp {output_path} mcp_outlook/mcp_server/server.py")
        if decorators_path:
            print(f"   cp {decorators_path} mcp_outlook/mcp_server/")
        print(f"\n3. Clean up temp files when done:")
        print(f"   rm {output_path}")
        if decorators_path:
            print(f"   rm {decorators_path}")
    else:
        print(f"\nTo use the generated server:")
        print(f"1. Review the generated files")
        print(f"2. Copy to mcp_outlook/mcp_server/ directory")
        print(f"3. Test with: python -m mcp_outlook.mcp_server.server")


if __name__ == "__main__":
    main()