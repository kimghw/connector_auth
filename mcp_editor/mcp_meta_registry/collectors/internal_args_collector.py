"""
Internal args collector - loads and enriches tool_internal_args.json
"""
import json
from typing import Dict, Any, Optional
from pathlib import Path
from .base import BaseCollector, CollectorContext


class InternalArgsCollector(BaseCollector):
    """Collector for loading and enriching internal args"""

    def collect(self, ctx: CollectorContext) -> Dict[str, Any]:
        """Load internal args from JSON file and enrich with defaults"""
        internal_args_path = self._find_internal_args_file(ctx)
        if not internal_args_path:
            return self.collect_minimal(ctx)

        try:
            internal_args_raw = self._load_internal_args(internal_args_path)
            internal_args = self._enrich_internal_args_with_defaults(internal_args_raw)

            return {
                'internal_args': internal_args,
                'internal_args_path': str(internal_args_path),
                'tools_with_internal_args': list(internal_args.keys())
            }
        except Exception as e:
            print(f"Warning: Failed to load internal args from {internal_args_path}: {e}")
            return self.collect_minimal(ctx)

    def collect_minimal(self, ctx: CollectorContext) -> Dict[str, Any]:
        """Return minimal valid structure"""
        return {
            'internal_args': {},
            'internal_args_path': None,
            'tools_with_internal_args': []
        }

    def validate(self, metadata: Dict[str, Any]) -> bool:
        """Validate internal args structure"""
        if 'internal_args' not in metadata:
            return False

        internal_args = metadata['internal_args']
        if not isinstance(internal_args, dict):
            return False

        # Each tool's internal args should be a dict
        for tool_name, tool_args in internal_args.items():
            if not isinstance(tool_args, dict):
                return False
            # Each arg should have at least a 'type' field
            for arg_name, arg_info in tool_args.items():
                if not isinstance(arg_info, dict):
                    return False

        return True

    def _find_internal_args_file(self, ctx: CollectorContext) -> Optional[Path]:
        """
        Find tool_internal_args.json based on context.
        First checks explicit path, then searches common locations.
        """
        # Use explicit path if provided
        if ctx.internal_args_path and ctx.internal_args_path.exists():
            return ctx.internal_args_path

        # Search patterns based on tools_path location
        if not ctx.tools_path:
            return None

        tools_path = ctx.tools_path.resolve()

        # Extract server name from path (e.g., mcp_outlook -> outlook)
        grandparent_name = tools_path.parent.parent.name
        server_name = None
        if grandparent_name.startswith("mcp_"):
            server_name = grandparent_name[4:]
        elif ctx.server_name:
            server_name = ctx.server_name

        # Search patterns (in order of priority)
        search_paths = [
            # Same directory as tools file
            tools_path.parent / "tool_internal_args.json",
            # mcp_editor/{server_name}/ pattern
            tools_path.parent.parent / tools_path.parent.name / "tool_internal_args.json",
        ]

        # Try to find the file
        for candidate in search_paths:
            if candidate.exists():
                return candidate

        # Fallback: search in mcp_editor directories at project root
        project_root = tools_path.parent
        while project_root.parent != project_root:
            mcp_editor_dir = project_root / "mcp_editor"
            if mcp_editor_dir.exists():
                # First, try specific server name directory if we know it
                if server_name:
                    specific_path = mcp_editor_dir / server_name / "tool_internal_args.json"
                    if specific_path.exists():
                        return specific_path

                # Look for tool_internal_args.json in subdirectories
                for subdir in mcp_editor_dir.iterdir():
                    if subdir.is_dir():
                        candidate = subdir / "tool_internal_args.json"
                        if candidate.exists():
                            return candidate
                break
            project_root = project_root.parent

        return None

    def _load_internal_args(self, internal_args_path: Path) -> Dict[str, Any]:
        """Load internal args from JSON file"""
        try:
            with open(internal_args_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _extract_defaults_from_schema(self, original_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract default values from original_schema.properties.
        Returns a dict with property names and their default values.
        """
        defaults = {}
        properties = original_schema.get('properties', {})
        for prop_name, prop_info in properties.items():
            if 'default' in prop_info:
                defaults[prop_name] = prop_info['default']
        return defaults

    def _enrich_internal_args_with_defaults(self, internal_args: Dict[str, Any]) -> Dict[str, Any]:
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
                    defaults = self._extract_defaults_from_schema(arg_info['original_schema'])
                    if defaults:
                        enriched_arg['value'] = defaults

                enriched[tool_name][arg_name] = enriched_arg

        return enriched