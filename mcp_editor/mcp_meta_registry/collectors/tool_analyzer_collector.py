"""
Tool analyzer collector - analyzes tools to generate template-required data structures
This is the most critical collector that ensures template compatibility.
"""
from typing import Dict, Any, List, Optional
from .base import BaseCollector, CollectorContext


class ToolAnalyzer(BaseCollector):
    """
    Analyzes tools to generate template-required data structures.
    Creates tool.params, tool.object_params, tool.call_params, tool.handler.*
    """

    def __init__(self):
        super().__init__()
        self.services = {}
        self.internal_args = {}
        self.methods = {}

    def collect(self, ctx: CollectorContext) -> Dict[str, Any]:
        """
        Analyze tools to generate template-compatible structures.
        Requires tools, services, and internal_args from other collectors.
        """
        # This collector depends on data from other collectors
        # In practice, the registry will pass this data
        return {
            'analyzed_tools': [],
            'requires': ['tools', 'services', 'internal_args']
        }

    def analyze_with_dependencies(self, tools: List[Dict[str, Any]],
                                 services: Dict[str, Any],
                                 internal_args: Dict[str, Any],
                                 methods: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze tools with dependency data from other collectors.
        This is the main analysis method that should be called by the registry.
        """
        self.services = services
        self.internal_args = internal_args
        self.methods = methods or {}

        analyzed_tools = []
        for tool in tools:
            analyzed = self._analyze_tool_schema(tool)
            analyzed_tools.append(analyzed)

        # Collect unique handler instances
        handler_instances = self._collect_handler_instances(analyzed_tools)

        return {
            'analyzed_tools': analyzed_tools,
            'handler_instances': handler_instances
        }

    def validate(self, metadata: Dict[str, Any]) -> bool:
        """Validate analyzed tools structure"""
        if 'analyzed_tools' not in metadata:
            return False

        tools = metadata['analyzed_tools']
        if not isinstance(tools, list):
            return False

        # Each analyzed tool should have required fields
        for tool in tools:
            if not isinstance(tool, dict):
                return False
            # Check for required template fields
            required_fields = ['name', 'handler', 'params', 'object_params', 'call_params']
            for field in required_fields:
                if field not in tool:
                    return False

        return True

    def _to_python_literal(self, value: Any) -> str:
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
            items = ', '.join(f'{self._to_python_literal(k)}: {self._to_python_literal(v)}' for k, v in value.items())
            return '{' + items + '}'
        elif isinstance(value, (list, tuple)):
            items = ', '.join(self._to_python_literal(item) for item in value)
            return '[' + items + ']'
        else:
            # Fallback to repr for other types
            return repr(value)

    def _analyze_tool_schema(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze tool schema to generate template-required structures.
        Main analysis logic migrated from generate_outlook_server.py
        """
        tool_name = tool['name']
        tool_name_lower = tool_name.lower()

        # Determine handler info based on tool type
        if 'file' in tool_name_lower or 'convert' in tool_name_lower or 'onedrive' in tool_name_lower or 'directory' in tool_name_lower:
            handler_class = 'FileManager'
            handler_instance = 'file_manager'
            handler_module = 'file_manager'
            handler_method = tool_name
        elif 'metadata' in tool_name_lower:
            handler_class = 'MetadataManager'
            handler_instance = 'metadata_manager'
            handler_module = 'metadata.manager'
            handler_method = tool_name
        else:
            # Default to GraphMailQuery for outlook tools
            handler_class = 'GraphMailQuery'
            handler_instance = 'graph_mail_query'
            handler_module = 'graph_mail_query'
            handler_method = tool_name

        # Create improved structure
        analyzed = {
            # MCP/Tool naming
            'tool_name': tool_name,
            'name': tool_name,  # Legacy compatibility
            'server_name': 'outlook',  # Will be determined from context

            # Handler info (grouped in dictionary)
            'handler': {
                'method': handler_method,
                'class': handler_class,
                'instance': handler_instance,
                'module': handler_module,
            },

            # Parameters (will be filled below)
            'params': {},
            'object_params': {},
            'call_params': {},

            # Legacy fields for compatibility
            'service_class': handler_class,
            'service_object': handler_instance,
            'service_method': handler_method,
        }

        # Process mcp_service metadata if present
        if 'mcp_service' in tool:
            service_info = tool['mcp_service']
            if isinstance(service_info, str):
                analyzed['handler']['method'] = service_info
                analyzed['service_method'] = service_info
                analyzed['mcp_service'] = service_info
                signature_params = {}
            else:
                # mcp_service is a dict with metadata
                method_name = service_info.get('name', tool_name)
                analyzed['handler']['method'] = method_name
                analyzed['service_method'] = method_name
                analyzed['mcp_service'] = method_name

                # Extract server name if available
                if 'server_name' in service_info:
                    analyzed['server_name'] = service_info['server_name']

                # Override handler info if class is specified
                if 'class' in service_info:
                    class_name = service_info['class']
                    if class_name in self.services:
                        service = self.services[class_name]
                        analyzed['handler']['class'] = class_name
                        analyzed['handler']['instance'] = service['instance_name']
                        analyzed['handler']['module'] = service['module']
                        analyzed['service_class'] = class_name
                        analyzed['service_object'] = service['instance_name']

                signature_params = self._params_from_service_info(service_info)
        else:
            signature_params = {}

        # Analyze input schema
        schema = tool.get('inputSchema', {})
        properties = schema.get('properties', {})
        required = schema.get('required', [])

        for param_name, param_schema in properties.items():
            param_type = param_schema.get('type', 'string')
            has_default = 'default' in param_schema
            param_default = param_schema.get('default')

            if param_type == 'object':
                # Object parameter that needs conversion to a class
                base_model = param_schema.get('baseModel')
                if not base_model:
                    # Try to infer from name
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
                        'is_dict': True,
                        'has_default': has_default,
                        'default': param_default,
                        'default_json': self._to_python_literal(param_default) if has_default and param_default is not None else None
                    }

                    # Add to call_params with converted name
                    analyzed['call_params'][param_name] = {
                        'value': f"{param_name}_params"
                    }
            elif param_type == 'array':
                # Arrays pass through directly
                analyzed['params'][param_name] = {
                    'is_required': param_name in required,
                    'has_default': has_default,
                    'default': param_default,
                    'default_json': self._to_python_literal(param_default) if has_default else None
                }
                analyzed['call_params'][param_name] = {
                    'value': param_name
                }
            else:
                # Regular parameters
                param_info = signature_params.get(param_name, {})
                final_has_default = has_default or 'default' in param_info
                final_default = param_default if has_default else param_info.get('default')
                analyzed['params'][param_name] = {
                    'is_required': param_name in required,
                    'has_default': final_has_default,
                    'default': final_default,
                    'default_json': self._to_python_literal(final_default) if final_has_default else None
                }

                # Add to call_params if not an object param
                if param_name not in analyzed['object_params']:
                    analyzed['call_params'][param_name] = {
                        'value': param_name
                    }

        # Apply special handling for specific tools
        self._apply_tool_specific_overrides(analyzed)

        # Add internal args for this tool
        tool_internal_args = self.internal_args.get(tool_name, {})
        analyzed['internal_args'] = tool_internal_args

        # Merge internal_args into call_params
        for arg_name, arg_info in tool_internal_args.items():
            if arg_name not in analyzed['call_params']:
                analyzed['call_params'][arg_name] = {
                    'value': f"{arg_name}_params"
                }

        # Derive getter name for handler instance
        analyzed['handler']['getter'] = f"get_{analyzed['handler']['instance']}_instance"

        return analyzed

    def _params_from_service_info(self, service_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters from service info (prefer structured over signature string)"""
        signature_params = {}

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

                # Infer has_default from presence of default value
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

        # Fallback to parsing signature string
        signature = service_info.get("signature")
        if signature:
            return self._parse_signature(signature)

        return signature_params

    def _parse_signature(self, signature: str) -> Dict[str, Any]:
        """Parse function signature string to extract parameters"""
        params = {}

        # Remove spaces around equals for easier parsing
        signature = signature.replace(" = ", "=")

        # Split by comma, being careful with nested brackets
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

    def _apply_tool_specific_overrides(self, analyzed: Dict[str, Any]) -> None:
        """Apply special handling for specific tools based on existing patterns"""
        tool_name = analyzed['name']

        if tool_name == 'query_emails':
            analyzed['handler']['method'] = 'query_filter'
            analyzed['service_method'] = 'query_filter'
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

        elif tool_name == 'mail_search':
            if 'mcp_service' in analyzed:
                # Keep the extracted method name
                pass
            else:
                analyzed['handler']['method'] = 'query_search'
                analyzed['service_method'] = 'query_search'

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

        elif tool_name == 'mail_list':
            analyzed['handler']['class'] = 'GraphMailQuery'
            analyzed['handler']['instance'] = 'graph_mail_query'
            analyzed['handler']['module'] = 'graph_mail_query'
            analyzed['service_class'] = 'GraphMailQuery'
            analyzed['service_object'] = 'graph_mail_query'

            service_override = analyzed.get('mcp_service')
            method_name = service_override or 'query_filter'
            analyzed['handler']['method'] = method_name
            analyzed['service_method'] = method_name

    def _collect_handler_instances(self, analyzed_tools: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Collect unique handler instances for helper generation in template"""
        handler_instances = []
        seen_instances = set()

        for tool in analyzed_tools:
            instance_name = tool['handler'].get('instance') or tool.get('service_object')
            class_name = tool['handler'].get('class') or tool.get('service_class')

            if instance_name and instance_name not in seen_instances:
                handler_instances.append({
                    'name': instance_name,
                    'class': class_name
                })
                seen_instances.add(instance_name)

        return handler_instances