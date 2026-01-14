"""
Service Registry - Multi-language MCP service scanner and configuration generator.

This package provides functionality for:
- Scanning Python and JavaScript code for @mcp_service decorators
- Extracting type information from source code
- Generating editor configuration files
- Managing MCP service metadata

Structure:
- base.py: Common utilities (Language enum, detect_language, etc.)
- scanner.py: Unified scanner with re-exports from language-specific modules
- config_generator.py: Editor configuration generator
- meta_registry.py: Service metadata registry
- python/: Python-specific modules
    - scanner.py: Python AST scanner
    - types.py: Python type extraction
    - decorator.py: @mcp_service decorator
- javascript/: JavaScript-specific modules
    - scanner.py: JS/JSDoc scanner
    - types.py: Sequelize type extraction
"""

# Re-export main components for backward compatibility
from .base import Language, detect_language, DEFAULT_SKIP_PARTS
from .scanner import (
    # Python scanning
    MCPServiceExtractor,
    extract_decorator_metadata,
    find_mcp_services_in_python_file,
    signature_from_parameters,
    # JavaScript scanning
    ESPRIMA_AVAILABLE,
    JSDOC_TYPE_MAP,
    find_mcp_services_in_js_file,
    find_jsdoc_mcp_services_in_js_file,
    # Scanning utilities
    scan_codebase_for_mcp_services,
    get_services_map,
    export_services_to_json,
)

# Type extraction modules (for direct access)
from .python import types as extract_types
from .javascript import types as extract_types_js

# Backward compatibility aliases
from .python.decorator import mcp_service, MCP_SERVICE_REGISTRY

__all__ = [
    # Core
    "Language",
    "detect_language",
    "DEFAULT_SKIP_PARTS",
    # Python scanning
    "MCPServiceExtractor",
    "extract_decorator_metadata",
    "find_mcp_services_in_python_file",
    "signature_from_parameters",
    # JavaScript scanning
    "ESPRIMA_AVAILABLE",
    "JSDOC_TYPE_MAP",
    "find_mcp_services_in_js_file",
    "find_jsdoc_mcp_services_in_js_file",
    # High-level functions
    "scan_codebase_for_mcp_services",
    "get_services_map",
    "export_services_to_json",
    # Type extraction modules
    "extract_types",
    "extract_types_js",
    # Decorator
    "mcp_service",
    "MCP_SERVICE_REGISTRY",
]
