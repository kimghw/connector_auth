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


def load_registry(registry_path: str) -> Dict[str, Any]:
    """Load service registry JSON file"""
    with open(registry_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_internal_args_file(tools_path: str, server_name: str) -> Optional[str]:
    """Find tool_internal_args.json file"""
    tools_path = Path(tools_path).resolve()

    # Search patterns in order of priority
    search_paths = [
        # Same directory as tools file (most reliable)
        tools_path.parent / "tool_internal_args.json",
        # Pattern: mcp_editor/mcp_{server}/tool_internal_args.json (current convention per docs)
        PROJECT_ROOT / "mcp_editor" / f"mcp_{server_name}" / "tool_internal_args.json",
        # Legacy pattern
        PROJECT_ROOT / "mcp_editor" / server_name / "tool_internal_args.json",
    ]

    for candidate in search_paths:
        if candidate.exists():
            return str(candidate)

    return None


def load_internal_args(internal_args_path: Optional[str]) -> Dict[str, Any]:
    """Load internal args from JSON file"""
    if not internal_args_path or not Path(internal_args_path).exists():
        return {}

    try:
        with open(internal_args_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load internal_args from {internal_args_path}: {e}")
        return {}


def load_tool_definitions(tool_def_path: str) -> List[Dict[str, Any]]:
    """Load tool definitions from Python module or JSON file"""
    path = Path(tool_def_path)

    if path.suffix == '.json':
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
                        # Handle json.loads pattern
                        if isinstance(node.value, ast.Call):
                            func = node.value.func
                            if hasattr(func, 'attr') and func.attr == 'loads':
                                # json.loads("""...""")
                                if node.value.args and isinstance(node.value.args[0], ast.Constant):
                                    return json.loads(node.value.args[0].value)
                        # Handle literal list/dict
                        return ast.literal_eval(node.value)

            # Handle type-annotated assignment
            if isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and node.target.id == 'MCP_TOOLS':
                    if isinstance(node.value, ast.Call):
                        func = node.value.func
                        if hasattr(func, 'attr') and func.attr == 'loads':
                            if node.value.args and isinstance(node.value.args[0], ast.Constant):
                                return json.loads(node.value.args[0].value)
                    return ast.literal_eval(node.value)

        raise ValueError("Could not find MCP_TOOLS in the Python file")
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")


def extract_param_types(registry: Dict[str, Any]) -> List[str]:
    """Extract unique parameter types from registry"""
    param_types = set()

    for service_name, service_data in registry.get('services', {}).items():
        for param in service_data.get('parameters', []):
            param_type = param.get('type', '')
            # Extract custom types (not built-ins)
            if param_type and 'Params' in param_type:
                # Handle Optional[XXXParams] -> XXXParams
                if 'Optional[' in param_type:
                    param_type = param_type.replace('Optional[', '').replace(']', '')
                param_types.add(param_type)

    return sorted(list(param_types))


def prepare_context(registry: Dict[str, Any], tools: List[Dict[str, Any]], server_name: str, internal_args: Dict[str, Any] = None) -> Dict[str, Any]:
    """Prepare Jinja2 context from registry, tools, and internal args"""
    if internal_args is None:
        internal_args = {}

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

    # Extract parameter types
    param_types = extract_param_types(registry)

    # Process tools with internal args and implementation info
    processed_tools = []
    for tool in tools:
        tool_name = tool.get('name', '')
        tool_internal_args = internal_args.get(tool_name, {})

        # Add internal_args to the tool
        tool_with_internal = dict(tool)
        tool_with_internal['internal_args'] = tool_internal_args

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
            # Fallback: try to find by iterating services
            for svc_name, svc_info in services.items():
                tool_with_internal['implementation'] = svc_info
                break

        # Build params from mcp_service.parameters or inputSchema.properties
        params = {}
        object_params = {}
        call_params = {}

        # Get parameters from mcp_service if available
        if isinstance(mcp_service, dict):
            for param in mcp_service.get('parameters', []):
                param_name = param.get('name', '')
                param_type = param.get('type', 'str')
                is_required = param.get('is_required', False)
                has_default = param.get('has_default', False)
                default = param.get('default')

                params[param_name] = {
                    'type': param_type,
                    'is_required': is_required,
                    'has_default': has_default,
                    'default': default,
                    'default_json': json.dumps(default) if default is not None else 'None'
                }

                # Check if it's an object type (Params class)
                if 'Params' in param_type or param_type == 'object':
                    # Extract class name from type (e.g., Optional[FilterParams] -> FilterParams)
                    class_name = param_type.replace('Optional[', '').replace(']', '')
                    object_params[param_name] = {
                        'class_name': class_name,
                        'is_optional': 'Optional' in param_type or has_default,
                        'has_default': has_default,
                        'default_json': json.dumps(default) if default is not None else None
                    }

                # Build call_params (how to pass to service method)
                if param_name in tool_internal_args:
                    call_params[param_name] = {'value': f'{param_name}_params'}
                elif param_name in object_params:
                    call_params[param_name] = {'value': f'{param_name}_params'}
                else:
                    call_params[param_name] = {'value': param_name}

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
                    'default_json': json.dumps(default) if default is not None else 'None'
                }

                if prop_type == 'object':
                    base_model = prop_def.get('baseModel', '')
                    object_params[prop_name] = {
                        'class_name': base_model or 'dict',
                        'is_optional': not is_required,
                        'has_default': default is not None,
                        'default_json': json.dumps(default) if default is not None else None
                    }

                call_params[prop_name] = {'value': f'{prop_name}_params' if prop_name in object_params else prop_name}

        tool_with_internal['params'] = params
        tool_with_internal['object_params'] = object_params
        tool_with_internal['call_params'] = call_params

        processed_tools.append(tool_with_internal)

    # Prepare context
    context = {
        'server_name': server_name,
        'server_title': f"{server_name.replace('_', ' ').title()} MCP Server",
        'services': services,
        'tools': processed_tools,  # List of tools with implementation info for template iteration
        'tools_map': tools_map,    # Dict for quick lookup by name
        'param_types': param_types,
        'MCP_TOOLS': processed_tools,  # Tool definitions with internal args (same as tools)
        'internal_args': internal_args  # Full internal args for reference
    }

    return context


def generate_server(
    template_path: str,
    output_path: str,
    registry_path: str,
    tools_path: str,
    server_name: str
):
    """Generate server.py from registry and template

    Args:
        template_path: Path to Jinja2 template file
        output_path: Path for generated server.py
        registry_path: Path to service registry JSON
        tools_path: Path to tool definitions
        server_name: Name of the server (outlook, file_handler, etc.)
    """

    # Load registry and tools
    print(f"Loading registry from: {registry_path}")
    registry = load_registry(registry_path)

    print(f"Loading tool definitions from: {tools_path}")
    tools = load_tool_definitions(tools_path)

    # Find and load internal args
    internal_args_path = find_internal_args_file(tools_path, server_name)
    internal_args = {}
    if internal_args_path:
        print(f"Loading internal args from: {internal_args_path}")
        internal_args = load_internal_args(internal_args_path)
        print(f"  - Loaded internal args for {len(internal_args)} tools")
    else:
        print("No internal args file found")

    # Prepare context
    context = prepare_context(registry, tools, server_name, internal_args)

    # Setup Jinja2
    template_dir = os.path.dirname(template_path)
    env = Environment(loader=FileSystemLoader(template_dir))
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

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        # Default: mcp_{server}/mcp_server/server.py
        output_path = str(PROJECT_ROOT / f"mcp_{args.server_name}" / "mcp_server" / "server.py")

    # Generate server
    try:
        generate_server(
            server_name=args.server_name,
            registry_path=registry_path,
            tools_path=tools_path,
            template_path=args.template,
            output_path=output_path
        )
    except Exception as e:
        print(f"❌ Error generating server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


