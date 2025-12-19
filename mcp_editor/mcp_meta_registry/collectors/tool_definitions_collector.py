"""
Tool definitions collector - loads MCP_TOOLS from .py/.json files
"""
import ast
import json
from typing import Dict, Any, List
from pathlib import Path
from .base import BaseCollector, CollectorContext


class ToolDefinitionsCollector(BaseCollector):
    """Collector for loading MCP tool definitions from template files"""

    def collect(self, ctx: CollectorContext) -> Dict[str, Any]:
        """Load MCP_TOOLS from the specified tools_path"""
        if not ctx.tools_path or not ctx.tools_path.exists():
            return self.collect_minimal(ctx)

        try:
            tools = self._load_tool_definitions(ctx.tools_path)
            return {
                'tools': tools,
                'tools_count': len(tools),
                'tools_path': str(ctx.tools_path)
            }
        except Exception as e:
            print(f"Warning: Failed to load tool definitions from {ctx.tools_path}: {e}")
            return self.collect_minimal(ctx)

    def collect_minimal(self, ctx: CollectorContext) -> Dict[str, Any]:
        """Return minimal valid structure"""
        return {
            'tools': [],
            'tools_count': 0,
            'tools_path': str(ctx.tools_path) if ctx.tools_path else None
        }

    def validate(self, metadata: Dict[str, Any]) -> bool:
        """Validate that tools were loaded correctly"""
        if 'tools' not in metadata:
            return False

        tools = metadata['tools']
        if not isinstance(tools, list):
            return False

        # Each tool should have at least a name and inputSchema
        for tool in tools:
            if not isinstance(tool, dict):
                return False
            if 'name' not in tool:
                return False

        return True

    def _load_tool_definitions(self, tool_def_path: Path) -> List[Dict[str, Any]]:
        """Load tool definitions from a Python module or JSON file (reused from generate_outlook_server.py)"""
        if tool_def_path.suffix == '.json':
            # Load from JSON file
            with open(tool_def_path, 'r') as f:
                data = json.load(f)
                return data.get('MCP_TOOLS', data)

        elif tool_def_path.suffix == '.py':
            # Use AST to parse the file without importing
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

            with open(tool_def_path, 'r') as f:
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
            raise ValueError(f"Unsupported file type: {tool_def_path.suffix}. Use .py or .json")