"""
Type Extractor Module

Pydantic BaseModel 클래스에서 프로퍼티 정보를 추출하는 모듈.
mcp_service_scanner.py에서 import하여 사용.

주요 함수:
- extract_class_properties(file_path): 파일 내 모든 BaseModel 클래스 추출
- extract_single_class(file_path, class_name): 특정 클래스만 추출
- map_python_to_json_type(python_type): Python 타입 → JSON Schema 타입 변환
"""

from __future__ import annotations

import ast
from typing import Any, Dict, List, Optional


def map_python_to_json_type(python_type: str) -> str:
    """Map Python type to JSON Schema type.

    Args:
        python_type: Python type string (e.g., "str", "int", "List")

    Returns:
        JSON Schema type string (e.g., "string", "integer", "array")
    """
    type_mapping = {
        "str": "string",
        "int": "integer",
        "float": "number",
        "bool": "boolean",
        "list": "array",
        "dict": "object",
        "List": "array",
        "Dict": "object",
        "Any": "any",
        "None": "null",
        "Optional": "any",
    }
    return type_mapping.get(python_type, "object")


def extract_type_from_annotation(annotation: Optional[ast.AST]) -> str:
    """Extract type string from AST annotation node.

    Args:
        annotation: AST annotation node

    Returns:
        JSON Schema compatible type string
    """
    if annotation is None:
        return "any"

    # Handle Optional[T]
    if isinstance(annotation, ast.Subscript):
        if hasattr(annotation.value, "id") and annotation.value.id == "Optional":
            if isinstance(annotation.slice, ast.Name):
                return map_python_to_json_type(annotation.slice.id)
            else:
                # Recursive call already returns JSON type, don't re-map
                return extract_type_from_annotation(annotation.slice)

        # Handle List[T]
        elif hasattr(annotation.value, "id") and annotation.value.id == "List":
            return "array"

        # Handle Union types
        elif hasattr(annotation.value, "id") and annotation.value.id == "Union":
            # Check if Union contains List - if so, treat as array
            # e.g., Union[str, List[str]] -> array (single value can be wrapped in list)
            if isinstance(annotation.slice, ast.Tuple):
                has_list = False
                first_type = None
                for elt in annotation.slice.elts:
                    if isinstance(elt, ast.Subscript):
                        if hasattr(elt.value, "id") and elt.value.id == "List":
                            has_list = True
                            break
                    elif isinstance(elt, ast.Name) and elt.id != "None":
                        if first_type is None:
                            first_type = elt.id

                if has_list:
                    return "array"
                elif first_type:
                    return map_python_to_json_type(first_type)
            return "any"

        # Handle Literal types
        elif hasattr(annotation.value, "id") and annotation.value.id == "Literal":
            return "string"  # Literals are typically string enums

    # Handle simple types
    elif isinstance(annotation, ast.Name):
        return map_python_to_json_type(annotation.id)

    elif isinstance(annotation, ast.Constant):
        return map_python_to_json_type(type(annotation.value).__name__)

    return "any"


def extract_field_info(node: ast.AnnAssign, class_name: str) -> Optional[Dict[str, Any]]:
    """Extract field information from a Pydantic Field assignment.

    Args:
        node: AST AnnAssign node (annotated assignment)
        class_name: Name of the containing class

    Returns:
        Dictionary with field metadata or None if not a valid field
    """
    if not isinstance(node.target, ast.Name):
        return None

    field_name = node.target.id
    field_info = {
        "name": field_name,
        "type": extract_type_from_annotation(node.annotation),
        "description": "",
        "examples": [],
        "default": None,
    }

    # Extract Field() parameters
    if isinstance(node.value, ast.Call):
        if hasattr(node.value.func, "id") and node.value.func.id == "Field":
            # Process Field arguments
            for i, arg in enumerate(node.value.args):
                if i == 0:  # First positional arg is default value
                    if isinstance(arg, ast.Constant):
                        # Handle Ellipsis (...) - convert to None
                        if arg.value is ...:
                            field_info["default"] = None
                        else:
                            field_info["default"] = arg.value

            # Process keyword arguments
            for keyword in node.value.keywords:
                if keyword.arg == "description" and isinstance(keyword.value, ast.Constant):
                    field_info["description"] = keyword.value.value
                elif keyword.arg == "examples" and isinstance(keyword.value, ast.List):
                    examples = []
                    for elt in keyword.value.elts:
                        if isinstance(elt, ast.Constant):
                            examples.append(elt.value)
                        elif isinstance(elt, ast.List):
                            # Handle list of lists
                            inner_list = []
                            for inner_elt in elt.elts:
                                if isinstance(inner_elt, ast.Constant):
                                    inner_list.append(inner_elt.value)
                            if inner_list:
                                examples.append(inner_list)
                    field_info["examples"] = examples
                elif keyword.arg == "default" and isinstance(keyword.value, ast.Constant):
                    field_info["default"] = keyword.value.value

    return field_info


def extract_class_properties(file_path: str) -> Dict[str, Dict[str, Any]]:
    """Extract properties from all Pydantic BaseModel classes in a file.

    Args:
        file_path: Path to Python source file

    Returns:
        Dictionary mapping class names to their metadata:
        {
            "ClassName": {
                "file": "/path/to/file.py",
                "line": 15,
                "properties": [
                    {"name": "field1", "type": "string", ...},
                    ...
                ]
            }
        }
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)
    classes_info: Dict[str, Dict[str, Any]] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check if it's a BaseModel subclass
            is_base_model = False
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == "BaseModel":
                    is_base_model = True
                    break

            if is_base_model:
                class_properties = []

                # Extract field definitions
                for item in node.body:
                    if isinstance(item, ast.AnnAssign):
                        field_info = extract_field_info(item, node.name)
                        if field_info and not field_info["name"].startswith("_"):
                            # Skip private/internal fields
                            class_properties.append(field_info)

                classes_info[node.name] = {
                    "file": file_path,
                    "line": node.lineno,
                    "properties": class_properties,
                }

    return classes_info


def extract_single_class(file_path: str, class_name: str) -> Optional[Dict[str, Any]]:
    """Extract properties from a specific class in a file.

    Args:
        file_path: Path to Python source file
        class_name: Name of the class to extract

    Returns:
        Class metadata dictionary or None if not found:
        {
            "file": "/path/to/file.py",
            "line": 15,
            "properties": [...]
        }
    """
    all_classes = extract_class_properties(file_path)
    return all_classes.get(class_name)


def get_class_names_from_file(file_path: str) -> List[str]:
    """Get list of BaseModel class names defined in a file.

    Args:
        file_path: Path to Python source file

    Returns:
        List of class names
    """
    all_classes = extract_class_properties(file_path)
    return list(all_classes.keys())
