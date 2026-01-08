#!/usr/bin/env python3
"""
Universal MCP server generator using registry data
Generates server.py from registry JSON files and universal template
"""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent


def to_python_repr(value: Any) -> str:
    """Convert a Python value to its Python code representation.

    Unlike json.dumps, this produces valid Python syntax:
    - True/False instead of true/false
    - None instead of null
    - repr() for strings to preserve quotes
    """
    if value is None:
        return 'None'
    elif isinstance(value, bool):
        return 'True' if value else 'False'
    elif isinstance(value, str):
        return repr(value)
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, (list, dict)):
        return repr(value)
    else:
        return repr(value)


def load_registry(registry_path: str) -> Dict[str, Any]:
    """Load service registry JSON file"""
    with open(registry_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _convert_params_list_to_dict(params_list: list) -> dict:
    """Convert parameters from list format to dict format.

    Input (list format):
        [{'name': 'subject', 'type': 'boolean', 'is_optional': False, 'default': True, 'description': '메시지 제목'}]

    Output (dict format):
        {'subject': {'default': True, 'description': '메시지 제목', 'type': 'boolean'}}
    """
    if not params_list or not isinstance(params_list, list):
        return {}

    params_dict = {}
    for param in params_list:
        name = param.get("name")
        if not name:
            continue

        param_dict = {"type": param.get("type", "string")}
        # Only add default if has_default is True
        if param.get("has_default", False):
            param_dict["default"] = param.get("default")
        if param.get("description"):
            param_dict["description"] = param["description"]

        params_dict[name] = param_dict

    return params_dict


def extract_service_factors_from_tools(tools: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Extract service factors from mcp_service_factors in tool definitions

    Processes both 'internal' and 'signature_defaults' sources.
    Requires explicit targetParam field in each factor.

    Returns:
        Dict with structure:
        {
            tool_name: {
                'internal': { factor_name: {...}, ... },
                'signature_defaults': { factor_name: {...}, ... }
            }
        }
    """
    service_factors = {}

    for tool in tools:
        tool_name = tool.get('name', '')
        mcp_service_factors = tool.get('mcp_service_factors', {})

        tool_factors = {
            'internal': {},
            'signature_defaults': {}
        }

        for factor_name, factor_data in mcp_service_factors.items():
            source = factor_data.get('source', '')

            # Only process 'internal' and 'signature_defaults' sources
            if source not in ('internal', 'signature_defaults'):
                continue

            # Support both 'type' (new) and 'baseModel' (legacy) field names
            factor_type = factor_data.get('type') or factor_data.get('baseModel', '')

            # targetParam is REQUIRED - no auto-matching
            if 'targetParam' not in factor_data:
                raise ValueError(
                    f"Tool '{tool_name}': mcp_service_factors['{factor_name}'] "
                    f"requires 'targetParam' field to specify target mcp_service parameter"
                )
            target_param = factor_data['targetParam']

            # Get parameters - handle both list format (new) and dict format (legacy)
            raw_params = factor_data.get('parameters', [])
            if isinstance(raw_params, list):
                params_dict = _convert_params_list_to_dict(raw_params)
            else:
                params_dict = raw_params  # Already a dict

            # Extract default values from parameters
            default_values = {}
            for param_name, param_def in params_dict.items():
                if 'default' in param_def:
                    default_values[param_name] = param_def['default']

            # Build the factor structure
            factor_info = {
                'targetParam': target_param,
                'type': factor_type,
                'source': source,
                'value': default_values,
                'original_schema': {
                    'targetParam': target_param,
                    'properties': params_dict,
                    'type': 'object'
                }
            }

            tool_factors[source][factor_name] = factor_info

        # Only add if there are any factors
        if tool_factors['internal'] or tool_factors['signature_defaults']:
            service_factors[tool_name] = tool_factors

    return service_factors


def extract_internal_args_from_tools(tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract internal args from mcp_service_factors in tool definitions (legacy compatibility)

    Requires explicit targetParam field in each factor.
    """
    service_factors = extract_service_factors_from_tools(tools)

    # Convert to legacy internal_args format for backward compatibility
    internal_args = {}
    for tool_name, factors in service_factors.items():
        tool_internal = {}
        # Combine internal factors
        for factor_name, factor_info in factors.get('internal', {}).items():
            tool_internal[factor_name] = {
                'targetParam': factor_info['targetParam'],
                'type': factor_info['type'],
                'value': factor_info['value'],
                'original_schema': factor_info['original_schema']
            }
        if tool_internal:
            internal_args[tool_name] = tool_internal

    return internal_args


def load_tool_definitions(tool_def_path: str) -> List[Dict[str, Any]]:
    """Load tool definitions from Python module, JSON, or YAML file"""
    import yaml
    path = Path(tool_def_path)

    # Try YAML file first (preferred format)
    yaml_path = path.with_suffix('.yaml') if path.suffix == '.py' else path
    if yaml_path.suffix == '.yaml' and yaml_path.exists():
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data.get('tools', data.get('MCP_TOOLS', data))

    if path.suffix == '.json':
        with open(path, 'r') as f:
            data = json.load(f)
            return data.get('MCP_TOOLS', data)
    elif path.suffix == '.py':
        # Check for companion YAML file
        yaml_companion = path.with_suffix('.yaml')
        if yaml_companion.exists():
            with open(yaml_companion, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data.get('tools', data.get('MCP_TOOLS', data))

        # Use AST to parse the file without importing
        import ast

        with open(path, 'r') as f:
            tree = ast.parse(f.read())

        for node in tree.body:
            # Handle regular assignment (MCP_TOOLS = [...])
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'MCP_TOOLS':
                        # Handle json.loads pattern
                        if isinstance(node.value, ast.Call):
                            func = node.value.func
                            if hasattr(func, 'attr') and func.attr == 'loads':
                                # json.loads("""...""")
                                if node.value.args and isinstance(node.value.args[0], ast.Constant):
                                    return json.loads(node.value.args[0].value)
                        # Handle literal list/dict (skip function calls)
                        if not isinstance(node.value, ast.Call):
                            return ast.literal_eval(node.value)

            # Handle type-annotated assignment
            if isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and node.target.id == 'MCP_TOOLS':
                    if isinstance(node.value, ast.Call):
                        func = node.value.func
                        if hasattr(func, 'attr') and func.attr == 'loads':
                            if node.value.args and isinstance(node.value.args[0], ast.Constant):
                                return json.loads(node.value.args[0].value)
                        # Skip other function calls (like _load_tools_from_yaml())
                        # Try to load from YAML companion file
                        yaml_companion = path.with_suffix('.yaml')
                        if yaml_companion.exists():
                            with open(yaml_companion, 'r', encoding='utf-8') as f:
                                data = yaml.safe_load(f)
                                return data.get('tools', data.get('MCP_TOOLS', data))
                    else:
                        return ast.literal_eval(node.value)

        raise ValueError("Could not find MCP_TOOLS in the Python file")
    elif path.suffix == '.yaml':
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data.get('tools', data.get('MCP_TOOLS', data))
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")


def find_type_locations(server_name: str) -> Dict[str, str]:
    """Find the locations of types for a server

    Returns dict mapping type names to their import paths
    """
    import ast
    import glob

    type_locations = {}

    # Search patterns for finding type definitions
    search_paths = [
        PROJECT_ROOT / f"mcp_{server_name}" / "*.py",
        PROJECT_ROOT / f"{server_name}" / "*.py",
        PROJECT_ROOT / "mcp_editor" / f"mcp_{server_name}" / "*.py",
    ]

    for pattern in search_paths:
        for file_path in glob.glob(str(pattern)):
            try:
                with open(file_path, 'r') as f:
                    tree = ast.parse(f.read())

                # Extract module name from file path
                module_parts = Path(file_path).stem
                if 'mcp_' in str(file_path):
                    if 'mcp_editor' in str(file_path):
                        module_name = f"mcp_editor.mcp_{server_name}.{module_parts}"
                    else:
                        module_name = f"mcp_{server_name}.{module_parts}"
                else:
                    module_name = f"{server_name}.{module_parts}"

                # Find class definitions and enums
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check if it's an Enum
                        is_enum = any(
                            base.id == 'Enum' if isinstance(base, ast.Name) else
                            (base.attr == 'Enum' if isinstance(base, ast.Attribute) else False)
                            for base in node.bases
                        )

                        if node.name not in type_locations:
                            type_locations[node.name] = {
                                'module': module_name,
                                'is_enum': is_enum,
                                'file': file_path
                            }
            except:
                # Skip files that can't be parsed
                continue

    return type_locations


def extract_type_info(registry: Dict[str, Any], tools: List[Dict[str, Any]], server_name: str = None) -> Dict[str, Any]:
    """Extract type information from registry and tools

    Returns:
        Dict with:
        - param_types: List of parameter type names
        - enum_types: List of enum type names
        - type_imports: Dict mapping types to their import paths
    """
    param_types = set()
    enum_types = set()
    type_imports = {}

    # Extract from registry parameters
    for service_name, service_data in registry.get('services', {}).items():
        for param in service_data.get('parameters', []):
            param_type = param.get('type', '')

            # Extract custom types (not built-ins)
            if param_type and param_type not in ['str', 'int', 'float', 'bool', 'dict', 'list']:
                # Handle Optional[XXXParams] -> XXXParams
                clean_type = param_type
                if 'Optional[' in clean_type:
                    clean_type = clean_type.replace('Optional[', '').replace(']', '')

                # Categorize types
                if 'Params' in clean_type:
                    param_types.add(clean_type)
                elif clean_type and clean_type[0].isupper():  # Likely an enum or class
                    enum_types.add(clean_type)

    # Extract from tool definitions
    for tool in tools:
        # Check mcp_service parameters
        mcp_service = tool.get('mcp_service', {})
        if isinstance(mcp_service, dict):
            for param in mcp_service.get('parameters', []):
                param_type = param.get('type', '')
                if param_type and param_type not in ['str', 'int', 'float', 'bool', 'dict', 'list']:
                    clean_type = param_type
                    if 'Optional[' in clean_type:
                        clean_type = clean_type.replace('Optional[', '').replace(']', '')

                    if 'Params' in clean_type:
                        param_types.add(clean_type)
                    elif clean_type and clean_type[0].isupper():
                        enum_types.add(clean_type)

    # Find type locations if server_name is provided
    type_locations = {}
    if server_name:
        type_locations = find_type_locations(server_name)

    return {
        'param_types': sorted(list(param_types)),
        'enum_types': sorted(list(enum_types)),
        'all_types': sorted(list(param_types | enum_types)),
        'type_locations': type_locations
    }


def prepare_context(registry: Dict[str, Any], tools: List[Dict[str, Any]], server_name: str, internal_args: Dict[str, Any] = None, protocol_type: str = 'rest', service_factors: Dict[str, Dict[str, Any]] = None) -> Dict[str, Any]:
    """Prepare Jinja2 context from registry, tools, internal args, and service factors"""
    if internal_args is None:
        internal_args = {}
    if service_factors is None:
        service_factors = {}

    # Extract services with proper structure
    services = {}
    for service_name, service_data in registry.get('services', {}).items():
        impl = service_data.get('implementation', service_data.get('handler', {}))
        services[service_name] = {
            'class_name': impl.get('class_name', impl.get('class', '')),
            'module_path': impl.get('module_path', impl.get('module', '')),
            'instance': impl.get('instance', impl.get('instance_name', '')),
            'method': impl.get('method', service_name)
        }

    # Map tools to their implementations
    tools_map = {}
    for service_name, service_data in registry.get('services', {}).items():
        # Get tool names from metadata
        metadata = service_data.get('metadata', {})
        tool_names = metadata.get('tool_names', [])

        impl = service_data.get('implementation', service_data.get('handler', {}))

        for tool_name in tool_names:
            # Clean up tool name (remove Handle_ prefix if present)
            clean_name = tool_name
            if tool_name.startswith('Handle_'):
                clean_name = tool_name[7:]
            elif tool_name.startswith('handle_'):
                clean_name = tool_name[7:]

            tools_map[clean_name] = {
                'implementation': {
                    'class_name': impl.get('class_name', impl.get('class', '')),
                    'method': impl.get('method', service_name),
                    'instance': impl.get('instance', impl.get('instance_name', ''))
                }
            }

    # Extract type information
    type_info = extract_type_info(registry, tools, server_name)

    # Create unique_services for compatibility with STDIO/STREAM templates
    unique_services = {}
    for service_name, service_info in services.items():
        class_name = service_info['class_name']
        if class_name not in unique_services:
            unique_services[class_name] = service_info

    # Process tools with internal args, signature_defaults, and implementation info
    processed_tools = []
    for tool in tools:
        tool_name = tool.get('name', '')
        tool_internal_args = internal_args.get(tool_name, {})
        tool_service_factors = service_factors.get(tool_name, {})

        # Add internal_args and signature_defaults to the tool
        tool_with_internal = dict(tool)
        tool_with_internal['internal_args'] = tool_internal_args
        tool_with_internal['signature_defaults'] = tool_service_factors.get('signature_defaults', {})
        tool_with_internal['service_factors'] = tool_service_factors

        # Find implementation info from registry
        # Check mcp_service for the service name mapping
        mcp_service = tool.get('mcp_service', {})
        if isinstance(mcp_service, str):
            service_name = mcp_service
        else:
            service_name = mcp_service.get('name', tool_name)

        # Get implementation from services
        if service_name in services:
            tool_with_internal['implementation'] = services[service_name]
        elif tool_name in tools_map:
            tool_with_internal['implementation'] = tools_map[tool_name]['implementation']
        else:
            # Fallback: Use a default implementation based on tool configuration
            # For outlook service, use MailService as default
            if server_name == 'outlook':
                tool_with_internal['implementation'] = {
                    'class_name': 'MailService',
                    'module_path': 'mcp_outlook.outlook_service',
                    'instance': 'mail_service',
                    'method': service_name  # Use service_name from mcp_service
                }
            else:
                # Generic fallback for other servers
                for svc_name, svc_info in services.items():
                    tool_with_internal['implementation'] = svc_info
                    break

        # Build params from mcp_service.parameters or inputSchema.properties
        params = {}
        object_params = {}
        call_params = {}

        # First, get the inputSchema to understand the mappings
        input_schema = tool.get('inputSchema', {})
        properties = input_schema.get('properties', {})

        # Create a mapping from inputSchema property name to targetParam (service method param name)
        param_mappings = {}
        for prop_name, prop_def in properties.items():
            target_param = prop_def.get('targetParam', prop_name)
            param_mappings[prop_name] = target_param

        # Build a set of Internal parameter targetParams
        # Note: Internal parameters may also have Signature counterparts with the same targetParam
        internal_target_params = set()
        for arg_name, arg_info in tool_internal_args.items():
            target_param = arg_info.get('targetParam') or arg_info.get('original_schema', {}).get('targetParam', arg_name)
            internal_target_params.add(target_param)

        # Build a set of Signature targetParams (from inputSchema properties)
        signature_target_params = set()
        for prop_name, prop_def in properties.items():
            target_param = prop_def.get('targetParam', prop_name)
            signature_target_params.add(target_param)

        # Get parameters from mcp_service if available
        if isinstance(mcp_service, dict):
            for param in mcp_service.get('parameters', []):
                param_name = param.get('name', '')
                param_type = param.get('type', 'str')

                # Skip Internal parameters ONLY if they don't have a Signature counterpart in inputSchema
                # If both Internal and Signature exist with same targetParam, process it (merge will happen)
                if param_name in internal_target_params and param_name not in signature_target_params:
                    continue

                # Compute is_required: it's required if not optional and no default
                is_optional = param.get('is_optional', False)
                has_default = param.get('has_default', False)
                is_required = param.get('is_required', not is_optional)  # Use is_required if provided, else derive from is_optional
                default = param.get('default')

                # Find the input schema property name that maps to this service parameter
                input_param_name = None
                for inp_name, tgt_name in param_mappings.items():
                    if tgt_name == param_name:
                        input_param_name = inp_name
                        break

                # If not found in mappings, check if param_name exists directly in inputSchema
                if input_param_name is None:
                    if param_name in properties:
                        input_param_name = param_name
                    else:
                        # This parameter is NOT in inputSchema - skip it
                        # (It's neither a Signature parameter nor Internal, likely a service-only param)
                        continue

                params[input_param_name] = {
                    'type': param_type,
                    'is_required': is_required,
                    'has_default': has_default,
                    'default': default,
                    'default_json': to_python_repr(default)
                }

                # Check if it's an object type (Params class)
                if 'Params' in param_type or param_type == 'object':
                    # Extract class name from type (e.g., Optional[FilterParams] -> FilterParams)
                    class_name = param_type.replace('Optional[', '').replace(']', '')

                    # Get the targetParam for this input param
                    target_param = param_mappings.get(input_param_name, param_name)

                    # Find matching internal and signature_defaults by targetParam
                    internal_defaults = {}
                    sig_defaults_values = {}

                    for factor_name, factor_info in tool_service_factors.get('internal', {}).items():
                        if factor_info.get('targetParam') == target_param:
                            internal_defaults = factor_info.get('value', {})
                            break

                    for factor_name, factor_info in tool_service_factors.get('signature_defaults', {}).items():
                        if factor_info.get('targetParam') == target_param:
                            sig_defaults_values = factor_info.get('value', {})
                            break

                    object_params[input_param_name] = {
                        'class_name': class_name,
                        'is_optional': 'Optional' in param_type or has_default,
                        'has_default': has_default,
                        'default_json': to_python_repr(default) if default is not None else None,
                        'target_param': target_param,
                        'internal_defaults': internal_defaults,
                        'signature_defaults_values': sig_defaults_values
                    }

                # Build call_params (how to pass to service method)
                # Map from service param name to the value expression
                if input_param_name in object_params:
                    call_params[param_name] = {'value': input_param_name, 'source_param': input_param_name}
                else:
                    call_params[param_name] = {'value': input_param_name, 'source_param': input_param_name}

        # Fallback: extract from inputSchema if no mcp_service parameters
        if not params:
            input_schema = tool.get('inputSchema', {})
            properties = input_schema.get('properties', {})
            required = input_schema.get('required', [])

            for prop_name, prop_def in properties.items():
                prop_type = prop_def.get('type', 'string')
                is_required = prop_name in required
                default = prop_def.get('default')

                params[prop_name] = {
                    'type': prop_type,
                    'is_required': is_required,
                    'has_default': default is not None,
                    'default': default,
                    'default_json': to_python_repr(default)
                }

                # Get targetParam from inputSchema property or default to prop_name
                target_param = prop_def.get('targetParam', prop_name)

                if prop_type == 'object':
                    base_model = prop_def.get('baseModel', '')

                    # Find matching internal and signature_defaults by targetParam
                    internal_defaults = {}
                    sig_defaults_values = {}

                    for factor_name, factor_info in tool_service_factors.get('internal', {}).items():
                        if factor_info.get('targetParam') == target_param:
                            internal_defaults = factor_info.get('value', {})
                            break

                    for factor_name, factor_info in tool_service_factors.get('signature_defaults', {}).items():
                        if factor_info.get('targetParam') == target_param:
                            sig_defaults_values = factor_info.get('value', {})
                            break

                    object_params[prop_name] = {
                        'class_name': base_model or 'dict',
                        'is_optional': not is_required,
                        'has_default': default is not None,
                        'default_json': to_python_repr(default) if default is not None else None,
                        'target_param': target_param,
                        'internal_defaults': internal_defaults,
                        'signature_defaults_values': sig_defaults_values
                    }

                call_params[target_param] = {'value': prop_name, 'source_param': prop_name}

        # Internal args are handled separately with targetParam mappings
        # They are processed in the template itself (lines 260-291 in universal_server_template.jinja2)
        # Do NOT add them to call_params here as they need to be built at runtime

        tool_with_internal['params'] = params
        tool_with_internal['object_params'] = object_params
        tool_with_internal['call_params'] = call_params
        internal_overrides = {}
        for arg_name, arg_info in tool_internal_args.items():
            if not arg_name.endswith("_internal"):
                continue
            base_name = arg_name[: -len("_internal")]
            if base_name in object_params:
                internal_overrides[base_name] = {
                    "name": arg_name,
                    "info": arg_info
                }
        tool_with_internal['internal_overrides'] = internal_overrides

        processed_tools.append(tool_with_internal)

    # Prepare context
    context = {
        'server_name': server_name,
        'server_title': f"{server_name.replace('_', ' ').title()} MCP Server",
        'protocol_type': protocol_type,  # Add protocol type to context
        'services': services,
        'unique_services': unique_services,  # Add unique_services for STDIO/STREAM templates
        'tools': processed_tools,  # List of tools with implementation info for template iteration
        'tools_map': tools_map,    # Dict for quick lookup by name
        'param_types': type_info['param_types'],  # Parameter types (FilterParams, etc.)
        'enum_types': type_info['enum_types'],     # Enum types (QueryMethod, etc.)
        'all_types': type_info['all_types'],       # All custom types
        'type_info': type_info,                    # Full type information
        'MCP_TOOLS': processed_tools,  # Tool definitions with internal args (same as tools)
        'internal_args': internal_args,  # Full internal args for reference (legacy)
        'service_factors': service_factors  # Full service factors (internal + signature_defaults)
    }

    return context


def generate_server(
    template_path: str,
    output_path: str,
    registry_path: str,
    tools_path: str,
    server_name: str,
    protocol_type: str = 'rest'
):
    """Generate server.py from registry and template

    Args:
        template_path: Path to Jinja2 template file
        output_path: Path for generated server.py
        registry_path: Path to service registry JSON
        tools_path: Path to tool definitions
        server_name: Name of the server (outlook, file_handler, etc.)
        protocol_type: Protocol type ('rest', 'stdio', 'stream')
    """

    # Load registry and tools
    print(f"Loading registry from: {registry_path}")
    registry = load_registry(registry_path)

    print(f"Loading tool definitions from: {tools_path}")
    tools = load_tool_definitions(tools_path)

    # Extract service factors from mcp_service_factors in tool definitions
    print(f"Extracting service factors from mcp_service_factors...")
    service_factors = extract_service_factors_from_tools(tools)
    internal_args = extract_internal_args_from_tools(tools)  # Legacy format for backward compatibility

    if service_factors:
        print(f"  - Extracted service factors for {len(service_factors)} tools")
        for tool_name, factors in service_factors.items():
            internal_count = len(factors.get('internal', {}))
            defaults_count = len(factors.get('signature_defaults', {}))
            print(f"    - {tool_name}: internal={internal_count}, signature_defaults={defaults_count}")
    else:
        print("  - No service factors found in mcp_service_factors")

    # Prepare context
    context = prepare_context(registry, tools, server_name, internal_args, protocol_type, service_factors)

    # Setup Jinja2
    template_dir = os.path.dirname(template_path)
    env = Environment(loader=FileSystemLoader(template_dir))

    # Add custom filter to raise errors during template rendering
    def raise_error(message):
        raise ValueError(message)
    env.filters['raise_error'] = raise_error

    template = env.get_template(os.path.basename(template_path))

    # Render template
    rendered = template.render(**context)

    # Create output directory if needed
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Write output
    with open(output_path, 'w') as f:
        f.write(rendered)

    # Print summary
    print(f"\n✅ Generated {output_path} successfully!")
    print(f"\n📊 Summary:")
    print(f"  - Server: {server_name}")
    print(f"  - Protocol: {protocol_type}")
    print(f"  - Services: {len(context['services'])}")
    print(f"  - Tools mapped: {len(context['tools'])}")
    print(f"  - Parameter types: {', '.join(context['param_types'])}")

    print(f"\n🔧 Services:")
    for service_name, service_info in context['services'].items():
        print(f"  - {service_info['class_name']} ({service_info['module_path']})")

    print(f"\n🛠️ Tool mappings:")
    for tool in context['tools']:
        impl = tool.get('implementation', {})
        print(f"  - {tool.get('name', 'unknown')} -> {impl.get('class_name', '?')}.{impl.get('method', '?')}()")


def find_registry_file(server_name: str) -> Optional[str]:
    """Find registry file for a given server"""
    candidates = [
        # Pattern: registry_{server}.json (current convention per docs)
        PROJECT_ROOT / "mcp_editor" / "mcp_service_registry" / f"registry_{server_name}.json",
        # Legacy patterns
        PROJECT_ROOT / "mcp_editor" / "mcp_service_registry" / f"{server_name}_registry.json",
        PROJECT_ROOT / "mcp_editor" / f"mcp_{server_name}" / f"registry_{server_name}.json",
        PROJECT_ROOT / f"mcp_{server_name}" / f"{server_name}_registry.json",
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return None


def find_tools_file(server_name: str) -> Optional[str]:
    """Find tool definitions file for a given server"""
    candidates = [
        # Pattern: mcp_editor/mcp_{server}/tool_definition_templates.py (current convention per docs)
        PROJECT_ROOT / "mcp_editor" / f"mcp_{server_name}" / "tool_definition_templates.py",
        # Legacy patterns
        PROJECT_ROOT / "mcp_editor" / server_name / "tool_definition_templates.py",
        PROJECT_ROOT / "mcp_editor" / "tool_definition_templates.py",
        PROJECT_ROOT / f"mcp_{server_name}" / "tool_definitions.py",
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate MCP server from universal template")
    parser.add_argument("server_name", help="Server name (e.g., 'outlook', 'file_handler')")
    parser.add_argument("--protocol", help="Protocol type",
                       choices=['rest', 'stdio', 'stream', 'all'], default='rest')
    parser.add_argument("--registry", help="Path to registry JSON file (auto-detected if not specified)")
    parser.add_argument("--tools", help="Path to tool definitions file (auto-detected if not specified)")
    parser.add_argument("--template", help="Path to Jinja2 template",
                       default=str(SCRIPT_DIR / "universal_server_template.jinja2"))
    parser.add_argument("--output", help="Output path for generated server.py")

    args = parser.parse_args()

    # Find registry file
    registry_path = args.registry or find_registry_file(args.server_name)
    if not registry_path:
        print(f"❌ Could not find registry file for server '{args.server_name}'")
        print(f"   Searched in: mcp_editor/mcp_service_registry/registry_{args.server_name}.json")
        sys.exit(1)

    # Find tools file
    tools_path = args.tools or find_tools_file(args.server_name)
    if not tools_path:
        print(f"❌ Could not find tool definitions file for server '{args.server_name}'")
        print(f"   Searched in: mcp_editor/mcp_{args.server_name}/tool_definition_templates.py")
        sys.exit(1)

    # Generate all protocols or specific one
    if args.protocol == 'all':
        protocols_to_generate = ['rest', 'stdio', 'stream']
    else:
        protocols_to_generate = [args.protocol]

    # Track success/failure
    success_count = 0
    failed_protocols = []

    for protocol in protocols_to_generate:
        # Always use universal template for all protocols
        template_path = args.template or str(SCRIPT_DIR / "universal_server_template.jinja2")

        # Determine output path
        if args.output:
            output_base = Path(args.output)
            # Check if output is a directory or file
            if output_base.suffix == '' or output_base.is_dir():
                # Output is a directory - generate filename automatically
                if protocol == 'rest':
                    filename = 'server_rest.py'  # Changed for consistency
                else:
                    filename = f'server_{protocol}.py'
                output_path = str(output_base / filename)
            else:
                # Output is a file path
                if len(protocols_to_generate) == 1:
                    output_path = args.output
                else:
                    # Multiple protocols but single file specified - append protocol
                    base = output_base.stem
                    ext = output_base.suffix
                    if protocol == 'rest':
                        filename = f'{base}_rest{ext}'
                    else:
                        filename = f'{base}_{protocol}{ext}'
                    output_path = str(output_base.parent / filename)
        else:
            # Default: mcp_{server}/mcp_server/server_{protocol}.py
            if protocol == 'rest':
                filename = 'server_rest.py'  # Changed for consistency
            else:
                filename = f'server_{protocol}.py'
            output_path = str(PROJECT_ROOT / f"mcp_{args.server_name}" / "mcp_server" / filename)

        # Generate server
        try:
            print(f"\n{'='*60}")
            print(f"🚀 Generating {protocol.upper()} server...")
            print(f"{'='*60}")

            generate_server(
                server_name=args.server_name,
                registry_path=registry_path,
                tools_path=tools_path,
                template_path=template_path,
                output_path=output_path,
                protocol_type=protocol
            )
            success_count += 1
        except Exception as e:
            print(f"❌ Error generating {protocol} server: {e}")
            import traceback
            traceback.print_exc()
            failed_protocols.append(protocol)

    # Print final summary
    print(f"\n{'='*60}")
    print(f"📋 GENERATION SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successfully generated: {success_count}/{len(protocols_to_generate)} servers")

    if failed_protocols:
        print(f"❌ Failed protocols: {', '.join(failed_protocols)}")
        sys.exit(1)
    else:
        print(f"🎉 All servers generated successfully!")
        sys.exit(0)

