"""
Base collector interface and context for MCPMetaRegistry
"""
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Literal
from pathlib import Path

DEFAULT_SKIP_PARTS = (
    "venv",
    "__pycache__",
    ".git",
    "node_modules",
    "backups",
    "tests",
    "test",
)

@dataclass(frozen=True)
class CollectorContext:
    """
    Execution context for template generation (server-specific configuration)
    - server_name: outlook/file_handler/...
    - tools_path: tool_definition_templates.py path
    - internal_args_path: tool_internal_args.json path (optional)
    - scan_dir: @mcp_service scan target root (mcp_outlook, mcp_file_handler etc)
    - types_files: Pydantic type files list (outlook_types.py etc)
    """
    server_name: str
    tools_path: Path
    internal_args_path: Optional[Path] = None
    scan_dir: Optional[Path] = None
    types_files: list[Path] = field(default_factory=list)

    # Directories to skip during scanning (defaults to commonly unnecessary paths)
    skip_parts: tuple[str, ...] = DEFAULT_SKIP_PARTS

    # Caching (useful for long-running processes like web editor)
    cache_enabled: bool = True

    # Collection strategy
    # - ast: Safe (default), no import side-effects
    # - runtime: Import execution (side-effects/environment dependencies), can capture dynamic registrations
    # - hybrid: AST first, runtime to fill gaps (recommended: use sparingly)
    collect_mode: Literal["ast", "runtime", "hybrid"] = "ast"

class BaseCollector(ABC):
    """Base abstract class for all collectors"""

    @abstractmethod
    def collect(self, ctx: CollectorContext) -> Dict[str, Any]:
        """Collect metadata based on ctx (per server/file/environment)"""
        pass

    def collect_minimal(self, ctx: CollectorContext) -> Dict[str, Any]:
        """Minimal data for exception scenarios to keep pipeline alive (default: empty dict)"""
        return {}

    def collect_with_fallback(self, ctx: CollectorContext) -> Dict[str, Any]:
        """Return minimal output even on exceptions (recommended: accumulate warnings/errors in registry)"""
        try:
            return self.collect(ctx)
        except Exception:
            return self.collect_minimal(ctx)

    @abstractmethod
    def validate(self, metadata: Dict[str, Any]) -> bool:
        """Validate collected metadata"""
        pass

    def merge(self, existing: Dict, new: Dict) -> Dict:
        """Merge existing metadata with new metadata"""
        # NOTE: Template data has many nested structures, so shallow merge is risky.
        # Deep-merge + conflict reporting recommended at registry level.
        return {**existing, **new}