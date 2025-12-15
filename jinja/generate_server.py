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
    analyzed = {
        'name': tool['name'],
        'params': {},
        'object_params': {},
        'call_params': {},
        'service_class': 'GraphMailQuery',  # Default
        'service_object': 'graph_mail_query',  # Default
        'service_method': tool['name'],  # Default to tool name
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

    # Add default services if none found
    if not metadata['services']:
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
        # Load from Python module
        # Add parent directory to path
        sys.path.insert(0, str(path.parent.parent))

        # Import the module dynamically
        module_path = str(path.parent.name) + '.' + path.stem
        module = __import__(module_path, fromlist=['MCP_TOOLS'])
        return getattr(module, 'MCP_TOOLS', [])
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
        required=True,
        help='Output path for generated server.py'
    )
    parser.add_argument(
        '--config', '-c',
        help='Path to configuration file with service metadata (JSON)'
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

    # Generate server
    output_path = Path(args.output)
    generate_server(str(template_path), str(output_path), MCP_TOOLS)

    print(f"\n✅ Generated server successfully!")
    print(f"   Output: {output_path}")
    print(f"\nTo use the generated server:")
    print(f"1. Review the generated file: {output_path}")
    print("2. Test with: python {output_path}")
    print("3. Replace your existing server.py if satisfied")


if __name__ == "__main__":
    main()