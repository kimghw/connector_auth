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


def to_python_literal(value: Any) -> str:
    """
    Convert a Python value to a string that is valid Python code.
    Unlike json.dumps which produces true/false/null,
    this produces True/False/None.
    """
    if value is None:
        return 'None'
    elif isinstance(value, bool):
        return 'True' if value else 'False'
    elif isinstance(value, str):
        return repr(value)
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, dict):
        items = ', '.join(f'{to_python_literal(k)}: {to_python_literal(v)}' for k, v in value.items())
        return '{' + items + '}'
    elif isinstance(value, (list, tuple)):
        items = ', '.join(to_python_literal(item) for item in value)
        return '[' + items + ']'
    else:
        # Fallback to repr for other types
        return repr(value)


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


def find_internal_args_file(tools_path: str) -> Optional[str]:
    """
    Find tool_internal_args.json based on tools_path location.
    Searches in the same directory or common editor directories.
    """
    tools_path = Path(tools_path).resolve()  # Convert to absolute path

    # Extract server name from path (e.g., mcp_outlook -> outlook)
    # Try to infer from parent directory name
    parent_name = tools_path.parent.name  # e.g., "mcp_server"
    grandparent_name = tools_path.parent.parent.name  # e.g., "mcp_outlook"

    # Derive server name from grandparent (mcp_outlook -> outlook)
    server_name = None
    if grandparent_name.startswith("mcp_"):
        server_name = grandparent_name[4:]  # "outlook"

    # Search patterns (in order of priority)
    search_paths = [
        # Same directory as tools file
        tools_path.parent / "tool_internal_args.json",
        # mcp_editor/{server_name}/ pattern (relative to tools file)
        tools_path.parent.parent / tools_path.parent.name / "tool_internal_args.json",
    ]

    # Try to find the file
    for candidate in search_paths:
        if candidate.exists():
            return str(candidate)

    # Fallback: search in mcp_editor directories at project root
    # Find project root by looking for mcp_editor directory
    project_root = tools_path.parent
    while project_root.parent != project_root:
        mcp_editor_dir = project_root / "mcp_editor"
        if mcp_editor_dir.exists():
            # First, try specific server name directory if we know it
            if server_name:
                specific_path = mcp_editor_dir / server_name / "tool_internal_args.json"
                if specific_path.exists():
                    return str(specific_path)

            # Look for tool_internal_args.json in subdirectories
            for subdir in mcp_editor_dir.iterdir():
                if subdir.is_dir():
                    candidate = subdir / "tool_internal_args.json"
                    if candidate.exists():
                        return str(candidate)
            break
        project_root = project_root.parent

    return None


def load_internal_args(internal_args_path: Optional[str]) -> Dict[str, Any]:
    """
    Load internal args from JSON file.
    Returns empty dict if file doesn't exist.
    """
    if not internal_args_path or not Path(internal_args_path).exists():
        return {}

    try:
        with open(internal_args_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load internal_args from {internal_args_path}: {e}")
        return {}


def extract_defaults_from_schema(original_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract default values from original_schema.properties.
    Returns a dict with property names and their default values.
    Only includes properties that have a 'default' key.
    """
    defaults = {}
    properties = original_schema.get('properties', {})
    for prop_name, prop_info in properties.items():
        if 'default' in prop_info:
            defaults[prop_name] = prop_info['default']
    return defaults


def enrich_internal_args_with_defaults(internal_args: Dict[str, Any]) -> Dict[str, Any]:
    """
    For internal args with empty value {}, extract defaults from original_schema.properties
    and use them as the effective value.
    """
    enriched = {}
    for tool_name, tool_args in internal_args.items():
        enriched[tool_name] = {}
        for arg_name, arg_info in tool_args.items():
            enriched_arg = dict(arg_info)  # Copy original

            # If value is empty dict and original_schema has properties with defaults
            if arg_info.get('value') == {} and 'original_schema' in arg_info:
                defaults = extract_defaults_from_schema(arg_info['original_schema'])
                if defaults:
                    enriched_arg['value'] = defaults

            enriched[tool_name][arg_name] = enriched_arg

    return enriched


def collect_all_param_types(tools: List[Dict[str, Any]], internal_args: Dict[str, Any]) -> set:
    """
    Collect all parameter types from both Signature (inputSchema) and Internal args.
    This ensures all necessary types are imported in the generated server.
    """
    types = set()

    # Collect from Signature parameters (inputSchema)
    for tool in tools:
        schema = tool.get('inputSchema', {})
        properties = schema.get('properties', {})
        for prop_name, prop_schema in properties.items():
            if prop_schema.get('type') == 'object':
                base_model = prop_schema.get('baseModel')
                if base_model:
                    types.add(base_model)

    # Collect from Internal args
    for tool_name, params in internal_args.items():
        for param_name, param_info in params.items():
            param_type = param_info.get('type')
            if param_type:
                types.add(param_type)

    return types


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


def params_from_service_info(service_info: Dict[str, Any]) -> Dict[str, Any]:
    """Prefer structured parameters over re-parsing signature strings."""
    signature_params: Dict[str, Any] = {}

    if not service_info:
        return signature_params

    structured = service_info.get("parameters")
    if isinstance(structured, list):
        for param in structured:
            name = param.get("name")
            if not name or name == "self":
                continue

            param_type = param.get("type") or "Any"
            has_default = param.get("has_default", False)
            default_val = param.get("default")

            # If has_default not explicitly provided, infer from presence of default value
            if not has_default and default_val is not None:
                has_default = True

            signature_params[name] = {
                "type": param_type,
                "has_default": has_default,
                "default": default_val,
                "is_required": param.get(
                    "is_required",
                    not has_default and "Optional" not in str(param_type),
                ),
            }
        return signature_params

    signature = service_info.get("signature")
    if signature:
        return parse_signature(signature)

    return signature_params


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
        # If mcp_service is a string, use it directly as the service method
        if isinstance(service_info, str):
            analyzed['service_method'] = service_info
            analyzed['mcp_service'] = service_info
            signature_params = {}
        else:
            # mcp_service is a dict with 'name' key
            service_method_name = service_info.get('name', tool['name'])
            analyzed['service_method'] = service_method_name
            analyzed['mcp_service'] = service_method_name  # Always set as string for template
            signature_params = params_from_service_info(service_info)
    else:
        signature_params = {}

    # Analyze input schema
    schema = tool.get('inputSchema', {})
    properties = schema.get('properties', {})
    required = schema.get('required', [])

    for param_name, param_schema in properties.items():
        param_type = param_schema.get('type', 'string')

        # Check if this is an object parameter that needs conversion
        # Check for default value - use 'default' in param_schema to detect explicit null defaults
        has_default = 'default' in param_schema
        param_default = param_schema.get('default')

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
                    'is_dict': True,  # Most are dict-based
                    'has_default': has_default,
                    'default': param_default,
                    # Use to_python_literal for valid Python code (True/False/None instead of true/false/null)
                    'default_json': to_python_literal(param_default) if has_default and param_default is not None else None
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
                'has_default': has_default,
                'default': param_default,
                # Use to_python_literal for valid Python code (True/False/None instead of true/false/null)
                'default_json': to_python_literal(param_default) if has_default else None
            }
            analyzed['call_params'][param_name] = {
                'value': param_name
            }
        else:
            # Regular parameters
            # Priority: inputSchema.default > signature_params.default
            param_info = signature_params.get(param_name, {})
            final_has_default = has_default or 'default' in param_info
            final_default = param_default if has_default else param_info.get('default')
            analyzed['params'][param_name] = {
                'is_required': param_name in required,
                'has_default': final_has_default,
                'default': final_default,
                # Use to_python_literal for valid Python code (True/False/None instead of true/false/null)
                'default_json': to_python_literal(final_default) if final_has_default else None
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
            'client_filter': {'class_name': 'ExcludeParams', 'is_optional': True, 'is_dict': True},
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
    elif tool['name'] == 'mail_list':
        # Ensure mail_list maps to the underlying query_filter service
        analyzed['service_class'] = 'GraphMailQuery'
        analyzed['service_object'] = 'graph_mail_query'
        service_override = tool.get('mcp_service')
        if isinstance(service_override, dict):
            service_override = service_override.get('name')
        analyzed['service_method'] = service_override or 'query_filter'

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


def generate_server(template_path: str, output_path: str, tools: List[Dict[str, Any]] = None,
                    tools_path: str = None, internal_args_path: str = None, server_name: str = None):
    """Generate server.py from template and tool definitions

    Args:
        template_path: Path to Jinja2 template file
        output_path: Path for generated server.py
        tools: List of tool definitions (optional, falls back to global MCP_TOOLS)
        tools_path: Path to tools definition file (used for finding internal_args)
        internal_args_path: Explicit path to tool_internal_args.json (optional)
        server_name: Server name for context (optional)
    """
    # Use provided tools or fall back to global MCP_TOOLS
    if tools is None:
        tools = MCP_TOOLS

    # Load internal args
    if not internal_args_path and tools_path:
        internal_args_path = find_internal_args_file(tools_path)
    internal_args_raw = load_internal_args(internal_args_path)

    # Enrich internal args: extract defaults from original_schema.properties
    internal_args = enrich_internal_args_with_defaults(internal_args_raw)

    if internal_args:
        print(f"Loaded internal args for {len(internal_args)} tools from: {internal_args_path}")
        # Show enriched defaults
        for tool_name, tool_args in internal_args.items():
            for arg_name, arg_info in tool_args.items():
                if arg_info.get('value') and arg_info['value'] != internal_args_raw.get(tool_name, {}).get(arg_name, {}).get('value'):
                    print(f"  - {tool_name}.{arg_name}: extracted defaults from schema -> {arg_info['value']}")

    # Set up Jinja2 environment
    template_dir = os.path.dirname(template_path)
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(os.path.basename(template_path))

    # Extract service metadata
    service_metadata = extract_service_metadata(tools)

    # Collect all param types (Signature + Internal)
    all_param_types = collect_all_param_types(tools, internal_args)
    service_metadata['param_types'].update(all_param_types)

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

        # Add internal args for this tool (if any)
        tool_internal_args = internal_args.get(analyzed['name'], {})
        analyzed['internal_args'] = tool_internal_args

        # CRITICAL: Merge internal_args into call_params so they are passed to service methods
        # Internal args use {arg_name}_params naming convention in the template
        for arg_name, arg_info in tool_internal_args.items():
            # Only add to call_params if not already present (internal args should not override schema params)
            if arg_name not in analyzed['call_params']:
                analyzed['call_params'][arg_name] = {
                    'value': f"{arg_name}_params"
                }

        analyzed_tools.append(analyzed)

    # Prepare context for template
    context = {
        'tools': analyzed_tools,
        'services': service_metadata['services'],
        'param_types': sorted(service_metadata['param_types']),
        'modules': sorted(service_metadata['modules']),
        'internal_args': internal_args,  # Full internal args dict for reference
        'server_name': server_name
    }

    # Render template
    rendered = template.render(**context)

    # Write output
    with open(output_path, 'w') as f:
        f.write(rendered)

    print(f"Generated {output_path} successfully!")
    print(f"Processed {len(analyzed_tools)} tools:")
    for tool in analyzed_tools:
        internal_count = len(tool.get('internal_args', {}))
        internal_info = f" (+ {internal_count} internal args)" if internal_count else ""
        print(f"  - {tool['name']} -> {tool['service_method']}(){internal_info}")
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

        def _eval_mcp_tools(node_value):
            """
            Evaluate the MCP_TOOLS assignment node.
            Supports both literal lists/dicts and json.loads(\"\"\"...\"\"\") patterns
            produced by the web editor.
            """
            # Handle json.loads(\"\"\"...\"\"\") style (Call node)
            if isinstance(node_value, ast.Call):
                func = node_value.func
                func_name = None
                if isinstance(func, ast.Attribute):
                    # e.g., json.loads(...)
                    func_name = f"{getattr(func.value, 'id', None)}.{func.attr}"
                elif isinstance(func, ast.Name):
                    # e.g., loads(...)
                    func_name = func.id

                if func_name in ('json.loads', 'loads') and node_value.args:
                    first_arg = node_value.args[0]
                    if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                        return json.loads(first_arg.value)
            # Fallback to literal eval for plain list/dict constants
            return ast.literal_eval(node_value)

        with open(path, 'r') as f:
            tree = ast.parse(f.read())

        for node in tree.body:
            # Handle regular assignment (MCP_TOOLS = [...])
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'MCP_TOOLS':
                        return _eval_mcp_tools(node.value)

            # Handle type-annotated assignment (MCP_TOOLS: List[Dict[str, Any]] = [...])
            if isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and node.target.id == 'MCP_TOOLS':
                    return _eval_mcp_tools(node.value)

        raise ValueError("Could not find MCP_TOOLS in the Python file")
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}. Use .py or .json")


def main():
    parser = argparse.ArgumentParser(description='Generate MCP server from tool definitions')
    parser.add_argument(
        '--tools', '-t',
        default='/home/kimghw/Connector_auth/mcp_editor/outlook/tool_definition_templates.py',
        help='Path to tool definition templates file (default: mcp_editor/outlook/tool_definition_templates.py)'
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

    # Generate server (with tools_path for internal_args discovery)
    generate_server(str(template_path), str(output_path), MCP_TOOLS, tools_path=args.tools)

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
