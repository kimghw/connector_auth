"""
Service scanner collector - scans for @mcp_service decorated methods using AST
"""
import ast
import re
from typing import Dict, Any, Set, List
from pathlib import Path
from .base import BaseCollector, CollectorContext


class ServiceScanner(BaseCollector):
    """Collector for scanning @mcp_service and @mcp_tool decorated methods"""

    def collect(self, ctx: CollectorContext) -> Dict[str, Any]:
        """Scan for decorated methods in the scan_dir"""
        if not ctx.scan_dir or not ctx.scan_dir.exists():
            return self.collect_minimal(ctx)

        try:
            result = self._analyze_decorated_methods(ctx.scan_dir, ctx.skip_parts)
            return {
                'services': result['services'],
                'methods': result['methods'],
                'param_types': list(result['param_types']),
                'scan_dir': str(ctx.scan_dir)
            }
        except Exception as e:
            print(f"Warning: Failed to scan services in {ctx.scan_dir}: {e}")
            return self.collect_minimal(ctx)

    def collect_minimal(self, ctx: CollectorContext) -> Dict[str, Any]:
        """Return minimal valid structure"""
        return {
            'services': {},
            'methods': {},
            'param_types': [],
            'scan_dir': str(ctx.scan_dir) if ctx.scan_dir else None
        }

    def validate(self, metadata: Dict[str, Any]) -> bool:
        """Validate service metadata structure"""
        if 'services' not in metadata or 'methods' not in metadata:
            return False

        services = metadata['services']
        if not isinstance(services, dict):
            return False

        methods = metadata['methods']
        if not isinstance(methods, dict):
            return False

        # Each service should have module and instance_name
        for service_name, service_info in services.items():
            if not isinstance(service_info, dict):
                return False
            if 'module' not in service_info or 'instance_name' not in service_info:
                return False

        return True

    def _analyze_decorated_methods(self, scan_dir: Path, skip_parts: tuple) -> Dict[str, Any]:
        """
        Analyze Python files to find @mcp_tool/@mcp_service decorated methods and extract service info
        """
        result = {
            'services': {},  # class_name -> {'module': module_name, 'instance_name': instance_name}
            'methods': {},   # method_name -> {'class': class_name, 'module': module_name, 'signature': ..., 'parameters': ...}
            'param_types': set()
        }

        # Common directories to check for service files
        search_dirs = [
            scan_dir,
            scan_dir.parent,  # Check parent directory
            scan_dir / 'mcp_server'
        ]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            # Find all Python files
            py_files = list(search_dir.glob('*.py'))

            for py_file in py_files:
                # Skip excluded directories and files
                if any(skip in str(py_file) for skip in skip_parts):
                    continue
                # Skip generated files
                if any(skip in py_file.name for skip in ['server.py', 'tool_definitions.py', 'test_']):
                    continue

                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Parse the AST
                    tree = ast.parse(content)

                    # Find classes and their decorated methods
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            class_name = node.name
                            module_name = py_file.stem  # Use filename as module name

                            # Look for @mcp_tool/@mcp_service decorated methods
                            for item in node.body:
                                if isinstance(item, (ast.AsyncFunctionDef, ast.FunctionDef)):
                                    # Check decorators
                                    for decorator in item.decorator_list:
                                        decorator_info = self._parse_decorator(decorator)
                                        if decorator_info and decorator_info['name'] in ['mcp_tool', 'mcp_service']:
                                            # Found an MCP service/tool method
                                            method_name = item.name

                                            # Add service info if not already present
                                            if class_name not in result['services']:
                                                instance_name = self._class_to_instance_name(class_name)
                                                result['services'][class_name] = {
                                                    'module': module_name,
                                                    'instance_name': instance_name
                                                }

                                            # Extract method signature and parameters
                                            decorated_tool_name = (
                                                (decorator_info.get('args') or {}).get('tool_name')
                                                or method_name
                                            )
                                            method_info = {
                                                'class': class_name,
                                                'module': module_name,
                                                'name': decorated_tool_name,
                                                'signature': self._extract_signature(item),
                                                'parameters': self._extract_parameters(item)
                                            }

                                            # Add decorator arguments if present
                                            if decorator_info.get('args'):
                                                method_info['decorator_args'] = decorator_info['args']

                                            result['methods'][method_name] = method_info

                                            # Extract parameter types from method signature
                                            for param in method_info['parameters']:
                                                param_type = param.get('type')
                                                if param_type and self._is_custom_type(param_type):
                                                    result['param_types'].add(param_type)

                except Exception as e:
                    # Skip files that can't be parsed
                    continue

        return result

    def _parse_decorator(self, decorator) -> Dict[str, Any]:
        """Parse decorator node to extract name and arguments"""
        decorator_info = {}

        if isinstance(decorator, ast.Name):
            # Simple decorator: @decorator_name
            decorator_info['name'] = decorator.id

        elif isinstance(decorator, ast.Call):
            # Decorator with arguments: @decorator_name(args)
            if isinstance(decorator.func, ast.Name):
                decorator_info['name'] = decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                decorator_info['name'] = decorator.func.attr

            # Extract arguments
            args = {}
            # Positional arguments
            for i, arg in enumerate(decorator.args):
                if isinstance(arg, ast.Constant):
                    if i == 0:
                        args['tool_name'] = arg.value
                    else:
                        args[f'arg_{i}'] = arg.value

            # Keyword arguments
            for keyword in decorator.keywords:
                if isinstance(keyword.value, ast.Constant):
                    args[keyword.arg] = keyword.value

            if args:
                decorator_info['args'] = args

        return decorator_info if 'name' in decorator_info else None

    def _extract_signature(self, func_node) -> str:
        """Extract function signature as string"""
        params = []
        for arg in func_node.args.args:
            if arg.arg == 'self':
                continue

            param_str = arg.arg
            if arg.annotation:
                param_str += f": {ast.unparse(arg.annotation)}"

            # Check for default value
            defaults = func_node.args.defaults
            if defaults:
                # Map defaults to args (defaults are right-aligned)
                arg_index = func_node.args.args.index(arg)
                default_index = arg_index - (len(func_node.args.args) - len(defaults))
                if default_index >= 0:
                    default_value = ast.unparse(defaults[default_index])
                    param_str += f" = {default_value}"

            params.append(param_str)

        return ', '.join(params)

    def _extract_parameters(self, func_node) -> List[Dict[str, Any]]:
        """Extract structured parameter information"""
        parameters = []

        # Get defaults (right-aligned with args)
        defaults = func_node.args.defaults or []
        default_offset = len(func_node.args.args) - len(defaults)

        for i, arg in enumerate(func_node.args.args):
            if arg.arg == 'self':
                continue

            param = {
                'name': arg.arg,
                'type': 'Any',  # Default type
                'has_default': False,
                'default': None,
                'is_required': True
            }

            # Extract type annotation
            if arg.annotation:
                type_str = ast.unparse(arg.annotation)
                param['type'] = type_str
                # Check if Optional
                if 'Optional' in type_str:
                    param['is_required'] = False

            # Check for default value
            default_index = i - default_offset
            if default_index >= 0 and default_index < len(defaults):
                default_node = defaults[default_index]
                param['has_default'] = True
                param['is_required'] = False

                # Extract default value
                if isinstance(default_node, ast.Constant):
                    param['default'] = default_node.value
                else:
                    param['default'] = ast.unparse(default_node)

            parameters.append(param)

        return parameters

    def _class_to_instance_name(self, class_name: str) -> str:
        """Convert ClassName to instance_name (snake_case)"""
        if not class_name:
            return 'service'

        # First letter lowercase
        instance_name = class_name[0].lower() + class_name[1:]
        # Convert camelCase to snake_case
        instance_name = re.sub(r'(?<!^)(?=[A-Z])', '_', instance_name).lower()
        return instance_name

    def _is_custom_type(self, type_str: str) -> bool:
        """Check if a type string represents a custom type that needs importing"""
        builtin_types = {
            'str', 'int', 'bool', 'float', 'list', 'dict', 'tuple', 'set',
            'Any', 'Optional', 'Union', 'List', 'Dict', 'Tuple', 'Set',
            'None', 'bytes', 'object', 'array', 'string', 'number', 'integer', 'boolean', 'null'
        }

        # Extract base type name (handle Optional[Type], List[Type], etc.)
        base_type = type_str.split('[')[0].strip()
        return base_type not in builtin_types
