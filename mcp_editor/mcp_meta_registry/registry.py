"""
Main MCPMetaRegistry class that integrates all collectors
"""
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta

from .collectors import (
    CollectorContext,
    ToolDefinitionsCollector,
    InternalArgsCollector,
    ServiceScanner,
    ToolAnalyzer,
    PydanticModelsCollector
)


@dataclass
class CacheEntry:
    """Cache entry with value, timestamp, and fingerprint"""
    value: Dict[str, Any]
    created_at: datetime
    fingerprint: str


class MCPMetaRegistry:
    """
    Central registry for MCP metadata collection and management.
    Coordinates all collectors to produce Jinja-ready context data.
    """

    def __init__(self, cache_ttl: int = 300):
        """
        Initialize the registry.

        Args:
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
        """
        self.cache: Dict[str, CacheEntry] = {}
        self.cache_ttl = timedelta(seconds=cache_ttl)

        # Initialize collectors
        self.tool_definitions_collector = ToolDefinitionsCollector()
        self.internal_args_collector = InternalArgsCollector()
        self.service_scanner = ServiceScanner()
        self.tool_analyzer = ToolAnalyzer()
        self.pydantic_models_collector = PydanticModelsCollector()

        # Store warnings and errors
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def collect_all(self, ctx: CollectorContext) -> Dict[str, Any]:
        """
        Collect all metadata using the configured collectors.

        Args:
            ctx: Collector context with server configuration

        Returns:
            Complete metadata dictionary
        """
        # Check cache if enabled
        if ctx.cache_enabled:
            cache_key = self._get_cache_key(ctx)
            cached = self._get_cached(cache_key, ctx)
            if cached:
                return cached

        # Clear previous warnings/errors
        self.warnings.clear()
        self.errors.clear()

        # Phase 1: Load basic data
        tools_data = self.tool_definitions_collector.collect_with_fallback(ctx)
        internal_args_data = self.internal_args_collector.collect_with_fallback(ctx)

        # Phase 2: Scan for services
        services_data = self.service_scanner.collect_with_fallback(ctx)

        # Phase 3: Collect parameter types
        pydantic_data = self.pydantic_models_collector.collect_with_fallback(ctx)

        # Augment parameter types from tools and internal args
        additional_types = self.pydantic_models_collector.collect_from_tools_and_args(
            tools_data.get('tools', []),
            internal_args_data.get('internal_args', {})
        )

        # Merge all parameter types
        all_param_types = self.pydantic_models_collector.merge_param_types(
            set(pydantic_data.get('param_types', [])),
            set(services_data.get('param_types', [])),
            additional_types
        )

        # Phase 4: Analyze tools with all dependencies
        analysis = self.tool_analyzer.analyze_with_dependencies(
            tools_data.get('tools', []),
            services_data.get('services', {}),
            internal_args_data.get('internal_args', {}),
            services_data.get('methods', {})
        )

        # Combine all metadata
        metadata = {
            'tools': tools_data.get('tools', []),
            'analyzed_tools': analysis.get('analyzed_tools', []),
            'services': services_data.get('services', {}),
            'methods': services_data.get('methods', {}),
            'param_types': all_param_types,
            'internal_args': internal_args_data.get('internal_args', {}),
            'handler_instances': analysis.get('handler_instances', []),
            'server_name': ctx.server_name,
            'warnings': self.warnings.copy(),
            'errors': self.errors.copy()
        }

        # Extract modules from services
        metadata['modules'] = sorted({
            info['module'] for info in metadata['services'].values()
        })

        # Cache the result if enabled
        if ctx.cache_enabled:
            self._cache_result(cache_key, metadata, ctx)

        return metadata

    def to_jinja_context(self, ctx: CollectorContext) -> Dict[str, Any]:
        """
        Generate Jinja-ready context from collected metadata.
        This is the main output method that produces template-compatible data.

        Args:
            ctx: Collector context with server configuration

        Returns:
            Context dictionary ready for Jinja template rendering
        """
        # Collect all metadata
        metadata = self.collect_all(ctx)

        # Transform to Jinja context format
        context = {
            'tools': metadata['analyzed_tools'],  # Use analyzed tools with all fields
            'services': metadata['services'],
            'param_types': metadata['param_types'],
            'modules': metadata['modules'],
            'internal_args': metadata['internal_args'],
            'server_name': ctx.server_name,
            'handler_instances': metadata['handler_instances']
        }

        return context

    def validate_all(self, ctx: CollectorContext) -> bool:
        """
        Validate all collected metadata.

        Args:
            ctx: Collector context with server configuration

        Returns:
            True if all validations pass, False otherwise
        """
        metadata = self.collect_all(ctx)

        # Validate each collector's output
        validations = [
            self.tool_definitions_collector.validate(metadata),
            self.internal_args_collector.validate({'internal_args': metadata['internal_args']}),
            self.service_scanner.validate(metadata),
            self.tool_analyzer.validate({'analyzed_tools': metadata['analyzed_tools']}),
            self.pydantic_models_collector.validate({'param_types': metadata['param_types']})
        ]

        return all(validations)

    def get_summary(self, ctx: CollectorContext) -> str:
        """
        Get a summary of collected metadata.

        Args:
            ctx: Collector context with server configuration

        Returns:
            Human-readable summary string
        """
        metadata = self.collect_all(ctx)

        summary = []
        summary.append(f"Server: {ctx.server_name}")
        summary.append(f"Tools: {len(metadata.get('tools', []))}")
        summary.append(f"Services: {len(metadata.get('services', {}))}")
        summary.append(f"Parameter Types: {len(metadata.get('param_types', []))}")
        summary.append(f"Internal Args: {len(metadata.get('internal_args', {}))}")

        if self.warnings:
            summary.append(f"Warnings: {len(self.warnings)}")
        if self.errors:
            summary.append(f"Errors: {len(self.errors)}")

        return "\n".join(summary)

    def _get_cache_key(self, ctx: CollectorContext) -> str:
        """Generate cache key from context"""
        resolved_internal_args = self._resolve_internal_args_path(ctx)
        parts = [
            ctx.server_name,
            str(ctx.tools_path),
            str(resolved_internal_args),
            str(ctx.scan_dir),
            ','.join(str(f) for f in ctx.types_files)
        ]
        return '|'.join(parts)

    def _resolve_internal_args_path(self, ctx: CollectorContext) -> Optional[Path]:
        """Resolve internal args path even when ctx.internal_args_path is not set."""
        if ctx.internal_args_path and ctx.internal_args_path.exists():
            return ctx.internal_args_path
        try:
            return self.internal_args_collector._find_internal_args_file(ctx)
        except Exception:
            return None

    def _get_fingerprint(self, ctx: CollectorContext) -> str:
        """
        Generate fingerprint based on file modification times.
        Used for cache invalidation.
        """
        fingerprint_parts = []

        # Add file modification times
        resolved_internal_args = self._resolve_internal_args_path(ctx)
        for path in [ctx.tools_path, resolved_internal_args]:
            if path and path.exists():
                mtime = path.stat().st_mtime
                fingerprint_parts.append(f"{path}:{mtime}")

        for type_file in ctx.types_files:
            if type_file and type_file.exists():
                mtime = type_file.stat().st_mtime
                fingerprint_parts.append(f"{type_file}:{mtime}")

        # Include scan_dir Python files (used by ServiceScanner) so edits invalidate cache
        if ctx.scan_dir and ctx.scan_dir.exists():
            search_dirs = [
                ctx.scan_dir,
                ctx.scan_dir.parent,
                ctx.scan_dir / 'mcp_server'
            ]
            for search_dir in search_dirs:
                if not search_dir.exists():
                    continue
                for py_file in sorted(search_dir.glob('*.py')):
                    if any(skip in str(py_file) for skip in ctx.skip_parts):
                        continue
                    if any(skip in py_file.name for skip in ['server.py', 'tool_definitions.py', 'test_']):
                        continue
                    try:
                        mtime = py_file.stat().st_mtime
                    except OSError:
                        continue
                    fingerprint_parts.append(f"{py_file}:{mtime}")

        return '|'.join(fingerprint_parts)

    def _get_cached(self, cache_key: str, ctx: CollectorContext) -> Optional[Dict[str, Any]]:
        """Get cached result if valid"""
        if cache_key not in self.cache:
            return None

        entry = self.cache[cache_key]

        # Check TTL
        if datetime.now() - entry.created_at > self.cache_ttl:
            del self.cache[cache_key]
            return None

        # Check fingerprint (file modifications)
        current_fingerprint = self._get_fingerprint(ctx)
        if entry.fingerprint != current_fingerprint:
            del self.cache[cache_key]
            return None

        return entry.value

    def _cache_result(self, cache_key: str, metadata: Dict[str, Any], ctx: CollectorContext) -> None:
        """Cache the metadata result"""
        self.cache[cache_key] = CacheEntry(
            value=metadata,
            created_at=datetime.now(),
            fingerprint=self._get_fingerprint(ctx)
        )

    def clear_cache(self) -> None:
        """Clear all cached entries"""
        self.cache.clear()

    def add_warning(self, message: str) -> None:
        """Add a warning message"""
        self.warnings.append(message)

    def add_error(self, message: str) -> None:
        """Add an error message"""
        self.errors.append(message)
