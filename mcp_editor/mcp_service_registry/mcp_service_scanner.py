"""
MCP Service Scanner - Multi-language code analyzer for @mcp_service decorators.

This module scans Python and JavaScript source code to find functions decorated
with @mcp_service (Python) or @McpService (JavaScript), extracts their signatures
and metadata, and exports them to JSON format.

Supported languages:
- Python (.py): Uses built-in ast module
- JavaScript (.js, .mjs): Uses esprima parser
- TypeScript (.ts): Uses esprima parser (basic support)

Core functionality:
- Language detection based on file extension
- AST parsing for each language
- Function signature extraction (parameters, types, defaults)
- Decorator metadata extraction (server_name, tool_name, etc.)
- JSON export for web editor consumption
"""

from __future__ import annotations

import ast
import re
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# JavaScript parser (optional - graceful fallback if not installed)
try:
    import esprima
    ESPRIMA_AVAILABLE = True
except ImportError:
    ESPRIMA_AVAILABLE = False
    esprima = None

DEFAULT_SKIP_PARTS = ("venv", "__pycache__", ".git", "node_modules", "backups")


class Language(Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    UNKNOWN = "unknown"


def detect_language(file_path: Path) -> Language:
    """Detect programming language from file extension."""
    ext = file_path.suffix.lower()
    if ext == ".py":
        return Language.PYTHON
    elif ext in (".js", ".mjs"):
        return Language.JAVASCRIPT
    elif ext in (".ts", ".tsx"):
        return Language.TYPESCRIPT
    return Language.UNKNOWN


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


def _is_class_type(type_str: str) -> bool:
    """Check if type is a custom class (not a primitive or generic type).

    Custom class types:
    - Start with uppercase letter
    - Don't start with generic prefixes (List, Dict, Union, Optional, etc.)
    - Are not Python primitives (str, int, float, bool, None, Any)
    """
    if not type_str or not type_str[0].isupper():
        return False

    # Generic type prefixes (keep as-is, not class types)
    generic_prefixes = ("List[", "Dict[", "Union[", "Optional[", "Set[", "Tuple[", "Callable[")
    if any(type_str.startswith(prefix) for prefix in generic_prefixes):
        return False

    # Python/typing primitives that start with uppercase
    primitives = ("None", "Any", "NoReturn", "Type", "Literal")
    if type_str in primitives:
        return False

    # If it's a simple identifier starting with uppercase, it's likely a class
    # e.g., FilterParams, EventSelectParams, QueryMethod
    return True


def _parse_type_info(type_str: Optional[str]) -> Dict[str, Any]:
    """Parse type string to extract base type, class name, and optional flag.

    Returns:
        - base_type: JSON Schema compatible type (object, string, etc.) or generic type
        - class_name: Original class name if type is a custom class, else None
        - is_optional: True if type was Optional[...]

    Examples:
        'Optional[str]' -> {'base_type': 'str', 'class_name': None, 'is_optional': True}
        'str' -> {'base_type': 'str', 'class_name': None, 'is_optional': False}
        'Optional[FilterParams]' -> {'base_type': 'object', 'class_name': 'FilterParams', 'is_optional': True}
        'FilterParams' -> {'base_type': 'object', 'class_name': 'FilterParams', 'is_optional': False}
        'List[str]' -> {'base_type': 'List[str]', 'class_name': None, 'is_optional': False}
    """
    if type_str is None:
        return {"base_type": None, "class_name": None, "is_optional": False}

    is_optional = False
    inner_type = type_str

    # Check for Optional[...]
    if type_str.startswith("Optional[") and type_str.endswith("]"):
        inner_type = type_str[9:-1]  # Remove 'Optional[' and ']'
        is_optional = True

    # Check if inner type is a custom class
    if _is_class_type(inner_type):
        return {"base_type": "object", "class_name": inner_type, "is_optional": is_optional}

    return {"base_type": inner_type, "class_name": None, "is_optional": is_optional}


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
    - type: JSON Schema compatible type (object for classes, or base type)
    - class_name: original class name if type is a custom class (optional field)
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

        # Parse type to extract base_type, class_name, and is_optional
        raw_type = _annotation_to_str(arg.annotation)
        type_info = _parse_type_info(raw_type)

        # Parameter is optional if type is Optional[...] or has a default value
        is_optional = type_info["is_optional"] or has_default

        # Build param dict with class_name right after type (if exists)
        param_dict = {"name": arg.arg, "type": type_info["base_type"]}
        if type_info["class_name"]:
            param_dict["class_name"] = type_info["class_name"]
        param_dict["is_optional"] = is_optional
        param_dict["default"] = default_val
        param_dict["has_default"] = has_default

        params.append(param_dict)

    # *args
    if args.vararg:
        vararg_type = _annotation_to_str(args.vararg.annotation)
        vararg_type_info = _parse_type_info(vararg_type)
        vararg_dict = {"name": f"*{args.vararg.arg}", "type": vararg_type_info["base_type"]}
        if vararg_type_info["class_name"]:
            vararg_dict["class_name"] = vararg_type_info["class_name"]
        vararg_dict["is_optional"] = True  # *args is always optional
        vararg_dict["default"] = None
        vararg_dict["has_default"] = False
        params.append(vararg_dict)

    # **kwargs
    if args.kwarg:
        kwarg_type = _annotation_to_str(args.kwarg.annotation)
        kwarg_type_info = _parse_type_info(kwarg_type)
        kwarg_dict = {"name": f"**{args.kwarg.arg}", "type": kwarg_type_info["base_type"]}
        if kwarg_type_info["class_name"]:
            kwarg_dict["class_name"] = kwarg_type_info["class_name"]
        kwarg_dict["is_optional"] = True  # **kwargs is always optional
        kwarg_dict["default"] = None
        kwarg_dict["has_default"] = False
        params.append(kwarg_dict)

    return params


def signature_from_parameters(params: List[Dict[str, Any]]) -> str:
    """Build a signature string like 'param: str, other: int = 1' from param metadata.

    Uses is_optional to determine if type should be wrapped in Optional[...].
    Uses class_name for display if available (to show original Python class name).
    """
    parts: List[str] = []
    for param in params:
        name = param.get("name", "")
        if not name or name == "self":
            continue

        param_str = name
        # Use class_name for display if available, otherwise use type
        type_str = param.get("class_name") or param.get("type")
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
                "language": "python",
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
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


# =============================================================================
# JavaScript/TypeScript Parser
# =============================================================================

def _extract_js_decorator_metadata(decorator_node: dict) -> Dict[str, Any]:
    """Extract metadata from JavaScript decorator call.

    Handles patterns like:
    - @McpService({ serverName: "outlook", description: "..." })
    - @mcp_service({ server_name: "outlook" })
    """
    metadata: Dict[str, Any] = {}

    if not decorator_node:
        return metadata

    # Get the arguments of the decorator call
    arguments = decorator_node.get("arguments", [])
    if not arguments:
        return metadata

    # First argument should be an object expression
    first_arg = arguments[0]
    if first_arg.get("type") != "ObjectExpression":
        return metadata

    # Extract properties from the object
    for prop in first_arg.get("properties", []):
        if prop.get("type") != "Property":
            continue

        key = prop.get("key", {})
        value = prop.get("value", {})

        # Get property name
        key_name = key.get("name") or key.get("value")
        if not key_name:
            continue

        # Convert camelCase to snake_case for consistency
        snake_key = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', key_name).lower()

        # Get property value
        if value.get("type") == "Literal":
            metadata[snake_key] = value.get("value")
        elif value.get("type") == "ArrayExpression":
            elements = value.get("elements", [])
            metadata[snake_key] = [
                el.get("value") for el in elements
                if el.get("type") == "Literal"
            ]

    return metadata


def _extract_js_parameters(func_node: dict) -> List[Dict[str, Any]]:
    """Extract parameters from JavaScript function node."""
    params: List[Dict[str, Any]] = []

    js_params = func_node.get("params", [])

    for param in js_params:
        param_info = {
            "name": None,
            "type": None,
            "is_optional": False,
            "default": None,
            "has_default": False,
        }

        # Handle different parameter types
        if param.get("type") == "Identifier":
            param_info["name"] = param.get("name")
        elif param.get("type") == "AssignmentPattern":
            # Parameter with default value
            left = param.get("left", {})
            right = param.get("right", {})
            param_info["name"] = left.get("name")
            param_info["has_default"] = True
            param_info["is_optional"] = True
            if right.get("type") == "Literal":
                param_info["default"] = right.get("value")
        elif param.get("type") == "RestElement":
            # ...args
            argument = param.get("argument", {})
            param_info["name"] = f"...{argument.get('name', 'args')}"
            param_info["is_optional"] = True

        if param_info["name"]:
            params.append(param_info)

    return params


def _js_signature_from_parameters(params: List[Dict[str, Any]]) -> str:
    """Build signature string from JavaScript parameters."""
    parts: List[str] = []
    for param in params:
        name = param.get("name", "")
        if not name:
            continue

        param_str = name
        if param.get("has_default"):
            default = param.get("default")
            if isinstance(default, str):
                param_str += f' = "{default}"'
            elif default is not None:
                param_str += f" = {default}"
            else:
                param_str += " = null"

        parts.append(param_str)

    return ", ".join(parts)


def find_mcp_services_in_js_file(file_path: str) -> Dict[str, Dict[str, Any]]:
    """Find all @McpService or @mcp_service decorated functions in JavaScript/TypeScript file."""
    if not ESPRIMA_AVAILABLE:
        print(f"Warning: esprima not installed, skipping JS file: {file_path}")
        return {}

    services: Dict[str, Dict[str, Any]] = {}

    try:
        content = Path(file_path).read_text(encoding="utf-8")

        # Parse with esprima
        tree = esprima.parseScript(content, {"tolerant": True, "loc": True})

        # Find decorated functions
        for node in tree.body:
            _process_js_node(node, file_path, services)

    except Exception as exc:
        print(f"Error parsing JS file {file_path}: {exc}")

    return services


def _process_js_node(node: dict, file_path: str, services: Dict[str, Dict[str, Any]], class_name: str = None):
    """Process a JavaScript AST node to find MCP services."""
    node_type = node.get("type") if isinstance(node, dict) else getattr(node, "type", None)

    # Convert esprima node to dict if needed
    if hasattr(node, "toDict"):
        node = node.toDict()
    elif not isinstance(node, dict):
        node = vars(node) if hasattr(node, "__dict__") else {}

    # Handle class declarations
    if node_type == "ClassDeclaration":
        class_name = node.get("id", {}).get("name")
        body = node.get("body", {}).get("body", [])
        for item in body:
            _process_js_node(item, file_path, services, class_name)
        return

    # Handle method definitions in classes
    if node_type == "MethodDefinition":
        decorators = node.get("decorators", [])
        func_node = node.get("value", {})
        func_name = node.get("key", {}).get("name")
        _check_js_mcp_service(decorators, func_node, func_name, file_path, services, class_name)
        return

    # Handle function declarations
    if node_type == "FunctionDeclaration":
        # Check for decorators (experimental syntax)
        decorators = node.get("decorators", [])
        func_name = node.get("id", {}).get("name")
        _check_js_mcp_service(decorators, node, func_name, file_path, services, class_name)
        return

    # Handle exported functions
    if node_type == "ExportNamedDeclaration":
        declaration = node.get("declaration", {})
        if declaration:
            _process_js_node(declaration, file_path, services, class_name)
        return

    # Handle variable declarations (arrow functions)
    if node_type == "VariableDeclaration":
        for decl in node.get("declarations", []):
            init = decl.get("init", {})
            if init and init.get("type") in ("ArrowFunctionExpression", "FunctionExpression"):
                func_name = decl.get("id", {}).get("name")
                decorators = node.get("decorators", [])
                _check_js_mcp_service(decorators, init, func_name, file_path, services, class_name)


def _check_js_mcp_service(decorators: list, func_node: dict, func_name: str,
                           file_path: str, services: Dict[str, Dict[str, Any]],
                           class_name: str = None):
    """Check if function has MCP service decorator and extract info."""
    if not func_name:
        return

    # Look for @McpService or @mcp_service decorator
    mcp_decorator = None
    for dec in decorators or []:
        dec_name = None
        if dec.get("type") == "Identifier":
            dec_name = dec.get("name")
        elif dec.get("type") == "CallExpression":
            callee = dec.get("callee", {})
            dec_name = callee.get("name")

        if dec_name in ("McpService", "mcp_service", "McpTool"):
            mcp_decorator = dec
            break

    if not mcp_decorator:
        return

    # Extract metadata
    if mcp_decorator.get("type") == "CallExpression":
        metadata = _extract_js_decorator_metadata(mcp_decorator)
    else:
        metadata = {}

    # Extract parameters
    params = _extract_js_parameters(func_node)
    signature = _js_signature_from_parameters(params)

    # Get line number
    loc = func_node.get("loc", {})
    line = loc.get("start", {}).get("line", 0) if loc else 0

    service_info = {
        "function_name": func_name,
        "metadata": metadata,
        "signature": signature,
        "parameters": params,
        "is_async": func_node.get("async", False),
        "file": str(file_path),
        "line": line,
        "language": "javascript",
    }

    if class_name:
        service_info["class"] = class_name
        service_info["instance"] = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', class_name).lower()
        service_info["module"] = Path(file_path).stem
        service_info["method"] = func_name

    services[func_name] = service_info


# =============================================================================
# Unified File Scanner
# =============================================================================

def find_mcp_services_in_file(file_path: str) -> Dict[str, Dict[str, Any]]:
    """Find all @mcp_service decorated functions in a file (Python or JavaScript)."""
    path = Path(file_path)
    language = detect_language(path)

    if language == Language.PYTHON:
        return find_mcp_services_in_python_file(file_path)
    elif language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
        return find_mcp_services_in_js_file(file_path)
    else:
        return {}


def find_mcp_services_in_python_file(file_path: str) -> Dict[str, Dict[str, Any]]:
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
    languages: Optional[List[str]] = None,
) -> Dict[str, Dict[str, Any]]:
    """Scan a codebase recursively for @mcp_service decorated functions.

    Args:
        base_dir: Base directory to scan
        server_name: Optional filter by server name
        exclude_examples: Skip example files
        skip_parts: Directory parts to skip
        languages: List of languages to scan ("python", "javascript", "typescript")
                   If None, scans all supported languages

    Returns:
        Dictionary of service name to service info
    """
    all_services: Dict[str, Dict[str, Any]] = {}

    # Determine which file extensions to scan
    extensions = []
    if languages is None:
        # Scan all supported languages
        extensions = [".py", ".js", ".mjs", ".ts", ".tsx"]
    else:
        if "python" in languages:
            extensions.append(".py")
        if "javascript" in languages:
            extensions.extend([".js", ".mjs"])
        if "typescript" in languages:
            extensions.extend([".ts", ".tsx"])

    # Scan files for each extension
    for ext in extensions:
        pattern = f"*{ext}"
        for source_file in Path(base_dir).rglob(pattern):
            if _should_skip(source_file, skip_parts):
                continue
            if exclude_examples and "example" in str(source_file).lower():
                continue

            services = find_mcp_services_in_file(str(source_file))

            if server_name:
                services = {
                    name: info for name, info in services.items()
                    if info["metadata"].get("server_name") == server_name
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
