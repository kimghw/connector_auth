"""
Pydantic models collector - collects and analyzes Pydantic BaseModel types
"""
import ast
from typing import Dict, Any, Set, List
from pathlib import Path
from .base import BaseCollector, CollectorContext


class PydanticModelsCollector(BaseCollector):
    """Collector for Pydantic BaseModel types and parameter types"""

    def collect(self, ctx: CollectorContext) -> Dict[str, Any]:
        """Collect parameter types from type files and tools"""
        param_types = set()

        # Collect from type files if specified
        if ctx.types_files:
            for type_file in ctx.types_files:
                if type_file and type_file.exists():
                    types_from_file = self._extract_types_from_file(type_file)
                    param_types.update(types_from_file)

        return {
            'param_types': sorted(param_types),
            'types_files': [str(f) for f in ctx.types_files] if ctx.types_files else []
        }

    def collect_minimal(self, ctx: CollectorContext) -> Dict[str, Any]:
        """Return minimal valid structure"""
        return {
            'param_types': [],
            'types_files': []
        }

    def validate(self, metadata: Dict[str, Any]) -> bool:
        """Validate parameter types structure"""
        if 'param_types' not in metadata:
            return False

        param_types = metadata['param_types']
        if not isinstance(param_types, list):
            return False

        # Each type should be a string
        for param_type in param_types:
            if not isinstance(param_type, str):
                return False

        return True

    def collect_from_tools_and_args(self, tools: List[Dict[str, Any]],
                                   internal_args: Dict[str, Any]) -> Set[str]:
        """
        Collect all parameter types from tools and internal args.
        This method is called by the registry to augment types from files.
        """
        types = set()

        # JSON schema types that should NOT be imported (they are Python built-ins or schema keywords)
        EXCLUDED_TYPES = {'object', 'array', 'string', 'number', 'integer', 'boolean', 'null'}

        # Collect from tool inputSchema
        for tool in tools:
            schema = tool.get('inputSchema', {})
            properties = schema.get('properties', {})
            for prop_name, prop_schema in properties.items():
                if prop_schema.get('type') == 'object':
                    base_model = prop_schema.get('baseModel')
                    if base_model and base_model not in EXCLUDED_TYPES:
                        types.add(base_model)

        # Collect from internal args
        for tool_name, params in internal_args.items():
            for param_name, param_info in params.items():
                param_type = param_info.get('type')
                # Only add actual class names, not JSON schema types
                if param_type and param_type not in EXCLUDED_TYPES:
                    types.add(param_type)

        return types

    def _extract_types_from_file(self, type_file: Path) -> Set[str]:
        """Extract BaseModel class names from a Python file"""
        types = set()

        try:
            with open(type_file, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            # Find all class definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it inherits from BaseModel or has Pydantic-like structure
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            if 'BaseModel' in base.id or 'Model' in base.id:
                                types.add(node.name)
                        elif isinstance(base, ast.Attribute):
                            if 'BaseModel' in base.attr:
                                types.add(node.name)

                    # Also include classes with Field annotations (common Pydantic pattern)
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign):
                            # Check if using Field() or has type annotations
                            if item.value:
                                if isinstance(item.value, ast.Call):
                                    if isinstance(item.value.func, ast.Name):
                                        if item.value.func.id == 'Field':
                                            types.add(node.name)
                                            break

        except Exception as e:
            print(f"Warning: Failed to extract types from {type_file}: {e}")

        return types

    def merge_param_types(self, *type_sets: Set[str]) -> List[str]:
        """Merge multiple sets of parameter types and return sorted list"""
        merged = set()
        for type_set in type_sets:
            if type_set:
                merged.update(type_set)

        # Add common Outlook types if GraphMailQuery is being used
        # This ensures compatibility even if type files are missing
        if any('GraphMailQuery' in str(s) for s in type_sets):
            merged.update(['FilterParams', 'ExcludeParams', 'SelectParams'])

        return sorted(merged)