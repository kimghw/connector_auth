"""
MCP Service Scanner - AST-based code analyzer for @mcp_service decorators.

This module scans Python source code to find functions decorated with @mcp_service,
extracts their signatures and metadata, and exports them to JSON format.

Core functionality:
- AST parsing to find @mcp_service decorated functions
- Function signature extraction (parameters, types, defaults)
- Decorator metadata extraction (server_name, tool_name, etc.)
- JSON export for web editor consumption

This consolidates logic previously duplicated in:
- legacy mcp_service_extractor.py (signature extraction, now removed)
- extract_real_mcp_services.py (JSON export)
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_SKIP_PARTS = ("venv", "__pycache__", ".git", "node_modules", "backups")


def _should_skip(path: Path, skip_parts: tuple[str, ...] = DEFAULT_SKIP_PARTS) -> bool:
    """Check whether a path should be skipped based on directory parts."""
    return any(part in path.parts for part in skip_parts)


def extract_decorator_metadata(decorator: ast.Call) -> Dict[str, Any]:
    """Extract metadata from @mcp_service decorator call."""
    metadata: Dict[str, Any] = {}

    for keyword in decorator.keywords:
        if isinstance(keyword.value, ast.Constant):
            metadata[keyword.arg] = keyword.value.value
        elif isinstance(keyword.value, ast.List):
            values: List[Any] = []
            for element in keyword.value.elts:
                if isinstance(element, ast.Constant):
                    values.append(element.value)
            metadata[keyword.arg] = values
        elif isinstance(keyword.value, ast.Name):
            metadata[keyword.arg] = keyword.value.id

    return metadata


def _annotation_to_str(annotation: Optional[ast.AST]) -> Optional[str]:
    if annotation is None:
        return None
    try:
        return ast.unparse(annotation)
    except Exception:
        return None


def _parse_type_info(type_str: Optional[str]) -> Dict[str, Any]:
    """Parse type string to extract base type and optional flag.

    Examples:
        'Optional[str]' -> {'base_type': 'str', 'is_optional': True}
        'str' -> {'base_type': 'str', 'is_optional': False}
        'Optional[FilterParams]' -> {'base_type': 'FilterParams', 'is_optional': True}
        'List[str]' -> {'base_type': 'List[str]', 'is_optional': False}
    """
    if type_str is None:
        return {"base_type": None, "is_optional": False}

    # Check for Optional[...]
    if type_str.startswith("Optional[") and type_str.endswith("]"):
        inner_type = type_str[9:-1]  # Remove 'Optional[' and ']'
        return {"base_type": inner_type, "is_optional": True}

    return {"base_type": type_str, "is_optional": False}


def _default_to_value(node: ast.AST) -> Any:
    """Convert an AST default value to a JSON-serializable value or string."""
    if isinstance(node, ast.Constant):
        return node.value
    try:
        return ast.unparse(node)
    except Exception:
        return None


def _extract_parameters(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> List[Dict[str, Any]]:
    """Extract parameter info from a function definition.

    Returns parameters with unified structure:
    - name: parameter name
    - type: base type only (without Optional wrapper)
    - is_optional: True if type was Optional[...] or has default value
    - default: default value if any
    - has_default: True if parameter has a default value
    """
    args = func_node.args
    params: List[Dict[str, Any]] = []

    # Regular arguments
    defaults_offset = len(args.args) - len(args.defaults)
    for i, arg in enumerate(args.args):
        if arg.arg == "self":
            continue
        default_idx = i - defaults_offset
        has_default = default_idx >= 0
        default_val = None
        if has_default and default_idx < len(args.defaults):
            default_val = _default_to_value(args.defaults[default_idx])

        # Parse type to extract base_type and is_optional
        raw_type = _annotation_to_str(arg.annotation)
        type_info = _parse_type_info(raw_type)

        # Parameter is optional if type is Optional[...] or has a default value
        is_optional = type_info["is_optional"] or has_default

        params.append(
            {
                "name": arg.arg,
                "type": type_info["base_type"],
                "is_optional": is_optional,
                "is_required": not is_optional,  # Add is_required for compatibility
                "default": default_val,
                "has_default": has_default,
            }
        )

    # *args
    if args.vararg:
        vararg_type = _annotation_to_str(args.vararg.annotation)
        vararg_type_info = _parse_type_info(vararg_type)
        params.append(
            {
                "name": f"*{args.vararg.arg}",
                "type": vararg_type_info["base_type"],
                "is_optional": True,  # *args is always optional
                "default": None,
                "has_default": False,
            }
        )

    # **kwargs
    if args.kwarg:
        kwarg_type = _annotation_to_str(args.kwarg.annotation)
        kwarg_type_info = _parse_type_info(kwarg_type)
        params.append(
            {
                "name": f"**{args.kwarg.arg}",
                "type": kwarg_type_info["base_type"],
                "is_optional": True,  # **kwargs is always optional
                "default": None,
                "has_default": False,
            }
        )

    return params


def signature_from_parameters(params: List[Dict[str, Any]]) -> str:
    """Build a signature string like 'param: str, other: int = 1' from param metadata.

    Uses is_optional to determine if type should be wrapped in Optional[...].
    """
    parts: List[str] = []
    for param in params:
        name = param.get("name", "")
        if not name or name == "self":
            continue

        param_str = name
        type_str = param.get("type")
        is_optional = param.get("is_optional", False)
        default = param.get("default")
        has_default = param.get("has_default", False)

        if type_str:
            # Wrap in Optional if is_optional but don't double-wrap
            if is_optional and not type_str.startswith("Optional["):
                param_str += f": Optional[{type_str}]"
            else:
                param_str += f": {type_str}"

        if has_default:
            if (
                isinstance(default, str)
                and not default.startswith(("'", '"'))
                and " " not in default
                and not default.startswith("[")
            ):  # noqa: E501
                param_str += f' = "{default}"'
            elif default is not None:
                param_str += f" = {default}"
            else:
                param_str += " = None"

        parts.append(param_str)

    return ", ".join(parts)


class MCPServiceExtractor(ast.NodeVisitor):
    """Extract MCP services with class context."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.services: Dict[str, Dict[str, Any]] = {}
        self.current_class = None

    def visit_ClassDef(self, node):
        """Track current class context."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node):
        """Process function definitions."""
        self._process_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        """Process async function definitions."""
        self._process_function(node)
        self.generic_visit(node)

    def _process_function(self, node):
        """Extract MCP service info from function."""
        for decorator in node.decorator_list:
            is_mcp_service = False
            metadata: Dict[str, Any] = {}

            if isinstance(decorator, ast.Name) and decorator.id == "mcp_service":
                is_mcp_service = True
            elif (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Name)
                and decorator.func.id == "mcp_service"
            ):
                is_mcp_service = True
                metadata = extract_decorator_metadata(decorator)

            if not is_mcp_service:
                continue

            params = _extract_parameters(node)
            signature = signature_from_parameters(params)

            service_info = {
                "function_name": node.name,
                "metadata": metadata,
                "signature": signature,
                "parameters": params,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "file": str(self.file_path),
                "line": node.lineno,
            }

            # Add class info if function is a method
            if self.current_class:
                service_info["class"] = self.current_class
                # Convert class name to snake_case for instance name
                service_info["instance"] = self._to_snake_case(self.current_class)
                service_info["module"] = Path(self.file_path).stem
                service_info["method"] = node.name

            self.services[node.name] = service_info
            break

    def _to_snake_case(self, name: str) -> str:
        """Convert CamelCase to snake_case."""
        import re

        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def find_mcp_services_in_file(file_path: str) -> Dict[str, Dict[str, Any]]:
    """Find all @mcp_service decorated functions in a Python file."""
    try:
        content = Path(file_path).read_text(encoding="utf-8")
        tree = ast.parse(content)

        extractor = MCPServiceExtractor(file_path)
        extractor.visit(tree)

        return extractor.services
    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"Error parsing {file_path}: {exc}")
        return {}


def scan_codebase_for_mcp_services(
    base_dir: str,
    server_name: Optional[str] = None,
    exclude_examples: bool = True,
    skip_parts: tuple[str, ...] = DEFAULT_SKIP_PARTS,
) -> Dict[str, Dict[str, Any]]:
    """Scan a codebase recursively for @mcp_service decorated functions."""
    all_services: Dict[str, Dict[str, Any]] = {}

    for py_file in Path(base_dir).rglob("*.py"):
        if _should_skip(py_file, skip_parts):
            continue
        if exclude_examples and "example" in str(py_file).lower():
            continue

        services = find_mcp_services_in_file(str(py_file))

        if server_name:
            services = {
                name: info for name, info in services.items() if info["metadata"].get("server_name") == server_name
            }

        all_services.update(services)

    return all_services


def get_signatures_by_name(base_dir: str, server_name: Optional[str] = None) -> Dict[str, str]:
    """Return {service_name: signature_string} map."""
    services = scan_codebase_for_mcp_services(base_dir, server_name)
    return {name: info["signature"] for name, info in services.items()}


def get_services_map(base_dir: str, server_name: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """Return {service_name: {signature, parameters, metadata, ...}} map."""
    return scan_codebase_for_mcp_services(base_dir, server_name)


def export_services_to_json(base_dir: str, server_name: str, output_dir: str) -> Dict[str, str]:
    """
    Export services to registry_{server_name}.json format used by the web editor.
    The registry format is compatible with tool_editor_web.py's load_services_from_registry().
    """
    import json
    from datetime import datetime

    services = scan_codebase_for_mcp_services(base_dir, server_name)
    services_items = sorted(services.items(), key=lambda item: (item[1]["file"], item[1]["line"]))

    # Build registry format (used by web editor)
    registry_output = {
        "version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "server_name": server_name,
        "services": {}
    }

    for name, service in services_items:
        service_name = service.get("metadata", {}).get("service_name", name)
        registry_output["services"][service_name] = {
            "service_name": service_name,
            "handler": {
                "class_name": service.get("class"),
                "module_path": f"mcp_{server_name}.{service.get('module', f'{server_name}_service')}",
                "instance": service.get("instance"),
                "method": service.get("method", name),
                "is_async": service.get("is_async", True),
                "file": str(Path(service.get("file", "")).resolve()),
                "line": service.get("line", 0)
            },
            "signature": service.get("signature", ""),
            "parameters": service.get("parameters", []),
            "metadata": service.get("metadata", {})
        }

    # Save registry file directly in output_dir (no subfolder)
    output_dir_path = Path(output_dir)
    registry_path = output_dir_path / f"registry_{server_name}.json"
    registry_path.write_text(json.dumps(registry_output, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "registry": str(registry_path),
        "count": len(registry_output["services"])
    }
